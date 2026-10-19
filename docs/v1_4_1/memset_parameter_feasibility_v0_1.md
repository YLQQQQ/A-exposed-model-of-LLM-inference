# Batch4 memset参数取证可行性审查 0.1

## 2026-10-19增补：B控制包协调复核通过 0.18（当前，目标B NOT_RUN）

控制662b94a、native/reader cedd706严格分列。小包59,681 bytes、SHA256
`ba5f332a887390427feadd7a2fb3d8fb96fa07063adebd78f58908e80d664e50`，8成员/7项清单的
CRC/path/全部hash及commit表示通过；A receipt/manifest原字节与真实A一致，build、EXE、
runtime/CUPTI、Python与GPU配置匹配已审数据。没有部署bundle、新二进制或SDK。

入口先复核A receipt原SHA及全artifact_manifest、源码/checkout/clean、库与二进制，
复用已审namespace绑定后进入真实新鲜2GiB空间门；仅启动一次已审micro。
CUDA_VISIBLE_DEVICES为完整已审UUID、PCI_BUS_ID排序、本地ordinal0；这不冒充native已测
UUID。原native/分析未修改，后验再次检查A；缺开关、身份/空间冲突或非零/效果审核失败
均停止，未知writer拒绝封包，既不重试也不切工具。微例硬120s，校验/封包时间另计。

协调复跑22项新增边界CPU：22通过/零失败/跳过，6.24s；明确A/Git/GPU为替身，未运行
native或加载vendor，不能与原22项相加。实际随包-I缺开关拒绝、包未变；PS5.1解析通过。
这批准的是**用户显式运行一个0/64-byte tiny**，不是GPU验证已经完成。0模型/0Nsight，
不重跑A/重编/恢复旧槽；成功仍需原件审查，不授权PyTorch/1024/零依赖/A/COE/provider。

完整机器路径及精确命令位于忽略的B交付说明/同控制版本stage_b.ps1；协调审计
`.local/diagnostics/independent_cupti_b_coordination_review_v0_1/audit.json`，CPU JUnit为
`.local/cupti_b_coordination_check.xml`。研究进度7.203同步；旧原件及用户DOCX保持。

## 2026-10-19增补：绑定真实A的独立B执行边界 0.17（当前，B未运行）

仅准备一个新0/64-byte tiny的控制入口，不恢复模型、旧七槽或多点。目标A限定PASS保留，
native/审核器继续为cedd706，不重编/重跑A。新控制commit与cedd706分开绑定，代码从小包
直接运行，目标checkout不切换；旧A-only launcher保持拒绝所有采集开关。

入口先核包/控制字节，再核给定A receipt SHA256、原manifest及全部清单、build/binary/
runtime/CUPTI/源码与clean commit。bind_checkout_modules复用已通过的真实A代码，仍-I、
来源明确、无PYTHONPATH。只运行已审micro.exe，原argv保持；执行前后复核A/源码/库未改。
新的receipt保存原A SHA、controller/native/analysis三种身份，原A receipt从不改写。

唯一可见GPU固定为已审完整UUID，原native `cudaSetDevice(0)`因此选择该可见设备；
依据[CUDA12.4.1设备可见性规定](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-c-programming-guide/index.html#env-vars)。
这不是native新增UUID查询或仅凭历史ordinal猜测。保存应用环境选择声明，CUPTI记录
native context/stream/device/对应效果；零模型/零Nsight，不与torch.profiler共用subscriber。

新鲜空间门复用2GiB参与卷检查，输出/ZIP均新路径；不重扫历史/ACL或自动清理。
tiny只有一次启动、两case，硬120秒；超时保留原process状态及UNKNOWN，拒绝强行封包。
参数/返回/效果桥/读回/drop/flush/关闭由未改native和原独立审核器检查；控制层另核实际
PID、加载库路径、run及库hash。非零、缺效果或审核失败即BLOCKED，不重试/替补/追加。
成功只记`MICRO_EVIDENCE_COMPLETE_PENDING_REVIEW`，仍待回传审查。

本地仅新增边界22 passed/0 failed/0 skipped，7.46s（`.local/cupti_b_release.xml`）；
真实PS5.1参数/-I、隔离资源依赖及失败回执/封包均运行，GPU调用是明确CPU替身。既有A74项、
native编译、微例及完整Q0未重跑。本地Python3.12.7不代替目标3.11.16或实际订阅资格。
包/hash先由实现commit固定后再集中记科研进度7.202和本地交付说明；控制662b94a，native/
reader仍cedd706，不切目标checkout。小包8成员/7清单/全部hash/CRC及真实A原件绑定通过，
实际包在`python -I`下未给B开关时明确拒绝；完整PS5.1待审命令仅启用独立B launcher，
没有裸EXE命令。审计`.local/diagnostics/independent_cupti_b_delivery_v0_1/review.json`。
本轮没有服务器、GPU/vendor库加载或模型。微例成功亦不接回完整provider，不升级旧1024、
零长度依赖或A/COE；原定义/Raw/角色/历史判断与用户DOCX保持。

## 2026-10-18增补：真实目标阶段A审查PASS 0.16（历史A结论保持；B准备见0.17）

独立CUPTI新A静态ZIP17,311,337 bytes，SHA256
`71ff920f60e1fd27ec09f7f781c1f4c716e621019e11256c8479447d004decbf`；944成员/943清单，
CRC/路径/全部hash、交付与13源码表示、118 SDK/377 CUPTI成员均通过。
执行/分析cedd706、包清单cb93f554…、真实checkout及实际资源模块来源一致，
receipt为STATIC_READY_FOR_REVIEW/error=null，14条process记录均exit0且无超时。

目标3.11.16/MSVC14.38/SDK10.0.20348构建三个真实EXE，产物hash匹配build.json；
imports仅系统库，GPU micro只构建未运行。CUPTI17项/CUDART9项导出通过PE字节检查，
不是目标库加载。CPU原stdout与JUnit均74通过、零失败/跳过，12.34s/12.304s。
stage_a_cuda_programs_executed=0、B_authorized=false，实际GPU订阅/参数/效果仍未知。
空间373,384,695,808 bytes，历史总量UNKNOWN及长期50e9目标不变，无清理。

下一项仅由实现窗口准备B执行边界，**直接复用新A已审产物，不重跑A、不重编未变native**。
绑定外部receipt原SHA、原artifact_manifest及build/源码/库/二进制实字节；新B控制入口
如有新commit，必须明确其控制身份与cedd706 native/reader身份，不能静默混同。
一个tiny进程，两case，硬120s；不通过Nsight/torch.profiler启动，不运行模型或恢复旧槽。
设备选择必须绑定已审UUID而非仅cudaSetDevice(0)，新输出不覆盖，失败/未知writer停。
保存实际调用参数、返回/资源及效果桥、独立读回、drop/flush/关闭、进程状态，随后用现有
独立审核器判定；失败即保留诊断，不补采或自动扩设施。B入口本轮尚未实现/交付，不能
通过给当前A-only launcher附开关或裸跑EXE代替已审执行边界。

真实A receipt SHA256为
`67f02b575aa4ce37cdcdc9c861e1149a1e960d5d33b730d9983a541ae7877fb0`；micro.exe为
335,872 bytes/SHA256 `b735bd1ee7484d6df3d52db5d5ccc4808ab63fd5c10fb90a5064e9aae5b4495b`。
其余完整摘要、机器路径及14条进程argv存本地
`.local/diagnostics/independent_cupti_target_a_review_v0_1/`；研究进度7.201同步。
本轮无代码或新实验，A通过不授Q0/模型覆盖/旧1024或S/A/COE资格，原件及用户DOCX保持。

## 2026-10-18增补：cedd706修复包仅A协调复核通过 0.15（当前，目标A/B未运行）

**只允许下一步显式运行阶段A，不启动GPU微例或模型。** 新包15,978,375 bytes、SHA256
`0c1bb777261affe498a8a4944938796c301eebac29d41344b4af9d7c1d51c892`；13成员/12清单、
13源码、118 SDK/377 CUPTI成员全部CRC/路径/hash及bundle通过，原包不改。

协调独立使用ZIP内实际bootstrap/support及已审干净本地Git fixture，以真实`python -I`
重走bind_checkout_modules→startup_resources，未mock资源函数，空间门为实际2GiB。
新包正确绑定已验证checkout/单一namespace/精确资源文件，exit0，严格清单无pycache污染。
错误parent、混合namespace、篡改源码及错误commit四项均明确非零拒绝。前一次0.13的隔离
导入阻塞已消除；不是依赖环境刚好有scripts包，也没有通过取消隔离或PYTHONPATH绕过。

这5个协调复核情形仅验证本地依赖/失效路径，不能与主窗口74项CPU叠加为新科学样本。
目标3.11.16/MSVC14.38/SDK10.0.20348、实际CUPTI订阅及设备仍未验证。A-only入口复核确认
只部署/核实源码、SDK与库PE、编译链接和Host CPU测试；GPU micro只构建，不执行。
没有B开关/命令，不需旧Nsight采样路线的管理员权限，不自动提权、安装或清理。

下一步由用户在Windows PowerShell5.1显式执行准确新A命令，并回传新静态ZIP。
身份、空间或构建/CPU失败即停，原样保留；不能保证目标必过，也不能预先称目标A完成。
目标前置仍9c78e355bb43/clean；执行身份cedd706，后续审查文档commit不替代它。
真实A审查后才可另审无模型0/64 tiny；1024、零长度顺序及S/A/COE/provider资格不升级，
旧原件、Gate13与用户DOCX保持。机器命令和审计索引仅保存在本地交付说明及
`.local/diagnostics/independent_cupti_repair_coordination_v0_1/`，科研进度7.200同步。

## 2026-10-18增补：隔离bootstrap模块绑定修复 0.14（当前，仅本地验证）

按0.13复现并修复启动链，不扩大独立CUPTI功能或研究支持域。保留`python -I`及原包，
不以PYTHONPATH、取消隔离或吞异常放行。原f1ba8fb包仍是被拒绝的历史交付。

顺序固定为：严格包清单→前置checkout/部署→执行commit及clean→全索引源码字节→再次核
commit及资源依赖字节→显式绑定该checkout的`namespace + file`→真实空间函数。新组件
记录`independent-cupti-checkout-import/0.1.0`，包含commit、code_root、namespace_path、
模块origin和源码bytes/SHA256；写入`checkout_imports.json`，由A回执及产物清单绑定。
这是启动链provenance，不是新增测量合同；原A-only配置和科研schema不放宽。

绑定不搜索环境中的同名包，不修改sys.path。已有scripts若来自旧checkout、第三方或
混合namespace，或已有leaf与预定源文件不同，则明确拒绝；不执行未入源码索引的init文件。
仅依赖实际已审核的标准库资源模块，不加载vendor库、torch或采集入口。

真实本地隔离子进程使用随包bootstrap/support、临时真实Git checkout和真实参与卷空间
函数，正反例覆盖错误来源/commit/源码、未加载但可发现的第三方包，以及实际stage_a
资源之后下一文件门的失败回执/封包。未再mock startup_resources。旧测试环境含合并的
第三方namespace会被新严格门拒绝；测试fixture显式声明隔离namespace，真实-I负例保留
这种拒绝，未为了普通pytest通过而降低生产门槛。

定向74 passed/0 failed/0 skipped（16.47s），JUnit`.local/cupti_import_release.xml`；
新增前7项失败的红例和原ModuleNotFoundError均保留。native/参数审核器未变，复用此前
真实头文件编译产物并验证binary hash，执行Host-only回归；本地3.12.7不替代目标3.11.16。
不重跑完整Q0/旧110项，不运行模型、GPU或Nsight。先取得实现commit再绑定新包，避免hash
自引用；执行/分析为`cedd70610588d4d5691c5a86cbcb923ef8ea6433`，包及SHA256集中科研进度
7.199。13成员/12清单、13源码、118 SDK/377 CUPTI成员及全部hash/CRC/bundle核验通过；
从最终ZIP取bootstrap/support字节，经真实-I/干净临时Git checkout/真实空间函数exit0，
封包文件未变，详`.local/diagnostics/independent_cupti_import_fix_v0_1/review.json`。临时
checkout只作本地依赖演练，不冒充目标执行commit或3.11资格。新包仍需协调审查，A真实
原件审查前没有B命令。原始证据、冻结/旧Formal及1024拒绝不改。

## 2026-10-18增补：f1ba8fb交付启动链协调审查 0.13（历史，原包暂不执行A）

**协调审查发现可复现的隔离导入缺口，原包暂不执行；不是GPU微例或1024又失败。**
ZIP为15,968,398 bytes、SHA256
`a8952447b034715efa3657cf339676e2cfcebf781d026c260d569057e064934b`；13成员/12项清单、
13源码路径、118 SDK/377 CUPTI成员的路径/CRC/hash与执行commit绑定均通过，bundle及
PowerShell解析通过。下面阻塞不靠修改原包复现。

`run_independent_cupti_a.ps1`明确以`python -I`启动随包
`independent_cupti_stage.py`；该bootstrap读取并核验checkout源码后，调用
`startup_resources`→`micro_support.resources`，后者直接导入
`scripts.coe_startup_storage`。但bootstrap没有把已核验checkout绑定到模块解析。
本地用随包原文件、真实`-I`子进程调用相同函数：exit1、
`ModuleNotFoundError: No module named 'scripts.coe_startup_storage'`。
本地偶然可见的scripts namespace实际来自第三方目录，不是本仓库。目标3.11未运行，
不能假定目标site-packages有正确模块，也不能用普通非隔离测试证明这条启动链可用。

定位对照仅在外部诊断脚本接入本地已审checkout，原bootstrap/support不改，真实资源函数
即exit0，模块来源是本仓库。这个对照只定位根因；没有在生产修复，没有GPU/vendor库加载。
原A模拟测试替换了`startup_resources`；support清单测试只调用support导入，没有走其
资源依赖。这解释了为什么既有65项CPU通过仍漏掉该问题；本轮不重复同一测试堆叠。

给实现窗口的最小修复要求：保留`-I`和全部身份门，在使用仓库资源模块之前绑定**已核验**
checkout与实际模块来源；第三方同名包/旧checkout不得冒充。新增实际随包bootstrap到
真实resources导入路径的正反例，分别覆盖无PYTHONPATH、错误/同名模块及失败回执；
不要仅关掉隔离、依赖当前工作目录或再次mock掉此资源函数。修复后建立新执行身份和包，
重新审查，不改旧ZIP/hash、目标前置仍需核验9c78e355bb43/clean。

审计索引在本地`.local/diagnostics/independent_cupti_coordination_review_v0_1/`：
`package_audit.json`及原始隔离stdout/stderr。科研进度7.198同步；本轮仅审查与文档，
没有业务代码/新包、服务器动作或新CPU/GPU资格；旧定义、Raw及用户DOCX保持。

## 2026-10-18增补：独立CUPTI微例本地实现 0.12（历史交付；当前审查见0.13）

**本地实现完成；仅可交付A构建/CPU审查，不是1024修复、CUPTI目标资格或COE放行。**
按用户批准的0.11实现，不恢复Nsight来源包、共享入口hook、旧七槽或多点矩阵。
固定CUDA12.4.127/API22，目标可信checkout为9c78e355bb43，非旧4da800d。

实现集中于`native_cupti_memset/{core.h,micro.cpp}`、独立审核器
`analysis/independent_cupti_memset.py`和A-only launcher/controller：

- 独立进程动态加载显式路径/预定SHA256的官方CUPTI和共享CUDART，加载后再核实际路径、
  API22/runtime12040，结束复核文件未变；不借Nsight私有DLL。原生入口拒绝已知注入环境/
  已加载CUPTI及模型profiler客户端，订阅失败保留实际返回码，不共用subscriber。
- ENTRY即复制size_t/count、value、指针及native stream，EXIT只复制实际cudaError_t/
  CUresult，不再次读取参数。普通51与PTSZ235使用各自真实结构，身份明确分开；微例
  profile首版仅接受普通入口，PTSZ有记录也不能静默授予同等资格。无转发hook、无包装内
  CUDA查询/同步/磁盘I/O，记录原PID/TID/native context/contextUid和correlation。
  API身份按固定domain/CBID确定；保留observed_name，另在回调外通过cuptiGetCallbackName
  核对SDK元数据名，允许明确入口名或该精确名称，不猜版本前缀、也不丢原始名称。
- driver回调只消费两条目标runtime动态栈内的调用，以ENTRY/EXIT栈恢复父子关系，不按
  时间邻近。runtime/driver API activity的ID各自匹配；MEMSET4依据匹配SDK的**driver**
  correlation连接，再核context/stream/device/bytes/value。相同数字不能替代domain。
  微例使用一条显式nonblocking流，CUPTI查询在目标回调外绑定native handle与stream ID。
- 固定8×64KiB Host缓冲、64个callback、4096个API、128个MEMSET槽，耗尽、溢出、丢失、
  解析/查询失败及未返回缓冲均拒绝；这是客户端容量，不声称限制CUPTI内部总内存。
  保存注册、enable、两次forced flush、disable、unsubscribe/finalize状态及丢失查询。
  Context/stream保留至flush/drop查询完成，未知不填零。重入/额外线程超出微例域即拒绝。
- 固定独立参考：同一64-byte buffer初始化58；请求count0/value123后读回64字节均为58，
  count64/value123后均为123。两条逻辑调用与API记录均保留；非零必须有唯一合法设备效果。
  零字节参数/正确读回不证明无依赖、顺序豁免、旧调用count0或A/COE准入。
- Native JSON与独立reader分别版本化0.1.0，区分HOST_CALLBACK_DOUBLE/TARGET_GPU。
  真实目标源还需外部已审run/库hash绑定；不允许只改role/source升级Host替身。

**实际本地验证：** Python3.12.7、现有MSVC14.44/SDK10.0.26100；使用匹配12.4.127/API22
真实头文件编译并链接完整微例及两个Host harness，三个EXE均无静态CUDA/CUPTI导入。
只运行Host harness，没有加载CUDA/CUPTI、初始化GPU或运行微例。
手算正反例、真实native JSON→reader、缓冲耗尽/丢失/解析错误、参数突变后快照、PTSZ分派、
同数不同domain、缺效果/错scope/错父子/错返回、A-only真实PS5.1分派及失败回执/封包均覆盖。
定向最终65 passed/0 failed/0 skipped（9.25s），JUnit`.local/cupti_release_verified.xml`；
本地14.44/3.12结果**不冒充**目标14.38/3.11.16构建或GPU覆盖。
修正了真实编译发现的SDK重复include及明确ABI对齐警告，未修改vendor头或使用stub；
PS5.1子进程按仓库已有测试方式固定其自身Modules目录，不继承PS7模块路径。
最后真实bootstrap演练复现并修正随包support导入产生pycache导致清单拒绝；没有忽略多余
文件。另以成功查询状态区分合法的零context/stream ID，不能将数值0自动解释为缺失或默认流。
首次本地包装误列不存在的tests/__init__.py已移除（新测试无跨tests helper导入）；
未发布草稿不用于目标执行，最终包只绑定修正后commit。

交付A仅验证前置/固定bundle/源码实字节、SDK/库PE文件身份及所需导出，真实构建/链接、
上述CPU和新鲜参与卷空间；无B开关，不初始化CUDA，不安装依赖/升级工具链，不遍历历史
YLQ/ACL或清理。估2～5分钟、临时预留2GiB；长期<50,000,000,000字节仍UNKNOWN。
目标必须重新取得A原件后才另给B命令；目标微例最多1进程/120s、0 Nsight profile，尚NOT_RUN。
交付由实际实现commit绑定，包/hash另记进度和本地handoff，避免hash自引用。

**同次证据链的真实缺口：** 本版只启用runtime/driver/MEMSET，既无模型scope/producer、
完整kernel/Memcpy/NVTX，也未获得Canonical provider/ownership/drain/必要集合/terminal资格。
所以**不能直接接回生产S/A/COE**，更不能拼接新CUPTI参数与旧Nsight。微例通过仅允许再评估
一次真实PyTorch覆盖诊断的价值；若最终需要完整新provider或更多观测设施，先另审代价与
科研收益，不自动实施。微例未闭合则停在模型前；旧1024及原因UNKNOWN/BLOCKED不变。

<a id="2026-10-18增补下一项工作的顺序与止损条件-011方案未实施"></a>

## 2026-10-18增补：下一项工作的顺序与止损条件 0.11（原方案，本地实现见0.12）

**下一项是取得可靠的调用参数证据路径，不是重跑1024，也不是扩负载矩阵。** 本轮只读
复核匹配SDK、已有原型及已封存能力证据，没有新实现、测试、打包或服务器命令。
旧来源包暂停，不要求管理员原样重跑；没有把其它Windows版本的拒绝当成目标解析实测。

推荐将独立CUPTI窄域微例作为下一项实现候选，先跳过“必须先拿到调用栈”的非必要步骤。
真实问题是调用count及设备效果，不是一定要知道某个库名称。依据固定CUDA12.4.127/API22：
`CUpti_CallbackData.functionParams`可在ENTRY复制实际参数，EXIT读取返回码，callback
correlationId与相应domain的API activity对应；runtime普通/ptsz的memset回调ID分别为
51/235，参数结构分别声明，不把PTSZ静默当成普通入口。匹配SDK五项关键文件hash重新一致。
这些是接口依据，**不是目标回调覆盖通过，也不是新collector已可用**。

### 顺序门：每一步明确回答一个问题

1. **本地最小native实现与CPU审查，尚待开始。** 复用已有真实结构体复制原型与SDK，
   增加独立初始化/关闭、runtime及必要driver callback、有限activity缓冲/flush、丢失计数
   和版本身份回执。仅支撑0/64-byte微例，保留逻辑调用/原返回码；禁止读取已过期参数。
   先检查缺参数、错correlation/domain、重入/多线程、溢出/丢失及subscriber冲突的停止行为。
   编译/链接及Host替身通过后才允许审查目标A，不能称GPU通过。不同时开发通用collector。
2. **目标无模型微例，未来另审。** 默认A只编译及CPU/PE/身份检查；新A审查后才显式B。
   B最多一个tiny进程、120秒，独立运行、不通过Nsight/torch.profiler启动；固定buffer和流，
   两case请求count0及count64，读回独立预期分别保持原值/全部为指定新值。要求实际参数、
   返回码、唯一调用绑定与64-byte合法设备效果同时闭合；DLL/版本/订阅/覆盖/丢失任一
   冲突即停，不试另一库、不追运行模型。未来总体估15分钟/2GiB，不是实测承诺。
3. **真实1024覆盖诊断，尚未授权或准备。** 只有微例全部通过，再审最多一个新模型进程，
   1024/batch1/o2/P/w3/r1，完成政策与模型内容不变。逐调用记录实际count及效果，接受
   覆盖失败或非零缺效果；不能承诺微例通过等于PyTorch内部覆盖，也不假定重现旧84次。
4. **回到研究链的独立决策门。** 即便新参数完整，也先说明同一次新执行如何满足原
   drain、流/ownership、提交顺序、必要集合/terminal及completion证据；参数齐全不是
   A/COE准入。不能拼接独立CUPTI参数与旧Nsight时间线，不能把新provider自动送入原
   Canonical/S/A。若必须开发完整新provider才能继续，先另审工程量、验证与科研收益；
   不从窄域诊断静默扩大，不凭“拿到了count”恢复多点采集或旧七槽。

### 此路线与旧失败的区别

普通导出Detours记录器没有覆盖真实PyTorch，本候选利用CUDA提供的回调接口读取调用
参数，不靠猜哪个DLL导出地址被执行；**实际覆盖仍须验证**。现有SDK单subscriber限制
意味着不与Nsight同时运行，不升级工具栈、不用Nsight私有CUPTI；官方样例的
`InitializeInjection`/activity接口只提供接线参照，不复制其无界行为或自动启用全部活动。
微例失败即在模型之前停止，后续是否需要独立实现另审；当前不制作修复/采集包。

预先固定裁决：count0/成功仅证明请求零字节，不证明无依赖、无顺序影响或旧调用为零；
count>0且合法效果可继续检查依赖，count>0缺效果继续BLOCKED。当前最高优先级是审查并
完成上述第1项最小实现，目标微例/模型/A/COE资格均NOT_RUN，不改变测量语义和数据角色。
旧512/2048四block结果保留，但不用于认证1024；多点矩阵在准入闭合后再另行固定。

## 2026-10-18增补：真实A权限与CLI能力双重阻塞 0.10（历史回执，当前方案见0.11）

**本次A为BLOCKED，不能仅换管理员窗口重跑。** 封存静态ZIP为77,013 bytes、SHA256
`d4ceeae555ec0f5b146821aba40133e2d7df6e6cc61aaeff1cbed3dcd5d96b4b`；25成员、24项清单、
CRC/路径/全部哈希通过。359项科研源码实字节表示匹配，交付配置/实际入口与原包相同。
原receipt及ZIP只读保留，不补写成功终态。

实际`capability.json`同时记录administrator=false及required_options中
`--cudabacktrace`=false；Windows及其它四项选项为true。目标确为2026.2.1.210，完整
profile默认帮助没有该选项。bundle、fetch、checkout、version/help均exit0，已经过3.11.16
前置门与源码/空间检查，空闲373,423,542,272 bytes。本次CPU/compile尚未开始，
模型/CUDA初始化/profile均未运行；不能把交付前CPU结果写成目标本次CPU通过。

这里有两个必须分开的限制：

1. 目标令牌不是管理员，Windows process-tree采样前提不满足。
2. 综合[官方UserGuide的选项说明](https://docs.nvidia.com/nsight-systems/UserGuide/index.html#cli-profile-command-switch-options)
   不能证明该目标Windows CLI具有相同选项。先前仅以综合文档及CPU替身形成接口级GO的
   审查不充分；本次真实能力门正确停止，不能删门或将普通采样栈按时间附近匹配为API栈。

补充本地反例：已装的Windows 2026.1.1及2025.6.1分别执行普通帮助、backtrace分类帮助及
`profile --cudabacktrace=all:0 --help`，无application参数。前两项exit0但不列该选项，
后一项均exit1并报unrecognised option；未运行profile或GPU。**这是本地其它版本，
不是目标2026.2.1解析实测；目标默认帮助缺项也不足以证明所有Windows接口不可行。**

裁决与后续：暂停现有来源采集方案，先核实固定Windows可用的逐调用来源入口，再审最小
诊断路径。当前不制作新包、不要求管理员原样重跑、不改ACL/安装栈，不提供B命令或扩大
hook/CUPTI。B的原预算/风险条件不是执行授权，旧七槽不恢复。此处没有证明1024不可修复，
也没有补齐count、设备效果或S/A/COE资格；旧原因仍UNKNOWN，原定义/数据角色保持。

审查脚本及机器索引位于本地
`.local/diagnostics/memset_callsite_stage_a_review_v0_1/`：
`audit_receipt.py`逐项核验sealed原件、源码表示及状态，`adjudication.json`保存结果，
`local_cli_help.json`及六组原始stdout/stderr保留其它版本反例。本轮无生产代码修改、
模型/CUDA实验或新回归测试，科研进度7.195与本地handoff同步。

## 2026-10-18增补：1024原生调用栈有限实现与交付准备 0.9（历史；真实A见0.10）

用户批准继续完成通用分析适用性目标。本轮实现0.8已选的来源诊断；**还没有取得目标机
调用栈、count或设备效果，不能称1024已经修复。** 256和四点研究准备保留，旧失败不重写。

- [有限身份](../../exposedpath/memset_callsite.py)为独立Engineering，只允许1024/1/2、
  P/w3/r1、一次profile。通过原Engineering adapter复用真实Qwen执行链，P helper函数体及
  CUDA/Host-readable完成政策不变；旧Pilot、原S/A/B/COE计算没有放宽。旧collector及COE
  preparation消费者显式拒绝新source-only角色。
- [collector](../../scripts/memset_callsite_collect.py)保留原目标/producer/trace/nonce绑定；
  开启原生all:0栈与process-tree 200Hz采样，不使用VectorModel、Python栈或第二subscriber。
  CLI duration240秒、profile进程硬上限300秒、外层900秒，避免两个相同deadline抢在封尾前
  强杀；不扩大原预算。只导出与运行来源查询，绝不为本诊断运行完整S/A/COE。
- [来源消费](../../analysis/memset_callsite.py)只读原SQLite，按真实callchainId连接目标
  帧，不按时间配栈。全部Prefill调用保留，并区分有/无关联效果；未观察效果不推断count0。
  合法共享栈、未解析符号、VM命名空间、空/悬空栈、重复depth与仅工具帧均有CPU检查。
  采后文件hash不是装载证明，原IP不是callee入口；源定位不等于参数、效果或必要依赖闭合。
- [A/B入口](../../scripts/memset_callsite_stage.py)默认A，仅部署/CPU/compile/空间与NSys
  help/version、实际管理员token；不自行提权。B须新A精确receipt SHA及显式采样风险接受。
  原BugCheck 0x133仍UNKNOWN；200Hz不限制API取栈成本，不承诺系统安全。只一次，失败停止，
  不自动进入CUPTI或重开hook；没有确证目标退出时拒绝封包，保留现场。
- [打包器](../../scripts/package_memset_callsite.py)从真实Git commit和已审4da800d静态原件
  绑定前置，固定1024输入/模型清单及源码实字节（明确Git blob/合法CRLF表示，不归一化文件）。
  不安装依赖或构建native库。实际包身份/路径由忽略的本地交付说明提供；不将CPU替身视为
  目标机权限、profile或参数资格。目标3.11及实际Nsight栈均待新A/B回执。

相关回归242项通过；最后入口30项通过，覆盖重叠不相加，均无失败/跳过。仅通用Python/CRT
框架不构成有用来源，负例保留。完整producer和
prepare/seal/consume使用真实文件与共同trace投影，模型/设备/NSys边界是CPU替身；
Python3.11语法、compileall、PS5.1解析及diff检查通过。本地Python3.12.7，没有GPU实验。
原始1024/旧BLOCKED仍不可评估；成功时只报CALLSITE_LOCATED，若缺口未复现或栈不足则
不可判别/失败。研究进度7.194及handoff同步，旧Formal/Gate与用户DOCX保持。

最终交付固定执行/分析`9c78e355bb43a8696f7eccb44c48d8448f366d09`，前置4da800d；
唯一发布包`memset_callsite_9c78e355bb43_delivery.zip`146,418 bytes，SHA256
`6a79cd0c12870e296c8d78a71be6299259f5d0e98c2422aa2e9d117c0b77a4f0`。
10成员/9清单及359源码表示、bundle与PS5.1检查通过；准确路径和仅A命令位于本地交付说明。
目标机仍未部署/采集，内部3d1bafd草稿不执行；B仍须新A和明确风险接受。

## 2026-10-18增补：1024来源定位优先，先用Nsight原生CUDA调用栈 0.8（当前）

**裁决：1024能执行，当前不能完成的是分析准入；尚未证明它不可修复。优先准备一次真实
1024 PyTorch的原生调用栈诊断，不再盲改共享入口hook。独立CUPTI参数/效果路线保留为
尚未完成目标验证的候选，不与本次Nsight诊断并行、不自动接续。** 用户本轮仅授权本地
调查/必要CPU原型与方案，未授权服务器、GPU或恢复旧七槽；256已完成准备原样保留，
三点采集包暂缓。研究设计v7.1、协议v2.1、已签路线A、原A/B/COE均不变。

### 三个不同的问题，不能合成一个根因

|问题|已证明的事实|仍未证明|
|---|---|---|
|1024为什么被拒绝|模型/profile/export成功；Prefill的113次目标API中29次已有映射、84次缺效果，Raw/Canonical一致，submit mapping门拒绝；见进度7.191/7.192|缺效果调用是否count0、未记录正效果、库内特殊路径或其它原因|
|设备效果为什么缺失|现存关联/替代桥已审，不能由时间邻近kernel补齐；本轮直接复用，不重搜旧correlation|真实count、native stream、实际callee/调用来源，以及缺失原因|
|旧记录器为什么零捕获|真实B2中113次Prefill目标API存在，已绑定普通共享导出hook却无调用侧记录/调用NVTX；微例可命中|实际调用是否经过该地址、是否有其它入口/副本或注入交互；不是已经认定private/PTSZ/cuBLAS|

把1024设为512的两倍，是合法的**工作量变量改变**，不是底层执行轨迹按比例复制。
[PyTorch v2.6固定源码](https://raw.githubusercontent.com/pytorch/pytorch/v2.6.0/torch/nn/functional.py)
的SDPA说明明确允许根据输入选择实现；本地[已有Raw分支事实](coe_research_short_note_v0_1.md)
也显示512/2048实际Softmax/GEMM名称、次数和grid改变。矩阵维度、临时空间和launch实现
可能改变，但**这些事实没有证明1024缺效果的具体原因**。目前是观测/准入缺口，不是模型
不支持1024，也不是输入响应研究已被否定。

### 固定版本能力核对：可定位，不等于已测参数

以目标安装原件为主，未用滚动新版本能力替换固定Windows栈：

- 已封存UserGuide SHA256
  `5b100930126f3a3a819f13dd8335efc0bc2cd7f8bf0207a7063d57acb4c33e7c`，L805–818及
  L1292–1307：`--cudabacktrace=memory:0`可请求memory类别全部时长的API栈，必须启用CPU
  sampling；默认阈值1000ns会漏掉所关心的短调用，不能沿用默认后宣称全覆盖。参数实际
  接受情况仍须目标build帮助/诊断验证，不支持时停，不改阈值追绿。
- 同份文档L441要求Windows CLI管理员权限；未来A只记录实际权限/能力，不自动提权。
  `--python-backtrace=cuda`仅支持x86 Linux/SBSA，不放进本Windows方案；原生CUDA API栈
  与Python栈不是同一功能。不额外启用torch.profiler或自动PyTorch标记。
- 已封存AnalysisGuide SHA256
  `bdcf574189e7eb687d4dc7c52bcebacae9c700c5a93a9e3aed8ff674960cbb11`，L4006–4015、
  L4126–4135及L6247起示例给出直接关系：runtime.callchainId→CUDA_CALLCHAINS.id，
  每帧含stackDepth、symbol、module、unresolved和originalIP；StringIds解析模块/符号。
  [官方分析指南同类查询](https://docs.nvidia.com/nsight-systems/AnalysisGuide/#select-cuda-calls-with-backtraces)
  可作交叉核对。读原SQLite即可，不要求生产Canonical先支持新增栈表，不改Raw表做ALTER。
- 以每条runtime原始身份/PID/TID/phase及callchainId建立连接，不靠邻近时间配栈，不对ID
  作历史off-by-one修补。同一个栈ID可以合法复用于多条调用，不能误判成重复调用。
  未解析符号但有可信module+originalIP时保留地址级定位；缺模块绑定、悬空ID、重复depth、
  缺失/截断的有用调用者帧均保持不确定。连续depth不证明整个真实调用栈完整。
  原始IP不是已证明的callee函数入口，缺装载基址时不伪造RVA，栈也不提供count/设备效果。

本轮直接访问2026.2在线归档和12.4 API页面失败，目标版本判断来自上述已核验安装文档/
SDK原件，不把网页不可访问说成工具不支持。在线PyTorch v2.6 raw源码及官方分析指南读取
成功；文档允许某能力不等于目标实测已通过。

### 两条路线的重新比较与唯一优先项

1. **优先：Nsight自己的native CUDA API backtrace，分析仅限目标memset。** 不增加subscriber或新hook，
   最小变更仅为独立Engineering诊断角色/argv/来源消费接线；保留原模型/固定1024输入、
   P/w3/batch1/输出2、自然Host-readable完成政策。原`--sample=none`改为
   `--sample=process-tree`、`--sampling-frequency=200`，去掉原`--cpuctxsw=none`（实际调度
   采集将随sample为process-tree），增加
   `--cudabacktrace=all:0`，其余CUDA/NVTX采集政策不改。虽有memory类别，但尚无目标build的
   API分组实测回执；固定all:0是避免分组漏取，不逐类试采。使用平台默认原生栈方式，
   不套用Linux的fp/dwarf参数。函数名可未知，不下载PDB/升级工具；采样/栈采集可显著扰动
   执行，所以只作来源诊断，绝不进入性能或负载重复。200Hz仅限制周期CPU采样，不限制
   API取栈成本。可复用`gate8_source_probe.py`已存在的显式argv/版本/失败保留结构，但其
   VectorModel只属历史fixture，不执行它代替真实1024覆盖。本轮尚未实现新可采集入口。
2. **保留候选：独立CUPTI callback+activity。** 既有SDK为12.4.127/API22；header的
   runtime CBID51为普通cudaMemsetAsync、235为PTSZ，参数结构含size_t count/native
   stream，callback还可给出ENTRY/EXIT/返回及correlation。现有CPU原型只是结构体复制和
   关联逻辑，没有实际native subscriber、activity缓冲/flush及真实PyTorch覆盖。
   该层不依赖普通DLL导出Detours地址，故旧hook失败**不能否定**它；但也不能保证一定捕获
   实际目标。`cupti_callbacks.h` L679–711的旧接口只允许一个subscriber，遇到Nsight或
   其它工具冲突必须停；不借用Nsight私有CUPTI、不升级到较新多subscriber栈。独立运行
   获得的是**另一运行的新实例**，不是同份Nsight实参，不能补旧1024；若未来选它，必须
   用真实PyTorch API activity清单逐项对照callback覆盖，再审合法效果/依赖，微例不足。
   [官方接口限制](https://docs.nvidia.com/cupti/12.9/api/group__CUPTI__CALLBACK__API.html)
   仅作旧接口交叉核对，实际ABI仍取已核验API22头文件。开发缺口比原生栈采集大，本轮不选。

Nsight内存使用曲线不能给调用实参；额外cuBLAS/cuDNN trace范围也不能自动确定每次memset
入口或count，且当前没有证据先指向某vendor。因此不批量试多个library trace/hook。

### 下一次诊断的唯一问题、预算与停止规则（待审，尚无服务器执行授权）

**唯一问题：一次新的真实1024 Prefill中，正常映射和缺效果的cudaMemsetAsync，能否按
实例取得可核验的native模块/地址调用链，从而定位参数取证应针对的真实来源？** 允许两类
调用栈相同，定位成功不以发现不同vendor/零字节为条件，也不以再次出现恰好84次为条件。

- 新诊断仅1个模型进程、1条profile，无P0/配对/重试/微例/旧槽恢复；batch1、1024/2、
  固定P、warmup3/repeat1及原模型/FP16/eager/SDPA/Windows/4090保持。预估5～10分钟，
  profile硬超时300秒、外层含导出/来源审查最多900秒；临时预留12GiB，保留约0.5～2GiB
  仅为估计，不生成巨型domain。长期50e9/历史UNKNOWN保持，不清理、不扫描历史ACL。
- 实施前先准备独立Engineering角色/新输出目录及薄argv分派，不能把新诊断冒充旧Pilot
  或恢复旧报告。A只校验源码/输入/目标build选项帮助、实际权限、新鲜空间和相关CPU接线；
  不支持/权限不足/版本冲突即停，不启动模型、不自动提权或换工具。只有A真实回执审查后
  才可显式B，本轮不生成包或命令。
- [历史来源方案风险](gate8_eager_source_alignment_v0_1.md#111-历史候选有额外风险的profile747暂停非当前待裁决项)
  仍保留：既往BugCheck 0x133的根因未证实，不能归因本次选项，也不能因minimal profile
  后续成功而证明新增采样/栈采集无风险。低频、短时、超时或Ctrl+C不保证系统安全。
  未来真实B须显式审查并接受该组合风险，不由A的CPU通过自动授权，不恢复旧微例attempt。
- B保存模型/collector/export各自状态、同次producer token/phase/drain、REP/SQLite、
  完整目标API清单及每条callchain/帧、已观测module/IP/可读模块文件身份；导出不作时间
  截断。按同次Prefill身份列**全部**目标调用和覆盖，不按旧record ID/时长挑选。已有S门
  若因缺效果拒绝，仅保留其原拒绝；独立来源报告不伪造S/A/COE成功，也不要求先跑完整分析。
- 有目标调用且有缺效果组，逐条栈能定位有用调用者模块/地址：只判`CALLSITE_LOCATED`，
  允许符号UNKNOWN；随后依据实物再选参数路径，不自动hook。栈只有公共工具帧、缺失/
  无法绑定module、采集/输入身份冲突等：失败或INCONCLUSIVE，原原因保留。
- 新run若不再出现缺效果组：`NOT_DISCRIMINATING_FOR_MISSING_EFFECT_ORIGIN`，不追认旧
  实例、不追加重跑；任一必需覆盖/诊断失败或固定单次结束即停。调用栈结果不能回答count
  或证明无提交，即使定位成功，旧1024及四点研究资格也不自动改变。

### 本地已完成及真正尚缺

本轮复用原Raw/Canonical/关联搜索和旧零捕获结论，未重复旧SQLite查询。核验固定安装
文档/SDK接口及原native CPU原型，另以一次纯CPU内存SQLite检验官方ID连接：同时段不同栈
不串配、null/悬空不填零、不完整符号保留module/IP、共享栈ID合法、重复depth拒绝。
临时原型及回执在忽略的`.local/diagnostics/coe_1024_callsite_feasibility_v0_1/`，不是新collector。
它没有读取真实参数、加载CUDA或证明Windows展开能力；未重跑完整Q0或已有74项验证。

**当前停点：本地接口级方案成立，可准备这一条来源诊断；目标真实栈覆盖NOT_RUN，设备
效果缺失与旧hook零捕获的内部原因仍UNKNOWN。** 不说“1024修不好”，也不承诺下一次定位
一定成功。256准备保留、三点包暂停；原Raw/BLOCKED、A/B/COE、旧Formal/Gate保持。

<a id="2026-10-17增补新b2零捕获当前普通共享入口路线收口-07当前"></a>

## 2026-10-17增补：新B2零捕获，当前普通共享入口路线收口 0.7（历史收口）

> 本方案零捕获和停止结论不改；后续用户授权的新调查/原生栈优先项见0.8，不等于恢复原hook。

**裁决：本次参数覆盖FAIL；新B2及原Pilot仍BLOCKED。按预定条件停止当前普通共享入口方案，
不重采、不扩hook、不恢复旧七槽。** 这不是COE定义、已合格案例或整个研究方向被证明无效，
但当前没有支持继续扩建参数采集工程的实例依据，不制作后续部署包。

### 原件及范围/加载/记录链

原件`memset_prefill_63ca05178b80_b2_once.zip`，3,962,993bytes，SHA256
`80b6b72b4234112c9c5d75a0c2f52590d285f1c88f96a03395ca54d21424596e`。
本轮CRC、安全唯一82成员/81项清单、全部长度/hash及覆盖通过；manifest SHA256
`69750f2d845c7741610ad0e7f178aad5ebe4896be3648dc68658d9a532026e4e`。
新展开在忽略的`.local/diagnostics/memset_prefill_b2_closeout_v0_1/source`，原ZIP/报告不改。
只读审查脚本、review.json、逐Prefill runtime清单及NVTX摘录在同一诊断目录关联；不运行完整分析。

- 执行/原分析`63ca05178b802fc986278467364f21524591ad41`，28项源码实字节与Git一致，
  封存runner副本与执行blob一致。新run `980654293f9b47ea9ac79de52b04fc76`，模型PID4788/
  请求TID49924，入口/side/producer的创建FILETIME均134366848005075190，模型入口exit0。
- 已审A receipt SHA `ad94f07a1ab6e0e07a528807d7dfc7d49cb51a0ac360cf6f542aadf9ca14ba90`
  与本B回执绑定；本轮核对A包CRC/hash/build引用，不重跑其CPU/编译。实际记录器DLL SHA
  `2084570aa1c1ed0ea2fed63e25e349939fc2ee205fd96b249ab9536f332b316d`与A产物/manifest/
  side一致；指定普通CUDART SHA为`f95273031fc5ea44cdb37e0a696a1b15b9d84a4ee977299a6f6e652ef4d790cf`，
  与本次文件回执/加载路径检查相符。这证明所检查模块身份，不证明全部实际CUDA调用来自该导出。
- 原源码顺序是三次warmup→窗前安装→原成功drain→begin→原Prefill→首Host token→end，
  Decode后finally detach/落盘。三次warmup和measured COMPLETE，实际`[2,512]`及mask摘要
  已绑定，输出`[[29184,29184],[6556,6556]]`符合功能参考；不升级旧B2。
- attach/begin/end/detach/recorder_error均0，completion_observed=true；side完成时间
  2066840628952000与原Host首token锚点一致。没有独立的begin指令级时间戳，因此不能把源码/
  成功回执说成逐指令证明hook在每次目标调用时均有效。
- Raw中DomainCreate row1在28013835075ns；成功drain runtime37486为
  `28252671522..28252723990`；Prefill `28253195594..28398917859`，Decode
  `28398917859..28490458213`（均trace ns，不与Host时钟相减）。DomainCreate早于drain；
  参数domain没有任何调用级闭合range，side `calls=[]`。这不是再次误拒绝NVTX的-1/-1。

| 本次Raw窗口 | 成功同目标PID/TID的cudaMemsetAsync | 缺关联MEMSET效果 | 侧参数调用/调用NVTX |
|---|---:|---:|---:|
| Prefill | 113 | 84 | 0 / 0 |
| Decode（不在记录范围） | 85 | 84 | 不据此要求覆盖 |

Prefill不是“没有目标调用”，而是**目标调用存在但本方案零捕获**；全部113次参数（不只84次）
的count、实际native stream等均未取得。29次有MEMSET效果也不能补齐另84次的参数或顺序。
加载/生命周期成功、domain存在均不能替代双向实例覆盖。具体内部原因仍UNKNOWN：不能认定
cuBLAS/private/static runtime、PTSZ、后续patch机制或count0；本轮不继续追索这些可能性。
零字节消费规则及后续局部成员/依赖/terminal证明尚未执行，不能说其已被真实B2验证。

### 与采集成功分开的退出码缺陷（仅本地修复）

profile exit0/38.047s、export PASS、模型成功。参数分析进程exit1/8.437s，原stderr明确
`MEMSET_PREFILL_NO_TARGET_CALLS_NOT_DISCRIMINATING`。其上层保留
`PARAMETER_OFFLINE_DRIVER_FAILED_SEE_ORIGINAL_LOG`，但collection status仍为
`DIAGNOSTIC_COLLECTED_NOT_QUALIFIED`，被历史诊断成功状态列表当成exit0；外层随后通过结果
合同拒绝为`MEMSET_PREFILL_COLLECTION_RESULT`。两者都不是模型失败，后者也不是叶根因。

[collection消费者](../../scripts/gate8_diagnostic_collect.py)仅对新
`--memset-prefill-parameters`路径将已捕获的分析/结果文件异常状态改为BLOCKED，返回非零；
保留采集/导出成功事实、原error和分析stderr。未修改旧诊断-only退出合同、身份或准入门。
CPU先复现分析拒绝/缺结果两种exit0错误，再修复；同时保留成功分支、历史诊断退出语义和
零捕获不能冒充零payload的反例。实际验证命令/数量见科研进度7.180。原回传报告不重写，
此次补丁无需部署，不为验证它再运行模型。

### 后续研究决策：保留什么，缺什么，停止什么

| 既有证据 | 仍可使用的角色/判断 | 不能补出的结论 |
|---|---|---|
| [四token受控原件](completion_operation_controlled_validation_v0_1.md) | 操作配对、预定必要成员/terminal及区间算术的独立依据；Engineering | 自然PyTorch内部调用覆盖、参数取证成功 |
| [G32/G512 12run/24链](completion_operation_candidate_review_v0_1.md)及[复用记录](completion_operation_reuse_validation_v0_1.json) | 原合格输入上事后探索性COE；原Formal只按原签署口径保留 | 新Formal COE、纯Host阻塞/可消除时延、普遍batch响应 |
| [旧同批B1/B4局部Prefill](completion_operation_batch_prefill_review_v0_1.md) | 各自已闭合的局部Engineering COE个案；旧B4未解决调用在该首token之后的原证明保留 | B4 Request/Decode准入，或当前B2/B4运行也没有Prefill缺口 |
| d6957de Pilot B1 | 其合格Prefill单个Pilot槽，原始样本保留 | 完整block、B4−B1重复差或batch1/2/4规律 |
| 旧B2与本次参数诊断 | 执行事实/缺映射/零捕获的Engineering证据 | 可信B2 COE、零payload、合法零暴露、完整A/B或任何缺口已解决 |

**推荐：停止这条参数覆盖支线及九槽Pilot补齐的工程投入，按既有合格支持域保全/解释COE。**
当前缺的是同次实例参数覆盖及其后的合法依赖证明，不是多几个同配置样本；增加重复不能填补。
现有源码/导入资料没有指出可保证命中的另一个有界入口，微例PASS也已证明不能推广。因此没有
据此推荐新hook、工具链或collector预算。未来若另有实际入口证据和明确成本，须另行裁决，
不是本轮待办。当前可继续的本地研究工作只限已有案例的分析用途与公平timeline对照，不把
“当前手段不覆盖”包装为对所有负载/所有完成操作的科学否定或论文贡献成立。

旧B2和七槽、原Raw/ZIP/BLOCKED/UNKNOWN保持，生产A/B/COE定义及原Formal/Gate不变。
本轮无服务器、采集、CUDA、模型或新交付包；Gate13限定PASS保持，Gate14不启动。

<a id="2026-10-17增补新b2-prefill参数诊断实现-06当前目标机待验证"></a>

## 2026-10-17增补：新B2 Prefill参数诊断实现 0.6（历史交付，后续零捕获见0.7）

**最小实现与本地CPU验证完成；只交付待审阶段A，不授予模型覆盖、A或COE资格。** 用户接受下文
0.5窄域方案后，本轮实现独立Engineering profile与参数消费者。0.5保留为设计时历史，旧微例
PASS、旧B2/Pilot BLOCKED、7槽NOT_RUN/0完整block及原UNKNOWN/NOT_ASSESSED均保持。

### 实际接线与版本边界

- 新声明`MEMSET-PYTORCH-PREFILL-PARAMS/0.1`、profile
  `MEMSET_PREFILL_PARAMETER_DIAGNOSTIC/0.1`、side/receipt/execution独立0.1.0；不是旧G1/Pilot
  的batch2扩容。manifest严格绑定新run/commit、完整`[2,512]`输入及mask摘要、实际两样本两token、
  三次warmup、repeat1、普通CUDART与记录器DLL实字节。旧batch版本仍不接受B2。
- [verified入口](../../exposedpath/gate8_diagnostic.py)复用原解释器、prepare→seal→model-run、
  模型inventory、设备UUID/PCI、真实软件配置及producer链。记录器**在原最终drain之前安装**，
  原成功drain后只启用预分配记录；原first Host-readable token时间戳之后关闭记录，Decode前停用。
  `.cpu()`、completion锚点、流、同步、请求边界和token-ready helper内容不改。落盘/拆除在窗外。
- [native recorder](../../scripts/native_memset_probe/prefill_recorder.cpp)仅hook已核验绝对路径的
  共享普通`cudaMemsetAsync`。一次Detours事务纳入既存同进程线程；4096预分配槽、自动call_id、
  uint64 count、指针地址别名、原value/return/LastError。命中时恰好一次原参数转发，无新CUDA
  查询/复制/同步、堆分配或磁盘I/O。别名不证明allocation生命周期；PTSZ/private不自动覆盖。
- [consumer](../../analysis/memset_prefill.py)枚举整个Prefill的目标runtime，不按旧84条或邻近时间
  配对。side↔闭合唯一NVTX domain/range↔同PID/TID/runtime严格双向唯一；实际process creation
  FILETIME另与入口started.json绑定。负返回仅复用已验`-1/-1`情况且仍要求真实完整范围。
  非零必须唯一合法MEMSET效果；零参正效果、未知效果、漏记、重入、外线程、溢出均拒绝。

### 零payload消费：独立实现，不是生产准入豁免

规则`MEMSET-ZERO-LOGICAL/0.1`仅用于这个未来新Engineering profile。保留原API墙钟/submit
类别、逻辑身份、真实提交顺序和原Canonical，不创建0ns或其他device activity。
临时验证视图仅去除已被参数证明count0的“必须有正activity”断言，再调用原局部Prefill门；
原始A输入仍含这些API预算，内部A不发布。随后必须独立满足同次drain、设备/context/native-
trace流桥、Host token、成功sync、所有真实成员/相邻FIFO边、terminal及LEGACY/PTDS必要后缀
一致。已完成历史和已完成必要成员保留；操作内D2H包含，sync提交边界之后工作不纳入。

允许的两种有限关系只是“Host零调用”或“同一隔离FIFO内空节点”；二者不得改变真实成员、
真实依赖和后续D2H terminal。零调用必须在该实际后续提交之前。pending历史、事件/graph/
跨流依赖、未知context/入口、模式相关歧义或terminal缺失仍拒绝；不声称已排除所有未记录依赖，
不授完整物理W/B。若真实B2不能证明这些条件，就停止，不扩hook或改合同追绿。

输出`parameters.json`包括原始实例参数、原API预算、效果引用、全部源hash、局部门事实及零节点
证明，成功仅称`MEMSET_PREFILL_EVIDENCE_COMPLETE_PENDING_REVIEW`。A/COE仍NOT_ASSESSED，
Request/Decode NOT_ACCEPTED。当前没有新模型trace或新可信A/COE结果。

### 本地验证与明确限制

定向新检查64项：参数/范围/覆盖反例，独立FIFO成员与terminal正反例，实际prepare→seal→profile
argv→verified producer→Canonical→参数消费文件链，阶段A/B显式分派与失败封包。运行环境
Python3.12.7；目标Python3.11.16尚待阶段A，未把本地AST或替身称为目标验证。

真实CUDA12.4头文件编译/链接与真实Detours **Host替身**转发执行已完成；本地工具链14.44/
SDK26100，目标既有14.38/SDK20348仍须实际编译验证。测试包含64位大count、原错误码/LastError、
容量溢出仍原转发、重入/外线程/错误入口、ctypes真实ABI与落盘；不运行CUDA程序。
旧路径另有14项相关检查通过（9项定向选择、5项入口检查），不是重跑全110/Q0。

整段本地演练实际运行PS5.1→控制器→头文件编译/Host Detours→64项CPU→单ZIP及CRC/hash；
Git部署/HEAD是明确替身，模型/设备/collector只在测试边界用替身。第一次深目录演练59通过/
5失败，原因为Windows路径长度，失败现场保留；改用新短路径后重跑，不修改测试期望或身份门。
最终命令、结果和回执位置见唯一科研进度7.179。未重跑旧SQLite/完整analyzer、旧54/110或Q0。

### 唯一待审交付与停止条件

增量前置以已核验微例回执的执行`002f3ae9fcc22f04356dbd22092dcddd8c63a460`绑定，
而非猜测服务器HEAD。复用固定Detours4.0.1/NVTX3.1.0/SDK12.4头文件；无安装/升级。
包索引绑定提交后实际执行/分析commit、全部新增接线实字节、输入/模型引用及历史功能token参考，
不把旧B2功能值参考解释为旧准入通过。实际包和阶段A整段命令见本地handoff交付入口。

阶段A仅部署、头文件编译链接、Host CPU检查、源码/运行库身份与新鲜空间回执；不运行模型/
CUDA程序/Nsight。阶段B必须另经真实A回执审查、绑定其精确SHA后显式启用；本轮不提供B命令。
只允许一个全新B2/512/2/warmup3/repeat1、1模型进程/1profile，无P0/Cpre/旧槽恢复。
安装/记录会扰动执行，该次只作参数/支持域诊断，不作自然性能或Pilot重复。

未来单次预算估计15分钟；profile300s、export180s（另readiness60s）、离线300s、driver900s硬
上限，无重试/替补/自动追加。启动实际输出/临时/归档卷分别检查且同卷不重复计数，2GiB预留；
历史YLQ总量null/UNKNOWN、长期50,000,000,000bytes目标未证明，不扫描ACL或自动清理。

**新B2成功**只意味着普通入口确实完整覆盖这次Prefill、参数/效果及有限局部依赖证据可审，
可以决定是否另审参数辅助COE；不自动恢复9组Pilot或发布A。**失败**则定位普通入口缺覆盖、
非零缺效果、参数/身份/范围或依赖/terminal不闭合的具体项并停止；不回填旧168次实例，
不恢复旧B2和7槽，不扩大hook/工具链。生产A/B/COE/registry、原Formal/Gate判定均未改变。

<a id="2026-10-17增补真实pytorch覆盖桥接与参数消费规则草案-05当前"></a>

## 2026-10-17增补：真实PyTorch覆盖桥接与参数消费规则草案 0.5（历史设计）

**裁决：GO，限进入一个新B2 Engineering参数诊断的最小本地实现准备；不是模型覆盖/COE准入已通过。**
参数完整后存在合法的窄域解决路径：正长度继续要求真实效果；零长度保留逻辑调用和已证依赖，
不伪造activity，并只在局部依赖闭包不受未定顺序语义影响时消除“必需正activity”这一拒绝。
若共享普通入口不能覆盖、出现非零缺效果或依赖不闭合，就在这一条路线停止，不扩hook。
本轮只审查/设计，未实现新记录器/消费者、未测试/编译、未发包或服务器命令，未运行任何GPU程序。

Material Passport：ARS experiment-agent / bounded plan；日期2026-10-17；本节DRAFT、未实施；
来源为当前源码、固定第一方接口和既有封存事实，不是新实验/新资格。当前研究设计v7.1、
实验协议v2.1与限定签署路线均不改；0.4微例PASS和旧B2/批次BLOCKED并存且含义不同。

### 0.5.1 真实调用覆盖：已有依据与尚不能证明的部分

微例已证明目标Torch目录内**共享CUDART普通导出**可被此Detours实现命中，并在一次Nsight
采集中与runtime/效果关联；目标运行库实际SHA256为
`f95273031fc5ea44cdb37e0a696a1b15b9d84a4ee977299a6f6e652ef4d790cf`，不是本地SDK归档DLL的hash。
不能由相同文件名、同版CUDA、微例成功推导PyTorch全部调用命中。

已有目标机PE原件（2026-09-27）在本轮按自身清单核对：
`torch_cuda.dll.imports.txt` SHA256 `608df902abc49982e4b3f9faa30c0c90977725324fb7fae59af86f5fd4855148`，
`c10_cuda.dll.imports.txt` SHA256 `0449388f81783840444f030227dcf11513cb129e7ff2e7867316480f9a36c51c`。
**c10_cuda导入cudart64_12.dll；两份导入表都没有cudaMemsetAsync或PTSZ直接导入；torch_cuda
另导入cuBLAS/cuBLASLt等native库。** 这既不证明缺口来自某vendor，也不证明一定是私有runtime；
动态解析、静态/私有副本及vendor内部路径尚未排除。该历史PE不冒充未来进程的实际加载事实。

固定执行链可读到：`gate8_diagnostic.model_run`核验解释器/输入/设备后，复用
[runner](../../exposedpath/runner.py)的setup→三次warmup→成功窗前drain→Prefill forward/argmax→
自然`detach().cpu().reshape(-1).tolist()`→实际Host token锚点；本轮不改该链。
保存的Transformers SDPA调用进入`torch.nn.functional.scaled_dot_product_attention`；
[PyTorch2.6 CUDABlas](https://github.com/pytorch/pytorch/blob/v2.6.0/aten/src/ATen/cuda/CUDABlas.cpp)
说明BLAS调用路径，[FillKernel](https://github.com/pytorch/pytorch/blob/v2.6.0/aten/src/ATen/native/cuda/FillKernel.cu)
使用gpu_kernel，均不能给旧168次实例指定真实callsite或count。**精确实例来源仍未知，拟用同次
动态覆盖判定，而不是继续源码猜测。** 本轮不查询旧SQLite或追索84条参数。

未来覆盖集合T预先定义为：已绑定目标进程/创建实例、原Prefill半开窗口内全部同类runtime，
包括合法数字版本后缀；另外审列PTSZ/其他入口和外线程，不能先过滤后宣布全覆盖。
T与侧记录R必须双向一一对应：run/request/phase、PID/TID、call_id、真实模块/导出、闭合唯一
NVTX domain范围、唯一完整runtime及原返回码全部一致；不是按旧rowid、次数84或最近时间配对。
PTSZ/private副本、漏记、范围跨界、重复、重入、外线程、容量溢出、未支持诊断一律BLOCKED。

### 0.5.2 从双case记录器到模型所需的最小调整（尚未实现）

1. **范围而非逐case arm。** 保留现有微例接口/角色；新增独立
   `MEMSET-PYTORCH-PREFILL-PARAMS/0.1` Engineering声明和侧记录版本，不把B2伪装旧G1/Pilot。
   复用verified模型入口与prepare/seal/输入/实际batch/token门，新源码/运行库/DLL另绑定新执行身份。
2. **窗口通知。** 在原成功drain之后、forward之前启用记录；首个Host token完成后停用，Decode
   前关闭，异常finally关闭。开始/完成仍取原锚点，不把NVTX或hook返回当completion。
   仅`before_copy`不够：它漏掉forward阶段调用。暖机/窗外调用原样转发、不误报“未arm”；
   Prefill内不允许不记录。只新增诊断Host/NVTX工作，不新增CUDA查询、同步、复制或切流。
3. **多调用但有上限。** 预分配4096记录及消息槽，自动单调uint64 call_id，不假定实例数；
   每个真实命中自动记录count/value/native stream/原return、调用线程与run内pointer别名。
   别名不能继续用“非空全部等于1”，也不记录内存内容。边界内无分配/磁盘I/O；溢出标错、
   仍恰好一次原转发，不覆写旧槽或重试。uint64 count/原LastError等复用已验ABI/转发纪律。
4. **安装与线程安全。** 仅同一绝对路径/实际模块普通导出，不改全API hook或第二subscriber。
   不能把微例的`DetourUpdateThread(current)`直接当多线程安全证明；安装/拆除在无在途调用的
   窗外，按[Detours事务接口](https://github.com/microsoft/Detours/wiki/Using-Detours)一次性纳入
   本进程可能受影响的既存线程，失败即停，不做常驻线程监控/权限升级。边界内外线程调用
   必须留故障事实并拒绝，不能静默略过；不得以只记录主线程掩盖其他线程的runtime。
5. **落盘/消费。** 原Host完成后保存完整侧记录、装载/attach/detach状态、原始NVTX返回值及
   捕获/漏记计数；真实导出范围仍是记录证明。Canonical不改写，新增参数证据sidecar引用
   原API/source hash；所有目标API统一审查。独立新profile消费后才能调用原局部投影/COE，
   不调用旧失败批次入口、不伪造`coe_pilot.process`成功。当前双caseconsumer不能直接用于模型。

### 0.5.3 参数消费草案：MEMSET-ZERO-LOGICAL/0.1-DRAFT

这是一项**仅未来新Engineering profile的准入增量草案，尚未批准生效/编码**，不是旧A/B或COE
公式改版。依据[CUDA12.4.1 memset规范](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/group__CUDART__MEMORY.html)
的count字节范围及[stream completion](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/group__CUDART__STREAM.html)，
count0只证明请求的字节写入范围为空，成功不证明工作完成/无内部命令/无顺序影响。

|实例证据|拟保留的事实与处置|不能推导|
|---|---|---|
|count=0、成功、完整实例覆盖|逻辑submit调用节点z、原API墙钟、原ordinal/native stream/context证据；没有设备记录就不创建device activity，状态ZERO_PAYLOAD_LOGICAL_ONLY；须再满足下面闭包条件|非阻塞、没有队列/顺序作用、全capture零丢失、自动COE通过|
|count>0、成功、唯一合法MEMSET效果|保留实际bytes/value/device/context/stream及correlation桥，沿原活动/依赖规则；首版只支持已验单MEMSET，value按字节语义核对，原int值不丢|最终token正确即可补关联；多效果求和/替代kernel自动获资格|
|count>0但缺效果，或count/身份/关联未知|具体NONZERO_EFFECT_MISSING或PARAMETER/PAIR/SCOPE原因，BLOCKED|填零、改non-submit/Host、借相邻活动；不能再用同配置重采追绿|

**零长度的有限可证明条件：**

- z保持API身份和真实同线程提交顺序；`host_call_order`不是GPU依赖边。已有流FIFO、event边、
  成功drain闭合的历史、已完成必要前缀以及所有后续真实成员全部保留；不删先行工作。
- native handle不直接当trace ID。必须复用同次成功drain/自然sync的物理scope、实际设备/主线程
  stream记录以及完整已支持调用序列，唯一约束z所在context/stream；仅阶段前后handle相同、
  或表里只看到一个context不足。context/device切换、未知入口或生命周期不明时继续BLOCKED。
- 首版限定已批准的**主线程、同一自然流、成功drain后的局部Prefill、无新incoming event/跨流/
  graph依赖**。所有正活动/正提交均完整映射且由实际copy/成功sync及Host token完成界定。
  完整必要成员截止于该sync捕获的提交边界，含copy内部D2H，不截在copy入口。
- 不宣称z实际入队或被跳过。分别保留“仅Host零长度调用”与“可能承担同流顺序的逻辑空操作”
  的未定关系；并沿既有LEGACY/PTDS审查。此处只比较文档流序语义和这两种零payload表示
  所构成的有限候选关系，不要求排除所有未观测内部机制。只有在**这些候选关系均不改变
  真实活动成员、真实成员间必要依赖及被观测terminal证据**时，才可消去z的几何贡献，继续局部投影。
  同一隔离FIFO内两种关系都保留相同先行活动是成立实例；不能仅比较A数值相同或守恒。
- 若z可能携入别流工作、成为无法被后续已观测必要效果界定的完成前沿，或终端/closure依赖
  未定关系，拒绝；不能以sync返回为z造GPU终止时间，不能给z造零ns activity或B barrier。
  已观测的正效果与count0矛盾也拒绝，未知效果不填零。

逻辑节点的设备区间是**不存在的观测对象**，不是“测得0ns”。A仍计原CUDA submit API墙钟；
COE只与被恢复为必要成员的真实GPU区间相交。内部未分离时间/空隙不改成纯等待，单sync B
保持原义且不因本草案获得完整物理资格。baseline也保留原API count/sum/union，将“参数证明
零payload”与“未解决缺映射”分栏，不能把两者一起改为mapped或零成本。

### 0.5.4 预先固定的独立预期/反例（设计，未运行）

|手工构造|独立预期|
|---|---|
|同S提交K，z(count0)，L，D2H，成功sync(S)；K已在sync前完成|W中的真实成员仍K/L/D2H；z保留逻辑序号，无activity；已完成K不删除，terminal为后续已证D2H；零关系投影不改真实依赖|
|别流Q工作可经legacy默认流空操作z影响后续S，缺少该关系证明|两种关系可能改变W，BLOCKED，即使count0、返回成功、最终token正确|
|z位于未映射context/stream，或只知stage前后handle0|BLOCKED，不复制相邻调用scope|
|z是末端可能完成节点，没有后续已观测效果约束|terminal未闭合，BLOCKED，不用sync.end造z终点|
|count0却关联正bytes MEMSET或未支持效果|冲突/BLOCKED；不按零参数过滤证据|
|count64→同次唯一64-byte MEMSET/正确scope，全部其他门完整|按原必要活动规则继续；不由读值代替映射|
|count64成功但无效果，或bytes/value/scope冲突|BLOCKED；这会否定“该实例仅因零payload缺activity”的解释|
|侧记录少/多一条、重复runtime、PTSZ/private未覆盖、外线程或第4097次命中|覆盖/容量明确失败，原调用仍转发；不得靠已有84条清单选择实例或扩大hook|
|零值合法但未知诊断、失败drain、pending历史或token冲突|独立质量门仍拒绝，不因为参数齐全而放行|

### 0.5.5 唯一后续建议及决策价值（待批准实现，非执行授权）

若继续，只实现上述最小调整与CPU文件链负例，再审一个**新B2 Engineering参数诊断**：现有
Windows/4090、固定1.5B/FP16/eager/SDPA、相同512输入复制两份、每样本输出2、warmup3/
repeat1、自然Host-readable路径；1新模型进程/1profile，无P0/Cpre/其他负载/旧槽续跑。
安装在窗外，记录仅主请求Prefill；模型仍按原定义完成Decode，Decode不准入也不追参数。
reuse未改的解释器/模型/输入/device检查，role与新源码精确绑定，不沿用旧seal。
这不是预先承诺旧B2的scope可复用：所需context/stream桥和有限关系不变性必须由新run事实
与已支持语义逐项建立；缺少任何一项，即使全部count为0也仍BLOCKED。

一次运行要同时回答两项有可判别后果的问题，而非为获得更多样本：
**共享入口是否完整覆盖本次Prefill？缺映射实例究竟是零payload、合法正效果，还是非零缺效果？**
双向覆盖及新草案所有前提均成立，才可另作参数辅助局部准入审查；普通入口未命中/部分命中、
非零缺效果、context/default依赖或terminal不闭合任一成立，就停止该路径，无重试、补样、
hook private/PTSZ、PyTorch重编或工具链更换。不要求新实例重现84次，不回填旧B2。

本地实现仍受原1～2工作日上限约束，先复用已验ABI/Detours/微例与既有S能力，只补模型
范围通知、多调用覆盖/容量、逻辑节点投影和实际文件链的独立CPU反例；不重跑完整Q0/110项。
未来目标预算建议：profile硬上限300s（含setup/warmup）、export180s、离线300s，整个流程
预留15分钟是估计，不是成功承诺；临时预留2GiB，预计新增保留20～100MiB（不含既有权重/
环境），不生成巨型domain。实际fresh空间待后续静态回执，长期YLQ<50,000,000,000bytes
仍未证明；本轮不盘点、清理或假定当前checkout。固定单次/硬失败即停，无自动追加。

**当前停点：覆盖审查和规则/反例草案完成，可继续这一窄域本地实现；真实PyTorch覆盖与
新规则资格未完成。** 若不接受上述窄域逻辑节点消费条件，则仅得到参数不能关闭准入，
不应为此制作采集包。旧B2/Pilot BLOCKED、7槽NOT_RUN/0完整block、旧A/B/COE、Formal/
UNKNOWN/历史Gate和全部原件均保持；0.4微例结论不升级。

<a id="2026-10-16增补nvtx返回值适配与封存微例离线裁决-04当前"></a>

## 2026-10-16增补：NVTX返回值适配与封存微例离线裁决 0.4（历史微例审查）

**限定0/64-byte同次微例Engineering复核PASS；原attempt仍BLOCKED，旧B2/批次仍BLOCKED。**
这是对已采原件的消费者0.1.1离线修复，不是新采集、模型覆盖或COE资格。下文0.3保留交付时状态。
没有服务器操作、部署、微例重采、CUDA/Nsight执行或新包。

### 根因与最小规则

原消费者把`push_level>=0 && pop_level==push_level`当作NVTX记录必要条件；两次实际返回均
`-1/-1`，却已有完整NVTX导出范围，因此在设备效果检查前误拒绝。
[NVTX接口文档](https://nvidia.github.io/NVTX/doxygen/group___m_a_r_k_e_r_s___a_n_d___r_a_n_g_e_s.html)
描述层级及负值错误约定，但[CUDA12.4.1 Profiler §5.1 Return Values](https://docs.nvidia.com/cuda/archive/12.4.1/profiler-users-guide/index.html#nvtx-api-overview)
明确提示返回值随工具实现变化，不宜用于条件判断；
[2023年官方论坛讨论](https://forums.developer.nvidia.com/t/nvtxrangepusha-and-nvtxrangepop-returns-2/255993)
也有Nsight返回-1而正确记录范围的实例。这不证明所有负值成功，不能据此忽略丢范围。

消费者/微型导出provider升级为**0.1.1**，side仍按0.1.0读取。只增加已观察的`-1/-1`
返回组合兼容，原始值写入新结果、标记`UNAVAILABLE_LEVEL_NOT_RECORDING_PROOF`，不改0或成功码；
其他未知负值/混合组合仍拒绝。无论返回正负，都必须核对：同进程唯一DomainCreate(event75)
实物及名称`EP_MEMSET_MICRO`、正确非默认domainId、闭合event59范围、run/call/PID/TID、
外层scope包含关系、固定调用/验证次序、唯一完整runtime动态范围和原返回码。
随后全部原设备/context/stream/correlation/bytes/value、功能参考及diagnostic门继续执行。
不是按NVTX消息推断domain，也不是用时间邻近配对。旧0.1.0 raw_excerpt缺少这些证明字段，
不能当新provider输入；从同一原SQLite重新提取，旧结果保留原版本，不补造字段。
native记录器、producer、launcher、采集argv及生产S/A/B/COE/registry均未改。

### 封存输入与独立复核

原ZIP `memset_micro_002f3ae9fcc2_once.zip`：68,580 bytes，SHA256
`29e4413ad7c2895d261718c54fd301266c01a94e647fe2d265475865f22ab3b8`。
CRC、27唯一安全成员/26项清单全部通过；manifest SHA256
`c177dcdd8caf4fb448074cf648c03f0e7734dd8f5c1ae48e7460a5b2be67bb32`。
原执行/原分析002f3ae9fcc22f04356dbd22092dcddd8c63a460，13源实字节↔对应Git blob、
delivery/包清单、已审A receipt/build/runtime引用全部一致，profile/export均exit0/无超时。
本次修复分析版本0.1.1及实际分析commit/源码hash另立绑定，不沿用旧分析身份。

|case / count|实际NVTX / domain|唯一runtime / corr|设备效果与验证|窄域判断|
|---|---|---|---|---|
|1 / 0|row2 / EP_MEMSET_MICRO，返回-1/-1|row8 / 126|未见关联效果；成功sync corr127 / physical row2，context1/stream7；读回64字节0x3c|零长度参数事实成立，顺序作用仍NOT_PROVEN|
|2 / 64|row3 / 同domain，返回-1/-1|row11 / 129|MEMSET row2，64bytes/value123，同context1/stream7；成功sync corr130 / physical row3；读回64字节0x7b|非零设备效果明确映射|

两次PID70312/TID73452、native stream0；不把native0等同trace7或全局默认流模式。
DomainCreate row1与外层row4均实际存在；setup成功drain为runtime row7，先于外层scope。
14条diagnostic全部severity1，既有规则无阻塞；不因此声称全会话无丢失，UNKNOWN保持。
独立Raw SQL按固定scope/call标签、同线程动态范围和文档correlation恢复以上表，不调用候选函数
生成预期成员；与完整消费者输出交叉核对。没有按最长API、相邻活动或最终读值补关联。

### 验证、产物与停止点

新增[回归](../../tests/test_memset_nvtx_recording.py)先复现14失败/2通过，原件失败原因为
`NVTX_RECORDING`；修复后实际命令：

```text
python -m pytest -q -p no:cacheprovider tests/test_memset_nvtx_recording.py tests/test_memset_same_capture.py --basetemp .local/micro_nvtx_final --junitxml .local/diagnostics/memset_micro_nvtx_reanalysis_v0_1/final.xml --tb=short -ra
```

**54 passed / 0 failed / 0 skipped，1.50s**，本地Python3.12.7；仅消费者CPU回归，不重跑native
构建、110项、完整Q0或任何实验。缺/重复范围、错domain/进程/线程/run、未闭合、API越界、
范围交叠、未知负值、效果缺失及真实SQLite错domain/endGlobalTid反例均按具体原因拒绝；
原正返回路径保留，fixture仅增加真实provider要求的domain/scope字段，不删负例。
py_compile、diff检查通过。复核新目录`memset_micro_nvtx_reanalysis_v0_1/analysis_0_1_1`包含
review/source_hashes/raw_excerpt、独立adjudication/calls及提交后analysis_binding；输入副本与原ZIP
前后逐项hash不变。原Raw/side/原derived/原BLOCKED receipt全保留，不覆盖报告。

**本次仅关闭这个微例的消费者误拒绝。** 可确认普通共享CUDART入口在这一次Nsight观测中完成
两次参数/NVTX/runtime/效果取证，但不能外推PyTorch/cuBLAS内部覆盖、零长度无顺序作用、
COE/A准入或自然性能。旧B2/批次BLOCKED、7槽NOT_RUN/0完整block、Gate13限定PASS及
UNKNOWN/NOT_ASSESSED不变。无需服务器补执行，不发新包、不恢复剩余槽；任何模型覆盖/零字节
消费政策仍未获本微例授权。本轮用户DOCX与大型原件均不纳入提交。

## 2026-10-16增补：最小同次微例实现与待审交付 0.3（历史交付状态）

**本地实现与CPU审查完成；目标机阶段A/B均NOT_RUN。** 用户已接受0.2接口级GO，
本轮只落实普通动态runtime入口的0/64-byte微例，不接模型、不恢复d6957de剩余7槽，
不改生产A/B、COE、registry、已签署协议或旧证据。下面0.2是设计来源，不再是当前实现状态；
不是因为本地通过就授予新实例/旧B2的准入。

### 0.3.1 实际接线与版本身份

- [记录器](../../scripts/native_memset_probe/recorder.cpp)、[真实SDK接口](../../scripts/native_memset_probe/recorder.h)
  固定Detours v4.0.1 / `e4bfd6b03e50de46b47abfbd1e46b384f0c5f833`，
  NVTX v3.1.0 / `bc282655dadb9288505f419c5b79d2ed3f1b4dfd`，CUDA12.4.127 runtime头与12.4.131 CRT头。
  依赖归档SHA与逐文件清单放入唯一交付，不在服务器下载浮动依赖或升级环境。
- [微例](../../scripts/native_memset_probe/micro.cpp)无CUDART/static runtime导入或链接库；
  未来B仅由绝对路径加载目标Torch所用`cudart64_12.dll`，校验实际模块路径/导出所属模块，
  查实际runtime API版本12040、单个mask3设备UUID/PCI。仅ordinary `cudaMemsetAsync`被审，
  PTSZ/static/private副本没有覆盖声明。微例通过也不能证明PyTorch内部走这个地址。
- 包装内只有一次原参数trampoline转发，保留原CUDA返回码及Win32线程LastError；
  `size_t`按uint64保存，含`2^63+7`的CPU实转发检查，无float/signed截断。
  预分配记录，无包装内磁盘I/O、CUDA查询/同步/复制。重入、未arm/溢出明确标错。
  实际PID/TID、进程创建FILETIME、run/call_id、native stream、导出地址与事务状态保留。
- 每次调用由专用domain的闭合NVTX线程范围包住；[离线消费者](../../analysis/memset_same_capture.py)
  用同PID/TID/entry的唯一完整动态包围关系双向配对，**不是最近时间**。
  侧记录、NVTX范围、runtime和效果均单独校验；readback不能代替效果映射。
  `side / exported-provider / review / delivery / receipt`均显式0.1.0版本。

本轮补齐的是**Nsight导出命名空间依据**，不改旧Native CUPTI字段解释：保存的目标2026.2
`AnalysisGuide.html`（SHA256 `bdcf574189e7eb687d4dc7c52bcebacae9c700c5a93a9e3aed8ff674960cbb11`）
明确把MEMSET.correlationId外键指向`CUPTI_ACTIVITY_KIND_RUNTIME(correlationId)`，该API表
eventClass 0/1区分runtime/driver。新微例只用该provider关系及进程内唯一correlation，
不把原生`CUpti_ActivityMemset4`的driver编号无条件当runtime编号。0.2要求的“已证明的Nsight关系”
据此落实；旧B2确无效果，仍无桥可补。目标归档网页不能直接读取，依据是已保存且复核hash的
安装文档，公开[AnalysisGuide](https://docs.nvidia.com/nsight-systems/AnalysisGuide/index.html)仅作可访问参照。

### 0.3.2 独立预期、真实验证及其界限

固定顺序不依赖实际活动长短：64-byte buffer setup为0x3c，成功device drain在测试scope外；
case1原参数count0/value0x7b，验证读回全0x3c；case2 count64/value0x7b，读回全0x7b。
两case各自既定成功stream sync与D2H是**微例功能参考**，位于被测调用范围之外，
不向模型增加同步。普通native handle0经每次独立成功stream sync的物理记录绑定trace
device/context/stream，**不证明全局LEGACY/PTDS**。正64必须唯一关联同scope的64-byte MEMSET；
非零无效果、错scope、重复/未知关联停止。count0只报告零长度实参；顺序作用NOT_PROVEN、
COE/A准入NOT_ASSESSED、dropped UNKNOWN，不实施零字节消费豁免。

独立手写fixture/SQLite文件链与实际Host DLL检查见
[配对测试](../../tests/test_memset_same_capture.py)、
[交付测试](../../tests/test_memset_micro_delivery.py)、
[native测试](../../tests/test_memset_micro_native.py)。
先验证缺失、重复、wrong entry/stream/identity、失败返回、重入、count溢出、未知诊断、
错误sync类型、缺drain和缺效果的拒绝；不能用更早的错误掩盖预期负例。
MEMSET之外的相关KERNEL/MEMCPY也读入，避免过滤后误称零效果；缺诊断表不等于空诊断。
同类官方warning沿用既有Gate9处置规则，不新建宽松规则。

本地实际命令（显式`MEMSET_MICRO_CPU_CONFIG`指向本地MSVC/SDK/固定依赖）：

```text
python -m pytest -q -p no:cacheprovider tests/test_memset_same_capture.py tests/test_memset_micro_delivery.py tests/test_memset_micro_native.py --basetemp .local/memset_micro_release --junitxml .local/diagnostics/memset_same_capture_v0_1/release.xml --tb=short -ra
```

最终 **54 passed / 0 failed / 0 skipped，10.93s**。本地Python3.12.7、MSVC19.44.35217、
SDK10.0.26100.0；目标Python3.11.16/MSVC19.38.33135/SDK10.0.20348.0仍待A。
真实编译/链接了完整微例与生产记录DLL，未执行二者；PE导入检查无CUDART/nvcuda/CUPTI。
真实运行的是Host函数替身DLL＋**真实Detours**，验证原参数恰好一次、返回码/LastError、
detach、错误入口和重入；NVTX在这组CPU测试中是明确替身，不是目标Nsight收集证据。
官方CUDART PE文件只读查询得到`6.14.11.12040`，不是虚构的toolkit semver；没有加载CUDA DLL。

另在全新本地目录完成**真实PS5.1→默认A→编译/HostCPU→回执/封包→已审A SHA→显式B失败**演练：
A exit0、内层54通过，B的采集器替身exit17后立即BLOCKED并封存原退出码，未生成side/SQLite、
未进入export或任何微例。Git部署/HEAD/clean和Nsight程序是明确CPU替身，不能冒称真实部署/共存。
证据位于忽略目录`memset_same_capture_v0_1/entry_rehearsal_release/audit.json`及原始日志/单ZIP。
本地未跑完整110项、完整Q0或旧模型分析；不新增长期监控或追索旧PID。

### 0.3.3 唯一交付及停止点

[默认PS入口](../../scripts/run_memset_micro.ps1)与[控制器](../../scripts/memset_micro.py)
仅A部署/构建/CPU检查，B必须显式开关＋真实已审A receipt SHA。新执行=分析commit在实现提交后
由[包生成器](../../scripts/package_memset_micro.py)精确绑定，避免hash自引用；服务器前置仅复用
封存d6957de真实receipt，旧失败包不解锁。交付包括bundle、固定依赖/SDK头、来源/源码/工具链
清单；不附新模型/新环境。A只编译链接与CPU替身，不运行微例、GPU查询或Nsight。
新runtime文件实际hash/PE导出/二进制hash必须先审A，再由B复核同一字节，不能由运行时hash自认证。

资源仅查询新输出、TEMP/TMP（可选TMPDIR）及归档卷的fresh空闲、同卷去重/可写；每卷预留
0.25GiB。本次无历史遍历/ACL/清理；长期目标<50,000,000,000 bytes，历史总量null/UNKNOWN。
预计A数分钟、含B/导出审查预留15分钟，仅估计；B单profile120s硬上限、export另120s，
失败/缺桥/共存/重入/诊断冲突即停，禁止重试/替补/模型；timeout后代UNKNOWN时拒绝自动封包。
所有新输出/ZIP不覆盖；旧B2、7槽NOT_RUN、0完整block及旧Gate/Raw/UNKNOWN保持。
**下一项只有协调审查这一个交付，然后由用户选择执行A；当前没有B采集授权或模型续跑授权。**

## 2026-10-16增补：同次Nsight实例取证的有界裁决 0.2

**裁决：GO，仅指有依据进入一个窄域同进程记录器的最小实现评审与受控微例设计；不是目标机验证通过，也不是模型采集或COE准入授权。** 选用下面路径b，不增加CUPTI subscriber。路径a在固定版本的已核验接口内不足。若b的唯一调用绑定或与Nsight共存不能在微例闭合，停止此路线，不扩大hook范围、换工具链或制作模型包。

本节保留0.2时点的接口裁决与设计来源，当前实现状态见0.3；下文2026-10-12的独立CUPTI方案/CPU原型保留为历史，不是本次选定路径。当前依据是[本批失败审查§13](completion_operation_batch_prefill_review_v0_1.md#13-d6957de候选pilot失败收口b2-prefill缺提交效果不续剩余槽位2026-10-16)：d6957de的B1完成、B2阻塞、7槽未运行、0完整block；B2 Prefill/Decode各84次缺效果。复用已完成Raw/Canonical和替代关联核对，本轮不重新查询SQLite。新实例不能补旧参数，旧B2/批次保持BLOCKED。

### 0.2.1 参数事实不等于资格

共同必要事实是新run/进程创建实例、PID/TID、实际被调用模块/入口、`size_t count`、native stream、原始返回码和同次Nsight API身份；还需原request/phase、设备/context/stream生命周期、drain、依赖闭包与完成证据。

|同次证据|能证明什么|仍不能自动证明什么|
|---|---|---|
|count=0且成功，实参/调用绑定完整|请求写入0字节；可以标记ZERO_LENGTH_ARGUMENT_OBSERVED|无内部设备操作、无顺序影响、全局无漏记录或A/COE合格|
|count>0且成功，有唯一合法设备效果桥，bytes/value/scope相符|该实例的非零效果可纳入既有提交/依赖恢复审查|必要前驱齐全、默认流条件、terminal与整窗质量均通过|
|count>0但效果缺失，或参数/桥接不明|具体缺口可被区分和定位|不能补零、改成non-submit/Host或借相邻kernel；仍BLOCKED|

[CUDA12.4.1 memory API](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/group__CUDART__MEMORY.html)定义count为字节数、写入前count字节；没有给出“count=0必然不建立任何顺序关系”的独立保证。因此零参数不能删除先行成员、事件边或默认流依赖，不能据此更改submit门。若未来拟允许“有实参但无activity”的零长度实例，仍须另审窄域零字节操作的消费规则及反例；本节不实施或预批准该语义。返回成功也不等于异步工作已完成；[API synchronization behavior](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/api-sync-behavior.html)不支持把调用墙钟解释为纯等待。

### 0.2.2 仅比较两条接口路径

**a．固定Nsight自有接口：本轮NO-GO。** 保存的2026.2.1安装UserGuide（SHA256 `5b100930126f3a3a819f13dd8335efc0bc2cd7f8bf0207a7063d57acb4c33e7c`）L763–779把`cuda-memory-usage`定义为内存使用观测、`cuda-trace-all-apis`定义为API覆盖；backtrace提供调用栈，不提供count。L6109起的NVTX payload能力能记录调用者显式传入的数据，并不自动取得第三方CUDA实参。现有已审schema没有这些API参数。固定[2026.2官方归档链接](https://archive.docs.nvidia.com/nsight-systems/2026.2/UserGuide/index.html)本轮不可读取，版本判断来自本地安装原件，不借滚动新版网页授予目标build能力。结论仅为“已核验接口不足”，不声称REP内部永无参数；不再搜索私有REP或增加采样。

**b．同进程native入口拦截＋专用NVTX调用范围：源码/接口级GO，目标兼容性NOT_RUN。**

- 候选插入点是实际已加载CUDA runtime模块的`cudaMemsetAsync`机器码入口，不是Python `.zero_()`包装或另一份runtime。匹配12.4.127 SDK的`cuda_runtime_api.h:7538`声明为`cudaError_t CUDARTAPI (void*, int, size_t, cudaStream_t)`；保留x64宽度/调用约定。头文件L210另有PTSZ重定向，**不得把_ptsz、私有静态runtime或其他模块默认为同一入口**；首版未绑定的入口一律未覆盖。
- 具体机制为[Microsoft Detours v4.0.1](https://github.com/microsoft/Detours/releases/tag/v4.0.1)，release绑定commit `e4bfd6b03e50de46b47abfbd1e46b384f0c5f833`。其[固定源码样例](https://github.com/microsoft/Detours/blob/e4bfd6b03e50de46b47abfbd1e46b384f0c5f833/samples/simple/simple.cpp)展示`DetourAttach`、trampoline调用原函数并原样返回结果；[使用说明](https://github.com/microsoft/Detours/wiki/Using-Detours)要求签名/调用约定一致。仅加载独立参数DLL，不调用`cuptiSubscribe`、不启用第二套activity、不借用Nsight私有CUPTI DLL。
- 在模型窗外完成库身份、地址和事务检查；包装体仅分配预留记录槽，复制count/value/stream与run内目标指针别名，push唯一调用NVTX范围，**原参数转发原trampoline恰好一次**，保存返回码并pop。不得新增CUDA查询、同步、D2H、模型行为或原request边界；不在包装内做磁盘I/O/模型日志，溢出或异常保留失败。保存原返回码/Windows线程错误状态，不清除CUDA错误或伪造成功。DLL/所指模块/导出地址身份、实际加载实例与事务结果均需留痕；加载、调用覆盖未在目标机验证。
- NVTX使用已有基础线程范围接口`nvtxDomainRangePushEx/Pop`，专用domain、带run nonce的消息及uint64 call_id；不依赖新扩展payload功能。[NVIDIA接口定义](https://nvidia.github.io/NVTX/doxygen/group___m_a_r_k_e_r_s___a_n_d___r_a_n_g_e_s.html)保证的是同线程嵌套范围，**不是CUDA correlation自动桥**。参数/返回记录在窗外落盘并绑定源码、DLL和REP/SQLite身份；不保存完整环境、调用参数全集或用户数据。

### 0.2.3 同次绑定及不能越过的边界

拟验证的证据链：`run/进程实例/TID/call_id侧记录 → 同call_id闭合NVTX线程范围 → 该动态范围内唯一原函数runtime记录 → Nsight合法correlation/driver桥 → device effect`。

这不是最近时间配对：范围由受审包装明确包住**一次原函数调用**；必须在同一Nsight时钟、PID/TID、函数/事件类别内完整包含该runtime，且一对一、无重复、无重入歧义，返回码与侧记录一致。无runtime、两个候选、范围丢失/交叉或不能证明一次原转发均拒绝，不设距离容差或回退到相邻编号。NVTX的call_id不冒充CUPTI correlation；缺少实际效果时，范围本身不能补造效果。

非零效果继续使用已验证的Nsight关联合同；匹配SDK `CUpti_ActivityMemset4`的correlation是**driver API命名空间**（`cupti_activity.h:2247–2252`），不能无条件等同runtime编号。有可见、唯一的嵌套driver桥或其他已证明的Nsight关系才使用；仅bytes、重叠或最终内存内容相同不足以补桥。native stream handle不能直接等于trace stream ID，尤其handle0不能判全局模式。零长度无activity时context/stream仍需独立现有生命周期与调用scope桥；缺失则停，不从相邻调用复制。

**覆盖/共存风险是微例的硬门，不是已消除的假设。** [Detours FAQ](https://github.com/microsoft/Detours/wiki/FAQ#why-dont-i-see-any-calls-to-my-detour-of-malloc)明确指出hook另一份函数不能覆盖目标私有实现。未来被审scope中每条目标Nsight runtime都必须唯一匹配记录器，记录器也必须反向匹配；未绑定的静态/动态副本、PTSZ变体保留未知，不升级成全API hook。安装UserGuide L1089–1092的`--injection-use-detours`仅描述Nsight进程注入，**不是自有API hook与Nsight共存保证**。不得修改Nsight的hook或以关闭Nsight绕过冲突；若记录丢失/重复或API/诊断冲突，路线停止。此附加NVTX/Host工作有时延扰动，所得运行不能当自然P0性能或无扰动基准。

### 0.2.4 唯一微例与停止预算（仅设计，未实现/未授权执行）

一个新native x64进程、一条同版本Nsight CUDA+NVTX profile；同Windows/4090/driver555.99/CUDA12.4栈，使用实际锁定runtime，不改工具链。与PyTorch同runtime文件身份必须另核；直接调用微例**不证明cuBLAS等第三方内部路径已覆盖**。只审已绑定的`cudaMemsetAsync`入口；不加载模型、不追加模型槽。

1. Setup在case窗外：选择既定GPU，单context、实际默认流入口、64-byte合法device buffer，置0x3c并成功drain；记录身份。测试计划预先给定两个不同call_id，不从analyzer生成答案。
2. case Z：原始参数`(buffer,0x7b,0,stream)`，原样转发一次；随后在**被测调用范围之外**执行既定成功sync/D2H验证，64字节须仍为0x3c。必须记录count0、实际stream与原始成功返回，并一对一找到Nsight runtime。零次/零bytes activity均按实物保留，不能预设缺activity=零顺序影响；出现正bytes矛盾或未知桥则停。
3. case N：同buffer/流调用`(buffer,0x7b,64,stream)`，随后范围外相同验证，64字节须全为0x7b。必须取得count64/成功、唯一runtime及合法64-byte设备效果桥、正确device/context/stream。最终读值是独立功能参考，不替代correlation；效果未映射即失败，即使读值正确。

这是一次微例内两个预定case，不是两个模型进程；验证用sync/读取属于微例oracle，**不复制进模型完成路径**。任何构建/加载/入口身份、NVTX/runtime覆盖、参数/return/效果或诊断冲突即停止；零值本身不是失败，必需记录缺失也不能判成功。结果只决定是否值得审查记录器的有限模型应用：通过不能认证旧B2，不能证明所有模型调用经过该地址，更不能授予COE或零字节准入。后续新模型如再出现任何未覆盖/非零缺效果，仍拒绝，不临场补hook/加采。

投入上限建议：后续若批准，最小本地原型及CPU ABI/转发/文件链审查封顶1～2工作日，**这是止损预算而非完成承诺**；目标机仅1进程/1profile、硬超时120s、含构建/审查预留15分钟/临时0.25GiB估计，未知空间拒绝，无重试/模型/额外样本。微例失败或到本地投入上限仍不能建立唯一调用桥即NO-GO，保留失败事实并结束，不滚动扩建。本轮没有代码、测试、包或服务器命令。

### 0.2.5 本轮证据与未验证项

本轮只读安装说明/匹配SDK/公开接口，未运行旧SQL、CUDA DLL、Nsight或任何实验。新核对`cuda_runtime_api.h` SHA256 `fb3c938ef38d3a9be88e111688ced12ea9b96dd62e48da8c955409e867e1db08`；UserGuide与`cupti_activity.h`的既有hash复核一致（后者`3796fb651d9983e407f2d007d8089f53a218e96b167a5452ab23908176b18b6e`）。官方Detours/NVTX/CUDA资料只证明接口存在与所述功能；目标加载、共存、命中率和效果桥均NOT_RUN。没有“取得参数即可放行”的规则改变；COE/生产A/B/registry/旧Formal、UNKNOWN/NOT_ASSESSED和Gate13限定PASS均不变。唯一建议下一步是**审查该微例的最小实现是否值得投入**，不是恢复剩余7槽或重采旧配置。

---

## 2026-10-12历史方案（以下原文保留，不作为当前执行计划）

2026-10-12；Engineering设计和CPU原型，不是collector资格、服务器交付或采集授权。[旧实例审查](batch_load_memset_effect_review_v0_1.md)已结束：原B4仍BLOCKED，旧84次调用不再追索。Gate13限定PASS、Gate14 NOT_RUN保持。

## 明确结论

**有公开SDK依据的窄域候选是独立CUPTI callback＋activity诊断，不能假设与现Nsight并行。** 匹配CUDA12.4的Windows头文件已核验，CPU原型验证了参数复制和拒绝关联歧义；目标进程的实际DLL加载、订阅及activity路径仍未验证。因此本轮不交付模型/重采入口、不修改A准入；下面的有界步骤须先审查，再实现和验证其native运行部分。若要求“原Nsight profile不变且直接增添CUPTI subscriber”，该方式停止。

新增记录用于识别**新调用实例**的count、stream、return和设备效果，不是自然性能结果；也不能补旧84次参数或恢复原B4资格。独立CUPTI数据不是现Nsight Canonical合同的自动替代品，不启动通用collector、全Q0或新A/B资格工程。

## 固定版本与第一方依据

目标平台已有回执：Windows/x64、Python3.11.16、torch2.6.0+cu124、CUDA12.4、原4090/driver555.99、Nsight2026.2.1.210-262137639646v0。模型、固定512-token输入、batch4、每样本输出2、FP16/eager/SDPA、warmup3/repeat1和Host-readable完成路径均沿用原[batch合同](batch_load_engineering_plan_v0_1.md)。不升级平台或改allocator/同步/边界。

已保存的目标安装UserGuide：SHA256 `5b100930126f3a3a819f13dd8335efc0bc2cd7f8bf0207a7063d57acb4c33e7c`。`cuda-memory-usage`是内存使用观测，`cuda-trace-all-apis`是API覆盖，backtrace是栈信息；这些说明没有给出当前build能导出每次memset count/native参数的肯定接口。已有SQLite/API schema也无此实参。**仅结论“当前已核验接口不足”，不是工具绝不支持。** 不为此开启CPU采样或重复REP搜索。

从[NVIDIA CUDA12.4.1官方组件索引](https://developer.download.nvidia.com/compute/cuda/redist/redistrib_12.4.1.json)取得并校验Windows组件，未安装、未执行其中的CUDA工具或DLL：

|组件|版本|ZIP bytes|ZIP SHA256|
|---|---|---:|---|
|cuda_cupti|12.4.127|14921079|6ad8df634d60e4bc96cf6914af71a5708f6460a25a39d0183780c6bdebfa60c7|
|cuda_cudart|12.4.127|2474721|6a1c32e68ee1a95ca17334691ff9ad1ffe7f352c24a083d55e4c96b8063b2bcb|
|cuda_nvcc（仅CRT头文件依赖）|12.4.131|63662970|3b14cf8dd9dda4a3b1a9682270d46eef775f018e17650187a8a448a06111f2b8|

此SDK的CUPTI API版本为22；`cupti64_2024.1.1.dll`为4576840 bytes、FileVersion2024.1.1.0、SHA256 `560a36596b6c6db6ecb44bbdc1b9d3bbf34965e919d13e7285f4d1c3542916ce`。这只是已下载候选，**未在目标机加载或查询版本**。目标Nsight安装自带`cupti64_129.dll`为4579976 bytes、FileVersion2025.2.1.0、SHA256 `47b244aafd892c52bc9f6e954b49c8f94e01186a73152e6d9aaf1fbc5d2aa8d8`；库存信息不证明其实际加载、公共ABI版本或可作为第三方client依赖，禁止借用/混装。

匹配SDK中的可复查定义（并非拿较新文档推断目标ABI）：

- `generated_cuda_runtime_api_meta.h:1988–1993`：`cudaMemsetAsync_v3020_params`包含devPtr、value、size_t count及cudaStream_t stream。count是字节数；x64不得经signed-int64/浮点截断。[CUDA12.4.1 API定义](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/group__CUDART__MEMORY.html)。
- `cupti_callbacks.h`的CallbackData/订阅说明：参数只在callback内有效；ENTRY复制参数，EXIT复制返回码，`correlationData`绑定同次进入/退出。runtime/driver callback各自匹配相应API activity correlation，命名空间不得混用。只允许单subscriber；Nsight启动时也可能返回`CUPTI_ERROR_MULTIPLE_SUBSCRIBERS_NOT_SUPPORTED`，必须停止，不取消他人订阅或换较新多subscriber版本。
- `cupti_activity.h:2194–2302`的Memset4：bytes、context/device/stream、时间及**driver API correlation**。没有MEMCPY结构中的runtimeCorrelationId桥接，不能把原runtime编号直接借给MEMSET。start=end=0表示时间不可得，不是零时长证明。
- `cuptiGetTimestamp`提供activity共同时间域；`cuptiGetContextId`、`cuptiGetDeviceId`、`cuptiGetStreamIdEx`提供显式映射，后者要求正确perThreadStream语义。native handle0、logical cuda:0、trace stream0不等价；若默认流映射不能证明，保留UNKNOWN/拒绝，不回填全局LEGACY/PTDS。

匹配归档内完整说明/头文件与本地审计存于忽略的诊断目录；不提交vendor文件、二进制或机器路径。

## 最小运行设计（尚无可启动入口）

**候选native client仅服务本任务；不同时运行Nsight、torch.profiler或另一CUPTI subscriber。** 在独立目标Python进程中、模型加载/首次CUDA初始化之前，显式初始化client。使用绝对路径加载锁定DLL，不搜索PATH；保存候选SHA、实际模块路径/文件身份/hash、实际`cuptiGetVersion`及每项enable/subscribe返回值。已加载不匹配CUPTI、API不为22、subscriber冲突或初始化失败立即停，不尝试另一版本/自动重试。调用SDK查询本身不是CPU-only。

只启用所需runtime/driver/resource callback和API/MEMSET/KERNEL/MEMCPY activity。全driver回调只用于同线程实际嵌套桥接，不记录用户数据/环境/无关参数。callback内禁止CUDA runtime/driver调用；仅用文档允许的CUPTI查询、复制小记录，窗外落盘；callback异常、队列溢出或flush失败保留拒绝，不让记录器改变同步语义。量化新增记录数量/时间，但不将诊断时延当自然性能。

同次记录最少包括run/进程创建实例/TID、全局序号、独立call_id、ENTRY/EXIT、domain/cbid/name、context/native stream、count/value、run内pointer别名、返回码及CUPTI clock。参数指针不能留到EXIT再读。request/phase绑定来自原producer的显式scope生命周期接口并保留原ledger引用，不能仅按相邻时间猜ownership；接线不移动原completion/NVTX或增加同步。资源映射保留查询参数、返回码、同线程/生命周期；设备必须对应既定UUID/PCI，不按编号相同推断。

runtime ENTRY → 实际嵌套driver ENTRY/EXIT → runtime EXIT → 对应API activity → driver-correlation设备activity为唯一允许的关联链。无嵌套记录、缺context/stream映射、correlation重复、跨run/进程或未能界定的诊断均拒绝；不借邻近kernel。若库内部不走可观测driver桥接，记录参数事实但设备效果保持未知。kernel替代路径仅保存明确桥接事实，不能用kernel时长或假bytes冒充MEMSET覆盖。

三种关键结果必须分开：

|证据|允许输出|不能输出|
|---|---|---|
|同次ENTRY实际count=0、EXIT成功、身份/参数完整|ZERO_LENGTH_ARGUMENT_OBSERVED|全部GPU效果为零、无顺序影响、A自动通过|
|count>0且有唯一同次显式MEMSET映射、bytes/流/设备一致|NONZERO_DEVICE_EFFECT_MAPPED|全capture无丢失或自然性能结论|
|count>0但无明确设备效果|NONZERO_EFFECT_MISSING，BLOCKED|补零、non-submit/Host归类或借成员|

参数/返回码/关联未知继续拒绝；零参数与实际正bytes效果矛盾、多MEMSET仅靠bytes相加、未支持kernel关联、时间/生命周期冲突均单独阻塞。UNKNOWN保持UNKNOWN；事实确认和测量资格分开，不以返回成功或未见warning放行。

## 一次受控验证与有界预算

后续若批准并完成native client，只允许以下**顺序门**，不是重新跑原四组：

1. 一个不加载模型的tiny CUDA进程，锁定相同DLL、身份和client。初始化与必要drain在测试scope外；固定显式nonblocking流和64-byte buffer。独立预期：先置为0x3c，调用count=0后Host读取仍为0x3c；再调用count=64/value=0x7b后64字节均为0x7b。实际参数/返回码必须分别为0/64及成功；非零须有明确driver桥接的64-byte MEMSET和正确资源映射。测试中允许其既定验证sync/D2H，绝不向模型request添加这些调用。CPU原型不能替代此目标栈验证。
2. 只有上述全部通过，才考虑**最多一个新B4模型进程**，固定512×4/每样本2输出/warmup3/repeat1，原input/model/GPU/backend及完成路径不变，无P0/B1或同批补采。在目标scope中逐call输出三类事实；本进程用独立CUPTI，不产生“同Nsight qualified A”。新实例数量可与旧84线索描述性比较，但不能认证旧实例或假定同样参数。

本轮不执行、不打包；先协调审查此证据路径是否值得。未来预算建议：tiny最多120s、模型最多300s、总15min/临时2GiB硬上限，均为待审估计；固定两进程上限、无自动重试/换provider/扩点/补采。加载/订阅/微例失败就在模型前终止；新B4参数仍未知、非零缺效果或冲突时到此结束，不追加监控或同配置采集。原长期存储<50GB政策沿用，完整归档核验后才另审可重建副本清理，不在本轮删除。

即使此参数诊断成功，若要发布新B4可信A，仍须另审其实际输入桥接与现有科学消费者适用性；本方案不承诺通过，也不把新provider自动纳入冻结协议。无需重做完整旧Q0；不启用D/Signature、Pilot或Gate14。

## 本轮CPU原型与验证边界

[纯CPU参数证据原型](../../scripts/memset_parameter_prototype.py)版本`memset-parameter-prototype/0.1.0`，显式只接受`CPU_SYNTHETIC`/`ENGINEERING_PARAMETER_FORENSICS`。它没有采集CLI、torch/CUDA/CUPTI调用或S/A入口。真实数据不能靠改role送入科学链。只实现单MEMSET的窄域关联，不用求和补齐多活动，不支持的路径拒绝。

[native结构体复制原型](../../scripts/prototypes/memset_callback_copy.cpp)使用匹配SDK真实定义，ENTRY复制count/value/native stream，EXIT复制return；CPU替身改变原参数后，副本必须保持。它是普通EXE而非注入DLL，未链接CUDA/CUPTI。实际PE导入表只有Windows/CRT，源码没有动态加载/vendor API调用；没有通过打印“0 CUDA调用”来代替检查。

[独立测试](../../tests/test_memset_parameter_prototype.py)包含零/非零/缺效果、同次ENTRY/EXIT、driver桥接、跨run/PID、correlation跨线程复用、native0错流、缺参数/return、失败/部分记录、零时间未知、多活动求和错误及实际JSON文件往返。六个native用例含x64大count `2^63+7`，不加载GPU库。未设置匹配SDK和MSVC时native测试显式skip，不能称验证完成。本次显式配置执行后的最终结果见科研进度7.138；不重复全量/Q0或旧实物分析。

本地MSVC为19.44.35217（不是目标机19.38），本地头文件编译不是服务器加载/回调资格。编译依赖/编码/无关activity头文件padding导致的初稿失败已保留，改为匹配12.4 CRT依赖、UTF-8和最小callback头文件；未改vendor定义或屏蔽生产错误。

**停止点：本地可行性/CPU接线可审查；目标加载及tiny CUDA验证未运行，新B4不获授权，旧B4保持BLOCKED。** 目前没有可安全直接部署的采集包；不把SDK存在等同真实回调成功，不制作未经验证的重采入口。
