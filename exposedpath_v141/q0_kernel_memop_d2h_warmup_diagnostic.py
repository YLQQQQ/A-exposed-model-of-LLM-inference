"""warm-up-only 64 MiB D2H / 10 ms kernel Engineering 配对 diagnostic（A'/B）。

该模块只服务单一单变量 diagnostic：

* A'（``A_PRIME_NO_WARMUP``）与 B（``B_WARMUP``）使用**同一个** binary / commit；
* 两者的 GPU、measured workload、两个 nonblocking stream、Host condvar 编排、
  Nsight collection argv 逐元素相同；
* 唯一差异是 B 追加 ``--diagnostic-warmup-kernel``，在 ``cudaProfilerStart()``
  /request 之外对同一个 ``q0_spin_kernel`` 做一次固定预热。

warm-up 元数据不经过 collection stdout，而是由目标程序在 capture 开始后、request
开始前写入一条 NVTX mark；runner 只从导出的 SQLite 中唯一恢复该 mark，缺失、
重复、eventType 不符或字段不合法一律 fail closed。

不新增 event/gate，不升级 Q0，也不把结果解释为 lazy module loading、WDDM、
driver 或 Runtime 的根因。
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


CASE_ID = "Q0-KERNEL-MEMOP-001"
DIAGNOSTIC_D2H_BYTES = 64 * 1024 * 1024
DIAGNOSTIC_KERNEL_MS = 10
WARMUP_KERNEL_MS = 10
# 历史 baseline 只作参考；本次单变量 A/B 的 A 侧必须来自同一个新 binary。
BASELINE_REFERENCE_COMMIT = "a607645e9c4fcd7df4b05d4e97fa8bf788763e47"
# run-id 保留 binary 侧冻结 identity 子串，再追加 warm-up 标记。
FROZEN_RUN_ID_IDENTITY = "kernel-memop-d2h-diag-64m-10ms"
RUN_ID_PATTERN = re.compile(
    r"q0-win-4090-\d{8}-kernel-memop-d2h-diag-64m-10ms-warmup-\d{2}"
)
# warm-up metadata 的唯一 transport：目标程序写入的 NVTX marker 标签前缀。
# 该前缀刻意不同于 Q0 structured identity 前缀（EXPOSEDPATH_JSON_V1:），
# 因此 Canonical/S 解析不会把它当作 request/phase/marker identity。
NVTX_DIAGNOSTIC_PREFIX = "EXPOSEDPATH_DIAGNOSTIC_V1:"
WARMUP_MARKER_REQUIRED_FIELDS = (
    "arm",
    "cuda_module_loading_mode",
    "warmup_host_ns",
    "warmup_interleave",
    "warmup_status",
)
WARMUP_MARKER_INTERLEAVE = "OUTSIDE_CAPTURE_RANGE"
# nsys SQLite 里 NVTX mark（NvtxMark）的 eventType；push/pop range 在本仓库真实
# trace 中为 59，因此不会与 mark 混淆。
NVTX_MARK_EVENT_TYPE = 34
METADATA_TRANSPORT = {
    "channel": "NVTX_MARK",
    "nvtx_label_prefix": NVTX_DIAGNOSTIC_PREFIX,
    "nvtx_event_type": NVTX_MARK_EVENT_TYPE,
    "nvtx_event_kind": "NvtxMark",
    "recovery": "TRACE_SQLITE_NVTX_UNIQUE_MARK",
    "collection_stdout_is_authoritative": False,
    "marker_placement": "AFTER_cudaProfilerStart_BEFORE_request",
    "required_fields": list(WARMUP_MARKER_REQUIRED_FIELDS),
}
# warmup-01 的 metadata transport 依赖 collection stdout，已固定为无效输出通道。
SUPERSEDED_RUN_ID_SUFFIX = "-warmup-01"
PRIOR_RUN_DISPOSITION = {
    "run_id_suffix": SUPERSEDED_RUN_ID_SUFFIX,
    "disposition": "INVALID_INSTRUMENTATION_OUTPUT_CHANNEL",
    "reason": (
        "metadata transport 依赖 collection stdout：marker 写在 cudaProfilerStart() "
        "之前，目标程序 stdout 未出现在 collection_stdout.txt，B 未执行"
    ),
    "usable_as_arm_result": False,
    "rerun_allowed": False,
}
WARMUP_FLAG = "--diagnostic-warmup-kernel"
ARM_A = "A_PRIME_NO_WARMUP"
ARM_B = "B_WARMUP"
ARM_OUTPUT_NAMES = {ARM_A: "arm-a-no-warmup", ARM_B: "arm-b-warmup"}

# pair-level 解释只按预注册组合归类；任何结果都保持 Engineering-only。
PAIR_OUTCOME_POLICY = {
    "A_PRIME_0_B_POSITIVE": (
        "controlled association with warm-up/preconditioning; Engineering-only"
    ),
    "BOTH_ZERO": "warm-up did not restore overlap; Engineering-only",
    "A_PRIME_POSITIVE_B_POSITIVE": (
        "implementation/control arm already overlaps; must NOT be attributed to warm-up"
    ),
    "A_PRIME_POSITIVE_B_ZERO": (
        "no positive warm-up effect; descriptive only"
    ),
    "PAIR_INVALID": "任一 arm invalid -> pair INVALID / STOP",
}
PAIR_OUTCOME_RULE = (
    "PASS if and only if both arms are valid; then classify by "
    "(overlap_a > 0, overlap_b > 0); any invalid arm yields PAIR_INVALID STOP"
)


def classify_pair_outcome(
    *, overlap_a_ns: int, overlap_b_ns: int, arms_valid: bool
) -> str:
    """按预注册组合归类 pair-level 结果。"""

    if not arms_valid:
        return "PAIR_INVALID"
    a_positive = overlap_a_ns > 0
    b_positive = overlap_b_ns > 0
    if not a_positive and b_positive:
        return "A_PRIME_0_B_POSITIVE"
    if not a_positive and not b_positive:
        return "BOTH_ZERO"
    if a_positive and b_positive:
        return "A_PRIME_POSITIVE_B_POSITIVE"
    return "A_PRIME_POSITIVE_B_ZERO"

ProcessRunner = Callable[..., subprocess.CompletedProcess[str]]
EnvironmentProbe = Callable[..., Mapping[str, Any]]


class KernelMemopD2HWarmupDiagnosticError(RuntimeError):
    """warm-up-only D2H 配对诊断的输入或产物合同不满足要求。"""


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
        "warmup_kernel_ms": WARMUP_KERNEL_MS,
        "warmup_interleave": "OUTSIDE_CAPTURE_RANGE",
        "single_variable": "PRE_CAPTURE_WARMUP_ONLY",
    }


def build_pair_arm_argv(
    nsys: Path,
    binary: Path,
    arm: str,
    arm_output: Path,
    case_run_id: str,
) -> list[str]:
    """构造某一 arm 的 collection 命令；两 arm 仅差一个 warm-up 开关。"""

    if arm not in ARM_OUTPUT_NAMES:
        raise KernelMemopD2HWarmupDiagnosticError(f"未知 arm: {arm}")
    argv = [
        str(Path(nsys).resolve()),
        "profile",
        "--trace=cuda,nvtx",
        "--capture-range=cudaProfilerApi",
        "--capture-range-end=stop",
        "--force-overwrite=false",
        "-o",
        str((Path(arm_output) / "trace").resolve()),
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
    if arm == ARM_B:
        argv.append(WARMUP_FLAG)
    return argv


def build_pair_export_argv(nsys: Path, sqlite_path: Path, raw_path: Path) -> list[str]:
    return [
        str(Path(nsys).resolve()),
        "export",
        "--type",
        "sqlite",
        "--lazy=false",
        "--force-overwrite=false",
        "--output",
        str(Path(sqlite_path).resolve()),
        str(Path(raw_path).resolve()),
    ]


def _warmup_marker_payload(label: str) -> dict[str, Any] | None:
    """把一条候选 NVTX 标签还原为 marker payload；非本 diagnostic 标签返回 None。"""

    if not label.startswith(NVTX_DIAGNOSTIC_PREFIX):
        return None
    try:
        payload = json.loads(label[len(NVTX_DIAGNOSTIC_PREFIX) :])
    except json.JSONDecodeError as exc:
        raise KernelMemopD2HWarmupDiagnosticError(
            f"warm-up marker 不是合法 JSON: {exc}"
        ) from exc
    if not isinstance(payload, Mapping):
        raise KernelMemopD2HWarmupDiagnosticError("warm-up marker 必须是 JSON 对象")
    return dict(payload)


def recover_warmup_diagnostic_marker(trace_sqlite: Path) -> dict[str, Any]:
    """从导出的 SQLite 中唯一恢复 warm-up NVTX mark；缺失/重复即 fail closed。

    只接受 ``eventType=NvtxMark`` 且带本 diagnostic 前缀的行；同前缀的 push/pop
    range 不会被误认为 mark。mark provenance 只依赖 rowid/start/globalTid/text，
    不使用 end。
    """

    with _open_readonly(trace_sqlite) as connection:
        tables = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if not {"NVTX_EVENTS", "StringIds"}.issubset(tables):
            raise KernelMemopD2HWarmupDiagnosticError(
                "trace 缺少 warm-up marker 所需的 NVTX_EVENTS/StringIds 表"
            )
        matches: list[dict[str, Any]] = []
        non_mark_prefix_rows = 0
        for rowid, start, event_type, text, text_id, global_tid in connection.execute(
            """
            SELECT n.rowid, n.start, n.eventType, COALESCE(n.text, s.value, ''),
                   n.textId, n.globalTid
            FROM NVTX_EVENTS AS n
            LEFT JOIN StringIds AS s ON s.id = n.textId
            ORDER BY n.start, n.rowid
            """
        ):
            label = str(text)
            if not label.startswith(NVTX_DIAGNOSTIC_PREFIX):
                continue
            if event_type != NVTX_MARK_EVENT_TYPE:
                # 同前缀但非 mark（例如 push/pop range 59）：不得被误认为 marker。
                non_mark_prefix_rows += 1
                continue
            payload = _warmup_marker_payload(label)
            if payload is None:  # pragma: no cover - 前缀已在上方判定
                continue
            missing = [
                field
                for field in WARMUP_MARKER_REQUIRED_FIELDS
                if field not in payload
            ]
            if missing:
                raise KernelMemopD2HWarmupDiagnosticError(
                    f"warm-up marker 缺少必需字段: {missing}"
                )
            if payload["warmup_interleave"] != WARMUP_MARKER_INTERLEAVE:
                raise KernelMemopD2HWarmupDiagnosticError(
                    "warm-up 不在 capture range 之外: "
                    f"{payload['warmup_interleave']}"
                )
            if not isinstance(payload["warmup_host_ns"], int) or isinstance(
                payload["warmup_host_ns"], bool
            ):
                raise KernelMemopD2HWarmupDiagnosticError(
                    "warm-up marker 的 warmup_host_ns 必须是整数"
                )
            matches.append(
                {
                    "payload": payload,
                    "nvtx": {
                        "source_table": "NVTX_EVENTS",
                        "source_rowid": rowid,
                        "event_type": event_type,
                        "event_kind": "NvtxMark",
                        "text_id": text_id,
                        "start_ns": start,
                        "global_tid": global_tid,
                        "text": label,
                    },
                }
            )

    if not matches:
        raise KernelMemopD2HWarmupDiagnosticError(
            "trace SQLite 缺少 warm-up diagnostic NVTX mark"
            f"（同前缀非 mark 行 {non_mark_prefix_rows} 条）"
        )
    if len(matches) != 1:
        raise KernelMemopD2HWarmupDiagnosticError(
            f"warm-up diagnostic NVTX mark 必须唯一，实际 {len(matches)} 条"
        )
    return matches[0]


def _open_readonly(path: Path) -> sqlite3.Connection:
    uri = path.resolve().as_uri() + "?mode=ro&immutable=1"
    connection = sqlite3.connect(uri, uri=True)
    connection.text_factory = lambda value: value.decode("utf-8", errors="replace")
    connection.execute("PRAGMA query_only = ON")
    return connection


def _normalized_api_name(value: str) -> str:
    return re.sub(r"_v\d+$", "", value)


def summarize_warmup_diagnostic_sqlite(trace_sqlite: Path) -> dict[str, Any]:
    """从导出的 SQLite 读取 Host API 时长与 device interval，只做描述性统计。"""

    with _open_readonly(trace_sqlite) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        required = {
            "CUPTI_ACTIVITY_KIND_RUNTIME",
            "CUPTI_ACTIVITY_KIND_KERNEL",
            "CUPTI_ACTIVITY_KIND_MEMCPY",
        }
        missing = sorted(required - tables)
        if missing:
            raise KernelMemopD2HWarmupDiagnosticError(f"trace 缺少必需表: {missing}")
        strings = {
            row[0]: row[1]
            for row in connection.execute("SELECT id, value FROM StringIds")
        }
        runtime_rows = [
            {
                "api_name": strings.get(row[2], ""),
                "correlation_id": row[3],
                "duration_ns": row[1] - row[0],
                "end_ns": row[1],
                "global_tid": row[4],
                "start_ns": row[0],
            }
            for row in connection.execute(
                "SELECT start, end, nameId, correlationId, globalTid "
                "FROM CUPTI_ACTIVITY_KIND_RUNTIME ORDER BY start"
            )
        ]
        kernel_rows = [
            {
                "correlation_id": row[2],
                "duration_ns": row[1] - row[0],
                "end_ns": row[1],
                "name": strings.get(row[3], strings.get(row[4], "")),
                "start_ns": row[0],
                "stream_id": row[5],
            }
            for row in connection.execute(
                "SELECT start, end, correlationId, demangledName, shortName, streamId "
                "FROM CUPTI_ACTIVITY_KIND_KERNEL ORDER BY start"
            )
        ]
        memcpy_rows = [
            {
                "bytes": row[4],
                "copy_kind": row[3],
                "correlation_id": row[2],
                "duration_ns": row[1] - row[0],
                "end_ns": row[1],
                "start_ns": row[0],
                "stream_id": row[5],
            }
            for row in connection.execute(
                "SELECT start, end, correlationId, copyKind, bytes, streamId "
                "FROM CUPTI_ACTIVITY_KIND_MEMCPY ORDER BY start"
            )
        ]

    if len(kernel_rows) != 1 or len(memcpy_rows) != 1:
        raise KernelMemopD2HWarmupDiagnosticError(
            "capture 内的 kernel/memcpy device activity 必须各恰好一条"
        )
    launches = [
        row
        for row in runtime_rows
        if _normalized_api_name(row["api_name"]) == "cudaLaunchKernel"
    ]
    if len(launches) != 1:
        raise KernelMemopD2HWarmupDiagnosticError(
            "capture 内必须恰好有一个 measured cudaLaunchKernel"
        )
    copies = [
        row
        for row in runtime_rows
        if _normalized_api_name(row["api_name"]) == "cudaMemcpyAsync"
    ]
    if len(copies) != 1:
        raise KernelMemopD2HWarmupDiagnosticError(
            "capture 内必须恰好有一个 measured cudaMemcpyAsync"
        )

    kernel = kernel_rows[0]
    memcpy = memcpy_rows[0]
    overlap_ns = max(
        0,
        min(kernel["end_ns"], memcpy["end_ns"])
        - max(kernel["start_ns"], memcpy["start_ns"]),
    )
    completion_order = (
        "KERNEL_TERMINAL" if kernel["end_ns"] >= memcpy["end_ns"] else "MEMCPY_TERMINAL"
    )
    gap_ns = max(
        kernel["start_ns"] - memcpy["end_ns"],
        memcpy["start_ns"] - kernel["end_ns"],
        0,
    )
    launch_ns = launches[0]["duration_ns"]

    return {
        "measured_launch_kernel_api_ns": launch_ns,
        "measured_launch_kernel_api_start_ns": launches[0]["start_ns"],
        "measured_launch_kernel_api_end_ns": launches[0]["end_ns"],
        "measured_memcpy_async_api_ns": copies[0]["duration_ns"],
        "kernel_device_interval": kernel,
        "memcpy_device_interval": memcpy,
        "overlap_ns": overlap_ns,
        "gap_ns": gap_ns,
        "completion_order": completion_order,
        "descriptive_class": (
            "OVERLAP_POSITIVE"
            if overlap_ns > 0
            else "OVERLAP_ZERO_LAUNCH_LATENCY_REDUCED"
            if launch_ns < 1_000_000
            else "OVERLAP_ZERO_LAUNCH_LATENCY_STILL_HIGH"
        ),
    }


def _run_one_arm(
    *,
    arm: str,
    arm_output: Path,
    binary_path: Path,
    nsys_path: Path,
    run_id: str,
    environment: Mapping[str, str],
    snapshot: Mapping[str, Any],
    process_runner: ProcessRunner,
) -> dict[str, Any]:
    arm_output.mkdir(parents=True)
    case_run_id = f"{run_id}.{'a' if arm == ARM_A else 'b'}.{CASE_ID.lower()}"
    collection_argv = build_pair_arm_argv(
        nsys_path, binary_path, arm, arm_output, case_run_id
    )
    collected = _run_text(process_runner, collection_argv, environment=environment)
    (arm_output / "collection_stdout.txt").write_text(
        collected.stdout or "", encoding="utf-8"
    )
    (arm_output / "collection_stderr.txt").write_text(
        collected.stderr or "", encoding="utf-8"
    )
    raw_path = arm_output / "trace.nsys-rep"
    if collected.returncode != 0:
        _write_json(
            arm_output / "diagnostic_failure.json",
            {"stage": "COLLECTION", "arm": arm, "returncode": collected.returncode},
        )
        raise KernelMemopD2HWarmupDiagnosticError(
            f"{arm} 采集失败 ({collected.returncode})"
        )
    if not raw_path.is_file() or raw_path.stat().st_size <= 0:
        raise KernelMemopD2HWarmupDiagnosticError(
            f"{arm}: Nsight 成功返回但未生成非空 Raw trace"
        )

    sqlite_path = arm_output / "trace.sqlite"
    export_argv = build_pair_export_argv(nsys_path, sqlite_path, raw_path)
    exported = _run_text(process_runner, export_argv, environment=environment)
    (arm_output / "export_stdout.txt").write_text(exported.stdout or "", encoding="utf-8")
    (arm_output / "export_stderr.txt").write_text(exported.stderr or "", encoding="utf-8")
    if exported.returncode != 0 or not sqlite_path.is_file():
        _write_json(
            arm_output / "diagnostic_failure.json",
            {"stage": "SQLITE_EXPORT", "arm": arm, "returncode": exported.returncode},
        )
        raise KernelMemopD2HWarmupDiagnosticError(f"{arm}: SQLite 导出失败")

    # metadata transport 只从导出的 NVTX 记录恢复；collection stdout 不参与判定。
    recovered = recover_warmup_diagnostic_marker(sqlite_path)
    marker = recovered["payload"]
    if marker["arm"] != arm:
        raise KernelMemopD2HWarmupDiagnosticError(
            f"warm-up marker 的 arm 与采集 arm 不一致: {marker['arm']} != {arm}"
        )
    expected_status = "PASS" if arm == ARM_B else "NOT_APPLICABLE"
    if marker["warmup_status"] != expected_status:
        raise KernelMemopD2HWarmupDiagnosticError(
            f"{arm} 的 warm-up 状态必须为 {expected_status}: {marker['warmup_status']}"
        )
    warmup = {
        **marker,
        "warmup_marker_source": recovered["nvtx"],
    }
    measured = summarize_warmup_diagnostic_sqlite(sqlite_path)
    eligibility = {
        "formal_evidence": False,
        "q0_status": "NOT_RUN",
        "scope": "KERNEL_MEMOP_D2H_WARMUP_PAIR_ENGINEERING_DIAGNOSTIC_ONLY",
    }
    arm_manifest = {
        "schema_version": "exposedpath-q0-kernel-memop-d2h-warmup-arm/0.1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "arm": arm,
        "data_role": "Engineering",
        "diagnostic_only": True,
        "q0_status": "NOT_RUN",
        "run_id": case_run_id,
        "case_id": CASE_ID,
        "command_argv": collection_argv,
        "export_argv": export_argv,
        "environment": dict(snapshot),
        "warmup": warmup,
        "metadata_transport": METADATA_TRANSPORT,
        "measured": measured,
        "source": {
            "binary": {"path": str(binary_path), "sha256": _sha256(binary_path)},
            "nsys": {"path": str(nsys_path), "sha256": _sha256(nsys_path)},
        },
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
    }
    _write_json(arm_output / "diagnostic_manifest.json", arm_manifest)
    return {
        "arm": arm,
        "run_id": case_run_id,
        "output_dir": str(arm_output),
        "command_argv": collection_argv,
        "export_argv": export_argv,
        "environment": dict(snapshot),
        "warmup": warmup,
        "measured": measured,
        "source": arm_manifest["source"],
        "raw_trace": arm_manifest["raw_trace"],
        "sqlite": arm_manifest["sqlite"],
        "research_eligibility": eligibility,
    }


def run_kernel_memop_d2h_warmup_pair_diagnostic(
    output_dir: Path,
    binary: Path,
    nsys: Path,
    *,
    run_id: str,
    cuda_visible_device: str,
    implementation_commit: str,
    baseline_reference_commit: str = BASELINE_REFERENCE_COMMIT,
    process_runner: ProcessRunner = subprocess.run,
    environment_probe: EnvironmentProbe = _default_environment_probe,
) -> Path:
    """按预注册顺序执行 A'（无 warm-up）与 B（warm-up），产出不可覆盖配对证据。"""

    output = Path(output_dir).resolve()
    binary_path = Path(binary).resolve()
    nsys_path = Path(nsys).resolve()
    if output.exists():
        raise KernelMemopD2HWarmupDiagnosticError(f"拒绝覆盖已有配对 diagnostic: {output}")
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise KernelMemopD2HWarmupDiagnosticError(
            "run-id 必须匹配 kernel-memop-d2h-diag-64m-10ms-warmup-NN"
        )
    if run_id.endswith(SUPERSEDED_RUN_ID_SUFFIX):
        raise KernelMemopD2HWarmupDiagnosticError(
            "warmup-01 已固定为 INVALID_INSTRUMENTATION_OUTPUT_CHANNEL，"
            "不得补跑；修复后必须使用新的 run-id（...-warmup-02）"
        )
    if not cuda_visible_device or "," in cuda_visible_device:
        raise KernelMemopD2HWarmupDiagnosticError("配对 diagnostic 必须绑定唯一 GPU")
    if not implementation_commit:
        raise KernelMemopD2HWarmupDiagnosticError("必须记录 implementation_commit")
    if not baseline_reference_commit:
        raise KernelMemopD2HWarmupDiagnosticError("必须记录 baseline_reference_commit")
    if not binary_path.is_file():
        raise KernelMemopD2HWarmupDiagnosticError(f"Q0 binary 不存在: {binary_path}")
    if not nsys_path.is_file():
        raise KernelMemopD2HWarmupDiagnosticError(f"nsys 不存在: {nsys_path}")

    output.mkdir(parents=True)
    environment = os.environ.copy()
    environment["CUDA_VISIBLE_DEVICES"] = cuda_visible_device
    parameters = _parameters()
    eligibility = {
        "formal_evidence": False,
        "q0_status": "NOT_RUN",
        "scope": "KERNEL_MEMOP_D2H_WARMUP_PAIR_ENGINEERING_DIAGNOSTIC_ONLY",
    }
    plan_path = output / "pair_plan.json"
    _write_json(
        plan_path,
        {
            "schema_version": "exposedpath-q0-kernel-memop-d2h-warmup-pair-plan/0.1.0",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "PRE_REGISTERED_NOT_EXECUTED",
            "data_role": "Engineering",
            "diagnostic_only": True,
            "q0_status": "NOT_RUN",
            "run_id": run_id,
            "case_id": CASE_ID,
            "implementation_commit": implementation_commit,
            "baseline_reference_commit": baseline_reference_commit,
            "diagnostic_parameters": parameters,
            "metadata_transport": METADATA_TRANSPORT,
            "prior_run_disposition": PRIOR_RUN_DISPOSITION,
            "execution_order": [ARM_A, ARM_B],
            "single_variable": WARMUP_FLAG,
            "arms": {
                ARM_A: {"warmup_flag": False, "output": ARM_OUTPUT_NAMES[ARM_A]},
                ARM_B: {"warmup_flag": True, "output": ARM_OUTPUT_NAMES[ARM_B]},
            },
            "preregistered_rules": [
                "A_PRIME_FIRST_THEN_B_ONCE",
                "NO_RETRY",
                "NO_WARMUP_DURATION_TUNING",
                "B_PARAMETERS_NOT_CHANGED_FROM_A_PRIME_RESULT",
                "BOTH_ARMS_SAME_BINARY_AND_COMMIT",
                "MEASURED_WORKLOAD_STREAMS_HOST_CONDVAR_NSYS_ARGV_IDENTICAL",
                "FIXED_EXECUTION_ORDER_IS_A_KNOWN_LIMITATION",
                "METADATA_TRANSPORT_IS_NVTX_MARKER_NOT_COLLECTION_STDOUT",
                "SUPERSEDED_WARMUP_01_NOT_RERUNNABLE",
            ],
            "decision_policy": {
                "primary_measure": "device_interval_overlap_ns",
                "validity_rule": "WARMUP_COMPLETED_AND_PROVENANCE_VALID",
                "launch_latency_is_not_a_validity_condition": True,
                "descriptive_classes": [
                    "OVERLAP_POSITIVE",
                    "OVERLAP_ZERO_LAUNCH_LATENCY_REDUCED",
                    "OVERLAP_ZERO_LAUNCH_LATENCY_STILL_HIGH",
                ],
                "stop_after_single_pair": True,
                "q0_upgrade_on_any_result": False,
                "causal_verdict": "NOT_ESTABLISHED",
            },
            "pair_level_interpretation": {
                "rule": PAIR_OUTCOME_RULE,
                "policy": PAIR_OUTCOME_POLICY,
                "engineering_only": True,
                "changes_gate6_or_q0": False,
            },
            "interpretation_boundary": {
                "allowed_conclusion_if_b_overlaps": (
                    "warm-up / preconditioning is in controlled association with "
                    "the observed overlap; this is an Engineering association only"
                ),
                "not_allowed_conclusion": (
                    "No concrete mechanism causality may be established from this "
                    "single pair alone."
                ),
                "forbidden_attribution": [
                    "LAZY_MODULE_LOADING",
                    "WDDM",
                    "DRIVER",
                    "RUNTIME",
                ],
            },
            "research_eligibility": eligibility,
        },
    )

    snapshot = dict(
        environment_probe(binary_path, nsys_path, cuda_visible_device, process_runner)
    )
    _validate_environment(snapshot, cuda_visible_device)

    arms = []
    arms.append(
        _run_one_arm(
            arm=ARM_A,
            arm_output=output / ARM_OUTPUT_NAMES[ARM_A],
            binary_path=binary_path,
            nsys_path=nsys_path,
            run_id=run_id,
            environment=environment,
            snapshot=snapshot,
            process_runner=process_runner,
        )
    )
    arms.append(
        _run_one_arm(
            arm=ARM_B,
            arm_output=output / ARM_OUTPUT_NAMES[ARM_B],
            binary_path=binary_path,
            nsys_path=nsys_path,
            run_id=run_id,
            environment=environment,
            snapshot=snapshot,
            process_runner=process_runner,
        )
    )

    arm_a, arm_b = arms
    argv_a = build_pair_arm_argv(
        nsys_path, binary_path, ARM_A, output / ARM_OUTPUT_NAMES[ARM_A], arm_a["run_id"]
    )
    argv_b = build_pair_arm_argv(
        nsys_path, binary_path, ARM_B, output / ARM_OUTPUT_NAMES[ARM_B], arm_b["run_id"]
    )

    def _normalized(argv: list[str]) -> list[str]:
        """移除仅因 arm output 目录与 run identity 而必然不同的元素。"""

        normalized = list(argv)
        normalized[normalized.index("--run-id") + 1] = "<run-id>"
        trace_index = normalized.index("-o") + 1
        normalized[trace_index] = Path(normalized[trace_index]).name
        return normalized

    normalized_a = _normalized(argv_a)
    normalized_b = _normalized(argv_b)
    # 这是“有意 construction diff + 同 binary/环境/collection”的可机检记录，而不是
    # 物理层面的严格单变量证明：A' 固定先于 B，可能带来跨进程 clock/cache carryover。
    construction_diff_evidence = {
        "binary_sha256_equal": arm_a["source"]["binary"]["sha256"]
        == arm_b["source"]["binary"]["sha256"],
        "nsys_sha256_equal": arm_a["source"]["nsys"]["sha256"]
        == arm_b["source"]["nsys"]["sha256"],
        "gpu_uuid_equal": arm_a["environment"]["selected_gpu"]["uuid"]
        == arm_b["environment"]["selected_gpu"]["uuid"],
        "environment_equal": arm_a["environment"] == arm_b["environment"],
        "argv_equal_except_run_id_output_and_warmup_flag": (
            normalized_b[:-1] == normalized_a
        ),
        "warmup_flag_only_on_b": (
            WARMUP_FLAG not in argv_a and argv_b[-1] == WARMUP_FLAG
        ),
        "warmup_flag_count_b": argv_b.count(WARMUP_FLAG),
        "warmup_flag": WARMUP_FLAG,
        "intended_construction_diff": WARMUP_FLAG,
        "execution_order": [ARM_A, ARM_B],
        "fixed_execution_order_limitation": (
            "A_PRIME_ALWAYS_FIRST_SO_CROSS_PROCESS_CLOCK_OR_CACHE_CARRYOVER_"
            "CANNOT_BE_EXCLUDED"
        ),
        "claim_scope": "ENGINEERING_CONTROLLED_ASSOCIATION_ONLY",
        "cuda_module_loading_mode_a": (arm_a["warmup"] or {}).get(
            "cuda_module_loading_mode"
        ),
        "cuda_module_loading_mode_b": (arm_b["warmup"] or {}).get(
            "cuda_module_loading_mode"
        ),
        "cuda_module_loading_mode_equal": (arm_a["warmup"] or {}).get(
            "cuda_module_loading_mode"
        )
        == (arm_b["warmup"] or {}).get("cuda_module_loading_mode"),
    }
    required_proofs = (
        "binary_sha256_equal",
        "nsys_sha256_equal",
        "gpu_uuid_equal",
        "environment_equal",
        "argv_equal_except_run_id_output_and_warmup_flag",
        "warmup_flag_only_on_b",
        "cuda_module_loading_mode_equal",
    )
    if not all(construction_diff_evidence[key] for key in required_proofs):
        raise KernelMemopD2HWarmupDiagnosticError(
            "A'/B 未满足同 binary/同环境/仅 warm-up 开关的受控对照前提"
        )

    # pair-level 归类由两 arm 的实测 overlap 直接决定，不引入新的测量语义。
    both_arms_valid = all(
        arm["measured"].get("overlap_ns") is not None for arm in (arm_a, arm_b)
    )
    pair_outcome = classify_pair_outcome(
        overlap_a_ns=int(arm_a["measured"]["overlap_ns"]),
        overlap_b_ns=int(arm_b["measured"]["overlap_ns"]),
        arms_valid=both_arms_valid,
    )
    pair_interpretation = {
        "pair_outcome": pair_outcome,
        "pair_outcome_statement": PAIR_OUTCOME_POLICY[pair_outcome],
        "overlap_a_prime_ns": int(arm_a["measured"]["overlap_ns"]),
        "overlap_b_ns": int(arm_b["measured"]["overlap_ns"]),
        "arms_valid": both_arms_valid,
        "rule": PAIR_OUTCOME_RULE,
        "engineering_only": True,
        "changes_gate6_or_q0": False,
    }

    receipt = {
        "schema_version": "exposedpath-q0-kernel-memop-d2h-warmup-pair-receipt/0.1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "COLLECTED_AND_EXPORTED",
        "data_role": "Engineering",
        "diagnostic_only": True,
        "q0_status": "NOT_RUN",
        "run_id": run_id,
        "case_id": CASE_ID,
        "implementation_commit": implementation_commit,
        "baseline_reference_commit": baseline_reference_commit,
        "diagnostic_parameters": parameters,
        "metadata_transport": METADATA_TRANSPORT,
        "prior_run_disposition": PRIOR_RUN_DISPOSITION,
        "environment": snapshot,
        "plan": {"name": plan_path.name, "sha256": _sha256(plan_path)},
        "arms": arms,
        "construction_diff_evidence": construction_diff_evidence,
        "pair_interpretation": pair_interpretation,
        "research_eligibility": eligibility,
        "interpretation_boundary": {
            "allowed_conclusion_if_b_overlaps": (
                "warm-up / preconditioning is in controlled association with "
                "the observed overlap; this is an Engineering association only"
            ),
            "not_allowed_conclusion": (
                "No concrete mechanism causality may be established from this "
                "single pair alone."
            ),
            "forbidden_attribution": [
                "LAZY_MODULE_LOADING",
                "WDDM",
                "DRIVER",
                "RUNTIME",
            ],
        },
    }
    receipt_path = output / "pair_receipt.json"
    _write_json(receipt_path, receipt)
    return receipt_path


__all__ = [
    "ARM_A",
    "ARM_B",
    "BASELINE_REFERENCE_COMMIT",
    "CASE_ID",
    "DIAGNOSTIC_D2H_BYTES",
    "DIAGNOSTIC_KERNEL_MS",
    "METADATA_TRANSPORT",
    "NVTX_DIAGNOSTIC_PREFIX",
    "PAIR_OUTCOME_POLICY",
    "PAIR_OUTCOME_RULE",
    "PRIOR_RUN_DISPOSITION",
    "SUPERSEDED_RUN_ID_SUFFIX",
    "WARMUP_FLAG",
    "WARMUP_KERNEL_MS",
    "WARMUP_MARKER_REQUIRED_FIELDS",
    "KernelMemopD2HWarmupDiagnosticError",
    "build_pair_arm_argv",
    "build_pair_export_argv",
    "classify_pair_outcome",
    "recover_warmup_diagnostic_marker",
    "run_kernel_memop_d2h_warmup_pair_diagnostic",
    "summarize_warmup_diagnostic_sqlite",
]
