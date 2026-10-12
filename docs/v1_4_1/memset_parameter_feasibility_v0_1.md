# Batch4 memset参数取证可行性审查 0.1

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
