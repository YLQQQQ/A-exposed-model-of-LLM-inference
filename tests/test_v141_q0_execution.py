"""Gate 6 GPU 前 Q0 执行合同、dry-run 与资格边界测试。"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from exposedpath_v141.q0_execution import (
    Q0ExecutionError,
    load_q0_execution_manifest,
    prepare_q0_run,
    validate_q0_execution_manifest,
)
from exposedpath_v141.cli import main
from exposedpath_v141.q0_oracle import load_oracle_bundle


def test_committed_execution_manifest_covers_oracle_exactly_once():
    oracle = load_oracle_bundle()
    manifest = load_q0_execution_manifest()

    assert {case["case_id"] for case in manifest["cases"]} == {
        case["case_id"] for case in oracle["cases"]
    }
    assert len(manifest["cases"]) == 23
    assert manifest["research_eligibility"] == {
        "formal_evidence": False,
        "q0_status": "NOT_RUN",
        "scope": "Q0_PRE_GPU_ONLY",
    }


@pytest.mark.parametrize("mutation", ["missing", "extra", "duplicate"])
def test_case_coverage_mismatch_fails_closed(mutation):
    oracle = load_oracle_bundle()
    manifest = load_q0_execution_manifest()
    if mutation == "missing":
        manifest["cases"].pop()
    elif mutation == "extra":
        extra = deepcopy(manifest["cases"][0])
        extra["case_id"] = "Q0-UNKNOWN-001"
        manifest["cases"].append(extra)
    else:
        manifest["cases"].append(deepcopy(manifest["cases"][0]))

    with pytest.raises(Q0ExecutionError, match="case"):
        validate_q0_execution_manifest(manifest, oracle)


def test_execution_manifest_cannot_claim_q0_or_formal_eligibility():
    oracle = load_oracle_bundle()
    manifest = load_q0_execution_manifest()
    manifest["research_eligibility"]["q0_status"] = "PASS"
    manifest["research_eligibility"]["formal_evidence"] = True

    with pytest.raises(Q0ExecutionError, match="资格"):
        validate_q0_execution_manifest(manifest, oracle)


def test_stable_labels_must_equal_oracle_construction():
    oracle = load_oracle_bundle()
    manifest = load_q0_execution_manifest()
    target = next(case for case in manifest["cases"] if case["activity_labels"])
    target["activity_labels"].append("UNKNOWN_ACTIVITY")

    with pytest.raises(Q0ExecutionError, match="activity_labels"):
        validate_q0_execution_manifest(manifest, oracle)


@pytest.mark.parametrize(
    ("strategy", "seed", "fault"),
    [
        ("NATIVE_CUDA", None, None),
        ("NATIVE_WITH_CANONICAL_FAULT", "Q0-MISSING-CORR-001", None),
        ("SYNTHETIC_CANONICAL", "Q0-TERMINAL-TIE-001", None),
    ],
)
def test_strategy_specific_fields_are_not_silently_guessed(strategy, seed, fault):
    oracle = load_oracle_bundle()
    manifest = load_q0_execution_manifest()
    target = manifest["cases"][0]
    target.update(
        execution_strategy=strategy,
        native_seed_case_id=seed,
        fault_injection=fault,
    )

    with pytest.raises(Q0ExecutionError, match="策略"):
        validate_q0_execution_manifest(manifest, oracle)


def test_each_case_has_explicit_synthetic_profile():
    oracle = load_oracle_bundle()
    manifest = load_q0_execution_manifest()
    manifest["cases"][0]["synthetic_profile"] = None

    with pytest.raises(Q0ExecutionError, match="synthetic_profile"):
        validate_q0_execution_manifest(manifest, oracle)


def _fake_tools(tmp_path: Path) -> tuple[Path, Path]:
    tool_dir = tmp_path / "tools with spaces"
    tool_dir.mkdir()
    binary = tool_dir / "exposedpath q0.exe"
    nsys = tool_dir / "nsys.exe"
    binary.write_bytes(b"q0-binary")
    nsys.write_bytes(b"nsys-binary")
    return binary, nsys


@pytest.mark.parametrize("platform", ["windows", "linux"])
def test_prepare_q0_run_writes_complete_nonexecuted_plan_with_structured_argv(
    tmp_path, platform
):
    binary, nsys = _fake_tools(tmp_path)
    output_dir = tmp_path / f"prepared {platform}"

    manifest_path = prepare_q0_run(
        output_dir, binary, nsys, platform=platform, run_id="q0-dry-run-001",
        cuda_visible_device="GPU-TEST-0001",
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["status"] == "PREPARED_NOT_EXECUTED"
    assert manifest["research_eligibility"]["q0_status"] == "NOT_RUN"
    assert manifest["research_eligibility"]["formal_evidence"] is False
    assert len(manifest["cases"]) == 23
    native = [case for case in manifest["cases"] if case["command_argv"] is not None]
    assert len(native) == 21
    for case in native:
        argv = case["command_argv"]
        assert argv[0] == str(nsys.resolve())
        assert str(binary.resolve()) in argv
        assert all('"' not in argument for argument in argv)
        assert "--capture-range=cudaProfilerApi" in argv
        assert "--capture-range-end=stop" in argv
        assert not any(argument.startswith("--nvtx-capture") for argument in argv)
        assert "--trace=cuda,nvtx" in argv
        assert not any("wddm" in argument.lower() for argument in argv)
        assert "--diagnostic-h2d-bytes" not in argv
        assert "--diagnostic-kernel-ms" not in argv
    assert not list(output_dir.rglob("*.nsys-rep"))
    for case in manifest["cases"]:
        source_manifest = output_dir / case["source_manifest"]
        assert source_manifest.is_file()
        assert hashlib.sha256(source_manifest.read_bytes()).hexdigest().upper() == case[
            "source_manifest_sha256"
        ]
        source_identity = json.loads(source_manifest.read_text(encoding="utf-8"))
        assert source_identity["q0_case_id"] == case["case_id"]
        assert source_identity["q0_status"] == "NOT_RUN"
        assert source_identity["cuda_visible_device"] == "GPU-TEST-0001"
        assert source_identity["selected_device_id"] == 0
    assert manifest["gpu_selection"] == {
        "cuda_visible_device": "GPU-TEST-0001",
        "logical_device_id": 0,
    }


@pytest.mark.parametrize("platform", ["windows", "linux"])
def test_prepare_q0_run_enables_node_graph_trace_only_for_graph_fault_seed(
    tmp_path, platform
):
    binary, nsys = _fake_tools(tmp_path)
    manifest_path = prepare_q0_run(
        tmp_path / f"graph trace {platform}",
        binary,
        nsys,
        platform=platform,
        run_id="q0-graph-trace-001",
        cuda_visible_device="GPU-TEST-0001",
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    native_cases = {
        case["case_id"]: case["command_argv"]
        for case in manifest["cases"]
        if case["command_argv"] is not None
    }

    assert native_cases["Q0-GRAPH-UNSUPPORTED-001"].count(
        "--cuda-graph-trace=node"
    ) == 1
    for case_id, argv in native_cases.items():
        if case_id != "Q0-GRAPH-UNSUPPORTED-001":
            assert "--cuda-graph-trace=node" not in argv, case_id


def test_prepare_q0_run_rejects_missing_tools_and_existing_output(tmp_path):
    binary, nsys = _fake_tools(tmp_path)
    output_dir = tmp_path / "prepared"
    prepare_q0_run(
        output_dir, binary, nsys, platform="windows", run_id="run-1",
        cuda_visible_device="0",
    )

    with pytest.raises(Q0ExecutionError, match="拒绝覆盖"):
        prepare_q0_run(
            output_dir, binary, nsys, platform="windows", run_id="run-2",
            cuda_visible_device="0",
        )
    with pytest.raises(Q0ExecutionError, match="binary"):
        prepare_q0_run(
            tmp_path / "missing-binary", tmp_path / "none.exe", nsys,
            platform="windows", run_id="run-3", cuda_visible_device="0"
        )
    with pytest.raises(Q0ExecutionError, match="nsys"):
        prepare_q0_run(
            tmp_path / "missing-nsys", binary, tmp_path / "none-nsys.exe",
            platform="windows", run_id="run-4", cuda_visible_device="0"
        )

    with pytest.raises(Q0ExecutionError, match="CUDA_VISIBLE_DEVICES"):
        prepare_q0_run(
            tmp_path / "multiple-gpus", binary, nsys,
            platform="windows", run_id="run-5", cuda_visible_device="0,1"
        )


def test_prepare_q0_cli_is_explicitly_dry_run(tmp_path, capsys):
    binary, nsys = _fake_tools(tmp_path)
    output_dir = tmp_path / "cli-plan"

    status = main([
        "prepare-q0-run", "--output-dir", str(output_dir),
        "--binary", str(binary), "--nsys", str(nsys),
        "--platform", "windows", "--run-id", "cli-run-1",
        "--cuda-visible-device", "GPU-TEST-0001",
    ])

    output = capsys.readouterr().out
    assert status == 0
    assert "run_status: PREPARED_NOT_EXECUTED" in output
    assert "q0_execution_status: NOT_RUN" in output
    assert "verdict: DRY_RUN_ONLY" in output
