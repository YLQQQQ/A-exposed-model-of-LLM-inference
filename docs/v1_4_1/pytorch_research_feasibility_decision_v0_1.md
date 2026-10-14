# PyTorch研究可行性裁决与最小判别方案 0.1

2026-10-14；`PYTORCH-RESEARCH-FEASIBILITY/0.1`。本地证据/文献审查与待审方案，
不是新测量合同、签署、资格或采集授权。ExposedPath研究协议与ARS有界审查；AI辅助
整理第一方材料和既有汇总，未运行同行工具作实测对比，不是独立外部评审或系统综述。

## 1. 裁决：收缩为限定测量与边界研究

**选择“收缩为限定测量与边界研究”。** 值得保留的对象是：在明示完成政策和支持域下，
以可核验依赖把观测执行映射为request/phase预算，并说明它与activity/critical-path
分析的等价处、差异处和不能回答之处。当前没有充分依据，把它推广为全部GPU相关Host
阻塞恢复、稳定性能机制、通用负载转折规律或优于已有依赖图方法的新理论。

正确性证据可复用，但不能用“公式正确＋工具已完成”代替贡献。**当前三个实物问题，
增强到完整时间线/同一CUDA语义的baseline基本能够复原其关键事实。** ExposedPath的
实际增量是条件化、互斥、带来源与拒绝行为的输出组织；独特信息、分析效率/用户收益及
可迁移性能解释均尚未被证明。若只需复现“插同步后sync变长”，不值得继续扩工程。
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

本轮核对的公共A CSV SHA256为`f9923fa01254b26dfd8502e306bb77e5e0377983b62bd2082a61e87926d52b98`，
B CSV为`87a60193d6bc31181861434aceaf7915703767fa3b19a0cea75d2f4c01a91331`。
复用的30条独立Raw审查终稿是`raw_independent_final.json`；C0/Cpre独立记录schema为
`completion-path-independent-raw-review/0.1`，SHA256
`b62962ee800b82e41cb99e817af04d22e8cfb2ec6fde6e639c70ec1b49bf648f`，绑定既存pair
`cde7c9101a5ca98b82f2c1472a6b4e8a9af80229a06d565c68f54d7bfe1a38e7`。
机器专属定位在忽略的handoff，不提交Raw。本轮复用其独立性/原资格审查，不声称重做了
30条SQLite或重新验证全部oracle程序。各数据的执行/分析版本见原来源记录，不由本文HEAD替代。

## 3. 有界最近工作核对与新颖性停点

检索日2026-10-14；限定Daydream、HTA critical path、SKIP三族及直接CUDA/PyTorch
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

## 4. 风险：三个层次不能互相替代

1. **定义内正确性**：现有独立oracle与Raw区间/依赖核对支持获准子域，不靠守恒或零unknown
   单独判正确。同期比较仍必须核实际流、request后缀、成功drain、边界、token和诊断；
   缺效果/影响不明仍拒绝。局部Prefill资格不授自然默认流完整物理B或整个Decode。
2. **近似潜在量**：A_device_wait不是全部GPU相关Host阻塞；API可能含未分离内部阻塞，
   residual不等CPU开销。当前没有完整阻塞ground truth或误差界；
   [CUDA12.4.1同步说明](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/api-sync-behavior.html)
   和[PyTorch2.6复制helper](https://github.com/pytorch/pytorch/blob/v2.6.0/c10/cuda/CUDAFunctions.h)
   只支持相应语义与实现，不替实例参数/依赖证明。
3. **实际性能解释**：P0性能与P1观测结构分开。Formal Request的P1−P0为+2.1013%～+106.6759%，
   N1净差有方向反转；不能统一扣开销、精确迁移组成或推出稳定收益。C0/Cpre单次copy差
   147.401031ms及Prefill差−13.477785ms均不是纯因果贡献。

标记风险是实质限制，不是装饰性免责声明：已有block1 G512的Host完成至point准备间隔
2.4938ms、marker调用49.7µs。它发生在完成后，不能当作同步前准备成本；不同clock的
记录与projection窗口须保留来源。小差可能受边界观测/顺序/Host准备影响，不能静默扣除
或按本次结果新增阈值。已有2～4ms个案不是所有新run的偏差上界。相同包装和顺序平衡
降低部分混淆，不消除profiler、缓存/分配或共享平台漂移。

最强反方意见：**强baseline已经解释关键事实；大wait只是额外同步与指标定义共同造成的
可预期现象，其幅度受P1扰动与运行波动影响，尚无独立的新机制或性能结论。** 当前证据
没有充分排除它。不预设wait随负载上升，也不以达到某个百分比证明方法成功。

## 5. 唯一待审下一步：8-profile反证首批，而非24-profile系列

**主要待证命题**：在固定输入/配置与Host-readable端点下，完成政策相关的Prefill预算
位置差能在轻/重两个工作量及相反执行顺序中重复观察，并经独立依赖/区间核对解释；
其可支持的结论是条件化结构而非自然内部等待或性能收益。竞争解释就是§4的
“已知同步位置变化＋P1/顺序波动，强baseline已经充分”。这不是把“更大wait”写成命题。

24条候选来自batch1/2/4×两政策×四block；中点与更多重复不能先解决贡献是否非冗余。
建议首批仅保留**batch1/4两个端点×C0/Cpre×两个完整block=8个P1进程/8条profile**。
这是贡献/可行性反证的待审Pilot设计，不是正式重复数选择或新Formal；旧实物不计入样本。

- 固定Windows/4090与当前软件/模型内容、FP16/eager/既定backend，512固定token输入、
  每样本输出2、warmup3/repeat1。batch4为四份相同输入的一次批量request，不是并发用户。
  两个政策均保持同一Host-readable端点/包装；Cpre仅测量首token复制前同步实际当前流，
  不切流、不改Decode/暖机。两负载已有独立工作量与局部可行性依据，不按wait选点。
  同负载同block两政策的实际每样本token逐值一致、输出数量/EOS及身份规则仍严格；
  缺失或冲突拒绝，不填目标值。跨batch的实际token差异照实保存，不预设相同或按其筛点。
- 预定顺序：block1为B1(C0→Cpre)、B4(Cpre→C0)；block2为B4(C0→Cpre)、B1(Cpre→C0)。
  每负载两次序均出现，负载先后也平衡。统计单位为**完整四run block，n=2**，不把8进程、
  kernel或token当作8个独立政策×负载重复；共享平台独立性/平稳性不能由编排保证。
- 记录全部Prefill原值、各A绝对预算/逐次占比/ratio-of-sums、GPU活动union、同窗常规
  count/sum/union与合法mapping、copy与sync包络、最后必要提交/活动及Host-ready/point。
  逐block报告Cpre−C0及两负载政策差的差中差，保留signed值；不做n=2 bootstrap精度声明。
  复用独立Raw区间/依赖预期，不用被测A/B产生oracle，也不单独新造评分/预测器。
- **只P1**：回答观测执行结构，不能检验P0收益或估计纯profiler成本。若日后必须联系未profile
  性能，最低结构要求是四种条件各有同期相同执行合同的P0/P1完整block；这仍不支持组成
  精确迁移，也不保证统计充分。该追加不在本首批/授权内，不把旧P0拼配新P1。
- 成本依据为旧driver192.687/261.610s与8槽历史外推：预估45～60分钟、预留5GiB临时空间；
  不是保证。沿既有collector300s/export180s/单driver900s硬限，固定8槽结束或硬失败就停，
  无重试/替补/自动续批，长期存储仍按既有归档后可恢复副本清理政策，不在运行中清理。

**只列实际接线差额**：现completion-path入口限定Engineering的512/batch4两槽；需在
方案获审后才绑定新的Pilot角色、batch1/4、block/顺序与局部消费者，复用现有hook/S/A。
相同支持域不因输入变化重跑完整Q0，但每个新run仍核后缀映射、实际流、边界/drain/
诊断。可证明只影响首ready之后的Decode缺口保留拒绝，不能界定则拒绝Prefill并停批。
本首批不发布Cpre自然默认流完整物理B，故不为B恢复旧probe或加设施；已有N1单sync B可
作为参照。未改变测量公式、registry、warning政策或opaque范围，不以未知填Host或零。

**预先固定裁决方法**：

- 逐run先由独立参照核对依赖/活动及预算，检查原始准入；这只是结果可用条件，不是贡献。
- 如果重复仅显示“长sync换短copy”，且增强baseline已经充分，则停止更大系列/引擎投入，
  维持限定测量与边界主张；不再把插同步、守恒或大占比称创新。
- 若两块出现可复核的条件化结构，清楚记录聚合指标的解释缺口及增强baseline的等价处，
  才讨论是否值得下一段有限研究；仍不宣布新理论、统计稳定或论文贡献已确立。小样本
  方向一致只是继续评估的线索，不保证效应；方向反转、零值或与观测延迟/波动难分则报告
  不确定，同样停止首批，不追采到显著。无样本删除、临场改点位或事后调质量阈值。

**当前实际下一步仅为协调审查这项收缩裁决及8槽预算/角色**。未生成脚本或包，未获新采
授权；不恢复旧四对B4追加方案、不默认启动任何实验。若目标必须是超过完整依赖时间线的
独占解释或完整自然Host阻塞，当前增量不足，应重新讨论问题而非继续设施建设。

本轮只读DOCX/原小回执及汇总，轻量CSV均值/原值算术与来源hash核对；不重跑完整分析、
Q0、测试、模型/CUDA/Nsight或服务器步骤。用户DOCX、Raw、旧BLOCKED、UNKNOWN/
NOT_ASSESSED及所有Gate/数据角色保持；只更新本文、科研进度和当前handoff/入口。
