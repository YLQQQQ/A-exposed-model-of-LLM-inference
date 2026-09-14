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
from .sync_semantics import analyze_sync_semantics, classify_cuda_api


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
        if case_id == "Q0-MISSING-CORR-001":
            kwargs.update(
                ownership_status="INVALID",
                ownership_reasons=("MISSING_ACTIVITY_CORRELATION",),
            )
        elif case_id == "Q0-EXTERNAL-001":
            kwargs.update(
                ownership_status="INVALID",
                ownership_reasons=("EXTERNAL_OWNERSHIP_IN_SCOPE",),
            )
        elif case_id == "Q0-INVOCATION-BLEED-001":
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


def _nvtx(identity: Mapping[str, Any], start: int, end: int, record_id: str) -> dict[str, Any]:
    payload = dict(identity)
    text = "EXPOSEDPATH_JSON_V1:" + json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return {
        "record_id": record_id,
        "start_ns": start,
        "end_ns": end,
        "global_tid": 1001,
        "structured_identity": payload,
        "text": text,
    }


def _ab_inputs(
    case_id: str,
    inventory: Mapping[str, Any],
    raw_syncs: Sequence[Mapping[str, Any]],
    s_records: Sequence[Mapping[str, Any]],
) -> ABInputs:
    end = max([100, *[int(sync["host_end_ns"]) for sync in raw_syncs]])
    request_identity = _identity("full_request")
    request_identity["kind"] = "request"
    nvtx = [_nvtx(request_identity, 0, end, "nvtx:request")]
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
        start_ns=0,
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


def _observed_case(case: Mapping[str, Any]) -> dict[str, Any]:
    case_id = str(case["case_id"])
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
