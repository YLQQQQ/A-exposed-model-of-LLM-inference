# Gate13 完整取证副本与限定Formal离线审查 0.1

2026-10-11；`G13-LOCAL-COMPLETE-REVIEW/0.1`。Material Passport：ExposedPath / ARS experiment-agent validate；统计解释 ANALYZED，实际文件链已重新核验，不是重新采集。

**60次逐run执行合同检查、30条profile质量复核、90个A窗口、60条N1单sync B和六完整block统计已经完成，没有测量准入失败。Gate13仍BLOCKED：用户指定的外部`forensic_receipt.json`未在本地取得，服务器最终源集合复查及归档终态尚不能直接核验。** 这是一个具体取证收尾缺件，不是新增科学门槛、重新追索写者或要求重新采集。只需传回已存在的该文件，核对预定hash及其终态；本轮其余本地工作已经完成。

## 1. 原件与分析授权

- 封存ZIP：1381808437 bytes，SHA256 `a3f2e05bbfbdda8bbba025fd016bdc60c7652cd001b1dd54f5a0aec65435e6ef`。
- 清单SHA256 `87f60c7841c1a71225a4ccffa297503fdfc63e193d9c4f99c2b9c1c8488d42fa`。全部成员读至EOF完成CRC、路径/大小写/Unicode别名安全、重复、大小/SHA256及完整覆盖核验；4225成员恰为3586源文件、633目录项、5取证附件、1清单自身。没有缺源文件或空目录遗漏。
- 5附件为`instance_receipt.json`、原quiescence ZIP、取证工具、`source_before.json`、`copy_checkpoint.json`。源文件共42790896265 bytes。checkpoint明确复制后源一致、最终ZIP验证待完成，不能当作缺失外部终态回执。预期外部回执SHA256 `b4f5f8eef7cfbf1dec47be0285b0d39c12c3503b82e3e464b62227ea8dc46172`，尚未实测。
- 有限取证检查不证明不存在写者，也不是跨文件原子快照。原历史UNKNOWN、marker、BLOCKED及完整原件均保留；没有运行旧pack/finish-only或清理。
- 签署协议`G12-ROUTEA/0.1.1`内容hash `d9204a80bf15ce810093ec53c506d4bf3eadd2f1ad71db8844cff330f0c7448b`；签署发布字节hash `1378c89db04336102a9dc0ce53ef7b1ef17dd9c518320c060e74d39abaa5b669`；approval内容hash `423852a31bd858a56255ca092bc370eb2349fc293ecab182c9fae7dbc562780e`。
- 执行固定`99f3bae966f2fb794073ff4d7468233b6b8dd2ac`；新分析`e19c308d1254feb0e643ae56429d5afd2ab6b4fd`，parent `6e34959da44e5ede9f3f04241934194713144301`。本次审查/文档提交不代替任一执行身份。

按用户本次条件授权，[精确源码兼容记录](gate13_analysis_compatibility_v0_1.json)已激活为**本ZIP限定本地分析授权**，不是全局执行白名单。126冻结artifact：121不变、3纯性能分析接线、2此前签署状态文字变化。测量/质量/registry/baseline/统计公式与版本不变，不需研究协议amendment或重签输入。

独立授权`G13-OFFLINE-PERFORMANCE-AUTHORIZATION/0.1`绑定协议、ZIP、清单、执行/新分析SHA，内容字节hash `520053f1ea3dfc7d63352c98c1e2ce65e81ff3838d0575cbb48ead6a66f7616d`。使用e19的最小Git blob运行材料和显式审计adapter，不伪造checkout/clean，不沿用99的分析seal。旧封套/source/产物hash先独立验证；新计算完整S/A/B语义载荷与原载荷逐值相等，然后另绑定新分析源码/授权。baseline仍独立重算并与原保存值完全相等。

## 2. 已完成的退出项与证据等级

| 检查 | 实际结果与范围 |
|---|---|
| 执行/身份/输入/配置 | 60/60；五条件、六block、固定平衡次序及相邻30pair；协议、clean、GPU、显式解释器/PID、实际配置与逐值token一致 |
| 真实预检路径 | 每run原始Git二进制NUL清单617路径完整覆盖预检tree；126冻结执行文件实际LF/CRLF表示与Git内容锁一致；不是用当前任意hash更新期望 |
| 执行行为 | 每进程实际成功warmup3、measured repeat1、输出2且无early EOS；加载/暖机/drain/cleanup在窗外；N1 fresh显式流和V0/Vmarker/V16次数/位置成立 |
| P1身份与窗口 | 30/30；原NVTX point引用、clock、三窗连续、成功drain、必要后缀/归属/依赖全部复核；G1不授自然默认流完整物理B |
| S/A/B及公平baseline | e19完整复核30条profile；90窗口具体A分类、顶层/子类互斥守恒及Request=Prefill+Decode成立；unattributed全为0但不作为成功依据 |
| 独立Raw复核 | 30/30只读SQLite integrity、原point/drain、runtime correlation、限定FIFO必要集合、terminal、单sync B及五类A区间手算一致；不调用被测S/A函数 |
| N1单sync B | 60/60 B_VALID：N0/Nm每run3个，N16每run4个；内部RAW_PHYSICAL、两个token-ready、预定干预分开；完整W含已完成前缀 |
| 诊断 | 既有四消息按冻结官方处置依据；原warning与来源保留，无新类型豁免；dropped UNKNOWN、measurement NOT_ASSESSED不变 |
| 配对/统计 | 全部60原值、30pair、六完整block；102预定对比、signed差、固定seed联合成块bootstrap、留一及前/后三块全部保存；无排除/拼接/替补 |
| 完整取证终态 | 本地ZIP内容通过；外部终态回执缺失，尚不能核验服务器归档后最后一次源集合/内容复查。这是当前唯一待补文件 |

物理全会话S/B中的窗外INVALID不改写为有效，也不自动污染已经独立审查的目标窗。opaque记录54条（18个N1 P1各3次cudaMalloc），allocation大小未知、内部等待NOT_DECOMPOSED；各run总调用成本0.689340～1.790092ms，各组差异保留。不能把opaque cost说成非阻塞、全等待已恢复或全部E2E差由同步干预造成。

## 3. 结果与统计不确定性

全部整数ns见[60原值](gate13_host_durations_v0_1.csv)、[102对比](gate13_contrasts_v0_1.csv)、[90窗A/同窗baseline](gate13_a_baseline_v0_1.csv)、[60条单sync B](gate13_single_sync_b_v0_1.csv)、[allocation](gate13_allocation_v0_1.csv)。完整timeline/W/来源及图表保存在本地版本化派生目录，不提交Raw或私有路径。

下表单位ms；区间是冻结的95%percentile whole-block bootstrap描述，不是总体覆盖率或稳定性认证。每量n=6，kernel/token/sync不作为独立重复。

| P0对比 | Request mean [区间] | Prefill mean [区间] | Decode mean [区间] |
|---|---|---|---|
| G512−G32 | 16.7515 [1.7085,29.5059] | 11.0325 [1.8595,17.8551] | 5.7190 [−0.3232,11.6242] |
| Nm−N0 | 1.3585 [−9.0610,11.7780] | −4.0534 [−9.2816,1.8752] | 5.4119 [−0.4681,10.9951] |
| N16−Nm | 11.1567 [−4.8618,28.8418] | 4.3791 [−5.7032,14.4692] | 6.7777 [−0.4389,14.7649] |

三项P0 Request对比都存在block方向反转，不能称本六块方向一致。N1 P1 Request对比也混合：Nm−N0均值13.7519ms，N16−Nm 5.9063ms；同步profile×variant交互−5.2505ms，区间[−45.9330,41.5615]。不删负差/有效长值，不把这些值解释为纯marker/Nsight/等待成本。

P1−P0 Request相对差本批为+2.1013%～+106.6759%；Prefill +0.5514%～+107.0295%，Decode +3.8380%～+106.2806%。本批没有负profile差，历史批次的负值仍保留，不改规则。配对包含观测扰动、次序及运行波动；不从A统一扣除，不迁移P1精确组成到P0。

10ms Request/Prefill、5ms Decode精度候选未获统一支持：例如G1 P0 Request描述区间半宽13.8987ms，N1同步Request16.8518ms、Decode7.6019ms；部分量较窄也不能证明精度保证。六block是已完成预算，不追加到显著。留一/前后三块及所有原差完整报告，N1 P1 Request前后三方向反转尤其禁止稳定收益claim。

## 4. 信息增益：有限支持与负结果分开

**支持的是相对常规聚合指标的有限、自动可审计语义解释，不是工具不可替代性、广泛性能规律或加速。** 使用同一P1窗/clock/registry/记录范围的公平baseline；完整标准timeline及其流/context/correlation可用，结合相同CUDA语义可以手工恢复同样结论。不能说Nsight无法解释。driver独立activity层未采集，保持NOT_COLLECTED_UNKNOWN，不填0或宣称双层嵌套实物验证。

- **G1设备活动与等待：** 12个request实例中，G32 GPU union32.7489～39.8643ms、受支持wait0.009952～0.065535ms；G512 GPU union49.4517～60.5030ms、wait0.015104～0.072704ms。较长输入在六块均有更多activity，但wait差`[0.005248,−0.050431,−0.030719,0.016096,0.005696,0.024257]`ms，方向混合。独立必要后缀证明大部分工作不在这些同步阻塞区间内暴露；聚合GPU总量不能唯一恢复该归属。三phase全部实例见[36项信息案例](gate13_information_cases_v0_1.csv)，不是选最好看的trace；首尾镜像block1/4及其余全部Raw已核。
- **G1 API与Host：** 本批36个G1窗口API sum=union，没有观察到嵌套重复造成的额外解释；不能把一般反例当模型实证增益。相同窗T−API union可直接给出相同Host补集值，这一数值上baseline已足够，记录“未显示额外信息”。Host仍非CPU busy；不存在统一解释优势。
- **N1固定干预：** 六个实际干预W均2814成员，hidden union分别23.469255/32.744202/29.094255/24.383935/21.248018/30.811765ms；该sync exposed分别0.130335/0.762937/0.107807/0.107071/0.107231/0.107647ms，tail0.022170～0.061745ms。完整前缀、唯一terminal及独立FIFO核对说明“已先行完成的必要工作、局部暴露、返回尾”与raw sync持续时间不同。聚合sync成本不足以给出W归属；标准timeline+同语义手工可恢复，不声称独占解释能力。
- **N1数量级/性能：** Decode A wait的N16−Nm六块均正，与实际干预exposed对应；block2较大值照实保留。只称本六块P1局部观察，不推广自然G1或P0净收益。P0/P1总差波动及allocation差异不能由该单sync解释；稳定性能效应不受支持/数量级仍不确定。

因此不是“方法所有问题都有增益”：设备必要等待/单sync provenance有限支持；API嵌套和Host补集在本数据未显示非冗余增益；P0稳定收益及全输入域规律不支持。A守恒、unattributed=0仅是资格/记账事实，不替代上述判据。

## 5. 实际验证、保留项与唯一下一步

原ZIP流式全核验/展开115.036s；新e19逐run完整S/A/B+独立baseline+统计3319.893s。不同机器/完整度，不能以原7200s中断计算本批精确提速比例。逐run释放大对象，无全批S常驻cache；102对比均值/留一另行算术核对，Raw独立30/30，baseline各窗count/sum/union与Raw一致。

授权/载荷适配tests-first：13 failed红例后通过；本次收口实际命令`python -X utf8 -m pytest -q -p no:cacheprovider tests/test_gate13_offline_binding.py --basetemp=.local/diagnostics/gate13_complete_v0_1/test_closeout --junitxml=.local/diagnostics/gate13_complete_v0_1/binding_closeout.xml`，13 passed、0 failed、0 skipped，0.23s；该模块compileall/diff通过。此前纯性能36项及历史实物等值回执复用，未重跑Q0/全量/实验。辅助审计初稿误读tree_hashes结构/大小写摘要及扩大Raw局部前缀的读法已修正，保留失败审计，未修改测量或追绿生产规则。不是目标机新测试。

ARS 11/11检查：条件/pass/block分层防Simpson；不由该运行序列推平台总体（生态）；支持域选择透明（Berkson）；不按结果筛选/控制碰撞变量（collider）；无诊断概率基率claim；非极值选样/追采（均值回归）；60全部保留（幸存者）；102预定对比全报（多处寻找）；冻结顺序/统计未改（分析分叉）；P1不迁移P0/局部sync不等因果净增量（相关因果）；时间关系证据不等全部混杂排除（反向因果）。小样本、共享平台/顺序漂移及扰动仍限制统计解释；不新增显著性测试。

唯一下一步是**复制已存在的外部终态回执到本地**，无须操作模型/collector、部署、重采、追索PID或重算。核对其预定hash、成功终态、ZIP/manifest/source_before绑定和归档后源复查；若不一致只报告具体差距，不修改原件。未取得前Gate13 BLOCKED，批次正式收口待决；已经通过的逐run/逐窗检查和有限信息结论保存，无新样本任务。原执行99f3bae、新分析e19、原签署和旧BLOCKED均分别记录。

本轮没有清理。Gate7～12限定PASS保持，Gate14不启动；[机器汇总](gate13_review_summary_v0_1.json)与[唯一进度](research_progress.md)一致。不授完整新版Q0、D/Signature、自然默认流B、Formal之外的平台/模型或Decision Gain。
