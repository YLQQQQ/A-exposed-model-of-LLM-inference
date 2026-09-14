# Gate 6 Windows GPU 服务器操作手册

## 1. 本轮目标与边界

本轮在 **一张固定 GPU、一个固定软件栈** 上运行 Q0。输出只用于证明 analyzer 的 Correctness 资格，不是 N1/G1/G2 性能结果，也不是 Formal 数据。RTX 4090 或 RTX 6000 Ada 均可先做 Windows Engineering/Q0；同一轮不得混用两张卡。若论文正式平台改为 Linux，必须在 Linux 目标栈重新执行平台资格检查和 Q0，不能直接沿用 Windows Q0。

开始前应确保工作区位于 `codex/v141-analyzer`，且至少包含本地准备完成提交。禁止覆盖已有输出；失败后使用新的 `run-id` 和新目录重跑，保留失败现场。

## 2. 一次性环境检查

在仓库根目录打开 PowerShell：

```powershell
git status --short --branch
nvidia-smi -L
python --version
& "C:\Program Files\NVIDIA Corporation\Nsight Systems 2026.4.1\target-windows-x64\nsys.exe" --version
nvcc --version
python -m pytest tests/test_v141_q0_execution.py tests/test_v141_q0_collection.py tests/test_v141_q0_faults.py tests/test_v141_q0_real.py tests/test_v141_q0_gate.py -q -p no:cacheprovider
```

建议用 `nvidia-smi -L` 显示的 GPU UUID 作为 `CUDA_VISIBLE_DEVICES` 选择器。若 Nsight 安装路径不同，以服务器实际路径为准，不要复制本机绝对路径。

## 3. 编译并准备不可覆盖运行目录

```powershell
$Q0Root = Resolve-Path .
$RunId = "q0-win-4090-20260914-r1"
$Out = Join-Path $Q0Root "engineering_evidence\q0_real\$RunId"
$Binary = Join-Path $Out "bin\exposedpath_q0.exe"
$Nsys = "C:\Program Files\NVIDIA Corporation\Nsight Systems 2026.4.1\target-windows-x64\nsys.exe"
$GpuSelector = "GPU-替换为nvidia-smi显示的完整UUID"

python -m exposedpath_v141 build-q0-microbench --nvcc (Get-Command nvcc).Source --output $Binary --platform windows
python -m exposedpath_v141 prepare-q0-run --output-dir (Join-Path $Out "run") --binary $Binary --nsys $Nsys --platform windows --run-id $RunId --cuda-visible-device $GpuSelector
```

验收：编译输出为 `PASS`；run manifest 为 `PREPARED_NOT_EXECUTED`；每个 source manifest 中 logical device 都是 `0`，物理 GPU 由同一个 UUID 显式绑定。

## 4. 采集 21 个真实 seed

```powershell
$RunManifest = Join-Path $Out "run\q0_run_manifest.json"
$Run = Get-Content -LiteralPath $RunManifest -Raw | ConvertFrom-Json
$NativeCases = @($Run.cases | Where-Object { $null -ne $_.command_argv })
foreach ($Case in $NativeCases) {
    python -m exposedpath_v141 execute-q0-case --run-manifest $RunManifest --case $Case.case_id
    if ($LASTEXITCODE -ne 0) { throw "采集失败：$($Case.case_id)，保留现场并停止" }
}
```

验收：应恰有 21 份 `collection_receipt.json` 和 21 份非空 `.nsys-rep`；每份 receipt 的 GPU UUID、driver、CUDA、Nsight 和 OS 身份一致。不要手工改 receipt 或 Raw。

## 5. 导出 SQLite 与生成 Canonical

逐 case 执行以下模板。`nsys export` 只读取 Raw，不得覆盖已存在 SQLite：

```powershell
$CaseId = "Q0-STREAM-001"  # 每次替换
$CaseDir = Join-Path $Out "run\cases\$CaseId"
$Raw = Join-Path $CaseDir "trace.nsys-rep"
$Sqlite = Join-Path $CaseDir "trace.sqlite"
$SourceManifest = Join-Path $CaseDir "source_manifest.json"
$RawSha = (Get-FileHash -LiteralPath $Raw -Algorithm SHA256).Hash
$Receipt = Get-Content -LiteralPath (Join-Path $CaseDir "collection_receipt.json") -Raw | ConvertFrom-Json
$CollectorVersion = [string]$Receipt.environment.nsight_systems

& $Nsys export --type sqlite --force-overwrite=false --output $Sqlite $Raw
if ($LASTEXITCODE -ne 0) { throw "SQLite 导出失败：$CaseId" }
python -m exposedpath_v141 convert-sqlite --sqlite $Sqlite --output-dir (Join-Path $CaseDir "canonical") --data-role Engineering --raw-sha256 $RawSha --collector-version $CollectorVersion --source-manifest $SourceManifest
if ($LASTEXITCODE -notin 0,2,3) { throw "Canonical 转换异常：$CaseId" }
```

`2/3` 只在预期的含糊/无效负例中可能出现；它不是程序崩溃。是否符合预写 oracle 由后续 evaluator 判定，不能人工改成成功。

## 6. 三个受控故障 case

只对以下 case 的源 Canonical 创建新副本，然后以下游输入改用副本：

```powershell
$FaultCases = @("Q0-MISSING-CORR-001", "Q0-DROPPED-001", "Q0-GRAPH-UNSUPPORTED-001")
foreach ($CaseId in $FaultCases) {
    $CaseDir = Join-Path $Out "run\cases\$CaseId"
    python -m exposedpath_v141 apply-q0-fault --canonical-manifest (Join-Path $CaseDir "canonical\canonical_manifest.json") --case $CaseId --output-dir (Join-Path $CaseDir "canonical_fault")
    if ($LASTEXITCODE -ne 0) { throw "故障副本生成失败：$CaseId" }
}
```

源 Canonical 和 Raw 必须保持不变。故障 manifest 必须显示恰好一次 mutation，并记录目标记录、预写活动标签及源 manifest 哈希。

## 7. S、A/B 与逐 case 独立对照

对 21 个真实 case 循环。故障 case 使用 `canonical_fault`，其余使用 `canonical`。S/A/B 对预期负例可返回 `2/3`，但必须实际生成完整 bundle；最终只接受 evaluator 的 `REAL_CASE_PASS`。

```powershell
foreach ($Case in $NativeCases) {
    $CaseId = $Case.case_id
    $CaseDir = Join-Path $Out "run\cases\$CaseId"
    $CanonicalDir = if ($FaultCases -contains $CaseId) { "canonical_fault" } else { "canonical" }
    $CanonicalManifest = Join-Path $CaseDir "$CanonicalDir\canonical_manifest.json"
    $SDir = Join-Path $CaseDir "s"
    $ABDir = Join-Path $CaseDir "ab"
    $EvidenceDir = Join-Path $Out "real_evidence\$CaseId"

    python -m exposedpath_v141 analyze-s --canonical-manifest $CanonicalManifest --output-dir $SDir
    if ($LASTEXITCODE -notin 0,2,3) { throw "S 执行异常：$CaseId" }
    python -m exposedpath_v141 analyze-ab --canonical-manifest $CanonicalManifest --s-manifest (Join-Path $SDir "s_manifest.json") --output-dir $ABDir
    if ($LASTEXITCODE -notin 0,2,3) { throw "A/B 执行异常：$CaseId" }
    python -m exposedpath_v141 evaluate-q0-real-case --case $CaseId --canonical-manifest $CanonicalManifest --s-manifest (Join-Path $SDir "s_manifest.json") --ab-manifest (Join-Path $ABDir "ab_manifest.json") --collection-receipt (Join-Path $CaseDir "collection_receipt.json") --output-dir $EvidenceDir
    if ($LASTEXITCODE -ne 0) { throw "真实 Q0 case 未通过：$CaseId" }
}
```

## 8. 合成边界例与唯一 Gate 报告

两个不能靠普通真实调度稳定制造的边界例（terminal 并列、提交顺序不可判定）必须继续走预定义合成 Canonical；完整合成回归不能替代其余 21 个真实 case。

```powershell
$SyntheticDir = Join-Path $Out "synthetic"
python -m exposedpath_v141 run-q0-synthetic --output-dir $SyntheticDir
if ($LASTEXITCODE -ne 0) { throw "合成 Q0 回归失败" }

python -m exposedpath_v141 aggregate-q0-gate --real-evidence-dir (Join-Path $Out "real_evidence") --synthetic-report (Join-Path $SyntheticDir "q0_synthetic_report.json") --output-dir (Join-Path $Out "gate")
if ($LASTEXITCODE -ne 0) { throw "Gate 6 未通过" }
```

只有 `q0_gate_report.json` 同时显示 `23/23`、`verdict=PASS`、`q0_status=PASS`，才能把 Gate 6 判为通过。该 PASS 只说明当前 analyzer 在这套目标 observation stack 上取得 Q0 资格；仍不能称 Engineering Pilot、Protocol Freeze 或正式实验已完成。

## 9. 完成后需要带回本地的内容

保留整个 `$Out` 目录，至少包括 run manifest、21 份 Raw/SQLite/receipt、Canonical（含 3 个故障副本）、S、A/B、real evidence、synthetic 和唯一 gate report。不要只复制最后一张表。返回本地后先核对 Raw 哈希和 Gate report，再更新科研进度清单。
