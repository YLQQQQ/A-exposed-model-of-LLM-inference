# Gate8 本地文件链接口状态 v0.2

> 7.40新增：[eager来源接线0.1](gate8_eager_source_alignment_v0_1.md)。显式model_setup可
> 在真实加载/初始化处记录stage，warmup/measured保留原identity，producer/input0.3、
> file-chain0.5只作Canonical Host-call诊断；不是S ownership或default/lifetime证明。
> 新stage诊断始终BLOCKED/NOT_ASSESSED；不改变下列旧入口和S/A/B/Derived资格。

> 7.39更新（2026-09-27）：本文件保留时间表示/旧文件入口历史。新增显式
> [closed-prior0.1](gate8_closed_prior_amendment_v0_1.md)使用producer/input receipt0.2、
> S0.3、A-B0.4、analysis0.5、file-chain0.4；Derived未支持新ownership版本而拒绝。
> 不替换旧入口、不追认旧Raw；仅窄连续nondefault域本地确定性验证，非模型/新Q0资格。
> 后续Route A已取消统一全capture认证前置，下方早期provider下一步不是当前待办。

2026-09-25；基线 `ac5f02c838ed2d866b11c0b5a510aa6f74811a27`。本轮完成时间表示及本地文件链实现与确定性验证，不部署服务器、不采集或重验旧证据。Gate7历史PASS/legacy-only限制保持，Gate8 NOT_RUN。

版本：package/analyzer `0.3.1`，adapter `exposedpath-gate8-adapter/0.2.0`；[时间表示amendment](gate8_time_representation_amendment_v0_1.md)，A/B及Derived `0.3.0`；D1/D2与Canonical/S原版本不变。第一批记录见[v0.1](gate8_local_implementation_v0_1.md)，其中signed/file-chain缺口由本记录取代。

## 本地文件入口与有向来源链

1. `runner.run_gate8_requests_to_files(output_dir=..., **request_arguments)`：复用实际runner，写实际pass ledger、host boundary ledger及最后的producer receipt；文件hash单向引用，不回填共享WMPC/Raw。Pass0/Pass1分别有自己的receipt，warmup/measured/FAILED/EXCLUDED保留。已存在输出在模型工作前拒绝。该API接受已加载model/resident输入，不是服务器模型加载或采集launcher。
2. `gate8_files.write_input_receipt(...)`：输入已存在的 `raw, sqlite, pass_identity, host_ledger, preflight, cuda_probe, wmpc_manifest, prompt, runner_source, producer_receipt, export_report`。按文件字节hash绑定shared WMPC、prompt、source及run/pass/attempt；核对producer receipt指向真实文件。export report显式适配当前`gate7_nsys_postprocess`字段：PASS、唯一成功attempt、exit0/process exited/no timeout、REP/SQLite hash和size；不执行export，不把export成功当零丢失。
3. `process_gate8_receipt(receipt, new_output, ...)`：重读并核验全部输入→新Canonical及device/finalized pass sidecars→原point anchors/host bytes/scope projection→完整性门→S bundle→A/B bundle→coverage→合格输入上的D/Signature。Canonical namespace来自UUID/PCI/PID/context，不按数字相等推断。
4. 真实默认入口始终UNKNOWN/BLOCKED，不写A/B、D数值。只有显式`synthetic_fixture=True`且两个通道的合成receipt形状/范围一致、全部计划request COMPLETE时，允许本地确定性计算，输出`SYNTHETIC_CALCULATION_ONLY`。A有unattributed/原因、B invalid/ambiguous、coverage分母不完整则不发布D。底层计算API不是科学验收入口。
5. `load_chain_result`：验证唯一最终索引、完整文件集合/大小/hash、run identity、analysis report、provenance及Raw lineage。新结果带 `provenance/` 小型原始metadata/source/prompt字节快照，不复制REP/SQLite/模型；原input receipt hash留在最终索引。Raw字节身份来自输入receipt，不能声称仅凭派生包又复算了未附带的Raw。

所有输入只读。新目录不覆盖；使用同文件系统独立staging，最终索引最后写且目录rename后才发布。失败/中断仅留下`.name-partial-*`诊断目录，不能用作完成回执、不能resume拼接；不自动删除历史/输入。hash顺序：共享输入→producer文件→export/receipt→Canonical/projection→S→A/B→coverage/Derived→最终索引；无自包含hash、无反向回填。

公共路径为相对路径/调用方配置。receipt内文件须在其目录允许范围内且不能别名复用；metadata保留原字节，包括历史路径，禁止据新路径重写旧证据。原始文件与本机快照不提交Git。

## 验证与剩余边界

tests-first红绿覆盖：缺版本策略/缺schema、负时间原点保护、实际S/A/B文件入口、scope lineage、未知版本和Derived upstream拒绝、producer落盘、input/result身份重标记、producer/export hash、UNKNOWN及失败request阻塞。补充边界/读写/原始字节不变性回归。跨零预期独立手算，不以实现生成oracle。运行时token/model替身及SQLite fixture均为合成；完整性正例counter也是合成，不是Nsight证据。

本地计算及文件入口可供后续集成；**不是已完成模型加载/pre-model admission、双pass实际采集/遥测/性能overhead和服务器launcher验收**。这些需要固定workload/环境与另行批准的执行方案，不借本地API绕过。WMPC字节身份可核验，不等于已复算模型权重/环境事实或真实Pass0/Pass1 parity。

采用逐层人工代码自审与CPU回归；研究skill限制下未创建子agent，不冒充独立审查签字。具体最终命令与结果在research_progress同次记录。

新Q0资格仍缺：新adapter/observation profile的23-case影响审查、身份/投影/负时间/hidden-terminal/跨phase/完整性负例回归，以及受影响目标栈真实Q0验证。历史Gate6 PASS不继承、不撤销。真实完整性provider仍UNKNOWN，见[调查及有界下一步](gate8_nsys_integrity_evidence_note_v0_1.md)。当前不要求部署/采集；先取得版本绑定的肯定证据说明，否则提交collector/证据政策的显式决策，不能再盲跑模型。
