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


def _function_body(source: str, name: str) -> str:
    """提取一个顶层 C++ 函数体，用于检查无法在无 GPU 环境实跑的 NVTX 所有权结构。"""

    signature = f"void {name}("
    start = source.index(signature)
    opening = source.index("{", start)
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[opening + 1:index]
    raise AssertionError(f"无法解析函数体：{name}")


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


def test_capture_drains_controlled_work_before_profiler_stop():
    source = SOURCE.read_text(encoding="utf-8")

    case_call = source.index("selected->second(resources, case_id, run_id);")
    drain = source.index("CUDA_CHECK(cudaDeviceSynchronize());", case_call)
    capture_scope_end = source.index("    }\n    return 0;", drain)

    assert case_call < drain < capture_scope_end


@pytest.mark.parametrize(
    ("function_name", "worker_labels"),
    [
        ("run_ptds", ("WORKER_PTDS_OTHER",)),
        ("run_multithread", ("WORKER_THREAD_A", "WORKER_THREAD_B")),
        ("run_overlapping_sync", ("WORKER_SYNC_A", "WORKER_SYNC_B")),
    ],
)
def test_multithread_cases_have_one_coordinator_scope_covering_all_workers(
    function_name, worker_labels
):
    """捕获 worker 自建同 identity request，或 coordinator 范围未覆盖线程生命周期。"""

    body = _function_body(SOURCE.read_text(encoding="utf-8"), function_name)

    assert body.count("one_phase(c, id, [&] {") == 1
    assert "request_range(" not in body
    assert "phase_range(" not in body
    assert body.index("one_phase(c, id, [&] {") < body.index("std::thread")
    assert body.rfind(".join();") < body.rfind("  });")
    for label in worker_labels:
        assert f'worker_marker(c, id, "decode", "{label}")' in body


def test_worker_marker_ends_before_worker_cuda_api_to_preserve_unique_callsite():
    """worker 身份标记不能包住 activity/sync marker，否则 launch API 会有两个候选。"""

    source = SOURCE.read_text(encoding="utf-8")
    body = _function_body(source, "worker_marker")

    assert "identity_json(\"marker\"" in body
    assert "NvtxRange" in body
    assert "cuda" not in body.lower()


def test_ptds_request_uses_one_host_callback_instead_of_cuda_query_polling():
    """PTDS worker 完成协调不能生成重复的 CUDA query/synchronization activity。"""

    body = _function_body(SOURCE.read_text(encoding="utf-8"), "run_ptds")

    assert "cudaStreamQuery" not in body
    assert "cudaEventQuery" not in body
    assert "cudaLaunchHostFunc(cudaStreamPerThread" in body
    assert "completion.condition.wait(" in body
    assert "sleep_for" not in body
    assert body.index('"K_OTHER_THREAD"') < body.index('"K_PTDS"')
    assert body.index('"S_PTDS"') < body.index("other.join();")
    assert body.count("sync_range(") == 1


def test_kernel_memop_uses_case_scoped_preallocated_capacity_for_stable_overlap():
    """混合构造必须让 H2D 足够长，且分配发生在 profiler/request 之前。"""

    source = SOURCE.read_text(encoding="utf-8")
    body = _function_body(source, "run_kernel_memop")
    main = source[source.index("int main("):]

    assert "kDefaultBufferBytes = 4096" in source
    assert "kKernelMemopBufferBytes = 512ULL * 1024ULL * 1024ULL" in source
    assert "kKernelMemopKernelMilliseconds = 10" in source
    assert "buffer_capacity_bytes" in source
    assert 'case_id == "Q0-KERNEL-MEMOP-001"' in main
    assert "Resources resources(buffer_bytes);" in main
    assert main.index("Resources resources(buffer_bytes);") < main.index(
        "CudaProfilerRange capture;"
    )
    assert '"KERNEL_A", r.first, kKernelMemopKernelMilliseconds' in body
    assert "r.buffer_capacity_bytes" in body
    assert "cudaMalloc(" not in body
    assert "cudaMallocHost(" not in body


@pytest.mark.parametrize(
    "function_name",
    ["run_ptds", "run_multithread", "run_overlapping_sync"],
)
def test_multithread_cases_do_not_poll_cuda_completion(function_name):
    body = _function_body(SOURCE.read_text(encoding="utf-8"), function_name)

    assert "cudaStreamQuery" not in body
    assert "cudaEventQuery" not in body


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
