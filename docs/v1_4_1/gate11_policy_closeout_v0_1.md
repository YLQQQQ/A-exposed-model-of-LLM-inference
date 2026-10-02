# Gate11 共同warmup3审查与限定Pilot政策收口 0.1

2026-10-02；`G11-POLICY-CLOSEOUT/0.1`。**Gate11 PASS：限定Pilot的政策评估与Freeze输入准备完成，不是Protocol Freeze、Formal资格、统计稳定性或信息增益通过。**沿用[预定裁决方法](gate11_policy_decision_v0_1.md#4-批次结束后的政策裁决方法预先固定非找显著性)，通过依据是实际同政策配对可用、硬门成立，以及有界运行/解释政策和claim收缩明确；不是30/30或bootstrap较窄。Gate12仍NOT_RUN，政策需在下一阶段确认并绑定版本，当前不采集。

## 1. 唯一新证据及审查范围

执行commit **`470c5afa6400a77fb79692699cdd8cecc47b314d`**，与本报告的文档收尾commit分开。封存包`gate11_w3_pair_470c5afa6400_pilot.zip`，653736655 bytes，SHA256 `64F930679FAF7B2B55538E4381AB4A6A8B8652CFE8892BB21EBDFFBDC2A0884D`；清单SHA256 `4EB0D72252D1754C1CC374CDD130A9686DEABA2BDA61CAB02FBEA5559A1ABADA`。本地流式核验1746个文件/1745项清单、唯一安全路径、完整覆盖、CRC及全部大小/hash；原件和原`WARMUP3_PAIR_BATCH_COMPLETE_STOP_FOR_REVIEW`/BLOCKED报告不改。定位用本机交接索引，公共文件不提交私有路径/Raw。

可复查数值与来源： [机器汇总](gate11_w3_pair_summary_v0_1.json)、[30次host原值CSV](gate11_w3_pair_durations_v0_1.csv)。机器汇总保留15对signed差、6个同pass N1对照、3个profile×variant对照、90条实际暖机、45窗A、逐sync B/terminal/完整集合计数和669个关键文件hash。本地复用已有独立Raw审查工具，不调用被测S/A/B函数生成预期，不重跑完整analyzer/Q0/仓库测试。服务器原CPU日志64 passed属目标机此前执行，不称本地重跑。

- 30个独立入口exit0、无timeout/retry/exclusion/early EOS；15个profile，90次实际顺序成功暖机、每进程repeat1；组序/相邻pass顺序与[G11-WARMUP3-PAIR/0.1](gate11_warmup3_pair_v0_1.md)精确一致。角色、预执行用途、manifest→producer/ledger→输入receipt→域/配对一致，30run环境snapshot及runner源码字节身份一致。
- 实际输入32或512、输出2、batch1、eager/fp16/配置SDPA/cache/greedy及既定模型/GPU一致；loaded_config和observed_configuration均核对。`native_attention_backend=UNKNOWN`、其qualification=NOT_ASSESSED原样保留，不把配置名称当特定native实现资格。32输入各组token均`[[463],[2529]]`，G512均`[[29184],[6556]]`，两pass逐值一致。暖机未观测token/EOS仍null，不用配置补成实测。
- 三个host-readable completion边界、成功窗前drain、加载/暖机在外；N1每request专用流，3个held暖机流与fresh measured流独立。两pass均实际保持V0零干预、Vmarker第16层marker不同步、V16同位置一次同步，不只检查配置。
- 15条实际profile argv为既定cuda,nvtx/process-tree最小观测、CPU采样/切换/内存usage/ISR关闭，显式目标解释器入口；15个SQLite只读integrity/schema及Raw→Canonical→投影/clock/hash逐字段核对。必要提交/同步集合、相关context/stream/thread、成功返回及drain前缀检查通过。G1有独立必要成员/依赖与两模式窗口投影证据，只授A；N130个实际同步的完整W、terminal、B公式/来源与原文件一致，其中9个RAW_PHYSICAL内部同步、18个结构化token-ready、3个结构化V16干预。
- 45窗A按独立API类别/区间并集/等待交集复算一致，顶层/子类互斥守恒、连续边界及Request=Prefill+Decode成立；unattributed全0是本批事实，非未来清零门。N1裁剪physical-call coverage为supported/B-valid；G1物理B coverage不主张，不补100%。
- 60条同类外进程warning按既有`G8-WARNING-EVIDENCE/0.1`处置，核原消息/rowid和目标CUDA/NVTX实物，无新型或目标冲突；不删除warning，不转换为全capture认证。`dropped_records_status=UNKNOWN`、`measurement_validity=NOT_ASSESSED`、D/Signature禁用保留。

## 2. 原值、扰动与实际A/B

以下单位ms，保留三个block次序；完整30条Request/Prefill/Decode原值及warmup/driver成本在CSV，配对原整数及描述性统计在JSON。**P0性能用host clock，P1的A用trace clock，两者不合并，不从A扣差。**

| 条件 | P0 Request b1/b2/b3 | P0 Prefill b1/b2/b3 | P0 Decode b1/b2/b3 | P1−P0 Request b1/b2/b3 |
|---|---|---|---|---|
| G32 | 165.943 / 156.844 / 150.610 | 86.366 / 83.220 / 80.604 | 79.577 / 73.624 / 70.006 | +50.976 / +56.218 / +57.071 |
| G512 | 179.403 / 176.796 / 164.695 | 107.540 / 102.844 / 90.485 | 71.862 / 73.952 / 74.210 | +43.703 / +45.732 / +57.051 |
| N0 | 143.496 / 137.635 / 165.486 | 80.030 / 75.120 / 92.934 | 63.466 / 62.516 / 72.552 | +75.295 / +85.207 / +79.570 |
| Nm | 330.628 / 156.687 / 170.457 | 207.504 / 88.045 / 93.884 | 123.124 / 68.642 / 76.572 | **−119.126** / +72.250 / +49.713 |
| N16 | 183.807 / 162.577 / 164.987 | 105.337 / 89.575 / 86.186 | 78.470 / 73.002 / 78.801 | +14.392 / +33.062 / +49.210 |

Request配对相对差**−36.030%～+61.908%**（绝对−119.126～+85.207ms），14正/1负全部有效保留。Nm b1长值无硬门错误，不删、不归因纯初始化或Nsight；各阶段/顺序和profile×variant不一致，不能将其统称“profiler成本”或精确迁移到未profile性能。三个顺序块不足以独立识别block漂移和pass/variant因果效应。

N1同pass Request原对照：

| block | P0 Nm−N0 | P0 N16−Nm | P1 Nm−N0 | P1 N16−Nm |
|---|---:|---:|---:|---:|
| 1 | +187.132 | −146.821 | −7.289 | −13.304 |
| 2 | +19.052 | +5.890 | +6.095 | −33.298 |
| 3 | +4.971 | −5.470 | −24.886 | −5.973 |

方向反转及两pass差中差保留；即使P1 N16−Nm三次都负，也不是稳定收益、显著性或纯等待贡献。每block不是随机化因果排除所有混杂的证明。

P1三个block均值，仅描述**观测执行的trace窗口**，不与host性能长度混同：

| 条件/窗口 | T | CUDA API | device wait | sync residual | Host path | unattributed |
|---|---:|---:|---:|---:|---:|---:|
| G32 Request | 212.5672 | 124.5486 | .0261 | .6402 | 87.3523 | 0 |
| G32 Prefill | 112.8796 | 66.9469 | .0261 | .6027 | 45.3040 | 0 |
| G32 Decode | 99.6876 | 57.6017 | 0 | .0376 | 42.0484 | 0 |
| G512 Request | 222.0024 | 117.3114 | .2828 | .3271 | 104.0811 | 0 |
| G512 Prefill | 119.1564 | 63.9839 | .2828 | .1373 | 54.7523 | 0 |
| G512 Decode | 102.8460 | 53.3275 | 0 | .1897 | 49.3288 | 0 |
| N0 Request | 228.6722 | 123.6516 | .0464 | .7154 | 104.2587 | 0 |
| N0 Prefill | 122.4465 | 67.8787 | .0464 | .6906 | 53.8308 | 0 |
| N0 Decode | 106.2256 | 55.7729 | 0 | .0248 | 50.4279 | 0 |
| Nm Request | 219.9380 | 124.9357 | .0175 | .6942 | 94.2906 | 0 |
| Nm Prefill | 117.8484 | 67.5971 | .0175 | .6678 | 49.5660 | 0 |
| Nm Decode | 102.0896 | 57.3386 | 0 | .0264 | 44.7246 | 0 |
| N16 Request | 202.4337 | 111.7985 | .1837 | .8294 | 89.6221 | 0 |
| N16 Prefill | 107.5812 | 60.3651 | .0690 | .4997 | 46.6475 | 0 |
| N16 Decode | 94.8525 | 51.4334 | .1147 | .3297 | 42.9746 | 0 |

显示舍入不参与守恒判定；原整数和API submit/non-submit子类在JSON。API成本不等同设备等待。30条合格N1 B均逐sync保留、不跨sync相加；V16预定同步有如下独立恢复（每条W=2814，terminal为对应decode kernel）：

| block | W hidden union | W exposed union | terminal overlap | return tail |
|---|---:|---:|---:|---:|
| 1 | 42.882086 | .117055 | .000992 | .024297 |
| 2 | 44.572819 | .117632 | .000960 | .101375 |
| 3 | 47.873587 | .109375 | .001024 | .015711 |

hidden仅相对该次同步，不是整个request未暴露；A_device_wait仅为受支持同步恢复部分。九条N1 profile各3次opaque cudaMalloc，API区间成本合计各约1.145～1.922ms、具体三次原值/差异见JSON；大小未知，内部等待NOT_DECOMPOSED，无虚假W/B。P0没有对应physical trace，不假定allocation相同，不把全部E2E组差归因于干预。

## 3. 三批分开比较与精度限制

[首批221f46c](gate11_first_batch_review_v0_1.md)是w1配对；[4abb5ea对照](gate11_warmup_policy_review_v0_1.md)是P0 w1/w3相邻对照、0profile；本批470c5afa为共同w3相邻P0/P1。各政策仍n=3，**不混池、不跨warmup配对、不拼成n=6**。历史审查复用，不重扫原包。

Request样本SD（ms，旧w1→新共同w3）：

| 条件 | P0 | P1 |
|---|---|---|
| G32 | 25.698→7.711 | 22.156→4.640 |
| G512 | 9.550→7.848 | 16.416→.682 |
| N0 | 57.503→14.683 | **12.132→14.140** |
| Nm | **24.136→96.695** | 11.146→8.717 |
| N16 | 36.147→11.624 | 58.179→10.057 |

多数分组变窄、两组反向，**不能据跨时段比较认定w3普遍改善可重复性或已稳定**。本批十个condition/pass的第1次暖机stage中位数约1053～1323ms，第2次171～271ms，第3次145～229ms；第3−2次方向仍混合。结合独立w1/w3对照及双方实际w3通过，足以采纳有限conditioning政策，不证明完全收敛；fresh measured N1流不因暖机流变热而改政策。

63个host均值/配对/指定对照描述量联合按完整block做10000次percentile bootstrap，seed=20261001，并展示全部block和逐一留出敏感性。n=3仅探索性；37个量的探索性半宽或留出变化超出预提10/5ms候选，**即使其余较窄也不证明覆盖率、等价或精度保证**。A各量原值/SD单列，不能从较小P0波动推定A/B精度。

| 对象（Request） | n=3样本SD ms | 假设n=6的SE粗预算ms |
|---|---:|---:|
| P0 G32 / G512 | 7.711 / 7.848 | 3.148 / 3.204 |
| P0 N0 / Nm / N16 | 14.683 / 96.695 / 11.624 | 5.994 / 39.476 / 4.745 |
| P0 Nm−N0 / N16−Nm | 101.351 / 85.078 | 41.376 / 34.733 |
| P1 Nm−N0 / N16−Nm | 15.538 / 14.143 | 6.343 / 5.774 |

粗预算是各量自身SD/√n，独立/平稳尚未证明，**不是CI、功效或n6充分性**。n3/6/12细表在JSON，不按显著性、最有利pass或目标差方向选n。10ms Request/Prefill与5ms Decode继续是未获保证的解释精度候选，不是效应/等价/分类/clock阈值。

## 4. 可供Gate12确认的唯一政策

1. **warmup3、每进程repeat1；正式建议6完整block。**保留五条件及固定输入/执行/边界/drain；原三个组序加镜像，条件次序和相邻pass先后均平衡。n6选有界成本和次序平衡，不称满足10/5ms或独立稳态。不得拿90个Pilot进程填Formal重复，也不因最终CI跨0/宽/效果不符追加。
2. **全部原值与配对保留。**Whole-block作为联合重采样单位；性能主口径P0 Request，phase/同pass N1两对照及profile×variant一并报告，原值、mean/median/range/SD、预定区间和留出敏感性均保留。kernel/token/sync/warmup不当独立重复。B仍单sync、按request/block聚类，不累加。
3. **开销政策固定为并列而非校正。**报告signed P1−P0/相对差/次序及variant交互，负差不删/截，不从A统一扣除，不设回溯性overhead百分比门。P1解释观测执行，**撤去精确P1→自然P0拆分迁移**；无纯Nsight/marker/同步等待因果成本claim。
4. **质量硬门不变，局部缺口限制解释。**身份/输入/token/配置/clock/边界/drain、必要成员/ownership/依赖/terminal/诊断和整数互斥守恒逐request验证。冲突/影响不明拒绝受影响窗口并沿批次硬失败停；仅可证明局部影响时保留unattributed及原因，给有证据部分或保守范围。若该缺口足以改变拟比较的方向/量级，就不发布对应精确分类claim，不填Host/residual。required单sync B无效禁止该机制解释；coverage是裁剪调用证据诊断，不是可解释request比例。不新增零unknown/100%门。
5. **时间和支持域边界公开。**本批marker观测延迟约.8956～2.0611ms；P1 trace/host窗口长度差−1.474478～+.675294ms。各clock内边界有源证据，但这些长度差不是clock原点映射、误差界或延迟校准；不补偿marker、不设任意容差，不作亚毫秒跨clock或跨pass等同claim。G1不发布自然默认流完整物理B；opaque内部等待不拆；UNKNOWN/NOT_ASSESSED、D/Signature禁用及完整新版Q0/Formal未授状态不变。
6. **收缩claim而不是加采。**保留“有限workload中、观测执行的可信归属与合格单sync机制事实，以及对常规指标的信息增益问题”；未来冻结后可以得到有限、null或不确定结论。**不把当前Pilot当信息增益证明，不预设N1收益，取消细微稳定E2E收益/排名、群体精度已保证、hidden跨sync总量及硬件因果/普遍预测claim。**未来区间或局部证据无法支持某比较，就如实不支持，不继续采到显著。

11/11统计风险已检查：①Simpson按条件/block/pass分层；②生态谬误不推广到所有request/平台；③Berkson不按效果/低unknown择样；④collider不按allocation或profile结果筛选/校正；⑤基率忽略不适用于本次非诊断概率报告；⑥回归均值不把跨批变窄当w3因果效果；⑦幸存偏差保留失败/排除事实及全部有效长值；⑧look-elsewhere不只挑有利对照；⑨forking paths公开三批与政策选择、固定比较/停止；⑩相关不当因果、不把配对差称纯profiler成本；⑪逆因果不作未识别方向推断。另不把零差称等价、重采样次数当样本量或独立启动当统计独立。

## 5. Freeze输入与停点

已具备依据：固定workload/内容摘要/域资格；共同w3两pass适用；三窗口/成功drain/fresh流与N1干预；完整block统计单位与n6有界建议；signed扰动及局部证据政策；硬失败/partial/无重试；claim收缩与精度不能保证的报告方式。**Gate11无需新实物或新一轮Pilot**；没有未解决的本阶段执行/语义硬阻塞，剩余不确定性通过上述禁止claim和不确定性报告保留，而非宣布消失。

本批driver合计5992.207s≈99.87min（包括采集/导出/分析，不是request时长）；展开原件21.03GB。原70～90min/15GB估计偏低。若未来确认6block，粗规划60进程/30profile、约200～240min、42.1GB原件/90GB含审查空间；仅成本估计，非本轮预算/执行授权，不新增部署包。

**唯一下一步：Gate12本地协议审查，确认上述有限政策/claim，并绑定最终代码、registry/schema/analyzer、统计/绘图/排除及协议签字版本。**现行研究设计v7.1与协议v2.1仍Pre-Pilot；此报告不是冻结正文，不启动Gate12实施或Formal采集。服务器现在无需操作。Gate7～9、Gate10限定G1及N1独立Engineering PASS保持；所有原Raw/ZIP/报告和用户DOCX保持。

本轮校核：本地完整包身份/覆盖和Raw交叉审查通过；公开原值/配对/三窗口守恒、逐sync来源、63量探索性区间有限支持/留出算术及669来源检查通过；182相对文件链接、公开隐私、DOCX原字节及diff-check通过。无业务代码/schema/公式修改，不重复仓库测试或完整analyzer。本地诊断首次在流式选取未完成时尝试semantic，遇到尚未生成的本地选取文件后停止；完整提取后15条全部通过。这是审计编排问题，不是原采集或语义失败。
