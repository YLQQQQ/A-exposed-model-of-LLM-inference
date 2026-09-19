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


def test_d2h_native_parameters_reject_h2d_run_identity_before_cuda(compiled_q0):
    completed = subprocess.run(
        [
            str(compiled_q0),
            "--case", "Q0-KERNEL-MEMOP-001",
            "--run-id", "q0-win-4090-20260917-kernel-memop-size-diag-64m-10ms-01.q0-kernel-memop-001",
            "--diagnostic-d2h-bytes", str(64 * 1024 * 1024),
            "--diagnostic-kernel-ms", "10",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 2
    assert "diagnostic parameters are only supported" in completed.stderr


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
    """混合构造用并发 Host 提交，且分配发生在 profiler/request 之前。"""

    source = SOURCE.read_text(encoding="utf-8")
    body = _function_body(source, "run_kernel_memop")
    main = source[source.index("int main("):]

    assert "kDefaultBufferBytes = 4096" in source
    assert "kKernelMemopBufferBytes = 512ULL * 1024ULL * 1024ULL" in source
    assert "kKernelMemopKernelMilliseconds = 10" in source
    assert "buffer_capacity_bytes" in source
    assert 'case_id == "Q0-KERNEL-MEMOP-001"' in main
    construction = "Resources resources(buffer_bytes, diagnostic_kernel_ms,"
    assert construction in main
    assert main.index(construction) < main.index(
        "CudaProfilerRange capture;"
    )
    assert '"KERNEL_A", r.first,' in body
    assert "r.kernel_memop_kernel_milliseconds" in body
    assert "r.buffer_capacity_bytes" in body
    assert "std::thread kernel_worker" in body
    worker_marker = 'worker_marker(c, id, "decode", "WORKER_KERNEL_MEMOP")'
    assert worker_marker in body
    assert body.index(worker_marker) < body.index(
        '"KERNEL_A", r.first,'
    )
    assert "kernel_ready" in body
    assert "release_kernel" in body
    assert "kernel_submitted" in body
    assert "start_condition.wait(" in body
    assert "start_condition.wait(lock, [&] { return kernel_submitted; });" in body
    assert body.index("cudaMemcpyAsync(") < body.index('"S_DEVICE"')
    assert body.index("return kernel_submitted;") < body.index('"S_DEVICE"')
    assert body.index('"S_DEVICE"') < body.index("kernel_worker.join();")
    assert "cudaStreamQuery" not in body
    assert "cudaEventQuery" not in body
    assert body.count("one_phase(c, id, [&] {") == 1
    assert body.count("sync_range(") == 1
    assert "request_range(" not in body
    assert "phase_range(" not in body
    assert "cudaMalloc(" not in body
    assert "cudaMallocHost(" not in body


def test_kernel_memop_diagnostic_parameters_are_strictly_isolated_from_default_q0():
    source = SOURCE.read_text(encoding="utf-8")
    main = source[source.index("int main("):]

    assert "kKernelMemopBufferBytes = 512ULL * 1024ULL * 1024ULL" in source
    assert "kKernelMemopKernelMilliseconds = 10" in source
    assert '"--diagnostic-h2d-bytes"' in main
    assert '"--diagnostic-kernel-ms"' in main
    assert "64ULL * 1024ULL * 1024ULL" in main
    assert "kernel-memop-size-diag-64m-10ms" in main
    assert "diagnostic parameters are only supported" in main
    assert "diagnostic_h2d_bytes" in main
    assert "diagnostic_kernel_ms" in main


def test_d2h_diagnostic_keeps_default_h2d_and_adds_no_cuda_dependency():
    source = SOURCE.read_text(encoding="utf-8")
    body = _function_body(source, "run_kernel_memop")
    main = source[source.index("int main("):]

    assert "KernelMemopCopyDirection::HOST_TO_DEVICE" in source
    assert "KernelMemopCopyDirection::DEVICE_TO_HOST" in body
    assert "cudaMemcpyDeviceToHost" in body
    assert '"--diagnostic-d2h-bytes"' in main
    assert "kernel-memop-d2h-diag-64m-10ms" in main
    assert body.count("cudaMemcpyAsync(") == 1
    assert "cudaMemset" not in body
    assert "cudaEventRecord" not in body
    assert "cudaStreamWaitEvent" not in body
    assert "cudaEventSynchronize" not in body
    assert "cudaStreamQuery" not in body
    assert "cudaEventQuery" not in body
    assert body.count("cudaDeviceSynchronize") == 1


def test_formalshape_diagnostic_keeps_native_measured_defaults():
    source = SOURCE.read_text(encoding="utf-8")
    main = source[source.index("int main("):]
    assert 'const bool formalshape_diagnostic =' in main
    assert 'kernel-memop-h2d-formalshape-warmup-' in main
    assert 'positional_argc == 5 && case_id == "Q0-KERNEL-MEMOP-001"' in main
    assert 'diagnostic_warmup || d2h_diagnostic_parameters || formalshape_diagnostic' in main
    # No measured parameter is assigned inside the formalshape guard.
    segment = main[main.index('const bool formalshape_diagnostic ='):main.index('try {', main.index('const bool formalshape_diagnostic ='))]
    assert 'diagnostic_h2d_bytes =' not in segment
    assert 'diagnostic_copy_direction =' not in segment
    assert 'diagnostic_kernel_ms =' not in segment


def test_warmup_diagnostic_changes_only_the_precapture_warmup():
    """warm-up diagnostic 不得改动 measured construction。"""

    source = SOURCE.read_text(encoding="utf-8")
    body = _function_body(source, "run_kernel_memop")
    main = source[source.index("int main("):]
    warmup = _function_body(source, "warmup_kernel_memop")

    # measured 构造不变：仍然没有 event/gate/query，仅一个 device sync。
    assert body.count("cudaMemcpyAsync(") == 1
    assert "cudaEventRecord" not in body
    assert "cudaStreamWaitEvent" not in body
    assert "cudaEventSynchronize" not in body
    assert "cudaStreamQuery" not in body
    assert "cudaEventQuery" not in body
    assert "std::thread kernel_worker" in body
    assert "start_condition.wait(" in body
    assert body.count("sync_range(") == 1

    # warm-up 复用同一个 kernel 与既有 stream，不新增 event/gate/stream。
    assert "q0_spin_kernel<<<1, 1, 0, resources.first>>>" in warmup
    assert "cudaStreamSynchronize(resources.first)" in warmup
    assert "cudaEvent" not in source[source.index("void warmup_kernel_memop"):source.index("template <typename Body>")]
    assert "cudaStreamWaitEvent" not in warmup
    assert "cudaStreamCreate" not in warmup
    # module loading mode 只做记录，不改变构造。
    assert "cuModuleGetLoadingMode" in source
    assert "cuda_module_loading_mode" in source
    # metadata transport 必须走 NVTX marker，不再走 stdout。
    assert "print_warmup_diagnostic_line" not in source
    assert "EXPOSEDPATH_DIAGNOSTIC_V1:" in source
    assert "A_PRIME_NO_WARMUP" in source and "B_WARMUP" in source
    assert "warmup_interleave" in source and "OUTSIDE_CAPTURE_RANGE" in source
    assert "warmup_status" in source and "warmup_host_ns" in source
    # A'（不启用 warm-up）与 B 必须对称写入同一条 marker。
    assert "const bool emit_warmup_diagnostic" in main
    assert "diagnostic_warmup || d2h_diagnostic_parameters" in main
    # metadata transport 必须是 NVTX mark（单点事件），不是 range。
    assert "nvtxMarkA(text.c_str());" in source
    assert "emit_nvtx_mark(diagnostic_label);" in main
    assert "NvtxRange diagnostic(" not in main

    # warm-up 必须发生在 cudaProfilerStart()/request 之前。
    warmup_index = main.index("warmup_kernel_memop(resources, warmup_milliseconds);")
    capture_index = main.index("CudaProfilerRange capture;")
    assert warmup_index < capture_index
    # mark 必须写在 capture 开始之后、request 开始之前（request 之外）。
    marker_index = main.index(
        "warmup_diagnostic_label(diagnostic_warmup, warmup_host_ns)"
    )
    request_index = main.index("selected->second(resources, case_id, run_id);")
    assert capture_index < marker_index < request_index
    mark_index = main.index("emit_nvtx_mark(diagnostic_label);")
    assert marker_index < mark_index < request_index
    assert "--diagnostic-warmup-kernel" in main

    # 正常 Q0 argv 不含 warm-up 开关，且 warm-up 只允许出现在冻结 diagnostic identity 上。
    assert 'std::string(argv[argc - 1]) == "--diagnostic-warmup-kernel"' in main
    assert "is only supported for the frozen" in main


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


def _main_section(source: str) -> str:
    return source[source.index("int main("):]


def test_formal_measurement_initialization_flag_and_enum_match_frozen_manifest():
    """正式 argv 名称与两个 policy 取值必须与 Manifest/Schema 逐字一致。"""

    source = SOURCE.read_text(encoding="utf-8")
    manifest = load_q0_execution_manifest()
    policies = {case["measurement_initialization"] for case in manifest["cases"]}

    assert 'kMeasurementInitializationFlag = "--measurement-initialization"' in source
    assert 'kMeasurementInitializationNone = "NONE"' in source
    assert 'kMeasurementInitializationPreCaptureSameKernelWarmup =\n    "PRE_CAPTURE_SAME_KERNEL_WARMUP"' in source
    assert policies == {"NONE", "PRE_CAPTURE_SAME_KERNEL_WARMUP"}
    for policy in policies:
        assert f'"{policy}"' in source


def test_formal_warmup_decision_comes_from_manifest_policy_not_case_or_run_id():
    """binary 不得用 case_id、run-id、oracle 或结果决定是否预热。"""

    main = _main_section(SOURCE.read_text(encoding="utf-8"))
    start = main.index("const bool policy_warmup =")
    decision = main[start:main.index(";", start)]

    assert "measurement_initialization_present" in decision
    assert "measurement_initialization ==" in decision
    assert "kMeasurementInitializationPreCaptureSameKernelWarmup" in decision
    assert "case_id" not in decision
    assert "run_id" not in decision
    assert "regex" not in decision

    # warm-up 触发点同时接受 Engineering 开关与正式 policy，两者互不替代。
    assert "if (diagnostic_warmup || policy_warmup) {" in main


def test_formal_path_emits_no_diagnostic_metadata_mark():
    """正式路径不得写入 EXPOSEDPATH_DIAGNOSTIC_V1；mark 只属于 Engineering diagnostic。"""

    source = SOURCE.read_text(encoding="utf-8")
    main = _main_section(source)
    start = main.index("const bool emit_warmup_diagnostic =")
    emit = main[start:main.index(";", start)]

    assert "diagnostic_warmup" in emit
    assert "formalshape_diagnostic" in emit
    assert "policy_warmup" not in emit
    assert "measurement_initialization" not in emit


def test_formal_policy_is_rejected_when_combined_with_diagnostic_arguments():
    source = SOURCE.read_text(encoding="utf-8")
    main = _main_section(source)
    # 正式 policy 既出现在 parser 的未知取值检查里，也出现在互斥 guard 里；
    # 用 guard 唯一 message 反查它自己的 `if (`，避免误取前一处。
    anchor = main.index("is only valid for the formal native case argv")
    start = main.rindex("if (", 0, anchor)
    guard = main[start:main.index("return 2;", start)]

    for token in (
        "diagnostic_warmup",
        "diagnostic_parameters",
        "formalshape_diagnostic",
        "positional_argc != 5",
    ):
        assert token in guard, token
    assert "is only valid for the formal native case argv" in main


def test_formal_policy_parser_fails_closed_on_missing_duplicate_or_unknown_value():
    main = _main_section(SOURCE.read_text(encoding="utf-8"))

    # 无值 / 重复出现 / 未知取值都必须以非零码退出。
    assert "must appear exactly once" in main
    assert "unknown " in main
    assert "policy: " in main
    # policy 必须在位置形态校验之前被摘除，因此 argv[5]/argv[7] 等既有索引语义不变。
    parse_index = main.index("bool measurement_initialization_present = false;")
    shape_index = main.index("const bool h2d_diagnostic_parameters =")
    assert parse_index < shape_index

    # 缺失 policy 必须真的 STOP：formal native argv 在进入 CUDA 初始化前被拒绝，
    # 而不是静默按“无初始化”继续执行。
    anchor = main.index("formal native case argv requires")
    guard_start = main.rindex("if (", 0, anchor)
    missing_guard = main[guard_start:main.index("return 2;", guard_start)]
    assert "!measurement_initialization_present" in missing_guard
    assert "!diagnostic_warmup" in missing_guard
    assert "!diagnostic_parameters" in missing_guard
    assert "!formalshape_diagnostic" in missing_guard
    assert "kMeasurementInitializationFlag" in missing_guard


def test_formal_native_invocation_without_policy_fails_closed(compiled_q0):
    """真跑 binary：formal native argv 缺少 policy 必须在 CUDA 初始化前非零退出。"""

    completed = subprocess.run(
        [str(compiled_q0), "--case", "Q0-STREAM-001", "--run-id", "q0-formal-no-policy"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 2
    assert "--measurement-initialization" in completed.stderr
    assert "requires" in completed.stderr


def test_formal_warmup_uses_existing_measured_kernel_stream_and_stream_sync_only():
    source = SOURCE.read_text(encoding="utf-8")
    warmup = _function_body(source, "warmup_kernel_memop")

    assert "q0_spin_kernel<<<1, 1, 0, resources.first>>>" in warmup
    assert "cudaStreamSynchronize(resources.first)" in warmup
    # duration 由调用方显式传入，helper 自身不再绑定任何一种来源。
    assert "void warmup_kernel_memop(Resources& resources, int milliseconds)" in source
    assert "resources.cycles(milliseconds)" in warmup
    # 不得用更宽 scope 的同步代替，也不得新增 stream/event。
    assert "cudaDeviceSynchronize" not in warmup
    assert "cudaStreamCreate" not in warmup
    assert "cudaEvent" not in warmup
    assert "cudaStreamWaitEvent" not in warmup


def test_warmup_duration_source_differs_for_engineering_and_formal_paths():
    """Engineering diagnostic 固定 10 ms；formal policy 与 measured kernel 同源。"""

    source = SOURCE.read_text(encoding="utf-8")
    main = _main_section(source)

    assert "constexpr int kKernelMemopWarmupMilliseconds = 10;" in source
    start = main.index("const int warmup_milliseconds =")
    selection = main[start:main.index(";", start)]
    assert "diagnostic_warmup ? kKernelMemopWarmupMilliseconds" in selection
    assert "resources.kernel_memop_kernel_milliseconds" in selection
    assert "warmup_kernel_memop(resources, warmup_milliseconds);" in main


def test_list_cases_and_environment_json_stay_before_the_formal_policy_parser():
    main = _main_section(SOURCE.read_text(encoding="utf-8"))
    parse_index = main.index("bool measurement_initialization_present = false;")

    assert main.index('argc == 2 && std::string(argv[1]) == "--list-cases"') < parse_index
    assert main.index(
        'argc == 2 && std::string(argv[1]) == "--environment-json"'
    ) < parse_index


def test_engineering_diagnostic_argv_shape_is_unchanged_by_the_formal_policy():
    """Engineering diagnostic 不带正式 policy，因此摘除逻辑对它们是 no-op。"""

    main = _main_section(SOURCE.read_text(encoding="utf-8"))

    # 只有出现正式 policy 时才可能触发新的拒绝；缺失时沿用原 argv 语义。
    assert "if (measurement_initialization_present &&" in main
    assert 'std::string(argv[argc - 1]) == "--diagnostic-warmup-kernel"' in main
    assert '"--diagnostic-h2d-bytes"' in main
    assert '"--diagnostic-d2h-bytes"' in main
    assert '"--diagnostic-kernel-ms"' in main
    assert "diagnostic parameters are only supported" in main
    assert "--diagnostic-warmup-kernel is only supported for the frozen" in main
