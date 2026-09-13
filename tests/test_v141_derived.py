"""Gate 5 Task 7: A/B-only derived exposure integration tests."""

from __future__ import annotations

from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path

import pytest

from exposedpath_v141.ab_bundle import analyze_ab, load_ab_bundle
from exposedpath_v141.derived import DerivedBundleError, derive_exposure, load_derived_bundle
from exposedpath_v141.cli import main
from scripts.verify_canonical_raw_boundary import check_derived_source
from tests.test_v141_ab_bundle import _make_inputs


_TIMING_FIELDS = (
    "wait_set_hidden_union_ns",
    "wait_set_exposed_union_ns",
    "terminal_pre_sync_ns",
    "terminal_overlap_sync_ns",
    "sync_return_tail_ns",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _write_b_records(ab_manifest: Path, records: list[dict[str, object]]) -> None:
    """Replace B records as an integrity-capable upstream A/B bundle producer."""

    manifest = json.loads(ab_manifest.read_text(encoding="utf-8"))
    record_path = ab_manifest.parent / "b_sync_records.jsonl.gz"
    with record_path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            for record in records:
                compressed.write(
                    (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
                )
    manifest["files"]["b_sync_records"].update(
        record_count=len(records), sha256=_sha256(record_path), size_bytes=record_path.stat().st_size
    )
    counts = {status: sum(row["validity"] == status for row in records) for status in (
        "B_VALID", "B_NOT_APPLICABLE", "B_AMBIGUOUS", "B_INVALID",
    )}
    manifest["summary"].update(
        physical_sync_count=len(records),
        b_valid_count=counts["B_VALID"],
        b_not_applicable_count=counts["B_NOT_APPLICABLE"],
        b_ambiguous_count=counts["B_AMBIGUOUS"],
        b_invalid_count=counts["B_INVALID"],
    )
    ab_manifest.write_text(json.dumps(manifest), encoding="utf-8")


def _write_a_records(ab_manifest: Path, records: list[dict[str, object]]) -> None:
    manifest = json.loads(ab_manifest.read_text(encoding="utf-8"))
    record_path = ab_manifest.parent / "a_window_records.jsonl.gz"
    with record_path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            for record in records:
                compressed.write(
                    (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
                )
    manifest["files"]["a_window_records"].update(
        record_count=len(records), sha256=_sha256(record_path), size_bytes=record_path.stat().st_size
    )
    manifest["summary"]["window_count"] = len(records)
    ab_manifest.write_text(json.dumps(manifest), encoding="utf-8")


def _b_record(base: dict[str, object], sync_id: str, *, validity: str, values: tuple[int, int, int, int, int] | None = None, completion_boundary: bool = False) -> dict[str, object]:
    record = deepcopy(base)
    record["sync_id"] = sync_id
    record["sync_kind"] = "STREAM"
    record["sync_origin"] = "natural_token_ready"
    record["callsite_id"] = "token-ready"
    record["validity"] = validity
    record["secondary_reasons"] = []
    if validity == "B_VALID":
        record["primary_reason"] = None
        if completion_boundary:
            record["terminal"] = {
                "status": "VALID", "kind": "COMPLETION_BOUNDARY", "activity_id": None,
                "end_ns": 75, "clock_domain_id": "NSYS_TRACE_RELATIVE_NS",
            }
            record["terminal_pre_sync_ns"] = None
            record["terminal_overlap_sync_ns"] = None
            assert values is not None
            for field, value in zip(("wait_set_hidden_union_ns", "wait_set_exposed_union_ns", "sync_return_tail_ns"), (values[0], values[1], values[4]), strict=True):
                record[field] = value
        else:
            assert values is not None
            for field, value in zip(_TIMING_FIELDS, values, strict=True):
                record[field] = value
        return record
    for field in _TIMING_FIELDS:
        record[field] = None
    expected_status = {
        "B_NOT_APPLICABLE": "NOT_APPLICABLE",
        "B_AMBIGUOUS": "AMBIGUOUS",
        "B_INVALID": "INVALID",
    }[validity]
    record["terminal"] = {
        "status": expected_status, "kind": "NONE", "activity_id": None,
        "end_ns": None, "clock_domain_id": None,
    }
    record["primary_reason"] = None if validity == "B_NOT_APPLICABLE" else "UPSTREAM_FAIL_CLOSED"
    return record


def _make_ab(tmp_path: Path) -> Path:
    canonical, s_manifest = _make_inputs(tmp_path)
    return analyze_ab(canonical, s_manifest, tmp_path / "ab")


def test_derive_exposure_computes_hand_checked_d_and_zero_denominator(tmp_path):
    """Would fail if D read anything other than the three frozen A top-level fields."""

    ab_manifest = _make_ab(tmp_path)
    derived_manifest = derive_exposure(ab_manifest, tmp_path / "derived")
    d_records = {record["phase"]: record for record in load_derived_bundle(derived_manifest)["d_window_records"]}

    assert d_records["full_request"] == {
        "window_id": "nvtx:NVTX_EVENTS:1:full_request", "experiment_id": "exp-1",
        "wmpc_id": "wmpc-1", "run_id": "run-1", "run_role": "Engineering",
        "pass_id": "Pass1", "request_id": "request-1", "repeat_id": "repeat-1",
        "phase": "full_request", "D_margin_ns": -85, "D_score": -85 / 95,
    }
    assert d_records["decode"]["D_margin_ns"] == -25
    assert d_records["decode"]["D_score"] == -25 / 35

    # Rewrite the valid Prefill window as a zero-length, conserved A vector.
    ab_records = [dict(record) for record in load_ab_bundle(ab_manifest)["a_window_records"]]
    zero = next(record for record in ab_records if record["phase"] == "prefill")
    zero["window_end_ns"] = zero["window_start_ns"]
    zero["T_window_ns"] = 0
    for field in (
        "A_host_path_ns", "A_cuda_api_ns", "A_device_wait_ns", "A_sync_residual_ns",
        "A_unattributed_ns", "A_cuda_api_submit_ns", "A_cuda_api_non_submit_ns",
        "A_device_wait_kernel_only_ns", "A_device_wait_memop_only_ns",
        "A_device_wait_kernel_memop_mixed_ns",
    ):
        zero[field] = 0
    _write_a_records(ab_manifest, ab_records)
    zero_d = {record["phase"]: record for record in load_derived_bundle(derive_exposure(ab_manifest, tmp_path / "zero"))["d_window_records"]}["prefill"]
    assert zero_d["D_margin_ns"] == 0
    assert zero_d["D_score"] is None


def test_signature_groups_only_valid_b_timings_and_preserves_nonadditive_distributions(tmp_path):
    """Would fail if null B states entered statistics, p90 rounded down, or B became a total."""

    ab_manifest = _make_ab(tmp_path)
    base = json.loads(gzip.open(ab_manifest.parent / "b_sync_records.jsonl.gz", "rt", encoding="utf-8").readline())
    records = [
        _b_record(base, "sync:1", validity="B_VALID", values=(10, 2, 4, 1, 5)),
        _b_record(base, "sync:2", validity="B_VALID", values=(20, 3, 8, 2, 7)),
        _b_record(base, "sync:3", validity="B_VALID", values=(100, 9, 12, 3, 11), completion_boundary=True),
        _b_record(base, "sync:4", validity="B_NOT_APPLICABLE"),
        _b_record(base, "sync:5", validity="B_AMBIGUOUS"),
        _b_record(base, "sync:6", validity="B_INVALID"),
    ]
    _write_b_records(ab_manifest, records)

    signature = next(record for record in load_derived_bundle(derive_exposure(ab_manifest, tmp_path / "derived"))["exposure_signature_records"] if record["phase"] == "decode")
    assert len(signature["b_groups"]) == 1
    group = signature["b_groups"][0]
    assert {key for key in group if "total" in key.lower() or "sum" in key.lower()} == set()
    assert group["status_counts"] == {
        "B_VALID": 3, "B_NOT_APPLICABLE": 1, "B_AMBIGUOUS": 1, "B_INVALID": 1,
    }
    assert group["valid_timing_statistics_ns"]["wait_set_hidden_union_ns"] == {"median": 20, "p90": 100}
    assert group["valid_timing_statistics_ns"]["sync_return_tail_ns"] == {"median": 7, "p90": 11}
    assert group["valid_timing_statistics_ns"]["terminal_pre_sync_ns"] == {"median": 6, "p90": 8}
    assert group["valid_timing_distributions_ns"]["terminal_pre_sync_ns"] == [
        {"value_ns": 4, "count": 1}, {"value_ns": 8, "count": 1},
    ]
    assert group["terminal_kind_counts"] == {"ACTIVITY": 2, "COMPLETION_BOUNDARY": 1}


def test_derived_bundle_is_deterministic_rejects_invalid_ab_and_cleans_failed_output(tmp_path):
    """Would fail if a derivation accepted a bad upstream bundle or exposed partial output."""

    ab_manifest = _make_ab(tmp_path)
    first = derive_exposure(ab_manifest, tmp_path / "first")
    second = derive_exposure(ab_manifest, tmp_path / "second")
    first_bundle = load_derived_bundle(first)
    second_bundle = load_derived_bundle(second)
    assert first_bundle["manifest"]["files"] == second_bundle["manifest"]["files"]
    with pytest.raises(FileExistsError, match="拒绝覆盖"):
        derive_exposure(ab_manifest, first.parent)

    bad_manifest = json.loads(ab_manifest.read_text(encoding="utf-8"))
    bad_manifest["schema_version"] = "exposedpath-ab/999"
    ab_manifest.write_text(json.dumps(bad_manifest), encoding="utf-8")
    output_dir = tmp_path / "bad"
    with pytest.raises(DerivedBundleError, match="A/B"):
        derive_exposure(ab_manifest, output_dir)
    assert not output_dir.exists()


def test_derived_loader_rechecks_optional_ab_lineage(tmp_path):
    """Would fail if a valid-looking derived manifest could be attached to another A/B input."""

    ab_manifest = _make_ab(tmp_path)
    derived_manifest = derive_exposure(ab_manifest, tmp_path / "derived")
    assert load_derived_bundle(derived_manifest, ab_manifest=ab_manifest)["manifest"]["source"]["ab_manifest_name"] == "ab_manifest.json"

    other_root = tmp_path / "other"
    other_root.mkdir()
    other_ab_manifest = _make_ab(other_root)
    with pytest.raises(DerivedBundleError, match="lineage"):
        load_derived_bundle(derived_manifest, ab_manifest=other_ab_manifest)


def test_derived_loader_rejects_hash_matched_summary_count_inconsistency(tmp_path):
    """Would fail if terminal/distribution evidence could disagree with B_VALID after hashing."""

    ab_manifest = _make_ab(tmp_path)
    derived_manifest = derive_exposure(ab_manifest, tmp_path / "derived")
    manifest = json.loads(derived_manifest.read_text(encoding="utf-8"))
    path = derived_manifest.parent / "exposure_signature_records.jsonl.gz"
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        records = [json.loads(line) for line in handle]
    decode = next(record for record in records if record["phase"] == "decode")
    decode["b_groups"][0]["valid_timing_distributions_ns"]["wait_set_hidden_union_ns"][0]["count"] = 2
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            for record in records:
                compressed.write((json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8"))
    manifest["files"]["exposure_signature_records"].update(sha256=_sha256(path), size_bytes=path.stat().st_size)
    derived_manifest.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(DerivedBundleError, match="distribution"):
        load_derived_bundle(derived_manifest)


def test_derive_exposure_cli_and_ast_boundary(tmp_path, capsys):
    """Would fail if the public command bypassed the A/B loader or reintroduced Raw/S access."""

    ab_manifest = _make_ab(tmp_path)
    assert main(["derive-exposure", "--ab-manifest", str(ab_manifest), "--output-dir", str(tmp_path / "derived")]) == 0
    assert "q0_status: NOT_RUN" in capsys.readouterr().out
    assert check_derived_source("from .canonical_raw import load\n")
    assert check_derived_source("from .s_bundle import load\n")
    assert check_derived_source("value = record['sync_start_ns']\n")
    assert check_derived_source("import sqlite3\n")
    assert check_derived_source("value = 'CUPTI_ACTIVITY_KIND_KERNEL'\n")
    assert check_derived_source((Path(__file__).parents[1] / "exposedpath_v141" / "derived.py").read_text(encoding="utf-8")) == []


@pytest.mark.parametrize(
    "source",
    [
        "from exposedpath_v141.canonical_raw import load as upstream\n",
        "from exposedpath_v141 import s_bundle as upstream\n",
        "from .sync_semantics import classify as upstream\n",
        "value = record.sync_start_ns\n",
    ],
)
def test_derived_ast_boundary_rejects_absolute_package_member_relative_and_attribute_bypasses(source):
    """Would fail if an equivalent spelling bypassed the A/B-only import or field boundary."""

    assert check_derived_source(source)


def test_derived_ast_boundary_keeps_exact_allowed_imports_and_attributes():
    """Would fail if the hardening rejected the validated interface or unrelated attributes."""

    assert check_derived_source("from exposedpath_v141 import ab_bundle as interface\n") == []
    assert check_derived_source("value = record.sync_kind\n") == []
