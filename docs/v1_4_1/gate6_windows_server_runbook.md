# Gate 6 Windows GPU 服务器操作手册

## 0. 从本机部署到已有服务器

服务器中原有的 `YLQ_test` 包含旧项目、旧虚拟环境和历史 `nsys_*`、`pilot_*` 结果，应完整保留，不得覆盖、删除或把它改名冒充新版。本轮继续使用已有 `YLQ_test_q0_v141`，通过 Git bundle 只更新受 Git 跟踪的代码，不重新 clone，也不执行 `git clean`。

本机已经生成的交付文件位于仓库根目录的 `transfer` 文件夹，名称以最终交付消息为准。把这一份 `.bundle` 文件通过 RDP、共享盘或移动介质复制到服务器原 `YLQ_test` 的同级目录。服务器目录建议为：

```text
Wsn1
├── YLQ_test                 # 旧项目和旧结果，保持不动
├── ExposedPath_Q0_*.bundle  # 本机交付包
└── YLQ_test_q0_v141         # 已有 Q0 工作目录，含未跟踪的 r1/r2/r3/r4/r5/r6/r7/r8/r9/r10
```

先在服务器 PowerShell 中确认不存在尚未提交的受跟踪修改，并为服务器临时提交建立备份分支：

```powershell
Set-Location ".\YLQ_test_q0_v141"
git status --short --branch
$TrackedDirty = git status --porcelain=v1 --untracked-files=no
if ($TrackedDirty) { throw "存在未保存的受跟踪修改，停止更新" }
$BeforeUpdate = git rev-parse HEAD
$FrozenImplementation = "e44777e8e8ae0eb4d4dcf3f74980954dc6627bf1"
git branch "backup/server-before-$($BeforeUpdate.Substring(0,8))" $BeforeUpdate
git fetch "..\ExposedPath_Q0_实际文件名.bundle" codex/gate6-canonical-baseline
git reset --hard FETCH_HEAD
$CheckoutCommit = (git rev-parse HEAD).Trim()
# unified provenance：不再要求 HEAD == FrozenImplementation；checkout 允许是 frozen 之后的 runbook-only docs commit
if (@(git status --porcelain=v1 --untracked-files=no).Count -ne 0) { throw "tracked working tree 不 clean" }
git merge-base --is-ancestor $FrozenImplementation $CheckoutCommit
if ($LASTEXITCODE -ne 0) { throw "frozen implementation 不是 checkout HEAD 的 ancestor：$FrozenImplementation" }
$ProvenanceDelta = @(git diff --name-only "$FrozenImplementation..$CheckoutCommit")
if ($ProvenanceDelta.Count -ne 1 -or $ProvenanceDelta[0] -ne "docs/v1_4_1/gate6_windows_server_runbook.md") {
    throw "frozen..checkout 的 committed delta 必须且只能是 docs/v1_4_1/gate6_windows_server_runbook.md：$($ProvenanceDelta -join ', ')"
}
$FrozenImplementation
$CheckoutCommit
```

`git reset --hard` 只能在上述 tracked-dirty 检查为空、备份分支已建立后执行；它不会删除未跟踪的 `engineering_evidence/r1、r2、r3、r4、r5、r6、r7、r8、r9、r10`。严禁追加 `git clean`。更新后必须核对 unified provenance：tracked tree clean（`git status --porcelain=v1 --untracked-files=no` 为空，`engineering_evidence/*` 等 untracked evidence 不构成失败）、`$FrozenImplementation` 是 checkout HEAD 的 ancestor，且 `frozen..checkout` committed delta 恰好只有 `docs/v1_4_1/gate6_windows_server_runbook.md`。任一不满足即 STOP，不得继续编译或采集。不再要求 `HEAD == $FrozenImplementation`，也不得把后续 runbook-only docs commit 当作 implementation commit。

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

开始前应确保工作区位于 `codex/gate6-canonical-baseline`，并满足 §0 冻结的 unified provenance：`$FrozenImplementation = e44777e8e8ae0eb4d4dcf3f74980954dc6627bf1`（Gate 6 Missing-Corr oracle amendment v0.2 的 unified implementation commit）是 checkout HEAD 的 ancestor、tracked tree clean（`git status --porcelain=v1 --untracked-files=no` 为空）、且 `frozen..checkout` committed delta 恰好只有 `docs/v1_4_1/gate6_windows_server_runbook.md`。checkout HEAD 允许是 frozen implementation 之后的 approved runbook-only docs commit，不要求等于 frozen，也不得被当作 implementation commit。禁止覆盖已有输出；失败后使用新的 `run-id` 和新目录重跑，保留失败现场。禁止 retry/tuning：不得依据上一轮结果调整参数、时长、buffer、stream 或 policy 后重跑同一 case。

> **历史记录（2026-09-17 construction amendment 轮次，非当前 provenance 断言）：** 该轮 implementation commit 为 `2e81f6f9a9ec590d37fb01be9e31f2251645c5d1`（`docs/v1_4_1/gate6_construction_amendment_v0_1.md`，`APPLY = {Q0-KERNEL-MEMOP-001}`）；offline validation=`PASS`（targeted tests `70 passed`、Q0 offline regression `199 passed`、`--list-cases` 21/21），server validation=`NOT_STARTED`。此前“`Q0-KERNEL-MEMOP-001` platform construction blocked”的结论已被 formal-shape 配对 evidence 取代，原 construction failure 不再作为平台 incapable 证据。Gate 6 仍保持 `FAIL`、Q0 仍保持 `NOT_RUN`。当前正式 provenance 为 unified provenance：`$FrozenImplementation = e44777e8e8ae0eb4d4dcf3f74980954dc6627bf1`（Gate 6 Missing-Corr oracle amendment v0.2 的 unified implementation commit，见 §0/§1/§3）；上面这个旧 implementation commit 仅作历史记录，不得用作当前 workflow 的 identity 断言。
>
> 第 3 节及后续 r11 **当前仍一律禁止执行**。amendment 只批准 `Q0-KERNEL-MEMOP-001` 的 pre-capture same-kernel warm-up policy，不授权任何服务器实验；只有取得用户对“在该平台执行完整 21 real + 2 synthetic Q0”的单独书面批准，才允许执行第 3 节。construction amendment 获批或 construction admission PASS 本身都不等于 Gate 6 PASS、Q0 PASS 或 Gate 9 正式平台资格。`EP-G6-07` Candidate 路线保持暂停。

### 1.1 正式 native invocation 的 measurement initialization（amendment 冻结）

execution manifest / run manifest 版本为 `exposedpath-q0-execution/0.2.1` / `exposedpath-q0-run/0.2.1`。正式 native case 必须显式携带且只携带一次：

```text
--measurement-initialization <POLICY>
```

- `Q0-KERNEL-MEMOP-001` → `PRE_CAPTURE_SAME_KERNEL_WARMUP`（capture/request 之前对同一个 `q0_spin_kernel` 做一次预热，duration 与 measured invocation 同源，完成后 `cudaStreamSynchronize(measured_kernel_stream)`；不新增 event/gate，正式路径不写 `EXPOSEDPATH_DIAGNOSTIC_V1`）。
- 其余 20 个 native real case → `NONE`。
- 2 个 synthetic boundary case 仍是 `NONE`，且不由本手册采集 raw。
- `--list-cases` 与 `--environment-json` 不要求也不接受该 policy（保持 early-return）。
- missing / unknown / duplicate policy = STOP（binary 以非零码退出），不得手工补写 argv、不得静默按“无初始化”执行。
- policy 由 `prepare-q0-run` 依据 manifest 写入每个 case 的 `command_argv`，并记录进 case provenance；不要手工编辑 argv 或 receipt。

Engineering diagnostic 命令继续使用原有 diagnostic argv（例如 §2.12～§2.16 的 `--diagnostic-h2d-bytes` / `--diagnostic-d2h-bytes` / `--diagnostic-kernel-ms` / `--diagnostic-warmup-kernel` 与 formalshape run-id），**不得混用 formal `--measurement-initialization`**；两者互斥，混用会被 binary 直接拒绝。这些 diagnostic 结果只属 Engineering，不能作为正式 Q0 证据，也不能替代任何 Q0 case。

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

## 2.5 使用现有 r3 做只读范围诊断

代码更新后，先检查已有 r3，不修改其 Raw、SQLite、receipt 或 manifest。诊断输出写入新的同级派生目录：

```powershell
$Q0Root = Resolve-Path .
$R3SqliteCandidates = @(
    Get-ChildItem (Join-Path $Q0Root "engineering_evidence") -Recurse -File -Filter "trace.sqlite" |
        Where-Object { $_.Directory.Name -eq "Q0-STREAM-001" -and $_.FullName -match "(?i)r3" }
)
$R3SqliteCandidates | Select-Object FullName
if ($R3SqliteCandidates.Count -ne 1) { throw "无法唯一定位 r3/Q0-STREAM-001；请先核对上面列出的路径" }
$R3Case = $R3SqliteCandidates[0].Directory.FullName
$R3Raw = Join-Path $R3Case "trace.nsys-rep"
$R3Sqlite = $R3SqliteCandidates[0].FullName
$R3Manifest = Join-Path $R3Case "source_manifest.json"
$R3Receipt = Get-Content -LiteralPath (Join-Path $R3Case "collection_receipt.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$CodeShort = git rev-parse --short=8 HEAD
$R3Diag = Join-Path $Q0Root "engineering_evidence\q0_compat_diagnostics\r3-stream-$CodeShort"

& $Python -m exposedpath_v141 inspect-sqlite --sqlite $R3Sqlite --output-dir $R3Diag --data-role Engineering --raw-sha256 (Get-FileHash -LiteralPath $R3Raw -Algorithm SHA256).Hash --collector-version ([string]$R3Receipt.environment.nsight_systems) --source-manifest $R3Manifest
if ($LASTEXITCODE -ne 0) { throw "r3 目标 observation 仍未通过；保留诊断并停止" }
$R3Report = Get-Content -LiteralPath (Join-Path $R3Diag "observation_report.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$R3Invalid = @($R3Report.validity.issues | Where-Object level -eq "invalid")
$R3Harness = @($R3Report.validity.issues | Where-Object code -eq "HARNESS_SYNC_RUNTIME_MAPPING_NOT_UNIQUE")
if ($R3Invalid.Count -ne 0) { throw "r3 仍存在目标 observation invalid" }
if ($R3Harness.Count -ne 1 -or $R3Harness[0].detail.offending[0].correlation_id -ne 135 -or $R3Harness[0].detail.offending[0].scope -ne "HARNESS_OUTSIDE_REQUEST") { throw "r3 harness 尾部同步诊断不符合预期" }
```

已知 r3 的目标 `cudaStreamSynchronize`（`correlationId=133`）和 request 后显式 `cudaDeviceSynchronize`（`correlationId=134`）均唯一映射；另有一条 request 结束后的尾部同步（`correlationId=135`）没有 runtime 候选。该记录只能表述为与 profiler/harness teardown 时间一致，不能在没有 API 映射时断言其具体来源。新版 analyzer 应完整保留它并标为 `HARNESS_OUTSIDE_REQUEST` warning，不得让它污染目标 request validity，也不得忽略目标 request 内的证据缺失。诊断通过仍不把已有 r3 升级为 Q0 PASS。

## 2.6 使用现有 r4 EMPTY 做只读 lazy-export 诊断

r4 已在批量阶段的 `Q0-EMPTY-001` 停止，必须保持失败现场。更新代码后只读取其 SQLite，并把新输出写入独立诊断目录：

```powershell
$R4EmptyCandidates = @(
    Get-ChildItem (Join-Path $Q0Root "engineering_evidence") -Recurse -File -Filter "trace.sqlite" |
        Where-Object { $_.Directory.Name -eq "Q0-EMPTY-001" -and $_.FullName -match "(?i)r4" }
)
$R4EmptyCandidates | Select-Object FullName
if ($R4EmptyCandidates.Count -ne 1) { throw "无法唯一定位 r4/Q0-EMPTY-001" }
$R4Case = $R4EmptyCandidates[0].Directory.FullName
$R4Sqlite = $R4EmptyCandidates[0].FullName
$R4Raw = Join-Path $R4Case "trace.nsys-rep"
$R4Manifest = Join-Path $R4Case "source_manifest.json"
$R4Receipt = Get-Content -LiteralPath (Join-Path $R4Case "collection_receipt.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$R4Diag = Join-Path $Q0Root "engineering_evidence\q0_compat_diagnostics\r4-empty-$CodeShort"

& $Python -m exposedpath_v141 inspect-sqlite --sqlite $R4Sqlite --output-dir (Join-Path $R4Diag "inspect") --data-role Engineering --raw-sha256 (Get-FileHash -LiteralPath $R4Raw -Algorithm SHA256).Hash --collector-version ([string]$R4Receipt.environment.nsight_systems) --source-manifest $R4Manifest
if ($LASTEXITCODE -ne 0) { throw "r4 EMPTY observation 未通过" }
& $Python -m exposedpath_v141 convert-sqlite --sqlite $R4Sqlite --output-dir (Join-Path $R4Diag "canonical") --data-role Engineering --raw-sha256 (Get-FileHash -LiteralPath $R4Raw -Algorithm SHA256).Hash --collector-version ([string]$R4Receipt.environment.nsight_systems) --source-manifest $R4Manifest
if ($LASTEXITCODE -ne 0) { throw "r4 EMPTY Canonical 未通过" }
& $Python -m exposedpath_v141 analyze-s --canonical-manifest (Join-Path $R4Diag "canonical\canonical_manifest.json") --output-dir (Join-Path $R4Diag "s")
if ($LASTEXITCODE -notin 0,2,3) { throw "r4 EMPTY S 执行异常" }
& $Python -m exposedpath_v141 analyze-ab --canonical-manifest (Join-Path $R4Diag "canonical\canonical_manifest.json") --s-manifest (Join-Path $R4Diag "s\s_manifest.json") --output-dir (Join-Path $R4Diag "ab")
if ($LASTEXITCODE -notin 0,2,3) { throw "r4 EMPTY A/B 执行异常" }
& $Python -m exposedpath_v141 evaluate-q0-real-case --case Q0-EMPTY-001 --canonical-manifest (Join-Path $R4Diag "canonical\canonical_manifest.json") --s-manifest (Join-Path $R4Diag "s\s_manifest.json") --ab-manifest (Join-Path $R4Diag "ab\ab_manifest.json") --collection-receipt (Join-Path $R4Case "collection_receipt.json") --output-dir (Join-Path $R4Diag "evidence")
if ($LASTEXITCODE -ne 0) { throw "r4 EMPTY 独立对照未通过" }
```

验收：observation 与 Canonical 返回 0；目标 `S_EMPTY` 为 `VALID_EMPTY`，B 为 `B_NOT_APPLICABLE`，独立 evaluator 为 `REAL_CASE_PASS`。这只是兼容性诊断，不改变 r4 的失败资格。当前还必须继续执行 2.7 的 r5 只读诊断，不能跳过历史失败现场直接重跑。

## 2.7 使用现有 r5 PTDS 做只读 instrumentation 诊断

r5 已在 `Q0-DEFAULT-PTDS-001` 因两个同 identity `full_request` 停止。新版只修 CUDA microbench，不放宽 analyzer；因此旧 r5 SQLite 在新版下仍必须 fail closed。下面命令只读取 r5，并将新报告写入独立目录：

```powershell
$Q0Root = Resolve-Path .
$CodeShort = git rev-parse --short=8 HEAD
$R5PtdsCandidates = @(
    Get-ChildItem (Join-Path $Q0Root "engineering_evidence") -Recurse -File -Filter "trace.sqlite" |
        Where-Object { $_.Directory.Name -eq "Q0-DEFAULT-PTDS-001" -and $_.FullName -match "(?i)r5" }
)
$R5PtdsCandidates | Select-Object FullName
if ($R5PtdsCandidates.Count -ne 1) { throw "无法唯一定位 r5/Q0-DEFAULT-PTDS-001" }
$R5Case = $R5PtdsCandidates[0].Directory.FullName
$R5Sqlite = $R5PtdsCandidates[0].FullName
$R5Raw = Join-Path $R5Case "trace.nsys-rep"
$R5Manifest = Join-Path $R5Case "source_manifest.json"
$R5Receipt = Get-Content -LiteralPath (Join-Path $R5Case "collection_receipt.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$R5SqliteHashBefore = (Get-FileHash -LiteralPath $R5Sqlite -Algorithm SHA256).Hash
$R5Diag = Join-Path $Q0Root "engineering_evidence\q0_compat_diagnostics\r5-ptds-$CodeShort"

& $Python -m exposedpath_v141 inspect-sqlite --sqlite $R5Sqlite --output-dir $R5Diag --data-role Engineering --raw-sha256 (Get-FileHash -LiteralPath $R5Raw -Algorithm SHA256).Hash --collector-version ([string]$R5Receipt.environment.nsight_systems) --source-manifest $R5Manifest
if ($LASTEXITCODE -ne 3) { throw "r5 PTDS 应继续 fail closed，但退出码不是 3" }
$R5Report = Get-Content -LiteralPath (Join-Path $R5Diag "observation_report.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$R5Scope = $R5Report.derived_checks.target_request_scope
$R5Mapping = @($R5Report.validity.issues | Where-Object code -eq "SYNC_RUNTIME_MAPPING_NOT_UNIQUE")
if ($R5Report.validity.status -ne "invalid") { throw "r5 PTDS 不应被升级为 valid" }
if ($R5Scope.reason -ne "TARGET_REQUEST_NOT_UNIQUE" -or $R5Scope.structured_request_count -ne 2 -or $R5Scope.matching_request_count -ne 2) { throw "r5 重复 request 诊断不符合已知失败现场" }
if ($R5Mapping.Count -ne 1 -or $R5Mapping[0].detail.offending[0].correlation_id -ne 133 -or $R5Mapping[0].detail.offending[0].scope -ne "GLOBAL_TRACE" -or $R5Mapping[0].detail.offending[0].runtime_match_count -ne 0) { throw "r5 尾部同步诊断不符合已知失败现场" }
if ((Get-FileHash -LiteralPath $R5Sqlite -Algorithm SHA256).Hash -ne $R5SqliteHashBefore) { throw "r5 SQLite 被意外修改" }
```

验收：r5 仍明确报告两个匹配 request，并将尾部 `correlationId=133` 保守归为 `GLOBAL_TRACE`；SQLite 哈希保持不变。这证明 analyzer 的唯一性规则没有被放宽。r6 已验证重复 request 修复，但暴露了 query 轮询问题；继续执行 2.8。

## 2.8 使用现有 r6 PTDS 做只读 query-polling 诊断

r6 已确认 target request 唯一且 request 后尾部同步能归为 `HARNESS_OUTSIDE_REQUEST`，但 PTDS worker 的 `cudaStreamQuery` 轮询在 request 内产生 31 条无 Runtime 映射的 synchronization activity。新版只移除该轮询，不修改 analyzer，因此旧 r6 仍必须 fail closed：

```powershell
$Q0Root = Resolve-Path .
$CodeShort = git rev-parse --short=8 HEAD
$R6PtdsCandidates = @(
    Get-ChildItem (Join-Path $Q0Root "engineering_evidence") -Recurse -File -Filter "trace.sqlite" |
        Where-Object { $_.Directory.Name -eq "Q0-DEFAULT-PTDS-001" -and $_.FullName -match "(?i)r6" }
)
$R6PtdsCandidates | Select-Object FullName
if ($R6PtdsCandidates.Count -ne 1) { throw "无法唯一定位 r6/Q0-DEFAULT-PTDS-001" }
$R6Case = $R6PtdsCandidates[0].Directory.FullName
$R6Sqlite = $R6PtdsCandidates[0].FullName
$R6Raw = Join-Path $R6Case "trace.nsys-rep"
$R6Manifest = Join-Path $R6Case "source_manifest.json"
$R6Receipt = Get-Content -LiteralPath (Join-Path $R6Case "collection_receipt.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$R6SqliteHashBefore = (Get-FileHash -LiteralPath $R6Sqlite -Algorithm SHA256).Hash
$R6Diag = Join-Path $Q0Root "engineering_evidence\q0_compat_diagnostics\r6-ptds-$CodeShort"

& $Python -m exposedpath_v141 inspect-sqlite --sqlite $R6Sqlite --output-dir $R6Diag --data-role Engineering --raw-sha256 (Get-FileHash -LiteralPath $R6Raw -Algorithm SHA256).Hash --collector-version ([string]$R6Receipt.environment.nsight_systems) --source-manifest $R6Manifest
if ($LASTEXITCODE -ne 3) { throw "r6 PTDS 应继续 fail closed，但退出码不是 3" }
$R6Report = Get-Content -LiteralPath (Join-Path $R6Diag "observation_report.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$R6Issues = @($R6Report.validity.issues)
$R6ScopeErrors = @($R6Issues | Where-Object code -eq "TARGET_REQUEST_SCOPE_UNRESOLVED")
$R6Mapping = @($R6Issues | Where-Object code -eq "SYNC_RUNTIME_MAPPING_NOT_UNIQUE")
$R6TargetUnmapped = @($R6Mapping.detail.offending | Where-Object scope -eq "TARGET_REQUEST")
$R6HarnessWarnings = @($R6Issues | Where-Object code -eq "HARNESS_SYNC_RUNTIME_MAPPING_NOT_UNIQUE")
$ExpectedR6CorrelationIds = @(129) + @(133..162)
$ActualR6CorrelationIds = @($R6TargetUnmapped.correlation_id | Sort-Object)
if ($R6Report.validity.status -ne "invalid") { throw "r6 PTDS 不应被升级为 valid" }
if ($R6ScopeErrors.Count -ne 0) { throw "r6 不应重新出现 target request 唯一性错误" }
if ($R6TargetUnmapped.Count -ne 31 -or @($R6TargetUnmapped | Where-Object runtime_match_count -ne 0).Count -ne 31) { throw "r6 query 轮询诊断数量不符合失败现场" }
if (@(Compare-Object $ExpectedR6CorrelationIds $ActualR6CorrelationIds).Count -ne 0) { throw "r6 query 轮询 correlation 集合不符合失败现场" }
if ($R6HarnessWarnings.Count -lt 1) { throw "r6 request 后尾部同步未保留为 harness warning" }
if ((Get-FileHash -LiteralPath $R6Sqlite -Algorithm SHA256).Hash -ne $R6SqliteHashBefore) { throw "r6 SQLite 被意外修改" }
```

验收：r6 不再出现重复 target request；31 条 request 内未映射同步仍使旧 trace invalid；request 外尾部同步保持 warning；SQLite 哈希不变。r7 已验证 host callback 路径继续推进，但暴露 target resolver 对 prior invocation 的错误限制；继续执行 2.9。

## 2.9 使用现有 r7 invocation-bleed 做只读 scope 诊断

r7 的 `Q0-INVOCATION-BLEED-001` 同时包含一个 prior request 和一个唯一 target request。旧 analyzer 因 `structured_request_count=2` 错误 fail closed；新版按完整 target identity 过滤后，应解析唯一 target，并把 request 后 correlation 131 按既有规则归为 harness warning：

```powershell
$Q0Root = Resolve-Path .
$CodeShort = git rev-parse --short=8 HEAD
$R7Candidates = @(
    Get-ChildItem (Join-Path $Q0Root "engineering_evidence") -Recurse -File -Filter "trace.sqlite" |
        Where-Object { $_.Directory.Name -eq "Q0-INVOCATION-BLEED-001" -and $_.FullName -match "(?i)r7" }
)
$R7Candidates | Select-Object FullName
if ($R7Candidates.Count -ne 1) { throw "无法唯一定位 r7/Q0-INVOCATION-BLEED-001" }
$R7Case = $R7Candidates[0].Directory.FullName
$R7Sqlite = $R7Candidates[0].FullName
$R7Raw = Join-Path $R7Case "trace.nsys-rep"
$R7Manifest = Join-Path $R7Case "source_manifest.json"
$R7Receipt = Get-Content -LiteralPath (Join-Path $R7Case "collection_receipt.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$R7SqliteHashBefore = (Get-FileHash -LiteralPath $R7Sqlite -Algorithm SHA256).Hash
$R7Diag = Join-Path $Q0Root "engineering_evidence\q0_compat_diagnostics\r7-invocation-$CodeShort"

& $Python -m exposedpath_v141 inspect-sqlite --sqlite $R7Sqlite --output-dir $R7Diag --data-role Engineering --raw-sha256 (Get-FileHash -LiteralPath $R7Raw -Algorithm SHA256).Hash --collector-version ([string]$R7Receipt.environment.nsight_systems) --source-manifest $R7Manifest
if ($LASTEXITCODE -ne 0) { throw "r7 invocation-bleed 在新版 resolver 下未通过 observation" }
$R7Report = Get-Content -LiteralPath (Join-Path $R7Diag "observation_report.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$R7Scope = $R7Report.derived_checks.target_request_scope
$R7ScopeErrors = @($R7Report.validity.issues | Where-Object code -eq "TARGET_REQUEST_SCOPE_UNRESOLVED")
$R7HarnessWarnings = @($R7Report.validity.issues | Where-Object code -eq "HARNESS_SYNC_RUNTIME_MAPPING_NOT_UNIQUE")
$R7Correlation131 = @($R7HarnessWarnings.detail.offending | Where-Object correlation_id -eq 131)
if ($R7Report.validity.status -ne "valid") { throw "r7 invocation-bleed 应只读重放为 valid" }
if ($R7Scope.status -ne "RESOLVED" -or $R7Scope.request_id -ne "Q0-INVOCATION-BLEED-001") { throw "r7 唯一 target request 未正确解析" }
if ($R7ScopeErrors.Count -ne 0) { throw "r7 不应继续报告 target request 不唯一" }
if ($R7Correlation131.Count -ne 1 -or $R7Correlation131[0].scope -ne "HARNESS_OUTSIDE_REQUEST" -or $R7Correlation131[0].runtime_match_count -ne 0) { throw "r7 correlation 131 未按既有 request 外规则分类" }
if ((Get-FileHash -LiteralPath $R7Sqlite -Algorithm SHA256).Hash -ne $R7SqliteHashBefore) { throw "r7 SQLite 被意外修改" }
```

验收：唯一 target request 成功解析；prior request 保留但不制造歧义；correlation 131 仅作为 request 外 warning；SQLite 哈希不变。该只读成功不升级 r7 的失败资格。服务器后续 r8 已越过此处，证明该修复生效。

## 2.10 r8 Graph fault 失败现场与 r9 边界

r8 已完成 `Q0-STREAM-001` smoke、21/21 native collection、21/21 源 Canonical，以及 `Q0-MISSING-CORR-001`、`Q0-DROPPED-001` 两个故障副本；随后在 `Q0-GRAPH-UNSUPPORTED-001` 停止。这里的“21/21 源 Canonical valid”只表示通用 observation 与转换有效，不表示 Graph fault 的前态充分。

r8 默认采集只有 graph-level trace，没有 node-level activity，因此 Graph 源 Canonical 的 `device_activity` 为零，`REMOVE_GRAPH_NODE_MAPPING` 按 fail-closed 规则零命中。独立 Engineering 诊断仅增加 `--cuda-graph-trace=node` 后，真实 graph kernel、`graph_id`、`graph_node_id` 与 node events 均可观察，现有 Canonical adapter 和 fault selector 能完成一次明确 mutation。因此新代码只给 `Q0-GRAPH-UNSUPPORTED-001` 增加该采集参数；其他 native case 不变。

r8 必须保持失败现场，不覆盖、不续跑、不升级资格。该独立诊断只证明采集修复方向，不是完整 Q0 证据。服务器已完成上述诊断时，更新代码后无需重复 2.5～2.9，直接从下面的新 r9 开始；r1～r8 均不得执行 `git clean` 或人工改写。

## 2.11 使用现有 r9 DEVICE 做只读 evaluator 诊断

r9 已证明 Graph case 的 node tracing 参数进入正式执行计划，但批量运行在 `Q0-DEVICE-001` 的独立 evaluator 停止。唯一 mismatch 是同一 wait-set 的枚举顺序不同：oracle 为 `['K_A', 'K_B']`，真实 S 为 `['K_B', 'K_A']`。`W(s)` 是活动集合，不以 JSON 数组顺序表达 CUDA dependency 顺序；新版 evaluator 只对 `wait_set_activity_labels` 使用无序且无重复的精确成员比较，其他 list 字段仍保持原比较语义。

更新代码后，先只读使用 r9 已生成的 Canonical、S、A/B 与 receipt，输出写入新的诊断目录：

```powershell
$Q0Root = Resolve-Path .
$CodeShort = git rev-parse --short=8 HEAD
$R9DeviceCandidates = @(
    Get-ChildItem (Join-Path $Q0Root "engineering_evidence") -Recurse -Directory -Filter "Q0-DEVICE-001" |
        Where-Object {
            $_.FullName -match "(?i)r9" -and
            (Test-Path (Join-Path $_.FullName "canonical\canonical_manifest.json")) -and
            (Test-Path (Join-Path $_.FullName "s\s_manifest.json")) -and
            (Test-Path (Join-Path $_.FullName "ab\ab_manifest.json")) -and
            (Test-Path (Join-Path $_.FullName "collection_receipt.json"))
        }
)
$R9DeviceCandidates | Select-Object FullName
if ($R9DeviceCandidates.Count -ne 1) { throw "无法唯一定位 r9/Q0-DEVICE-001 完整派生输入" }
$R9Case = $R9DeviceCandidates[0].FullName
$R9Raw = Join-Path $R9Case "trace.nsys-rep"
$R9RawHashBefore = (Get-FileHash -LiteralPath $R9Raw -Algorithm SHA256).Hash
$R9Diag = Join-Path $Q0Root "engineering_evidence\q0_compat_diagnostics\r9-device-evaluator-$CodeShort"

& $Python -m exposedpath_v141 evaluate-q0-real-case --case Q0-DEVICE-001 --canonical-manifest (Join-Path $R9Case "canonical\canonical_manifest.json") --s-manifest (Join-Path $R9Case "s\s_manifest.json") --ab-manifest (Join-Path $R9Case "ab\ab_manifest.json") --collection-receipt (Join-Path $R9Case "collection_receipt.json") --output-dir $R9Diag
if ($LASTEXITCODE -ne 0) { throw "r9 DEVICE 只读 evaluator 诊断未通过" }
if ((Get-FileHash -LiteralPath $R9Raw -Algorithm SHA256).Hash -ne $R9RawHashBefore) { throw "r9 Raw 被意外修改" }
$R9Evidence = Get-Content -LiteralPath (Join-Path $R9Diag "q0_real_evidence.json") -Raw -Encoding UTF8 | ConvertFrom-Json
if ($R9Evidence.verdict -ne "REAL_CASE_PASS") { throw "r9 DEVICE 未得到 REAL_CASE_PASS" }
```

验收：新诊断返回 `REAL_CASE_PASS`，且 r9 Raw 哈希不变。该结果仅证明 evaluator 修复能正确重放既有证据，不把 r9 升级为完整 Q0；r9 保持失败现场。正式重跑必须使用全新 r10，r1～r9 均不得覆盖、续跑或执行 `git clean`。

## 2.12 已完成的 KERNEL-MEMOP activity-ownership 诊断（历史步骤，不要重跑）

> 本节已经执行并形成不可变失败现场。真实结果确认 activity ownership 修复成功，但设备活动仍未重叠。不要覆盖或续跑本节目录；当前唯一允许执行的服务器步骤是 §2.13。

r10 在 `Q0-KERNEL-MEMOP-001` 停止：wait-set、`MEMCPY_B` terminal 和 B 均正确，但 4 KiB H2D 在真实 4090 上晚于 35 ms kernel 才开始，`mixed_ns=0`。第一版 512 MiB/10 ms diagnostic 仍显示 kernel 先完成、copy 晚约 108159 ns 才开始。第二版 memcpy-first diagnostic 也必须保留：`MEMCPY_B=22241366..73604625 ns`、`KERNEL_A=74688941..84689831 ns`，二者相隔 1084316 ns，仍无重叠且 terminal 变为 `KERNEL_A`。

第二版的 Runtime API 时间进一步排除了“长 H2D 提交阻塞 Host”这一假设：`cudaMemcpyAsync` 仅为 `21248593..21307992 ns`（59399 ns），随后同一 `globalTid` 的 `cudaLaunchKernel` 却为 `21314302..74556590 ns`（53242288 ns）。该 launch 调用覆盖了几乎整个 copy 设备区间，且 kernel 设备活动在 launch 返回后才开始，说明该 Windows/WDDM 栈上的同 Host 线程顺序提交发生了序列化。

第三版不再扩大 buffer，也不改变 stream、标签或 sync。coordinator 与 kernel worker 先通过纯 Host 条件变量同时放行：coordinator 向既有 `r.second` 提交 512 MiB `MEMCPY_B`，worker 向既有 `r.first` 提交 10 ms `KERNEL_A`；coordinator 等待 kernel launch 调用返回后立即进入原 `S_DEVICE`，并在该同步完成后才 join worker。该结构不增加 CUDA query/event/sync，唯一 request/decode 仍由 coordinator 创建并覆盖 worker 生命周期。它只验证分离 Host 提交路径能否绕开现场序列化；真实重叠仍必须由本节 diagnostic 证明。

第三版 concurrent-host diagnostic 已证明 `KERNEL_A` 与 `MEMCPY_B` 的 submission evidence 均为 `PROVEN`，但 S 层只把 `MEMCPY_B` 归入 decode。第四版增加立即结束的 `WORKER_KERNEL_MEMOP` marker 后，真实时间线进一步证明现有 `KERNEL_A` marker 已在同一 worker 线程完整覆盖 launch，而旧 S resolver 只读取 request/phase，导致它仍以 `INVOCATION_BOUNDARY_INVALID` fail closed。新实现只让完整、同线程、完整覆盖 API 且 identity 一致的 activity marker 参与 device activity ownership；sync/event ownership、A 窗口、oracle、A/B 和 Q0 expected 均不改变。四份失败 diagnostic 都必须保留。

不要直接开始完整 r11。先创建独立 Engineering diagnostic，只运行该 case：

```powershell
$Q0Root = Resolve-Path .
$DiagRunId = "q0-win-4090-YYYYMMDD-kernel-memop-activity-ownership-diag"  # 替换日期；必须是全新目录
$DiagOut = Join-Path $Q0Root "engineering_evidence\q0_diagnostics\$DiagRunId"
$DiagBinary = Join-Path $DiagOut "bin\exposedpath_q0.exe"
$Nsys = "C:\Program Files\NVIDIA Corporation\Nsight Systems 2026.2.1\target-windows-x64\nsys.exe"
$GpuSelector = "GPU-替换为nvidia-smi显示的完整UUID"
$Nvcc = (Get-Command nvcc).Source

cmd /d /s /c "`"$VcVars`" -vcvars_ver=14.39 && where cl && `"$Python`" -m exposedpath_v141 build-q0-microbench --nvcc `"$Nvcc`" --output `"$DiagBinary`" --platform windows"
if ($LASTEXITCODE -ne 0) { throw "KERNEL-MEMOP diagnostic CUDA 编译失败" }
& $Python -m exposedpath_v141 prepare-q0-run --output-dir (Join-Path $DiagOut "run") --binary $DiagBinary --nsys $Nsys --platform windows --run-id $DiagRunId --cuda-visible-device $GpuSelector
if ($LASTEXITCODE -ne 0) { throw "KERNEL-MEMOP diagnostic 准备失败" }

$DiagRunManifest = Join-Path $DiagOut "run\q0_run_manifest.json"
$DiagCaseId = "Q0-KERNEL-MEMOP-001"
& $Python -m exposedpath_v141 execute-q0-case --run-manifest $DiagRunManifest --case $DiagCaseId
if ($LASTEXITCODE -ne 0) { throw "KERNEL-MEMOP diagnostic 采集失败" }

$DiagCase = Join-Path $DiagOut "run\cases\$DiagCaseId"
$DiagRaw = Join-Path $DiagCase "trace.nsys-rep"
$DiagSqlite = Join-Path $DiagCase "trace.sqlite"
$DiagReceipt = Get-Content -LiteralPath (Join-Path $DiagCase "collection_receipt.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$DiagRawSha = (Get-FileHash -LiteralPath $DiagRaw -Algorithm SHA256).Hash
& $Nsys export --type sqlite --lazy=false --force-overwrite=false --output $DiagSqlite $DiagRaw
if ($LASTEXITCODE -ne 0) { throw "KERNEL-MEMOP diagnostic SQLite 导出失败" }
& $Python -m exposedpath_v141 convert-sqlite --sqlite $DiagSqlite --output-dir (Join-Path $DiagCase "canonical") --data-role Engineering --raw-sha256 $DiagRawSha --collector-version ([string]$DiagReceipt.environment.nsight_systems) --source-manifest (Join-Path $DiagCase "source_manifest.json")
if ($LASTEXITCODE -ne 0) { throw "KERNEL-MEMOP diagnostic Canonical 失败" }
& $Python -m exposedpath_v141 analyze-s --canonical-manifest (Join-Path $DiagCase "canonical\canonical_manifest.json") --output-dir (Join-Path $DiagCase "s")
if ($LASTEXITCODE -notin 0,2,3) { throw "KERNEL-MEMOP diagnostic S 执行异常" }
& $Python -m exposedpath_v141 analyze-ab --canonical-manifest (Join-Path $DiagCase "canonical\canonical_manifest.json") --s-manifest (Join-Path $DiagCase "s\s_manifest.json") --output-dir (Join-Path $DiagCase "ab")
if ($LASTEXITCODE -notin 0,2,3) { throw "KERNEL-MEMOP diagnostic A/B 执行异常" }
$DiagEvidenceDir = Join-Path $DiagOut "real_evidence\$DiagCaseId"
& $Python -m exposedpath_v141 evaluate-q0-real-case --case $DiagCaseId --canonical-manifest (Join-Path $DiagCase "canonical\canonical_manifest.json") --s-manifest (Join-Path $DiagCase "s\s_manifest.json") --ab-manifest (Join-Path $DiagCase "ab\ab_manifest.json") --collection-receipt (Join-Path $DiagCase "collection_receipt.json") --output-dir $DiagEvidenceDir
if ($LASTEXITCODE -ne 0) { throw "KERNEL-MEMOP diagnostic evaluator 未通过" }

$DiagObserved = Get-Content -LiteralPath (Join-Path $DiagEvidenceDir "real_observed.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$DiagKernel = $DiagObserved.cases[0].activity_intervals | Where-Object activity_label -eq "KERNEL_A"
$DiagMemcpy = $DiagObserved.cases[0].activity_intervals | Where-Object activity_label -eq "MEMCPY_B"
$DiagSync = $DiagObserved.cases[0].syncs | Where-Object sync_label -eq "S_DEVICE"
$DiagOverlapNs = [Math]::Min([int64]$DiagKernel.end_ns, [int64]$DiagMemcpy.end_ns) - [Math]::Max([int64]$DiagKernel.start_ns, [int64]$DiagMemcpy.start_ns)
$DiagEvidence = Get-Content -LiteralPath (Join-Path $DiagEvidenceDir "q0_real_evidence.json") -Raw -Encoding UTF8 | ConvertFrom-Json
if ($DiagOverlapNs -le 0) { throw "KERNEL_A 与 MEMCPY_B 没有真实时间重叠" }
if ([int64]$DiagSync.a_window.A_device_wait_kernel_memop_mixed_ns -le 0) { throw "mixed_ns 必须大于 0" }
if ($DiagSync.terminal.activity_label -ne "MEMCPY_B") { throw "terminal 必须保持 MEMCPY_B" }
if ($DiagEvidence.verdict -ne "REAL_CASE_PASS") { throw "diagnostic 必须得到 REAL_CASE_PASS" }
```

本节真实结果为：`S_DEVICE=VALID_NONEMPTY`、wait-set=`{MEMCPY_B,KERNEL_A}`，说明 ownership 修复已生效；但 `MEMCPY_B=26742751..57382403 ns`、`KERNEL_A=57811107..67811983 ns`，间隔 428704 ns，故 `mixed_ns=0`、terminal=`KERNEL_A`，evaluator 正确失败。该目录必须保留，不得升级为 Q0 证据。

## 2.13 已完成的 WDDM-enhanced KERNEL-MEMOP diagnostic（历史步骤，不要重跑）

本节已由管理员 PowerShell 以 diag-02 完成。Raw/SQLite/source manifest 哈希与 receipt 一致；目标 request 内获得 WDDM queue 可见性，但 HAGS 状态未确认且 packet 无 CUDA correlationId，因此 `causal_verdict=NOT_ESTABLISHED`。不要覆盖 diag-01/diag-02；当前唯一允许执行的步骤改为 §2.14。

先更新至本手册对应的新 commit/bundle，再在仓库目录执行。`$PriorDiagOut` 必须指向服务器上 §2.12 的原始 activity-ownership diagnostic 根目录，其中应存在 `bin\exposedpath_q0.exe`；不要指向回传到本地的精简副本。

```powershell
$Q0Root = Resolve-Path .
$Python = Join-Path $Q0Root ".venv\Scripts\python.exe"
$Nsys = "C:\Program Files\NVIDIA Corporation\Nsight Systems 2026.2.1\target-windows-x64\nsys.exe"
$GpuSelector = "GPU-替换为nvidia-smi显示的完整UUID"
$PriorDiagOut = "C:\替换为服务器上原activity-ownership-diagnostic目录"
$WddmBinary = Join-Path $PriorDiagOut "bin\exposedpath_q0.exe"
$WddmRunId = "q0-win-4090-YYYYMMDD-kernel-memop-wddm-diag-01"  # 替换实际日期
$WddmOut = Join-Path $Q0Root "engineering_evidence\q0_diagnostics\$WddmRunId"

if (-not (Test-Path -LiteralPath $WddmBinary -PathType Leaf)) { throw "找不到 §2.12 的原 binary" }
if (Test-Path -LiteralPath $WddmOut) { throw "WDDM diagnostic 目录已存在，禁止覆盖" }

& $Python -m exposedpath_v141 run-q0-wddm-diagnostic `
    --output-dir $WddmOut `
    --binary $WddmBinary `
    --nsys $Nsys `
    --run-id $WddmRunId `
    --cuda-visible-device $GpuSelector
if ($LASTEXITCODE -ne 0) { throw "WDDM diagnostic 执行失败；保留现场并停止" }

$WddmSummary = Get-Content -LiteralPath (Join-Path $WddmOut "wddm_summary.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$WddmReceipt = Get-Content -LiteralPath (Join-Path $WddmOut "wddm_diagnostic_receipt.json") -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $WddmSummary.diagnostic_only) { throw "必须是 diagnostic-only" }
if ($WddmSummary.data_role -ne "Engineering") { throw "必须是 Engineering" }
if ($WddmReceipt.q0_status -ne "NOT_RUN") { throw "WDDM diagnostic 不得升级 Q0" }
if ($WddmSummary.strict_cuda_wddm_mapping -ne $false) { throw "不得声称 CUDA-WDDM 严格映射" }
if ($WddmSummary.causal_verdict -ne "NOT_ESTABLISHED") { throw "不得输出硬件根因结论" }

Get-Content -LiteralPath (Join-Path $WddmOut "wddm_summary.json") -Raw -Encoding UTF8
```

入口会自动保存 `nsys_version.txt`、完整 `nsys_profile_help.txt`、筛选后的 `nsys_profile_help_wddm.txt`、`hags_status.json`、实际 collection/export argv、Raw、SQLite、两个 receipt、WDDM 表计数和 `wddm_timeline.json`。它会先核对当前安装版本的帮助输出确实包含 `wddm`、`--wddm-additional-events`、`--wddm-memory-trace` 和 `--wddm-backtraces`，缺任一参数即在采集前停止。

`TIMELINE_ATTRIBUTION_AVAILABLE` 只表示：在目标 request 的 PID 和时间窗内找到了带 context/engine 字段的 WDDM packet 记录。WDDM packet 没有 CUDA correlationId，因此只能做 PID/context/engine/time-window 下的归属推断，不能写成 CUDA activity 与 packet 一一对应。若 HAGS 未确认启用、WDDM 表为空或没有可归属目标 packet，`EVIDENCE_INSUFFICIENT` 就是本次合法结论，必须停止进一步根因推断。

diag-02 的标准 CUDA 时间线为：`cudaMemcpyAsync=26639965..26702789 ns`、`cudaLaunchKernel=27022422..62116191 ns`、H2D activity=`33435296..58635297 ns`、kernel activity=`63136725..73137628 ns`，两项 device activity 间隔 `4501428 ns`。WDDM Copy sequence 34 与 copy 时间吻合，CUDA-context sequence 53 与 kernel 时间邻近；后者只能作为时间归属推断，不能写成严格映射或具体根因。

## 2.14 已完成并停止：64 MiB H2D + 10 ms kernel 参数 diagnostic

本节只检验缩短 copy 后，kernel launch/device activity 是否仍等待 copy 完成。它不是 Q0 正例验收，不要求 terminal=`MEMCPY_B` 或 evaluator PASS。正常 Q0 继续固定 512 MiB H2D/10 ms kernel；本节使用独立入口、标准 `--trace=cuda,nvtx`，不采集 WDDM，不进入标准 Q0 run manifest。

新参数由 binary 严格限制为 64 MiB/10 ms，并要求 diagnostic 专用 run identity。必须用新 commit 重新编译一个独立 binary，不能复用 §2.12 的旧 binary：

```powershell
$Q0Root = Resolve-Path .
$Python = Join-Path $Q0Root ".venv\Scripts\python.exe"
$Nsys = "C:\Program Files\NVIDIA Corporation\Nsight Systems 2026.2.1\target-windows-x64\nsys.exe"
$GpuSelector = "GPU-替换为nvidia-smi显示的完整UUID"
$VcVars = "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
$Nvcc = (Get-Command nvcc).Source
$CodeShort = (git rev-parse --short HEAD).Trim()
$SizeBuild = Join-Path $Q0Root "engineering_evidence\q0_diagnostic_builds\kernel-memop-size-$CodeShort"
$SizeBinary = Join-Path $SizeBuild "exposedpath_q0.exe"
$SizeRunId = "q0-win-4090-YYYYMMDD-kernel-memop-size-diag-64m-10ms-01"  # 替换实际日期
$SizeOut = Join-Path $Q0Root "engineering_evidence\q0_diagnostics\$SizeRunId"

if (Test-Path -LiteralPath $SizeBuild) { throw "diagnostic build 目录已存在，禁止覆盖" }
if (Test-Path -LiteralPath $SizeOut) { throw "diagnostic 输出目录已存在，禁止覆盖" }
New-Item -ItemType Directory -Path $SizeBuild | Out-Null

cmd /d /s /c "`"$VcVars`" -vcvars_ver=14.39 && where cl && `"$Python`" -m exposedpath_v141 build-q0-microbench --nvcc `"$Nvcc`" --output `"$SizeBinary`" --platform windows"
if ($LASTEXITCODE -ne 0) { throw "64 MiB/10 ms diagnostic CUDA 编译失败" }

& $Python -m exposedpath_v141 run-q0-kernel-memop-diagnostic `
    --output-dir $SizeOut `
    --binary $SizeBinary `
    --nsys $Nsys `
    --run-id $SizeRunId `
    --cuda-visible-device $GpuSelector
if ($LASTEXITCODE -ne 0) { throw "64 MiB/10 ms diagnostic 失败；保留现场并停止" }

git rev-parse HEAD | Set-Content -LiteralPath (Join-Path $SizeOut "code_commit.txt") -Encoding UTF8
git status --porcelain=v1 | Set-Content -LiteralPath (Join-Path $SizeOut "git_status.txt") -Encoding UTF8

$SizeReceipt = Get-Content -LiteralPath (Join-Path $SizeOut "diagnostic_receipt.json") -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $SizeReceipt.diagnostic_only) { throw "必须是 diagnostic-only" }
if ($SizeReceipt.data_role -ne "Engineering") { throw "必须是 Engineering" }
if ($SizeReceipt.q0_status -ne "NOT_RUN") { throw "不得升级 Q0" }
if ([int64]$SizeReceipt.diagnostic_parameters.h2d_size_bytes -ne 67108864) { throw "H2D 必须为 64 MiB" }
if ([int]$SizeReceipt.diagnostic_parameters.kernel_duration_ms -ne 10) { throw "kernel 必须为 10 ms" }
if ($SizeReceipt.command_argv -notcontains "--trace=cuda,nvtx") { throw "必须使用标准 CUDA/NVTX collection" }
if (@($SizeReceipt.command_argv | Where-Object { $_ -match "wddm" }).Count -ne 0) { throw "参数 diagnostic 不得启用 WDDM" }

Get-Content -LiteralPath (Join-Path $SizeOut "diagnostic_receipt.json") -Raw -Encoding UTF8
```

完成后保留并回传整个 `$SizeOut`。不要运行 evaluator 来决定本单例成功与否，也不要建立 r11。后续只比较 SQLite 中 `MEMCPY_B` 与 `KERNEL_A` 的真实 device interval：若 overlap=0，立即停止且不实现 1 ms；若 overlap>0，也先停止并审核，再决定是否设计 64 MiB/1 ms。

本次真实结果为：H2D activity=`22365422..26112424 ns`，kernel activity=`26741607..36745367 ns`，间隔 `629183 ns`，真实 overlap=`0`。因此本路线已经按预定判据停止，不得执行 64 MiB/1 ms。

## 2.15 已完成：GPU copy/compute 并发能力探针

本节只读取当前 Q0 GPU 的 CUDA device capability，不运行任何 Q0 case、不启动 Nsight、不创建 r11。必须先用当前 commit 重新编译 binary；`CUDA_VISIBLE_DEVICES` 使用完整 GPU UUID 后，binary 中的逻辑设备 0 才代表目标物理 GPU。

```powershell
$Q0Root = Resolve-Path .
$Python = Join-Path $Q0Root ".venv\Scripts\python.exe"
$GpuSelector = "GPU-0d8fafe6-a1e9-33cc-25fb-632316736455"
$VcVars = "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
$Nvcc = (Get-Command nvcc).Source
$CodeShort = (git rev-parse --short HEAD).Trim()
$CapabilityRoot = Join-Path $Q0Root "engineering_evidence\q0_device_capability\gpu3-rtx4090-$CodeShort"
$CapabilityBinary = Join-Path $CapabilityRoot "exposedpath_q0.exe"

if (Test-Path -LiteralPath $CapabilityRoot) { throw "能力探针目录已存在，禁止覆盖" }
New-Item -ItemType Directory -Path $CapabilityRoot | Out-Null

cmd /d /s /c "`"$VcVars`" -vcvars_ver=14.39 && where cl && `"$Python`" -m exposedpath_v141 build-q0-microbench --nvcc `"$Nvcc`" --output `"$CapabilityBinary`" --platform windows"
if ($LASTEXITCODE -ne 0) { throw "能力探针 binary 编译失败" }

$env:CUDA_VISIBLE_DEVICES = $GpuSelector
$CapabilityRaw = (& $CapabilityBinary --environment-json | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { throw "CUDA device capability 探针失败" }
$Capability = $CapabilityRaw | ConvertFrom-Json

$ExpectedUuid = $GpuSelector.ToUpper().Replace("-", "")
$ObservedUuid = ([string]$Capability.uuid).ToUpper().Replace("-", "")
if ($ObservedUuid -ne $ExpectedUuid) { throw "能力探针 GPU UUID 与目标 GPU 不一致" }
foreach ($Field in @("async_engine_count", "device_overlap", "concurrent_kernels", "can_map_host_memory")) {
    if ($null -eq $Capability.$Field) { throw "能力字段缺失：$Field" }
}
# Gate 6 Missing-Corr oracle amendment v0.2：`can_map_host_memory` 来自
# `cudaDevAttrCanMapHostMemory`，只作为被记录的平台能力事实（字段缺失仍 STOP）。
# sentinel handshake 撤销后该值不再是正式 Q0 的准入 gate：为 0 不阻止 collection，
# 也不得据此调参、换平台假设或绕过其它前置检查。

$Utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllText(
    (Join-Path $CapabilityRoot "device_capabilities.json"),
    ($Capability | ConvertTo-Json -Depth 8),
    $Utf8NoBom
)
$Receipt = [ordered]@{
    data_role = "Engineering"
    diagnostic_only = $true
    q0_status = "NOT_RUN"
    code_commit = (git rev-parse HEAD).Trim()
    cuda_visible_devices = $GpuSelector
    capability_file = "device_capabilities.json"
}
[System.IO.File]::WriteAllText(
    (Join-Path $CapabilityRoot "capability_probe_receipt.json"),
    ($Receipt | ConvertTo-Json -Depth 8),
    $Utf8NoBom
)

Get-Content -LiteralPath (Join-Path $CapabilityRoot "device_capabilities.json") -Raw -Encoding UTF8
```

完成后只需回传整个 `$CapabilityRoot`。四项字段无论为 0 还是非 0 都必须原样保存，不得为满足 Q0 假设而改写。收到证据前，不实施 D2H/D2D，不建立 r11。

真实 GPU3 RTX 4090 结果为：`async_engine_count=5`、`device_overlap=1`、`concurrent_kernels=1`。这只证明设备声明支持相关并发能力，不能证明任意 workload 必然重叠，也不能把此前 overlap=0 归因于 WDDM、driver、runtime 或设备调度层。

## 2.16 已完成并停止：64 MiB D2H + 10 ms kernel 方向 diagnostic（历史步骤，不要重跑）

本节以 §2.14 的 64 MiB H2D/10 ms 结果为唯一匹配对照，只把 `MEMCPY_B` 从 H2D 改为 D2H。buffer 大小、kernel 时长、pinned host memory、device buffer、双 Host thread、两个 nonblocking stream、同时放行编排、NVTX identity、`S_DEVICE` 和标准 `cuda,nvtx` 采集均不变；不增加初始化、event、query 或额外同步。

本单例已于 2026-09-17 在 commit `a607645e9c4fcd7df4b05d4e97fa8bf788763e47` 上执行并回传，结果按预注册判据停止，因此本节脚本只保留为历史记录，不得重跑，也不得据其结果创建新的参数变体。

```powershell
$Q0Root = Resolve-Path .
$Python = Join-Path $Q0Root ".venv\Scripts\python.exe"
$Nsys = "C:\Program Files\NVIDIA Corporation\Nsight Systems 2026.2.1\target-windows-x64\nsys.exe"
$GpuSelector = "GPU-0d8fafe6-a1e9-33cc-25fb-632316736455"
$VcVars = "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
$Nvcc = (Get-Command nvcc).Source
$CodeShort = (git rev-parse --short HEAD).Trim()
$D2HRunId = "q0-win-4090-YYYYMMDD-kernel-memop-d2h-diag-64m-10ms-01"  # 替换实际日期
$D2HBuild = Join-Path $Q0Root "engineering_evidence\q0_diagnostic_builds\kernel-memop-d2h-$CodeShort"
$D2HBinary = Join-Path $D2HBuild "exposedpath_q0.exe"
$D2HOut = Join-Path $Q0Root "engineering_evidence\q0_diagnostics\$D2HRunId"

if (Test-Path -LiteralPath $D2HBuild) { throw "D2H build 目录已存在，禁止覆盖" }
if (Test-Path -LiteralPath $D2HOut) { throw "D2H 输出目录已存在，禁止覆盖" }
New-Item -ItemType Directory -Path $D2HBuild | Out-Null

cmd /d /s /c "`"$VcVars`" -vcvars_ver=14.39 && where cl && `"$Python`" -m exposedpath_v141 build-q0-microbench --nvcc `"$Nvcc`" --output `"$D2HBinary`" --platform windows"
if ($LASTEXITCODE -ne 0) { throw "D2H diagnostic CUDA 编译失败" }

& $Python -m exposedpath_v141 run-q0-kernel-memop-d2h-diagnostic `
    --output-dir $D2HOut `
    --binary $D2HBinary `
    --nsys $Nsys `
    --run-id $D2HRunId `
    --cuda-visible-device $GpuSelector
if ($LASTEXITCODE -ne 0) { throw "D2H diagnostic 采集或导出失败；保留现场并停止" }

git rev-parse HEAD | Set-Content -LiteralPath (Join-Path $D2HOut "code_commit.txt") -Encoding UTF8
git status --porcelain=v1 | Set-Content -LiteralPath (Join-Path $D2HOut "git_status.txt") -Encoding UTF8

$D2HReceiptPath = Join-Path $D2HOut "diagnostic_receipt.json"
$D2HReceipt = Get-Content -LiteralPath $D2HReceiptPath -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $D2HReceipt.diagnostic_only) { throw "必须是 diagnostic-only" }
if ($D2HReceipt.data_role -ne "Engineering") { throw "必须是 Engineering" }
if ($D2HReceipt.q0_status -ne "NOT_RUN") { throw "不得升级 Q0" }
if ($D2HReceipt.diagnostic_parameters.copy_direction -ne "DEVICE_TO_HOST") { throw "copy direction 必须为 D2H" }
if ([int64]$D2HReceipt.diagnostic_parameters.d2h_size_bytes -ne 67108864) { throw "D2H 必须为 64 MiB" }
if ([int]$D2HReceipt.diagnostic_parameters.kernel_duration_ms -ne 10) { throw "kernel 必须为 10 ms" }
if ($D2HReceipt.command_argv -notcontains "--trace=cuda,nvtx") { throw "必须使用标准 CUDA/NVTX collection" }
if ($D2HReceipt.command_argv -contains "--diagnostic-h2d-bytes") { throw "D2H 路径不得使用 H2D 参数" }

$D2HRaw = Join-Path $D2HOut "trace.nsys-rep"
$D2HSqlite = Join-Path $D2HOut "trace.sqlite"
$D2HSourceManifest = Join-Path $D2HOut "source_manifest.json"
$D2HRawSha = (Get-FileHash -LiteralPath $D2HRaw -Algorithm SHA256).Hash

& $Python -m exposedpath_v141 convert-sqlite --sqlite $D2HSqlite --output-dir (Join-Path $D2HOut "canonical") --data-role Engineering --raw-sha256 $D2HRawSha --collector-version ([string]$D2HReceipt.environment.nsight_systems) --source-manifest $D2HSourceManifest
if ($LASTEXITCODE -ne 0) { throw "D2H Canonical observation 无效；保留现场并停止" }
& $Python -m exposedpath_v141 analyze-s --canonical-manifest (Join-Path $D2HOut "canonical\canonical_manifest.json") --output-dir (Join-Path $D2HOut "s")
if ($LASTEXITCODE -notin 0,2,3) { throw "D2H S 执行异常" }
& $Python -m exposedpath_v141 analyze-ab --canonical-manifest (Join-Path $D2HOut "canonical\canonical_manifest.json") --s-manifest (Join-Path $D2HOut "s\s_manifest.json") --output-dir (Join-Path $D2HOut "ab")
if ($LASTEXITCODE -notin 0,2,3) { throw "D2H A/B 执行异常" }

Get-Content -LiteralPath $D2HReceiptPath -Raw -Encoding UTF8
```

预期 evidence/run-id 为 `engineering_evidence\q0_diagnostics\q0-win-4090-YYYYMMDD-kernel-memop-d2h-diag-64m-10ms-01`。完整目录必须包含 Raw、SQLite、diagnostic/source manifest、receipt、环境与命令日志，以及 `canonical/`、`s/`、`ab/` 派生目录。回传后再只读核验 D2H copy kind、context/stream、Runtime API、device interval、overlap、完成顺序和 S terminal。

本诊断唯一成功判据是 `overlap_ns > 0`；terminal 及完成顺序只记录、不作为方向诊断门槛。`overlap_ns=0` 与 `overlap_ns>0` 都必须立即停止并回传审核，不得自动进入 D2D、参数调优、r11 或 Q0 策略修改，也不得输出 WDDM/driver/runtime/调度层根因结论。

本次真实结果为 `overlap_ns=0`，因此本路线已经按预定判据停止：

- run-id：`q0-win-4090-20260917-kernel-memop-d2h-diag-64m-10ms-01`，commit `a607645e9c4fcd7df4b05d4e97fa8bf788763e47`，数据角色 `Engineering`、diagnostic-only、Q0 `NOT_RUN`。
- 真实 device interval：D2H `77979638..87266973 ns`（duration `9287335 ns`，`copy_kind=DEVICE_TO_HOST`、64 MiB），kernel `88995128..98995997 ns`（duration `10000869 ns`）；间隔 `1728155 ns`，`overlap_ns=0`，完成顺序为 copy 先、kernel terminal。
- 两项同 `contextId=1`、分别位于 non-blocking stream `14`（copy）与 `13`（kernel），无 CUDA event dependency，Runtime API correlation 唯一。
- 分析链：`S_DEVICE=VALID_NONEMPTY`、wait-set=`{MEMCPY_B,KERNEL_A}`、terminal=`KERNEL_A`（`end_ns=98995997`）；A/B 为 `kernel_only=10000869 ns`、`kernel_memop_mixed=0`、`wait_set_hidden_union_ns=9287335`、`wait_set_exposed_union_ns=10000869`。Canonical `observation_validity=valid`、`identity=VALID`，S/A-B quality=`VALID`，仅 1 条 `HARNESS_OUTSIDE_REQUEST` warning。
- 哈希链已本地只读复核：Raw `76FAEC18…`、SQLite `C9964B0E…`、source manifest `BE917E5E…`、canonical manifest `DEEEF8F2…`、S manifest `08D0B2A0…`，A/B 压缩件哈希与各自 manifest 相符。回传副本位于本地主工作区未跟踪目录 `server_evidence_inbox/q0-win-4090-20260917-kernel-memop-d2h-diag-64m-10ms-01/`；服务器原始输出目录见 receipt 的 `command_argv`/`export_argv`。

结论与停止条件：改变 H2D→D2H 方向仍未恢复真实 device overlap，`Q0-KERNEL-MEMOP-001` 在当前 Windows/RTX 4090 上判定为 **platform construction blocked**；Q0 保持 `NOT_RUN`，Gate 6 保持 `FAIL`。当前证据不能区分 WDDM、driver、Runtime 或其他层，任何根因结论都不成立。不得进入 D2D，不得运行 64 MiB/1 ms，不得建立 r11，不得在该平台继续参数搜索，也不得修改 oracle、Canonical、S、A/B、evaluator 或 Measurement Contract。后续处置只能通过 `docs/v1_4_1/gate6_strategy_review_v0_1.md` 提出；该审查已于 2026-09-17 定稿，决定为“不新增 synthetic、只做异平台 construction admission 设计、scope limitation 仅作 fallback”。

## 3. 复用冻结 binary 并准备不可覆盖运行目录

> **当前禁止执行。** 第 3 节及后续 r11 步骤只保留为未来流程草案，**当前仍一律禁止执行**：必须取得用户对“执行完整 21 real + 2 synthetic Q0”的单独书面批准（见 §1）。本节已按 construction amendment 与 Missing-Corr oracle amendment v0.2 更新：execution/run schema 为 `0.2.1`，正式 native invocation 必须显式携带且只携带一次 `--measurement-initialization <POLICY>`（§1.1），Missing-Corr 不再使用 sentinel/watchdog。本节固定复用已完成并审计通过的冻结 build（`engineering_evidence/q0_diagnostic_builds/gate6-missingcorr-v02-e44777/exposedpath_q0.exe`，即 final-03 冻结身份），**不重新编译、不复制、不覆盖**；clean-tree gate 只针对 tracked tree（`git status --porcelain=v1 --untracked-files=no`），`engineering_evidence/*` 允许作为 untracked evidence 存在，不得因此 STOP，也不得执行 `git clean`。WDDM、diagnostic 参数与 Engineering diagnostic argv 绝不能加入本节标准 collection argv；Engineering diagnostic 命令也不得混用 formal policy。禁止 retry/tuning。

```powershell
$Q0Root = Resolve-Path .
$Python = Join-Path $Q0Root ".venv\Scripts\python.exe"   # formal Python 固定为仓库 venv，不使用 Get-Command python
$RunId = "q0-win-4090-20260920-gate6-final-03"  # 必须是全新目录；final-01 / final-02 为 frozen historical incomplete run，不重跑、不续跑、不拼接
$Out = Join-Path $Q0Root "engineering_evidence\q0_real\$RunId"
# 复用冻结 build：不复制、不重编、不覆盖该 binary。
$Binary = Join-Path $Q0Root "engineering_evidence\q0_diagnostic_builds\gate6-missingcorr-v02-e44777\exposedpath_q0.exe"
$FrozenBinarySha256 = "6A6DD4340058462E0F4F6CEA36D82B37B9C72D0ACC031F606A1372A4673BB56B"
$FrozenSourceSha256 = "7D0260CA3D4F62E6A2D1AFFE4943A32E84063B19DE3DCBD823205BAD5160E32D"
$Nsys = "C:\Program Files\NVIDIA Corporation\Nsight Systems 2026.2.1\target-windows-x64\nsys.exe"
$GpuSelector = "GPU-替换为nvidia-smi显示的完整UUID"

$Nvcc = (Get-Command nvcc).Source
# Gate 6 Q0 build contract amendment：codegen 只能来自冻结 argv，不得被 ambient 变量注入。
foreach ($Injected in @("NVCC_APPEND_FLAGS", "NVCC_PREPEND_FLAGS")) {
    if (Test-Path "env:$Injected") { throw "存在 ambient nvcc 注入变量：$Injected" }
}

# Gate 6 Q0 build contract amendment：编译必须有可审计 provenance，本节只验证既有 build，不产生新 build。
if (-not ($(& $Nvcc --version | Out-String) -match "12\.4\.131")) { throw "nvcc 不是冻结的 CUDA 12.4.131" }

if (-not (Test-Path -LiteralPath $Binary)) { throw "冻结 Q0 binary 不存在：$Binary" }
if ((Get-FileHash -LiteralPath $Binary -Algorithm SHA256).Hash -ne $FrozenBinarySha256) { throw "binary SHA 与冻结值不一致" }
$BuildReceiptPath = "$Binary.build_receipt.json"
if (-not (Test-Path -LiteralPath $BuildReceiptPath)) { throw "缺少 Q0 build receipt" }
$BuildReceipt = Get-Content -LiteralPath $BuildReceiptPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($BuildReceipt.receipt_version -ne "exposedpath-q0-build-receipt/0.1.0") { throw "build receipt 版本不受支持" }
if ($BuildReceipt.gpu_arch -ne "sm_89") { throw "build receipt gpu_arch 不是 sm_89" }
if (@($BuildReceipt.compile_command | Where-Object { $_ -eq "-arch=sm_89" }).Count -ne 1) { throw "compile argv 必须恰好包含一次 -arch=sm_89" }
if ([string]$BuildReceipt.nvcc.version_output -notmatch "12\.4\.131") { throw "build receipt 记录的 nvcc 不是 12.4.131" }
if (-not (Test-Path -LiteralPath $BuildReceipt.cuda_source.path)) { throw "build receipt 记录的 CUDA source 不存在" }
$SourceSha = (Get-FileHash -LiteralPath $BuildReceipt.cuda_source.path -Algorithm SHA256).Hash
if ($SourceSha -ne $BuildReceipt.cuda_source.sha256) { throw "CUDA source SHA 与 build receipt 不一致" }
if ($SourceSha -ne $FrozenSourceSha256) { throw "CUDA source SHA 与 final-03 冻结值不一致" }
$BinaryShaAtBuild = (Get-FileHash -LiteralPath $Binary -Algorithm SHA256).Hash
if ($BinaryShaAtBuild -ne $BuildReceipt.binary.sha256) { throw "binary SHA 与 build receipt 不一致" }

& $Python -m exposedpath_v141 prepare-q0-run --output-dir (Join-Path $Out "run") --binary $Binary --nsys $Nsys --platform windows --run-id $RunId --cuda-visible-device $GpuSelector

# amendment 校验：冻结 commit、schema 与 formal policy 必须逐字一致，否则 STOP
# frozen unified implementation commit：implementation identity 由该 SHA 定义
$FrozenImplementation = "e44777e8e8ae0eb4d4dcf3f74980954dc6627bf1"
if ($FrozenImplementation -notmatch "^[0-9a-f]{40}$") { throw "冻结 implementation commit 未填写；不得运行正式 Q0" }
# provenance gate：tracked tree clean + frozen implementation 是 HEAD 的 ancestor + 二者之间只允许 runbook-only provenance 修订
# clean-tree 只针对 tracked tree；engineering_evidence/* 允许作为 untracked evidence 存在，不得因此 STOP，也不得 git clean
if (@(git status --porcelain=v1 --untracked-files=no).Count -ne 0) { throw "tracked working tree 不 clean；不得运行正式 Q0" }
$CheckoutCommit = (git rev-parse HEAD).Trim()
git merge-base --is-ancestor $FrozenImplementation $CheckoutCommit
if ($LASTEXITCODE -ne 0) { throw "冻结的 unified implementation commit 不是当前 HEAD 的 ancestor：$FrozenImplementation" }
$ProvenanceDelta = @(git diff --name-only "$FrozenImplementation..$CheckoutCommit")
if ($ProvenanceDelta.Count -ne 1 -or $ProvenanceDelta[0] -ne "docs/v1_4_1/gate6_windows_server_runbook.md") {
    throw "frozen implementation 之后的 committed delta 必须且只能是 docs/v1_4_1/gate6_windows_server_runbook.md：$($ProvenanceDelta -join ', ')"
}
$ExecutionManifest = Get-Content -LiteralPath (Join-Path $Q0Root "q0\execution_manifest_v0_2.json") -Raw -Encoding UTF8 | ConvertFrom-Json
if ($ExecutionManifest.schema_version -ne "exposedpath-q0-execution/0.2.1") { throw "execution manifest 必须为 0.2.1：$($ExecutionManifest.schema_version)" }
$Run0 = Get-Content -LiteralPath (Join-Path $Out "run\q0_run_manifest.json") -Raw -Encoding UTF8 | ConvertFrom-Json
if ($Run0.schema_version -ne "exposedpath-q0-run/0.2.1") { throw "run manifest 必须为 0.2.1：$($Run0.schema_version)" }
$Policies = @($Run0.cases | ForEach-Object { $_.measurement_initialization })
if ($Policies.Count -ne 23) { throw "23/23 case 必须全部显式声明 measurement_initialization" }
if (@($Policies | Where-Object { $_ -notin @("NONE", "PRE_CAPTURE_SAME_KERNEL_WARMUP") }).Count -ne 0) { throw "出现未知 measurement_initialization 取值" }
$WarmupCases = @($Run0.cases | Where-Object { $_.measurement_initialization -eq "PRE_CAPTURE_SAME_KERNEL_WARMUP" })
if ($WarmupCases.Count -ne 1 -or $WarmupCases[0].case_id -ne "Q0-KERNEL-MEMOP-001") { throw "只允许 Q0-KERNEL-MEMOP-001 使用 PRE_CAPTURE_SAME_KERNEL_WARMUP" }
foreach ($Case in @($Run0.cases | Where-Object { $null -ne $_.command_argv })) {
    $FlagCount = @($Case.command_argv | Where-Object { $_ -eq "--measurement-initialization" }).Count
    if ($FlagCount -ne 1) { throw "native case 必须恰好携带一次 --measurement-initialization：$($Case.case_id)" }
    if ($Case.command_argv[-2] -ne "--measurement-initialization" -or $Case.command_argv[-1] -ne $Case.measurement_initialization) {
        throw "native case 的 argv policy 与 manifest policy 不一致：$($Case.case_id)"
    }
}

$FrozenImplementation | Set-Content (Join-Path $Out "frozen_implementation_commit.txt")
$CheckoutCommit | Set-Content (Join-Path $Out "code_commit.txt")
git status --porcelain=v1 | Set-Content (Join-Path $Out "git_status.txt")

$Run = Get-Content -LiteralPath (Join-Path $Out "run\q0_run_manifest.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$GraphCase = $Run.cases | Where-Object case_id -eq "Q0-GRAPH-UNSUPPORTED-001"
$GraphFlagCount = @($GraphCase.command_argv | Where-Object { $_ -eq "--cuda-graph-trace=node" }).Count
$UnexpectedGraphFlags = @(
    $Run.cases |
        Where-Object { $_.case_id -ne "Q0-GRAPH-UNSUPPORTED-001" -and $null -ne $_.command_argv } |
        Where-Object { $_.command_argv -contains "--cuda-graph-trace=node" }
)
if ($GraphFlagCount -ne 1) { throw "Graph case 必须恰好包含一次 node-level graph tracing 参数" }
if ($UnexpectedGraphFlags.Count -ne 0) { throw "普通 case 不得启用 node-level graph tracing" }
```

验收：本节不重新编译，直接复用 final-03 冻结 build `engineering_evidence/q0_diagnostic_builds/gate6-missingcorr-v02-e44777/exposedpath_q0.exe`，其 binary SHA256 必须等于 `6A6DD4340058462E0F4F6CEA36D82B37B9C72D0ACC031F606A1372A4673BB56B`、CUDA source SHA256 必须等于 `7D0260CA3D4F62E6A2D1AFFE4943A32E84063B19DE3DCBD823205BAD5160E32D`，且同目录 `<binary>.build_receipt.json` 存在，其中 `receipt_version=exposedpath-q0-build-receipt/0.1.0`、`gpu_arch=sm_89`、compile argv 恰好一次 `-arch=sm_89`、nvcc `12.4.131`，且 source SHA 与 checkout、binary SHA 与 receipt 双向一致；binary 不被复制、重编或覆盖；无 `NVCC_APPEND_FLAGS` / `NVCC_PREPEND_FLAGS` 等 ambient codegen 注入；tracked working tree clean（`git status --porcelain=v1 --untracked-files=no` 为空，`engineering_evidence/*` 等 untracked evidence 不构成失败）、frozen unified implementation commit `e44777e8e8ae0eb4d4dcf3f74980954dc6627bf1` 是当前 HEAD 的 ancestor，且二者之间 committed delta 恰好只有 `docs/v1_4_1/gate6_windows_server_runbook.md` 一个文件（implementation identity 由 frozen commit 定义；checkout commit 只允许额外包含 implementation 之后的 approved runbook-only provenance 修订，不要求与 frozen commit 相等；实际编译产物仍由 build receipt、CUDA source SHA 与 binary SHA 证明）；run manifest 为 `PREPARED_NOT_EXECUTED` 且 schema 为 `exposedpath-q0-run/0.2.1`；23/23 case 显式声明 `measurement_initialization`（`Q0-KERNEL-MEMOP-001` = `PRE_CAPTURE_SAME_KERNEL_WARMUP`，其余 22 = `NONE`）；21 个 native case 的 `command_argv` 各自恰好一次 `--measurement-initialization` 且与 manifest policy 一致；每个 source manifest 中 logical device 都是 `0`，物理 GPU 由同一个 UUID 显式绑定；只有 `Q0-GRAPH-UNSUPPORTED-001` 恰好包含一次 `--cuda-graph-trace=node`。任何缺失、未知、重复 policy、receipt 不匹配、ambient 注入或 argv/manifest 不一致都必须 STOP，不得手工修补 argv，不得补加 `-arch`、更换 arch 或改 flags 后重试。

## 4. 只采集 r11 单例

```powershell
$RunManifest = Join-Path $Out "run\q0_run_manifest.json"
$Run = Get-Content -LiteralPath $RunManifest -Raw -Encoding UTF8 | ConvertFrom-Json
$NativeCases = @($Run.cases | Where-Object { $null -ne $_.command_argv })
$SmokeCaseId = "Q0-STREAM-001"
& $Python -m exposedpath_v141 execute-q0-case --run-manifest $RunManifest --case $SmokeCaseId
if ($LASTEXITCODE -ne 0) { throw "r11 单例采集失败，保留现场并停止" }
```

验收：此时只能新增 `Q0-STREAM-001` 的 receipt 和非空 `.nsys-rep`。不要提前运行其余 20 个 seed，也不要手工改 receipt 或 Raw。

## 5. r11 单例全链路验收

先只处理 `Q0-STREAM-001`。`nsys export` 只读取 Raw，不得覆盖已存在 SQLite：

```powershell
$CaseId = $SmokeCaseId
$CaseDir = Join-Path $Out "run\cases\$CaseId"
$Raw = Join-Path $CaseDir "trace.nsys-rep"
$Sqlite = Join-Path $CaseDir "trace.sqlite"
$SourceManifest = Join-Path $CaseDir "source_manifest.json"
$RawSha = (Get-FileHash -LiteralPath $Raw -Algorithm SHA256).Hash
$Receipt = Get-Content -LiteralPath (Join-Path $CaseDir "collection_receipt.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$CollectorVersion = [string]$Receipt.environment.nsight_systems

& $Nsys export --type sqlite --lazy=false --force-overwrite=false --output $Sqlite $Raw
if ($LASTEXITCODE -ne 0) { throw "SQLite 导出失败：$CaseId" }
& $Python -m exposedpath_v141 convert-sqlite --sqlite $Sqlite --output-dir (Join-Path $CaseDir "canonical") --data-role Engineering --raw-sha256 $RawSha --collector-version $CollectorVersion --source-manifest $SourceManifest
if ($LASTEXITCODE -ne 0) { throw "Canonical 转换未通过：$CaseId；保留现场并停止" }

$SDir = Join-Path $CaseDir "s"
$ABDir = Join-Path $CaseDir "ab"
$EvidenceDir = Join-Path $Out "real_evidence\$CaseId"
& $Python -m exposedpath_v141 analyze-s --canonical-manifest (Join-Path $CaseDir "canonical\canonical_manifest.json") --output-dir $SDir
if ($LASTEXITCODE -notin 0,2,3) { throw "r11 单例 S 执行异常；保留现场并停止" }
& $Python -m exposedpath_v141 analyze-ab --canonical-manifest (Join-Path $CaseDir "canonical\canonical_manifest.json") --s-manifest (Join-Path $SDir "s_manifest.json") --output-dir $ABDir
if ($LASTEXITCODE -notin 0,2,3) { throw "r11 单例 A/B 执行异常；保留现场并停止" }
& $Python -m exposedpath_v141 evaluate-q0-real-case --case $CaseId --canonical-manifest (Join-Path $CaseDir "canonical\canonical_manifest.json") --s-manifest (Join-Path $SDir "s_manifest.json") --ab-manifest (Join-Path $ABDir "ab_manifest.json") --collection-receipt (Join-Path $CaseDir "collection_receipt.json") --output-dir $EvidenceDir
if ($LASTEXITCODE -ne 0) { throw "r11 单例独立对照未通过；保留现场并停止" }
```

验收：Canonical 转换必须返回 0；S/A/B 必须生成完整 bundle，其中 request 外的 harness 尾部同步可以按既有 fail-closed 规则形成非零状态；独立 evaluator 必须返回 0，且 `Q0-STREAM-001` 的 real evidence 为 `REAL_CASE_PASS`。若目标 request 仍出现额外 sync、映射歧义或其他 invalid，停止并回传整个 r11 单例目录；不能继续批量。

本轮修复未放宽 target request 唯一性。后续批量运行到 `Q0-DEFAULT-PTDS-001`、`Q0-MULTITHREAD-ORDERED-001` 和 `Q0-OVERLAPPING-HOST-SYNC-001` 时，Canonical 转换返回 0 是最低验收条件：它意味着每个 case 的 coordinator `full_request + decode` 能唯一解析，并覆盖相应 worker 的 CUDA 工作；一旦任一 case 再次报告 `TARGET_REQUEST_NOT_UNIQUE` 或 scope unresolved，立即保留现场并停止。

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
    $Receipt = Get-Content -LiteralPath (Join-Path $CaseDir "collection_receipt.json") -Raw -Encoding UTF8 | ConvertFrom-Json
    $CollectorVersion = [string]$Receipt.environment.nsight_systems
    & $Nsys export --type sqlite --lazy=false --force-overwrite=false --output $Sqlite $Raw
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

同一轮 Gate 6 Q0 必须是一次完整的 21 real + 2 synthetic 采集，且全部使用同一 run、同一环境与同一 binary；不允许跨 run、跨平台或跨 binary 拼接，不允许 retry/tuning，也不允许用任何 Engineering diagnostic（含 §2.12～§2.16 与 formalshape warm-up-02）替代正式 Q0 case 或其证据。正式 Q0 的每个 native case 都必须带 §1.1 冻结的 `--measurement-initialization`；`Q0-KERNEL-MEMOP-001` 的 warm-up 只能来自该 formal policy，不得用 `--diagnostic-warmup-kernel` 或手工命令替代。

## 10. 完成后需要带回本地的内容

保留并回传整个 `$Out` 目录，至少包括 `frozen_implementation_commit.txt`、`code_commit.txt`、`git_status.txt`、run manifest（含每个 case 的 `measurement_initialization` policy 与实际 `command_argv`）、21 份 Raw/SQLite/receipt、Canonical（含 3 个故障副本）、S、A/B、real evidence、synthetic 和唯一 gate report。不要只复制最后一张表。返回本地后先核对 provenance（`frozen_implementation_commit.txt` 必须等于 `e44777e8e8ae0eb4d4dcf3f74980954dc6627bf1`；`code_commit.txt` 是该 run 的 checkout commit，允许是 frozen implementation 之后的 approved runbook-only docs commit，不要求与 frozen 相等）、Raw 哈希和 Gate report，再更新科研进度清单。
