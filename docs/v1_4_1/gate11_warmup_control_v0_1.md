# Gate11 Pass0 warmup1/3 对照 0.1

2026-10-01；用户批准的 `G11-WARMUP-CONTROL/0.1`，仅未来新采限定Pilot，用于warmup政策估计，不是Protocol Freeze。沿用[原Gate11计划](gate10_workload_plan_v0_1.md#gate11-local-preparation)、[分域与首批合同](gate11_pilot_contract_v0_1.md)，首批[审查结果](gate11_first_batch_review_v0_1.md)及其原件不改、不升级。

## 固定执行与版本

G32/G512自然32/2、512/2；N0/Nm/N16显式流32/2，V0/Vmarker/Vsync。batch1、fp16/eager/SDPA/cache/greedy、固定输入字节与模型inventory、主要请求线程、既定设备/解释器不变。每新进程独立run/PID/nonce，repeat1；warmup_count仅1或3。

- b1 G32,N0,Nm,N16,G512；b2 G512,Nm,N16,N0,G32；b3 G32,N16,N0,Nm,G512。
- b与位置j从1开始，b+j偶数w1→w3，奇数w3→w1，两个新Pass0相邻同pair；封闭schedule逐字段/类型匹配，不接受任意配置/额外字段。
- **30个新模型进程、15对、0条新profile**；加首批30，耗尽原60总预算。固定批次完成或硬失败即停；partial/NOT_RUN保留，无retry、替补、resume、改点或自动续批。失败已用槽位不自动补齐。
- 默认交付只部署/相关CPU（mask=-1），待协调窗口审查静态回执后，另行显式执行开关才启动模型及CUDA；本地交付不是执行授权。

[schema 0.1](contracts/gate11/warmup_control_schema_v0_1.json)封闭binding：版本、batch/block/position、condition/variant、pair/run、pass0、warmup_count/order、WARMUP_POLICY_ESTIMATION_ONLY、PRE_EXECUTION、formal=false。
显式pass ledger **0.3.0**、producer receipt **0.2.0**、execution **0.2.0**、diagnostic **0.2.0**；token文件沿用0.1并绑定新声明及manifest/producer hash。N1 execution `N1-VERIFIED-MODEL/0.2`只扩展1/3暖机；N1 calls文件0.2.0，既有marker/lifecycle几何不改。stage ledger0.1仍逐request身份/顺序/clock/hash检查。旧Engineering及首批Pilot版本/读取行为保持，不接受未知版本或仅重标旧数据。

## 实际暖机、窗口与证据

原verified入口加载一次模型，实际按warmup-0…warmup-(n−1)依次调用原暖机函数，每次执行相同输入及2-token构造，原有窗外同步不增不减。每次stage记录原host perf_counter开始、结束、成功/异常和request身份；失败停止剩余暖机及measured request，实际未执行仍明确记录。`COMPLETE`仅表示暖机例程成功返回，不代表输出token已读取。

**暖机actual_output_tokens/early_eos=null；N1暖机observed_tokens=null。** 目标输出长度2保留为配置，不冒充实测；不为填字段增加D2H、EOS读取或计时同步。测量输出仍来自原host-readable helper，最后completion之后保存原值并逐值比较；必须实际2个token且非early EOS。

N1每次暖机创建并持有独立专用流，全部暖机完成后创建不同的fresh measured stream，保留相同包装、层16一次marker/同步、原anchor及窗前drain。w3不把fresh measured流“预热”以制造收益；仅Python上下文不是物理ownership证明，Pass0不伪造Raw或S/B。所有实际warmup及measured调用/干预计数、native流不复用、恢复、配置、身份和文件链仍验证。

Request/Prefill/Decode仍用原host completion三边界；加载、暖机与drain不入窗，不改变S/A/B、五类守恒或opaque解释。Pass0不新增A/B计算、Raw/diagnostics；UNKNOWN/NOT_ASSESSED及D/Signature禁用保持。

## 预先确定的审查方法与停点

每条件/block保留实际次序、w1/w3 measured三窗口原值、每次warmup原值/时长。`delta=T(w3)−T(w1)`及T(w1)>0时的相对差，保留全部正负值；零分母比例null。按3个block和两种先后序描述范围与方向，不删极值、不把warmup/token当独立重复，也不混合两政策总体。

若额外两次暖机的时长序列呈可重复变化，且measured变化在两种先后序均一致、不能仅由block/次序漂移解释，可支持讨论改变政策；若不同阶段/条件响应不同，讨论条件限定而非统一充分性。仍不宣称因果消除全部冷态或warmup3已充分；N1 fresh measured流的首次资源成本保持。
若方向反转、顺序混杂、波动相当、样本不足或暖机仍无收敛迹象，政策继续PENDING；小样本零差不证明等价，不临时设百分比/显著性阈值或加采。

本批**不能估计Nsight开销**，不能把P0-w3配给首批P1-w1。若拟改变P1 warmup，须另审同政策证据/预算；repeat、绝对精度与质量政策仍须集中评估。批次成功只 `WARMUP_BATCH_COMPLETE_STOP_FOR_REVIEW`，Gate11继续BLOCKED，Freeze未启动。

预计25～35分钟、预留0.5GB（规划估计，非保证）。模型/输入/代码/实际设备、warmup次数/顺序、输出值、边界/drain、N1干预/流、任何部分失败或超时冲突即停，不扩大超时。P0子入口沿用300秒、外层driver900秒。单ZIP含部署静态原件、输入/配置、Git二进制预检、每run入口stdout/stderr/异常/退出、producer/token/stage/N1记录、pair及batch计划/未执行清单；疑似活跃写入者先停封包，不杀无关进程。私有路径/精确包身份只在忽略的本地交付中。
