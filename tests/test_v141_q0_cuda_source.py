"""Q0 CUDA 微程序的无 GPU 编译、身份和参数边界测试。"""

from __future__ import annotations

import shutil
import subprocess
import sys
import os
from pathlib import Path

import pytest

from exposedpath_v141.q0_execution import (
    build_q0_compile_command,
    load_q0_execution_manifest,
)
from exposedpath_v141.cli import main


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "q0" / "cuda" / "exposedpath_q0.cu"


def test_compile_command_is_structured_and_preserves_paths_with_spaces(tmp_path):
    nvcc = tmp_path / "cuda toolkit" / "nvcc.exe"
    source = tmp_path / "source tree" / "q0.cu"
    output = tmp_path / "build output" / "q0.exe"

    command = build_q0_compile_command(nvcc, source, output, platform="windows")

    assert isinstance(command, tuple)
    assert command[0] == str(nvcc)
    assert str(source) in command
    assert command[-2:] == ("-o", str(output))
    assert all('"' not in argument for argument in command)


def test_compile_command_rejects_unknown_platform(tmp_path):
    with pytest.raises(ValueError, match="platform"):
        build_q0_compile_command(
            tmp_path / "nvcc", tmp_path / "q0.cu", tmp_path / "q0", platform="macos"
        )


@pytest.fixture(scope="module")
def compiled_q0(tmp_path_factory):
    nvcc = shutil.which("nvcc")
    if nvcc is None:
        pytest.skip("本机没有 nvcc；命令合同测试仍会运行")
    output = tmp_path_factory.mktemp("q0-cuda-build") / (
        "exposedpath_q0.exe" if sys.platform == "win32" else "exposedpath_q0"
    )
    command = build_q0_compile_command(
        Path(nvcc), SOURCE, output, platform="windows" if sys.platform == "win32" else "linux"
    )
    environment = os.environ.copy()
    environment.pop("CL", None)
    environment.pop("_CL_", None)
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return output


def test_compiled_binary_lists_exact_native_seed_cases_without_gpu(compiled_q0):
    manifest = load_q0_execution_manifest()
    expected = {
        case["native_seed_case_id"]
        for case in manifest["cases"]
        if case["native_seed_case_id"] is not None
    }

    completed = subprocess.run(
        [str(compiled_q0), "--list-cases"], capture_output=True, text=True, check=False
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert set(completed.stdout.splitlines()) == expected


def test_unknown_case_fails_before_cuda_initialization(compiled_q0):
    completed = subprocess.run(
        [str(compiled_q0), "--case", "Q0-UNKNOWN-001", "--run-id", "dry-list"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 2
    assert "unknown case" in completed.stderr.lower()


def test_build_cli_compiles_without_claiming_q0_pass(tmp_path, capsys):
    nvcc = shutil.which("nvcc")
    if nvcc is None:
        pytest.skip("本机没有 nvcc")
    output = tmp_path / ("q0.exe" if sys.platform == "win32" else "q0")

    status = main([
        "build-q0-microbench",
        "--nvcc", nvcc,
        "--output", str(output),
        "--platform", "windows" if sys.platform == "win32" else "linux",
    ])

    printed = capsys.readouterr().out
    assert status == 0
    assert output.is_file()
    assert "compile_status: PASS" in printed
    assert "q0_execution_status: NOT_RUN" in printed
