#!/usr/bin/env python3
"""
Exposed Latency Accounting — v2 (exposedpath-v2).

Reads a nsys .sqlite file and computes:
  Raw  – per-phase event counts, durations, GPU activity
  S    – sync semantic preprocessing (wait set validity)
  A    – mutually-exclusive wall-clock accounting (interval-based)
  B    – per-sync local diagnostics (valid syncs only, one row per physical sync)

Usage:
    python analysis/exposed_accounting.py --sqlite <file.sqlite> --output-dir <dir>

Output files per workload:
    accounting/accounting_result.json
    accounting/accounting_summary.csv
    accounting/b_sync_detail.csv
"""

from __future__ import annotations

import argparse
import bisect
import csv
import json
import math
import os
import sqlite3
import sys
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Optional, Union

# Import internal utilities
try:
    from . import accounting_utils as U
except ImportError:
    try:
        from analysis import accounting_utils as U
    except ModuleNotFoundError:
        _script_dir = os.path.dirname(os.path.abspath(__file__))
        _parent_dir = os.path.dirname(_script_dir)
        if _parent_dir not in sys.path:
            sys.path.insert(0, _parent_dir)
        from analysis import accounting_utils as U

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_git_commit() -> Optional[str]:
    """Get current git commit hash, or None if unavailable."""
    try:
        import subprocess
        script_dir = os.path.dirname(os.path.abspath(__file__))
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=script_dir, capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()[:12]
    except Exception:
        pass
    return None


def _utc_now_iso() -> str:
    """ISO 8601 UTC timestamp."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

A_CATEGORIES = [
    "A_host_path", "A_cuda_api", "A_device_wait",
    "A_sync_residual", "A_unattributed",
]


# ---------------------------------------------------------------------------
# 1. Schema-adaptive event loader (with sync activities)
# ---------------------------------------------------------------------------

def load_events_from_sqlite(sqlite_path: str) -> tuple[list, list, list, list, dict]:
    """Load all events + sync activities from nsys SQLite.

    Returns: (nvtx_raw, cuda_apis, gpu_activities, sync_activities, schema)
    """
    conn = U.open_readonly_sqlite(sqlite_path)
    cur = conn.cursor()

    schema = U.inspect_schema(cur)
    print(f"  Schema version: {schema['schema_version']}")
    print(f"  Nsight Systems: {schema['nsys_product_version']}")
    print(f"  Tables: {len(schema['all_tables'])} total")

    if schema["critical_missing"]:
        for msg in schema["critical_missing"]:
            print(f"  CRITICAL: {msg}")
        conn.close()
        raise RuntimeError(f"Critical tables missing: {', '.join(schema['critical_missing'])}")

    for msg in schema["missing_optional"]:
        print(f"  WARNING: {msg}")

    # String lookup (one-shot)
    strings = U.build_string_lookup(cur)
    print(f"  Loaded {len(strings)} strings")

    # Enum lookups
    sync_type_enum = U.build_enum_lookup(cur, schema.get("enum_sync_type_table", ""))
    memcpy_kinds = U.build_enum_lookup(cur, "ENUM_CUDA_MEMCPY_OPER")

    def resolve_name(name_id) -> str:
        try:
            nid = int(name_id)
        except (ValueError, TypeError):
            return str(name_id)
        return strings.get(nid, f"id_{nid}")

    # ---- NVTX ----
    nvtx_raw = _load_nvtx(cur, schema, resolve_name)
    print(f"  Loaded {len(nvtx_raw)} NVTX ranges")

    # ---- CUDA API ----
    cuda_apis = _load_cuda_apis(cur, schema, resolve_name)
    print(f"  Loaded {len(cuda_apis)} CUDA API calls")

    # ---- GPU activities ----
    gpu_activities = _load_gpu_activities(cur, schema, strings, memcpy_kinds)
    print(f"  Loaded {len(gpu_activities)} GPU activities "
          f"(kernels: {sum(1 for g in gpu_activities if g.activity_type == 'kernel')}, "
          f"memcpy: {sum(1 for g in gpu_activities if g.activity_type == 'memcpy')}, "
          f"memset: {sum(1 for g in gpu_activities if g.activity_type == 'memset')})")

    # ---- Sync activities (CUPTI_ACTIVITY_KIND_SYNCHRONIZATION) ----
    sync_activities = _load_sync_activities(cur, schema)
    print(f"  Loaded {len(sync_activities)} sync activities")

    conn.close()
    return nvtx_raw, cuda_apis, gpu_activities, sync_activities, schema


def _load_nvtx(cur, schema, resolve_name) -> list[dict]:
    nvtx_table = schema["nvtx_table"]
    if not nvtx_table:
        return []
    nvtx_cols = schema["table_columns"].get(nvtx_table, [])
    nvtx_cm = U.col_map_from_columns(nvtx_cols)
    start_c = U.pick_col(nvtx_cm, "start", "startns", "start_ns")
    end_c = U.pick_col(nvtx_cm, "end", "endns", "end_ns")
    text_c = U.pick_col(nvtx_cm, "text", "textid", "text_id", "name", "nvtxname")
    tid_c = U.pick_col(nvtx_cm, "threadid", "thread_id", "globaltid", "global_tid")
    if not (start_c and end_c):
        return []
    # Build the quoted column expressions outside the f-strings. Before PEP 701
    # (Python < 3.12) an f-string expression part may not contain a backslash,
    # and its delimiter quote terminates the literal even inside an expression;
    # the previous inline form therefore failed to compile on older hosts with
    # "SyntaxError: unterminated triple-quoted string literal". The generated
    # SQL is byte-for-byte unchanged.
    text_col = '"' + text_c + '"' if text_c else "CAST('''' AS TEXT)"
    tid_col = '"' + tid_c + '"' if tid_c else "0"
    query = (f'SELECT "{start_c}", "{end_c}", '
             f"{text_col}, {tid_col} "
             f'FROM "{nvtx_table}" ORDER BY "{start_c}"')
    result = []
    try:
        for row in cur.execute(query):
            name = resolve_name(row[2]) if row[2] != "" else ""
            result.append({
                "start_ns": int(row[0]), "end_ns": int(row[1]),
                "name": name, "global_tid": int(row[3]) if len(row) > 3 else 0,
            })
    except sqlite3.OperationalError as e:
        print(f"  ERROR reading NVTX: {e}")
    return result


def _load_cuda_apis(cur, schema, resolve_name) -> list[U.CudaApi]:
    rt_table = schema["runtime_table"]
    if not rt_table:
        return []
    rt_cols = schema["table_columns"].get(rt_table, [])
    rt_cm = U.col_map_from_columns(rt_cols)
    start_c = U.pick_col(rt_cm, "start", "startns", "start_ns")
    end_c = U.pick_col(rt_cm, "end", "endns", "end_ns")
    name_id_c = U.pick_col(rt_cm, "nameid", "name_id", "textid")
    corr_c = U.pick_col(rt_cm, "correlationid", "correlation_id")
    tid_c = U.pick_col(rt_cm, "threadid", "thread_id", "globaltid")
    ret_c = U.pick_col(rt_cm, "returnvalue", "return_value")
    pid_c = U.pick_col(rt_cm, "processid", "process_id", "pid")
    if not start_c:
        return []
    select = [f'"{start_c}"']
    select.append(f'"{end_c}"' if end_c else f'"{start_c}"')
    select.append(f'"{name_id_c}"' if name_id_c else "NULL")
    select.append(f'"{corr_c}"' if corr_c else "-1")
    select.append(f'"{tid_c}"' if tid_c else "0")
    select.append(f'"{ret_c}"' if ret_c else "0")
    select.append(f'"{pid_c}"' if pid_c else "0")
    query = f"SELECT {', '.join(select)} FROM \"{rt_table}\" ORDER BY {select[0]}"
    apis = []
    try:
        for i, row in enumerate(cur.execute(query)):
            name = resolve_name(row[2]) if row[2] is not None else ""
            apis.append(U.CudaApi(
                api_id=i,
                name=name,
                start_ns=int(row[0]),
                end_ns=int(row[1]),
                correlation_id=int(row[3]) if row[3] is not None else -1,
                global_tid=int(row[4]) if len(row) > 4 else 0,
                return_value=int(row[5]) if len(row) > 5 else 0,
                is_explicit_sync=U.is_sync_api(name),
                sync_type=U.classify_sync_type(name),
                process_id=int(row[6]) if len(row) > 6 else 0,
                thread_id=int(row[4]) if len(row) > 4 else 0,
            ))
    except sqlite3.OperationalError as e:
        print(f"  ERROR reading CUDA API: {e}")
    return apis


def _load_gpu_activities(cur, schema, strings, memcpy_kinds) -> list[U.GpuActivity]:
    activities = []
    aid = 0
    # Kernels
    kt = schema["kernel_table"]
    if kt:
        cols = schema["table_columns"].get(kt, [])
        cm = U.col_map_from_columns(cols)
        start_c = U.pick_col(cm, "start", "startns", "start_ns", "beginns")
        end_c = U.pick_col(cm, "end", "endns", "end_ns")
        name_c = U.pick_col(cm, "demangledname", "shortname", "name", "kernelname")
        stream_c = U.pick_col(cm, "streamid", "stream_id")
        corr_c = U.pick_col(cm, "correlationid", "correlation_id")
        dev_c = U.pick_col(cm, "deviceid", "device_id")
        ctx_c = U.pick_col(cm, "contextid", "context_id")
        if start_c and end_c:
            sel = [f'"{start_c}"', f'"{end_c}"',
                   f'"{name_c}"' if name_c else "CAST('' AS TEXT)",
                   f'"{stream_c}"' if stream_c else "0",
                   f'"{corr_c}"' if corr_c else "-1",
                   f'"{dev_c}"' if dev_c else "0",
                   f'"{ctx_c}"' if ctx_c else "0"]
            try:
                for row in cur.execute(
                    f"SELECT {', '.join(sel)} FROM \"{kt}\" ORDER BY {sel[0]}"
                ):
                    name = str(row[2]) if row[2] is not None else ""
                    if name.isdigit() or (name.startswith("id_") and len(name) < 10):
                        name = strings.get(int(name), name) if name.isdigit() else name
                    activities.append(U.GpuActivity(
                        activity_id=aid, activity_type="kernel", name=name,
                        start_ns=int(row[0]), end_ns=int(row[1]),
                        stream_id=int(row[3]) if len(row) > 3 else 0,
                        correlation_id=int(row[4]) if len(row) > 4 else -1,
                        device_id=int(row[5]) if len(row) > 5 else 0,
                        context_id=int(row[6]) if len(row) > 6 else 0,
                    ))
                    aid += 1
            except sqlite3.OperationalError as e:
                print(f"  WARNING: kernel read failed: {e}")
    # Memcpy + Memset
    for op_type, table_key in [("memcpy", "memcpy_table"), ("memset", "memset_table")]:
        tbl = schema.get(table_key)
        if not tbl:
            continue
        cols = schema["table_columns"].get(tbl, [])
        cm = U.col_map_from_columns(cols)
        start_c = U.pick_col(cm, "start", "startns", "start_ns")
        end_c = U.pick_col(cm, "end", "endns", "end_ns")
        stream_c = U.pick_col(cm, "streamid", "stream_id")
        corr_c = U.pick_col(cm, "correlationid", "correlation_id")
        dev_c = U.pick_col(cm, "deviceid", "device_id")
        ctx_c = U.pick_col(cm, "contextid", "context_id")
        bytes_c = U.pick_col(cm, "bytes", "size", "datasize")
        kind_c = U.pick_col(cm, "copykind", "copy_kind", "memcpytype", "type")
        if not (start_c and end_c):
            continue
        sel = [f'"{start_c}"', f'"{end_c}"',
               f'"{stream_c}"' if stream_c else "0",
               f'"{corr_c}"' if corr_c else "-1",
               f'"{dev_c}"' if dev_c else "0",
               f'"{ctx_c}"' if ctx_c else "0",
               f'"{bytes_c}"' if bytes_c else "NULL",
               f'"{kind_c}"' if kind_c else "NULL"]
        try:
            for row in cur.execute(
                f"SELECT {', '.join(sel)} FROM \"{tbl}\" ORDER BY {sel[0]}"
            ):
                bv = None
                if len(row) > 6 and row[6] is not None:
                    try:
                        bv = int(row[6])
                    except (ValueError, TypeError):
                        pass
                kn = ""
                if len(row) > 7 and row[7] is not None:
                    try:
                        kn = memcpy_kinds.get(int(row[7]), str(row[7]))
                    except (ValueError, TypeError):
                        kn = str(row[7])
                activities.append(U.GpuActivity(
                    activity_id=aid, activity_type=op_type, name=kn or op_type,
                    start_ns=int(row[0]), end_ns=int(row[1]),
                    stream_id=int(row[2]) if len(row) > 2 else 0,
                    correlation_id=int(row[3]) if len(row) > 3 else -1,
                    device_id=int(row[4]) if len(row) > 4 else 0,
                    context_id=int(row[5]) if len(row) > 5 else 0,
                    bytes_val=bv, copy_kind=kn,
                ))
                aid += 1
        except sqlite3.OperationalError as e:
            print(f"  WARNING: {op_type} read failed: {e}")
    return activities


def _load_sync_activities(cur, schema) -> list[U.SyncActivity]:
    """Load CUPTI_ACTIVITY_KIND_SYNCHRONIZATION records."""
    sync_table = schema.get("sync_table")
    if not sync_table:
        return []
    cols = schema["table_columns"].get(sync_table, [])
    cm = U.col_map_from_columns(cols)
    start_c = U.pick_col(cm, "start", "startns", "start_ns")
    end_c = U.pick_col(cm, "end", "endns", "end_ns")
    corr_c = U.pick_col(cm, "correlationid", "correlation_id")
    sync_type_c = U.pick_col(cm, "synctype", "sync_type", "type")
    dev_c = U.pick_col(cm, "deviceid", "device_id")
    ctx_c = U.pick_col(cm, "contextid", "context_id")
    stream_c = U.pick_col(cm, "streamid", "stream_id")
    event_c = U.pick_col(cm, "eventid", "event_id")
    event_sync_c = U.pick_col(cm, "eventsyncid", "event_sync_id")

    if not start_c:
        return []

    sel_parts = [f'"{start_c}"']
    sel_parts.append(f'"{end_c}"' if end_c else f'"{start_c}"')
    sel_parts.append(f'"{corr_c}"' if corr_c else "-1")
    sel_parts.append(f'"{sync_type_c}"' if sync_type_c else "-1")
    sel_parts.append(f'"{dev_c}"' if dev_c else "0")
    sel_parts.append(f'"{ctx_c}"' if ctx_c else "0")
    sel_parts.append(f'"{stream_c}"' if stream_c else "-1")
    sel_parts.append(f'"{event_c}"' if event_c else "-1")
    sel_parts.append(f'"{event_sync_c}"' if event_sync_c else "-1")

    query = f"SELECT {', '.join(sel_parts)} FROM \"{sync_table}\" ORDER BY {sel_parts[0]}"
    result = []
    try:
        for i, row in enumerate(cur.execute(query)):
            result.append(U.SyncActivity(
                sync_activity_id=i,
                start_ns=int(row[0]),
                end_ns=int(row[1]),
                correlation_id=int(row[2]) if row[2] is not None else -1,
                sync_type_id=int(row[3]) if len(row) > 3 and row[3] is not None else -1,
                device_id=int(row[4]) if len(row) > 4 and row[4] is not None else 0,
                context_id=int(row[5]) if len(row) > 5 and row[5] is not None else 0,
                stream_id=int(row[6]) if len(row) > 6 and row[6] is not None else -1,
                event_id=int(row[7]) if len(row) > 7 and row[7] is not None else -1,
                event_sync_id=int(row[8]) if len(row) > 8 and row[8] is not None else -1,
            ))
    except sqlite3.OperationalError as e:
        print(f"  WARNING: sync activity read failed: {e}")
    return result


# ---------------------------------------------------------------------------
# 2. NVTX window construction (sweep-line, O(N log N))
# ---------------------------------------------------------------------------

def _parse_v3_invocation_label(label: str) -> dict:
    """Parse EXPOSEDPATH_INVOCATION:<exp_id>:<wmpc_id>:<run_id>:<pass>:<rep>."""
    try:
        parts = label.split(":")
        if len(parts) >= 6 and parts[0] == "EXPOSEDPATH_INVOCATION":
            return {
                "experiment_id": parts[1],
                "wmpc_id": parts[2],
                "run_id": parts[3],
                "pass_label": parts[4],
                "repeat_index": int(parts[5]),
            }
    except (ValueError, IndexError):
        pass
    return {}

def build_nvtx_windows(nvtx_raw: list[dict]) -> list[U.NvtxWindow]:
    if not nvtx_raw:
        return []
    sorted_nvtx = sorted(nvtx_raw, key=lambda x: (x["start_ns"], -x["end_ns"]))
    tid_groups: dict[int, list[dict]] = defaultdict(list)
    for n in sorted_nvtx:
        tid_groups[n.get("global_tid", 0)].append(n)
    windows = []
    wid = 0
    for tid, group in tid_groups.items():
        group.sort(key=lambda x: (x["start_ns"], -x["end_ns"]))
        stack: list[U.NvtxWindow] = []
        for nvtx in group:
            name = nvtx.get("name", "")
            s, e = nvtx["start_ns"], nvtx["end_ns"]
            while stack and stack[-1].end_ns <= s:
                stack.pop()
            # Normalize phase: supports legacy (full_request/prefill/decode) and
            # v3 (EXPOSEDPATH_PHASE:full_request etc.) labels.
            phase = U.normalize_phase_name(name)

            token_idx = -1
            if name.startswith(U.NVTX_DECODE_STEP_PREFIX):
                try:
                    token_idx = int(name[len(U.NVTX_DECODE_STEP_PREFIX):])
                except ValueError:
                    pass

            # Parse v3 invocation label for identity fields
            v3_identity: dict = {}
            if U.is_v3_invocation_label(name):
                v3_identity = _parse_v3_invocation_label(name)
            parent_id = stack[-1].window_id if stack else -1
            depth = len(stack)
            request_id = -1
            for anc in stack:
                if anc.phase == U.NVTX_FULL_REQUEST:
                    request_id = anc.window_id
                    break
            win = U.NvtxWindow(
                window_id=wid, request_id=-1, repeat_id=-1,
                phase=phase, token_idx=token_idx, start_ns=s, end_ns=e,
                global_tid=tid, parent_window_id=parent_id, depth=depth,
            )
            windows.append(win)
            stack.append(win)
            wid += 1
    print(f"  Built {len(windows)} NVTX windows across {len(tid_groups)} threads")
    return windows


def assign_api_to_windows(apis: list[U.CudaApi], windows: list[U.NvtxWindow]) -> None:
    """Assign each CUDA API to its innermost NVTX window. O(N log N + M)."""
    if not windows or not apis:
        return
    wins_by_tid: dict[int, list[U.NvtxWindow]] = defaultdict(list)
    for w in windows:
        wins_by_tid[w.global_tid].append(w)
    apis.sort(key=lambda a: a.start_ns)

    total_assigned = 0
    for tid, tid_wins in wins_by_tid.items():
        tid_wins.sort(key=lambda w: (w.start_ns, -w.end_ns))
        win_starts = [w.start_ns for w in tid_wins]
        tid_apis = [a for a in apis if a.global_tid == tid]
        if not tid_apis:
            continue
        for api in tid_apis:
            idx = bisect.bisect_right(win_starts, api.start_ns) - 1
            if idx < 0:
                idx = 0
            best_win, best_depth = None, -1
            for wi in range(max(0, idx - 10), min(len(tid_wins), idx + 10)):
                w = tid_wins[wi]
                if w.start_ns <= api.start_ns and api.end_ns <= w.end_ns:
                    if w.depth > best_depth:
                        best_depth = w.depth
                        best_win = w
            if best_win:
                api.phase = best_win.phase
                api.token_idx = best_win.token_idx
                _set_api_hierarchy(api, best_win, windows)
                total_assigned += 1

    # Coverage refined later once request windows are known
    global_cov = total_assigned / max(len(apis), 1) * 100
    print(f"  APIs with NVTX window: {total_assigned} / {len(apis)} = {global_cov:.4f}%")


def _set_api_hierarchy(api: U.CudaApi, win: U.NvtxWindow, all_windows: list[U.NvtxWindow]):
    """Record which full_request window the API belongs to via window_id.

    The actual normalized request_id/repeat_id will be set later
    via wid_to_rid mapping after build_repeat_phases.
    """
    current = win
    while current is not None:
        if current.phase == U.NVTX_FULL_REQUEST:
            # Store the raw window_id temporarily; will be remapped later
            api.request_id = current.window_id
            api.repeat_id = current.window_id
            break
        if current.parent_window_id >= 0:
            current = next(
                (w for w in all_windows if w.window_id == current.parent_window_id), None
            )
        else:
            break


# ---------------------------------------------------------------------------
# 3. API-GPU correlation via correlation_id
# ---------------------------------------------------------------------------

def correlate_gpu_to_api(
    gpu_activities: list[U.GpuActivity], cuda_apis: list[U.CudaApi]
) -> dict:
    api_by_corr: dict[int, U.CudaApi] = {}
    for api in cuda_apis:
        cid = api.correlation_id
        if cid >= 0 and cid not in api_by_corr:
            api_by_corr[cid] = api
    matched, tk, tm, ts = 0, 0, 0, 0
    total_k, total_m, total_s = 0, 0, 0
    for ga in gpu_activities:
        if ga.activity_type == "kernel":
            total_k += 1
        elif ga.activity_type == "memcpy":
            total_m += 1
        elif ga.activity_type == "memset":
            total_s += 1
        cid = ga.correlation_id
        if cid >= 0 and cid in api_by_corr:
            api = api_by_corr[cid]
            ga.submit_api_id = api.api_id
            ga.submit_end_ns = api.end_ns
            ga.request_id = api.request_id
            ga.repeat_id = api.repeat_id
            ga.phase = api.phase
            ga.token_idx = api.token_idx
            matched += 1
            if ga.activity_type == "kernel":
                tk += 1
            elif ga.activity_type == "memcpy":
                tm += 1
            elif ga.activity_type == "memset":
                ts += 1
    total = len(gpu_activities)
    stats = {
        "total_gpu_activities": total, "matched_gpu_activities": matched,
        "correlation_coverage": round(matched / total, 4) if total > 0 else 0.0,
        "kernel_correlation_coverage": round(tk / total_k, 4) if total_k > 0 else 0.0,
        "memcpy_correlation_coverage": round(tm / total_m, 4) if total_m > 0 else 0.0,
        "memset_correlation_coverage": round(ts / total_s, 4) if total_s > 0 else 0.0,
    }
    print(f"  GPU correlation coverage: {stats['correlation_coverage']:.1%} ({matched}/{total})")
    return stats


# ---------------------------------------------------------------------------
# 4. Repeat/phase identification
# ---------------------------------------------------------------------------

def build_repeat_phases(windows: list[U.NvtxWindow]) -> list[dict]:
    full_requests = [w for w in windows if w.phase == U.NVTX_FULL_REQUEST]
    full_requests.sort(key=lambda w: w.start_ns)
    prefills = [w for w in windows if w.phase == U.NVTX_PREFILL]
    prefills.sort(key=lambda w: w.start_ns)
    decodes = [w for w in windows if w.phase == U.NVTX_DECODE]
    decodes.sort(key=lambda w: w.start_ns)
    pref_starts = [p.start_ns for p in prefills]
    dec_starts = [d.start_ns for d in decodes]
    repeats = []
    for ri, fr in enumerate(full_requests):
        fr_s, fr_e = fr.start_ns, fr.end_ns
        pf = None
        idx = bisect.bisect_left(pref_starts, fr_s)
        for pi in range(idx, min(len(prefills), idx + 20)):
            if fr_s <= prefills[pi].start_ns < fr_e:
                pf = prefills[pi]
                break
        dc = None
        idx = bisect.bisect_left(dec_starts, fr_s)
        for di in range(idx, min(len(decodes), idx + 20)):
            if fr_s <= decodes[di].start_ns < fr_e:
                dc = decodes[di]
                break
        if pf is None or dc is None:
            continue
        dc_s, dc_e = dc.start_ns, dc.end_ns
        repeats.append({
            "request_id": ri + 1, "repeat_id": ri + 1,
            "full_request": (fr_s, dc_e),
            "prefill": (pf.start_ns, pf.end_ns),
            "decode": (dc_s, dc_e),
        })
    print(f"  Found {len(repeats)} repeats with prefill+decode phases")
    return repeats


# filter_objects_by_window and _build_prefix_max_end are replaced by
# U.IntervalIndex. See accounting_utils.py. Kept as thin wrapper for
# any remaining callers that don't use IntervalIndex.
def filter_objects_by_window(
    objects: list, start_ns: int, end_ns: int,
    start_attr: str = "start_ns", end_attr: str = "end_ns",
    start_array: list = None, prefix_max_end: list = None,
) -> list:
    """Legacy wrapper — prefer U.IntervalIndex.query()."""
    if not objects:
        return []
    if start_array is None:
        start_array = [getattr(o, start_attr) for o in objects]
    hi = bisect.bisect_left(start_array, end_ns)
    hi = min(len(objects), hi)
    lo = 0
    result = []
    for idx in range(lo, hi):
        obj = objects[idx]
        if getattr(obj, end_attr) > start_ns and getattr(obj, start_attr) < end_ns:
            result.append(obj)
    return result


def _build_prefix_max_end(objects: list, end_attr: str = "end_ns") -> list[int]:
    """Legacy — prefer U.IntervalIndex."""
    result = []
    cur_max = 0
    for obj in objects:
        cur_max = max(cur_max, getattr(obj, end_attr))
        result.append(cur_max)
    return result


def _compute_tps(latency_ns: int, tokens: int) -> Optional[float]:
    """Compute tokens per second. Returns None if inputs invalid."""
    if latency_ns <= 0 or tokens <= 0:
        return None
    return round(tokens / (latency_ns / 1e9), 1)


def _compute_in_request_api_coverage(
    apis: list, repeats: list[dict], api_index: U.IntervalIndex,
) -> float:
    """Compute in-request API assignment coverage.

    Numerator: APIs with request_id > 0 (assigned to a full_request).
    Denominator: APIs whose time range overlaps any full_request window.
    """
    num = sum(1 for a in apis if a.request_id > 0)

    # Union of all full_request windows
    fr_intervals = [rep["full_request"] for rep in repeats if rep.get("full_request")]
    if not fr_intervals:
        return 0.0

    fr_merged = U.merge_intervals(fr_intervals)

    # Count APIs within any full_request window (using IntervalIndex)
    denom = 0
    for ws, we in fr_merged:
        denom += len(api_index.query(ws, we))

    return num / max(denom, 1)


# ---------------------------------------------------------------------------
# 5. Raw statistics
# ---------------------------------------------------------------------------

def compute_raw_stats(apis, gpu_activities, ws, we,
                     api_index: U.IntervalIndex = None,
                     gpu_index: U.IntervalIndex = None) -> dict:
    """Compute Raw-level statistics for a time window.

    Activity overlap condition: end_ns > ws AND start_ns < we.
    Uses IntervalIndex for O(log N + k) window queries.
    """
    if api_index is not None:
        win_apis = api_index.query(ws, we)
    else:
        win_apis = [a for a in apis if a.end_ns > ws and a.start_ns < we]
    if gpu_index is not None:
        win_gpus = gpu_index.query(ws, we)
    else:
        win_gpus = [g for g in gpu_activities if g.end_ns > ws and g.start_ns < we]

    # CUDA API
    cuda_api_count = len(win_apis)
    api_intervals = [(max(a.start_ns, ws), min(a.end_ns, we)) for a in win_apis]
    cuda_api_union = U.union_duration(api_intervals)
    launch_count = sum(1 for a in win_apis if not a.is_explicit_sync)
    sync_count = sum(1 for a in win_apis if a.is_explicit_sync)
    distinct_tids = len({a.global_tid for a in win_apis})

    api_name_counts: dict[str, int] = defaultdict(int)
    api_name_dur: dict[str, int] = defaultdict(int)
    for a in win_apis:
        dur = min(a.end_ns, we) - max(a.start_ns, ws)
        api_name_counts[a.name] += 1
        api_name_dur[a.name] += dur
    top_apis = sorted(api_name_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    # Kernels
    kernels = [g for g in win_gpus if g.activity_type == "kernel"]
    kernel_count = len(kernels)
    kernel_intervals = [(max(g.start_ns, ws), min(g.end_ns, we)) for g in kernels]
    kernel_union = U.union_duration(kernel_intervals)
    distinct_kernel_names = len({k.name for k in kernels})
    distinct_streams = len({g.stream_id for g in win_gpus})

    kname_counts: dict[str, int] = defaultdict(int)
    kname_dur: dict[str, int] = defaultdict(int)
    for k in kernels:
        dur = min(k.end_ns, we) - max(k.start_ns, ws)
        kname_counts[k.name] += 1
        kname_dur[k.name] += dur
    top_kernels = sorted(kname_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    # Memcpy
    memcpys = [g for g in win_gpus if g.activity_type == "memcpy"]
    memcpy_count = len(memcpys)
    memcpy_bytes = sum(g.bytes_val for g in memcpys if g.bytes_val is not None)
    memcpy_intervals = [(max(g.start_ns, ws), min(g.end_ns, we)) for g in memcpys]
    memcpy_union = U.union_duration(memcpy_intervals)

    # Memset
    memsets = [g for g in win_gpus if g.activity_type == "memset"]
    memset_count = len(memsets)
    memset_bytes = sum(g.bytes_val for g in memsets if g.bytes_val is not None)
    memset_intervals = [(max(g.start_ns, ws), min(g.end_ns, we)) for g in memsets]
    memset_union = U.union_duration(memset_intervals)

    # GPU activity union
    gpu_all_intervals = [(max(g.start_ns, ws), min(g.end_ns, we)) for g in win_gpus]
    gpu_activity_union = U.union_duration(gpu_all_intervals)
    win_dur = we - ws
    gpu_active_ratio = gpu_activity_union / win_dur if win_dur > 0 else 0.0

    # Multi-stream concurrency
    multistream_concurrent = 0
    if distinct_streams > 1:
        total_raw = sum(e - s for s, e in gpu_all_intervals)
        merged_total = sum(e - s for s, e in U.merge_intervals(gpu_all_intervals))
        multistream_concurrent = max(0, total_raw - merged_total)
    multistream_ratio = multistream_concurrent / win_dur if win_dur > 0 else 0.0

    kernel_merged = U.merge_intervals(kernel_intervals)
    memop_merged = U.merge_intervals(memcpy_intervals + memset_intervals)
    kernel_only = U.union_duration(U.subtract_intervals(kernel_merged, memop_merged))
    memop_only = U.union_duration(U.subtract_intervals(memop_merged, kernel_merged))
    kernel_memop_mixed = U.overlap_duration(kernel_merged, memop_merged)

    return {
        "cuda_api_count": cuda_api_count, "cuda_api_union_ns": cuda_api_union,
        "launch_api_count": launch_count, "sync_api_count": sync_count,
        "distinct_api_thread_count": distinct_tids,
        "top_cuda_api_names": [{"name": n, "count": c, "total_duration_ns": api_name_dur[n]} for n, c in top_apis],
        "kernel_count": kernel_count, "kernel_union_ns": kernel_union,
        "distinct_kernel_name_count": distinct_kernel_names,
        "distinct_stream_count": distinct_streams,
        "top_kernel_names": [{"name": n, "count": c, "total_duration_ns": kname_dur[n]} for n, c in top_kernels],
        "memcpy_count": memcpy_count, "memcpy_bytes": memcpy_bytes if memcpy_count > 0 else None,
        "memcpy_union_ns": memcpy_union,
        "memset_count": memset_count, "memset_bytes": memset_bytes if memset_count > 0 else None,
        "memset_union_ns": memset_union,
        "gpu_activity_union_ns": gpu_activity_union, "gpu_active_ratio": round(gpu_active_ratio, 4),
        "multistream_concurrent_ns": multistream_concurrent,
        "multistream_ratio": round(multistream_ratio, 4),
        "kernel_only_ns": kernel_only, "memop_only_ns": memop_only,
        "kernel_memop_mixed_ns": kernel_memop_mixed,
    }


# ---------------------------------------------------------------------------
# 6. Dominant thread detection
# ---------------------------------------------------------------------------

def find_dominant_thread(apis, request_start, request_end,
                         api_index: U.IntervalIndex = None) -> dict:
    if api_index is not None:
        win_apis = api_index.query(request_start, request_end)
    else:
        win_apis = [a for a in apis if a.end_ns > request_start and a.start_ns < request_end]
    if not win_apis:
        return {"dominant_tid": -1, "dominant_api_count_share": 0.0,
                "dominant_api_time_share": 0.0, "api_thread_count": 0,
                "multi_launch_thread_flag": False}
    tid_counts: dict[int, int] = defaultdict(int)
    tid_dur: dict[int, int] = defaultdict(int)
    for a in win_apis:
        tid = a.global_tid
        tid_counts[tid] += 1
        tid_dur[tid] += min(a.end_ns, request_end) - max(a.start_ns, request_start)
    tc = sum(tid_counts.values())
    td = sum(tid_dur.values())
    dominant_tid = max(tid_counts, key=tid_counts.get)
    cs = tid_counts[dominant_tid] / tc if tc > 0 else 0.0
    ts = tid_dur[dominant_tid] / td if td > 0 else 0.0
    return {
        "dominant_tid": dominant_tid,
        "dominant_api_count_share": round(cs, 4),
        "dominant_api_time_share": round(ts, 4),
        "api_thread_count": len(tid_counts),
        "multi_launch_thread_flag": not (cs >= 0.95 or ts >= 0.95),
    }


# ---------------------------------------------------------------------------
# 7. S-layer: sync semantic preprocessing (fixed)
# ---------------------------------------------------------------------------

def build_sync_records(
    apis: list[U.CudaApi],
    gpu_activities: list[U.GpuActivity],
    sync_activities: list[U.SyncActivity],
    schema: dict,
) -> list[U.SyncRecord]:
    """Pre-process sync APIs using real synchronization activity data."""
    # Build correlation_id → sync_activity index
    sync_act_by_corr: dict[int, U.SyncActivity] = {}
    for sa in sync_activities:
        if sa.correlation_id >= 0 and sa.correlation_id not in sync_act_by_corr:
            sync_act_by_corr[sa.correlation_id] = sa

    # Build GPU activity indexes by context and by (context, stream)
    gpu_by_ctx: dict[int, list[U.GpuActivity]] = defaultdict(list)
    gpu_by_ctx_stream: dict[tuple[int, int], list[U.GpuActivity]] = defaultdict(list)
    for g in gpu_activities:
        gpu_by_ctx[g.context_id].append(g)
        gpu_by_ctx_stream[(g.context_id, g.stream_id)].append(g)

    # Sort each group by submit_end_ns for bisect queries
    def _sort_and_index(group):
        group.sort(key=lambda x: x.submit_end_ns if x.submit_end_ns > 0 else x.start_ns)
        return [g.submit_end_ns if g.submit_end_ns > 0 else g.start_ns for g in group]

    gpu_by_ctx_submit_starts = {}
    for ctx_id, group in gpu_by_ctx.items():
        gpu_by_ctx_submit_starts[ctx_id] = _sort_and_index(group)

    gpu_by_cs_submit_starts = {}
    for (ctx_id, stream_id), group in gpu_by_ctx_stream.items():
        gpu_by_cs_submit_starts[(ctx_id, stream_id)] = _sort_and_index(group)

    sync_apis = [a for a in apis if a.is_explicit_sync and a.request_id >= 0]
    if not sync_apis:
        print("  S-layer: No attributed sync APIs found")
        return []

    sync_records: list[U.SyncRecord] = []
    sync_id = 0

    for api in sync_apis:
        sr = U.SyncRecord(
            sync_id=sync_id, sync_api_id=api.api_id,
            sync_type=api.sync_type, sync_api_name=api.name,
            start_ns=api.start_ns, end_ns=api.end_ns,
            correlation_id=api.correlation_id,
            request_id=api.request_id, repeat_id=api.repeat_id,
            phase=api.phase, token_idx=api.token_idx,
        )

        # ---- Get real context/stream from synchronization activity ----
        sync_act = sync_act_by_corr.get(api.correlation_id)
        if sync_act:
            sr.device_id = sync_act.device_id
            sr.context_id = sync_act.context_id
            sr.stream_id = sync_act.stream_id
            sr.event_id = sync_act.event_id
            sr.event_sync_id = sync_act.event_sync_id
        else:
            pass  # No sync activity — use API name fallback

        # ---- Determine wait set based on sync type ----
        if api.sync_type == "stream":
            _build_stream_wait_set_v2(sr, api, gpu_by_ctx_stream, gpu_by_cs_submit_starts)
        elif api.sync_type == "device":
            _build_device_wait_set_v2(sr, api, gpu_by_ctx, gpu_by_ctx_submit_starts)
        elif api.sync_type == "event":
            sr.wait_set_valid = False
            sr.invalid_reason = "MISSING_EVENT_MAP"
        else:
            sr.wait_set_valid = False
            sr.invalid_reason = "UNSUPPORTED_SYNC_TYPE"

        # ---- Determine terminal activity ----
        if sr.wait_set_valid and sr.wait_activity_ids:
            _find_terminal(sr, gpu_activities)
        elif sr.wait_set_valid and not sr.wait_activity_ids:
            sr.wait_set_valid = False
            sr.invalid_reason = "NO_PENDING_ACTIVITY"

        # ---- Generate physical sync UID (globally unique across repeats) ----
        sr.physical_sync_uid = U.make_physical_sync_uid(
            correlation_id=sr.correlation_id,
            start_ns=sr.start_ns, end_ns=sr.end_ns,
            request_id=sr.request_id, repeat_id=sr.repeat_id,
            sync_type=sr.sync_type, stream_id=sr.stream_id, context_id=sr.context_id,
        )

        sync_records.append(sr)
        sync_id += 1

    valid_ws = sum(1 for s in sync_records if s.wait_set_valid)
    b_valid = sum(1 for s in sync_records if s.B_valid)
    print(f"  S-layer: {len(sync_records)} syncs, {valid_ws} valid wait sets, {b_valid} B-valid")
    return sync_records


def _build_stream_wait_set_v2(
    sr: U.SyncRecord, api: U.CudaApi,
    gpu_by_ctx_stream: dict,
    gpu_by_cs_submit_starts: dict,
):
    """Stream sync wait set: activities on same context+stream, submitted before sync."""
    ctx_id = sr.context_id
    stream_id = sr.stream_id

    if stream_id < 0:
        sr.wait_set_valid = False
        sr.invalid_reason = "MISSING_STREAM_ID"
        return

    key = (ctx_id, stream_id)
    group = gpu_by_ctx_stream.get(key, [])
    submit_starts = gpu_by_cs_submit_starts.get(key, [])

    if not group:
        sr.wait_set_valid = False
        sr.invalid_reason = "NO_PENDING_ACTIVITY"
        return

    wait_ids = _query_wait_set(group, submit_starts, api.start_ns)
    sr.wait_activity_ids = wait_ids
    sr.wait_set_valid = True


def _build_device_wait_set_v2(
    sr: U.SyncRecord, api: U.CudaApi,
    gpu_by_ctx: dict,
    gpu_by_ctx_submit_starts: dict,
):
    """Device sync wait set: all pending activities on same context."""
    ctx_id = sr.context_id

    if ctx_id <= 0:
        sr.wait_set_valid = False
        sr.invalid_reason = "MISSING_CONTEXT_ID"
        return

    group = gpu_by_ctx.get(ctx_id, [])
    submit_starts = gpu_by_ctx_submit_starts.get(ctx_id, [])

    if not group:
        sr.wait_set_valid = False
        sr.invalid_reason = "NO_PENDING_ACTIVITY"
        return

    wait_ids = _query_wait_set(group, submit_starts, api.start_ns)
    sr.wait_activity_ids = wait_ids
    sr.wait_set_valid = True


def _query_wait_set(
    group: list[U.GpuActivity],
    submit_starts: list[int],
    sync_start_ns: int,
) -> list[int]:
    """Query wait set: activities with submit_end_ns <= sync_start AND end_ns > sync_start.

    Uses bisect on submit_end_ns for O(log N + k). No 10ms cutoff.
    """
    if not group:
        return []

    # Find candidates: submit_end_ns <= sync_start_ns
    # bisect_right gives first index where submit > sync_start
    idx = bisect.bisect_right(submit_starts, sync_start_ns) - 1
    if idx < 0:
        return []

    wait_ids = []
    # Scan backwards from idx (these all have submit_end <= sync_start)
    # and forwards (later submissions that might have started before sync_start)
    for i in range(idx + 1):
        g = group[i]
        # Only include if still executing at sync_start
        if g.end_ns > sync_start_ns:
            wait_ids.append(g.activity_id)

    return wait_ids


def _find_terminal(sr: U.SyncRecord, gpu_activities: list[U.GpuActivity]):
    """Find terminal activity (latest end_ns) in wait set."""
    act_map = {g.activity_id: g for g in gpu_activities}
    wait_activities = [act_map[aid] for aid in sr.wait_activity_ids if aid in act_map]
    if not wait_activities:
        sr.B_valid = False
        sr.B_invalid_reason = "NO_PENDING_ACTIVITY"
        return
    max_end = max(g.end_ns for g in wait_activities)
    candidates = [g for g in wait_activities if max_end - g.end_ns <= U.TERMINAL_TOLERANCE_NS]
    if len(candidates) > 1:
        sr.B_valid = False
        sr.B_invalid_reason = "MULTI_TERMINAL"
        return
    terminal = candidates[0]
    sr.terminal_activity_id = terminal.activity_id
    sr.terminal_end_ns = terminal.end_ns
    sr.B_valid = True


# ---------------------------------------------------------------------------
# 8. A-layer: explicit interval-based computation (FIXED)
# ---------------------------------------------------------------------------

def compute_a_layer(
    apis: list[U.CudaApi],
    gpu_activities: list[U.GpuActivity],
    sync_records: list[U.SyncRecord],
    window_start: int, window_end: int, request_id: int,
) -> tuple[dict, U.AIntervals]:
    """Compute A-layer using explicit interval arithmetic.

    Returns:
        (a_result_ns dict, AIntervals for overlap computation)
    """
    gpu_act_map = {g.activity_id: g for g in gpu_activities}

    # ---- Collect intervals ----
    # Sync intervals
    all_sync_intervals = []
    sr_starts = [s.start_ns for s in sync_records]
    win_syncs = filter_objects_by_window(
        sync_records, window_start, window_end,
        start_attr="start_ns", end_attr="end_ns", start_array=sr_starts
    )

    # Device-wait intervals = sync ∩ union(wait_set activities)
    device_wait_parts = []
    for sr in win_syncs:
        cs = max(sr.start_ns, window_start)
        ce = min(sr.end_ns, window_end)
        if ce <= cs:
            continue
        all_sync_intervals.append((cs, ce))
        if sr.wait_set_valid and sr.wait_activity_ids:
            ws_parts = []
            for aid in sr.wait_activity_ids:
                g = gpu_act_map.get(aid)
                if g and g.end_ns > cs and g.start_ns < ce:
                    overlap = U.intersect_one((cs, ce), (g.start_ns, g.end_ns))
                    if overlap:
                        ws_parts.append(overlap)
            if ws_parts:
                device_wait_parts.extend(U.merge_intervals(ws_parts))

    sync_merged = U.merge_intervals(all_sync_intervals)
    device_wait_merged = U.merge_intervals(device_wait_parts)

    # A_device_wait intervals
    a_device_wait = U.intersect_intervals(sync_merged, device_wait_merged)

    # A_sync_residual = sync - device_wait
    a_sync_residual = U.subtract_intervals(sync_merged, device_wait_merged)

    # CUDA API intervals (non-sync, in window)
    api_starts_arr = [a.start_ns for a in apis]
    win_apis = filter_objects_by_window(apis, window_start, window_end, start_array=api_starts_arr)
    api_intervals = []
    for a in win_apis:
        if a.is_explicit_sync:
            continue
        cs, ce = max(a.start_ns, window_start), min(a.end_ns, window_end)
        if ce > cs:
            api_intervals.append((cs, ce))
    a_cuda_api_merged = U.merge_intervals(api_intervals)

    # A_host_path = window - sync - api - unattributed
    all_excluded = U.merge_intervals(
        list(sync_merged) + list(a_cuda_api_merged)
    )
    a_host_path = U.subtract_intervals([(window_start, window_end)], all_excluded)

    # A_unattributed (empty for well-formed traces)
    a_unattributed: list[tuple[int, int]] = []

    intervals = U.AIntervals(
        host_path=a_host_path,
        cuda_api=a_cuda_api_merged,
        device_wait=a_device_wait,
        sync_residual=a_sync_residual,
        unattributed=a_unattributed,
    )

    result = {
        "A_host_path_ns": U.union_duration(a_host_path),
        "A_cuda_api_ns": U.union_duration(a_cuda_api_merged),
        "A_device_wait_ns": U.union_duration(a_device_wait),
        "A_sync_residual_ns": U.union_duration(a_sync_residual),
        "A_unattributed_ns": 0,
    }

    return result, intervals


# ---------------------------------------------------------------------------
# 9. Overlap metrics (using exact A intervals)
# ---------------------------------------------------------------------------

def compute_overlap_metrics(
    a_result: dict,
    a_intervals: U.AIntervals,
    gpu_activities: list[U.GpuActivity],
    window_start: int, window_end: int,
) -> dict:
    """Compute O_api_gpu and O_hostpath_gpu using exact A intervals."""
    gpu_index = U.IntervalIndex(gpu_activities, key_start="start_ns", key_end="end_ns")
    win_gpus = gpu_index.query(window_start, window_end)
    gpu_intervals = [
        (max(g.start_ns, window_start), min(g.end_ns, window_end)) for g in win_gpus
    ]
    gpu_merged = U.merge_intervals(gpu_intervals)

    # O_api_gpu
    api_dur = U.union_duration(a_intervals.cuda_api)
    api_gpu_overlap = U.overlap_duration(a_intervals.cuda_api, gpu_merged)
    O_api_gpu = (api_gpu_overlap / api_dur) if api_dur > 0 else None

    # O_hostpath_gpu
    host_dur = U.union_duration(a_intervals.host_path)
    host_gpu_overlap = U.overlap_duration(a_intervals.host_path, gpu_merged)
    O_hostpath_gpu = (host_gpu_overlap / host_dur) if host_dur > 0 else None

    return {
        "api_gpu_overlap_ns": api_gpu_overlap,
        "O_api_gpu": round(O_api_gpu, 4) if O_api_gpu is not None else None,
        "hostpath_gpu_overlap_ns": host_gpu_overlap,
        "O_hostpath_gpu": round(O_hostpath_gpu, 4) if O_hostpath_gpu is not None else None,
    }


# ---------------------------------------------------------------------------
# 10. B-layer: compute once for all canonical syncs (FIXED)
# ---------------------------------------------------------------------------

def compute_b_for_all_syncs(
    sync_records: list[U.SyncRecord],
    gpu_activities: list[U.GpuActivity],
    workload_id: str,
) -> list[U.BSyncDetail]:
    """Compute B-layer per-sync diagnostics. ONE row per physical sync.

    Each SyncRecord is processed exactly once, regardless of how many
    repeats or phases it belongs to. Dedup is by physical_sync_uid.
    """
    gpu_map = {g.activity_id: g for g in gpu_activities}

    # Pre-index by (context, stream) for predecessor search
    gpu_by_stream: dict[tuple[int, int], list[U.GpuActivity]] = defaultdict(list)
    for g in gpu_activities:
        gpu_by_stream[(g.context_id, g.stream_id)].append(g)
    stream_starts: dict[tuple[int, int], list[int]] = {}
    for key, group in gpu_by_stream.items():
        group.sort(key=lambda x: x.start_ns)
        stream_starts[key] = [g.start_ns for g in group]

    # Index all GPU activities by activity_id for ownership checks
    gpu_by_id = {g.activity_id: g for g in gpu_activities}

    details: list[U.BSyncDetail] = []
    seen_uids: set[str] = set()

    for sr in sync_records:
        uid = sr.physical_sync_uid
        if uid in seen_uids:
            continue
        seen_uids.add(uid)

        # Resolve canonical phase (prefill or decode)
        canonical_phase = sr.phase
        if canonical_phase.startswith("decode_step_"):
            canonical_phase = "decode"

        # Count wait_set ownership
        unassigned_count = 0
        external_count = 0
        for aid in sr.wait_activity_ids:
            g = gpu_by_id.get(aid)
            if g is None:
                unassigned_count += 1
            elif g.request_id < 0:
                unassigned_count += 1
            elif g.request_id != sr.request_id:
                external_count += 1

        detail = U.BSyncDetail(
            workload_id=workload_id,
            physical_sync_uid=uid,
            sync_id=sr.sync_id,
            request_id=sr.request_id, repeat_id=sr.repeat_id,
            phase=canonical_phase, token_idx=sr.token_idx,
            sync_api_correlation_id=sr.correlation_id,
            sync_api_name=sr.sync_api_name,
            sync_type=sr.sync_type,
            sync_start_ns=sr.start_ns, sync_end_ns=sr.end_ns,
            sync_duration_ms=round((sr.end_ns - sr.start_ns) / 1e6, 6),
            context_id=sr.context_id, stream_id=sr.stream_id,
            wait_set_valid=sr.wait_set_valid,
            B_valid=sr.B_valid,
            invalid_reason=sr.B_invalid_reason or sr.invalid_reason,
            wait_set_size=len(sr.wait_activity_ids),
            wait_set_unassigned_count=unassigned_count,
            wait_set_external_count=external_count,
        )

        if sr.B_valid and sr.terminal_activity_id >= 0:
            terminal = gpu_map.get(sr.terminal_activity_id)
            if terminal:
                detail.terminal_activity_id = terminal.activity_id
                detail.terminal_type = terminal.activity_type
                detail.terminal_name = terminal.name
                detail.terminal_stream_id = terminal.stream_id
                detail.terminal_submit_end_ns = terminal.submit_end_ns
                detail.terminal_start_ns = terminal.start_ns
                detail.terminal_end_ns = terminal.end_ns
                detail.terminal_request_id = terminal.request_id
                detail.terminal_repeat_id = terminal.repeat_id
                detail.terminal_phase = terminal.phase
                detail.terminal_api_correlation_id = terminal.correlation_id

                # Ownership validation
                detail.terminal_ownership_valid = (
                    terminal.request_id == sr.request_id
                )
                # Cross-phase: same request/repeat but different phase
                # Normalize decode_step_N → decode before comparing
                def _norm_phase(p: str) -> str:
                    if p.startswith("decode_step_"):
                        return "decode"
                    return p
                detail.cross_phase_wait_flag = (
                    terminal.request_id == sr.request_id
                    and terminal.repeat_id == sr.repeat_id
                    and _norm_phase(terminal.phase) != _norm_phase(sr.phase)
                )

                # B_self: terminal full execution time
                B_self_ns = terminal.end_ns - terminal.start_ns

                # Device overlap: sync ∩ terminal
                sync_term_overlap = U.intersect_one(
                    (sr.start_ns, sr.end_ns),
                    (terminal.start_ns, terminal.end_ns),
                )
                detail.device_overlap_with_sync_ms = (
                    round((sync_term_overlap[1] - sync_term_overlap[0]) / 1e6, 6)
                    if sync_term_overlap else 0.0
                )

                # B_predecessor
                key = (terminal.context_id, terminal.stream_id)
                stream_group = gpu_by_stream.get(key, [])
                s_starts = stream_starts.get(key, [])

                B_predecessor_ns = 0
                if stream_group and s_starts:
                    submit_ns = terminal.submit_end_ns if terminal.submit_end_ns > 0 else terminal.start_ns
                    term_start = terminal.start_ns
                    lo = bisect.bisect_left(s_starts, submit_ns)
                    pred_ivs = []
                    for idx in range(lo, min(len(stream_group), lo + 500)):
                        g = stream_group[idx]
                        if g.start_ns >= term_start:
                            break
                        if g.activity_id == terminal.activity_id:
                            continue
                        if g.end_ns > submit_ns and g.start_ns < term_start:
                            pred_ivs.append((
                                max(g.start_ns, submit_ns),
                                min(g.end_ns, term_start),
                            ))
                    B_predecessor_ns = U.union_duration(pred_ivs)

                # B_stream_gap
                B_stream_gap_ns = max(0, terminal.start_ns -
                    (terminal.submit_end_ns if terminal.submit_end_ns > 0 else terminal.start_ns)
                    - B_predecessor_ns)

                # sync_return_tail with timestamp tolerance
                raw_tail_ns = sr.end_ns - terminal.end_ns
                detail.sync_return_tail_raw_ns = raw_tail_ns
                if raw_tail_ns >= 0:
                    detail.sync_return_tail_ms = round(raw_tail_ns / 1e6, 6)
                elif raw_tail_ns >= -U.TIMESTAMP_TOLERANCE_NS:
                    detail.sync_return_tail_ms = 0.0
                    detail.timestamp_tolerance_applied = True
                else:
                    detail.B_valid = False
                    detail.invalid_reason = "TRACE_ORDERING_ERROR"
                    detail.sync_return_tail_ms = round(raw_tail_ns / 1e6, 6)

                detail.B_predecessor_ms = round(B_predecessor_ns / 1e6, 6)
                detail.B_stream_gap_ms = round(B_stream_gap_ns / 1e6, 6)
                detail.B_self_ms = round(B_self_ns / 1e6, 6)

        details.append(detail)

    return details


# ---------------------------------------------------------------------------
# 11. Output writing
# ---------------------------------------------------------------------------

def _ns_to_ms(val, ndigits=3):
    if val is None:
        return None
    return round(val / 1e6, ndigits)


def write_accounting_result(out_dir, metadata, trace_quality, raw_summary,
                           A_summary, overlap_summary, B_summary,
                           repeat_results, b_sync_details, legacy_compat):
    result = {
        "metric_definition_version": U.METRIC_VERSION,
        "metadata": metadata,
        "trace_quality": trace_quality,
        "raw_summary": raw_summary,
        "A_summary": A_summary,
        "overlap_summary": overlap_summary,
        "B_summary": B_summary,
        "repeat_results": repeat_results,
        "b_sync_details": [asdict(bd) for bd in b_sync_details],
    }
    if legacy_compat:
        result["legacy_compatibility"] = legacy_compat
    path = out_dir / "accounting_result.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    print(f"  → {path}")


def write_accounting_summary_csv(out_dir, rows):
    if not rows:
        return
    columns = [
        "workload_id", "request_id", "repeat_id", "phase",
        "prompt_len", "batch_size", "output_len", "gpu_name", "window_duration_ms",
        "cuda_api_count", "cuda_api_union_ms", "launch_api_count", "sync_api_count",
        "kernel_count", "kernel_union_ms", "memcpy_count", "memcpy_bytes", "memcpy_union_ms",
        "memset_count", "gpu_activity_union_ms", "gpu_active_ratio",
        "distinct_stream_count", "multistream_ratio",
        "A_host_path_ms", "A_cuda_api_ms", "A_device_wait_ms",
        "A_sync_residual_ms", "A_unattributed_ms",
        "A_host_path_pct", "A_cuda_api_pct", "A_device_wait_pct",
        "A_sync_residual_pct", "A_unattributed_pct",
        "epsilon_ms", "conservation_error_pct",
        "api_gpu_overlap_ms", "O_api_gpu",
        "hostpath_gpu_overlap_ms", "O_hostpath_gpu",
        "dominant_tid", "dominant_api_count_share", "dominant_api_time_share",
        "multi_launch_thread_flag", "correlation_coverage", "boundary_valid",
        "sync_supported_count", "B_valid_count", "B_invalid_count",
        "B_valid_coverage", "top_invalid_reason",
    ]
    path = out_dir / "accounting_summary.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print(f"  → {path}")


def write_b_sync_detail_csv(out_dir, details):
    if not details:
        return
    columns = [
        "workload_id", "physical_sync_uid", "sync_id",
        "request_id", "repeat_id", "phase", "token_idx",
        "sync_api_correlation_id", "sync_api_name", "sync_type",
        "sync_start_ns", "sync_end_ns", "sync_duration_ms",
        "context_id", "stream_id",
        "wait_set_valid", "B_valid", "invalid_reason",
        "wait_set_size", "wait_set_unassigned_count", "wait_set_external_count",
        "terminal_activity_id", "terminal_type", "terminal_name",
        "terminal_request_id", "terminal_repeat_id", "terminal_phase",
        "terminal_api_correlation_id",
        "terminal_ownership_valid", "cross_phase_wait_flag",
        "terminal_stream_id", "terminal_submit_end_ns",
        "terminal_start_ns", "terminal_end_ns",
        "B_predecessor_ms", "B_stream_gap_ms", "B_self_ms",
        "device_overlap_with_sync_ms",
        "sync_return_tail_ms", "sync_return_tail_raw_ns",
        "timestamp_tolerance_applied",
    ]
    path = out_dir / "b_sync_detail.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        for d in details:
            writer.writerow([getattr(d, c, "") for c in columns])
    print(f"  → {path}")


# ---------------------------------------------------------------------------
# 12. Main orchestration
# ---------------------------------------------------------------------------

def compute_exposed_accounting_v2(
    nvtx_raw, cuda_apis, gpu_activities, sync_activities, schema,
    workload_id="", gpu_name="", prompt_len=0, batch_size=0, output_len=0,
) -> dict:
    windows = build_nvtx_windows(nvtx_raw)
    assign_api_to_windows(cuda_apis, windows)
    corr_stats = correlate_gpu_to_api(gpu_activities, cuda_apis)
    repeats = build_repeat_phases(windows)
    if not repeats:
        return {"error": "No repeat boundaries found via NVTX"}

    # Build IntervalIndex objects (encapsulated — no array mismatch possible)
    api_index = U.IntervalIndex(cuda_apis, key_start="start_ns", key_end="end_ns")
    gpu_index = U.IntervalIndex(gpu_activities, key_start="start_ns", key_end="end_ns")

    sync_records = build_sync_records(cuda_apis, gpu_activities, sync_activities, schema)

    # ---- Map NVTX window_id → display repeat_id (1-indexed) ----
    wid_to_rid: dict[int, int] = {}
    for w in windows:
        if w.phase == "full_request":
            for rep in repeats:
                if (w.start_ns <= rep["full_request"][0]
                        and w.end_ns >= rep["full_request"][1]):
                    wid_to_rid[w.window_id] = rep["request_id"]
                    break

    # Remap ALL objects from raw window_id → normalized repeat_id
    # 1. NVTX windows
    for w in windows:
        if w.request_id >= 0 and w.request_id in wid_to_rid:
            new_rid = wid_to_rid[w.request_id]
            # Walk up to propagate to parent windows that share the same request_id
            w.request_id = new_rid
            w.repeat_id = new_rid

    # 2. CUDA APIs
    for api in cuda_apis:
        if api.request_id >= 0 and api.request_id in wid_to_rid:
            api.request_id = wid_to_rid[api.request_id]
            api.repeat_id = api.request_id

    # 3. GPU activities (inherited from APIs via correlation)
    for ga in gpu_activities:
        if ga.request_id >= 0 and ga.request_id in wid_to_rid:
            ga.request_id = wid_to_rid[ga.request_id]
            ga.repeat_id = ga.request_id

    # 4. Sync records
    for sr in sync_records:
        if sr.request_id >= 0 and sr.request_id in wid_to_rid:
            sr.request_id = wid_to_rid[sr.request_id]
            sr.repeat_id = sr.request_id

    # ---- Compute B ONCE for all canonical syncs ----
    all_b_details = compute_b_for_all_syncs(sync_records, gpu_activities, workload_id)

    # Index B by (request_id, phase) for per-repeat CSV counts
    b_by_req_phase: dict[tuple[int, str], list] = defaultdict(list)
    for bd in all_b_details:
        b_by_req_phase[(bd.request_id, bd.phase)].append(bd)

    phase_names = ["prefill", "decode", "full_request"]
    all_raw = {p: [] for p in phase_names}
    all_a = {p: [] for p in phase_names}
    all_overlap = {p: [] for p in phase_names}
    all_thread = []
    csv_rows = []

    # Compute dominant thread once per repeat, propagate to all phases
    req_thread: dict[int, dict] = {}
    for rep in repeats:
        req_id = rep["request_id"]
        ws, we = rep["full_request"]
        thread_info = find_dominant_thread(cuda_apis, ws, we, api_index=api_index)
        thread_info["request_id"] = req_id
        req_thread[req_id] = thread_info
        all_thread.append(thread_info)

    for ri, rep in enumerate(repeats):
        req_id = rep["request_id"]
        for phase in phase_names:
            pw = rep.get(phase)
            if not pw:
                continue
            ws, we = pw

            raw = compute_raw_stats(cuda_apis, gpu_activities, ws, we,
                                     api_index=api_index, gpu_index=gpu_index)
            all_raw[phase].append(raw)

            a_result, a_intervals = compute_a_layer(
                cuda_apis, gpu_activities, sync_records, ws, we, req_id,
            )
            all_a[phase].append(a_result)

            overlap = compute_overlap_metrics(
                a_result, a_intervals, gpu_activities, ws, we,
            )
            all_overlap[phase].append(overlap)

            # B counts for this repeat×phase (from canonical B results)
            if phase == "full_request":
                # Aggregate prefill + decode syncs for this request
                phase_b = (
                    b_by_req_phase.get((req_id, "prefill"), [])
                    + b_by_req_phase.get((req_id, "decode"), [])
                )
            else:
                phase_b = b_by_req_phase.get((req_id, phase), [])

            sync_supported = len(phase_b)
            b_valid = sum(1 for bd in phase_b if bd.B_valid)
            b_invalid = sync_supported - b_valid
            bv_coverage = (b_valid / sync_supported) if sync_supported > 0 else 0.0
            ir_counts = defaultdict(int)
            for bd in phase_b:
                if bd.invalid_reason:
                    ir_counts[bd.invalid_reason] += 1
            top_ir = max(ir_counts, key=ir_counts.get) if ir_counts else ""

            win_dur_ns = we - ws
            conservation = sum(a_result[f"{cat}_ns"] for cat in [
                "A_host_path", "A_cuda_api", "A_device_wait",
                "A_sync_residual", "A_unattributed",
            ])
            epsilon_ns = max(0, win_dur_ns - conservation)
            cons_err = (epsilon_ns / win_dur_ns * 100) if win_dur_ns > 0 else 0.0

            # Propagate dominant thread to all phases
            dt = req_thread.get(req_id, {})

            row = {
                "workload_id": workload_id, "request_id": req_id, "repeat_id": req_id,
                "phase": phase, "prompt_len": prompt_len, "batch_size": batch_size,
                "output_len": output_len, "gpu_name": gpu_name,
                "window_duration_ms": _ns_to_ms(win_dur_ns),
                "cuda_api_count": raw["cuda_api_count"],
                "cuda_api_union_ms": _ns_to_ms(raw["cuda_api_union_ns"]),
                "launch_api_count": raw["launch_api_count"],
                "sync_api_count": raw["sync_api_count"],
                "kernel_count": raw["kernel_count"],
                "kernel_union_ms": _ns_to_ms(raw["kernel_union_ns"]),
                "memcpy_count": raw["memcpy_count"],
                "memcpy_bytes": raw["memcpy_bytes"],
                "memcpy_union_ms": _ns_to_ms(raw["memcpy_union_ns"]),
                "memset_count": raw["memset_count"],
                "gpu_activity_union_ms": _ns_to_ms(raw["gpu_activity_union_ns"]),
                "gpu_active_ratio": raw["gpu_active_ratio"],
                "distinct_stream_count": raw["distinct_stream_count"],
                "multistream_ratio": raw["multistream_ratio"],
                "A_host_path_ms": _ns_to_ms(a_result["A_host_path_ns"]),
                "A_cuda_api_ms": _ns_to_ms(a_result["A_cuda_api_ns"]),
                "A_device_wait_ms": _ns_to_ms(a_result["A_device_wait_ns"]),
                "A_sync_residual_ms": _ns_to_ms(a_result["A_sync_residual_ns"]),
                "A_unattributed_ms": _ns_to_ms(a_result["A_unattributed_ns"]),
                "A_host_path_pct": round(a_result["A_host_path_ns"] / win_dur_ns * 100, 2) if win_dur_ns > 0 else 0,
                "A_cuda_api_pct": round(a_result["A_cuda_api_ns"] / win_dur_ns * 100, 2) if win_dur_ns > 0 else 0,
                "A_device_wait_pct": round(a_result["A_device_wait_ns"] / win_dur_ns * 100, 2) if win_dur_ns > 0 else 0,
                "A_sync_residual_pct": round(a_result["A_sync_residual_ns"] / win_dur_ns * 100, 2) if win_dur_ns > 0 else 0,
                "A_unattributed_pct": round(a_result["A_unattributed_ns"] / win_dur_ns * 100, 2) if win_dur_ns > 0 else 0,
                "epsilon_ms": _ns_to_ms(epsilon_ns),
                "conservation_error_pct": round(cons_err, 3),
                "api_gpu_overlap_ms": _ns_to_ms(overlap.get("api_gpu_overlap_ns")),
                "O_api_gpu": overlap.get("O_api_gpu"),
                "hostpath_gpu_overlap_ms": _ns_to_ms(overlap.get("hostpath_gpu_overlap_ns")),
                "O_hostpath_gpu": overlap.get("O_hostpath_gpu"),
                "dominant_tid": dt.get("dominant_tid", -1),
                "dominant_api_count_share": dt.get("dominant_api_count_share", 0),
                "dominant_api_time_share": dt.get("dominant_api_time_share", 0),
                "multi_launch_thread_flag": dt.get("multi_launch_thread_flag", False),
                "correlation_coverage": corr_stats.get("correlation_coverage", 0),
                "boundary_valid": True,
                "sync_supported_count": sync_supported,
                "B_valid_count": b_valid, "B_invalid_count": b_invalid,
                "B_valid_coverage": round(bv_coverage, 4),
                "top_invalid_reason": top_ir,
                # Tokens per phase (for ratio-of-sums throughput)
                "tokens_in_phase": (
                    batch_size * prompt_len if phase == "prefill" and prompt_len > 0
                    else batch_size * output_len if phase == "decode" and output_len > 0
                    else batch_size * (prompt_len + output_len) if phase == "full_request" and prompt_len > 0 and output_len > 0
                    else None
                ),
                "ttft_proxy_ms": _ns_to_ms(win_dur_ns)
                    if phase == "prefill" else None,
                "tpot_proxy_ms": _ns_to_ms(win_dur_ns / max(output_len - 1, 1))
                    if phase == "decode" and output_len > 1 else None,
            }
            csv_rows.append(row)

    # ---- Aggregate per-phase ----
    def _aggregate(acc_list, ns_keys, win_dur_list=None):
        if not acc_list:
            return {}
        n = len(acc_list)
        result = {}
        for key in ns_keys:
            vals = [d.get(key, 0) for d in acc_list]
            mean = sum(vals) / n
            # Sample SD (n-1) for n >= 2, null for n == 1
            sdev = U.sample_std(vals) if n >= 2 else None
            base = key[:-3] if key.endswith("_ns") else key
            result[f"{base}_ns_mean"] = round(mean, 1)
            result[f"{base}_ns_std"] = round(sdev, 1) if sdev is not None else None
            result[f"{base}_ms_mean"] = round(mean / 1e6, 3)
            result[f"{base}_ms_std"] = round(sdev / 1e6, 3) if sdev is not None else None
        return result

    a_summary = {}
    overlap_summary_out = {}
    for phase in phase_names:
        a_list = all_a.get(phase, [])
        a_agg = _aggregate(a_list, [
            "A_host_path_ns", "A_cuda_api_ns", "A_device_wait_ns",
            "A_sync_residual_ns", "A_unattributed_ns",
        ])
        if a_list and repeats:
            n = len(a_list)
            win_durs = []
            for ri2, rep2 in enumerate(repeats):
                pw2 = rep2.get(phase)
                if pw2:
                    win_durs.append(pw2[1] - pw2[0])
            avg_win = sum(win_durs) / n if win_durs and n > 0 else 1
            for cat in A_CATEGORIES:
                mk = f"{cat}_ns_mean"
                if mk in a_agg:
                    a_agg[f"{cat}_pct_mean"] = round(
                        a_agg[mk] / avg_win * 100, 2
                    ) if avg_win > 0 else 0.0
        a_summary[phase] = a_agg

        ov_list = all_overlap.get(phase, [])
        ov_agg = {}
        if ov_list:
            n = len(ov_list)
            for key in ["O_api_gpu", "O_hostpath_gpu"]:
                vals = [d.get(key) for d in ov_list if d.get(key) is not None]
                if vals:
                    ov_agg[f"{key}_mean"] = round(sum(vals) / len(vals), 4)
        overlap_summary_out[phase] = ov_agg

    # B summary (aggregates across ALL repeats, count-weighted)
    b_summary_out = {}
    for phase in phase_names:
        if phase == "full_request":
            # Aggregate prefill + decode
            phase_b_details = [
                bd for bd in all_b_details
                if bd.phase in ("prefill", "decode")
            ]
        else:
            phase_b_details = [bd for bd in all_b_details if bd.phase == phase]
        # Count-weighted B_valid_coverage
        total_s = len(phase_b_details)
        total_v = sum(1 for bd in phase_b_details if bd.B_valid)
        b_summary_out[phase] = {
            "total_syncs": total_s,
            "valid_wait_sets": sum(1 for bd in phase_b_details if bd.wait_set_valid),
            "B_valid": total_v,
            "B_invalid": total_s - total_v,
            "B_valid_coverage": round(total_v / total_s, 4) if total_s > 0 else 0.0,
        }

    # ---- Raw summary: phase-level mean/std across repeats ----
    def _raw_summary_for_phase(raw_list, ns_keys):
        if not raw_list:
            return {}
        n = len(raw_list)
        result = {}
        for key in ns_keys:
            vals = [d.get(key) for d in raw_list if d.get(key) is not None]
            if not vals:
                result[f"{key}_mean"] = None
                result[f"{key}_std"] = None
                continue
            mean = sum(vals) / n
            sdev = U.sample_std(vals) if n >= 2 else None
            result[f"{key}_mean"] = round(mean, 4)
            result[f"{key}_std"] = round(sdev, 4) if sdev is not None else None
        return result

    raw_ns_keys = [
        "cuda_api_union_ns", "kernel_union_ns", "memcpy_union_ns",
        "memset_union_ns", "gpu_activity_union_ns",
    ]
    raw_scalar_keys = [
        "cuda_api_count", "launch_api_count", "sync_api_count",
        "kernel_count", "distinct_kernel_name_count", "distinct_stream_count",
        "memcpy_count", "memcpy_bytes", "memset_count", "memset_bytes",
        "gpu_active_ratio", "multistream_ratio",
    ]
    raw_summary_out = {}
    for phase in phase_names:
        raw_list = all_raw.get(phase, [])
        if not raw_list:
            continue
        # Compute window_duration from raw (it's not stored directly)
        win_durs = []
        for ri2, rep2 in enumerate(repeats):
            if ri2 < len(raw_list):
                pw2 = rep2.get(phase)
                if pw2:
                    win_durs.append(pw2[1] - pw2[0])
        phase_raw = {}
        phase_raw["window_duration_ms_mean"] = round(sum(win_durs) / len(win_durs) / 1e6, 3) if win_durs else None
        phase_raw["window_duration_ms_std"] = round(U.sample_std([w / 1e6 for w in win_durs]), 3) if len(win_durs) >= 2 else None
        # NS-valued keys → convert to ms, strip _ns suffix
        for key in raw_ns_keys:
            vals = [d.get(key) for d in raw_list if d.get(key) is not None]
            if vals:
                ms_vals = [v / 1e6 for v in vals]
                mean = sum(ms_vals) / len(vals)
                sdev = U.sample_std(ms_vals) if len(ms_vals) >= 2 else None
                base = key[:-3] if key.endswith("_ns") else key  # strip _ns
                phase_raw[f"{base}_ms_mean"] = round(mean, 3)
                phase_raw[f"{base}_ms_std"] = round(sdev, 3) if sdev is not None else None
        # Scalar keys
        for key in raw_scalar_keys:
            vals = [d.get(key) for d in raw_list if d.get(key) is not None]
            if vals:
                mean = sum(vals) / len(vals)
                sdev = U.sample_std(vals) if len(vals) >= 2 else None
                phase_raw[f"{key}_mean"] = round(mean, 3)
                phase_raw[f"{key}_std"] = round(sdev, 3) if sdev is not None else None
        raw_summary_out[phase] = phase_raw

    # Trace quality
    invalid_counts = defaultdict(int)
    for bd in all_b_details:
        if bd.invalid_reason:
            invalid_counts[bd.invalid_reason] += 1

    trace_quality = {
        "schema_version": schema.get("schema_version", "unknown"),
        "nsys_product_version": schema.get("nsys_product_version", "unknown"),
        "available_tables": schema.get("all_tables", []),
        "missing_optional_tables": schema.get("missing_optional", []),
        "request_count": len(repeats), "repeat_count": len(repeats),
        "boundary_coverage": round(len(repeats) / max(1, len([w for w in windows if w.phase == "full_request"])), 4),
        "correlation_coverage": corr_stats.get("correlation_coverage", 0),
        "dominant_thread_coverage": round(
            sum(1 for t in all_thread if not t.get("multi_launch_thread_flag", True)) / max(1, len(all_thread)), 4
        ),
        "dropped_records_status": "unknown",
        "conservation_error_max": max((abs(r.get("conservation_error_pct", 0)) for r in csv_rows), default=0.0),
        "unattributed_pct_max": max((r.get("A_unattributed_pct", 0) for r in csv_rows), default=0.0),
        "B_valid_coverage": round(
            sum(1 for bd in all_b_details if bd.B_valid) / max(1, len(all_b_details)), 4
        ),
        "invalid_reason_counts": dict(invalid_counts),
        "warnings": schema.get("missing_optional", []),
        "fatal_errors": schema.get("critical_missing", []),
        "global_api_assignment_coverage": round(
            sum(1 for a in cuda_apis if a.phase) / max(1, len(cuda_apis)), 4
        ),
        "in_request_api_assignment_coverage": round(
            _compute_in_request_api_coverage(cuda_apis, repeats, api_index), 4
        ),
    }

    return {
        "metadata": {
            "metric_definition_version": U.METRIC_VERSION,
            "parser_version": U.METRIC_VERSION,
            "workload_id": workload_id, "gpu_name": gpu_name,
            "schema_version": schema.get("schema_version", "unknown"),
            "nsys_product_version": schema.get("nsys_product_version", "unknown"),
            "prompt_len": prompt_len, "batch_size": batch_size, "output_len": output_len,
            "git_commit": _get_git_commit(),
            "generation_timestamp": _utc_now_iso(),
        },
        "trace_quality": trace_quality,
        "raw_summary": raw_summary_out,
        "A_summary": a_summary,
        "overlap_summary": overlap_summary_out,
        "B_summary": b_summary_out,
        "repeat_results": csv_rows,
        "b_sync_details": all_b_details,
        "legacy_compatibility": {
            "legacy_removed_fields": [
                "A_device_compute", "A_memory_transfer", "A_submit", "A_host_runtime",
                "b_exposed_ms", "b_self_block_ms", "b_kernel_block_ms",
                "b_memory_block_ms", "b_device_gap_ms", "b_top_motif",
                "exposed_total_ms", "hidden_total_ms",
            ],
        },
    }


# ---------------------------------------------------------------------------
# 13. CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Exposed Latency Accounting v2")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--sqlite", help="Path to .sqlite file")
    src.add_argument("--csv-dir", help="Directory with parsed CSVs (legacy)")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--workload-id", default=None)
    parser.add_argument("--gpu-name", default="")
    parser.add_argument("--prompt-len", type=int, default=0)
    parser.add_argument("--batch-size", type=int, default=0)
    parser.add_argument("--output-len", type=int, default=0)
    parser.add_argument("--legacy-output", action="store_true")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[accounting v2] Input: {args.sqlite or args.csv_dir}")
    print(f"[accounting v2] Output: {out_dir.resolve()}")

    if args.sqlite:
        nvtx_raw, cuda_apis, gpu_activities, sync_activities, schema = \
            load_events_from_sqlite(args.sqlite)
    else:
        print("[accounting v2] CSV input not supported in v2")
        sys.exit(1)

    # Parse workload ID from filename
    sqlite_path = Path(args.sqlite)
    wl_info = U.parse_workload_id(args.workload_id or sqlite_path.stem)
    workload_id = args.workload_id or wl_info["workload_id"]
    prompt_len = args.prompt_len or wl_info["prompt_len"]
    batch_size = args.batch_size or wl_info["batch_size"]
    output_len = args.output_len or wl_info["output_len"]

    # Resolve GPU name: CLI arg → SQLite metadata → path inference → None
    gpu_name = args.gpu_name or ""
    if not gpu_name and args.sqlite:
        conn2 = U.open_readonly_sqlite(str(sqlite_path))
        cur2 = conn2.cursor()
        gpu_name = U.resolve_gpu_name(str(sqlite_path), cur2) or ""
        conn2.close()
    if not gpu_name:
        gpu_name = None  # null in JSON

    git_commit = _get_git_commit()
    print(f"  Workload: {workload_id} (p{prompt_len}_b{batch_size}_o{output_len})")
    print(f"  GPU: {gpu_name or 'unknown'}")
    if git_commit:
        print(f"  Git commit: {git_commit}")

    print("\n[accounting v2] Computing exposed accounting...")
    result = compute_exposed_accounting_v2(
        nvtx_raw, cuda_apis, gpu_activities, sync_activities, schema,
        workload_id=workload_id, gpu_name=gpu_name,
        prompt_len=prompt_len, batch_size=batch_size, output_len=output_len,
    )

    if "error" in result:
        print(f"[accounting v2] ERROR: {result['error']}")
        sys.exit(1)

    print("\n[accounting v2] Writing outputs...")
    write_accounting_result(out_dir, result["metadata"], result["trace_quality"],
                            result["raw_summary"], result["A_summary"],
                            result["overlap_summary"], result["B_summary"],
                            result["repeat_results"], result.get("b_sync_details", []),
                            result.get("legacy_compatibility", {}))
    write_accounting_summary_csv(out_dir, result["repeat_results"])
    write_b_sync_detail_csv(out_dir, result["b_sync_details"])

    # Console summary
    print(f"\n{'='*60}")
    print(f"[accounting v2] ACCOUNTING COMPLETE")
    print(f"  Metric version: {U.METRIC_VERSION}")
    print(f"  Schema version: {schema.get('schema_version', 'unknown')}")
    print(f"  Nsight Systems: {schema.get('nsys_product_version', 'unknown')}")
    print(f"  GPU: {gpu_name or 'unknown'}")

    bd_list = result["b_sync_details"]
    unique_uids = len(set(bd.physical_sync_uid for bd in bd_list))
    dup_count = len(bd_list) - unique_uids
    print(f"  Physical syncs (B detail rows): {len(bd_list)}")
    print(f"  Unique physical_sync_uid: {unique_uids}")
    print(f"  Duplicates: {dup_count}")
    print(f"  B valid: {sum(1 for bd in bd_list if bd.B_valid)} / {len(bd_list)}")

    # Per-repeat B counts
    from collections import Counter as _Counter
    req_b_counts = _Counter()
    for bd in bd_list:
        if bd.phase in ("prefill", "decode"):
            req_b_counts[(bd.request_id, bd.phase)] += 1
    request_ids = sorted(set(bd.request_id for bd in bd_list))
    for rid in request_ids:
        pf = req_b_counts.get((rid, "prefill"), 0)
        dc = req_b_counts.get((rid, "decode"), 0)
        print(f"  repeat {rid}: prefill={pf}, decode={dc}, full={pf + dc}")

    # Ownership stats
    total_own = sum(1 for bd in bd_list if bd.terminal_ownership_valid)
    total_ext = sum(bd.wait_set_external_count or 0 for bd in bd_list)
    total_unass = sum(bd.wait_set_unassigned_count or 0 for bd in bd_list)
    total_cross = sum(1 for bd in bd_list if bd.cross_phase_wait_flag)
    print(f"  Terminal ownership valid: {total_own} / {len(bd_list)}")
    print(f"  Wait-set external activities: {total_ext}")
    print(f"  Wait-set unassigned activities: {total_unass}")
    print(f"  Cross-phase terminals: {total_cross}")

    # B_summary
    bs = result["B_summary"]
    for phase in ["prefill", "decode", "full_request"]:
        p = bs.get(phase, {})
        if p:
            print(f"  B_summary.{phase}: total={p['total_syncs']} valid={p['B_valid']} invalid={p['B_invalid']}")

    # raw_summary non-empty check
    rs = result.get("raw_summary", {})
    print(f"  raw_summary non-empty: {any(rs.values())}")

    for phase in ["prefill", "decode", "full_request"]:
        a = result["A_summary"].get(phase, {})
        if not a:
            continue
        print(f"\n  {phase.upper()}:")
        for cat in A_CATEGORIES:
            ms_key = f"{cat}_ms_mean"
            pct_key = f"{cat}_pct_mean"
            if ms_key in a and a[ms_key] is not None:
                print(f"    {cat:<25s} {a[ms_key]:>8.3f} ms  ({a.get(pct_key, 0):>5.1f} %)")
    any_residual = any(
        (a.get("A_sync_residual_ms_mean") or 0) > 0
        for a in result["A_summary"].values()
    )
    print(f"\n  A_sync_residual > 0: {'YES' if any_residual else 'NO (BUG)'}")
    print(f"{'='*60}")

    # Debug: RAW_B per-activity query-chain trace
    if args.debug and result.get("b_sync_details"):
        # Rebuild phase windows from the raw data for tracing
        windows = build_nvtx_windows(nvtx_raw)
        repeats = build_repeat_phases(windows)
        _debug_raw_b_consistency(result, gpu_activities, repeats)

    if args.legacy_output:
        _write_legacy(out_dir, result)

    # Return all results for verification
    return result


def _debug_raw_b_consistency(result, gpu_activities, repeats):
    """Per-activity query-chain trace for --debug mode.

    For each memcpy terminal, traces the full path:
    activity_id → global index → IntervalIndex.query(ws, we) → candidates → final filter.
    """
    gpu_map = {g.activity_id: g for g in gpu_activities}
    bd_list = result.get("b_sync_details", [])

    # Build IntervalIndex on the full GPU activity list
    gpu_index = U.IntervalIndex(gpu_activities, key_start="start_ns", key_end="end_ns")

    # Build global position lookup: activity_id → position in gpu_activities
    global_pos = {g.activity_id: i for i, g in enumerate(gpu_activities)}

    # Build repeat×phase window lookup
    phase_windows: dict[tuple[int, str], tuple[int, int]] = {}
    for rep in repeats:
        rid = rep["request_id"]
        for ph in ["prefill", "decode", "full_request"]:
            pw = rep.get(ph)
            if pw:
                phase_windows[(rid, ph)] = pw

    print(f"\n[debug] ===== PER-ACTIVITY QUERY-CHAIN TRACE =====")
    print(f"[debug] GPU activities total: {len(gpu_activities)}")
    print(f"[debug] Index objects count: {len(gpu_index.objects)}")
    print(f"[debug] Repeats: {len(repeats)}")

    inconsistencies = 0

    for bd in bd_list:
        if not bd.B_valid or bd.terminal_activity_id < 0:
            continue
        terminal = gpu_map.get(bd.terminal_activity_id)
        if terminal is None:
            continue
        if bd.terminal_type != "memcpy":
            continue

        rid = bd.request_id
        phase = bd.phase

        # Global position
        gpos = global_pos.get(terminal.activity_id, -1)
        in_global = terminal in gpu_activities

        # Find position in index.objects
        idx_pos = -1
        for i, obj in enumerate(gpu_index.objects):
            if obj.activity_id == terminal.activity_id:
                idx_pos = i
                break

        # Check if activity is in gpu_activities but NOT in index.objects
        in_index = idx_pos >= 0

        print(f"\n[debug] ── memcpy terminal #{bd.sync_id} "
              f"uid={bd.physical_sync_uid} ──")
        print(f"  repeat={rid}  phase={phase}")
        print(f"  activity_id={terminal.activity_id}")
        print(f"  global_pos={gpos}  in_global_list={in_global}")
        print(f"  index_pos={idx_pos}  in_index_objects={in_index}")

        # Show raw activity timing
        print(f"  activity: start={terminal.start_ns} end={terminal.end_ns} "
              f"corr={terminal.correlation_id} req={terminal.request_id} "
              f"phase={terminal.phase} stream={terminal.stream_id}")

        # Query prefill window
        pf_win = phase_windows.get((rid, "prefill"))
        fr_win = phase_windows.get((rid, "full_request"))

        for win_label, (ws, we) in [("prefill", pf_win) if pf_win else (None, None),
                                      ("full_request", fr_win) if fr_win else (None, None)]:
            if win_label is None:
                continue

            # Manual trace: replicate IntervalIndex.query()
            starts = gpu_index._starts
            pmax = gpu_index._prefix_max_ends
            lo = bisect.bisect_right(pmax, ws)
            hi = bisect.bisect_left(starts, we)

            in_candidates = lo <= gpos < hi if gpos >= 0 else False
            overlaps = (
                terminal.end_ns > ws and terminal.start_ns < we
            )

            # Check if terminal is in the candidate slice
            candidate_slice = list(gpu_index.objects[lo:hi])
            in_slice = terminal in candidate_slice

            # Check manual overlap
            print(f"  [{win_label}] ws={ws} we={we} dur_ms={(we-ws)/1e6:.3f}")
            print(f"    lo={lo} hi={hi}  gpos_in_range[{lo}:{hi}]={in_candidates}")
            print(f"    in_candidate_slice={in_slice}")
            print(f"    overlap: end({terminal.end_ns})>ws({ws})={terminal.end_ns > ws}  "
                  f"start({terminal.start_ns})<we({we})={terminal.start_ns < we}")
            print(f"    → overlaps_window={overlaps}")

            if overlaps and not in_slice:
                print(f"    *** INCONSISTENCY: overlaps but not in query candidates! ***")
                inconsistencies += 1
                # Show nearby objects
                lo_safe = max(0, lo - 2)
                hi_safe = min(len(gpu_index.objects), hi + 2)
                print(f"    nearby objects [{lo_safe}:{hi_safe}]:")
                for i in range(lo_safe, hi_safe):
                    obj = gpu_index.objects[i]
                    print(f"      [{i}] id={obj.activity_id} "
                          f"start={obj.start_ns} end={obj.end_ns} "
                          f"type={obj.activity_type}")

            if not overlaps and in_slice:
                print(f"    Note: in candidates but filtered out (correct for strict overlap)")

    print(f"\n[debug] RAW_B_INTERVAL_INCONSISTENCY count: {inconsistencies}"
          f"{' ✓' if inconsistencies == 0 else ' ✗'}")


def _write_legacy(out_dir, result):
    """Legacy output (opt-in)."""
    import csv as _csv
    path = out_dir / "a_metrics_summary.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = _csv.writer(f)
        w.writerow(["phase", "category", "latency_ms_mean", "latency_ms_std", "pct_of_phase"])
        for phase in ["prefill", "decode", "full_request"]:
            a = result["A_summary"].get(phase, {})
            if not a:
                continue
            for cat in A_CATEGORIES:
                w.writerow([phase, cat,
                            a.get(f"{cat}_ms_mean", 0),
                            a.get(f"{cat}_ms_std", 0),
                            a.get(f"{cat}_pct_mean", 0)])
    print(f"  → {path} (legacy)")


if __name__ == "__main__":
    main()
