# 复制—成功同步完成操作候选合同草案 0.1

版本：`COE-CANDIDATE/0.1.0-draft`；2026-10-15；状态：**候选对象已获用户认可，本文待审，
未签署、未接入生产A/B**。不是对G12-ROUTEA/0.1.1的追溯amendment，不授新Formal。
依据：[候选语义/24链](completion_operation_candidate_review_v0_1.md)、
[四token独立增量验证](completion_operation_controlled_validation_v0_1.md)。
本轮预算迁移只允许独立的事后探索性预览；历史协议、registry、schema及输出原样保留。

## 1. 测量对象与三个独立判断

测量对象是**复制runtime入口至配对成功stream sync返回的子包络内，语义必要设备活动的
区间并集长度**。不是整个`.cpu()`、完整Host token取得区间、纯Host阻塞或可优化时延。
仅复制提交而无可证明的完成操作，不成为本候选；不按Memcpy名字统一判作同步。

- `operation_validity`：`VALID / INVALID / UNRESOLVED / NOT_COMPOSITE`。判断固定配对、
  真实成功返回、scope/clock/identity及必要集合是否可靠；不以交集大小判断。
- `profile_applicability`：`MATCH / OUT_OF_SCOPE / NOT_QUALIFIED`。同一合理操作可能不符合
  当前窄profile，不能把它写成原Raw错误，也不能将另一profile的资格自动转移。
- `interpretation`：固定为`NECESSARY_ACTIVITY_DURING_COMPLETION_OPERATION`；
  `pure_host_stall=NOT_IDENTIFIED`、`removable_latency=NOT_IDENTIFIED`。
  有Host工作重叠不自动否定操作；没有/极短Host间隙也不证明纯等待。

## 2. 配对、边界、完成保证与必要集合

1. 配对先由完整run/request/repeat/pass、结构化operation/token身份和固定源码确定，
   再映射唯一成功copy API和随后成功stream sync。不得按时间最近配对、按交集筛样本。
   同一外层范围或同一源计划下的不同操作范围均可承载，但必须证明是同一次完成操作。
2. 固定`I(o)=[copy.runtime.start, paired_sync.runtime.end)`，使用原trace signed-int64 ns。
   缺失不能补0；end≥start，半开区间；duration非负且目标duration字段须显式范围校验。
   不把NVTX start、最早kernel或Cpre干预起点替换为copy入口。
3. 整体保证来自**同一实际流的配对同步成功返回**，不是Async复制本身的独立保证。
   copy、D2H activity与physical sync必须有唯一correlation和相符进程实例/device/context/流。
   Host实际token取得和结果内容是另一项完成证据，发生在配对sync之后；marker只标事实。
4. 令`c(s)`为该同步根据受支持语义捕获的提交边界。必要集合截止于`c(s)`，**不是copy入口**。
   包络开始后才提交的D2H仍可能必要。当前串行profile中同线程提交已在sync入口前结束；
   并发线程无法确定捕获边界时保持UNRESOLVED，不按时间重叠补依赖。
5. `W_qualified(s)`从已获支持的FIFO/event/completion语义与证据取得；保留已完成成员，
   排除边界之后提交的活动。token数据依赖与sync必须完成的流序前驱不同，不能混称。
   全物理W与合格局部后缀分开；后者保留窗前成功drain/闭合前缀、成员/依赖边、两模式投影
   证明及支持假设，不能据此发布未获资格的自然默认流物理B。
6. `Q_o=I(o)∩union(intervals(W_qualified(s)))`，kernel/MemOp统一去重。
   输出`wall=|I|`、`overlap=|Q_o|`、`complement=|I\Q_o|`及逐片段来源；
   补集不自动归因CPU、驱动、调度或return tail。terminal保持原证据，不用入口到terminal
   的距离替代活动并集。无关流长kernel即便重叠也不能进入W。

## 3. 当前profile与边界

| profile | 已有依据 | 当前用途/限制 |
|---|---|---|
| `CONTROLLED_NULL_FIFO_PINNED/0.1` | 原NULL-FIFO-D2H两request四token、4字节Device→Pinned、独立2/4成员与terminal | 操作层结构、成员及算术的独立依据；原Engineering不升级 |
| `PYTORCH_NATURAL_HELPER_PAGEABLE/0.1-exploratory` | 固定99f3bae源码、原G1投影资格、12run/24链、8字节Device→Pageable与实际token | 本轮仅事后探索及预算预览；不是新的Formal A或通用复制资格 |

整体保证依赖尾部成功sync，不依赖把copy判成阻塞，故Pinned/Pageable差异本身不要求
新GPU实验或重跑Q0；调用路径、配对来源、内存类型和已获支持依赖仍须分别留证。
当前只声明单GPU、隔离request、主要请求线程、既有eager执行和获支持的后缀闭包。
不覆盖并发ownership、多GPU、graph/未知event、N1其它干预或Cpre的干预包络。
当前G32/G512单token的资格不自动推广到任意执行方式；同已批准支持域内输入长度改变
本身不触发全Q0，逐request实际检查仍必需。

## 4. 必需字段与拒绝/限制

每条操作记录必须携带以下合同，不依靠schema猜测或静默fallback：

| 字段组 | 必需内容 |
|---|---|
| 版本/角色 | 本草案版本、profile及状态、source data role、derived role、原执行/分析身份和新分析来源 |
| 稳定身份 | run/request/repeat/pass/attempt、process instance、thread、token及phase；operation_id由输入hash＋两API原ID＋逻辑身份确定 |
| 原始来源 | SQLite/source hash、scope/point/Host ledger/token来源、API及physical sync record ID/correlation、返回码 |
| 实际设备 | physical/logical/inventory/activity映射、context与trace stream；由UUID/PCI/context证据桥接，不按编号相等 |
| 时间 | 原clock identity、copy/sync起止、I及固定边界规则；无Host/trace钟拟合 |
| 必要性 | c(s)及来源、合格W/局部后缀成员和submit引用、依赖边/前缀闭合、terminal、未记录incoming依赖支持假设 |
| 内容 | copy方向、bytes、按本文件enum解出的内存类型、Host实际token值；未采实参/地址继续UNKNOWN |
| 区间结果 | 原sync交集、Q、kernel/MemOp及mixed来源、wall、补集、原子片段；无效结果为null/原因而非0 |
| 质量 | 原dropped-record/measurement validity、诊断裁决及来源，不能因本草案变为零丢失或全局有效 |

拒绝条件必须区分具体原因：缺/多配对、身份或clock冲突、失败API、缺correlation/stream
映射、capture边界不明、必要依赖/前缀未闭合、terminal冲突、错误实际token及影响范围
不明的诊断。未知规则或未签署版本不能用于新Formal。只有名字/耗时/重叠是证据不足，
不是有效completion scope。

操作内有确定Host工作、GPU活动空隙、很小/零交集，**不单独导致INVALID**；只禁止纯等待
解释。若Host路径引入新请求、缓冲覆盖、无法界定的新提交或配对歧义，则按实际身份/
依赖失败拒绝。严格helper profile若不允许额外处理，应标OUT_OF_SCOPE而非伪称全局损失。

## 5. 独立预算迁移预览合同

标识：`COE-BUDGET-PREVIEW/0.1.0-draft`；角色固定
`EXPLORATORY_POSTHOC_BUDGET_PREVIEW_NOT_FORMAL_A`。不是可被旧A/B loader接受的新A。
固定原request/prefill/decode窗口和全部有效run，不改变P0/P1、边界、排除或统计规则。

令原互斥集合H/C/E/Z/U分别为Host、CUDA API、旧Device wait、sync residual、unattributed。
先按原子区间令`Q=union_o Q_o`，排除旧E后取`Δ=Q\E`；核实每片段原类别及来源：

- `E_preview=E∪Q`；H、C、Z分别减去自己与Δ的交集，不能在旧A上额外加Q。
  预览字段称`completion_exposure`，不把更宽对象无版本地改名为旧Device wait。
- U保持；`Δ∩U`未经独立解决不得迁移。如果原类别/归属无法证明，预览拒绝对应片段，
  不把分类或依赖缺口填成Host/API/零。
- C的submit/non-submit同步移除相同片段，父子守恒；原API count/sum/union不改，
  不能与迁移后预算相加。opaque allocation不自动纳入本copy/sync子域。
- 活动、操作、旧sync之间均union去重；kernel/MemOp子类用互斥kernel-only、MemOp-only、
  mixed表示。逐片段保留from/to、API/source records、operation ID和window membership。
- 同步子区间与kernel/MemOp endpoints、操作、phase边界共同切原子片段，保持半开边界。
  检查旧/新顶层总长、父子预算和Request=Prefill+Decode；守恒只是必要条件，不证明归属。
- 预览允许复用已获资格的旧A总量，但迁移来源须有区间证明。本批若Q与所有Raw sync API
  包络不相交，结合旧合同`E⊆sync API包络`即可证明`Q∩E=∅`；不必重算S。
  若此证明不成立又缺旧E的合格原子来源，不能猜测排除量，须停止该预览。

单sync B保持原物理同步、W/terminal与公式，不为组合操作制造barrier/B或跨sync求和。
本草案和预览均不回写旧Formal，不授予方法创新、纯GPU阻塞、关键路径或可优化时延结论。

## 6. 2026-10-17本地接线计划：原预算来源与输入轴（用户本轮授权）

只补候选离线连接器，不改生产S/A/B、helper或采集入口；在main原工作树保留用户修改。
输入为精确hash绑定的candidate、Canonical与既有局部准入结果；仅复用已有合法S证明，
不以COE集合自身生成旧A。输出新版本原A/候选预算、迁移片段来源及逐token位置。

- [x] 先补手算fixture：相交/重复操作union、旧E去重、来源类别/父子、未知与invalid、
  缺成员/重复成员、错源/错身份、阶段相加与文件hash；观察预期缺功能失败后实现。
- [x] 从已有准入的同scope Canonical API及两模式一致的必要集合证明重建原预算原子区间，
  逐类别与封存原A核对后才调用已有preview_budget；原A不一致即停止，不替代准入。
- [x] 逐token保留所有必要成员及其copy前/操作内union、copy/sync/补集、原sync交集、H/D；
  Request/phase取操作union，不累加单sync B，结果独立版本化，旧版本和产物不改。
- [x] 复用本批8run封存结果和既有24链/受控证据，仅运行受影响回归；输出完整signed
  比较、GPU与COE倍数、扩展预算百分点变化及可证伪命题，不绘图或启GPU。
- [x] 核对封存模型inventory所绑config/输入构造与2048静态容量条件，明确未运行/未接新runner域；
  在现有短稿固定唯一待审点位/完整block/预算/停止条件，不生成执行包或服务器命令。

这是一项既有流程的有界实现计划，不新增资格层、独立collector或新测量定义。

## 7. 固定P输入轴Pilot最小接线（2026-10-17，用户批准本地实现及待审交付）

采用writing-plans的有界任务顺序，在当前main保留用户修改，不另建worktree或评审文件：
先独立手算/失败文件链，再接有限角色和输入，继而核对launcher和包。没有新S/A/B公式。
合同`COE-INPUT-P-PILOT/0.1`仅接受512/2048、batch1、输出2、w3/r1、FP16/eager/SDPA，
自然Host-readable完成和既有P准备不变；旧COE batch Pilot及O/P Engineering版本不扩域。
Envelope沿用已支持COE Pilot pass/producer/token/input 0.1.0的原结构，新增执行字段
observation_preparation仅对上述精确声明开放，必须验证实际cache消费及源码字节。

- [x] tests-first：有限绑定/输入和mask摘要、完整两token生产文件及准入、错误传播；最终验证见进度7.188。
- [x] 新输入模块及显式分派；复用P helper，准备前移内容不增不减，保留实际warmup/drain。
- [x] 分析器复用原两token闭合准入、COE和独立预算连接器，原A不覆盖，无巨型domain。
- [x] 完整block有符号ΔQ和`R=Q2048-Q512*(G2048/G512)`；G是对应phase union，不是累计W。
  R保留精确有理数及ns展示；G512为零、缺失、非合法数时R为null/UNDEFINED，不加epsilon。
  首token主要，第二token必报；null/零/反向不是自动追加或拒绝合法样本的理由。
- [x] AB/BA/BA/AB八个新P1编排，失败/完成即停，无额外2048试跑、不降级、不补槽；未执行。
- [x] 独立新阶段A实现（部署/CPU/参与卷新鲜空闲），真实回执审查及显式开关后才可B；目标A未执行。
  复用最近可信2d0d88e执行回执作前置；当前checkout须实查，不能用本地文档HEAD代替。

2048只有model config容量静态依据，没有目标机实际准入。预计35～60分钟、临时12GiB、
最终保留1～3GiB均为估计；长期目标50,000,000,000字节与启动资源分开，历史总量UNKNOWN。
本批只筛查固定带包装参考程序的非比例响应，不授纯等待、P0收益、稳定性、Formal或论文成功。

## 8. 当前来源的确认性准备候选（2026-10-22，未签署、未授权执行）

**7.240覆盖说明：本节保留7.239的候选历史；§9为当前安排。** 尤其§8.3的1024/2048、
4P1→12P1、六次全正描述规则与bootstrap参数均未签署、不是必经流程或现行统计政策。
当前优先保留512→2048主要比较，1024分叉为补充；资源恢复后按问题/预算一次固定。

Material Passport：research-protocol＋academic-research-suite/experiment-agent，plan；
`COE-CONFIRMATION-CANDIDATE/0.1`；状态`DRAFT_NOT_APPROVED_NOT_RUN`。
这是对既有候选的前瞻验证设计，不改§1～5、生产A/B或历史资格。研究设计v7.1的
§1.8/§3.3与Pre-Pilot协议v2.1的§3/§5.1要求区分正确性、信息与决策增量；本节只准备
其中**固定观测程序下的条件化完成结构验证**，不是完整7B/BF16、多平台或G2主矩阵。

### 8.1 完成边界与唯一主问题

- **旧路线保持**：[Gate13裁决](gate13_closeout_v0_1.json)的签署G12-ROUTEA/0.1.1、
  执行99f3bae/分析e19c308、60run/30profile/六block限定PASS不变。它没有授予新CUPTI、
  COE、完整自然默认流物理B或P1→P0组成迁移；旧Formal的COE演算仍为事后探索。
- **新路线已有**：6c744bf原DLL/SDK与活动策略0.2的真实A、event关联微例、768及新1024
  两token局部Engineering链，随后bd377c三点Pilot的9run/18链全部合格。查询政策及
  submit-effect-bridge0.3保留实际零payload逻辑节点、独立driver提交、双时间边界、
  closed-prior单FIFO局部必要后缀与terminal。证据见[参数/消费审查0.24～0.28](memset_parameter_feasibility_v0_1.md)、
  [三点来源索引](cupti_input_pilot_sources_v0_1.json)及[短稿§14](coe_research_short_note_v0_1.md#14-独立cupti三点pilot完整响应与1024高值2026-10-22)。
  这些是受限组件/实例/Pilot证据，**不是新路线全Q0、协议签署或Formal**。

主要问题固定为：**同一模型、P完成政策与CUPTI观测实现下，输入增长是否可重复地改变
必要工作在copy之前/完成操作之内的分布，而不只是整个phase GPU活动量的同比例放大？**
令每block、每token的`Q_L=COE_L`，`G_L=对应phase的GPU union`，保留
`ΔQ=Q_high−Q_low`和`R=Q_high−Q_low×G_high/G_low`。G_low无效或为0时R未定义，
不加epsilon；第二token的G只用Decode窗口，不能拿累计W当Decode新增活动。
另外直接报告必要成员在历史前缀、当前phase copy前、I内的位置；R本身不是因果模型。

已观察512→2048首token三次R均正；但1024→2048的R为
**+71.548881/−15.820230/+64.567864ms**，1024高值46.853457ms及第二token反向均保留。
因此不能把待验证问题写成“输入越长，每次都必然超比例”。竞争解释仍是输入相关工作/
布局与相对推进状态/观测影响共同改变位置，当前不能分离净份额。
同操作GPU union在这18链等于COE，完整依赖timeline可恢复同样判断；本方案不检验
方法独占性或算法优越性。COE、API墙钟、H/D、补集均不称纯Host阻塞或可消除时延。

### 8.2 只与主张直接相关的证据缺口

| 必需项 | 已有可复用证据 | 尚缺什么、为何影响主张、最小补法 |
|---|---|---|
| 当前provider的独立语义与算术 | [四token人工construction](completion_operation_controlled_validation_v0_1.md)独立规定2/4成员、已完成前缀、操作内D2H与terminal；CPU独立反例；768真实Raw独立成员/端点核验；九run协调成员核对及独立区间复算 | 四token是旧Nsight/Pinned来源；event微例只证明事件关联，0/64微例只证明参数/效果。现有来源索引尚没有**当前CUPTI→bridge0.3→COE针对先验已知completion集合**的目标受控闭环。Formal前仅补这个增量：优先复用原construction/独立expected，覆盖早完成前驱、操作内D2H、逻辑零节点及已证无关流/边界后提交排除；Raw独立端点扫描提供数值参考，不能由被测S生成expected。若实现/流不在实际支持域，停止而非借用旧资格；不重跑完整Q0或开发collector。 |
| 目标身份和资源 | 原A/event、九run pre/post库/源码/GPU身份及零丢失/溢出；固定参与卷12GiB检查 | 当前GPU被占用，全部新采集暂停。恢复时需用户确认分配独占时段、记录该时段使用约束与实际启动前后GPU占用事实；快照不证明全程绝无写者/竞争，无法确认则继续暂停或先审收缩为已知共享条件。旧批独占UNKNOWN不改。无须追索旧PID/ACL或建连续监控。 |
| 观测扰动适用范围 | [512/2048 O/P敏感性结果](observation_preparation_engineering_v0_1.md#2026-10-19八次真实结果审查)、当前CUPTI调用/标记及同钟规则 | 旧Nsight O/P不校准当前CUPTI的净扰动。**限定目标就是固定P＋该CUPTI观测程序**，因而不必新增P0或证明无插桩等价；若要求未profile自然性能/纯阻塞，则现有低成本设计不能验证，撤去这些claim，而非统一扣开销。 |
| 重复和统计单位 | 三个完整block、全部signed值、1024分叉、位置平衡及第二token反例 | n=3不能定精度、状态频率或平稳性。下一4P1仅作初筛；Formal重复数必须前瞻固定，候选见§8.3。新进程不自动等于独立同分布，token/kernel不能扩n；留出、顺序与时间结构敏感性限制推广。 |
| 输出、局部质量与排除 | 九run实际token均[[29184],[6556]]、完整二维input/mask、drain、参数/效果、闭包/terminal及容量检查；768/1024独立Raw复核 | 所选旧输入可复用精确token内容参考，但新run必须重新证明实际值/边界/源身份；不是独立数值精度认证。沿原硬门，零payload不虚构activity、非零缺效果/未知调用/闭包冲突/丢失均停止。零值、反向、1024高值不是质量排除项。 |
| 前瞻Formal身份封套 | 当前配置、producer、receipt/Canonical与候选版本的Pilot/Engineering链已实现；旧Route A Formal封套仅供机制参考 | [当前输入合同](../../scripts/cupti_input_contract.py)的输出政策只接Engineering/Pilot，[控制器](../../scripts/cupti_timeline_b.py)没有新路线签署Formal链。需在签署前补**限定角色/协议hash/源码与schema绑定及拒绝升级**，复用runner/消费者、不改测量定义。不能给旧配置改role就开跑。未实现，不假装文档即接通。 |

这是有界增量资格与封套缺口，不是要求重新取得全栈厂商认证、恢复默认流全物理B、
拆驱动内部等待、扫OOM或重做全部Gate。若独立成员验证发现与主张有关的真实错误，
按新版本审查受影响结果；不能凭本表默认旧结果全部有效或全部失效。

### 8.3 历史候选顺序与两种样本角色（7.240后不作为固定流程）

**下一批只推荐资源恢复后的4P1 Pilot筛查**：1024→2048、2048→1024两个完整block，
两token全部审查；固定batch1/output2/warmup3/repeat1、原FP16/eager/SDPA、输入字节、
P helper、同一6c744bf DLL/SDK＋0.3消费者。主比较为首token1024→2048的signed ΔQ/R，
第二token与全部baseline为预定描述。不是恢复4096、512全矩阵或任何旧失败入口。
选择1024是为了正面检验已有状态分叉，而非避开不利点；2048是同期高侧参照。
这项前瞻比较不改写旧Pilot预定的512→2048主要比较。

四次只回答“资源明确的新批次能否再次得到合格链，以及位置/方向是否重现”；不能估计
低概率1024高状态发生率、分离内部因果或认证Formal资格。正向加强有限可复核线索；
混合/反向削弱一致输入响应，应保留条件化状态解释；不判“坏样本”或据此加采。
若只出现两个1024低值，也不能排除先前高状态。筛查结束须一次审查研究主张；
**不论结果，均不自动进入Formal**。质量硬失败则立即停止，报告完整/不完整/未运行槽。

**正式验证合同候选，而非本轮预算**：保持上述两个输入，6个完整配对block、12P1，
顺序AB/BA/BA/AB/AB/BA（A=1024，B=2048）。六block只因3AB/3BA的固定成本与顺序
平衡推荐，**不是继承旧Route A的样本量资格，也不保证10/5ms、功效或稀有状态覆盖**。
其主要估计为首tokenblock级R的中位数，ΔQ、位置分布、Q/phase、Q/G及第二token全值
必报；不是验证256～4096普遍曲线、阈值、连续Decode或512→2048新的正式配对结论。
若论文必须支持这些更广目标，本候选不足，不靠本合同宣称其已完成。

统计/判定候选须在签署前一次固定：全部block原值、median/range、逐block留出与AB/BA
分层；列95%成块percentile bootstrap，固定seed=20261022、10000次，整对连同
两token/全部字段一起抽样，只作小样本描述，不用重采样次数替代n，不据窄区间保证精度。
样本内方向一致（六block ΔQ/R均正，且成员位置核对闭合、AB/BA无方向冲突）才记作
“本次固定预算内正向重现”；这是严格的前瞻描述性支持规则，**不是显著性、效应大小
或总体单调性门槛**。混合/含零表示一致正向主张未获支持，保留条件性/不确定；一致
反向则该方向主张不支持。不能将不支持写成证明无效应或等价。若独立性/时间结构不足，
将任何总体重现推断降为样本内描述，不用bootstrap挽救。

所有角色共用固定输出：原A与独立候选预算分开，逐token Q/kernel/MemOp/补集、原sync
交集、API count/sum/union、phase和同操作GPU union、copy/操作墙钟、H/D、完整成员/
提交来源及实际kernel布局。Request/phase以union去重，不累加单sync B。合法零/负值
和近同比例结果全部保留；无P0、不插Cpre、不扩点/后端，不把同窗union相等藏起来。

模型硬300s＋分析硬180s/run：筛查4P1合计**32min子进程硬上限**，Formal候选12P1
合计**96min**；传输/前后核验/封包另计。按原9run ZIP107.2MB，粗估筛查归档0.05～
0.15GiB、Formal0.15～0.45GiB，展开各约0.3～1.2/0.8～3GiB；尚非实际峰值保证，
12GiB新鲜参与卷预留仍必需。独立增量资格若需目标机受控执行，另行审1进程/1session/
120s预算，不塞入模型槽、不先实施。历史总容量UNKNOWN与长期50,000,000,000bytes
目标单列，不遍历ACL、不自动清理。任一必需身份/映射/依赖/terminal/容量错误即停，
未知writer不强行封包；预算到即停，无重试、替补、补采到显著或自动续批。全部合法run
保留；不完整block不能跨批/跨槽拼接，只能列partial原值，不进入完整配对估计。
质量接受与科学支持分开：即使完整数据的R为负或混合，仍可通过按冻结规则审查收口，
但不能据此判正向主张成立；文献新颖性也不是这项重复验证自动通过的结论。

### 8.4 历史Gate建议及停点（7.240后仅作证据索引）

**调整后续计划，不重排历史Gate，也不新增按长度/工具报错划分的Gate。** 在旧Gate13
之后列三个限定分支检查点（进度中使用稳定`EP-COE-01～03`）：受限资格/政策，独立
冻结，前瞻验证/裁决。它们复用已完成组件，只补本节直接缺口；不是重走Gate0～13。
旧Gate14是G2优化/held-out决策增益，保持NOT_RUN/后移；COE确认性响应不改名Gate14，
不自动启用D/Signature或决策/性能收益claim。

当前完成的是**候选设计**，不是检查点PASS或签署。GPU用户暂停仍有效，4096 NOT_RUN，
62b5a5a包及本地检查保留，不打包、不出服务器命令、不执行上述4/12P1。
下一集中确认应是：资源恢复后是否批准4P1筛查；以后是否接受限定样本内结构主张、
增量正确性证据及新冻结预算。没有授权则停在这里，不因文件完成自动进入执行。

## 9. 统一论文主线与问题驱动的验证准备（7.240，当前）

**主线不是“输入长度曲线”本身，而是：在明确的单GPU完成语义下，如何可核验地把必要
设备活动映射到请求/阶段的完成暴露结构，并判明活动聚合量何时充分、何时会误读、
何时仍不能解释。** 输入响应、N1/Cpre完成政策与O/P观测敏感性为同一问题的不同证据，
不预设拆成多篇。统一论文骨架与逐项证据/解释限制见[短稿§15](coe_research_short_note_v0_1.md)。
原S/A/B和独立COE仍是不同测量对象，不把COE改名生产Device wait或纯Host阻塞。

### 9.1 已实际完成的最小本地正确性准备

新增[独立construction/手算答案](../../tests/fixtures/coe_completion_reference_v0_1.json)
在消费前列明三个逻辑成员k/m/d、D2H terminal、count0逻辑节点与完成后的提交排除；
答案不调用S/COE集合恢复或区间函数。复用既有API22 callback/resource和producer/drain
fixture，只补**0.3隔离文件入口与预期成员的显式对照**，不复制collector或测量实现。

| CPU受控情形（人工ns，不预测硬件时长） | 保留的必要成员 / terminal | COE / 原sync交集 / 操作墙钟 / 补集 |
|---|---|---|
| 活跃后缀：k[30,55)、m[56,60)、d[61,62) | k,m,d / d | 20 / 15 / 30 / 10 |
| k已在copy前完成：k[18,20)，其余同上 | k,m,d / d，不删早完成成员 | 5 / 5 / 30 / 25 |
| k/m先完成，d在copy内部[42,43)完成、早于末尾sync | k,m,d / d | 1 / 0 / 30 / 29 |

固定copy[40,44)、sync[45,70)；必要集合截止于sync捕获的先行提交，包含copy之后提交的d。
后续同流kernel在Host完成之后提交，不进入成员。真实`-I -S -B`子进程先执行四源文件
hash绑定，再消费producer/marker→成功drain/copy/sync→scope文件→adapter0.3→bridge0.3
→COE结果；另复用既有两token producer/输入/hash/消费者来源与损坏拒绝检查。
[CPU检查](../../tests/test_coe_completion_reference.py)还要求缺非零效果、错流、缺count、
失败sync、晚terminal、重复记录产生明确原始拒绝，不能被0值或手写成功结果取代。
补集是本地参考报告明确以wall−COE派生，0.3接口未凭空添加字段。

**已验证的是CPU构造的成员、算术、版本/身份绑定与实际文件消费，不是新CUDA资格。**
此前Nsight四token独立construction、0/64参数及event微例、768/1024真实Raw核对直接
复用；缺口仍是当前CUPTI来源把先验已知completion成员/terminal交给同一消费链的
目标受控证据。可优先复用已有受控构造及独立expected，得到实际区间后独立扫描端点；
目标区间不能借用本表ns或CPU record ID，不用analyzer恢复结果充当expected。
若旧构造无法在现有限定scope中复用，先明确差额，不默认扩collector、跨流支持或完整Q0。

### 9.2 真正缺少的新实验及判别用途，不是固定工程清单

1. **来源增量正确性**：上述目标受控连接只决定“当前来源是否把预定成员/terminal与
   原始区间正确送到COE”，不决定负载规律。目标GPU条件恢复并另批预算后才考虑；
   若已有等效证据可精确覆盖同一差额，则直接复用，不为完成编号再跑微例。
2. **主要响应的前瞻复核**：优先保留固定P、同期512→2048首token的signed ΔQ/R，
   第二token、全部原值/成员位置和公平baseline完整保留。它区分“该固定观测程序下的
   超同比例响应能重现”与“当前样本不足以推广”，不能分离驱动/硬件/观测净因果。
   1024分叉与O/P是必须披露的补充证据，不用1024替换主比较，也不要求新采才能披露。
3. **仅当扩大解释时才需要的证据**：若要外推未profile P0、包装无扰动或精确Host阻塞，
   现有设计不能支持；不将它们偷偷加入本次目标，也不靠有限重复或统一扣开销取得。
   同操作GPU union=COE与完整timeline同答本来就成立，无须再采去证明数值独占优势。

4P1/12P1均降为可调整的**历史成本候选**，不是先筛查再Formal的必经序列；不沿用
“六次全正”作为已定科学门，不预定必须用某次bootstrap或达到10/5ms。资源恢复后，
依据唯一主要比较、现有波动和可用预算，一次确定点位、完整block数、顺序、统计与
不同结果的结论，再签署/执行相应角色。此后不能按方向补采、替补、删除不利点或拼
不完整block；质量接受与主张获支持分别裁决。旧Pilot不升级为前瞻Formal。

EP-COE-01～03编号保留，仅作“直接证据／冻结／前瞻结果”的导航；不是新增强制Gate
流水线，不自动授予PASS或GPU预算。4096和其他目标GPU采集继续暂停，无包/命令。
GPT未来可用能力受限不构成停用本地CPU测试的理由；本轮照常完成相关检查。

## 10. 当前provider的受控连接：可执行准备0.1（7.241，目标NOT_RUN）

复用的实际程序是[`gate8_qualification_token.cu`](../../scripts/gate8_qualification_token.cu)：
legacy NULL流，单int kernel、Pinned D2H、stream同步和Host读回。原源码字节不改。
原程序缺少memset出口，因此仅由[`coe_cupti_controlled.cu`](../../scripts/coe_cupti_controlled.cu)
include它并增加`ep_coe_abi=1`和`ep_memset(size_t,int)`；后者只允许0或4bytes并转发
原`cudaMemsetAsync`。它是受控程序，不是新collector，不复制S/COE。

采集复用`exposedpath.cupti_timeline.CaptureSession`、已审6c744bf的client.dll
（SHA256 `5e0ffa4b332652c6107cb278ed300ddc9b1bc0e201a370dbe1040cb463d2247a`）、
CUPTI12.4.127/API22及activity-policy0.2；消费复用adapter/bridge0.3、distinct-boundaries0.2
和五类精确driver-query政策0.1。真实A/event-B引用仍为7.201及后续已审原件，不能用
本地新程序的编译成功替代它们。本轮未重建或加载client.dll。

### 10.1 先验构造与独立答案

固定计划[`coe_cupti_controlled_v0_1.json`](../../configs/coe_cupti_controlled_v0_1.json)
在读取未来Raw之前给定以下顺序，所有调用同一Host线程/实际NULL流：

`成功device drain → request point → kernel(17) → 成功early stream wait →
memset(4,0) → kernel(23) → memset(0,123) → copy D2H(4) → 成功paired stream wait →
Host读回23 → token point → future kernel(29) → future wait`。

- 必要设备成员固定为early kernel、4-byte memset、late kernel、D2H；early kernel
  被early wait强制完成，仍须保留在必要集合中，不能按pending删除。
- 0-byte memset保留为实测参数/逻辑提交节点，预期无设备activity；若参数缺失、实际
  非零而缺效果，或零参数却有冲突效果，则拒绝，不能因程序预期0而覆盖Raw实参。
- terminal预先固定D2H，不从被测S的最大end选择；实际端点须证明先行成员已完成且
  D2H不晚于配对成功sync。配对sync捕获的提交边界是截止点，D2H在copy内部提交也必须纳入。
- Host读回/point之后才调用的future kernel排除；不做跨流、event或graph资格外推。
  原init/资源建立在成功drain之前，仅用于闭合历史和资源身份，不冒充本次局部后缀。

独立参考分两层：构造决定逻辑成员/terminal/排除项；当前捕获的显式步骤范围、domain/
PID/TID/CBID/correlation及真实父子关系只把它们映射到Raw ID。时间答案由这些实际
Raw区间单独作端点计数扫描，得到copy入口→paired sync返回内的union交集、原sync
交集、墙钟和补集。参考不调用`recover_suffix`、`completion_overlap`或S结果生成expected。
先保存reference，再调用被测0.3文件消费者逐项比较。CPU测试的16/11ns等数字**不是**
未来GPU时间预期；合法零交集不失败，交集大也不构成额外成功依据。

### 10.2 已接通的文件链与边界

[`coe_cupti_controlled.py`](../../scripts/coe_cupti_controlled.py)提供既有session的最小接线：
精确源码/库/设备配置 → 隔离模块来源 → 原session先打开 → init/资源身份 → 构造步骤及
side.json → session close/质量 → capture.json → 先验reference → scope文件 →
原adapter/bridge0.3结果 → 成员/terminal/算术对照。callback采样与API activity边界仍
各按原0.2规则核验，不新添容差。Raw和side只读，新派生目录不覆盖。

默认没有执行授权即拒绝；未来显式入口复用原有bounded-process helper，以单进程、
单session、零模型/零Nsight、硬120秒为上限，无封包/重试/清理。超时沿用UNKNOWN writer
记录，不把终止父进程当作子进程都已退出。配置需要另批执行身份、实际程序build/hash、
已审client/CUPTI/runtime、GPU UUID/PCI/可见掩码和新输出路径；本轮不填目标配置、
不提供服务器命令或部署包，GPU暂停状态不变。

### 10.3 本地验证与目标仍缺的事实

本地实际用CUDA12.4.127头文件、nvcc12.4.131、legacy默认流、显式sm_89、shared
CUDART完成编译/链接和11个ABI导出/import检查，未执行或加载生成DLL。最初受限执行
中cl以访问异常失败；同源码/同参数在非沙箱编译环境成功，两份原始日志均保留，
不推断更深层根因。本地MSVC14.44与目标已审14.38不同，且本地用了显式
`--allow-unsupported-compiler`；这**不授目标工具链资格**。未来目标构建不沿用该本地开关，
不重编已审collector。CPU替身检查真实步骤、side/marker、隔离文件消费者和具体拒绝，
不是实际CUDA执行，也没有重跑7.240的72项检查。

目标仍须取得：目标编译产物/实际加载runtime身份；真实callback参数、资源/流/父子关联
及设备效果；early成员已完成、0字节实参、D2H terminal和Host值23；丢失/溢出/关闭为0；
最后用实际区间独立对照。任一未知或不支持调用均停止，不扩collector/跨流支持。
本构造是**Pinned 4-byte**单FIFO参考，不等于自然PyTorch的Pageable token复制行为，
即便将来通过，也只关闭该来源的这项受控连接差额，不授全部Q0、自然内部阻塞、
完整物理B、COE Formal或负载规律。新GPU结果与前瞻复核均保持NOT_RUN。

## 11. 512→2048前瞻复核候选0.1（7.242，未授权执行）

Material Passport：research-protocol / ARS experiment-agent plan；2026-10-22；本地配置
准备，不是新实验或Freeze。唯一主要问题固定为：**同一模型内容、P自然Host-readable
政策和CUPTI观测实现下，首token必要活动在完成操作内的执行量是否再次出现超出phase
GPU union同比例参照的响应？** COE不是纯Host阻塞或它的近似；第二token完整报告，
1024分叉及O/P幅度敏感性作为既有补充证据，不另加槽、不拼旧样本。

### 11.1 推荐4完整block/8P1的依据和范围

候选顺序为`512→2048；2048→512；2048→512；512→2048`。正反次序各两次，每点
在两个执行位置各两次，前两块/后两块也各含一次正反。每run新进程，w3/r1、batch1、
output2、FP16/eager/SDPA和原P/完成边界不变。位置平衡不消除非线性漂移、外部竞争或
跨run相关；新进程不等于统计上已独立。

已有bd377c三block首token端点R为+70.513613/+80.496420/+62.326314ms；1024的
3.115148/46.853457/3.299398ms和第二token反向说明不能用端点三正保证平稳。选择四块
是**在每种次序至少有两次、能作顺序/留一描述的最小平衡预算**，不是由三样本估计出
功效或精度。两块仅每次序一次；三块不能正反等数；六块没有现成的精度/功效依据，
故本次不机械继承旧4P1/12P1方案。四块只能作固定观测程序的有限前瞻重现，不能冻结
普遍稳定域、10/5ms精度、阈值、P0时延组成或硬件因果。

### 11.2 可检查的声明和复用入口

机器声明为[`coe_endpoint_replication_v0_1.json`](../../configs/coe_endpoint_replication_v0_1.json)，
包含原512/2048输入**文件字节**、完整[1,L] input/mask摘要及逐值token参考
`[[29184],[6556]]`，模型清单摘要沿bd377c原件；不重构/归一化输入。内嵌原严格
`CUPTI-INPUT-PLAN/0.2.0`，没有新增长度schema或角色。小型CPU适配
[`coe_replication_prepare.py`](../../scripts/coe_replication_prepare.py)只做声明/输入绑定，
调用现有`schedule`、`one_configuration`和`summarize`；原采集、producer、两token准入、
预算/空间及失败停止链不改。`execution_plan.json`与`preparation.json`是本地准备产物，
不是可执行交付、真实执行seal或运行授权。

候选当前用已有Pilot角色，`execution_commit=null`、`gpu_authorized=false`、
`formal_eligible=false`。如要将新数据称正式确认性证据，必须执行前完成当前来源直接
正确性差额审查、资格/排除/协议签署及相应Formal身份封套，不能把本计划改个role就
升级。本文没有实施或要求现在开发该封套；旧Engineering/Pilot不升级。

主量为每完整block的`R=Q2048−Q512×G2048/G512`，主要统计量是四block等权平均R；
同报signed ΔQ、全部原值、mean/median/range、两次序均值、前两/后两均值和留一完整
block均值。分母无效则R=null并列明block，不加epsilon、不用其余块冒充完整主要均值。
第二token独立列为次要，不把其累计W当Decode新增活动，不视token/kernel/sync为重复。
不预定bootstrap或p值，不用重采样次数冒充样本量，不调整旧10/5ms目标后宣称达到。

数据质量、科学方向、论文增量分别裁决：

- **质量**：身份/输入/输出、成功drain、参数/正长度效果、依赖/scope/terminal、
  dropped/overflow等沿原硬门；失败立即停，已完成/失败/未运行槽位全保留。不得按R、
  占比、零/负值排除，也不拼不完整block。
- **方向性复核**：若主要平均R、两次序均值及全部留一均值都正，仅支持“本批固定P
  的方向性响应重现”；它不要求四次全正、不提供显著性/总体可靠性。平均与敏感性均
  负则不支持正响应；零、方向冲突、未定义或质量缺证则不确定/不可评估。ΔQ另报，
  正R不自动等于绝对Q增加。全部结果均不触发补采、替补或更换统计法。
- **论文**：正向复核不证明COE优于同操作GPU union或完整依赖timeline；反向/混合会
  收缩“输入端点稳定响应”的描述，但不抹去已验证成员/算术。质量失败只限制该次
  适用性，不作为方法无价值或正假设成立的证据。新颖性与解释用途仍需独立论证。

公平参照保留API墙钟/可审计API union、原sync交集、phase GPU union、同操作GPU
union和完整依赖timeline、H/D/成员/提交及布局。旧来源已合格A/overlay单列；**当前
CUPTI0.3入口不输出完整五类A及整窗候选预算，保持NOT_ASSESSED**，不能用局部API union
冒充或从COE直接相加。主R不依赖该整窗A资格，不为这批复核暗增accounting工程。

### 11.3 资源及停止点

已封存九run展开文件共1,970,793,104bytes；512/2048六run分别合计656,624,234/
653,506,526bytes，以同量级外推8run约1.63GiB。候选预留展开保留1.5～3GiB、ZIP
80～200MiB、参与卷新鲜12GiB；历史YLQ总量仍UNKNOWN，长期<50,000,000,000bytes另管。
原process回执没有elapsed字段，不能把旧估时当已测端到端耗时；本批30～55分钟仅
规划估计。现有模型300s/分析180s×8的子进程时限之和64分钟，不含身份/I/O/封包，
不是整批墙钟保证。固定八槽或任一硬失败即停，无自动重试、替补、续批、清理。

执行前必须另审资源恢复/环境、当前来源受控GPU证据、最终角色/政策/预算、实际执行/
分析commit和输入身份、新静态回执及空间、显式授权。本轮不构造交付或命令，不恢复
4096/1024/provider/hook/batch采集；7.241程序、编译及24项证据直接复用。

## 12. batch参数化影响清单（7.242，只读审查；未实现）

当前CUPTI计划/model合同仍是batch1、输入[1,L]、两token各一Host ID。**底层runner已
支持[B,L]运算不等于当前入口已支持B。** 具体位置和最小差额如下，不修改这些文件：

| 层与当前限制 | 若将来扩为[B,L]的最小差额 |
|---|---|
| [`cupti_input_contract.py`](../../scripts/cupti_input_contract.py)的`input_identity`要求单sample、shape[1,L]；`validate_model`固定1 | 配置单独声明B，记录有序sample_indices和完整B行input/mask/shape摘要；即使每行相同也不能复用单行digest。输入文件字节另绑；不是按L豁免 |
| [`gate11_pilot.py`](../../exposedpath/gate11_pilot.py)的`cupti_plan_schedule`、[`cupti_input_pilot.py`](../../scripts/cupti_input_pilot.py)的`one_configuration`均固定batch1 | 版本化配置、slot/run/producer身份含B；旧0.1/0.2读取不放宽。B与L为不同轴，不改旧身份或把旧B1/B4加入新block |
| [`cupti_timeline_model.py`](../../scripts/cupti_timeline_model.py)只构造`samples[0]`，setup和consumer验证shape[1,L]；scope逐token要求len1 | 依sample顺序构造全部B行tensor，贯通setup/input/token/producer/hash检查；逐token保存B个实际Host ID，输出矩阵为[2,B]，不得填缺失值或预设各样本相同 |
| [`runner.py`](../../exposedpath/runner.py)的`run_one_invocation`已用shape提取B、向量argmax和B个Host ID；P的[`Execution.prepare`](../../exposedpath/observation_preparation.py)缓存绑定包含manifest摘要的完整identity | 可复用原`.cpu().reshape(-1).tolist()`批量读回和P闭包，不新增同步；未来由新版本manifest摘要传递B/样本顺序绑定，并验证实际输出数量，不必为B重写P helper，不借改变L偷偷解锁 |
| runner当前任一sample出现EOS即结束整个batch；新消费者`validate_tokens`/`producer_scopes`仍要求每token长度1 | 明确保留“任何样本early EOS则整次排除/停止”的有限政策，先不做动态batch/逐样本结束。逐token向量均已Host-readable才是整批锚点；当前不提供每样本独立完成时间 |
| 当前S/COE输入scope和`token_metrics`是PID/context/stream/单invocation，非batch维度；`summarize`按L成块 | 作为**一次batched invocation**恢复合格实际提交前缀和terminal，保留已完成成员；不把数学数据依赖/每样本ownership凭B拆分。Request/phase和候选操作union一次去重，不乘B、不跨sync累加B |

旧`batch_load.py`已有512/B1/B4有序样本、token矩阵/EOS及边界经验；只复用工程设计，
不授当前CUPTI/P包装batch资格。旧B4 Prefill局部可用而Request/Decode BLOCKED保持。
新CUPTI的core以实际uint64 count/bytes、PID/TID、context/stream/correlation及kernel布局
记录，无batch1专用过滤；当前证据**没有要求修改collector的依据**。先改producer/输入/
消费者适配才有意义；若将来真出现未知API、容量/映射/依赖缺口则原样拒绝，不能预告必过。

具体科研用途只保留一个：未来若输入端点响应得到有限复核，在固定L和P下改变B，检验
“较多必要活动在copy后执行，仅依赖输入长度触发的某组实现/布局切换”这一解释。
若固定L、可比较布局下COE/G仍明显改变，将削弱该**仅由输入长度分支解释**；若G增加
但位置/比例不变，则限制把端点响应推广为所有工作量增长。布局和位置一起变化仍无法
分离内部因果；单次零/负或未知不决定方向。B不等于L、同样总token数也不是同负载。
该用途依赖实际分支/成员/位置，不以更大wait为选点目标，不授并发用户请求研究。

**结论：batch值得保留为解释的反证轴，暂不实施。** 首先完成本节端点复核的政策审定；
若只想增加配置数或当前论文无需区分上述解释，则继续暂缓，而不是扩矩阵或collector。
