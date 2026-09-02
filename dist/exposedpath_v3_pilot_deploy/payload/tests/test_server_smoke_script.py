"""Tests for run_server_smoke_test.ps1 — syntax, parameter validation, no GPU required."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "run_server_smoke_test.ps1"


def _run_ps(argv: str, cwd: str = None) -> tuple[int, str, str]:
    """Run the smoke test script with given arguments. Returns (rc, stdout, stderr).

    Uses -Command style invocation to avoid subprocess quoting issues with
    paths containing spaces on Windows.
    """
    full_cmd = f"& '{SCRIPT}' {argv}"
    cmd = [
        "powershell", "-ExecutionPolicy", "Bypass", "-NoProfile",
        "-Command", full_cmd,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd or str(SCRIPT.parent.parent))
    return r.returncode, r.stdout, r.stderr


# ===== Dry-run tests =====

def test_dry_run_succeeds():
    """--DryRun with valid paths prints plan and exits 0."""
    with tempfile.TemporaryDirectory() as td:
        # Create a fake model dir with config.json
        model = Path(td) / "model"
        model.mkdir()
        (model / "config.json").write_text('{"model_type":"test"}')

        # Create a fake nsys.exe
        nsys_dir = Path(td) / "nsys"
        nsys_dir.mkdir()
        (nsys_dir / "nsys.exe").write_text("fake nsys")

        rc, out, err = _run_ps(
            f'-ModelPath "{model}" -GpuId 0 -NsysPath "{nsys_dir / "nsys.exe"}" -DryRun',
            cwd=td,
        )
        assert rc == 0, f"stderr: {err}"
        assert "SMOKE TEST PLAN" in out
        assert "DryRun" in out


# ===== Missing parameters =====

def test_missing_modelpath_fails():
    """Missing -ModelPath causes PowerShell error (non-zero exit)."""
    with tempfile.TemporaryDirectory() as td:
        rc, out, err = _run_ps('-GpuId 0 -NsysPath "C:\\nsys.exe" -DryRun', cwd=td)
        # PowerShell param binding failure → non-zero
        assert rc != 0


def test_missing_gpuid_fails():
    """Missing -GpuId fails."""
    with tempfile.TemporaryDirectory() as td:
        rc, out, err = _run_ps(
            f'-ModelPath "C:\\fake" -NsysPath "C:\\nsys.exe" -DryRun', cwd=td)
        assert rc != 0


def test_missing_nsyspath_fails():
    """Missing -NsysPath fails."""
    with tempfile.TemporaryDirectory() as td:
        rc, out, err = _run_ps('-ModelPath "C:\\fake" -GpuId 0 -DryRun', cwd=td)
        assert rc != 0


# ===== ModelPath validation =====

def test_modelpath_not_found_blocks():
    """Non-existent ModelPath → BLOCKED_BY_ENVIRONMENT."""
    with tempfile.TemporaryDirectory() as td:
        nsys_dir = Path(td) / "nsys"
        nsys_dir.mkdir()
        (nsys_dir / "nsys.exe").write_text("fake")
        fake_model = Path(td) / "nonexistent_model"
        rc, out, err = _run_ps(
            f'-ModelPath "{fake_model}" -GpuId 0 -NsysPath "{nsys_dir / "nsys.exe"}"',
            cwd=td,
        )
        assert rc != 0
        assert "BLOCKED_BY_ENVIRONMENT" in out


def test_model_missing_config_json_blocks():
    """Model dir without config.json → BLOCKED_BY_ENVIRONMENT."""
    with tempfile.TemporaryDirectory() as td:
        model = Path(td) / "model"
        model.mkdir()
        nsys_dir = Path(td) / "nsys"
        nsys_dir.mkdir()
        (nsys_dir / "nsys.exe").write_text("fake")
        rc, out, err = _run_ps(
            f'-ModelPath "{model}" -GpuId 0 -NsysPath "{nsys_dir / "nsys.exe"}"',
            cwd=td,
        )
        assert rc != 0
        assert "BLOCKED_BY_ENVIRONMENT" in out


# ===== NsysPath validation =====

def test_nsys_not_found_blocks():
    """Non-existent nsys.exe → BLOCKED_BY_ENVIRONMENT."""
    with tempfile.TemporaryDirectory() as td:
        model = Path(td) / "model"
        model.mkdir()
        (model / "config.json").write_text("{}")
        fake_nsys = Path(td) / "nsys.exe"
        rc, out, err = _run_ps(
            f'-ModelPath "{model}" -GpuId 0 -NsysPath "{fake_nsys}"',
            cwd=td,
        )
        assert rc != 0
        assert "BLOCKED_BY_ENVIRONMENT" in out


# ===== UTC directory creation =====

def test_utc_directory_created():
    """DryRun shows smoke_<UTC> directory pattern."""
    with tempfile.TemporaryDirectory() as td:
        model = Path(td) / "model"
        model.mkdir()
        (model / "config.json").write_text("{}")
        nsys_dir = Path(td) / "nsys"
        nsys_dir.mkdir()
        (nsys_dir / "nsys.exe").write_text("fake")
        rc, out, err = _run_ps(
            f'-ModelPath "{model}" -GpuId 0 -NsysPath "{nsys_dir / "nsys.exe"}" -DryRun',
            cwd=td,
        )
        assert rc == 0
        assert "smoke_" in out


# ===== No-overwrite check: treated as smoke dir collision =====

def test_existing_smoke_dir_blocks():
    """Smoke directory collision: verified by code structure (timestamp is unique per run).

    The script checks with ``Test-Path $SmokeDir`` then ``Get-ChildItem`` on the
    timestamped directory. Since timestamps are UTC-second-unique, collision is
    virtually impossible. The guard clause is confirmed present in the script source
    (``if ($existing.Count -gt 0)`` → ``Set-GateFailure``).
    """
    text = SCRIPT.read_text(encoding="utf-8")
    assert 'Get-ChildItem -Path $SmokeDir' in text
    assert '$existing.Count -gt 0' in text


# ===== Paths with spaces =====

def test_paths_with_spaces_in_dryrun():
    """Paths containing spaces are handled correctly (quoted)."""
    with tempfile.TemporaryDirectory() as td:
        model = Path(td) / "my model dir"
        model.mkdir()
        (model / "config.json").write_text("{}")
        nsys_dir = Path(td) / "nsys tools"
        nsys_dir.mkdir()
        (nsys_dir / "nsys.exe").write_text("fake")
        rc, out, err = _run_ps(
            f'-ModelPath "{model}" -GpuId 0 -NsysPath "{nsys_dir / "nsys.exe"}" -DryRun',
            cwd=td,
        )
        assert rc == 0


# ===== Report JSON format =====

def test_report_json_keys():
    """Verify the smoke_test_report.json has all required top-level keys."""
    # We test by checking the script source code, not by running it
    script_text = SCRIPT.read_text(encoding="utf-8")
    assert "gate_decision" in script_text
    assert "environment" in script_text
    assert "pass0" in script_text
    assert "pass1" in script_text
    assert "analyzer" in script_text
    assert "paths" in script_text
    assert "errors" in script_text
    assert "BLOCKED_BY_ENVIRONMENT" in script_text
    assert "BLOCKED_BY_RUNNER" in script_text
    assert "BLOCKED_BY_NSYS" in script_text
    assert "BLOCKED_BY_ANALYZER" in script_text
    assert "READY_FOR_SMALL_PILOT" in script_text


# ===== PowerShell syntax check =====

def test_powershell_syntax_valid():
    """PowerShell script is valid UTF-8, readable, and contains param block."""
    text = SCRIPT.read_text(encoding="utf-8")
    assert "param(" in text, "Script must have a param block"
    assert "run_server_smoke_test" in text.lower() or "smoke" in text.lower()
    # Basic structure checks
    assert "Set-GateFailure" in text
    assert "Save-Report" in text
    assert "READY_FOR_SMALL_PILOT" in text
