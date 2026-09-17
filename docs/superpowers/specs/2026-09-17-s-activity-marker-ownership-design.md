# S 层跨线程 Activity Marker Ownership 修正规格

## 1. 状态与目的

状态：已批准并按测试先行方式实施；真实 GPU 单例尚未复验。

本规格属于 Gate 6 的 Engineering/Q0 调试，不是 Protocol Freeze，也不产生 Pilot 或 Formal 证据。它修正 S v0.2 中跨 Host 线程 device activity 的 invocation/phase ownership 证据缺口，不修改 CUDA completion semantics、`W(s)`、terminal、A/B 定义或 Q0 oracle。

真实 concurrent-host-marker diagnostic 已确认：`KERNEL_A` 的 device activity 与 `cudaLaunchKernel` correlation 唯一，`KERNEL_A` 结构化 marker 也在同一 worker 线程完整覆盖该 Runtime API；但现有 S ownership resolver 只读取 `kind=request/phase`，忽略 `kind=marker`，因此把 activity 判为 `INVOCATION_BOUNDARY_INVALID`。立即结束的 `WORKER_KERNEL_MEMOP` marker 不覆盖 API，不能成为 ownership 证据；将它扩展为覆盖 launch 还会与 `KERNEL_A` 同时成为 Q0 activity-label 候选，造成标签不唯一，所以不采用该方案。

## 2. 术语与分层边界

- **窗口范围**：`kind=request/phase` 的结构化 NVTX range。它们是 A 层 request/phase 窗口的唯一来源。
- **Activity ownership marker**：`kind=marker`、与 enqueue API 同线程并完整覆盖该 API 的结构化 NVTX range。它只证明该 device activity 属于哪个 invocation/phase，不创建 A 窗口。
- **Activity label marker**：带稳定 `callsite_id` 的 activity marker。Q0 仍要求每个真实 activity 对应唯一 covering label marker。

同一 `KERNEL_A` marker 可以同时承担 activity label 与 S ownership 证据，但这两种用途由不同校验规则独立判定。marker 不证明 CUDA dependency；activity 是否进入 `W(s)` 仍由 correlation、submission order、context/stream/event 和 synchronization completion semantics 决定。

## 3. 冻结规则

S 只在 device activity 已唯一关联一个 enqueue Runtime API 后，才评估 marker ownership。一个 marker 成为合格证据必须同时满足：

1. `kind=marker`，且 `global_tid` 与 enqueue API 相同；
2. 使用半开区间完整覆盖 API：`marker.start <= api.start` 且 `api.end <= marker.end`；只有相交或位于 API 之前均不合格；
3. `experiment_id/wmpc_id/run_id/run_role/pass_id/request_id/repeat_id/phase/callsite_id` 完整、非空；NVTX `text` 中的 `EXPOSEDPATH_JSON_V1` payload 必须可重新解析，并与 Canonical `structured_identity` 完全一致；
4. 所有覆盖 API 的合格 ownership 候选必须指向同一 invocation tuple；所有非 `full_request` phase 声明必须一致；
5. activity ownership 与目标 physical sync 的 invocation identity 仍须通过现有 `ownership_supported()` 检查。

判定规则：

- 同线程、完整覆盖、相同 invocation 与相同 phase 的一个或多个候选可得到 `VALID`；callsite 不属于 invocation tuple，不能仅因 callsite 不同就改变 ownership，但 Q0 label 恢复仍独立要求唯一 covering label。
- 覆盖 API 的候选若缺少必需字段、结构化 payload 不完整或不一致，结果为 `INVALID/INVOCATION_BOUNDARY_INVALID`，不能因为同时存在一个合法 marker 而忽略坏证据。
- 覆盖 API 的候选若声明不同 invocation tuple，结果为 `AMBIGUOUS/INVOCATION_OWNERSHIP_AMBIGUOUS`。
- 同一 invocation 下出现冲突 phase，结果为 `AMBIGUOUS/PHASE_OWNERSHIP_AMBIGUOUS`。
- 非同线程或时间上与 API 完全分离的 marker 不是 ownership 候选；它既不能证明 ownership，也不能凭时间接近被推断为 ownership。同线程 marker 若与 API 发生部分相交，或在 API 结束前开始但缺失结束边界，则属于不完整 ownership 证据，必须 `INVALID/INVOCATION_BOUNDARY_INVALID`，不能被另一个合法 marker 遮蔽。
- 找不到合格 request/phase range 或 activity marker 时，继续返回 `INVALID/INVOCATION_BOUNDARY_INVALID`。

## 4. 实现范围

只为 `_normalize_activity()` 增加 activity-specific ownership resolver；不得全局放宽现有 `_phase_ownership()`。因此：

- `_normalize_sync()`、event record ownership 和 physical sync identity 规则保持不变；
- `ab_inputs._discovery_result()` 仍只让 `request/phase` 创建 A 窗口；
- A/B schema、计算公式、validity 传播、Q0 oracle/evaluator 均不修改；
- `run_kernel_memop()` 保持 concurrent-host、512 MiB H2D、10 ms kernel、两个既有 nonblocking stream 与原 `S_DEVICE`；`WORKER_KERNEL_MEMOP` 继续是 API 前立即结束的 marker，不扩展为外层 covering range；
- 不增加 CUDA query、event 或 synchronization，不建立 r11。

## 5. 正反例测试设计

### 5.1 S 单元测试

先写下列失败测试，再实施 resolver：

1. **正例：跨线程 activity marker。** coordinator 的唯一 request/decode 在线程 A；线程 B 的 `KERNEL_A` marker 完整覆盖唯一 correlated launch API，identity 与目标 sync 一致。预期 activity ownership=`VALID`、origin phase=`decode`，并可按既有 DEVICE completion semantics 进入 `W(S_DEVICE)`。
2. **正例：相同 ownership 的嵌套 marker。** 多个 covering marker 的 invocation tuple 与 phase 完全一致。预期 ownership 不因嵌套本身变为 ambiguous。
3. **回归：request/phase 路径不退化。** 原同线程 request/phase fixture 的 ownership、origin phase 与 range IDs 保持不变。
4. **反例：marker 在 API 前结束。** 使用真实 diagnostic 的相对关系构造 fixture。预期 `INVALID/INVOCATION_BOUNDARY_INVALID`。
5. **反例：仅部分相交或线程不同。** 均不得成为正向证据；部分相交与合法 marker 并存时仍须 boundary invalid，错线程 marker 不污染目标线程。
6. **反例：未闭合，或覆盖但 identity 不完整/payload-cache 不一致。** 即使另有合法 marker，也必须 fail closed 为 invalid。
7. **反例：两个 covering marker 的 request/repeat/run 等 invocation 字段冲突。** 预期 `AMBIGUOUS/INVOCATION_OWNERSHIP_AMBIGUOUS`。
8. **反例：同 invocation、不同 phase。** 预期 `AMBIGUOUS/PHASE_OWNERSHIP_AMBIGUOUS`。
9. **反例：activity 与 sync 属于不同 invocation。** marker 本身合法也不能进入目标 wait-set，继续触发现有 invocation-bleed/ownership 拒绝逻辑。

### 5.2 分层与 Q0 回归

1. marker-only 输入不得创建任何 A request/phase 窗口；已有 `WINDOW_DISCOVERY_INVALID` 与 worker-marker/A-window 回归必须继续通过。
2. Q0 real label 恢复必须仍只得到 `KERNEL_A` 一个 covering callsite；新增 resolver 不参与或放宽 label selector。
3. `run_kernel_memop()` 源码回归继续保证唯一 coordinator request/decode、原并发提交、一个 `S_DEVICE`、sync 早于 worker join、无新增 CUDA query/event/sync。
4. 合成集成 fixture 应得到 `W(S_DEVICE)={KERNEL_A,MEMCPY_B}`、两者 origin phase 均为 decode；oracle 文件和 expected 不修改。
5. 运行 S 定向测试、A 窗口/ownership 边界、Q0 全套、合同/边界检查、CUDA 编译测试与全仓 pytest。真实 GPU diagnostic 只能在这些检查通过并生成新 commit/bundle 后，以全新 run-id 执行。

## 6. 完成条件与停止条件

实现完成只表示新的 Engineering analyzer 候选可进入单例复验，不表示 Gate 6 或 Q0 通过。只有全新 KERNEL-MEMOP diagnostic 同时满足真实 overlap、`mixed_ns>0`、terminal=`MEMCPY_B` 与 `REAL_CASE_PASS`，才允许讨论建立 r11。

若 marker ownership 修复后仍出现 ownership ambiguity，不得继续叠加 microbench marker；应保存失败现场并重新审查候选集合及 identity 冲突。任何需要改变 oracle、A/B 定义、activity/sync 标签或 completion semantics 的发现，都必须停止本方案并单独决策。
