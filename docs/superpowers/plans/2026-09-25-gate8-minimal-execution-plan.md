# Gate8 最小执行计划 v0.1

## 7.46 当前覆盖：本地来源fixture，单次profile仍未授权

[来源对齐§11](../../v1_4_1/gate8_eager_source_alignment_v0_1.md)记录plan/result0.1、
诊断task0.2与旧loader0.1的显式区分；两task/两request/four-token15仅验证来源诊断
producer。定向88项、全量1345 passed/5 skipped（原CUDA编译项）及静态检查通过，
只读review无剩余重要问题；不等于目标运行或Q0资格。
唯一下一项外部决策是§11.1精确backtrace+sample+ctxsw的单次风险授权；不自动部署、
不打开profile，不以200Hz或短程序保证无BugCheck。服务器仍f5edc64；Gate7 PASS、
新Q0/Gate8 NOT_RUN。以下7.45及更早记录是历史，不是并行待执行任务。

## 7.45 当前：静态路线结束，Engineering来源观察单项审查

PE原件已直接核清单/身份，候选符号无法代替实际调用绑定，停止静态索包。
[来源对齐§10](../../v1_4_1/gate8_eager_source_alignment_v0_1.md)固定一次小task/
两request来源诊断及独立token预期；不是Qwen性能或Q0验收。UNKNOWN可启动诊断，
不成为科学放行。目标文档说明CUDA backtrace要求sample与ctxsw，不能与原最小profile
混称相同观测；精确参数、开销和历史系统风险已交协调先审，未执行/部署或改业务代码。
Gate7 PASS，新Q0/Gate8 NOT_RUN。

## 7.44 当前停止点：必要调用点映射完成，外部候选有界

[来源对齐§9](../../v1_4_1/gate8_eager_source_alignment_v0_1.md)已把影响目标W的
setup worker、warmup/model、token copy/sync、原drain和传入event/default边逐项列明。
条件性单流等价不等于目标事实；worker历史反例证明即使A相同/已有drain，B完整W仍可能不同。
本地不再增诊断版本；下一唯一候选是授权后对已hash两DLL的相关静态调用点做一次核查。
缺符号/只有imports即结束静态路线，不追加安装搜索；如需目标callchain观察则另列单项方案。
本轮没有执行服务器/采集或改变S准入，Gate7 PASS、新Q0/Gate8 NOT_RUN。

## 7.43 当前：本地load-task观察收口；不部署

已将7.42接点落实到显式opt-in producer0.4/load-task0.1及独立文件读取。
这是HOST_JOB_ONLY来源事实，不是S ownership；旧file-chain0.5拒绝新receipt，
不能丢弃load_tasks再降级。失败fallback保留两个attempt，封存不等待未结束任务。
本地确定性验证与限制见[来源对齐§8](../../v1_4_1/gate8_eager_source_alignment_v0_1.md)。
下一项最小工作是把必要调用点的mode/lifetime证明义务与已有Raw关联明确对齐；
没有证明前不扩S准入、不运行模型碰运气。安装补证已完成，不重复向服务器索取。
服务器仍固定f5edc64；Gate7 PASS，新Q0/Gate8 NOT_RUN。

## 7.42 当前：安装原件已审计，服务器等待；本地task来源接口

一次来源快照已到解压原件，外14/内9/总15文件的hash与精确集合直接核验通过。
ZIP本体未到，不宣称CRC/ZIP hash本地验证、不要求重传。目标安装的device_map、
worker/materialize/Future和非等待shutdown已按实际源码核对，详见
[来源对齐§7](../../v1_4_1/gate8_eager_source_alignment_v0_1.md)。
下一项由主窗口本地实现显式attempt/task观察及实际文件链确定性反例；不加等待/同步、
不改变异步加载/流/fallback，不凭主线程范围认领worker。default-mode/lifetime缺口
与task观察分开，静态hash不授S准入。无需用户服务器下一操作，不重搜安装/旧controlled。
Gate7 PASS，新Q0/Gate8 NOT_RUN；下面7.41外部补证待办已完成，不能再次执行。

## 7.41 当前停止点：一次目标安装来源补证，不部署/采集

已核精确Torch2.6与Transformers5.17第一方源码；现回传没有目标包相关源码字节。
loader worker只在已消费Future上等待，最终pool shutdown不等待全部任务，不能以
源码或主线程stage认领历史worker/推断default-mode。详见[来源对齐§4～5](../../v1_4_1/gate8_eager_source_alignment_v0_1.md)。
下一项唯一外部动作：协调审查一次只读安装快照命令后，由用户用现固定checkout的
`.venv -I -S`运行单一工具副本，回传10个白名单文件的身份（8源码+2DLL仅hash）、
两包有限metadata及操作回执。无GPU/Nsight/import Torch/部署，无环境dump/全盘搜索。
本地主窗口随后核对来源，再完成合同内必要scope接口；缺证据不猜测、不删UNKNOWN。
本地工具及确定性测试完成不等于descriptor资格或模型验收；服务器仍f5edc64，
Gate7 PASS、新Q0/Gate8 NOT_RUN。无需重复旧controlled或全量服务器检查。

## 7.40 当前：eager source 接线与明确的剩余资格边界

[来源对齐0.1](../../v1_4_1/gate8_eager_source_alignment_v0_1.md)记录真实历史Raw及第一方
torch/CUDA核查；本地显式model_setup→stage producer/input0.3→Canonical诊断→file-chain0.5
已接通，保持HOST_CALL_ONLY、worker/default/lifetime UNKNOWN。真实模型归属未就绪，
stage不供S/Derived消费；现drain只改已登记ABI别名匹配，不改同步或选流。
下一项仍由主窗口本地把目标torch/default/worker来源descriptor及必要前驱/可证无关scope
闭合起来；确需目标资料时只交付一次有界只读补证方案，不重复全capture调查、不重采旧controlled。
本地接口测试不是资格；服务器f5edc64不更新，GPU/Nsight未授权，新Q0/Gate8 NOT_RUN。
下方7.37/7.38的等待裁决、旧下一步是历史；7.39已批准，不重复请求普通工程授权。

## 7.39当前覆盖（2026-09-27）

用户已批准7.38 closed-prior方向；[amendment0.1](../../v1_4_1/gate8_closed_prior_amendment_v0_1.md)
及显式S0.3/A-B0.4的本地实现正在收口。保留完整物理W、原owner、A窗口裁剪及B历史进度，
不再等待同一语义重复审批。drain仅观察现有调用，实际scope/clock/source/失败路径严格核验。
Derived不支持新版本而继续拒绝；服务器f5edc64不更新，新Q0/Gate8 NOT_RUN。

本版本仅连续producer-owned非default窄域确定性验证，未证明真实torch默认流/初始化/
warmup来源。因此下一项由主窗口本地完成最小source映射审查：区分目标必要前驱与
可证无关活动，补实际owner/lifetime承载方案；不能将当前全inventory闭合限制写成
Route A全capture门，也不换stream、补造owner或删W。完成接口/来源可行性后才准备
新增路径的目标机两request受控资格方案。用户服务器当前无操作、无新采集授权。
下方7.38及更早段落是历史计划，未完成的资格项继续保留稳定编号。

## 7.38当前最小推进（2026-09-26，替代下方历史待办）

固定capture07625b7、分析f5edc64的受控计算原件已审计，B phase修复关闭。
它证明此独立stream构造的接口/边界及具体A/B计算，不是完整新版Q0资格、模型支持
或Gate8 PASS。服务器等待；本轮不部署、不采集、不要求再传话确认普通工程步骤。
详细证据见[实物审计](../../v1_4_1/gate8_controlled_optional_tables_audit_v0_1.md)。

### 最少剩余工作及负责人

| 顺序 | 主窗口可直接做的本地工作 | 所需证据/停止条件 |
|---|---|---|
| 1 新版资格影响表 | 沿用23-case独立oracle与旧结果，只补改变接口的资格映射；当前STREAM两request/D1/device/phase计算列为已取得窄Engineering证据，不修改旧qualification | signed表示、D2、文件hash和phase序列化仅回归；未变W(s)/A/B公式复用历史结论。未证明的API族不授资格，不默认21次全重采 |
| 2 必要反例 | 优先复用现有局部correlation缺失、未知影响、混run/clock、已完成前驱、无关流测试；若对真实Raw作故障注入，只在新诊断副本中标注注入及来源 | 当前真实controlled checker对破坏闭合构造的输入应拒绝，不强迫其输出partial A；局部unknown已有独立合成文件链证据，不能冒称真实collector故障验证 |
| 3 模型入口接线 | 列出真实runner→D1 producer落盘→新receipt/双pass的缺口；复用Gate7 pre-model身份门、固定model/prompt和Pass0/1规则，不改自然completion | 现controlled native成功不能代替torch模型API universe、warmup依赖范围或model receipt。新入口只能在下面epoch语义确定后完成适用域准入，不用新stream掩盖问题 |
| 4 有界资格/模型验证 | 本地实现及独立预期收口后，才给用户一次最小受控补证/单模型计划；允许复用环境/模型内容来源，但新执行固定commit | 只补所声明路径受影响接口；新Q0范围报告经审查后才进入真实模型。GPU/Nsight须另授权；失败保留、不自动retry |

**当前唯一优先研究裁决：closed-prior ownership准入，而非截断W(s)。**
详见[共享stream裁决稿0.2](../../v1_4_1/gate8_controlled_bridge_v0_1.md)。
7.37提案把旧request排除后给出`W={B}/hidden5`，现明确撤回该方向；未曾实现。
新推荐保留完整物理前缀、原owner及B进度，仅对有原始drain闭合证据的前一request
增加版本化S ownership准入；A继续按窗口裁剪，不把旧进度解释为当前request贡献。
同样的旧活动[0,20)、新B[40,50)、sync[45,60)例，证据齐全时提案应为
`W={旧活动,B}/hidden25/exposed5/tail10`，sync内A_wait5/residual10。
缺drain、未决event/外部ownership、clock/lifetime冲突仍拒绝；详稿含五类独立预期。
现runner已有窗前drain，首先补其非同步身份绑定，不增加新同步或改变自然行为。
此处仅待批语义设计，现代码/冻结合同保持原样。服务器无操作。

**Derived不是此刻必须放开的门。** 现五条范围外B_INVALID保留，不删除全B检查。
后续若要发布逐request D/Signature，需版本化规定：如何凭稳定identity及依赖闭合
证明哪些B属于目标窗、哪些仅外部诊断、未知影响如何向窗口传播；不能仅按时间不重叠
过滤。目前先完成A/B正确性资格，保留记账差值的有限解释。非零unknown整窗机制发布
仍按RouteA amendment等待Pilot质量门，不在本次指定百分比。

无需新增全capture厂商认证、全面扫描、第二平台或G2；它们不成为上述局部工作的前置。
Gate7历史PASS；新版Q0/Gate8 NOT_RUN。后续普通工程由主窗口推进，服务器当前无操作。

**7.28最新覆盖（2026-09-26）：** [窄受控桥接](../../v1_4_1/gate8_controlled_bridge_v0_1.md)
已有本地确定性验证，[服务器草案](../../v1_4_1/gate8_controlled_server_runbook_v0_1.md)
分静态编译、受控采集、后处理三段，均未执行。模型跨request同流epoch未决，
GetLastError未分类；不得把controlled包准备完成表述为模型/Q0/Gate8就绪。
Gate7 PASS、Gate8 NOT_RUN；下方7.25/7.26厂商路径是已暂停历史，不作为当前待办。

**当前7.27覆盖规则：** 用户批准路线A及目标request/必要依赖质量门，见
[Route A amendment 0.1](../../v1_4_1/gate8_route_a_quality_amendment_v0_1.md)。
厂商询证暂停，统一全capture认证不再前置；UNKNOWN仍保留。下方历史编号保留，
合并/缩减/后移以新amendment处置表为准。Gate7 PASS、Gate8 NOT_RUN。
本轮为本地实现、受控文件链与服务器前准备，不授权服务器采集。

**当前7.26：** 安装只读取证与审查完成，仍未找到充分完整性来源。下一项为用户审阅[一次厂商询证草稿](../../v1_4_1/gate8_nsys_vendor_inquiry_v0_1.md)，未发送；不再执行7.25安装搜索。答复后按有限路线裁决，UNKNOWN继续阻塞，未授权部署/采集。Q0与真实workload验收顺序不变。

**当前7.25覆盖说明：** 用户要求暂停扩功能，先做完整性可行性与新版Q0计划。已形成[决策备忘录](../../v1_4_1/gate8_integrity_q0_decision_memo_v0_1.md)：B一次目标安装文件只读取证→有界厂商询证/裁决→必要本地provider/资格接口→授权新Q0→再授权workload。无部署/GPU/Nsight授权，以下本地实现队列不作为本轮继续编码指令。

2026-09-25，当前状态：**用户已批准时间表示amendment，本地文件链及显式API已接通并做确定性验证；真实完整性仍UNKNOWN。服务器部署和采集未授权，Gate8 NOT_RUN**。当前执行状态以[本地实现v0.2](../../v1_4_1/gate8_local_implementation_v0_2.md)及 research_progress 7.24 为准；下方历史实施队列不表示实验完成，EP-G8-01～04仍未勾选。

本计划使用既有 EP-G8-01～04，不新增Gate、不创建worktree。输入依据为研究设计v7.1、实验协议v2.1 Pre-Pilot、冻结Measurement Contract及[接口审计](../../v1_4_1/gate8_interface_gap_audit_v0_1.md)。不修改冻结S/A/B、Q0或旧证据。

实施前问题已进一步收敛为[合同决策稿D1/D2](../../v1_4_1/gate8_contract_decisions_v0_1.md)。该稿细化本计划中的审查入口，不自动授权实现或实验；多repeat/设备identity工程细节无需用户逐项选择。

当前规范：[G8-OBS-BOUNDARY/0.1.0](../../v1_4_1/gate8_observation_boundary_amendment_v0_1.md)、[G8-COVERAGE/0.1.0](../../v1_4_1/gate8_coverage_reporting_amendment_v0_1.md)、[独立预期](../../v1_4_1/gate8_design_test_expectations_v0_1.md)。两份JSON Schema位于`docs/v1_4_1/contracts/gate8/`，已由新显式本地API消费，不自动切换旧路径。完整性调查见[目标版本记录](../../v1_4_1/gate8_nsys_integrity_evidence_note_v0_1.md)。D1/D2及本地实施均获批准，服务器执行仍未授权。

### 本地实现队列（已授权；在根main逐项tests-first）

- [ ] adapter身份单元：`platform_adapter.py` / `canonical_raw.py`与独立sidecar loader，先以ID-01/02、GPU-01和坏hash/PID负例复现producer→consumer断链；再接per-pass多request及namespace映射，不改W(s)。
- [ ] boundary单元：`runner.py` / `nvtx.py`共同helper点、host诊断ledger；新增专责scope projection模块，按D1-01～11先写预期；不把projection伪造成Raw range、不做clock平移。新模块须由Canonical sidecar向S/A共享ownership入口显式提供，拒绝旧/新profile混用。
- [ ] coverage单元：独立报告模块读S/A-B/projection，不重算W(s)或A；先实现手算主例和C系列负例，字段绑定`exposedpath-sync-call-coverage/0.1.0`。
- [ ] observation gate单元：肯定完整性证据provider未落实时只实现UNKNOWN/冲突拒绝路径；不写假成功provider。loss正例只可标synthetic。
- [ ] 资格/编排单元：核对boundary amendment §6 Q0影响矩阵、离线回归、CPU全量/contract/Canonical/oracle检查，审查新package/adapter版本资格；新增Gate8全链编排而不修改Gate7 legacy验收历史。服务器部署、相关真实Q0及新Engineering采集分别另授权。

上述为历史实施队列：显式身份/device adapter、共同marker/projection、coverage、UNKNOWN门以及signed-time A/B兼容、producer落盘与计算文件链均已有本地确定性验证，详见实现v0.2。未勾选不代表尚未实现；新Q0、真实完整性provider和目标机采集验收仍未完成。此前设计schema检查（8正例、11结构负例）仅属设计证据，本地回归也不等于EP-G8-01～04实验验收。

## 最小目标与工作量

在目标栈，以一次新的 **Engineering** run 证明 `benchmark → runner → Nsight → Canonical Raw → S → A/B → D/Signature` 可执行且每层身份、完成边界、有效性和证据缺口可审计。不是Gate7 legacy复跑、不是Pilot统计结论、更不是Formal。

候选保持 Qwen2.5-1.5B-Instruct、batch=1、32 input tokens、2 output tokens、warmup=1、repeat=2。两输出token使prefill结束于token0，decode包含一次后续token的完成，full_request结束于token1；不承诺其它长度/架构推广。执行模式为自然Token-ready（G1_NATURAL身份，不是G1正式实验），不引入N1同步。Pass0/1共用冻结token IDs、seed/生成算法、dtype、attention/backend、cache与EOS政策；EOS或不足2 token按既有exclusion记录并停止本最小验收，不偷偷补跑直到成功。

可复用既有模型内容清单（revision未知仍明确未知）、环境/编译器/marker快照作为**来源**；部署后需检查其仍适用。不得声称本地复算过未传回权重。模型输入文件与.cache辅助项分列。不能复用旧REP、性能、machine report、静态成绩作为新run结果。

## 分阶段执行与停止点

| 阶段 / 既有编号 | 输入与负责人 | 产物 / 通过条件 | 停止条件 |
|---|---|---|---|
| a 本地设计与确定性修复（EP-G8-01/02前置） | 主窗口；D1/D2已批准，仅根main | 版本化边界/多repeat/trace-device/coverage/quality适配；先红后绿的真实producer→consumer fixtures；负例涵盖缺字段、冲突、时钟逆序、缺completion、跨phase、外部ownership、dropped unknown；CPU回归/合同/Canonical/oracle/diff审查 | 超出冻结语义先报告；zero-drop未知不阻塞确定性实现，但阻塞科学验收及后续采集方案 |
| b 固定checkout部署与静态检查 | 用户服务器执行，协调窗口审查命令；固定批准的新commit/parent，不追随main | Git/bundle来源、clean；显式repo Python；VS x64/CUDA/Nsight/GPU mask/UUID/PCI/模型内容身份；pytest/compileall/verify及合同/边界/oracle原始回执；新pre-model门在模型加载前检查全部身份/输出冲突 | 身份/测试不符、环境变更未经核对、代码dirty；不额外复制checkout或移动venv |
| c 最小新Engineering采集（EP-G8-01） | b通过后另行请求明确GPU/Nsight授权；用户服务器执行 | 全新run，Pass0/1、warmup/repeat/attempt/EOS、telemetry、NVTX/REP/SQLite完整；逐层lineage；approved observation profile，timeout/retry独立产物 | 模型/OOM/EOS/时间逆序、身份错误、缺REP/SQLite/必需事实、异常退出；保留失败attempt，禁止resume拼接 |
| d 科学链与质量审计（EP-G8-02/03） | 主窗口只读回传包；协调窗口传输校验 | 六个request/phase窗口（两repeat各三窗）、精确completion；S/B原因与有效性；A原子互斥、守恒、unattributed；coverage口径/分母；D/Signature纯派生；逐项trace完整性、存储、可靠性与overhead报告 | 无窗口/全unknown不能写科学链通过；缺必需global证据整窗阻塞；局部失败保留unattributed而非填Host；不得用数值守恒替代归属正确 |
| e EP-G8-04报告与人工verdict | 主窗口 | 固定执行commit/输入/环境/包哈希、每阶段结果、失败原因和限制；四任务分别按证据勾选；下一阶段另规划 | 无全链证据不写Gate8 PASS；不把Engineering报告作为Formal或自动启动后续Gate |

实施范围：`exposedpath/nvtx.py`、`runner.py`（仅必要身份/边界instrumentation，保持completion语义）、平台adapter（trace namespace显式映射）、`exposedpath_v141/canonical_raw.py`及独立sidecar/编排/报告。已改文件和范围见实现记录；不重构S/A/B算法。每一项必须有producer-shaped回归；不能只修改测试fixture使consumer看似兼容。Gate7 launcher与legacy acceptance历史规则保持可追溯。

## 判定规则与研究限制

- Measurement Contract §4/5：host-readable token完成、predrain前置、cleanup不在测量窗，Pass0/1输入/控制流等价；不比较未解析时钟。A窗口不是CUDA提交范围。
- §9/10：全局drops、时钟未解、invocation边界无效影响整窗；无合法边界则不能造出一个全unattributed窗口。局部unsupported/ambiguous/invalid只污染受影响physical sync区间并报告原因，未受影响片段可保留。unclassified API按冻结规则处理，不能忽略。必需identity/lineage缺失阻塞整run验收。
- §10：整数纳秒duplicate/uncovered/out-of-window均0，五项互斥守恒；unattributed必须显式；守恒仅必要条件，不证明正确归属。Host residual不能掩盖缺证据。
- §9/11：VALID_EMPTY对应B_NOT_APPLICABLE，ambiguous/invalid的B数值null；不跨sync相加。§12：D/Signature只纯派生；零分母null，不造0。保留失败原因分布。
- 协议v2.1 Pre-Pilot质量要求：dropped=0、NVTX完整、无request-owned bleed必须有证据；当前Gate7的dropped unknown豁免不能沿用。对局部失败允许报告可分析部分，但是否达到Engineering报告的可解释性目标须如实评估；本计划不发明supported/B-valid百分比阈值，也不允许全invalid作为全链验收成功。
- Coverage是揭示A归属/B解释证据缺口的诊断，不是新增贡献指标，不能代替request A validity/守恒；按已批准D2处理跨phase/重叠，缺证据仍输出unknown而非伪精确比例。
- EP-G8-03：记录REP/SQLite/派生产物字节数、解析耗时、失败/attempt数、每repeat Pass0/1时间及描述性相对开销（分母非正则unknown）。repeat=2只检查可行性，不做置信区间、性能排名或正式overhead阈值；后续Pilot决定政策。capture时间与纯模型时间分开。

## 路径、身份与回传

沿用[目录规范](../../repository_layout.md)：固定 `$CodeRoot`；新证据 `$ServerRoot/evidence/gate8/<run>`，非采集诊断 `diagnostics/<task>`，操作回执 `logs/<operation>`，传输包 `transfer/`。精确机器路径只在`.local`/忽略handoff，不移动历史模型或证据，不另建repo_<commit>。

本地第一批实现基线main 8ea177e；服务器仍8d64f75。本地实现提交不是部署授权，不提供服务器bundle或采集命令。服务器布局完成仅来自用户回传，原receipt待协调窗口传回并核验。

未来回传：部署/静态/环境及模型清单来源、命令/transcript、manifest/prompt/源码身份、Pass0/1 JSONL/parity/attempt/exclusion/telemetry、原REP与采集诊断、export attempts/SQLite及schema检查、Canonical/S/A-B/Derived各manifest与数据文件、coverage/QA/存储/耗时/overhead/可靠性报告、机器报告与退出回执。包内清单先快照输入并排除清单自身；逐项大小/hash及ZIP hash，不能覆盖旧包。

**下一项具体动作：主窗口/协调窗口审查本地v0.2交付及新版本Q0影响清单；按完整性调查的有界路径取得目标版本肯定证据说明，而不是重复无结果的检索或模型采集。用户服务器本阶段无操作。** 本地提交不需要部署；实现审查及完整性方案明确后，才提出阶段b/c的具体方案。
