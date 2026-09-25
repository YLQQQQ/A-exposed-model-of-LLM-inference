# Nsight 2026.2 完整性证据核验 v0.1

**7.26当前覆盖：** 目标安装四份完整说明已审查并本地复核hash，仍无充分全capture CUDA/NVTX肯定完整性来源；不是工具不支持的断言。[调查收口及厂商草稿](gate8_nsys_vendor_inquiry_v0_1.md)为当前下一步，DRAFT_NOT_SENT；不重复安装搜索，UNKNOWN继续阻塞。下方7.25的B已完成。

**7.25更新：** 已重新直接核对历史SQLite全部69条diagnostics、metadata白名单和collector日志，并经官方Archives链接成功读取2026.2相关正文。当前结论与停止点、CUPTI DLL实际身份、scope/flush/API过滤歧义及新版Q0计划统一见[决策备忘录v0.1](gate8_integrity_q0_decision_memo_v0_1.md)。选择B（一次安装内容只读取证）；仍UNKNOWN，不运行Nsight。下方7.24访问失败是历史记录，不代表本轮仍无法访问。

2026-09-25，仅官方文档与既有本地产物只读核验；未启动Nsight GUI/CLI/export或服务器。结论：**目标2026.2.1.210采集的全会话肯定零丢失证据来源尚未确认，保持UNKNOWN及Gate8科学验收技术阻塞。** 不是声称工具绝不可能提供它，也不是要求更换collector。

## 核验范围与证据强度

- 经[官方Archives](https://docs.nvidia.com/nsight-systems/Archives/)定位[2026.2归档](https://archive.docs.nvidia.com/nsight-systems/2026.2/index.html)，避免用当前latest特性替代目标版本能力。
- [2026.2 Release Notes](https://archive.docs.nvidia.com/nsight-systems/2026.2/ReleaseNotes/index.html)描述记录容量限制的诊断、buffer问题及程序退出/flush相关数据损失风险。这些条款证明应保留损失线索，不提供“没有该警告就一定完整”的充分条件。其API tracing subset说明也要求adapter核验必需blocking API确实可观察，不据表非空默认universe完备。
- [2026.2 User Guide / Diagnostics Summary](https://archive.docs.nvidia.com/nsight-systems/2026.2/UserGuide/index.html#diagnostics-summary-view)说明诊断包含采集及后处理产生的信息/警告/错误，未在该节给出覆盖所有目标CUDA/NVTX记录的显式零丢失认证。
- [2026.2 Analysis Guide](https://archive.docs.nvidia.com/nsight-systems/2026.2/AnalysisGuide/index.html)的DIAGNOSTIC_EVENT有timestamp/source/severity/text/globalPid；本轮检索未发现通用全会话dropped计数合同。不能据“检索未发现”断言所有未公开或其他导出接口都不存在。
- CUPTI计数API只能作为后续证据来源调查线索；读取重置、scope和收集器生命周期必须核对，不能在Nsight旁注入reader并以最后一次0作为整次采集证明；本轮不授权这样做。

## 既有实物（历史输入，不作Gate8验收）

唯一Gate7 PASS输入SQLite SHA256：`005cf068bff99c36585a91343d8841d12bb2cad41a94bdc9bc1478045691877c`。用SQLite immutable/readonly读取全部表schema和69条DIAGNOSTIC_EVENT：未发现列名含drop/lost/loss的计数字段；有采集数量、CUPTI buffer/produced数量、flush说明，以及非目标进程NVTX等warning。列名搜索不是完整性证明。

两条CUPTI produced数量42863/42868与collected CUDA数量41975的口径/时点未被证明一致，**不能相减当丢失数**。12个NVTX collected记录也不能证明预期标记或全部CUDA事件无缺失。历史logs中的analyzer/acceptance输出不是collector肯定证明，Gate7已经明确接受unknown限制；不修改或追认它。

## 下一项最小动作（仍非实验）

### 本地文件链接通后的有界复核（7.24）

本次检索了官方Nsight Archives/2026.2条目及[CUPTI Activity API](https://docs.nvidia.com/cupti/api/group__CUPTI__ACTIVITY__API.html)。CUPTI dropped计数查询有读取后清零语义；这是计数器接口说明，不是Nsight 2026.2已向用户交付全会话证明的保证。目标2026.2 AnalysisGuide/ReleaseNotes归档URL本次工具访问失败；不把失败写成重新核验全文成功，也不以latest 2026.5说明替代目标版本。

本地只读核对历史8d64f75的`pass1_postprocess_report.json`字段：export attempt带REP/SQLite hash、exit/process_exited/timeout/validation_issues，报告PASS/analyzer_allowed=true。它适合导出lineage适配，**没有全会话CUDA/NVTX零丢失attestation字段**。旧SQLite schema及69条diagnostics的已核对事实见上文，本轮不重复解析后声称新科学证据、不重验旧attempt。

当前可明确判定为“现有可得材料无法满足肯定完整性合同”的观测能力阻塞，但不能断言厂商任何接口都不可能支持。停止重复相同网页/同一批diagnostics的循环搜索。剩余可行路径只有：

1. 优先取得**目标安装版本随附文档/字段说明或厂商答复**，需明确CUDA与NVTX、session/进程范围、final flush及所有计数读取/重置后的累积语义。可以由用户复制已有说明文件，无需运行Nsight/profile/export或模型；不能只回传exit0/无warning。
2. 若厂商确认该栈没有可用证明，另行裁决新collector/附加collector-side记录的研究与工程成本，包括互斥订阅、观测开销和重新Q0资格；当前不采用、不修改collector。
3. 或另行裁决证据政策缩减，仅允许明确UNKNOWN的工程诊断、继续禁止科学链验收；这将是质量规则amendment，当前没有降低门槛的授权，不执行。

当前推荐路径1；无需服务器部署或新采集。路径1无肯定结果前，UNKNOWN保持，不能以本地完整文件链通过代替它。

本地实现阶段再次核对官方 Nsight 文档和 CUPTI Activity API 资料，仍未获得可绑定目标 Nsight 全会话的肯定零丢失 provider。新增 `gate8_integrity.py` 只把真实 Nsight 入口映射为 UNKNOWN；允许验证未来 receipt 的形状/身份，不把此形状验证称为 collector authenticity 或 PASS。未运行真实 Nsight 或改写旧报告；本轮对历史 SQLite 仅以 immutable/read-only 查询设备表列名与 UUID 的 SQLite 存储类型（TEXT），用于确定 adapter 字段接口，不产生新历史 verdict。

主窗口先核对目标安装包已存在的帮助/本地文档或获取该版本官方字段说明，寻找可绑定session、通道、完整范围和最终状态的肯定counter/attestation；有来源再设计adapter，不能先设计一个永远填0的字段。若必须借助目标机材料，只请求用户复制已有帮助/诊断说明，不能附带profile/export/model命令。若资料仍不足，保持UNKNOWN并报告平台证据能力阻塞；更换collector、降低验收或扩大Q0均需另行明确授权。

现有规范的ZERO_CONFIRMED只是将来可接受证据的合同，不代表当前已取得。NVTX ledger双向匹配与CUDA完整性分别验收；已证明作用域之外的warning可保留并标其scope，但不能仅按PID不同豁免collector全局问题。
