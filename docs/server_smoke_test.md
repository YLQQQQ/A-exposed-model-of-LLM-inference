# Gate 7 Windows/RTX 4090 server smoke 操作入口

本页适用于 v1.4.1 `EP-G7-11` **Engineering** smoke，不是 Pilot/Formal 许可。当前服务器代码基线为 `12f6eaee4b30327167cce7fde8083bd6a48250a5`。旧 `BLOCKED` attempt 不可升级为 Gate 7 PASS；环境修复后的 fresh final smoke 已启动，但服务器发生 Windows BugCheck `0x133`，该 attempt 为 `INTERRUPTED_BY_SYSTEM_BUGCHECK`，亦不可作为 acceptance evidence。**当前暂停所有 smoke、续跑与 GPU 操作；下列命令仅保留为历史操作模板，不得执行，直至事故只读审计完成并重新取得明确批准。**host-toolchain 故障见 [`gate7_windows_host_toolchain_incident.md`](v1_4_1/gate7_windows_host_toolchain_incident.md)，独立系统事件见 [`gate7_system_bugcheck_incident.md`](v1_4_1/gate7_system_bugcheck_incident.md)。

## 1. 固定服务器执行身份

从 VS2022 Developer PowerShell（Build Tools 17.8.6、MSVC 14.38.33130）进入部署 repo。`where.exe cl` 的首个结果必须属于 VS2022 `Hostx64\x64`，`cl` 为 19.38.33135；`VSCMD_ARG_HOST_ARCH`、`VSCMD_ARG_TGT_ARCH` 均为 `x64`。`nvcc` 必须为 CUDA 12.4.131。VS2026/MSVC 19.51 不适用本次 CUDA 12.4 编译；不得用 `-allow-unsupported-compiler` 或升级 CUDA major version绕过。若本机仍依赖两个零字节 compatibility markers，记录它们的路径/大小、人工批准、A/B 日志和最小 CUDA 编译结果；launcher 不得自动创建。仅有 marker 不构成编译成功证据。

```powershell
Set-Location '<GATE7_REPO>'
git rev-parse HEAD
git status --short
where.exe cl
cl /Bv
where.exe nvcc
nvcc --version
$env:VSCMD_ARG_HOST_ARCH
$env:VSCMD_ARG_TGT_ARCH
```

**解释器必须显式选择。** `run_server_smoke_test.ps1` 把选定的 `-PythonExe` 传给 pytest、compileall、verify_pilot_install、CUDA 检查、Pass0/Pass1 和 analyzer，但默认 `python` 会先按 PATH 解析，可能误入无 torch 的 base Anaconda。不要给 base Python 装 torch 作为修复。使用 repo `.venv\Scripts\python.exe` 的绝对路径：

```powershell
$repo = (Resolve-Path '.').Path
$python = (Resolve-Path (Join-Path $repo '.venv\Scripts\python.exe')).Path
& $python --version
& $python -c 'import sys, torch; print(sys.executable); print(torch.__version__); print(torch.version.cuda)'
```

目标 RTX 4090 的 physical GPU index 为 `3`、UUID 为 `GPU-0d8fafe6-a1e9-33cc-25fb-632316736455`；当前目标配置 `CUDA_DEVICE_ORDER=PCI_BUS_ID`、`CUDA_VISIBLE_DEVICES=3`，PyTorch logical device 为 `cuda:0`。`-GpuId 3` 与 manifest `gpu_index`/`gpu_index_physical` 为 physical，`gpu_index_logical` 为 logical；不从 `torch.cuda.device_count()` 反推 physical index。还须核对 PCI 与 driver。

```powershell
$env:CUDA_DEVICE_ORDER = 'PCI_BUS_ID'
$env:CUDA_VISIBLE_DEVICES = '3'
nvidia-smi --query-gpu=index,uuid,pci.bus_id,name,driver_version --format=csv
& $python -c 'import os, torch; from exposedpath.manifest import resolve_logical_cuda_index; p=3; l=resolve_logical_cuda_index(p, os.environ.get("CUDA_VISIBLE_DEVICES")); print("physical", p, "logical", l, "name", torch.cuda.get_device_name(l))'
```

## 2. 静态检查与最终命令计划（当前暂停执行）

此前的执行要求是在同一 VS2022 x64 shell、同一 repo `.venv` 和上述 CUDA 环境下保存原始 stdout/stderr、退出码和时间。服务器回报 Q0 CUDA source `37 passed`、全量 pytest `917 passed, 1 skipped`；原始日志仍待审计。`verify_pilot_install.ps1 -SkipTests` 仅避免重复 pytest；完整 smoke 不得使用 `-SkipStaticTests`。当前 launcher 没有独立验证 cl/nvcc 路径、版本、x64 或 marker。以下静态命令是已暂停的历史模板，**不得因它们曾通过就自行解除系统事故后的执行暂停**。

```powershell
& $python -m pytest -q tests/test_v141_q0_cuda_source.py
& $python -m pytest -q -p no:cacheprovider
& $python -m compileall exposedpath analysis exposedpath_v141
& $python -m exposedpath_v141 validate-contract
& $python scripts/verify_canonical_raw_boundary.py
& $python scripts/verify_q0_oracle_independence.py
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo 'scripts\verify_pilot_install.ps1') -SkipTests -PythonExe $python
```

以下是先前批准 smoke 时使用的命令形式，仅供审计执行参数，**当前不得再次执行**。当时使用真实模型目录（含 `config.json`）、已验证的 Nsight `nsys.exe` 绝对路径以及新的空 evidence root；未传 `-ResumeFrom`、`-ExistingSmokeDir`、`-SkipStaticTests` 或 `-DryRun`。旧 `BLOCKED` evidence 与本次中断 evidence 均须保留、不续跑、不拼接。

```powershell
$model = '<MODEL_DIR_WITH_CONFIG_JSON>'
$nsys = '<ABSOLUTE_PATH_TO_VALIDATED_NSYS.EXE>'
$evidenceRoot = '<NEW_EMPTY_GATE7_EVIDENCE_ROOT>'
& (Join-Path $repo 'scripts\run_server_smoke_test.ps1') `
    -ModelPath $model `
    -GpuId 3 `
    -NsysPath $nsys `
    -OutputRoot $evidenceRoot `
    -PythonExe $python `
    -ExperimentId 'ep-g7-11-final' `
    -FixedInputTokens 32 `
    -FixedOutputTokens 2 `
    -WarmupCount 1 `
    -RepeatCount 2
```

脚本会创建 `<NEW_EMPTY_GATE7_EVIDENCE_ROOT>\smoke_<UTC_timestamp>`，含 `smoke_test_report.json`、manifest、Pass0/Pass1、Nsight `.nsys-rep`/SQLite、analyzer 与 logs。**即使机器报告为 `BLOCKED`，当前脚本结尾也可能 `exit 0`**；shell code 不能单独表示 PASS。必须读取报告的 `gate_decision`、`environment.pytest`、`environment.compileall`、`environment.verify_pilot_install`、Pass0/Pass1、analyzer、身份和 errors。`READY_FOR_SMALL_PILOT` 仅是脚本内部结果，仍需按 Gate 7 执行计划逐项审计；缺失证据 fail closed。

## 3. 最终 smoke 前检查清单（历史模板，当前不可用于放行）

- [ ] HEAD 等于 `12f6eaee4b30327167cce7fde8083bd6a48250a5`，工作树符合预期；全新 evidence root，不续跑旧 attempt。
- [ ] VS2022 Build Tools 17.8.6／MSVC 14.38.33130／`cl 19.38.33135`，host/target x64；`where.exe cl`、`cl /Bv` 留痕。
- [ ] `nvcc` 为 CUDA 12.4.131；host-local compatibility condition 已记录并经最小 CUDA 编译验证。
- [ ] repo `.venv` Python 3.11 已显式选择；torch `2.6.0+cu124`、`torch.version.cuda=12.4`。
- [ ] physical GPU index `3`，UUID/PCI/driver 核对；`CUDA_VISIBLE_DEVICES=3`，torch logical index `0`。
- [ ] Q0 CUDA source `37/37 PASS`、全量 pytest `917 passed, 1 skipped` 的原始日志和退出码已复核；本次同环境预检查也通过。
- [ ] compileall、validate-contract、Canonical boundary、oracle independence、verify_pilot_install 均成功并留痕。
- [ ] 模型、Nsight、输出目录与实验参数已确认；**fresh final smoke 已启动但系统 bugcheck 中断。当前清单不构成重跑许可**。

失败或中断时保留整个新 smoke 目录，不覆盖、不拼接，也不进入 Gate 8。

## 4. 当前事故封存与只读审计

- 服务器回报：本次 fresh evidence root 名为 `ep-g7-11-final-12f6eae-20260923T061109Z`；预检查完成后启动完整 smoke，执行中发生 Windows kernel bugcheck/restart。文件 LastWriteTime 约至本地 14:16:16，但既有列表截断了文件名，**不能据此判定中断发生在 pytest、Pass0、Pass1/Nsight 还是 Analyzer**。
- 只读记录该目录全部文件的完整相对路径、大小、时间戳、关键报告存在性和内容；保存 Event 41/6008/1001、相关时间线与本次 minidump。原始日志、事件导出和 dump 尚未在本地审计工作树核验；服务器绝对路径与私有模型路径仅放受控 evidence 索引。
- 不修改两个 host-local compatibility markers，不改 CUDA/NVIDIA driver/Windows/VS，不安装调试工具或启用 Driver Verifier；不运行 GPU stress、Nsight rerun、smoke rerun 或 Resume。事故审计与单独决策前 Gate 7 正式状态保持 `NOT_RUN`，Gate 8 不启动。
