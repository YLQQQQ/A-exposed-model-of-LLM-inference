"""隔离的 64 MiB D2H / 10 ms kernel Engineering diagnostic。"""

from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from .q0_collection import (
    _default_environment_probe,
    _run_text,
    _sha256,
    _validate_environment,
)


CASE_ID = "Q0-KERNEL-MEMOP-001"
DIAGNOSTIC_D2H_BYTES = 64 * 1024 * 1024
DIAGNOSTIC_KERNEL_MS = 10
RUN_ID_PATTERN = re.compile(
    r"q0-win-4090-\d{8}-kernel-memop-d2h-diag-64m-10ms-\d{2}"
)

ProcessRunner = Callable[..., subprocess.CompletedProcess[str]]
EnvironmentProbe = Callable[..., Mapping[str, Any]]


class KernelMemopD2HDiagnosticError(RuntimeError):
    """KERNEL-MEMOP D2H 方向诊断的输入或产物合同不满足要求。"""


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _parameters() -> dict[str, Any]:
    return {
        "copy_direction": "DEVICE_TO_HOST",
        "d2h_size_bytes": DIAGNOSTIC_D2H_BYTES,
        "d2h_size_mib": 64,
        "kernel_duration_ms": DIAGNOSTIC_KERNEL_MS,
    }


def build_kernel_memop_d2h_diagnostic_argv(
    nsys: Path, binary: Path, trace_prefix: Path, case_run_id: str
) -> list[str]:
    """构造不含 WDDM、且不会进入正常 Q0 manifest 的 D2H 诊断命令。"""

    return [
        str(Path(nsys).resolve()),
        "profile",
        "--trace=cuda,nvtx",
        "--capture-range=cudaProfilerApi",
        "--capture-range-end=stop",
        "--force-overwrite=false",
        "-o",
        str(Path(trace_prefix).resolve()),
        str(Path(binary).resolve()),
        "--case",
        CASE_ID,
        "--run-id",
        case_run_id,
        "--diagnostic-d2h-bytes",
        str(DIAGNOSTIC_D2H_BYTES),
        "--diagnostic-kernel-ms",
        str(DIAGNOSTIC_KERNEL_MS),
    ]


def run_kernel_memop_d2h_diagnostic(
    output_dir: Path,
    binary: Path,
    nsys: Path,
    *,
    run_id: str,
    cuda_visible_device: str,
    process_runner: ProcessRunner = subprocess.run,
    environment_probe: EnvironmentProbe = _default_environment_probe,
) -> Path:
    """采集并导出一个不可覆盖的 64 MiB D2H/10 ms Engineering diagnostic。"""

    output = Path(output_dir).resolve()
    binary_path = Path(binary).resolve()
    nsys_path = Path(nsys).resolve()
    if output.exists():
        raise KernelMemopD2HDiagnosticError(f"拒绝覆盖已有 D2H diagnostic: {output}")
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise KernelMemopD2HDiagnosticError(
            "run-id 必须匹配 kernel-memop-d2h-diag-64m-10ms-NN"
        )
    if not cuda_visible_device or "," in cuda_visible_device:
        raise KernelMemopD2HDiagnosticError("D2H diagnostic 必须绑定唯一 GPU")
    if not binary_path.is_file():
        raise KernelMemopD2HDiagnosticError(f"Q0 binary 不存在: {binary_path}")
    if not nsys_path.is_file():
        raise KernelMemopD2HDiagnosticError(f"nsys 不存在: {nsys_path}")

    output.mkdir(parents=True)
    environment = os.environ.copy()
    environment["CUDA_VISIBLE_DEVICES"] = cuda_visible_device
    case_run_id = f"{run_id}.{CASE_ID.lower()}"
    parameters = _parameters()
    source_manifest = {
        "cuda_visible_device": cuda_visible_device,
        "default_stream_mode": "PER_THREAD",
        "diagnostic_parameters": parameters,
        "experiment_id": "exposedpath-q0",
        "gpu_index": 0,
        "pass_id": "Pass1",
        "q0_case_id": CASE_ID,
        "q0_status": "NOT_RUN",
        "repeat_id": "repeat-0",
        "run_id": case_run_id,
        "run_role": "Engineering",
        "selected_device_id": 0,
        "wmpc_id": "q0-controlled",
    }
    source_manifest_path = output / "source_manifest.json"
    _write_json(source_manifest_path, source_manifest)

    snapshot = dict(
        environment_probe(binary_path, nsys_path, cuda_visible_device, process_runner)
    )
    _validate_environment(snapshot, cuda_visible_device)
    trace_prefix = output / "trace"
    collection_argv = build_kernel_memop_d2h_diagnostic_argv(
        nsys_path, binary_path, trace_prefix, case_run_id
    )
    eligibility = {
        "formal_evidence": False,
        "q0_status": "NOT_RUN",
        "scope": "KERNEL_MEMOP_D2H_ENGINEERING_DIAGNOSTIC_ONLY",
    }
    decision_policy = {
        "primary_measure": "device_interval_overlap_ns",
        "overlap_observed_if": "overlap_ns > 0",
        "terminal_required_for_direction_diagnostic": False,
        "on_overlap_zero": "STOP",
        "on_overlap_positive": "STOP_AND_REVIEW",
        "causal_verdict": "NOT_ESTABLISHED",
    }
    source = {
        "binary": {"path": str(binary_path), "sha256": _sha256(binary_path)},
        "nsys": {"path": str(nsys_path), "sha256": _sha256(nsys_path)},
        "source_manifest": {
            "name": source_manifest_path.name,
            "sha256": _sha256(source_manifest_path),
        },
    }
    manifest = {
        "schema_version": "exposedpath-q0-kernel-memop-d2h-diagnostic-run/0.1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PREPARED_NOT_EXECUTED",
        "data_role": "Engineering",
        "diagnostic_only": True,
        "q0_status": "NOT_RUN",
        "run_id": run_id,
        "case_id": CASE_ID,
        "diagnostic_parameters": parameters,
        "command_argv": collection_argv,
        "source": source,
        "research_eligibility": eligibility,
        "decision_policy": decision_policy,
    }
    _write_json(output / "diagnostic_manifest.json", manifest)

    completed = _run_text(process_runner, collection_argv, environment=environment)
    (output / "collection_stdout.txt").write_text(
        completed.stdout or "", encoding="utf-8"
    )
    (output / "collection_stderr.txt").write_text(
        completed.stderr or "", encoding="utf-8"
    )
    raw_path = trace_prefix.with_suffix(".nsys-rep")
    if completed.returncode != 0:
        _write_json(
            output / "diagnostic_failure.json",
            {"stage": "COLLECTION", "returncode": completed.returncode},
        )
        raise KernelMemopD2HDiagnosticError(
            f"D2H diagnostic 采集失败 ({completed.returncode})"
        )
    if not raw_path.is_file() or raw_path.stat().st_size <= 0:
        raise KernelMemopD2HDiagnosticError("Nsight 成功返回但未生成非空 Raw trace")

    sqlite_path = output / "trace.sqlite"
    export_argv = [
        str(nsys_path),
        "export",
        "--type",
        "sqlite",
        "--lazy=false",
        "--force-overwrite=false",
        "--output",
        str(sqlite_path),
        str(raw_path),
    ]
    exported = _run_text(process_runner, export_argv, environment=environment)
    (output / "export_stdout.txt").write_text(
        exported.stdout or "", encoding="utf-8"
    )
    (output / "export_stderr.txt").write_text(
        exported.stderr or "", encoding="utf-8"
    )
    if exported.returncode != 0 or not sqlite_path.is_file():
        _write_json(
            output / "diagnostic_failure.json",
            {"stage": "SQLITE_EXPORT", "returncode": exported.returncode},
        )
        raise KernelMemopD2HDiagnosticError("D2H diagnostic SQLite 导出失败")

    receipt = {
        "schema_version": "exposedpath-q0-kernel-memop-d2h-diagnostic-receipt/0.1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "COLLECTED_AND_EXPORTED",
        "data_role": "Engineering",
        "diagnostic_only": True,
        "q0_status": "NOT_RUN",
        "run_id": run_id,
        "case_id": CASE_ID,
        "diagnostic_parameters": parameters,
        "command_argv": collection_argv,
        "export_argv": export_argv,
        "environment": snapshot,
        "source": source,
        "raw_trace": {
            "name": raw_path.name,
            "size_bytes": raw_path.stat().st_size,
            "sha256": _sha256(raw_path),
        },
        "sqlite": {
            "name": sqlite_path.name,
            "size_bytes": sqlite_path.stat().st_size,
            "sha256": _sha256(sqlite_path),
        },
        "research_eligibility": eligibility,
        "decision_policy": decision_policy,
    }
    receipt_path = output / "diagnostic_receipt.json"
    _write_json(receipt_path, receipt)
    return receipt_path
