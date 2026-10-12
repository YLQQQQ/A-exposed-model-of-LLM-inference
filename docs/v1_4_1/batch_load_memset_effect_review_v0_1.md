# Batch-load memset提交效果有界审查 0.1

2026-10-12收口；实物查询于2026-10-11完成。[前次失败审查](batch_load_failure_review_v0_1.md)及[执行合同](batch_load_engineering_plan_v0_1.md)保持。仅本地只读查询、来源核对与文档收口，无新模型/CUDA/Nsight运行、export或完整analyzer重算。

## 结论与证据身份

**未发现parser过滤或runtime/driver关联的实现遗漏；现有可读证据接口下，旧B4不能合法离线修复，结束这84次旧调用的追索。** B4仍为`ENGINEERING_SCOPE_SUBMIT_MAPPING`/A空；不把无activity、returnValue=0、调用短或规则性当作零提交。B1已准入的Engineering投影A、两组P0性能和B4观测事实可保留。Gate13限定PASS、Gate14 NOT_RUN不变。

执行版本`2af14b11dd990d159ff0b3204d26a1527244079c`。原包103907198 bytes、SHA256 `b290a96f85d68c54adf8f9be0705fce2f188d4dffc8e98b44f7b6d5a909b8494`、清单SHA256 `157ff32769bb569ef1982ba3daa2846dbe06979a10e8330a9720a648f2ea4998`；沿用前次完整CRC/258项哈希与覆盖核验，不重复扫描全包。

本次消费的B4 SQLite SHA256 `569b690715495748f1af6706d2ea93a5b0a5a94a0fc29f104e1c9cd542b2a7be`，REP SHA256 `a83385338d612ef9ebaa374c2d6878f764c4e782be7abeda79799959b30253f5`，均与原Canonical manifest绑定一致。SQLite以read-only/immutable打开，查询前后哈希不变；没有重新export或改Raw。新本地小产物：

- `cross_table_audit.json`：179218 bytes，SHA256 `f97cbfb6b66eb32a793e2fed499c0e0d7855cd20cbfa8d7f08a98215803a06d0`。
- `evidence_binding_and_results.json`：9530 bytes，SHA256 `f05ddf441d1f35814cdd9836e4aa09afb7c0a1b4797cc9ce3875b6d766482903`。

私有定位留在忽略的handoff。上述新审计不替换原报告或授予batch4资格；`dropped_records_status=UNKNOWN`、`measurement_validity=NOT_ASSESSED`保持。

## Raw→Canonical与关联排查

已检查全部46张表的schema及其中全部六个correlation列；按原始rowid、进程、context、device、stream、correlation、时间及memory属性逐项比较，不用时间邻近补关系。

|原表|Raw/Canonical记录数|遗漏、额外记录或关键字段差异|
|---|---:|---|
|KERNEL|13408 / 13408|0|
|MEMCPY|348 / 348|0|
|MEMSET|120 / 120|0|
|RUNTIME（含driver类）|40769 / 40769|0|

RUNTIME的`eventClass=0`为CUDA runtime、`eventClass=1`为CUDA driver；分别13953/26816条。没有独立DRIVER表不意味着driver未被采集。84个缺映射correlation在RUNTIME中只命中这84条API自身，在KERNEL/MEMCPY/MEMSET/OVERHEAD/SYNCHRONIZATION均无记录（查询没有先按目标PID过滤）。没有已采external-correlation桥接表；这些API的callchainId全部null，同线程实际包含/被包含区间也没有driver候选。

目标request内114次成功`cudaMemsetAsync_v3020`中，30次有实际MEMSET关联：28次1536 bytes、2次16 bytes。剩余84次全在Decode，API墙钟合计50717ns；30次已知参数不能替代另外84次的参数。

首个缺口是runtime38606/corr201238/PID65008/TID59500，23699269762～23699271214ns。随后driver23455/corr201239（23699271675～23699280228ns）有自己的kernel11867/corr201239/context1/device0/stream7；二者不嵌套，返回后相邻461ns及corr递增不是关联证据。末个缺口runtime39985/corr226267。全部缺口列表及精确字段保存在上述审计JSON。

API表仅有start/end/eventClass/globalTid/correlationId/nameId/returnValue/callchainId，没有旧调用实例的devPtr/count/value/native-stream实参。MEMSET表的bytes/value只描述已有设备activity。[CUDA12.4.1定义](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/group__CUDART__MEMORY.html)中的count是字节数；Async也不是Host非阻塞保证。因此现有实物不能区分零字节调用、其他提交路径或观测缺失。这个结论限定为**当前已核验接口不足**，不声称REP私有格式绝不含任何信息或工具永不支持参数。

## 固定源码能说明什么

[Qwen2 v5.17.0源码](https://raw.githubusercontent.com/huggingface/transformers/v5.17.0/src/transformers/models/qwen2/modeling_qwen2.py)的SHA256 `34390fea7648b444d5727abef0b85acceba28f856aedec6c335d51253806bfee`，与已有目标机源码快照中该文件声明完全相同。它可定位带bias的q/k/v Linear、cache/attention调用路径；不能给出旧84次native调用的字节数、调用栈或提交效果。

对照[PyTorch2.6 CUDABlas](https://raw.githubusercontent.com/pytorch/pytorch/v2.6.0/aten/src/ATen/cuda/CUDABlas.cpp)及[FillKernel](https://raw.githubusercontent.com/pytorch/pytorch/v2.6.0/aten/src/ATen/native/cuda/FillKernel.cu)：前者提供GEMM/batched GEMM/cuBLAS调用路径，后者使用gpu_kernel；这两个文件没有直接cudaMemsetAsync调用。官方tag不等于整个目标wheel/native库的精确构建证明。不能根据84=28×3、偏置层结构或相邻GEMM就归因cuBLAS，也不能凭源码可能路径认定旧实例是no-op。本次没有复现运行来替代原调用证据。

## 可保留的数字

以下均为一次Engineering观测，不是稳定性、收益或新Formal结论。两组Pass0的Host completion时长，单位ms：

|条件|Request|Prefill|Decode|
|---|---:|---:|---:|
|512/batch1/输出2|141.544300|72.305100|69.239200|
|512/batch4/每样本输出2|231.408800|167.782100|63.626700|

B1已准入Pass1的trace-native A，单位ms；**不用P0或Host记录时长作A分母**：

|窗口|T|Host|CUDA API|Device wait|sync residual|unattributed|
|---|---:|---:|---:|---:|---:|---:|
|Request|178.790817|87.402909|90.700161|0.525502|0.162245|0|
|Prefill|100.116413|45.683467|53.771358|0.525502|0.136086|0|
|Decode|78.674404|41.719442|36.928803|0|0.026159|0|

Device wait占比分别0.293920%/0.524891%/0%；CUDA API submit/non-submit分别87.509551/3.190610、52.179575/1.591783、35.329976/1.598827ms。顶层/子类守恒、互斥和Request=Prefill+Decode沿用已完成逐记录核验，不能据守恒替代依赖正确性。

B4模型入口PID65008正常退出，producer COMPLETE、profile exit0/无超时、export PASS；实际warmup3、512×4、每样本2token，逐值与P0一致。Host P1 Request/Prefill/Decode为248.322400/152.443000/95.879400ms，仅为完成边界观测。已观察GPU activity并集：B1为71.678087/52.541659/19.136428ms；B4为138.484709/104.121389/34.363320ms。活动量增加不等于Host暴露增加，B4缺映射未解除前不发布可信A或Device wait比例，也不称其设备效果为零。

## 唯一最小补证方向：先设计，不交采集任务

真正缺的是**同一次native调用的实际参数及设备效果关联**，不是更多同配置Nsight结果。已有包不能补这些实参；新观测也不能反向认证旧84次调用。仅推荐审查一次独立、窄域CUPTI callback＋activity参数取证：同B4输入/完成路径、单目标进程，无B1/整批重跑，不加同步，不用于性能比较或替换正式collector。当前仅设计，未实现、打包、部署或授权执行。

[CUPTI12.9.1 CallbackData](https://docs.nvidia.com/cupti/12.9.1/api/structCUpti__CallbackData.html)提供entry/exit、functionParams、exit returnValue、context/contextUid和对应API activity correlationId；参数指针只能在callback内读取并复制。最小记录实际count/value、地址的run内别名（无内存内容）、native stream、PID实例/TID、返回码及同次MEMSET/KERNEL activity。runtime/driver若有不同correlation，必须记录实际嵌套桥接；context/stream到设备标识也须有显式映射和生命周期，不能按编号相等或时间邻近猜测。

[CUPTI12.9.1订阅限制](https://docs.nvidia.com/cupti/12.9.1/main/main.html)不允许与另一subscriber并行。**不得直接在现Nsight profile中再订阅**，不得引用较新CUDA的多subscriber能力作为目标机依据。目标SDK/ABI与该方案可用性尚未核验；若版本、订阅或参数结构不支持，必须在模型执行前STOP，不自动升级工具、改collector或fallback。此限制使方案仍是待审取证方向，而不是可直接执行的交付。

预定判别与反例：成功且count>0要求同次明确设备效果；缺activity、错PID/correlation、生命周期冲突、未能界定的诊断均保留拒绝。count=0只证明**新调用**的实参为零，还须核对该调用有无其他提交/顺序影响，不能自动推导无依赖或A通过。任何新结果均不得给旧84次补零、借成员或改判旧B4。若后续需要将零效果参数纳入准入，须另审显式adapter规则及这些负例，不在本轮偷改支持域。

此次有界调查已结束：没有可修的分类/parser遗漏，不改业务代码或运行旧回归来凑验证。现有4槽全已执行，无待续槽位；不提供重复采集包。唯一下一步是协调审查上述参数取证是否值得且能取得所需证据，旧batch4 A结论停在BLOCKED；不扩负载、API内部等待分类、Gate14或其他资格层。
