# Gate 6 Sync Projection Amendment v0.1：registry-role-preserving semantic sync projection

> **后记（2026-09-20）：** 本文档为冻结的 amendment 记录，其 requirement 内容不变；正文中“final-04 尚未执行 / Gate 6 尚未 PASS”等描述均为批准时刻的历史状态，已由 Gate 6/Q0 `PASS`（`q0-win-4090-20260920-gate6-final-04`，package `0.2.2`，`final-04` 已按 fresh 21-native collection 完整重派生）取代。当前状态见 `docs/v1_4_1/research_progress.md` 与 `docs/v1_4_1/gate6_closeout_v0_1.md`。

状态：**批准（2026-09-20）**
适用范围：Gate 6 / Q0 Qualification；S 层 sync universe 成员判定、A/B 输入联结（S ↔ Canonical
correspondence）与 `q0_real` 的真实 case 投影
canonical baseline 分支：`codex/gate6-canonical-baseline`
canonical implementation commit（unified implementation）：`97054163b661870fe98db0cedff5657f71d69500`
frozen runs：`q0-win-4090-20260919-gate6-final-01`、`q0-win-4090-20260919-gate6-final-02`、
`q0-win-4090-20260920-gate6-final-03`（均为 frozen incomplete Engineering run，永远不得 retry / resume /
重派生 / 升级）
supersede：`docs/superpowers/specs/2026-09-12-gate5-accounting-design.md` §3「S sync 必须按 `sync_id`
与 Canonical physical sync 一一对应」的**实现级**联结规则，以及
`docs/superpowers/plans/2026-09-12-gate5-accounting.md` 中同一表述对应的验收条目；两者只在本
amendment 定义的 role-preserving correspondence 范围内被取代，其余内容继续有效

本文件冻结：final-03 的三个观测症状与其 registry-role-preserving 根因、角色到 semantic sync 的统一
投影规则、`UNSUPPORTED` 的 API-backed semantic sync 构造规则与去重规则、共享 helper 要求、
`q0_real` 的冻结规则、version 决策、final-04 派生边界、implementation touch list、zero-diff 清单、
invariants 与 STOP 条件。

本 amendment **不**处理：

- Q0 oracle expected 语义（`q0/oracle_cases_v0_2.json` 保持 zero-diff）；
- Measurement Contract / sync registry / Canonical schema / S schema / A/B schema（全部 zero-diff）；
- CUDA construction（`q0/cuda/exposedpath_q0.cu` 保持 zero-diff）；
- Phase-Spill、Marker Ownership、Build Contract、Missing-Corr oracle v0.2 四份已批准 amendment
  的既有结论（继续有效）。

## 1. Evidence basis（final-03 Engineering 观测，冻结为根因证据）

final-03 在 21-real evaluation 阶段停止，run 已冻结 incomplete。观测到的三个症状：

```text
Q0-QUERY-001
  Canonical cuda_sync: runtime_api_name = cudaEventQuery_v3020, runtime_mapping_count = 1
  S: registry_rule_id = NON-SYNC-QUERY-001, sync_universe_class = NON_BLOCKING_QUERY,
     sync_kind = QUERY, callsite_id = null
  q0_real.build_real_q0_case -> "存在缺失 callsite_id 的 physical sync"（CLI exit 1）

Q0-MULTITHREAD-ORDERED-001
  canonical marker EVENT_RECORD_THREAD_A（包住 cudaEventRecord）进入 non_sync_api_labels

Q0-SYNC-D2H-UNSUPPORTED-001
  Canonical 有 cudaMemcpy_v3020；S_SYNC_COPY sync marker 唯一存在并包住该 API
  但该调用没有对应 CUPTI synchronization row，S 因此完全没有 S_SYNC_COPY
  oracle expected syncs = ["S_SYNC_COPY"]
```

已生成的 21 个 real evidence 汇总（Engineering 观测，不是正式证据）：

```text
18 REAL_CASE_PASS
Q0-MULTITHREAD-ORDERED-001   = FAIL
Q0-SYNC-D2H-UNSUPPORTED-001  = FAIL
Q0-QUERY-001                 = evaluator 执行失败（未生成 verdict）
```

三者绑定同一类缺陷：**S 层 sync universe 没有按 registry role 投影，且 `q0_real` 把 S 集合无条件
当作 oracle 的 semantic sync 集合**。具体实现事实：

1. `sync_semantics.build_semantic_inventory()` 只排除 `role == "DEPENDENCY_EDGE"`
   （`exposedpath_v141/sync_semantics.py`：`"syncs": [sync for sync in normalized_syncs if
   sync["role"] != "DEPENDENCY_EDGE"]`），因此 role 为 `NON_SYNC`（universe class
   `NON_BLOCKING_QUERY`）的行仍留在 `inventory["syncs"]`，并被 `analyze_semantic_inventory()`
   分析成一条 S record。
2. `normalized_syncs` 只来自 `records["cuda_sync"]`（CUPTI `CUPTI_ACTIVITY_KIND_SYNCHRONIZATION`
   适配结果）。因此「属于同步 universe 但平台不产生该 activity row」的调用（例如
   `cudaMemcpy` 型同步 copy）永远无法进入 S。
3. `q0_real.build_real_q0_case()` 用 `request_id == case_id` 取 `relevant_s`，并要求每条记录的
   `callsite_id` 非空、再全量投影进 `syncs[]`；`callsite_id` 只能来自同线程包围该 runtime API 的
   `kind=sync` marker，而 query 调用按 construction 只有 `kind=marker`，因此该要求对
   `NON_SYNC` 行必然失败。
4. `q0_real._non_sync_api_labels()` 只判断「marker 是否包住某个 `cuda_api` 行」，不检查该 API 的
   registry role，因此 `DEPENDENCY_EDGE`（`cudaEventRecord`）与 `UNSUPPORTED`（`cudaMemcpy`）的
   marker 都会漏进 `non_sync_api_labels`。
5. `ab_inputs._load_canonical()` 与 `ab_inputs._validate_s_join()` 强制 S `sync_id` 与「Canonical
   `cuda_sync` 行（排除 `DEPENDENCY_EDGE`）」严格一一对应。该规则同时阻止了「排除 `NON_SYNC`」与
   「加入 API-backed `UNSUPPORTED`」两类修正，必须随本 amendment 一起收敛为 role-preserving
   correspondence。

本 amendment 的规则**不是**新合同：`measurement_contract_v0_2.md` §6 已逐行冻结同一张表
（event record / stream wait event 为依赖边；同步 copy 或依参数阻塞的 API 属于同步 universe 但
v0.2 不恢复 scope、整段 fail closed；event/stream query 为非阻塞查询、不建立 `W(s)`；未匹配
registry 的潜在阻塞 API 不得静默当作普通非同步 API），机器合同亦冻结
`s_layer.sync_universe_denominator = "all_physical_blocking_sync_calls_inside_the_request_or_phase_window"`。
A 层实现（`exposedpath_v141/a_accounting.py` 的 `_api_category`）**已经**按 registry role 区分
`DEVICE_DEPENDENCY_EDGE` / `NON_BLOCKING_QUERY`；本 amendment 只把 S 层与 `q0_real` 对齐到同一
权威。因此这是**实现对齐**，不是语义 redesign，也不修改任何冻结合同。

## 2. Registry-role-preserving projection（冻结）

唯一权威是 sync registry 的 `universe_class` 与由它导出的 role
（`exposedpath_v141/sync_semantics.py` 的 `_ROLE_BY_UNIVERSE`），不得按 API 名、大小写、case id
或 oracle expected 推断：

| registry role | 进入 S semantic sync | 说明 |
| --- | --- | --- |
| `HOST_BLOCKING_SYNC` | 是 | 现有 stream / device / context / event synchronize 路径 |
| `UNSUPPORTED` | 是 | 见 §3；有 mapped `cuda_sync` 时 physical row 唯一权威 |
| `NON_SYNC` | 否 | 只作为 A 的 non-submit API 事实与 `non_sync_api_labels` 证据 |
| `DEPENDENCY_EDGE` | 否 | 维持 `dependency_events` 边路径，现有行为不变 |
| `UNCLASSIFIED` | 维持现状 | 继续输出 `UNCLASSIFIED_CUDA_API` fail-closed，不合成、不静默丢弃 |

冻结要求：

- `NON_SYNC` 行不得出现在 `inventory["syncs"]`、S bundle、A/B 的 B 行或 `q0_real` 的 `syncs[]` 中；
- `NON_SYNC` 的排除是**成员判定**，不是 reason suppression：该 API 仍由 A 层与非同步标签路径
  继续承担，不得通过删记录的方式让任何 unsupported/invalid 事实消失；
- `HOST_BLOCKING_SYNC` 与 `UNSUPPORTED` 的 W(s)、terminal、validity、reason 计算保持 zero-diff；
- `IN_UNIVERSE_UNSUPPORTED` 的现有 fail-closed 结果（`UNSUPPORTED_SYNC_API`、空 `W(s)`、
  `INVALID` terminal、整段 `A_unattributed`）不得被本 amendment 放松。

## 3. `UNSUPPORTED` 的 API-backed semantic sync（冻结）

对 canonical `cuda_api` 行 `a`：

### 3.1 有 mapped `cuda_sync` row

physical row 是唯一权威，**禁止**再构造 API-backed 记录（避免同一调用出现两条 semantic sync）。

### 3.2 无 mapped `cuda_sync` row

仅当以下全部成立时才构造 deterministic API-backed semantic sync：

1. `classify_cuda_api(a.api_name)` 的 role 为 `UNSUPPORTED`；
2. **确定性去重**：不存在任何 `cuda_sync` 行满足 `runtime_record_id == a.record_id`
   （`runtime_record_id` 是 Canonical 冻结的 runtime 映射字段，指向被映射的 `cuda_api`
   `record_id`；`runtime_mapping_count` 同源）；
3. 存在**恰好一个** `kind=sync` structured marker：与该 API 同 Host 线程（或按已批准的 trusted
   cross-thread ownership fallback 允许的线程）、完整包围 `[a.start_ns, a.end_ns]`、NVTX payload
   可重新解析且与 Canonical 缓存 identity 精确一致；
4. 该 marker 的 invocation identity 与被唯一包含该区间的 `request`（以及声明的唯一 `phase`）范围
   一致；多解、冲突或跨线程但无 fallback 时不得猜测。

字段生成（全部来自可观察事实，不使用 oracle expected）：

| 字段 | 生成规则 |
| --- | --- |
| `sync_id` | 确定性派生 `cuda_api_sync:{source_table}:{source_rowid}`（与 `cuda_sync:…` 前缀不可能冲突） |
| `host_start_ns` / `host_end_ns` | runtime API 行的 `start_ns` / `end_ns`（合同要求「完整调用区间 fail closed」） |
| `request_id` / `repeat_id` / `sync_owner_phase` | 由 request/phase 包含关系与 marker identity 联合确定 |
| `callsite_id` / `sync_origin` / `sync_ordinal` | 唯一权威 `kind=sync` marker |
| `registry_rule_id` / `sync_kind` / `sync_universe_class` / `completion_scope` | `classify_cuda_api(a.api_name)`（例如 `cudaMemcpy*` → `SYNC-COPY-IMPLICIT-001` / `SYNCHRONOUS_COPY_OR_IMPLICIT_BLOCK` / `IN_UNIVERSE_UNSUPPORTED`） |
| `device_id` / `context_id` / `stream_id` / `event_id` / `event_sync_id` | `null`（runtime API 行不携带这些标识；该 `sync_kind` 不触发 `MISSING_*` 检查，且合同已决定该区间整体 fail closed）。若将来要求非空，必须单独 amendment 批准「由唯一 correlated activity 推导」，本文件不默认引入第二条推断路径 |

### 3.3 fail-closed 行为（冻结）

- 完全没有包围该 API 的 `kind=sync` marker → **不构造**记录，不伪造同步事实；Q0 侧由 oracle 集合
  比较暴露缺失（final-03 的 `Q0-SYNC-D2H-UNSUPPORTED-001` 属于「marker 存在但 physical row 缺失」
  的第 3.2 类，因此必须被构造）；
- marker 重复、仅跨线程而无 fallback、部分相交、identity 与 request/phase 冲突 → 仍构造确定性记录，
  但 `validity = INVALID` 且 primary reason 为 `INVOCATION_BOUNDARY_INVALID`（或既有更高优先级
  reason），`W(s) = []`、terminal 为 `INVALID/NONE`；
- 任何时候都不得用 case id、API 名白/黑名单、oracle expected 或 label 猜测来决定成员或字段。

### 3.4 共享 helper（冻结）

第 3.2 / 3.3 的资格判定、去重、marker 选择与字段生成必须实现为**单一共享 helper**，由
`exposedpath_v141/sync_semantics.py` 与 `exposedpath_v141/ab_inputs.py` 共同复用：

- `sync_semantics.py` 用它在 `build_semantic_inventory()` 中生成 semantic sync；
- `ab_inputs.py` 用**同一个 helper**独立重算 expected correspondence 集合，再与 S bundle 比对；
- 禁止在两处复制两套判定逻辑、常量表或正则；两份实现漂移即视为 amendment 违规；
- helper 必须只读取 Canonical 事实（records + registry + 已验证的 NVTX identity），不读取 S 输出、
  不读取 oracle。

## 4. `q0_real.py`（冻结）

- `non_sync_api_labels` **只**接受 registry role 为 `NON_SYNC` 的 `cuda_api` 行所对应的 marker 标签；
  `DEPENDENCY_EDGE` 与 `UNSUPPORTED` 的 marker 一律不得泄漏进去（这也修正了
  `Q0-KERNEL-MEMOP-001` 等含 `cudaMemcpy` 的 case 的同类泄漏风险）；
- `syncs[]` 只消费 role-preserving 的 semantic S records；由于 A/B loader 已强制 correspondence，
  `q0_real` 不再自行增加第二套过滤规则（单一权威，避免双重语义）；
- `build_real_q0_case()` 的「`callsite_id` 必须非空」检查保留，且继续 fail closed：它只对
  semantic sync 生效，`NON_SYNC` 行不再进入该路径；
- 禁止按 case id、API 名或 oracle expected 特判；禁止 analyzer suppression、reason suppression 或
  reason ranking 修改。

## 5. Version 决策（冻结）

```text
package / analyzer version: 0.2.1 -> 0.2.2
```

依据：本次改变 analyzer 的成员判定语义（S 记录集合与 `q0_real` 投影）。S/A/B manifest 内嵌
`analyzer_version`，因此 final-03（`0.2.1`）的 S/A-B/real evidence 不得与 `0.2.2` 产物混用。

保持不变：Measurement Contract 版本、sync registry 版本、Canonical Raw schema、S schema、
A/B schema、oracle `oracle_version`（`exposedpath-q0-oracle-0.2.0`）。

本 amendment 自身（docs-only commit）**不**修改 package `__version__`；版本提升属于 implementation
阶段动作。

## 6. final-04 派生边界（冻结）

裁决：

```text
final-04 = fresh 21-native collection（不复用 final-03 Raw）
final-01 / final-02 / final-03 = frozen incomplete forever（不 retry、不 resume、不重派生、不升级）
```

final-04 必须在新 run id 下完整重建证据链：

```text
fresh collection (21 native, 目标 GPU UUID 绑定)
  -> SQLite export
  -> Canonical Raw（21）
  -> controlled faults（Q0-MISSING-CORR-001 / Q0-DROPPED-001 / Q0-GRAPH-UNSUPPORTED-001）
  -> S（21，role-preserving）
  -> A/B（21）
  -> real evidence（21）
  -> synthetic（2）
  -> gate aggregation
```

final-03 的 Raw / SQLite / Canonical / `canonical_fault` / S / A-B / real evidence 一律不得作为
final-04 的输入被复用或拼接；只允许作为历史 Engineering 观测被引用。freeze 的 binary / build
receipt 规则按 `gate6_q0_build_contract_amendment_v0_1.md` 继续有效，但 binary 必须对应本
amendment 实施后的 implementation commit 与 `0.2.2`。

## 7. Scope（冻结；本轮不 implementation）

REQUIRED production：

- `exposedpath_v141/sync_semantics.py`（role 过滤 + API-backed 合成 + 共享 helper）
- `exposedpath_v141/ab_inputs.py`（用同一 helper 重算 correspondence 并 fail closed）
- `exposedpath_v141/q0_real.py`（`non_sync_api_labels` 按 registry role 限定）
- `exposedpath_v141/__init__.py`（`0.2.1 -> 0.2.2`）

REQUIRED tests：

- `tests/test_v141_sync_semantics.py`：`NON_SYNC` 不入 semantic sync；`UNSUPPORTED` 无 mapped row 时
  构造、有 mapped row 时不重复；marker 缺失 / 重复 / 跨线程 / 不包围 / identity 冲突的 fail-closed 行为
- `tests/test_v141_ab_inputs.py`：role-preserving correspondence 的缺、多、重复、字段冲突拒绝
- `tests/test_v141_q0_real.py`：`non_sync_api_labels` 只取 `NON_SYNC`；`DEPENDENCY_EDGE` /
  `UNSUPPORTED` 不泄漏；semantic sync 缺 `callsite_id` 仍 fail closed
- `tests/test_v141_q0_synthetic.py`：synthetic 路径与 `UNSUPPORTED` 期望保持一致

REQUIRED docs（implementation 阶段）：

- `docs/v1_4_1/s_layer_v0_2.md`（sync universe 成员判定说明）
- `docs/v1_4_1/gate6_windows_server_runbook.md`（final-04 provenance / 阶段边界）
- `docs/v1_4_1/q0_execution_package_v0_2.md`（S 成员规则与 version 记录）

## 8. Zero-diff 清单

以下内容在本 amendment 的 implementation 完成后仍必须保持 zero-diff：

```text
q0/oracle_cases_v0_2.json（oracle expected）
docs/v1_4_1/measurement_contract_v0_2.md 与 contracts/measurement_contract_v0_2.json
docs/v1_4_1/contracts/sync_semantics_registry_v0_2.json
docs/v1_4_1/contracts/canonical_raw_schema_v0_2.json
docs/v1_4_1/contracts/s_layer_schema_v0_2.json
docs/v1_4_1/contracts/ab_schema_v0_2.json
docs/v1_4_1/contracts/q0_execution_schema_v0_2.json（execution/run schema）
exposedpath_v141/q0_gate.py 与 Gate 6 PASS criterion
23-case composition / execution manifest 的 case 集合与顺序
q0/cuda/exposedpath_q0.cu（CUDA construction）
exposedpath_v141/q0_evaluator.py
exposedpath_v141/q0_faults.py
```

`q0/cuda/exposedpath_q0.cu` 无需修改：harness 已经用 `sync_range` + `marker_range` 包住
`cudaMemcpy`（`S_SYNC_COPY` / `COPY_D2H`），本 amendment 只修正 analyzer 侧成员判定。

## 9. Invariants

1. semantic sync 集合由 registry role 决定，不由 CUPTI activity 表是否存在对应 row 决定。
2. 每个 `UNSUPPORTED` 调用最多产生一条 semantic sync；mapped physical row 优先。
3. `NON_SYNC` 调用不得产生 semantic sync，也不得因此丢失 A/B 事实。
4. `DEPENDENCY_EDGE` 只作为设备依赖边存在。
5. `UNCLASSIFIED` 继续保持 `UNCLASSIFIED_CUDA_API` fail-closed。
6. correspondence 由共享 helper 单点定义，S 与 A/B loader 必须给出同一集合。
7. 任何缺失、重复或冲突证据都 fail closed，不得转换为零值或猜测 label。
8. final-03 及更早 run 的证据身份不被重写、不被升级。

## 10. STOP 条件

- 需要按 case id、API 名或 oracle expected 特判才能通过；
- 同一 `UNSUPPORTED` 调用同时产生 physical 与 API-backed 两条 semantic sync；
- `NON_SYNC` 调用仍进入 `syncs[]`，或 `DEPENDENCY_EDGE` / `UNSUPPORTED` 仍进入
  `non_sync_api_labels`；
- 为实现该规则而必须修改 §8 中任一 zero-diff 文件；
- S 与 `ab_inputs` 出现两套复制逻辑；
- final-04 复用 final-03 的 Raw/SQLite/Canonical/S/A-B/real evidence，或 final-01/02/03 被
  retry / resume / 升级。

任一触发即 STOP，交回 amendment review，不得就地放宽规则。

## 11. Migration / acceptance

1. 本 amendment commit（docs-only）不改变任何代码或产物。
2. implementation 阶段一次性完成 §7 的 production / tests / docs 变更，并把 package
   `__version__` 提升到 `0.2.2`。
3. offline 验证至少覆盖：role-preserving 成员判定、API-backed 构造与去重、marker/ownership
   fail-closed、correspondence 拒绝路径、`q0_real` 非同步标签限定，以及既有 Q0/S/A-B 定向回归。
4. final-04 按 §6 执行 fresh collection 与完整重派生；Gate 6 判据与 23-case composition 保持不变。
