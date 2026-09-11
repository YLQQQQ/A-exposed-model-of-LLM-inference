# ExposedPath S 同步语义层 v0.2

## 1. 本层回答什么

S 层回答的不是“哪些 GPU 活动与同步在时间上重叠”，而是：一个可观察的 Host 阻塞同步究竟等待哪些已提交、属于同一次推理调用、且位于其 CUDA completion scope 内的设备活动。输出是每个同步独立的 `W(s)`、semantic frontier、terminal、validity 和原因；本层不计算 A/B/D。

输入只能是 Canonical Raw v0.2。S 层不导入 SQLite，也不识别 Nsight 私有表名。输出为 `s_manifest.json` 与确定性压缩的 `s_sync_records.jsonl.gz`，schema 为 `contracts/s_layer_schema_v0_2.json`；已有目录拒绝覆盖。

## 2. ownership 与提交证据

设备活动通过唯一 CUDA correlation 找到 enqueue API，再用同线程、结构化、半开 NVTX 范围恢复 batched invocation 与 origin phase。Host blocking sync 使用其 runtime API 区间恢复 owner phase，并要求唯一结构化 sync identity 提供 origin、callsite 和 ordinal。同一 invocation 的 prefill 活动可以成为 decode 同步的依赖；跨 invocation 活动不能用于强归因。

活动进入同步候选只接受两种正向证据：`gpu_start < sync.host_start` 或 `enqueue.host_end <= sync.host_start`。enqueue 从同步入口之后才开始只用于证明它不是此前任务，不被当成提交证据；enqueue 跨越同步入口且 activity 尚未开始时保持 `SUBMISSION_ORDER_AMBIGUOUS`。

## 3. completion graph 与 W(s)

依赖边只来自同 stream 顺序、event record 捕获、stream wait event 和已声明的 legacy default-stream 规则。活动时间戳只用于确定同一语义流内部的顺序或描述状态，跨流时间重叠本身绝不建边。

- Stream sync：目标流在同步入口前的提交前缀，加上 event/default-stream 的可观察传递前驱。`streamWaitEvent` 自身作为目标流的 completion 节点；即使其后没有 consumer activity，被该 event 捕获的 producer 前缀也不会丢失。
- Device sync：目标 device 上此前提交且属于同一 invocation 的可观察任务。
- Context sync：目标 context 内此前提交且属于同一 invocation 的可观察任务。
- Event sync：使用 `eventSyncId` 精确关联 event record，恢复该 record 捕获的 stream 前缀；不按 eventId 或时间距离猜“最近记录”。

已经在同步入口前完成的语义前驱仍属于 `W(s)`；它在后续 B 中体现 hidden progress。无依赖路径的其他 stream 活动即使覆盖整个同步窗口也不会进入 `W(s)`。观察到 default stream 而 manifest 未声明 `LEGACY/PER_THREAD` 时 fail closed；legacy 模式保留 nonblocking stream 例外。

CUDA event 事实的解释依据 CUPTI 官方定义：CUDA event activity 的 correlationId 对应 event API，cudaEventSyncId 用于把同步记录关联到该 event 的最新 record。Nsight Systems 的 CUDA event trace 仍有版本和行为限制，因此真实 Q0 必须在目标 observation stack 上单独验证。[CUPTI Activity API](https://docs.nvidia.com/cupti/api/group__CUPTI__ACTIVITY__API.html)、[Nsight Systems User Guide](https://docs.nvidia.com/nsight-systems/UserGuide/)

## 4. terminal 与 validity

terminal 先从 `W(s)` 的语义最大节点求 frontier。frontier 唯一时直接选择；多个 frontier 只有在共享时钟域中存在唯一最晚完成者时才能选择；相同最晚完成时间按 0 ns 容差记为 `TERMINAL_TIE/AMBIGUOUS`。terminal 晚于同步返回为 `INVALID`。空且证据完整的 completion scope 是 `VALID_EMPTY`，不是缺失数据，也不会把已提前完成的活动误删成空集合。

原因按 Measurement Contract 的冻结优先级输出 primary/secondary；任何必需事实缺失产生的 `INVALID` 证据都不能被通用 ownership 歧义降级。依赖图先保留完整可观察前驱，再检查 ownership，不能预先删除外部 invocation。输入 identity/observation 已 ambiguous 时不尝试生成“看似合理”的 `W(s)`；旧 trace 可以生成 S 派生产物以验证链路，但记录保持 fail closed，不能升级为 Q0、Pilot 或 Formal 证据。

## 5. 当前验证边界

离线测试覆盖 stream/device/context/event、跨流 wait-event、completed-before、无关重叠、legacy/PTDS、nonblocking stream、提交竞态、跨 phase、invocation bleed、terminal frontier/tie/after-return、valid-empty、原因优先级和 Q0 核心 expected 对照。它们证明实现符合当前合成语义合同，不替代真实 CUDA/Nsight Q0；Gate 6 在获得 GPU 前仍为 `BLOCKED`。
