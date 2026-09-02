#!/usr/bin/env python3
"""
Parse nsys SQLite export into structured CSV / JSON files.

Usage:
    python analysis/parse_nsys_sqlite.py --sqlite <path/to/file.sqlite> --output-dir <dir>

Handles version differences in nsys SQLite schema robustly:
  - Lists all tables first (→ tables.json)
  - Tries to parse NVTX ranges, CUDA API calls, GPU kernels, memcpy, OSRT
  - Warns (does NOT crash) if an expected table is missing

Output files:
    tables.json          – list of all tables in the sqlite
    nvtx_ranges.csv      – NVTX push/pop range events
    cuda_api.csv         – CUDA API calls
    gpu_kernels.csv      – GPU kernel launches
    memcpy.csv           – memory copy / memory operations
    osrt.csv             – OS runtime events (if available)
    timeline_summary.json – counts & time range per event type
"""

import argparse
import csv
import json
import os
import sqlite3
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Known table name patterns across nsys versions
# ---------------------------------------------------------------------------
# NVTX:  NVTX_EVENTS, NvtxEvents, nvtx_events, StringTable+NVTX_EVENTS
# CUDA API: CUDA_API_EVENTS, CudaApiEvents, cuda_api_events
# GPU kernels: CUPTI_ACTIVITY_KIND_KERNEL, GPU_KERNELS, Kernel
# Memcpy: CUPTI_ACTIVITY_KIND_MEMCPY, Memcpy, MEMCPY
# OSRT: OS_RT_EVENTS, OSRTEvents, osrt_events
# String table: StringTable, STRING_TABLE, string_table
# ---------------------------------------------------------------------------

# Case-insensitive table name patterns to try (in order)
NVTX_TABLE_CANDIDATES = [
    "NVTX_EVENTS",
    "nvtx_events",
    "NvtxEvents",
    "nvtx",
]

CUDA_API_TABLE_CANDIDATES = [
    "CUPTI_ACTIVITY_KIND_RUNTIME",
    "CUDA_API_EVENTS",
    "cuda_api_events",
    "CudaApiEvents",
    "cuda_api",
]

GPU_KERNEL_TABLE_CANDIDATES = [
    "CUPTI_ACTIVITY_KIND_KERNEL",
    "cupti_activity_kind_kernel",
    "GPU_KERNELS",
    "gpu_kernels",
    "Kernel",
    "kernel",
]

MEMCPY_TABLE_CANDIDATES = [
    "CUPTI_ACTIVITY_KIND_MEMCPY",
    "cupti_activity_kind_memcpy",
    "Memcpy",
    "memcpy",
    "MEMCPY",
    "Memory",
    "memory",
]

OSRT_TABLE_CANDIDATES = [
    "OSRT_EVENTS",
    "osrt_events",
    "OSRTEvents",
    "osrt",
    "OS_RT_EVENTS",
]

STRING_TABLE_CANDIDATES = [
    "StringIds",
    "StringTable",
    "STRING_TABLE",
    "string_table",
    "String",
    "string",
]


def find_table(cursor, candidates: list) -> str | None:
    """Return the first matching table name from candidates, or None."""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing = {row[0] for row in cursor.fetchall()}
    for cand in candidates:
        if cand in existing:
            return cand
        # Also try case-insensitive
        for ex in existing:
            if ex.lower() == cand.lower():
                return ex
    return None


def list_all_tables(cursor) -> list:
    """Return all table names in the database."""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    return [row[0] for row in cursor.fetchall()]


def get_table_columns(cursor, table_name: str) -> list:
    """Return column names for a table."""
    cursor.execute(f"PRAGMA table_info('{table_name}')")
    return [row[1] for row in cursor.fetchall()]


def safe_fetch_csv(cursor, table_name: str, columns: list | None = None,
                   order_by: str | None = None) -> list:
    """
    Fetch all rows from a table as list of dicts.
    If columns is None, fetch all columns.
    """
    if columns is None:
        columns = get_table_columns(cursor, table_name)
    if not columns:
        return []

    col_str = ", ".join(f'"{c}"' for c in columns)
    query = f"SELECT {col_str} FROM '{table_name}'"
    if order_by:
        query += f" ORDER BY {order_by}"

    try:
        cursor.execute(query)
        rows = cursor.fetchall()
    except sqlite3.OperationalError as e:
        print(f"  WARNING: Failed to query {table_name}: {e}")
        return []

    return [dict(zip(columns, row)) for row in rows]


def resolve_nvtx_ranges(cursor, conn) -> list:
    """
    Build NVTX range records.

    nsys typically stores NVTX data in a table like NVTX_EVENTS with columns:
      - rangeId, textId (→ StringTable), start (ns), end (ns), threadId, processId, etc.

    Some versions store push/pop separately; others store ranges with start/end.

    We attempt to return a unified schema:
      start_ns, end_ns, duration_ns, name, range_id, thread_id, process_id,
      stream_id, correlation_id
    """
    nvtx_table = find_table(cursor, NVTX_TABLE_CANDIDATES)
    if not nvtx_table:
        print("  WARNING: No NVTX table found in database")
        return []

    cols = get_table_columns(cursor, nvtx_table)
    print(f"  NVTX table: {nvtx_table}, columns: {cols}")

    string_table = find_table(cursor, STRING_TABLE_CANDIDATES)

    # Try to build query based on available columns
    select_cols = []
    name_expr = "NULL"

    # Common NVTX column name mappings (case-insensitive)
    col_map = {c.lower(): c for c in cols}

    # start time
    start_col = None
    for key in ["start", "startns", "start_ns", "timestamp", "beginns"]:
        if key in col_map:
            start_col = col_map[key]
            break

    # end time
    end_col = None
    for key in ["end", "endns", "end_ns", "endtimestamp"]:
        if key in col_map:
            end_col = col_map[key]
            break

    # text / name
    text_col = None
    for key in ["textid", "text_id", "text", "name", "nvtxname", "messagetext"]:
        if key in col_map:
            text_col = col_map[key]
            break

    # range id
    range_id_col = None
    for key in ["rangeid", "range_id", "id", "nvtxrangeid"]:
        if key in col_map:
            range_id_col = col_map[key]
            break

    # thread id
    thread_col = None
    for key in ["threadid", "thread_id", "thread", "osthreadid"]:
        if key in col_map:
            thread_col = col_map[key]
            break

    # process id
    process_col = None
    for key in ["processid", "process_id", "pid"]:
        if key in col_map:
            process_col = col_map[key]
            break

    # stream id
    stream_col = None
    for key in ["streamid", "stream_id", "stream"]:
        if key in col_map:
            stream_col = col_map[key]
            break

    # correlation id
    corr_col = None
    for key in ["correlationid", "correlation_id", "correlation"]:
        if key in col_map:
            corr_col = col_map[key]
            break

    if not start_col or not end_col:
        print(f"  WARNING: Cannot find start/end columns in {nvtx_table}. Available: {cols}")
        return []

    # Build query
    query_cols = [start_col, end_col]
    col_aliases = ["start_ns", "end_ns"]

    # Try to resolve text names via StringTable
    if text_col and string_table:
        try:
            name_expr = f'COALESCE(s.value, "{nvtx_table}"."{text_col}")'
            query_cols = [f'"{nvtx_table}"."{start_col}"',
                          f'"{nvtx_table}"."{end_col}"',
                          f'"{nvtx_table}"."{text_col}"']
            col_aliases = ["start_ns", "end_ns", "name"]
            # We'll handle name via sub-select or Python join
        except Exception:
            name_expr = f'"{nvtx_table}"."{text_col}"'
            query_cols.append(f'"{nvtx_table}"."{text_col}"')
            col_aliases.append("name")
    elif text_col:
        query_cols.append(f'"{nvtx_table}"."{text_col}"')
        col_aliases.append("name")

    # Simple approach: fetch raw rows and build output
    sel = ", ".join(query_cols)
    query = f"SELECT {sel} FROM '{nvtx_table}' ORDER BY {start_col}"

    try:
        cursor.execute(query)
        raw_rows = cursor.fetchall()
    except sqlite3.OperationalError as e:
        print(f"  WARNING: Query failed: {e}")
        return []

    # Try to resolve names via StringTable
    name_lookup = {}
    if string_table and text_col:
        try:
            str_cols = get_table_columns(cursor, string_table)
            id_col = None
            val_col = None
            for key in ["id", "stringid", "_id_"]:
                if key in [c.lower() for c in str_cols]:
                    id_col = key
                    break
            if not id_col:
                id_col = str_cols[0]
            for key in ["value", "string", "text", "name"]:
                if key in [c.lower() for c in str_cols]:
                    val_col = key
                    break
            if not val_col:
                val_col = str_cols[1] if len(str_cols) > 1 else str_cols[0]

            cursor.execute(f'SELECT "{id_col}", "{val_col}" FROM "{string_table}"')
            for row in cursor.fetchall():
                name_lookup[row[0]] = row[1]
        except Exception:
            pass  # StringTable join not critical

    records = []
    for row in raw_rows:
        rec = {"start_ns": row[0], "end_ns": row[1]}
        name = None
        if len(row) > 2 and text_col:
            raw_name = row[2]
            name = name_lookup.get(raw_name, raw_name)
        rec["name"] = name or ""

        # duration
        try:
            rec["duration_ns"] = int(rec["end_ns"]) - int(rec["start_ns"])
        except (ValueError, TypeError):
            rec["duration_ns"] = 0

        rec["event_type"] = "NVTX"
        rec["stream_id"] = ""
        rec["correlation_id"] = ""
        rec["process_id"] = ""
        rec["thread_id"] = ""
        rec["nvtx_range"] = name or ""

        records.append(rec)

    return records


def parse_cuda_api(cursor) -> list:
    """Parse CUDA API events."""
    table = find_table(cursor, CUDA_API_TABLE_CANDIDATES)
    if not table:
        print("  WARNING: No CUDA API table found")
        return []

    cols = get_table_columns(cursor, table)
    print(f"  CUDA API table: {table}, columns: {cols}")
    col_lower = {c.lower(): c for c in cols}

    # Map columns
    start_col = None
    for k in ["start", "startns", "start_ns", "timestamp"]:
        if k in col_lower:
            start_col = col_lower[k]
            break

    end_col = None
    for k in ["end", "endns", "end_ns"]:
        if k in col_lower:
            end_col = col_lower[k]
            break

    name_col = None
    for k in ["name", "apiname", "apifunction", "functionname"]:
        if k in col_lower:
            name_col = col_lower[k]
            break

    stream_col = None
    for k in ["streamid", "stream_id"]:
        if k in col_lower:
            stream_col = col_lower[k]
            break

    corr_col = None
    for k in ["correlationid", "correlation_id"]:
        if k in col_lower:
            corr_col = col_lower[k]
            break

    thread_col = None
    for k in ["threadid", "thread_id"]:
        if k in col_lower:
            thread_col = col_lower[k]
            break

    process_col = None
    for k in ["processid", "process_id", "pid"]:
        if k in col_lower:
            process_col = col_lower[k]
            break

    if not start_col:
        print(f"  WARNING: No start column found in {table}")
        return []

    # Build select
    sel_parts = [f'"{start_col}" as start_ns']
    if end_col:
        sel_parts.append(f'"{end_col}" as end_ns')
    else:
        sel_parts.append(f'"{start_col}" as end_ns')  # fallback

    for c, alias in [(name_col, "name"), (stream_col, "stream_id"),
                      (corr_col, "correlation_id"), (thread_col, "thread_id"),
                      (process_col, "process_id")]:
        if c:
            sel_parts.append(f'"{c}" as {alias}')

    query = f"SELECT {', '.join(sel_parts)} FROM '{table}' ORDER BY start_ns"
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
    except sqlite3.OperationalError as e:
        print(f"  WARNING: CUDA API query failed: {e}")
        return []

    col_names = [p.split(" as ")[-1] for p in sel_parts]
    records = []
    for row in rows:
        rec = dict(zip(col_names, row))
        try:
            dur = int(rec.get("end_ns", rec["start_ns"])) - int(rec["start_ns"])
        except (ValueError, TypeError):
            dur = 0
        rec["duration_ns"] = dur
        rec["event_type"] = "CUDA_API"
        rec.setdefault("name", "")
        rec.setdefault("stream_id", "")
        rec.setdefault("correlation_id", "")
        rec.setdefault("thread_id", "")
        rec.setdefault("process_id", "")
        rec["nvtx_range"] = ""
        records.append(rec)

    return records


def parse_gpu_kernels(cursor) -> list:
    """Parse GPU kernel events."""
    table = find_table(cursor, GPU_KERNEL_TABLE_CANDIDATES)
    if not table:
        print("  WARNING: No GPU kernel table found")
        return []

    cols = get_table_columns(cursor, table)
    print(f"  GPU kernel table: {table}, columns: {cols}")
    col_lower = {c.lower(): c for c in cols}

    start_col = None
    for k in ["start", "startns", "start_ns", "beginns", "timestamp"]:
        if k in col_lower:
            start_col = col_lower[k]
            break

    end_col = None
    for k in ["end", "endns", "end_ns"]:
        if k in col_lower:
            end_col = col_lower[k]
            break

    name_col = None
    for k in ["name", "kernelname", "shortname", "demangledname"]:
        if k in col_lower:
            name_col = col_lower[k]
            break

    stream_col = None
    for k in ["streamid", "stream_id"]:
        if k in col_lower:
            stream_col = col_lower[k]
            break

    corr_col = None
    for k in ["correlationid", "correlation_id"]:
        if k in col_lower:
            corr_col = col_lower[k]
            break

    if not start_col:
        print(f"  WARNING: No start column found in {table}")
        return []

    sel_parts = [f'"{start_col}" as start_ns']
    sel_parts.append(f'"{end_col}" as end_ns' if end_col else f'"{start_col}" as end_ns')

    for c, alias in [(name_col, "name"), (stream_col, "stream_id"), (corr_col, "correlation_id")]:
        if c:
            sel_parts.append(f'"{c}" as {alias}')

    query = f"SELECT {', '.join(sel_parts)} FROM '{table}' ORDER BY start_ns"
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
    except sqlite3.OperationalError as e:
        print(f"  WARNING: GPU kernel query failed: {e}")
        return []

    col_names = [p.split(" as ")[-1] for p in sel_parts]
    records = []
    for row in rows:
        rec = dict(zip(col_names, row))
        try:
            dur = int(rec.get("end_ns", rec["start_ns"])) - int(rec["start_ns"])
        except (ValueError, TypeError):
            dur = 0
        rec["duration_ns"] = dur
        rec["event_type"] = "GPU_KERNEL"
        rec.setdefault("name", "")
        rec.setdefault("stream_id", "")
        rec.setdefault("correlation_id", "")
        rec["thread_id"] = ""
        rec["process_id"] = ""
        rec["nvtx_range"] = ""
        records.append(rec)

    return records


def parse_memcpy(cursor) -> list:
    """Parse memory copy / memory operation events."""
    table = find_table(cursor, MEMCPY_TABLE_CANDIDATES)
    if not table:
        print("  WARNING: No memcpy/memory table found")
        return []

    cols = get_table_columns(cursor, table)
    print(f"  Memcpy table: {table}, columns: {cols}")
    col_lower = {c.lower(): c for c in cols}

    start_col = None
    for k in ["start", "startns", "start_ns", "timestamp"]:
        if k in col_lower:
            start_col = col_lower[k]
            break

    end_col = None
    for k in ["end", "endns", "end_ns"]:
        if k in col_lower:
            end_col = col_lower[k]
            break

    name_col = None
    for k in ["name", "operation", "memcpytype", "type", "shortname"]:
        if k in col_lower:
            name_col = col_lower[k]
            break

    stream_col = None
    for k in ["streamid", "stream_id"]:
        if k in col_lower:
            stream_col = col_lower[k]
            break

    corr_col = None
    for k in ["correlationid", "correlation_id"]:
        if k in col_lower:
            corr_col = col_lower[k]
            break

    if not start_col:
        print(f"  WARNING: No start column found in {table}")
        return []

    sel_parts = [f'"{start_col}" as start_ns']
    sel_parts.append(f'"{end_col}" as end_ns' if end_col else f'"{start_col}" as end_ns')

    for c, alias in [(name_col, "name"), (stream_col, "stream_id"), (corr_col, "correlation_id")]:
        if c:
            sel_parts.append(f'"{c}" as {alias}')

    query = f"SELECT {', '.join(sel_parts)} FROM '{table}' ORDER BY start_ns"
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
    except sqlite3.OperationalError as e:
        print(f"  WARNING: Memcpy query failed: {e}")
        return []

    col_names = [p.split(" as ")[-1] for p in sel_parts]
    records = []
    for row in rows:
        rec = dict(zip(col_names, row))
        try:
            dur = int(rec.get("end_ns", rec["start_ns"])) - int(rec["start_ns"])
        except (ValueError, TypeError):
            dur = 0
        rec["duration_ns"] = dur
        rec["event_type"] = "MEMCPY"
        rec.setdefault("name", "")
        rec.setdefault("stream_id", "")
        rec.setdefault("correlation_id", "")
        rec["thread_id"] = ""
        rec["process_id"] = ""
        rec["nvtx_range"] = ""
        records.append(rec)

    return records


def parse_osrt(cursor) -> list:
    """Parse OS runtime events."""
    table = find_table(cursor, OSRT_TABLE_CANDIDATES)
    if not table:
        print("  WARNING: No OSRT table found (optional, may not be present)")
        return []

    cols = get_table_columns(cursor, table)
    print(f"  OSRT table: {table}, columns: {cols}")
    col_lower = {c.lower(): c for c in cols}

    start_col = None
    for k in ["start", "startns", "start_ns", "timestamp"]:
        if k in col_lower:
            start_col = col_lower[k]
            break

    end_col = None
    for k in ["end", "endns", "end_ns"]:
        if k in col_lower:
            end_col = col_lower[k]
            break

    name_col = None
    for k in ["name", "eventname", "apiname", "functionname"]:
        if k in col_lower:
            name_col = col_lower[k]
            break

    thread_col = None
    for k in ["threadid", "thread_id"]:
        if k in col_lower:
            thread_col = col_lower[k]
            break

    process_col = None
    for k in ["processid", "process_id", "pid"]:
        if k in col_lower:
            process_col = col_lower[k]
            break

    if not start_col:
        print(f"  WARNING: No start column found in {table}")
        return []

    sel_parts = [f'"{start_col}" as start_ns']
    sel_parts.append(f'"{end_col}" as end_ns' if end_col else f'"{start_col}" as end_ns')

    for c, alias in [(name_col, "name"), (thread_col, "thread_id"), (process_col, "process_id")]:
        if c:
            sel_parts.append(f'"{c}" as {alias}')

    query = f"SELECT {', '.join(sel_parts)} FROM '{table}' ORDER BY start_ns"
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
    except sqlite3.OperationalError as e:
        print(f"  WARNING: OSRT query failed: {e}")
        return []

    col_names = [p.split(" as ")[-1] for p in sel_parts]
    records = []
    for row in rows:
        rec = dict(zip(col_names, row))
        try:
            dur = int(rec.get("end_ns", rec["start_ns"])) - int(rec["start_ns"])
        except (ValueError, TypeError):
            dur = 0
        rec["duration_ns"] = dur
        rec["event_type"] = "OSRT"
        rec.setdefault("name", "")
        rec.setdefault("thread_id", "")
        rec.setdefault("process_id", "")
        rec["stream_id"] = ""
        rec["correlation_id"] = ""
        rec["nvtx_range"] = ""
        records.append(rec)

    return records


# ---------------------------------------------------------------------------
# Unified CSV output columns
# ---------------------------------------------------------------------------
UNIFIED_COLUMNS = [
    "start_ns", "end_ns", "duration_ns", "event_type", "name",
    "stream_id", "correlation_id", "process_id", "thread_id", "nvtx_range",
]


def write_csv(records: list, path: Path):
    """Write records to CSV."""
    if not records:
        print(f"  (no records to write for {path.name})")
        return
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=UNIFIED_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for rec in records:
            # Fill missing keys
            for col in UNIFIED_COLUMNS:
                rec.setdefault(col, "")
            writer.writerow(rec)
    print(f"  Wrote {len(records)} rows → {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Parse nsys SQLite export to structured CSV/JSON"
    )
    parser.add_argument("--sqlite", required=True, help="Path to .sqlite file")
    parser.add_argument("--output-dir", required=True, help="Directory for output files")
    args = parser.parse_args()

    sqlite_path = Path(args.sqlite)
    if not sqlite_path.exists():
        print(f"ERROR: SQLite file not found: {sqlite_path}")
        sys.exit(1)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[parse_nsys_sqlite] Input:  {sqlite_path}")
    print(f"[parse_nsys_sqlite] Output: {out_dir.resolve()}")
    print()

    conn = sqlite3.connect(str(sqlite_path))
    cursor = conn.cursor()

    # ---- 1. List all tables ----
    tables = list_all_tables(cursor)
    print(f"[parse_nsys_sqlite] Found {len(tables)} table(s):")
    for t in tables:
        cols = get_table_columns(cursor, t)
        print(f"  {t} ({len(cols)} cols: {', '.join(cols[:10])}{'...' if len(cols) > 10 else ''})")

    tables_json = out_dir / "tables.json"
    with open(tables_json, "w", encoding="utf-8") as f:
        json.dump({"sqlite_file": str(sqlite_path.resolve()), "tables": tables}, f, indent=2)
    print(f"\n[parse_nsys_sqlite] Wrote: {tables_json}")

    # ---- 2. Parse each event type ----
    print("\n[parse_nsys_sqlite] Parsing NVTX ranges...")
    nvtx_records = resolve_nvtx_ranges(cursor, conn)

    print("\n[parse_nsys_sqlite] Parsing CUDA API calls...")
    cuda_api_records = parse_cuda_api(cursor)

    print("\n[parse_nsys_sqlite] Parsing GPU kernels...")
    gpu_kernel_records = parse_gpu_kernels(cursor)

    print("\n[parse_nsys_sqlite] Parsing memcpy events...")
    memcpy_records = parse_memcpy(cursor)

    print("\n[parse_nsys_sqlite] Parsing OSRT events...")
    osrt_records = parse_osrt(cursor)

    # ---- 3. Write CSVs ----
    print("\n[parse_nsys_sqlite] Writing CSVs...")
    write_csv(nvtx_records, out_dir / "nvtx_ranges.csv")
    write_csv(cuda_api_records, out_dir / "cuda_api.csv")
    write_csv(gpu_kernel_records, out_dir / "gpu_kernels.csv")
    write_csv(memcpy_records, out_dir / "memcpy.csv")
    if osrt_records:
        write_csv(osrt_records, out_dir / "osrt.csv")
    else:
        print("  Skipping osrt.csv (no OSRT data)")

    # ---- 4. Timeline summary ----
    all_records = nvtx_records + cuda_api_records + gpu_kernel_records + memcpy_records + osrt_records
    event_type_counts = {}
    min_ns = None
    max_ns = None
    for rec in all_records:
        et = rec.get("event_type", "UNKNOWN")
        event_type_counts[et] = event_type_counts.get(et, 0) + 1
        try:
            s = int(rec["start_ns"])
            e = int(rec["end_ns"])
            if min_ns is None or s < min_ns:
                min_ns = s
            if max_ns is None or e > max_ns:
                max_ns = e
        except (ValueError, TypeError, KeyError):
            pass

    timeline_summary = {
        "sqlite_file": str(sqlite_path.resolve()),
        "total_events": len(all_records),
        "time_range_ns": {"start": min_ns, "end": max_ns},
        "time_range_ms": {
            "start": round(min_ns / 1e6, 3) if min_ns else None,
            "end": round(max_ns / 1e6, 3) if max_ns else None,
            "duration": round((max_ns - min_ns) / 1e6, 3) if (min_ns and max_ns) else None,
        },
        "event_counts": event_type_counts,
    }

    timeline_path = out_dir / "timeline_summary.json"
    with open(timeline_path, "w", encoding="utf-8") as f:
        json.dump(timeline_summary, f, indent=2, ensure_ascii=False)
    print(f"\n[parse_nsys_sqlite] Wrote: {timeline_path}")

    # ---- Print summary ----
    print(f"\n{'='*50}")
    print(f"[parse_nsys_sqlite] PARSE COMPLETE")
    print(f"  Total events: {len(all_records)}")
    for et, cnt in sorted(event_type_counts.items()):
        print(f"    {et}: {cnt}")
    print(f"{'='*50}")

    conn.close()


if __name__ == "__main__":
    main()
