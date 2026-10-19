# 观测准备位置消融 0.1：待审Engineering执行合同

## 2026-10-19八次真实结果审查

**固定8P1、16条token链、两个完整block均完成；本次限定Engineering复核通过。**
执行/分析仍为`9c8b03eae89f5f5e62e647cdeb15b9010ba0b0ee`，不是当前文档HEAD。
未改原A/B、COE或支持域；原receipt仍为`FIXED_EIGHT_COMPLETE_STOP_FOR_REVIEW`，
measurement_validity=NOT_ASSESSED、dropped_records_status=UNKNOWN，未授Formal资格。

回传ZIP57,450,743 bytes，SHA256
`afd428171bbe84e2ab53ea1b32a5f8099e750ca84c4a6b74f3fd8ee0c84d0f0e`，
606成员/605清单、CRC/安全路径及全部hash通过，原A的19成员字节相同。415实际源码、
原launcher/delivery、输入/mask、producer/准备消费与成功窗前drain身份相符。独立读取
SQLite核对成员/API原行与配对同步，重新计算16条区间并集、补集及signed有理数R；
24个原A/候选窗口和14,106个迁移片段守恒，Request=Prefill+Decode。
这是对封存数据的来源/区间/预算复核，未重新运行完整S/analyzer或建立新的W oracle。

本批所有实际输出均为首token 29184、第二token 6556。下表是全部首token结果，单位ms；
比例分母是同run的Prefill trace投影长度，不是Request或累计W。O原现场准备，P窗前准备，
两者都保留研究包装及逐token Host-readable完成政策；都不是无插桩基准或Cpre。

| block | 条件 | Prefill | phase GPU union | COE | COE/Prefill | 候选预算/Prefill |
|---|---|---:|---:|---:|---:|---:|
| 1 | 512O | 173.828240 | 40.347740 | 23.663268 | 13.613017% | 13.708209% |
| 1 | 512P | 79.677931 | 32.018497 | 2.259078 | 2.835262% | 3.636442% |
| 1 | 2048P | 193.352318 | 151.031578 | 99.573788 | 51.498626% | 51.513753% |
| 1 | 2048O | 215.254248 | 165.260886 | 102.704496 | 47.713110% | 47.725256% |
| 2 | 2048O | 188.315682 | 152.918530 | 94.184631 | 50.014226% | 50.027939% |
| 2 | 2048P | 182.615635 | 139.687560 | 89.997308 | 49.282367% | 49.945789% |
| 2 | 512P | 74.765965 | 37.663117 | 1.750317 | 2.341061% | 2.361390% |
| 2 | 512O | 174.300034 | 28.378155 | 16.222008 | 9.306945% | 9.316105% |

“候选预算”是原device wait与COE去重后迁移所得completion exposure；两列不相加。
所有16条末尾配对同步交集均0，但完成操作内COE非0。2048下比例已约48%～51%，
不能因此把它命名为纯Host阻塞、可节省时延或旧Device wait。

预定`R_v=Q2048,v−Q512,v×G2048,v/G512,v`使用同phase活动并集G及整数有理数：

| block/token | R_O ms | R_P ms | R_P−R_O ms |
|---|---:|---:|---:|
| 1/首token | +5.781778 | +88.917694 | +83.135916 |
| 2/首token | +6.770716 | +83.505612 | +76.734895 |
| 1/第二token | +0.136005 | +0.025037 | −0.110968 |
| 2/第二token | −3.773594 | −0.081274 | +3.692320 |

**判读：首token正R在O/P均出现，但强非比例幅度不具包装不敏感证据。**
O的phase活动增长4.096/5.389倍、COE增长4.340/5.806倍，较接近同比例；P分别为
4.717/3.709倍与44.077/51.418倍。主要区别在512参照：O的COE为16～24ms，P为1.75～2.26ms；
2048两种包装均约90～103ms。不能只报告四个正号就宣布强响应已稳健，也不能因幅度不同
否定本批全部结果。第二token两block方向不同，不支持逐token普遍单调规律。

**时序反证与新事实。** 8个P−O的H均下降0.139468～0.651662ms；准备回执P恰好准备/
消费两次，O现场路径未替换。同长度/同block的必要kernel名称、grid/block和动态共享内存
序列均相同，但不等于时长、排队或运行状态相同。512首token的D却下降91.014676/
94.036969ms，故不能用H减少量解释全部差异，或把D差直接当包装效应。

512O的copy为93.312369/95.831608ms，操作中未覆盖69.683762/79.696249ms；其中
69.561224/79.501896ms的后续必要活动所对应提交API，已在空隙开始前返回。P对应
“下一提交已返回”的未覆盖部分仅0.424477/0.298397ms。这些是成员及提交位置的
可复核事实，不足以指定驱动/调度/共同profiler/硬件根因，或证明整个GPU空闲；
它们也不能被填入COE。空隙分类属于本次事后诊断，不冒充预定主要终点。

**公平性与后续范围。** 全16条同操作普通GPU union仍等于COE；完整依赖timeline可恢复
相同成员和解释，没有新的独占数值或方法优越性证据。两个block不提供统计精度、显著性、
等价性或无插桩迁移保证；kernel/token不是独立重复，旧Pilot不并入本批。
当前证据允许继续固定P的输入响应实证候选，同时把O/P保留为敏感性控制。下一建议是另审
256/512/2048三点、3位置平衡block、9P1的有限输入轴，而非重开1024/provider或输出轴；
256真实准入尚未验证，新预算/入口/交付未批准、未制作，也不自动开始下一批。
扩展须回答低侧与端点响应是否复核，不为凑配置或追求较大比例修改语义。

完整16条原值、24个预算、成块比较、逐空隙来源与只读审计代码位于忽略的
`.local/diagnostics/observation_input_result_review_9c8b03_v0_1/`，无新图或完整分析重跑。
旧B命令已执行，不可再次启动；当前用户无需操作服务器。Gate13限定PASS/Gate14 NOT_RUN、
Raw、历史BLOCKED/UNKNOWN及用户DOCX保持，长期总容量仍UNKNOWN，未清理。

> 以下为阶段A审查时的历史记录；B已执行，当前以本节及进度7.212为准。

> 2026-10-19真实A原件审查通过：静态ZIP104,163 bytes，19成员/18清单与全部hash、
> 415项实际源码和6个exit0通过；CPU stdout/JUnit均32通过、零失败/跳过（99.81s）。
> 现仅可由用户显式启动既定8P1 B，绑定新receipt SHA256
> `6e7bf50642ed45f3afc6f4e9ffcff01975aee478b3991303837fd85e890d7803`；不重跑A或换包。
> 当时B仍NOT_RUN，入口仍须fresh核资源、clean及采集身份。审计见本地
> `observation_input_target_a_9c8b03_v0_1`，科研进度7.211同步。

> 2026-10-19协调复核：固定9c8b03e交付包仅阶段A通过审查。CRC/17成员/16清单/
> 415源码表示、bundle及完整输入身份核验通过；新增32项CPU复跑全通过（87.17s，
> 不与原32项相加）。原O/P函数AST未变，默认A不启动模型。目标A/B仍NOT_RUN，
> 新A真实回执审查后才另审B；审计见本地`observation_input_coordination_9c8b03_v0_1`，
> 科研进度7.210同步。本轮未改业务代码或采集定义。

## 当前增量：512/2048 × O/P，执行合同0.2（2026-10-19）

用户批准本地实现与待审交付；目标执行仍NOT_RUN。仅新增有限声明
`OBSERVATION-PREPARATION-ENGINEERING/0.2`，沿用旧pass/execution/token/result
封套0.1，以内含的精确binding/version和profile0.2区分；旧0.1仍只允许32/512。
计划见[固定8槽配置](../../configs/observation_input_sensitivity_v0_1.json)。
block1：512O→512P→2048P→2048O；block2反向。每run新进程，8P1/8profile，
batch1、输出2、warmup3/repeat1。O直接使用原helper，P的prepare/ready函数体不变；
只复用既有有限输入构造并将完整矩阵input/mask摘要接入新manifest与实际输入检查。
两token完整request闭合与原质量门不变，无Decode隔离新例外、无Cpre/新hook。

预定首token主要比较为各包装的R=Q2048−Q512×(phase GPU union2048/512)及R_P−R_O；
用有理数保留signed精确值，分母无效则null/未定义，不加epsilon。第二token全保留，
phase GPU union不是累计W。保存全部原值、H/D、成员/提交/位置、copy墙钟、phase及
operation GPU union；原A和独立候选预算分别保存，迁移仍union去重，不改生产定义。
完整block才比较，不拼旧样本。H下降不是精确包装成本或充分的操纵证明。

两block只筛查：若准备操纵有效、成员/位置合格且O/P均保留正R，削弱“强响应仅为P
特有”解释，不能排除共同profiler/时序影响；O反向或响应消失提示敏感性；混合、操纵
不足或质量失败则不可判别，不追加。任何方向不构成新Formal或论文成功。

预计40～60分钟（含现有后处理，非保证）；每槽现有driver硬超时900秒，固定8槽或
硬失败停止，无重试/替补。新鲜空间门为输出/TEMP/归档卷各12GiB，同卷不重复计算；
历史总量null/UNKNOWN、长期目标50,000,000,000 bytes未证明，不扫旧目录/ACL或清理。
阶段A默认仅固定版本部署、变更CPU检查与空间回执；必须审查真实新A，之后才另行
显式启用B。单ZIP保留原始和小型来源证据，不生成巨型domain。下文0.1及已执行审查
保持历史身份，不能当作本批已执行。

用户2026-10-17批准本地实现、CPU验证及待审打包，未授权本窗口执行服务器。
本合同不签署Formal、不修改A/B、COE、完成政策或旧结果。Gate13限定PASS保持；
新实验NOT_RUN，B2/旧七槽及历史UNKNOWN/BLOCKED保持。机器计划见
[配置](../../configs/observation_preparation_engineering_v0_1.json)。

## 唯一问题与范围

同一自然Host-readable政策下，提前完成不变的观测准备，是否改变输入长度×token位置的
完成结构判断？不是测纯Host阻塞，不要求COE或Device wait变大。固定现有4090/
Qwen2.5-1.5B-Instruct内容、FP16/eager/SDPA、batch1、输出2、warmup3/repeat1。
8个新P1/8条profile，新进程，两个完整四条件block：

|block|固定顺序|
|---|---|
|1|32O → 32P → 512P → 512O|
|2|512O → 512P → 32P → 32O|

首、第二token都须完成证据审查，不以Prefill通过代替第二token。无P0、Cpre、batch2、
hook或引擎；历史样本仅为动机，不并入重复。输入由已封存512输入的32-token循环生成
32/512，逐run绑定完整文件字节hash、实际shape、mask、token值；同长度O/P及block之间
逐值核对输出，不要求不同输入长度产生同样token。

## 唯一干预及身份

- O直接使用原`runner.observe_token_ready_boundary`函数；该函数结构身份保持
  `coe-helper-structure/0.1.0:COE_PILOT_NATURAL`，没有重新实现或故意增加现场工作。
- P只在已有最终drain**之前、暖机之后**，对两个已知token身份调用同一严格构造/校验与
  同一编码函数，生成不可变标签。缓存绑定完整run/request/repeat/pass/token/phase及
  进程/线程；窗口内仍检查归属、索引、一次性消费，错配/复用/过期即拒绝。
- P不提前执行NVTX、CUDA、token读取、时间戳或动态完成记录。`detach→cpu→reshape→
  tolist→Host int tuple→clock→boundary recorder→range_pop`与O同序，不改流和同步。
  P有必要缓存检查成本，不将H差称为净包装开销；标签准备后原drain自然执行。
- 新Engineering角色保留原自然helper的当前Engineering校验分支，**不冒充99f旧Formal
  分支的schema读取成本**，不通过伪造Formal身份或额外读文件复刻旧约3ms间隔。
  本次能筛查匹配的新O/P准备敏感性，不能单独校正或归因旧Formal实例。
- 版本`OBSERVATION-PREPARATION-ENGINEERING/0.1`，独立pass/token/execution/result
  schema；manifest、producer、collector显式开关、receipt、Canonical、报告和8槽身份
  同源绑定。runner实际字节与P模块实际字节分别核验；P模块源码副本随run保存。
  不沿用旧seal。旧入口没有这项新版本授权，旧报告不改写。

## 准入、参照和固定计算

复用既有隔离预检、目标解释器/site、模型内容、mask/UUID/PCI、token、drain、边界与
官方同类诊断处置。Canonical只生成一次；复用完整request闭合FIFO的S/A检查，取得
三窗口原A，再审两个COE操作。无新的Decode豁免或零字节例外；未知依赖、缺映射、
失败同步、身份冲突及任一token不闭合均硬停，保存具体原拒绝。完整request作为此
batch1两token路线的保守准入证据，不授新科学资格或完整物理W/B。

COE规则仍为copy入口→配对成功stream sync返回，必要成员截止该sync捕获提交边界，
保留已完成前缀和操作内D2H，不凭时间重叠选依赖。两模式检查、terminal/成员记录与
全部coverage保留；未知不填零。不生成巨型`domain.json`，不重写生产A。

所有位置在同一trace时钟：L为copy前最后必要submit API返回，C为copy入口，K为该
操作最后必要kernel完成；H=C−L，D=K−L。保留L/C/K、D2H terminal、sync返回、Host
token的trace point、所有成员与submit记录。H不是精确包装耗时，D包含执行/排队/空隙；
不得跨Host clock相减或把K−C当纯阻塞。kernel时长与分支不要求逐值相等。

每个block、token预定比较：各长度P−O，各variant的512−32，以及二者差的差。
全部signed值、负差与零值保留。共同输出COE绝对值/组成/补集、copy/sync墙钟、原sync
交集、同操作普通GPU union、phase原A和同窗API/count/sum/union/mapping/GPU baseline。
完整依赖timeline可给同样解释，不将自动化或数值增大称新信息。

## 预定判读与停止

1. CPU文件链证明两组标签等价，O每token现场构造/编码一次，P现场零次、窗前各一次；
   目标机仍需实际输出身份、源码、缓存消费、完整NVTX范围及copy/sync链复核。
2. 八run及两个block质量闭合后才形成比较；不拼接不完整block。H均下降只输出
   `CONSISTENT_H_DECREASE_SCREEN_ONLY`，仍须联合D、成员、提交/分支与两token结果审查。
   不能自动宣称因果或原Formal污染得到定量恢复。
3. 若准备未生效、H未有效改变、D/执行结构同时改变不能区分，或方向混合，则
   `INCONCLUSIVE_OR_MIXED`。不设置事后ms阈值，不强迫kernel相同，不追加采集。
4. 即使H下降且响应改变，也只支持本栈的观测准备敏感性；若响应保留，只削弱这个
   具体竞争解释，不排除所有Host/profiler作用，不自动建立论文贡献或负载普遍规律。
5. 两个block无稳定性、10/5ms精度、显著性或P0收益保证。质量硬失败或8槽完成即停；
   不重试、不替补、不自动续采/改输入。模型采集沿用120s profile限制，每槽外层900s；
   超时/未知后代保留现场，原封包guard拒绝时不强制打包或删除marker。

## 本地证据及目标机边界

独立CPU预期：两token各有两个kernel与一个D2H；kernel已在copy前完成，D2H在copy内
提交且sync前完成，COE各2ns、原sync交集0。真实producer文件→Canonical→两token
准入→COE→结果消费已覆盖，并保留缺drain、错流、未知依赖、前/后phase缺提交效果、
缺token范围、身份/标签/文件hash冲突反例；另验证有符号成块比较与立即停止。
实际PowerShell5.1分支/文件/空间回执/封包检查使用明确Git、pytest与collector进程替身，
不是目标部署或GPU验证。实际版本和最终命令/结果见同次进度7.184及交付说明。

预计8P1约25～45分钟，仅据既有小批次作预算估计，不是完成时间保证；按新批次
Raw+SQLite+Canonical+小型来源估计最终新增/保留1～3GiB，临时各参与卷12GiB空闲。
同卷不累计，多卷分别核验；不安装环境、不遍历历史YLQ/ACL、不自动清理。
长期目标严格小于50,000,000,000字节，历史总量仍null/UNKNOWN，不能称已达标。
审查、完整归档核验之后才能另行精确清理可恢复副本，本轮不清理。

待审ZIP以最后可信回执63ca051为前置，精确commit及大小/hash在忽略的交付说明中。
A默认仅部署/相关CPU/空间检查；B须A回执经审查后凭其真实SHA显式启动。旧静态包不解锁。
服务器当前checkout/剩余空间和真实CUDA适用性均须目标回执确认，不猜测已通过。
