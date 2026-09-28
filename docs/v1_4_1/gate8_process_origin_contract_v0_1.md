# 有界子进程来源记录 0.1

2026-09-28，Engineering。实现schema：`exposedpath-adapter-process-origin/0.1.0`。
它记录调用来源，不是observability证书、dependency证据或warning豁免规则。
Measurement Contract、S/A/B、Q0及已有attempt的判定不变。

## 覆盖范围

仅在目标`model-run`入口开启到返回/抛出期间，记录**该Python进程通过
exposedpath.platform_adapter.run_tool创建的子进程**。不替换系统全局Popen，不开启采样、
ETW、轮询或常驻监控；关闭后恢复原有无记录run_tool路径。
第三方Python直接Popen、os/system调用、native库CreateProcess、后代再启动均未覆盖；
不存在记录不能证明不存在进程、活动或依赖。native_process_coverage固定UNKNOWN。
这项工程选择不足以完整识别旧包中的10988/54228，不能回写旧evidence。

## 最小字段与生命周期

新增`diagnostic-entry/subprocess_origin.jsonl`，与同目录started/exit和单ZIP清单关联。
OPEN包含schema、范围、父PID/executable、随机parent_instance_id、clock与未知限制。
parent_instance_id是本次记录会话ID，不伪称OS进程创建时间。
每次调用独立call_id，按STARTING→STARTED→EXITED，或STARTING→START_FAILED记录。
STARTING仅白名单purpose：Git commit/dirty、nvidia-smi query或未分类adapter命令。
STARTED含Popen实际返回PID及解析后launch executable；不宣称已独立查询OS实际映像。
若该映像是launcher，实际执行子孙的身份仍未知，不把Popen PID等同所有后代。
EXITED记录实际returncode；启动失败PID/returncode保持null并仅记异常类型。
不记录完整argv、stdout/stderr、异常消息、环境变量或其值，不复制命令中的凭证。

时间使用父进程PYTHON_PERF_COUNTER_NS；分别是调用前、Popen返回后、退出被观察到时。
不是OS精确出生/退出时间，短命child可能在STARTED落盘之前已退出。
PID+call_id+parent_instance+观测生命周期可区分记录中的PID复用，不能只按PID拼接trace。
与trace关联仍需共同身份/可证明时钟关系；同PID但缺生命周期/命名空间映射时拒绝。

## 错误与读取

每条flush/fsync、序号连续，独立loader校验schema/范围/时钟/父身份/用途/启动退出配对。
缺文件、缺CLOSED、缺EXITED、版本或身份冲突都拒绝。空OPEN/CLOSED只证明本记录器
没有观察到adapter调用；不证明完整进程树为空。没有有效CLOSED不能声称记录完整。
任一次记录写入失败会永久使该记录器失效，即使调用者捕获异常也不能正常闭合。
入口exit.json在来源记录闭合之后写入；闭合失败不得写成功退出。
原执行已有异常时保留原异常；记录故障不伪造成功，原本成功则记录失败导致非零。
timeout维持原run语义和Windows异常输出；仅清理本次已记录child，禁止按名或整树kill。

模型算法、token读回、drain/sync和窗口规则没有改变；记录本身有Host I/O开销，不宣称零开销。
当前预模型身份命令位于request外；若未来某adapter调用落入request，不能忽略记录开销
或把新旧时序当成严格无扰动对照。记录角色仍是Engineering。

## 判断warning不影响目标还缺什么

至少需要同时成立：

1. warning原始globalPid与记录中进程实例可无歧义关联（不能仅靠数字PID）；
2. 该进程实际角色和执行路径足以排除目标request/必要依赖的CUDA/NVTX证据来源；
3. 该具体warning的影响确可局限于这个进程，而非共享collector/buffer或未知范围。

知道“这是git”本身不自动满足后两项，出现可见冲突或不能界定影响仍拒绝。
不得将UNKNOWN改零丢失；目标有事件、外PID无事件、exit0都不是上述三项的替代物。
本模块没有修改任何warning处置函数，没有发布条件A、D或Signature。

## 下一步约束

本地记录/反例及反事实A检查先完成并审查。旧Qwen缺少来源记录，不能由新实现补造。
如后续协调需目标平台补证，最小提案是独立CPU入口仅导入及Git身份检查后退出，
保留该来源记录；不调用model-run、不执行TorchBackend.identity/CUDA/Nsight。
它只能验证目标环境的记录路径，不能证明旧PID角色或解决native来源与warning作用域。
因此当前不默认安排新一轮模型采集；任何真实采集方案须先说明三项证据如何取得。
