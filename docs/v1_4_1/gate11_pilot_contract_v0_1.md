# Gate11 限定 Pilot 角色与首批执行合同 0.1

2026-09-30；`G11-LIMITED-PILOT/0.1`。用户已批准，**仅适用于本版本声明之后的新采Pilot**；不是Protocol Freeze。执行设计沿用[既有Gate11准备](gate10_workload_plan_v0_1.md#gate11-local-preparation)，进度以[科研进度7.112](research_progress.md)为准。

## 适用范围与不可继承的资格

复用限定平台及N1/G1分域：Qwen2.5-1.5B-Instruct、batch1、fp16/eager/SDPA/cache/greedy、单GPU、主要request线程。G1自然32/2、512/2仅投影A；N1显式流32/2的V0/Vmarker/V16仅已获资格的A和合格单sync B。沿用[Gate9分域资格](gate9_closeout_v0_1.md)、[Gate10选定点一次可行性](gate10_closeout_v0_1.md)、[N1三组Engineering收尾](n1_model_feasibility_closeout_v0_1.md)及已批准opaque allocation/RAW_PHYSICAL边界。

Pilot只估计repeat、warmup、观测开销及质量政策。旧Engineering、原BLOCKED和历史资格不升级；本地CPU替身不是目标机验证。`dropped_records_status=UNKNOWN`、`measurement_validity=NOT_ASSESSED`、`formal_eligible=false`保持；D/Signature禁用，不授完整新版Q0、Formal或信息增益结论。

## 版本与文件链

以下是显式角色扩展，不改S的W/terminal、A互斥规则、B公式或completion定义。旧Engineering schema/读取路径不替换。

| 产物 | 新版本/必需绑定 |
|---|---|
| 执行前manifest | `run_role=PILOT`、`data_role=Pilot`及封闭`pilot.version=G11-LIMITED-PILOT/0.1`；原源码/输入/设备/环境/分域声明仍必需 |
| pass ledger | `exposedpath-pass-identity/0.2.0`；`pilot`、run/pass、请求身份、manifest/prompt hash一致 |
| producer receipt | `exposedpath-pilot-producer-receipt/0.1.0`；原文件集合、大小/hash及状态＋同一pilot绑定 |
| 执行receipt | `exposedpath-pilot-execution/0.1.0`；原实际配置/执行/来源检查＋角色、pilot、token文件hash |
| 窗外token文件 | `exposedpath-pilot-tokens/0.1.0`；manifest/producer hash、唯一measured request身份、2个batch1非负整数值 |
| input receipt | `exposedpath-pilot-input-receipt/0.1.0`；原Raw/SQLite/export/身份/边界/源码＋必需drain、stage、pilot_tokens |
| Canonical/投影 | 原几何/clock/schema不改；Canonical data_role必须匹配producer；Raw结构化NVTX实际含Pilot请求身份，不能仅重写sidecar |
| domain/report | `exposedpath-pilot-domain-check/0.1.0`、`gate11-pilot-collection/0.1.0`、`gate11-pilot-diagnostic/0.1.0`；保留所有原支持域/诊断门；成功只为待审，不是Gate PASS |

封闭pilot对象字段：version、batch_id、block、position、condition、variant、pair_id、run_id、pass_id、pass_order、purpose=`POLICY_ESTIMATION_ONLY`、declaration_role=`PRE_EXECUTION`、formal_eligible=false。`exposedpath/gate11_pilot.py`将每条声明与固定schedule逐字段/类型精确比对；不接受额外字段、任意条件或其他block数。marker的0.1几何schema只作明确Pilot角色扩展，不能与旧Engineering身份混用；账本必须新0.2。

文件名`engineering_execution.json`作为已有传输入口保留，数据角色由严格版本及声明决定，不由文件名推测。封存旧Raw不补写；Pilot适用版本不追认旧输出。任何缺文件/hash、错run/pass/block/variant、错角色、输入/输出不一致、未知schema或实际配置冲突拒绝。

## 配对与预算（只实现已批准首批）

G32/G512/N0/Nm/N16对应自然32/2、自然512/2、显式32/2 V0/Vmarker/Vsync（展示名V16）。每进程warmup1/repeat1；各run独立manifest、PID、attempt及request身份。

- b1：G32、N0、Nm、N16、G512；b2：G512、Nm、N16、N0、G32；b3：G32、N16、N0、Nm、G512。
- b与位置j从1开始，b+j偶数P0→P1，奇数P1→P0；相邻两run同pair。共30个模型进程/15条profile。准备/身份/静态子进程不作为模型重复样本。
- Pass0只关闭通用trace观测NVTX，保留N1包装、预定marker/V16真实同步、实际流、host边界及窗前成功drain；不通过通用trace开关删除N1行为。加载和warmup仍窗外。
- token取自原helper已host-readable的结果，在最后completion之后持久化；不再读Tensor、不添加D2H或sync。每pair逐值一致，同32输入的G32/N1及block间一致，G512各block一致。不是只比较数量。
- pair核代码/输入/环境/配置、实际入口PID、drain/stage、角色及逐值输出；跨block公共环境/模型配置不能漂移。N1各pass的实际干预0/1、layer16、decode token1及同步布尔值都验证，不能只看manifest。
- Pass1复用原Canonical/投影/S/A/B消费者和逐request门。新型/目标诊断冲突、缺correlation/ownership/边界/drain/依赖仍拒绝；官方同类外进程warning沿用已有处置，原记录和UNKNOWN保留。

失败立即停止，失败run保留partial，余下槽位NOT_RUN；不retry/resume/替补/改参数。首批完成只写`FIRST_BATCH_COMPLETE_STOP_FOR_REVIEW`、Gate11 NOT_RUN；60进程是总体预算上限，未实现也未预授权续批或warmup扩展。

## 计时和政策边界

P0/P1均从host起点到最后host-readable completion记录三窗口；P1的trace clock只用于A，不能跨clock直接相减。`delta=T1−T0`、`ratio=delta/T0`（T0>0），保留负差。这是profile＋共同观测插桩差异＋运行波动，不是纯Nsight成本；不从P1 A各项减掉它。N1 Pass0也保留干预，因此按同pass/block比较Nm−N0与N16−Nm，不能把全部差值解释为纯wait因果贡献。

warmup1充分性、repeat数、精度/等价带及overhead/局部unknown政策均待Pilot依据。首批n=3不保证能定案；不得按显著性或unattributed=0追加/选样。opaque allocation内部等待不拆，不预设组间相同；B不跨sync相加。Gate12 Freeze独立，不能从批次exit0或低噪声自动授予。

## 交付及停点

`scripts/run_gate11_pilot.ps1`默认只校验包、从固定服务器前置部署、严格核源码字节并跑相关CPU测试（mask=-1）。不调用模型/设备adapter/Nsight。回执需协调窗口审查；显式`-CollectReviewedPilot`才会进入另一个全新目录，绑定已完成静态回执，复核当前内容，并进行必要设备/输入检查和首批30进程。此开关是未来执行入口，不表示本轮已经授权采集。

固定输入/模型inventory、服务器路径、commit/bundle/hash在不提交的本机delivery配置；源码候选字节只允许预先从该Git内容得到的LF/CRLF表现，记录实际长度/hash，不拿当前字节更新期望、不改服务器源码。模型内容重新核验仍走原入口。参考旧V0字节兼容不是本轮新Pilot的输入。

预计首批1.5–2小时，规划15GB数据及0.3–0.5GB ZIP，预留35GB（含审查副本）；不保证实际速度或压缩率。超时沿用工具120s、collection300s、driver900s，不自动提高。阶段输出及20秒状态提示只显示日志，不改变测量/timeout；原始字节日志保留。疑似未退出后代则停止封包，不杀无关进程；否则单ZIP包括原始entry异常/退出、preflight、manifest、tokens、REP/SQLite、分析、配对、批次计划/未执行和静态回执。首批后只审查，不自动Pilot PASS。
