"""Test-only child process: real storage CLI, explicit deterministic OS doubles."""
import importlib.util
import os
from pathlib import Path
import sys
from types import SimpleNamespace

spec=importlib.util.spec_from_file_location('actual_storage',Path.cwd()/'scripts/coe_startup_storage.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
scenario=os.environ['COE_TEST_SCENARIO']
m.volume_identity=lambda p:'CPU_BOUNDARY_VOLUME_NOT_TARGET'
def free(path):
    if scenario=='query':raise OSError('CPU query unavailable')
    return SimpleNamespace(free=12884901887 if scenario=='low' else 12884901888,total=100000000000)
m.shutil.disk_usage=free
if scenario=='write':
    def denied(path):raise PermissionError('CPU explicit write denial')
    m.write_probe=denied
raise SystemExit(m.main(sys.argv[1:]))
