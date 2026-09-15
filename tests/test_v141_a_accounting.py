"""手算 A 墙钟记账夹具：只向 A 提供 Canonical 事实和已恢复的 S 语义。"""

from __future__ import annotations

import importlib
import json
from dataclasses import replace

import pytest

from exposedpath_v141.ab_inputs import ABInputs, CanonicalBundle, RequestPhaseWindow


def _accounting_module():
    try:
        return importlib.import_module("exposedpath_v141.a_accounting")
    except ModuleNotFoundError as exc:
        pytest.fail(f"A accounting 尚未实现: {exc}")


def _window(phase: str = "full_request", start: int = 0, end: int = 100) -> RequestPhaseWindow:
    return RequestPhaseWindow(
        window_id=f"window:{phase}:{start}:{end}",
        experiment_id="experiment-1", wmpc_id="wmpc-1", run_id="run-1",
        run_role="Engineering", pass_id="pass-1", request_id="request-1",
        repeat_id="repeat-1", phase=phase, start_ns=start, end_ns=end,
        nvtx_record_id="nvtx:1",
    )


def _sync(sync_id: str, start: int, end: int, validity: str, wait_set: list[str], reason: str | None = None) -> dict[str, object]:
    return {
        "sync_id": sync_id,
        "host_start_ns": start,
        "host_end_ns": end,
        "validity": validity,
        "wait_set_activity_ids": wait_set,
        "primary_reason": reason,
        "secondary_reasons": [] if reason is None else [reason],
    }


def _api(record_id: str, start: int, end: int, name: str, correlation: int | None, global_tid: int | None = 101) -> dict[str, object]:
    return {"record_id": record_id, "start_ns": start, "end_ns": end, "api_name": name, "correlation_id": correlation, "global_tid": global_tid}


def _activity(record_id: str, start: int, end: int, kind: str, correlation: int | None) -> dict[str, object]:
    return {"record_id": record_id, "start_ns": start, "end_ns": end, "activity_kind": kind, "correlation_id": correlation}


def _nvtx(window: RequestPhaseWindow, global_tid: int = 101, request_id: str | None = None) -> dict[str, object]:
    identity = {
        "kind": "request" if window.phase == "full_request" else "phase",
        "experiment_id": window.experiment_id, "wmpc_id": window.wmpc_id,
        "run_id": window.run_id, "run_role": window.run_role, "pass_id": window.pass_id,
        "request_id": request_id or window.request_id, "repeat_id": window.repeat_id,
        "phase": window.phase,
    }
    return {
        "record_id": window.nvtx_record_id, "start_ns": window.start_ns, "end_ns": window.end_ns,
        "global_tid": global_tid,
        "text": "EXPOSEDPATH_JSON_V1:" + json.dumps(identity),
        "structured_identity": identity,
    }


def _ownership_marker(
    window: RequestPhaseWindow, record_id: str, global_tid: int, start: int, end: int,
    request_id: str | None = None,
) -> dict[str, object]:
    """Marker 仅证明 worker-thread invocation ownership，绝不定义 A phase window。"""
    marker = _nvtx(window, global_tid=global_tid, request_id=request_id)
    marker.update({"record_id": record_id, "start_ns": start, "end_ns": end})
    marker["structured_identity"] = {**marker["structured_identity"], "kind": "marker"}
    marker["text"] = "EXPOSEDPATH_JSON_V1:" + json.dumps(marker["structured_identity"])
    return marker


def _inputs(*, global_reasons: tuple[str, ...] = (), windows: tuple[RequestPhaseWindow, ...] | None = None, apis: tuple[dict[str, object], ...] | None = None, syncs: tuple[dict[str, object], ...] | None = None, activities: tuple[dict[str, object], ...] | None = None, nvtx: tuple[dict[str, object], ...] | None = None) -> ABInputs:
    activities = activities if activities is not None else (
        _activity("kernel", 30, 50, "KERNEL", 11),
        _activity("memop", 45, 55, "MEMCPY", 12),
    )
    apis = apis if apis is not None else (
        _api("submit", 10, 12, "cudaLaunchKernel", 11),
        _api("event-record", 12, 16, "cudaEventRecord", None),
        _api("stream-wait", 16, 20, "cudaStreamWaitEvent", None),
        _api("second-thread-submit", 14, 18, "cudaEventRecord", None),
        _api("query", 20, 30, "cudaEventQuery", None),
        _api("submit-during-sync", 50, 60, "cudaEventRecord", None),
        _api("unknown", 70, 75, "cudaMystery", None),
    )
    syncs = syncs if syncs is not None else (
        _sync("valid", 30, 60, "VALID_NONEMPTY", ["kernel", "memop"]),
        _sync("overlap-empty", 40, 58, "VALID_EMPTY", []),
        _sync("invalid", 60, 70, "INVALID", [], "MISSING_CORRELATION"),
    )
    windows = windows if windows is not None else (_window(),)
    nvtx = nvtx if nvtx is not None else tuple(_nvtx(window) for window in windows)
    canonical = CanonicalBundle(
        manifest={}, records={"cuda_api": apis, "device_activity": activities, "nvtx": nvtx}, schema={},
        cuda_api_by_id={str(row["record_id"]): row for row in apis},
        activity_by_id={str(row["record_id"]): row for row in activities},
        physical_sync_by_id={},
    )
    return ABInputs(canonical=canonical, s_manifest={}, s_records=syncs,
                    windows=windows, global_quality_reasons=global_reasons,
                    window_discovery_issues=())


def _only_record(inputs: ABInputs) -> dict[str, object]:
    accounting = _accounting_module()
    records = accounting.calculate_a_windows(inputs)
    assert len(records) == 1
    return records[0]


def test_priority_and_conservation_use_unique_atomic_wall_clock_segments():
    record = _only_record(_inputs())

    assert {key: record[key] for key in (
        "T_window_ns", "A_host_path_ns", "A_cuda_api_ns", "A_device_wait_ns",
        "A_sync_residual_ns", "A_unattributed_ns",
    )} == {
        "T_window_ns": 100, "A_host_path_ns": 35, "A_cuda_api_ns": 20,
        "A_device_wait_ns": 25, "A_sync_residual_ns": 5, "A_unattributed_ns": 15,
    }
    assert record["A_cuda_api_submit_ns"] == 10
    assert record["A_cuda_api_non_submit_ns"] == 10
    assert record["A_device_wait_kernel_only_ns"] == 15
    assert record["A_device_wait_memop_only_ns"] == 5
    assert record["A_device_wait_kernel_memop_mixed_ns"] == 5
    assert all(record[field] == 0 for field in (
        "top_level_conservation_error_ns", "top_level_overlap_ns", "top_level_uncovered_ns",
        "out_of_window_ns", "cuda_api_subcategory_conservation_error_ns",
        "device_wait_subcategory_conservation_error_ns",
    ))
    assert record["primary_reason"] == "MISSING_CORRELATION"


def test_unknown_or_conflicting_api_and_unknown_wait_kind_fail_closed_to_unattributed():
    activities = (_activity("unknown-wait", 20, 30, "GRAPH", 1),)
    syncs = (_sync("valid", 20, 30, "VALID_NONEMPTY", ["unknown-wait"]),)
    apis = (
        _api("submit", 0, 10, "cudaLaunchKernel", 1),
        _api("query", 0, 10, "cudaEventQuery", None),
        _api("unknown", 10, 20, "cudaNotInRegistry", None),
    )
    record = _only_record(_inputs(apis=apis, syncs=syncs, activities=activities))

    assert record["A_cuda_api_ns"] == 0
    assert record["A_device_wait_ns"] == 0
    assert record["A_unattributed_ns"] == 30
    assert record["A_host_path_ns"] == 70
    assert record["A_cuda_api_submit_ns"] == 0
    assert record["A_cuda_api_non_submit_ns"] == 0


def test_global_quality_failure_unattributes_every_known_window_and_zero_decode_is_valid():
    windows = (_window("decode", 60, 60), _window("full_request", 0, 100))
    accounting = _accounting_module()
    records = accounting.calculate_a_windows(_inputs(global_reasons=("TRACE_DROPPED_RECORDS",), windows=windows))
    by_phase = {record["phase"]: record for record in records}

    assert by_phase["full_request"]["A_unattributed_ns"] == 100
    assert by_phase["full_request"]["primary_reason"] == "TRACE_DROPPED_RECORDS"
    assert by_phase["decode"]["T_window_ns"] == 0
    assert by_phase["decode"]["A_unattributed_ns"] == 0
    accounting.validate_a_record(by_phase["full_request"])


def test_phase_clipping_and_runtime_validation_reject_nonconserving_record():
    inputs = _inputs(windows=(_window("prefill", 0, 40),), syncs=(
        _sync("cross-phase", 30, 60, "VALID_NONEMPTY", ["kernel"]),
    ))
    record = _only_record(inputs)
    assert record["A_device_wait_ns"] == 10
    assert record["T_window_ns"] == 40

    invalid = dict(record)
    invalid["A_host_path_ns"] = int(invalid["A_host_path_ns"]) + 1
    with pytest.raises(ValueError, match="守恒"):
        _accounting_module().validate_a_record(invalid)

    invalid = dict(record)
    invalid["not_in_frozen_schema"] = 1
    with pytest.raises(ValueError, match="字段集合"):
        _accounting_module().validate_a_record(invalid)


def test_external_or_threadless_api_is_not_owned_by_current_request_window():
    apis = (
        _api("external-thread", 10, 20, "cudaEventQuery", None, global_tid=202),
        _api("threadless", 20, 30, "cudaEventQuery", None, global_tid=None),
    )
    record = _only_record(_inputs(apis=apis, syncs=(), activities=()))

    assert record["A_cuda_api_ns"] == 0
    assert record["A_unattributed_ns"] == 20
    assert record["A_host_path_ns"] == 80
    assert record["primary_reason"] == "CUDA_API_EXTERNAL_THREAD"
    assert "CUDA_API_THREAD_OWNERSHIP_MISSING" in record["secondary_reasons"]


def test_worker_thread_api_uses_same_invocation_marker_not_window_thread():
    first = _window()
    api = _api("worker-query", 10, 20, "cudaEventQuery", None, global_tid=202)
    inputs = _inputs(
        windows=(first,), apis=(api,), syncs=(), activities=(),
        nvtx=(_nvtx(first, global_tid=101), _ownership_marker(first, "marker:worker", 202, 0, 100)),
    )
    records = _accounting_module().calculate_a_windows(inputs)

    assert len(records) == 1
    assert records[0]["A_cuda_api_ns"] == 10
    assert records[0]["A_cuda_api_non_submit_ns"] == 10


def test_cross_phase_api_clips_after_worker_marker_proves_same_invocation():
    prefill = replace(_window("prefill", 0, 50), nvtx_record_id="nvtx:prefill")
    decode = replace(_window("decode", 50, 100), nvtx_record_id="nvtx:decode")
    api = _api("cross-phase-query", 40, 60, "cudaEventQuery", None, global_tid=202)
    inputs = _inputs(
        windows=(prefill, decode), apis=(api,), syncs=(), activities=(),
        nvtx=(
            _nvtx(prefill, global_tid=101), _nvtx(decode, global_tid=101),
            _ownership_marker(prefill, "marker:worker", 202, 0, 100),
        ),
    )
    records = {record["phase"]: record for record in _accounting_module().calculate_a_windows(inputs)}

    assert set(records) == {"prefill", "decode"}
    assert records["prefill"]["A_cuda_api_ns"] == 10
    assert records["decode"]["A_cuda_api_ns"] == 10
    assert records["prefill"]["A_host_path_ns"] == 40
    assert records["decode"]["A_host_path_ns"] == 40


def test_same_invocation_multithread_api_overlap_uses_union_not_thread_sum():
    window = _window()
    apis = (
        _api("main-query", 10, 20, "cudaEventQuery", None, global_tid=101),
        _api("worker-query", 15, 25, "cudaEventQuery", None, global_tid=202),
    )
    record = _only_record(_inputs(
        windows=(window,), apis=apis, syncs=(), activities=(),
        nvtx=(_nvtx(window, global_tid=101), _ownership_marker(window, "marker:worker", 202, 0, 100)),
    ))

    assert record["A_cuda_api_ns"] == 15
    assert record["A_cuda_api_non_submit_ns"] == 15
    assert record["A_host_path_ns"] == 85


def test_conflicting_same_thread_invocation_markers_fail_closed():
    window = _window()
    api = _api("ambiguous-worker-query", 10, 20, "cudaEventQuery", None, global_tid=202)
    record = _only_record(_inputs(
        windows=(window,), apis=(api,), syncs=(), activities=(),
        nvtx=(
            _nvtx(window, global_tid=101),
            _ownership_marker(window, "marker:owner", 202, 0, 100),
            _ownership_marker(window, "marker:conflict", 202, 0, 100, request_id="request-other"),
        ),
    ))

    assert record["A_cuda_api_ns"] == 0
    assert record["A_unattributed_ns"] == 10
    assert record["primary_reason"] == "CUDA_API_IDENTITY_CONFLICT"


def test_non_enclosing_same_thread_marker_is_missing_ownership_evidence():
    window = _window()
    api = _api("unowned-worker-query", 10, 20, "cudaEventQuery", None, global_tid=202)
    record = _only_record(_inputs(
        windows=(window,), apis=(api,), syncs=(), activities=(),
        nvtx=(_nvtx(window, global_tid=101), _ownership_marker(window, "marker:too-short", 202, 0, 5)),
    ))

    assert record["A_cuda_api_ns"] == 0
    assert record["A_unattributed_ns"] == 10
    assert record["primary_reason"] == "CUDA_API_WINDOW_OWNERSHIP_MISSING"


def test_incomplete_enclosing_owner_is_not_ignored_when_a_matching_owner_exists():
    window = _window()
    api = _api("worker-query", 10, 20, "cudaEventQuery", None, global_tid=202)
    incomplete = _ownership_marker(window, "marker:incomplete", 202, 0, 100)
    del incomplete["structured_identity"]["repeat_id"]
    incomplete["text"] = "EXPOSEDPATH_JSON_V1:" + json.dumps(incomplete["structured_identity"])
    record = _only_record(_inputs(
        windows=(window,), apis=(api,), syncs=(), activities=(),
        nvtx=(
            _nvtx(window, global_tid=101),
            _ownership_marker(window, "marker:matching", 202, 0, 100),
            incomplete,
        ),
    ))

    assert record["A_cuda_api_ns"] == 0
    assert record["A_unattributed_ns"] == 10
    assert record["primary_reason"] == "CUDA_API_IDENTITY_MISSING"


def test_invalid_sync_precedes_overlapping_valid_sync_and_two_nonempty_wait_sets_union():
    activities = (
        _activity("kernel", 10, 30, "KERNEL", 1),
        _activity("memop", 20, 40, "MEMCPY", 2),
    )
    syncs = (
        _sync("valid-kernel", 10, 30, "VALID_NONEMPTY", ["kernel"]),
        _sync("invalid", 20, 25, "INVALID", [], "MISSING_CORRELATION"),
        _sync("valid-memop", 20, 40, "VALID_NONEMPTY", ["memop"]),
    )
    record = _only_record(_inputs(apis=(), syncs=syncs, activities=activities))

    assert record["A_device_wait_ns"] == 25
    assert record["A_device_wait_kernel_only_ns"] == 10
    assert record["A_device_wait_kernel_memop_mixed_ns"] == 5
    assert record["A_device_wait_memop_only_ns"] == 10
    assert record["A_unattributed_ns"] == 5
    assert record["A_host_path_ns"] == 70


def test_zero_ns_window_without_global_failure_preserves_both_conservations():
    inputs = _inputs(windows=(_window("decode", 60, 60),), apis=(), syncs=(), activities=())
    record = _only_record(inputs)

    assert record["T_window_ns"] == 0
    assert all(record[field] == 0 for field in (
        "A_host_path_ns", "A_cuda_api_ns", "A_device_wait_ns", "A_sync_residual_ns",
        "A_unattributed_ns", "A_cuda_api_submit_ns", "A_cuda_api_non_submit_ns",
        "A_device_wait_kernel_only_ns", "A_device_wait_memop_only_ns",
        "A_device_wait_kernel_memop_mixed_ns",
    ))
    _accounting_module().validate_a_record(record)


def test_signed_trace_relative_api_before_window_does_not_invalidate_a():
    record = _only_record(
        _inputs(
            apis=(_api("profiler-start", -20, -10, "cudaProfilerStart", None),),
            syncs=(),
            activities=(),
        )
    )

    assert record["T_window_ns"] == 100
    assert record["A_host_path_ns"] == 100
    assert record["A_cuda_api_ns"] == 0
    assert record["A_unattributed_ns"] == 0


def test_missing_sync_time_is_only_allowed_for_unowned_invalid_row():
    invalid_owned = _sync("bad", 10, 20, "VALID_EMPTY", [])
    invalid_owned["host_start_ns"] = None
    invalid_owned["host_end_ns"] = None

    with pytest.raises(ValueError, match="request 外 invalid"):
        _only_record(_inputs(apis=(), syncs=(invalid_owned,), activities=()))


@pytest.mark.parametrize(("field", "value"), (("T_window_ns", 1.5), ("A_host_path_ns", -1)))
def test_runtime_validation_rejects_noninteger_and_negative_ns(field: str, value: object):
    record = _only_record(_inputs(apis=(), syncs=(), activities=()))
    invalid = dict(record)
    invalid[field] = value

    with pytest.raises(ValueError, match="非负整数|长度"):
        _accounting_module().validate_a_record(invalid)
