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


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "docs" / "v1_4_1" / "contracts" / "q0_execution_schema_v0_2.json"
MEASUREMENT_INITIALIZATIONS = {"NONE", "PRE_CAPTURE_SAME_KERNEL_WARMUP"}
APPLY_POLICY = "PRE_CAPTURE_SAME_KERNEL_WARMUP"
APPLY_CASE_ID = "Q0-KERNEL-MEMOP-001"


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
        assert "--diagnostic-d2h-bytes" not in argv
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


def test_manifest_declares_frozen_measurement_initialization_for_all_23_cases():
    """每条 case 都必须显式声明 policy；缺失或未知值不能被隐式猜测。"""

    manifest = load_q0_execution_manifest()

    assert manifest["schema_version"] == "exposedpath-q0-execution/0.2.1"
    cases = manifest["cases"]
    assert len(cases) == 23
    policies = {case["case_id"]: case["measurement_initialization"] for case in cases}
    assert len(policies) == 23
    assert set(policies.values()) <= MEASUREMENT_INITIALIZATIONS
    assert sorted(
        case_id for case_id, policy in policies.items() if policy == APPLY_POLICY
    ) == [APPLY_CASE_ID]
    assert sum(1 for policy in policies.values() if policy == "NONE") == 22


def test_synthetic_cases_use_explicit_none_policy_without_a_third_enum_value():
    """2 个 synthetic 的 amendment classification 是 NOT_APPLICABLE，但 runtime policy 仍为 NONE。"""

    manifest = load_q0_execution_manifest()
    synthetic = {
        case["case_id"]: case["measurement_initialization"]
        for case in manifest["cases"]
        if case["execution_strategy"] == "SYNTHETIC_CANONICAL"
    }

    assert len(synthetic) == 2
    assert set(synthetic.values()) == {"NONE"}


def test_execution_schema_freezes_measurement_initialization_enum():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    case = schema["$defs"]["case"]

    assert schema["$id"] == "https://exposedpath.local/schema/q0-execution-0.2.1.json"
    assert schema["properties"]["schema_version"]["const"] == (
        "exposedpath-q0-execution/0.2.1"
    )
    assert "measurement_initialization" in case["required"]
    assert case["properties"]["measurement_initialization"] == {
        "enum": ["NONE", "PRE_CAPTURE_SAME_KERNEL_WARMUP"]
    }


def test_missing_measurement_initialization_is_rejected():
    oracle = load_oracle_bundle()
    manifest = load_q0_execution_manifest()
    manifest["cases"][0].pop("measurement_initialization")

    with pytest.raises(Q0ExecutionError, match="measurement_initialization"):
        validate_q0_execution_manifest(manifest, oracle)


def test_unknown_measurement_initialization_is_rejected():
    oracle = load_oracle_bundle()
    manifest = load_q0_execution_manifest()
    manifest["cases"][0]["measurement_initialization"] = "PRE_CAPTURE_WARMUP"

    with pytest.raises(Q0ExecutionError, match="measurement_initialization"):
        validate_q0_execution_manifest(manifest, oracle)


def test_policy_validation_does_not_depend_on_the_committed_schema(tmp_path, monkeypatch):
    """schema 之外仍必须 fail closed：guard 不能只在 JSON schema 里存在。"""

    from exposedpath_v141 import q0_execution

    oracle = load_oracle_bundle()
    manifest = load_q0_execution_manifest()
    manifest["cases"][0]["measurement_initialization"] = "PRE_CAPTURE_WARMUP"
    monkeypatch.setattr(
        q0_execution, "_SCHEMA_PATH", tmp_path / "absent-schema.json"
    )
    relaxed = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
    }
    (tmp_path / "absent-schema.json").write_text(
        json.dumps(relaxed), encoding="utf-8"
    )

    with pytest.raises(Q0ExecutionError, match="measurement_initialization"):
        validate_q0_execution_manifest(manifest, oracle)


def test_prepare_q0_run_passes_frozen_policy_to_every_native_case(tmp_path):
    binary, nsys = _fake_tools(tmp_path)
    manifest_path = prepare_q0_run(
        tmp_path / "policy plan", binary, nsys, platform="windows",
        run_id="q0-policy-001", cuda_visible_device="GPU-TEST-0001",
    )
    run_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    frozen = {
        case["case_id"]: case["measurement_initialization"]
        for case in load_q0_execution_manifest()["cases"]
    }

    assert run_manifest["schema_version"] == "exposedpath-q0-run/0.2.1"
    native = [case for case in run_manifest["cases"] if case["command_argv"] is not None]
    assert len(native) == 21
    for case in native:
        policy = frozen[case["case_id"]]
        assert case["measurement_initialization"] == policy
        argv = case["command_argv"]
        assert argv.count("--measurement-initialization") == 1
        assert argv.index("--measurement-initialization") == len(argv) - 2
        assert argv[-2:] == ["--measurement-initialization", policy]
    assert [
        case["case_id"] for case in native
        if case["measurement_initialization"] == APPLY_POLICY
    ] == [APPLY_CASE_ID]

    synthetic = [case for case in run_manifest["cases"] if case["command_argv"] is None]
    assert len(synthetic) == 2
    for case in synthetic:
        assert case["measurement_initialization"] == "NONE"


def test_prepare_q0_run_records_the_policy_it_actually_passed(tmp_path):
    """run provenance 记录的实际 policy 必须与 argv 逐字一致，而不是只看 manifest。"""

    binary, nsys = _fake_tools(tmp_path)
    manifest_path = prepare_q0_run(
        tmp_path / "provenance", binary, nsys, platform="linux",
        run_id="q0-provenance-001", cuda_visible_device="0",
    )
    run_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    for case in run_manifest["cases"]:
        if case["command_argv"] is None:
            continue
        argv_policy = case["command_argv"][-1]
        assert case["measurement_initialization"] == argv_policy
        assert case["command_argv"][-2] == "--measurement-initialization"
