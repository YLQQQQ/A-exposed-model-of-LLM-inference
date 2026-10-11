# w11与Formal G512完成路径对照 0.1

2026-10-11；`G13-W11-EXECUTION-COMPARISON/0.1`。仅解释已有实物；Gate13限定PASS保持，Gate14 NOT_RUN。未改runner、冻结S/A/B、Formal统计或数据角色，未采集新样本。

## 1. 已确定的差异

**这份w11不是4090实验。** `nsys_results/w11_p512_b4_o16.nsys-rep`的应用日志（导出`StringIds.id=18`）明确输出RTX 6000 Ada Generation、torch 2.5.1+cu121、CUDA 12.1、transformers 5.13.0。目标PID57540的CUDA inventory把logical0映射到inventory GPU3；该GPU为RTX 6000 Ada，活动的deviceId0不是inventory编号0。不能从同名workload或inventory里有4090推断实际在4090执行。

Raw启动实参和应用日志共同声明：Qwen2.5-1.5B-Instruct目录、synthetic input512、batch4、output16、warmup3、repeat5、`--streaming`。五个request、每窗15个decode-step及每request16个device-wide sync可观察。ArgMax kernel gridX4与该声明一致，但没有固定输入digest、模型内容/revision锁或逐值Host token证据；backend和实际执行源码字节仍未知。不能授新版本或Formal资格。

| 对照项 | 本份w11实物／旧入口 | Formal G512（已有六block） |
|---|---|---|
| 平台/软件 | RTX 6000 Ada、torch2.5.1/cu121、transformers5.13.0；collector2025.6.3.541 | RTX4090、torch2.6.0/cu124、transformers5.17.0；collector2026.2.1 |
| 输入/输出 | synthetic512/b4/o16；5 request，旧输入/输出digest缺失 | 冻结输入512/b1/o2、逐值token和内容digest；6独立block |
| argmax之后 | 取cache→直接device-wide synchronize；没有每token `.cpu()`/Host值提取 | 取cache→structured helper准备/range→`.cpu()`内部copy→stream sync→Host值→完成记录/point |
| 同步前completion | Prefill初段有1-byte D2H/stream sync；不是末尾token完成；decode-step1末尾无copy | 每token末尾有8-byte D2H；对应stream sync入口前已完成 |
| “streaming”含义 | flag使每decode-step增加device-wide sync；不执行网络发送，token仍在GPU | host-readable token-ready；也没有网络发送 |
| 边界 | legacy NVTX range与Host计时；没有D1原始point/ledger | host性能完成点与trace D1投影窗分别承载，clock不混用 |
| Device wait口径 | 旧pending-only筛选后，sync与候选活动union交集；不是整个sync时长 | 已获资格的必要后缀／完整物理W对应当前union；G1仅投影A，不发布自然完整B |

这些同时改变了平台、软件、batch、输出步数、输入构造和完成路径，**不能定量归因于输入负载或copy API单一因素**。看到旧长sync的事实成立；当前小Device wait也不因此被证明是实现错误。

## 2. 原脚本与旧计算口径的绑定强度

找到旧入口[bench_eager.py](../../bench_eager.py)、launcher [single](../../scripts/run_nsys_single.ps1)/[matrix](../../scripts/run_nsys_matrix.ps1)、[legacy analyzer](../../analysis/exposed_accounting.py)及[旧汇总器](../../analysis/summarize_matrix.py)。Git首提交`3a64db2d095b43a6dda2e6a9a2bd189185989b6f`（2026-07-17）和Prototype tag `abab013c5483109007ab5a2a232438d46bbaf02b`（2026-09-02）保存这些原有代码；不是本轮新写复原脚本。

两版本bench差异仅弃用说明；analyzer差异仅v3 NVTX身份/phase接入，旧legacy W查询和A计算不变。既有交付快照`dist/exposedpath_v3_pilot_deploy/payload/bench_eager.py`及`analysis/exposed_accounting.py`与tag原字节一致，SHA256分别为`210580fc87edc298bea61a578945d2416c7f98cb104c339356b347b5a246a448`、`4348ac1e74e681cb9c91b471c6c582880cb1e5b886ab1e8440bbae5c9d4dd293`。Raw命令指向同名bench_eager，观测顺序与这些源代码一致；**采集早于Git首提交，没有当时源码hash，不能证明精确执行了其中某commit**。

旧v2 `_query_wait_set`按`submit_end <= sync.start`且`activity.end > sync.start`只保留pending活动；空集合判NO_PENDING_ACTIVITY。`compute_a_layer`累积`sync interval ∩ union(候选GPU活动interval)`，sync剩余进入旧residual。因而它既不是sync全长，也不是“所有GPU活动重叠即wait”；但它不是当前完整W/ownership/validity合同，尤其不能据此恢复完整hidden progress。简单同流case内，已完成前缀不与sync相交，A的该局部交集可相同；不能把旧S差异一概说成wait差异的原因。

每次旧比例为`A_device_wait/T_phase`；matrix汇总取这些逐次比例的mean。analyzer `A_summary`另有mean预算/mean窗口比例，不与matrix字段混用。当前[总预算表](gate13_a_budget_summary_v0_1.csv)采用`sum(A)/sum(T)`并保留[逐次比例](gate13_all_block_a_proportions_v0_1.csv)。Prefill/Decode/Request分母必须分别说明。

[6000旧汇总](../../results/matrix_summary6000.json)同名w11的Prefill/Decode/Request比例均值是**39.890%／12.044%／15.474%**，不是[4090汇总](../../results/matrix_summary4090.json)的**22.586%／1.322%／3.768%**。本REP五个Prefill NVTX实值为271.202353、245.889004、246.835048、253.746712、253.397335ms；均值254.2140904ms，与6000旧汇总254.2140ms一致至其舍入精度。Decode均值1809.5266096ms；Request实值均值2063.7814756ms与旧汇总2063.7772ms差0.0042756ms。旧摘要无REP hash、source_root亦非完全同一原路径，故日志/时间高度相符不替代Raw hash绑定；不把其39.89%作为本轮重新计算的新A。

## 3. 少量真实时序

单位ms；各自相对其request起点，不能跨文件比较绝对时间。旧行来自新导出副本；当前行直接复用[已核验token时序](gate13_token_completion_timing_v0_1.csv)和[原API解释](gate13_cuda_api_storage_review_v0_1.md)。

| 原记录 | argmax提交API结束 | argmax GPU起止／最后设备完成 | copy API／D2H | 末尾sync起止 | 阶段／step边界 |
|---|---:|---|---|---|---|
| w11 request1 Prefill | 93.763376 | 270.833191～271.050822 | 末尾无copy；初段见下文 | device 93.804097～271.153139 | Prefill结束271.204396 |
| w11 request1 decode-step1 | 363.017455 | 395.686424～395.776919 | 本step无copy/D2H | device 363.118065～395.806661 | step结束395.824768 |
| G512 block1 token0 | 83.530640 | 88.608445～88.687869 | copy86.897104～88.771602；D2H88.689277～88.689821 | stream88.772503～88.808056 | Prefill point91.390771 |
| G512 block1 token1 | 159.908546 | argmax结束160.781253 | copy162.745139～163.094461；D2H163.081811～163.082227 | stream163.095252～163.117906 | Request point165.190699 |

代表性时间线：

```text
w11：argmax提交结束93.763 → device-sync入口93.804
        [GPU必要候选继续推进，最后ArgMax完成271.051] → sync返回271.153
G512：argmax提交结束83.531 → helper范围86.824 → copy入口86.897
        [ArgMax完成88.688，D2H完成88.690] → copy返回88.772
        → stream-sync入口88.773 → 返回88.808 → Host token/完成记录 → point91.391
```

旧Prefill同步runtime80423/correlation988994、physical354（CONTEXT_SYNCHRONIZE）、目标PID57540/TID51896；末端ArgMax kernel78928/correlation988988/context1/stream7。sync全长**177.349042ms**，独立只读筛选同进程/同context先行且仍pending的1190个观测活动，其与sync的union交集**112.633243ms**；入口至最后完成**177.246725ms**。三个量不同，不把后者全填成wait。decode-step1 runtime82016/correlation1008694、physical355，446个pending观测候选的交集16.157432ms，sync全长32.688596ms。这些是旧规则的两次局部解释算术，**不是新版合格W/B或旧完整A复算**。

旧Prefill初段runtime78581/correlation965505 copy0.901568～0.913015ms；1-byte D2H346在1.025252～1.025860ms；stream sync78582/correlation965506在0.913446～1.029600ms。该小copy/sync早于主要forward/argmax，不能拿它证明末尾token已完成；实际末端GPU活动仍持续到271.050822ms。decode-step1没有同期copy或先行sync。全份观测kernel都在context1/stream7，但这不证明所有未观测依赖不存在。

G512 token0 copy runtime37815/correlation197682、D2H347；sync runtime37816/correlation197683、physical354/context1/stream7。最后D2H在sync入口前82.682µs结束，现有合格投影后缀的sync wait为0；token1提前13.025µs，也为0。**D2H完成不等于`.cpu()`已返回**：目标PyTorch2.6实际header和Copy.cu路径是helper内部`cudaMemcpyAsync → cudaStreamSynchronize`，之后才取Host值。API内部可能包含等待，但本次Raw没有足够driver/native-stack证据分离它，不新增分类。

旧最后提交→sync入口只有40.721µs/100.610µs；当前token0最后提交→helper range有3.293756ms，再经历copy包络。这提供了不同的设备推进时机，但没有相同平台/输入/边界的因果对照，不能量化各因素贡献。当前完成后point的2.4938ms准备延迟是另一段，不能算作同步前准备或GPU等待。

## 4. 原因、未决解释与最小后续问题

- **已证实**：不是同一平台/负载/完成路径；旧设备sync入口时末尾GPU工作未完成，当前末尾stream sync入口时token D2H已经完成。高/低局部wait与Raw一致；无证据表明当前sync分类或计算错误。
- **仍可能**：较大batch/不同软件与输入、同步前Host推进机会、copy API内部阻塞共同改变完成位置。不能认定cudaMemcpyAsync是“主要原因”，也不能用整个API或重叠补造等待。
- **排除**：该REP实际GPU=4090、末尾每步8-byte Host token读取、两者是只改变输入负载的对照、旧wait=整个sync时长、unattributed0=所有内部等待已解释；这些均不成立。
- **若以后另行批准一个实验**：先问“在同一现平台/输入下，显式device completion在D2H之前，与自然host-readable路径相比，必要设备完成会暴露在哪个调用区间？”这是独立Engineering completion-path对照，会改变执行合同，不能当G1自然结果或当前Formal续采。本轮不设计新等待类别、不实现、不采集，也不以提高wait比例为目标；较重batch候选暂不抢在路径问题之前。

## 5. 取证动作与清理回执边界

本轮只在新忽略诊断目录复制原REP并离线export，工具2026.1.1.204-261137176666v0，exit0、1.609s。原件/副本导出前后SHA256均`981db025cab3e4a43a099f11ae200d424d2f101186970490d9c33c2be5852e13`。新SQLite27336704 bytes，SHA256 `adee4a45f9a04b450977c282ece01f92ebd380b19ab8941d0d511a58e918e81d`；与历史export报告不是同一个文件hash，明确为本轮新导出。未重新执行完整analyzer或Formal统计，未运行profile/模型/CUDA/服务器。

用户称服务器清理回执已回传，但截至本地审查，在transfer/server_receipts及既有交接入口未找到服务器原`cleanup_receipt.json`；同名测试fixture不能替代。**实际清理数量/空间尚未核验**，41820242784 bytes/30文件仍只是已有候选，不能写成实际释放。已请求准确本地定位；不再清理其他Gate、不重扫服务器。新回执到达后只核对其字节hash、30目标/归档绑定、删除状态及释放算术，不再执行删除或原数据扫描。
