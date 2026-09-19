"""64 MiB/10 ms KERNEL-MEMOP Engineering 参数诊断测试。"""

from __future__ import annotations

import json
import sqlite3
import subprocess
from pathlib import Path

import pytest

from exposedpath_v141.cli import main
from exposedpath_v141.q0_kernel_memop_diagnostic import (
    DIAGNOSTIC_H2D_BYTES,
    DIAGNOSTIC_KERNEL_MS,
    KernelMemopDiagnosticError,
    build_kernel_memop_diagnostic_argv,
    run_kernel_memop_diagnostic,
)


def test_diagnostic_argv_uses_standard_trace_and_explicit_frozen_parameters(tmp_path):
    argv = build_kernel_memop_diagnostic_argv(
        tmp_path / "nsys.exe",
        tmp_path / "q0.exe",
        tmp_path / "trace",
        "q0-win-4090-20260917-kernel-memop-size-diag-64m-10ms-01.q0-kernel-memop-001",
    )

    assert argv.count("--trace=cuda,nvtx") == 1
    assert not any("wddm" in argument.lower() for argument in argv)
    assert "--diagnostic-d2h-bytes" not in argv
    assert argv[-8:] == [
        "--case", "Q0-KERNEL-MEMOP-001",
        "--run-id", "q0-win-4090-20260917-kernel-memop-size-diag-64m-10ms-01.q0-kernel-memop-001",
        "--diagnostic-h2d-bytes", str(64 * 1024 * 1024),
        "--diagnostic-kernel-ms", "10",
    ]
    assert DIAGNOSTIC_H2D_BYTES == 64 * 1024 * 1024
    assert DIAGNOSTIC_KERNEL_MS == 10


def _environment() -> dict[str, object]:
    return {
        "selected_gpu": {
            "physical_index": None,
            "logical_index": 0,
            "uuid": "GPU-ABC",
            "name": "NVIDIA GeForce RTX 4090",
            "memory_total_mib": 24563,
            "async_engine_count": 2,
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
                b"size-diagnostic-raw"
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


def test_run_diagnostic_records_parameters_and_never_upgrades_q0(tmp_path):
    binary = tmp_path / "q0.exe"
    nsys = tmp_path / "nsys.exe"
    binary.write_bytes(b"q0-binary")
    nsys.write_bytes(b"nsys")
    output = tmp_path / "diag"
    seen: list[list[str]] = []

    receipt_path = run_kernel_memop_diagnostic(
        output,
        binary,
        nsys,
        run_id="q0-win-4090-20260917-kernel-memop-size-diag-64m-10ms-01",
        cuda_visible_device="GPU-ABC",
        process_runner=_runner(seen),
        environment_probe=lambda *_: _environment(),
    )

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    manifest = json.loads((output / "diagnostic_manifest.json").read_text(encoding="utf-8"))
    source = json.loads((output / "source_manifest.json").read_text(encoding="utf-8"))
    expected = {
        "copy_direction": "HOST_TO_DEVICE",
        "h2d_size_bytes": 64 * 1024 * 1024,
        "h2d_size_mib": 64,
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
        "scope": "KERNEL_MEMOP_SIZE_ENGINEERING_DIAGNOSTIC_ONLY",
    }
    profile = next(command for command in seen if command[1] == "profile")
    assert "--trace=cuda,nvtx" in profile
    assert not any("wddm" in argument.lower() for argument in profile)
    assert (output / "trace.nsys-rep").is_file()
    assert (output / "trace.sqlite").is_file()

    with pytest.raises(KernelMemopDiagnosticError, match="拒绝覆盖"):
        run_kernel_memop_diagnostic(
            output,
            binary,
            nsys,
            run_id="q0-win-4090-20260917-kernel-memop-size-diag-64m-10ms-01",
            cuda_visible_device="GPU-ABC",
        )


@pytest.mark.parametrize(
    "run_id",
    [
        "q0-win-4090-20260917-r11",
        "q0-win-4090-20260917-kernel-memop-size-diag-64m-1ms-01",
        "q0-win-4090-20260917-kernel-memop-size-diag-128m-10ms-01",
    ],
)
def test_diagnostic_rejects_non_frozen_run_identity(tmp_path, run_id):
    binary = tmp_path / "q0.exe"
    nsys = tmp_path / "nsys.exe"
    binary.write_bytes(b"q0")
    nsys.write_bytes(b"nsys")

    with pytest.raises(KernelMemopDiagnosticError, match="64m-10ms"):
        run_kernel_memop_diagnostic(
            tmp_path / run_id,
            binary,
            nsys,
            run_id=run_id,
            cuda_visible_device="GPU-ABC",
        )


def test_diagnostic_cli_remains_engineering_only_and_not_q0(monkeypatch, tmp_path, capsys):
    receipt = tmp_path / "diagnostic_receipt.json"
    receipt.write_text(
        json.dumps({"diagnostic_parameters": {"h2d_size_mib": 64, "kernel_duration_ms": 10}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "exposedpath_v141.cli.run_kernel_memop_diagnostic",
        lambda *_args, **_kwargs: receipt,
    )

    status = main(
        [
            "run-q0-kernel-memop-diagnostic",
            "--output-dir", str(tmp_path / "out"),
            "--binary", str(tmp_path / "q0.exe"),
            "--nsys", str(tmp_path / "nsys.exe"),
            "--run-id", "q0-win-4090-20260917-kernel-memop-size-diag-64m-10ms-01",
            "--cuda-visible-device", "GPU-ABC",
        ]
    )

    output = capsys.readouterr().out
    assert status == 0
    assert "diagnostic_scope: ENGINEERING_ONLY" in output
    assert "diagnostic_parameters: 64 MiB H2D, 10 ms kernel" in output
    assert "q0_execution_status: NOT_RUN" in output
