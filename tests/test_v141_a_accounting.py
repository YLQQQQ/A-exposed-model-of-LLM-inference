"""手算 A 墙钟记账夹具：只向 A 提供 Canonical 事实和已恢复的 S 语义。"""

from __future__ import annotations

import importlib

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


def _api(record_id: str, start: int, end: int, name: str, correlation: int | None) -> dict[str, object]:
    return {"record_id": record_id, "start_ns": start, "end_ns": end, "api_name": name, "correlation_id": correlation}


def _activity(record_id: str, start: int, end: int, kind: str, correlation: int | None) -> dict[str, object]:
    return {"record_id": record_id, "start_ns": start, "end_ns": end, "activity_kind": kind, "correlation_id": correlation}


def _inputs(*, global_reasons: tuple[str, ...] = (), windows: tuple[RequestPhaseWindow, ...] | None = None, apis: tuple[dict[str, object], ...] | None = None, syncs: tuple[dict[str, object], ...] | None = None, activities: tuple[dict[str, object], ...] | None = None) -> ABInputs:
    activities = activities or (
        _activity("kernel", 30, 50, "KERNEL", 11),
        _activity("memop", 45, 55, "MEMCPY", 12),
    )
    apis = apis or (
        _api("submit", 10, 12, "cudaLaunchKernel", 11),
        _api("event-record", 12, 16, "cudaEventRecord", None),
        _api("stream-wait", 16, 20, "cudaStreamWaitEvent", None),
        _api("second-thread-submit", 14, 18, "cudaEventRecord", None),
        _api("query", 20, 30, "cudaEventQuery", None),
        _api("submit-during-sync", 50, 60, "cudaEventRecord", None),
        _api("unknown", 70, 75, "cudaMystery", None),
    )
    syncs = syncs or (
        _sync("valid", 30, 60, "VALID_NONEMPTY", ["kernel", "memop"]),
        _sync("overlap-empty", 40, 58, "VALID_EMPTY", []),
        _sync("invalid", 60, 70, "INVALID", [], "MISSING_CORRELATION"),
    )
    canonical = CanonicalBundle(
        manifest={}, records={"cuda_api": apis, "device_activity": activities}, schema={},
        cuda_api_by_id={str(row["record_id"]): row for row in apis},
        activity_by_id={str(row["record_id"]): row for row in activities},
        physical_sync_by_id={},
    )
    return ABInputs(canonical=canonical, s_manifest={}, s_records=syncs,
                    windows=windows or (_window(),), global_quality_reasons=global_reasons,
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
