"""Fail-closed, CPU-only evidence checks for the Gate7 smoke launcher.

This checks existing runner artifacts; it does not change scientific analysis.
"""

from __future__ import annotations

import argparse
from contextlib import closing
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from exposedpath.cross_pass_validator import (
    PASS_PARITY_OK,
    load_attempt_accounting,
    validate_attempt_accounting,
    validate_pair,
)


# Engineering export-completeness gate, not v1.4.1 scientific qualification.
# This Gate7 CUDA+NVTX model smoke must retain the connected metadata, host API,
# synchronization, kernel, mapping, and diagnostic tables. MEMCPY/MEMSET are
# activity-dependent and deliberately not required here.
GATE7_REQUIRED_EXPORT_COLUMNS = {
    "META_DATA_CAPTURE": ("name", "value"),
    "META_DATA_EXPORT": ("name", "value"),
    "StringIds": ("id", "value"),
    "NVTX_EVENTS": ("start", "end", "text", "textId"),
    "CUPTI_ACTIVITY_KIND_RUNTIME": ("start", "end", "correlationId", "nameId"),
    "CUPTI_ACTIVITY_KIND_SYNCHRONIZATION": ("start", "end", "correlationId"),
    "CUPTI_ACTIVITY_KIND_KERNEL": ("start", "end", "correlationId"),
    "TARGET_INFO_CUDA_CONTEXT_INFO": ("contextId", "deviceId"),
    "TARGET_INFO_CUDA_STREAM": ("streamId", "contextId"),
    "TARGET_INFO_GPU": ("id", "name"),
    "DIAGNOSTIC_EVENT": ("timestamp", "source", "severity", "text"),
}


def _read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict]:
    records = [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    if not records or not all(isinstance(record, dict) for record in records):
        raise ValueError(f"Missing or invalid telemetry records: {path}")
    return records


def validate_sqlite(path: Path) -> list[str]:
    path = Path(path)
    try:
        if not path.is_file() or path.stat().st_size == 0:
            return ["SQLite missing or empty"]
        with closing(sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)) as db:
            if db.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                return ["SQLite integrity_check failed"]
            tables = {row[0].casefold(): row[0]
                      for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not tables:
                return ["SQLite has no readable tables"]
            issues = []
            for table, required_columns in GATE7_REQUIRED_EXPORT_COLUMNS.items():
                actual_name = tables.get(table.casefold())
                if actual_name is None:
                    issues.append(f"SQLite missing required table {table}")
                    continue
                # Names come only from the fixed table list above, never input.
                columns = {row[1].casefold() for row in db.execute(f'PRAGMA table_info("{table}")')}
                missing = [name for name in required_columns if name.casefold() not in columns]
                if missing:
                    issues.append(f"SQLite {table} missing columns: {', '.join(missing)}")
            return issues
    except (sqlite3.DatabaseError, OSError, ValueError) as exc:
        return [f"SQLite schema unreadable: {exc}"]
    return []


def validate_evidence(manifest_path: Path, preflight_path: Path, pass0: Path, pass1: Path) -> list[str]:
    issues: list[str] = []
    try:
        manifest = _read_json(Path(manifest_path))
        preflight = _read_json(Path(preflight_path))
        parities = [
            _read_json(Path(folder) / "cross_pass_parity.json")
            for folder in (pass0, pass1)
        ]
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"Required identity evidence missing/invalid: {exc}"]

    if manifest.get("data_role") != "Engineering":
        issues.append("Gate7 manifest data_role is not Engineering")
    parity_status = validate_pair(*parities)
    if parity_status != [PASS_PARITY_OK]:
        issues.append(f"Cross-pass parity failed: {parity_status}")
    for label, parity in zip(("pass0", "pass1"), parities):
        for key, manifest_key in (
            ("data_role", "data_role"),
            ("gpu_uuid", "gpu_uuid"),
            ("gpu_pci_bus_id", "gpu_pci_bus_id"),
            ("requested_physical_gpu_index", "gpu_index_physical"),
        ):
            if parity.get(key) != manifest.get(manifest_key):
                issues.append(f"{label} parity {key} differs from manifest")

    try:
        warmups = int(manifest["warmup_count"])
        repeats = int(manifest["repeat_count"])
        accounting = [
            load_attempt_accounting(Path(folder), planned_warmup_count=warmups,
                                    planned_repeat_count=repeats)
            for folder in (pass0, pass1)
        ]
        accounting_status = validate_attempt_accounting(*accounting)
        if accounting_status != [PASS_PARITY_OK]:
            issues.append(f"Attempt accounting failed: {accounting_status}")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        issues.append(f"Attempt accounting missing/invalid: {exc}")

    physical = manifest.get("gpu_index_physical")
    logical = manifest.get("gpu_index_logical")
    expected = {
        "physical_gpu_index": physical,
        "logical_gpu_index": logical,
        "gpu_uuid": manifest.get("gpu_uuid"),
        "gpu_pci_bus_id": manifest.get("gpu_pci_bus_id"),
    }
    if physical is None or manifest.get("gpu_index") != physical or logical is None:
        issues.append("Manifest physical/logical GPU identity incomplete")
    for key, value in expected.items():
        if value is None or preflight.get(key) != value:
            issues.append(f"Preflight {key} differs from manifest or missing")

    for label, folder in (("pass0", pass0), ("pass1", pass1)):
        path = Path(folder) / "telemetry" / f"{label}_gpu_telemetry.jsonl"
        try:
            records = _read_jsonl(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            issues.append(f"{label} telemetry missing/invalid: {exc}")
            continue
        for index, row in enumerate(records):
            prefix = f"{label} telemetry record {index}"
            if row.get("query_exit_code") != 0 or row.get("identity_match") is not True:
                issues.append(f"{prefix} query/identity failure")
            for key, value in (
                ("requested_physical_gpu_index", physical),
                ("requested_gpu_uuid", expected["gpu_uuid"]),
                ("requested_pci_bus_id", expected["gpu_pci_bus_id"]),
                ("observed_gpu_uuid", expected["gpu_uuid"]),
                ("observed_pci_bus_id", expected["gpu_pci_bus_id"]),
            ):
                if value is None or row.get(key) != value:
                    issues.append(f"{prefix} {key} mismatch")
            if str(row.get("observed_gpu_index")) != str(physical):
                issues.append(f"{prefix} observed_gpu_index mismatch")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="check", required=True)
    sqlite = sub.add_parser("sqlite")
    sqlite.add_argument("--sqlite", type=Path, required=True)
    evidence = sub.add_parser("evidence")
    for name in ("manifest", "preflight", "pass0", "pass1"):
        evidence.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    issues = (validate_sqlite(args.sqlite) if args.check == "sqlite" else
              validate_evidence(args.manifest, args.preflight, args.pass0, args.pass1))
    print(json.dumps({"status": "PASS" if not issues else "BLOCKED", "issues": issues}))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
