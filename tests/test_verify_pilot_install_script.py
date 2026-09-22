"""Behavioral regression tests for verify_pilot_install.ps1."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "verify_pilot_install.ps1"


def _powershell_exe() -> str:
    found = shutil.which("powershell")
    if found:
        return found
    system_root = os.environ.get("SystemRoot", r"C:\Windows")
    candidate = (
        Path(system_root)
        / "System32"
        / "WindowsPowerShell"
        / "v1.0"
        / "powershell.exe"
    )
    if candidate.is_file():
        return str(candidate)
    pytest.skip("Windows PowerShell is unavailable on this host")


def test_verify_script_imports_required_packages_with_selected_python():
    """The selected interpreter imports every package and reports its version."""
    completed = subprocess.run(
        [
            _powershell_exe(),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(SCRIPT),
            "-SkipTests",
            "-PythonExe",
            sys.executable,
        ],
        cwd=SCRIPT.parent.parent,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=60,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    for package_name in ("torch", "transformers", "yaml", "exposedpath"):
        assert f"{package_name}: import OK; version=" in completed.stdout
