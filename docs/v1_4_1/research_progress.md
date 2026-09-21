# ExposedPath 科研进度清单

> 一句话状态：**Gate 0～6 = `PASS`（Gate 6 / Q0 已完成）；Gate 7 的 `EP-G7-08`、`EP-G7-09` 已完成，当前唯一下一步是 `EP-G7-10`。**
> 本文件是仓库内**唯一的科研进度事实源**：记录“现在做到哪里、证据在哪里、下一步是什么”。研究设计文档说明“为什么做、应该怎样做”。

## 0. 项目速览与交接入口（第一次接手请先读本节）

### 0.1 研究对象、立意与目标

- **研究对象**：单 GPU、单请求内部的异步 Host 与加速器执行，如何经由同步与完成行为形成**用户可感知的纯模型推理时延**。
- **核心区分**：`Activity Cost ≠ Request-Visible Exposure`。kernel 时长、API 时长、GPU 利用率、时间重叠都不能直接解释为延迟贡献。
- **目标**：建立可机器验证的 `Raw → S → {A, B} → D / Exposure Signature` 证据链，并用 `Correctness → Information Gain → Decision Gain` 三段证据回答三个问题：暴露在哪里、这些暴露是否可解释或可预测、能否指导决策。
- **范围边界（未经明确批准不得扩张）**：单 GPU、请求内部 Host-device exposure。不扩展到多 GPU、分布式 serving、并发 ownership、硬件因果归因或通用性能预测。

### 0.2 方法链与不变量

| 层 | 回答的问题 | 关键不变量 |
|---|---|---|
| Raw / Canonical | 观测到了什么事实 | 只记录可观察事实与 identity/clock/lineage；缺证据 fail closed，不补零 |
| S | 同步点 `s` 返回前**必须**完成哪些活动 | `W(s)` 由 CUDA 完成语义决定，不由时间重叠决定；terminal 只在证据充分时唯一 |
| A | 用户可见墙钟暴露在哪里 | 按 request/phase 互斥、保守、整数纳秒守恒；窗口只来自结构化 request/phase |
| B | 单次同步内部发生了什么 | per-sync provenance，validity 未通过时全部为 null；不得跨同步求和 |
| D / Exposure Signature | 顶层导航与机制摘要 | 只从冻结后的 A/B 纯派生，不构成硬件根因结论 |

### 0.3 数据角色与平台边界

- **数据角色**：`Prototype` / `Engineering` / `Pilot` / `Formal` 严格分开；复制、改名或重新分析都不能提升资格。当前只有 `Prototype` 与 `Engineering` 数据，**无合格 Pilot/Formal 数据**。
- **当前唯一声明的目标 observation stack**：Windows + RTX 4090（UUID `GPU-0d8fafe6-a1e9-33cc-25fb-632316736455`）+ CUDA 12.4.131 + Nsight 2026.2.1 + package/analyzer `0.2.2`。Q0 资格只在该栈上取得。
- **第二平台（含 Linux）**：不声明支持；其 launcher、smoke、平台资格检查与 Q0 属 Gate 9。任一平台未通过该平台的真实 smoke 前不得声称受支持。

### 0.4 文档地图（按接手顺序）

| 路径 | 作用 |
|---|---|
| `docs/current/ExposedPath_研究设计.docx`（文内版本 v7.1） | 研究主体：背景、立意、目标、方法与成败判据 |
| `docs/current/ExposedPath_实验协议.docx`（文内版本 v2.1） | 当前执行依据（仍为 `Pre-Pilot`，不是 Protocol Freeze） |
| `AGENTS.md`、`.agents/skills/exposedpath-research-protocol/` | 仓库协作规范与研究协议 skill（含 `references/method-semantics.md`、`references/stage-gates.md`） |
| `CONTEXT.md` | 统一研究语言：该说与不该说的术语表 |
| `docs/v1_4_1/measurement_contract_v0_2.md` + `docs/v1_4_1/contracts/*.json` | 机器合同与版本化 schema（Measurement Contract / Canonical / S / A-B / Derived / Q0） |
| `docs/v1_4_1/q0_oracle_design_v0_2.md`、`q0/oracle_cases_v0_2.json` | Q0 独立标准答案（23 个必需 case） |
| `docs/v1_4_1/gate6_closeout_v0_1.md` | **Gate 6 论文级技术总结**：身份/哈希、根因→amendment→implementation→verification 映射、成熟度与遗留限制 |
| `docs/v1_4_1/gate6_windows_server_runbook.md` | Q0 正式服务器采集／导出／派生／provenance 操作手册 |
| `docs/superpowers/plans/2026-09-20-gate7-execution-plan.md` | 当前 Gate 7 执行计划（`EP-G7-08`～`EP-G7-11`） |
| `docs/v1_4_1/candidate_platform_inventory_v0_1.md`、`candidate_platform_admission_checklist_v0_1.md` | 第二平台静态盘点与冻结的准入判据（仅在 Gate 9 需要时启用） |
| `docs/prototype_archive/README.md` | 旧 Prototype 封存说明（历史数据只能用于回归，不能作为 v1.4.1 证据） |

### 0.5 30 分钟接手路径

1. 读本文件 §0～§2 与 §6～§7：当前状态、Gate 状态、下一步。
2. 读 `docs/current/ExposedPath_研究设计.docx` 第 1 章（背景与立意）与 `docs/current/ExposedPath_实验协议.docx`（执行语义）。
3. 读 `CONTEXT.md` 统一术语，再读 `AGENTS.md` 与 research protocol skill 的 `method-semantics.md`。
4. 需要看实现时：`exposedpath_v141/`（Canonical/S/A/B/D/Q0 计算与 CLI）、`q0/`（微程序、manifest、oracle）、`tests/`。
5. 需要复现 Gate 6 结论时读 `gate6_closeout_v0_1.md`；需要重跑 Q0 时读 runbook（**不得**在未获批准时重跑 Gate 6 采集）。
6. 开始新工作时读 `docs/superpowers/plans/2026-09-20-gate7-execution-plan.md`，从 `EP-G7-08` 开始。

## 1. 当前快照

- 清单版本：`7.3`
- 最近更新：`2026-09-21`
- 权威研究主体：`docs/current/ExposedPath_研究设计.docx`，文内版本 `v7.1`
- 当前执行依据：`docs/current/ExposedPath_实验协议.docx`，文内版本 `v2.1`；仍为 `Pre-Pilot`，不是 `Protocol Freeze`
- 当前研究阶段：`Engineering`
- 当前工作分支：`codex/gate7-runner`（从 Gate 6 canonical closeout `478b945` 创建的隔离 worktree）
- 当前数据资格：Gate 6 `final-04` 提供 `Engineering` / `Q0_QUALIFICATION_ONLY` 资格证据；历史 trace 仍仅限 `Prototype/Engineering`；尚无 `Pilot/Formal` 合格数据
- 当前 Gate 状态：Gate 0～6 = `PASS`；Gate 7 = `NOT_RUN`（`EP-G7-08`、`EP-G7-09` 已完成，待 `EP-G7-10`/`EP-G7-11`）；Gate 8 = `NOT_RUN`（不得在 Gate 7 acceptance 前启动）；Gate 9～11 = `BLOCKED`（Formal 平台未确定/未接入）；Gate 12～14 = `NOT_RUN`
- 当前最高优先级：Gate 7 `EP-G7-10`（旧编号 `EP-G7-05`＋`EP-G7-06` 基线失败部分已合并）——平台适配隔离并给出两项既有 smoke 失败的最终处置；完整步骤、acceptance 与 STOP 条件见 §5 与 `docs/superpowers/plans/2026-09-20-gate7-execution-plan.md`
- 当前总体判断（2026-09-20）：Gate 6 / Q0 已正式 `PASS`。frozen run `q0-win-4090-20260920-gate6-final-04` 在 package/analyzer `0.2.2`、formal binary SHA256 `4DFF82028F4FCFB57D42ABF061AE8962C1867DCE19DF23808D223B425868FC80` 下完成：21/21 `REAL_CASE_PASS`、2 个 synthetic-only case（`Q0-TERMINAL-TIE-001`、`Q0-SUBMISSION-RACE-001`）PASS、23/23 `SYNTHETIC_PASS`，且存在唯一一份 `q0_gate_report.json`（schema `exposedpath-q0-gate/0.2.0`、`23/23`、`verdict=PASS`、`q0_status=PASS`、report count `1`）。该 PASS 只说明当前 analyzer 在本目标 observation stack 上取得 **Q0 正确性资格**；不等于 Engineering Pilot、Pilot、Protocol Freeze 或 Formal 结果，也不建立第二平台等价性。身份、哈希、provenance caveat、根因映射与实现成熟度见 `docs/v1_4_1/gate6_closeout_v0_1.md`。
- 当前到达点（`EP-G7-09`）：runner 已统一首/后续 Token 的 Host-readable completion boundary，并冻结 Pass0/Pass1 parity identity（workload / GPU / execution strategy / phase boundary / environment snapshot / attempt plan 六组字段）；`cross_pass_parity.json` 升级为 `exposedpath-v3-cross-pass-2`，缺失身份一律 `PASS_PARITY_IDENTITY_MISSING` fail closed；attempt/exclusion/retry/data-role 已机器可读，planned repeat index 必须恰好记账一次。Gate 7 verdict 仍为 `NOT_RUN`，下一步是 `EP-G7-10`，不是 Gate 8。

历史快照（保留，不覆盖；以下描述 2026-09-19 及更早的当时状态，均已由 2026-09-20 Gate 6 PASS 取代，详细过程见 `docs/v1_4_1/gate6_closeout_v0_1.md`）：

- 2026-09-19（Gate 6 `final-01`）：frozen run `q0-win-4090-20260919-gate6-final-01` 跑完采集链与 16 个 real evaluator，`Q0-KERNEL-MEMOP-001 = REAL_CASE_PASS`，4 例 semantic FAIL（`Q0-MISSING-CORR-001`、`Q0-EXTERNAL-001`、`Q0-MULTITHREAD-ORDERED-001`、`Q0-OVERLAPPING-HOST-SYNC-001`），`Q0-PHASE-SPILL-001` 因 analyzer blocker 未完成，无 `q0_gate_report.json`。该 run 为 frozen incomplete Engineering run：不续跑、不重跑、不拼接、不升级为 Gate PASS。**当时状态**：Gate 6 `FAIL`、Q0 `NOT_RUN`、Gate 7 `BLOCKED/暂停`、Gate 8 未启动。
- 2026-09-18：formal-shape 配对 diagnostic（`q0-win-4090-20260918-kernel-memop-h2d-formalshape-warmup-02`）证明 `Q0-KERNEL-MEMOP-001` 的构造失败可由 pre-capture same-kernel warm-up 恢复（B：overlap `10000741 ns`、`S_DEVICE=VALID_NONEMPTY`、wait set `{KERNEL_A,MEMCPY_B}`、terminal `MEMCPY_B/MEMOP`），推翻“平台 incapable”解释；不作 LAZY/WDDM/driver/Runtime 机制归因。**当时状态**：Gate 6 `FAIL`、Q0 `NOT_RUN`。
- 2026-09-17（`EP-G6-06` 策略决定）：synthetic 只允许作为 Engineering regression strengthening；差异矩阵未发现新增覆盖价值，故不新增 synthetic profile，只固化 coverage 与边界（`EP-G6-08`）；批准进入“候选平台 + construction admission”**设计**（不代表授权任何外部平台实验）；scope limitation 不批准、仅作 fallback；该轮 r11 及后续当时一律禁止执行。

## 2. 使用与更新规则

1. 每项任务使用稳定编号；计划调整时不得重排或复用旧编号。取消或合并的任务保留并标注状态，不得直接删除历史。
2. 任何实质性的研究定义、代码、测试、实验、证据资格或执行计划变化，都必须在同一次提交中更新本清单。
3. 完成项必须同时给出可复查证据。只有文档、代码或测试存在但尚未满足完成条件时，不得勾选完成。
4. Gate 只能使用 `PASS`、`FAIL`、`BLOCKED`、`NOT_RUN`。局部测试通过、mock 通过或无法运行 GPU 测试，不能写成 Gate `PASS`。
5. `Prototype`、`Engineering`、`Pilot`、`Formal` 数据资格分开记录；复制、改名或重新分析不能提升数据资格。
6. 计划改变时同步更新 §8「计划调整记录」，说明原因、受影响编号、顺序变化，以及是否影响已冻结协议或 Formal 数据。
7. 每次结束实质性工作前，至少核对：完成状态、Gate verdict、证据、阻塞原因、当前最高优先级和下一项任务。

状态标记：`[x]` 表示完成；`[ ]` 后注明“进行中、未开始、受阻或取消”。Gate verdict 与任务勾选相互独立。

## 3. Gate 0～6 完成摘要

### Gate 0：封存旧 Prototype

**Gate verdict：`PASS`。** 只表示旧实现、Raw 身份、基线和限制已封存，不表示 v1.4.1 方法正确或 Q0 已通过。

- [x] `EP-G0-01` 固定旧 prototype 提交和标签。证据：标签 `prototype-windows-v0.1`，提交 `abab013c5483109007ab5a2a232438d46bbaf02b`。
- [x] `EP-G0-02` 固定三份历史 `.nsys-rep` 的文件大小和 SHA-256。证据：`docs/prototype_archive/raw_trace_manifest_v1.json`。
- [x] `EP-G0-03` 记录采集/读取环境、测试基线和已知失败。证据：`docs/prototype_archive/README.md`。
- [x] `EP-G0-04` 历史数据只能用于 Prototype/Engineering 回归，不能作为 Q0、Pilot 或 Formal 证据。

### Gate 1：Measurement Contract v0.2

**Gate verdict：`PASS`。** 只表示 phase/Token、同步身份、completion scope、`W(s)`、terminal、validity、A/B 和派生规则已形成版本化、机器可检查且无未决语义占位的合同；不表示实现正确或 Q0 已通过。

- [x] `EP-G1-01` 完成 `Nsight SQLite -> observation report` 合同草案 0.1。证据：`docs/v1_4_1/analyzer_contract_v0_1.md`。
- [x] `EP-G1-02` 定义 Request、Prefill、Decode、首 Token 和后续 Token 的可观察完成边界。
- [x] `EP-G1-03` 定义自然逐 Token 同步、N1 人为同步与仅标记版本的互斥身份，并冻结 Pass0/Pass1 完成行为等价。
- [x] `EP-G1-04` 冻结 stream、device、context、event 的 completion scope；同步 copy 保持透明 unsupported。证据：`docs/v1_4_1/contracts/sync_semantics_registry_v0_2.json`。
- [x] `EP-G1-05` 冻结 `W(s)` 的提交证明、同流/event/default-stream 传递依赖、ownership 和排除规则。
- [x] `EP-G1-06` 冻结 terminal 的 semantic frontier 优先规则、并列候选及 0 ns 语义容差。
- [x] `EP-G1-07` 冻结 `VALID_NONEMPTY/VALID_EMPTY/AMBIGUOUS/INVALID`、原因码优先级和 A/B fail-closed 传播。
- [x] `EP-G1-08` 冻结 A/B 字段、互斥/守恒、B per-sync 生命周期，以及 D/Exposure Signature 的纯派生规则。
- [x] `EP-G1-09` 为 37 条合同规则建立 25 个验证案例映射并完成内部合同审查。证据：`docs/v1_4_1/contracts/measurement_contract_test_map_v0_2.json`、`tests/test_v141_contract.py`；`python -m exposedpath_v141 validate-contract` 输出 `37/37 (100%)` 与 `PASS`。

**后续状态（2026-09-20）：** Gate 2～6 已全部完成，Gate 6 / Q0 已 `PASS`。本 Gate 不再有待办或前序条件；当前状态以 §1 与 §5 为准。

### Gate 2：设计 Q0 独立标准答案

**Gate verdict：`PASS`。** 只表示 23 个受控案例的 expected/oracle 已预先写定、可机器校验且独立于被测 analyzer。

- [x] `EP-G2-01`～`EP-G2-03` 建立 23 个必需受控用例并预写 `W(s)`、terminal、validity 和 A/B 关系。证据：`q0/oracle_cases_v0_2.json`。
- [x] `EP-G2-04` AST 独立性检查：禁止 oracle 导入旧 analyzer 或未来 Raw/S/A/B 实现，禁止区间函数读取 dependency edges。证据：`scripts/verify_q0_oracle_independence.py`。
- [x] `EP-G2-05` 完成 7 正例、7 边界例、2 含糊例、7 负例及 25 特性覆盖审查。证据：`docs/v1_4_1/q0_oracle_design_v0_2.md`、`tests/test_v141_q0_oracle.py`；CLI 输出 `DESIGN_ONLY_PASS`。

### Gate 3：Canonical Raw 层

**Gate verdict：`PASS`。** 只表示唯一、版本化 Canonical Raw schema、只读转换器、identity/fail-closed 边界和三份历史 trace Engineering 回归通过。

- [x] `EP-G3-01`～`EP-G3-02` 独立入口 `python -m exposedpath_v141 inspect-sqlite`；对支持的 Nsight schema、必需表/字段、sync correlation 与 dropped records 执行 fail-closed 检查。
- [x] `EP-G3-03`～`EP-G3-04` 三份历史 trace 的 observation 回归稳定；因缺 source manifest 保持 `ambiguous`。证据：`engineering_evidence/observation_v0_1/`、`tests/test_v141_observation.py`。
- [x] `EP-G3-05`～`EP-G3-07` 冻结 Canonical Raw v0.2（八类记录、结构化 NVTX、单 trace 相对纳秒时钟、source-row identity、lineage、资格字段），实现只读 gzip JSONL 转换与合成/历史回归。证据：`docs/v1_4_1/contracts/canonical_raw_schema_v0_2.json`、`canonical_raw_v0_2.md`、`tests/test_v141_canonical_raw.py`。
- [x] `EP-G3-08` 下游边界静态检查：禁止未来 S/A/B 导入 sqlite3 或直接引用 Nsight 私有表名。证据：`scripts/verify_canonical_raw_boundary.py`。
- [x] `EP-G3-09`～`EP-G3-10` Windows/Nsight `2026.2.1.210` adapter 审查，以及 Q0 observation scope 固定（目标 request 外未映射同步记 `HARNESS_OUTSIDE_REQUEST` warning；目标 request 内与非 Q0 trace 继续 fail closed）。

### Gate 4：S 同步语义层

**Gate verdict：`PASS`。** 只表示 S v0.2 的离线语义实现、版本化输出、合成 fixture、Q0 核心 expected 对照及历史 trace fail-closed 回归通过。

- [x] `EP-G4-01`～`EP-G4-02` 实现 stream/device/context/event completion scope、可观察依赖图与每个 physical sync 的 `W(s)`，以及 ownership、submission evidence、semantic frontier、唯一 terminal、0 ns tie、validity 与原因优先级。证据：`exposedpath_v141/sync_semantics.py`、`tests/test_v141_sync_semantics.py`。
- [x] `EP-G4-03`～`EP-G4-04` 验证 completed-before 活动仍在 `W(s)`、无依赖跨流重叠不进入 `W(s)`，且缺失 correlation 的 invalid 不被提交歧义掩盖。
- [x] `EP-G4-05` 冻结 S schema 与 `analyze-s` CLI，完成确定性 fixture、Raw→S 边界和历史 trace 回归。证据：`docs/v1_4_1/contracts/s_layer_schema_v0_2.json`、`docs/v1_4_1/s_layer_v0_2.md`、`engineering_evidence/s_layer_v0_2/historical_regression.json`。
- 注：Gate 6 合成 Q0 复核额外发现并修正一处 fail-closed 缺口——graph activity 缺少 node mapping 时，S 必须在判定 `GRAPH_MAPPING_UNSUPPORTED/INVALID` 的同时清空 `W(s)`、origin phase 与 cross-phase 派生状态。

### Gate 5：A/B，再到 D/Exposure Signature

**Gate verdict：`PASS`。** 只表示 A/B 与纯派生层 v0.2 的离线语义实现、严格输入联结、版本化输出、合成测试、边界检查、历史 Engineering fail-closed 回归和完整分支独立复审通过。

- [x] `EP-G5-01`～`EP-G5-02` 冻结 A/B 输入联结与窗口规则，实现面向 request/phase、互斥且保守的 A 与整数纳秒守恒／invalid-ambiguous 传播。证据：`exposedpath_v141/ab_inputs.py`、`a_accounting.py`、`intervals.py`、`docs/v1_4_1/contracts/ab_schema_v0_2.json`。
- [x] `EP-G5-03` 实现保持 per-sync provenance 的 B，禁止无依据跨同步求和。证据：`exposedpath_v141/b_provenance.py`、`tests/test_v141_b_provenance.py`。
- [x] `EP-G5-04`～`EP-G5-05` 仅从冻结后的 A/B 派生 D 与 Exposure Signature（零分母输出 `null`，不输出根因/瓶颈标签）。证据：`exposedpath_v141/derived.py`、`docs/v1_4_1/contracts/derived_schema_v0_2.json`。
- [x] `EP-G5-06` 完成互斥、守恒、provenance、版本与 validity 传播的离线验收和独立复审（`Approved`）。历史链路无合格 A window、S 446 invalid 且 B 446 `B_INVALID`。证据：`engineering_evidence/ab_v0_2/historical_regression.json`。

### Gate 6：Q0 资格验证

**Gate verdict：`PASS`（2026-09-20）。Q0 = `PASS`。** frozen run `q0-win-4090-20260920-gate6-final-04` 在 package/analyzer `0.2.2`、frozen HEAD `4720881f400762d98f4d0759b1ffb55708968970`、implementation `ec945a67f048ff624e3701229d287894b9701ea3`、formal binary SHA256 `4DFF82028F4FCFB57D42ABF061AE8962C1867DCE19DF23808D223B425868FC80` 下完成：21/21 real `REAL_CASE_PASS`、2/2 synthetic-only PASS、23/23 `SYNTHETIC_PASS`，且只存在一份 `q0_gate_report.json`（`exposedpath-q0-gate/0.2.0`、`23/23`、`verdict=PASS`、`q0_status=PASS`、report count `1`，SHA256 `3A94F8B9B65294D82929EF183C59C4C84177D489F5AE9E8AF56FDDD676178967`）。

该 PASS 只说明当前 analyzer 在本目标 observation stack（Windows + RTX 4090 + CUDA 12.4.131 + Nsight 2026.2.1）上取得 **Q0 正确性资格**；不等于 Engineering Pilot、Pilot、Protocol Freeze 或 Formal 结果，也不建立第二平台等价性。完整 closeout（身份、哈希、缺失 prepare-time sidecar 边界、根因映射、实现成熟度、已关闭诊断分支）见 `docs/v1_4_1/gate6_closeout_v0_1.md`。

`final-01`/`final-02`/`final-03` 永久保持 frozen incomplete，不 retry、不 resume、不拼接、不升级；不得重跑 Gate 6 GPU collection / synthetic / gate aggregation。

### Gate 6 历史编号索引（试错过程的压缩记录，仅用于追溯）

Gate 6 的工程试错已收敛为 `docs/v1_4_1/gate6_closeout_v0_1.md` 中的四类根因；下表只保留编号、结果与去向，不重述过程。

| 编号 | 结果摘要 | 证据／去向 |
|---|---|---|
| `EP-G6-01` | 受控 CUDA Q0 微程序 + 机器可读 manifest：23 oracle case 严格映射，21 native seed + 2 纯合成；`--list-cases` 21/21 | `q0/cuda/exposedpath_q0.cu`、`q0/execution_manifest_v0_2.json` |
| `EP-G6-02` | GPU 前执行准备：结构化 `nsys` argv、每 case source manifest、输入哈希、不可覆盖输出与 dry-run；23 个合成 profile 经正式 S/A/B 与独立 evaluator 对照 | `exposedpath_v141/q0_execution.py`、`q0_synthetic.py`、`q0_evaluator.py` |
| `EP-G6-02A` | GPU 前集成验收（编译/list、Windows dry-run、23/23 合成对照、静态边界与全仓回归） | `engineering_evidence/q0_pre_gpu_v0_2/readiness_report.json` |
| `EP-G6-02B` | 真实 Q0 执行适配：Profiler API 控制 capture、显式 GPU 身份、单 case executor/receipt、三种受控 fault、真实 observed/evaluator、23-case 聚合、CLI 与 Windows runbook | `q0_collection.py`、`q0_faults.py`、`q0_real.py`、`q0_gate.py`、`docs/v1_4_1/gate6_windows_server_runbook.md` |
| `EP-G6-02C` | 首次 Windows 实跑修复：GPU UUID 比较、Nsight `2026.2.1/3.25.0`、同步映射诊断、MSVC 14.39、受控设备工作显式排空 | 失败现场 r2 保持不可变 |
| `EP-G6-02D` | r3：Q0 observation scope 与下游合同错位修复（request 外同步 → harness warning；单阶段两窗口） | `EP-ISSUE-08`、`EP-ISSUE-09` |
| `EP-G6-02E` | r4：lazy-export 零行 KERNEL 表规范化与真实 `VALID_EMPTY` evaluator | `EP-ISSUE-10` |
| `EP-G6-02F` | r5：三个同源多线程 seed 的重复 target request 修复（coordinator 唯一持有 request/decode） | `EP-ISSUE-11` |
| `EP-G6-02G` | r6：删除 PTDS `cudaStreamQuery` 轮询，改一次 stream-ordered host callback | `EP-ISSUE-12` |
| `EP-G6-02H` | r7：target identity 唯一性过滤（非目标 request 可共存，零/重复目标仍 fail closed） | `EP-ISSUE-13` |
| `EP-G6-02I` | r8：仅 Graph case 增加一次 `--cuda-graph-trace=node` | `EP-ISSUE-14` |
| `EP-G6-02J` | r9：`wait_set_activity_labels` 改用无序、无重复的精确成员比较 | `EP-ISSUE-15` |
| `EP-G6-02K` | r10：仅 KERNEL-MEMOP case 预分配 512 MiB buffer，改用 10 ms kernel | `EP-ISSUE-16` |
| `EP-G6-02L` | memcpy-first 提交顺序（让 DMA 先进入执行） | `EP-ISSUE-16` |
| `EP-G6-02M` | coordinator/worker 双 Host 路径并发提交，消除同线程序列化 | `EP-ISSUE-16` |
| `EP-G6-02N` | worker launch 前增加立即结束的 `WORKER_KERNEL_MEMOP` marker | `EP-ISSUE-16` |
| `EP-G6-02O` | activity-specific marker ownership：只接受同线程、完整覆盖 enqueue API、text/cache 完整一致的 marker | `docs/superpowers/specs/2026-09-17-s-activity-marker-ownership-design.md`、`EP-ISSUE-17` |
| `EP-G6-02P` | 与正常 executor 隔离的 WDDM Engineering diagnostic（禁止 CUDA↔packet 一一对应或根因结论） | `exposedpath_v141/q0_wddm_diagnostic.py`、runbook §2.13 |
| `EP-G6-02Q` | 64 MiB H2D/10 ms 参数 diagnostic（独立 CLI 与 identity；正常 Q0 仍为 512 MiB/10 ms） | `exposedpath_v141/q0_kernel_memop_diagnostic.py` |
| `EP-G6-02R` | 环境快照增加 `async_engine_count`/`device_overlap`/`concurrent_kernels`，缺失即 fail closed | `--environment-json` |
| `EP-G6-02S` | 64 MiB D2H/10 ms 参数 diagnostic（唯一实验变量为 copy direction） | `exposedpath_v141/q0_kernel_memop_d2h_diagnostic.py`、`EP-G6-04B` |
| `EP-G6-03` | r1～r10 与失败 diagnostic 一律 fail-fast 停止并保留现场，不覆盖、不升级资格 | 各 `rN` 证据目录 |
| `EP-G6-04` | 64 MiB/10 ms 单例：overlap=`0`（间隔 `629183 ns`）→ 按预定规则停止，不进入 64 MiB/1 ms | 历史 diagnostic 证据 |
| `EP-G6-04A` | GPU3 RTX 4090 能力探针：`async_engine_count=5`、`device_overlap=1`、`concurrent_kernels=1`（只证明设备声明能力） | 服务器 capability/receipt/ZIP SHA256 |
| `EP-G6-04B` | 64 MiB D2H/10 ms 单例：真实 overlap=`0`、terminal=`KERNEL_A` → STOP（不进入 D2D、不调参、不建 r11） | `server_evidence_inbox/` |
| `EP-G6-05` | 输出唯一 Q0 gate report（final-04） | `gate/q0_gate_report.json`，SHA256 `3A94F8B9…` |
| `EP-G6-06` | 策略审查：synthetic 边界、候选平台 admission 设计批准（仅设计）、scope limitation 不批准 | `docs/v1_4_1/gate6_strategy_review_v0_1.md` |
| `EP-G6-07` | 候选平台 + construction admission：设计与判据已冻结；**非 Gate 6 阻塞项**，仅在需要第二平台（含 Linux Formal 平台）时按 Gate 9 重启 | `docs/v1_4_1/candidate_platform_admission_checklist_v0_1.md`、`candidate_platform_inventory_v0_1.md` |
| `EP-G6-08` | 固化 `KERNEL_MEMOP_MIXED` 的 synthetic coverage 与 synthetic↔real 边界（纯文档） | `gate6_strategy_review_v0_1.md` §4/§4.1 |
| `EP-G6-09` | construction amendment 收口：formal-shape 配对诊断 + amendment 冻结 + preflight + implementation（execution schema `0.2.1`、`measurement_initialization` policy） | `gate6_construction_amendment_v0_1.md`、runbook §3 |
| `EP-G6-10` | `final-01` 收口与 4 例 semantic FAIL 的 root triage（Phase-Spill / Missing-Corr / External / Multithread-Ordered / Overlapping-Host-Sync） | 见 `gate6_closeout_v0_1.md` §3 |
| `EP-G6-11` | Gate 6 closeout 与 final-04 落账（只读独立复核，未重跑任何采集） | `docs/v1_4_1/gate6_closeout_v0_1.md` |

## 4. Gate 6 根因、amendment 与实现去向（一句话版）

Gate 6 的失败簇收敛为四类工程／科学问题，逐类的完整映射见 `docs/v1_4_1/gate6_closeout_v0_1.md` §3：

1. **观测/采集适配**（r2～r8：Nsight 版本与可选表、lazy-export 零行表、request scope、target identity、graph node tracing）→ adapter 条件化 + fail closed，最终在 final-04 真实数据上通过。
2. **测量构造 / warm-up**（`Q0-KERNEL-MEMOP-001` 的 device overlap 恢复）→ `gate6_construction_amendment_v0_1.md`：仅该 case 使用 `PRE_CAPTURE_SAME_KERNEL_WARMUP`；底层机制仍不归因。
3. **ownership / phase / sync 语义投影**（External、Multithread-Ordered、Overlapping-Host-Sync、Query、Sync-D2H）→ `gate6_marker_ownership_amendment_v0_1.md` 与 `gate6_sync_projection_amendment_v0_1.md`：trusted marker authority、跨线程 worker ownership、registry-role-preserving projection（共享 helper）。
4. **oracle / evaluator 与证据聚合**（Phase-Spill 窗口规则、Missing-Corr secondary、wait-set 成员顺序、gate 唯一性）→ `gate6_phase_spill_amendment_v0_1.md`、`gate6_missing_corr_amendment_v0_2.md`、`gate6_q0_build_contract_amendment_v0_1.md`。

## 5. Gate 7～14 计划

### Gate 7：Runner 与执行链对齐

**Gate verdict：`NOT_RUN`。** `EP-G7-08`、`EP-G7-09` 已完成，但 Gate 7 只有在 `EP-G7-11` 的全部 acceptance 判据满足后才形成 verdict。当前事实：Token-ready completion 与 G1/N1 身份已对齐；Pass0/Pass1 parity identity 与 attempt/exclusion/retry provenance 已冻结并机器可校验；launcher 仍只有 PowerShell（`scripts/*.ps1`），无等价平台入口；`tests/test_server_smoke_script.py::test_dry_run`、`::test_spaces` 两项既有失败未处置。

**重审计结论（2026-09-20）：** 原 `EP-G7-01`～`EP-G7-07` 的 7 个行政步骤压缩为 4 个可执行步骤（`EP-G7-08`～`EP-G7-11`）。合并的是**同一工程单元**（runner 语义/身份、identity/parity/schema、平台适配、验证与验收），没有合并彼此独立的科学 acceptance 判据：每一步内部仍逐条保留各自的 PASS/STOP 条件。执行计划：`docs/superpowers/plans/2026-09-20-gate7-execution-plan.md`；旧计划 `docs/superpowers/plans/2026-09-17-gate7-isolated-plan.md` 仅作历史记录。

**平台范围决定（2026-09-20，显式 scope 决定，不是静默弱化）：** 项目当前只声明**一个**目标 observation stack（Windows + RTX 4090 + CUDA 12.4.131 + Nsight 2026.2.1），Q0 资格也仅在该栈取得。因此 Gate 7 的“合同等价”**只在当前声明的目标平台上要求真实 GPU smoke 证据**。runner/launcher 仍必须完成平台适配隔离（核心不得硬编码 Windows 路径/命令/shell）；“声称支持第二平台（含 Linux）”所需的 Linux launcher、smoke、平台资格检查与 Linux Q0 归入 Gate 9。**任一平台在通过该平台的真实 smoke 前不得声称受支持。**

- [x] `EP-G7-08`（2026-09-21 完成，合并旧 `EP-G7-01`+`EP-G7-02`）
  - **Objective**：首 Token 与后续 Token 使用同一个可观察 completion 语义；G1 自然逐 Token 同步与 N1 人为干预以互斥、机器可读的模式身份表达。
  - **Why**：`EP-ISSUE-01` 使两类 Token 的完成边界不同，而这个差别会直接进入 A 窗口与 phase 定义；模式不分离则 N1 的人为同步会被误读为 G1 的自然行为。
  - **Implementation**：更新 `exposedpath/runner.py` 的 Token 边界取值与 `docs/pilot_runner_contract.md`；引入模式身份字段并实现非法组合 fail closed。测试先行。
  - **Evidence**：新增 `tests/test_runner_token_ready.py`，覆盖首/后续统一 Host-readable helper、首 Token/后续 Token EOS 均复用 Host 值、边界完整性/单调性、时间倒序与缺失边界 fail closed、机器可读边界记录、phase range 在校验/cleanup 前关闭、G1/N1 身份互斥、非法模式、双侧缺失 mode identity fail closed、N1 执行禁止及 Pass0/Pass1 Token-ready 行为一致；定向回归 `155 passed`，完整 CPU suite `845 passed, 3 failed, 4 errors`（均为既有 server smoke 与本机 CUDA 13/CP936 Q0 fixture 编译问题），合同 `37/37 PASS`，Canonical Raw 边界 `PASS`。
  - **PASS**：首/后续 Token 均通过同一 `device_to_host_token_ids` completion helper；runner 的 `inference_end_ns` 对应最后一个 Token-ready 完成点，legacy phase ranges 在随后校验/cleanup 前关闭；G1 使用 `natural_token_ready`，N1 仅建立 `n1_intervention` 身份且执行 fail closed；未修改 Measurement Contract 或 `exposedpath_v141`。严格 Pass0/Pass1 phase-boundary parity 仍属于 `EP-G7-09`，本步不提前宣称。
  - **STOP**：若修正边界需要改动 Measurement Contract 语义或 `exposedpath_v141` 语义 → 停止并单独提出。
  - **Dependency**：无（Gate 7 第一个可执行步骤；只依赖已冻结的 Gate 1 合同）。
  - **Unlock**：逐 Token 边界可比较，N1/G1 不会被静默混用。
- [x] `EP-G7-09`（2026-09-21 完成，合并旧 `EP-G7-03`+`EP-G7-04`）
  - **Objective**：冻结并证明 Pass0/Pass1 的输入、身份、phase boundary 与执行策略等价；补齐环境快照、early EOS、OOM、exclusion、retry、attempt 与 data role 字段。
  - **Why**：Pass0/Pass1 若不等价，profiler overhead 与执行差异会被混同为模型行为；缺失的 exclusion/retry/attempt 字段会让“计划 repeat 数”与“有效样本数”不可区分。
  - **Implementation**：复用既有 `wmpc_manifest.json`／`inference_results.jsonl`／`exclusion_log.jsonl` 结构补齐字段并加入机器可读 parity 检查；不新建平行 manifest 体系。
  - **Evidence**：`exposedpath/results.py` 为每条 attempt 写入 `repeat_index`/`retry_index`/`is_retry`/`attempt_uid`/`retry_of_attempt_uid`/`attempt_plan_version` 与 `data_role`/`run_role`/`study_mode`/`phase_boundary_policy_version`；exclusion 写入冻结 `exclusion_reason` 码与 `early_eos`/`oom`/`output_len_*` 证据；`exposedpath/runner.py` 写出 `cross_pass_parity.json`（schema `exposedpath-v3-cross-pass-2`）六组冻结身份并在 pass 结束前校验 planned repeat index 恰好记账一次（否则 `sys.exit(1)`）；`exposedpath/cross_pass_validator.py` 增加 `PARITY_*_FIELDS`／`PASS_PARITY_IDENTITY_MISSING`／`PASS_ATTEMPT_ACCOUNTING_MISMATCH` 与 `summarize_attempt_records`／`load_attempt_accounting`／`validate_attempt_accounting`；新增 `tests/test_runner_pass_parity.py`（真实 parity writer + JSONL 账目；等价通过、缺失/重复/有意差异 fail closed），并更新 `tests/test_small_pilot.py`、`tests/test_exposedpath_v3.py`、`tests/test_runner_token_ready.py` 的受影响夹具。
  - **PASS**：等价输入 `validate_pair` = `[PASS_PARITY_OK]`、`validate_attempt_accounting` = `[PASS_PARITY_OK]`；任一必需字段缺失 → `PASS_PARITY_IDENTITY_MISSING`；token-ready/环境/attempt-plan 的有意差异 → `PASS_EXECUTION_PARITY_MISMATCH`；exclusion 原因、retry、缺失/重复 repeat index 的差异 → `PASS_ATTEMPT_ACCOUNTING_MISMATCH`；缺失 role、未知 exclusion 码、无父 attempt 的 retry 直接抛错而非写 null/0。定向 `158 passed`，完整 CPU suite `874 passed, 3 failed, 4 errors`（失败/错误集合与既有基线相同），合同 `37/37 PASS`，Canonical Raw 边界 `PASS`，`compileall` 与 `git diff --check` PASS。
  - **STOP**：若要求把缺字段降级为零值/默认值来让检查通过 → 停止。
  - **Dependency**：与 `EP-G7-08` 无相互依赖，可并行；两者都必须先于 `EP-G7-11` 完成。
  - **Unlock**：Pass0/Pass1 可配对比较，exclusion/retry 规则有机器可读依据。
- [ ] `EP-G7-10`（未开始，合并旧 `EP-G7-05`＋旧 `EP-G7-06` 的基线失败部分）
  - **Objective**：把 Windows PowerShell、平台探测、Nsight 调用收敛到 adapter/launcher；处置两项既有 smoke 失败。
  - **Why**：平台差异目前散落在脚本中，任何第二平台（Gate 9）都会重新暴露同类问题；未解释的基线失败会让后续回归无法区分“新缺陷”与“旧噪声”。
  - **Implementation**：runner 核心改用 `pathlib` 与结构化子进程参数；平台特定逻辑下沉到 adapter/launcher；修复或按平台范围决定明确重界定 `tests/test_server_smoke_script.py::test_dry_run` 与 `::test_spaces`。
  - **Evidence**：Windows/Linux 命令构造与参数单测（不需要 GPU）；两项基线失败的最终处置结论。
  - **PASS**：定向单测全绿；两项基线失败被修复或经明确重界定后不再计为未知失败。
  - **STOP**：若某项必须先有真实 GPU 才能判定 → 移交 `EP-G7-11`，不得用 mock 结论代替。
  - **Dependency**：独立于 `EP-G7-08`/`EP-G7-09`，可并行；其结论不依赖 GPU。
  - **Unlock**：平台可移植性被结构性保护，测试基线不再含未解释失败。
- [ ] `EP-G7-11`（未开始，合并旧 `EP-G7-06` 的全量验证＋旧 `EP-G7-07`，按平台范围决定重写）
  - **Objective**：在 Windows/RTX 4090 上执行 runner 端到端 smoke（Pass0/Pass1、identity/phase boundary、exclusion/retry 记录），证明产出可被机器读取且与 Gate 7 合同一致，并完成 Gate 7 验收决定。
  - **Why**：只有真实 GPU smoke 能证明该执行链在真实执行栈上成立；Gate 8 必须以这份证据为入口。
  - **Implementation**：不改语义；只执行既有 runner 链路并收集 manifest/receipt 证据。真实 GPU 执行须在用户批准的窗口内进行。
  - **Evidence**：全量 `python -m pytest -q -p no:cacheprovider`、`python -m compileall exposedpath analysis exposedpath_v141`、合同/边界检查，以及目标平台 smoke 的 manifest/receipt 证据。
  - **PASS**：非 GPU 判据与目标平台真实 smoke 判据同时成立，且未修改 Measurement Contract 或 `exposedpath_v141` 计算语义。
  - **STOP**：任何真实 smoke 失败都保留现场并停止，不得用 mock 或局部测试替代；需要第二平台等价性时转 Gate 9。
  - **Dependency**：消费 `EP-G7-08`～`EP-G7-10` 的产物；是 Gate 7 verdict 的必要条件，必须最后执行。
  - **Unlock**：Gate 8 Engineering Pilot 获得唯一入口。

原编号处置（不得复用旧编号）：`EP-G7-01`→`EP-G7-08`；`EP-G7-02`→`EP-G7-08`；`EP-G7-03`→`EP-G7-09`；`EP-G7-04`→`EP-G7-09`；`EP-G7-05`→`EP-G7-10`；`EP-G7-06`→`EP-G7-10`（基线失败部分）＋`EP-G7-11`（全量验证部分）；`EP-G7-07`→`EP-G7-11`（其跨平台部分转入 Gate 9）。

### Gate 8：Engineering Pilot

**Gate verdict：`NOT_RUN`（未启动）。** 唯一前序依赖是 Gate 7 的 acceptance（`EP-G7-11`）；在 Gate 7 满足完成判据前不得启动，也不得把 Gate 6 PASS 当作 Gate 8 的通行证。

- [ ] `EP-G8-01`（未开始，依赖 `EP-G7-11`）运行最小端到端开发 workload。
- [ ] `EP-G8-02`（未开始，依赖 `EP-G7-11`）验证 benchmark → runner → Nsight → Canonical Raw → S → A/B → D/Signature 全链路。
- [ ] `EP-G8-03`（未开始，依赖 `EP-G7-11`）记录 trace coverage、存储规模、profiler overhead、运行可靠性和失败模式。
- [ ] `EP-G8-04`（未开始，依赖 `EP-G7-11`）形成 Engineering Pilot 报告；不得将结果用作正式科学结论。

### Gate 9：Formal 平台资格检查

**Gate verdict：`BLOCKED`。** 正式 GPU 平台尚未确定或接入（与 Gate 6 无关：Gate 6 只在其声明的 Windows/RTX 4090 目标栈上取得 Q0 资格）。若正式平台选为 Linux 或第二平台，则该平台的 launcher、smoke 与平台资格检查在此处执行。

- [ ] `EP-G9-01`（受阻）记录候选平台的 GPU、driver、CUDA、framework、Nsight、OS 和 launcher 身份。
- [ ] `EP-G9-02`（受阻）验证该平台满足冻结 observation contract 和 Q0 可观测性。
- [ ] `EP-G9-03`（受阻）检查 eager 行为及 G2 所需 compile/graph 可行性。
- [ ] `EP-G9-04`（受阻）给出平台 `PASS/FAIL/BLOCKED` 资格结论。

### Gate 10：可行域与 OOM 边界

**Gate verdict：`BLOCKED`。** 等待合格正式平台。

- [ ] `EP-G10-01`（受阻）预定义候选 input/output/batch 探测范围和停止规则。
- [ ] `EP-G10-02`（受阻）记录 OOM、early EOS、不稳定和 retry，不把 OOM 当科学重要性指标。
- [ ] `EP-G10-03`（受阻）确定跨配置比较所需的共同稳定范围和平台特定排除项。

### Gate 11：Pilot

**Gate verdict：`BLOCKED`。** 依赖合格平台和共同可行域。

- [ ] `EP-G11-01`（受阻）冻结前选择代表 workload 点。
- [ ] `EP-G11-02`（受阻）确定 repeat 数、profiler overhead 政策、质量阈值和运行规则。
- [ ] `EP-G11-03`（受阻）记录 Pilot 依据并保持其非 Formal 数据角色。
- [ ] `EP-G11-04`（受阻）形成 Protocol Freeze 所需输入清单。

### Gate 12：Protocol Freeze

**Gate verdict：`NOT_RUN`。** 只有前置 Gate 完成后才允许冻结。

- [ ] `EP-G12-01`～`EP-G12-04`（未开始）冻结代码提交、analyzer/schema、平台栈、协议版本、workload matrix、seed/input digest、repeat、Pass0/Pass1 配对、排除规则、质量 gate、统计方法、绘图方案与 N1/G1/G2 claim 评估规则。
- [ ] `EP-G12-05`（未开始）建立冻结后实质变更的新版协议及 Formal 数据失效规则。

### Gate 13：N1 与 G1

**Gate verdict：`NOT_RUN`。** 尚未进入 Formal 实验。

- [ ] `EP-G13-01`～`EP-G13-04`（未开始）按冻结协议执行 N1 受控同步干预与 G1 自然 workload sweep，验证 Information Gain（如实报告 null、按比例和依赖 regime 的结果），并审查 claim 是否仍保持单 GPU、请求内部 Host-device exposure 边界。

### Gate 14：G2

**Gate verdict：`NOT_RUN`。** 必须在 Correctness 和 Information Gain 证据成立后执行。

- [ ] `EP-G14-01`～`EP-G14-03`（未开始）按预定义规则选择真实优化 intervention 与 held-out 场景，执行 decision-gain 评估；若无额外决策价值，则删除预测/决策优越性 claim。

## 6. 已知问题与风险

**未关闭／长期有效：**

- `EP-ISSUE-02`：三份历史 trace 缺少 source manifest。影响：validity 必须保持 `ambiguous`，不能升级数据资格。**永久限制**。
- `EP-ISSUE-03`（已指派，未关闭）：仓库全量测试长期保留两项既有本地 PowerShell smoke 失败 `tests/test_server_smoke_script.py::test_dry_run` 与 `::test_spaces`，与工作前基线相同，不属于任何 Gate 新增失败，也不影响 Gate 6 PASS（Gate 6 的判据是唯一 gate report，不依赖该 smoke 脚本）。**处置**：Gate 7 `EP-G7-10` 必须在 `EP-G7-11` 前给出修复或明确重界定结论；在此之前它仍是未解释的基线失败，不得当作“已解决”。
- `EP-ISSUE-04`：本机（Lenovo 82L5，Windows build 26200）存在 GTX 1650（4 GiB，driver package `581.57`，Toolkit/nvcc `V13.0.88`，Nsight 2026.1.1 系列），但**尚未完成 Candidate qualification**（driver API 与 runtime 版本未知、schema 未审查、独占性未确认、A7 未闭合），因此当前不得作为真实 Q0/workload 平台；仅允许离线工作与已批准的非 case qualification。静态盘点见 `docs/v1_4_1/candidate_platform_inventory_v0_1.md`。
- `EP-ISSUE-06`：S 层已建立 event/wait 查找索引并缓存重复 scope 建图；event/default-stream 密集型大 trace 的规模性能尚未在真实 Engineering 数据上验收。影响：需在 Engineering Pilot 记录耗时与峰值内存；不改变 S 语义正确性或数据资格。
- `EP-ISSUE-07`：本机环境变量 `CL` 被配置为 MSVC 目录，但该名称会被 `cl.exe`/`nvcc` 解释为隐式编译参数。Q0 编译入口只在子进程环境中移除 `CL/_CL_`，不修改用户系统环境；GPU 平台资格检查仍需记录并复核实际编译环境。
- `EP-ISSUE-16`（遗留未归因，**不再阻塞**）：512 MiB H2D、64 MiB H2D 与 64 MiB D2H 在 RTX 4090 上均未与 10 ms kernel 重叠；真实 trace 已排除相同/default stream、event wait、数据依赖和过早同步；GPU capability 为 `async_engine_count=5/device_overlap=1/concurrent_kernels=1`，只说明硬件声明支持相关能力。formal-shape 配对 diagnostic 证明 pre-capture same-kernel warm-up 可恢复该构造的 device overlap，因此“平台 incapable”解释不再成立；该 construction 已作为 manifest policy 在 final-04 验证为 `REAL_CASE_PASS`。**现有证据不能区分 WDDM／driver／Runtime／调度层，禁止根因归因，禁止在该平台重启参数搜索或诊断。**异平台 admission（`EP-G6-07`）只在需要第二平台时按 Gate 9 重启。

**已解决（保留历史，不再需要为正常前进执行而复查）：**

| 编号 | 结论 |
|---|---|
| `EP-ISSUE-01` | `EP-G7-08` 已统一首/后续 Token 的 Host-readable completion boundary；EOS 使用已读取 Host 值，`inference_end_ns` 截止于最后一个 Token-ready 完成点，phase ranges 在校验/cleanup 前关闭；严格跨 pass phase parity 留给 `EP-G7-09` |
| `EP-ISSUE-05` | 本地全页渲染与研究主体/协议文档 QA 已完成（渲染器只用于文档 QA，不改变研究 Gate） |
| `EP-ISSUE-08` | r2 捕获结束同步未映射；r3 证明新增显式排空具有唯一 runtime 映射 |
| `EP-ISSUE-09` | r3 request 后尾部同步无 runtime 候选；以唯一 full_request identity 限定 observation scope，标为 `HARNESS_OUTSIDE_REQUEST` warning |
| `EP-ISSUE-10` | Nsight `lazy=true` 零 kernel case 缺 KERNEL 表被误判缺表；已用条件化 adapter 与真实区间 oracle 修复 |
| `EP-ISSUE-11` | r5 PTDS worker 创建同 identity `full_request`；coordinator 唯一 request/decode 已生效 |
| `EP-ISSUE-12` | r6 `cudaStreamQuery` 轮询产生 31 条无 Runtime 映射同步；改用一次 stream-ordered host callback |
| `EP-ISSUE-13` | r7 resolver 误用全 trace request 总数作为唯一性条件；已改为只对完整 target identity 计数 |
| `EP-ISSUE-14` | r8 默认 graph-level tracing 无 node activity；仅 Graph case 增加 `--cuda-graph-trace=node` |
| `EP-ISSUE-15` | r9 evaluator 以通用 list equality 比较 wait-set；该字段改为唯一字符串集合比较 |
| `EP-ISSUE-17` | activity-specific marker ownership 已在真实单例上验证；`INVOCATION_BOUNDARY_INVALID` 不再出现 |

## 7. 固定执行顺序与最近任务

当前顺序：`Gate 1 合同 → Gate 2 oracle → Gate 3 Canonical Raw → Gate 4 S → Gate 5 A/B/D/Signature → Gate 6 Q0 → Gate 7 runner/执行链对齐 → Gate 8 Engineering Pilot → Gate 9～12 正式实验准备 → Gate 13 N1/G1 → Gate 14 G2`。Gate 0 已完成封存。

**最近应执行的任务（按顺序）：**

1. `EP-G7-10`（当前最高优先级）：平台适配隔离（runner 核心改用 `pathlib` 与结构化子进程参数，平台特定逻辑下沉 adapter/launcher）与两项既有 PowerShell smoke 失败的最终处置。
2. `EP-G7-11`：非 GPU 全量验证＋当前声明目标平台（Windows/RTX 4090）真实 GPU smoke，形成 Gate 7 acceptance 决定。
3. 已完成的 `EP-G7-08`（Token-ready 与 G1/N1 身份）与 `EP-G7-09`（Pass0/Pass1 parity 与机器可读 provenance）不再产生新任务；如后续发现需要放宽其 fail-closed 判据，属于新计划项，不得直接修改。

（历史顺序，保留不删：`EP-G7-09` → `EP-G7-10` → `EP-G7-11`；`EP-G7-09` 已于 2026-09-21 完成。）

**Gate 7 验收前置：** Gate 7 只在 `EP-G7-11` 判据同时成立时改判 `PASS`；此前 Gate 8 不得启动。

**Gate 6 冻结边界（不再产生新任务）：** `final-01`/`final-02`/`final-03` 永久 frozen incomplete，`final-04` 为唯一有效 PASS 证据；不得重跑 Gate 6 GPU collection、synthetic 或 gate aggregation，不回填缺失的 prepare-time sidecar，不对 WDDM/driver/Runtime 作根因归因；`EP-G6-07` 只在需要第二平台时按 Gate 9 重启。Gate 6 清理与诊断周期已关闭。

## 8. 计划调整记录

（按时间顺序。行内出现的 `Gate 6 = FAIL`、`Q0 = NOT_RUN`、`Gate 7 = BLOCKED` 等字样均为该行日期当时的状态，已由 7.0 行改判；各行只保留结论摘要，详细过程见对应 amendment、runbook 与 `docs/v1_4_1/gate6_closeout_v0_1.md`。）

| 清单版本 | 日期 | 调整摘要 | 影响编号 | 冻结协议／Formal 数据影响 |
|---|---|---|---|---|
| 0.1 | 2026-09-10 | 首次建立完整清单；纳入无 GPU 离线路线、自然逐 Token 同步边界与现有 observation 基础 | 全部 | 无 Formal 数据，不产生失效 |
| 0.2 | 2026-09-10 | 权威关系审计：协议修订底稿由 WMPC v1.5 更正为实验协议 v2.0；新增两份 Pre-Pilot 整合候选版 | EP-FND-06～10 | 未改变冻结协议 |
| 0.3 | 2026-09-10 | 基于两份 Word 母版吸收 v1.4.1，完成 40/27 页视觉验收；完整 v7.0/v2.1 成为当前入口 | EP-FND-07～11、EP-ISSUE-05 | 未通过 Gate 1 或 Protocol Freeze |
| 0.4 | 2026-09-10 | 复核发现 v7.0 第一章背景论证不完整，启动 v7.1 修订并简化交付文件名 | EP-FND-09、EP-FND-11、EP-FND-12 | 不改变合同或资格 |
| 0.5 | 2026-09-11 | 完成 v7.1 背景与研究立意补齐、结构/语义校验与全页视觉验收 | EP-FND-12、EP-ISSUE-05 | 不改变合同或资格 |
| 0.6 | 2026-09-11 | 完成 Measurement Contract v0.2，建立 37 条规则到 25 个验证案例的机器映射 | EP-G1-02～09 | Gate 1 内部合同审查 PASS |
| 0.7 | 2026-09-11 | 完成 Q0 独立标准答案设计（23 case、25 特性、`DESIGN_ONLY_PASS`） | EP-G2-01～05、EP-G3-05 | Gate 2 设计审查 PASS |
| 0.8 | 2026-09-11 | 完成 Canonical Raw v0.2 与三份历史 trace 的 Engineering 回归 | EP-G3-05～08、EP-G4-01～05 | Gate 3 PASS |
| 0.9 | 2026-09-11 | 完成 S v0.2：ownership、submission、completion graph、`W(s)`、terminal、validity 与版本化输出 | EP-G4-01～05、EP-G5-01 | 无 |
| 1.0 | 2026-09-11 | Gate 4 复审修正三项语义缺陷：missing correlation 降级、wait-event 漏 producer、外部 invocation 静默删除 | EP-G4-01～05 | 无 |
| 1.1 | 2026-09-11 | Gate 4 二轮复审：`eventSyncId` 唯一映射与 event/context/device 校验、invalid 传播、default-stream 污染；补 9 回归 | EP-G4-01～05、EP-ISSUE-03、EP-ISSUE-06 | 无 |
| 1.2 | 2026-09-11 | Gate 4 三轮复审：统一缺失 correlation 的 fail-closed 传播路径；补 3 回归 | EP-G4-02、EP-G4-05 | 无 |
| 1.3 | 2026-09-12 | 冻结 Gate 5 设计（A/B 双输入联结、窗口发现、B 投影、D/Signature 纯派生） | EP-G5-01～06 | 无 |
| 1.4 | 2026-09-12 | 冻结 A/B 与派生层 v0.2 JSON Schema（守恒字段、null-only、lineage） | EP-G5-01～06 | 无 |
| 1.5 | 2026-09-12 | Gate 5 schema 一审修复：terminal kind/status 的 identity、clock 与 timing nullability，count 收紧 | EP-G5-01、EP-G5-03、EP-G5-05、EP-G5-06 | 无 |
| 1.6 | 2026-09-12 | Gate 5 schema 二审修复：`B_VALID>0` 时 terminal count 与统计分布必须非空 | EP-G5-01、EP-G5-03、EP-G5-05、EP-G5-06 | 无 |
| 1.7 | 2026-09-12 | 完成整数半开区间原语（交、裁剪、相邻/重叠 union、union 长度、原子切分） | EP-G5-02 | 无 |
| 1.8 | 2026-09-12 | 完成 A 墙钟记账：按窗口/API/sync/`W(s)` 原子切分，固定优先级互斥分配，fail-closed 到 unattributed | EP-G5-01、EP-G5-02 | 无 |
| 1.9 | 2026-09-12 | Gate 5 Task 4 一审引入结构化 NVTX API ownership gate（过严规则已在 2.0 修正） | EP-G5-01、EP-G5-02 | 无 |
| 2.0 | 2026-09-12 | 二审澄清 API ownership 与 phase clipping：ownership 只证明同一 invocation，不定义 A 窗口 | EP-G5-01、EP-G5-02 | 无 |
| 2.1 | 2026-09-12 | 集成复审修正窗口发现：非窗口 marker 不创建也不否定 A 三窗口 | EP-G5-01、EP-G5-02 | 无 |
| 2.2 | 2026-09-12 | 收紧 worker API ownership：采用前重解析 NVTX text 并要求与缓存 identity 完整一致 | EP-G5-01、EP-G5-02 | 无 |
| 2.3 | 2026-09-13 | 完成 B 单同步 provenance：仅 `B_VALID` 按区间 union 计算，其他状态 null-only，不提供跨同步 total | EP-G5-03 | 无 |
| 2.4 | 2026-09-13 | 补两条 B 回归：重叠活动按 union、`COMPLETION_BOUNDARY` terminal timing 为 null | EP-G5-03 | 无 |
| 2.5 | 2026-09-13 | 完成 A/B bundle 与 `analyze-ab` CLI：严格联结、逐条 schema 校验、确定性 gzip、拒绝覆盖、边界审计 | EP-G5-06、EP-G3-08 | 无 |
| 2.6 | 2026-09-13 | A/B loader 在 schema 允许未来资格值时仍执行当前 Engineering 资格策略；外部 S lineage 核对 registry SHA | EP-G5-06、EP-G3-08 | 该策略不是对 Formal bundle 的永久否定 |
| 2.7 | 2026-09-13 | 完成 `derive-exposure`：D 与 Exposure Signature 纯派生，边界禁止回读 Canonical/S 或 Raw/S 时间字段 | EP-G5-04～06、EP-G3-08 | 无 |
| 2.8 | 2026-09-13 | Gate 5 Task 8 历史 trace 离线工程验证：S 446 invalid → B 446 `B_INVALID`，无合格 A 窗口 | EP-G5-06、EP-ISSUE-02、EP-ISSUE-03 | 历史数据仍为 ambiguous Engineering 证据 |
| 2.9 | 2026-09-14 | 分支复审最终修复：S/wait-set/frontier/terminal 一致性、跨 invocation 重叠 fail closed、Derived 精确符号白名单 | EP-G5-01、EP-G5-03、EP-G5-05、EP-G5-06、EP-G3-08 | 未产生 Formal 数据 |
| 3.0 | 2026-09-14 | 独立再复审通过（补 completion boundary 时钟域校验）；Gate 5 判为 `PASS`，优先级切换至 Gate 6 GPU 前工作 | EP-G5-03、EP-G5-06、EP-G6-01、EP-G6-02 | Gate 5 PASS |
| 3.1 | 2026-09-14 | 冻结 Gate 6 GPU 前实施计划：23 个 oracle case → native CUDA / seed+fault / 纯合成三类 | EP-G6-01、EP-G6-02 | Gate 6 仍 `BLOCKED` |
| 3.2 | 2026-09-14 | 完成 Q0 执行合同第一步：case 严格一一对应、稳定 label 不可改写、策略字段冲突 fail closed | EP-G6-01 | 无 |
| 3.3 | 2026-09-14 | 完成受控 Q0 CUDA 微程序（21 native seed、结构化 NVTX、可无 GPU 编译并核对 seed 集合） | EP-G6-01、EP-ISSUE-07 | 只证明可构建，不证明 GPU 行为 |
| 3.4 | 2026-09-14 | 完成 Windows/Linux 结构化 `nsys` argv dry-run、23 份 source manifest 与不可覆盖 run manifest | EP-G6-02 | 不产生 `.nsys-rep` |
| 3.5 | 2026-09-14 | 完成 23 案例合成 S/A/B + 独立 evaluator 对照；修正 graph mapping unsupported 时 S 保留未证明 wait-set 的缺口 | EP-G4-01～05、EP-G6-02 | 仅 `SYNTHETIC_ONLY` |
| 3.6 | 2026-09-14 | GPU 前集成验收：编译/list、Windows dry-run、合成对照、静态边界与全仓非 GPU 回归 | EP-G6-02A、EP-G6-03 | GPU 前 PASS ≠ Gate 6 PASS |
| 3.7 | 2026-09-14 | 真实执行复审新增 `EP-G6-02B`：改用 CUDA Profiler API 控制 capture 并冻结显式单 GPU 选择 | EP-G6-02B、EP-G6-03 | 修正“可直接真实采集”的过早推断 |
| 3.8 | 2026-09-14 | 完成单 case executor 与不可覆盖 receipt（工具/source manifest 哈希、环境身份、命令日志、Raw 哈希） | EP-G6-02B | 仅新增采集能力 |
| 3.9 | 2026-09-14 | 完成三种受控 Canonical 故障副本（移除唯一 activity correlation／dropped records／graph node mapping） | EP-G6-02B | Raw 与源 Canonical 保持不可变 |
| 4.0 | 2026-09-14 | 完成真实 observed/evaluator：标签联结 + 本次真实区间重算，缺区间/映射一律 fail closed | EP-G6-02B | 单 case 仅 `REAL_CASE_ONLY` |
| 4.1 | 2026-09-14 | 完成本地真实 Q0 执行缺口：唯一聚合器强制 21 real + 2 synthetic、单 run/单环境，补齐 CLI 与双平台手册 | EP-G6-02B、EP-G6-03～05 | 本地准备 ≠ 真实 Q0 |
| 4.2 | 2026-09-15 | 补充服务器部署与回传流程（Git bundle clone、独立 venv、先单例后批量、记录 commit/dirty state） | EP-G6-03 | 无 |
| 4.3 | 2026-09-15 | 基于 r2 修复 Windows 适配：Nsight `2026.2.1.210/3.25.0`、可选表规范化、有符号 trace-relative 时间、UUID、诊断输出 | EP-G3-09、EP-G6-02C、EP-ISSUE-08 | r2 不升级资格 |
| 4.4 | 2026-09-15 | 基于 r3 修正 observation scope 与下游空映射；r3 本地只读重放 `REAL_CASE_PASS` | EP-G3-10、EP-G6-02D、EP-ISSUE-09 | r3 不升级资格 |
| 4.5 | 2026-09-15 | 基于 r4 EMPTY 修正 lazy-export 零行 KERNEL 表与真实 `VALID_EMPTY` evaluator；导出统一 `--lazy=false` | EP-G6-02E、EP-ISSUE-10 | r4 不升级资格 |
| 4.6 | 2026-09-16 | 基于 r5 修复三个同源多线程 seed 的重复 target request（coordinator 唯一 request/decode） | EP-G6-02F、EP-ISSUE-11 | r5 不升级资格 |
| 4.7 | 2026-09-16 | r6 确认修复并发现 PTDS `cudaStreamQuery` 轮询产生 31 条未映射同步 → 改一次 stream-ordered host callback | EP-G6-02G、EP-ISSUE-12 | r6 不升级资格 |
| 4.8 | 2026-09-16 | r7 修正 resolver 的目标唯一性判定：只对完整 target identity 计数 | EP-G6-02H、EP-ISSUE-13 | r7 不升级资格 |
| 4.9 | 2026-09-16 | r8 为 Graph case 增加一次 `--cuda-graph-trace=node`，其余 native case 采集参数不变 | EP-G6-02I、EP-ISSUE-14 | r8 不升级资格 |
| 5.0 | 2026-09-16 | r9 evaluator 对 `wait_set_activity_labels` 改用无序、无重复精确成员比较 | EP-G6-02J、EP-ISSUE-15 | r9 不升级资格 |
| 5.1 | 2026-09-16 | r10 无 device overlap → 仅 KERNEL-MEMOP case 预分配 512 MiB 并把 kernel 改为 10 ms，新增单 case diagnostic gate | EP-G6-02K、EP-ISSUE-16 | r10 不升级资格 |
| 5.2 | 2026-09-16 | 512 MiB diagnostic 仍串行 → 改为 memcpy-first 提交顺序并以静态回归锁定 | EP-G6-02L、EP-ISSUE-16 | 同上 |
| 5.3 | 2026-09-16 | 证明同线程 `cudaLaunchKernel` 被长 H2D 阻塞 → 改为 coordinator/worker 双 Host 路径并发提交 | EP-G6-02M、EP-ISSUE-16 | 同上 |
| 5.4 | 2026-09-16 | concurrent-host diagnostic 缺 worker invocation marker → worker launch 前增加立即结束的 `WORKER_KERNEL_MEMOP` | EP-G6-02N、EP-ISSUE-16 | 同上 |
| 5.5 | 2026-09-17 | 证明仅延长 worker marker 无效 → 冻结 activity-specific marker ownership 修正规格，暂停 GPU 重跑 | EP-G6-02O、EP-ISSUE-17 | 未修改 S 语义 |
| 5.6 | 2026-09-17 | 按规格测试先行实现 activity-specific marker ownership；S 定向 `77 passed`，全仓 `661 passed, 2 failed` | EP-G6-02O、EP-ISSUE-17 | 真实 GPU 单例尚未复验 |
| 5.7 | 2026-09-17 | 真实 ownership 单例确认 S 修复成功但 device overlap 仍为 0 → 新增完全隔离的 WDDM Engineering diagnostic；全仓 `671 passed` | EP-G6-02P、EP-ISSUE-16 | 无 |
| 5.8 | 2026-09-17 | WDDM diag-02 采集成功但 HAGS 未确认、packet 无 correlationId → 新增 64 MiB H2D/10 ms diagnostic；全仓 `678 passed` | EP-G6-02Q、EP-ISSUE-16 | 仅 Engineering 假设检验能力 |
| 5.9 | 2026-09-17 | 64 MiB/10 ms 仍 overlap=0 → 按预定判据停止 1 ms 路线；新增 device capability 探针；全仓 `681 passed` | EP-G6-02R、EP-G6-04A、EP-ISSUE-16 | 无 |
| 6.0 | 2026-09-17 | 服务器 capability 复核：`async_engine_count=5`、`device_overlap=1`、`concurrent_kernels=1`（只证明设备声明能力） | EP-G6-04A、EP-ISSUE-16 | 不解释此前 overlap=0 |
| 6.1 | 2026-09-17 | 实现严格隔离的 64 MiB D2H/10 ms diagnostic（专用 flag + run identity 双条件） | EP-G6-02S、EP-G6-04B、EP-ISSUE-16 | 默认 Q0 路径不变 |
| 6.2 | 2026-09-17 | 收录 D2H 真实证据：仍 overlap=0，`Q0-KERNEL-MEMOP-001` 记为 platform construction blocked，按判据 STOP | EP-G6-04B、EP-G6-05、EP-G6-06、EP-ISSUE-16 | Gate 6 仍 `FAIL`、Q0 `NOT_RUN` |
| 6.3 | 2026-09-17 | 完成 `EP-G6-06` 策略审查：synthetic 仅作 regression strengthening、批准候选平台 admission 设计、冻结 admission checklist、scope limitation 不批准 | EP-G6-06～08 | 纯设计，未运行实验 |
| 6.4 | 2026-09-17 | 批准 Gate 7 非 GPU 项与 Gate 6 等待期并行（该前提已被 6.7/7.0 取代） | EP-G7-01～06 | Gate 7 保持 `BLOCKED` |
| 6.5 | 2026-09-17 | `EP-G6-07` 首轮候选平台盘点：主线切到 Candidate Platform qualification，CP-01 A3 修正，A7 保持 `UNKNOWN` | EP-G6-07、EP-ISSUE-04、EP-ISSUE-16 | Gate 7/8 暂停推进 |
| 6.6 | 2026-09-17 | CP-03 静态 qualification 收敛（A1、A3～A9 = `PASS`；A2 pending、A7 unknown；仍为 `NEEDS_INFORMATION`） | EP-G6-07 | 未运行任何 case/workload probe |
| 6.7 | 2026-09-18 | formal-shape 配对 diagnostic 证明 warm-up 可恢复 overlap → 建立 canonical baseline `codex/gate6-canonical-baseline` 与 construction amendment；`EP-G6-07` 暂停 | EP-G6-05、EP-G6-07、EP-G6-09、EP-ISSUE-16 | Gate 6 仍 `FAIL`、Q0 `NOT_RUN` |
| 6.8 | 2026-09-19 | construction amendment implementation：execution schema `0.2.1`、23/23 case 显式 `measurement_initialization`（1 warm-up + 22 `NONE`）；targeted `70 passed`、Q0 offline `199 passed` | EP-G6-05、EP-G6-07、EP-G6-09 | server validation `NOT_STARTED` |
| 6.9 | 2026-09-19 | `final-01` 收口与 4 例 semantic FAIL root triage（新增 `EP-G6-10`）：Phase-Spill / Missing-Corr / External / Multithread-Ordered / Overlapping-Host-Sync | EP-G6-05、EP-G6-07、EP-G6-09、EP-G6-10 | Gate 6 仍 `FAIL`、Q0 `NOT_RUN` |
| 7.0 | 2026-09-20 | **Gate 6/Q0 正式 PASS 并收口**（新增 `EP-G6-11` 与 `gate6_closeout_v0_1.md`）；Gate 7 压缩为 `EP-G7-08`～`EP-G7-11` 并作出平台范围显式决定；清理本地可重建垃圾 | EP-G6-05、EP-G6-11、EP-G7-08～11、EP-ISSUE-01、EP-ISSUE-03、EP-ISSUE-16 | Gate 6/Q0 改判 `PASS`（依据既有唯一 gate report，未新增采集）；Gate 7 由 `BLOCKED` 改为 `NOT_RUN` |
| 7.1 | 2026-09-20 | 最后一次收尾：本清单重构为“交接入口 + 当前快照 + Gate 摘要 + 压缩历史”；清除过时 live 状态文字；为旧 Gate 6/5 计划与规格加历史横幅；为 Gate 7 四步补 `Dependency`；补 Gate 6 论文级分类总结 | EP-G6-11、EP-G7-08～11、EP-ISSUE-03 | 不改变任何 Gate verdict、Measurement Contract、oracle、schema 或数据资格 |
| 7.2 | 2026-09-21 | 完成 `EP-G7-08`：统一首/后续 Token 的 Host-readable completion，首/后续 EOS 均复用 Host 值，结果时间截止于最后 Token-ready 且 phase ranges 在校验/cleanup 前关闭；加入 G1/N1 互斥机器身份、结构化 NVTX 与 fail-closed validation | EP-G7-08、EP-ISSUE-01 | Gate 7 保持 `NOT_RUN`；严格跨 pass phase parity 留给 `EP-G7-09`；不改变 Measurement Contract、`exposedpath_v141`、Gate 6 证据或数据资格 |
| 7.3 | 2026-09-21 | 完成 `EP-G7-09`：冻结 Pass0/Pass1 parity identity（workload／GPU／execution strategy／phase boundary／environment snapshot／attempt plan 六组）并把 `cross_pass_parity.json` 升为 `exposedpath-v3-cross-pass-2`；attempt/exclusion/retry/data-role 机器可读；缺失身份、缺失/重复 repeat index 与有意差异一律 fail closed | EP-G7-09、EP-G7-03、EP-G7-04 | Gate 7 保持 `NOT_RUN`；不改变 Measurement Contract、`exposedpath_v141`、Gate 6 证据、数据资格或 Gate 7 PASS 判据 |
