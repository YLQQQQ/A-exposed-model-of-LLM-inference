# Gate 7 Windows kernel bugcheck 事件记录（Engineering）

状态：`EP-ISSUE-22`，只读审计中。服务器回报在 `12f6eaee4b30327167cce7fde8083bd6a48250a5` 的 fresh final `EP-G7-11` smoke 执行期间，Windows Server build 20348 发生 BugCheck `0x133` 并自动重启。该 attempt 记为 `INTERRUPTED_BY_SYSTEM_BUGCHECK`，仅作 incident evidence；Gate 7 正式状态仍为 `NOT_RUN`，最终 acceptance 未建立，Gate 8 不得启动。**本页依据服务器回报编写；原始 smoke 文件、Event 导出和 dump 尚未在本地审计工作树核验。**服务器绝对目录及私有路径仅保存于受控 evidence 索引。

本事件与 [`gate7_windows_host_toolchain_incident.md`](gate7_windows_host_toolchain_incident.md) 的 CUDA/VS host-toolchain 编译故障属于不同故障域；现无证据证明两者有共同根因。本文不改变 Measurement Contract、S/A/B/D、Q0、runner 或 Gate 6 冻结证据。

## 事故前已通过的事实（服务器回报，原始日志待复核）

- 代码基线 `12f6eae`，事故前 tracked working tree clean；repo 自有 `.venv` Python 3.11.16、torch `2.6.0+cu124`、`torch.version.cuda=12.4`。
- VS2022 Build Tools 17.8.6、MSVC 14.38.33130／`cl 19.38.33135` x64、`nvcc 12.4.131`、Nsight Systems 2026.2.1。两个 host-local 零字节 `vcvarsall.bat`、`vcvars64.bat` compatibility markers 存在；无 marker 时最小编译报 `Host compiler targets unsupported OS`，有 marker 时在所述主机条件下最小 CUDA 编译 exit 0。此 A/B 只支持本机 workaround，不是通用修复。
- 独立 Q0 CUDA source tests：`37 passed`。使用同一 repo `.venv` 的完整 pytest：`917 passed, 1 skipped`，exit 0。后续系统重启**不把这两项已通过结果改写为 FAIL**；它们也不能替代完整 smoke acceptance。
- 目标 GPU 为 RTX 4090，physical index `3`、UUID `GPU-0d8fafe6-a1e9-33cc-25fb-632316736455`、PCI `00000000:E1:00.0`；`CUDA_VISIBLE_DEVICES=3`，进程内 logical CUDA index `0`。身份仍须在本次 attempt 原始快照中逐项复核。

## Fresh attempt 与已知时间线

- 新 evidence root 名：`ep-g7-11-final-12f6eae-20260923T061109Z`。服务器回报 preflight 完成后启动完整 fresh smoke，未使用 `ResumeFrom`、`ExistingSmokeDir`、`SkipStaticTests` 或 `DryRun`；事故前有 evidence 文件写入。
- 现有 LastWriteTime 观察延续至服务器本地时间约 `2026-09-23 14:16:16`，但 PowerShell `Format-Table` 截断了文件名。尚无法判定事故时 smoke 处于 static pytest、Pass0、Pass1/Nsight 或 Analyzer 的哪一阶段；也未据此确认最终 machine report 是否存在或可信。
- 重启后服务器 System Event Log 回报：Event 6008 记录上次意外关闭时间约为本地 `2026-09-23 14:15:52`；Event 12（Kernel-General）记录 OS startup `2026-09-23T06:19:21.500000000Z`。这些时间均须与原始事件时间字段及文件时间线核对，不据修改时间倒推精确崩溃阶段。
- 中断目录不删除、不覆盖、不 Resume、不与任何旧 attempt 拼接，也不作为 Gate 7 acceptance evidence。

## Windows 系统事件（服务器回报，待原始导出核验）

- Event 41，`Microsoft-Windows-Kernel-Power`，Critical：系统未经正常关机重新启动。
- Event 6008，`EventLog`，Error：上次关闭被记录为意外关闭，回报时间约为 `2026-09-23 14:15:52` 本地。
- Event 1001，`Microsoft-Windows-WER-SystemErrorReporting`，Error：BugCheck `0x00000133`，参数为 `(0x0000000000000000, 0x0000000000000501, 0x0000000000000500, 0xfffff8056010f328)`；Report ID `fdc45af2-49d2-481c-b192-7b58f888efdc`；引用本次 minidump `%SystemRoot%\Minidump\092326-24484-01.dmp`（服务器回报约 6.3 MB）。
- Event 1076 是用户在重启后对上次意外关闭的“其他（计划外）”分类，**不证明用户发起重启**。当前查询的事故窗口内未见 Event 1074；这不等于证明所有时间范围都不存在 1074。
- 服务器另有旧 dump `%SystemRoot%\Minidump\071726-25968-01.dmp`，回报 LastWriteTime 为 `2026-07-17`；未审计，**不得推断与本次根因相同**。

## 证据等级与因果边界

- **已由所回报事件内容支持、待本地原件复核**：Windows kernel BugCheck `0x133`（`DPC_WATCHDOG_VIOLATION`）及非正常重启；Event 1001 指向本次 dump。它不是一条已证明的正常人工／脚本 Restart 记录。
- **时间相关**：fresh Gate 7 smoke 在 bugcheck 发生时正在执行，可记录为可能的触发条件，但时间相关性不等于因果性。
- **未知**：确切违规的 kernel driver/component、是否涉及 NVIDIA 驱动、Nsight、Gate 7 脚本或管理员 PowerShell，以及中断时的精确 smoke 阶段。不得把任何一项写成已确认 root cause；BugCheck 参数本身不足以完成归因。

## 只读后续动作与暂停范围

1. 保全原始 fresh evidence、事故前环境快照、System Event 导出及两份 dump；列出中断目录所有文件的**完整相对路径**、大小和时间戳，核对 machine report、manifest、Pass0/Pass1、Nsight、Analyzer 与 static preflight 哪些实际写出，缺失项保持缺失而不补推断。原件不可改写；分析副本与原件区分。
2. 对照 Event 12/41/6008/1001 的原始时间字段、报告 ID、dump identity 与文件时间线，形成可复核 chronology；必要时对现有 dump 做只读分析，当前不要求安装 WinDbg 或其他新调试软件。
3. 事故审计和新的显式决策前，**不**重跑/Resume smoke，不运行 GPU stress 或 Nsight profile，不改 CUDA、NVIDIA driver、Windows、VS2022 或两个 markers，不启用 Driver Verifier，不安装调试工具，不修改 runtime 代码或冻结合同，不启动 Gate 8。

结论：本次 fresh attempt 是系统中断的 Engineering incident，不是 Gate 7 PASS，也不简单归为普通 smoke FAIL。事故前静态验证保持其独立结果；Gate 7 = `NOT_RUN`，当前不建议重跑 smoke。
