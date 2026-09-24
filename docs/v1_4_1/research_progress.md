# ExposedPath 科研进度清单

> 一句话状态：**Gate 0～7 = `PASS`；EP-G7-11已收口。唯一合格fresh 8d64f75完整证据经本地只读逐项审计通过，见gate7_closeout_v0_1.md；仅Windows目标栈的Engineering integration通过，legacy-only/coverage unknown/measurement NOT_ASSESSED等限制保留。旧attempt不追认；Gate8 NOT_RUN、待规划，不启动。**
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
- **平台边界（代码位置）**：Python 侧唯一平台边界是 `exposedpath/platform_adapter.py`（工具解析 + 结构化 argv + fail closed；包内仅此模块导入 `subprocess`）；Windows 启动层是 `scripts/*.ps1`。runner/manifest 核心保持平台无关，新增平台能力不得绕过该边界。

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
| `docs/v1_4_1/gate7_closeout_v0_1.md` | **Gate 7 Engineering closeout**：唯一合格fresh身份、逐项验收、原始diagnostics审查及legacy-only限制；不是Gate8科学全链验收 |
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
6. Gate7已关闭；先读 `gate7_closeout_v0_1.md` 和本文件当前状态，不重启EP-G7-08～11；Gate8仅待独立规划/授权。

## 1. 当前快照

- 清单版本：`7.19`
- 最近更新：`2026-09-24`
- 权威研究主体：`docs/current/ExposedPath_研究设计.docx`，文内版本 `v7.1`
- 当前执行依据：`docs/current/ExposedPath_实验协议.docx`，文内版本 `v2.1`；仍为 `Pre-Pilot`，不是 `Protocol Freeze`
- 当前研究阶段：`Engineering`
- 当前工作入口：根目录 `main`，已正规快进整合Gate7收尾及全部必要实现；目录约定见 `docs/repository_layout.md`。唯一验收执行commit仍为 `8d64f7580d43d7c8e1cb7a416b459cec8f60b011`，closeout commit为 `16604d59b05ee6d7e8415f75dbaaa1be3be7cf8a`；本轮目录整理提交不是新的执行身份。
- 当前数据资格：Gate 6 `final-04` 提供 `Engineering` / `Q0_QUALIFICATION_ONLY` 资格证据；历史 trace 仍仅限 `Prototype/Engineering`；尚无 `Pilot/Formal` 合格数据
- 当前 Gate 状态：Gate 0～7 = `PASS`（EP-G7-08～11完成）；Gate8 = `NOT_RUN`（本轮禁止启动，仅待规划）；Gate9～11 = `BLOCKED`（Formal平台未确定/未接入）；Gate12～14 = `NOT_RUN`。
- 当前最高优先级：保留Gate7唯一合格证据和closeout限制；无待补证/重跑事项。下一阶段Gate8仅待独立规划/授权，不自动执行；完整scientific coverage仍属Gate8。
- 历史总体判断（2026-09-20）：Gate 6 / Q0 已正式 `PASS`。frozen run `q0-win-4090-20260920-gate6-final-04` 在 package/analyzer `0.2.2`、formal binary SHA256 `4DFF82028F4FCFB57D42ABF061AE8962C1867DCE19DF23808D223B425868FC80` 下完成：21/21 `REAL_CASE_PASS`、2 个 synthetic-only case（`Q0-TERMINAL-TIE-001`、`Q0-SUBMISSION-RACE-001`）PASS、23/23 `SYNTHETIC_PASS`，且存在唯一一份 `q0_gate_report.json`（schema `exposedpath-q0-gate/0.2.0`、`23/23`、`verdict=PASS`、`q0_status=PASS`、report count `1`）。该 PASS 只说明当前 analyzer 在本目标 observation stack 上取得 **Q0 正确性资格**；不等于 Engineering Pilot、Pilot、Protocol Freeze 或 Formal 结果，也不建立第二平台等价性。身份、哈希、provenance caveat、根因映射与实现成熟度见 `docs/v1_4_1/gate6_closeout_v0_1.md`。
- 历史到达点（已由7.18取代）（`EP-G7-11`）：此前一次 fresh smoke 在 Pass1/Nsight 启动边界遭系统 BugCheck `0x133` 中断，根因未获证明。随后服务器报告：`799fb8d` 在目标 Windows/RTX 4090 的 static preflight `940 passed, 1 skipped`、compileall、verify、合同/Canonical/oracle 检查通过；新 Engineering smoke `smoke_20260923T134310Z` 的 Pass0、Pass1 inference/telemetry/parity 和最小 Nsight collection 完成，生成非空 REP，且未再出现 BugCheck。但即时 `nsys export` 在约 51% 停滞，被人工终止后 machine report 为 `BLOCKED_BY_NSYS`、exit 1，Analyzer 未运行；该 attempt **不是** Gate 7 acceptance evidence。相同 SHA256 的 REP 副本后续离线 export 得到 integrity PASS 的 SQLite，诊断 analyzer exit 0；仅支持“REP 可离线导出/分析”，不证明即时 export 挂起的精确根因，也不追认原 attempt。Gate 7 仍为 `NOT_RUN`，Gate 8 未启动。

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

**2026-09-24 目录收敛（7.19）：** Gate7 PASS保持；根main是唯一日常代码入口，五个退休worktree在保全独有资料后正常移除，分支/tag保留。gate7-audit原四份未提交文档先原样封存为a867d541d01f683ccfc462fcdec31afeeefbaecf，两份事故说明标注历史后整合，不覆盖当前进度。清理核实冗余的bundle、相同DOCX和缓存，原始证据/ZIP/冻结dist保持不变；本地handoff仅作索引，不形成第二事实源。服务器仅准备单根/固定checkout方案，未执行变更。Gate8 NOT_RUN，不运行GPU/Nsight；本轮验证和清理细项见repository_layout及本地回执。

**2026-09-24 最终closeout（7.18）：Gate7 PASS，EP-G7-11 completed。** 唯一合格attempt为`fresh_8d64f75_20260924T084650Z_d75ef1b8a4fb46709dbb7cfc1c95d27f/collection/smoke_20260924T084657Z`，执行commit 8d64f7580d43d7c8e1cb7a416b459cec8f60b011、dirty=false。服务器执行、本地审计；完整ZIP/清单/77文件逐字节、源代码CRLF身份、manifest/prompt、run/wmpc、parity、四request token-ready边界、14telemetry、profile/REP/export/SQLite、legacy JSON/CSV/diagnostics和machine report均通过；审计前后证据未变。版本化依据与hash见`gate7_closeout_v0_1.md`。

- 本次launcher原始全量日志：1040 passed、1 skipped/140.76s（不是dced364成绩；本次-q未列skip原因，源码支持pre-3.12 portability skip解释，不声称skip执行通过）；compileall/verify/pre-model/evidence门均PASS。两pass各warmup1/repeat2成功、32/2 tokens/batch1、无EOS/OOM/exclusion/retry。export1成功/0.265s，SQLite只读integrity/schema及analyzer冻结验收本地复核与服务器报告一致，machine READY_FOR_SMALL_PILOT/errors=[]、exit0。
- 原始SQLite69条diagnostics中44条warning属于11个其他进程；目标PID50740无warning且有12个NVTX range/4个structured token sync。按既有gate7-legacy-analyzer/1保留原始诊断，不把它们或dropped unknown抹成零，不推断工具根因。legacy-only/A结构验证/window coverage unknown/measurement_validity NOT_ASSESSED全部保留，不称v1.4.1真实workload科学全链已通过。
- EP-G7-08～10既有条件加本次EP-G7-11全部成立，Gate7正式PASS；旧BLOCKED/interrupted和离线诊断均不追认。无新GPU/Nsight/测试采集，只有本地只读验证与文档更新；Gate8仍NOT_RUN，下一阶段待规划、未启动。保留此前7.17未提交文档。

以下7.17和更早checkpoint中的NOT_RUN、待授权、待部署均为历史状态，以7.18和closeout为准。

**2026-09-24 8d64f75服务器最小静态复验本地审计（7.17）：** 直接读取 `identity_8d64f75_20260924T082913Z_1418665342a544ae911caf9d58bbff80/transcript.txt`，SHA256=`CF0C15956237D3F79F9124764D10F1AC73965693178287802952D83C5F69BF92`；记录时间08:29:13–08:30:35Z（服务器本地16:29:13–16:30:35）。服务器执行、本地只读审计，本轮不重跑测试。HEAD=8d64f7580d43d7c8e1cb7a416b459cec8f60b011；仓库venv Python3.11.16实际adapter解析Git成功、commit正确、dirty=false；定向185 passed/72.74s。compileall、contract37/37、Canonical7模块、oracle、diff/show-check全部exit0，最终HEAD及clean检查通过。测试mask=-1，结束恢复3。**不是8d64f75的服务器全量测试，更不是fresh smoke**；dced364的1014/1结果只保留为旧提交历史。

- 环境/模型关联：07:20:13Z的dced364环境身份、07:21:33Z的模型23文件内容清单、07:34:16Z的compiler/marker文件快照仍可作为相同环境/模型的历史来源；来源提交/时间必须保留，执行前检查未漂移，不作为新smoke结果。已直接读到cl19.38.33135.0、MSVC14.38.33130、x64/x64、mask实值及两marker零字节/空文件SHA，7.15所列补证缺口已补齐。模型清单SHA仍为72465C906BAEB0CFA4FD94D21EF6C69C1CD8046BB68C61A94C02A1580D2541F9；revision unknown，模型本体未传回，未声称本地重算权重。实际loader输入与.cache辅助项分开记录。
- 源码只读审查：launcher STEP3显式传preflight UUID/PCI及strict Git/worktree；通用manifest验证后调用`pre-model` CLI（logs/12_pre_model_identity），检查commit/clean/GPU/mask/G1身份；非零、报告非PASS或hash读取错误调用Set-GateFailure/exit1，位于STEP4首次模型加载之前。STEP2仅准备tokenizer输入。验收缺失不后移、不放宽；本次185定向包含producer和真实PowerShell前置门回归。
- 下一步：固定8d64f75、既定模型/GPU和32/2/1/1/2配置的fresh执行草案；launcher自身全量/compileall/verify、manifest/pre-model、Pass0、Pass1/Nsight、后处理及final report全部执行。仅保存历史快照作provenance，不复制旧attempt结果充数。现无已知必须先追加的补证；当前环境漂移或其他CUDA工作负载不明则STOP。尚未获得本次GPU/Nsight授权，未执行。Gate7 NOT_RUN，旧attempt BLOCKED，Gate8 DO NOT START；本轮文档不需要新提交或服务器部署。

以下7.16及更早状态为历史记录，其中“尚未部署/复验”已被7.17取代。

**2026-09-24 fresh dced364 身份链故障 / bounded repair（7.16）：** 直接读取用户传回的 `fresh_dced364_20260924T074033Z_43e53591d86341b2b025e1daf174b62e` 中 `collection/smoke_20260924T074034Z`；服务器执行、本地只读审计。machine decision=BLOCKED、exit=1，Pass0/Pass1/REP→SQLite/SQLite validation/analyzer process 均 exit0，但 analyzer acceptance 因 manifest commit 缺失、evidence 因请求 UUID/PCI 缺失而失败。两个 pass 全部14条 telemetry 的 observed index/UUID/PCI 一致且 query exit0，requested UUID/PCI 均 null；不能把它解释为跑错 GPU。旧产物不补写、不重验追认。

- 根因已在本地真实 Git 子进程入口复现：adapter 的 `capture_output=True` 与 `stderr=DEVNULL` 冲突，Python 抛 ValueError 后被 manifest 两个 getter 吞成 null，并非已证明的服务器 PATH/权限/timeout 问题。另 launcher producer 未传已有 preflight UUID/PCI；通用 `SHA256:` 输出实为 prompt 哈希，却写入 machine manifest 哈希。
- 最小实现：adapter 用明确 stdout/stderr pipe，Git 保留失败 stderr；Gate7 producer 显式 worktree、严格 Git 查询（原异常进入日志，无替代值）、结构化传入 preflight GPU 字段；Pass0 前核验完整 commit/clean/GPU/mask/G1 Engineering 身份，失败即阻塞；报告分别保存真实 manifest 文件 SHA256 与 prompt SHA256。runner、analyzer、冻结 Measurement Contract/S/A/B/D、Q0、Gate6证据和 observation profile 不改。
- 扩展审计：两 pass 的 manifest SHA 为 `e8e8b87042d0eff0bdb80def97b2ce40a0363d07b060cdbaa75f78842c40bc5b`，prompt SHA 为 `4dffd0ddcbd3185c656ae4a27efaf5aab302febba6ead5df4d37d903a2091920`；run/wmpc、G1 natural、mask、32/2 tokens 一致。runner source SHA `f3765d96f161f13a879c44b1f98adf3c36c8a9a2fdc7ff136af929b98301a6c3` 与 dced364 的 CRLF 文件字节一致（不是把 LF/CRLF 文件哈希视作相同）。analyzer metadata commit=dced3646b536；fatal_errors为空、dropped unknown、已批准的 CUDA event optional warning 仍保留，不升级科学有效性。
- Tests first：先用实际 launcher Python producer + 临时真实 Git 仓库复现 null commit/异常被吞；再实现并验证 producer→manifest→现有 runner parity/telemetry（仅 GPU query 替身）及真实 Windows PowerShell pre-model block。新增负例覆盖 missing/malformed/mismatch/dirty/mask/Git error；未执行 GPU、真实 Nsight 或服务器命令。此前7.15未提交文档保留在同次提交。
- 本地Windows/Python3.12 CPU-only最终验证：定向185 passed（含新增26项）、全量1036 passed/5 skipped（219.40s；屏蔽CUDA PATH并确认无nvcc，五项均Q0 source编译检查）；compileall四目录、contract37/37、Canonical boundary7模块、oracle independence、git diff --check通过。真实PowerShell block与真实Git调用不等于服务器/GPU验证；完成本地逐项自审，未声称独立外部审查。旧 attempt BLOCKED，Gate7仍 NOT_RUN，EP-G7-11未验收。部署新提交并完成服务器静态复验后，也必须另行授权全新 smoke；不得复用本次证据改变 verdict。完整真实 workload Canonical→S→A/B 仍属于 Gate8。

以下7.15和更早段落为历史快照；其中“仅余环境补证/无代码缺陷/仅文档更新”等不再是当前执行指令，以7.16为准。

**2026-09-24 dced364 服务器静态/环境/模型原始记录本地审计（7.15）：** 直接读取 targeted_dced364_20260924T070511Z_75d74c2e649e4303bd65a290d4185ded、static_dced364_20260924T070829Z_9bfeacd94903497ba472240b54b10f70、identity_dced364_20260924T072013Z_400f5980c94548b79d7b2e8aac66b26c、model_dced364_20260924T072133Z_d4a3ac4169ab48a1bba6d4f7d1f703ae 的四份 transcript 及模型清单。服务器执行、本地审计，未重跑测试：新增 33 passed、定向 130 passed、全量 1014 passed/1 skipped（263.79s）；skip 明确为 test_python_source_portability.py:98 的 pre-3.12 编译时已拒绝该 f-string，非未知失败。compileall、contract37/37、Canonical、oracle、diff/show-check 与 verify_pilot_install -SkipTests 均 exit0。HEAD/parent 与部署身份一致，记录显示检查后 clean；本地无服务器文件系统的独立实时观测。

环境记录支持：Python3.11.16 / repo venv / Conda base、torch2.6.0+cu124 / CUDA12.4、transformers5.17.0、nvcc12.4.131、MSVC 环境变量14.38.33130；GPU3/目标 UUID/PCI/RTX4090/driver555.99、logical0 且唯一可见；Nsight2026.2.1.210-262137639646v0。**尚缺文件身份补证**：四份记录未输出实际 where cl 的首项及 cl.exe 文件版本，也未输出两个 0-byte marker 的绝对路径/length/SHA256。CUDA 两变量的名称仅见 transcript Host Application 命令文本，尚缺实值输出；一次纯文件/环境快照即可补齐，不需重跑静态测试或 GPU 初始化。不要混淆 Python 构建字符串 MSC v.1942 与当前 cl.exe。

**模型与输入：** 本地复核 model_sha256.csv 为23行、合计3098976006 bytes、SHA256 `72465C906BAEB0CFA4FD94D21EF6C69C1CD8046BB68C61A94C02A1580D2541F9`。模型本体未传回，未本地重算权重 hash。七个 loader 输入候选为 config.json、generation_config.json、merges.txt、model.safetensors、tokenizer.json、tokenizer_config.json、vocab.json；其余为13个 .cache 辅助文件及3个文档/仓库辅助文件，不据缓存文件名推断 revision。Engineering runner 的 model_revision 默认 unknown，manifest schema revision 仅要求 string，Gate7 合同未要求可解析 hub commit；因此 unknown+明确本地内容快照满足本次工程身份限制，不宣称 upstream revision 已知或 Formal 资格。fresh attempt 必须关联该清单、保留 unknown，模型内容若改变先 STOP。

源码核对：launcher STEP2 生成4组各32 tokens 的合成 token IDs；cli 使用 seed=42+i*1000、合法 vocab 范围，无 chat template。batch1 使用第一样本，prompt 文件在测量窗口外生成，并由两 pass 共用且校验 SHA256。32 input / 2 output（首 token prefill，第二 token decode）、warmup1/repeat2 符合 pilot_runner_contract §§2/4/5 和当前 launcher 默认范围；不构成 Pilot workload 选择。执行身份为 eager/fp16/sdpa、do_sample=false、G1_NATURAL/natural_token_ready、n1_intervention=null、run_role=PILOT/data_role=Engineering，非 N1 实验。实际新 prompt digest/manifest 由 fresh launcher 创建并回传，不提前伪造或要求另跑一遍。

**既有 JSON 适配核验：** 本地运行 dced364 的 validate_analyzer，只读取旧 JSON/SQLite/CSV，临时合成 manifest 提供旧 ecac542 commit 与明确 SYNTHETIC-SHAPE-CHECK-ONLY 身份（原旧诊断包没有完整 manifest）。结构兼容 PASS、issues=[]、窗口 coverage unknown/null；将临时 manifest 换成 dced364 则正确 BLOCKED（Analyzer/runner commit identity mismatch）。这是适配逻辑检查，不是旧 attempt 的 lineage 或新验收。14个源文件检查前后哈希不变；未运行 analyzer、Nsight、模型或 GPU。未发现需要改代码的缺陷。

**下一步最小动作与授权边界：** 补上述 cl/marker/mask 快照后，请求一次固定身份的完整 fresh smoke 授权；不重复手工静态检查，但不跳过 launcher 自身 static/verify。完整新目录关联四组快照、模型清单和最终补证，保留全部 machine report/日志/manifest/prompt/parity/telemetry/REP/SQLite/analyzer 产物；失败保留现场、不 resume/覆盖。成功进程码与 READY_FOR_SMALL_PILOT 仍须后续逐项审计，不直接 Gate7 PASS。本地 handoff 的新 final-review 草案为入口；本轮仅文档更新，无新提交/部署包。

**2026-09-24 用户批准的验收修订 / implementation checkpoint（7.14，取代 7.12/7.13 的待决状态）：** 权威执行计划 §6 冻结 `gate7-legacy-analyzer/1` 工程验收修订；这是对 Gate7 的显式修改，不修改 Measurement Contract。只适用于新执行 Engineering attempt；launcher 在任何采集前拒绝 ExistingSmokeDir/ResumeFrom，不覆盖或追认历史。保持静态、Pass0/Pass1、parity、telemetry、REP/SQLite 和 final machine report 全部门槛。

新增验证分支只接收明确的 exposedpath-v2 JSON/metadata/parser identity。校验 A/repeat 输出结构、同步明细类型/UID/时间、CSV 必需列、版本/commit/workload/manifest 身份和 diagnostics；拒绝空对象、缺产物、NaN/重复键、fatal/unreviewed warning 与新 dropped 状态。仅保留已批准 optional event-table warning 和 dropped_records_status=unknown。报告显式 legacy-only / ENGINEERING_INTEGRATION_ONLY / measurement_validity=NOT_ASSESSED；window_coverage count/duration=null 并给出原因；原 trace_quality 和同步明细保留，不构造 valid/total。A 标记 VALIDATED_STRUCTURE_ONLY，绝非科学守恒 PASS。SHA256 绑定本次 invocation 的 manifest/input/output/CSV，明确不伪装为 legacy 自带的 scientific lineage。

**测试与审查：** 先执行实际 PowerShell STEP6 validation block 红测，准确复现 sync_coverage missing；随后增加坏 CSV/矛盾 validity/非有限 diagnostics 红测和历史 resume 红测，再实现修复。自审发现 CSV/JSON 身份关联与摘要类型校验不足，先补 3 项红测后收紧校验。新增合成 fixture 不包含私有 trace 或服务器路径。最终 4 文件定向测试 130 passed（新增验收测试 33 项）；CPU-only 全量 1010 passed、5 skipped（141.10s，本地 Windows Python 3.12 venv，进程内 CUDA_VISIBLE_DEVICES=-1 并移除 CUDA PATH/确认 nvcc 不可见；5 skip 均为 Q0 CUDA source 的 nvcc 检查，不代表服务器 skip 原因）。compileall exposedpath/analysis/exposedpath_v141/scripts、contract 37/37、Canonical boundary、oracle independence 与 diff-check 均通过。本地自审覆盖 fail-close、native argv、report 传播、unknown 不补零及历史 evidence 防追认；不是独立外部评审、服务器或真实 Nsight 验证。生产 analyzer、runner、冻结 S/A/B/D、Q0、Gate6 evidence 和 observation profile 零修改。

**交付与后续：** 原有未提交进度记录保留并纳入同一次代码提交；本地根 AI_HANDOFF 为未跟踪接力索引，不提交私有路径。服务器静态复验通过后也不能直接运行 smoke；fresh 草案须另行授权，固定新提交/模型/环境/新目录并读取机器报告。Gate7 NOT_RUN、Gate8 DO NOT START。v1.4.1 完整 request A 已实现，真实 workload Raw→Canonical→S→A/B、completion、互斥守恒、unattributed、validity/coverage 的验收仍为 Gate8 EP-G8-02，不由本次 offline PASS 代替。

**2026-09-24 coverage 用途与字段充分性复核（7.13，收紧 7.12 建议）：** 用户原则同意分开记录 supported/B-valid，但要求 request/phase 范围、physical identity 去重、重叠与 unknown 处理有合同依据。coverage 仅用于揭示 A 归属/B 解释的证据覆盖与缺口，是质量/provenance 诊断，不是新增研究贡献指标，不能替代 request-level A 守恒或 validity；同步时长累计不是 request-visible exposure，同步 coverage 不是完整 request 的可解释比例。

- **分母：部分字段存在，不足以完成所要求的窗口统计。** legacy 实物有 6 个不同 physical_sync_uid、request/repeat 数字和 sync_start/end_ns，可证明已输出 6 行无重复；不能由此证明 physical sync universe 完整。repeat_results 只有 window_duration_ms，未输出窗口 start/end；4/6 phase 为整段 structured label。legacy UID 和数字 request/repeat 不能未经核对替代冻结 sync_identity 的 run/pass/request/repeat/origin/callsite/ordinal。不能按 2 条规范 phase 摘要过滤后声称完整分母，也不能在 adapter 中重新猜测 ownership/phase。
- **判定：冻结状态明确，legacy 不能无损映射。** Measurement Contract §9：VALID_NONEMPTY 与 VALID_EMPTY 可用于 A 有效归属，后者 B_NOT_APPLICABLE；AMBIGUOUS/INVALID 不可归有效同步。B 只有 B_VALID 才有有效解释。legacy wait_set_valid=false/NO_PENDING_ACTIVITY 并不证明冻结 INVALID 或 VALID_EMPTY；legacy B_valid 布尔也没有冻结 B_AMBIGUOUS/B_NOT_APPLICABLE 的状态区分。可原样保留 legacy 标志，不能命名为已恢复的 v1.4.1 supported/B-valid。
- **count/duration：不把旧 audit 的 sum 当作新规则。** frozen §10 要求 A 使用窗口裁剪、interval union、invalid 片段优先；§11 禁止 additive B total。count 应基于同一 universe 的 distinct physical identity；phase 计数不可直接相加成 request count。现物 6 条区间无同 request 重叠，但不证明对重叠输入适配正确。同步窗口并集诊断与逐调用时长加权是不同口径；当有效/无效 sync 重叠，简单 union(valid) 也不等于 A 可归属片段。当前机器输出未定义 coverage 的独立重叠优先级与跨 phase 计数约定，不由 adapter 自行补成科学规则。
- **零值与缺失：** 完整 universe 已知且为空才可记录 count=0；比例为 null/不适用而非 0% 或 100%。正数量、零总时长与空 universe 分开记录；缺少窗口/identity/状态则数值 null、明确原因，不能输出零或静默删行。INVALID、AMBIGUOUS、UNKNOWN、B_NOT_APPLICABLE 分开，不能折叠为 false；legacy 未提供的区分保持 unknown。上述为约束，尚未发布新的 schema 或改变 launcher 验收。

**集中待决事项：** (1) Gate7 是否接受明确标记 legacy-only、不能恢复窗口 coverage 的诊断报告（缺失保持 unknown），及此状态如何影响既有 analyzer gate；这属于验收映射决定，不因 offline PASS 自动放行。(2) 若必须具备 request/phase coverage，则需批准补充稳定 identity/窗口/状态的 producer-side 证据输出及对应范围，不能把完整 v1.4.1 链静默提前到 Gate7。(3) coverage 独立 schema 的跨 phase count 和重叠 duration 口径需在完整输入合同上明确，禁止借此改写冻结 A/S/B。建议优先裁决 (1)，把 legacy 诊断与后续 scientific coverage 分开；不再推荐直接把全明细 duration 求和作为窗口覆盖。

**实现与资格边界：** Gate7 当前调用 legacy analysis/exposed_accounting.py。v1.4.1 的完整 request A 拆分已有 a_accounting.py/ab_inputs.py/ab_bundle.py 实现：显式窗口、原子片段、invalid 优先、整数域守恒和去重校验；但真实 workload 的 Canonical→S→A/B 全链验收仍属 Gate8 EP-G8-02。此次离线 PASS 不替代该验收。本轮只读字段/源码核验并更新记录，未改代码或测试、未运行 GPU/Nsight；冻结合同与旧证据不变。生产修复继续暂停，不创建“全部 null 但 PASS”的适配来绕过门槛。

**2026-09-24 本地完整诊断包审计（取代下方“未收到完整产物”的当前状态）：** 已直接读取诊断 `postprocess_ecac542_20260924T040753Z_a95e202b974d48eca6824b4c2564b460`。本地复核 ZIP 2024855 bytes、SHA256 `89C745A85EA62B7AB32B413751AB18195F8AFA2DE807914DBBDC81F50EB94909`、14 文件 CRC 及解压字节一致；v2 清单固定哈希及 12/12 项文件哈希匹配。SQLite 只读 integrity_check=ok；helper 首次 export PASS/analyzer_allowed=true 与回执一致。identity 中 helper/analyzer 源哈希分别匹配 ecac542 Git blob 的 CRLF checkout 字节，不把 LF/CRLF 差异误判为代码变化。旧服务器原始 machine report 未包含在此包，关于其不变性仍为 identity/transcript/用户回传证据，不声称本地读取过该原件。

**已复现的阻塞与合同缺口：** 本地提取并执行当前 launcher STEP 6 的真实 validation block（不执行 analyzer/Nsight），给定 exit=0 和收到的 accounting_result.json，得到 analysis_ok=false、conservation=present、count/duration=unknown、errors=[sync_coverage missing]。PowerShell 对 A_summary 的大小写匹配正常。producer write_accounting_result 与 legacy metric spec §11 均未输出 sync_coverage；所以是 consumer/producer 合同脱节，不是 export 失败。离线诊断只检查 JSON 可解析，未覆盖此验收；不得称为完整 launcher PASS。

**必须先确认的映射，不擅自修复：** 当前 Gate7 计划、pilot_runner_contract §9/§10 及 server_smoke_test 未定义 launcher 的 sync_count_valid/sync_duration_valid_ms 应指 wait-set supported 还是 B-valid，也未明确分母是否为全部 b_sync_details。旧 summarize_small_pilot 使用 B_summary.full_request 且 duration=null；generate_p1_audit 则对所有 b_sync_details 分别累计 wait_set_valid 与 B_valid 对应的 sync_duration_ms。两者不能无条件互换。实物 B_summary.full_request 为 2/2，但 b_sync_details 共 6 条、B_valid=2；另外 4 条 wait_set_valid=false/NO_PENDING_ACTIVITY，phase 为整段 structured NVTX label。不得从原因字符串改判 supported、用 B 2/6 冒充 sync coverage，或按 full_request 摘要漏计其余 4 条。建议修复位置为 launcher 侧显式 legacy-output adapter，保留 supported/B-valid 两组诊断、来源和未知状态；其具体字段/分母/缺失处理需先获确认，不改变 analyzer/S 语义。批准后先用脱敏 producer-shaped fixture 做真实 consumer 红测，再实现适配；本轮未添加测试或修改生产代码。

**trace_quality / diagnostics 边界：** event activity table unavailable 为 legacy optional warning；fatal_errors=[] 不等于无采集诊断。SQLite DIAGNOSTIC_EVENT 有其他 globalPid 的 NVTX/CUDA 初始化或未采集警告；持有 NVTX/runtime 行的进程 globalPid 为 282358666231808，其日志记录 12 NVTX / 41975 CUDA events，未出现上述 severity=2 警告。不能据此推导 dropped=0：analyzer dropped_records_status 仍为 unknown，保持原值。B 摘要/structured phase 局限不升级为 v1.4.1 科学语义验收，也不在本次字段修复中扩大到 Gate8。

**本轮收口：** 仅更新进度与本地 handoff，保留原有未提交记录；HEAD/parent 不变，无新 commit/bundle/部署动作。生产代码、测试、REP、旧 machine report、Gate6 evidence、Measurement Contract、S/A/B/D、Q0 和 observation profile 均不修改。Gate7 NOT_RUN，fresh smoke PAUSED，Gate8 DO NOT START。以下 7.11 回执与草案按历史记录保留，不能再作为当前执行指令。

**Gate verdict：`PASS`（2026-09-24）。** EP-G7-08～11完成；唯一合格fresh及逐项证据见`gate7_closeout_v0_1.md`。旧BugCheck、BLOCKED_BY_NSYS和dced364身份链BLOCKED不追认；本地最终审计未运行GPU/Nsight或操作服务器。

**2026-09-24 用户回传的离线后处理回执（未直接取得完整服务器产物）：** commit `ecac54272230fe5feef517ad9d908c64e93d517f`，role `POSTPROCESSING_IMPLEMENTATION_VALIDATION`，诊断 id `postprocess_ecac542_20260924T040753Z_a95e202b974d48eca6824b4c2564b460`；Nsight `2026.2.1.210-262137639646v0`，repo .venv Python 3.11.16、base Conda gate7_py311。helper PASS、analyzer_allowed 检查通过，仅一次 export：PID 64844、exit 0、process_exited=true、timed_out=false、terminated_pid=null、validation_issues=[]、elapsed 0.312 秒。SQLite 2568192 bytes，SHA256 `310f119306414b7f740574566e59dcf9112c363141038125ab9e7230dc269b25`；成功 attempt/canonical/report 哈希一致，integrity/schema PASS、issues=[]、exit 0，legacy analyzer exit 0、accounting_result.json 可解析。源/副本 REP SHA256 均保持 `C2F561943C6465CA758845E8526652591363AD85EC8BCEAB074C9413AD6BB219`；原 machine report SHA256 保持 `CE3EFC198A3CA8D93B676AA77FEF1A5AB03E4409EE6E7E42B84D82D319192100`、原 verdict BLOCKED_BY_NSYS。结束 HEAD 不变/clean、无残留 nsys；独立 validation_result.json PASS/error=null。只证明该 REP 上真实离线成功路径的实现集成；未触发真实 timeout/kill/retry，不证明即时挂起根因修复。与前次手工诊断 SQLite hash 不同，不要求不同 export 产物逐字节相同；本次身份须以本次 REP lineage/attempt/canonical/report 一致性审计。

**清单补救边界：** 初次流式枚举把正在写入的 artifact_sha256.csv 纳入输入而发生占用错误；先前的 PASS 不保证清单生成成功。用户报告协调窗口仅修复清单生成（快照文件列表、排除 artifact_sha256*.csv、写新文件并逐项复核），没有重跑 export/analyzer、没有改仓库代码。旧清单保留，有效 artifact_sha256_v2.csv 含 12 文件、逐项校验通过，清单自身 SHA256 `FCF2FAF38F7B58F8EE5D54A8B7B5A9CA10DD88BF23E93EC6A68640FE36B58735`。补救发生在原 transcript 结束后，来源仅为用户回传；不能声称原 transcript 包含补救过程。本地 handoff 草案已改为先快照/排除所有清单，再计算和写入新清单。

**Analyzer scope 判断（沿用既有条款，不修改判据）：** exposedpath-v2 标记、CUDA event activity table unavailable 与 B valid=2/6 本身不违反 Gate7 integration smoke。依据：执行计划 §1/EP-G7-11 关注 runner/launcher 边界与身份；pilot_runner_contract §9 明确 A/B 来自 legacy analyzer，§10 尚不支持 full event synchronization recovery；此前已接受的 scope checkpoint 把真实 workload 完整 Canonical→S→A/B→D 链放在 Gate8 EP-G8-02。代码证据：analysis/accounting_utils.py 将 event_table 列为 missing_optional；gate7_smoke_validation.py 的必需表集合不含 event activity table；launcher STEP 6 要求 analyzer exit 0、可解析 JSON、a_summary 与 sync_coverage，并记录 count/duration coverage，未规定 B valid 比例阈值。故不能临时增加 6/6 阈值，也不能把 2/6 解释为 v1.4.1 语义 PASS。仅“JSON 可解析”的回执尚不能独立证明 a_summary/sync_coverage 字段齐全，需完整 accounting_result/SQLite/日志核验，尤其不得将缺表或 dropped-record 问题整体降为可忽略警告。

**2026-09-24 用户回传的服务器验证结果（非本助手亲自执行）：** HEAD `ecac54272230fe5feef517ad9d908c64e93d517f`，parent `5a37eb0848dea486c715750341ff8a07d0efcee1`，验证前后 porcelain 均为空；bundle `ExposedPath_Gate7_fixture_ecac542.bundle`，3038 bytes，SHA256 `832B2EE632218C476EBBD1CC877442F6226D1A63F50606E855A5FE59D67B92B7`，bundle verify 通过。环境为 Windows PowerShell 5.1.20348.2849、Python 3.11.16 Anaconda 构建，测试使用 repo `.venv`，base interpreter 属于 Conda `gate7_py311`；VS host/target x64，VCToolsVersion 14.38.33130，CUDA_DEVICE_ORDER=PCI_BUS_ID、CUDA_VISIBLE_DEVICES=3。单测 `1 passed in 1.27s`；后处理文件 `19 passed in 39.83s`；三文件 targeted suite `97 passed in 35.84s`；全量 `981 passed, 1 skipped in 182.84s`。compileall、contract 37/37 PASS（CONTRACT_INTERNAL_CONSISTENCY_ONLY）、Canonical boundary PASS（7 个下游模块）、oracle independence PASS（STATIC_ORACLE_AND_EVALUATOR_INDEPENDENCE）、diff-check、show-check 均成功；用户报告上述所有命令 exit 0。单个 skipped 原因未提供，保持 UNKNOWN，不由本地 skip 结果推断；本轮回执未包含新的 verify_pilot_install 结果。本地只核对了提交/parent/bundle 与回传摘要的一致性，未获得或逐文件审计服务器原始日志。

**后续操作边界：** 离线验证按用户回传已完成，不重复运行；完整目录及 v2 清单、独立清单修复回执待传回。fresh smoke 草案置于本地 AI_HANDOFF.md：继续固定 ecac542、核对环境与模型内容身份、先显式 verify_pilot_install，再由完整 launcher 自行执行静态/Pass0/Pass1/后处理/最终门槛；全新 evidence，不使用 ResumeFrom/ExistingSmokeDir/SkipStaticTests/DryRun。本轮未执行任何草案，未生成新提交或部署包；静态/离线成功不能授权 fresh GPU smoke，READY_FOR_SMALL_PILOT 机器字段也不能替代人工 Gate7 verdict。

**2026-09-24 Windows venv fixture checkpoint：** 服务器静态验证的 timeout/retry 测试中，`Popen.pid=63380`、fake exporter `os.getpid()=27820`；成功 retry 不写 PID 文件，因此不是 PID 文件被覆盖。Windows venv launcher 与实际 interpreter 为两个进程，结束 launcher 不能证明 exporter 当时已退出。本地新建 Windows venv 后，先运行原测试复现同一断言失败（`8364 != 10756`），再仅把共享 fake-exporter fixture 的 Windows 默认 executable 改为原安装位置的 `sys._base_executable`；非 Windows 保持 `sys.executable`，显式 executable override 保留。直接使用 base interpreter 不涉及复制/搬迁，无需引入 copied-executable 场景的 `PYTHONHOME`/`PATH` 设置。保留 `Popen PID == fake exporter os.getpid()`、terminated PID、退出确认、partial 保留、独立 retry 输出及 canonical promotion 断言，并在真实第二次 `Popen` 前检查第一个进程已退出。生产 `Popen`/`kill`/`wait`、Nsight observation profile、Gate 7 acceptance、runner、Measurement Contract、S/A/B/D、Q0 与 Gate 6 evidence 均未修改。此项仅为 Engineering/static-validation 修复，不是 Gate 7 acceptance，也不证明真实 Nsight 超时路径。

此前本地 Windows venv 验证：原 PID-sensitive 单测先 `1 failed`，修复后 `1 passed`；后处理测试文件 `19 passed`；服务器同款 targeted suite `97 passed`；CPU-only 全量 `977 passed, 5 skipped`（进程内移除 CUDA PATH、确认 nvcc 不可见并设置 `CUDA_VISIBLE_DEVICES=-1`）。`compileall exposedpath analysis exposedpath_v141 scripts`、contract 37/37、Canonical boundary、oracle independence 与 diff-check 均 PASS。随后用户回传的目标服务器验证见上；本助手未运行 GPU 或真实 Nsight。

**2026-09-23 scope / trace 审计与 repair checkpoint：** Gate 7 只验目标 Windows/RTX 4090 的 runner、identity、Pass0/Pass1、Token-ready、phase-boundary、CUDA+NVTX 和 launcher integration smoke；真实模型 workload 上完整 `Canonical Raw v1.4.1 → S → A/B → D / Exposure Signature` 首次属于 Gate 8 `EP-G8-02`，不提前纳入 Gate 7。前一次 fresh attempt 的已知边界是 `Pass0 completed → Pass1/Nsight launch boundary → system BugCheck 0x133`；exact root cause **NOT PROVEN**，不得归因 NVIDIA、Nsight、launcher script 或 admin PowerShell。Trace minimization 是删去 Gate 7 非必需采集项并分离后处理，**不是** BugCheck 根因修复。

上一轮 bounded launcher repair 将 Gate 7 `data_role` 显式设为 `Engineering`，静态门槛对齐 `pytest -p no:cacheprovider`、`compileall exposedpath analysis exposedpath_v141` 与同一 Python 的 `verify_pilot_install`；最终门槛实际验证六组 cross-pass parity、attempt accounting、physical/UUID/PCI/logical telemetry identity，缺证据或不一致 fail closed，`BLOCKED` machine report 对应非零进程码。Nsight collection profile 为 `--trace=cuda,nvtx --sample=none --cpuctxsw=none --cuda-memory-usage=false --cuda-trace-scope=process-tree --isr=false`，collection 不启用 stats；原流程按 `collection → 非空 .nsys-rep → 显式 SQLite export / schema 校验 → analyzer` 执行，并在启动前保存 exact argv、Nsight 版本与 observation-profile provenance。新 profile 与旧 smoke evidence **不可拼接验收**。其后 `799fb8d` 已在服务器执行一次新 Engineering smoke，结果见下；Gate 7 未判 `PASS`，Gate 8 不启动。

**2026-09-23 后处理可靠性修复 checkpoint：** 服务器报告的 `799fb8d` fresh smoke evidence id 为 `ep-g7-11-final-799fb8d-20260923T134309Z/smoke_20260923T134310Z`（绝对服务器位置保留在私有交接记录，不纳入仓库）。Pass0/Pass1 与最小 collection 完成，REP 大小 `979593` bytes、SHA256 `C2F561943C6465CA758845E8526652591363AD85EC8BCEAB074C9413AD6BB219`；即时 export 处理 `43074` events 后约 51% 停滞，人工仅结束该 exporter PID，launcher 正确报告 `BLOCKED_BY_NSYS`。相同 hash 的 REP 副本稍后离线导出 `2568192`-byte SQLite（SHA256 `DE064BFB37FF1CA3D9FEF240278E8BF9C1F531308D83B712B7FD3008373C5A6C`），`PRAGMA integrity_check=ok`、46 tables，`analysis/exposed_accounting.py` exit 0/`ACCOUNTING COMPLETE`；这只是否定 REP 固有不可导出的解释，exact Nsight internal hang root cause **NOT PROVEN**。本轮代码仅在 profile exit 后增加有界 REP 稳定/可读/哈希 gate、单次 180 秒且最多两次独立路径 export、仅结束超时 attempt 自身 PID、保留 stdout/stderr/partial SQLite、REP hash 复核、integrity+Gate7 必需 CUDA/NVTX/metadata 表及关键字段校验、同目录原子且无覆盖的 canonical 链接 promotion 与 SHA256 对照、Analyzer 前再次校验；旧 machine report 不可被 resume 覆写，恢复时核对后处理 PASS/attempt/REP/SQLite 身份。可选 `nsys stats` 不再位于 acceptance 主链。上述 schema gate 只检查 Engineering export 完整性，不把真实 workload 的完整 v1.4.1 science chain 提前移入 Gate7。既有 profile launch 对含空格路径的完整执行尚无验证，本轮不声称通用空格路径支持；目标服务器路径需在后续部署前核对。Nsight observation profile、runner、Measurement Contract、S/A/B/D、Q0 与 Gate 6 证据不变。原 attempt 保持 `BLOCKED_BY_NSYS`，诊断 SQLite 不回填；修复尚未获 GPU smoke 授权。

本地 Windows argv/path 二审：新增纯 mock 回归，以含空格路径下的测试可执行文件副本运行 fake exporter，同时覆盖含空格 REP、输出 SQLite、stdout/stderr 文件和逐项 argv；实际走 `Popen(argv, shell=False)`，无生产实现改动。该回归不等于目标服务器真实 Nsight 或 elevated parent 验证；原 profile launch 的通用空格路径限制仍在。新增/相关定向测试 `97 passed`；全仓 CPU-only `977 passed, 5 skipped`（在 Python 进程内屏蔽本机 nvcc 并设 `CUDA_VISIBLE_DEVICES=-1`，不等于目标服务器 GPU smoke）；`compileall`、Measurement Contract `37/37 PASS`、Canonical boundary 与 oracle independence 均 PASS。一次未成功屏蔽本机 CUDA 13 nvcc 的全仓尝试为 `953 passed, 1 failed, 4 errors`，失败局限 Q0 CUDA source 编译夹具；未据此改动 Q0 或冻结证据。

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
- [x] `EP-G7-10`（2026-09-21 完成，合并旧 `EP-G7-05`＋旧 `EP-G7-06` 的基线失败部分）
  - **Objective**：把 Windows PowerShell、平台探测、Nsight 调用收敛到 adapter/launcher；处置两项既有 smoke 失败。
  - **Why**：平台差异目前散落在脚本中，任何第二平台（Gate 9）都会重新暴露同类问题；未解释的基线失败会让后续回归无法区分“新缺陷”与“旧噪声”。
  - **Implementation**：runner 核心改用 `pathlib` 与结构化子进程参数；平台特定逻辑下沉到 adapter/launcher；修复或按平台范围决定明确重界定 `tests/test_server_smoke_script.py::test_dry_run` 与 `::test_spaces`。
  - **Evidence**（无 GPU）：新增 `exposedpath/platform_adapter.py` 作为唯一 Python 侧平台边界（平台身份、可执行后缀、工具解析、结构化 argv、`ToolUnavailableError`/`ToolExecutionError` fail closed），包内仅此模块导入 `subprocess`；`exposedpath/runner.py` 的 driver-version 与 telemetry 查询、`exposedpath/manifest.py` 的 driver/git provenance 全部改经 adapter（字段名与取值语义不变，无 schema 变更）；新增 `tests/test_platform_adapter.py` 覆盖平台身份、`.exe` 规则、解析顺序、无 shell 的字面量传参、fail closed，以及“核心模块不得导入 `subprocess`／不得出现裸工具名与 `shell=True`”的结构不变式。两项 smoke 失败根因：`tests/test_server_smoke_script.py::_run` 以裸名 `"powershell"` 启动宿主、且 launcher 的 `Resolve-Executable python` 依赖环境 `PATH`；受控复现（`PATH = System32 + WindowsPowerShell`，无 python）得到 launcher `exit 1` + `ERROR: Cannot resolve PythonExe`，即该两项的 `assert 0 == 1`，`PATH` 连 PowerShell 目录都缺失时则表现为 `FileNotFoundError`。修复：显式解析 PowerShell（`shutil.which` → `%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe`）、显式传 `-PythonExe sys.executable`、失败时在断言消息中回显 stdout/stderr，并把同文件 `test_import` 的裸 `python` 一并改为 `sys.executable`；新增回归 `test_dry_run_is_independent_of_ambient_path`（PATH 去 python 仍须 `exit 0`）与 `test_launcher_invocation_does_not_use_bare_powershell_name`（AST 断言 `subprocess.run` 首参不得为裸字符串）。
  - **PASS**：`tests/test_platform_adapter.py` 20 passed；`tests/test_server_smoke_script.py` 31 passed（含 PATH 去 python 的回归）；`tests/test_server_smoke_script.py::test_dry_run`、`::test_spaces` 在默认与受控 `PATH` 两种环境下均 `exit 0`，**不再计为未知失败**；两项失败为测试非封闭而非产品缺陷（launcher 语义未改，仅显式化宿主与解释器）。
  - **STOP**：若某项必须先有真实 GPU 才能判定 → 移交 `EP-G7-11`，不得用 mock 结论代替。
  - **Dependency**：独立于 `EP-G7-08`/`EP-G7-09`，可并行；其结论不依赖 GPU。
  - **Unlock**：平台可移植性被结构性保护，测试基线不再含未解释失败。
- [x] `EP-G7-11`（2026-09-24完成；fresh 8d64f75完整证据逐项审计通过；合并旧EP-G7-06全量验证与EP-G7-07；旧attempt不追认）
  - **最终Evidence**：`gate7_closeout_v0_1.md`，本次launcher1040 passed/1 skipped、静态与verify门PASS、目标平台两pass及后处理完整通过；保留legacy-only工程限制。下述实现过程中的早期失败仍为历史，不是当前阻塞。
  - **Objective**：在 Windows/RTX 4090 上执行 runner 端到端 smoke（Pass0/Pass1、identity/phase boundary、exclusion/retry 记录），证明产出可被机器读取且与 Gate 7 合同一致，并完成 Gate 7 验收决定。
  - **Why**：只有真实 GPU smoke 能证明该执行链在真实执行栈上成立；Gate 8 必须以这份证据为入口。
  - **Implementation**：smoke 前置修复新增纯函数 `resolve_logical_cuda_index(physical_gpu_index, cuda_visible_devices)`，不读取 GPU 或 `torch.cuda.device_count()`；`manifest.py` 与 server smoke 共享该 helper，torch name 查询只使用 logical index，manifest 的 `gpu_index`/`gpu_index_physical` 保持 physical、`gpu_index_logical` 保持进程内 logical。`runner.py` 已有 remapping 不修改。修复部署及目标环境确认后，只执行既有 runner 链路并收集 manifest/receipt 证据。
  - **Evidence**：新增 `tests/test_gpu_index_mapping.py`；首轮旧实现上 3 项预期失败（helper 缺失、manifest 查询 index `3`、smoke 未共享 helper），独立复审后第二轮 3 项预期失败（空 mask 未拒绝、显式 logical 可绕过一致性检查、PowerShell `-c` 多行 argv 不安全），第三轮 4 项预期失败（禁用/垃圾/混合 mask 未拒绝、CUDA check 脚本空格路径未引用）。修复后相关 manifest/smoke 回归 `150 passed`；最终完整 CPU suite `910 passed, 1 failed, 4 errors`，唯一失败与 4 个 error 仍为既有本机 CUDA 13/CP936 下 Q0 CUDA fixture 编译问题。最终 diff 上 `compileall` PASS、Measurement Contract `37/37 PASS`、Canonical Raw boundary PASS、oracle/evaluator independence PASS，独立静态复审无剩余 Critical/Important；该阶段尚未运行目标平台 GPU smoke，后续 interrupted attempt 与本次 repair 状态见本节 checkpoint。
  - **PASS**：非 GPU 判据与目标平台真实 smoke 判据同时成立，且未修改 Measurement Contract 或 `exposedpath_v141` 计算语义。
  - **STOP**：任何真实 smoke 失败都保留现场并停止，不得用 mock 或局部测试替代；需要第二平台等价性时转 Gate 9。
  - **Dependency**：消费 `EP-G7-08`～`EP-G7-10` 的产物；是 Gate 7 verdict 的必要条件，必须最后执行。
  - **Unlock**：Gate 8 Engineering Pilot 获得唯一入口。

原编号处置（不得复用旧编号）：`EP-G7-01`→`EP-G7-08`；`EP-G7-02`→`EP-G7-08`；`EP-G7-03`→`EP-G7-09`；`EP-G7-04`→`EP-G7-09`；`EP-G7-05`→`EP-G7-10`；`EP-G7-06`→`EP-G7-10`（基线失败部分）＋`EP-G7-11`（全量验证部分）；`EP-G7-07`→`EP-G7-11`（其跨平台部分转入 Gate 9）。

### Gate 8：Engineering Pilot

**Gate verdict：`NOT_RUN`（未启动）。** Gate7 acceptance已完成，仅满足前序依赖；本轮不启动Gate8。下一阶段需独立规划/授权，不能把Gate7 Engineering/legacy通过当成EP-G8-02科学全链通过。

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
- `EP-ISSUE-18`（冻结发布副本，**本轮不修**）：`dist/exposedpath_v3_pilot_deploy/payload/analysis/exposed_accounting.py` 是被发布校验和钉住的旧副本，仍含 Python <3.12 不兼容 f-string；Gate 7 server smoke 不读取该副本。若未来复用 payload，必须另立任务并重签校验和，不得在本轮静默改写。

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
| `EP-ISSUE-19` | `7e67219` 的 Python <3.12 portability 修复及其验证已在本次同提交补记到唯一进度事实源，消除 handoff/SSOT 不一致 |
| `EP-ISSUE-20` | server smoke/manifest 的 physical/logical GPU index 混用已按 tests first 修复：共享纯 resolver，不用 `device_count()` 推断 physical identity，不修改 runner remapping |

## 7. 固定执行顺序与最近任务

当前顺序：`Gate 1 合同 → Gate 2 oracle → Gate 3 Canonical Raw → Gate 4 S → Gate 5 A/B/D/Signature → Gate 6 Q0 → Gate 7 runner/执行链对齐 → Gate 8 Engineering Pilot → Gate 9～12 正式实验准备 → Gate 13 N1/G1 → Gate 14 G2`。Gate 0 已完成封存。

**最近应执行的任务（按顺序）：**

1. Gate7已正式收口，保留唯一合格fresh与版本化closeout；不再要求EP-G7-11重跑/补证，旧attempt不拼接、不追认。
2. Gate8只记录为下一阶段待规划；独立明确真实workload Canonical→S→A/B→D的observation/validity与验收设计后再请求执行授权，本轮不启动。
3. 已完成的 `EP-G7-08`～`EP-G7-10` 不再产生新任务；如后续发现需要放宽其 fail-closed 判据，属于新计划项，不得直接修改。

（历史顺序，保留不删：`EP-G7-09` → `EP-G7-10` → `EP-G7-11`；`EP-G7-09` 已于 2026-09-21 完成。）

**Gate7验收：** EP-G7-11判据已同时成立并记录PASS；这不自动授权Gate8执行。

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
| 7.4 | 2026-09-21 | 完成 `EP-G7-10`：新增 `exposedpath/platform_adapter.py` 作为唯一 Python 侧平台边界（结构化 argv、无 shell、工具解析与 fail closed），runner/manifest 的 `nvidia-smi`／`git` 调用全部改经 adapter（无 schema/字段语义变化）；两项既有 smoke 失败定位为测试非封闭（裸 `powershell`＋依赖环境 `PATH` 解析 `python`）并修复，新增 PATH 独立性与 AST 结构回归 | EP-G7-10、EP-G7-05、EP-G7-06、EP-ISSUE-03 | Gate 7 保持 `NOT_RUN`（`EP-G7-11` 真实 GPU smoke 未执行）；不改变 Measurement Contract、`exposedpath_v141`、Gate 6 证据、数据资格或 Gate 7 PASS 判据 |
| 7.5 | 2026-09-22 | 补记 `7e67219` 的 Python <3.12 f-string portability 修复；在 EP-G7-11 smoke 前按 tests first 修复 physical/logical GPU index 混用：manifest 与 server smoke 共享纯 resolver，torch 查询使用 logical index，manifest/telemetry 保留 physical identity，runner remapping 零修改 | EP-G7-11、EP-ISSUE-18～20 | Gate 7 保持 `NOT_RUN`（未运行 GPU smoke）；不改变 Measurement Contract、S/A/B/D、Q0 oracle/evaluator、Gate 6 evidence、schema 或数据资格 |
| 7.6 | 2026-09-23 | EP-G7-11 fresh attempt 在 Pass0 后、Pass1/Nsight 启动边界遭 BugCheck 0x133 中断（根因未证实）；Trace Minimization / Acceptance Scope Audit 确认 Gate 7 为 integration smoke、完整真实 workload 科学链首属 Gate 8 EP-G8-02；同提交补记 bounded launcher repair：Engineering role、静态/跨 pass/telemetry fail-close、非零 BLOCKED、最小 CUDA+NVTX profile、独立 SQLite 后处理与观察身份留痕 | EP-G7-11、EP-G8-02 | Gate 7 仍 `NOT_RUN`，Gate 8 不启动，GPU smoke 未重新授权；旧/新 observation profile evidence 不可拼接；不改变 Measurement Contract、S/A/B/D、Q0 oracle/evaluator、Gate 6 冻结证据或 Formal 数据 |
| 7.7 | 2026-09-23 | 服务器报告 `799fb8d` fresh smoke 的最小 Nsight collection 成功、无本次 BugCheck，但即时 SQLite export 挂起且原 machine report 正确 `BLOCKED_BY_NSYS`；同 hash REP 副本离线 export/integrity/analyzer 通过，精确挂起根因仍未证明。测试先行实现有界 REP readiness、最多两次 180 秒独立 SQLite export、PID 定向结束、哈希/必需表字段/完整性校验、无覆盖 promotion、Analyzer 前校验、历史 machine report 防覆写与 attempt provenance；原 attempt 不追认 | EP-G7-11 | Gate 7 仍 `NOT_RUN`，Gate 8 不启动，新 GPU smoke 未授权；仅改变 Engineering 后处理可靠性与 fail-close，不改变 observation profile、Measurement Contract、S/A/B/D、Q0、Gate 6 evidence 或 Formal 数据 |
| 7.8 | 2026-09-23 | 后处理 Windows path/argv 二审新增真实 `Popen` + fake exporter 回归：含空格 exe/REP/SQLite 路径逐项传递，stdout/stderr 可追溯；生产实现无需修改。等待独立 bundle 部署、服务器静态验证及已有 REP 的新目录离线后处理验证，不运行 GPU smoke | EP-G7-11 | Gate 7 仍 `NOT_RUN`，Gate 8 不启动；原 `799fb8d` attempt 继续 `BLOCKED_BY_NSYS`，不改变 Measurement Contract、科学 analyzer、Q0 或 Gate 6 evidence |
| 7.9 | 2026-09-24 | 已部署 `5a37eb0` 的服务器 static validation 暴露 Windows venv launcher/fake exporter PID 分离；本地 venv 红测复现后，仅修复测试 fixture 使用直接 base interpreter，保留 PID 等值断言并检查 retry 前真实进程退出；生产 termination logic 不变 | EP-G7-11 | Engineering/static-validation 修复；Gate 7 仍 `NOT_RUN`，Gate 8 不启动，新 GPU smoke 未授权；旧 attempt 不追认 |
| 7.10 | 2026-09-24 | 接收用户回传的 `ecac542` 目标服务器静态验证：1/19/97 项定向通过，全量 981 passed、1 skipped（原因未知），全部命令 exit 0；fixture 阻塞解除，准备独立 REP 副本离线验证方案，未执行 | EP-G7-11 | 仅 Engineering 回执与文档更新；无新提交/部署需求，Gate 7 仍 NOT_RUN，Gate 8 不启动，旧 attempt 不追认 |
| 7.11 | 2026-09-24 | 接收用户回传的 ecac542 真实离线单次 export/analyzer 成功路径及 v2 清单补救结果；明确真实 timeout/kill/retry 未验证、legacy B 2/6 非 v1.4.1 语义验收；准备 fresh smoke 草案 | EP-G7-11 | 未取得完整服务器产物；仅文档更新，执行基线仍 ecac542；Gate7 NOT_RUN、Gate8 不启动，fresh smoke 未授权 |
| 7.12 | 2026-09-24 | 直接审计完整本地诊断包并复核哈希；执行真实 STEP6 validation block 复现 sync_coverage missing；发现 legacy 摘要/明细覆盖不同且 valid 映射未定义，依用户要求暂停实现、先明确合同 | EP-G7-11 | 仅文档更新，无新提交；不改变冻结语义或判据，fresh smoke 暂停，Gate7 NOT_RUN、Gate8 不启动 |
| 7.13 | 2026-09-24 | 明确 coverage 仅为证据缺口诊断；核对 physical UID、窗口缺失、legacy 与冻结 validity 不等价、union/跨 phase 口径及 null 约束；收紧全明细求和建议，集中待决验收映射与输入合同 | EP-G7-11 | 无运行代码/schema 改动；完整 request A 已实现但真实 workload 全链验收仍属 Gate8；Gate7 NOT_RUN、fresh smoke 暂停 |
| 7.14 | 2026-09-24 | 用户批准并版本化 gate7-legacy-analyzer/1；tests first 修复 launcher/validation consumer，严格 legacy-only 结构/身份/diagnostics gate，窗口 coverage 显式 unknown，拒绝历史 resume | EP-G7-11 | Gate7 工程验收规则显式修订、仅对后续新 attempt 有效；不修改冻结测量语义或旧 evidence；Gate7 NOT_RUN，GPU/Nsight 未授权，Gate8 不启动 |
| 7.15 | 2026-09-24 | 直接审计服务器 dced364 的33/130/1014测试及环境/23文件模型快照；确认 skip 和 revision unknown 的 Engineering 限制；旧实际 JSON 本地结构兼容、跨 commit 拒绝；只余 cl/marker/mask 最小补证 | EP-G7-11 | 仅文档更新、执行基线不变，无重跑测试/模型/Nsight；旧 attempt 不追认，Gate7 NOT_RUN，fresh smoke 未授权、Gate8不启动 |
| 7.16 | 2026-09-24 | fresh dced364身份链BLOCKED：修复Git adapter参数冲突、preflight GPU字段传递、prompt/manifest哈希混淆；增加模型加载前身份gate及实际producer回归 | EP-G7-11 | 工程修复，不放宽验收、不改冻结科学语义；旧attempt保持BLOCKED，Gate7 NOT_RUN；新GPU/Nsight未授权，Gate8不启动 |
| 7.17 | 2026-09-24 | 直接审计8d64f75服务器adapter/185定向/静态回执；关联已有环境、模型及补齐的compiler/marker快照；准备固定版本fresh草案 | EP-G7-11 | 仅文档、不提交/部署、不重跑测试；不将旧全量算作新版本验证；Gate7 NOT_RUN、旧attempt BLOCKED、新GPU/Nsight待授权、Gate8不启动 |
| 7.18 | 2026-09-24 | fresh8d64f75完整证据只读审计通过，新增gate7_closeout_v0_1；本次1040/1全量、两pass、身份/边界/后处理/legacy验收闭环；关闭EP-G7-11，Gate7 PASS | EP-G7-11 | 仅Engineering integration；保留原始diagnostics/unknown与legacy限制，不改冻结科学语义、不追认旧attempt；Gate8 NOT_RUN待规划、未启动 |
| 7.19 | 2026-09-24 | main统一入口；保全历史事故修改/审查笔记，移除五个worktree、核实冗余bundle/DOCX/缓存；单根固定checkout路径规范与GitHub同步 | 目录治理 | 根CPU-only1036 passed/5 skipped，原本机CUDA13编译失败另记；243证据文件不变，无代码语义修改，无服务器/GPU/Nsight执行；Gate7 PASS、Gate8 NOT_RUN |
