"""Fail-closed, CPU-only evidence checks for the Gate7 smoke launcher.

This checks existing runner artifacts; it does not change scientific analysis.
"""

from __future__ import annotations

import argparse
from contextlib import closing
import csv
import hashlib
import json
import math
import os
import re
import sqlite3
import sys
from pathlib import Path

# Bootstrap only direct CLI execution; library imports must not mutate the
# interpreter identity sealed by the target-Python probe.
if __package__ in (None, ''):
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


def validate_pre_model_identity(manifest_path: Path, preflight_path: Path, project_root: Path,
                                *, execution_contract: str = 'GATE7_G1') -> list[str]:
    """Shared provenance, with an explicit closed execution-contract dispatch.

    Historical Gate7 callers remain G1-only; the isolated N1 entry opts into
    its versioned model contract, never a generic permission to accept N1.
    """
    from exposedpath import platform_adapter
    from exposedpath.manifest import resolve_logical_cuda_index
    issues = []
    try:
        manifest = _read_json(manifest_path)
        preflight = _read_json(preflight_path)
        commit = manifest.get("runner_git_commit")
        if not isinstance(commit, str) or re.fullmatch(r"[0-9a-f]{40}", commit) is None:
            issues.append("Manifest runner_git_commit missing/invalid")
        if manifest.get("runner_git_dirty") is not False:
            issues.append("Manifest runner_git_dirty is not explicitly false")
        # Explicit worktree, resolved Git executable, structured argv; never fallback.
        actual = platform_adapter.git(["-C", str(project_root), "rev-parse", "HEAD"])
        dirty = platform_adapter.git(["-C", str(project_root), "status", "--porcelain"])
        if actual != commit or dirty:
            issues.append("Current Git identity differs or worktree is dirty")
        physical = manifest.get("gpu_index_physical")
        logical = manifest.get("gpu_index_logical")
        if type(physical) is not int or physical < 0 or type(logical) is not int:
            raise ValueError("Manifest physical/logical GPU identity missing/invalid")
        if manifest.get("gpu_index") != physical or manifest.get("gpu") != physical:
            issues.append("Manifest physical GPU aliases conflict")
        if os.environ.get("CUDA_DEVICE_ORDER") != "PCI_BUS_ID" or os.environ.get("CUDA_VISIBLE_DEVICES") != str(physical):
            issues.append("Gate7 physical-index masking environment conflicts")
        resolve_logical_cuda_index(physical_gpu_index=physical,
            cuda_visible_devices=os.environ.get("CUDA_VISIBLE_DEVICES"), declared_logical_index=logical)
        for key, pattern in (("gpu_uuid", r"GPU-[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}"),
                             ("gpu_pci_bus_id", r"[0-9a-fA-F]{8}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-7]")):
            value = manifest.get(key)
            if not isinstance(value, str) or re.fullmatch(pattern, value) is None or preflight.get(key) != value:
                issues.append(f"Preflight/manifest {key} missing, invalid or conflicting")
        for key, value in (("physical_gpu_index", physical), ("logical_gpu_index", logical)):
            if type(preflight.get(key)) is not int or preflight[key] != value:
                issues.append(f"Preflight {key} missing or conflicting")
        if execution_contract == 'GATE7_G1':
            if (manifest.get("data_role") != "Engineering" or manifest.get("study_mode") != "G1_NATURAL"
                    or manifest.get("n1_intervention") is not None):
                issues.append("Gate7 Engineering/G1 identity conflicts")
        elif execution_contract == 'N1-VERIFIED-MODEL/0.1':
            from exposedpath.n1_model import validate_prepared
            validate_prepared(manifest, manifest_path.parent, project_root)
        elif execution_contract in ('G11-LIMITED-PILOT/0.1','G11-WARMUP-CONTROL/0.1','G11-WARMUP3-PAIR/0.1'):
            from exposedpath.gate11_pilot import validate_prepared
            if manifest.get('pilot',{}).get('version')!=execution_contract:
                raise ValueError('Pilot pre-model contract version conflicts')
            validate_prepared(manifest, manifest_path.parent, project_root)
        else:
            raise ValueError('Unknown pre-model execution contract')
    except Exception as exc:
        # Keep missing identity unknown and expose the precise adapter/IO error.
        issues.append(f"Pre-model identity unavailable: {type(exc).__name__}: {exc}")
    return issues


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


def validate_analyzer(result_path: Path, sqlite_path: Path, manifest_path: Path) -> dict:
    """Gate7 legacy-only integration acceptance, never scientific qualification.

    The launcher separately gates analyzer exit and SQLite integrity/schema.
    Hashes record the invocation's artifacts; legacy JSON has no embedded input
    digest or stable run identity, so these are not a scientific lineage proof.
    """
    report = {
        "acceptance_version": "gate7-legacy-analyzer/1",
        "analyzer_type": "legacy-only",
        "acceptance_scope": "ENGINEERING_INTEGRATION_ONLY",
        "measurement_validity": "NOT_ASSESSED",
        "window_coverage": {"status": "unknown", "count": None, "duration": None,
            "reason": "LEGACY_OUTPUT_LACKS_WINDOW_IDENTITY_AND_FROZEN_VALIDITY"},
        "a_structure_status": "NOT_VALIDATED", "status": "BLOCKED", "issues": [],
    }
    issues = report["issues"]

    def require(condition: bool, message: str) -> None:
        if not condition:
            raise ValueError(message)

    def number(value) -> bool:
        return type(value) in (int, float) and math.isfinite(value) and value >= 0

    def text(value) -> bool:
        return isinstance(value, str) and bool(value.strip())

    def digest(path: Path) -> str:
        require(path.is_file() and path.stat().st_size > 0, f"Required artifact missing/empty: {path.name}")
        sha = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                sha.update(chunk)
        return sha.hexdigest()

    def strict_json(path: Path) -> dict:
        def reject_constant(value):
            raise ValueError(f"Non-finite JSON number: {value}")
        def unique_object(pairs):
            result = {}
            for key, value in pairs:
                require(key not in result, f"Duplicate JSON key: {key}")
                result[key] = value
            return result
        value = json.loads(path.read_text(encoding="utf-8-sig"),
                           parse_constant=reject_constant, object_pairs_hook=unique_object)
        require(isinstance(value, dict), "Expected JSON object")
        return value

    try:
        result_path, sqlite_path, manifest_path = map(Path, (result_path, sqlite_path, manifest_path))
        hashes = {"result_sha256": digest(result_path), "sqlite_sha256": digest(sqlite_path),
                  "manifest_sha256": digest(manifest_path)}
        csv_rows = {}
        for name in ("accounting_summary.csv", "b_sync_detail.csv"):
            hashes[name + "_sha256"] = digest(result_path.parent / name)
            with (result_path.parent / name).open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                fields = {"physical_sync_uid"} if name == "b_sync_detail.csv" else {"request_id", "repeat_id", "phase"}
                require(fields <= set(reader.fieldnames or []), f"{name} required columns missing")
                rows = list(reader)
                require(bool(rows) and all(all(text(row.get(k)) for k in fields) for row in rows),
                        f"{name} missing/malformed rows")
                csv_rows[name] = rows
        data = strict_json(result_path)
        manifest = strict_json(manifest_path)
        require(data.get("metric_definition_version") == "exposedpath-v2", "Unknown analyzer output version")
        metadata = data.get("metadata")
        require(isinstance(metadata, dict), "metadata missing/malformed")
        for key in ("metric_definition_version", "parser_version"):
            require(metadata.get(key) == "exposedpath-v2", f"metadata {key} mismatch")
        require(metadata.get("workload_id") == sqlite_path.stem, "Analyzer input workload identity mismatch")
        commit = manifest.get("runner_git_commit")
        require(isinstance(commit, str) and re.fullmatch(r"[0-9a-f]{40}", commit) is not None,
                "Manifest runner_git_commit missing/invalid")
        require(metadata.get("git_commit") == commit[:12], "Analyzer/runner commit identity mismatch")
        require(manifest.get("data_role") == "Engineering", "Manifest is not Engineering")
        for key in ("run_id", "wmpc_id"):
            require(text(manifest.get(key)), f"Manifest {key} missing/invalid")
        report["identity"] = {**hashes, "runner_git_commit": commit,
            "analyzer_git_commit": metadata["git_commit"], "run_id": manifest["run_id"],
            "wmpc_id": manifest["wmpc_id"], "workload_id": metadata["workload_id"],
            "binding": "LAUNCHER_INVOCATION_ARTIFACTS_NOT_SCIENTIFIC_LINEAGE"}
        quality = data.get("trace_quality")
        require(isinstance(quality, dict) and bool(quality), "trace_quality missing/malformed")
        report["diagnostics"] = quality
        for key in ("fatal_errors", "warnings", "missing_optional_tables"):
            require(isinstance(quality.get(key), list) and all(text(x) for x in quality[key]),
                    f"trace_quality {key} missing/malformed")
        require(not quality["fatal_errors"], "Analyzer fatal diagnostics")
        # This exact optional-table observation is known for this legacy parser.
        # Other warnings require explicit review, not blanket warning immunity.
        for warning in quality["warnings"] + quality["missing_optional_tables"]:
            require(warning == "CUDA event activity table unavailable", "Unreviewed analyzer warning: " + warning)
        require(quality.get("dropped_records_status") == "unknown",
                "Unrecognized/dropped trace status; only legacy unknown is approved")
        for key in ("request_count", "repeat_count"):
            require(type(quality.get(key)) is int and quality[key] > 0, f"Invalid {key}")
        for key in ("schema_version", "nsys_product_version"):
            require(text(metadata.get(key)), f"metadata {key} missing")
        categories = ("host_path", "cuda_api", "device_wait", "sync_residual", "unattributed")
        summary = data.get("A_summary")
        require(isinstance(summary, dict), "A_summary missing/malformed")
        for phase in ("prefill", "decode", "full_request"):
            values = summary.get(phase)
            require(isinstance(values, dict) and bool(values), f"A_summary {phase} missing/empty")
            for category in categories:
                require(number(values.get(f"A_{category}_ms_mean")), f"A_summary {phase}/{category} invalid")
            require(all(value is None or number(value) for value in values.values()),
                    f"A_summary {phase} malformed numeric field")
        for key in ("raw_summary", "overlap_summary", "B_summary", "legacy_compatibility"):
            require(isinstance(data.get(key), dict) and bool(data[key]), f"{key} missing/empty/malformed")
        for phase in ("prefill", "decode", "full_request"):
            for key in ("raw_summary", "overlap_summary", "B_summary"):
                require(isinstance(data[key].get(phase), dict) and bool(data[key][phase]),
                        f"{key}/{phase} missing/malformed")
            for key in ("total_syncs", "valid_wait_sets", "B_valid", "B_invalid"):
                value = data["B_summary"][phase].get(key)
                require(type(value) is int and value >= 0, f"B_summary/{phase}/{key} invalid")
        repeats = data.get("repeat_results")
        require(isinstance(repeats, list) and bool(repeats), "repeat_results missing/empty")
        for row in repeats:
            require(isinstance(row, dict), "repeat result malformed")
            require(row.get("phase") in ("prefill", "decode", "full_request"), "repeat phase invalid")
            require(all(type(row.get(k)) is int for k in ("request_id", "repeat_id")), "repeat identity invalid")
            require(number(row.get("window_duration_ms")), "repeat duration invalid")
            for category in categories:
                require(number(row.get(f"A_{category}_ms")), "repeat A field invalid")
        csv_repeat_ids = sorted((r["request_id"], r["repeat_id"], r["phase"])
                                for r in csv_rows["accounting_summary.csv"])
        json_repeat_ids = sorted((str(r["request_id"]), str(r["repeat_id"]), r["phase"]) for r in repeats)
        require(csv_repeat_ids == json_repeat_ids, "CSV/JSON repeat identities differ")
        details = data.get("b_sync_details")
        require(isinstance(details, list) and bool(details), "b_sync_details missing/empty")
        seen = set()
        for row in details:
            require(isinstance(row, dict), "legacy sync detail malformed")
            uid = row.get("physical_sync_uid")
            require(text(uid) and uid not in seen, "legacy physical sync UID missing/duplicate")
            seen.add(uid)
            require(text(row.get("phase")), "legacy phase label missing")
            for key in ("request_id", "repeat_id", "sync_start_ns", "sync_end_ns"):
                require(type(row.get(key)) is int, f"legacy {key} invalid")
            require(row["sync_end_ns"] >= row["sync_start_ns"], "legacy sync time reversal")
            for key in ("wait_set_valid", "B_valid"):
                require(type(row.get(key)) is bool, f"legacy {key} invalid")
            require(not row["B_valid"] or row["wait_set_valid"], "Contradictory legacy validity flags")
            require(isinstance(row.get("invalid_reason"), str), "legacy invalid_reason missing")
        require(sorted(r["physical_sync_uid"] for r in csv_rows["b_sync_detail.csv"]) == sorted(seen),
                "CSV/JSON physical sync identities differ")
        report["legacy_sync_diagnostics"] = details  # no reinterpretation or aggregation
        report["a_structure_status"] = "VALIDATED_STRUCTURE_ONLY"
        report["status"] = "PASS"
    except (OSError, ValueError, TypeError, KeyError, OverflowError) as exc:
        issues.append(str(exc))
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="check", required=True)
    sqlite = sub.add_parser("sqlite")
    sqlite.add_argument("--sqlite", type=Path, required=True)
    evidence = sub.add_parser("evidence")
    for name in ("manifest", "preflight", "pass0", "pass1"):
        evidence.add_argument(f"--{name}", type=Path, required=True)
    analyzer = sub.add_parser("analyzer")
    for name in ("result", "sqlite", "manifest"):
        analyzer.add_argument(f"--{name}", type=Path, required=True)
    pre_model = sub.add_parser("pre-model")
    for name in ("manifest", "preflight", "project-root"):
        pre_model.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    if args.check == "pre-model":
        issues = validate_pre_model_identity(args.manifest, args.preflight, args.project_root)
        print(json.dumps({"status": "BLOCKED" if issues else "PASS", "issues": issues}))
        return 1 if issues else 0
    if args.check == "analyzer":
        report = validate_analyzer(args.result, args.sqlite, args.manifest)
        print(json.dumps(report, allow_nan=False))
        return 0 if report["status"] == "PASS" else 1
    issues = (validate_sqlite(args.sqlite) if args.check == "sqlite" else
              validate_evidence(args.manifest, args.preflight, args.pass0, args.pass1))
    print(json.dumps({"status": "PASS" if not issues else "BLOCKED", "issues": issues}))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
