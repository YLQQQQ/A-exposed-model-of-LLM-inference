# Batch4 memset参数取证可行性审查 0.1

## 2026-10-16增补：最小同次微例实现与待审交付 0.3（当前）

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
