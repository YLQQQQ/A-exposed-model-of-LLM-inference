# Device Exposure解释范围与Windows首引擎核对 0.2

2026-10-13；依据用户本轮明确决定的**解释/研究范围收敛**，不是测量合同amendment、
新资格或采集授权。取代[0.1方案](natural_completion_engine_applicability_v0_1.md)的现行
优先级和Linux前提；原审查/数据角色/失败判定保留。Gate13限定PASS、Gate14 NOT_RUN。
四对C0/Cpre追加Pilot暂停；不安装、部署、采集、重算旧结果或修改用户DOCX。

> **2026-10-15课题整体投入建议（7.160）**：见[AI模拟导师预审0.1](ai_supervisor_topic_review_v0_1.md)。
> 推荐限定方法/测量与适用边界论文候选的成文收口，不追加技术/实验预算；不是已确认发表
> 增量或导师认可。下述路线B停止结论保留，不等于整个课题失败。下一项仅将已形成的
> 主张/证据交真实导师确认范围与要求，不自动恢复任何技术支线或改写旧Formal。

> **2026-10-14当前优先级（7.156）**：暂停llama.cpp扩展、交付及目标机资格工作；
> 保留已完成的本地SDK接口修复与历史现场。下文§3～4仅保留先前引擎方案，不再是执行指令。
> 当前只读回到PyTorch自然C0与独立受控Cpre，现行路线见下节；不改baseline、合同或数据角色。

> **2026-10-15当前终态见[同一决策稿0.3（7.159）](pytorch_research_feasibility_decision_v0_1.md)**：
> 用户批准的一次本地方法检查已结束，限定必要关系可行且已核验24次自然token；未得到
> 足以新增方法投入的负载解释增量。唯一建议停止扩大路线B，不追加受控GPU验证/设施。8/24-profile、
> 四对方案及引擎支线均不恢复。保留已有限定方法与Formal成果，不称新立项贡献已成立。
> 无新采/语义授权，原Formal、测量定义及下文解释边界不变。

## 当前PyTorch路线：完成政策、负载与可支持的解释

**自然C0作为执行baseline。** 固定输入已驻留GPU、成功窗前drain返回后开始request；
forward→argmax→token-ready标记/Host准备→`.cpu().reshape(-1).tolist()`→实际Host token值
及完成point。Prefill终止于首token可读，Request终止于末token可读，Decode为两者之间的
半开窗口；文本输出/网络发送不在其中，当前未实现实际流式发送。源码见
[runner完成helper](../../exposedpath/runner.py)及[MC0.2 §4](measurement_contract_v0_2.md#4-requestprefilldecode-与-token-就绪)。
helper内部已观测复制/同步的顺序与依赖须按实物恢复；D2H结束不等于`.cpu()`已返回，
NVTX也不独立证明GPU完成。自然路径的API预算可能含未分离内部阻塞；后续合格同步入口前
必要活动已完成时，Device wait可以为零。这与当前有限指标一致，不证明不存在GPU相关Host阻塞。

**Cpre是独立受控完成政策，不是修正后的自然baseline。** 同一负载下，仅在测量Prefill
首token复制前同步实际当前流，仍以实际Host token可读作为完成边界；Decode未改。
实际接线见[completion_path](../../exposedpath/completion_path.py)。它检验完成政策改变后，
可观察同步暴露、API预算与residual如何迁移；不能用复制API差值精确估计原内部等待，
不能由一次结果推断稳定收益，也不能拿Cpre替代自然G1或将不同政策混作负载效应。

**同政策内的负载比较已有两种证据，不需先补引擎或改完成路径。**
[Formal收尾](gate13_closeout_v0_1.json)的G32/G512固定batch1/输出2，检验输入长度；
[B1/B4局部审查](batch_load_prefill_review_v0_1.md)固定输入512/每样本输出2，检验batch，
batch4是一次批量request，不是四个并发用户。后者只有Prefill局部Engineering资格，
Request/Decode拒绝保留。比较时同时呈现绝对A预算、逐次占比、总时长、GPU活动并集、
同窗常规指标及同步/复制时间线，不能以较高Device wait选点或要求它随工作量单调增加。
Formal与Engineering不能合并为重复，P1组成也不能精确迁移到P0。

已有证据能支持“活动量与合格同步暴露不是同一个量”；C0/Cpre个案记录了不同完成政策下
的预算位置差异，仍不能排除运行波动，或将全部差值因果归于新增同步。
独立Q0/受控资格支持定义内的依赖与记账正确性，不支持完整Host等待识别或任意负载趋势。
7.159本地方法检查已判定：**目前只闭合完成必要关系，没有独立的整段负载约束解释**；
重复Cpre图形或理想正例不能补足迁移证据，故停止该方法增量投入。B4整request缺口不阻断已闭合Prefill，
本轮不重新追索84次调用、w11或旧UNKNOWN，也不恢复四对Pilot。

**路线B的技术停止点仍是7.159；整体投入建议见7.160。** 不再等待7.158同一次检查的再次授权。保留已有
Formal和Engineering解释材料；不新增测量字段/资格层，也不制造下一轮服务器任务。
重新选择研究主张须另有判别依据，不自动改baseline、冻结定义或Formal资格。
Gate13限定PASS及UNKNOWN/NOT_ASSESSED保持。

> 本地接线与固定SDK接口校正现见[native候选0.1](native_llama_window_and_adapter_v0_1.md)。
> 固定头文件的普通batch入口为`llama_decode`；本页先前`llama_process`为接口简写，不能
> 直接用于编译。原指标/证据结论不变，target native资格与新窗口仍未授予。

## 1. 核心指标、假设与不变的拒绝规则

`A_device_wait = 合格同步区间 ∩ 根据完成语义恢复的必要GPU活动区间并集`的区间长度，
仍按既有request/phase裁剪、同步优先级与互斥union规则记账，不逐sync直接相加。
W(s)来自成功completion语义、提交顺序、真实设备/context/stream/event及ownership证据，
不是“刚好重叠的活动”，也不是只取pending成员。物理W及获准的局部投影范围不能混用。

**Device Exposure是操作性建模指标**：回答在该支持域、执行政策和观测执行中，有多少
必要设备活动执行区间暴露在合格Host同步区间内；不直接回答全部GPU相关Host阻塞、
硬件因果、反事实可消除时延或自然P0的精确组成。这里“指标正确”指相对于明示定义、
支持假设和证据义务正确，不是凭定义证明它等于潜在的全部等待。

“该指标大致等于全部GPU相关Host阻塞”仅保留为**未验证的近似假设**，不是既有结论、
准入前置或选点目标。当前资料没有独立的全部阻塞ground truth，不能给出近似误差；
自然API内可能阻塞及大residual表明不能仅由A数值替该假设背书。
本轮不新增“完整等待”指标、阈值、采集设施或验证任务。

同步copy及依参数阻塞调用的registry支持缺口仍见[MC0.2 §6](measurement_contract_v0_2.md)
和[0.1审查](natural_completion_engine_applicability_v0_1.md#1-自然token复制的裁决c有明确的合同解释缺口)。
已批准的异步copy submit记账不证明非阻塞，也不是新opaque-copy许可。
实例若已确定属于未支持completion，或必要身份/边界/提交映射/依赖/诊断影响不能确定，
仍按原规则拒绝；影响可界定的局部缺口仅按既有合同处理，不能用“建模”豁免、填Host、
猜W/B或追认旧结果。opaque cudaMalloc窄域规则也不自动扩用到其他API/引擎域。

## 2. 论文现行口径与已有证据

建议方法正文表述：

> ExposedPath依据可核验的同步完成语义恢复必要GPU活动集合，将其在合格同步区间内的
> 执行交集作为Device Exposure的操作性预算；通过request/phase互斥记账及单sync
> provenance，检验其相对于同窗口常规活动聚合指标的有限解释价值。

PyTorch自然路径保留为**执行baseline**；信息增益对照是同一P1窗口/clock/registry/记录
范围的API/kernel/MemOp/sync count、sum、union、合法mapping及完整时间线。
Cpre是完成政策的受控机制对照，不是自然baseline或方法“修好全部等待”的证明。
P0性能、P1机制及配对扰动分开；不从A扣P1−P0，不跨同步累加B。

| 证据与角色 | 已支持什么 | 未显示额外增益／未支持什么 |
|---|---|---|
| 历史Q0与限定资格、独立正反例 | 支持域内W/terminal、交集与union、具体A/单sync B及拒绝行为的正确性 | 不授未测试native域、全部等待ground truth或新版本全资格 |
| 签署Formal G32/G512，六block | GPU活动总量不能唯一决定有依赖证据的同步暴露；wait差有正负方向 | API sum=union及Host补集在本数据未显示额外信息；不支持输入增加必使wait增大 |
| 签署Formal N0/Nmarker/N16，六block | 完整先行W、terminal与单sync hidden/exposed给出自动可审计的有限归属信息 | 标准完整timeline加同CUDA语义可手工恢复；不支持稳定P0收益或所有E2E差由干预解释 |
| B1/B4局部Prefill、C0/Cpre，Engineering | 同路径负载及完成政策可改变已观察活动/预算落点；自然copy预算与后sync交集不同 | 不授B4/Cpre Request/Decode、完整物理B；单次结果不证明普遍规律、精确内部等待或统计收益 |

结论与原值直接引用[Formal最终审查§4](gate13_local_review_v0_1.md#4-信息增益有限支持与负结果分开)、
[同窗A/baseline](gate13_a_baseline_v0_1.csv)、[预定signed比较](gate13_contrasts_v0_1.csv)、
[单sync B](gate13_single_sync_b_v0_1.csv)及[局部完成路径审查](batch_load_prefill_review_v0_1.md)。
没有重跑分析。守恒、零unattributed、Gate PASS及大wait都不能替代信息增益判据。
不宣称方法提供了标准trace没有的信息，或已证明相对完整timeline的独占优势。

现有Cpre新增sync（Engineering局部投影）墙钟87.646953ms，必要活动交集38.946574ms，
residual48.700379ms；后者48.658361ms在最后必要活动完成之前、0.042018ms在之后。
这三个量不是同一个对象，residual不是纯CPU/返回开销。
自然C0首copy148.126383ms、Cpre首copy0.725352ms；差147.401031ms不是内部等待估计。
自然block1/G512 copy1.874498ms及其后sync35.553µs是另一个实例，不与C0混为同一次。
CUDA API预算可能含未分离阻塞；submit/non-submit不等阻塞/非阻塞。
数值及区间均复用[已有解释§3](completion_path_scientific_review_and_pilot_plan_v0_1.md#3-cpre残余的完整区间证据)
和原局部审查，不生成新数据。Cpre只说明干预后的预算落点，与自然内部等待不可识别并存。

论文组织保持“定义/独立正确性→全部Formal比较与公平baseline→Engineering机制个案→
支持域和负结果”；不挑大wait图替代自然结果，不把P1组成迁移到P0，不授Decision Gain。
已有论文提纲在[解释文档§4](completion_path_scientific_review_and_pilot_plan_v0_1.md#4-论文结果与限制提纲)，
本页是其现行口径覆盖层；没有独立论文正文可同步，用户DOCX保持原样。

## 3. 历史待审Windows首引擎：固定源码的自然完成链（当前暂停）

当前仅既有Windows Server/4090；Linux、WSL、换服务器、升级driver均未授权。
vLLM仅作未来候选，不是当前阻塞。首候选llama.cpp v0.6.0的
[真实commit](https://github.com/ggml-org/llama.cpp/commit/d81235049384534c167caea52b85a694f6103d14)
为`d81235049384534c167caea52b85a694f6103d14`。本轮只查官方固定源码，未下载/安装引擎。

| 固定源码与位置 | 已核验的调用关系 | 目标机尚不能由源码代替的事实 |
|---|---|---|
| [simple.cpp L173/L182](https://github.com/ggml-org/llama.cpp/blob/d81235049384534c167caea52b85a694f6103d14/examples/simple/simple.cpp#L173) | llama_process后调用llama_sampler_sample取得Host token；之后才文本化/打印 | 不直接采用CLI含打印的计时；实际token/EOS/输入与产物身份须绑定 |
| [sampler L833](https://github.com/ggml-org/llama.cpp/blob/d81235049384534c167caea52b85a694f6103d14/src/llama-sampler.cpp#L833) | sampled-token/getter先读取；无backend token时转Host logits采样 | backend采样和CPU采样分支必须显式固定，不凭配置猜实际分支 |
| [context L699/L1784/L3736](https://github.com/ggml-org/llama.cpp/blob/d81235049384534c167caea52b85a694f6103d14/src/llama-context.cpp#L699) | 输出有异步get；getter调用context synchronize→scheduler synchronize | Host-ready锚点应在真实token取得之后，不用llama_process返回或NVTX作完成证明 |
| [scheduler L2004](https://github.com/ggml-org/llama.cpp/blob/d81235049384534c167caea52b85a694f6103d14/ggml/src/ggml-backend.cpp#L2004) | 遍历实际backend的synchronize | native工作线程/CPU backend及跨stream event关系，不可默认全属主线程 |
| [CUDA backend L2327/L2405](https://github.com/ggml-org/llama.cpp/blob/d81235049384534c167caea52b85a694f6103d14/ggml/src/ggml-cuda/ggml-cuda.cu#L2327) | D2H走cudaMemcpyAsync；该backend同步走实际stream的cudaStreamSynchronize | handle→context/trace stream/device、完整必要成员与terminal需实物桥接；不要求wait非零 |

此链是引擎原有完成行为，不添Cpre。异步copy在先、getter同步在后，也可能出现API预算
较大而后sync交集很小；不能从源码预言占比或把C++方法的总时长全算Device Exposure。
重复getter同步和框架其他同步全部照实保留，不为提高wait减少/移动它们。

[Windows构建说明](https://github.com/ggml-org/llama.cpp/blob/d81235049384534c167caea52b85a694f6103d14/docs/build.md)
支持VS2022；[固定CUDA CMake](https://github.com/ggml-org/llama.cpp/blob/d81235049384534c167caea52b85a694f6103d14/ggml/src/ggml-cuda/CMakeLists.txt)
接受Toolkit并含sm89路径及GGML_CUDA_GRAPHS开关。候选保持CUDA12.4/MSVC14.38/现driver，
限定单GPU、禁CUDA Graph子域；源码可行性不等目标构建已通过，不自动取较新CUDA预编译包。
实际CMake/依赖/二进制/构建参数尚待锁定，失败就报告具体阻塞，不升级平台迁就方案。

[固定Qwen2转换器](https://github.com/ggml-org/llama.cpp/blob/d81235049384534c167caea52b85a694f6103d14/conversion/qwen.py#L45)
识别Qwen2ForCausalLM；候选HF→GGUF F16是非量化表示，不是HF字节或数值等价证明。
须保留HF权重/配置/tokenizer来源hash、转换commit/参数、GGUF hash及实际tensor类型；
输入用固定token内容，不让chat template/BOS自动改变输入；P0/P1逐值核对，不要求与HF
生成token必然相同。不据转换后的时延做旧HF的同口径引擎排名。

## 4. 历史引擎方案及有限资格增量（当前暂停，不执行）

下一项本地工作是**写清native窗口/identity adapter的最小声明并对接现有文件链**，
不是新collector或完整Q0：首次原生model process调用之前记录start，在首/末真实Host
token取得后记录ready；加载、分词、暖机、窗前成功drain及输出持久化在窗外。
自然process包含input preparation/H2D，不能直接宣称满足旧MC0.2的GPU-resident起点。
该起点差异及native多线程ownership须先形成窄域边界/支持声明供裁决；不得暗插同步、
预执行model或把Host logits可读等同已取得token。三个半开窗口公式可复用，具体起点
资格和引擎域不自动继承。NVTX只投影真实事实；文本、网络、客户端TTFT不在当前模型窗。

已能复用：既有Raw/S/A/B公式、受支持stream/event语义、设备identity规则、独立oracle
的相应不变量及官方同类warning处置。实际增量仅为native PID/TID/request/token ledger、
Host-ready clock引用、实际stream/context/correlation/event生命周期及已观察依赖闭包。
未知来源、相关默认流模式歧义、缺活动效果或未支持completion仍拒绝；不授完整物理B。

未来待审目标步骤只须：固定构建/转换/模型身份→必要的同路径受控桥接→一对自然P0/P1
（首例建议32/2、batch1、warmup3/repeat1、单GPU隔离request）。桥接须有独立已完成
前缀/后提交/错流/缺映射等预期，不能只验守恒。实际预算和包在声明与目标构建依赖锁定后
再审；现在无服务器命令、部署包或采集授权。接受零wait、API主导及无额外增益。

本轮只做解释/来源与文档检查；测量实现、schema/registry、签署0.1.1、Raw/历史报告及
资格判定均不变。真实引擎资格尚未取得，不重开Gate13、不启动Gate14或追加C0/Cpre Pilot。
