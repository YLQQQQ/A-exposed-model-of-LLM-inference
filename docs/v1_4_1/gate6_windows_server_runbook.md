# Gate 6 Windows GPU 服务器操作手册

## 0. 从本机部署到已有服务器

服务器中原有的 `YLQ_test` 包含旧项目、旧虚拟环境和历史 `nsys_*`、`pilot_*` 结果，应完整保留，不得覆盖、删除或把它改名冒充新版。本轮继续使用已有 `YLQ_test_q0_v141`，通过 Git bundle 只更新受 Git 跟踪的代码，不重新 clone，也不执行 `git clean`。

本机已经生成的交付文件位于仓库根目录的 `transfer` 文件夹，名称以最终交付消息为准。把这一份 `.bundle` 文件通过 RDP、共享盘或移动介质复制到服务器原 `YLQ_test` 的同级目录。服务器目录建议为：

```text
Wsn1
├── YLQ_test                 # 旧项目和旧结果，保持不动
├── ExposedPath_Q0_*.bundle  # 本机交付包
└── YLQ_test_q0_v141         # 已有 Q0 工作目录，含未跟踪的 r1/r2
```

先在服务器 PowerShell 中确认不存在尚未提交的受跟踪修改，并为服务器临时提交建立备份分支：

```powershell
Set-Location ".\YLQ_test_q0_v141"
git status --short --branch
$TrackedDirty = git status --porcelain=v1 --untracked-files=no
if ($TrackedDirty) { throw "存在未保存的受跟踪修改，停止更新" }
$BeforeUpdate = git rev-parse HEAD
git branch "backup/server-before-$($BeforeUpdate.Substring(0,8))" $BeforeUpdate
git fetch "..\ExposedPath_Q0_实际文件名.bundle" codex/v141-analyzer
git reset --hard FETCH_HEAD
git rev-parse HEAD
```

`git reset --hard` 只能在上述 tracked-dirty 检查为空、备份分支已建立后执行；它不会删除未跟踪的 `engineering_evidence/r1、r2`。严禁追加 `git clean`。更新后以最终交付消息记录的 commit 为核对值。

Q0 不加载模型，因此不用复制旧 `models`。服务器已有 GPU driver、CUDA Toolkit、`nvcc` 和 Nsight Systems 可以复用，但必须重新记录版本。旧 `.venv` 不必删除，也不要向其中追加依赖；在新版目录建立轻量独立环境：

```powershell
if (-not (Test-Path ".\.venv\Scripts\python.exe")) { py -m venv .venv }
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install pytest jsonschema
$Python = (Resolve-Path ".\.venv\Scripts\python.exe").Path
& $Python -m pytest tests/test_v141_q0_execution.py tests/test_v141_q0_collection.py tests/test_v141_q0_faults.py tests/test_v141_q0_real.py tests/test_v141_q0_gate.py -q -p no:cacheprovider
```

后续命令统一把文中的 `python` 替换为 `& $Python`，避免意外调用旧环境。先完成环境检查和 `Q0-STREAM-001` 单例；单例失败时停止并回传该次输出，不要直接批量运行。

## 1. 本轮目标与边界

本轮在 **一张固定 GPU、一个固定软件栈** 上运行 Q0。输出只用于证明 analyzer 的 Correctness 资格，不是 N1/G1/G2 性能结果，也不是 Formal 数据。RTX 4090 或 RTX 6000 Ada 均可先做 Windows Engineering/Q0；同一轮不得混用两张卡。若论文正式平台改为 Linux，必须在 Linux 目标栈重新执行平台资格检查和 Q0，不能直接沿用 Windows Q0。

开始前应确保工作区位于 `codex/v141-analyzer`，且至少包含本地准备完成提交。禁止覆盖已有输出；失败后使用新的 `run-id` 和新目录重跑，保留失败现场。

## 2. 一次性环境检查

在新版仓库根目录打开 PowerShell：

```powershell
git status --short --branch
nvidia-smi -L
& $Python --version
& "C:\Program Files\NVIDIA Corporation\Nsight Systems 2026.2.1\target-windows-x64\nsys.exe" --version
nvcc --version
& $Python -m pytest tests/test_v141_q0_execution.py tests/test_v141_q0_collection.py tests/test_v141_q0_faults.py tests/test_v141_q0_real.py tests/test_v141_q0_gate.py -q -p no:cacheprovider
```

建议用 `nvidia-smi -L` 显示的 GPU UUID 作为 `CUDA_VISIBLE_DEVICES` 选择器。若 Nsight 安装路径不同，以服务器实际路径为准，不要复制本机绝对路径。

CUDA 12.4 不支持默认的 VS 2026/MSVC 14.51。服务器必须并行安装 VS 2022 v143 的兼容工具集，并在编译 Q0 时显式选择 MSVC 14.39；不要使用 `-allow-unsupported-compiler` 掩盖版本不兼容：

```powershell
$VsWhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
$VsInstall = & $VsWhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$VcVars = Join-Path $VsInstall "VC\Auxiliary\Build\vcvars64.bat"
Get-ChildItem (Join-Path $VsInstall "VC\Tools\MSVC") -Directory | Select-Object Name,FullName
```

验收：列表中必须存在 `14.39.*`。只有 `14.51.*` 时先安装兼容 v143 工具集，不能继续编译。

## 2.5 使用现有 r2 做只读兼容性诊断

代码更新后，先检查已有 r2，不修改其 Raw、SQLite、receipt 或 manifest。诊断输出写入新的同级派生目录：

```powershell
$Q0Root = Resolve-Path .
$R2SqliteCandidates = @(
    Get-ChildItem (Join-Path $Q0Root "engineering_evidence") -Recurse -File -Filter "trace.sqlite" |
        Where-Object { $_.Directory.Name -eq "Q0-STREAM-001" -and $_.FullName -match "(?i)r2" }
)
$R2SqliteCandidates | Select-Object FullName
if ($R2SqliteCandidates.Count -ne 1) { throw "无法唯一定位 r2/Q0-STREAM-001；请先核对上面列出的路径" }
$R2Case = $R2SqliteCandidates[0].Directory.FullName
$R2Raw = Join-Path $R2Case "trace.nsys-rep"
$R2Sqlite = $R2SqliteCandidates[0].FullName
$R2Manifest = Join-Path $R2Case "source_manifest.json"
$R2Receipt = Get-Content (Join-Path $R2Case "collection_receipt.json") -Raw | ConvertFrom-Json
$CodeShort = git rev-parse --short=8 HEAD
$R2Diag = Join-Path $Q0Root "engineering_evidence\q0_compat_diagnostics\r2-stream-$CodeShort"

& $Python -m exposedpath_v141 inspect-sqlite --sqlite $R2Sqlite --output-dir $R2Diag --data-role Engineering --raw-sha256 (Get-FileHash $R2Raw -Algorithm SHA256).Hash --collector-version ([string]$R2Receipt.environment.nsight_systems) --source-manifest $R2Manifest
if ($LASTEXITCODE -ne 3) { throw "r2 应因已知捕获结束同步而 fail-closed" }
$R2Report = Get-Content (Join-Path $R2Diag "observation_report.json") -Raw | ConvertFrom-Json
$R2Invalid = @($R2Report.validity.issues | Where-Object level -eq "invalid")
if ($R2Invalid.Count -ne 1 -or $R2Invalid[0].code -ne "SYNC_RUNTIME_MAPPING_NOT_UNIQUE") { throw "r2 出现未预期的兼容性问题" }
```

已知 r2 的唯一 invalid 是 request 结束后由 `cudaProfilerStop` 触发的 context 同步，`correlationId=134` 且没有 runtime 候选。它证明旧 Raw 必须被阻断，不表示 3.25.0 schema 不兼容。新版微程序会在 request 外、停止 profiler 前显式排空受控设备工作；因此必须创建全新的 r3，不能覆盖或把 r2 改成通过。

## 3. 编译并准备不可覆盖运行目录

```powershell
$Q0Root = Resolve-Path .
$RunId = "q0-win-4090-YYYYMMDD-r3"  # 执行时替换日期；必须是全新目录
$Out = Join-Path $Q0Root "engineering_evidence\q0_real\$RunId"
$Binary = Join-Path $Out "bin\exposedpath_q0.exe"
$Nsys = "C:\Program Files\NVIDIA Corporation\Nsight Systems 2026.2.1\target-windows-x64\nsys.exe"
$GpuSelector = "GPU-替换为nvidia-smi显示的完整UUID"

$Nvcc = (Get-Command nvcc).Source
cmd /d /s /c "`"$VcVars`" -vcvars_ver=14.39 && where cl && `"$Python`" -m exposedpath_v141 build-q0-microbench --nvcc `"$Nvcc`" --output `"$Binary`" --platform windows"
if ($LASTEXITCODE -ne 0) { throw "Q0 CUDA 编译失败" }
& $Python -m exposedpath_v141 prepare-q0-run --output-dir (Join-Path $Out "run") --binary $Binary --nsys $Nsys --platform windows --run-id $RunId --cuda-visible-device $GpuSelector

git rev-parse HEAD | Set-Content (Join-Path $Out "code_commit.txt")
git status --porcelain=v1 | Set-Content (Join-Path $Out "git_status.txt")
```

验收：编译输出为 `PASS`；run manifest 为 `PREPARED_NOT_EXECUTED`；每个 source manifest 中 logical device 都是 `0`，物理 GPU 由同一个 UUID 显式绑定。

## 4. 只采集 r3 单例

```powershell
$RunManifest = Join-Path $Out "run\q0_run_manifest.json"
$Run = Get-Content -LiteralPath $RunManifest -Raw | ConvertFrom-Json
$NativeCases = @($Run.cases | Where-Object { $null -ne $_.command_argv })
$SmokeCaseId = "Q0-STREAM-001"
& $Python -m exposedpath_v141 execute-q0-case --run-manifest $RunManifest --case $SmokeCaseId
if ($LASTEXITCODE -ne 0) { throw "r3 单例采集失败，保留现场并停止" }
```

验收：此时只能新增 `Q0-STREAM-001` 的 receipt 和非空 `.nsys-rep`。不要提前运行其余 20 个 seed，也不要手工改 receipt 或 Raw。

## 5. r3 单例全链路验收

先只处理 `Q0-STREAM-001`。`nsys export` 只读取 Raw，不得覆盖已存在 SQLite：

```powershell
$CaseId = $SmokeCaseId
$CaseDir = Join-Path $Out "run\cases\$CaseId"
$Raw = Join-Path $CaseDir "trace.nsys-rep"
$Sqlite = Join-Path $CaseDir "trace.sqlite"
$SourceManifest = Join-Path $CaseDir "source_manifest.json"
$RawSha = (Get-FileHash -LiteralPath $Raw -Algorithm SHA256).Hash
$Receipt = Get-Content -LiteralPath (Join-Path $CaseDir "collection_receipt.json") -Raw | ConvertFrom-Json
$CollectorVersion = [string]$Receipt.environment.nsight_systems

& $Nsys export --type sqlite --force-overwrite=false --output $Sqlite $Raw
if ($LASTEXITCODE -ne 0) { throw "SQLite 导出失败：$CaseId" }
& $Python -m exposedpath_v141 convert-sqlite --sqlite $Sqlite --output-dir (Join-Path $CaseDir "canonical") --data-role Engineering --raw-sha256 $RawSha --collector-version $CollectorVersion --source-manifest $SourceManifest
if ($LASTEXITCODE -ne 0) { throw "Canonical 转换未通过：$CaseId；保留现场并停止" }

$SDir = Join-Path $CaseDir "s"
$ABDir = Join-Path $CaseDir "ab"
$EvidenceDir = Join-Path $Out "real_evidence\$CaseId"
& $Python -m exposedpath_v141 analyze-s --canonical-manifest (Join-Path $CaseDir "canonical\canonical_manifest.json") --output-dir $SDir
if ($LASTEXITCODE -notin 0,2,3) { throw "r3 单例 S 执行异常；保留现场并停止" }
& $Python -m exposedpath_v141 analyze-ab --canonical-manifest (Join-Path $CaseDir "canonical\canonical_manifest.json") --s-manifest (Join-Path $SDir "s_manifest.json") --output-dir $ABDir
if ($LASTEXITCODE -notin 0,2,3) { throw "r3 单例 A/B 执行异常；保留现场并停止" }
& $Python -m exposedpath_v141 evaluate-q0-real-case --case $CaseId --canonical-manifest (Join-Path $CaseDir "canonical\canonical_manifest.json") --s-manifest (Join-Path $SDir "s_manifest.json") --ab-manifest (Join-Path $ABDir "ab_manifest.json") --collection-receipt (Join-Path $CaseDir "collection_receipt.json") --output-dir $EvidenceDir
if ($LASTEXITCODE -ne 0) { throw "r3 单例独立对照未通过；保留现场并停止" }
```

验收：Canonical 转换必须返回 0；S/A/B 必须生成完整 bundle，其中 request 外的 harness 排空同步可以按既有 fail-closed 规则形成非零状态；独立 evaluator 必须返回 0，且 `Q0-STREAM-001` 的 real evidence 为 `REAL_CASE_PASS`。若目标 request 仍出现额外 sync、映射歧义或其他 invalid，停止并回传整个 r3 单例目录；不能继续批量。

## 6. 单例通过后采集并转换其余 20 个 seed

```powershell
$RemainingCases = @($NativeCases | Where-Object case_id -ne $SmokeCaseId)
foreach ($Case in $RemainingCases) {
    $CaseId = $Case.case_id
    & $Python -m exposedpath_v141 execute-q0-case --run-manifest $RunManifest --case $CaseId
    if ($LASTEXITCODE -ne 0) { throw "采集失败：$CaseId，保留现场并停止" }

    $CaseDir = Join-Path $Out "run\cases\$CaseId"
    $Raw = Join-Path $CaseDir "trace.nsys-rep"
    $Sqlite = Join-Path $CaseDir "trace.sqlite"
    $SourceManifest = Join-Path $CaseDir "source_manifest.json"
    $RawSha = (Get-FileHash -LiteralPath $Raw -Algorithm SHA256).Hash
    $Receipt = Get-Content -LiteralPath (Join-Path $CaseDir "collection_receipt.json") -Raw | ConvertFrom-Json
    $CollectorVersion = [string]$Receipt.environment.nsight_systems
    & $Nsys export --type sqlite --force-overwrite=false --output $Sqlite $Raw
    if ($LASTEXITCODE -ne 0) { throw "SQLite 导出失败：$CaseId" }
    & $Python -m exposedpath_v141 convert-sqlite --sqlite $Sqlite --output-dir (Join-Path $CaseDir "canonical") --data-role Engineering --raw-sha256 $RawSha --collector-version $CollectorVersion --source-manifest $SourceManifest
    if ($LASTEXITCODE -ne 0) { throw "Canonical 转换未通过：$CaseId；保留现场并停止" }
}
```

验收：最终恰有 21 份 receipt、21 份非空 Raw 和 21 份 valid 源 Canonical；GPU、driver、CUDA、Nsight 和 OS 身份一致。三个预期负例也必须先得到 valid 源 Canonical，其 invalid 只能来自下一步的受控副本。

## 7. 三个受控故障 case

只对以下 case 的源 Canonical 创建新副本，然后以下游输入改用副本：

```powershell
$FaultCases = @("Q0-MISSING-CORR-001", "Q0-DROPPED-001", "Q0-GRAPH-UNSUPPORTED-001")
foreach ($CaseId in $FaultCases) {
    $CaseDir = Join-Path $Out "run\cases\$CaseId"
    & $Python -m exposedpath_v141 apply-q0-fault --canonical-manifest (Join-Path $CaseDir "canonical\canonical_manifest.json") --case $CaseId --output-dir (Join-Path $CaseDir "canonical_fault")
    if ($LASTEXITCODE -ne 0) { throw "故障副本生成失败：$CaseId" }
}
```

源 Canonical 和 Raw 必须保持不变。故障 manifest 必须显示恰好一次 mutation，并记录目标记录、预写活动标签及源 manifest 哈希。

## 8. 其余 20 个 case 的 S、A/B 与独立对照

`Q0-STREAM-001` 已在步骤 5 通过，不再重复写输出。对其余 20 个真实 case 循环；故障 case 使用 `canonical_fault`，其余使用 `canonical`。S/A/B 对预期负例可返回 `2/3`，但必须实际生成完整 bundle；最终只接受 evaluator 的 `REAL_CASE_PASS`。

```powershell
foreach ($Case in $RemainingCases) {
    $CaseId = $Case.case_id
    $CaseDir = Join-Path $Out "run\cases\$CaseId"
    $CanonicalDir = if ($FaultCases -contains $CaseId) { "canonical_fault" } else { "canonical" }
    $CanonicalManifest = Join-Path $CaseDir "$CanonicalDir\canonical_manifest.json"
    $SDir = Join-Path $CaseDir "s"
    $ABDir = Join-Path $CaseDir "ab"
    $EvidenceDir = Join-Path $Out "real_evidence\$CaseId"

    & $Python -m exposedpath_v141 analyze-s --canonical-manifest $CanonicalManifest --output-dir $SDir
    if ($LASTEXITCODE -notin 0,2,3) { throw "S 执行异常：$CaseId" }
    & $Python -m exposedpath_v141 analyze-ab --canonical-manifest $CanonicalManifest --s-manifest (Join-Path $SDir "s_manifest.json") --output-dir $ABDir
    if ($LASTEXITCODE -notin 0,2,3) { throw "A/B 执行异常：$CaseId" }
    & $Python -m exposedpath_v141 evaluate-q0-real-case --case $CaseId --canonical-manifest $CanonicalManifest --s-manifest (Join-Path $SDir "s_manifest.json") --ab-manifest (Join-Path $ABDir "ab_manifest.json") --collection-receipt (Join-Path $CaseDir "collection_receipt.json") --output-dir $EvidenceDir
    if ($LASTEXITCODE -ne 0) { throw "真实 Q0 case 未通过：$CaseId" }
}
```

## 9. 合成边界例与唯一 Gate 报告

两个不能靠普通真实调度稳定制造的边界例（terminal 并列、提交顺序不可判定）必须继续走预定义合成 Canonical；完整合成回归不能替代其余 21 个真实 case。

```powershell
$SyntheticDir = Join-Path $Out "synthetic"
& $Python -m exposedpath_v141 run-q0-synthetic --output-dir $SyntheticDir
if ($LASTEXITCODE -ne 0) { throw "合成 Q0 回归失败" }

& $Python -m exposedpath_v141 aggregate-q0-gate --real-evidence-dir (Join-Path $Out "real_evidence") --synthetic-report (Join-Path $SyntheticDir "q0_synthetic_report.json") --output-dir (Join-Path $Out "gate")
if ($LASTEXITCODE -ne 0) { throw "Gate 6 未通过" }
```

只有 `q0_gate_report.json` 同时显示 `23/23`、`verdict=PASS`、`q0_status=PASS`，才能把 Gate 6 判为通过。该 PASS 只说明当前 analyzer 在这套目标 observation stack 上取得 Q0 资格；仍不能称 Engineering Pilot、Protocol Freeze 或正式实验已完成。

## 10. 完成后需要带回本地的内容

保留并回传整个 `$Out` 目录，至少包括 `code_commit.txt`、`git_status.txt`、run manifest、21 份 Raw/SQLite/receipt、Canonical（含 3 个故障副本）、S、A/B、real evidence、synthetic 和唯一 gate report。不要只复制最后一张表。返回本地后先核对代码版本、Raw 哈希和 Gate report，再更新科研进度清单。
