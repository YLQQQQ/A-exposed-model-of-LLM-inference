"""Q0 唯一 Gate 聚合的策略覆盖与 fail-closed 测试。"""

from __future__ import annotations

import hashlib
import json

from exposedpath_v141.q0_execution import load_q0_execution_manifest
from exposedpath_v141.q0_gate import aggregate_q0_evidence
from exposedpath_v141.q0_synthetic import run_synthetic_q0
from exposedpath_v141.cli import main


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _evidence(tmp_path, case_id, *, environment="same"):
    root = tmp_path / case_id
    root.mkdir(parents=True)
    report = {
        "verdict": "REAL_CASE_PASS", "evidence_scope": "REAL_CASE_ONLY", "q0_status": "NOT_RUN",
        "cases": [{"case_id": case_id, "status": "PASS"}],
    }
    report_path = root / "q0_real_report.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    evidence = {
        "schema_version": "exposedpath-q0-real-evidence/0.2.0",
        "case_id": case_id, "run_id": "q0-run", "verdict": "REAL_CASE_PASS",
        "environment": {"identity": environment},
        "report": {"name": report_path.name, "sha256": _sha(report_path)},
    }
    evidence_path = root / "q0_real_evidence.json"
    evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
    return evidence_path


def _all_real(tmp_path):
    specs = load_q0_execution_manifest()["cases"]
    return [
        _evidence(tmp_path, case["case_id"])
        for case in specs
        if case["execution_strategy"] != "SYNTHETIC_CANONICAL"
    ]


def test_gate_requires_real_evidence_for_every_native_or_fault_case(tmp_path):
    synthetic = run_synthetic_q0(tmp_path / "synthetic")
    real = _all_real(tmp_path / "real")

    report = aggregate_q0_evidence(real, synthetic)

    assert report["verdict"] == "PASS"
    assert report["q0_status"] == "PASS"
    assert report["summary"] == {
        "required_case_count": 23, "passed_case_count": 23, "failed_case_count": 0,
    }


def test_gate_does_not_let_full_synthetic_report_replace_native_case(tmp_path):
    synthetic = run_synthetic_q0(tmp_path / "synthetic")
    real = _all_real(tmp_path / "real")
    real.pop()

    report = aggregate_q0_evidence(real, synthetic)

    assert report["verdict"] == "FAIL"
    assert report["summary"]["failed_case_count"] == 1


def test_gate_rejects_mixed_real_environments(tmp_path):
    synthetic = run_synthetic_q0(tmp_path / "synthetic")
    real = _all_real(tmp_path / "real")
    item = json.loads(real[0].read_text(encoding="utf-8"))
    item["environment"] = {"identity": "different"}
    real[0].write_text(json.dumps(item), encoding="utf-8")

    report = aggregate_q0_evidence(real, synthetic)

    assert report["verdict"] == "FAIL"
    assert any("不同" in mismatch for mismatch in report["global_mismatches"])


def test_gate_cli_writes_unique_pass_report(tmp_path):
    synthetic = run_synthetic_q0(tmp_path / "synthetic")
    real_root = tmp_path / "real"
    _all_real(real_root)
    output = tmp_path / "gate"

    code = main([
        "aggregate-q0-gate", "--real-evidence-dir", str(real_root),
        "--synthetic-report", str(synthetic), "--output-dir", str(output),
    ])

    assert code == 0
    report = json.loads((output / "q0_gate_report.json").read_text(encoding="utf-8"))
    assert report["verdict"] == "PASS"
