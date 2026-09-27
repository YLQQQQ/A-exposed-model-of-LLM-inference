# Qwen 单次诊断只读审计 v0.1

2026-09-27；Engineering / NOT_QUALIFIED。执行commit为
`35b5bffe4f771f9783d10fdcdb8260d056902bdd`。本地仅读取回传ZIP及其内存SQLite，
不运行profile/export/模型，不修改原件，不授予Q0或Gate8资格。

## 身份与文件链

ZIP 1,434,073 bytes，SHA256
`adb6a88d9b14170cf40353b317ffba18998b3c28ac2d2c50160bc2649893bd5a`。
27源文件加清单共28项，逐项大小/SHA、CRC通过；输入三副本字节一致，producer
receipt四文件hash一致。REP SHA256为
`981537c3db8799dbfe5ffa88c7e113fd6df716d60533e0523d59ae2ea6406ed1`；
canonical与attempt1 SQLite同hash
`25e7bd0e79597744f3485c1eb155621e0d93491b034ccb7756dc9f312d5e0145`，
1,863,680 bytes，只读integrity检查ok。一次collection exit0、28.516s；一次export
exit0、0.234s，无timeout/retry。报告仍明确NOT_QUALIFIED/NOT_ASSESSED。

run=`run-20260927T094130Z-cc460baf`，wmpc=`wmpc-9f1e23faccf92c93`，pass1，
diagnostic-1；PID50660，measured request-0/repeat0，warmup另列。两者COMPLETE，
measured 2/2 tokens、无early EOS。不是Pass0/Pass1配对实验或可靠性统计。
runner报告hash `7ed08a068915b8bf765d3ce8a674b470be011b200dc2cfef8cb88eedd90bf94a`
等于该commit源码CRLF表示；本地LF字节不同，不冒称收到服务器源码原件。
模型沿用历史内容清单并核当前大小/集合，10输入文件与13缓存辅助文件分开；
revision UNKNOWN，未复算权重。loaded config为sdpa/use_cache=true，native backend UNKNOWN。

## 三窗与同步的直接观察

`NVTX_EVENTS` rowid1/2/3为同身份、同globalTid的三个point，trace ns依次为
20995361790、21085953944、21160901865。按D1公式，marker窗口为：
request 165540075 ns；prefill 90592154 ns；decode 74947921 ns。
这些是共同trace clock的窗口，不是已合格A归属或无扰动延迟。
Host observed→before marker间隔分别459900/414200/419800 ns，marker调用
18500/33700/59000 ns；不将host与trace原点直接相减，不宣称观测误差为零。

drain NVTX row7包含Runtime row17430的cudaDeviceSynchronize，correlation61540、
return0，结束20994877037，早于request point。setup/warmup/measured三段range及ledger
齐全；drain只证明先行完成，不能单独证明无未来迟发工作。

| 阶段 | Runtime row / correlation | API区间(ns) | 对应D2H |
|---|---|---|---|
| prefill内部 | 17440 / 61647 | 20996393139–20996484466 | correlation61646，1 byte |
| token0 | 19142 / 90859 | 21085435931–21085463331 | correlation90858，8 bytes |
| token1 | 20736 / 116224 | 21160422320–21160447157 | correlation116223，8 bytes |

三条cudaStreamSynchronize均return0，分别关联CUPTI sync row347/348/349，
context1/stream7/activity device0；不能仅凭字节数断定内部Python调用点。
目标窗口观察到3492 kernel、3 copy、3 memset，均此PID/context/stream/device；
9672 Runtime行均来自同globalTid，返回码无非零。每项GPU活动存在同进程Runtime
correlation，未观察到活动跨request首尾或prefill/decode界。以上不等于完整W(s)、
唯一terminal或零丢失证明，也未把API/activity时长当exposure。

## 设备、诊断与尚未取得的资格

manifest/preflight目标physical3/logical0；SQLite CUDA_DEVICE的PID50660/cudaId0
指向gpuId2，GPU inventory id2的UUID和PCI匹配目标；activity device0沿进程CUDA
映射联结，不以0=physical/inventory推断。CONTEXT_INFO明确PID50660/context1的
nullStreamId=7；stream7确为默认/null stream，但这不确定每次调用的legacy/PTDS
语义或完整依赖闭包。当前synthetic-only入口的DEFAULT_STREAM_NOT_SUPPORTED仍有效，
不能删除检查或把模型换stream以掩盖此真实准入缺口。

24条DIAGNOSTIC_EVENT中，目标PID报告13 NVTX、28804 CUDA events；另有CUPTI
produced计数29682/29687，计数层级/时点不同，不能相减解释为丢失数量。
“Not all NVTX events might have been collected”及CUDA未正常启动警告关联
PID65108/65272而非目标50660；保留其范围，不能删除，也不能仅因不同PID便证明
其对目标必要依赖无影响。目标注入成功/计数非零/SQLite完整均不使dropped UNKNOWN变零。

当前能确认的是三个已观察sync及活动关联。不能发布supported/B-valid覆盖比例：
API识别不等于依赖scope受支持，分母完整性和B资格未通过。缺少独立真实device/source
准入与目标依赖影响证明；pass identity的raw/device mapping hash为采集前null，后续
须在独立派生receipt中绑定，不回写producer。当前没有合格A、B或D/Signature产物。

## 下一项最小工作

本地对本包三个sync形成逐项target-scope准入/拒绝清单：成功drain前缀上界、
request后缀提交与必要依赖、默认流条件等价所需条件、跨进程警告影响范围；
只能按已批准合同给出受证结论。不能闭合的边必须具体保留UNKNOWN，不再要求统一
全capture认证、不继续无界索源、不盲重采。新Q0增量仍须独立oracle验证，不能以
此真实诊断替代。服务器暂不操作；Gate7 PASS，新Q0/Gate8 NOT_RUN。
后续回传统一一个包含prepared/collection/logs及完整清单的ZIP，不重复三份副本。
