# Gate9 N1/G1 分域资格合同 0.1

版本：`G9-DOMAIN-QUALIFICATION/0.1.0`；2026-09-29；状态：用户批准；本地增量实现见[7.97说明](gate9_domain_increment_v0_1.md)，最终限定资格已由[7.99裁决](gate9_closeout_v0_1.md)判PASS。以下合同义务不变。
依据：研究设计v7.1、Pre-Pilot实验协议v2.1、用户批准的路线A及7.96分域决定。
本文件版本化收缩执行/claim范围并定义G1投影资格义务，不改W(s)、A互斥规则或B公式，不是Protocol Freeze。
此前[7.95方案](gate9_platform_assessment_v0_1.md)的待裁决状态由本合同取代；历史判定保留。

## 1. 两域与证据角色

| 域 | 执行合同与研究问题 | 允许与禁止 |
|---|---|---|
| `N1_EXPLICIT_STREAM_AB/0.1.0` | 单平台/模型/eager；V0/Vmarker/Vsync同显式非默认非阻塞流、输入、模型内容、backend/dtype/cache/greedy、batch/token和边界。Vmarker/Vsync同预定callsite、分支与marker，仅Vsync增加current-stream sync；V0无额外干预包装 | 合格A与单sync物理B检验局部wait变化是否对应E2E增量，以及等待/hidden/exposed的迁移。不得跨sync加总B，不把marker差值机械扣成纯因果效应，不将显式流结果套到自然G1 |
| `G1_NATURAL_PROJECTED_A/0.1.0` | 自然执行、不为N1切流；预定输入对照，逐request验证下述条件。比较kernel/API/sync常规指标与request/phase A变化 | 检验工作量是否等量暴露、A是否提供常规指标未揭示的信息；不发布自然默认流完整物理B、hidden progress或默认流机制结论。A图/守恒/零unattributed本身不是信息增益 |

两域固定host-readable completion，request=[start,last-ready)、prefill=[start,first-ready)、decode=[first-ready,last-ready)。
模型加载、warmup、成功drain在窗口外；Pass0/1同输入和执行合同。Engineering/Pilot/Formal角色独立，资格通过不改变数据角色。
N1所有组同流生命周期策略：优先warmup/drain后创建专用流；已有流则保留其完整物理前缀，包括已完成工作。
`with stream`不是归属证明。框架其他流只能通过已获资格的明确依赖与ownership进入W；未知隐式关系拒绝，不关闭必要模型行为。
N1、G1都不授权硬件根因、通用预测、D/Signature或决策增益；信息增益允许零结果，比较与统计政策仍待Pilot/Freeze。

## 2. G1投影A：充分条件是联合条件，不是单一数值检查

以下为有显式支持假设的限定充分条件；不声称证明没有任何未记录活动。

1. **身份/窗口**：run/request/repeat/pass、进程实例/主线程、GPU/context、输入和实际配置一致；D1原始record引用与共同clock可核验；三个completion点有host-readable证据、顺序合法。保留signed时间，不能补0/平移。
2. **前缀隔离**：窗前drain成功且映射到实际device/context；已观测前缀提交与完成不晚于drain；相关未完成工作、迟到提交、跨窗口incoming依赖不得被裁掉。所有进入目标scope的已观测提交/同步均有解释。
3. **支持假设**：单request主要线程、单实际FIFO后缀，无未记录incoming依赖；这是预声明的执行支持条件，不是“没看见即没有”的事实。可见其他流/event/线程提交与该条件冲突则拒绝；新增诊断按既有目标scope规则处理，不一律豁免。
4. **逐sync证据**：原API、返回结果、correlation、线程、context/stream及生命周期唯一对应；恢复所有相关blocking调用。分别按LEGACY/PTDS恢复后缀必要集合，成员ID及依赖边必须一致，闭包完整，completion frontier唯一、活动已在返回前完成；映射或ownership冲突拒绝。
5. **投影证明**：保留物理前缀与后缀的来源；只能因已证前缀完成在窗前且无后续传播，将其对目标sync区间的交集判为空。输出的是必要活动对sync/window的投影，不是截短后的完整W。两模式必要投影一致后才计算A；数值相等只是末端校验。
6. **分类/质量**：同步优先于CUDA API，嵌套/重叠按现有union去重，Host只是证据充分后的补集。局部缺口须有独立影响范围证明，准确进入unattributed；不能用缺失correlation、未知依赖或全局诊断冒充局部分类缺口。

缺边界/clock/身份或影响范围未知：拒绝受影响窗口；不能证明局限到phase则拒绝整个request三窗。不得生成可信A或B，保留诊断及原Raw。
可界定局部缺口：保留已证明分量、缺口区间与原因，标为局部不完整；不声称完整解释，也不设置任意百分比门槛。
drop状态UNKNOWN保留；既有目标scope诊断裁决可复用但不自动覆盖新消息/冲突。G1物理B不获资格，旧physical S/B输出不被投影记录改写。

## 3. 最小字段与来源合同

新增资格封套版本为`exposedpath-domain-qualification/0.1.0`，引用现有Canonical、S、signed A/B及closed-prior版本产物，不重定义其schema。实现状态与受支持子集见7.97；封套并非资格证书。

| 来源→消费者 | 必需信息与用途 |
|---|---|
| 执行前manifest→receipt | contract/profile版本、role、variant/callsite、固定内容digest、平台/代码/adapter版本、支持假设；receipt记录实际配置，不能复制期望代替实际 |
| producer/trace→Canonical | request/repeat/pass/进程实例、native流创建/销毁、context、实际enqueue/sync correlation、trace stream ID；physical GPU/logical CUDA/inventory/activity映射按UUID/PCI/context证据，不按编号相等 |
| 原始boundary/drain→projection | record ID、clock、source hash、成功返回及时间；保存前缀完成证据、后缀成员、依赖边、两模式结果、拒绝原因和局部缺口区间 |
| projection→A | 显式`A_INTERSECTION_ONLY_NOT_PHYSICAL_W`来源、逐sync必要交集/terminal证据、窗口归属；不能送入物理B或冒充新的dependency证据 |
| N1 Canonical→S→A/B | 完整物理W、terminal/ownership和validity；已有S/B合同不变，B逐sync发布 |

封套分开保存observed facts、support assumptions、derived proofs、window verdict及数据资格；引用Raw/各层hash，不循环hash。
未知版本/缺必需字段/跨run或profile混用拒绝。G1的B资格明确为未申请，不以空B/零值伪装有效。
历史A_SCOPE_ENGINEERING_ONLY/NOT_ASSESSED、旧schema读取路径、旧BLOCKED及INCONCLUSIVE不改。
合同只用于预声明此版本的新执行或明确标记的历史输入兼容性检查；后者不能追认Formal或旧attempt。

## 4. 独立手算预期：先锁定，再接实现

以下单位ns、区间半开，是设计oracle，不调用S/A生成期望。真实平台资格另用事件/提交顺序确定集合，不能强求GPU实测这些时长。
R=[0,100)，P=[0,40)，D=[40,100)。已证窗前drain结束于-5，前缀K0=[-20,-10)。
主线程提交API=[5,10)、[45,50)，non-submit=[60,65)；K1=[10,30)、K2=[50,85)，同一合格FIFO。
s1=[25,40)，s2=[75,100)，各成功且唯一映射。独立顺序规定s1后缀必要集={K1}、s2={K1,K2}；terminal分别K1/K2。

| 窗口 | Host | CUDA API | device wait | residual | unattributed |
|---|---:|---:|---:|---:|---:|
| Request | 45 | 15 | 15 | 25 | 0 |
| Prefill | 20 | 5 | 5 | 10 | 0 |
| Decode | 25 | 10 | 10 | 15 | 0 |

wait分别[25,30)、[75,85)，return residual分别[30,40)、[85,100)；不把K1在sync前的部分算request wait。
N1专用流若含K0，物理W必须保留K0；另流且无依赖的U即便重叠也不得进入W。G1前缀成员可随模式不同，但已证全部窗前完成，必要后缀和交集必须相同。

| 独立反例/变体 | 预期，不以实现自洽作oracle |
|---|---|
| 给s1关联同时间但错误identity的U；或两模式集合不同但时长相同 | 拒绝，不能因同A数值/守恒放行 |
| K1 correlation缺失、流lifetime复用冲突、boundary错clock | 拒绝；不能证明影响局限则三窗全拒绝，不填Host |
| drain失败/前缀未完成/窗内外线程incoming依赖影响不明 | 拒绝；不能靠裁窗口隐藏 |
| 已独立证明仅[60,65)分类证据缺失、无提交/依赖传播（否则不属此例） | R的API=10、unattributed=5；D的API=5、unattributed=5；其余不变，局部不完整，不作完整解释claim |
| 把5ns wait错放residual，仍保持总和 | 与上述手算分段不符，失败；守恒不是正确性 |
| 新输入使s2=[95,120)、K2=[50,105)、last-ready=120，其余相同 | R Host=65，其余15/15/25/0；D Host=45，其余10/10/15/0。同支持域逐request检查，不因长度变更自动重Q0 |
| 新输入出现未支持event依赖/内部其他流 | 当前profile拒绝；仅对实际新语义申请增量资格，不能把长度当作豁免理由 |

复用已有缺边界/unknown诊断/ownership负例，新增测试只补profile接线与上述独立预期的缺口。

## 5. 复用、增量与Gate9退出

逐request自动检查第2节及实际身份/输入/分类覆盖；正常长度、活动数量、kernel名称变化不自动改变资格。
资格键绑定语义profile、平台/观测栈、调用与identity adapter、projection/analyzer/schema版本；内容digest另作run身份，不使每个prompt成为新Q0。
未知API先拒绝或按已证明局部范围保留，分类覆盖修复需定向回归；只有同步/依赖/ownership/边界/clock等实际语义变化才要求对应资格增量。平台工具变化按受影响观测能力核对，不机械全重采。

- 复用Gate6已知stream/event/default-scope S/A/B独立oracle与负例、D1/identity/三窗及限定受控A资格；不自动授全部新版本资格。
- **剩余N1桥接**：实际PyTorch显式非默认非阻塞流→native handle/lifetime→trace context/stream→current-stream sync的唯一映射与ownership；最小受控kernel/D2H证据对照独立必要集/terminal/A/单sync B。内部跨流只有已支持明确依赖方可纳入；不为资格实现全部N1干预。
- **剩余G1投影资格**：本地真实文件入口验证上述集合/来源/三窗正反例与逐request门；复用已有真实后缀/drain/边界实物作适用性证据，明确旧Engineering角色。若发现实际缺字段，仅补具体缺口，不默认重采模型。
- Gate9需两项增量审查完成才可判PASS；设计完成不通过。Gate10仅选定workload可行性，11 Pilot，12 Freeze，13信息增益；均不是本次Gate9任务，也不被Gate9 PASS替代。

上述设计任务已在7.97实现、7.98完成实物离线审查、7.99完成最终裁决；§5原“剩余”项目为设计时清单，均已结案，不重复执行。未来执行仍须另行批准固定版本；资格不能代替逐request质量检查。
