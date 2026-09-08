# ExposedPath 阶段与数据 Gate

任务涉及执行规划、workload 选择、数据分类、就绪判断，或在 Engineering、Pilot 与 Formal 阶段之间转换时，读取本参考文件。

## 数据角色

| 角色 | 允许用途 | 禁止用途 |
|---|---|---|
| Prototype | 保存旧实现、复现旧行为、建立回归 fixture、理解失败历史 | 作为当前方法证据或论文正式结果 |
| Engineering | 验证 runner、schema、可观测性、parser 行为、环境记录和调试假设 | 支撑 workload claim、最终 repeat 数量或正式科学结论 |
| Pilot | 在冻结前选择可行点、repeat 数、overhead 政策、排除规则和质量阈值 | 作为冻结后的验证性证据 |
| Formal | 在合格平台上执行已经冻结的 N1/G1/G2 协议 | 观察结果后重新调整方法、排除规则、指标或 workload 点 |

每个产物都必须携带自己的数据角色。不得通过复制或重命名把产物升级到更高证据类别。

## 推荐的 Gate 顺序

### 0. 封存 Prototype

保存 commit/tag、环境记录、输出 schema、样例 trace 和已知限制。完成条件是旧 prototype 仍可复现，并且能够明确识别为非 Formal 数据。

### 1. Measurement Contract

冻结带版本的 Raw 输入、S 语义、A/B 字段、D/Signature 派生规则、phase completion boundary、validity、identity 和错误行为。完成条件是所有语义问题都明确且可由机器测试，未解决选项被记录而不是猜测。

### 2. 设计 Q0 Oracle

在使用 analyzer 作为证据前，定义受控 CUDA 用例和独立预期结果，并包含负例及 ambiguous 用例。完成条件是预期 completion set 和 gate verdict 不来自被测试的实现本身。

### 3. Canonical Raw 层

针对支持的 Nsight schema 建立唯一且带版本的中间表示与 observation gate。完成条件是缺失或含糊证据能够显式失败，并且下游层不再各自直接查询 profiler table。

### 4. 实现 S 层

针对不同 sync 实现 `W(s)`、terminal、ownership 和 validity。完成条件是确定性 fixture 覆盖语义 completion set，而不是只覆盖时间重叠。

### 5. 先实现 A/B，再实现 D/Signature

只有 S 稳定后，才能实现保守的 A 和 per-sync B。D 与 Exposure Signature 只能从已经冻结的 A/B 派生。完成条件是守恒、互斥、provenance、invalid 传播和 schema 版本测试均通过。

### 6. Q0 资格验证

使用合成 trace 和真实受控 CUDA trace 对照独立 oracle。只有必需用例在目标 observation stack 上全部通过，并证明 fail-closed 行为后，Q0 才能判定为通过。部分通过不能授权 Formal 实验。

### 7. 对齐 Runner 与跨平台执行

对齐 Request/Prefill/Decode completion boundary、固定输入、identity、exclusion logging、Pass0/Pass1 parity，以及 Windows/Linux launcher。完成条件是在所声称支持的平台上证明合同等价且输出可由机器读取。

### 8. Engineering Pilot

运行一个小型开发子集，验证端到端链路、trace coverage、存储规模、overhead 和运行可靠性。不得在此阶段调整科学结论。

### 9. Formal 平台资格检查

在每个候选 Formal 平台上检查 Q0 所需可观测性，GPU/driver/CUDA/framework/Nsight identity，eager 行为，以及 G2 所需的 compile/graph 可行性。无法支持冻结后 observation contract 的平台不具备资格，或必须声明新的协议变体。

### 10. 探索可行域与 OOM 边界

探测候选 input/output/batch 点。OOM 和不稳定性用于确定可行性，不能决定科学重要性。在记录平台特定排除项的同时，选择比较所需的共同稳定范围。

### 11. Pilot

使用预定义代表点选择 repeat 数、overhead 处理、质量阈值和运行规则。完成条件是所有 freeze 输入都有依据，同时不把 Pilot 当作验证性证据。

### 12. Protocol Freeze

冻结 code commit、analyzer/schema、平台栈、workload matrix、seed/input digest、repeat、排除规则、质量 gate、统计方法、绘图方案和 claim 评估规则。任何实质变更都必须建立新协议版本，并使受影响的 Formal 数据失效。

### 13. N1 与 G1

执行受控 N1 intervention 和自然 G1 sweep。不得为了寻找 rank reversal 或反直觉例子而修改指标。对 null、按比例和依赖 regime 的结果都应如实报告。

### 14. G2

执行真实优化 intervention 和 held-out decision-gain 评估。根据预定义标准决定最终 claim 边界，不能根据叙事偏好决定。

## 产物身份与 Provenance

每次 run 及其派生结果至少要绑定：

- run role 和 protocol version；
- code commit 和 dirty-state 标识；
- analyzer 与 schema 版本；
- workload 和固定输入 digest；
- model/revision 与 execution mode；
- GPU、driver、CUDA、framework、Nsight、OS 与 launcher identity；
- Pass0/Pass1 配对关系以及 repeat/attempt identity；
- exclusion、OOM、early termination、retry、缺失证据和 validity verdict；
- Raw artifact digest 和派生 lineage。

不得把绝对路径作为唯一逻辑 identity，也不得只根据时间顺序推断 repeat identity。

## Gate 报告方式

每个 gate 只能报告以下状态之一：

- `PASS`：所有预定义的必需条件均已通过；
- `FAIL`：至少一项必需条件失败；
- `BLOCKED`：所需证据或平台能力不可用；
- `NOT_RUN`：尚未执行该 gate。

不得把 warning、跳过用例、mock 测试或无法运行的 GPU 测试转换为 `PASS`。下一项修正行动应与 verdict 分开记录。
