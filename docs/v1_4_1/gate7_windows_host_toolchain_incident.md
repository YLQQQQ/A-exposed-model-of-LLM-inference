# Gate 7 Windows/CUDA host-toolchain 故障记录（Engineering）

状态：`EP-ISSUE-21` 的静态编译阻塞**据服务器回报已解除**；`EP-G7-11` 全新最终 smoke 随后启动，但因独立的 Windows kernel bugcheck 中断。本文只记录该主机的 host-toolchain/解释器诊断、环境和待验事项；系统事故单独记录于 [`gate7_system_bugcheck_incident.md`](gate7_system_bugcheck_incident.md)，不得把两类故障混作一个根因。不修改 Gate 6 冻结证据或 v1.4.1 测量语义。代码基线为 `12f6eaee4b30327167cce7fde8083bd6a48250a5`。原始服务器日志尚未导入本审计工作树，数字与 A/B 结果须在最终验收前对照日志复核。

## 事件与时间顺序

1. 旧 smoke 的机器结论为 `BLOCKED`：static preflight 的 pytest `FAIL (exit=1)`，compileall 与 verify_pilot_install 为 `PASS`，Analyzer 为 `PASS`。该 smoke 只作 Engineering 故障证据，不续跑、不拼接、不升格为 Gate 7 PASS。
2. 原先 VS 2026 Build Tools 18.6／MSVC 14.51（`cl 19.51.36243`）被 CUDA 12.4 host configuration 拒绝。后以 side-by-side 的 VS 2022 Build Tools 17.8.6／MSVC 14.38.33130（`cl 19.38.33135`）作为本次已验证的 host compiler；`nvcc` 为 CUDA 12.4.131。
3. 换成 VS2022 后，最小 `__global__` CUDA 程序仍报 `nvcc fatal: Host compiler targets unsupported OS.`。依次选择 Windows SDK 10.0.20348.0、10.0.22621.0、10.0.26100.0 均未改变结果：**SDK 版本切换不是这次错误的有效修复**，无需重复安装/切换 SDK 进行碰运气式排查。
4. VS2022 developer environment 的 `VSCMD_ARG_HOST_ARCH=x64`、`VSCMD_ARG_TGT_ARCH=x64`、`Hostx64\x64\cl.exe`、`_M_X64`、`_WIN64` 与生成 `.obj` 的 machine `8664 (x64)` 一致，排除 x86/ARM host-target 误选。`_WIN32` 在 Win64 下仍定义，不能据此推断 x86。
5. 该 VS2022 安装的 `VC\Auxiliary\Build\vcvarsall.bat`、`vcvars64.bat`、`vcvars32.bat` 均缺失；`Common7\Tools\vsdevcmd\ext\vcvars.bat` 存在，VS DevShell 能初始化有效的 MSVC 14.38 x64 环境。A/B 中仅在 host 的 VS2022 `VC\Auxiliary\Build` 下加入零字节 `vcvarsall.bat` 与 `vcvars64.bat`，其余已验证编译条件保持不变；随后最小 CUDA 编译 exit 0、可执行文件存在。此 A/B 支持**本主机的 nvcc host-toolchain discovery/layout compatibility** 分类，不证明 CUDA 12.4 在所有 VS2022 安装上有同一缺陷，也不揭示 nvcc 内部实现的唯一根因。
6. 在上述条件下，服务器回报 `tests/test_v141_q0_cuda_source.py` 为 `37 passed in 20.42s`。同一代码的 Q0 source tests 可运行，支持将此前失败归类为 host 编译环境阻塞，而非 Q0 source 回归；这**不是**重跑 Gate 6 Q0 资格采集。
7. 首次重跑全量 pytest 时，裸 `python` 解析到 base Anaconda Python 3.12.4、无 torch，出现 5 个 collection errors。显式选择 repo `.venv\Scripts\python.exe` 后，确认 torch `2.6.0+cu124`／`torch.version.cuda=12.4`，服务器回报全量 pytest `917 passed, 1 skipped in 94.97s`、exit 0。不要通过给 base Python 装 torch 掩盖解释器漂移。

## 处理决定与 provenance

- 两个零字节文件仅是**HOST-LOCAL COMPATIBILITY WORKAROUND / DIAGNOSTICALLY VALIDATED**，不是仓库源码补丁、正式平台通用要求或测量合同变更。不得由 smoke launcher 自动创建，不得静默提权，不得使用 `-allow-unsupported-compiler` 或为此升级 CUDA major version。
- 在系统事故另行审计且恢复许可前，**不执行** VS 安装修复或 marker 操作。此前曾考虑的永久处理是核对 VS2022 Build Tools 安装组件和标准 VC auxiliary 布局；若以后恢复此项，须另行批准并保全 VS 安装与工具版本、两个 marker 的相对路径/零字节状态、最小 CUDA compile 输出，以及前后 A/B 原始日志。该主机限定结论须在 Gate 7 evidence 中披露。不要把 marker 存在本身当成充分性证明，实际编译成功才是验证。
- 当前 launcher 不显式校验 `cl`／`nvcc` 路径版本、host/target 架构或 marker。**本轮不扩展 launcher 代码或运行编译测试**；此前静态检查的通过事实保留，但系统事故审计前不重复。若将来需要自动化，先提出独立、只读 preflight patch：报告 toolchain identity，并以真实最小编译失败而非仅缺 marker 判阻塞；不得自行修复 Program Files 内容。
- Gate 7 固定代码基线 `12f6eae` 与目标 GPU 的 physical index `3`、`CUDA_VISIBLE_DEVICES=3`、PyTorch logical index `0`。旧烟测目录与最终新目录必须分别保留，不合并报告。最终报告还需记录 GPU UUID/PCI、driver、Nsight、Python/torch/CUDA、git commit、manifest 与 run role。

## 待验与证据索引

- 待导入/核对：旧 `BLOCKED` smoke 的 `smoke_test_report.json` 和 static log，host compiler A/B 命令及 stdout/stderr，三个 SDK 试验日志，x64 macro/object 证据，零字节 marker 文件信息，最小编译日志，Q0 37/37 与全量 pytest 917/1 的原始输出与退出码。服务器绝对路径和私有模型路径只放受控 evidence manifest，不写入本仓库。
- 全新 smoke 已启动，但因系统 bugcheck 中断；当前暂停重跑、Resume、GPU 测试与 profiling，只读保全本次中断 evidence、Windows 事件及 minidump。不得把事故前静态 `37 passed`、`917 passed, 1 skipped` 改写为 FAIL，也不得把它们当作 Gate 7 完整 acceptance。Gate 7 正式状态仍为 `NOT_RUN`，Gate 8 不可启动。

操作命令与最终检查清单见 [`docs/server_smoke_test.md`](../server_smoke_test.md)。
