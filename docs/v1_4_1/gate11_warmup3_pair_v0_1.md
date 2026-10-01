# Gate11 共同 warmup3 配对批次 0.1

2026-10-01；`G11-WARMUP3-PAIR/0.1`，未来新采 **Pilot / POLICY ESTIMATION ONLY**。用户已批准额外30模型进程/15profile预算；本地准备不是目标机验证，Gate11 **BLOCKED**，Protocol Freeze未启动。依据[政策决策0.1](gate11_policy_decision_v0_1.md)，不修改研究设计v7.1 / Pre-Pilot协议v2.1的S/A/B公式或已有资格支持域。

## 固定执行与适用范围

五条件G32/G512/N0/Nm/N16；原Qwen2.5-1.5B-Instruct内容清单及32-token prompt、原循环构造512-token prompt，batch1/fp16/eager/SDPA/cache/greedy，输出2、repeat1、**两pass共同实际warmup3**。每进程独立加载，加载/3次暖机/成功drain位于request窗外。G1自然投影A；N1显式流V0/Vmarker/V16，原第16层每decode一次，held暖机流及fresh measured流不变。

- b1：G32,N0,Nm,N16,G512；b2：G512,Nm,N16,N0,G32；b3：G32,N16,N0,Nm,G512。
- b、位置j从1起：b+j偶数Pass0→Pass1，奇数Pass1→Pass0。同条件两pass相邻，run/PID独立，绑定同pair/block及实际variant/pass。
- 仅3完整block、30新模型进程/15profile；原60预算已使用，本批完成才累计90进程/30profile。不是授权后续批次或Formal n=6/12。预计70～90分钟，规划15GB原件/预留35GB为估计，不能删旧证据腾空间。
- 所有有效值、负配对差、Vmarker等必要对照保留；不按效果/低unknown/区间离零选择样本。

## 版本接线与必需检查

[封闭binding schema](contracts/gate11/warmup3_pair_schema_v0_1.json)固定新版本、`purpose=COMMON_WARMUP_POLICY_ESTIMATION_ONLY`、PRE_EXECUTION及formal_eligible=false；manifest、producer/pass ledger、执行/token回执、input receipt、domain、pair/batch及delivery须携带这一binding。只识别显式版本，不按warmup_count猜测角色。

复用已经逐次观测的pass ledger0.3、producer0.2、execution0.2、diagnostic0.2、N1 execution0.2/calls0.2；格式不另复制一套。旧Engineering、首批`G11-LIMITED-PILOT/0.1`与P0对照`G11-WARMUP-CONTROL/0.1`读取/判定保持；不能用改label把它们当本批。

实际ledger顺序必须为warmup-0/1/2及request-0；每次stage有开始/结束/成功/顺序，未读取暖机token/EOS与N1 observed_tokens保持null。消费者分别检验这些未知值和测量的实际2 token/非early EOS，不填目标值。测量token复用已有host-readable值、窗外持久化后逐值核对；不增加D2H、同步或改变completion。N1各暖机与测量的实际包装/marker/同步次数、held stream身份和fresh measured生命周期都保留；通用trace开关不得删Pass0干预。

提交/clean、解释器/PID、模型/输入内容、实际CUDA设备/配置、隔离预检及源hash仍严格核验；三窗口、成功drain、必要依赖/ownership/terminal、诊断及A/B准入不改。新binding只对齐实际request数量和暖机未知观测，不能豁免测量缺证据。G1无自然默认流完整B；N1仅合格单sync B；opaque allocation原记录/内部等待不拆，UNKNOWN/NOT_ASSESSED保持，D/Signature禁用。

## 编排、交付及停止

复用`scripts/gate11_pilot_batch.py`，新入口必须显式`--execute-reviewed-warmup3-pair`并核config版本；旧入口不可消费本批config。每run prepare→verified entry→回执→pair→batch，阶段与block/condition/pass/warmup数输出复用现有progress。正式结果仅`WARMUP3_PAIR_BATCH_COMPLETE_STOP_FOR_REVIEW`，不等于Gate11 PASS。

一个增量bundle/部署ZIP以前置服务器4abb5ea为基线；固定commit、脚本/config/source字节与清单绑定，准确私有路径/hash只在本地交接。`run_gate11_pilot.ps1`默认仅部署和相关CPU(mask=-1)，静态回执必须先审查；显式`-CollectReviewedPilot`才初始化CUDA/模型/Nsight，不是CPU-only。每阶段一个ZIP，最终单ZIP包含原静态副本及所有30run计划、partial/NOT_RUN、入口异常/退出、预检/输入/实际暖机/token/流干预、REP/SQLite/派生结果/pair/batch。清单先快照文件列表，排除自身，原输入不覆盖。

保持已有tool120s / collection300s / driver900s超时；身份/输入/token、暖机次数/顺序、边界/drain/依赖、diagnostic/分析、OOM、磁盘不足或超时硬失败立即停，保留partial及未执行，不retry/resume/替补、临场改参或杀无关进程。写入者退出不明先停止封包。30槽位完成也停，无自动续采；CPU回执通过不授目标机测量资格。

## 预定审查与裁决边界

结束后按[政策决策§4](gate11_policy_decision_v0_1.md#4-批次结束后的政策裁决方法预先固定非找显著性)一次集中审查：同批同政策P1−P0、同pass N1两对照、profile×variant、R/P/D及A/逐sync B原值、warmup顺序和allocation；不能把新P0-w3与旧P1-w1配对/混池。

Pass0报告性能，Pass1解释观测执行，不从A扣配对差、不称纯Nsight/marker/wait成本。10/5ms仍是待审精度候选，不是效应/等价/分类/clock tolerance。3block bootstrap仅探索性，需同时报告全部block及留出敏感性，区间窄不证明充分。固定预算结束后决定warmup/repeat/质量政策及有限claim；不足就收缩claim，不追采到显著或波动归零，Gate12签字和Formal采集仍独立。
