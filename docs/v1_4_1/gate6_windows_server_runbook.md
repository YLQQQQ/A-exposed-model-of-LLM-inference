# Gate 6 Windows GPU 服务器操作手册

## 0. 从本机部署到已有服务器

服务器中原有的 `YLQ_test` 包含旧项目、旧虚拟环境和历史 `nsys_*`、`pilot_*` 结果，应完整保留，不得覆盖、删除或把它改名冒充新版。本轮继续使用已有 `YLQ_test_q0_v141`，通过 Git bundle 只更新受 Git 跟踪的代码，不重新 clone，也不执行 `git clean`。

本机已经生成的交付文件位于仓库根目录的 `transfer` 文件夹，名称以最终交付消息为准。把这一份 `.bundle` 文件通过 RDP、共享盘或移动介质复制到服务器原 `YLQ_test` 的同级目录。服务器目录建议为：

```text
Wsn1
├── YLQ_test                 # 旧项目和旧结果，保持不动
├── ExposedPath_Q0_*.bundle  # 本机交付包
└── YLQ_test_q0_v141         # 已有 Q0 工作目录，含未跟踪的 r1/r2/r3/r4/r5/r6/r7
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

`git reset --hard` 只能在上述 tracked-dirty 检查为空、备份分支已建立后执行；它不会删除未跟踪的 `engineering_evidence/r1、r2、r3、r4、r5、r6、r7`。严禁追加 `git clean`。更新后以最终交付消息记录的 commit 为核对值。

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

验收：唯一 target request 成功解析；prior request 保留但不制造歧义；correlation 131 仅作为 request 外 warning；SQLite 哈希不变。该只读成功不升级 r7 的失败资格，正式重跑必须使用全新 r8。

## 3. 编译并准备不可覆盖运行目录

```powershell
$Q0Root = Resolve-Path .
$RunId = "q0-win-4090-YYYYMMDD-r8"  # 执行时替换日期；必须是全新目录
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

## 4. 只采集 r8 单例

```powershell
$RunManifest = Join-Path $Out "run\q0_run_manifest.json"
$Run = Get-Content -LiteralPath $RunManifest -Raw -Encoding UTF8 | ConvertFrom-Json
$NativeCases = @($Run.cases | Where-Object { $null -ne $_.command_argv })
$SmokeCaseId = "Q0-STREAM-001"
& $Python -m exposedpath_v141 execute-q0-case --run-manifest $RunManifest --case $SmokeCaseId
if ($LASTEXITCODE -ne 0) { throw "r8 单例采集失败，保留现场并停止" }
```

验收：此时只能新增 `Q0-STREAM-001` 的 receipt 和非空 `.nsys-rep`。不要提前运行其余 20 个 seed，也不要手工改 receipt 或 Raw。

## 5. r8 单例全链路验收

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
if ($LASTEXITCODE -notin 0,2,3) { throw "r8 单例 S 执行异常；保留现场并停止" }
& $Python -m exposedpath_v141 analyze-ab --canonical-manifest (Join-Path $CaseDir "canonical\canonical_manifest.json") --s-manifest (Join-Path $SDir "s_manifest.json") --output-dir $ABDir
if ($LASTEXITCODE -notin 0,2,3) { throw "r8 单例 A/B 执行异常；保留现场并停止" }
& $Python -m exposedpath_v141 evaluate-q0-real-case --case $CaseId --canonical-manifest (Join-Path $CaseDir "canonical\canonical_manifest.json") --s-manifest (Join-Path $SDir "s_manifest.json") --ab-manifest (Join-Path $ABDir "ab_manifest.json") --collection-receipt (Join-Path $CaseDir "collection_receipt.json") --output-dir $EvidenceDir
if ($LASTEXITCODE -ne 0) { throw "r8 单例独立对照未通过；保留现场并停止" }
```

验收：Canonical 转换必须返回 0；S/A/B 必须生成完整 bundle，其中 request 外的 harness 尾部同步可以按既有 fail-closed 规则形成非零状态；独立 evaluator 必须返回 0，且 `Q0-STREAM-001` 的 real evidence 为 `REAL_CASE_PASS`。若目标 request 仍出现额外 sync、映射歧义或其他 invalid，停止并回传整个 r8 单例目录；不能继续批量。

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

## 10. 完成后需要带回本地的内容

保留并回传整个 `$Out` 目录，至少包括 `code_commit.txt`、`git_status.txt`、run manifest、21 份 Raw/SQLite/receipt、Canonical（含 3 个故障副本）、S、A/B、real evidence、synthetic 和唯一 gate report。不要只复制最后一张表。返回本地后先核对代码版本、Raw 哈希和 Gate report，再更新科研进度清单。
