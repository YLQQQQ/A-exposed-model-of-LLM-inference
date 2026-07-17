#!/usr/bin/env python3
"""
Internal utility module for exposed accounting analysis (v2).

Dataclasses, interval utilities, schema inspection, and helpers.
Not intended for direct CLI use.
"""

from __future__ import annotations

import bisect
import math
import os
import re
import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field, fields
from typing import Optional, Union

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------

TERMINAL_TOLERANCE_NS = 1000          # 1 µs — MULTI_TERMINAL threshold
TIMESTAMP_TOLERANCE_NS = 20_000       # 20 µs — negative tail tolerance
METRIC_VERSION = "exposedpath-v2"

# Workload ID parsing regex: wNN_pNNN_bN_oNN
WORKLOAD_ID_RE = re.compile(
    r"w\d+_p(?P<prompt>\d+)_b(?P<batch>\d+)_o(?P<output>\d+)"
)

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class NvtxWindow:
    """NVTX range window with full hierarchy information."""
    window_id: int
    request_id: int
    repeat_id: int
    phase: str
    token_idx: int = -1
    start_ns: int = 0
    end_ns: int = 0
    global_tid: int = 0
    parent_window_id: int = -1
    depth: int = 0


@dataclass
class CudaApi:
    """CUDA API call event."""
    api_id: int
    name: str
    start_ns: int
    end_ns: int
    global_tid: int = 0
    correlation_id: int = -1
    return_value: int = 0
    request_id: int = -1
    repeat_id: int = -1
    phase: str = ""
    token_idx: int = -1
    is_explicit_sync: bool = False
    sync_type: str = ""
    event_id: int = -1
    stream_id: int = -1
    process_id: int = 0
    thread_id: int = 0


@dataclass
class GpuActivity:
    """GPU activity (kernel, memcpy, memset)."""
    activity_id: int
    activity_type: str
    name: str
    start_ns: int
    end_ns: int
    device_id: int = 0
    context_id: int = 0
    stream_id: int = 0
    correlation_id: int = -1
    submit_api_id: int = -1
    submit_end_ns: int = 0
    request_id: int = -1
    repeat_id: int = -1
    phase: str = ""
    token_idx: int = -1
    bytes_val: Optional[int] = None
    copy_kind: str = ""


@dataclass
class SyncActivity:
    """CUPTI_ACTIVITY_KIND_SYNCHRONIZATION record."""
    sync_activity_id: int
    start_ns: int = 0
    end_ns: int = 0
    correlation_id: int = -1
    sync_type_id: int = -1
    device_id: int = 0
    context_id: int = 0
    stream_id: int = -1
    event_id: int = -1
    event_sync_id: int = -1


@dataclass
class SyncRecord:
    """S-layer sync semantic record."""
    sync_id: int
    sync_api_id: int
    sync_type: str
    sync_api_name: str = ""
    start_ns: int = 0
    end_ns: int = 0
    device_id: int = 0
    context_id: int = 0
    stream_id: int = -1
    event_id: int = -1
    event_sync_id: int = -1
    correlation_id: int = -1
    request_id: int = -1
    repeat_id: int = -1
    phase: str = ""
    token_idx: int = -1
    physical_sync_uid: str = ""
    wait_set_valid: bool = False
    invalid_reason: str = ""
    wait_activity_ids: list[int] = field(default_factory=list)
    terminal_activity_id: int = -1
    terminal_end_ns: int = 0
    B_valid: bool = False
    B_invalid_reason: str = ""


@dataclass
class AIntervals:
    """A-layer per-category intervals (for overlap computation)."""
    host_path: list[tuple[int, int]] = field(default_factory=list)
    cuda_api: list[tuple[int, int]] = field(default_factory=list)
    device_wait: list[tuple[int, int]] = field(default_factory=list)
    sync_residual: list[tuple[int, int]] = field(default_factory=list)
    unattributed: list[tuple[int, int]] = field(default_factory=list)


@dataclass
class BSyncDetail:
    """B-layer per-sync diagnostic result."""
    workload_id: str = ""
    physical_sync_uid: str = ""
    sync_id: int = 0
    request_id: int = 0
    repeat_id: int = 0
    phase: str = ""
    token_idx: int = -1
    sync_api_correlation_id: int = -1
    sync_api_name: str = ""
    sync_type: str = ""
    sync_start_ns: int = 0
    sync_end_ns: int = 0
    sync_duration_ms: float = 0.0
    context_id: int = 0
    stream_id: int = -1
    wait_set_valid: bool = False
    B_valid: bool = False
    invalid_reason: str = ""
    wait_set_size: int = 0
    wait_set_unassigned_count: int = 0
    wait_set_external_count: int = 0
    terminal_activity_id: int = -1
    terminal_type: str = ""
    terminal_name: str = ""
    terminal_request_id: int = -1
    terminal_repeat_id: int = -1
    terminal_phase: str = ""
    terminal_api_correlation_id: int = -1
    terminal_ownership_valid: bool = False
    cross_phase_wait_flag: bool = False
    terminal_stream_id: int = -1
    terminal_submit_end_ns: int = 0
    terminal_start_ns: int = 0
    terminal_end_ns: int = 0
    B_predecessor_ms: Optional[float] = None
    B_stream_gap_ms: Optional[float] = None
    B_self_ms: Optional[float] = None
    sync_return_tail_ms: Optional[float] = None
    sync_return_tail_raw_ns: Optional[int] = None
    device_overlap_with_sync_ms: Optional[float] = None
    timestamp_tolerance_applied: bool = False


@dataclass
class TraceQuality:
    """Trace quality assessment."""
    schema_version: str = "unknown"
    nsys_product_version: str = "unknown"
    available_tables: list[str] = field(default_factory=list)
    missing_optional_tables: list[str] = field(default_factory=list)
    request_count: int = 0
    repeat_count: int = 0
    boundary_coverage: float = 0.0
    correlation_coverage: float = 0.0
    dominant_thread_coverage: float = 0.0
    dropped_records_status: str = "unknown"
    conservation_error_max: float = 0.0
    unattributed_pct_max: float = 0.0
    B_valid_coverage: float = 0.0
    invalid_reason_counts: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    fatal_errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Invalid reason enum (unified)
# ---------------------------------------------------------------------------

INVALID_REASONS = [
    "NO_SYNC_RECORD",
    "MISSING_STREAM_ID",
    "MISSING_CONTEXT_ID",
    "MISSING_EVENT_MAP",
    "MISSING_CORRELATION",
    "DROPPED_TRACE_RECORDS",
    "NO_PENDING_ACTIVITY",
    "EXTERNAL_ACTIVITY",
    "UNSUPPORTED_SYNC_TYPE",
    "UNSUPPORTED_EVENT_DEPENDENCY",
    "TRACE_ORDERING_ERROR",
    "MULTI_TERMINAL",
]

# Sync API name patterns
SYNC_KEYWORDS = ("Synchronize", "Sync")

STREAM_SYNC_NAMES = (
    "cudaStreamSynchronize", "cuStreamSynchronize",
    "cudaStreamSynchronize_v", "cuStreamSynchronize_v",
)

DEVICE_SYNC_NAMES = (
    "cudaDeviceSynchronize", "cuCtxSynchronize",
    "cudaDeviceSynchronize_v", "cuCtxSynchronize_v",
)

EVENT_SYNC_NAMES = (
    "cudaEventSynchronize", "cuEventSynchronize",
    "cudaEventSynchronize_v", "cuEventSynchronize_v",
)

# Known NVTX phase names
NVTX_FULL_REQUEST = "full_request"
NVTX_PREFILL = "prefill"
NVTX_DECODE = "decode"
NVTX_DECODE_STEP_PREFIX = "decode_step_"
NVTX_PREPARE_INPUT = "prepare_input"


def is_sync_api(name: str) -> bool:
    """Check if a CUDA API name indicates a synchronization primitive."""
    for kw in SYNC_KEYWORDS:
        if kw in name:
            return True
    return False


def classify_sync_type(name: str) -> str:
    """Classify sync API into 'stream', 'device', 'event', or 'unknown'."""
    for n in STREAM_SYNC_NAMES:
        if n in name:
            return "stream"
    for n in DEVICE_SYNC_NAMES:
        if n in name:
            return "device"
    for n in EVENT_SYNC_NAMES:
        if n in name:
            return "event"
    if "Stream" in name and "Synchronize" in name:
        return "stream"
    if "Device" in name and "Synchronize" in name:
        return "device"
    if "Event" in name and "Synchronize" in name:
        return "event"
    if "Ctx" in name and "Synchronize" in name:
        return "device"
    return "unknown"


def sample_std(values: list[float]) -> Optional[float]:
    """Sample standard deviation (divide by n-1). Returns None if n < 2."""
    n = len(values)
    if n < 2:
        return None
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / (n - 1)
    return math.sqrt(variance)


def population_std(values: list[float]) -> Optional[float]:
    """Population standard deviation (divide by n)."""
    n = len(values)
    if n < 1:
        return None
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n
    return math.sqrt(variance)


def parse_workload_id(name: str) -> dict:
    """Parse wNN_pNNN_bN_oNN pattern from workload directory/file name."""
    m = WORKLOAD_ID_RE.search(name)
    if m:
        return {
            "workload_id": m.group(0),
            "prompt_len": int(m.group("prompt")),
            "batch_size": int(m.group("batch")),
            "output_len": int(m.group("output")),
        }
    return {"workload_id": name, "prompt_len": 0, "batch_size": 0, "output_len": 0}


# ---------------------------------------------------------------------------
# Interval utility functions — all O(N log N) or O(N+M)
# ---------------------------------------------------------------------------


def merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Merge overlapping intervals.  O(N log N)."""
    if not intervals:
        return []
    sorted_iv = sorted(intervals, key=lambda x: x[0])
    merged = [[sorted_iv[0][0], sorted_iv[0][1]]]
    for s, e in sorted_iv[1:]:
        if s <= merged[-1][1]:
            if e > merged[-1][1]:
                merged[-1][1] = e
        else:
            merged.append([s, e])
    return [(s, e) for s, e in merged]


def union_duration(intervals: list[tuple[int, int]]) -> int:
    """Total wall-clock duration covered by interval union.  O(N log N)."""
    return sum(e - s for s, e in merge_intervals(intervals))


def intersect_intervals(
    a: list[tuple[int, int]], b: list[tuple[int, int]]
) -> list[tuple[int, int]]:
    """Intersection of two pre-sorted, non-overlapping interval lists.  O(len(a)+len(b))."""
    result = []
    i = j = 0
    while i < len(a) and j < len(b):
        s = max(a[i][0], b[j][0])
        e = min(a[i][1], b[j][1])
        if s < e:
            result.append((s, e))
        if a[i][1] < b[j][1]:
            i += 1
        else:
            j += 1
    return result


def overlap_duration(
    a: list[tuple[int, int]], b: list[tuple[int, int]]
) -> int:
    """Total overlap duration between two sets of intervals."""
    return sum(e - s for s, e in intersect_intervals(a, b))


def subtract_intervals(
    base: list[tuple[int, int]], remove: list[tuple[int, int]]
) -> list[tuple[int, int]]:
    """Subtract remove from base (all pre-merged, sorted).  O(len(base)+len(remove))."""
    result = []
    ri = 0
    for bs, be in base:
        current = bs
        while ri < len(remove) and remove[ri][1] <= current:
            ri += 1
        while current < be:
            if ri >= len(remove) or remove[ri][0] >= be:
                result.append((current, be))
                current = be
                break
            rs, re = remove[ri]
            if rs > current:
                result.append((current, min(rs, be)))
                current = min(rs, be)
            current = max(current, re)
            ri += 1
    return result


def intersect_one(base: tuple[int, int], other: tuple[int, int]) -> Optional[tuple[int, int]]:
    """Intersection of two single intervals."""
    s = max(base[0], other[0])
    e = min(base[1], other[1])
    return (s, e) if s < e else None


# ---------------------------------------------------------------------------
# Schema inspection helpers
# ---------------------------------------------------------------------------

NVTX_TABLE_CANDIDATES = ["NVTX_EVENTS", "nvtx_events", "NvtxEvents", "nvtx"]
CUPTI_RUNTIME_CANDIDATES = [
    "CUPTI_ACTIVITY_KIND_RUNTIME", "cupti_activity_kind_runtime",
    "CUDA_API_EVENTS", "cuda_api_events", "CudaApiEvents",
]
CUPTI_KERNEL_CANDIDATES = [
    "CUPTI_ACTIVITY_KIND_KERNEL", "cupti_activity_kind_kernel",
    "GPU_KERNELS", "gpu_kernels", "Kernel", "kernel",
]
CUPTI_MEMCPY_CANDIDATES = [
    "CUPTI_ACTIVITY_KIND_MEMCPY", "cupti_activity_kind_memcpy",
    "Memcpy", "memcpy", "MEMCPY",
]
CUPTI_MEMSET_CANDIDATES = [
    "CUPTI_ACTIVITY_KIND_MEMSET", "cupti_activity_kind_memset",
    "Memset", "memset", "MEMSET",
]
CUPTI_SYNC_CANDIDATES = [
    "CUPTI_ACTIVITY_KIND_SYNCHRONIZATION",
    "cupti_activity_kind_synchronization", "SYNCHRONIZATION",
]
CUPTI_EVENT_CANDIDATES = [
    "CUPTI_ACTIVITY_KIND_CUDA_EVENT", "cupti_activity_kind_cuda_event", "CUDA_EVENT",
]
STRING_TABLE_CANDIDATES = [
    "StringIds", "StringTable", "STRING_TABLE", "string_table", "String", "string",
]
ENUM_SYNC_TYPE_CANDIDATES = ["ENUM_CUPTI_SYNC_TYPE", "enum_cupti_sync_type"]
THREAD_NAMES_CANDIDATES = ["ThreadNames", "thread_names", "THREAD_NAMES"]
META_TABLE_CANDIDATES = ["META_DATA_EXPORT", "meta_data_export"]


def find_table(cursor: sqlite3.Cursor, candidates: list[str]) -> Optional[str]:
    """Return the first matching table name, case-insensitive."""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing = {row[0] for row in cursor.fetchall()}
    for cand in candidates:
        if cand in existing:
            return cand
        cand_lower = cand.lower()
        for ex in existing:
            if ex.lower() == cand_lower:
                return ex
    return None


def get_table_columns(cursor: sqlite3.Cursor, table_name: str) -> list[str]:
    """Return column names for a table."""
    cursor.execute(f"PRAGMA table_info('{table_name}')")
    return [row[1] for row in cursor.fetchall()]


def col_map_from_columns(columns: list[str]) -> dict[str, str]:
    """Return {lowercase_name: actual_name} dict."""
    return {c.lower(): c for c in columns}


def pick_col(col_map_: dict[str, str], *keys: str) -> Optional[str]:
    """Return the actual column name matching one of the keys."""
    for k in keys:
        if k.lower() in col_map_:
            return col_map_[k.lower()]
    return None


def read_meta_export(cursor: sqlite3.Cursor) -> dict[str, str]:
    """Read all key-value pairs from META_DATA_EXPORT(name, value)."""
    meta_table = find_table(cursor, META_TABLE_CANDIDATES)
    if not meta_table:
        return {}
    cols = get_table_columns(cursor, meta_table)
    cm = col_map_from_columns(cols)
    name_col = pick_col(cm, "name", "key", "property")
    val_col = pick_col(cm, "value", "val")
    if not name_col or not val_col:
        # Try first two columns
        if len(cols) >= 2:
            name_col, val_col = cols[0], cols[1]
        else:
            return {}
    result = {}
    try:
        cursor.execute(f'SELECT "{name_col}", "{val_col}" FROM "{meta_table}"')
        for row in cursor.fetchall():
            result[str(row[0])] = str(row[1]) if row[1] is not None else ""
    except sqlite3.OperationalError:
        pass
    return result


def inspect_schema(cursor: sqlite3.Cursor) -> dict:
    """Inspect the nsys SQLite schema and return adapter information."""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    all_tables = [row[0] for row in cursor.fetchall()]

    result = {
        "all_tables": all_tables,
        "nvtx_table": find_table(cursor, NVTX_TABLE_CANDIDATES),
        "runtime_table": find_table(cursor, CUPTI_RUNTIME_CANDIDATES),
        "kernel_table": find_table(cursor, CUPTI_KERNEL_CANDIDATES),
        "memcpy_table": find_table(cursor, CUPTI_MEMCPY_CANDIDATES),
        "memset_table": find_table(cursor, CUPTI_MEMSET_CANDIDATES),
        "sync_table": find_table(cursor, CUPTI_SYNC_CANDIDATES),
        "event_table": find_table(cursor, CUPTI_EVENT_CANDIDATES),
        "string_table": find_table(cursor, STRING_TABLE_CANDIDATES),
        "enum_sync_type_table": find_table(cursor, ENUM_SYNC_TYPE_CANDIDATES),
        "thread_names_table": find_table(cursor, THREAD_NAMES_CANDIDATES),
        "meta_table": find_table(cursor, META_TABLE_CANDIDATES),
    }

    # Column details for found tables
    result["table_columns"] = {}
    for key, table in result.items():
        if key in ("all_tables", "table_columns"):
            continue
        if table:
            result["table_columns"][table] = get_table_columns(cursor, table)

    # Read META_DATA_EXPORT as key-value pairs
    meta_export = read_meta_export(cursor)
    result["schema_version"] = meta_export.get("EXPORT_SCHEMA_VERSION", "unknown")
    result["nsys_product_version"] = meta_export.get("EXPORT_PRODUCT_VERSION", "unknown")

    # Identify optional tables
    optional_candidates = {
        "memset_table": "memset data unavailable",
        "sync_table": "synchronization table unavailable (CUPTI_ACTIVITY_KIND_SYNCHRONIZATION)",
        "event_table": "CUDA event activity table unavailable",
        "enum_sync_type_table": "sync type enum unavailable",
        "thread_names_table": "thread name resolution unavailable",
    }
    result["missing_optional"] = []
    for key, msg in optional_candidates.items():
        if not result.get(key):
            result["missing_optional"].append(msg)

    # Critical tables
    critical = {
        "nvtx_table": "NVTX_EVENTS — NVTX range data required for phase identification",
    }
    result["critical_missing"] = []
    for key, msg in critical.items():
        if not result.get(key):
            result["critical_missing"].append(msg)

    if not result["string_table"]:
        result["missing_optional"].append("StringIds — name resolution disabled")

    return result


# ---------------------------------------------------------------------------
# String / enum lookup builders
# ---------------------------------------------------------------------------

def build_string_lookup(cursor: sqlite3.Cursor) -> dict[int, str]:
    """Load all strings from StringIds/StringTable into a dictionary."""
    string_table = find_table(cursor, STRING_TABLE_CANDIDATES)
    if not string_table:
        return {}
    cols = get_table_columns(cursor, string_table)
    cm = col_map_from_columns(cols)
    id_col = pick_col(cm, "id", "stringid", "_id_", "rowid")
    val_col = pick_col(cm, "value", "string", "text", "name")
    if not id_col:
        id_col = cols[0]
    if not val_col:
        val_col = cols[1] if len(cols) > 1 else cols[0]
    lookup: dict[int, str] = {}
    try:
        cursor.execute(f'SELECT "{id_col}", "{val_col}" FROM "{string_table}"')
        for row in cursor.fetchall():
            try:
                lookup[int(row[0])] = str(row[1]) if row[1] is not None else ""
            except (ValueError, TypeError):
                pass
    except sqlite3.OperationalError:
        pass
    return lookup


def build_enum_lookup(cursor: sqlite3.Cursor, table_name: str) -> dict[int, str]:
    """Load an enum table (id, name) into a dictionary."""
    if not table_name:
        return {}
    try:
        cols = get_table_columns(cursor, table_name)
        cm = col_map_from_columns(cols)
        id_col = pick_col(cm, "id", "value", "enum_id") or cols[0]
        name_col = pick_col(cm, "name", "label", "enum_name") or (
            cols[1] if len(cols) > 1 else cols[0]
        )
        lookup: dict[int, str] = {}
        cursor.execute(f'SELECT "{id_col}", "{name_col}" FROM "{table_name}"')
        for row in cursor.fetchall():
            try:
                lookup[int(row[0])] = str(row[1]) if row[1] is not None else ""
            except (ValueError, TypeError):
                pass
        return lookup
    except sqlite3.OperationalError:
        return {}


# ---------------------------------------------------------------------------
# Physical sync UID
# ---------------------------------------------------------------------------

def make_physical_sync_uid(
    correlation_id: int, start_ns: int, end_ns: int,
    request_id: int = -1, repeat_id: int = -1,
    sync_type: str = "", stream_id: int = -1, context_id: int = 0,
) -> str:
    """Generate a globally unique physical sync identifier across all repeats.

    Primary key: (correlation_id, start_ns, end_ns).
    Fallback includes request/repeat/sync_type/stream/context for robustness.
    """
    if correlation_id >= 0:
        return f"corr={correlation_id}:start={start_ns}:end={end_ns}"
    return (
        f"req={request_id}:rep={repeat_id}:start={start_ns}:end={end_ns}"
        f":type={sync_type}:stream={stream_id}:ctx={context_id}"
    )


# ---------------------------------------------------------------------------
# GPU name resolution
# ---------------------------------------------------------------------------

GPU_PATH_MAP = {
    "nsys_matrix_4090": "NVIDIA GeForce RTX 4090",
    "4090": "NVIDIA GeForce RTX 4090",
    "nsys_matrix_6000ada": "NVIDIA RTX 6000 Ada Generation",
    "6000ada": "NVIDIA RTX 6000 Ada Generation",
    "6000_ada": "NVIDIA RTX 6000 Ada Generation",
}


def resolve_gpu_name(sqlite_path: str = "", cursor=None) -> Optional[str]:
    """Resolve GPU name with priority: SQLite metadata → path inference → null.

    Args:
        sqlite_path: Path to the .sqlite file (used for path inference).
        cursor: Optional open SQLite cursor for reading metadata tables.

    Returns:
        GPU name string or None.
    """
    # Priority 1: Path inference (nsys_matrix_4090 / nsys_matrix_6000ada)
    if sqlite_path:
        gpu = _infer_gpu_from_path(sqlite_path)
        if gpu:
            return gpu

    # Priority 2: SQLite target metadata
    if cursor is not None:
        gpu = _read_gpu_from_metadata(cursor)
        if gpu:
            return gpu

    return None


def _read_gpu_from_metadata(cursor) -> Optional[str]:
    """Try to read GPU name from TARGET_INFO_GPU or similar tables."""
    target_candidates = [
        "TARGET_INFO_GPU", "target_info_gpu",
        "GPU_INFO", "gpu_info", "DEVICE_INFO", "device_info",
        "CUDADevice", "CUDA_DEVICE",
    ]
    for cand in target_candidates:
        table = find_table(cursor, [cand])
        if not table:
            continue
        try:
            cols = get_table_columns(cursor, table)
            cm = col_map_from_columns(cols)
            name_col = pick_col(cm, "devicename", "device_name", "gpuname", "gpu_name",
                                "productname", "product_name", "name")
            if name_col:
                cursor.execute(f'SELECT "{name_col}" FROM "{table}" LIMIT 1')
                row = cursor.fetchone()
                if row and row[0]:
                    return str(row[0])
        except Exception:
            pass
    return None


def _infer_gpu_from_path(path: str) -> Optional[str]:
    """Infer GPU name from directory path."""
    path_lower = path.lower().replace("\\", "/")
    for key, name in GPU_PATH_MAP.items():
        if key.lower() in path_lower:
            return name
    return None


# ---------------------------------------------------------------------------
# IntervalIndex: encapsulated O(log N + k) interval query
# ---------------------------------------------------------------------------

from typing import Generic, Sequence, TypeVar as _TypeVar

_T = _TypeVar("_T")


class IntervalIndex(Generic[_T]):
    """Immutable interval index with prefix-max-end for O(log N + k) queries.

    Correctness invariant: objects, starts, and prefix_max_ends are all
    derived from the SAME sorted list and share the same index positions.
    This class cannot be constructed with mismatched arrays.
    """

    __slots__ = ("_objects", "_starts", "_prefix_max_ends")

    def __init__(
        self,
        objects: Sequence[_T],
        key_start: str = "start_ns",
        key_end: str = "end_ns",
        sort_key=None,
    ):
        """Build index from a sequence of objects.

        Objects are sorted by start_ns (then end_ns, then activity_id).
        If the input is already sorted, pass sort_key=lambda x: x to skip sort.
        """
        if sort_key is None:
            ordered = tuple(
                sorted(
                    objects,
                    key=lambda obj: (
                        int(getattr(obj, key_start)),
                        int(getattr(obj, key_end)),
                        int(getattr(obj, "activity_id", 0)),
                    ),
                )
            )
        else:
            ordered = tuple(sort_key(obj) for obj in objects) if callable(sort_key) else tuple(objects)

        self._objects = ordered
        _starts: list[int] = []
        _pmax: list[int] = []
        cur_max = 0
        for obj in ordered:
            s = int(getattr(obj, key_start))
            e = int(getattr(obj, key_end))
            _starts.append(s)
            cur_max = max(cur_max, e) if _pmax else e
            _pmax.append(cur_max)
        self._starts: tuple[int, ...] = tuple(_starts)
        self._prefix_max_ends: tuple[int, ...] = tuple(_pmax)

    @property
    def objects(self) -> tuple[_T, ...]:
        return self._objects

    def query(self, window_start: int, window_end: int) -> list[_T]:
        """Return objects overlapping [window_start, window_end).

        Condition: obj.end_ns > window_start AND obj.start_ns < window_end.
        O(log N + k), worst-case O(N) when all objects overlap.
        """
        if window_end <= window_start or not self._objects:
            return []

        # Lower bound via prefix-max-end:
        # prefix_max_ends[i] = max end_ns among objects[0..i].
        # If prefix_max_ends[i] <= window_start, ALL objects[0..i] have
        # end_ns <= window_start → none overlap. First index where
        # prefix_max_ends[i] > window_start is a safe starting point.
        lo = bisect.bisect_right(self._prefix_max_ends, window_start)

        # Upper bound via start_ns:
        # starts[i] >= window_end → object starts at or after window end.
        hi = bisect.bisect_left(self._starts, window_end)

        if lo >= hi:
            return []

        return [
            obj
            for obj in self._objects[lo:hi]
            if getattr(obj, "end_ns") > window_start
            and getattr(obj, "start_ns") < window_end
        ]

    def __len__(self) -> int:
        return len(self._objects)

    def __repr__(self) -> str:
        return f"IntervalIndex(n={len(self._objects)})"


# ---------------------------------------------------------------------------
# Read-only SQLite connection
# ---------------------------------------------------------------------------

def open_readonly_sqlite(path: str) -> sqlite3.Connection:
    """Open SQLite database in read-only mode."""
    uri_path = path.replace("\\", "/")
    if not uri_path.startswith("file:"):
        uri_path = f"file:{uri_path}?mode=ro"
    try:
        conn = sqlite3.connect(uri_path, uri=True)
    except sqlite3.OperationalError:
        conn = sqlite3.connect(path)
    conn.text_factory = lambda b: b.decode("utf-8", errors="replace")
    return conn
