# ExposedPath Measurement Contract v0.2

**状态：Engineering / Pre-Pilot；Gate 1 合同。** 本合同冻结“测量对象怎样定义、证据不足时怎样拒答”，不证明 analyzer 已经正确实现，也不代表 Q0、Pilot 或 Protocol Freeze 已通过。

## 1. 合同结论与边界

ExposedPath 测量的不是 GPU 做了多少工作，而是异步活动经过同步和完成边界后，有多少时间真正暴露在 Request、Prefill 或 Decode 的墙钟上。方法链固定为 `Raw -> S -> {A, B} -> D / Exposure Signature`：Raw 保留事实，S 恢复完成依赖，A 解释请求时间去了哪里，B 解释单次同步为何等待，D 和 Exposure Signature 只做派生导航。

核心范围保持为单 GPU、单次 batched inference invocation 内的纯模型推理。Token ID 对 Host 可读之后的反分词、文本拼接、协议封装、网络、前端显示和外部消费者处理全部排除。Batch 大于 1 时，owner 是整次 batch invocation，不把 A/B 反事实分摊为单样本因果开销。

以下内容不由本合同声称：多 GPU 或分布式 serving 的 ownership、完整 CUDA 因果图、CPU busy time、硬件根因、可实现 speedup 上界和通用性能预测。

## 2. 合同文件及唯一职责

- 本文是中文语义正文，解释每条规则为什么存在及其输入、处理和输出。
- `contracts/measurement_contract_v0_2.json` 是 phase、S、A/B、D/Signature 和原因码的机器事实源。
- `contracts/sync_semantics_registry_v0_2.json` 只负责 API 属于哪类同步、是否支持、completion scope 和必需证据。
- `contracts/measurement_contract_test_map_v0_2.json` 只负责合同规则与验证案例的对应关系；Q0 的独立 expected/oracle 在 Gate 2 另行建立。
- `exposedpath_v141.contract` 只校验三份 JSON 的版本绑定、唯一性和覆盖完整性，不实现测量算法。

旧 `analysis/`、`exposedpath/`、历史 trace 和旧结果均不是本合同的实现证明。

## 3. 时间、窗口与身份

所有语义时间使用整数纳秒，区间统一为半开区间 `[start,end)`。成员关系和 terminal 身份不使用经验时间阈值：`semantic_ordering_tolerance_ns=0`，`terminal_tie_tolerance_ns=0`。Pilot 以后可以冻结“数值比较误差容差”，但该容差不得反向改变 `W(s)` 成员或 terminal 身份。

每个同步至少贯通 experiment、WMPC、run、data role、pass、request、repeat、phase、callsite、origin 和 ordinal。自然 Token-ready 同步还必须记录 token index 与完成机制；N1 人为同步还必须记录 intervention variant 与 intervention ordinal。

## 4. Request、Prefill、Decode 与 Token 就绪

### 4.1 可观察完成点

`request.start` 位于固定输入张量已驻留目标设备、请求前 drain 已返回之后，并紧邻首次 Prefill 模型调用之前。该 drain 不进入请求窗口。

`token[i].host_readable` 表示该次 batched invocation 的第 `i` 个生成 Token ID 已完成必要设备计算，并在 Token-ready 阻塞操作返回后能够由 Host 读取。它不要求 Token 已转成文本或已经发送给外部用户。

### 4.2 半开区间

- `Prefill = [request.start, token[0].host_readable)`，包含首 Token 选择和使首 Token ID 对 Host 可读所需的自然完成等待。
- `Decode = [token[0].host_readable, token[N-1].host_readable)`；当固定输出数 `N=1` 时，这是合法空区间。
- 第 `i>=1` 个 Decode step 为 `[token[i-1].host_readable, token[i].host_readable)`。
- `Full Request = [request.start, token[N-1].host_readable)`。

固定输出实验若发生 early EOS，必须保留 attempt 与实际输出数并按运行协议排除，不能把不同 Token 数静默混入同一 workload。

## 5. 自然同步、N1 干预与双 Pass

流式推理为了取得每个 Token ID 而发生的完成等待是 `natural_token_ready`，属于 G1 的自然推理行为。N1 为改变完成路径而额外插入、删除或移动的同步是 `n1_intervention`。只增加标记但不改变同步的版本是 `non_sync_marker`。三类身份不可混用，自然同步不能被重新标成干预，删除自然同步后的非流式路径也不能称为自然 G1。

Pass0 与 Pass1 必须使用相同输入、生成控制流、Token-ready 操作和同步操作。Pass1 只增加 NVTX 标记与 Nsight profiler；主时延来自 Pass0，机制证据来自 Pass1。两者不一致时，当前 run pair 无资格进入后续分析。

## 6. Physical blocking sync universe

支持矩阵不是按函数名中的 `stream` 或 `event` 猜测。每个 CUDA API 必须先经 registry 分类：

| 类别 | v0.2 处理 |
| --- | --- |
| Runtime/Driver stream synchronize | 核心支持，恢复目标 stream 的可观察传递前驱闭包 |
| Runtime device synchronize | 核心支持，恢复当前 runtime device 上此前请求的、可观察且 ownership 合法的任务 |
| Driver context synchronize | 核心支持，恢复当前或显式 context 中此前请求的任务 |
| Runtime/Driver event synchronize | 核心支持，恢复同步调用可见的最近一次 event record 所捕获的状态 |
| event record、stream wait event | 作为设备依赖边，不当作 Host blocking sync |
| 同步 copy 或依参数而阻塞的 API | 属于同步 universe，但 v0.2 不恢复 scope，完整调用区间 fail closed |
| event/stream query | 非阻塞查询，不建立 `W(s)` |

潜在阻塞但未匹配 registry 的 API 输出 `UNCLASSIFIED_CUDA_API`，不能静默当成普通非同步 API。

## 7. 从 completion scope 恢复 W(s)

### 7.1 提交证据

只有满足以下任一条件，活动 `e` 才能被证明在同步 `s` 之前进入可排序执行域：

`submission_proven(e,s) := e.gpu_start_ns < s.host_start_ns OR enqueue(e).host_end_ns <= s.host_start_ns`

它不声称知道命令物理到达硬件队列的时刻。enqueue 与 sync 相交、activity 又尚未开始时，结果为 `SUBMISSION_ORDER_AMBIGUOUS`。不得使用 enqueue start、correlation 存在性、固定回看窗口或时间重叠代替提交证明。

### 7.2 依赖图

可观察依赖边仅包括：同 stream 顺序、event record 捕获、stream wait event，以及 registry 支持且 manifest 已声明模式的 default-stream 顺序。时间重叠只描述运行状态，永远不生成依赖边。

`W(s) = {e | e 属于 s 的语义前驱传递闭包，submission_proven(e,s)，且 ownership_supported(e,s)}`

活动即使在 `sync.start` 前已经完成，只要是语义前驱，就仍属于 `W(s)`；它在 B 中体现为 hidden progress，而不是被删除。仅在其他 stream 与同步时间重叠、但没有依赖路径的活动不得进入 `W(s)`。

### 7.3 三类 completion scope

- Stream：目标 stream 的提交前缀，加上通过 event/default-stream 边可观察到的传递前驱。
- Device：Runtime 当前 device 上的全部此前请求任务；若存在无法恢复的 context 或外部 ownership，相关同步 fail closed。
- Context：Driver 当前或显式 context 中跨 stream 的全部此前请求任务。
- Event：同步调用时可见的最近一次 event record 所捕获的 stream 状态及传递前驱，不包含该 record 之后的活动。event 被重复 record 时，以同步调用可见的最近一次 record 为准。

default-stream mode 必须是 `LEGACY`、`PER_THREAD` 或 `NO_DEFAULT_STREAM_OBSERVED`。若 trace 中出现 default stream 而 mode 未记录，输出 `DEFAULT_STREAM_MODE_UNKNOWN`；legacy 模式还必须区分 non-blocking stream 例外。

## 8. terminal

terminal 是唯一支持“同步完成条件何时满足”的活动或 completion boundary，不是 `W(s)` 中任意时间戳最大的活动。

处理顺序如下：

1. 从 completion semantics 和依赖图中取最大前驱节点，形成 semantic dependency frontier。
2. frontier 唯一时，选择该活动或完成边界。
3. frontier 有多个节点时，只有它们处于同一已解析时钟域、且存在唯一最晚完成节点，才能选择该节点。
4. 最晚完成时刻相同即 `TERMINAL_TIE` 和 `AMBIGUOUS`；不强行选一个。
5. terminal 晚于 sync return、时钟逆序或必需映射缺失时为 `INVALID`。

对 completed-before-sync，terminal 可以位于 sync 入口之前；这表示完成条件早已满足，并不把 `W(s)` 变为空集合。

## 9. validity 与 fail-closed

| 状态 | 含义 | A | B |
| --- | --- | --- | --- |
| `VALID_NONEMPTY` | 证据完整，`W(s)` 非空且 terminal 唯一 | 按有效同步规则分类 | `B_VALID` |
| `VALID_EMPTY` | 可观察、受支持、ownership 合法的语义前驱确实为空 | device wait 为 0；同步区间归 residual | `B_NOT_APPLICABLE` |
| `AMBIGUOUS` | 同时存在两个或更多合理语义解释 | 同步区间归 unattributed | `B_AMBIGUOUS`，保留候选与原因 |
| `INVALID` | 必需事实缺失、冲突或类型不受支持 | 同步区间归 unattributed | `B_INVALID` |

primary reason 按以下优先级选择，其余保存在 secondary reasons：trace 完整性；请求边界与确定的外部 ownership；ownership 歧义；支持性；映射；默认流/提交/closure 歧义；closure 缺失；terminal tie；terminal 完整性。

主要原因码已在机器合同中冻结，包括 dropped records、时钟、request/phase ownership、外部 ownership、unsupported/unclassified API、context/stream/event/correlation 缺失、default-stream mode、submission race、dependency closure、terminal tie/not-found/after-sync 等。原因码是正式输出字段，不是可随意改名的调试字符串。

全局 dropped records、时钟域无法解析或 invocation 边界无效时，整个受影响窗口进入 `A_unattributed`。同步局部证据失败时，只把该 physical sync 区间归入 `A_unattributed`，其余窗口仍可保留，但必须同时报告 supported count/duration coverage 和失败分布。

## 10. A 层

顶层守恒式为：

`T_window = A_host_path + A_cuda_api + A_device_wait + A_sync_residual + A_unattributed`

分析器按 request/phase 窗口、CUDA API、physical sync 和 wait-set activity 的所有边界切分原子片段，再按以下优先级归属：

1. invalid、ambiguous、unsupported 或 ownership 不足的同步片段 -> `A_unattributed`；
2. valid sync 内有 `W(s)` activity 正在执行 -> `A_device_wait`；
3. valid sync 的其余片段 -> `A_sync_residual`；
4. 其余可归属的非阻塞 CUDA API -> `A_cuda_api`；
5. 其余 ownership 有效的请求推进墙钟 -> `A_host_path`；
6. 仍无足够证据的片段 -> `A_unattributed`。

其中：

`A_device_wait(s) = measure([s.start,s.end) intersect union(e.interval for e in W(s)))`

`A_sync_residual(s) = duration(s) - A_device_wait(s)`

所有计算使用 interval union，不把多线程 duration 直接相加。跨 phase 活动只按当前 phase 窗口交集记账，同时在 B 中保留 activity origin 与 cross-phase dependency。

`A_host_path` 是剩余型 Host 请求路径，不是 CPU busy time。`A_cuda_api` 在父类内互斥分为 submit/non-submit；`A_device_wait` 在父类内按同时存在的受等待活动分为 kernel-only、MemOp-only 和 mixed。二级分类不增加新的墙钟预算。

整数纳秒域要求顶层类别重复覆盖、未覆盖和越界均为 0 ns。毫秒序列化与统计比较的质量阈值由 Pilot 后续冻结，不能替代整数域守恒检查。

## 11. B 层

B 一条记录只对应一个 physical sync，必须保留 request/phase、origin、callsite、registry、`W(s)`、terminal、ownership、validity 和原因。它不进入 A 的墙钟预算，也不跨同步相加。

对 `B_VALID`：

- `wait_set_hidden_union_ns`：`W(s)` 活动在 sync 入口前执行部分的区间并集；
- `wait_set_exposed_union_ns`：`W(s)` 活动与当前 sync 窗口交集的区间并集；
- `terminal_pre_sync_ns`：terminal 是 activity 时，其执行在 sync 前的部分；
- `terminal_overlap_sync_ns`：terminal 是 activity 时，其执行与 sync 的交集；
- `sync_return_tail_ns = max(0, sync.end_ns - max(sync.start_ns, terminal.end_ns))`。

最后一式只保留同步窗口内部、完成条件满足后的可观察尾部。terminal 若早已完成，不能把 terminal end 到 sync start 的外部间隔算入 return tail。terminal 是无持续时间的 completion boundary 时，两项 terminal 执行指标为 null。return tail 不能自动解释为 runtime overhead。

Exposure Signature 对 B 只允许按 phase、sync kind、origin 和 callsite 报告状态 count、有效记录的 median/p90、terminal 类型与 provenance；不得构造 additive B total。

## 12. D 与 Exposure Signature

`D_margin = A_device_wait - A_host_path - A_cuda_api`

`D_score = D_margin / (A_device_wait + A_host_path + A_cuda_api)`

分母为 0 时 `D_score=null`。二者只从 A 读取，用于导航 Host/API 与 device-wait 哪侧更值得继续审计，不是硬件根因或 speedup 上界。

Exposure Signature 是冻结 A 一级/二级字段、A validity/coverage，以及 B 的 per-sync 状态、hidden/exposed、terminal、tail 和 provenance 的版本化投影。它不得读取 Raw 时间戳重新分类，不得建立第二套 accounting，也不得绕开 Q0 形成机制主张。

## 13. 规则与验证映射

机器合同共有 37 条规则，分为 phase 7 条、身份 4 条、S 14 条、A 6 条、B 4 条和派生 2 条；当前映射到 25 个 contract、runner、合成 trace、fault injection 和 Q0 real 案例，规则覆盖率为 100%。

这里的“覆盖”只表示每条规则都有预先指定的验证去向。Gate 2 必须独立写出每个 Q0 case 的输入结构和 expected `W(s)`、terminal、validity 与 A/B 关系；不能调用正式 S/A/B 实现生成答案。合成测试不能替代目标 Nsight observation stack 上的真实 CUDA Q0。

## 14. 当前 prototype 与本合同的已知不一致

- `bench_eager.py` 虽在流式路径逐 Token 调用 device synchronize，但 Token tensor 仍留在设备侧，没有形成统一的 Host-readable Token ID 证据。
- `exposedpath/runner.py` 在异步 argmax 提交后立即记录首 Token 时间，没有首 Token completion；后续 EOS 判断可能隐式同步，首 Token与后续 Token 语义不一致。
- 旧 S 只保留 `end > sync.start` 的 pending 活动，错误删除了 completed-before-sync 成员。
- 旧 stream wait-set 只按相同 context/stream 筛选，没有 event/default-stream 的传递闭包；event sync 直接标记缺映射。
- 旧 terminal 在缩减后的 wait-set 中按最大 end timestamp 选择，不先构造 semantic frontier。
- 旧 A 把剩余窗口直接放入 Host，且 `A_unattributed` 固定为 0，可能掩盖 invalid/unsupported/ownership 缺口。
- 旧 B 的 predecessor/gap/self 字段不是本合同的 wait-set hidden/exposed/terminal 生命周期定义。

因此，旧代码和历史 trace 只能继续承担 Prototype/Engineering 回归，不能计入 Gate 4、Gate 5 或 Q0 进度。

## 15. 版本、兼容与变更

合同、registry、测试映射和 analyzer 必须记录各自版本。新增 API alias、改变 completion scope、submission 规则、terminal 选择、validity、A 优先级、B 公式或 D/Signature 输入，均属于语义变化，必须发布新合同/registry 版本并重新通过相关资格测试。

Nsight SQLite schema 不是前向兼容格式；读取时必须检查导出 schema 版本、必需表字段和 dropped-record 证据。下游 S/A/B 只能读取 Gate 3 的 Canonical Raw，不得各自直接猜测 Nsight 表结构。

## 16. Gate 1 退出判断

合同内部审查只在以下条件同时满足时为 PASS：三份机器文件版本一致；规则、API alias 和案例 ID 唯一；每条 supported sync 均有 completion scope 与必需证据；37 条规则全部映射验证案例；A 五类和优先级完整；D/Signature 只引用 A/B；禁止占位与静默 fallback；命令 `python -m exposedpath_v141 validate-contract` 返回 PASS。

Gate 1 PASS 后，下一步只能进入 Gate 2 的独立 Q0 expected/oracle 设计。Canonical Raw、S、A/B、Q0、runner、Engineering Pilot 和 Formal 实验仍保持未通过或受阻状态。

## 参考依据

- NVIDIA CUDA Runtime API：[Stream Management](https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__STREAM.html)
- NVIDIA CUDA Runtime API：[Event Management](https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__EVENT.html)
- NVIDIA CUDA Runtime API：[Device Management](https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__DEVICE.html)
- NVIDIA CUDA Driver API：[Context Management](https://docs.nvidia.com/cuda/cuda-driver-api/group__CUDA__CTX.html)
- NVIDIA CUDA Runtime API：[Default stream synchronization behavior](https://docs.nvidia.com/cuda/cuda-runtime-api/stream-sync-behavior.html)
- NVIDIA Nsight Systems：[SQLite Schema Reference](https://docs.nvidia.com/nsight-systems/AnalysisGuide/index.html#sqlite-schema-reference)
