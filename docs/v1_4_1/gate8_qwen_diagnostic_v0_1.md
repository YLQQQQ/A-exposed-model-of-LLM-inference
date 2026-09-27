# Gate8 Qwen 单次 Engineering 诊断 v0.1

仅可观测性诊断：`NOT_QUALIFIED`，Gate8 `NOT_RUN`，不运行A/B/D科学发布。替代继续安装索源，不替代Q0或真实A资格。

## 固定入口与产物

- `python -m exposedpath.gate8_diagnostic prepare`：显式commit、模型目录、既有模型CSV及其SHA、既有32-token prompt及SHA、physical GPU、新output；检查当前Git/clean，引用历史模型内容hash并核当前文件集合/大小，不重新读取3GB权重。缺失或冲突拒绝。最小CUDA identity probe核physical UUID与logical0；不是zero GPU interaction，但无模型加载。
- 新manifest与preflight/prompt副本位于独立prepared目录；run_id新生成，Engineering、eager、FP16、argmax、batch1、32/2、warmup1/request1。配置加载前attention为UNKNOWN，不能把共享manifest默认sdpa当实际值。
- `python -m exposedpath.gate8_diagnostic run`：执行前再次检查Git/mask/GPU预检身份、代码根、runner字节、输入hash、固定执行字段；调用原Gate8 producer，保留stage/drain/共同completion及request ledger。setup观察仅记录加载后config，不增加CUDA同步、不改变stream或attention。
- 旧load_model允许fallback的默认值保留；新诊断显式禁fallback，第一次加载异常即结束，不二次from_pretrained。失败/earlyEOS产物保留INCOMPLETE，不重试。
- 产物：输入字节副本、loaded_config、producer receipt、pass identity、host boundaries、drain/stage ledger、diagnostic report。配置名不是native SDPA kernel选择证明；native mode、迟发及丢失仍UNKNOWN。模型内容是历史hash参考，revision未知不补造。

## 单次采集与停止

`scripts/gate8_diagnostic_collect.py`必须显式`--execute-engineering-diagnostic`，参数固定checkout venv、绝对Nsight路径、prepared、新output。
使用cuda,nvtx / sample=none / cpuctxsw=none / memory-usage=false / process-tree / isr=false，不启用CPU采样、backtrace、stats或覆盖。
平台修订v0.1.1（7.60）：目标安装UserGuide Windows条款规定kill=true/false；Linux信号名sigkill不适用于Windows。本入口在Windows使用kill=true，非Windows保留sigkill的argv规则但不声明Linux平台已验证。120秒collection及300秒外层上限不变。旧v0.1误引用Linux条款已造成服务器参数解析拒绝；不得将旧BLOCKED追认成功。未知/不支持选项失败即停止，不fallback。

外层300秒等待只终止本次记录的Nsight PID；**不保证其后代或内核已经退出**，超时标UNKNOWN_STOP_AND_INSPECT_NO_RETRY，不export、不重采，人工检查残留。Nsight自身120秒终止策略不能保证驱动/系统挂死可恢复。历史BugCheck 0x133根因未证，短运行不构成系统安全保证。

启动前及取得PID后落盘命令/状态；落盘异常也管理已启动进程，不能保证断电/系统BugCheck下最后写入留存。
collection exit0还须producer COMPLETE；否则停止。之后仅一次已有限时export（max_attempts=1）；REP稳定hash→SQLite integrity/schema→lineage保留。无科学analyzer调用。export失败保留partial，不retry。

## 交付与验收边界

静态部署与GPU执行分开，后者需协调窗口核对静态原件、用户明确单次风险授权。固定checkout正常快进/脱离部署，禁止自动追随main。
回传新prepared目录、整个collection目录与操作日志；包含命令/PID/退出、REP/SQLite/export report、producer所有产物和NOT_QUALIFIED报告。原始证据不改、不覆盖旧attempt，不提交Git。

本地CPU doubles只验证入口与文件合同；受影响Q0、真实默认流/A来源、范围内缺证据影响仍未合格。无论本次收集成功与否，Gate8不自动PASS。一次诊断后只读检查目标request三个边界与全部sync/活动/ownership缺口，不自动启动第二次实验。
