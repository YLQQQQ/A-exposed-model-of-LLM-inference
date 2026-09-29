# Gate9 current-stream关系probe 0.1

## 7.94 封存回执：INCONCLUSIVE，尝试关闭（2026-09-29）

原件`.local/transfer/gate9_probe_bee6a25_once.zip`，14183 bytes，SHA256
`02c57ff654a99eb35dc1e280538088ab127bb282f6cec61aff7268a0f81cc5f3`。
本地直接读取ZIP：29文件，CRC、无重复/越界路径、外层28项与其余文件精确覆盖/大小/hash、
内层11项与probe目录精确覆盖全部通过；未解压改写或运行probe。
外层清单SHA256 `c234c5983ae962282c41bb86ecf3a26dbc15843425e4c0ed899b168570ac90ce`。
包内source_hashes与bee6a25 Git字节一致，DLL身份与预声明一致，runtime snapshot与CPU contract相同。
服务器CPU 34 passed/7.41s、compile exit0；这是回传执行证据，不是本轮重跑。

`probe/supervisor.json`及`probe/observation/report.json`：INCONCLUSIVE、error=null、
Popen/目标PID66200一致、timed_out=false、exit2。M TID67204、W TID53976、各handle[0,0]；
before=false、after=true；worker_recorded→query_before→sync_enter→sync_return→query_after完整。
stdout/stderr为空。外层receipt BLOCKED/error描述exit2是预定停止路径，不是目标程序异常；不改该receipt。
checkout日志的PowerShell NativeCommandError包装对应git正常stderr，checkout exit0，不作CUDA故障证据。

解释：before=false只证明查询时尚未完成；到after=true之间，既可能因S等待，也可能独立完成。
缺少反事实约束，不能选择LEGACY/PTDS。墙钟耗时不参与判别。**本次关闭，不延长K、不重跑、不增加同类概率性实验。**
没有本次Nsight trace，也不把旧trace拼接为本次调用轨迹。原件与UNKNOWN保持。
路线裁决见[Gate9当前入口7.94](gate9_platform_assessment_v0_1.md)；以下为原预声明设计，保留历史。

目的仅为目标torch2.6.0+cu124同调用路径的等待关系资格；不是N1、模型、Q0全套或模式自动检测器。
前置为已批准7.92方案；固定一次执行，无重试。执行资格仍待目标平台回执，本地CPU测试不证明CUDA语义。

## 固定独立预期

主线程M、worker W各自调用PyTorch current/default stream，均须native0；线程存活至判别完成。
warmup在W：1-cycle `_sleep`、E.record、E.synchronize；M随后device drain。全部在probe区间外。
不加载模型，不把Qwen窗前工作移入request；这个小程序的probe区间不是模型request。
W：固定50,000,000-cycle `_sleep` K → E.record(W.current_stream) → Host submitted通知 → 等待Host release。
M：收到通知 → E.query(before) → **torch.cuda.current_stream().synchronize() S** → E.query(after)。
之后才E.synchronize清理、release/join。query只观察完成状态，不插入stream等待边；CPU握手不等待GPU。
有限K不作时长阈值、工作量扫描或优化；可能在M判别前已完成，接受INCONCLUSIVE。

独立oracle不调用S/A：
- shared legacy等待关系：先提交K/E属于S的共享默认流前缀；S返回后E应完成。
- independent per-thread关系：S不必等W的K/E；after=false在该关系下允许，在共享等待下不允许。
- before=false、after=false、身份/线程/handle/顺序全部有效：NOT_SHARED_FOR_PROBED_CALL。
- after=true：INCONCLUSIVE（两种关系均可出现）；不能因耗时长或事件完成判LEGACY。
- before=true而after=false、缺记录、异常、身份冲突：BLOCKED；同步/初始化/清理超时45秒，终止记录的直接PID，不重试。

无CUDA event elapsed-time推导，不用墙钟等待时长作为证据；Host时间仅记录边界/顺序。
正式判断函数与CUDA后端分离，测试用独立字面预期与真实Host线程/子进程。
测试故障注入只证明编排/拒绝/日志保全，不是实际CUDA故障资格。

## 与Qwen及Gate9的对应边界

对应的是**计划中的**N1 current_stream().synchronize调用、相同安装二进制、主线程native0及跨线程默认流。
不声称旧Qwen自然D2H一定经过完全相同编译调用点。前后固定c10/torch_cuda hash、目标解释器/site/mask/GPU身份；
不把当前probe反向贴到旧Canonical中补mode，旧物理B不重新变valid。

NOT_SHARED结果有决策价值：排除该固定调用上下文对worker默认流的共享等待，供窄域复用Gate6 PTDS作用域规则审查；
它不是全库或全运行PTDS证书。只有后续N1确实使用此调用、同二进制/设备/线程条件，且保留完整提交及ownership
证据时，才能据此关闭相应Gate9适用命题；不能扩大到混合API、未知incoming依赖或自然D2H的所有调用。
若未来N1改变调用条件，或审查发现probe与拟用路径不一致，则不能关闭缺口。
INCONCLUSIVE/故障：Gate9保持BLOCKED，停止，不再加长K或重复执行追求结果。
任一结果都不自动授Formal；旧A条件性与UNKNOWN/NOT_ASSESSED保持。Gate8不重开。

## 交付与审查

生产adapter用于实际CUDA UUID/PCI核对，启动使用已验证的显式base interpreter + site，
CPU snapshot绑定及Popen/目标PID必须一致。原始stdout/stderr按bytes保存，不做GBK解码。
外层交付脚本先固定commit部署、仅相关CPU测试，再一次CUDA probe；失败即停，所有结果单ZIP。
不运行Nsight，不采集trace，不使用等待时长替代事件状态。目标验证不包括模型或profile环境。
私有固定路径/脚本与bundle hash在忽略的`.local/transfer/`交付说明，不提交机器路径。

源码：`scripts/gate9_stream_probe.py`、`scripts/gate9_stream_probe_run.py`；
CPU测试：`tests/test_gate9_stream_probe.py`及既有target_python回归。
本地先见13个缺实现失败；设备adapter接口和PCI格式反例另见失败后修复。
实际启动/字节保全/超时及Torch后端调用顺序测试保留；不是独立第三方审查。
