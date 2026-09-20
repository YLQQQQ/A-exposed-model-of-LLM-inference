# Gate 6 Unified Marker Ownership Amendment v0.1：跨线程 marker authority 与 request-scope provenance

> **后记（2026-09-20）：** 本文档为冻结的 amendment 记录，其 requirement 内容不变；正文中“Gate 6 = `FAIL` / Q0 = `NOT_RUN` / 待 implementation / Gate 7 暂停”等描述均为批准时刻的历史状态，已由 Gate 6/Q0 `PASS`（`q0-win-4090-20260920-gate6-final-04`，package `0.2.2`）取代。当前状态见 `docs/v1_4_1/research_progress.md` 与 `docs/v1_4_1/gate6_closeout_v0_1.md`。

状态：**批准（2026-09-19）**
适用范围：Gate 6 / Q0 Qualification，仅涉及 `Q0-EXTERNAL-001`、`Q0-MULTITHREAD-ORDERED-001`、`Q0-OVERLAPPING-HOST-SYNC-001` 的 S 层 ownership 证据规则
canonical baseline 分支：`codex/gate6-canonical-baseline`
canonical implementation commit：`2e81f6f9a9ec590d37fb01be9e31f2251645c5d1`
frozen run：`q0-win-4090-20260919-gate6-final-01`（frozen incomplete Engineering run，不得重跑/续跑/重派生/升级）

本文件冻结 Unified Marker Ownership amendment 的证据基础、统一 marker authority model、
ownership 裁决、worker sync ownership 传播规则、`cudaEventRecord` native
instrumentation、External 规则的收窄适用范围、synthetic 对齐要求、版本与 provenance
策略、不变量、scope、zero-diff 清单与 STOP 条件。

本 amendment **不**处理：

- `Q0-MISSING-CORR-001`（其 remediation 仍未批准，另案处理）；
- Phase-Spill 的 implementation（已由 `gate6_phase_spill_amendment_v0_1.md` 单独批准）。

本 amendment 不修改 Measurement Contract、Q0 oracle、Canonical、A/B 实现与 schema、
evaluator、`q0_gate.py`、execution manifest / 23-case composition、Gate 6 PASS 判据、
sync registry 与 S schema。

## 1. Evidence basis

### 1.1 冻结 run

```text
q0-win-4090-20260919-gate6-final-01
```

该 run 为 frozen incomplete Engineering run：Raw/SQLite/source Canonical 21/21、
controlled fault Canonical 3/3、S bundles 21/21、A/B bundles 21/21、real evidence 已生成
16、real PASS 12、real FAIL 4、`Q0-PHASE-SPILL-001` evaluator 因 analyzer blocker 未完成、
synthetic 与 gate aggregation 未运行、无 `q0_gate_report.json`。

与本 amendment 直接相关的三个 case 的最终 S 事实为：

```text
Q0-EXTERNAL-001
  S_DEVICE: VALID_NONEMPTY / wait_set={K_EXTERNAL} / terminal=K_EXTERNAL
            B_VALID / submission=ENQUEUE_COMPLETED_BEFORE_SYNC(PROVEN)
  full_request = 41,625,075 .. 81,872,785
  K_EXTERNAL   = 41,687,740 .. 81,688,566
  S_DEVICE     = 41,642,451 .. 81,709,120

Q0-MULTITHREAD-ORDERED-001
  S_THREAD_B: INVALID / INVOCATION_BOUNDARY_INVALID + MISSING_EVENT_RECORD
              request_id=null / repeat_id=null / sync_owner_phase=null
              dependency_edges=[] / activity_origin_phases={}
  WORKER_THREAD_A    = 23,832,896 .. 24,438,774   (thread 431132)
  K_THREAD_A marker  = 24,441,177 .. 25,787,214   cudaLaunchKernel corr=127
  cudaEventRecord                                 corr=129, event_id=1
  WORKER_THREAD_B    = 28,057,366 .. 28,651,487   (thread 193700)
  cudaStreamWaitEvent                             corr=130, event_id=1
  K_THREAD_B marker  = 28,702,423 .. 28,742,032   cudaLaunchKernel corr=131
  S_THREAD_B marker  = 28,745,357 .. 89,016,688
  cudaStreamSynchronize                           = 28,746,238 .. 89,013,403
  K_THREAD_A device  = 28,875,449 .. 53,876,309
  K_THREAD_B device  = 53,966,037 .. 88,966,881

Q0-OVERLAPPING-HOST-SYNC-001
  S_A: INVALID / INVOCATION_BOUNDARY_INVALID   sync_ordinal=0
  S_B: INVALID / INVOCATION_BOUNDARY_INVALID   sync_ordinal=1
  S_A = 22,514,632 .. 63,220,988  (thread 172596, stream 13)
  S_B = 23,755,625 .. 73,069,996  (thread 247696, stream 14)
  host-sync overlap = 39,465,363 ns
  K_A device = 23,020,505 .. 63,021,342
  K_B device = 23,018,905 .. 73,019,623
```

### 1.2 源码事实（判定依据，不依赖运行结果）

marker 与 identity 产生方式：

- `q0/cuda/exposedpath_q0.cu:83-104` `identity_json()`：payload 为
  `EXPOSEDPATH_JSON_V1:{...}`，`request_id` 直接取 `case_id`，含 7 字段 invocation
  identity、`phase`、`callsite_id`（`kind=sync` 时另有 `sync_origin`/`sync_ordinal`）。
- `q0/cuda/exposedpath_q0.cu:115-123` `marker_range()` / `worker_marker()`：`kind=marker`。
- `q0/cuda/exposedpath_q0.cu:140-143` `sync_range()`：`kind=sync`。
- `q0/cuda/exposedpath_q0.cu:194-200` `launch()`：在 `cudaLaunchKernel` 外包一层
  covering `kind=marker`。
- `q0/cuda/exposedpath_q0.cu:247-252` `one_phase()`：唯一 `full_request` + 内嵌 `decode`。

S 层当前实现（缺陷位置）：

- `exposedpath_v141/sync_semantics.py:172-237` `_phase_ownership()`：只接受**同线程**
  `kind ∈ {request, phase}` 范围，marker 不参与。
- `exposedpath_v141/sync_semantics.py:240-266` `_trusted_activity_marker_identity()`：
  marker 可信性校验（text 可重解析、与缓存 `structured_identity` 完全一致、字段完整）。
- `exposedpath_v141/sync_semantics.py:269-378` `_activity_ownership()`：接受同线程
  covering marker，但**没有**与 matching request 的时间包含校验 → activity authority 过强。
- `exposedpath_v141/sync_semantics.py:441-507` `_normalize_sync()`：ownership 只走
  `_phase_ownership()`，sync marker 仅提供 `sync_origin`/`callsite_id`/`sync_ordinal`
  → worker sync authority 过弱。
- `exposedpath_v141/sync_semantics.py:510-549` `_normalize_event_record()`：ownership 只走
  `_phase_ownership()`。
- `exposedpath_v141/sync_semantics.py:748-793` `_capture_event_prefixes()` 与
  `:809-851` `_add_stream_wait_edges()`：event ownership 非 VALID 时不创建 event node，
  wait 边因此追加 `MISSING_EVENT_RECORD`。
- `exposedpath_v141/sync_semantics.py:1136-1148` `_ordered_reasons()`：primary/secondary
  由 Measurement Contract 的 rank 决定。

契约与规范依据：

- `docs/v1_4_1/contracts/measurement_contract_v0_2.json:179`：
  `EXTERNAL_OWNERSHIP_IN_SCOPE` 属 rank 2 `BOUNDARY_AND_OWNERSHIP`、`default_validity=INVALID`；
  MC-S-007 `wait_set_members_require_supported_request_ownership`、MC-S-009
  `temporal_overlap_never_creates_dependency`、MC-S-013
  `insufficient_evidence_fails_closed_with_versioned_reasons`。
- `docs/v1_4_1/measurement_contract_v0_2.md:89,118`：存在无法恢复的 context 或外部
  ownership 时相关同步 fail closed；primary reason 优先级中「请求边界与确定的外部
  ownership」位于 ownership 歧义、支持性、映射、closure 歧义之前。
- `docs/v1_4_1/s_layer_v0_2.md:11`：当前明文规定 Host blocking sync 只使用其 runtime
  API 所在的 request/phase 区间恢复 owner phase —— 本 amendment 明确修订该句。
- `docs/superpowers/specs/2026-09-17-s-activity-marker-ownership-design.md` §4：
  明文要求「不得全局放宽现有 `_phase_ownership()`」—— 本 amendment 明确 supersede
  该条限制（历史原文不重写）。

结论：本次 INVALID 不是平台问题，而是 marker authority 的**双向**缺陷 —— activity
marker authority 过强（request 外 marker 可把 External activity 吸进 invocation），
sync/event worker marker authority 过弱（携带 identity 仍不能传播 invocation
ownership）。

## 2. 统一 marker authority model（冻结）

一个 structured marker 只有同时满足以下全部条件，才可以对目标 API 提供 invocation
ownership：

1. marker 与目标 API 位于同一 host thread；
2. marker 使用半开区间完整包含 API interval（`marker.start <= api.start` 且
   `api.end <= marker.end`）；
3. structured payload 可重新解析（`EXPOSEDPATH_JSON_V1:` 前缀 + JSON）；
4. payload 与 Canonical cached `structured_identity` 精确一致；
5. 7 字段 invocation identity（`experiment_id`、`wmpc_id`、`run_id`、`run_role`、
   `pass_id`、`request_id`、`repeat_id`）完整、非空；
6. 该 identity 对应**唯一** matching `kind=request` range；
7. current-invocation ownership 要求 marker/API interval 被该 matching request
   **时间包含**；
8. 若 marker 声明 phase，则还要求存在 identity **与 phase 值**同时相等的唯一
   matching `kind=phase` range，且 marker/API interval 被其时间包含；
9. request/phase range 可以位于另一 host thread（cross-thread temporal containment）；
10. zero 个 matching、多个 matching、identity/phase 冲突、partial overlap 一律
    fail closed；
11. 不得仅凭相同 `request_id` 字符串授权；
12. 不得按 case-id / run-id / oracle / result 特判；
13. 不得引入 tolerance / epsilon。

核心条件冻结为：

```text
same-thread API containment
+ trusted re-parsed structured payload
+ full identity
+ unique matching request/phase by identity
+ cross-thread temporal containment
+ fail-closed on zero/multiple/conflict/partial
```

## 3. Ownership 裁决（冻结）

### 3.1 `PROVEN_CURRENT_INVOCATION`

唯一 matching request 存在，且 marker/API 完整位于该 request 内；声明 phase 时也完整
位于唯一 matching phase 内。→ 维持现有 VALID ownership 语义与 origin phase。

### 3.2 `PROVEN_EXTERNAL_TO_REQUEST` → `EXTERNAL_OWNERSHIP_IN_SCOPE`

仅当以下全部成立：

- 目标 activity 由 trusted activity launch marker/API 恢复（唯一 correlation）；
- 其 identity 指向唯一 matching request；
- marker/API interval 与该 request **完全不相交**；
- 且 marker/API interval **整体位于该 request 之前**；
- 该 device activity 延伸进入该 request / target sync scope。

输出：activity ownership `INVALID`，reason `EXTERNAL_OWNERSHIP_IN_SCOPE`。此时 marker
payload 中的 phase **不得**赋予当前 request 的 phase ownership。经既有 reason 传播
路径，目标同步得到 primary=`EXTERNAL_OWNERSHIP_IN_SCOPE`（rank 2）、空 wait set、
`INVALID/NONE` terminal 与 `B_INVALID`，与 oracle 一致。

### 3.3 其它情况（一律 fail closed）

| 情形 | 裁决 |
|---|---|
| marker/API 与该 request 部分相交（partial overlap） | `INVOCATION_BOUNDARY_INVALID` |
| identity 相等的 matching request 为 zero | `INVOCATION_BOUNDARY_INVALID` |
| matching request 为 multiple | `INVOCATION_OWNERSHIP_AMBIGUOUS` |
| marker/API 整体位于 request **之后** | `INVOCATION_BOUNDARY_INVALID`（本 amendment **不**分类为 external） |

不得引入 `NEEDS_REVIEW` machine reason；“entirely AFTER” 情形保持 fail-closed，如需
分类必须另立 amendment。

### 3.4 External 规则的收窄适用范围与逐 case 影响

本 amendment 只批准 frozen evidence 已证明的形态（request 之前的 disjoint
launch）。逐 case 影响：

| case | construction 形态（源码） | 本 amendment 后 |
|---|---|---|
| `Q0-EXTERNAL-001` | marker/launch 在 `one_phase` 之前（cu:398-404） | VALID → `EXTERNAL_OWNERSHIP_IN_SCOPE`（唯一预期变化） |
| `Q0-MULTITHREAD-ORDERED-001` | worker sync/event 无 owner（cu:438-455） | sync ownership 恢复 + event node 建立 |
| `Q0-OVERLAPPING-HOST-SYNC-001` | 两个 worker sync（cu:457-474） | 两条 sync ownership 恢复 |
| `Q0-INVOCATION-BLEED-001` | prior request+phase range 存在（cu:489-499） | 不变：prior marker 仍被 identity 相等的 prior request 包含 → `INVOCATION_BLEED` |
| `Q0-COMPLETED-001` | launch+marker 在 request 内，host sleep 无 marker | 不变 |
| `Q0-KERNEL-MEMOP-001` | worker marker 落在 coordinator request 内（cu:320-340） | 不变（EP-G6-09 修复不回退） |
| `Q0-DEFAULT-PTDS-001` | `K_OTHER_THREAD` covering marker 在 coordinator request 内（cu:415-436） | 不变 |
| `Q0-PHASE-SPILL-001` | prefill marker 在 request+prefill 内（cu:476-487） | 不变（要求 identity+phase 双匹配） |
| `Q0-EVENT-001` / `Q0-EVENT-XSTREAM-001` / `Q0-QUERY-001` | record/wait 在 request 内同线程 | 不变（原同线程路径） |
| `Q0-GRAPH-UNSUPPORTED-001` | capture/instantiate 在 request 外但无 marker | 不变（无 marker 不参与） |
| `Q0-MISSING-CORR-001` / `Q0-DROPPED-001` | 无 correlation / schema 白名单路径 | 不变 |
| harness drain / request 外 trailing sync 行 | request 外、无 marker | 仍 INVALID；仅 reason 归属需回归确认 |

## 4. Worker-thread sync ownership（冻结）

`kind=sync` marker 在满足第 2 节 unified trusted-marker 条件后，可以**跨 host thread**
通过 matching request/phase 的时间包含，向 Host blocking sync 传播：

- `request_id`
- `repeat_id`
- `sync_owner_phase`

原有同线程 request/phase ownership 路径**保持不变**；本规则是附加且更严格受
provenance 约束的 fallback。conflict / duplicate / partial marker 继续 fail closed
（`INVOCATION_OWNERSHIP_AMBIGUOUS` / `PHASE_OWNERSHIP_AMBIGUOUS` /
`INVOCATION_BOUNDARY_INVALID`）。

## 5. `cudaEventRecord` native instrumentation（冻结）

明确 frozen fact：当前 Multithread construction 的 `cudaEventRecord`（corr=129）**没有**
covering trusted marker；因此 native amendment 必须新增 `EVENT_RECORD_THREAD_A`。

精确形状：

```text
launch K_THREAD_A
marker_range(... "EVENT_RECORD_THREAD_A") {
    cudaEventRecord(...)
}
```

要求：

- `kind=marker`；
- 与 `cudaEventRecord` 同 producer thread；
- 完整包含且**仅**包含 `cudaEventRecord`；
- 不与 `K_THREAD_A` marker 重叠或嵌套（`launch()` 内 marker 在函数返回时已 pop）；
- payload 使用与 `K_THREAD_A` 相同的 invocation identity + `phase=decode`，
  `callsite_id="EVENT_RECORD_THREAD_A"`；
- 不新增任何 CUDA API / event / sync / gate / dependency。

明确：`marker only = host-side provenance instrumentation`。measured ordering topology
仍然是

```text
K_A → EventRecord → WaitEvent → K_B → StreamSynchronize
```

amendment 后必须真实形成：

```text
trusted EventRecord marker
  → event ownership VALID
  → event node
  → STREAM_WAIT_EVENT
  → K_THREAD_A 进入 S_THREAD_B dependency closure
  → W(S_THREAD_B) = {K_THREAD_A, K_THREAD_B}
```

不允许删除或放宽 event requirement。`cudaStreamWaitEvent` 不需要 marker（DEPENDENCY_EDGE
不进 `syncs`，边只依赖 event node）。`Q0-EVENT-001` / `Q0-EVENT-XSTREAM-001` /
`Q0-QUERY-001` 的 record 位于 request 内同线程，保持原路径，不新增 marker。

## 6. Synthetic 对齐（冻结）

对以下 3 个 proxy：

- External（`Q0-EXTERNAL-001`）
- Multithread（`Q0-MULTITHREAD-ORDERED-001`）
- Overlapping（`Q0-OVERLAPPING-HOST-SYNC-001`）

禁止继续直接注入 `ownership_status`、`ownership` 最终 reason，或其它最终 semantic
conclusion。它们必须以结构事实构造，并进入与 real path **相同**的
`sync_semantics` 正常化/推导链：

- `kind=request` / `kind=phase` ranges（含 `structured_identity` 与 text）；
- 每个 activity 的 covering structured marker 及其 `cuda_api`（唯一 correlation）；
- sync marker 与物理 sync API；
- Multithread 的 event record / wait-event 结构。

映射要求：External 必须由 structural provenance 真实推导出
`EXTERNAL_OWNERSHIP_IN_SCOPE`；Multithread 必须真实推导 worker sync ownership 与
`STREAM_WAIT_EVENT` 边；Overlapping 必须真实推导两条 worker sync ownership。

`Q0-MISSING-CORR-001` 的 synthetic 本 amendment **不修改**。

实现阶段若发现必须新增 synthetic helper module，**STOP**，先做 scope review。

## 7. Versioning 与 provenance 策略（冻结）

- `exposedpath-s-layer/0.2.0` S schema **不变**：`sync_record_fields` 集合不变，本
  amendment 只改变接受/推导规则；改版本会连带 `ab_schema_v0_2.json` 的
  `s_schema_version` const 与相关测试。
- A/B schema **不变**。
- `sync_semantics_registry_v0_2.json` 内容与 SHA-256 必须 **zero-diff**：
  `exposedpath_v141/ab_inputs.py:239-245` 校验 S manifest 的 registry version 与
  SHA-256，`ab_schema_v0_2.json` 固定 `exposedpath-sync-registry-0.2.0`，历史
  regression 证据记录 `sync_registry_sha256`。本 amendment 不涉及 API 分类、
  completion scope 或 `required_evidence`，registry 无内容需要修改。
- `s_layer_schema_v0_2.json` **zero-diff**。
- Python package / analyzer version：`0.2.0 → 0.2.1`。原因：本 amendment 改变
  analyzer semantic rules，后续 S/A-B manifest 的 `analyzer_version` 必须能与 frozen
  `final-01` 的 `0.2.0` 区分。**不得**把 package version 当作 schema version。
- Measurement Contract `0.2.0` 不改。
- `docs/v1_4_1/s_layer_v0_2.md` §2 在 **implementation 阶段**修订，并加入
  amendment / supersede 注记（修订标记为文档级 provenance，不写入机器
  `schema_version`）。
- `docs/superpowers/specs/2026-09-17-s-activity-marker-ownership-design.md` 历史内容
  **不重写**；本 amendment 明确 supersede 其中「不得放宽 `_phase_ownership()`」的
  相关规则。

## 8. Invariants

- `W(s)` 只由 correlation、ownership、submission order 与 CUDA completion semantics
  决定；时间重叠永不建立 dependency（MC-S-009）。
- marker 只提供 invocation/phase ownership 证据，永不创建 A 窗口，也永不单独建立
  dependency。
- activity origin phase 与 wall-clock exposure owner 仍是两个不同概念。
- reason 的 primary/secondary 顺序仍由 Measurement Contract rank 决定。
- invalid/ambiguous 永不降级为零值，也永不升级为 Q0、Pilot 或 Formal 证据。
- 以下全部保持不变：measured request/phase/sync topology、activity labels 与
  ownership 语义、stream/context/dependency 语义、oracle、Canonical、S 记录字段、
  A/B、evaluator、23-case composition、Gate 6 PASS 判据。

## 9. Scope（冻结）

REQUIRED production：

- `exposedpath_v141/sync_semantics.py`
- `exposedpath_v141/__init__.py`（analyzer version `0.2.0 → 0.2.1`）

REQUIRED native：

- `q0/cuda/exposedpath_q0.cu`（仅 `run_multithread` 增加 `EVENT_RECORD_THREAD_A` marker）

REQUIRED synthetic：

- `exposedpath_v141/q0_synthetic.py`（仅 3 个 in-scope case 改走结构事实 → 正常化链）

REQUIRED tests：

- `tests/test_v141_sync_semantics.py`
- `tests/test_v141_q0_cuda_source.py`
- `tests/test_v141_q0_synthetic.py`

REQUIRED docs：

- 本 amendment；
- implementation 阶段：`docs/v1_4_1/s_layer_v0_2.md`；
- implementation 阶段：对 marker ownership design spec 加 supersede 注记。

## 10. Zero-diff 清单

- Measurement Contract（`measurement_contract_v0_2.json` / `.md`）；
- Q0 oracle（`q0/oracle_cases_v0_2.json`）；
- Canonical（`canonical_raw*`、以及 `q0/cuda/exposedpath_q0.cu` 中与本 amendment
  无关的其它 case）；
- A/B implementation 与 schema（`ab_inputs.py`、`ab_bundle.py`、
  `ab_schema_v0_2.json`、`derived_schema_v0_2.json`）；
- evaluator（`q0_evaluator.py`）；
- `q0_gate.py`（只校验 real-evidence/gate `0.2.0`）；
- execution manifest / 23-case composition；
- Gate 6 PASS criterion；
- `sync_semantics_registry_v0_2.json`；
- `s_layer_schema_v0_2.json`。

## 11. Hard STOP

以下任一情形必须立即停止并回报，不得自行扩大 scope：

- case-id / run-id / oracle / result 特判；
- 仅凭 `request_id` 文本授权 ownership；
- tolerance / epsilon；
- partial-overlap marker 被当作 ownership；
- multiple candidates 时猜测；
- External 修复破坏 worker delegation；
- worker delegation 修复把 request 外 External 重新吸入 invocation；
- synthetic 继续预置最终 semantic reason；
- 修改 registry / S schema / A/B schema；
- 新增模块而未重新 scope review；
- 修改 oracle / Measurement Contract / evaluator / A/B。

## 12. Migration / acceptance

1. amendment 批准（本文件）；
2. unified implementation（production / native / synthetic / tests，同一
   implementation commit）；
3. offline review 与定向测试（含 External 推导、worker sync/event ownership、
   synthetic 结构等价、drain 行不回归）；
4. server rebuild + identity verification；
5. 新 run-id 下**唯一一次**完整 21 real + 2 synthetic Q0；
6. 只有唯一 `q0_gate_report.json` 达到 `23/23 + verdict=PASS + q0_status=PASS`，
   Gate 6 才正式 PASS。

## 13. `final-01` disposition（文档叙述，不新增 machine-schema enum）

`q0-win-4090-20260919-gate6-final-01` 保持 frozen incomplete Engineering run：

- 不重跑、不续跑；
- 不重派生后升级为 Gate PASS；
- 不生成补丁式 gate report；
- Raw / SQLite / Canonical / S / A-B / 已有 real evidence 只读保留。

本 amendment 的任何 implementation 结果都必须来自新的正式 run-id，不得与
`final-01` 拼接。
