# Gate 6 真实 Q0 执行设计

> **HISTORICAL / SUPERSEDED FOR CURRENT EXECUTION** — 本设计已实现并被 `EP-G6-11` 收口，仅作追溯保留。正文中的 `真实 Gate6 仍保持 BLOCKED`、`q0_status = NOT_RUN` 等均为当时状态，不得作为当前执行依据。当前 Gate 状态见 `docs/v1_4_1/research_progress.md`；Gate 6 结论见 `docs/v1_4_1/gate6_closeout_v0_1.md`。

## 目标与边界

在不改变 Measurement Contract v0.2 和 Gate 2 人工 oracle 的前提下，把现有 GPU 前执行包补全为可在 Windows/Linux 单 GPU 上逐 case 运行、可恢复、不可覆盖且可独立判定的真实 Q0 工具链。所有采集仍属于 Engineering；只有完整 Q0 报告可以把 `q0_status` 从 `NOT_RUN` 改为 `PASS/FAIL`，且永远不能自动授予 Formal 资格。

## 已确认根因

现有 `prepare-q0-run` 使用 `--capture-range=nvtx`，但未指定 `--nvtx-capture`；微程序又使用动态、未注册的 JSON NVTX 字符串，因此生成的命令不能证明会触发采集。另有四个缺口：没有真实 case executor/receipt、没有受控 Canonical 故障注入、真实 trace 不能标准化为 observed、没有唯一 Gate 聚合报告。

## 方案选择

采用 `cudaProfilerStart/cudaProfilerStop` 控制采集，而不匹配动态 NVTX 字符串。资源初始化在 Start 之前，request/phase/sync 在 capture 内，析构同步在 Stop 之后；这样既保留结构化 NVTX 身份，也避免初始化/析构 activity 污染 Q0 sync 集合。Nsight 命令固定使用 `--capture-range=cudaProfilerApi`。

真实执行按 case 增量写入：预备 manifest 不修改；每个 case 成功后新建 receipt，记录 argv、退出码、stdout/stderr、Raw 路径/哈希、GPU UUID、驱动/CUDA/Nsight/OS 和环境选择。任何已有 Raw、receipt、身份冲突、工具哈希变化或 GPU 选择不一致均拒绝执行。多 GPU 通过显式 `CUDA_VISIBLE_DEVICES` 选择，微程序仍只使用过滤后的逻辑设备 0。

## 数据流

`prepared manifest -> execute case -> immutable .nsys-rep + receipt -> nsys export --lazy=false -> Canonical Raw -> [optional controlled fault copy] -> S -> A/B -> real observed -> independent evaluator -> Q0 gate report`

原始 `.nsys-rep` 永不修改。`REMOVE_ACTIVITY_CORRELATION`、`MARK_TRACE_DROPPED`、`REMOVE_GRAPH_NODE_MAPPING` 只作用于新的 Canonical 派生副本，并记录源/目标哈希和变换标识。terminal tie 与 submission race 保持纯合成，不能伪称 GPU 观测。

## 真实 observed 与独立判定

真实 observed 除 S/A/B 投影外，必须携带通过结构化 marker 恢复的稳定 activity label 及其真实区间。evaluator 使用人工写定的 wait-set/terminal label 判断结构正确性；B 数值的期望值根据这些真实区间独立进行半开区间计算，不能拿合成 oracle 的固定纳秒数比较真实 GPU。A 的数值关系同样从人工 wait-set 与真实区间推导；无法唯一恢复 label、时钟或 identity 时 fail closed。

Gate 聚合器要求 23 个必需 case 恰好一次：21 个 native seed 必须有真实 receipt，其中三项再有受控 fault 副本；两个 synthetic-only case 必须来自冻结合成执行器。任一 case 缺失、失败、哈希不一致、环境不完整或资格越界，Gate 只能为 `FAIL/BLOCKED`。

## 测试与验收

- CUDA source/argv 测试证明 Start/Stop 位置与 `cudaProfilerApi` 一致。
- executor 使用可执行假工具验证参数数组、GPU 环境、日志、哈希、不可覆盖和失败回执。
- fault 测试验证源 bundle 哈希不变、变换恰好命中预期字段并重写 lineage。
- real observed/evaluator 用确定性 Canonical/S/A/B fixture 验证真实区间计算、label 冲突和资格升级均 fail closed。
- gate 聚合测试覆盖 23/23 PASS、缺失、重复、失败、环境不完整和错误 source kind。
- 无 GPU 验收只能声明 `REAL_Q0_EXECUTION_READY`；真实 Gate6 仍保持 `BLOCKED`。
