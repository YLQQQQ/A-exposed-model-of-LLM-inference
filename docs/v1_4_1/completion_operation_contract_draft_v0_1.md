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
