"""Offline tests: native 512 MiB H2D construction and real Canonical -> S analysis."""

import hashlib
import importlib
import importlib.util
import json
import sqlite3
import subprocess
from pathlib import Path

import pytest

from test_v141_canonical_raw import SQLITE_SCHEMA
from test_v141_q0_kernel_memop_d2h_warmup_diagnostic import _environment


MODULE = "exposedpath_v141.q0_kernel_memop_h2d_warmup_diagnostic"
RUN_ID = "q0-win-4090-20260918-kernel-memop-h2d-formalshape-warmup-02"
CASE = "Q0-KERNEL-MEMOP-001"
IMPL = "1" * 40
PREFIX = "EXPOSEDPATH_DIAGNOSTIC_V1:"
BYTES = 536870912
PID = 100 << 24
TID = PID | 1
WORKER = PID | 2


def _m():
    return importlib.import_module(MODULE)


def _fixture(path, case_run_id, arm, *, overlap=True, kernel_terminal=False,
             marker_count=1, marker_type=34, marker_start=5, corrupt_corr=False):
    """Hand-checked intervals; no CUDA or profiler process is executed."""
    c = sqlite3.connect(path)
    c.executescript(SQLITE_SCHEMA)
    c.execute(
        "CREATE TABLE ENUM_CUPTI_STREAM_TYPE(id INTEGER NOT NULL, name TEXT, label TEXT)"
    )
    c.executemany("INSERT INTO META_DATA_EXPORT VALUES (?,?)", [
        ("EXPORT_PRODUCT_VERSION", "2026.2.1.210"),
        ("EXPORT_SCHEMA_VERSION", "3.25.0"), ("EXPORT_PARAM_LAZY", "false"),
    ])
    c.executemany("INSERT INTO META_DATA_CAPTURE VALUES (?,?)", [
        ("CAPTURE_EVENT_TYPE", "Cuda"), ("CAPTURE_EVENT_TYPE", "NvtxEvents"),
    ])
    c.executemany("INSERT INTO StringIds VALUES (?,?)", [
        (1, "cudaLaunchKernel"), (2, "cudaMemcpyAsync"),
        (3, "cudaDeviceSynchronize"), (4, "q0_spin_kernel(unsigned long long)"),
    ])
    identity = dict(experiment_id="exposedpath-q0", wmpc_id="q0-controlled",
                    run_id=case_run_id, run_role="Engineering", pass_id="Pass1",
                    repeat_id="repeat-0", request_id=CASE)
    def nvtx(start, end, kind, tid=TID, label=None):
        payload = dict(identity, kind=kind,
                       phase="full_request" if kind == "request" else "decode")
        if label:
            payload["callsite_id"] = label
        if kind == "sync":
            payload.update(sync_origin="q0_controlled", sync_ordinal=0)
        c.execute("INSERT INTO NVTX_EVENTS(start,end,eventType,text,globalTid) VALUES (?,?,?,?,?)",
                  (start, end, 59, "EXPOSEDPATH_JSON_V1:" + json.dumps(payload), tid))
    nvtx(10, 120, "request")
    nvtx(10, 120, "phase")
    nvtx(19, 23, "marker", WORKER, "KERNEL_A")
    nvtx(24, 28, "marker", TID, "MEMCPY_B")
    nvtx(30, 111, "sync", TID, "S_DEVICE")
    for _ in range(marker_count):
        payload = dict(arm=arm, cuda_module_loading_mode="LAZY", warmup_host_ns=10_000_000
                       if arm == "B_WARMUP" else 0,
                       warmup_interleave="OUTSIDE_CAPTURE_RANGE",
                       warmup_status="PASS" if arm == "B_WARMUP" else "NOT_APPLICABLE")
        c.execute("INSERT INTO NVTX_EVENTS(start,end,eventType,text,globalTid) VALUES (?,?,?,?,?)",
                  (marker_start, None, marker_type, PREFIX + json.dumps(payload), TID))
    c.executemany("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?,?,?,?,?,?,?,?)", [
        (20, 22, 0, WORKER, 1, 1, 0, None), (25, 27, 0, TID, 2, 2, 0, None),
        (31, 110, 0, TID, 3, 3, 0, None),
    ])
    kernel = (40, 100) if kernel_terminal else (40, 70)
    copy = (50, 80) if kernel_terminal else (50, 100) if overlap else (75, 100)
    c.execute("INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
              (*kernel, 0, 1, None, 13, 999 if corrupt_corr else 1, PID, 4, 4, None, None))
    c.execute("INSERT INTO CUPTI_ACTIVITY_KIND_MEMCPY VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (*copy, 0, 1, None, 14, 2, PID, BYTES, 1, 1, 2, None))
    c.execute("INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
              (32, 109, 0, 1, None, 4294967295, 3, PID, None, 1, 4294967295, None))
    c.execute("INSERT INTO ENUM_CUPTI_SYNC_TYPE VALUES (1,'CONTEXT_SYNCHRONIZE','Context sync')")
    c.executemany("INSERT INTO ENUM_CUPTI_STREAM_TYPE VALUES (?,?,?)", [
        (1, "CUPTI_ACTIVITY_STREAM_CREATE_FLAG_DEFAULT", "Default"),
        (2, "CUPTI_ACTIVITY_STREAM_CREATE_FLAG_NON_BLOCKING", "Non-blocking"),
        (3, "CUPTI_ACTIVITY_STREAM_CREATE_FLAG_NULL", "Null"),
    ])
    c.execute("INSERT INTO TARGET_INFO_CUDA_CONTEXT_INFO VALUES (0,0,0,100,0,1,NULL,0)")
    c.executemany("INSERT INTO TARGET_INFO_CUDA_STREAM VALUES (?,?,?,?,?,?,?)",
                  [(13, 0, 0, 100, 1, 0, 2), (14, 0, 0, 100, 1, 0, 2)])
    c.execute("INSERT INTO TARGET_INFO_GPU VALUES (0,'NVIDIA GeForce RTX 4090')")
    c.commit()
    c.close()


def _inputs(tmp_path):
    binary, nsys = tmp_path / "q0.exe", tmp_path / "nsys.exe"
    binary.write_bytes(b"frozen-native-binary")
    nsys.write_bytes(b"nsys")
    return binary, nsys


def _runner(seen, *, a_positive=False, b_kernel_terminal=False, a_marker_count=1):
    def run(argv, **kwargs):
        argv = list(argv)
        seen.append(argv)
        if argv[1] == "profile":
            assert kwargs["env"]["CUDA_VISIBLE_DEVICES"] == "GPU-ABC"
            Path(argv[argv.index("-o") + 1]).with_suffix(".nsys-rep").write_bytes(b"raw")
            return subprocess.CompletedProcess(argv, 0, "no application stdout", "")
        assert argv[1] == "export"
        output = Path(argv[argv.index("--output") + 1])
        is_b = "arm-b-warmup" in str(output)
        case_run_id = f"{RUN_ID}.{'b' if is_b else 'a'}.{CASE.lower()}"
        _fixture(output, case_run_id, "B_WARMUP" if is_b else "A_PRIME_NO_WARMUP",
                 overlap=True if is_b else a_positive, kernel_terminal=b_kernel_terminal if is_b else False,
                 marker_count=1 if is_b else a_marker_count)
        return subprocess.CompletedProcess(argv, 0, "exported", "")
    return run


def _run(tmp_path, **options):
    binary, nsys = _inputs(tmp_path)
    seen = []
    receipt = _m().run_kernel_memop_h2d_warmup_pair_diagnostic(
        tmp_path / "pair", binary, nsys, run_id=RUN_ID, cuda_visible_device="GPU-ABC",
        implementation_commit=IMPL, process_runner=_runner(seen, **options),
        environment_probe=lambda *_: _environment())
    return json.loads(receipt.read_text()), seen


def test_native_pair_uses_formal_default_path_not_size_diagnostic(tmp_path):
    assert importlib.util.find_spec(MODULE) is not None, "missing formal-shape pair runner"
    m = _m()
    a = m.build_pair_arm_argv(tmp_path / "nsys", tmp_path / "q0", m.ARM_A, tmp_path / "a", RUN_ID)
    b = m.build_pair_arm_argv(tmp_path / "nsys", tmp_path / "q0", m.ARM_B, tmp_path / "a", RUN_ID)
    assert a[9:] == ["--case", CASE, "--run-id", RUN_ID]
    assert b[:-1] == a and b[-1] == "--diagnostic-warmup-kernel"
    assert not any("bytes" in x or "kernel-ms" in x or "d2h" in x for x in a)


@pytest.mark.parametrize("a,b,terminal,valid,expected", [
    (0, 1, "MEMCPY_B", True, "AMENDMENT_REVIEW_ELIGIBLE"),
    (0, 1, "KERNEL_A", True, "TERMINAL_MISMATCH_STOP"),
    (0, 0, "MEMCPY_B", True, "NO_OVERLAP_STOP"),
    (1, 1, "MEMCPY_B", True, "CONTROL_OVERLAP_REVIEW"),
    (1, 0, "KERNEL_A", True, "CONTROL_OVERLAP_REVIEW"),
    (0, 1, "MEMCPY_B", False, "INVALID_STOP"),
])
def test_outcome_matrix(a, b, terminal, valid, expected):
    assert _m().classify_pair_outcome(overlap_a_ns=a, overlap_b_ns=b,
        b_terminal_label=terminal, b_terminal_kind="MEMOP" if terminal == "MEMCPY_B" else "KERNEL",
        arms_valid=valid) == expected


def test_real_canonical_s_pipeline_records_wait_set_and_terminal(tmp_path):
    receipt, seen = _run(tmp_path)
    assert receipt["q0_status"] == "NOT_RUN" and receipt["gate6_verdict"] == "FAIL"
    assert receipt["pair_interpretation"]["outcome"] == "AMENDMENT_REVIEW_ELIGIBLE"
    assert receipt["research_eligibility"]["formal_evidence"] is False
    assert [x[1] for x in seen] == ["profile", "export", "profile", "export"]
    assert len(receipt["arms"]) == 2
    for arm in receipt["arms"]:
        assert arm["semantics"]["validity"] == "VALID_NONEMPTY"
        assert arm["semantics"]["wait_set_activity_labels"] == ["KERNEL_A", "MEMCPY_B"]
        assert arm["semantics"]["terminal_label"] == "MEMCPY_B"
        assert arm["semantics"]["terminal_kind"] == "MEMOP"
        assert arm["semantics"]["terminal_activity_kind"] == "MEMCPY"
        assert arm["warmup"]["warmup_marker_source"]["event_type"] == 34
        assert arm["lineage"]["canonical_manifest"]["sha256"]
        assert arm["lineage"]["s_manifest"]["sha256"]
        assert arm["measured"]["h2d_device_interval"]["bytes"] == BYTES
        assert {item["flag"] for item in arm["stream_provenance"].values()} == {2}
        assert {item["process_id"] for item in arm["stream_provenance"].values()} == {100}
        assert {
            item["enum_name"] for item in arm["stream_provenance"].values()
        } == {"CUPTI_ACTIVITY_STREAM_CREATE_FLAG_NON_BLOCKING"}
    assert receipt["arms"][0]["measured"]["overlap_ns"] == 0
    assert receipt["arms"][1]["measured"]["overlap_ns"] == 20
    assert not list((tmp_path / "pair").rglob("ab_manifest.json"))
    plan = json.loads((tmp_path / "pair" / "pair_plan.json").read_text())
    assert plan["outcome_policy"]["AMENDMENT_REVIEW_ELIGIBLE"]["changes_gate6_or_q0"] is False
    assert plan["construction"]["h2d_size_bytes"] == BYTES
    assert plan["prior_run_disposition"]["disposition"] == (
        "INVALID_ANALYZER_STREAM_FLAG_ASSUMPTION"
    )
    assert plan["prior_run_disposition"]["rerun_allowed"] is False


def test_valid_kernel_terminal_is_structure_stop_not_invalid_evidence(tmp_path):
    receipt, _ = _run(tmp_path, b_kernel_terminal=True)
    assert receipt["pair_interpretation"]["outcome"] == "TERMINAL_MISMATCH_STOP"
    assert receipt["pair_interpretation"]["arms_valid"] is True
    assert receipt["arms"][1]["semantics"]["terminal_label"] == "KERNEL_A"


def test_control_overlap_has_review_precedence(tmp_path):
    receipt, _ = _run(tmp_path, a_positive=True, b_kernel_terminal=True)
    assert receipt["pair_interpretation"]["outcome"] == "CONTROL_OVERLAP_REVIEW"


def test_invalid_first_arm_stops_before_b_and_writes_invalid_receipt(tmp_path):
    receipt, seen = _run(tmp_path, a_marker_count=0)
    assert receipt["pair_interpretation"]["outcome"] == "INVALID_STOP"
    assert [x[1] for x in seen] == ["profile", "export"]
    assert receipt["failed_arm"] == "A_PRIME_NO_WARMUP"
    assert not (tmp_path / "pair" / "arm-b-warmup").exists()


@pytest.mark.parametrize("options", [
    {"marker_count": 0}, {"marker_count": 2}, {"marker_type": 59},
    {"marker_start": 15}, {"corrupt_corr": True},
])
def test_analysis_fails_closed_on_missing_duplicate_range_inside_request_or_mapping(tmp_path, options):
    m = _m()
    path = tmp_path / "trace.sqlite"
    identity = f"{RUN_ID}.a.{CASE.lower()}"
    _fixture(path, identity, m.ARM_A, **options)
    raw = tmp_path / "trace.nsys-rep"
    raw.write_bytes(b"raw")
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(m.KernelMemopH2DWarmupDiagnosticError):
        m.analyze_arm_evidence(path, raw, tmp_path / "analysis", arm=m.ARM_A,
            case_run_id=identity, cuda_visible_device="GPU-ABC", nsys_version="2026.2.1.210")
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_scope_rejects_old_d2h_run_identity_before_process_launch(tmp_path):
    binary, nsys = _inputs(tmp_path)
    with pytest.raises(_m().KernelMemopH2DWarmupDiagnosticError):
        _m().run_kernel_memop_h2d_warmup_pair_diagnostic(
            tmp_path / "pair", binary, nsys,
            run_id="q0-win-4090-20260918-kernel-memop-d2h-diag-64m-10ms-warmup-02",
            cuda_visible_device="GPU-ABC", implementation_commit=IMPL,
            process_runner=lambda *_: pytest.fail("must not execute"))


def test_scope_rejects_superseded_formalshape_warmup_01_before_process_launch(tmp_path):
    binary, nsys = _inputs(tmp_path)
    with pytest.raises(_m().KernelMemopH2DWarmupDiagnosticError, match="warmup-02"):
        _m().run_kernel_memop_h2d_warmup_pair_diagnostic(
            tmp_path / "pair", binary, nsys,
            run_id="q0-win-4090-20260918-kernel-memop-h2d-formalshape-warmup-01",
            cuda_visible_device="GPU-ABC", implementation_commit=IMPL,
            process_runner=lambda *_: pytest.fail("must not execute"))


def test_scope_rejects_any_formalshape_run_id_other_than_warmup_02(tmp_path):
    binary, nsys = _inputs(tmp_path)
    with pytest.raises(_m().KernelMemopH2DWarmupDiagnosticError, match="warmup-02"):
        _m().run_kernel_memop_h2d_warmup_pair_diagnostic(
            tmp_path / "pair", binary, nsys,
            run_id="q0-win-4090-20260918-kernel-memop-h2d-formalshape-warmup-03",
            cuda_visible_device="GPU-ABC", implementation_commit=IMPL,
            process_runner=lambda *_: pytest.fail("must not execute"))


def test_stream_provenance_ignores_other_process_same_context_stream_decoy(tmp_path):
    m = _m()
    path = tmp_path / "trace.sqlite"
    identity = f"{RUN_ID}.b.{CASE.lower()}"
    _fixture(path, identity, m.ARM_B)
    with sqlite3.connect(path) as connection:
        connection.execute(
            "INSERT INTO TARGET_INFO_CUDA_STREAM VALUES (?,?,?,?,?,?,?)",
            (13, 0, 0, 999, 1, 0, 1),
        )
    raw = tmp_path / "trace.nsys-rep"
    raw.write_bytes(b"raw")
    result = m.analyze_arm_evidence(
        path, raw, tmp_path / "analysis", arm=m.ARM_B,
        case_run_id=identity, cuda_visible_device="GPU-ABC",
        nsys_version="2026.2.1.210",
    )
    assert result["stream_provenance"]["KERNEL_A"] == {
        "process_id": 100,
        "stream_id": 13,
        "context_id": 1,
        "flag": 2,
        "enum_name": "CUPTI_ACTIVITY_STREAM_CREATE_FLAG_NON_BLOCKING",
    }


@pytest.mark.parametrize("sql", [
    "DELETE FROM CUPTI_ACTIVITY_KIND_SYNCHRONIZATION",
    "UPDATE CUPTI_ACTIVITY_KIND_MEMCPY SET bytes=67108864",
    "UPDATE CUPTI_ACTIVITY_KIND_MEMCPY SET copyKind=2",
    "UPDATE TARGET_INFO_CUDA_STREAM SET flag=0",
    "UPDATE TARGET_INFO_CUDA_STREAM SET flag=1",
    "UPDATE ENUM_CUPTI_STREAM_TYPE SET name='WRONG' WHERE id=2",
    "DELETE FROM ENUM_CUPTI_STREAM_TYPE WHERE id=2",
    "INSERT INTO ENUM_CUPTI_STREAM_TYPE VALUES (2,'CUPTI_ACTIVITY_STREAM_CREATE_FLAG_NON_BLOCKING','Duplicate')",
    "DROP TABLE ENUM_CUPTI_STREAM_TYPE",
    "UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET end=100",
    "UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET nameId=2 WHERE correlationId=1",
])
def test_analysis_rejects_invalid_sync_workload_stream_terminal_or_runtime(tmp_path, sql):
    m = _m()
    path = tmp_path / "trace.sqlite"
    identity = f"{RUN_ID}.b.{CASE.lower()}"
    _fixture(path, identity, m.ARM_B)
    with sqlite3.connect(path) as connection:
        connection.execute(sql)
    raw = tmp_path / "trace.nsys-rep"
    raw.write_bytes(b"raw")
    with pytest.raises((m.KernelMemopH2DWarmupDiagnosticError, ValueError)):
        m.analyze_arm_evidence(path, raw, tmp_path / "analysis", arm=m.ARM_B,
            case_run_id=identity, cuda_visible_device="GPU-ABC", nsys_version="2026.2.1.210")


@pytest.mark.parametrize("invalid", [False, True])
def test_cli_reports_native_shape_semantics_and_fail_closed_without_evaluator(
        monkeypatch, tmp_path, capsys, invalid):
    from exposedpath_v141 import cli
    m = _m()
    binary, nsys = _inputs(tmp_path)
    seen = []
    native_runner = m.run_kernel_memop_h2d_warmup_pair_diagnostic
    def offline_runner(*args, **kwargs):
        return native_runner(*args, **kwargs,
            process_runner=_runner(seen, a_marker_count=0 if invalid else 1),
            environment_probe=lambda *_: _environment())
    monkeypatch.setattr(cli, "run_kernel_memop_h2d_warmup_pair_diagnostic", offline_runner)
    monkeypatch.setattr(cli, "analyze_ab", lambda *_: pytest.fail("A/B forbidden"))
    monkeypatch.setattr(cli, "run_real_q0_case", lambda *_: pytest.fail("evaluator forbidden"))
    status = cli.main([
        "run-q0-kernel-memop-h2d-formalshape-warmup-diagnostic",
        "--output-dir", str(tmp_path / "pair"), "--binary", str(binary),
        "--nsys", str(nsys), "--run-id", RUN_ID,
        "--cuda-visible-device", "GPU-ABC", "--implementation-commit", IMPL,
        "--baseline-reference-commit", m.BASELINE_REFERENCE_COMMIT,
    ])
    output = capsys.readouterr().out
    assert status == (1 if invalid else 0)
    assert "q0_execution_status: NOT_RUN" in output
    assert "gate6_verdict: FAIL" in output
    assert "INVALID_ANALYZER_STREAM_FLAG_ASSUMPTION" in output
    assert ("INVALID_STOP" if invalid else "AMENDMENT_REVIEW_ELIGIBLE") in output
    if not invalid:
        assert "terminal=MEMCPY_B/MEMOP" in output
        assert "launch_api_ns=2" in output
    assert [x[1] for x in seen] == (["profile", "export"] if invalid else
                                  ["profile", "export", "profile", "export"])
