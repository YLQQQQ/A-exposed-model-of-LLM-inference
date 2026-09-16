# ExposedPath 科研进度清单

## 当前快照

- 清单版本：`4.9`
- 最近更新：`2026-09-16`
- 权威研究主体：`docs/current/ExposedPath_研究设计.docx`，文内版本 `v7.1`
- 当前执行依据：`docs/current/ExposedPath_实验协议.docx`，文内版本 `v2.1`；仍为 `Pre-Pilot`，不是 `Protocol Freeze`
- 当前研究阶段：`Engineering`
- 当前工作分支：`codex/v141-analyzer`
- 当前数据资格：历史 trace 仅限 `Prototype/Engineering`；尚无 `Pilot/Formal` 合格数据
- 当前最高优先级：`EP-G6-04`，将本轮新 bundle 增量更新到服务器并新建 r9，从 `Q0-STREAM-001` smoke 重新开始；已有 r1～r8 均保持不可变，不续跑、不覆盖且不执行 `git clean`
- 当前总体判断：Measurement Contract、Q0 独立标准答案设计、Canonical Raw v0.2、S v0.2 与 Gate 5 的 A/B/D/Exposure Signature 已通过离线/Engineering 审查；r8 已完成 21/21 native collection 和通用有效的源 Canonical，但在 `Q0-GRAPH-UNSUPPORTED-001` 故障注入处停止。原因是默认 Nsight graph-level tracing 不产生该故障所需的 node activity；独立服务器诊断确认 `--cuda-graph-trace=node` 后，现有 Canonical adapter 与 fault selector 可完成全链路。当前只对该 Graph case 增加采集参数，仍须由全新 r9 验证完整 Q0

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

**下一项：**Gate 2～5 已完成；继续执行 `EP-G6-01` 的受控 CUDA Q0 微程序与机器可读 manifest，并并行准备 `EP-G6-02` 的合成 trace/oracle 自动对照；真实 Q0 仍须等待 GPU。

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
- [x] `EP-G3-04` 新版 observation 定向测试通过。证据：最近记录为 `12 passed`，测试文件 `tests/test_v141_observation.py`。
- [x] `EP-G3-05` 冻结 Canonical Raw v0.2 的八类记录、结构化 NVTX、单 trace 相对纳秒时钟、source-row identity、lineage、诊断和研究资格字段。证据：`canonical_raw_schema_v0_2.json`、`canonical_raw_v0_2.md`。
- [x] `EP-G3-06` 实现 SQLite 到确定性 gzip JSONL bundle 的只读转换器；已有输出拒绝覆盖，临时目录成功后原子改名。
- [x] `EP-G3-07` 建立合成 SQLite、未知 schema、缺表/重复 correlation/dropped/逆序时间等测试，并完成三份历史 trace 回归。证据：`tests/test_v141_canonical_raw.py`、`engineering_evidence/canonical_raw_v0_2/historical_regression.json`。
- [x] `EP-G3-08` 建立下游边界静态检查，禁止未来 S/A/B 导入 sqlite3 或直接引用 Nsight 私有表名。当前下游模块尚未创建，测试同时用恶意样例证明检查器能拒绝越界访问。证据：`scripts/verify_canonical_raw_boundary.py`。
- [x] `EP-G3-09` 完成 Windows 真实 r2 的 Nsight `2026.2.1.210 / 3.25.0` adapter 审查：核心表继续必需，未发生相应活动时允许缺少 Memcpy/Memset/CUDA event 表并规范化为 0 条记录；可选表存在但字段不全仍 fail-closed；保留有符号 trace-relative 控制时间。r2 原 SQLite 哈希复核不变，唯一 invalid 为未映射的捕获结束同步。证据：`tests/test_v141_observation.py`、`tests/test_v141_canonical_raw.py` 及本轮只读诊断。
- [x] `EP-G3-10` 用真实 r3 固定 Q0 observation scope：只有 source manifest 与唯一结构化 full_request identity 完整匹配时，request 结束后的未映射同步才记为 `HARNESS_OUTSIDE_REQUEST` warning；目标 request 内、范围不唯一和非 Q0 trace 继续 fail closed。Canonical 不删除该行，也不伪造 runtime 映射。证据：r3 SQLite 只读诊断、`tests/test_v141_observation.py`、`tests/test_v141_canonical_raw.py`。

## Gate 4：S 同步语义层

**Gate verdict：`PASS`。** 只表示 S v0.2 的离线语义实现、版本化输出、合成 fixture、Q0 核心 expected 对照及历史 trace fail-closed 回归通过；不表示真实 CUDA/Nsight Q0 已执行。

- [x] `EP-G4-01` 实现 stream/device/context/event completion scope、可观察依赖图和每个 physical sync 的 `W(s)` 恢复；eventSyncId 要求唯一 record 且 event/context/device 一致。证据：`exposedpath_v141/sync_semantics.py`、`tests/test_v141_sync_semantics.py`。
- [x] `EP-G4-02` 实现 activity/sync ownership、submission evidence、semantic frontier、唯一 terminal、0 ns tie、validity 和原因优先级。
- [x] `EP-G4-03` 验证 completed-before 活动仍在 `W(s)`，并与冻结 Q0 核心 expected 交叉对照。
- [x] `EP-G4-04` 验证无依赖路径的跨流时间重叠不进入 `W(s)`，明确 post-sync 活动不造成提交歧义或未来 default-stream 污染，并确保缺失 correlation 的 invalid 不被提交歧义掩盖。
- [x] `EP-G4-05` 冻结 S schema 与 `analyze-s` CLI，并完成确定性 fixture、Raw→S 边界和历史 trace 回归。证据：`s_layer_schema_v0_2.json`、`s_layer_v0_2.md`、`tests/test_v141_s_bundle.py`、`engineering_evidence/s_layer_v0_2/historical_regression.json`。

Gate 6 合成 Q0 复核额外发现并修正一处 fail-closed 缺口：graph activity 缺少 node mapping 时，S 必须在判定 `GRAPH_MAPPING_UNSUPPORTED/INVALID` 的同时清空 `W(s)`、origin phase 与 cross-phase 派生状态，不能保留无法证明的依赖。

## Gate 5：A/B，再到 D/Exposure Signature

**Gate verdict：`PASS`。** 只表示 A/B 与纯派生层 v0.2 的离线语义实现、严格输入联结、版本化输出、合成测试、边界检查、历史 Engineering fail-closed 回归和完整分支独立复审通过；不表示真实 Q0、GPU 端到端链路、Pilot 或 Formal 已通过。旧 accounting 不能视为本 Gate 证据。

2026-09-14 完整分支复审与收尾修复后的验证：S 联结在 A/B 计算前拒绝 validity/wait-set/frontier/terminal/closure 不一致，以及 terminal 时间/clock 与 Canonical 冲突或晚于 sync return；`COMPLETION_BOUNDARY` 还必须与对应 Canonical physical sync 使用同一时钟域，合法 completion boundary 和非 valid 状态仍保留。相同 run/pass 中正长度重叠的 invocation 全部停止生成 A 窗口，包括具有可信 Full Request 但缺 phase 的相邻 invocation；半开相邻及无关请求不受污染。marker-only/无 NVTX 的零窗口输入产生 `WINDOW_DISCOVERY_INVALID`，bundle 与 CLI fail closed。Derived 只准直接导入 `ABBundleError`、`load_ab_bundle`（支持 alias），禁止模块 namespace、package-member 和其他 re-export。证据：`tests/test_v141_ab_inputs.py`、`tests/test_v141_ab_bundle.py`、`tests/test_v141_derived.py`；最终 Gate 5 定向 `171 passed`，全量 `541 passed, 2 failed`（仅 `test_dry_run`、`test_spaces` 基线）；合同、oracle 设计/独立性、下游边界、compile 与 diff 检查通过。独立复审结论为 `Approved`，未改变 Measurement Contract、Q0 或 Protocol Freeze。

- [x] `EP-G5-01` 冻结 A/B 输入联结、窗口、输出 schema，并实现面向 request/phase、互斥且保守的 A。输入适配证据：`exposedpath_v141/ab_inputs.py`、`tests/test_v141_ab_inputs.py`；设计与 schema 证据：`docs/superpowers/specs/2026-09-12-gate5-accounting-design.md`、`docs/v1_4_1/contracts/ab_schema_v0_2.json`、`docs/v1_4_1/contracts/derived_schema_v0_2.json`、`tests/test_v141_ab_schemas.py`；A 证据：`exposedpath_v141/a_accounting.py`、`tests/test_v141_a_accounting.py`。非窗口 structured marker 不创建或否定 A 窗口；其作为 worker API invocation ownership 证据时，必须由完整一致的 NVTX text payload 与缓存 identity 共同证明。
- [x] `EP-G5-02` 实现 A 的 residual、整数纳秒守恒和 invalid/ambiguous 传播。证据：`exposedpath_v141/intervals.py`、`exposedpath_v141/a_accounting.py`、`tests/test_v141_intervals.py`、`tests/test_v141_a_accounting.py`，以及真实 `ABInputs` discovery 到 A 多线程 API union 与伪造 worker marker fail-closed 的回归 `tests/test_v141_ab_inputs.py`（定向验证 `53 passed`）。
- [x] `EP-G5-03` 实现保持 per-sync provenance 的 B，禁止无依据跨同步求和。证据：`exposedpath_v141/b_provenance.py`、`tests/test_v141_b_provenance.py`；逐条投影 S 的 `W(s)`、terminal、validity 和 provenance，仅对 `B_VALID` 以 Canonical 半开区间 union 计算 hidden/exposed/terminal/return-tail，其他状态时长均为 `null`；定向验证 `29 passed`（含独立 Q0 oracle、overlapping wait-set union 和 completion-boundary terminal 回归）。
- [x] `EP-G5-04` 仅从冻结后的 A/B 派生 D。`derive-exposure` 通过既有严格 A/B loader 读取唯一输入，按冻结公式生成每个窗口的 `D_margin/D_score`；零分母严格输出 `null`。证据：`exposedpath_v141/derived.py`、`tests/test_v141_derived.py`。
- [x] `EP-G5-05` 仅从冻结后的 A/B 派生 Exposure Signature。输出冻结 A 向量/窗口比例及按 `(phase, sync_kind, sync_origin, callsite_id)` 的 B 状态 count、仅 `B_VALID` 数值的 median/nearest-rank p90、终端类型与离散分布；不输出 B total 或根因/瓶颈/速度上界标签。证据：`exposedpath_v141/derived.py`、`docs/v1_4_1/contracts/derived_schema_v0_2.json`、`tests/test_v141_derived.py`。
- [x] `EP-G5-06` 完成互斥、守恒、provenance、版本和 validity 传播的离线验收。A/B 及 Derived bundle 均严格校验 manifest/记录 schema、gzip 哈希/大小/计数与可选外部 lineage，使用确定性 `mtime=0` gzip 和临时目录原子改名；Derived loader 额外校验 terminal-kind 对 `B_VALID` 的精确 count 与每项统计分布的有效数值样本数。CLI 为 `analyze-ab` 和 `derive-exposure`；静态边界拒绝 Derived 导入 Canonical/S/A/B 计算模块、Raw/S 时间字段、SQLite 或 Nsight 表名。最终定向 Gate 5 测试 `171 passed`，合同/Oracle/边界/compile/diff 检查通过；全量 pytest 为 `541 passed, 2 failed`，仅保留基线 PowerShell smoke `tests/test_server_smoke_script.py::test_dry_run`、`::test_spaces` 两项失败。历史链路无合格 A window、S 446 invalid 且 B 446 `B_INVALID`；证据：`engineering_evidence/ab_v0_2/historical_regression.json`。完整分支独立复审及最后一处 completion-boundary 时钟域定向复核均为 `Approved`。

## Gate 6：Q0 资格验证

**Gate verdict：`FAIL`。** r2 至 r8 均为 Engineering 失败现场，不能升级为 Q0 证据。r8 已证明此前 invocation scope、PTDS、EMPTY 等问题不再阻断，并得到 21/21 通用有效源 Canonical；但 Graph 源 trace 缺少 node-level activity，无法构造预定义的 mapping-removal 负例。仍须由全新 r9 从 smoke 开始，Q0 状态保持 `NOT_RUN`。

- [x] `EP-G6-01` 实现受控 CUDA Q0 微程序和机器可读 manifest。23 个 oracle case 严格一一映射，其中 21 个具有 native CUDA seed，terminal tie 与 submission race 明确保持纯合成；缺 correlation、dropped records 与 graph mapping 缺失使用真实 seed 后受控 Canonical 故障注入。CUDA 13.0 在无 GPU 执行条件下成功编译，binary `--list-cases` 与 21 个 seed 集合一致，未知 case 在 CUDA 初始化前失败。证据：`q0/cuda/exposedpath_q0.cu`、`q0/execution_manifest_v0_2.json`、`tests/test_v141_q0_cuda_source.py`。
- [x] `EP-G6-02` 完成 GPU 前 Q0 执行准备：Windows/Linux 结构化 `nsys` argv、每 case source manifest、输入哈希、不可覆盖输出和 `PREPARED_NOT_EXECUTED/NOT_RUN` dry-run；23 个显式合成 Canonical profile 均经正式 S/A/B 与独立 evaluator 对照通过。observed 使用严格 schema，evaluator 静态禁止导入被测 S/A/B，错误字段、重复 identity、缺失/额外 case 和资格升级均 fail closed。证据：`exposedpath_v141/q0_execution.py`、`exposedpath_v141/q0_synthetic.py`、`exposedpath_v141/q0_evaluator.py`、`docs/v1_4_1/contracts/q0_observed_schema_v0_2.json`、`tests/test_v141_q0_execution.py`、`tests/test_v141_q0_synthetic.py`、`tests/test_v141_q0_evaluator.py`。
- [x] `EP-G6-02A` 完成 GPU 前集成验收。CUDA 13.0 编译和 21-seed 清单、Nsight 2026.1.1 Windows dry-run、23/23 合成对照、oracle/evaluator 独立性、Canonical 边界和 Python compileall 通过；Gate4/5/Q0 定向 `200 passed`，CUDA source `5 passed`，全仓 `570 passed, 2 failed`，仅为既有 PowerShell smoke 基线失败。证据：`engineering_evidence/q0_pre_gpu_v0_2/readiness_report.json`。
- [x] `EP-G6-02B` 补齐真实 Q0 执行适配。capture/显式 GPU 身份、单 case executor/receipt、三种受控 Canonical fault、真实 observed/evaluator、策略约束的 23-case Gate 聚合、CLI 与 Windows 服务器手册均已实现。活动标签必须经 `activity correlation -> launch API -> 同线程唯一 marker` 恢复；缺 correlation 故障只能使用注入前写入 lineage 的预写标签；真实 A/B 预期使用人工 wait-set/terminal 与实际区间独立重算。Q0 聚焦回归 `62 passed`、独立性与 compileall `PASS`；全仓 `590 passed, 2 failed`，仅为已登记的旧 PowerShell smoke 基线失败。证据：`exposedpath_v141/q0_collection.py`、`q0_faults.py`、`q0_real.py`、`q0_gate.py`、`docs/v1_4_1/gate6_windows_server_runbook.md`。
- [x] `EP-G6-02C` 修复首次 Windows 实跑暴露的执行适配问题：GPU UUID 比较兼容带/不带内部连字符；精确加入已审查的 Nsight 2026.2.1/3.25.0；增强同步映射诊断；明确 CUDA 12.4 使用 v143/MSVC 14.39；Q0 微程序在请求范围结束后、`cudaProfilerStop` 前显式排空受控设备工作。全仓非 GPU 回归 `602 passed`，边界、oracle 独立性和 compileall 通过；显式排空尚未经过 GPU 验证。
- [x] `EP-G6-02D` 修复真实 r3 揭示的 Q0 范围与下游合同错位：request 外未映射同步可贯穿 Canonical→S→B 且保持 invalid/null，不污染 A；Q0 单阶段微程序允许严格的 full_request+内嵌 decode 两窗口，普通 workload 仍要求 full_request/prefill/decode 三段；A 接受窗口外的有符号 trace-relative profiler API。真实 r3 输入哈希复核不变，本地只读链路为 inspect/Canonical 0、S/A-B 3、独立 evaluator 0/`REAL_CASE_PASS`；全仓 `615 passed`，Canonical 边界、oracle/evaluator 独立性、合同与 compileall 均通过。
- [x] `EP-G6-02E` 修复真实 r4 EMPTY 暴露的 lazy-export 适配：KERNEL 缺表只在白名单 schema、`lazy=true`、CUDA capture 存在、关键导出元数据唯一且无 kernel/graph launch API 证据时规范化为零条；request 内外的 launch 冲突、非 lazy、未知 schema、缺 CUDA capture、元数据重复/冲突和残缺表继续 fail closed。真实 `VALID_EMPTY` evaluator 改用本次 sync 实际区间重算 A residual，不再使用合成 30 ns 常量。本地只读 r4 EMPTY 链路为 inspect/Canonical 0、S/A-B 3、evaluator 0/`REAL_CASE_PASS`；r4 输入保持不可变。
- [x] `EP-G6-02F` 修复真实 r5 暴露的多线程 NVTX 范围错误：`Q0-DEFAULT-PTDS-001`、`Q0-MULTITHREAD-ORDERED-001`、`Q0-OVERLAPPING-HOST-SYNC-001` 均改为由 coordinator 创建唯一 `full_request + decode`，且范围从 worker 创建前持续到全部 worker join 后；worker 仅写立即结束的结构化 marker，避免包住 CUDA API 后与 activity/sync marker 形成多候选。原有 activity/sync/API/callsite identity 与 Q0 oracle 不变，analyzer 对重复 target request 继续 fail closed。r6 已验证 request 唯一性修复生效；该版用于保持 PTDS worker 生命周期的 query 轮询随后被 r6 证明不适合目标 Nsight observation stack，转由 `EP-G6-02G` 修复。
- [x] `EP-G6-02G` 修复真实 r6 暴露的 PTDS query 轮询副作用：删除 `cudaStreamQuery` 循环，在 worker 的 `K_OTHER_THREAD` 后只排入一次 `cudaLaunchHostFunc`，由 Host 条件变量等待该 stream-ordered callback 并在 coordinator request 内 join。该机制不新增 CUDA sync/query；另外两个同源多线程 case 经源码检查没有 query 轮询，保持原实现。analyzer、Q0 oracle 及既有 activity/sync/API/callsite 标签均不变。定向 observation/CUDA 测试 `48 passed`，CUDA source/编译测试 `14 passed`，全仓 `639 passed, 2 failed`（仍仅为既有 PowerShell smoke 基线）；r7 已越过 PTDS 并推进至 invocation-bleed，确认本问题不再阻断批量流程。
- [x] `EP-G6-02H` 修复真实 r7 暴露的 target scope 过滤错误：resolver 不再要求全 trace 只能有一个结构化 request，而是先按 `request_id + experiment/wmpc/run/run_role/pass/repeat + full_request` 完整目标 identity 过滤，再要求目标匹配数恰好为 1。prior 等非目标 request 可共存；零匹配和重复同 identity target 继续 fail closed。新增合成回归同时验证 prior+唯一 target、零目标、重复目标，以及 target 后 correlation 131 自动归为 request 外 warning；microbench、oracle 和既有 identity 均不修改。observation 定向测试 `36 passed`，全仓 `641 passed, 2 failed`（仍仅为既有 PowerShell smoke 基线）；合同 37/37、Canonical 边界、oracle 独立性和 compileall 通过。
- [x] `EP-G6-02I` 修复真实 r8 暴露的 Graph 采集前态缺失：仅 `Q0-GRAPH-UNSUPPORTED-001` 的结构化 Nsight argv 增加一次 `--cuda-graph-trace=node`，其余 20 个 native seed 保持原采集参数。microbench、oracle、analyzer/S、Canonical adapter/schema、fault 语义和既有 identity 均不修改；run manifest 与 receipt 继续记录实际 argv。新增 Windows/Linux 回归验证 Graph case 参数恰好出现一次且其余 native case 均不包含；Q0 定向与合同/边界测试通过，全仓为 `643 passed, 2 failed`，两项仍是既有 PowerShell smoke 基线。
- [x] `EP-G6-03` r4 在 EMPTY、r5 在重复 request、r6 在 PTDS query 轮询、r7 在 invocation scope resolver、r8 在 Graph fault 前态处均按 fail-fast 规则停止并保留现场。r1～r8 均不得覆盖或升级资格。
- [ ] `EP-G6-04`（等待 r9）用新 bundle 更新服务器代码后新建 r9，从 `Q0-STREAM-001` 单例完成 Raw→Canonical→S→A/B→real evaluator；单例通过后才批量运行其余 native seed。Graph case 的 run manifest 必须恰好包含一次 node tracing 参数，其他 case 必须不包含。
- [ ] `EP-G6-05`（未开始）输出唯一 Q0 gate 报告；任何必需用例未通过都不得判为 `PASS`。

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
- `EP-ISSUE-04`：本机无 GPU，但实验室 Windows 服务器已有可用 RTX 4090/6000 Ada。本地只能完成离线验证；Q0、跨平台 GPU smoke、Engineering Pilot 及后续实验的真实结论必须由服务器证据给出。
- `EP-ISSUE-05`（已解决）：使用校验过哈希的 LibreOffice 临时解包版本完成本地全页渲染；研究主体 40 页、实验协议 27 页均已检查。渲染器仅用于文档 QA，不改变研究 Gate。
- `EP-ISSUE-06`：S 层已对 event/wait 的 context/stream 活动查找建立索引，并缓存重复 scope 建图；event/default-stream 密集型大 trace 的规模性能尚未在真实 Engineering 数据上验收。影响：需在 Engineering Pilot 记录耗时与峰值内存；当前不改变 S 语义正确性或数据资格。
- `EP-ISSUE-07`：本机环境变量 `CL` 被配置为 MSVC 目录，但该名称会被 `cl.exe`/`nvcc` 解释为隐式编译参数，导致 CUDA 编译失败。Q0 编译入口只在子进程环境中移除 `CL/_CL_`，不修改用户系统环境；后续 GPU 平台资格检查仍需记录并复核实际编译环境。
- `EP-ISSUE-08`（已解决并保留历史）：r2 的 `Q0-STREAM-001` 在 request 结束后出现未映射 context sync；r2 保持原失败现场，未修改或升级资格。后续 r3 已证明新增显式排空本身具有唯一 runtime 映射。
- `EP-ISSUE-09`（已解决，待 r4 复验）：r3 的 request 后尾部同步 `correlationId=135` 无 runtime 候选。现以唯一 Q0 full_request identity 限定 observation scope，保留该 Raw/Canonical 记录并标为 `HARNESS_OUTSIDE_REQUEST` warning；因无 API 映射，只能称为与 teardown 时间一致，不能断言具体 API 来源。
- `EP-ISSUE-10`（已解决并经 r5 路径推进验证）：Nsight 2026.2.1 的 `lazy=true` SQLite 在零 kernel case 不创建 KERNEL 表，旧 observation 将其误判为核心缺表；真实 EMPTY evaluator 还错误沿用合成 trace 的 30 ns residual。现已用条件化 adapter 与真实区间 oracle 修复，并对 kernel/graph launch API 变体及关键导出元数据重复/冲突继续 fail closed；r4 保持失败现场。
- `EP-ISSUE-11`（已解决并经 r6 复验）：r5 的 PTDS worker 线程创建了与 coordinator 完全相同 identity 的 `full_request`，触发 `TARGET_REQUEST_NOT_UNIQUE`；同源 multithread/overlapping-sync 实现也有相同结构。r6 已确认 coordinator 唯一 request/decode 生效，不再出现 target request 唯一性错误。
- `EP-ISSUE-12`（已解决并经 r7 路径推进验证）：r6 中 PTDS worker 的 `cudaStreamQuery` 轮询产生 correlation 129、133～162 共 31 条 request 内 synchronization activity，但 Runtime 表无对应 API 行。microbench 改用一次 stream-ordered host callback 与 Host 条件变量；r7 已越过该 case，analyzer 未放宽映射规则。
- `EP-ISSUE-13`（已解决并经 r8 复验）：r7 invocation-bleed 的 prior 与 target request identity 不同且不重叠，旧 resolver 却因结构化 request 总数为 2 判定目标不唯一。现只对完整目标 identity 的匹配数执行唯一性 gate；r8 已完成 21/21 native source Canonical，确认该问题不再阻断。
- `EP-ISSUE-14`（代码已修复，待 r9 复验）：r8 默认 Nsight graph-level tracing 只产生 `GRAPH_TRACE`，没有 KERNEL node activity 或 `CUDA_GRAPH_NODE_EVENTS`，导致 Graph mapping-removal fault 零命中。独立服务器诊断确认仅增加 `--cuda-graph-trace=node` 后，真实 node mapping 可进入现有 Canonical 并被既有 selector 唯一移除。修复严格限定 Graph case，不放宽 fault 或 analyzer。

## 固定执行顺序与最近任务

当前顺序为：`Gate 1 合同 -> Gate 2 oracle -> Gate 3 Canonical Raw -> Gate 4 S -> Gate 5 A/B/D/Signature -> Gate 6 Q0 -> Gate 7 runner/跨平台 -> Gate 8 Engineering Pilot -> Gate 9~12 正式实验准备 -> Gate 13 N1/G1 -> Gate 14 G2`。

最近应执行的任务：

1. `EP-G6-04`：用新 bundle 更新服务器受跟踪代码，保留 r1～r8；核对 Graph case 独占且恰好一次 `--cuda-graph-trace=node`，然后新建 r9，仅采集 `Q0-STREAM-001`。
2. `EP-G6-04`：r9 单例依次完成 Raw→Canonical→S→A/B→real evaluator；若仍存在额外 sync、映射歧义或其他 invalid，保留现场并回到诊断，不运行其余 20 个 seed。
3. `EP-G6-04/05`：只有单例全链路通过后才批量采集其余 native seed、实施受控负例并聚合唯一 Q0 gate 报告。

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
| 1.9 | 2026-09-12 | Gate 5 Task 4 第一轮复审引入 CUDA API 的结构化 NVTX ownership gate，并覆盖外部线程、无线程、invalid-over-valid、双非空 wait-set union、正常 0 ns 窗口与运行时数值校验；其中把 ownership 与当前 phase/thread 绑定的过严规则已在 2.0 修正。 | EP-G5-01、EP-G5-02 | 不改变 Measurement Contract、Q0 或 Protocol Freeze；Gate 5 保持 `NOT_RUN`，当前无 Formal 数据，不产生失效；B、bundle、D/Signature 与 Gate 5 集成验证仍未完成 |
| 2.0 | 2026-09-12 | Gate 5 Task 4 第二轮复审澄清 API ownership 与 phase clipping：同 API 线程、完整 identity 且包含 API 的 Canonical structured request/phase/marker range 仅证明同一 invocation；它不定义 A 窗口。A 仍只由结构化 request/phase windows 定义，跨 phase API 由原子区间分别裁剪；允许同 invocation 的 worker-thread marker，拒绝冲突或不完整的 enclosing ownership。 | EP-G5-01、EP-G5-02 | 不改变 Measurement Contract、Q0 或 Protocol Freeze；Gate 5 保持 `NOT_RUN`，当前无 Formal 数据，不产生失效；B、bundle、D/Signature 与 Gate 5 集成验证仍未完成 |
| 2.1 | 2026-09-12 | Gate 5 Task 4 集成复审修正窗口发现：完整 structured 非窗口 kind（含 worker ownership marker）不参与 A window creation，也不否定同一 invocation 的 request/prefill/decode 三个有效窗口；request/phase 的文本伪造、字段缺失和边界冲突仍按原有规则 fail-closed。新增真实 ABInputs discovery 到 A 的多线程 query union 回归。 | EP-G5-01、EP-G5-02 | 不改变 Measurement Contract、Q0 或 Protocol Freeze；Gate 5 保持 `NOT_RUN`，当前无 Formal 数据，不产生失效；该检查仅为合成 Engineering 证据，B、bundle、D/Signature 与完整 Gate 5 集成仍未完成 |
| 2.2 | 2026-09-12 | Gate 5 Task 4 第二轮集成复审收紧 worker API ownership：A 在采用任一 structured request/phase/marker range 前重新解析其 NVTX text，并要求与缓存 identity 完整一致；缺前缀、解析/对象失败或字段冲突一律不是 ownership evidence。窗口发现继续忽略非窗口 marker，因此伪造 marker 不会否定正常三窗口，但其 API 片段 fail-closed 至 unattributed。 | EP-G5-01、EP-G5-02 | 不改变 Measurement Contract、Q0 或 Protocol Freeze；Gate 5 保持 `NOT_RUN`，当前无 Formal 数据，不产生失效；该检查仅为合成 Engineering 证据，B、bundle、D/Signature 与完整 Gate 5 集成仍未完成 |
| 2.3 | 2026-09-13 | 完成 Gate 5 Task 5 的 B 单同步 provenance：B 逐条投影 S 的 sync identity、wait-set、terminal、validity、origin 和 cross-phase 字段；仅在 `B_VALID` 时按 Canonical 活动区间 union 计算 hidden/exposed、terminal pre/overlap 与 return-tail，其他状态保持 null-only。输出不含跨同步 total/sum 接口；新增 Q0 oracle 独立 expected 的合成回归。 | EP-G5-03 | 不改变 Measurement Contract、Q0、Pilot 或 Protocol Freeze；Gate 5 保持 `NOT_RUN`，当前无 Formal 数据，不产生失效；下一步为 bundle/纯派生层与 Gate 5 集成验证 |
| 2.4 | 2026-09-13 | Approved review 后补齐两条 B 回归：同一有效 wait-set 的重叠活动按区间 union 而非 duration sum，及 `COMPLETION_BOUNDARY` terminal 的 activity timing 为 null、return-tail 仍按可观察 completion boundary 计算。现有实现已满足，未修改生产代码。 | EP-G5-03 | 不改变 Measurement Contract、Q0、Pilot 或 Protocol Freeze；Gate 5 保持 `NOT_RUN`，当前无 Formal 数据，不产生失效 |
| 2.5 | 2026-09-13 | 完成 Gate 5 A/B bundle 与 `analyze-ab` CLI：Canonical+S 先严格联结，A/B 只调用既有冻结计算模块；输出逐条 schema 校验、确定性 gzip、拒绝覆盖、临时目录原子改名，loader 校验 schema/hash/size/count 和可选外部 lineage。边界审计显式覆盖 S 与四个 A/B 下游模块，并拒绝 sqlite3、Nsight 私有表名和旧 accounting import。 | EP-G5-06、EP-G3-08 | 不改变 Measurement Contract、Q0、Pilot 或 Protocol Freeze；Gate 5 保持 `NOT_RUN`，当前无 Formal 数据，不产生失效；D/Signature 仍未实现。 |
| 2.6 | 2026-09-13 | Gate 5 Task 6 复审修正：A/B loader 在 schema 允许未来资格值时仍执行当前 Engineering 资格策略（`formal_evidence=false`、`q0_status=NOT_RUN`、`scope=A_B_LAYER_ONLY`），该策略只在 Gate 6 尚无独立哈希资格证明期间适用；外部 S lineage 额外逐项核对 sync registry version/SHA-256；静态边界检查覆盖 `from analysis import exposed_accounting` 及 alias，保留无关 `analysis` import。 | EP-G5-06、EP-G3-08 | 不改变 Measurement Contract、Q0、Pilot 或 Protocol Freeze；Gate 5 保持 `NOT_RUN`，当前无 Formal 数据，不产生失效；该 loader policy 不是对未来 Formal bundle 的永久否定。 |
| 2.7 | 2026-09-13 | 完成 Gate 5 Task 7：`derive-exposure` 仅消费已验证 A/B bundle，确定性、不可覆盖地输出 D 和 Exposure Signature；D 使用冻结三项 A 公式与零分母 null，Signature 只摘要 A 向量/比例和 B 状态、有效数值统计、终端类型/分布。派生 loader 复查 schema/hash/可选 A/B lineage、资格不升级，以及 terminal/distribution 的运行时 count 一致性；边界审计禁止其回读 Canonical/S 或 Raw/S 时间字段。 | EP-G5-04 至 EP-G5-06、EP-G3-08 | 不改变 Measurement Contract、Q0、Pilot 或 Protocol Freeze；Gate 5 仍为 `NOT_RUN`，当前无 Formal 数据，不产生失效；下一步是 Task 8 的历史 Engineering 回归、全量验证与独立复审。 |
| 2.8 | 2026-09-13 | 完成 Gate 5 Task 8 离线工程验证：以 `nsys export --lazy=false` 只读导出历史 `w01` trace，Raw SHA-256 前后相同；Canonical identity 保持 ambiguous，S 的 446 条 physical sync 均 invalid，A 无合格 window，B 一一投影为 446 条 `B_INVALID`，Q0 保持 `NOT_RUN`。完成 A/B 定向、合同、oracle/边界、compile 和全量 pytest；全量仅保留已记录的两项 PowerShell smoke 失败。 | EP-G5-06、EP-ISSUE-02、EP-ISSUE-03 | 不改变 Measurement Contract、Q0、Pilot 或 Protocol Freeze；历史结果仍仅为 Engineering，当前无 Formal 数据。Gate 5 明确保持 `NOT_RUN`，awaiting independent review；controller 在独立完整 diff 复审后决定 verdict。 |
| 2.9 | 2026-09-14 | 完整分支复审后的最终修复：严格校验 S 状态、wait-set/frontier 和 Canonical terminal 一致性；跨 invocation Full Request 正重叠按 identity fail closed；零窗口必须有质量 issue；Derived 改为精确 A/B loader/error 符号白名单。首轮 RED 30 项复现，另补缺 phase 的重叠请求 RED→GREEN；最终 Gate 5 `170 passed`，全量 `540 passed, 2 failed`（仅既有 PowerShell smoke）。 | EP-G5-01、EP-G5-03、EP-G5-05、EP-G5-06、EP-G3-08 | 不改变 Measurement Contract、Q0、Pilot 或 Protocol Freeze；未重新采集历史 trace 或产生 Formal 数据。Gate 5 保持 `NOT_RUN`，awaiting independent re-review。 |
| 3.0 | 2026-09-14 | 独立再复审确认三项问题闭合，并发现 completion boundary 尚未核对 Canonical sync 时钟域；新增反例先失败后修复，最终定向复核 `Approved`。Gate 5 新鲜验证为 `171 passed`，全量为 `541 passed, 2 failed`（仅既有 PowerShell smoke），据此将 Gate 5 判为 `PASS`，当前优先级切换至 Gate 6 的 GPU 前可执行工作。 | EP-G5-03、EP-G5-06、EP-G6-01、EP-G6-02 | 不改变 Measurement Contract、真实 Q0、Pilot 或 Protocol Freeze；历史数据仍仅为 Engineering，当前无 Formal 数据。 |
| 3.1 | 2026-09-14 | 冻结 Gate 6 GPU 前实施计划：23 个 oracle case 一一映射到原生 CUDA、真实 seed 后故障注入或纯合成 Canonical；新增 CUDA compile/list、Windows/Linux argv dry-run、正式 S/A/B 合成执行和独立 evaluator 的测试先行顺序。 | EP-G6-01、EP-G6-02 | 不改变 Measurement Contract 或 Gate 2 expected；Gate 6 继续 `BLOCKED`，不产生真实 Q0、Pilot 或 Formal 证据。 |
| 3.2 | 2026-09-14 | 完成 Q0 执行合同第一步：23 个 oracle case 与执行 case 严格一一对应，稳定 activity/sync/API label 不得改写；区分原生 CUDA、真实 seed 后 Canonical 故障注入和纯合成 Canonical，缺失/额外/重复 case、资格升级及策略字段冲突均 fail closed。 | EP-G6-01 | 不改变 Gate 2 expected；只是 Engineering 执行规划证据，Gate 6 与真实 Q0 保持 `BLOCKED/NOT_RUN`。 |
| 3.3 | 2026-09-14 | 完成受控 Q0 CUDA 微程序：覆盖 21 个 native seed，使用结构化 NVTX request/phase/activity/sync label，支持 stream、device、driver context、event/cross-stream、completed-before、empty、kernel+MemOp、default stream、multithread、overlapping host sync、phase spill、invocation bleed、graph、同步 D2H 与 query。CUDA 13.0 可在不运行 case 时编译并核对 seed 集合；本机污染性的 `CL` 环境变量只在编译子进程中移除。 | EP-G6-01、EP-ISSUE-07 | 仅证明源码可构建及身份注册一致，不证明 GPU 行为或 Nsight 可观测性；Gate 6 继续 `BLOCKED`，Q0 `NOT_RUN`。 |
| 3.4 | 2026-09-14 | 完成 Q0 跨平台 dry-run：Windows/Linux 均生成无 shell 引号拼接的 `nsys` argv、23 份 source manifest、逐文件哈希和不可覆盖 run manifest；21 个 native seed 有采集命令，2 个 synthetic-only case 明确无 GPU 命令。 | EP-G6-02 | dry-run 不执行 CUDA、Nsight 或 analyzer，不产生 `.nsys-rep`；Gate 6 继续 `BLOCKED`，Q0 `NOT_RUN`。 |
| 3.5 | 2026-09-14 | 完成 Gate 6 的 GPU 前合成对照：23 个显式 Canonical profile 进入正式 S/A/B，独立 evaluator 按冻结 oracle 对照且静态禁止导入被测模块；严格 observed schema 与重复/缺失/额外 identity 检查 fail closed。该回归发现并修正 graph mapping unsupported 时 S 仍保留未证明 wait-set 的缺口。 | EP-G4-01 至 EP-G4-05、EP-G6-02 | 合成结果仅为 Engineering/SYNTHETIC_ONLY，Q0 仍为 NOT_RUN，Gate 6 保持 BLOCKED；不改变 Measurement Contract、Protocol Freeze 或 Formal 数据。 |
| 3.6 | 2026-09-14 | 完成 Gate 6 GPU 前集成验收并固化机器可读证据：实际执行 CUDA 编译/list、Nsight Windows dry-run、23-case 合成 S/A/B 对照、静态边界与全仓非 GPU 回归。全仓为 `570 passed, 2 failed`，无新增失败。 | EP-G6-02A、EP-G6-03 | GPU 前准备判定 PASS 不等于 Gate 6 PASS；Q0 仍为 NOT_RUN，EP-G6-03 至 05 继续受 GPU 阻塞，不改变任何实验数据资格。 |
| 3.7 | 2026-09-14 | 真实执行复审发现 NVTX capture 缺少明确触发 range、真实 receipt/fault/observed/gate 尚未实现，因此在服务器采集前新增 EP-G6-02B。第一步改用 CUDA Profiler API 控制 capture，并冻结显式单 GPU 选择。 | EP-G6-02B、EP-G6-03 | 修正此前“可直接真实采集”的过早推断；不否定合成就绪证据，不改变 Q0 NOT_RUN、Gate6 BLOCKED 或任何 Formal 资格。 |
| 3.8 | 2026-09-14 | 完成真实 Q0 单 case executor 与不可覆盖 receipt：执行前检查工具和 source manifest 哈希，显式传递单 GPU 选择，采集环境身份、命令日志与 Raw 哈希；失败现场与成功收据严格分开。 | EP-G6-02B | 仅新增 Engineering 采集能力，尚无真实 GPU 产物；Q0 保持 NOT_RUN，Gate6 保持 BLOCKED。 |
| 3.9 | 2026-09-14 | 完成三种 Q0 Canonical 故障副本：只在新 bundle 中移除唯一 activity correlation、标记 dropped records 或移除唯一 graph node mapping，并重写确定性文件哈希和 lineage。 | EP-G6-02B | Raw 与源 Canonical 保持不可变；故障副本只用于 Q0 Engineering，不能升级数据资格。 |
| 4.0 | 2026-09-14 | 完成真实 Q0 observed/evaluator：稳定活动标签由 correlation、launch API 与唯一结构化 marker 联结；真实数值预期只使用 oracle 预写的 wait-set/terminal 标签和本次真实区间独立重算，避免拿合成固定纳秒值评判 GPU。缺区间、缺映射和歧义映射均 fail closed。 | EP-G6-02B | 单 case 通过仅标记 `REAL_CASE_PASS/REAL_CASE_ONLY`，Q0 仍为 `NOT_RUN`；尚未聚合全部必需 case，Gate 6 保持 `BLOCKED`。 |
| 4.1 | 2026-09-14 | 完成本地全部真实 Q0 执行缺口：故障注入前记录唯一目标/预写标签；单 case 证据绑定 receipt、Raw/source manifest、Canonical/S/A/B 哈希与环境；唯一聚合器强制 21 个真实 case、2 个合成边界例、单 run 和单环境，完整合成报告不得替代真实案例；补齐 CLI 与 Windows 服务器手册。 | EP-G6-02B、EP-G6-03 至 EP-G6-05 | 本地准备完成不等于真实 Q0 已运行。Gate 6 仍 `BLOCKED`、Q0 仍 `NOT_RUN`；下一步必须在固定 GPU/软件栈执行服务器采集。 |
| 4.2 | 2026-09-15 | 根据服务器已有旧 `YLQ_test` 环境补充部署与回传流程：旧项目/虚拟环境/历史结果保持不动；新版由 Git bundle 在同级目录 clone，使用轻量独立虚拟环境并记录 commit/dirty state；先跑单例再批量，最终回传完整 `$Out`。 | EP-G6-03 | 只完善 Engineering 执行与 provenance，不改变 Measurement Contract、Q0 verdict、Protocol Freeze 或 Formal 数据资格。 |
| 4.3 | 2026-09-15 | 基于服务器 r2 真实 SQLite 修复 Windows Q0 适配：精确支持 Nsight `2026.2.1.210 / 3.25.0`，区分核心表与按活动出现的可选表，保留有符号 trace-relative 时间，规范化 GPU UUID，并输出未唯一映射 sync 的完整诊断；r2 哈希保持不变且继续因捕获结束同步 fail-closed。微程序新增 request 外显式排空，手册改为原目录 bundle 更新、MSVC 14.39 和 r3 单例优先。全仓 `602 passed`。 | EP-G3-09、EP-G6-02C、EP-G6-03、EP-ISSUE-08 | 不改变 `W(s)`、terminal、A/B 等 Measurement Contract；这是 Protocol Freeze 前的 observation/执行适配修正。Q0 仍 `NOT_RUN`，r1/r2 不升级资格，当前无 Formal 数据。 |
| 4.4 | 2026-09-15 | 基于不可变 r3 修正 Q0 observation scope 和下游空映射处理：唯一目标 request 外同步保留为 harness warning，目标内与非 Q0 仍 fail closed；S/B 保留 invalid/null 行，A 不让无 ownership 的 request 外行污染窗口；Q0 单阶段窗口与微程序对齐，并允许窗口外有符号 profiler API。r3 本地只读重放得到 `REAL_CASE_PASS`，全仓 `615 passed`，手册切换为 r3 诊断后新建 r4。 | EP-G3-10、EP-G6-02D、EP-G6-03、EP-ISSUE-09 | 不改变 `W(s)`、terminal 或正式 workload 三阶段语义；属于 Engineering、Protocol Freeze 前合同澄清。r3 不升级为 Q0 证据，Gate 6 仍 `FAIL`、Q0 仍 `NOT_RUN`，当前无 Pilot/Formal 数据。 |
| 4.5 | 2026-09-15 | 基于不可变 r4 EMPTY 修正 lazy-export 零行 KERNEL 表与真实 `VALID_EMPTY` evaluator：缺表只在已审查 schema、lazy、CUDA capture、关键导出元数据唯一且无 kernel/graph launch evidence 时规范化为零条；其他情况继续 fail closed。独立复审后补齐 graph launch、`_ptsz`/`_ptds` API 变体、严格 lazy 取值与重复/冲突元数据反例。新导出统一 `--lazy=false`，服务器流程改为 r4 只读诊断后新建 r5。最终定向测试 `86 passed`、全量 pytest `632 passed`，合同 37/37、Canonical 边界、oracle 独立性和 compileall 均通过。 | EP-G6-02E、EP-G6-04、EP-ISSUE-10 | 不改变 Measurement Contract、Q0 oracle 的语义预期、S/A/B 定义或 Formal 资格；r4 不升级，Gate 6 仍 `FAIL`、Q0 仍 `NOT_RUN`。 |
| 4.6 | 2026-09-16 | 基于不可变 r5 PTDS 修复三个同源多线程 native seed 的重复 target request：coordinator 唯一持有 full_request/decode 并覆盖 worker GPU 工作，worker 仅写不包住 CUDA API 的短 marker；analyzer 唯一性规则保持 fail closed。旧 r5 只读复核仍 invalid 且哈希不变；服务器流程切换为 r5 诊断后新建 r6。全仓 `636 passed, 2 failed`，两项仍为既有 PowerShell smoke 基线。 | EP-G6-02F、EP-G6-03、EP-G6-04、EP-ISSUE-11 | 不改变 Measurement Contract、Q0 oracle、A/B 定义或 Formal 资格；r5 不升级，Gate 6 仍 `FAIL`、Q0 仍 `NOT_RUN`。 |
| 4.7 | 2026-09-16 | r6 已确认重复 request 修复和 request 外 harness 分类正确，同时发现 PTDS 的 `cudaStreamQuery` 轮询生成 31 条无 Runtime 映射的 request 内 synchronization。microbench 改为一次 stream-ordered host callback 加 Host 条件变量；analyzer 保持 fail closed，手册切换为 r6 只读诊断后新建 r7。全仓 `639 passed, 2 failed`，两项仍为既有 PowerShell smoke 基线。 | EP-G6-02G、EP-G6-03、EP-G6-04、EP-ISSUE-11、EP-ISSUE-12 | 不改变 Measurement Contract、Q0 oracle、既有稳定标签、A/B 定义或 Formal 资格；r6 不升级，Gate 6 仍 `FAIL`、Q0 仍 `NOT_RUN`。 |
| 4.8 | 2026-09-16 | r7 invocation-bleed 暴露 resolver 将全 trace request 总数误用为目标唯一性条件。现改为只对完整 target identity 的匹配数执行唯一性 gate；prior request 可共存，零目标与重复目标继续 fail closed，correlation 131 复用既有 request 外规则。手册切换为 r7 只读诊断后新建 r8。全仓 `641 passed, 2 failed`，两项仍为既有 PowerShell smoke 基线。 | EP-G6-02H、EP-G6-03、EP-G6-04、EP-ISSUE-13 | 不改变 Measurement Contract、Q0 oracle、microbench、既有 identity、A/B 定义或 Formal 资格；r7 不升级，Gate 6 仍 `FAIL`、Q0 仍 `NOT_RUN`。 |
| 4.9 | 2026-09-16 | r8 已完成 21/21 源 Canonical，但默认 graph-level tracing 无 node activity，导致 Graph mapping-removal fault 零命中。现仅为该 Graph case 增加 `--cuda-graph-trace=node`，并以跨平台命令回归保证其余 native case 不受影响；手册切换到全新 r9。全仓 `643 passed, 2 failed`，两项仍为既有 PowerShell smoke 基线。 | EP-G6-02I、EP-G6-03、EP-G6-04、EP-ISSUE-14 | 不改变 Measurement Contract、Q0 oracle、microbench、analyzer/S、Canonical 或 fault 语义；r8 不升级，Gate 6 仍 `FAIL`、Q0 仍 `NOT_RUN`，无 Pilot/Formal 数据受影响。 |
