# ExposedPath：研究设计与论文证据框架

> 历史说明：这是阶段性的摘要候选稿，现已被 `docs/current/ExposedPath_研究设计与论文证据框架_v7.0_v1.4.1整合修订版.docx` 完整取代，不再作为当前研究主体。

**版本：v7.0 Pre-Pilot 整合候选版**

**状态：待 Measurement Contract 审查，不是 Protocol Freeze**

**适用主线：Q0 → N1/G1 → G2**

## 1. 文档定位

本文件整合研究设计主体 v6.0、实验相关材料和 v1.4.1 补充说明中仍然有效的研究逻辑。它用于说明“研究什么、为什么值得研究、怎样形成可信证据、允许提出什么主张”。当前仓库代码仍是 prototype 与 Engineering 基础，不能因为已有实现就视为符合本文件。

本候选版不替代当前权威的 v1.4.1。只有关键测量语义写入 Measurement Contract、完成规则—测试映射并通过审查后，才可讨论升级权威版本。

## 2. 核心研究问题

在单 GPU、单请求内部的延迟敏感异步 LLM 推理中，Host 线程经常在提交 GPU 工作后继续执行，随后又在同步点等待。传统分析常报告 kernel 时长、CUDA API 时长、GPU 利用率或 Host/GPU 活动重叠，但这些量不能直接回答：

> 哪些 Host—device 活动真正暴露在请求可见的等待路径上，它们如何形成用户能够感受到的纯模型推理时延？

ExposedPath 的目标不是重新计算“设备做了多少工作”，而是恢复请求在关键同步点等待了什么、等到何时、哪些时间被异步推进隐藏、哪些时间最终暴露，并把这些证据组织成可解释、可验证、能支持优化决策的结构。

## 3. 研究意义

Activity Cost 与 Request-Visible Exposure 不是同一个量。同一段 GPU 工作可能很长，却大部分在 Host 执行其他工作时已经完成，因此只暴露很少；一段较短工作也可能恰好位于关键同步点末端，直接决定请求何时继续。只看总时长或时间重叠容易产生三类错误：

1. 把昂贵但已被隐藏的活动当成主要时延来源；
2. 把时间上重叠、但没有同步依赖的活动错误归入请求关键路径；
3. 给出“优化最大 kernel 即可”的建议，却不能说明该优化是否会缩短请求可见等待。

因此，本研究的价值在于补足“设备活动成本”与“请求可见时延”之间缺失的语义层，并验证这种新信息是否真的改变诊断与优化选择。

## 4. 研究范围

### 4.1 核心范围

- 单 GPU；
- 单个请求内部的 Host—device exposure；
- 纯模型推理中的 Request、Prefill、Decode、首 Token 和后续 Token 就绪边界；
- eager 或其他能够满足冻结 observation contract 的执行模式；
- stream、device/context、event 等具有明确 completion semantics 的同步。

流式输出中的自然逐 Token 同步属于研究范围，因为它用于确认模型侧 Token 已经就绪。Token 就绪以后进行的反分词、文本拼接、网络传输、前端显示和外部消费者处理不属于核心测量范围。

### 4.2 暂不主张

- 多 GPU 或分布式 serving；
- 多请求并发下的通用 ownership 归因；
- 从 trace 直接推出硬件微架构根因；
- 对任意模型、任意平台的通用性能预测；
- 端到端产品时延中排队、网络和界面渲染等外部环节。

这些方向只有在核心证据链完成后才能作为独立扩展，不得静默并入当前 claim。

## 5. Activity Cost 与 Request-Visible Exposure

`Activity Cost` 描述某项活动本身占用了多少时间或资源，例如 kernel duration、CUDA API duration、传输时长或利用率。它适合回答“设备做了什么、成本多大”。

`Request-Visible Exposure` 描述请求因某个 completion dependency 实际无法继续推进、并暴露在请求 wall-clock 上的时间。它适合回答“用户为什么还要等”。

二者可以相关，但不存在天然相等关系。ExposedPath 不替代现有 activity profiling，而是在其之上补充请求可见的 completion 语义和暴露结构。

## 6. 方法链：Raw → S → A/B → D / Exposure Signature

### 6.1 Raw：保留可观察事实

Raw 层将 Nsight SQLite 和运行 manifest 转换为版本化、规范化的观察记录，保留时间戳、CUDA API、GPU activity、correlation、context、stream、event、NVTX/request identity、clock domain、dropped-record 状态和来源 lineage。

Raw 只回答“trace 中观察到了什么”，不能直接把重叠解释为依赖，也不能在缺表、缺字段、身份冲突或 dropped records 时静默补零。

### 6.2 S：恢复同步语义

S 层以每个请求内同步点 `s` 为单位，根据同步类型的 completion semantics 恢复：

- `W(s)`：该同步必须完成的、属于研究范围且能够归属到该请求的前驱活动集合；
- terminal：使同步完成的唯一末端证据；
- validity：该次恢复是 `valid`、`ambiguous` 还是 `invalid`，以及原因码。

`W(s)` 不是“与同步时间区间重叠的活动”，也不是“同步开始时仍在执行的活动”。只要一个活动属于该同步的 completion scope，即使它在同步开始前已经完成，也仍是 `W(s)` 的成员；它的相关时间可以表现为已隐藏进展，而不是被删除。

不同同步原语的 scope 必须分别定义。例如：

- stream 同步通常约束该 stream 上在同步之前提交的工作；
- device/context 同步通常约束相应 device/context 中此前提交的工作；
- event 同步约束被记录 event 所代表的提交前缀，并依赖 event record、wait 与活动之间的可验证关联。

具体规则必须由 Measurement Contract 冻结。单纯的时间重叠、相近时间戳或“最后结束”都不足以证明 dependency 或 terminal。

### 6.3 terminal 与 validity

terminal 是完成语义所指向、并能唯一支持“该同步何时解除”的末端证据。它不能简单等同于 `W(s)` 中 end 最大的活动；还必须满足同步类型、correlation/context/stream/event、ownership 和时间容差规则。

- `valid`：必需证据完整，scope、ownership 和 terminal 可唯一恢复；
- `ambiguous`：存在多个合理解释，无法唯一决定，但 trace 未必损坏；
- `invalid`：必需表/字段或映射缺失、记录丢失、身份矛盾，或违反冻结合同。

`valid_empty` 只能表示该同步没有请求内、在研究范围中且可归属的前驱活动；“前驱活动已经提前完成”并不等于空集合。

### 6.4 A：请求与阶段的互斥时间核算

A 回答：“在 Request、Prefill、Decode 等范围内，wall-clock 时间分别落入哪些互斥类别？”其基本要求是：

- 面向 request/phase；
- 各类别互斥；
- 总量守恒，残差显式记录；
- validity 向下游传播；
- 不用活动时长重复相加替代 wall-clock accounting。

A 的精确字段和分割边界属于 Gate 1 的待冻结内容。本候选版只固定其角色，不提前发明最终分类。

### 6.5 B：保留每个同步点的来源证据

B 回答：“这一次同步在等待什么，它的 `W(s)`、terminal、隐藏进展与暴露部分分别是什么？”B 必须保留 per-sync provenance，包括同步身份、请求/阶段、同步类型、completion scope、成员活动、terminal 和 validity。

由于不同同步可能覆盖相同前驱活动或嵌套依赖，B 默认不能跨同步直接求和。任何汇总必须有冻结的去重和解释规则。

### 6.6 D 与 Exposure Signature

D 是从冻结后的 A/B 派生的顶层导航视图，用于指出“应先查看哪个阶段或哪类同步证据”。D 不能被表述成硬件根因或新的 measurement definition。

Exposure Signature 是对 A/B 结构的机制摘要，用于比较不同 workload 或执行模式下暴露形态如何变化。它必须完全由冻结字段派生，不另行创造与 A/B 冲突的 accounting。

## 7. 研究问题与证据链

### 7.1 Q0：Correctness

Q0 验证 analyzer 是否依据真实 CUDA completion semantics 正确恢复 `W(s)`、terminal、validity 和 A/B 关系。它需要受控 CUDA 微程序、预先写定的独立 oracle、正例/负例/含糊例，以及真实 Nsight observation stack。重复 analyzer 逻辑的单元测试不能替代 Q0。

Q0 回答“测量是否正确”，不回答工作负载趋势或优化收益。

### 7.2 N1：受控干预下的信息响应

N1 人为改变同步位置、频率或方式，用于验证 ExposedPath 的输出是否对已知 completion-path 变化产生方向正确、可解释的响应。人为干预必须与自然逐 Token 同步分开标记，不能把干预结果冒充自然 workload 发现。

### 7.3 G1：自然工作负载中的信息增益

G1 在冻结后的自然推理行为下改变 input、output、batch 等 workload 条件，比较传统 activity 指标与 ExposedPath 的 A/B/Signature 是否提供不同且有解释力的信息。

G1 不预设结果必须出现明显“机制迁移”。若结果是按比例变化、分区依赖或 null，也必须如实报告，并相应收缩论文 claim。

### 7.4 G2：决策增益

G2 检验 ExposedPath 是否能在 held-out 场景中帮助选择更有效的真实优化干预，并相对传统指标提供增量决策价值。候选干预、选择规则、成功标准和统计方法必须在看到 Formal 结果前冻结。

若没有增量价值，研究仍可报告正确性和信息边界，但必须删除“更优优化决策”主张。

### 7.5 主证据链

研究论证顺序固定为：

1. `Correctness`：Q0 证明测量语义和实现可信；
2. `Information Gain`：N1/G1 证明其相对传统视角增加了什么信息；
3. `Decision Gain`：G2 证明这些信息能否改善实际选择。

不得越过 Q0，用看起来合理的图表替代正确性；也不得只有新指标差异，就直接声称优化决策更好。

## 8. 数据资格与实验阶段

| 数据角色 | 用途 | 不允许的用途 |
|---|---|---|
| Prototype | 追溯旧实现、保留历史基线 | 当前方法正确性或论文主证据 |
| Engineering | 验证采集链、schema、环境和错误处理 | Pilot 决策或 Formal 结论 |
| Pilot | 决定 workload、repeat、开销政策和质量门 | Protocol Freeze 后的正式统计证据 |
| Formal | 按冻结协议回答 N1/G1/G2 | 反向修改测量、排除或统计规则 |

若冻结后必须实质修改 analyzer、schema、workload、排除或统计规则，应建立新协议版本，并使受影响的 Formal 数据失效。

## 9. 预期贡献与主张边界

当前可追求的核心贡献是：

1. 一套从 Nsight 可观察事实恢复请求内 synchronization/completion exposure 的语义方法；
2. 保守、可审计的 request/phase accounting 与 per-sync provenance 表示；
3. 在受控正确性、自然信息增益和 held-out 决策增益链条上的实证评估。

论文可以根据证据强度逐级主张“可正确恢复”“提供额外解释信息”“帮助优化决策”。不能仅凭现有 prototype 或单一 trace 主张通用性、硬件因果、跨平台普适或显著性能提升。

G3/G4 可在核心链完成后用于适用边界验证；更广的 G5–G7 只保留为后续扩展池，不占用当前毕业与主论文的关键路径。

## 10. 风险与停止规则

- 若 Q0 无法在目标 observation stack 上稳定恢复 completion semantics，则停止 Formal 采集，优先收缩同步类型或可观测范围。
- 若 G1 仅显示与传统 activity 成比例的结果，则保留正确性贡献，降低“机制新信息”主张。
- 若 G2 无法提供 held-out 增量决策价值，则删除决策优越性主张，不事后改规则追求正结果。
- 若平台无法提供必需字段、identity 或 dropped-record 诊断，则该平台不具备正式实验资格。
- OOM 只用于确定可行域和排除，不作为研究意义证据。

## 11. 当前状态与下一步

当前处于 Engineering、Pre-Pilot 阶段。旧 prototype 已封存；新版 observation 检查入口能够只读处理历史 trace，但历史 trace 缺 source manifest，只能保持 Prototype/Engineering 资格。Canonical Raw、S、A/B、D/Signature 和 Q0 尚未完成。

唯一最高优先级是完成并审查 Measurement Contract v0.2：先定义 Token/phase 完成边界和自然/人为同步身份，再冻结 completion scope、`W(s)`、terminal、validity、A/B 与派生规则。完成后才能构造 Q0 oracle 和实现新版 S 层。

具体任务状态和证据以 `docs/v1_4_1/research_progress.md` 为唯一事实源；实验操作以 `experiment_protocol_candidate_v2_1.md` 为候选说明。
