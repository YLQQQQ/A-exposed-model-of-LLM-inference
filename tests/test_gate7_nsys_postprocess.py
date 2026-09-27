"""CPU-only behavioral tests for Gate7 Nsight SQLite post-processing."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import scripts.gate7_nsys_postprocess as postprocess
from scripts.gate7_nsys_postprocess import run_postprocess, wait_for_rep_ready


FAKE_EXPORTER = r'''
import os, sqlite3, sys, time
from pathlib import Path

assert sys.argv[1:5] == ["export", "--type", "sqlite", "--output"]
output = Path(sys.argv[5])
rep = Path(sys.argv[6])
attempt = 1 if "attempt1" in output.name else 2
behavior = os.environ[f"FAKE_EXPORT_ATTEMPT{attempt}"]
if behavior == "timeout":
    Path(os.environ["FAKE_EXPORT_PID_FILE"]).write_text(str(os.getpid()))
    output.write_bytes(b"partial")
    time.sleep(30)
elif behavior == "nonzero":
    output.write_bytes(b"partial")
    raise SystemExit(7)
elif behavior == "change_rep":
    rep.write_bytes(b"changed")
    raise SystemExit(7)
elif behavior == "empty":
    output.touch()
elif behavior == "bad_schema":
    with sqlite3.connect(output) as db:
        db.execute("CREATE TABLE TRACE_EVENTS (id INTEGER)")
elif behavior == "bad_integrity":
    output.write_bytes(b"not a database")
else:
    assert behavior == "success"
    with sqlite3.connect(output) as db:
        db.executescript("""
            CREATE TABLE META_DATA_CAPTURE (name TEXT, value TEXT);
            CREATE TABLE META_DATA_EXPORT (name TEXT, value TEXT);
            CREATE TABLE StringIds (id INTEGER, value TEXT);
            CREATE TABLE NVTX_EVENTS (start INTEGER, end INTEGER, text TEXT, textId INTEGER);
            CREATE TABLE CUPTI_ACTIVITY_KIND_RUNTIME
                (start INTEGER, end INTEGER, correlationId INTEGER, nameId INTEGER);
            CREATE TABLE CUPTI_ACTIVITY_KIND_SYNCHRONIZATION
                (start INTEGER, end INTEGER, correlationId INTEGER);
            CREATE TABLE CUPTI_ACTIVITY_KIND_KERNEL
                (start INTEGER, end INTEGER, correlationId INTEGER);
            CREATE TABLE TARGET_INFO_CUDA_CONTEXT_INFO (contextId INTEGER, deviceId INTEGER);
            CREATE TABLE TARGET_INFO_CUDA_STREAM (streamId INTEGER, contextId INTEGER);
            CREATE TABLE TARGET_INFO_GPU (id INTEGER, name TEXT);
            CREATE TABLE DIAGNOSTIC_EVENT
                (timestamp INTEGER, source TEXT, severity TEXT, text TEXT);
        """)
print(f"attempt={attempt} behavior={behavior}")
print(f"stderr attempt={attempt}", file=sys.stderr)
'''


def _run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *behaviors: str,
         nsys_exe: str | None = None, **options):
    rep = tmp_path / "pass1_profile.nsys-rep"
    rep.write_bytes(b"immutable rep")
    fake = tmp_path / "fake_exporter.py"
    fake.write_text(FAKE_EXPORTER, encoding="utf-8")
    canonical = tmp_path / "pass1_profile.sqlite"
    report_path = tmp_path / "postprocess_report.json"
    pid_file = tmp_path / "export_pid.txt"
    monkeypatch.setenv("FAKE_EXPORT_PID_FILE", str(pid_file))
    for index, behavior in enumerate(behaviors, 1):
        monkeypatch.setenv(f"FAKE_EXPORT_ATTEMPT{index}", behavior)
    # Windows venv python.exe can launch another interpreter process. Use the
    # base executable in place so Popen.pid is the exporter PID (also on timeout).
    # Unlike the copied-executable test, this needs no PYTHONHOME/PATH relocation.
    direct_interpreter = sys._base_executable if os.name == "nt" else sys.executable
    result = run_postprocess(
        nsys_exe=nsys_exe or direct_interpreter,
        rep_path=rep,
        canonical_path=canonical,
        report_path=report_path,
        export_prefix=[str(fake)],
        export_timeout_seconds=0.8,
        readiness_timeout_seconds=0.15,
        retry_readiness_timeout_seconds=0.15,
        poll_interval_seconds=0.01,
        stable_samples=1,
        **options,
    )
    assert json.loads(report_path.read_text(encoding="utf-8")) == result
    return result, canonical, rep, pid_file


def test_single_attempt_diagnostic_policy_never_retries(tmp_path, monkeypatch):
    result, canonical, _, _ = _run(tmp_path, monkeypatch, 'nonzero', 'success', max_attempts=1)
    assert result['status'] == 'BLOCKED_BY_NSYS'
    assert result['attempt_count'] == 1
    assert not canonical.exists()
    assert not (tmp_path/'pass1_profile.export_attempt2.sqlite').exists()


@pytest.mark.parametrize("condition", ["missing", "empty"])
def test_rep_missing_or_empty_blocks_before_export(tmp_path, condition):
    rep = tmp_path / "trace.nsys-rep"
    if condition == "empty":
        rep.touch()
    with pytest.raises(ValueError):
        wait_for_rep_ready(rep, timeout_seconds=0.03, poll_interval_seconds=0.01,
                           stable_samples=1)


def test_rep_readiness_timeout_blocks(tmp_path):
    rep = tmp_path / "trace.nsys-rep"
    rep.write_bytes(b"ready")
    with pytest.raises(TimeoutError):
        wait_for_rep_ready(rep, timeout_seconds=0.02, poll_interval_seconds=0.01,
                           stable_samples=10)


def test_first_attempt_success_promotes_without_retry(tmp_path, monkeypatch):
    result, canonical, rep, _ = _run(tmp_path, monkeypatch, "success")
    digest = hashlib.sha256(canonical.read_bytes()).hexdigest()
    assert result["status"] == "PASS"
    assert result["attempt_count"] == 1
    assert result["successful_attempt"] == 1
    assert result["canonical_sqlite_sha256"] == digest
    assert result["attempts"][0]["sqlite_sha256"] == digest
    assert result["attempts"][0]["rep_sha256"] == hashlib.sha256(rep.read_bytes()).hexdigest()
    assert result["analyzer_allowed"] is True


def test_export_and_report_paths_with_spaces_are_literal(tmp_path, monkeypatch):
    spaced = tmp_path / "Gate 7 smoke evidence"
    spaced.mkdir()
    result, canonical, _, _ = _run(spaced, monkeypatch, "success")
    assert result["status"] == "PASS"
    assert canonical.is_file()
    assert "Gate 7 smoke evidence" in result["attempts"][0]["output_path"]


def test_executable_rep_and_output_paths_with_spaces_are_argv_safe(tmp_path, monkeypatch):
    spaced = tmp_path / "Nsight Systems 2026.2.1"
    spaced.mkdir()
    executable = spaced / ("nsys.exe" if os.name == "nt" else "nsys")
    if os.name == "nt":
        base_executable = Path(getattr(sys, "_base_executable", sys.executable))
        shutil.copy2(base_executable, executable)
        monkeypatch.setenv("PYTHONHOME", sys.base_prefix)
        monkeypatch.setenv("PATH", str(base_executable.parent) + os.pathsep + os.environ["PATH"])
    else:
        executable.symlink_to(sys.executable)
    result, canonical, rep, _ = _run(
        spaced, monkeypatch, "success", nsys_exe=str(executable),
    )
    assert result["status"] == "PASS"
    assert canonical.is_file()
    assert result["attempts"][0]["argv"][0] == str(executable)
    assert result["attempts"][0]["argv"][-1] == str(rep)
    assert result["attempts"][0]["argv"][-2] == result["attempts"][0]["output_path"]
    assert "attempt=1 behavior=success" in Path(result["attempts"][0]["stdout_path"]).read_text()
    assert "stderr attempt=1" in Path(result["attempts"][0]["stderr_path"]).read_text()


def test_timeout_terminates_only_recorded_pid_then_retry_succeeds(tmp_path, monkeypatch):
    original_popen = postprocess.subprocess.Popen
    processes = []

    def start_after_previous_exit(*args, **kwargs):
        if processes:
            assert processes[-1].poll() is not None, "Retry started before exporter exit"
        process = original_popen(*args, **kwargs)
        processes.append(process)
        return process

    monkeypatch.setattr(postprocess.subprocess, "Popen", start_after_previous_exit)
    result, canonical, _, pid_file = _run(tmp_path, monkeypatch, "timeout", "success")
    first, second = result["attempts"]
    assert result["status"] == "PASS"
    assert result["attempt_count"] == 2
    assert len(processes) == 2
    assert first["timed_out"] is True
    assert first["pid"] == int(pid_file.read_text())
    assert first["terminated_pid"] == first["pid"]
    assert first["process_exited"] is True
    assert first["output_path"] != second["output_path"]
    assert Path(first["output_path"]).read_bytes() == b"partial"
    assert result["retry_readiness"]["sha256"] == result["rep_sha256"]
    assert result["readiness_timeout_seconds"] == 0.15
    assert result["retry_readiness_timeout_seconds"] == 0.15
    assert canonical.is_file()
    assert result["successful_attempt"] == 2


def test_two_timeouts_block_analyzer_and_preserve_partials(tmp_path, monkeypatch):
    result, canonical, _, _ = _run(tmp_path, monkeypatch, "timeout", "timeout")
    assert result["status"] == "BLOCKED_BY_NSYS"
    assert result["attempt_count"] == 2
    assert all(attempt["timed_out"] for attempt in result["attempts"])
    assert all(Path(attempt["output_path"]).exists() for attempt in result["attempts"])
    assert result["analyzer_allowed"] is False
    assert not canonical.exists()


def test_nonzero_then_success_records_both_attempts(tmp_path, monkeypatch):
    result, canonical, _, _ = _run(tmp_path, monkeypatch, "nonzero", "success")
    assert result["status"] == "PASS"
    assert [attempt["exit_code"] for attempt in result["attempts"]] == [7, 0]
    assert result["attempts"][0]["sqlite_size"] == len(b"partial")
    assert result["attempts"][0]["sqlite_sha256"]
    assert result["successful_attempt"] == 2
    assert canonical.is_file()


def test_existing_canonical_fails_closed_without_export(tmp_path, monkeypatch):
    canonical = tmp_path / "pass1_profile.sqlite"
    canonical.write_bytes(b"existing")
    result, _, _, _ = _run(tmp_path, monkeypatch, "success")
    assert result["status"] == "BLOCKED_BY_NSYS"
    assert result["attempt_count"] == 0
    assert result["analyzer_allowed"] is False
    assert canonical.read_bytes() == b"existing"


def test_rep_hash_change_between_attempts_blocks(tmp_path, monkeypatch):
    result, canonical, _, _ = _run(tmp_path, monkeypatch, "change_rep", "success")
    assert result["status"] == "BLOCKED_BY_NSYS"
    assert result["attempt_count"] == 1
    assert "SHA256" in result["error"]
    assert not canonical.exists()


@pytest.mark.parametrize("behavior", ["empty", "bad_integrity", "bad_schema"])
def test_invalid_sqlite_never_promoted(tmp_path, monkeypatch, behavior):
    result, canonical, _, _ = _run(tmp_path, monkeypatch, behavior, behavior)
    assert result["status"] == "BLOCKED_BY_NSYS"
    assert result["attempt_count"] == 2
    assert all(attempt["validation_issues"] for attempt in result["attempts"])
    assert result["analyzer_allowed"] is False
    assert not canonical.exists()


def test_first_partial_never_becomes_canonical(tmp_path, monkeypatch):
    result, canonical, _, _ = _run(tmp_path, monkeypatch, "nonzero", "success")
    assert Path(result["attempts"][0]["output_path"]).read_bytes() == b"partial"
    assert canonical.read_bytes() != b"partial"


def test_cli_missing_rep_exits_nonzero_and_writes_blocked_report(tmp_path):
    report_path = tmp_path / "postprocess_report.json"
    command = [
        sys.executable,
        str(Path(__file__).resolve().parents[1] / "scripts" / "gate7_nsys_postprocess.py"),
        "--nsys", sys.executable,
        "--rep", str(tmp_path / "missing.nsys-rep"),
        "--canonical-sqlite", str(tmp_path / "pass1_profile.sqlite"),
        "--report", str(report_path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=10)
    assert completed.returncode == 1
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "BLOCKED_BY_NSYS"
    assert report["attempt_count"] == 0
    assert report["analyzer_allowed"] is False


def test_unreadable_partial_metadata_preserves_attempt_provenance(tmp_path, monkeypatch):
    original_sha256 = postprocess._sha256

    def read_with_locked_attempt(path):
        if "export_attempt1.sqlite" in str(path):
            raise PermissionError("simulated locked attempt output")
        return original_sha256(path)

    monkeypatch.setattr(postprocess, "_sha256", read_with_locked_attempt)
    result, canonical, _, _ = _run(tmp_path, monkeypatch, "success", "success")
    assert result["status"] == "PASS"
    assert result["attempt_count"] == 2
    first = result["attempts"][0]
    assert first["pid"] is not None
    assert first["process_exited"] is True
    assert first["exit_code"] == 0
    assert any("metadata" in issue.lower() for issue in first["validation_issues"])
    assert canonical.is_file()


def test_sqlite_validation_io_error_preserves_attempt_provenance(tmp_path, monkeypatch):
    original_validate = postprocess.validate_sqlite

    def validate_with_locked_attempt(path):
        if "export_attempt1.sqlite" in str(path):
            raise PermissionError("simulated validation lock")
        return original_validate(path)

    monkeypatch.setattr(postprocess, "validate_sqlite", validate_with_locked_attempt)
    result, canonical, _, _ = _run(tmp_path, monkeypatch, "success", "success")
    assert result["status"] == "PASS"
    assert result["attempt_count"] == 2
    first = result["attempts"][0]
    assert first["pid"] is not None
    assert first["process_exited"] is True
    assert first["exit_code"] == 0
    assert any("validation" in issue.lower() for issue in first["validation_issues"])
    assert canonical.is_file()


def test_promotion_hash_failure_does_not_leave_canonical(tmp_path, monkeypatch):
    original_sha256 = postprocess._sha256

    def corrupt_canonical_hash(path):
        if Path(path).name == "pass1_profile.sqlite":
            return "0" * 64
        return original_sha256(path)

    monkeypatch.setattr(postprocess, "_sha256", corrupt_canonical_hash)
    result, canonical, _, _ = _run(tmp_path, monkeypatch, "success")
    assert result["status"] == "BLOCKED_BY_NSYS"
    assert result["analyzer_allowed"] is False
    assert not canonical.exists()
    assert Path(result["attempts"][0]["output_path"]).is_file()
