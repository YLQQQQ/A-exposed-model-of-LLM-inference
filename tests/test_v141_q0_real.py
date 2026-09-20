"""真实 Q0 观测适配器的稳定标签恢复测试。"""

from __future__ import annotations

from copy import deepcopy

import pytest

from exposedpath_v141.ab_inputs import ABInputs, CanonicalBundle
from exposedpath_v141.q0_real import (
    Q0RealObservedError,
    _non_sync_api_labels,
    build_real_q0_case,
    map_real_activity_labels,
)


def _records():
    return {
        "device_activity": [
            {"record_id": "activity:1", "correlation_id": 7},
        ],
        "cuda_api": [
            {"record_id": "api:1", "correlation_id": 7, "global_tid": 99, "start_ns": 10, "end_ns": 12},
        ],
        "nvtx": [
            {
                "record_id": "nvtx:1", "global_tid": 99, "start_ns": 9, "end_ns": 13,
                "structured_identity": {"kind": "marker", "callsite_id": "K_ONE"},
            }
        ],
    }


def test_real_activity_label_requires_correlation_and_covering_marker():
    assert map_real_activity_labels(_records()) == {"activity:1": "K_ONE"}


def test_real_activity_label_rejects_ambiguous_marker():
    records = _records()
    duplicate = deepcopy(records["nvtx"][0])
    duplicate["record_id"] = "nvtx:2"
    duplicate["structured_identity"]["callsite_id"] = "K_TWO"
    records["nvtx"].append(duplicate)

    with pytest.raises(Q0RealObservedError, match="无法唯一关联稳定 marker"):
        map_real_activity_labels(records)


def test_real_activity_label_rejects_missing_correlation():
    records = _records()
    records["device_activity"][0]["correlation_id"] = None

    with pytest.raises(Q0RealObservedError, match="无法唯一关联 launch API"):
        map_real_activity_labels(records)


def _api_row(
    record_id: str,
    api_name: str,
    *,
    global_tid: int = 99,
    start: int = 10,
    end: int = 12,
) -> dict:
    return {
        "record_id": record_id,
        "api_name": api_name,
        "global_tid": global_tid,
        "start_ns": start,
        "end_ns": end,
    }


def _marker_row(
    record_id: str,
    callsite_id: str,
    *,
    global_tid: int = 99,
    start: int = 9,
    end: int = 13,
) -> dict:
    return {
        "record_id": record_id,
        "global_tid": global_tid,
        "start_ns": start,
        "end_ns": end,
        "structured_identity": {"kind": "marker", "callsite_id": callsite_id},
    }


def _labeled_records() -> dict:
    """四个 marker：NON_SYNC query、DEPENDENCY_EDGE event record、UNSUPPORTED copy、UNCLASSIFIED。"""

    return {
        "cuda_api": [
            _api_row("api:query", "cudaEventQuery_v3020", start=10, end=12),
            _api_row("api:event-record", "cudaEventRecord", start=20, end=22),
            _api_row("api:copy", "cudaMemcpy", start=30, end=32),
            _api_row("api:mystery", "mysteryCudaWait", start=40, end=42),
        ],
        "nvtx": [
            _marker_row("nvtx:query", "Q_EVENT", start=9, end=13),
            _marker_row("nvtx:event-record", "EVENT_RECORD_THREAD_A", start=19, end=23),
            _marker_row("nvtx:copy", "S_SYNC_COPY", start=29, end=33),
            _marker_row("nvtx:mystery", "K_MYSTERY", start=39, end=43),
        ],
    }


def test_non_sync_api_labels_accept_only_registry_non_sync_roles():
    """Gate 6 Sync Projection Amendment v0.1 §4：只有 registry role `NON_SYNC` 可进入。"""

    assert _non_sync_api_labels(_labeled_records(), set()) == ["Q_EVENT"]


def test_non_sync_api_labels_respect_excluded_labels():
    assert _non_sync_api_labels(_labeled_records(), {"Q_EVENT"}) == []


def _minimal_inputs(s_records: list[dict]) -> ABInputs:
    records = {
        kind: ()
        for kind in (
            "nvtx",
            "cuda_api",
            "cuda_sync",
            "device_activity",
            "cuda_event",
            "context",
            "stream",
            "diagnostic",
        )
    }
    canonical = CanonicalBundle(
        manifest={},
        records=records,
        schema={},
        cuda_api_by_id={},
        activity_by_id={},
        physical_sync_by_id={},
    )
    return ABInputs(
        canonical=canonical,
        s_manifest={},
        s_records=tuple(s_records),
        windows=(),
        global_quality_reasons=(),
        window_discovery_issues=(),
    )


def test_build_real_q0_case_still_fails_closed_without_semantic_sync_callsite():
    """`callsite_id` 非空检查保留：只对 semantic sync 生效，且继续 fail closed。"""

    inputs = _minimal_inputs([{"request_id": "Q0-QUERY-001", "callsite_id": None}])

    with pytest.raises(Q0RealObservedError, match="缺失 callsite_id"):
        build_real_q0_case("Q0-QUERY-001", inputs, [], [])
