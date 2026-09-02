#!/usr/bin/env python3
"""
Tests for exposed accounting v2 (exposedpath-v2).

Creates temporary in-memory SQLite databases mimicking nsys export format
and validates the full pipeline: schema → load → NVTX → correlation → S → A → B.
"""

from __future__ import annotations

import json
import math
import os
import sqlite3
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis import accounting_utils as U
from analysis.exposed_accounting import (
    build_nvtx_windows,
    assign_api_to_windows,
    correlate_gpu_to_api,
    build_repeat_phases,
    build_sync_records,
    compute_a_layer,
    compute_b_for_all_syncs,
    compute_raw_stats,
    compute_overlap_metrics,
    compute_exposed_accounting_v2,
    find_dominant_thread,
    load_events_from_sqlite,
)


# ===================================================================
# Helpers
# ===================================================================

def make_test_sqlite() -> str:
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("CREATE TABLE StringIds (id INTEGER PRIMARY KEY, value TEXT)")
    strings = {
        1: "full_request", 2: "prefill", 3: "decode",
        4: "decode_step_1", 5: "decode_step_2", 6: "decode_step_3",
        10: "cudaLaunchKernel", 11: "cudaStreamSynchronize",
        12: "cudaDeviceSynchronize", 13: "cudaMemcpyAsync",
        14: "cudaEventSynchronize",
    }
    for sid, val in strings.items():
        cur.execute("INSERT INTO StringIds VALUES (?, ?)", (sid, val))
    cur.execute(
        "CREATE TABLE NVTX_EVENTS (start INTEGER, \"end\" INTEGER, text INTEGER, globalTid INTEGER)"
    )
    cur.execute(
        "CREATE TABLE CUPTI_ACTIVITY_KIND_RUNTIME "
        "(start INTEGER, \"end\" INTEGER, correlationId INTEGER, nameId INTEGER, globalTid INTEGER)"
    )
    cur.execute(
        "CREATE TABLE CUPTI_ACTIVITY_KIND_KERNEL "
        "(start INTEGER, \"end\" INTEGER, streamId INTEGER, correlationId INTEGER, "
        "demangledName TEXT, deviceId INTEGER, contextId INTEGER)"
    )
    cur.execute(
        "CREATE TABLE CUPTI_ACTIVITY_KIND_MEMCPY "
        "(start INTEGER, \"end\" INTEGER, streamId INTEGER, correlationId INTEGER, "
        "copyKind INTEGER, deviceId INTEGER, contextId INTEGER)"
    )
    cur.execute("CREATE TABLE ENUM_CUDA_MEMCPY_OPER (id INTEGER PRIMARY KEY, name TEXT)")
    cur.execute("INSERT INTO ENUM_CUDA_MEMCPY_OPER VALUES (1, 'DeviceToDevice')")
    # Synchronization activity table
    cur.execute(
        "CREATE TABLE CUPTI_ACTIVITY_KIND_SYNCHRONIZATION "
        "(start INTEGER, \"end\" INTEGER, correlationId INTEGER, syncType INTEGER, "
        "deviceId INTEGER, contextId INTEGER, streamId INTEGER, "
        "eventId INTEGER, eventSyncId INTEGER)"
    )
    # META_DATA_EXPORT
    cur.execute(
        "CREATE TABLE META_DATA_EXPORT (name TEXT, value TEXT)"
    )
    cur.execute("INSERT INTO META_DATA_EXPORT VALUES ('EXPORT_SCHEMA_VERSION', '3.24.8')")
    cur.execute("INSERT INTO META_DATA_EXPORT VALUES ('EXPORT_PRODUCT_VERSION', '2025.6.3.541')")
    conn.commit()
    conn.close()
    return path


def populate_test_trace(db_path, prompt_ns=100_000, kernel_dur_ns=500_000,
                        output_tokens=2, sync_delay_ns=50_000):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    tid = 12345

    pf_end = prompt_ns + kernel_dur_ns + sync_delay_ns // 2
    dc_end = pf_end + output_tokens * (kernel_dur_ns + sync_delay_ns) + prompt_ns
    fr_end = dc_end

    # NVTX
    nvtx_data = [
        (0, fr_end, 1, tid), (0, pf_end, 2, tid), (pf_end, dc_end, 3, tid),
    ]
    for i in range(output_tokens):
        ss = pf_end + i * (kernel_dur_ns + sync_delay_ns)
        se = ss + kernel_dur_ns + sync_delay_ns
        nvtx_data.append((ss, se, 4 + i, tid))
    for s, e, text_id, t in nvtx_data:
        cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)", (s, e, text_id, t))

    # CUDA API
    cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)",
                (0, prompt_ns, 100, 10, tid))
    sync_start = prompt_ns + kernel_dur_ns - sync_delay_ns // 2
    sync_end = sync_start + sync_delay_ns
    cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)",
                (sync_start, sync_end, 101, 11, tid))
    for i in range(output_tokens):
        ss = pf_end + i * (kernel_dur_ns + sync_delay_ns)
        le = ss + prompt_ns // 2
        cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)",
                    (ss, le, 200 + i, 10, tid))
        ke = ss + prompt_ns // 2 + kernel_dur_ns
        s_start = ke - sync_delay_ns // 2
        s_end = s_start + sync_delay_ns
        cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)",
                    (s_start, s_end, 201 + i, 11, tid))

    # GPU kernels
    cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES (?, ?, ?, ?, ?, ?, ?)",
                (prompt_ns, prompt_ns + kernel_dur_ns, 7, 100, "volta_sgemm_32x32", 0, 1))
    for i in range(output_tokens):
        ss = pf_end + i * (kernel_dur_ns + sync_delay_ns)
        ks = ss + prompt_ns // 2
        ke = ks + kernel_dur_ns
        cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (ks, ke, 7, 200 + i, f"volta_sgemm_decode_{i}", 0, 1))

    # Sync activities (match runtime correlation IDs)
    cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (sync_start, sync_end, 101, 0, 0, 1, 7, -1, -1))
    for i in range(output_tokens):
        ss = pf_end + i * (kernel_dur_ns + sync_delay_ns)
        ke = ss + prompt_ns // 2 + kernel_dur_ns
        s_start = ke - sync_delay_ns // 2
        s_end = s_start + sync_delay_ns
        cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (s_start, s_end, 201 + i, 0, 0, 1, 7, -1, -1))

    conn.commit()
    conn.close()


# ===================================================================
# Tests
# ===================================================================

class TestIntervalUtils:
    def test_merge_empty(self):
        assert U.merge_intervals([]) == []

    def test_merge_single(self):
        assert U.merge_intervals([(0, 100)]) == [(0, 100)]

    def test_merge_overlapping(self):
        assert U.merge_intervals([(0, 100), (50, 150), (200, 300)]) == [(0, 150), (200, 300)]

    def test_merge_subsumed(self):
        assert U.merge_intervals([(0, 100), (20, 50)]) == [(0, 100)]

    def test_union_duration(self):
        assert U.union_duration([(0, 100), (50, 150)]) == 150

    def test_intersect_simple(self):
        a = [(0, 100), (200, 300)]
        b = [(50, 150), (180, 250)]
        assert U.intersect_intervals(a, b) == [(50, 100), (200, 250)]

    def test_subtract_simple(self):
        assert U.subtract_intervals([(0, 100)], [(20, 40)]) == [(0, 20), (40, 100)]

    def test_merge_large(self):
        import random
        random.seed(42)
        intervals = [(random.randint(0, 10_000_000),) for _ in range(100_000)]
        intervals = [(s, s + random.randint(1, 1000)) for (s,) in intervals]
        result = U.merge_intervals(intervals)
        for i in range(len(result) - 1):
            assert result[i][1] < result[i + 1][0]

    def test_sample_std(self):
        assert U.sample_std([1.0]) is None
        assert U.sample_std([1.0, 1.0, 1.0]) == 0.0
        assert U.sample_std([1.0, 3.0]) == math.sqrt(2.0)

    def test_parse_workload_id(self):
        info = U.parse_workload_id("w05_p256_b1_o16")
        assert info["prompt_len"] == 256
        assert info["batch_size"] == 1
        assert info["output_len"] == 16
        assert "w05_p256_b1_o16" in info["workload_id"]


class TestIsSyncApi:
    def test_stream_sync(self):
        assert U.is_sync_api("cudaStreamSynchronize")

    def test_device_sync(self):
        assert U.is_sync_api("cudaDeviceSynchronize")

    def test_non_sync(self):
        assert not U.is_sync_api("cudaLaunchKernel")

    def test_classify_sync_type(self):
        assert U.classify_sync_type("cudaStreamSynchronize") == "stream"
        assert U.classify_sync_type("cudaDeviceSynchronize") == "device"
        assert U.classify_sync_type("cudaEventSynchronize") == "event"


class TestNvtxWindows:
    def test_build_windows_basic(self):
        nvtx_raw = [
            {"start_ns": 0, "end_ns": 1000, "name": "full_request", "global_tid": 1},
            {"start_ns": 0, "end_ns": 400, "name": "prefill", "global_tid": 1},
            {"start_ns": 400, "end_ns": 1000, "name": "decode", "global_tid": 1},
        ]
        windows = build_nvtx_windows(nvtx_raw)
        assert len(windows) == 3
        fr = [w for w in windows if w.phase == "full_request"][0]
        assert fr.depth == 0

    def test_api_assignment(self):
        nvtx_raw = [
            {"start_ns": 0, "end_ns": 1000, "name": "full_request", "global_tid": 1},
            {"start_ns": 0, "end_ns": 400, "name": "prefill", "global_tid": 1},
            {"start_ns": 400, "end_ns": 1000, "name": "decode", "global_tid": 1},
            {"start_ns": 400, "end_ns": 700, "name": "decode_step_1", "global_tid": 1},
        ]
        windows = build_nvtx_windows(nvtx_raw)
        apis = [
            U.CudaApi(api_id=0, name="cudaLaunchKernel", start_ns=50, end_ns=100, global_tid=1),
            U.CudaApi(api_id=2, name="cudaLaunchKernel", start_ns=450, end_ns=500, global_tid=1),
        ]
        assign_api_to_windows(apis, windows)
        assert apis[0].phase == "prefill"
        assert apis[1].phase == "decode"  # normalized from decode_step_1 by v3


class TestCorrelation:
    def test_correlation_basic(self):
        apis = [U.CudaApi(api_id=0, name="launch", start_ns=0, end_ns=100, correlation_id=100)]
        gpus = [U.GpuActivity(activity_id=0, activity_type="kernel", name="k1",
                               start_ns=200, end_ns=500, correlation_id=100)]
        stats = correlate_gpu_to_api(gpus, apis)
        assert stats["correlation_coverage"] == 1.0
        assert gpus[0].submit_end_ns == 100

    def test_one_api_multiple_gpu(self):
        apis = [U.CudaApi(api_id=0, name="launch", start_ns=0, end_ns=100, correlation_id=100)]
        gpus = [
            U.GpuActivity(activity_id=0, activity_type="kernel", name="k1", start_ns=200, end_ns=500, correlation_id=100),
            U.GpuActivity(activity_id=1, activity_type="kernel", name="k2", start_ns=600, end_ns=900, correlation_id=100),
        ]
        stats = correlate_gpu_to_api(gpus, apis)
        assert stats["correlation_coverage"] == 1.0


class TestFullPipeline:
    def setup_method(self):
        self.db_path = make_test_sqlite()

    def teardown_method(self):
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def test_load_and_schema(self):
        populate_test_trace(self.db_path, output_tokens=2)
        nvtx, apis, gpus, syncs, schema = load_events_from_sqlite(self.db_path)
        assert schema["schema_version"] == "3.24.8"
        assert schema["nsys_product_version"] == "2025.6.3.541"
        assert len(syncs) >= 3

    def test_sync_activity_correlation(self):
        """Sync activities should be correlated to runtime APIs via correlationId."""
        populate_test_trace(self.db_path, output_tokens=2)
        nvtx, apis, gpus, sync_acts, schema = load_events_from_sqlite(self.db_path)
        windows = build_nvtx_windows(nvtx)
        assign_api_to_windows(apis, windows)
        correlate_gpu_to_api(gpus, apis)
        sync_records = build_sync_records(apis, gpus, sync_acts, schema)
        # Stream syncs should have context_id=1, stream_id=7
        for sr in sync_records:
            if sr.sync_type == "stream":
                assert sr.context_id == 1, f"Expected context_id=1, got {sr.context_id}"
                assert sr.stream_id == 7, f"Expected stream_id=7, got {sr.stream_id}"

    def test_a_residual_nonzero(self):
        """A_sync_residual must be > 0 when sync extends past GPU activity."""
        # Construct: kernel [0,10], sync [8,12] → A_device_wait=2, A_sync_residual=2
        db_path = make_test_sqlite()
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        tid = 1
        # NVTX
        cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)", (0, 20000, 1, tid))
        cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)", (0, 20000, 2, tid))
        cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)", (0, 20000, 3, tid))
        # Launch API + kernel
        cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)",
                    (0, 1000, 100, 10, tid))
        cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (2000, 10000, 7, 100, "kernel_10ms", 0, 1))
        # Sync API
        cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)",
                    (8000, 12000, 101, 11, tid))
        # Sync activity
        cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (8000, 12000, 101, 0, 0, 1, 7, -1, -1))
        conn.commit()
        conn.close()

        nvtx, apis, gpus, syncs, schema = load_events_from_sqlite(db_path)
        result = compute_exposed_accounting_v2(
            nvtx, apis, gpus, syncs, schema, workload_id="test_residual",
        )
        a = result["A_summary"].get("prefill", {})
        dw = a.get("A_device_wait_ms_mean", 0) or 0
        sr_val = a.get("A_sync_residual_ms_mean", 0) or 0
        assert dw > 0, f"Expected A_device_wait > 0, got {dw}"
        assert sr_val > 0, f"Expected A_sync_residual > 0, got {sr_val}"
        os.unlink(db_path)

    def test_b_dedup_one_row_per_sync(self):
        """Each physical sync must appear exactly once in b_sync_details."""
        populate_test_trace(self.db_path, output_tokens=2)
        nvtx, apis, gpus, syncs, schema = load_events_from_sqlite(self.db_path)
        result = compute_exposed_accounting_v2(
            nvtx, apis, gpus, syncs, schema, workload_id="test_dedup",
        )
        bd_list = result["b_sync_details"]
        sync_ids = [bd.sync_id for bd in bd_list]
        from collections import Counter
        dupes = {sid: cnt for sid, cnt in Counter(sync_ids).items() if cnt > 1}
        assert len(dupes) == 0, f"Duplicate sync_ids found: {dupes}"
        assert len(bd_list) == len(set(sync_ids))

    def test_b_self_vs_overlap_different(self):
        """B_self (full kernel time) can differ from device_overlap_with_sync."""
        populate_test_trace(self.db_path, output_tokens=2)
        nvtx, apis, gpus, syncs, schema = load_events_from_sqlite(self.db_path)
        result = compute_exposed_accounting_v2(
            nvtx, apis, gpus, syncs, schema, workload_id="test_self",
        )
        for bd in result["b_sync_details"]:
            if bd.B_valid and bd.B_self_ms is not None:
                # B_self should be >= device_overlap (kernel may start before sync)
                assert bd.B_self_ms >= (bd.device_overlap_with_sync_ms or 0) - 0.001

    def test_timestamp_tolerance(self):
        """Negative tail within tolerance → tail=0; large negative → TRACE_ORDERING_ERROR."""
        db_path = make_test_sqlite()
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        tid = 1
        cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)", (0, 100_000, 1, tid))
        cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)", (0, 100_000, 2, tid))
        cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)", (0, 100_000, 3, tid))
        cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)",
                    (0, 1000, 100, 10, tid))
        cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (2000, 60000, 7, 100, "k", 0, 1))
        # Sync ends slightly before kernel ends (negative tail within tolerance)
        cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)",
                    (30000, 59990, 101, 11, tid))  # tail = -10µs → within 20µs tolerance
        cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (30000, 59990, 101, 0, 0, 1, 7, -1, -1))
        conn.commit()
        conn.close()

        nvtx, apis, gpus, syncs, schema = load_events_from_sqlite(db_path)
        result = compute_exposed_accounting_v2(
            nvtx, apis, gpus, syncs, schema, workload_id="test_tail",
        )
        for bd in result["b_sync_details"]:
            if bd.sync_id == 0:
                assert bd.timestamp_tolerance_applied, "Should apply tolerance for -10µs tail"
                assert bd.sync_return_tail_ms == 0.0
        os.unlink(db_path)

    def test_a_layer_conservation(self):
        populate_test_trace(self.db_path, output_tokens=2)
        nvtx, apis, gpus, syncs, schema = load_events_from_sqlite(self.db_path)
        result = compute_exposed_accounting_v2(
            nvtx, apis, gpus, syncs, schema, workload_id="test_cons",
        )
        for row in result["repeat_results"]:
            window_ms = row.get("window_duration_ms", 0) or 0
            a_sum = sum(row.get(f"{cat}_ms", 0) or 0 for cat in [
                "A_host_path", "A_cuda_api", "A_device_wait",
                "A_sync_residual", "A_unattributed",
            ])
            eps = abs(window_ms - a_sum)
            assert eps < 0.05, f"Phase {row['phase']}: eps={eps:.6f}ms (tolerance=0.05ms)"

    def test_legacy_fields_removed(self):
        populate_test_trace(self.db_path, output_tokens=2)
        nvtx, apis, gpus, syncs, schema = load_events_from_sqlite(self.db_path)
        result = compute_exposed_accounting_v2(
            nvtx, apis, gpus, syncs, schema, workload_id="test_legacy",
        )
        for row in result["repeat_results"]:
            assert "A_device_compute" not in row
            assert "b_exposed_ms" not in row

    def test_performance_no_o_n2(self):
        """10k events should complete quickly."""
        db_path = make_test_sqlite()
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        tid = 1
        cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)", (0, 100_000_000, 1, tid))
        cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)", (0, 100_000_000, 2, tid))
        cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)", (0, 100_000_000, 3, tid))
        for i in range(5000):
            s = i * 2000
            is_sync = (i % 10 == 0)
            cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)",
                        (s, s + 1000, i, 11 if is_sync else 10, tid))
            if is_sync:
                cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (s, s + 1000, i, 0, 0, 1, 7, -1, -1))
        for i in range(5000):
            s = i * 2000 + 1000
            cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (s, s + 500, 7, i, f"k{i}", 0, 1))
        conn.commit()
        conn.close()

        import time
        t0 = time.perf_counter()
        nvtx, apis, gpus, syncs, schema = load_events_from_sqlite(db_path)
        result = compute_exposed_accounting_v2(
            nvtx, apis, gpus, syncs, schema, workload_id="perf",
        )
        elapsed = time.perf_counter() - t0
        os.unlink(db_path)
        assert elapsed < 30.0, f"Performance: {elapsed:.1f}s"
        assert "error" not in result

    def test_no_stream_guessing(self):
        """Stream sync must use real stream_id from sync activity, not guess."""
        db_path = make_test_sqlite()
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        tid = 1
        cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)", (0, 200_000, 1, tid))
        cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)", (0, 200_000, 2, tid))
        cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)", (0, 200_000, 3, tid))
        # Launches on stream 0 (many activities) vs stream 7 (one activity)
        cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)",
                    (0, 1000, 100, 10, tid))
        cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (2000, 100_000, 0, 100, "wrong_stream_kernel", 0, 1))  # stream 0, more work
        cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)",
                    (0, 1000, 200, 10, tid))
        cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (2000, 50_000, 7, 200, "right_stream_kernel", 0, 1))  # stream 7
        # Stream sync with correlation pointing to sync activity on stream 7
        cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)",
                    (40000, 60000, 101, 11, tid))
        cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (40000, 60000, 101, 0, 0, 1, 7, -1, -1))
        conn.commit()
        conn.close()

        nvtx, apis, gpus, syncs, schema = load_events_from_sqlite(db_path)
        windows = build_nvtx_windows(nvtx)
        assign_api_to_windows(apis, windows)
        correlate_gpu_to_api(gpus, apis)
        sr_list = build_sync_records(apis, gpus, syncs, schema)
        stream_syncs = [sr for sr in sr_list if sr.sync_type == "stream"]
        assert len(stream_syncs) > 0
        for sr in stream_syncs:
            assert sr.stream_id == 7, f"Must use real stream_id=7, got {sr.stream_id}"
            if sr.wait_set_valid:
                # Wait set should only contain activities on stream 7
                gpu_map = {g.activity_id: g for g in gpus}
                for aid in sr.wait_activity_ids:
                    g = gpu_map.get(aid)
                    if g:
                        assert g.stream_id == 7, f"Activity on wrong stream: {g.stream_id}"
        os.unlink(db_path)

    def test_device_sync_context_scope(self):
        """Device sync must only include activities from same context."""
        db_path = make_test_sqlite()
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        tid = 1
        cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)", (0, 200_000, 1, tid))
        cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)", (0, 200_000, 2, tid))
        cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)", (0, 200_000, 3, tid))
        # Context 1 kernel
        cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)",
                    (0, 1000, 100, 10, tid))
        cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (2000, 100_000, 7, 100, "ctx1_kernel", 0, 1))
        # Context 2 kernel (should NOT be in wait set)
        cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)",
                    (0, 1000, 200, 10, tid))
        cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (2000, 100_000, 7, 200, "ctx2_kernel", 0, 2))
        # Device sync on context 1
        cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)",
                    (50000, 70000, 101, 12, tid))
        cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (50000, 70000, 101, 0, 0, 1, -1, -1, -1))
        conn.commit()
        conn.close()

        nvtx, apis, gpus, syncs, schema = load_events_from_sqlite(db_path)
        windows = build_nvtx_windows(nvtx)
        assign_api_to_windows(apis, windows)
        correlate_gpu_to_api(gpus, apis)
        sr_list = build_sync_records(apis, gpus, syncs, schema)
        device_syncs = [sr for sr in sr_list if sr.sync_type == "device"]
        assert len(device_syncs) > 0
        gpu_map = {g.activity_id: g for g in gpus}
        for sr in device_syncs:
            if sr.wait_set_valid:
                for aid in sr.wait_activity_ids:
                    g = gpu_map.get(aid)
                    if g:
                        assert g.context_id == 1, f"Wrong context {g.context_id} in wait set"
        os.unlink(db_path)


class TestNewRegressions:
    """New regression tests for B dedup, physical_sync_uid, GPU name, raw_summary, etc."""

    def setup_method(self):
        self.db_path = make_test_sqlite()

    def teardown_method(self):
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def test_repeat_local_sync_id_must_not_globally_dedup(self):
        """5 repeats, each with sync_id 0,1 → 10 physical syncs, 10 unique UIDs."""
        db_path = make_test_sqlite()
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        tid = 1
        # 5 repeats, each with 2 syncs
        for ri in range(5):
            offset = ri * 500_000
            # NVTX
            cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)",
                        (offset, offset + 200_000, 1, tid))
            cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)",
                        (offset, offset + 200_000, 2, tid))
            cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)",
                        (offset, offset + 200_000, 3, tid))
            # Launch + kernel + stream sync (×2 per repeat)
            for si in range(2):
                cid = 100 + ri * 10 + si
                ls = offset + si * 50_000
                cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)",
                            (ls, ls + 1000, cid, 10, tid))
                cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (ls + 2000, ls + 40_000, 7, cid, f"k_r{ri}_s{si}", 0, 1))
                ss = ls + 30_000  # sync overlaps kernel
                cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)",
                            (ss, ss + 10_000, cid + 1, 11, tid))
                cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (ss, ss + 10_000, cid + 1, 0, 0, 1, 7, -1, -1))
        conn.commit()
        conn.close()

        nvtx, apis, gpus, syncs, schema = load_events_from_sqlite(db_path)
        result = compute_exposed_accounting_v2(
            nvtx, apis, gpus, syncs, schema, workload_id="test_5repeats",
        )
        bd_list = result["b_sync_details"]
        # 5 repeats × 2 syncs = 10 physical syncs
        assert len(bd_list) == 10, f"Expected 10 B rows, got {len(bd_list)}"
        unique_uids = len(set(bd.physical_sync_uid for bd in bd_list))
        assert unique_uids == 10, f"Expected 10 unique UIDs, got {unique_uids}"
        os.unlink(db_path)

    def test_full_request_does_not_duplicate_b(self):
        """1 repeat, 2 prefill + 3 decode syncs → 5 B rows, full=5."""
        populate_test_trace(self.db_path, output_tokens=3)
        nvtx, apis, gpus, syncs, schema = load_events_from_sqlite(self.db_path)
        result = compute_exposed_accounting_v2(
            nvtx, apis, gpus, syncs, schema, workload_id="test_no_fr_dup",
        )
        bd = result["b_sync_details"]
        # Should be exactly the number of physical syncs (1 prefill + 3 decode = 4)
        assert len(bd) == 4, f"Expected 4 B rows, got {len(bd)}"
        bs = result["B_summary"]
        assert bs["prefill"]["total_syncs"] == 1
        assert bs["decode"]["total_syncs"] == 3
        # full_request = prefill + decode
        assert bs["full_request"]["total_syncs"] == 4

    def test_b_coverage_count_weighted(self):
        """Coverage = sum(B_valid) / sum(sync_supported), not mean of per-repeat coverage."""
        db_path = make_test_sqlite()
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        tid = 1
        for ri in range(2):
            offset = ri * 500_000
            cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)",
                        (offset, offset + 200_000, 1, tid))
            cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)",
                        (offset, offset + 200_000, 2, tid))
            cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)",
                        (offset, offset + 200_000, 3, tid))
            # Repeat 0: 1 valid / 1
            # Repeat 1: 1 valid / 9 → many invalid syncs
            sync_count = 1 if ri == 0 else 9
            for si in range(sync_count):
                cid = 100 + ri * 20 + si
                valid = (ri == 0 or si == 0)
                ls = offset + si * 20_000
                cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)",
                            (ls, ls + 1000, cid, 10, tid))
                cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (ls + 2000, ls + 10_000 if valid else ls + 1000, 7, cid, f"k{ri}_{si}", 0, 1))
                ss = ls + 5_000
                cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)",
                            (ss, ss + 5_000, cid + 1, 11, tid))
                cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (ss, ss + 5_000, cid + 1, 0, 0, 1, 7, -1, -1))
        conn.commit()
        conn.close()

        nvtx, apis, gpus, syncs, schema = load_events_from_sqlite(db_path)
        result = compute_exposed_accounting_v2(
            nvtx, apis, gpus, syncs, schema, workload_id="test_cov",
        )
        bs = result["B_summary"]
        # Coverage = 2 / 10 = 0.2 (not mean(1.0, 0.111) = 0.556)
        cov = bs["full_request"].get("B_valid_coverage", 0)
        assert abs(cov - 0.2) < 0.01, f"Expected count-weighted coverage ~0.2, got {cov}"
        os.unlink(db_path)

    def test_gpu_name_from_path(self):
        """GPU name from path inference."""
        name = U._infer_gpu_from_path("/data/nsys_matrix_4090/work/w01.sqlite")
        assert name == "NVIDIA GeForce RTX 4090"
        name2 = U._infer_gpu_from_path("/data/nsys_matrix_6000ada/work/w01.sqlite")
        assert name2 == "NVIDIA RTX 6000 Ada Generation"

    def test_gpu_name_null_for_unknown(self):
        """Unknown path returns None."""
        assert U._infer_gpu_from_path("/unknown/path/file.sqlite") is None

    def test_raw_summary_non_empty(self):
        """raw_summary should be populated with mean/std."""
        populate_test_trace(self.db_path, output_tokens=2)
        nvtx, apis, gpus, syncs, schema = load_events_from_sqlite(self.db_path)
        result = compute_exposed_accounting_v2(
            nvtx, apis, gpus, syncs, schema, workload_id="test_raw",
        )
        rs = result.get("raw_summary", {})
        assert any(rs.values()), "raw_summary should not be empty"
        for phase in ["prefill", "decode", "full_request"]:
            if phase in rs and rs[phase]:
                assert "cuda_api_count_mean" in rs[phase] or "kernel_count_mean" in rs[phase], \
                    f"raw_summary.{phase} should have metric keys"

    def test_dominant_thread_propagates(self):
        """Dominant thread info should appear on all phase rows."""
        populate_test_trace(self.db_path, output_tokens=2)
        nvtx, apis, gpus, syncs, schema = load_events_from_sqlite(self.db_path)
        result = compute_exposed_accounting_v2(
            nvtx, apis, gpus, syncs, schema, workload_id="test_dt",
        )
        for row in result["repeat_results"]:
            # dominant_tid should not be empty string
            assert row.get("dominant_tid") is not None
            assert row.get("dominant_tid") != ""
            assert row.get("dominant_api_count_share") is not None

    def test_b_terminal_ownership_fields(self):
        """B detail rows should have ownership validation fields."""
        populate_test_trace(self.db_path, output_tokens=2)
        nvtx, apis, gpus, syncs, schema = load_events_from_sqlite(self.db_path)
        result = compute_exposed_accounting_v2(
            nvtx, apis, gpus, syncs, schema, workload_id="test_own",
        )
        for bd in result["b_sync_details"]:
            assert hasattr(bd, "terminal_ownership_valid")
            assert hasattr(bd, "cross_phase_wait_flag")
            assert hasattr(bd, "wait_set_unassigned_count")
            assert hasattr(bd, "wait_set_external_count")
            assert hasattr(bd, "terminal_request_id")
            assert hasattr(bd, "terminal_phase")

    def test_physical_sync_uid_present(self):
        """Every B detail must have a non-empty physical_sync_uid."""
        populate_test_trace(self.db_path, output_tokens=2)
        nvtx, apis, gpus, syncs, schema = load_events_from_sqlite(self.db_path)
        result = compute_exposed_accounting_v2(
            nvtx, apis, gpus, syncs, schema, workload_id="test_uid",
        )
        for bd in result["b_sync_details"]:
            assert bd.physical_sync_uid, "physical_sync_uid must not be empty"
            assert bd.physical_sync_uid.startswith("corr="), \
                f"Expected corr= prefix for correlated sync, got {bd.physical_sync_uid}"

    def test_window_id_not_used_as_request_id(self):
        """window_id and request_id must be different when window_id != 1."""
        db_path = make_test_sqlite()
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        tid = 1
        # 2 repeats → different full_request window_ids
        for ri in range(2):
            offset = ri * 500_000
            cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)",
                        (offset, offset + 200_000, 1, tid))
            cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)",
                        (offset, offset + 200_000, 2, tid))
            cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)",
                        (offset, offset + 200_000, 3, tid))
            cid = 100 + ri * 10
            cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)",
                        (offset, offset + 1000, cid, 10, tid))
            cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (offset + 2000, offset + 100_000, 7, cid, f"k_r{ri}", 0, 1))
            ss = offset + 50_000
            cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)",
                        (ss, ss + 10_000, cid + 1, 11, tid))
            cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (ss, ss + 10_000, cid + 1, 0, 0, 1, 7, -1, -1))
        conn.commit()
        conn.close()

        nvtx, apis, gpus, syncs, schema = load_events_from_sqlite(db_path)
        result = compute_exposed_accounting_v2(
            nvtx, apis, gpus, syncs, schema, workload_id="test_wid_vs_rid",
        )
        # Check that request_id is normalized (1 or 2), not raw window_id
        for bd in result["b_sync_details"]:
            assert bd.request_id in (1, 2), \
                f"request_id should be 1 or 2, got {bd.request_id}"
            assert bd.terminal_request_id in (1, 2), \
                f"terminal_request_id should be 1 or 2, got {bd.terminal_request_id}"
            # Ownership should be valid
            assert bd.terminal_ownership_valid, \
                f"terminal_ownership should be valid for uid={bd.physical_sync_uid}"
        # External count should be 0
        total_ext = sum(bd.wait_set_external_count or 0 for bd in result["b_sync_details"])
        assert total_ext == 0, f"wait_set_external_count should be 0, got {total_ext}"
        os.unlink(db_path)

    def test_multi_repeat_ownership_all_valid(self):
        """5 repeats, each with different internal window_id → all ownership valid."""
        db_path = make_test_sqlite()
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        tid = 1
        # window_ids will be 0, 3, 6, 9, 12 (3 NVTX ranges per repeat)
        # request_ids should be 1, 2, 3, 4, 5
        for ri in range(5):
            offset = ri * 500_000
            cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)",
                        (offset, offset + 200_000, 1, tid))
            cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)",
                        (offset, offset + 200_000, 2, tid))
            cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)",
                        (offset, offset + 200_000, 3, tid))
            cid = 100 + ri * 10
            cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)",
                        (offset, offset + 1000, cid, 10, tid))
            cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (offset + 2000, offset + 100_000, 7, cid, f"k_r{ri}", 0, 1))
            ss = offset + 50_000
            cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)",
                        (ss, ss + 10_000, cid + 1, 11, tid))
            cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (ss, ss + 10_000, cid + 1, 0, 0, 1, 7, -1, -1))
        conn.commit()
        conn.close()

        nvtx, apis, gpus, syncs, schema = load_events_from_sqlite(db_path)
        result = compute_exposed_accounting_v2(
            nvtx, apis, gpus, syncs, schema, workload_id="test_5r_own",
        )
        bd_list = result["b_sync_details"]
        assert len(bd_list) == 5  # 1 sync per repeat
        for bd in bd_list:
            assert bd.request_id in (1, 2, 3, 4, 5)
            assert bd.terminal_ownership_valid
        total_ext = sum(bd.wait_set_external_count or 0 for bd in bd_list)
        assert total_ext == 0
        os.unlink(db_path)

    def test_gpu_activity_inherits_normalized_request_id(self):
        """GPU activity must inherit normalized request_id (not window_id)."""
        populate_test_trace(self.db_path, output_tokens=2)
        nvtx, apis, gpus, syncs, schema = load_events_from_sqlite(self.db_path)
        result = compute_exposed_accounting_v2(
            nvtx, apis, gpus, syncs, schema, workload_id="test_ga_inherit",
        )
        for bd in result["b_sync_details"]:
            # terminal_request_id should be 1 (normalized), not the raw window_id
            if bd.terminal_request_id >= 0:
                assert bd.terminal_request_id == 1, \
                    f"terminal_request_id should be 1, got {bd.terminal_request_id}"

    def test_a_regression_after_ownership_fix(self):
        """A-layer values must stay unchanged after ownership fixes."""
        populate_test_trace(self.db_path, output_tokens=2,
                            prompt_ns=100_000, kernel_dur_ns=500_000, sync_delay_ns=50_000)
        nvtx, apis, gpus, syncs, schema = load_events_from_sqlite(self.db_path)
        result = compute_exposed_accounting_v2(
            nvtx, apis, gpus, syncs, schema, workload_id="test_a_reg",
        )
        a = result["A_summary"].get("prefill", {})
        # A values should be close to the original expected values
        assert abs((a.get("A_host_path_ms_mean", 0) or 0) - 0.475) < 0.05
        assert abs((a.get("A_cuda_api_ms_mean", 0) or 0) - 0.100) < 0.05
        assert a.get("A_sync_residual_ms_mean", 0) > 0, "A_sync_residual must be > 0"

    def test_b_count_regression_after_ownership_fix(self):
        """B row count and dedup must stay correct after ownership fixes."""
        populate_test_trace(self.db_path, output_tokens=3)
        nvtx, apis, gpus, syncs, schema = load_events_from_sqlite(self.db_path)
        result = compute_exposed_accounting_v2(
            nvtx, apis, gpus, syncs, schema, workload_id="test_b_count",
        )
        bd = result["b_sync_details"]
        assert len(bd) == 4  # 1 prefill + 3 decode
        assert len(set(b.physical_sync_uid for b in bd)) == 4
        assert result["B_summary"]["full_request"]["total_syncs"] == 4

    def test_early_activity_captured_by_raw_stats(self):
        """Activity starting long before window must still be counted if it overlaps."""
        db_path = make_test_sqlite()
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        tid = 1
        # NVTX: prepare_input [0, 100k], prefill [100k, 500k]
        cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)", (0, 600_000, 1, tid))
        cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)", (0, 100_000, 2, tid))
        cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)", (100_000, 500_000, 3, tid))
        # Memcpy: starts at t=1000 (during prepare_input), ends at t=150000 (during prefill)
        cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)",
                    (0, 500, 100, 13, tid))  # cudaMemcpyAsync
        cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_MEMCPY VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (1000, 150_000, 7, 100, 1, 0, 1))  # D2H, starts early, ends in prefill
        # Many kernels between memcpy start and prefill window start (to test bisect)
        for i in range(200):
            ks = 2000 + i * 400
            cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)",
                        (ks, ks + 100, 200 + i, 10, tid))
            cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (ks + 100, ks + 300, 7, 200 + i, f"k{i}", 0, 1))
        conn.commit()
        conn.close()

        nvtx, apis, gpus, syncs, schema = load_events_from_sqlite(db_path)
        result = compute_exposed_accounting_v2(
            nvtx, apis, gpus, syncs, schema, workload_id="test_early",
        )
        # Check Raw prefill: memcpy should be counted
        for row in result["repeat_results"]:
            if row["phase"] == "prefill":
                assert row["memcpy_count"] >= 1, \
                    f"Memcpy should be counted in prefill, got {row['memcpy_count']}"
        os.unlink(db_path)

    def test_raw_memcpy_consistency_with_b_terminal(self):
        """If B terminal is memcpy, Raw phase must count it or explain why not."""
        populate_test_trace(self.db_path, output_tokens=2)
        nvtx, apis, gpus, syncs, schema = load_events_from_sqlite(self.db_path)
        result = compute_exposed_accounting_v2(
            nvtx, apis, gpus, syncs, schema, workload_id="test_consistency",
        )
        gpu_map = {g.activity_id: g for g in gpus}
        for bd in result["b_sync_details"]:
            terminal = gpu_map.get(bd.terminal_activity_id)
            if terminal is None:
                continue
            for row in result["repeat_results"]:
                if row["phase"] == bd.phase and row["repeat_id"] == bd.request_id:
                    if terminal.activity_type == "memcpy":
                        if row["memcpy_count"] == 0:
                            assert bd.cross_phase_wait_flag, \
                                f"memcpy_count=0 but not cross-phase for {bd.physical_sync_uid}"
                    break

    def test_interval_query_with_non_monotonic_end_times(self):
        """Prefix-max-end must handle A=[0,100], B=[10,20], C=[30,40], window=[50,60]."""
        from analysis.exposed_accounting import filter_objects_by_window, _build_prefix_max_end
        from dataclasses import dataclass

        @dataclass
        class Obj:
            start_ns: int
            end_ns: int

        # A=[0,100], B=[10,20], C=[30,40] — sorted by start_ns
        objs = [Obj(0, 100), Obj(10, 20), Obj(30, 40)]
        # end_array = [100, 20, 40] — NOT monotonic!
        # A overlaps [50,60], B and C do not
        start_arr = [o.start_ns for o in objs]
        pmax = _build_prefix_max_end(objs, "end_ns")
        result = filter_objects_by_window(objs, 50, 60, start_array=start_arr, prefix_max_end=pmax)
        assert len(result) == 1, f"Expected 1 (A), got {len(result)}"
        assert result[0].end_ns == 100, "Should capture A=[0,100]"

    def test_long_activity_started_far_before_window(self):
        """Activity at index 0 with very long duration must be found."""
        from analysis.exposed_accounting import filter_objects_by_window, _build_prefix_max_end
        from dataclasses import dataclass

        @dataclass
        class Obj:
            start_ns: int
            end_ns: int

        objs = [Obj(0, 1000)] + [Obj(i, i + 1) for i in range(100, 5000, 10)]
        start_arr = [o.start_ns for o in objs]
        pmax = _build_prefix_max_end(objs, "end_ns")
        # window far ahead
        result = filter_objects_by_window(objs, 800, 900, start_array=start_arr, prefix_max_end=pmax)
        assert any(o.end_ns == 1000 for o in result), "Must find long activity"

    def test_multistream_overlapping_activity_query(self):
        """Activities on different streams with overlapping times must all be found."""
        db_path = make_test_sqlite()
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        tid = 1
        cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)", (0, 500_000, 1, tid))
        cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)", (0, 500_000, 2, tid))
        cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)", (0, 500_000, 3, tid))
        # Kernel on stream 0
        cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)",
                    (0, 100, 100, 10, tid))
        cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (200, 100_000, 0, 100, "k_stream0", 0, 1))
        # Kernel on stream 7
        cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)",
                    (0, 100, 200, 10, tid))
        cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (300, 90_000, 7, 200, "k_stream7", 0, 1))
        conn.commit()
        conn.close()

        nvtx, apis, gpus, syncs, schema = load_events_from_sqlite(db_path)
        result = compute_exposed_accounting_v2(
            nvtx, apis, gpus, syncs, schema, workload_id="test_multistream",
        )
        for row in result["repeat_results"]:
            if row["phase"] == "prefill":
                assert row["kernel_count"] >= 2, f"Expected 2 kernels, got {row['kernel_count']}"
        os.unlink(db_path)

    def test_multithread_overlapping_api_query(self):
        """APIs on different threads within window must all be found."""
        db_path = make_test_sqlite()
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        # Two threads
        cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)", (0, 500_000, 1, 1))
        cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)", (0, 500_000, 2, 1))
        cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)", (0, 500_000, 3, 1))
        cur.execute("INSERT INTO NVTX_EVENTS VALUES (?, ?, ?, ?)", (0, 500_000, 1, 2))
        # Thread 1 APIs
        for i in range(10):
            cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)",
                        (i * 1000, i * 1000 + 500, 100 + i, 10, 1))
        # Thread 2 APIs
        for i in range(10):
            cur.execute("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)",
                        (5000 + i * 1000, 5000 + i * 1000 + 500, 200 + i, 10, 2))
        conn.commit()
        conn.close()

        nvtx, apis, gpus, syncs, schema = load_events_from_sqlite(db_path)
        result = compute_exposed_accounting_v2(
            nvtx, apis, gpus, syncs, schema, workload_id="test_multithread",
        )
        for row in result["repeat_results"]:
            if row["phase"] == "prefill":
                assert row["cuda_api_count"] >= 20, f"Expected >=20 APIs, got {row['cuda_api_count']}"
        os.unlink(db_path)


class TestIntervalIndex:
    """Tests for the IntervalIndex class."""

    @staticmethod
    def _obj(s, e, aid=0):
        from dataclasses import dataclass
        @dataclass
        class O:
            start_ns: int
            end_ns: int
            activity_id: int = 0
        return O(s, e, aid)

    def test_basic_query(self):
        objs = [self._obj(0, 100), self._obj(10, 20), self._obj(30, 40)]
        idx = U.IntervalIndex(objs)
        r = idx.query(50, 60)
        assert len(r) == 1
        assert r[0].end_ns == 100

    def test_multiple_long_short_interleaving(self):
        objs = [
            self._obj(0, 1000, aid=1),
            self._obj(10, 20, aid=2),
            self._obj(30, 900, aid=3),
            self._obj(40, 50, aid=4),
        ]
        idx = U.IntervalIndex(objs)
        r = idx.query(800, 850)
        ids = {x.activity_id for x in r}
        assert 1 in ids, "A=[0,1000] must be found"
        assert 3 in ids, "C=[30,900] must be found"
        assert 2 not in ids, "B=[10,20] should not be found"

    def test_empty_window(self):
        objs = [self._obj(0, 100)]
        idx = U.IntervalIndex(objs)
        assert idx.query(100, 50) == []

    def test_no_overlap(self):
        objs = [self._obj(0, 10), self._obj(20, 30)]
        idx = U.IntervalIndex(objs)
        assert idx.query(15, 18) == []

    def test_exact_boundary_excluded(self):
        """end == start is excluded (half-open interval)."""
        objs = [self._obj(0, 50), self._obj(60, 100)]
        idx = U.IntervalIndex(objs)
        r = idx.query(50, 60)
        # [0,50): end=50 == ws=50 → excluded
        # [60,100): start=60 == we=60 → excluded
        assert len(r) == 0

    def test_cross_phase_d2h(self):
        """D2H from prepare_input crossing into prefill must be found."""
        objs = [
            self._obj(0, 10, aid=1),    # short kernel
            self._obj(50, 150, aid=2),  # D2H memcpy starting in prepare_input
            self._obj(120, 130, aid=3), # short kernel inside prefill
        ]
        idx = U.IntervalIndex(objs)
        # prefill = [100, 200]
        r = idx.query(100, 200)
        ids = {x.activity_id for x in r}
        assert 2 in ids, "D2H memcpy crossing from prepare_input must be found"
        assert 3 in ids, "Kernel inside prefill must be found"

    def test_d2h_ends_before_prefill(self):
        """D2H ending before prefill window must NOT be counted."""
        objs = [
            self._obj(50, 90, aid=1),   # ends before prefill
            self._obj(120, 150, aid=2), # inside prefill
        ]
        idx = U.IntervalIndex(objs)
        r = idx.query(100, 200)
        ids = {x.activity_id for x in r}
        assert 1 not in ids, "D2H ending before window must not be found"

    def test_full_request_contains_all_sub_phase(self):
        """full_request memcpy count >= prefill memcpy count."""
        objs = [
            self._obj(50, 150, aid=1),   # D2H: overlaps prefill+decode
            self._obj(120, 130, aid=2),  # kernel in prefill
            self._obj(250, 300, aid=3),  # kernel in decode
        ]
        idx = U.IntervalIndex(objs)
        pf = idx.query(100, 200)
        dc = idx.query(200, 400)
        fr = idx.query(100, 400)
        pf_mem = [x for x in pf if x.activity_id == 1]
        fr_mem = [x for x in fr if x.activity_id == 1]
        assert len(fr_mem) >= len(pf_mem), "full_request must contain prefill's memcpy"

    def test_type_classification_after_query(self):
        """Activity type classification must be correct after query."""
        from dataclasses import dataclass

        @dataclass
        class GA:
            start_ns: int
            end_ns: int
            activity_type: str
            activity_id: int = 0

        objs = [
            GA(0, 100, "kernel", 1),
            GA(10, 20, "kernel", 2),
            GA(50, 150, "memcpy", 3),
            GA(120, 130, "memset", 4),
            GA(200, 300, "kernel", 5),
        ]
        idx = U.IntervalIndex(objs)
        r = idx.query(100, 200)
        kernels = [x for x in r if x.activity_type == "kernel"]
        memcpys = [x for x in r if x.activity_type == "memcpy"]
        memsets = [x for x in r if x.activity_type == "memset"]
        # [0,100] end=100 == ws=100 → half-open excluded
        # [10,20] end=20 <= 100 → excluded
        # [200,300] start=200 == we=200 → half-open excluded
        assert len(kernels) == 0, f"Expected 0 kernels, got {len(kernels)}"
        assert len(memcpys) == 1, f"Expected 1 memcpy, got {len(memcpys)}"
        assert len(memsets) == 1, f"Expected 1 memset, got {len(memsets)}"

    def test_index_internal_consistency(self):
        """IntervalIndex objects/starts/prefix_max_ends share same length."""
        objs = [self._obj(0, 100), self._obj(10, 20)]
        idx = U.IntervalIndex(objs)
        assert len(idx.objects) == len(idx._starts) == len(idx._prefix_max_ends)
        assert idx.objects[0].start_ns == 0


class TestSchema:
    def test_meta_export(self):
        db_path = make_test_sqlite()
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        meta = U.read_meta_export(cur)
        assert meta.get("EXPORT_SCHEMA_VERSION") == "3.24.8"
        assert meta.get("EXPORT_PRODUCT_VERSION") == "2025.6.3.541"
        conn.close()
        os.unlink(db_path)

    def test_schema_version_in_inspect(self):
        db_path = make_test_sqlite()
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        schema = U.inspect_schema(cur)
        assert schema["schema_version"] == "3.24.8"
        assert schema["nsys_product_version"] == "2025.6.3.541"
        conn.close()
        os.unlink(db_path)


# ===================================================================
# Main runner
# ===================================================================

def run_tests():
    import traceback
    test_classes = [
        TestIntervalUtils, TestIsSyncApi, TestNvtxWindows,
        TestCorrelation, TestFullPipeline, TestSchema,
    ]
    total = passed = failed = 0
    errors = []
    for tc in test_classes:
        instance = tc()
        for name in dir(instance):
            if name.startswith("test_"):
                total += 1
                method = getattr(instance, name)
                try:
                    if hasattr(instance, "setup_method"):
                        instance.setup_method()
                    method()
                    if hasattr(instance, "teardown_method"):
                        instance.teardown_method()
                    passed += 1
                    print(f"  ✓ {tc.__name__}.{name}")
                except Exception as e:
                    failed += 1
                    msg = f"  ✗ {tc.__name__}.{name}: {e}"
                    print(msg)
                    errors.append(msg)
                    if hasattr(instance, "teardown_method"):
                        try:
                            instance.teardown_method()
                        except Exception:
                            pass
    print(f"\n{'='*50}")
    print(f"  Results: {passed}/{total} passed, {failed} failed")
    if errors:
        print(f"\n  Failures:")
        for err in errors:
            print(f"    {err}")
    print(f"{'='*50}")
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
