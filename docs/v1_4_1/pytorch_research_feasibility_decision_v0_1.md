# PyTorch研究可行性裁决与最小判别方案 0.3

2026-10-15；`PYTORCH-RESEARCH-FEASIBILITY/0.3`；沿用原文件路径，避免增加现行入口。
用户已批准0.2提出的一次有界本地方法检查，本版记录其终态。0.1/0.2及7.157/7.158保留为历史。
本地证据/方法可行性审查，
不是新测量合同、签署、资格或采集授权。ExposedPath研究协议与ARS有界审查；AI辅助
整理第一方材料和既有汇总，未运行同行工具作实测对比，不是独立外部评审或系统综述。

## 1. 最终建议：停止扩大路线B，不再以新增受控采集延长本次检查

**选择“应停止扩大”。** 完成前提的必要关系在自然PyTorch中确实可以核验，本轮12条
现有trace、24次token链均通过；但这只闭合“这些设备效果必须先完成，Host才可取得token”。
**本轮批准的必要关系目标可行，已在现有证据上完成验证，不需要新GPU实验。** 但它尚未
产生超出既有完成顺序/同窗timeline描述的、可独立检验的负载解释关系。不能把这项有限
可行性同时写成研究增量成立，也不能缩成只验一个极短内部同步。
这里不要求测出全部内部等待或独立整段阻塞时长；即使只研究完成关系，也必须有不止于
“先算完再读取”的负载命题与区分预测，才值得为新增方法继续投入。

0.2提出的立项闸口是：**自然C0中非空、独立可检验、对负载响应有实质解释的关系**。
本次前两项在必要先后关系层面成立，第三项仅取得可复核的位置描述，未显示新的解释能力。
这不否定本轮限定对象的可行性。若再沿0.2较强的“②近似③”方向寻找新关系，则须补完成
操作内部的前提/就绪状态和可核验的消费需求位置；重复Cpre或增加模型trace不能直接提供它们。
这已超出一次小成本本地方法检查，并且尚无相对已有依赖图分析的新关系/能力收益依据。
**不推荐为此开发新采集设施，不交付新的GPU验证方案，不恢复8-profile或引擎支线。**

这不是宣布“GPU约束永不可测”或“整个领域没有价值”，也不是因单一盲区否定已有成果。
保留已验证A/B、独立oracle、有限Formal信息结果及自然完成路径案例；停止的是用当前
②到③推断作为新核心贡献的扩大投入。现有材料可支持限定方法与边界报告，**不能据此
确认一个值得新增GPU预算、已具论文级增量的新立项**。本次检查在此结束，不滚动延期。

正确性证据可复用，但不能用“公式正确＋工具已完成”代替贡献。**当前三个实物问题，
增强到完整时间线/同一CUDA语义的baseline基本能够复原其关键事实。** ExposedPath的
实际增量是条件化、互斥、带来源与拒绝行为的输出组织；独特信息、分析效率/用户收益及
可迁移性能解释均尚未被证明。完整时间线也能复原，不意味着方法没有价值；但若没有
额外可验证的测量关系、适用条件或实证解释，不能把工程组织本身包装成论文创新。
该裁决不否定签署范围内相对常规聚合指标的有限信息增益，也不重判Gate13。

当前实物为Windows/4090、Qwen2.5-1.5B-Instruct/FP16/eager、既定backend声明；
与[研究设计v7.1](../current/ExposedPath_研究设计.docx)及[协议v2.1](../current/ExposedPath_实验协议.docx)
中的7B/BF16候选主矩阵分开。实际Formal遵循`G12-ROUTEA/0.1.1`，不能把限定实物当成
原候选主矩阵已完成，也不启动7B部署。llama.cpp/其他引擎/Linux/新设施继续暂停。

## 2. 贡献—证据表：最多三个解释问题

所有baseline都获得相同P1窗口、clock、registry、合法原记录、completion锚点和
correlation/stream证据，不能人为少给信息。聚合项包含count、裁剪sum/union、GPU活动
与sync墙钟；增强项包含完整时间线及同一支持域的CUDA依赖规则。不得以“图上重叠”
替代依赖，也不声称本次已安装/运行Daydream、HTA或SKIP。
增强baseline是依据已有独立Raw记录核对的手工/概念参照，不是同行工具跑分；能够恢复
这些事实不等于某工具发行版能直接消费本Nsight schema或已与本项目数值等价。

| 具体问题与实物 | 独立参照，不仅analyzer输出 | 常规聚合能回答 | 加入映射、stream与完整时间线后 | ExposedPath实际增量／没有额外增益 |
|---|---|---|---|---|
| Q1：自然G32→G512的GPU工作增加，为什么同步暴露没有同比增加？Formal六block；Prefill GPU union均值19.710030→42.431923ms，wait均值0.034954→0.029979ms；六块GPU差全正，wait差有正有负，Decode wait均0。 | 复用原独立Raw区间复核、成功drain/提交映射、token时序及源代码；GPU工作与Host完成的异步语义来自第一方CUDA/PyTorch。小CSV本轮只做均值/原值算术。 | 知道工作量、API成本、sync墙钟及其变化；不能仅由GPU总量推出暴露或根因。 | 原argmax/D2H在helper sync入口前完成可逐记录核验；能够解释为什么该sync交集为0，不需要ExposedPath独占的观测信息。 | 给出同窗预算及依赖合格性/来源，防止把GPU总量当延迟贡献。全部36个G1窗口API sum=union；Host补集也可由同窗union直接算，二者在本批没有额外数值增益。不能推一般负载规律或P0组成。 |
| Q2：N16第16层同步究竟等了什么，而非“它使request慢了多少”？Formal六block，预定干预各W为2814成员；block1 hidden union23.469255ms、exposed0.130335ms，terminal为kernel13286，tail0.023147ms。 | 复用独立FIFO/原correlation/scope/terminal核对及受控oracle；完整W保留已完成前缀，后提交排除。固定block仅作展示，结论核对六块，不以其有利程度选例。 | sync持续时间/次数不能直接给出完整成员、hidden/terminal或把E2E差归因给该sync。 | 同一依赖图及原活动区间可手工恢复先行集合、完成情况与terminal；HTA/Daydream说明这种依赖分析并非新思想。 | 逐sync B保留完整必要前缀和来源，提供可重复的限定查询，不跨调用求和。优于只给sync总量，但没有证明优于同语义完整图；P0 N16−Nm差波动，稳定收益不成立。 |
| Q3：自然C0与复制前同步Cpre是否只是改变暴露的观测位置？Engineering各一次；Prefill wait0.026304/38.971918ms，copy148.126383/0.725352ms；新增sync87.646953ms=必要交集38.946574+residual48.700379ms。 | 直接读取既存独立Raw复核和完整709段union/710段补集记录，含API/活动rowid、实际流、提交次序、成功状态及Host-ready锚点；不重新跑S/A。 | 能看见长sync、短copy、GPU总量；不能把copy差或sync全长解释为纯等待。 | 能恢复复制/同步/最后必要活动的先后顺序及包络内GPU推进；双方都不能从这些记录精确拆出自然copy内部等待。 | 互斥预算明确区分交集与残余，并拒绝把局部后缀冒充完整物理B。48.658361ms残余在terminal前、0.042018ms在后，但没有硬件/CPU/profiler根因。单次、不同时间执行，尚无稳定政策效应；不是新Formal。 |

来源：[Formal原审查](gate13_local_review_v0_1.md)、[A与公平baseline CSV](gate13_a_baseline_v0_1.csv)、
[单sync B CSV](gate13_single_sync_b_v0_1.csv)、[token时序CSV](gate13_token_completion_timing_v0_1.csv)、
[C0/Cpre与B1/B4局部审查](batch_load_prefill_review_v0_1.md)、[残余区间审查](completion_path_scientific_review_and_pilot_plan_v0_1.md#3-cpre残余的完整区间证据)。
B1/B4局部Prefill也已有GPU union52.541659/104.121389ms、wait0.525502/0.025024ms，
只能作为Q1的另一个Engineering线索，不与Formal六块或C0/Cpre混成重复；整request/Decode拒绝保留。

既有公共A CSV SHA256为`f9923fa01254b26dfd8502e306bb77e5e0377983b62bd2082a61e87926d52b98`，
B CSV为`87a60193d6bc31181861434aceaf7915703767fa3b19a0cea75d2f4c01a91331`。
复用的30条独立Raw审查终稿是`raw_independent_final.json`；C0/Cpre独立记录schema为
`completion-path-independent-raw-review/0.1`，SHA256
`b62962ee800b82e41cb99e817af04d22e8cfb2ec6fde6e639c70ec1b49bf648f`，绑定既存pair
`cde7c9101a5ca98b82f2c1472a6b4e8a9af80229a06d565c68f54d7bfe1a38e7`。
机器专属定位在忽略的handoff，不提交Raw。本轮复用其独立性/原资格审查，不声称重做了
30条SQLite或重新验证全部oracle程序。各数据的执行/分析版本见原来源记录，不由本文HEAD替代。

## 3. 有界最近工作核对与新颖性停点

原核验日2026-10-14；本轮2026-10-15只回读三项已知第一方页面，未扩展搜索。
限定Daydream、HTA critical path、SKIP三族及直接CUDA/PyTorch
语义来源。检索串为Daydream dependency graph、HTA critical path CUDA synchronization、
SKIP LLM inference profiling及SKIP精确标题。只使用作者论文、USENIX、官方文档/源码；
排除同名无关研究、二手综述和论坛摘要。不是全面新颖性证明，不按数量扩综述。

- **Daydream，USENIX ATC 2020**：作者正文§4.2.2已经以线程顺序、stream顺序、correlation和
  CUDA同步恢复CPU/GPU依赖；其所测配置也报告D2H Async可能在先行GPU工作完成前阻塞Host。
  §3还解释额外同步会改变依赖/运行时间。因而“依赖比重叠可靠”“同步位置重要”“Async可能阻塞”
  都不能作为本项目首次发现。它主要做训练优化what-if图变换/模拟，不等同当前实测互斥A/B。
  [发表页](https://www.usenix.org/conference/atc20/presentation/zhu-hongyu)、
  [作者全文§3～4](https://arxiv.org/pdf/2006.03318)。USENIX PDF读取因尺寸限制失败，改读同论文
  arXiv全文；未混用两份版本作逐字一致性证明，也不把2020平台行为直接授予当前平台。
- **HTA critical path**：官方文档已含CPU串行、kernel launch/同流顺序、device/stream/event
  同步边及ROI选择；输出是带假设的加权DAG/最长路径，不是“五类A＋完整W的单sync B”。
  当前源码也列出可能同步的cudaMemcpyAsync。不能将HTA降格成kernel总量baseline，
  也不能因其简化假设/特定trace格式就宣布本项目更准确。
  [设计及假设](https://hta.readthedocs.io/en/latest/source/features/lightweight_critical_path_analysis.html)、
  [官方源码](https://github.com/facebookresearch/HolisticTraceAnalysis/blob/main/hta/analyzers/critical_path_analysis.py)。
  页面标TraceInsight0.6.1，源码为本日读取的main，不声称固定发行实测；缺目标格式执行对比。
- **SKIP，ISPASS 2025**：核验作者v1正文§III-A、IV-A及作者接受声明/related DOI。
  它已有ATen→runtime→kernel的correlation/stream/thread映射，以及TKLQT、AKD、推理时延
  和GPU idle等量。因此“研究LLM CPU/GPU关系”或“从operator追到kernel”不是充分新贡献。
  TKLQT是launch/queue延迟的逐kernel累计，不是互斥request exposure；它能提供本项目
  不能删掉的竞争解释。未取得/运行其源码，不猜测其全部能力或宣称不存在相同预算接口。
  [作者全文§III～IV](https://arxiv.org/html/2504.11750v1)、
  [元数据及ISPASS关联DOI](https://arxiv.org/abs/2504.11750)。

**可验证的新贡献候选**仅是这一组合的研究价值：Host-readable端点、完整必要前缀、
phase互斥预算、逐sync来源及透明拒绝，在完成政策比较中提供可重复解释和明确等价边界。
在核对章节没有看到完全相同的输出合同，**不等于证明别人的代码/其他论文没有它**。
接口不同、自动化和更严身份门只是实现差异，尚不证明科学增量或效率优势；如果增强baseline
已充分解释所有实例，就应以限定测量/边界结果收口，而非继续追加引擎寻找有利图。

## 4. 本次验证对象：必要完成约束，不是一个新“阻塞时长”

对每个稳定request/token身份j，验证对象是三项：

1. **前提集Pj**：由预设程序关系、成功completion语义及合法映射证明，在取得该token之前
   必须完成的指定设备效果；不得按重叠或全局最后kernel猜。完整物理W、局部投影后缀和
   指定token的D2H效果是不同scope，不能互相冒名。
2. **完成事实Gj(t)**：Pj中这些效果在t时是否已完成。已知全部完成/已知有未完成/缺证据
   UNKNOWN三种判断分开。只有Pj及其所有完成条件已独立闭合，才可定义整个集合的就绪点；
   单条D2H结束只是指定效果完成事实，不自动等于所有GPU/驱动前提已经全部满足。
3. **Host事实Hj**：成功取得的实际token值、消费线程及其程序顺序。必要关系为
   “取得Hj之前，Pj的前提已满足”；它不是充分的返回条件，还可能有Host/驱动等步骤。

验证输出是**带来源的必要关系和区间约束**，不是sync墙钟、入口→terminal、API包络或
“GPU单独造成的净停顿”。不把①GPU工作量、②原A交集、③本次完成前提关系和④优化收益
合并成一个量。对④仍没有真实优化/反事实证据，本次也不试图补齐它。
0.2曾讨论②作为③时长代理的更强问题；本轮按用户指令限定为必要关系，**不以不能量化
全部③来判这一弱对象失败**。投入决定另看是否产生值得检验的负载解释增量。

**这项定义可以检验，但科学用途不能只凭定义成立。** 还须判断它是否能解释固定完成政策下
负载造成的phase完成变化，而不是只说所有正确程序都必须先算出结果再读取。当前后者
确实可核验；前者只得到已有完整时间线也能直接给出的位置关系，未得到新的可检验关系。
这里没有将“必须测尽全部Host阻塞”重新设为门槛。

## 5. 独立参考：明确输入、答案与取得方式

| 参考 | 输入、预设关系与完成条件 | 独立预期及取得方式 | 不能证明 |
|---|---|---|---|
| 既有受控Q0 | 人工construction/expected中的稳定活动与sync身份，例如Q0-STREAM-001、COMPLETED-001；W事先给定。 | 读取已冻结人工答案与历史独立Raw核对；STREAM交集40ns，提前完成成员仍必要。未调用S/A生成答案，未重跑Q0。 | 原oracle没有自然复制内部Host状态及真实token读取参考，不能改名授予③资格。 |
| 本次CPU手算token例 | 输入x=3，假定已知设备运算2x+1得7，必要效果K→D2H→Host读取。合成完成K=5、D2H=7；晚到无关效果U=25不在Pj。 | 读时刻6判NOT_READY、9且实际值7判READY；缺D2H判UNKNOWN、值8判冲突、D2H未完成判NOT_READY。答案由预设运算/依赖给定。 | 这是逻辑参考原型，没有运行CUDA运算或模型，不是自然路径正确性证据。 |
| 自然Formal原件 | 固定99f3bae的helper：argmax结果→同线程.cpu()/tolist/整数token→Host采样→D1 point；复用已资格的成功drain和scope。 | 原SQLite里的结构化request/token范围、唯一复制runtime及相关D2H、唯一成功stream sync，与producer的实际token/ledger相符。以下24次直接核对，不读取A/B数值当答案。 | 不能由成功结果推回复制内部何时在等待，也不能把推定源码路径当成实测完整native callstack。 |

CPU原型只检验参考的READY/NOT_READY/UNKNOWN与内容冲突行为；**6项新断言通过、0失败**。
此前10项区间断言原样保留，本轮没有重跑或包装成真实CUDA证据。晚到无关活动不能延长
前提集，已完成成员不因此失去必要性；“已知pending”与“缺映射”不能合并成已完成零值。
该原型未恢复依赖图，Pj是手工输入；没有新增生产代码、资格读取器或采集设施。

第一方依据只定向回读已知版本：
[PyTorch2.6 CUDAFunctions.h](https://github.com/pytorch/pytorch/blob/v2.6.0/c10/cuda/CUDAFunctions.h)
的CUDA分支为cudaMemcpyAsync→cudaStreamSynchronize；
[Copy.cu](https://github.com/pytorch/pytorch/blob/v2.6.0/aten/src/ATen/native/cuda/Copy.cu)
在相应阻塞分支调用该helper。目标机原头文件及其hash引用复用
[既有API审查](gate13_cuda_api_storage_review_v0_1.md)，不拿不同版本替代目标二进制资格。
[CUDA12.4.1说明](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/api-sync-behavior.html)
明确API行为可能依赖参数/内部资源；这不授予任何内部等待数值。

## 6. 自然路径的实际参考及其负载解释能力

### 6.1 已闭合：不是只找到了一个极短sync

在**12个既有G32/G512 P1 run、六block、24次token**中定向读取SQLite及必要小文件：

- 每个输入receipt的SQLite/runner源码/Host ledger/token文件长度与hash相符；旧完整审查身份
  复用，不重复CRC/全包或Canonical扫描。原执行99f3bae、原分析e19c308不由本次文档HEAD替换。
- 结构化boundary与natural_token_ready范围绑定相同request/token、PID/TID；范围内唯一
  cudaMemcpyAsync和成功cudaStreamSynchronize，原correlation唯一映射8-byte D2H及physical
  sync。device/context/trace stream一致；没有用时间邻近配对。
- 实际token为G32 [463,2529]、G512 [29184,6556]，分别与同条件记录一致；**不要求不同
  输入长度生成相同token**。成功模型执行/Token值是事实，不声称独立重算了LLM的正确答案。
- 24次均满足复制调用返回≤sync入口，以及D2H结束≤成功sync返回<后发completion point。
  D2H均早于该sync入口5.084～168.788µs；同一调用的活动交集为0有独立顺序依据。
  这不是整个Prefill无wait；原框架内部sync及原A/B仍保留。
- 来源程序顺序给出实际Host读取的trace-clock区间：
  **sync API返回≤Hj≤D1 point**。这是同线程先后的夹界，不拟合Host/trace时钟offset。
  此区间宽度为2.072793～4.205537ms；Host同钟完成采样到point准备为2.0358～4.1146ms。
  不把这些个案当所有run的误差上界，操作完成到Host采样的未观测调度延迟仍不精确可分。

它覆盖首、末token完成链，结合既有scope/drain资格可说明request/phase端点如何形成，
不只宣称极短内部同步“存在适用窗口”。但全Prefill的Host提交/API内部步骤与GPU执行
交错，端点关系并没有把这些交错转换成GPU造成的时延预算。加载/暖机/drain仍在窗外，
没有修改C0完成政策、加同步或用Cpre替换自然路径。

### 6.2 与负载变化的具体联系，以及没有闭合的部分

下表直接由原始D2H、request point、首token point得出，单位ms，均为**G512−G32**。
它是本次事后解释性小核对，不是新增冻结统计检验；六block全部保留，不合并Engineering。

| block | 投影Prefill结束差 | 指定D2H完成位置差（相对各自request point） | 实际Host读取后缀差的可行区间 |
|---|---:|---:|---:|
| 1 | −2.674752 | −3.058493 | [−2.198974,2.663013] |
| 2 | 4.446996 | 5.529030 | [−3.286954,2.183670] |
| 3 | −8.411904 | −7.325998 | [−3.432668,2.497181] |
| 4 | 0.866753 | 1.072328 | [−2.346390,2.173386] |
| 5 | 8.506455 | 9.427312 | [−4.192569,3.284680] |
| 6 | −13.625525 | −12.929171 | [−3.057738,2.486006] |

“Host读取后缀”指Hj−D2H.end，不是CPU忙、GPU等待或返回开销。区间通过两个run各自的
同线程夹界相减取得：[Lb−Ua,Ub−La]，不是置信区间。全部含0只表示这些参考不能排除
后缀差为0，**不证明后缀不变或等价**。point差也不是精确实际Host读取时刻差。

已有GPU union在六块均增加，而上述完成位置及point变化三正三负。因此：

- 必要关系参考确实连接到了**整个Prefill的末端位置**，可以展示工作量增加与完成位置
  不是同一量；不是仅检查一个微秒sync。
- 它没有区分这段完成位置变化由Host提交、API内部前提、设备执行/空隙或观测扰动各造成
  多少；不能据“D2H完成位置跟point同向”判GPU导致了同量phase差。
- 原E差为4正2负。例如block1 E增加0.005248ms、D2H完成位置却提前3.058493ms；
  block2 E减少0.050431ms、D2H位置延后5.529030ms。它不支持把E当该位置变化的简单代理；
  这不违反原E的局部定义，也不是把D2H位置当作真实③反证计算错误。
- 同窗完整timeline加correlation及相同CUDA语义能给出本表相同先后/位置。这一事实不
  单独否定方法贡献；但本次没有另外获得可独立校验的约束量、误差关系、非显然预测或
  分析能力改进，尚不能把这些位置描述提升为路线B的研究增量。

### 6.3 Cpre为什么不能补这一缺口

仍复用既有独立区间审查：新增sync墙钟87.646953ms、必要活动交集38.946574ms；
入口至最后必要活动87.604935ms，其中48.658361ms未被必要活动执行覆盖，另有
terminal后0.042018ms。**这些跨度不是真实GPU阻塞参考**，更不能因其中一项接近期望
就将它作为标准答案。Cpre只授局部A必要后缀，不授完整物理W/B。

GPU活动有空隙时，交集与完成前提持续未满足的时段会不同；自然opaque复制还可把设备
推进包含在API包络内。此处只需保留这些有限解释缺口，不追索旧84次调用、w11或全会话
UNKNOWN，不把未解释部分重分到Host/wait。原Formal边界与全部结果保持。

## 7. 明确不同判断、代价与终止结论

| 待判命题 | 独立参考与现模型能否区分 | 本次判断 |
|---|---|---|
| token读取前是否完成指定必要设备效果？ | 手工预设依赖/值与原correlation/程序顺序可独立检查；缺映射UNKNOWN、未完成NOT_READY、晚到无关效果不能冒充前提。 | 可行，24次自然链与6项CPU检查支持这个层次。 |
| E较小是否表示整个完成过程所受GPU约束较小？ | 已知gapped/opaque例可出现E小而必要设备前提尚未满足；同一完成位置可有不同活动交集。 | 不能由E单独判断；没有通用误差界/下界或近似资格。 |
| 必要关系对负载phase变化增加了什么？ | 参考给出先后与位置，六块位置变化混合，可描述但未独立分离其余前提的变化；同源位置恒等式不是新预测。 | 限定对象可行；新增解释关系/能力未成立，不把二者混成研究成功。 |
| 再做一次连续必要执行的受控GPU正例能否改变决定？ | “模型仅在明确同步里记交集”与“能解释自然完成约束”的解释都可能通过该正例。改成Cpre又改变了待迁移的自然政策。 | 无足够新增判别价值，不申请该采集。 |

**为什么不是恢复全部内部机制的要求：** 已经接受并保留必要关系这个弱目标。停止的理由
是它虽有负载完成位置上的联系，仍不足支撑新增方法的实质解释主张，不能用对象验证通过
掩盖贡献未成立。无需解释每个CPU周期、每个driver函数或证明全capture零丢失；也不把缺全套
底层机制当作撤销原A/B资格的理由。

若继续选择0.2的更强代理解释，至少须有一条可靠途径区分**进入完成操作后实际等待哪个前提、该
前提何时满足、Host何时已经可以消费但尚未消费**。当前仅有API包络、活动时间和后发
point，不能分离这些状态；**这不是本轮必要关系验收的新条件，而是更强用途的额外代价**：

- 仅加Host marker能缩小程序位置区间，不能看穿复制helper内部前提；point也不等于CPU
  真正可运行状态。更多同配置模型trace不补这个信息。
- 记录复制参数/地址可能改善效果映射，却不自动产生内部等待分解或消费就绪参考；没有
  理由恢复独立CUPTI支线来假定它解决此问题。
- 要在当前固定Windows/PyTorch栈上分离这些状态，可能涉及框架/driver边界的额外观测、
  实例级内存/完成关联及其独立验证；具体可靠接口尚未具备。那会成为新设施/资格工程，
  时延扰动与迁移有效性还要另证，超出本次投入上限，不制定安装/开发/采集任务。

**唯一建议：停止扩大路线B及其GPU验证，不把“还需要研究”列成下次自动待办。**
原0.2中的2受控进程/1profile只是未授权候选；本次已判其不能直接关闭自然路径缺口，
**不准备该入口或预算申请**。8/24-profile、四对C0/Cpre、llama.cpp/其他引擎均继续暂停。
没有一项现成目标机操作可以直接取得所缺答案，因此用户现在无需操作服务器。

可保留的成果是限定A/B实现、历史Q0/独立Raw oracle、签署Formal的有限信息解释与自然/
受控完成政策案例。不能把它们改写成全部Host阻塞、GPU单独净停顿、优化收益或普遍负载
规律已成立。若研究目标将来重新选择，须另有实质主张与判别设计，不能通过恢复旧矩阵
绕开本次停止结论；本稿不提出一个替代任务来延长投入。

## 8. 本轮记录、历史兼容与保全

- 读取当前协议/已有审查、固定源码差异、目标安装头文件引用与原件；只做定向只读SQL及
  小文件绑定，不跑完整analyzer/Q0/模型/CUDA/Nsight或服务器步骤。
- 12个run的24条完成链、六block位置/夹界与6项CPU检查保存于本机版本化诊断索引，
  schema为`completion-constraint-feasibility-reference/0.3`，SHA256
  `08523a5166b8b75c50ae71f2cdb287759e367f7d3624e80cb7c042301ae9792e`。
  这是事后解释性参考，不是新的Formal资格、阻塞时长oracle或冻结统计替代品。
- 0.1（b8f1d4d）曾建议限定边界路线及8槽；0.2（444310b）撤回8槽判别能力，建议一次B
  方法检查；用户随后仅批准该检查。本版完成检查并选择停止扩大，历史7.157/7.158保留。
- 未修改A/B公式、registry、边界、统计或业务代码，不需为本次文档重签协议。Gate13
  限定PASS、Gate14 NOT_RUN及所有数据角色、UNKNOWN/NOT_ASSESSED/旧BLOCKED保持；
  原Raw/ZIP/报告和用户DOCX不改、不纳入提交。不生成部署包、不清理原件。
- 进度事实源更新7.159；当前handoff只指向本版终态。不是把论文增量评为PASS，不承诺
  投稿等级/录用，也不将本次停止解释成旧Gate失败。
