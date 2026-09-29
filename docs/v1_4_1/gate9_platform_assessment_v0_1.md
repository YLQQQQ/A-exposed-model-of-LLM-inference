# Gate9 单平台资格评估 0.1

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
