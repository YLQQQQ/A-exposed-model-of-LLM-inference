"""Gate 6 合成 Canonical -> S/A/B -> 独立 oracle 对照。"""

from __future__ import annotations

import json

from exposedpath_v141.cli import main
from exposedpath_v141.q0_synthetic import run_synthetic_q0


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
