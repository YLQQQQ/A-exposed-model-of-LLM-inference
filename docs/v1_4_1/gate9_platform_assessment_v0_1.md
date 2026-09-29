# Gate9 单平台资格评估 0.1

更新2026-09-29（7.89）。工作继续，**最终资格 verdict = BLOCKED：拟用于后续科学对照的版本/执行范围尚未形成绑定的资格结论**。
这不是继续因四warning拒绝当前工程结果；[新证据裁决](gate8_warning_evidence_review_v0_1.md)已关闭该工程阻塞。
历史首评见[12f61df版本](https://github.com/YLQQQQ/A-exposed-model-of-LLM-inference/blob/12f61df41b1666fbcc4d11128dffb6a4886896e8/docs/v1_4_1/gate9_platform_assessment_v0_1.md)，不继续沿用其中“只有无影响假设”的结论。

## 已完成且直接复用

| 原编号 | 现有证据 | 结论 |
|---|---|---|
| EP-G9-01 平台身份 | [7.86配对](gate8_conditional_closeout_v0_1.md)实际Windows/RTX4090、CUDA12.4/Nsight2026.2.1、解释器/代码/模型/输入/设备关联 | 完成封存运行身份评估；不冒称当前服务器无变化 |
| EP-G9-02 观测及资格 | [Gate6原Q0](gate6_closeout_v0_1.md)、[限定受控资格](gate8_bounded_qualification_review_v0_1.md)、[1733ff3分类回归与实物复算](gate8_non_submit_api_review_v0_1.md)、7.89用户回传答复 | 当前最小eager工程观测已有支持，四warning不再作为其否决理由；尚不能把限定资格改成所有后续科学执行方式均合格 |
| EP-G9-03 eager | 实际Qwen/eager/SDPA、32/2、batch1、warmup1/repeat1、三窗/drain/内部同步、必要集合与A | 当前最小点完成；不要求第二平台、compile/graph或G2 |
| EP-G9-04 结论 | 本次更新划清已取得资格的版本/构造与未来科学用途 | 初评继续有效但阻塞理由更新；不自动授Formal或完整新版Q0 |

既有支持域假设（无未记录incoming依赖等）和两默认流条件等价保留；不新增“不可能有任何共享故障”的认证任务。
UNKNOWN/NOT_ASSESSED、单次开销40.3414%及输出token值parity未记录等仍是解释限制，不自动成为新服务器待办。
厂商答复目前是用户回传，作者/日期/回复楼层未直接核实；补齐引用元信息有价值，但不是平台身份或本地工作的重新开工条件。

## 真正剩余的一项本地工作

为首个拟采用的最小N1/G1对照形成**版本/执行模式—资格适用表**：
从已验证36ed952执行、1733ff3分析及NULL-FIFO-D2H限定资格出发，明确自然token-ready与拟用intervention
是否改变completion/sync集合、backend、stream或ownership。已有边界/身份/分类负例直接引用，不重跑完整Q0。
这不是扩大参数扫描或要求先做Pilot；是把“这个受控构造/最小点已验证”对应到“下一科学对照究竟使用什么”。

- 若只复用相同执行/观测范围，签发窄域适用结论，不为了换文档commit采集。
- 若存在实际改变，只列受影响的一个必要命题及独立预期；没有明确区别性观察量就不提出服务器执行。
- 停止条件：跨出单GPU/主要请求线程/既定eager支持域，或出现新的未恢复同步/依赖；不能用本次官方解释豁免。
- 不提前冻结repeat/overhead/解释度阈值；不将现Engineering数据变成Formal。
  后续Formal仍需其版本化协议、数据用途和资格签发，不因本次文档审查直接授权。

当前没有已确认必须进行的新服务器验证，故不提供重采脚本。下一步由主窗口在本地完成上述一页适用表，
然后按实际差异决定是否有最小补证；不是等待厂商、追索旧PID或再次修改warning门。
Gate8限定Engineering PASS保持；Pilot、Formal、D/Signature本轮均不启动。
