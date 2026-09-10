# ExposedPath：实验与分析协议

> 历史说明：这是阶段性的摘要候选稿，现已被 `docs/current/ExposedPath_实验与分析协议_v2.1_v1.4.1整合修订版_Pre-Pilot.docx` 完整取代，不再作为当前执行入口。

**版本：v2.1 Pre-Pilot 整合候选版**

**状态：待语义审查与 Pilot 决策，不是 Protocol Freeze**

**承接底稿：实验与分析协议 v2.0；WMPC v1.5 仅作候选配置来源**

## 1. 协议定位

本文件描述 ExposedPath 从当前 Engineering 阶段走向 Q0、Pilot 和 Formal 实验的候选执行方式。它吸收 v1.4.1 对 `W(s)`、terminal、validity、A/B、自然逐 Token 同步和证据链的修正，并删除旧协议中“尚未验证便已冻结”的表述。

当前必须先完成 Measurement Contract。本文中的 workload、模型、平台、repeat、开销政策和统计门均为候选输入；只有经过平台资格检查、OOM/可行域探测和 Pilot 后，才可写入 Protocol Freeze。

本协议沿用研究设计中 `Activity Cost` 与 `Request-Visible Exposure` 的区分：前者描述活动自身成本，后者描述请求因 completion dependency 实际暴露的等待；二者不得相互替代。

## 2. 输入材料与优先级

1. 用户当前明确要求和研究边界；
2. v1.4.1 补充说明及仓库研究语义不变量；
3. 研究设计主体候选版 v7.0；
4. 实验与分析协议 v2.0 中无冲突的内容；
5. WMPC v1.5 中的 workload、模型和平台候选；
6. 当前代码与历史 trace，仅用于说明已有实现和工程可行性。

若候选协议与 Measurement Contract 冲突，以后者通过审查的版本为准，并提升本协议版本。任何含义不清的 trace 不得通过推测补全。

## 3. 数据角色

| 角色 | 目的 | 进入条件 | 禁止事项 |
|---|---|---|---|
| Prototype | 回归旧实现、复现历史行为 | 已封存身份与哈希 | 作为当前方法或论文证据 |
| Engineering | 打通命令、schema、环境和失败路径 | 明确标记 Engineering | 用于 workload 选择之外的科学结论 |
| Pilot | 决定 repeat、开销门、质量门和可行 workload | Q0 与执行链满足进入条件 | 混入 Formal 主统计 |
| Formal | 回答冻结后的 N1/G1/G2 | Protocol Freeze 完成 | 看到结果后改规则 |

Pass0 是无 Nsight Systems 主采集的真实性能测量；Pass1 用于 Raw/S/A/B/D/Signature 机制证据。两者数据角色相同，但用途不同。

## 4. 固定执行顺序

| Gate | 当前任务 | 退出条件 |
|---|---|---|
| 0 | 封存旧 Prototype | 旧提交、trace、基线和限制可追溯 |
| 1 | Measurement Contract | phase、同步、`W(s)`、terminal、validity、A/B/派生规则无未决语义 |
| 2 | Q0 独立 oracle 设计 | 正例、负例、含糊例及预期输出预先写定，且不复用 analyzer |
| 3 | Canonical Raw | schema 唯一、版本化，SQLite 转换确定且 fail closed |
| 4 | S 层 | completion set、`W(s)`、terminal、ownership、validity 测试通过 |
| 5 | A/B/D/Signature | 互斥、守恒、provenance 和派生不变量测试通过 |
| 6 | Q0 | 合成与真实受控 trace 均对照独立 oracle 通过 |
| 7 | Runner 对齐 | 自然/人为同步隔离，Pass0/1 身份和边界一致，非 GPU 测试通过 |
| 8 | Engineering Pilot | 最小端到端链路与 observation contract 可运行 |
| 9 | 正式平台资格 | 目标栈可观测、Q0 可复现、身份完整 |
| 10 | OOM 与可行域 | 共同稳定范围和预定义排除规则确定 |
| 11 | Pilot | repeat、overhead、质量门、代表点和执行策略有证据支持 |
| 12 | Protocol Freeze | 代码、schema、平台、WMPC、统计、主张判据均版本化 |
| 13 | N1/G1 Formal | 完成受控干预与自然工作负载信息增益评估 |
| 14 | G2 Formal | 完成 held-out 决策增益评估并据结果限定主张 |

不得用后续实验看起来合理的结果补偿前置 Gate 失败。

## 5. 运行与身份合同

### 5.1 每次运行必须记录

- 实验 ID、request ID、repeat ID、attempt ID、run role 与 Pass；
- 模型名称和 revision、tokenizer、输入 token digest、期望/实际输出 token 数；
- workload ID、batch、seed、greedy/采样设置、KV cache 和 attention backend；
- GPU、CPU、OS、driver、CUDA、framework、Nsight、launcher、git commit；
- schema、analyzer、sync registry、oracle 和协议版本；
- warmup、compile/capture、early EOS、OOM、retry、排除和退出状态。

这些身份必须通过 manifest 与 NVTX/trace 贯通，不能只按时间顺序猜测 request 或 repeat。

### 5.2 Pass0/Pass1 配对

- 使用相同的冻结 input IDs、模型 revision、生成参数、workload、seed、warmup 状态和执行模式；
- compile/capture 与缓存建立不得进入正式计时；
- Pass0 给出主要 latency/throughput，Pass1 不替代 Pass0；
- profiler overhead 的估计和接受门由 Pilot 决定，不在 Pre-Pilot 阶段固定为 5% 或 10%；
- repeat 数由 Pilot 的波动、失败率和成本决定，不预先固定为 20。

## 6. Measurement Contract 的最低内容

### 6.1 Phase 和 Token 边界

Request、Prefill、Decode、首 Token 与后续 Token 必须使用可观察的完成边界。自然逐 Token 同步用于确认模型侧 Token 已就绪，属于 G1 的自然行为；Token 到文本、网络和前端不在测量窗口。N1 插入的同步必须有独立 variant/callsite 身份。

### 6.2 `W(s)` 与 completion scope

对每个同步点 `s`，`W(s)` 是该同步按 CUDA completion semantics 必须完成、且属于该请求范围的前驱活动集合。集合构造至少需要：

- Host 提交顺序；
- context/device、stream、event record/wait 的明确关联；
- request ownership 与排除规则；
- 同步类型对应的 scope；
- trace 必需字段、clock domain 和 dropped-record 状态。

活动即使在同步进入前已经完成，只要属于 completion scope 仍进入 `W(s)`。时间重叠只作为活动状态计算的输入，不能单独证明依赖。

### 6.3 terminal 与三态判定

terminal 必须是 completion scope 内能够唯一支持同步解除的证据。若存在不可消解的并列候选、event 映射缺失、ownership 冲突或记录不完整，应标记 `ambiguous/invalid`，而不是选择最大时间戳。

`valid_empty` 只允许用于“没有请求内、受支持、可归属的前驱活动”；不得用于“前驱在同步前已经完成”。三态和原因码必须传播至 A/B/D/Signature，缺失证据不得转换为零值。

## 7. Canonical Raw 与输出层

| 层 | 必需内容 | 主要不变量 |
|---|---|---|
| Raw | API/activity、时间、correlation、context/stream/event、request/phase、lineage、诊断 | 可观察事实与解释分离；版本不兼容时拒绝 |
| S | sync、completion scope、`W(s)`、terminal、ownership、validity/reason | 重叠不等于依赖；证据不足 fail closed |
| A | request/phase 互斥 wall-clock 类别、残差、守恒和 validity | 不重复计时，闭合误差受控 |
| B | per-sync 成员、terminal、hidden/exposed 结构和 provenance | 默认不跨同步求和 |
| D | 由 A/B 派生的导航字段 | 不解释为硬件根因 |
| Signature | 由 A/B 派生的机制摘要 | 不创建第二套 accounting |

字段名称、单位、枚举、版本兼容和误差容差必须在 Gate 1/3 明确定义，本文不替代 schema。

## 8. Q0：独立正确性资格测试

### 8.1 原则

Q0 由受控 CUDA 微程序和独立 oracle 组成。oracle 根据用例代码、提交关系和同步语义预先写定 expected `W(s)`、terminal、validity 及 A/B 关系，不能调用或复制 analyzer 的分类实现。

### 8.2 必需案例

| 类别 | 必须验证的事实 | 预期行为 |
|---|---|---|
| Stream | 同一 stream 上同步前提交的 kernel/MemOp | 全部语义前驱进入 `W(s)`，包括同步前已完成者 |
| Device/context | scope 内多个 stream 的此前提交活动 | 只纳入受该同步约束且可归属的活动 |
| Event | event record 所代表的提交前缀 | 由 event 关联恢复，不以重叠猜测 |
| 提前完成 | 活动在 sync entry 前结束 | 仍属于 `W(s)`，其进展体现为 hidden |
| 同步中完成 | terminal 在等待窗口内完成 | 暴露部分和解除时刻与 oracle 一致 |
| 无关重叠 | 另一 stream 活动时间重叠但无 completion dependency | 不进入 `W(s)` |
| 空集合 | 确实没有请求内受支持前驱 | 可判 `valid_empty` |
| terminal 并列 | 多个候选在规则/容差下不可唯一判定 | `ambiguous`，不强选一个 |
| 外部 ownership | 活动无法可靠归属请求 | 按合同 `ambiguous/invalid` |
| 缺失或丢记录 | correlation/event/table 不完整或 dropped records | `invalid` 并保留原因码 |

### 8.3 Q0 通过条件

- 所有声明支持的必需案例，`W(s)` 成员身份与 terminal 对 oracle 精确匹配；
- hidden/exposed 和 A/B 的时间结果在冻结容差内一致；
- 所有含糊、缺失、unsupported 情况正确 fail closed；
- 合成 fixture 通过后，还必须在目标 Nsight observation stack 上采集真实受控 trace；
- 真实 LLM sentinel 的支持覆盖和失败分布达到 Pilot 冻结的质量门。

任何核心用例失败都不能用 G1/G2 结果补偿。

## 9. N1：人为同步干预

N1 只在 Q0 通过后运行。基线 V0、仅标记 Vmarker 和候选同步变体必须共享输入、模型与执行合同。插入同步的 callsite、所在 stream、次数和 variant 必须可审计。

N1 比较 Pass0 的真实请求/phase 时延，传统 raw sync 与 activity 指标，以及 A 的净 wall-clock 变化和 B 的 per-sync 迁移证据。若干预造成局部等待增加、后续自然等待减少或 hidden progress 改变，A/B 应能解释净变化；若只得到“越早同步越慢”且 raw sync 已足够解释，N1 降级为压力测试，不作为方法不可替代性的主贡献。

自然逐 Token 同步不得标成 N1 干预，也不得被移除后再把非流式路径称为自然 G1。

## 10. G1：自然工作负载信息增益

G1 保持模型、计算栈和生成协议稳定，改变 input、output 和 batch，在自然 Token 就绪行为下比较传统指标与 A/B/Signature。目标是判断 ExposedPath 是否揭示额外、稳定且可解释的暴露结构，而不是预设必须观察到某种迁移。

允许的结果包括：非比例变化、按比例变化、不同 phase/平台的分区依赖或 null。论文主张必须随证据收缩。Nsight Compute 等机制审计只能用于解释少量 sentinel 的设备侧现象，不能替代 Request-Visible Exposure accounting。

## 11. G2：held-out 决策增益

G2 的优化干预必须与基线处于可解释的同栈比较中，并在 Formal 数据前冻结候选、选择规则、baseline、held-out 单元、成功标准和失败后的主张处理。

旧协议中的 `G2_score = A_host_path + A_cuda_api_submit`、C1 compile 和 P1 held-out 可保留为待 Pilot 审查的候选，不在本版中宣告冻结。Pilot 只能检验输出一致性、可运行性、graph break/capture、噪声和成本，不能用观察到的相关性选择有利公式。

若 held-out 结果不优于冻结 baseline，则删除“预测或选择优化收益”的主张；若变化 accounting 仍可靠，可保留优化响应解释。

## 12. WMPC 候选池

### 12.1 六个代表点

| 编号 | 输入 Token | 输出 Token | Batch | 候选用途 |
|---|---:|---:|---:|---|
| S1 | 128 | 16 | 1 | 轻请求，观察固定 Host/API 暴露 |
| S2 | 512 | 16 | 1 | 中等基线 |
| S3 | 2048 | 16 | 1 | Prefill-heavy |
| S4 | 2048 | 16 | 4 | Prefill + batch-heavy |
| S5 | 512 | 256 | 1 | Decode-heavy |
| S6 | 512 | 256 | 4 | Decode + batch-heavy |

### 12.2 二十二个 workload 候选

| WID | 输入 | 输出 | Batch | 备注 |
|---|---:|---:|---:|---|
| W01 | 128 | 16 | 1 | S1；输入切片 |
| W02 | 128 | 16 | 2 | 输入切片 |
| W03 | 128 | 16 | 4 | 输入切片 |
| W04 | 512 | 16 | 1 | S2；输入切片 |
| W05 | 512 | 16 | 2 | 输入切片 |
| W06 | 512 | 16 | 4 | 输入切片 |
| W07 | 2048 | 16 | 1 | S3；输入切片 |
| W08 | 2048 | 16 | 2 | 输入切片 |
| W09 | 2048 | 16 | 4 | S4；输入切片 |
| W10 | 4096 | 16 | 1 | 输入切片 |
| W11 | 4096 | 16 | 2 | 输入切片 |
| W12 | 4096 | 16 | 4 | 高显存风险 |
| W13 | 512 | 64 | 1 | 输出切片 |
| W14 | 512 | 64 | 2 | 输出切片 |
| W15 | 512 | 64 | 4 | 输出切片 |
| W16 | 512 | 256 | 1 | S5；输出切片 |
| W17 | 512 | 256 | 2 | 输出切片 |
| W18 | 512 | 256 | 4 | S6；输出切片 |
| W19 | 128 | 256 | 1 | 长输出补点 |
| W20 | 128 | 256 | 4 | 长输出 + batch |
| W21 | 2048 | 256 | 1 | 长输入 + 长输出 |
| W22 | 2048 | 256 | 4 | 长输入 + 长输出；高显存风险 |

这些点不是当前正式矩阵。平台资格、OOM 探测和 Pilot 可以依据预先声明的整组规则删减；不得根据显著性或趋势单点选择。核心配对比较应尽量使用共同可行集合。

### 12.3 模型、平台和计算栈候选

| 维度 | 当前候选 | 本版结论 |
|---|---|---|
| 主模型 M0 | Qwen2.5-7B-Instruct、BF16 | 需固定 revision 并在目标平台验证，不是 Formal 冻结项 |
| 边界模型 | 同家族小/大模型 | 仅在核心链资源允许时用于适用边界 |
| 核心栈 C0 | Transformers + 手写 prefill/decode + PyTorch eager | 需确认自然 Token 就绪边界和实际 attention backend |
| 干预栈 C1 | 同路径上的 `torch.compile` 候选 | 只作为 G2 候选；Pilot 失败则删除，不自动换题 |
| 平台 | 旧文档中的 RTX 4090、RTX 6000 Ada 等 | 当前尚未获得或完成资格检查，全部只视为候选 |

G3/G4 仅作为核心链完成后的适用边界候选；MoE、量化、跨引擎等 G5–G7 保留为后续扩展池，本阶段不投入主要资源。

## 13. Pilot 决策项

Pilot 只决定运行政策，不提供 Formal 结论。必须记录并冻结：

- 共同可行 workload 和统一删点规则；
- warmup、repeat、随机化/分块顺序；
- Pass0/Pass1 profiler overhead 接受与重采政策；
- timestamp 容差、A residual、supported sync、B-valid 等质量门；
- early EOS、OOM、失败、retry、attempt 与 block 重跑规则；
- 代表 sentinel、G2 干预可行性和输出一致性；
- 统计单元、bootstrap/区间方法和图表映射。

不得在 Pre-Pilot 文档中用未经数据支持的固定数值替代这些决策。

## 14. Protocol Freeze 与正式执行

Protocol Freeze 至少包含：代码提交、runner/analyzer、Canonical Raw schema、sync registry、oracle、目标平台栈、模型 revision、WMPC、输入 digest、repeat、Pass 配对、排除/重跑、质量门、统计脚本、图表和 N1/G1/G2 判据。

冻结后若必须改变任何会影响结果含义或样本选择的内容，应创建新协议版本，并将受影响的 Formal 数据标记失效；不得将不同协议版本混入同一主分析。

## 15. 当前进入条件判断

当前 Gate 0 已通过；Gate 1 和 Gate 3 为 `FAIL`；Q0、runner GPU 对齐、Engineering Pilot 及后续阶段尚未运行或受 GPU 阻塞。历史 `.nsys-rep` 只能用于 Prototype/Engineering 回归。

因此，本协议当前只用于指导离线准备。下一步不是采集 G1/G2，而是完成 Measurement Contract v0.2，随后建立 Q0 oracle、Canonical Raw、S 和 A/B。最新状态以 `docs/v1_4_1/research_progress.md` 为唯一事实源。
