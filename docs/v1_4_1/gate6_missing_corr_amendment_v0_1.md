# Gate 6 Missing-Corr Amendment v0.1：same-activity mapped-sentinel deterministic construction

状态：**批准（2026-09-19）**
适用范围：Gate 6 / Q0 Qualification，仅涉及 `Q0-MISSING-CORR-001` 的 native construction 与 synthetic 对齐
canonical baseline 分支：`codex/gate6-canonical-baseline`
canonical implementation commit：`2e81f6f9a9ec590d37fb01be9e31f2251645c5d1`
frozen run：`q0-win-4090-20260919-gate6-final-01`（frozen incomplete Engineering run，不得重跑/续跑/重派生/升级）
依赖：`docs/v1_4_1/gate6_q0_build_contract_amendment_v0_1.md`（已批准）

本文件冻结 `Q0-MISSING-CORR-001` 的规范测试意图、frozen evidence 的根因定性、唯一批准的
one-way same-activity mapped-sentinel handshake、sentinel 内存与可见性合同、one-way 裁决、
watchdog 规则、controlled fault 边界、synthetic 对齐、scope、zero-diff 清单与 STOP 条件。

本 amendment **不**处理：

- Phase-Spill observational boundary（`gate6_phase_spill_amendment_v0_1.md`）；
- External / Multithread-Ordered / Overlapping-Host-Sync 的 marker ownership 规则
  （`gate6_marker_ownership_amendment_v0_1.md`）；
- controlled fault injection 语义（`REMOVE_ACTIVITY_CORRELATION` 保持不变）。

> **Supersede 注记（2026-09-20）**：本文件的 §2（one-way mapped-sentinel handshake）、§3（sentinel
> 内存与可见性合同）、§4（one-way 裁决与 watchdog），以及 §6 / §7 / §9 中与 sentinel runtime
> construction 相关的条目，已由 `docs/v1_4_1/gate6_missing_corr_amendment_v0_2.md` **supersede**：
> 该 handshake 在目标 Windows/WDDM 栈上被独立 diagnostic evidence 否决（pure host poll queue ≈30 s、
> pre-capture same-kernel warm-up ≈5 s、`cudaStreamGetFlags` ≈5 s），正式 construction 回退为普通
> `launch K_UNMAPPED -> S_STREAM -> cudaStreamSynchronize`，并删除 sentinel / watchdog /
> system-scope atomic。§1（规范测试意图与根因定性）、§5（controlled fault 边界）与
> 「synthetic 必须经真实语义推导」的原则继续有效，但具体期望值以 v0.2 §3 / §4 为准。
> 本文件不再作为 implementation 依据。

## 1. Evidence basis

### 1.1 规范测试意图（oracle，冻结）

`Q0-MISSING-CORR-001` 为 `NEGATIVE`、`required_for_q0 = true`、features `MISSING_CORRELATION`、
required contract rules `MC-S-002` / `MC-S-013`。其 expected 冻结为：

```text
S_STREAM: wait_set_status = INVALID
          wait_set_activity_labels = []
          terminal = INVALID / NONE
          validity = INVALID
          primary_reason = MISSING_ACTIVITY_CORRELATION
          secondary_reasons = []
          b_status = B_INVALID
          a_relations = ["whole_sync=A_unattributed"]
```

即本合同要隔离验证的**只有一个** fault：activity correlation 缺失。其余 submission / ordering
证据必须保持确定且充分，故 `secondary_reasons` 被冻结为空。

### 1.2 frozen `final-01` 现场

```text
K_UNMAPPED.start_ns = 32,923,286
S_STREAM.start_ns   = 32,881,809
delta               = +41,477 ns

observed: validity = INVALID
          primary_reason = MISSING_ACTIVITY_CORRELATION
          secondary_reasons = ["SUBMISSION_ORDER_AMBIGUOUS"]
```

同一 observed A window 另记 `primary_reason = CUDA_API_SEMANTICS_UNRESOLVED`、
`secondary_reasons = ["MISSING_ACTIVITY_CORRELATION", "SUBMISSION_ORDER_AMBIGUOUS"]`。

### 1.3 根因定性（源码事实）

当前 native construction 为：

```text
launch(r, c, id, "decode", "K_UNMAPPED", r.first, 35);
auto sync = sync_range(c, id, "decode", "S_STREAM", 0);
cudaStreamSynchronize(r.first);
```

kernel launch 只是**入队**，host 侧不等待任何 device 起步证据就立即打开 `S_STREAM` range。
因此 `K_UNMAPPED.start < S_STREAM.host_start` 不具备结构性保证，实测恰好取到
`K_UNMAPPED.start` 晚于 `S_STREAM.start`（+41,477 ns）。

在 correlation 已被 controlled fault 真实删除、enqueue provenance 同时失效的前提下，
submission proof 只剩 `GPU_STARTED_BEFORE_SYNC` 一条候选；该候选在本次构造下**不成立**，
analyser 因此合法地追加 `SUBMISSION_ORDER_AMBIGUOUS`。

结论（冻结）：

- 这不是 analyzer bug，也不是 evaluator 过严；
- 也不是 oracle 冻结过窄；
- 而是当前 construction **无法确定保证** `K_UNMAPPED.start < S_STREAM.host_start`；
- 因此不得通过放宽 `secondary_reasons` 比较、修改 evaluator 为 subset 比较、或调参重跑来"解决"。

## 2. 唯一批准的修复（冻结）：one-way same-activity mapped-sentinel handshake

仍只有**一个** measured GPU activity：`K_UNMAPPED` 本身。

- Missing-Corr 专用新 kernel symbol：`q0_spin_kernel_signaled`；
- `q0_spin_kernel` 保持 **zero-change**（其它 case 与 `warmup_kernel_memop` 继续使用它），
  因而 `Q0-KERNEL-MEMOP-001` 的 same-kernel warm-up 规则不受影响；
- measured kernel 的 label（`K_UNMAPPED`）、launch config（单 block 单 thread）、
  stream（`r.first`）、时长/work 参数与 NVTX identity 均保持不变；
- kernel 自身在开始执行后写入 STARTED sentinel；
- host 观察到 STARTED 之后才打开 `S_STREAM` 并调用 `cudaStreamSynchronize`。

由此得到可由结构直接证明的链：

```text
K_UNMAPPED begins
    -> same K_UNMAPPED writes STARTED sentinel
    -> host observes STARTED
    -> S_STREAM host interval starts

therefore: K_UNMAPPED.start < S_STREAM.host_start
```

该链使 `GPU_STARTED_BEFORE_SYNC` 成为确定、可复现的 submission proof，从而使
`primary = MISSING_ACTIVITY_CORRELATION` + `secondary = []` 成为 construction 的必然结果。

## 3. Sentinel 内存与可见性合同（冻结）

### 3.1 分配与映射

- 独立的 4-byte sentinel，单独分配，不复用现有大 host buffer；
- `cudaHostAlloc(..., cudaHostAllocMapped)`（**不**使用 `WriteCombined`）；
- 分配后零初始化；
- 通过 `cudaHostGetDevicePointer()` 取得 device 侧指针；即使 UVA 下 host/device 指针数值相同，
  仍显式调用以做 fail-closed mapping 验证，不依赖指针相等假设；
- device 与 host 两侧都必须自然对齐到 4 byte；
- allocation / mapping / 初始化全部发生在 `cudaProfilerStart()` **之前**；
- 释放使用 `cudaFreeHost`，在 case 结束时执行，不影响 measured request 内的时间线。

### 3.2 `cudaDeviceMapHost` 设置时机（case-scoped）

- 仅在 `Q0-MISSING-CORR-001` 这一条进程内设置
  `cudaSetDeviceFlags(cudaDeviceMapHost)`；
- 插入点是 `main()` 中 argv 解析完成之后、**首个 context-creating CUDA call 之前**
  （当前首个此类调用是 `Resources` 构造中的 `cudaGetDeviceProperties`）；
- `cudaGetDeviceProperties` 属性检查必须发生在 flags 设置之后，不得因提前查询属性而让
  flags 设置过晚；
- 能力 gate 使用 `properties.canMapHostMemory != 0`（等价于
  `cudaDevAttrCanMapHostMemory`），**不得**用 `unifiedAddressing` 代替；
- 若无法做到 case-scoped 且 pre-context，必须 STOP，不得静默改为全局设置。

### 3.3 同步原语

- device 侧：`cuda::atomic_ref<unsigned int, cuda::thread_scope_system>::store(1, release)`；
- host 侧：同类型 `load(acquire)`；
- 只使用 store / load，不使用 RMW；
- **不使用** `volatile` fallback，也不保留其为正式路径；
- **不使用** `__threadfence_system()`；
- 该形式要求 `<cuda/atomic>` 头（当前源文件只包含 `<atomic>`）；
- 规范依据：system-scope release store 使 store 对 host 可见；host 一旦 acquire load 观察到 `1`，
  即可规范地推出同一个 kernel 已开始执行。单一 sentinel 没有需要额外排序的其它 payload。
- 若 CUDA 12.4 服务器 build 无法编译该形式，必须 STOP 回到 amendment review，
  不得静默 fallback、不得添加 `-arch`、不得修改 build flags。

### 3.4 编译依赖

system-scope atomic 需要显式 codegen target，因此本 amendment 显式依赖已批准的 build contract：

- 整份 Q0 binary 固定 `-arch=sm_89`；
- build receipt 记录 exact argv / nvcc / `gpu_arch`；
- `can_map_host_memory` 由正式 target preflight 在任何 Q0 case 前验证 `== 1`。

已有服务器 compile-only 证据：`CUDA 12.4.131 + -arch=sm_89 + system-scope atomic_ref`
compile/link `PASS`、executable created、未运行任何 GPU workload，因此不存在
`SCOPE_REVIEW_REQUIRED`。

## 4. one-way 裁决与 watchdog（冻结）

只采用 **one-way**：

```text
launch K_UNMAPPED
kernel: writes STARTED (release)
host: waits for STARTED (acquire)
host: opens S_STREAM range, then cudaStreamSynchronize
```

不采用 two-way（kernel 等待 host release）：它需要额外 host thread 或额外同步原语，且会把
measured activity 的持续时间与 host 调度耦合，改变 measured topology 而不增加规范收益。

明确禁止新增：

- 第二个 kernel / sentinel kernel；
- CUDA event、query、device gate；
- 任何额外 dependency；
- sleep / timing tuning / tolerance；
- case-id / run-id / oracle / result 特判。

watchdog 规则：

- 只用于防止 host 无限轮询，是 operational ceiling，**不是** construction 参数；
- 不参与任何 PASS 条件，不得被当作 semantic threshold；
- timeout 只能 STOP（fail closed）；
- 失败后不得调大 timeout 重跑，也不得换参数重试；
- 若仓库已有统一 process/diagnostic timeout 可复用，优先复用。

## 5. Controlled fault 边界（冻结）

controlled fault 本身**不改**：

- correlation 仍被真实删除；
- enqueue / request ownership provenance 仍按现有规则失效；
- handshake 只负责提供独立、确定的 `GPU_STARTED_BEFORE_SYNC` submission proof。

`q0_faults.py` 保持 zero-diff。不得用 case-id 特判、不得为通过用例而弱化 fault。

## 6. Synthetic 对齐（冻结）

synthetic proxy 必须与 real construction 语义同构，表达三个结构事实：

```text
correlation absent
enqueue provenance absent
activity.start < sync.host_start
```

并**经正常 `sync_semantics` 推导链**得到：

```text
primary_reason = MISSING_ACTIVITY_CORRELATION
secondary_reasons = []
```

当前 `q0_synthetic.py` 对 `Q0-MISSING-CORR-001` 直接注入
`ownership_status="INVALID"` / `ownership_reasons=("MISSING_ACTIVITY_CORRELATION",)`，
属于预置最终 semantic conclusion，必须改为结构事实输入后由正常化链推导。
不得预置 ownership status、reason、wait set、terminal 或 B 状态。

## 7. Scope（冻结）

REQUIRED native：

- `q0/cuda/exposedpath_q0.cu`
  - 新增 `q0_spin_kernel_signaled`（仅 Missing-Corr 使用）；
  - Missing-Corr case 的 handshake 与 `S_STREAM` 打开顺序；
  - sentinel allocation / mapping / free 与 `cudaSetDeviceFlags(cudaDeviceMapHost)` 的
    case-scoped pre-context 插入点；
  - `properties.canMapHostMemory != 0` 的 native fail-closed guard；
  - `q0_spin_kernel` 与 `warmup_kernel_memop` 保持不变。

REQUIRED synthetic：

- `exposedpath_v141/q0_synthetic.py`（仅该 case 改为结构事实输入）。

REQUIRED tests：

- `tests/test_v141_q0_cuda_source.py`
  - `q0_spin_kernel_signaled` 的存在与仅 Missing-Corr 使用；
  - 单 block / 单 thread / measured stream / 35 ms 形状不变；
  - sentinel allocation 与 `cudaSetDeviceFlags` 位于 `cudaProfilerStart()` 之前；
  - host 打开 `S_STREAM` 前存在 STARTED 观察；
  - system-scope `atomic_ref` release/acquire，无 `volatile`、无 `__threadfence_system()`；
  - `q0_spin_kernel` 未被修改；
  - formal path 未新增 `cudaDeviceSynchronize`。
- `tests/test_v141_q0_synthetic.py`
  - 该 case 由结构事实推导，不预置最终 reason / ownership。

REQUIRED docs：

- 本 amendment；
- implementation 阶段如需在 runbook 增补正式 run 前置检查，归
  `gate6_q0_build_contract_amendment_v0_1.md` 已批准的 docs scope，不重复扩大。

## 8. Zero-diff 清单

- `exposedpath_v141/q0_faults.py`；
- Q0 oracle（`q0/oracle_cases_v0_2.json`）；
- Measurement Contract（`measurement_contract_v0_2.json` / `.md`）；
- Canonical；
- S / A / B semantics 与 implementation；
- evaluator（`q0_evaluator.py`）；
- `q0_gate.py`；
- 23-case composition 与 execution manifest / schema；
- run manifest schema（`exposedpath-q0-run/0.2.1`）；
- `exposedpath_v141/cli.py`、`exposedpath_v141/q0_execution.py`、
  `exposedpath_v141/q0_collection.py`（后两者只属于 build-contract amendment 的 scope）；
- Gate 6 PASS criterion。

package `__version__` 不在本 amendment 内修改；`0.2.0 -> 0.2.1` 由 Marker Ownership
amendment 独立负责。

## 9. Invariants

- 该 case 仍恰好有 1 个 measured GPU activity，符号为 `q0_spin_kernel_signaled`，
  NVTX label 仍为 `K_UNMAPPED`；
- `K_UNMAPPED.start < S_STREAM.host_start` 由 handshake 结构性保证，不依赖 sleep 或统计假设；
- handshake 只影响 submission proof，不改变 correlation 缺失这一 primary；
- sentinel 只承载"kernel 已开始执行"这一事实，不得被解释为 completion、overlap 或 exposure 证据；
- primary / secondary 组合必须完全确定：`MISSING_ACTIVITY_CORRELATION` + `[]`；
- real 与 synthetic 必须由等价结构事实导出同一结果；
- 不新增 machine-schema enum。

## 10. Hard STOP

以下任一情形必须立即停止并回报，不得自行扩大 scope：

- 新增第二个 sentinel kernel、CUDA event / query / device gate 或额外 dependency；
- 使用 sleep / timing tuning / tolerance；
- 使用 `volatile` 或 `__threadfence_system()` 作为正式路径；
- 修改 `q0_spin_kernel` / `warmup_kernel_memop` 或影响 `Q0-KERNEL-MEMOP-001` warm-up；
- `canMapHostMemory == 0` 或改用 `unifiedAddressing` 作为 gate；
- 无法保证 `cudaSetDeviceFlags(cudaDeviceMapHost)` 位于首个 context-creating call 之前；
- 为通过用例修改 oracle / evaluator / Measurement Contract / Canonical / S / A / B；
- case-id / run-id / result 特判；
- synthetic 继续预置最终 semantic conclusion；
- 失败后换参数、换 arch 或调大 timeout 重跑；
- 改动第 7 节 scope 之外的文件。

## 11. `final-01` disposition（文档叙述，不新增 machine-schema enum）

`q0-win-4090-20260919-gate6-final-01` 保持 frozen incomplete Engineering run：
不重跑已执行 case、不续跑剩余 evaluator、不拼接、不重派生升级为 Gate PASS、无 gate report；
Raw / SQLite / Canonical / S / A-B 与已有 real evidence 只读保留。本 amendment 不下调该 run
的既有 real FAIL 判定。

## 12. Migration / acceptance

1. amendment 批准（本文件）；
2. unified implementation（本 amendment + Phase-Spill + Marker Ownership + build contract
   在同一 implementation commit 冻结）；
3. offline validation：targeted tests、`tests/test_v141_q0_*.py` offline regression、
   `python -m compileall -q exposedpath_v141 tests`、`git diff --check`；
4. server rebuild + identity verification（compile-only；不得运行任何 Q0 case）；
5. 所有前置成立后，才允许新 run-id 下**唯一一次**完整 21 real + 2 synthetic Q0；
6. 唯一 gate report 达 23/23 才可能使 Gate 6 PASS。

当前正式状态保持：Gate 6 = `FAIL`、Q0 = `NOT_RUN`、Gate 7 = `BLOCKED/暂停`、Gate 8 未启动。
