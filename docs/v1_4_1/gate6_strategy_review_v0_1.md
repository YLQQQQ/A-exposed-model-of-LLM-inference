# Gate 6 策略审查：mixed kernel/memop 的证据来源（`EP-G6-06` 审查定稿）

> **后记（2026-09-20）：** 本文档为冻结的策略审查记录，其审查结论与判据不变；正文中“Gate 6 保持 `FAIL`、Q0 保持 `NOT_RUN`、`Q0-KERNEL-MEMOP-001` 保持 platform construction blocked、Candidate 路线推进中”等描述均为 2026-09-17 的历史状态，已由 Gate 6/Q0 `PASS`（`q0-win-4090-20260920-gate6-final-04`，package `0.2.2`，`Q0-KERNEL-MEMOP-001 = REAL_CASE_PASS`）取代；`EP-G6-07` Candidate Platform 路线只在需要第二平台（含 Linux Formal 平台）时按 Gate 9 重启。当前状态见 `docs/v1_4_1/research_progress.md` 与 `docs/v1_4_1/gate6_closeout_v0_1.md`。

## 1. 状态、决定来源与不变边界

状态：**审查定稿**。文件路径保持 `gate6_strategy_review_v0_1.md`，内容取代此前的提案版，并记录用户 2026-09-17 对 `EP-G6-06` 的四项决定及据此形成的设计。

本轮只做设计与文档，不实施任何 synthetic 变更，不运行任何服务器实验，不申请外部平台。

四项决定：

1. **Synthetic regression**：原则允许作为 Engineering regression strengthening，但不得替代 real Q0 evidence、不得改变 Gate 6 verdict、不得提升数据资格、不得扩大 scientific claim；且必须先证明新增 synthetic 相对现有覆盖存在新的未覆盖 failure mode，否则不重复实现，只固化现有覆盖与边界说明。
2. **异平台路线**：批准进入“候选平台 + construction admission”设计。第一阶段只定义候选平台资格条件与最小真实 kernel/memop overlap construction check，不运行完整 Q0。只有真实 trace 明确得到 `overlap_ns > 0` 且 provenance / observation validity 满足要求后，才允许提出在该平台执行完整 Q0 的下一阶段计划。该批准只是**方案设计批准**，不代表已授权任何外部服务器实验；具体平台与运行步骤仍需单独审核。
3. **Scope limitation**：当前不批准，保留为 fallback（见 §6）。
4. **Gate 7**：允许与 Gate 6 等待期并行推进不依赖 GPU 的 `EP-G7-01`～`EP-G7-06`，但 Gate 7 保持 `BLOCKED`，`EP-G7-07` 不得执行，Gate 8 不得启动；Gate 7 工作与 Gate 6 策略工作隔离提交。计划见 `docs/superpowers/plans/2026-09-17-gate7-isolated-plan.md`（Gate 7 隔离计划，单独提交）。

不变边界：Measurement Contract v0.2、Q0 oracle/expected、Canonical Raw schema、S/A/B/D 语义、real evaluator、聚合规则与数据资格规则均不变。当前 Gate 6 为 `FAIL`，Q0 为 `NOT_RUN`，`Q0-KERNEL-MEMOP-001` 在当前 Windows/RTX 4090 上为 platform construction blocked。

## 2. 触发事实

`Q0-KERNEL-MEMOP-001` 是 `required_for_q0=true` 的真实 required case，其 oracle 要求 `KERNEL_A` 与 `MEMCPY_B` 在设备时间轴上真实重叠（合成 expected 为 KERNEL `10..75`、MEMOP `40..90`，重叠 35 ns，terminal=`MEMCPY_B`，`A_device_wait_ns=40`，`device_wait_composition=MIXED`）。

当前 Windows / RTX 4090 / driver 12050 上，全部已执行的构造都未产生设备侧重叠：

| 构造 | copy device interval (ns) | kernel device interval (ns) | 间隔 (ns) | overlap |
|---|---|---|---|---|
| 512 MiB H2D + 10 ms kernel | `33435296..58635297` | `63136725..73137628` | `4501428` | `0`（WDDM diag-02 标准时间线） |
| 64 MiB H2D + 10 ms kernel | `22365422..26112424` | `26741607..36745367` | `629183` | `0` |
| 64 MiB D2H + 10 ms kernel | `77979638..87266973` | `88995128..98995997` | `1728155` | `0` |

第三行是本轮收录的 `EP-G6-04B` 单例（commit `a607645e`，run-id `q0-win-4090-20260917-kernel-memop-d2h-diag-64m-10ms-01`）：`S_DEVICE=VALID_NONEMPTY`、wait-set=`{MEMCPY_B,KERNEL_A}`、terminal=`KERNEL_A`，A 为 `kernel_only=10000869 ns`、`kernel_memop_mixed=0`，Canonical/S/A-B 资格有效。三项构造均使用两个 non-blocking stream、同 `contextId`、无 CUDA event dependency、Runtime API correlation 唯一。

GPU capability 探针给出 `async_engine_count=5`、`device_overlap=1`、`concurrent_kernels=1`，只说明设备声明支持相关能力。因此：**改变 H2D→D2H 方向仍未恢复真实 device overlap**，`Q0-KERNEL-MEMOP-001` 在当前平台为 platform construction blocked。现有证据不能区分 WDDM、driver、Runtime 或其他层，本文件不作任何根因判断。

证据索引：回传副本位于本地主工作区未跟踪目录 `server_evidence_inbox/q0-win-4090-20260917-kernel-memop-d2h-diag-64m-10ms-01/`（Raw `76FAEC18…`、SQLite `C9964B0E…`、source manifest `BE917E5E…`、canonical manifest `DEEEF8F2…`、S manifest `08D0B2A0…`）；服务器原始输出目录见该目录 receipt 的 `command_argv`/`export_argv`。H2D 参数诊断与 capability 证据见 research_progress 的 `EP-G6-04`、`EP-G6-04A` 条目。

## 3. 缺口定位

**已被离线证据覆盖的部分。** 重叠输入下的语义与记账已由冻结 oracle 与确定性合成 Canonical profile 覆盖：Gate 4 的 `W(s)`/terminal/validity、Gate 5 的 A 互斥守恒与 `kernel_only/memop_only/mixed` 分桶、B 的 per-sync hidden/exposed/return-tail、D/Signature 派生，均已在正式实现与独立 evaluator 上通过合成对照（`EP-G6-02`、`EP-G6-02A`）。

**仍然缺口的部分是真实观测合同本身**：在真实并发设备执行下，Nsight/Raw 能否如实给出两个同 context activity 的区间与 correlation，adapter 能否在不猜测的前提下重建两 stream 的 wait-set 成员，S 的 semantic frontier/terminal 能否在两个真实重叠 activity 上正确选择，B 能否按半开区间 union 计算而不重复计数。64 MiB D2H 单例已经覆盖“wait-set 两成员、terminal 取语义前沿、hidden/exposed 裁剪”；唯独“两个 device interval 在真实时间轴上重叠”从未在任何真实硬件证据中出现过。

## 4. 差异矩阵：现有 `KERNEL_MEMOP_MIXED` synthetic coverage 与拟新增 synthetic

复核方法：读取 `q0/oracle_cases_v0_2.json` 的 23 个 construction 与 `exposedpath_v141/q0_synthetic.py` 的 profile 生成规则。合成 profile 直接构造 Canonical 记录（`correlation_id` 为空、ownership 由 `ownership_status` 直接给定、不经过 Nsight table/adapter 或 label 恢复），再进入正式 S/A/B 与独立 evaluator。`Q0-KERNEL-MEMOP-001` 的 profile 为：`KERNEL_A` stream 2 `10..75`、`MEMCPY_B` stream 4 `40..90`、`S_DEVICE` `50..100`、`default_stream_mode=PER_THREAD`、`input_status=VALID`。

| 覆盖维度 | 现有 coverage（证据） | 拟新增 synthetic 的增量 | 判定 |
|---|---|---|---|
| 重叠 device interval 进入同一 `W(s)` | `KERNEL-MEMOP`（kernel+memop 跨 stream 重叠）、`DEVICE`/`CONTEXT`（两 kernel 重叠）、`OVERLAPPING-HOST-SYNC`、`STREAM-001` | 无 | 不新增 |
| A 的 `kernel_only/memop_only/mixed` 分桶与整数守恒 | `KERNEL-MEMOP` 合成 profile；`tests/test_v141_a_accounting.py` 另有手算 15/5/5 与 10/5/10 断言 | 无 | 不新增 |
| B 的 hidden/exposed/return-tail、重叠 wait-set 按 union 不重复计数 | `KERNEL-MEMOP` 合成 profile；Gate 5 定向回归含重叠 wait-set union 与 completion-boundary terminal | 无 | 不新增 |
| terminal 由语义前沿决定且跨 kind（terminal=MemOp） | `KERNEL-MEMOP`（terminal=`MEMCPY_B`） | 无 | 不新增 |
| terminal 并列（0 ns 语义容差） | `TERMINAL-TIE`（两 kernel 同时结束） | kernel↔memop 并列属新组合，但 tie 规则与 kind 无关，走同一 frontier 路径 | 边际价值低，不新增 |
| 跨 stream 无依赖的重叠不得进入 `W(s)` | `STREAM-001`（`K_OTHER`）、`DEFAULT-PTDS`（`UNRELATED_OVERLAP`） | 无 | 不新增 |
| 三个及以上活动同时进入同一 `W(s)` | 现有 profile 每个 sync 最多 2 个活动 | 2 kernel + 1 memop 的三重重叠分桶 | 唯一候选新组合；但原子切分、union 与 kind 集合判定已由 2 活动与多窗 profile 覆盖 |
| 跨 phase 且重叠（例如 decode 与 prefill 活动同时进入一个 `W(s)`） | `PHASE-SPILL` 只用单活动跨 phase | 跨 phase + 重叠的组合 | 两条路径各自已覆盖，组合未覆盖；边际价值低 |
| `MEMSET` 类型 memop 参与 mixed | oracle 只用 `MEMCPY`；`terminal_kind=MEMOP` 同时接受 `MEMCPY/MEMSET` | MEMSET+kernel 混合 | A/B 按 activity kind 分类，kind 级已统一；边际价值低 |
| **真实观测合同**（correlation → launch API → 唯一 structured marker → Nsight table/adapter → Canonical identity） | 合成 profile 不经此路径（`correlation_id` 为空、ownership 直接给定） | **synthetic 原理上无法覆盖** | 真实缺口，只能靠真实 trace |

**结论（对应决定 1）**：本次差异矩阵未发现独立的、未被任何现有 profile 触发的 semantic/accounting failure mode；表中列出的候选组合都只是同一冻结语义下的窄组合，且其底层原语已被 2 活动 profile 与 Gate 5 定向回归覆盖。因此**不实施新增 synthetic profile**，也不把 synthetic 结果用于 Gate 6 verdict 或任何 claim；`EP-G6-08` 只负责把现有 synthetic coverage 与“synthetic ↔ real”的角色边界写成书面说明，不改实现、不新增 case。

### 4.1 `EP-G6-08` 边界固化（定稿，2026-09-17）

**现有 `KERNEL_MEMOP_MIXED` synthetic 已覆盖的事实**（证据：`q0/oracle_cases_v0_2.json` 的 `Q0-KERNEL-MEMOP-001`、`exposedpath_v141/q0_synthetic.py` 的 profile 规则、`EP-G6-02`/`EP-G6-02A` 与 Gate 4/5 定向回归）：

- mixed wait-set：`KERNEL_A`（stream 2，`10..75`）与 `MEMCPY_B`（stream 4，`40..90`）同时进入 `S_DEVICE`（`50..100`）的 `W(s)`，两者 device interval 部分重叠。
- A 层：mixed 分桶与整数纳秒守恒成立，`device_wait_composition=MIXED`；并有手算 `15/5/5` 与 `10/5/10` 的独立单元断言。
- B 层：按半开区间 union 计算 hidden/exposed 而不重复计数，terminal 取语义前沿且可跨 kind（terminal=`MEMCPY_B`）。
- 相关语义：无依赖的跨 stream 重叠不得进入 `W(s)`（`STREAM-001`、`DEFAULT-PTDS`）、terminal 并列（`TERMINAL-TIE`）、completed-before、以及 validity/ambiguous/invalid 的 fail-closed 传播。

**synthetic 无法替代 real observation contract 的原因**：

1. 合成 profile 直接构造 Canonical 记录，`correlation_id` 为空、ownership 由 `ownership_status` 直接给定，不经过 Nsight table/adapter 与 `correlation → launch API → 唯一 structured marker` 的标签恢复路径。
2. 因此它无法证明真实 trace 中两个并发 device activity 的区间、context/stream 归属与 Runtime API mapping 能被如实记录并唯一恢复。
3. 它也无法产生“真实设备确实在同一时间轴上重叠执行”的证据——这正是当前平台 construction blocked 的唯一缺口。

**结论**：synthetic 只作为 Engineering regression strengthening，不得用于 Gate 6 verdict、Q0 资格或任何 claim 扩展；本项为纯文档固化，不新增 profile、不修改实现。

## 5. 异平台 construction admission 设计草案（`EP-G6-07`）

### 5.1 性质

admission 只回答“该平台能否构造出满足 oracle 的真实 kernel/memop overlap 观测对象”。它不运行完整 Q0，不产生 Q0 资格，也不构成 Gate 9 的正式平台资格结论。本节为设计草案，未授权任何外部平台实验。

### 5.2 候选平台最低资格

资格要求已**冻结**为 `docs/v1_4_1/candidate_platform_admission_checklist_v0_1.md`（A 节 A1～A9），判定一律以该冻结清单为准，本节不重复其条目：平台/OS 身份、GPU UUID 与单 GPU 独占、driver/runtime/toolkit 版本、Nsight Systems 版本、已审查的 Nsight schema 与 export compatibility、microbench compile 与冻结 `--list-cases` 一致性、512 MiB pinned-host/device buffer 能力、Linux 候选的 `EP-G7-05` launcher 前置条件，以及冻结采集参数可用性。

该清单在确认任何候选平台**之前**冻结，以避免按候选平台事后调整准入标准；§5.3～§5.7 的要点同样已固化为该清单的 B～F 节，执行与判定以清单为准。

### 5.3 固定 workload 与变量

- 只运行 `Q0-KERNEL-MEMOP-001` 一个 case，使用与冻结 Q0 完全相同的构造：512 MiB H2D + 10 ms kernel、两个 non-blocking stream、coordinator/worker 同时放行、无 CUDA event dependency、单一 `S_DEVICE`、标准 `--trace=cuda,nvtx`。
- 唯一允许变化的变量是平台本身；run-id 必须体现平台与日期，并绑定代码 commit 与 dirty state。
- 禁止：任何参数搜索（copy 大小、kernel 时长、stream 数量、线程编排）、D2D 变体、为得到 overlap 而增删 event/query，或修改 microbench 语义与标签。

### 5.4 预注册的尝试次数与早停语义（冻结）

- 预注册 `k_max=3`，必须在第一次运行前冻结；不得把 `k_max` 从 3 增加，也不得在 attempt 之间修改任何 workload 参数。
- 所有 attempt 使用完全相同的构造与参数，仅 run identity 不同。
- 任一有效 attempt **首次**满足 `overlap_ns > 0`，且 provenance / identity / `observation_validity` / Runtime→activity mapping 全部有效时，立即判 admission PASS 并停止，不再执行剩余 attempt（早停）。
- 只有 3 个有效 attempt 全部 `overlap_ns = 0` 才判 admission FAIL。
- 任一 attempt 出现 invalid / ambiguous / schema unsupported / hash failure 等，立即 admission STOP；STOP 不得通过新增 attempt“补跑到成功”。
- 本规则只判断 construction feasibility，不用于估计平台 overlap 概率，也不得外推平台一般能力。
- 单次 `overlap_ns=0` 只表示“本次未观察到重叠”，不得据此宣布平台不支持该构造。

### 5.5 成功、失败与停止条件

| 结果 | 判据 | 动作 |
|---|---|---|
| admission PASS（早停） | 任一有效 attempt **首次**出现 `overlap_ns>0`，且 provenance / identity / `observation_validity` / Runtime→activity mapping 全部有效 | 立即判 PASS 并停止，不再执行剩余 attempt；记录并进入 §5.7 硬门槛审查；**不自动**进入完整 Q0 |
| admission FAIL | 3 个有效 attempt 全部 `overlap_ns=0` | 停止，保存全部现场；不得增加 attempt 或改变参数，如需再试必须重新批准 |
| admission STOP | 任一 attempt 出现 invalid / ambiguous / schema unsupported / hash failure 等 | 立即停止，不做补救式重采样，也不得补跑到成功；先修复或重新设计准入方案 |

### 5.6 所需 evidence（admission 产物）

`.nsys-rep` Raw、`--lazy=false` SQLite、source manifest、receipt（完整 argv、环境、GPU UUID 与版本）、Canonical/S/A-B 派生目录、device interval 与 `overlap_ns` 的独立计算、SHA-256 哈希链、代码 commit 与 dirty state，以及一份 admission 报告（数据角色 `Engineering`、Q0 `NOT_RUN`、明确只用于构造准入）。

### 5.7 通过 admission 后进入完整 Q0 的硬门槛（全部满足才可提出下一阶段计划）

1. admission PASS，且 evidence 完整可复核。
2. 平台身份与软件栈在同一 run 环境内冻结。
3. 该平台的 Nsight schema 与 Canonical adapter 一致（否则先完成只读审查）。
4. 21 个 native case 与 3 个故障 case 的采集参数在该平台逐一可行（可用 dry-run 证明，不执行真实 case）。
5. 21 个真实 case + 2 个合成边界例必须在同一 run/同一环境下一次聚合通过；不得拼接不同平台或不同环境的结果。
6. 取得用户对“在该平台执行完整 Q0”的单独批准。

## 6. Scope limitation 的定位（fallback，不是当前选择）

当前**不批准**任何 scope limitation。不得因为当前 Windows/RTX 4090 construction blocked 而缩窄 Q0 case、Gate 6 要求或 scientific claim。

只有当（a）确认异平台短期不可得，或（b）按 §5 的预注册资格与构造尝试仍未取得真实 overlap 时，才可单独提出 scope amendment。该 amendment 必须明确其对研究问题、claim 边界、oracle/Q0 requirement、Measurement Contract 版本与后续 protocol freeze 的影响，并单独审核；本文件不预设其内容。

## 7. 全程保持不变的约束

- Gate 6 保持 `FAIL`，Q0 保持 `NOT_RUN`，`Q0-KERNEL-MEMOP-001` 保持 platform construction blocked。
- 不做 D2D，不运行 64 MiB/1 ms，不建立 r11，不在当前平台继续参数搜索。
- 不修改 oracle、Canonical、S、A/B、evaluator 或 Measurement Contract。
- 不对 WDDM、driver、Runtime 或其他层作根因归因。
- 合成证据不得升级为 Q0 真实证据；Gate 6 verdict 只有在唯一 `q0_gate_report.json` 对完整 Q0 聚合显示 `23/23`、`verdict=PASS`、`q0_status=PASS` 时才能判为 `PASS`；其中 21 个 real case 必须全部由真实证据通过，2 个 synthetic-only boundary case 只承担其冻结的边界角色，synthetic 不得替代任何 real case。
- 通过 re-export、放宽 identity/ownership/terminal 规则或 fallback 默认值掩盖缺失证据的做法一律禁止。

## 8. 下一步

- `EP-G6-07`：本文件 §5 的设计已提出，资格与准入判据已冻结为 `docs/v1_4_1/candidate_platform_admission_checklist_v0_1.md`；候选平台确认与“在某一具体平台执行准入检查”仍待单独决定与授权。
- `EP-G6-08`：**已完成**（本文件 §4.1）。只固化现有 synthetic coverage 与“synthetic ↔ real”边界说明，未改实现、未新增 profile。
- `EP-G7-01`～`EP-G7-06`：允许并行推进，计划见 `docs/superpowers/plans/2026-09-17-gate7-isolated-plan.md`（单独提交）；Gate 7 verdict 保持 `BLOCKED`，`EP-G7-07` 与 Gate 8 不启动，且不借并行推进修改 Gate 6/Q0 requirement 或数据资格。
- 第 3 节及后续 r11 当前仍一律禁止执行；只有准入 PASS 之后再取得单独书面批准，才允许更新并执行。
