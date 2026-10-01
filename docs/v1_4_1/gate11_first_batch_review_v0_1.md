# Gate11 首批限定 Pilot 审查 0.1

2026-10-01；审查版本 `G11-FIRST-BATCH-REVIEW/0.1`。

**结论：首批数据可用于限定政策估计；Gate11 BLOCKED，未满足全部 Freeze 输入条件。**
执行链和本批支持域审查通过，不是测量科学有效性、稳定性或信息增益通过。
原批次 `FIRST_BATCH_COMPLETE_STOP_FOR_REVIEW` / `gate11=NOT_RUN` 不改写。
本次没有服务器、模型、CUDA/Nsight、export、完整 analyzer/Q0 或仓库测试执行，也没有业务代码修改。

## 依据和证据身份

Material Passport：ExposedPath Pilot 结果审查；统计状态 **ANALYZED**，不是新实验复现。
依据当前研究设计 v7.1 §2.3.9/3.2.1、实验协议 v2.1 的运行政策与数据角色要求，以及用户批准的
[G11-LIMITED-PILOT/0.1](gate11_pilot_contract_v0_1.md) / [限定计划](gate10_workload_plan_v0_1.md#gate11-local-preparation)。两份 DOCX 仍是 Pre-Pilot/研究依据，不是 Protocol Freeze；保留用户已有修改。

- 执行 commit：`221f46c3f97749396653f16f61b01eb6c6aeeafc`；本审查的文档提交另记，不冒充执行版本。
- 原包 `gate11_221f46c3f977_pilot.zip`，337537738 bytes；SHA256 `85871ae289fcab1731b4e33a7f43e80d21b75b7a32bd5c0b98af3660927612ac`。
- 清单 SHA256 `cea36179a2b58491c77fa83392051aba981247b6d26379083fcbe2e4a7f6510a`；1745 项、ZIP 1746 文件（含清单）。完整 CRC/全部 hash/覆盖由协调窗口核验回传；本窗口独立核 ZIP/清单身份及本次实际消费的关键文件，未重复全包扫描。
- 原值与证据索引：[机器汇总](gate11_first_batch_summary_v0_1.json)、[30 次运行 CSV](gate11_first_batch_durations_v0_1.csv)。JSON 的 `runs.source` / `profile_evidence` 给出包内相对定位和 manifest/REP/SQLite/domain hash。私有路径与只读审查脚本保存在忽略的本地交接，不提交 Raw。
- 本地增量目录 `gate11_first_batch_review_v0_1`：流式选择原 domain 字段和目标同步，不加载约 10.7GB 派生文件到内存；读取原 SQLite 的内存只读副本。独立核 Raw→Canonical 字段/记录数、FIFO 必要集合、terminal 和区间算术，没有调用被测 S/A/B 函数。不是重新生成整套分析。

## 实际资格与测量链

30 个独立 run / 15 pair / 3 block，固定组序及相邻 pass 次序吻合；目标入口、driver 均 exit0，无超时/early EOS/排除/retry。静态副本原日志 **63 passed / 84.60s** 是服务器成绩，不是本窗口重跑。
manifest 执行前 Pilot 声明→producer/pass ledger→执行/token receipt→Canonical/投影→domain→配对引用一致；代码 clean、源码字节、prompt、模型内容 inventory、实际 fp16/eager/SDPA/cache/greedy/batch1、warmup1/repeat1、mask/设备和隔离预检 final PASS 保持。
模型 revision 仍 UNKNOWN，以固定内容 hash 绑定，不补推 revision。

32 输入的 G32/N1 各组各 pass 输出逐值 `[[463],[2529]]`；G512 为 `[[29184],[6556]]`。测量输入分别实际 32/512，输出实际 2；不能把 warmup ledger 的目标 token 赋值当实测输出。
Pass0 关闭通用观测 NVTX，但 N1 的包装、marker、实际 V16 同步、专用流/anchor、drain 和 host-readable completion 保留；这是允许差异，不是两 pass 指令流完全相同。
N0 实际干预 0；Nm/N16 每次 measured decode 第16层后 marker 1，实际干预同步分别 0/1，在两个 pass 的 producer 中一致；Pass1 另以 Raw 区间、成功 API 和物理 sync/correlation 核实。

- 两 pass 的三个 host 时点严格递增，加载/warmup/成功 drain 窗外，截止最后一个已 host-readable token；窗外持久化复用原 token 值，不新增同步/传输。30 次 request 的三窗口公式成立。
- 15 profile / **45 A 窗口**：Raw 锚点、同 trace clock 的 Request/Prefill/Decode 投影吻合；五类及子类独立区间核算、互斥/守恒、Request=Prefill+Decode 成立，unattributed 均 0。没有用守恒替代成员/归属核验。
- G1 的 **18 个 A-only 同步交集**，逐 request 的 drain 前缀、后缀实际提交、成员及依赖边，两默认模式的适用证明均匹配独立 Raw 核查；不发布自然默认流完整物理 S/B。
- N1 的 **30 个物理同步**：每 N0/Nm 3、N16 4。完整显式 nonblocking 流 FIFO 集合、唯一 terminal、成功/唯一映射、实际 scope 和来源一致；各同步 B_VALID。W 大小为 8/1906/3498，V16 干预为 2814，包含已完成前缀；不是仅选 overlap。每 request 内部同步 1 为 RAW_PHYSICAL，token-ready 2 为 STRUCTURED，V16 额外干预 1 为 STRUCTURED。独立复算各 B 的 hidden/exposed union、terminal 前/重叠及 return-tail；不跨同步相加。
- 各 profile 保留同类外进程四条 warning，共 60 条，依 `G8-WARNING-EVIDENCE/0.1` 官方回传依据处置，目标 CUDA/NVTX 实物存在，原记录及来源保留；未发现新型/目标冲突。没有据此宣称 dropped=0、排除未记录依赖或全会话绝对完整。

边界 marker 的 host 观测到发 marker 之间延迟 **0.9246–2.6230ms**，marker 调用区间 **0.0002–0.3264ms**。
P1 trace 窗口长度相对同 run host 窗口长度的差：Request −0.413620～+0.839884ms；Prefill −0.435544～+1.496060ms；Decode −0.656176～+0.814761ms。
这里只比较各自 clock 内的长度，不相减跨 clock 的绝对时间；不是 clock 校准或误差上界。D1 观测延迟不是零，Formal 所需分辨率/容差仍待政策确定。

## 原值、组序和配对差

单位 ms，三元组顺序 **Request / Prefill / Decode**；表中四舍五入到 0.001ms，CSV/JSON 保留整数 ns。
每条件只有 3 对，重复单位是 run/pair/block，不是 token/kernel/sync；独立进程不保证统计独立。

| block:位置 / 条件 | pass 顺序 | Pass0 R/P/D | Pass1 R/P/D | P1−P0 R/P/D | Request 相对差 |
|---|---|---|---|---|---|
| 1:1 G32 | 0→1 | 223.732/143.597/80.135 | 264.512/162.244/102.268 | 40.780/18.647/22.134 | +18.23% |
| 1:2 N0 | 1→0 | 286.797/158.311/128.486 | 234.862/125.217/109.644 | −51.935/−33.094/−18.842 | −18.11% |
| 1:3 Nm | 0→1 | 208.504/130.604/77.901 | 209.160/112.661/96.499 | 0.656/−17.943/18.598 | +0.31% |
| 1:4 N16 | 1→0 | 233.562/153.382/80.180 | 219.983/117.172/102.811 | −13.579/−36.211/22.632 | −5.81% |
| 1:5 G512 | 0→1 | 184.260/104.332/79.928 | 265.031/164.258/100.773 | 80.771/59.926/20.845 | +43.84% |
| 2:1 G512 | 1→0 | 203.280/127.428/75.852 | 278.304/181.540/96.764 | 75.023/54.111/20.912 | +36.91% |
| 2:2 Nm | 0→1 | 214.309/135.021/79.288 | 227.546/125.658/101.888 | 13.237/−9.362/22.600 | +6.18% |
| 2:3 N16 | 1→0 | 162.731/83.232/79.499 | 327.321/191.009/136.312 | 164.590/107.777/56.813 | +101.14% |
| 2:4 N0 | 0→1 | 175.314/99.163/76.152 | 257.755/138.639/119.116 | 82.441/39.476/42.965 | +47.02% |
| 2:5 G32 | 1→0 | 203.999/128.222/75.778 | 223.624/122.435/101.189 | 19.625/−5.787/25.411 | +9.62% |
| 3:1 G32 | 0→1 | 172.766/96.880/75.886 | 258.860/152.159/106.701 | 86.094/55.279/30.815 | +49.83% |
| 3:2 N16 | 1→0 | 185.617/101.005/84.612 | 234.749/127.564/107.185 | 49.132/26.559/22.573 | +26.47% |
| 3:3 N0 | 0→1 | 255.520/184.948/70.572 | 253.272/154.654/98.617 | −2.249/−30.294/28.045 | −0.88% |
| 3:4 Nm | 1→0 | 252.907/169.034/83.873 | 229.268/121.201/108.067 | −23.639/−47.833/24.194 | −9.35% |
| 3:5 G512 | 0→1 | 195.274/118.031/77.244 | 245.660/127.753/117.907 | 50.386/9.722/40.664 | +25.80% |

Request 描述性 median [min,max]：

| 条件 | Pass0 ms | Pass1 ms | Pass0 样本 SD ms（n=3） |
|---|---|---|---|
| G32 | 203.999 [172.766,223.732] | 258.860 [223.624,264.512] | 25.698 |
| G512 | 195.274 [184.260,203.280] | 265.031 [245.660,278.304] | 9.550 |
| N0 | 255.520 [175.314,286.797] | 253.272 [234.862,257.755] | 57.503 |
| Nm | 214.309 [208.504,252.907] | 227.546 [209.160,229.268] | 24.136 |
| N16 | 185.617 [162.731,233.562] | 234.749 [219.983,327.321] | 36.147 |

三阶段的描述性 SD/范围全列于 JSON。Request 配对相对差 **−18.109%～+101.142%**；Prefill −28.298%～+129.491%；Decode −14.664%～+71.463%。所有负差保留。P1−P0 是 profiler/观测插桩差异与运行波动的合量，不能统一从 A 扣除或全称 Nsight 成本。

**事实：**G32 Pass0 的下降主要在 prefill，而其他条件未呈共同单调变化；N0 b1 decode 比另两个 block 长，N16 b2 profile 三阶段都较长。Pass0-first 有 8 对、Pass1-first 7 对，条件/位置并未完全平衡；负差也不只出现于一种 pass 次序。
**推断边界：**可怀疑热态/Host 调度/共享栈或观测扰动，但没有足够证据归因其中任一因素；不按位置混池证明“order effect”，不删除 b1/b2 或设冷启动异常。

## N1 对照、allocation 与质量

同 pass、同 block 的差值，R/P/D（ms）：

| block / pass | Nm−N0 | N16−Nm |
|---|---|---|
| 1 / 0 | −78.292/−27.707/−50.585 | 25.058/22.779/2.279 |
| 1 / 1 | −25.701/−12.556/−13.145 | 10.823/4.510/6.312 |
| 2 / 0 | 38.994/35.858/3.136 | −51.578/−51.789/0.211 |
| 2 / 1 | −30.209/−12.980/−17.229 | 99.775/65.351/34.424 |
| 3 / 0 | −2.613/−15.914/13.301 | −67.291/−68.029/0.738 |
| 3 / 1 | −24.003/−33.453/9.450 | 5.481/6.362/−0.882 |

Request 的 profile×variant 差中差，Nm−N0 为 b1 +52.591、b2 −69.203、b3 −21.391ms；N16−Nm 为 −14.235、+151.353、+72.771ms。
这是描述性不一致，不是交互显著性或因果估计。Nm 对照还含包装/分支；V16 总差不是纯 wait。V16 单次同步 B 的 exposed union 为 0.236318 / 18.716567 / 0.514684ms，hidden union 为 30.738813 / 178.663819 / 53.070623ms；每行只对应那次 sync，不能解释整个 request 或跨同步相加。

N1 各 profile 的 **3 次 prefill cudaMalloc**、大小 UNKNOWN、opaque 内部等待 NOT_DECOMPOSED：

| block | N0 opaque ms | Nm opaque ms | N16 opaque ms |
|---|---|---|---|
| 1 | 2.398310 | 1.120623 | 1.222034 |
| 2 | 1.578556 | 1.671223 | 1.243726 |
| 3 | 1.848218 | 1.282014 | 1.457435 |

G1 measured 窗口未观测 allocation。不能推定 Pass0 allocation 相同或大小为零，不能将所有组差归于预定同步；N1 fresh measured stream 的成本不移出窗口。

Coverage 按既有逐窗口规则：分母为该窗口内按 `(source SQLite, physical sync ID)` 去重的 observed call，按 host API 区间裁剪后时长加权，Request/phase 独立计算，不重复累加。N1 Request 为 3/3 或 4/4，prefill 2/2，decode 1/1 或 2/2，supported/B-valid count 和 clipped-duration 都是本批 100%；逐窗分母及来源见 JSON。这是调用证据覆盖，不是 request 可解释比例/visible exposure。G1 仅 A 投影必要集合通过，物理 B coverage 不主张；不是把窗外/默认流物理 INVALID 判成 request 失败。

45 窗口 unattributed=0、30/30 成功只描述本批，不能估计未来缺口概率为零，不能据此冻结“unknown必须0”或“所有覆盖必须100%”。硬性身份/边界/drain/依赖/诊断和互斥守恒不放宽；可界定局部缺口才保留 unattributed，影响不明仍拒绝。UNKNOWN、NOT_ASSESSED、分域与 opaque/B/Derived 限制保持。
11 类统计谬误已核对：按条件/block/pass 分层防聚合反转，不从 kernel/token/sync 伪造 n；不因成功/低unknown择样或剔除极值；没有 p-value、显著性检验、干预收益或因果结论。基率/生态/逆因果等不适用的项不制造分析任务；Pilot 探索性判断显式保留，不冒充确认性分析。

## Freeze 输入与唯一下一步

**已有依据、可继续固化：**有限 workload/内容摘要、N1/G1支持域与 claim 限制、host/trace completion 和窗外 drain、variant/流政策、硬性质量门、统计单位及固定配对/组序；Pass0 性能主口径、Pass1 解释口径；保留 signed 差、allocation、失败/partial，禁止统一 A 校正和自动 retry。不是已完成 Gate12 或已冻结执行/analyzer commit。

**仍未定：**warmup 充分性；Formal repeat/block 与最大成本；与有限 claim 对应的绝对精度/等价带；profiler 扰动的数值接受/处理政策；局部 unknown/coverage 数值解释政策及时间容差；最终 registry/schema/analyzer、统计/图表及排除签字版本。
不能用 n=3 冻结稳定性或 repeat。若先给出有研究意义的绝对精度 h，方差—预算粗估随 `s²/h²` 变化；h 减半约需四倍样本只是成本敏感性，不是基于本批效果倒设精度或样本量保证。当前没有充分依据给出一个“正式 n”。

**warmup1 未证明充分，不等于已发现不足。**30 次 warmup stage 都成功，持续 1.058209～1.551770s，但每进程只有一次，不能观察暖机迭代收敛；warmup/request 随次序并不一致。prefill 波动、配对负差及 N1 fresh-stream allocation 不能单独证明 warmup 根因。

**唯一推荐：已计划的五条件各 3 对 Pass0 warmup1/3 对照，30 个新进程、0 条新 profile。**不同时追加 b4～b6，不改点位/输入/variant/stream/backend/completion。沿用三 block 条件顺序和 b+j 决定 1→3 / 3→1；先做未来必需的最小 warmup 参数/逐 stage 记录接线并审查，不扩长驻框架、不在本轮实现或执行。
它直接问“增加两次同合同暖机是否改变 measured request/phase，以及第2/3次暖机是否仍明显变化”，而不是为显著性加采。结果分别解释为支持/反对 warmup1 作为固定政策的证据，或仍不确定；零/混合差不证明等价，不把 Pass0 warmup3 配对给本批 Pass1 warmup1。
预先保留全部原值/正负差，观察所有条件而不只 N16；如效果与次序混淆、暖机未收敛、绝对精度无法承担 claim，则明确未定并停，不改阈值或追加另一方向。

成本：本批 driver 累计 **3951.437s（65.86min）**，15 个 Pass0 累计 615.577s，单次 36.968～43.687s；15 个 profile 采集共 586.779s，其他是准备/加载/导出/分析，均不是 request latency。
30 个 P0 可按约 **25～35min**调度（旧速度外推并留余量，非保证），不含审查/传输；本批15个P0目录合计3429523 bytes，30个同类目录线性参考约6.9MB，预留0.5GB避免日志/partial不足。没有新REP/大domain，现有10.704GB原件与337.5MB ZIP不删。

余下30进程耗完即到60上限；任何身份/输入/token/边界/资源/超时或其他硬门失败立即停止余下槽位，不重试/替补。固定批次完成也停止待审，不自动Gate11 PASS。
**预算不保证定案**：若必须改 profile warmup，本批 P1-w1 不能替代新的 P1-w3 政策证据，需集中另审预算/claim；当前不预授权额外 profile。repeat/数值政策也可能仍缺依据，不以更多工程设施代替。
Gate7～9、Gate10限定G1与N1独立Engineering PASS保持；Gate12/Freeze/Formal均不启动。

本地交付检查：30行CSV与JSON原值、15配对及N1对照/差中差算术、45A/30N1同步汇总一致；143个相对链接、公开新增内容私有信息扫描、用户DOCX未改及`git diff --check`通过。首次暂存检查发现新汇总CRLF被报尾随空白，改为LF后复核除换行外字节不变；不是Raw或测量缺陷。没有仓库测试重跑；本审查提交只包含文档和必要派生汇总。
