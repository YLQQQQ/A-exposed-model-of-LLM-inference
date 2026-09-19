"""64 MiB D2H/10 ms KERNEL-MEMOP Engineering 方向诊断测试。"""

from __future__ import annotations

import json
import sqlite3
import subprocess
from pathlib import Path

import pytest

from exposedpath_v141.cli import main
from exposedpath_v141.q0_kernel_memop_d2h_diagnostic import (
    DIAGNOSTIC_D2H_BYTES,
    DIAGNOSTIC_KERNEL_MS,
    KernelMemopD2HDiagnosticError,
    build_kernel_memop_d2h_diagnostic_argv,
    run_kernel_memop_d2h_diagnostic,
)


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
            "can_map_host_memory": 1,
        },
        "driver_version": 12050,
        "cuda_driver_version": 12050,
        "cuda_runtime_version": 12040,
        "nsight_systems": "NVIDIA Nsight Systems version 2026.2.1.210",
        "os": "Windows-test",
    }


def _runner(seen: list[list[str]]):
    def run(argv, **_kwargs):
        command = [str(value) for value in argv]
        seen.append(command)
        if len(command) > 1 and command[1] == "profile":
            Path(command[command.index("-o") + 1]).with_suffix(".nsys-rep").write_bytes(
                b"d2h-diagnostic-raw"
            )
            return subprocess.CompletedProcess(command, 0, "profile ok", "")
        if len(command) > 1 and command[1] == "export":
            output = Path(command[command.index("--output") + 1])
            connection = sqlite3.connect(output)
            connection.execute("CREATE TABLE marker (value INTEGER)")
            connection.commit()
            connection.close()
            return subprocess.CompletedProcess(command, 0, "export ok", "")
        raise AssertionError(command)

    return run


def test_d2h_argv_is_isolated_and_changes_only_copy_direction(tmp_path):
    argv = build_kernel_memop_d2h_diagnostic_argv(
        tmp_path / "nsys.exe",
        tmp_path / "q0.exe",
        tmp_path / "trace",
        "q0-win-4090-20260917-kernel-memop-d2h-diag-64m-10ms-01.q0-kernel-memop-001",
    )

    assert argv.count("--trace=cuda,nvtx") == 1
    assert not any("wddm" in argument.lower() for argument in argv)
    assert argv[-8:] == [
        "--case", "Q0-KERNEL-MEMOP-001",
        "--run-id", "q0-win-4090-20260917-kernel-memop-d2h-diag-64m-10ms-01.q0-kernel-memop-001",
        "--diagnostic-d2h-bytes", str(64 * 1024 * 1024),
        "--diagnostic-kernel-ms", "10",
    ]
    assert DIAGNOSTIC_D2H_BYTES == 64 * 1024 * 1024
    assert DIAGNOSTIC_KERNEL_MS == 10


def test_d2h_run_records_engineering_parameters_without_q0_upgrade(tmp_path):
    binary = tmp_path / "q0.exe"
    nsys = tmp_path / "nsys.exe"
    binary.write_bytes(b"q0-binary")
    nsys.write_bytes(b"nsys")
    output = tmp_path / "diag"
    seen: list[list[str]] = []

    receipt_path = run_kernel_memop_d2h_diagnostic(
        output,
        binary,
        nsys,
        run_id="q0-win-4090-20260917-kernel-memop-d2h-diag-64m-10ms-01",
        cuda_visible_device="GPU-ABC",
        process_runner=_runner(seen),
        environment_probe=lambda *_: _environment(),
    )

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    manifest = json.loads((output / "diagnostic_manifest.json").read_text(encoding="utf-8"))
    source = json.loads((output / "source_manifest.json").read_text(encoding="utf-8"))
    expected = {
        "copy_direction": "DEVICE_TO_HOST",
        "d2h_size_bytes": 64 * 1024 * 1024,
        "d2h_size_mib": 64,
        "kernel_duration_ms": 10,
    }
    assert receipt["diagnostic_parameters"] == expected
    assert manifest["diagnostic_parameters"] == expected
    assert source["diagnostic_parameters"] == expected
    assert receipt["data_role"] == "Engineering"
    assert receipt["diagnostic_only"] is True
    assert receipt["q0_status"] == "NOT_RUN"
    assert receipt["research_eligibility"] == {
        "formal_evidence": False,
        "q0_status": "NOT_RUN",
        "scope": "KERNEL_MEMOP_D2H_ENGINEERING_DIAGNOSTIC_ONLY",
    }
    assert receipt["decision_policy"] == {
        "primary_measure": "device_interval_overlap_ns",
        "overlap_observed_if": "overlap_ns > 0",
        "terminal_required_for_direction_diagnostic": False,
        "on_overlap_zero": "STOP",
        "on_overlap_positive": "STOP_AND_REVIEW",
        "causal_verdict": "NOT_ESTABLISHED",
    }
    assert manifest["decision_policy"] == receipt["decision_policy"]
    profile = next(command for command in seen if command[1] == "profile")
    assert "--diagnostic-d2h-bytes" in profile
    assert "--diagnostic-h2d-bytes" not in profile
    assert (output / "trace.nsys-rep").is_file()
    assert (output / "trace.sqlite").is_file()

    with pytest.raises(KernelMemopD2HDiagnosticError, match="拒绝覆盖"):
        run_kernel_memop_d2h_diagnostic(
            output,
            binary,
            nsys,
            run_id="q0-win-4090-20260917-kernel-memop-d2h-diag-64m-10ms-01",
            cuda_visible_device="GPU-ABC",
        )


@pytest.mark.parametrize(
    "run_id",
    [
        "q0-win-4090-20260917-r11",
        "q0-win-4090-20260917-kernel-memop-size-diag-64m-10ms-01",
        "q0-win-4090-20260917-kernel-memop-d2h-diag-128m-10ms-01",
        "q0-win-4090-20260917-kernel-memop-d2h-diag-64m-1ms-01",
    ],
)
def test_d2h_diagnostic_rejects_other_run_identity(tmp_path, run_id):
    binary = tmp_path / "q0.exe"
    nsys = tmp_path / "nsys.exe"
    binary.write_bytes(b"q0")
    nsys.write_bytes(b"nsys")

    with pytest.raises(KernelMemopD2HDiagnosticError, match="d2h-diag-64m-10ms"):
        run_kernel_memop_d2h_diagnostic(
            tmp_path / run_id,
            binary,
            nsys,
            run_id=run_id,
            cuda_visible_device="GPU-ABC",
        )


def test_d2h_cli_reports_engineering_only_and_not_q0(monkeypatch, tmp_path, capsys):
    receipt = tmp_path / "diagnostic_receipt.json"
    receipt.write_text(
        json.dumps({"diagnostic_parameters": {"d2h_size_mib": 64, "kernel_duration_ms": 10}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "exposedpath_v141.cli.run_kernel_memop_d2h_diagnostic",
        lambda *_args, **_kwargs: receipt,
    )

    status = main(
        [
            "run-q0-kernel-memop-d2h-diagnostic",
            "--output-dir", str(tmp_path / "out"),
            "--binary", str(tmp_path / "q0.exe"),
            "--nsys", str(tmp_path / "nsys.exe"),
            "--run-id", "q0-win-4090-20260917-kernel-memop-d2h-diag-64m-10ms-01",
            "--cuda-visible-device", "GPU-ABC",
        ]
    )

    output = capsys.readouterr().out
    assert status == 0
    assert "diagnostic_scope: ENGINEERING_ONLY" in output
    assert "diagnostic_parameters: 64 MiB D2H, 10 ms kernel" in output
    assert "q0_execution_status: NOT_RUN" in output
