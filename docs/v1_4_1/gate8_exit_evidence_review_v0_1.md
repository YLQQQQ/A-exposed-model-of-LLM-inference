# Gate8 A主线退出证据审查 0.1

2026-09-28；7.84。只读证据复核与计划收敛，不修订准入，不运行测试或实验。
依据是[route-a-execution/0.2 §1五项](gate8_route_a_execution_v0_2.md)，不是历史待办总数。
Gate7 PASS；限定受控资格保持；Gate8 NOT_RUN；旧attempt BLOCKED；UNKNOWN不改零。

## 1. 询证状态及本轮实际检查

[一次窄询证](https://forums.developer.nvidia.com/t/nsight-systems-2026-2-1-windows-scope-of-cuda-nvtx-warnings-associated-with-another-process/384556)
记录为**用户回传已发送，待回复**。本窗口未直接取得帖子正文或回复，不声称已核验厂商意见。
没有追加发送、附件、自动监控或服务器请求。此记录取代7.83的“未发送”，不是恢复泛化询证。

复用[7.82完整审计](gate8_isolated_attempt_audit_v0_1.md)与其本地隔离派生结果，本轮再次核对：
原ZIP 26487072 bytes，SHA256 `660b531f45bd768441c13757adddc57ee249911e0db24a7c80f62e69b70bf360`；
CRC通过，71文件与封存副本逐字节相同。70项原清单核验沿用7.82；不改Raw或报告。
直接用SQLite只读immutable查询NVTX row1–3、Runtime17431/17441/19143/20737、Sync346–349，
不用S/A函数复核原记录身份、顺序、returnValue及correlation。没有重复候选计算或新资格测试。

## 2. 实际退出清单（分项通过不等于Gate通过）

| 分类 | 对应退出条件与结论 | 依据/尚缺什么 |
|---|---|---|
| 已通过 | §1.3限定受控正例与拒绝反例；稳定公式历史资格按影响复用 | [7.71限定审查](gate8_bounded_qualification_review_v0_1.md)，不是全新版Q0或模型资格 |
| 已通过 | §1.1已观察的同run身份、三锚点、窗外成功drain事实 | 原NVTX三个payload的run/request/repeat/pass及globalTid一致；Runtime drain return0/corr61548→Sync346，end30162803099早于start30163654309；不证明不存在迟发工作 |
| 已通过 | §1.5封存、导出、状态层级与证据索引可复核 | ZIP/副本一致；profile/export成功但正式A空且BLOCKED；本审查不是EP-G8-04通过报告 |
| 可独立推进：本轮已关闭审查 | §1.2/4既有同步后缀及A候选的证据等级 | 三个sync相关原记录核对无冲突；双模式集合8/1906/3498及三窗A相等复用7.82。后者是同一算法条件自洽，不是独立模型oracle |
| 可独立推进：仍待目标平台验证 | 新预检Git binary修复 | f491d6e本地100项回归已有证据，服务器仍db9f028。486路径覆盖是事后核对，不追认有缺陷的运行时seal；无需重采整套Q0 |
| 可独立推进：仍缺证据 | §1.4同执行合同的开销对照 | 本包没有未profile同输入基线，不能从38.563s采集耗时或PROFILER_OVERHEAD事件推导request overhead；记录NOT_MEASURED，不填0。数值阈值仍留Pilot |
| 仅受warning作用域阻塞（在已声明支持域内） | §1.2/4可信request A发布 | 原四warning影响未界定；其余已观察条件及候选计算无新增阻塞不等于所有条件独立证明。该问题解除也不能补救旧seal或自动追认attempt |
| 随前项待结案 | §1.5 EP-G8-04最终退出报告 | 可先完成失败/存储/限制记录；不能以文档齐全填PASS |

存储事实：REP hash `98eca3d360959b24e48cc764f50e7cdcad172c6c99ad4b45aec7b85d2e0ce675`；
SQLite 1880064 bytes/hash `2d52d6dbb1253880e0c0a6776b7e65480128c97962bcd7f537182a5612913321`；
ZIP体积不是全部未压缩存储成本。可靠性仅记录本次target/profile/export成功、准入失败及历史失败原因，
不从repeat1估计稳定率。无采集重试/超时不等于科学排除为零。

## 3. warning门：事实、必要缺口与额外假设分开

条款定位：[质量amendment“最小质量门”](gate8_route_a_quality_amendment_v0_1.md)、
[限定依据“依据与限制”“诊断与unknown”“0.1实现合同”](gate8_engineering_sufficiency_amendment_v0_1.md)。
后者第86–90行明确规定“任何warning（含其它PID）”为IMPACT_UNBOUNDED；当前代码与此一致。

| 拒绝依据类型 | 本包事实与request影响 | 合同判断 |
|---|---|---|
| 已观察冲突 | 未观察到目标三边界/成功drain/身份冲突；四条warning是肯定的诊断记录，不是肯定的目标丢失记录 | “可见冲突拒绝”不应被改述为本包已证明全局损失。Git清单reader失败则是另一项真实预检缺陷 |
| 必需证据缺失 | row2/3/5/6关联52740：NVTX可能不全、无NVTX、CUDA启动可能异常、无CUDA；没有affected-scope或可用跨时钟区间 | “诊断与unknown”要求逐条处置有依据；OTHER_PROCESS不是OUT_OF_SCOPE。缺NVTX可能损害窗口，缺CUDA可能损害必要集合、终点及A类别；目前仅是可能，不能量化为局部gap |
| 保守支持域限制 | 0.1对任何warning统一拒绝，比“确定目标损失才拒绝”更保守 | 是明确批准的工程支持限制，不是工具已证明共享故障。当前没有足够证据应用例外，继续BLOCKED |
| 不应追加的无界要求 | 证明任何未知进程、任意未记录依赖、所有潜在共享故障绝不发生 | “依据与限制”已允许无未记录incoming依赖作为显式假设；不得另加全capture认证，也不能用该假设抹去已经出现的warning |

四类消息都没有当前可用的“只影响本PID”依据。无事件两类在确为无插桩辅助进程时可能是正常现象，
但其宿主及范围尚未证明；“might”两类也不等于已发生丢失。目标有事件不是完整性证据。
不再追查该PID，不再用同配置采集或来源记录尝试回答同一缺口。

仅提交协调讨论、**未实施**的有限语义选项：将“任意warning必拒绝”改为版本绑定的消息处置表，
允许在明确声明“此类进程局部注入失败不传播至目标”假设且有该build消息语义依据时，判OTHER_PROCESS_LOCAL；
这不是单凭PID不同放行。当前依据不足，不能给四条消息填LOCAL。若选择仅凭该假设接受而无外部依据，
必须显式amend支持域并承认未排除共享损失，不能称沿用0.1或原证据充分。
必要独立反例：不同PID但共享buffer损失仍拒绝；目标零事件与边界冲突拒绝；局部声明却出现目标correlation缺口拒绝；
正例须有版本匹配的局部故障说明、进程实例映射和完整目标条件。此处是预期，不新增测试或豁免。

## 4. 独立性与限定资格影响

真实原记录独立复核的是观测事实，不是丢失不存在。三窗duration为197087143/107045815/90041328ns；
三个Runtime同步均return0，与Sync347–349逐一correlation匹配，同context1/stream7；包含内部sync。
候选6171局部分类gap共4730533ns保留unattributed，不降低比例。三窗类别、双模式等价来自既有S/A计算，
不能以数值闭合证明归属；具体类别正确性的独立证据仍来自受控oracle及负例，而非模型自身。

从离线资格修复cb4b3b3到f491d6e的Git文件差异显示：runner、Canonical/S/A、
engineering_scope及受控oracle未变；不存在因此重跑完整Q0的依据。
改变的是模型入口/异常receipt、显式解释器接线、adapter来源记录、隔离预检/native设备和Git文件名读取。
这些由各自CPU负例和已回传目标平台身份检查覆盖；不继承为模型执行的科学资格。
最后Git binary修复尚未目标平台执行，只需后续合并批次的相关CPU检查，不需要GPU资格重采来测解码。
新增模型内部同步没有独立受控token数值oracle覆盖；已有真实correlation/scope检查与稳定stream规则提供条件依据，
不据此宣称所有Qwen算子均独立验真，也不另造一个全模型oracle作为Gate前置。

## 5. 机器状态一致性与最少后续动作

实际server_receipt=BLOCKED/“Machine report not accepted”；collection_report=
DIAGNOSTIC_COLLECTED_NOT_QUALIFIED/error=MODEL_A_SCOPE_BLOCKED；diagnostic_report=DIAGNOSTIC_COMPLETE；
producer=COMPLETE；engineering_a拒绝且a_records为空。层级不同但没有最终PASS。
collector当前诊断完成状态可保留exit0，即使error表示A拒绝；外层显式核验机器状态并阻塞。
因此exit0不能充当验收接口；未来消费必须同时核status/error/A准入，不能只看返回码。此轮不改代码。

唯一当前下一步：协调裁决上述**有限消息作用域依据/假设是否足以形成新版本处置规则**；
厂商答复是可选补充，未答复不阻塞本轮索引/资格影响/报告审查，但也不自动提供缺失依据。
若不能接受任何新假设且无新证据，明确暂停模型可信A，不以继续工程替代这个决定。

服务器剩余最多合并为一个后续授权批次，而非现在执行：固定经审查版本，先Git读取相关CPU复验；
只有warning范围路线已可执行时，才同批安排一次匹配的未profile/profile最小对照并统一回传，
同时消除新预检目标平台未验、profile开销缺基线及新准入实际接线三个不确定性。
失败即停，不重跑旧Gate/Q0、不自动重试、不为等回复先采一次。未给采集授权或部署包。
