# Gate8 条件性A与最小配对交付 0.1

2026-09-28，7.85。用户明确授权：暂按四条外进程warning不影响目标request的假设推进其余Engineering工作。
**不是作用域证明，不修订正式warning门，不授予原标准Gate8 PASS。** 研究设计v7.1、Pre-Pilot协议v2.1及
route-a-execution/0.2仍为背景；无Formal资格变化、无历史追认。此轮只本地实现/CPU验证/交付。

## 1. 独立条件性派生，不是第二套分析器

假设版本`FOUR_OTHER_PROCESS_WARNINGS_NO_TARGET_IMPACT/0.1`；输出版本`exposedpath-conditional-a/0.1.0`。
只接受该Nsight已支持版本、同一明确OTHER_PROCESS global PID下、各一次的四条精确消息，
source=3/severity=2/timestampType=2。消息为：

- `Not all NVTX events might have been collected.`
- `No NVTX events collected. Does the process use NVTX?`
- `CUDA profiling might have not been started correctly.`
- `No CUDA events collected. Does the process use CUDA?`

先走不变的正式process/load；正式拒绝原因必须仅为诊断影响未界定，再显式进入
`python -m exposedpath_v141.gate8_warning_assumption`，指定原formal/input/execution及全新output。
新目录复制已有Canonical/projection/diagnostic依赖，重新核源hash并复用同一`_request`、S恢复及A函数。
只从有效诊断门输入移出这四条；原diagnostic_dispositions和全部源记录不变，另存假设依据、原rowid/hash。
未知/目标PID、新型或额外warning、未知通知、目标零事件冲突仍停止；缺身份/边界/drain/correlation/
stream/配置等仍由原检查拒绝。其他失败不得一起绕过。局部分类gap仍进unattributed，不改Host/residual。

成功仅标`CONDITIONAL_A_ONLY_NOT_ACCEPTED`、trusted_a=false、scope_proven=false；其余仍BLOCKED。
measurement_validity=NOT_ASSESSED、dropped=UNKNOWN、Gate8/Q0=NOT_RUN，D/Signature关闭。
有不合格窗口时不能称“其余条件均完成”。输入和旧formal结果逐字节保持；partial目录不发布完成结果。
历史Qwen不重判。本轮不运行旧Raw的条件分析；待新配对完整包回传后统一离线审查。

## 2. 一次配对合同与计时

新增manifest `engineering_pair={schema_version:gate8-engineering-pair/0.1,pair_id,pass_id}`，在prepare时声明。
各pass有独立run/manifest/一次性预检nonce；同pair_id不是复用旧receipt。默认非pair入口仍pass1。
Qwen2.5-1.5B-Instruct、固定32输入/2输出、batch1、fp16、greedy、eager、配置SDPA、use_cache，
每pass warmup1/repeat1，physical3/logical0及既定UUID/PCI；模型清单与prompt digest固定于机器交付。
执行顺序固定pass0→pass1，不重试、不扫描、不更改同步或模型行为。

两次均显式目标解释器`-I -S`及site路径，采用同一model-run异常/退出持久化入口；Git/nvidia-smi先于目标启动，
目标仍直接核身份/内容/native设备。pass0使用runner已有禁NVTX路径，无Nsight；pass1保持原minimal profile。
加载、warmup和成功drain在计时窗外；host ledger的`host_observed_ns`而非marker后的时间用于两pass比较：

`T_request=t_last-t_start; T_prefill=t_first-t_start; T_decode=t_last-t_first`。
时钟均为进程内PYTHON_PERF_COUNTER_NS，不作跨进程时间戳相减，也不将host时间偷换为A的trace时钟。
每窗`delta=T_pass1-T_pass0`，`relative_delta=delta/T_pass0`；零分母为null，负差保留，不截零。
这些是一次配对的profile/插桩扰动加运行波动观察，不能单独识别纯profiler因果开销、统计稳定性或Pilot阈值。
不把启动/加载/cleanup/export墙钟计入request；保留marker诊断，不假设零开销。
核对输入/模型清单/代码/配置/目标snapshot/实际设备及完整producer、drain、exit、预检链。
现producer记录输出数量/EOS而非token值序列，报告明确`output_token_value_parity=NOT_RECORDED_COUNT_ONLY`，
不得称输出token字节一致；本轮没有为此改变冻结producer schema或增加一个资格前置。

## 3. 两阶段执行与一个汇总回传

固定bundle前置为服务器db9f028，包含f491d6e的Git binary修复及本次最小接线。
完整固定机器路径、commit、bundle/script hash在忽略的本机交付索引，不提交私有路径。
公共driver为`scripts/gate8_pair_server.ps1`，机器包装器固化所有参数；不跟随远端main。

1. Static：校验bundle、verify/fetch/detach、相关CPU定向回归及改动语法/diff检查。CUDA mask=-1，无模型/Nsight。
   失败停止；成功只STATIC_PASS。回传一个static ZIP，由协调窗口审查，不自动进入Pair。
2. Pair：显式独立授权开关＋固定批次STATIC_PASS及文件hash；不再重复CPU或全量。检查必要环境/输入，
   分别新prepare/pass0/pass1；baseline任意失败不profile，采集/导出失败不重试。
   正式A保留；若仅四warning，服务器只检查条件分析适用性，不将候选A当就绪。
   汇总host计时，然后单一完整pair ZIP包含Static与Pair全部证据，回传后本地统一条件性A审查。

每次输出目录、清单和ZIP禁止覆盖。先快照文件列表再生成清单，清单自身不进入自己的输入；
最终pair ZIP也包含原static索引和CPU记录。两个审查时点各一个ZIP，不零散回传、不覆盖先前static ZIP。
timeout/子进程存活不明则停止打包，保留目录；不按进程名kill。所有正常失败仍保留异常与退出记录。

## 4. 收尾判据和停点

回传一次性核：目标平台Git读取、显式解释器/实际CUDA身份/配置、三窗口/成功drain/全部必要同步、
正式与条件结果并列、unattributed、同合同开销、存储/失败/排除与清单。复用限定受控资格，不能据CPU/mock授新Q0。
新型诊断或任一其他冲突停止；四warning假设不是通用豁免。只有其余项均有证据才能记录
“其余退出条件已完成，仅warning作用域假设待决”；原标准Gate8仍按实际依据，不自动PASS。
厂商答复不是执行前置；本次交付不承诺一定通过。Gate7历史PASS保持。

## 5. 本地验证与审查

先RED后最小实现：条件入口缺失、pass0身份未贯穿、非法pair声明、等边界/零分母、
双pass同错设备及warmup越界均有独立反例。相关9文件141 passed；最终pair/delivery25 passed，
Python语法、diff-check、PowerShell5.1解析通过。合成trace/CPU模型与设备替身，不是目标机或Nsight证明。
逐项审查默认正式诊断路径、原S/A/B调用、原件不写、独立派生状态、直接解释器argv、
CPU失败授权门及模型前/后身份链。没有生产runner、冻结schema或历史Q0改动。
新版本仍须交付后目标平台相关CPU复验；不能因本地结果将其余退出条件提前勾选。
