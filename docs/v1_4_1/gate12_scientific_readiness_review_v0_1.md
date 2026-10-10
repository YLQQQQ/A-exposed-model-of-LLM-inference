# Gate12 科学适用性审查 0.1

> 2026-10-10：有限P0/P1范围、负结果判据及原预算仍有效。Gate13 prepare工程修复需[0.1.1新精确候选](gate12_freeze_candidate_v0_1_1.json)重新签署，不重选claim或重新评估Pilot；没有新的测量语义或资格采集。旧0.1发布/失败证据保留，当前Gate13 BLOCKED；源码/文档锁与后续状态提交分开，见进度7.125。

> 2026-10-09：用户已接受本页有限P0性能/P1观测机制、限定Formal适用和六block预算，已记录[签署与Gate12收尾](gate12_closeout_v0_1.md)。下文待裁决/NOT_RUN保留为历史，不重新要求确认；科学限制和负结果判据不变，尚无Formal采集或信息增益结论。

2026-10-02；`G12-SCIENTIFIC-READINESS/0.1`；Material Passport：ExposedPath research protocol + ARS experiment-agent plan/validate；状态 **ANALYZED / 待裁决，不是Protocol Freeze**。Gate11仅限定Pilot政策审查PASS；Gate12 **NOT_RUN**，Formal未授权。推荐[冻结草案0.1](gate12_protocol_freeze_draft_v0_1.md)，本页不改研究设计DOCX、测量合同、历史数据角色或机器报告。

## 1. 核心问题与可证伪范围

权威来源：[研究设计v7.1](../current/ExposedPath_研究设计.docx) §1.3–1.4、1.8–1.9、2.3.9、2.11、3.2；[实验协议v2.1](../current/ExposedPath_实验协议.docx) §1.2/1.5、4.4–4.5、5.1、6.1–6.4。两份仍是当前主体/Pre-Pilot，不是已冻结协议。研究设计明确“现有指标是否足够不能靠预设判断”（§1.3）；协议§4.5允许raw sync已足够解释时降级为信息边界结果。后续已批准路线A、[N1/G1分域合同](gate9_domain_qualification_contract_v0_1.md)、[窄域allocation规则](n1_opaque_allocation_v0_1.md)收缩早期多平台/全矩阵计划，而非恢复所有历史候选。

| 预先固定的问题 | 比较、证据与统计单位 | 支持／不支持／不确定判据 |
|---|---|---|
| G1：32→512输入时，常规工作量描述遗漏了哪项request/phase归属信息？ | G32/G512；同block的P0性能差与P1 Raw、三窗A分别比较；每条件每block一request，不把kernel当重复 | 支持有限信息增益须有可审计的具体归属命题，公平baseline不能直接回答，而合格S/投影/A及独立必要成员核对能回答。只有更多kernel、API、总时长或五类图不支持增益；baseline已解释则记录本设计未显示增益。缺必需证据或重复变化无法支持数量级则不确定，不另选点 |
| N1：固定层16同步的局部等待，与整个request/phase变化是什么关系？ | 同显式流的Nm−N0（必要包装/marker对照）与N16−Nm（预定同步对照），两pass均保留；P1逐sync的完整W、terminal、hidden/exposed/tail与三窗A | 支持限定机制信息须证实实际干预、必要集合和等待所在区间，并指出raw sync持续时间与request预算不是同一量；若baseline已足够解释则无额外机制增益。不能从局部sync直接推导P0净增量；稳定增量/等待迁移强度无足够精度时只报告观测事实与不确定性 |

两项区分四层：①已有资格验证正确性，Formal逐request再核准入；②具体机制事实是该P1执行的W/terminal/等待归属；③信息增益是相对预定公平baseline的新增、可检验解释，不是守恒；④性能收益须另有P0差值及不确定性证据，不是信息增益的必需成功条件。G2/决策价值、D/Signature、硬件根因、长decode规律和输入轴连续响应不在本设计内。

### 公平baseline与有限增益判定

baseline使用**同一P1 trace、同一目标进程/request/phase、clock与裁剪窗口、同一API registry**，不把全会话或未裁剪sum拿来与A比较。预定常规层包含kernel/MemOp/API/sync count、区间时长sum及union、GPU active ratio、launch-to-start及其mapping状态；附标准timeline的流/context/correlation和调用顺序。相交活动sum明确可能重复，union按层报告，不当墙钟分区。失配mapping保持unknown，不能以baseline少查字段制造优势。

ExposedPath增加的是**完成语义约束的必要集合、terminal与互斥窗口预算**。标准timeline若结合相同CUDA语义也能手工得到同一答案，不能声称原始工具无法解释；应收缩为相对常用聚合指标的自动、可审计解释。若必须给baseline加入完整W与同样的A/B推导才得到答案，这已经是方法复用而非独立activity baseline；两种比较范围都公开，不把它称不可替代。

预定的解释检查只有三项，不建立新评分：G1的设备活动成本是否等于该窗设备等待、非同步API是否重叠/嵌套导致sum不能代表互斥预算、剩余时间是否有足够证据为Host补集；N1的干预W中哪些已先行完成、哪些在该sync内暴露、terminal后的部分是否仍不能解释为纯runtime成本。每条用源记录、区间/集合及独立复核支持或拒绝。可复用独立oracle中“相同activity成本、不同等待归属”和“总和闭合但错归类”反例，**反例证明不可仅由聚合值唯一恢复，不证明本模型一定有额外信息增益**。

Formal结果若只有API成本/普通阶段时长变化、对照已充分，必须结论为“当前两端点/固定位置未显示非冗余增益”；不能把一个漂亮timeline或小unattributed算作成功。只有两个输入端点，不能鉴定一般比例函数、regime边界或单调趋势；目前设计能检验有限案例信息增益，不能承担广泛图谱claim。此有限问题仍可得到明确负结果，而非以“允许不确定”掩盖未定义的目标。

## 2. P0、P1与观测扰动：必须集中确认的目标取舍

P0是**无Nsight、保留共同completion记录的指定执行**，不是绝对零插桩。G1保持自然流；N1 P0仍保留所属variant包装/marker/实际同步及fresh measured专用流。主性能来自host clock的Request/Prefill/Decode。P1是相同输入/执行合同下的被观测执行：host计时仅用于配对，A/B来自trace原生共同锚点和相应trace clock。

`δ_profile=T_host,P1−T_host,P0`及相对差仅是profile、观测插桩差异、顺序和运行波动的联合观察；`(N16−Nm)P1−(N16−Nm)P0`同样不是纯profiler交互因果值。**不做统一扣除、不重标P1成P0、不把P1的ΔA守恒改写为P0性能的因果分解**。单sync的hidden仍仅相对该sync；opaque allocation是API区间成本，内部等待未拆。

Pilot实际P1−P0 Request为−36.030%～+61.908%，N1跨pass方向/量级不同，marker lag约0.896～2.061ms、trace/host窗口长度差−1.474～+0.675ms。后两项不是时钟原点校准或误差界。trace内合法区间与source identity有资格，但不授亚毫秒跨clock等同、P1→P0迁移或精细Host边界误差结论；源记录错误仍硬拒绝，不能拿10/5ms当clock容差。

**推荐取舍：保留P0性能与P1执行机制的并列验证，取消精确自然P0组成迁移。**损失是不能把A图直接称为“未profile用户请求真实时延由哪些原因组成”，也不能据P1推断细微P0收益。保留的是同步语义驱动的可审计归属方法、观测执行中的有限非冗余解释及公平负结果；这仍覆盖原核心“activity不等于exposure”的测量问题，但比原自然性能机制解释更窄。若用户坚持后者是最低贡献，本方案不足，应停在该claim并另行设计扰动迁移验证；增加几个相同block并不能证明迁移，本轮不实施新观察方式。

## 3. 已有Pilot的实际判别能力

只消费[共同w3汇总](gate11_w3_pair_summary_v0_1.json)及[host原值CSV](gate11_w3_pair_durations_v0_1.csv)，沿用[完整实物审查](gate11_policy_closeout_v0_1.md)，不重扫封存包或调用analyzer。汇总SHA256 `650c762c4d4411ef1d71f64dc6dfd3dccadb9f5331a22c5bbc175bb29e50c279`；执行`470c5afa6400a77fb79692699cdd8cecc47b314d`。本轮只核所用整数/配对/三窗算术和两个小manifest的已有来源hash；新算术与两份草案可复算，不是新平台或Q0证据。

三批分开：221f46c是w1配对，4abb5ea是P0 w1/3对照，470c5afa是双方共同w3。均每条件三个block；不拼成n6，不跨批/暖机配对。共同w3足以作为有限conditioning选择，不证明完全收敛；独立进程启动不证明统计独立、稳定或没有共享主机混杂。

### 性能与必要对照

单位ms；`SE6`仅为**本量n3样本SD/√6**的预算敏感性，不是CI/功效或实际精度。G1三窗均给出，N1的phase原对照保存在源JSON，全量随未来结果报告。

| 对象 | 本批三个原差值 | 样本SD | SE6粗预算 | 能／不能判断 |
|---|---|---:|---:|---|
| G1 P0 Request：G512−G32 | 13.4596 / 19.9525 / 14.0855 | 3.5817 | 1.4622 | 有限端点总时长对照可设计；不是输入规律/精度保证 |
| G1 P0 Prefill | 21.1741 / 19.6243 / 9.8812 | 6.1218 | 2.4992 | 输入轴主要阶段有可比较量；顺序混杂保留 |
| G1 P0 Decode | −7.7145 / .3282 / 4.2043 | 6.0796 | 2.4820 | 方向反转；输出2只有一个decode step，不能宣称稳定输入效应 |
| G1 P1 host Request／Prefill／Decode | 均值9.9058 / 6.9964 / 2.9094 | 3.9578 / 6.1844 / 3.0241 | 1.6158 / 2.5248 / 1.2346 | 仅观测执行host对照；不等同P0或trace A |
| P0 Nm−N0 Request | 187.1321 / 19.0520 / 4.9711 | 101.3507 | 41.3763 | 没有10ms精度依据，不删有效长值 |
| P0 N16−Nm Request | −146.8211 / 5.8898 / −5.4698 | 85.0782 | 34.7330 | 无稳定收益/纯等待因果依据 |
| P1 Nm−N0 Request | −7.2887 / 6.0945 / −24.8864 | 15.5382 | 6.3434 | marker对照仍必要，不能扣成固定成本 |
| P1 N16−Nm Request | −13.3035 / −33.2980 / −5.9728 | 14.1432 | 5.7739 | 可检机制事实，三次同号不保证稳定收益 |

### A/B不能套用性能精度

P1 **同block trace A分量差**（均值／SD，ms）：

| 对照/窗口 | CUDA API | Host path | 受支持device wait |
|---|---|---|---|
| G512−G32 Request | −7.2372 / 5.7894 | 16.7288 / 8.3077 | .2567 / .4781 |
| G512−G32 Prefill | −2.9630 / 2.1633 | 9.4483 / 3.7774 | .2567 / .4781 |
| G512−G32 Decode | −4.2742 / 5.5600 | 7.2804 / 6.1842 | 0 / 0 |
| Nm−N0 Request | 1.2841 / 16.0877 | −9.9681 / 22.1026 | −.0289 / .0575 |
| N16−Nm Request | −13.1371 / 5.8586 | −4.6685 / 8.9439 | .1662 / .0546 |
| N16−Nm Decode | −5.9052 / 2.3180 | −1.7500 / 3.1206 | .1147 / .0046 |

所有有效值、API子类/residual/unknown和阶段均保留源JSON，不只报告此表显眼分量。当前G1较大Host/API差可能已被普通API/阶段指标充分解释；不能预设增益。device wait小量不用于证明P0的亚毫秒效应。45窗unattributed=0只是实际支持域结果，不是未来选样或资格阈值。

N16三次干预单sync的W均2814，hidden union均值45.1095ms、SD2.5387ms；exposed union均值.114687ms、SD.004610ms；return tail均值.047128ms、SD.047175ms。这是**对应原record的单sync观测事实**，不跨sync加总，不把2814成员当n，也不将小SD变为测量误差认证。能检查完整W含已完成前缀、terminal及局部暴露；不能据此解释P0的N16−Nm总差。各组实际allocation与未观测大小保留，不假定组间相同。

### 固定预算选择

| 完整block数 | 进程/profile | 粗成本（沿本批99.87min/21.03GB外推） | 判别能力与缺点 |
|---|---|---|---|
| 3 | 30 / 15 | 约100–120min、21.0GB原件/45GB含审查 | 与当前Pilot同量级，顺序不平衡、小样本；不推荐作为最终重复设计 |
| **6：推荐** | **60 / 30** | **约200–240min、42.1GB原件/90GB含审查** | 原三序及镜像改善位置平均与对照先后平衡；每条件n6，仍不保证独立/平稳/10或5ms |
| 12 | 120 / 60 | 约400–480min、84.1GB原件/180GB含审查 | 只在独立平稳假设下SE再约降√2；不能解除扰动迁移/顺序混杂，本轮不推荐或授权 |

六block不是完全Latin-square或随机化：若沿同会话顺序，镜像不能消除全部时间漂移。N1 P0差值SE粗预算仍数十ms，**明确放弃保证10/5ms与细微稳定收益**，不反向加宽候选后称达标。该预算适合限定机制事实与粗粒度对照；性能/分量效应方向若仍不可靠则给“不支持数量级结论/不确定”，而非追加到显著。若最低论文claim是证明5ms级性能改善，n6设计不够，最小选择是取消该claim，不是承诺n12解决。

## 4. 资格转入Formal的真正差异

| 条件 | 可复用证据 | 剩余事项，不重采全部Q0 |
|---|---|---|
| N1实际流/ownership、完整W/terminal、单sync B；G1必要后缀投影A | [Gate9裁决](gate9_closeout_v0_1.md)、受控独立oracle/负例；[N1模型实物](n1_model_feasibility_closeout_v0_1.md)、本批三次暖机/fresh流及逐request门 | 同支持域/同语义复用；输入长度本身不触发Q0。没有自然默认流B、event/graph/多线程扩域资格 |
| RAW_PHYSICAL、signed时间与cudaMalloc opaque例外 | [来源增量](n1_raw_provenance_allocation_v0_1.md)、窄域amendment、原V0续算和本批30合格B/45A | 冻结精确版本/hash和解释限制；不把资源管理API成本改称非阻塞或完整设备等待，不授所有新版功能 |
| 同类外进程warning | 已批准[G8-WARNING-EVIDENCE/0.1](gate8_warning_evidence_review_v0_1.md)、目标实物及本批精确消息处置 | 复用，禁止重开全capture认证。新类型/目标冲突仍拒绝；UNKNOWN不改零，不声称排除未记录依赖 |
| Formal角色与协议引用 | 当前`exposedpath/gate11_pilot.py::roles`只收Engineering/Pilot；`canonical_raw.py::convert_sqlite_to_canonical`的gate8_sources同样限两角色；域报告写formal_eligible=false | **确有本地接线缺口**：批准草案后新增严格Formal执行封套/消费分派，贯通预声明→manifest/ledger/NVTX→receipt→Canonical→报告，不开放任意role；旧数据拒绝升级。只做元数据/封套定向CPU链检查，S/A/B未变则不要求新CUDA微程序 |
| 公平baseline及统计复算 | 相同Raw/phase/correlation字段已有，本轮源汇总算术可用；既有Pilot统计为描述性 | 冻结前需要一个小型同窗baseline/对照汇总入口及whole-block统计版本/hash，独立手算正反例：嵌套sum/union、错scope、缺mapping、signed差和成块重采样。不是新采集/监控或第二analyzer |

`ab_schema_v0_6.json`虽枚举Formal，标题及validation_role/NOT_ASSESSED限制并不自动赋予资格。Formal角色是新采数据用途；“限定支持域是否足以承载本草案claim”须明确签字的资格裁决，不能把schema接受或Gate9 PASS当科学有效性。当前docx的广域扩展Q0/registry v1.0要求须与批准的增量复用及窄域例外**透明对应**：发布固定受支持profile的正式资格清单及内容锁，不给未覆盖能力全量v1.0证书。历史Gate6 PASS不撤销、不自动继承新版本全面资格。

Pre-Pilot原设计§2.11的5%目标/10%门、协议§6.2 dropped=0/失败重跑，与已批准的目标scope、Pilot signed扰动/无自动补采政策不同。冻结草案逐项列明拟覆盖：**科学claim限定P1，不能承诺通过原自然P0迁移/全矩阵/精度标准**。这不是据Formal结果放宽，Formal尚无；需冻结前集中确认，不静默修改DOCX原文。共享平台/动态clock、native attention backend UNKNOWN保留，不能以configured SDPA取得特定native kernel资格或纯干预因果识别。

## 5. 推荐、集中确认与停点

推荐版本：`G12-ROUTEA-FREEZE-DRAFT/0.1`，五条件、共同w3、六完整反向平衡block、每进程repeat1；问题是有限观测解释增益，P0性能并列，不承担精确迁移/细微稳定收益。**能检验收缩后的原核心问题，不能证明广域信息增益或原自然P0组成目标。**当前没有需要新Pilot或服务器操作的必要问题。

用户只需集中确认一个范围决策：**是否接受这一有限P0/P1双对象claim、窄支持域Formal适用声明及n6固定预算，不要求10/5ms保证？**推荐接受并允许负结果；若必须保留自然P0精确组成/细微性能收益，当前草案不足，停在该目标，不默认追加采集。

历史审查停点（2026-10-02）：冻结前仍不可省最小Formal封套、baseline/统计CPU复算、版本绑定及签字。本地实现已获后续授权，接线说明见[草案§7](gate12_protocol_freeze_draft_v0_1.md#7-冻结前实现封套与审阅入口2026-10-09)。Gate12不能因实现/CPU文件链通过即PASS；不生成可直接启动的Formal任务。

本轮11/11统计风险核对：按condition/pass/block分层防Simpson；不推广平台总体防生态谬误；不按漂亮A/有效长值择样防Berkson/幸存偏差；不按allocation/profile差筛样防collider；基率型诊断不适用；跨批变窄不作因果防回归均值；固定全部主要对照防look-elsewhere/forking paths；不把配对差或同期机制当纯因果，亦不倒推方向。没有p-value选择、伪重复、零差等价或bootstrap伪样本。数值是ANALYZED，未重跑实验；不承诺投稿结果。

本轮必要验证：本地`python -X utf8`运行独立描述性算术与文档校核，核原整数signed差/SD/SE预算、保存A的阶段加法及两份所消费manifest引用；六block组序/镜像、pass先后、条件平均位置和对照先后平衡、60进程/30profile/180实际暖机拟预算通过。174相对文件链接、公开私有路径扫描、DOCX原字节与暂存五份Markdown范围、`git diff --check`通过。未运行仓库测试/compileall、原analyzer/collect/export或全包再次hash扫描，因为业务代码未改；这些文档校核不冒称GPU或Formal资格。数值检查初稿的舍入手录值、负号显示字符检查不一致均在本地更正后通过，不修改源JSON/Raw。

## 6. 冻结前本地实现与资格复用审查（2026-10-09）

上述“仍只接Engineering/Pilot/不实施”等是10月2日的代码事实，不是现行限制。后续本地封套已按新版本贯通协议→manifest→producer/ledger/NVTX→receipt/Canonical→域报告，并增加同窗baseline和完整block统计入口；**协议未签署，Formal未授权，Gate12 NOT_RUN**。实现提交及精确内容绑定分两次提交，最终候选记录引用前者，不以候选/文档commit执行。

独立预期固定为：嵌套API[-8,4)、[-6,2)及sync[4,10)在[-10,20)内，sum26ns/union18ns，sync union6ns；kernel[0,8)、[6,14)的sum16ns/union14ns。signed post-return为−4/+4，不截零。缺mapping/ownership不是已知零；错scope/clock/重复record或未知registry拒绝。成块样例中每对P1−P0=−2ns，预定条件差10ns、交互0，whole-block联合抽样不能把条件/pass/kernel作为独立重复。实际CPU文件链还覆盖旧角色升级、未签署/错hash、设备/来源/token冲突、缺drain、wrong slot与完整60run索引；它们使用明确合成批准、设备/模型替身，不是CUDA或Formal实物。

审查测量差异：runner只扩展角色/同计划暖机/回执身份，不改变host-readable completion、window、drain、专用流、实际同步或S/A/B公式。新增driver只读baseline层不回写Canonical/S，缺表仍unknown；现有Raw、资格及所有历史输出不改。因此复用Gate9分域、N1模型/RAW_PHYSICAL/opaque及G1投影资格，增量仅为元数据与CPU文件链；不自动授全部新版Q0、默认流完整B或D/Signature。未来实际source/collector/执行语义改变须重新审查相应增量。

当前DOCX逐条对应仍为：研究设计§1.3–1.4的信息充分性/负结果、§2.4资源管理API成本、§2.11 repeat-cluster及Pass0主性能；协议§1.5–1.6 prospective Freeze、§4.5 raw指标已足够则收缩、§6.1同合法映射baseline、§6.2统计与质量。后续用户已批准单平台/单模型、分域、RAW_PHYSICAL、opaque和目标scope质量政策沿版本文档保留。**待签署的实质范围覆盖**只有原5/10%统一overhead/精确P0迁移与本草案双对象、全面registry/扩展Q0/广域矩阵与窄资格清单、dropped=0/自动重跑与保留UNKNOWN/硬停、不启用D/G2/长decode。不能把DOCX原文改成已经满足，也不提交用户DOCX。

11/11风险核对沿§5保持：按condition/pass/block分层、不推广平台总体、不择样/删长值或按allocation/profile差过滤、不从跨批变窄推因果、固定全部对照/预算与signed差、无p值择claim/伪重复/零差等价。基率型诊断不适用；新CPU数据仅检查实现，不重新估计Pilot精度。六block仍是有限预算/顺序平衡，不保证10/5ms；允许“不支持增益/不确定”，不以更多bootstrap迭代替代样本量。最终仍须用户集中确认此有限claim及预算并签署完整内容hash。

最终本地证据：九文件相关回归224 passed、0 failed、0 skipped（336.25s）；实际命令及临时目录ACL初次失败见[进度7.120](research_progress.md)。compileall、170相对文件链接、Formal schema校验、4份生成SVG的XML结构、保护语义文件zero diff、公开内容私有路径及用户DOCX原SHA检查通过。图表结构检查不是研究解释验收。代码审查逐入口核对版本分派、外部批准与prospective时序、实际输入/角色/文件来源、未知映射、joint block重采样与逐sync B不加总；没有发现本次范围内必须新增平台实物的测量变化。签署及执行授权仍是独立未决项。

版本绑定已收口：[未签署候选0.1](gate12_freeze_candidate_v0_1.json)执行/分析e38fa91850b8f31e17cc0ee264987ef3c1313d7d，protocol SHA256389a28a17bec830e4f32bea72c259dce15ba279ce69fc20caebfdca88a1326e2。候选引用该实现提交的本审查/草案快照，后续文档提交不是执行身份；125个hash锁定实现、schema/registry和限定资格，不自动授全面Q0或未启用功能。当前DOCX保留本地用户修改，候选仅记录其审阅来源hash，不提交或要求服务器覆盖。

推荐方案仍可检验原研究的有限信息增益：同P1 scope的常规cost/timeline与基于必要依赖的A/单sync B解释公平比较，baseline已经足够则不支持增益、证据或方向混合则不确定。它不承担自然P0精确组成迁移或细微稳定收益。六block只为固定预算/次序平衡，正式预算及签署尚未批准；本地实现完成不等于Gate12 PASS。唯一待用户集中确认仍是上述有限claim/阶段适用、预算和完整候选签署，无新增平台、实验或工程设施前置。
