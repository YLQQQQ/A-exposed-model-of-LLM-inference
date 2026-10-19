# 观测准备位置消融 0.1：待审Engineering执行合同

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
