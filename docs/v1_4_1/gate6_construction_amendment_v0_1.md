# Gate 6 Construction Amendment v0.1：pre-capture same-kernel warm-up

> **后记（2026-09-20）：** 本文档为冻结的 amendment 记录，其 requirement 内容不变；正文中“Gate 6 = `FAIL` / Q0 = `NOT_RUN` / 待 implementation / Gate 7 暂停”等描述均为批准时刻的历史状态，已由 Gate 6/Q0 `PASS`（`q0-win-4090-20260920-gate6-final-04`，package `0.2.2`）取代。当前状态见 `docs/v1_4_1/research_progress.md` 与 `docs/v1_4_1/gate6_closeout_v0_1.md`。

状态：**批准（2026-09-18）**
适用范围：Gate 6 / Q0 Qualification
canonical baseline 分支：`codex/gate6-canonical-baseline`
canonical baseline HEAD：`bc6c69cf5a6ec1d6e72d8f87454047246d5ad8f7`

本文件冻结 amendment 的 evidence basis、scope、runtime policy transport、warm-up
语义、不变量、provenance 映射、版本策略、迁移与 STOP 条件。它不改变 Measurement
Contract、Q0 oracle、Canonical、S、A/B、evaluator，也不改变 23-case composition
或 Gate 6 PASS 判据。

## 1. Evidence basis

Primary evidence：formalshape warm-up 配对 Engineering diagnostic
（`q0-win-4090-20260918-kernel-memop-h2d-formalshape-warmup-02.zip`）。

ZIP SHA256：
`04767C513ACEB0EF73EFB284981CF0D43AD255161A67ABEEBDDFCDBDEC70FDA1`

两 arm 使用同一 binary、同一 Nsight、同一 GPU、同一 measured construction，固定
执行顺序 A' → B，唯一有意 construction diff 是 B 在 capture/request 之前对同一个
`q0_spin_kernel` 做一次 warm-up 并 sync。

| arm | measured launch API | H2D device interval | kernel device interval | overlap_ns | terminal |
|---|---|---|---|---|---|
| A'（无 warm-up） | 68,103,639 ns | 30,159,150 → 96,480,876 ns | 97,379,466 → 107,383,666 ns | 0 | KERNEL_A / KERNEL |
| B（warm-up） | 75,884 ns | 29,714,834 → 92,596,712 ns | 29,743,762 → 39,744,503 ns | 10,000,741 | MEMCPY_B / MEMOP |

两 arm 的 `S_DEVICE` 均为 `VALID_NONEMPTY`，wait set 精确为 `{KERNEL_A, MEMCPY_B}`。
B 的 terminal 结构（`MEMCPY_B` / `MEMOP`）与 `q0/oracle_cases_v0_2.json` 中
`Q0-KERNEL-MEMOP-001` 的冻结 expected 一致。

解释边界（冻结）：

- 本证据只支持 “preconditioning / warm-up 与测量结果存在受控关联”；
- **不得**归因到 LAZY_MODULE_LOADING、WDDM、driver、runtime 或其他具体层；
- 两 arm 的 `cuda_module_loading_mode` 均为 `LAZY`，不能声称 lazy module
  loading 机制已被证实；
- 固定执行顺序带来跨进程 clock/cache carryover 的已知 limitation；
- 本证据为 Engineering-only，不构成 Formal evidence，不改变任何 Gate verdict。

## 2. Scope

冻结：

```
APPLY          = { Q0-KERNEL-MEMOP-001 }
DO_NOT_APPLY   = 其余 20 个 real case
NOT_APPLICABLE = 2 个 synthetic-only case（不执行 GPU）
```

该集合由 **static construction predicate** 在 review-time 对
`q0/oracle_cases_v0_2.json` 与 `q0/cuda/exposedpath_q0.cu` 求值得到。

规范 predicate（review-time only）：

```
APPLY(C) ⟺ 存在 sync s ∈ expected.syncs 满足全部：
  (a) C.execution_strategy ∈ {NATIVE_CUDA, NATIVE_WITH_CANONICAL_FAULT}
  (b) s.wait_set_status = VALID_NONEMPTY 且 s.terminal.status = VALID
      且 s.terminal 指向 W(s) 内的一个 device activity
  (c) W(s) 同时包含至少一个 KERNEL activity 和至少一个非 KERNEL device activity
  (d) 这些 activity 之间不存在 dependency_edge，且不位于同一 stream
  (e) measured request 中所有 kernel launch 都提交到 capture 前已创建的既有
      non-blocking stream，且不涉及 event record/wait、graph capture、
      default / legacy / PTDS stream
```

21 个 real case 中只有 `Q0-KERNEL-MEMOP-001` 满足 (c) 与 (d)。

排除依据（摘要）：

- `Q0-STREAM-001` / `Q0-OVERLAPPING-HOST-SYNC-001`：`W(s)` 只含 KERNEL，无 (c)。
- `Q0-DEVICE-001` / `Q0-CONTEXT-001`：`W(s)` 只含 KERNEL；且同一 host 线程
  串行提交，terminal 不翻转。
- `Q0-EVENT-001` / `Q0-EVENT-XSTREAM-001` / `Q0-MULTITHREAD-ORDERED-001`：
  存在 dependency edge，违反 (d)。
- `Q0-DEFAULT-LEGACY-001` / `Q0-DEFAULT-PTDS-001`：涉及 legacy / PTDS stream，
  违反 (e)。
- `Q0-EMPTY-001` / `Q0-SYNC-D2H-UNSUPPORTED-001`：无 kernel。
- `Q0-QUERY-001`：expected 无 sync，无 (b)。
- `Q0-MISSING-EVENT-001` / `Q0-MISSING-CORR-001` / `Q0-DROPPED-001` /
  `Q0-EXTERNAL-001` / `Q0-INVOCATION-BLEED-001` / `Q0-GRAPH-UNSUPPORTED-001`：
  expected 为 INVALID / AMBIGUOUS，与时序无关，无 (b)。
- `Q0-COMPLETED-001` / `Q0-PHASE-SPILL-001`：单 kernel，terminal 唯一。

Explanatory observation（非规范、不参与 predicate 求值、不得用于任何判定或
运行时决策）：在 `Q0-KERNEL-MEMOP-001` 中，两个并发 device activity 由不同的
host 执行路径提交，因此首次 kernel 使用的 host 侧成本只推迟其一的提交。这一点
仅用于帮助理解为何该 case 命中 (c)+(d)，**不作为** APPLY 判据，也不构成机制
因果结论。

该集合是 predicate 的唯一匹配结果，不是 `case_id` runtime heuristic。predicate
本身不含任何具体 case identifier，实现中也不得退化为 case 白名单。

## 3. 禁止 circular policy

- construction predicate 与 oracle analysis 只用于 review-time scope 证明，其
  结论固化在 manifest 中；
- **runtime 不得读取 oracle、trace、overlap、terminal、validity 或任何测量结果**
  来决定是否执行 warm-up；
- runtime 只读取 manifest 中冻结的 initialization policy；
- 不得存在“先看结果、再决定是否 warm-up、必要时重跑”的路径。

## 4. Runtime policy transport（冻结）

正式数据流固定为：

```
q0/execution_manifest_v0_2.json
  → exposedpath_v141/q0_execution.py
    → generic formal initialization argv
      → native binary (q0/cuda/exposedpath_q0.cu)
```

约束：

- manifest 冻结 scope：每个 case 显式声明其 initialization policy；
- `q0_execution.py` 按 manifest policy 决定传给 binary 的 generic
  initialization flag，并把实际生效的 policy 写入 run manifest 的 case 记录；
- CUDA binary **不得**通过 `case_id`、run-id regex、oracle 内容或任何运行结果
  决定是否 warm-up；
- 正式 warm-up flag 与 Engineering `--diagnostic-warmup-kernel` 语义完全分离：
  后者保留给独立 Engineering diagnostic，正式路径不使用它；
- formal path **不写** `EXPOSEDPATH_DIAGNOSTIC_V1` NVTX metadata mark；
- 未知或缺失 policy 值必须 fail closed。

建议的正式 argv（命名建议，尚未实现）：单一枚举参数

```
--measurement-initialization <POLICY>
```

取值与 manifest policy 同名字符串，便于逐字校验一致性：

```
NONE
PRE_CAPTURE_SAME_KERNEL_WARMUP
```

所有 native case 都显式传该参数（`NONE` 也显式传），使“缺失”与“显式 NONE”
可区分；binary 端遇到缺失或未知值立即以非零退出。

## 5. Warm-up semantics

对 APPLY case，warm-up 必须同时满足：

1. 使用同一个 `q0_spin_kernel` symbol；不得换成其它 kernel 或空 kernel。
2. 与 measured kernel 使用**同一 invocation shape**：相同 launch configuration
   （grid / block / shared memory）与相同 duration/work 参数；warm-up 时长与
   measured 时长必须同源，不得各自硬编码。
3. 提交到该 case 的**既有 measured kernel stream**；不得新建 stream。
4. 在 `cudaProfilerStart()` 与 request NVTX range **之前**完成。
5. 完成后以 `cudaStreamSynchronize(measured_kernel_stream)` 同步；**不得**泛化
   为 `cudaDeviceSynchronize()`，也不得用其它 broader-scope 同步替代。其目的是
   保证 warm-up 在 pre-profiler 阶段已彻底完成，而不是引入额外的 device-scope
   同步语义。
6. 不新增 measured event、gate 或 activity。
7. warm-up activity 不进入 Raw measured capture、request 或 S wait set。
8. 不做结果驱动的参数调整；warm-up 参数在实现提交时冻结。
9. 正式 Q0 不写 Engineering diagnostic NVTX metadata mark。

## 6. Invariants

amendment 通过后以下全部保持不变：measured request / phase / sync topology、
activity labels 与 ownership、stream / context / dependency semantics、
Q0 oracle（`exposedpath-q0-oracle-0.2.0`）、Canonical、S、A/B、evaluator、
21 real + 2 synthetic case composition、Gate 6 PASS 判据。

## 7. Provenance mapping

| 角色 | commit |
|---|---|
| evidence implementation commit（`warmup-02` receipt 记录） | `3dae79d8517678cfd1ad36752c74efab10184160` |
| canonical equivalent HEAD | `bc6c69cf5a6ec1d6e72d8f87454047246d5ad8f7` |

两者 7 个 implementation blob 已逐一验证完全一致：`exposedpath_v141/cli.py`、
`exposedpath_v141/q0_kernel_memop_d2h_warmup_diagnostic.py`、
`exposedpath_v141/q0_kernel_memop_h2d_warmup_diagnostic.py`、
`q0/cuda/exposedpath_q0.cu`、`tests/test_v141_q0_cuda_source.py`、
`tests/test_v141_q0_kernel_memop_d2h_warmup_diagnostic.py`、
`tests/test_v141_q0_kernel_memop_h2d_warmup_diagnostic.py`。

历史 evidence 不可变：不得改写 `warmup-02` 的任何 receipt、trace 或派生产物。

## 8. Versioning proposal

- `exposedpath-q0-execution`：`0.2.0` → `0.2.1`
- `exposedpath-q0-run`：`0.2.0` → `0.2.1`（记录实际生效的 initialization policy）
- `exposedpath-q0-real-evidence`：保持 `0.2.0`
- `exposedpath-q0-gate`：保持 `0.2.0`
- `exposedpath-q0-oracle-0.2.0` 与 `exposedpath-measurement-contract-0.2.0`：
  **必须保持不变**
- 文件策略：就地更新 `q0/execution_manifest_v0_2.json` 与
  `docs/v1_4_1/contracts/q0_execution_schema_v0_2.json`，不新建 patch-version
  文件名，避免与既有的 `_SCHEMA_PATH` 绑定冲突。

精确 version touch list（只读核查所得，含源码依据）：

| 位置 | 当前值 | 变更 | 依据 |
|---|---|---|---|
| `q0/execution_manifest_v0_2.json:2` | `exposedpath-q0-execution/0.2.0` | → `0.2.1` | manifest 自身声明 |
| `docs/v1_4_1/contracts/q0_execution_schema_v0_2.json:17` | `const` `exposedpath-q0-execution/0.2.0` | → `0.2.1` | JSON Schema const，由 `q0_execution.py:91-97` 强制执行 |
| 同上，`$id` | `.../q0-execution-0.2.0.json` | → `0.2.1` | schema 文档身份 |
| `exposedpath_v141/q0_execution.py:347` | `exposedpath-q0-run/0.2.0` | → `0.2.1` | run manifest 写入点 |
| `exposedpath_v141/q0_collection.py:159` | 校验 `!= "exposedpath-q0-run/0.2.0"` | → 推荐兼容读取 `0.2.0` 与 `0.2.1` | 真实依赖，否则采集阶段直接抛错 |
| `exposedpath_v141/q0_gate.py` | `real-evidence/0.2.0`、`q0-gate/0.2.0` | **明确不改** | 该文件不检查 execution/run version |

run version 策略（冻结）：

- 新的正式 Q0 run **只能**由 execution path 产生 `exposedpath-q0-run/0.2.1`；
- `q0_collection.py` 在 implementation 阶段推荐同时兼容读取 `0.2.0` 与 `0.2.1`，
  便于重放历史 run manifest；该兼容窗口不授权任何新 run 使用 `0.2.0`。

## 9. Migration / acceptance

1. amendment approval（本文件定稿并批准）
2. implementation（见 §11 文件列表）
3. offline tests / independent review
4. server rebuild + identity：固定 implementation commit、冻结源码 dirty guard、
   binary SHA256、Nsight 版本与哈希、GPU UUID、`--list-cases` 与冻结 21 native
   seed 集合完全一致
5. 唯一一次完整 21 real + 2 synthetic Q0，同一 run、同一环境、同一 binary
6. 生成唯一 `q0_gate_report.json`

Gate 6 只有在唯一 `q0_gate_report.json` 同时满足全部条件时才判 PASS：`23/23`、
`verdict=PASS`、`q0_status=PASS`、21 real 全部由真实 evidence 通过、2 synthetic
只承担冻结 boundary role、同一 run / 环境 / binary、禁止跨 run 或跨平台拼接。
部分通过、warning、跳过、mock 或无法运行的 GPU 测试一律不得转为 PASS。

## 10. Hard STOP

出现以下任一情况立即 STOP，且不得通过新增 attempt“补跑到成功”：

- oracle / S / A-B / evaluator 被修改
- warm-up 进入 measured region（Raw capture、request、S wait set）
- 引入 Engineering diagnostic metadata（`EXPOSEDPATH_DIAGNOSTIC_V1:`）
- 用 `cudaDeviceSynchronize()`（或其它 broader-scope 同步）替代
  `cudaStreamSynchronize(measured_kernel_stream)` 完成 warm-up
- event / graph / default-stream / PTDS / API warm-up 被顺带引入
- runtime 依据运行结果选择或调整 warm-up
- 任何 retry 或参数 tuning
- 实现中以 `case_id` 特判代替 construction predicate
- 仅修改 manifest 而未同步 schema 定义
- formal path 缺失或收到未知 policy 值时未 fail closed
- 任一 evidence invalid / ambiguous / schema unsupported / hash failure

Gate 6 保持 `FAIL`、Q0 保持 `NOT_RUN`，直至 §9 条件在同一 run 中全部满足。

## 11. Implementation file list

必需 9 项：

1. `q0/execution_manifest_v0_2.json` — 每个 case 新增必填
   `measurement_initialization`；升 `schema_version` 到 `0.2.1`
2. `docs/v1_4_1/contracts/q0_execution_schema_v0_2.json` — 定义并 required 该
   字段；更新 `$id` 与 `schema_version` const
3. `q0/cuda/exposedpath_q0.cu` — 新增 generic `--measurement-initialization`
   入口（与 measured 参数同源、pre-profiler 完成并以
   `cudaStreamSynchronize(measured_kernel_stream)` 同步、formal path 不写
   diagnostic mark）；保留 `--diagnostic-warmup-kernel` 原语义不受影响
4. `exposedpath_v141/q0_execution.py` — 按 manifest policy 追加 argv、写 run
   `0.2.1` 并在 case 记录中留存 policy
5. `exposedpath_v141/q0_collection.py` — 兼容读取 run `0.2.0` 与 `0.2.1`
6. `tests/test_v141_q0_execution.py` — policy / argv / schema 回归
7. `tests/test_v141_q0_cuda_source.py` — 源码结构回归（manifest policy 驱动
   warm-up，非 case_id 特判；review-time predicate 不进入 runtime）
8. `tests/test_v141_q0_collection.py` — collection version regression：
   `0.2.1` accepted；unknown run version rejected；若保留 backward
   compatibility 则 `0.2.0` accepted
9. `docs/v1_4_1/gate6_construction_amendment_v0_1.md` — 本文件

条件性：`docs/v1_4_1/gate6_windows_server_runbook.md`（§3、§9）、
`docs/v1_4_1/research_progress.md`（6.6 → 6.7）。

明确不涉及：`q0/oracle_cases_v0_2.json`、`canonical_raw.py`、`s_bundle.py`、
`sync_semantics.py`、A/B 与 evaluator 实现、`measurement_contract_v0_2.json`、
`q0_gate.py`、任何 evidence 文件。
