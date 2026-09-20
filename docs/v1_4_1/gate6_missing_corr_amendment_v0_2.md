# Gate 6 Missing-Corr Amendment v0.2：oracle 期望与 construction 回退

状态：**批准（2026-09-20）**
适用范围：Gate 6 / Q0 Qualification，仅涉及 `Q0-MISSING-CORR-001` 的 oracle 期望、native construction、
synthetic 对齐与 `can_map_host_memory` capability 地位
canonical baseline 分支：`codex/gate6-canonical-baseline`
canonical implementation commit（unified implementation）：`97054163b661870fe98db0cedff5657f71d69500`
frozen runs：`q0-win-4090-20260919-gate6-final-01`、`q0-win-4090-20260919-gate6-final-02`（均为 frozen
incomplete Engineering run，不得 retry / resume / 重派生 / 升级）
supersede：`docs/v1_4_1/gate6_missing_corr_amendment_v0_1.md` §2 / §3 / §4 及其中与 sentinel 相关的
native / tests 条目；`docs/v1_4_1/gate6_q0_build_contract_amendment_v0_1.md` §4 的
`can_map_host_memory` hard gate 与 case 内 native guard

本文件冻结 Missing-Corr 的规范测试意图、v0.1 handshake 被否决的 diagnostic 依据、oracle 期望修订、
construction 回退、synthetic 对齐、capability 地位调整、scope、zero-diff 清单、invariants 与 STOP 条件。

本 amendment **不**处理：

- Phase-Spill observational boundary（`gate6_phase_spill_amendment_v0_1.md`）；
- External / Multithread-Ordered / Overlapping-Host-Sync 的 marker ownership 规则
  （`gate6_marker_ownership_amendment_v0_1.md`）；
- controlled fault 注入语义（`q0_faults.py` 的 `REMOVE_ACTIVITY_CORRELATION` 保持 zero-diff）；
- Q0 build architecture 与 build receipt（`gate6_q0_build_contract_amendment_v0_1.md` §2 / §3 继续有效）。

## 1. 规范测试意图（冻结）

`Q0-MISSING-CORR-001` 为 `NEGATIVE`、`required_for_q0 = true`、features `MISSING_CORRELATION`、
required contract rules `MC-S-002` / `MC-S-013`。本 case 真正要验证的是：

```text
primary_reason = MISSING_ACTIVITY_CORRELATION
validity       = INVALID
```

即「必需证据（activity correlation）缺失时必须 fail closed，并给出冻结的 versioned reason，
不得把未知转换为零值」。Measurement Contract 同时要求把**真实观测到的**其余 reason 保留在
`secondary_reasons`（`measurement_contract_v0_2.md` §9：primary 按优先级选择，其余保存在 secondary；
机器合同 `s_layer.reason_output`：`primary_reason = highest_priority_reason`、
`secondary_reasons = all_remaining_observed_reasons_in_priority_order`）。

在目标 Windows/WDDM 栈下，普通 construction：

```text
launch K_UNMAPPED
  -> S_STREAM（sync_range）
  -> cudaStreamSynchronize(r.first)
```

无法独立证明 `GPU_STARTED_BEFORE_SYNC`：request 内 launch 之后不存在 submission 进展，直到出现
flush 型调用，而该 case 中第一个此类调用就是 `S_STREAM` 自身；因此在 correlation 已被 controlled
fault 真实删除、enqueue provenance 同时失效的前提下，submission proof 只会落在
`SUBMISSION_ORDER_AMBIGUOUS`（rank 6）一侧，而 `MISSING_ACTIVITY_CORRELATION`（rank 5）仍是 primary。

冻结后的期望为：

```text
primary_reason    = MISSING_ACTIVITY_CORRELATION
secondary_reasons = ["SUBMISSION_ORDER_AMBIGUOUS"]
validity          = INVALID
wait_set          = []
terminal          = INVALID / NONE
b_status          = B_INVALID
a_relations       = ["whole_sync=A_unattributed"]
```

明确不变：

- 不修改 reason ranking；
- 不修改 analyzer（`sync_semantics.py` 的既有实现与测试已按上述优先级输出正确结果）；
- 不修改 Measurement Contract；
- `secondary_reasons = []` 在「submission order 已被证明」的形状下仍是正确期望，本 amendment 只把
  该 case 的期望对齐到目标栈**可实现**的形状。

## 2. v0.1 handshake 被否决（diagnostic evidence）

v0.1 的 one-way same-activity mapped-sentinel handshake 要求 host 在观察到同一 kernel 写出的 STARTED
之后才打开 `S_STREAM`。独立 Engineering diagnostic 已逐项否决该路线（均为 Engineering 诊断，
不构成 Q0 证据，且不得重跑）：

| diagnostic | 结果 |
| --- | --- |
| pure host poll（sentinel polling，无 flush 型调用） | kernel queue ≈ 30 s；final-02 实测 `cudaLaunchKernel API end = 22,610,034 ns`、`Queue Dur = 30,001,262,644 ns`、kernel start = `30,023,872,678 ns`、watchdog = 30 s → 未观察到 STARTED |
| `cudaStreamQuery` exactly once | 可推动 submission（`cudaErrorNotReady`、15.5 µs、`observed_before_sync = true`、`observe_latency = 26.3 µs`、`sentinel_before_sync = 1`），但该 API 在目标栈已有 synchronization-activity 污染证据（`EP-ISSUE-12`：request 内 31 条无 Runtime 映射的 synchronization activity），故放弃 |
| pre-capture same-kernel warm-up | measured `Queue Dur = 5,000,174,675 ns`，`cudaStreamSynchronize` 在 launch API end 后约 5.000023 s 才开始，kernel 在 sync 开始约 151.5 µs 后才启动 → 无效 |
| `cudaStreamGetFlags` exactly once | measured queue ≈ 5 s → 无效 |

结论（冻结）：在目标栈上「同时保证 `K_UNMAPPED.start < S_STREAM.host_start`」与「measured request 内
零额外 sync/query/dependency footprint」目前没有已证实可行的 construction；问题不是 tuning，也不得
通过新 CUDA API probe、sleep、tolerance 或 watchdog 调参解决。

因此正式 construction 回退为普通形状：

```text
launch K_UNMAPPED
  -> S_STREAM
  -> cudaStreamSynchronize(r.first)
```

并删除 sentinel / watchdog / system-scope atomic 相关的全部 construction：

- 不新增 `q0_spin_kernel_signaled` 或任何第二个 kernel；
- 不新增 mapped host allocation、`cudaHostGetDevicePointer`、`cudaSetDeviceFlags(cudaDeviceMapHost)`
  的 case-scoped 设置；
- 不新增 `cuda::atomic_ref<..., thread_scope_system>` 依赖，`<cuda/atomic>` 在无其它使用方时不再需要；
- 不新增 host polling 与 watchdog 常量；
- `q0_spin_kernel`、`warmup_kernel_memop` 与 `Q0-KERNEL-MEMOP-001` 的
  `PRE_CAPTURE_SAME_KERNEL_WARMUP` 规则保持不变。

## 3. Oracle amendment（冻结）

`q0/oracle_cases_v0_2.json` 中 `Q0-MISSING-CORR-001`：

- `expected.syncs[0].secondary_reasons` 改为 `["SUBMISSION_ORDER_AMBIGUOUS"]`；
- `construction` 时间戳同步改成 submission-order-ambiguous 的形状（`K_UNMAPPED` 不再整体早于
  `S_STREAM.host_start`，例如 activity `60..95`、sync `50..90`），使 oracle 的构造与期望自洽；
- `wait_set_activity_labels`、`terminal`、`validity`、`b_status`、`a_relations`、`b_relations`
  均不改变；
- 其它 22 个 case 的 construction / expected 不改变。

版本策略：

- `oracle_version` 保持 `exposedpath-q0-oracle-0.2.0`；本 case 的**内容** revision 由 oracle 文件
  SHA256 与本 amendment commit 共同区分；
- 不修改 execution / run schema（`q0_execution_schema_v0_2.json` 的 `oracle_version` const 不变）；
- 不修改 `exposedpath-q0-comparison/0.2.0` 比较语义：evaluator 仍对 `secondary_reasons` 做精确相等比较，
  不引入 subset、不忽略 secondary、不特判 case-id。

## 4. Synthetic 对齐（冻结）

synthetic structural proxy 必须继续只输入**结构事实**并经正常 `sync_semantics` 推导链得出结果：

```text
correlation absent
enqueue provenance absent
activity.start >= sync.host_start
```

推导结果必须是：

```text
primary_reason    = MISSING_ACTIVITY_CORRELATION
secondary_reasons = ["SUBMISSION_ORDER_AMBIGUOUS"]
```

禁止预置 ownership status、ownership reason、wait set、terminal、validity 或 B 状态；禁止按 case-id
注入最终语义结论。real 与 synthetic 必须在上述结构事实上同构。

## 5. `can_map_host_memory` 地位调整（冻结）

sentinel 删除后，`can_map_host_memory` **不再是正式 Q0 的 hard capability gate**：

- 字段继续由 `--environment-json` / collection 记录，并继续要求存在（缺失仍 fail closed）；
- `can_map_host_memory == 0` 不再自动拒绝正式 collection；
- Missing-Corr case 内不再保留 `properties.canMapHostMemory != 0` 的 native guard；
- `unifiedAddressing` 仍不是 capability gate。

`gate6_q0_build_contract_amendment_v0_1.md` §2 的 `-arch=sm_89` 与 §3 的 build receipt 规则**保持不变**
（显式 codegen architecture、receipt、source/binary SHA、nvcc 版本、compile argv 继续按该文件执行）；
其 evidence basis 中「不带 `-arch` 时 system-scope atomic 编译失败」的记录降级为历史依据，不影响
显式 `-arch=sm_89` 的现行要求。

## 6. Scope（冻结，本轮不 implementation）

REQUIRED production：

- `q0/oracle_cases_v0_2.json`（§3）；
- `q0/cuda/exposedpath_q0.cu`（§2 回退与 sentinel / watchdog / atomic 删除）；
- `exposedpath_v141/q0_synthetic.py`（§4 structural 输入）；
- `exposedpath_v141/q0_collection.py`（§5：保留字段与必填校验，删除 `== 1` 的 capability 拒绝）。

REQUIRED tests：

- `tests/test_v141_q0_cuda_source.py`（该 case 与其它 case 同形、无 sentinel / 无额外 API / 无 polling）；
- `tests/test_v141_q0_synthetic.py`（structural proxy 推导出上述 reason 组合且不预置结论）；
- `tests/test_v141_q0_collection.py`（字段仍必填且被记录，`can_map_host_memory == 0` 不再拒绝）。

REQUIRED docs：

- 本 amendment；
- `gate6_missing_corr_amendment_v0_1.md` 与 `gate6_q0_build_contract_amendment_v0_1.md` 的 supersede 注记；
- implementation 阶段同步 `docs/v1_4_1/gate6_windows_server_runbook.md` 前置检查
  （移除 `can_map_host_memory != 1` 的 STOP，保留字段记录与 `sm_89` / receipt / binary SHA 校验）。

## 7. Zero-diff 清单

- `exposedpath_v141/sync_semantics.py`（analyzer 已按合同正确输出，且已有冻结测试覆盖该组合）；
- reason ranking 与 `reason_output`；
- Measurement Contract（`measurement_contract_v0_2.json` / `measurement_contract_v0_2.md`）；
- Canonical 与 `exposedpath_v141/q0_faults.py`；
- A / B 定义与实现；
- evaluator（`q0_evaluator.py`，含精确相等的 `secondary_reasons` 比较）；
- `q0_gate.py`；
- execution / run schema 与 23-case composition；
- S schema 与 `sync_semantics_registry_v0_2.json`；
- package `__version__`（本 amendment 不改变 analyzer 语义）；
- 四份已批准 amendment 文档的既有正文（只新增 supersede 注记）；
- `docs/v1_4_1/research_progress.md`（由独立 checkpoint 记录，不在本 amendment 内修改）。

## 8. Invariants

- 该 case 仍恰有一个 measured GPU activity，label 仍为 `K_UNMAPPED`，stream / launch config /
  时长与 NVTX identity 与其它 case 同形；不新增第二个 kernel、event、query、device gate 或 dependency；
- measured request 内零额外 sync / query / dependency footprint；
- `primary_reason` 必须是 `MISSING_ACTIVITY_CORRELATION`，`validity` 必须是 `INVALID`；
- `secondary_reasons` 必须是 `["SUBMISSION_ORDER_AMBIGUOUS"]`，且该值由真实 S 记录中的
  `submission_evidence` 支持；
- real 与 synthetic 由等价结构事实导出同一结果；
- 不引入 tolerance、epsilon、sleep 或 watchdog 调参；
- 不按 case-id / run-id / oracle / result 特判。

## 9. STOP 条件

- 新正式 run 若该 sync 的 `submission_evidence` 为 `PROVEN`（`GPU_STARTED_BEFORE_SYNC`），使
  `secondary_reasons` 不再等于 `["SUBMISSION_ORDER_AMBIGUOUS"]`，必须 FAIL / STOP 并重新评审
  platform submission 行为；**不得**让 oracle 或 evaluator 同时接受两种结果，不得引入 subset 比较；
- 任何试图以新 CUDA API、sleep、tolerance、watchdog 调参或手工修补 argv 的方式「恢复」
  `GPU_STARTED_BEFORE_SYNC`；
- 任何对 `sync_semantics.py`、reason ranking、Measurement Contract、Canonical、A/B、evaluator、
  `q0_gate.py`、execution/run schema、23-case composition、S schema/registry 的改动；
- synthetic 继续预置最终 semantic conclusion；
- 改动第 6 节 scope 之外的文件。

## 10. Migration / acceptance

1. amendment 批准（本文件）与两份 supersede 注记；
2. unified implementation（本 amendment + Phase-Spill + Marker Ownership + build contract 在同一
   implementation commit 冻结）；
3. offline validation：targeted tests、`tests/test_v141_q0_*.py` offline regression、
   `python -m compileall -q exposedpath_v141 tests`、`git diff --check`；
4. server rebuild + identity verification（compile-only；不得运行任何 Q0 case）；
5. 所有前置成立后，才允许新 run-id 下**唯一一次**完整 21 real + 2 synthetic Q0；
6. 唯一 gate report 达 `23/23 + verdict=PASS + q0_status=PASS`，Gate 6 才正式 PASS。

`q0-win-4090-20260919-gate6-final-01` 与 `q0-win-4090-20260919-gate6-final-02` 均保持 frozen
incomplete Engineering run：不 retry、不 resume、不拼接、不重派生、不升级为 Gate PASS，也不生成
补丁式 gate report；其既有 real FAIL 判定不下调。当前正式状态保持：Gate 6 = `FAIL`、
Q0 = `NOT_RUN`、Gate 7 = `BLOCKED/暂停`、Gate 8 未启动。
