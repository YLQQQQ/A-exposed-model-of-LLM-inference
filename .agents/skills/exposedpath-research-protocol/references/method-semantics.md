# ExposedPath 方法语义

任务涉及测量模型、analyzer、trace 语义、Q0/N1/G1/G2 或研究 claim 时，读取本参考文件。

## 测量目标

ExposedPath 测量异步 Host-accelerator 执行如何转化为请求可见的 wall-clock exposure。它不会把 GPU 工作量、利用率或 API activity 重新定义为延迟贡献。

- **Activity Cost** 描述系统完成的工作，例如 kernel/API/MemOp 时长、次数、利用率及相关 activity metrics。
- **Request-Visible Exposure** 描述通过 synchronization 与 completion 行为，实际暴露在 request 或 phase wall-clock 中的部分。

一个长 activity 可能在 Host 开始等待之前已经大部分完成，因此被隐藏。一个长 synchronization 也可能只是 completion boundary 发生了迁移，而不是 request E2E 等量增加。

## 方法链

### Raw：执行事实

Raw 应保留可观察事实，但不能直接给出 dependency claim：

- Request/Prefill/Decode 和 invocation identity；
- CUDA API 与 synchronization record；
- kernel、Memcpy、Memset 和其他纳入分析的 GPU activity；
- context、stream、event、device、thread、process 与 correlation 标识；
- start/end timestamp 和 clock-domain 信息；
- profiler/schema/tool 版本以及 dropped-record 证据；
- manifest、固定输入 digest、workload、repeat、mode 与 run role。

缺失必需的 Raw 证据是一种 validity 结果，不能用零值代替。

### S：恢复 synchronization/completion 语义

对于每个 synchronization `s`，恢复：

- `W(s)`：根据 observation contract 和 CUDA completion semantics，在 `s` 可以返回前必须完成的 GPU activity 集合；
- terminal 证据：如果能够唯一观察，确定该同步何时具备返回条件的 activity 或 completion boundary；
- validity：trace 是否包含充分且不冲突的证据。

不得把 `W(s)` 定义为只包含与 sync 时间重叠的 activity，或只包含 sync 入口时仍然 pending 的工作。已经完成但仍属于语义 completion set 的成员，是测量 hidden progress 所必需的。

按照 sync 类型应用对应 scope：

- stream synchronization：相关 stream 及其中按序位于同步前的工作；
- device/context synchronization：相关 completion scope 中纳入分析的先行工作；
- event synchronization：event record boundary，以及必须先于该 event 完成的工作；
- 其他 synchronization 形式：只有其 completion semantics 和必需标识已经明确定义时才支持。

另一个 stream 上的并发工作不会因为 timestamp 重叠就自动成为 dependency。必须同时考虑 submission order、stream/context/event identity、correlation 和 CUDA 语义。

Validity 至少要区分 valid、invalid 与 ambiguous/unresolved。缺少 mapping 或标识、dropped records 影响 completion set、存在外部或无 ownership 的 activity、terminal 候选冲突、或同步类型不受支持时，必须 fail closed。

### A：request/phase wall-clock accounting

A 回答用户可见的 request 或 phase 时间去了哪里。各类别必须互斥，并在明确的误差容限内守恒于所纳入的 wall-clock window。

当前研究方案要求至少区分：

- Host path；
- CUDA submit API；
- CUDA non-submit API；
- device wait；
- 当证据不足以支持更强归因时，明确记录 residual、unattributed 或 invalid 部分。

不得把 Host path 称为“CPU busy”，也不得把无法解决的 synchronization 时间转换为已知 device wait 或已知 return tail。

### B：per-sync provenance

B 解释单次 synchronization 如何形成：

- sync 入口前已经隐藏完成的必需 activity progress；
- 与 sync 阻塞区间重叠的必需 progress；
- terminal identity 与 ownership 证据；
- 在可观察且有效时，terminal 完成后的 return tail。

B 面向单次 synchronization。除非另有明确定义的去重规则能够保证聚合有效，否则不得跨 synchronization 调用直接累加 B 行。

### D 与 Exposure Signature

`D_margin = A_device_wait - (A_host_path + A_cuda_api)` 是顶层导航信号，用于识别 Host/API 主导区域和 device-wait 主导区域；它不能证明硬件或软件根因。

Exposure Signature 把已经冻结的 A/B 维度组合成机制指纹，例如 Host path、submit/non-submit API、kernel/MemOp/mixed device wait，以及 hidden/exposed/terminal provenance。看到结果后不得重新定义 A、B 或 D。

## Phase boundary

Request、Prefill、Decode 和 TTFT label 必须说明其代表哪一种可观察 completion event。异步 launch 之后的 Host return 不会自动成为 device-complete 或用户可见边界。如果合同采用 synchronization、event、token transfer 或其他 observation point，应明确记录，并保持 Pass0 与 Pass1 一致。

不得让 N1 使用的人为 per-token synchronization 静默变成 G1 自然 workload 的定义。

## 证据问题

- **Q0——正确性：** 使用受控 CUDA 微程序和独立 oracle，验证 `W(s)`、terminal、validity、A/B、守恒和 fail-closed 行为。
- **N1——受控机制干预：** 改变 completion boundary，检验局部 wait、request E2E、A 以及 hidden/exposed provenance 是否按预期迁移。
- **G1——自然信息增益：** 在预定义的 input/output/batch、phase 和 platform 范围内，检验 Raw work 变化是否按比例、非比例或依赖 regime 地映射为 exposure。Prefill 使用绝对量，Decode 使用适当的 per-token 视角。
- **G2——决策增益：** 使用 eager 到 compile/graph 等真实优化，检验其相对常规指标是否具有额外的 held-out 决策价值。如果不存在额外决策价值，应收缩 claim。

## Claim 边界

当前核心 claim 是：在单 GPU、请求内部的范围内，把可观察执行映射为 request-visible exposure。增加平台可以检验稳健性，但不会自动扩展方法适用域。多 GPU、分布式 serving、并发 ownership、硬件根因归因、通用优化预测或替代硬件 profiler，都需要新的证据与语义定义。
