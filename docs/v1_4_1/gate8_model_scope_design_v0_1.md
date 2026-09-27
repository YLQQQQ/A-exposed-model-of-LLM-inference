# Gate8 真实模型窄支持域方案 v0.1

状态：**只读设计／待准入裁决，不是 amendment 或执行授权**。以 main `1456b9c` 为审计基线。
Route A 限单平台、单模型 eager、串行 request；不改流、不截历史、不默认启动来源 profile。
Gate7 PASS；新 Q0/Gate8 NOT_RUN。旧 trace 不补写新 marker，不追认资格。

## 1. 现合同内的工程接线

依据：[D1/D2 执行计划](../superpowers/plans/2026-09-25-gate8-minimal-execution-plan.md)、
[closed-prior](gate8_closed_prior_amendment_v0_1.md)、
[Route A 质量门](gate8_route_a_quality_amendment_v0_1.md)。以下为待实现方案，不宣称接口已贯通。

| producer／原证据 | Canonical／scope 接线 | S/A/B 使用及拒绝条件 |
|---|---|---|
| producer0.4 五文件及 manifest、源码 hash | 显式版本 reader，校验 pass/request/repeat/attempt、文件 hash 和相互引用；共享 manifest 不放单个 repeat | 跨 pass、缺文件、部分写入拒绝；不能把0.4静默降级为旧 reader |
| `EXPOSEDPATH_BOUNDARY_V1` request-start、每 token host-readable point | 保留原 NVTX record、trace clock；按既有 D1 公式投影三窗，host clock 仅诊断 | 首末 token、顺序、唯一性不符拒绝整窗；projection 不是依赖边 |
| physical GPU UUID/PCI、logical mask、trace inventory/context/activity | 经 UUID/PCI 和进程/context 明确绑定，不按数字相等；保留各命名空间 | identity 冲突或无法证明唯一映射拒绝，不将 stream sentinel 当真实流 |
| stage ledger 与 `EXPOSEDPATH_STAGE_V1` | setup 保留原 stage owner、request_identity=null；warmup/measured 保留各自 request identity | 原 owner 不重标为当前 repeat；主线程 range 不覆盖 worker 的来源证明 |
| `load_tasks.json` 与 `EXPOSEDPATH_LOAD_TASK_V1` | 以 task ID、parent stage、native thread instance、source hash 关联同线程所包围 API，再用 correlation 绑定 activity | task 只是 HOST_JOB_ONLY；不能单凭 `.submit`、源码或区间重叠授予 GPU ownership；漏 task/失败/seal 未完保留缺口 |
| drain ledger 与原有 device-sync record | 唯一匹配 PID/TID、API、clock、成功和范围；保留其原位置 | drain 证明其 completion scope，不证明流寿命，不删除已完成 W 成员；窗口外 drain 不计入本窗 A |

原始 owner 与“当前窗口 membership”必须分字段表达。完整 physical W 保留历史前驱；
A 仅按当前窗口裁剪、互斥 union；B 保留 per-sync 完整历史，不跨 sync 求和。
现 `gate8_files.py` 的 stage-source 拒绝、`gate8_analysis.py` 的 target-source 拒绝、
closed-prior 的 nondefault／全 inventory 必须有 measured projection 限制，不能靠删检查接通。

## 2. 尚需明确批准的准入扩展（集中一项）

**建议批准设计一个新版本 target-scope admission：允许有证据的默认流及 setup/warmup 原 owner；
不要求它们伪装成 measured request。** 这是支持域／资格规则扩展，不改变 W、A/B 或 D 公式，
也不是本文件自动批准。当前 closed-prior0.1 未覆盖它。

默认流必须有可复查的 context、thread-instance、mode 和资源连续性证据。
单个 nullStreamId、当前 stream handle、一次 drain、无 create/destroy 行，均不单独足够。
known LEGACY 按既有阻塞流顺序；known PTDS 保留线程域及显式 event 边；mode 缺失或冲突继续拒绝。
源码版本可限定实际路径，但静态头文件／符号存在不能证明该次执行选中的模式。
目前尚无已验证的目标运行 mode 证据 adapter，不能把“未来 marker 会有”写成已解决。

历史来源至少追到目标同步必要闭包的可证明起点；setup 早期遗漏、context/thread 复用、
无法排除的前缀或 incoming event 使影响不可界定时拒绝窗口。能够证明无关的记录不强制
投影为 request；证明相关但局部缺证据则按 Route A 进入 unattributed，不能仅以 sync API
短区间冒充已证明影响范围。跨 owner event 的支持若没有相应证据与独立预期，仍在域外。

**不建议本轮另加“mode UNKNOWN 但两种模式算出同值就放行”或 A-only 资格。**
这需要独立等价性／发布合同，现有材料不能推出；不是上述准入扩展的隐含部分。

## 3. 最小可证伪检查及 Q0 复用

| 检查 | 独立预期／反例 | 历史证据可复用与新增边界 |
|---|---|---|
| 完整历史而非 drain 截断 | 已批准 bridge：两 owner hidden=25、三 owner=35，exposed=5、tail=10；本窗 A wait=5/residual=10 | 复用 closed-prior 人工预期；新 setup 原 owner／producer0.4 接线先文件链回归，真实来源绑定尚需目标资格 |
| 默认流模式敏感反例 | worker X=[0,10)、drain=[12,15)、main Y=[20,30)、s=[25,35)：LEGACY W={X,Y}，PTDS 无 incoming edge 时 W={Y}；hidden 分别15/5，不能因 exposed 同为5而合并 | 复用旧 PTDS、无关流、completed-before 的语义及 oracle 隔离；新 thread/context/mode adapter 必须单独验证，不能继承 Gate6 |
| 边界与身份失败 | 缺最后 token point、混 pass、thread-instance 冲突必须拒绝；stage 范围内另一线程 API 不能自动归属 | 复用历史 invocation bleed／external／multithread 反例原理；D1 trace point、五文件生命周期是新增资格项 |
| 局部与不界定缺口 | 有独立证明的局部影响只进入对应 unattributed；未知前缀影响闭包时拒绝可信整窗及 D/Signature | 复用 Route A 已批准三例和旧缺 correlation/event oracle；不要求重新采全部23例，也不把 synthetic 作为真实来源证明 |

手算默认流反例的前提必须分别构造成两种模式，不能把相同物理流 ID 强行套进两种世界。
[来源对齐§9](gate8_eager_source_alignment_v0_1.md)保留完整条件；
[Gate6 closeout](gate6_closeout_v0_1.md)只证明旧0.2.2栈的21个真实／2个合成案例。
旧公式、旧 reader 和已有失败处理做回归；新 owner/mode/marker 到 Raw/S 的真实接口必须新增资格。
不自动重采全部 Q0，也不自动沿用旧资格。

## 4. 最短下一步与未来采集能力边界

1. 用户仅裁决§2的支持域设计方向；主窗口随后在批准范围内写明确 admission 合同和
   producer0.4 实际文件链失败测试，不再追加宽泛调查、通用工具或默认流等价旁路。
2. 目标运行 mode 来源未证实时保持技术阻塞。先具体指出哪条模式证据缺失，不能把
   CPU stack profile 当唯一解决方案；已暂停的 source-probe 仍不执行。
3. 后续另行授权的一次最小受控采集，应同时验证新 marker→API/activity→原 owner、
   D1 三窗和模式敏感 oracle；必须先有模式／连续性证据方案。可验证接口可观测性，
   不能单凭一次成功证明所有历史无遗漏、真实模型低 unattributed、信息增益或新 Q0 全资格。
4. 受控资格通过后再申请单模型最小 workload；不以旧 Gate7 六 sync 诊断代替。

本轮未改生产代码／合同，未新跑测试或采集。仅文档检查；不更新服务器部署。
