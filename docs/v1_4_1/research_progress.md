# ExposedPath 科研进度清单

## 当前快照

- 清单版本：`0.2`
- 最近更新：`2026-09-10`
- 权威研究方案：ExposedPath `v1.4.1`
- 当前研究阶段：`Engineering`
- 当前工作分支：`codex/v141-analyzer`
- 当前数据资格：历史 trace 仅限 `Prototype/Engineering`；尚无 `Pilot/Formal` 合格数据
- 当前最高优先级：`EP-G1-02` 至 `EP-G1-09`，完成并审查 Measurement Contract v0.2
- 当前总体判断：GPU 前离线准备正在进行；`Q0`、Engineering Pilot、Protocol Freeze 和正式实验均未完成

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
- [x] `EP-FND-07` 形成研究设计主体 v7.0 Pre-Pilot 整合候选版。证据：`docs/v1_4_1/research_design_integrated_candidate_v7_0.md`、`docs/v1_4_1/revised_documents/ExposedPath_研究设计与论文证据框架_v7.0_Pre-Pilot整合候选版.docx`。
- [x] `EP-FND-08` 形成实验与分析协议 v2.1 Pre-Pilot 整合候选版。证据：`docs/v1_4_1/experiment_protocol_candidate_v2_1.md`、`docs/v1_4_1/revised_documents/ExposedPath_实验与分析协议_v2.1_Pre-Pilot整合候选版.docx`。
- [ ] `EP-FND-09`（受阻）完成两份候选 DOCX 的页面渲染与视觉验收。结构和关键语义检查已通过；当前主机未发现 Word 或 LibreOffice 渲染器，不能确认分页、表格跨页和文字截断。
- [ ] `EP-FND-10`（未开始）由用户审阅候选版，并在 Gate 1 通过后决定是否提升为新的权威研究设计/协议版本；在此之前 v1.4.1 仍为当前权威。

## Gate 0：封存旧 Prototype

**Gate verdict：`PASS`。** 只表示旧实现、Raw 身份、基线和限制已封存，不表示 v1.4.1 方法正确或 Q0 已通过。

- [x] `EP-G0-01` 固定旧 prototype 提交和标签。证据：标签 `prototype-windows-v0.1`，提交 `abab013c5483109007ab5a2a232438d46bbaf02b`。
- [x] `EP-G0-02` 固定三份历史 `.nsys-rep` 的文件大小和 SHA-256。证据：`docs/prototype_archive/raw_trace_manifest_v1.json`。
- [x] `EP-G0-03` 记录采集/读取环境、测试基线和已知失败。证据：`docs/prototype_archive/README.md`。
- [x] `EP-G0-04` 明确历史数据只能用于 Prototype/Engineering 回归，不能作为 Q0、Pilot 或 Formal 证据。

## Gate 1：Measurement Contract v0.2

**Gate verdict：`FAIL`。** observation 输入边界已有草案，但完整的 S、A/B、D/Signature、phase completion 和 validity 语义尚未冻结。

- [x] `EP-G1-01` 完成 `Nsight SQLite -> observation report` 合同草案 0.1。证据：`docs/v1_4_1/analyzer_contract_v0_1.md`。
- [ ] `EP-G1-02`（进行中）定义 Request、Prefill、Decode、首 Token 和后续 Token 的可观察完成边界。
- [ ] `EP-G1-03`（未开始）定义自然逐 Token 同步与 N1 人为同步干预的身份和隔离规则。
- [ ] `EP-G1-04`（未开始）冻结 stream、device/context、event synchronization 的 completion scope。
- [ ] `EP-G1-05`（未开始）冻结 `W(s)` 的提交顺序、context/stream/event、ownership 和排除规则。
- [ ] `EP-G1-06`（未开始）冻结 terminal 的选择规则、并列候选和时间容差。
- [ ] `EP-G1-07`（未开始）冻结 valid/ambiguous/invalid 判定、原因码和逐层传播规则。
- [ ] `EP-G1-08`（未开始）冻结 A/B 字段、互斥/守恒规则，以及 D/Exposure Signature 的纯派生规则。
- [ ] `EP-G1-09`（未开始）为每条合同规则建立测试映射并完成合同审查；无未决语义占位后才可将 Gate 改为 `PASS`。

**下一项：**先完成 `EP-G1-02`，再依次推进 `EP-G1-03` 至 `EP-G1-09`；不得跳到 S 或 A/B 实现。

## Gate 2：设计 Q0 独立标准答案

**Gate verdict：`NOT_RUN`。** 必须等待 Gate 1 的语义输入稳定，但用例目录可以在 Gate 1 后半段开始整理。

- [ ] `EP-G2-01`（未开始）建立受控 CUDA 用例目录：stream、device/context、event。
- [ ] `EP-G2-02`（未开始）覆盖提前完成、同步期间完成、跨流重叠但无依赖、terminal 唯一/并列、外部 ownership、缺失映射和 dropped records。
- [ ] `EP-G2-03`（未开始）为每个用例预先写定 `W(s)`、terminal、validity 和 A/B 关系。
- [ ] `EP-G2-04`（未开始）证明 oracle 不调用或复制 analyzer 的被测实现。
- [ ] `EP-G2-05`（未开始）审查正例、负例和含糊例完整性。

## Gate 3：Canonical Raw 层

**Gate verdict：`FAIL`。** observation gate 已有可运行基础，但唯一、版本化的 Canonical Raw schema 和转换器尚未建立。

- [x] `EP-G3-01` 建立独立新版入口 `python -m exposedpath_v141 inspect-sqlite`，未覆盖旧 analyzer。
- [x] `EP-G3-02` 对支持的 Nsight schema、必需表/字段、sync correlation 和 dropped-record 诊断执行 fail-closed 检查。
- [x] `EP-G3-03` 三份历史 trace 的 observation 回归稳定；因缺 source manifest 保持 `ambiguous`。证据：`engineering_evidence/observation_v0_1/`。
- [x] `EP-G3-04` 新版 observation 定向测试通过。证据：最近记录为 `8 passed`，测试文件 `tests/test_v141_observation.py`。
- [ ] `EP-G3-05`（受阻于 Gate 1）冻结 Canonical Raw schema、身份、时钟域、lineage 和诊断字段。
- [ ] `EP-G3-06`（未开始）实现 SQLite 到 Canonical Raw 的确定性转换器。
- [ ] `EP-G3-07`（未开始）建立合成 SQLite fixture、历史 trace 回归和 schema 版本拒绝测试。
- [ ] `EP-G3-08`（未开始）确保所有下游层只读取 Canonical Raw，不再直接查询 Nsight 表。

## Gate 4：S 同步语义层

**Gate verdict：`NOT_RUN`。** S 层尚未实现。

- [ ] `EP-G4-01`（受阻于 Gate 1、3）实现每个同步的 completion set 与 `W(s)` 恢复。
- [ ] `EP-G4-02`（受阻）实现 terminal 唯一性、并列候选、ownership 和 validity。
- [ ] `EP-G4-03`（受阻）验证提前完成但属于 completion set 的活动仍进入 `W(s)`。
- [ ] `EP-G4-04`（受阻）验证仅时间重叠而无依赖的活动不会进入 `W(s)`。
- [ ] `EP-G4-05`（受阻）完成三类同步的确定性 fixture 和语义不变量测试。

## Gate 5：A/B，再到 D/Exposure Signature

**Gate verdict：`NOT_RUN`。** 新语义的 A/B/D/Exposure Signature 尚未实现；旧 accounting 不能视为本 Gate 进度。

- [ ] `EP-G5-01`（受阻于 Gate 4）实现面向 request/phase、互斥且保守的 A。
- [ ] `EP-G5-02`（受阻）实现 A 的 residual、守恒容差和 invalid 传播。
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

- [ ] `EP-G7-01`（受阻于 Gate 1）设计并实现一致、可观察的 Token 就绪边界。
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
- `EP-ISSUE-03`：仓库全量测试最近记录为 `226 passed, 2 failed`；既有失败为 `tests/test_server_smoke_script.py::test_dry_run` 和 `test_spaces`。影响：跨平台执行层需单独修复或重新界定，但不应掩盖为新增 analyzer 失败。
- `EP-ISSUE-04`：当前无 GPU。影响：Q0 真实 trace、跨平台 GPU smoke、Engineering Pilot 及后续实验保持 `BLOCKED`；不影响 Gate 1 至 Gate 5 的离线设计和确定性测试工作。
- `EP-ISSUE-05`：当前主机未发现可用的 Word/LibreOffice DOCX 渲染器。影响：候选文档已通过 OOXML、结构和关键语义检查，但页面级视觉验收保持 `BLOCKED`；不影响 Measurement Contract 的文本设计。

## 固定执行顺序与最近任务

当前顺序为：`Gate 1 合同 -> Gate 2 oracle -> Gate 3 Canonical Raw -> Gate 4 S -> Gate 5 A/B/D/Signature -> Gate 6 Q0 -> Gate 7 runner/跨平台 -> Gate 8 Engineering Pilot -> Gate 9~12 正式实验准备 -> Gate 13 N1/G1 -> Gate 14 G2`。

最近应执行的五项任务：

1. `EP-G1-02`：确定 Token 就绪和各 phase 的可观察完成边界。
2. `EP-G1-03`、`EP-G1-04`：隔离自然/人为同步并冻结三类同步 scope。
3. `EP-G1-05` 至 `EP-G1-08`：完成 `W(s)`、terminal、validity、A/B/D/Signature 合同。
4. `EP-G1-09`：建立规则到测试的映射并审查 Gate 1。
5. Gate 1 通过后进入 `EP-G2-01`，不得提前用实现细节生成 Q0 标准答案。

## 计划调整记录

| 清单版本 | 日期 | 调整内容 | 影响编号 | 冻结协议/Formal 数据影响 |
|---|---|---|---|---|
| 0.1 | 2026-09-10 | 首次建立完整清单；纳入无 GPU 离线路线、自然逐 Token 同步边界和现有 observation 基础 | 全部 | 当前尚未 Protocol Freeze，也无 Formal 数据，不产生失效 |
| 0.2 | 2026-09-10 | 完成旧研究设计、WMPC、实验协议与 v1.4.1 的权威关系审计；新增两份 Pre-Pilot 整合候选版。协议修订底稿由此前假定的 WMPC v1.5 更正为实验协议 v2.0，WMPC 仅保留为候选配置来源；执行 Gate 顺序不变 | EP-FND-06 至 EP-FND-10 | 未改变冻结协议；当前无 Formal 数据，不产生失效 |
