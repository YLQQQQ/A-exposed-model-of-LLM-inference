"""Producer -> SQLite adapter -> Canonical; all inputs are synthetic, no GPU."""
from copy import deepcopy
import hashlib
import json
import sqlite3

import pytest

from exposedpath import nvtx
from exposedpath_v141 import canonical_raw
from test_v141_canonical_raw import _make_source_sqlite


UUID = "12345678-1234-1234-1234-123456789abc"


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def producer_pass(**overrides):
    factory = getattr(nvtx, "make_gate8_pass_identity", None)
    assert callable(factory), "Gate8 needs a real multi-request producer, not scalar repeat inference"
    return factory(
        experiment_id="exp", wmpc_id="wmpc", run_id="run", pass_id="pass1",
        attempt_id="attempt-1", pid=3, wmpc_manifest_sha256="a" * 64,
        prompt_sha256="b" * 64, runner_source_sha256="c" * 64,
        runner_git_commit="d" * 40, runner_git_dirty=False,
        **overrides, requests=[{
            "request_id": f"request-{i}", "repeat_id": str(i),
            "request_role": "measured", "expected_output_tokens": 2,
            "actual_output_tokens": 2, "expected_boundary_ids": [f"r{i}", f"t{i}-0", f"t{i}-1"],
            "observed_boundary_ids": [f"r{i}", f"t{i}-0", f"t{i}-1"],
            "outcome": "COMPLETE", "early_eos": False, "reasons": [],
        } for i in range(2)],
    )


@pytest.mark.parametrize("field,value", [("run_role", "FORMAL"), ("data_role", "Formal")])
def test_producer_rejects_conflicting_role_instead_of_relabeling(field, value):
    with pytest.raises(ValueError, match="IDENTITY_CONFLICT"):
        producer_pass(**{field: value})


def test_adapter_rejects_explicit_conflicting_nvtx_data_role(tmp_path):
    inputs = sources(tmp_path)
    with sqlite3.connect(inputs[0]) as conn:
        for rowid, label in conn.execute("SELECT rowid,text FROM NVTX_EVENTS").fetchall():
            prefix, payload = label.split(":", 1)
            identity = json.loads(payload)
            identity["data_role"] = "Formal"
            conn.execute("UPDATE NVTX_EVENTS SET text=? WHERE rowid=?",
                         (prefix + ":" + json.dumps(identity), rowid))
    with pytest.raises(ValueError, match="IDENTITY_CONFLICT"):
        convert(tmp_path, inputs)


def sources(tmp_path):
    db = tmp_path / "trace.sqlite"
    tid = _make_source_sqlite(db)
    with sqlite3.connect(db) as conn:
        conn.executescript("""
        ALTER TABLE TARGET_INFO_GPU ADD COLUMN uuid TEXT;
        ALTER TABLE TARGET_INFO_GPU ADD COLUMN busLocation TEXT;
        DELETE FROM TARGET_INFO_GPU;
        CREATE TABLE TARGET_INFO_CUDA_DEVICE(pid INTEGER, cudaId INTEGER, uuid TEXT, gpuId INTEGER);
        """)
        conn.execute("INSERT INTO TARGET_INFO_GPU VALUES (2,'synthetic',?, '00000000:E1:00.0')", (UUID,))
        conn.execute("INSERT INTO TARGET_INFO_CUDA_DEVICE VALUES (3,0,?,2)", (UUID,))
        conn.execute("DELETE FROM NVTX_EVENTS")
        for i in range(2):
            label = nvtx.make_structured_nvtx_label({
                "experiment_id": "exp", "wmpc_id": "wmpc", "run_id": "run",
                "run_role": "ENGINEERING", "pass_id": "pass1", "attempt_id": "attempt-1",
                "request_id": f"request-{i}", "repeat_id": str(i),
                "kind": "sync", "phase": "prefill", "callsite_id": "token_ready",
                "sync_origin": "natural_token_ready", "sync_ordinal": 0,
                "token_index": 0, "token_ready_mechanism": "device_to_host_token_ids",
            })
            conn.execute("INSERT INTO NVTX_EVENTS(start,end,eventType,text,globalTid) VALUES (?,?,59,?,?)",
                         (10 + i * 100, 90 + i * 100, label, tid))
    pre = write_json(tmp_path / "preflight.json", {
        "gpu_index_physical": 3, "gpu_uuid": "GPU-" + UUID,
        "pci_bus_id": "00000000:E1:00.0", "cuda_device_order": "PCI_BUS_ID",
        "cuda_visible_devices": "3",
    })
    probe = write_json(tmp_path / "probe.json", {
        "pid": 3, "gpu_index_logical": 0, "gpu_uuid": UUID,
        "pci_bus_id": "0000:e1:00.0", "cuda_device_order": "PCI_BUS_ID",
        "cuda_visible_devices": "3",
    })
    ledger = write_json(tmp_path / "pass.json", producer_pass())
    return db, pre, probe, ledger


def convert(tmp_path, inputs):
    db, pre, probe, ledger = inputs
    return canonical_raw.convert_sqlite_to_canonical(
        db, tmp_path / "canonical", "Engineering", raw_sha256="e" * 64,
        collector_version="2026.1.1.204",
        gate8_sources={"pass_identity": ledger, "preflight": pre, "cuda_probe": probe},
    )


def test_multi_repeat_producer_to_canonical_and_three_device_namespaces(tmp_path):
    inputs = sources(tmp_path)
    manifest = json.loads(convert(tmp_path, inputs).read_text())
    assert manifest["observation_profile"] == "G8-OBS-BOUNDARY/0.1.0"
    assert manifest["identity"]["status"] == "VALID"
    assert "repeat_id" not in manifest["identity"]["values"]
    assert [x["identity"]["repeat_id"] for x in manifest["identity"]["requests"]] == ["0", "1"]
    assert manifest["execution_context"]["selected_device_id"] == 0
    mapping = json.loads((tmp_path / "canonical" / "gate8_device_mapping.json").read_text())
    assert (mapping["gpu_index_physical"], mapping["gpu_index_logical"],
            mapping["nsys_inventory_gpu_id"], mapping["trace_device_id"]) == (3, 0, 2, 0)
    assert mapping["pci_bus_id"] == "0000:e1:00.0"
    assert mapping["source_sqlite_sha256"] == sha(inputs[0])
    assert mapping["preflight_ref"]["sha256"] == sha(inputs[1])
    final = json.loads((tmp_path / "canonical" / "gate8_pass_identity.json").read_text())
    assert final["device_mapping_sha256"] == sha(tmp_path / "canonical" / "gate8_device_mapping.json")
    assert final["raw_artifact_sha256"] == "e" * 64
    assert json.loads(inputs[3].read_text())["raw_artifact_sha256"] is None


@pytest.mark.parametrize("field,value", [
    ("gpu_uuid", "87654321-1234-1234-1234-123456789abc"),
    ("pci_bus_id", "0000:e2:00.0"), ("pid", 9), ("gpu_index_logical", 3),
    ("cuda_visible_devices", "0"), ("cuda_device_order", None),
])
def test_device_conflicts_reject_before_publishing_bundle(tmp_path, field, value):
    inputs = sources(tmp_path)
    probe = json.loads(inputs[2].read_text())
    probe[field] = value
    write_json(inputs[2], probe)
    with pytest.raises(ValueError, match="DEVICE_MAPPING_UNPROVEN"):
        convert(tmp_path, inputs)
    assert not (tmp_path / "canonical").exists()


@pytest.mark.parametrize("sql", [
    "DELETE FROM TARGET_INFO_CUDA_DEVICE",
    "INSERT INTO TARGET_INFO_CUDA_DEVICE SELECT * FROM TARGET_INFO_CUDA_DEVICE",
    "UPDATE TARGET_INFO_CUDA_CONTEXT_INFO SET deviceId=2",
    "UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET deviceId=3",
    "UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET globalPid=NULL",
    "UPDATE TARGET_INFO_GPU SET busLocation='10000:e1:00.0'",
])
def test_trace_identity_missing_ambiguous_or_conflicting(tmp_path, sql):
    inputs = sources(tmp_path)
    with sqlite3.connect(inputs[0]) as conn:
        conn.execute(sql)
    with pytest.raises(ValueError, match="DEVICE_MAPPING_UNPROVEN"):
        convert(tmp_path, inputs)


def test_marker_from_another_attempt_is_not_accepted(tmp_path):
    inputs = sources(tmp_path)
    with sqlite3.connect(inputs[0]) as conn:
        conn.execute("UPDATE NVTX_EVENTS SET text=replace(text,'attempt-1','attempt-2')")
    with pytest.raises(ValueError, match="IDENTITY_CONFLICT"):
        convert(tmp_path, inputs)


def test_duplicate_request_and_incomplete_success_rejected_at_producer():
    ledger = producer_pass()
    from exposedpath.gate8_identity import validate_pass_identity
    duplicate = deepcopy(ledger)
    duplicate["requests"][1] = deepcopy(duplicate["requests"][0])
    with pytest.raises(ValueError, match="IDENTITY_CONFLICT"):
        validate_pass_identity(duplicate)
    ledger["requests"][0]["actual_output_tokens"] = 1
    with pytest.raises(ValueError, match="IDENTITY_CONFLICT"):
        validate_pass_identity(ledger)


def test_request_ledger_order_is_not_identity():
    from exposedpath.gate8_identity import validate_pass_identity
    ledger = producer_pass()
    ledger["requests"].reverse()
    validate_pass_identity(ledger)


def test_adapter_rejects_malformed_structured_marker_instead_of_ignoring_it(tmp_path):
    inputs = sources(tmp_path)
    with sqlite3.connect(inputs[0]) as conn:
        conn.execute("UPDATE NVTX_EVENTS SET text='EXPOSEDPATH_JSON_V1:{' WHERE rowid=1")
    with pytest.raises(ValueError, match="IDENTITY_CONFLICT"):
        convert(tmp_path, inputs)
