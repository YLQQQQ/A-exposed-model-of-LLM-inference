# CUPTI 提交效果桥与局部完成分析 0.1

阶段：Engineering 本地实现。权威方案仍为研究设计 v7.1、实验协议 v2.1 Pre-Pilot。
这是独立的新来源合同，不修改已有 Nsight Canonical、S/A/B、COE 或 Formal。

## 本轮解决的层次

原先的缺口在 API 实例到设备效果之间。stream/device/event 标识限定完成范围，却不能
单独说明某次 memset 是否请求了零字节，也不能把同流的邻近活动指定为该调用的效果。
本实现把两个关系分开：

1. ENTRY 参数快照、EXIT 返回、实际 runtime/driver 父子栈及分域 correlation，建立
   提交实例到设备效果的来源边。允许有实际 API 行的顶层 driver 提交，不虚构 runtime 父节点。
2. 实际物理同步及其提交边界，建立同步到必要设备效果的完成关系。已完成成员仍保留；
   不是仅选择与同步重叠的活动。

若记录到嵌在复制 API 内的真实 driver stream 同步，单独输出其成员、物理区间及活动交集。
缺 driver API 行时其 API 墙钟为 null，不把 callback 或物理同步区间伪造成缺失 API 行。
没有这种证据时，不假定复制 API 自带可分离的同步，更不把 memset 当作同步。

## 文件链与合同

- `scripts/native_cupti_timeline/`：固定 CUDA12.4 / CUPTI API22；预分配有界容量、逐线程
  父子栈，复制 kernel/Memcpy/Memset/API/sync/context/stream/event 结构，在缓冲返还前
  保存需要的字段和字符串。显式 open 才加载 CUPTI；DLL 导入和加载本身不初始化 CUDA。
- `exposedpath/cupti_timeline.py`：同进程显式会话；原 NVTX 调用仍在原位置发出，另记
  同一 CUPTI 时钟的原标签。不能与 Nsight/torch.profiler 同时订阅。此观测实现的开销
  不继承 Nsight 的资格，尚未在真实模型上评估。
- `analysis/cupti_timeline.py`：`cupti-timeline-capture/0.1.0` 到
  `submit-effect-evidence/0.1.0`；从原 producer 标签选择物理 drain、request、copy、
  sync 和 Host-token point。外部输入/producer/token 文件真实性仍须由运行合同绑定。
- `exposedpath_v141/submit_effect_bridge.py`：`submit-effect-bridge/0.1.0`。
  输出来源边、logical-zero、完整局部必要成员、terminal、COE及观察到的内部同步事实。
  复用旧 FIFO/区间算法，但不伪造 Nsight SQLite、clock、rowid 或 production A/B。

普通 runtime LaunchKernel/MemsetAsync/MemcpyAsync、stream synchronize，以及有实际
API 行的顶层 driver LaunchKernel/MemsetD8Async/MemcpyDtoHAsync 有显式窄域规则。
driver Memcpy 的 typed runtime correlation 必须与实际父子关系相符，或独立完整成立；
数值相同的跨域编号不构成关联。

count=0 保留逻辑调用与原 API 时间，不造活动。只在成功 drain 后、同一请求内、单线程
单 FIFO、无事件/图依赖、零调用在 copy 前返回、真实同步和 terminal 闭合的投影中允许空
设备效果节点。count>0 的效果缺失、payload 冲突、错流、缺父子、丢失或关闭失败仍拒绝。
历史 event 只有实际关联且被后续 context drain 闭合才列入前缀；请求内事件依赖不支持。
这不是对全部 CUDA API、并发、多流或所有输入长度的通用资格声明。

## 独立验证

手定小 trace 的必要成员为 kernel、64-byte memset、8-byte D2H，另有零 payload 逻辑节点。
物理同步 47–68ns，操作 40–70ns；独立预期 COE=20ns、原同步交集=15ns。真实 SDK 结构
Host 替身 → native JSON → 原标签/物理 drain → 来源桥 → 局部 S/COE 复现这些预期。
另有嵌套 driver 同步参考，物理交集为13ns，缺 driver API 行时墙钟保持 null。

本地新入口 **82 passed / 0 failed / 0 skipped**，包含实际头文件编译链接、DLL Host-only
加载、逐线程栈/参数快照、跨域冲突/孤儿/错 scope/缺效果等反例、PS5.1 禁采入口。
旧参数消费者、COE及预算等相关回归 **156 passed / 0 failed / 0 skipped**。
本地 MSVC14.44、Python3.12.7；目标 MSVC14.38、Python3.11.16 与真实 GPU 尚未验证。
命令/JUnit/build 记录在忽略的本地 `cupti_timeline_development_v0_1` 诊断目录。
这是 CPU 与 SDK 编译证据，不是 CUDA Q0、模型覆盖、平台资格或新的 Formal。

## 固定下一步

新 Stage A 仅部署、固定工具链/依赖字节核验、真实头文件构建及上述 CPU 文件链检查。
默认模型/微例/profile 预算均0，没有采集开关。目标机回执通过后，才能准备一个新运行的
同进程真实模型诊断；参数、所有必需活动、原标签、资源、丢失与关闭状态必须同次闭合。
不拿新参数补旧768/1024，也不恢复原七槽。若真实模型暴露新的未支持 API/事件/并发，
按具体来源拒绝并裁决，不据无效果填零或自动扩设施。

完整PS5.1正向启动演练发现本机缺`Get-FileHash`命令；新入口直接使用.NET SHA256，
不依赖该附加命令。正向CPU驱动替身及禁采参数均实测；不把它当成目标服务器证据。
完整包演练另发现`-I`忽略禁写bytecode环境变量；bootstrap在任何同目录导入前显式禁写，
独立子进程反例核对包目录没有新增`__pycache__`，保持精确文件清单。

82项本地成功不证明真实 PyTorch 已修复。新的采集来源、观测扰动和模型覆盖是剩余闸口；
`pure_host_blocking` 保持 null。旧 BLOCKED、UNKNOWN、Gate13限定PASS和Gate14 NOT_RUN不变。

## 固定交付与本地完整控制演练

执行/分析固定`7fa36efb340fe59a3138eb6132e162d6b0cbfc41`；后续交付记录提交不替代它。
`cupti_timeline_7fa36efb340f_reviewed_delivery.zip`为唯一交付，2,596,307 bytes，SHA256
`2957f49862b3eaac4e70b57e41220f7ce9a93886485fbbe3855d59b6645841da`。
14成员/13项清单，438源码表示；旧421科研源码逐Git blob不变。只保留原厂CUPTI头文件、
DLL及许可证的必要子集，避免无关HTML长路径；所保留字节与封存原资产一致。

最终包的本地CPU控制演练已实际经过PS5.1入口、真实Git bundle/deploy/clean、438源码
核验、PE导出、SDK提取、真实编译链接、82项CPU检查、末次身份与封包，exit0。演练明确
替换本地路径/Python3.12.7/MSVC14.44，回执标注为本地控制测试，**不是目标服务器A**。
原失败演练和最终日志/receipt/JUnit均保留在忽略的本地诊断目录。此前演练还暴露深测试
目录下无关HTML的长路径失败，最终资产子集不再含这些文档；未调整目标机系统策略。
目标服务器仍须严格核验前置8197f0d且clean、Python3.11.16/MSVC14.38和新鲜12GiB空间。
用户复制包、执行单独的A脚本并回传`cupti_timeline_7fa36efb340f_static.zip`后才审下一步。

## 目标Stage A审查与单次模型接回合同

目标A真实回传3,040,625 bytes，SHA256
`89265f8ddcce6b513457b1d40f44eda325e058f9cf654cf53d40d05476ae5376`。
231成员/230清单、CRC/安全路径/全部hash通过，438项源码逐Git blob或预定CRLF表示匹配。
原CPU日志和JUnit一致：82 passed/0 failed/0 skipped，3.23s。10个部署/编译/导出/测试
进程均exit0，无超时。目标Python3.11.16、MSVC14.38和SDK10.0.20348.0完成真实编译链接。
这次阶段A审查PASS仅证明构建、CPU文件链和身份，不证明实际CUPTI订阅或模型覆盖。

固定新B采用最新拒绝形状768输入、batch1、每样本输出2、3次原暖机、1次测量。
`scripts/cupti_timeline_model.py`直接继承原P的prepare/finish方法；仅Engineering构造器
版本化，不冒充旧Pilot绑定。原模型加载、输入内容和FP16/eager/SDPA均核验；加载/原暖机
位于订阅之前，随后开启一次session，原resident runner执行原drain及两个Host-readable
token完成操作。新增CUPTI marker sink和订阅位置有观测成本，不声称与旧Nsight时序等价。
该范围选择用于覆盖失败形状；不是重新采集负载规律或授予所有输入长度资格。

独立B包绑定真实A的receipt/manifest/delivery、全部封存文件、438源码与现有DLL；不换
checkout、不重编、不重跑A。固定一个模型进程/一个CUPTI session，零Nsight/零micro。
模型硬300秒，后续CPU离线消费硬180秒；新鲜空间12GiB。一次或硬失败停止，无重试或
替补。writer未知仍拒绝封包并保留现场。B成功状态只允许STOP_FOR_REVIEW。

producer/token/输入/模型/库/进程均绑定同次capture，完成标记使用CUPTI活动时钟。
从原producer标签恢复两条操作，继续使用7fa36ef来源桥/局部必要集合/COE；不造Nsight
SQLite、API墙钟或缺失设备效果。原暖机完成、实际模型配置和输入记录均单列并绑定hash。
即使模型或reader失败，后验A检查也执行，避免将前置副本代替采集后的身份核验。

独立CPU手定两token参考：第一操作交集20ns，第二仅D2H交集1ns；来源和producer的
真实文件链通过。真实PS5.1默认拒绝、显式CPU替身入口，以及控制器成功/模型失败/分析
失败封包分支均验证。所有CPU替身保持本地测试角色；目标GPU验证仍待用户执行固定B。
结果不得直接成为旧A或负载曲线数据；纯Host阻塞始终不由此授予。

固定控制版本`c58c65b94b5a33d6fb7b49cfa195edec4d348aed`，服务器native/analyzer checkout
继续保持7fa36ef。唯一B包`cupti_timeline_b_c58c65b94b5a_delivery.zip`为48,019 bytes，
SHA256 `9c24ad3f12d59794dc401706081e5de53e101d78ddc8b4b2b6709bfc6252d5fe`。
16成员/15清单、CRC/全部hash、控制源码Git字节与旧helper原件均通过；包内默认CLI
禁采和真实PS5.1命令解析通过。新接线27项通过，含来源桥的命令87项、原P/helper/A入口
回归68项均无失败/跳过，计数不相加。目标B仍NOT_RUN，实际覆盖必须依据新回传裁决。

## c58c65b目标B失败：初始化原始状态未保留

回传ZIP59,045 bytes，SHA256
`dc25d11710cd2a5ff3741f9a1204e3f2ed873544af4f9276573620ae80d7590f`；21成员/20清单、
CRC/安全路径/全部hash通过，固定包控制文件和A参考匹配。真实模型加载、内容/配置/
设备/输入检查及三次原暖机完成；PID13504退出1、未超时。异常为
`CUPTI_TIMELINE_SESSION_OPEN_FAILED:3`，位于测量drain/请求执行之前。

仅留下1条context、7条stream资源记录，无CUDA API callback或token marker。
原生client的`need`丢弃具体CUptiResult，catch又统一返回3；因此确切失败操作、kind及
原始错误码均未记录。资源已发出只能缩小初始化位置，不能将资源行当作API成功返回，
也不能直接断定CUDA_EVENT不支持、权限不足或订阅冲突。关闭记录closed=true且累计
errors=[1]，close_code=4不自动证明第二个独立关闭错误。

后验A检查成功；原子进程process.json保留PID/exit。顶层receipt.process=null来自抛出
先于赋值的控制流，不代表模型未执行。没有producer、token结果或COE输出，不能离线
补成成功，也不能拿本次资源记录修复旧768/1024。

下一步先在本地补齐初始化步骤/活动类型/原始CUptiResult的可测试记录，保留已有拒绝；
不先删必需类型或调整初始化次序碰运气。此轮只读审查，未改业务代码/原件、重采、
打包或操作服务器；目标模型覆盖仍BLOCKED。

## 初始化事实记录的本地修复

用户要求本地修复后，新增`cupti-timeline-startup/0.1.0`诊断对象，作为capture的
`initialization`事实扩展：有界记录每个初始化步骤、activity kind/name、状态域、原始
状态码及首个失败。CUPTI、Win32、版本/路径合同和异常分域；不从统一open_code=3猜
原始错误。实际CUPTI调用次序与原9种activity集合相同，不重试或跳过失败步骤。
原capture schema/活动字段、来源桥及S/A/B/COE定义不变；诊断不产生新的有效性资格。

session receipt改为0.1.1，按显式诊断版本核验并保留首失败，在Python异常中展示API、
kind、domain和status_code。旧capture缺该对象时保留None；未知版本/类型、首失败冲突
和成功矛盾均记录诊断错误，不能覆盖原启动失败或授予通过。失败进程的原始process.json
也被保留到顶层回执，解决先抛异常导致process=null的问题。

验证使用真实CUDA12.4/API22结构和签名，MSVC14.44编译实际client DLL及独立CPU ABI
替身库，覆盖stream/event、订阅、线程/缓冲/driver域启用、缺库/缺导出、版本冲突与成功
序列。替身由.def导出原SDK签名，未改SDK头文件；进程检查确认没有CUDA/CUPTI厂商库。
实际client DLL经Python隔离子进程到receipt也复现精确的注入步骤/错误码。
**注入错误码仅是CPU测试数据，不是服务器失败的原始码。**

最终相关126 passed/0 failed/0 skipped；本机Python3.12.7。原失败/成功JUnit、真实SDK
编译及注入capture留在忽略的本地`cupti_startup_*`诊断目录。目标14.38/3.11和真实CUPTI
初始化修复未验证，没有制作或执行新的服务器包；旧attempt、Raw及其UNKNOWN/BLOCKED
不改。下一步先固定新诊断的执行/构建身份和预算，再取得目标原始错误事实。

## API22活动控制策略0.2与事件关联验证（2026-10-21，当前）

7.227目标原件明确证明：直接enable CUDA_EVENT(kind36)返回21/INVALID_KIND，之前8类
成功；不证明旧768同因，也不修复1024缺效果。封存12.4.127 SDK头文件与本轮实际编译
头文件逐字节相同。枚举/结构可解析不等于接受单独enable。
[官方CUDA12.9发布说明](https://docs.nvidia.com/cupti/release-notes/release-notes.html#updates-in-cuda-12-9)
说明此前CUDA_EVENT与SYNCHRONIZATION收集耦合。将此用于API22的控制策略是有依据的
候选，**不是12.4目标事件实际发出的证明**，不得升级工具链来迁就它。

固定`cupti-api22-activity-policy/0.2.0`：显式顺序为RUNTIME5、DRIVER4、
CONCURRENT_KERNEL10、MEMCPY1、MEMSET2、SYNCHRONIZATION38、CONTEXT9、STREAM37；
末两项仍用EnableAndDump。只对成功启用前缀逆序disable，36不单独enable或disable，
无吞21/重试/fallback。保留全部9种原始kind的解码及必需证据检查；“保留记录类型”不等于
要求未执行的操作也有非零计数，真实event例必须存在相应记录才可通过。request内未知
event依赖继续拒绝，不把本微例变成S层event资格。原capture schema不改，初始化事实版本
0.2.0携带完整策略；旧0.1.0照读、不附新policy、不重判旧状态。session receipt新增0.1.2，
声明新policy不能接受旧/缺失/冲突元数据。关闭步骤另存原始码及首失败，不覆盖初始化失败。

Stage A独立版本0.1.2，仅部署/真实SDK编译链接/CPU/身份/新鲜2GiB；构建policy必须与
合同一致，不能把新库写成旧0.1.1诊断。旧A读取/历史配置保留，混用明确拒绝。新DLL在
新commit目录，不覆盖旧库；旧成功A只确定前置checkout与资产，不能替代新A。

**未来一次B独立预期，当前不执行。** 单进程、单session、硬120秒、0 LLM、0 Nsight：
沿已核验PyTorch2.6/cu124的小上下文、64-byte逻辑张量与单显式流建立并订阅前drain，
session内创建一个event，按record→event synchronize→stream synchronize→destroy执行。
流上无待验证的长任务，允许极短/零活动交集；本例只检验记录存在与真实关联，不测等待。
不把64-byte逻辑分配称为物理显存上限。保持原始返回码；任一步失败停止，无重试/替补。

必需来源：同session/PID/TID和CUPTI时钟的闭合操作范围、侧记实际native event/stream与
每次返回、唯一runtime activity及callback、明确driver父子关系、CUDA_EVENT记录的
driver correlation/context/stream/eventId，以及同eventId的物理event sync与同流物理
stream sync、context/stream资源、loss查询/flush/关闭/退出。native event指针不等于
CUPTI eventId；关联来自受控调用范围与明确父子/correlation，不按时间邻近猜配。
API activity和callback时刻可能不同，不强求逐ns相等，各保留原值及范围。driver API
行若存在必须严格核对；不补造缺行或计算其时长。API22的旧event记录没有设备完成时间戳，
保持NOT_AVAILABLE，不能填0冒充实测。

缺事件/范围、重复/错线程/错父子、同步失败或eventId/stream/context冲突、丢失/容量/
关闭失败均拒绝；open成功而缺event尤其不能通过。新分析入口只授`EVENT_LINK_COMPLETE_PENDING_REVIEW`，
不授模型覆盖、1024修复、W/terminal、A/COE或新Formal。B约2～5分钟、临时2GiB、
小型回传估计<1MiB（非保证）；先审真实新A，再绑定原receipt/库/hash准备控制入口及命令。
历史总占用仍null/UNKNOWN，长期<50,000,000,000bytes目标独立，无ACL遍历或自动清理。

### 真实A与独立B控制边界（2026-10-21）

6c744bf真实A已审：399成员/398清单，458源码、SDK/库、原82项CPU/10项顶层exit0。
A receipt SHA256为`9d6d4000d07ea7d752c78f4d337f88fe35085e99995ee88242eae5a824ad971e`；
不是此前本地改配演练包。新`cupti-event-b/0.1.0`只复用此A的client/CUPTI/CUDART和
未变6c744bf probe/reader，不切换服务器checkout、不构建、不重跑A。控制层版本单独绑定，
不能将文档HEAD替代执行/分析身份。

默认入口拒绝；显式B仍严格为上述一个事件链/一个GPU子进程/一个session、硬120秒。
父控制器不初始化CUDA。初始化、真实事件和物理同步唯一关联、完整关闭/flush及进程退出
均为必要证据。结果只允许`EVENT_LINK_COMPLETE_STOP_FOR_REVIEW`，不是资格判PASS。
运行前后核A全部封存文件、fresh HEAD/clean、源码和库；两份检查证据独立保存。
子进程原始错误与后验变化可同时记录，不能以后验失败覆盖原错误。超时/未知writer仍拒绝
封包，保留场景且停止，无重试/自动清理。新的B不接受旧0.1.1 A/旧policy来代替此次A。

本地新增控制边界及相关probe共45 passed/0 failed/0 skipped（6.57s），真实PS5.1和
隔离Python读取已运行，外部进程/CUDA参数与event均为CPU替身；没有执行GPU或重编。
目标B仍NOT_RUN；成功也不授PyTorch真实模型覆盖、1024效果修复、S事件依赖或A/COE资格。

固定控制`38baca449d2f53ebb92b5422cda3944da44dc531`，native/分析继续使用
`6c744bf52daff3fc54571e264a0c34e3207aa1df`。唯一B包
`cupti_event_b_38baca449d2f_delivery.zip`为49,059 bytes，SHA256
`7858aec7e2aa80765233681e15202b0276dda97e2a7eebbf7c90175c66c120e8`；
16成员/15清单全部CRC/hash、真实A引用和源码核验通过，不含替换二进制或部署bundle。
准确服务器路径/整段命令在忽略的本地交付记录中；先交协调审查，未执行B。

## 事件B已闭合；一次768完整链接回0.1.1（2026-10-21，当前）

真实event B原件23成员/22清单、PID36656 exit0、前后A核验通过；实际record138→
event-sync140→stream-sync142，context1/stream13/eventId1，有明确runtime/driver父子，
初始化/关闭及loss闭合。协调及本地裁决为限定事件记录与关联Engineering PASS。
receipt SHA256：`824183fcea1e4ca5d0f3423cfedf6fb791379bc80a4f3dd47318854a0fac0ed9`。
它不等于真实模型覆盖、S层event依赖、旧768同因、1024修复或COE/Formal资格。

复用原`cupti_timeline_model.py`/`cupti_timeline_b.py`，新增model/stage-B/result/review
显式0.1.1合同，绑定原6c744bf DLL、启用政策0.2和同次session receipt0.1.2。
旧0.1.0/7fa36ef读取仍保留，新旧/未知混用拒绝。实际checkout/runner/S/COE固定6c744bf，
新的控制/producer脚本另绑commit及字节hash；不部署checkout、不重编或替换DLL。
原`resident_capture`、scope标签、P.prepare/finish及Host-readable位置、warmup/drain
未改；新source role仍Engineering，不宣称Nsight时序等价。

仅一次768/batch1/输出2、原warmup3/repeat1，1模型进程/1 CUPTI session；不与Nsight
并采。输入/完整model inventory/实际token值同次核验，两token完整S/COE消费。
初始化和完整flush/逆序关闭、无丢失/溢出/未知依赖为必要条件；新request内event等未支持
依赖仍拒绝，不因事件小例成功而放行。API22缺event完成时间戳仍NOT_AVAILABLE。

`cupti-model-memset-coverage/0.1.0`仅汇总观察到的真实参数与原严格S/COE判定：
零payload逻辑节点、合法非零效果、未准入/参数未知分别保存；count=0本身不豁免scope/
顺序/依赖/terminal。成员覆盖request前缀直到各token，不当成Decode新增活动量。
未知效果为null，失败不填零；模型与CPU分析退出和后验错误分别保存并传播。
一次完成/任何硬失败即停，不重试、替补、降级输入或自动清理；未知writer拒绝强封包。

本地相关42 passed/0 failed/0 skipped（25.89s），包含实际隔离CPU消费者、真实PS5.1
双回执门、旧路径/新政策、原runner文件链及缺效果失败传播；独立手算20ns/1ns保持。
GPU/模型边界为CPU替身，未运行模型/CUDA/Nsight或重编；目标768仍NOT_RUN。
模型硬300秒、CPU消费硬180秒，新鲜参与卷12GiB；预计5～10分钟、保留20～150MiB为估计。
长期总量UNKNOWN独立，不复读历史ACL。先固定包交协调审查，由用户另行执行。

2026-10-22固定交付：控制/producer入口`2be05ce6cefe69de46bdfcae513ed55c3b3cd4e8`；
native/runner/S/COE继续`6c744bf52daff3fc54571e264a0c34e3207aa1df`。
唯一`cupti_model_2be05ce6cefe_delivery.zip`，64,422 bytes，SHA256
`0680c5e1548543693ccc22f480ea133afc78c92c5ddc674779f007744ba39a82`；21成员/20清单
CRC/路径/hash、原A/事件B/输入/模型inventory绑定通过；7项核心源码与6c逐blob一致，
原resident_capture和producer_scopes同解释器AST一致。新包不含二进制或部署bundle。
包内隔离默认入口及PS5.1命令/launcher解析通过；准确路径及命令仅存本地忽略的交付说明。
目标真实模型仍NOT_RUN，不因包审查/CPU成功而称新768或1024已合格。
