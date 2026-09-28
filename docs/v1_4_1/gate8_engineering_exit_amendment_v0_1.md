# Gate8 限定 Engineering 退出 amendment 0.1

2026-09-28；版本 `G8-ENGINEERING-EXIT/0.1`；用户本轮明确批准。

**修订后 Gate8 = PASS，仅限 Engineering 执行链、可观测性接口和条件性 accounting 的工程可行性。**
四条指定外进程 warning 不影响目标 request 是未证实、可被反证推翻的支持假设；
真实 Qwen A 仍是条件性结果。此 PASS 不授予完整新版 Q0、模型科学有效性或 Formal 资格。

## 修订发生的时间及边界

这是**观察现有结果后**作出的阶段政策调整，不是原标准早已满足的声明。
研究设计 v7.1、实验协议 v2.1（Pre-Pilot）背景不变；冻结 MC、S/A/B 公式、warning 生产门均不修改。
旧 Route A 0.2 的可信准入要求不再作为本版“工程可行性退出”的前置，仍作为科学证据义务保留。
旧标准 Gate8 NOT_RUN、原 collection/engineering_a BLOCKED、空正式 a_records 保持历史原状。
本版建立独立的工程退出结论，不回写 machine report、不补 manifest、不追认 Formal 数据。
Gate9 可立即开展平台资格评估，不自动 PASS，也不自动进入 Pilot 或 Formal。

## 退出逐项判断（仅复用已有审计，不重新执行）

| 工程退出条件 | 已有依据 | 本版判定 |
|---|---|---|
| 固定执行内容、输入/设备/解释器、preflight 与实际目标关联 | [7.86收尾](gate8_conditional_closeout_v0_1.md)：36ed952、496路径Git binary/claim/final、两pass身份、执行exit0 | 满足 |
| 模型驻留、warmup/drain在窗外、completion三窗及实际同步可读可计算 | 同上原始边界/drain/内部sync/correlation；两默认流条件集合一致，支持假设明确 | 满足工程可行性，不证明记录无遗漏 |
| 受影响受控正确性及失效拒绝有独立证据 | [限定资格](gate8_bounded_qualification_review_v0_1.md)；[7.87分类修正](gate8_non_submit_api_review_v0_1.md)143+3相关回归 | 满足限定复用；不授完整新版Q0 |
| 条件性A可复算、具体归属及守恒，开销/存储/失败限制已报告 | 7.87三窗unattributed=0，其他类别/T不变；7.86一次配对+40.3414%，非统计开销结论 | 满足；不以清零为质量门，不算科学验证 |
| 封存、版本、lineage、失败记录和解释限制可追溯 | 7.86/7.87原件不变性审计、原BLOCKED及独立条件输出 | 满足 |

执行 commit `36ed952b57f20651dd290fc484d7b21fc7dbbfc4`；分类修正/离线分析 commit
`1733ff3291bb3c44ad8dd6a3d90a96015d644bc1`；本 amendment 的提交仅是阶段政策/文档身份。
原配对 ZIP SHA256 `3c90764357547cfb28de3c16bc624664e36d58565dfa4dcb02f1063e0294940f`；
新版条件输出 SHA256 `f0e81b5e3f1dba30f0e2c8b6a6d3f9542a361d4005b338b6905ae54696ec4928`。
直接引用既有核验，不声称本轮再次扫描原件。

## 假设适用、反证及 claim

沿用 `FOUR_OTHER_PROCESS_WARNINGS_NO_TARGET_IMPACT/0.1` 的四个精确消息及source/severity/
timestampType、同一OTHER_PROCESS global PID条件，见[原假设合同§1](gate8_conditional_pair_v0_1.md)。
当前证据只覆盖既定 Windows/RTX4090、CUDA12.4/Nsight2026.2.1.210、单模型eager/SDPA、
32/2、batch1、warmup1/repeat1及主要请求线程；不是所有其它PID warning 的一般豁免。
未来run不能仅因版本相同继承：仍需独立身份、边界、drain、同步、输入及诊断门，
不允许把新消息/目标或未知PID/额外诊断一并移出检查。本版不授权新run。

出现以下任一情况即停止援用该假设：适用版本资料证明这些消息可能源于共享故障且影响目标；
目标必要事件/边界/同步实际缺失或矛盾；关联进程存在影响目标的依赖；消息版本或作用域不再匹配。
疑似反证须记录为未解决冲突，不能按旧假设自动消解；确认反证则另版撤销受影响条件解释，
保留原历史记录及本次事后政策事实。来源可以是可核验工具说明、已有或后续独立受控证据，
不只限厂商答复；任何答复都不是自动验收。

允许 claim：执行/文件链可运行，支持域与假设下可计算互斥A，已观察到一次配对差异。
禁止 claim：warning已无害、已排除未记录依赖/共享采集故障、全capture零丢失、真实A已科学有效、
稳定overhead、完整Q0、信息增益或Formal资格。UNKNOWN、NOT_ASSESSED、trusted_a=false保持。
因此不删除科学证据义务，只把它与工程退出分开；[Gate9入口](gate9_platform_assessment_v0_1.md)承接。
