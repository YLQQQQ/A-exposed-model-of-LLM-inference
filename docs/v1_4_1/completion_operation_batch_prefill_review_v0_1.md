# 自然B1/B4 Prefill：完成操作候选演算与研究决策 0.1

## Material Passport

- Origin Skill / Mode：research-protocol、ARS experiment-agent / bounded validate。
- Date / Version：2026-10-16；`COE-BATCH-PREFILL-EXPLORATION/0.1.0`。
- Verification Status：ANALYZED；独立区间算术已核对，不是新GPU验证或研究规律验证。
- 角色：原Engineering；新结果为`EXPLORATORY_POSTHOC_BUDGET_PREVIEW_NOT_FORMAL_A`。

7.166展示补充（2026-10-16）：依据用户重发的完整五项要求，复用7.165演算，只补占比、
来源时间线与选定Raw记录复核。唯一分析对象仍是同一2af14b批次的B1P1/B4P1，不用C0/Cpre
替代；无新实验/协议/生产改版。下文未获授权的后续建议不是本次执行任务。

**裁决：B1/B4首token完成操作符合固定COE通用条件，可作本轮事后演算；不是继承99f3bae的
profile资格。现有证据支持继续研究自然完成操作的必要活动暴露，但不支持“全部GPU阻塞已测准”
或稳定负载规律。下一步不扩展大矩阵，优先以小规模独立重复检验解释增量。**

## 1. 适用性：先核对来源，不凭较大交集放行

本轮开始基线`098efde4e9455b279454c97470d114b765cbb263`。
使用[COE-CANDIDATE/0.1.0-draft](completion_operation_contract_draft_v0_1.md)作为固定探索规则，
其SHA256为`0dd73d0f95a3947263236eeb17fb4ff2f6a9b046e9894f85280db6e0fb0927a8`，未修改或签署。
原件`batch_load_2af14b11dd99_engineering.zip`为103,907,198 bytes，SHA256
`b290a96f85d68c54adf8f9be0705fce2f188d4dffc8e98b44f7b6d5a909b8494`；清单SHA256
`157ff32769bb569ef1982ba3daa2846dbe06979a10e8330a9720a648f2ea4998`。
本次核对ZIP/清单身份、安全路径及258项清单覆盖；复用7.136已完成的全包CRC/全部hash，
只重新读取消费成员并核对CRC、清单/receipt hash和原展开字节，不解压巨型domain。

复用[已批准B1/B4局部审查](batch_load_prefill_review_v0_1.md)，但逐实例再核对：

- 执行`2af14b11dd990d159ff0b3204d26a1527244079c`，旧局部计算`dc78fc881157a4078c4a6c9f8f34c724140f4660`。
  本轮只读SQLite及小型成员/边证据，不调用生产S/A/B或旧domain reader。
- 两组固定512/每样本输出2、w3/r1、FP16/eager/SDPA、torch2.6.0+cu124；B4是一次四样本
  批量request，不是四个并发请求。实际首token分别为`[29184]`和四个29184，后token分别为
  `[6556]`和四个6556；原P0/P1逐值一致，实际shape/数量/EOS与manifest/producer绑定相符。
- 两份实际runner源码SHA均为`a0e3e0cb9ee518b8bbb1c4a348e597e7984c23a0cebacc6de4ed88754bfe09f3`。
  `observe_token_ready_boundary`函数AST与99f3bae同函数一致：NVTX push→
  `detach().cpu().reshape(-1).tolist()`→Host整数token→clock/实际completion记录→finally NVTX pop。
  此顺序证明为何完成point在range内部；NVTX range结束不是完成操作边界，更不独立证明GPU完成。
- 本批是独立Engineering执行，非原99f Formal；B1为8-byte、B4为32-byte Device→Pageable，
  根据各SQLite自己的enum解释。原profile的固定cohort/单样本资格**不继承**。
  记录`operation_validity=VALID`（在声明支持假设下）、通用操作条件MATCH；原profile资格为
  `NOT_QUALIFIED`，不授新Formal或通用batch资格。
- 同进程实例/主线程/clock、唯一copy/sync、成功返回、correlation→D2H/physical sync、实际
  context/FIFO、UUID/PCI设备桥接、窗前成功drain、Host token值均可核验。physical3/logical0/
  activity0/inventory2来自桥接，不按编号相等；实际context1/trace stream7不替代模式证据。
- 原成功drain闭合历史前缀：B1 10,827条、B4 10,491条；保留原ID，不伪造request ownership。
  必要后缀分别1,905/1,821条，其中1,893/1,295条在copy入口前已完成，仍保留为成员。
  捕获截止为配对sync，不是copy入口，故包络内提交的D2H纳入；后提交排除。
- 逐成员唯一成功submit及scope核对；与原LEGACY/PER_THREAD后缀的成员、依赖边和terminal一致，
  不是因为两模式算出同值才放行。无可见incoming/event/graph冲突；不存在未记录incoming
  依赖仍是既有支持假设，不授自然默认流完整物理W/B。
- 原B4缺效果调用在首ready之后、影响局限的证明复用7.139，不再次追索参数。本次只计算
  Prefill，**原B4 Request/Decode及attempt继续BLOCKED**。诊断沿已有官方同类处置，
  UNKNOWN/NOT_ASSESSED不变，不将它们当零丢失。

## 2. 完整两条件演算（ms，除注明外）

固定`I=[copy runtime入口, 配对成功stream sync返回)`，不以GPU起点/Host marker移界。
Q为I与该次合格必要后缀活动union的交集，不是copy API时长减D2H。
旧Device wait是整个Prefill的冻结结果；“原配对sync交集”仅是末尾token-ready那一次。

各行单位ms，括号统一为占各自**原Prefill窗口**的比例；它们不是互斥项目，不能相加。
只有§3的预算overlay作互斥守恒检查。操作补集也不是整个Prefill的补集。

| 实物/派生量，ms（占原Prefill %） | B1 | B4 |
|---|---:|---:|
| Prefill原窗口总长 | 100.116413（100.000000%） | 152.587591（100.000000%） |
| 全Prefill GPU activity union（非A） | 52.541659（52.480565%） | 104.121389（68.237127%） |
| 原Prefill Device wait | 0.525502（0.524891%） | 0.025024（0.016400%） |
| 首token copy API墙钟 | 1.868619（1.866446%） | 43.854908（28.740809%） |
| 配对sync墙钟 | 0.027852（0.027820%） | 0.040571（0.026589%） |
| 原配对sync交集 | 0.000000（0.000000%） | 0.000000（0.000000%） |
| 操作I墙钟 | 1.897322（1.895116%） | 43.897532（28.768743%） |
| 候选Q交集 | 1.782176（1.780104%） | 30.910044（20.257246%） |
| └ 必要kernel并集 | 1.781280（1.779209%） | 30.867774（20.229544%） |
| └ 必要MemOp并集 | 0.000896（0.000895%） | 0.042270（0.027702%） |
| └ 其中D2H | 0.000544（0.000543%） | 0.000416（0.000273%） |
| I补集（非纯CPU成本） | 0.115146（0.115012%） | 12.987488（8.511497%） |
| 预算预览：旧Device wait ∪ Q | 2.307678（2.304995%） | 30.935068（20.273646%） |

[完整占比CSV](completion_operation_batch_prefill_percentages_v0_1.csv)逐值保留整数ns、分母、
原结果/SQLite hash，百分比只是显示派生，不是新质量阈值。

两组Q全部位于copy API内，没有与旧sync交集重叠；本批kernel/MemOp无交叠，但一般情形
必须union并保留mixed，不能默认相加。B1来源为10 kernel＋1 memset＋1 D2H；B4为516 kernel＋
9 memset＋1 D2H。**新增主要来自先行kernel，不是把整个43.854908ms复制API改称等待。**

可逐条核验的原trace时间线（绝对ns，不与Host时钟相减）：

- B1 PID52532/TID30804：copy runtime37815/corr197682，`22417152902..22419021521`；
  D2H347 `22419004006..22419004550`；sync37816/corr197683/physical354，
  `22419022372..22419050224`；首Host-ready `22419841194`。最后必要活动为D2H，早于sync入口。
- B4 PID65008/TID59500：copy38583/corr200922，`23649330213..23693185121`；
  最后必要kernel11846于`23693053659`完成；D2H347 `23693055035..23693055451`；
  sync38584/corr200923/physical354，`23693187174..23693227745`；首Host-ready `23694390270`。
  kernel和D2H在该sync入口前完成，但有30.910044ms必要活动落于I内。

![同批B1/B4自然Prefill完成子包络及尾部放大，来源为原SQLite记录](figures/completion_operation_batch_prefill_v0_1/source_timeline.png)

图只展开完成操作附近；只画与I相交的成员，不把它们冒充整个W。全部必要成员、早完成
成员与闭合历史仍在7.165的原清单中。虚线是固定copy入口/paired sync返回；横轴仅为
**显示用**copy-entry偏移（两panel比例不同），各自原点ns已标明；不修改原trace时间，
不作Host/trace时钟拟合。黑菱形为Host结果之后发出的原trace token-ready point，不是
CPU实际读取token的精确瞬间，也不由NVTX独立证明GPU完成。

[原始时间线CSV](completion_operation_batch_timeline_v0_1.csv)保存两组Prefill/drain、最后
kernel及其launch、copy、D2H、runtime/physical sync、原completion point的绝对ns、
record/correlation和SQLite hash。新增展示逐条核对copy/D2H/runtime和physical sync、最后
kernel及其launch、原completion point；Prefill/drain复用已绑定的7.165结果。成员与算术
验证同样复用，没有重算S或据几何重叠生成依赖。

“旧sync交集为零”和“自然完成操作期间有必要GPU活动”可以同时正确；它们测的是不同对象。
不能反推旧分析算错，也不能由重叠认定copy内部Host净停顿。API间隙、GPU空隙及库/观测
成本均可能在补集中，现有证据不作CPU/驱动归因；I也不是整个`.cpu()`或完整Host读取范围。

## 3. 候选预算：同墙钟迁移，不另加GPU时间

沿用原Prefill窗口。Q与全部相关Raw同步包络不交，结合旧E必在同步包络内，证明`Q∩E=∅`。
共538个互斥迁移片段（B1 12、B4 526），逐片段旧owner唯一为copy submit API。
未碰Host、non-submit、residual或unattributed，原API count/sum/union baseline不改。

- B1预览H/C/完成暴露/residual/U为
  `45.683467 / 51.989182 / 2.307678 / 0.136086 / 0`ms；
  C的submit/non-submit为`50.397399 / 1.591783`ms。
- B4对应为`69.544101 / 51.985255 / 30.935068 / 0.123167 / 0`ms；
  submit/non-submit为`48.557345 / 3.427910`ms。

两组总长及API父子守恒严格保持。迁移后API预算接近只是本次实值，不证明Host API成本
对batch不变。新字段是独立完成暴露预览，不能拿它替换旧A_device_wait或与原API全长相加。
本轮未计算/发布B4 Request、Decode或新物理B，不能把仅Prefill守恒当完整request准入。

既有[预算迁移图](figures/completion_operation_batch_prefill_v0_1/budget_preview.png)保持原样。

完整[两条件数值/来源/旧新预算CSV](completion_operation_batch_prefill_v0_1.csv)及
[538片段迁移清单](completion_operation_batch_migration_atoms_v0_1.csv)保留整数ns与Raw引用。
独立事件扫描（不调用候选union函数）得到1,782,176/30,910,044ns；反向预算重构一致。
消费的28项来源后验hash未变；没有重跑完整analyzer/Q0/pytest或新GPU实验。
原完整归档、Raw、报告、用户DOCX、Gate13限定PASS及Gate14 NOT_RUN保持。

## 4. 配置数量与可信程度：现在缺什么

**配置少限制外推，不自动否定实例证据；配置多也不能代替独立重复。** 本次每条件仅一条
P1，能验证这个执行实例的配对、依赖和区间，不能估计batch规律的运行间方差/稳定性。
同一B4内四个样本、516个kernel或多个sync不是独立重复。旧G32/G512六block的
[24链探索](completion_operation_budget_preview_review_v0_1.md)不能与本批混作同一政策重复：
它们是不同执行版本/批次/角色，原Formal并未冻结COE。本轮没有按有利数值选择Prefill；
局部窗口及其准入在7.139先于本候选已确定，B4其余失败完整保留。

既有Host-ledger Prefill P0/P1分别为B1 `72.3051/100.9650`ms、B4 `167.7821/152.4430`ms，
配对差`+28.6599/−15.3391`ms；这是Host钟原时长，不与上表trace投影T混算。
一次波动/观测扰动没有分离，不能把本次P1结构迁移为P0精确组成或纯负载因果效应。
零未知、守恒、较大占比和符合预期都不是重复性/创新判据。

## 5. 唯一研究建议与待审最小下一步

**完整指令后的当前停点：本轮仅补齐已有数据分析，不推进下述九次建议、点位接线或新预算。**
有限重复值得审查的具体理由是：同完成政策下，两实例的全phase GPU活动约增为1.98倍、
copy约23.47倍、候选交集约17.34倍，暴露位置均发生在copy包络而非配对sync；但每点一次
及已有P0/P1波动不能判断这是否可重复。重复能回答“该条件结构是否仅是单次现象”，
不能回答“算法是否比完整timeline多出独占信息”。若目标是后一命题，不应凭本结果申请
更多相同单FIFO采集；也不以20%或大占比本身作为继续依据。下述预算方案仍仅是先前待审建议。

**建议继续“自然完成操作的必要设备活动暴露与负载结构”这一限定方法方向，不继续承诺
测准全部GPU阻塞CPU。** 本轮把原先opaque的长copy包络细分为有依赖来源的活动交集与
未分离补集，且无需给自然路径插同步。这是值得检验的具体建模对象，不是旧算法追绿。
相对只有API/活动聚合量，多了“哪些必要成员在什么完成操作内推进”的解释；完整依赖
timeline仍能给出相同答案，因此目前是潜在分析能力/表达增量，不是已成立的独占信息或论文创新。

更强的公平对照也已实际核对：**相同I内目标进程全部GPU活动的普通union，B1/B4分别也是
1.782176/30.910044ms，与Q完全相同。** 当前单FIFO自然实例没有展示依赖过滤带来的数值差异。
必要性证据为这些区间提供完成语义，而不是产生普通timeline无法得到的新数字；不能把
“优于整个Prefill的聚合量”写成“优于任何同窗baseline”。若将论文目标限定为新的计算算法
胜过完整timeline，目前没有证据；单纯再加相同单流负载点也不能补上这个差异。

推荐的主要待证命题是实证而非算法优越性：**固定自然完成政策下，负载导致的全phase活动量、
API包络与完成操作内必要活动暴露可以呈不同响应，且这种局部结构能在独立执行中复核。**
最强竞争解释是当前两点的差异主要来自单次调度/观测波动，同窗常规多指标已足以解释，
没有可重复的额外结构。不能用当前20%占比排除它；也不预设单调增加或必须出现排序反转。
新颖性若成立，须来自明确的完成语义/适用边界与非显然的可重复实证，不来自窗口扩大或
数字更大。固定backend也不保证不同batch使用相同kernel实现，实际分支/活动变化须照实保留。

待审方案仅一个：固定自然512/每样本输出2、同模型/FP16/eager/SDPA/w3/r1及边界，
batch选`1/2/4`，做三个独立block，共**9个P1进程/9profile**。B2按输入tensor工作量的
倍增中点选择，不按Device wait调点；每block循环平衡顺序为`1→2→4`、`2→4→1`、`4→1→2`。
每个run为新进程，完整block为比较单位；block间独立/平稳仍是需要检查的统计假设。
三个block是预算有限的结构筛查，不是精度或统计充分保证；原一次B1/B4只作先验线索，
不拼接为新block。B2需明确的新执行声明/实际质量检查，但不自动触发完整Q0或新采集设施。

该方案仅P1观测结构，不授P0性能/优化收益；若后续要此类claim，须另有同政策相邻P0配对。
同窗API count/sum/union、GPU活动、合法mapping与完整timeline保留为公平baseline，不能
故意少给字段。冻结候选配对/成员规则后看全样本的原值、signed差和来源，不追采显著。
这九次仅能筛查负载响应的重复性/中间点，不区分候选与完整timeline（两者可预测相同数值），
不能凭它授论文创新或普遍规律；若只想证明算法独占信息，不应执行该方案。
若有效记录反复表明所称额外结构可由简单API/活动量同样解释，且没有具体来源层面的额外
判断，则停止扩大测量主张；若仅方向/精度不确定，不包装成已发现规律，也不自动加预算。

成本先按现有profile每次约33s参考，9次采集本体约5min只是线性估算；沿既有300s/profile
硬上限，采集阶段预算最多45min，部署/导出/审查/传输另计，不承诺总耗时。沿既有12GiB
临时空间规划；长期50GB目标及归档后精确清理政策不变，当前不部署或生成采集入口。
完成固定批次或遇身份/边界/drain/映射/未知影响/支持域硬失败即停；不重试、替补、加点。
Prefill新缺口不能借局部历史成功放行，Decode缺口只有可独立定位在首ready之后才隔离。

**当前停点：本轮离线任务完成；九次验证只是待协调审查的后续预算建议，不是执行授权。
不恢复CUPTI、引擎或Cpre追加Pilot。** 研究可继续检验，但是否形成论文级增量仍需公平的
解释对照和可重复证据，不能凭配置数、漂亮占比或Gate数量宣布立项已获科学确认。

### 审计索引与有限统计检查

本机独立目录`.local/diagnostics/coe_batch_prefill_v0_1/derived_v0_1_r2/`：
results SHA256 `667aa4621620e41d76923fe0f35a44b2957177af0f4c4b584a2b699983a9fb27`；
审计器SHA256 `85e62353b964ba36b71785a2294d9a8a7f972485b24748cdd259d7ffd41bea53`。
B1/B4实际阶段耗时约1.017/4.122s，不是模型/CUDA执行。初稿错误要求NVTX pop早于point，
在匹配源码/Raw后改为真实callback顺序，失败诊断保留；候选copy→sync边界没有变。
呈现器的API子类字段拼写错误亦只修本地审计读取，未改生产输出或测量定义。
实际命令为该本地目录下`python -X utf8 -u analyze_batch_prefill.py`、
`python -X utf8 present_and_verify.py`、`python -X utf8 check_final_artifacts.py`，最终均exit0；
三脚本`python -m py_compile`通过。前两项来源/算术回执与最终公平baseline/输入复核回执
分别保存在同一派生目录，不称目标机复现或科学规律验证。

7.166仅新增本机`complete_delivery.py`及`presentation_v0_2/`显示产物，未重跑前三项。
显示脚本SHA256 `a4b434044a2a1898c5d74353005b4f20bc63e1324bd712d9c0623800a00952c2`；
`display_receipt.json`绑定原results、固定草案、两份未变预算CSV和新增占比/时间线CSV及PNG。
实际命令`python -X utf8 .local/diagnostics/coe_batch_prefill_v0_1/complete_delivery.py`成功，
新图目视检查、选定Raw/比例/来源/链接/diff和单脚本编译检查通过；不是新qualification。

ARS统计风险11/11已检查：phase/角色混合（分开展示）、生态推断（批量不作四重复）、
Berkson/选择偏差（支持域/局部限制披露）、collider（无结果后协变量调整）、base-rate（不适用）、
回归均值（不按大数挑点）、survivorship（失败保留）、look-elsewhere（全两点展示）、
forking paths（明确事后探索）、相关/因果（不称净阻塞/收益）、反向因果（未作此推断）。
未作显著性/等价/功效结论；新的Formal合同、生产A改版和新预算均未在本轮生效。
