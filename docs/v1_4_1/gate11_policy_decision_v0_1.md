# Gate11 补证前政策与预算决策 0.1

2026-10-01；`G11-POLICY-DECISION/0.1`。Material Passport：ExposedPath / 本地政策设计；数值政策状态 **ANALYZED / PROPOSED**，不是新实验或 Protocol Freeze。

**7.117现行授权追加：用户已批准本页唯一30进程/15profile共同w3批次预算，已进行[最小接线与待审交付](gate11_warmup3_pair_v0_1.md)。**10/5ms、repeat及最终政策仍待审；只批准此有限批次，不自动续采、不授Gate11 PASS。本页以下“预算未批/不实现”保留为7.116形成提案时的历史，不再是当前操作指令；§4裁决方法保持。

**推荐只补一批：五条件共同 warmup3、三个完整 block、相邻 Pass0/Pass1，共30新模型进程/15新profile。**本次仅收敛方案；原60进程预算已耗尽，追加预算未批准，不实现或制作新部署包。Gate11 **BLOCKED**，Gate12 **NOT_RUN**。补证目标是确定可执行的有限政策，不是证明同步干预有效或波动归零。

## 1. 证据与文献约束

复用[首批审查](gate11_first_batch_review_v0_1.md)、[首批汇总](gate11_first_batch_summary_v0_1.json)及[两批集中审查](gate11_warmup_policy_review_v0_1.md)/[warmup汇总](gate11_warmup_policy_summary_v0_1.json)，不重扫ZIP、重算analyzer或测试。执行221f46c为w1配对，4abb5ea为独立P0-w1/w3对照；**不跨批配对，不混成n=6**。新批每条件仍只有3个完整pair，不能把旧P1-w1当新w3证据。

权威依据：研究设计v7.1 §2.3.9/2.11/3.2.1、Pre-Pilot协议v2.1 §1.5/6.2及已批准[限定Pilot合同](gate11_pilot_contract_v0_1.md)。当前DOCX的历史广域任务不恢复为本次前置；本页不修改S/A/B、资格支持域或旧判定。

文献只支持设计原则，不替本项目给出repeat或warmup常数：

- Kalibera & Jones，*Quantifying Performance Changes with Effect Size Confidence Intervals*，2013技术报告（2020上传[作者全文](https://arxiv.org/html/2007.10899)，§2.2/4/6.1/7）：量化最终比较量的不确定性；重复应匹配变异层级和成本；未控制因素造成的偏差不能靠更多重复消除。本文据此保留block/配对，估计差值本身，不把单组SD当差值精度。没有照搬其示例的30次或steady-state保证。
- Hoefler & Belli，*Scientific Benchmarking of Parallel Computing Systems*，SC15（[作者资料及摘要](https://htor.inf.ethz.ch/publications/index.php?pub=222)，DOI `10.1145/2807591.2807644`）：性能报告须区分改进与噪声并保持可解释性。本轮核验范围为作者摘要/书目信息，不将其表述为已全文审核或“六次足够”的来源。

这是对既有政策方向的窄文献核对，不开启新文献调查。进程内多request可降低将来加载成本，但会改变变异层级和流生命周期；**仅列后续可选优化，不实现、不作为Gate11前置**。

## 2. 精简决策表：解释尺度与claim退路

`h`为**建议的均值/差值区间半宽目标**，单位ms，不是最小真实效应、显著性门、A分类阈值或等价带。本页先提出Request/Prefill 10ms、Decode 5ms、N1总差10ms的有限解释目标：面向约百毫秒request的粗粒度结构、以及一个decode step的阶段比较；不以本批差值方向/效果量选目标，也不宣称该尺度足够所有用途。它们是研究用途与预算的待审取舍，**不是由文献或测量粒度唯一推出的常数**；预算不足须缩claim，不能反向放宽h后声称原精度已通过。更细1ms不列当前主claim。追加预算批准不自动等于冻结这些目标。

| 拟解释对象/尺度 | 当前具体不确定性 | 重复候选与成本依据 | 预算不足时收缩的claim |
|---|---|---|---|
| G1及各N1条件P0 Request；h=10ms候选 | 新P0-w3各条件SD 2.679～20.727ms，仅n=3；条件化/次序与跨时段波动未排除 | 完整block n=3/6/12比较；最宽SD对应SE粗预算11.967/8.462/5.983ms，成本见下表；不是CI或充分性证明 | 报原值、分布和区间；不报精确到1ms的性能排名、稳定加速率或平台总体规律 |
| P0 Prefill；h=10ms候选 | w3 SD最大20.320ms；warmup变化多集中于prefill，不能将全部差归于暖机 | n=3/6/12的最宽SE粗预算11.732/8.296/5.866ms | 限定所测输入的阶段描述；不外推输入轴连续/单调关系或微小prefill收益 |
| P0 Decode；h=5ms候选 | w3 SD最大6.191ms；暖机对照方向混合，且输出2只有一个decode step | n=3/6/12的最宽SE粗预算3.575/2.528/1.787ms | 报该单步原值/区间；不主张长decode、逐token稳定性或细尺度差值等价 |
| 同block、同pass的Nm−N0与N16−Nm；总差h=10ms候选 | 新w3-P0 Request差SD分别14.714/17.116ms，有反转；新w3-P1与profile×variant尚无数据；allocation不能假设相同 | n=6粗SE约6.007/6.988ms，只是P0预算参考；P1及差中差须用其自身差值波动，不能套P0结果 | 保留实际干预/等待迁移的可核验事实；不称稳定E2E收益、纯marker成本或纯wait因果贡献；不得按最有利pass选主结果 |
| P1 Request/phase A结构及N1合格单sync B机制 | 旧P1-w1的A分量波动不同；marker观测延迟不是已校准误差界；opaque等待未拆；B不能跨sync求和 | n=3新批先检同政策观测适用；正式n只按本量/差值预算。A比较沿Request/Prefill 10ms、Decode 5ms候选；不由P0较小SD保证 | A只解释观测执行；B只解释该次合格sync。细尺度群体变化不支持时，保留单次provenance/区间而不宣称普遍机制强度；不迁移为未profile执行的精确拆分 |
| P1−P0与profile×variant扰动；保留全部signed差 | 旧w1 Request配对差SD 16.142～90.377ms、相对差−18.109%～+101.142%；含profile/插桩/波动，w3未知 | n=6最宽SE粗预算36.896ms只是旧政策风险参考；不作为新w3方差预测或一个全局overhead门 | 仍可并列P0性能与P1观测解释；扰动/variant交互无法支持精确迁移时，取消“P1数值代表自然P0”的claim，不扣A、不删负差/极值 |

所有SE粗预算均是`历史样本SD/√n`，只展示未证明独立/平稳近似下的成本敏感性，**不是95%CI、功效、测量误差界或建议n已经足够**。n来自完整block，不来自token/kernel/sync/warmup；单进程独立启动不证明统计独立。h减半约需四倍n也只作粗预算，不触发补采。

| 共同w3的完整block候选 | 新进程/profile | 时间/原件数据/含审查空间估计 | 资格与预算说明 |
|---|---|---|---|
| 3 | 30/15 | 70～90min / 规划15GB / 预留35GB | **唯一下一批提案**；每条件3pair，完成即停，不保证政策精度 |
| 6（原三组序＋镜像） | 60/30 | 140～180min / 30GB / 70GB | 仅未来正式设计成本候选，先解决w3适用；不是追加Pilot授权、充分性证明或最终repeat决定 |
| 12（重复完整平衡组序） | 120/60 | 280～360min / 60GB / 140GB | 仅精度—成本敏感性比较，不是推荐续批或预算承诺；预算不支持时缩claim |

时间以首批driver合计65.86min及warmup对照的实际stage记录留余量外推；不是request latency，传输/审查另计，磁盘不是峰值内存。保持已有数据，不删除Raw满足空间。未来Formal须重新采，Pilot和跨暖机队列不能补齐其n。

## 3. 唯一待预算批准的新批

五条件仍G32/G512/N0/Nm/N16；Qwen2.5-1.5B-Instruct，固定内容/输入digest，单平台、batch1、eager/fp16/SDPA/cache/greedy。G1为32/2、512/2；N1显式流32/2 V0/Vmarker/V16，层16一次decode干预。**共同warmup3、每进程repeat1**，加载/暖机/成功drain在计时窗外，host-readable completion不改；N1 held暖机流和fresh measured stream不改。

- b1：G32→N0→Nm→N16→G512；b2：G512→Nm→N16→N0→G32；b3：G32→N16→N0→Nm→G512。
- block b与位置j从1起，b+j偶数P0→P1，奇数P1→P0；同条件两pass相邻、独立进程/run、同pair身份。三个block不声称完全平衡。无新点位/暖机扫描/长期进程框架。
- 每次暖机实际顺序/次数/成功、测量token逐值一致、实际variant/流/干预和stage须留痕；未观测暖机token/EOS保持未知。不增加D2H、同步或改变completion用于比较。
- P0性能，P1观测执行A/B；保留Nm−N0、N16−Nm两项对照及两pass的差中差，不因符号不利删除Vmarker或其他必要对照。所有有效样本和负配对差保留。
- 新批预执行版本/用途须绑定manifest→producer→pair→consumer/report；旧合同/数据/原报告保留，不仅修改文字升级角色。固定执行commit与源码/配置身份**在预算批准后的交付阶段**核定，本轮不占位生成部署脚本/ZIP。

这是原60预算外**额外30模型进程/15profile**；若完整执行，全部Pilot累计90模型进程/30profile。只审此批，不授权其他批次、正式n=6/12或Formal。

## 4. 批次结束后的政策裁决方法（预先固定，非找显著性）

1. **先核硬门。**逐run核身份/输入/实际token/执行配置、clock/completion、成功drain、N1实际干预/流、S必要集合/ownership/terminal、诊断规则、整数互斥守恒及源引用。缺失、冲突或影响不明仍拒绝；官方同类warning仅按已批准规则。coverage是调用证据覆盖，不是request可解释比例；UNKNOWN/NOT_ASSESSED不改零。required intervention B不合格就禁止该机制claim，不能以A守恒替代。
2. **报告完整原值与指定比较。**按condition/block/实际先后序列Request/Prefill/Decode、P1−P0、同pass N1两对照和profile×variant，列mean、median、min/max、样本SD；A各分量和opaque实际记录单列，保留未知allocation大小和内部等待未拆。不得从A扣配对差，不能把全部N1总差解释为sync净等待。旧w1和独立w3-P0仅作分层背景，不与本批混池或配对。
3. **精度只用既定统计单位。**均值/差值的95%percentile bootstrap候选沿协议，以完整block重采样，保留同block所有条件/pass/phase、单sync来源；拟固定seed=20261001、10000次重采样。n=3的区间仅为小样本探索性估计，不保证覆盖率；同时必须展示全部三个block及逐一留出block的均值变化，不能把重采样次数当样本量。相对差仅补充，接近0用绝对ms，不做p-value选点或“CI须离零”停止规则。本轮不实现统计脚本，Gate12再绑定批准版本。
4. **warmup裁决。**新w3双方实际完成、执行/观测硬门一致且有可报告三窗口/A/B，结合已完成w1/w3对照，可采纳w3为有限conditioning政策；不要求零漂移或完全收敛。若有明确初始化/状态问题破坏支持域，保留BLOCKED；若只是混合方向/噪声较大，报告限制并收缩精细解释claim，不恢复暖机扫描。N1 measured流“fresh”是合同条件，不作为异常删样。
5. **精度—成本裁决。**对每个对象列区间半宽`H=max(mean−L,U−mean)`、全部block方向/顺序及留出敏感性，与上表待审h并列。H或留出敏感性大于h时，标为该尺度未获支持，不据此剔除样本/补采；即使小于h，小样本/顺序混杂仍须明示，不宣称稳定性或等价。最终repeat从完整block成本候选中一次性决定，给出各主要量自身的精度预算及有限claim；不能将六次当充分，也不拿稳定P0替P1/N1证明。Formal中固定n结束后仍按预定规则报告不确定性，不追采到显著。
6. **扰动与局部缺口的解释政策。**不设追溯性统一overhead百分比门。较大扰动/差中差或方向冲突只限制P1→P0迁移claim，不自动否定合格观测执行的A/B。可证明局部缺口保留unattributed/原因及其对特定比较的最坏可能影响；该影响覆盖拟解释尺度就只发布有证据部分/保守范围，不称精确分类差。缺口影响无法界定则沿原门拒绝；不能补Host/residual。supported/B-valid分母与失效原因全量保留，不将100%/零unknown追设为必须。marker lag及host/trace各自窗口差独立报告，既有整数守恒不当校准证明，h不充当clock tolerance；未经误差资格不作亚毫秒跨时钟/跨pass数值等同claim。
7. **一次集中收口。**若w3适用、硬门/处理政策/最终repeat与成本/有限claim均有明确记录，EP-G11-02/04可按其退出条件审查，不要求观察到干预收益；只是噪声较大时优先删除精细或稳定收益claim，保留有限观测机制问题。若收缩后仍无法给选定claim的必要精度/观测适用依据，Gate11继续BLOCKED并指出具体未决项，**不自动下一批**。Gate12的代码/registry/schema、统计脚本与协议签字仍独立，不能由本报告或预算批准直接授Formal。

## 5. 授权与停止点

预算批准前只保留本政策表及计划；下一步由用户集中决定是否批准上述**额外30进程/15profile，70～90min及35GB空间**。批准后才实现最小版本化配对接线、相关CPU验证，绑定固定版本、以前置服务器4abb5ea为基线制作唯一部署ZIP/完整hash/准确传输路径/整段命令/单ZIP回传，先交协调窗口审查；不新增独立资格层、全量Q0或工程监控。

沿用现有工具/采集/driver超时，不增加超时。OOM、超时、身份/输入/token/边界/drain/必要依赖/诊断/分析硬失败或磁盘不足立即停，保留partial、失败原因及未执行槽位；不自动retry/替补/resume、临场改参数或杀无关进程。partial消耗attempt预算，未执行不冒称已尝试；写入者退出不明先停封包。固定30槽位完成也立即停待审，不因噪声、负差、CI跨0或预期效果缺失继续采。

本轮11/11统计风险已检查：保留分层/共同block防聚合混淆和伪重复；不按效果/成功/低unknown择样，不删极值，不补到显著；明确Pilot选择是探索性、未知混杂不能靠CI消除；不作纯profiler/同步因果归因或“无差即等价”。其余不适用项不新增分析。只核本页方案/数字/链接与进度一致性，不重复原包/分析/测试；原证据、旧判定、用户DOCX及全部研究语义保持。
