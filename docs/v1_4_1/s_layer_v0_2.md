# ExposedPath S 同步语义层 v0.2

## 1. 本层回答什么

S 层回答的不是“哪些 GPU 活动与同步在时间上重叠”，而是：一个可观察的 Host 阻塞同步究竟等待哪些已提交、属于同一次推理调用、且位于其 CUDA completion scope 内的设备活动。输出是每个同步独立的 `W(s)`、semantic frontier、terminal、validity 和原因；本层不计算 A/B/D。

输入只能是 Canonical Raw v0.2。S 层不导入 SQLite，也不识别 Nsight 私有表名。输出为 `s_manifest.json` 与确定性压缩的 `s_sync_records.jsonl.gz`，schema 为 `contracts/s_layer_schema_v0_2.json`；已有目录拒绝覆盖。

## 2. ownership 与提交证据

设备活动通过唯一 CUDA correlation 找到 enqueue API，再用与该 API 同线程、完整覆盖 API 的结构化半开 NVTX 范围恢复 batched invocation 与 origin phase。普通同线程路径使用 `request/phase` 范围；跨 Host 线程提交允许使用完整且一致的 `kind=marker` activity marker 作为 activity ownership 证据。marker 的 NVTX text payload 必须可重新解析并与 Canonical 缓存 identity 完全一致；缺字段、未闭合、与 API 部分相交、identity/phase 冲突继续 fail closed，且不能被同时存在的合法 marker 遮蔽。marker 的 7 字段 invocation identity 还必须对应**唯一** matching `kind=request` 范围，并按时间包含判定归属：marker/API 完整位于该 request（声明 phase 时还须完整位于该唯一 matching phase）内才是 current-invocation ownership，request/phase 范围可以位于另一 Host 线程。若 identity 指向当前 request、但 marker/API 与该 request 完全不相交且整体位于其**之前**，而 device activity 延伸进入该 request/sync scope，则该活动是 `PROVEN_EXTERNAL_TO_REQUEST`，判 `EXTERNAL_OWNERSHIP_IN_SCOPE` 并 fail closed；部分相交、整体位于 request 之后、zero/multiple matching 一律 `INVOCATION_BOUNDARY_INVALID` / `INVOCATION_OWNERSHIP_AMBIGUOUS`，不得按 `request_id` 文本猜测。该 marker 只证明 device activity 的 invocation/phase 归属，不能创建 A 窗口，也不能单独建立 dependency。Host blocking sync 的第一条 ownership 路径仍是其 runtime API 所在的 request/phase 区间，并要求唯一结构化 sync identity 提供 origin、callsite 和 ordinal；完整覆盖该 sync runtime API、同线程、payload 可重解析且与缓存 identity 精确一致的 `kind=sync` structured marker 另有一条更严格受 provenance 约束的 fallback，可在其 marker/API 区间被 identity 相同且唯一的 matching request（以及声明的唯一 matching phase）时间包含时，**跨 Host 线程**传播 `request_id`、`repeat_id` 与 `sync_owner_phase`。`cudaEventRecord` 的 event ownership 使用同一 marker 规则；`cudaStreamWaitEvent` 是 dependency edge，不需要 marker。同一 invocation 的 prefill 活动可以成为 decode 同步的依赖；跨 invocation 活动不能用于强归因。conflict / duplicate / partial marker 继续 fail closed。

> **Amendment 注记（2026-09-19）**：上一段由 Gate 6 Unified Marker Ownership amendment（`docs/v1_4_1/gate6_marker_ownership_amendment_v0_1.md`）修订：原有「Host blocking sync 只使用其 runtime API 所在的 request/phase 区间恢复 owner phase」的表述不再是最完整的规则，新增同线程 trusted structured marker 的跨线程 ownership 传播 fallback 与 activity marker 的 request 时间包含/external 判定；同线程路径与该节其余 fail-closed 规则保持不变。本注记只是文档级 provenance，`s_layer_schema_v0_2.json`、`exposedpath-s-layer/0.2.0` 与 `sync_semantics_registry_v0_2.json` 均未改变；变更后的 analyzer 语义由 package `0.2.1` 标识。

活动进入同步候选只接受两种正向证据：`gpu_start < sync.host_start` 或 `enqueue.host_end <= sync.host_start`。enqueue 从同步入口之后才开始只用于证明它不是此前任务，不被当成提交证据；enqueue 跨越同步入口且 activity 尚未开始时保持 `SUBMISSION_ORDER_AMBIGUOUS`。若候选 activity 缺少唯一 correlation/ownership，即使提交顺序同时不明，也必须保留 `MISSING_ACTIVITY_CORRELATION/INVALID`，不能被较弱的提交歧义覆盖；只有 enqueue start 已明确位于同步入口之后时，才可作为 definitively post-sync 排除。

## 3. completion graph 与 W(s)

依赖边只来自同 stream 顺序、event record 捕获、stream wait event 和已声明的 legacy default-stream 规则。活动时间戳只用于确定同一语义流内部的顺序或描述状态，跨流时间重叠本身绝不建边。

- Stream sync：目标流在同步入口前的提交前缀，加上 event/default-stream 的可观察传递前驱。`streamWaitEvent` 自身作为目标流的 completion 节点；即使其后没有 consumer activity，被该 event 捕获的 producer 前缀也不会丢失。
- Device sync：目标 device 上此前提交且属于同一 invocation 的可观察任务。
- Context sync：目标 context 内此前提交且属于同一 invocation 的可观察任务。
- Event sync：使用 `eventSyncId` 精确关联 event record，恢复该 record 捕获的 stream 前缀；不按 eventId 或时间距离猜“最近记录”。同一个 `eventSyncId` 必须且只能对应一条 record，并且 record 与 event sync/stream wait 的 `eventId/context/device` 必须一致；缺失、重复或冲突均按 `MISSING_EVENT_RECORD/INVALID` fail closed。

已经在同步入口前完成的语义前驱仍属于 `W(s)`；它在后续 B 中体现 hidden progress。无依赖路径的其他 stream 活动即使覆盖整个同步窗口也不会进入 `W(s)`。观察到 default stream 而 manifest 未声明 `LEGACY/PER_THREAD` 时 fail closed；legacy 模式保留 nonblocking stream 例外。已由 enqueue start 明确证明发生在当前同步之后的 default/阻塞流活动，不参与该同步的 legacy 建图，也不能以未来的 enqueue overlap 污染较早同步。

CUDA event 事实的解释依据 CUPTI 官方定义：CUDA event activity 的 correlationId 对应 event API，cudaEventSyncId 用于把同步记录关联到该 event 的最新 record。Nsight Systems 的 CUDA event trace 仍有版本和行为限制，因此真实 Q0 必须在目标 observation stack 上单独验证。[CUPTI Activity API](https://docs.nvidia.com/cupti/api/group__CUPTI__ACTIVITY__API.html)、[Nsight Systems User Guide](https://docs.nvidia.com/nsight-systems/UserGuide/)

## 4. terminal 与 validity

terminal 先从 `W(s)` 的语义最大节点求 frontier。frontier 唯一时直接选择；多个 frontier 只有在共享时钟域中存在唯一最晚完成者时才能选择；相同最晚完成时间按 0 ns 容差记为 `TERMINAL_TIE/AMBIGUOUS`。terminal 晚于同步返回为 `INVALID`。空且证据完整的 completion scope 是 `VALID_EMPTY`，不是缺失数据，也不会把已提前完成的活动误删成空集合。

原因按 Measurement Contract 的冻结优先级输出 primary/secondary；任何必需事实缺失产生的 `INVALID` 证据都不能被通用 ownership 或 submission 歧义降级。这一规则同时适用于同步直接 scope、event record 捕获前缀和 legacy default-stream 传递路径，而不是只在最终 `W(s)` 成员上检查。依赖图先保留完整可观察前驱，再检查 ownership，不能预先删除外部 invocation。输入 identity/observation 已 ambiguous 时不尝试生成“看似合理”的 `W(s)`；旧 trace 可以生成 S 派生产物以验证链路，但记录保持 fail closed，不能升级为 Q0、Pilot 或 Formal 证据。

Q0 observation 已唯一恢复目标 request 时，Canonical 仍会保留 request 结束后的 harness 尾部同步。若这类记录没有唯一 runtime 映射，S 不补造 Host API 时间或 ownership，而是输出 `INVALID` 行、空 `W(s)` 和空 terminal；无 Host 时间的行按稳定 sync identity 排在有时间记录之后。A 只忽略同时满足“无 Host 时间、无 request ownership、S=INVALID”的行，B 则保留一一对应的 `B_INVALID` 行并令时间字段为 `null`。该规则只保证目标 request 不被外部 harness 污染，不会放宽 request 内同步的 fail-closed 条件。

## 5. sync universe 成员判定（Gate 6 Sync Projection Amendment v0.1）

S 的 semantic sync 集合由 sync registry 的 `universe_class`（及其导出的 role）唯一决定，不由 CUPTI 是否产生 `CUPTI_ACTIVITY_KIND_SYNCHRONIZATION` 行决定：

| registry role | 进入 S semantic sync | 说明 |
| --- | --- | --- |
| `HOST_BLOCKING_SYNC` | 是 | 现有 stream / device / context / event synchronize 路径 |
| `UNSUPPORTED` | 是 | 有 mapped `cuda_sync` 行时该 physical 行是唯一权威；否则按 API-backed 规则构造 |
| `NON_SYNC` | 否 | 只作为 A 的非提交事实与 `q0_real` 的 `non_sync_api_labels` 证据 |
| `DEPENDENCY_EDGE` | 否 | 只作为设备依赖边（`dependency_events` 路径） |
| `UNCLASSIFIED` | 维持现状 | 继续 `UNCLASSIFIED_CUDA_API` fail closed，既不合成分解也不静默丢弃 |

对 role 为 `UNSUPPORTED` 且 Canonical 中不存在 `runtime_record_id == record_id` 映射行的调用，S 由「runtime API 的完整调用区间 + 唯一权威 `kind=sync` structured marker」构造 deterministic API-backed semantic sync：`sync_id` 固定为 `cuda_api_sync:{source_table}:{source_rowid}`，`host_start_ns`/`host_end_ns` 取 runtime API 区间，`request_id`/`repeat_id`/`sync_owner_phase` 由唯一包含该区间的 request/phase 范围与 marker identity 联合确定，`callsite_id`/`sync_origin`/`sync_ordinal` 只来自该唯一权威 marker，device/context/stream/event identity 为 `null`（该 `sync_kind` 按合同整段 fail closed）。marker 完全缺失时不构造记录、不伪造同步事实；marker 重复、仅跨线程或只部分相交时仍构造确定性记录，但身份不可用并输出 `INVOCATION_BOUNDARY_INVALID`。成员判定与去重由 `sync_semantics.build_semantic_sync_candidates()` 单点实现，S 层与 A/B loader 共用同一 helper，禁止按 case id、API 名或 oracle expected 特判。

`NON_SYNC` 的排除是成员判定而非 reason suppression：它仍由 A 层与非同步标签路径继续承担，不得通过删记录让任何事实消失。A/B 的 correspondence 与 S 必须给出同一集合，缺、多、重复或 identity 冲突一律 fail closed。

> **Amendment 注记（2026-09-20）**：本节由 Gate 6 Sync Projection Amendment v0.1（`docs/v1_4_1/gate6_sync_projection_amendment_v0_1.md`）引入；`s_layer_schema_v0_2.json`（仍为 `exposedpath-s-layer/0.2.0`）、`sync_semantics_registry_v0_2.json` 与 Measurement Contract 均未改变。变更后的 analyzer 语义由 package `0.2.2` 标识，`0.2.1` 及更早 run 的 S/A-B 产物不得与本版本混用。

## 6. 当前验证边界

离线测试覆盖 stream/device/context/event、event record 唯一性与 scope 冲突、跨流 wait-event、completed-before、无关重叠、legacy/PTDS、nonblocking stream、提交竞态、缺失 correlation、跨 phase、invocation bleed、跨线程 activity marker 的同线程/完整覆盖/identity 完整性及冲突判定、terminal frontier/tie/after-return、valid-empty、原因优先级和 Q0 核心 expected 对照。事件和 wait 前缀查找已经按 context/stream 建立索引，同 scope 结果带缓存；event/default-stream 密集型真实 trace 的规模性能仍需在 Engineering Pilot 单独验收，不能由合成测试推断。上述离线测试只证明实现符合当前合成语义合同，不替代真实 CUDA/Nsight Q0；真实 Q0 已于 2026-09-20 在冻结目标栈（Windows + RTX 4090 + CUDA 12.4.131 + Nsight 2026.2.1）通过 Gate 6（`q0-win-4090-20260920-gate6-final-04`，package/analyzer `0.2.2`），见 `docs/v1_4_1/gate6_closeout_v0_1.md`。
