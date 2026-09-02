# ExposedPath v2 Metric Specification

```text
Metric definition version: exposedpath-v2
Status: validated on real Nsight Systems trace
Validated schema: 3.24.8
Validated Nsight Systems: 2025.6.3.541
Validated GPU: NVIDIA GeForce RTX 4090
```

---

## 1. Research Objective & Measurement Boundaries

ExposedPath v2 answers two questions for each LLM inference request:

- **A-layer**: How is the end-to-end wall-clock latency mutually exclusively composed?
- **B-layer**: For any given verifiable synchronisation point, why did it return at that moment?

Measurement boundaries are defined by NVTX `full_request` ranges issued by `bench_eager.py`. Each `full_request` contains a `prefill` and a `decode` sub-range. Warmup iterations carry no NVTX and are excluded.

## 2. Nsight Systems SQLite Input

### Required tables

| Table | Purpose |
|---|---|
| `NVTX_EVENTS` | Request / phase / token boundaries |
| `CUPTI_ACTIVITY_KIND_RUNTIME` | Host-side CUDA API calls |
| `CUPTI_ACTIVITY_KIND_KERNEL` | GPU kernel launches |
| `CUPTI_ACTIVITY_KIND_MEMCPY` | GPU memory copies |
| `StringIds` | Name resolution |
| `META_DATA_EXPORT` | Schema/product version |

### Required optional tables

| Table | Used for |
|---|---|
| `CUPTI_ACTIVITY_KIND_SYNCHRONIZATION` | Real context/stream for sync semantics |
| `CUPTI_ACTIVITY_KIND_MEMSET` | GPU memset operations |
| `ENUM_CUDA_MEMCPY_OPER` | Memcpy type names |

Table and column names are auto-detected via `PRAGMA table_info` and case-insensitive candidate matching.

## 3. NVTX Window Attribution

### Window hierarchy

```
full_request
├── prefill
└── decode
    ├── decode_step_1
    ├── decode_step_2
    └── ...
```

### Attribution algorithm

1. NVTX ranges grouped by `globalTid`.
2. Each group sorted by `(start_ns, -end_ns)`.
3. Sweep-line with depth stack: each API assigned to the **innermost** containing window.
4. `request_id` / `repeat_id` propagated from the `full_request` ancestor.
5. Internal `window_id` is NOT used as `request_id`; a separate `wid_to_rid` mapping normalizes all IDs.

## 4. CUDA API → GPU Activity Correlation

1. Build `api_by_correlation[correlationId] → CudaApi` (first submit wins).
2. Each GPU activity inherits from its correlated submit API:
   - `request_id`, `repeat_id`, `phase`, `token_idx`
   - `submit_api_id`, `submit_end_ns`
3. Missing correlation → marked in `correlation_coverage`.

## 5. Raw Metrics

Computed per `repeat × phase` window `[ws, we)`.

### Activity overlap condition

```
end_ns > ws AND start_ns < we
```

Uses `IntervalIndex` (encapsulated prefix-max-end index over start-sorted objects)
for O(log N + k) queries. The index is a single object — `objects`, `starts`,
and `prefix_max_ends` share positions, preventing array mismatches.

#### IntervalIndex correctness

- `IntervalIndex.build()` sorts by `(start_ns, end_ns, activity_id)`.
- `prefix_max_ends[i] = max(end_ns of objects[0..i])`.
- If `prefix_max_ends[i] ≤ window_start`, ALL `objects[0..i]` have `end_ns ≤ window_start` → none overlap → safe to skip.
- Upper bound: `bisect_left(starts, window_end)`.
- Final filter: `end > ws AND start < we`.
- Complexity: O(N log N) build, O(log N + k) query, worst-case O(N).

#### Raw window overlap vs B wait-set

- **Raw**: `end > window_start AND start < window_end` (time overlap).
- **B wait set**: `submit_end ≤ sync_start AND end > sync_start` (submission state).
- A B terminal may not appear in the same phase's Raw count — if so, `cross_phase_wait_flag = true`.

#### RAW_B_INTERVAL_INCONSISTENCY

If a B terminal overlaps the sync phase window but is NOT found in that phase's
Raw activity set, a warning is raised. Expected: 0 for validated traces.

### Metrics

| Category | Metrics |
|---|---|
| CUDA API | count, union_duration, launch_count, sync_count, distinct_threads, top-10 names |
| Kernel | count, union_duration, distinct_names, distinct_streams, top-10 names |
| Memcpy | count, bytes (nullable), union_duration |
| Memset | count, bytes (nullable), union_duration |
| GPU aggregate | activity_union, gpu_active_ratio, multistream_concurrent, multistream_ratio |
| GPU states | kernel_only, memop_only, kernel_memop_mixed (mutually exclusive) |

`bytes` is nullable — absent from trace → `null`, not `0`.

## 6. S-Layer: Sync Semantic Preprocessing

### Sync type classification

- Stream sync: `cudaStreamSynchronize` / `cuStreamSynchronize`
- Device sync: `cudaDeviceSynchronize` / `cuCtxSynchronize`
- Event sync: `cudaEventSynchronize` / `cuEventSynchronize`

Context/stream taken from `CUPTI_ACTIVITY_KIND_SYNCHRONIZATION` via `correlationId` join. API name is fallback only.

### Wait-set definition

**Stream sync**:
```
activity.context_id == sync.context_id
activity.stream_id == sync.stream_id
activity.submit_end_ns <= sync.start_ns
activity.end_ns > sync.start_ns
```

**Device sync**:
```
activity.context_id == sync.context_id
activity.submit_end_ns <= sync.start_ns
activity.end_ns > sync.start_ns
```

**Event sync**: `wait_set_valid = false`, `invalid_reason = MISSING_EVENT_MAP` (CUDA 12.1 limitation).

### Fail-closed rules

| Condition | Result |
|---|---|
| No sync activity record | `NO_SYNC_RECORD` |
| Stream sync without stream_id | `MISSING_STREAM_ID` |
| Device sync without context_id | `MISSING_CONTEXT_ID` |
| No pending activities | `NO_PENDING_ACTIVITY` |
| Multiple terminal candidates within tolerance | `MULTI_TERMINAL` |
| Negative tail exceeds tolerance | `TRACE_ORDERING_ERROR` |
| External activities in wait set | `EXTERNAL_ACTIVITY` |

Stream guessing (iterating all streams) is **prohibited**.

## 7. A-Layer: Mutually Exclusive Wall-Clock Accounting

### Categories

| Category | Definition |
|---|---|
| `A_host_path` | Window time not in sync, not in CUDA API, not unattributed |
| `A_cuda_api` | Non-sync CUDA API call intervals (union) |
| `A_device_wait` | sync ∩ union(wait_set GPU activity intervals), for valid syncs |
| `A_sync_residual` | sync − A_device_wait |
| `A_unattributed` | Boundary/correlation issues (should be 0 for well-formed traces) |

### Computation method

Explicit interval arithmetic:

```
all_sync = merge(sync_intervals)
device_wait_parts = merge(all [sync_interval ∩ wait_set_activity] for valid syncs)
A_device_wait = intersect(all_sync, device_wait_parts)
A_sync_residual = subtract(all_sync, device_wait_parts)
A_cuda_api = merge(non_sync_api_intervals)
all_excluded = merge(all_sync ∪ A_cuda_api)
A_host_path = subtract([(ws, we)], all_excluded)
```

### Conservation

```
T_window = A_host_path + A_cuda_api + A_device_wait + A_sync_residual + A_unattributed + ε
```

Quality gate: `|ε| / T_window ≤ 0.01%`.

## 8. Overlap Metrics

### O_api_gpu

```
numerator   = intersection(A_cuda_api_intervals, GPU_activity_union)
denominator = duration(A_cuda_api_intervals)
```

Measures: during CUDA API execution, how much GPU time is spent on previously submitted work.

### O_hostpath_gpu

```
numerator   = intersection(A_host_path_intervals, GPU_activity_union)
denominator = duration(A_host_path_intervals)
```

Measures: during non-API host path, how much GPU time is concurrently active.

These two metrics use different numerators and different denominators; they must not be identical or degenerate to `gpu_active_ratio`.

## 9. B-Layer: Per-Sync Local Diagnostics

### Canonical sync

Each physical sync appears **exactly once** in `b_sync_detail.csv`. Deduplication uses `physical_sync_uid`.

### physical_sync_uid

```
corr={correlation_id}:start={start_ns}:end={end_ns}
```

Fallback (no correlation): includes request_id, repeat_id, sync_type, stream_id, context_id.

### Terminal

```
terminal = max(wait_set, key=lambda x: x.end_ns)
```

Only from the properly constructed wait set. Multiple candidates within `TERMINAL_TOLERANCE_NS = 1000ns` → `MULTI_TERMINAL`.

### B_self

```
terminal.end_ns - terminal.start_ns
```

Full execution time of the terminal activity. May be larger than `device_overlap_with_sync`.

### B_predecessor

Union of earlier GPU activities on the same (context, stream) between `submit_end_ns` and `terminal.start_ns`.

### B_stream_gap

```
terminal.start_ns - terminal.submit_end_ns - B_predecessor_ns
```

Minimum 0.

### sync_return_tail

```
raw_tail = sync.end_ns - terminal.end_ns

if raw_tail >= 0: tail = raw_tail
elif raw_tail >= -TIMESTAMP_TOLERANCE_NS (20µs): tail = 0, tolerance_applied = true
else: B_valid = false, TRACE_ORDERING_ERROR
```

### Why B cannot be summed across syncs

B metrics are per-sync local diagnostics. A_sync_residual already accounts for the total sync time not spent in device_wait. Summing B_predecessor, B_stream_gap, etc. across syncs has no meaning for phase latency.

### Ownership

```
terminal_ownership_valid =
    terminal.request_id == sync.request_id
    AND terminal.repeat_id == sync.repeat_id
```

```
cross_phase_wait_flag =
    same request_id AND same repeat_id
    AND normalized(terminal.phase) != normalized(sync.phase)
```

```
wait_set_unassigned_count =
    count(activity in wait_set where activity.request_id is None)

wait_set_external_count =
    count(activity in wait_set where activity.request_id != sync.request_id)
```

## 10. Aggregation Rules

### Repeat → Workload

- **A-layer**: mean across repeats, sample SD (n ≥ 2; null for n = 1).
- **Overlap**: mean across repeats.
- **B coverage**: count-weighted: `sum(B_valid_count) / sum(sync_supported_count)`.
- **Raw**: mean and sample SD for all numeric fields.

### Workload → Matrix

Same rules, stratified by `metric_definition_version`. Only workloads with matching version are aggregated.

### Statistical formulas

- Sample SD: `√(Σ(x - μ)² / (n - 1))`, n ≥ 2; null otherwise.
- Median, IQR, CV (null when mean ≈ 0).

## 11. Output Files

### Per workload: `accounting/`

| File | Contents |
|---|---|
| `accounting_result.json` | Full result: metadata, trace_quality, raw_summary, A_summary, overlap_summary, B_summary, repeat_results, legacy_compatibility |
| `accounting_summary.csv` | One row per `repeat × phase` with Raw, A, overlap, thread, B counts |
| `b_sync_detail.csv` | One row per physical sync with full B diagnostics |

### Per matrix: root directory

| File | Contents |
|---|---|
| `matrix_summary.json` | Per-workload aggregates: mean, sample SD, median, IQR, CV for all metrics. Primary analysis artifact. |
| `matrix_summary.csv` | Same data in CSV format for Excel/viewing. |

`matrix_summary.json` is the primary artifact for cross-workload comparison, plotting, and paper tables. Individual workload files remain essential for repeat-level auditing.

## 12. Removed Legacy Fields

| Removed | Replacement |
|---|---|
| `A_device_compute` | `A_device_wait` |
| `A_memory_transfer` | merged into `A_device_wait` |
| `A_submit` | `A_cuda_api` |
| `A_host_runtime` | `A_host_path` |
| `b_exposed_ms`, `b_self_block_ms`, `b_kernel_block_ms`, `b_memory_block_ms`, `b_device_gap_ms`, `b_top_motif` | Per-sync B diagnostics |
| `exposed_total_ms`, `hidden_total_ms` | Not applicable |

## 13. Known Limitations

- **CUDA 12.1 event sync**: No `eventSyncId` → event sync always `MISSING_EVENT_MAP`.
- **Dropped records**: No explicit counter in SQLite → `dropped_records_status = "unknown"`.
- **Nsight versions**: Schema adapter tested on 2025.6.3.541; other versions use candidate matching.
- **Timestamp tolerance**: 20 µs threshold for negative tails; real clock skew may vary.

## 14. Validated Reference Values

Workload: `w05_p256_b1_o16`, GPU: NVIDIA GeForce RTX 4090, 5 repeats.

### A-layer (mean across repeats, ms)

| Category | Prefill | Decode | Full Request |
|---|---|---|---|
| A_host_path | 36.183 | 482.823 | 519.070 |
| A_cuda_api | 88.199 | 1169.655 | 1257.854 |
| A_device_wait | 27.468 | 262.397 | 289.865 |
| A_sync_residual | 33.488 | 269.958 | 303.446 |
| A_unattributed | 0 | 0 | 0 |

Tolerance for regression: ±0.1 ms per category mean.

### B-layer

- 85 physical syncs, 85 unique physical_sync_uid, 0 duplicates.
- 5 stream syncs, 80 device syncs, 0 event syncs.
- Per repeat: 2 prefill + 15 decode = 17 syncs.
- Workload total: 10 prefill + 75 decode = 85 syncs.
- Terminal ownership valid: 85/85.
- Wait-set external: 0, unassigned: 0.

## 15. Test Invariants

1. A conservation error ≤ 0.01%.
2. A_sync_residual > 0 in at least one phase.
3. b_sync_detail rows = unique physical_sync_uid count.
4. No duplicate physical_sync_uid.
5. terminal_ownership_valid = 100% for correlated traces.
6. Raw activity count correctly includes cross-window activities.
7. Prefix-max-end index handles non-monotonic end times.

## 16. Metric Definition Changelog

| Version | Date | Changes |
|---|---|---|
| exposedpath-v2 | 2026-07 | Complete rewrite: Raw→S→A→B architecture. A_cuda_api/A_device_wait/A_sync_residual/A_host_path replace legacy categories. B per-sync diagnostics replace summed provenance. Interval-based A computation. Synchronization activity table integration. |
| exposedpath-v2 (interval fix) | 2026-07 | Fixed `filter_objects_by_window` lower-bound bug: replaced unsorted `end_array` bisect with prefix-max-end index. Encapsulated into `IntervalIndex` class. Added `--debug` RAW_B check. |
| exposedpath-v2 (matrix v2) | 2026-07 | Rewrote `summarize_matrix.py` for v2-only aggregation. Added throughput (tokens/sec), B distribution (percentiles), quality gates (CV thresholds, hard gates), version/git_commit validation, `--accounting-dir-name`. Removed all legacy fields from matrix output. JSON boolean typing enforced. API coverage denominator fixed. |
