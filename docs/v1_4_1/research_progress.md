# ExposedPath 科研进度清单

## 7.229 真实策略A通过；限定event B控制接线本地完成（2026-10-21，当前）

- [x] 消费协调已审真实A：ZIP 4,955,356 bytes，SHA256
  `894d3636653d4ef30603bd0e279110ef6e18727db7e0fa8343f6989827c5ebdb`；receipt
  `9d6d4000d07ea7d752c78f4d337f88fe35085e99995ee88242eae5a824ad971e`。
  本地再次核对399成员/398清单、CRC/安全路径/全部hash、458源码Git表示、SDK/库、
  原82 passed/0 failed/0 skipped与10项顶层exit0。未重跑A或编译；此A只授静态资格。
  独立小审查在忽略的`cupti_event_target_a_6c744bf_v0_1/review.json`。
- [x] 新`cupti-event-b/0.1.0`控制层绑定真实A/manifest/delivery、6c744bf执行/分析版本、
  已建client.dll（314,880 bytes，SHA256
  `5e0ffa4b332652c6107cb278ed300ddc9b1bc0e201a370dbe1040cb463d2247a`）、
  CUDART/CUPTI及SDK。无checkout切换/重编/重跑A；未变probe/reader沿用6c744bf。
  默认拒绝，显式B只开启1个GPU探针进程/1 session，硬120秒，0 LLM/0 Nsight。
- [x] 沿7.228先验event record→event同步→stream同步；独立reader继续检查真实闭合范围、
  runtime/driver父子、event/context/stream及loss，不能只凭open成功。新父控制器核对
  capture/side/context/session/review全部文件覆盖与hash、成功初始化和完整flush/逆序关闭。
  运行前后fresh核A/HEAD/clean/源码/库，分别保存回执；子进程与后验双失败分别保存原错。
  超时保留真实process及UNKNOWN，拒绝强制封包，无重试/续跑/清理。
- [x] tests-first缺入口与双失败原错丢失红例后实现；最终命令
  `python -m pytest -q -ra -p no:cacheprovider tests/test_cupti_event_b.py
  tests/test_cupti_event_probe.py --basetemp .local/ceb_release --junitxml .local/ceb_release.xml`：
  **45 passed/0 failed/0 skipped，6.57s**。含真实PS5.1开关/hash门、隔离`-I -S`纯CPU读取、
  完整文件链/缺事件/哈希/旧版本/身份/后验冲突/UNKNOWN拒绝；外部CUDA/进程边界明确替身。
  本地Python3.12.7，不是目标3.11.16/GPU验证；复用已审A82项，不重跑Q0或无关检查。
  compileall exposedpath/analysis、变更文件py_compile及diff检查通过。
- [ ] 控制实现先提交后绑定唯一B包/命令；目标事件B仍NOT_RUN，先交协调审查后用户执行。
  新鲜2GiB参与卷检查；预计2～5分钟、回传约1MiB内均为估计，硬预算120秒不延长。
  历史总量null/UNKNOWN，长期50,000,000,000bytes目标独立，不遍历ACL/自动清理。

最高优先级仅本次限定事件关联B交付与实物审查；它不重判旧768启动同因、不修复旧1024，
不授予模型覆盖、W/terminal、COE或Formal，不恢复输入矩阵。原Raw/ZIP/BLOCKED/UNKNOWN、
用户DOCX与大型未跟踪原件、Gate13限定PASS/Gate14 NOT_RUN保持；本轮无服务器/GPU操作。

## 7.228 API22启用策略最小修复与单event验证入口，本地完成待新A（2026-10-21，历史；真实A见7.229）

- [x] 复用7.227归档核验，重新核对本轮消费的原capture及来源hash：旧0.1.0首失败仍是
  `cuptiActivityEnable(36)=21`，新reader照读，原ZIP/Raw/报告不变。实际编译使用的
  cupti_activity/result/version头文件与封存官方12.4.127 ZIP逐字节相同；官方12.9中
  旧CUDA_EVENT/SYNCHRONIZATION耦合说明仅作为API22修复候选依据，不冒充目标证明。
  本地审计`.local/diagnostics/cupti_event_policy_sources_v0_1/review.json`。
- [x] 实现版本化`cupti-api22-activity-policy/0.2.0`：显式启用原前8项，36作为由38控制的
  记录类型保留；只逆序关闭成功前缀，不尝试36、吞码、fallback或重试。全部9种原始kind
  继续解码，事件/缺映射/依赖拒绝不放宽。关闭API原始状态及首失败独立保存，不覆盖初始化。
  新startup0.2.0/session receipt0.1.2/Stage A0.1.2严格绑定policy；旧版本读取/选择保留，
  未知或混用、将新构建假标旧诊断均拒绝；S/A/B/COE和旧冻结合同不改。
- [x] 新增窄域event入口/独立reader及先验手定反例：单进程/单session、0 LLM/0 Nsight，
  事件record→event同步→stream同步，闭合标记+runtime/callback/driver父子+eventId/
  context/stream关联。保留真实返回和失败partial；缺event不能因open成功放行。API22
  event没有设备完成时间戳，保持NOT_AVAILABLE；不构造新W/B或授事件依赖资格。
  独立预期、必需字段/停止条件见[控制策略及事件验证](cupti_submit_effect_vertical_slice_v0_1.md#api22活动控制策略02与事件关联验证2026-10-21当前)。
- [x] tests-first真实SDK/client+CPU ABI替身先复现旧open3/close4及关闭原码丢失，再修复。
  实际命令`python -m pytest -q -ra -p no:cacheprovider tests/test_cupti_activity_policy.py
  tests/test_cupti_timeline_startup.py tests/test_cupti_timeline_session.py tests/test_cupti_timeline_native.py
  tests/test_cupti_event_probe.py tests/test_cupti_timeline_stage.py
  tests/test_cupti_timeline_adapter.py::test_historical_event_is_closed_only_by_explicit_callback_and_later_drain
  --basetemp .local/epol_done --junitxml .local/epol_done.xml`：**82 passed/0 failed/0 skipped，19.69s**。
  含实际client DLL启用顺序/关闭范围/其他接口失败、原码21保留、新旧版本拒绝、SDK事件结构
  解码、实际入口→capture/side→独立reader→receipt的成功/缺event失败文件链，及原事件依赖拒绝。
  本地Python3.12.7/MSVC14.44，厂商CUDA/CUPTI库未执行；参数/事件是CPU替身，不是目标GPU资格。
  compileall exposedpath/analysis、变更scripts的py_compile及diff检查通过；无完整Q0/无关套件。
- [x] 固定执行/分析`6c744bf52daff3fc54571e264a0c34e3207aa1df`。唯一Stage A包
  `cupti_event_policy_6c744bf52daf_delivery.zip`，2,595,474bytes，SHA256
  `96589852237123cbeea892a3d9b4cbd619f5ef79d42f371d470dfe26ee214283`；14成员/13清单、
  CRC/安全路径/hash及458项源码Git表示独立核验通过；SDK/CUPTI/工具链参考与ddc7abc旧包
  完全相同。core.h、runner、S/A/B/COE及迁移7项核心文件与前置字节一致。新包在提交之后
  绑定，控制记录不替代执行身份，不重新包装成文档HEAD。
- [x] 本地短期隔离checkout完整演练PS5.1→bundle/fetch/checkout→真实SDK编译链接→
  CPU82项→前后验/封包成功，10项顶层进程exit0/无超时，399成员/398清单全hash通过。
  本地Python3.12.7/MSVC14.44改配明确记录，厂商库未执行，不是目标3.11/14.38回执。
  原短期clone尝试被沙箱MSYS命名对象权限拒绝，未进入产品；隔离的本地授权演练通过。
  确认clean且无独有资料后移除仅演练checkout，日志/编译证据/完整ZIP保留，源码可从Git
  恢复。证据及包审查在`.local/diagnostics/cupti_event_policy_delivery_v0_1/`。
- [ ] 真实新Stage A待协调审查/用户执行。前置以真实A ddc7abc及e017一次B
  后验A检查确定（控制e017未换checkout），新A仍fresh核ddc7abc HEAD/clean；不猜文档HEAD。
  原SDK/CUPTI/toolchain资产复用，不安装依赖；新DLL写新输出。默认A仅构建/CPU/身份/
  新鲜2GiB，0模型/0 CUDA程序/0采集，无B开关；真实新A审查后另给B命令。
- [ ] 目标事件实物仍NOT_RUN：未来一次硬120秒单进程event验证，成功也只关闭本次限定
  启用/事件关联问题，不证明旧768同因、不修复1024效果、不恢复输入矩阵或旧七槽。

最高优先级仅新A固定交付及协调审查；A估2～5分钟、保留静态证据约4～8MiB，未来B估
2～5分钟/小型回传<1MiB，均非保证。长期总容量null UNKNOWN与50,000,000,000bytes目标
分开，无ACL/自动清理。用户DOCX、原Raw、旧BLOCKED/UNKNOWN、数据角色、Gate13限定PASS/
Gate14 NOT_RUN保持；本轮未操作服务器、未运行GPU/模型/Nsight。

## 7.227 启动诊断取得明确失败：CUDA_EVENT直接启用返回INVALID_KIND（2026-10-21，历史；修复见7.228）

- [x] 回传44,821 bytes、SHA256
  `77403b1db387979784f3e3313cdb139fcc79ebc72e05c0942e78ebc0677e4fe9`；19成员/18清单、
  CRC/路径安全/全部hash、控制源码与e017dca实际Git字节及原交付一致。manifest SHA256
  `c12d34fcf63a9ab47a401f6a2c7c1ea57e0507d750cc69d9e7c962b9b70eecad`。
  实际PID50800、exit2、未超时；执行后A完整核验已完成，原A/源码/库未变。
- [x] UUID/PCI、torch2.6.0+cu124、已加载runtime路径/hash一致；64-byte逻辑张量/1条
  显式流及订阅前drain完成，未加载LLM。成功订阅、线程设置、缓冲注册、双callback域，
  以及RUNTIME/DRIVER/KERNEL/MEMCPY/MEMSET/SYNCHRONIZATION/CONTEXT/STREAM八项显式
  启用均成功；最后`cuptiActivityEnable(kind=36, CUDA_EVENT)`原始返回21，明确失败。
  相同12.4.127/API22 SDK `cupti_result.h`证明21为`CUPTI_ERROR_INVALID_KIND`；不是
  控制器exit2或包装open3，不能称为权限失败、模型失败或1024尺寸问题。
- [x] capture/session/probe/stdout四处失败事实一致；1 context/135 stream资源记录，
  0 callback/0 marker；closed=true、errors=[1]，overflow/dropped/query错误均0。
  close4含累计初始化错误，不另造关闭根因。原768暖机失败未保存原码，因此本次与其
  共享初始化代码不等于已实证两个attempt同因；也未解决旧84次缺效果问题。
- [x] 核对封存官方12.4.127 SDK/文档：record kind枚举存在不等于运行时接受独立enable。
  官方12.9发布说明又明确旧版CUDA_EVENT与SYNCHRONIZATION记录收集耦合，提供了具体
  修复候选依据；它不能替代目标12.4上事件记录实际发出及同次关联的验证。独立审查存
  忽略的`cupti_startup_failure_e017_v0_1`，原ZIP/Raw/回执不覆盖。
- [x] 原最高优先级：版本化区分“显式enable控制项”和“必须保留/验证的记录类型”，
  审查以SYNCHRONIZATION取得CUDA_EVENT的固定API22方案，再做本地修复/回归及有限
  事件/同步实物验证设计。不得在原入口临时吞21、自动fallback、填空event或直接判COE
  合格；必须保留事件解码/依赖拒绝和旧读取版本。本地修复已于7.228完成，目标效果仍NOT_RUN。

计划调整：当前从泛化“启动失败”收敛到具体enable操作拒绝，有可定位的采集器兼容
问题；本轮只读审查原件/固定SDK及第一方说明，未修改生产代码、重跑测试、制作新包
或安排服务器执行。研究方案/Pre-Pilot、S/A/B/COE及旧Formal不变；用户DOCX、Raw、
旧BLOCKED/UNKNOWN、Gate13限定PASS和Gate14 NOT_RUN保持。

## 7.226 新诊断库目标A通过；准备单次无LLM上下文启动诊断（2026-10-21，历史；后续见7.227）

- [x] 新回传4,074,407 bytes、SHA256
  `ba1bd7a5b6b7d3963f7a11c50bca50345a553c1a41a5973a71031c53d87e0c2f`；411成员/410清单、
  CRC/路径安全/全部hash、448项Git blob或显式CRLF源码表示一致。manifest SHA256
  `d7089d1611c805c9381f9ecc8e996ac5c1f8fcd56ec9c63f55543ea5e68fd0fe`；receipt SHA256
  `42e54632d1058ba4c56916ca3dc1bbd72a8f496d81cce857fbbc5fa9ca31e088`。
- [x] 执行/分析固定ddc7abc8a1bf09b40fa868bf1a0c319f3977f80a，真实目标Python3.11.16/
  MSVC14.38完成构建/CPU115 passed、0 failed、0 skipped，13.73s。封存库及SDK身份不变；
  新client313,856 bytes、SHA256
  `372fdca399895c23bdbde8f7fdd1070e554a8e96a73e4792996812b75537066f`；PE仅KERNEL32。
  10项顶层进程exit0/未超时；测试内部预定非零CPU反例不冒充产品失败。末次clean由
  已绑定脚本成功终态证明；本次未查询目标实时状态。新鲜空闲368,571,654,144 bytes，
  满足当次2GiB；长期总量仍UNKNOWN。独立审查存本地忽略的`cupti_startup_target_a_ddc7abc_v0_1`。
- [x] 实现限定B控制器及无LLM探针：仅1子进程/1 CUPTI session、硬120秒，沿用已审库及
  全部9类活动/原顺序，不部署checkout/重编/运行Nsight/加载模型。仅按原目标torch栈
  建立64-byte逻辑张量及1条显式流，订阅前排空；初始化/关闭与标记同次记录，不计算COE。
  PyTorch分配器可能保留更大的底层块，64-byte不是物理显存上限。小上下文不冒充原模型
  三次暖机后的状态；成功也不关闭原故障、不授予模型覆盖或1024准入。
- [x] 新入口绑定真实A receipt/完整manifest/源码/已建库，实际UUID/PCI及已加载runtime
  路径/hash；默认拒绝，须显式开关。失败保留真实进程及startup原码/上下文事实；执行后
  再验A，超时未知writer拒绝封包，无重试/替补/清理。隔离父进程只显式加载已核验的
  stdlib reader，不使用PYTHONPATH或猜测包来源。
- [x] 新功能先有失败用例；修复本地隔离导入及库/执行路径绑定反例后，最终相关87 passed、
  0 failed、0 skipped。含实际SDK/DLL CPU启动链、PS5.1默认拒绝/正向hash门、控制器
  成功/失败封包与后验核验、同次文件消费负例、上下文CPU替身。Python3.12.7/MSVC14.44，
  **不是新目标GPU证据**；完整命令/JUnit存忽略的`cupti_startup_b_*`。语法及diff检查通过。
- [x] 控制提交固定e017dcad666e821a26361581457b12ea441ebaec，native/读取库沿用已审
  ddc7abc，不切换目标checkout。唯一推荐`cupti_startup_b_e017dcad666e_delivery.zip`，
  46,124 bytes，SHA256
  `33fb1922cae2f9adec1ca832729b3e97fb7e56838a9c2b1d6716ef26e686b858`；13成员/12清单、
  CRC/全部hash、真实A引用和Git实际控制字节通过。GPU PCI的4/8位domain及大小写
  表示用原规范化函数核对，是同一设备；未放宽设备门。PS5.1整段命令解析及入口正反
  CPU演练通过。唯一回传`cupti_startup_e017dcad666e_once.zip`；本地交付审查在忽略的
  `cupti_startup_b_delivery_v0_1`，准确服务器路径和命令仅存`.local/`。
- [x] 当时最高优先级：用户显式执行上述一次B并回传，已在7.227核验为明确启动失败；
  预计2～5分钟，GPU子进程硬120秒、
  启动新鲜2GiB，0模型/0 Nsight/1 CUPTI session。B仍NOT_RUN，目标失败接口和原始
  CUptiResult仍UNKNOWN；不会由小上下文通过追认模型故障或1024资格，不恢复负载系列。

计划调整：继续此前已定的初始化定位步骤，未增加模型/样本预算。对同一初始化序列的
小上下文失败可获得具体接口/码，若通过则只排除该小上下文中的失败；不做跨状态归因。
本轮未操作服务器或运行真实GPU；研究方案/Pre-Pilot及生产S/A/B/COE不变，用户DOCX、
Raw、旧BLOCKED/UNKNOWN、Gate13限定PASS和Gate14 NOT_RUN保持。

## 7.225 新诊断库Stage A有限交付接线；目标启动问题仍未解决（2026-10-21，历史；后续见7.226）

- [x] 下一操作先固定并构建7.224的新诊断库，不重复运行旧768模型包。Stage A合同及
  receipt显式版本化为0.1.1，固定加入真实SDK/实际DLL启动失败链和原失败process回填
  检查；原0.1.0读取路径及固定测试选择保留，未知/混用诊断版本拒绝。A无B开关，
  model/micro/profile预算均为0；前后核验源码、产物、SDK及runtime实字节。
- [x] 新负例先复现2失败/14通过；修复后阶段A选定7文件共115 passed、0 failed、
  0 skipped。本地Python3.12.7/MSVC14.44、真实12.4/API22头文件与CPU ABI替身，
  没有加载CUDA/CUPTI厂商库，不代表目标14.38/3.11或GPU通过。记录在忽略的
  `cupti_startup_stage_red/green`及对应JUnit。
- [x] 最终执行/分析固定ddc7abc8a1bf09b40fa868bf1a0c319f3977f80a，从目标可信7fa36ef
  制作唯一推荐`cupti_startup_ddc7abc8a1bf_delivery.zip`：2,597,527 bytes、SHA256
  `5b20a7b44a743cb8c7bbc7ec81b57e8313a0a6127115a043b70f08c90472ecba`；14成员/13清单、
  CRC/全部hash、448项源码表示及bundle verify通过。SDK/CUPTI/工具链资产与原封存包
  字节相同；前置checkout须7fa36ef且clean，新输出不覆盖旧A。此前0c7db8b本地候选
  已被深路径修正替代，不作为用户执行包。
- [x] 首次完整本地部署/编译成功，CPU为112通过/3失败：新加入的B控制器CPU fixture
  在深层输出下超过Win32路径限制，尚未到模拟进程；不是目标CUPTI故障。仅将该测试的
  自动长目录名改为短唯一名，未改生产路径/校验。独立深路径11项通过；另一次复核的
  basetemp父目录未建导致setup错误，保留记录，不将其计为产品故障或通过证据。
- [x] 修正后的本地完整PS5.1→bundle/fetch/checkout→真实SDK编译/链接→CPU115项→
  后验身份检查→封包链成功，0失败/跳过。10项顶层进程均exit0/未超时；仅用CPU ABI
  替身，不运行厂商GPU库。归档及审查存忽略的`cupti_startup_delivery_v0_3`，本地机器
  路径/3.12.7/14.44改配明确单列，不能冒充目标回执。演练临时checkout确认无工作修改、
  无独有提交、ignored仅pyc后已移除，日志/封包及失败原件保留。
- [x] 当时最高优先级：用户执行新Stage A，回传`cupti_timeline_ddc7abc8a1bf_static.zip`；
  已在7.226核验通过。
  A预计2～5分钟/启动新鲜2GiB空间；仅部署/构建/CPU，目标3.11.16/14.38仍NOT_RUN。
  已生成完整PS5.1命令并解析通过，无采集开关，无自动清理或历史ACL/占用遍历。
- [x] 新目标A真实回执审查后，准备单次最小CUDA上下文启动诊断，记录每一步API及
  原始状态。最小上下文不等于原模型三次暖机后的状态；若通过，不能据此关闭模型故障。
  本轮不自动授权/运行GPU，不恢复输入矩阵；原768失败和1024缺效果继续BLOCKED。

计划调整：有限工程诊断阶段，只解决初始化可诊断性与新库部署；不跳过任一必需活动、
不换CUPTI版本、不重试/提权/重跑旧模型。前述最小启动诊断是有界的下一候选步骤，
不是新模型资格或研究结果。研究方案/Pre-Pilot、生产Raw->S/A/B/COE及旧Formal不变；
用户DOCX、Raw、UNKNOWN、Gate13限定PASS和Gate14 NOT_RUN保持。

## 7.224 本地修复CUPTI初始化诊断与失败进程回执；目标原因仍待实物（2026-10-21，历史；后续见7.225）

- [x] 用户明确要求按7.223分析进行本地修复。新增有界初始化事实记录
  `cupti-timeline-startup/0.1.0`：API名称、activity kind及名称、原始状态码/成功状态、
  CUPTI/WIN32/CONTRACT/EXCEPTION域、完整步骤和首个失败分开保存。首次失败不被后续
  catch或关闭覆盖；旧open_code=3仍保留，不再把它当作原始CUptiResult。
- [x] session receipt版本0.1.1将已验证的首个失败带入Python异常与回执。旧capture没有
  新诊断字段时保持None；出现未知版本、类型冲突、首失败不一致或成功矛盾时明确拒绝/
  保留诊断错误，不补造API原因。失败进程的原process.json现在回填顶层receipt，保留
  原PID、exit和timeout状态；失败即停、后验A检查及unknown writer拒绝继续生效。
- [x] 保持原初始化调用顺序及全部9类活动，无自动重试/删除类型/新CUDA同步。原
  `Raw->S`来源桥、必要集合算法、生产A/B/COE及模型/P helper未改。新诊断是事实扩展，
  不授予纯Host阻塞或新的测量资格。
- [x] 先复现信息丢失及process=null反例，再修复。真实CUDA12.4/API22头文件、MSVC14.44
  编译链接实际client和独立CPU ABI替身；实际DLL覆盖stream/event、订阅、线程/缓冲/
  driver域、缺库/缺导出/版本冲突及成功路径。替身不加载CUDA/CUPTI厂商库；另有实际DLL
  经Python隔离子进程写回receipt的完整失败链。CPU注入码不是服务器原始码。
- [x] 最终相关检查126 passed、0 failed、0 skipped；Python3.12.7。包含新诊断、session/
  控制器、真实SDK/native、Stage A禁采、producer两token、来源桥及区间参考；语法与
  diff检查通过。完整命令/JUnit/build及原red记录位于本地忽略的`cupti_startup_*`目录。
- [ ] 最高优先级：在另行固定新执行身份/构建/预算后，以修复后的记录获得目标机明确
  初始化失败操作和原始状态，再决定针对性修复。原59,045-byte失败ZIP仍BLOCKED，
  具体目标API和原始CUptiResult仍UNKNOWN；未制作部署包/服务器命令，未执行新GPU或模型。

计划调整：本轮完成用户明确授权的本地诊断缺陷修复，未推断或修改尚未查明的CUDA启用
机制；未重采、提权、换栈或恢复负载矩阵。目标MSVC14.38/Python3.11和实际provider覆盖
尚待后续实物。研究方案/Pre-Pilot与历史数据资格不变；用户DOCX、Raw、旧BLOCKED/
UNKNOWN、Gate13限定PASS和Gate14 NOT_RUN保持。

## 7.223 新768模型诊断在CUPTI初始化失败；原始错误码缺失（2026-10-21，历史；后续见7.224）

- [x] 回传ZIP59,045 bytes，SHA256
  `dc25d11710cd2a5ff3741f9a1204e3f2ed873544af4f9276573620ae80d7590f`；21成员/20清单、
  CRC/安全路径/全部hash通过。manifest SHA256
  `fda6ed5e7a2b3290c6ab1da4d5f570c6a12106e0b6cca189e1d0da73a47a1d47`。
  原delivery/控制脚本/模型入口/launcher/A参考原件均与c58c65b固定包一致。
- [x] 实际PID13504以exit1结束，未超时；模型内容、GPU UUID/PCI、Python3.11.16/
  torch2.6.0+cu124、FP16/SDPA和[1,768]输入检查已完成，原三次暖机均完成。
  首个明确异常为`CUPTI_TIMELINE_SESSION_OPEN_FAILED:3`，发生在subscription打开阶段，
  早于原测前drain、测量请求和两token完成操作；未进入同次COE分析。
- [x] 原capture与session/子进程PID及hash一致：open_code=3、close_code=4；仅1条context、
  7条stream资源记录，无callbacks/markers。quality.closed=true、errors=[1]，无overflow/
  dropped/query错误。close_code=4包含累计初始化错误，不能单独认定关闭又发生独立故障。
- [x] 已确定记录缺陷：native初始化把所有CUPTI非成功码和异常合并成open_code=3，未
  保留操作名、activity kind和原返回码。资源发出将位置缩小到stream dump/其后event启用
  附近，但“已有资源行”不证明对应EnableAndDump成功返回，具体失败API仍UNKNOWN。
  不认定权限、模型、零payload、某一库或某种activity为根因，不关闭必需观测来绕过。
- [x] 采集后A检查已实际执行成功，原封存源码/库未变。顶层receipt.process为null是因
  command先抛异常而未赋值；原one_model.process.json保留了真实PID/exit，不代表未启动。
  原始回执/capture/ZIP保留，独立审查在本地忽略的`cupti_model768_c58c65b_failure_v0_1`。
- [ ] 最高优先级：本地先设计/补齐可测试的初始化逐步返回事实及原始错误码，再据明确
  原因决定最小修复与是否需要目标验证。当前没有可信参数/必要集合/COE；不重跑模型、
  不重做A、不恢复输入矩阵或旧七槽。目标provider/PyTorch资格继续BLOCKED/NOT_ASSESSED。

计划调整：本轮按用户报错进行只读诊断和事实收口，未修改业务代码或制作新包，未运行
GPU/服务器命令。CPU/编译检查没有覆盖真实CUPTI初始化，是此前验证边界，不能追认GPU
通过。研究方案/Pre-Pilot及生产S/A/B/COE未变；用户DOCX、Raw、旧BLOCKED/UNKNOWN、
Gate13限定PASS和Gate14 NOT_RUN保持。

## 7.222 CUPTI时间线目标Stage A通过；准备单次768模型接回验证（2026-10-21，历史；后续见7.223）

- [x] 真实Stage A回传3,040,625 bytes，SHA256
  `89265f8ddcce6b513457b1d40f44eda325e058f9cf654cf53d40d05476ae5376`；231成员/230清单、
  CRC/路径与全部hash通过。manifest SHA256
  `18565ddc0153e48111dc6238c7e72b3339972e23b3c15ab43f8e12ca38e45d72`；receipt SHA256
  `59271549fb7e4fb160870af0303aeba6b6fc9eae8f02a5c74b5e80047cc18ef2`。
- [x] 执行/分析固定7fa36ef；438项实际源码逐Git blob/显式CRLF表示一致，原delivery及
  资产身份匹配唯一reviewed包。原日志/JUnit一致：82 passed、0 failed、0 skipped，
  3.23s；10项部署/构建/导出/CPU进程记录均exit0且未超时。目标Python3.11.16、
  MSVC14.38/SDK10.0.20348.0真实编译链接成功；DLL/Host程序仅导入KERNEL32。
  最终clean由已绑定入口成功执行末次tree检查证明；未另查服务器实时状态。
- [x] 新鲜参与卷空闲368,942,075,904 bytes，满足当次12GiB预留；历史YLQ总量仍UNKNOWN。
  审查记录存忽略的本地`cupti_timeline_target_a_7fa36ef_v0_1/review.json`。Stage A只授静态
  部署/构建/CPU通过，模型/GPU/COE资格不由此授予。
- [x] 已补独立Stage B控制器和模型入口：绑定真实A原件、库及438源码，复用已建DLL，
  不切checkout/重编/重跑A。固定新768/batch1/输出2/warmup3/repeat1；原P方法直接继承，
  模型/输入加载和原暖机在订阅前完成，随后同进程同次记录原drain及两个token完成操作。
  新观测来源与订阅位置单列，不能把时延并入旧Nsight曲线。
- [x] 原producer、输入/模型内容、实际token、CUPTI时钟/资源/参数/活动、关闭与丢失检查
  接入同次局部S/COE消费；模型或分析失败也执行后验A检查并保留回执。手定两token文件链
  预期20ns/1ns复现；错PID/篡改/错token/缺scope/关闭与暖机冲突均拒绝。
- [x] 本地新接线/同次文件链27项及相关来源桥/adapter/session共87 passed，另有原P/helper/
  Stage A入口68 passed，均0 failed/0 skipped；数量按命令分别记录，不相加成资格。真实
  PS5.1默认拒绝及显式CPU替身入口、控制器成功/模型失败/分析失败封包和后验检查通过。
  本机Python3.12.7；新模型入口在目标3.11及GPU上的实际执行仍待验证。
- [x] B控制版本固定c58c65b94b5a33d6fb7b49cfa195edec4d348aed；唯一
  `cupti_timeline_b_c58c65b94b5a_delivery.zip`为48,019 bytes，SHA256
  `9c24ad3f12d59794dc401706081e5de53e101d78ddc8b4b2b6709bfc6252d5fe`。
  16成员/15项清单、CRC/hash、Git实际控制源码、原helper复用及隔离默认禁采检查通过。
  准确传输路径与整段PS5.1命令在忽略的本地CUPTI_TIMELINE_B_DELIVERY.md/STAGE_B.ps1。
- [ ] 当前最高优先级：待用户执行固定B并回传；预算仅一个新模型进程/一个
  CUPTI session，零Nsight/零micro；模型硬300s、离线分析180s，固定一次或硬失败即停。
  目标真实PyTorch覆盖、768缺口闭合、观测扰动和新COE准入仍NOT_RUN/NOT_ASSESSED。

计划调整：用户要求继续已授权的通用来源修复；本轮以真实A为前置准备一个新失败形状的
同次模型诊断。没有恢复长度矩阵/旧七槽，不使用新参数追认旧768/1024。当前研究方案及
Pre-Pilot协议不变；生产S/A/B/COE、Raw、历史BLOCKED、UNKNOWN、Gate13限定PASS与
Gate14 NOT_RUN保持。用户DOCX未改。

## 7.221 按用户授权实现提交效果桥与同进程CUPTI局部文件链；目标资格NOT_RUN（2026-10-21，历史；后续见7.222）

- [x] 用户明确暂停追加负载点，要求解决通用来源缺口并完善脚本。重新启用限定的独立
  CUPTI纵切片：ENTRY参数/EXIT返回、逐线程真实父子关系、分域correlation、kernel/
  Memcpy/Memset/API/物理sync/资源及原token标记同次取证。没有与Nsight并采或换后端。
- [x] 新`submit-effect-bridge/0.1.0`区分提交→效果与同步→必要成员；允许有实际API行的
  顶层driver提交。实际零payload保留逻辑节点/API时间，不虚构效果；非零缺效果、错域/
  错流/丢失/关闭失败拒绝。实际嵌套driver同步单列，缺API行不补墙钟。不是把memset或
  copy名称直接改成sync。有限支持域、版本和独立预期见
  [纵切片合同](cupti_submit_effect_vertical_slice_v0_1.md)。
- [x] 原标签与物理drain→新Raw→来源桥→局部必要集合→COE的完整Host文件链通过；
  独立预期20ns/15ns及内部同步13ns复现。新入口82 passed、0 failed、0 skipped，含
  真实CUDA12.4/API22头文件编译链接和Host替身；相关旧路径156 passed、0 failed、0
  skipped。本地MSVC14.44/Python3.12.7；**不是目标14.38/3.11、真实GPU或Q0资格**。
- [x] 新Stage A仅部署、构建、CPU及新鲜空间/身份检查，模型/微例/profile预算全0；
  无B采集开关。不按输入长度写豁免，不修改旧生产S/A/B/COE、旧Raw或历史判定。
  本机PS5.1正向入口发现`Get-FileHash`缺件，改用.NET SHA256并保留正向CPU驱动反例，
  隔离包演练另发现`-I`忽略bytecode环境变量，bootstrap现显式禁写，独立子进程核对包目录
  不新增缓存。不把本机演练称作目标机验证。
- [x] 执行/分析锁定7fa36efb340fe59a3138eb6132e162d6b0cbfc41。唯一reviewed ZIP
  2,596,307 bytes/SHA256 `2957f49862b3eaac4e70b57e41220f7ce9a93886485fbbe3855d59b6645841da`，
  14成员/13清单/CRC/hash/bundle通过；438源码表示、旧421科研源码不变。原厂CUPTI资产
  仅留编译头文件/DLL/许可证，避免不参与执行的HTML长路径；所留字节不改。私有准确传输
  路径和整段A命令在忽略的本地CUPTI_TIMELINE_DELIVERY.md/STAGE_A.ps1。
- [x] 最终包本地完整CPU控制演练exit0：PS5.1→真实Git部署/clean→源码与库身份→真实
  SDK编译链接→82项检查→末次身份→ZIP。显式本地路径/Python3.12.7/MSVC14.44替代，
  不是服务器回执。原失败演练和最终receipt/JUnit/log均保留，临时checkout完成后移除，
  不长期保留测试仓库副本。新服务器A、GPU和PyTorch覆盖仍NOT_RUN。
- [ ] 最高优先级：固定执行版本的Stage A真实回执；随后才准备单次同进程模型覆盖诊断，
  需要同次全部必需记录及关闭/丢失证据。真实PyTorch覆盖、provider扰动和新COE准入
  均NOT_RUN/NOT_ASSESSED，不能宣称768/1024或所有输入已修复。

计划调整：本轮从纯审查进入用户明确授权的本地Engineering实现；不追加长度矩阵/恢复七槽，
不把新参数拼接旧Nsight记录，不扩至并发/多GPU，不自动启用GPU采集。阶段A交付后暂停
等待真实回执，后续单次模型诊断另绑定原输入/producer/token/设备与库身份。当前研究方案
与Pre-Pilot协议不变，无新Protocol Freeze/Formal资格。用户DOCX/大原件保留；历史BLOCKED、
UNKNOWN/NOT_ASSESSED、Gate13限定PASS、Gate14 NOT_RUN不变。

## 7.220 增量三点Pilot在768的提交效果证据门阻塞；不续七槽（2026-10-21，历史；后续见7.221）

- [x] 回传失败ZIP11,457,863 bytes，SHA256
  `176dc97ed38db012d023103d247425c94e170f17e894064a4806e3ec99f42a11`；184成员/183清单、
  CRC/安全路径/全部hash通过，manifest SHA256
  `4e2a349513d5dd1189a98352086a9977fba375c1b32bd81db9cd2f7321231e44`。原A的23个
  文件逐字节保留，原delivery/launcher及421项实际源码匹配8197f0d，非部署身份冲突。
- [x] 新512、768均模型exit0、profile进程exit0且未超时、SQLite export PASS；512两token
  消费完成，768在`preparation_both_token_admission`拒绝：
  `OBS_PREP_BOTH_TOKEN_ADMISSION:['ENGINEERING_SCOPE_SUBMIT_MAPPING']`。
  本批1 COMPLETE、1 BLOCKED、7 NOT_RUN、0完整block；1536尚未运行，不能形成相邻
  signed差/R或据失败推断1536资格，不从旧批拼接补齐。
- [x] 独立Raw/Canonical核对：40,709条runtime、13,408条kernel、348条Memcpy、568条
  Memset数量一致，全部runtime的行ID/名称/时间/correlation/返回码/callchain逐行一致。
  Request内56次成功`cudaMemsetAsync_v3020`无关联设备效果，**全部在Prefill**；首条
  runtime36560/correlation170542，距Request开始3.756075ms。该Prefill另141次目标调用
  有映射，Decode目标调用1次有映射；不能把56项整体隔离到未来窗口或填为零。
- [x] 56条correlation在原kernel/Memcpy/Memset/sync表均无命中；已检查全部六种CUPTI
  表的correlation字段，无driver/callchain/backtrace表，目标callchain均null，runtime表
  没有count参数。原SQLite/导出副本与Canonical源hash一致；未建立可离线修复的解析遗漏
  或替代关联。**直接拒绝原因确定，效果为何缺失/是否零payload仍UNKNOWN**；不声称
  丢了56个真实设备操作、无操作或某个backend导致。依赖/terminal后续准入未完成。
- [x] 可保留新512单次Pilot：首/第二token COE为3.418316/0.813147ms；只是单次结构记录，
  不构成新增重复或负载趋势。旧合格256/512/2048、O/P及Formal原角色与结论不变。
  审计命令`python .local/diagnostics/coe_incremental_failure_8197f0d_v0_1/review.py` exit0；
  audit.json、56条CSV及只读SQLite副本保留；未重跑完整analyzer/Q0/CPU或GPU。

计划调整：本次attempt保持BLOCKED，不重采/续跑/替补/清理；暂停追加输入点或下一矩阵。
下一修复决策须针对这类调用的实例参数/明确效果关联或可证明的消费语义，不能仅增加长度
常量、按无activity豁免或自动重启已暂停provider工程。当前没有可验证的纯离线修复依据；
这不是“768推理不支持”或断言问题永远不可修复。当前最高优先级为将此精确失败事实交主
窗口作有界修复可行性裁决，并继续保全已审研究证据。本轮仅审计与进度记录，无服务器
操作/业务代码修改/新包；用户DOCX/Raw及原A/B/COE、1024 BLOCKED、Gate13限定PASS、
Gate14 NOT_RUN、UNKNOWN/NOT_ASSESSED全部保持；不升级新Formal或全输入适配资格。

## 7.219 增量三点真实A回执审查通过；B待用户显式启动（2026-10-20，历史；后续见7.220）

- [x] 新A原ZIP108266 bytes，SHA256
  `c030e4dbb8739044aa64371ed579d92f511296f52fe0c7d96818750dd1b536bb`；23成员/22清单、
  CRC/安全路径/全部hash通过，manifest SHA256
  `f4948aeaf0ddb8984a19324e9baff300421709baf458fcae5f193690e142bd33`。原delivery/执行
  launcher与已审包逐字节一致，执行/分析8197f0d，421项实际源码均匹配；8项退出记录exit0。
  绑定入口成功终态证明最后clean检查已通过，不冒充独立服务器实时查询。
- [x] 实际controller和target Python均3.11.16、isolated=1/no_site=1；CPU原日志与JUnit
  一致：**36 passed、0 failed、0 skipped**，113.25s，compile exit0。默认A没有真实模型/
  CUDA/Nsight采集；这是已绑定执行链的静态资格，不是768/1536 GPU或COE准入。
- [x] 空间记录为2026-10-20T14:04:18Z，唯一参与卷可用369077116928 bytes，输出/临时/
  归档路径可写，满足12GiB门；B会fresh重查。历史YLQ总量仍null/UNKNOWN，不扫描ACL、
  不据空闲推断长期占用、不自动清理。原A仍保留measurement_validity=NOT_ASSESSED及
  dropped_records_status=UNKNOWN。
- [x] 原receipt SHA256
  `719b687a4c356b680ea652210f21fcc2317c4b03e171cf376ba219ae0660f670`已绑定显式B命令。
  命令另核launcher/delivery字节，实际PS5.1解析及三个哈希与原件交叉检查通过；未运行。
  只读审计及静态原件副本位于`.local/diagnostics/coe_incremental_target_a_8197f0d_v0_1/`。
- [ ] B仍NOT_RUN，由用户显式执行既定512/768/1536各3次、9P1，预计30～45min非硬保证；
  逐槽driver900s/profile300s、fresh12GiB及原证据门继续适用。固定9次或硬失败即停，
  不重试/续跑/替补/拼旧block。回传`coe_input_8197f0d0d6ac_pilot.zip`后逐原件审查；
  当前不预授新长度、完整物理B、新Formal或科学响应结论。

本轮仅只读审查真实新A及生成已审B命令，未重跑CPU/模型/采集、未操作服务器或修改业务
代码/包/合同。用户DOCX与Raw保留。原A/B/COE及所有历史BLOCKED/UNKNOWN、Gate13限定
PASS/Gate14 NOT_RUN不变；当前最高优先级是用户执行既定B并回传唯一原ZIP。

## 7.218 增量三点交付协调复核通过：仅允许执行新阶段A（2026-10-20，历史；后续见7.219）

- [x] 独立审查7.217唯一ZIP：100342 bytes及SHA256与交付一致，19成员/18清单、
  CRC/安全路径/全部hash、421项Git源码表示、三份完整输入/mask摘要及13项未变核心组件
  均通过。bundle verify/list-heads和唯一前置核对通过：8f49ab0→8197f0d；包内计划、
  launcher、旧成功A/B回执与封存原件字节一致。当前测试代码与8197f0d执行版本一致。
- [x] 本地独立重跑7.217同组最小相关检查：**36 passed、0 failed、0 skipped**，170.29s；
  JUnit实际36项、errors=0。Python3.12.7，实际Windows PowerShell5.1.26100.9711；
  真实文件/隔离子进程/PS分派检查使用明确的外部OS、设备与collector CPU替身。
  包内原36项与11项JUnit亦核验，无重复相加；不代表目标3.11或768/1536 GPU资格。
  另直接解析包内launcher，PS5.1无语法错误。审查脚本、audit.json、cpu.xml/log及
  包副本保留在`.local/diagnostics/coe_incremental_coordination_8197f0d_v0_1/`。
- [x] 排程与边界复核：只运行新512/768/1536各3次、3完整block；原P/helper/完成政策、
  S/A/B/COE与迁移不改。相邻signed比较、无效分母保持undefined；不把旧2048配对、不按
  512校正历史点、不预设单调。默认A仅部署/CPU/compile/fresh12GiB，B必须绑定本次真实
  成功A回执及另行显式开关；源码/空间冲突与硬失败拒绝，固定预算不重试/续跑/替补。
- [ ] 新目标A与B仍NOT_RUN。下一步由用户在服务器执行已审原阶段A命令，回传
  `coe_input_8197f0d0d6ac_static.zip`原件；真实A审查通过后才另给B命令。协调记录提交不
  改变包执行8197f0d或服务器前置8f49ab0，不要求把服务器切到文档HEAD。

本轮仅本地协调审查及最小CPU复核，未修改业务代码/包/合同，未运行模型、CUDA或Nsight，
未操作服务器。研究方案v7.1/协议v2.1的Pre-Pilot身份与本批Pilot角色不变；无新Freeze/
Formal资格。Gate13限定PASS、Gate14 NOT_RUN、1024及历史BLOCKED/UNKNOWN保持。
当前最高优先级为取得并审查新A原回执；用户DOCX与Raw均保全，不纳入本次提交。

## 7.217 Raw机制已核对；独立512/768/1536增量Pilot本地接线（2026-10-20，历史；后续见7.218）

- [x] 先完成7.216原件机制核对：输入ZIP身份不变，只读9份SQLite及18条已审链，复用必要
  成员/提交映射而非按重叠选成员、不重建S。生成每kernel符号、次数、grid/block/动态共享、
  提交API行及返回位置、copy前/操作内执行并集；18链、1356个符号/布局分组可追溯。
  小型[机制摘要](coe_low3_raw_mechanism_v0_1.csv)及[短稿§13.1](coe_research_short_note_v0_1.md#131-已有raw机制核对与有限中间点探索2026-10-20)
  已补充；完整派生及只读审计在`.local/diagnostics/coe_low3_mechanism_v0_1/`。
  实际命令`python .local/analyze_low3_mechanism.py` exit0，约9.85s；没有完整analyzer/Q0。
- [x] 2048首token必要kernel数1762，低于512的1818和256的1846；全部提交API在copy前
  返回，2048最后返回距copy0.093039～0.116935ms。2048 copy前执行46.308962～49.461800ms，
  操作内93.860885～102.665413ms，其中kernel93.766678～102.613605ms。block1实际
  fp16 GEMM(56次，grid70×16×1/block128×1×1)、SoftMaxForwardSmem组(28次，
  grid24576×1×1/block1024×1×1)、add<float>组(28次，grid196608×1×1/block128×1×1)
  分别贡献12.735186/8.900520/8.892519ms。完整模板符号和Raw/API来源不缩写丢弃。
  排除“仅复制/整API/更多kernel次数”这一描述；总量、布局和相对位置都变，尚不能识别
  后端选择、CPU/driver/profiler根因或净因果贡献，未声称纯Host阻塞或无插桩迁移。
- [x] 新增独立`COE-INPUT-P-INCREMENTAL-PILOT/0.1`，有限输入/mask身份、prepare/seal
  分派、消费及完整block汇总；旧LOW3/0.1、0.1/0.2/四点0.3不改。计划
  [JSON](../../configs/coe_input_incremental_pilot_v0_1.json)：512→768→1536、768→1536→512、
  1536→512→768，9个新P1，固定P/batch1/输出2/warmup3/repeat1及原自然Host-readable路径。
  首token两项相邻signed ΔCOE/R为主要比较，512→1536描述性；第二token及原A/独立候选
  预算/同操作union/成员位置全保留，完整block为比较单位。没有新1536与旧2048的配对，
  共同512只查部分跨批漂移，不校正旧点；不预设平滑/单调/显著，不解锁1024或旧七槽。
- [x] tests-first先观察`COE_INPUT_BINDING_VERSION`及真实PS分派`Delivery conflict`红例，
  再最小接线。实际`python -m pytest -q -ra -p no:cacheprovider tests/test_coe_input_incremental.py
  tests/test_coe_incremental_delivery.py tests/test_coe_helper_identity.py::test_pinned_source_provenance_and_real_isolated_python
  --basetemp .local/increment_final --junitxml .local/increment_final.xml`：**36 passed/0 failed/0 skipped**，
  98.17s。覆盖prepare→seal→实际profile argv、producer/Canonical→两token→预算→3完整block，
  输入字节/role/版本/token/drain/依赖/hash、signed负/零及无效分母、PS5.1默认A/显式B新receipt、
  空闲不足/未知/不可写/来源冲突和硬失败未运行槽位。外部设备/OS/collector用CPU替身，
  真实隔离子进程使用`-I -S -B`，不称768/1536目标资格。
- [x] 受影响旧版本定向回归：原端点R、LOW3低侧R、中点/四点signed、旧四点入口拒绝及
  LOW3静态资源分派共**11 passed/0 failed/0 skipped**（10.93s），证据`.local/increment_legacy.xml`；
  `python -m compileall -q exposedpath analysis`、两个变更scripts的py_compile及diff检查exit0。
  本地Python3.12.7；本机py launcher无注册3.11（不是全盘环境断言）；真实目标3.11.16旧A
  仅复用为历史依据，新A同时记录controller/target实际版本。未重跑完整Gate/Q0/无关套件。
- [x] 实现/分析精确绑定`8197f0d0d6ac35ef17c4c5f6ba0d9ed00fe5b41e`，已正常推送。
  唯一`coe_incremental_8197f0d0d6ac_delivery.zip` **100342bytes**，SHA256
  `0716d92194467385d5168a96f6f4f33cfdb0c06bbf1760f25678184806460582`，manifest SHA256
  `d5e94fd0b19d149b64b77a51647b3304154107861467a3bbc2e6f14aea0d1025`；19成员/18清单，
  CRC/安全路径/覆盖/hash通过，另独立逐Git blob核对421项源码表示及13项未变核心组件。
  bundle精确要求8f49ab0、目标8197f0d，verify/list-heads通过；计划/三份完整input与mask摘要、
  launcher、原静态/成功执行回执及组件兼容均绑定。包内不含模型/大型Raw或可执行GPU产物。
  本地全源码审计`.local/coe_incremental_8197f0d0d6ac_package_full_source_review.json`；本次
  包身份记录是实现commit之后的控制元数据，不修改bundle目标或产生哈希自引用。
- [ ] 真实新阶段A待协调审查/用户执行；B NOT_RUN。新A必须fresh核实际HEAD/clean为封存
  成功执行`8f49ab01ca3606626bce0987e6129b4d0f9ae637`，不能用22f71f4文档HEAD代替服务器。
  新launcher/源码绑定新commit，默认仅部署/CPU/compile/参与卷fresh空间，无CUDA/模型/profile。
  真实新A原receipt审查后才另给B命令。768/1536首次真实准入就在预定槽位，硬失败或9次即停，
  无试跑、重试、替补/拼块、自动追加或清理。

资源按7.216真实9driver总1325.062s、单槽133.297～175.156s、完整ZIP66,509,841bytes/
展开900,187,644bytes重新估计：新B约30～45min，A约2～5min，保留ZIP65～140MiB、展开
1～2GiB，均非保证；未知新分支/取证/服务器竞争可改变成本。实际profile硬300s、外层每槽
900s，9槽driver上界合计8100s，不误称45min全局硬超时。启动仍参与卷新鲜12GiB门，
同卷不重复计数，长期目标<50,000,000,000bytes/历史总量null UNKNOWN独立记录，不查ACL。
当前最高优先级仅本地单包身份复核及协调审查新A；本轮无服务器/GPU/Nsight/新模型执行、
无图/开题稿/新采集设施。原A/B/COE与迁移、数据角色、Gate13限定PASS/Gate14 NOT_RUN、
所有BLOCKED/UNKNOWN/NOT_ASSESSED与用户DOCX和Raw保持，用户修改不纳提交。

## 7.216 固定P低侧三点九次完成：256准入闭合，首token响应复核（2026-10-19，历史；后续见7.217）

- [x] 新Pilot ZIP66,509,841 bytes，SHA256
  `9e0bbefd89f0a7500e05d43545e028db9171bcd6d8be2509439cdb9883630c9a`；691成员/690清单、
  安全路径/CRC及全部hash核验，manifest SHA256
  `0501c0b1204821660665743fdb30702d23c1d443eebe282d698bc5356e8448e9`。
  原A的23成员字节不变，delivery/launcher/418项实际源码与8f49ab0一致，根3个exit0；
  9run/9profile、3完整block、18条token链、27个原A/候选预算均齐全，无替补或拼旧样本。
- [x] 独立只读核对387条来源hash、47,946次活动行引用和47,991次API行引用（含累计前缀
  重复，不是样本数）、物理drain/sync、D2H及terminal；18条区间并集/27窗口/8,656个
  迁移片段行去重守恒，Request=Prefill+Decode。未重跑完整analyzer或Q0；不授完整物理B。
  256本次两token链在原声明支持假设下闭合，并非一般长度或新Formal资格；1024仍BLOCKED。
- [x] 首token COE中位数：256为0.912891ms，512为2.681677ms，2048为97.546735ms；
  各自COE/Prefill范围1.094920%～1.309083%、2.976901%～3.840910%、
  50.185424%～55.525901%。独立候选完成预算/Prefill分别1.110507%～1.327438%、
  2.997711%～3.862568%、50.201676%～55.541197%，不是旧Device wait或纯Host阻塞率。
  3个block首token均256<512<2048；低侧R为+1.340980/+0.451339/+1.166011ms，
  端点R为+91.044476/+88.784905/+82.895469ms。端点G增长4.021～4.266倍，COE增长
  35.001～44.769倍；仅作固定P/profile/模型的Pilot响应线索，不作显著性或普遍单调结论。
- [x] 现有Raw位置核对：首token在copy入口已有提交API返回但活动尚未完成的必要kernel，
  256为5～13个、512为14～80个、2048为1089～1174个；2048 COE约99.87%～99.95%
  为先行kernel，其余为MemOp，不是把8-byte D2H或完整copy墙钟改算等待。该计数不是硬件
  队列深度或因果证明。同输入三个block的必要kernel名称/grid/block序列一致；跨输入不同。
- [x] 第二token没有相同单调响应，2048 block2的6.732092ms保留。全部12个预定token
  比较中，copy墙钟与COE方向10个相同、2个相反：block1端点ΔCOE−0.022431ms/
  Δcopy+0.041102ms，block3为+0.084259/−0.176974ms。这是实例级参照差异，不证明
  稳定判别优势；全18条同操作GPU union仍等于COE，完整timeline能恢复相同答案。
- [x] 原下一项：优先利用本批Raw检查2048暴露所来自的具体kernel符号/实现、提交及执行位置，
  提出一个有竞争解释和失败判据的机制假设，再审最小后续验证；不立刻堆输入点、扩输出轴
  或恢复1024/provider。该只读任务已于7.217完成并另获有限中间点本地准备授权；本条保留
  当时无新GPU预算/采集包/服务器命令的状态，旧B已经执行不可重跑。

完整18条原值与27个预算见[本批结果](coe_input_low3_results_v0_1.csv)、
[预算](coe_input_low3_budgets_v0_1.csv)，每行绑定Pilot/执行commit/源ZIP/run身份；
科学收口见[短稿§13](coe_research_short_note_v0_1.md#13-固定p低侧三点pilot九次完成2026-10-19)。
两份新汇总CSV使用LF行结束；仅调整派生文本表示，原ns、字段/来源、Raw及运行文件未改。
2026-10-20收尾核对：18/27行与原派生表及前次提交逐字段相同，仅行结束表示变化；
未新增实验或修改语义，不重跑已完成批次。
审计代码、12项signed比较与来源在`.local/diagnostics/coe_low3_result_review_8f49ab0_v0_1/`。
本轮仅离线来源/区间/描述统计核对及必要记录，无新图、业务修改、测试套件/GPU/服务器操作。
原Raw/DOCX/定义/Gate与所有历史BLOCKED保持；本批仍Pilot，NOT_ASSESSED/UNKNOWN及
长期容量UNKNOWN不升级，不与旧Engineering/Pilot拼为新Formal或宣布论文创新已成立。

## 7.215 低侧三点真实阶段A通过，绑定新receipt后仅9P1待显式执行（2026-10-19，历史；实际B见7.216）

- [x] 真实静态ZIP107,261 bytes、SHA256
  `b58485902497e3a871426e40304f309718fcbe913c1748bbcacebed7c25e1927`；23成员/22清单、
  安全路径/CRC及全部hash通过，manifest SHA256
  `cc79a04d054ca25edc6929193f208bb718b0aab8dc702c1ea05ae8d8b459a436`。
  实际delivery/executed.ps1与原交付逐字节一致；418项实际源码均匹配固定8f49ab0的
  Git/CRLF表示，8个exit均0。CPU stdout/JUnit均36 passed/零失败/错误/跳过，
  72.73s/72.732s；compile通过。本轮不重跑测试、模型或GPU。
- [x] 新A分别实测编排与目标解释器均Python3.11.16，isolated=1/no_site=1；不再依赖
  旧版本推断。receipt为STATIC_READY_FOR_REVIEW/error=null，execution=analysis=8f49ab0；
  原始receipt字节SHA256
  `f5c6473786552c5d246cc5e53df1448bfd63bddf4b2be5ca1eec7ef8f2b3ada6`。
  delivery/source_bytes/storage hash链成立，最终clean由已绑定launcher成功路径证明，
  不是独立现场查询。A未启动模型/CUDA/Nsight，未来256目标准入仍NOT_RUN。
- [x] 新鲜资源回执370,037,780,480 bytes空闲、四位置同一卷且可写，无查询错误，满足
  12GiB；历史总量仍null/UNKNOWN，不扫历史ACL或清理。B仍须重新核资源/源码/clean。
- [ ] 用户可执行固定P256/512/2048、3完整block、9新P1/profile；仅原已部署launcher的
  CollectReviewedInputPilot开关，绑定上述真实新A receipt哈希。不重跑A、不解压新包，
  不切换文档HEAD、不复用其他批次B。准确本地命令
  `.local/coe_low3_8f49ab01ca36_stage_b.ps1`仅做PS5.1解析，未在本地/服务器运行。
  首个256仍在预定槽位接受完整实物门；九次或硬失败即停，不重试/替补/追加。

审计及静态副本在`.local/diagnostics/coe_low3_target_a_8f49ab0_v0_1/`。下一项仅用户显式
B并回传`coe_input_8f49ab01ca36_pilot.zip`；估35～55min、fresh12GiB，完成仅STOP_FOR_REVIEW，
不授COE正式资格或负载规律结论。生产代码/定义/DOCX/Raw/Gate及暂停支线不变；
measurement_validity=NOT_ASSESSED、dropped_records_status=UNKNOWN及长期容量UNKNOWN保持。

## 7.214 固定P低侧三点交付协调通过，仅可执行新阶段A（2026-10-19，历史；真实A见7.215）

- [x] 原93,884-byte ZIP及SHA256
  `b7d0327332632a78039dfba8a98a29c5e616d2611d989bb43f1bef80d3ad12fb`核验；20成员/
  19清单、安全路径/CRC及全部hash通过。418源码路径逐项对应8f49ab0固定Git内容与
  明确CRLF表示；13个核心组件相对9c8b03e内容不变。bundle verify/head、真实前置A/B
  receipt/归档引用、三份完整input/mask矩阵和P三点九槽计划一致，不改旧四点BLOCKED。
- [x] 精确包内launcher匹配执行Git及SHA256
  `c8773e01c7207ec45e0474b193cfdcba040dfb83b6a10091666e2137fc586b1a`；默认A只部署/
  CPU/compile/解释器身份/新鲜空间，B另需显式Pilot开关和新A真实receipt哈希。
  PowerShell5.1语法通过，未运行真实launcher/模型/CUDA/Nsight。未来256资格仍未知。
- [x] 协调复跑本次36项全部通过，零失败/跳过，111.80s，本地Python3.12.7。真实文件链、
  隔离子进程及PS5.1分支运行，外部OS/设备/collector为明确CPU替身；不是目标3.11或
  GPU资格，不与原36项相加。最初审查命令在父临时目录建立前启动，2 passed/34项setup
  errors均为该目录FileNotFoundError；原XML保留。补齐审查目录后同一交付/代码完成上述
  复跑，未修交付文件、删除失败原件或重跑GPU。旧8/19项证据直接复用，未重复套件。
- [ ] 用户可将原ZIP复制到既定服务器transfer位置，使用已有准确整段命令执行新A。
  前置须fresh为9c8b03e且clean，否则停止不reset；执行目标仍8f49ab0，不部署文档HEAD。
  回传`coe_input_8f49ab01ca36_static.zip`；目标A/B仍NOT_RUN，真实新A审过前不启B。

只读协调审计、原包副本及CPU/JUnit在`.local/diagnostics/coe_low3_coordination_8f49ab0_v0_1/`；
准确A命令仍为`.local/coe_low3_8f49ab01ca36_stage_a.md`，不另发B或重打包。后续固定P
256/512/2048三完整block、9P1，估35～55min，fresh12GiB；任何质量硬失败或九次即停，
不重试/替补/扩展。历史总容量UNKNOWN，原Raw/DOCX/合同/Gate及暂停支线不变。
本轮仅本地审查/CPU与必要进度记录，不修改生产代码或新增科学样本。

## 7.213 固定P低侧三点Pilot：本地接线与唯一待审交付（2026-10-19，历史；协调结论见7.214）

用户批准本地实现/验证/打包；本窗口不操作服务器或模型/CUDA/Nsight。基于7.212，
O/P首token正R均保留，但O约+5.78/+6.77ms、P约+88.92/+83.51ms，幅度明显敏感。
本批只研究固定P参考程序，不宣称包装不敏感、无插桩迁移、纯Host阻塞或COE优越；
同操作普通GPU union仍作公平参照。原有限Formal/旧COE/Raw与Gate结论不变。

- [x] 独立合同`COE-INPUT-P-LOW3-PILOT/0.1`与profile/input身份/schema有限分派，
  不修改或解锁旧0.3四点BLOCKED计划。三完整block顺序256→512→2048、
  512→2048→256、2048→256→512，共9新P1/profile；只有P、batch1/output2/
  warmup3/repeat1。同模型/FP16/eager/SDPA/自然Host-readable，不新增或移动同步。
  [机器计划](../../configs/coe_input_low3_pilot_v0_1.json)固定全部槽位、质量与停止规则。
- [x] 复用256有限构造及input/mask全矩阵摘要，接通prepare→seal→采集argv边界→
  实际producer→Canonical→两token准入→原A/独立预算→完整三点block。端点signed
  ΔCOE及原R保持，低侧256→512同公式单列；无效分母null、无epsilon。新汇总分别
  保存COE/phase、COE/phase GPU union、候选预算占比、copy/操作墙钟、原sync交集、
  H/D、必要成员/提交位置；第二token累计必要后缀不当Decode新增量或独立样本。
  只消费已有资格和预算文件，不改变S/A/B、COE与迁移定义、不产生巨型domain。
- [x] 本地Python3.12.7最终36 passed/0 failed/0 skipped（100.50s）：
  `python -m pytest -q -p no:cacheprovider tests/test_coe_input_low3.py tests/test_coe_low3_delivery.py tests/test_coe_helper_identity.py::test_pinned_source_provenance_and_real_isolated_python --basetemp .local/low3_final_verified --junitxml=.local/low3_final_verified.xml`。
  覆盖9份真实producer结果/3完整block消费、256/512/2048实际prepare/seal边界、
  错身份/token/hash/版本、预算冲突、未知依赖/drain、失败未运行槽位、正负零/未定义、
  `-I`排除cwd/PYTHONPATH同名模块及真实PS5.1的默认A/显式B、旧回执/空间/源码门。
  外部设备/OS/collector为明确CPU替身，不是256目标准入或新GPU资格。
- [x] 未变旧合同定向8 passed/0 failed/0 skipped（5.95s）；helper19 passed/0 failed/
  0 skipped（1.41s，和主命令1项有重叠，不相加为科研证据）。发现旧helper测试仍从
  d6957de已删除的launcher内联片段抽代码，导致IndexError；最小修复为真实`-I -S`
  子进程直接加载现有身份模块、核两个固定源码与hash，保留行为变化/AST字段负例。
  原失败日志保留，不改生产helper。新A额外记录编排/目标解释器的实际版本；本地未
  执行3.11（py launcher无注册版本不等于全机无3.11），不把AST形状替身称实机3.11。
- [ ] 新A及9P1均**NOT_RUN**；首个256在预定槽位同时接受实物准入，无额外试跑。
  前置仅取7.212封存A/B的执行commit `9c8b03eae89f5f5e62e647cdeb15b9010ba0b0ee`，
  已审A receipt为`6e7bf50642ed45f3afc6f4e9ffcff01975aee478b3991303837fd85e890d7803`。
  新A必须fresh核现场HEAD/clean和新源码实字节；文档HEAD不是现场版本。真实新A
  回执审查后才另行提供B命令；旧A不替代、不解锁旧批次或七槽。

最高优先级为固定代码commit后的单一包本地审查及目标新A。组件兼容证明绑定原P
helper/runner、生产S/A/B、COE/预算与资源函数均未改。依据7.212的小process回执与ZIP
目录（非重分析），P单槽driver139.437～163.359s，9槽历史中位数外推约22.96min；
另留准备/hash/封包与256未知路径余量，计划35～55min、最终单ZIP约70～140MiB、
展开约1～2GiB（均估计，不是容量/可行性保证）。profile300s、每槽driver900s沿用；
后者9槽总和上界135min不含准备/封包，非全局超时。固定9槽或身份/效果映射/依赖/
terminal/容量硬失败即停，不重试/替补/追加/删点拼block。资源仍参与卷新鲜12GiB、
同卷不重复，长期50,000,000,000 bytes目标及历史总量UNKNOWN单列，不扫历史ACL或清理。
归档核验/批次审查前保留Raw、REP、SQLite、Canonical、输入身份及小型来源记录；
本轮不清理。1024/provider/hook、引擎、batch/输出轴保持暂停；用户DOCX不纳提交。

交付执行/分析固定`8f49ab01ca3606626bce0987e6129b4d0f9ae637`（已正常推送），唯一
`coe_low3_8f49ab01ca36_delivery.zip`为93884 bytes，SHA256
`b7d0327332632a78039dfba8a98a29c5e616d2611d989bb43f1bef80d3ad12fb`；清单SHA256
`36d61c4813da324b5668b8bb7e8a35d49f2f1eedc4d8a39b912cd82b2ed46b61`。
本地包审CRC/安全路径/20成员19清单全覆盖、418源码身份、三份完整输入/mask摘要、
封存A/B引用及13个未变组件Git hash对应通过，包内PowerShell解析通过；并非目标A/GPU
验收。launcher SHA256为`c8773e01c7207ec45e0474b193cfdcba040dfb83b6a10091666e2137fc586b1a`。
该补充是控制层交付记录，不以文档HEAD代替执行commit、不重包装；准确机器路径与
阶段A整段命令在忽略的`.local/coe_low3_8f49ab01ca36_stage_a.md`，包审小回执为
`.local/coe_low3_8f49ab01ca36_package_review.json`。A及9P1均NOT_RUN；B命令未提供。

## 7.212 512/2048×O/P八次完成并审查：方向保留，非比例幅度敏感（2026-10-19，历史；新三点准备见7.213）

- [x] 新B归档57,450,743 bytes，SHA256
  `afd428171bbe84e2ab53ea1b32a5f8099e750ca84c4a6b74f3fd8ee0c84d0f0e`；606成员/605项清单、
  CRC、安全路径及全部hash核验，manifest SHA256
  `0fe79cd8a514549a14971316f25cc6f41941d045706c94942f44c60e51f86ad8`。
  原A的19成员逐字节保留；launcher/delivery、415项实际源码与既定9c8b03e一致，
  根3个exit均0。8run/8profile、16条链、两个完整block，全部实际token为29184/6556。
  输入/mask/模型源码/PID及GPU身份、准备消费和成功窗前drain证据相符；非重采或新Q0。
- [x] 独立只读SQLite行及整数区间核对42,320次成员行引用、42,360次API行引用（含重复
  前缀，不是新增样本数）；328条候选来源hash、8条辅助合同Git内容绑定成立。
  16条COE、terminal/直接D2H、物理同步及24个原A/候选窗口相符；14,106个迁移片段
  只从submit扣除，去重/守恒/Request=Prefill+Decode均成立。未重跑完整analyzer，
  不把行与算术复核写成独立W oracle或完整物理B资格。
- [x] 首token预定R：block1 O/P为+5.781778/+88.917694ms，block2为
  +6.770716/+83.505612ms；R_P−R_O为+83.135916/+76.734895ms。
  O/P均正，削弱“正响应只在P存在”；但O的COE/GPU活动增长接近同比例，P明显偏离，
  不支持响应幅度包装不敏感。2048的COE占Prefill为47.713110%～51.498626%；
  这是候选完成暴露，不是原Device wait或纯Host阻塞率。第二token仍一block正、一block负。
- [x] 8个P−O的H均下降0.139468～0.651662ms；同长度/同block的必要kernel名称及
  grid/block/动态共享内存序列相同，但512首token的D下降91.014676/94.036969ms。
  其O操作未覆盖部分69.683762/79.696249ms，其中69.561224/79.501896ms的下一个
  必要活动所对应提交API已在空隙开始前返回。该分类只报告时间/提交事实，不判定驱动、
  调度、profiler或纯阻塞根因；H差不能解释全部时序变化。16条同操作普通GPU union仍等于COE。
- [ ] 后续建议固定P，将O/P作为独立敏感性证据，另审256/512/2048同期三点的3完整block、
  9P1有限计划，检查低侧与端点响应；256目标准入仍未验证。尚未批准/生成新包或服务器
  命令，不恢复1024/provider/引擎/输出轴/旧七槽。先审现有解释和准确预算，不为追大值改定义。

结果集中于[执行与结果审查](observation_preparation_engineering_v0_1.md#2026-10-19八次真实结果审查)。
只读审计、16条原值、24个预算、signed比较及空隙来源在
`.local/diagnostics/observation_input_result_review_9c8b03_v0_1/`；旧B命令已经执行，不再运行。
两block仅Engineering敏感性筛查，不与旧Pilot拼样本，不作显著性/稳定性/无插桩因果或方法优越主张。
本轮无业务修改、图表、GPU/服务器操作或测试套件重跑；仅离线核对及必要记录。
历史NOT_ASSESSED/UNKNOWN、长期总容量UNKNOWN、生产A/B/COE、用户DOCX/Raw、
Gate13限定PASS和Gate14 NOT_RUN均保持。当前协议仍Pre-Pilot，不授新Formal。

## 7.211 真实阶段A回执审查通过，绑定新receipt后仅8P1待用户显式执行（2026-10-19，历史；实际B见7.212）

- [x] 新静态ZIP104,163 bytes、SHA256 `32f6a44663a678953f2fa3380e189f4ee5d40d1a1761f6fca50ec87e1e17b653`；
  19成员/18项清单、安全路径/CRC及全部hash通过，manifest SHA256
  `b7718fba9e78603d200e6c6982ddc2f68914ecd4baa8695dd8db8c06cacc037a`。实际delivery/
  executed.ps1与原交付精确相同，execution=analysis=9c8b03e；415项实际源码均命中已审
  Git/CRLF表示。6个exit记录均0，原32项CPU stdout/JUnit一致：32 passed/零失败/跳过，
  99.81s/99.812s；compile通过。未重跑CPU或GPU，A未记录解释器版本，不借旧版本填入。
- [x] receipt为STATIC_READY_FOR_REVIEW/error=null；新receipt实字节SHA256
  `6e7bf50642ed45f3afc6f4e9ffcff01975aee478b3991303837fd85e890d7803`，delivery/storage/
  source_bytes绑定成立。最终clean由精确绑定launcher成功路径证明，不冒充独立现场查询。
  资源记录370,851,753,984 bytes空闲，满足12GiB；输出/TEMP/TMP/归档同卷、可写无错误。
  历史容量仍UNKNOWN，不清理或查ACL；B仍须fresh资源/源码/clean与模型身份门。
- [ ] 用户可显式执行本次固定8P1 Engineering：512/2048×O/P、两完整block，原计划及
  两token消费不变。B命令只启用原launcher的CollectReviewedEngineering，绑定上述真实
  receipt SHA，不换包、不fetch新文档HEAD、不重跑A。准确本地命令及PS5.1仅解析验证见
  `.local/observation_input_9c8b03eae89f_stage_b.ps1`；尚未执行，无模型/GPU结果。

只读审计和副本位于`.local/diagnostics/observation_input_target_a_9c8b03_v0_1/`。
下一项仅用户执行既定B并回传`observation_9c8b03eae89f_engineering.zip`，预计40～60min、
每driver900s、fresh12GiB；硬失败或8槽完成即停，不重试/替补/追加。成功也只STOP_FOR_REVIEW，
不授Formal/纯阻塞/论文结论。业务代码、用户DOCX、旧Raw/UNKNOWN/Gate与暂停支线保持。

## 7.210 512/2048×O/P交付协调复核通过，仅阶段A可显式执行（2026-10-19，历史；真实A审查见7.211）

- [x] 原137,870-byte ZIP、SHA256 `3df595a7e1f70e3a5a606e0dcc698d9bdc92633b753016f6e54f79eb6095ea07`、
  CRC/安全路径、17成员/16项清单及全部内容hash独立核验；bundle verify与head精确为
  9c8b03e，前置cedd706。415源码路径的Git blob/明确CRLF表示均匹配执行commit，
  两份完整input/mask身份匹配；可信前置A receipt与原静态ZIP逐字节相同。
- [x] 随包launcher匹配执行commit，默认分支只部署/CPU/compile/新鲜空间，不启动模型；
  8槽/两block、原O及P prepare函数AST相对前置未变。B另核真实新A receipt/hash/清单、
  fresh资源与显式开关，不从A或失败路径续采；不扫描旧YLQ/ACL，不自动清理。
- [x] 协调复跑新增两文件32 passed/0 failed/0 skipped，87.17s，本地Python3.12.7；
  实际PS5.1分支/文件链运行，OS、Git、外部进程及GPU为明确CPU替身。不是新增科学样本，
  不与主窗口同32项相加，未重复旧26/6项或运行模型/CUDA/Nsight。审计及JUnit见
  `.local/diagnostics/observation_input_coordination_9c8b03_v0_1/`；原ZIP读后hash不变。
- [ ] 用户可按已有精确命令在目标PowerShell5.1执行阶段A；现场cedd706/clean和参与卷
  各12GiB须fresh成立，否则停止，不reset/重试。回传新`observation_9c8b03eae89f_static.zip`。
  目标A/B仍NOT_RUN，真实A回执审查后才另启B，本轮不提供或授权B启动命令。

本轮只读代码/包审计、CPU验证与必要进度/handoff更新，无业务修改、新包或服务器操作。
用户DOCX原hash保持；旧Raw/UNKNOWN/BLOCKED、Gate13限定PASS/Gate14 NOT_RUN保持。
执行身份仍9c8b03e，provider/1024/引擎/输出轴/旧七槽继续暂停，等待目标新A原件。

## 7.209 实验优先：512/2048×O/P的8P1本地接线与待审交付（2026-10-19，历史；协调结论见7.210）

用户批准本地实现、CPU验证与单一待审包；未授权本窗口服务器/模型/CUDA/Nsight。
沿用[现有执行说明](observation_preparation_engineering_v0_1.md)新增0.2小节及
[固定8槽配置](../../configs/observation_input_sensitivity_v0_1.json)，不写开题/论文或新图。

- [x] 有限合同`OBSERVATION-PREPARATION-ENGINEERING/0.2`接通512/2048 O/P，
  旧0.1仍只支持32/512。复用原O helper及P prepare/ready函数体，不移动动态读取、
  NVTX、时间戳、CUDA或completion。新manifest/实际input observer绑定完整input/mask
  矩阵摘要；独立版本profile和采集前身份分派，不借旧seal或改旧Pilot/Formal角色。
- [x] prepare→seal→真实采集argv边界→producer→Canonical→两token准入→独立候选
  预算→消费者→完整四条件block已做CPU文件链验证（外部设备/进程明确替身）。
  缺drain/依赖/标记、错流/身份/token/版本/结果或预算hash均拒绝；原A及COE迁移预算
  独立保存，完整request闭合门不变，无Decode新豁免，不生成巨型domain。
- [x] block1为512O→512P→2048P→2048O，block2反向；8个新P1、8profile，
  batch1/输出2/warmup3/repeat1。首token各包装R与R_P−R_O用signed有理数，
  对应phase GPU union作为分母，零/无效时null而非epsilon；保留第二token全部原值、
  COE绝对量/phase比例、phase/operation union、H/D、copy及成员/提交位置。
  两block只筛查P特有解释/观测敏感性；混合、反向、操纵不足及零值不触发追加。
- [x] 本地Python3.12.7：新版本两文件最终32 passed/0 failed/0 skipped（81.18s），
  命令`python -m pytest -q -p no:cacheprovider tests/test_observation_input_sensitivity.py tests/test_observation_input_delivery.py --basetemp .local/obs2048_final2 --junitxml=.local/obs2048_final.xml`。
  旧合同定向26 passed/0 failed/0 skipped（56 deselected，20.33s），覆盖原排程、
  缓存、负差/R及旧角色门；实际PowerShell5.1解析/分派、空间不足/未知、源码冲突、
  错A回执、B失败传播均使用CPU边界。compileall/diff通过，不是目标GPU资格。
  早期测试括号/fixture目录/错误block构造及空选集记录保留，不将初稿当最终证据。
  追加旧producer实文件链6 passed/0 failed/0 skipped（8 deselected，35.53s）；曾有
  2项旧Pilot单独选择时失败，已定位为fixture在OS receipt替身之后延迟导入输入模块，
  捕获`read=lambda:{}`。提前导入真实文件模块后相同检查通过，不修改生产读取或形状门。
  命令`python -m pytest -q -p no:cacheprovider tests/test_observation_preparation.py::test_actual_producer_canonical_both_tokens tests/test_coe_input_pilot.py::test_real_producer_canonical_both_tokens_and_budget -k 'None or test_actual_producer' --basetemp .local/obs2048_legacy_files3 --junitxml=.local/obs2048_legacy_files.xml`。
- [ ] 新目标A及8P1真实执行均**NOT_RUN**。最近可信checkout仅为已审A的cedd706，
  其receipt SHA256为67f02b575aa4ce37cdcdc9c861e1149a1e960d5d33b730d9983a541ae7877fb0；
  不用本地HEAD或B控制层版本猜现场。新A必须fresh核checkout/clean、源码实字节、
  新执行版本和资源，若已偏离此前置则停止，不自动重置/试包。

最高优先级为协调审查**新的**单一交付及A静态原件，之后才另行显式B；默认仅部署/CPU/
空间，包与实际执行/分析commit精确绑定，构建后再记录完整ZIP/hash，避免自引用。
预计40～60min、临时12GiB（估计）；每槽driver硬超时900s，固定8槽或硬失败停止，
无重试/替补/追加；未知writer不强封包。新鲜输出/TEMP/归档卷空间同卷不重复核算；
历史总量null/UNKNOWN，长期50,000,000,000 bytes目标尚未证明，不扫ACL/旧目录/清理。
CUPTI provider/1024取证/引擎/输出轴及旧七槽暂停。Gate13限定PASS/Gate14 NOT_RUN、
原A/B/COE定义、Raw/历史BLOCKED/UNKNOWN及用户DOCX不变，本批不授新Formal。

交付固定执行/分析commit为`9c8b03eae89f5f5e62e647cdeb15b9010ba0b0ee`（已正常推送）。
唯一包`observation_input_9c8b03eae89f_delivery.zip`，137870 bytes，SHA256
`3df595a7e1f70e3a5a606e0dcc698d9bdc92633b753016f6e54f79eb6095ea07`；清单SHA256
`6e635ed4b323bf2eb83fa97146c79c015ef7eb293a3aa0d2bf42e8231176792c`。
本地独立包审：CRC、17成员/16清单项全覆盖、415源码路径的固定Git内容/明确CRLF表示、
两份完整输入矩阵摘要、原可信A绑定及包内PS解析通过；O原helper与P prepare体对
cedd706的同解释器AST比较均相同（跨版本helper身份仍用既有独立结构合同）。
包内launcher SHA256为`27fbb7d52b1bdda00cf3e0651196010a0cd3c9d03d55da38e96b5c78fc3ed448`。
本条为控制层交付记录，不改变已封包执行commit、不再打包；新A/B均未执行。
具体机器路径、阶段A整段命令及包审小回执在忽略的`.local/observation_input_9c8b03eae89f_*`
与本地handoff；不提供可直接运行B命令，待真实A回传审查。

## 7.208 科研优先的一页开题裁决：有条件适合，provider任务暂停（2026-10-19，历史；当前执行准备见7.209）

本轮按用户优先级只复用已有数据/文稿，在[现有决策稿0.4](pytorch_research_feasibility_decision_v0_1.md)
集中回答问题、假设、证据/竞争解释、公平用途和唯一判别设计；保留原0.3全文及其停止范围。
未修改业务/测量代码、用户DOCX或Raw，无新测试、图表、collector、包、服务器或预算。

- [x] 明确裁决：**有条件适合开题**，定位固定自然Host-readable政策下的负载响应与观测
  敏感性实证研究，不以COE新算法、纯Host阻塞、无插桩因果或完整曲线立项，不保证论文
  新颖性/录用。主假设：512→2048首token的正比例参照差R在同期O/P下均可复核，非P特有。
- [x] 证据复用：P四block Pilot的首tokenR+101.961～+107.954ms、第二token一正三负，
  Raw量/位置/分支；O/P32/512 Engineering的H全降、Q混合。角色不合并，不重新统计CSV
  或将旧Formal的事后COE派生升级。最主要竞争解释是P特有的Host到达/包装影响；共同
  profiler/运行状态仍未排除，单次Cpre或缺效果的1024不作为科学支持。
- [x] 分析用途限定为“增加的必要活动在copy前还是操作内执行”的来源化分解，API墙钟/
  phase GPU union不能单独回答；同操作GPU union在本批等于COE，完整依赖timeline也
  足够，不声称独有信息/准确性优势。工具完成不作为科研贡献成立条件。
- [ ] 唯一下一验证仅是**未获预算的设计候选**：同期512/2048×O/P，两完整四条件block、
  共8P1 Engineering敏感性筛查，两token全保留，主要比较各包装首tokenR与R_P−R_O。
  正方向且操纵/成员有效只削弱P特有解释；O下消失/反向否定包装稳健主张；混合、操纵
  不足/质量失败则不可判别并停止扩大，不补采。不能用两block保证精度或排除共同Nsight。

**最高优先级不再是执行7.207两日provider任务，该任务现暂停。** 1024/provider不是此
端点×包装检验的必要条件，不以通用适配修完作为科研前置。未来若另获授权，最多补新
版本O/2048身份/排程与相关文件链检查；现成O/P声明只含32/512，不能假称直接可运行。
未来8P1估30～45分钟/临时12GiB，不是本轮预算。本轮没有新增服务器执行或工程授权；
后续任何新增投入必须指出改变哪个研究判断。七槽不恢复，旧1024/B2/UNKNOWN/BLOCKED、
Gate13限定PASS/Gate14 NOT_RUN、生产A/B/COE定义及全部历史数据角色不变。

## 7.207 通用输入适配选路：推荐B的两日本地验证，不盲换后端（2026-10-19，历史；工程现暂停，科研优先见7.208）

本轮半天上限的本地选路审查完成，仅更新现有说明/进度/handoff；无业务修改、测试、
新provider、部署包、服务器或GPU。当前目标纠正为**通用输入适配**，不是1024专用豁免。
输入改变kernel/库分支本身合法；具体参数/效果/依赖缺证才阻断准入，不代表输入不支持。

- [x] 复用已封存中点/来源审计：同SDPA/runner/P下512有85次全部映射，1024有113次中
  84次缺效果；callchain/callee/count未知，未再查旧SQLite。固定Qwen2、CUDABlas/Fill
  源码及512/2048 kernel/grid分支事实，没有把缺口归因给某attention backend/库。
- [x] 定向核验PyTorch2.6官方dispatcher及sdpa_kernel：可指定MATH，但这不证明能修复
  缺效果，且现实际native backend仍UNKNOWN，固定MATH也不冻结全部GEMM路径。路线A
  当前无针对性证据，**不推荐/不试包**；将来若另选，是新执行栈，关键输入须同期全保留，
  不与旧结果拼曲线。half输入的math中间精度变化也不能静默忽略。
- [x] 唯一推荐B：保持当前执行栈的单进程/单subscriber限定provider。完整参数、设备
  时间线、窗口/clock/身份和COE必须同次；三类证据状态（有合法效果/已证零payload/未知）
  对所有长度统一。零payload仍需逻辑依赖/terminal投影证明，未知不填0；不重跑0/64。
- [ ] 下一项仅为[取证审查0.22](memset_parameter_feasibility_v0_1.md)的**两日封顶本地
  验证任务，尚未开始**：第1日Host DLL/真实SDK结构/线程栈/容量与记录来源；第2日同身份
  参数＋全时间线＋producer窗口→局部必要集合→COE的CPU文件链和反例。只有参数日志或
  缺任一必需来源即停止，不自动扩工具/资格步骤或延长为旧估计5～10日完整provider工程。

本地通过不等于真实模型覆盖或新provider资格；未来真实运行仍须双向全覆盖和同次完整
COE逐request门，1024最多作为预定反证用例，而非专用规则。A的接线约1～2日、B完整
工程约5～10日均只是代码审查估计，不是预算批准。本轮不开始两日实现或目标执行。
科研进度7.206/取证0.21保留为历史；旧B后验不牵引新任务，旧1024/B2 BLOCKED、已审
512/2048、Raw、UNKNOWN、生产A/B/COE及所有Gate/数据角色不变，用户DOCX不动。

## 7.206 1024同进程接回可行性审查：需限定新provider，尚不可执行（2026-10-19，历史；通用输入选路见7.207）

唯一目标转为未来同次1024真实调用缺证及COE路径。用户已接受0.2参数/效果结论；旧B
后验checked_a未执行/BLOCKED保持，**不再以补历史B状态为后续前置**。本轮仅本地源码/
固定SDK和接口审查及进度更新，没有业务代码、测试、微例、模型、服务器或新包。

- [x] 技术路线GO：已核验API22存在同进程Callback/Activity、Windows x64与统一活动时钟
  接口；推荐Python模型进程加载独立C ABI客户端，由唯一subscriber同时采参数及时间线。
  不跑micro.exe代替模型，不与Nsight/torch.profiler共用或拼接跨执行证据。
- [x] 明确当前执行/COE准入NO-GO的代码证据：Core单owner/共用栈、CALL_CAP64，84次缺
  效果调用已超容量；仅支持API/MEMSET。micro主动拒绝torch并自行创建流/分配，不能
  换argv就使用；0.2 reader固定两case/一显式流/非零handle，普通51→216微例资格不覆盖
  PyTorch、PTSZ或自然handle0。新模型须按TID实际父子栈、容量和双向覆盖重新核验。
- [x] 逐项接回清单及最短路线写入[取证审查0.21](memset_parameter_feasibility_v0_1.md)：
  复用参数快照/返回/driver域效果、P/Host-readable/drain政策与纯区间/FIFO/预算算法；
  新增kernel/Memcpy/sync、NVTX token窗口、资源与真实clock/身份输入；CUPTI provider/
  Canonical同形view和质量门不能复用Nsight-only来源声明。旧analyze_files、schema和设备
  表硬绑定Nsight，analyze_evidence_file也不授profile准入，不伪造SQLite或NSYS时钟。
- [x] 参数成功与COE成功分开：count0保留逻辑调用/API预算，须独立零关系图不变性及scope/
  terminal证明；zero_scope输出仅参数支持，候选提交覆盖门尚无此显式证据输入。count>0
  唯一效果才能继续、缺效果仍拒绝；新provider完整时间线及局部资格是另外的必需条件。
- [ ] 尚未实现：限定provider本地垂直切片、SDK结构解码/原NVTX捕获及新来源/时钟的文件链，
  然后定向provider依赖桥接与一个新1024/batch1/output2真实PyTorch覆盖。它是新provider
  工程，不是已完成小修；不制作count-only模型工具、可绕过缺口的入口或采集包。

成本审查估计5～10工程工作日量级，非预算批准/交付保证；建议首次本地封顶2日只检验
完整垂直切片，不能闭合即停，不滚动扩工具。未来若另获授权：定向桥接1进程/120s，
1024诊断1进程/300s、0Nsight profile，约15～30分钟/临时2GiB为未实测规划；当前不执行。
需要重编PyTorch、换栈、扩hook或混用Nsight/跨执行时即停止。原1024仍BLOCKED，旧参数
不能回填；本轮不恢复七槽/矩阵，COE公式、生产A/B、Raw、UNKNOWN、用户DOCX及Gate13
限定PASS/Gate14 NOT_RUN保持。优先级为先裁定该限定provider工程是否投入，不是重跑微例。

## 7.205 同封存微例0.2限定参数/效果复核PASS；原B完整验收仍BLOCKED（2026-10-19，历史；接回1024见7.206）

本轮仅离线原件核验和独立版本消费者；不部署、重采、编译native或运行模型/CUDA/Nsight。
原B ZIP/Raw/receipt及0.1审核器保持原字节，缺driver活动原因仍UNKNOWN，不改成解析bug。

- [x] 原50,225-byte ZIP、17成员/16清单、安全路径/CRC/全部hash复核通过；原0.1仍精确
  复现API_COVERAGE。A receipt/manifest/build/库/源码副本与已审真实A相同，micro进程
  PID12640、exit0/no timeout及Raw run/库hash/路径一致；这不是目标A树的后验复核。
- [x] 官方12.4.127/API22归档及四个头文件实字节复核：CallbackData区分domain，MEMSET4
  correlation对应driver调用；实际parent/ENTRY-EXIT是已审Core栈记录，不是时间邻近。
  runtime参数/API→真实driver parent/闭合顺序/context→driver域唯一效果，足以支持此微例
  的参数/效果判定，不恢复缺失driver API的起止/时长或其缺失原因。
- [x] 新独立`analysis/independent_cupti_memset_v0_2.py`输出schema0.2.0及窄域policy0.1.0。
  原0.1/driver/native/默认分派/生产S/A/B/COE不改。runtime API始终必需；缺driver API
  只接受普通216入口、明确父调用、每个缺行driver自身有唯一64-byte效果的桥。额外无
  效果driver和零字节下缺行driver不获该例外；已有API仍核身份/返回/interval，未归属
  目标driver API拒绝。无虚构API/时间/参数，driver未复制的默认0不当实参。
- [x] 旧30项及新41项定向回归共71 passed/0 failed/0 skipped，0.53s：
  `python -m pytest -q -ra -p no:cacheprovider tests/test_independent_cupti_memset.py tests/test_independent_cupti_memset_v0_2.py --basetemp=.local/cupti_v02_release --junitxml=.local/cupti_v02_release.xml --tb=short`。
  先37项缺模块红例，再4项桥接边界红例；预期来自手工fixture而非analyzer。真实文件链
  保留输入/拒绝覆盖。未跑A、完整Q0或GPU；本地Python3.12.7仅CPU验证。
- [x] 同Raw在新`.local/diagnostics/independent_cupti_b_offline_v0_2/derived/review.json`
  和`adjudication.json`独立复核：count0/64、返回0，call3/parent2序号3<4<5<6，driver corr4
  →唯一64bytes/value123/context1/stream13/device0效果，设备区间993ns；读回0x3a/0x7b。
  0.2仅参数/效果判PASS_LIMITED，不是0.1 attempt改判或新Formal。
- [ ] 完整B仍BLOCKED：原reader提前异常，历史后验checked_a确实NOT_RUN；原件缺目标
  A tree/源码/build/库的实际后验状态。native退出前库hash自检及前置副本可证相应局部
  事实，不能代替完整后验A检查，本地副本不能补写它曾在服务器执行。

当前窄域参数/效果问题无需新采；完整B真正缺后验目标状态证据，而不是再跑一次0/64。
缺driver API时间能力仍未取得，未知不填0。取证审查0.20和handoff同步；实际分析实现
commit为`d32a2533f6c52128ddfb1b4577b844e9be47b1c5`，提交后以同目录
`analysis_binding.json`绑定原ZIP/Raw、消费者实字节及三个派生结果hash，避免自引用。
不制作新包或服务器命令；PyTorch、旧1024/B2、
零长度依赖、Canonical/provider及A/COE未获资格，七槽不恢复。原Raw/UNKNOWN、用户DOCX、
Gate13限定PASS/Gate14 NOT_RUN保持。

## 7.204 独立CUPTI真实微例取得参数/效果，旧审核器因driver活动覆盖拒绝（2026-10-19，历史；独立0.2见7.205）

目标用户已执行一次tiny；本轮仅离线审查回传原件，没有重采、运行GPU或修改生产代码。
原attempt按cedd706审核器仍BLOCKED，不将已观察事实自动升级为限定微例PASS。

- [x] ZIP50,225 bytes、SHA256
  `d1dbf34c018230c82f7d2cce537e9fb5c783f2e99a00f44afed934e9812920ef`，manifest SHA256
  `c357b426a3edcc6be823b865bfdfa04174dbf94437454e948038b384dd18d46d`；17成员/16项清单，
  CRC/安全路径/全部hash通过。配置及包清单匹配已审662b94a控制包；随包A receipt、
  manifest/build/库/源码清单副本与真实A相同，不混用controller/native/reader身份。
- [x] 真实micro PID12640、exit0、无超时，Raw run/PID与执行一致；CUDA12040/API22及
  加载库路径/hash符合预定。订阅、缓冲、启用、flush、关闭等状态均成功，closed=true；
  已记录的overflow/drop/query error均0，三次drop查询成功，不扩大为所有潜在记录皆无损证明。
- [x] 两次runtime CBID51参数为count=0/64，返回均0，原ENTRY/EXIT及runtime API记录闭合。
  零字节case独立读回64字节保持0x3a；64-byte case读回全0x7b，存在MEMSET效果64bytes/
  value123/context1/stream13/device0，正时长993ns。前者不自动授零长度依赖豁免。
- [x] 精确复现`CUPTI_MICRO_API_COVERAGE`：Raw为6条runtime API活动、0条driver API活动；
  唯一被拒回调为driver call3/CBID216/cuMemsetD8Async/correlation4。其真实parent_call_id=2，
  ENTER/EXIT序号3<4<5<6，与64-byte runtime同PID/TID/context，效果的DRIVER correlation为4。
  不同domain数值相同本身不作为桥接证明。driver参数未复制，其默认count=0不是真实参数事实。
- [x] driver活动行为何缺失仍UNKNOWN；未发现足以归因的native过滤或解析证据。旧消费者
  强制每个driver回调另有API活动行，故在后续效果检查前停止；不能删除覆盖门或虚构该行。
  reader异常使控制层后验checked_a未执行，不能声称完整后验A树检查通过；原native自身
  库hash检查及既有封存副本核验与该缺项分别记录。
- [ ] 唯一下一步交主窗口：先依据固定12.4/API22和封存原件，评估“runtime API＋真实嵌套
  driver回调＋同driver域唯一效果”能否作为仅参数/效果的独立版本化证据路径。若可成立，
  仅增加明确新版本消费者/正反例并离线重判，不伪造driver API时长或宣称其interval已核验。
  driver API存在时仍严格校验；runtime API/父子关系/真实scope/效果/读回/关闭及丢失门缺失
  继续拒绝。保留旧读取/原BLOCKED，后验检查未运行的边界须单独说明。

审计`.local/diagnostics/independent_cupti_b_failure_review_v0_1/adjudication.json`及Raw/
process/receipt副本可复查。原包hash读后未变；无新测试或CUDA资格声明。本轮不制作包、
部署、重编、重跑A/B、模型、Nsight或恢复七槽。1024及PyTorch覆盖、Canonical/S/A/COE
仍未授资格；用户DOCX、旧Raw/UNKNOWN、Gate13限定PASS/Gate14 NOT_RUN保持。
取证说明0.19及本地handoff同步，长期历史容量UNKNOWN不变。

## 7.203 独立CUPTI B包协调审查通过，仅一次tiny待用户显式执行（2026-10-19，历史；实物失败审查见7.204）

只读审查控制包`662b94a33421550958d927cb819b88cb5c67b401`，精确复用真实A的
cedd706 native/reader及原checkout，不重跑A、不重编产物、无业务代码修改或目标操作。

- [x] B ZIP59,681 bytes、SHA256
  `ba5f332a887390427feadd7a2fb3d8fb96fa07063adebd78f58908e80d664e50`；8成员/7清单，
  CRC/安全路径/全部hash通过，两个控制文件绑定662b94a，两份helper绑定cedd706。
  随包A receipt/manifest与真实A原件逐字节相同，receipt SHA67f02b57…及build、EXE、
  runtime、CUPTI、Python版本/路径和GPU UUID均与已审A一致，没有混用控制/native身份。
- [x] 真实入口检查确认：严格复核原A全清单、当前checkout/clean/源码及库；在真实资源
  门后仅调用一次micro，使用完整UUID/本地ordinal0/PCI_BUS_ID；原native未加UUID查询，
  不声称其独立测了UUID。timeout120s，环境冲突、缺效果、PID/加载路径、关闭/丢失或
  后验A字节冲突均非零；未知writer由原pack拒绝，不自动换工具/重试/封包。
- [x] 协调复跑新增边界22 passed/0 failed/0 skipped，6.24s，
  `.local/cupti_b_coordination_check.xml`。A/Git/GPU明确使用CPU替身，未运行native；
  不与主窗口同22项相加。实际随包-I缺显式开关拒绝且包未变，两个PS入口经真实PS5.1解析。
- [x] 仅B控制包/命令获协调通过：用户可在目标Windows PowerShell5.1显式执行本次
  0/64-byte一次微例，硬120秒（校验/封包另计），0模型/0Nsight、新鲜2GiB。准确命令
  位于忽略的`.local/independent_cupti_662b94a33421_stage_b.ps1`及B交付说明。
- [ ] 目标B的加载/订阅/参数/效果仍NOT_RUN，成功终态仅PENDING_REVIEW；收到新原件
  才审限定微例，不预授PyTorch、1024、零字节依赖、provider或A/COE资格。

审计`.local/diagnostics/independent_cupti_b_coordination_review_v0_1/audit.json`及随包原件、
缺开关stderr可复查；回传一个新B ZIP，不覆盖旧A。取证说明0.18及handoff同步。
旧Raw/BLOCKED/UNKNOWN、用户DOCX、已审端点及Gate13限定PASS/Gate14 NOT_RUN不变；
无服务器、GPU、模型操作，不恢复七槽或多点采集。

## 7.202 独立CUPTI微例B入口本地准备，复用真实A产物（2026-10-19，历史；协调复核见7.203）

用户授权仅本地入口/CPU与待审命令，未操作服务器或运行CUDA、GPU、模型、Nsight。
真实A限定PASS复用，不重跑A/74项CPU、不重编native或修改既有独立审核器。

- [x] 新独立B控制入口与显式PS5.1 launcher，不向旧A加开关；native/审核器精确复用
  `cedd70610588d4d5691c5a86cbcb923ef8ea6433`，目标checkout不切换。控制commit单独记录，
  实现提交后再固定包/hash，后续文档HEAD不得替代native或分析身份。
- [x] 强绑定已审A receipt SHA256 `67f02b575aa4ce37cdcdc9c861e1149a1e960d5d33b730d9983a541ae7877fb0`、
  原artifact_manifest、build/micro.exe、runtime/CUPTI及source_bytes，执行前后复核未变。
  A原receipt/B_authorized=false不改；新的显式用户授权只由独立B入口消费，不升级旧数据。
- [x] 新目录/一次tiny、0/64-byte、硬120秒、零模型/零Nsight；固定完整已审GPU UUID为
  子进程CUDA_VISIBLE_DEVICES，保留CUDA_DEVICE_ORDER和本地序号0的选择声明。没有向native
  添加UUID查询，也不声称它独立查询了物理UUID。新鲜参与卷2GiB门/可写检查复用已审
  资源函数，不遍历历史YLQ或ACL，历史总量null/UNKNOWN、长期<50e9目标保留。
- [x] 参数/返回/资源及效果桥、独立读回、drop/flush/关闭均由既有native和审核器保存；
  新增实际argv/环境选择、PID/exit/超时与Raw来源交叉绑定。审核/进程失败返回非零，
  保留BLOCKED；未知writer拒绝封包，零重试/清理/恢复七槽，不裸跑EXE。
- [x] 仅新增执行边界定向`python -m pytest -q -ra -p no:cacheprovider tests/test_independent_cupti_b.py --basetemp=.local/cupti_b_release --junitxml=.local/cupti_b_release.xml --tb=short`：
  **22 passed / 0 failed / 0 skipped，7.46s**。含真实PS5.1显式参数/-I、真实隔离
  bootstrap→资源→native之前停止，以及回执/Raw/既有reader/封包链。A/Git和GPU进程用
  明确CPU替身；GPU替身记录只作文件链验证，不能冒充目标参数/效果通过。
  前16项缺入口的红例、嵌套support替身未贯通导致的3项中间失败保留，未放宽生产门。
- [x] 控制版本`662b94a33421550958d927cb819b88cb5c67b401`；唯一小包
  `independent_cupti_b_662b94a33421_delivery.zip`，59,681 bytes，SHA256
  `ba5f332a887390427feadd7a2fb3d8fb96fa07063adebd78f58908e80d664e50`，manifest SHA256
  `3162dbf70ea0ec422aac67b58af3dc6e282b9291e6275ba6e7f4d27467cde23b`。8成员/7项清单及
  全hash/CRC、真实A receipt/build/runtime/CUPTI与精确helper字节核验通过；没有EXE/DLL/
  SDK或执行bundle。实际随包`python -I`缺显式B开关时拒绝，且包文件不变。审计
  `.local/diagnostics/independent_cupti_b_delivery_v0_1/review.json`；完整待审命令与机器
  路径在忽略的`.local/INDEPENDENT_CUPTI_B_DELIVERY.md`，未执行。
- [ ] B控制包/命令待协调审查。用户以后显式执行并回传后，才审一个新微例；当前B实际
  加载、订阅、参数/设备效果均NOT_RUN，不能把CPU替身或入口完成记为微例PASS。

新入口成功最多到`MICRO_EVIDENCE_COMPLETE_PENDING_REVIEW`，不是科学资格自动PASS。
微例通过也不授PyTorch内部覆盖、1024修复、零字节依赖豁免或Canonical/S/A/COE资格；
旧1024/B2、历史BLOCKED/UNKNOWN、Raw/用户DOCX、Gate13限定PASS/Gate14 NOT_RUN不改。
最高优先级仅协调审查B边界/命令；微例硬120秒，校验/封包另计，估数分钟、临时2GiB，
小型回传预计低于10MiB但非目标实测。取证说明0.17及本地handoff同步，无新模型预算。

## 7.201 独立CUPTI目标阶段A原件审查通过，GPU微例B尚未准备/运行（2026-10-18，历史；B准备见7.202）

真实静态ZIP17,311,337 bytes，SHA256
`71ff920f60e1fd27ec09f7f781c1f4c716e621019e11256c8479447d004decbf`，manifest SHA256
`696858267face79a889e49eda92e23189d0126db6ed2a1fafecf013107c88880`。本轮只读审查，
不重跑CPU、构建或GPU，不修改业务代码/测量合同；执行=分析cedd706不变。

- [x] 944成员/943项清单、CRC/安全路径及全部hash通过；交付配置/包清单与原包一致，
  13源码表示、118 SDK/377 CUPTI成员匹配。receipt为STATIC_READY_FOR_REVIEW/error=null，
  14条process记录均EXITED/exit0/无超时；checkout及模块来源绑定cedd706/正确仓库。
- [x] 目标Python3.11.16前置门、MSVC14.38/SDK10.0.20348实际编译链接通过；三个EXE
  bytes/hash与build.json一致，imports只有系统库，无静态CUDA/CUPTI导入。PE检查17项
  CUPTI/9项CUDART导出成立；runtime PE版本6.14.11.12040，CUPTI候选库hash匹配SDK。
- [x] 原CPU stdout及JUnit一致：74 passed/0 failed/0 skipped，stdout12.34s/JUnit12.304s。
  只运行Host harness；micro_invoked=false、stage_a_cuda_programs_executed=0。
  原静态检查已通过，不因后续B控制入口新增而无理由重复A/构建/74项测试。
- [x] 空间观察373,384,695,808 bytes，满足2GiB；历史总量仍UNKNOWN，无清理/ACL追索。
- [ ] 下一步交主窗口准备绑定真实A receipt、全部产物及已审micro二进制的窄域B入口，
  不改/重编native、模型或分析语义。一个新tiny进程，0/64-byte两case，硬120秒，
  独立运行、0 Nsight profile/0模型，显式设备UUID绑定及新鲜空间检查，失败即停。
  B应保存实际argv/环境选择/退出、加载及关闭/丢失状态、独立读回和参数—设备效果关联，
  并运行已有独立审核器；未知writer拒绝封包。不提供裸exe命令、无界启动或自动续跑。
- [ ] 当前A-only包没有B开关，本轮没有制作B代码/包/命令或授权目标执行。
  GPU加载/订阅/效果、PyTorch覆盖、1024及Canonical/S/A/COE仍未获资格。

新A外部receipt SHA256
`67f02b575aa4ce37cdcdc9c861e1149a1e960d5d33b730d9983a541ae7877fb0`；已审micro.exe
335,872 bytes，SHA256`b735bd1ee7484d6df3d52db5d5ccc4808ab63fd5c10fb90a5064e9aae5b4495b`。
准确runtime/CUPTI/build/receipt摘要与机器路径见本地
`.local/diagnostics/independent_cupti_target_a_review_v0_1/adjudication.json`，
process原argv索引同目录processes.json。取证审查0.16及handoff同步；目标A判PASS仅限
Engineering构建/CPU，不升级Q0、微例或旧失败。Raw、用户DOCX、UNKNOWN/NOT_ASSESSED、
Gate13限定PASS/Gate14 NOT_RUN、旧七槽和多点暂停保持。

## 7.200 独立CUPTI修复包协调复核通过，仅可进入目标A（2026-10-18，历史；真实A见7.201）

本轮只读复核新cedd706交付及隔离入口，无业务代码/测量合同修改。执行=分析仍为
`cedd70610588d4d5691c5a86cbcb923ef8ea6433`，目标前置9c78e355bb43/clean不变。

- [x] ZIP15,978,375 bytes、SHA256
  `0c1bb777261affe498a8a4944938796c301eebac29d41344b4af9d7c1d51c892`匹配。
  13成员/12清单、13源码路径、118 SDK/377 CUPTI成员及全部CRC/路径/hash、bundle verify通过；
  bootstrap/support/launcher绑定实际commit源码表示，原包及文件集合保持不变。
- [x] 独立协调复核实际包文件，真实`python -I`、干净本地Git fixture及真实resources，
  不改sys.path、不用PYTHONPATH、不mock存储，使用实际2GiB空间门。成功绑定仅本仓库资源
  文件并exit0；错误parent、混合namespace、篡改源码和错误commit四项均非零/明确拒绝。
  这是5个本地依赖复核情形，不与主窗口74项CPU相加，不冒充目标Python3.11/构建/GPU。
- [x] 已核现有入口只允许阶段A，构建micro但不执行；CPU只运行Host harness/PE检查，
  无B开关、无自动提权或Nsight启动。本轮不重复未改native及原74项测试。
- [ ] 新目标A的Python3.11.16/MSVC14.38/SDK10.0.20348构建、库PE与74项CPU仍NOT_RUN。
  协调仅同意用户显式运行本次A；目标空间/身份/编译失败即停，保留新回执，不承诺必过。
- [ ] B实际CUPTI加载/订阅/参数/设备效果仍NOT_RUN，未提供命令或授权。新A原件审查
  后才可另审无模型tiny；本地通过不授1024、Canonical/provider/S/A/COE资格。

准确机器路径及A整段命令只存忽略的`.local/INDEPENDENT_CUPTI_A_DELIVERY.md`与
`.local/independent_cupti_cedd706_stage_a.ps1`；回传新A静态ZIP。旧f1ba8fb、9c78来源包及
失败现场不执行/覆盖，旧七槽/多点不恢复。审计
`.local/diagnostics/independent_cupti_repair_coordination_v0_1/{audit.json,replay.py}`及stdout/
stderr可复查；取证稿0.15及handoff同步。服务器尚未操作，原Raw/UNKNOWN/用户DOCX、
512/2048结果、原A/B/COE及Gate13限定PASS不变，Gate14 NOT_RUN。

## 7.199 独立CUPTI隔离bootstrap最小修复：绑定已验证checkout模块来源（2026-10-18，历史；协调复核见7.200）

本轮仅本地Engineering启动链修复，承接7.198；没有服务器、模型、CUDA/CUPTI加载或Nsight
运行。原f1ba8fb ZIP和协调拒绝原件保持，不能用新本地通过改写旧BLOCKED或授目标资格。

- [x] 用原随包文件、真实`python -I`再次复现`ModuleNotFoundError`；原因是support资源函数
  需要仓库模块，而原bootstrap没有建立已验证checkout的模块绑定。新增隔离回归先7项失败，
  缺陷/失败记录保存在`.local/cupti_import_red.xml`，不是目标3.11运行证据。
- [x] 保留`-I`。在部署、commit/clean及源码实字节审核后，显式建立仅指向该checkout的
  `scripts` namespace和`coe_startup_storage`文件导入；再次核commit及该依赖源码表示。
  不改`sys.path`、不使用PYTHONPATH、不执行未入索引的`__init__.py`，已加载第三方、旧
  checkout、混合namespace或错子模块来源明确拒绝。新`checkout_imports.json`记录执行
  commit、实际模块路径及源码bytes/SHA256，随新A回执/清单归档。
- [x] 新增真实隔离子进程：随包bootstrap/support→临时真实Git checkout→真实空间函数，
  包含错误commit、源码hash、第三方/旧/混合namespace和错误leaf反例；另经实际stage_a
  走到资源后下一文件门，缺runtime保留BLOCKED、非零返回及完整封包。仅部署/构建等外部
  边界替身，资源函数不再mock。普通pytest自身的第三方namespace污染由fixture明确隔离，
  没有放宽生产拒绝条件；随包文件无pycache或其他新增字节。
- [x] 定向命令：`python -m pytest -q -ra -p no:cacheprovider tests/test_independent_cupti_memset.py tests/test_independent_cupti_native.py tests/test_independent_cupti_delivery.py --basetemp=.local/cupti_import_release --junitxml=.local/cupti_import_release.xml --tb=short`，
  **74 passed / 0 failed / 0 skipped，16.47s**。通过显式CPU配置和已核hash的build.json复用
  未改native编译产物，只运行Host harness、PE字节检查及CPU文件链；不重建未变GPU程序。
  本地Python3.12.7不冒充目标3.11.16；目标A真实构建/CPU仍NOT_RUN。
- [x] 新执行=分析`cedd70610588d4d5691c5a86cbcb923ef8ea6433`，前置仍为已审9c78e355bb43。
  唯一新包`independent_cupti_cedd706_delivery.zip`，15,978,375 bytes，SHA256
  `0c1bb777261affe498a8a4944938796c301eebac29d41344b4af9d7c1d51c892`，manifest SHA256
  `cb93f55456a563b28fc40b394e5018e92cec7ae04080f75a559b3f9e1a5cee15`。13成员/12清单、
  13源码、118 SDK/377 CUPTI成员及全部hash/CRC/路径、bundle核验通过；实际从ZIP取两份
  bootstrap字节，在真实-I/干净临时Git checkout上调用未mock的空间函数exit0，包未改动。
  此为本地导入/资源演练，不是目标checkout部署或目标Python通过；审计
  `.local/diagnostics/independent_cupti_import_fix_v0_1/review.json`。后续文档HEAD不替代
  cedd706执行身份。原包永久保留历史，不试跑/解锁原入口。
- [ ] 新包仍待协调审查，目标A/B NOT_RUN，不因本地修复直接安排服务器或GPU执行。

最高优先级仅新A交付审查；本轮不安排服务器执行，无B命令或采集授权。仍估A 2～5分钟、
临时2GiB，历史总量UNKNOWN/长期<50e9目标不变。取证说明增补0.14及本地handoff同步。
未改参数/效果审核器、native逻辑、生产A/B/COE或冻结合同；旧1024/B2 BLOCKED、Gate13
限定PASS/Gate14 NOT_RUN、Raw/UNKNOWN/NOT_ASSESSED及用户DOCX/大型原件保持。

## 7.198 独立CUPTI交付协调审查：隔离入口缺checkout导入绑定，A执行暂不通过（2026-10-18，历史；修复见7.199）

仅审查已发布f1ba8fb阶段A包，未修改业务代码、未执行服务器或GPU。发现一个本地可复现
阻塞：launcher以`python -I`运行随包bootstrap；bootstrap未在调用`startup_resources`
前将已核验checkout接入模块解析，support的`resources`却要导入
`scripts.coe_startup_storage`。本地真实隔离子进程/随包原文件复现ModuleNotFoundError，
失败发生在空间检查，早于SDK构建与CPU。目标3.11未运行；不能依赖偶然安装的同名包。

- [x] 包15968398 bytes及所给SHA256一致；13成员/12项清单、13源码表示、118 SDK/
  377 CUPTI成员、全部hash/CRC/安全路径核对通过；bundle verify及PS入口解析通过。
- [x] 未改随包bootstrap/support的`-I`复现exit1；只在外部诊断脚本加入已审本地checkout
  路径后，相同真实空间函数exit0，模块来源指向本仓库。未运行模型/vendor库或profile，
  外部诊断边界改动不是已实施生产修复，也不证明目标版本运行通过。
- [x] 找到测试覆盖缺口：已有A文件链测试替换`startup_resources`，随包support测试仅
  导入support，不调用真实资源依赖；原65项通过不能替代此启动链检查，未无意义重跑65项。
- [ ] 下一步交主窗口最小修复：保持`-I`，在checkout/源码身份验证后绑定真实模块来源，
  防止从旧checkout或第三方同名scripts解析；补实际随包bootstrap→真实resources导入
  路径及错误模块来源反例，OS/编译/Git边界替身须明确。不可仅取消隔离、改PYTHONPATH、
  屏蔽ModuleNotFoundError或将空间检查再替换掉。
- [ ] 修复后重新固定execution commit/源码/包hash，并重审A；当前f1ba8fb包暂不执行，
  不在服务器删除/覆盖旧现场。当前没有B命令/授权；目标A/B仍NOT_RUN。

原f1ba8fb包保持不可变，0.12历史实现记录不重写为测试失败。审查原件/隔离stdout/stderr
索引：`.local/diagnostics/independent_cupti_coordination_review_v0_1/package_audit.json`、
`without_checkout.stderr`、`verified_checkout_path_only.stdout`。取证稿0.13及handoff同步。
此次只新增交付启动链阻塞，不改变参数语义/原S/A/B/COE、旧1024 BLOCKED或Gate13限定PASS；
用户DOCX、Raw/UNKNOWN及长期容量政策不变，Gate14 NOT_RUN，未生成新包。

## 7.197 独立CUPTI微例本地实现与A-only交付（2026-10-18，历史；当前协调审查见7.198）

用户批准0.11范围：仅无模型0/64-byte窄域客户端、本地CPU/真实头文件编译链接和阶段A包。
不运行服务器、GPU、Nsight或模型，不恢复旧七槽/多点；旧定义、角色、Raw及历史判定不变。

- [x] `scripts/native_cupti_memset`独立API22客户端：ENTRY参数复制、EXIT原返回，普通/PTSZ
  明确分开（微例资格只含普通），保留PID/TID/context/native stream及domain/correlation。
  driver桥由动态调用栈与同domain API activity建立，MEMSET按driver ID，不按邻近时间猜配。
- [x] 有界Host缓冲/记录槽及flush、drop、overflow、关闭状态；缺参数、非零缺效果、
  subscriber冲突、重入/跨线程/歧义均拒绝。固定0/64-byte独立读回，零字节不授顺序豁免。
- [x] 独立版本化审核器和native writer→文件消费；Host与目标源分开，库实字节及外部run
  绑定不匹配拒绝。原S/A/B/COE、registry及旧数据入口无修改，不靠参数齐全自动授准入。
- [x] A-only默认入口：只部署、SDK/源码/库PE/导出检查、构建链接和CPU；无采集开关。
  前置绑定已审9c78e355bb43回执，不再假定4da800d。源码允许的LF/CRLF表示由commit预定，
  记录实际字节，不用实际hash替换期望。失败返回非零、保留新receipt/未覆盖旧现场。
- [x] 本地定向65 passed/0 failed/0 skipped，9.25s，`.local/cupti_release_verified.xml`；包含真实
  MSVC/匹配SDK编译链接及Host替身、PE导出、PS5.1实际分派、身份/失败传播。GPU微例未运行，
  Host EXE没有加载vendor库。Python3.12.7/MSVC14.44/SDK10.0.26100不同于目标3.11.16/
  MSVC14.38/SDK10.0.20348；不称目标构建/GPU验证。不重跑旧110项或完整Q0。
- [x] 最终A-only包绑定执行/分析`f1ba8fb1edbac3c4b5f96295838c088ae2f3c210`，前置
  `9c78e355bb43a8696f7eccb44c48d8448f366d09`。ZIP为
  `independent_cupti_f1ba8fb1edba_delivery.zip`，15,968,398 bytes，SHA256
  `a8952447b034715efa3657cf339676e2cfcebf781d026c260d569057e064934b`；
  13成员/12清单、13源码路径、118 SDK/377 CUPTI成员及全部hash/CRC、bundle verify通过。
  实际随包bootstrap导入/清单/源码审核无新增文件。准确机器路径及A整段命令保存在忽略的
  `.local/INDEPENDENT_CUPTI_A_DELIVERY.md`，不提供B命令；后续文档HEAD不替代执行身份。
  本地首次包装在Git源码清单预检查发现不存在的tests/__init__.py，尚无ZIP/bundle发布；
  三个新测试文件不导入tests共享helper，移除该错误依赖项，不新增全局测试包或放宽源码门。
  后续真实bootstrap检查复现随包support导入pycache污染，已修正且不忽略多余文件；
  成功查询的context/stream数值0不再被误判缺失。草稿b306018未发布、不可执行。
- [ ] 目标A构建/CPU/库及B实际订阅、参数/设备效果均NOT_RUN；新A真实原件审查后才可另审
  一个0/64-byte微例，不能由本地CPU或包完整性自动启动。
- [ ] 本版并非完整Canonical provider；微例成功不能直接接回S/A/COE，不拼接旧Nsight实例。
  完整同次模型scope/kernel/Memcpy/ownership/drain/依赖/terminal的返回路径仍未实现/授资格；
  若需要扩大provider，先作独立投入决定，不将窄域工具滚动扩建。旧1024仍BLOCKED。

实现与解释集中[取证审查0.12](memset_parameter_feasibility_v0_1.md#2026-10-18增补独立cupti微例本地实现-012当前目标未运行)。
当前最高优先级仅为交审新A包；估2～5分钟、临时2GiB，不初始化CUDA；历史占用仍UNKNOWN，
长期<50e9目标不以不可读部分为零。未来B仅1 tiny进程/120s/0 Nsight profile，非本轮授权。
本地compile/导入、diff/测量代码未变与DOCX保全检查通过。Gate13限定PASS/Gate14 NOT_RUN、
Formal、旧BLOCKED/UNKNOWN/NOT_ASSESSED和256准备保持，不新增GPU/模型预算。

## 7.196 1024后续顺序：先评审独立CUPTI窄域微例实现，模型及多点不启动（2026-10-18，历史方案）

用户询问下一项具体工作。本轮只读复核已有匹配SDK/CPU原型、Windows入口事实及
单subscriber限制，计划收敛到取证审查0.11；没有实现、测试重跑、新包或服务器操作。
旧Nsight来源包仍暂停，不凭管理员权限或综合文档绕过真实能力门。

- [x] 固定CUDA12.4.127/API22的参数、callback/activity关联与单subscriber证据复核；
  runtime普通/ptsz的memset callback ID为51/235，参数结构独立。SDK关键hash保持。
  旧原型只有CPU复制/关联验证，不包含真实订阅、缓冲/flush或目标PyTorch覆盖。
- [ ] 推荐下一项仅为独立CUPTI窄域native微例的本地最小实现/CPU审查；先支持参数、
  返回、identity、唯一关联及失效停止，不开发通用collector。当前为方案，尚未实施。
- [ ] 本地验证后另审A构建/CPU；再显式审查一个无模型0/64-byte微例，硬120秒。
  微例与Nsight独立，失败停在模型前，不自动换版本/重试。目标版本/加载/订阅仍NOT_RUN。
- [ ] 微例通过后才另审一个新1024真实参数覆盖诊断；不恢复旧七槽，不假定旧84次count。
  最多两个目标进程是分阶段上限，不是本轮执行授权；未来总体估15分钟/2GiB，尚未实测。
- [ ] 新参数之后另审同次Raw→S→A/COE的完整返回路径；独立CUPTI参数不能与旧Nsight
  时间线拼接，不能自动授Canonical/provider资格。若需完整新provider，先审新增工程量
  和科研收益，不能让窄域取证自动扩大为测量基础设施重建。

阶段/计划调整：仍是Engineering可行性方案，非1024修复完成或新Q0/采集资格。
当前唯一建议进入上述本地最小实现审查，不再先追调用栈；真实count与效果才是拒绝缺证。
count0不取消逻辑依赖，非零缺效果仍拒绝；原S/A/B/COE、Raw、用户DOCX、旧BLOCKED及
UNKNOWN不变，512/2048已审端点保留，256准备及多点计划暂停。Gate13限定PASS保持，
Gate14 NOT_RUN。本轮没有业务代码或合同修改、无CPU/GPU新测试，不声称目标能力已证明。
复核索引：`.local/diagnostics/memset_parameter_feasibility_v0_1/feasibility_audit.json`、
匹配SDK headers/samples及7.195审计；新顺序/失败判据见取证审查0.11。

## 7.195 1024来源诊断A回执：权限及目标CLI选项双重阻塞，B未运行（2026-10-18，历史；下一项见7.196）

已审用户回传的真实静态ZIP：77,013 bytes，SHA256
`d4ceeae555ec0f5b146821aba40133e2d7df6e6cc61aaeff1cbed3dcd5d96b4b`。
25成员/24项清单、CRC、路径与全部哈希通过；359项源码符合封存表示，执行入口与原交付
字节一致。目标已checkout到`9c78e355bb43`，不再以旧4da800d作为下一入口的当前状态假设。

- [x] 真实`capability.json`：Windows=true、administrator=false；`--cudabacktrace`不在
  目标2026.2.1.210默认profile帮助中，其余四项必需选项存在。报错是两个门同时失败，
  不能只归因权限，也不能通过删除选项检查或改成普通周期采样直接授予逐调用来源能力。
- [x] bundle/fetch/checkout及NSys version/help均exit0；3.11.16前置门与源码核验已越过。
  空间检查成功，观察空闲373,423,542,272 bytes；长期总量仍UNKNOWN。
  capability在CPU/compile之前，故本次30项CPU、compile均NOT_RUN，不能复述为目标通过。
- [x] 本地已装Windows 2026.1.1与2025.6.1只做帮助及参数解析：普通帮助和backtrace
  分类帮助都不列该选项；`profile --cudabacktrace=all:0 --help`均exit1/unrecognised。
  没有application参数、模型或profile。这是其它版本反例，不冒充目标2026.2.1解析实测。
- [ ] 固定Windows目标可用的逐CUDA调用来源入口仍未闭合。最高优先级先做本地平台能力
  复核，再决定最小方案；不要求用户管理员原样重跑A，不清理/覆盖旧输出，不提供B命令。
  默认help缺项尚不等于目标解析器已测拒绝，也不证明所有Windows接口均不可行。

计划调整：7.193/7.194的综合文档接口依据未证明固定Windows CLI实际可用，当前路线的
接口级GO需暂停，不能凭既有CPU替身验证继续交付采集。原A回执保持BLOCKED；B、来源、
实际count/效果、S/A/COE资格均未获得。旧1024缺效果原因和旧hook零捕获仍UNKNOWN，
不据此认定1024不可修复；256及多点研究准备保留，旧七槽不恢复。
本轮仅只读封存审查/本地其它版本help解析及文档更新，无生产代码、服务器操作或新包；
不重跑已有回归。Raw、用户DOCX、Gate13限定PASS和既有定义不变，Gate14 NOT_RUN。
可复查索引：`.local/diagnostics/memset_callsite_stage_a_review_v0_1/adjudication.json`、
同目录`audit_receipt.py`与`local_cli_help.json`；详见取证审查0.10。

## 7.194 1024真实来源诊断：有限入口与只读消费实现完成（2026-10-18，历史交付；目标状态见7.195）

用户接受继续完成“同一规则覆盖不同长度”的目标；本轮落实7.193已选原生栈诊断的本地
实现与交付准备，不将1024假定零长度或跳过。最高优先级是审查新A真实回执，再由用户显式
决定一次B来源采集；1024实际count/设备效果及旧hook零捕获原因仍UNKNOWN。

- [x] 独立`MEMSET-CALLSITE-ENGINEERING/0.1`，固定1024/batch1/o2/P/w3/r1、一个模型
  进程/一个profile。复用原prepare/isolated seal/target入口/P helper；角色始终Engineering，
  不冒充Pilot或恢复七槽。P的Host读取/NVTX/完成函数体、原S/A/B/COE算法不改。
- [x] 独立collector固定`--sample=process-tree --sampling-frequency=200 --cudabacktrace=all:0`；
  不保留冲突的sample/ctxsw none，不用Linux Python栈。CLI duration240s，进程硬超时300s，
  外层900s，给结束/导出留余量，不提高原预算。旧采集/COE消费入口明确拒绝source-only角色。
- [x] 只读SQLite通过runtime.callchainId连接CUDA_CALLCHAINS.id，保留全部Prefill目标调用、
  实际ID/线程/模块/IP及有无效果组；复用栈ID合法，空栈、悬空、重复depth、仅工具帧与
  不可读模块不伪造来源。VM/global process命名空间保留；只读取目标调用涉及的栈行。
  模块文件hash是采后Raw所命名文件的身份，不冒充已证装载或callee入口。count仍null，
  参数/效果恢复及A/COE均NOT_ASSESSED；若新run无缺效果组则不可判别，不追认旧1024。
- [x] 默认A只部署/源码实字节/CPU/compile、新鲜12GiB空间和NSys help/version及实际管理员
  token核验，不加载模型/启动profile、不自动提权。B另需新A receipt SHA及显式接受采样风险；
  历史BugCheck 0x133未定因，低频/timeout不保证无系统风险。失败即停，不自动换hook/CUPTI。
- [x] 真实PS5.1分派、CPU producer→Canonical/共同trace锚点→来源报告、prepare→seal→consume
  →profile argv，以及实际控制器/清单/ZIP路径均覆盖；模型、设备、NSys和OS外部边界明确为
  CPU替身。已观察目标退出才允许封包；未知writer保留现场并拒绝封包，不清理或杀无关进程。
- [ ] 新A目标3.11.16/权限/选项事实、B实际栈覆盖及1024根因：均NOT_RUN。构建包由真实
  execution commit及封存4da800d静态回执绑定；A通过不自动授B或1024/四点资格。

验证：新增检查先见缺模块/入口、VM串配及超时余量红灯；本地相关回归242 passed/0 failed/
0 skipped（`.local/callsite_final_regression2.xml`）；最后入口30 passed/0 failed/0 skipped
（`.local/callsite_final30.xml`），覆盖重叠不相加。新完整prepare/seal/consume边界
另单项通过并包含在最后30项。仅Python/CRT等通用框架帧不能判来源已定位，新增负例通过。
回归中已修正测试替身导入污染，仅调整测试加载，不放宽门。
本地Python3.12.7；Python3.11语法检查不冒充目标3.11运行。compileall、PS5.1解析及diff检查
通过；不是新Q0/GPU验证。原始1024/BLOCKED、四block端点、256准备、Raw和用户DOCX均保持。
Gate13限定PASS、Gate14 NOT_RUN不改。本轮不操作服务器；旧三点/四点采集包继续暂停。

最终待审交付：执行/分析`9c78e355bb43a8696f7eccb44c48d8448f366d09`，服务器前置
`4da800d2e8d270fdc2e25e07ab3511a73066df46`且clean。唯一发布包
`memset_callsite_9c78e355bb43_delivery.zip`146,418 bytes，SHA256
`6a79cd0c12870e296c8d78a71be6299259f5d0e98c2422aa2e9d117c0b77a4f0`；
10成员/9项清单、359源码路径实字节、bundle verify及交付PS5.1解析通过。
机器路径/阶段A整段命令只保存在`.local/MEMSET_CALLSITE_DELIVERY.md`及同前缀stage_a.ps1。
3d1bafd内部草稿未发布、不可执行；本次只提供最终A，不提供B命令。新目标回执仍NOT_RUN。

## 7.193 1024来源定位优先：原生CUDA调用栈方案，独立CUPTI候选不否定（2026-10-18，当前）

> 本节保留方案时点；本地实现及真实待验证项见7.194，诊断尚未在目标机执行。

用户调整优先级：256准备保留，暂缓256/512/2048三点包；重新调查1024真实调用来源。
本轮仅本地接口/文档/SDK核对及必要CPU原型，没有服务器、GPU、新模型或新采集。

- [x] 分开三个结论：1024模型/profile/export已成功，拒绝因84个Prefill提交缺效果；
  效果为什么缺、旧记录器为什么零捕获尚UNKNOWN。直接复用既有Raw/Canonical/关联
  搜索，不重复旧correlation，不把旧普通共享入口失败等同1024不可修复。
- [x] 核验目标安装UserGuide及AnalysisGuide：原生CUDA API backtrace需CPU sampling，
  Windows CLI需管理员；`--python-backtrace=cuda`不是本Windows可用替代。
  官方runtime.callchainId→CUDA_CALLCHAINS.id及module/originalIP关系可用于逐实例来源
  定位，不是参数或效果证据；共享栈ID可复用，不按时间猜栈。目标实际捕获仍NOT_RUN。
- [x] 重评已存在的独立CUPTI/API22原型：有实参/返回/correlation接口依据，但未实现目标
  native订阅/缓冲/flush/模型覆盖；不与Nsight同时订阅，不借私有CUPTI或升级。旧hook失败
  不能否定这条候选，但其新运行也不能补旧实例，微例不代替模型覆盖。本轮不选为优先。
- [x] [现有取证审查0.8](memset_parameter_feasibility_v0_1.md#2026-10-18增补1024来源定位优先先用nsight原生cuda调用栈-08当前)
  固定唯一下一诊断：新1024、batch1/输出2/P/w3/r1的一次真实PyTorch来源采集，
  固定`--cudabacktrace=all:0`避免未实测API分组漏取，事后仅审查Prefill目标memset。
  最多1模型进程/1profile，估5～10分钟、profile300s/外层900s，临时12GiB，保留0.5～2GiB
  为估计。记录全部Prefill目标API、按真实ID连接帧并比较有/无效果组，不依赖旧84条ID。
  栈相同/不同均可报告；缺栈/只公共工具帧/缺module绑定不宣称定位，不再复现缺口则
  不可判别。固定单次或硬失败即停，不自动接CUPTI/hook/重采，不输出性能/新资格。
  周期采样固定200Hz，实际ctxsw随process-tree；复用旧来源argv框架而非执行其向量fixture。
  历史BugCheck 0x133仍未定因，低频/timeout不保证安全，未来B须单独显式接受新增profile风险。
- [x] 小型纯CPU内存SQLite原型验证ID连接、null/悬空、符号未解析、合法共享栈及重复depth
  行为；源码/输出在`.local/diagnostics/coe_1024_callsite_feasibility_v0_1/`。
  没有生产代码改动、目标DLL加载或新CUDA资格，不重跑全Q0或已有74项CPU。
- [ ] 目标build选项/权限与实际栈覆盖NOT_RUN。下一步仅准备独立Engineering诊断角色、
  薄argv分派和来源报告；先做相关CPU/静态审查，A真实回执通过后才能显式B。当前无新包、
  无服务器命令，预算/执行仍待用户审查。定位成功也不自动授予count、效果、COE或四点资格。

依据：已封存UserGuide SHA256`5b100930126f3a3a819f13dd8335efc0bc2cd7f8bf0207a7063d57acb4c33e7c`；
AnalysisGuide SHA256`bdcf574189e7eb687d4dc7c52bcebacae9c700c5a93a9e3aed8ff674960cbb11`；
API22 callback头文件和既有CPU原型。在线2026.2/12.4归档读取失败，未伪称直接核验；
PyTorch v2.6源码及官方分析页可读，未用新版本多subscriber功能推断目标能力。
参数/效果与source定位分开，未改变S/A/B/COE、Raw、旧BLOCKED/UNKNOWN/NOT_ASSESSED、
旧Formal或Gate13限定PASS/Gate14 NOT_RUN，用户DOCX/大型原件不纳入提交。

## 7.192 输入轴继续扩展：256有限接线完成，1024实例来源缺口保留（2026-10-18，历史准备）

> 256实现和验证不变；用户随后暂停三点采集包，当前优先级改为7.193的1024来源诊断。

本轮用户批准本地适配/定向CPU/1024来源诊断/方案准备，未批准服务器、GPU或新批次预算。
当前最高优先级：推进256独立准备及同期比较设计，不把1024缺证当整个研究停止；同时不
强行输出1024、不恢复旧七槽。原研究设计v7.1、Pre-Pilot协议v2.1、签署路线A及旧数据角色保持。

- [x] [有限输入合同](../../exposedpath/coe_input_pilot.py)新增0.3及矩阵身份0.3.0，支持未来
  256/512/1024/2048声明；旧0.1/0.2不放宽。256沿封存32token循环8次、全1 mask，
  实际文件字节/完整矩阵摘要/模型范围和角色严格检查；采集前分派增加精确0.3。
  原P helper/runner/completion、S/A/B、registry及COE/预算计算实现不变。
- [x] 256真实CPU文件链接通prepare→seal→采集argv边界、producer→Canonical→两token
  准入→候选预算→报告消费；外部模型/设备/collector均为明确替身。错字节/mask/角色/
  版本、缺drain/依赖/映射、token/结果hash冲突仍拒绝。四点完整block汇总保留signed
  及null分母；1024失败反例保留未运行槽位/原原因，不能删点补block。旧入口仍拒绝
  0.3 delivery schema，尚无可启动的新服务器入口，不把本地功能完成写成GPU资格。
- [x] 1024比较成功/失败调用来源及覆盖，复用7.191全部效果搜索结论，不重搜84个
  correlation。封存同批512 Prefill有85次该API均已映射；1024有29映射/84缺效果。
  所有callchain均null；runner/P helper/input adapter及软件内容相同，API名/主线程
  不能确定实际callee。既有历史PE也未绑定实例入口，普通共享hook零捕获保持。
  没有可验证的新解析修复或不同真实入口方案；1024模型成功、分析不可评估，不称输入
  不支持，不推断零字节/无提交，不制作仅微例有效的模型取证包。具体来源仍UNKNOWN。
- [x] [机器可读四点方案](../../configs/coe_input_extension_pilot_plan_v0_1.json)及
  [现有报告§12.8](coe_research_short_note_v0_1.md#128-继续输入轴256独立适配与1024来源对照2026-10-18当前)
  固定4位置平衡block/16P1/16profile、每点4次，旧数据不并入；估55～80分钟，临时12GiB，
  保留1.5～3GiB。四次不保证精度/显著性；全样本/两token、原A/候选预算、Q/T和Q/G、API/
  sync及活动位置等公平参照保留，零/负/非单调不是质量失败。1024闭合前四点交付BLOCKED。
- [x] 不让1024阻断所有准备：另建议同期256/512/2048、3完整block/9P1，估30～45分钟、
  临时12GiB、保留0.8～1.5GiB；仅检验低侧与端点，1024仍明列未解决。它须独立预算/
  有限合同，不是临场删点或恢复旧批次；本轮未接新采集入口、未打包、未提供服务器命令。
- [ ] 256实际GPU准入NOT_RUN；1024真实count/效果/调用覆盖及依赖闭包仍BLOCKED；
  完整四点同期研究未完成。制作包前须先确定独立矩阵/预算、真实commit/输入/源码绑定及
  对应launcher；四点还须闭合1024。只有新A实际回执审查通过才可显式B。只查新鲜空间，
  不扫历史YLQ/ACL、不自动清理；历史占用UNKNOWN及长期<50e9目标保留。

定向验证：先新增测试见16 failed/1 passed（缺0.3版本，`.local/input_extension_red.xml`）；
最小实现后初步17/0/0。补充严格prepared字节/角色/schema和固定预算验证后，最终命令
`python -m pytest -q -ra -p no:cacheprovider tests/test_coe_input_extension.py
tests/test_coe_input_midpoint.py tests/test_coe_input_pilot.py --basetemp=.local/input_extension_final
--junitxml=.local/input_extension_final.xml`：74 passed、0 failed、0 skipped，115.17s（10月17日
本地运行，10月18日继续收口），不与初步重叠数量相加。本地Python3.12.7；目标既有3.11.16，
新代码未做目标机验证。新增摘要有独立字面量答案，实际GPU/S资格仍复用旧证据，不重跑Q0。
来源对照回执`.local/diagnostics/coe_input_extension_v0_1/call_origin_review.json`，8个消费成员
按原清单核对；模型/输入身份事实与未知callee/参数分开。`python -m compileall -q exposedpath
analysis scripts/gate7_smoke_validation.py`、16槽/位置/相邻顺序与配置一致性、来源/新增链接及
`git diff --check`通过。内联代码审查未发现需修改测量语义的冲突；不是独立同行/GPU验证。

计划调整：用户明确继续输入轴，替代7.191“仅保留端点”的优先级；不否定该失败收口或消除
1024缺口。四点合同和256本地实现不是签署新Formal协议。旧A/B/候选角色、Gate13限定PASS、
Gate14 NOT_RUN、Raw、旧BLOCKED/UNKNOWN/NOT_ASSESSED及用户DOCX/大型原件均保持。

## 7.191 三点输入轴Pilot失败收口：1024 Prefill缺效果、零完整block（2026-10-17，历史收口）

> 失败结论不变；用户后来明确授权独立256适配与四点准备，当前优先级见7.192。

当前裁决：本批`BLOCKED`，1024合格COE/候选预算不可评估；这是已观察的提交效果证据缺口，
不是模型执行失败、OOM或已证实的parser遗漏。最高优先级是保留这一适用边界，并以7.189的
已闭合512/2048四block结果为现有研究依据；不恢复本批七槽，不重采、不重开hook或制作新包。

- [x] 消费协调审查`midpoint_failure_review_rjy6pdf4/review.json`及84行
  `missing_effect_instances.csv`；原ZIP、清单及实际消费成员绑定复核。CRC/全部文件hash及
  389项静态源码绑定复用协调审查；本轮独立核对15个消费成员hash、全部84个Raw/CSV/
  Canonical调用身份和核心字段、实际Prefill边界及目标correlation的三类效果表。
- [x] 执行/原分析`4da800d2e8d270fdc2e25e07ab3511a73066df46`，有限角色0.2不变。
  原批次1个512槽COMPLETE、1个1024槽BLOCKED、7槽NOT_RUN、0完整block；三个预定block
  均未完成。1024模型exit0、profile COMPLETE/exit0、export PASS；driver exit1、无超时，
  真实拒绝`OBS_PREP_BOTH_TOKEN_ADMISSION:['ENGINEERING_SCOPE_SUBMIT_MAPPING']`保留。
- [x] 84次`cudaMemsetAsync_v3020`均在request开始至首token完成的Prefill内，不是可隔离的
  Decode缺口。首条runtime row36193/correlation169869，PID30488/TID27172；Raw与Canonical
  一致，成功返回不构成零长度/无提交证明。KERNEL/MEMCPY/MEMSET的合法候选关联无命中，
  没有driver表或可用参数sidecar；现有材料不能补出count、实际效果和必要依赖闭包。
  不按邻近kernel、84次规律、源代码可能路径或最终token正确填补。零字节规则的实参/
  双向覆盖及闭包前提未满足，不适用；不更改submit分类或把缺效果记为零。
- [x] 本批512的两token候选交集2.649075/0.545149ms保留为单次Pilot记录，不是一个完整
  block，不替补旧重复、不并入7.189；1024不发布合格COE或推测预算，不作本批ΔQ/R。
  旧512/2048四block及原signed结果不变，但只支持其已审端点/阶段；不授1024适用性、
  中点响应、曲线形状或精确转折。
- [x] [现有短稿§12.7](coe_research_short_note_v0_1.md#127-三点pilot失败收口1024不可评估2026-10-17当前)
  与本地handoff同步。下一阶段三点曲线/中点比较暂不能成立：不得删去1024后拼曲线、
  借旧2048补本批block或以相同配置重采替代缺证。若未来重议该点，须先有能改变准入
  判断的独立实例证据；当前不安排该取证、GPU预算或实现支线。原计划/失败槽位均保留。
- [ ] 本批三完整block、中点比较和响应形状：未完成，因上述硬证据缺口停止；不是已完成
  或一般统计不显著。1024真实参数/设备效果仍未知，既未证明零payload，也未证明非零丢失。

原回传`coe_input_4da800d2e8d2_pilot.zip`11,285,611 bytes，SHA256
`8d4accd2c4d0077a1ca9bfd3f485f3afc137f4fd0e227a1e5f75542941859784`；180成员/179清单，
manifest SHA256`7fabac4029307c935fada06d8d1f26d28c3002f0dc2893bc4bc13e4cd8d40803`。
诊断review SHA256`f9b3f8d070f60c7d606e57037c51182a23f5fd8b949a252c2f3c29b9207d6de8`，
84项CSV SHA256`b4e37c810241b4652f1a6885daec827f2801b958ed7afd26f033afffebece372`；
1024 SQLite SHA256`eeca2c95450bd0dba00a86f5342802aa849cffdcf469bd21a095b1b08b7aca83`。
新本地复核仅写`.local/diagnostics/coe_midpoint_failure_closeout_v0_1/review.json`；
未改生产代码/合同/原报告，未运行测试、完整analyzer/Q0、服务器或GPU。仅执行定向只读
来源/实例核对及文档一致性检查，不将其写成独立完整S重建或新资格。Gate13限定PASS、
Gate14 NOT_RUN、旧Formal/Pilot/Engineering角色、UNKNOWN/NOT_ASSESSED及用户DOCX保持。

## 7.190 固定P三点输入轴Pilot：0.2有限合同、本地接线及两阶段待审交付（2026-10-17，历史发布）

> 下文NOT_RUN/待A是交付时状态。实际已回传1完成/1拒绝/7未运行，0完整block；当前失败收口
> 见7.191，不继续使用本项的待启动指令，也不改写原回执。

用户批准512/1024/2048、三个完整block、9P1/9profile的本地准备和预算；本轮不操作服务器。
当前最高优先级：完成新阶段A真实回执审查后才可显式启动该批B；1024实际目标准入NOT_RUN。
旧7.189的“尚未授权本地准备”是当时状态，原数据与判定不改。

- [x] 新有限角色`COE-INPUT-P-PILOT/0.2`、profile0.2及矩阵身份schema0.2；保留0.1的
  默认行为、两点/四block/八槽及输入拒绝。1024只在新角色下进入，旧G1/Engineering/
  Formal和其它Pilot不扩域。新文件字节、全batch input/mask及源码身份逐层绑定。
- [x] 复用原prepare/seal/采集argv、producer/Canonical、两token准入、COE和预算连接器。
  P helper、runner、Host读取/同步/drain边界、S/A/B/registry及候选公式无变化。
  仅共享COE角色adapter按已验证binding版本分派输入；采集前验证器显式识别0.2。
- [x] 九槽顺序512→1024→2048、1024→2048→512、2048→512→1024，三个位置各一次；
  不声称消除全部顺序/漂移。每run新进程、只P1、batch1/o2/w3/r1，自然路径无Cpre。
  固定预算或硬失败即停，完整block为比较单位，partial/失败/未运行槽位保留，无补采/替补。
- [x] 主比较仍首token端点ΔQ和原R；两相邻输入的signed ΔQ/精确R为预定中点描述。
  端点R不意外依赖中点分母，无效分母null不加epsilon，Q/G显式保存。第二token全部保留，
  累计W不当Decode新增量；零/负/非单调/混合不是质量门。原A与候选去重预算仍独立。
- [x] 独立手算覆盖端点R=-3、两中点R=+4/-15、零分母及中点UNKNOWN与端点隔离；
  实际producer→Canonical→两token→预算→三完整block真实文件消费由CPU外部替身验证，
  另覆盖1024实际prepare/seal/profile边界、错角色/hash/token/drain/依赖/预算及硬失败停槽。
  这些不是目标CUDA/1024资格，未重跑完整Q0或无关大测试。
- [x] launcher默认A仅部署/源码/定向CPU/compile/新鲜资源；新B必须精确绑定新静态回执
  和独立显式开关。继续新鲜12GiB参与卷检查，同卷去重，不遍历历史YLQ/ACL或自动清理；
  历史总量null/UNKNOWN及长期<50,000,000,000 bytes未证明的状态不变。
- [ ] 新目标阶段A和9槽P1：NOT_RUN，交付审查不等于目标准入；本轮不提供B命令。

最终定向命令：`python -m pytest -q -ra -p no:cacheprovider tests/test_coe_input_pilot.py
tests/test_coe_input_delivery.py tests/test_coe_input_midpoint.py tests/test_coe_midpoint_delivery.py
--basetemp=.local/midpoint_final_release --junitxml=.local/midpoint_final.xml`：
75 passed、0 failed、0 skipped，147.34s。本地3.12.7；目标旧回执3.11.16，新代码仍待新A。
实际九run CPU producer文件另核对27窗口原/候选预算union守恒、父子及phase相加一致，
不作为新增GPU/Q0证据。定向compileall及真实PS5.1入口/参数分派通过；红灯阶段已见
缺版本接口、缺0.2部署分派、缺Q/G输出、端点误依赖中点分母等对应断言，错输入hash仍拒绝。
未修改测试追绿或放宽身份/依赖门；额外`tests/test_observation_delivery.py`旧Engineering
launcher定向回归10 passed/0 failed/0 skipped、22.48s，非重复GPU/全Q0。

固定执行/分析`4da800d2e8d270fdc2e25e07ab3511a73066df46`；最近可信服务器前置
`006d371a41c936b4cbf517d41e7ac7f89de76a47`，由已审静态/八槽终态绑定，新A仍须核对实际HEAD。
唯一待审包`coe_input_midpoint_4da800d2e8d2_delivery.zip`，104,899 bytes，SHA256
`70b2083420dd9c3f6947353ddee466b3e14eb9396520f7bc801e02a260bdc483`；manifest SHA256
`9f5ae764cd050e01f7b1efa66c4a360e63d13b039953655e21b5ef255878e527`。
独立回读17成员/16项清单、CRC/hash全覆盖、389源码表示、三输入独立摘要、bundle、真实
PS5.1语法及10项未变测量组件通过；新A/1024GPU仍NOT_RUN。原包不因后续文档HEAD重制，
控制层提交不替代4da800执行身份。本地准确命令/路径见handoff，不含本轮B命令。

机器计划
[三点Pilot](../../configs/coe_input_midpoint_pilot_v0_1.json)，执行说明补入
[当前短稿§12.6](coe_research_short_note_v0_1.md#126-三点pilot本地执行准备2026-10-17目标执行仍not_run)。
预算30～45分钟/临时12GiB/保留0.8～1.5GiB为估计，实际沿用profile300s、单run driver900s，
无新增全批超时放宽。旧Formal、Gate13限定PASS/Gate14 NOT_RUN、B2/七槽BLOCKED、
参数/引擎支线停止、UNKNOWN/NOT_ASSESSED、用户DOCX与大型原件均保留。

## 7.189 已执行512/2048输入轴Pilot：四block离线科学收口（2026-10-17，历史收口）

当前最高优先级：研究固定P自然完成程序的条件化输入响应；本批已完成，不再等待7.188的
阶段A或把2048实物写成NOT_RUN。唯一推荐下一阶段为同期512/1024/2048中点Pilot设计，
**本轮未批准/实施新预算、代码适配或采集**；输出轴另列后移条件，不同时推进。

- [x] 原`coe_input_006d371a41c9_pilot.zip`，57,439,121 bytes，SHA256
  `1cefbd642591f73e95d94f618524b6f775439396f00150b8aece01877013ea68`；manifest
  `72998ce8eace51ef89f5222a7a41ddba703fc5962760d42a28f5c154e945b4ca`。
  复用协调614成员/613项完整CRC/hash与源码绑定；重新核对ZIP身份、消费文件hash和
  全覆盖安全路径。执行/原分析`006d371a41c936b4cbf517d41e7ac7f89de76a47`不变。
- [x] 8run/4完整block/16操作/24原A窗口；真实Python3.11.16、P、w3/r1、输入/token/
  drain/准入证明链复用并核对。Raw成员逐行连接、两模式保存后缀、区间union、精确R、
  原A/候选预算守恒及phase拆分通过已审证据核查；**不是独立重建全部S或重跑Q0**。
- [x] 首token四个signed ΔQ为+111.106898/+135.736971/+113.308640/+105.558336ms，
  预定R为+105.987593/+106.342583/+107.954190/+101.960957ms。G增3.39～3.73倍，
  Q增12.04～72.04倍；候选E∪Q/Prefill为45.95%～52.16%，Q自身约45.94%～52.15%。
  不是因较大占比即成功，也不把原A其它内部同步贡献误写成0。
- [x] 16个末尾sync交集均0；第二tokenΔQ一正三负（+6.879959/−0.158686/−1.679924/
  −7.243499ms）完整保留，512长值不删。必要GPU活动的phase内copy前/操作内位置
  逐行列出；首tokenQ/G从2.96%～21.25%变为62.28%～75.44%，增量98.54%～98.90%
  来自kernel。Raw实际kernel/count/grid与MemOp来源变化另列，不补造数学数据依赖。
- [x] 公平保留API墙钟、phaseGPU union、同操作GPU union及完整timeline；本批16次
  同操作union=COE，**不宣称独有数值信息或优于完整依赖时间线**。H/D为同trace钟，
  H非精确包装成本，D/补集/API/COE不称纯Host阻塞；无P0迁移、稳定收益或硬件因果claim。
- [x] 收口结论：本批支持phase特异、非比例活动位置响应的限定可证伪命题，值得继续
  审查中间形状；不是新Formal、普遍单调规律或已成立论文贡献。原件PENDING_REVIEW不改，
  新审查状态`PILOT_RESPONSE_OBSERVED_WITHIN_BOUND_SUPPORT_NOT_NEW_FORMAL`。
- [x] 在[现有短稿§12](coe_research_short_note_v0_1.md#12-已执行5122048输入轴pilot响应活动位置及下一项有限问题2026-10-17)
  补全部16链与8比较；小型[操作CSV](coe_input_pilot_operations_v0_1.csv)、
  [比较CSV](coe_input_pilot_comparisons_v0_1.csv)、[原A CSV](coe_input_pilot_original_a_v0_1.csv)、
  [来源/公平baseline JSON](coe_input_pilot_sources_v0_1.json)保留整数ns/来源hash。
- [x] 本轮本地命令`python .local/analyze_coe_input_pilot_closeout.py`与
  `python .local/publish_coe_input_closeout.py`均exit0；前者仅消费保存结果/只读Raw连接，
  后者只汇总，不重跑完整analyzer。`python .local/check_coe_input_closeout.py`核对全部16行
  展示/8精确比较/24原A、来源hash、Markdown链接及DOCX身份，exit0；`git diff --check`通过。
  小回执见本地`coe_input_pilot_closeout_v0_1/consistency_final.json`；
  本地Python3.12.7，不新增CPU测试或将其当目标GPU资格。生产代码/合同未变。
- [ ] 下一批仅设计：512/1024/2048、3完整位置平衡block、9P1，约30～45分钟、临时12GiB，
  新增保留估0.8～1.5GiB。1024须新有限输入/mask/身份及顺序/汇总版本接线，不重写S/A/B。
  第二token全保留；实际准入失败即停，不试跑、补槽、扩hook。预算/执行尚未授权。
- [ ] 输出轴后移：当前输出2只含一次Decode；固定512、输出2/16配对设计及真实16token
  缓存/身份/完成锚点、历史前缀、逐token分母/去重资格未实现，不能直接授输出16/32。

计划调整：7.188已从本地交付进入已执行Pilot的离线科研收口，后续优先中点而非扩大端点/
引擎/collector。三个中点block只审查响应形状，不保证精度或识别精确阈值；旧数据不拼接为
新重复。历史总占用UNKNOWN、长期<50,000,000,000 bytes尚未证明，不清理或遍历ACL。
Gate13限定PASS/Gate14 NOT_RUN、旧Formal/Raw、B2/旧七槽BLOCKED、参数支线停止及
UNKNOWN/NOT_ASSESSED均保持；用户DOCX和大型原件不纳入提交。

## 7.188 固定P输入轴512/2048 Pilot本地接线及两阶段待审交付（2026-10-17）

> 历史发布记录：下文“待A/2048 NOT_RUN”是交付时状态；实际静态和8P1已回传，当前结论见7.189。

用户批准既定四个完整配对block、8P1/8profile预算；本轮仅本地实现、CPU和交付准备。
依据仍v7.1/v2.1及独立COE候选，生产S/A/B/registry、旧Formal及历史判定不改。
当前最高优先级：审查新阶段A真实回执后才可显式启动B；目标2048实际准入NOT_RUN。

- [x] 新有限合同`COE-INPUT-P-PILOT/0.1`与PROFILE：512/2048、batch1/输出2、w3/r1、
  FP16/eager/SDPA、固定P与自然Host-readable。共享COE Pilot原结构envelope显式分派，
  旧batch1/2/4及O/P Engineering声明不扩域；新输入只进入新角色。
- [x] 完整输入/mask矩阵摘要与预备文件字节绑定；交付前离线生成固定输入，目标运行必须
  匹配预定字节及摘要，不把即时sha作为期望。模型沿用原inventory/内容，不部署新模型。
- [x] 复用现有P helper，源字节及实际两token cache消费绑定manifest/producer/receipt；
  新增的只是角色与2048接线。没有移动动态状态、clock、NVTX发射、Host读取或CUDA调用，
  不插Cpre、不切流。seal前发现缺少新合同分派，补精确版本而非绕过身份门。
- [x] prepare→seal→真实profile argv边界、实际producer文件→Canonical→两token完整
  原准入→COE→独立预算→报告hash消费，以明确外部OS/设备/collector替身验证。
  原A和独立候选三窗口继续分开；Request/phase/操作union去重、原类别迁移和来源不变；
  无domain巨型输出，Decode缺口不能以Prefill-only规则绕过。
- [x] AB/BA/BA/AB固定8槽新进程；首token主比较signed ΔQ及
  `R=Q2048-Q512*(G2048/G512)`，保存精确有理数及ns。G是对应phase GPU union，
  第二token累计必要集合不充当Decode新增量；分母无效R=null/UNDEFINED，不加epsilon。
  第二token/原A/候选E∪Q/COE/分母/成员/H/D/同窗baseline全保留，完整block才配对。
  负、零、混合结果不拒绝；硬失败/固定8槽即停，无额外2048试跑、补槽或降级输入。
- [x] 默认A复用原launcher部署、源码实字节核对、相关CPU、compile与参与卷新鲜12GiB
  空闲检查。B另需新A回执精确hash及显式角色开关，仍复查clean/source/新鲜资源。
  不遍历历史YLQ/ACL、不自动清理；历史总量null/UNKNOWN，长期目标<50,000,000,000字节
  未证明。最近可信服务器前置来自已核验2d0d88e静态及八run终态回执，不假定实时checkout。
- [ ] 新目标阶段A及8槽GPU实际执行/准入：本轮均未运行，不能把CPU替身写成2048资格。

最终定向命令：`python -m pytest -q -p no:cacheprovider tests/test_coe_input_pilot.py
tests/test_coe_input_delivery.py --basetemp=.local/input_release --junitxml=.local/input_final.xml`：
44 passed、0 failed、0 skipped，75.23s。更广受影响回归（同两文件及旧observation、delivery、
budget、coe_pilot）139 passed/0 failed/0 skipped，156.07s，与44重叠不相加。
定向compileall和真实PowerShell5.1入口/分派检查通过；本地Python3.12.7，目标3.11.16为
既有证据，新增代码仍待新静态回执。中间复验因分析期间改动受hash保护源码触发
COE_SOURCE_CHANGED；未放宽该门，冻结本地文件后最终44项全部通过。

已验证有限输入/角色/源码/hash/Token/缺drain与依赖/第二token缺映射/错误出口等拒绝，
含独立手算R=-3、零分母null、全预算负差和失败保留未运行槽位。不是完整Q0/新CUDA资格。
交付在实现真实commit后绑定执行/分析版本，不自引用hash；准确包身份见本机handoff。
固定执行/分析`006d371a41c936b4cbf517d41e7ac7f89de76a47`，服务器前置
`2d0d88e7553b11587d66132ec51f5956092a87e6`。唯一包
`coe_input_006d371a41c9_delivery.zip`：1,560,328 bytes，SHA256
`6bd182bc616423ce9b0899830fb556931c71537938bbfda6b475d980225954d9`。
独立回读15成员/14清单、CRC/hash全覆盖、386源码Git表示、bundle、PS5.1语法、
两输入再生成字节/矩阵摘要均通过；原runner/S/A/B/registry与该前置一致。
此处包身份为实现提交后的控制层追加，不改变包内checkout或重新包装。
预计35～60分钟、临时12GiB、最终1～3GiB是估计，不保证2048可行；任何新API分支、
映射/依赖/诊断等硬缺证仍停。阶段A回传后集中审查，暂不交B启动命令。

计划调整：7.187待审预算已获本轮批准，新增有限执行域，不是新Formal冻结或原合同改写。
Gate13限定PASS、Gate14 NOT_RUN，旧B2/七槽BLOCKED、参数支线停止及UNKNOWN/NOT_ASSESSED
保持。用户DOCX、大型原件不纳入提交；没有服务器/GPU/Nsight/新模型或引擎/hook操作。

## 7.187 COE候选预算最小接线、现有非比例响应及512/2048待审设计（2026-10-17）

本轮用户授权本地代码/相关CPU及已有小结果分析，未授权新GPU预算。当前依据仍研究设计
v7.1、Pre-Pilot协议v2.1、既有RouteA限定冻结及独立COE候选；不改旧Formal测量/判定。
不画图、打包、操作服务器、启动模型/CUDA/Nsight或恢复引擎/hook/B2/旧七槽。

- [x] 先核对并复用coe_candidate的逐token身份配对、FIFO必要集合/coverage及已有
  preview_budget的union迁移；新analysis/coe_budget_preview.py仅连接已准入原A、
  Canonical和两默认流模式一致的S成员证明，逐类核对旧A后再迁移，不按重叠选W。
  [独立合同0.2](contracts/coe_budget_preview_v0_2.json)；缺成员/重复、未覆盖API、
  错身份/source、模式证明不一致/无效准入继续拒绝，unknown不得未经解决迁移。
- [x] observation_preparation.process在既有两token链完成后自动另写
  candidate_budget_preview.json；独立已存结果离线入口复用同连接器，不改原candidate CLI。
  原A及子类不改，候选completion_exposure与原Device wait分开；逐片段保留API/活动/
  sync/operation来源，Request/phase去重守恒，不跨sync B求和。
- [x] 先红后绿：新功能缺失及实际producer不输出预览分别复现，另用遗漏Canonical API
  的反例识别清单覆盖缺口；补严后通过。真实source→producer→Canonical→局部准入→
  候选输出使用CPU外部替身，不冒充目标GPU验证。最终相关命令和数量见下。
- [x] 新目录coe_response_preview_v0_6消费同一封存8run：16链/24原A窗口/阶段关系均与
  原件匹配，成员copy前/操作内union、H/D、原sync/补集及迁移来源可追溯；单run约2.4～
  6.4s，无完整analyzer/Q0重跑。旧24链及四token/反例复用已有资格和本轮相关回归，
  旧12个成块比较仅小CSV连接，保留角色，不再恢复旧Raw/重新演算其集合。
- [x] [现有短稿§11](coe_research_short_note_v0_1.md#11-候选预算接线与输入轴主线有限的非比例响应待检验2026-10-17)
  给出8个新配对G/Q倍数、扩展预算pp、H/D及位置；另有旧12配对，同存
  coe_load_response_comparisons_v0_1.csv但不合并样本。固定P首token的G倍数1.8466/2.2009，
  Q倍数2.2378/6.0972，扩展预算+1.9131/+3.7896pp；仅可追溯非比例线索，不是稳定/因果结论。
- [x] config内容核验：官方660字节配置SHA98d2ff8c…bf670与封存model_inventory一致，
  max_position_embeddings=32768，2048+2静态未越界；不是显存、API分支或资格PASS。
  当前runner仍只接受32/512，不放宽旧profile或声称2048已可运行。
- [x] 唯一[待审机器设计](../../configs/coe_input_axis_proposal_v0_1.json)：P包装下512/2048、
  batch1/输出2/w3/r1，顺序AB/BA/BA/AB，4完整block/8P1；仅待审，无执行commit/入口。
  同期512作配对，不复用旧512作新重复，不机械重跑32。预计35～60min、临时12GiB、
  保留1～3GiB，均非2048实测。首/第二token全审，主比较首tokensigned ΔQ并对照同比例
  G缩放；混合/近比例/单block主导为不支持或不确定，硬失败或固定预算即停，不追采。

本轮没有把个位数否定或把增长当贡献。可证伪候选为固定完成/观测政策下首token操作内
必要活动是否相对phase活动量超比例增长；公平同操作union/timeline同样能回答，分析用途
不等于算法优越。H/D、kernel分支和第二token限制保留；旧B1/B4与W11只作各自角色线索。
下一步需用户只审查上述8P1预算；批准后才接新有限输入/身份域和交付，当前不要求服务器。

验证：`python -m pytest -q -p no:cacheprovider tests/test_coe_budget_preview.py
tests/test_coe_candidate.py tests/test_completion_operation_candidate.py tests/test_observation_preparation.py
--basetemp=.local/coe_release_final3 --junitxml=.local/coe_release_final3.xml`，127 passed、0 failed、
0 skipped（63.59s）；
另新模块/文件链17 passed、0 failed/skipped（19.83s），与总回归重叠不相加。
`python -m compileall -q analysis/coe_candidate.py analysis/coe_budget_preview.py analysis/observation_preparation.py`
通过。Python3.12.7，本轮无目标3.11复验，不把既有3.11证据扩大；只做相关CPU及文档/数值检查。
用户DOCX及大型原件不纳入提交；Gate13限定PASS、Gate14 NOT_RUN及UNKNOWN/NOT_ASSESSED/
历史BLOCKED均保持。执行计划调整不影响已冻结或旧Formal数据，handoff同步本项。

## 7.186 参考执行对象/P0包装澄清与全部A/COE结果图（2026-10-17）

本轮按用户要求只梳理既有证据和作图，直接补[现有COE短稿§10](coe_research_short_note_v0_1.md#10-执行对象包装与结果图固定后续观测实现的条件2026-10-17)，
不新增评审流程、推理实现、测试、包/服务器命令或采集。7.185混合/不可判别科学裁决保持。

- [x] 分层流程图及实际调用顺序：forward/argmax是计算，逐token`.cpu()`→实际Host ID
  是我们选定的完成政策，身份/标签/NVTX/recorder/clock是研究包装。模型/输入上GPU、
  warmup和final drain在窗外；T0后的point/record工作可进入Decode，NVTX不是GPU完成。
  O/P均带包装；P仅前移不变准备，仍有现场检查/记录，不是Cpre或已证明的无插桩时序。
- [x] 回读99f3bae冻结runner/recorder和2d0d88e当前路径：P0仅禁用Nsight/NVTX发射，
  copy前身份仍构造；recorder即使marker_sink=None仍校验/编码payload并采时钟。
  故旧P0是共同封套未profile性能，不是无包装真值，P1−P0不能消掉共同包装影响。
  这是解释澄清，不是冻结违例或旧Formal失效；本批没有P0/U不能补造其组成。
- [x] 三幅可视化及图源：原A24窗口五类绝对值和各自百分比；COE16链绝对值及对应
  phase百分比，全部block/run保留，不合并总体比例、不将COE加进旧Device wait。
  图、PNG/SVG、图源JSON及只读绘图脚本在figures/observation_preparation_v0_1/。
  原值与§9.4及协调CSV核对，类别守恒/阶段相加，数据角色不变。
- [x] 最小缺证分离：限定目标若是固定带包装P1参考程序，既有实物可复用逻辑/适用性，
  不需再做同型“能运行”资格；固定实现后真正缺的是独立block验证预定输入响应。
  若额外主张迁移到无包装程序，才须少包装参考与拟选实现的受控对照，且不能冒称绝对
  零扰动/无trace COE。本轮建议不作该迁移claim，不默认P已最终冻结，不自动增加U组。

执行的唯一数据处理命令为`python docs/v1_4_1/figures/observation_preparation_v0_1/plot_figures.py`：
最终8run/24A窗口/16COE链作图，原CSV hash一致；不导入producer/analyzer，不读巨型domain。
初次绘图的报告列数检查拒绝后，按实际11列修正图表读取器；另消除字体缺字，未改原数据。
最终只做图源数值/比例、图片视觉、链接和diff核对，无pytest、compileall、GPU或实验。
本地Python3.12.7/matplotlib3.9.2仅为绘图环境，不冒充目标机资格。

当前优先级：明确限定参考程序和观测实现，再为可证伪输入响应安排研究；当前无需用户
操作服务器、不重开Gate或恢复已暂停支线。Gate13限定PASS/Gate14 NOT_RUN、旧Formal、
历史UNKNOWN/NOT_ASSESSED/BLOCKED及用户DOCX/大型原件保持。handoff同步。

## 7.185 O/P八次实物科学收口：操纵有效，独立效应不可判别（2026-10-17）

用户回传8P1原件及协调review/operations/Raw引用复核，本轮只做本地证据核对与现有报告
收口，无实现、测试、采集、完整analyzer/Q0、设施或新预算。执行/分析仍为
`2d0d88e7553b11587d66132ec51f5956092a87e6`，控制文档HEAD不替代它。

- [x] 复用协调598成员/597清单及全CRC/hash核验；直接消费3份小来源及8份已绑定结果
  JSON，逐份核对CSV结果hash。原包55,685,025 bytes，SHA256
  `bfd0bb05913c5af0079fb8d9e3cb991b2ad808b123ee8f7bdcba87b03cf78838`。
- [x] [现有短稿§9](coe_research_short_note_v0_1.md#9-op观测准备位置消融8p116链科学收口2026-10-17当前)
  展示全部16链、copy/操作/组成/补集、预定P−O/512−32/差的差及24个原A窗口（含API
  submit/non-submit）。ns整数独立核对、父子/守恒、Request阶段相加成立；原A未迁移。
- [x] 目标实物8run/2block/16链在声明Engineering域闭合；token、准备消费、实际源码与
  同长度kernel/shape结构一致。独立Raw复核仅引用成员/区间，不冒充本轮全依赖重建。
  H全部下降0.174381～0.575510ms；COE的P−O为5正3负，D同时变化（3正5负）。
  科学裁决INCONCLUSIVE_OR_MIXED，不是准入失败或可补采到预期的理由。
- [x] 两token在O/P下的512−32 COE均为正，旧第二token反向未在新批复现。
  新O不是旧Formal分支，不能归因于P或改判旧数据。16个原token同步交集全部0；
  phase原A可有其他sync贡献，不能混写。unattributed原值0不证明机制均已解释。
- [x] 公平baseline：COE与同操作窗口普通GPU union在16链数值完全相同；完整依赖
  timeline可回答同一任务，不以数字更大/自动化/校验通过宣称新颖性。

当前已支持：准备位置操纵、限定完成结构的可追溯查询、phase总活动量不能单独替代
操作内时间位置这一具体反例。仍未支持：独立包装效应、稳定负载规律、纯Host阻塞、
P0精确组成/收益或方法论文增量。两输入端点/两block不足以识别曲线，但先扩配置不是
核心补救；关键缺证是固定观测/完成政策下独立复现的非平凡关系及公平baseline下的
实际分析用途。候选开题收敛为“输入负载与token完成结构及其观测准备敏感性”，不是
新等待指标或预设单调。详细可证伪边界/停止条件在§9.6；技术报告定位保持，不宣称开题
或论文贡献已成立，不把再采样作为默认下一步。

本轮文档数值、来源/链接和diff检查；不重跑测试/实验。同步忽略的AI_HANDOFF和交付
历史提示，保留用户DOCX、未跟踪巨型ZIP、所有Raw/UNKNOWN/NOT_ASSESSED/旧BLOCKED。
Gate13限定PASS、Gate14 NOT_RUN、B2/旧七槽BLOCKED及参数支线停止结论保持。
最高优先级为据已完成结果确定上述单一、可证伪的实证主张；当前无需服务器操作，
不得继续执行旧交付命令或自动追加8/24profile、引擎/hook。7.184为发布时状态，已执行
及当前结论以本项为准。

## 7.184 观测准备位置消融：本地最小实现/验证及待审交付（2026-10-17）

> 历史发布记录；静态与8P1实物已回传，当前科学收口见7.185。下文NOT_RUN/待执行均为当时状态。

用户已批准32/512、batch1、输出2、w3/r1、O/P两个完整四条件block/8P1的Engineering
测量敏感性验证。本轮仅本地接线、CPU和打包准备；没有服务器、模型/CUDA/Nsight、新
样本或旧数据重算。新实验NOT_RUN，Gate13限定PASS、Gate14 NOT_RUN、B2/旧七槽及
历史UNKNOWN/BLOCKED不变。不是原8次仅Prefill重复，也不是恢复负载矩阵或纯阻塞路线。

- [x] [版本化合同](observation_preparation_engineering_v0_1.md)及
  [机器计划](../../configs/observation_preparation_engineering_v0_1.json)：顺序32O/32P/512P/512O
  及反向；O原helper直接调用，AST与bbbb468完全相同，结构指纹205ef13d…c1f。
  P仅在既有最终drain之前校验/编码不变的run/request/token标签，缓存绑定进程/线程与
  一次消费。NVTX、CUDA、动态状态、Host读取和完成clock均不前移。
- [x] 直接CPU证据：每token O现场身份构造/编码各1次，P现场各0次、窗前各1次；两token
  标签在仅区分预定run_id后逐字段等价，Host read→clock→recorder/pop同序。
  新Engineering O不冒充旧Formal校验分支成本；H不是精确包装开销。
- [x] prepare→严格seal→实际profile argv边界，及真实producer文件→Canonical→两token
  S/A闭合→COE→小结果/consumer/hash回归；外部设备/Git/模型/collector为明确CPU替身。
  两token采用既有完整request闭合检查，不添加Decode豁免；旧角色/版本/门槛不扩大。
  新模块实际源码随run归档、manifest/hash/独立schema绑定，不复用旧seal。
- [x] 每token/block固定signed P−O、512−32及差的差；保留H/D、必要成员/提交、COE、
  kernel/MemOp、copy/sync/补集、原A与公平baseline。完整block为单位，无拼接/填零。
  H均下降仅screen标签；D/结构共同变化仍须审查，混合/准备未有效改变为不可判别，
  不加样本、不保证稳定性/精度/因果或论文创新。
- [x] 两阶段PowerShell5.1入口：默认A只部署/相关CPU/新鲜参与卷空间；B需新A真实
  receipt SHA显式启用，旧A不解锁。低/未知空间、源码/回执冲突或硬失败停止。
  复用12GiB启动预留；不遍历历史YLQ/ACL。长期目标<50,000,000,000 bytes仍null/UNKNOWN，
  不自动清理；旧安全pack拒绝UNKNOWN writer时保留现场，不强行封包。
- [ ] 新静态回执及8P1目标实物：待交付审查后由用户执行，不能由CPU替身授予资格。

验证命令/结果：`python -m pytest -q -p no:cacheprovider tests/test_observation_preparation.py
tests/test_observation_delivery.py --basetemp=.local/test_obs_release2 --junitxml=.local/obs_release.xml`
结果48 passed、0 failed、0 skipped（81.12s）；另运行`tests/test_coe_pilot.py tests/test_runner_token_ready.py
tests/test_batch_load_diagnostic.py tests/test_n1_preprofile_identity.py`，118 passed、0 failed、
0 skipped。`compileall -q exposedpath analysis scripts/observation_preparation_batch.py`及
`git diff --check`通过。未重跑完整Q0/全量测试或已完成GPU实验；本地Python3.12.7，目标
3.11.16的新变更仍待静态阶段复验，先前真实3.11身份只作历史依据。

最高优先级：审查固定新执行/分析commit的单一待审ZIP；前置取最后可信63ca051目标
回执，不猜当前checkout。A默认不初始化CUDA；B回执审查后启用。预计25～45分钟、
8进程/8profile、临时12GiB，最终新增/保留估计1～3GiB；均为预算估计而非实测。
用户DOCX和未跟踪大型原ZIP保持且不纳入提交，原研究设计/冻结语义/数据角色不变。

收尾绑定：执行/分析`2d0d88e7553b11587d66132ec51f5956092a87e6`，已正常推送。
唯一待审`observation_2d0d88e7553b_delivery.zip`，129029 bytes，SHA256
`3203f043ca93764c139488d762e9bd1464f6d296fdfb241dbf72ebb6d3f402ab`；12成员/11项
全覆盖清单、CRC/hash、bundle verify及379项Git源码表示核验通过，未包含用户DOCX/Raw。
准确私有传输路径、A整段命令和B新回执启用条件集中在忽略的`.local/OBSERVATION_DELIVERY.md`。
控制文档后续提交不替代该执行身份；新A/B均仍未执行。

## 7.183 24条自然链竞争解释核对；暂缓8次纯Prefill重复（2026-10-17）

本轮只做用户授权的本地只读时间位置分析与待审设计；未改生产代码、测量定义、质量门或
旧结果，无测试、模型/CUDA/Nsight、包/服务器命令及新预算。复用已绑定成员索引及12份
SQLite，按引用rowid只读取得必要活动/submit时间，不恢复依赖、不重跑COE/完整analyzer。
[现有短稿§8](coe_research_short_note_v0_1.md#8-竞争解释核对设备执行host到达与观测包装2026-10-17)
集中给出竞争解释表与唯一建议；[24链位置表](coe_completion_positions_v0_1.csv)逐行保留
来源ID/hash、同trace钟、绝对copy入口和偏移，不跨Host ledger钟相减。新演算不是新Formal。

将copy前最后必要submit API返回L、copy入口C、最后kernel完成K、D2H terminal和sync
返回分开。H=C−L为Host调用间隔，D=K−L包含排队/执行/空隙；K−C=D−H只作时间恒等式，
不作纯阻塞真值。最后必要submit为copy API，其内部准确入队点未观测。成员仍截止配对sync，
保留已完成前缀及操作内D2H；G为相邻捕获集合新增成员union，不授完整物理W/B。

实物：G512第二token5/6在copy前完成全部kernel；其中4次H还比G32短，不能统一归因
Host更晚。block5 G增加0.307611ms但COE减少0.856154；block4 G减少2.892774ms但COE增加
0.194398，否定活动总量单因子。block1第二token末尾同名argmax时长0.067168/0.069312ms，
但提交返回至末kernel完成D为3.818970/0.872707ms；不将差异直接归因某硬件或队列根因。
24链H为2.678358～5.061804ms，其中L→NVTX入口2.552900～4.960163ms。冻结99f源码在
argmax后调用身份构造及schema校验/编码；P0也做身份构造。只能提出包装敏感性解释，
没有逐函数旧实例计时，不能称整段是标记成本或P1−P0已消除共同包装影响。

裁决：暂不推进前一回复建议的输入轴8次纯Prefill重复。它只能检查跨批次/次序重复性，
不能分离共同的Host/设备/观测影响，更不能仅审Prefill就验证首/第二token反向。对原研究
主线尚不足以宣布立项，技术报告判断保持。唯一待审验证为相同完成政策的观测准备位置
消融：G32/G512×原包装/预先严格校验编码，两个四条件block/8P1，两token均独立闭合；
无新增同步/切流/Host读取，改变包装不改CUDA完成政策。仅为尚未授权的设计，不立项为
新采集任务。H未改变、D也变化而不可分或任一质量失败需停；只见COE变化不算区分成功。
若依赖新设施/大改则停止；不恢复引擎/hook/旧七槽或宏观矩阵。

第一方依据只定向复用SKIP执行/排队、Daydream依赖及RL-Scope §3.4/附录C的bookkeeping
影响；本轮问题是共同包装对完成位置判断的具体敏感性，不宣称扰动首次发现或新指标
创新。必要的文档/来源一致性检查，不运行测试或新增统计显著性检验；原DOCX/Raw/历史
报告、UNKNOWN/NOT_ASSESSED、Gate13限定PASS及Gate14 NOT_RUN保持。handoff同步7.183。

## 7.182 COE贡献差异有界核验：具体任务成立，确认技术报告定位（2026-10-17）

按用户授权仅补[现有COE短稿](coe_research_short_note_v0_1.md)§4.1/§6.1/§7；未新增研究
流程文件、代码、测试、CSV统计、Raw查询、GPU预算、实验方案/采集包/服务器命令。旧7.181
统计和图表直接复用，生产A/B、COE定义、数据角色、原Formal及全部历史判定不变。

明确一项分析任务：对实际Host token完成操作，判明I内活动仅为直接D2H，还是还包含配对
成功sync按流序必须完成的先行kernel，给出成员及其I内执行量；不称API内部纯Host阻塞。
block1/G512/t0：copy1.874498ms、phase GPU union44.157288ms，合格Q1.525365ms（kernel
1.524501、MemOp0.000864），直接D2H0.000544、原配对sync交集0。所有数字转录既有来源，
未重新演算。给予普通union同一I时，本例数值/相交成员相同；完整依赖timeline保留前缀后
也能恢复同一答案。1899个copy前已完成必要成员保留；不以I内6成员冒充整个必要后缀1905。

定向回读三项既有第一方原文/资料：Daydream作者v1§4.2.1～4.2.2和§6.2已讨论D2H先行
依赖及包含复制API的GPU-only预算；HTA文档0.6.1及可读main源码已有launch/流序/同步边和
ROI图查询；SKIP作者v1§III-A/§IV-A定义TKLQT等及ATen/runtime/kernel映射。所读位置未见
完全相同的copy+sync必要union接口，不据此断言整项工具没有能力或COE首次提出。Daydream
出版PDF读取失败，采用明确标注的作者v1；HTA源码未取得不可变commit，不冒称固定版本
实测。未运行同行工具、未扩展文献搜寻或恢复任何工程支线。

裁决：**确认技术报告定位**。有可复核的完成语义查询/实例化与相对简单聚合的分析用途，
但不是已证明的新方法或强baseline无法回答的新信息；API差已复现全部12方向、同I union
及完整依赖图可等价回答的反方证据保留。最小可检验实例化主张已获四token/24链支持，
唯一论文差异缺证是公平强依赖参照下的任务级增量，而非更多较大的数值。现无具体差异
实例或收益证据，不建议为此新增GPU重复、设施或工具移植；重复只能检查波动，不填补
差异论证。本轮不生成后续实验任务，不将未证新颖性写成已证明整个领域无价值。

必要验证仅检查修改文档相对链接、新增数字与既有来源转录一致、diff及原CSV/用户DOCX
未改；未运行测试/analyzer/Q0/实验。当前handoff同步7.182；Gate13限定PASS、Gate14
NOT_RUN、B2/旧批次BLOCKED及UNKNOWN/NOT_ASSESSED保持。用户DOCX和大型原件不纳入提交。

## 7.181 COE独立研究短稿：全部24链、公平baseline与技术报告裁决（2026-10-17）

本轮按用户授权只做COE科研成文和小型CSV连接/描述统计；未改生产代码、合同、registry、
数据角色或旧报告，无服务器、模型/CUDA/Nsight、新预算、采集包/命令、测试或完整分析。
参数取证路线7.180已结束，不恢复七槽、引擎或hook。
当前产物：[COE独立短稿0.1](coe_research_short_note_v0_1.md)，与旧A/B核心稿分开；
[12个完整block内比较](coe_research_block_comparisons_v0_1.csv)保留24条原链的全部值和来源。

明确RQ：在同一自然Host-readable完成政策下，输入长度变化时，首/第二token的哪些必要
设备活动仍落在copy→成功sync完成子包络内；常规参照能否回答同样问题。仍只测完成操作内
必要活动，不称纯Host阻塞/近似阻塞/可优化时延。W由原同步/提交/流序证据取得，不从重叠选；
candidate边界固定，不改生产A/B。原Formal角色与事后COE探索角色分开，未升级为新Formal。

六block/12run/24链全展示：首token G512−G32 signed差依次
`+0.705755,+0.976280,+0.979512,+0.995095,+1.090264,+0.876154`ms，配对差中位数+0.977896ms；
第二token`−0.649627,−0.604444,−0.601531,+0.194398,−0.856154,−0.574620`ms，中位数−0.6029875ms。
G512第二token五条仅0.416～0.448µs D2H，block4有kernel，全部保留；没有把token/kernel当
独立重复，无bootstrap、显著性检验或P0迁移。复用既有24链图，不重复区间演算或读取Raw。

公平比较结果：原配对sync交集24条全0；copy API墙钟已经复现12个输入长度差的全部同号
方向，COE没有新增方向判别。phase GPU union与COE在第二token的block4/5出现反向，支持
“总量与完成操作内时间位置不同”的描述，但不证明COE优越。给予普通union相同I/必要集合
时数值可等价；完整依赖timeline可恢复相同解释。新增的是可核验的完成语义/成员来源查询，
不是独占的Raw信息。长输入组P1阶段总长中位数反而更短的事实也披露，不选有利趋势。

四token独立验证仅用于成员/terminal/区间关系；旧同批B1/B4只作局部Engineering个案，Cpre
只作改变完成政策的机制对照，不与六block拼接或作为自然纯等待真值。零捕获B2及旧批次
继续BLOCKED，0完整batch1/2/4 block、不发布可信B2 COE。UNKNOWN/NOT_ASSESSED保持。

裁决：**当前最合适是技术报告（采用探索性测量案例结构）**。有具体RQ、独立计算依据及
正反实物，但公平强baseline下尚未建立新方法、非冗余实证或分析任务收益；不因Gate PASS、
较大交集、自动化或守恒宣布创新，也不将未证新颖性写成已证明毫无价值。未指定venue，不
保证发表或学位充分性。当前不建议任何新的GPU/工程预算，下一项不自动生成实验任务。

实际轻量核对：CSV键覆盖24链/12run/6block、与既有candidate和独立复用记录逐值相符；
baseline按相同run/block/phase连接，signed差由整数ns相减；小型来源hash和统计在忽略的
`.local/diagnostics/coe_short_note_v0_1/summary.json`，非新测量。复用原图并人工查看；文档
相对链接、表格值、diff和原CSV/DOCX未改检查，不新增测试充当研究证据。用户DOCX/Raw及
历史报告均保留。Gate13限定PASS、Gate14 NOT_RUN、旧A/B/COE定义及Formal不变。

## 7.180 新B2参数诊断零捕获收口；仅修正离线失败退出码（2026-10-17）

本轮Engineering原件只读核验/小型CPU修复，无服务器、CUDA、模型、Nsight、重采或新包。
当前集中依据：[可行性/收口稿0.7](memset_parameter_feasibility_v0_1.md#2026-10-17增补新b2零捕获当前普通共享入口路线收口-07当前)。
**当前普通共享入口方案覆盖FAIL；新B2和原Pilot仍BLOCKED。按预先停止条件关闭该参数采集
路线，不扩hook、不恢复旧B2或七槽，不将零捕获归因于具体库/runtime或count0。**

输入`memset_prefill_63ca05178b80_b2_once.zip`，3,962,993bytes，
SHA256 `80b6b72b4234112c9c5d75a0c2f52590d285f1c88f96a03395ca54d21424596e`。
本轮CRC、安全唯一82成员/81项清单、全部长度/hash/全覆盖通过；manifest SHA
`69750f2d845c7741610ad0e7f178aad5ebe4896be3648dc68658d9a532026e4e`。
新展开`.local/diagnostics/memset_prefill_b2_closeout_v0_1/source`，同目录review.json、参数NVTX
摘录和逐Prefill runtime引用保留；只读SQL复核，不重跑完整analyzer/Q0或旧B2 SQLite。
28源实字节/封存runner与63ca051 Git、已审A receipt/build/DLL、侧记录/manifest/producer/
entry创建实例、input/mask/token和模块文件hash均相符。该绑定不证明所有实际调用经由该导出。

实物：模型PID4788/TID49924、FILETIME134366848005075190，模型/profile/export成功、token
`[[29184,29184],[6556,6556]]`符合功能参考；3warmup及measured COMPLETE。原源码在drain前
安装、成功drain后begin、原first Host token后end、Decode后detach；五生命周期/错误码均0，
side完成时间与Host首token锚点一致。Raw DomainCreate在drain前，但无调用range；side calls=[]。
此证据只支持“本次方案零捕获”，没有每条目标调用时的hook内部执行/enable指令级证明。
Prefill 113次成功同目标runtime、84缺MEMSET；Decode85次、84缺MEMSET（本就不在记录范围）。
参数/count/native stream实例值UNKNOWN；不是NVTX -1返回适配再次失效，不授零payload规则。
具体内部原因UNKNOWN，不断言cuBLAS/private/static/PTSZ/patch干扰等来源，不再追索。

真实叶拒绝`MEMSET_PREFILL_NO_TARGET_CALLS_NOT_DISCRIMINATING`；分析进程exit1/8.437s。
collection异常仅写error，状态保留DIAGNOSTIC_COLLECTED_NOT_QUALIFIED导致driver exit0；
外层结果门最终拒绝为MEMSET_PREFILL_COLLECTION_RESULT，原attempt仍BLOCKED。
最小5行修改仅在新参数路径捕获分析/文件异常后置BLOCKED，返回1；成功采集/export事实及
原error/独立stderr保留，不改旧诊断-only退出语义。原ZIP/collection_report/Raw不覆盖，
也不为部署该控制修复新增模型任务；新分析代码不为本次数据补出参数或资格。

CPU先修正测试fixture缺字段/错pass，随后有效红灯为2failed/3passed：分析拒绝和缺结果均错误
exit0。最小修复后实际最终命令：
`python -m pytest -q -p no:cacheprovider tests/test_memset_prefill_failure_exit.py tests/test_memset_prefill.py tests/test_memset_prefill_files.py tests/test_gate8_diagnostic_collect.py tests/test_batch_load_scope_failure.py --basetemp .local/mp_failure_final --junitxml .local/diagnostics/memset_prefill_b2_closeout_v0_1/final.xml --tb=short -ra`
**56passed/0failed/0skipped，102.88s，Python3.12.7**。新5项涵盖实际main写回执/退出（采集、
模型、export、分析执行边界明确CPU替身）、合法成功、缺结果、历史退出兼容、零捕获不能当
零参数；复用原参数/Canonical文件链、旧拒绝和进程回执回归，无目标机新编译/GPU资格。
`python -m compileall -q exposedpath analysis scripts/gate8_diagnostic_collect.py`、diff检查通过。

研究决策：四token独立操作验证、12个G32/G512的24链、旧同批B1/B4局部Prefill及d6957de单个
B1合格Pilot槽继续按原角色/支持假设使用；不因本次新入口失败将其推翻，也不升级成新Formal。
缺失的是可信B2 COE、完整位置平衡block、B4−B1重复差/中间点/普遍负载关系；0完整block，
不能拼接Engineering/Pilot/旧Formal补重复。零参逻辑规则尚无真实B2资格，W/terminal未进入后续
审查。完整依赖timeline仍可解释同样完成结构，COE不获得纯Host阻塞/可优化时延解释。

唯一建议/停点：**不再追加当前参数采集设施或九槽补齐预算**；已有资料没有能保证命中的
另一个有界入口，增加同配置样本不能解决实例覆盖。保留已有支持域和失败的适用边界事实，
仅继续既有证据的有限分析用途/公平baseline论证。任何新工程投入需另有现存入口事实及明确
成本后集中裁决，不是本轮待办。生产A/B/COE/registry、旧Formal/Raw/BLOCKED、UNKNOWN/
NOT_ASSESSED、Gate13限定PASS/Gate14 NOT_RUN及用户DOCX/未跟踪大型ZIP均保持。

## 7.179 新B2 Prefill参数记录/零逻辑节点最小实现与待审A交付（2026-10-17）

依据用户批准0.5，本轮只本地实现/CPU/打包准备，未操作服务器或运行模型、CUDA程序、Nsight。
当前集中依据：[原可行性稿0.6](memset_parameter_feasibility_v0_1.md#2026-10-17增补新b2-prefill参数诊断实现-06当前目标机待验证)。
0.5历史设计及7.178保留；生产A/B/S/COE/registry、旧Formal和原报告不改。

新独立Engineering profile固定B2/512/2/warmup3/repeat1，复用verified模型入口与真实
prepare→seal→profile argv→producer/receipt→Canonical/局部Prefill检查；完整batch输入与mask
digest、实际token、模块实字节、process creation及run/request身份均绑定。仅一个未来新run，
无P0/Cpre/Pilot旧槽。记录器安装在原final drain之前，成功drain后启用，原首Host token后
关闭；不加CUDA查询/同步/复制/切流，不移动原completion。源码AST行为身份不变。

普通共享导出Detours范围记录4096预分配槽/自动call_id，精确uint64 count、别名、value/return/
LastError、PID/TID；窗外原转发，重入/外线程/overflow保留原调用但参数准入拒绝。消费者枚举
全部Prefill同类runtime，side↔闭合唯一NVTX↔runtime双向唯一，未覆盖/PTSZ/private不泛用。
`MEMSET-ZERO-LOGICAL/0.1`独立参数支持规则保留API墙钟和逻辑顺序、不造activity；正长度
必须真实合法MEMSET。零长度仍须原drain/局部门、实际设备/context/流桥、全部真实FIFO成员/
依赖、成功sync/Host token、两模式成员/边/terminal不变；缺闭包继续拒绝。原Canonical不改，
临时验证视图只处理已证零payload的缺正activity断言，原A输入保留全部API但不发布A结果。
成功仅`MEMSET_PREFILL_EVIDENCE_COMPLETE_PENDING_REVIEW`；A/COE NOT_ASSESSED，Request/
Decode NOT_ACCEPTED，不给零调用物理区间或完整W/B资格。

Tests-first经历缺实现/错误接线负例红灯后修复。最终本地真实PS5.1整段A演练命令：
`python -X utf8 .local/diagnostics/memset_prefill_v0_1/rehearse_a.py`。
实际CPU子命令（清除插件配置，CUDA_VISIBLE_DEVICES=-1，build路径指向本次Host构建）：
`python -X utf8 -m pytest -q -ra -p no:cacheprovider tests/test_memset_prefill.py tests/test_memset_prefill_native.py tests/test_memset_prefill_entry.py tests/test_memset_prefill_files.py tests/test_memset_prefill_delivery.py --basetemp .local/mpa1/Y/diagnostics/memset_prefill_aaaaaaaaaaaa_cpu_tmp --junitxml .local/mpa1/Y/diagnostics/memset_prefill_aaaaaaaaaaaa_static/cpu.xml`。
**64 passed/0 failed/0 skipped，31.93s**；本地Python3.12.7、MSVC14.44/SDK26100，真实CUDA12.4
头编译/链接、真实Detours Host替身/ctypes ABI，未执行CUDA程序。PS5.1→控制器→编译→pytest→
ZIP CRC/全hash/回执实际完成，退出0。Git部署/HEAD、测试中的模型/设备/collector边界明确替身；
不是服务器A或GPU验证。第一次深嵌套演练59passed/5failed（Windows路径长度）原件保留；
新短路径演练未改测试预期。证据`.local/mpa1/audit.json`及其static ZIP/原始CPU日志。

未改组件复用既有微例0.4/110项资格；只补旧路径相关回归：
`python -m pytest -q -p no:cacheprovider tests/test_batch_load_diagnostic.py -k "old_engineering_and_formal or prepare_finalizes or actual_producer_reads" tests/test_gate8_target_python.py tests/test_gate8_diagnostic_entry.py --basetemp .local/memset_prefill_legacy --junitxml .local/diagnostics/memset_prefill_v0_1/legacy.xml --tb=short -ra`
为9passed/74deselected（全局-k，不能说整个目标入口测试集通过）。另显式运行real_entry_argparse、
real_file_entry、pre_model_failure、model_failure、direct_cpu_probe五项，5passed/0skipped。
合计14项相关旧路径检查，不重跑54/110/Q0或完整analyzer；本地与目标3.11.16/14.38/SDK20348
差异保留，目标实际普通入口覆盖仍NOT_PROVEN。

交付策略：先提交实现，再由Git已提交内容生成增量bundle与精确源码/依赖索引，避免自引用。
前置002f3ae9fcc22f04356dbd22092dcddd8c63a460来自已核验微例原回执，原BLOCKED不改判。
复用固定依赖，无安装/升级；默认A仅部署/编译/CPU/新鲜资源检查，B必须另经真实A回执审查、
精确SHA显式启动。本轮只给A命令。future单次预算约15分钟/2GiB临时，profile300s/export180s/
readiness60s/analysis300s、driver900s硬限；一次失败或完成即停，无重试/替补/自动追加。
历史YLQ总量null/UNKNOWN、长期50,000,000,000bytes目标未证明；不扫旧目录、ACL或清理。

唯一后续：先审本地实现/新A包；以后一次新B2成功可回答普通入口完整覆盖及零payload/正效果/
闭包是否成立，供另审参数辅助局部COE，不自动PASS。失败即具体原因停止，不扩hook或重编。
旧B2/Pilot BLOCKED、7 NOT_RUN/0block、Gate13限定PASS/Gate14 NOT_RUN及UNKNOWN/
NOT_ASSESSED保持；用户DOCX和未提交大型原ZIP保留。本轮不升级旧数据或原Formal。

## 7.178 真实PyTorch memset覆盖审查与零payload逻辑节点消费草案（2026-10-17）

本轮为Engineering准备/合同设计，仅本地源码、第一方接口和既有小回执核对；无新记录器/消费者
实现、CPU测试/编译、包、服务器命令或CUDA/Nsight/model执行。复用7.177限定微例PASS，
不重复Q0/54项/110项，也不再查旧B2的84/168条SQLite实例。
当前集中裁决：[可行性稿0.5](memset_parameter_feasibility_v0_1.md#2026-10-17增补真实pytorch覆盖桥接与参数消费规则草案-05当前)。

**GO仅指一个未来新B2 Engineering参数诊断具备具体、有限的准备路径；PyTorch覆盖与新准入
仍NOT_PROVEN，参数完整本身不等于COE合格。** 历史目标PE原件及其清单hash表明：c10_cuda导入
共享CUDART，但torch_cuda/c10_cuda均无cudaMemsetAsync/PTSZ直接导入。不能据此认定实际来源
是cuBLAS、private或静态副本；也不能由微例PASS推导模型命中。未来必须以本次Prefill全部目标
runtime↔侧记录↔闭合唯一NVTX/call_id/PID/TID双向一一覆盖为门，不能按旧rowid/84次或时间邻近。

设计最小调整：范围通知接原成功drain后、forward前到首个真实Host token；自动call_id/有界
4096槽、实际pointer别名、多线程安装事务/外线程拒绝、窗外转发和异常关闭，均尚未实现。
不加CUDA查询/同步/复制/切流；普通导出以外的入口、重入、遗漏/重复、跨界及溢出即停，不扩hook。

消费规则MEMSET-ZERO-LOGICAL/0.1-DRAFT：count0保留submit API墙钟、逻辑调用及已证顺序/依赖，
不造device activity，不宣称无顺序作用。仅新窄域主线程/同流/closed-prior局部Prefill，在实际
context/stream桥、全部正活动、成功sync/Host completion完整且有限合法关系下的真实成员/依赖/
terminal不变时，才可考虑去除“每次submit必有正activity”的条件；该规则尚未批准生效/编码。
count>0继续要求唯一合法效果；缺效果/矛盾/映射未知BLOCKED，实际读回和成功返回不能替代。
独立预期已写9类正反例，含已完成前缀、跨流空操作歧义、未知scope/terminal、零参正效果、
非零缺效果、配对/入口/容量、质量失败；本轮仅设计，未运行，不冒称目标机资格。

唯一后续建议：先审/实现该窄域增量，再考虑1新B2、512输入×batch2、每样本输出2、warmup3/
repeat1、1进程/1profile，原自然完成路径，无P0/Cpre/旧槽续跑。它只判断普通入口是否完整覆盖，
以及缺口实际是零payload、合法正效果或非零缺效果；不能命中/依赖不闭合即停，不制作追绿批次。
预算估计15分钟/2GiB临时，profile300s/export180s/离线300s硬上限；未授权执行、未假定新空间。
历史总占用UNKNOWN及长期50,000,000,000bytes目标保持，不盘点/清理。

本轮验证限文档链接/差异、三份实际消费PE小资料的清单hash及微例既有派生绑定；无新CPU/CUDA
验证。计划调整不改冻结测量/统计、生产A/B/COE/registry、原Formal或数据角色。旧B2/Pilot
BLOCKED、7槽NOT_RUN/0完整block、Gate13限定PASS/Gate14 NOT_RUN、原UNKNOWN/NOT_ASSESSED
及用户DOCX/全部原件保持。最高优先级是该单项模型覆盖/参数消费的最小本地准备，不恢复旧批次。

## 7.177 NVTX返回值消费者修复；同一0/64微例离线限定PASS（2026-10-16）

仅本地封存副本/CPU修复与复核，不部署、不运行CUDA/Nsight/模型、不重采或发新包。
当前依据：[可行性稿0.4](memset_parameter_feasibility_v0_1.md#2026-10-16增补nvtx返回值适配与封存微例离线裁决-04当前)。
原微例ZIP 68,580bytes/SHA29e4413ad7c2895d261718c54fd301266c01a94e647fe2d265475865f22ab3b8，
27成员/26清单的CRC/全部hash/安全唯一全覆盖通过；manifest c177dcdd8caf4fb448074cf648c03f0e7734dd8f5c1ae48e7460a5b2be67bb32。
原执行/分析002f3ae，13源实字节与Git、已审A/build/runtime/包索引绑定一致；profile/export
exit0/无超时。原attempt仍BLOCKED/NVTX_RECORDING，原ZIP/Raw/side/旧派生/receipt不改。

根因是把NVTX非负相等层级返回当成已记录的必要条件；两次-1/-1却都有真实闭合范围。
CUDA12.4.1官方指南明确提示返回值随工具变化，不能以返回值决定是否记录。consumer/provider
升0.1.1，side0.1.0兼容；仅额外支持已观察-1/-1，不笼统接受未知负值。原值保留，任何正负
返回均需同进程真实DomainCreate/正确domain/run/call/PID/TID/闭合范围、scope与顺序及唯一
runtime；其后所有效果、bytes/value、stream/context/corr、读回和诊断检查保持。
不改native记录器/producer/launcher/S/A/B/COE/registry或冻结语义；旧raw_excerpt不冒充新schema。

tests-first原件与新增负例14 failed/2 passed复现；最终命令：
`python -m pytest -q -p no:cacheprovider tests/test_memset_nvtx_recording.py tests/test_memset_same_capture.py --basetemp .local/micro_nvtx_final --junitxml .local/diagnostics/memset_micro_nvtx_reanalysis_v0_1/final.xml --tb=short -ra`
**54 passed/0 failed/0 skipped，1.50s**，本地3.12.7；真实SQLite错误domain/endGlobalTid及缺效果
反例也严格拒绝，保留旧身份/同步/映射负例；未重跑native、110项、完整Q0或实验。

新analysis_0_1_1完整离线复核与独立Raw SQL均通过：PID70312/TID73452，NVTX2/3→runtime8/11
corr126/129；count0无关联效果、读回全3c；count64→MEMSET2/64bytes/value123，context1/stream7、
读回全7b。两次配对sync corr127/130正确，setup drain row7在scope前，14诊断均severity1。
**限定普通共享runtime微例Engineering PASS**由新adjudication关联，不改原BLOCKED。
新分析版本/源码hash及提交后实际commit单独绑定原ZIP/SQLite/side；原输入逐项hash前后不变。

最高优先级/停止点：交本地修复与离线裁决，无服务器操作需要，不恢复7槽、不制作采集包。
PyTorch内部覆盖、零长度顺序作用仍NOT_PROVEN；COE/A NOT_ASSESSED、旧B2/批次BLOCKED、
7 NOT_RUN/0完整block、Gate13限定PASS/Gate14 NOT_RUN、原Formal/UNKNOWN及用户DOCX均保持。

## 7.176 同次memset微例最小实现、CPU演练与待审两阶段交付（2026-10-16）

本轮按用户接受db6bd3e接口GO后的授权实现；仅本地CPU，未操作服务器、模型、CUDA或Nsight。
当前集中依据：[原可行性稿0.3](memset_parameter_feasibility_v0_1.md#2026-10-16增补最小同次微例实现与待审交付-03当前)。
实现先提交95c8371；打包前仅清除新增文件EOF空白并重新检查，不改变测试预期或运行逻辑，最终执行身份以交付索引绑定的后续提交为准。
本地实现完成不等于目标验证：目标A/B均NOT_RUN、COE/A NOT_ASSESSED；d6957de旧B2/批次
BLOCKED、7 NOT_RUN、0完整block，Gate13限定PASS/Gate14 NOT_RUN及所有原件/角色保持。

新增独立`memset_same_capture`适配器、固定Detours4.0.1/NVTX3.1.0记录器与一个0/64-byte微例。
只绑定目标共享CUDART普通导出，动态绝对路径/所属模块核验，无static/private/PTSZ覆盖声明；
真实SDK签名，原参数恰好一次转发，保存uint64 count/原return/线程LastError、PID/TID/创建实例。
唯一NVTX线程范围↔唯一runtime双向对应，再经目标Nsight2026.2保存AnalysisGuide所定义的
MEMSET→API表外键映射效果，禁止邻近配对/原生driver编号借用。微例的同步/D2H是范围外
预定读回oracle，不改变任何模型完成路径；0bytes不授无顺序影响，64bytes缺效果继续BLOCKED。

tests-first并实际运行：`python -m pytest -q -p no:cacheprovider tests/test_memset_same_capture.py tests/test_memset_micro_delivery.py tests/test_memset_micro_native.py --basetemp .local/memset_micro_release --junitxml .local/diagnostics/memset_same_capture_v0_1/release.xml --tb=short -ra`
显式本地MSVC/SDK配置，**54 passed/0 failed/0 skipped，10.93s**；完整微例/记录DLL真实头文件
编译链接且PE无CUDA导入，**未执行微例/DLL的CUDA路径**。Host函数/NVTX为明确替身，但
Detours attach/trampoline/detach是真实CPU执行，含大count、失败return、LastError、重入/错入口。
本地Python3.12.7/MSVC19.44/SDK26100，不冒称目标3.11.16/MSVC19.38/SDK20348资格。

完整PS5.1默认A演练exit0/54通过、封包与真实已审A SHA接线通过；显式B用采集器替身exit17
验证立即停止、原退出码/日志/失败ZIP保全，无side/SQLite/微例执行。Git边界/collector是替身，
不冒称真实部署或Nsight共存。实际源码/SDK byte、三份相关测试/必要静态检查完成，不重跑110项/
完整Q0。演练及JUnit在.local/diagnostics/memset_same_capture_v0_1；旧失败演练不覆盖。

交付前置由封存d6957de真实receipt确定；实现提交后绑定执行=分析commit及全部源码/依赖/工具链，
包与命令身份写入忽略交付说明，避免自引用hash。默认A只部署/编译/CPU/PE文件查询；必须先审
目标A原件和实际runtime字节，再凭该真实receipt SHA显式B，1native进程/1profile、0模型，
profile120s/export另120s，失败即停不重试。fresh输出/TEMP/TMP/归档卷预留0.25GiB、同卷去重，
历史总量null/UNKNOWN、长期50,000,000,000bytes目标尚未证明，不遍历/ACL/自动清理。

最高优先级/止点：仅交协调窗口审查唯一两阶段包及A命令，不启动B、不恢复旧7槽。
目标编译/3.11、实际ordinary导出命中、Nsight共存与context/trace stream/效果映射仍未验证；
任一失败就在微例停，不扩大hook、重编PyTorch、换工具链或追加模型。生产A/B/COE/registry/
冻结协议/原Formal无变化；用户DOCX修改与大型原件不纳入提交。

## 7.175 同次Nsight memset实例取证：接口级GO，仅限微例实现评审（2026-10-16）

本轮仅源码/SDK/接口审查与文档收口，无采集器实现、测试、包、服务器命令或CUDA/Nsight执行。
当前集中裁决：[既有可行性稿0.2增补](memset_parameter_feasibility_v0_1.md#2026-10-16增补同次nsight实例取证的有界裁决-02)。
复用7.174全部实例/关联结论，不再次查询旧SQLite；d6957de的B1 COMPLETE、B2 BLOCKED、
7 NOT_RUN、0完整block不变，参数不能由未来实例回填。

只比较两路：固定Nsight已核验API覆盖/内存/栈接口不提供缺失count，路径a本轮NO-GO；
路径b为同进程实际cudaMemsetAsync入口的窄域Detours trampoline参数/原返回码记录，
以唯一call_id NVTX线程范围绑定同次Nsight runtime，再用合法correlation/driver桥审设备效果。
Microsoft v4.0.1明确固定commit e4bfd6b03e50de46b47abfbd1e46b384f0c5f833；匹配CUDA12.4头文件
确认ABI，NVTX只作显式调用范围，既不冒充correlation也不用最近时间配对。无第二CUPTI subscriber。

**GO是技术接口级、可进入最小微例实现评审，不是目标机通过或模型/COE准入。** 私有/static
runtime、副本/PTSZ、Nsight共存、实际native stream↔trace stream/context及全部实例覆盖均未验证；
每条runtime必须与侧记录一对一，任何缺口停，不扩展通用hook或关闭Nsight来追绿。
count0只证明零字节参数，不证明无顺序/隐式效果；零字节无activity准入若要变化仍需另审窄规则。
count>0有合法效果桥才可继续现门；无效果仍BLOCKED。身份/边界/drain/依赖/terminal不删。

唯一未来验证设计是同栈一个native进程/一条profile内0/64-byte两case，独立sentinel/读回预期，
oracle同步与D2H位于被测调用范围外；非零必须有明确64-byte效果桥，不能由读值代替关联。
本地原型审查投入封顶1～2工作日为止损预算，后续目标验证120s硬上限、15分钟/0.25GiB估计，
均未执行/未授权；失败、唯一绑定或共存不成立即停止该路线，不追加模型批次。

本地核固定安装UserGuide和12.4 SDK字段/小文件hash；公开第一方Detours/NVTX/CUDA接口核对，
固定Nsight2026.2归档网页不可读，版本依据使用既有安装原件，不借滚动新版本推断。
下一项仅是集中审该微例的最小实现投入，当前无用户服务器操作。Gate13限定PASS/Gate14
NOT_RUN、旧Formal/Raw/报告/BLOCKED、UNKNOWN/NOT_ASSESSED与用户DOCX均保持。

## 7.174 COE候选Pilot B2 Prefill缺效果：本批BLOCKED，停止剩余7槽（2026-10-16）

本轮仅本地只读审计和文档收口，不改生产代码、合同或质量门，不制作新包/命令、不操作
服务器/模型/CUDA/Nsight，不重跑完整analyzer/Q0/测试或恢复旧参数/CUPTI追索。
当前集中依据：[主报告§13](completion_operation_batch_prefill_review_v0_1.md#13-d6957de候选pilot失败收口b2-prefill缺提交效果不续剩余槽位2026-10-16)。
原ZIP coe_d6957deeb588_pilot.zip为8,738,786 bytes，SHA256
3f4b6bd63b6ced66612f462b8344106a7d060418255ae8c936609238fd34a10f；181成员/180项清单，
manifest 3c911d66442e656fc5b8c5087630783d339dec20e62e7a2be8ad98a2516bc59d。
独立核包身份/安全唯一覆盖，复用协调全CRC/180hash；实际消费24成员再核hash/CRC。
执行/分析d6957deeb588cc125bf386d8ae07620ea35e14e3；新A READY、组件复用和空间READY，
历史总占用仍null/UNKNOWN。本次不是Storage或旧warning再阻塞，原历史报告不改。

9槽实际为**1 COMPLETE（B1）、1 BLOCKED（B2）、7 NOT_RUN；0完整block**。
B2目标PID66188 exit0、producer/execution COMPLETE，实际[2,512]、每样本2token、非early EOS，
tokens [[29184,29184],[6556,6556]]；profile30.485s/exit0/无超时、export PASS。
局部准入最早具体拒绝ENGINEERING_SCOPE_SUBMIT_MAPPING；外层COLLECTION_CONTRACT非根因。

B2 SQLite只读副本SHA5e5529ac94cae1426bca8d2ff47b8bbd119bc5aefca417688e3beaeb9c76a2f3，
与Canonical绑定一致。Raw→Canonical：41,523 API、13,520 kernel、348 memcpy、120 memset
全部逐rowid及关键字段一致，无过滤遗漏。46表schema/全部6个correlation列中，168个缺口
只命中API自身；driver类别也已包含，不是未查独立DRIVER表。无同线程嵌套/包含API桥、
无重复runtime关联，callchain全部null、无实参/外部关联表，不能按时间邻近或corr递增补图。
84条缺口实在Prefill [22936806408,23033553142)ns内，另84条Decode；首条runtime37514/
corr173737在起点后2.580762ms，不能按未来Decode隔离。已有submit分类不等于效果已证明，
不改non-submit/Host、不给unknown补零，不发布B2可信A/COE或跳过前缀。

B1原局部候选结果保留：Prefill95.904337ms、COE5.088286ms（kernel5.048510/MemOp0.039776ms），
GPU活动union29.088835ms；仍单次Pilot、非Formal，不与旧样本拼block，不支持负载差或重复性。
最小缺证是本次84条Prefill native调用的明确效果/身份scope关联，或可证明无设备提交的
实例参数与条件。现存接口不足，**无合同内消费修复可让旧B2通过**；不声称已证明真实零长度。

最高优先级/停止点：保持B2与批次BLOCKED、7槽NOT_RUN，不重试/续跑/替补或同配置盲采；
若未来再讨论，必须先给出能回答上述实例命题的有界证据方案，不恢复泛化追索/新设施。
新审计脚本/JSON/逐条CSV仅在.local/diagnostics/coe_d6957_local_failure_review_v0_1；
原ZIP/Raw/协调审计/失败报告与用户DOCX保持，Gate13限定PASS/Gate14 NOT_RUN及旧角色不变。

## 7.173 已批准存储分离接线完成；新两阶段包待A回执审查（2026-10-16）

本轮按用户接受§11的决定实现，不再停于运维政策待审；未操作服务器/模型/CUDA/Nsight。
详细当前入口：[主报告§12](completion_operation_batch_prefill_review_v0_1.md#12-已批准存储政策的两阶段最小接线2026-10-16)。
新增[资源检查](../../scripts/coe_startup_storage.py)与[组件复用](../../scripts/coe_delivery_reuse.py)，
只替换[launcher](../../scripts/run_coe_candidate_pilot.ps1)存储/证据复用接线及必要回执绑定，
科学runner、Canonical、局部Prefill/COE、A/B和registry均未改。

启动查实际输出/TEMP/TMP（可选TMPDIR）/归档父目录的fresh空闲与写入，volume GUID同卷去重；
每个参与卷12GiB，不加总；未知/不足/写入失败、旧输出/ZIP/reparse拒绝。无历史目录遍历、
ACL、旧补证调用或自动清理。历史YLQ总量null/UNKNOWN，长期<50,000,000,000 bytes尚未证明，
随新回执保留，**本身不阻断当前启动资源检查**。只删除独占新建的微小写探针，不删证据。

复用原4f1静态ZIP的110 CPU/compile/真实3.11.16两helper子证据，不改原BLOCKED或旧包。
新提交构建后精确比较全部311旧源/合同Git内容，并由原source_bytes的已核验表示与当前实字节
复核；模型/输入、plan/analysis合同hash和设备/解释器配置固定。新launcher/新增运维代码及测试
单独锁定新commit的精确blob，不再要求等于旧executed.ps1；新包带原ZIP和组件兼容证明。

本地最终命令：
`python -m pytest -q -p no:cacheprovider tests/test_coe_startup_storage.py tests/test_coe_delivery_resources.py --basetemp .local/coe-resource-release --junitxml .local/coe-resource-release.xml --tb=short`
本地3.12.7/PS5.1，最终**28 passed/0 failed/0 skipped（120.02s）**，见该JUnit及交付local_validation；
相关py_compile、源码科学目录zero-diff、文档链接与diff检查通过。
原launcher解析/旧stage_a_only禁采三项定向保护**3 passed/0 failed/0 skipped（2.49s）**。
不是重跑110/完整Q0或GPU资格。实际执行PS解析/文件hash/真实封存ZIP消费/安全新ZIP封包及
一次本地真实volume查询；部署/git状态、CPU命令分派、collector/九槽模型调用和故障磁盘是
明确CPU边界替身。中间错误保留：PS7继承模块路径、内存ScriptBlock上下文、测试夹具控制字符；
均修在测试边界，不删反例、不放宽身份。合同hash冲突先红测，补兼容比较后精确拒绝。

新包默认A仅固定版本部署、变更28CPU/相关compile、兼容和fresh空间；结束回传待审。
B严格要求本次已审A receipt实际SHA，核验A完整清单/delivery/storage/reuse，并再次fresh查
来源/空间；旧BLOCKED/hash或错误版本不放行。真实B命令仅A审查后再给，当前不提前提供。
旧stage_a_only交付永久历史不解锁。新提交后才写交付commit/hash和bundle，无自引用。

仍固定9 P1/9profile、三个位置平衡block、512/每样本2、batch1/2/4、w3/r1、自然完成、
FP16/eager/SDPA，无P0/Cpre，完整输入/mask/token/drain/依赖/诊断质量门均不变；
仅局部Prefill、无巨型domain，无重试/替补/追加。15～30分钟/新增约0.1～0.5GB为估计，
临时预留12GiB，长期容量归档后另行核验/精准清理审查，历史未知不当零或删除依据。

最高优先级：交协调审查唯一新包与A整段命令，由用户执行A后回传单ZIP；不跑九P1。
新存储/兼容接线目标3.11实际结果和目标fresh空间待A，batch2 GPU实物与九run局部闭合仍待
后续显式批准B回答；不是提前判Pilot/研究增益成功。Gate13限定PASS/Gate14 NOT_RUN、
旧Formal/Raw/UNKNOWN/NOT_ASSESSED/BLOCKED和用户DOCX保持。当前交付身份保存在私有
`.local/coe_storage_delivery_identity.json`及`.local/COE_STORAGE_DELIVERY.md`，不把文档HEAD当服务器实物。

## 7.172 本地绑定修复完成；启动空间与长期留存分离，入口调整待审（2026-10-16）

用户本轮授权最小本地修复/真实包回归及存储执行含义纠正；未操作服务器、模型、CUDA/
Nsight，不发命令、不制作包、不改ACL/删除/提权或继续权限追索。
当前结论集中于[主报告§11](completion_operation_batch_prefill_review_v0_1.md#11-本地绑定修复及存储执行含义纠正2026-10-16待协调审查)。

新增[绑定模块0.2.0](../../scripts/coe_storage_binding.py)，无CLI/扫描/采集。Python两源按
真实封存source_bytes.json；PS按同ZIP executed.ps1及既核验11714 bytes/SHA99ba960b…28d6b47，
之后严格比较当前实字节，不归一化或运行hash自认证。原ZIP/manifest/receipt固定hash、
当前HEADclean/精确Python门保留；缺失、重复、篡改和原receipt变化有明确拒绝与冲突详情。
原已执行0.1脚本/ZIP/BLOCKED保持历史，不再补跑它；生产launcher/S/A/B/registry未改。

先用封存失败ZIP里的真实原代码运行成功夹具，得到1 failed（StopIteration），不是猜测；
修复后命令：
`python -m pytest -q -p no:cacheprovider tests/test_coe_storage_binding.py --basetemp .local/storage-binding-final --junitxml .local/storage-binding-final.xml --tb=short`
最终实际**20 passed / 0 failed / 0 skipped（7.84s）**；
相关py_compile通过。真实静态ZIP、原receipt、固定4f1 Git字节，只有目标Git状态与Python
3.11.16元组为CPU边界替身；本地3.12.7，不冒称目标验证。110 CPU/compile/目标实际3.11
及311源码原通过证据复用未重跑。小型本地审查产物coe_storage_binding_v0_2/review.json。

**计划调整（纠正7.170的过强执行前置）：**长期目标是归档后YLQ保留<50,000,000,000 bytes，
临时可超出；不是每次科研启动前完整扫描历史树。启动应新查实际卷free及本批12GiB临时
预算，本批新增/最终保留量另记；历史总量和不可读部分仍UNKNOWN/尚未证明达标，不将未知
算零，也不把历史目录不可读自动作为本批科学不合格。当前launcher仍有全根Storage硬门，
**本轮未改**，只交入口分离方案待协调审查；旧stage_a_only包仍禁止采集，旧BLOCKED不重判。
一次补证free349.59055GiB只代表原时刻，不可用作未来启动许可。

仅复用旧batch-load ZIP目录元数据估算：不含巨型domain/重复export的B1/B4展开为
9,175,273/6,203,231 bytes，九倍较大者82,577,457 bytes只是尺度参考非上界；B2未实测。
本批新增/最终归档约0.1～0.5GB量级估计，临时预留仍12GiB，实际另记；不生成domain，
不据此保证历史50GB目标。核验归档后再评估可恢复重复副本，清理另审，本轮无清理。

最高优先级：协调审查一次“fresh free/临时预算是启动门、长期容量是归档后管理”的入口调整；
通过后仅补Storage接线及新版本/交付绑定，复用110项，不再全A/权限追索；Pilot仍须显式
授权，9P1逐run质量与局部闭合硬门不变，batch2真实支持待证。无测量/冻结规则或Formal资格
变化，Gate13限定PASS/Gate14 NOT_RUN，用户DOCX、Raw、历史UNKNOWN/BLOCKED保留。

## 7.171 存储补证回传：消费者清单绑定错误，权限查询到此为止（2026-10-16）

本轮只读核验新7070-byte ZIP，SHA256
88e527a15d6a970a448b1c438349891c83e56d0b8ea8949468482aab2f519409；4成员/3项清单、
安全路径/CRC/hash/覆盖通过，manifest SHA
ad888e08a881be6d1557bc3b0a89c845adfbb57e0db9b411ce204c96f3dbd07e。
详见[现有主报告§10](completion_operation_batch_prefill_review_v0_1.md)。
原status BINDING_OR_QUERY_BLOCKED_STOP_FOR_REVIEW，error.type=StopIteration。
原因是补证脚本误到311项Python/JSON源清单查PowerShell launcher；两Python各1行，
该.ps1为0行，唯一next()空匹配，本地原清单已复现。不是本次又遇遍历WinError5或采集错误。
说明此前诊断验证缺少真实归档的成功绑定路径；不弱化身份门或把实际hash回填为期望。
当前Git/历史盘点/占用遍历均未执行，storage=null，不能将它们当作通过。

已取得独立事实：2026-10-16T06:23:02Z前后free均375369994240 bytes（349.59055GiB），
满足当时临时12GiB；不是当前/未来空闲保证。admin_token=false，祖先3级ACL可读，
pytest_full_tmp自身ACL UNKNOWN（0x80070005）；不能推断为空、大小、枚举结果或管理员可解决。
YLQ总量仍未知，长期低于50,000,000,000 bytes尚未证明，不将空闲充足替代总量要求。

一次权限补证结束，不再发权限/提权/逐目录查询或服务器命令。本轮未修改诊断/业务脚本，
无新测试或GPU/实验；只做原归档核验和原lookup独立重现。原件/报告不改，旧命令撤为历史。
后续最小本地修复设计：.py走source_bytes，.ps1单独绑定封存executed.ps1/固定Git内容及
当前实字节；先补真实归档成功/缺失/重复/hash冲突覆盖，再决定未执行的存储取证必要性。
不自动安排重跑，且绑定修复不等于ACL未知解决。此前110 CPU/compile/真实3.11/helper
继续复用；COE/生产A/B/数据角色、Gate13限定PASS/Gate14 NOT_RUN、UNKNOWN/BLOCKED及DOCX不变。

## 7.170 COE目标静态实现项通过；独立存储补证待审（2026-10-16）

原件coe_4f1c3b55caf3_static.zip，85783 bytes，SHA256
b062b9502e2796cdbd91b47a1d0de17c549062036cc361948a9d6d131e8e13bc；本地独立核验
20 ZIP成员/19项清单、安全路径、CRC/全部hash/完整覆盖，manifest SHA256
d2e11bfb636eae91be0ba754a019b1ae6571c8c7316a6617122fdd3bcb1e66c0。
当前[主报告§9](completion_operation_batch_prefill_review_v0_1.md)集中说明；原报告保持BLOCKED。
最近可信执行/分析为4f1c3b55caf33cd669aeee05e95be98c96ef0e11；311源码实字节匹配，
目标**110 passed/0 failed/0 skipped（JUnit45.466s）**、compile exit0、实际Python3.11.16
新旧helper身份通过，旧7.169“目标3.11待证”已关闭。无模型/CUDA初始化/collector。
不重跑这组CPU/Stage A，不因静态子项通过授Pilot/GPU资格。

唯一失败是Storage读取历史gate7静态预检的pytest_full_tmp发生WinError5；旧onerror
立即raise，未记录累计值、未查询disk free、未产生storage.json，故两项数值均未知。
已查本地既有存储说明/清理方案/交接：历史盘点两项异常的原始路径明细未取得，不能
认定就是同目录，也不能从pytest名称判断为空或可删。旧总量与清理后估计不作当前证明。

本轮只准备一次独立只读补证命令，脚本/准确路径保存在.local/coe_storage_evidence_once.ps1
及同主题私有说明；无新部署包/checkout/采集入口，不改生产代码或存储门。
绑定原ZIP/manifest/旧receipt、当前HEAD/clean及三份相关源码；复用已通过110/311/helper。
记录当前token/四级ACL、有限读取旧盘点原错误/summary（最多64项、单报告1MiB/合计4MiB），
再做一次YLQ文件元数据遍历（300s/500000项软预算），收集所有已发现错误和未扫描frontier。
不读取大Raw内容，不改ACL/takeown、不自动提权、不删除、不追索进程或逐目录重试。
已观察文件逻辑长度之和只能作相应口径的下界，不是NTFS实际分配或原子快照；未知子树
字节保持null。磁盘空闲前后独立查询，临时12GiB与长期<50,000,000,000 bytes分开。
不可读/预算耗尽时，长期目标仍未证明；错误/冲突回执照常保存为新的诊断ZIP，不改旧BLOCKED。

本地仅新增诊断逻辑的六项小型检查通过（0失败/0跳过，0.72秒），PS5.1真实解析、仅本地
fixture权限片段及错原件绑定的实际入口保护通过；无110/Q0/实验/完整分析重跑。
本地审计与命令验证：.local/diagnostics/coe_storage_review_v0_1；不是服务器权限或空间实测。
当前最高优先级：协调审查这一次存储命令，用户如执行则回传单ZIP；若仍不可读，停止
权限追索，集中保留“YLQ低于50,000,000,000字节尚未证明”，不自动续A/B或修改质量规则。
COE/生产A/B/签署Formal不改，原Raw/UNKNOWN/BLOCKED及用户DOCX保留；Gate13限定PASS，
Gate14 NOT_RUN，候选Pilot尚未采集。本轮无服务器操作。

## 7.169 COE静态失败的AST结构身份兼容修复（2026-10-16）

从7fcdb2f继续，用户仅授权本地诊断/最小修复/CPU/待审Stage A包；未操作服务器、模型、
CUDA/Nsight或采集。当前说明集中在[原主报告§8](completion_operation_batch_prefill_review_v0_1.md)。
原静态ZIP 87027 bytes、SHA ae7fb5d98976f49eb2b6d942d86741faae59699a68c9351de046abc6dccdcfac；
CRC/安全路径/14项清单完整覆盖/hash通过，manifest SHA
647b00213b4c1cc5c9e118a5402fe740d14d911e86cdf1c2cadb96a7853d37eb；308项源码实字节匹配。
CPU78通过/11失败/0跳过，均COE_HELPER_PROFILE_OUT_OF_SCOPE；原BLOCKED不改，无模型/采集，
compile尚未执行。最近可信服务器前置已是7fcdb2fa3952fc61926d3ac3fd38356c294c866b，不再沿用48567aa。

根因：未版本化的ast.dump格式混入身份。实际3.10.19/3.12.7/3.13.1对同源码dump不同；
3.12新增空type_params，3.13又省略空列表字段。未发现可用本地3.11，结构模拟不冒充目标实测。
完成[独立身份模块](../../analysis/coe_helper_identity.py) coe-helper-structure/0.1.0与
[分析兼容0.2.1](contracts/coe_candidate_analysis_v0_2_1.json)：闭合节点/字段、固定JSON编码，
仅容许空type_params缺省，未知/非空字段和行为变化拒绝。期望分别绑定旧2af14b1及新7fcdb2f
真实Git源码内容，不接受incoming hash作期望；旧合同/产物保留，新输出另带helper_identity和Python。
源码实字节、角色、manifest/输入/token、设备/drain、依赖、诊断与局部准入检查不删不改。
生产A/B、registry、runner、COE科学定义和九P1矩阵无变更，不影响旧冻结Formal。

先红测新结构/行为与Stage A采集禁止门，再实现；最终命令：
`python -m pytest -q -p no:cacheprovider tests/test_coe_pilot.py tests/test_coe_pilot_driver.py tests/test_coe_candidate.py tests/test_coe_helper_identity.py --basetemp .local/ast-chain-delivery --junitxml .local/ast-chain-delivery.xml --tb=short`
实得**110 passed/0 failed/0 skipped，65.53s**，本地3.12.7；真实文件链负例精确核对拒绝原因。
compileall analysis、相关py_compile、Windows PowerShell5.1实际解析及diff检查通过。
两profile在实际3.10/3.12/3.13隔离进程结构一致，真实行为改动拒绝；不是3.11或GPU资格。
封存原件轻回归输出regression_ast_identity_v0_2_1，共30条全部成员/交集算术MATCH；
B1/B4 Prefill仍1.782176/30.910044ms、四token仍448/24032/480/1376ns；旧B4 Decode仍拒绝。
本地审计及中间失败保留coe_ast_identity_v0_2_1与ast-*，无完整Q0/旧大分析/新实验。
交付前实际3.10发现非空type_params负例的夹具会因实例_fields属性提前拒绝；改为明确
AST形状，再于实际3.10/3.12/3.13核对五种精确拒绝。中间5cbf788包撤回不交付，最终包
绑定后续夹具/记录修正提交；生产模块、测量与30条旧结果未再变化。

当前最高优先级：提交后绑定新执行=分析commit，提供单一待审增量包（前置7fcdb2f），
新输出目录，只重做A。包stage_a_only=true，即使显式Collect也拒绝；新增真实目标3.11.16
stdlib只读两helper回执，记录实际Python/原AST/新结构/源码hash，不导入runner或CUDA。
旧BLOCKED/静态报告和成功身份不复用；目标CPU、实际3.11/空间仍待新A回执审查，Pilot未采。
长期YLQ严格<50,000,000,000字节、临时空闲12GiB分开，不安装依赖、不升级Python、不自动清理。
Gate13限定PASS/Gate14 NOT_RUN、UNKNOWN/NOT_ASSESSED、历史角色/Raw及用户DOCX不变。

## 7.168 COE候选Pilot真实执行接线与两阶段待审交付（2026-10-16）

本次从207bdf2继续，用户授权本地实现/CPU/打包；未授权服务器、模型、CUDA/Nsight或采集。
完成[独立执行域](../../exposedpath/coe_pilot.py) `COE-NATURAL-PREFILL-PILOT/0.1`、
[局部分析链](../../analysis/coe_pilot.py)、[九槽编排](../../scripts/coe_pilot_batch.py)及
[待审执行配置](../../configs/coe_candidate_pilot_execution_v0_1.json)。复用verified prepare/seal/
显式解释器/collector/producer/Canonical与原局部Prefill S/A；COE分析入口增量版本0.2.0，
[兼容合同](contracts/coe_candidate_analysis_v0_2.json)保留0.1原合同和旧helper指纹。
没有改生产S/A/B公式、registry、旧Formal协议或历史结果。旧7.167不打包/不可执行状态为历史；
本次只将新执行链准备为待审交付，不是采集授权或新资格PASS。

新域固定batch1/2/4、512/每样本2、w3/r1、FP16/eager/SDPA、自然Host-readable完成。
逐run绑定完整二维input_ids、attention_mask、batch payload及文件字节摘要；对实际送入
tensor构造的Host列表独立观察并比对，输出形状/每样本token由真实producer结果取得，
不以单样本digest或复制manifest冒充实际batch身份，不增加D2H/同步。旧Pilot/Formal
重复样本门保留；只有完整新绑定允许这次已批准的同输入克隆，batch2不扩展旧G1。
当前runner保留可选Cpre钩子但本域禁止controller；自然分支与旧路径相同，新指纹显式绑定。

每run执行Canonical→边界/成功drain→局部Prefill准入→COE→严格报告/hash消费，不走巨型domain。
原有两模式成员/依赖边、ownership、terminal、诊断与前缀检查均保留；完成后的缺效果调用
必须同线程同clock且开始于首token锚点之后，并通过无incoming event/graph等局部闭合门。
它们逐项留在覆盖与隔离记录；Request/Decode仍NOT_ACCEPTED，UNKNOWN/NOT_ASSESSED不变。
固定三个位置平衡block 1→2→4 / 2→4→1 / 4→1→2，9新P1；完整block的B4−B1 signed绝对差，
保留B2、零/负/反向及全部单次值；首硬失败停，保存完成/失败/未运行槽，不拼接、不重试/替补。

先红测缺入口、克隆域、实际构造mask冲突、软件身份与完整文件链，再实现。最终命令：
`python -m pytest -q -p no:cacheprovider tests/test_coe_pilot.py tests/test_coe_pilot_driver.py tests/test_coe_candidate.py tests/test_runner_token_ready.py tests/test_batch_load_diagnostic.py tests/test_gate11_pilot_files.py tests/test_gate12_formal.py --basetemp .local/cp-release --junitxml .local/cp-release-results.xml`
实得 **205 passed / 0 failed / 0 skipped，174.44s**。含真实prepare、seal→profile argv、实际producer
文件→collector post-export分派→Canonical/局部Prefill/COE/消费，以及九槽whole-block编排的CPU边界替身。
compileall、diff检查及实际Windows PowerShell5.1解析通过。本地Python3.12.7，目标3.11.16；
这些是CPU文件链/算术/拒绝证据，不是目标CUDA或batch2实物资格。不重跑Q0、完整旧分析或GPU。
提交前用0.2入口做轻量旧原件回归：24自然链、同批B1/B4 Prefill及四token，共30条
成员/terminal/交集算术均MATCH，逐run约2.1～3.6秒；B1/B4仍1.782176/30.910044ms，
四token仍448/24032/480/1376ns。新派生目录regression_pilot_wiring_v0_2，不覆盖旧结果或运行完整analyzer。

最近可信服务器回传HEAD为48567aa890bfd7f101ebf7b6b720308b4b48e20f，来源是已核验native_stage1
回传中的部署receipt及最终git_head/clean原日志；不是假定当前checkout。交付在提交后从实际
commit生成增量bundle并绑定执行=分析、源码精确Git/LF及合法CRLF表示与输入，避免自引用。
默认[阶段A](../../scripts/run_coe_candidate_pilot.ps1)仅部署/必要CPU/空间检查；B另需显式开关和
已审查A原receipt实际SHA256，不能凭本地测试自动采集。当前最高优先级仅协调审查交付、
用户执行A并回传；目标实际HEAD/软件/空间、batch2与新run局部闭合仍未实测。

预计总15～30分钟仅规划估计，单profile300s、单run driver900s保留硬限；临时空闲12GiB。
**长期YLQ目标统一为严格低于50,000,000,000字节，不是50GiB**，取代7.167的旧单位表述。
A/B记录实际空间，不自动清理；归档门遇UNKNOWN writer仍拒绝封包。采集后只保留必要Raw/
Canonical/小型来源与局部结果，不重复展开或生成domain。已有Gate13限定PASS、Gate14 NOT_RUN、
历史数据角色/Raw/BLOCKED及用户DOCX不变；不启用P0/Cpre/引擎/CUPTI、Pilot统计冻结或Formal。

## 7.167 COE可复用本地入口、成员级回归及待审9P1配置（2026-10-16）

用户接受“自然完成操作内必要设备活动结构”的有限科学对象，不将COE视为纯Host阻塞
或其近似；结束概念评审，授权最小本地实现/验证和机器配置，不授权服务器/采集/打包。
新增独立[候选入口](../../analysis/coe_candidate.py)版本coe-candidate-analysis/0.1.0及
[接口合同](contracts/coe_candidate_analysis_v0_1.json)，复用严格receipt/Canonical、producer/
token/设备桥接、现有FIFO后缀和官方诊断处置，不调用生产A/B或巨型domain。计算不依赖
旧run/CSV/固定record ID/最长copy；helper AST限定实际已审路径，旧答案仅在回归驱动比较。
[现有主报告§6](completion_operation_batch_prefill_review_v0_1.md)
为当前说明，不另起重复流程。原COE草案SHA0dd73d0f…0927a8、生产schema/registry/冻结A/B不变。

新增完整逐run操作/API覆盖；[公开示例](completion_operation_coverage_examples_v0_1.csv)21行，
[机器汇总](completion_operation_reuse_validation_v0_1.json)含30条回归和14个run覆盖计数/hash。
24条G32/G512链、同批B1/B4 Prefill、原四token的必要成员/闭合历史/未来排除及算术均复现；
B1/B4仍1.782176/30.910044ms，四token仍448/24032/480/1376ns。B4 Decode保持null及具体
SUBMIT_EFFECT_MISSING（runtime38606），覆盖明确84项缺效果、2项已配对但未准入组件；
不追索参数、不发布B4可信Request/Decode、不改原BLOCKED。计算正确性、操作适用性及
尚未证明的纯阻塞/收益/可重复性/分析增量分别报告；同I普通GPU union相同的限制保留。

先补缺口红测，再最小实现。最终命令`python -m pytest -q -p no:cacheprovider
tests/test_coe_candidate.py tests/test_completion_operation_candidate.py --basetemp .local/tmp/coe_release_context_verified`：
72 passed/0 failed/0 skipped，18.68秒，本地Python3.12.7；相关py_compile通过，不代表CUDA资格。
最后审查发现调用方N1 opaque上下文可泄漏到分类；红测后显式绑定原A registry 0.1.0，
不继承该例外，未改生产规则。封存回归driver最终输出regression_release_v0_1，每run约2～3.5秒，原件/源码hash前后复核；
独立源及新输出另存.local/diagnostics/coe_reusable_v0_1，不覆盖旧结果。初始Temp路径、
零值fixture terminal并列等诊断保留，未弱化terminal门或改测试追绿；只修了错误fixture。

[待审配置](../../configs/coe_candidate_pilot_v0_1.json)锁定512/每样本2、batch1/2/4、w3/r1、
三个位置平衡完整block、9个全新P1；固定B4−B1绝对signed差、B2/全部样本及公平baseline，
完整block统计、不混旧数据、不按零/反向/不确定自动补采。状态PENDING_REVIEW_NOT_EXECUTABLE，
execution_commit=null；只有配置，不是新runner或执行授权。实证重复性与分析用途分开评价。
真正剩余仅未来Pilot角色/batch2及局部Prefill消费者的producer/receipt接线、固定执行/输入身份审查及届时目标机
checkout/空间事实和显式执行授权；不自动要求新完整Q0、引擎/设施或模型实验。粗估总操作
15～30分钟（非承诺），300s/profile硬限下采集本体上限45分钟，临时12GiB，长期YLQ<50GiB
目标但实际余量未知。本轮无包/服务器命令/清理。用户DOCX/大原件、UNKNOWN/NOT_ASSESSED、
Gate13限定PASS/Gate14 NOT_RUN及所有原数据角色不变；最高优先级仅审阅本地交付与剩余接线。

## 7.166 完整指令补齐：同批B1/B4占比与来源时间线（2026-10-16）

用户补发完整任务，唯一对象仍为2af14b同批B1P1/B4P1局部Prefill；不以C0/Cpre替代。
复用7.165已闭合的适用性/成员/独立算术及538片段overlay，补齐同一
[审查报告](completion_operation_batch_prefill_review_v0_1.md)的13项绝对值/统一Prefill分母占比，
新增[来源时间线](completion_operation_batch_timeline_v0_1.csv)与图，包含copy/D2H/sync、
最后必要kernel及launch、原Host结果之后的trace point；原ns/clock和显示偏移明确分开。
本轮只复核选定Raw和显示，不重跑成员恢复、S/A/B、Q0或完整分析。原结果SHA667aa462…，
原预算/538片段CSV的SHA51b4dc4b…/2bb39632…保持；固定草案也未改。新显示命令exit0，
图目视、比例/来源/链接/diff/隐私与单脚本py_compile通过，不新增GPU/pytest资格。

结论仍是候选操作可作有支持假设的探索：1.782176/30.910044ms、1.780104%/20.257246%；
旧配对sync交集均0，同I普通GPU union与COE相同，不声称独占信息或纯Host阻塞。有限重复
值得审查的是本次“活动/包络/暴露不同响应”能否复现，不是为了获得较大占比或胜过完整
timeline。九次建议仍未授权，本轮不推进点位接线/采集包/新预算，仅收齐已有数据交付。
原B4 Request/Decode/BLOCKED、UNKNOWN/NOT_ASSESSED、Gate13限定PASS/Gate14 NOT_RUN、
Formal/Raw及用户DOCX保持。无服务器步骤或新设施，7.165实算与历史建议保留。

## 7.165 自然B1/B4 Prefill的COE候选实算与研究决策（2026-10-16）

用户授权从098efde继续本地事后分析，不停留于合同审阅；同时质疑负载点数和研究可信度。
完成[两条件演算及集中建议](completion_operation_batch_prefill_review_v0_1.md)、完整数值/预算、
538片段CSV与图。固定COE-CANDIDATE/0.1.0-draft字节，未签署或改生产A/B，不继承99f资格。
复核原ZIP/清单身份，复用旧全包CRC/hash，只校验实际消费成员及原receipt/源码/producer；
2af14b真实helper与99f同函数AST相符，但Engineering角色、batch4/32-byte及独立实例单列。

在既有局部准入上核对成功drain、10827/10491条历史、1905/1821成员、唯一terminal、
LEGACY/PER_THREAD成员和边、实际流/设备/时钟/配对成功sync及Host token。已完成成员保留，
以sync捕获提交边界纳入操作内D2H、排除未来；未追查84参数或借Decode拒绝污染Prefill。
候选B1/B4交集1.782176/30.910044ms，kernel1.781280/30.867774、MemOp0.000896/0.042270，
占原Prefill1.780104%/20.257246%。原配对sync交集仍0，不称旧A计算错误或纯Host阻塞。
旧Prefill Device wait0.525502/0.025024保留；预算迁移只从submit扣除，预览完成暴露
2.307678/30.935068ms（2.304995%/20.273646%），总长/API父子逐ns守恒，Host/non-submit/
residual/U不动。独立事件扫描/反向重构通过，28个实际来源后验hash未变，图已目视检查。

每点仅一个P1，证明的是实例条件和区间，不证明负载规律；更多配置不能替代独立重复，
旧Formal/Engineering不可混池。唯一研究建议继续自然完成操作的条件化暴露解释，不扩
“全部GPU阻塞”；完整timeline可恢复同信息，论文级增量尚待公平对照/重复验证。
额外实际核对同I内全部目标GPU活动union，两个条件均与COE逐ns相同；当前单FIFO没有
依赖过滤的数值优势，不将API聚合对比夸大为胜过同窗timeline。后续仅检验实证重复性，
若坚持算法独占信息，当前九次建议不能回答该问题，不应以此批准采集。
待审最小建议是固定512/2自然路径batch1/2/4×三个平衡block，共9个P1，仅作结构筛查；
不是当前预算/采集授权，不生成部署包/服务器命令，不做P0迁移、完整Q0或大矩阵。
若仅是API重标度/单次波动且无额外来源判断，停止扩大主张；不为显著性/占比追加。

本地脚本本轮exit0，阶段约1.017/4.122s，独立算术/CSV/来源/角色/链接/diff/保全及
三脚本py_compile为验证，不新增pytest数量/完整分析或GPU资格。初稿NVTX point/pop顺序
及呈现字段读取错误保留诊断后按实际源修正，生产代码未变。原B4 Request/Decode/attempt
BLOCKED、UNKNOWN/NOT_ASSESSED、Gate13限定PASS/Gate14 NOT_RUN、用户DOCX及Raw保持。
当前下一步仅协调审查这一个有界验证建议，无需用户现在操作服务器。

## 7.164 候选合同0.1与24链预算迁移预览完成（2026-10-15）

用户认可独立完成操作对象，仅授权合同设计及既有数据的事后预算预览。完成
[COE-CANDIDATE/0.1.0-draft](completion_operation_contract_draft_v0_1.md)及
[完整演算/图表/科学限制](completion_operation_budget_preview_review_v0_1.md)。配对/成功保证、
copy入口→paired sync返回、sync捕获提交截止、完整W/局部后缀、有效性/profile/解释限制分开；
不是单copy同步保证或纯GPU阻塞，不改生产A/B/registry/冻结协议，不自动恢复旧路线B。

复用四token独立预设及原24链成员/资格，只读12个封存G32/G512 SQLite与小型旧A审查；
没有重跑完整analyzer/Q0或恢复集合。逐Raw成员/提交/实际scope验证、原类别来源和区间检查后，
24链全部候选片段均位于copy API内，与所有目标同步API包络不交；据旧E定义证明无重复覆盖。
新153原子片段全来自CUDA API/submit，36个旧窗口只作同墙钟扣减与completion_exposure预览
增加；Host/non-submit/opaque/residual/U不动，父子守恒与Request=Prefill+Decode逐ns成立。
完整24链/36窗口/153片段公开CSV相互绑定，不把原Formal输入角色冒充新Formal结果。

首token交集中位数G32 0.672139ms、G512 1.642275ms，六block差均正；第二token分别
0.618300ms、0.000448ms，G512−G32五负一正。新增来源以FIFO必要kernel前驱为主，不是
API−D2H；迁移仅占各Request原长0.574232%～1.403041%。完整依赖timeline可恢复同样信息；
数值变大/守恒/独立验证不单独证明创新、全部Host等待或优化收益。全部有效值和负向结果保留。

本轮独立审计exit0（12run/24token/36窗口/153片段），仅复用区间union算术，不调用生产S/A/B；
12个Raw SHA前后未变，原角色/UNKNOWN/NOT_ASSESSED/历史BLOCKED保持。另做整数反向重构、
已有手算重叠例、公开CSV/图表/链接/隐私/diff与用户DOCX保全检查；不新增/重跑pytest。
本地新派生目录`.local/diagnostics/completion_operation_budget_preview_v0_1/derived_v0_1/`；
preview SHA803b4ce7…60dd4b，草案SHA0dd73d0f…0927a8。当前停点仅审阅候选合同/独立overlay，
未签署、未授生产A改版或新Formal，单sync B不变；Gate13限定PASS、Gate14 NOT_RUN保持。
不需要服务器、采集包或新实验。7.163“未来迁移仅设计”的范围由本轮独立预览授权扩展，
其独立验证/历史边界保留，不改旧报告或用户DOCX，不将旧数据升级。

## 7.163 封存四token的操作层增量验证：可进入合同设计（2026-10-15）

用户认可独立的“复制—成功同步子包络内必要活动暴露”对象，仅授权复用封存
NULL-FIFO-D2H四token原件。完成[增量验证0.1](completion_operation_controlled_validation_v0_1.md)：
**操作层独立依据充分，可以进入版本化合同设计；不授生产A改版、自然阻塞解释或新Formal。**
不是恢复路线B，也不改变Gate13限定PASS/Gate14 NOT_RUN或原attempt BLOCKED。

先从原prepared/prompt、固定runner/native源锁定两request的copy→sync ordinal2→3/7→8、
token11/12/21/22、人工必要后缀{K1,C1}/{K1,C1,K2,C2}及terminal C1/C2，再读SQLite区间。
按完整identity/原operation NVTX/成功runtime/correlation验证，未调用候选集合恢复或生产
S/A/B。集合截止于配对sync捕获的提交边界，四次copy入口之后才提交的D2H均在集合；
历史warmup/前request的2/6条前缀保留、闭合，后提交排除。先验证成员非重叠再逐项手算
裁剪，与既有候选区间函数比较，身份/完成、成员、算术三层逐条相符，不以交集增大为准。

原sync/候选交集分别均为448、24032、480、1376ns；I墙钟56634、223673、56394、66860ns，
补集56186、199641、55914、65484ns。四条扩大包络后交集未增加，同样验证成立，不移起点。
源码和本SQLite枚举明确受控原件为Device→Pinned/4-byte，不能把它写成上一轮自然
Device→Pageable/8-byte子域已获完整新增资格。已验证的是组合对象结构与独立成员/算术；
可复用范围和Pageable特定资格需在下一版合同中分开，不默认新采。

澄清Host工作重叠不自动使固定配对/依赖无效，但不能称纯等待；身份/配对歧义、未闭合
前缀、失败同步、错误token及未知incoming则保持拒绝。未来A设计仅纸面集合迁移：先对
操作/成员union，新增片段从原API等预算重分配，保留未知，旧sync不重复计；本次四条
增量Δ全0，不可重复加预算。单sync B及冻结A/B保持原义，未实现任何生产改版。

本机独立目录`.local/diagnostics/completion_operation_controlled_v0_1/derived_v0_1/`保留
四行CSV、来源/原始区间JSON和审计脚本hash。仅复核实际消费12项旧源文件的hash及关联，
查询后全部未变；复用原全包CRC/清单、限定资格及既有反例，不重跑完整Q0/原analyzer或
31项旧CPU检查，不新增测试数量。没有服务器、模型、CUDA/Nsight、部署包或采集命令。
UNKNOWN/NOT_ASSESSED、所有原Raw/报告及用户DOCX保持；当前下一步只有版本化合同设计。

## 7.162 复制—同步完成操作候选：新假设的实际探索演算（2026-10-15）

用户单独授权有界的完成操作语义验证与现有Raw离线候选演算。不是自动恢复此前路线B，
也不将7.159/7.161的停止/技术报告结论机械套给新对象。完成
[候选审查及同页未批准草案0.1](completion_operation_candidate_review_v0_1.md)和
[24条数值CSV](completion_operation_candidates_v0_1.csv)：**A单个Async复制的独立返回scope
仍未证明；B复制入口→配对成功stream sync返回的完成操作子包络可定义、可计算。**
两者不能混同；B不称纯Host阻塞/优化收益或新Formal A，不重定义原Device wait。

演算前固定12个G32/G512 P1 run及24个token的唯一配对/范围和独立手算反例，明确已知
block1旧时序、不是盲选/预注册。独立复核指定SQLite SHA84d3a0c...70d87e：MEMCPY347
corr197682/bytes8，按该文件枚举解释Device→Pageable；runtime37815复制/37816成功sync、
physical354同流同context。头文件2.6.0+cu124真实字节SHA343d0c...d84a重新核对，官方
CUDA12.4.1只说Async Device↔Pageable可能对Host同步，不提供此实例内部等待真值。
复制加随后成功sync具有整体完成保证；原runner、输入receipt、token与ledger绑定保持。

独立只读SQLite脚本不导入S/A/B、torch或domain。以correlation→submit、同线程FIFO、
drain闭合及原两模式投影条件恢复本地必要后缀，保留已完成成员和全部Raw历史前缀ID，
排除后提交；不将该清单宣称完整物理W/B或全部token数学数据依赖。可见额外流/线程/
event/graph或缺映射拒绝，无未记录incoming依赖仍是显式支持假设。24链完成演算、
查询后12个SQLite hash未变，原身份/作用域资格复用，不重跑完整分析/Q0。

block1/G512首token：固定I总长1.910952ms，候选必要活动交集1.525365ms，其中kernel
1.524501、MemOp0.000864（D2H0.000544+memset0.000320），未覆盖0.385587；原token-ready
sync交集0。仅copy correlation会漏掉FIFO必要前驱；API全长也不能作等待。全部24链原
token-ready sync交集0、新交集均在copy API内；G512第2token五个block仅极短D2H，
保留另一block及方向变化。新数值为事后探索，不反写Formal统计或A；未声称新负载规律。
Cpre before_copy在natural NVTX之前，本轮没有共同起点的对照资格，不任意扩包络。

新增CPU独立反例包括有用Host工作、无关流、短D2H长前驱、早完成成员、GPU空隙和
任意改起点；证明候选不是纯等待，不以CPU模型冒充新CUDA资格。首次实际文件入口
因run级receipt与request级token身份结构不同拒绝；修为精确字段/共同身份/原签署引用
检查并补错role/run/request/reference反例，不以忽略字段追绿。原失败探索目录保留。

唯一建议：审阅窄域`COMPLETION-OPERATION-EXPOSURE/0.1-draft`，再决定是否以封存
NULL-FIFO-D2H四token的预设独立集合做最小操作层增量资格；当前未批准/实施生产
amendment、未授新资格，无服务器操作或新采集需求。全依赖timeline也能恢复相同结果，
本轮解释增量不等于论文创新；旧停止/成文记录和Gate13限定PASS/Gate14 NOT_RUN保持。
生产S/A/B/registry/冻结协议、Raw/原报告、UNKNOWN/NOT_ASSESSED和用户DOCX未改。
实际运行新独立脚本测试`python -m pytest -q -p no:cacheprovider
tests/test_completion_operation_candidate.py --junitxml=.local/diagnostics/completion_operation_candidate_v0_1/cpu_final.xml`：
31 passed、0 failed、0 skipped；`python -m py_compile`仅新脚本/测试通过，未跑旧全量。
逐条CSV/结果JSON、来源索引/12个SQLite后验hash、文档链接、隐私和diff定向核对；提交身份在
本轮收尾handoff，不将验证数量当作研究增量。

## 7.161 限定核心成文验证：完成方法/结果稿，按技术报告收口（2026-10-15）

用户接受路线A的一次有界成文授权，取消“真实导师确认为推进前置”；不是预先认可论文
增量，也不恢复技术路线。完成独立[中文核心稿0.1](exposedpath_core_manuscript_v0_1.md)：
先方法/W/terminal/validity与A/B，再独立oracle正反例、完整Formal/Engineering结果、
第一方近邻差异，最后写短摘要与提纲。不覆盖用户DOCX，不再交另一轮泛泛可行性评审。

**成文后的唯一结论为本轮选项B：可形成诚实技术报告，当前尚无充分论文增量依据，
保全资产，不继续扩工程或新增采集。** 这里的B不是恢复7.159已停止的方法路线B。
限定正确性/相对聚合的部分解释保持，未将完整timeline可恢复单独作为否定理由，也不以
wait小、零值或没有稳定加速判方法失败。增量不足针对当前有限问题：依赖和墙钟分解
已有近邻，当前实例化/数据边界尚未证明相对强参照的新测量关系、适用关系或实际分析
改进；不要求先测尽全部Host阻塞，不通过标题/Windows/LLM包装补足。若只有报表组织，
按技术产物定位，不追加矩阵追求正结果；本轮不提出自动补证/新设施任务。

正文复用4个核心图表（三表一既有全90窗图）：人工Q0 STREAM/COMPLETED/EVENT/缺映射
反例、五条件P0/P1三个phase中位数、全部单run A、近邻实质比较。表2仅从原60行Host
CSV做中位数算术；原signed差/冻结bootstrap/全block来源直接引用，未重跑。N1完整W、
terminal与合格单sync B保留；C0/Cpre局部Engineering各一次，不升级Formal或Request/
Decode。P1扰动、Host读取夹界、opaque allocation、UNKNOWN/NOT_ASSESSED与无增益/
方向反转均披露。原研究设计/Pre-Pilot与实际签署0.1.1严格分开。

定向回读Daydream/HTA/SKIP，并只新增直接影响“自动分解墙钟”贡献判断的RL-Scope
MLSys2021第一方§3.3/§3.4/附录C。未运行同行工具，不声称更准/更快或全面新颖性；
精确纠正旧稿Daydream运行时分解定位：§6.2/图6，不是§6.1，旧记录原样保留。
ARS按本轮限定写作使用，不启动多agent/外部模型/full评审或投稿流水线。当前不再以
找导师确认为工作前置，也不将AI收口判断当作科学证据。

Gate13限定PASS/Gate14 NOT_RUN、原A/B/registry/冻结统计、Raw/角色及历史BLOCKED/
UNKNOWN/NOT_ASSESSED不变。无服务器/模型/CUDA/Nsight、生产代码/新测试或完整分析，
无部署包/命令，无论文成立或学位录用保证。7.160/0.3及先前历史保留；当前入口与忽略
handoff改指本稿终态。用户DOCX及未跟踪大原件不改、不stage，报告类改动正常提交。
实际文档核对：218个仓库文件链接0缺失，三表/一原图；10格phase中位数与原Host CSV
相符，5个引用Q0身份及N16六条必要成员/B状态与来源相符；原contrast直接回读，无新
统计推断。隐私/diff及DOCX原hash保全通过，不将这些文档核对数量当科研增量或新资格。

## 7.160 AI模拟导师预审：推荐限定方法/测量成文，不追加技术投入（2026-10-15）

完成[AI模拟课题去留评审0.1](ai_supervisor_topic_review_v0_1.md)，不是导师认可、独立同行
评审、学位或录用保证。按用户指定顺序保留支持继续、严格方法/领域、投入负责人三种
视角，再综合；同一AI/上下文，NOT_CALIBRATED，无子agent或外部模型。**唯一推荐A：
停止扩大工程，转为限定方法/测量与适用边界论文候选的成文收口**；不是认为论文级创新
已经成立，也不是将7.159停止扩大路线B等同整个课题失败。该历史停止结论继续有效。

直接读取用户当前v7.1设计/Pre-Pilot v2.1、实际签署G12-ROUTEA/0.1.1、Q0/分域资格、
Formal小汇总、C0/Cpre与0.3关键独立参考及冻结helper。分开判断：定义内正确性有独立
限定证据；相对聚合的部分信息解释成立，API/Host等价结果、N1性能不确定照报；相对
强依赖分析的发表级差异尚未闭合；在现有资源下只建议有限成文，不追加GPU/设施预算。
不将1.5B/FP16五条件六block实物当7B/BF16原候选矩阵完成；Q0、Formal、Engineering及
事后解释核对不混用。报告两张精简表展示实际数值和三类判断，不重跑分析或增加测试。

第一方文献仅定向回读Daydream、HTA、SKIP。额外明确Daydream §6.1已有运行时分解，
不只是预测工具；HTA有同步依赖而非仅聚合。未运行同行软件，不虚称全面新颖性证明或
更准/更快。完整timeline可复原不单独否定方法，但输出合同/自动化也不证明创新。
主要优缺点均绑定证据、事实/推断层次、影响与最低补救；尚无真实导师/venue标准，不能
代其判定学位充分。**下一项唯一建议是把现成主张与证据交真实导师作范围/接受标准决定**，
不是再做AI可行性审查或技术补采。确认前不追加预算；若只剩工程组织，就按技术报告/
artifact定位，不靠扩矩阵强推创新。此为投入建议，不是已批准的研究改版或新Gate。

Gate13限定PASS、Gate14 NOT_RUN、原A/B/协议/Raw/角色、UNKNOWN/NOT_ASSESSED及
旧BLOCKED保持；路线B、8-profile、Cpre追加Pilot、llama.cpp/其他引擎/设施仍暂停。
本轮不修改生产代码、用户DOCX或大型原件，不生成部署包/命令、不操作服务器、模型/
CUDA/Nsight、不跑测试/完整分析。当前handoff与解释入口只增加本评审指针，不重写历史。
本轮203个仓库文件链接、报告两表、隐私、diff及DOCX原hash保全检查通过；初版临时隐私
正则误报https中的s:/，修正边界后0项命中，没有为此改动文献链接或业务内容。无新测试/
实验或数据资格变化，报告类改动单独正常提交，提交/推送身份在忽略handoff记录。

## 7.159 路线B一次本地可行性检查终态：停止扩大（2026-10-15）

用户仅批准7.158的一次本地方法检查，未授权新GPU/8-profile/引擎。已在同一
[决策稿0.3](pytorch_research_feasibility_decision_v0_1.md)收口：**唯一建议是停止扩大路线B，
不安排新的受控GPU验证、采集设施或负载矩阵。** 不是撤销A/B或旧Gate，也不是断言工具
永不可观测；**本轮限定的必要关系目标可行且已在现有资料上完成验证，无需新GPU实验**。
取得了必要设备效果→实际Host token及负载完成位置描述，但未产生值得新增方法投入的
独立解释关系。不能用“存在一个合格内部sync”替代自然路径用途，也不把测尽全部Host
阻塞/整段约束时长重新设为这一弱对象的前置。方法对象可核验与科研增量成立分开记录。

实际完成了新的、有限的本地工作，而非重复旧10项CPU断言：从原件12个G32/G512 P1 run
只读查询24次token的结构化范围、唯一runtime复制/同步、原correlation映射D2H/physical
sync及device/context/trace stream，并与实际token/Host ledger和输入receipt文件hash绑定。
24次均满足必要先后关系；G32实际token为463/2529，G512为29184/6556，不把不同输入的
token强行设为相同。CPU手写参考6项通过/0失败，区分READY/NOT_READY/UNKNOWN、内容
冲突及晚到无关效果；不调用S/A/B，不将逻辑例称真实CUDA证据或新增资格。

六block的G512−G32 D2H完成位置差（相对原request point）为−3.058493/5.529030/
−7.325998/1.072328/9.427312/−12.929171ms，与投影Prefill结束差均三正三负。结合GPU
union差全正，能核验活动量与完成位置不同；不能将位置差归因给GPU净阻塞。实际Host
读取仅夹在成功sync返回和后发point之间，区间宽2.072793～4.205537ms；Host后缀差夹界
均含0不证明等价。该小表是事后解释核对，不替换原冻结统计/计时，不跨钟拟合offset。

本次验证对象、输入/预设依赖、独立参考取得方式、反例和停止依据均在同稿§4～7；Q0人工
expected及已完成独立Raw资格直接复用，未重跑全Q0或完整analyzer。原0.2所提一次受控
P0/P1也不能独自验证自然opaque完成的解释迁移，两种竞争解释都可通过同一理想正例，
因此不制作入口或交付包。进一步区分完成操作内部前提/消费就绪需要尚无可靠证据路径的
新观测与验证工程，本轮判定其当前信息收益依据不足，不滚动延长1～2工作日检查上限。

本机参考产物schema `completion-constraint-feasibility-reference/0.3`、SHA256
`08523a5166b8b75c50ae71f2cdb287759e367f7d3624e80cb7c042301ae9792e`，24条原始引用/
12run输入hash/六block夹界及6项断言留在忽略的本地索引。没有业务代码、schema、registry、
测量或统计语义变化，不重签/重算旧Formal；Gate13限定PASS/Gate14 NOT_RUN及原Raw/ZIP/
BLOCKED/UNKNOWN/NOT_ASSESSED保持。用户DOCX和未跟踪大型原件不改/不stage，当前
无需服务器操作；只更新少量现行文档、唯一进度与handoff，下方7.158保留为当时建议。
本轮194个仓库文件链接、新增行隐私、参考结果/hash/作用域、DOCX前后hash及diff-check
通过；无生产代码变更，不执行pytest/compileall、全量测试或任何实验。

## 7.158 投入收敛：完成约束适用性先于新增负载矩阵（2026-10-15）

更新同一[研究决策稿至0.2](pytorch_research_feasibility_decision_v0_1.md)，不是新合同或资格。
**当前证据不足以将“准确GPU阻塞／普遍负载规律”作为已成立的立项贡献；推荐B的有界
方法可行性验证，需集中确认新推断目标/验证义务。** 保留负载→执行结构→请求暴露主问题，
不以简单记账替代；先验证必要GPU完成约束与活动交集的适用关系，失败就停止扩大。A的
现有描述保留；不并行追加矩阵/引擎或新采集设施。没有把推荐写成用户已经批准的amendment。

区分GPU活动量、合格同步必要活动交集②、Host受GPU完成约束③、GPU优化可节省请求时延④。
Q0与30条独立Raw审查支持②的限定正确性，不自动验证③/④。Cpre入口到最后必要活动
87.604935ms、交集38.946574ms、未覆盖48.658361ms；另有terminal后0.042018ms。
不把跨度叫真实阻塞、不把差值叫GPU等待低估，不把residual归CPU/profiler。自然opaque
完成与共同先决条件是实质可识别性缺口，不是靠措辞即可补齐。原同窗公平baseline/完整
时间线可恢复的事实不虚称独占增益；近邻三族已有依赖/关键路径/负载思想，创新仍待证。

已完成独立本地工作：读取用户当前DOCX/Pre-Pilot协议及实际签署0.1.1，复用Q0人工expected、
Formal/C0/Cpre已保存独立来源；定向核对小文件hash。一次CPU模型关系审计**10项断言通过、
0失败**，包括同聚合不同W、同交集不同就绪跨度、连续/有空隙理想门、不透明完成、相同
外部记录不同反事实收益、原Q0手算40ns、12行G1 Prefill与独立来源一致及Cpre区间关系。
没有导入被测S/A/B、没有重跑Q0/完整analyzer/实验；不是生产回归或真实CUDA/Host阻塞资格。
Formal六块GPU差全正、E差4正2负，仅支持这两个观测量不同；不是模型响应面。

**修正7.157的下一步建议：8-profile接线/包装继续暂停，不再当作科研增量判别实验。**
两个完整block能筛查政策图形重复性，但两种竞争解释都可能预测长sync/短copy，不能判别
自然阻塞量或新颖性；原24条及四对方案也不恢复。只建议先在现有构造内形成③的精确对象、
独立参考和非空自然适用条件；一次有界本地方法设计上限估计1～2工作日，无法独立判别就
停止，不滚动扩大设施/预算。需要改变推断语义时先用户集中决定，不实现③估计器、不
生成包或服务器命令。当前用户无需操作服务器。

Gate7～13既有限定结论及数据角色保持，Gate13限定PASS/Gate14 NOT_RUN；原Raw、旧
BLOCKED、UNKNOWN/NOT_ASSESSED、用户DOCX及未跟踪大型原件不改/不stage。测量代码、
registry、冻结规则/输入/统计未变化，无需重签或追改旧Formal。本轮只提交决策、当前指针
及同次进度，机器专属小审计定位与逐项结果留在忽略handoff。CPU审计摘要SHA256为
`af22912a7b806341d6c5cf3b39d1dadc4946bea62d70c8ef3b5cca244dbc0003`；192个仓库文件链接、
新增行私有路径/凭证检查、diff-check及用户DOCX前后hash检查通过。没有生产代码变更，
未执行pytest/compileall/完整Q0；不将10项推理断言写成模型资格。下方7.157保留历史建议。

## 7.157 PyTorch研究可行性裁决：限定测量与边界主线（2026-10-14）

完成用户授权的有界证据/最近工作审查；[唯一决策稿0.1](pytorch_research_feasibility_decision_v0_1.md)
集中给出三问题贡献—证据表、风险与待审8槽方案。**研究建议裁决为“收缩为限定测量与
边界研究”**：相对聚合指标的有限解释可以保留，但增强到同窗correlation/stream/完整
时间线及同CUDA语义后，三个实物问题的关键事实基本可复原；尚未证明独占信息、稳定
性能机制或效率/用户收益。不是推翻Gate13有限Formal审查，也不擅自修改签署claim。

复用99f3bae执行/e19c308分析的六block、独立Raw终稿与同窗baseline；本轮仅读取小汇总、
独立复核记录及CSV均值/原值，未重跑S/A/B或Raw全扫。G1 Prefill GPU union均值
19.710030→42.431923ms、wait0.034954→0.029979ms；六块wait方向混合，Decode wait均0。
N16完整W/hidden/terminal与C0/Cpre交集/residual独立记录保留；不把analyzer当唯一oracle。
Formal/Engineering分开；1.5B/FP16实物不替7B/BF16设计候选矩阵，未部署新模型。

直接核对Daydream作者全文§3～4/USENIX ATC2020、HTA官方critical path文档/源码、SKIP
作者v1§III～IV及ISPASS2025接受元数据；依赖图、sync位置、Async可能阻塞及LLM映射均有
先行思想，不能按“面向LLM/自动A/B”宣称创新。未运行同行工具，不猜源码缺失或能力差距，
本有界核对不等于全面新颖性证明。CPU/P1扰动、point延迟、局部支持域及潜在量识别限制
集中记录，不放宽原质量门或将结构直接迁移P0。

**待审唯一下一步**由24-profile候选缩减为B1/B4×C0/Cpre×两个完整block，共8条新P1，
只作Prefill政策结构的反证首批；0P0，不授性能收益/精度/稳定或Formal。固定输入512/
每样本2、warmup3/repeat1、同包装/实际流，正反组序和负载先后平衡；预计45～60min/
5GiB临时空间，固定预算或硬失败停止，不重试/替补/续批。这是设计建议，不是预算/实现/
采集授权；协调审查前不制作包，旧四对Pilot不恢复。若仅重现强baseline已知现象，则
停止扩大矩阵/引擎；不追显著。llama.cpp/Linux/设施继续暂停。

本轮仅文档/链接/diff验证，无代码/测试/实验/服务器变更。Gate13限定PASS、Gate14 NOT_RUN，
原Raw/报告/UNKNOWN/NOT_ASSESSED及用户DOCX、大型原件保持。当前服务器无需操作。

## 7.156 安全停点与PyTorch完成政策主线回归（2026-10-14）

依据用户本轮优先级调整，**暂停llama.cpp扩展、部署包、服务器执行及后续引擎资格**；
不撤销实现、不清理原件、不恢复历史入口。7.155最小API修复已完成并正常推送，固定
提交`1e1c1fd6b91ed2001ea308d9bda2b721c23c2f9b`；本轮直接复用既有13 passed/0 failed/0 skipped
真实头文件/对象审计及152 passed/0 failed/7可选skipped CPU入口记录，没有重跑测试。
目标机旧C/C++、CUDA编译链接预检和configure已通过；新adapter的MSVC实际编译、最终link、
GGUF转换及native观测资格仍未验证，stage1原BLOCKED/native资格NOT_RUN不改。暂停工作
不是通过或撤销资格，未来若恢复须从保留的实际差距开始，不重跑已证明事项。

本轮只读核对PyTorch实际runner/helper与Cpre接线：输入驻留目标GPU、成功窗前drain后
request开始；首/末token经过真实Host读取后观察completion，共用三个半开窗口。
没有实际网络流式发送。C0后复制同步的必要活动交集为零可符合有限Device Exposure定义，
不证明复制API无内部阻塞；Cpre只改首token复制前的实际流同步，边界仍是Host-readable，
Decode未改。预算迁移个案不是“Device wait修好”，也不是自然baseline替换或完整等待恢复。

当前少量入口集中到[解释范围0.2的PyTorch路线](device_exposure_scope_and_windows_engine_v0_2.md#当前pytorch路线完成政策负载与可支持的解释)：
复用Formal G32/G512的同政策输入长度证据、Engineering B1/B4的局部Prefill batch证据，
与独立C0/Cpre完成政策个案分开。比较绝对预算/占比、GPU活动及同窗baseline，不要求wait
单调或较大，不混合角色、不将P1组成迁移P0。已有独立正确性证据不等于一般机制规律；
Cpre政策效应可重复性/适用范围仍是提出更广claim时的实际缺口。现有资料可以先完成有限
论文解释，不需要引擎构建、完整Host等待认证或新增监控。旧84次/Request/Decode拒绝保持，
不追索旧w11/UNKNOWN；四对C0/Cpre追加Pilot继续暂停。

此次只是解释、优先级及交接更新，测量代码、schema/registry、冻结G12-ROUTEA/0.1.1、
Formal结果/排除/统计规则及所有数据角色不变。Gate13限定PASS、Gate14 NOT_RUN、
UNKNOWN/NOT_ASSESSED和用户DOCX/大型原件保持。本轮仅文档链接/diff检查，不实验、不
重算、不清理、不生成交付包或服务器命令；当前服务器无需操作。以下7.155及更早为历史。

## 7.155 Native真实SDK接口修复与前置adapter编译（2026-10-14）

**48567aa目标C/C++、CUDA真实编译链接预检及完整configure通过；native最终构建仍BLOCKED。** 本地只读核验新回传132773 bytes，SHA256 `5858ec42c8bcdc82bd3adb47fee47b58f80ce138153f53a8ae73c68121d3f25f`，109成员/108项、CRC/安全路径/长度/hash/完整覆盖通过，manifest SHA `3495eb1cf2a681d772f87900109db04567cbea45b1de6467feead7389925d7d3`。执行48567aa890bfd7f101ebf7b6b720308b4b48e20f；原CPU142 passed/4 skipped，原始两precheck JSON/输出及configure exit0已直接读取；build1606.078s exit1、无timeout，唯一编译错误为main.cpp:29的`cudaDeviceGetUuid`不存在。未进入GGUF转换，无模型/GPU探测/collector。原字节、退出码及BLOCKED不变；build stdout含非UTF8的MSVC诊断，读取展示不能改写Raw或假称UTF8原件。

根因是Runtime API调用错误与自行虚构声明的stub一起掩盖SDK兼容问题，不是环境缺组件。固定CUDA12.4.1官方device/uuid原文及NVIDIA12.4真实头文件确认正确路径为`cudaGetDeviceProperties`→`cudaDeviceProp.uuid`。修复保留实际count/logical/mask/UUID/PCI及错误门，在模型/窗口之外；stub明确仅不完整语法子集，删除不存在的API。核对第一方native七个Runtime查询/错误接口及五个backend调用点复用的stream synchronize签名；不改变vendor CUDA行为或宣称所有API已获分析资格。接口/来源和支线claim集中在[native §7.155](native_llama_window_and_adapter_v0_1.md#7155-实际cuda接口与adapter前置编译支线收口范围)。

新增真实adapter对象编译门位于完整configure之后、昂贵llama backend构建之前；同一main对象与observer库由最终exe复用，真实头文件来自固定SDK/vendor/NVTX而非stubs，不执行生成程序。必需输出、实际版本/SDK12040、源码/头文件/对象hash保存为adapter-compile0.1.0，新build0.2.2须严格绑定；旧0.1.0/0.2.0/0.2.1读取和原判定保留，不升级旧数据。source manifest新增共同target文件；当前服务器前置绑定48567aa。阶段1配置0.2.0、测量spec/producer/边界/流/同步/S/A/B/registry、签署G12-ROUTEA/0.1.1与旧Formal均不改变。本轮未生成交付ZIP或服务器命令。

tests-first：真实12.4头编译独立复现同一缺API，stub“错误API应拒绝”和缺前置门反例先失败；修复后新文件13 passed/0 failed/0 skipped（15.75s）。其中真实CMake3.31.10/Ninja1.12.1在本地GCC仅编译实际main/observer对象、backend sentinel未触发、未生成或运行native模型exe；全Runtime签名静态检查不调用函数。头文件来自NVIDIA固定Windows runtime12.4.127（wheel SHA `09c2e35f48359752dfa822c09918211844a3d93c100a715d79b59591130c5e1e`）及nvcc12.4.131（`aadd9fb307352bbcd5bc89b5f98c10cd78000915094882d97321f5fe36441742`），只提取头文件、未安装/加载库/执行nvcc；runtime主头SHA `06fd5b2b2becb7f9165e88b8fdfdab778136f614be80ff82628c78ea97e218f4`与目标原回执完全一致，其他header未声称全部服务器字节一致。GCC头文件有已保留的`__cdecl`重定义警告，不冒充目标MSVC编译证据。

生产CPU计划实际命令：`python -X utf8 -m pytest -q -rs -p no:cacheprovider tests/test_native_stage1.py tests/test_native_ninja.py tests/test_native_tool_identity.py tests/test_native_llama.py tests/test_native_cpu_import.py tests/test_native_cmake_contract.py tests/test_native_adapter_compile.py --basetemp <new-short-root>/cpu-tests`，本地Python3.12.7、工具式PATH无g++，152 passed/0 failed/7 skipped（35.36s）。3既有skip为可选SDK语法/两个编译CPU替身；4新skip为该入口无g++的可选本地header/syntax/CMake对象审计，已在上述独立13项中实际验证，不能把本机证明写成服务器资格。必需目标adapter编译不在pytest skip路径、无fallback；不重跑全量/Q0/旧实验，不运行生成程序。负例保留错schema/hash/SDK、缺对象、旧版兼容及真实文件链失败停在backend/转换之前。用户DOCX原SHA保持且不stage。

相关Python compileall及diff-check通过；已审查完整configure→adapter→backend/link→转换调用链，不存在本轮新增模型/程序执行入口，失败仍保留原错误。用户DOCX及原未跟踪大ZIP不提交，无新部署包/服务器执行要求。

**最小产出与停止点**：此支线只验证固定Windows llama.cpp自然完成子域的合法accounting及相对同窗baseline的解释适用性，不追求更大Device wait、不替代已完成PyTorch Formal、不进入Gate14。当前仅本地修复完成；必须目标机证明的剩余项为同对象前置编译、最终link/F16内容身份，之后才按另审方案做最小drain/依赖桥接与一对自然P0/P1。缺件或依赖闭包不足就停该子域，不无限扩展监控/负载/完成政策。零wait/无信息增益均是合法可能结果。Stage1仍BLOCKED/nativeGPU资格NOT_RUN；Gate13限定PASS、Gate14 NOT_RUN、UNKNOWN/NOT_ASSESSED及历史证据保持。以下7.154为历史，旧包不恢复；下一步先审本地修改，**现在不安排服务器执行**。

## 7.154 阶段1 CMake路径序列化与原始版本贯通（2026-10-14）

**34fa866导入修复目标机通过；当前为CMake适配失败，不是缺VS安装。** 本地直接核验回传ZIP39717 bytes、SHA256 `ae6b7bbd643e76893650bb6e4887ba82786d447759b9ae998b71c18491809a08`，81成员/80项、CRC、安全路径、长度/hash及完整覆盖通过，manifest SHA `62eff475312c49890d54cdd59f197885553d04b27df01f5e26669c5d8d26e06c`。原始CPU日志为103 passed/4 skipped；源码/Git/工具/依赖门已跨过，CMake原始stdout识别C/CXX为MSVC19.38.33135.0。compiler identification小程序已真实编译链接；完整C/C++预检、CUDA预检、native构建/权重转换未通过或未执行，不能混称构建成功。最早失败为`NATIVE_STAGE1_STEP_EXIT:cxx_configure`，生成的RC编译器文件因未类型化反斜杠路径出现`Invalid character escape '\P'`。原退出码、失败cache、ZIP及BLOCKED保持。

最小修复在CMake argv边界统一工具FILEPATH、源码/根PATH及`-S/-B/--build`正斜杠表示，结构化参数保留空格/括号，严格核对原文件路径/长度/hash，不归一化源码内容；无法安全表示的路径拒绝。三个CMakeLists共用精确MSVC规则，只接受已核验的`19.38.33135`或`19.38.33135.0`，不前缀匹配、不重写原始版本；nvcc仍精确12.4.131，工具路径/PE资源/SDK/输出检查不变。新precheck schema `exposedpath-native-compile-link/0.2.0`、Ninja build `exposedpath-native-llama-build/0.2.1`；旧build0.2.0只能配旧check0.1.0/原三段版本，VS0.1.0及旧读取/历史判定保留。未知、混用或不同版本拒绝。stage1配置仍0.2.0，producer/边界/流/同步/S/A/B/registry未改变。新共同CMake文件纳入实际native源码hash来源。

tests-first真实固定CMake3.31.10模板生成→include先复现路径错误，三个实际CMakeLists先复现四段误拒绝。修复后涵盖空格/括号/反斜杠路径往返、same-file/hash、原始版本、实际预检→native回执→消费者接线、显式旧版兼容、错版本/错schema/缺输出反例；不以命令字符串或手填成功JSON代替CMake生成。LANGUAGES NONE及CMake脚本只验证生成/解析和版本门；CPU外部编译步骤仍为非执行替身，**没有本机cl/nvcc/生成程序执行，不证明目标机编译资格**。按生产`cpu_regression_plan`与Runner的六文件实际命令：`python -X utf8 -m pytest -q -rs -p no:cacheprovider tests/test_native_stage1.py tests/test_native_ninja.py tests/test_native_tool_identity.py tests/test_native_llama.py tests/test_native_cpu_import.py tests/test_native_cmake_contract.py --basetemp <new-short-root>/cpu-tests`，本地Python3.12.7，**143 passed/0 failed/3 skipped，28.87s**。三个既有skip为可选SDK语法审计及两个需要g++/固定JSON头的CPU编译替身；实际工具式PATH不含g++，不据skip授构建资格。新真实CMake资产明确绑定且不得缺件skip；CPU回执记录实际Ninja/CMake/test模块来源。

后续configure→compile/link→转换核对：新目录、固定Ninja/cl/link/lib/rc/mt/nvcc/SDK及既有禁CUDA运行探测patch；两项真实编译链接及native实际cache/compiler/output成功后才转换，Python转换路径不受CMake序列化改写。只读复用原资产/CPU环境，不安装、不修改VS/CUDA/旧源码。独立历史VS诊断入口不是本次Ninja链，原规则保留。最终三个CMakeLists版本门12 passed/27 deselected（1.16s）；相关Python compileall、PowerShell解析与diff-check通过。仅准备以前置34fa866的小修复包，先交协调审查，**本轮不安排服务器执行**；阶段1仍BLOCKED，nativeGPU资格/Gate14 NOT_RUN、Gate13限定PASS、UNKNOWN/NOT_ASSESSED保持。用户DOCX及大型原件不改、不stage；当前入口[native §7.154](native_llama_window_and_adapter_v0_1.md#7154-cmake路径与原始版本合同)。下方7.153及更早为历史，不再执行旧包。

## 7.153 阶段1定向CPU测试模块身份修复（2026-10-14）

**d77386目标机工具身份/源码/CPU依赖检查已跨过，仍在CPU测试失败，实际编译/转换NOT_RUN。** 本地直接核验回传ZIP30602 bytes、SHA256 `2ba5e75e62c0dd64d3fce89da781b817717848416e6e8203132721c7d17bfd09`，72成员/71项、CRC、安全路径、hash/完整覆盖通过，manifest SHA `aa0fe68244c1b4265a080a1f8ef0f42a1de791f96d53fecf70f623ee575ed68f`。真实执行d77386f79c16f01e25298564e98a0af431a3cedf，link/lib固定资源身份成功、依赖check和CPU版本成功；CPU为91 passed/6 failed/4 skipped，6项均在`tests.test_native_*`导入时失败。原日志未记录实际tests包解析来源，不能将某具体第三方包写成已证实根因；没有进入实际C/C++或CUDA预检/模型/转换/collector，原BLOCKED与原ZIP保留。

独立子进程用同名外部regular tests包复现完全相同的6项失败；最小修复统一采用仓库原有`test_*`共享helper约定，覆盖Ninja→stage1和stage1→Ninja内部反向导入，不删除失败测试/skip/吞ImportError。只对该生产CPU入口显式绑定tests和code路径后保留gguf-py；不全仓包化tests或修改全局pytest配置。新增实际Python/cwd/PYTHONPATH/module origin+SHA的只读子进程回执，来源错配拒绝；记录未使用的tests namespace来源及可选审计输入可用性，但不导入外部包、不读取全环境。实际stage1文件链证明此门在CPU回归之前、实编译之前；真实Python/测试清单仍由固定配置执行，未来目标机数据不能由本地替代。新入口附`-rs`保留skip原因。

原4项skip对应：fixed_backend_patch缺可选私有upstream字节审计输入；main_host_syntax缺可选g++或固定llama.h；compiled_native_producer两个参数用例缺g++或固定JSON头。后两种OR分支缺哪项原日志没有记录，保持该限制，不断言系统组件缺失。它们是可选开发/CPU替身审计，**不是**目标机必需的C/C++与CUDA configure/compile/link；后者必须实际成功并验证cache/输出，不因skip授构建资格。新回执保留g++路径与三项文件存在性，目标缺件照实记录，不能静默通过或安装补齐。

后续接线审查另发现：固定编译PATH排除了Git，native CMake却`find_package(Git REQUIRED)`；新configure显式绑定已有verified Git executable，消除环境偶然发现，不改变源码/同步或补工具。部署前置本次d77386、CPU环境事实来源598d447、工具query原件来源882425c继续分开；两个旧引用均按原哈希校验，不把新部署HEAD填回旧reference。其余Ninja/MSVC14.38/nvcc12.4/SDK、只读CPU环境、原40资产、禁运行CUDA ABI探测、预检→native→转换与真实输出验证不变；没有重新安装、工具链升级或VS修改。

tests-first：新子进程/环境3项先失败，其中嵌套真实pytest复现6项；Git绑定/部署来源分离2项先失败；实际CPU入口接线新增反例先失败后通过。本地按生产`cpu_regression_plan`+Runner、同argv/cwd/PYTHONPATH/测试清单运行5个相关文件，**104 passed/0 failed/3 skipped，19.67s**。本地Python3.12.7，固定工具式PATH不含g++，所以3项既有可选审计skip；upstream字节审计输入本地存在并通过，不把差异改写成目标机4skip已经完成。没有运行生成CPU/native程序、CUDA/Nsight/模型。本地长诊断根使3个既有fixture文件达到261字符而失败，扩展路径确认限制后仅在新的短临时根按同入口验证通过，不改测试/生产规则；保留该本地失败记录。Python compileall/diff检查通过，用户DOCX原字节保持。目标机相关CPU和真实构建仍需新回执审查，stage1 BLOCKED/GPU资格NOT_RUN；Gate13限定PASS、Gate14 NOT_RUN、UNKNOWN/NOT_ASSESSED保持。唯一下一步是以前置d77386的小包、新输出目录、单metadata ZIP，先交协调审查；不重复旧入口、不恢复/重试/清理。

## 7.152 阶段1工具身份查询与构建退出码分离（2026-10-13）

**服务器882425c已部署，但link帮助查询误拒绝，实际编译/转换仍NOT_RUN；本次仅本地工程修复。** 直接核验回传ZIP17793 bytes、SHA256 `3d8f2599cf0dec1499463e1a90d1ab1b3dcb32bbf2bd2df14314da3fa6746264`，43成员/42项、CRC、安全路径、hash及完整覆盖通过；manifest SHA `98b211c361b041947b56ea18b975ff301ccb21b8bb9b4c994c8fe3c1952d2986`。真实checkout为882425c02f3e0ec70679c0ed58875a852cf3cbd1且clean；ninja --version成功，link /?在0.047s退出1100、无timeout，stdout含14.38.33135.0及帮助、stderr为空。Runner在版本解析前执行通用exit-zero门，故误把身份查询作为构建失败。lib查询及真实configure/compile/link尚未执行，不能推断其返回约定或构建能力；旧BLOCKED原件不改。

最小修复选择**文件版本资源查询**，不建立宽泛非零退出白名单。新tool identity合同`exposedpath-native-tool-identity/0.1.0`独立读取link/lib的Windows固定PE版本资源，记录路径/长度/SHA256、原13个DWORD、实际版本及错误；工具exe不执行、exit_code=null不是伪造0。当前两个文件必须精确匹配本次封存回执中的实际文件身份，查询前后字节一致、资源签名/类型及14.38.33135.0严格匹配；错文件/版本/资源、读取失败或变化拒绝。依据[GetFileVersionInfoW](https://learn.microsoft.com/en-us/windows/win32/api/winver/nf-winver-getfileversioninfow)与[VerQueryValueW](https://learn.microsoft.com/en-us/windows/win32/api/winver/nf-winver-verqueryvaluew)，查询固定版本不依赖本地化帮助文本。原帮助stdout/stderr与1100完整保存在封存ZIP、并作为新包的原样reference；不能将1100改写成功。通用Runner不变，实际configure/compile/link/转换等仍要求exit0和真实产物/cache验证。Ninja/CMake/Python/Git查询维持各自原有严格规则，不新增fallback。

同时完成后续接线核对：部署前置882425c与只读复用CPU环境/事实的来源598d447分字段绑定，避免部署commit变化误污染旧资产身份；原40项离线资产/layout、598 CPU环境和禁运行CUDA探测patch不改。真实reference ZIP→工具文件/version→stage1消费路径补CPU正反例；Ninja入口纳入新相关测试，再C/C++实预检→CUDA实预检→native构建→GGUF转换，任何失败即停。stage1/build仍0.2.0，旧0.1.0读取及原判定不改，测量/producer/S/A/B与研究结果不变。

tests-first首轮新查询反例16 failed/1 passed，部署前置接线反例1 failed/22 passed；最小实现后实际定向命令（mask=-1）`python -m pytest -q -p no:cacheprovider tests/test_native_tool_identity.py tests/test_native_ninja.py tests/test_native_stage1.py tests/test_native_llama.py`为**101 passed、0 failed、0 skipped，41.92s**。包含本机真实Windows PE资源只读查询、错误读取/内容/版本/变化、原始1100仍被真实构建Runner拒绝及实际文件reference消费链；CPU替身不等目标工具或compile/link验证。Python compileall/diff-check通过，用户DOCX原SHA不变。不重复全量/Q0、没有服务器/模型/CUDA初始化/Nsight操作。唯一下一步为以882425c为前置的小修复包，经协调审查后由用户执行一次原阶段1范围的新目录入口；20GiB临时空间/45–120分钟估计，长期<50GB、无清理。Gate13限定PASS、Gate14/nativeGPU资格NOT_RUN、UNKNOWN/NOT_ASSESSED保持。当前交付入口见[native §7.152](native_llama_window_and_adapter_v0_1.md#7152-工具身份查询独立规则)。

## 7.151 阶段1固定Ninja路线修复与编译预检（2026-10-13）

**VS事实检查已完成，原VS生成器路线不能仅靠实例路径续跑；Ninja仅完成本地接线，目标编译/转换仍NOT_RUN。** 已直接核验事实ZIP12840 bytes，SHA256 `e1dad7999c2d4e0780c23e9664bb807e9e5f55d06483d7e884430bc05709d34d`；23成员/22项清单、CRC、安全路径/hash/完整覆盖通过，manifest SHA `ba3ba6a5b16a69cbab10029891265539050b63d3075935442d9c5588bf1758a6`，facts SHA `4d59db2bcb836f4634fe8773515f27b9db3aaaf4ec89cc160f66858ae3031037`。598 checkout clean；VS17.8.34525.116/MSBuild存在，VC与qualified查询为空；默认VCTools文件、CUDA12.4 VS props/targets缺失，三版SDK指定头/库存在。CMake固定源码要求默认工具声明，不能用cl可执行替代该事实。旧现场/报告保留；不修VS安装/注册表/marker、不升级Toolkit/driver、不转Linux。

用户批准改用固定Ninja 1.12.1驱动现有MSVC14.38.33130（实际cl19.38.33135）/nvcc12.4.131。使用已观测SDK10.0.20348.0；明确指定cl/link/lib/rc/mt/nvcc/CMake/Ninja，编译环境的PATH/INCLUDE/LIB固定，删除继承编译器覆盖选项，不依赖VS实例或CUDA MSBuild扩展，也不自动fallback。先一次列出所有真实编译依赖缺件，再通过C/C++和CUDA的实际configure/compile/link及输出/cache/编译器事实验证；CUDA ABI架构运行探测仍按既有私有模块hash严格禁用，无任何生成程序执行。失败立刻停，不自动安装/重试。完整命题与当前入口见[native §7.151](native_llama_window_and_adapter_v0_1.md#7151-固定ninja构建路线)；原7.150查询入口成为历史，不重复取事实。

显式新增stage1与native build schema 0.2.0，仅标识Ninja构建路径；0.1.0的VS读取/历史判定保留，未知版本或错生成器拒绝。新build需要两份真实编译预检引用及精确编译器/SDK/status，不手填compiler works，不改producer/边界/同步/S/A/B/旧Formal。现有598阶段1CPU环境、CMake字节和原禁探测patch由封存回执/事实ZIP绑定后只读复用，设置禁pyc及新cache路径；pip只check、不install，不重传或再安装原wheels。原HF内容身份仍严格，转换与build新目录，GGUF仍F16/F32实际tensor检查、revision未知。

本地tests-first覆盖缺能力、Ninja参数/SDK锁定、集中缺件、错实际编译器/路径/架构/输出、旧schema不可伪装Ninja、错/重封预检状态及实际stage1文件消费顺序。定向CPU命令`python -m pytest -q -p no:cacheprovider tests/test_native_ninja.py tests/test_native_stage1.py tests/test_native_llama.py tests/test_native_vs_precheck.py`（mask=-1）为94 passed、0 failed、0 skipped，40.21s；编译外部依赖用CPU替身，不等目标机真实compile/link。新增Python compileall、PS5.1 parse、diff及用户DOCX原字节检查通过；固定官方Ninja二进制仅本地执行--version=1.12.1，没有cl/nvcc实编译、GPU/CUDA初始化/模型/Nsight或Q0。一次小修复包以前置服务器598d447为基线，显式先预检后构建/转换、回传单metadata ZIP；目标机失败则只报告具体缺件/原始错误，不补造VS信息。20GiB临时空间/45–120分钟估计沿用，长期<50GB，无清理。Gate13限定PASS、Gate14/nativeGPU资格NOT_RUN及UNKNOWN/NOT_ASSESSED保持；用户DOCX及原ZIP不stage。

## 7.150 阶段1 VS实例发现停点与有界工具链预检（2026-10-13）

**598d447的Git修复已由目标机实物验证；阶段1仍BLOCKED于CMake实例发现，不是模型执行失败。** 本地直接核验回传ZIP29227 bytes、SHA256 `ddfa4d5830874c2c0d98949deecd806fb447ccb07b329157ac37d2ec0b143e3c`；76文件/75项清单、CRC、安全路径、全部hash与完整覆盖通过，manifest SHA256 `d45b3e5e0c142b3dc15f8ae4e87765c601971c70fecab12da363e1faf8d8bc37`。实际checkout=598d447811e948a3ffb54845185631f4be761985/clean，独立llama HEAD=d81235049384534c167caea52b85a694f6103d14/clean。离线依赖、pip check、CPU32 passed（9.23s）、CMake3.31.10版本均成功；工具链回执记录cl19.38.33135、nvcc12.4.131/x64/14.38.33130。原receipt SHA256 `7c3e4f557c102fe8c6d649b01c8d510ec3061f4c256d4e529545f13118a41178`。

实际configure以VS17 2022/x64/-T version=14.38.33130调用，在CMakeLists第2行C/C++ project处0.109秒exit1/无timeout；错误为could not find any instance of Visual Studio。未进入native/CUDA编译或HF转换；没有模型/CUDA初始化/Nsight。argv没有显式generator instance，但这不能独自证明根因。回传没有Installer实例、MSBuild、默认VCTools实际声明或cache信息，不能从cl可用推断实例注册/组件完整，也不能断言缺安装。

最高优先级仅一次定向只读事实检查：固定598 checkout和原失败receipt，查询vswhere全实例/VC/MSBuild组件谓词，记录实际路径/hash、默认工具版本及其目录、SDK文件、CUDA VS props/targets和旧CMake cache/log。原失败树/环境只读，所有输出在新diagnostic root、回传一个小ZIP。缺工具/查询失败保留unknown；不安装/升级、改cache、复制整个仓库或重跑阶段1。当前入口见[native §7.150](native_llama_window_and_adapter_v0_1.md#7150-vs实例发现与真实cc预检)。

已实现独立的C/C++-only配置/编译/链接预检，采用同VS生成器/x64/14.38.33130和已观测实例版本，新build目录，实际检查Windows SDK、C/C++混合对象及链接输出；不运行生成exe、不启用CUDA语言。实例未被唯一完整识别时拒绝，不猜portable版本、不回填默认VCTools。**目标机真实预检尚未运行，不以CPU替身宣布通过；完整阶段1修复/续跑包需其实际回执后再收敛。** 本轮交付入口默认仅inspect，绝不自动调用precheck/build/convert。

tests-first记录：缺能力RED，默认VCTools引用缺字段RED，真实-I子进程发现并修正兄弟模块导入失败（固定文件加载，不放宽搜索路径）。复核固定CMake源码另修正cache消费：它将实例说明存为所选location，不保留输入version参数；位置按路径身份核对，版本仍绑定事实与configure argv，不用原字符串相等误拒绝。最终相关命令`python -m pytest -q -p no:cacheprovider tests/test_native_vs_precheck.py tests/test_native_stage1.py`（CUDA_VISIBLE_DEVICES=-1）为**48 passed、0 failed、0 skipped，21.59s**，含真实独立Git/文件入口及错原receipt拒绝；编译器/Installer外部依赖由CPU替身替代，不是目标机实编译证据。相关compileall与PS5.1语法/diff检查通过；无全量/Q0/实验重跑。现有测量合同/Native候选边界/A/B/原Formal不变；Gate13限定PASS、Gate14/nativeGPU资格NOT_RUN、UNKNOWN/NOT_ASSESSED保持。用户DOCX和未跟踪原ZIP保留、不stage、不清理。

## 7.149 阶段1源码归档空目录与Git作用域最小修复（2026-10-13）

**首次cc9b595阶段1保持BLOCKED，不是GPU/模型失败。** 本地直接核验回传ZIP17365 bytes，SHA256 `eff229f2165bc200bef7d80dc2bd343eaf9c49e141e3502e0aa13e7b507c2918`，39文件/38项清单及CRC/全部hash通过。原receipt前三步Git checkout身份成功后engine_head exit128/无超时，stderr为not a git repository；没有创建CPU转换venv、编译、转换、模型/CUDA初始化或collector步骤。旧包/报告不改，GPU资格NOT_RUN、Gate13限定PASS/Gate14 NOT_RUN保持。

根因为packager只写文件、遗漏空`.git/refs`等目录；真实Git独立/嵌套父仓库回归复现，不用engine_head替身作为证明。新归档保全目录；旧源码ZIP只由绑定archive SHA和原目录快照的layout恢复到全新目录，文件字节不变。worker/CMake显式Git目录与工作树，验证实际top-level/HEAD/clean，缺结构、错commit或父仓库身份拒绝；清除继承Git路径变量并禁用可选index刷新（独立RED证明status会修改index）。原固定源码、构建/转换参数、A/B与测量合同不变。

真实封存源码副本已本地恢复：3712文件、386目录，真实HEAD=d81235049384534c167caea52b85a694f6103d14、clean，Git检查后全部文件仍与原清单一致。证据位于忽略的`.local/diagnostics/native_stage1_refs_repair_v0_1`；CPU替身文件链另验证严格资产复用、阶段步骤与新回执，不等目标机编译/转换通过。修复以前置cc9b595a42a39ff5d6524274a4dda4c03717dc16交付，仅增量bundle/脚本/layout/config；已传40项固定资产按旧manifest与当前字节完整核验后只读复用，不重传全部wheels、不写旧失败目录、不恢复旧入口。

最终命令`python -m pytest -q -p no:cacheprovider tests/test_native_stage1.py`（mask=-1、独立basetemp）为**32 passed、0 failed、0 skipped，9.84s**；新增真实Git回归包含独立/父仓库、缺refs、错HEAD、index字节保全及封存legacy ZIP恢复，另覆盖严格复用依赖的实际CPU文件消费链。相关compileall、diff及PS5.1语法通过；未重复未变化的native S/A测试。本轮未操作服务器/模型/CUDA/Nsight，未重跑完整Q0或旧分析；没有研究语义裁决、新资格或原状态升级。下一步仅协调审查全新阶段1修复包，成功后仍先审查实际build/GGUF身份，不自动进入阶段2。

## 7.148 Windows native阶段1离线固定交付（2026-10-13）

**本项只完成本地交付与CPU验证；目标机阶段1尚未执行，不授GPU资格。** 延续7.147的候选窗口/支持范围，[唯一native入口§6](native_llama_window_and_adapter_v0_1.md)记录固定源码、构建/转换身份和下一阶段独立预期。用户授权单一ZIP、构建/转换/身份检查；不运行服务器、模型/CUDA初始化/Nsight，不自动续至受控桥接或自然P0/P1。Gate13限定PASS、Gate14 NOT_RUN，旧Formal/Raw/BLOCKED/UNKNOWN/NOT_ASSESSED保持；用户DOCX与原件未修改、不stage。

新增`native_stage1.py`、阶段1PowerShell入口及本地packager：固定增量bundle以前次目标机401ed420945472c9612d84b21f6a477abe3c4671为前置，固定llama d81235049384534c167caea52b85a694f6103d14浅源码/Git快照、NVTX3.1.1、CMake3.31.10、Windows/Python3.11 CPU转换完整wheels和SHA256锁。服务器不临时下载、不改变原推理venv/Toolkit/driver；读取原HF快照CSV及其23项字节身份，原manifesthash与源归档引用绑定，转换F16 GGUF另存，实际tensor类型/shape/offset与F16/F32计数来自GGUFReader，revision仍未知。

固定CMake实物中发现ABI编译成功后会运行CUDA架构检测二进制（即使sm89已设），因此仅在全新私有CMake内按原模块hash替换运行探测函数、保留原件与patch回执；不伪造compiler works或跳过编译/链接。构建仍调用已有cl/nvcc CPU工具，且图/native自动探测关闭、FetchContent离线。阶段1命令清单仅部署/CPU依赖检查/compile/convert/inspect，不能启动native-llama或collector。超时保留直接工具与后代UNKNOWN，不杀同名进程/重试/清理。

回传一个小metadata ZIP，含原始日志/退出、Git/toolchain/CPU回执、实际cache/probe原件、GGUF tensor表和build/conversion身份；不重复传送大GGUF/build/env。预留20GiB临时、45–120分钟估计，临时空间可超过长期50GB；长期必要新增约4–5GiB仅为估计，审查归档后再另列可重建副本清理，本轮没有删除。阶段1成功只能STAGE1_COMPLETE_NOT_QUALIFICATION，实际CUDA/native适用性仍NOT_RUN。

提交后最终调用链核查补齐控制解释器依赖：run固定使用已验证repo venv的jsonschema/pytest，Conda base仅stdlib bootstrap/部署和创建CPU环境，不能假设base已安装研究schema依赖。原推理venv不改包；9009db4生成的本地未分发候选ZIP被最终修正版取代，不是目标机部署或新attempt，不使旧数据/资格失效。末次交付相关回归25 passed、0 failed/skip，2.90s；PS5.1 parse及diff-check通过，未重复其余未变化的35项native回归。

阶段2独立预期已收敛到同scheduler/backend的确定性加法及自然Host读回：检查完整暖机/drain前缀、真实stream/event/correlation和ownership、已完成成员与后提交排除；只有成功drain与依赖闭包证据俱全才可讨论局部投影。源码调用名/时间先后不替代依赖；必要native closed-prior若涉及新适用性条款须另审。不借用旧device-wide声明、不自动启动自然模型。

tests-first实际RED包括交付模块缺失、HF原manifest未绑定、离线依赖检查缺接线、literal SHA不能导出bundle引用等；修复后最终命令`python -m pytest -q -p no:cacheprovider tests/test_native_stage1.py tests/test_native_llama.py tests/test_native_llama_scope.py`（mask=-1、独立basetemp）为**60 passed、0 failed、0 skipped，29.58s**。其中阶段1实际文件链以CPU工具替身替换compile/convert，不声称目标构建；真实Git小fixture bundle、实际私有CMake函数、真实PowerShell错误角色入口和原始stderr/失败回执通过。仅新增Python compileall、PowerShell5.1 parser和diff-check通过；未跑全量/完整Q0/旧分析。没有修改runner/completion/流/同步、S/A/B/registry或签署语义。普通工程交付无研究裁决；真实构建及native桥接的资格仍待后续实物，不包装为已通过。

## 7.147 Windows llama.cpp候选native最小接线与CPU文件链（2026-10-13）

**当前是候选Engineering本地实现，不是新引擎资格/采集授权。** [native窗口/接线0.1](native_llama_window_and_adapter_v0_1.md)为本项入口；保留7.146的操作性Device Exposure口径、PyTorch自然baseline、Cpre受控角色。Gate13限定PASS、Gate14 NOT_RUN及旧Formal/Engineering/Raw/BLOCKED/UNKNOWN/NOT_ASSESSED不变；用户DOCX和scripts未跟踪大ZIP保留、不纳入提交。没有服务器操作、模型/CUDA/Nsight执行、旧分析重算或完整Q0。

`LLAMA-NATIVE-WINDOW/0.1.0`显式候选起点在首次处理固定输入前，含自然batch准备/H2D；首/末实际Host token返回后为锚点，文本/持久化窗外，共用三个半开窗口公式。它不冒充旧GPU-resident起点、不改签署0.1.1或授新Formal。固定d81235049384534c167caea52b85a694f6103d14、32/2/batch1/warmup3/repeat1、CPU greedy/no backend sampler、无graph；HF→GGUF F16允许非量化F32张量并保持revision未知、实际token逐值配对，不授HF数值/时延等价。

已实现独立native prepare/producer消费合同、共享C++编排与实际SDK入口、固定CMake及CPU文件CLI；spec/输入/binary/GGUF/build/conversion/执行commit与PID/TID/实际token贯通，角色仅Engineering，缺文件/变化/错角色配置、重封违规、EOS/partial/失败拒绝。五个真实backend/buffer同步点按固定源码字节patch成新的编译输入，保留调用数/顺序与参数、不修改vendor原件、不增加同步；记录真实native handle/设备/线程/调用序号及source callsite，未继承frame的工作线程保持未知。

新Raw→Canonical native适配复用现有设备UUID/PCI四namespace映射、官方四消息规则及S/A；共同trace point保留原引用/hash/clock，投影不提供依赖，必要已完成前缀保留/后提交排除。完整S两模式条件等价不是A数字相等，模式仍UNKNOWN；缺提交效果、错流/request/mapping、失败同步、未知依赖/诊断拒绝。native不泛用旧N1 RAW_PHYSICAL/opaque cudaMalloc例外；输出仅ADAPTER_CALCULATION_ONLY_NOT_QUALIFICATION，物理B未资格、D/Signature禁用。

固定官方原始SDK头/少量构建文本只读取得于忽略目录（不是安装）。真实头的`llama_process`参数为batch_ext指针，已用host语法负例发现上一页接口简写不能编译，最小入口改为该版本标准`llama_decode(ctx,batch)`并通过真实头检查；公式/旧结果不变。实际CUDA backend/目标VS14.38编译、转换后真实tensor事实、native scope资格仍未执行。

具体剩余差额是native窗前drain为scheduler/backend scope，不是旧device-wide；暖机历史闭合不能直接继承旧声明，现代码保留完整物理前缀并拒绝未知ownership。只在后续同backend桥接证明实际stream/event闭包后，才能决定必要的native局部closed-prior支持条款；不裁前缀或猜所有工作都属主线程。下一目标方案先仅构建/转换/身份回执，审查后最多1个受控backend桥接；闭合后才一对自然P0/P1，当前不交自动采集包或重跑V0/旧Q0。

验证使用编译的真实producer core＋CPU替身与合成SQLite、独立手算W/terminal/三窗口A；不是目标GPU证据。实际最终命令为`python -m pytest -q -p no:cacheprovider tests/test_native_llama.py tests/test_native_llama_scope.py tests/test_gate8_identity.py tests/test_gate8_boundaries.py tests/test_gate8_signed_time.py tests/test_v141_sync_semantics.py tests/test_gate9_diagnostic_review.py`（独立本地basetemp、CUDA_VISIBLE_DEVICES=-1），**200 passed、0 failed、0 skipped，54.12s**。仅新增三个Python文件compileall、Canonical boundary（7模块）和oracle独立性静态检查均exit0；不运行无关全量。原SDK/JSON header可选字节审查缺缓存时显式skip，不自动联网安装；本机已取得固定原件，CPU host语法检查使用真实SDK头＋声明-only CUDA/NVTX替身，本次无skip。代码审查补齐了缺submit效果、重封角色/量化、实际输入值及派生sidecar缺失等fail-closed；用户DOCX hash保持，旧测量代码/签署/registry零修改。

## 7.146 Device Exposure操作性口径与Windows首引擎源码核对（2026-10-13）

**用户已收敛范围：保留冻结A_device_wait交集/union定义，取消“完整GPU相关Host等待可识别性”前置；Windows/4090是当前唯一环境。** [现行0.2入口](device_exposure_scope_and_windows_engine_v0_2.md)统一论文提纲、解释与本地handoff；PyTorch自然路径是执行baseline，同窗常规活动/完整timeline是信息增益参照，Cpre保持受控机制Engineering角色。四对追加Pilot仍暂停，Linux/WSL/升级/换服务器未获授权；vLLM只保留为未来候选。Gate13限定PASS、Gate14 NOT_RUN、Raw/历史报告/BLOCKED/UNKNOWN/NOT_ASSESSED及全部数据角色不变。

Device Exposure是合格同步区间与根据completion证据恢复的必要GPU活动并集的操作性预算；已完成成员仍保留、跨sync不直接相加、投影与完整物理W/B分开。“大致等于全部GPU相关Host阻塞”仅未验证假设，无独立ground truth/误差证据，不新增完整等待指标或采集设施。同步copy/依参数阻塞的已知支持缺口与原拒绝门保留；建模不豁免缺身份/边界/映射/依赖/诊断，不制造W/B或新增opaque-copy许可。用户本轮改变研究解释范围，不改冻结公式、registry、质量或排除规则，不重签/重标旧Formal。

实际复用Formal最终审查§4与已保存C0/Cpre区间，无重算：G1 GPU activity增加不唯一决定同步exposure，wait差方向混合；API sum=union与Host补集在该数据未显示额外信息。N1完整W/terminal/单sync provenance有限支持自动可审计解释，标准完整timeline＋同语义可手工恢复；稳定P0收益、10/5ms保证、P1组成迁移P0不受支持。Cpre 87.646953=38.946574+48.700379ms保留，residual前/后terminal和copy差不推因果/全部等待。零unattributed/守恒/Gate PASS不替代信息增益，不以大wait选点。

首引擎源码固定llama.cpp v0.6.0真实commit `d81235049384534c167caea52b85a694f6103d14`。官方simple→sample→sampled-token/logits getter→context/scheduler synchronize→CUDA backend `cudaStreamSynchronize`调用链已只读核验，CUDA输出get先提交D2H copy；这是原生完成行为，不添Cpre且不保证wait较大。VS2022/CUDA sm89/graph开关及Qwen2ForCausalLM转换识别已查，但现CUDA12.4/MSVC14.38/driver目标构建未验证，GGUF F16转换及数值/token身份未取得。未下载/安装引擎、不跑CUDA或模型。

下一项本地工作仅native窗口/identity声明与最小文件链设计：自然process含input preparation/H2D，与MC0.2 GPU-resident start确有差异，须显式窄域声明裁决后接线；实际native多TID/stream/context/correlation/event/Host-ready桥接增量不等重跑全Q0。不强插同步统一路径、不授新引擎/完整B。后续目标只提议构建/模型身份、必要桥接和一对自然32/2 P0/P1；当前不制作包或服务器命令，不新增大矩阵/collector/监控。

本轮仅文档/官方固定源码检查；无业务代码、测量schema/registry或签署协议变更，无pytest/重算/采集。32个相对文件链接目标存在、diff-check通过，新增公共内容私有路径/凭证模式检查无命中；代码/测试/合同/schema/registry/签署协议零diff。用户DOCX实际SHA256保持、原未跟踪大ZIP保留，均不纳入提交；本地handoff继续忽略。0.1的Linux环境待决及旧四对Pilot“当前下一步”均已标为历史，避免冲突入口。

## 7.145 自然完成支持范围裁决与首引擎适用性收敛（2026-10-13）

> 历史方案；当前范围/Windows硬约束与首引擎优先级由7.146取代，下方Linux待决不再是前置。

**优先级调整已执行：四对C0/Cpre追加Pilot暂停；当前只审查自然推理支持范围并准备首引擎方案。** [唯一新入口0.1](natural_completion_engine_applicability_v0_1.md)复用7.143/7.144、B4局部Prefill及Formal审查，不重追w11、84个memset或旧UNKNOWN。Gate13限定PASS、Gate14 NOT_RUN、全部原数据角色/失败报告及UNKNOWN/NOT_ASSESSED保持；不安装引擎、不改业务/合同、不运行测试/分析/实验、不交付采集包。

自然复制裁决为**C：当前实例证据不能可靠拆分内部等待，保留已批准API预算，不制造W/B**。重新对照研究设计v7.1物理blocking条款、Pre-Pilot协议v2.1、MC0.2 §6/§10、签署G12-ROUTEA/0.1.1及两registry：明确正文要求参数依赖blocking识别，而现registry没有异步copy参数到completion scope的恢复规则。A registry的显式submit处理及“Async不保证非阻塞”是有限处理，不等于完整blocking覆盖。此项解释/证据缺口修正7.144可能过强的“未发现违例”读法：尚未证明某实例被遗漏为unsupported，但也不能保证全部参数依赖阻塞已覆盖。若将来证实unsupported completion，仍须fail closed，不能用本页豁免；新增内部等待/opaque-copy政策需另裁决。

实际只消费已保存block1/G512引用：runtime37815/corr197682，copy1.874498ms、8-byte D2H/Host类型未确定、后成功stream sync35.553µs；不由82.682µs先完成或`.cpu()`整体Host-readable推断copy内部等待。Cpre预算迁移与自然内部等待可观测性、实现正确性分别记录，不将零unattributed/守恒/Gate PASS说成完整解释。旧Formal限定结果/原件不改，不发布新的科学有效性或全部GPU阻塞claim。

仅比较固定vLLM v0.20.0与llama.cpp v0.6.0官方平台/模型/源码；推荐前者的Linux、单GPU/UniProc、eager/非async、单请求HF Qwen2配置子域。固定源码自然路径为pinned token copy→event record/synchronize→Host列表，非插入Cpre；已有S/event公式复用，但新平台、event生命周期/实际流与设备、request/token桥接须增量验证，Windows资格不自动继承。llama.cpp虽可Windows构建，仍需GGUF/数值及native路径资格，不默认替补。vLLM自然input preparation位于执行步骤内，与旧“输入已驻留GPU后首次forward”起点不同；新引擎窗口建议含自然preparation，须独立边界版本批准，不能为套旧窗口额外drain。

集中待决仅为Linux新栈及该引擎窗口子域，不需用户选择底层文件组织。批准后最小本地adapter/独立event正反例，未来提议一次受控桥接加一对32/2 P0/P1（1受控进程/1profile、2模型进程/1profile）；30～60min/12GiB临时数据为未批准估算、安装/环境大小未知。无相关服务器环境目标，当前无需查询原Windows或操作服务器；不新增长期副本/监控/Q0全重跑。后续按工作量/资源选点，不以wait比例挑选，公平保留同窗baseline、零变化/API主导/无增益或不确定结果。四对旧计划保留暂停说明；用户DOCX/未跟踪大型原件保留，不stage、不清理。

本轮验证仅文档：新报告及历史计划的21个相对文件链接有效，公共新报告私有路径/凭证检查通过；runner/analyzer/tests/scripts、contracts及签署0.1.1零diff，用户DOCX hash保持`7e630e4a…`。未运行pytest、模型或离线计算；不是新资格证据。fetch只核对远端，不变更执行/分析身份。

## 7.144 完成路径科学边界、residual区间审查及四对Pilot待审方案（2026-10-13）

> 历史待审计划；四对追加Pilot已由7.145暂停，以下当时“最高优先级”不再是执行指令。

**Gate13限定PASS、Gate14 NOT_RUN；现有C0/Cpre仅Engineering局部证据，未来Pilot NOT_RUN。** [现行解释与计划0.1](completion_path_scientific_review_and_pilot_plan_v0_1.md)对应研究设计v7.1/Pre-Pilot协议v2.1、已签署G12-ROUTEA/0.1.1及分域/opaque批准边界。G32/G512、N0/Nmarker/N16原Formal结论不变；B1/B4与C0/Cpre不升级，旧w11仍Prototype。统一的是Host-readable completion，Cpre只是同端点下的显式干预，不能因wait变大而替换自然C0/G1或声称恢复全部GPU阻塞；vLLM只可讨论语义端点可移植，具体多进程/调度/流与ownership需以后适用性资格，不按同步位置强制统一。

复用7.143原输入/结果/分析绑定，仅执行5.416s局部Raw引用与独立半开区间算术，不重跑S/A/analyzer或实验。Cpre runtime38583/corr200922、physical354：Host包络87.646953ms，1820个已证明request后缀裁剪为709个union区间，wait38.946574；710个补集共48.700379ms。其中**48.658361ms在最后必要ArgMax完成之前，0.042018ms在其后**。完整Raw/table/rowid/correlation/提交引用及所有区间另存新忽略诊断目录；摘要SHA256 `1995babc7f1c31d4ac3dcb0ef16768e70f2b21da32ab4995657de51fb335ee14`，SQLite/pair hash前后不变。不能把残余全称返回/CPU/硬件/profiler开销，未构造物理W/B；CUDA API不是纯CPU、submit/non-submit不等阻塞/非阻塞、unattributed=0不是完整机制解释。当前未发现由这些记录证明的分类合同违例；若目标要求全部GPU相关Host阻塞，现证据能力不足不能文字掩盖。

论文提纲公平保留同窗常规baseline与无增益/反向/不确定结果、P0性能/P1观测分开；不迁移P1精确组成或把copy差解释为内部等待。拟同期4个完整配对block、C0→Cpre与反向各两次，共8个新P1进程/8profile、0P0；固定512×4/o2/w3/r1与现自然实际流/Host边界，仅Prefill局部资格。方向/次数/记录/比较/硬停已在待审计划锁定，无试跑、重试、替补、自动扩预算；真实Pilot角色/八槽顺序接线仍是将来最小实现，不能改旧Engineering名称。依据两旧driver192.687/261.610s、有限目录字节，预算估计45～60分钟/临时5GiB；长期50GB十进制政策不变，实际服务器总量/清理回执未取得，不称已清理。补充Formal须另版本协议和未来新采，现Formal不改。

本轮只更新一份审查/计划、当前索引与进度/handoff；未改runner/测量/分类/schema/合同、未生成可采集入口、部署包或清理命令，不跑pytest/完整Q0/CUDA/Nsight/模型。文档链接、残余源绑定/独立算术、隐私/diff和用户DOCX不变检查为实际验证；官方资料仅用于解释现合同及未来引擎架构，不新增宽泛调查。最高优先级：协调审查本四对Pilot范围/预算后，再决定本地最小角色接线与交付；当前无服务器操作。用户DOCX和未跟踪原ZIP保留不stage，原Raw/BLOCKED/UNKNOWN/NOT_ASSESSED不改。

## 7.143 Cpre闭合异线程历史前缀修复与C0/Cpre局部离线收口（2026-10-12）

**C0/Cpre Prefill局部Engineering离线审查完成；原batch/collection BLOCKED不改，Request/Decode仍不准入。Gate13限定PASS、Gate14 NOT_RUN保持。** [当前审查7.143](batch_load_prefill_review_v0_1.md#7143-cpre闭合历史前缀修复与最终局部对照)复核12,169,554-byte ZIP/SHA256 `71ee4b6d618bf12acf937acac75673c06453236531af4d25eab2da765b14fd19`：CRC/安全路径/无重复、111文件、110项主清单与21项静态子清单全部匹配；主清单SHA256 `2054367978a6d584fb72b45f2a07a3d211ed8580a2d16127af890689d41b3c42`。原C0 ZIP嵌入副本与已核验c181d834…原件相同。Cpre执行401ed4209454，目标PID59636 exit0、producer COMPLETE、collector38.625s/exit0/export PASS；旧错误52.027s真实复现为`COMPLETION_PATH_PRE_SYNC_PREFIX_SCOPE`，不是模型/采集失败。

10,491个窗前活动包含338个异线程提交（4个TID分别提交79/78/77/104条），全部同PID/device/context/trace stream/clock、在成功device drain实际返回前完成，FIFO观测顺序无冲突。G9分域合同§2.2/2.5已将历史隔离与request后缀单主线程分开；额外要求全部历史TID等于新增sync TID属于局部消费者实现过约束。仅新局部结果schema `exposedpath-completion-path-prefill/0.1.1`按已核验drain接受这类历史，保留逐线程Raw ID引用；旧0.1.0重读仍执行原规则。pending、错scope/流、缺drain/映射/依赖、后缀异线程/身份冲突及两模式歧义门不改。历史清单不是当前request的W，不构造完整物理W/hidden/B；S/A/B公式、runner/completion/流/同步、registry、冻结协议与Formal结果零diff，无新研究语义裁决。

新独立派生目录复用已保存Canonical/projection，复核完整输入/执行/结果hash文件链。Cpre后缀1,820成员、1,820依赖边、唯一ArgMax terminal，两模式成员/边/terminal一致；后提交D2H排除于预同步，进入随后helper的1,821成员集合。C0结果与旧保存值逐字段相同；两组共同配置/输入/模型快照/runner字节及8个实际token一致（29184×4、6556×4），非early EOS，w3/r1。C0计算/严格reader为49.346/51.247s，Cpre55.956/53.975s；直接Raw唯一correlation联结与独立半开区间并集再次复现5个同步交集和守恒，未调用S/A作为此Raw审查的oracle。读取的原封存文件计算前后hash不变，无export/完整Q0/采集。

Prefill单位ms，C0：T249.447084，Host53.371575/API194.976979/wait0.026304/residual1.072226/unattributed0，GPU活动union105.585714；Cpre：T235.969299，Host98.868381/API49.054879/wait38.971918/residual49.074121/unattributed0，GPU union94.752606。新增预同步墙钟87.646953=wait38.946574+residual48.700379ms；copy148.126383→0.725352ms，helper sync wait两组均0。只支持此Engineering个案中completion位置改变已观察预算落点，不把API差当精确内部等待、不把单次总差当稳定收益或纯因果效应。两组各84项首ready之后Decode提交效果缺口保留，UNKNOWN/NOT_ASSESSED不改，physical B/Formal/D/Signature不授。

tests-first原文件链1 failed/8 passed（同叶拒绝），版本兼容红例1 failed/13 deselected；最小修复后14 passed。相关集成命令`python -X utf8 -m pytest -q -p no:cacheprovider tests/test_completion_path_closed_prefix.py tests/test_completion_path.py tests/test_completion_path_report.py tests/test_completion_path_reference.py tests/test_completion_path_driver.py tests/test_gate8_engineering_scope.py --tb=short --junitxml=.local/diagnostics/completion_prefix_review_v0_1/release.xml`：**129 passed/0 failed/0 skipped，135.33s**。补prefix order反例及夹具确保四个TID确实异于main后，最终`python -X utf8 -m pytest -q -p no:cacheprovider tests/test_completion_path_closed_prefix.py --tb=short --junitxml=.local/diagnostics/completion_prefix_review_v0_1/final.xml`：**15 passed/0 failed/0 skipped，41.63s**（与129项重叠，不相加）。包括旧版本行为、源/hash/版本篡改、pending/错drain/流/依赖拒绝及真实producer→合成Raw→文件reader；CPU不是目标资格。修改文件compileall、diff与闭集代码自审通过；未委派外部审查，不冒称独立review。

本轮只完成现有证据的离线结论；无需服务器操作/重采/新交付包。旧7.142 Cpre待执行指令转历史。用户DOCX及未跟踪大型原件保留不stage，不清理；准确派生/源码/输入hash及实际分析commit在忽略的handoff索引绑定，不用文档HEAD替换19f7/401执行身份。

## 7.142 成功报告消费修复、C0复核与Cpre-only交付（2026-10-12；历史，当前见7.143）

**本地接口/CPU验证和C0局部复核完成；Cpre NOT_RUN，原batch BLOCKED不改。Gate13限定PASS、Gate14 NOT_RUN保持。** 原ZIP4,303,788 bytes/SHA256 `c181d83490ed13fd17eb6377f23eda76f95d793fc892f7fe022ab0feec4b4435`，清单SHA256 `1f61502caf07e209c687d5bc1ba3be55550530cda719f94dc3e7cadb1a6379cd`；直接核验CRC/安全路径/无重复/104文件与103项全覆盖哈希，静态子清单15项也匹配。仅展开新诊断目录，原ZIP/Raw/报告不改。

最早失败是未profile的driver强读成功报告不存在的error，不是模型/collector/export错误。C0执行`19f7c6020abf5b607bdb59eb10deee50593c26a9`，目标PID64776 exit0，collector36.859s exit0、单次export PASS；`gate8-qwen-engineering-collection/0.1.0`成功对象合法省略error。仅该明确成功版本允许缺省/null，显式错误、错版本/status/qualification、采集失败、缺结果及result/manifest/runtime/launch哈希冲突仍拒绝。CPU替身不再无条件添error:null；后续loader、run/commit/clean、token lineage和逐值配对保留。

新独立回执使用原`completion_path_scope.load`复核保存值与完整来源/准入，51.049s。C0 Prefill249.447084ms：Host53.371575/API194.976979/wait0.026304/residual1.072226/unattributed0ms；API submit193.452450/non-submit1.524529ms，互斥守恒成立。四样本token为29184×4、6556×4。84项同线程/clock且首completion之后的Decode提交效果缺口保留；Request/Decode=`NOT_ACCEPTED_LOCAL_REVIEW_ONLY`，不授物理B/科学有效性/零丢失，不追认原batch。

tests-first旧成功分支复现KeyError（初轮29 failed/1 passed，含新helper缺实现）；单Cpre预算红例3 failed。文件链测试发现夹具receipt命名不同、其11起的token序列经三次两token暖机后应为17/18；对齐夹具/独立手算预期，未改研究门。旧PS预算文本断言改为单双槽核对并补实际PS5.1错预算早拒绝。最终命令：`python -m pytest -q -p no:cacheprovider tests/test_completion_path_report.py tests/test_completion_path_reference.py tests/test_completion_path_driver.py tests/test_completion_path.py tests/test_gate8_diagnostic_collect.py --junitxml=.local/diagnostics/completion_report_repair_v0_1/release.xml --tb=short`，**100 passed/0 failed/0 skipped，65.07s**；部署三个report/reference/driver文件55项为其子集，不相加。修改脚本compileall、PS5.1解析及diff通过；CPU producer→合成Raw→Canonical/S/A→consumer不是CUDA资格。未跑全量/Q0/GPU/Nsight。

当前`completion-path-remaining-delivery/0.1`只含一个新Cpre模型进程/一条P1，绑定原完整C0 ZIP/清单、preflight/claim/final、原执行字节及旧/新Git内容兼容证明。既有production Python和schema/registry内容不变，仅未profile的控制层消费者/launcher与CPU引用检查变化。当前实字节仍严检明确Git/LF→CRLF形式，不任意更新旧期望或归一化。默认A仅部署/55项CPU/C0引用复核，回执审查后才显式B；新prepare核对模型内容/输入/config/设备/runner hash与逐值token。新batch/目录/回执，不恢复旧入口、不重采C0，不因commit不同泛化失效。固定512/b4/o2/w3/r1、FP16/eager/SDPA、mask3、实际流/completion/S/A/warning门不变；失败/单槽结束即停，无retry/替补。comparison明确旧/新执行与工程角色，API差不是原内部等待。机器路径及提交/交付SHA仅在忽略的handoff索引维护。用户DOCX和未跟踪大型原件保留。

交付自审补充：旧C0展开若嵌入新静止树，会将历史`process.json`的PID误当成当前writer/PID复用风险。先补三项位置红例，再将引用展开限制到独立diagnostics，不嵌入新采集/归档树；回传保留完整C0 ZIP、绑定元数据及复核回执，旧PID记录仍在封存ZIP内。原静止门和新采集writer检查不改。修改后的driver12项通过（3.99s，属于上述100项中的受影响子集），脚本compileall/PS5.1解析/diff再次通过。完整实际引用入口CPU复核在原位置版本52.039s通过；后续仅引用位置/归档接线改变，不重复S/A重算。最终待审包以当前实际提交锁定，先前本地预打包版不作为服务器入口。

## 7.141 完成路径窄域Engineering实现与待审交付（2026-10-12；历史，当前见7.142）

**用户已批准7.140的本地实现；实现/确定性CPU文件链已收口，目标机新采集NOT_RUN。Gate13限定PASS、Gate14 NOT_RUN，旧B4 Request/Decode/attempt BLOCKED保持。** [现行审查末节](batch_load_prefill_review_v0_1.md)新增`COMPLETION-PATH-ENGINEERING/0.1`，仅未来两个新P1、C0→Cpre、512×4/每样本2输出/warmup3/repeat1。C0同诊断包装不同步；Cpre仅测量Prefill token0 Host复制前对持有的实际current-stream同步一次。不切流，不改Decode/暖机/Host-readable completion，不新采P0、不改冻结A/B、API分类、warning或Formal产物。

复用verified模型入口、Git二进制源码seal/直接解释器/native设备/内容身份、逐样本token和Canonical/projection；新pass ledger0.6、execution0.1及独立prefill-result0.1显式绑定闭集variant/实际PID/TID/native流/同步次数。旧自然domain reader拒绝该新role；独立局部入口保留完整Raw，Request/Decode明确NOT_ACCEPTED_LOCAL_REVIEW_ONLY，不能冒充成功domain。只有同线程/clock且实际始于首ready后的提交效果缺口可隔离；影响不明、边界/映射/实际流/诊断冲突仍硬拒绝并停止后续组。

新增同步的当前request必要集合复用原S，包含已完成工作、不包含后提交D2H；完整drain前Raw FIFO前缀另行核验/引用，不为setup/warmup伪造request ownership。两模式必要成员/边/唯一terminal必须相同，前缀实际流/线程冲突拒绝；不回填全局默认模式，不借N1资格发布自然默认流完整物理B。时间线保留last-submit、公共hook、copy/D2H、新旧sync及Host completion；sync墙钟、必要交集、residual、API预算和Prefill A分列，API差值不是原内部等待。UNKNOWN/NOT_ASSESSED与未记录依赖的既有支持假设保留。

tests-first初始19项缺模块红例；局部回归暴露独立手算fixture缺correlation、真实暖机前缀计数遗漏，以及core消费者导入launcher时捕获CPU替身造成旧batch路径污染。手算预期未改变，补独立来源映射/真实次数，纯sync-observation报告下沉到core、旧入口委托同函数，恢复旧路径而非改测试追绿。中间7 failed/166 passed不是终态；修正后相关48 passed。最终命令：`python -m pytest -q -p no:cacheprovider --basetemp=.local/completion_release --junitxml=.local/diagnostics/completion_path_release/cpu_results.xml tests/test_completion_path.py tests/test_completion_path_driver.py tests/test_batch_load_diagnostic.py tests/test_batch_load_driver.py tests/test_gate8_diagnostic_entry.py tests/test_runner_token_ready.py tests/test_gate8_identity.py tests/test_gate8_engineering_scope.py tests/test_n1_model_domain.py tests/test_n1_preprofile_identity.py tests/test_gate8_diagnostic_collect.py`，**241 passed/0 failed/0 skipped，124.35s**；没有全量/Q0/CUDA/目标模型资格复验。`python -m compileall -q exposedpath analysis exposedpath_v141 scripts/completion_path_diagnostic.py scripts/gate8_diagnostic_collect.py`、PS5.1只解析及diff检查通过。CPU真实producer→合成SQLite→Canonical/S/A与seal→profile调用边界均为替身验证，不冒称目标机采集。

交付自审新增两个布尔值冒充device/token整数反例：先2 failed/33 deselected，再强化闭集execution实际字段类型，未放宽身份。最终部署同组命令`python -m pytest -q -p no:cacheprovider --basetemp=.local/completion_delivery_final --junitxml=.local/diagnostics/completion_path_release/delivery_cpu_results.xml tests/test_completion_path.py tests/test_completion_path_driver.py tests/test_batch_load_diagnostic.py`：**83 passed/0 failed/0 skipped，53.12s**；与241项覆盖重叠，不能相加。修改文件compileall/diff再次通过。

交付前置固定服务器`2af14b11dd990d159ff0b3204d26a1527244079c`，新执行/分析commit由同次提交绑定。默认A仅部署/源码实字节/相关83项CPU/compile，mask=-1不初始化CUDA；静态回执协调审查后才可显式B。B最多两模型进程/两profile，既有Nsight duration120s/collector壁钟300s、export180s、外层driver900s；预计15～25分钟、至少12GiB临时空间（估计，长期50GB政策不变），硬失败/固定两槽结束即停，无自动retry/续采。每阶段单ZIP保留输入/身份、Raw/REP/SQLite、producer/partial、独立Prefill结果/全部诊断与清单；UNKNOWN writer仍拒绝强行封包。本轮不操作服务器、不清理、不推进CUPTI/84追索。用户DOCX及未跟踪大型原件保留不stage；handoff和含机器路径的交付索引仅本地忽略。

## 7.140 同负载完成路径聚焦复核与待审设计（2026-10-12）

**Gate13限定PASS、Gate14 NOT_RUN，原B4 Request/Decode/attempt BLOCKED保持；仅完成本地证据解释和待审方案。** [7.139审查补充的完成路径方案](batch_load_prefill_review_v0_1.md)不新增实现/合同、部署包或采集入口；暂停CUPTI及旧84调用追索，不扩大batch/output，不重算整批A/B、pytest或实验。

原SQLite只读查询独立复现协调回传：成功copy runtime38583/corr200922为43.854908ms；同目标context1/trace stream7的516 kernel在API区间内的裁剪并集30.867774ms，全部唯一成功launch在copy入口前返回。最后ArgMax kernel11846/corr200916在copy入口后43.723446ms结束；32-byte D2H347随后完成，比token-ready sync入口早131.723µs，因此该sync既有合格投影wait=0。SQLite SHA569b6907…前后不变，无同线程嵌套runtime/driver记录可分离API内等待；重叠及其余区间不反推Host等待/纯CPU预算。复制整体维持CUDA API，原局部Prefill A不重算/改写。

唯一待审设计`COMPLETION-PATH-ENGINEERING-DRAFT/0.1`：同512/b4/每样本2、warmup3/repeat1、现有自然实际流/Host-readable completion，最多两次P1、C0→Cpre；只在测量Prefill token0 Host复制前增加一次已核验实际流同步，Decode不改。Raw以argmax/copy/API/physical sync的唯一correlation/context/流/lifetime核对实际流，必要集合保留完整先行工作、不含后提交D2H；默认模式不回填，沿原两模式后缀成员/边/terminal投影义务。当前自然消费者拒绝干预，未来须获准窄域身份/分派及独立反例，不能冒充G1自然路径或借N1授default-stream物理B。

预先接受非零/零wait、copy不缩短及其他不支持解释的结果；同步包络不全部记wait，不按结果改负载或重试。身份/边界/drain/映射/依赖及新诊断冲突仍拒绝，84后续效果缺口不借本方案解决。局部数字和手算只为Engineering设计/接线预期，不授科学资格/Pilot/Formal，不改变冻结协议。原ZIP/Raw/BLOCKED、UNKNOWN/NOT_ASSESSED及用户DOCX保留；当前只有方案审查，无需用户服务器操作。

## 7.139 Batch4 Prefill局部证据闭合审查（2026-10-12）

**Gate13限定PASS、Gate14 NOT_RUN保持；B4 Request/Decode及原attempt仍BLOCKED，但Prefill可独立作局部Engineering投影A审查。暂停7.138的CUPTI native后续，不再追索旧84实参。** [审查0.1](batch_load_prefill_review_v0_1.md)复用已封存归档/身份/映射核验，实际读取原Canonical、source-bound execution和projection，复核成功drain到首ready的全部前缀；没有服务器、模型/CUDA/Nsight/export或整批重算，不修改生产代码/合同/旧报告。

依据G9分域合同§2的受影响窗口失败传播，不按Decode标签排除：首未知runtime38606/corr201238发生在原首ready23694390270ns之后4,879,492ns。B4 Prefill的1,821活动（1790 kernel/2 copy/29 memset）、4,810 API均有合法scope/ownership/实际映射；10,491已观察前缀在成功drain前完成。两个同步的后缀成员8/1821、唯一frontier、返回前完成及LEGACY/PER_THREAD必要成员/依赖边相同；旧整request图取Prefill诱导子图的1820边与本次一致，未删除物理S/B或回填mode。未记录incoming依赖仍是原支持假设，UNKNOWN/NOT_ASSESSED保持，非完整物理W/B资格。

在新本地派生目录仅选择原Prefill窗口、复用原A互斥计算；B1结果与既有observation逐字段一致，B4五类A为Host69.544101/CUDA API82.895299/Device wait0.025024/residual0.123167/unattributed0ms，T152.587591ms；B1为45.683467/53.771358/0.525502/0.136086/0ms，T100.116413ms。Device wait占比0.016400%对0.524891%，GPU活动union104.121389对52.541659ms，不能将GPU工作量等同暴露或由一次结果推稳定趋势。B4首token同步投影wait0，内部sync贡献25024ns；copy API43.854908ms保留API预算，不拆内部等待，zero unattributed不代表全机制已解释。

局部检查/计算为本地CPU、两条件各约4.7/4.8s，不是pytest、完整Q0或新目标资格；读取源文件集合计算前后hash不变。实际分析代码dc78fc88，执行仍2af14b11；runner/S/A/Engineering scope/G9 domain相对执行源码零diff。本报告只记录现行合同的局部审查，当前domain入口仍按request统一拒绝，没有新增partial-phase reader/schema、没有改判旧attempt或将小汇总作成功domain。新摘要在忽略的诊断目录；用户DOCX/原ZIP保留。当前Prefill负载问题已有可解释个案，无必要服务器步骤；完整B4 Request/Decode仍缺提交效果证据，不为此自动实现CUPTI或重采。

## 7.138 Batch4 memset参数取证本地可行性及CPU原型（2026-10-12）

**Gate13限定PASS、Gate14 NOT_RUN保持；旧B4仍BLOCKED，新B4/目标CUPTI验证NOT_RUN。** [可行性审查0.1](memset_parameter_feasibility_v0_1.md)不再追索旧84次实例。当前Nsight安装说明/已采表未提供实际count/native参数的肯定入口；不宣称工具永不支持。匹配CUDA12.4.1 Windows官方redistributable已按元数据校验：CUPTI12.4.127/API22、cudart12.4.127及nvcc12.4.131仅供CRT头文件；未安装或运行CUDA/Nsight/DLL。候选cupti64_2024.1.1.dll hash560a3659…不是目标Nsight私有cupti64_129.dll hash47b244aa…；实际目标加载/API/订阅仍未知。匹配12.4文档也明确单subscriber及Nsight冲突，不能借较新版本能力或并行订阅。

新增仅隔离CPU证据原型0.1.0与native结构体复制EXE，不接科学消费者或runner、不生成采集/部署入口。实际SDK字段支持ENTRY复制count/value/stream、EXIT return；MEMSET correlation绑定driver而不是runtime。CPU原型保留零长度参数事实、明确非零MEMSET映射、非零缺效果/冲突三种状态；参数/身份/桥接/流生命周期未知、跨线程native0借用、correlation复用、零零未知时间及多活动bytes求和均拒绝。UNKNOWN/NOT_ASSESSED不变，A/B/schema/registry/冻协议未改；CPU合成数据不授目标资格。

tests-first初始3 failed/32 deselected（缺实现），身份负例2 failed→2 passed、映射负例3 failed→3 passed；native编译初稿出现SDK依赖/编码/无关activity头padding错误，补匹配CRT、UTF-8及最小callback头文件，不改vendor字段或屏蔽错误。最终显式配置匹配SDK/MSVC19.44 x64后：`python -X utf8 -m pytest -q -p no:cacheprovider --basetemp=.local/memset_proto_final --junitxml=.local/diagnostics/memset_parameter_feasibility_v0_1/cpu_tests_final.xml tests/test_memset_parameter_prototype.py`：**40 passed/0 failed/0 skipped，1.09s**（34纯Python及6 native CPU）；只证明本地CPU，非服务器MSVC19.38资格。修改文件compileall、PE imports、源码无动态加载/vendor调用、来源/hash/文档链接/用户DOCX保全及diff检查通过；没有完整Q0/全量/旧Raw重算。审计5922 bytes/SHA256 `59d24cbc2d991edfd355b99bf33887a82bf143ceb49cf13041e53eaef216e4aa`，存忽略的本地诊断目录。

唯一下一候选：先审查独立CUPTI加载/订阅握手＋一个zero/64-byte tiny CUDA验证，全部通过才考虑最多一次同路径512×4/每样本2输出/w3/r1的新B4参数诊断。建议总15min/2GiB、最多两个进程（tiny120s＋模型300s），预算和运行部分尚待审，失败不重试、不fallback、不扩设施。零参数不自动证明无依赖，非零缺效果保持拒绝；新实例不能补旧84次，新增插桩时延不是自然性能，独立provider不自动获得现Nsight Canonical/A资格。当前没有安全可直接执行的重采包/服务器命令，不要求用户现在操作服务器。7.137旧实例收口保持；本轮原ZIP/Raw/报告、用户DOCX及未跟踪大型归档不动、不stage、无清理。

## 7.137 Batch4 memset提交效果有界审查收口（2026-10-12）

**Gate13限定PASS、Gate14 NOT_RUN保持；B4投影A仍BLOCKED，停止旧84次调用追索。** [审查0.1](batch_load_memset_effect_review_v0_1.md)在前次已核验原包/来源链上检查46表、六个correlation列及Raw→Canonical实字段：KERNEL13408、MEMCPY348、MEMSET120、runtime/driver40769记录全部一致，无过滤/桥接遗漏。84个corr除API自身外无命中，同线程实际嵌套driver也为空，callchain均null。114成功memset中另30次有28×1536及2×16 bytes活动，但不能补推84次的count或效果；全部缺口在Decode、API累计50717ns。未知零提交/替代路径/观测缺失未被解决，不改为non-submit/Host，不按小比例放行。

SQLite/REP/Canonical/投影hash与原manifest一致，read-only/immutable查询前后不变；新cross_table_audit（179218 bytes/SHA f97cbfb6…）及evidence_binding_and_results（9530 bytes/SHA f05ddf44…）独立保存。官方Qwen5.17源码hash与已有目标机快照一致；PyTorch2.6 GEMM/Fill路径只能缩小可能来源，不能证明旧实例参数/调用栈。现有可读接口不足不等于工具永不支持，原Raw/ZIP/BLOCKED、UNKNOWN/NOT_ASSESSED均不改。

已准入B1 A及两组P0可复用：P0 Request分别141.544300/231.408800ms；B1 P1三窗口Device wait0.525502/0.525502/0ms，原生trace占比0.293920%/0.524891%/0%，互斥/子类守恒及阶段拆分沿用已核验结果。B4已观察GPU union138.484709ms、实际token/边界成功仅为观测事实，不发布B4 A/wait占比，不用活动量或未恢复映射当零。四槽和两profile全已执行，无续跑槽位。

唯一下一方向为待审的同次native参数＋activity窄域取证，不是盲目再跑Nsight：实际count/return/context/native stream及明确correlation/生命周期。CUPTI12.9.1不支持与现Nsight subscriber并行，目标SDK/ABI未核验，因此只提出独立诊断设计、模型前不支持即停；无新增collector实现/部署包/服务器命令，新实例不能追认旧84次。7.136的REP追索停点转历史。此轮只完成本地审计来源/算术/链接/隐私/diff检查及文档提交，不重复完整测试/Q0/analyzer或采集；用户DOCX和未跟踪原取证ZIP保留不stage，无文件清理。

## 7.136 Batch-load失败实物审查、离线续算及拒绝诊断传递（2026-10-11）

**Gate13限定PASS、Gate14 NOT_RUN保持；batch-load整体BLOCKED，B1投影A通过、B4投影A拒绝。** [集中审查0.1](batch_load_failure_review_v0_1.md)独立核验103907198-byte原ZIP（b290a96f…）、CRC、安全路径及258项清单（157ff327…）：259文件/零遗漏，包含静态原件副本。执行2af14b11dd99的四个模型入口均exit0/producer COMPLETE，两个profile/export成功；264源码实字节及显式Git/LF-CRLF表示、身份/隔离预检/模型输入引用、实际512×1/4、每样本2token及warmup3通过。模型本体未本地重算。

最早实际拒绝B4 Decode的84次成功cudaMemsetAsync缺同进程/correlation activity，首runtime38606/corr201238；不是08_batch、模型异常或类别注册遗漏。114次memset中84次缺映射，总API墙钟50717ns，不据小比例宣称局部影响；Raw没有count或runtime→driver桥接，邻近cuLaunchKernel/corr201239的成员不能借用。零提交/替代路径/丢失均未被证明，不改为non-submit/Host/opaque，不补零。

新派生目录复用原Canonical/投影，每run复核一次实际S/A/B并释放大型对象；原两份约3.38GiB domain只流式核验不另展开。B1三窗口与原A一致，互斥/子类守恒与阶段拆分通过；B4仍SUBMIT_MAPPING/A空。已观察子集两模式成员/边/terminal及全部API尾部独立检查无新冲突，但缺提交效果仍阻止完整W/可信A。自然默认流完整物理B不授予；同类官方warning按旧规则，原UNKNOWN/NOT_ASSESSED与Raw/BLOCKED不改。两组新pair仅性能/逐样本token观察，非验收；GPU已观察union约71.678→138.485ms不能作Device wait。

tests-first最小修复仅控制层丢失叶原因：显式model-scope-rejection/0.1绑定结果SHA、request身份/原reasons，实际collector→batch拒绝上下文接通；严格门、退出含义、parser/registry/runner/S/A/B/baseline/冻结统计未改。初次5项失败后5 passed；扩大回归1 failed/81 passed为CPU替身漏目录，未弱化反例。最终`python -X utf8 -m pytest -q -p no:cacheprovider --basetemp=.local/batch_failure_release tests/test_batch_load_scope_failure.py tests/test_batch_load_driver.py tests/test_batch_load_diagnostic.py tests/test_gate8_diagnostic_collect.py tests/test_gate9_domain.py`：**83 passed/0 failed/0 skipped，50.93s**；修改文件compileall/diff通过。正例显式MEMSET、缺映射/近邻driver负例及真实报告→batch拒绝CPU接线不冒充平台资格。

最高优先级仅特定memset提交效果证据；4/4模型和2/2profile已全执行，无续跑槽位。先判断现存REP/调用资料能否给出真实成员或可核验的零提交依据；不交付盲目重采/部署包，不按文档HEAD重新部署。7.135采集指令转历史；本轮无服务器/GPU/Nsight、删除或新研究裁决。用户DOCX和未跟踪原取证ZIP保留不stage。

## 7.135 同完成路径512/batch1与batch4 Engineering本地准备（2026-10-11）

**Gate13限定PASS保持，Gate14 NOT_RUN；本轮仅实现／CPU验证／待审交付，未操作服务器、模型、CUDA、Nsight或采集。** 用户明确批准固定4模型进程/2profile、512输入/b1与四份相同输入b4/每样本输出2、warmup3/repeat1、FP16/eager/SDPA/自然Host-readable路径；[最小合同与计划0.1](batch_load_engineering_plan_v0_1.md)限定整体batched request，不扩为并发用户研究，不追认旧w11或重开Formal。Device wait/API预算/S/A/B公式、原官方warning处置及UNKNOWN/NOT_ASSESSED保持，不添加API内部wait拆分。

tests-first补闭集batch binding、真实prepare→seal→profile调用边界、runner暖机/全batch Host向量→逐样本token文件→配对消费者→合成Raw/Canonical/投影/S/A文件链及独立手算。复用现有入口和消费者，新ledger0.5/token与execution0.1/独立batch-input-receipt0.1显式关联；先暴露旧收据不接受token产物，再将其纳入完整artifact/hash集合。runner只增加已读向量长度验证；没有新增Tensor读取、同步或更改正常完成边界。EOS、错role/version/配置/input/token、缺correlation/drain、错误线程/流、未知API/依赖/warning仍拒绝。CPU fixture的OS/模型/CUDA均为明确替身，不授目标机batch4资格。

新批次固定B1P0→B1P1→B4P0→B4P1；失败立即停并保留NOT_RUN，无自动重试/替换。报告保留P0/P1三窗口、signed差、A绝对量/占比、activity union、API/copy/D2H及sync入口/返回/最后必要完成和原始point/引用；投影suffix不冒充物理B。缺Driver表保留UNKNOWN。默认交付仅部署和CPU检查，协调回执审查后才显式采集；预算/空间及归档后定向清理见计划，当前不删任何文件。

实际相关回归命令：`python -m pytest -q -p no:cacheprovider --basetemp=.local/bld_final tests/test_batch_load_diagnostic.py tests/test_batch_load_driver.py tests/test_gate8_pair.py tests/test_gate8_identity.py tests/test_gate11_warmup.py tests/test_gate11_pilot_files.py tests/test_gate12_formal.py tests/test_gate13_prepare_identity.py tests/test_n1_model_domain.py tests/test_runner_token_ready.py tests/test_n1_preprofile_identity.py`，**287 passed/0 failed/0 skipped，138.48s**。末次版本门补充后，`python -m pytest -q -p no:cacheprovider --basetemp=.local/bld_release3 tests/test_batch_load_diagnostic.py tests/test_batch_load_driver.py`：**52 passed/0 failed/0 skipped，29.66s**；两次覆盖有重叠，不相加为独立样本。`python -m compileall -q exposedpath analysis exposedpath_v141 scripts/batch_load_diagnostic.py`、PS5.1仅语法解析及diff检查通过；未运行无关全量、Q0、真实CUDA或模型。

早期测试失败包括缺新模块、旧artifact集合不含token，以及CPU fixture的导入替身/模型inventory/native设备替身作用范围，均有原输出留在本地；报告D2H字段初稿误读顶层改为Canonical attributes.copy_kind、缺Driver保持unknown；PS5.1调用传参问题修为环境传入只解析。最后实际producer报告未知版本负例先失败（未拒绝），再为batch配对消费者补显式版本门，通过最终52项。交付自审另将CPU故障fixture移出静态回传树，避免伪process/UNKNOWN污染真实writer检查，保留JUnit/原CPU日志；交付定向`python -m pytest -q -p no:cacheprovider --basetemp=.local/bld_delivery_finish tests/test_batch_load_driver.py`：**9 passed/0 failed/0 skipped，11.35s**。没有修改测试预期以削弱生产拒绝门。

实际服务器cleanup_receipt原件仍未定位，删除数量与释放空间待核验，不能从30候选推断实际。旧w11平台更正与历史报告保持，DOCX用户SHA7e630e4a…及未跟踪原取证ZIP保留不stage。当前最高优先级仅协调审阅本次固定Engineering交付；服务器模型采集尚未由本窗口执行，不自动启动Gate14、Pilot、Formal或第二轮同步干预。

## 7.134 w11原执行路径与Formal G512有界实物对照（2026-10-11）

**Gate13限定签署PASS保持，Gate14 NOT_RUN；没有业务、测量、统计或资格变更。** 用户调整优先级为旧w11执行/计算口径对照，暂不设计复制API内部等待类别。[集中对照0.1](gate13_w11_execution_comparison_v0_1.md)按新明确授权从已核验REP的字节相同副本离线export；本地Nsight2026.1.1.204，exit0、1.609s，新SQLite27336704 bytes/hash adee4a45…，原REP/副本前后hash均981db025…，原件未改。不是采集、GPU运行、服务器操作或完整analyzer复算。局部脚本独立读取Raw/已有Formal时序、保存历史Git源快照，不调用S/A/B；无测试/完整Q0重跑。

重要更正：Raw应用日志StringIds18与目标PID57540的CUDA inventory映射证明，本REP实际**RTX6000 Ada、torch2.5.1+cu121、CUDA12.1、transformers5.13.0**，不是4090。启动/日志声明Qwen2.5-1.5B目录、synthetic512/b4/o16、w3/repeat5/streaming，5request及每request16device sync成立；kernel实际CUDA device0映射inventory GPU3，编号不同不矛盾。模型内容/revision、backend、输入digest、Host token值及当时源码hash仍缺。7.132的22.586%Prefill/3.768%Request只是4090另attempt同名汇总，不能代表本Raw；6000旧汇总为39.890%/12.044%/15.474%。五个Prefill/Decode实值均值与6000舍入值吻合，Request均值差0.0042756ms且旧报告无REP hash，仍不强绑定完整旧A结果。

找到bench_eager、single/matrix launcher及v2 analyzer/汇总器；首Git3a64db2（7/17）晚于Raw7/8，Prototype tag abab013（9/2）及已有交付payload保全相同旧执行逻辑/原源文件，但不是精确当时源码身份。旧S按先提交且sync入口仍pending筛选，A为sync∩候选活动union，不是整个sync时长；旧matrix为逐次比例均值，与当前总预算比/完整W/ownership分开。无新写复原脚本冒充原始入口、无Prototype升级。

实物request1 Prefill argmax提交结束93.763376ms→device sync93.804097～271.153139ms，最后ArgMax在271.050822ms完成；sync177.349042ms、旧规则观测候选交集112.633243ms、入口至terminal177.246725ms不混同。decode-step1 sync32.688596ms，候选交集16.157432ms。旧Prefill初段1-byte D2H/stream sync不是token末尾；对应decode-step无copy。当前G512 block1同样复用原记录：copy内部→D2H→stream sync，末尾同步入口前已完成，token0/1现有投影wait0。平台、输入、batch、输出及完成路径同时不同；未证copy或标记是主因，没有具体证据显示当前sync算法错误，不修改冻结结果。未来唯一实验问题仅是同平台/输入下device completion-before-copy与自然host-readable路径的局部暴露位置差异，需未来独立合同批准；本轮不实现/采集、不自动Gate14。

服务器cleanup_receipt原件在已检查的transfer/server_receipts/当前交接入口尚未找到，同名测试替身不算；已非阻塞请求准确本地路径，实际删除数量/空间**待原件核验**，不把30候选/38.95GiB写成已释放。不再清理其他Gate或重扫服务器；原UNKNOWN/BLOCKED/Raw及用户DOCX保持。仅更新必要解释/进度/交接、局部完整性/算术/链接/diff检查，提交不替代执行99f3bae/分析e19。最高优先级为结果解释及取得已经存在的清理回执定位，无必须的新研究执行步骤。

## 7.133 Gate13服务器定向存储收口准备与复制API解释更正（2026-10-11）

**Gate13限定签署PASS保持，Gate14 NOT_RUN；不改变冻结A/B或原Formal结论。** 用户授权仅准备服务器30个已归档domain副本的PowerShell5.1清理命令，不删除本地研究资料、不操作服务器、不重跑完整分析。[聚焦解释/存储入口](gate13_cuda_api_storage_review_v0_1.md)关联7.132时序与完整取证归档；当时30项合计41820242784 bytes=38.948136GiB。用户回传最新73.33GiB盘点，成功清理后约34.38GiB，满足50GB十进制长期预算的估算；仍有两条跳过/错误原记录未在本地取得，不能称已实审或精确完整空间已确认。脚本只读既有盘点目录两项问题、记录与候选相交关系，路径/格式/数量无法识别则删除前停止；不新扫YLQ或全机PID。

更正此前“.cpu()先完成再stream sync”的歧义：目标机2.6.0+cu124 CUDAFunctions.h（4027 bytes/hash343d0cd1…）与官方2.6 Copy.cu路径为复制helper内部cudaMemcpyAsync→cudaStreamSynchronize，之后才取得host token。直接核验block1/G512/P1 runtime37815/correlation197682 cudaMemcpyAsync_v3020总1.874498ms；D2H347仅0.544µs，提前sync入口82.682µs结束；sync runtime37816/correlation197683成功35.553µs，唯一physical354/context1/stream7。没有同线程已观测嵌套API，但driver表/栈未采集，不能证明无driver内部等待。现合同token-ready wait0成立于已恢复必要集合/同步包络，不是所有GPU相关Host阻塞为0；API预算非纯CPU，unattributed0不等全部内部机制解释，opaque等待不补造W/B。

新增一个独立定向清理脚本，不接旧retention或实验入口、不改运行代码：固定清单/归档/manifest/外部回执四重字节绑定、明确30叶路径/reparse/当前长度hash、全项先锁读检查再删除、每项删除前复核、异常即停、源树外新回执及已删/未删/释放字节/ZIP恢复引用；默认只预检查，真实删除需操作者确认当前分析/采集已停止。原writer UNKNOWN/BLOCKED、marker/manifest保持；清理不证明不存在所有写者、不是Formal资格变化。保留REP/SQLite/Canonical、原始与失败报告、输入/身份、完整ZIP及最终结果，其他Gate/环境不动。全包已核验档保留，清理后展开源树不再完整，来源定位转由既有归档member+hash及新receipt承载，不重写旧清单。正式归档和已接受结果未变。

实际只读命令`python -X utf8 .local/gate13_copy_api_evidence.py` exit0，生成全新本地解释诊断，没有运行S/A/B。最终定向`python -m pytest -q -p no:cacheprovider --basetemp=.local/c13k tests/test_gate13_archived_domain_cleanup.py`：**15 passed**，19.12s；含缺失/hash/来源/越界/重复、reparse、文件写占用、部分删除失败、未删清单完整性及两项盘点范围关联，均为Windows真实PowerShell临时fixture。先红测再实现；初始pytest默认Temp权限和长路径失败改用仓库内短basetemp，独立PowerShell缺Get-FileHash时改用标准.NET SHA256，无弱化检查。PS5.1解析及diff检查通过；不称服务器真实删除或已腾出空间。无全量/Q0/GPU/Nsight/模型/新样本。用户DOCX与未跟踪完整ZIP保持原字节，不纳提交；本地handoff及单次交付路径在忽略的.local。最高优先级仅是两条已有盘点异常原记录的定向核验/命令审阅，不新增研究采集任务。

## 7.132 Gate13逐block展示、低wait路径解释与历史w11对照（2026-10-11）

**Gate13限定签署PASS保持，Gate14 NOT_RUN；没有新采集、语义修订或资格变化。** 用户要求只读解释当前低Device wait、定位历史较重w11，并澄清空间压力指服务器。[集中解释0.1](gate13_completion_workload_review_v0_1.md)复用60Host原值、90A窗及六block冻结结果，保存三张全样本图、90窗逐次比例/75项分量预算汇总、六个token的原row/correlation时序。总预算比与逐次比例均保留；P0 Host性能与P1 trace投影A分母/clock不混用，不删除长值/负差，不重跑S/A/B或统计bootstrap。

实际执行99f3bae的相关runner/NVTX/boundary/drain/N1/model入口与当前读取内容一致。block1 G32/G512/N16六个token：argmax提交返回→token-ready range开始2.725608～4.668297ms，包含多种Host工作，不能全算NVTX成本；D2H在后续stream sync入口前8.212～82.682µs完成，支持必要后缀内token-ready wait为0。完成后point准备延迟2.0358～3.9617ms不能归成同步前成本；实际marker调用包络10.9～99.4µs。当前cudaMemcpyAsync登记submit，Async不等于非阻塞，API内部可能包含设备等待但本合同不进一步拆分；**低A_device_wait不证明全部设备相关Host阻塞近零**。Host预算波动不等CPU busy或硬件因果，不能由本批精确迁移P0。实际无网络流式发送，核心T_model-request排除下游文本/网络/消费者，不预设其必须位于其他进程。

唯一w11 Raw在`nsys_results/w11_p512_b4_o16.nsys-rep`，9677123 bytes/SHA256 **981db025cab3e4a43a099f11ae200d424d2f101186970490d9c33c2be5852e13**，与Prototype索引一致。对应旧4090汇总声明512/b4/o16、5 repeat：Prefill wait均值比例22.586%，Request 3.768%（不是整个request>20%）；旧汇总无REP摘要且来源日期与Raw历史日期不同，不把同名强绑定同一attempt。旧device-wide逐步同步没有当前host-token读取路径，legacy pending-only S/边界/软件、模型/设备身份不完整；无可消费SQLite及必需新证据，不导出或追认v1.4.1/Formal。batch4/output16的generic tensor能力不等支持域资格，EOS整批停止与每步token身份需另声明。仅提出未来512/b4/o2单轴Engineering候选，不执行或纳当前冻结方案，不以高wait选点。

服务器存储仅从已验证取证manifest盘点：30展开domain.json **41820242784 bytes=38.95GiB**，占当时源树97.73%；REP/SQLite约0.22GiB，不能先删Raw。准确机器路径/预期hash/member仅保存忽略的本地索引，不提交私有目录。完整ZIP/清单/外部终态与本地最终结果都保留；服务器原finish/BLOCKED与writer UNKNOWN不修改，当前服务器文件hash/空闲未查询。该30项是清理候选而非删除回执，旧UNKNOWN清理门未被绕过；本轮**无任何本地或服务器删除**，不追索旧PID或新增监控。用户澄清后，先前本地空闲/副本数值不当作服务器当前占用。

实际命令`python -X utf8 .local/gate13_completion_workload_review.py` exit0：60/90键全覆盖、顶层/API子类守恒、Request=Prefill+Decode、原时序唯一关联及归档30目标member长度通过；三图目视检查。bundled Python缺matplotlib，未安装包，采用现有Anaconda/matplotlib3.9.2/numpy1.26.4；只展示/算术复核，不是新GPU/目标平台资格测试，没有pytest/Q0/全量/完整分析或实验。用户DOCX修改与未跟踪原ZIP均保留，不纳提交；研究判定及旧报告不改。最高优先级是用户审阅解释与服务器可重建文件清单，无必须的研究采集/部署步骤；下一负载候选仅待未来另行决定。

## 7.131 Gate13外部取证终态补审与限定Formal最终裁决（2026-10-11）

**Gate13 PASS，严格限于已签署G12-ROUTEA/0.1.1路线A；Gate14 NOT_RUN。** [集中收尾](gate13_local_review_v0_1.md)/[最终机器裁决](gate13_closeout_v0_1.json)关联既有7.130完整分析和本次终态补审。60次执行、30pair/30profile、90A窗口、60条合格N1单sync B、公平baseline及六完整block统计全部接受；无排除/测量准入失败。PASS表示签署范围的执行与证据审查闭合，不要求效应为正，不授稳定性能收益、10/5ms精度、完整新版Q0、自然默认流物理B或Decision Gain。

直接读取用户新回传外部`forensic_receipt.json`：1071 bytes，实测SHA256 **b4f5f8eef7cfbf1dec47be0285b0d39c12c3503b82e3e464b62227ea8dc46172**，与预定值一致。status=FORENSIC_BYTE_COPY_VERIFIED_NOT_ACCEPTANCE、error=null；归档a3f2e05b…/1381808437字节、manifest87f60c78…、3586源文件/42790896265字节/4225成员及空目录与已核验离线输入一致；源路径由原run配置绑定，source_before摘要1231d92c…与封存清单/checkpoint一致。封存工具eb37e0e1…精确核验，成功终态仅在完整ZIP验证及归档后源快照等于固定快照、无覆盖发布后生成。末次源一致依据绑定回执和该控制流，不声称直接读过未回传的source_after_archive.json；不证明无全部写者、跨文件原子快照或零丢失。本地补审76e9a083…，conflicts=[]，关闭7.130唯一剩余缺件。

执行**99f3bae966f2fb794073ff4d7468233b6b8dd2ac**、授权性能分析**e19c308d1254feb0e643ae56429d5afd2ab6b4fd**、签署协议及其内容hash不变；收尾提交不冒充执行/分析身份。直接复用7.130逐run质量、独立Raw30/30、baseline及102冻结对比，不重算、不重跑测试/实验或全包hash。此次只新增终态审查和文档/JSON一致性、链接与diff检查；无生产代码、合同、统计、排除或样本变化。

结论分项保留：P1必要等待与N1单sync完整provenance相对常规聚合指标有有限解释增益；同语义标准timeline仍可手工恢复。G1 API嵌套/Host补集未显示非冗余数值增益；N1稳定收益与精细数量级不确定，六block不是精度/平稳性认证。不从A扣开销、不迁移P1精确组成到P0、不跨sync加总B。UNKNOWN、NOT_ASSESSED、opaque内部等待/未知size、原超时/BLOCKED/marker/Raw及7.130缺件机器汇总均原样保留，新裁决独立关联。历史Engineering/Pilot不升级。

没有必须由用户操作的服务器事项，没有清理或新部署包。最高优先级转为基于已保存全部结果的论文结论与限制整理，不自动启动G2/Gate14、新采集或数据清理；用户DOCX修改保留且不纳提交。7.130及更早“待回执/恢复/执行”指令均为历史。

## 7.130 Gate13完整取证原件与六block本地离线收口（2026-10-11）

**60逐run执行合同、30profile质量/公平baseline、90A窗口、60N1合格单sync B及六完整block统计已完成；Gate13仍BLOCKED，仅缺指定外部forensic_receipt.json原件。** [集中审查](gate13_local_review_v0_1.md)/[机器汇总](gate13_review_summary_v0_1.json)保存全部通过项与限制。用户授权的ZIP本地实测1381808437 bytes/SHA256 a3f2e05bbfbdda8bbba025fd016bdc60c7652cd001b1dd54f5a0aec65435e6ef；清单87f60c7841c1a71225a4ccffa297503fdfc63e193d9c4f99c2b9c1c8488d42fa。全部CRC、唯一路径/安全/大小/hash/完整覆盖通过，4225成员=3586源文件+633目录+5附件+清单。展开115.036秒，新版本本地诊断/派生目录不覆盖输入。源共42790896265 bytes；复制checkpoint不是最终外部回执，预期外回执hash b4f5f8eef7cfbf1dec47be0285b0d39c12c3503b82e3e464b62227ea8dc46172尚未实测，不能伪称服务器最后源复查已核验。局部ZIP/内部证据链通过不证明没有全部写者、跨文件原子快照或全会话零丢失。

按本次用户条件授权精确复核126冻结artifact：121不变、3性能分析接线、2此前签署状态文字。执行99f3bae966f2fb794073ff4d7468233b6b8dd2ac；新分析e19c308d1254feb0e643ae56429d5afd2ab6b4fd。协议G12-ROUTEA/0.1.1及hash d9204a80bf15ce810093ec53c506d4bf3eadd2f1ad71db8844cff330f0c7448b保持，测量/质量/baseline/统计无变化。新增严格独立授权/语义载荷适配绑定本ZIP、清单、协议及新分析源码；不是恢复旧seal或宽泛Formal白名单。e19最小Git blob运行材料不使用dirty main，不复制整仓库。逐run完整S/A/B重核与原语义结果完全相等，baseline独立重算完全相等，大对象逐run释放。全部完成3319.893秒，原7200超时/UNKNOWN/BLOCKED/marker/Raw不改。

直接复核60次实际warmup3/repeat1、固定五条件/平衡顺序/30pair、token/PID/GPU/输入配置及原Git二进制617路径覆盖；126实际LF/CRLF执行表示绑定通过。独立Raw不调用S/A计算函数，30/30验证point/drain/必要FIFO集合/terminal/单sync B及五类A，90窗unattributed=0且具体归属/阶段拆分成立，不用零unknown代替正确性。N1物理合格B60条（内部RAW_PHYSICAL、token-ready、干预分开）；54opaque allocation不拆等待/未知size、调用差异保留；窗外INVALID不改写。102冻结对比、全部signed差及whole-block统计保存，n6不称稳定性/10或5ms保证。

信息裁决有限且分项：GPU活动成本与必要等待、N1完整W/hidden/exposed/tail相对常规聚合有可审计解释；标准timeline+相同CUDA语义可手工恢复，不声称工具不可替代。G1 API sum=union，无模型实物嵌套增益；Host补集baseline已可给出，无非冗余数值增益。P0 G1 Request差均值16.7515ms、N1 marker1.3585ms、sync11.1567ms，均有block方向反转；N1稳定收益不支持/不确定。P1−P0 Request+2.1013%～+106.6759%，是扰动/次序/波动联合观察，不扣A或精确迁移P0。所有Raw实物、完整timeline/W在本地保留，公开只存精简数值表与来源hash。

tests-first授权/载荷适配13 failed红例→通过；本次收口实际`python -X utf8 -m pytest -q -p no:cacheprovider tests/test_gate13_offline_binding.py --basetemp=.local/diagnostics/gate13_complete_v0_1/test_closeout --junitxml=.local/diagnostics/gate13_complete_v0_1/binding_closeout.xml`：13 passed/0 failed/0 skipped（0.23s），该模块compileall与diff通过；既有性能36项/历史等值复用，无全量/Q0/实验。辅助本地审计误读dict、摘要大小写、局部前缀读法等初稿失败保留，修正读取不改变生产规则。用户DOCX保全、不纳提交；没有服务器/GPU/Nsight/新样本/清理。最高优先级仅取得已存在外部回执并核其身份/终态；不新增监控、权限试验或重复检查。Gate7～12限定PASS、Gate14 NOT_RUN保持。7.129准备复制及更早启动指令成为历史，不再执行。

## 7.129 Gate13一次身份补证收口与保留UNKNOWN的取证复制准备（2026-10-10）

**Gate13保持BLOCKED；停止进程追索，不再重跑静止检查/权限试验。** 直接读取用户新回传的`instance_receipt.json`：14910 bytes，本地原字节SHA256 `7536d1ee6f37953fd7b89e7b3115546aa5209a29075e379ebfd0f4d10d22340b`；未取得独立服务器摘要回执，不能冒称双端摘要核对。与既有quiescence封存记录逐项比较15组PID/创建时间及来源ZIP引用通过。实际管理员令牌false、PowerShell5.1.20348.2849、query_count=1、query_error=null。11个MATCHED_PRESENT仍UNKNOWN：ExecutablePath/CommandLine不可读，path match均null而非false；4个成功查询中未出现的原实例EXITED，无PID_REUSED。不把缺字段的原因直接归为权限不足，不推断这11个进程无关，不把历史descendant UNKNOWN回写为退出。

用户明确批准的下一步是**完整取证字节副本**，不是恢复原归档门。新增独立stdlib工具`scripts/gate13_forensic_copy.py`（gate13-forensic-byte-copy/0.1），不导入runner/analyzer、不查询进程、不运行模型/CUDA/Nsight/SQLite或旧pack/finish入口。固定源文件/目录集合，逐文件长度/SHA256与元数据绑定；拒绝越界、重复/大小写或规范化别名及reparse point。单个ZIP64流式压缩，保留所有原文件（含marker、partial、BLOCKED/UNKNOWN）及空目录；清单与新回执只写原树外。复制中校验实字节，复制后及ZIP完整验证后再次复核源集合/hash，ZIP逐项CRC/大小/hash/完整覆盖检查；任何变化、缺失、读取/空间/输出冲突保留失败副本并停止，无自动重试、覆盖或清理。压缩不依赖预期压缩率，容量门按源总字节+2GiB及逐项索引余量。最终ZIP摘要仅记录在外部回执，避免自身hash循环；ZIP内checkpoint明确最终验证尚待完成，后续本地须直接复核归档。

tests-first先暴露工具缺失，后补回执IO故障红例（备用输出失败不得掩盖原错，原成功但回执失败不能exit0）。实际最终命令：`python -m pytest -q -p no:cacheprovider tests/test_gate13_forensic_copy.py --basetemp=.local/diagnostics/forensic_final4_tmp --junitxml=.local/diagnostics/forensic_final4.xml`：**28 passed、0 failed、1 skipped，1.34s**；skip为本机无创建真实symlink权限，Windows reparse属性拒绝另有确定性验证。包含真实CPU CLI（与交付一致的`-I -X utf8`）、中文/二进制/空目录、UNKNOWN/marker原字节、错误哈希/路径/缺失/增删/变化、ZIP CRC/覆盖/篡改、空间不足及失败副本保留。compileall通过；仅本地CPU小fixture，不是目标机或Formal验证。独立私有PowerShell完整入口仅在本地PS5.1 AST核验，未操作服务器。

最高优先级改为协调窗口审查一次取证复制命令；无需部署分析commit或改checkout。旧元数据清单3586文件/42790896265 bytes仅用于空间估计，实际集合和摘要由复制工具在执行前固定。建议45GiB空闲，执行时按实际总量严格核算，不以清理现场腾空间。身份补证到此结束；字节一致的有限观察不证明不存在所有写者，也不是跨文件原子快照/文件系统镜像。完整原件回传并核验后才处理e19c308分析兼容绑定、新派生目录CPU收口；不改原报告/UNKNOWN/marker、0.1.1签署或S/A/B/统计规则，不恢复实验。Gate7～12限定PASS、Gate14 NOT_RUN及用户DOCX保持。7.128的“再次静止检查前置”由本节用户裁决替代，历史记录保留。

## 7.128 Gate13后处理超时审查与逐run等价复用（2026-10-10）

实现/拟分析commit **e19c308d1254feb0e643ae56429d5afd2ab6b4fd**，parent **6e34959da44e5ede9f3f04241934194713144301**；本节追加绑定的文档提交不代替它。[精确兼容记录](gate13_analysis_compatibility_v0_1.json)逐项核验126冻结Git artifact：121不变、3分析接线变化、2此前签署状态文档变化。状态仅REVIEWED_SOURCE_DELTA_NOT_ACTIVE_FORMAL_AUTHORIZATION，无新签署/运行白名单，原协议hash与执行99f3bae保持；完整原件及明确分析身份重绑定后才进入新派生Formal复核。根目录用户DOCX修改保留，不称clean或已可执行Formal新分析。

**Gate13 BLOCKED，60次执行完成仍待Formal资格审查；不恢复原批次、不新增样本。** [当前后处理入口](gate13_postprocess_timeout_review_v0_1.md)直接核验小诊断包86330 bytes / SHA256 `ae8c6deb277a61cb1dbd77ced06d9926df684f04221ba86f42e645625e803fea`；11文件/10项索引、CRC、安全路径、完整覆盖、全部大小/hash通过，索引`cf27ee85231bb2e3f1f55bd5f66dc53b8fa090f3359142e61aec1737cd29796f`，missing_files=[]。batch_report与formal_index的60槽位一致、30pair；执行/原分析仍`99f3bae966f2fb794073ff4d7468233b6b8dd2ac`。小包缺实际各run的输入、Raw/SQLite/Canonical/domain/baseline/token，不能据此判60次Formal合格。原7200.016秒超时、UNKNOWN_STOP_AND_INSPECT_NO_RETRY及BLOCKED不改。

完整日志与实际调用链确认每条profile采集3次、最终复核2次完整domain恢复；finish完成53次、另1次S中断。S累计4729.759秒，A/准入与N1 A/B647.184秒，G1 B0.281秒；转发日志与包裹计时不双计。依据固定串行顺序推定前26条各2次、第27条第二次中断、最后3条未复核，仅作定位而非身份重建。历史实物CPU profiling亦显示每sync依赖图和registry重复读取：N1 40494/G1 20776次registry load；558MB/930MB domain大对象成本真实存在，重复load不是声称唯一瓶颈。

最小实现只改最终复核接线：同一run的`DomainReview`先执行原完整S/A/B验证，baseline使用严格绑定的小准入凭据，仍独立重算count/sum/union/mapping并逐值对比。完整source/derived集合、hash/大小、代码/registry/schema、SQLite非空WAL/journal和Formal冻结artifact门逐次复核；变化、错run、缺文件、篡改、合同冲突均拒绝。逐run释放大型对象，无全批缓存；新增domain/baseline进度。原读取路径、S/A/B、baseline范围、signed差、whole-block统计/排除规则和超时保持。代码审查已补齐合同锁与sidecar负例，无剩余重要发现。

实际最终命令：`python -m pytest -q -p no:cacheprovider tests/test_domain_review_reuse.py tests/test_gate12_baseline.py tests/test_gate12_statistics.py --basetemp=.local/diagnostics/gate13_finish_timeout_v0_1/final_guard_tmp --junitxml=.local/diagnostics/gate13_finish_timeout_v0_1/final_guard.xml`，**36 passed/0 failed/0 skipped，244.25s**。含实际producer文件链及完整60 CPU替身批次，30条P1只恢复30次；tests-first最初10项因缺会话失败，sidecar红例2项未拒绝，子目录schema红例1项未拒绝，修复后通过。中间测试曾因运行中源码改动触发FORMAL_ARTIFACT_CONTENT，保留原回执且未弱化门，最终源码稳定后36项才是最终成绩。没有全量/Q0/模型/CUDA/Nsight或服务器执行。

历史封存G1/N1同输入最终无profiler比较：G1 **106.945→66.377s**，N1 **103.601→66.466s**，domain与baseline完全等值、输入hash不变、完整恢复2→1。各一次本地CPU观察，不是当前Formal实物或目标机性能保证；保留UNKNOWN/NOT_ASSESSED，旧Engineering数据不升级。用户DOCX原修改保持且不纳提交。

本补丁是纯性能/生命周期修复，不改变已签署研究规则，但新analysis commit不能静默继承0.1.1的99f3bae精确seal。原`validate_analysis`仍严格，新三文件源码差异须单独精确兼容绑定；相对冻结集另继承两份Gate12文档的此前签署状态提示变化，已审查不改条款，仍明确列入hash差异。不改旧manifest/domain/approval。唯一待审步骤：一次当前只读静止检查→协调审查→完整原树取证ZIP回传，外部新索引保留历史UNKNOWN、不删.active、不调用旧retention/finish入口、不清理现场。完整档及分析兼容绑定核验后才在新派生目录CPU复核60/30与统计；7.127的阶段B启动指令现为历史，不重启或替补。

## 7.127 Gate13 0.1.1阶段A原始回执审查通过（2026-10-10）

**阶段A回执审查通过；Gate12限定PASS保持，Gate13仍BLOCKED（待新正式批次与结果审查），Gate14 NOT_RUN。** 用户在服务器执行部署/CPU检查后回传`gate13_99f3bae966f2_static.zip`，本地直接只读消费原件：52961 bytes，SHA256 **b5a6e3c49ab7d4b5dcb64b78076516f05af3e44dae6fd9482230b473a3e993fc**，清单SHA256 **cf05fe98783f91b339b90aa5be69341286db0c1a2725fc0fefec240fb5ba95dc**。15文件/14清单、CRC、安全唯一路径、完整覆盖及全部大小/hash通过；没有解包或改写原件。原服务器transcript时间11:44:36–11:44:41，Windows PowerShell 5.1.20348.2849。

四步bundle verify/fetch/detached checkout/CPU检查原始exit回执均0，原日志与transcript一致。实际执行/分析 **99f3bae966f2fb794073ff4d7468233b6b8dd2ac**，不是后续文档HEAD。126项源码实字节逐项与该commit的Git内容锁及已签署允许表示核验，**56 LF、70 CRLF**；没有任意归一化后放行。最终clean依据实际CPU Git adapter和成功状态前最后`Tree($Target)`门（不是另有独立porcelain输出）。签署发布、delivery配置、执行脚本均与原交付逐字节一致；协议d9204a80…/发布1378c89d…/脚本26b88cad…及固定输入、模型清单绑定一致。CPU原回执`DELIVERY_CPU_PASS`，60计划槽位/30pair；静态receipt为`STATIC_READY_FOR_COORDINATOR_REVIEW`、error=null。

实际默认调用无`-CollectReviewedFormal`，源码/原始调用链确认没有模型加载、CUDA初始化或collector执行；没有重跑150项、完整Q0、实验或目标机命令。Git正常stderr经PowerShell呈现`NativeCommandError`，结合原exit0、成功消息和后续严格门，不判为部署失败。本地首次日志读取按UTF-8遭遇实际UTF-16 BOM，随后严格按BOM只读解码；审计脚本首次漏用冻结规范化hash的终止换行而拒绝，核对既定ASCII+LF算法后通过。这两项是本地审计工具错误，不是服务器缺陷，未改Raw或身份规则。

唯一下一步：用户经协调审查后显式阶段B，复用同一签署交付及固定launcher，不重包/重部署/恢复旧失败目录。五条件/六平衡block、60新进程/30profile、共同warmup3/repeat1及90GB门、200–240分钟粗估和失败即停规则不变；无自动重试/替补/扩预算。最终单ZIP回传后逐项审查，采集完成不等于Gate13 PASS或信息增益成立。旧BLOCKED、原0.1/seal、UNKNOWN/NOT_ASSESSED、G1投影A/N1合格单sync B/opaque/D禁用与用户DOCX保持；尚不清理任何证据。私有路径及完整阶段B命令仍在忽略的本地交付索引；下方7.126“新阶段A待审”已由本节关闭。

## 7.126 Gate12 0.1.1精确重签及Gate13唯一新交付（2026-10-10）

用户明确授权沿用已批准的研究范围和六block预算，审查后记录[0.1.1重签发布](gate12_protocol_signed_v0_1_1.json)/[收尾](gate12_closeout_v0_1_1.md)。**Gate12限定PASS，Gate13仍BLOCKED、Gate14 NOT_RUN。** approval ID USER-20261010-G12-ROUTEA-011，生效2026-10-10T03:25:04Z；是明确人类授权记录，不冒称密码学签名。协议内容hash **d9204a80bf15ce810093ec53c506d4bf3eadd2f1ad71db8844cff330f0c7448b**，发布文件hash **1378c89db04336102a9dc0ce53ef7b1ef17dd9c518320c060e74d39abaa5b669**，approval hash423852a31bd858a56255ca092bc370eb2349fc293ecab182c9fae7dbc562780e；原候选approval=null保持，旧0.1签署/seal/失败包/报告不改。

执行/分析 **99f3bae966f2fb794073ff4d7468233b6b8dd2ac**；文档/签署提交不替代执行。126个Git source锁、12schema/registry及资格引用逐项核对；原输入/模型/software/GPU、w3/repeat1、五条件/六block/60进程/30profile、固定组序/pass序、成块统计及质量门与旧payload一致。只有3修复模块/新增reference schema及此前2状态文档锁变化，无研究语义修改。五交付helper取99f3bae，和c5fcb77完全同字节；服务器前置e38fa918，旧0.1.1待审bundle直接复用。

实际链为binding/source/输入门→复制实际输入→finalize实字节hash/WMPC→严格Formal validate→保存manifest→verified入口重核。缺文件、原/副本变化、hash/config/身份冲突仍拒绝。兼容闭集仅G12-ROUTEA/0.1/0.1.1，reference仅protocol_version/protocol_sha256/approval_sha256；新schema源码必须在锁中，未知版本/混版本/未签署/旧角色升级或旧approval用于新内容仍拒绝。复用7.124最终**150 passed/0 failed/0 skipped/67.07s**原回执和负例，没有重跑测试/实验。此次仅生产validate_release、源blob/版本/hash、60计划槽位及交付检查；CPU替身成绩不冒称目标机或Formal样本。

唯一新签署ZIP `gate13_99f3bae966f2_signed_delivery.zip` **106697 bytes / SHA256 c223b8b09710a02727449cc3962b1b675916e73ea78440447f96daf30401f677**；15文件/14清单、CRC/全覆盖/全部大小hash通过，清单ada313cfbb92a4e29718709b13af0aadeadae8ab22e6acd042e1620d17a6ae27。bundle63889 bytes/a33d7393b1f50194d9343c8d10a7a69922c1aad23ed4e95bb1bdb0493dfe275e，verify/list-heads通过；launcher26b88cada4be7537fe6bfb4300fe29476d978fe11304be91157c9dce4c6d6472，PS5.1只解析两脚本通过。私有路径与完整A/B命令在忽略的本地说明，不提交模型、Raw、环境私有位置或本机配置。

最高优先级：协调窗口审查新包后，用户阶段A默认部署/CPU绑定检查，新的静态单ZIP审查通过才独立显式B；不用旧e38静态回执替代。不自动试采/重试/恢复/替补/扩预算，使用新输出目录；硬失败或固定预算完成即停。旧失败未启动模型/采集，仅最小CUDA身份查询、Formal测量样本0，不生成/升级样本。阶段B沿用200–240min粗估/90GB空间门，后处理/封包另计；完整batch仅STOP_FOR_REVIEW，不自动信息增益或Gate13 PASS。UNKNOWN/NOT_ASSESSED、G1投影A/N1单sync B/opaque等待不拆/D禁用保持。归档核验后再产准确可重建/重复文件清单及安全清理回执，当前不清理。本轮没有服务器、模型、CUDA/Nsight、追加Pilot/Q0或实验，用户DOCX原字节保持且不纳提交。7.125及更早待签署/旧阶段B为历史。

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

- 清单版本：`7.131`（下方较早逐条记录为历史；当前状态以顶部7.131及Gate摘要为准）
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
- 最近更新：`2026-10-11`（7.135）
- 权威研究主体：`docs/current/ExposedPath_研究设计.docx`，文内版本 `v7.1`
- 当前执行依据：原DOCX v2.1仍为Pre-Pilot；未来限定Formal使用[重签G12-ROUTEA/0.1.1](gate12_protocol_signed_v0_1_1.json)及[收尾边界](gate12_closeout_v0_1_1.md)，不覆盖原文；旧0.1签署保留。
- 当前研究阶段：Gate13签署0.1.1限定Formal最终审查PASS；60run/30profile、新e19完整质量和六block统计及外部取证终态补审闭合。原后处理超时BLOCKED保持，不恢复旧入口、不新增样本；Gate14未启动。
- 当前工作入口：根目录 `main`；目录约定见 `docs/repository_layout.md`。Gate7历史封存验收执行commit为 `8d64f7580d43d7c8e1cb7a416b459cec8f60b011`，closeout为 `16604d59b05ee6d7e8415f75dbaaa1be3be7cf8a`。N1历史Engineering执行V0为c21d835、Vmarker/V16为d25b4d1；新Pilot首批执行221f46c；审查提交不是新执行身份。
- 当前数据资格（7.131）：Gate6历史Engineering/Q0保持；[首批/暖机对照](gate11_warmup_policy_review_v0_1.md)及[共同w3 Pilot](gate11_policy_closeout_v0_1.md)仍只作政策依据、不混池/升级。已签署限定Formal60次执行/30条P1质量、归档终态及冻结统计全部接受，见[完整审查](gate13_local_review_v0_1.md)/[最终裁决](gate13_closeout_v0_1.json)；不是普遍测量有效性或完整新Q0认证。UNKNOWN/NOT_ASSESSED与旧资格边界保持。
- 当前 Gate 状态（7.131）：Gate0～7历史PASS、Gate8限定Engineering PASS、Gate9分域PASS、[Gate10仅选定G1三点一次可行性PASS](gate10_closeout_v0_1.md)、[N1独立Engineering PASS](n1_model_feasibility_closeout_v0_1.md)、[Gate11限定Pilot政策PASS](gate11_policy_closeout_v0_1.md)、[Gate12限定0.1.1重签PASS](gate12_closeout_v0_1_1.md)；[Gate13签署路线A限定PASS](gate13_closeout_v0_1.json)、Gate14 NOT_RUN。容量/精度/稳定性未授，旧报告/UNKNOWN/NOT_ASSESSED保持。
- 当前最高优先级（7.135）：协调审阅固定512/b1与b4同完成路径Engineering交付，阶段A部署/CPU回执审查后才显式B；不恢复旧Formal入口或追认Prototype，不自动G2/第二轮干预，不操作服务器或清理。
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

**Gate verdict：`PASS`（7.131，G13-CLOSEOUT/0.1，已签署路线A限定Formal）。** 新0.1.1六block60run/30profile完成逐run质量、公平baseline、统计及终态补审；旧首槽prepare失败和后处理超时报告不改。不是稳定收益/精度/完整新版Q0认证；有限信息解释、未显示增益及不确定结论均保留，见[集中审查](gate13_local_review_v0_1.md)。

- [x] `EP-G13-01`～`EP-G13-04`（7.131仅当前批准范围）按签署0.1.1完成G1两端点及N1三组、60run/30pair、公平baseline、六block统计、源/归档终态绑定及限定信息结论审查。分项支持/未显示增益/不确定不是统一正向收益；原编号保留，广域路线未执行且不追认为完成。无重采/补样本，Raw/旧报告不改。

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

**7.175现行补充：** COE新Pilot仍按7.174停止，不续7槽；同次Nsight参数取证只完成接口级
GO与一个0/64-byte微例设计，未实现/执行、未授COE/模型资格，详见可行性稿0.2。与Nsight
共存/入口覆盖未验证，不能默认为成功；无服务器下一步命令，不恢复独立CUPTI路线。

**7.131现行覆盖：** Gate13限定签署路线A最终PASS，唯一现行入口[完整审查](gate13_local_review_v0_1.md)/[最终裁决](gate13_closeout_v0_1.json)。外部取证回执已经取得并核验，无待执行服务器事项。下方各“现行覆盖”是历史；不重启阶段B/finish/pack、不重采、追索进程或清理。Gate14 NOT_RUN，有限信息支持与不确定/负结果照实报告。

**7.126现行覆盖：** Gate13首槽prepare失败BLOCKED，模型/collector未启动；0.1.1修复已重签绑定99f3bae，新签署包先交审查/默认阶段A，新的静态回执审查通过才独立显式B。禁止旧阶段B重试/续采。Gate12限定PASS及旧签署历史、Gate7～11和全部限制保持，下方旧“唯一下一步阶段B”为历史。

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

7.175（2026-10-16）：用户授权一次同Nsight memset实例取证的源码/SDK接口裁决；原7.174
失败事实不重查。已核验Nsight接口不足，不恢复独立CUPTI；选择native窄入口＋NVTX调用范围
作为接口级GO，仅设计一个0/64-byte微例及有界止损，不实现/打包/执行或放宽count0准入。
共存、覆盖与效果映射未验证，失败即停止，不改冻结规则、原Formal或任何历史资格/UNKNOWN。

7.135（2026-10-11）：用户批准同自然completion路径的512/b1与512/b4/o2、固定4进程/2profile Engineering单轴对照。只增加闭集批量身份、已读Host向量/逐样本token和文件链接线、报告及有界交付；不新增API内部等待拆分，不要求Device wait升高，不改变S/A/B或旧Formal冻结语义/资格。默认A部署CPU、回执审阅后显式B，失败不续采；本轮无服务器/模型/CUDA/Nsight/删除。Gate13限定PASS、Gate14 NOT_RUN；旧w11/失败报告/UNKNOWN原样保留。

7.131（2026-10-11）：指定外部取证终态原件hash/归档/manifest/源集合及已完成离线输入绑定通过，关闭唯一缺件，另作Gate13签署路线A限定PASS裁决。执行99f3bae、分析e19及协议0.1.1不变；无研究语义、统计、排除或样本变更，不修改历史BLOCKED/UNKNOWN或升级旧角色，不重算/重采/清理。有限解释增益与负结果/不确定并存，不自动启动Gate14或任何服务器任务。

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
