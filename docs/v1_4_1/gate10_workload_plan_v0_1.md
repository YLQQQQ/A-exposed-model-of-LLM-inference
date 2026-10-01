# Gate10 最小 workload 可行性准备 0.1

版本：G10-WORKLOAD-FEASIBILITY/0.1。Engineering；[7.102退出裁决及7.111范围澄清](gate10_closeout_v0_1.md)：Gate10仅选定G1三点一次可行性PASS；容量/OOM/最大长度/batch未探索，512和2不是上限，不外推未测配置。稳定编号下未执行子项见[进度](research_progress.md)。
下述Gate10准备/待执行语句保留为历史，两个新点均已完成，不再执行旧交付。7.111直接在本计划末尾补充[Gate11本地准备](#gate11-local-preparation)，不另建重复计划。**7.116现行：两批Pilot复用完成补证前[政策/预算决策](gate11_policy_decision_v0_1.md)，Gate11 BLOCKED，60预算耗尽；仅待额外30进程/15profile预算审查，不实现/打包/执行。** 以下组序/预算保留，待执行措辞属于当时准备状态。
依据：当前研究设计v7.1 §2.1、Pre-Pilot实验协议v2.1 §2.1候选池、用户批准的单平台路线及[Gate9分域资格](gate9_closeout_v0_1.md)。不修改冻结S/A/B公式，不是Pilot或Freeze。

## 候选与执行边界

| 点 | 处理 | 比较问题与信息用途 |
|---|---|---|
| 输入32/输出2/batch1 | 复用Gate8封存配对和1733ff3分类审查，不重跑 | 最短已有完整prefill/decode执行基线；不是当前提交的重新验证 |
| 输入128/输出2/batch1 | 首个新点，一次profile | 输入增至4倍时，同一eager/SDPA执行及G1投影支持域能否成立，为后续输入轴比较提供可行点 |
| 输入512/输出2/batch1 | 仅128成功后执行一次profile | 再增至4倍，检查中等输入的资源及必要依赖证据；不预设API/kernel工作是否按比例转为A |

128/512来自协议候选池；输出2沿用已批准Engineering基线，不冒充W01/W04的16输出token点。没有根据既有A比例选点，也不将unattributed=0或趋势符合预期作为通过条件。2048/4096、第二模型/平台、compile/graph、G2本轮不做。

固定Qwen2.5-1.5B-Instruct内容快照、batch1、fp16、greedy、eager、SDPA/use_cache、原GPU及隔离解释器；自然G1不增加人工同步。模型加载、一次同输入warmup及成功drain在request窗外，测量一次request（repeat1）。输出2覆盖prefill首token与decode一个token。
仅Pass1逐request支持域/资源可行性，不另跑Pass0、不估计新点overhead；已有32/2配对仅是单次工程观察。未来latency比较仍需同合同Pass0，不用profile时间当自然性能。

## 输入和有效性

使用已封存prompt文件（SHA256 `4dffd0ddcbd3185c656ae4a27efaf5aab302febba6ead5df4d37d903a2091920`）sample0的32个token，按原顺序循环4/16次；无tokenizer在线操作、无chat template、无截断/补齐。新文件保留tokenizer/special-token元数据，batch只取一个样本，attention_mask全1，显式记录构造及源文件hash。文件SHA256在prepare之前生成并写入候选清单与manifest。
必须逐token检查整数、vocab范围、非special token、长度/全1 mask及模型config最大位置长度；模型内容必须匹配已封存inventory，revision仍UNKNOWN/content-addressed，不冒称revision已知。
实际runner输入由经过hash校验的同一prompt构造；输出数来自producer实际读取token计数，early EOS/不足2即不可接受，不禁用EOS、不替换prompt、不自动重试。合成token只服务本批Engineering，不授予语言质量/真实语料代表性。

## 必要实现与验证计划

采用writing-plans与tests-first；在当前根目录直接执行，不新建worktree或委派。

- [x] 新增 `exposedpath/gate10_workload.py`：固定有限点/构造/声明/输入检查，拒绝未知版本、错长度、无效token；对应 `tests/test_gate10_workload.py` 先红后绿。
- [x] 最小对齐 `gate8_diagnostic.py` prepare及target入口：仅显式Gate10声明允许128/512，旧32路径原样；manifest在执行前声明G1分域，实际文件producer测试验证非32不会静默回退。runner在完成窗后回调读取既有shape/count事实，单独写 `gate10-workload-observed/0.1`，绑定manifest/producer hash与request身份；不修改封闭pass identity schema或引入同步。
- [x] 将已接受官方warning review接入G1 domain；原诊断和UNKNOWN保留，新型/目标warning拒绝。以真实fixture文件链验证正反例；collector只在显式domain声明时调用domain，不绕过任何边界/成员/依赖检查。
- [x] 新增有限batch编排/服务器脚本，逐点停止，保留失败/未执行点；打包同一ZIP。CPU测试验证清单、顺序、停止、未知分类及实际接线；仅相关回归/语法检查。

7.100历史：N1 V0/Vmarker/Vsync模型矩阵当时尚未实现；7.110已独立完成[32/2三组一次Engineering可行性](n1_model_feasibility_closeout_v0_1.md)，不是OOM或统计稳定性证据。G1每request重新验证身份、三窗口、窗前drain、内部sync、必要成员/依赖边和支持域；长度变化本身不触发新Q0。

## 7.101执行调整

128/2在76ef717已采集，原driver离线分析900秒超时。经[不变Raw续算审查](gate10_timeout_review_v0_1.md)，性能修复后128/2一次可行性通过；仅512/2未运行。下一交付使用`--remaining-512-only`新目录单点，不重新调用原两点批次、不恢复旧输出；其余合同和超时上限不变。原失败及UNKNOWN后代记录不改。

## 停止与结果

顺序128→512；任何失败停止余下点并记NOT_RUN，禁止重试/恢复/覆盖/临场改参数/扩大搜索。collection沿用120秒工具上限、300秒外层上限；单次export，无自动retry。超时可能有存活后代时停止打包，先由协调窗口处置写入者，不杀进程名、不重试。

区分事实与裁决：明确CUDA OOM异常才记RESOURCE_INFEASIBLE；超时记TIMEOUT_UNRESOLVED，不推测OOM；身份/配置/输入冲突为EXECUTION_CONTRACT_FAILURE；缺表/边界/依赖/超支持域/未知诊断/分析失败为EVIDENCE_OR_ANALYSIS_FAILURE；其他异常保留UNCLASSIFIED_FAILURE及原文。低unknown不是warning安全证据，known局部unattributed按合同保留。
单点成功要求实际2token、非EOS、完整producer/entry/preflight/REP/SQLite、G1 domain逐request质量通过；仅记FEASIBLE_ONCE_NOT_STABILITY。有界失败不是方法科学否定，也不是把该点从Formal中静默删除。

回传后才审查EP-G10-02/03；不以两次单次成功确定repeat数、overhead阈值、统计显著性或“稳定范围”。Pilot/Freeze另行准备。Gate7/8/9历史限定PASS保持。

## 本地验证及交付（7.100）

先红后绿已复现候选模块缺失、非32目标文件入口、实际shape未持久化、G1同类warning未接线、collector未dispatch domain、失败未分类等问题。相关7文件CPU回归119 passed；最终新增/收口定向22 passed（与119有重叠，不相加当独立测试数）。compileall及PowerShell语法解析、diff-check通过；不是目标机或CUDA验证。既有未知warning、missing correlation/drain/ownership及模式成员不等价负例保持，新增同类warning与correlation缺口共存仍拒绝。

执行入口 `scripts/run_gate10_once.ps1`，编排 `scripts/gate10_feasibility.py`；机器本地delivery固定commit/prerequisite、源码/输入hash、模型inventory与路径，随单包交协调窗口审查。以服务器15b24ec为前置，部署后只跑相关CPU测试，再顺序两点；无需重新编译native、跑旧probe/完整Q0/全量测试。prepare会初始化CUDA做设备身份查询，不能称整段CPU-only。
单次collection仍120秒工具限制/300秒外层限制，包含analysis的point子进程900秒上限；超时不自动延长。所有原始exit/stdout/stderr、entry异常记录、输入/manifest/preflight、producer/drain/stage、REP/SQLite/export、domain/diagnostics和batch机器报告统一单ZIP。任何中断只保留已产生证据，未执行点不得补成失败或成功。
本批只能确认G1两点一次可行性；不能据此宣布N1同点模型执行或完整N1/G1共同可行域已验证。N1模型功能准备与以后Pilot仍分开。

<a id="gate11-local-preparation"></a>
## Gate11 本地准备（G11-PILOT-PREP/0.1；7.116补证前政策停点）

2026-09-30；这是既有EP-G11-01～04的最小具体化，不是新资格层、采集授权或Protocol Freeze。
依据研究设计v7.1 §2.3.9/3.2、Pre-Pilot协议v2.1 §1.2/1.4/4.2–4.4/6.2，结合已批准单平台分域路线。
现有Engineering只提供执行可行性、身份/语义适用依据和粗略资源预算；新Pilot需新run/角色，不能把旧值计入重复样本。
不沿用旧`docs/small_pilot.md`的v3四点、warmup5/repeat5或任意CV/coverage阈值。

7.116：已执行两批证据复用，当前只读[政策/预算决策0.1](gate11_policy_decision_v0_1.md)。共同w3、三个原组序block、相邻P0/P1的额外30进程/15profile为唯一补证提案；约70～90min/35GB，追加预算未批准，未实现/打包/执行。提出解释尺度候选和n=3/6/12成本比较，n6不是充分性结论；预先保留负差/所有有效样本、block不确定性及预算不足claim收缩，不要求波动归零或干预有效。原60已耗尽，Gate11仍BLOCKED；以下原组序/解释/预算是历史依据，不自动再用剩余预算。

7.112历史：用户已批准未来新采限定Pilot适用性，[G11-LIMITED-PILOT/0.1](gate11_pilot_contract_v0_1.md)与最小本地角色/配对/首批编排已实现。只实现前三block，未实现/授权剩余30进程或warmup扩展；当时Gate11 NOT_RUN。

### 代表点、问题和复用边界（EP-G11-01）

| 条件 | 固定点 | Pilot需要回答的问题 |
|---|---|---|
| G32、G512 | G1自然32/2、512/2，batch1 | 输入轴两端的latency/投影A及常规API/kernel/sync描述是否可稳定测量；能否估计噪声和profile扰动，而非预选非比例趋势 |
| N0、Nm、N16 | N1显式流32/2的V0/Vmarker/V16 | 包装/marker成本与同步干预能否区分；A和合格单sync B、raw sync与E2E对照所需精度及成本，不以出现显著效果为成功条件 |

这五个条件按比较问题选取，不按已知A占比、unknown或干预效果选择。128/2保留Engineering证据，不在首批重复；两端不能证明中间单调或完整输入响应。
模型内容快照、固定prompt及循环构造/digest、fp16/greedy/eager/SDPA/cache、单GPU和32/2的三组公共合同沿用。
G1不引入N1流或干预；N1层16位置、每个decode一次、各组相同专用流及配置不变。只含一个decode step，不能代表长decode。
旧证据复用范围见[Gate10收尾](gate10_closeout_v0_1.md)、[N1收尾](n1_model_feasibility_closeout_v0_1.md)与[Gate9资格](gate9_closeout_v0_1.md)；不重跑完整Q0，不补测容量极限。

### 最小配对、组序与warmup评估（EP-G11-02草案）

记录单位为独立进程的一次measured request/phase；进程独立不等于统计独立，配对/三组对比按共同block保留相关性。先保持每进程repeat1，外层block承载重复，不新增长驻多request状态。
每个条件每block有一组相邻Pass0/Pass1：完全相同输入、variant、warmup1、completion/流政策和输出token；分别绑定run/pass/request/nonce/PID，不能共用一个PID或把旧V0当新Pilot基线。
Pass0保留N1预定marker/同步，关闭仅用于trace的观测插桩；Pass1沿用已获资格观测方式。公共合同与允许的观测差异须机器列明，不能声称两pass指令流字节完全相同。
host-readable host时钟边界用于两pass latency对照；Pass1 trace共同锚点用于A，两个时钟不直接相减。

首批3个完整block的条件顺序：

- b1：G32 → N0 → Nm → N16 → G512。
- b2：G512 → Nm → N16 → N0 → G32。
- b3：G32 → N16 → N0 → Nm → G512。

若经首批审查仍需更好的噪声/精度估计，最多续b4～b6，分别反转b1～b3；不因差值符号、显著性或图是否好看而追加。
条件在block中位置为j（从1开始）：b+j为偶数时P0→P1，奇数时P1→P0；六block可平衡次序，首批三block不声称完全平衡。
N1三组均独立新进程，同block内比较；不得跨域把自然G1当显式流V0。实际执行顺序持久化，不按文件名排序恢复。

warmup1只是Engineering起点，未证明充分。首批复用实际stage ledger的warmup开始/结束/成功记录，结合measured request随block、顺序及allocation的变化筛查热态/漂移；这些只能提示问题，不能证明warmup1充分。
现有warmup的`actual_output_tokens`是成功后赋目标值，不能当成逐token/EOS实测；测量request仍须读取实际tokens。加载、warmup、成功drain在窗外，不增加CUDA同步来计时。
N1保留独立held warmup流与fresh measured流；即使模型已热，measured流仍可能发生首次allocation，不能将其移出request或按“冷启动异常”事后删除。
若首批不足以选定warmup政策，优先把剩余预算用于**五条件各3个P0-warmup1/3相邻对照，共30进程、无新Nsight**；条件顺序复用b1～b3，warmup对照顺序按b+j偶数为1→3、奇数为3→1，其他合同不变。不能把不同warmup混成一个repeat总体或把warmup3当P1-warmup1的配对。
该对照与b4～b6扩重复二选一，不两项叠加；按热态/精度问题决定，不按干预效果选择。少量数据不能证明等效，warmup3仍不充分或时间漂移不可分时停止政策定案。
若最终需改变profile warmup，须另审该新政策最小配对Pilot证据，不能拿本批warmup1的Pass1直接冻结warmup3；不自动执行后续增量。

### 预算、精度估计与停止

**首批：3 block × 5条件 ×（P0-w1、P1-w1）=30进程、15条profile；每条件主配对n=3。**
**本计划总上限：60进程、至多30条profile。** 剩余30进程只选b4～b6（主配对n≤6），或上述warmup对照（主配对仍n=3，最多15条profile）。这是Pilot资源上限，不是已证明足够的正式repeat数；只授权准备，未授权运行。
首批后统一审查一次再决定是否使用剩余预算；不自动续跑/重试、不按单组补足“成功样本”。失败/partial消耗attempt预算；未执行槽位保留NOT_RUN，不冒称已尝试，也不自动替补或扩预算。关键失败停止余下批次。

先报告每个repeat原值、配对差、median/范围、block/顺序变化及失败原因。用Pilot重复/配对差的波动估计Formal所需n：分别对latency、A分量/unknown及N1配对差建立精度—成本表，按repeat/block重采样，不把token/kernel/sync当独立样本。
可给`n候选≈n试测×(当前不确定性宽度/预定目标宽度)^2`作粗预算，不当作保证或功效证明；接近零的差用绝对精度，不以相对CV或CI跨0决定加采。
目标精度/等价带须按可支持claim的最小有意义分辨率，于Formal前结合Pilot噪声和成本明确固定，不从Engineering单值、效果大小或旧v3阈值套出。
首批n=3甚至上限n=6都可能不足，不能因预算用尽就判Gate11 PASS；预算内不能支撑政策则报告未定并收缩claim/集中审查，不无限加采。

成本只用于调度：已有N1两组driver为219.203/224.157s、G512为231.063s（包含分析复读），profile约36.671–38.312s；旧G32 Pass0约27.437s。
来源为封存d25两组及700f671/36ed952的`driver/process.json`、`collection_log/process.json`，不是request latency，也不保证Pilot速度。
按每profile全链4–6分钟、每Pass0进程0.5–1分钟留余量：首批约**1.5–2小时**，上限约**3–4小时**，传输/人工审查另计；warmup增量或失败不据此自动扩超时。
已有两N1组解压1,131,867,072 bytes，G512 935,230,566 bytes，G32配对928,843,305 bytes；主要是派生文件，不能只按小REP估计。
首批约**11GB原件/派生（规划15GB）＋0.3–0.5GB ZIP**，上限约22GB（规划30GB）＋0.6–1GB ZIP；按封存与审查副本并存，预留**35GB/70GB**工作空间。不复制仓库/模型，不删除Raw来满足预算。
这是旧包目录大小/小报告读取的预算，不是新采集、峰值内存证明或哈希复验；实际成本必须逐run记账。

沿用已验证profile/driver的有界超时（工具120s、collection外层300s、含分析driver900s，交付时核对实际接线），禁止自动提高。
OOM、EOS/输出不一致、身份/边界/drain冲突、必要依赖缺失、超支持域/新型未知影响诊断、分析/守恒失败、磁盘不足或超时即停，保留具体分类和未执行清单。
不得把慢分析当OOM、把调度总时长当request时长，或自动杀无关进程；写入者退出状态不明先停止封包。

### 区分开销及待冻结政策

- 对同窗口host边界时长T0、T1，记录`delta=T1−T0`和`ratio=(T1−T0)/T0`（T0必须正），负差也保留；它是**profile＋观测插桩＋运行波动的配对差**。当前P0不发通用NVTX，不能称纯Nsight overhead，不从P1 A逐项减这个差。
- 同pass、同block的Nm−N0估计整套分支/包装/marker成本；N16−Nm估计同步干预总差，不是纯同步API持续时间或因果净等待。
- Pass0是性能主口径；Pass1给A和合格单sync B用于解释，N1配对还需按pass分别检查差异，识别profile×variant交互。allocation次数/区间/opaque预算差别仅按实际可观测的Pass1保留，不能推定未profile的Pass0也相同；大小未知不填0。
- 有效性硬门（身份、completion、S/terminal、互斥/守恒、源引用及输出一致性）不由Pilot放宽。已知warning仅按现有官方版本规则，未知影响仍拒绝；UNKNOWN/NOT_ASSESSED不改零或PASS。
- Pilot需要形成：warmup策略、repeat/block与最大成本、profiler差异可接受范围/处理政策、局部unknown与supported/B-valid覆盖的解释阈值、排除/失败/重试规则、最小精度/等价带。按原因/分布/敏感性与claim决定，不设“unknown必须0”或按结果反向放宽。
- G1只投影A；N1只合格单sync B，保留RAW_PHYSICAL来源及opaque等待不拆的限制；无自然默认流完整B，B不跨sync加总，D/Signature禁用。null/信息等价也是合法研究结果。

### 本地接线与阶段适用性（7.112）

已有入口可复用：固定内容/解释器/设备、isolated preflight、host completion、专用流桥接、producer/文件链、S/A/B及逐request准入；没有理由再跑完整Q0或旧Gate。
7.111发现的Engineering-only/pass1与仅核输出数量缺口已在明确Pilot分支修复，旧Engineering读取/拒绝门保留。新角色贯通manifest、pass ledger/Raw marker、producer、receipt、Canonical和domain；不能只改文字升级旧产物。G512/N1均有真实Pass0接线，窗外持久化已host-readable token值并逐值配对，不增加D2H或同步。
N1 Pass0保留干预marker/branch、V16实际sync及原流/anchor/drain；通用观测NVTX关闭不会删掉干预行为。首批CPU producer/文件链及预算/停止验证不是模型CUDA/Pilot证据。首批warmup1不改；7.114新版本及7.115目标warmup1/3证据已收口，未观测暖机字段仍null；本批无新profile/A/B，不自动采集或升级资格。

用户已明确批准仅未来新采“沿用已限定支持域的Pilot政策估计”；版本化声明见上链。原UNKNOWN/NOT_ASSESSED、opaque/B及分域claim限制不变，Engineering不改名，不授科学效果/Formal。无需全capture认证、完整Q0重跑或重开Gate8～10；超支持域仍拒绝。没有新增语义待决，本批尚未采集。

### Freeze输入与本轮停点（EP-G11-03/04）

后续Pilot报告须填入：所选有限输入/输出/batch及digest、模型/栈/执行与分析版本、N1/G1分域claim和资格引用、边界/流/opaque政策、实际warmup/repeat/组序/pass差异、失败与排除清单、质量/overhead/精度数值依据、统计单位/方法/seed及图表比较规则。
未定数值明确PENDING，不用Engineering数据填齐；Protocol Freeze仍Gate12单独决策、Formal须新采。本计划不预授N1信息增益或G1趋势。
7.112历史首批交付已由7.113实物审查取代，7.114待审交付由7.115目标warmup证据/集中政策审查取代。下一项仅集中裁决warmup3候选及唯一有界补证预算；原60已耗尽，Gate11 BLOCKED，不自动进入Freeze/Formal或加预算。原批次NOT_RUN/BLOCKED/STOP_FOR_REVIEW报告不改写。
