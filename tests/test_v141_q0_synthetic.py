"""Gate 6 合成 Canonical -> S/A/B -> 独立 oracle 对照。"""

from __future__ import annotations

import json

from exposedpath_v141.cli import main
from exposedpath_v141.q0_synthetic import (
    _STRUCTURAL_CASE_IDS,
    _structural_bundle,
    _structural_inventory,
    build_synthetic_observed,
    run_synthetic_q0,
)
from exposedpath_v141.sync_semantics import (
    analyze_semantic_inventory,
    build_semantic_inventory,
)

_CONCLUDED_FIELDS = (
    "ownership_status",
    "ownership_reasons",
    "validity",
    "wait_set_activity_ids",
    "wait_set_status",
    "primary_reason",
    "secondary_reasons",
)


def test_all_23_profiles_run_through_production_semantics_without_q0_upgrade(tmp_path):
    report_path = run_synthetic_q0(tmp_path / "synthetic-q0")
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert report["summary"] == {
        "required_case_count": 23,
        "passed_case_count": 23,
        "failed_case_count": 0,
    }
    assert report["verdict"] == "SYNTHETIC_PASS"
    assert report["evidence_scope"] == "SYNTHETIC_ONLY"
    assert report["research_eligibility"]["q0_status"] == "NOT_RUN"
    assert report["research_eligibility"]["formal_evidence"] is False
    observed_path = report_path.parent / report["observed_file"]
    observed = json.loads(observed_path.read_text(encoding="utf-8"))
    assert len(observed["cases"]) == 23


def test_synthetic_output_directory_is_immutable(tmp_path):
    output_dir = tmp_path / "synthetic-q0"
    run_synthetic_q0(output_dir)

    try:
        run_synthetic_q0(output_dir)
    except FileExistsError:
        pass
    else:
        raise AssertionError("必须拒绝覆盖已有合成 Q0 输出")


def test_synthetic_q0_cli_reports_scope_without_upgrading_q0(tmp_path, capsys):
    output_dir = tmp_path / "synthetic-q0"

    assert main(["run-q0-synthetic", "--output-dir", str(output_dir)]) == 0

    printed = capsys.readouterr().out
    assert "verdict: SYNTHETIC_PASS" in printed
    assert "evidence_scope: SYNTHETIC_ONLY" in printed
    assert "q0_execution_status: NOT_RUN" in printed
    assert (output_dir / "q0_synthetic_report.json").is_file()


def test_structural_proxies_feed_structure_only_without_semantic_conclusions():
    for case_id in sorted(_STRUCTURAL_CASE_IDS):
        bundle, _, _ = _structural_bundle(case_id)
        for kind, rows in bundle["records"].items():
            for row in rows:
                for field in _CONCLUDED_FIELDS:
                    assert field not in row, f"{case_id}.{kind} 预置了 {field}"


def test_structural_proxies_derive_reasons_from_structure():
    external_inventory, _, _ = _structural_inventory("Q0-EXTERNAL-001")
    external_activity = external_inventory["activities"][0]
    assert external_activity["ownership_reasons"] == ["EXTERNAL_OWNERSHIP_IN_SCOPE"]

    missing_inventory, _, _ = _structural_inventory("Q0-MISSING-CORR-001")
    missing_activity = missing_inventory["activities"][0]
    assert missing_activity["ownership_reasons"] == ["MISSING_ACTIVITY_CORRELATION"]
    assert missing_activity["enqueue_start_ns"] is None

    multithread = analyze_semantic_inventory(
        _structural_inventory("Q0-MULTITHREAD-ORDERED-001")[0]
    )[0]
    assert multithread["wait_set_activity_ids"] == ["K_THREAD_A", "K_THREAD_B"]
    assert [edge["edge_type"] for edge in multithread["dependency_edges"]] == [
        "EVENT_RECORD_CAPTURE",
        "STREAM_WAIT_EVENT",
        "SAME_STREAM_ORDER",
    ]

    overlapping_inventory = _structural_inventory("Q0-OVERLAPPING-HOST-SYNC-001")[0]
    assert [
        (record["record_id"], record["ownership_status"], record["sync_owner_phase"])
        for record in overlapping_inventory["syncs"]
    ] == [("S_A", "VALID", "decode"), ("S_B", "VALID", "decode")]
    overlapping = analyze_semantic_inventory(overlapping_inventory)
    assert [record["sync_id"] for record in overlapping] == ["S_A", "S_B"]
    assert [record["wait_set_activity_ids"] for record in overlapping] == [["K_A"], ["K_B"]]


def test_structural_proxies_without_native_marker_fail_closed():
    external_bundle, _, _ = _structural_bundle("Q0-EXTERNAL-001")
    external_bundle["records"]["nvtx"] = [
        row
        for row in external_bundle["records"]["nvtx"]
        if row["record_id"] != "nvtx:marker:K_EXTERNAL"
    ]
    external = build_semantic_inventory(external_bundle)["activities"][0]
    assert external["ownership_status"] == "INVALID"
    assert external["ownership_reasons"] == ["INVOCATION_BOUNDARY_INVALID"]

    multithread_bundle, _, _ = _structural_bundle("Q0-MULTITHREAD-ORDERED-001")
    multithread_bundle["records"]["nvtx"] = [
        row
        for row in multithread_bundle["records"]["nvtx"]
        if row["record_id"] != "nvtx:marker:EVENT_RECORD_THREAD_A"
    ]
    multithread = analyze_semantic_inventory(
        build_semantic_inventory(multithread_bundle)
    )[0]
    assert multithread["wait_set_activity_ids"] == ["K_THREAD_B"]
    assert multithread["validity"] == "INVALID"


def test_missing_corr_structural_proxy_derives_frozen_reason_pair():
    """v0.2 冻结的形状：correlation 缺失 + activity.start >= sync.host_start。"""

    bundle, _, _ = _structural_bundle("Q0-MISSING-CORR-001")
    record = analyze_semantic_inventory(build_semantic_inventory(bundle))[0]

    assert record["primary_reason"] == "MISSING_ACTIVITY_CORRELATION"
    assert record["secondary_reasons"] == ["SUBMISSION_ORDER_AMBIGUOUS"]
    assert record["validity"] == "INVALID"
    assert record["submission_evidence"]["K_UNMAPPED"] == {
        "status": "AMBIGUOUS",
        "proof": None,
        "reason": "SUBMISSION_ORDER_AMBIGUOUS",
    }


def test_missing_corr_structural_proxy_exposes_submission_order_from_timing():
    """secondary 由时间关系推导：一旦 activity 早于 sync 入口，ambiguity 必须消失。"""

    bundle, _, _ = _structural_bundle("Q0-MISSING-CORR-001")
    for row in bundle["records"]["device_activity"]:
        row["start_ns"] = 20
        row["end_ns"] = 30
    record = analyze_semantic_inventory(build_semantic_inventory(bundle))[0]

    assert record["primary_reason"] == "MISSING_ACTIVITY_CORRELATION"
    assert record["secondary_reasons"] == []
    assert record["submission_evidence"]["K_UNMAPPED"]["proof"] == "GPU_STARTED_BEFORE_SYNC"


def test_sync_d2h_unsupported_synthetic_keeps_single_unsupported_sync():
    """Gate 6 Sync Projection Amendment v0.1：synthetic 的 UNSUPPORTED 期望保持不变。"""

    observed = build_synthetic_observed()
    case = next(
        item for item in observed["cases"] if item["case_id"] == "Q0-SYNC-D2H-UNSUPPORTED-001"
    )

    assert [row["sync_label"] for row in case["syncs"]] == ["S_SYNC_COPY"]
    record = case["syncs"][0]
    assert record["validity"] == "INVALID"
    assert record["primary_reason"] == "UNSUPPORTED_SYNC_API"
    assert record["wait_set_activity_labels"] == []
    assert record["terminal"] == {
        "status": "INVALID",
        "kind": "NONE",
        "activity_label": None,
    }


def test_synthetic_projection_never_fabricates_api_backed_duplicate_syncs():
    """synthetic 构造只输入结构事实：不得额外合成 API-backed semantic sync。"""

    observed = build_synthetic_observed()

    assert not [
        (case["case_id"], row["sync_label"])
        for case in observed["cases"]
        for row in case["syncs"]
        if str(row["sync_label"]).startswith("cuda_api_sync:")
    ]
