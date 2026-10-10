# ExposedPath 科研进度清单

## 7.125 Gate13修复执行锁与未签署补丁候选绑定（2026-10-10）

实现commit **99f3bae966f2fb794073ff4d7468233b6b8dd2ac**，parent **c443c105018606b6b7a7f9992c6ad574990e3e16**；本节/候选提交是后续文档身份，不代替执行/分析版本。[未签署补丁候选0.1.1](gate12_freeze_candidate_v0_1_1.json)协议内容SHA256 **d9204a80bf15ce810093ec53c506d4bf3eadd2f1ad71db8844cff330f0c7448b**；候选文件SHA256 **22c644a5e1bad12fea62f8fcf48f50b926df1f743bbbd6156a666710b93d8566**。126个Git blob锁/12个schema-registry引用逐项核验，无自引用。相对旧125锁，仅3个修复模块及2份此前已变更的状态说明文档不同；新增reference schema0.1.1。已只读对照两份旧文档差异，均为已完成实现、绑定/签署状态说明，不改变claim/输入/统计规则；候选透明记录，不静默当成零diff。

未签署候选及旧0.1 approval均在当前严格release门被拒绝。输入/软件/模型声明、warmup3/repeat1、五条件/六block/60进程/30profile及全部测量/资格限制与原payload逐字段一致；旧签署和实际字节seal不能覆盖新内容。原Gate12历史限定PASS保留，**补丁尚未签署；Gate13 BLOCKED、Gate14 NOT_RUN**。人类需要集中确认新精确内容hash/执行锁，才可生成新签署发布并审查新批交付；不是重新选择研究目标或扩预算。

唯一待审ZIP `gate13_99f3bae966f2_prepare_review.zip`：**89539 bytes / SHA256 71f817e9350f1d9367f4c393341558010ea28f5bcffec7dc97b2393d482fe953**；11文件/10清单、CRC/大小/hash/完整覆盖通过，清单SHA256 fdfa648dbf311e02129c77d35b74af765f2587add506b53bec62abbd29cc4838。增量bundle63889 bytes / a33d7393b1f50194d9343c8d10a7a69922c1aad23ed4e95bb1bdb0493dfe275e，prerequisite **e38fa91850b8f31e17cc0ee264987ef3c1313d7d**，verify/list-heads通过。包只含unsigned候选、bundle、验证/源码索引及原封存输入参考，没有signed release、有效approval或采集脚本，不能部署或执行。机器路径只保存在忽略的本地索引，原失败包未改；本地构建不冒称服务器动作。

复用7.124最终150 passed/0 failed/0 skipped（67.07s），不重跑已完成检查；本次只检查候选字节/source锁/版本兼容拒绝、交付清单、公开内容/链接/diff及DOCX保全。最高优先级仅协调窗口审查补丁与集中重新签署，不执行旧阶段B、不续采/替补、不清理证据。

## 7.124 Gate13首槽prepare失败审查与最小接线修复（2026-10-10）

**原批次BLOCKED，Gate13 BLOCKED；没有模型进程或测量样本。** [集中审查](gate13_prepare_repair_v0_1.md)直接核验封存失败包172716 bytes/SHA256 `5279780d660f97668e3d7d73dde584a84a7d6ac5bc5524156656cac0a9b0faa0`，39文件/38清单/完整覆盖/CRC/全部大小hash通过，清单`86aa6761a9e58eaaa7055726c1f6f28a8e375fe521e6e0b935277addb344ad49`。首槽b1/G32/P0 prepare报FORMAL_INPUT_HASH、其余59槽位NOT_RUN；包内只有prepared输入/模型清单副本，无manifest/producer/REP/SQLite。源码与控制器证明模型/collector尚未启动；prepare已做最小CUDA身份查询，不称零CUDA交互。原报告中的Gate13 NOT_RUN字段不改，当前汇总裁决记录BLOCKED。

实际冻结期望为signed protocol.input_hashes.G32=`4dffd0ddcbd3185c656ae4a27efaf5aab302febba6ead5df4d37d903a2091920`；原输入和copied prompt均2893 bytes/同SHA256。create_manifest未填prompt_tokens_sha256，formal.validate先于finalize，故实际比较对象是字段缺失的None，不是不同输入hash或token内容digest/LF-CRLF问题。封存输入＋原签署＋125原Git内容锁的CPU回放复现None/WMPC=null；只调整顺序后实际copied bytes重算一致。外部设备/解释器/软件/模型是明确CPU替身，未授目标机验证或旧协议对修复源码的执行权。

tests-first红例16 failed/3 passed，最小finalize→原严格Formal validate修复后19 passed。补丁`G12-ROUTEA/0.1.1`新增独立formal reference schema，不改旧0.1；新版本仍要求独立content approval及新schema锁。实际producer暴露reference装配硬编码0.1，已闭集oneOf接线，并由跨记录exact binding继续拒绝混版本/未知版本。无期望复制、输入归一化、宽泛fallback或角色升级。

最终实际命令：`python -X utf8 -m pytest -q -p no:cacheprovider tests/test_gate13_prepare_identity.py tests/test_gate12_formal.py tests/test_gate13_delivery.py tests/test_gate11_pilot.py tests/test_gate8_diagnostic_entry.py --tb=short --basetemp=.local/diagnostics/gate13_prepare_final_v3 --junitxml=.local/diagnostics/gate13_prepare_final_v3.xml`，**150 passed/0 failed/0 skipped，67.07s**。五条件×两pass×新旧版本实际prepare/校验/verified替身/producer文件链、三次暖机/新测量流、错输入/副本/role/variant/hash/config/commit/版本拒绝全部包含。首次绿测旧替身只有两条流/误读ledger字段；按真实w3文件合同扩充替身后通过，未改生产流规则。新增34项不是CUDA、目标机、新Q0或Formal结果。

受影响Python compileall、schema校验、diff与代码自审通过；runner/MC/S/A/B/原0.1 schema/registry/Q0零diff，用户DOCX原hash保持且不纳提交。先提交实现，再按真实commit绑定补丁候选126个源码锁（含新schema），避免自引用；新候选待重新签署，旧approval和seal不可沿用。Gate12旧0.1历史限定PASS不撤销；新版本待确认，Gate7～11保持。最高优先级是审查新精确候选/单待审包，不部署、不采集、不恢复旧目录或自动替补。本轮无服务器、真实模型/CUDA/Nsight、完整Q0/全量测试或数据删除。7.123及旧显式阶段B指令现为历史，不执行。

## 7.123 Gate13阶段A原始静态回执审查（2026-10-09）

**阶段A回执审查通过；Gate13仍NOT_RUN，尚无Formal采集。** 本地直接读取用户服务器回传`gate13_e38fa91850b8_static.zip`：51983 bytes，SHA256 `ef05a58b85fcc1721b5616d9dd491ea7d673777f653478d5db28fae756fb1d6d`；清单hash `b56e1744e5e74096f20fb0c95487b304b9e5dcc5a2627f63d870a441e6970802`。15文件/14清单完整覆盖、大小/hash、CRC及安全路径通过；原件未解包改写。用户执行服务器部署和CPU检查，本助手只审计，未重跑224/23项、Q0、实验或目标机命令。

四份原始exit回执均0；bundle/fetch/checkout/CPU日志与transcript一致。实际checkout为e38fa91850b8f31e17cc0ee264987ef3c1313d7d，CPU真实Git状态检查和脚本末次Tree门通过，最终clean。125项实际源码hash/length均匹配签署锁及显式表示（55 LF、70 CRLF），不是仅引用本地测试；签署、delivery配置和执行脚本逐字节匹配原交付包，输入/model清单绑定一致。执行脚本SHA256 `26b88cada4be7537fe6bfb4300fe29476d978fe11304be91157c9dce4c6d6472`。控制层仍c5fcb77，后续记录提交不替代执行/分析身份。

CPU回执DELIVERY_CPU_PASS：计划60进程/30对，model_executed=false、cuda_initialized=false、collector_executed=false；核对实际默认分支/导入与四步命令，没有模型执行、CUDA初始化或collector调用。Git正常stderr被PowerShell呈现NativeCommandError，不据此认定失败：原始exit0、成功消息及后续严格检查均成立。保持UNKNOWN/NOT_ASSESSED、原数据角色和签署语义；不重新包装或改现有协议。唯一下一步是用户经协调审查后显式阶段B，固定六block/60新进程/30profile、90GB空间门与既有停止规则；收集完成后再本地审查，不自动Gate13 PASS。

## 7.122 Gate12限定签署、收尾及Gate13待审交付（2026-10-09）

**Gate12 PASS，限于`G12-ROUTEA/0.1`未来限定Formal；Gate13/14 NOT_RUN。** 用户当前明确接受有限P0性能/P1机制、限定Formal适用和六block预算，授权记录签署。[签署发布](gate12_protocol_signed_v0_1.json)/[唯一收尾](gate12_closeout_v0_1.md)于`2026-10-09T13:21:15Z`生效，批准ID USER-20261009-G12-ROUTEA-01；助手记录人类授权，不冒称密码学签名。原未签署候选/旧角色/Raw/BLOCKED报告保留，不追认旧数据。payload内FREEZE_CANDIDATE是封套固定内容字段，实际生效状态由外层SIGNED及approval hash决定。

执行/分析固定 **e38fa91850b8f31e17cc0ee264987ef3c1313d7d**；协议内容hash **389a28a17bec830e4f32bea72c259dce15ba279ce69fc20caebfdca88a1326e2**，签署发布文件hash **472f0ecabad15df11686676cc1ebfa5a6208a4c2ccc9f5e00e847320b70916cc**。本轮复核125个Git内容锁/11版本/限定资格/无自引用，复用7.120最终224 passed及既有实验记录，不重跑。文档/外部交付控制层提交不替代执行身份；当前DOCX字节保持、不纳提交。

冻结五条件/w3/repeat1/六完整block，60新模型进程/30profile，预定组序/对照/whole-block统计、公平同窗baseline和负结果口径。P0性能/P1机制分开，不扣A/跨sync加总/精确迁移，10/5ms不保证。G1投影A、N1合格单sync B/RAW_PHYSICAL/opaque内部等待不拆、UNKNOWN/NOT_ASSESSED及D禁用保持，不授完整新版Q0或信息增益。实质变更须新签署版本并标明受影响Formal失效。

[Gate13交付与保留](gate13_delivery_v0_1.md)复用固定实现，外部控制层只接通60槽位/30pair、实际身份/配对/同窗baseline和统计文件入口；不改runner/completion/流/同步/S/A/B。默认部署必要CPU、协调审查后用户独立显式采集，前置470c5afa，单包/每阶段单ZIP。硬失败/预算完成即停，无retry/resume/替补。200–240min/42.1GB/90GB仅模型链历史粗估，新增CPU复核、封包/传输另计；纯CPU baseline900s/整批统计7200s为操作界限，不扩模型预算。准确清理清单仅在批次审查＋完整归档核验后生成，逐文件LiteralPath及清理回执；当前不清理任何现有产物，不预造未来名单。

新交付控制层tests-first红例后最小实现；本次最终实际命令`python -m pytest -q -p no:cacheprovider tests/test_gate13_delivery.py --basetemp=.local/diagnostics/gate13_delivery_final4 --junitxml=.local/diagnostics/gate13_delivery.xml`，**23 passed/0 failed/0 skipped，20.71s**，mask=-1。包含实际G1/N1 producer文件配对、60槽位/失败停止、真实部署CPU入口、归档与nested清单、PS5.1 dry/delete/变档拒绝；全为CPU替身或临时测试文件，不冒称CUDA/目标机/Formal验证。代码审查发现清理根/祖先junction漏查，独立临时文件反例先失败，修复为初验及每次删除前逐级核查叶/根/全部祖先，最终回归与只读复审通过，不删除研究数据。新增三Python compileall、WindowsPS5.1.26100.9444语法、签署/source/196链接/公开隐私/用户DOCX及diff检查通过；runner/MC/S/A/B/schema零diff。首次CPU fixture模板/实际release区别、包内helper缺失和Python→PS5.1模块路径故障均先拒绝，按实际文件绑定及显式内置module最小对齐，不改生产身份门。包的固定身份与本机私有路径在忽略的交付索引，正常bundle verify/全包核验后交协调窗口。本轮无服务器、模型、CUDA/Nsight或新实验，Gate7～11限定PASS保持。下方7.121及更早待签署/预算均为历史，不重复执行。

## 7.121 Gate12实现commit与未签署冻结候选绑定（2026-10-09）

补充交付校核：候选初稿生成器采用Windows CRLF，暂存检查报行尾空白；格式化为UTF-8无BOM/LF并更新全部文件hash引用，协议规范化内容hash不变。初稿候选文档提交6ee660a仅为未签署历史，最终文件身份以下述LF版本为准；未改变执行实现e38fa91、JSON值或任何数据资格。最终推送前按整体差异重新校验，不把初稿失败写成检查通过。

**Gate12 NOT_RUN；本地实现/验证和候选绑定已完成，未签署、未授权Formal预算或执行。** [候选记录0.1](gate12_freeze_candidate_v0_1.json)绑定执行及分析commit **e38fa91850b8f31e17cc0ee264987ef3c1313d7d**（parent3619f46f2a198a36ccc3fbe983e5fb59b49c98d2）；本次候选/入口文档提交不是执行commit。封套`G12-FORMAL-ENVELOPE/0.1`、协议`G12-ROUTEA/0.1`；125个源码/合同/资格引用取该commit的Git内容SHA256，包含同窗baseline/统计与相关schema/registry。候选自身不进入artifact锁，避免自引用；运行时实际字节仍另seal，只允许显式LF/CRLF表示等价，不能用当前任意hash放行。

协议规范化内容hash **389a28a17bec830e4f32bea72c259dce15ba279ce69fc20caebfdca88a1326e2**；候选文件hash **78cff3228d00b8410a42d51930df4556121eaf879eb95b430c9365ac8788e761**。候选`PENDING_USER_SIGNATURE`、approval=null、budget=NOT_APPROVED；没有生成SIGNED回执或部署/采集任务。人类批准须关联完整候选及协议内容hash，程序验证不代替作者/授权证明。

只消费已审查共同w3包内G32/G512两个小manifest，按公开source索引复核大小/hash，绑定既有输入/model inventory/GPU/软件栈；不是重新核当前服务器状态或升级Pilot。G32输入hash4dffd0dd…、G51236c507c5…；model inventory72465c90…，固定既有Windows/4090、physical3/logical0、torch2.6.0+cu124/CUDA12.4/Python3.11.16/Nsight2026.2.1.210。完整值与原件引用在候选中。用户DOCX的本地hash仅为审阅来源，不把未提交DOCX当作服务器源码artifact或覆盖文件。

复用7.120最终CPU回归224 passed/0 failed/0 skipped、compileall及代码审查，不重复测试/实验。候选检查125个Git源码hash、11项schema/registry、规范化协议/候选文件hash、无自引用及未签署执行前拒绝全部通过；178个相对文件链接、4份SVG XML、隐私/用户DOCX及diff检查通过。生成草稿时索引结构/不存在路径检查先拒绝，按实际来源修正后绑定，未绕过hash或提交临时生成器。S/A/B公式、边界、流/同步和既有资格不变，不授完整新版Q0。

**唯一集中待确认：接受有限P0性能/P1观测机制及公平“不支持/不确定”结果、限定资格用于未来Formal，并批准五条件共同w3/repeat1的6完整block（60进程/30profile，估计200～240min、42.1GB原件/90GB空间），签署上述完整候选。** 不承诺10/5ms、精确P1→P0组成或细微稳定收益；签署与之后服务器执行授权分开。Gate7～11限定PASS、UNKNOWN/NOT_ASSESSED、opaque/N1单sync B/G1只A及旧Raw/报告保持；现在无需服务器操作。

## 7.120 Gate12冻结前本地封套、baseline与成块统计收口（2026-10-09）

**Gate12 NOT_RUN；本地实现与相关CPU验证已完成，候选绑定、限定Formal适用/预算确认及签署仍待完成。** 用户批准的是冻结前实现，不是协议签署或采集授权。当前入口仍为[科学适用性审查0.1](gate12_scientific_readiness_review_v0_1.md)与[冻结草案0.1](gate12_protocol_freeze_draft_v0_1.md)。7.119“仅Engineering/Pilot实现”为历史描述；旧数据和原报告不升级。

显式`G12-FORMAL-ENVELOPE/0.1`贯通外部人类批准回执、manifest、producer、ledger/NVTX、sealed preflight、receipt、Canonical与限定domain/报告；未签署、错hash/角色/身份/配置/输入、过期或旧角色升级均拒绝。代码不签署回执，也不证明批准者身份，必须独立保存用户对完整候选hash的批准。复用runner与N1包装，未修改host-readable completion、流/同步、S的W/terminal或A/B公式。旧Pilot局部导入遮蔽最小修为显式别名，保留旧分派和反例，不修改测试追绿。

新增同P1窗口/clock/ownership/registry的baseline文件入口：count、裁剪sum、union、同步/非同步、GPU活动和合法映射时序；driver缺表/字段为UNKNOWN，不补零。新增完整60run文件索引、逐值token配对、signed差、完整block联合bootstrap/留一及顺序敏感性、原值/图表及逐sync B来源；不拼接partial、不扣A或累加B。独立手算API sum26/union18、kernel sum16/union14及signed差−2；实际文件链使用合成批准/设备/模型替身，不冒称目标机、CUDA、新Q0或Formal验证。

本次实际命令：`python -m pytest -q -p no:cacheprovider tests/test_gate12_formal.py tests/test_gate12_baseline.py tests/test_gate12_statistics.py tests/test_gate11_pilot.py tests/test_gate11_pilot_files.py tests/test_gate11_warmup_pair.py tests/test_n1_model_domain.py tests/test_runner_token_ready.py tests/test_n1_preprofile_identity.py --tb=short --basetemp=.local/diagnostics/gate12_resume_20261009/tmp --junitxml=.local/diagnostics/gate12_resume_20261009/related.xml`，**224 passed，0 failed，0 skipped，336.25s**，CUDA mask=−1。此前151 passed/73 failed不是最终结果；本次首个默认temp运行49 passed/175 setup errors源于旧临时目录ACL，使用全新仓库内temp后得到最终结果，未削弱测试。`python -m compileall -q exposedpath analysis exposedpath_v141 scripts`及`git diff --check`通过；未跑无关全量、完整Q0或实验。

先提交实现，再绑定真实执行/分析commit、Git内容hash、schema/registry与限定资格复用，避免自引用；文档commit不冒充执行身份。P0性能/P1观测机制分开、公平baseline允许“不支持/不确定”；六block只为预算/有限次序平衡，10/5ms不保证。UNKNOWN/NOT_ASSESSED、G1只A/N1单sync B、opaque内部等待未拆及D禁用保持。DOCX原修改保留不纳提交；Gate7～11限定PASS保持。无服务器、模型、CUDA/Nsight、追加Pilot或默认Formal任务。本节覆盖下方7.119及当前阶段/优先级中尚未实现的历史描述。

## 7.119 Gate12本地科学适用性审查与冻结草案（2026-10-02）

**Gate11限定Pilot政策PASS保持；Gate12 NOT_RUN，已开始本地准备但未冻结，Gate13/14未启动。** 当前只保留[科学适用性审查0.1](gate12_scientific_readiness_review_v0_1.md)和[协议冻结草案0.1](gate12_protocol_freeze_draft_v0_1.md)两个新入口，7.118实物/政策依据继续有效；没有服务器、CUDA/Nsight/模型/追加Pilot或Formal任务。用户研究设计DOCX修改保留，不覆盖、不纳提交。

读当前研究设计v7.1/Pre-Pilot协议v2.1及已批准路线A/分域/opaque合同，固定G1两输入端点的解释信息问题和N1 marker/同步两个必要对照。公平baseline同P1目标窗/clock/输入/registry，包含常规聚合与timeline，不通过少给字段制造优势；明确正确性、机制事实、信息增益、性能收益四层及“不支持/不确定”。G1只有32/512、输出2，不能提出输入响应图谱/长decode或默认流完整B；N1不将单sync hidden加总或迁移到自然G1，D/Signature禁用。

复用共同w3汇总和原值，未重扫全包/重跑analyzer/Q0/测试。消费两个已有来源hash绑定的小manifest，复算G1同block差、A分量与单sync B自身波动。G1 P0 Request差13.4596/19.9525/14.0855ms，SD3.5817ms；N1两项P0 Request差SD101.3507/85.0782ms。六block只由有限成本/原三序加镜像、pass先后与位置平均平衡支持，不是完整Latin-square/随机化或10/5ms保证；候选精度未获支持就如实保留，不另设效应/等价带、不追采到显著。

**集中待确认：是否接受P0性能与P1机制并列、撤去精确P1→P0组成/细微稳定收益claim，以五条件共同w3/repeat1、6完整block开展未来有限Formal？** 推荐接受这一有限信息增益检验，公平baseline可能已足够且允许负结果；若自然P0精确组成/5ms收益为最低目标，本设计不足，不能用“允许不确定”伪装达标。明确列出原DOCX5/10%overhead、dropped=0/重跑等政策与批准窄路线的拟覆盖，当前只草案、不静默改正文或历史资格。

实际代码仍Engineering/Pilot-only（roles/Canonical gate8_sources及报告false）；冻结前确有最小Formal封套接线及同窗baseline/成块统计CPU复算、最终实现commit/源码/registry/schema/hash与有限资格签字绑定缺口。旧数据不能仅改role升级；不重写S/A/B或恢复完整新版Q0，变化影响增量而非机械重采。假设/UNKNOWN/NOT_ASSESSED、opaque内部等待未拆及native backend未知保持。未来60进程/30profile粗预算200～240min、42.1GB原件/90GB含审查，尚非授权或默认执行计划。

本轮只新增两份Markdown及同步入口；相关算术/原值、六block顺序预算、来源/隐私/链接/diff检查按本轮实际完成记录，不用历史测试冒充。首次数值自检误用四舍五入后的手录端点整数而停；改为源JSON原整数复核后通过，未修改源汇总/Raw/analyzer。Gate7～10限定PASS及N1独立Engineering PASS保持；下一项是上述一次集中范围确认，之后才最小本地角色/复算绑定，不要求服务器操作或交付包。

## 7.118 Gate11共同warmup3实物审查与限定Pilot政策收口（2026-10-02）

**Gate11 PASS：限定Pilot政策评估和Freeze输入准备完成，Gate12～14仍NOT_RUN。**[当前收尾0.1](gate11_policy_closeout_v0_1.md)、[机器汇总](gate11_w3_pair_summary_v0_1.json)及[30次原值](gate11_w3_pair_durations_v0_1.csv)为唯一当前入口；以下7.117及更早的待部署/待采集/BLOCKED状态均保留为历史，不重启旧指令。不是30/30即PASS或证明稳定性，而是同政策实际链/硬门成立、有限运行和质量政策、成本与claim收缩已一次记录；下一阶段还须确认政策并绑定Protocol Freeze，无本轮采集/执行授权。

执行身份470c5afa6400a77fb79692699cdd8cecc47b314d；新封存包653736655 bytes、SHA256 64F930679FAF7B2B55538E4381AB4A6A8B8652CFE8892BB21EBDFFBDC2A0884D，清单4EB0D72252D1754C1CC374CDD130A9686DEABA2BDA61CAB02FBEA5559A1ABADA。本地单次流式CRC/全大小hash/唯一安全路径及完整覆盖1746文件/1745清单通过；新独立诊断目录复用审计工具核30入口/15pair、90实际成功暖机、token逐值、跨run环境/源码、N1各pass干预/fresh流和窗外drain；保存669关键源引用。服务器此前CPU64 passed是原日志证据，不是本地重跑。

15profile只读SQLite/Raw→Canonical→completion投影和必要成员、dependency/ownership/terminal审查完成；45A独立API/区间并集预期、顶层/子类守恒、连续边界及Request=Prefill+Decode通过。N1完整30个合格单sync B含9个RAW_PHYSICAL内部、18个结构化token-ready、3个V16干预；不跨sync累加，G1只授自然投影A。60条同类warning按已接受官方规则处置，原记录保留；UNKNOWN/NOT_ASSESSED、opaque内部等待未拆及未知size、D/Signature禁用保持。unattributed全0是实物事实，不追设零门或信息增益结论。

每条件新政策仅3对，不与221f46c-w1或4abb5ea-P0对照混池/跨warmup配对。Request P1−P0相对差−36.030%～+61.908%，Nm b1有效长值和负差保留；共同w3多数分组SD变窄、N0 P1/Nm P0反向，不认定整体改善或收敛。三block探索性联合bootstrap/留出、所有phase/N1对照/差中差原值和A/B来源保留，不扣A、不作纯Nsight/marker/wait因果归因；10/5ms继续是未保证精度候选，不是效应/等价/质量阈值。

**政策收口：共同warmup3、repeat1/进程，建议正式6个完整平衡block（原三组序＋镜像），不是n6充分性或10/5ms功效证明。**P0性能/P1观测解释、全部有效原值/负差、whole-block分析、无可选停止或替补；硬性身份/边界/依赖/诊断门不变，局部可界定缺口保留unattributed及范围、不填Host，无法界定拒绝。不设回溯统一overhead%/zero-unknown门或任意clock tolerance。收缩精细稳定E2E收益/排名和精确P1→P0拆分迁移claim；未来固定预算后如不精确，报告不支持/不确定，不追采到显著。

实耗driver5992.207s≈99.87min、展开21.03GB，高于旧估计；未来6block仅粗预算60进程/30profile、200～240min、42.1GB原件/90GB含审查空间，非授权。累计Pilot90进程/30profile预算结束，无必要新Pilot/服务器任务。唯一下一项是Gate12本地协议确认及最终代码/registry/schema/analyzer/统计/绘图/排除与签字版本绑定；Pre-Pilot v2.1未冻结，不授Formal、完整新版Q0、信息增益或科学稳定性。

本轮只本地只读证据/描述性算术及政策文档、来源/算术/链接/diff检查，不重跑完整analyzer/Q0/仓库测试、不操作服务器/CUDA/Nsight/模型。原Raw/ZIP/报告和用户DOCX字节不改，DOCX不纳提交；执行commit与本次文档收尾commit分开。Gate7～9、Gate10限定G1选定点一次可行性及N1独立Engineering PASS保持。

## 7.117 Gate11共同warmup3追加预算、最小配对接线与待审交付（2026-10-01）

用户已批准[政策决策0.1](gate11_policy_decision_v0_1.md)中的唯一追加批次：五条件共同warmup3、原三个完整block、相邻P0/P1，30新模型进程/15profile，预计70～90min、预留35GB。仅本批授权，完成才累计90进程/30profile；不扩点位/暖机扫描/进程内多request，不自动retry/resume/替补或剩余批次。10/5ms继续是待审精度候选，不是效应、等价、分类或clock tolerance；3block bootstrap仅探索性，预算后一次决定政策/repeat/可支持claim，不追采到显著。

[G11-WARMUP3-PAIR/0.1](gate11_warmup3_pair_v0_1.md)及封闭binding schema区分未来新采用途，manifest→producer/ledger→input receipt→domain/pair/batch贯通。复用已有逐次暖机、verified入口、N1包装/marker/层16同步、held暖机流及fresh measured流；复用host-readable token窗外持久化，不增D2H/sync或改completion。旧首批/Engineering/P0对照读取保持，不改S/A/B公式、opaque或支持域/诊断门。

tests-first新增22项缺入口红例，并用实际producer/Canonical/域消费者文件链暴露首批消费者残留的单次warmup限制；最小按显式新binding消费ledger0.3/producer0.2、实际3次及未知暖机token/EOS，测量实际token/边界/依赖要求不变。已接固定30槽位/15pair、失败partial/NOT_RUN、阶段可见输出、默认部署CPU/显式采集分离。本地模型/设备/Raw替身不授目标机验证，新批尚未执行。

本地验证：`python -X utf8 -m pytest -q -p no:cacheprovider`的10个受影响文件**238 passed（265.01s）**；补充真实采集前新binding→seal/target claim→profile argv边界和CLI版本拒绝后，新增批次文件最终**40 passed（73.93s）**。旧首批/P0对照/Engineering和opaque/支持域反例均包含相关回归，未跑全量或完整Q0。改动Python compileall、PowerShell5.1 parser/封闭dispatch实际函数、158相对链接/schema/预算算术、公开隐私及diff检查通过。手工审查版本分派、原公式/必要集合/诊断零diff、无额外token读取/同步、N1未知暖机/fresh流及失败停止；保留旧launcher输出路径。用户DOCX原SHA256保持，不纳提交；无服务器/GPU/Nsight/模型执行。

服务器前置4abb5ea，固定commit和单一增量部署ZIP/字节清单及整段命令由本地交付身份钉住；先交协调窗口审查静态回执，再显式启动唯一批次，最终单ZIP含原静态副本及全部执行/入口异常/producer/Raw/分析/配对与未执行。机器绝对路径/hash放忽略的本地交接，不进入公共文档。旧Raw/ZIP/报告、未知状态及用户DOCX不改、不纳无关提交。

**Gate11 BLOCKED；Gate12～14 NOT_RUN。** 当前最高优先级是协调审查本批固定交付和未来目标机CPU复验；没有本轮服务器/模型/CUDA/Nsight操作，预算授权不等于测量成功或Protocol Freeze。Gate7～9、Gate10限定G1及N1独立Engineering PASS保持。采完仅STOP_FOR_REVIEW；所有有效值/负差/必要对照保留，P0性能/P1观测解释不扣A，政策不足优先缩claim。7.116及以下为历史提案/证据，不重启旧指令。

## 7.116 Gate11补证前解释尺度、预算与收口政策收敛（2026-10-01）

按用户本轮限定完成[政策/预算决策0.1](gate11_policy_decision_v0_1.md)；直接复用7.113/7.115两个审查及其机器汇总，不重扫证据包、重算analyzer或重跑测试。窄核作者原始资料：Kalibera/Jones技术报告§2.2/4/6/7、Hoefler/Belli作者摘要/书目信息；文献支持不确定性、变异层级和成本约束，**没有通用repeat/warmup常数或repeat6充分依据**。完整语义/质量门、UNKNOWN/NOT_ASSESSED与用户DOCX保持。

精简决策表分开Request/Prefill、单步Decode、N1同pass/block差值、P1 A/单sync B与P1−P0扰动；提出绝对解释精度候选h（Request/Prefill与N1总差10ms、Decode5ms），不是已冻结门、效应/等价阈值或仪器误差界。n=3/6/12与SD/√n成本敏感性明确只供预算，不当CI/功效保证，不按显著性、差值符号或波动归零选规则。预算不足先收缩精细性能排名、稳定收益或P1→P0精确迁移claim，保留有证据的观测机制解释。

唯一补证方案仍为五条件共同warmup3、三个原组序完整block、相邻P0/P1，**额外30模型进程/15profile**，预计70～90min、规划15GB/35GB空间；若完整执行累计Pilot90进程/30profile。原60已耗尽，本轮只是政策/预算审查，**追加预算未批准，未实现/打包/执行**。固定输入/backend/completion/drain、N1 held暖机流/fresh measured流及身份/质量门不变，不增加暖机扫描、点位或进程内多request（仅未来可选优化）。新批每条件n=3，不跨warmup/批次配对混池；候选正式n=6/12不是续采授权。

预先记录一次集中裁决：所有原值/负差/必要对照保留，P0性能/P1观测解释且不扣A；完整block重采样的探索性95%percentile区间候选与逐block/留出敏感性并报，不用小样本区间保证覆盖率。噪声/精度不足限制claim，不放宽硬门、不补到显著。预算完成或硬失败停，无retry/替补/自动加采；收缩后仍缺必要依据才具体保留BLOCKED，不增加无限稳定性前置。

**Gate11 BLOCKED，Gate12～14 NOT_RUN；当前最高优先级仅审查该政策候选及额外预算。** 用户批准预算后才完成固定版本/单部署ZIP/准确路径与整段命令/单ZIP回传并交协调审查；现在无需服务器操作。Gate7～9、Gate10限定G1及N1独立Engineering PASS不变，不授信息增益/Formal或升级旧数据。原ZIP/Raw/报告和历史判定不改，本次纯文档政策建议不修改冻结测量语义。

本轮检查：150个相对文件链接、表内SE/成本/组序与累计预算算术、状态/政策限制、新公开文件私有内容及diff检查通过；用户研究设计DOCX原SHA256保持且不纳提交。仅四份公共文档与忽略的根handoff更新；无业务代码/schema/测试/Raw变更、无服务器或CUDA/Nsight操作。

## 7.115 Gate11 warmup对照与首批Pilot集中政策审查（2026-10-01）

直接消费执行`4abb5ea1f1bf08f1883f1d1e471900087b4c5504`的新Pass0 warmup对照包：[集中审查0.1](gate11_warmup_policy_review_v0_1.md)、[机器汇总](gate11_warmup_policy_summary_v0_1.json)、[15对原值CSV](gate11_warmup_pair_durations_v0_1.csv)。ZIP 2607212 bytes / SHA256 `86272acd630d9878347a8c4c430d6b914d5498f58fca3a4d7f750eee621e02ff`，清单`fac1d56c28cd5e65449fd9a2cd466a9f21b597eb1ebd749daf17c1b9c2735fe5`独立核对；1383项全hash/CRC/静态副本复用协调窗口已核验事实。本窗口核实际消费338关键文件大小/hash/引用及独立host边界/stage整数算术，未重扫全包/重跑analyzer。服务器静态原日志65 passed/75.36s，不称本地重跑。

30新P0/15对/60实际暖机及固定次序、实际输入/输出token、三窗口/窗外drain和N1实际干预/held暖机流/fresh measured流吻合；暖机token/EOS仍null，Pass0不伪造物理A/B。15对w3−w1完整保留signed R/P/D与block/先后序：Request12负/3正，−149.736～+20.014ms；G32/N0三block Request/Prefill同向变短，其余有反转，Decode不一致。第2/3暖机远短于第1次，N0/Nm第2→3仍三次下降，不证明完全收敛。driver累计1298.577s/21.64min，不是request性能。

联合复用7.113首批15对/45A/30N1 B及已完成独立Raw核验，不重算；不同批次/版本不混成重复，不配新P0-w3与旧P1-w1。**建议未来共同warmup3作为有界政策候选，非已冻结或充分稳定；repeat候选6完整平衡block仅预算/组序理由，最终次数与绝对精度仍PENDING。**明确P0性能/P1观测执行解释、signed差/不扣A、run/block统计单位、硬性身份/边界/依赖/诊断门、局部缺口保留和opaque/B限制已有依据；数值扰动/coverage/局部缺口/时间解释政策及最终签字版本未定。没有按当前unknown=0冻结零阈值，也不增加“绝对稳定/全capture认证”前置。

**Gate11 BLOCKED；原60进程预算已耗尽，Freeze未启动。**唯一下一项建议是集中决定warmup3候选及一次同政策新相邻P0/P1桥接预算：五条件/3完整block、额外30进程/15profile，预计70～90min、规划15GB原件/35GB空间；仅提案，不实现/执行/打新包。回答新profile政策及variant/phase波动，固定批次/硬失败停；仍未定则收缩claim/保留不确定，不自动加采或追求显著性。现在无服务器操作任务。

本轮只本地证据算术、政策/文档整理；原STOP_FOR_REVIEW/BLOCKED、Raw/ZIP、UNKNOWN/NOT_ASSESSED及用户DOCX字节保持。Gate7～9、Gate10选定G1与N1独立Engineering PASS保持，不授信息增益/完整新版Q0/Formal。计划调整只记录候选/待决预算，不改冻结测量语义或历史证据。7.114“尚未部署/执行”及7.113“下一步warmup对照”等属于历史，不再作为执行指令。

完成本地15配对/30 measured/60 warmup整数算术与CSV/JSON引用一致性、338源hash索引、151相对文件链接、新增公开内容私有信息及diff检查；代码/schema/测试zero diff，无测试重跑。根目录本地handoff同步，用户DOCX保持原hash且不纳提交。

## 7.114 Gate11 Pass0 warmup1/3最小本地接线与待审交付（2026-10-01）

用户批准原计划唯一warmup方向的本地实现/准备：[G11-WARMUP-CONTROL/0.1](gate11_warmup_control_v0_1.md)及[封闭schema](contracts/gate11/warmup_control_schema_v0_1.json)。五条件/三个原组序block，b+j偶数1→3、奇数3→1，两个新Pass0相邻；30新模型进程/0新profile，用完原60预算。不取旧P0代替，不同时加profile block，不自动重试/替补/续批；本轮没有服务器/模型/CUDA/Nsight执行授权。

复用原verified入口及身份/输入/设备/preflight，实际逐次暖机、独立身份和开始/结束/成功/顺序记录。pass ledger0.3、producer0.2、execution0.2、diagnostic0.2、N1 execution0.2/calls0.2明确区分新批；旧Engineering/首批版本和读取保持。暖机未读取的token/EOS保持null，N1暖机observed_tokens=null；不拿目标长度冒充实测，不增D2H或计时sync。原measured completion/drain、N1包装/marker/V16同步、每次held暖机流及fresh measured流不改，原值窗外持久化逐值核对。S/A/B/opaque/资格与UNKNOWN/NOT_ASSESSED不变，无新增A/B或D/Signature分析。

tests-first记录13项缺入口红例；实际producer→文件→配对补充揭示次数变量混用，已最小修复。相关CPU真实prepare/verified producer/token/ledger/stage/预检到直接Pass0启动边界、配对和固定预算反例覆盖五条件1/3次、实际顺序、错角色/身份/variant/输出、缺文件、partial和立即停止；模型/设备均CPU替身，不冒充目标机验证。最终九文件**187 passed（125.13s）**，包含旧首批/Engineering相关读取回归；改动Python compileall、PowerShell5.1 parser和diff检查通过。无全量、完整Q0、旧首批重算或新实验。一次检查误拼不存在的测试文件，未执行任何测试，已更正，不隐去该事实。用户DOCX保持，不覆盖或纳提交。

交付前置服务器`221f46c3f97749396653f16f61b01eb6c6aeeafc`，一个增量bundle/部署ZIP；默认仅部署/相关CPU(mask=-1)，协调审查静态回执后才可显式执行新目录30-run。每阶段单ZIP，最终包保留原静态副本及全部入口异常/退出、实际逐次warmup/token/流/干预和计划/未执行。包SHA/私有路径放本地交接；源码严格核预先固定Git LF/CRLF表示，不依当前字节更新期望。估计25～35min、预留0.5GB，非保证；300s P0/900s driver有界超时不扩大。

**Gate11继续BLOCKED，Freeze未启动。** 审查预先保留signed w3−w1三窗口差、逐warmup时长和block/次序；一致改变只支持讨论政策，不证明warmup3充分，小样本零差不证明等价。方向冲突/顺序混杂/不足则PENDING，不任设阈值；本批不能解释Nsight开销，不能配P0-w3与旧P1-w1。repeat/精度/质量政策仍待集中审查。下一项仅协调窗口审查固定包及未来部署CPU，采集尚未执行。Gate7～9、Gate10选定G1及N1独立Engineering PASS/旧报告/Raw保持；无Formal数据变化。7.113以下是历史证据/建议，不是当前未接线指令。

## 7.113 Gate11首批限定Pilot证据与政策审查（2026-10-01）

直接读取新采Pilot `gate11_221f46c3f977_pilot.zip`，执行commit `221f46c3f97749396653f16f61b01eb6c6aeeafc`。[首批审查0.1](gate11_first_batch_review_v0_1.md)、[机器汇总](gate11_first_batch_summary_v0_1.json)与[30次原值](gate11_first_batch_durations_v0_1.csv)关联包内证据。ZIP 337537738 bytes / SHA256 `85871ae289fcab1731b4e33a7f43e80d21b75b7a32bd5c0b98af3660927612ac`、清单 `cea36179a2b58491c77fa83392051aba981247b6d26379083fcbe2e4a7f6510a`独立核对；1745项完整hash/CRC/覆盖为协调窗口已核验的回传事实，本窗口只核实际消费的关键文件，不重复全包扫描。原件、Raw及`FIRST_BATCH_COMPLETE_STOP_FOR_REVIEW`/NOT_RUN报告保持。

30run/15pair/3block的Pilot角色、实际输入/配置/输出token、执行身份、组序、两pass边界/drain及N1实际干预一致。直接读取静态副本CPU63 passed/84.60s，不称本窗口测试。15profile的45A窗口均通过独立Raw/Canonical/投影、必要集合/归属及区间算术；N1 30个完整W/terminal/逐sync B_VALID，G1 18个A-only交集与依赖证据吻合；unattributed均0。9个N1 profile各3次opaque allocation保留实际差异及未知大小/内部等待未拆；60条同类外进程warning按既有官方依据处置，原诊断、UNKNOWN/NOT_ASSESSED、G1不主张默认流完整物理B及D/Signature禁用保持。没有完整新版Q0、模型科学有效性或Formal资格升级。

**首批可用于限定政策估计；Gate11 BLOCKED，而非30/30成功即PASS。** 每条件仅3对。Request配对相对差−18.109%～+101.142%，原值、阶段差、block/pass顺序、同pass N1对照与profile×variant描述性差异全部保留；不能截负差、删极值、统一从A扣除或归因纯Nsight/纯同步等待。warmup1未证明充分，不等于已发现不足；repeat/绝对精度、数值扰动/coverage/局部缺口政策及时间容差尚未定。支持域/边界/身份/依赖硬门、配对统计单位、有限workload与claim限制等Freeze输入有依据，但没有Protocol Freeze。

**唯一推荐下一方向：原计划的五条件各3对Pass0 warmup1/3对照，30进程、0新profile。** 先审查最小参数/逐stage接线与可判别问题，再由用户决定执行；本轮不实现或采集，不同时追加profile block，不自动使用预算。预计25～35min、约6.9MB线性参考、预留0.5GB（非保证）。固定批次/硬失败即停，无retry/替补；达到60上限仍不保证数值政策定案。若需改变profile warmup，旧P1-w1不能代替P1-w3，额外预算/claim另集中审查，不预授权。

本轮仅本地证据审查、描述性汇总与文档检查；30行CSV/JSON、15pair及N1同pass/差中差算术、45A/30N1同步汇总、143个相对链接、私有信息扫描和diff检查通过；用户DOCX字节hash保持。未运行服务器、模型、CUDA/Nsight/export、完整analyzer/Q0或仓库测试，无业务/schema/测量语义修改。Gate7～9、Gate10选定G1一次可行性及N1独立Engineering PASS保持；Gate12～14 NOT_RUN。用户DOCX修改保留，不纳提交。7.112以下为历史准备/交付状态，当前以本节及§1/§5为准。

## 7.112 Gate11限定Pilot角色、真实配对与首批本地交付（2026-09-30）

用户明确批准仅未来新采Pilot沿用已限定N1/G1支持域作repeat/warmup/观测开销/质量政策估计。[G11-LIMITED-PILOT/0.1](gate11_pilot_contract_v0_1.md)版本化适用声明已固化；旧Engineering和原BLOCKED不升级，UNKNOWN/NOT_ASSESSED及opaque/单sync B限制保持，无Formal或信息增益资格。测量公式、S/A/B恢复/分类和completion时点未修改。

本地实现：闭合Pilot声明贯通manifest、pass ledger0.2、实际NVTX角色、producer/执行/token/input receipt及Canonical/domain报告；旧Engineering版本仍按原门读取。接通G512和N1 Pass0，N1包装、预定marker、V16实际同步及专用流不随通用trace关闭而删除；token值复用原host-readable结果，在计时窗外保存并逐值比较，不增加D2H/sync。每pair核输入、实际配置/解释器/PID/设备、边界/drain/stage、实际N1干预及token，跨block核公共环境和输出一致性；非profile不可观测的physical S/B不伪造。

固定[原计划](gate10_workload_plan_v0_1.md#gate11-local-preparation)首批：G32/G512/N0/Nm/N16，3个已审查block、固定相邻pass顺序，30模型进程/15profile、每进程warmup1/repeat1。独立run/pair/block/variant/pass身份，失败停、partial/NOT_RUN保留，不resume/retry/替补；完整批次只STOP_FOR_REVIEW。60只是总体上限，没有实现或预授权剩余批次、warmup扩展或长驻多request。P1−P0只表示profile/观测差异＋运行波动，不是纯profiler成本；repeat/政策数值仍待Pilot。

tests-first依次复现角色路径缺失、G512/pass0冲突、预算/跨block漂移及进度入口缺失；新增CPU真实prepare→verified producer→receipt/token→Raw/Canonical/投影→原S/A/B→pair文件链和独立W/A预期，包含错角色/输入/token/variant/pass、身份/边界/drain/correlation/未知warning、partial与停止反例。**14个相关文件263 passed（202.42s）**；末轮补G512完整pair与token receipt来源错配反例，修复后**16项文件链/准入定向通过（52.98s，与263有重叠，不相加）**。不是目标机CUDA/Pilot验收。一次测试命令误拼文件名、未执行任何测试，修正后上述整组通过；未隐去失败。改动Python compileall、PowerShell5.1语法及diff检查通过；未跑全量、Q0、旧trace重算、服务器/模型/CUDA/Nsight。自行差异审查未改变核心S/A/B文件，DOCX哈希保持用户版本且不纳提交。

交付前置固定服务器d25b4d1；一个增量bundle/部署ZIP，固定源码LF/CRLF候选字节和输入hash，不以当前字节更新期望。`run_gate11_pilot.ps1`默认部署＋相关CPU（mask=-1），采集默认不启动；协调审查静态回执后显式开关才启动新目录首批。包/机器路径与hash放忽略的本地交接，公共合同不含私有路径。每阶段单ZIP，最终含静态原件；疑似活跃后代停止封包。35GB磁盘要求、阶段输出和20秒状态提示保留原日志字节与既有超时。

**Gate11 NOT_RUN；EP-G11-01代表集及EP-G11-02本地接线完成不等于Pilot政策完成，EP-G11-03未采集、EP-G11-04数值输入未定。** Gate7～9、Gate10限定G1一次Engineering、N1三组独立Engineering PASS保持。没有新增研究语义待决；唯一下一步是协调窗口审查固定交付，再由用户决定部署CPU步骤和后续真实首批。本轮不执行服务器，无Protocol Freeze或Formal数据受影响。

## 7.111 Gate10范围澄清与Gate11最小本地准备（2026-09-30）

用户确认：**Gate10 PASS仅指固定平台、模型与执行配置下，选定G1候选点的一次Engineering可行性检查通过。** 32/2、128/2、512/2的真实执行、token、边界、支持域与A证据及其历史执行/分析版本不变；不是完整可行域、统计稳定域或容量边界。OOM边界、最大输入/输出/batch均未探索，512和2不是上限，也不外推其他配置。原EP-G10-01～03的广域/容量/共同稳定范围子项保留为未执行、后移，不勾成完成；当前claim不涉及容量极限，不为Gate编号故意跑OOM。以后明确研究长上下文/长decode/更大batch/容量时才另拟对应有界增量。N1三组32/2独立Engineering可行性PASS不替代OOM探索；不重开已通过的检查或改写失败报告。

在[既有workload计划中补充G11-PILOT-PREP/0.1](gate10_workload_plan_v0_1.md#gate11-local-preparation)，不另起重复流程：代表集G1自然32/2与512/2、N1显式流32/2 V0/Vmarker/V16，按输入轴/marker与同步问题选取，不按A效果。128只复用可行性，不进入首批。首批3个有序block、每条件相邻P0/P1各一次（warmup1/repeat1），共30进程/15trace、主配对n=3；总上限60进程/30trace。剩余预算只选再3个配对block或5条件各3个warmup1/3的P0对照，不自动加采、不因显著性补点。首批预计1.5–2小时、约11GB（规划15GB）数据/0.3–0.5GB ZIP，预留35GB含审查副本；上限3–4小时、规划30GB/0.6–1GB ZIP、预留70GB。仅从既有小报告和ZIP目录大小估预算，无重算/哈希扫描，不是保证或request性能。

本地只读接线核对发现真实准备缺口：身份/执行/消费合同锁Engineering，G512+pair与N1+pair被prepare拒绝，N1 controller限定pass1；G1现有配对只核输出数量。需最小显式Pilot角色/版本、真实Pass0与block/pair身份、已host-readable输出值记录，不重写S/A/B、不扩支持域。首批warmup1只能筛查漂移，不能证明充分；warmup ledger中的目标token赋值不是实际EOS证据。P1−P0保留profiler+观测插桩+运行波动解释，Nm−N0为包装/marker成本，N16−Nm不是纯wait因果贡献；opaque与逐sync B限制不变。

**唯一阶段适用性待集中确认：**推荐只对未来新采Pilot显式沿用已限定支持域，用于运行/质量政策估计，保留UNKNOWN/NOT_ASSESSED及资格/claim限制；不能自动把现行Engineering-only合同或历史数据升级。此页未实施角色/schema修订，正式采集前需固化适用版本并完成最小CPU接线验证。Gate11仍NOT_RUN，EP-G11-01本地代表集完成；EP-G11-02/04仅方案/Freeze输入清单草案，数值政策待Pilot，EP-G11-03未采集。没有服务器操作、GPU/Nsight、OOM、测试重跑或全量验证；仅文档一致性/链接/diff检查。用户DOCX不覆盖、不纳提交。Gate7～9及Gate10限定PASS、N1独立Engineering PASS保持。

## 7.110 N1三组限定Engineering可行性退出审查：PASS（2026-09-30）

已直接核验`n1_remaining_d25b4d1_once.zip`：38951058 bytes，SHA256 `e2fa13cf6fed9a46d9c61c2b78f2c2f083c64c45d3755ad93de4c645917849ea`；CRC/安全唯一路径、166文件/165项大小hash和完整覆盖通过。四份reference validation各57项PASS、32个producer当前实际字节严格匹配旧V0，24CRLF/8LF与c21→d25相同Git内容分开验证；本次已观察`__init__.py`实际b46cf529…，不是反推d51失败。原服务器CPU57 passed，两组entry/driver/profile exit0无超时、一次export PASS；本地没有重跑测试或完整分析。

依据[三组收尾0.1](n1_model_feasibility_closeout_v0_1.md)完成身份/Raw/producer/结果交叉审查：V0执行c21d835，复用7.108 adapter0.3/A-B0.6新合同准入、复读和独立Raw检查；Vmarker/V16执行及服务器分析d25b4d1。三组输入/模型内容、fp16/eager/SDPA/cache、32/2/batch1/warmup1/repeat1公共合同与实际tokens[[463],[2529]]一致，非early EOS。原preflight四件及manifest/input/runner/calls/ledger/nonce/PID、实际CUDA设备、REP→SQLite→Canonical/projection/派生文件hash贯通。文档裁决身份不同于执行commit；原V0 BLOCKED与新包pending/not-qualified等原字段保持不变。

独立只读SQLite字段/记录覆盖、实际correlation与同流完整FIFO/terminal/区间union复核：Vmarker三sync W=8/1906/3498；V16四sync W=8/1906/2814/3498，全部B_VALID。V16干预Runtime20193/correlation105548/sync351、ctx1/stream17，terminal Kernel6302，W保留2802个入口前已完成成员；内部Raw来源的源码字段仍未知，token-ready及干预仍结构身份。实际V0无干预、Vmarker层16一marker零sync、V16同位置一marker一sync。warmup/模型加载/锚点/成功drain在窗外，native handle与trace stream不按编号等同；全局lifetime UNKNOWN不被局部held证明覆盖。

三组九窗A顶层/子类互斥守恒、连续边界及逐分量Request=Prefill+Decode通过；新两组独立Raw区间验算与保存结果一致，不以零unknown替代归属。Request时长分别212715004/200583364/235519187ns；unattributed均0。每组三次Prefill allocation，opaque预算1637163/1994220/1283575ns，大小null、内部等待NOT_DECOMPOSED，无假W/B/双计；实际差异不解释为稳定收益或全部干预因果贡献。两组四条既知warning按已有官方依据处置，原诊断、UNKNOWN/NOT_ASSESSED、无未记录incoming依赖支持假设保留；D/Signature不启用。

**N1模型V0/Vmarker/V16限定Engineering一次可行性PASS。** Gate7～9及Gate10限定G1 PASS不变；这补足N1模型准备依赖，不授N1/G1共同统计稳定域、完整新版Q0、Pilot、Freeze、Formal或信息增益。没有剩余本范围证据阻塞，不新增实现/部署/服务器检查/重采。下一项仅Gate11本地准备：按研究问题选最小代表集，拟定有界Pilot组序/配对、重复/停止与overhead/质量政策的估计方法，整理Freeze输入；Gate11仍NOT_RUN，不自动采集。不改变测量合同或旧证据，用户DOCX保留且不纳提交。

## 7.109 N1续跑reference字节身份修复（2026-09-30）

直接核验`n1_remaining_d51a880_once.zip`：21322 bytes，SHA256 `c7bd5553abaee43f67e5bf4d712474ee955bb879d6cb38f5db62d36c40e1cdf2`；CRC、安全/唯一路径、23文件/22清单项与完整覆盖通过。服务器已部署d51a880，CPU107 passed属该原始回执；失败发生于reference校验，Vmarker/V16未进入模型/profile。旧失败目录/报告及原V0证据保留。这不是模型、A/B或allocation政策失败。

交付构建器把本地LF/Git blob字节错误当作目标执行字节。原c21 V0的完整preflight/claim/final/target claim和manifest、input receipt、producer/ledger/calls可重联；32个producer的Git内容c21→d51完全相同，旧观测hash精确解释为24个CRLF、8个LF。旧`__init__.py`为`b46cf529e2c9e9d4b11d0c7f66ca755eedca1f942b82d59c2794da75e2f46268`；原交付误期待LF的`e8a755439f13533ab95b8e5c3475a0ed8852ad386d82130503b631b42acd7d62`。**失败回执未记录当前实字节，当前服务器文件是否CRLF仍未直接观察，不由该错误反推。**

新`N1-REMAINING-REFERENCE/0.2`分别绑定旧执行hash/长度与old/new Git内容证明；Git以二进制读取，LF→CRLF只用于解释已封存hash，不用于运行时归一化。封存preflight四原件随包保留，必须与仍在原位置的原件逐字节一致，并重联nonce/run/PID、final状态、collector argv、manifest/prompt、runner、input receipt与measured V0 calls；32路径集合不能由reference任意缩减。当前文件必须精确匹配旧执行字节，缺失、越界、读取失败、hash/长度不符分别报错，保留expected/actual和实际读取位置。初始、每组执行前、结束后均核验；缺口不能先执行V16再在收尾拒绝。0.1交付reference不自动升级，旧包/历史判定保留。

tests-first复现LF/CRLF及新绑定入口缺失；审查补组间字节变化、measured身份错配的6个失败正反例后最小修复。相关两文件CPU **57 passed**（24.09秒）；覆盖同Git不同执行字节、篡改、错来源/版本/commit、缺文件、越界、读Git失败、公共合同/token及真实CLI→collect_group→profile边界替身。另用封存V0真实reference和32个精确hash的CPU文件替身完成CLI接线，真实本地LF先严格拒绝，再以旧hash绑定的重建字节通过；不是服务器字节复验、模型或GPU验证。compileall、PowerShell本地语法解析及diff检查通过；不重跑全量、Q0或原V0分析。

只改Engineering交付/身份验证，不改producer、runner、插桩、流/输入政策、研究合同、A/B/S/schema或既有资格。7.108 V0新合同支持域结论保持；N1三组可行性仍NOT_RUN，Gate7～9及Gate10限定G1 PASS保持，Pilot/Freeze/Formal不启动。用户DOCX修改不覆盖、不纳提交。下一项为前置**d51a880**的修复单ZIP交协调窗口审查；新目录只续跑Vmarker/V16，身份不符先停并回传具体差异，不修改服务器源码/期望hash、不重采V0、不恢复旧失败批次。

## 7.108 窄域opaque allocation amendment实施与V0离线收口（2026-09-30）

用户已批准7.107裁决稿的限定资源预算例外；[现行amendment与实物收口0.1](n1_opaque_allocation_v0_1.md)明确只支持精确cudaMalloc/合法数字后缀。新registry0.2、A/B0.6、N1 adapter0.3显式选择；旧registry/schema及0.1.1/0.2.0读取和历史判定保持，基础MC正文不覆盖。五类及互斥union/守恒、S的W/terminal、B公式未变；opaque计入non-submit且单独标注，不是非阻塞或已恢复内部等待，不新增假barrier/W/B、删除先行活动或启用D/Signature。

逐调用准入重建Raw身份/区间/成功/唯一correlation，窗外成功drain、实际非null NON_BLOCKING scope与完整下游闭包仍必需；失败、缺界、clock/owner冲突、嵌套/相交、关联activity/sync冲突、跨流/event或影响不明均拒绝。名字规则本身不能授准入。allocation未知大小null，内部等待NOT_DECOMPOSED；A_device_wait只含受支持sync恢复等待，B hidden只相对单sync。无未记录incoming依赖仍为显式支持域假设，UNKNOWN/NOT_ASSESSED不改，不授完整新版Q0/Formal或干预效果结论。

原c21d835 V0封存副本新派生`continuation_opaque_v0_1`完整准入55.555秒、文件重载全链37.399秒；收口修正严格drain名称/clock/correlation后，同一已保存domain再次完整复读39.950秒，结果精确一致。domain SHA256 `aec788be61053c6edbdb6b262be5b19fbe9d5c25a5233159c1e3cd60bb011d08`，review SHA256 `90d654334dcf28cfec670521516035c06c7a88a8949b82755c2ece250999a28b`。原ZIP/REP/SQLite/collection报告不改，旧attempt保持BLOCKED；新版本记录独立关联，不追认旧报告。

三次成功Prefill allocation（17566/17579/17646，correlation61737/61867/62931）总1637163ns转明确opaque API预算。Request212715004ns：Host119176616/API92285548/wait223646/residual1029194/unknown0；Prefill128172644ns与Decode84542360ns每个分量相加等于Request。五类守恒、API子类及opaque预算无双计；原总时长/Host/wait/residual不变。内部sync348完整FIFO8、terminalMemcpy344，token349/350 FIFO1906/3498、terminalMemcpy345/346仍三条B_VALID；实际32/2、tokens[[463],[2529]]。**V0新合同限定Engineering支持域审查完成，无独立剩余V0阻塞；不是完整N1三组可行性PASS。**

本机Python3.12.7，tests-first独立手算裁剪/守恒、真实producer CPU替身文件链、旧读取/unknown版本、proof和registry hash篡改、同步优先级与下游负例。10文件相关CPU198 passed（115.06秒）；最终allocation/续跑两文件44 passed（20.86秒，和前者重叠），另模型文件/调用层纳入63项收口（重叠不累加）。compileall、contract37/37内部一致性、Canonical boundary、静态oracle independence、PowerShell本地语法解析及diff检查通过；不是目标机或GPU验证，无全量/Q0重跑。

续跑接线复用原verified入口与collector，仅准备Vmarker/V16，各一次32/2；不因consumer变化重采V0。固定baseline review/原manifest/calls/producer/输入hash和未改producer源码；profile前复核公共合同及实际声明variant，之后核对实际tokens及Vmarker 1标记/0同步、V16 1标记/1同步。不能仅信reference期望值，不能将合法V0误接到Vmarker；新组实际allocation分别记录，不要求相同、不归因全部E2E差异。任何失败/超时即停止、无恢复/重试，固定增量单ZIP先交协调窗口审查；本轮未操作服务器、模型、GPU/Nsight。用户DOCX不改、不纳提交。

**当前下一项：协调窗口审查仅剩两组的固定交付后，由用户另行执行服务器步骤并回传单ZIP；Vmarker/V16仍NOT_RUN，N1模型三组可行性未授。** Gate7～9及Gate10限定G1 PASS保持，Pilot/Freeze/Formal不启动。此次amendment不影响历史Gate6资格或尚未存在的Formal数据；没有新的研究裁决项。下方7.107“政策待批准/V0阻塞”为当时历史，不再作为当前指令。

## 7.107 P1 Raw同步来源增量与P2 allocation保守识别（2026-09-30）

用户批准P1内部同步使用可核验RAW_PHYSICAL来源，批准P2只做已知allocation识别；opaque allocation放行政策未批准、未实施。已完成[版本化amendment及集中裁决稿0.1](n1_raw_provenance_allocation_v0_1.md)。源码origin/callsite/ordinal未观测保持null，不伪造forward/callsite；token-ready及N1预定干预继续要求结构身份，冲突不可由Raw替代。保留成功、唯一映射、进程实例/clock/scope、request/phase、完整W/terminal检查。

新来源schema0.1、S0.4、A/B0.5及N1 adapter0.2.0显式接线；旧schema/读取路径及0.1.1分析文件行为保持，未知/混用版本拒绝。A数值定义与B公式未改；仅P1来源身份扩展已生效，基础MC0.2正文/registry及旧Q0/Gate6证据未修改。Derived拒绝新A/B，不授完整新版Q0资格。P2精确cudaMalloc/合法版本后缀诊断KNOWN_ALLOCATION、completion_support=UNSUPPORTED、scope=null，不注册普通non-submit、假W/B或放行N1。

复用7.106封存V0的独立副本，新派生`continuation_p1_v0_1`；执行提交仍c21d835，consumer分析版本变化不改producer/runner/插桩/allocator/流政策。内部sync348/runtime17576/corr61831来源恢复：完整FIFO8、terminal Memcpy344；token349/350仍STRUCTURED，FIFO1906/3498、terminal Memcpy345/346。三条下层B_VALID；独立按Raw提交顺序及区间union检查，不用被测S/A/B生成预期。

完整准入44.348秒（S28.667、A/B1.982）；仍DOMAIN_MODEL_UNSUPPORTED_API，physical_b_failures为空、不生成domain.json。三次成功cudaMalloc合计1637163ns仍unattributed；内部1195434ns拆为223646ns wait及971788ns追加residual。诊断Request总212715004ns、Host119176616、API90648385、wait223646、residual1029194、unknown1637163；三窗守恒且各分量Request=Prefill+Decode，**不发布为合格模型A/B**。原ZIP/REP/SQLite/report哈希不变，UNKNOWN/NOT_ASSESSED及旧BLOCKED保留。独立checker初稿错误的全residual预期由Raw活动union纠正，未修改analyzer去迎合预期。

tests-first含真实producer替身文件链、独立完整FIFO/来源正反例、必需结构标签、映射/owner/clock/process冲突、来源篡改、schema读写和旧版本回归。相关8文件CPU239 passed（155.85秒）；最终来源文件33 passed（45.68秒，与239重叠不累加）。compileall、contract37/37（内部一致性）、Canonical boundary及静态oracle independence通过；无全量、服务器、模型、GPU、Nsight/export或Q0采集。用户DOCX修改保留且不纳本提交。

**当前唯一研究待决：是否接受无嵌套窄域opaque allocation作为资源管理API占据预算，并限制“不拆内部等待、不授allocation B/完整wait解释”？** 推荐透明修订后有条件采用，不因unknown小或欲放行推荐；有未界定跨流/owner影响、失败/缺边界、unexpected映射仍拒绝。现行代码继续BLOCKED，Vmarker/V16 NOT_RUN，当前无新采集/部署必要，不准备包。Gate7～9及Gate10限定G1 PASS保持，N1模型可行性未授，Pilot/Freeze/Formal不启动。

## 7.106 N1 V0完整离线审查、局部scope修复与语义停止点（2026-09-30）

直接核验`n1_model_c21d835_once.zip`：2177563 bytes，SHA256 `7867c610da1025cba1e68de2459f45b36d2b5979b949a70711def17315af28ed`，CRC/安全路径/重复项/87项清单完整覆盖通过。执行c21d835，服务器CPU142 passed属于原回传。V0模型/profile35.672秒exit0、producer/diagnostic COMPLETE、export PASS；原错误DOMAIN_MODEL_UNSUPPORTED_API和Raw/旧报告不改，Vmarker/V16 NOT_RUN。详见[有界实物审查0.1](n1_v0_review_v0_1.md)。

tests-first修复三项分析侧问题：实际Raw/桥接证明的fresh nondefault NON_BLOCKING同步不再受无incoming依赖的历史default活动污染；Canonical既有global PID解码保留VM高位且正确连接OS PID；unsupported不再只报第一条，结构化保留全部API来源与后续物理B/A失败。没有全局模式回填、W前缀截断、Raw修改、identity/warning绕过；相关event/缺映射/其他scope仍拒绝，旧合成/G1默认路径不opt-in。adapter0.1.1，不改producer/runner/插桩、V0/Vmarker/V16合同、S/A/B公式或冻结schema/registry。

同一封存副本在新版本目录完整续算，准入45.761秒仍BLOCKED；独立核对9678条API/3498活动的真实owner/单FIFO、成功窗前drain、32/2及三个completion窗。按提交顺序独立确定前缀8/1906/3498、最后节点Memcpy344/345/346，未按最大end单独定义依赖。内部stream sync物理映射完整，但origin/callsite/ordinal未观测，仍B_INVALID；两次token-ready下层B_VALID仅用于诊断，不授整次模型资格。S诊断28.543秒、A2.377秒、B0.087秒，未增timeout或跳检查。

三次Prefill cudaMalloc（runtime17566/17579/17646）均成功；官方CUDA12.4.1说明allocation及可能隐式ordering，但无逐调用Host全域completion保证。第二/三次返回时先行kernel仍pending，禁止硬套device-sync；无关联activity不证明无同步。合计1637163ns；内部来源缺口1195434ns。诊断A request212715004ns，unknown2832597ns；守恒及phase分量可加，但不发布可信A/B或D/Signature。未知未转Host/residual，也不作为永久“未注册名字”糊弄；停止在明确的已知allocation测量政策。

本机Python3.12.7，五文件相关CPU **185 passed**（113.21秒）；覆盖真实producer替身文件链、独立正反例与VM高位。收口自审补未知incoming顺序的红例并收紧opt-in，最终S文件100 passed及N1相关文件链7 passed（与185重叠，不累加）。实物没有已观察dependency event，保留无未记录依赖支持假设，不宣称排除全部未知。compileall、validate-contract37/37（内部一致性）和diff-check通过，无全量/Q0重跑、服务器/模型/GPU/Nsight/export。本轮DOCX出现外部修改，保留、不纳本提交；原始证据及hash不变。

集中未生效提案：P1新显式schema允许可追溯Raw物理来源身份，源码origin/callsite/ordinal保持UNKNOWN，不伪造forward标签；P2精确识别cudaMalloc为已知可能隐式排序而completion尚不支持，保留范围依据/unknown，不生成假W/B，不自动放行N1。不是删除无效B/零unknown门；批准后才做受影响资格增量。**N1模型支持域BLOCKED、可行性未授；Gate7～9及Gate10限定G1 PASS保持，Pilot不启动。** 当前无需服务器任务或重采包，Vmarker/V16暂停；先集中裁决最小语义政策。无Protocol Freeze/Formal数据变化。

## 7.105 N1采集前身份分派修复（2026-09-29）

直接核验`n1_model_c6cdb36_once.zip`：21345 bytes，SHA256 `3f41335dfc69a65bdc3e8e6c53f276280120070edde98d44e1fa0bc603f2d76b`，CRC/安全路径/29项清单及完整覆盖通过。服务器CPU141 passed属回传记录，不是新修复的验证。V0 driver 5.89秒exit1、未超时；collection为空，Vmarker/V16 NOT_RUN。traceback明确停在profile之前的`isolated.seal → validate_pre_model_identity`，不是模型执行失败；原`EXECUTION_FAILURE_UNRESOLVED`报告及封存ZIP保持原样。

根因是共享验证器仍只接受Gate7 Engineering/G1，**不是N1 producer声明错误**。真实prepared V0通过既有N1声明校验，却触发G1专属拒绝；此前CPU测试在seal之前结束或替换了validator，未覆盖此接口。修复保留默认Gate7 G1-only，isolated入口对N1意图显式分派至既有`N1-VERIFIED-MODEL/0.1`，复用通用commit/clean/physical-logical/UUID/PCI/mask核对，严格验证N1域、variant/public V16、callsite、流/执行声明、Engineering配置及prompt/runner源哈希。未知版本、矛盾/缺字段不能fallback成G1。没有新增研究语义或放宽身份门。

tests-first三个variant在真实collector→seal链先同因失败，修复后通过；真实prepare→seal也纳入回归。CPU profile边界替身继续调用真实target receipt consume、验证nonce/hash/run，故意停止，不运行Nsight/模型。18类错域/variant/配置/输入/源/commit/dirty/GPU/mask负例及未知dispatch版本拒绝。封存prepared原字节在新本地诊断目录、以明确CPU外部身份替身复查seal成功，不改原件或追认旧attempt。后续model-run/runner已有N1 opt-in；target/current、模型内容、native CUDA身份、固定配置、实际次数和多API消费检查仍在。

本机Python3.12.7，七文件相关回归 **142 passed**（104.18秒）；包括新回归、prepare、collector、isolated、Gate7兼容、N1 verified入口与多API domain。修改文件compileall及diff检查通过；无全量/Q0重跑，无服务器/模型/GPU/Nsight操作。物理S/A/B、runner、warning门、冻结测量合同及旧证据零改动。

下一项仅把以服务器`c6cdb369f683ffcdb28fe3b462d11c0280284392`为前置的固定修复单包、新commit专属输出目录和单ZIP方案交协调窗口审查；旧c6输出不恢复、不覆盖。审查后另行授权才运行相关CPU复验及原V0→Vmarker→V16有限批次，任何失败停止，不重试。N1真实模型支持域仍未验证、可行性NOT_RUN；Gate7～9限定PASS及Gate10限定G1 PASS保持，Pilot不启动。

## 7.104 N1 verified模型入口与多API文件链收口（2026-09-29）

按用户授权从31cd84e完成两处剩余接线；见[接线/最小可行性0.2](n1_model_wiring_v0_2.md)。沿用v2.1 §4.2 V16，不新增位置/次数选择：V0/Vmarker/V16只差预定decode层16干预；输入32/输出2、batch1、fp16/eager/SDPA、warmup1/repeat1一致。

原verified model-run入口显式opt-in N1，复用解释器/PID、内容、设备、Git seal、manifest及执行检查。`N1-VERIFIED-MODEL/0.1`声明warmup独立held流、成功drain后不同measured流及窗外共同sync锚点；满足Gate9优先fresh-stream策略，不截短物理W。0.1 resident helper不作为部署入口。实际调用、位置/次数、shape/token与sidecar hash接入原producer/execution链。

新增`exposedpath-n1-model-ownership/0.1.0`连接多API Canonical/ownership，不沿用旧一标记一API假设。锚点→correlation/context/trace stream与drain核对，逐API/活动/同步验证request/phase/实际流并复用原S/A/B；未知、歧义、其他流/依赖/graph保持拒绝。non-submit伴随查询只按原注册表支持，原内部同步也检查：没有冻结S必需sync身份时仍INVALID，不能补造callsite或转Host。物理S/B、G1自然路径、Q0、冻结公式和旧证据均未修改。

tests-first实际verified producer→合成SQLite→Canonical→projection→S/A/B及复读已接通；独立预期W为[3,6]/[3,5,6]并检查具体A分量，不仅守恒。相关14文件CPU **192 passed**（163.83秒），收口后三文件定向 **36 passed**（70.39秒，与192重叠，不累加）；本机Python3.12.7，修改Python compileall、PowerShell语法解析、diff检查通过。不是目标机CUDA/模型验证，无全量/Q0重跑、服务器/模型/GPU/Nsight操作。

本地接线完成；**N1模型可行性NOT_RUN**，仍需目标机证明实际模型提交/内部同步满足支持域，CPU不能代替。准备以700f671为前置的固定单包与V0→Vmarker→V16各一次有限方案，先交协调窗口审查；任何失败停止后续组、不重试、单ZIP回传。首批仅执行/支持域，不评价干预效果或选Pilot阈值。Gate7～9限定PASS及Gate10限定G1 PASS保持，Gate11/Pilot不启动。没有新的研究语义裁决项；没有变更Protocol Freeze或Formal数据（均未启动）。

## 7.103 N1模型最小调用层接线与CPU文件回归（2026-09-29）

用户确认Gate10限定G1 PASS并授权本地N1接线。直接沿用Pre-Pilot协议v2.1 §4.2 V16：每次decode第16层后一次current-stream sync；Vmarker同callsite/branch/marker但不同步，V0无layer干预包装。没有新增选点、位置扫描或研究语义裁决。详见[接线0.1](n1_model_wiring_v0_1.md)。

tests-first新增独立opt-in `n1_model`：临时decode layer-forward包装、异常恢复，复用未修改runner completion/EOS/drain和Gate9实际current-stream记录。resident子入口封存plan/prompt与hash、实际配置/调用/边界/drain/失败回执；同held流warmup在窗外，保留完整物理前缀。Vmarker/Vsync标记结构相同，V0不装层包装。相关五文件CPU **62 passed**，Python compileall和diff检查通过；CPU替身不冒充目标机模型/CUDA验证，无全量/Q0重跑或服务器操作。

**本地端到端N1模型接线尚未全部完成**：现Gate9消费者是“一标记一API”的受控桥接，不能直接接受模型forward中的多API；仍须接既有verified model loader/preflight到新子入口，并完成模型Raw→Canonical实际ownership文件消费者及反例。不删除旧unbound检查，不把with-stream/host成功当物理归属。当前子receipt明确COMPLETE_PENDING_TRACE_OWNERSHIP、NOT_ASSESSED及N1模型可行性NOT_RUN，不是WMPC/域资格报告。

Gate10限定G1 PASS和Gate7～9限定PASS保持；N1模型可行性单独未运行，Gate11/Pilot不启动。下一项是上述两处必要本地接线，不再整理选点待办；无语义待决，不要求用户重复授权。尚未达到交付采集包条件，本轮不生成部署/采集脚本，不要求服务器操作。冻结合同/旧证据/G1路径未改，历史编号及判定保留。

## 7.102 Gate10选定G1候选退出审查：限定PASS（2026-09-29）

已直接核验700f671的512-only回传：27081774-byte ZIP/hash/CRC、89文件、88项清单完整覆盖及大小/hash通过；只读input/producer/entry/preflight身份、实际512输入/2输出非EOS、阶段/drain、domain文件集合/hash和report一致。原服务器CPU221 passed，本轮未重跑测试或完整分析；只读SQLite quick_check通过。完整证据及版本表见[Gate10收尾0.1](gate10_closeout_v0_1.md)。

G1逐request准入通过、无reasons，三窗整数守恒和逐分量阶段相加通过；已有官方诊断处置适用，原warning/UNKNOWN/NOT_ASSESSED保留。复用32/2（执行36ed952、分析1733ff3及后续官方依据审查）；128/2执行76ef717、700f671离线修复后通过，原超时不改；512/2执行/分析700f671成功。均一次Engineering可行性，不比较profile趋势、不推稳定性/repeat/阈值。

**Gate10 PASS仅限G10-WORKLOAD-FEASIBILITY/0.1的自然G1 32/2、128/2、512/2 batch1候选范围**；EP-G10-01～03在此缩减范围收口，不授N1模型V0/Vmarker/Vsync可行性或N1/G1共同稳定域。N1功能/模型可行性按原计划保留后续准备依赖，本轮不临时扩张或采集。Gate7～9限定PASS保持；Gate11 NOT_RUN仅可本地准备，N1相关Pilot仍依赖N1模型验证，Gate12～14不启动。

下一项最小工作为本地N1模型最小执行接线依赖整理；当前无服务器操作。仅文档更新、链接与diff检查，无业务代码/冻结语义变化；Raw/封存ZIP/旧失败报告保持。文档收尾commit不冒充700f671执行身份。

## 7.101 Gate10 128/2离线超时定位、性能修复与不变Raw续算（2026-09-29）

直接核验76ef717回传ZIP/hash/CRC/86项路径及副本；原采集36.406秒exit0、driver900.016秒超时、UNKNOWN后代记录不改，512 NOT_RUN。原服务器CPU121 passed仅是原日志。本地限时profiling与独立工作量反例定位重复registry读取、A逐原子片全扫API/sync、LEGACY同流两两无效扫描。见[审查0.1](gate10_timeout_review_v0_1.md)。

tests-first最小修复批内registry复用、default跨流候选过滤、A活动区间sweep；保留必要集合/边顺序、半开区间、同步优先级、未知/冲突、物理S/B与复读校验，冻结合同/schema/拒绝条件不变。补flush阶段进度，不提高timeout或跳检查。512-only入口仅执行未运行点、新目录，不恢复旧attempt。

新派生完整文件链及复读186.206秒，本机Python3.12 CPU，非服务器加速比；128/2质量通过、实际token2/non-EOS，三窗守恒/分量相加、unattributed0。目标PID/环境/Git536路径/preflight绑定、窗前drain与后缀证明通过；159路径Git blob字节相等，377仅LF→CRLF，不伪称全字节一致。原ZIP/86项副本不变，原失败report不补写。仅一次Engineering可行性，UNKNOWN/NOT_ASSESSED保留。

最终9文件相关CPU回归221 passed（107.90秒）；修改Python compileall、PowerShell解析及diff-check通过。新增8项中含真实A入口旧版30100次覆盖扫描的红例和新实现绿例。未重跑全量、旧Q0、服务器/GPU/Nsight/export/模型。EP-G10-02的128/2实物及离线分析已审查；512/2尚未运行，EP-G10-03总审查未完成。**Gate10 NOT_RUN；Gate7～9限定PASS保持。** 下一步只交协调窗口审查以76ef717为前置的增量包及512-only命令，不重复128或整个批次。domain约937MB是已知证据存储成本，本轮不扩展schema优化；没有新增研究语义裁决或Formal数据变更。

## 7.100 Gate10最小G1输入轴准备与本地接线（2026-09-29）

用户确认Gate9限定分域PASS后，固定[G10-WORKLOAD-FEASIBILITY/0.1](gate10_workload_plan_v0_1.md)：复用32/2 batch1封存可行性，仅新增128/2和512/2，按协议输入轴且不依据A比例选点。均单平台Qwen1.5B、fp16/eager/SDPA、自然G1、warmup1/repeat1；只作Engineering可行性，不作Pilot统计或Formal性能比较。
首样本32token循环扩展，文件digest固定；执行前校验vocab/special token/全1 mask/max position和内容快照，前置manifest声明G1资格域。N1完整模型V0/Vmarker/Vsync功能单列后续依赖，本批不替代N1模型可行性。

tests-first完成显式非32入口、G1接入已有官方诊断review及collector domain接线、既有实际shape/count窗后持久化、两点有限编排及失败停止。旧32入口/封闭identity schema/物理S/B/冻结公式不变；原warning及UNKNOWN保留，同类warning不豁免correlation等其他缺口，旧attempt不改。机器report与实际token/entry/preflight/domain一起校验，exit0不能替代分析准入。
本地相关7文件119 passed；最终收口22 passed（重叠不合计），compileall/PowerShell解析/diff-check通过。无全量重跑、旧Q0/模型/GPU/Nsight/服务器执行。仅CPU模型/设备替身与实际文件链，不冒充目标机验证。

EP-G10-01候选/规则已完成，EP-G10-02/03待新点实物；**Gate10 NOT_RUN，Gate7/8/9限定PASS保持**。首批单包以服务器15b24ec为前置，经协调窗口审查后才执行相关CPU检查及128→512各一次profile；任何失败停止、不自动重试/恢复/换参/扩搜，单ZIP回传。当前不要求用户立即执行。
计划调整仅缩减工作负载组织，不修改冻结研究语义或已有Formal数据（未启动）；无新平台/模型/compile/G2、D/Signature或Pilot任务。

## 7.99 Gate9最终分域退出裁决：PASS（2026-09-29）

依据用户已批准的G9-DOMAIN-QUALIFICATION/0.1.0 §2–5和fe25d5b完成[最终资格裁决](gate9_closeout_v0_1.md)。
逐项区分N1目标桥接实物/独立Raw oracle、G1既有自然实物/新增文件入口独立正反例、支持域假设；必需增量已满足，无剩余Gate9证据缺口。
EP-G9-01～04收口，**Gate9 PASS仅限当前Windows/4090固定观测栈：N1显式非默认非阻塞流A及合格单sync B；G1自然投影A，不授自然默认流完整物理B。**
fe25d5b两项分析侧修复已由7.98回归及不变Raw续算验证；服务器未部署分析修复不是重采理由。执行15b24ec、分析fe25d5b与本次文档提交严格分开。
原BLOCKED/INCONCLUSIVE/条件性产物、UNKNOWN/NOT_ASSESSED保持；不授完整新Q0、Pilot、Freeze、Formal或信息增益结论。Gate8 PASS不重开。

本轮仅文档审查和链接/diff检查，复用既有60项相关回归与独立oracle结果，没有测试重跑、重分析、服务器或GPU/Nsight操作。
计划调整：Gate10由平台前置阻塞转NOT_RUN；先本地固定选定workload的最小候选及目的，复用G1 32/2 batch1可行性，只给真正新点准备停止规则。
不自动执行新采集、广域OOM扫描或Pilot统计；当前无需服务器动作。不改变冻结测量合同或历史Formal数据（未启动）。

## 7.98 Gate9桥接回传审查、诊断接线与离线oracle（2026-09-29）

已直接读取15b24ec执行回传原件；ZIP/CRC/路径安全及71项清单、72文件字节一致性通过。[完整有界审查](gate9_bridge_return_review_v0_1.md)。
服务器原日志CPU102 passed，profile/producer COMPLETE、export一次PASS；本地未运行服务器/CUDA/Nsight。
四条warning为同组已接受消息，row3/4/6/7属PID60888；目标27224有实际31 NVTX及CUDA活动和完整身份链。
复用用户回传官方解释，不重启PID追索/询证：新增版本化独立诊断review，保留原始diagnostics及UNKNOWN，不把warning改成不存在；旧Gate8门不变。
先复现失败再补正反例与最小接线。随后发现并独立修正N1桥接把runtime flags=1误当CUPTI stream type的问题：实物ENUM表明确2=NON_BLOCKING；只改桥接比较及两个错误合成fixture，不改Raw或S/A/B公式。

新目录离线domain文件链通过，独立Raw oracle MATCH_REVIEW_REQUIRED：14调用、两个request、6边界/6 sync、W数1/2/4/5/6/8、terminal/B和六窗A全部相符；unattributed=0，互斥守恒、phase分量可加。
runtime/launch/关键源码/DLL身份复核通过；复用CUDA源码的CRLF checkout与Git LF blob差异已明确记录，未伪称字节相同。
本地CPU36 passed，另G1/旧诊断回归24 passed；修改文件compileall及diff-check通过。未重跑全量或旧Q0，既有7.97旧oracle失败不被掩盖/改写。

**本包N1桥接技术阻塞已关闭；Gate8 PASS保持，Gate9总判定本轮不自动改PASS（原BLOCKED状态保留至最终分域汇总）。**
当前优先级仅为将本增量与7.97 G1投影资格及已有实物复用完成最终退出审查；本包没有需要新采集的缺口，不要求服务器操作。
原attempt/Raw/报告不变，派生结果仍Engineering、UNKNOWN/NOT_ASSESSED、非Formal，不授完整新Q0、模型或信息增益资格。

## 7.97 Gate9分域本地接线与受控桥接准备（2026-09-29）

从98a85e5继续，按[合同0.1](gate9_domain_qualification_contract_v0_1.md)落实[最小增量](gate9_domain_increment_v0_1.md)。
N1实际current handle/线程/device/lifetime观察，经NVTX→原API→correlation→物理stream/context连接；保留完整已完成measured前缀，复用S/A/B。
G1新增必要成员与依赖边双模式检查，不以同数值/守恒代替归属证据；版本封套/文件链保留UNKNOWN、NOT_ASSESSED及非Formal状态。
独立手算三窗、长度变体、局部5ns故障注入和拒绝反例，以及实际新producer的CPU替身Raw全链已纳入测试。
局部缺口测试只暂时撤去已知non-submit的A子类证据，不授权未知依赖局部化。新request继续逐窗质量门，长度不自动重Q0。

范围审查发现旧closed-prior schema仅容纳measured来源；未扩展或改写schema。目标微程序采用新建显式流、两个measured request、warmup_count=0，初始化/drain窗外。
未来模型采用合同首选“warmup/drain之后新建专用流”；复用含warmup历史的流仍拒绝，不能把warmup改标measured。
独立Raw oracle核对预定六个物理集合（1/2/4/5/6/8成员）、terminal、A和逐sync B，不调用被测S/A函数。

验证记录：扩展相关回归133 passed、1 failed；失败为旧`test_bounded_gap_file_chain_retains_two_ns_unknown`，
旧oracle仍把已在1733ff3支持的cuKernelGetFunction按unknown计。本轮两个被改旧模块换成98a85e5源码在内存执行，独立复现相同失败；没有修改旧oracle/测试或历史资格。
最终核心定向回归101 passed（131.80s）；追加G1可见N1 marker拒绝及相关文件/启动链17 passed（40.98s，与前组重叠），真实隔离解释器导入前后snapshot一致且未导入torch。
compileall、contract内部一致性37/37、Canonical边界（7模块）、旧oracle静态独立性检查与PowerShell语法解析通过，git diff --check通过。
没有运行全量、CUDA编译/执行、Nsight、模型或真实Q0；CPU替身不是目标机证据。

交付为固定增量bundle＋一次脚本/配置，前置目标机bee6a25；脚本CPU失败停止，显式授权后只作一次受控CUDA/Nsight桥接、单次export，结果统一单ZIP。
MATCH仅进入增量审查；缺字段/未知诊断为证据不可判别并保持BLOCKED；矛盾/失败/超时停止，禁止自动重试。
**Gate8限定Engineering PASS保持；Gate9仍BLOCKED待目标显式流桥接及增量证据审查。**完整N1、Pilot、Freeze和Formal不并入本轮。旧probe/Raw/报告不变。
当前优先级：先由协调窗口审查固定交付，不自动操作服务器，不重采Qwen。此前未推送合同一并正常补推，具体远端结果见交付回执，不强推。

## 7.96 N1/G1分域合同批准与独立预期（2026-09-29）

用户接受7.95两域及claim限制，授权合同设计。[G9-DOMAIN-QUALIFICATION/0.1.0](gate9_domain_qualification_contract_v0_1.md)
固定N1显式非默认非阻塞流V0/Vmarker/Vsync、G1自然投影A；不主张自然完整物理B/hidden，不跨域外推。
合同明确G1边界/身份/成功drain/必要后缀与依赖闭包/唯一frontier/局部缺口义务，区分事实与无未记录incoming依赖的支持假设。
已给独立手算三窗正例、同数值错成员、缺映射、drain/跨线程冲突、局部缺口和长度变化预期；没有运行被测实现生成答案或测试/采集。
输入长度本身不触发重Q0；新request逐窗自动准入，实际语义变化才申请受影响增量。封套字段/版本仅设计，旧schema及历史判定不变。
Gate9仍BLOCKED，当前剩余改为N1显式流调用/ownership桥接与G1投影资格增量，不再要求确定自然默认流全局模式。
Gate6/7历史PASS、Gate8限定Engineering PASS保持；完整N1 runner、Pilot、Freeze不并入Gate9。无Formal数据变化。
下一步本地最小实现与独立预期接线见合同§5；目标平台桥接需另交协调审查，本轮无服务器操作。
本轮验证仅文档引用/差异检查，不声称新增Q0或平台资格。7.95以下保留为历史。

## 7.95 N1/G1最小分域方案（2026-09-29，待裁决）

用户原则上考虑接受，未批准立即实现/采集。本轮在[Gate9现有入口](gate9_platform_assessment_v0_1.md)
集中写明两项可证伪命题、统一N1显式流控制组、内部其他流/依赖拒绝规则、自然G1逐request的A/S准入及claim损失。
明确Engineering A-only现状不能通过删除标签自动获得科学资格；若采纳，需版本化投影适用条款和独立验证。
已有Gate6/边界/身份/三窗证据复用；新增只针对显式流调用桥接及G1投影资格，不完整Q0重跑。
平台资格与workload可行性/Pilot/Freeze/信息增益分开，完整N1 runner不是Gate9单独门槛。
推荐有条件采纳，取舍为放弃自然默认流物理B及跨域机制外推，保留受控机制＋自然请求A有限信息增益。
待用户最终裁决；Gate8 PASS、Gate9 BLOCKED，当前无服务器操作，无业务代码/测试/采集或旧证据重算。

## 7.94 Gate9 probe原件INCONCLUSIVE与路线停点（2026-09-29）

本地直接核验[probe回执](gate9_stream_probe_v0_1.md)：ZIP14183bytes及指定SHA、CRC、29文件安全性、
外层28项/内层11项hash与精确覆盖、source commit/runtime绑定通过。服务器CPU34passed、compile成功；
目标PID66200，error=null，无超时、exit2，before=false/after=true，两线程handle0且顺序完整。
按预声明INCONCLUSIVE收口；外层BLOCKED是停止路径而非程序异常。不用耗时判模式、不重跑或延长K。
Gate9仍仅阻塞自然默认流完整物理W/B适用性；已有平台能力与Gate8 PASS不否定。原件不改。
现有材料无确定性模式证据，也无已审查安全两面判别构造；不新建实验设施。
[Gate9入口](gate9_platform_assessment_v0_1.md)集中提出一项待裁决：N1显式流受控对照，G1自然执行但不作默认流B claim。
这会改变N1执行合同和claim分域，尚未批准/实现，不把它当普通修复。当前用户无需服务器操作。
本轮仅读取/文档校验，无测试、CUDA/Nsight或旧A重算；Gate8已收尾，Formal/Pilot未授权。

## 7.93 Gate9单向区别probe本地实现（2026-09-29）

按用户批准完成[固定操作与独立预期](gate9_stream_probe_v0_1.md)，没有N1/model/Nsight。
实际current_stream().synchronize后，已记录worker事件仍pending才排除本次共享等待；
事件完成不判LEGACY，INCONCLUSIVE停止。窄域结果仅服务计划调用资格，不回填旧Qwen物理B或mode。
新增probe、直接解释器/身份/45秒超时监督、CPU正反例；设备查询复用生产native adapter。
先13例缺实现失败，再最小实现；PCI域宽度回归失败后采用既有normalizer，不用编号相等猜身份。
相关CPU测试34 passed（本地Python3.12）；新文件compileall/diff-check通过，没有目标CUDA验证。
交付复查将新PID敏感CPU子进程测试统一为sys._base_executable，避免重复既有Windows venv launcher
PID分离问题；生产supervisor原本已经采用显式direct interpreter，不改变CUDA判定或支持域。
Gate9仍BLOCKED待固定probe目标证据/审查；Gate8已收尾；不授Q0总资格、Pilot或Formal。
单一增量包以前置服务器36ed952为基线，配套固定版本单段步骤与单ZIP回传；本轮不操作服务器。

## 7.92 默认流有界核对结论C（2026-09-29）

[Gate9入口](gate9_platform_assessment_v0_1.md)保存目标机源码/header/PE依据及一次区别性方案。
静态资料能支持同步包装路径，不能确定实际默认流语义；停止该搜索。
只读既有Canonical发现3838窗前活动中338由四worker提交但显示同NULL trace stream7，
其是否进入主线程物理W会影响B hidden/ownership；成功drain不消除此语义差异。
未证物理B双模式等价，因此选择C，不新增模式猜测或扩大A-only资格。
Gate9 BLOCKED仅限此具体范围歧义，N1未实现仍仅为后续准备；Gate8已完成、不重开。
下一步只准备同PyTorch调用路径、跨线程默认流的有限probe，预写可判别/不确定结果及停止规则；
一次观察不证明全局模式，不自动重试。当前没有服务器执行命令，不要求用户操作。
本轮无实现、无测试、无analyzer重算或采集；已有字段枚举与correlation连接只用于适用性核对。

## 7.91 Gate9边界纠正及默认流适用性核对（2026-09-29）

[Gate9当前入口](gate9_platform_assessment_v0_1.md)已集中记录有限核对和Gate0–14精简处置。
撤回7.90以N1 runner缺失作为平台阻塞的理由。一般stream-sync观测/物理S/A/B资格直接复用Gate6；
当前真实Qwen的stream/context/ownership与后缀A等价证据已具备，不重验。
本轮只读现有Canonical明确default_stream_mode=null、null_stream_id7，native handle0不区分模式。
已批准两模式后缀等价只覆盖A，不能自动授物理B。Gate9 BLOCKED仅剩实际current-stream调用
默认流语义与既有物理S/B资格的适用绑定；不是重跑Q0或实现完整N1。
下一项精确PyTorch调用/构建身份的有界核对；能证即复用，否则仅设计同调用路径的区别性受控probe。
当前无服务器命令或采集，用户无需操作。Gate10仅选定点可行性；11 Pilot、12 Freeze、13信息增益
保留必要目的；14/G2、第二平台、compile/graph后移。Gate8不重开，旧证据和UNKNOWN不改。
本轮无实现、无测试、无离线重算；文档更新不授新Q0或Formal资格。

## 7.90 Gate9最小执行方式与资格对应（2026-09-29）

用户确认Gate8限定Engineering PASS收尾；官方答复按用户内容采信，不再网页核验或询证。
新增[最小适用表](gate9_minimal_mode_qualification_v0_1.md)：读取研究设计v7.1及协议v2.1
§4.1–4.5/§5.1，沿用路线A单平台单模型eager；V0/Vmarker/单位置V16是最小N1候选，
G1只提出32→64输入单轴候选，不冻结Pilot点或阈值。
本地源码确认runner明确拒绝N1，NVTX/manifest仅有身份合同。现有资格不是N1执行证据；
真正缺口收敛为N1实际接线及新增stream-sync在当前projection/S/A/B路径上的资格桥接。
复用平台身份、真实Qwen自然基线、Gate6稳定语义、限定受控资格与1733ff3分类回归；
不重开Gate8、不完整重跑Q0。Gate9仍BLOCKED于上述具体缺口，不因warning或泛化未知阻塞。
下一项主窗口本地tests-first最小接线；完成后再判断是否确需单次受控目标机增量验证。
当前没有可执行的N1入口，故不交付占位服务器脚本，用户无需操作服务器。
本轮仅文档与只读源码/文档检查，无生产修改、测试、GPU/Nsight或旧证据重算。
初次DOCX文本显示受GBK限制，改UTF-8读取关键条款；未修改文档原件。
Protocol Freeze仍未进行，Formal不授权，D/Signature不启用。

## 7.89 官方答复回传后的warning证据裁决（2026-09-29）

新增[G8-WARNING-EVIDENCE/0.1](gate8_warning_evidence_review_v0_1.md)，逐字保存用户回传官方答复。
网页工具不可访问；直接公开JSON读取限速、按提示重试一次仍失败，已停止。本轮未直接核验作者身份、
发布日期或回复楼层，来源明确USER_RELAYED_OFFICIAL_RESPONSE，不捏造回复链接/日期。
答复说明进程树无事件/短命进程warning与目标CUDA/NVTX采集的关系；与既有目标PID60060、三点、
成功drain及sync/activity实物相符，无已记录具体矛盾。不再要求证明每个外PID用途，关闭本包warning
的Engineering作用域阻塞。不能把“could be read”转换为dropped=0或绝对完整性认证。

Gate8 PASS仍限定G8-ENGINEERING-EXIT/0.1；现在由回传官方解释及实物支撑，而非只有未证假设。
7.88事后政策及原标准NOT_RUN保留历史；旧attempt BLOCKED和1733ff3派生条件性字段、UNKNOWN/
NOT_ASSESSED全部不改，不授完整新版Q0、模型科学有效性、Formal或信息增益。精确证据hash见新裁决。
本轮只引用已完成退出清单，未重新执行测试、离线分析或hash扫描，没有服务器/GPU/Nsight操作。

[Gate9评估更新](gate9_platform_assessment_v0_1.md)：身份及eager项继续复用，观测项加入新解释，
不再因同四warning维持工程否决；最终资格仍BLOCKED于后续科学执行范围的版本绑定结论未签发。
下一项具体本地工作：首个最小N1/G1对照的执行模式—资格适用表，只比较completion/sync/backend/
stream/ownership变化，已有覆盖直接引用，不全重跑Q0。不把答复来源补齐设成所有工作的前置。
当前无已确认必要服务器补证，不生成重采方案；Gate7 PASS，Pilot/Formal、D/Signature不启动。
本次只改当前入口与审查文档；生产warning规则、Raw、旧报告和历史资格均未改。

## 7.88 工程退出政策修订与Gate9首轮资格评估（2026-09-28）

用户在观察现有结果后明确批准[G8-ENGINEERING-EXIT/0.1](gate8_engineering_exit_amendment_v0_1.md)。
**修订后Gate8 PASS：仅Engineering执行链、可观测性接口与条件性accounting的工程可行性。**
四指定外进程warning无目标影响仍是未证、可推翻的支持假设；真实Qwen A仍条件性，
不授完整新版Q0、模型科学有效性或Formal资格。原标准NOT_RUN、旧attempt BLOCKED和原报告不改，
UNKNOWN/NOT_ASSESSED保留。下方7.87及更早记录是当时历史，不能作为“Gate9一律禁止”的现行指令。

五项工程退出按7.86/7.87既有证据逐项满足，未重跑测试或hash扫描。执行36ed952、分析1733ff3、
本次文档/政策commit三者分开；MC/S/A/B及生产warning门零修改，事后政策不追认Formal。
[Gate9首轮评估](gate9_platform_assessment_v0_1.md)已完成：EP-G9-01身份、03最小eager范围已复用核定；
02旧Q0/限定新资格分层复用，科学观测资格尚缺；04给出初评BLOCKED，原因是科学证据准入未闭合，
不再写“平台未接入”。本轮已正式开展评估，不能把BLOCKED等同未开展工作。

最高优先级：集中界定后续科学claim/证据接受边界。工程支持假设不能自动授权科学机制claim；
厂商答复仅补充来源，不是其它工作的统一前置。当前没有能消除该不确定性的已证可行服务器补测，
不交付同配置重采/部署命令，不新增全量、完整Q0、第二平台、compile/graph或G2任务。
Gate7历史PASS；Gate9不自动PASS，Gate10/11仍未启动，Formal不授权；D/Signature不启用。

整理只收敛当前入口与历史横幅；审计、Raw、ZIP、manifest及合同版本不移动、不删除。
已逐路径核验并清除四个源码/测试目录内172个可再生Python字节码（4419847 bytes），源文件均在、无tracked缓存或reparse目标，未递归删除目录；可由Python/pytest再生。
公共handoff缩为当前入口和历史链接，完整旧交接保留Git历史而非新建副本。
`.local/transfer`现有13个bundle、2个脚本、11个ZIP未逐一证明冗余，全部保留；其它独有诊断及临时派生未清理，不猜测可删。
本轮验证仅文档链接/状态一致性、私有路径扫描与git diff检查，无实验、无代码测试。

## 7.87 non-submit 类别机制修正与条件性复算（2026-09-28）

按用户合并授权，仅修正既有观测中可解释的分类缺口；见
[有界审查及结果0.1](gate8_non_submit_api_review_v0_1.md)。直接核对研究设计v7.1 §2.4、
Pre-Pilot协议v2.1 §3.3、MC0.2 §10/15及CUDA12.4.1官方资料；non-submit不等于绝不阻塞。
新增A专用registry0.1.0与共享adapter，保留冻结物理同步优先；不再由“有activity”替代未知API语义。
真实request七种API逐项覆盖，两个handle/capture查询由明确语义归non-submit；窗口外其余15种
列明支持边界，不把初始化/资源管理接口无条件放行。父类/子类不可判定时当前schema仍保守unknown，
未增加类别或修改守恒式；未来parent-only表示须单独amendment，本次没有依赖该裁决的调用。

先15项红测复现，再最小实现；相关七文件143 passed，追加文件链activity/sync/error三反例3 passed。
本地Python3.12.7；修改模块/测试compileall、contract37/37内部一致性、diff-check通过。
未知调用、缺依赖、ownership、同步及重叠子类冲突仍拒绝/unknown；旧S/B/schema/Q0路径保留。
这些是本地回归，不自动授新版本Q0资格，不撤销历史Gate6或既有限定受控资格。

封存执行身份仍36ed952，修正代码不是服务器新执行。实际条件入口exit0，新目录派生
SHA256 `f0e81b5e3f1dba30f0e2c8b6a6d3f9542a361d4005b338b6905ae54696ec4928`，924663324 bytes。
6171条分类缺口消除：Request/Prefill/Decode分别3840151/2112805/1727346ns由unattributed
转为CUDA non-submit；三窗unattributed均0，Host、submit、wait、residual、T均不变。
Raw独立裁窗和返回/关联/无API重叠检查通过；两默认流必要集合逐成员保持、五类/二级守恒及
Request=Prefill+Decode通过。原ZIP、146文件、正式报告及旧条件输出重新核验未变。
原7.86结果保留为旧分类版本，不覆写、追认或部署。只声称当前支持域和warning假设下分类缺口消除，
不将低/零unattributed当充分质量证据；UNKNOWN、NOT_ASSESSED、trusted_a=false保持。
warning作用域假设保持，标准Gate8 NOT_RUN，Gate7 PASS；Gate9/Pilot与D/Signature不启用。
本地分类修正及精确差值核验已收口；最高优先级为协调审阅条件性结果和未证warning假设，
当前实物无需额外研究语义裁决，不安排服务器操作或重复采集。本提交同时记录实现与进度。

## 7.86 配对原件审计与条件性集中收尾（2026-09-28）

执行commit固定36ed952b57f20651dd290fc484d7b21fc7dbbfc4；文档收尾不是服务器新执行身份。
本地直接审计pair原ZIP：26583909 bytes，SHA256
`3c90764357547cfb28de3c16bc624664e36d58565dfa4dcb02f1063e0294940f`；CRC、146文件、
顶层145项及嵌套清单全部大小/hash匹配，原static ZIP逐字节未变。详见
[条件性收尾0.1](gate8_conditional_closeout_v0_1.md)，其退出表取代此前“尚待目标机配对”的状态。
服务器原日志94 passed/42.51s及静态回执通过；本轮未重跑测试、完整Q0、模型、GPU或Nsight。

已关闭Git二进制修复的实际运行验证：每pass保留23833 bytes NUL输出，496个tracked路径与
固定commit树完全一致，seal恰好覆盖496项。输入、独立run/nonce、目标claim、final hash及runner字节
匹配；不是将旧486项事后核对追认为新预检。两pass入口exit0，producer COMPLETE、final PASS。
本地重新调用配对检查，结果与服务器pair_observation完全一致；模型/输入/配置/设备身份一致。

原SQLite直接核三trace点、窗外成功drain和3次内部/边界同步；后缀3498项，必要集合8/1906/3498。
独立区间核算得到request T=164259912ns、局部unattributed=3840151ns（2.33785%），
6171条有界API分类缺口保留，不填Host/residual；结果仅用于声明假设下的条件性分析。
Host配对request为117197100/164476100ns，差47279000ns（40.3414%）；
一次观察包含插桩及运行波动，不称稳定开销或据此冻结Pilot阈值。D1 marker延迟非零，A/host两种窗口分开。

正式A仍因row3/4/6/7四warning（PID64488）BLOCKED，原报告a_records为空且不改；
UNKNOWN、NOT_ASSESSED不改零或有效。复用既有限定受控资格，不授完整新版Q0或真实模型资格。
固定生产条件入口已exit0，CONDITIONAL_A_ONLY_NOT_ACCEPTED；三窗分量与独立区间核算一致，
两模式必要集合逐成员相等，顶层/子类守恒、互斥、uncovered、越窗检查均0。原146文件逐字节不变。
派生SHA256 `bf17787e6647d36b0fc15ccb87deb9519b384ebab0c4fd2dfa691f793a6f2e4a`，
926646005 bytes（含物理S/B记录），只本地保存；未因存储成本扩展本轮开发。
最终审计首次误用守恒字段名，修正本地审计脚本后通过；生产结果及原件未改。
已批准限定范围内，其余退出条件已完成，仅warning作用域假设待决，未发现其他必要阻塞。
Gate7历史PASS保持、标准Gate8 NOT_RUN。最高优先级为协调审阅条件性收尾报告及未证假设，
无需服务器操作或同配置重采。此文档提交不是执行commit；无冻结语义或Formal资格变化。

## 7.85 四warning假设隔离派生与最小配对交付（2026-09-28）

用户已批准暂按“四条外进程warning不影响目标request”推进条件性分析；不是范围证明或标准Gate8 PASS。
[条件配对合同0.1](gate8_conditional_pair_v0_1.md)记录精确适用消息、假设/输出版本、计时及停止规则。
正式warning门及旧报告不变；新入口先验证正式来源，只有四条精确OTHER_PROCESS消息才允许假设派生，
其余身份/边界/drain/同步/配置/诊断检查全部复用。输出单列scope_proven=false、trusted_a=false、
UNKNOWN/NOT_ASSESSED、CONDITIONAL_A_ONLY_NOT_ACCEPTED；D/Signature禁用，不改S/A/B公式。

实际接通manifest pair_id/pass_id到现有runner；pass0/pass1均显式解释器和相同输入/配置/host-readable边界，
新run/nonce独立，加载warmup/drain在窗外。host三个窗口按进程内相减，观察一次顺序配对delta/relative_delta，
零分母null、负差保留；不比较跨时钟时间戳，不声称纯因果开销或统计稳定。
producer输出token值序列未记录，parity仅固定输入/合同/实际输出数量和EOS，不伪称输出字节一致。

tests-first已见新入口缺失、pass0误标pass1、非法声明未拒绝、零分母/等边界及实际设备仅跨pass比对等失败，
最小修复后实际CPU producer文件链、独立手算A/开销预期及负例验证：9个相关文件141 passed/108.57s；
最后补充baseline warmup不得入窗检查后，pair/delivery两文件25 passed/21.28s。
改动Python compileall、diff-check及PowerShell5.1 AST解析通过；无全量、GPU或目标机验证。
审查确认默认正式路径不变、参数缺失/CPU失败阻止模型阶段、实际设备须匹配manifest而非仅跨pass相等。
现有封存四条消息与精确选择器兼容，仅做消息形状检查，旧formal仍BLOCKED，没有重分析或改写Raw。
本次使用新派生复用原计算，不另建分析器。稳定受控资格继续按影响复用，不重跑完整Q0/全量。

交付按服务器db9f028增量；先固定部署＋Git binary/配对/条件路径CPU定向复验，失败停止，
回执审查后才另启一次pass0→pass1。各审查时点一个ZIP，最终pair ZIP含两阶段全证据；无覆盖/自动重试。
服务器只核条件适用性并回传；本地回传审查后才生成独立条件性A。新型/其他冲突仍停止。
本轮不操作服务器、不执行GPU/Nsight/模型。Gate7 PASS、限定受控资格保持、旧BLOCKED不变、Gate8 NOT_RUN。
warning为已批准待决假设，不作为其余工作的前置；其余退出条件尚待本次目标平台证据，不能提前写已完成。

## 7.84 Gate8实际退出证据与warning门对应审查（2026-09-28）

一次窄询证记录为“用户回传已发送，待回复”；链接及核验边界见
[退出证据审查0.1](gate8_exit_evidence_review_v0_1.md)。本窗口未取得帖子回复、不追加发送或附件。
按route-a-execution/0.2五项退出条件收敛，不扩张历史待办。厂商回复不是本地审查前置。
本轮只读再次核对原ZIP hash/CRC及71文件与封存副本逐字节一致；直接SQLite查询三点、
窗外成功drain及三个内部/边界同步的原记录、身份、returnValue/correlation；复用既有双模式与A候选。
原记录复核不同于独立归属oracle；候选仍反事实，可信类别证据来自限定受控oracle/历史稳定Q0与负例。
已关闭本地证据索引、资格变更影响与分层机器状态审查。无新测试、监控、代码、服务器或采集。

当前任何warning拒绝符合已批准0.1显式条款，但它是保守支持限制，不证明本包全局丢失。
目标有事件/PID不同不豁免；额外要求排除所有想象得到的故障则超出限定支持域。
文档集中提出版本绑定局部诊断处置的待决范围/假设/反例，未修改准入、未实施放行。
三个剩余项分开：warning影响范围待裁决；f491d6e Git binary修复尚无目标平台复验；
该profile缺未profile同合同开销基线（NOT_MEASURED，不填0）。后两项不要求现在分批模型采集。
服务器未来至多合并相关CPU复验与经另行授权的一次匹配对照；当前不发部署包、不安排同配置重采。
唯一下一步为协调审查有限warning处置依据/支持假设；若不接受新假设且无新证据，停止可信模型链而非追加工程。
Gate7 PASS、限定受控资格保持、旧attempt BLOCKED、UNKNOWN保持；Gate8 NOT_RUN，D/Signature关闭。
本次仅文档记录，不改变冻结合同或数据资格；EP-G8-04仍未验收。

## 7.83 Git NUL预检fail-open最小修复与Gate8停点（2026-09-28）

用户裁决：询证继续暂停、不发送、不重采、不追索未知PID；7.82建议已结束，不再作为下一指令。
7.82[审计](gate8_isolated_attempt_audit_v0_1.md)及本修复同一提交。
仅isolated preflight两条Git NUL清单经现有adapter二进制读取并原样保存stdout/stderr，
主线程严格UTF-8/NUL解析；读取失败/None、非法编码、缺终止NUL、重复/越界、空tracked均拒绝。
ignored可合法为空；缺任一tracked文件仍拒绝，不通过空集合绕过。原始stderr不强制解码。
新增26项先RED；修复后相关5文件100 passed/22.65s，本地Windows/Python3.12.7；
含真实seal、临时Git仓库中文名、真实CPU二进制子进程及读取错误替身，compileall/diff-check通过。
未跑全量或任何服务器/GPU/Nsight/模型，无部署包。无MC/S/A/B/Q0/旧证据或warning门变化。
封存tree_hashes含486个tracked路径是事后核对，不追认缺陷运行时预检；warning阻塞独立存在。
现有证据只支持Engineering执行链/已观察边界身份/导出及候选计算验证；无法取得可信Qwen A、
模型资格或信息增益结论。停止资格工程扩张：复用受影响范围证据，不加监控、重复采集或资格层。
Gate7历史PASS及限定受控资格保持；Qwen attempt BLOCKED，Gate8 NOT_RUN，反事实不作为研究结果。


## 7.82 隔离预检attempt审计与证据路线停止（2026-09-28）

[有界审计0.1](gate8_isolated_attempt_audit_v0_1.md)：本地独立核验新ZIP/CRC/70清单及71解压文件不变，
执行db9f028；target53792/producer/采集/export成功，新preflight/claim/final绑定成立。
四条OTHER_PROCESS警告仍关联52740；现有SQLite及安装资料不提供宿主实例/排他影响范围，
停止同配置重采、重复来源记录/GUI；不从8→4条警告推断根因，也不豁免。
独立新目录反事实双默认流集合8/1906/3498及三窗口A一致；6171局部gap4730533ns约2.40%，
不发布可信A，不改分类、原BLOCKED/UNKNOWN或封存报告。
另以真实CPU子进程复现Git NUL文件名GBK位置4195错误；adapter stdout=None→空串存在
tracked集合检查fail-open风险，不把final PASS当成全部预检闭合。本包486个tracked路径均在tree_hashes，
仅补证集合覆盖，不追认运行时门。字节保全修复设计已记录，未实施/部署生产补丁。
唯一下一建议为协调审查是否解除一次四类消息范围窄询证的暂停；未批准不发送，
无明确答复维持停止，不安排新采集。Gate7 PASS、限定资格不变、Gate8 NOT_RUN；D关闭。


## 7.81 固定部署与原生设备adapter小检查交付（2026-09-28）

执行commit固定db9f028b1a7ceac40b9a110bfaacf6d613319638，服务器前置097f68a21eb9c75dbf390b7529a19c4316dda98e。
单一增量bundle已本地verify，44598 bytes，SHA256
`F9C467E34E640CB6B80AF87DDCD73799C1EEF92B744D949FED00A85A20473B30`。
机器路径与两个固定脚本仅在忽略的本地交付/交接中；不改变生产代码或执行commit。
第一脚本校验部署身份、9文件必要CPU定向回归后，以显式解释器/site及mask3直接调用一次
生产`cuda_identity_native(torch.cuda)`，记录实际UUID/PCI、版本、异常和退出码，冲突拒绝。
该步骤初始化CUDA，不是CPU-only；不加载模型、不推理、不运行Nsight。
第二脚本独立授权，必须先协调审查目标机回执；仍为单次原Qwen32/2、batch1、warmup1/repeat1、sdpa，
新manifest/预检/目录，不复用旧attempt；第一脚本不自动调用它。两者均单ZIP回传、失败不重试。
本地交付QA先RED后GREEN，4项CPU测试通过（成功/身份冲突/原异常及脚本接线检查），
两脚本PowerShell5.1语法检查通过；未重复全量或执行真实驱动/服务器/Nsight/模型。
CPU替身不证明native ABI或profile环境；小检查即使通过也不证明warning消失。
Gate7历史PASS、限定受控资格及旧BLOCKED保持；完整新Q0/Gate8 NOT_RUN，UNKNOWN保留。


## 7.80 保全身份的辅助预检外移（2026-09-28）

用户选择7.79备选2；[版本化执行合同0.1](gate8_isolated_preflight_v0_1.md)及最小本地实现完成。
原Git/mask/GPU身份检查在profile前真实执行；目标不运行Git/nvidia-smi，改核验一次性run/output/nonce
回执、当前文件/Git元数据、原解释器snapshot/模型清单/固定输入及进程内CUDA UUID/PCI。
目标设备数据来自Torch+CUDA Driver，不复制预期PCI；错误或冲突在模型前拒绝。
120秒双时钟新鲜度、排他claim、同prepared禁重试、目标与collector后检查防止已观察变化被接受；
Git观察角色明确为preflight，不伪称目标又查询过Git。保留无并发修改条件，不宣称抗恶意改后恢复。
tests-first覆盖真实文件入口/collector顺序、隔离CPU子进程、过期/错run/内容/设备等反例；
本地Python3.12.7相关9文件128 passed/48.40s（新增文件25项），改动代码compileall与diff-check通过。
未跑全量或服务器/GPU/Nsight/模型。native ABI仅CPU替身验证；本地临时Git仓库与隔离子进程是真实CPU执行。
自审确认新producer字段经argv/claim/target receipt/collector final向分析入口绑定，未删除warning门或改runner。
warning、三窗口、drain、模型必要行为、物理S/B及旧证据不改；6171局部gap不改分类。
一次新执行仅准备方案：固定交付commit/原Qwen32/2配置、新run、完整单ZIP，先协调审查；
不开展厂商询证或旧warning调查，不部署/重采。新adapter仍需真实目标身份核验，不自动继承资格。
Gate7 PASS、限定受控资格及旧attempt BLOCKED保持，UNKNOWN不改零，完整新Q0/Gate8 NOT_RUN。

## 7.79 来源记录方案可行性最后收口（2026-09-28）

[审查0.1](gate8_process_origin_feasibility_v0_1.md)明确结论B：不再追加来源设施、部署或重采。
成功路径可记录目标中两次Git及一次nvidia-smi直接子进程；prepare/probe、collector、
第三方/native/后代不覆盖，不能以三次调用指认旧两个PID。四类warning原行/字段与安装
UserGuide/ReleaseNotes/AnalysisGuide/schema notes逐项核对，没有足够的进程排他影响依据。
零事件消息可能与非CUDA/NVTX辅助用途相容，但不能抵消同PID的不完整/启动警告；
身份已知不等于安全，也不重启全capture零丢失认证要求。
有限备选为：经协调决定的消息范围窄询证（不发送）；重新设计将已知辅助预检置于profile外并
保全目标身份新鲜度（未批准/实现）；或暂停模型链claim。当前不能交付有把握补齐缺口的一次执行。
6171局部gap约4.99ms/2.78%保持反事实unattributed；低比例不支持warning豁免。
本轮仅源码/原SQLite/已传回资料只读审查及文档更新；不重跑CPU回归、不改生产或旧证据。
整理并正常推送ebdf4eb及本次文档提交；执行服务器仍097f68a，不跟随文档HEAD。
Gate7 PASS、限定受控资格及旧BLOCKED不变，UNKNOWN不改零，完整新Q0/Gate8 NOT_RUN。

## 7.78 有界进程来源实现与双模式反事实收口（2026-09-28）

用户批准的本地Engineering工作完成；[来源合同0.1](gate8_process_origin_contract_v0_1.md)
仅覆盖记录会话内platform_adapter主动启动的直接子进程，不覆盖第三方直接Popen、native或后代。
逐调用ID/父会话ID、实际Popen PID、父PID、解析启动文件、白名单用途、观察起止/退出码；
不记录argv/环境/输出内容。顺序PID复用可区分，重叠复用拒绝；不是OS出生时间或最终映像认证。
model-entry在成功退出前验证完整来源记录；记录失败不得成功，也不得覆盖原执行异常。
未记录来源仍UNKNOWN_NOT_ABSENCE，身份已知不自动豁免warning；无新增同步/模型操作。
tests-first覆盖成功、启动/子进程失败、缺失/损坏、IO失败、timeout、PID复用和入口集成；
本地Python3.12.7相关7文件98 passed，另有3个诊断算法等价检查通过。
compileall、contract 37/37、Canonical 7模块、oracle independence、diff-check通过；未跑全量或服务器实验。

[作用域审计补充](gate8_qwen_diagnostic_scope_audit_v0_1.md)在独立v0.2诊断目录完成：
LEGACY/PER_THREAD三sync必要后缀8/1906/3498项逐集合相等，三窗口A逐字段相等。
仅反事实省略diagnostic门，其余request门通过；full_request候选unattributed=4988324ns，
精确对应6171条既有局部API语义缺口，不转Host/residual、不新增API豁免。
原始未剪裁A第一模式与诊断优化结果逐字段相等；第二模式使用经独立等价检查的本地优化，
未改生产算法。原ZIP/SQLite hash不变，trusted_a=false、diagnostics_still_block=true。
仍缺PID10988/54228的可核验进程实例/角色及八条警告影响边界，旧attempt继续BLOCKED。
新记录不能补造旧事实，也不覆盖native；不默认部署/重采。下一项仅向协调窗口交付
来源合同及警告证据准入条件，先判断其能否补足实例关联和影响范围，未满足不安排采集。
不改冻结测量、物理S/B、Q0或历史证据；Gate7 PASS、限定受控资格不变，完整新Q0/Gate8 NOT_RUN。

## 7.77 新Qwen已有证据的诊断作用域审计（2026-09-28）

[有界审计0.1](gate8_qwen_diagnostic_scope_audit_v0_1.md)：直接核验26453554 bytes ZIP，
SHA256 7cc443d3b43882c1eb1160746bb5b81c91b979ab1afb2416c3bd679b87ded2fb，CRC/61项hash通过。
097f68a目标65784 exit0、producer/采集/export完成；collection仍MODEL_A_SCOPE_BLOCKED。
8 warning绑定10988/54228，库中仅注入线程/overhead，无宿主exe/parent/lifetime；
HostTimestamp警告不可直接与request trace时钟比较。代码子进程候选没有PID回执，不能指认角色。
未发现OTHER_PROCESS错配，影响范围仍无肯定证据，不修adapter/豁免warning，不改UNKNOWN。
原始request三锚点、成功窗前drain、窗内三次同步、3498个stream7活动及API返回已集中检查；
不把350条physical S INVALID直接当成request失败。完整physical S重算因耗时主动停止，
不冒称通过；原ZIP及封存副本逐字节hash复查不变。
复用封存physical S后的诊断门后续计算亦有界停止，未发布新A；默认流两模式完整计算
未复核完成，不能把原始必要条件检查写成条件A通过。离线summary显式记录该限制。
下一项仅审查本地CPU可验证的子进程来源receipt最小方案，不实施、不安排服务器/GUI/重采。
旧attempt继续BLOCKED，限定受控资格保持，Gate7历史PASS、Gate8 NOT_RUN。

## 7.76 目标CPU复验通过与新Qwen草案（2026-09-28）

直接读取服务器097f68a静态原件ZIP：1986 bytes，SHA256
e7ed49ca34638acd607f1aee4672dfcc73ae624bda0ce94286a24fb698305a0b；CRC及2项清单哈希通过。
Python3.11.16，29 passed/95.77s，compileall/show-check通过；receipt STATIC_PASS、最终clean。
两条deliberate receipt IO error是预期注入，不是新失败；不是Nsight环境或模型验收。
固定执行commit097f68a21eb9c75dbf390b7529a19c4316dda98e，沿用7.72模型/输入/GPU/backend及
32/2、batch1、warmup1/repeat1。只更新忽略的单次脚本：不部署、不重跑CPU测试，
新manifest与全新run；diagnostic-entry启动/异常/退出及stdout/stderr随完整目录单ZIP回传。
脚本仅PowerShell语法审查，无执行；协调窗口审查并取得单次采集授权后才可使用。
本次文档commit不是执行commit，不需服务器跟随或新代码bundle。旧attempt BLOCKED，
限定受控资格不变，Gate7历史PASS、Gate8 NOT_RUN。

## 7.75 备用错误输出不得覆盖主异常（2026-09-28）

直接读取服务器150b24a静态回传：ZIP 4127 bytes，SHA256
1478a706ebf9a389de478a4282f672b640b977c732989e7fbb7eb3e16934e193，CRC及3项清单复核通过。
服务器22 passed/1 failed，receipt BLOCKED；原RuntimeError→exit.json模拟OSError→
sys.__stderr__打印WinError6覆盖原异常。服务器尚未完成本轮静态复验。
tests-first增加无效句柄/关闭/None替身，覆盖原执行成功与失败，修复前4 failed/2 passed。
仅保护最后备用诊断输出，原执行失败保留同一异常对象；原执行成功则仍抛持久化OSError，
不得静默成功。保留原反例，不改snapshot门、采集或研究合同。
本地相关三文件29 passed/20.46s，改动文件compileall及diff-check通过；未跑全量或模型/GPU/Nsight。
单一增量包以前置150b24a交付审查，下一步仅目标CPU静态复验，不安排重采。
旧attempt BLOCKED、Gate7 PASS、既有限定受控资格不变、Gate8 NOT_RUN。

## 7.74 隔离CPU导入身份差异收口（2026-09-28）

真实base Python -I/-S子进程证明：probe仅导入snapshot依赖；model入口导入
gate7_smoke_validation时无条件重复插入repo sys.path，current精确比较因此拒绝。
随后runner导入无新增变化，PATH摘要及其他字段不变；CUDA未初始化，无模型加载。
先新增独立回归得到1 failed/1 passed，再仅将CLI路径bootstrap限制为直接脚本执行。
修复后全字段一致，人为重复sys.path仍拒绝，仓库外直接CLI仍可用。
六文件定向83 passed/35.69s，compileall四目录与diff-check通过；非服务器验证。
本地Python3.12.7结果不证明服务器3.11环境没有其他差异，不将本地缺陷认作旧失败唯一根因。
与7.73异常持久化合并为单一交付包，替代单独7201507部署建议；不安排部署/重采。
本地已充分复现，不新增服务器补证或诊断功能；未来目标平台先CPU回归，另行审查授权。
旧attempt BLOCKED/Raw不变，Gate7 PASS、限定受控资格不变、Gate8 NOT_RUN。
详见[入口失败审计补充](gate8_qwen_entry_failure_audit_v0_1.md)。

## 7.73 Qwen入口失败有界审计与持久化异常（2026-09-28）

[入口审计0.1](gate8_qwen_entry_failure_audit_v0_1.md)：直接核验32187 bytes封存包，
SHA256 603d650baa40f3afc7b80aa069072cecdd125194c6322ac0c911dc9c0e4683d7，27项hash/CRC通过。
Nsight exit1/16.75s无timeout，REP存在但无diagnostic，不能推断模型已运行或PATH坏。
REP字节中压缩输出片段指向runtime snapshot guard；未完整解码，不证明具体差异字段。
本地tests-first补diagnostic-entry启动/异常/退出及stdout/stderr持久化，snapshot差异仅诊断，
不放宽比较；原始异常保留。旧attempt BLOCKED、限定受控资格不变、Gate8 NOT_RUN。
3个新增回归先失败，另一个IO失败负例先暴露成功路径吞错再修正；最终四文件50 passed/21.57s。
真实isolated CPU子进程验证argparse SystemExit2原样记录且runner未导入；独立sentinel和IO反例
验证原异常优先/不得假成功。compileall与diff-check通过；没有GPU/Nsight/模型或全量测试。
下一步仅协调窗口审查诊断增量与CPU静态复验范围，不执行服务器或新profile/模型。

## 7.72 单Qwen A-only入口审查与本地衔接（2026-09-28）

7.71审查/进度/公共handoff已同次提交3d7ef52并推送。当前按用户授权完成
[单Qwen执行审查0.1](gate8_qwen_a_only_execution_v0_1.md)：32/2、batch1、warmup1/repeat1、
sdpa/qwen2、固定模型清单与prompt，prepare及目标进程重新hash模型；显式Python身份写manifest，
模型前重验、producer/trace PID绑定后自动进入既有Engineering A-only门。旧诊断路径保留。
不改变runner同步策略、S/A/B/Q0/Measurement Contract；不豁免外PIDwarning，不重判旧attempt。
本地新增失败回归先复现内容仅查大小、身份冲突仍加载、argv仍venv路径，再最小修复。
CPU替身验证实际模型producer→receipt→Canonical→A衔接，不是新服务器/model验证。
六文件定向106 passed/97.62s；compileall四目录、contract37/37、Canonical7、oracle静态独立性、
diff-check和PowerShell Parser通过。新增集成fixture先暴露诊断表列数不全，补齐测试原始schema后
通过；该测试准备错误不是服务器问题。不跑全量或GPU，不把本地结果当新模型证据。
下一项为协调窗口审查固定bundle与单次采集命令，尚未授权服务器执行；Gate7 PASS、
完整新版Q0/Gate8 NOT_RUN，限定受控A-only资格不扩成模型资格。

## 7.71 路线A限定新版资格覆盖收口（2026-09-28）

[覆盖审查0.1](gate8_bounded_qualification_review_v0_1.md)判定限定Engineering A-only资格PASS：
执行8ef1385、离线cb4b3b3/oracle0.1.2；共同点/身份、drain、默认流条件后缀、六窗口具体A
由真实受控trace证明，缺点/映射/身份/未知诊断拒绝复用独立负例。Gate6只复用历史稳定S/A/B
结论，不自动授予新版本；完整新版Q0总状态/Gate8仍NOT_RUN，Gate7 PASS。
本轮53个输入与ZIP字节一致、既有派生hash匹配；不改Raw或原BLOCKED报告。
UNKNOWN/NOT_ASSESSED和支持域假设保留，不是模型/全capture零丢失/正式科学验收。
限定子集无剩余必要补证，停止本轮审查；下一步是最小模型方案授权前审查，不默认重采。
本轮四文件CPU回归79 passed/97.14s、diff-check通过；仅文档变更，未操作服务器。
按用户随后授权将7.71审查、进度及[脱敏公共handoff](current_handoff.md)同提交推送；
根AI_HANDOFF.md含私有历史路径，继续忽略，本地同步而不强制加入Git。

## 7.70 drain API后缀最小适配及封存副本离线复验（2026-09-27）

[审计0.1](gate8_drain_api_reanalysis_v0_1.md)：8ef1385执行包246133 bytes，ZIP SHA256
42c40987ae982e9887a5fb2dde0785759d6421ba52efcdae476ee9cb4c3703a5；CRC/安全路径/52项清单独立通过。
原attempt因DRAIN_API保持BLOCKED；两drain为成功cudaDeviceSynchronize_v3020及关联context sync。
tests-first复现后，oracle0.1.2仅对该名称接受可选ASCII数字版本后缀，不放宽身份/warning/sync。
定向51 passed/41.84s；compileall、contract37/37、Canonical及oracle静态检查通过，未跑全量。
原件副本上新版本派生CONTROLLED_SCOPE_MATCH：身份、drain、双默认流条件后缀、六窗口具体A分类
均与独立oracle相符；53个输入文件hash不变。14条info无warning不是零丢失证明；UNKNOWN和
NOT_ASSESSED保留。事后修复不授予新Q0资格，不追认旧attempt，不运行服务器/GPU/Nsight/模型。
下一步仅审查离线结果和资格覆盖，不安排重采；Gate7 PASS，新Q0/Gate8 NOT_RUN，D关闭。

## 7.69 显式目标Python身份链与独立枚举修复（2026-09-27）

用户批准限定本地实现，[目标Python合同0.1](gate8_target_python_v0_1.md)：显式base解释器与
venv purelib、隔离bootstrap、CPU nonce/Popen→实际PID及环境probe，plan封存；producer在
native加载前重验snapshot，execution→pass PID绑定；原Nsight启动通知/完整global PID与producer
在export后绑定。新qualification0.2只接新计划，旧0.1及失败attempt不追认。没有warning白名单，
缺通知/冲突/环境差异仍拒绝；不是认定venv为旧warning根因，不保证未来warning消失。

独立oracle0.1.1只有限映射两类sync的完整/短枚举名，未知名拒绝；不改S/A/B或冻结registry。
tests-first先复现缺adapter、实际全枚举失败、计划缺身份和collector关联缺失，再最小实现。
真实CPU隔离子进程使用测试native替身调用实际producer文件链，Popen/运行时/ledger PID一致，
篡改后拒绝；无GPU/Nsight/模型/native执行。跨机器离线reader不以本机路径误拒服务器产物。
最终六文件定向88 passed/88.34s；包括真实CPU子进程、实际producer落盘、全/短枚举、
既有warning拒绝、默认流/Engineering接口及后处理回归。compileall四目录、contract37/37
（内部一致性）、Canonical7、oracle静态独立性、diff-check及PowerShell Parser检查通过。
没有重跑CPU全量、native编译或目标机检查，不将本地Python3.12验证冒称服务器3.11资格。

原7.67/7.68审计与用户GUI回执同步保留；原ZIP/REP/report未改，变化后服务器REP不是封存原件。
下一项仅协调窗口审查固定commit、基于d4865d0的单bundle和整段新受控执行草案；本轮不部署，
不授权采集。Gate7 PASS，新Q0/Gate8 NOT_RUN，D/Signature关闭。

## 7.68 GUI补证结束、受控attempt停止资格判定（2026-09-27）

用户回传GUI内容：55192有GPU/NVTX，60628有Profiler overhead，四警告位于60628，
两进程均information not available。没有程序名/父子/生命周期及警告局部影响证据。
本窗口未直接读取截图；补证仍不足，attempt保持BLOCKED，结束7.67补证，不再要求服务器操作。

用户回传REP打开前90424 bytes/C6B2630B3DB4AE53A1E145D6032AA7EF8F55FDA73325B0B04B1833CC0146FBC8，
关闭后90405 bytes/B39FA8EDF6E459FA79CC5F6136697C1B75F76B977D222D51675BEFA83A8854E3，
LastWriteTimeUtc=2026-09-27T13:39:16.2560288Z，无残留nsys/nsys-ui。
变化后REP未本地取得，不推断改动原因；不能冒充原件或替代原SQLite/export lineage。
封存ZIP仍243486 bytes/39667BEE6D8576EA1BAB3875E52A67C1AF1720CD084152F9C9160A006D98234D，
内含打开前REP。本轮再次本地核验该ZIP和内嵌REP身份，原件不改，不请求差异分析或重复采集。

[审计追加收口](gate8_qualification_warning_audit_v0_1.md)只提出一个后续方案：本地设计
显式目标解释器启动合同，先以CPU替身验证启动端/执行端与环境身份，不借此豁免warning。
仅方案待审，不实施或授权服务器执行。短sync枚举名适配独立待修，不解决警告范围。
本轮文档同步，无生产代码/合同/测试/采集变化；Gate7 PASS，新Q0/Gate8 NOT_RUN，D/Signature关闭。

## 7.67 d4865d0受控资格失败包只读审计（2026-09-27）

直接审计243486 bytes ZIP（SHA256 39667bee6d8576ea1bab3875e52a67c1af1720cd084152f9c9160a006d98234d），
CRC/安全路径/52文件与51项清单精确集合及hash通过，SQLite在内存只读检查integrity=ok。
服务器d4865d0 clean、定向51 passed/33.97s、DLL构建与producer COMPLETE；4 token/6 boundary/2 drain，
Nsight exit0无timeout、一次export PASS。是本地审计服务器回传，不是本窗口执行GPU/Nsight。
collection仍BLOCKED，无qualification.json；不得把前段成功写成新Q0或A资格。

[warning审计0.1](gate8_qualification_warning_audit_v0_1.md)：19行诊断中的row3/4/6/7均Analysis warning，
关联profiler直接启动端PID60628；目标55192有独立注入/活动。消息涉及NVTX可能缺失/无NVTX与
CUDA启动可能失败/无CUDA事件。HostTimestamp不能裁目标trace窗；包内缺完整parent/image/lifetime
和诊断局部作用证据，“仅venv转发器”不能由PID不同或零事件推出。
当前all-warning拒绝符合已批准0.1实现及影响不明拒绝原则，不等于研究上永久禁止范围处置。
证据不足，本轮不改代码、不绕过warning离线验收、不重复测试或采集；原ZIP/REP/report不改。

唯一下一项：从同一REP只读GUI进程/诊断详情补60628→55192角色关系及四消息影响边界，若
属性不可得或仍未证明即停止，不自动重采/询证/更换collector。另记录oracle短sync枚举名与
实际全前缀枚举的适配风险，未执行到、不冒称warning是唯一潜在缺口。本轮仅文档同步。
Gate7 PASS；新Q0/Gate8 NOT_RUN；UNKNOWN不改零，D/Signature关闭。

## 7.66 新profile受控资格连接器及独立oracle（2026-09-27）

从682afcd按已批准qualification-next/0.1完成本地tests-first最小实现，说明见
[受控资格0.1](gate8_controlled_qualification_v0_1.md)。新NULL-FIFO-D2H/0.1.0，两个顺序request各两token，
窗外分配/暖机、真实drain、内部同步、三点completion与固定操作声明；不用旧入口改名或伪造模型backend。
实际producer落盘→封存receipt→合成SQLite→Canonical/projection→限定Engineering A已连通。
独立stdlib Raw oracle不调用S/A，逐项比较必要后缀集合和六窗具体五类，不以总和闭合冒充归属正确。

先RED再修复的覆盖包括缺入口、manifest重哈希脱离plan、pre-native GPU冲突、工具build前缀误接受、
缺物理drain、正确token跨身份、sync枚举编号变化、相同A但错误后缀集合；缺边界/correlation/warning拒绝，
局部两API缺口保留unattributed。假设与观测分离，dropped UNKNOWN/NOT_ASSESSED不改零。
全部新增trace为CPU确定性fixture，不是实际CUDA/Nsight完整性证明；没有本轮服务器/模型/native执行。

验证：资格专项19 passed/17.27s；接口三文件42 passed/71.00s；扩大到request/default及旧受控链
六文件99 passed/70.07s（后续增加的后缀集合反例由最终19项专项覆盖）。CPU全量1472 passed、
5 skipped/374.55s，Python3.12.7、同进程mask=-1且移除nvcc PATH并断言不可见；五skip为既有
native编译测试。全量收集后新增的枚举/集合两例单独通过，不冒称已包含在1472中。
compileall四目录、contract37/37（仅内部）、Canonical7、oracle静态独立性、diff-check通过。
PowerShell交付段仅Parser语法验证，无本机native/GPU/Nsight/服务器执行。
目标机资格尚未执行。下一项仅固定本提交及单一增量bundle、
在既有固定checkout做最小受控编译/执行并回传单一ZIP（命令已准备，不由本窗口执行）。
任何未知作用warning、缺证据、额外stream/活动、oracle不符或超时停止，不自动重试。
原物理S/B、旧Q0/旧Qwen/历史证据不变；D/Signature关闭；Gate7 PASS，新Q0/Gate8 NOT_RUN。

## 7.65 247f4fd目标机静态回执审计及最小资格下一步（2026-09-27）

直接只读核验用户传回单ZIP：4680 bytes/SHA256 fc129db5a104ce8e052f56512a6bab292bddbd12c670a260f57d98fa2c0b41d3；CRC/路径/8文件精确集合与清单7项bytes/hash全部通过。清单SHA256 fa10caa43c662893f08e3d3af7d43db8f58246fce0e748bb562c483f90bf4ce0。原始日志95 passed/42.63s、Python3.11.16；receipt六步exit0/STATIC_PASS，contract37/37、Canonical7、oracle静态独立性通过，compileall成功来自receipt而非不存在的单独日志。部署verify/fetch/checkout控制台证据为用户提供、不在此transcript；不是本助手服务器执行。服务器部署基线现为247f4fd211007b7dfc2ef011043d7ecebdbf6f88，不再写待部署/待静态复验。

[下一步备忘录0.1](gate8_engineering_qualification_next_v0_1.md)区分历史公式资格、目标机确定性接口与新profile受控资格：新编排仍缺受控资格封套，不用旧SOURCE_DIAGNOSTIC_ONLY入口伪造模型backend或补写旧receipt。下一项主窗口本地准备限定受控构造与独立oracle；本轮仅规划、不扩实现、不重复静态或模型采集，暂不需要服务器动作/新包。

旧Qwen SQLite只读确认8条warning确为两个外global PID；目标producer/Runtime/Kernel一致不证明外进程无依赖。HostTimestamp不可直接裁目标trace窗；现有进程关系及诊断作用域不足，继续IMPACT_UNBOUNDED，不当作目标已丢失、不豁免、不重判。旧Raw/报告不变，D/Signature关闭；Gate7 PASS、新Q0/Gate8 NOT_RUN，Protocol Freeze/Formal资格无变化。详见备忘录逐项来源与停止点；文档收尾commit不要求服务器追随main。

## 7.64 限定Engineering质量门及真实A-only文件编排（2026-09-27）

接续0ce3aec完成[限定依据0.1](gate8_engineering_sufficiency_amendment_v0_1.md)的本地实现：显式prepare声明、目标进程设备probe/runner字节、实际setup backend核对、execution receipt、封存input receipt、Canonical/D1、逐request质量门、LEGACY/PTDS条件性交集及A-only结果/重算reader。无静默启用；旧Qwen诊断无此声明不追认。支持域假设与原始事实分字段保存，dropped UNKNOWN不改零。

检查边界/drain、完整global PID、设备/context/clock、全部已观察API及physical-sync、submission correlation、stage/setup、单实际NULL FIFO、逐sync完成和唯一frontier。内部sync无独立marker时仅复用既有dependency recovery构造A交集输入，不伪造callsite，不修改原物理S/B。局部两API分类缺口保留原interval和unattributed，其余未知作用/缺物理映射/冲突/未界定diagnostics均拒绝，不转Host/residual；独立request结果可保留但run BLOCKED。D/Signature关闭。

Tests first独立正反例覆盖signed时间、多request、完整producer→实际落盘→合成SQLite→Canonical→A、backend冲突前置停止、默认条件等价/其它流反例、局部分类缺口、全局/外PID警告、缺边界/drain/correlation/physical sync、跨global namespace、结果篡改、partial不发布及CLI防覆盖。手算request [400,600)的五类预期=(130,10,40,20,0)ns；[420,425)分类缺口后=(125,10,40,20,5)ns。初始缺入口/receipt、跨namespace错误准入、target零计数冲突、未知collector版本、sync已返回但必要活动未完成、CLI缺产物分别有RED→GREEN。两个API未扩展冻结registry：只界定成功原调用的分类缺口，不声称GPU永不阻塞或零丢失。

最终验证：六文件定向94 passed/64.70s，最后CLI及completion反例2 passed/11.64s；CPU全量1455 passed、5 skipped/319.49s（本地Python3.12.7），五skip均为既有nvcc编译门。compileall四目录、contract内部37/37、Canonical7模块、oracle静态独立性、diff-check及修改文档链接通过。独立review发现逐sync completion漏检，补回成员end≤sync返回和唯一frontier后关闭。首次全量1455 passed、1 failed、4 errors（329.91s），五项均为未改动的旧Q0原生编译路径，本机CUDA13/MSVC出现C4819及连锁语法错误，未运行GPU程序；PowerShell PATH过滤未传入Python生效。最终按既有CPU验证方式在同一Python进程过滤nvcc并断言不可见、mask=-1后复跑；不改测试skip、不声称本机native编译或目标机通过。所有新增trace为确定性合成输入，未使用合成零丢失证明授予资格。

剩余：实际Nsight目标机新版本资格未验证；旧包的外PID warning影响范围仍无肯定依据，新门会拒绝，不能因此盲重采。没有通用warning局部化或丢记录补全能力。最小服务器动作至多固定新commit的CPU静态复验；新受控Q0及模型采集仍待单独授权/明确必要证据。单一bundle交付、回执单一ZIP，不重新索源/全capture认证。Gate7 PASS、新Q0/Gate8 NOT_RUN，旧证据及Formal资格不变。

## 7.63 限定Engineering依据批准及来源诊断入口（2026-09-27）

用户已接受7.62的限定依据，版本化为[Engineering sufficiency amendment 0.1](gate8_engineering_sufficiency_amendment_v0_1.md)。不要求全capture认证；目标必要依赖风险、支持域假设与可观察事实分开，OTHER_PROCESS不能自动豁免。仅未来预声明profile的新attempt适用，旧诊断不追认。旧合成request_scope及物理S/B不改，新真实路径不以零unattributed为条件；未知影响范围仍拒绝，B/D/Signature不自动发布。

第1段已实现diagnostic-scope/0.1.0来源sidecar：实际producer NVTX与pass ledger绑定完整global PID，保留原诊断row/hash/time/type；同数字PID不同namespace、负系统sentinel和缺字段不猜测。reader重新派生，不允许改写事实；非空WAL/journal输入拒绝，immutable读取且不改Raw。timestamp_raw不假定时钟/单位。全部影响保持UNASSESSED、dropped UNKNOWN、scientific_outputs_allowed=false。

tests-first：初始缺模块、跨namespace、WAL旁路和未定义时间单位均有失败回归后修复。当前11项新测试通过；来源/identity/stage三文件45 passed；含旧S/A及request_scope的五文件162 passed（时间字段反例加入前），最后11项复跑5.02s。compileall四目录、contract内部37/37、Canonical7模块、oracle静态独立性通过；不是目标服务器或新Q0验证，未重跑全量。独立review发现WAL hash旁路后已修复。

下一项仍为第2～4段：显式profile/receipt与逐窗口真实quality gate、受限默认流A-only交集编排、两API有限对齐。尚未完成，不可把本段sidecar成功当成真实A准入。无部署/模型/GPU/Nsight，Gate7 PASS、新Q0/Gate8 NOT_RUN；Protocol Freeze/Formal资格不变。

## 7.62 默认流三sync证明义务及独立回归（2026-09-27）

接续7.61，在既有S→A上补七项独立手算正反例：单FIFO条件性A相同、另一个blocking stream使同terminal不同A、漏掉该活动仍可能假闭合、mode局部unknown与不可界定整窗风险分别传播。详见同一审计文档7.62。没有新增生产算法：当前批准amendment仍明确合成basis/非默认流，真实来源必要依赖闭合不能由本包观察集合自证，不删除SOURCE_NOT_QUALIFIED或DEFAULT_STREAM_NOT_SUPPORTED。实际文件拒绝及旧S/A回归同步检查，不授新Q0资格。无服务器/采集，Gate7 PASS、新Q0/Gate8 NOT_RUN。

本地Python3.12.7验证：新增7 passed/0.27s；四文件定向152 passed/31.26s（新测试、request_scope、旧sync_semantics和a_accounting），mask=-1；新测试compileall及diff-check通过。本轮没有生产修复，新增测试首跑即通过是既有语义回归，不声称RED→GREEN。未重跑全量或新目标机验证，不改变冻结公式/旧schema/独立oracle/历史资格。

独立只读review无重要问题；补terminal identity断言后7 passed/0.26s。原ZIP内存条件性A原型已收口：完整已观察FIFO假设下full A=(81223925,81122141,21184,122380,3050445)ns，不是S准入或科学发布。精确定位两种未分类API贡献3050445ns；下一项独立工程工作是这两API的版本化分类核对，不需要服务器。集中研究待决候选是目标scope有限正证+显式残余风险的Engineering充分性依据，尚未生效，不恢复全capture认证、不追认本包。

## 7.61 真实Qwen单次诊断已回传，只读范围审计（2026-09-27）

服务器已执行35b5bff单次诊断，不再是“尚未部署”。本地直接读单ZIP：27源文件/28项大小hash/CRC、producer四文件与输入副本、内存SQLite integrity通过。详见[审计v0.1](gate8_qwen_diagnostic_audit_v0_1.md)。三trace point/成功drain/三stream sync齐全，request marker窗口165540075ns；内部1-byte D2H及两token copy实际存在，不能仅凭这些事实发布A。设备physical3→logical0→inventory2有UUID/PCI链。目标外两PID警告保留，dropped UNKNOWN、native backend UNKNOWN；无合格S/A/B/D或新Q0资格。仅审计和文档更新，无新测试/服务器/GPU/Nsight执行，原件不变。下一项本地三个sync的target-scope受证条件清单，不盲重采或重复索源；Gate7 PASS、新Q0/Gate8 NOT_RUN。

## 7.60 Windows Nsight kill参数修复（2026-09-27）

本轮验证：Windows argv回归先FAIL后修复；collection/entry/postprocess三文件45 passed/34.98s。compileall四目录、contract37/37、Canonical7、oracle独立性、diff-check通过，独立只读review无新增重要问题。未重跑全量；7.59的1410/5只属于上一实现验证，不算本次新全量。该改动不触及runner/科学analyzer/冻结合同。新包仅以服务器已部署4d8fe10为前提，后续新目录/新run，旧BLOCKED不变。

直接读取回传原件：4d8fe10单次诊断在Nsight参数解析被拒，stderr明确Windows kill只接受true/false；PID27548，exit1，0.219s，未timeout，attempt1，stdout空；collection仅4个日志/report，无REP/SQLite/producer，未进入模型target。prepare/verify成功包含最小CUDA初始化，不能说全程零GPU交互。目标安装UserGuide Windows段与此一致；7.59误采用Linux sigkill是工程平台参数错误，不是模型或科学语义问题。最小修订v0.1.1：Windows argv为kill=true，保留120s/300s、单次profile/export、不重试和NOT_QUALIFIED；Linux仅argv回归，不新增平台支持。新增Windows失败回归已复现旧值；旧attempt保持BLOCKED，服务器现4d8fe10。Gate7 PASS、新Q0/Gate8 NOT_RUN；本地不执行真实Nsight/GPU。

## 7.59 单次Qwen诊断本地实现（2026-09-27，CPU验证完成）

按继续推进授权完成[诊断入口v0.1](gate8_qwen_diagnostic_v0_1.md)：新prepared manifest/prompt/preflight、固定32/2 batch1 warmup1/request1、原producer文件链与loaded config，NOT_QUALIFIED，真实A/B/D禁用。旧load fallback默认保留，新诊断单次；export默认两次保留，新诊断max_attempts=1。模型历史清单hash+当前大小/集合，不重复3GB内容哈希。minimal profile有界等待/失败保存/不重试；超时不声称后代已退出，保留BugCheck风险。定向先RED后GREEN，复审身份字段/根路径/alias及落盘失败进程监管均补反例；最终CPU全量进行中。未部署服务器、未运行模型/GPU/Nsight，服务器仍f5；Gate7 PASS、新Q0/Gate8 NOT_RUN。

验证收尾（覆盖上段进行中）：Python3.12.7本地定向71 passed/23.90s；CPU全量1410 passed/5 skipped/292.84s（进程mask=-1且nvcc不可见，5项为既有CUDA source检查，未改skip）。前两次全量在review修复时中止，不计通过；初次timeout fixture启动预算不足已改隔离解释器与2秒预算，最终通过。compileall四目录、contract37/37内部一致性、Canonical7模块、oracle静态独立性、diff-check通过。复审问题均关闭；两段服务器草案仅AST解析通过：A纯CPU static，verify移到B mask3阶段，明确可能初始化CUDA；不是目标服务器成绩。没有修改Measurement Contract、S/A/B/Derived公式、Q0 oracle或历史证据。当前下一项由协调窗口审核固定包并指导用户先A静态，核原件后再B单次诊断，不再静态索源。

## 7.58 最新限定来源审查（2026-09-27）

七文件服务器原件已直接读取；服务器静态exit0/f5前后clean，协调窗口独立核验10文件/内部8项hash。详见[限定审查与单次诊断路径](gate8_qwen_source_review_v0_1.md)。prefill SDPA fast_all的布尔求值是旧1-byte D2H/第三sync候选，不是已证实callsite；实际backend/native mode/迟发保持UNKNOWN。停止进一步静态索源。下一项仅本地窄诊断入口封装现有run_gate8_requests（legacy CLI不启用它），CPU fixture核实身份/文件产物后提出一次NOT_QUALIFIED真实Qwen Engineering诊断授权；不以科学资格未通过禁止探索，也不将探索当资格。无新GPU/Nsight、无生产代码变更、未重跑测试；Gate7 PASS，新Q0/Gate8 NOT_RUN。

> 一句话状态：**Gate 0～7 = `PASS`；服务器35b5bff已完成单次NOT_QUALIFIED Qwen诊断，本地已核原包、三D1点/三sync/null stream与身份。真实source依赖范围仍未证明；七项独立条件性正反例不授Q0资格。物理S/B不改、UNKNOWN不改零、D/Signature不放行；新Q0/Gate8=`NOT_RUN`，不再重复索源或盲重采。**
> 本文件是仓库内**唯一的科研进度事实源**：记录“现在做到哪里、证据在哪里、下一步是什么”。研究设计文档说明“为什么做、应该怎样做”。

## 0. 项目速览与交接入口（第一次接手请先读本节）

### 0.1 研究对象、立意与目标

- **研究对象**：单 GPU、单请求内部的异步 Host 与加速器执行，如何经由同步与完成行为形成**用户可感知的纯模型推理时延**。
- **核心区分**：`Activity Cost ≠ Request-Visible Exposure`。kernel 时长、API 时长、GPU 利用率、时间重叠都不能直接解释为延迟贡献。
- **目标**：建立可机器验证的 `Raw → S → {A, B} → D / Exposure Signature` 证据链，并用 `Correctness → Information Gain → Decision Gain` 三段证据回答三个问题：暴露在哪里、这些暴露是否可解释或可预测、能否指导决策。
- **范围边界（未经明确批准不得扩张）**：单 GPU、请求内部 Host-device exposure。不扩展到多 GPU、分布式 serving、并发 ownership、硬件因果归因或通用性能预测。

### 0.2 方法链与不变量

| 层 | 回答的问题 | 关键不变量 |
|---|---|---|
| Raw / Canonical | 观测到了什么事实 | 只记录可观察事实与 identity/clock/lineage；缺证据 fail closed，不补零 |
| S | 同步点 `s` 返回前**必须**完成哪些活动 | `W(s)` 由 CUDA 完成语义决定，不由时间重叠决定；terminal 只在证据充分时唯一 |
| A | 用户可见墙钟暴露在哪里 | 按 request/phase 互斥、保守、整数纳秒守恒；窗口只来自结构化 request/phase |
| B | 单次同步内部发生了什么 | per-sync provenance，validity 未通过时全部为 null；不得跨同步求和 |
| D / Exposure Signature | 顶层导航与机制摘要 | 只从冻结后的 A/B 纯派生，不构成硬件根因结论 |

### 0.3 数据角色与平台边界

- **数据角色**：`Prototype` / `Engineering` / `Pilot` / `Formal` 严格分开；复制、改名或重新分析都不能提升资格。当前只有 `Prototype` 与 `Engineering` 数据，**无合格 Pilot/Formal 数据**。
- **当前唯一声明的目标 observation stack**：Windows + RTX 4090（UUID `GPU-0d8fafe6-a1e9-33cc-25fb-632316736455`）+ CUDA 12.4.131 + Nsight 2026.2.1 + package/analyzer `0.2.2`。Q0 资格只在该栈上取得。
- **第二平台（含 Linux）**：不声明支持；其 launcher、smoke、平台资格检查与 Q0 属 Gate 9。任一平台未通过该平台的真实 smoke 前不得声称受支持。
- **平台边界（代码位置）**：Python 侧唯一平台边界是 `exposedpath/platform_adapter.py`（工具解析 + 结构化 argv + fail closed；包内仅此模块导入 `subprocess`）；Windows 启动层是 `scripts/*.ps1`。runner/manifest 核心保持平台无关，新增平台能力不得绕过该边界。

### 0.4 文档地图（按接手顺序）

| 路径 | 作用 |
|---|---|
| `docs/current/ExposedPath_研究设计.docx`（文内版本 v7.1） | 研究主体：背景、立意、目标、方法与成败判据 |
| `docs/current/ExposedPath_实验协议.docx`（文内版本 v2.1） | 当前执行依据（仍为 `Pre-Pilot`，不是 Protocol Freeze） |
| `AGENTS.md`、`.agents/skills/exposedpath-research-protocol/` | 仓库协作规范与研究协议 skill（含 `references/method-semantics.md`、`references/stage-gates.md`） |
| `CONTEXT.md` | 统一研究语言：该说与不该说的术语表 |
| `docs/v1_4_1/measurement_contract_v0_2.md` + `docs/v1_4_1/contracts/*.json` | 机器合同与版本化 schema（Measurement Contract / Canonical / S / A-B / Derived / Q0） |
| `docs/v1_4_1/q0_oracle_design_v0_2.md`、`q0/oracle_cases_v0_2.json` | Q0 独立标准答案（23 个必需 case） |
| `docs/v1_4_1/gate6_closeout_v0_1.md` | **Gate 6 论文级技术总结**：身份/哈希、根因→amendment→implementation→verification 映射、成熟度与遗留限制 |
| `docs/v1_4_1/gate7_closeout_v0_1.md` | **Gate 7 Engineering closeout**：唯一合格fresh身份、逐项验收、原始diagnostics审查及legacy-only限制；不是Gate8科学全链验收 |
| `docs/v1_4_1/gate8_interface_gap_audit_v0_1.md`、`docs/superpowers/plans/2026-09-25-gate8-minimal-execution-plan.md` | 当前Gate8实际接口审计、集中待决项与最小分阶段计划；不构成实施/采集授权 |
| `docs/v1_4_1/gate6_windows_server_runbook.md` | Q0 正式服务器采集／导出／派生／provenance 操作手册 |
| `docs/superpowers/plans/2026-09-20-gate7-execution-plan.md` | 当前 Gate 7 执行计划（`EP-G7-08`～`EP-G7-11`） |
| `docs/v1_4_1/candidate_platform_inventory_v0_1.md`、`candidate_platform_admission_checklist_v0_1.md` | 第二平台静态盘点与冻结的准入判据（仅在 Gate 9 需要时启用） |
| `docs/prototype_archive/README.md` | 旧 Prototype 封存说明（历史数据只能用于回归，不能作为 v1.4.1 证据） |

### 0.5 30 分钟接手路径

1. 读本文件 §0～§2 与 §6～§7：当前状态、Gate 状态、下一步。
2. 读 `docs/current/ExposedPath_研究设计.docx` 第 1 章（背景与立意）与 `docs/current/ExposedPath_实验协议.docx`（执行语义）。
3. 读 `CONTEXT.md` 统一术语，再读 `AGENTS.md` 与 research protocol skill 的 `method-semantics.md`。
4. 需要看实现时：`exposedpath_v141/`（Canonical/S/A/B/D/Q0 计算与 CLI）、`q0/`（微程序、manifest、oracle）、`tests/`。
5. 需要复现 Gate 6 结论时读 `gate6_closeout_v0_1.md`；需要重跑 Q0 时读 runbook（**不得**在未获批准时重跑 Gate 6 采集）。
6. Gate7已关闭；不重启EP-G7-08～11。Gate8局部受控采集及离线复验已有分次授权与回执，当前读本文件§1最新状态和controlled adapter审计；不自动授权下一次服务器操作或真实模型采集。

## 1. 当前快照

- 清单版本：`7.119`（下方较早逐条记录为历史；当前状态以顶部7.119及Gate摘要为准）
- 7.57路线收敛：[Route A执行/退出v0.2](gate8_route_a_execution_v0_2.md)把未来Gate8结论限定A_SCOPE_ENGINEERING_ONLY的五项实际证据，B/Derived后移，不冒充旧全链通过、不设真实unknown=0门。runner未固定attention backend，旧1-byte内部D2H/sync须纳入T；本地已知selector可能默认SDPA。复用快照工具新增qwen-request/0.1选择、回执0.2，限定7源文件；不读DLL/模型、不导入目标包。先RED后实现，21项工具测试（含隔离子进程禁止包导入/native/网络）及compileall/diff通过；未重跑核心全量，7.55的1379/5结果只属于当时实现。仅准备一次目标来源补证，无部署/实验；回传仍不能闭合必要依赖则停止，不扩搜索。
- 7.56有界只读收口：[默认流后缀等价备忘录](gate8_request_suffix_equivalence_review_v0_1.md)。直接只读旧QwenSQLite：每候选request有3492K/3copy/3memset及3次stream sync，额外内部同步不能只按Token标签忽略；已记录Q同TID/context/NULL stream，不等于无遗漏。严格受证单FIFO Q条件下W_Q/唯一terminal/A可条件等价，W_full/B历史仍可能不同；独立反例显示另一blocking stream会使wait40与10不同。现有producer/资料未证明来源闭合，当前没有单个现成充分补证，不建议重复采集或再传泛化安装包。0.1实现及合同不改，服务器无动作；Gate7 PASS、新Q0/Gate8 NOT_RUN。
- 7.55当前实现：[request/drain A范围amendment 0.1](gate8_request_drain_scope_amendment_v0_1.md)。用户批准前缀完成证书＋合格Q独立A资格；旧MC正文及S/A-B/Q0不改。新增文件入口/显式reader，保留原physical S/B，后缀证明不冒充W；源身份、真实drain scope、时序、资源重建、跨线程/迟发、后缀S失败均拒绝。仅SYNTHETIC_CONTROLLED_ORACLE来源，本地确定性验证不是新Q0资格；真实来源SOURCE_NOT_QUALIFIED，默认流尚不在首版支持域。collector暂停，无服务器动作。
- 7.55验证：先RED复现缺独立入口，后补drain/后缀/身份/reader反例；独立review发现错context/外PID同步可误成空Q，及外PID activity借Runtime correlation，均先失败后加入实际scope检查。初始受影响定向94 passed，最终新增测试34 passed。首次全量PATH筛选未隔离nvcc，意外触发本机CUDA13旧Q0编译失败：1377 passed、1 failed、4 errors（均同一编译路径），未执行GPU程序，不改旧Q0/skip。改为同一Python进程过滤CUDA路径并先断言`shutil.which('nvcc') is None`，`CUDA_VISIBLE_DEVICES=-1`；最终CPU全量1379 passed、5 skipped（现有5项nvcc编译门，288.08s）。compileall、contract37/37、Canonical7模块、oracle independence及diff-check通过。所有新资格输入为合成fixture；未部署、未运行真实Nsight或采集。
- 7.54当前设计：[request/drain范围草案0.1](gate8_request_drain_scope_draft_v0_1.md)，DRAFT_NOT_APPROVED。核对研究设计v7.1 §1.5/协议v2.1 Pre-Pilot，明确模型sampling/Token-ready在内、setup/文本化/I-O在外；历史线程不等于推理多线程。原有成功drain可有条件证明前缀对A交集为零，但不证明无迟发/无丢失、不删B历史；提出A独立范围资格这一集中待审amendment，后缀依赖仍严格。collector原型暂停，旧7.53建议不再是当前下一步。精简定向/收口验证及hash复用，保留合同要求；无代码/正式schema/服务器变更。
- 7.53研究转向一页草案：[单一collector Go/No-Go](gate8_collector_pivot_decision_v0_1.md)。自然Qwen当前NO-GO；首选替换而非并挂Nsight的受控可行性原型为条件性GO、未授权。第一方API有具体参数/correlation/resource/NVTX/丢弃入口，但目标ABI/thread epoch/implicit PTDS仍需原型证伪，不保证平台可用。备选受控显式流须收缩自然行为claim。唯一下一步是用户决定是否投入该受控原型，不同时授权模型采集。无代码/合同/服务器变更。
- 7.52最后替代路线裁决见[可行性文档末节](gate8_mode_feasibility_decision_v0_1.md)：CUPTI旁挂adapter缺目标共存及完整epoch正面依据；所有兼容世界A等价路线缺候选集合完备性，且属新发布语义，不能因两个模式同值就放行。两者均未达可执行条件，关闭本轮调查，不请求批准空adapter/不默认profile。Route A自然模型目标仍未完成，Gate7 PASS、新Q0/Gate8 NOT_RUN。
- 7.51有界技术裁决：[mode/epoch可行性0.1](gate8_mode_feasibility_decision_v0_1.md)。仅比较现有Nsight字段和固定源码/二进制证明两条低风险候选，均未闭合。原SQLite有NULL stream正面类型证据但Runtime无stream参数、inventory无epoch；不得将缺口写成完全无证据或整进程mode。暂停抽象准入批准，停止同类搜索，不默认profile；真实模型支持域仍阻塞，受控正确性不能冒充自然模型claim。只读/文档，服务器不动。
- 7.50批准前具体提案：[target-scope admission草案0.1](gate8_target_scope_admission_draft_v0_1.md)，DRAFT_NOT_APPROVED。按调用/TU/thread/context绑定mode与epoch证据；同族窄域、混合mode拒绝、setup/warmup原owner和完整历史，给拒绝矩阵和手算正反例。官方CUDA12.4.1及安装Nsight API列表不证明目标调用；可执行mode/连续性adapter仍技术阻塞。仅文档，未改变合同/代码/资格，未授权profile或服务器采集。
- 7.49窄支持域只读设计：[真实模型scope方案0.1](gate8_model_scope_design_v0_1.md)。明确producer0.4五文件、D1、stage/task/drain的工程接线；集中待决为新版默认流及setup/warmup原owner准入，mode UNKNOWN仍拒绝，不默认A-only/模式等价旁路。旧Q0按影响复用，新接口不继承资格。来源profile仍暂停；仅文档，无新测试/服务器操作；Gate7 PASS，新Q0/Gate8 NOT_RUN。
- 7.48六点只读实审：[目标sync差距表0.1](gate8_target_sync_gap_audit_v0_1.md)。固定历史SQLite hash前后一致，四token/two drain经Runtime/correlation逐行核对；三个新版marker均0、旧角色如实保留。四DtoH均早于显式sync进入，已观测候选提交无横跨且GPU均先结束；这不是完整W/零等待证明。区别整窗D1缺口、未资格default/历史owner、可证明局部unattributed与不可界定影响；不发布新A/B。下一项仅本地窄支持域方案，别把现nondefault/全inventory projection实现限制当普遍门。只读/文档，不新增测试/服务器操作或改合同；Gate7 PASS，新Q0/Gate8 NOT_RUN。
- 7.47必要性重审：[来源对齐§12](gate8_eager_source_alignment_v0_1.md)。周期CPU sample与CUDA API取栈分开；module/RVA不是MC/S/closed-prior的普遍必需，也不单独解除默认流/生命周期/owner未知。暂停source profile及A/B/C交付执行，不再请求风险批准；d62c818实现/包仅未授权备用。下一项只读检查四目标token sync/两drain及必要前驱，逐项说明唯一关键缺口、对W/terminal/A/B影响与低风险路径。旧受控证据按覆盖复用，不自动新Q0，旧模型仍不授默认流资格。本轮仅文档/只读，无新测试/业务修改/服务器操作，不改变冻结语义或Formal数据；Gate7 PASS，新Q0/Gate8 NOT_RUN。
- 7.46本地候选实现：[来源对齐§11](gate8_eager_source_alignment_v0_1.md)。source_probe静态plan/纯argv/显式run与实际文件入口已接通；复用runner/D1/stage/drain，独立整数预期四token15。新的hf-source-probe分支使用task ledger/marker0.2，旧loader0.1不变；COMPLETE只是诊断producer完成，source_binding UNKNOWN/measurement NOT_ASSESSED，不授S/Q0。版本/身份/同步重哈希/partial发布/第二request失败反例先RED后修，失败观察保留。新增22项、定向88 passed/15.39s；CPU全量1345 passed/5 skipped/247.16s（Python3.12.7，进程mask=-1、确认nvcc不可见，五skip为原Q0 CUDA source编译项，未改skip）。compileall、contract37/37内部一致性、Canonical7模块、oracle静态独立性、文档相对链接/diff/增量隐私检查通过；独立只读review无剩余重要问题。不是目标TorchBackend/服务器/Nsight验证。未部署/采集，Gate7 PASS，新Q0/Gate8 NOT_RUN。
- 7.45PE原件实审：[来源对齐§10](gate8_eager_source_alignment_v0_1.md)，run pe_source_20260927T034417Z_826108098513436c84501b34bb4a7b77的9项/10文件大小hash/精确集合直接核验通过，清单SHA4a6e2c241a5d4496b2fdf2368dbac8f39fad62c01f3fc840897e162fc255e3e5；receipt六命令exit0/error=null/server f5edc64未变。c10导出copy/sync/current/default候选及torch导入可见，但旧运行callchain为空、headers无PDB identity；不推出整模块mode，不复算未传回DLL。静态路线正式关闭，不索PDB/反汇编/安装包；UNKNOWN/NOT_ASSESSED不变。
- 7.45下一有限准备：一次UNKNOWN起步的Engineering来源观察，两个小task与自然流两request，独立算术固定四token=15，仅观察实际copy/sync来源，不冒充Qwen或Q0。目标安装UserGuide明确CUDA backtrace依赖CPU sampling且强制相同scope的cpuctxsw；§10.2给精确memory:0,sync:0/process-tree/200Hz提案、显著开销及历史BugCheck风险、空栈/参数不支持停止规则，已交协调只读审查。未更改profile/业务代码或执行服务器；本轮无新pytest/全量，7.43成绩不升级为目标验证。Gate7 PASS，新Q0/Gate8 NOT_RUN。
- 7.44交付收紧：已准备忽略本地索引中的单文件静态脚本，5633 bytes、SHA256 `28ba3efee8eb63971ddcaf3fb1c40efa1ef04eac9b9fafa43ab3f9daa114f318`；固定原server HEAD/两DLL hash，仅六次imports/exports/headers、无反汇编/扫描/加载。语法AST检查通过，未执行目标工具/服务器；准确传输、执行、10文件/9项清单回件说明已获协调只读复核，最后补直接输出清单hash/项数与子进程启动策略说明。候选不是必做Gate；缺符号结束静态路线，后续Engineering来源取证允许UNKNOWN开始，不形成运行绑定前置循环。GPU/Nsight仍未授权。
- 7.44必要调用点调查收口：[来源对齐§9](gate8_eager_source_alignment_v0_1.md)。只读旧合格SQLite白名单复核四token sync/两device drain、5线程Memcpy同trace stream7、相关callchain全部null及event-create记录，输入SHA前后一致；不读取敏感metadata、不追认资格。给出独立条件性单流等价正例及worker历史/另blocking流反例：A相同不保证B完整W相同，drain不能截断历史。源码/hash/marker/单流外观不足以关闭目标mode/lifetime来源；本轮无业务修改或新测试，不把7.43成绩当本轮实验。
- 7.44唯一外部候选：经单次授权后只读已hash的c10_cuda/torch_cuda相关imports/exports/已有符号及可定位调用RVA，限定相关copy/sync/default/event/context入口，不扫描安装、不加载CUDA、不采集、不部署。本轮只准备，未执行；仅imports不能证明实际调用，缺可绑定调用点即终止静态路线、不再索包。详见§9.3的能/不能证明、两个终点及后续受控来源验证边界。无需新增研究claim；如后续需改变observation profile，应单项说明再批准。Gate7 PASS，新Q0/Gate8 NOT_RUN。
- 7.43本地加载观察：[来源对齐§8](gate8_eager_source_alignment_v0_1.md)。目标原件审计后，显式record_load_tasks将原load_model两个加载分支接到精确来源限定的临时单hook；任务、attempt、父setup、native TID与线程实例随producer0.4/load-task0.1落盘。原Future/返回/异常和非等待shutdown保留，不新增等待/CUDA同步/流切换。未结束/取消/失败任务保留INCOMPLETE，setup不伪造request；HOST_JOB_ONLY/UNKNOWN/NOT_ASSESSED不授S资格，旧file-chain0.5明确拒绝新诊断receipt。
- 7.43验证完成：新纯线程10项、真实producer文件入口9项先RED后GREEN；重哈希跨run host/drain反例、review的封存竞态/锁交接/关键字/内存源码与来源集合缺口均补RED后修复。最终新增29项、定向81 passed/11.65s；CPU全量1323 passed/5 skipped/246.37s（Python3.12.7，进程内mask=-1并确认nvcc不可见，5项为既有Q0 CUDA source编译测试，不改skip）。两轮较早启动的全量因review修复中止，不计通过。compileall、contract37/37内部一致性、Canonical7模块、oracle静态独立性、文档链接/增量隐私/diff-check通过。四项review经只读复核关闭；全部为CPU替身/合成marker，不是目标CUDA/Nsight资格。服务器仍f5edc64，无部署/采集；Gate7 PASS，新Q0/Gate8 NOT_RUN。
- 7.42直接到件审计：[来源对齐§7](gate8_eager_source_alignment_v0_1.md)。目标快照解压目录外清单14项/内清单9项（8源码+receipt）/总15文件的bytes/hash与精确集合全部本地匹配；外清单SHA870a2184abc0bdb00cdf972991015fdb47c1d7f7a644ee757426e7a7919b81c3。ZIP本体未到，不能称CRC或ZIP hash本地核验，不要求重传。operation原件server f5edc64前后clean/exit0，Python3.11.16隔离启动；snapshot10项RECORD匹配、issues为空。DLL仅服务器hash回执，未本地复算。首次Git多路径前置失败在创建run前，修正封装后此次快照成功；不计首次为采集attempt。
- 7.42来源可用范围：直接读目标Torch2.6+cu124/CUDA12.4/git2236df1、Transformers5.17的设备映射、materialize worker、Future与非等待shutdown。源码引用身份可固定；实际task/native TID/加载分支及default-mode/相关lifetime不能由文件hash或Future推断。停止同一安装搜索/重复补证；下一项主窗口本地opt-in task/attempt观察与实际文件链反例，不加wait/sync、不换流/禁异步、UNKNOWN不授S资格。服务器现在没有操作；Gate7 PASS，新Q0/Gate8 NOT_RUN。
- 7.42本轮只读核查及文档更新，无业务代码/schema/冻结合同/旧证据修改，无新pytest/compileall或服务器实验；不将7.41的15项本地fixture与本次服务器快照混为新的科学验证。
- 7.41有界来源收口：[eager来源对齐§4～5](gate8_eager_source_alignment_v0_1.md)记录Torch2.6 copy/sync与Transformers5.17字符串device_map、worker/materialize/Future及非等待shutdown的精确第一方出处。标签源码不是目标二进制/历史TID证明；本地已有安装/环境回执无这些目标源码，default-mode/worker ownership仍UNKNOWN。未添加S准入或必要scope猜测，不换流/禁异步/加sync。
- 7.41唯一最小外部动作已准备：stdlib-only安装快照0.1用固定repo的.venv -I -S，不import Torch/模型/环境dump/GPU/Nsight；只读10白名单（8源码+2DLL仅hash）、两个包有限metadata/RECORD，写新独立诊断目录与排除自身清单。完成状态只表示快照，不是资格；服务器仍f5edc64，不部署repo、不生成bundle。本轮未执行该服务器命令；须用户经协调窗口审查后执行一次并回传，主窗口再核来源，不重复宽泛搜索或旧controlled。
- 7.41本地验证：先RED10后实现；只读review的重复Name/Version3例与device_map源文件缺失1例先RED后修复，15 passed/3.12s（本地Python3.12.7）。隔离fixture子进程验证不import目标包、不网络/子进程/动态库加载；曾因测试误禁stdlib socket导入出现1失败，定位改为事件级限制后通过。未重跑上一轮1279/5全量，不称目标3.11正向CLI已验证。运行代码、冻结MC/S/A/B/Derived/Q0及旧证据未改；Gate7 PASS，新Q0/Gate8 NOT_RUN。
- 7.41交付检查：本轮新增脚本/测试compileall、完整PowerShell草案语法解析、修改Markdown相对链接、增量私有路径/敏感模式与diff-check通过；独立及协调只读review关闭同字节metadata唯一性缺口，最终协调核对工具hash和交付流程无具体阻塞。仅传一个9694-byte工具副本，脚本SHA256及完整机器命令在忽略交付索引；服务器不追随本地文档/工具commit。
- 7.40本地source接线：[eager来源对齐0.1](gate8_eager_source_alignment_v0_1.md)。直接只读历史真实Raw确认default/null stream7、窗前setup/warmup及worker提交、真实`_v3020` drain别名；不能把旧trace补写为新资格。复用既有精确registry修复别名；显式model_setup接原load_model/输入初始化，新增HOST_CALL_ONLY stage/stream观察、producer/input0.3/file-chain0.5诊断。setup无伪request，warmup/measured保留原identity；stream mode/lifetime和worker ownership不猜测。WMPC/输入/source/mode/次数/mask在模型加载前匹配，失败不继续；新入口不替代全launcher preflight。S/A/B/Derived不消费stage作为准入证据，UNKNOWN继续阻塞。
- 7.40验证与边界：先producer RED8、file入口RED4、ABI别名RED1；review所提截断stage/状态矛盾RED2、实际WMPC执行合同RED5、自审logical mapping RED1等先失败后修复。第一轮定向113 passed/64.69s、全量1274/5；随后协调只读review发现结果版本降级绕过校验，stage5/closed-prior1反例先RED，再绑定input/producer/result版本、精确artifact集合及存在性。修复后三文件61 passed/73.81s；最终CPU全量1279 passed/5 skipped（251.18s，Python3.12.7，进程内mask=-1且nvcc不可见），五skip均既有Q0 CUDA source编译项，未改skip政策。一条定向命令曾因测试文件名错误未收集测试，纠正后运行上述三文件，不计为验证成绩。compileall、contract37/37内部一致性、Canonical7模块、oracle静态独立性、diff检查、增量隐私和修改Markdown链接均通过。独立review与协调只读复核所提具体缺口已关闭；未改变同步次数/stream选择、冻结MC/旧schema/Q0或历史证据；没有服务器/GPU/Nsight操作。
- 7.40剩余最小工作：真实model producer已接阶段文件，但default-mode/目标二进制来源、worker归属与必要依赖closure尚未证明，不能称一般模型科学链收口。all-inventory仍是窄profile限制而非研究全capture门。下一项主窗口本地完成source descriptor及必要/无关scope成对准入；若现有本地材料不足，只提出一次针对目标torch来源/相关default调用与worker提交的最小只读补证方案，不先跑模型、换流或重采旧controlled。服务器仍f5edc64，不更新部署；Gate7 PASS，新Q0/Gate8 NOT_RUN。

以下7.37/7.38为历史快照：7.38“等待批准”已被7.39用户批准覆盖；7.37“以旧计划为准”不再是当前待办。当前只按7.40/7.39已批准范围执行，不重复申请同一语义授权。

- 7.39用户批准后的本地实现：[closed-prior amendment0.1](gate8_closed_prior_amendment_v0_1.md)，producer仅观察现有drain、在warmup与drain前检查actual current logical device；真实API+physical sync绑定PID/device/context/clock及NVTX/receipt，保留失败。S0.3/A-B0.4明确逐activity来源与cross-request，不改A/W/B公式；signed整数边界精确，旧读取路径隔离，Derived不接受新版本。两/三request与同request已完成前驱、负时间、scope/生命周期/版本/hash反例及文件链已做本地确定性验证，全部为合成/CPU替身；不是新Q0或模型验收。
- 7.39验证：本地Python3.12.7；初始producer RED4/closed-prior RED10、文件接口RED及后续review各缺口先失败后修复。最后一轮定向73 passed/55.99s，其后新增的未知drain版本与负时间文件回归由最终CPU全量覆盖：`pytest -q -p no:cacheprovider -rs` 为1240 passed/5 skipped（237.07s）。在Python进程内明确mask=-1并确认nvcc不可见，五skip均现有Q0 CUDA source编译项，未修改skip政策；首次外层PATH隔离检查失败即停止，未启动该次pytest。compileall、contract37/37（仅内部一致性）、Canonical7模块、oracle静态独立性与diff检查通过。独立只读review复核11项通过，所提device/scope/lifecycle/host-clock/精确整数/未知版本缺口关闭；协调只读审查确认窄支持域限制。冻结旧schema、MC正文、Q0源码/oracle、Gate6/7证据未改。
- 7.39就绪边界：continuous nondefault producer-owned范围声明仍需目标资格；当前all-inventory/完整measured projection限制会拒绝未标记setup/warmup，不能称一般模型已接通，也不是Route A新增全capture门。下一项本地审查可用source→必要前驱/可证无关scope→owner/lifetime映射，default/continuous/recreated分开，不强制所有路径create/destroy；不造证据、不换stream。无需用户服务器操作，不交付未就绪部署包。
- 7.38有界裁决设计：只读核对MC §4.1/7.2/7.3/9/10/11、S ownership与runner现有窗前drain，形成[共享stream裁决稿0.2](gate8_controlled_bridge_v0_1.md)。保留物理前缀和B历史进度、A按窗口裁剪；明确修正7.37的W截断预期。列出Raw drain/clock/context/lifetime/owner证据、五类独立正负预期、现有producer缺口及最小Q0影响。仅提案，不修改冻结合同/生产代码，不运行新测试/实验；Derived全B门保留。等待一次集中语义裁决，常规已授权工作不重复请求审批；服务器仍固定f5edc64，无新部署。
- 7.37直接原件审计：f5edc64服务器新73文件/72清单、38派生引用及29旧输入全部匹配；清单SHA84dff0dbf83596142d1a0381e53690204e1de3d8cdab322a227e10eb9765a2a7。目标机原始日志129 passed/27.75s、静态成功，非本窗口执行。四phase已纠正，S全字段、B其余字段/五INVALID、A数值及边界不变（window_id仅fresh lineage变化）。19诊断/UNKNOWN/NOT_ASSESSED/Derived阻断保留。关闭B phase修复，不再要求相同部署/静态/离线重复；当前待办以[计划7.37](../superpowers/plans/2026-09-25-gate8-minimal-execution-plan.md)为准。
- 7.36本地修复验证：真实S mapping→B unique phase values，null保留、缺失/畸形fail closed、旧A/B 0.2/0.3读取不变。RED13/31；对齐残留伪list夹具后定向129 passed，CPU全量1204 passed/5 skipped（226.39s；nvcc隔离，均CUDA source编译项）；compileall/37条contract/Canonical7/oracle/diff-check通过。前一次提前启动的全量因已知夹具失败中止，不算通过。新本地真实输入派生S/五INVALID/B timing不变，仅四phase数组修正；A除fresh lineage window_id外完全相同，Derived仍阻断。协调只读review无阻塞；不是修复版本服务器成绩。
- 7.36直接实物审计：[controlled adapter审计](gate8_controlled_optional_tables_audit_v0_1.md)核72清单/73文件、38派生引用、29旧输入全部一致。capture07625b7/analysis c827b61分开；服务器原始日志98 passed/91.36s、静态检查通过，不是本窗口新测试。六A独立Raw算术吻合、四B W(s)/terminal/五时长吻合，但实际B activity_origin_phases错误装入S映射的activity ID键；需本地最小兼容修复，暂不称B全字段通过。五窗外INVALID/19diagnostics保留，Derived阻断、UNKNOWN/NOT_ASSESSED不变；纠正旧文档把sync residual等同return tail的表述，无公式变更。
- 7.34后续已到件审计：[可选表/diagnostics审计](gate8_controlled_optional_tables_audit_v0_1.md)核29文件/28清单。MEMSET缺失由明确lazy元数据与版本文档支持，窄adapter红绿回归完成；现SQLite只读前瞻仍停19条diagnostics，未静默豁免。暂不部署，不重采/export/编译DLL；现REP/SQLite可复用，新分析版本应独立留痕。Gate8/新Q0 NOT_RUN。
- 7.34后续用户回传（原件待收）：0.2首次export PASS，audit因`RAW_TABLE_MISSING:CUPTI_ACTIVITY_KIND_MEMSET` BLOCKED，尚未本地核验实际schema。先据对应版本的按需表规则审计，不默认缺表为空、不重采/重export；若只需分析adapter修复，使用原输入新目录离线复验。Gate8/新Q0仍NOT_RUN。
- 7.33后续用户回传（原件待收）：07625b7的0.2窄受控capture已结束，run `controlled_20260926T133649Z_8dd7210fc970474eb1b6358a9e91d8cd`，plan/REP生成、capture exit0；未export/analysis/模型。本窗口尚未取得完整目录，不能声称trace语义或文件身份链通过。下一步仅到件只读审计及新run绑定后处理草案；Gate8/新Q0仍NOT_RUN。
- 7.32验证：37项受控定向通过；本地Python3.12.7 CPU-only全量1169 passed/5 skipped（nvcc编译项），compileall/合同37/37/Canonical7模块/oracle/diff-check通过。不是目标机新native编译或采集资格。
- 最近更新：`2026-10-10`（7.125）
- 权威研究主体：`docs/current/ExposedPath_研究设计.docx`，文内版本 `v7.1`
- 当前执行依据：原DOCX v2.1仍为Pre-Pilot；未来限定Formal使用[签署G12-ROUTEA/0.1](gate12_protocol_signed_v0_1.json)及[收尾边界](gate12_closeout_v0_1.md)，不覆盖原文。
- 当前研究阶段：Gate12旧0.1历史限定签署PASS；Gate13首槽prepare失败BLOCKED，无模型或测量样本。0.1.1修复候选已绑定99f3bae，待精确内容重新签署，旧角色保持。
- 当前工作入口：根目录 `main`；目录约定见 `docs/repository_layout.md`。Gate7历史封存验收执行commit为 `8d64f7580d43d7c8e1cb7a416b459cec8f60b011`，closeout为 `16604d59b05ee6d7e8415f75dbaaa1be3be7cf8a`。N1历史Engineering执行V0为c21d835、Vmarker/V16为d25b4d1；新Pilot首批执行221f46c；审查提交不是新执行身份。
- 当前数据资格（7.122）：Gate6历史Engineering/Q0保持；[首批/暖机对照](gate11_warmup_policy_review_v0_1.md)及[共同w3 Pilot](gate11_policy_closeout_v0_1.md)仍只作政策依据、不混池/升级。累计90进程/30profile Pilot预算结束；签署仅准未来限定Formal声明，尚无Formal采集或合格结果。UNKNOWN/NOT_ASSESSED与旧资格边界保持。
- 当前 Gate 状态（7.124）：Gate0～7历史PASS、Gate8限定Engineering PASS、Gate9分域PASS、[Gate10仅选定G1三点一次可行性PASS](gate10_closeout_v0_1.md)、[N1独立Engineering PASS](n1_model_feasibility_closeout_v0_1.md)、[Gate11限定Pilot政策PASS](gate11_policy_closeout_v0_1.md)、[Gate12旧0.1限定签署历史PASS](gate12_closeout_v0_1.md)；Gate13 BLOCKED、Gate14 NOT_RUN；0.1.1补丁待新精确内容签署。容量/精度/稳定性未授，旧报告/UNKNOWN/NOT_ASSESSED保持。
- 当前最高优先级（7.125）：审查[prepare修复](gate13_prepare_repair_v0_1.md)及[已绑定的0.1.1候选](gate12_freeze_candidate_v0_1_1.json)，集中确认新精确内容hash并重新签署；不得沿用旧seal/approval或再次执行旧阶段B。服务器暂停，原批次不恢复。
- 7.27本地验证：tests-first新增16例，定向49 passed；显式令nvcc不可见的CPU全量1132 passed/5 skipped（编译相关5例，不改skip源码），compileall、contract37/37、Canonical boundary、oracle independence、diff-check通过。首次全量PATH隔离未生效，意外触发本机CUDA13旧Q0编译失败：1130 passed/1 failed/4 errors，保留事实；未运行GPU/Q0程序。review新增直接入口伪零/错basis的RED→GREEN，共享shape校验并绑定physical sync_id。新scope入口仅synthetic受控证据，真实受控桥接与目标栈资格尚缺。旧S/A/B/Derived公式、Q0源码/oracle及Gate6证据zero diff。
- 7.28本地验证：先新增producer/Raw/file-proof回归；review的额外sync、前窗同流memset、独立Driver表、冲突trace/plan五项先失败后修复。29项定向通过；CPU全量1161 passed/5 skipped（nvcc隔离，196.78s），compileall、contract37/37、Canonical7模块、oracle independence、diff-check通过。所有Raw均确定性fixture，未编译/执行新native、未运行GPU/Nsight。局部API unknown20ns/request未改成Host，4个B独立oracle吻合，不产Derived。
- 7.29服务器回执：本窗口直接读取用户传回文本，24f58f8已部署；模块式DevShell成功，cl19.38.33135.0/MSVC14.38.33130/nvcc12.4.131/Python3.11.16。该commit服务器全量1165 passed/1 skipped（195.55s，未打印skip原因，不推断）；contract37/37、Canonical7、oracle PASS。native在cudaDeviceGetUuid未定义处编译失败，未产成功build receipt、未采集GPU，mask恢复3。本轮只修UUID获取为既有Q0及官方CUDA12.4支持的cudaGetDeviceProperties().uuid，身份语义不变；source回归先RED后修复。恢复脚本以24f58f8为基线，旧8d64f75部署脚本停用；不无故重跑服务器全量。
- 7.29本地最小验证：新增UUID源合同回归1例先失败；修复后受控五文件30 passed（22.37s），compileall与diff-check通过。未使用本机CUDA12.9/13编译冒充目标12.4验证，未重跑全量；待服务器用已验证工具链实际编译。旧S/A/B/Q0/oracle/evidence没有改动。
- 7.30本地直接审计：传回transcript/build_receipt/DLL/LIB/EXP五原件，7f61102/parent24f58f8、工具身份、30 passed/54.20s、contract/Canonical/oracle及native编译完成一致。305152-byte DLL实际SHA256与receipt一致；源码报告hash精确对应7f61102 Git blob的CRLF表示（本地LF不同，不改hash）。详情及完整hash见build audit；没有本轮新测试/服务器执行。7.29恢复已完成，无需再次部署或编译。
- 7.30后续启动观察（协调回传，尚未本地原件审计）：capture草案在Get-Command nsys.exe找不到工具时停止，位于RunRoot创建/profile之前，不算采集attempt。已知工具绝对位置由协调窗口核验并安排仅当前进程PATH修正；本窗口不改已交付脚本hash、不改系统PATH，不把尚无回执的重试写成成功。
- 7.31直接读取完整capture原件：run controlled_20260926T040859Z_48bf088f634b453fb2070eecda6c6c39；REP82711 bytes/hash与collection一致，init/warmup/cleanup COMPLETE、PID61680、2request/4token、GPU/19项argv与所有封存hash链匹配，17文件前后不变。结论仅CAPTURE_RECEIPTS_CHECKED_NOT_TRACE_ACCEPTANCE；无新本地Nsight执行。后处理固定server原checkout、新唯一diagnostics保存字节副本及派生，不改原capture。PowerShell Parser/17file只读preflight已验；尚未实际export/audit，Gate8/Q0 NOT_RUN。
- 7.39历史本地/服务器身份：capture为`07625b72e90d5fbb5bcb581d03a6f7582b2e0dc6`及0.2 DLL，服务器分析checkout当时为`f5edc64862a8d5fbe94a7bf19be68303a4874b7f`，parent c827b61；该阶段基于dbe638ed开发。不是7.110当前部署/执行身份；机器路径及回执定位在忽略handoff。
- 历史总体判断（2026-09-20）：Gate 6 / Q0 已正式 `PASS`。frozen run `q0-win-4090-20260920-gate6-final-04` 在 package/analyzer `0.2.2`、formal binary SHA256 `4DFF82028F4FCFB57D42ABF061AE8962C1867DCE19DF23808D223B425868FC80` 下完成：21/21 `REAL_CASE_PASS`、2 个 synthetic-only case（`Q0-TERMINAL-TIE-001`、`Q0-SUBMISSION-RACE-001`）PASS、23/23 `SYNTHETIC_PASS`，且存在唯一一份 `q0_gate_report.json`（schema `exposedpath-q0-gate/0.2.0`、`23/23`、`verdict=PASS`、`q0_status=PASS`、report count `1`）。该 PASS 只说明当前 analyzer 在本目标 observation stack 上取得 **Q0 正确性资格**；不等于 Engineering Pilot、Pilot、Protocol Freeze 或 Formal 结果，也不建立第二平台等价性。身份、哈希、provenance caveat、根因映射与实现成熟度见 `docs/v1_4_1/gate6_closeout_v0_1.md`。
- 历史到达点（已由7.18取代）（`EP-G7-11`）：此前一次 fresh smoke 在 Pass1/Nsight 启动边界遭系统 BugCheck `0x133` 中断，根因未获证明。随后服务器报告：`799fb8d` 在目标 Windows/RTX 4090 的 static preflight `940 passed, 1 skipped`、compileall、verify、合同/Canonical/oracle 检查通过；新 Engineering smoke `smoke_20260923T134310Z` 的 Pass0、Pass1 inference/telemetry/parity 和最小 Nsight collection 完成，生成非空 REP，且未再出现 BugCheck。但即时 `nsys export` 在约 51% 停滞，被人工终止后 machine report 为 `BLOCKED_BY_NSYS`、exit 1，Analyzer 未运行；该 attempt **不是** Gate 7 acceptance evidence。相同 SHA256 的 REP 副本后续离线 export 得到 integrity PASS 的 SQLite，诊断 analyzer exit 0；仅支持“REP 可离线导出/分析”，不证明即时 export 挂起的精确根因，也不追认原 attempt。Gate 7 仍为 `NOT_RUN`，Gate 8 未启动。

历史快照（保留，不覆盖；以下描述 2026-09-19 及更早的当时状态，均已由 2026-09-20 Gate 6 PASS 取代，详细过程见 `docs/v1_4_1/gate6_closeout_v0_1.md`）：

- 2026-09-19（Gate 6 `final-01`）：frozen run `q0-win-4090-20260919-gate6-final-01` 跑完采集链与 16 个 real evaluator，`Q0-KERNEL-MEMOP-001 = REAL_CASE_PASS`，4 例 semantic FAIL（`Q0-MISSING-CORR-001`、`Q0-EXTERNAL-001`、`Q0-MULTITHREAD-ORDERED-001`、`Q0-OVERLAPPING-HOST-SYNC-001`），`Q0-PHASE-SPILL-001` 因 analyzer blocker 未完成，无 `q0_gate_report.json`。该 run 为 frozen incomplete Engineering run：不续跑、不重跑、不拼接、不升级为 Gate PASS。**当时状态**：Gate 6 `FAIL`、Q0 `NOT_RUN`、Gate 7 `BLOCKED/暂停`、Gate 8 未启动。
- 2026-09-18：formal-shape 配对 diagnostic（`q0-win-4090-20260918-kernel-memop-h2d-formalshape-warmup-02`）证明 `Q0-KERNEL-MEMOP-001` 的构造失败可由 pre-capture same-kernel warm-up 恢复（B：overlap `10000741 ns`、`S_DEVICE=VALID_NONEMPTY`、wait set `{KERNEL_A,MEMCPY_B}`、terminal `MEMCPY_B/MEMOP`），推翻“平台 incapable”解释；不作 LAZY/WDDM/driver/Runtime 机制归因。**当时状态**：Gate 6 `FAIL`、Q0 `NOT_RUN`。
- 2026-09-17（`EP-G6-06` 策略决定）：synthetic 只允许作为 Engineering regression strengthening；差异矩阵未发现新增覆盖价值，故不新增 synthetic profile，只固化 coverage 与边界（`EP-G6-08`）；批准进入“候选平台 + construction admission”**设计**（不代表授权任何外部平台实验）；scope limitation 不批准、仅作 fallback；该轮 r11 及后续当时一律禁止执行。

## 2. 使用与更新规则

1. 每项任务使用稳定编号；计划调整时不得重排或复用旧编号。取消或合并的任务保留并标注状态，不得直接删除历史。
2. 任何实质性的研究定义、代码、测试、实验、证据资格或执行计划变化，都必须在同一次提交中更新本清单。
3. 完成项必须同时给出可复查证据。只有文档、代码或测试存在但尚未满足完成条件时，不得勾选完成。
4. Gate 只能使用 `PASS`、`FAIL`、`BLOCKED`、`NOT_RUN`。局部测试通过、mock 通过或无法运行 GPU 测试，不能写成 Gate `PASS`。
5. `Prototype`、`Engineering`、`Pilot`、`Formal` 数据资格分开记录；复制、改名或重新分析不能提升数据资格。
6. 计划改变时同步更新 §8「计划调整记录」，说明原因、受影响编号、顺序变化，以及是否影响已冻结协议或 Formal 数据。
7. 每次结束实质性工作前，至少核对：完成状态、Gate verdict、证据、阻塞原因、当前最高优先级和下一项任务。

状态标记：`[x]` 表示完成；`[ ]` 后注明“进行中、未开始、受阻或取消”。Gate verdict 与任务勾选相互独立。

## 3. Gate 0～6 完成摘要

### Gate 0：封存旧 Prototype

**Gate verdict：`PASS`。** 只表示旧实现、Raw 身份、基线和限制已封存，不表示 v1.4.1 方法正确或 Q0 已通过。

- [x] `EP-G0-01` 固定旧 prototype 提交和标签。证据：标签 `prototype-windows-v0.1`，提交 `abab013c5483109007ab5a2a232438d46bbaf02b`。
- [x] `EP-G0-02` 固定三份历史 `.nsys-rep` 的文件大小和 SHA-256。证据：`docs/prototype_archive/raw_trace_manifest_v1.json`。
- [x] `EP-G0-03` 记录采集/读取环境、测试基线和已知失败。证据：`docs/prototype_archive/README.md`。
- [x] `EP-G0-04` 历史数据只能用于 Prototype/Engineering 回归，不能作为 Q0、Pilot 或 Formal 证据。

### Gate 1：Measurement Contract v0.2

**Gate verdict：`PASS`。** 只表示 phase/Token、同步身份、completion scope、`W(s)`、terminal、validity、A/B 和派生规则已形成版本化、机器可检查且无未决语义占位的合同；不表示实现正确或 Q0 已通过。

- [x] `EP-G1-01` 完成 `Nsight SQLite -> observation report` 合同草案 0.1。证据：`docs/v1_4_1/analyzer_contract_v0_1.md`。
- [x] `EP-G1-02` 定义 Request、Prefill、Decode、首 Token 和后续 Token 的可观察完成边界。
- [x] `EP-G1-03` 定义自然逐 Token 同步、N1 人为同步与仅标记版本的互斥身份，并冻结 Pass0/Pass1 完成行为等价。
- [x] `EP-G1-04` 冻结 stream、device、context、event 的 completion scope；同步 copy 保持透明 unsupported。证据：`docs/v1_4_1/contracts/sync_semantics_registry_v0_2.json`。
- [x] `EP-G1-05` 冻结 `W(s)` 的提交证明、同流/event/default-stream 传递依赖、ownership 和排除规则。
- [x] `EP-G1-06` 冻结 terminal 的 semantic frontier 优先规则、并列候选及 0 ns 语义容差。
- [x] `EP-G1-07` 冻结 `VALID_NONEMPTY/VALID_EMPTY/AMBIGUOUS/INVALID`、原因码优先级和 A/B fail-closed 传播。
- [x] `EP-G1-08` 冻结 A/B 字段、互斥/守恒、B per-sync 生命周期，以及 D/Exposure Signature 的纯派生规则。
- [x] `EP-G1-09` 为 37 条合同规则建立 25 个验证案例映射并完成内部合同审查。证据：`docs/v1_4_1/contracts/measurement_contract_test_map_v0_2.json`、`tests/test_v141_contract.py`；`python -m exposedpath_v141 validate-contract` 输出 `37/37 (100%)` 与 `PASS`。

**后续状态（2026-09-20）：** Gate 2～6 已全部完成，Gate 6 / Q0 已 `PASS`。本 Gate 不再有待办或前序条件；当前状态以 §1 与 §5 为准。

### Gate 2：设计 Q0 独立标准答案

**Gate verdict：`PASS`。** 只表示 23 个受控案例的 expected/oracle 已预先写定、可机器校验且独立于被测 analyzer。

- [x] `EP-G2-01`～`EP-G2-03` 建立 23 个必需受控用例并预写 `W(s)`、terminal、validity 和 A/B 关系。证据：`q0/oracle_cases_v0_2.json`。
- [x] `EP-G2-04` AST 独立性检查：禁止 oracle 导入旧 analyzer 或未来 Raw/S/A/B 实现，禁止区间函数读取 dependency edges。证据：`scripts/verify_q0_oracle_independence.py`。
- [x] `EP-G2-05` 完成 7 正例、7 边界例、2 含糊例、7 负例及 25 特性覆盖审查。证据：`docs/v1_4_1/q0_oracle_design_v0_2.md`、`tests/test_v141_q0_oracle.py`；CLI 输出 `DESIGN_ONLY_PASS`。

### Gate 3：Canonical Raw 层

**Gate verdict：`PASS`。** 只表示唯一、版本化 Canonical Raw schema、只读转换器、identity/fail-closed 边界和三份历史 trace Engineering 回归通过。

- [x] `EP-G3-01`～`EP-G3-02` 独立入口 `python -m exposedpath_v141 inspect-sqlite`；对支持的 Nsight schema、必需表/字段、sync correlation 与 dropped records 执行 fail-closed 检查。
- [x] `EP-G3-03`～`EP-G3-04` 三份历史 trace 的 observation 回归稳定；因缺 source manifest 保持 `ambiguous`。证据：`engineering_evidence/observation_v0_1/`、`tests/test_v141_observation.py`。
- [x] `EP-G3-05`～`EP-G3-07` 冻结 Canonical Raw v0.2（八类记录、结构化 NVTX、单 trace 相对纳秒时钟、source-row identity、lineage、资格字段），实现只读 gzip JSONL 转换与合成/历史回归。证据：`docs/v1_4_1/contracts/canonical_raw_schema_v0_2.json`、`canonical_raw_v0_2.md`、`tests/test_v141_canonical_raw.py`。
- [x] `EP-G3-08` 下游边界静态检查：禁止未来 S/A/B 导入 sqlite3 或直接引用 Nsight 私有表名。证据：`scripts/verify_canonical_raw_boundary.py`。
- [x] `EP-G3-09`～`EP-G3-10` Windows/Nsight `2026.2.1.210` adapter 审查，以及 Q0 observation scope 固定（目标 request 外未映射同步记 `HARNESS_OUTSIDE_REQUEST` warning；目标 request 内与非 Q0 trace 继续 fail closed）。

### Gate 4：S 同步语义层

**Gate verdict：`PASS`。** 只表示 S v0.2 的离线语义实现、版本化输出、合成 fixture、Q0 核心 expected 对照及历史 trace fail-closed 回归通过。

- [x] `EP-G4-01`～`EP-G4-02` 实现 stream/device/context/event completion scope、可观察依赖图与每个 physical sync 的 `W(s)`，以及 ownership、submission evidence、semantic frontier、唯一 terminal、0 ns tie、validity 与原因优先级。证据：`exposedpath_v141/sync_semantics.py`、`tests/test_v141_sync_semantics.py`。
- [x] `EP-G4-03`～`EP-G4-04` 验证 completed-before 活动仍在 `W(s)`、无依赖跨流重叠不进入 `W(s)`，且缺失 correlation 的 invalid 不被提交歧义掩盖。
- [x] `EP-G4-05` 冻结 S schema 与 `analyze-s` CLI，完成确定性 fixture、Raw→S 边界和历史 trace 回归。证据：`docs/v1_4_1/contracts/s_layer_schema_v0_2.json`、`docs/v1_4_1/s_layer_v0_2.md`、`engineering_evidence/s_layer_v0_2/historical_regression.json`。
- 注：Gate 6 合成 Q0 复核额外发现并修正一处 fail-closed 缺口——graph activity 缺少 node mapping 时，S 必须在判定 `GRAPH_MAPPING_UNSUPPORTED/INVALID` 的同时清空 `W(s)`、origin phase 与 cross-phase 派生状态。

### Gate 5：A/B，再到 D/Exposure Signature

**Gate verdict：`PASS`。** 只表示 A/B 与纯派生层 v0.2 的离线语义实现、严格输入联结、版本化输出、合成测试、边界检查、历史 Engineering fail-closed 回归和完整分支独立复审通过。

- [x] `EP-G5-01`～`EP-G5-02` 冻结 A/B 输入联结与窗口规则，实现面向 request/phase、互斥且保守的 A 与整数纳秒守恒／invalid-ambiguous 传播。证据：`exposedpath_v141/ab_inputs.py`、`a_accounting.py`、`intervals.py`、`docs/v1_4_1/contracts/ab_schema_v0_2.json`。
- [x] `EP-G5-03` 实现保持 per-sync provenance 的 B，禁止无依据跨同步求和。证据：`exposedpath_v141/b_provenance.py`、`tests/test_v141_b_provenance.py`。
- [x] `EP-G5-04`～`EP-G5-05` 仅从冻结后的 A/B 派生 D 与 Exposure Signature（零分母输出 `null`，不输出根因/瓶颈标签）。证据：`exposedpath_v141/derived.py`、`docs/v1_4_1/contracts/derived_schema_v0_2.json`。
- [x] `EP-G5-06` 完成互斥、守恒、provenance、版本与 validity 传播的离线验收和独立复审（`Approved`）。历史链路无合格 A window、S 446 invalid 且 B 446 `B_INVALID`。证据：`engineering_evidence/ab_v0_2/historical_regression.json`。

### Gate 6：Q0 资格验证

**Gate verdict：`PASS`（2026-09-20）。Q0 = `PASS`。** frozen run `q0-win-4090-20260920-gate6-final-04` 在 package/analyzer `0.2.2`、frozen HEAD `4720881f400762d98f4d0759b1ffb55708968970`、implementation `ec945a67f048ff624e3701229d287894b9701ea3`、formal binary SHA256 `4DFF82028F4FCFB57D42ABF061AE8962C1867DCE19DF23808D223B425868FC80` 下完成：21/21 real `REAL_CASE_PASS`、2/2 synthetic-only PASS、23/23 `SYNTHETIC_PASS`，且只存在一份 `q0_gate_report.json`（`exposedpath-q0-gate/0.2.0`、`23/23`、`verdict=PASS`、`q0_status=PASS`、report count `1`，SHA256 `3A94F8B9B65294D82929EF183C59C4C84177D489F5AE9E8AF56FDDD676178967`）。

该 PASS 只说明当前 analyzer 在本目标 observation stack（Windows + RTX 4090 + CUDA 12.4.131 + Nsight 2026.2.1）上取得 **Q0 正确性资格**；不等于 Engineering Pilot、Pilot、Protocol Freeze 或 Formal 结果，也不建立第二平台等价性。完整 closeout（身份、哈希、缺失 prepare-time sidecar 边界、根因映射、实现成熟度、已关闭诊断分支）见 `docs/v1_4_1/gate6_closeout_v0_1.md`。

`final-01`/`final-02`/`final-03` 永久保持 frozen incomplete，不 retry、不 resume、不拼接、不升级；不得重跑 Gate 6 GPU collection / synthetic / gate aggregation。

### Gate 6 历史编号索引（试错过程的压缩记录，仅用于追溯）

Gate 6 的工程试错已收敛为 `docs/v1_4_1/gate6_closeout_v0_1.md` 中的四类根因；下表只保留编号、结果与去向，不重述过程。

| 编号 | 结果摘要 | 证据／去向 |
|---|---|---|
| `EP-G6-01` | 受控 CUDA Q0 微程序 + 机器可读 manifest：23 oracle case 严格映射，21 native seed + 2 纯合成；`--list-cases` 21/21 | `q0/cuda/exposedpath_q0.cu`、`q0/execution_manifest_v0_2.json` |
| `EP-G6-02` | GPU 前执行准备：结构化 `nsys` argv、每 case source manifest、输入哈希、不可覆盖输出与 dry-run；23 个合成 profile 经正式 S/A/B 与独立 evaluator 对照 | `exposedpath_v141/q0_execution.py`、`q0_synthetic.py`、`q0_evaluator.py` |
| `EP-G6-02A` | GPU 前集成验收（编译/list、Windows dry-run、23/23 合成对照、静态边界与全仓回归） | `engineering_evidence/q0_pre_gpu_v0_2/readiness_report.json` |
| `EP-G6-02B` | 真实 Q0 执行适配：Profiler API 控制 capture、显式 GPU 身份、单 case executor/receipt、三种受控 fault、真实 observed/evaluator、23-case 聚合、CLI 与 Windows runbook | `q0_collection.py`、`q0_faults.py`、`q0_real.py`、`q0_gate.py`、`docs/v1_4_1/gate6_windows_server_runbook.md` |
| `EP-G6-02C` | 首次 Windows 实跑修复：GPU UUID 比较、Nsight `2026.2.1/3.25.0`、同步映射诊断、MSVC 14.39、受控设备工作显式排空 | 失败现场 r2 保持不可变 |
| `EP-G6-02D` | r3：Q0 observation scope 与下游合同错位修复（request 外同步 → harness warning；单阶段两窗口） | `EP-ISSUE-08`、`EP-ISSUE-09` |
| `EP-G6-02E` | r4：lazy-export 零行 KERNEL 表规范化与真实 `VALID_EMPTY` evaluator | `EP-ISSUE-10` |
| `EP-G6-02F` | r5：三个同源多线程 seed 的重复 target request 修复（coordinator 唯一持有 request/decode） | `EP-ISSUE-11` |
| `EP-G6-02G` | r6：删除 PTDS `cudaStreamQuery` 轮询，改一次 stream-ordered host callback | `EP-ISSUE-12` |
| `EP-G6-02H` | r7：target identity 唯一性过滤（非目标 request 可共存，零/重复目标仍 fail closed） | `EP-ISSUE-13` |
| `EP-G6-02I` | r8：仅 Graph case 增加一次 `--cuda-graph-trace=node` | `EP-ISSUE-14` |
| `EP-G6-02J` | r9：`wait_set_activity_labels` 改用无序、无重复的精确成员比较 | `EP-ISSUE-15` |
| `EP-G6-02K` | r10：仅 KERNEL-MEMOP case 预分配 512 MiB buffer，改用 10 ms kernel | `EP-ISSUE-16` |
| `EP-G6-02L` | memcpy-first 提交顺序（让 DMA 先进入执行） | `EP-ISSUE-16` |
| `EP-G6-02M` | coordinator/worker 双 Host 路径并发提交，消除同线程序列化 | `EP-ISSUE-16` |
| `EP-G6-02N` | worker launch 前增加立即结束的 `WORKER_KERNEL_MEMOP` marker | `EP-ISSUE-16` |
| `EP-G6-02O` | activity-specific marker ownership：只接受同线程、完整覆盖 enqueue API、text/cache 完整一致的 marker | `docs/superpowers/specs/2026-09-17-s-activity-marker-ownership-design.md`、`EP-ISSUE-17` |
| `EP-G6-02P` | 与正常 executor 隔离的 WDDM Engineering diagnostic（禁止 CUDA↔packet 一一对应或根因结论） | `exposedpath_v141/q0_wddm_diagnostic.py`、runbook §2.13 |
| `EP-G6-02Q` | 64 MiB H2D/10 ms 参数 diagnostic（独立 CLI 与 identity；正常 Q0 仍为 512 MiB/10 ms） | `exposedpath_v141/q0_kernel_memop_diagnostic.py` |
| `EP-G6-02R` | 环境快照增加 `async_engine_count`/`device_overlap`/`concurrent_kernels`，缺失即 fail closed | `--environment-json` |
| `EP-G6-02S` | 64 MiB D2H/10 ms 参数 diagnostic（唯一实验变量为 copy direction） | `exposedpath_v141/q0_kernel_memop_d2h_diagnostic.py`、`EP-G6-04B` |
| `EP-G6-03` | r1～r10 与失败 diagnostic 一律 fail-fast 停止并保留现场，不覆盖、不升级资格 | 各 `rN` 证据目录 |
| `EP-G6-04` | 64 MiB/10 ms 单例：overlap=`0`（间隔 `629183 ns`）→ 按预定规则停止，不进入 64 MiB/1 ms | 历史 diagnostic 证据 |
| `EP-G6-04A` | GPU3 RTX 4090 能力探针：`async_engine_count=5`、`device_overlap=1`、`concurrent_kernels=1`（只证明设备声明能力） | 服务器 capability/receipt/ZIP SHA256 |
| `EP-G6-04B` | 64 MiB D2H/10 ms 单例：真实 overlap=`0`、terminal=`KERNEL_A` → STOP（不进入 D2D、不调参、不建 r11） | `server_evidence_inbox/` |
| `EP-G6-05` | 输出唯一 Q0 gate report（final-04） | `gate/q0_gate_report.json`，SHA256 `3A94F8B9…` |
| `EP-G6-06` | 策略审查：synthetic 边界、候选平台 admission 设计批准（仅设计）、scope limitation 不批准 | `docs/v1_4_1/gate6_strategy_review_v0_1.md` |
| `EP-G6-07` | 候选平台 + construction admission：设计与判据已冻结；**非 Gate 6 阻塞项**，仅在需要第二平台（含 Linux Formal 平台）时按 Gate 9 重启 | `docs/v1_4_1/candidate_platform_admission_checklist_v0_1.md`、`candidate_platform_inventory_v0_1.md` |
| `EP-G6-08` | 固化 `KERNEL_MEMOP_MIXED` 的 synthetic coverage 与 synthetic↔real 边界（纯文档） | `gate6_strategy_review_v0_1.md` §4/§4.1 |
| `EP-G6-09` | construction amendment 收口：formal-shape 配对诊断 + amendment 冻结 + preflight + implementation（execution schema `0.2.1`、`measurement_initialization` policy） | `gate6_construction_amendment_v0_1.md`、runbook §3 |
| `EP-G6-10` | `final-01` 收口与 4 例 semantic FAIL 的 root triage（Phase-Spill / Missing-Corr / External / Multithread-Ordered / Overlapping-Host-Sync） | 见 `gate6_closeout_v0_1.md` §3 |
| `EP-G6-11` | Gate 6 closeout 与 final-04 落账（只读独立复核，未重跑任何采集） | `docs/v1_4_1/gate6_closeout_v0_1.md` |

## 4. Gate 6 根因、amendment 与实现去向（一句话版）

Gate 6 的失败簇收敛为四类工程／科学问题，逐类的完整映射见 `docs/v1_4_1/gate6_closeout_v0_1.md` §3：

1. **观测/采集适配**（r2～r8：Nsight 版本与可选表、lazy-export 零行表、request scope、target identity、graph node tracing）→ adapter 条件化 + fail closed，最终在 final-04 真实数据上通过。
2. **测量构造 / warm-up**（`Q0-KERNEL-MEMOP-001` 的 device overlap 恢复）→ `gate6_construction_amendment_v0_1.md`：仅该 case 使用 `PRE_CAPTURE_SAME_KERNEL_WARMUP`；底层机制仍不归因。
3. **ownership / phase / sync 语义投影**（External、Multithread-Ordered、Overlapping-Host-Sync、Query、Sync-D2H）→ `gate6_marker_ownership_amendment_v0_1.md` 与 `gate6_sync_projection_amendment_v0_1.md`：trusted marker authority、跨线程 worker ownership、registry-role-preserving projection（共享 helper）。
4. **oracle / evaluator 与证据聚合**（Phase-Spill 窗口规则、Missing-Corr secondary、wait-set 成员顺序、gate 唯一性）→ `gate6_phase_spill_amendment_v0_1.md`、`gate6_missing_corr_amendment_v0_2.md`、`gate6_q0_build_contract_amendment_v0_1.md`。

## 5. Gate 7～14 计划

### Gate 7：Runner 与执行链对齐

**2026-09-24 目录收敛（7.19）：** Gate7 PASS保持；根main是唯一日常代码入口，五个退休worktree在保全独有资料后正常移除，分支/tag保留。gate7-audit原四份未提交文档先原样封存为a867d541d01f683ccfc462fcdec31afeeefbaecf，两份事故说明标注历史后整合，不覆盖当前进度。清理核实冗余的bundle、相同DOCX和缓存，原始证据/ZIP/冻结dist保持不变；本地handoff仅作索引，不形成第二事实源。服务器仅准备单根/固定checkout方案，未执行变更。Gate8 NOT_RUN，不运行GPU/Nsight；本轮验证和清理细项见repository_layout及本地回执。

**2026-09-24 最终closeout（7.18）：Gate7 PASS，EP-G7-11 completed。** 唯一合格attempt为`fresh_8d64f75_20260924T084650Z_d75ef1b8a4fb46709dbb7cfc1c95d27f/collection/smoke_20260924T084657Z`，执行commit 8d64f7580d43d7c8e1cb7a416b459cec8f60b011、dirty=false。服务器执行、本地审计；完整ZIP/清单/77文件逐字节、源代码CRLF身份、manifest/prompt、run/wmpc、parity、四request token-ready边界、14telemetry、profile/REP/export/SQLite、legacy JSON/CSV/diagnostics和machine report均通过；审计前后证据未变。版本化依据与hash见`gate7_closeout_v0_1.md`。

- 本次launcher原始全量日志：1040 passed、1 skipped/140.76s（不是dced364成绩；本次-q未列skip原因，源码支持pre-3.12 portability skip解释，不声称skip执行通过）；compileall/verify/pre-model/evidence门均PASS。两pass各warmup1/repeat2成功、32/2 tokens/batch1、无EOS/OOM/exclusion/retry。export1成功/0.265s，SQLite只读integrity/schema及analyzer冻结验收本地复核与服务器报告一致，machine READY_FOR_SMALL_PILOT/errors=[]、exit0。
- 原始SQLite69条diagnostics中44条warning属于11个其他进程；目标PID50740无warning且有12个NVTX range/4个structured token sync。按既有gate7-legacy-analyzer/1保留原始诊断，不把它们或dropped unknown抹成零，不推断工具根因。legacy-only/A结构验证/window coverage unknown/measurement_validity NOT_ASSESSED全部保留，不称v1.4.1真实workload科学全链已通过。
- EP-G7-08～10既有条件加本次EP-G7-11全部成立，Gate7正式PASS；旧BLOCKED/interrupted和离线诊断均不追认。无新GPU/Nsight/测试采集，只有本地只读验证与文档更新；Gate8仍NOT_RUN，下一阶段待规划、未启动。保留此前7.17未提交文档。

以下7.17和更早checkpoint中的NOT_RUN、待授权、待部署均为历史状态，以7.18和closeout为准。

**2026-09-24 8d64f75服务器最小静态复验本地审计（7.17）：** 直接读取 `identity_8d64f75_20260924T082913Z_1418665342a544ae911caf9d58bbff80/transcript.txt`，SHA256=`CF0C15956237D3F79F9124764D10F1AC73965693178287802952D83C5F69BF92`；记录时间08:29:13–08:30:35Z（服务器本地16:29:13–16:30:35）。服务器执行、本地只读审计，本轮不重跑测试。HEAD=8d64f7580d43d7c8e1cb7a416b459cec8f60b011；仓库venv Python3.11.16实际adapter解析Git成功、commit正确、dirty=false；定向185 passed/72.74s。compileall、contract37/37、Canonical7模块、oracle、diff/show-check全部exit0，最终HEAD及clean检查通过。测试mask=-1，结束恢复3。**不是8d64f75的服务器全量测试，更不是fresh smoke**；dced364的1014/1结果只保留为旧提交历史。

- 环境/模型关联：07:20:13Z的dced364环境身份、07:21:33Z的模型23文件内容清单、07:34:16Z的compiler/marker文件快照仍可作为相同环境/模型的历史来源；来源提交/时间必须保留，执行前检查未漂移，不作为新smoke结果。已直接读到cl19.38.33135.0、MSVC14.38.33130、x64/x64、mask实值及两marker零字节/空文件SHA，7.15所列补证缺口已补齐。模型清单SHA仍为72465C906BAEB0CFA4FD94D21EF6C69C1CD8046BB68C61A94C02A1580D2541F9；revision unknown，模型本体未传回，未声称本地重算权重。实际loader输入与.cache辅助项分开记录。
- 源码只读审查：launcher STEP3显式传preflight UUID/PCI及strict Git/worktree；通用manifest验证后调用`pre-model` CLI（logs/12_pre_model_identity），检查commit/clean/GPU/mask/G1身份；非零、报告非PASS或hash读取错误调用Set-GateFailure/exit1，位于STEP4首次模型加载之前。STEP2仅准备tokenizer输入。验收缺失不后移、不放宽；本次185定向包含producer和真实PowerShell前置门回归。
- 下一步：固定8d64f75、既定模型/GPU和32/2/1/1/2配置的fresh执行草案；launcher自身全量/compileall/verify、manifest/pre-model、Pass0、Pass1/Nsight、后处理及final report全部执行。仅保存历史快照作provenance，不复制旧attempt结果充数。现无已知必须先追加的补证；当前环境漂移或其他CUDA工作负载不明则STOP。尚未获得本次GPU/Nsight授权，未执行。Gate7 NOT_RUN，旧attempt BLOCKED，Gate8 DO NOT START；本轮文档不需要新提交或服务器部署。

以下7.16及更早状态为历史记录，其中“尚未部署/复验”已被7.17取代。

**2026-09-24 fresh dced364 身份链故障 / bounded repair（7.16）：** 直接读取用户传回的 `fresh_dced364_20260924T074033Z_43e53591d86341b2b025e1daf174b62e` 中 `collection/smoke_20260924T074034Z`；服务器执行、本地只读审计。machine decision=BLOCKED、exit=1，Pass0/Pass1/REP→SQLite/SQLite validation/analyzer process 均 exit0，但 analyzer acceptance 因 manifest commit 缺失、evidence 因请求 UUID/PCI 缺失而失败。两个 pass 全部14条 telemetry 的 observed index/UUID/PCI 一致且 query exit0，requested UUID/PCI 均 null；不能把它解释为跑错 GPU。旧产物不补写、不重验追认。

- 根因已在本地真实 Git 子进程入口复现：adapter 的 `capture_output=True` 与 `stderr=DEVNULL` 冲突，Python 抛 ValueError 后被 manifest 两个 getter 吞成 null，并非已证明的服务器 PATH/权限/timeout 问题。另 launcher producer 未传已有 preflight UUID/PCI；通用 `SHA256:` 输出实为 prompt 哈希，却写入 machine manifest 哈希。
- 最小实现：adapter 用明确 stdout/stderr pipe，Git 保留失败 stderr；Gate7 producer 显式 worktree、严格 Git 查询（原异常进入日志，无替代值）、结构化传入 preflight GPU 字段；Pass0 前核验完整 commit/clean/GPU/mask/G1 Engineering 身份，失败即阻塞；报告分别保存真实 manifest 文件 SHA256 与 prompt SHA256。runner、analyzer、冻结 Measurement Contract/S/A/B/D、Q0、Gate6证据和 observation profile 不改。
- 扩展审计：两 pass 的 manifest SHA 为 `e8e8b87042d0eff0bdb80def97b2ce40a0363d07b060cdbaa75f78842c40bc5b`，prompt SHA 为 `4dffd0ddcbd3185c656ae4a27efaf5aab302febba6ead5df4d37d903a2091920`；run/wmpc、G1 natural、mask、32/2 tokens 一致。runner source SHA `f3765d96f161f13a879c44b1f98adf3c36c8a9a2fdc7ff136af929b98301a6c3` 与 dced364 的 CRLF 文件字节一致（不是把 LF/CRLF 文件哈希视作相同）。analyzer metadata commit=dced3646b536；fatal_errors为空、dropped unknown、已批准的 CUDA event optional warning 仍保留，不升级科学有效性。
- Tests first：先用实际 launcher Python producer + 临时真实 Git 仓库复现 null commit/异常被吞；再实现并验证 producer→manifest→现有 runner parity/telemetry（仅 GPU query 替身）及真实 Windows PowerShell pre-model block。新增负例覆盖 missing/malformed/mismatch/dirty/mask/Git error；未执行 GPU、真实 Nsight 或服务器命令。此前7.15未提交文档保留在同次提交。
- 本地Windows/Python3.12 CPU-only最终验证：定向185 passed（含新增26项）、全量1036 passed/5 skipped（219.40s；屏蔽CUDA PATH并确认无nvcc，五项均Q0 source编译检查）；compileall四目录、contract37/37、Canonical boundary7模块、oracle independence、git diff --check通过。真实PowerShell block与真实Git调用不等于服务器/GPU验证；完成本地逐项自审，未声称独立外部审查。旧 attempt BLOCKED，Gate7仍 NOT_RUN，EP-G7-11未验收。部署新提交并完成服务器静态复验后，也必须另行授权全新 smoke；不得复用本次证据改变 verdict。完整真实 workload Canonical→S→A/B 仍属于 Gate8。

以下7.15和更早段落为历史快照；其中“仅余环境补证/无代码缺陷/仅文档更新”等不再是当前执行指令，以7.16为准。

**2026-09-24 dced364 服务器静态/环境/模型原始记录本地审计（7.15）：** 直接读取 targeted_dced364_20260924T070511Z_75d74c2e649e4303bd65a290d4185ded、static_dced364_20260924T070829Z_9bfeacd94903497ba472240b54b10f70、identity_dced364_20260924T072013Z_400f5980c94548b79d7b2e8aac66b26c、model_dced364_20260924T072133Z_d4a3ac4169ab48a1bba6d4f7d1f703ae 的四份 transcript 及模型清单。服务器执行、本地审计，未重跑测试：新增 33 passed、定向 130 passed、全量 1014 passed/1 skipped（263.79s）；skip 明确为 test_python_source_portability.py:98 的 pre-3.12 编译时已拒绝该 f-string，非未知失败。compileall、contract37/37、Canonical、oracle、diff/show-check 与 verify_pilot_install -SkipTests 均 exit0。HEAD/parent 与部署身份一致，记录显示检查后 clean；本地无服务器文件系统的独立实时观测。

环境记录支持：Python3.11.16 / repo venv / Conda base、torch2.6.0+cu124 / CUDA12.4、transformers5.17.0、nvcc12.4.131、MSVC 环境变量14.38.33130；GPU3/目标 UUID/PCI/RTX4090/driver555.99、logical0 且唯一可见；Nsight2026.2.1.210-262137639646v0。**尚缺文件身份补证**：四份记录未输出实际 where cl 的首项及 cl.exe 文件版本，也未输出两个 0-byte marker 的绝对路径/length/SHA256。CUDA 两变量的名称仅见 transcript Host Application 命令文本，尚缺实值输出；一次纯文件/环境快照即可补齐，不需重跑静态测试或 GPU 初始化。不要混淆 Python 构建字符串 MSC v.1942 与当前 cl.exe。

**模型与输入：** 本地复核 model_sha256.csv 为23行、合计3098976006 bytes、SHA256 `72465C906BAEB0CFA4FD94D21EF6C69C1CD8046BB68C61A94C02A1580D2541F9`。模型本体未传回，未本地重算权重 hash。七个 loader 输入候选为 config.json、generation_config.json、merges.txt、model.safetensors、tokenizer.json、tokenizer_config.json、vocab.json；其余为13个 .cache 辅助文件及3个文档/仓库辅助文件，不据缓存文件名推断 revision。Engineering runner 的 model_revision 默认 unknown，manifest schema revision 仅要求 string，Gate7 合同未要求可解析 hub commit；因此 unknown+明确本地内容快照满足本次工程身份限制，不宣称 upstream revision 已知或 Formal 资格。fresh attempt 必须关联该清单、保留 unknown，模型内容若改变先 STOP。

源码核对：launcher STEP2 生成4组各32 tokens 的合成 token IDs；cli 使用 seed=42+i*1000、合法 vocab 范围，无 chat template。batch1 使用第一样本，prompt 文件在测量窗口外生成，并由两 pass 共用且校验 SHA256。32 input / 2 output（首 token prefill，第二 token decode）、warmup1/repeat2 符合 pilot_runner_contract §§2/4/5 和当前 launcher 默认范围；不构成 Pilot workload 选择。执行身份为 eager/fp16/sdpa、do_sample=false、G1_NATURAL/natural_token_ready、n1_intervention=null、run_role=PILOT/data_role=Engineering，非 N1 实验。实际新 prompt digest/manifest 由 fresh launcher 创建并回传，不提前伪造或要求另跑一遍。

**既有 JSON 适配核验：** 本地运行 dced364 的 validate_analyzer，只读取旧 JSON/SQLite/CSV，临时合成 manifest 提供旧 ecac542 commit 与明确 SYNTHETIC-SHAPE-CHECK-ONLY 身份（原旧诊断包没有完整 manifest）。结构兼容 PASS、issues=[]、窗口 coverage unknown/null；将临时 manifest 换成 dced364 则正确 BLOCKED（Analyzer/runner commit identity mismatch）。这是适配逻辑检查，不是旧 attempt 的 lineage 或新验收。14个源文件检查前后哈希不变；未运行 analyzer、Nsight、模型或 GPU。未发现需要改代码的缺陷。

**下一步最小动作与授权边界：** 补上述 cl/marker/mask 快照后，请求一次固定身份的完整 fresh smoke 授权；不重复手工静态检查，但不跳过 launcher 自身 static/verify。完整新目录关联四组快照、模型清单和最终补证，保留全部 machine report/日志/manifest/prompt/parity/telemetry/REP/SQLite/analyzer 产物；失败保留现场、不 resume/覆盖。成功进程码与 READY_FOR_SMALL_PILOT 仍须后续逐项审计，不直接 Gate7 PASS。本地 handoff 的新 final-review 草案为入口；本轮仅文档更新，无新提交/部署包。

**2026-09-24 用户批准的验收修订 / implementation checkpoint（7.14，取代 7.12/7.13 的待决状态）：** 权威执行计划 §6 冻结 `gate7-legacy-analyzer/1` 工程验收修订；这是对 Gate7 的显式修改，不修改 Measurement Contract。只适用于新执行 Engineering attempt；launcher 在任何采集前拒绝 ExistingSmokeDir/ResumeFrom，不覆盖或追认历史。保持静态、Pass0/Pass1、parity、telemetry、REP/SQLite 和 final machine report 全部门槛。

新增验证分支只接收明确的 exposedpath-v2 JSON/metadata/parser identity。校验 A/repeat 输出结构、同步明细类型/UID/时间、CSV 必需列、版本/commit/workload/manifest 身份和 diagnostics；拒绝空对象、缺产物、NaN/重复键、fatal/unreviewed warning 与新 dropped 状态。仅保留已批准 optional event-table warning 和 dropped_records_status=unknown。报告显式 legacy-only / ENGINEERING_INTEGRATION_ONLY / measurement_validity=NOT_ASSESSED；window_coverage count/duration=null 并给出原因；原 trace_quality 和同步明细保留，不构造 valid/total。A 标记 VALIDATED_STRUCTURE_ONLY，绝非科学守恒 PASS。SHA256 绑定本次 invocation 的 manifest/input/output/CSV，明确不伪装为 legacy 自带的 scientific lineage。

**测试与审查：** 先执行实际 PowerShell STEP6 validation block 红测，准确复现 sync_coverage missing；随后增加坏 CSV/矛盾 validity/非有限 diagnostics 红测和历史 resume 红测，再实现修复。自审发现 CSV/JSON 身份关联与摘要类型校验不足，先补 3 项红测后收紧校验。新增合成 fixture 不包含私有 trace 或服务器路径。最终 4 文件定向测试 130 passed（新增验收测试 33 项）；CPU-only 全量 1010 passed、5 skipped（141.10s，本地 Windows Python 3.12 venv，进程内 CUDA_VISIBLE_DEVICES=-1 并移除 CUDA PATH/确认 nvcc 不可见；5 skip 均为 Q0 CUDA source 的 nvcc 检查，不代表服务器 skip 原因）。compileall exposedpath/analysis/exposedpath_v141/scripts、contract 37/37、Canonical boundary、oracle independence 与 diff-check 均通过。本地自审覆盖 fail-close、native argv、report 传播、unknown 不补零及历史 evidence 防追认；不是独立外部评审、服务器或真实 Nsight 验证。生产 analyzer、runner、冻结 S/A/B/D、Q0、Gate6 evidence 和 observation profile 零修改。

**交付与后续：** 原有未提交进度记录保留并纳入同一次代码提交；本地根 AI_HANDOFF 为未跟踪接力索引，不提交私有路径。服务器静态复验通过后也不能直接运行 smoke；fresh 草案须另行授权，固定新提交/模型/环境/新目录并读取机器报告。Gate7 NOT_RUN、Gate8 DO NOT START。v1.4.1 完整 request A 已实现，真实 workload Raw→Canonical→S→A/B、completion、互斥守恒、unattributed、validity/coverage 的验收仍为 Gate8 EP-G8-02，不由本次 offline PASS 代替。

**2026-09-24 coverage 用途与字段充分性复核（7.13，收紧 7.12 建议）：** 用户原则同意分开记录 supported/B-valid，但要求 request/phase 范围、physical identity 去重、重叠与 unknown 处理有合同依据。coverage 仅用于揭示 A 归属/B 解释的证据覆盖与缺口，是质量/provenance 诊断，不是新增研究贡献指标，不能替代 request-level A 守恒或 validity；同步时长累计不是 request-visible exposure，同步 coverage 不是完整 request 的可解释比例。

- **分母：部分字段存在，不足以完成所要求的窗口统计。** legacy 实物有 6 个不同 physical_sync_uid、request/repeat 数字和 sync_start/end_ns，可证明已输出 6 行无重复；不能由此证明 physical sync universe 完整。repeat_results 只有 window_duration_ms，未输出窗口 start/end；4/6 phase 为整段 structured label。legacy UID 和数字 request/repeat 不能未经核对替代冻结 sync_identity 的 run/pass/request/repeat/origin/callsite/ordinal。不能按 2 条规范 phase 摘要过滤后声称完整分母，也不能在 adapter 中重新猜测 ownership/phase。
- **判定：冻结状态明确，legacy 不能无损映射。** Measurement Contract §9：VALID_NONEMPTY 与 VALID_EMPTY 可用于 A 有效归属，后者 B_NOT_APPLICABLE；AMBIGUOUS/INVALID 不可归有效同步。B 只有 B_VALID 才有有效解释。legacy wait_set_valid=false/NO_PENDING_ACTIVITY 并不证明冻结 INVALID 或 VALID_EMPTY；legacy B_valid 布尔也没有冻结 B_AMBIGUOUS/B_NOT_APPLICABLE 的状态区分。可原样保留 legacy 标志，不能命名为已恢复的 v1.4.1 supported/B-valid。
- **count/duration：不把旧 audit 的 sum 当作新规则。** frozen §10 要求 A 使用窗口裁剪、interval union、invalid 片段优先；§11 禁止 additive B total。count 应基于同一 universe 的 distinct physical identity；phase 计数不可直接相加成 request count。现物 6 条区间无同 request 重叠，但不证明对重叠输入适配正确。同步窗口并集诊断与逐调用时长加权是不同口径；当有效/无效 sync 重叠，简单 union(valid) 也不等于 A 可归属片段。当前机器输出未定义 coverage 的独立重叠优先级与跨 phase 计数约定，不由 adapter 自行补成科学规则。
- **零值与缺失：** 完整 universe 已知且为空才可记录 count=0；比例为 null/不适用而非 0% 或 100%。正数量、零总时长与空 universe 分开记录；缺少窗口/identity/状态则数值 null、明确原因，不能输出零或静默删行。INVALID、AMBIGUOUS、UNKNOWN、B_NOT_APPLICABLE 分开，不能折叠为 false；legacy 未提供的区分保持 unknown。上述为约束，尚未发布新的 schema 或改变 launcher 验收。

**集中待决事项：** (1) Gate7 是否接受明确标记 legacy-only、不能恢复窗口 coverage 的诊断报告（缺失保持 unknown），及此状态如何影响既有 analyzer gate；这属于验收映射决定，不因 offline PASS 自动放行。(2) 若必须具备 request/phase coverage，则需批准补充稳定 identity/窗口/状态的 producer-side 证据输出及对应范围，不能把完整 v1.4.1 链静默提前到 Gate7。(3) coverage 独立 schema 的跨 phase count 和重叠 duration 口径需在完整输入合同上明确，禁止借此改写冻结 A/S/B。建议优先裁决 (1)，把 legacy 诊断与后续 scientific coverage 分开；不再推荐直接把全明细 duration 求和作为窗口覆盖。

**实现与资格边界：** Gate7 当前调用 legacy analysis/exposed_accounting.py。v1.4.1 的完整 request A 拆分已有 a_accounting.py/ab_inputs.py/ab_bundle.py 实现：显式窗口、原子片段、invalid 优先、整数域守恒和去重校验；但真实 workload 的 Canonical→S→A/B 全链验收仍属 Gate8 EP-G8-02。此次离线 PASS 不替代该验收。本轮只读字段/源码核验并更新记录，未改代码或测试、未运行 GPU/Nsight；冻结合同与旧证据不变。生产修复继续暂停，不创建“全部 null 但 PASS”的适配来绕过门槛。

**2026-09-24 本地完整诊断包审计（取代下方“未收到完整产物”的当前状态）：** 已直接读取诊断 `postprocess_ecac542_20260924T040753Z_a95e202b974d48eca6824b4c2564b460`。本地复核 ZIP 2024855 bytes、SHA256 `89C745A85EA62B7AB32B413751AB18195F8AFA2DE807914DBBDC81F50EB94909`、14 文件 CRC 及解压字节一致；v2 清单固定哈希及 12/12 项文件哈希匹配。SQLite 只读 integrity_check=ok；helper 首次 export PASS/analyzer_allowed=true 与回执一致。identity 中 helper/analyzer 源哈希分别匹配 ecac542 Git blob 的 CRLF checkout 字节，不把 LF/CRLF 差异误判为代码变化。旧服务器原始 machine report 未包含在此包，关于其不变性仍为 identity/transcript/用户回传证据，不声称本地读取过该原件。

**已复现的阻塞与合同缺口：** 本地提取并执行当前 launcher STEP 6 的真实 validation block（不执行 analyzer/Nsight），给定 exit=0 和收到的 accounting_result.json，得到 analysis_ok=false、conservation=present、count/duration=unknown、errors=[sync_coverage missing]。PowerShell 对 A_summary 的大小写匹配正常。producer write_accounting_result 与 legacy metric spec §11 均未输出 sync_coverage；所以是 consumer/producer 合同脱节，不是 export 失败。离线诊断只检查 JSON 可解析，未覆盖此验收；不得称为完整 launcher PASS。

**必须先确认的映射，不擅自修复：** 当前 Gate7 计划、pilot_runner_contract §9/§10 及 server_smoke_test 未定义 launcher 的 sync_count_valid/sync_duration_valid_ms 应指 wait-set supported 还是 B-valid，也未明确分母是否为全部 b_sync_details。旧 summarize_small_pilot 使用 B_summary.full_request 且 duration=null；generate_p1_audit 则对所有 b_sync_details 分别累计 wait_set_valid 与 B_valid 对应的 sync_duration_ms。两者不能无条件互换。实物 B_summary.full_request 为 2/2，但 b_sync_details 共 6 条、B_valid=2；另外 4 条 wait_set_valid=false/NO_PENDING_ACTIVITY，phase 为整段 structured NVTX label。不得从原因字符串改判 supported、用 B 2/6 冒充 sync coverage，或按 full_request 摘要漏计其余 4 条。建议修复位置为 launcher 侧显式 legacy-output adapter，保留 supported/B-valid 两组诊断、来源和未知状态；其具体字段/分母/缺失处理需先获确认，不改变 analyzer/S 语义。批准后先用脱敏 producer-shaped fixture 做真实 consumer 红测，再实现适配；本轮未添加测试或修改生产代码。

**trace_quality / diagnostics 边界：** event activity table unavailable 为 legacy optional warning；fatal_errors=[] 不等于无采集诊断。SQLite DIAGNOSTIC_EVENT 有其他 globalPid 的 NVTX/CUDA 初始化或未采集警告；持有 NVTX/runtime 行的进程 globalPid 为 282358666231808，其日志记录 12 NVTX / 41975 CUDA events，未出现上述 severity=2 警告。不能据此推导 dropped=0：analyzer dropped_records_status 仍为 unknown，保持原值。B 摘要/structured phase 局限不升级为 v1.4.1 科学语义验收，也不在本次字段修复中扩大到 Gate8。

**本轮收口：** 仅更新进度与本地 handoff，保留原有未提交记录；HEAD/parent 不变，无新 commit/bundle/部署动作。生产代码、测试、REP、旧 machine report、Gate6 evidence、Measurement Contract、S/A/B/D、Q0 和 observation profile 均不修改。Gate7 NOT_RUN，fresh smoke PAUSED，Gate8 DO NOT START。以下 7.11 回执与草案按历史记录保留，不能再作为当前执行指令。

**Gate verdict：`PASS`（2026-09-24）。** EP-G7-08～11完成；唯一合格fresh及逐项证据见`gate7_closeout_v0_1.md`。旧BugCheck、BLOCKED_BY_NSYS和dced364身份链BLOCKED不追认；本地最终审计未运行GPU/Nsight或操作服务器。

**2026-09-24 用户回传的离线后处理回执（未直接取得完整服务器产物）：** commit `ecac54272230fe5feef517ad9d908c64e93d517f`，role `POSTPROCESSING_IMPLEMENTATION_VALIDATION`，诊断 id `postprocess_ecac542_20260924T040753Z_a95e202b974d48eca6824b4c2564b460`；Nsight `2026.2.1.210-262137639646v0`，repo .venv Python 3.11.16、base Conda gate7_py311。helper PASS、analyzer_allowed 检查通过，仅一次 export：PID 64844、exit 0、process_exited=true、timed_out=false、terminated_pid=null、validation_issues=[]、elapsed 0.312 秒。SQLite 2568192 bytes，SHA256 `310f119306414b7f740574566e59dcf9112c363141038125ab9e7230dc269b25`；成功 attempt/canonical/report 哈希一致，integrity/schema PASS、issues=[]、exit 0，legacy analyzer exit 0、accounting_result.json 可解析。源/副本 REP SHA256 均保持 `C2F561943C6465CA758845E8526652591363AD85EC8BCEAB074C9413AD6BB219`；原 machine report SHA256 保持 `CE3EFC198A3CA8D93B676AA77FEF1A5AB03E4409EE6E7E42B84D82D319192100`、原 verdict BLOCKED_BY_NSYS。结束 HEAD 不变/clean、无残留 nsys；独立 validation_result.json PASS/error=null。只证明该 REP 上真实离线成功路径的实现集成；未触发真实 timeout/kill/retry，不证明即时挂起根因修复。与前次手工诊断 SQLite hash 不同，不要求不同 export 产物逐字节相同；本次身份须以本次 REP lineage/attempt/canonical/report 一致性审计。

**清单补救边界：** 初次流式枚举把正在写入的 artifact_sha256.csv 纳入输入而发生占用错误；先前的 PASS 不保证清单生成成功。用户报告协调窗口仅修复清单生成（快照文件列表、排除 artifact_sha256*.csv、写新文件并逐项复核），没有重跑 export/analyzer、没有改仓库代码。旧清单保留，有效 artifact_sha256_v2.csv 含 12 文件、逐项校验通过，清单自身 SHA256 `FCF2FAF38F7B58F8EE5D54A8B7B5A9CA10DD88BF23E93EC6A68640FE36B58735`。补救发生在原 transcript 结束后，来源仅为用户回传；不能声称原 transcript 包含补救过程。本地 handoff 草案已改为先快照/排除所有清单，再计算和写入新清单。

**Analyzer scope 判断（沿用既有条款，不修改判据）：** exposedpath-v2 标记、CUDA event activity table unavailable 与 B valid=2/6 本身不违反 Gate7 integration smoke。依据：执行计划 §1/EP-G7-11 关注 runner/launcher 边界与身份；pilot_runner_contract §9 明确 A/B 来自 legacy analyzer，§10 尚不支持 full event synchronization recovery；此前已接受的 scope checkpoint 把真实 workload 完整 Canonical→S→A/B→D 链放在 Gate8 EP-G8-02。代码证据：analysis/accounting_utils.py 将 event_table 列为 missing_optional；gate7_smoke_validation.py 的必需表集合不含 event activity table；launcher STEP 6 要求 analyzer exit 0、可解析 JSON、a_summary 与 sync_coverage，并记录 count/duration coverage，未规定 B valid 比例阈值。故不能临时增加 6/6 阈值，也不能把 2/6 解释为 v1.4.1 语义 PASS。仅“JSON 可解析”的回执尚不能独立证明 a_summary/sync_coverage 字段齐全，需完整 accounting_result/SQLite/日志核验，尤其不得将缺表或 dropped-record 问题整体降为可忽略警告。

**2026-09-24 用户回传的服务器验证结果（非本助手亲自执行）：** HEAD `ecac54272230fe5feef517ad9d908c64e93d517f`，parent `5a37eb0848dea486c715750341ff8a07d0efcee1`，验证前后 porcelain 均为空；bundle `ExposedPath_Gate7_fixture_ecac542.bundle`，3038 bytes，SHA256 `832B2EE632218C476EBBD1CC877442F6226D1A63F50606E855A5FE59D67B92B7`，bundle verify 通过。环境为 Windows PowerShell 5.1.20348.2849、Python 3.11.16 Anaconda 构建，测试使用 repo `.venv`，base interpreter 属于 Conda `gate7_py311`；VS host/target x64，VCToolsVersion 14.38.33130，CUDA_DEVICE_ORDER=PCI_BUS_ID、CUDA_VISIBLE_DEVICES=3。单测 `1 passed in 1.27s`；后处理文件 `19 passed in 39.83s`；三文件 targeted suite `97 passed in 35.84s`；全量 `981 passed, 1 skipped in 182.84s`。compileall、contract 37/37 PASS（CONTRACT_INTERNAL_CONSISTENCY_ONLY）、Canonical boundary PASS（7 个下游模块）、oracle independence PASS（STATIC_ORACLE_AND_EVALUATOR_INDEPENDENCE）、diff-check、show-check 均成功；用户报告上述所有命令 exit 0。单个 skipped 原因未提供，保持 UNKNOWN，不由本地 skip 结果推断；本轮回执未包含新的 verify_pilot_install 结果。本地只核对了提交/parent/bundle 与回传摘要的一致性，未获得或逐文件审计服务器原始日志。

**后续操作边界：** 离线验证按用户回传已完成，不重复运行；完整目录及 v2 清单、独立清单修复回执待传回。fresh smoke 草案置于本地 AI_HANDOFF.md：继续固定 ecac542、核对环境与模型内容身份、先显式 verify_pilot_install，再由完整 launcher 自行执行静态/Pass0/Pass1/后处理/最终门槛；全新 evidence，不使用 ResumeFrom/ExistingSmokeDir/SkipStaticTests/DryRun。本轮未执行任何草案，未生成新提交或部署包；静态/离线成功不能授权 fresh GPU smoke，READY_FOR_SMALL_PILOT 机器字段也不能替代人工 Gate7 verdict。

**2026-09-24 Windows venv fixture checkpoint：** 服务器静态验证的 timeout/retry 测试中，`Popen.pid=63380`、fake exporter `os.getpid()=27820`；成功 retry 不写 PID 文件，因此不是 PID 文件被覆盖。Windows venv launcher 与实际 interpreter 为两个进程，结束 launcher 不能证明 exporter 当时已退出。本地新建 Windows venv 后，先运行原测试复现同一断言失败（`8364 != 10756`），再仅把共享 fake-exporter fixture 的 Windows 默认 executable 改为原安装位置的 `sys._base_executable`；非 Windows 保持 `sys.executable`，显式 executable override 保留。直接使用 base interpreter 不涉及复制/搬迁，无需引入 copied-executable 场景的 `PYTHONHOME`/`PATH` 设置。保留 `Popen PID == fake exporter os.getpid()`、terminated PID、退出确认、partial 保留、独立 retry 输出及 canonical promotion 断言，并在真实第二次 `Popen` 前检查第一个进程已退出。生产 `Popen`/`kill`/`wait`、Nsight observation profile、Gate 7 acceptance、runner、Measurement Contract、S/A/B/D、Q0 与 Gate 6 evidence 均未修改。此项仅为 Engineering/static-validation 修复，不是 Gate 7 acceptance，也不证明真实 Nsight 超时路径。

此前本地 Windows venv 验证：原 PID-sensitive 单测先 `1 failed`，修复后 `1 passed`；后处理测试文件 `19 passed`；服务器同款 targeted suite `97 passed`；CPU-only 全量 `977 passed, 5 skipped`（进程内移除 CUDA PATH、确认 nvcc 不可见并设置 `CUDA_VISIBLE_DEVICES=-1`）。`compileall exposedpath analysis exposedpath_v141 scripts`、contract 37/37、Canonical boundary、oracle independence 与 diff-check 均 PASS。随后用户回传的目标服务器验证见上；本助手未运行 GPU 或真实 Nsight。

**2026-09-23 scope / trace 审计与 repair checkpoint：** Gate 7 只验目标 Windows/RTX 4090 的 runner、identity、Pass0/Pass1、Token-ready、phase-boundary、CUDA+NVTX 和 launcher integration smoke；真实模型 workload 上完整 `Canonical Raw v1.4.1 → S → A/B → D / Exposure Signature` 首次属于 Gate 8 `EP-G8-02`，不提前纳入 Gate 7。前一次 fresh attempt 的已知边界是 `Pass0 completed → Pass1/Nsight launch boundary → system BugCheck 0x133`；exact root cause **NOT PROVEN**，不得归因 NVIDIA、Nsight、launcher script 或 admin PowerShell。Trace minimization 是删去 Gate 7 非必需采集项并分离后处理，**不是** BugCheck 根因修复。

上一轮 bounded launcher repair 将 Gate 7 `data_role` 显式设为 `Engineering`，静态门槛对齐 `pytest -p no:cacheprovider`、`compileall exposedpath analysis exposedpath_v141` 与同一 Python 的 `verify_pilot_install`；最终门槛实际验证六组 cross-pass parity、attempt accounting、physical/UUID/PCI/logical telemetry identity，缺证据或不一致 fail closed，`BLOCKED` machine report 对应非零进程码。Nsight collection profile 为 `--trace=cuda,nvtx --sample=none --cpuctxsw=none --cuda-memory-usage=false --cuda-trace-scope=process-tree --isr=false`，collection 不启用 stats；原流程按 `collection → 非空 .nsys-rep → 显式 SQLite export / schema 校验 → analyzer` 执行，并在启动前保存 exact argv、Nsight 版本与 observation-profile provenance。新 profile 与旧 smoke evidence **不可拼接验收**。其后 `799fb8d` 已在服务器执行一次新 Engineering smoke，结果见下；Gate 7 未判 `PASS`，Gate 8 不启动。

**2026-09-23 后处理可靠性修复 checkpoint：** 服务器报告的 `799fb8d` fresh smoke evidence id 为 `ep-g7-11-final-799fb8d-20260923T134309Z/smoke_20260923T134310Z`（绝对服务器位置保留在私有交接记录，不纳入仓库）。Pass0/Pass1 与最小 collection 完成，REP 大小 `979593` bytes、SHA256 `C2F561943C6465CA758845E8526652591363AD85EC8BCEAB074C9413AD6BB219`；即时 export 处理 `43074` events 后约 51% 停滞，人工仅结束该 exporter PID，launcher 正确报告 `BLOCKED_BY_NSYS`。相同 hash 的 REP 副本稍后离线导出 `2568192`-byte SQLite（SHA256 `DE064BFB37FF1CA3D9FEF240278E8BF9C1F531308D83B712B7FD3008373C5A6C`），`PRAGMA integrity_check=ok`、46 tables，`analysis/exposed_accounting.py` exit 0/`ACCOUNTING COMPLETE`；这只是否定 REP 固有不可导出的解释，exact Nsight internal hang root cause **NOT PROVEN**。本轮代码仅在 profile exit 后增加有界 REP 稳定/可读/哈希 gate、单次 180 秒且最多两次独立路径 export、仅结束超时 attempt 自身 PID、保留 stdout/stderr/partial SQLite、REP hash 复核、integrity+Gate7 必需 CUDA/NVTX/metadata 表及关键字段校验、同目录原子且无覆盖的 canonical 链接 promotion 与 SHA256 对照、Analyzer 前再次校验；旧 machine report 不可被 resume 覆写，恢复时核对后处理 PASS/attempt/REP/SQLite 身份。可选 `nsys stats` 不再位于 acceptance 主链。上述 schema gate 只检查 Engineering export 完整性，不把真实 workload 的完整 v1.4.1 science chain 提前移入 Gate7。既有 profile launch 对含空格路径的完整执行尚无验证，本轮不声称通用空格路径支持；目标服务器路径需在后续部署前核对。Nsight observation profile、runner、Measurement Contract、S/A/B/D、Q0 与 Gate 6 证据不变。原 attempt 保持 `BLOCKED_BY_NSYS`，诊断 SQLite 不回填；修复尚未获 GPU smoke 授权。

本地 Windows argv/path 二审：新增纯 mock 回归，以含空格路径下的测试可执行文件副本运行 fake exporter，同时覆盖含空格 REP、输出 SQLite、stdout/stderr 文件和逐项 argv；实际走 `Popen(argv, shell=False)`，无生产实现改动。该回归不等于目标服务器真实 Nsight 或 elevated parent 验证；原 profile launch 的通用空格路径限制仍在。新增/相关定向测试 `97 passed`；全仓 CPU-only `977 passed, 5 skipped`（在 Python 进程内屏蔽本机 nvcc 并设 `CUDA_VISIBLE_DEVICES=-1`，不等于目标服务器 GPU smoke）；`compileall`、Measurement Contract `37/37 PASS`、Canonical boundary 与 oracle independence 均 PASS。一次未成功屏蔽本机 CUDA 13 nvcc 的全仓尝试为 `953 passed, 1 failed, 4 errors`，失败局限 Q0 CUDA source 编译夹具；未据此改动 Q0 或冻结证据。

**重审计结论（2026-09-20）：** 原 `EP-G7-01`～`EP-G7-07` 的 7 个行政步骤压缩为 4 个可执行步骤（`EP-G7-08`～`EP-G7-11`）。合并的是**同一工程单元**（runner 语义/身份、identity/parity/schema、平台适配、验证与验收），没有合并彼此独立的科学 acceptance 判据：每一步内部仍逐条保留各自的 PASS/STOP 条件。执行计划：`docs/superpowers/plans/2026-09-20-gate7-execution-plan.md`；旧计划 `docs/superpowers/plans/2026-09-17-gate7-isolated-plan.md` 仅作历史记录。

**平台范围决定（2026-09-20，显式 scope 决定，不是静默弱化）：** 项目当前只声明**一个**目标 observation stack（Windows + RTX 4090 + CUDA 12.4.131 + Nsight 2026.2.1），Q0 资格也仅在该栈取得。因此 Gate 7 的“合同等价”**只在当前声明的目标平台上要求真实 GPU smoke 证据**。runner/launcher 仍必须完成平台适配隔离（核心不得硬编码 Windows 路径/命令/shell）；“声称支持第二平台（含 Linux）”所需的 Linux launcher、smoke、平台资格检查与 Linux Q0 归入 Gate 9。**任一平台在通过该平台的真实 smoke 前不得声称受支持。**

- [x] `EP-G7-08`（2026-09-21 完成，合并旧 `EP-G7-01`+`EP-G7-02`）
  - **Objective**：首 Token 与后续 Token 使用同一个可观察 completion 语义；G1 自然逐 Token 同步与 N1 人为干预以互斥、机器可读的模式身份表达。
  - **Why**：`EP-ISSUE-01` 使两类 Token 的完成边界不同，而这个差别会直接进入 A 窗口与 phase 定义；模式不分离则 N1 的人为同步会被误读为 G1 的自然行为。
  - **Implementation**：更新 `exposedpath/runner.py` 的 Token 边界取值与 `docs/pilot_runner_contract.md`；引入模式身份字段并实现非法组合 fail closed。测试先行。
  - **Evidence**：新增 `tests/test_runner_token_ready.py`，覆盖首/后续统一 Host-readable helper、首 Token/后续 Token EOS 均复用 Host 值、边界完整性/单调性、时间倒序与缺失边界 fail closed、机器可读边界记录、phase range 在校验/cleanup 前关闭、G1/N1 身份互斥、非法模式、双侧缺失 mode identity fail closed、N1 执行禁止及 Pass0/Pass1 Token-ready 行为一致；定向回归 `155 passed`，完整 CPU suite `845 passed, 3 failed, 4 errors`（均为既有 server smoke 与本机 CUDA 13/CP936 Q0 fixture 编译问题），合同 `37/37 PASS`，Canonical Raw 边界 `PASS`。
  - **PASS**：首/后续 Token 均通过同一 `device_to_host_token_ids` completion helper；runner 的 `inference_end_ns` 对应最后一个 Token-ready 完成点，legacy phase ranges 在随后校验/cleanup 前关闭；G1 使用 `natural_token_ready`，N1 仅建立 `n1_intervention` 身份且执行 fail closed；未修改 Measurement Contract 或 `exposedpath_v141`。严格 Pass0/Pass1 phase-boundary parity 仍属于 `EP-G7-09`，本步不提前宣称。
  - **STOP**：若修正边界需要改动 Measurement Contract 语义或 `exposedpath_v141` 语义 → 停止并单独提出。
  - **Dependency**：无（Gate 7 第一个可执行步骤；只依赖已冻结的 Gate 1 合同）。
  - **Unlock**：逐 Token 边界可比较，N1/G1 不会被静默混用。
- [x] `EP-G7-09`（2026-09-21 完成，合并旧 `EP-G7-03`+`EP-G7-04`）
  - **Objective**：冻结并证明 Pass0/Pass1 的输入、身份、phase boundary 与执行策略等价；补齐环境快照、early EOS、OOM、exclusion、retry、attempt 与 data role 字段。
  - **Why**：Pass0/Pass1 若不等价，profiler overhead 与执行差异会被混同为模型行为；缺失的 exclusion/retry/attempt 字段会让“计划 repeat 数”与“有效样本数”不可区分。
  - **Implementation**：复用既有 `wmpc_manifest.json`／`inference_results.jsonl`／`exclusion_log.jsonl` 结构补齐字段并加入机器可读 parity 检查；不新建平行 manifest 体系。
  - **Evidence**：`exposedpath/results.py` 为每条 attempt 写入 `repeat_index`/`retry_index`/`is_retry`/`attempt_uid`/`retry_of_attempt_uid`/`attempt_plan_version` 与 `data_role`/`run_role`/`study_mode`/`phase_boundary_policy_version`；exclusion 写入冻结 `exclusion_reason` 码与 `early_eos`/`oom`/`output_len_*` 证据；`exposedpath/runner.py` 写出 `cross_pass_parity.json`（schema `exposedpath-v3-cross-pass-2`）六组冻结身份并在 pass 结束前校验 planned repeat index 恰好记账一次（否则 `sys.exit(1)`）；`exposedpath/cross_pass_validator.py` 增加 `PARITY_*_FIELDS`／`PASS_PARITY_IDENTITY_MISSING`／`PASS_ATTEMPT_ACCOUNTING_MISMATCH` 与 `summarize_attempt_records`／`load_attempt_accounting`／`validate_attempt_accounting`；新增 `tests/test_runner_pass_parity.py`（真实 parity writer + JSONL 账目；等价通过、缺失/重复/有意差异 fail closed），并更新 `tests/test_small_pilot.py`、`tests/test_exposedpath_v3.py`、`tests/test_runner_token_ready.py` 的受影响夹具。
  - **PASS**：等价输入 `validate_pair` = `[PASS_PARITY_OK]`、`validate_attempt_accounting` = `[PASS_PARITY_OK]`；任一必需字段缺失 → `PASS_PARITY_IDENTITY_MISSING`；token-ready/环境/attempt-plan 的有意差异 → `PASS_EXECUTION_PARITY_MISMATCH`；exclusion 原因、retry、缺失/重复 repeat index 的差异 → `PASS_ATTEMPT_ACCOUNTING_MISMATCH`；缺失 role、未知 exclusion 码、无父 attempt 的 retry 直接抛错而非写 null/0。定向 `158 passed`，完整 CPU suite `874 passed, 3 failed, 4 errors`（失败/错误集合与既有基线相同），合同 `37/37 PASS`，Canonical Raw 边界 `PASS`，`compileall` 与 `git diff --check` PASS。
  - **STOP**：若要求把缺字段降级为零值/默认值来让检查通过 → 停止。
  - **Dependency**：与 `EP-G7-08` 无相互依赖，可并行；两者都必须先于 `EP-G7-11` 完成。
  - **Unlock**：Pass0/Pass1 可配对比较，exclusion/retry 规则有机器可读依据。
- [x] `EP-G7-10`（2026-09-21 完成，合并旧 `EP-G7-05`＋旧 `EP-G7-06` 的基线失败部分）
  - **Objective**：把 Windows PowerShell、平台探测、Nsight 调用收敛到 adapter/launcher；处置两项既有 smoke 失败。
  - **Why**：平台差异目前散落在脚本中，任何第二平台（Gate 9）都会重新暴露同类问题；未解释的基线失败会让后续回归无法区分“新缺陷”与“旧噪声”。
  - **Implementation**：runner 核心改用 `pathlib` 与结构化子进程参数；平台特定逻辑下沉到 adapter/launcher；修复或按平台范围决定明确重界定 `tests/test_server_smoke_script.py::test_dry_run` 与 `::test_spaces`。
  - **Evidence**（无 GPU）：新增 `exposedpath/platform_adapter.py` 作为唯一 Python 侧平台边界（平台身份、可执行后缀、工具解析、结构化 argv、`ToolUnavailableError`/`ToolExecutionError` fail closed），包内仅此模块导入 `subprocess`；`exposedpath/runner.py` 的 driver-version 与 telemetry 查询、`exposedpath/manifest.py` 的 driver/git provenance 全部改经 adapter（字段名与取值语义不变，无 schema 变更）；新增 `tests/test_platform_adapter.py` 覆盖平台身份、`.exe` 规则、解析顺序、无 shell 的字面量传参、fail closed，以及“核心模块不得导入 `subprocess`／不得出现裸工具名与 `shell=True`”的结构不变式。两项 smoke 失败根因：`tests/test_server_smoke_script.py::_run` 以裸名 `"powershell"` 启动宿主、且 launcher 的 `Resolve-Executable python` 依赖环境 `PATH`；受控复现（`PATH = System32 + WindowsPowerShell`，无 python）得到 launcher `exit 1` + `ERROR: Cannot resolve PythonExe`，即该两项的 `assert 0 == 1`，`PATH` 连 PowerShell 目录都缺失时则表现为 `FileNotFoundError`。修复：显式解析 PowerShell（`shutil.which` → `%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe`）、显式传 `-PythonExe sys.executable`、失败时在断言消息中回显 stdout/stderr，并把同文件 `test_import` 的裸 `python` 一并改为 `sys.executable`；新增回归 `test_dry_run_is_independent_of_ambient_path`（PATH 去 python 仍须 `exit 0`）与 `test_launcher_invocation_does_not_use_bare_powershell_name`（AST 断言 `subprocess.run` 首参不得为裸字符串）。
  - **PASS**：`tests/test_platform_adapter.py` 20 passed；`tests/test_server_smoke_script.py` 31 passed（含 PATH 去 python 的回归）；`tests/test_server_smoke_script.py::test_dry_run`、`::test_spaces` 在默认与受控 `PATH` 两种环境下均 `exit 0`，**不再计为未知失败**；两项失败为测试非封闭而非产品缺陷（launcher 语义未改，仅显式化宿主与解释器）。
  - **STOP**：若某项必须先有真实 GPU 才能判定 → 移交 `EP-G7-11`，不得用 mock 结论代替。
  - **Dependency**：独立于 `EP-G7-08`/`EP-G7-09`，可并行；其结论不依赖 GPU。
  - **Unlock**：平台可移植性被结构性保护，测试基线不再含未解释失败。
- [x] `EP-G7-11`（2026-09-24完成；fresh 8d64f75完整证据逐项审计通过；合并旧EP-G7-06全量验证与EP-G7-07；旧attempt不追认）
  - **最终Evidence**：`gate7_closeout_v0_1.md`，本次launcher1040 passed/1 skipped、静态与verify门PASS、目标平台两pass及后处理完整通过；保留legacy-only工程限制。下述实现过程中的早期失败仍为历史，不是当前阻塞。
  - **Objective**：在 Windows/RTX 4090 上执行 runner 端到端 smoke（Pass0/Pass1、identity/phase boundary、exclusion/retry 记录），证明产出可被机器读取且与 Gate 7 合同一致，并完成 Gate 7 验收决定。
  - **Why**：只有真实 GPU smoke 能证明该执行链在真实执行栈上成立；Gate 8 必须以这份证据为入口。
  - **Implementation**：smoke 前置修复新增纯函数 `resolve_logical_cuda_index(physical_gpu_index, cuda_visible_devices)`，不读取 GPU 或 `torch.cuda.device_count()`；`manifest.py` 与 server smoke 共享该 helper，torch name 查询只使用 logical index，manifest 的 `gpu_index`/`gpu_index_physical` 保持 physical、`gpu_index_logical` 保持进程内 logical。`runner.py` 已有 remapping 不修改。修复部署及目标环境确认后，只执行既有 runner 链路并收集 manifest/receipt 证据。
  - **Evidence**：新增 `tests/test_gpu_index_mapping.py`；首轮旧实现上 3 项预期失败（helper 缺失、manifest 查询 index `3`、smoke 未共享 helper），独立复审后第二轮 3 项预期失败（空 mask 未拒绝、显式 logical 可绕过一致性检查、PowerShell `-c` 多行 argv 不安全），第三轮 4 项预期失败（禁用/垃圾/混合 mask 未拒绝、CUDA check 脚本空格路径未引用）。修复后相关 manifest/smoke 回归 `150 passed`；最终完整 CPU suite `910 passed, 1 failed, 4 errors`，唯一失败与 4 个 error 仍为既有本机 CUDA 13/CP936 下 Q0 CUDA fixture 编译问题。最终 diff 上 `compileall` PASS、Measurement Contract `37/37 PASS`、Canonical Raw boundary PASS、oracle/evaluator independence PASS，独立静态复审无剩余 Critical/Important；该阶段尚未运行目标平台 GPU smoke，后续 interrupted attempt 与本次 repair 状态见本节 checkpoint。
  - **PASS**：非 GPU 判据与目标平台真实 smoke 判据同时成立，且未修改 Measurement Contract 或 `exposedpath_v141` 计算语义。
  - **STOP**：任何真实 smoke 失败都保留现场并停止，不得用 mock 或局部测试替代；需要第二平台等价性时转 Gate 9。
  - **Dependency**：消费 `EP-G7-08`～`EP-G7-10` 的产物；是 Gate 7 verdict 的必要条件，必须最后执行。
  - **Unlock**：Gate 8 Engineering Pilot 获得唯一入口。

原编号处置（不得复用旧编号）：`EP-G7-01`→`EP-G7-08`；`EP-G7-02`→`EP-G7-08`；`EP-G7-03`→`EP-G7-09`；`EP-G7-04`→`EP-G7-09`；`EP-G7-05`→`EP-G7-10`；`EP-G7-06`→`EP-G7-10`（基线失败部分）＋`EP-G7-11`（全量验证部分）；`EP-G7-07`→`EP-G7-11`（其跨平台部分转入 Gate 9）。

### Gate 8：Engineering Pilot

**Gate verdict（7.89）：PASS，仅限[G8-ENGINEERING-EXIT/0.1](gate8_engineering_exit_amendment_v0_1.md)的工程执行链、可观测性接口及条件性accounting可行性。** [新证据裁决](gate8_warning_evidence_review_v0_1.md)以用户回传官方解释和目标实物关闭四warning工程阻塞，不声称已网页核实或零丢失。Qwen派生仍条件性，不授完整新版Q0/模型科学有效性/Formal资格。原Route A0.2标准下NOT_RUN及旧attempt BLOCKED不改；下方7.21～7.37差距/步骤均为历史，不得重新生成待办。

**本轮实证差距：** 在根main用现有8d64f75 Gate7 SQLite只读派生到`.local/diagnostics/gate8-gap-v0_1-20260925-r3/`：observation valid（不等于dropped=0）；Canonical identity AMBIGUOUS（缺pass/repeat）、selected_device_id=3但trace device_id=0；12个NVTX range中8 legacy/4 structured sync，无结构化request/phase。S exit1、354条全invalid；A/B exit1、0窗口、FAIL_CLOSED；D未执行。354是全进程而非request分母。原REP/SQLite/manifest/report四文件hash前后不变。只证明历史输入兼容性缺口，不是Gate8 evidence、不撤销Gate7 PASS。未运行pytest、GPU、真实Nsight/export。

**当前未决与下一步：** D1/D2及时间表示amendment已批准，本地文件计算入口已接通。肯定零丢失provider仍未落实，科学验收继续BLOCKED；新Q0/真实producer目标栈、模型admission与双pass运行尚未验证。当前无服务器操作，不能因本地测试完成勾选以下实验任务。

**7.21合同收敛：** 见`gate8_contract_decisions_v0_1.md`，细化上段但不冻结新语义。重新核对协议v2.1 §3.6，确认B_valid coverage分母已定义为“支持sync”，不是全部sync；支持率的physical universe/去重/null已有依据，仅duration运算及跨phase计数需报告细则。历史SQLite另证实physical3/logical0/Nsight inventory2/activity device0经PID/UUID/PCI可联结，给出明确adapter映射。D1推荐同trace边界点派生scope而不转换perf_counter；D2推荐调用裁剪时长加权（不是request exposure）；两者均待批准并版本化。零drop无肯定来源仍阻塞，无警告不能等价为0；不自动授权新增collector或扩大Q0。只读核验/文档更新，未跑测试或GPU/Nsight，历史Gate7诊断不升级。

**7.22批准及交付：** 用户接受D1/D2，仅授权设计/独立预期与文档提交推送。发布独立`G8-OBS-BOUNDARY/0.1.0`、`G8-COVERAGE/0.1.0`设计及`contracts/gate8/`两份Draft2020-12 schema，未改原MC/C/S/A-B合同正文和生产loader。手算规格覆盖三窗口、跨phase/重叠/零时长/空分母/unknown、身份映射与完整性负例；schema自身检查及8正例/11负例通过，3语义反例只验证不被shape检查冒充解决。目标2026.2归档与69条历史SQLite诊断仍未给出全会话肯定零证据，记录在`gate8_nsys_integrity_evidence_note_v0_1.md`。D1影响ownership/phase/device/correlation/完整性资格，须在实现diff后按影响矩阵验证；未执行Q0，不自动继承新版本资格、不撤销历史Gate6 PASS。计划及handoff同步；此设计提交不是服务器执行commit，服务器继续8d64f75，无部署操作。

**7.23本地第一批实现：** 用户授权基于8ea177e的根main tests-first实现。显式per-pass ledger/device adapter、实际runner共同point/host ledger、可重算scope、S/A共享ownership、独立D2报告和完整性入口已实现；package `0.3.0` / adapter `exposedpath-gate8-adapter/0.1.0`，旧默认路径保持。详见[实现状态与剩余清单](gate8_local_implementation_v0_1.md)。未修改冻结MC/schema、W(s)/A/B公式、Q0/oracle/evaluator或历史证据；新版本资格不继承。

本地Python 3.12.7确定性验证：新增四文件56 passed；CPU全量 `1092 passed, 5 skipped in 139.97s`。全量命令通过子进程设置 `CUDA_VISIBLE_DEVICES=-1`，仅在该进程PATH排除CUDA/nvcc，断言nvcc不可用后运行 `pytest -q -p no:cacheprovider -rs`；五项skip来自既有 `test_v141_q0_cuda_source.py` 的nvcc检查（93/109/121/367/478行），未修改skip规则。`compileall -q exposedpath analysis exposedpath_v141 scripts`、`validate-contract` 37/37、Canonical boundary（7模块）、oracle independence、`git diff --check`均通过。提交前角色冲突红测覆盖producer不得重标记，以及NVTX显式data_role冲突不得被兼容分支忽略。上述为本地CPU检查，不是服务器/真实Nsight或新Q0结果。

剩余：signed-int64 Raw/projection已保留，但旧A/B非负时间表示暂以明确错误阻塞；真实完整性provider仍UNKNOWN；实际producer文件编排及D/Signature发布包装未接通。只交付第一批，不要求部署/采集。手算与mock链路不替代真实workload；Gate7 PASS、Gate8 NOT_RUN不变。

**7.24本地接口收口：** 用户明确批准只限时间表示的新版本amendment。新增`G8-TIME-REPRESENTATION/0.1.0`、A/B与Derived 0.3 schema，旧0.2 schema不变；timestamp signed-int64，A/B duration uint64，精确差值最大2^64−1，无截零/平移/float中转。实际runner的pass/host ledger及receipt可落盘；只读input receipt绑定WMPC/prompt/source/producer/export，原子发布新Canonical/projection/S/A-B/coverage/Derived及自检索引，小型provenance字节保留，Raw不复制/改写。详见[实现v0.2](gate8_local_implementation_v0_2.md)。

真实入口UNKNOWN不产出A/B/D；合成肯定receipt仅允许`SYNTHETIC_CALCULATION_ONLY`，计划request失败仍阻塞；新A/B/Derived自身标`LOCAL_DETERMINISTIC_ONLY`、measurement validity NOT_ASSESSED、Q0 NOT_RUN。D在A/B不合格时不发布。不声明新Q0/真实Nsight/模型/双passoverhead已验证。本轮无服务器操作。

验证：本地Windows/Python3.12.7，Gate8七文件定向80 passed（34.81s）；CPU全量`pytest -q -p no:cacheprovider -rs`为1116 passed、5 skipped（149.93s）；仅测试进程设置CUDA_VISIBLE_DEVICES=-1并过滤CUDA PATH，确认无nvcc，五项skip均为既有Q0 CUDA source检查。`compileall -q exposedpath analysis exposedpath_v141 scripts`、`validate-contract`37/37（仅内部一致性）、Canonical boundary7模块、oracle independence（仅静态独立性）、diff-check通过。tests-first中间红测不是验收结果；最终回归包含旧Q0确定性测试，新资格仍须独立验证。未运行GPU/真实Nsight/export/服务器；旧schema、冻结Measurement Contract、Q0源/oracle及Gate6/7 closeout未改。

**7.25完整性/Q0计划：** 本轮只读历史REP身份、SQLite46表/69条diagnostics、collector日志与官方2026.2相关章节，不执行analyzer/Nsight。实际collector载入`cupti64_129.dll`且使用software trace；不能以torch CUDA版本代替collector组件版本。produced/collected口径不明，flush metadata与诊断文字待解释；没有肯定零丢失证明。B：一次安装只读取证，仍不足则一次厂商询证后停止循环搜索。既有证据含敏感环境信息，仅私有保存，不上传；用户应处理凭证风险。本轮不改原证据。

新版Q0计划覆盖23case影响：旧结论/旧Raw重放只用于旧路径兼容，不能提供新D1/identity/完整性资格；新profile默认21个真实策略（含seed+fault）+2 synthetic-only，新增signed/投影/identity/完整性负例为独立确定性补充。必要provider、Q0载体/资格封套、真实pre-model/双pass编排尚未验收；先证据方案、再本地必要接口、授权Q0、独立资格审计，最后另授权Gate8 workload。见[决策备忘录](gate8_integrity_q0_decision_memo_v0_1.md)。本轮无业务代码/测试运行，只有文档与只读查询；Gate7 PASS、Gate8 NOT_RUN。

- [x] `EP-G8-01`（7.88限定工程退出）同一最小workload及配对执行已由7.86核验，无扫描。
- [x] `EP-G8-02`（7.88限定工程退出）真实链路与条件性A已核，7.87分类修复收口；仅按G8-ENGINEERING-EXIT/0.1完成，原可信A/完整科学链义务未宣告满足，B/D后移。
- [x] `EP-G8-03`（7.88限定工程退出）coverage限制、存储、单次开销、成功/失败/排除已记录，不声称统计稳定或冻结Pilot阈值。
- [x] `EP-G8-04`（7.88限定工程退出）7.86/7.87报告及新amendment形成工程closeout；不作正式科学结果。

### Gate 9：Formal 平台资格检查

**7.27路线A覆盖：** EP-G9-01/02/04只核对当前平台增量资格，可共享G8身份记录，
不得用其Engineering verdict替代Formal资格。第二平台后移；EP-G9-03仅保留eager，
compile/graph后移。以下原任务保留编号及历史。

**Gate verdict：PASS（7.99，限定分域资格）。** 按[最终裁决](gate9_closeout_v0_1.md)复用历史资格并完成N1目标桥接/G1投影增量；仅当前固定栈、N1显式流A/合格单sync B、G1自然投影A，不授默认流完整B或Formal。7.96–7.98 BLOCKED为保留的历史，旧机器报告不改。当前不要求服务器操作。

- [x] `EP-G9-01` 已复用核定封存运行的GPU/driver/CUDA/framework/Nsight/OS/launcher及身份联结；不推断当前服务器状态。
- [x] `EP-G9-02` 7.99按合同完成分层复用及增量资格绑定：15b24ec目标桥接＋fe25d5b离线oracle，G1真实适用性事实＋7.97/7.98投影独立正反例；不自动授全部新版Q0，不要求完整重采。
- [x] `EP-G9-03` 既有最小eager实际配置/执行完成已核；compile/graph与G2按路线A后移，不作为当前前置。
- [x] `EP-G9-04` 7.99签发限定PASS及版本/域/claim边界；旧首评BLOCKED和原attempt原样保留，不重复检查或追索旧PID。

### Gate 10：可行域与 OOM 边界

**Gate verdict：`PASS`（7.102；7.111范围澄清）。** [收尾0.1](gate10_closeout_v0_1.md)：**固定平台、模型与执行配置下，选定G1候选点的一次Engineering可行性检查通过。** 仅32/2、128/2、512/2 batch1；非完整可行域、统计稳定域或容量边界。OOM边界/最大输入/最大输出/最大batch未探索，512不是输入上限，2不是输出上限，不推断其他配置可行。

7.110补充：[N1模型32/2三组限定Engineering可行性独立PASS](n1_model_feasibility_closeout_v0_1.md)，是实验准备依赖，不替代OOM探索，不重定义G1范围或授共同统计稳定性。

- `EP-G10-01` 原任务“预定义候选input/output/batch探测范围和停止规则”（编号保留）：
  - [x] 7.27/7.100缩减范围的三点候选、输入及停止规则/接线完成。
  - [ ] 原广域input/output/batch与容量探索设计未执行、后移；当前只需要选定点，不以容量极限为claim。
- `EP-G10-02` 原任务“记录OOM、early EOS、不稳定和retry”（编号保留）：
  - [x] 选定三点的实际token、未见OOM/EOS、无自动retry及128历史分析超时已记录；一次可行性完成。
  - [ ] 主动OOM边界、最大输入/输出/batch探索未执行、后移；重复稳定性不由单次数据替代，留Gate11。
- `EP-G10-03` 原任务“共同稳定范围和平台特定排除项”（编号保留）：
  - [x] 当前选定G1离散点的一次可行集合/已观察排除记录完成；N1 32/2三组准备依赖另行通过。
  - [ ] 原完整/共同稳定范围未确定；选定点统计政策待Pilot，更广可行域后移，不从离散点内插或外推。

后移是用户批准的范围澄清，不否定实物或重开检查。只有后续明确长上下文、长decode、更大batch或容量研究问题时，才提出相应有界增量，不为编号故意运行到OOM。

### Gate 11：Pilot

**Gate verdict：`PASS`（7.118，限定Pilot政策评估/Freeze输入准备）。** [共同w3审查与政策收尾](gate11_policy_closeout_v0_1.md)及[机器汇总](gate11_w3_pair_summary_v0_1.json)钉住新实物/原值及建议政策；[两批集中审查](gate11_warmup_policy_review_v0_1.md)和[预定裁决方法](gate11_policy_decision_v0_1.md)保留历史依据。不是30/30/预算完成即PASS；实际硬门成立，有限warmup/repeat、质量/扰动和claim收缩有记录。不授稳定性/10或5ms保证、信息增益或Formal；Gate12仍NOT_RUN，最终政策签字/版本冻结另行，原STOP_FOR_REVIEW/NOT_RUN/BLOCKED不改。

- [x] `EP-G11-01`（7.113）已选并执行G1自然32/2与512/2、N1显式流32/2 V0/Vmarker/V16；问题驱动，非按A效果选点，30run的实际配置/输入核对通过。
- [x] `EP-G11-02`（7.118）三批分层证据审查收口，不跨暖机/批次混池；新共同w3有30run/90实际暖机/15pair及双方观测适用实物。建议共同w3和正式6完整平衡block、repeat1/进程，依据有限conditioning/次序平衡/成本，不称充分收敛或精度保证；n3/6/12预算、原值及探索性区间/留出保留，政策确认留Gate12，不自动续采。
- [x] `EP-G11-03`（7.113首批采集依据与非Formal角色已记录）[原值/汇总](gate11_first_batch_summary_v0_1.json)、45A/30N1 B及身份/Raw交叉审查；不升级Engineering，不以此授全部政策或科学资格。
- [x] `EP-G11-04`（7.118）[限定政策收口](gate11_policy_closeout_v0_1.md)明确全部有效值/负差、whole-block原值/区间与敏感性、P0性能/P1解释不扣A、局部有界缺口/无法界定拒绝及所需单sync B硬门；h只为未保证精度候选，不设新数值放行门。有限claim收缩、成本和Freeze输入齐备；Gate12仅下一阶段本地确认/最终版本签字，未启动或授权Formal。

### Gate 12：Protocol Freeze

**Gate verdict：`PASS`（7.122，限定未来路线A）。** [签署发布](gate12_protocol_signed_v0_1.json)/[收尾](gate12_closeout_v0_1.md)绑定用户批准、固定实现/schema/registry/hash与限定资格；不是已采Formal、完整新版Q0或信息增益成立。原草案/候选状态保留历史。

- [x] `EP-G12-01`～`EP-G12-04`（7.122）五条件/w3/六block、对照/质量/统计/封套、125内容锁/11版本与窄资格适用及真实用户批准已签署；不是单凭CPU或文档勾选，不授精度/自然P0组成/完整新版Q0。
- [x] `EP-G12-05`（7.122）签署生效的失效规则：实质修改须新协议、受影响Formal失效；不回写旧角色/Raw/报告或按结果调规则。

### Gate 13：N1 与 G1

**Gate verdict：`BLOCKED`（7.124）。** 首槽prepare失败、模型未启动；原报告不改。修复本地CPU已验证，新的协议补丁/执行锁必须审查和重新签署后才能另行执行，尚无Formal测量或科学结论。

- [ ] `EP-G13-01`～`EP-G13-04`（7.122交付准备，非实验完成）按签署有限协议执行G1两端点及N1三组，公平baseline检验有限信息增益、允许不支持/不确定；不机械执行历史广域sweep。六block后停，单GPU请求内边界保持。

### Gate 14：G2

**Gate verdict：`NOT_RUN`。** 必须在 Correctness 和 Information Gain 证据成立后执行。

- [ ] `EP-G14-01`～`EP-G14-03`（7.27后移，当前路线不执行）G2真实优化与held-out decision-gain；按将来claim需要另决定，不是路线A先决条件。

## 6. 已知问题与风险

**未关闭／长期有效：**

- `EP-ISSUE-02`：三份历史 trace 缺少 source manifest。影响：validity 必须保持 `ambiguous`，不能升级数据资格。**永久限制**。
- `EP-ISSUE-03`（已指派，未关闭）：仓库全量测试长期保留两项既有本地 PowerShell smoke 失败 `tests/test_server_smoke_script.py::test_dry_run` 与 `::test_spaces`，与工作前基线相同，不属于任何 Gate 新增失败，也不影响 Gate 6 PASS（Gate 6 的判据是唯一 gate report，不依赖该 smoke 脚本）。**处置**：Gate 7 `EP-G7-10` 必须在 `EP-G7-11` 前给出修复或明确重界定结论；在此之前它仍是未解释的基线失败，不得当作“已解决”。
- `EP-ISSUE-04`：本机（Lenovo 82L5，Windows build 26200）存在 GTX 1650（4 GiB，driver package `581.57`，Toolkit/nvcc `V13.0.88`，Nsight 2026.1.1 系列），但**尚未完成 Candidate qualification**（driver API 与 runtime 版本未知、schema 未审查、独占性未确认、A7 未闭合），因此当前不得作为真实 Q0/workload 平台；仅允许离线工作与已批准的非 case qualification。静态盘点见 `docs/v1_4_1/candidate_platform_inventory_v0_1.md`。
- `EP-ISSUE-06`：S 层已建立 event/wait 查找索引并缓存重复 scope 建图；event/default-stream 密集型大 trace 的规模性能尚未在真实 Engineering 数据上验收。影响：需在 Engineering Pilot 记录耗时与峰值内存；不改变 S 语义正确性或数据资格。
- `EP-ISSUE-07`：本机环境变量 `CL` 被配置为 MSVC 目录，但该名称会被 `cl.exe`/`nvcc` 解释为隐式编译参数。Q0 编译入口只在子进程环境中移除 `CL/_CL_`，不修改用户系统环境；GPU 平台资格检查仍需记录并复核实际编译环境。
- `EP-ISSUE-16`（遗留未归因，**不再阻塞**）：512 MiB H2D、64 MiB H2D 与 64 MiB D2H 在 RTX 4090 上均未与 10 ms kernel 重叠；真实 trace 已排除相同/default stream、event wait、数据依赖和过早同步；GPU capability 为 `async_engine_count=5/device_overlap=1/concurrent_kernels=1`，只说明硬件声明支持相关能力。formal-shape 配对 diagnostic 证明 pre-capture same-kernel warm-up 可恢复该构造的 device overlap，因此“平台 incapable”解释不再成立；该 construction 已作为 manifest policy 在 final-04 验证为 `REAL_CASE_PASS`。**现有证据不能区分 WDDM／driver／Runtime／调度层，禁止根因归因，禁止在该平台重启参数搜索或诊断。**异平台 admission（`EP-G6-07`）只在需要第二平台时按 Gate 9 重启。
- `EP-ISSUE-18`（冻结发布副本，**本轮不修**）：`dist/exposedpath_v3_pilot_deploy/payload/analysis/exposed_accounting.py` 是被发布校验和钉住的旧副本，仍含 Python <3.12 不兼容 f-string；Gate 7 server smoke 不读取该副本。若未来复用 payload，必须另立任务并重签校验和，不得在本轮静默改写。

**已解决（保留历史，不再需要为正常前进执行而复查）：**

| 编号 | 结论 |
|---|---|
| `EP-ISSUE-01` | `EP-G7-08` 已统一首/后续 Token 的 Host-readable completion boundary；EOS 使用已读取 Host 值，`inference_end_ns` 截止于最后一个 Token-ready 完成点，phase ranges 在校验/cleanup 前关闭；严格跨 pass phase parity 留给 `EP-G7-09` |
| `EP-ISSUE-05` | 本地全页渲染与研究主体/协议文档 QA 已完成（渲染器只用于文档 QA，不改变研究 Gate） |
| `EP-ISSUE-08` | r2 捕获结束同步未映射；r3 证明新增显式排空具有唯一 runtime 映射 |
| `EP-ISSUE-09` | r3 request 后尾部同步无 runtime 候选；以唯一 full_request identity 限定 observation scope，标为 `HARNESS_OUTSIDE_REQUEST` warning |
| `EP-ISSUE-10` | Nsight `lazy=true` 零 kernel case 缺 KERNEL 表被误判缺表；已用条件化 adapter 与真实区间 oracle 修复 |
| `EP-ISSUE-11` | r5 PTDS worker 创建同 identity `full_request`；coordinator 唯一 request/decode 已生效 |
| `EP-ISSUE-12` | r6 `cudaStreamQuery` 轮询产生 31 条无 Runtime 映射同步；改用一次 stream-ordered host callback |
| `EP-ISSUE-13` | r7 resolver 误用全 trace request 总数作为唯一性条件；已改为只对完整 target identity 计数 |
| `EP-ISSUE-14` | r8 默认 graph-level tracing 无 node activity；仅 Graph case 增加 `--cuda-graph-trace=node` |
| `EP-ISSUE-15` | r9 evaluator 以通用 list equality 比较 wait-set；该字段改为唯一字符串集合比较 |
| `EP-ISSUE-17` | activity-specific marker ownership 已在真实单例上验证；`INVOCATION_BOUNDARY_INVALID` 不再出现 |
| `EP-ISSUE-19` | `7e67219` 的 Python <3.12 portability 修复及其验证已在本次同提交补记到唯一进度事实源，消除 handoff/SSOT 不一致 |
| `EP-ISSUE-20` | server smoke/manifest 的 physical/logical GPU index 混用已按 tests first 修复：共享纯 resolver，不用 `device_count()` 推断 physical identity，不修改 runner remapping |

## 7. 固定执行顺序与最近任务

**7.125现行覆盖：** Gate13首槽prepare失败BLOCKED，模型/collector未启动；本地修复已验证，补丁候选已绑定99f3bae、待新精确内容签署，禁止旧阶段B重试/续采。Gate12旧签署历史PASS、Gate7～11及全部限制保持，下方旧“唯一下一步阶段B”为历史。

**7.123现行覆盖：** Gate12限定签署PASS保持，阶段A原回执已本地核验通过；唯一下一步为用户显式阶段B，不重跑或包装。Gate13仍NOT_RUN，签署/静态成功不等于采集或信息增益；原报告/角色/UNKNOWN不改，完整归档和批次审查后才可清理准确名单中的重复中间文件。

**7.118现行覆盖：** Gate11限定政策审查PASS，唯一当前入口[政策收尾0.1](gate11_policy_closeout_v0_1.md)；没有本阶段必要新实物阻塞，不再执行旧Pilot/部署包。下一项Gate12本地确认共同w3、6完整block建议及有限claim并冻结版本/统计/排除/图表；精度不保证、UNKNOWN/NOT_ASSESSED及历史原报告不变。现在无服务器操作，以下覆盖语句均历史。

**7.114当前覆盖：** Gate11首批Pilot审查保持；原计划P0 warmup1/3最小本地接线/待审交付完成，目标批次未执行，Gate11 BLOCKED。30新进程/0profile用完60预算，不同时续profile、不自动执行或加采。Gate10范围与N1独立Engineering PASS保持；以§1和[对照合同](gate11_warmup_control_v0_1.md)为准，下方历史状态不重启。

**7.45当前覆盖：** PE原件已实审，静态路线结束；来源对齐§10的一次Engineering
来源观察提案已交协调审查。不能重跑7.44工具或继续索包，不能自动启用新profile。

**7.44当前覆盖：** 必要调用点映射已收口，条件性mode等价不能用旧模型Raw证明。
只准备来源对齐§9.3的一次限定静态调用点核查；未授权服务器操作，未新增准入或诊断版本。

**7.43当前覆盖：** 目标资料已到且本地加载观察/文件链已实现，见来源对齐§8。
不再按下方7.41索取快照，或按7.42重复实现task接口；下一步仅必要调用点的
mode/lifetime/correlation证据映射，不扩大工具或启动实验。新诊断receipt不是S准入。

**7.42当前覆盖：** 7.41的单次目标安装补证已成功且实物审计关闭；不要重复执行。
下一项为来源对齐§7的本地task/attempt观察接口及文件反例，不先放开S default/owner门。
服务器等待，不重新传输/部署/采集；ZIP未直接核验的限制保留。

**7.41当前覆盖：** 以来源对齐§4～5的一次只读补证为唯一外部待办。服务器不更新
checkout、不运行模型/collector；目标资料回传前不为形式增加scope准入实现。
7.39共享stream语义已批准；下方“模型epoch未决”等旧顺序不再要求重复裁决。

**7.39当前覆盖：** f5edc64目标服务器B phase修复关闭。用户已批准closed-prior并推进本地tests-first实现，不能截断W；新S0.3/A-B0.4窄域来源/失败验证见amendment0.1。Derived仍拒绝新版本，五历史INVALID不删。当前未证明一般torch模型lifetime/setup来源，先做必要本地映射；服务器无操作，7.38待批准与7.36待复验仅历史。

**7.36当前覆盖：** 0.2受控capture与c827b61离线复验原件已审计；本地S→B phase字段已最小修复并实文件复核，准备审查后的增量离线交付，服务器暂不操作。五范围外B_INVALID保持，Derived范围如改变需单独明确合同，不能借字段修复过滤。下述7.26询证/固定长路线均为历史；路线A和最近用户授权优先，厂商询证仍暂停。

**7.26覆盖说明：** 已直接读取目标安装盘点回执及四份完整说明，四文件bytes/SHA256本地复核全部一致。CPU sampling lost-events段落不能证明CUDA/NVTX完整性；条件性teardown/flush建议不等于每会话认证；API subset与cuda-trace-all-apis适用性保留询证。组件hash来自服务器回执、非本地二进制复算。已准备[英文草稿及有限决策路线](gate8_nsys_vendor_inquiry_v0_1.md)，未发送。安装搜索结束，服务器无下一操作；不再执行7.25安装指令。无生产/冻结合同变化，无新测试或实验成绩。Q0影响矩阵继续有效但资格未取得；Gate7 PASS、Gate8 NOT_RUN，UNKNOWN阻塞科学验收。

当前顺序：`Gate 1 合同 → Gate 2 oracle → Gate 3 Canonical Raw → Gate 4 S → Gate 5 A/B/D/Signature → Gate 6 Q0 → Gate 7 runner/执行链对齐 → Gate 8 Engineering Pilot → Gate 9～12 正式实验准备 → Gate 13 N1/G1 → Gate 14 G2`。Gate 0 已完成封存。

**最近应执行的任务（按顺序）：**

1. Gate7已正式收口，保留唯一合格fresh与版本化closeout；不再要求EP-G7-11重跑/补证，旧attempt不拼接、不追认。
2. 路线A已批准；0.2窄受控construction及B phase修复已有目标机实物证据。进入最小资格/模型本地准备，不重复修复复验；模型epoch未决，不扩支持域，全capture认证和厂商询证继续暂停。
3. 已完成的 `EP-G7-08`～`EP-G7-10` 不再产生新任务；如后续发现需要放宽其 fail-closed 判据，属于新计划项，不得直接修改。

（历史顺序，保留不删：`EP-G7-09` → `EP-G7-10` → `EP-G7-11`；`EP-G7-09` 已于 2026-09-21 完成。）

**Gate7验收：** EP-G7-11判据已同时成立并记录PASS；这不自动授权Gate8执行。

**Gate 6 冻结边界（不再产生新任务）：** `final-01`/`final-02`/`final-03` 永久 frozen incomplete，`final-04` 为唯一有效 PASS 证据；不得重跑 Gate 6 GPU collection、synthetic 或 gate aggregation，不回填缺失的 prepare-time sidecar，不对 WDDM/driver/Runtime 作根因归因；`EP-G6-07` 只在需要第二平台时按 Gate 9 重启。Gate 6 清理与诊断周期已关闭。

## 8. 计划调整记录

7.122（2026-10-09）：用户批准有限P0/P1、限定Formal和六block预算，版本化签署并完成Gate12限定PASS。固定e38fa91执行/分析；外部交付/归档控制层不改变测量语义，文档commit不冒充执行身份。旧候选/Raw/角色/报告原样保存，Gate13/14 NOT_RUN，本轮无服务器执行或删除。

7.121（2026-10-09）：先提交已验证实现e38fa91，再以独立未签署候选绑定执行/分析版本、125个源码/合同hash和限定资格；候选不自引用，保留真实字节seal及人类批准边界。n6预算/有限claim与签署仍待确认，不生成Formal采集任务；无服务器/实验操作，Gate12 NOT_RUN，旧角色与原件不升级。

7.120（2026-10-09）：恢复冻结前Formal封套、baseline/成块统计及实际CPU文件链，Pilot局部导入遮蔽修复；224 passed/0 failed/0 skipped及静态检查完成。只扩版本/元数据和公平分析，未改completion/流/同步/S/A/B；不签署、无新增资格或实验，DOCX原修改保留。

7.119（2026-10-02）：按用户授权完成Gate12本地科学审查及两份冻结草案，明确公平baseline/负结果、P0性能与P1机制双对象及精确迁移目标损失；六block推荐依据成本/有限次序平衡，不保证10/5ms。Formal阶段适用/预算仍待集中确认，当前实际角色消费者只接Engineering/Pilot，列出最小封套/统计/baseline版本与身份签字缺口而不扩Q0/平台。未修改业务/测量语义、DOCX或Raw、未冻结、无Formal数据或执行授权；Gate11限定PASS、Gate12 NOT_RUN。

7.118（2026-10-02）：已批准共同w3追加Pilot实物一次审查完成；30run/90实际暖机/15pair、45A/30N1单sync B硬门有证据，按7.116预定方法完成有限运行/质量/扰动与精度政策。建议正式6完整平衡block、共同w3、repeat1，不承诺精度/稳定收益；撤去精细E2E排名/精确P1→P0迁移claim，保留有限观测归属与信息增益待检问题。预算结束不再加采，Gate11限定政策PASS、Gate12未启动；不改S/A/B/支持域/诊断门，不冻结Protocol或影响Formal（尚无），原件/旧判定及用户DOCX保留。成本按新实物上修而非沿旧估计部署。

7.117（2026-10-01）：用户批准唯一共同w3五条件3block、额外30模型进程/15profile预算；最小版本化配对接线及实际文件链CPU验证、固定增量交付准备。复用已批准暖机/流/测量语义，不改S/A/B公式/必要集合/诊断或旧资格；仅未来新Pilot适用。预算后集中确定最终政策，h仍候选、三block区间不保证充分；没有服务器/采集/Formal变更，原Raw/报告及DOCX保持，Gate11 BLOCKED、Freeze未启动。

7.116（2026-10-01）：用户要求先收敛两批Pilot的政策/预算，完成窄原始文献核对、Request/phase/N1解释尺度候选、n/成本敏感性及批次后一次裁决/claim收缩规则。仍只提共同w3五条件3block额外30进程/15profile；原60耗尽，预算未批准，不实现/交付/执行，不增加点位/暖机扫描/进程内框架。h不是已冻结效应门，n6不是充分性结论；保留signed差及未知、旧报告与DOCX，不改S/A/B/测量合同，无Formal数据受影响。Gate11 BLOCKED，Gate12未启动。

7.113（2026-10-01）：首批新Pilot原件本地审查闭合执行/身份、45A与30N1 B证据，限定政策估计可用；Gate11 BLOCKED，warmup/repeat/数值政策未定。只推荐既定剩余预算中的P0 warmup1/3方向，不增点/同时加profile，不执行或自动授下一批。无研究定义/schema/S/A/B改动，无Protocol Freeze或Formal数据受影响；原件/报告及用户DOCX保持。

7.114（2026-10-01）：用户批准限定P0 warmup1/3本地接线与准备；新封闭版本/schema区分实际暖机成功与未观测token/EOS，保留旧路径及N1 fresh measured流。固定30新进程/0profile待审包，不同时加采或扩60上限；Gate11继续BLOCKED、Freeze未启动。S/A/B/测量公式不变，无Formal数据失效或历史追认；仅新Pilot版本适用。

7.110（2026-09-30）：原V0新合同审查复用与d25两组新实物完成N1限定Engineering三组可行性PASS；关闭模型准备依赖，不扩张Gate10 G1范围或授统计/科学资格。Gate11只列最小本地准备，无新采集授权；旧报告及UNKNOWN不改，DOCX不纳提交。

7.111（2026-09-30）：用户明确Gate10只通过固定配置下三个G1选定点的一次Engineering检查；OOM/容量/最大长度/batch、完整与统计稳定域未完成，原编号/未执行子项保留后移。Gate11复用原计划完成代表点、有界配对/预算/warmup及Freeze输入草案，阶段适用版本/入口及Pilot数值依据仍待完成。无测量语义/旧判定变更，无Protocol Freeze或Formal数据受影响；不运行测试、服务器、GPU/Nsight/OOM。

7.112（2026-09-30）：按用户批准为未来新采限定Pilot固化G11-LIMITED-PILOT/0.1，最小角色/Pass0/token配对及首批30进程编排完成CPU验证和待审交付。只扩阶段角色适用，不改S/A/B/completion或历史数据；Gate11仍NOT_RUN，数值政策/Freeze未完成，无Formal数据受影响。

7.107（2026-09-30）：按用户批准使内部同步Raw来源身份amendment生效（S0.4/A-B0.5/N1 adapter0.2）；只新增来源证据，不改变W/A/B公式，不修改旧schema/历史资格。allocation只做已知但completion未支持的诊断，opaque例外集中待裁决未实施。复用同一V0 Raw完成P1独立检查；N1仍BLOCKED，Vmarker/V16暂停，无新部署/采集或Formal数据变化。用户DOCX保留在提交之外。

7.106（2026-09-30）：N1 V0真实采集后优先复用同一Raw完成所有独立离线检查，修复局部适配、不重采；停止于已知allocation的completion测量政策及内部Raw同步来源schema要求。仅提出P1/P2未生效amendment，不改冻结schema/registry或W/A/B公式；N1模型支持域BLOCKED、Vmarker/V16暂停，Gate10限定G1范围及Gate7～9 PASS保持。无Formal数据变化，不因分析commit变更笼统要求新V0。

7.103（2026-09-29）：N1模型准备从依赖核对进入最小调用层实现，沿用协议V16及分域合同；Gate10限定G1范围不变，N1模型可行性另记NOT_RUN。旧Gate编号不重排，未修改冻结语义/旧证据，无Formal数据影响；剩余仅为模型端到端生产/消费接线，不以CPU结果授资格。

（按时间顺序。行内出现的 `Gate 6 = FAIL`、`Q0 = NOT_RUN`、`Gate 7 = BLOCKED` 等字样均为该行日期当时的状态，已由 7.0 行改判；各行只保留结论摘要，详细过程见对应 amendment、runbook 与 `docs/v1_4_1/gate6_closeout_v0_1.md`。）

| 清单版本 | 日期 | 调整摘要 | 影响编号 | 冻结协议／Formal 数据影响 |
|---|---|---|---|---|
| 0.1 | 2026-09-10 | 首次建立完整清单；纳入无 GPU 离线路线、自然逐 Token 同步边界与现有 observation 基础 | 全部 | 无 Formal 数据，不产生失效 |
| 0.2 | 2026-09-10 | 权威关系审计：协议修订底稿由 WMPC v1.5 更正为实验协议 v2.0；新增两份 Pre-Pilot 整合候选版 | EP-FND-06～10 | 未改变冻结协议 |
| 0.3 | 2026-09-10 | 基于两份 Word 母版吸收 v1.4.1，完成 40/27 页视觉验收；完整 v7.0/v2.1 成为当前入口 | EP-FND-07～11、EP-ISSUE-05 | 未通过 Gate 1 或 Protocol Freeze |
| 0.4 | 2026-09-10 | 复核发现 v7.0 第一章背景论证不完整，启动 v7.1 修订并简化交付文件名 | EP-FND-09、EP-FND-11、EP-FND-12 | 不改变合同或资格 |
| 0.5 | 2026-09-11 | 完成 v7.1 背景与研究立意补齐、结构/语义校验与全页视觉验收 | EP-FND-12、EP-ISSUE-05 | 不改变合同或资格 |
| 0.6 | 2026-09-11 | 完成 Measurement Contract v0.2，建立 37 条规则到 25 个验证案例的机器映射 | EP-G1-02～09 | Gate 1 内部合同审查 PASS |
| 0.7 | 2026-09-11 | 完成 Q0 独立标准答案设计（23 case、25 特性、`DESIGN_ONLY_PASS`） | EP-G2-01～05、EP-G3-05 | Gate 2 设计审查 PASS |
| 0.8 | 2026-09-11 | 完成 Canonical Raw v0.2 与三份历史 trace 的 Engineering 回归 | EP-G3-05～08、EP-G4-01～05 | Gate 3 PASS |
| 0.9 | 2026-09-11 | 完成 S v0.2：ownership、submission、completion graph、`W(s)`、terminal、validity 与版本化输出 | EP-G4-01～05、EP-G5-01 | 无 |
| 1.0 | 2026-09-11 | Gate 4 复审修正三项语义缺陷：missing correlation 降级、wait-event 漏 producer、外部 invocation 静默删除 | EP-G4-01～05 | 无 |
| 1.1 | 2026-09-11 | Gate 4 二轮复审：`eventSyncId` 唯一映射与 event/context/device 校验、invalid 传播、default-stream 污染；补 9 回归 | EP-G4-01～05、EP-ISSUE-03、EP-ISSUE-06 | 无 |
| 1.2 | 2026-09-11 | Gate 4 三轮复审：统一缺失 correlation 的 fail-closed 传播路径；补 3 回归 | EP-G4-02、EP-G4-05 | 无 |
| 1.3 | 2026-09-12 | 冻结 Gate 5 设计（A/B 双输入联结、窗口发现、B 投影、D/Signature 纯派生） | EP-G5-01～06 | 无 |
| 1.4 | 2026-09-12 | 冻结 A/B 与派生层 v0.2 JSON Schema（守恒字段、null-only、lineage） | EP-G5-01～06 | 无 |
| 1.5 | 2026-09-12 | Gate 5 schema 一审修复：terminal kind/status 的 identity、clock 与 timing nullability，count 收紧 | EP-G5-01、EP-G5-03、EP-G5-05、EP-G5-06 | 无 |
| 1.6 | 2026-09-12 | Gate 5 schema 二审修复：`B_VALID>0` 时 terminal count 与统计分布必须非空 | EP-G5-01、EP-G5-03、EP-G5-05、EP-G5-06 | 无 |
| 1.7 | 2026-09-12 | 完成整数半开区间原语（交、裁剪、相邻/重叠 union、union 长度、原子切分） | EP-G5-02 | 无 |
| 1.8 | 2026-09-12 | 完成 A 墙钟记账：按窗口/API/sync/`W(s)` 原子切分，固定优先级互斥分配，fail-closed 到 unattributed | EP-G5-01、EP-G5-02 | 无 |
| 1.9 | 2026-09-12 | Gate 5 Task 4 一审引入结构化 NVTX API ownership gate（过严规则已在 2.0 修正） | EP-G5-01、EP-G5-02 | 无 |
| 2.0 | 2026-09-12 | 二审澄清 API ownership 与 phase clipping：ownership 只证明同一 invocation，不定义 A 窗口 | EP-G5-01、EP-G5-02 | 无 |
| 2.1 | 2026-09-12 | 集成复审修正窗口发现：非窗口 marker 不创建也不否定 A 三窗口 | EP-G5-01、EP-G5-02 | 无 |
| 2.2 | 2026-09-12 | 收紧 worker API ownership：采用前重解析 NVTX text 并要求与缓存 identity 完整一致 | EP-G5-01、EP-G5-02 | 无 |
| 2.3 | 2026-09-13 | 完成 B 单同步 provenance：仅 `B_VALID` 按区间 union 计算，其他状态 null-only，不提供跨同步 total | EP-G5-03 | 无 |
| 2.4 | 2026-09-13 | 补两条 B 回归：重叠活动按 union、`COMPLETION_BOUNDARY` terminal timing 为 null | EP-G5-03 | 无 |
| 2.5 | 2026-09-13 | 完成 A/B bundle 与 `analyze-ab` CLI：严格联结、逐条 schema 校验、确定性 gzip、拒绝覆盖、边界审计 | EP-G5-06、EP-G3-08 | 无 |
| 2.6 | 2026-09-13 | A/B loader 在 schema 允许未来资格值时仍执行当前 Engineering 资格策略；外部 S lineage 核对 registry SHA | EP-G5-06、EP-G3-08 | 该策略不是对 Formal bundle 的永久否定 |
| 2.7 | 2026-09-13 | 完成 `derive-exposure`：D 与 Exposure Signature 纯派生，边界禁止回读 Canonical/S 或 Raw/S 时间字段 | EP-G5-04～06、EP-G3-08 | 无 |
| 2.8 | 2026-09-13 | Gate 5 Task 8 历史 trace 离线工程验证：S 446 invalid → B 446 `B_INVALID`，无合格 A 窗口 | EP-G5-06、EP-ISSUE-02、EP-ISSUE-03 | 历史数据仍为 ambiguous Engineering 证据 |
| 2.9 | 2026-09-14 | 分支复审最终修复：S/wait-set/frontier/terminal 一致性、跨 invocation 重叠 fail closed、Derived 精确符号白名单 | EP-G5-01、EP-G5-03、EP-G5-05、EP-G5-06、EP-G3-08 | 未产生 Formal 数据 |
| 3.0 | 2026-09-14 | 独立再复审通过（补 completion boundary 时钟域校验）；Gate 5 判为 `PASS`，优先级切换至 Gate 6 GPU 前工作 | EP-G5-03、EP-G5-06、EP-G6-01、EP-G6-02 | Gate 5 PASS |
| 3.1 | 2026-09-14 | 冻结 Gate 6 GPU 前实施计划：23 个 oracle case → native CUDA / seed+fault / 纯合成三类 | EP-G6-01、EP-G6-02 | Gate 6 仍 `BLOCKED` |
| 3.2 | 2026-09-14 | 完成 Q0 执行合同第一步：case 严格一一对应、稳定 label 不可改写、策略字段冲突 fail closed | EP-G6-01 | 无 |
| 3.3 | 2026-09-14 | 完成受控 Q0 CUDA 微程序（21 native seed、结构化 NVTX、可无 GPU 编译并核对 seed 集合） | EP-G6-01、EP-ISSUE-07 | 只证明可构建，不证明 GPU 行为 |
| 3.4 | 2026-09-14 | 完成 Windows/Linux 结构化 `nsys` argv dry-run、23 份 source manifest 与不可覆盖 run manifest | EP-G6-02 | 不产生 `.nsys-rep` |
| 3.5 | 2026-09-14 | 完成 23 案例合成 S/A/B + 独立 evaluator 对照；修正 graph mapping unsupported 时 S 保留未证明 wait-set 的缺口 | EP-G4-01～05、EP-G6-02 | 仅 `SYNTHETIC_ONLY` |
| 3.6 | 2026-09-14 | GPU 前集成验收：编译/list、Windows dry-run、合成对照、静态边界与全仓非 GPU 回归 | EP-G6-02A、EP-G6-03 | GPU 前 PASS ≠ Gate 6 PASS |
| 3.7 | 2026-09-14 | 真实执行复审新增 `EP-G6-02B`：改用 CUDA Profiler API 控制 capture 并冻结显式单 GPU 选择 | EP-G6-02B、EP-G6-03 | 修正“可直接真实采集”的过早推断 |
| 3.8 | 2026-09-14 | 完成单 case executor 与不可覆盖 receipt（工具/source manifest 哈希、环境身份、命令日志、Raw 哈希） | EP-G6-02B | 仅新增采集能力 |
| 3.9 | 2026-09-14 | 完成三种受控 Canonical 故障副本（移除唯一 activity correlation／dropped records／graph node mapping） | EP-G6-02B | Raw 与源 Canonical 保持不可变 |
| 4.0 | 2026-09-14 | 完成真实 observed/evaluator：标签联结 + 本次真实区间重算，缺区间/映射一律 fail closed | EP-G6-02B | 单 case 仅 `REAL_CASE_ONLY` |
| 4.1 | 2026-09-14 | 完成本地真实 Q0 执行缺口：唯一聚合器强制 21 real + 2 synthetic、单 run/单环境，补齐 CLI 与双平台手册 | EP-G6-02B、EP-G6-03～05 | 本地准备 ≠ 真实 Q0 |
| 4.2 | 2026-09-15 | 补充服务器部署与回传流程（Git bundle clone、独立 venv、先单例后批量、记录 commit/dirty state） | EP-G6-03 | 无 |
| 4.3 | 2026-09-15 | 基于 r2 修复 Windows 适配：Nsight `2026.2.1.210/3.25.0`、可选表规范化、有符号 trace-relative 时间、UUID、诊断输出 | EP-G3-09、EP-G6-02C、EP-ISSUE-08 | r2 不升级资格 |
| 4.4 | 2026-09-15 | 基于 r3 修正 observation scope 与下游空映射；r3 本地只读重放 `REAL_CASE_PASS` | EP-G3-10、EP-G6-02D、EP-ISSUE-09 | r3 不升级资格 |
| 4.5 | 2026-09-15 | 基于 r4 EMPTY 修正 lazy-export 零行 KERNEL 表与真实 `VALID_EMPTY` evaluator；导出统一 `--lazy=false` | EP-G6-02E、EP-ISSUE-10 | r4 不升级资格 |
| 4.6 | 2026-09-16 | 基于 r5 修复三个同源多线程 seed 的重复 target request（coordinator 唯一 request/decode） | EP-G6-02F、EP-ISSUE-11 | r5 不升级资格 |
| 4.7 | 2026-09-16 | r6 确认修复并发现 PTDS `cudaStreamQuery` 轮询产生 31 条未映射同步 → 改一次 stream-ordered host callback | EP-G6-02G、EP-ISSUE-12 | r6 不升级资格 |
| 4.8 | 2026-09-16 | r7 修正 resolver 的目标唯一性判定：只对完整 target identity 计数 | EP-G6-02H、EP-ISSUE-13 | r7 不升级资格 |
| 4.9 | 2026-09-16 | r8 为 Graph case 增加一次 `--cuda-graph-trace=node`，其余 native case 采集参数不变 | EP-G6-02I、EP-ISSUE-14 | r8 不升级资格 |
| 5.0 | 2026-09-16 | r9 evaluator 对 `wait_set_activity_labels` 改用无序、无重复精确成员比较 | EP-G6-02J、EP-ISSUE-15 | r9 不升级资格 |
| 5.1 | 2026-09-16 | r10 无 device overlap → 仅 KERNEL-MEMOP case 预分配 512 MiB 并把 kernel 改为 10 ms，新增单 case diagnostic gate | EP-G6-02K、EP-ISSUE-16 | r10 不升级资格 |
| 5.2 | 2026-09-16 | 512 MiB diagnostic 仍串行 → 改为 memcpy-first 提交顺序并以静态回归锁定 | EP-G6-02L、EP-ISSUE-16 | 同上 |
| 5.3 | 2026-09-16 | 证明同线程 `cudaLaunchKernel` 被长 H2D 阻塞 → 改为 coordinator/worker 双 Host 路径并发提交 | EP-G6-02M、EP-ISSUE-16 | 同上 |
| 5.4 | 2026-09-16 | concurrent-host diagnostic 缺 worker invocation marker → worker launch 前增加立即结束的 `WORKER_KERNEL_MEMOP` | EP-G6-02N、EP-ISSUE-16 | 同上 |
| 5.5 | 2026-09-17 | 证明仅延长 worker marker 无效 → 冻结 activity-specific marker ownership 修正规格，暂停 GPU 重跑 | EP-G6-02O、EP-ISSUE-17 | 未修改 S 语义 |
| 5.6 | 2026-09-17 | 按规格测试先行实现 activity-specific marker ownership；S 定向 `77 passed`，全仓 `661 passed, 2 failed` | EP-G6-02O、EP-ISSUE-17 | 真实 GPU 单例尚未复验 |
| 5.7 | 2026-09-17 | 真实 ownership 单例确认 S 修复成功但 device overlap 仍为 0 → 新增完全隔离的 WDDM Engineering diagnostic；全仓 `671 passed` | EP-G6-02P、EP-ISSUE-16 | 无 |
| 5.8 | 2026-09-17 | WDDM diag-02 采集成功但 HAGS 未确认、packet 无 correlationId → 新增 64 MiB H2D/10 ms diagnostic；全仓 `678 passed` | EP-G6-02Q、EP-ISSUE-16 | 仅 Engineering 假设检验能力 |
| 5.9 | 2026-09-17 | 64 MiB/10 ms 仍 overlap=0 → 按预定判据停止 1 ms 路线；新增 device capability 探针；全仓 `681 passed` | EP-G6-02R、EP-G6-04A、EP-ISSUE-16 | 无 |
| 6.0 | 2026-09-17 | 服务器 capability 复核：`async_engine_count=5`、`device_overlap=1`、`concurrent_kernels=1`（只证明设备声明能力） | EP-G6-04A、EP-ISSUE-16 | 不解释此前 overlap=0 |
| 6.1 | 2026-09-17 | 实现严格隔离的 64 MiB D2H/10 ms diagnostic（专用 flag + run identity 双条件） | EP-G6-02S、EP-G6-04B、EP-ISSUE-16 | 默认 Q0 路径不变 |
| 6.2 | 2026-09-17 | 收录 D2H 真实证据：仍 overlap=0，`Q0-KERNEL-MEMOP-001` 记为 platform construction blocked，按判据 STOP | EP-G6-04B、EP-G6-05、EP-G6-06、EP-ISSUE-16 | Gate 6 仍 `FAIL`、Q0 `NOT_RUN` |
| 6.3 | 2026-09-17 | 完成 `EP-G6-06` 策略审查：synthetic 仅作 regression strengthening、批准候选平台 admission 设计、冻结 admission checklist、scope limitation 不批准 | EP-G6-06～08 | 纯设计，未运行实验 |
| 6.4 | 2026-09-17 | 批准 Gate 7 非 GPU 项与 Gate 6 等待期并行（该前提已被 6.7/7.0 取代） | EP-G7-01～06 | Gate 7 保持 `BLOCKED` |
| 6.5 | 2026-09-17 | `EP-G6-07` 首轮候选平台盘点：主线切到 Candidate Platform qualification，CP-01 A3 修正，A7 保持 `UNKNOWN` | EP-G6-07、EP-ISSUE-04、EP-ISSUE-16 | Gate 7/8 暂停推进 |
| 6.6 | 2026-09-17 | CP-03 静态 qualification 收敛（A1、A3～A9 = `PASS`；A2 pending、A7 unknown；仍为 `NEEDS_INFORMATION`） | EP-G6-07 | 未运行任何 case/workload probe |
| 6.7 | 2026-09-18 | formal-shape 配对 diagnostic 证明 warm-up 可恢复 overlap → 建立 canonical baseline `codex/gate6-canonical-baseline` 与 construction amendment；`EP-G6-07` 暂停 | EP-G6-05、EP-G6-07、EP-G6-09、EP-ISSUE-16 | Gate 6 仍 `FAIL`、Q0 `NOT_RUN` |
| 6.8 | 2026-09-19 | construction amendment implementation：execution schema `0.2.1`、23/23 case 显式 `measurement_initialization`（1 warm-up + 22 `NONE`）；targeted `70 passed`、Q0 offline `199 passed` | EP-G6-05、EP-G6-07、EP-G6-09 | server validation `NOT_STARTED` |
| 6.9 | 2026-09-19 | `final-01` 收口与 4 例 semantic FAIL root triage（新增 `EP-G6-10`）：Phase-Spill / Missing-Corr / External / Multithread-Ordered / Overlapping-Host-Sync | EP-G6-05、EP-G6-07、EP-G6-09、EP-G6-10 | Gate 6 仍 `FAIL`、Q0 `NOT_RUN` |
| 7.0 | 2026-09-20 | **Gate 6/Q0 正式 PASS 并收口**（新增 `EP-G6-11` 与 `gate6_closeout_v0_1.md`）；Gate 7 压缩为 `EP-G7-08`～`EP-G7-11` 并作出平台范围显式决定；清理本地可重建垃圾 | EP-G6-05、EP-G6-11、EP-G7-08～11、EP-ISSUE-01、EP-ISSUE-03、EP-ISSUE-16 | Gate 6/Q0 改判 `PASS`（依据既有唯一 gate report，未新增采集）；Gate 7 由 `BLOCKED` 改为 `NOT_RUN` |
| 7.1 | 2026-09-20 | 最后一次收尾：本清单重构为“交接入口 + 当前快照 + Gate 摘要 + 压缩历史”；清除过时 live 状态文字；为旧 Gate 6/5 计划与规格加历史横幅；为 Gate 7 四步补 `Dependency`；补 Gate 6 论文级分类总结 | EP-G6-11、EP-G7-08～11、EP-ISSUE-03 | 不改变任何 Gate verdict、Measurement Contract、oracle、schema 或数据资格 |
| 7.2 | 2026-09-21 | 完成 `EP-G7-08`：统一首/后续 Token 的 Host-readable completion，首/后续 EOS 均复用 Host 值，结果时间截止于最后 Token-ready 且 phase ranges 在校验/cleanup 前关闭；加入 G1/N1 互斥机器身份、结构化 NVTX 与 fail-closed validation | EP-G7-08、EP-ISSUE-01 | Gate 7 保持 `NOT_RUN`；严格跨 pass phase parity 留给 `EP-G7-09`；不改变 Measurement Contract、`exposedpath_v141`、Gate 6 证据或数据资格 |
| 7.3 | 2026-09-21 | 完成 `EP-G7-09`：冻结 Pass0/Pass1 parity identity（workload／GPU／execution strategy／phase boundary／environment snapshot／attempt plan 六组）并把 `cross_pass_parity.json` 升为 `exposedpath-v3-cross-pass-2`；attempt/exclusion/retry/data-role 机器可读；缺失身份、缺失/重复 repeat index 与有意差异一律 fail closed | EP-G7-09、EP-G7-03、EP-G7-04 | Gate 7 保持 `NOT_RUN`；不改变 Measurement Contract、`exposedpath_v141`、Gate 6 证据、数据资格或 Gate 7 PASS 判据 |
| 7.4 | 2026-09-21 | 完成 `EP-G7-10`：新增 `exposedpath/platform_adapter.py` 作为唯一 Python 侧平台边界（结构化 argv、无 shell、工具解析与 fail closed），runner/manifest 的 `nvidia-smi`／`git` 调用全部改经 adapter（无 schema/字段语义变化）；两项既有 smoke 失败定位为测试非封闭（裸 `powershell`＋依赖环境 `PATH` 解析 `python`）并修复，新增 PATH 独立性与 AST 结构回归 | EP-G7-10、EP-G7-05、EP-G7-06、EP-ISSUE-03 | Gate 7 保持 `NOT_RUN`（`EP-G7-11` 真实 GPU smoke 未执行）；不改变 Measurement Contract、`exposedpath_v141`、Gate 6 证据、数据资格或 Gate 7 PASS 判据 |
| 7.5 | 2026-09-22 | 补记 `7e67219` 的 Python <3.12 f-string portability 修复；在 EP-G7-11 smoke 前按 tests first 修复 physical/logical GPU index 混用：manifest 与 server smoke 共享纯 resolver，torch 查询使用 logical index，manifest/telemetry 保留 physical identity，runner remapping 零修改 | EP-G7-11、EP-ISSUE-18～20 | Gate 7 保持 `NOT_RUN`（未运行 GPU smoke）；不改变 Measurement Contract、S/A/B/D、Q0 oracle/evaluator、Gate 6 evidence、schema 或数据资格 |
| 7.6 | 2026-09-23 | EP-G7-11 fresh attempt 在 Pass0 后、Pass1/Nsight 启动边界遭 BugCheck 0x133 中断（根因未证实）；Trace Minimization / Acceptance Scope Audit 确认 Gate 7 为 integration smoke、完整真实 workload 科学链首属 Gate 8 EP-G8-02；同提交补记 bounded launcher repair：Engineering role、静态/跨 pass/telemetry fail-close、非零 BLOCKED、最小 CUDA+NVTX profile、独立 SQLite 后处理与观察身份留痕 | EP-G7-11、EP-G8-02 | Gate 7 仍 `NOT_RUN`，Gate 8 不启动，GPU smoke 未重新授权；旧/新 observation profile evidence 不可拼接；不改变 Measurement Contract、S/A/B/D、Q0 oracle/evaluator、Gate 6 冻结证据或 Formal 数据 |
| 7.7 | 2026-09-23 | 服务器报告 `799fb8d` fresh smoke 的最小 Nsight collection 成功、无本次 BugCheck，但即时 SQLite export 挂起且原 machine report 正确 `BLOCKED_BY_NSYS`；同 hash REP 副本离线 export/integrity/analyzer 通过，精确挂起根因仍未证明。测试先行实现有界 REP readiness、最多两次 180 秒独立 SQLite export、PID 定向结束、哈希/必需表字段/完整性校验、无覆盖 promotion、Analyzer 前校验、历史 machine report 防覆写与 attempt provenance；原 attempt 不追认 | EP-G7-11 | Gate 7 仍 `NOT_RUN`，Gate 8 不启动，新 GPU smoke 未授权；仅改变 Engineering 后处理可靠性与 fail-close，不改变 observation profile、Measurement Contract、S/A/B/D、Q0、Gate 6 evidence 或 Formal 数据 |
| 7.8 | 2026-09-23 | 后处理 Windows path/argv 二审新增真实 `Popen` + fake exporter 回归：含空格 exe/REP/SQLite 路径逐项传递，stdout/stderr 可追溯；生产实现无需修改。等待独立 bundle 部署、服务器静态验证及已有 REP 的新目录离线后处理验证，不运行 GPU smoke | EP-G7-11 | Gate 7 仍 `NOT_RUN`，Gate 8 不启动；原 `799fb8d` attempt 继续 `BLOCKED_BY_NSYS`，不改变 Measurement Contract、科学 analyzer、Q0 或 Gate 6 evidence |
| 7.9 | 2026-09-24 | 已部署 `5a37eb0` 的服务器 static validation 暴露 Windows venv launcher/fake exporter PID 分离；本地 venv 红测复现后，仅修复测试 fixture 使用直接 base interpreter，保留 PID 等值断言并检查 retry 前真实进程退出；生产 termination logic 不变 | EP-G7-11 | Engineering/static-validation 修复；Gate 7 仍 `NOT_RUN`，Gate 8 不启动，新 GPU smoke 未授权；旧 attempt 不追认 |
| 7.10 | 2026-09-24 | 接收用户回传的 `ecac542` 目标服务器静态验证：1/19/97 项定向通过，全量 981 passed、1 skipped（原因未知），全部命令 exit 0；fixture 阻塞解除，准备独立 REP 副本离线验证方案，未执行 | EP-G7-11 | 仅 Engineering 回执与文档更新；无新提交/部署需求，Gate 7 仍 NOT_RUN，Gate 8 不启动，旧 attempt 不追认 |
| 7.11 | 2026-09-24 | 接收用户回传的 ecac542 真实离线单次 export/analyzer 成功路径及 v2 清单补救结果；明确真实 timeout/kill/retry 未验证、legacy B 2/6 非 v1.4.1 语义验收；准备 fresh smoke 草案 | EP-G7-11 | 未取得完整服务器产物；仅文档更新，执行基线仍 ecac542；Gate7 NOT_RUN、Gate8 不启动，fresh smoke 未授权 |
| 7.12 | 2026-09-24 | 直接审计完整本地诊断包并复核哈希；执行真实 STEP6 validation block 复现 sync_coverage missing；发现 legacy 摘要/明细覆盖不同且 valid 映射未定义，依用户要求暂停实现、先明确合同 | EP-G7-11 | 仅文档更新，无新提交；不改变冻结语义或判据，fresh smoke 暂停，Gate7 NOT_RUN、Gate8 不启动 |
| 7.13 | 2026-09-24 | 明确 coverage 仅为证据缺口诊断；核对 physical UID、窗口缺失、legacy 与冻结 validity 不等价、union/跨 phase 口径及 null 约束；收紧全明细求和建议，集中待决验收映射与输入合同 | EP-G7-11 | 无运行代码/schema 改动；完整 request A 已实现但真实 workload 全链验收仍属 Gate8；Gate7 NOT_RUN、fresh smoke 暂停 |
| 7.14 | 2026-09-24 | 用户批准并版本化 gate7-legacy-analyzer/1；tests first 修复 launcher/validation consumer，严格 legacy-only 结构/身份/diagnostics gate，窗口 coverage 显式 unknown，拒绝历史 resume | EP-G7-11 | Gate7 工程验收规则显式修订、仅对后续新 attempt 有效；不修改冻结测量语义或旧 evidence；Gate7 NOT_RUN，GPU/Nsight 未授权，Gate8 不启动 |
| 7.15 | 2026-09-24 | 直接审计服务器 dced364 的33/130/1014测试及环境/23文件模型快照；确认 skip 和 revision unknown 的 Engineering 限制；旧实际 JSON 本地结构兼容、跨 commit 拒绝；只余 cl/marker/mask 最小补证 | EP-G7-11 | 仅文档更新、执行基线不变，无重跑测试/模型/Nsight；旧 attempt 不追认，Gate7 NOT_RUN，fresh smoke 未授权、Gate8不启动 |
| 7.16 | 2026-09-24 | fresh dced364身份链BLOCKED：修复Git adapter参数冲突、preflight GPU字段传递、prompt/manifest哈希混淆；增加模型加载前身份gate及实际producer回归 | EP-G7-11 | 工程修复，不放宽验收、不改冻结科学语义；旧attempt保持BLOCKED，Gate7 NOT_RUN；新GPU/Nsight未授权，Gate8不启动 |
| 7.17 | 2026-09-24 | 直接审计8d64f75服务器adapter/185定向/静态回执；关联已有环境、模型及补齐的compiler/marker快照；准备固定版本fresh草案 | EP-G7-11 | 仅文档、不提交/部署、不重跑测试；不将旧全量算作新版本验证；Gate7 NOT_RUN、旧attempt BLOCKED、新GPU/Nsight待授权、Gate8不启动 |
| 7.18 | 2026-09-24 | fresh8d64f75完整证据只读审计通过，新增gate7_closeout_v0_1；本次1040/1全量、两pass、身份/边界/后处理/legacy验收闭环；关闭EP-G7-11，Gate7 PASS | EP-G7-11 | 仅Engineering integration；保留原始diagnostics/unknown与legacy限制，不改冻结科学语义、不追认旧attempt；Gate8 NOT_RUN待规划、未启动 |
| 7.19 | 2026-09-24 | main统一入口；保全历史事故修改/审查笔记，移除五个worktree、核实冗余bundle/DOCX/缓存；单根固定checkout路径规范与GitHub同步 | 目录治理 | 根CPU-only1036 passed/5 skipped，原本机CUDA13编译失败另记；243证据文件不变，无代码语义修改，无服务器/GPU/Nsight执行；Gate7 PASS、Gate8 NOT_RUN |
| 7.20 | 2026-09-25 | Gate8实际producer/consumer审计与版本化最小计划；历史SQLite只读转换揭示identity/窗口/trace-device/quality/coverage缺口；记录用户回传服务器目录完成但未读取原receipt | EP-G8-01～04规划 | 无业务代码/冻结合同改变；无新GPU/Nsight、无Gate8验收证据；Gate7 PASS限制不变，Gate8 NOT_RUN，四实验任务未勾选 |
| 7.21 | 2026-09-25 | 合同收敛为D1共同completion锚点与D2 coverage统计细则；协议确认B-valid分母=支持sync；设备映射/多repeat来源给出确定工程设计，零丢失肯定证据仍为技术阻塞 | EP-G8-01～04规划 | 仅建议amendment、尚未批准/实施；未改冻结合同或Q0，不升级旧证据；Gate7 PASS、Gate8 NOT_RUN |
| 7.22 | 2026-09-25 | 用户批准D1/D2设计；新增两份独立amendment/schema、手算预期、版本化Nsight完整性调查；正常提交推送设计文档，不部署服务器 | EP-G8-01～04设计 | 仅schema/文档，无生产修改；shape检查不等于语义/真实验证；新资格待验证、零丢失仍UNKNOWN；Gate7 PASS、Gate8 NOT_RUN |
| 7.23 | 2026-09-25 | 授权本地tests-first第一批：多请求/device身份、共同point/projection、S/A ownership接口、D2 coverage、UNKNOWN完整性门；56项新回归及CPU全量1092 passed/5 skipped | EP-G8-01～04实现前置 | signed-time A/B及文件/全链编排仍待收口；无服务器/GPU/Nsight、无新Q0资格；Gate7 PASS、Gate8 NOT_RUN |
| 7.24 | 2026-09-25 | 批准时间表示amendment：A/B、Derived 0.3显式signed-int64/uint64；实际producer/receipt→Canonical/projection→S/A/B/coverage/D文件入口，CPU全量1116 passed/5 skipped | EP-G8-01～04本地实现前置 | 旧0.2路径/冻结公式不变；新Q0未取得，真实完整性仍UNKNOWN，服务器部署/采集未授权；Gate7 PASS、Gate8 NOT_RUN |
| 7.25 | 2026-09-25 | 只读核验真实SQLite/collector与官方2026.2；选择B一次安装取证并设停止点；新版Q0影响矩阵、独立oracle与真实编排缺口计划 | EP-G8-01～04资格前置规划 | 无代码/collector/冻结语义变化，无实验；历史PASS不继承，完整性UNKNOWN，Gate8 NOT_RUN |
| 7.26 | 2026-09-25 | 安装资料回传直接审查与四文件hash复核；有界调查收口，英文厂商询证DRAFT_NOT_SENT及支持/不支持/无答复路线 | EP-G8-01～04资格前置调查 | 未找到充分来源而非断言工具不支持；无外发/服务器搜索/实验/代码变化；UNKNOWN继续阻塞，Gate7 PASS、Gate8 NOT_RUN |
| 7.27 | 2026-09-25 | 用户批准路线A与目标request/必要依赖质量amendment；保留编号并合并/缩减/后移任务；新增显式scope文件入口和局部记账诊断，三例实际文件链及CPU回归 | EP-G8～14计划/本地接口 | 取消统一全capture认证前置，UNKNOWN不改零；机制发布仍受限，旧S/A/B/Q0及历史证据不变；无服务器采集，新资格未授予；Gate7 PASS、Gate8 NOT_RUN |
| 7.28 | 2026-09-26 | 窄controlled producer/native源、CLI及独立Raw/file-backed proof接通；29定向、1161/5 CPU；固定argv、精确sync集合及前窗依赖负例；服务器静态/采集分段草案 | EP-G8-01/02本地必要桥接 | native未实机编译运行；同流跨request epoch仍未决，GetLastError未分类，不改S/registry/Q0；受控诊断不授新资格、模型尚未就绪；Gate7 PASS、Gate8 NOT_RUN |
| 7.29 | 2026-09-26 | 直接审查服务器24f58f8静态1165/1回执及native UUID API编译失败；tests-first最小CUDA12.4兼容修复；DevShell已验证模块入口同步文档；基于24f58f8恢复包 | EP-G8-01/02兼容修复 | 不改GPU映射、W(s)/A/B、Q0或旧证据；新native编译待服务器，未GPU/Nsight；epoch/API支持限制保留；Gate7 PASS、Gate8 NOT_RUN |
| 7.30 | 2026-09-26 | 直接审计7f61102目标机30项静态/native构建五原件，DLL哈希一致、源码CRLF身份可解释；窄受控采集静态前置就绪 | EP-G8-01/02执行前审查 | 仅文档，不更新服务器部署；GPU/Nsight/新Q0未执行，不授模型资格；Gate7 PASS、Gate8 NOT_RUN |
| 7.31 | 2026-09-26 | 直接审计窄受控capture17原件、receipt/REP/hash/argv/身份，准备固定run的bounded export+audit单段脚本 | EP-G8-01/02受控诊断 | receipt成功不是trace/S/A/B资格，后处理待执行；原件不变、无重采/模型；Gate7 PASS、Gate8 NOT_RUN |
| 7.32 | 2026-09-26 | 直接审计29文件离线原件，单次export PASS、Raw因四处缺GetLastError正确BLOCKED；tests-first新0.2直接检查launch返回码、版本隔离与实文件回归 | EP-G8-01/02受控可观察性对齐 | 仅本地实现，不改S/A/B/registry/observation profile/旧证据；新目标编译与采集未执行，不授新Q0或A科学资格；Gate7 PASS、Gate8 NOT_RUN |
| 7.33 | 2026-09-26 | 直接审计07625b7目标机37项定向/静态/native构建五原件，DLL哈希及源码CRLF表示一致；核验未变capture草案固定身份 | EP-G8-01/02执行前审查 | 仅文档审计，无本窗口服务器/GPU/Nsight执行；源码本体未回传，不冒称读取；新采集待授权、旧attempt BLOCKED；Gate7 PASS、Gate8 NOT_RUN |
| 7.34 | 2026-09-26 | 0.2新capture17原件/8封存引用、commit/构造/19argv/token/GPU及source/DLL身份直接审计；新run绑定bounded离线脚本及17文件只读preflight | EP-G8-01/02受控诊断 | 仅回执链通过，REP尚未解析，无本窗口export/GPU；旧attempt不追认，后处理待审；Gate7 PASS、Gate8 NOT_RUN |
| 7.35 | 2026-09-26 | 29离线原件审计；明确lazy metadata驱动MEMSET适配，固定源码/版本诊断scope分类；本地实文件前瞻六A/四目标B与独立预期，五scope外INVALID使Derived仍阻断 | EP-G8-01/02分析adapter | 原capture/失败report不改，无重采/export/编译；NOT_ASSESSED不授新Q0，Derived输入选择域未改变；Gate7 PASS、Gate8 NOT_RUN |
| 7.36 | 2026-09-26 | c827b61服务器离线73原件核验，独立Raw算术六A/四B集合与时长匹配；发现并tests-first修复S映射取键造成B phase误写；129定向、1204/5 CPU、旧0.2/0.3读兼容及真实输入新派生核验 | EP-G8-01/02字段对齐 | 无新服务器采集/export，旧产物不改/不追认；不改公式/S/Q0/Derived资格域；UNKNOWN/NOT_ASSESSED、五范围外INVALID保留；Gate7 PASS，新Q0/Gate8 NOT_RUN |
| 7.37 | 2026-09-26 | f5edc64服务器73原件/72清单审计，四phase修复且其余A/S/B不变；129目标机定向原始日志核验，字段修复关闭；收敛资格/模型最小准备及epoch独立预期 | EP-G8-01/02审计与计划 | 仅文档，无业务改动/重复实验；不追认历史错误B，不颁新Q0；Derived门保留，epoch仅待裁决提案；Gate7 PASS、Gate8 NOT_RUN |
| 7.38 | 2026-09-26 | 共享stream裁决稿0.2：纠正7.37截断W提案，推荐保留物理前缀/原owner/B进度的closed-prior准入；列drain实证、五类独立预期、现runner绑定缺口及Q0最小影响 | EP-G8-01/02语义待决 | 仅文档设计，未批准/实施ownership变化；冻结合同/历史数据/资格不变，无新测试或服务器执行；Gate7 PASS，新Q0/Gate8 NOT_RUN |
| 7.39 | 2026-09-27 | 用户批准后新增closed-prior0.1及S0.3/A-B0.4：观察原drain、Raw physical scope绑定、历史owner/lifetime、全W/B进度与A裁窗、文件链/版本/失败隔离；tests-first及只读review | EP-G8-01/02本地窄域实现 | 仅Engineering确定性验证，旧schema/Q0/证据不改、不自动授新资格；真实torch setup/warmup/lifetime来源仍缺，all-inventory限制非全capture要求；Derived拒绝新版本、服务器不更新；Gate7 PASS，新Q0/Gate8 NOT_RUN |
| 7.40 | 2026-09-27 | 真实历史eager Raw/第一方源码核查；登记drain别名对齐，实际model setup/warmup/stage身份与Canonical诊断文件链；严格执行合同及失败状态回归 | EP-G8-01/02本地source接线 | 仅Host-call关联，不授worker/default/lifetime或S准入；必要依赖closure仍待来源闭合，不修改W/A/B/Derived门或旧证据；服务器不部署/采集；Gate7 PASS，新Q0/Gate8 NOT_RUN |
| 7.41 | 2026-09-27 | 精确Torch/Transformers源码链及worker非join边界；一次限定10文件安装快照工具、tests-first/只读review与服务器只读交接准备 | EP-G8-01/02来源补证准备 | 不是生产descriptor或资格，不改冻结语义/准入/历史，UNKNOWN保留；无服务器操作/部署/采集；Gate7 PASS，新Q0/Gate8 NOT_RUN |
| 7.42 | 2026-09-27 | 安装快照解压原件14/9清单及目标源码实审；关闭一次补证，固定条件性源码引用和task/attempt本地接口最小顺序 | EP-G8-01/02来源证据审计 | ZIP/DLL本体未到，不冒称本地复算；源码hash不授default/worker/lifetime资格，无业务/schema/实验变化；Gate7 PASS，新Q0/Gate8 NOT_RUN |
| 7.43 | 2026-09-27 | 显式加载attempt/task/native-TID观察与producer0.4真实文件接口；CPU线程/失败重试/取消/封存及跨run反例；不改变原加载等待策略 | EP-G8-01/02本地来源观察 | 仅HOST_JOB_ONLY诊断，不接S准入、不改MC/S/A/B/Derived或旧Q0证据；不部署/采集；Gate7 PASS，新Q0/Gate8 NOT_RUN |
| 7.44 | 2026-09-27 | 必要调用点/mode/lifetime/correlation有限核查；旧Raw白名单复核、独立条件性正反例、一次两DLL静态调用来源候选与停止点 | EP-G8-01/02来源可行性收口 | 仅文档，不改生产/合同/证据；不将条件性等价授为资格；服务器操作待授权，Gate7 PASS，新Q0/Gate8 NOT_RUN |
| 7.45 | 2026-09-27 | 限定PE原件9项/10文件实审，关闭静态路线；提出带独立token预期的Engineering来源观察和明确CPU sampling/ctxsw代价的backtrace profile供审 | EP-G8-01/02来源可行性 | 仅文档，无生产/profile/证据修改；无本轮采集/新Q0资格，Gate7 PASS，新Q0/Gate8 NOT_RUN |
| 7.46 | 2026-09-27 | 微小来源fixture plan/result0.1、task0.2与真实producer文件链；22新增/88定向/1345+5 CPU；重哈希身份/partial/失败记录反例与只读review | EP-G8-01/02本地Engineering准备 | 无Qwen/服务器/GPU/Nsight执行，不改W/A/B/Derived/Q0与历史证据；单次额外profile风险尚未授权，Gate7 PASS、新Q0/Gate8 NOT_RUN |
| 7.47 | 2026-09-27 | 必要性重审：module/RVA非普遍前置，暂停source profile及风险审批请求；转已有目标sync的关键缺口/A影响与低风险路径判定 | EP-G8-01/02执行优先级调整 | 仅文档，已备代码/包保留未授权备用；不改合同、准入、历史资格或Formal数据，无服务器操作；Gate7 PASS、新Q0/Gate8 NOT_RUN |
| 7.48 | 2026-09-27 | 四token sync/两drain及先行候选只读逐行核验，区分新版整窗边界缺口和default/owner闭包缺口，形成紧凑差距表及真实模型支持域下一步 | EP-G8-01/02有界实证审查 | 原SQLite hash不变；不把已观察完成当完整W/零等待，不改合同/实现/资格，无GPU/Nsight；Gate7 PASS、新Q0/Gate8 NOT_RUN |
| 7.49 | 2026-09-27 | producer0.4到目标scope窄支持域只读方案；工程接线、默认流/历史owner新准入与Q0复用明确分离 | EP-G8-01/02设计收口 | 仅方案，未批准新准入；mode UNKNOWN仍拒绝，不改合同/代码/历史证据，无新测试/部署/采集；Gate7 PASS、新Q0/Gate8 NOT_RUN |
| 7.50 | 2026-09-27 | target-scope admission具体未生效草案：逐调用mode/epoch证据、同族范围、原owner、拒绝及独立预期 | EP-G8-01/02批准前提案 | 技术来源未解决不猜测；未改生产schema/代码/公式，无采集；Gate7 PASS、新Q0/Gate8 NOT_RUN |
| 7.51 | 2026-09-27 | 两条低风险mode/epoch证据路径有界裁决，均未闭合；暂停抽象准入审批和同类搜索 | EP-G8-01/02技术停止点 | 受控正确性不代替自然模型claim，无代码/合同/采集；Gate7 PASS、新Q0/Gate8 NOT_RUN |
| 7.52 | 2026-09-27 | 最后比较新增adapter与所有兼容世界A等价准入；均未形成可执行方案，关闭替代调查 | EP-G8-01/02研究决策材料 | 不批准新语义/collector，不降低门槛，不再请求抽象批准；Gate7 PASS、新Q0/Gate8 NOT_RUN |
| 7.53 | 2026-09-27 | 单一自有collector替换Nsight的一页转向评估；受控原型条件性GO、真实Qwen当前NO-GO，备选显式流需claim收缩 | EP-G8-01/02研究资源决策草案 | 未授权实现/collector更换/实验，原合同与证据不变；Gate7 PASS、新Q0/Gate8 NOT_RUN |
| 7.54 | 2026-09-27 | 纠正setup线程与request线程混淆，暂停collector转向；形成drain前缀证书/严格后缀/A与历史B分离的窄范围草案，精简重复测试与hash | EP-G8-01/02批准前合同设计 | 正式MC/S/A-B未改、草案未生效；不追认旧证据，无代码/服务器/采集；Gate7 PASS、新Q0/Gate8 NOT_RUN |
| 7.55 | 2026-09-27 | 用户批准A优先范围；版本化前缀证书/A独立准入与tests-first文件链，原物理S/B保持，真实来源拒绝 | EP-G8-01/02本地确定性实现，不是实验完成 | MC正文/Q0/历史证据不改；非默认流合成不授予Qwen资格，D/Signature不放行；Gate7 PASS、新Q0/Gate8 NOT_RUN |
| 7.56 | 2026-09-27 | 有界只读区分后缀条件等价与真实来源证明，补查Qwen内部sync及独立反例 | EP-G8-01/02证据必要性判断 | 只更新决策/进度，无代码或合同变化，不运行测试/采集；Gate7 PASS、新Q0/Gate8 NOT_RUN |
| 7.57 | 2026-09-27 | 用户A优先范围下版本化Gate8 A主线退出条件、G8–14精简组织；新增一次7源文件静态选择profile及tests-first验证 | EP-G8-01/02来源补证准备，不是资格或实验 | 不改变S/W/B/MC或旧证据；默认流/真实来源仍拒绝，B/Derived后移；无服务器执行，Gate7 PASS、新Q0/Gate8 NOT_RUN |
