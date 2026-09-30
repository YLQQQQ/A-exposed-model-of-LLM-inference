# N1 V0 实物审查与局部适配修复 0.1

状态：**V0 模型支持域仍 BLOCKED；本轮不是新的 N1/Q0 资格。** 执行身份是 `c21d8358e42e764c37cf9b315d87235989a817e1`，分析侧适配是 `exposedpath-n1-model-ownership/0.1.1`。Gate7～9及Gate10限定G1 PASS保持；Vmarker/V16未运行，Pilot不启动。

## 1. 输入及完成的检查

直接核验用户回传 `n1_model_c21d835_once.zip`：2177563 bytes，SHA256 `7867c610da1025cba1e68de2459f45b36d2b5979b949a70711def17315af28ed`；CRC、安全路径、重复项及87项清单完整覆盖通过。原ZIP、REP、SQLite及失败报告保持不变，所有计算在忽略的本地副本/新版本派生目录完成。

- 原服务器CPU142 passed是回传成绩。本轮本地Python3.12.7，仅CPU离线分析与相关回归；没有服务器、CUDA、模型或Nsight/profile/export操作。
- V0采集35.672秒、exit0、无超时，producer/diagnostic COMPLETE，export PASS；原错误 `DOMAIN_MODEL_UNSUPPORTED_API` 不改写。
- 原manifest commit/clean、prepared/producer/execution哈希、输入32/输出2、非early EOS、实际配置及preflight绑定已检查；封存runner源码与执行提交Git blob字节相同。
- warmup与measured held native handle不同；实际锚点/API/physical sync将measured handle连接到唯一非null CUPTI `NON_BLOCKING` 流。窗前成功drain返回早于request.start，未将其计入request。
- 全部窗内9678条API及3498个设备活动继续检查：唯一primary-thread/correlation、真实process/context/stream、request/phase ownership、返回状态、无graph/超域event依赖。不是“一标记一API”，也不是仅以 `with stream` 认定归属。
- 三窗口 completion、必要FIFO前缀及最后提交节点使用独立顺序核对。A守恒/分量阶段可加另作记账检查，不冒充归属正确性或模型资格。

REP SHA256 `d07248a71dcf19c2fa2c17f18d4f7279c71432dc24c8be6808e511326e2bb301`；SQLite SHA256 `861f5faf559fd98db962694491e2f3e543827b56a3c2232eae9da52a89408fed`。机器路径和完整逐record资料只在本地handoff/诊断索引，不提交Raw。

## 2. 三次 cudaMalloc：已知语义与尚未决定的测量处理

权威研究设计v7.1 §2.4包含资源管理API的互斥API成本；但Measurement Contract0.2 §6/10规定潜在completion/同步不能未经支持直接按普通API处理。先前[non-submit审查0.1](gate8_non_submit_api_review_v0_1.md)没有授权cudaMalloc，其窗外出现不授窗内支持资格。

[CUDA12.4.1 cudaMalloc](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/group__CUDART__MEMORY.html)定义分配线性设备内存，并非kernel/memop提交接口；它没有提供本分析所需的、逐调用“所有先行设备工作在Host返回前完成”的scope保证。[Programming Guide §3.2.8.5.4](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-c-programming-guide/index.html#implicit-synchronization)将设备分配列为跨stream隐式排序/并发受限的操作。设备排序与Host可观察completion不能直接互换。[API synchronization behavior](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/api-sync-behavior.html)也禁止把未文档化阻塞行为当作稳定保证。

三个成功调用均在Prefill、primary thread，无嵌套API交叠，无唯一相关activity/physical-sync行。以下pending只指已证明的先行活动，不是根据名称猜出的W：

| Runtime row / correlation | API时长ns | 入口仍pending | 返回仍pending |
|---|---:|---:|---:|
| 17566 / 61737 | 773224 | 0 | 0 |
| 17579 / 61867 | 176954 | 1 | 1 |
| 17646 / 62931 | 686985 | 25 | 12 |

第二次返回后kernel3500仍未完成；第三次返回后也有先行kernel未完成。因此**不可将这些调用硬套为device/context-wide Host completion**。这不证明没有任何内部同步或依赖。第一条空pending也不是“绝无同步”的证明。

在当前单一measured FIFO范围，活动排序仍由已有同流提交边覆盖；没有依据额外生成allocation→kernel、跨流或Host completion边。若要拆分allocation内device-wait，必须先确定其真实completion集合，不能用窗口内全部活动重叠代替。也不能仅凭无mapped activity就加普通non-submit白名单。

目前生产registry仍输出UNCLASSIFIED，不掩盖旧限制；本审查已将原因准确收敛为**已知allocation的隐式ordering/completion处理尚不支持**，不是“API名字未知”。版本化注册/测量政策见§6，尚未实施。三次合计1637163ns没有转入Host或residual。

## 3. 内部stream sync：四种身份不能混用

Prefill内部调用为Runtime17576 / correlation61831 → physical sync348，成功、唯一API映射、真实scope/clock/process/thread及projected request/phase均可追溯。

| 身份/证据 | 实物状态 | 对恢复的作用 |
|---|---|---|
| Raw物理record、source hash/table/rowid、correlation、调用/同步区间及成功状态 | 可核验 | 确定实际物理调用及completion scope |
| request/repeat/pass/phase与同一clock、提交、device/context/stream、依赖/owner | 可核验 | 确定完整W及其归属，缺失/冲突确实必须拒绝 |
| 实验sync_origin、sync_ordinal | 未观测 | 来源分类/实验比较，不由物理row编号自动产生 |
| 源码callsite_id | 未观测 | 来源分组；宽泛forward范围不能当作源码调用点 |

独立FIFO核对其完整先行集合为8个活动，最后提交/完成节点是Memcpy344；它在API返回前完成。两次token-ready对应1906/3498个完整成员、Memcpy345/346。不是删去已完成前缀后再选terminal，也不是按最大end单独定义frontier。

当前`sync_semantics.analyze_sync_semantics`与MC0.2 §3/11还要求origin/callsite/ordinal，故内部记录仍 `INVOCATION_BOUNDARY_INVALID`，terminal输出INVALID、B_INVALID；**能够从物理证据提出唯一集合不等于当前schema已允许发布它**。本轮保留该拒绝，不从forward伪造标签，不自动追加所有框架调用包装。Raw来源替代必须显式版本化批准。

## 4. 已修复的实现问题及边界

1. **局部nonblocking scope被无关历史default流污染。** Gate9合同首选fresh nondefault NON_BLOCKING流；[CUDA12.4.1 stream语义](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/stream-sync-behavior.html)明确legacy implicit ordering排除nonblocking流。N1真实桥接和Raw stream/context证明齐备、没有已观察到或顺序不确定的incoming event时，S建图只使用完整选定物理流前缀；不填全局LEGACY/PTDS、不删除原活动、不截短W。原冻结/合成/G1默认路径不opt-in，其他scope或incoming event仍使用原拒绝/closure规则。保留合同已有的“无未记录incoming依赖”支持域假设，未宣称排除一切未记录依赖；UNKNOWN/NOT_ASSESSED不改。该修复不解决allocation未知completion。
2. **Nsight global PID的VM高位。** 使用既有Canonical解码连接OS PID；Raw完整global PID保留。不是把global PID直接除以2^24当OS PID；加入含高位的文件链反例。
3. **第一处unsupported提前终止，遮蔽其余问题。** 收集全部unsupported API的record/correlation/phase/关联记录，再检查物理S/A/B并输出结构化失败详情；未知与其他门仍拒绝，失败不生成domain.json。

新目录完整准入尝试45.761秒，最终依然BLOCKED。诊断链S28.543秒、A2.377秒、B0.087秒；不提高timeout，不跳必要检查。另有重复诊断读取用于独立交叉核对，不作为生产性能加速比。

## 5. 诊断性结果，不是合格A/B

以下仅用于确认剩余缺口，禁止作为N1研究结果、qualified模型B或D/Signature输入：

| 窗口 | 总ns | Host | API | Device wait | Sync residual | Unattributed |
|---|---:|---:|---:|---:|---:|---:|
| Request | 212715004 | 119176616 | 90648385 | 0 | 57406 | 2832597 |
| Prefill | 128172644 | 67308362 | 58000578 | 0 | 31107 | 2832597 |
| Decode | 84542360 | 51868254 | 32647807 | 0 | 26299 | 0 |

记账/阶段分量相加通过；unknown恰为allocation1637163ns + 内部来源身份1195434ns。零device-wait不是“未知区间绝无等待”的结论。下层两次token-ready获得B_VALID、内部同步B_INVALID，但**整次N1模型仍拒绝**；没有发布合格domain产物。

本地相关五文件回归185 passed /113.21秒；收口自审另补“incoming wait顺序未知不能视为没有依赖”反例，先复现新shortcut错误COMPLETE，再收紧opt-in条件。最终S文件100 passed /0.65秒及N1 nonblocking文件链定向7 passed /27.18秒（与185重叠，不累加）；实物已有dependency event数为0，收紧不改变保存的诊断结果。独立手写预期覆盖无关default与完整FIFO、相关incoming事件（包括缺record/顺序未知）、blocking/null/错scope、correlation冲突、内部来源缺失、所有allocation失败记录及VM高位。compileall和validate-contract37/37通过，后者仅内部一致性。没有全量、Q0重采或目标机测试重跑。

## 6. 集中待裁决：最小语义提案，PROPOSED_NOT_APPLIED

推荐分清两个条款，并作为一次集中amendment审阅；不要为了放行V0删检查。

**P1：已观察内部同步的Raw来源身份替代。** 新S/A-B显式版本可允许唯一source SHA/table/rowid/API/physical correlation作为`physical_source_identity`；必须仍满足成功状态、scope/clock/process instance、request/phase及完整提交/依赖/terminal检查。实验origin/callsite/ordinal未观测时保持null/UNKNOWN，用独立`provenance_basis=RAW_PHYSICAL`字段说明，不伪装natural_token_ready/n1_intervention。禁止源码callsite分组及干预来源claim；N1预定干预和token-ready仍须原结构化身份。旧schema/读取/资格不变，新版本离线审查另写目录、不改旧report。

独立预期：同一完整物理stream前缀有/无源码标签应得相同W/terminal，但来源完整度不同；若API/physical映射重复、缺context/stream/clock、跨owner、失败返回或marker给出冲突身份，则拒绝，不能使用替代路径消除真实矛盾。

**P2：cudaMalloc已知但未支持completion的显式规则。** 新registry准确识别合法名称/版本后缀为allocation/可能隐式排序，而不是普通non-submit或假device-sync。在没有足够completion证据时记录`KNOWN_ALLOCATION_COMPLETION_UNSUPPORTED`诊断，保留unattributed及其范围依据、不生成虚构W/B。仅能界定局部影响时保留其余片段，影响不明仍拒绝整窗可信claim。是否未来将allocation作为opaque API成本纳入A，是另一项测量承诺：将失去allocation内等待的拆分，不能称“已恢复完整device-wait”。**本轮不推荐直接采用这种放行政策。**

独立预期：返回时先行kernel仍pending的反例禁止device-wide completion；空pending/无关联activity均不能证明无同步；观察到相关physical sync、其他流/未恢复依赖或scope冲突时，不能套局部/普通API路径。未知API仍未知。

P1/P2的新增schema、registry支持性和资格边界需批准后实现受影响增量；不改变A五类/W/terminal/B公式、不继承新Q0资格、不撤销Gate6历史PASS。P2的保守注册也**不自动满足N1现行“所有measured physical B合格、A无拒绝原因”门**。若研究要求allocation完整解释，需要具体completion证据或另行批准测量范围；低unknown不是替代条件。

## 7. 现在是否需要采集

**现在没有重采或Vmarker/V16执行必要，也不交付重采包。** Raw已含内部物理同步身份；先裁决P1/P2，不能用同配置重采解决schema承诺。仅consumer/局部adapter改变，producer/runner/插桩/流政策/输入均未改，原V0保留将来复用可能；不是因分析commit变化就要求新的V0。若后续决定改变allocator、窗口/producer或统一流行为，才需说明三组可比性并考虑新V0。当前绝不保证后两组已经可执行。

当前唯一下一步：审阅上述来源身份与已知allocation的最小政策；所有不依赖该裁决的本地修复和完整离线检查已完成。原attempt BLOCKED、UNKNOWN/NOT_ASSESSED及已有限定资格保持。
