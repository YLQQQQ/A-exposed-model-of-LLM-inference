# Route A / target-scope quality amendment 0.1.0

2026-09-25。用户批准；Engineering。Gate7历史PASS及限制不变，Gate8 NOT_RUN。

## 适用与替代关系

路线A：单平台、单模型，可信request归属及相对常规指标的有限信息增益。
本修订显式替代实验协议v2.1 Pre-Pilot中丢失质量要求的**统一全capture解释**，
以及G8-OBS-BOUNDARY/0.1.0 §5将肯定全会话零丢失作为统一前置的规则。
原文件及历史结论保留；新执行须显式引用本版本，不追认旧attempt。
Measurement Contract 0.2、W(s)、A互斥union、B per-sync、D公式和Q0 oracle不变。
厂商询证暂停；无全capture认证不再单独否决所有目标窗口，UNKNOWN不写成零。

## 最小质量门

| 检查 | 防止的错误 | 失败后的结果/claim |
|---|---|---|
| request/repeat/pass、设备命名空间、原始clock与completion锚点可联结 | 混run、错卡、Host提交冒充完成 | 对应窗口不发布可信A或机制解释 |
| 必需API种类及依赖前驱范围有依据；包含窗口前已完成前驱 | 未观测同步落入Host、丢失hidden progress | 影响不明则拒绝，不以空W(s)冒充无工作 |
| 缺口位置、相关提交及依赖传播范围可证明 | 把缺证据伪装为wait/residual | 局部保留A的unattributed及原因，受影响B invalid/null |
| 未观测风险不能界定到局部 | 五类闭合掩盖整窗错误 | 保留原始/身份诊断，不发布该窗可信A/B/D |
| 独立受控正例的具体类别与W(s)/terminal吻合 | 仅守恒而分类错误 | 正例不通过则停止真实模型验证 |

“局部”不是仅按缺记录时间裁剪：缺kernel correlation同时损害submit归属和sync解释。
缺失影响在目标范围外必须有作用域证据，不能仅因记录不与request重叠便忽略。
NVTX完整、SQLite integrity、exit0或无警告均不单独证明必需依赖完整。

## D/Signature：保留结果不等于发布机制

本次不删除Derived 0.3的零unattributed/有效B保护。新增单独版本的
`exposedpath-accounting-publication/0.1.0`诊断：
`accounting_D_margin_ns = A_device_wait_ns - A_host_path_ns - A_cuda_api_ns`。
这是原式在已保留分量上的**记账差值**，不是完整窗口主导性或根因结论；
不计算局部unknown下的D score，不发布Exposure Signature，不推断未知部分方向。
局部行标记`PARTIAL_ACCOUNTING_ONLY`，附unattributed、window引用；
`mechanism_claim_allowed=false`、`signature_published=false`。
正例允许旧Derived模块生成明确synthetic测试产物，但不是科学发布。

唯一待后续Pilot固定的发布选择：非零unknown时何种证据/敏感性界限足以支持
**整窗**D/Signature机制claim。当前没有批准其阈值，因此不开放该claim。
这不阻塞有证据A分量及有效per-sync B的受限报告；不擅自设百分比。
开发先查原因与独立预期，Pilot依据支持域的unknown分布、误归属反例、扰动及
结论敏感性制定门槛，Formal前冻结；不得按Formal结果反向放宽。

## 显式本地接口与证据能力

`process_gate8_receipt(..., scope_assessment_path=..., synthetic_fixture=True)`
增加`exposedpath-target-scope-assessment/0.1.0`。旧integrity入口及旧schema不变；
两种输入互斥。新分析报告版本0.3.0、带scope的文件链0.2.0（旧0.1.0仍读），
package 0.3.2；S/A/B/Derived版本不变。

assessment必需字段：schema_version、input_receipt_sha256、basis、
collector_integrity_status、dropped_count、scope_status、boundary_identity_clock、
required_api_universe、dependency_scope、requests、local_gaps、reasons、evidence。
未知版本/额外字段、错hash、错窗口、未证实dependency或与实际S失败不一致均拒绝。
requests绑定request/repeat、signed-int64起止与dependency_start；与projection精确比对。
local_gaps列**失效physical sync**的Canonical sync_id、request/repeat身份、原始Host时间及原因，不冒充完整A unknown集合；
A仍自行按冻结规则传播到相关submit并作union。所有实际S失败必须被列出。
provenance保存assessment与其逐项hash证据；文件清单封存，输入不覆盖。

当前唯一实现basis为`SYNTHETIC_CONTROLLED_ORACLE`：它是测试construction的显式
前提，不是从Nsight自动推导的完整性认证，必须synthetic模式且始终NOT_ASSESSED。
SUFFICIENT/LOCAL_GAPS允许本地计算；UNBOUNDED保留诊断、拒绝A/B。
collector_integrity_status固定UNKNOWN、dropped_count=null；不生成ZERO_CONFIRMED。
现有Canonical全局错误不能被此入口覆盖。当前UNBOUNDED保守阻塞整次文件分析，
尚无自动拆分“其它合格request”的优化；不额外开发该可选能力。
真实目标scope证据入口仍待受控验证与审查；不得给真实REP加synthetic开关放行。

## 独立预期与实际文件链回归

`tests/test_gate8_route_a.py`经已有fake runner producer、真实SQLite文件、receipt、
Canonical、projection、S、A/B及发布诊断执行；不是GPU/Nsight证据。
使用既有`q0_oracle.calculate_expected_timing`的独立construction接口，不调用A生成期望。
Raw trace时钟保持负值：request[-60,140)，kernel[-30,0)，submit[-50,-45)，sync[-20,10)。
独立construction仅为oracle另用request-relative坐标，不平移Raw时钟。

| 用例 | A五类(Host/API/wait/residual/unattributed)，ns | B与发布 |
|---|---|---|
| 受支持正例 | 165 / 5 / 20 / 10 / 0 | B_VALID；hidden10、exposed20、tail10；差值-150；仅合成诊断 |
| kernel correlation缺失的受控副本 | 165 / 0 / 0 / 0 / 35 | B_INVALID；submit5+sync30不能具体归属；差值-165仅partial，不产D/Signature |
| 缺口作用域UNKNOWN | 不计算可信A | BLOCKED；无A/B/D，保留原因 |

局部例unknown位于prefill，decode为0；总和闭合之外逐类检查。
35ns不是方法成功的质量阈值，只是故障注入的独立预期。正例证明零unknown的
已知construction，不承诺真实模型必然为零。模型高unknown须先分实现错误、
工具观测不足、unsupported方法边界，不能一律重新分配Host。

## 原任务处置（编号与历史不变）

| 原编号 | 当前组织方式 |
|---|---|
| Gate0–7既有全部任务 | 保留历史结果；不重跑/不升级旧证据 |
| EP-G8-01/02 | 合并一次最小workload执行组织；先受控request，再单模型；各自证据仍列明 |
| EP-G8-03/04 | 同批记录coverage、overhead、可靠性并形成报告，不另建扫描 |
| EP-G9-01/02/04 | 当前平台复用身份、增量资格核对；与G8共享记录，不共享验收结论；第二平台后移 |
| EP-G9-03 | eager必要检查保留；compile/graph后移 |
| EP-G10-01/02/03 | 缩减为信息增益对照必需的稳定点与排除记录，取消当前广域扫描 |
| EP-G11-01/02/03/04 | 与G10合并Pilot组织；选点、repeat、开销/质量门及Freeze输入仍独立留痕 |
| EP-G12-01～05 | 保留最小Protocol Freeze、变更失效规则；只冻结路线A所选claim及支持域 |
| EP-G13-01～04 | 保留有限N1/G1对照；允许null，不预设rank reversal；不做全面参数扫描 |
| EP-G14-01～03 | G2及决策优越性claim后移，不是本路线前置 |

## Q0增量资格与下一次服务器受控验证（计划，未授权执行）

历史Gate6证明旧0.2 observation stack上的23-case资格，不证明新D1/adapter。
所有23-case独立oracle及CPU语义回归保留。未改的W(s)、A union、B公式复用旧结论；
signed时间、溢出、版本/文件/hash拒绝、D2裁剪只需本地新回归。
新真实验证按**所声明支持族**补D1 marker、physical/logical/trace映射、request/repeat、
scope projection和必要API观测；不能把一个STREAM成功升级为全部族资格。
STREAM/DEVICE/CONTEXT/EVENT及跨stream/default-mode/线程族分别有独有设备或API证据，
继续声明这些族时须增量验证对应接口；可同批，不默认23次独立重采。
COMPLETED/EMPTY可与STREAM批次共享；MISSING-CORR/DROPPED/GRAPH拒绝用受控副本与
旧oracle回归；TIE/RACE保持synthetic；mixed、phase spill、invocation bleed、
blocking D2H、QUERY按实际声称支持的路径补验证，不扩展graph支持。

下一项只规划一个受控STREAM request：单GPU单线程eager、显式known kernel及
stream completion，真实D1起点/first/last host-readable点、两次可区分request。
同一新Engineering批次承载正例；局部correlation缺失及作用域不明是**派生副本**
负例，不刻意制造collector丢包、不另跑故障GPU。保留原Raw。

执行前固定本修订、代码commit、工具/设备identity、construction与独立oracle版本；
仍须补最小受控producer到D1 receipt的真实桥接并审查目标scope证据，不可直接拿旧Q0
特殊窗口当新三窗。这是下一步必要实现/审查，不是已就绪的采集命令。
采集内容仅cuda/nvtx及既定必要event/API、completion与身份sidecar；不换collector。
oracle从受控提交拓扑声明W(s)/terminal、相关/无关工作和边界，时间从原始record引用
独立计算，不从被测analyzer回抄。不得用本地20ns等合成数字要求真实GPU时长。

通过：目标scope证据可界定、正例成员/terminal与具体A归属正确且无非预期unknown；
故障副本仅在可证明影响范围转unknown，未知影响拒绝；新旧资格映射逐项记录。
停止：缺API/event、device/clock/边界冲突、前驱无法界定、正例错误或意外高unknown；
不进入模型、不调阈值掩盖。此批不自动颁新Q0全资格。
回传：construction/oracle及hash、source/commit/clean、环境/设备/模式、producer receipt、
ledger/anchors、不可变REP/SQLite及export记录、scope证据与理由、全部新派生、
正负例对照、stdout/stderr/退出码、逐文件hash清单。新目录分别用
`$ServerRoot/evidence/gate8/<run>`及`diagnostics/<task>`，不覆盖历史目录。
