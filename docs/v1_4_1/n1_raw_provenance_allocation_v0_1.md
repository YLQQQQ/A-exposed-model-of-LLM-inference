# N1 Raw同步来源 amendment 与 allocation 裁决稿 0.1

日期：2026-09-30。Engineering / Pre-Pilot；研究设计v7.1、实验协议v2.1。

**P1已获用户批准并实现；P2仅保守识别已实现；opaque allocation记账政策待批准，未实施。V0仍BLOCKED，Vmarker/V16 NOT_RUN。** Gate7～9及Gate10限定G1 PASS保持；不启动Pilot、D/Signature或Formal。本文接替[7.106审查](n1_v0_review_v0_1.md)中的现行P1/P2状态，不改其历史诊断或原失败报告。

## 1. P1：版本、来源及兼容边界

| 合同/实现 | 新版本 | 作用 |
|---|---|---|
| 内部同步来源 | `exposedpath-sync-provenance/0.1.0` | `STRUCTURED / RAW_PHYSICAL / UNRESOLVED`及可复读Raw引用 |
| S | `exposedpath-s-layer/0.4.0` | 原字段加`sync_provenance`，不改W/terminal/validity算法 |
| A/B | `exposedpath-ab/0.5.0` | A定义不变，B显式携带同一来源证明 |
| N1模型适配 | `exposedpath-n1-model-ownership/0.2.0` | 明确选择上述扩展；旧0.1.1文件仍按旧路径复读 |
| allocation诊断 | `exposedpath-allocation-diagnostic/0.1.0` | 已知名称/资源语义，不授completion或A分类支持 |

新schema：[来源](contracts/sync_provenance_schema_v0_1.json)、[S0.4](contracts/s_layer_schema_v0_4.json)、[A/B0.5](contracts/ab_schema_v0_5.json)。基础Measurement Contract0.2及旧S0.2/0.3、A/B0.2/0.3/0.4保持原文件和读取行为；本amendment仅改变显式opt-in N1内部同步的**来源身份要求**，不是放宽物理依赖、改变A/B公式或将所有无标签同步放行。新版本仍为signed-int64时间戳、非负原范围duration；未知/混用版本拒绝。Derived不接受A/B0.5，不自动授新Q0资格，不撤销Gate6历史PASS。

`RAW_PHYSICAL`必须同时满足：

- Raw Runtime API与CUPTI synchronization唯一correlation映射，成功返回；物理区间包含于API区间，同一trace clock、线程、进程实例、context及实际stream。
- 既有N1桥接实际证明fresh、非null、NON_BLOCKING流，窗前成功drain；没有已观测或顺序不确定的incoming依赖。保留“支持域内无未记录incoming依赖”假设，不宣称已经排除所有未记录活动。
- 唯一projected request/repeat/phase ownership，与同一完整身份的`model_forward`原标记相容；它只证明调用位于forward范围，**不是源码callsite**。
- 不属于预定干预范围；没有重叠的冲突/畸形结构化sync身份。token-ready和N1预定干预仍须原结构化身份，部分标签缺失或来源冲突不能走Raw替代。
- 继续通过原S的完整必要集合、dependency closure、semantic frontier、terminal及validity检查。来源已知不意味着W完整或B有效。

来源保存SQLite及pass-ledger SHA256、原table/rowid/record、correlation、完整global PID/TID及OS PID、scope/clock、request/repeat/phase、projection/forward原引用、API和物理区间/返回值。进程实例以**本次不可变trace与pass身份**限定，不能只按OS PID跨capture合并或伪造出生/退出时间。序列化S消费时复读Raw映射、scope、ownership及forward引用；B复制同一来源。

内部调用的`sync_origin / callsite_id / sync_ordinal`仍为null/UNKNOWN；不使用rowid作为实验ordinal，不把forward范围改写为源码位置，不授源码callsite分组或人为干预来源claim。显式新版本附加来源与原数值/身份校验均不可省略。

## 2. P1在不变V0上的实际结果

执行提交仍为`c21d8358e42e764c37cf9b315d87235989a817e1`；本地只改consumer，未改producer/runner、插桩、allocator、窗口或流政策。原ZIP及REP/SQLite/collection report哈希与[7.106索引](n1_v0_review_v0_1.md)一致。新派生目录名`continuation_p1_v0_1`，仅存忽略的本地诊断根；准入失败详情、下层诊断和独立Raw复核分开，不写合格`domain.json`。

实际内部physical sync348 / Runtime17576 / correlation61831：RAW_PHYSICAL，源码字段仍null；完整同流FIFO前缀8，最后提交节点Memcpy344，terminal end27824075920 ≤ API return27824091037。token sync349/350仍STRUCTURED，前缀1906/3498，terminal Memcpy345/346。三条下层B均B_VALID；不是整个N1模型资格PASS。

独立复核直接按Raw enqueue顺序、记录身份及区间union计算，没有调用被测S/A/B来生成标准答案。内部API的1195434ns由Raw必要活动union拆成223646ns device-wait、971788ns residual；不是把全部区间都叫等待或全部转residual。

| 窗口 | 总ns | Host | CUDA API | Device wait | Sync residual | Unattributed |
|---|---:|---:|---:|---:|---:|---:|
| Request | 212715004 | 119176616 | 90648385 | 223646 | 1029194 | 1637163 |
| Prefill | 128172644 | 67308362 | 58000578 | 223646 | 1002895 | 1637163 |
| Decode | 84542360 | 51868254 | 32647807 | 0 | 26299 | 0 |

各窗互斥守恒、每个分量Request=Prefill+Decode，独立检查通过；边界总时长及Host/API未改变。剩余全部unattributed来自三次allocation；A仍带`CUDA_API_SEMANTICS_UNRESOLVED`，完整准入仍`DOMAIN_MODEL_UNSUPPORTED_API`。这些A/B是**失败链的诊断性结果**，不发布为合格模型结果；`dropped_records_status=UNKNOWN`、`measurement_validity=NOT_ASSESSED`及旧BLOCKED保持。

阶段计时：完整准入44.348秒（S28.667秒、A/B1.982秒）；另一次下层诊断S27.988秒、A1.756秒、B0.129秒。没有加timeout或跳检查。独立checker初稿误将全部内部API时间预期为residual，被Raw activity union推翻后只修正checker；未为符合预期修改analyzer或重复全链运行。更正及保护哈希见本地`independent_final_checks.json`。

## 3. P2：已知allocation，但completion不支持

精确识别`cudaMalloc`及合法`_v数字`后缀，诊断为`KNOWN_ALLOCATION`、`completion_support=UNSUPPORTED`、`completion_scope=null`。没有给A注册普通non-submit或生成物理sync/W/B；相似名字、Async/Managed/未知调用不能继承该规则。三次调用均继续阻塞N1准入，而非永远仅报“名字未知”。

研究设计v7.1 §2.4的API预算明确包含查询和资源管理；但其逐段规则及MC0.2 §6/9/10要求潜在completion受支持后拆分，否则保留未知。[既有non-submit审查](gate8_non_submit_api_review_v0_1.md)也没有授权cudaMalloc。父类CUDA API的资源成本动机**并不自动授权**改变未恢复等待的处理。

[CUDA12.4.1 Runtime cudaMalloc](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/group__CUDART__MEMORY.html)说明其分配设备内存，不提供本分析需要的逐次Host全域completion保证。[Programming Guide §3.2.8.5.4](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-c-programming-guide/index.html#implicit-synchronization)列出设备分配对跨流并行的隐式排序限制；这不是“API返回前全设备完成”。[API synchronization behavior](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/api-sync-behavior.html)明确调用可能因内部资源发生阻塞，未文档化行为不可当作稳定同步保证。

V0三条均成功、唯一Prefill/primary-thread ownership、无嵌套API交叠：Runtime17566/17579/17646，correlation61737/61867/62931，时长773224/176954/686985ns，合计1637163ns。第二/三次返回后先行kernel仍pending，反驳device-wide completion；无关联activity不证明无内部同步。源码没有记录allocation字节数，不声称三组分配大小已相同。

## 4. allocation最终政策：推荐有条件批准，不在本提交实施

**可成立的限定解释：** 将成功、唯一归属、边界明确且影响范围受支持的资源分配调用，记为`opaque resource-management CUDA API occupancy`，而非“普通非阻塞查询”。它回答该request的Host时间有多少被资源API占据；不回答allocation内部哪些时间在等GPU。这个预算问题符合原研究主线，但只能在透明承认解释损失的情况下采用。

**必须修订的最小条款：** 保留五个A顶层类及互斥union，保留CUDA API父类=submit+non-submit。扩展已注册non-submit的解释，允许一个显式标注opaque的资源管理子类型；它不代表nonblocking，也不代表无等待。对该窄子类型，未拆内部等待不再单凭此项转顶层unattributed；实际unknown/ownership冲突仍保留。这改变MC0.2中“潜在completion未支持必须未知”的适用例外，须另一个版本化amendment和资格增量，不能只添加白名单或声称冻结含义未变。

必需条件及拒绝边界：

1. API语义是明确版本支持的资源分配；成功、完整可界定的Host区间、唯一进程/线程/request/phase/clock归属。不是未知名称或失败调用。
2. 下游已观测submit/sync仍有真实correlation、完整同流W/terminal及scope证据；窗前drain和支持域检查仍通过。分配不成为虚构device-wide barrier，不删除已完成物理前缀。
3. 区分事实与假设：Raw能证明已观测调用及受支持流闭包；“没有未记录incoming依赖”仍为明确支持域假设。没有activity/无warning/exit0不能证明内部无等待。
4. 观察到其他流/owner、相关event、未界定隐式跨流影响、额外physical sync/submit、嵌套调用或与声明矛盾的映射时，不套单一opaque例外。仅能证明局部影响才保留局部unattributed；影响无法界定则拒绝对应窗口及机制claim。即使API自身区间明确，下游依赖不明也不能仅靠它返回成功放行。
5. 首版限定无嵌套/交叠的已知cudaMalloc。若以后确需支持嵌套，必须沿既有同步优先级和区间union验证，不得对外层全时长与内层同步重复记账；本次不扩展该支持域。

损失及claim限制：

- A仍是互斥wall-clock预算；opaque API可能包含未拆的内部等待。不能将A_device_wait称为**完整等待总量**，也不能将opaque API称为纯Host成本或反事实可消除的延迟贡献；数值闭合/unknown清零均不恢复这些解释。
- 不为allocation构造W、terminal或B，不声称其hidden progress已恢复。真实受支持的内部/token/干预单sync B可以保留，但只解释自己的必要集合；不能跨同步求和、把它当全request等待分解。
- N1仍能检验预定同步的局部机制和request预算变化；但allocation开销/行为变化可能改变等待分布。三组必须保留实际allocation记录及公共配置/token检查，不能预先假定其相同，不能将全部request差异归因干预或把N1结论移植到自然G1。
- 不自动给Formal、完整新版Q0、D/Signature或信息增益结论。若论文claim要求完整恢复allocation内等待，推荐**不采用**此例外，保持unattributed/阻塞，直到有充分completion证据。

推荐理由是资源管理API占据预算本身有明确研究含义，且原设计包含这类成本；不是因为本次unknown较小或希望V0通过。**当前V0继续BLOCKED；批准政策也不等于已经完成新支持域资格。**

## 5. 独立预期与验证边界

已实施P1/P2正反例：真实verified producer的CPU文件链，内部完整FIFO有/无源码标签数值一致、来源不同；缺/歧义correlation、clock/process/scope/owner、冲突marker、部分源码标签、质量失败均拒绝；token-ready和预定干预缺结构身份不能替代。S/AB读写往返、原引用/哈希篡改、未知或跨版本，以及旧adapter文件复读均覆盖。allocation识别精确但仍拒绝；真正未知API不继承规则。合成完整性/CPU成功不冒充目标机资格。

待政策批准才实施的手算预期（**不是已通过测试**）：

- request `[0,100)`，submit `[10,20)`，合格opaque allocation `[30,40)`，已支持sync `[60,80)`、其W活动`[60,70)`：应为Host60、API20（submit10+opaque10）、device-wait10、residual10、unknown0。它只证明该预算，不证明allocation内部无等待。
- 同一allocation增加未界定的其他流/owner依赖：即使返回成功且所有数值能闭合，仍拒绝对应窗口/机制输出，不能套opaque例外；必要集合必须独立证明。
- 缺allocation end、失败返回、唯一owner冲突、未支持名称/版本或unexpected physical completion：拒绝/保留有界unknown，不转Host、不构造allocation B。
- allocation内出现nested sync：超首版支持域，拒绝；不得将外层全部API时间与内层等待相加。未来支持须独立检验同步优先级及union。

本轮8文件相关CPU回归239 passed（155.85秒）；最终新增复读/来源篡改检查另跑来源文件33 passed（45.68秒），重叠不累加。compileall、contract37/37、Canonical boundary、oracle independence和diff检查记录于[进度7.107](research_progress.md)。没有全量、服务器、模型、GPU或Nsight操作。新Raw来源的本地增量与原V0实物检查已完成；仍不能自动继承完整新版Q0资格。

**唯一待裁决项：是否批准上述无嵌套窄域opaque allocation预算例外，并接受其“不拆内部等待、不授allocation B/完整wait claim”的限制？** 建议按这些限制批准，再做最小资格增量；在决定之前不交付Vmarker/V16或重采包。本次仅consumer变化，没有理由重采已完成V0。
