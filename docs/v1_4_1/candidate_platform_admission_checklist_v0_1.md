# Candidate Platform Qualification / Construction Admission Checklist v0.1（冻结）

## 0. 状态、冻结声明与使用规则

状态：**冻结**。本清单依据 `docs/v1_4_1/gate6_strategy_review_v0_1.md` §5.2 起草，并在确认任何具体候选平台**之前**冻结，用于避免按候选平台事后调整准入标准。

使用规则：

1. 本清单是构造准入（construction admission）的唯一判据来源；不得因为某个具体平台而增删条目、放宽阈值或改用其他成功判据。
2. 任何条目若要变更，必须建立新版本（`v0.2` 及以后）、说明变更理由，并重新取得批准；已按旧版本执行的准入结果不得据此追溯重判。
3. 本清单不是 Q0 执行计划，更不是平台正式资格结论。执行准入前仍需就“在某一具体平台执行准入检查”取得单独批准。
4. 本轮只冻结清单，不确认候选平台，不运行任何实验。

## A. 候选平台最低资格（全部必须满足）

- [ ] **A1 平台与 OS 身份**：记录 OS 名称/版本/内部版本、内核或等效版本、虚拟化/容器状态（如适用），以及平台是否为独占物理机。
- [ ] **A2 GPU UUID 与单 GPU 独占**：记录目标 GPU 型号与计算能力；`CUDA_VISIBLE_DEVICES` 必须使用完整 GPU UUID，且探针回读的 UUID 与目标一致；同一轮不得混用两张卡；准入运行期间该设备必须独占（无其他进程占用同一 GPU）。
- [ ] **A3 CUDA driver / runtime / toolkit**：分别记录 driver 版本、driver API 版本、CUDA runtime 版本与 CUDA Toolkit / `nvcc` 版本；不得以其中任一项代替其余项。
- [ ] **A4 Nsight Systems 版本**：记录 `nsys` 完整版本字符串与可执行文件路径（含安装来源），并记录采集与导出所用版本是否一致。
- [ ] **A5 已审查 Nsight schema / export compatibility**：export schema 必须已被仓库审查（当前已审查 `2026.2.1.210 / schema 3.25.0`）；未审查的 schema 必须先完成只读 adapter 审查（沿用 `EP-G3-09`/`EP-G3-10` 的做法），未通过前不得准入。
- [ ] **A6 microbench compile 与冻结 case 集合一致性**：微程序可在该平台编译成功，并在**不运行任何 case**的前提下通过 `--list-cases`，21 个 native seed 集合与冻结 manifest 完全一致；未知 case 必须在 CUDA 初始化前失败。
- [ ] **A7 512 MiB pinned-host/device buffer 能力**：平台可在 profiler/request 之前完成 512 MiB pinned host + device buffer 预分配，且不触发 OOM、驱动降级或隐式同步。
- [ ] **A8 Linux 候选的 launcher 前置条件**：若候选平台为 Linux，必须先在 `EP-G7-05` 的既定 adapter/launcher 边界内具备结构化（无 shell 字符串拼接）的等价命令构造与路径处理，方可准入；Windows 平台沿用既有 launcher。
- [ ] **A9 采集参数可用性**：平台支持冻结采集参数 `--trace=cuda,nvtx`、`--capture-range=cudaProfilerApi`，以及 Graph case 所需的 `--cuda-graph-trace=node`；准入本身不使用 Graph 参数。

## B. 固定 workload 与唯一变量

- [ ] **B1 构造固定**：准入只运行 `Q0-KERNEL-MEMOP-001` 一个 case，使用与冻结 Q0 完全相同的构造：**512 MiB H2D + 10 ms kernel**、两个 non-blocking stream、coordinator/worker 同时放行、无 CUDA event dependency、单一 `S_DEVICE`、标准 `--trace=cuda,nvtx`。
- [ ] **B2 唯一变量为 platform**：除平台本身外，不得改变任何参数或编排；run-id 必须体现平台与日期，并绑定代码 commit 与 git dirty state。
- [ ] **B3 禁止的参数搜索**：禁止 D2H 方向、D2D、buffer 大小调整、kernel 时长调整、stream 数量变化、线程编排变化、event/query 增删，以及任何其他为取得 overlap 而进行的参数搜索或语义修改。

## C. 预注册与早停语义

- [ ] **C1 `k_max=3` 预注册**：预注册 `k_max=3`，必须在**第一次运行前**冻结并记录；不得将 `k_max` 从 3 增加。
- [ ] **C2 构造与参数固定**：所有 attempt 使用完全相同的构造与参数，仅 run identity 不同；不得在 attempt 之间修改任何 workload 参数。
- [ ] **C3 记录预注册内容**：预注册需记录运行平台、commit、构造参数、`k_max`、每次运行标识、成功判据（见 E 节）、早停规则与停止条件。
- [ ] **C4 早停规则**：任一有效 attempt **首次**满足 `overlap_ns > 0` 且 provenance / identity / `observation_validity` / Runtime→activity mapping 全部有效时，立即判 admission PASS 并停止，不再执行剩余 attempt。
- [ ] **C5 目的限定**：本规则只判断 construction feasibility，不用于估计平台 overlap 概率，也不得外推平台一般能力。

## D. 每次运行所需 provenance（每次运行都必须完整）

- [ ] **D1 Raw**：`.nsys-rep`，含 SHA-256 与字节数。
- [ ] **D2 SQLite**：`nsys export --type sqlite --lazy=false` 产物，含 SHA-256 与字节数。
- [ ] **D3 receipt**：采集 receipt，含完整 `nsys` argv、导出 argv、运行身份、时间戳与数据角色（`Engineering`、diagnostic-only、Q0 `NOT_RUN`）。
- [ ] **D4 source manifest**：case/运行身份与该次输入绑定。
- [ ] **D5 environment**：OS、GPU UUID 与型号、driver/driver API、CUDA runtime/toolkit、Nsight 版本、default stream mode、selected device。
- [ ] **D6 Canonical**：Canonical Raw 输出的 manifest、`observation_validity` 与 `identity` 状态、逐文件哈希与记录数。
- [ ] **D7 S**：S 层 manifest、`input_validity`、逐 sync 的 `validity`/`wait_set_activity_ids`/`terminal` 以及 sync registry version 与 SHA-256。
- [ ] **D8 A/B provenance**：A/B manifest、`files` 哈希与记录数、quality 状态、`wait_set_hidden_union_ns`/`wait_set_exposed_union_ns`、`A_device_wait_kernel_only_ns`/`A_device_wait_memop_only_ns`/`A_device_wait_kernel_memop_mixed_ns`。
- [ ] **D9 独立 overlap 计算**：由 device activity 区间独立计算 `overlap_ns`，并记录两侧区间、间隔与完成顺序。
- [ ] **D10 代码与环境绑定**：commit 与 `git status`、工具路径与版本、以及 admission 报告（数据角色 `Engineering`，仅用于构造准入）。

## E. 判定规则

- [ ] **E1 success（admission PASS，早停）**：任一有效 attempt **首次**出现 `overlap_ns > 0`，且本次运行的 required provenance、identity、`observation_validity` 与 Runtime→activity mapping 全部有效（不允许以忽略 warning 之外的方式绕过）；立即判 PASS 并终止剩余 attempt。
- [ ] **E2 failure（admission FAIL）**：仅当 3 个有效 attempt 全部 `overlap_ns = 0` 时判 admission FAIL，停止并保存全部现场；不得增加 attempt。
- [ ] **E3 STOP 条件**：任一 attempt 出现 invalid / ambiguous / schema unsupported / hash failure（含哈希不符、identity 重复或缺失、adapter 未审查、observation invalid 等），立即 STOP；**不得补跑到成功**，也不得通过新增 attempt 或重采样掩盖失败现场。
- [ ] **E4 结果解释**：单次 `overlap_ns=0` 只表示“本次未观察到重叠”，不得据此宣布平台不支持该构造；一次 PASS 也只表示“本次观察到重叠”，不得外推为平台的一般能力结论。

## F. 与 Gate 6 / Q0 / Gate 9 的关系

- [ ] **F1 不改变 verdict**：admission PASS 不改变 Gate 6 verdict、不改变 Q0 状态，也不提升任何数据资格；它只允许提出“在该平台执行完整 Q0”的下一阶段申请。
- [ ] **F2 完整 Q0 的聚合要求**：完整 Q0 仍必须在同一 run / 同一环境内聚合 21 个真实 case + 2 个合成边界例；**禁止跨平台或跨环境拼接结果**。
- [ ] **F3 不是 Gate 9**：construction admission 不构成 Gate 9 的正式平台资格结论。
- [ ] **F4 仍需单独批准**：即使 admission PASS，第 3 节及后续 r11 流程仍必须取得用户对“在该平台执行完整 Q0”的单独书面批准，才允许更新并执行。

## G. 准入记录（运行前填写，运行后补齐结果）

| 字段 | 内容 |
|---|---|
| 候选平台（OS / 机型 / GPU UUID） | |
| driver / runtime / toolkit / Nsight | |
| 已审查 schema 版本 | |
| commit / dirty state | |
| 预注册 `k_max` | `3`（第一次运行前冻结；attempt 之间不得修改任何 workload 参数） |
| 早停记录 | 首次满足 `overlap_ns>0` 的 attempt（未触发则记“无”） |
| 预注册运行标识列表 | |
| 每次 `overlap_ns` 结果 | |
| 每次证据完整性（provenance / identity / validity） | |
| 最终 verdict（PASS / FAIL / STOP） | |
| 后续动作 | |
