"""真实 Q0 观测适配器的稳定标签恢复测试。"""

from __future__ import annotations

from copy import deepcopy

import pytest

from exposedpath_v141.q0_real import Q0RealObservedError, map_real_activity_labels


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
