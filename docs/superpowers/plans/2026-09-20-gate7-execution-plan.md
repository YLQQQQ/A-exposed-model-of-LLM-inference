# Gate 7 执行计划：`EP-G7-08`～`EP-G7-11`（2026-09-20 重审计版）

前提：Gate 6 / Q0 已于 2026-09-20 正式 `PASS`（`docs/v1_4_1/gate6_closeout_v0_1.md`）。本计划取代 `docs/superpowers/plans/2026-09-17-gate7-isolated-plan.md`；旧计划中“Gate 6 等待期内并行推进”的前提已失效，旧编号 `EP-G7-01`～`EP-G7-07` 只作历史，不再执行、不得复用。

## 1. 目标与范围

Gate 7 的唯一目标：让 runner/launcher 的**可观察边界、身份与执行策略**达到可机器验证的等价与一致，使 Gate 8 的 Engineering Pilot 能在一个没有未解释歧义的执行链上运行。

**平台范围决定（显式，不静默弱化）：** 项目当前只声明一个目标 observation stack（Windows + RTX 4090 + CUDA 12.4.131 + Nsight 2026.2.1），Q0 资格也只在该栈取得。因此 Gate 7 只要求**该平台**的真实 GPU smoke。runner 核心必须保持平台无关（不得硬编码 Windows 路径/命令/shell），但“声称支持第二平台（含 Linux）”所需的 launcher、smoke、平台资格检查与 Q0 属于 Gate 9 的平台资格流程。任一平台未通过该平台的真实 smoke 前，不得声称受支持。

**硬性边界：**

- 不修改 Measurement Contract 的语义定义、`exposedpath_v141/` 的 Canonical/S/A/B/D 计算语义、Q0 oracle/evaluator。
- 不提升任何数据资格；Gate 7 的所有产物仍是 `Engineering`。
- 不运行 Gate 6 的 GPU collection / synthetic / gate aggregation，不重跑 final-01～final-04，不回填缺失的 prepare-time sidecar。
- 不在 Gate 7 内做参数扫描、“以防万一”的平台探针或无研究假设支撑的诊断。
- 不为流程新建平行 checker：优先复用既有 `wmpc_manifest.json`、`inference_results.jsonl`、`exclusion_log.jsonl` 与既有测试套件。

## 2. 四个步骤（每个步骤一个实现动作 + 一个验证动作 + 一个验收决定）

### `EP-G7-08` 统一 Token 就绪边界 + 分离 G1/N1 模式

- **Objective：** 首 Token 与后续 Token 使用同一个可观察 completion 语义；G1 自然逐 Token 同步与 N1 人为干预以互斥、机器可读的模式身份表达。
- **Why：** `EP-ISSUE-01` 表明当前 runner 在异步 `argmax` 之后取 `t_first_token_ns`，而后续 Token 的 EOS 判定 `.any()` 可能触发隐式 device→host 同步；两类 Token 的完成边界不同，而这个差别会直接进入 A 窗口与 phase 定义。模式不分离则 N1 的人为同步会被误读为 G1 的自然行为。
- **Implementation：** 更新 `exposedpath/runner.py` 的 Token 边界取值与 `docs/pilot_runner_contract.md`；引入模式身份字段并实现非法组合 fail closed。测试先行。
- **Evidence：** 边界单调性/时间倒序 fail-closed 测试；模式互斥与非法组合拒绝测试；合同文字与实现一致的检查。
- **PASS：** 上述测试全绿，且首/后续 Token 边界在合成输入下使用同一语义。
- **STOP：** 若修正边界需要改动 Measurement Contract 的语义定义或 `exposedpath_v141` 语义 → 停止并单独提出，不在 Gate 7 内静默修改。
- **Dependency：** 无（Gate 7 的第一个可执行步骤）；只依赖已冻结的 Gate 1 Measurement Contract，不依赖 `EP-G7-09`/`EP-G7-10`。
- **Unlock：** 逐 Token 的可比较性成立，N1/G1 不会互相污染。

### `EP-G7-09` Pass0/Pass1 parity + 机器可读 provenance 补齐

- **Objective：** 冻结并证明 Pass0/Pass1 的输入、身份、phase boundary 与执行策略等价；补齐环境快照、early EOS、OOM、exclusion、retry、attempt 与 data role 字段。
- **Why：** Pass0/Pass1 若不等价，profiler overhead 与执行差异会被混同为模型行为；缺失的 exclusion/retry/attempt 字段会让“计划 repeat 数”与“有效样本数”不可区分，从而破坏后续 repeat 政策与质量门。
- **Implementation：** 复用既有 `wmpc_manifest.json` / `inference_results.jsonl` / `exclusion_log.jsonl` 结构补齐字段并加入机器可读 parity 检查；不新建平行 manifest 体系。
- **Evidence：** parity 校验测试；字段缺失/冲突 fail-closed 测试；一次合成 Pass0/Pass1 配对演练的机器可读产物。
- **PASS：** 缺失或冲突字段一律 fail closed，且 parity 检查在等价输入上通过、在任一有意差异上失败。
- **STOP：** 若要求把缺字段降级为零值/默认值来让检查通过 → 停止。
- **Dependency：** 与 `EP-G7-08` 无相互依赖，可并行实现；两者均须在 `EP-G7-11` 前完成。
- **Unlock：** Pass0/Pass1 可配对，exclusion/retry 政策有机器可读依据。

### `EP-G7-10` 平台适配隔离 + 既有 smoke 基线收敛

- **Objective：** 把 Windows PowerShell、平台探测、Nsight 调用收敛到 adapter/launcher；处置两项既有 smoke 失败。
- **Why：** 平台差异目前散落在脚本中，任何第二平台（Gate 9）都会重新暴露同类问题；而两项未解释的基线失败会让后续任何回归都无法区分“新缺陷”与“旧噪声”。
- **Implementation：** runner 核心改用 `pathlib` 与结构化子进程参数；平台特定逻辑下沉到 adapter/launcher；修复或按平台范围决定明确重界定 `tests/test_server_smoke_script.py::test_dry_run` 与 `::test_spaces`。
- **Evidence：** 命令构造与参数单测（不需要 GPU）；两项基线失败的最终处置结论（修复，或重界定并说明为何不再是未知失败）。
- **PASS：** 定向单测全绿；两项基线失败被修复或经明确重界定后不再计为未知失败。
- **STOP：** 若某项必须先有真实 GPU 才能判定 → 移交 `EP-G7-11`，不得用 mock 结论代替。
- **Dependency：** 独立于 `EP-G7-08`/`EP-G7-09`，可并行；其两项 smoke 失败的处置结论不依赖 GPU。
- **Unlock：** 平台可移植性被结构性保护，测试基线重新干净。

### `EP-G7-11` 非 GPU 全量验证 + 目标平台真实 GPU smoke + Gate 7 验收

- **Objective：** 在当前声明的目标平台（Windows + RTX 4090）上证明 runner 端到端链路成立，并完成 Gate 7 验收决定。
- **Why：** 只有真实 GPU smoke 能证明 Pass0/Pass1、identity/phase boundary、exclusion/retry 记录在真实执行栈上可被机器读取；Gate 8 必须以这份证据为入口。
- **Implementation：** 不改语义；只执行既有 runner 链路并收集 manifest/receipt 证据。真实 smoke 需在用户批准的窗口内运行，属于真实 GPU 执行，须单独取得授权。
- **Evidence：** 全量 `python -m pytest -q -p no:cacheprovider`；`python -m compileall exposedpath analysis exposedpath_v141`；合同/边界检查；目标平台 smoke 的 manifest/receipt 与逐项边界核对。
- **PASS：** 非 GPU 判据与目标平台真实 smoke 判据同时成立，且未修改 Measurement Contract 或 `exposedpath_v141` 计算语义。
- **STOP：** 任何真实 smoke 失败保留现场并停止，不得用 mock 或局部测试代替；需要第二平台等价性时转 Gate 9。
- **Dependency：** 消费 `EP-G7-08`～`EP-G7-10` 的产物；是 Gate 7 verdict 的必要条件，必须最后执行。
- **Unlock：** Gate 8 Engineering Pilot 可以启动；Gate 8 在 Gate 7 未满足本判据前不得启动。

## 3. 顺序与依赖

1. `EP-G7-08` 与 `EP-G7-09` 可并行设计与实现（无相互依赖）。
2. `EP-G7-10` 独立于前两项，可与它们并行；其两项 smoke 失败的处置结论不依赖 GPU。
3. `EP-G7-11` 最后执行，消费前三步产物；真实 GPU smoke 是 Gate 7 verdict 的必要条件。
4. Gate 7 verdict 在 `EP-G7-11` 之前保持 `NOT_RUN`；只有 `EP-G7-08`～`EP-G7-11` 的 PASS 判据全部成立时改判 `PASS`。

## 4. 最小验证顺序

定向 pytest → `python -m exposedpath_v141 validate-contract` 与 `scripts/verify_canonical_raw_boundary.py` → 全量 `python -m pytest -q -p no:cacheprovider` → `python -m compileall exposedpath analysis exposedpath_v141` → 目标平台真实 smoke。

## 5. 明确不做

- 不新建 Gate 6 诊断、不重跑 Gate 6 采集、不改动 Gate 6 的 PASS 判据或 evidence。
- 不为“跨平台”生成无研究假设支撑的第二平台探针；平台范围决定见 §1。
- 不引入新指标、新 accounting 定义或任何 D/Exposure Signature 改动。
- 不在本计划内执行 N1/G1/G2 或任何 Formal 采集。
