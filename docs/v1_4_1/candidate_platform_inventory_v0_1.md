# Candidate Platform Inventory v0.1（静态资格盘点）

## 0. 状态与边界

状态：**盘点稿，等待用户补充/确认**。本文件是 `EP-G6-07` 的第一步（候选平台盘点 + 静态资格审查），不完成 `EP-G6-07`。

边界：

- 判定严格使用 `docs/v1_4_1/candidate_platform_admission_checklist_v0_1.md` 的 A1～A9；本文件不修改 checklist、成功判据、`k_max`、workload 或 Gate 6/Q0 requirement。
- 本轮**未运行**任何 Q0 case、overlap workload、D2H/D2D 变体、k=3 admission、完整 Q0、GPU smoke 或 Gate 8；未生成或执行任何 construction admission 命令。
- 本轮只使用：已有机器信息、工具版本查询、编译，以及 `--list-cases`（均属冻结 checklist 明确允许的非 case qualification 手段）。
- 不因 GPU 理论支持 concurrent copy/compute、也不因平台是 Linux 或数据中心 GPU 而给出任何 overlap 预判。
- 任何静态资格结论都不构成 Gate 9 平台资格；Gate 6 保持 `FAIL`，Q0 保持 `NOT_RUN`，Gate 7 保持 `BLOCKED`。

本轮实际执行的静态动作（可复查）：

1. 本机 `nvidia-smi -L` 与 `nvidia-smi --query-gpu=...`（硬件/版本查询）。
2. 本机 `nvcc --version`、`nsys --version`、`nsys profile --help`（工具版本与参数支持查询）。
3. 本机编译冻结 microbench（`python -m exposedpath_v141 build-q0-microbench`，输出到临时目录，非仓库路径），再执行 `--list-cases` 并与冻结 manifest 的 21 个 native seed 做集合比较。
4. 只读检索仓库既有证据（receipt、runbook、manifest、历史文档）中已有的平台信息。
5. 用户在服务器侧执行本仓库提供的 CP-03 静态资格脚本（只读 `nvidia-smi`/`nvcc`/`nsys` 查询 + 在冻结 commit 上编译 microbench + `--list-cases`），其结果用于 CP-03 的 A1/A2/A3/A6 判定；该脚本同样未运行任何 case / workload / allocation probe。本会话未直接执行该服务器脚本。

## 1. Candidate Platform Inventory

### CP-01：本机 Windows 笔记本（当前会话所在机器）

| 项 | 事实 |
|---|---|
| machine / access source | Lenovo 82L5；本机直接可访问（当前会话即在此机器） |
| OS / 版本 / build | 注册表 `ProductName=Windows 10 Pro`、`DisplayVersion=25H2`、`CurrentBuild=26200`、`UBR=9457`；`[Environment]::OSVersion=10.0.26200.0`（即 Windows 11 25H2 语义，注册表沿用旧产品名） |
| bare metal / VM / container | UNKNOWN（WMI/CIM 在本会话被拒绝访问；Lenovo 机型提示物理机，Hypervisor 状态未读到） |
| 可独占 | UNKNOWN（未验证使用窗口与并发占用） |
| GPU | NVIDIA GeForce GTX 1650；compute capability 7.5；显存 4096 MiB |
| GPU UUID | `GPU-03612b49-0662-ddfb-6acc-b81c4fc6a736` |
| GPU 数量 | 1（`nvidia-smi -L` 仅列出一张） |
| CUDA driver version | 581.57（driver package 版本） |
| CUDA driver API version | **UNKNOWN**（`nvidia-smi` 的 `CUDA Version: 13.0` 是驱动支持的 CUDA 版本号，不能当作 driver API version；须以 `cudaDriverGetVersion` 一类查询为准） |
| CUDA runtime version | **UNKNOWN**（本轮未查询实际部署的 runtime 版本；`nvcc` 版本不等于 runtime 版本） |
| CUDA Toolkit / nvcc | CUDA Toolkit 13.0，`V13.0.88`，`C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.0\bin\nvcc.exe` |
| Nsight Systems 完整版本与路径 | 已安装 2025.1.3 / 2025.3.2 / 2025.6.1 / 2026.1.1；最新 `NVIDIA Nsight Systems version 2026.1.1.204-261137176666v0`，路径 `C:\Program Files\NVIDIA Corporation\Nsight Systems 2026.1.1\target-windows-x64\nsys.exe` |
| collection/export 同一 Nsight 版本 | 可用（同一 2026.1.1 采集与导出）；本轮未执行采集/导出 |
| Nsight schema 是否已被当前 adapter 审查 | **否**：本仓库已审查版本为 `2026.2.1.210 / schema 3.25.0`，本机为 2026.1.1 系列 |
| frozen microbench 是否可编译 | **PASS**（nvcc 13.0 + VS2022 Community `vcvars64`；输出 `compile_status: PASS`、`q0_execution_status: NOT_RUN`，二进制写入临时目录） |
| `--list-cases` 与冻结 21 seed 一致性 | **PASS**（列出的 21 个 case 与冻结 `native_seed_case_id` 集合完全相等，无缺失、无多余） |
| 512 MiB pinned host + device buffer | UNKNOWN（GPU 显存大小与 host RAM 都不足以证明 512 MiB pinned-host + device allocation 会成功；A7 只能由以后单独批准的最小 allocation/free capability probe 闭合） |
| launcher/adapter 前置 | PASS（Windows PowerShell launcher 与 runbook 已存在；Linux 不适用） |
| `--trace=cuda,nvtx` | PASS（2026.1.1 `profile --help` 支持 trace 选项） |
| `--capture-range=cudaProfilerApi` | PASS（同上） |
| `--cuda-graph-trace=node` | PASS（同上） |

### CP-02：实验室 Windows Server 2022 + RTX 4090

| 项 | 事实 |
|---|---|
| machine / access source | 用户中转的 Windows 服务器（bundle + RDP/共享盘工作流）；我无法直接执行命令 |
| OS / 版本 / build | `Windows-2022Server-10.0.20348-SP0`（receipt 记录） |
| bare metal / VM / container | UNKNOWN（未记录） |
| 可独占 | UNKNOWN（未记录使用窗口） |
| GPU | NVIDIA GeForce RTX 4090；24563 MiB；compute capability 未记录 |
| GPU UUID | `GPU-0d8fafe6-a1e9-33cc-25fb-632316736455` |
| GPU 数量 | 至少 1 张（同服务器另有 RTX 6000 Ada，见 CP-03） |
| CUDA driver version | 包版本未记录；receipt 的 `driver_version` 字段与 driver API 同为 `12050` |
| CUDA driver API version | 12050 |
| CUDA runtime version | 12040 |
| CUDA Toolkit / nvcc | UNKNOWN（runbook 要求 `(Get-Command nvcc).Source`，但版本未入档）。注意：同一主机栈的 Toolkit 已由 CP-03 本轮记录为 `12.4 / V12.4.131`、driver package 为 `555.99`；是否据此闭合 CP-02 的 A3 需另行确认，本文件暂不改变 CP-02 判定 |
| Nsight Systems 完整版本与路径 | `2026.2.1.210-262137639646v0`，`C:\Program Files\NVIDIA Corporation\Nsight Systems 2026.2.1\target-windows-x64\nsys.exe` |
| collection/export 同一 Nsight 版本 | PASS（采集与导出 argv 均为该版本） |
| Nsight schema 是否已被当前 adapter 审查 | **PASS**（`2026.2.1.210 / schema 3.25.0` 已审查） |
| frozen microbench 是否可编译 | PASS（既有 diagnostic 构建产物与 receipt 中 binary SHA-256 可复核） |
| `--list-cases` 与冻结 21 seed 一致性 | UNKNOWN（服务器上未记录该检查） |
| 512 MiB pinned host + device buffer 静态能力 | PASS（512 MiB H2D diagnostic 已在该平台执行成功） |
| launcher/adapter 前置 | PASS（Windows launcher 与 runbook 已就绪） |
| `--trace=cuda,nvtx` | PASS（已实际使用） |
| `--capture-range=cudaProfilerApi` | PASS（已实际使用） |
| `--cuda-graph-trace=node` | PASS（已在 r9 路径使用） |
| 构造历史（不属于冻结 k_max=3 admission） | 512 MiB H2D、64 MiB H2D、64 MiB D2H 三种不同构造均为 `overlap_ns=0`；因构造不同，**不构成**冻结清单定义的 admission FAIL |

### CP-03：同一服务器的 RTX 6000 Ada（不同 GPU，同一 OS/driver/Nsight 栈）

| 项 | 事实 |
|---|---|
| machine / access source | 与 CP-02 同一服务器；物理机型 ASUS `ESC8000A-E12`（来源为仓库文档 `CHANGE_MANIFEST.md`：`0 (6000 Ada) or 1 (4090)`，以及本轮服务器侧静态查询） |
| OS / 版本 / build | `Windows Server 2022 Datacenter`，`10.0.20348`（本轮服务器侧静态查询确认，**A1 = PASS**） |
| bare metal / VM / container | 物理机 ASUS `ESC8000A-E12`；Hyper-V 已安装且 `vmms` 服务运行（据此记录宿主状态，A1 = PASS） |
| 可独占 | **PENDING**：RTX 6000 Ada / GPU2 当前有其他用户任务运行，当前时刻不能独占；这只是临时占用，不代表正式实验时无法协调独占窗口——admission 执行前需另行确认并预留（这是 A2 唯一未闭合项） |
| GPU | index `2`；`NVIDIA RTX 6000 Ada Generation`；UUID `GPU-dff87fa4-1a85-8853-3fa7-c539b3886b38`；compute capability `8.9`；`memory.total = 49140 MiB`。**A2 = UNKNOWN / PENDING**（仅独占窗口未闭合） |
| driver package / driver API / runtime / toolkit | **PASS**：driver package `555.99`；`cudaDriverGetVersion = 12050 → 12.5`；`cudaRuntimeGetVersion = 12040 → 12.4`；Toolkit/nvcc `12.4 / V12.4.131` |
| Nsight / schema / launcher / flags | Nsight Systems `2026.2.1.210-262137639646v0`（与 CP-02 同一主机栈，schema 已审查）；A4/A5/A8/A9 = PASS |
| microbench 编译 / `--list-cases` | **PASS**：frozen HEAD `a607645e9c4fcd7df4b05d4e97fa8bf788763e47`，frozen source dirty lines = `0`；编译 `PASS`；`--list-cases` = `21/21 MATCH`；未运行任何 case；binary SHA256 `A07C4BE52ED8EB1901C2AFEA529AF3E8FB230D27861FE390DC14BD3DE5BCD308` |
| 512 MiB pinned host + device buffer | UNKNOWN（本轮未做任何 allocation；只能由以后单独批准的最小 allocation/free capability probe 闭合） |

### CP-04：任何其他可访问平台（Linux 或其他机器）

目前仓库与本机会话中**没有任何**关于其他可访问平台的信息。为避免虚构候选机器，不在此列出；请按 §5 的最小信息表提供实际可访问平台。

## 2. A1～A9 静态资格矩阵

| 条款 | CP-01 本机 GTX 1650 | CP-02 服务器 RTX 4090 | CP-03 服务器 6000 Ada |
|---|---|---|---|
| A1 平台与 OS 身份 | UNKNOWN（OS 身份已知，bare metal / VM / container 状态未确认） | UNKNOWN（OS 身份已知，bare metal / VM / container 状态未确认） | PASS |
| A2 GPU UUID 与单 GPU 独占 | UNKNOWN（UUID/数量 PASS，独占未确认） | UNKNOWN（UUID PASS，独占与 compute capability 未记录） | UNKNOWN / PENDING（GPU 身份已取得；仅独占窗口待 admission 前确认与预留） |
| A3 driver/runtime/toolkit | UNKNOWN（仅 driver package `581.57` 与 toolkit `V13.0.88` 已知；driver API 与 runtime 未取得） | UNKNOWN（toolkit/包版本未记录） | PASS |
| A4 Nsight 版本与路径 | PASS | PASS | PASS |
| A5 已审查 schema / export compatibility | UNKNOWN（2026.1.1 未审查，需只读 adapter 审查） | PASS | PASS |
| A6 compile 与冻结 `--list-cases` 一致性 | PASS（本轮实测） | UNKNOWN（`--list-cases` 未记录） | PASS（冻结 commit 编译 + `--list-cases` 21/21 一致） |
| A7 512 MiB pinned host + device buffer | UNKNOWN | PASS（依据该平台已实际执行过的 512 MiB 构造，而非算术推断） | UNKNOWN |
| A8 launcher/adapter 前置（Linux 尤其） | PASS | PASS | PASS |
| A9 冻结采集参数工具支持 | PASS | PASS | PASS |

## 3. 静态资格结论

- **没有任何候选达到 `QUALIFIED_FOR_ADMISSION_PLANNING`。**
- CP-01：`NEEDS_INFORMATION`，未闭合项为 **A1、A2、A3、A5、A7**。
- CP-02：`NEEDS_INFORMATION`，未闭合项为 **A1、A2、A3、A6**。其三种**不同**构造的 overlap=0 现场已按用户决定记为 construction-blocked baseline（不构成冻结判据下的 admission FAIL）；本轮不继续在该平台做参数搜索或根因深挖。
- CP-03：`NEEDS_INFORMATION`，未闭合项为 **A2（待 admission 前确认并预留独占窗口）与 A7（512 MiB pinned-host + device probe）**；A1、A3、A4、A5、A6、A8、A9 已 PASS。**不判为 `NOT_QUALIFIED`**，优先级不变（仍为第一候选）。
- CP-04：无信息，不判定。

因此本轮**不推荐**任何 `candidate_id` 进入 construction admission planning；应先补齐上表的 UNKNOWN 项或提供新的可访问平台信息。

### 3.1 信息补齐顺序（不构成 overlap 概率排名）

| 顺序 | candidate_id | 理由 |
|---|---|---|
| 第一优先 | CP-03（服务器 RTX 6000 Ada） | **仅因**与 CP-02 共用大量 host/software provenance（同 OS、同 driver 栈、同 Nsight 版本与已审查 schema、同 launcher 与采集参数），补齐缺口所需信息最少 |
| 第二优先 | CP-01（本机 GTX 1650） | 本机可直接补齐（独占确认、host 侧信息、schema 只读审查），且 A6 已 PASS |
| baseline（暂不作为推进对象） | CP-02（服务器 RTX 4090） | 已有三种不同构造的 overlap=0 现场，作为 construction-blocked baseline 记录；本轮不对其继续参数搜索或根因深挖 |

该顺序只反映"获取静态资格信息的成本"，**不是 overlap 成功概率排名**，也不构成对任一平台能否构造出重叠的预判。

### 3.2 根因边界（本轮保持不变）

- 已确认的事实：不同 non-blocking stream 上的 copy 与 kernel 在**真实 device timeline** 上仍然串行。
- 仍**不能**归因到 Runtime、driver、WDDM、GPU scheduler 中的任何具体一层；现有证据不足以区分层级。
- 不继续在 RTX 4090 上做参数搜索或根因深挖。

## 4. 缺失信息与最小获取方式

下表与 §2 的 A1～A9 矩阵逐条对应，覆盖每个候选的**全部** UNKNOWN 项。除 A7 需要**以后单独批准**的 allocation/free capability probe 外，其余为只读查询或已允许的非 case qualification。

| candidate_id | 缺失项（条款） | 最小获取方式 | 是否构成阻塞 |
|---|---|---|---|
| CP-01 | A1 bare metal / VM / container 状态 | 在非沙箱 shell 读取 `Win32_ComputerSystem` 的 Manufacturer / Model / HypervisorPresent（可辅以 `systeminfo`） | 是 |
| CP-01 | A2 独占 | 确认使用窗口内无其他 CUDA 进程；用 GPU UUID 过滤（`CUDA_VISIBLE_DEVICES`） | 是 |
| CP-01 | A3 driver API / runtime | 只读查询 `cudaDriverGetVersion` / `cudaRuntimeGetVersion`（driver package `581.57` 与 Toolkit/nvcc `V13.0.88` 已记录，但不足以闭合 A3） | 是 |
| CP-01 | A5 schema 审查 | 对 2026.1.1 导出的 SQLite 做只读 adapter 审查（沿用 `EP-G3-09` 模式） | 是 |
| CP-01 | A7 512 MiB pinned-host + device | **只能由以后单独批准**的最小 512 MiB pinned-host + device allocation/free capability probe 闭合；本轮不实现、不运行该 probe。host RAM / GPU 显存只作信息记录，不能使 A7 判为 PASS | 是 |
| CP-02 | A1 bare metal / VM / container 状态 | 在该服务器的用户会话中执行与 CP-01 相同的查询（本会话无法直接访问该主机） | 是 |
| CP-02 | A2 独占与 GPU 身份补全 | 确认服务器使用窗口；`nvidia-smi --query-gpu=uuid,driver_version,compute_cap,memory.total --format=csv` 补齐 compute capability 与 driver 包版本 | 是 |
| CP-02 | A3 toolkit / nvcc | `nvcc --version`（driver API `12050` 与 runtime `12040` 已记录，toolkit 未记录） | 是 |
| CP-02 | A6 `--list-cases` | 编译后在不运行任何 case 的前提下执行 `--list-cases`，与冻结 21 个 native seed 比对 | 是 |
| CP-03 | A2 独占窗口 | 当前 GPU2 有其他用户任务运行，属临时占用；admission 执行前需用户确认并预留独占窗口（GPU 身份已取得，不再是缺失项） | 是 |
| CP-03 | A7 512 MiB pinned-host + device | 只能由以后单独批准的最小 allocation/free capability probe 闭合；显存大小与当前 occupancy 均不作为判据 | 是 |
| CP-04 | A1～A9 全部 | 由用户填写 §5 最小信息表 | 是 |

## 5. 需要用户提供的 Candidate Platform Inventory 最小信息表

请对每个**实际可访问**的平台填写以下字段（不完整的字段直接写 UNKNOWN）：

| 字段 | 说明 | 填写 |
|---|---|---|
| candidate_id | 自定义代号（如 `CP-05`） | |
| access source | 我能否直接执行命令，或只能由你中转 | |
| host 标识 | 主机名/别名（可用代号） | |
| OS / 版本 / build | 精确到 build | |
| bare metal / VM / container | 三者其一或 UNKNOWN | |
| 可独占性与时间窗 | 是否可独占、可用时间段 | |
| GPU 型号 / UUID / compute capability / 显存 / 数量 | 逐项 | |
| driver 包版本 / driver API / CUDA runtime / CUDA Toolkit(nvcc) | 逐项 | |
| Nsight Systems 版本与路径 | 完整版本串 | |
| 采集与导出是否同一 Nsight 版本 | 是/否/UNKNOWN | |
| 该 Nsight schema 是否已被本仓库 adapter 审查 | 是/否/UNKNOWN | |
| host 物理内存 | **仅作信息记录**；A7 只能由单独批准的最小 512 MiB pinned-host + device allocation/free capability probe 闭合 | |
| 是否允许执行「编译 + `--list-cases`」 | 非 case qualification | |
| 是否允许后续另行审批的 construction admission | 仅记录意向，不代表授权 | |

## 6. 下一步

1. 用户补充 §5 信息表，或授权在服务器/本机执行 §4 的允许清单查询。
2. 补齐后重新评估 A1～A9，仍只有全部 PASS 者才可标为 `QUALIFIED_FOR_ADMISSION_PLANNING`。
3. 即使达到该状态，也只允许**另行提出** construction admission 执行计划并等待批准；本文件不生成也不执行任何 admission 命令。
