# Controlled Engineering server draft 0.1

2026-09-26。仅草案，未执行；按独立阶段授权，不自动续跑。
适用[controlled bridge 0.1](gate8_controlled_bridge_v0_1.md)，不是模型smoke。
使用现有固定checkout，不创建新repo/worktree。机器路径由忽略的本地交付清单提供。

**7.29更新：** 下方A的8d64f75首部署块已完成，不能再次执行。
服务器已到24f58f8；全量1165 passed/1 skipped，合同/Canonical/oracle通过，
但native UUID接口编译失败。修复只将UUID改从cudaGetDeviceProperties().uuid读取。
恢复须使用基于**24f58f8**的新增量包和完整恢复脚本；最小复验为30项受控定向、
compileall及native真实编译，不重复已通过的全量，不加载DLL，不采集。
必须记录此前全量属于24f58f8，不写成修复commit的全量成绩。

## A. 部署和静态构建（无profile/export/CUDA程序）

先核对交付清单中的完整commit、bundle prerequisite/bytes/SHA256；服务器必须clean。
从已存在的8d64f75正常fetch bundle并detach到明确目标；禁止追随未经审查的main。
以下 `$ServerRoot/$CodeRoot/$Bundle/$Target/$ExpectedBundleHash/$PythonExe` 由交付清单赋值。
`$PythonExe`必须是固定checkout的 `.venv\Scripts\python.exe`，不能依赖PATH python。

```powershell
$ErrorActionPreference = 'Stop'
function Read-Git([string[]]$GitArgs) {
  $Result = @(& git @GitArgs)
  if ($LASTEXITCODE -ne 0) { throw 'Git query failed' }
  return ($Result -join "`n").Trim()
}
Set-Location -LiteralPath $CodeRoot
if (Read-Git @('status','--porcelain')) { throw 'Dirty checkout' }
if ((Read-Git @('rev-parse','HEAD')) -ne '8d64f7580d43d7c8e1cb7a416b459cec8f60b011') { throw 'Baseline conflict' }
if ((Get-FileHash -LiteralPath $Bundle -Algorithm SHA256).Hash -ne $ExpectedBundleHash) { throw 'Bundle hash' }
git bundle verify $Bundle
if ($LASTEXITCODE -ne 0) { throw 'Bundle prerequisite' }
git fetch $Bundle main
if ($LASTEXITCODE -ne 0) { throw 'Bundle fetch' }
if ((Read-Git @('rev-parse','FETCH_HEAD')) -ne $Target) { throw 'Target conflict' }
git checkout --detach $Target
if ($LASTEXITCODE -ne 0) { throw 'Checkout failed' }
if (Read-Git @('status','--porcelain')) { throw 'Checkout not clean' }
$env:CUDA_DEVICE_ORDER = 'PCI_BUS_ID'
$env:CUDA_VISIBLE_DEVICES = '-1'
& $PythonExe -m pytest -q -p no:cacheprovider
if ($LASTEXITCODE -ne 0) { throw 'Static tests failed' }
& $PythonExe -m compileall -q exposedpath analysis exposedpath_v141 scripts
if ($LASTEXITCODE -ne 0) { throw 'Compileall failed' }
& $PythonExe -m exposedpath_v141 validate-contract
if ($LASTEXITCODE -ne 0) { throw 'Contract failed' }
& $PythonExe scripts/verify_canonical_raw_boundary.py
if ($LASTEXITCODE -ne 0) { throw 'Canonical boundary failed' }
& $PythonExe scripts/verify_q0_oracle_independence.py
if ($LASTEXITCODE -ne 0) { throw 'Oracle independence failed' }
git diff --check
if ($LASTEXITCODE -ne 0) { throw 'Diff check failed' }
```

在上述编译相关测试前，显式载入已验证VS2022 x64/MSVC14.38/CUDA12.4环境；
不能依赖重启前状态，两个0-byte compatibility marker仅记录length/hash，不能作为初始化脚本。
目标安装的Launch-VsDevShell wrapper不支持DevCmdArguments，旧草案已实机失败。
改为导入 `Common7\Tools\Microsoft.VisualStudio.DevShell.dll`，用
`Get-Command Enter-VsDevShell -Module Microsoft.VisualStudio.DevShell`检查
VsInstallPath/SkipAutomaticLocation/DevCmdArguments参数都存在后，调用
`Enter-VsDevShell -VsInstallPath $VsRoot -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64 -vcvars_ver=14.38'`，
核实实际第一cl路径及19.38.33135、VCToolsVersion14.38.33130、nvcc12.4.131。
不符停止，不用allow-unsupported-compiler。完整transcript存logs下全新目录。

构建单独在 `$ServerRoot/diagnostics/<unique-build>`，不把DLL放tracked目录。
`$Nvcc`取已核实绝对路径，`$NvtxInclude`为**实际存在**且含
`nvtx3/nvToolsExt.h`的include根（可用已安装Toolkit/Nsight；缺失则停止，不下载补猜）。

```powershell
if (Test-Path -LiteralPath $BuildRoot) { throw 'Build directory exists' }
New-Item -ItemType Directory -Path $BuildRoot | Out-Null
$Library = Join-Path $BuildRoot 'gate8_controlled_token.dll'
Push-Location -LiteralPath $BuildRoot
& $Nvcc '-std=c++17' '-shared' '-I' $NvtxInclude '-o' $Library (Join-Path $CodeRoot 'scripts\gate8_controlled_token.cu')
$BuildExit = $LASTEXITCODE
Pop-Location
if ($BuildExit -ne 0 -or !(Test-Path -LiteralPath $Library)) { throw 'Native build failed' }
Get-FileHash -LiteralPath $Library -Algorithm SHA256
Read-Git @('status','--porcelain')
```

本阶段不加载DLL、不跑CUDA probe。回传compiler/marker及环境身份、构建argv/log、
DLL与source hash、静态结果、HEAD/clean；先审查再决定B，不能把编译成功称GPU通过。

## B. 单独授权的窄受控采集

批准后设mask=3/order=PCI_BUS_ID，nvidia-smi仅查目标GPU index/UUID/PCI/driver，
写UTF8无BOM `preflight.json`：gpu_index_physical整数、gpu_uuid、pci_bus_id、
cuda_device_order、cuda_visible_devices。用实际查询，不手填“通过”。
工具/环境与A阶段有变化则停止重新审查；不自动改采集配置。
新目录 `$RunRoot=$ServerRoot/evidence/gate8/<unique-run>`；不存在才创建。
下面变量全部为绝对路径，plan/preflight/REP/execution均在同一RunRoot内，Library保持构建来源。

```powershell
$env:CUDA_DEVICE_ORDER = 'PCI_BUS_ID'
$env:CUDA_VISIBLE_DEVICES = '3'
& $PythonExe -m exposedpath_v141.gate8_controlled_cli prepare --output-dir $PlanDir --preflight $Preflight --library $Library --expected-commit $Target --run-id $RunId
if ($LASTEXITCODE -ne 0) { throw 'Prepare failed' }
$Plan = Join-Path $PlanDir 'control_plan.json'
$ProfileArgs = @('profile','--trace=cuda,nvtx','--sample=none','--cpuctxsw=none',
  '--cuda-memory-usage=false','--cuda-trace-scope=process-tree','--isr=false',
  '--output',$RepPrefix,$PythonExe,'-m','exposedpath_v141.gate8_controlled_cli',
  'run','--plan',$Plan,'--output-dir',$ExecutionDir,'--execute-controlled')
& $Nsys @ProfileArgs
$CollectionExit = $LASTEXITCODE
$Rep = $RepPrefix + '.nsys-rep'
$ExecutionReceipt = Join-Path $ExecutionDir 'execution_receipt.json'
# Failed/missing output仍保留日志，禁止伪造成功receipt或重用相同目录。
if (!(Test-Path -LiteralPath $Rep) -or !(Test-Path -LiteralPath $ExecutionReceipt)) { throw 'Missing capture artifact' }
$Receipt = [ordered]@{schema_version='exposedpath-controlled-collection/0.1.0';
  process_exit_code=$CollectionExit; argv=@($Nsys)+$ProfileArgs; rep_path=$Rep;
  rep_sha256=(Get-FileHash -LiteralPath $Rep -Algorithm SHA256).Hash.ToLowerInvariant();
  plan_sha256=(Get-FileHash -LiteralPath $Plan -Algorithm SHA256).Hash.ToLowerInvariant();
  execution_receipt_sha256=(Get-FileHash -LiteralPath $ExecutionReceipt -Algorithm SHA256).Hash.ToLowerInvariant();
  observation_profile='G8-CONTROLLED-CUDA-NVTX/0.1.0'}
[IO.File]::WriteAllText($CollectionReceipt,($Receipt | ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
if ($CollectionExit -ne 0) { throw 'Collection failed; stop, preserve evidence' }
```

`$PythonExe`必须与execution receipt的sys.executable字符串一致；差异先解释，不补改旧receipt。
禁止resume、force-overwrite、额外trace/GPU metrics、重复参数或偷偷修改CLI API subset。
无自动retry采集；任何错误、系统异常、缺record、身份冲突都停止并保留全部文件。
本草案不实现自动终止collection；操作员从profile启动开始计时，**300秒仍未返回即停止**，
这是Engineering操作上限，不是性能阈值。在原终端按Ctrl+C，不运行后处理/重试；记录
启动/中断UTC及终端输出，保留partial。另终端只读查询本RunRoot对应CommandLine、
ExecutablePath、PID/ParentPID；未确认进程归属不得终止。若Ctrl+C后本次进程仍存活，
回传这些记录等待精确PID处置，禁止按进程名批量kill/不受控进程树终止或继续新采集。

## C. 后处理（也须在授权范围内）

使用已审查的bounded exporter，禁止自动从B接模型。

```powershell
& $PythonExe scripts/gate7_nsys_postprocess.py --nsys $Nsys --rep $Rep --canonical-sqlite $Sqlite --report $ExportReport
if ($LASTEXITCODE -ne 0) { throw 'Export failed' }
& $PythonExe -m exposedpath_v141.gate8_controlled_cli audit --plan $Plan --execution-dir $ExecutionDir --rep $Rep --sqlite $Sqlite --export-report $ExportReport --collection-receipt $CollectionReceipt --input-receipt (Join-Path $RunRoot 'input_receipt.json') --output-dir (Join-Path $RunRoot 'derived-v1') --collector-version $NsysVersion
if ($LASTEXITCODE -ne 0) { throw 'Controlled audit blocked' }
```

成功仅表示此construction的工程计算链可用；逐项读report而非仅exit0。
预期独立W(s)/terminal/B对照、原始host-readable顺序/identity、局部GetLastError
unknown保留；不设任意百分比、不发布D/Signature、不判新Q0或Gate8 PASS。
没有必需GetLastError/API/边界、额外Driver/sync/memset、不可界定前驱或诊断影响均停止。

## 回传与完整归档

完整RunRoot、A阶段transcript/build receipt、环境/tool版本、native源/DLL哈希及来源、
所有plan/manifest/input/probe/producer/execution/collection/export receipts、REP/SQLite、
全部派生/partial/stdout/stderr一起保留。大型原始数据私有传输，不入Git。
先快照文件列表并排除`artifact_sha256*.csv`，再写新清单；不得把清单自身作为输入。
逐项校验清单，再打ZIP并记录bytes/SHA256、ZIP CRC/安全路径及内容覆盖；不删除失败尝试。
本地只读审计后再决定是否补受控缺证据副本/资格或需API支持修订，不自动进入模型。
