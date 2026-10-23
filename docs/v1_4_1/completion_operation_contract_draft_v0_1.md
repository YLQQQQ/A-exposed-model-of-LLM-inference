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

> **7.243论文用途裁决：** 以下4block/8P1机器声明及本地接线保留，不执行、不作为固定
> 工程流程。现有数据足够支撑有限探索性正文，但不足以宣称独立前瞻重现；如要保留后者，
> 资源恢复后一次审定最终角色、数量、顺序、分析及停止规则，不默认先Pilot再追加同用途
> Formal。现有配置仍是未授权Pilot候选，不能通过改role升级；源文件不改、预算未新增。
> 当前唯一论文主稿及最小缺口见[主稿§7](exposedpath_unified_manuscript_v0_1.md#7-最小证据缺口与前瞻复核的论文用途)。

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

## 13. 理论关系、机制判别和工程差额（7.244，GPU暂停）

2026-10-22～23；研究协议/ARS plan与CPU验证准备，不是新测量定义、Freeze或执行授权。
暂停统一主稿继续扩写/修订；保留7.241受控准备、356a38f八次候选及4096原准备，不执行。
本节只补此前未分开的关系和具体差额，沿用§14机制来源，不重做已有统计/组级分析。

### 13.1 可以证明什么：量、位置和实际完成不是同一个变量

令U为已合法恢复的必要活动**区间并集**，不是时长直接相加；a为目标phase起点，
c为copy入口，r为配对成功sync返回，p为Host读取后的共同point，均取同一trace时钟。
定义V=|U∩[a,r)|、F=|U∩[a,c)|、Q=|U∩[c,r)|。若a≤c≤r≤p且必要成员属于
phase GPU观察scope，则严格有：

`V=F+Q；0≤Q≤min(V,r−c)；V≤G_phase；Q≤G_phase；Q≤p−a。`

若逐成员时长求和为C_sum，则V≤C_sum；存在重叠时可严格小于，C_sum也不是FLOPs、
理想设备服务时间或GPU对Host的因果成本。上述G_phase含同一PID/device/context的
观察活动，只有U确为其子集、窗口可比较时才允许这个界，不向未支持的ownership推广。

证明只用半开区间的互斥分割/集合包含。它不是“纯Host阻塞的下界”。第二token的累计W
含前一phase历史，故必须裁剪到本phase才有V≤G_phase；不能拿累计|U|和Decode G比较。
非零必要集合可以Q=0，重叠成员只算一次。τ是合格terminal的完成时刻，τ≤r；`τ−c`
包含间隙，既不等于Q，也不独立识别Host阻塞。

对于**固定U、固定r**且c1≤c2≤r，精确有
`Q(c1)−Q(c2)=|U∩[c1,c2)|∈[0,c2−c1]`。这说明更早到达可使Q不减，但不能用于
把不同run的Q差分解成“Host效应”：真实c改变时，后续提交、设备轨迹或r也可能改变。
当τ是这些成员的最晚完成时刻时，另有`Q≤max(0,τ−c)`，这个区间上界仍不是等待真值。

实际性能保留Host时钟的`TTFT_H=h0_H−start_H`和后续`ITL_j=h_j_H−h_(j−1)_H`。
h为实际读回后采样，不是token网络发送；r在程序顺序上先于h，h先于p。但Raw中的c/r/p
与perf_counter的h不处于已校准同一数值域，**不能直接计算h_H−c_trace或h_H−τ_trace**。
上面的Q≤p−a是trace投影界，不宣称它给出Host TTFT的已测误差界。H取copy入口前已返回的
必要提交API中最晚返回至c的间隔，不把操作内随后提交的D2H排除出必要集合；D等时间
位置量也不是Host净阻塞或包装耗时。

一个仅用于推理的简化模型是假定所有必要工作已提交、其轨迹固定且连续为[0,τ)，
Host到达c不改变设备推进、没有后提交D2H/Host有用工作/内部间隙，令`r=max(c,τ)`，
Host完成`h=r+1`。这些条件**不适用于直接解释自然memcpy_and_sync**：实际D2H可在
操作内提交，轨迹、API内部行为及尾部不是固定常数。独立CPU整点手算给出最小反例：

- 固定U=[0,10)，c从8提前到2：Q从2变8，但h仍11。更早到达可以增加COE而不拖慢完成。
- U=[0,10)、c=9时Q=1/h=11；换为U=[0,8)、c=2时Q=6/h=9。
  COE变大同时完成更快；反向读即COE变小而完成更慢，否定跨运行的单变量性能推论。
- U=[0,20)、c=19时Q=1/h=21，相比U=[0,10)、c=2的Q=8/h=11，
  必要工作增多、完成变慢，COE反而减小。U=[0,4)∪[8,10)、c=2时Q=4，而τ−c=8。

这里是CPU构造ticks，不是真实CUDA纳秒或新oracle资格。不同运行的c、设备轨迹、尾部
都可改变，故COE增加/减少均不能单独推出实际完成变差/改善。若两端G都正，既定
`R=G_high×(Q_high/G_high−Q_low/G_low)`，所以正R只是Q/G结构比增加的代数描述，
不是对完成时延、根因或优化收益的判据。

### 13.2 三个可证伪假设及最小判别，不新增采集流程

**M1：端点正R伴随输入相关的必要后缀未在copy前消化，而非仅总活动同比例增加。**
已有支持为bd377c三次端点正R及实际kernel执行位置；2048交集主要来自先行kernel，
不是8-byte D2H。反例/约束是1024同布局分叉、第二token反向、O/P幅度敏感，静态布局
或工作量不能单独解释全部幅度。缺少的是固定观测程序在新资源条件下的前瞻重现，不是
再算旧CSV。最小干预沿保留的512/2048候选改变输入，固定P并报告F/V/Q/G和实际布局；
若Q/G与R不重现，收缩端点规律；重现只加强条件化后缀描述，**不能单独分开工作量和
实现/布局的因果份额**。八次候选不因此自动执行或改角色。

**M2：重复的观测Host准备占用请求关键路径，能改变时延/到达位置，但不是全部幅度根因。**
已有支持是O/P的现场工作确实减少、H全降；反证是D变化远大于H变化，1024高值H不是
最大。缺少直接的低观测性能对照和更窄的准备消融。最小干预只使用下一小节的边界
payload预备候选，保持数学计算、实际读取、同步和动态标记顺序；若现场准备减少而
TTFT/ITL不改善，就否定该候选的性能预期，不能改用Q下降宣称成功。若仅trace位置或Q
变化而Host性能不变，仅支持观测敏感性；若两者混合且波动较大，保持不可判别。

**M3：同布局长值包含未被必要设备执行覆盖的操作间隔，观测实现可能影响它，但根因未知。**
1024高值的108.717448ms内部未覆盖间隔和较少copy前完成进度是支持；它们不是硬件空闲
或profiler因果证据。缺少的是同合同低观测运行是否也出现长完成时延。最小判别是将
保留同一业务/完成政策的低观测参考与CUPTI观测分开、按预定次序复核实际TTFT/ITL：
若无CUPTI仍出现长值，削弱“必须有CUPTI才出现”的强说法；仅CUPTI样本出现则支持
继续审查观测敏感性，却不因有限未见证明自然路径绝无长值。此项不恢复内部驱动取证，
也不能用不同运行的时钟/参数拼接解释旧1024。未知内部原因继续UNKNOWN。

低观测参考只能观察其Host完成长值，不能在没有trace时断言“同布局/同108ms空隙也已
复现”。同输入/backend并不证明两次kernel轨迹相同。因此该对照最多反驳观测实现的
**必要条件**说法，不能精确标定CUPTI开销或分离旧run内部原因；两种机制可以共存。

事实/来源直接复用[三点Pilot§14.2～14.5](coe_research_short_note_v0_1.md)、
[全部位置来源](cupti_input_pilot_positions_v0_1.json)及[O/P实际结果](observation_preparation_engineering_v0_1.md)。
上述三个问题不意味着三个新实验；未来资源/预算恢复时只选择能改变判断的一项，
不把剩余内部机制全部设为前置。

### 13.3 唯一优化候选：边界静态payload准备，先不改生产P

源码核对定位到[`Gate8BoundaryRecorder.observe`](../../exposedpath/gate8_boundary.py)：
每次重新deepcopy身份、构造静态payload、`validate_shape`并JSON编码。P helper虽已
预备helper label，**没有消除此处重复准备**。选定的唯一候选是绑定run/request/ordinal
后，在现有最后drain之前预校验并编码这些不变边界内容。时间戳、顺序检查、实际Host
token、NVTX发出和CUDA调用保持现场执行；错身份/缓存/边界仍拒绝，不能把动态token
读回放到准备阶段。它是**观测实现开销优化候选，不是已发现的模型算子优化**。

在原runner中，请求开始record位于`t_start_ns`之后、forward之前，这段准备可以直接
进入TTFT；首token完成采样后的record不会改变已记录的首token时间，却可能推迟下一
Decode提交并进入后续ITL；末token后record主要影响trace point而不是已采末token时延。
不能把所有三次准备都从TTFT减去。[实际顺序](../../exposedpath/runner.py)

新增**仅测试内CPU原型**，调用真实边界schema，与原记录器在pass0/pass1下逐字节比较
label/payload及动态时间/顺序。现场schema校验与编码确已移除，错run、缓存、顺序和时间
仍拒绝。两轮小探针各三个CPU交替批次、每方案100次，三边界现场耗时分别处于
0.767～0.952ms与0.0040～0.0056ms；**含准备的总成本**保留全部批次配对：首次旧/新为
0.903/0.895、0.919/0.970、1.103/1.169ms，最终为0.890/0.878、0.896/0.886、0.890/0.895ms。
总成本方向混合，不能宣称已降低或等价。这里只证明可移出该关键路径，不能
外推目标GPU TTFT改善，更不能解释此前几十毫秒差异。本地Python3.12.7非目标3.11.16。

该CPU计时使用Engineering身份、空marker sink及常数诊断时钟，只测Python现场工作；
Pilot身份另作字节/顺序等价验证，未将两种身份计时混在一起。真实marker/采集/设备推进
成本均未进入这个小计时，不能把微秒差当作目标机性能预报。

这还是时间位置变换而非已证净优化。逐请求身份/标签准备的总成本必须连同setup另报；
若产品侧request到达后才能准备，不得将其藏在到达之前，或把仅模型窗TTFT改善表述为
端到端请求获益。当前先验证同一“resident＋drain后开始”的参考程序窗口，未来若要
服务时延结论，必须同时给出含必要准备的可比端到端时间，不能换起点取得收益。

未来性能主量必须是同一开始/Host-readable结束合同的TTFT或预定ITL，准备/setup成本另报。
低观测参考无CUPTI/Nsight且不作逐API记录，但两方案都保留相同必要业务控制、实际读取及
完成时钟；不能把现有“未开Nsight的P0”叫无包装。当前P.prepare限定pass1，**低观测P
入口尚未具备**，需明确的新Engineering观测模式/身份，不能把旧role改名接入。CUPTI只
解释对应观测运行，不用其时延代替低观测结果，不统一扣profiler成本。若要正式接入，
必须另绑实现/hash及等价/失败文件链；本轮没有修改runner/helper或安装此原型。

### 13.4 当前CUPTI接回完整A：复用点与停止差额

可直接复用原[`a_accounting.py`](../../exposedpath_v141/a_accounting.py)原子分区、
union/裁剪、五类互斥、同步优先级、子类守恒及invalid传播；
[`submit_effect_bridge.py`](../../exposedpath_v141/submit_effect_bridge.py)0.3已保留实际API
区间、typed效果边、逻辑零节点和query来源，`owners`已按runtime/root-driver筛选，
嵌套driver不再次加入API墙钟。这一排重不是待重写算法。

但完整A**不是把accounting_api_union_ns换字段名**，尚缺四项明确源合同连接：

1. **Canonical/ABInputs lineage与ownership：** 新source的同钟point、完整request/phase
   和producer身份必须经版本化投影进入ABInputs；不能伪造Nsight provider manifest、
   把callback采样时刻当ActivityAPI时刻，或复用旧seal。
2. **分类/submit证明：** 原A按旧API registry及correlation效果判定；新0.3的五类独立
   driver查询、root driver提交、零payload逻辑提交不能凭名称/缺activity自动获得类别。
   需新来源的精确domain/PID/CBID/返回/父子/效果证明桥，保留旧registry和旧读取。
   原始分域correlation不能压成未经证明的同一整数，也不能为count0造activity。
3. **完整同步集合：** 两个token的局部结果不是整窗每次物理同步的S覆盖。须枚举本窗
   必需同步、内部driver同步及其捕获提交边界、W/terminal/validity，按原优先级从外层
   API扣除同一片段。driver API行缺失时不拿callback包络补Host区间，未知保留。
4. **全窗API owner及未解决量：** 现有owner去重/查询来源可复用，但需证明没有遗漏
   standalone owner、窗口外/worker ownership或跨边界调用。opaque allocation仍须独立
   admission，未知分类/未解决同步进入unattributed，不能自动转Host或non-submit。

本轮直接向旧A提供独立CPU夹具：基准100 ticks为Host60/API20/wait10/residual10；
若天真加入嵌套driver查询，其中5 ticks变unattributed；只有零memset而无设备效果时
原A也保留5 ticks未知。它揭示旧入口所需证据，不是缺证场景应追绿的错误。
**停止完整A接线：公式无需改，但新来源分类/同步投影合同尚未完整绑定，不能绕旧门。**
当前不改A定义、registry、collector或输出可信全A；COE继续独立，不冒充Device wait。

旧A接线的最小验收不是要求所有残余归零，而是：完整同钟窗口和typed API owner清单、
全窗sync universe与S结果一一对应、对每个API片段有分类证明或显式未知、完整来源hash。
输入完整但部分同步/类别不支持时仍可按原规则输出含unattributed的守恒结果并报告拒绝
范围，不能把“全A”解读为“全部内部机制已解释”。局部token结果不足以给未审同步
填VALID_EMPTY；没有实际Host API区间的内部同步也不能补造。该输入层协议未绑定前
仅保留本节夹具/差额，不为显示五类而做不可信预算。

### 13.5 batch与输出轴的短设计，仅审差额

**batch候选**为L=512/1024/2048、B=1/2/4、输出2，共9个条件；**输出轴**独立为
L512/B1、输出2/8/32。不得先做输入×batch×输出全交叉、动态batch或把旧样本拼入新block。
未来若审三完整block，分别是27和9个新运行的**数量候选**，当前无GPU预算/固定顺序授权。
batch的三block只能让各条件重复三次，不可能使九条件各占全部九位置；输出轴三条件可
循环位置，但都不能消除漂移。最终顺序和主次比较必须执行前一次固定，不依结果改矩阵。

最小实现/验证范围具体为：

| 层 | batch差额 | 输出轴差额及共同验证 |
|---|---|---|
| 配置/身份 | `gate11_pilot`、`cupti_input_contract`与`one_configuration`目前固定B1；slot/run和摘要须同时绑定L/B/output | 计划与模型合同固定output2；显式新版本，旧0.1/0.2及历史角色不放宽。参数可声明不等于GPU资格 |
| 输入/模型 | 构造并hash完整有序[B,L] input/mask、sample_indices及文件原字节，不能复制单行digest | 模型长度/词表/EOS按L+output核对；不改32周期输入、FP16/backend/P自然政策，未知预期token不能沿用29184/6556补齐 |
| producer/P | `cupti_timeline_model.run`只取samples[0]，setup固定[1,L]；scope验证每步len1 | P.prepare/finish固定两label/used[0,1]，warmup/resident_capture也固定2。按全部输出步预备唯一标签，不改变实际读回与同步；原runner已循环output_len和向量Host读回 |
| 实际完成 | 输出为[步数,B]真实Host ID，每步B个值都可读才是整次batched invocation完成点 | 存实际N+1个边界；缺步、重号、错run/sample或提前结束均拒绝。任一样本EOS按固定输出政策使整run排除/停止，不填充缺token、不中途缩B；EOS集合须显式绑定 |
| S/COE与汇总 | 同一批量invocation按实际scope/顺序恢复，不分成B个独立请求 | producer_scopes、token_metrics、summarize、B后验读取均有“两token”限制，须联动改；W_j截止于各自sync，保留历史但不作Decode新增活动量，未来提交排除 |
| A/预算/统计 | 每批只有一组全局完成时延，不提供每样本独立时延，不把预算乘B | Request/Prefill/Decode原子区间去重，操作间union；trace逐token窗口[p_(j−1),p_j)与必要历史分开，不能用Host的ITL作trace COE分母。run/block承担重复，token嵌套，不当独立样本；原A与COE分开 |

上述边界内容正反例需覆盖[B,L]顺序/完整摘要、[N,B]实读值、缺step/错sample/EOS、
提交/terminal失效及跨token去重；预期token的独立参考/低观测逐值配对必须分开，
同配置两观测模式一致也不证明数学数值正确。旧B1/B4仅复用设计经验，不授新CUPTI资格。
目前没有batch必须修改collector的证据；未知API/映射/依赖仍照常拒绝，不预告B2/B4必过。

**用途和比较应随轴分开。** batch轴在每个固定L内，B4−B1的signed ΔQ和
`R_B=Q_(L,4)−Q_(L,1)×G_(L,4)/G_(L,1)`为拟定端点比较，B2作预定中点描述；
并报整批TTFT/实际输出数，不将TTFT除B称作每样本时延。它检验“仅输入长度触发的
实现分支足以解释位置变化”的强说法，但B也可改变实现/布局；只有实际布局可比较时
才给相应限制性判断，不能凭输入token总量相同强认负载等价。输入内比较按各固定B
单列，全部signed及分母失效null保留，不跨batch/旧批拼block。

输出轴的主用途是观察j=1～N−1的实际ITL序列及每run预定Decode平均ITL是否随生成
推进改变，首tokenTTFT另报；COE_j/trace逐token窗与同窗GPU union仅作结构解释。
共用前两步可以描述，不把输出2的第二token代表整个输出32。长生成的KV前缀、实际
后续token以及按N暖机后的内存状态可能共同变化，不能把差异全归为“输出数量”因果。
每run的后续步是相关重复，跨run/block才承担实验重复；不把几十个token扩成n。
确切统计量/顺序/角色/预算须另审，未执行或不可评估的条件留空，不做插值或追单调。

目前`validate_tokens`逐值拒绝EOS，原runner遇EOS停止；最后一个预定输出步出现EOS也
不得静默改成成功政策。将来应同时记录实际步数和命中EOS的样本/步号，再按已审固定
无EOS合同整run排除并硬停，不删除该失败点后补block。新增B或N需要相应完整输出
校验依据，[2,1]旧参考不能广播/补齐为[N,B]；低观测逐值配对也不等于独立数值正确性。

**输出轴存在实物容量风险，不能只解锁循环。** 当前固定DLL的Core上限是131072 calls、
131072 records、2048 markers。仅为容量审查有限读取已封存bd377c的block1/G512 capture，
复核该member SHA256 `41d2dd7f3ebbda7828b3dcc7f12a10822490c19fd39ecf4f486a136e317d0d88`：
两token已有83333 callbacks/57558 records/19 markers；按Decode半开phase内ENTRY/start
计数，增量为38874/26958/5。若后续步保持这一增量，输出8约316577 calls/219306 records，
输出32约1249553/866298，均超固定上限；这是**条件化容量估算**，不是目标必然溢出的
证明，后续实现可能改变。原flush不释放这些全会话数组，不能靠多flush宣称容量已够。
本轮不扩collector或重编DLL，输出8/32实现/执行准备停在该明确资源差额，不能无声截断。
临时12GiB及300s/180s也不自动成为长输出资格，须按计划实际保留量和容量另审。

另一项成本来自[`analyze_model`](../../scripts/cupti_timeline_b.py)当前逐token调用
`analyze_files`重复读取/建证据，再保存累计成员结果；输出增长会增加重复前缀及派生量，
旧180秒分析时限不能外推。未来若解除容量门，最小实现应逐run复用已验证的同一Raw对象、
保持每token独立截止点和完整审查，只保存可追溯成员/来源引用；不能截断前缀来省空间。
这是后续方案差额，不是本轮许可扩建collector、换schema或重采的理由。

**本轮完成与停点。** 真实源码核对、独立理论反例、边界CPU等价原型和旧A输入差额夹具
完成；仅新增`tests/test_coe_mechanism_preparation.py`，初次定向16 passed/0 failed/0 skipped，
0.94s为初次结果；继续补固定轨迹等式/历史裁剪及Pilot身份等价后，最终相关命令为
`python -m pytest -q -ra -p no:cacheprovider tests/test_coe_mechanism_preparation.py
--basetemp .local/coe_mechanism_final_20261023 --junitxml .local/coe_mechanism_final_20261023.xml`：
**19 passed / 0 failed / 0 skipped，1.01s**。不是Q0/真实CUDA资格。CPU计时与容量小回执保存在本地
`coe_mechanism_preparation_v0_1`；仅读取一份已审Raw用于新容量问题，未重建S/重算旧响应。
主稿、runner/P、生产S/A/B/COE、registry/DLL、受控/8次配置、Raw及用户DOCX均不变。
下一项本地选择应先审边界候选与低观测模式、或上述A输入合同的明确条款，不自动启动
矩阵、部署包、服务器或GPU；当前未知根因/旧BLOCKED/Gate13限定PASS均保持。

## 14. 逻辑完成约束、COE与A迁移的统一模型（7.245）

2026-10-23，`coe-completion-model/0.1.0`，仅独立离线模型/事后探索。
本节优先于§13的下一步优化安排：先完善完成操作，不启动优化实验或完整CUPTI→A工程。
旧`A_device_wait`、单sync B、签署G12-ROUTEA/0.1.1和原Formal产物不变。

### 14.1 操作成立的证明义务，不是单复制API的阻塞认定

命题是有条件的：固定调用源码/身份正确，且已声明的单FIFO局部依赖闭包与质量证据成立，
才可定义逻辑操作`o=(copy,sync)`。证明链分别为：

1. **程序路径。** 固定2.6.0的[CPU/GPU Copy分支](https://github.com/pytorch/pytorch/blob/v2.6.0/aten/src/ATen/native/cuda/Copy.cu#L341-L377)
   在blocking分支取得当前stream并调用memcpy_and_sync；[helper](https://github.com/pytorch/pytorch/blob/v2.6.0/c10/cuda/CUDAFunctions.h#L70-L90)
   对同一stream先copy、后sync，两次返回均经错误检查。目标2.6.0+cu124头文件的历史
   实字节身份为4027bytes/SHA256 `343d0cd132554849db0825f03834912bb2d82ebd6785908662838452ad0dd84a`，
   复用[已核验来源](completion_operation_candidate_review_v0_1.md#3-语义裁决单api不充分组合完成操作成立于限定范围)；
   本轮回读固定官方版本及封存runner/producer绑定，不冒称重新取得native调用栈或重核目标安装。
2. **实例配对。** 同一run/request/token的结构化helper范围内，唯一成功runtime copy→
   成功runtime stream sync，同PID/TID。实际stream/context通过callback/资源桥和设备效果
   核对，不把native handle和trace ID按数字相等，不按最近时间选对。已审scope/Raw来源
   绑定与闭合范围是必需条件，NVTX自身不是GPU完成证明。
3. **成员。** 沿已审S恢复的提交/效果边和FIFO顺序，W_q截止于sync捕获的提交边界。
   copy入口不是统一截止：操作内提交的D2H仍属成员；已完成先行kernel仍保留。
   逻辑count0节点保留API/顺序证明、没有伪造activity。窗前成功drain关闭历史前缀，
   后提交和无依赖重叠不纳入。无未记录incoming依赖仍是明确支持假设；不称恢复了完整
   token数学数据依赖图或全部自然默认流物理W。
4. **完成。** [CUDA12.4.1 stream sync](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/group__CUDART__STREAM.html)
   成功返回要求该scope先行任务完成，故包括已关联D2H。固定runner随后执行Host读取
   和整数token取得，producer保存实际值，构成Host-readable证据。保证来自组合，不依赖
   [Async copy可能对Host同步](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/api-sync-behavior.html)
   被提升成“单API每个实例都完成/阻塞”的保证。

因此在已审scope内，必要GPU任务是越过该完成操作的前提。它不证明Host从copy入口到
返回之间一直等待GPU；scope缺证则拒绝，而不是以“逻辑操作”跳过S。当前v7.1的
physical-blocking universe要求仍保留；本模型没有据此把每个Memcpy注册为物理sync，
也没有弥补单API内部机制或完整同步覆盖缺口。旧限定冻结处理不被本草案追溯修改。

### 14.2 三项量与terminal的关系

固定`I=[c,r)`，c为copy runtime入口、r为配对成功sync runtime返回；
`U=union(intervals(W_q))`，`Q=μ(I∩U)`，`C=I\U`。分别报告：

- 操作墙钟`T_o=r−c`；COE `Q`；未覆盖`μ(C)=T_o−Q`，三者不能相互改名。
- **保留最后必要活动完成时刻τ**及真实terminal ID。当前FIFO/D2H profile里已有这个
  证据，不新增采集量、顶层A类别或新的“等待指标”。τ能区分最后完成前间隙与完成后
  尾部；仅给COE无法区分这两类时间结构。
- 令`b=max(c,τ)`，合格成员要求τ≤r，则严格有
  `T_o = Q + μ([c,b)\U) + (r−b)`，`Q≤max(0,τ−c)≤T_o`。
  通用区间算术可描述τ<c、Q=0，此时全部I位于terminal后；**这不是当前正字节D2H
  profile的准入正例**。当前操作内实际提交的D2H也必须保留，其非零执行区间若在I内，
  自然要求Q>0；不能为制造合法零值删除它。τ−c不是纯等待，内部空隙也不是硬件空闲；
  r−b不是纯CPU/驱动返回成本。
- 再按原API时间拆`Q=Q_copy+Q_between+Q_sync`，区间互斥。允许API间有Host有用工作，
  不为获得更大Q移动c。程序顺序上是必要完成→sync返回→实际Host token取得→point；
  trace中可核τ≤r≤point。Host TTFT/ITL仍用各自perf_counter时间，不能跨钟相减。

这统一了**完成前提、必要设备执行位置、墙钟分区**三种描述，不统一为净因果延迟。
COE/τ和补集增加都不能单独推出TTFT变差或某项优化可节省相同时间；§13.1反例仍适用。

### 14.3 同一bd377c三点Pilot实物核对

独立新[模型入口](../../analysis/coe_completion_model.py)复用既有completion_overlap与
preview_budget；从原ZIP按manifest/hash读取54份实际消费文件，每run只读/释放一个Raw对象，
核scope、token、保存S输入hash/版本及成员区间；**没有重建S或重新授予准入**。
9run/18链全保留，COE、原sync交集、terminal和补集与原CSV逐项一致。
以下首token为ms，全部第二token与区间来源保存于新版本派生，不与首token充独立重复：

| block / 输入 | 操作墙钟 | COE | 未覆盖 | terminal前未覆盖 | terminal后至sync返回 |
|---|---:|---:|---:|---:|---:|
| 1 / 512 | 5.060900 | 2.403154 | 2.657746 | 2.367382 | 0.290364 |
| 1 / 1024 | 3.397200 | 3.115148 | 0.282052 | 0.256623 | 0.025429 |
| 1 / 2048 | 120.935900 | 79.349730 | 41.586170 | 41.526596 | 0.059574 |
| 2 / 512 | 2.805900 | 2.338357 | 0.467543 | 0.449021 | 0.018522 |
| 2 / 1024 | 159.302500 | 46.853457 | 112.449043 | 112.400304 | 0.048739 |
| 2 / 2048 | 115.610400 | 90.973368 | 24.637032 | 24.545498 | 0.091534 |
| 3 / 512 | 2.183700 | 1.834358 | 0.349342 | 0.295147 | 0.054195 |
| 3 / 1024 | 3.517700 | 3.299398 | 0.218302 | 0.192351 | 0.025951 |
| 3 / 2048 | 86.623200 | 72.420046 | 14.203154 | 14.154595 | 0.048559 |

全部18链`Q_sync=0`、`Q_between=0`、`Q_copy=Q`；不是GPU无执行，而是必要执行已在
配对显式sync进入前完成。2048首token的72.420046～90.973368ms来自操作内必要活动，
不能把86.623200～120.935900ms整个操作都迁移为设备暴露，更不能称纯Host阻塞。

1024高值的112.400304ms发生在terminal前：原结构分解为首个活动前3.682856ms及内部
未覆盖108.717448ms；末尾仅0.048739ms。因此“大补集主要是最后活动完成后才慢返回”
不符合该实例，但空隙的CPU/驱动/资源/观测根因仍UNKNOWN；不能由该分解给出硬件因果。
同布局高低分叉和第二token反向仍约束负载解释：第二token的2048−512为两负一正，
没有从本模型推出统一单调、P0迁移、方法优越或新的Formal规律。

来源仍为[三点完整CSV](cupti_input_pilot_operations_v0_1.csv)、[原件及资格索引](cupti_input_pilot_sources_v0_1.json)、
[位置来源](cupti_input_pilot_positions_v0_1.json)。新派生位于本地`coe_completion_model_v0_1`，
旧文件不改。API墙钟、phase GPU union、同操作GPU union与完整timeline公平保留；本批
同操作union=COE。模型增加可审查的完成scope/成员/位置解释，不宣称Raw中独占新信息。

### 14.4 版本化A扩展只能是同一墙钟的再分区

沿§5已认可迁移规则，令旧A互斥分区为H/C_submit/C_non-submit/E/Z/U0，
`J=union_o(I_o∩U_o)`，`Δ=J\E`；只有原子来源已证明才定义：
`E_completion=E∪J`，`X_new=X\Δ`（X为H/C_submit/C_non-submit/Z），U0保持。
`Δ∩U0`未解决则拒绝对应预览；不将COE另加到A，不把整个copy API搬入E。
每片保留原API/source ID和操作/活动引用，跨操作/旧sync union去重，API父子和
Request=Prefill+Decode守恒。字段必须叫版本化completion exposure，不冒充原Device wait。

新入口的preview只调用已有迁移函数；独立手算含旧E、重复操作、来源和未知拒绝。
**当前CUPTI实例没有合格旧A全窗原子来源，整窗迁移仍NOT_ASSESSED**，不以本模型强行
接回全A，不把API union当A。旧Nsight来源已有[受审预览](completion_operation_budget_preview_review_v0_1.md)
仅保留原事后角色；这次无生产A/B/registry改动，也没有新协议签署或历史资格升级。

本轮只增加本节与独立模型/定向CPU检查，未重跑旧Gate、完整Q0或GPU；GPU暂停、
受控目标验证NOT_RUN、原8P1候选和4096暂停不变。本地验证与保全记录见进度7.245。

## 15. 同源CUPTI原公式A分区与COE迁移接线（7.246）

2026-10-23，`cupti-a-coe-migration-preview/0.1.0`，**事后探索性候选预览**。
本节更新§14.4当时“尚无全窗原子来源”的接线状态，不追改其历史记录。新增
[独立入口](../../analysis/cupti_a_migration.py)只读同一bd377c封存ZIP；原公式A、COE与
扩展预算使用相同run、CUPTI时钟及三个半开窗口。这里的“原A”是**用旧公式新算的
同源候选分区**，不是旧Nsight/Frozen Formal的预算，不拼接或覆盖任何历史A。

来源接线与限制：

- 原A沿用旧分区优先级：合格sync内必要活动→Device wait；sync余段→residual；
  其余已证API→submit/non-submit；剩余request线程路径→Host。后者不是纯CPU执行。
  分类复用原registry及已审API22精确查询政策，不修改冻结registry，不以Get前缀或
  没有activity分类。实际零字节memset保留API预算、逻辑顺序及已审依赖，不伪造activity。
- 每条Raw API必须对应实际callback/root owner，并检查其**真实ActivityAPI区间**包含于
  所选owner的真实API区间；嵌套子API不另加预算。越界、缺owner或未知分类使全窗阻断，
  不扩大owner、不用callback包络补造API时长。保存S的owner/submit来源还须逐项匹配Raw。
- 复用最后token已准入的局部FIFO成员与提交来源，按每条实际成功stream sync捕获的
  提交截止投影此前成员；保留已完成成员、不纳入后提交。每条物理sync、runtime/driver
  父子关联及Host API须双向覆盖，不能凭跨域correlation数字相等或时间邻近选配。
  这不是重建全部S或授予完整物理W/B，仍受closed-prior、单FIFO、无未记录incoming
  依赖的原局部假设限制。当前适配还保守拒绝空必要前缀，以及未纳入本窄域的零字节
  memcpy；不把这种较窄支持范围写成所有完成操作已支持。
- 嵌套driver同步若只有物理/回调区间、没有真实Host API时间，则整个外层owner为不安全
  来源：整窗A返回null及记录级gap；重叠局部预览也拒绝。callback采样边界或物理SYNC
  区间都不能替代所缺Host API边界。未知/unattributed片段不能迁移。

迁移仍严格使用§14.4的`J=union(COE区间)`、`Δ=J\E`、`E_ext=E∪J`；复用既有
preview_budget作实际扣减。原子来源先分区，跨操作/旧wait去重，每片保留原类别、
原API/sync ID、必要activity及操作sync引用。原/新API父预算均等于submit+non-submit；
Request与Prefill+Decode逐类别相等。独立字段`completion_exposure`包括旧wait与新增Δ，
不能直接将COE加到生产`A_device_wait`或把整个copy墙钟迁移。

实际结果：先完成首个G512端到端，再消费9run/18链，27窗口均得到**全窗来源候选预览**。
每run只保留一个Raw对象；54个消费成员核hash，未重建已准入S。完整原/新六个叶预算
（API父类另列）、全部token、signed比较及来源索引见
[机器可读对照](cupti_a_migration_preview_v0_1.json)。以下Prefill单位ms；本批全部窗口
`COE∩旧wait=0`，新增Δ=COE，迁移来源均为submit API，其他类别不变：

| block/输入 | 原Device wait | COE / 新增Δ | 扩展Device Exposure |
|---|---:|---:|---:|
| 1/512 | 0.016635 | 2.403154 | 2.419789 |
| 1/1024 | 0.020608 | 3.115148 | 3.135756 |
| 1/2048 | 0.651326 | 79.349730 | 80.001056 |
| 2/512 | 0.028962 | 2.338357 | 2.367319 |
| 2/1024 | 0.425470 | 46.853457 | 47.278927 |
| 2/2048 | 0.042432 | 90.973368 | 91.015800 |
| 3/512 | 0.016448 | 1.834358 | 1.850806 |
| 3/1024 | 0.596734 | 3.299398 | 3.896132 |
| 3/2048 | 0.026848 | 72.420046 | 72.446894 |

每run有三条窗内物理sync，不能因18条token末尾sync交集都是0，就把其他sync的旧wait
也填0。首run Request的原预算为H131.099500、submit77.316800、non-submit29.574300、
wait0.016635、residual0.333165、unattributed0ms；COE union3.211182ms从submit扣除，
变为74.105618ms，扩展E3.227817ms，总长仍238.340400ms。Prefill与Decode逐项相加吻合。

趋势**不是验收条件**：首token512→2048的新增完成分量ΔCOE为
76.946576/88.635011/70.585688ms，R为70.513613/80.496420/62.326314ms；本批仍三次为正。
整个扩展E的signed差另为77.581267/88.648481/70.596088ms，R另为
71.103774/80.409088/62.262655ms，不把它们与新增分量混同。第二tokenΔCOE仍为
−0.121856/−0.719481/+2.191571ms，全部保留；1024高值未排除。

验收只针对来源/去重/扣减/守恒：定向字面区间、真实文件链和缺证反例；另用Raw及保存
成员清单、独立排序union重核实际区间与来源，不把候选自身输出当唯一答案。没有重新
证明保存S的语义正确性，当前CUPTI来源的目标受控正确性验证仍NOT_RUN。
本次无生产A/B、collector、runner、模型、GPU或协议变更；只授予此封存数据的候选来源
预览状态。旧Formal、Gate13限定PASS、Pilot角色、UNKNOWN/BLOCKED及GPU暂停保持。

## 16. 两输出步的batch参数化接线（7.247，本地实现）

沿§12/§13影响清单，新增`CUPTI-INPUT-PLAN/0.3.0`有限条件声明，条件键包含输入长度
和batch_size（当前仅1/2/4）；对应model/control为0.5.0。旧0.2计划和旧单样本身份仍按原
版本读取，不因新参数合法而取得GPU资格。此处没有批准或生成新矩阵/采集预算。

输入构造仍是同一32-token周期、全1 mask；每个batch内为同一固定输入的有序副本。
`cupti-input-identity/0.2.0`对完整`[B,L]` input_ids、mask、shape及sample_indices分别绑定，
实际tensor使用全部行。新run/slot、P准备缓存、manifest、producer、token scope和报告贯通
该身份；不能用单行摘要或单行token广播替代。输出固定为实际`[2,B]`；Pilot须逐值匹配
预先绑定的矩阵，Engineering观察模式明确没有独立内容正确性参考。

复用原runner及P的prepare/finish/Host读取实现，每步只有一次整批向量的自然Host-readable
完成锚点。整批是一个请求内部invocation；不产生B份独立时延或重复。任一样本EOS、
少输出、错顺序或错token拒绝整次分析，保留真实短输出，不补token、不做动态batch。

独立`cupti_batch_accounting.py`消费同一Raw及两条保存S，复用7.246迁移算法；原公式A、
COE、扩展completion exposure分别写文件，以来源/hash索引接入完整block汇总。不能
跨Raw拼预算、重复加token或单sync B；来源缺口使预算拒绝，不填零。新隔离消费者显式
绑定八项源码，旧四文件来源合同保持。迁移适配0.1.1仅修正已验证runtime→driver父子
同步的覆盖记数：物理记录携带driver correlation时同时覆盖其合法runtime根；一次只计
一个同步，重复物理记录/错parent/未匹配callback仍拒绝。公式、优先级和生产A/B不变，
不重算或替换7.246封存结果。

本地CPU文件链与Host替身不授予batch GPU资格。容量、真实参数/效果、依赖及terminal仍
逐新run判定；collector容量不扩展。GPU恢复后的第一项保持7.241受控正确性验证，
batch实测、8P1、4096继续NOT_RUN/暂停；本轮无部署包或目标执行命令。
