# ExposedPath 科研进度清单

## 当前快照

- 清单版本：`1.7`
- 最近更新：`2026-09-12`
- 权威研究主体：`docs/current/ExposedPath_研究设计.docx`，文内版本 `v7.1`
- 当前执行依据：`docs/current/ExposedPath_实验协议.docx`，文内版本 `v2.1`；仍为 `Pre-Pilot`，不是 `Protocol Freeze`
- 当前研究阶段：`Engineering`
- 当前工作分支：`codex/v141-analyzer`
- 当前数据资格：历史 trace 仅限 `Prototype/Engineering`；尚无 `Pilot/Formal` 合格数据
- 当前最高优先级：`EP-G5-02`，A/B 与纯派生层 v0.2 机器 schema 已冻结，Canonical Raw + S 严格联结与 request/phase 窗口发现已完成，共享半开区间工具已实现；下一步实现 A 互斥墙钟记账
- 当前总体判断：Measurement Contract、Q0 独立标准答案设计、Canonical Raw v0.2 和 S v0.2 已通过离线/Engineering 审查；Gate 5 机器 schema 已完成第二轮复审修正，Task 3 共享整数半开区间原语已通过定向测试，但 A/B/D/Exposure Signature 代码与真实 Q0 尚未完成，Engineering Pilot、Protocol Freeze 和正式实验仍未开始

本文件是仓库内唯一的科研进度事实源。设计文档说明“应该怎样做”，本文件记录“现在做到哪里、证据在哪里、下一步是什么”。

## 使用与更新规则

1. 每项任务使用稳定编号；计划调整时不得重排或复用旧编号。取消的任务保留并标记“取消”，不得直接删除历史。
2. 任何实质性的研究定义、代码、测试、实验、证据资格或执行计划变化，都必须在同一次提交中更新本清单。
3. 完成项必须同时给出可复查证据。只有文档、代码或测试存在但尚未满足完成条件时，不得勾选完成。
4. Gate 只能使用 `PASS`、`FAIL`、`BLOCKED`、`NOT_RUN`。局部测试通过、mock 通过或无法运行 GPU 测试，不能写成 Gate `PASS`。
5. `Prototype`、`Engineering`、`Pilot`、`Formal` 数据资格分开记录；复制、改名或重新分析不能提升数据资格。
6. 计划改变时同步更新“计划调整记录”，说明原因、受影响编号、顺序变化，以及是否影响已冻结协议或 Formal 数据。
7. 每次结束实质性工作前，至少核对：完成状态、Gate verdict、证据、阻塞原因、当前最高优先级和下一项任务。

状态标记：`[x]` 表示完成；`[ ]` 后注明“进行中、未开始、受阻或取消”。Gate verdict 与任务勾选相互独立。

## 基础工作

- [x] `EP-FND-01` 建立仓库级中文协作规范和 ExposedPath 专用研究协议 skill。证据：`AGENTS.md`、`.agents/skills/exposedpath-research-protocol/`。
- [x] `EP-FND-02` 隔离新版 analyzer 工作。证据：分支 `codex/v141-analyzer`，独立 worktree `.worktrees/v141-analyzer`；旧入口未被替换。
- [x] `EP-FND-03` 记录核心术语和研究边界。证据：`CONTEXT.md`。
- [x] `EP-FND-04` 明确 GPU 前可完成范围和验收边界。证据：`docs/v1_4_1/pre_gpu_readiness_design_v0_1.md`。
- [x] `EP-FND-05` 验证新版 Nsight 能只读处理三份历史报告，并区分采集器与导出器版本。证据：`docs/prototype_archive/README.md`、`engineering_evidence/observation_v0_1/`。
- [x] `EP-FND-06` 审计并固定研究文档权威层级。证据：`docs/v1_4_1/document_consolidation_plan.md`；确认实验协议 v2.0 才是协议修订底稿，WMPC v1.5 仅作候选配置来源，原件均保留并记录 SHA-256。
- [x] `EP-FND-07` 形成研究设计主体 v7.0 Pre-Pilot 摘要候选版。该文件现仅保留为阶段性整合记录，已被完整母版修订版取代。
- [x] `EP-FND-08` 形成实验与分析协议 v2.1 Pre-Pilot 摘要候选版。该文件现仅保留为阶段性整合记录，已被完整母版修订版取代。
- [x] `EP-FND-09` 完成 v7.0/v2.1 初版 DOCX 的结构、关键方法语义与页面视觉验收。后续审计发现该检查未覆盖研究背景的完整论证链，v7.0 已被 v7.1 取代。
- [x] `EP-FND-10` 按用户明确要求将完整修订版提升为当前研究主体与 Pre-Pilot 执行依据。该升级不代表 Gate 1 或 Protocol Freeze 通过。
- [x] `EP-FND-11` 基于 v6.0 与 v2.0 母版完成第一轮整合，保留 36/39 张表、原章节、图片和横纵节。后续确认该轮主要覆盖方法语义，背景与研究立意仍不完整。
- [x] `EP-FND-12` 重写研究设计第一章，补齐 v1.4.1 的背景、立意、单 GPU 基础域、信息增量与成败判据；同步简化两份交付文件名并完成结构、语义和全页视觉验收。证据：`docs/current/ExposedPath_研究设计.docx`（40 页）、`docs/current/ExposedPath_实验协议.docx`（27 页）、`docs/v1_4_1/document_build/verify_full_revision.py` 与 `revision_lineage_full.json`。

## Gate 0：封存旧 Prototype

**Gate verdict：`PASS`。** 只表示旧实现、Raw 身份、基线和限制已封存，不表示 v1.4.1 方法正确或 Q0 已通过。

- [x] `EP-G0-01` 固定旧 prototype 提交和标签。证据：标签 `prototype-windows-v0.1`，提交 `abab013c5483109007ab5a2a232438d46bbaf02b`。
- [x] `EP-G0-02` 固定三份历史 `.nsys-rep` 的文件大小和 SHA-256。证据：`docs/prototype_archive/raw_trace_manifest_v1.json`。
- [x] `EP-G0-03` 记录采集/读取环境、测试基线和已知失败。证据：`docs/prototype_archive/README.md`。
- [x] `EP-G0-04` 明确历史数据只能用于 Prototype/Engineering 回归，不能作为 Q0、Pilot 或 Formal 证据。

## Gate 1：Measurement Contract v0.2

**Gate verdict：`PASS`。** 只表示 phase/Token、同步身份、completion scope、`W(s)`、terminal、validity、A/B 和派生规则已形成版本化、机器可检查且无未决语义占位的合同；不表示实现正确或 Q0 已通过。

- [x] `EP-G1-01` 完成 `Nsight SQLite -> observation report` 合同草案 0.1。证据：`docs/v1_4_1/analyzer_contract_v0_1.md`。
- [x] `EP-G1-02` 定义 Request、Prefill、Decode、首 Token 和后续 Token 的可观察完成边界。证据：`measurement_contract_v0_2.md` 第 3～4 节及机器合同 `phase_boundaries`。
- [x] `EP-G1-03` 定义自然逐 Token 同步、N1 人为同步与仅标记版本的互斥身份，并冻结 Pass0/Pass1 完成行为等价。证据：合同第 5 节及 `sync_identity`、`pass_parity`。
- [x] `EP-G1-04` 冻结 stream、device、context、event synchronization 的 completion scope；同步 copy 保持透明 unsupported。证据：合同第 6～7 节及 `sync_semantics_registry_v0_2.json`。
- [x] `EP-G1-05` 冻结 `W(s)` 的提交证明、同流/event/default-stream 传递依赖、ownership 和排除规则。证据：合同第 7 节及机器合同 `s_layer`。
- [x] `EP-G1-06` 冻结 terminal 的 semantic frontier 优先规则、并列候选及 0 ns 语义容差；Pilot 统计比较容差不得改变身份。证据：合同第 8 节及 `s_layer.terminal`。
- [x] `EP-G1-07` 冻结 `VALID_NONEMPTY/VALID_EMPTY/AMBIGUOUS/INVALID`、原因码优先级和 A/B fail-closed 传播。证据：合同第 9 节及 `s_layer.validity/reason_priority`。
- [x] `EP-G1-08` 冻结 A/B 字段、互斥/守恒、B per-sync 生命周期，以及 D/Exposure Signature 的纯派生规则。证据：合同第 10～12 节及机器合同 `a_layer/b_layer/derived`。
- [x] `EP-G1-09` 为 37 条合同规则建立 25 个验证案例映射并完成内部合同审查。证据：`measurement_contract_test_map_v0_2.json`、`tests/test_v141_contract.py`；`python -m exposedpath_v141 validate-contract` 输出 `37/37 (100%)` 与 `PASS`。

**下一项：**Gate 2～4 已完成；`EP-G5-01` 的输入联结与窗口发现、以及 Gate 5 Task 3 的共享区间原语已完成，继续执行 `EP-G5-02` 的 A 记账实现；A/B 只能读取 Canonical Raw 与 S 产物，不得回退到旧 accounting。

## Gate 2：设计 Q0 独立标准答案

**Gate verdict：`PASS`。** 只表示 23 个受控案例的 expected/oracle 已预先写定、可机器校验且独立于被测 analyzer；不表示 CUDA 微程序已实现、真实 trace 已采集或 Q0 已执行。

- [x] `EP-G2-01` 建立 stream、device/context、event 等受控用例定义目录。证据：`q0/oracle_cases_v0_2.json`。这里只是微程序设计输入，可执行 CUDA 微程序仍属于 `EP-G6-01`。
- [x] `EP-G2-02` 覆盖提前完成、同步期间完成、跨流重叠但无依赖、terminal 唯一/并列、外部 ownership、缺失映射和 dropped records。
- [x] `EP-G2-03` 为 23 个必需用例预先写定 `W(s)`、terminal、validity 和 A/B 关系。
- [x] `EP-G2-04` 建立 AST 独立性检查，禁止 oracle 导入旧 analyzer 或未来 Raw/S/A/B 实现，并禁止区间函数读取 dependency edges。证据：`scripts/verify_q0_oracle_independence.py`。
- [x] `EP-G2-05` 完成 7 个正例、7 个边界例、2 个含糊例、7 个负例及 25 个特性的覆盖审查。证据：`docs/v1_4_1/q0_oracle_design_v0_2.md`、`tests/test_v141_q0_oracle.py`；CLI 输出 `DESIGN_ONLY_PASS`。

## Gate 3：Canonical Raw 层

**Gate verdict：`PASS`。** 只表示唯一、版本化 Canonical Raw schema、只读转换器、identity/fail-closed 边界和三份历史 trace Engineering 回归通过；不表示 S/A/B 已实现或 Q0 已通过。

- [x] `EP-G3-01` 建立独立新版入口 `python -m exposedpath_v141 inspect-sqlite`，未覆盖旧 analyzer。
- [x] `EP-G3-02` 对支持的 Nsight schema、必需表/字段、sync correlation 和 dropped-record 诊断执行 fail-closed 检查。
- [x] `EP-G3-03` 三份历史 trace 的 observation 回归稳定；因缺 source manifest 保持 `ambiguous`。证据：`engineering_evidence/observation_v0_1/`。
- [x] `EP-G3-04` 新版 observation 定向测试通过。证据：最近记录为 `8 passed`，测试文件 `tests/test_v141_observation.py`。
- [x] `EP-G3-05` 冻结 Canonical Raw v0.2 的八类记录、结构化 NVTX、单 trace 相对纳秒时钟、source-row identity、lineage、诊断和研究资格字段。证据：`canonical_raw_schema_v0_2.json`、`canonical_raw_v0_2.md`。
- [x] `EP-G3-06` 实现 SQLite 到确定性 gzip JSONL bundle 的只读转换器；已有输出拒绝覆盖，临时目录成功后原子改名。
- [x] `EP-G3-07` 建立合成 SQLite、未知 schema、缺表/重复 correlation/dropped/逆序时间等测试，并完成三份历史 trace 回归。证据：`tests/test_v141_canonical_raw.py`、`engineering_evidence/canonical_raw_v0_2/historical_regression.json`。
- [x] `EP-G3-08` 建立下游边界静态检查，禁止未来 S/A/B 导入 sqlite3 或直接引用 Nsight 私有表名。当前下游模块尚未创建，测试同时用恶意样例证明检查器能拒绝越界访问。证据：`scripts/verify_canonical_raw_boundary.py`。

## Gate 4：S 同步语义层

**Gate verdict：`PASS`。** 只表示 S v0.2 的离线语义实现、版本化输出、合成 fixture、Q0 核心 expected 对照及历史 trace fail-closed 回归通过；不表示真实 CUDA/Nsight Q0 已执行。

- [x] `EP-G4-01` 实现 stream/device/context/event completion scope、可观察依赖图和每个 physical sync 的 `W(s)` 恢复；eventSyncId 要求唯一 record 且 event/context/device 一致。证据：`exposedpath_v141/sync_semantics.py`、`tests/test_v141_sync_semantics.py`。
- [x] `EP-G4-02` 实现 activity/sync ownership、submission evidence、semantic frontier、唯一 terminal、0 ns tie、validity 和原因优先级。
- [x] `EP-G4-03` 验证 completed-before 活动仍在 `W(s)`，并与冻结 Q0 核心 expected 交叉对照。
- [x] `EP-G4-04` 验证无依赖路径的跨流时间重叠不进入 `W(s)`，明确 post-sync 活动不造成提交歧义或未来 default-stream 污染，并确保缺失 correlation 的 invalid 不被提交歧义掩盖。
- [x] `EP-G4-05` 冻结 S schema 与 `analyze-s` CLI，并完成确定性 fixture、Raw→S 边界和历史 trace 回归。证据：`s_layer_schema_v0_2.json`、`s_layer_v0_2.md`、`tests/test_v141_s_bundle.py`、`engineering_evidence/s_layer_v0_2/historical_regression.json`。

## Gate 5：A/B，再到 D/Exposure Signature

**Gate verdict：`NOT_RUN`。** A/B 与纯派生层 v0.2 机器 schema 已冻结；新语义的 A/B/D/Exposure Signature 代码尚未实现，旧 accounting 不能视为本 Gate 进度。

- [x] `EP-G5-01` 冻结 A/B 输入联结、窗口、输出 schema，并实现面向 request/phase、互斥且保守的 A。输入适配证据：`exposedpath_v141/ab_inputs.py`、`tests/test_v141_ab_inputs.py`；设计与 schema 证据：`docs/superpowers/specs/2026-09-12-gate5-accounting-design.md`、`docs/v1_4_1/contracts/ab_schema_v0_2.json`、`docs/v1_4_1/contracts/derived_schema_v0_2.json`、`tests/test_v141_ab_schemas.py`；A 证据：`exposedpath_v141/a_accounting.py`、`tests/test_v141_a_accounting.py`。
- [x] `EP-G5-02` 实现 A 的 residual、整数纳秒守恒和 invalid/ambiguous 传播。证据：`exposedpath_v141/intervals.py`、`exposedpath_v141/a_accounting.py`、`tests/test_v141_intervals.py`、`tests/test_v141_a_accounting.py`（定向验证 `20 passed`）。
- [ ] `EP-G5-03`（受阻）实现保持 per-sync provenance 的 B，禁止无依据跨同步求和。
- [ ] `EP-G5-04`（受阻）仅从冻结后的 A/B 派生 D。
- [ ] `EP-G5-05`（受阻）仅从冻结后的 A/B 派生 Exposure Signature。
- [ ] `EP-G5-06`（受阻）完成互斥、守恒、provenance、版本和 validity 传播测试。

## Gate 6：Q0 资格验证

**Gate verdict：`BLOCKED`。** 前置 Gate 未完成，且当前没有可执行真实 CUDA/Nsight 受控 trace 的 GPU。

- [ ] `EP-G6-01`（未开始）实现受控 CUDA Q0 微程序和机器可读 manifest。
- [ ] `EP-G6-02`（未开始）在合成 trace 上对照独立 oracle。
- [ ] `EP-G6-03`（受阻于 GPU）在目标 observation stack 上采集真实受控 trace。
- [ ] `EP-G6-04`（受阻）真实 trace 全部必需用例对照 oracle，并验证 fail-closed。
- [ ] `EP-G6-05`（受阻）输出唯一 Q0 gate 报告；任何必需用例未通过都不得判为 `PASS`。

## Gate 7：Runner 与跨平台执行对齐

**Gate verdict：`BLOCKED`。** 旧 runner 可运行，但首 Token 与后续 Token 的完成语义不一致，且尚无双平台真实 GPU smoke 证据。

- [ ] `EP-G7-01`（等待前序 Gate）设计并实现一致、可观察的 Token 就绪边界。
- [ ] `EP-G7-02`（未开始）分离 G1 自然逐 Token 同步和 N1 人为干预模式。
- [ ] `EP-G7-03`（未开始）冻结 Pass0/Pass1 输入、身份、边界和执行策略一致性。
- [ ] `EP-G7-04`（未开始）补齐 manifest、环境、early EOS、排除、retry、attempt 和 data role 字段。
- [ ] `EP-G7-05`（未开始）隔离 Windows PowerShell、Linux shell、Nsight 和平台探测 adapter。
- [ ] `EP-G7-06`（未开始）通过非 GPU 的参数、命令构造、身份、schema 和错误路径测试。
- [ ] `EP-G7-07`（受阻于平台/GPU）在实际声称支持的 Windows/Linux 平台完成 GPU smoke，并证明合同等价。

## Gate 8：Engineering Pilot

**Gate verdict：`BLOCKED`。** 依赖 Q0 和 runner 对齐，并需要 GPU。

- [ ] `EP-G8-01`（受阻）运行最小端到端开发 workload。
- [ ] `EP-G8-02`（受阻）验证 benchmark -> runner -> Nsight -> Canonical Raw -> S -> A/B -> D/Signature 全链路。
- [ ] `EP-G8-03`（受阻）记录 trace coverage、存储规模、profiler overhead、运行可靠性和失败模式。
- [ ] `EP-G8-04`（受阻）形成 Engineering Pilot 报告；不得将结果用作正式科学结论。

## Gate 9：Formal 平台资格检查

**Gate verdict：`BLOCKED`。** 正式 GPU 平台尚未确定或接入。

- [ ] `EP-G9-01`（受阻）记录候选平台的 GPU、driver、CUDA、framework、Nsight、OS 和 launcher 身份。
- [ ] `EP-G9-02`（受阻）验证该平台满足冻结 observation contract 和 Q0 可观测性。
- [ ] `EP-G9-03`（受阻）检查 eager 行为及 G2 所需 compile/graph 可行性。
- [ ] `EP-G9-04`（受阻）给出平台 `PASS/FAIL/BLOCKED` 资格结论。

## Gate 10：可行域与 OOM 边界

**Gate verdict：`BLOCKED`。** 等待合格正式平台。

- [ ] `EP-G10-01`（受阻）预定义候选 input/output/batch 探测范围和停止规则。
- [ ] `EP-G10-02`（受阻）记录 OOM、early EOS、不稳定和 retry，不把 OOM 当科学重要性指标。
- [ ] `EP-G10-03`（受阻）确定跨配置比较所需的共同稳定范围和平台特定排除项。

## Gate 11：Pilot

**Gate verdict：`BLOCKED`。** 依赖合格平台和共同可行域。

- [ ] `EP-G11-01`（受阻）冻结前选择代表 workload 点。
- [ ] `EP-G11-02`（受阻）确定 repeat 数、profiler overhead 政策、质量阈值和运行规则。
- [ ] `EP-G11-03`（受阻）记录 Pilot 依据并保持其非 Formal 数据角色。
- [ ] `EP-G11-04`（受阻）形成 Protocol Freeze 所需输入清单。

## Gate 12：Protocol Freeze

**Gate verdict：`NOT_RUN`。** 只有前置 Gate 完成后才允许冻结。

- [ ] `EP-G12-01`（未开始）冻结代码提交、analyzer/schema、平台栈和协议版本。
- [ ] `EP-G12-02`（未开始）冻结 workload matrix、seed/input digest、repeat 和 Pass0/Pass1 配对。
- [ ] `EP-G12-03`（未开始）冻结排除规则、质量 gate、统计方法和绘图方案。
- [ ] `EP-G12-04`（未开始）冻结 N1/G1/G2 claim 评估规则。
- [ ] `EP-G12-05`（未开始）建立冻结后实质变更的新版协议及 Formal 数据失效规则。

## Gate 13：N1 与 G1

**Gate verdict：`NOT_RUN`。** 尚未进入 Formal 实验。

- [ ] `EP-G13-01`（未开始）按冻结协议执行 N1 受控同步干预。
- [ ] `EP-G13-02`（未开始）按冻结协议执行 G1 自然 workload sweep。
- [ ] `EP-G13-03`（未开始）验证 Information Gain，并如实报告 null、按比例和依赖 regime 的结果。
- [ ] `EP-G13-04`（未开始）审查 claim 是否仍保持单 GPU、请求内部 Host-device exposure 边界。

## Gate 14：G2

**Gate verdict：`NOT_RUN`。** 必须在 Correctness 和 Information Gain 证据成立后执行。

- [ ] `EP-G14-01`（未开始）按预定义规则选择真实优化 intervention 和 held-out 场景。
- [ ] `EP-G14-02`（未开始）执行 held-out decision-gain 评估。
- [ ] `EP-G14-03`（未开始）依据预定义标准确定最终 claim；若无额外决策价值，则删除预测/决策优越性 claim。

## 已知问题与风险

- `EP-ISSUE-01`：旧 runner 的首 Token 时间取在异步 argmax 提交后，但后续 EOS `.any()` 可能触发隐式同步，Token 完成边界不一致。影响：Gate 1、7；不得直接用于新版 phase 定义。
- `EP-ISSUE-02`：三份历史 trace 缺少 source manifest。影响：validity 必须保持 `ambiguous`，不能升级数据资格。
- `EP-ISSUE-03`：Gate 4 第三轮复审修正后的仓库全量测试为 `365 passed, 2 failed`；两项失败与工作前基线相同，仍为 `tests/test_server_smoke_script.py::test_dry_run` 和 `test_spaces`。影响：跨平台执行层需单独修复或重新界定，但不属于 Gate 2～4 新增失败。
- `EP-ISSUE-04`：当前无 GPU。影响：Q0 真实 trace、跨平台 GPU smoke、Engineering Pilot 及后续实验保持 `BLOCKED`；不影响 Gate 1 至 Gate 5 的离线设计和确定性测试工作。
- `EP-ISSUE-05`（已解决）：使用校验过哈希的 LibreOffice 临时解包版本完成本地全页渲染；研究主体 40 页、实验协议 27 页均已检查。渲染器仅用于文档 QA，不改变研究 Gate。
- `EP-ISSUE-06`：S 层已对 event/wait 的 context/stream 活动查找建立索引，并缓存重复 scope 建图；event/default-stream 密集型大 trace 的规模性能尚未在真实 Engineering 数据上验收。影响：需在 Engineering Pilot 记录耗时与峰值内存；当前不改变 S 语义正确性或数据资格。

## 固定执行顺序与最近任务

当前顺序为：`Gate 1 合同 -> Gate 2 oracle -> Gate 3 Canonical Raw -> Gate 4 S -> Gate 5 A/B/D/Signature -> Gate 6 Q0 -> Gate 7 runner/跨平台 -> Gate 8 Engineering Pilot -> Gate 9~12 正式实验准备 -> Gate 13 N1/G1 -> Gate 14 G2`。

最近应执行的五项任务：

1. `EP-G5-02`：基于已完成的共享半开区间原语，实现 A 的 request/phase 原子区间切分、优先级、互斥和守恒；invalid/ambiguous sync 归 unattributed。
2. `EP-G5-03`：实现 B 的单同步 hidden/exposed/terminal/return-tail，并从接口和汇总层禁止跨同步相加。
3. `EP-G5-04`：用 Q0 oracle 的 A/B 关系、重叠 sync 和 phase spill 案例进行离线对照。
4. `EP-G5-05`：完成 A/B 后再实现纯派生 D/Exposure Signature；不新增研究指标。
5. `EP-G5-06`：完成互斥、守恒、provenance、版本和 validity 传播测试。

## 计划调整记录

| 清单版本 | 日期 | 调整内容 | 影响编号 | 冻结协议/Formal 数据影响 |
|---|---|---|---|---|
| 0.1 | 2026-09-10 | 首次建立完整清单；纳入无 GPU 离线路线、自然逐 Token 同步边界和现有 observation 基础 | 全部 | 当前尚未 Protocol Freeze，也无 Formal 数据，不产生失效 |
| 0.2 | 2026-09-10 | 完成旧研究设计、WMPC、实验协议与 v1.4.1 的权威关系审计；新增两份 Pre-Pilot 整合候选版。协议修订底稿由此前假定的 WMPC v1.5 更正为实验协议 v2.0，WMPC 仅保留为候选配置来源；执行 Gate 顺序不变 | EP-FND-06 至 EP-FND-10 | 未改变冻结协议；当前无 Formal 数据，不产生失效 |
| 0.3 | 2026-09-10 | 基于两份完整 Word 母版逐章吸收 v1.4.1，完成结构/语义自动校验和 40/27 页视觉验收；摘要候选版降为历史整合记录，完整 v7.0 成为当前研究主体，v2.1 成为 Pre-Pilot 执行依据 | EP-FND-07 至 EP-FND-11、EP-ISSUE-05 | 未通过 Gate 1 或 Protocol Freeze；当前无 Formal 数据，不产生失效 |
| 0.4 | 2026-09-10 | 复核发现 v7.0 的自动检查偏重方法语义，第一章未完整吸收 v1.4.1 的背景论证。启动 v7.1 修订，并将两个当前入口简化为 `ExposedPath_研究设计.docx` 与 `ExposedPath_实验协议.docx` | EP-FND-09、EP-FND-11、EP-FND-12 | 不改变 Measurement Contract、Gate 或 Formal 数据资格 |
| 0.5 | 2026-09-11 | 完成 v7.1 背景与研究立意补齐、两份文档的简洁命名、结构/语义自动校验及 40/27 页全页视觉验收；移除封面标题装饰线并修正表格与章节分页。 | EP-FND-12、EP-ISSUE-05 | 不改变 Measurement Contract、Gate 或 Formal 数据资格；下一步仍为 EP-G1-02 |
| 0.6 | 2026-09-11 | 完成 Measurement Contract v0.2：冻结 Token/phase、自然与干预同步身份、三类 completion scope、提交证明、`W(s)`、terminal、validity、A/B 与纯派生规则；建立 37 条规则到 25 个验证案例的机器映射和合同校验命令。 | EP-G1-02 至 EP-G1-09 | Gate 1 内部合同审查 PASS；不改变 Q0、Pilot、Protocol Freeze 或 Formal 数据资格；下一步为 EP-G2-01 |
| 0.7 | 2026-09-11 | 完成 Q0 独立标准答案设计：23 个必需案例覆盖 25 个特性，预写 `W(s)`、terminal、validity 和 A/B 关系，并增加 AST 独立性检查及 `DESIGN_ONLY_PASS` CLI。 | EP-G2-01 至 EP-G2-05、EP-G3-05 | Gate 2 设计审查 PASS；真实 Q0 仍未运行，Gate 6 保持 BLOCKED；不改变 Pilot、Protocol Freeze 或 Formal 数据资格；下一步为 EP-G3-05 |
| 0.8 | 2026-09-11 | 完成 Canonical Raw v0.2：冻结八类事实记录与 identity/clock/lineage 合同，实现只读 gzip JSONL 转换、越层访问检查，并对三份历史 trace 完成 Engineering 回归与 Raw 哈希复核。 | EP-G3-05 至 EP-G3-08、EP-G4-01 至 EP-G4-05 | Gate 3 PASS；历史数据仍为 ambiguous Engineering 证据，真实 Q0 与 Gate 6 不变；下一步为 EP-G4-01 |
| 0.9 | 2026-09-11 | 完成 S v0.2：Canonical-only ownership、submission、completion graph、`W(s)`、terminal、validity、版本化输出与历史 trace fail-closed 回归；下一优先级切换为 A/B | EP-G4-01 至 EP-G4-05、EP-G5-01 | 未改变 Protocol Freeze；真实 Q0 未运行，当前无 Formal 数据，不产生失效 |
| 1.0 | 2026-09-11 | Gate 4 独立代码复审后修正三项语义缺陷：missing correlation 不再被降级、wait-event 末端节点不再漏 producer、外部 invocation 不再于建图前静默删除；同时补齐 default-stream 冲突/歧义、submission 审计信息、registry lineage 与重复 scope 建图缓存 | EP-G4-01 至 EP-G4-05 | 未改变 Measurement Contract 或 Protocol Freeze；原 Gate 4 实现结论经修正后重新验证，真实 Q0 状态不变 |
| 1.1 | 2026-09-11 | Gate 4 第二轮独立复审后要求 eventSyncId 唯一映射并校验 event/context/device；修正缺失 correlation 与提交顺序不明并存时的 invalid 传播，以及未来 default-stream overlap 对较早同步的污染；补充 event/wait 查找索引和 9 个回归案例 | EP-G4-01 至 EP-G4-05、EP-ISSUE-03、EP-ISSUE-06 | 未改变 Measurement Contract、Q0 状态或 Protocol Freeze；当前仍无 Formal 数据，不产生失效 |
| 1.2 | 2026-09-11 | Gate 4 第三轮独立复审发现缺失 correlation 的强 invalid 在 event 捕获和 legacy default-stream 路径仍可能被顺序歧义覆盖；补齐三条路径的统一 fail-closed 传播和 3 个回归案例 | EP-G4-02、EP-G4-05、EP-ISSUE-03 | 未改变 Measurement Contract、Q0 状态或 Protocol Freeze；当前仍无 Formal 数据，不产生失效 |
| 1.3 | 2026-09-12 | Gate 4 独立复审无 Critical/Important 后正式进入 Gate 5；书面冻结 A/B 双输入联结、窗口发现、原子区间分类、B 状态投影、D/Signature 纯派生及无 GPU 验证方法，等待用户复核 | EP-G5-01 至 EP-G5-06 | 不改变 Measurement Contract、Q0 或 Protocol Freeze；仅形成 Gate 5 设计，尚未实现或产生新实验数据 |
| 1.4 | 2026-09-12 | 冻结 A/B 与纯派生层 v0.2 JSON Schema：A 记录携带整数纳秒守恒审计字段，B 严格保持 per-sync 冻结字段并对非 `B_VALID` 时长执行 null-only，D/Signature 仅接受 A/B lineage、向量、比例、状态 count 与非加和统计；后续代码实现顺序不变 | EP-G5-01 至 EP-G5-06 | 不改变 Measurement Contract、Q0 或 Protocol Freeze；Gate 5 保持 `NOT_RUN`，当前无 Formal 数据，不产生失效 |
| 1.5 | 2026-09-12 | 修复 Gate 5 schema 首轮复审的重要问题：按 terminal kind/status 强制有效 identity、clock 与 timing nullability；当 `B_VALID>0` 时强制 hidden/exposed/return-tail 具有非空统计和数值分布，并将 terminal-kind count 收紧为固定键对象；跨字段 count 求和仍由后续 Task 7 运行时校验 | EP-G5-01、EP-G5-03、EP-G5-05、EP-G5-06 | 不改变 Measurement Contract、Q0 或 Protocol Freeze；Gate 5 保持 `NOT_RUN`，当前无 Formal 数据，不产生失效 |
| 1.6 | 2026-09-12 | 修复 Gate 5 schema 第二轮复审的重要问题：`B_VALID>0` 时至少一个 terminal kind count 为正；`ACTIVITY>0` 时 terminal pre/overlap 的 median、p90 与数值分布必须非空；精确 count 求和仍由后续 Task 7 运行时校验 | EP-G5-01、EP-G5-05、EP-G5-06 | 不改变 Measurement Contract、Q0 或 Protocol Freeze；Gate 5 保持 `NOT_RUN`，当前无 Formal 数据，不产生失效 |
| 1.7 | 2026-09-12 | 完成 Gate 5 Task 3 共享整数半开区间原语：交、裁剪、相邻/重叠 union、union 长度和原子切分；覆盖空区间、逆序/负时间拒绝、重复与确定性排序。A/B 研究语义与冻结合同未改变。 | EP-G5-02 | 不改变 Measurement Contract、Q0 或 Protocol Freeze；Gate 5 保持 `NOT_RUN`，当前无 Formal 数据，不产生失效；下一步为 A 记账实现与测试 |
| 1.8 | 2026-09-12 | 完成 Gate 5 Task 4 的 A 墙钟记账：按窗口/API/sync/`W(s)` 边界原子切分，以固定优先级互斥分配顶层与二级字段；全局质量失败、局部 invalid/ambiguous sync、未知 API 语义及未知 wait activity kind 均 fail-closed 到 unattributed。加入手算 100 ns、API union/冲突、重叠 sync、phase clipping 与 0 ns Decode 定向测试。 | EP-G5-01、EP-G5-02 | 不改变 Measurement Contract、Q0 或 Protocol Freeze；Gate 5 保持 `NOT_RUN`，当前无 Formal 数据，不产生失效；下一步为 B provenance、D/Signature 与 Gate 5 集成验证 |
