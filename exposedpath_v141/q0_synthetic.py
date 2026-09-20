"""Gate 6 的确定性合成 Canonical 事实与正式 S/A/B 执行器。

输入只来自 oracle construction 和独立的 case profile；不得读取 expected 构造输入。
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .a_accounting import calculate_a_windows
from .ab_inputs import ABInputs, CanonicalBundle, RequestPhaseWindow
from .b_provenance import calculate_b_syncs
from .canonical_raw import load_canonical_raw_schema
from .q0_execution import load_q0_execution_manifest
from .q0_oracle import load_oracle_bundle
from .sync_semantics import (
    analyze_semantic_inventory,
    analyze_sync_semantics,
    build_semantic_inventory,
    classify_cuda_api,
)


_CLOCK = "NSYS_TRACE_RELATIVE_NS"


def _identity(phase: str, request_id: str = "req-0") -> dict[str, Any]:
    return {
        "kind": "phase",
        "experiment_id": "exposedpath-q0-synthetic",
        "wmpc_id": "q0-controlled",
        "run_id": "synthetic-run",
        "run_role": "Engineering",
        "pass_id": "Pass1",
        "request_id": request_id,
        "repeat_id": "repeat-0",
        "phase": phase,
    }


def _activity(
    spec: Mapping[str, Any],
    stream_id: int,
    *,
    request_id: str = "req-0",
    phase: str = "decode",
    ownership_status: str = "VALID",
    ownership_reasons: Sequence[str] = (),
    enqueue_start: int | None = None,
    enqueue_end: int | None = None,
    graph_id: int | None = None,
    graph_node_id: int | None = None,
) -> dict[str, Any]:
    start = int(spec["start_ns"])
    end = int(spec["end_ns"])
    enqueue_start = max(0, start - 2) if enqueue_start is None else enqueue_start
    enqueue_end = max(enqueue_start, start - 1) if enqueue_end is None else enqueue_end
    kind = "KERNEL" if spec.get("activity_type") == "KERNEL" else "MEMCPY"
    return {
        "record_id": spec["activity_label"],
        "start_ns": start,
        "end_ns": end,
        "clock_domain_id": _CLOCK,
        "device_id": 0,
        "context_id": 1,
        "stream_id": stream_id,
        "enqueue_record_id": f"api:{spec['activity_label']}",
        "enqueue_start_ns": enqueue_start,
        "enqueue_end_ns": enqueue_end,
        "request_id": request_id,
        "repeat_id": "repeat-0",
        "origin_phase": phase,
        "invocation_identity": _identity(phase, request_id),
        "ownership_status": ownership_status,
        "ownership_reasons": list(ownership_reasons),
        "activity_kind": kind,
        "name": spec["activity_label"],
        "correlation_id": None,
        "graph_id": graph_id,
        "graph_node_id": graph_node_id,
    }


def _sync(
    spec: Mapping[str, Any],
    ordinal: int,
    *,
    stream_id: int | None = 2,
    phase: str = "decode",
    request_id: str = "req-0",
    event_id: int | None = None,
    event_sync_id: int | None = None,
) -> dict[str, Any]:
    kind = spec["sync_kind"]
    api_name = {
        "STREAM": "cudaStreamSynchronize",
        "DEVICE": "cudaDeviceSynchronize",
        "CONTEXT": "cuCtxSynchronize",
        "EVENT": "cudaEventSynchronize",
        "SYNCHRONOUS_COPY": "cudaMemcpy",
    }[kind]
    classification = classify_cuda_api(api_name)
    return {
        "record_id": spec["sync_label"],
        "registry_rule_id": classification["registry_rule_id"],
        "universe_class": classification["universe_class"],
        "role": classification["role"],
        "sync_kind": classification["sync_kind"],
        "completion_scope": classification["completion_scope"],
        "host_start_ns": int(spec["start_ns"]),
        "host_end_ns": int(spec["end_ns"]),
        "stream_id": stream_id if kind == "STREAM" else None,
        "context_id": None if kind == "DEVICE" else 1,
        "device_id": 0,
        "event_id": event_id,
        "event_sync_id": event_sync_id,
        "request_id": request_id,
        "repeat_id": "repeat-0",
        "sync_owner_phase": phase,
        "sync_origin": "q0_controlled",
        "callsite_id": spec["sync_label"],
        "sync_ordinal": ordinal,
        "invocation_identity": _identity(phase, request_id),
        "ownership_status": "VALID",
        "ownership_reasons": [],
    }


def _event_record() -> dict[str, Any]:
    return {
        "record_id": "event:record-1",
        "event_id": 9,
        "event_sync_id": 90,
        "device_id": 0,
        "context_id": 1,
        "stream_id": 2,
        "host_start_ns": 25,
        "host_end_ns": 30,
        "request_id": "req-0",
        "repeat_id": "repeat-0",
        "ownership_status": "VALID",
        "ownership_reasons": [],
        "invocation_identity": _identity("decode"),
    }


def _event_wait() -> dict[str, Any]:
    return {
        "record_id": "edge:wait-1",
        "sync_kind": "STREAM_WAIT_EVENT",
        "role": "DEPENDENCY_EDGE",
        "event_id": 9,
        "event_sync_id": 90,
        "device_id": 0,
        "context_id": 1,
        "stream_id": 4,
        "host_start_ns": 32,
        "host_end_ns": 35,
        "ownership_status": "VALID",
        "ownership_reasons": [],
        "request_id": "req-0",
        "repeat_id": "repeat-0",
        "invocation_identity": _identity("decode"),
    }


def _profile(case: Mapping[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    case_id = str(case["case_id"])
    construction = case["construction"]
    specs = list(construction.get("activities", []))
    sync_specs = list(construction.get("syncs", []))
    streams = {spec["activity_label"]: 2 for spec in specs}
    if case_id in {"Q0-STREAM-001", "Q0-DEFAULT-PTDS-001"}:
        streams[specs[-1]["activity_label"]] = 4
    if case_id in {
        "Q0-DEVICE-001", "Q0-CONTEXT-001", "Q0-KERNEL-MEMOP-001",
        "Q0-TERMINAL-TIE-001", "Q0-OVERLAPPING-HOST-SYNC-001",
    } and len(specs) > 1:
        streams[specs[1]["activity_label"]] = 4
    if case_id == "Q0-EVENT-XSTREAM-001":
        streams["K_CONSUMER"] = 4
    if case_id == "Q0-DEFAULT-LEGACY-001":
        streams["K_LEGACY_DEFAULT"] = 0
    if case_id == "Q0-DEFAULT-PTDS-001":
        streams["K_PTDS"] = 0
        streams["K_OTHER_THREAD"] = 4
    if case_id == "Q0-MULTITHREAD-ORDERED-001":
        streams["K_THREAD_B"] = 4

    activities: list[dict[str, Any]] = []
    for spec in specs:
        kwargs: dict[str, Any] = {}
        if case_id == "Q0-INVOCATION-BLEED-001":
            kwargs.update(request_id="req-prior")
        elif case_id == "Q0-SUBMISSION-RACE-001":
            sync_start = int(sync_specs[0]["start_ns"])
            kwargs.update(enqueue_start=sync_start - 5, enqueue_end=sync_start + 10)
        elif case_id == "Q0-GRAPH-UNSUPPORTED-001":
            kwargs.update(graph_id=1, graph_node_id=None)
        if case_id == "Q0-PHASE-SPILL-001":
            kwargs.update(phase="prefill")
        activities.append(_activity(spec, streams[spec["activity_label"]], **kwargs))

    syncs: list[dict[str, Any]] = []
    for index, spec in enumerate(sync_specs):
        stream_id = 2
        if case_id == "Q0-EVENT-XSTREAM-001":
            stream_id = 4
        elif case_id == "Q0-DEFAULT-LEGACY-001":
            stream_id = 0
        elif case_id == "Q0-DEFAULT-PTDS-001":
            stream_id = 0
        elif case_id == "Q0-MULTITHREAD-ORDERED-001":
            stream_id = 4
        elif case_id == "Q0-OVERLAPPING-HOST-SYNC-001":
            stream_id = 2 if index == 0 else 4
        phase = "decode"
        event_id = 9 if spec["sync_kind"] == "EVENT" else None
        event_sync_id = 90 if spec["sync_kind"] == "EVENT" else None
        syncs.append(
            _sync(
                spec,
                index,
                stream_id=stream_id,
                phase=phase,
                event_id=event_id,
                event_sync_id=event_sync_id,
            )
        )

    event_records: list[dict[str, Any]] = []
    dependency_events: list[dict[str, Any]] = []
    if case_id in {"Q0-EVENT-001", "Q0-EVENT-XSTREAM-001", "Q0-MULTITHREAD-ORDERED-001"}:
        event_records.append(_event_record())
    if case_id in {"Q0-EVENT-XSTREAM-001", "Q0-MULTITHREAD-ORDERED-001"}:
        dependency_events.append(_event_wait())
    input_status = "INVALID" if case_id == "Q0-DROPPED-001" else "VALID"
    input_reasons = ["TRACE_DROPPED_RECORDS"] if input_status == "INVALID" else []
    mode = "LEGACY" if case_id == "Q0-DEFAULT-LEGACY-001" else "PER_THREAD"
    inventory = {
        "input_status": input_status,
        "input_reasons": input_reasons,
        "execution_context": {"default_stream_mode": mode, "selected_device_id": 0},
        "activities": activities,
        "event_records": event_records,
        "dependency_events": dependency_events,
        "contexts": [{"context_id": 1, "device_id": 0, "null_stream_id": 0}],
        "streams": [
            {"context_id": 1, "stream_id": 0, "flag": 0},
            {"context_id": 1, "stream_id": 2, "flag": 0},
            {"context_id": 1, "stream_id": 4, "flag": 1},
        ],
    }
    return inventory, syncs


def _nvtx(
    identity: Mapping[str, Any],
    start: int,
    end: int,
    record_id: str,
    *,
    global_tid: int = 1001,
) -> dict[str, Any]:
    payload = dict(identity)
    text = "EXPOSEDPATH_JSON_V1:" + json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return {
        "record_id": record_id,
        "start_ns": start,
        "end_ns": end,
        "global_tid": global_tid,
        "structured_identity": payload,
        "text": text,
    }


def _ab_inputs(
    case_id: str,
    inventory: Mapping[str, Any],
    raw_syncs: Sequence[Mapping[str, Any]],
    s_records: Sequence[Mapping[str, Any]],
    *,
    window_start: int = 0,
    window_end: int | None = None,
) -> ABInputs:
    start = int(window_start)
    end = (
        max([start + 100, *[int(sync["host_end_ns"]) for sync in raw_syncs]])
        if window_end is None
        else int(window_end)
    )
    request_identity = _identity("full_request")
    request_identity["kind"] = "request"
    nvtx = [_nvtx(request_identity, start, end, "nvtx:request")]
    for sync in raw_syncs:
        sync_identity = _identity(str(sync["sync_owner_phase"]))
        sync_identity.update(
            kind="sync",
            callsite_id=sync["callsite_id"],
            sync_origin=sync["sync_origin"],
            sync_ordinal=sync["sync_ordinal"],
        )
        nvtx.append(
            _nvtx(
                sync_identity,
                int(sync["host_start_ns"]),
                int(sync["host_end_ns"]),
                f"nvtx:{sync['record_id']}",
            )
        )
    cuda_apis = []
    for index, sync in enumerate(raw_syncs):
        cuda_apis.append(
            {
                "record_id": f"api:{sync['record_id']}",
                "start_ns": sync["host_start_ns"],
                "end_ns": sync["host_end_ns"],
                "global_tid": 1001,
                "correlation_id": 1000 + index,
                "api_name": {
                    "STREAM": "cudaStreamSynchronize",
                    "DEVICE": "cudaDeviceSynchronize",
                    "CONTEXT": "cuCtxSynchronize",
                    "EVENT": "cudaEventSynchronize",
                    "SYNCHRONOUS_COPY_OR_IMPLICIT_BLOCK": "cudaMemcpy",
                }[sync["sync_kind"]],
            }
        )
    activities = tuple(dict(item) for item in inventory["activities"])
    records = {
        "nvtx": tuple(nvtx),
        "cuda_api": tuple(cuda_apis),
        "cuda_sync": tuple(),
        "device_activity": activities,
        "cuda_event": tuple(),
        "context": tuple(),
        "stream": tuple(),
        "diagnostic": tuple(),
    }
    canonical = CanonicalBundle(
        manifest={"clock": {"clock_domain_id": _CLOCK}},
        records=records,
        schema=load_canonical_raw_schema(),
        cuda_api_by_id={item["record_id"]: item for item in cuda_apis},
        activity_by_id={item["record_id"]: item for item in activities},
        physical_sync_by_id={},
    )
    window = RequestPhaseWindow(
        window_id=f"window:{case_id}",
        experiment_id="exposedpath-q0-synthetic",
        wmpc_id="q0-controlled",
        run_id="synthetic-run",
        run_role="Engineering",
        pass_id="Pass1",
        request_id="req-0",
        repeat_id="repeat-0",
        phase="full_request",
        start_ns=start,
        end_ns=end,
        nvtx_record_id="nvtx:request",
    )
    global_reasons = tuple(inventory.get("input_reasons", ()))
    return ABInputs(
        canonical=canonical,
        s_manifest={},
        s_records=tuple(dict(record) for record in s_records),
        windows=(window,),
        global_quality_reasons=global_reasons,
        window_discovery_issues=(),
    )


# Gate 6 amendment 冻结的 in-scope case：Unified Marker Ownership amendment 的
# External / Multithread-Ordered / Overlapping-Host-Sync，以及 Missing-Corr
# amendment 的 Missing-Corr。这些 proxy 只允许输入结构事实（request/phase range、
# covering structured marker、CUDA API、device activity、event record / wait-event、
# physical sync），最终 ownership / wait set / terminal / validity 必须由
# `sync_semantics` 正常化与推导链得出。
_STRUCTURAL_CASE_IDS = frozenset(
    {
        "Q0-EXTERNAL-001",
        "Q0-MULTITHREAD-ORDERED-001",
        "Q0-OVERLAPPING-HOST-SYNC-001",
        "Q0-MISSING-CORR-001",
    }
)


def _structural_identity(
    kind: str,
    phase: str,
    *,
    callsite_id: str | None = None,
    sync_origin: str | None = None,
    sync_ordinal: int | None = None,
) -> dict[str, Any]:
    identity: dict[str, Any] = {
        "kind": kind,
        "experiment_id": "exposedpath-q0-synthetic",
        "wmpc_id": "q0-controlled",
        "run_id": "synthetic-run",
        "run_role": "Engineering",
        "pass_id": "Pass1",
        "request_id": "req-0",
        "repeat_id": "repeat-0",
        "phase": phase,
    }
    if callsite_id is not None:
        identity["callsite_id"] = callsite_id
    if sync_origin is not None:
        identity["sync_origin"] = sync_origin
    if sync_ordinal is not None:
        identity["sync_ordinal"] = sync_ordinal
    return identity


def _structural_bundle(case_id: str) -> tuple[dict[str, Any], int, int]:
    """构造 in-scope case 的 Canonical 结构事实与 (A/B window 边界)。"""

    nvtx: list[dict[str, Any]] = []
    cuda_api: list[dict[str, Any]] = []
    cuda_sync: list[dict[str, Any]] = []
    device_activity: list[dict[str, Any]] = []
    cuda_event: list[dict[str, Any]] = []

    def add_range(
        kind: str,
        phase: str,
        start: int,
        end: int,
        record_id: str,
        *,
        global_tid: int = 1001,
        **extra: Any,
    ) -> None:
        nvtx.append(
            _nvtx(
                _structural_identity(kind, phase, **extra),
                start,
                end,
                record_id,
                global_tid=global_tid,
            )
        )

    def add_api(
        record_id: str,
        api_name: str,
        start: int,
        end: int,
        *,
        global_tid: int = 1001,
        correlation_id: int | None = None,
        event_id: int | None = None,
    ) -> None:
        cuda_api.append(
            {
                "record_id": record_id,
                "start_ns": start,
                "end_ns": end,
                "global_tid": global_tid,
                "correlation_id": correlation_id,
                "api_name": api_name,
                "event_id": event_id,
                "return_value": 0,
            }
        )

    def add_activity(
        label: str,
        start: int,
        end: int,
        *,
        correlation_id: int | None,
        stream_id: int,
    ) -> None:
        device_activity.append(
            {
                "record_id": label,
                "start_ns": start,
                "end_ns": end,
                "clock_domain_id": _CLOCK,
                "device_id": 0,
                "context_id": 1,
                "stream_id": stream_id,
                "activity_kind": "KERNEL",
                "name": label,
                "correlation_id": correlation_id,
                "attributes": {},
            }
        )

    def add_sync(
        label: str,
        api_name: str,
        start: int,
        end: int,
        *,
        global_tid: int = 1001,
        stream_id: int = 2,
        ordinal: int = 0,
        event_id: int | None = None,
        event_sync_id: int | None = None,
    ) -> None:
        add_range(
            "sync",
            "decode",
            start,
            end,
            f"nvtx:sync:{label}",
            global_tid=global_tid,
            callsite_id=label,
            sync_origin="q0_controlled",
            sync_ordinal=ordinal,
        )
        cuda_sync.append(
            {
                "record_id": label,
                "start_ns": start,
                "end_ns": end,
                "global_tid": global_tid,
                "device_id": 0,
                "context_id": 1,
                "stream_id": stream_id,
                "sync_type_id": 1,
                "sync_type_name": "SYNC",
                "sync_type_label": "SYNC",
                "runtime_mapping_count": 1,
                "runtime_api_name": api_name,
                "runtime_start_ns": start,
                "runtime_end_ns": end,
                "runtime_global_tid": global_tid,
                "runtime_record_id": f"api:{label}",
                "event_id": event_id,
                "event_sync_id": event_sync_id,
            }
        )

    if case_id == "Q0-EXTERNAL-001":
        # launch marker/API 完全位于 request 之前，device activity 延伸进入 request。
        add_range("request", "full_request", 30, 130, "nvtx:request")
        add_range("phase", "decode", 30, 130, "nvtx:decode")
        add_range(
            "marker", "decode", 10, 20, "nvtx:marker:K_EXTERNAL",
            callsite_id="K_EXTERNAL",
        )
        add_api("api:K_EXTERNAL", "cudaLaunchKernel", 11, 19, correlation_id=7)
        add_activity("K_EXTERNAL", 40, 110, correlation_id=7, stream_id=2)
        add_sync("S_DEVICE", "cudaDeviceSynchronize", 80, 120)
        window_start, window_end = 30, 130
    elif case_id == "Q0-MISSING-CORR-001":
        # Gate 6 Missing-Corr oracle amendment v0.2 冻结的结构事实：
        # correlation 与 enqueue provenance 都缺失，且 activity.start >=
        # sync.host_start（目标 Windows/WDDM 栈上普通 launch->sync 的真实形状）。
        # 只输入结构事实，最终 reason / wait set / terminal / B 状态由正常化链推导。
        add_range("request", "full_request", 0, 100, "nvtx:request")
        add_range("phase", "decode", 0, 100, "nvtx:decode")
        add_activity("K_UNMAPPED", 60, 95, correlation_id=None, stream_id=2)
        add_sync("S_STREAM", "cudaStreamSynchronize", 50, 90)
        window_start, window_end = 0, 100
    elif case_id == "Q0-MULTITHREAD-ORDERED-001":
        add_range("request", "full_request", 0, 100, "nvtx:request")
        add_range("phase", "decode", 0, 100, "nvtx:decode")
        add_range(
            "marker", "decode", 1, 9, "nvtx:marker:WORKER_THREAD_A",
            global_tid=2002, callsite_id="WORKER_THREAD_A",
        )
        add_range(
            "marker", "decode", 1, 9, "nvtx:marker:K_THREAD_A",
            global_tid=2002, callsite_id="K_THREAD_A",
        )
        add_api(
            "api:K_THREAD_A", "cudaLaunchKernel", 2, 8,
            global_tid=2002, correlation_id=127,
        )
        add_activity("K_THREAD_A", 10, 45, correlation_id=127, stream_id=2)
        add_range(
            "marker", "decode", 11, 15, "nvtx:marker:EVENT_RECORD_THREAD_A",
            global_tid=2002, callsite_id="EVENT_RECORD_THREAD_A",
        )
        add_api(
            "api:EVENT_RECORD_THREAD_A", "cudaEventRecord", 12, 14,
            global_tid=2002, correlation_id=129, event_id=1,
        )
        add_range(
            "marker", "decode", 15, 19, "nvtx:marker:WORKER_THREAD_B",
            global_tid=3003, callsite_id="WORKER_THREAD_B",
        )
        add_range(
            "marker", "decode", 20, 26, "nvtx:marker:K_THREAD_B",
            global_tid=3003, callsite_id="K_THREAD_B",
        )
        add_api(
            "api:K_THREAD_B", "cudaLaunchKernel", 21, 25,
            global_tid=3003, correlation_id=131,
        )
        add_activity("K_THREAD_B", 50, 85, correlation_id=131, stream_id=4)
        add_sync("S_THREAD_B", "cudaStreamSynchronize", 60, 95, global_tid=3003, stream_id=4)
        # cudaStreamWaitEvent 是 DEPENDENCY_EDGE：没有 marker，边只依赖 event node。
        cuda_sync.append(
            {
                "record_id": "edge:S_THREAD_B",
                "start_ns": 15,
                "end_ns": 19,
                "global_tid": 3003,
                "device_id": 0,
                "context_id": 1,
                "stream_id": 4,
                "sync_type_id": 2,
                "sync_type_name": "STREAM_WAIT_EVENT",
                "sync_type_label": "STREAM_WAIT_EVENT",
                "runtime_mapping_count": 1,
                "runtime_api_name": "cudaStreamWaitEvent",
                "runtime_start_ns": 15,
                "runtime_end_ns": 19,
                "runtime_global_tid": 3003,
                "runtime_record_id": "api:EVENT_MT_WAIT",
                "event_id": 1,
                "event_sync_id": 1,
            }
        )
        cuda_event.append(
            {
                "record_id": "event:EVENT_MT",
                "correlation_id": 129,
                "timestamp_ns": 13,
                "device_id": 0,
                "context_id": 1,
                "stream_id": 2,
                "event_id": 1,
                "event_sync_id": 1,
            }
        )
        window_start, window_end = 0, 100
    elif case_id == "Q0-OVERLAPPING-HOST-SYNC-001":
        add_range("request", "full_request", 0, 100, "nvtx:request")
        add_range("phase", "decode", 0, 100, "nvtx:decode")
        add_range(
            "marker", "decode", 10, 18, "nvtx:marker:K_A", callsite_id="K_A",
        )
        add_api("api:K_A", "cudaLaunchKernel", 11, 17, correlation_id=127)
        add_activity("K_A", 20, 85, correlation_id=127, stream_id=2)
        add_range(
            "marker", "decode", 19, 27, "nvtx:marker:K_B", callsite_id="K_B",
        )
        add_api("api:K_B", "cudaLaunchKernel", 20, 26, correlation_id=129)
        add_activity("K_B", 30, 95, correlation_id=129, stream_id=4)
        add_range(
            "marker", "decode", 49, 50, "nvtx:marker:WORKER_SYNC_A",
            global_tid=2002, callsite_id="WORKER_SYNC_A",
        )
        add_sync("S_A", "cudaStreamSynchronize", 50, 90, global_tid=2002, stream_id=2)
        add_range(
            "marker", "decode", 59, 60, "nvtx:marker:WORKER_SYNC_B",
            global_tid=3003, callsite_id="WORKER_SYNC_B",
        )
        add_sync(
            "S_B", "cudaStreamSynchronize", 60, 100,
            global_tid=3003, stream_id=4, ordinal=1,
        )
        window_start, window_end = 0, 100
    else:  # pragma: no cover - guarded by _STRUCTURAL_CASE_IDS
        raise ValueError(f"未支持的结构化 synthetic case: {case_id}")

    bundle = {
        "manifest": {
            "identity": {"status": "VALID", "issues": []},
            "observation_validity": {"status": "valid", "issues": []},
            "clock": {"clock_domain_id": _CLOCK},
            "execution_context": {
                "default_stream_mode": "PER_THREAD",
                "selected_device_id": 0,
            },
        },
        "records": {
            "nvtx": nvtx,
            "cuda_api": cuda_api,
            "cuda_sync": cuda_sync,
            "device_activity": device_activity,
            "cuda_event": cuda_event,
            "context": [{"context_id": 1, "device_id": 0, "null_stream_id": 0}],
            "stream": [
                {"context_id": 1, "stream_id": 2, "flag": 0},
                {"context_id": 1, "stream_id": 4, "flag": 0},
            ],
            "diagnostic": [],
        },
    }
    return bundle, window_start, window_end


def _structural_inventory(case_id: str) -> tuple[dict[str, Any], int, int]:
    """把 in-scope case 的结构事实交给生产 `sync_semantics` 正常化链。"""

    bundle, window_start, window_end = _structural_bundle(case_id)
    return build_semantic_inventory(bundle), window_start, window_end


def _observed_case(case: Mapping[str, Any]) -> dict[str, Any]:
    case_id = str(case["case_id"])
    if case_id in _STRUCTURAL_CASE_IDS:
        inventory, window_start, window_end = _structural_inventory(case_id)
        s_records = analyze_semantic_inventory(inventory)
        inputs = _ab_inputs(
            case_id,
            inventory,
            inventory["syncs"],
            s_records,
            window_start=window_start,
            window_end=window_end,
        )
    else:
        inventory, syncs = _profile(case)
        s_records = [analyze_sync_semantics(inventory, sync) for sync in syncs]
        inputs = _ab_inputs(case_id, inventory, syncs, s_records)
    a_records = calculate_a_windows(inputs)
    b_records = calculate_b_syncs(inputs)
    a_record = dict(a_records[0]) if a_records else None
    b_by_id = {record["sync_id"]: record for record in b_records}
    activity_kind = {
        item["record_id"]: item.get("activity_kind") for item in inventory["activities"]
    }
    observed_syncs = []
    for s_record in s_records:
        b_record = b_by_id[s_record["sync_id"]]
        terminal_id = s_record["terminal"]["activity_id"]
        observed_syncs.append(
            {
                "sync_label": s_record["sync_id"],
                "sync_start_ns": s_record["host_start_ns"],
                "sync_end_ns": s_record["host_end_ns"],
                "wait_set_status": s_record["wait_set_status"],
                "wait_set_activity_labels": list(s_record["wait_set_activity_ids"]),
                "terminal": {
                    "status": s_record["terminal"]["status"],
                    "kind": s_record["terminal"]["kind"],
                    "activity_label": terminal_id,
                },
                "validity": s_record["validity"],
                "primary_reason": s_record["primary_reason"],
                "secondary_reasons": list(s_record["secondary_reasons"]),
                "b_status": b_record["validity"],
                "b_timing": {
                    key: b_record[key]
                    for key in (
                        "wait_set_hidden_union_ns",
                        "wait_set_exposed_union_ns",
                        "terminal_pre_sync_ns",
                        "terminal_overlap_sync_ns",
                        "sync_return_tail_ns",
                    )
                },
                "terminal_activity_kind": activity_kind.get(terminal_id),
                "activity_origin_phases": sorted(
                    {
                        phase
                        for phase in s_record["activity_origin_phases"].values()
                        if phase is not None
                    }
                ),
                "sync_owner_phase": s_record["sync_owner_phase"],
                "cross_phase_dependency": s_record["cross_phase_dependency"],
                "a_window": a_record,
            }
        )
    return {
        "case_id": case_id,
        "syncs": observed_syncs,
        "non_sync_api_labels": [
            item["api_label"] for item in case["construction"].get("api_calls", [])
        ],
    }


def build_synthetic_observed(
    *, oracle_cases: Sequence[Mapping[str, Any]] | None = None
) -> dict[str, Any]:
    """运行 23 个显式 construction/profile；不会读取 case.expected。"""

    if oracle_cases is None:
        oracle_cases = load_oracle_bundle()["cases"]
    execution = load_q0_execution_manifest()
    profiles = {case["synthetic_profile"] for case in execution["cases"]}
    case_ids = {str(case["case_id"]) for case in oracle_cases}
    if profiles != case_ids:
        raise ValueError("synthetic profile 与输入 case 集合不一致")
    return {
        "schema_version": "exposedpath-q0-observed/0.2.0",
        "source_kind": "SYNTHETIC_CANONICAL",
        "data_role": "Engineering",
        "research_eligibility": {
            "formal_evidence": False,
            "q0_status": "NOT_RUN",
            "scope": "Q0_SYNTHETIC_ONLY",
        },
        "cases": [_observed_case(case) for case in oracle_cases],
    }


def run_synthetic_q0(output_dir: Path) -> Path:
    """不可覆盖地写出 synthetic observed 和独立 comparison report。"""

    from .q0_evaluator import evaluate_q0_observed

    output = Path(output_dir)
    if output.exists():
        raise FileExistsError(f"拒绝覆盖已有合成 Q0 输出: {output}")
    observed = build_synthetic_observed()
    report = evaluate_q0_observed(load_oracle_bundle(), observed)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}.tmp-", dir=output.parent))
    observed_name = "synthetic_observed.json"
    observed_bytes = (json.dumps(observed, indent=2, sort_keys=True) + "\n").encode("utf-8")
    (temporary / observed_name).write_bytes(observed_bytes)
    report["observed_file"] = observed_name
    report["observed_sha256"] = hashlib.sha256(observed_bytes).hexdigest().upper()
    (temporary / "q0_synthetic_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(output)
    return output / "q0_synthetic_report.json"
