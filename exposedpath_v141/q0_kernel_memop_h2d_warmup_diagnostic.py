"""Engineering-only native Q0 formal-shape pair; never a full Q0 execution.

Both arms enter the unchanged native measured path without size/direction/time
overrides. Only B adds a fixed pre-capture same-kernel warm-up. Existing
Canonical and S analyzers read the exported evidence; no A/B evaluator runs.
"""

from __future__ import annotations

import gzip
import json
import os
import re
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .canonical_raw import convert_sqlite_to_canonical
from .q0_collection import (
    EnvironmentProbe, ProcessRunner, _default_environment_probe, _run_text,
    _sha256, _validate_environment,
)
from .q0_execution import _source_manifest
from .q0_kernel_memop_d2h_warmup_diagnostic import (
    ARM_A, ARM_B, ARM_OUTPUT_NAMES, BASELINE_REFERENCE_COMMIT, CASE_ID,
    METADATA_TRANSPORT, WARMUP_FLAG, WARMUP_KERNEL_MS,
    _open_readonly, build_pair_export_argv, recover_warmup_diagnostic_marker,
    summarize_warmup_diagnostic_sqlite,
)
from .q0_real import map_real_activity_labels
from .s_bundle import analyze_canonical_to_s
from .sync_semantics import load_canonical_bundle


H2D_BYTES = 512 * 1024 * 1024
KERNEL_MS = 10
RUN_ID_PATTERN = re.compile(
    r"q0-win-4090-\d{8}-kernel-memop-h2d-formalshape-warmup-02"
)
NON_BLOCKING_STREAM_ENUM_NAME = "CUPTI_ACTIVITY_STREAM_CREATE_FLAG_NON_BLOCKING"
SUPERSEDED_RUN_ID_SUFFIX = "-warmup-01"
PRIOR_RUN_DISPOSITION = {
    "run_id_suffix": SUPERSEDED_RUN_ID_SUFFIX,
    "disposition": "INVALID_ANALYZER_STREAM_FLAG_ASSUMPTION",
    "reason": (
        "analyzer 把 CUPTI stream enum id 错当成 cudaStreamNonBlocking==1：Raw SQLite "
        "中 flag=2 且 ENUM_CUPTI_STREAM_TYPE 为 NON_BLOCKING；B 未执行"
    ),
    "usable_as_arm_result": False,
    "rerun_allowed": False,
}
ELIGIBILITY = {
    "formal_evidence": False, "q0_status": "NOT_RUN",
    "scope": "NATIVE_H2D_FORMALSHAPE_WARMUP_ENGINEERING_ONLY",
}
OUTCOME_POLICY = {
    "AMENDMENT_REVIEW_ELIGIBLE": {
        "condition": "A=0,B>0,B_terminal=MEMCPY_B/MEMOP",
        "action": "CONSTRUCTION_AMENDMENT_REVIEW_ONLY", "changes_gate6_or_q0": False,
    },
    "TERMINAL_MISMATCH_STOP": {
        "condition": "A=0,B>0,B_terminal_mismatch", "action": "STOP_NO_ORACLE_CHANGE_OR_TUNING",
    },
    "NO_OVERLAP_STOP": {"condition": "A=0,B=0", "action": "STOP"},
    "CONTROL_OVERLAP_REVIEW": {
        "condition": "A>0", "action": "REVIEW_NO_WARMUP_ATTRIBUTION",
    },
    "INVALID_STOP": {"condition": "ANY_EVIDENCE_INVALID_OR_AMBIGUOUS", "action": "STOP_NO_RETRY"},
}
INTERPRETATION_BOUNDARY = {
    "claim_scope": "ENGINEERING_CONTROLLED_ASSOCIATION_ONLY",
    "fixed_execution_order_limitation": "A_FIRST_CROSS_PROCESS_CLOCK_CACHE_CARRYOVER_NOT_EXCLUDED",
    "causal_verdict": "NOT_ESTABLISHED",
    "forbidden_attribution": ["LAZY_MODULE_LOADING", "WDDM", "DRIVER", "RUNTIME"],
    "changes_gate6_or_q0": False,
}


class KernelMemopH2DWarmupDiagnosticError(ValueError):
    """Fail-closed violation of this diagnostic's construction or evidence."""


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    with path.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _artifact(path: Path, root: Path) -> dict[str, Any]:
    return {"name": path.relative_to(root).as_posix(),
            "sha256": _sha256(path), "size_bytes": path.stat().st_size}


def build_pair_arm_argv(nsys: Path, binary: Path, arm: str,
                        arm_output: Path, case_run_id: str) -> list[str]:
    """No measured overrides: native --case/--run-id, then B's warm-up flag."""
    if arm not in ARM_OUTPUT_NAMES:
        raise KernelMemopH2DWarmupDiagnosticError(f"unknown arm: {arm}")
    argv = [str(Path(nsys).resolve()), "profile", "--trace=cuda,nvtx",
            "--capture-range=cudaProfilerApi", "--capture-range-end=stop",
            "--force-overwrite=false", "-o", str((arm_output / "trace").resolve()),
            str(Path(binary).resolve()), "--case", CASE_ID, "--run-id", case_run_id]
    if arm == ARM_B:
        argv.append(WARMUP_FLAG)
    return argv


def classify_pair_outcome(*, overlap_a_ns: int, overlap_b_ns: int,
                          b_terminal_label: str | None, b_terminal_kind: str | None,
                          arms_valid: bool) -> str:
    if not arms_valid:
        return "INVALID_STOP"
    if overlap_a_ns > 0:
        return "CONTROL_OVERLAP_REVIEW"
    if overlap_b_ns <= 0:
        return "NO_OVERLAP_STOP"
    if b_terminal_label == "MEMCPY_B" and b_terminal_kind == "MEMOP":
        return "AMENDMENT_REVIEW_ELIGIBLE"
    return "TERMINAL_MISMATCH_STOP"


def _s_records(manifest_path: Path, canonical_path: Path) -> tuple[dict, list[dict]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (manifest["source"]["canonical_manifest_sha256"] != _sha256(canonical_path)
            or manifest["input_validity"]["status"] != "VALID"):
        raise KernelMemopH2DWarmupDiagnosticError("S lineage/input validity is not VALID")
    entry = manifest["files"]["sync_records"]
    path = (manifest_path.parent / entry["filename"]).resolve()
    if (path.parent != manifest_path.parent.resolve()
            or _sha256(path) != entry["sha256"] or path.stat().st_size != entry["size_bytes"]):
        raise KernelMemopH2DWarmupDiagnosticError("S records hash/size/path failure")
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        records = [json.loads(line) for line in handle]
    if len(records) != entry["record_count"]:
        raise KernelMemopH2DWarmupDiagnosticError("S record count failure")
    return manifest, records


def _nonblocking_stream_provenance(
    trace_sqlite: Path, activities: Mapping[str, Mapping[str, Any]]
) -> dict[str, dict[str, Any]]:
    """Resolve each target stream's CUPTI enum id rather than assuming a raw value."""

    with _open_readonly(trace_sqlite) as connection:
        tables = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        required = {"TARGET_INFO_CUDA_STREAM", "ENUM_CUPTI_STREAM_TYPE"}
        if not required.issubset(tables):
            raise KernelMemopH2DWarmupDiagnosticError(
                f"stream provenance tables missing: {sorted(required - tables)}"
            )
        enum_names: dict[int, str] = {}
        for enum_id, enum_name in connection.execute(
            "SELECT id, name FROM ENUM_CUPTI_STREAM_TYPE"
        ):
            if not isinstance(enum_id, int) or not isinstance(enum_name, str):
                raise KernelMemopH2DWarmupDiagnosticError(
                    "CUPTI stream enum row is not an id/name pair"
                )
            if enum_id in enum_names:
                raise KernelMemopH2DWarmupDiagnosticError(
                    f"CUPTI stream enum id is duplicated: {enum_id}"
                )
            enum_names[enum_id] = enum_name
        if not enum_names:
            raise KernelMemopH2DWarmupDiagnosticError("CUPTI stream enum table is empty")

        provenance: dict[str, dict[str, Any]] = {}
        for label, activity in activities.items():
            process_id = activity.get("process_id")
            if not isinstance(process_id, int):
                raise KernelMemopH2DWarmupDiagnosticError(
                    f"{label}: activity process identity is missing"
                )
            rows = list(
                connection.execute(
                    "SELECT streamId, contextId, flag FROM TARGET_INFO_CUDA_STREAM "
                    "WHERE processId = ? AND contextId = ? AND streamId = ?",
                    (process_id, activity["context_id"], activity["stream_id"]),
                )
            )
            if len(rows) != 1:
                raise KernelMemopH2DWarmupDiagnosticError(
                    f"{label}: target stream row must be unique"
                )
            stream_id, context_id, flag = rows[0]
            if stream_id != activity["stream_id"] or context_id != activity["context_id"]:
                raise KernelMemopH2DWarmupDiagnosticError(
                    f"{label}: target stream identity changed"
                )
            if flag not in enum_names:
                raise KernelMemopH2DWarmupDiagnosticError(
                    f"{label}: stream flag {flag!r} has no unique enum name"
                )
            enum_name = enum_names[flag]
            if enum_name != NON_BLOCKING_STREAM_ENUM_NAME:
                raise KernelMemopH2DWarmupDiagnosticError(
                    f"{label}: stream flag is {enum_name}, not NON_BLOCKING"
                )
            provenance[label] = {
                "process_id": process_id,
                "stream_id": stream_id,
                "context_id": context_id,
                "flag": flag,
                "enum_name": enum_name,
            }
    return provenance


def _analyze_arm_evidence(trace_sqlite: Path, raw_path: Path, output_dir: Path, *,
                         arm: str, case_run_id: str, cuda_visible_device: str,
                         nsys_version: str) -> dict[str, Any]:
    """Immutable Raw/SQLite -> existing Canonical -> existing S, then strict projection."""
    output_dir.mkdir(parents=True)
    source = output_dir / "source_manifest.json"
    _write_json(source, {**_source_manifest(CASE_ID, case_run_id, cuda_visible_device),
                         "diagnostic_only": True, "data_role": "Engineering"})
    input_hashes = {"raw": _sha256(raw_path), "sqlite": _sha256(trace_sqlite)}
    recovered = recover_warmup_diagnostic_marker(trace_sqlite)
    marker = recovered["payload"]
    expected_status = "PASS" if arm == ARM_B else "NOT_APPLICABLE"
    host_ns = marker["warmup_host_ns"]
    if (marker["arm"] != arm or marker["warmup_status"] != expected_status
            or host_ns < 0 or (arm == ARM_A and host_ns != 0)
            or (arm == ARM_B and host_ns <= 0)
            or marker["cuda_module_loading_mode"] not in {"LAZY", "EAGER", "UNKNOWN"}):
        raise KernelMemopH2DWarmupDiagnosticError("warm-up mark arm/status/metadata mismatch")

    canonical_path = convert_sqlite_to_canonical(
        trace_sqlite, output_dir / "canonical_v0_2", "Engineering",
        raw_sha256=input_hashes["raw"], collector_version=nsys_version, source_manifest=source)
    bundle = load_canonical_bundle(canonical_path)
    manifest, records = bundle["manifest"], bundle["records"]
    if (manifest["observation_validity"]["status"] != "valid"
            or manifest["identity"]["status"] != "VALID"):
        raise KernelMemopH2DWarmupDiagnosticError("Canonical observation/identity is not valid")
    requests = [row for row in records["nvtx"]
                if (row.get("structured_identity") or {}).get("kind") == "request"]
    if (len(requests) != 1
            or requests[0]["structured_identity"].get("request_id") != CASE_ID
            or requests[0]["structured_identity"].get("run_id") != case_run_id
            or recovered["nvtx"]["global_tid"] != requests[0]["global_tid"]
            or not isinstance(recovered["nvtx"]["start_ns"], int)
            or recovered["nvtx"]["start_ns"] >= requests[0]["start_ns"]):
        raise KernelMemopH2DWarmupDiagnosticError("diagnostic mark must precede the unique request")
    for row in records["nvtx"]:
        identity = row.get("structured_identity") or {}
        if (identity.get("kind") in {"request", "phase"}
                and row["start_ns"] <= recovered["nvtx"]["start_ns"] < row["end_ns"]):
            raise KernelMemopH2DWarmupDiagnosticError("diagnostic mark lies inside request/phase")

    labels = map_real_activity_labels(records)
    if len(labels) != 2 or set(labels.values()) != {"KERNEL_A", "MEMCPY_B"}:
        raise KernelMemopH2DWarmupDiagnosticError("activity labels must be exactly KERNEL_A/MEMCPY_B")
    by_id = {row["record_id"]: row for row in records["device_activity"]}
    by_label = {labels[key]: value for key, value in by_id.items()}
    kernel, copy = by_label["KERNEL_A"], by_label["MEMCPY_B"]
    if (kernel["activity_kind"] != "KERNEL" or copy["activity_kind"] != "MEMCPY"
            or copy["attributes"]["bytes"] != H2D_BYTES or copy["attributes"]["copy_kind"] != 1
            or copy["attributes"]["src_kind"] != 1 or copy["attributes"]["dst_kind"] != 2
            or kernel["context_id"] != copy["context_id"]
            or kernel["stream_id"] == copy["stream_id"]
            or kernel["device_id"] != 0 or copy["device_id"] != 0):
        raise KernelMemopH2DWarmupDiagnosticError("native pinned 512 MiB H2D/two-stream identity mismatch")
    for activity, api_name in ((kernel, "cudaLaunchKernel"), (copy, "cudaMemcpyAsync")):
        apis = [row for row in records["cuda_api"]
                if row["correlation_id"] == activity["correlation_id"]]
        if (len(apis) != 1 or apis[0]["source_table"] != "CUPTI_ACTIVITY_KIND_RUNTIME"
                or re.sub(r"_v\d+$", "", apis[0]["api_name"]) != api_name):
            raise KernelMemopH2DWarmupDiagnosticError("Runtime/activity mapping is not unique or correct")
    stream_provenance = _nonblocking_stream_provenance(
        trace_sqlite, {"KERNEL_A": kernel, "MEMCPY_B": copy}
    )

    s_path = analyze_canonical_to_s(canonical_path, output_dir / "s_v0_2")
    _, syncs = _s_records(s_path, canonical_path)
    target = [row for row in syncs if row.get("request_id") == CASE_ID]
    if len(target) != 1 or target[0].get("callsite_id") != "S_DEVICE":
        raise KernelMemopH2DWarmupDiagnosticError("S_DEVICE must be the unique request sync")
    sync = target[0]
    wait_ids = sync["wait_set_activity_ids"]
    if (sync["validity"] != "VALID_NONEMPTY" or sync["wait_set_status"] != "VALID_NONEMPTY"
            or sync["sync_kind"] != "DEVICE" or sync["sync_owner_phase"] != "decode"
            or len(wait_ids) != 2 or len(set(wait_ids)) != 2 or set(wait_ids) != set(labels)
            or sync["dependency_edges"]):
        raise KernelMemopH2DWarmupDiagnosticError("S_DEVICE validity/exact wait set/no-event contract failure")
    terminal = sync["terminal"]
    terminal_id = terminal.get("activity_id")
    if (terminal.get("status") != "VALID" or terminal.get("kind") != "ACTIVITY"
            or terminal_id not in wait_ids
            or terminal["end_ns"] != by_id[terminal_id]["end_ns"]):
        raise KernelMemopH2DWarmupDiagnosticError("S_DEVICE terminal is missing/ambiguous/non-unique")
    terminal_activity = by_id[terminal_id]
    measured = summarize_warmup_diagnostic_sqlite(trace_sqlite)
    if (measured["kernel_device_interval"]["correlation_id"] != kernel["correlation_id"]
            or measured["memcpy_device_interval"]["correlation_id"] != copy["correlation_id"]):
        raise KernelMemopH2DWarmupDiagnosticError("Runtime/activity correlation mismatch")
    for interval in (measured["kernel_device_interval"], measured["memcpy_device_interval"]):
        if interval["duration_ns"] <= 0:
            raise KernelMemopH2DWarmupDiagnosticError("nonpositive measured device interval")
    measured["h2d_device_interval"] = measured.pop("memcpy_device_interval")
    measured.pop("descriptive_class")
    semantics = {
        "sync_id": sync["sync_id"], "validity": sync["validity"],
        "wait_set_activity_labels": sorted(labels[key] for key in wait_ids),
        "terminal": terminal, "terminal_label": labels[terminal_id],
        "terminal_kind": "MEMOP" if terminal_activity["activity_kind"] == "MEMCPY" else "KERNEL",
        "terminal_activity_kind": terminal_activity["activity_kind"],
    }
    if input_hashes != {"raw": _sha256(raw_path), "sqlite": _sha256(trace_sqlite)}:
        raise KernelMemopH2DWarmupDiagnosticError("Raw/SQLite changed during read-only analysis")
    return {
        "warmup": {**marker, "warmup_marker_source": recovered["nvtx"]},
        "measured": measured, "semantics": semantics,
        "stream_provenance": stream_provenance,
        "lineage": {"source_manifest": _artifact(source, output_dir),
                    "canonical_manifest": _artifact(canonical_path, output_dir),
                    "s_manifest": _artifact(s_path, output_dir)},
        "raw_trace": {"sha256": input_hashes["raw"], "size_bytes": raw_path.stat().st_size},
        "sqlite": {"sha256": input_hashes["sqlite"], "size_bytes": trace_sqlite.stat().st_size},
    }


def analyze_arm_evidence(trace_sqlite: Path, raw_path: Path, output_dir: Path, *,
                         arm: str, case_run_id: str, cuda_visible_device: str,
                         nsys_version: str) -> dict[str, Any]:
    """Normalize reused readers' errors at this diagnostic's fail-closed boundary."""
    try:
        return _analyze_arm_evidence(trace_sqlite, raw_path, output_dir, arm=arm,
            case_run_id=case_run_id, cuda_visible_device=cuda_visible_device,
            nsys_version=nsys_version)
    except KernelMemopH2DWarmupDiagnosticError:
        raise
    except (ValueError, RuntimeError, OSError, sqlite3.Error, KeyError, TypeError) as exc:
        raise KernelMemopH2DWarmupDiagnosticError(f"{type(exc).__name__}: {exc}") from exc


def run_kernel_memop_h2d_warmup_pair_diagnostic(
    output_dir: Path, binary: Path, nsys: Path, *, run_id: str, cuda_visible_device: str,
    implementation_commit: str, baseline_reference_commit: str = BASELINE_REFERENCE_COMMIT,
    process_runner: ProcessRunner = subprocess.run,
    environment_probe: EnvironmentProbe = _default_environment_probe,
) -> Path:
    """Pre-register then collect A -> B once. Any invalid arm prevents further collection."""
    output, binary, nsys = Path(output_dir).resolve(), Path(binary).resolve(), Path(nsys).resolve()
    if run_id.endswith(SUPERSEDED_RUN_ID_SUFFIX):
        raise KernelMemopH2DWarmupDiagnosticError(
            "warmup-01 is fixed as INVALID_ANALYZER_STREAM_FLAG_ASSUMPTION; "
            "rerun is forbidden and the corrected run-id must use warmup-02"
        )
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise KernelMemopH2DWarmupDiagnosticError(
            "run-id must be q0-win-4090-<date>-kernel-memop-h2d-formalshape-warmup-02"
        )
    if output.exists():
        raise KernelMemopH2DWarmupDiagnosticError("refuse to overwrite an existing diagnostic")
    if (not cuda_visible_device.startswith("GPU-") or "," in cuda_visible_device
            or not binary.is_file() or not nsys.is_file()):
        raise KernelMemopH2DWarmupDiagnosticError("a single GPU UUID and existing binary/nsys are required")
    if (not re.fullmatch(r"[0-9a-f]{40}", implementation_commit)
            or baseline_reference_commit != BASELINE_REFERENCE_COMMIT):
        raise KernelMemopH2DWarmupDiagnosticError("explicit implementation SHA/frozen baseline reference required")
    output.mkdir(parents=True)
    source_root = Path(__file__).resolve().parents[1]
    source_paths = ["q0/cuda/exposedpath_q0.cu", "exposedpath_v141/cli.py",
                    "exposedpath_v141/q0_kernel_memop_h2d_warmup_diagnostic.py",
                    "exposedpath_v141/q0_kernel_memop_d2h_warmup_diagnostic.py",
                    "exposedpath_v141/canonical_raw.py", "exposedpath_v141/sync_semantics.py",
                    "exposedpath_v141/s_bundle.py"]
    frozen_hashes = {path: _sha256(source_root / path) for path in source_paths}
    tool_hashes = {"binary": _sha256(binary), "nsys": _sha256(nsys)}
    case_ids = {arm: f"{run_id}.{'a' if arm == ARM_A else 'b'}.{CASE_ID.lower()}"
                for arm in (ARM_A, ARM_B)}
    commands = {arm: build_pair_arm_argv(nsys, binary, arm, output / ARM_OUTPUT_NAMES[arm], case_ids[arm])
                for arm in (ARM_A, ARM_B)}
    plan = {
        "schema_version": "exposedpath-h2d-formalshape-pair-plan/0.1.0",
        "status": "PRE_REGISTERED_NOT_EXECUTED", "run_id": run_id,
        "data_role": "Engineering", "q0_status": "NOT_RUN", "gate6_verdict": "FAIL",
        "implementation_commit": implementation_commit, "baseline_reference_commit": baseline_reference_commit,
        "source_hashes": frozen_hashes, "tool_hashes": tool_hashes,
        "construction": {"measured_path": "NATIVE_Q0_DEFAULT_NO_OVERRIDES",
                         "h2d_size_bytes": H2D_BYTES, "kernel_ms": KERNEL_MS,
                         "warmup_kernel_ms": WARMUP_KERNEL_MS, "warmup_stream": "KERNEL_STREAM",
                         "warmup_interleave": "OUTSIDE_CAPTURE_RANGE"},
        "metadata_transport": METADATA_TRANSPORT, "execution_order": [ARM_A, ARM_B],
        "prior_run_disposition": PRIOR_RUN_DISPOSITION,
        "command_argv": commands, "outcome_policy": OUTCOME_POLICY,
        "preregistered_rules": ["EACH_ARM_ONCE", "NO_RETRY", "NO_PARAMETER_TUNING",
                                 "S_DEVICE_VALID_NONEMPTY_EXACT_KERNEL_A_MEMCPY_B",
                                 "CANONICAL_TO_S_ONLY_NO_AB_OR_EVALUATOR"],
        "interpretation_boundary": INTERPRETATION_BOUNDARY,
        "research_eligibility": ELIGIBILITY,
    }
    _write_json(output / "pair_plan.json", plan)
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = cuda_visible_device
    arms, snapshots = [], []
    failed_arm, failure = None, None
    for arm in (ARM_A, ARM_B):
        failed_arm = arm
        try:
            snapshot = dict(environment_probe(binary, nsys, cuda_visible_device, process_runner))
            _validate_environment(snapshot, cuda_visible_device)
            if ("RTX 4090" not in snapshot["selected_gpu"]["name"]
                    or "Windows" not in snapshot["os"]):
                raise KernelMemopH2DWarmupDiagnosticError("diagnostic is restricted to Windows/RTX4090")
            if snapshots and snapshot != snapshots[0]:
                raise KernelMemopH2DWarmupDiagnosticError("arm environments differ")
            snapshots.append(snapshot)
            if tool_hashes != {"binary": _sha256(binary), "nsys": _sha256(nsys)}:
                raise KernelMemopH2DWarmupDiagnosticError("binary/nsys hash changed")
            arm_dir = output / ARM_OUTPUT_NAMES[arm]
            arm_dir.mkdir()
            result = _run_text(process_runner, commands[arm], environment=env)
            (arm_dir / "collection_stdout.txt").write_text(result.stdout or "", encoding="utf-8")
            (arm_dir / "collection_stderr.txt").write_text(result.stderr or "", encoding="utf-8")
            raw, sqlite = arm_dir / "trace.nsys-rep", arm_dir / "trace.sqlite"
            if result.returncode or not raw.is_file() or raw.stat().st_size == 0:
                raise KernelMemopH2DWarmupDiagnosticError("collection failed/nonempty Raw missing")
            exported = _run_text(process_runner, build_pair_export_argv(nsys, sqlite, raw), environment=env)
            (arm_dir / "export_stdout.txt").write_text(exported.stdout or "", encoding="utf-8")
            (arm_dir / "export_stderr.txt").write_text(exported.stderr or "", encoding="utf-8")
            if exported.returncode or not sqlite.is_file():
                raise KernelMemopH2DWarmupDiagnosticError("SQLite export failed")
            evidence = analyze_arm_evidence(sqlite, raw, arm_dir / "analysis_v0_1", arm=arm,
                case_run_id=case_ids[arm], cuda_visible_device=cuda_visible_device,
                nsys_version=snapshot["nsight_systems"])
            if (tool_hashes != {"binary": _sha256(binary), "nsys": _sha256(nsys)}
                    or frozen_hashes != {path: _sha256(source_root / path) for path in source_paths}):
                raise KernelMemopH2DWarmupDiagnosticError("implementation/tool hash changed during arm")
            record = {"arm": arm, "run_id": case_ids[arm], "command_argv": commands[arm],
                      "environment": snapshot, "source": tool_hashes,
                      "research_eligibility": ELIGIBILITY, **evidence}
            _write_json(arm_dir / "diagnostic_manifest.json", record)
            arms.append(record)
        except (ValueError, RuntimeError, OSError, KeyError, TypeError) as exc:
            failure = f"{type(exc).__name__}: {exc}"
            break
    if failure is None:
        failed_arm = None
        if arms[0]["warmup"]["cuda_module_loading_mode"] != arms[1]["warmup"]["cuda_module_loading_mode"]:
            failure = "module loading mode differs between arms"
    outcome = classify_pair_outcome(
        overlap_a_ns=arms[0]["measured"]["overlap_ns"] if arms else 0,
        overlap_b_ns=arms[1]["measured"]["overlap_ns"] if len(arms) == 2 else 0,
        b_terminal_label=arms[1]["semantics"]["terminal_label"] if len(arms) == 2 else None,
        b_terminal_kind=arms[1]["semantics"]["terminal_kind"] if len(arms) == 2 else None,
        arms_valid=failure is None and len(arms) == 2)
    receipt = {
        "schema_version": "exposedpath-h2d-formalshape-pair-receipt/0.1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id, "implementation_commit": implementation_commit,
        "baseline_reference_commit": baseline_reference_commit,
        "status": "INVALID_STOP" if failure else "COLLECTED_AND_ANALYZED",
        "data_role": "Engineering", "diagnostic_only": True,
        "gate6_verdict": "FAIL", "q0_status": "NOT_RUN", "arms": arms,
        "failed_arm": failed_arm, "failure": failure,
        "prior_run_disposition": PRIOR_RUN_DISPOSITION,
        "source_hashes": frozen_hashes, "tool_hashes": tool_hashes,
        "plan": _artifact(output / "pair_plan.json", output),
        "pair_interpretation": {"outcome": outcome, "arms_valid": failure is None and len(arms) == 2,
                                "policy": OUTCOME_POLICY[outcome], "changes_gate6_or_q0": False},
        "interpretation_boundary": INTERPRETATION_BOUNDARY,
        "research_eligibility": ELIGIBILITY,
    }
    receipt_path = output / "pair_receipt.json"
    _write_json(receipt_path, receipt)
    return receipt_path
