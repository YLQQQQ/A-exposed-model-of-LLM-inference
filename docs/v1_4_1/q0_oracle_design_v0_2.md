# ExposedPath Q0 独立标准答案设计 v0.2

## 1. 目的与结论边界

本设计为未来 Q0 正确性验证预先写定标准答案。它回答“在一个人为控制、依赖关系已知的案例中，正确的 `W(s)`、terminal、validity 和 A/B 关系应是什么”，不负责从 Nsight trace 推导这些答案。

当前 Gate 2 的 `PASS` 只表示标准答案结构完整、可机器校验且与被测 analyzer 静态隔离。该设计冻结之后，CUDA 微程序、真实 Nsight trace 与 analyzer 对照已于 2026-09-20 在冻结目标栈（Windows + RTX 4090 + CUDA 12.4.131 + Nsight 2026.2.1）上完成：`q0-win-4090-20260920-gate6-final-04` 的全套 case（含 `Q0-MISSING-CORR-001` v0.2 的 `MISSING_ACTIVITY_CORRELATION` + `[SUBMISSION_ORDER_AMBIGUOUS]` 期望）通过，Q0 为 `PASS`、Gate 6 为 `PASS`（package/analyzer `0.2.2`）。本文件的 oracle 结构与预期未因该轮执行而改变；当前状态见 `docs/v1_4_1/research_progress.md` 与 `docs/v1_4_1/gate6_closeout_v0_1.md`。

## 2. 文件与职责

- `q0/oracle_cases_v0_2.json`：版本化的人工标准答案，是 Gate 2 的主要产物。
- `exposedpath_v141/q0_oracle.py`：只校验、加载标准答案，并对已给定的 `W(s)` 做独立区间并集计算。
- `scripts/verify_q0_oracle_independence.py`：用 AST 检查 oracle 未导入旧 analyzer、未来 Raw/S/A/B 实现，也未在区间函数中读取 dependency edges。
- `tests/test_v141_q0_oracle.py`：验证结构、合同引用、原因码、覆盖矩阵、手算时间和独立性。

上述文件不包含可执行 CUDA 微程序。微程序、manifest 与真实采集属于 Gate 6，不因 Gate 2 通过而提前完成。

## 3. 用例数据合同

每个 case 分为两部分：

- `construction`：描述未来微程序必须制造的活动、Host 阻塞同步、显式依赖边和特殊观测条件。稳定的 `activity_label` 与 `sync_label` 是标准答案身份；真实 trace 的临时行号不能成为身份。
- `expected`：人工写定每个同步的 `wait_set_activity_labels`、terminal、validity、主要/次要原因、B 状态及 A/B 应满足的关系。

数值时间用于可手算的合成区间验证；真实 CUDA 执行只比较稳定标签、集合、状态和关系，不要求运行时纳秒值与合成值相同。oracle 不允许缺省 `W(s)` 后自行推导，也不允许 terminal 指向 `W(s)` 之外的活动。

## 4. 覆盖矩阵

当前共 23 个必需案例，分为 7 个正例、7 个边界例、2 个含糊例和 7 个负例，共覆盖 25 个特性。

| 组别 | 核心案例 | 要验证的问题 |
|---|---|---|
| 基本 completion scope | stream、device、driver context、event | 不同同步的语义等待范围是否正确 |
| 事件传递依赖 | event record 前缀、cross-stream wait-event、跨线程有序 | 是否只沿可观察事件边恢复闭包 |
| 边界条件 | completed-before、valid-empty、kernel/MemOp、phase spill | 提前完成不丢失、空集合不伪装失败、活动来源与记账归属分离 |
| 排除时间重叠 | 无关流、PTDS、query/poll | 重叠不产生依赖，非阻塞查询不生成 physical sync |
| 含糊与失败 | terminal tie、submission race、缺 event/correlation、dropped records、外部 ownership | 证据不足时是否 fail closed |
| 支持边界 | graph mapping unsupported、同步 D2H unsupported、invocation bleed | 未冻结语义不得被猜测成有效零值 |
| 聚合边界 | 重叠 Host sync | A 使用区间并集且互斥；B 保持 per-sync，不跨同步求和 |

## 5. 独立性边界

oracle 可以读取人工 expected，并可以对这些已写定活动区间执行通用区间并集；它不能遍历 `dependency_edges` 生成 `W(s)`，不能选择 terminal，也不能调用 analyzer 的分类或记账函数。静态检查明确拒绝 `analysis`、旧 `exposedpath` 及未来 `exposedpath_v141.raw/sync/accounting` 导入。

这种隔离避免“用 analyzer 自己算出的结果检验 analyzer 自己”。不过静态隔离并不能替代人工审查，因此 JSON 同时引用 Measurement Contract 的规则编号和冻结原因码，测试会拒绝不存在或 validity 不匹配的引用。

## 6. 未来真实 Q0 的使用方式

1. Gate 3～5 完成 Canonical Raw、S 与 A/B 实现。
2. Gate 6 将 `construction` 转成最小 CUDA 微程序，并生成稳定 label 到真实 trace 的映射 manifest。
3. 在合格 Nsight observation stack 上采集 trace；先验证 trace 完整性和身份，再运行 analyzer。
4. 将 analyzer 输出逐 case 对照人工 expected；任何必需案例缺失、含糊处理错误或被静默置零，Q0 均不能通过。
5. Q0 报告必须同时记录 oracle、合同、schema、analyzer、CUDA/Nsight 与平台版本。

## 7. 本 Gate 验收

运行：

```powershell
python -m exposedpath_v141 validate-q0-oracle
python scripts/verify_q0_oracle_independence.py
python -m pytest tests/test_v141_q0_oracle.py -q -p no:cacheprovider
```

预期分别得到 `DESIGN_ONLY_PASS`、`oracle_independence: PASS` 和全部测试通过。`DESIGN_ONLY_PASS` 不能写成 Q0 `PASS`。
