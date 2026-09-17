"""独立的 Q0 KERNEL-MEMOP WDDM Engineering diagnostic。

该模块不参与正常 Q0 collection。WDDM packet 没有 CUDA correlationId，输出只提供
PID/context/engine/time-window 下的时间线归属推断，永不生成硬件根因结论。
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
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


STRUCTURED_NVTX_PREFIX = "EXPOSEDPATH_JSON_V1:"
CASE_ID = "Q0-KERNEL-MEMOP-001"
ATTRIBUTION_SEMANTICS = "PID_CONTEXT_ENGINE_TIME_WINDOW_INFERENCE_ONLY"
RUN_ID_PATTERN = re.compile(
    r"q0-win-4090-\d{8}-kernel-memop-wddm-diag-\d{2}"
)
REQUIRED_HELP_OPTIONS = (
    "wddm",
    "--wddm-additional-events",
    "--wddm-memory-trace",
    "--wddm-backtraces",
)

ProcessRunner = Callable[..., subprocess.CompletedProcess[str]]
EnvironmentProbe = Callable[..., Mapping[str, Any]]
HagsProbe = Callable[[], Mapping[str, Any]]


class WDDMDiagnosticError(RuntimeError):
    """WDDM diagnostic 输入、范围或证据合同不满足要求。"""


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _default_hags_probe() -> Mapping[str, Any]:
    result: dict[str, Any] = {
        "registry_path": r"HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers",
        "value_name": "HwSchMode",
        "raw_value": None,
        "status": "UNRESOLVED",
        "evidence_scope": "REGISTRY_CONFIGURATION_ONLY",
    }
    if os.name != "nt":
        result["reason"] = "NON_WINDOWS_HOST"
        return result
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers",
        ) as key:
            value, value_type = winreg.QueryValueEx(key, "HwSchMode")
        result["raw_value"] = value
        result["registry_value_type"] = value_type
        if value == 2:
            result["status"] = "ENABLED"
        elif value == 1:
            result["status"] = "DISABLED"
        else:
            result["reason"] = "UNRECOGNIZED_OR_SYSTEM_DEFAULT_VALUE"
    except FileNotFoundError:
        result["reason"] = "REGISTRY_VALUE_ABSENT_SYSTEM_DEFAULT_UNRESOLVED"
    except OSError as exc:
        result["reason"] = f"REGISTRY_READ_FAILED: {exc}"
    return result


def _global_parts(global_id: int | None) -> tuple[int | None, int | None]:
    if global_id is None:
        return None, None
    value = int(global_id)
    return (value >> 24) & 0xFFFFFF, value & 0xFFFFFF


def build_wddm_collection_argv(
    nsys: Path, binary: Path, trace_prefix: Path, case_run_id: str
) -> list[str]:
    """构造只属于独立 Engineering diagnostic 的 Nsight argv。"""

    return [
        str(Path(nsys).resolve()),
        "profile",
        "--trace=cuda,nvtx,wddm",
        "--wddm-additional-events=true",
        "--wddm-memory-trace=false",
        "--wddm-backtraces=false",
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
    ]


def _table_names(connection: sqlite3.Connection) -> set[str]:
    return {
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }


def _columns(connection: sqlite3.Connection, table: str) -> set[str]:
    escaped = table.replace('"', '""')
    return {
        str(row[1])
        for row in connection.execute(f'PRAGMA table_info("{escaped}")')
    }


def _target_request(
    connection: sqlite3.Connection,
    source_manifest: Mapping[str, Any],
    tables: set[str],
) -> dict[str, Any]:
    if not {"NVTX_EVENTS", "StringIds"}.issubset(tables):
        return {"status": "UNRESOLVED", "reason": "NVTX_TABLE_UNUSABLE"}
    identity_fields = (
        "experiment_id",
        "wmpc_id",
        "run_id",
        "run_role",
        "pass_id",
        "repeat_id",
    )
    matching: list[dict[str, Any]] = []
    for rowid, start, end, text, global_tid in connection.execute(
        """
        SELECT n.rowid, n.start, n.end, COALESCE(n.text, s.value, ''), n.globalTid
        FROM NVTX_EVENTS AS n
        LEFT JOIN StringIds AS s ON s.id = n.textId
        ORDER BY n.start, n.rowid
        """
    ):
        label = str(text)
        if not label.startswith(STRUCTURED_NVTX_PREFIX):
            continue
        try:
            payload = json.loads(label[len(STRUCTURED_NVTX_PREFIX) :])
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict) or payload.get("kind") != "request":
            continue
        if (
            payload.get("request_id") == source_manifest.get("q0_case_id")
            and payload.get("phase") == "full_request"
            and all(
                payload.get(field) == source_manifest.get(field)
                for field in identity_fields
            )
            and isinstance(start, int)
            and isinstance(end, int)
            and end >= start
        ):
            process_id, thread_id = _global_parts(global_tid)
            matching.append(
                {
                    "source_rowid": rowid,
                    "start_ns": start,
                    "end_ns": end,
                    "global_tid": global_tid,
                    "process_id": process_id,
                    "thread_id": thread_id,
                }
            )
    if len(matching) != 1:
        return {
            "status": "UNRESOLVED",
            "reason": "TARGET_REQUEST_NOT_UNIQUE",
            "matching_request_count": len(matching),
        }
    return {"status": "RESOLVED", **matching[0]}


def _lookup_labels(
    connection: sqlite3.Connection, tables: set[str], table: str
) -> dict[int, str]:
    if table not in tables:
        return {}
    return {
        int(row[0]): str(row[1])
        for row in connection.execute(f'SELECT id, label FROM "{table}"')
    }


def _context_labels(
    connection: sqlite3.Connection, tables: set[str]
) -> dict[tuple[int, int], str]:
    if "TARGET_INFO_WDDM_CONTEXTS" not in tables:
        return {}
    return {
        (int(row[0]), int(row[1])): str(row[2])
        for row in connection.execute(
            "SELECT context, engineType, friendlyName FROM TARGET_INFO_WDDM_CONTEXTS"
        )
    }


def summarize_wddm_sqlite(
    sqlite_path: Path,
    *,
    source_manifest: Mapping[str, Any],
    hags: Mapping[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """生成中立 WDDM 时间线摘要；不建立 CUDA↔packet 严格映射。"""

    if source_manifest.get("run_role") != "Engineering":
        raise WDDMDiagnosticError("WDDM diagnostic 只允许 Engineering 数据")
    if source_manifest.get("q0_case_id") != CASE_ID:
        raise WDDMDiagnosticError("WDDM diagnostic 只允许 Q0 KERNEL-MEMOP case")
    path = Path(sqlite_path).resolve()
    if not path.is_file():
        raise WDDMDiagnosticError(f"SQLite 不存在: {path}")

    uri = f"file:{path.as_posix()}?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        tables = _table_names(connection)
        request = _target_request(connection, source_manifest, tables)
        wddm_tables = sorted(
            table for table in tables if table.startswith("WDDM_")
        )
        packet_tables = [
            table
            for table in wddm_tables
            if "QUEUE_PACKET" in table or "DMA_PACKET" in table
        ]
        table_counts = {
            table: int(connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])
            for table in wddm_tables
        }
        engine_labels = _lookup_labels(
            connection, tables, "ENUM_WDDM_ENGINE_TYPE"
        )
        packet_labels = _lookup_labels(
            connection, tables, "ENUM_WDDM_PACKET_TYPE"
        )
        context_labels = _context_labels(connection, tables)
        timeline: list[dict[str, Any]] = []
        if request.get("status") == "RESOLVED":
            request_pid = request.get("process_id")
            for table in packet_tables:
                columns = _columns(connection, table)
                if not {"start", "globalTid"}.issubset(columns):
                    continue
                wanted = [
                    name
                    for name in (
                        "start", "end", "globalTid", "gpu", "context",
                        "engineType", "packetType", "submitSequence",
                        "ulQueueSubmitSequence", "queuePacket", "dmaBuffer",
                    )
                    if name in columns
                ]
                query = ", ".join(f'"{name}"' for name in wanted)
                for source_rowid, *values in connection.execute(
                    f'SELECT rowid, {query} FROM "{table}" ORDER BY start, rowid'
                ):
                    row = dict(zip(wanted, values, strict=True))
                    process_id, thread_id = _global_parts(row.get("globalTid"))
                    start_ns = int(row["start"])
                    end_ns = int(row.get("end") or start_ns)
                    if process_id != request_pid:
                        continue
                    if not (
                        start_ns < int(request["end_ns"])
                        and end_ns >= int(request["start_ns"])
                    ):
                        continue
                    engine_type = row.get("engineType")
                    packet_type = row.get("packetType")
                    context = row.get("context")
                    timeline.append(
                        {
                            "table": table,
                            "source_rowid": source_rowid,
                            "start_ns": start_ns,
                            "end_ns": end_ns,
                            "global_tid": row.get("globalTid"),
                            "process_id": process_id,
                            "thread_id": thread_id,
                            "gpu": row.get("gpu"),
                            "context": context,
                            "context_label": context_labels.get(
                                (int(context), int(engine_type))
                            )
                            if context is not None and engine_type is not None
                            else None,
                            "engine_type": engine_type,
                            "engine_label": engine_labels.get(int(engine_type))
                            if engine_type is not None
                            else None,
                            "packet_type": packet_type,
                            "packet_label": packet_labels.get(int(packet_type))
                            if packet_type is not None
                            else None,
                            "submit_sequence": row.get(
                                "submitSequence", row.get("ulQueueSubmitSequence")
                            ),
                            "queue_packet": row.get("queuePacket"),
                            "dma_buffer": row.get("dmaBuffer"),
                            "attribution": ATTRIBUTION_SEMANTICS,
                        }
                    )

    reasons: list[str] = []
    if hags.get("status") != "ENABLED":
        reasons.append("HAGS_NOT_CONFIRMED_ENABLED")
    if request.get("status") != "RESOLVED":
        reasons.append(str(request.get("reason", "TARGET_REQUEST_UNRESOLVED")))
    if not wddm_tables or not any(table_counts.values()):
        reasons.append("WDDM_TABLES_EMPTY")
    if not timeline:
        reasons.append("NO_TARGET_WDDM_PACKET_IN_REQUEST")

    summary = {
        "schema_version": "exposedpath-q0-wddm-diagnostic/0.1.0",
        "data_role": "Engineering",
        "diagnostic_only": True,
        "case_id": CASE_ID,
        "evidence_status": (
            "EVIDENCE_INSUFFICIENT" if reasons else "TIMELINE_ATTRIBUTION_AVAILABLE"
        ),
        "insufficient_reasons": list(dict.fromkeys(reasons)),
        "attribution_semantics": ATTRIBUTION_SEMANTICS,
        "strict_cuda_wddm_mapping": False,
        "causal_verdict": "NOT_ESTABLISHED",
        "interpretation_boundary": (
            "WDDM packet/queue 不含 CUDA correlationId；仅允许按目标 PID、WDDM "
            "context/engine 与 request 时间窗做归属推断。"
        ),
        "hags": dict(hags),
        "target_request": request,
        "wddm_table_counts": table_counts,
        "target_timeline_record_count": len(timeline),
    }
    return summary, timeline


def run_wddm_diagnostic(
    output_dir: Path,
    binary: Path,
    nsys: Path,
    *,
    run_id: str,
    cuda_visible_device: str,
    process_runner: ProcessRunner = subprocess.run,
    environment_probe: EnvironmentProbe = _default_environment_probe,
    hags_probe: HagsProbe = _default_hags_probe,
) -> Path:
    """采集并导出一个不可覆盖的 WDDM Engineering diagnostic。"""

    output = Path(output_dir).resolve()
    binary_path = Path(binary).resolve()
    nsys_path = Path(nsys).resolve()
    if output.exists():
        raise WDDMDiagnosticError(f"拒绝覆盖已有 WDDM diagnostic: {output}")
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise WDDMDiagnosticError(
            "run-id 必须匹配 q0-win-4090-YYYYMMDD-kernel-memop-wddm-diag-NN"
        )
    if not cuda_visible_device or "," in cuda_visible_device:
        raise WDDMDiagnosticError("WDDM diagnostic 必须绑定唯一 CUDA_VISIBLE_DEVICES")
    if not binary_path.is_file():
        raise WDDMDiagnosticError(f"Q0 binary 不存在: {binary_path}")
    if not nsys_path.is_file():
        raise WDDMDiagnosticError(f"nsys 不存在: {nsys_path}")

    output.mkdir(parents=True)
    environment = os.environ.copy()
    environment["CUDA_VISIBLE_DEVICES"] = cuda_visible_device
    case_run_id = f"{run_id}.{CASE_ID.lower()}"
    source_manifest = {
        "cuda_visible_device": cuda_visible_device,
        "default_stream_mode": "PER_THREAD",
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

    version = _run_text(
        process_runner, [str(nsys_path), "--version"], environment=environment
    )
    version_text = (version.stdout or "") + (version.stderr or "")
    (output / "nsys_version.txt").write_text(version_text, encoding="utf-8")
    if version.returncode != 0:
        raise WDDMDiagnosticError("Nsight Systems 版本探测失败")

    help_result = _run_text(
        process_runner,
        [str(nsys_path), "profile", "--help"],
        environment=environment,
    )
    help_text = (help_result.stdout or "") + (help_result.stderr or "")
    (output / "nsys_profile_help.txt").write_text(help_text, encoding="utf-8")
    wddm_help = "\n".join(
        line for line in help_text.splitlines() if "wddm" in line.lower()
    )
    (output / "nsys_profile_help_wddm.txt").write_text(
        wddm_help + ("\n" if wddm_help else ""), encoding="utf-8"
    )
    if help_result.returncode != 0:
        raise WDDMDiagnosticError("Nsight Systems profile --help 执行失败")
    missing_help = [
        option
        for option in REQUIRED_HELP_OPTIONS
        if option.lower() not in help_text.lower()
    ]
    if missing_help:
        raise WDDMDiagnosticError(f"Nsight 帮助输出缺少 WDDM 参数: {missing_help}")

    hags = dict(hags_probe())
    _write_json(output / "hags_status.json", hags)
    snapshot = dict(
        environment_probe(binary_path, nsys_path, cuda_visible_device, process_runner)
    )
    _validate_environment(snapshot, cuda_visible_device)

    trace_prefix = output / "trace"
    collection_argv = build_wddm_collection_argv(
        nsys_path, binary_path, trace_prefix, case_run_id
    )
    manifest = {
        "schema_version": "exposedpath-q0-wddm-diagnostic-run/0.1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PREPARED_NOT_EXECUTED",
        "data_role": "Engineering",
        "diagnostic_only": True,
        "q0_status": "NOT_RUN",
        "run_id": run_id,
        "case_id": CASE_ID,
        "command_argv": collection_argv,
        "source": {
            "binary": {"path": str(binary_path), "sha256": _sha256(binary_path)},
            "nsys": {"path": str(nsys_path), "sha256": _sha256(nsys_path)},
            "source_manifest": {
                "name": source_manifest_path.name,
                "sha256": _sha256(source_manifest_path),
            },
        },
        "research_eligibility": {
            "formal_evidence": False,
            "q0_status": "NOT_RUN",
            "scope": "WDDM_ENGINEERING_DIAGNOSTIC_ONLY",
        },
    }
    _write_json(output / "wddm_diagnostic_manifest.json", manifest)

    collected = _run_text(process_runner, collection_argv, environment=environment)
    (output / "collection_stdout.txt").write_text(
        collected.stdout or "", encoding="utf-8"
    )
    (output / "collection_stderr.txt").write_text(
        collected.stderr or "", encoding="utf-8"
    )
    raw_path = trace_prefix.with_suffix(".nsys-rep")
    if collected.returncode != 0:
        _write_json(
            output / "diagnostic_failure.json",
            {"stage": "COLLECTION", "returncode": collected.returncode},
        )
        raise WDDMDiagnosticError(
            f"WDDM diagnostic 采集失败 ({collected.returncode})"
        )
    if not raw_path.is_file() or raw_path.stat().st_size <= 0:
        raise WDDMDiagnosticError("Nsight 成功返回但没有生成非空 Raw trace")

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
        raise WDDMDiagnosticError("WDDM diagnostic SQLite 导出失败")

    summary, timeline = summarize_wddm_sqlite(
        sqlite_path, source_manifest=source_manifest, hags=hags
    )
    summary_path = output / "wddm_summary.json"
    _write_json(summary_path, summary)
    (output / "wddm_timeline.json").write_text(
        json.dumps(timeline, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    receipt = {
        "schema_version": "exposedpath-q0-wddm-diagnostic-receipt/0.1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "COLLECTED_AND_EXPORTED",
        "data_role": "Engineering",
        "diagnostic_only": True,
        "q0_status": "NOT_RUN",
        "run_id": run_id,
        "case_id": CASE_ID,
        "command_argv": collection_argv,
        "export_argv": export_argv,
        "environment": snapshot,
        "hags": hags,
        "source": manifest["source"],
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
        "wddm_evidence_status": summary["evidence_status"],
        "research_eligibility": manifest["research_eligibility"],
    }
    _write_json(output / "wddm_diagnostic_receipt.json", receipt)
    compatibility_receipt = {
        "schema_version": "exposedpath-q0-collection/0.2.0",
        "generated_at_utc": receipt["generated_at_utc"],
        "status": "COLLECTED",
        "data_role": "Engineering",
        "q0_status": "NOT_RUN",
        "case_id": CASE_ID,
        "run_id": run_id,
        "command_argv": collection_argv,
        "returncode": collected.returncode,
        "environment": snapshot,
        "source_manifest": manifest["source"]["source_manifest"],
        "raw_trace": receipt["raw_trace"],
        "research_eligibility": manifest["research_eligibility"],
    }
    _write_json(output / "collection_receipt.json", compatibility_receipt)
    return summary_path
