"""CPU-only acceptance checks for the Gate7 smoke launcher helper."""

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from exposedpath.cross_pass_validator import PARITY_STATUS_GROUPS
from scripts.gate7_smoke_validation import validate_evidence, validate_sqlite


def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")


@pytest.fixture
def evidence(tmp_path):
    manifest = {
        "data_role": "Engineering", "gpu_index": 3,
        "gpu_index_physical": 3, "gpu_index_logical": 0,
        "gpu_uuid": "GPU-test", "gpu_pci_bus_id": "00000000:E1:00.0",
        "warmup_count": 1, "repeat_count": 1,
    }
    preflight = {
        "physical_gpu_index": 3, "logical_gpu_index": 0,
        "gpu_uuid": "GPU-test", "gpu_pci_bus_id": "00000000:E1:00.0",
    }
    _write_json(tmp_path / "wmpc_manifest.json", manifest)
    _write_json(tmp_path / "preflight_gpu_identity.json", preflight)
    parity = {key: "same" for _, fields in PARITY_STATUS_GROUPS for key in fields}
    parity.update(data_role="Engineering", requested_physical_gpu_index=3,
                  gpu_uuid="GPU-test", gpu_pci_bus_id="00000000:E1:00.0")
    record = {
        "repeat_index": 0, "retry_index": 0, "attempt_uid": "attempt-0",
        "attempt_plan_version": "v1", "data_role": "Engineering",
        "phase_boundary_policy_version": "v1", "attempt_status": "success",
    }
    for pass_name in ("pass0", "pass1"):
        folder = tmp_path / pass_name
        _write_json(folder / "cross_pass_parity.json", parity)
        _write_jsonl(folder / "inference_results.jsonl", [record])
        _write_jsonl(folder / "telemetry" / f"{pass_name}_gpu_telemetry.jsonl", [{
            "requested_physical_gpu_index": 3, "requested_gpu_uuid": "GPU-test",
            "requested_pci_bus_id": "00000000:E1:00.0",
            "observed_gpu_index": "3", "observed_gpu_uuid": "GPU-test",
            "observed_pci_bus_id": "00000000:E1:00.0",
            "identity_match": True, "query_exit_code": 0,
        }])
    return tmp_path


def _validate(root):
    return validate_evidence(
        root / "wmpc_manifest.json", root / "preflight_gpu_identity.json",
        root / "pass0", root / "pass1",
    )


def test_matching_evidence_passes(evidence):
    assert _validate(evidence) == []


def test_missing_or_mismatched_parity_fails_closed(evidence):
    (evidence / "pass1" / "cross_pass_parity.json").unlink()
    assert _validate(evidence)
    _write_json(evidence / "pass1" / "cross_pass_parity.json", {})
    assert _validate(evidence)


@pytest.mark.parametrize("group", range(6))
def test_each_frozen_parity_group_fails_closed(evidence, group):
    key = PARITY_STATUS_GROUPS[group][1][0]
    path = evidence / "pass1" / "cross_pass_parity.json"
    data = json.loads(path.read_text())
    data[key] = "different"
    _write_json(path, data)
    assert _validate(evidence)


def test_attempt_accounting_mismatch_fails_closed(evidence):
    (evidence / "pass1" / "inference_results.jsonl").write_text("", encoding="utf-8")
    assert _validate(evidence)


def test_validation_cli_blocks_missing_evidence(evidence):
    helper = Path(__file__).resolve().parents[1] / "scripts" / "gate7_smoke_validation.py"
    (evidence / "pass1" / "cross_pass_parity.json").unlink()
    completed = subprocess.run(
        [sys.executable, str(helper), "evidence", "--manifest", str(evidence / "wmpc_manifest.json"),
         "--preflight", str(evidence / "preflight_gpu_identity.json"),
         "--pass0", str(evidence / "pass0"), "--pass1", str(evidence / "pass1")],
        cwd=str(helper.parents[1]), capture_output=True, text=True,
    )
    assert completed.returncode != 0
    assert json.loads(completed.stdout)["status"] == "BLOCKED"


@pytest.mark.parametrize("field,value", [
    ("observed_gpu_index", "2"), ("observed_gpu_uuid", "GPU-other"),
    ("observed_pci_bus_id", "00000000:00:00.0"), ("identity_match", False),
])
def test_telemetry_mismatch_fails_closed(evidence, field, value):
    path = evidence / "pass1" / "telemetry" / "pass1_gpu_telemetry.jsonl"
    record = json.loads(path.read_text())
    record[field] = value
    _write_jsonl(path, [record])
    assert _validate(evidence)


def test_logical_mapping_or_pilot_role_fails_closed(evidence):
    path = evidence / "preflight_gpu_identity.json"
    data = json.loads(path.read_text())
    data["logical_gpu_index"] = 1
    _write_json(path, data)
    assert _validate(evidence)
    data["logical_gpu_index"] = 0
    _write_json(path, data)
    path = evidence / "wmpc_manifest.json"
    manifest = json.loads(path.read_text())
    manifest["data_role"] = "Pilot"
    _write_json(path, manifest)
    assert _validate(evidence)


def test_sqlite_missing_empty_and_bad_schema_fail_closed(tmp_path):
    path = tmp_path / "trace.sqlite"
    assert validate_sqlite(path)
    path.touch()
    assert validate_sqlite(path)
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE TRACE_EVENTS (id INTEGER)")
    assert validate_sqlite(path) == []
