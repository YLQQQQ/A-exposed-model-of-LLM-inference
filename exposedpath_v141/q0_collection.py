"""逐 case 执行真实 Q0 采集，并写入不可覆盖的 Engineering receipt。"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .q0_execution import (
    LEGACY_RUN_SCHEMA_VERSION,
    MEASUREMENT_INITIALIZATION_FIELD,
    MEASUREMENT_INITIALIZATION_FLAG,
    MEASUREMENT_INITIALIZATIONS,
    RUN_SCHEMA_VERSION,
)


class Q0CollectionError(RuntimeError):
    """真实采集计划、环境或产物不满足 fail-closed 要求。"""


ProcessRunner = Callable[..., subprocess.CompletedProcess[str]]
EnvironmentProbe = Callable[..., Mapping[str, Any]]

# 正式 run 由 execution path 产出 `0.2.1`；同时兼容读取历史 `0.2.0` run manifest。
SUPPORTED_RUN_SCHEMA_VERSIONS = frozenset(
    {LEGACY_RUN_SCHEMA_VERSION, RUN_SCHEMA_VERSION}
)


def _normalize_gpu_uuid(value: Any) -> str:
    normalized = str(value).strip().upper()
    if normalized.startswith("GPU-"):
        return "GPU-" + normalized[4:].replace("-", "")
    return normalized


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _inside(path: Path, root: Path, label: str) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise Q0CollectionError(f"{label} 越出 Q0 run 目录") from exc
    return resolved


def _run_text(
    runner: ProcessRunner, argv: Sequence[str], *, environment: Mapping[str, str]
) -> subprocess.CompletedProcess[str]:
    return runner(
        list(argv),
        env=dict(environment),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _default_environment_probe(
    binary: Path,
    nsys: Path,
    selector: str,
    runner: ProcessRunner,
) -> Mapping[str, Any]:
    environment = os.environ.copy()
    environment["CUDA_VISIBLE_DEVICES"] = selector
    gpu = _run_text(runner, [str(binary), "--environment-json"], environment=environment)
    if gpu.returncode != 0:
        raise Q0CollectionError(
            f"GPU 环境探测失败 ({gpu.returncode}): {(gpu.stdout + gpu.stderr).strip()}"
        )
    try:
        payload = json.loads(gpu.stdout)
    except json.JSONDecodeError as exc:
        raise Q0CollectionError("GPU 环境探测未返回合法 JSON") from exc
    if not isinstance(payload, Mapping):
        raise Q0CollectionError("GPU 环境探测结果必须是对象")
    nsys_result = _run_text(runner, [str(nsys), "--version"], environment=environment)
    if nsys_result.returncode != 0:
        raise Q0CollectionError("Nsight Systems 版本探测失败")
    selected = {
        "physical_index": int(selector) if selector.isdigit() else None,
        "logical_index": 0,
        "uuid": payload.get("uuid"),
        "name": payload.get("name"),
        "memory_total_mib": payload.get("memory_total_mib"),
        "async_engine_count": payload.get("async_engine_count"),
        "device_overlap": payload.get("device_overlap"),
        "concurrent_kernels": payload.get("concurrent_kernels"),
    }
    return {
        "selected_gpu": selected,
        "driver_version": payload.get("driver_version"),
        "cuda_driver_version": payload.get("cuda_driver_version"),
        "cuda_runtime_version": payload.get("cuda_runtime_version"),
        "nsight_systems": (nsys_result.stdout + nsys_result.stderr).strip(),
        "os": platform.platform(),
    }


def _validate_environment(snapshot: Mapping[str, Any], selector: str) -> None:
    required = {
        "selected_gpu",
        "driver_version",
        "cuda_driver_version",
        "cuda_runtime_version",
        "nsight_systems",
        "os",
    }
    missing = sorted(
        field for field in required
        if snapshot.get(field) is None or snapshot.get(field) == ""
    )
    selected = snapshot.get("selected_gpu")
    if not isinstance(selected, Mapping):
        missing.append("selected_gpu")
    else:
        for field in (
            "logical_index",
            "uuid",
            "name",
            "memory_total_mib",
            "async_engine_count",
            "device_overlap",
            "concurrent_kernels",
        ):
            if selected.get(field) in {None, ""}:
                missing.append(f"selected_gpu.{field}")
        if selected.get("logical_index") != 0:
            raise Q0CollectionError("Q0 binary 必须运行在过滤后的逻辑设备 0")
        if (
            selector.upper().startswith("GPU-")
            and _normalize_gpu_uuid(selected.get("uuid", ""))
            != _normalize_gpu_uuid(selector)
        ):
            raise Q0CollectionError("GPU UUID 与 CUDA_VISIBLE_DEVICES 选择不一致")
    if missing:
        raise Q0CollectionError(f"环境证据缺失: {sorted(set(missing))}")


def execute_q0_case(
    run_manifest: Path,
    case_id: str,
    *,
    process_runner: ProcessRunner = subprocess.run,
    environment_probe: EnvironmentProbe = _default_environment_probe,
) -> Path:
    """执行一个 native seed；Raw、日志和 receipt 均拒绝覆盖。"""

    manifest_path = Path(run_manifest).resolve()
    root = manifest_path.parent
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Q0CollectionError(f"Q0 run manifest 无法读取: {exc}") from exc
    run_schema_version = manifest.get("schema_version")
    if run_schema_version not in SUPPORTED_RUN_SCHEMA_VERSIONS:
        raise Q0CollectionError("Q0 run manifest schema 不受支持")
    if manifest.get("status") != "PREPARED_NOT_EXECUTED":
        raise Q0CollectionError("Q0 run manifest 不是可执行的预备状态")
    cases = [case for case in manifest.get("cases", []) if case.get("case_id") == case_id]
    if len(cases) != 1:
        raise Q0CollectionError(f"case identity 不唯一或不存在: {case_id}")
    case = cases[0]
    argv = case.get("command_argv")
    if not isinstance(argv, list) or not argv:
        raise Q0CollectionError(f"{case_id} 没有原生采集命令")

    binary = Path(manifest["source"]["binary"]["path"]).resolve()
    nsys = Path(manifest["source"]["nsys"]["path"]).resolve()
    for label, path in (("binary", binary), ("nsys", nsys)):
        if not path.is_file() or _sha256(path) != manifest["source"][label]["sha256"]:
            raise Q0CollectionError(f"{label} 文件缺失或哈希不一致")
    if argv[0] != str(nsys) or str(binary) not in argv:
        raise Q0CollectionError("采集 argv 与已哈希工具不一致")
    if run_schema_version == RUN_SCHEMA_VERSION:
        # 正式 run：argv 必须携带与 manifest policy 逐字一致的初始化 policy，
        # 否则一份“缺少 measurement initialization”的正式采集会被静默当作合法证据。
        policy = case.get(MEASUREMENT_INITIALIZATION_FIELD)
        if policy not in MEASUREMENT_INITIALIZATIONS:
            raise Q0CollectionError(
                f"run 0.2.1 case 缺少显式 measurement initialization: {case_id}"
            )
        marker_positions = [
            index for index, token in enumerate(argv)
            if token == MEASUREMENT_INITIALIZATION_FLAG
        ]
        if (
            len(marker_positions) != 1
            or marker_positions[0] + 1 >= len(argv)
            or argv[marker_positions[0] + 1] != policy
        ):
            raise Q0CollectionError(
                f"{case_id} 采集 argv 的 measurement initialization 与 manifest policy 不一致"
            )

    source_manifest = _inside(root / case["source_manifest"], root, "source manifest")
    if not source_manifest.is_file() or _sha256(source_manifest) != case["source_manifest_sha256"]:
        raise Q0CollectionError("source manifest 缺失或哈希不一致")
    case_dir = source_manifest.parent
    trace_prefix = _inside(Path(case["trace_prefix"]), root, "trace prefix")
    raw_path = trace_prefix.with_suffix(".nsys-rep")
    receipt_path = case_dir / "collection_receipt.json"
    failure_path = case_dir / "collection_failure.json"
    stdout_path = case_dir / "collection_stdout.txt"
    stderr_path = case_dir / "collection_stderr.txt"
    if any(path.exists() for path in (raw_path, receipt_path, failure_path, stdout_path, stderr_path)):
        raise Q0CollectionError(f"拒绝覆盖已有 case 采集证据: {case_id}")

    selector = str(manifest.get("gpu_selection", {}).get("cuda_visible_device", ""))
    snapshot = dict(environment_probe(binary, nsys, selector, process_runner))
    _validate_environment(snapshot, selector)
    environment = os.environ.copy()
    environment["CUDA_VISIBLE_DEVICES"] = selector
    completed = _run_text(process_runner, argv, environment=environment)
    stdout_path.write_text(completed.stdout or "", encoding="utf-8")
    stderr_path.write_text(completed.stderr or "", encoding="utf-8")
    if completed.returncode != 0:
        failure = {
            "schema_version": "exposedpath-q0-collection-failure/0.2.0",
            "status": "COLLECTION_FAILED",
            "case_id": case_id,
            "returncode": completed.returncode,
            "q0_status": "NOT_RUN",
        }
        failure_path.write_text(json.dumps(failure, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        raise Q0CollectionError(f"Q0 采集失败 ({completed.returncode}): {case_id}")
    if not raw_path.is_file() or raw_path.stat().st_size <= 0:
        raise Q0CollectionError("Nsight 返回成功但未生成唯一非空 Raw trace")
    extras = [path for path in case_dir.glob(f"{trace_prefix.name}*.nsys-rep") if path != raw_path]
    if extras:
        raise Q0CollectionError("Nsight 生成多个 Raw trace，无法确定 identity")
    receipt = {
        "schema_version": "exposedpath-q0-collection/0.2.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "COLLECTED",
        "data_role": "Engineering",
        "q0_status": "NOT_RUN",
        "case_id": case_id,
        "run_id": manifest["run_id"],
        "command_argv": argv,
        "returncode": completed.returncode,
        "environment": snapshot,
        "source_manifest": {
            "name": source_manifest.name,
            "sha256": _sha256(source_manifest),
        },
        "raw_trace": {
            "name": raw_path.name,
            "size_bytes": raw_path.stat().st_size,
            "sha256": _sha256(raw_path),
        },
        "research_eligibility": {
            "formal_evidence": False,
            "scope": "Q0_REAL_COLLECTION_ONLY",
        },
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt_path
