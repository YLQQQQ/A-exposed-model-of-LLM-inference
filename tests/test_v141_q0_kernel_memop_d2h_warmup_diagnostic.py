"""同 binary A'(无 warm-up)/B(warm-up) 配对 Engineering 诊断测试。"""

from __future__ import annotations

import json
import sqlite3
import subprocess
from pathlib import Path

import pytest

from exposedpath_v141.cli import main
from exposedpath_v141.q0_kernel_memop_d2h_diagnostic import (
    build_kernel_memop_d2h_diagnostic_argv as build_baseline_argv,
)
from exposedpath_v141.q0_kernel_memop_d2h_warmup_diagnostic import (
    ARM_A,
    ARM_B,
    BASELINE_REFERENCE_COMMIT,
    CASE_ID,
    DIAGNOSTIC_D2H_BYTES,
    DIAGNOSTIC_KERNEL_MS,
    WARMUP_FLAG,
    KernelMemopD2HWarmupDiagnosticError,
    build_pair_arm_argv,
    classify_pair_outcome,
    run_kernel_memop_d2h_warmup_pair_diagnostic,
    summarize_warmup_diagnostic_sqlite,
)


RUN_ID = "q0-win-4090-20260918-kernel-memop-d2h-diag-64m-10ms-warmup-01"
IMPL_COMMIT = "1" * 40


def _environment() -> dict[str, object]:
    return {
        "selected_gpu": {
            "physical_index": None,
            "logical_index": 0,
            "uuid": "GPU-ABC",
            "name": "NVIDIA GeForce RTX 4090",
            "memory_total_mib": 24563,
            "async_engine_count": 5,
            "device_overlap": 1,
            "concurrent_kernels": 1,
        },
        "driver_version": 12050,
        "cuda_driver_version": 12050,
        "cuda_runtime_version": 12040,
        "nsight_systems": "NVIDIA Nsight Systems version 2026.2.1.210",
        "os": "Windows-test",
    }


def _write_trace_sqlite(path: Path, *, kernel_duration_ns: int, launch_duration_ns: int) -> None:
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE StringIds (id INTEGER PRIMARY KEY, value TEXT)")
    connection.execute(
        "CREATE TABLE CUPTI_ACTIVITY_KIND_RUNTIME "
        "(start INTEGER, end INTEGER, nameId INTEGER, correlationId INTEGER, globalTid INTEGER)"
    )
    connection.execute(
        "CREATE TABLE CUPTI_ACTIVITY_KIND_KERNEL "
        "(start INTEGER, end INTEGER, correlationId INTEGER, demangledName INTEGER, "
        "shortName INTEGER, streamId INTEGER)"
    )
    connection.execute(
        "CREATE TABLE CUPTI_ACTIVITY_KIND_MEMCPY "
        "(start INTEGER, end INTEGER, correlationId INTEGER, copyKind INTEGER, "
        "bytes INTEGER, streamId INTEGER)"
    )
    connection.executemany(
        "INSERT INTO StringIds (id, value) VALUES (?, ?)",
        [
            (38, "cudaMemcpyAsync_v3020"),
            (47, "cudaLaunchKernel_v7000"),
            (45, "<unnamed>::q0_spin_kernel(unsigned long long)"),
        ],
    )
    connection.execute(
        "INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)",
        (30_259_720, 30_715_272, 38, 127, 100),
    )
    connection.execute(
        "INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)",
        (30_922_624, 30_922_624 + launch_duration_ns, 47, 128, 200),
    )
    connection.execute(
        "INSERT INTO CUPTI_ACTIVITY_KIND_MEMCPY VALUES (?, ?, ?, ?, ?, ?)",
        (77_979_638, 87_266_973, 127, 2, DIAGNOSTIC_D2H_BYTES, 14),
    )
    connection.execute(
        "INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES (?, ?, ?, ?, ?, ?)",
        (88_995_128, 88_995_128 + kernel_duration_ns, 128, 45, 45, 13),
    )
    connection.commit()
    connection.close()


def test_two_arms_differ_only_by_warmup_flag(tmp_path):
    nsys = tmp_path / "nsys.exe"
    binary = tmp_path / "q0.exe"
    argv_a = build_pair_arm_argv(
        nsys, binary, ARM_A, tmp_path / "arm-a-no-warmup", f"{RUN_ID}.a.{CASE_ID.lower()}"
    )
    argv_b = build_pair_arm_argv(
        nsys, binary, ARM_B, tmp_path / "arm-b-warmup", f"{RUN_ID}.b.{CASE_ID.lower()}"
    )

    # 仅 trace 输出目录与 run identity 不同，其余逐元素相同。
    assert len(argv_a) == 17
    assert len(argv_b) == 18
    assert argv_b[-1] == WARMUP_FLAG
    assert argv_a.count(WARMUP_FLAG) == 0
    assert argv_b.count(WARMUP_FLAG) == 1
    normalized_a = list(argv_a)
    normalized_b = list(argv_b)
    normalized_a[normalized_a.index("--run-id") + 1] = "<run-id>"
    normalized_b[normalized_b.index("--run-id") + 1] = "<run-id>"
    normalized_a[normalized_a.index("-o") + 1] = "trace"
    normalized_b[normalized_b.index("-o") + 1] = "trace"
    assert normalized_b[:-1] == normalized_a

    # A' 与既有冻结 D2H diagnostic argv 完全一致（同一 measured 构造）。
    baseline = build_baseline_argv(
        nsys, binary, tmp_path / "arm-a-no-warmup" / "trace", f"{RUN_ID}.a.{CASE_ID.lower()}"
    )
    assert baseline == argv_a
    assert argv_a.count("--trace=cuda,nvtx") == 1
    assert not any("wddm" in argument.lower() for argument in argv_a + argv_b)


def test_summarize_sqlite_descriptive_classes(tmp_path):
    reduced = tmp_path / "reduced.sqlite"
    _write_trace_sqlite(reduced, kernel_duration_ns=10_000_869, launch_duration_ns=45_000)
    summary = summarize_warmup_diagnostic_sqlite(reduced)
    assert summary["overlap_ns"] == 0
    assert summary["completion_order"] == "KERNEL_TERMINAL"
    assert summary["gap_ns"] == 1_728_155
    assert summary["descriptive_class"] == "OVERLAP_ZERO_LAUNCH_LATENCY_REDUCED"

    high = tmp_path / "high.sqlite"
    _write_trace_sqlite(high, kernel_duration_ns=10_000_869, launch_duration_ns=57_281_975)
    summary_high = summarize_warmup_diagnostic_sqlite(high)
    assert summary_high["descriptive_class"] == "OVERLAP_ZERO_LAUNCH_LATENCY_STILL_HIGH"


def test_summarize_sqlite_fails_closed_without_required_tables(tmp_path):
    trace = tmp_path / "empty.sqlite"
    connection = sqlite3.connect(trace)
    connection.execute("CREATE TABLE StringIds (id INTEGER PRIMARY KEY, value TEXT)")
    connection.commit()
    connection.close()

    with pytest.raises(KernelMemopD2HWarmupDiagnosticError, match="缺少必需表"):
        summarize_warmup_diagnostic_sqlite(trace)


@pytest.mark.parametrize(
    ("overlap_a", "overlap_b", "valid", "expected"),
    [
        (0, 1, True, "A_PRIME_0_B_POSITIVE"),
        (0, 0, True, "BOTH_ZERO"),
        (1, 1, True, "A_PRIME_POSITIVE_B_POSITIVE"),
        (1, 0, True, "A_PRIME_POSITIVE_B_ZERO"),
        (0, 1, False, "PAIR_INVALID"),
        (1, 1, False, "PAIR_INVALID"),
    ],
)
def test_classify_pair_outcome_pre_registered_mapping(
    overlap_a, overlap_b, valid, expected
):
    assert (
        classify_pair_outcome(
            overlap_a_ns=overlap_a, overlap_b_ns=overlap_b, arms_valid=valid
        )
        == expected
    )


def test_pair_outcome_policy_is_frozen():
    from exposedpath_v141.q0_kernel_memop_d2h_warmup_diagnostic import (
        PAIR_OUTCOME_POLICY,
        PAIR_OUTCOME_RULE,
    )

    assert set(PAIR_OUTCOME_POLICY) == {
        "A_PRIME_0_B_POSITIVE",
        "BOTH_ZERO",
        "A_PRIME_POSITIVE_B_POSITIVE",
        "A_PRIME_POSITIVE_B_ZERO",
        "PAIR_INVALID",
    }
    # A'>0 且 B>0 时不得归因于 warm-up。
    assert "must NOT be attributed to warm-up" in PAIR_OUTCOME_POLICY[
        "A_PRIME_POSITIVE_B_POSITIVE"
    ]
    assert "did not restore overlap" in PAIR_OUTCOME_POLICY["BOTH_ZERO"]
    assert "descriptive only" in PAIR_OUTCOME_POLICY["A_PRIME_POSITIVE_B_ZERO"]
    assert "controlled association" in PAIR_OUTCOME_POLICY["A_PRIME_0_B_POSITIVE"]
    assert "PAIR_INVALID" in PAIR_OUTCOME_RULE


def _diagnostic_stdout(*, enabled: bool, status: str) -> str:
    """构造与 binary 一致的机读诊断行。"""

    return (
        'EXPOSEDPATH_DIAGNOSTIC_V1:{"cuda_module_loading_mode":"LAZY",'
        f'"warmup_enabled":{str(enabled).lower()},'
        '"warmup_kernel_ms":10,"warmup_host_ns":123456,'
        f'"warmup_status":"{status}",'
        '"warmup_interleave":"OUTSIDE_CAPTURE_RANGE"}\n'
    )


def _runner(seen: list[list[str]], *, arm_b_launch_ns: int = 45_000):
    def run(argv, **_kwargs):
        command = [str(value) for value in argv]
        seen.append(command)
        if len(command) > 1 and command[1] == "profile":
            is_b = command[-1] == WARMUP_FLAG
            Path(command[command.index("-o") + 1]).with_suffix(".nsys-rep").write_bytes(
                b"warmup-pair-raw"
            )
            stdout = _diagnostic_stdout(
                enabled=is_b, status="PASS" if is_b else "NOT_APPLICABLE"
            )
            return subprocess.CompletedProcess(command, 0, stdout, "")
        if len(command) > 1 and command[1] == "export":
            output = Path(command[command.index("--output") + 1])
            launch_ns = arm_b_launch_ns if "arm-b-warmup" in str(output) else 57_281_975
            _write_trace_sqlite(output, kernel_duration_ns=10_000_869, launch_duration_ns=launch_ns)
            return subprocess.CompletedProcess(command, 0, "export ok", "")
        raise AssertionError(command)

    return run


def test_pair_run_records_matched_arms_without_q0_upgrade(tmp_path):
    binary = tmp_path / "q0.exe"
    nsys = tmp_path / "nsys.exe"
    binary.write_bytes(b"q0-binary")
    nsys.write_bytes(b"nsys")
    output = tmp_path / "pair"
    seen: list[list[str]] = []

    receipt_path = run_kernel_memop_d2h_warmup_pair_diagnostic(
        output,
        binary,
        nsys,
        run_id=RUN_ID,
        cuda_visible_device="GPU-ABC",
        implementation_commit=IMPL_COMMIT,
        process_runner=_runner(seen),
        environment_probe=lambda *_: _environment(),
    )

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    plan = json.loads((output / "pair_plan.json").read_text(encoding="utf-8"))

    assert receipt["q0_status"] == "NOT_RUN"
    assert receipt["data_role"] == "Engineering"
    assert receipt["implementation_commit"] == IMPL_COMMIT
    assert receipt["baseline_reference_commit"] == BASELINE_REFERENCE_COMMIT
    assert receipt["research_eligibility"]["formal_evidence"] is False
    assert [arm["arm"] for arm in receipt["arms"]] == [ARM_A, ARM_B]

    arm_a, arm_b = receipt["arms"]
    assert arm_a["warmup"]["warmup_enabled"] is False
    assert arm_a["warmup"]["warmup_status"] == "NOT_APPLICABLE"
    assert arm_a["warmup"]["cuda_module_loading_mode"] == "LAZY"
    assert arm_b["warmup"]["warmup_enabled"] is True
    assert arm_b["warmup"]["warmup_status"] == "PASS"
    assert arm_b["warmup"]["cuda_module_loading_mode"] == "LAZY"
    assert arm_a["measured"]["descriptive_class"] == "OVERLAP_ZERO_LAUNCH_LATENCY_STILL_HIGH"
    assert arm_b["measured"]["descriptive_class"] == "OVERLAP_ZERO_LAUNCH_LATENCY_REDUCED"
    assert arm_a["measured"]["overlap_ns"] == 0
    assert arm_b["measured"]["overlap_ns"] == 0

    evidence = receipt["construction_diff_evidence"]
    assert evidence["binary_sha256_equal"] is True
    assert evidence["nsys_sha256_equal"] is True
    assert evidence["gpu_uuid_equal"] is True
    assert evidence["environment_equal"] is True
    assert evidence["argv_equal_except_run_id_output_and_warmup_flag"] is True
    assert evidence["warmup_flag_only_on_b"] is True
    assert evidence["cuda_module_loading_mode_equal"] is True
    assert evidence["intended_construction_diff"] == WARMUP_FLAG
    assert evidence["execution_order"] == [ARM_A, ARM_B]
    assert evidence["claim_scope"] == "ENGINEERING_CONTROLLED_ASSOCIATION_ONLY"
    assert "CROSS_PROCESS_CLOCK_OR_CACHE_CARRYOVER" in evidence[
        "fixed_execution_order_limitation"
    ]

    assert plan["status"] == "PRE_REGISTERED_NOT_EXECUTED"
    assert plan["execution_order"] == [ARM_A, ARM_B]
    assert plan["single_variable"] == WARMUP_FLAG
    assert plan["implementation_commit"] == IMPL_COMMIT
    assert plan["baseline_reference_commit"] == BASELINE_REFERENCE_COMMIT
    assert "NO_RETRY" in plan["preregistered_rules"]
    assert "FIXED_EXECUTION_ORDER_IS_A_KNOWN_LIMITATION" in plan["preregistered_rules"]
    assert plan["interpretation_boundary"]["forbidden_attribution"] == [
        "LAZY_MODULE_LOADING",
        "WDDM",
        "DRIVER",
        "RUNTIME",
    ]
    assert "controlled association" in plan["interpretation_boundary"][
        "allowed_conclusion_if_b_overlaps"
    ]
    assert "No concrete mechanism causality" in plan["interpretation_boundary"][
        "not_allowed_conclusion"
    ]
    pair_plan_policy = plan["pair_level_interpretation"]
    assert pair_plan_policy["engineering_only"] is True
    assert pair_plan_policy["changes_gate6_or_q0"] is False
    assert "PAIR_INVALID" in pair_plan_policy["rule"]

    # 本 fixture 为 A'=0 / B=0，必须归类为 BOTH_ZERO。
    pair = receipt["pair_interpretation"]
    assert pair["pair_outcome"] == "BOTH_ZERO"
    assert pair["overlap_a_prime_ns"] == 0
    assert pair["overlap_b_ns"] == 0
    assert pair["arms_valid"] is True
    assert pair["changes_gate6_or_q0"] is False
    assert "did not restore overlap" in pair["pair_outcome_statement"]

    # 预注册执行顺序：A' 先于 B，且各只采集一次。
    profiles = [command for command in seen if command[1] == "profile"]
    assert len(profiles) == 2
    assert profiles[0][-1] != WARMUP_FLAG
    assert profiles[1][-1] == WARMUP_FLAG

    with pytest.raises(KernelMemopD2HWarmupDiagnosticError, match="拒绝覆盖"):
        run_kernel_memop_d2h_warmup_pair_diagnostic(
            output,
            binary,
            nsys,
            run_id=RUN_ID,
            cuda_visible_device="GPU-ABC",
            implementation_commit=IMPL_COMMIT,
            process_runner=_runner([]),
            environment_probe=lambda *_: _environment(),
        )


def test_pair_run_stops_when_b_warmup_not_completed(tmp_path):
    binary = tmp_path / "q0.exe"
    nsys = tmp_path / "nsys.exe"
    binary.write_bytes(b"q0")
    nsys.write_bytes(b"nsys")

    def broken_runner(argv, **_kwargs):
        command = [str(value) for value in argv]
        if command[1] == "profile":
            Path(command[command.index("-o") + 1]).with_suffix(".nsys-rep").write_bytes(b"raw")
            is_b = command[-1] == WARMUP_FLAG
            stdout = _diagnostic_stdout(
                enabled=is_b, status="FAIL" if is_b else "NOT_APPLICABLE"
            )
            return subprocess.CompletedProcess(command, 0, stdout, "")
        if command[1] == "export":
            output = Path(command[command.index("--output") + 1])
            _write_trace_sqlite(output, kernel_duration_ns=10_000_869, launch_duration_ns=45_000)
            return subprocess.CompletedProcess(command, 0, "ok", "")
        raise AssertionError(command)

    with pytest.raises(KernelMemopD2HWarmupDiagnosticError, match="warm-up 未成功完成"):
        run_kernel_memop_d2h_warmup_pair_diagnostic(
            tmp_path / "out",
            binary,
            nsys,
            run_id=RUN_ID,
            cuda_visible_device="GPU-ABC",
            implementation_commit=IMPL_COMMIT,
            process_runner=broken_runner,
            environment_probe=lambda *_: _environment(),
        )


def test_pair_run_rejects_warmup_line_in_arm_a(tmp_path):
    binary = tmp_path / "q0.exe"
    nsys = tmp_path / "nsys.exe"
    binary.write_bytes(b"q0")
    nsys.write_bytes(b"nsys")

    def leaking_runner(argv, **_kwargs):
        command = [str(value) for value in argv]
        if command[1] == "profile":
            Path(command[command.index("-o") + 1]).with_suffix(".nsys-rep").write_bytes(b"raw")
            stdout = (
                'EXPOSEDPATH_DIAGNOSTIC_V1:{"cuda_module_loading_mode":"LAZY",'
                '"warmup_enabled":true,"warmup_kernel_ms":10,"warmup_host_ns":1,'
                '"warmup_status":"PASS","warmup_interleave":"OUTSIDE_CAPTURE_RANGE"}\n'
            )
            return subprocess.CompletedProcess(command, 0, stdout, "")
        raise AssertionError(command)

    with pytest.raises(KernelMemopD2HWarmupDiagnosticError, match="A' 不得启用 warm-up"):
        run_kernel_memop_d2h_warmup_pair_diagnostic(
            tmp_path / "out",
            binary,
            nsys,
            run_id=RUN_ID,
            cuda_visible_device="GPU-ABC",
            implementation_commit=IMPL_COMMIT,
            process_runner=leaking_runner,
            environment_probe=lambda *_: _environment(),
        )


@pytest.mark.parametrize(
    "run_id",
    [
        "q0-win-4090-20260917-r11",
        "q0-win-4090-20260918-kernel-memop-d2h-diag-64m-10ms-01",
        "q0-win-4090-20260918-kernel-memop-d2h-diag-64m-1ms-warmup-01",
        "q0-win-4090-20260918-kernel-memop-size-diag-64m-10ms-warmup-01",
    ],
)
def test_pair_diagnostic_rejects_other_run_identity(tmp_path, run_id):
    binary = tmp_path / "q0.exe"
    nsys = tmp_path / "nsys.exe"
    binary.write_bytes(b"q0")
    nsys.write_bytes(b"nsys")

    with pytest.raises(KernelMemopD2HWarmupDiagnosticError, match="d2h-diag-64m-10ms-warmup"):
        run_kernel_memop_d2h_warmup_pair_diagnostic(
            tmp_path / run_id,
            binary,
            nsys,
            run_id=run_id,
            cuda_visible_device="GPU-ABC",
            implementation_commit=IMPL_COMMIT,
        )


def test_pair_diagnostic_requires_both_commits(tmp_path):
    binary = tmp_path / "q0.exe"
    nsys = tmp_path / "nsys.exe"
    binary.write_bytes(b"q0")
    nsys.write_bytes(b"nsys")

    with pytest.raises(KernelMemopD2HWarmupDiagnosticError, match="implementation_commit"):
        run_kernel_memop_d2h_warmup_pair_diagnostic(
            tmp_path / "out1",
            binary,
            nsys,
            run_id=RUN_ID,
            cuda_visible_device="GPU-ABC",
            implementation_commit="",
        )
    with pytest.raises(KernelMemopD2HWarmupDiagnosticError, match="baseline_reference_commit"):
        run_kernel_memop_d2h_warmup_pair_diagnostic(
            tmp_path / "out2",
            binary,
            nsys,
            run_id=RUN_ID,
            cuda_visible_device="GPU-ABC",
            implementation_commit=IMPL_COMMIT,
            baseline_reference_commit="",
        )


def test_pair_cli_reports_both_arms_and_not_q0(monkeypatch, tmp_path, capsys):
    receipt = tmp_path / "pair_receipt.json"
    receipt.write_text(
        json.dumps(
            {
                "implementation_commit": IMPL_COMMIT,
                "baseline_reference_commit": BASELINE_REFERENCE_COMMIT,
                "diagnostic_parameters": {
                    "d2h_size_mib": 64,
                    "kernel_duration_ms": 10,
                    "warmup_kernel_ms": 10,
                    "warmup_interleave": "OUTSIDE_CAPTURE_RANGE",
                },
                "arms": [
                    {
                        "arm": ARM_A,
                        "warmup": None,
                        "source": {"binary": {"sha256": "AB" * 32}},
                        "measured": {
                            "measured_launch_kernel_api_ns": 57_281_975,
                            "overlap_ns": 0,
                            "gap_ns": 1_728_155,
                            "completion_order": "KERNEL_TERMINAL",
                            "descriptive_class": "OVERLAP_ZERO_LAUNCH_LATENCY_STILL_HIGH",
                        },
                    },
                    {
                        "arm": ARM_B,
                        "warmup": {"warmup_status": "PASS", "cuda_module_loading_mode": "LAZY"},
                        "source": {"binary": {"sha256": "AB" * 32}},
                        "measured": {
                            "measured_launch_kernel_api_ns": 45_000,
                            "overlap_ns": 0,
                            "gap_ns": 100,
                            "completion_order": "KERNEL_TERMINAL",
                            "descriptive_class": "OVERLAP_ZERO_LAUNCH_LATENCY_REDUCED",
                        },
                    },
                ],
                "construction_diff_evidence": {
                    "binary_sha256_equal": True,
                    "environment_equal": True,
                    "argv_equal_except_run_id_output_and_warmup_flag": True,
                    "intended_construction_diff": "--diagnostic-warmup-kernel",
                    "execution_order": ["A_PRIME_NO_WARMUP", "B_WARMUP"],
                    "fixed_execution_order_limitation": (
                        "A_PRIME_ALWAYS_FIRST_SO_CROSS_PROCESS_CLOCK_OR_CACHE_"
                        "CARRYOVER_CANNOT_BE_EXCLUDED"
                    ),
                    "claim_scope": "ENGINEERING_CONTROLLED_ASSOCIATION_ONLY",
                },
                "pair_interpretation": {
                    "pair_outcome": "BOTH_ZERO",
                    "pair_outcome_statement": (
                        "warm-up did not restore overlap; Engineering-only"
                    ),
                    "overlap_a_prime_ns": 0,
                    "overlap_b_ns": 0,
                    "changes_gate6_or_q0": False,
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "exposedpath_v141.cli.run_kernel_memop_d2h_warmup_pair_diagnostic",
        lambda *_args, **_kwargs: receipt,
    )

    status = main(
        [
            "run-q0-kernel-memop-d2h-warmup-diagnostic",
            "--output-dir", str(tmp_path / "out"),
            "--binary", str(tmp_path / "q0.exe"),
            "--nsys", str(tmp_path / "nsys.exe"),
            "--run-id", RUN_ID,
            "--cuda-visible-device", "GPU-ABC",
            "--implementation-commit", IMPL_COMMIT,
            "--baseline-reference-commit", BASELINE_REFERENCE_COMMIT,
        ]
    )

    output = capsys.readouterr().out
    assert status == 0
    assert "diagnostic_scope: ENGINEERING_ONLY" in output
    assert f"implementation_commit: {IMPL_COMMIT}" in output
    assert f"baseline_reference_commit: {BASELINE_REFERENCE_COMMIT}" in output
    assert f"arm {ARM_A}:" in output
    assert f"arm {ARM_B}:" in output
    assert "construction_diff_evidence: same_binary=True, same_env=True" in output
    assert "claim_scope: ENGINEERING_CONTROLLED_ASSOCIATION_ONLY" in output
    assert "limitation: fixed_execution_order=" in output
    assert "pair_outcome: BOTH_ZERO" in output
    assert "pair_outcome_statement: warm-up did not restore overlap" in output
    assert "changes_gate6_or_q0: False" in output
    assert "q0_execution_status: NOT_RUN" in output
