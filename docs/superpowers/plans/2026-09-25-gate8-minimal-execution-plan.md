# Gate8 最小执行计划 v0.1

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
