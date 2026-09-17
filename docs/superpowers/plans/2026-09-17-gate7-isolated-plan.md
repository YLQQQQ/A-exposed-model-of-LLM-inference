# Gate 7 隔离实施计划：`EP-G7-01`～`EP-G7-06`（并行、非 GPU）

状态：**定稿（docs-only）**。本文件与其对应的 `research_progress.md` Gate 7 状态更新单独提交，不包含 Gate 6 策略文档变更。

## 1. 授权与边界

本计划依据用户 2026-09-17 的决定编写，只覆盖 Gate 6 等待期内允许并行推进的**非 GPU** 项 `EP-G7-01`～`EP-G7-06`。

硬性边界：

- Gate 7 verdict 保持 `BLOCKED`；`EP-G7-07` 不得执行；Gate 8 不得启动。
- 不得把并行工作描述为前序 Gate（含 Gate 6）已通过，也不得据此修改 Gate 6/Q0 requirement 或任何数据资格。
- 本计划与 Gate 6 策略工作（`EP-G6-06`/`EP-G6-07`/`EP-G6-08`）**隔离提交**：不得在同一 commit 中混入 Gate 6 策略变更、Q0 requirement 变更或数据资格变更。
- 本轮不实施 GPU smoke，不采集任何 pass，不运行真实推理。
- Gate 7 只改 runner / launcher / 身份与 schema 层；不得修改 `exposedpath_v141/` 的 Canonical/S/A/B/D 计算模块、Q0 oracle/evaluator 或 Measurement Contract。

## 2. 现状（作为计划输入的事实）

- 旧 v3 runner 路径：`exposedpath/runner.py`（537 行）、`bench_eager.py`、`run_one.py`、`run_matrix.py`、`exposedpath/cli.py`、`exposedpath/manifest.py`、`exposedpath/validation.py`、`exposedpath/results.py`；合同说明为 `docs/pilot_runner_contract.md`。
- `exposedpath/runner.py:144` 首次 `argmax` 之后立即在 `:148` 取 `t_first_token_ns`，而此后 `:167` 的 EOS 判定使用 `(next_token == eos_token_id).any()`，可能触发隐式 device→host 同步；首 Token 与后续 Token 的完成边界因此不一致（`EP-ISSUE-01`）。
- launcher 目前只有 PowerShell：`scripts/*.ps1`（含 `run_pass0.ps1`、`run_pass1_nsys.ps1`、`run_nsys_single.ps1`、`export_nsys_sqlite.ps1` 等），没有等价的 Linux 入口。
- 既有基线失败：`tests/test_server_smoke_script.py::test_dry_run`、`::test_spaces`（PowerShell smoke 脚本相关，长期记录为基线）。

## 3. 逐项计划

| 编号 | 交付 | 验收证据 | 明确不做 |
|---|---|---|---|
| `EP-G7-01` | 设计并实现一致、可观察的 Token 就绪边界：首 Token 与后续 Token 使用同一 completion 语义，不再取值于异步 argmax 提交/返回之后；以 stream-ordered 完成点或等价的显式可观察边界定义并记录到 runner 合同中 | 设计说明 + 离线/合成测试证明首/后续 Token 边界一致；边界异常（如时间倒序）继续 fail closed | 不改变 Measurement Contract、不引入新指标、不在 GPU 上验证 |
| `EP-G7-02` | 分离 G1 自然逐 Token 同步与 N1 人为同步干预：以互斥、机器可读的模式身份表达，非法组合 fail closed | 配置/schema 测试、非法组合拒绝测试 | 不执行 N1/G1 实验、不产生任何实验数据 |
| `EP-G7-03` | 冻结 Pass0/Pass1 的输入、身份、阶段边界与执行策略一致性，并加入机器可读 parity 检查 | parity 校验测试、缺失/冲突字段 fail closed | 不采集 Pass0/Pass1、不做跨平台比较结论 |
| `EP-G7-04` | 补齐 manifest/结果字段：环境、early EOS、OOM、exclusion、retry、attempt、data role 与稳定实验身份 | schema 校验测试、字段缺失/冲突 fail closed、身份可机器读取 | 不把缺字段转换为默认值或零值 |
| `EP-G7-05` | 平台适配隔离：把 Windows PowerShell、Linux shell、Nsight 调用与平台探测收敛到 adapter/launcher，runner 核心保持跨平台；路径使用 `pathlib`，子进程使用参数列表 | Windows/Linux 命令构造与参数单测（不需要 GPU）；两类平台的 smoke 脚本静态检查 | 不声称同时支持双平台（需 `EP-G7-07` 的真实 smoke） |
| `EP-G7-06` | 非 GPU 测试收敛：参数、命令构造、身份、schema 与错误路径测试；处理 `test_dry_run`/`test_spaces` 两项既有基线失败（修复或明确重界定并记录） | `python -m pytest -q -p no:cacheprovider`；报告跳过的测试、环境限制与既有失败 | 不得把局部或 mock 测试描述为端到端 GPU 验证 |

## 4. 顺序、依赖与验证

1. `EP-G7-01`、`EP-G7-02`、`EP-G7-03`、`EP-G7-05` 相互独立，可并行设计与实现；采用测试先行（先写失败测试）。
2. `EP-G7-04` 依赖 `EP-G7-01`/`EP-G7-02` 确定的边界与模式字段定义。
3. `EP-G7-06` 覆盖全部改动并在最后收敛，包含两项基线失败的处理结论。
4. 最小验证顺序：定向 pytest → 合同/边界检查（`python -m exposedpath_v141 validate-contract`、`scripts/verify_canonical_raw_boundary.py`）→ 全量 `python -m pytest -q -p no:cacheprovider` → `python -m compileall exposedpath analysis exposedpath_v141`。
5. 每项完成时必须给出可复查证据（测试命令与输出、修改文件），并单独报告跳过项与环境限制。

## 5. 完成判据

`EP-G7-01`～`EP-G7-06` 全部具备可复查证据，且满足：未修改 Measurement Contract 与 `exposedpath_v141` 计算语义、未提升任何数据资格、未运行 GPU 实验。满足后 Gate 7 仍为 `BLOCKED`，只在 `EP-G7-07` 获得授权并完成后才允许重新判定 Gate 7。

## 6. 停止条件

- 若发现 Token 就绪边界必须改变 Measurement Contract 中的语义定义 → 停止该项并单独提出，不得在 Gate 7 内静默修改语义。
- 若某项必须依赖真实 GPU 证据才能判定 → 停止并等待 `EP-G7-07`；不得用 mock 结果替代。
- 若发现改动会波及 Gate 6/Q0 requirement、Canonical/S/A-B 语义或数据资格 → 停止并转交 Gate 6 策略流程处理。
