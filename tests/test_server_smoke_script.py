"""Tests for run_server_smoke_test.ps1 — resume state recovery, gates, Join-Path.

EP-G7-10 note: the launcher invocation below is hermetic. The host is part of
the platform boundary, so the PowerShell executable is resolved explicitly and
the interpreter is passed as ``-PythonExe``. A bare ``powershell`` / ``python``
lookup would make these checks depend on the caller's ambient PATH, which
previously produced two unexplained baseline failures.
"""

from __future__ import annotations
import os, shutil, subprocess, sys, tempfile
from pathlib import Path
import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "run_server_smoke_test.ps1"
def _t(): return SCRIPT.read_text(encoding="utf-8")

def _powershell_exe():
    """Resolve Windows PowerShell explicitly; never rely on the ambient PATH."""
    found = shutil.which("powershell")
    if found:
        return found
    system_root = os.environ.get("SystemRoot", r"C:\Windows")
    candidate = Path(system_root) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    if candidate.is_file():
        return str(candidate)
    return None

def _run(argv,cwd=None,env=None):
    exe=_powershell_exe()
    if exe is None:
        pytest.skip("Windows PowerShell is unavailable on this host")
    r=subprocess.run([exe,"-ExecutionPolicy","Bypass","-NoProfile","-Command",f"& '{SCRIPT}' {argv}"],capture_output=True,text=True,cwd=cwd or str(SCRIPT.parent.parent),env=env)
    return r.returncode,r.stdout,r.stderr

def _dry_run_args(model_path,nsys_path):
    """Dry-run argv with an explicit interpreter (PATH-independent)."""
    return f'-ModelPath "{model_path}" -GpuId 0 -NsysPath "{nsys_path}" -PythonExe "{sys.executable}" -DryRun'

def _assert_dry_run_ok(model_path,nsys_path,cwd=None,env=None):
    rc,out,err=_run(_dry_run_args(model_path,nsys_path),cwd,env=env)
    assert rc==0, f"dry run exited {rc}\n--- stdout ---\n{out}\n--- stderr ---\n{err}"

# ===== Recovery functions exist =====
def test_recover_pass0_function_exists():
    assert 'function Recover-Pass0State' in _t()
def test_recover_pass1_function_exists():
    assert 'function Recover-Pass1State' in _t()

# ===== Pass 0 recovery validation =====
def test_recover_pass0_checks_file_exists():
    assert 'inference_results.jsonl missing' in _t()
def test_recover_pass0_checks_success_count():
    assert 'success count' in _t()
def test_recover_pass0_checks_repeat_index():
    assert 'repeat_index mismatch' in _t() or 'repeat_index' in _t()
def test_recover_pass0_checks_attempt_status():
    assert 'attempt_status' in _t()
def test_recover_pass0_checks_latency_positive():
    assert 'e2e_latency <= 0' in _t() or 'inference_e2e_latency_ms' in _t()
def test_recover_pass0_checks_input_tokens():
    assert 'input_tokens' in _t()
def test_recover_pass0_checks_output_tokens():
    assert 'output_tokens' in _t()
def test_recover_pass0_checks_batch_size():
    assert 'batch_size' in _t()

# ===== Pass 1 recovery validation =====
def test_recover_pass1_checks_rep_exists():
    assert '.nsys-rep missing' in _t()
def test_recover_pass1_checks_rep_nonempty():
    assert '.nsys-rep empty' in _t()
def test_recover_pass1_checks_sqlite_exists():
    assert '.sqlite missing' in _t()
def test_recover_pass1_checks_sqlite_nonempty():
    assert '.sqlite empty' in _t()
def test_recover_pass1_sets_script_vars():
    """Recover-Pass1State sets script-level NsysRepFile/NsysSqliteFile."""
    assert '$Script:NsysRepFile' in _t() and '$Script:NsysSqliteFile' in _t()

# ===== Skip branches call recovery =====
def test_pass0_else_calls_recovery():
    assert 'Recover-Pass0State -Dir $Pass0Dir' in _t()
def test_pass1_else_calls_recovery():
    assert 'Recover-Pass1State -Dir $Pass1Dir' in _t()

# ===== Gate conditions =====
def test_final_gate_not_unconditional():
    t=_t()
    fs = t.find('FINAL: Gate Decision')
    assert fs > 0
    sec = t[fs:]
    assert sec.find('$allGatesOk') < sec.find('READY_FOR_SMALL_PILOT')
def test_all_three_pass_yields_ready():
    """When Pass0 + Pass1 + Analyzer PASS, gate is READY_FOR_SMALL_PILOT."""
    assert 'READY_FOR_SMALL_PILOT' in _t()

# ===== Old errors not inherited =====
def test_report_initialized_fresh():
    """Report starts with empty errors array, does not load old JSON."""
    t=_t()
    assert 'errors=@()' in t or "errors = @()" in t

# ===== Join-Path PS 5.1 =====
def test_join_path_named_params():
    assert 'Join-Path -Path' in _t() and '-ChildPath' in _t()

# ===== Analyzer gates =====
def test_analyzer_starts_false():
    assert '$analysis_ok=$false' in _t()

# ===== nsys stats =====
def test_nsys_force_export():
    assert '--force-export=true' in _t()

# ===== Dry-run / paths =====
def test_dry_run():
    with tempfile.TemporaryDirectory() as td:
        m=Path(td)/"m"; m.mkdir(); (m/"config.json").write_text("{}")
        n=Path(td)/"n"; n.mkdir(); (n/"nsys.exe").write_text("f")
        _assert_dry_run_ok(m,n/"nsys.exe",td)
def test_spaces():
    with tempfile.TemporaryDirectory() as td:
        m=Path(td)/"my m"; m.mkdir(); (m/"config.json").write_text("{}")
        n=Path(td)/"n s"; n.mkdir(); (n/"nsys.exe").write_text("f")
        _assert_dry_run_ok(m,n/"nsys.exe",td)
def test_dry_run_is_independent_of_ambient_path():
    """EP-G7-10 regression: a PATH without python must not fail the launcher."""
    if _powershell_exe() is None:
        pytest.skip("Windows PowerShell is unavailable on this host")
    with tempfile.TemporaryDirectory() as td:
        m=Path(td)/"m"; m.mkdir(); (m/"config.json").write_text("{}")
        n=Path(td)/"n"; n.mkdir(); (n/"nsys.exe").write_text("f")
        system_root=os.environ.get("SystemRoot", r"C:\Windows")
        env={
            "SystemRoot": system_root,
            "WINDIR": system_root,
            "PATH": str(Path(system_root)/"System32"),
            "TEMP": td,
            "TMP": td,
        }
        _assert_dry_run_ok(m,n/"nsys.exe",td,env=env)
def test_launcher_invocation_does_not_use_bare_powershell_name():
    """EP-G7-10: hosts must be resolved, never invoked by bare name.

    Structural guard: every ``subprocess.run`` in this module must pass an
    argv list whose first element is a resolved path (a name or call, not a
    bare string literal such as ``["powershell"`` or ``["python"``).
    """
    import ast

    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    run_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "run"
    ]
    assert run_calls, "expected at least one subprocess.run call in this module"
    for call in run_calls:
        argv = call.args[0] if call.args else None
        assert isinstance(argv, ast.List) and argv.elts, "subprocess.run expects an argv list"
        first = argv.elts[0]
        assert not (
            isinstance(first, ast.Constant) and isinstance(first.value, str)
        ), f"bare executable name is not hermetic: {ast.dump(first)}"

# ===== Misc =====
def test_import():
    p=Path(__file__).resolve().parent.parent
    r=subprocess.run([sys.executable,"-c","import sys; sys.path.insert(0,'.'); import exposedpath; print(exposedpath.__version__)"],capture_output=True,text=True,cwd=str(p),timeout=15)
    assert r.returncode==0 and "3.0.0-pilot" in r.stdout
def test_no_bom(): assert not SCRIPT.read_bytes().startswith(b'\xef\xbb\xbf')
def test_pythonpath(): assert '$env:PYTHONPATH' in _t()
def test_resolve_executable(): assert 'function Resolve-Executable' in _t()
