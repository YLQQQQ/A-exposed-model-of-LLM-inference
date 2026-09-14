"""Q0 Canonical 故障注入只修改派生副本。"""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pytest

from exposedpath_v141.canonical_raw import load_canonical_raw_schema
from exposedpath_v141.cli import main
from exposedpath_v141.q0_faults import Q0FaultError, apply_q0_fault
from exposedpath_v141.sync_semantics import load_canonical_bundle


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _bundle(path: Path, *, activity: dict | None = None) -> Path:
    path.mkdir()
    schema = load_canonical_raw_schema()
    files = {}
    for kind, spec in schema["record_types"].items():
        records = []
        if kind == "device_activity" and activity is not None:
            record = {field: None for field in spec["nullable_fields"]}
            record.update({
                "record_id": "device_activity:test:1", "source_table": "TEST_ACTIVITY",
                "source_rowid": 1, "clock_domain_id": "NSYS_TRACE_RELATIVE_NS",
                "activity_kind": "KERNEL", "start_ns": 10, "end_ns": 20,
                "device_id": 0, "context_id": 1, "stream_id": 2,
                "name": "q0_spin_kernel", "attributes": {},
            })
            record.update(activity)
            records.append(record)
        target = path / spec["filename"]
        payload = b"".join(
            (json.dumps(record, sort_keys=True) + "\n").encode("utf-8")
            for record in records
        )
        with target.open("xb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
                zipped.write(payload)
        files[kind] = {
            "filename": spec["filename"], "record_count": len(records),
            "sha256": _sha(target), "size_bytes": target.stat().st_size,
        }
    manifest = {
        "schema_version": schema["schema_version"],
        "measurement_contract_version": schema["measurement_contract_version"],
        "adapter_id": schema["adapter_id"], "analyzer_version": "test",
        "generated_at_utc": "2026-09-14T00:00:00+00:00", "data_role": "Engineering",
        "source": {"sqlite": {"sha256": "A" * 64}}, "clock": schema["clock_model"],
        "identity": {"status": "VALID"},
        "execution_context": {"default_stream_mode": "PER_THREAD", "selected_device_id": 0},
        "files": files, "observation_validity": {"status": "valid", "issues": []},
        "research_eligibility": {"formal_evidence": False, "q0_status": "NOT_RUN"},
    }
    manifest_path = path / "canonical_manifest.json"
    manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
    return manifest_path


@pytest.mark.parametrize(
    ("case_id", "activity", "field", "expected"),
    [
        ("Q0-MISSING-CORR-001", {"correlation_id": 77}, "correlation_id", None),
        (
            "Q0-GRAPH-UNSUPPORTED-001",
            {"correlation_id": 77, "graph_id": 5, "graph_node_id": 9},
            "graph_node_id",
            None,
        ),
    ],
)
def test_fault_mutates_exactly_one_derived_activity_and_preserves_source(
    tmp_path, case_id, activity, field, expected
):
    source = _bundle(tmp_path / "source", activity=activity)
    source_hashes = {path.name: _sha(path) for path in source.parent.iterdir()}

    result = apply_q0_fault(source, case_id, tmp_path / "derived")
    derived = load_canonical_bundle(result)

    assert derived["records"]["device_activity"][0][field] is expected
    assert derived["manifest"]["source"]["q0_fault"]["case_id"] == case_id
    assert derived["manifest"]["source"]["q0_fault"]["mutation_count"] == 1
    assert source_hashes == {path.name: _sha(path) for path in source.parent.iterdir()}


def test_dropped_fault_marks_only_derived_observation_invalid(tmp_path):
    source = _bundle(tmp_path / "source")

    result = apply_q0_fault(source, "Q0-DROPPED-001", tmp_path / "derived")
    derived = load_canonical_bundle(result)

    assert derived["manifest"]["observation_validity"]["status"] == "invalid"
    assert derived["manifest"]["observation_validity"]["issues"] == [{
        "level": "error", "code": "TRACE_DROPPED_RECORDS",
        "detail": {"injected_by": "MARK_TRACE_DROPPED"},
    }]
    assert json.loads(source.read_text(encoding="utf-8"))["observation_validity"]["status"] == "valid"


def test_fault_refuses_wrong_case_missing_target_and_existing_output(tmp_path):
    source = _bundle(tmp_path / "source")
    with pytest.raises(Q0FaultError, match="不使用 Canonical fault"):
        apply_q0_fault(source, "Q0-STREAM-001", tmp_path / "wrong")
    with pytest.raises(Q0FaultError, match="恰好命中一个"):
        apply_q0_fault(source, "Q0-MISSING-CORR-001", tmp_path / "missing")

    output = tmp_path / "existing"
    output.mkdir()
    with pytest.raises(Q0FaultError, match="拒绝覆盖"):
        apply_q0_fault(source, "Q0-DROPPED-001", output)


def test_apply_q0_fault_cli_keeps_q0_not_run(tmp_path, capsys):
    source = _bundle(tmp_path / "source")
    output = tmp_path / "derived"

    assert main([
        "apply-q0-fault", "--canonical-manifest", str(source),
        "--case", "Q0-DROPPED-001", "--output-dir", str(output),
    ]) == 0

    printed = capsys.readouterr().out
    assert "fault_status: APPLIED" in printed
    assert "q0_execution_status: NOT_RUN" in printed
