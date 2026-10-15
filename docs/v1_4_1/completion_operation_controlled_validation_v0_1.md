# 完成操作候选：封存四token增量验证 0.1

`COMPLETION-OPERATION-CONTROLLED-VALIDATION/0.1`；2026-10-15。
原件角色Engineering；新结果为操作层兼容性/增量验证，不是新Formal或全Q0，不修改生产A/B。
依据用户对[候选对象0.1](completion_operation_candidate_review_v0_1.md)的单独认可；
认可组合完成对象，不认可单复制API独立同步保证或纯Host阻塞解释。

## 1. 读取实测区间前锁定的独立预期

源于封存`NULL-FIFO-D2H/0.1.0`的prepared/prompt、固定runner与native源，不调用候选脚本
的集合恢复，不从analyzer输出生成答案。配对以完整request/repeat身份和操作ordinal选择，
不按时间最近或交集大小选择。下面先固定逻辑ID，随后才绑定Raw rowid与实际区间。

| request/repeat | token实值 | copy→sync操作ordinal | 预定本地必要后缀 | terminal |
|---|---:|---|---|---|
| controlled-0 / 0 | 11 | 2→3 | K1(0), C1(2) | C1 |
| controlled-0 / 0 | 12 | 7→8 | K1(0), C1(2), K2(6), C2(7) | C2 |
| controlled-1 / 1 | 21 | 2→3 | K1(0), C1(2) | C1 |
| controlled-1 / 1 | 22 | 7→8 | K1(0), C1(2), K2(6), C2(7) | C2 |

每request先成功device drain，再request点；K1后另有ordinal1内部stream sync。
该内部sync不是token0的配对同步，不能误选或删掉K1；token1也不能只保留K2/C2。
warmup K0/C0及前request活动作为已完成历史前缀单列，不伪装成新request成员；
其对本次候选区间的投影须独立确认为零。copy/sync之后的下一token、下一request或
cleanup工作不得加入。无关流仅因时间重叠不能加入；已有反例复用，不扩大本构造支持域。

固定I=[copy runtime.start, paired sync runtime.end)，原sync交集采用该sync的runtime包络。
**集合截止是配对sync捕获的提交边界，不是copy入口**；copy在I开始之后提交的D2H必须纳入。
源计划里的K/C集合独立给定，Raw只负责验证实例及填充时间，不能由交集反向筛选成员。
terminal为相应D2H，须验证同scope顺序及完成后成功返回，不能仅靠最大结束时间挑选。
四链允许交集小或零，不以“比旧值大”判成功。

## 2. 预先声明的验证层次与适用边界

1. **操作身份/完成保证**：原计划、源/DLL、producer身份与token；对应NVTX操作范围内
   唯一成功copy/sync，correlation唯一对应D2H/物理stream sync，同PID/TID/device/context/流。
2. **成员**：按上表人工集合核对全部实际提交/活动，保留早完成成员；检查历史前缀闭合、
   后提交排除及terminal。不执行候选集合恢复或生产S/A/B。
3. **区间算术**：用预定成员的原始区间独立手算裁剪；先验证该受控单FIFO活动互不重叠，
   再逐项相加，与既有候选区间函数比较。独立参考不调用该函数生成期望。

重要差异：封存native源码用`cudaMallocHost`，本构造是**4字节Device→Pinned**；
自然PyTorch实例是8字节Device→Pageable。两者整体保证都来自随后成功同步，
但不能因此把Pinned受控结果当成Pageable自然helper的精确执行子域资格。
本轮只能裁决操作层对象/成员/算术依据及是否可进入合同设计，不授后者资格。

以上在本轮实际SQLite区间查询前写定。原件已在历史审查中分析过，不声称盲法或新预注册。

## 3. 输入绑定与实际验证

复用[原drain离线审查](gate8_drain_api_reanalysis_v0_1.md)和
[原限定资格](gate8_bounded_qualification_review_v0_1.md)，不重跑旧oracle、完整Q0、
Canonical/S/A/B。原attempt继续BLOCKED，历史资格和原输出不覆盖。

- 原封包：`qualification_20260927T143910Z_4b9c1fd9128d4badb1f451843fd51aea.zip`，
  SHA256 `42c40987ae982e9887a5fb2dde0785759d6421ba52efcdae476ee9cb4c3703a5`；
  此前已核验CRC和完整清单。本轮仅复核实际消费的12项源文件hash及关联，不重复全包扫描。
- SQLite SHA256 `9894e76f395d6f44bd10f83742d4340278f9235ed0903cf4589befd37ff124fd`；
  以`mode=ro&immutable=1`读取。执行commit `8ef1385604c7d35d8ac15efbe76aa9d3a26ba9a2`；
  原计划/native源/DLL/producer身份/token、执行COMPLETE及原计划引用均相符。
- 固定native源码SHA `0b226e6b7b1116afa145f2c35e55fcadf7c8d93e364b8922e2afb1692f1ffe65`；
  DLL SHA `c2d8fef4a3c892e557c4d16154c5bae790632aee3de047f003a62cef8d99dc20`。
  封存代码确用`cudaMallocHost`，SQLite本文件枚举也解为Device→Pinned、4字节。
- PID61132、TID65060、device0/context1/trace stream7；对应原资格的NULL FIFO。
  每个操作的完整identity、ordinal、类型和范围唯一，成功runtime与physical sync按
  correlation映射；不是用PID/stream编号直接替代跨层身份。
- 目标作用域全部10条设备活动：warmup的K0/C0、两request各K1/C1/K2/C2。
  第一个request保留2条已完成历史前缀，第二个保留6条；成功drain和原始ID明确关联。
  每次实际捕获的完整**已观测FIFO前缀**与“这份历史清单＋人工本地后缀”逐ID一致。
  不把观察到的闭合集合升级为全capture无损认证，也不额外授予通用物理B资格。
- 当次sync的必要成员提交均完成于该sync入口之前；相应D2H在copy入口之后才提交，
  所以其属于正确集合，却不属于“以copy入口为截止”的错误集合。后token/后request
  的submit被排除。内部ordinal1同步与token-ready ordinal3/8严格分开。

本轮独立审计器在忽略的
`.local/diagnostics/completion_operation_controlled_v0_1/verify_controlled.py`，
只从人工ordinal表取成员；**未导入或调用候选脚本的`recover_suffix`**。
参考答案是已证互不重叠的至多4个原始区间逐项裁剪求和，再与既有`completion_overlap`
算术函数比较。后者只作被验证的区间运算，不生成独立expected。

## 4. 四token实值、来源和分层结果

时间均为同一`NSYS_TRACE_RELATIVE_NS`。为便于阅读，下表用µs；JSON保留整数ns，
无时钟平移或Host/trace钟拟合。这里“原sync”是**该配对同步**，不是整个phase的Device wait。

| request/token | 预定成员的Raw rowid | copy→sync runtime / corr；physical sync | 原sync交集 | 候选交集 | I墙钟 | I补集 |
|---|---|---|---:|---:|---:|---:|
| controlled-0 / 11 | K2,C2 | 13→14 / 133→134；S4 | 0.448 | 0.448 | 56.634 | 56.186 |
| controlled-0 / 12 | K2,C2,K3,C3 | 16→17 / 136→137；S5 | 24.032 | 24.032 | 223.673 | 199.641 |
| controlled-1 / 21 | K4,C4 | 21→22 / 143→144；S8 | 0.480 | 0.480 | 56.394 | 55.914 |
| controlled-1 / 22 | K4,C4,K5,C5 | 24→25 / 146→147；S9 | 1.376 | 1.376 | 66.860 | 65.484 |

K/C分别是`CUPTI_ACTIVITY_KIND_KERNEL`/`MEMCPY`的rowid，S为物理同步表rowid，
不是construction的逻辑K1/C1编号。四次terminal分别为MEMCPY row2/3/4/5。
操作NVTX row分别为copy/sync的12/13、16/17、23/24、27/28；实际Host read值为11/12/21/22。

| 验证层 | 独立依据和实际检查 | 结果 |
|---|---|---|
| 身份/整体完成保证 | 固定construction操作计划、成功copy与成功同流sync、Raw映射、实际Host read | 四链相符；不证明copy单独返回完成 |
| 成员与terminal | 预定2/4个本地成员＋闭合历史前缀，与捕获边界实际逐ID核对；terminal预设D2H | 四链相符；无依靠重叠挑成员 |
| 区间运算 | 预定成员的非重叠区间逐项手算，与候选区间函数比较 | 四链逐值一致；不以交集增大为准 |

例如token12：K3区间`[3585686078,3585709662)`为23584ns，C3区间
`[3585720094,3585720542)`为448ns；原K2/C2均已完成仍保留为成员，当前交集为0。
I=`[3585516911,3585740584)`，配对sync=`[3585535819,3585740584)`；
故两种交集都是23584+448=**24032ns**，I补集223673−24032=**199641ns**。
这里K3在copy之前提交、在sync期间执行；C3是在copy入口之后提交，同样必要。

token11则因先有内部sync，K2早于copy入口完成但仍留在集合，I内只剩448ns D2H。
其copy API为`[3584712170,3584720182)`，D2H为`[3584765606,3584766054)`，
配对sync为`[3584730757,3584768804)`：**copy已返回后D2H才开始**，但整体在成功sync
返回前完成。它是Pinned受控分支中“不能用copy返回替代整体完成”的真实例子，
不能反推Pageable分支也必须如此。
四链扩大包络后交集均未增加，不把此结果判作失败、不移动起点或修改选择规则。
补集含活动间隙与未分离的Host/库/观测成本，**不归因给CPU、驱动、return tail或纯等待**。

本轮输入12项在查询后hash均未变。新产物位于独立忽略目录
`.local/diagnostics/completion_operation_controlled_v0_1/derived_v0_1/`：
`controlled_validation.json` SHA256
`ca2784fec4f1d4d98746ceb30ed68eb8037f10b4a37a7506b94d736335ad8aec`，
同名CSV SHA256 `2798a81697985c67bacd43d280fdde92c0f5a33f21df7cb16df58708ee7e4022`。
审计器SHA256 `3ff608f5a4d3070802505309772b66c8d01735551ac2b65d047da89d2d63b767`，
其中记录了全部来源hash、原始区间、前缀/后提交清单和分层结果。
未新增或重跑31项CPU反例；复用[上一轮独立反例及绑定](completion_operation_candidate_review_v0_1.md#2-先验独立手算反例单位ns区间半开)。

## 5. Host工作：对象失效与解释限制不能混用

受控native的`ep_copy()`与`ep_wait()`之间存在Python/NVTX收尾和下一标签构造。
四次API间隙分别10.575、11.698、12.118、13.951µs；未测其内部CPU忙闲，不将全部间隙
称等待。它们不使预定配对、固定边界或同流completion语义自动失效。

| 情况 | 对操作/依赖的影响 | 允许的解释 |
|---|---|---|
| 固定操作内Host计算/标记与必要GPU工作重叠，但身份、配对、提交scope保持可核验 | 不自动使组合对象无效 | 仍可报告该固定操作期间的必要活动交集；不能称纯Host阻塞 |
| 没有间隙，或间隙很短 | 不增加语义保证 | 仍不能由时长推出Host无有用工作/纯阻塞 |
| 插入新请求、覆盖token缓冲、多个无法区分copy/sync或scope/相关性冲突 | 使配对或必要集合不可靠 | 拒绝对应操作，不能靠扩大I补救 |
| 新流/event/incoming工作尚无法证明、前缀未闭合、失败sync/错误token | 缺少依赖/完成保证 | 保持拒绝或未知，不按几何重叠赋予completion |
| 源策略明确仅限某helper，实际换成有额外Host处理的不同执行策略 | 对象未必无效，但可能超出该profile | 如实标profile不适用，不能悄悄挪动边界；是否新增profile属于合同设计 |

**澄清上一版草案“唯一连续”的含义**：不得把它解释成“必须排除一切Host工作，否则对象无效”。
应要求可核验的固定配对和scope；`operation validity`、`profile applicability`和
`pure-wait interpretation`分开。若保留strict-helper子域，就将Host路径限制明确写入
profile，而不是把纯阻塞尚不可识别误写为依赖错误。当前不改冻结合同或生产准入。

## 6. 未来接入A的预算迁移设计（未实施、未批准A改版）

先保留候选为独立overlay是最少语义变化的路径。若未来获准进入互斥A，必须新版本明确
更广的**completion-operation exposure**，不能继续把扩大后的量无说明地叫旧物理sync wait。
本轮认可候选对象不等于批准此A语义变化。

对同一request/phase窗口R，令原A互斥集合为H、C、E、Z、U（Host、API、原sync交集、
sync residual、unattributed）。每个已准入操作的候选集合为
`Q_o = R ∩ I_o ∩ union(必要活动区间)`；先令`Q=union_o Q_o`，再取`Δ=Q\E`。

- 建议迁移规则为`E'=E∪Q`，H/C/Z仅移除各自与Δ相交的**同一原子墙钟片段**；
  U不因候选计算而消失，`Δ∩U`必须先独立解决原缺证据，否则该片段不得迁移。
- 原sync交集已在E中，不能再加；重叠/嵌套操作的Q先union，kernel/MemOp重叠同样union，
  若拆子类则kernel-only/MemOp-only/mixed互斥，不能双计。
- 改动是预算重新分配，`T_R`不变。Raw API count/sum/union及同窗baseline不改；
  API原墙钟与迁移后A_API可不同，二者不能再相加。保留逐片段原类别/目标类别及来源。
  C的submit/non-submit子类也须同步移除相同片段，父子守恒保持；不把现有opaque
  allocation成本自动纳入这个只覆盖copy/sync的候选。
- 若Δ覆盖有用Host工作，迁移不意味着该CPU工作消失或变成等待；新A的解释将发生实质
  改变，必须在新合同明确。不愿承担该解释变化时继续仅发布overlay，不能暗中裁Q。
- 单sync B仍仅解释原物理同步及其W/terminal，不为组合操作制造physical barrier或假B，
  也不跨sync累加B。历史A/B和Formal永不按新规则回写。

独立手算迁移例：R=[0,20)，原H=10、C=6、E=2、Z=2、U=0；
C=[4,10)，E=[10,12)，Z=[12,14)。候选Q=[5,8)∪[10,12)，长5，
Δ=[5,8)从API移走3；新预算H10/C3/E5/Z2/U0，总和仍20。
直接把E2与Q5相加会多计2。**本次四个真实token全部Q等于原配对sync交集，增量Δ为0**；
不能把token12的24.032µs加两遍写成48.064µs。

## 7. 本轮唯一裁决与停点

**裁决：组合完成操作在声明的操作层范围内有足够独立验证依据，可以进入版本化合同设计。**
依据是独立固定的配对/2与4成员/terminal、真实成功完成与token、逐record核对和独立算术，
不是扩大窗口得到了更大数字。设计时必须显式区分：

- **本次已验证**：NULL-FIFO-D2H受控Device→Pinned/4-byte的操作身份、完成保证、必要成员、
  历史闭合及候选区间算术；保留原Engineering角色。
- **不可由它直接授予**：上一版草案所写自然PyTorch Device→Pageable/8-byte完整执行子域资格。
  该子域目前只有上一轮24链探索证据；内存类型和native/Python调用路径差异不可抹掉。
  本轮结构验证与自然执行子域准入是两件事。**整体保证来自尾部成功sync，不依赖将copy
  判为阻塞；Pinned/Pageable差异本身不构成新采或重跑Q0的理由。** 下一阶段先在合同中
  将本次结构依据与既有24链/原G1资格对应，不预设还须追加目标机证据。
- **始终未证明**：单个Async复制的独立同步保证、纯Host阻塞/可消除时延、自然阻塞测准、
  普遍负载规律或论文贡献；没有新Formal、全Q0、D/Signature或Gate变化。

当前停止在“可进入合同设计”，不实施新A，不制作采集包/服务器命令，也不把历史失败或
UNKNOWN/NOT_ASSESSED改成通过/零。研究设计DOCX和原Raw/报告均保留。
