# 完成路径的科学解释与限定重复方案 0.1

2026-10-13；研究问题/证据审查及**待审 Pilot 计划，不是新合同、签署或采集授权**。
Gate13限定PASS、Gate14 NOT_RUN保持。C0/Cpre现有资料仍是Engineering；旧BLOCKED、
Request/Decode拒绝、UNKNOWN/NOT_ASSESSED及原件不变。本轮无部署、采集入口或业务实现。

> 2026-10-13优先级调整：**下述四对追加Pilot暂停，不再是当前下一项执行。** 当前以
> [Device Exposure范围／Windows首引擎0.2](device_exposure_scope_and_windows_engine_v0_2.md)为入口；
> 本页保留已完成审查与历史待审方案，Cpre只作受控对照，不替代自然baseline。

> 用户本轮明确保留A_device_wait为操作性Device Exposure指标；“近似全部GPU相关Host阻塞”
> 仅是未验证假设，不是当前研究前置。下面历史引擎/完整等待讨论不授权Linux或语义扩展；
> 2026-10-14（7.156）：llama.cpp支线及交付暂停，既有工作保留；当前只读回到PyTorch
> 自然C0、独立受控Cpre及同完成政策负载比较，不恢复本页四对Pilot。现行口径见上述0.2入口。

## 1. 核心判断与证据—claim对应

**统一的是Host-readable completion语义，不是强制相同同步位置。** Cpre是可审计的复制前
同步干预，不能因其Device wait符合预期而替换自然C0/G1基准；否则会把干预制造的执行关系
当作自然模型事实。GPU活动增加不逻辑蕴含当前定义的Device wait增加。

未来可以另立“所有条件共同采用复制前同步”的**受控完成政策基准**，但须明确它测量的
是该执行政策下的模型，保持自然路径对照并另行版本化／取证；不能与现有自然Formal混合。
当时推荐不改主线基准、先做C0/Cpre重复；该追加步骤现已暂停。当前优先明确自然路径支持范围，
首引擎适用性现已暂停，仍保留C0自然基准及Cpre受控对照。
若论文目标是完整恢复所有GPU引起的Host等待，当前证据与支持域尚未达到，Cpre不能补齐
这个缺口；有限的依赖语义记账与完成政策解释目标仍可检验，不能把两种目标混写。

依据：当前[研究设计v7.1](../current/ExposedPath_研究设计.docx)§1.5、§2.3.7、§2.4及
[Pre-Pilot实验协议v2.1](../current/ExposedPath_实验协议.docx)第4章/§5.1；实际Formal范围由
[G12-ROUTEA/0.1.1](gate12_protocol_signed_v0_1_1.json)、已批准分域与后续窄域amendment限定。
Pre-Pilot文档不是该批Protocol Freeze；用户修改的DOCX未改写或纳入本次提交。

| 研究问题／组 | 实际证据与角色 | 当前允许claim | 不能据此推出 |
|---|---|---|---|
| 输入长度与activity/exposure：G32/G512 | 签署Formal：各六block；P0性能、同窗P1 A/常规baseline、独立Raw核验 | 本选点的GPU活动增加不唯一决定受支持同步暴露；自动、依赖语义明确的有限解释信息 | 输入域普遍规律、全部GPU相关Host阻塞、P1精确组成迁移P0 |
| 固定层干预：N0/Nmarker/N16 | 签署Formal：同显式流合同、六block；marker对照、具体W/terminal及合格单sync B | 区分必要先行工作、该sync的hidden/exposed、request/phase记账与局部干预；保留波动/不确定结果 | 跨sync加总B、自然默认流完整B、稳定加速、全部差值由sync造成 |
| 同路径batch负载：B1/B4 | Engineering一次P0/P1；B1完整、B4仅成功drain至首Host-ready局部闭合 | B4 Prefill GPU union较大，但token-ready sync交集仍可为零；批量invocation的个案 | B4 Request/Decode可信A、四个并发用户、统计收益；旧w11为Prototype且平台/算法不同 |
| 同负载完成路径：C0/Cpre | Engineering各一次、不同执行时点；局部结果0.1.1／分析323e912；实际输入/token一致 | 显式预同步内出现必要活动交集，copy包络缩短，A预算落点不同，与完成路径假说一致 | 精确恢复自然copy内部等待、单次总差因果收益、同期可重复性或补充Formal资格 |

Formal原值、signed成块比较、公平baseline与限制直接复用[最终审查](gate13_local_review_v0_1.md)、
[90窗A/baseline](gate13_a_baseline_v0_1.csv)、[102比较](gate13_contrasts_v0_1.csv)，不重新分析。
G1 API sum=union、Host补集在本数据未显示额外信息；N1 P0收益不确定。完整标准timeline加上
相同CUDA语义可以手工恢复这些解释，不声称Nsight没有这些信息或方法不可替代。

## 2. 定义、完成边界与跨引擎适用性

- Device wait是**合格同步Host区间∩有证据的必要活动并集**，不是sync总时长，也不是全部
  GPU造成的Host阻塞。已完成的必要成员仍保留，但交集可为零；时间重叠不产生依赖。
- CUDA API是互斥Host调用预算，可含未分离内部阻塞。submit/non-submit描述提交性质，
  不描述是否阻塞；同步优先级和union不变。成功opaque allocation只是明确成本标注，
  不制造W/B，不恢复其内部等待。
- residual是合格sync内未被必要活动并集覆盖的剩余墙钟，不是纯CPU、设备idle、
  返回尾或profiler开销；unattributed=0只说明当前记账证据规则闭合，不表示全部机制已解释。
- 当前没有网络流式发送；首/末token实际Host读取及随后可追溯point仍是完成路径。
  Cpre同步返回不替代首token完成；测得的point/记录延迟不是零。网络/反分词/IPC等位于
  核心窗口之外，是否由另一个进程承担由引擎架构决定，不能以进程位置自动划界。

**表述审查：** v7.1 §2.4优先级中的“其余…非阻塞CUDA API”是需要连同支持性规则阅读的
历史措辞，不能用于宣称所有API预算非阻塞。现行[non-submit解释](gate8_non_submit_api_review_v0_1.md)
及[opaque amendment](n1_opaque_allocation_v0_1.md)已有明确限制；
[当前Formal解释](gate13_local_review_v0_1.md)与[copy审查](gate13_cuda_api_storage_review_v0_1.md)
已区分这几层。本轮没有发现可由这些记录证明的“把整段sync当Device wait”等实现违例。
但若目标是测尽所有GPU相关Host阻塞，现方法证据能力确实不足，不能靠措辞宣称解决。
未注册的显式blocking语义、缺映射或依赖仍拒绝，不因任意API“可能内部阻塞”猜出W。
[CUDA12.4.1官方同步说明](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/api-sync-behavior.html)
支持Async名称不保证Host非阻塞；不是本轮改变分类的理由。

| 可保持一致的边界语义 | vLLM等引擎须重新确认的事实 | 当前不允许的捷径 |
|---|---|---|
| 内层模型request开始→首token可供Host使用→末token可供Host使用 | 开始点是哪一层、GPU输出转Host/跨进程传递在哪里、point时钟和延迟如何绑定同一request | 用同步返回、API返回、NVTX文字或HTTP TTFT代替实际Host-readable证据 |
| Prefill/Decode为首token分界的墙钟窗口 | chunked prefill／调度交错时，该窗口不等于“只执行prefill kernel”；origin与exposure owner分开 | 按forward函数名或请求排序猜ownership；强插sync令自然引擎适配现图 |
| 必要集合、保守互斥A与有效单sync B原则 | 实际线程/进程、流/context/event/graph依赖、异步输出与并发owner是否受支持 | 把当前单invocation主线程资格直接迁移到continuous batching／多进程 |

可移植的是**测量对象的语义定义和证据义务**，不是`.cpu()`/`synchronize()`调用模板。
vLLM可能需要不同boundary/identity adapter；若只能观测worker token-ready就明确是模型侧
端点，不能同时称frontend/client完成。新增同步会成为另一种执行政策，不是无扰动观测。
现阶段不实现引擎扩展；它属于后续完整栈适用边界，而非当前论文或Gate14的必做条件。
相同A类名也不保证不同完成政策／引擎的数值可以直接归因为硬件或效率差；比较必须明示
执行政策和端点层级。current模型batch4资格不自动解决引擎并发请求的ownership。
版本固定的架构依据仅作未来适用性审查：
[vLLM0.20.0架构](https://docs.vllm.ai/en/v0.20.0/design/arch_overview/)、
[指标端点](https://docs.vllm.ai/en/v0.20.0/design/metrics/)、
[V1调度说明](https://docs.vllm.ai/en/v0.20.0/usage/v1_guide/)。这些资料不授目标引擎资格。

## 3. Cpre残余的完整区间证据

复用[7.143原件及局部准入](batch_load_prefill_review_v0_1.md#7143-cpre闭合历史前缀修复与最终局部对照)。
Cpre执行401ed4209454，SQLite SHA256
`d3d96a1d9eda32fb2285e12e3fb4ef55cb2cdaa7b160303d9bcb5728562b614b`；
分析323e912，保存pair SHA256
`cde7c9101a5ca98b82f2c1472a6b4e8a9af80229a06d565c68f54d7bfe1a38e7`。
此次仅对已资格后缀做read-only Raw查询／半开区间算术，不重跑S/A或完整analyzer。

| 同一NSYS_TRACE_RELATIVE_NS时钟中的来源 | 原始区间／数值 |
|---|---|
| Runtime38583／corr200922／TID61308，成功`cudaStreamSynchronize_v3020` | [29174142522,29261789475)ns，87.646953ms |
| physical sync354，同目标PID59636/device0/context1/trace stream7 | [29174146448,29261785219)ns；A仍用Host API包络，二者不混换 |
| 1820个已证明request后缀成员及唯一terminal kernel11846 | 最后完成29261747457ns；不是完整物理W/B |
| 709个裁剪必要活动union区间 | 38.946574ms |
| 710个包络补集区间，合计residual | 48.700379ms |
| residual位于最后必要活动完成之前 | **48.658361ms** |
| residual位于最后必要活动完成之后 | **0.042018ms** |
| 后提交D2H347／后续helper sync355 | D2H[29262862619,29262863259)；helper[29262872572,29262878521)ns，wait0 |
| 首Host-readable完成point／NVTX row2 | 29263935689ns；不是新增sync返回 |

完整1820条Raw/table/rowid/correlation/提交引用、709个union及710个补集区间保存在忽略的
本地证据索引，摘要SHA256 `1995babc7f1c31d4ac3dcb0ef16768e70f2b21da32ab4995657de51fb335ee14`。
Raw/hash前后不变。残余绝大部分在terminal前：它表示那些时刻没有合格必要活动执行区间
覆盖，不证明GPU闲置，也不定位CPU、硬件、WDDM或profiler根因。terminal后的42.018µs
同样只是包络尾，不能纯因果归于返回开销。

## 4. 论文结果与限制提纲

1. **方法与正确性**：定义内层Host-readable窗口、支持的S依赖、五类互斥A与单sync B。
   展示独立oracle/Raw来源；守恒是必要QA，不是贡献证明。把当前适用范围写在方法正文。
   A_device_wait操作化Device Exposure而非全部Host阻塞；近似假设未获独立验证。
2. **Formal G1**：全部六block显示activity与支持同步exposure的条件差异；与同窗kernel/API/
   sync count、sum/union、合法mapping/launch-to-start比较。Host补集和API sum=union的
   无额外信息结果一并写入，不能挑有利phase。P0只报告各执行合同下未profile的性能，
   其中G1为自然路径、N1仍保留干预；P1解释相应观测执行。
3. **Formal N1**：保留Nmarker−N0、N16−Nmarker及实际allocation差异；具体W/terminal/
   hidden/exposed比单一raw sync更可审计，但标准完整timeline可复原同样信息。
   单sync不求和；P0净收益和细微稳定效应未得到支持，不能改为加速论文claim。
4. **补充Engineering完成路径个案**：并列C0/Cpre全部Prefill预算、GPU union、copy、
   sync wall／必要交集／residual／Host-ready，而非只画wait升高。
   现有copy差147.401031ms不是内部等待估计，Prefill差−13.477785ms不是稳定收益。
   该个案解释“同语义完成端点下，执行路径会改变可观察预算”，尚非重复或Formal证据。
5. **限制与反证**：零／反向／不确定结果保留；不主张全部GPU阻塞、完整硬件机制、P1→P0
   精确迁移、跨引擎泛化或Decision Gain。高质量论文的判断应依赖正确性与公平非冗余解释，
   不是大wait占比、图形直观或Gate PASS；本轮不宣称新颖性/录用层级已证明。

## 5. 待审同期Pilot：固定四对，不生成采集入口

目的：同一观测执行政策下，检验**复制前同步是否可重复改变可观察落点**；评估方向、
次序敏感性与扰动。不是估计自然copy内部等待，也不预设wait必须上升／copy必须缩短。

- 五个固定因素：现4090/软件内容身份；Qwen2.5-1.5B-Instruct/FP16/eager/SDPA声明；
  四份相同已冻结512-token输入；每样本输出2；warmup3/repeat1。batch4是一次invocation。
- 两条件：C0公共诊断包装、自然路径；Cpre相同包装，仅**测量Prefill首token Host复制前**
  在持有的实际执行流同步一次。无切流、无Decode/暖机干预。首Host-readable边界不变。
- **8个独立新run／8条P1／0个P0**，每run自有manifest、block/pair/variant/pass/request/
  attempt身份。旧Engineering只作设计依据，不充当本批样本。实际stream ID不能硬编码7，
  native handle=0不能判默认模式；保留真实映射、生命周期、成功drain与闭合历史证据。

| block | 相邻执行顺序 | 固定比较方向 |
|---|---|---|
| 1 | C0→Cpre | Cpre−C0 |
| 2 | Cpre→C0 | Cpre−C0 |
| 3 | Cpre→C0 | Cpre−C0 |
| 4 | C0→Cpre | Cpre−C0 |

顺序平衡只降低单向次序混淆，不消除共享设备漂移。不能把8进程或kernel当8个独立paired
样本；统计单位是4个完整pair/block，无跨批拼接。

**预锁定消费与比较：**

1. 逐run保留准备/预检、真实入口/异常/退出、配置/输入hash、四样本两个实际token、
   暖机实际次数、窗外drain、共同clock原锚点、实际同步次数和Raw/REP/SQLite/诊断。
2. 仅Prefill局部准入：成功drain→首ready完整后缀、已观察submit实际效果／归属、各sync
   correlation/成功状态/必要集合／closure/唯一terminal；两默认模式必要成员、边和
   terminal一致方可投影。已完成前缀不被伪装成本次物理W；不授完整物理B。
3. 主比较固定为四个block的Prefill **Device wait绝对ns变化和首token copy API时长变化**，
   共同展示sync wall/residual、Host/CUDA API总预算、Prefill总时长及GPU活动union。
   同时列逐run比值与ratio-of-sums，二者不混用。末次必要提交、最后活动、D2H、前置/
   helper sync及Host-ready时间线全报；后提交D2H不进入前置sync集合。
4. 常规baseline使用**同一P1 Prefill、clock、registry与合格原记录范围**：API/kernel/memop/
   sync count、裁剪sum/union、GPU union、合法correlation mapping及已有launch-to-start。
   缺字段/映射为unknown；不能少给baseline信息制造优势。完整timeline公平展示。
5. 输出全部四对原值、signed差、均值/中位数/范围、两顺序分层和留一敏感性；不做显著性
   追采，不用bootstrap次数宣称精度。4对是有界可重复性Pilot，不是效应power证明。
   稳定同向只支持该P1/负载的有限观察；混合或反向即相应结论不确定／不支持；raw sync
   本已足够解释的部分明确记录无额外信息。无P0，不能判断自然性能收益或profiler成本。
6. 同一已证明在首ready之后的Decode效果缺口，仍记Request/Decode BLOCKED，可以与合格
   Prefill分开报告；**不能按phase标签自行隔离**。缺口影响到前缀或无法界定、身份/输入/
   token/流/clock/边界冲突、失败sync、必要mapping缺失、新诊断影响不明、OOM/超时/
   collector/export失败均立即停止后续槽。保留partial及未执行清单，不retry/替补/补齐block。
7. 第8槽／第4完整block结束即停审查，接受合法零／反向／copy不缩短／总时长增加。
   不因结果扩大batch/output、追加block、改A或清除UNKNOWN。

**真实接线差额（规划，不在本轮实施）：** 现`completion_path.schedule()`只有Engineering
C0→Cpre两槽，局部reader也限定该role；不能执行四次旧入口后把名称改Pilot。
下一次实现仅需版本化Pilot用途/八槽block-pair顺序贯通manifest→producer→局部reader→
汇总，复用同一hook/S/A、旧Engineering路径与拒绝门，并用CPU文件链检验错role/顺序/
次数/输入/失败即停。没有新增模型行为、analyzer、监控、CUPTI或完整Q0义务。
普通接线与固定包应在此计划获审／预算获批后准备；当前无可启动脚本或部署包。

## 6. 时间、存储及后续Formal边界

实际旧collector为36.859/38.625s；完整driver261.610/192.687s（包括分析/严格消费，
不同执行版本且不是纯模型时长）。八槽机械外推25.7～34.9分钟；计入prepare、封包与
机器波动，**待审预算45～60分钟**，不是保证。沿现collector300s、单export180s、
单driver900s硬停，无自动超时扩大。固定8进程/8profile，不含补跑。

此次仅盘点两个既有局部run，不扫描服务器：封存展开分别16,281,529/9,445,860bytes；
两个新派生目录合计23,748,238bytes。按同规模窄域产物估计八槽展开约0.3～1GiB、
最终ZIP约0.05～0.25GiB，**预留5GiB临时空闲**（包含压缩/副本安全余量，不保证上界）。
不用此前Formal大型domain缓存；单run写完即释放对象，不能为本计划再构建全批常驻域。
长期YLQ目标是**50GB十进制**（约46.57GiB），临时峰值单列；当前实际总占用／旧清理回执
尚未在本轮取得，不能把候选38.95GiB或估算34.38GiB当成已释放／当前事实。
采集/分析结束、单ZIP与完整清单核验后才另行列精确可恢复副本清理清单；Raw/失败现场/
manifest/来源与最终汇总保留，不在运行中清理，也不顺带删除其他Gate。

现有签署Formal G32/G512/N1结论可保留；C0/Cpre不能以改role、事后修复或本Pilot计划
升级Formal。若需要论文的**补充Formal完成路径证据**，最小增量是：

1. 先审本Pilot的角色接线与局部资格，评估这四对是否足以选择有限claim/固定预算；
   不能将它改名为Formal，也不保证它足够冻结重复数。
2. 新补充协议明确512/b4的Prefill-only研究对象、Cpre干预、同窗公平baseline、固定次序/
   统计/排除/预算与上述限制；签署后新采。原G12/0.1.1五条件、batch1及Formal结果不改。
3. 仅做受影响身份/role/实际流与局部投影资格增量，复用独立S/A、闭合历史和两模式证据；
   不授Request/Decode、完整B、vLLM或全新版Q0。若核心测量语义实际变化，再集中裁决。

**历史计划停点（已暂停，不是当前下一步）：协调审查本四对Pilot的问题、八槽/45～60分钟/5GiB预算和角色
接线范围。** 现行下一步见顶部0.2入口；当前用户无需服务器操作。不是重开Gate13，
不是进入Gate14，更不是为得到较大Device wait而变更自然基准。
