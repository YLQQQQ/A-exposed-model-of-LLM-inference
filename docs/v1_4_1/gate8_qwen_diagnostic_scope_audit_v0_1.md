# Qwen诊断作用域有界审计 0.1

2026-09-28；Engineering；只读原件，不形成新资格。执行commit为
097f68a21eb9c75dbf390b7529a19c4316dda98e。

## 封存身份与结论

输入ZIP 26453554 bytes，SHA256
7cc443d3b43882c1eb1160746bb5b81c91b979ab1afb2416c3bd679b87ded2fb。
本地复核CRC及61项文件大小/hash。SQLite SHA256
b369a809c3764f933dc606305590e85b56eb2d5e7fda16dd1ab10fd217f5c196。
REP SHA256 4ed5f2f4540210089015a3db58c9994e5e366ebd22f918d2e83985478f16edd9。
目标入口65784 exit0、producer COMPLETE；collection/export成功不等于A准入。
原MODEL_A_SCOPE_BLOCKED及空a_records保持，不更改UNKNOWN，不授模型/Gate8通过。

## 警告及进程事实

DIAGNOSTIC_EVENT rowid 2/3/7/8对应PID10988，5/6/10/11对应PID54228。
两组各为NVTX可能未收全、NVTX零事件、CUDA profiling可能未正确启动、CUDA零事件。
这些记录的severity=2/source=3、timestampType=2；同库枚举明确2=HostTimestamp，
不能直接与request的TargetTimestamp比较来证明窗外影响。

rowid14证明54228于target timestamp 931198822完成common injection初始化；
rowid15证明10988于18125370533完成common injection初始化。PROFILER_OVERHEAD分别8条，
范围881021448–1000794346、18102045874–18129574347。
这些是已观测开销范围，不是宿主完整生命周期或警告影响范围。
ThreadNames中两进程具有[NSys]、[NSys Comms]、[NSys stream redirect]；
它们是线程标签，不足以把宿主进程称为Nsight转发器。

唯一profiler启动明确记录为rowid12目标65784。ProcessStreams只有目标及全局记录，
没有两个警告进程的独立输出。现有SQLite无父PID/可执行文件/命令行/进程生命周期字段；
StringIds未找到能绑定它们的git/python/nvidia-smi程序身份。
目标拥有全部21468条runtime与13条NVTX记录，仅说明已观察到什么，不证明外进程无相关活动。

代码的pre-model identity会调用git rev-parse/status；平台adapter subprocess.run只返回输出，
不保留PID与调用生命周期。TorchBackend.identity亦有nvidia-smi调用。代码存在候选子进程，
却不能把调用次数或时序猜测转成10988/54228的角色证明；第三方导入也不能据此排除。

## adapter判断

gate8_diagnostic_scope使用完整globalPid区分TARGET_PROCESS/OTHER_PROCESS，后者不是豁免。
gate8_engineering_scope当前没有有证据支持的warning resolver，将8条保持IMPACT_UNBOUNDED。
未发现这份输入上的PID解析错配或已有作用域证据被丢弃；当前阻塞是证据不足，
不是可通过改分类解除的已证实adapter缺陷。不提出PID白名单或warning删除补丁。

## request必要事实

共同trace锚点NVTX rowid1/2/3为29692454894、29797027557、29872161507 ns，
对应full=179706613 ns、prefill=104572663 ns、decode=75133950 ns，PID65784/TID50648。
三点具有同一run/request及原记录引用，host-readable token语义不由时间重叠推断。
drain runtime rowid17430：cudaDeviceSynchronize_v3020、return0、correlation61544，
29691467701–29691482102 ns；唯一context同步在其内部，早于request开始。
context1/process65784/device0声明nullStreamId7；request中3492条kernel均stream7。
按globalPid+correlation与API连接，另有3条memcpy、3条memset均stream7，合计3498 activity。
全部窗内API属于TID50648，drain返回到request结束之间没有部分越界API。
窗内观察到3个stream同步（correlation61651/90863/116228）；不能只检查两次token同步。
窗内API仅既有支持submit/sync及cuKernelGetFunction、cudaStreamIsCapturing两类局部分类缺口，
观测返回值均0。setup/config记录sdpa/qwen2/use_cache；native backend及default mode仍UNKNOWN。
物理S的350条INVALID/INVOCATION_BOUNDARY_INVALID不直接等价于request A失败，
须按既有条件A入口独立核对，不给物理S/B改判。

离线审计使用封存副本及SQLite immutable/read-only连接；第一次完整重算physical S
耗时过长已主动终止，仅终止本窗口的本地分析进程，没有服务器或采集操作。
这不是新的科学链执行失败，不能将未完成重算写成通过。
随后尝试复用封存physical S的隔离诊断门后续检查也未在本次有界预算内完成，已停止；
未生成non_diagnostic_checks.json或新的A结果。因此这里确认的是原始必要条件，
不声称LEGACY/PER_THREAD逐sync集合及三窗口A计算已完成等价复核。
没有据此新增服务器补证要求；现有warning阻塞独立成立。

## 唯一最小下一步及停止点

停止本attempt资格判定与泛化排查；不重采、不开GUI、不改报告。
下一项仅审查一个本地CPU可验证的进程来源记录方案：在既有外部命令adapter记录
调用用途、解析启动文件（不记录argv）、Popen PID、父PID、单调起止与exit，并与producer身份关联。
这是未来证据设计，不是对本次PID的事后证明，也不自动证明warning局限于子进程。
未来若需处置警告，仍必须同时证明该进程与目标request必要依赖无关且警告作用域可界定；
未满足则继续拒绝。该方案尚未实施，不附服务器命令。
既有限定受控资格不变，Gate7历史PASS、Gate8 NOT_RUN。

## 7.78 补充：独立v0.2反事实与来源实现

上述未完成状态为7.77历史记录。本轮独立版本化诊断已完成，两种默认流模式三sync
（同步表347/348/349）必要集合分别8/1906/3498项，逐项digest相等；全部三窗A字段相等。
完整API验证/correlation索引保留，优化仅在随后扫描排除不相交API及缓存纯函数。
跨窗边界、窗外correlation冲突、混合priority三个独立等价例通过；未经该优化的第一模式
实际A计算亦完成且全部字段一致。冗余第二次原算法停止，不冒称它完成；优化两模式均完成。
封存physical S仅复用为输入容器，request后缀重新恢复，不重判物理S/B。

下表全是反事实候选，单位ns，**不是可信A发布或验收**：

| 窗口 | T | Host | CUDA submit | device | sync residual | unattributed |
|---|---:|---:|---:|---:|---:|---:|
| full_request | 179706613 | 114557354 | 58381832 | 211262 | 1567841 | 4988324 |
| prefill | 104572663 | 68140396 | 31289334 | 211262 | 1537797 | 3393874 |
| decode | 75133950 | 46416958 | 27092498 | 0 | 30044 | 1594450 |

CUDA non-submit=0；device为kernel206398+memop4864、mixed0。各守恒/重叠/窗外审计误差为0。
未归因部分恰为6169条cuKernelGetFunction（4983526ns）及2条cudaStreamIsCapturing（4798ns）；
保留CUDA_API_SEMANTICS_UNRESOLVED，未填Host/residual，未为通过添加语义。
除反事实空diagnostics之外，实际request边界/drain/身份/API/sync/stream等门均通过。
无额外已发现准入阻塞不代表警告安全：外层固定trusted_a=false、diagnostics_still_block=true。
源ZIP/SQLite SHA保持原值，SQLite只读integrity ok；原BLOCKED报告不改。

来源实现及98项CPU验证见[合同0.1](gate8_process_origin_contract_v0_1.md)。它不回溯证明两个旧PID，
不覆盖native，也不能将“git等工具角色已知”单独当作警告局限证明。
本地已可完成的计算/实现收口。唯一剩余证据问题是：明确进程实例关联后，是否有可核验依据
界定这八条警告不影响目标必要CUDA/NVTX依赖。需同时有实例、用途/依赖、具体警告影响范围；
缺任一项继续拒绝。下一方案交协调窗口审核这一证据链，不安排同配置盲目重采或GUI复查。
