"""Real isolated CPU imports must preserve the sealed interpreter identity."""
import json
import os
import subprocess
import sys
import sysconfig

from exposedpath_v141 import gate8_target_python as target


def test_model_import_order_preserves_every_snapshot_field():
    code = r'''
import sys, json, importlib
sys.path[:0] = sys.argv[1:3]
from exposedpath_v141 import gate8_target_python as t
contract = t.probe(sys.executable, sys.argv[2])
expected = contract['actual']['snapshot']
stages = []
for name in ('exposedpath.gate8_diagnostic', 'exposedpath.runner'):
    importlib.import_module(name)
    observed = t.snapshot(sys.argv[2])
    stages.append({'stage': name, 'differences': {
        k: {'expected': expected[k], 'observed': observed[k]}
        for k in expected if expected[k] != observed[k]}})
print(json.dumps(stages), flush=True)
t.current(contract)
# Deliberate path tampering must still fail; never normalize duplicates away.
sys.path.insert(0, sys.path[0])
try:
    t.current(contract)
except ValueError as error:
    assert str(error) == 'TARGET_PYTHON_RUNTIME_ENVIRONMENT'
    assert set(error.snapshot_difference) == {'sys_path'}
else:
    raise AssertionError('path tampering accepted')
assert not sys.modules['torch'].cuda._initialized
'''
    result = subprocess.run(
        [sys._base_executable, '-I', '-S', '-c', code,
         str(target.ROOT), sysconfig.get_path('purelib')],
        capture_output=True, text=True, timeout=90,
        env={**os.environ, 'CUDA_VISIBLE_DEVICES': '-1'})
    assert result.returncode == 0, result.stdout + result.stderr
    assert all(not stage['differences'] for stage in json.loads(result.stdout))


def test_validation_direct_script_bootstrap_outside_repository(tmp_path):
    result = subprocess.run(
        [sys.executable, str(target.ROOT / 'scripts/gate7_smoke_validation.py'), '--help'],
        cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert 'usage:' in result.stdout
