# 同完成路径 batch 负载 Engineering 对照 0.1

状态：本地接线／待审交付，不是新 Formal 协议、Pilot 或 Gate14。Gate13 已有限定 PASS 及执行99f3bae／分析e19的结果保持。依据用户明确授权、当前研究设计 v7.1 中 batched invocation 的整体 ownership、已批准自然 G1 投影 A 和 Host-readable completion；没有扩大同步语义或默认流物理 B 资格。

## 固定问题与批次

在同一4090／Qwen2.5-1.5B-Instruct内容快照／torch2.6+cu124／FP16／eager／SDPA／greedy路径下，增加 batch 是否改变可观察工作量、完成位置和墙钟预算？这不预设 Device wait 单调增加。旧 w11 为 RTX6000 Ada／torch2.5.1+cu121／512-b4-o16 Prototype，且是显式 device-wide sync 完成路径，不能与本次作单变量或同口径效应比较；更正依据见[旧路径对照](gate13_w11_execution_comparison_v0_1.md)，旧报告原样保存。

固定顺序：B1-P0 → B1-P1 → B4-P0 → B4-P1。每进程 warmup3、repeat1；两个条件均输入512、每样本输出2。B4由已绑定的512输入 sample0复制四份、attention mask全1、sample_index=0..3；B1与B4仍绑定同一源字节SHA和实际新输入文件SHA。批量整体是一个 request，不是四个并发用户请求，不分摊单样本因果时间。每对 P0/P1要求同内容、配置、设备和逐样本 token 值一致；不同batch的实际token值照实保留，不填预期值。

## 最小接线与版本

- 新封套 `BATCH-LOAD-ENGINEERING/0.1`／profile `TARGET_SCOPE_ENGINEERING_BATCH_LOAD/0.1` 是闭集，仅允许B1/B4及固定四槽。原 Engineering b1、Pilot、Formal角色和旧版本读取路径不继承batch许可。
- manifest与pass ledger承载同一batch/pair/run/pass绑定；ledger `exposedpath-pass-identity/0.5.0`、执行 `exposedpath-batch-load-execution/0.1.0`、token `exposedpath-batch-load-tokens/0.1.0`、输入收据 `exposedpath-batch-load-input-receipt/0.1.0`。token文件进入收据完整文件集合、哈希与逐run来源不变性检查；manifest／producer／实际shape／sample身份全部关联，无循环hash。
- 复用 verified 模型入口、隔离预检、显式直接解释器、site、实际CUDA UUID/PCI、producer、completion helper、窗外成功drain与三窗口投影。新增runner检查只是已读Host token向量长度等于batch，不增加Tensor读取／D2H／同步或改变正常完成路径。
- 真正执行三次同合同暖机；暖机没有读取的token/EOS保持null。测量的两个Host-readable向量在窗口结束后持久化；每个向量必须有batch个非负整数。任一样本EOS按既有整批提前停止规则保留，不能成为合格2-token样本。没有token网络发送。

## 分析口径与拒绝

复用原 Raw→Canonical→共同completion projection→S→自然G1投影A。逐request检查边界、scope／clock、窗外drain、必要成员／依赖、实际同步、线程/流/context/correlation、已观察API分类及diagnostics。未知API、错身份、缺映射、跨支持域依赖、新型或目标冲突warning仍拒绝；仅同类官方已接受处置按原规则执行。batch4实物仍待验，不由CPU fixture授予新Q0或科学资格。D/Signature不启用，自然默认流物理B不发布；窗外INVALID不直接污染request准入。

每条件输出Request/Prefill/Decode的P0/P1 Host-readable时长、P1五类A绝对值及各自窗口比例、CUDA API submit/non-submit及opaque子预算、GPU活动union、copy API与D2H原始记录、逐sync入口／返回／最后必要activity完成及已验证的投影suffix引用、completion原始anchor；保留clock与record/correlation/thread引用。G1后缀不是完整物理W/B。可选Driver表没采到时是UNKNOWN，不当作零；嵌套sum和union不得与A混同。P1−P0和B4−B1保留signed差；单次配对扰动与运行波动不分离、不扣A、不作稳定性或统计结论。

`cudaMemcpyAsync` Host调用整体仍属CUDA API；设备侧复制属activity，凭已有依赖进入必要集合。submit/non-submit不代表阻塞/非阻塞，CUDA API不是纯CPU计算；Device wait仅受支持sync区间内必要GPU活动的暴露，不是全部GPU相关Host阻塞。API内部等待不可识别则不拆分，unattributed=0不证明所有内部机制已解释。

## 执行和停止

单一增量包以服务器已记录99f3bae为前置；默认A仅部署／CPU／源码实字节校验，禁止模型/CUDA初始化/Nsight。协调窗口审查静态单ZIP后，B才显式执行；新增独立evidence目录，完整回传单ZIP（含静态原件）。预计15–25分钟，分析/封包时间可能更长；至少12GiB临时空闲是保守规划而非实测成本。只运行4模型进程/2profile，不自动重试、替补、扩batch/output或续批。既有collector300秒、单export、外层driver900秒上限保持。OOM、超时、输入/设备/源码/模型/配置/token冲突、边界/drain/依赖/诊断/分析失败立即停，保留partial及NOT_RUN；UNKNOWN后代拒绝封包，不能删锁、杀无关进程或强行恢复。

长期YLQ低于50GB目标不授权运行中清理。采用临时展开→审查→完整归档核验→删除明确可重建展开副本；保留Raw/REP/SQLite/输入/身份/失败报告/最终小汇总/完整ZIP及清理回执。现有Gate13清理回执原件尚未定位，不能把候选30文件/38.95GiB称为已删除。新批次后具体清单须依实物另审，不在本包自动删除。

后续“同负载、复制前显式同步”仅为首轮仍不能解释路径时的待审干预设计：同batch/input/backend，独立声明新增device或stream completion与必要集合，不能当自然G1修复；本轮不实现、不授权第二轮，不按较高Device wait选样本。
