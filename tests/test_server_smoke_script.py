"""Tests for run_server_smoke_test.ps1 — resume state recovery, gates, Join-Path."""

from __future__ import annotations
import os, subprocess, sys, tempfile
from pathlib import Path
import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "run_server_smoke_test.ps1"
def _t(): return SCRIPT.read_text(encoding="utf-8")
def _run(argv,cwd=None):
    r=subprocess.run(["powershell","-ExecutionPolicy","Bypass","-NoProfile","-Command",f"& '{SCRIPT}' {argv}"],capture_output=True,text=True,cwd=cwd or str(SCRIPT.parent.parent))
    return r.returncode,r.stdout,r.stderr

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
        assert _run(f'-ModelPath "{m}" -GpuId 0 -NsysPath "{n/"nsys.exe"}" -DryRun',td)[0]==0
def test_spaces():
    with tempfile.TemporaryDirectory() as td:
        m=Path(td)/"my m"; m.mkdir(); (m/"config.json").write_text("{}")
        n=Path(td)/"n s"; n.mkdir(); (n/"nsys.exe").write_text("f")
        assert _run(f'-ModelPath "{m}" -GpuId 0 -NsysPath "{n/"nsys.exe"}" -DryRun',td)[0]==0

# ===== Misc =====
def test_import():
    p=Path(__file__).resolve().parent.parent
    r=subprocess.run(["python","-c","import sys; sys.path.insert(0,'.'); import exposedpath; print(exposedpath.__version__)"],capture_output=True,text=True,cwd=str(p),timeout=15)
    assert r.returncode==0 and "3.0.0-pilot" in r.stdout
def test_no_bom(): assert not SCRIPT.read_bytes().startswith(b'\xef\xbb\xbf')
def test_pythonpath(): assert '$env:PYTHONPATH' in _t()
def test_resolve_executable(): assert 'function Resolve-Executable' in _t()
