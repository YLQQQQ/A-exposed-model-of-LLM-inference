# 单主要Host提交线程的request范围与drain证书设计 0.1

**历史设计稿：用户已批准A优先方向，生效边界见[amendment 0.1](gate8_request_drain_scope_amendment_v0_1.md)。以下保留原待审措辞用于追溯，不再作为当前授权状态。**
基线main `83122233e5a8941a6d8187d27dac14f6565f173a`，进度7.54。
依据研究设计v7.1 §1.5、实验协议v2.1 Pre-Pilot（不是Protocol Freeze）、
[MC0.2](measurement_contract_v0_2.md) §7–10、已批准D1与Route A质量门。
暂停[collector转向提案](gate8_collector_pivot_decision_v0_1.md)：其必要性未被证明，
本方案优先检验request范围证据，而非从setup worker缺口推导“必须更换collector”。

## 1. 支持域及三种线程角色

模型/输入已就绪；单GPU、单隔离invocation，保留自然eager和现有同步；
窗口从原有request-start drain成功之后的D1 request_start，到最后token ID host-readable。
Prefill、Decode、模型侧sampling和自然Token-ready均在内；tokenization、加载、
token就绪后的反分词/文本拼接/网络/前端不计入核心A。不得把夹在窗口中的外层工作归Host。
拟支持域要求：目标CUDA提交与blocking sync由一个可辨识的主要Host线程发起；
这不声明整个框架只有一个CPU线程。其它线程只有证明不影响目标依赖才可排除。

| 角色 | 当前事实与边界 |
|---|---|
| 被测同步/提交线程 | 旧Gate7六sync同globalTid，四Token-ready在request内；不是Q0多线程反例的实测实例 |
| 历史GPU前驱来源线程 | 四加载worker共338次copy在首drain前；不算请求多线程推理，但其活动仍可能属于物理W历史 |
| 外层输出线程 | 在研究范围外，不据此推断存在或不存在；若实际侵入窗口，须识别并排除/拒绝相应执行，不能伪装为模型Host path |

旧SQLite进一步只读事实：首drain后已记录Runtime无其它Host TID；目标context后续
K6984/M6/S6全部由主要线程、stream7发起。记录缺失风险仍UNKNOWN；这些是支持域候选
证据，不证明没有遗漏。旧输入没有新版D1，不能追认为新版A或Gate8通过。

## 2. 有条件的前缀完成证书

提议profile `G8-REQUEST-DRAIN-SCOPE/0.1.0`，证书标识
`exposedpath-request-prefix-certificate/0.1.0`，均未注册/实现。
对request起点r、drain d和任一后续sync s，证书必须同时满足：

| 条件 | 具体来源及联结 | 失败处理 |
|---|---|---|
| 同次身份/实际scope | producer drain ledger、原NVTX range、唯一Runtime API成功返回及physical sync行；run/pass/request/attempt、PID、device/context经现设备adapter对应 | 错scope/失败/重复/缺physical行，不发证书 |
| 完成先于r | d的原trace结束≤D1 r，同clock；host诊断只校验同域顺序，不拟合时钟 | 缺point、倒序/跨clock拒绝窗口 |
| 前缀提交已封闭 | setup/warmup来源路径、完成记录、已登记相关加载任务完成且提交已结束；覆盖所有相关CUDA producer的限定范围与理由 | 仅load返回、AT_SEAL无等待快照、无worker行均不足；未登记producer/迟发任务可能影响请求则拒绝 |
| drain确实覆盖前缀 | 在d前已提交且属于实际device/context completion scope；排除跨scope、未提交/并发提交未定序、未知incoming依赖 | 不能把未来提交或其它context包进证书 |
| 请求期间无相关迟发提交 | 经审查执行路径/任务生命周期与Raw一致；核对从d到最终token的目标提交，外部来源、reset/reuse/资源冲突保留反证 | 时间或线程位于窗口外本身不是无关证明；影响无法界定则拒绝 |

来源字段复用producer0.4的pass_identity、host_boundaries、drain_ledger、stage_ledger、
load_tasks；新增证书只引用原record namespace/ID、文件hash、源版本及判据，不伪造Raw。
`load_tasks.COMPLETE`仅证明已观察任务完成；受支持源码的任务范围审查仍必需，不能称全程序证明。
普通无关CPU线程不要求逐一登记；只追踪能向目标依赖域提交工作的来源。

CUDA规则依据：`cudaDeviceSynchronize`覆盖此前各stream/Host线程提交的工作，
不覆盖未来提交，也不证明记录完整。
[官方同步说明§3.1.3.2](https://docs.nvidia.com/cuda/cuda-programming-guide/03-advanced/advanced-host-programming.html)，
[CUDA12.4.1 Runtime API](https://docs.nvidia.com/cuda/archive/12.4.1/pdf/CUDA_Runtime_API.pdf)。

## 3. A所需后缀证据，及与B的分离

将完整物理W记为历史部分P与drain后部分Q，仅用于证明，不删除或重写W：
若证书成立，则对P中每个成员有`end(e) ≤ end(d) ≤ r ≤ start(s)`，
所以`interval(P) ∩ interval(s) = ∅`。A的交集公式不变；无需知道P的hidden总量，
就能证明其对本次sync的A_device_wait交集为零。**这不是把未知活动时长填零。**

Q必须另有充分证据：请求/phase原completion点；所有目标blocking API分类；提交先后；
API/activity correlation；实际sync scope与stream/context对应；后缀所需event/default边；
owner和局部资源连续性；必要观测缺口能否影响归属。主线程相同、同stream编号、无告警均
不能单独满足它们。要求资源证据覆盖必要区间，不普遍要求复原所有setup TU/thread寿命。
如mode会改变Q的闭包，UNKNOWN仍拒绝；本草案**不顺带批准mode UNKNOWN等价放行**。
若其余都可证明但现mode门仍阻塞，必须报告具体后缀边，而非重新归咎加载worker。

| 判定 | A | B及派生 |
|---|---|---|
| 前缀证书成立、Q充分、三窗合格 | 提议新状态`A_SCOPE_CERTIFIED`，按既有互斥union逐段计算 | P成员/owner/hidden不全则B invalid/null，保留已知Raw及缺口；不标S完整有效 |
| P完整且全部既有S条件亦成立 | 走现有完整A/B路径 | 不因新profile自动授权，仍需对应新Q0资格 |
| 仅局部缺口的影响独立可界定 | 按Route A保留unattributed及原因 | B invalid；只允许已有保守记账差值，不产D_score/Signature |
| drain错误/迟发或外部提交影响不明、窗口/clock未知 | 拒绝可信整窗归属 | 不输出机制claim，不把request填满unknown后称成功 |

历史B的hidden、origin、完整terminal仍可能缺失；不能用drain构造虚拟活动或B terminal。
若Q有唯一合格terminal且晚于d，它可支撑A的后缀判断；若Q为空而全部必要历史由d覆盖，
提议仅使用“完成上界”证明sync内wait为空，不冒充B的精确terminal。此情形也属待审新准入。
本版不开放在B无效时的D_score/Exposure Signature，即使A的unattributed=0。

## 4. 最小amendment边界与唯一集中待审点

MC§7/closed-prior的完整物理W语义保留；MC§9–10当前把完整S validity与A绑定。
**需用户审阅的实质变更：允许上述前缀完成证书＋合格Q，独立授予A范围资格，而不授予
完整S/B资格。** 这是证据准入变化，不是普通字段重命名；A/B数值公式不改。
拟新增profile专用A资格/证据sidecar与显式loader版本，旧S/A-B/Derived reader行为不变，
未知/跨版本不兼容拒绝；B记录仍保留原失败原因，不覆盖成VALID。
批准后才定生产版本号/机器schema及tests-first实现；不把此草案当已批准合同。

## 5. 独立手算与精简验证矩阵

纸面正例单位ns：P=[-30,-20)，d=[-10,-5)，request=[0,100)，prefill=[0,50)，
decode=[50,100)；提交API=[0,5)、[50,55)，K1=[10,40)、K2=[60,90)，
sync1=[30,45)、sync2=[80,95)。同一支持流、先行提交、无其它边，token点50/100。
完整独立oracle：W1={P,K1}、W2={P,K1,K2}；B hidden=30/60，exposed=10/10，tail=5/5。
A每phase=(Host30,API5,wait10,residual5,unknown0)，总=(60,10,20,10,0)，不是仅总和闭合。
在只去掉P精确来源证明、保留完成证书的变体，新A须相同，B无效且数值null。

| 最小验证 | 复用／新增／停止线 |
|---|---|
| 上述正例＋前缀来源缺失变体 | 复用独立oracle区间运算及现文件链；新增新证书真实文件入口断言，不由analyzer生成预期 |
| 迟发相关任务 | worker在d后向目标域提交E，或任务结束无法确认；证书拒绝，不能以P完成推断E完成。相关性已知且范围可界定才走局部unknown |
| 错drain/外部scope/缺completion | 参数化错device/context/失败返回/错pass、请求内相关外部提交、丢末token；各自拒绝，不增加独立实验矩阵 |
| 历史已完成但B不同 | 复用closed-prior两/三owner手算、旧completed-before/phase-spill；确认P不从W删除，A不重复记历史 |
| 后缀依赖/时钟/terminal失败 | 复用旧Q0相关反例与signed-time测试；不因前缀证书掩盖Q缺event/correlation或默认流歧义 |
| 一次未来受控真实验证 | 仅新增受影响的单主要Host线程正例（带加载阶段及drain）及必要故障变体；稳定label/oracle比较W或证书范围、逐类A，不要求纳秒等于纸面值 |

Gate6旧资格/旧reader不重采；Gate7复用工程执行/设备/后处理结论，不用旧legacy产物
验收新A。新前缀证书与A资格不继承旧Q0。故障注入优先在新产物的独立副本中做确定性
负例；只有真实迟发/外部scope行为无法由已有资格覆盖时才追加最小受控负例，非全23项重采。

## 6. 测试与hash成本约定

- 设计阶段只检查文档/引用/diff，不跑pytest。实现迭代只跑新增测试及受影响的drain、
  scope、S/A-B文件链；有变化才扩大。CPU全量只在部署或阶段收口的固定commit执行一次，
  若launcher已负责该次全量则不另行手工重复。失败修复后重跑受影响项与最终集成门。
- Git跟踪脚本以commit＋clean及部署身份验证为主，不再为每段操作逐脚本hash；
  **现合同明确要求的runner_source_sha256、manifest/prompt等仍保留**，同次结果引用复用，
  不取消身份链。只读设计不改变现loader的强制校验行为。
- 固定模型完整内容清单建立一次，后续引用基线；仅模型改变或完整性有疑点时复算，
  不宣称引用旧清单就是本次复算。revision未知仍如实记录，实际输入/缓存辅助文件分开。
- Raw保持不可变，在封存时生成权威清单，跨机复制后完整核验一次；派生产物引用该身份。
  不逐条SQL/每份说明再次扫全文件。不同信任边界/文件变化仍须校验，不能靠文件名认身份。
  清单排除自身与历史清单，不产生循环hash。部署/分析入口既有必需校验不静默禁用。

## 7. 下一次唯一服务器动作的前置条件

现在**没有服务器动作**。用户审阅§4准入后，本地实现和定向/收口验证完成，
且前缀证书与Q的真实证据来源已具体可取得，才另行申请一次新Engineering受控验证包。
该包沿用一个固定checkout与既有最小cuda,nvtx profile，不开CPU sampling/新collector；
同一批次确认新执行身份、运行必要静态门并采集上述单线程正例，回传原件、producer/
drain/D1/证书输入、版本化报告与封存清单。任何关键来源未落实先停止，不靠模型重跑找缺口。
不包含自然Qwen科学验收、N1/G1正式实验；后续模型尝试需受影响资格通过后另行授权。
