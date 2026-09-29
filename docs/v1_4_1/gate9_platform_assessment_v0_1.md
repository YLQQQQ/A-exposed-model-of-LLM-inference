# Gate9 单平台资格评估 0.1

## 当前7.96：分域合同已批准，资格增量待验证

现行依据：[G9-DOMAIN-QUALIFICATION/0.1.0](gate9_domain_qualification_contract_v0_1.md)。
用户已接受N1同显式流V0/Vmarker/Vsync的A/单sync B，以及G1自然投影A、无默认流物理B claim。
合同含独立手算预期与逐request门，长度变化不自动触发Q0；没有实现或采集。
Gate9仍BLOCKED，仅待显式流调用/ownership桥接及G1投影资格增量；Gate8 PASS不变。
下一步是合同§5的最小本地接线，不是完整N1、Pilot或Freeze。下方7.95“待裁决”及7.94停点仅为历史。

## 7.95 最小分域方案与claim影响（待最终裁决，不是生效amendment）

2026-09-29。用户原则上考虑接受；本版只固定可裁决方案，无实现/采集。
依据研究设计v7.1的信息增益问题、Pre-Pilot协议v2.1 §4.1–4.5/§5.1及用户单平台路线。
**推荐有条件采用：保留“可信请求归属＋有限信息增益”；放弃自然默认流完整物理B的当前claim。**
Gate8 PASS不变，Gate9不自动PASS。7.94原件审计与probe关闭结论保持；不恢复旧probe。

### 1. 两个可证伪的研究命题

| 分域 | 要检验的具体命题 | 相对常规指标可能新增的信息；否证/降级方式 |
|---|---|---|
| N1显式流受控 | 在输入与执行合同相同、仅中间同步干预不同的条件下，局部raw sync增加是否等于request E2E增加？等待是否在中间sync与自然token-ready之间迁移？ | Pass0给E2E变化；A定位request增量分量；合格单sync B解释hidden/exposed/terminal变化。kernel/API总时长或一个raw sync时长不直接提供该关系。若常规指标在所测范围已充分解释，则报告等价/边界结果，不宣称额外机制解释必然成立 |
| G1自然执行 | 在预定单轴输入变化下，kernel/API工作量的变化是否按比例映射到request/prefill/decode的可见暴露？ | 在同一目标证据范围比较常规kernel/API/sync计数、时长与A的分量/变化，说明哪些工作发生变化却未等量暴露、哪些Host/API路径影响窗口。只在数据支持时报告非比例关系；若近似等价则如实报告。不能由A图、守恒或unattributed=0推导信息增益，也不由A解释GPU硬件根因 |

最小G1候选仍为32→64输入、输出2/batch1；只是有限prefill/短decode对照，不代表长decode规律。
单次Engineering观察不证明效应稳定；选定比较、噪声/开销政策和统计规则在Pilot后冻结，不能按结果追逐反例。
N1只对有证据的单sync做B，不累加B代替request贡献；Vsync与Vmarker是主要干预比较，V0只量化包装影响，
不能把Vmarker差值未经论证机械扣成“纯同步因果效应”。

### 2. N1统一执行合同（候选）

全部V0/Vmarker/Vsync使用同一显式**非默认、非阻塞**流策略，同一模型内容、精度/backend、输入digest、
greedy/cache策略、batch/token、host-readable三边界、warmup及Pass0/1合同。自然token-ready不删。
Vmarker和Vsync在同一预定decode位置执行同一分支/标记；只有Vsync调用该实际current stream的sync。
V0不插额外标记/同步。固定variant/callsite/ordinal，输入和输出token内容对齐，不只检查长度。

加载、warmup、成功device drain在request外。优先在warmup/drain后建立专用测量流，并记录创建/销毁及
native→trace stream/context/PID/thread映射，避免把不可追踪的warmup流前缀带入B；所有组同策略。
如该流已有工作，必须保留其完整可恢复前缀，不能只因其位于request外或已完成就删出物理W。
这改变受控N1执行配置，必须明确写入版本合同；不能声称与自然G1调度等价。

`with stream`只表达框架选择，不是完整归属证据：逐enqueue correlation、线程、context、stream/lifetime、
返回值、所有已观测blocking API及event依赖核对。内部其他流不删：只有已受Gate6支持、能恢复且唯一归属的
显式依赖才纳入W/terminal/B；若实际出现未覆盖的默认流依赖、混合线程、未记录提交或ambiguous closure，
停止该候选，不临时关闭模型行为或新增同步来让它通过。首个资格只覆盖最小实际必要集合，不追求通用多流支持。
专用非阻塞流避免依赖未定的默认流隐式排序，但不是“保证库内部不会使用其他流”的声明。

### 3. 自然G1不发布物理B时，A仍须有S证据

复用D1共同clock边界、身份adapter、成功drain、同线程单实际FIFO后缀及Gate6依赖恢复/互斥union规则；
现有7.86/7.87只证明那个32/2 request。A按sync区间内必要活动交集恢复wait/residual，
不是把未决物理B隐藏后直接记Host。已完成的窗前前缀可以有不同物理W成员，但在已证完成的条件下，
不与窗口/sync阻塞区间相交；**这只支持A投影，不支持完整B hidden量**。

每个新request必须重新满足相同准入义务：边界/身份/时钟、实际drain、全部提交及同步映射、
ownership、无未知incoming依赖的显式支持条件、无冲突event/其他流、两模式下后缀闭包及唯一frontier、
必要集合与三窗A一致。有界分类缺口只能unattributed，不能填Host；影响不明则拒绝。
输入变长可能改变kernel/backend、资源/stream/event或同步路径，任何此类变化都使原单点证据不足；
新点自身记录通过才接受，不因32/2通过就推定64/2通过。质量判据先固定、不得据结果放宽。

现有实现只输出A_SCOPE_ENGINEERING_ONLY、measurement_validity=NOT_ASSESSED。
若要把此**投影方法**用于未来科学G1，须另有明确版本化观测/资格条款及独立正反例，
说明哪些证据支持哪些A claim；不能只去掉Engineering标签或自动授Formal。
旧UNKNOWN、旧条件性产物、旧BLOCKED报告不改。此项是方法适用域裁决，不是重新要求全capture零丢失。

### 4. 明确损失

- 不发布自然默认流完整物理B、全前缀hidden progress或默认流等待迁移机制结论。
- N1显式流结论不直接套到G1；不能说二者代表相同库调度、同一隐式依赖或证明自然模型的B。
- G1保持自然执行；不为了配合N1切流、改边界或关闭内部行为。
- 论文贡献从统一自然A/B解释收缩为“受控栈机制证据＋自然支持域A的信息边界”，外推性更弱；
  不授硬件根因、通用预测、决策增益或D/Signature。若核心claim必须是自然模型完整B，此路线不够，应暂停该claim。

### 5. Gate9修订后最小退出条件（待批准）

1. 本地可确定：平台/工具身份、Gate6已知流S/A/B oracle、D1/身份/三窗与A互斥实现直接复用；
   本方案已明确新增的是N1显式流合同和G1投影资格适用域，不完整重跑Q0，不要求先完成全部N1 runner。
2. 批准后本地增量：固定上述两分域的支持条件/claim；复用已有反例，只补专用流lifetime/ownership桥接
   及G1新点不能继承单点资格的入口检查。对未知其他流、缺边/错mapping、两模式不等价仍拒绝。
   保留同A数值但W/ownership错误的负例，不能只查守恒。
3. 必要目标证据（另交协调审查，不在本轮执行）：同PyTorch显式流最小kernel/D2H/current-stream同步，
   对照独立W/terminal/A/B预期并验证实际流标识/依赖；只验证新adapter/调用桥接，不重做所有Gate6用例。
   可与第一个选定模型点的执行接线证据组织在最小批次，但不能让模型结果替代独立oracle。
4. 资格结论只覆盖已声明且被证据支持的执行范围。新workload可行性归Gate10、重复/阈值归11、冻结归12、
   N1/G1信息增益归13。完整N1功能完成不是Gate9单独前置；未来新增路径须满足逐run准入。

**集中裁决建议：接受上述两分域及其claim损失，并授权随后版本化合同设计；本轮不授权实现或目标采集。**
该路线能保留路线A核心问题，但前提是接受G1没有完整物理B，且不把Engineering A自动升级科学资格。
若不接受其中任一前提，不应先堆显式流实现。当前Gate9保持BLOCKED、服务器无需操作。

## 当前停点7.94：probe关闭，不再安排默认流判别采集

[原件审计](gate9_stream_probe_v0_1.md)得到预定义INCONCLUSIVE，不是程序异常，不支持任何模式判定。
Gate9 **BLOCKED仅针对自然默认流完整物理W/B资格**；已验证的GPU/工具身份、一般stream-sync观测、
Gate6已知scope的S/A/B、限定A-only工程链与Gate8 PASS均保持。不把本结果解读为平台不能研究LLM。
N1 runner尚未实现不是此处的阻塞依据。

### 哪些claim仍受阻，哪些不受此次结果否定

- 受阻：按当前未知默认流解释，声称主线程sync的完整W包含/排除worker已完成前缀；
  据此发布物理B hidden/terminal/ownership及N1等待迁移机制结论。terminal未必变化，不能因此忽略W差异。
- 不受本结果否定：既有自然G1请求边界、身份、限定A互斥守恒及工程可行性；这些不自动升级Formal或信息增益。
- 可复用平台能力：Gate6在已知流语义下的stream/默认流用例及拒绝证据，不完整重跑Q0。
  未来显式流方案也必须有实际stream/correlation/ownership证据，不是只换一个API名就授资格。

### 是否已有确定性解法

现有header/PE只有候选调用边，原trace没有足够默认流语义绑定；本次事件状态没有补上它。
没有已保存、足以直接回答缺失命题的确定性证据。不把“尚无证据”说成CUDA原则上不可判别。
已批准构造只有单向反证：after仍pending可排除共享等待；after已完成不能证明共享等待。
加长kernel或重复执行仍依赖调度，不构成两面可判别oracle，取消此路线后续实验。
用GPU/Host gate强行保持未完成将改变构造并可能造成循环等待；timeout本身仍不能证明模式，
现有材料没有经审查的安全两面判别构造，因此不先开发gate/监控/反汇编等新设施。

### 推荐的一项研究裁决（未实施）

建议将**N1限定为显式非默认、非阻塞流的受控执行对照；G1保留自然执行，默认流B不作当前claim**。
这保留“受控同步下的机制解释”与“自然请求A相对常规指标的有限信息增益”两条证据，
不再要求先破解默认流全前缀。它是协议/claim范围选择，不是本轮普通修复或已有结果重命名。

代价与必须分开：
- N1的V0/Vmarker/Vsync都须使用同一显式流执行合同，不能拿自然默认流V0比较显式流Vsync，
  否则同时改变了stream和同步两个因素。加载/暖机/drain仍在request外。
- 显式流可改变隐式排序、调度与库行为；所得N1结论只适用该受控栈，不能声称等于自然Qwen机制。
  其实际流支持与输出等价须另做最小验证，但无需先实现完整N1或重跑完整Q0。
- G1不切流，不改自然token-ready或旧产物；保留A支持条件，不声称默认流B或D/Signature已合格。
  若论文必须解释自然G1的完整物理B，此推荐不满足该claim，应保留该部分暂停，而非静默删除义务。

**需用户集中决定：是否接受上述N1/G1资格与claim分域？** 接受后先版本化修改协议范围，
再按实际新差异安排资格；不直接Gate9 PASS或Formal。若不接受，暂停该物理B路线，不再生成重复补证任务。
本轮只完成审计/建议，不实现显式流、不部署、不采集、不重开Gate8。当前用户无需服务器操作。
下方7.92及更早是历史，不是仍需执行的probe任务。

## 当前结论7.92：C，静态核对到此停止

2026-09-29。本轮读取目标机已保存的source_snapshot及PE回执，不读取本机torch替代它，
不追加网页、源码或二进制搜集。Gate9仍BLOCKED于下述**会影响物理B的具体范围歧义**，不因N1未实现阻塞。

目标torch2.6.0+cu124的`torch/cuda/streams.py:93–99`调用`super().synchronize()`；
安装`CUDAStream.h:131–133`走`c10::cuda::stream_synchronize(stream())`，
`CUDAFunctions.h:100–110`调用cudaStreamSynchronize(stream)。PE回执中c10导出该helper、
导入无后缀cudaStreamSynchronize；torch模块导入c10 helper。回执DLL身份为
c10 `ff798a3e18a09291e993e9bba452152447c7507b605d683c8289bf5112efe024`、
torch_cuda `37fcaf926c486739e4cb505acb167a55d8f2ffd021c78f8822365478935c4630`。
这些是目标安装资料，不是完整编译调用点证明；无_ptsz导入不能证明整进程模式。
框架current stream是线程/设备的选择状态，native handle是传入CUDA的值，trace ID是collector映射；
三者不能与LEGACY/PTDS等同。来源审计及限制见[eager源码审查§10](gate8_eager_source_alignment_v0_1.md)。

本轮只读1733ff3既有Canonical作字段枚举/唯一correlation连接，未运行analyzer或改写证据：
Trequest=24082591723之前3838活动都在trace stream7；3500由主TID282482616358736提交，
其余四TID分别82/86/82/88项，共338项。例：MEMCPY:1对应RUNTIME:20740，
TID282482616369696，区间[16903169991,16903171495)。全部对应唯一API。
这比“所有活动同一个trace stream”更弱：不能排除collector对NULL表示与线程语义的差异。
完整global TID保留，不把数字stream相同当作物理FIFO已经证明。

两模式下若这些是共享legacy NULL前缀，则可能属于后续同步的语义W；若是worker的PTDS前缀，
则不因显示同一个NULL trace编号就属于主线程W。drain只能证明完成，不能删掉B所需hidden成员。
338项均在窗口外，不能据此否定已有A；也不能据A等价宣称B等价。
terminal可能仍是相同主线程后缀终点，但W、hidden union及ownership/validity未证相同。
此为具体歧义，不推断338项必定实际属于W或实际发生丢失。

### 一次最小区别性补证方案（协调窗口审查用，尚未执行）

只回答固定torch二进制、主线程native0、`torch.cuda.current_stream().synchronize()`这条调用
如何对待另一个Host线程的默认流；不证明所有库/线程/运行的全局模式。

整段操作顺序：
1. 核对固定解释器/torch与DLL身份、目标GPU及mask；新diagnostics目录。预先固定脚本/操作和oracle身份。
2. 主线程与一个worker分别记录current/default native handle；必须均为预期0，不临时切到新流改变研究对象。
3. worker在其实际默认流提交一个有界、可观察的CUDA工作K并在其后record completion event E，
   用CPU握手仅报告提交完成；主线程随后走上述生产同步调用S。不得用device synchronize代替S。
4. S返回后只query E，随后窗外清理等待。若需要trace，只采既有cuda,nvtx最小范围并保留enqueue/thread/
   event/sync关联；不加载模型、无N1插入、无CPU采样。整个probe有硬超时，不自动重试或调时循环。
5. 独立预期：共享legacy NULL下，S不得在先提交K完成前返回，E应完成；独立PTDS下W(S)不含worker K，
   若观测S结束早于K结束且E未完成，则能排除共享legacy行为。E已完成或K先于S开始已完成，
   在两种模式都可能出现，只能记INCONCLUSIVE，不能据“等了很久”判legacy。
6. 若实际记录明确使用可解释的每线程CUDA入口/流实例，结合调用证据可判相应作用域；否则只有前项
   有区别性的结果才支持有限结论。缺correlation、额外同步污染、身份变化、未知影响或超时立即停止。
7. 单ZIP回传脚本/oracle、身份、producer线程/handle/操作记录、stdout/stderr/退出码、REP/SQLite（如采集）、
   原始结论与hash清单。原封存包不改；无结果不得自动升级Gate9或启动模型。

该单次probe可能不具判别力，明确允许INCONCLUSIVE；不得承诺一次一定关闭缺口。
这是可审查的操作合同，不是可直接粘贴运行的占位脚本：尚未实现probe，不要求用户现在执行。
下一项仅准备该有界probe及CPU操作顺序/超时验证，交协调窗口审查后才申请目标机执行；
不恢复静态无限搜索、不完整Q0、不完整N1。若不接受该单向可证伪方案，保留BLOCKED，不臆造模式。

## 当前结论7.91（2026-09-29，取代下方7.90/7.89待办）

Gate9 **BLOCKED仅限计划中默认流current-stream调用的物理S/B适用性**。
不是N1 runner尚未实现导致平台不合格；接线属于后续实验准备，不作为单独Gate9门槛。
本轮只读已有派生字段及合同/源码，没有重新分析、测试或采集。

### 有限核对的事实与复用

- Gate6 final-04在Windows/4090/CUDA12.4/Nsight2026.2.1验证23/23，包括
  Q0-STREAM-001的W={K_S1_A,K_S1_B}、排除K_OTHER、B_VALID；COMPLETED、EMPTY、
  DEFAULT-LEGACY/PTDS及缺correlation等证明原物理S/A/B与拒绝语义。无需重新证明一般stream-sync能力。
- 36ed952配对、1733ff3派生：目标PID60060/context1/null_stream_id7；窗内sync347/348/349，
  corr61655/90867/116232、stream7/device0。逐request同TID/identity、唯一runtime mapping及ownership有效
  已由既有审计核对。current/default native handle均0；这些证明流关联，**不证明LEGACY或PTDS**。
- 本轮直接读取既有`canonical_manifest.json`：schema0.2.0/analyzer0.3.3，
  `execution_context.default_stream_mode=null`；`context.jsonl.gz`的原始context行确认null_stream_id7。
  stream行flag=3原样保留，不将该数值猜作CUDA默认流模式。原文件不改、未重算或重扫哈希。
- 限定受控资格和Qwen A已证明两模式下drain后后缀必要集合/三窗A等价；
  `gate8_engineering_scope.py`明确只发布A交集，物理S/B保留原状态。
  受控小程序的`--default-stream legacy`只约束该编译单元，不能证明PyTorch调用路径。

### 唯一缺口及最小补证

**缺的是实际PyTorch current-stream sync调用路径的默认流语义证据，或经批准可用于物理S/B的等价证明；
不是缺stream编号、一般CUDA能力或完整N1实现。** 当前合同仅批准后缀A等价，不能擅自扩展到物理B。
既有证据足够直接复用Gate6的恢复规则和oracle，但不足以选择本调用适用的默认流规则。

下一项先做一次有界的**精确调用路径/构建身份核对**：确认拟用`current_stream().synchronize()`实际绑定的
CUDA入口及默认流选择证据；必须对应已安装torch2.6.0+cu124二进制/构建，不能拿另一程序的nvcc选项代替。
若现有材料可证，直接复用对应Gate6资格，不采集。若没有，停止文件追索，只需一个不加载模型的
目标栈区别性受控probe：通过相同PyTorch调用路径，在另一已知blocking stream与目标默认流之间
安排可区分LEGACY/PTDS的完成关系，独立oracle预声明两种预期；普通单流kernel→sync不能区分，故不重采它。
只有明确观察可区分结果、无额外同步污染、身份与correlation完整才接受；不明确即停止、不调参盲试。
具体固定程序/命令需该调用核对后才能定稿，本轮不实施、不要求用户现在操作服务器。
不以A相等或B时长相似取代模式证据，不更改UNKNOWN，不以进度需要扩大支持域。

### 当前路线的Gate用途（保留编号，不机械复做）

| Gate | 必须回答的问题 | 复用 / 真正剩余 / 后移 |
|---|---|---|
| 0–6 | 方法、oracle及观测/分析是否正确 | 历史PASS与受影响增量资格复用；只处理实际新差异，不全重跑 |
| 7–8 | 执行身份/边界及工程链是否可行 | 已收尾，限制保持；不重开 |
| 9 | 选定平台能否承载计划同步与归属 | 身份/eager/一般stream-sync能力复用；仅上项默认流物理S/B适用证据待补 |
| 10 | 选定workload是否可执行 | 已有32/2点复用；只检查最终选定新点，不做广域OOM/参数扫描 |
| 11 | 重复数、开销/质量政策是否有依据 | 单次配对仅先验观察；最小代表点Pilot仍必要，不能当稳定统计 |
| 12 | 正式执行与判断规则是否预先固定 | 冻结实际版本、输入、平台、质量/排除/统计与claim；当前Pre-Pilot不能冒称已冻结 |
| 13 | N1/G1是否提供有限信息增益或等价边界 | N1接线/控制与G1单轴点归实验准备；资格、Pilot、Freeze后才采正式数据 |
| 14/G2 | 是否还有决策增益 | 当前路线非必需，后移；第二平台、compile/graph同样不作先决条件 |

Gate9即使后续PASS也不授Formal即时采集资格。Gate8 PASS保持；官方回复按用户提供内容采信，不再核验。

> 当前7.90：[最小执行方式—资格适用表](gate9_minimal_mode_qualification_v0_1.md)已完成。
> Gate9 BLOCKED具体原因：runner尚不执行N1，需本地接线及新增stream-sync资格桥接；
> 不是继续等待warning。用户当前无需服务器操作。以下7.89为前次评估依据，原“完成适用表”任务已结案。

更新2026-09-29（7.89）。工作继续，**最终资格 verdict = BLOCKED：拟用于后续科学对照的版本/执行范围尚未形成绑定的资格结论**。
这不是继续因四warning拒绝当前工程结果；[新证据裁决](gate8_warning_evidence_review_v0_1.md)已关闭该工程阻塞。
历史首评见[12f61df版本](https://github.com/YLQQQQ/A-exposed-model-of-LLM-inference/blob/12f61df41b1666fbcc4d11128dffb6a4886896e8/docs/v1_4_1/gate9_platform_assessment_v0_1.md)，不继续沿用其中“只有无影响假设”的结论。

## 已完成且直接复用

| 原编号 | 现有证据 | 结论 |
|---|---|---|
| EP-G9-01 平台身份 | [7.86配对](gate8_conditional_closeout_v0_1.md)实际Windows/RTX4090、CUDA12.4/Nsight2026.2.1、解释器/代码/模型/输入/设备关联 | 完成封存运行身份评估；不冒称当前服务器无变化 |
| EP-G9-02 观测及资格 | [Gate6原Q0](gate6_closeout_v0_1.md)、[限定受控资格](gate8_bounded_qualification_review_v0_1.md)、[1733ff3分类回归与实物复算](gate8_non_submit_api_review_v0_1.md)、7.89用户回传答复 | 当前最小eager工程观测已有支持，四warning不再作为其否决理由；尚不能把限定资格改成所有后续科学执行方式均合格 |
| EP-G9-03 eager | 实际Qwen/eager/SDPA、32/2、batch1、warmup1/repeat1、三窗/drain/内部同步、必要集合与A | 当前最小点完成；不要求第二平台、compile/graph或G2 |
| EP-G9-04 结论 | 本次更新划清已取得资格的版本/构造与未来科学用途 | 初评继续有效但阻塞理由更新；不自动授Formal或完整新版Q0 |

既有支持域假设（无未记录incoming依赖等）和两默认流条件等价保留；不新增“不可能有任何共享故障”的认证任务。
UNKNOWN/NOT_ASSESSED、单次开销40.3414%及输出token值parity未记录等仍是解释限制，不自动成为新服务器待办。
厂商答复目前是用户回传，作者/日期/回复楼层未直接核实；补齐引用元信息有价值，但不是平台身份或本地工作的重新开工条件。

## 真正剩余的一项本地工作

为首个拟采用的最小N1/G1对照形成**版本/执行模式—资格适用表**：
从已验证36ed952执行、1733ff3分析及NULL-FIFO-D2H限定资格出发，明确自然token-ready与拟用intervention
是否改变completion/sync集合、backend、stream或ownership。已有边界/身份/分类负例直接引用，不重跑完整Q0。
这不是扩大参数扫描或要求先做Pilot；是把“这个受控构造/最小点已验证”对应到“下一科学对照究竟使用什么”。

- 若只复用相同执行/观测范围，签发窄域适用结论，不为了换文档commit采集。
- 若存在实际改变，只列受影响的一个必要命题及独立预期；没有明确区别性观察量就不提出服务器执行。
- 停止条件：跨出单GPU/主要请求线程/既定eager支持域，或出现新的未恢复同步/依赖；不能用本次官方解释豁免。
- 不提前冻结repeat/overhead/解释度阈值；不将现Engineering数据变成Formal。
  后续Formal仍需其版本化协议、数据用途和资格签发，不因本次文档审查直接授权。

当前没有已确认必须进行的新服务器验证，故不提供重采脚本。下一步由主窗口在本地完成上述一页适用表，
然后按实际差异决定是否有最小补证；不是等待厂商、追索旧PID或再次修改warning门。
Gate8限定Engineering PASS保持；Pilot、Formal、D/Signature本轮均不启动。
