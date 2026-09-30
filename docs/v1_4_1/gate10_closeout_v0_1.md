# Gate10 限定G1 workload可行性收尾 0.1

2026-09-30当前补充（7.110）：[N1模型32/2三组限定Engineering可行性另行PASS](n1_model_feasibility_closeout_v0_1.md)，已关闭下文当时未完成的模型准备依赖。
本页G1原裁决及范围不变；不将两域一次成功称为共同统计稳定域。当前仅Gate11本地准备，无服务器或重采任务；下方7.102“下一步接线”为历史，不再执行。

日期：2026-09-29。裁决：**PASS，仅限G10-WORKLOAD-FEASIBILITY/0.1预定的自然G1候选集一次Engineering可行性**。不是完整N1/G1共同稳定域。N1模型V0/Vmarker/Vsync可行性仍NOT_RUN，按原计划单列实验准备依赖，不被G1代替，也不在本次收口临时扩为新采集任务。

## 512/2原件与核验

原ZIP `gate10_g1_700f671_once.zip`，27081774 bytes；SHA256 `412D304BC56AB9E59D45AD68C35A43FD0466936D6F5AD8EA3747DE9A10D17D1B`。
清单SHA256 `1B37ACE26D8C51888BF1AA178DD42D01BB2337DA0DAB123407433E945FFB3F9D`。本地直接核验CRC、89个唯一路径及安全范围；88项清单大小/hash覆盖清单以外全部文件。新审计目录中的副本不替换Raw或服务器报告。

- 执行/分析均 `700f6711f8c6f105a94408c9c8fdd4bbdafb62ba`；manifest与seal记录clean，执行脚本正常完成最后Tree检查。run `run-20260929T124000Z-ce143e34`、WMPC `wmpc-b4213a6659235e07`、目标PID53220。CPU原日志221 passed/46.15秒；这是服务器实物，不是本轮测试重跑。
- 批次只有512/2，入口包含`--remaining-512-only`，exit0、receipt.error=null；实际输入shape512/输出2、非early EOS，warmup1/repeat1、batch1。没有重复128/2。manifest预执行声明`G1_NATURAL_PROJECTED_A/0.1.0`。
- 沿用同模型内容快照、fp16/greedy/eager/SDPA/use_cache、物理3/逻辑0、既定UUID/PCI与目标解释器；和128/2的模型、配置、设备、warmup/repeat合同一致。prompt SHA256 `36c507c56d1c851bab0238c30dfd7645a5ea7eef646310c01988ae2aaffbdd0a`。producer/entry、代码与输入hash、preflight claim/final、实际CUDA身份、阶段/drain、host边界由既有inspect_execution和input receipt只读验证。
- 采集exit0、无超时、export PASS；REP SHA256 `c839ad65c2d13ed648bb37630695c395e6e531200deda2bea63686efd0636aa7`；SQLite SHA256 `97352df56851f97ff6ec0a7f316d38b4bdd345fe68c77b6120e181666ef7b2ad`，本地只读quick_check=ok。未重新export。
- domain SHA256 `8340b398cef7dc20ea634a91dc2b35f9674d042ca6597fb8e45fe8321c12c8df`与collection/batch一致；派生文件集合及hash、input/execution receipt绑定通过。原driver日志记录完整分析和load_domain复读完成；本轮不重复完整S/A/B计算。
- request质量状态`QUALITY_CHECK_PASSED_NOT_QUALIFICATION`、reasons=[]；同一trace时钟三个completion窗口、成功窗外drain、必要同步后缀已记录。3个同步必要成员数8/1905/3497，LEGACY/PTDS两模式成员和依赖边相同；这是限定投影A证明，不授自然默认流物理B。原drain映射为runtime16936/sync346。
- 19条diagnostics保留；PID65868的row3/4/6/7四消息使用既有`G8-WARNING-EVIDENCE/0.1`官方依据，目标实物7334条activity、9条关联NVTX。其他准入不豁免，UNKNOWN和NOT_ASSESSED保留，不解释为零丢失。

三窗口保存值按整数逐项核对：

| 窗口(ns) | 总时长 | Host | CUDA API | device wait | sync residual | unattributed |
|---|---:|---:|---:|---:|---:|---:|
| Request | 160923842 | 100923366 | 59679698 | 24224 | 296554 | 0 |
| Prefill | 89536754 | 53752255 | 35490070 | 24224 | 270205 | 0 |
| Decode | 71387088 | 47171111 | 24189628 | 0 | 26349 | 0 |

互斥守恒审计值和逐分量Request=Prefill+Decode一致。零unattributed不是选点或验收必要条件；这些profile时间不能用于性能趋势、自然延迟排名、稳定性、repeat数或overhead阈值。

## 候选汇总与退出项

| 候选（input/output,batch1） | 执行版本 | 分析/审查版本 | 可复用结论及边界 |
|---|---|---|---|
| 32/2 | 36ed952 | 1733ff3分类修复及后续Gate8官方依据审查 | 复用封存配对的Engineering执行/三窗可行性；保留原BLOCKED与条件性产物，不重写其数据资格 |
| 128/2 | 76ef717 | 700f671离线性能修复 | 不变Raw新目录质量通过；原900秒超时/UNKNOWN后代记录保留，不追认原driver成功 |
| 512/2 | 700f671 | 700f671目标机分析，本次文档审查 | FEASIBLE_ONCE_NOT_STABILITY；BATCH_COMPLETE_PENDING_REVIEW经本次有限审查收口 |

依据：[预定候选合同](gate10_workload_plan_v0_1.md)、[32分类审查](gate8_non_submit_api_review_v0_1.md)、[128超时审查](gate10_timeout_review_v0_1.md)。所有数据仍Engineering，不是Pilot/Formal、完整新版Q0、科学有效性或信息增益证据。

EP-G10-01候选/输入规则、EP-G10-02真实执行/资源排除记录、EP-G10-03选定G1一次可行集合均已完成本次缩减范围。新128/512无显式OOM或early EOS，无自动retry；128的分析失败作为历史工程异常保留。没有扫描OOM边界，没有证明稳定域，没有跨N1/G1共同域。原EP-G10-03“共同稳定范围”的历史措辞按已批准最小计划仅落实为选定G1可行点集合，统计稳定性仍属Pilot。

## 停点和最小下一步（7.102历史；当前见页首7.110）

本范围没有剩余证据缺口，不新增部署/重采/测试轮次。下一项是**本地整理N1模型V0/Vmarker/Vsync最小执行准备与已有显式流合同的接线依赖**，不重做平台资格，也不自动采集。N1在实际验证前不得宣称模型可行；G1三点可作为后续Pilot设计候选，但本轮不选repeat、不冻结阈值、不启动Pilot。

本次仅审计/文档提交；执行commit700f671与文档收尾commit分开。Gate7～9限定PASS保持；Gate10限定G1 PASS。Raw、旧报告、UNKNOWN/NOT_ASSESSED不变，D/Signature、Protocol Freeze及Formal不启动。当前用户无需服务器操作。
