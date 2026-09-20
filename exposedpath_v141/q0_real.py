"""将真实 Q0 Canonical/S/A/B 证据投影为独立 evaluator 输入。"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
from pathlib import Path
import tempfile
from typing import Any

from .ab_bundle import load_ab_bundle
from .ab_inputs import ABInputs, load_ab_inputs
from .q0_oracle import load_oracle_bundle
from .sync_semantics import classify_cuda_api


class Q0RealObservedError(ValueError):
    """真实 Q0 输入不唯一、不完整或 lineage 不一致。"""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _marker_identity(record: Mapping[str, Any]) -> Mapping[str, Any] | None:
    identity = record.get("structured_identity")
    return identity if isinstance(identity, Mapping) and identity.get("kind") == "marker" else None


def map_real_activity_labels(
    records: Mapping[str, Sequence[Mapping[str, Any]]],
    *, controlled_overrides: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """用 correlation 找 launch API，再用同线程包围 marker 恢复稳定活动标签。"""

    apis = list(records.get("cuda_api", ()))
    markers = [row for row in records.get("nvtx", ()) if _marker_identity(row) is not None]
    result: dict[str, str] = dict(controlled_overrides or {})
    used: set[str] = set(result.values())
    for activity in records.get("device_activity", ()):
        activity_id = str(activity.get("record_id", ""))
        if activity_id in result:
            continue
        correlation = activity.get("correlation_id")
        candidates = [api for api in apis if correlation is not None and api.get("correlation_id") == correlation]
        if len(candidates) != 1:
            raise Q0RealObservedError(f"{activity_id} 无法唯一关联 launch API")
        api = candidates[0]
        covering = []
        for marker in markers:
            identity = _marker_identity(marker)
            if (
                marker.get("global_tid") == api.get("global_tid")
                and isinstance(marker.get("start_ns"), int)
                and isinstance(marker.get("end_ns"), int)
                and marker["start_ns"] <= api["start_ns"]
                and marker["end_ns"] >= api["end_ns"]
                and isinstance(identity.get("callsite_id"), str)
                and identity["callsite_id"]
            ):
                covering.append(str(identity["callsite_id"]))
        covering = sorted(set(covering))
        if len(covering) != 1:
            raise Q0RealObservedError(f"{activity_id} 无法唯一关联稳定 marker: {covering}")
        if covering[0] in used:
            raise Q0RealObservedError(f"活动 marker 标签重复: {covering[0]}")
        result[activity_id] = covering[0]
        used.add(covering[0])
    return result


def _non_sync_api_labels(records: Mapping[str, Sequence[Mapping[str, Any]]], excluded: set[str]) -> list[str]:
    """只恢复 registry role 为 `NON_SYNC` 的 API 标签。

    Gate 6 Sync Projection Amendment v0.1 §4：`DEPENDENCY_EDGE`（event record /
    stream wait event）与 `UNSUPPORTED`（同步 copy 等）不是非同步 API，其 marker
    一律不得进入 `non_sync_api_labels`；判定只依赖冻结的 registry role。
    """

    labels: set[str] = set()
    for api in records.get("cuda_api", ()):
        if classify_cuda_api(str(api.get("api_name", "")))["role"] != "NON_SYNC":
            continue
        for marker in records.get("nvtx", ()):
            identity = _marker_identity(marker)
            label = identity.get("callsite_id") if identity else None
            if (
                isinstance(label, str)
                and label not in excluded
                and marker.get("global_tid") == api.get("global_tid")
                and marker.get("start_ns") <= api.get("start_ns")
                and marker.get("end_ns") >= api.get("end_ns")
            ):
                labels.add(label)
    return sorted(labels)


def build_real_q0_case(
    case_id: str,
    inputs: ABInputs,
    a_records: Sequence[Mapping[str, Any]],
    b_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """从已严格加载的事实构造一个真实 case；不读取 oracle expected。"""

    fault = inputs.canonical.manifest.get("source", {}).get("q0_fault", {})
    overrides: dict[str, str] = {}
    if isinstance(fault, Mapping) and fault.get("fault_injection") == "REMOVE_ACTIVITY_CORRELATION":
        record_id, label = fault.get("target_record_id"), fault.get("target_activity_label")
        if not isinstance(record_id, str) or not isinstance(label, str) or not record_id or not label:
            raise Q0RealObservedError("缺 correlation 故障没有预先记录稳定活动标签")
        overrides[record_id] = label
    activity_labels = map_real_activity_labels(
        inputs.canonical.records, controlled_overrides=overrides
    )
    relevant_s = [row for row in inputs.s_records if row.get("request_id") == case_id]
    sync_labels = [row.get("callsite_id") for row in relevant_s]
    if any(not isinstance(label, str) or not label for label in sync_labels):
        raise Q0RealObservedError(f"{case_id} 存在缺失 callsite_id 的 physical sync")
    if len(sync_labels) != len(set(sync_labels)):
        raise Q0RealObservedError(f"{case_id} sync callsite_id 不唯一")
    b_by_id = {str(row.get("sync_id")): row for row in b_records}
    windows = [
        row for row in a_records
        if row.get("request_id") == case_id and row.get("phase") == "full_request"
    ]
    if len(windows) != 1:
        raise Q0RealObservedError(f"{case_id} 必须恰有一个 full_request A window")
    a_window = dict(windows[0])
    activity_kind = {
        str(row["record_id"]): str(row["activity_kind"])
        for row in inputs.canonical.records["device_activity"]
    }
    syncs: list[dict[str, Any]] = []
    for s_record in relevant_s:
        sync_id = str(s_record["sync_id"])
        if sync_id not in b_by_id:
            raise Q0RealObservedError(f"{case_id}/{sync_id} 缺少 B 记录")
        b_record = b_by_id[sync_id]
        try:
            wait_labels = [activity_labels[str(value)] for value in s_record["wait_set_activity_ids"]]
        except KeyError as exc:
            raise Q0RealObservedError(f"{case_id}/{sync_id} wait-set 活动缺少稳定标签") from exc
        terminal = s_record["terminal"]
        terminal_id = terminal.get("activity_id")
        terminal_label = activity_labels.get(str(terminal_id)) if terminal_id is not None else None
        if terminal_id is not None and terminal_label is None:
            raise Q0RealObservedError(f"{case_id}/{sync_id} terminal 活动缺少稳定标签")
        origins = s_record.get("activity_origin_phases", {})
        origin_values = origins.values() if isinstance(origins, Mapping) else origins
        syncs.append({
            "sync_label": str(s_record["callsite_id"]),
            "sync_start_ns": s_record["host_start_ns"],
            "sync_end_ns": s_record["host_end_ns"],
            "wait_set_status": s_record["wait_set_status"],
            "wait_set_activity_labels": wait_labels,
            "terminal": {"status": terminal["status"], "kind": terminal["kind"], "activity_label": terminal_label},
            "validity": s_record["validity"],
            "primary_reason": s_record["primary_reason"],
            "secondary_reasons": list(s_record["secondary_reasons"]),
            "b_status": b_record["validity"],
            "b_timing": {field: b_record[field] for field in (
                "wait_set_hidden_union_ns", "wait_set_exposed_union_ns", "terminal_pre_sync_ns",
                "terminal_overlap_sync_ns", "sync_return_tail_ns",
            )},
            "terminal_activity_kind": activity_kind.get(str(terminal_id)),
            "activity_origin_phases": sorted({str(value) for value in origin_values if value is not None}),
            "sync_owner_phase": s_record["sync_owner_phase"],
            "cross_phase_dependency": s_record["cross_phase_dependency"],
            "a_window": a_window,
        })
    intervals = []
    for activity in inputs.canonical.records["device_activity"]:
        activity_id = str(activity["record_id"])
        if activity_id in activity_labels:
            intervals.append({
                "activity_label": activity_labels[activity_id],
                "activity_kind": str(activity["activity_kind"]),
                "start_ns": activity["start_ns"],
                "end_ns": activity["end_ns"],
            })
    excluded = set(activity_labels.values()) | {str(value) for value in sync_labels}
    return {
        "case_id": case_id,
        "syncs": sorted(syncs, key=lambda row: (row["sync_start_ns"], row["sync_label"])),
        "non_sync_api_labels": _non_sync_api_labels(inputs.canonical.records, excluded),
        "activity_intervals": sorted(intervals, key=lambda row: row["activity_label"]),
    }


def build_real_q0_observed(
    case_id: str,
    canonical_manifest: Path,
    s_manifest: Path,
    ab_manifest: Path,
    collection_receipt: Path,
) -> dict[str, Any]:
    """严格验证采集 lineage 后生成单 case REAL_CONTROLLED_TRACE observed。"""

    receipt_path = Path(collection_receipt).resolve()
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("schema_version") != "exposedpath-q0-collection/0.2.0" or receipt.get("status") != "COLLECTED":
        raise Q0RealObservedError("collection receipt 非有效已采集状态")
    if receipt.get("case_id") != case_id or receipt.get("q0_status") != "NOT_RUN":
        raise Q0RealObservedError("collection receipt case/资格不匹配")
    inputs = load_ab_inputs(Path(canonical_manifest), Path(s_manifest))
    source = inputs.canonical.manifest.get("source", {})
    canonical_source_manifest = source.get("source_manifest", {}) if isinstance(source, Mapping) else {}
    canonical_raw = source.get("raw", {}) if isinstance(source, Mapping) else {}
    receipt_source = receipt.get("source_manifest", {})
    if canonical_source_manifest.get("sha256") != receipt_source.get("sha256"):
        raise Q0RealObservedError("Canonical 与 collection source manifest lineage 不匹配")
    if canonical_raw.get("sha256") != receipt.get("raw_trace", {}).get("sha256"):
        raise Q0RealObservedError("Canonical 与 collection Raw trace lineage 不匹配")
    bundle = load_ab_bundle(
        Path(ab_manifest), canonical_manifest=Path(canonical_manifest), s_manifest=Path(s_manifest)
    )
    case = build_real_q0_case(
        case_id, inputs, bundle["a_window_records"], bundle["b_sync_records"]
    )
    return {
        "schema_version": "exposedpath-q0-observed/0.2.0",
        "source_kind": "REAL_CONTROLLED_TRACE",
        "data_role": "Engineering",
        "research_eligibility": {
            "formal_evidence": False,
            "q0_status": "NOT_RUN",
            "scope": "Q0_REAL_CANDIDATE_ONLY",
        },
        "cases": [case],
    }


def run_real_q0_case(
    case_id: str,
    canonical_manifest: Path,
    s_manifest: Path,
    ab_manifest: Path,
    collection_receipt: Path,
    output_dir: Path,
) -> Path:
    """不可覆盖地写出单 case observed、comparison 与可聚合 evidence manifest。"""

    from .q0_evaluator import evaluate_q0_observed

    output = Path(output_dir).resolve()
    if output.exists():
        raise FileExistsError(f"拒绝覆盖真实 Q0 输出: {output}")
    paths = {
        "canonical_manifest": Path(canonical_manifest).resolve(),
        "s_manifest": Path(s_manifest).resolve(),
        "ab_manifest": Path(ab_manifest).resolve(),
        "collection_receipt": Path(collection_receipt).resolve(),
    }
    observed = build_real_q0_observed(case_id, **paths)
    oracle = load_oracle_bundle()
    oracle["cases"] = [case for case in oracle["cases"] if case["case_id"] == case_id]
    if len(oracle["cases"]) != 1:
        raise Q0RealObservedError(f"oracle case 不唯一或不存在: {case_id}")
    report = evaluate_q0_observed(oracle, observed)
    receipt = json.loads(paths["collection_receipt"].read_text(encoding="utf-8"))
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}.tmp-", dir=output.parent))
    try:
        observed_path = staging / "real_observed.json"
        observed_path.write_text(json.dumps(observed, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        report["observed_file"] = observed_path.name
        report["observed_sha256"] = _sha256(observed_path)
        report_path = staging / "q0_real_report.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        evidence = {
            "schema_version": "exposedpath-q0-real-evidence/0.2.0",
            "case_id": case_id,
            "run_id": receipt["run_id"],
            "data_role": "Engineering",
            "q0_status": "NOT_RUN",
            "verdict": report["verdict"],
            "environment": receipt["environment"],
            "inputs": {name: {"path": str(path), "sha256": _sha256(path)} for name, path in paths.items()},
            "observed": {"name": observed_path.name, "sha256": _sha256(observed_path)},
            "report": {"name": report_path.name, "sha256": _sha256(report_path)},
            "research_eligibility": {"formal_evidence": False, "scope": "Q0_REAL_CASE_ONLY"},
        }
        evidence_path = staging / "q0_real_evidence.json"
        evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        staging.replace(output)
        return output / evidence_path.name
    except Exception:
        import shutil
        shutil.rmtree(staging, ignore_errors=True)
        raise
