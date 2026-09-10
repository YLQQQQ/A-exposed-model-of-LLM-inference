# ExposedPath GPU 前离线准备设计说明 v0.1

## 目的与结论

本设计说明规定在暂时没有 GPU 的条件下，哪些工作可以真正完成并接受离线验收，哪些工作只能准备而不能宣称通过。当前权威研究方案为 v1.4.1，数据角色为 Engineering；本设计不改变 `Raw -> S -> {A, B} -> D / Exposure Signature`，也不扩大单 GPU、请求内部的研究范围。

GPU 前的目标是达到“离线准备完成”：方法合同和独立标准答案明确，分析链具备确定性测试证据，GPU 验收程序可以直接执行。它不是 Q0 通过、Engineering Pilot 完成或正式实验就绪。

## 已确认的研究边界

1. 研究覆盖纯模型推理：从请求开始，到模型生成的 Token 编号可由 Host 读取为止。
2. 自然逐 Token 同步属于流式模型推理的一部分；Token 转文字、文本拼接、协议封装、网络传输和前端显示不属于研究范围。
3. G1 保留自然 Token 就绪行为。N1 只使用额外加入、删除或移动的同步来研究等待新增与迁移，两者不得混用。
4. 第一版合同覆盖 stream、device/context 和 event synchronization。证据不足时输出含糊或无效，不用时间重叠近似依赖。
5. 历史 `.nsys-rep` 只作为 Prototype/Engineering 回归材料；缺少 source manifest 的历史 trace 不得升级为 Q0、Pilot 或 Formal 证据。

## 当前基础

- Prototype 已封存，三个历史 Raw trace 的身份和 SHA-256 已记录且保持不变。
- 新版入口与旧 analyzer 分离，当前只实现 `Nsight SQLite -> observation report`。
- 当前 observation adapter 已对支持的 Nsight 导出版本、必需表、字段、同步 correlation 和 dropped-record 诊断执行只读检查。
- 三个历史 trace 均可用于解析回归，但因缺 source manifest 保持 `ambiguous`。
- 当前 runner 的首 Token 时间发生在明确完成证据之前，而后续 EOS 判断可能形成隐式同步；这证明旧 runner 不能直接作为新 phase boundary 的定义。

## GPU 前可以准确完成并验收的工作

### 1. 研究语言与范围记录

**目标**：统一 Token 就绪、自然逐 Token 同步、人为同步干预、等待集合和返回条件终点等术语。

**产物**：仓库根目录 `CONTEXT.md`。

**完成条件**：术语只描述研究概念，不夹带实现细节；与 v1.4.1、仓库规则和本设计一致。

### 2. 测量合同 v0.2

**目标**：把方法定义变成可测试的输入、输出和错误合同。

**必须明确**：

- Request、Prefill、Decode、首 Token 和后续 Token 的可观察完成边界；
- 自然 Token 就绪与 N1 人为同步的身份和隔离规则；
- Raw 必需字段、时钟域、提交顺序、进程、线程、context、stream、event 和 correlation 身份；
- 三类同步各自的 completion scope；
- `W(s)`、terminal、ownership、并列候选和缺失证据的处理；
- 有效、含糊、无效的判定与向下传播；
- A 的互斥类别、残余项和守恒容差；
- B 的单同步字段、hidden/exposed/return-tail 定义及禁止直接跨同步求和；
- D 与 Exposure Signature 只能由冻结后的 A/B 派生。

**完成条件**：合同不存在未解决的语义占位；每条规则都能对应至少一个确定性测试；旧 analyzer 行为不作为合同依据。

**可达到状态**：Gate 1 `PASS`。

### 3. Q0 独立标准答案设计

**目标**：在编写被测逻辑之前，规定受控 CUDA 情形和预期结果。

**必需用例**：stream wait、device/context wait、event record/wait、同步入口前已经完成的活动、同步期间仍在执行的活动、跨流时间重叠但无依赖、terminal 唯一与并列、外部 ownership、缺失 mapping、dropped records、Token 就绪边界和 A 守恒。

**独立性要求**：标准答案由用例的 CUDA 提交关系和预先写定的期望集合产生，不能调用 analyzer 的 `W(s)`、terminal 或 A/B 实现来生成期望值。

**完成条件**：每个用例都有输入结构、预期等待集合、预期 terminal、预期有效性和预期 A/B 关系；正例、负例和含糊例完整。

**可达到状态**：Gate 2 `PASS`。这只表示标准答案设计完成，不表示 Q0 已通过。

### 4. 统一原始数据层

**目标**：建立唯一、版本化的 Nsight 事实表示，使下游不再直接读取 profiler 表。

**必须保留**：输入与派生哈希、采集和导出版本、run/data role、请求与 repeat 身份、NVTX 边界、CUDA API、同步、kernel/MemOp、context/stream/event/correlation、时钟域及诊断证据。

**完成条件**：支持的 SQLite schema 能确定性转换；缺表、缺字段、映射冲突和 dropped records 显式失败；Raw 与历史文件不被覆盖；合成输入及三个历史 trace 回归稳定。

**可达到状态**：Gate 3 可以完成离线验收。历史 trace 本身仍保持 `ambiguous`，不影响验证 fail-closed 行为。

### 5. S 同步语义层

**目标**：针对每个同步恢复 `W(s)`、terminal、ownership 和 validity。

**完成条件**：确定性 fixture 覆盖三类同步；已经提前完成但属于 completion set 的活动仍进入 `W(s)`；其他 stream 上仅时间重叠的无依赖活动不会进入；无法唯一确定 terminal 时不会伪造确定结果。

**可达到状态**：Gate 4 可以通过合成 fixture 完成离线验收，但仍需真实 Q0 trace 验证 Nsight 可观测映射。

### 6. A/B 与 D/暴露特征

**目标**：在 S 稳定后实现保守的请求/阶段记账与单同步来源解释。

**完成条件**：A 的类别互斥并在冻结容差内守恒；B 保持 per-sync，不把多次同步重复计算成请求总量；含糊或无效证据完整传播；D 和 Exposure Signature 不绕过 A/B 重新计算时间。

**可达到状态**：Gate 5 可以通过合成 fixture 完成离线验收，但输出尚不具备正式实验资格。

### 7. Runner 合同对齐与 GPU 验收包

**目标**：让 GPU 到位后的第一次执行能够直接验证合同，而不是现场重新设计。

**GPU 前可以完成**：

- 设计首 Token 和后续 Token 的显式就绪记录方式；
- 区分自然逐 Token 同步与 N1 干预模式；
- 规定 Pass0/Pass1 使用相同输入、边界和执行策略；
- 完善 manifest、版本、环境、early EOS、排除、retry 和数据角色字段；
- 准备受控 CUDA Q0 程序、预期 manifest、Linux/Windows 启动入口和结果检查命令；
- 运行不需要 GPU 的参数、身份、schema、错误路径和平台命令构造测试。

**离线完成条件**：所有 GPU 程序和命令可静态检查，dry-run 能生成完整 manifest，CPU/mock 测试通过，且不会把 mock 结果写成真实验证。

**状态边界**：Gate 6 和 Gate 7 仍为 `BLOCKED`，直到真实 GPU trace 与目标平台 smoke test 完成。

### 8. GPU 前总验收

**目标**：形成可复查的离线就绪报告和一次性 GPU 执行清单。

**完成条件**：

- Gate 1 至 Gate 5 的合同、标准答案、schema 和确定性测试均达到各自条件；
- 新旧 analyzer 入口并存，旧 prototype 未被覆盖；
- 全量非 GPU 测试结果、既有失败和环境限制被如实记录；
- 没有任何产物声称 Q0、Pilot、Protocol Freeze 或 Formal 已完成；
- GPU 到位后的顺序固定为 observation preflight、受控 Q0、最小 LLM trace、关键回归和 Engineering Pilot。

## GPU 前不能宣称完成的工作

以下事项可以准备程序和协议，但必须等待 GPU 证据：

1. 真实 CUDA/Nsight 栈下的 Q0 资格验证；
2. 新 runner 的 Token 就绪边界是否在 trace 中完整可观察；
3. event、stream 与 context 映射是否在目标 Nsight 版本中充分且无歧义；
4. Windows 与 Linux launcher 的真实 GPU 行为等价性；
5. 模型端到端 Engineering Pilot、profiler overhead 和 trace 规模；
6. 正式平台资格、OOM/共同可行域、Pilot、Protocol Freeze、N1/G1/G2 与正式结论。

## 依赖顺序与停止条件

严格顺序为：研究语言 -> 测量合同 -> Q0 独立标准答案 -> 统一原始数据层 -> S -> A/B -> D/暴露特征 -> runner 对齐与 GPU 验收包 -> GPU 上 Q0。

任一步出现语义冲突、必需证据无法表达、fixture 无法给出唯一预期或 fail-closed 被破坏时，应停止进入下一层，先修正当前合同。不得为了使用历史 trace 而降低证据要求，也不得为了让离线阶段显示为完成而更改 gate 名称。

## 审查方式

每一层独立审查四项：是否符合 v1.4.1、输入输出是否明确、失败是否可观察、测试是否独立于被测实现。完成报告分别列出已验证事实、推断、限制和下一 gate，并使用 `PASS`、`FAIL`、`BLOCKED`、`NOT_RUN` 四种状态。

本设计本身不冻结测量合同。只有测量合同 v0.2 经审查且所有语义问题均有明确答案后，Gate 1 才能报告 `PASS`。
