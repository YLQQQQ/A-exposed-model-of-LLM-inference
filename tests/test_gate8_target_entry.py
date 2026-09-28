"""CPU-only direct entry failures; no profiler, model or CUDA call."""
import json
import os
from pathlib import Path
import subprocess
import sys
import sysconfig

import pytest

from exposedpath_v141 import gate8_target_python as target


def test_real_entry_retains_argparse_exit_without_importing_runner(tmp_path):
    output=tmp_path/'diagnostic'
    command=target.argv(sys._base_executable,sysconfig.get_path('purelib'),[
        'model-run','--output-dir',str(output)])
    result=subprocess.run(command,capture_output=True,text=True,env={**os.environ,'CUDA_VISIBLE_DEVICES':'-1'})
    assert result.returncode==2
    entry=tmp_path/'diagnostic-entry'
    receipt=json.loads((entry/'exit.json').read_text())
    assert receipt['exit_code']==2 and receipt['exception_type']=='SystemExit'
    assert 'SystemExit: 2' in receipt['traceback']
    assert 'required' in (entry/'stderr.txt').read_text()
    assert receipt['runner_imported'] is False and not output.exists()


def test_entry_preserves_original_exception_stdout_and_pid(tmp_path,monkeypatch):
    from exposedpath import gate8_diagnostic
    output=tmp_path/'diagnostic'
    monkeypatch.setattr(sys,'argv',['entry','model-run','--output-dir',str(output)])
    def fail():
        print('before deliberate CPU failure')
        raise RuntimeError('independent sentinel original failure')
    monkeypatch.setattr(gate8_diagnostic,'main',fail)
    with pytest.raises(RuntimeError,match='independent sentinel original failure'):
        target.main()
    receipt=json.loads((tmp_path/'diagnostic-entry/exit.json').read_text())
    assert receipt['pid']==os.getpid() and receipt['exit_code']==1
    assert receipt['exception_type']=='RuntimeError'
    assert 'independent sentinel original failure' in receipt['traceback']
    assert 'before deliberate CPU failure' in (tmp_path/'diagnostic-entry/stdout.txt').read_text()
    assert not output.exists()


def test_runtime_conflict_exposes_differing_fields_without_weakening_gate(monkeypatch):
    contract=target.probe(sys._base_executable,sysconfig.get_path('purelib'))
    observed={**contract['actual']['snapshot'],'environment':{'changed':'CPU sentinel'}}
    monkeypatch.setattr(target,'snapshot',lambda _:observed)
    with pytest.raises(ValueError,match='TARGET_PYTHON_RUNTIME_ENVIRONMENT') as e:
        target.current(contract)
    assert set(e.value.snapshot_difference)=={'environment'}
    assert e.value.snapshot_difference['environment']['observed']==observed['environment']


@pytest.mark.parametrize('original_failure',[False,True])
def test_receipt_io_failure_cannot_succeed_or_mask_original(tmp_path,monkeypatch,original_failure):
    from exposedpath import gate8_diagnostic
    monkeypatch.setattr(sys,'argv',['entry','model-run','--output-dir',str(tmp_path/'diagnostic')])
    def model():
        if original_failure: raise RuntimeError('original remains primary')
        return 0
    monkeypatch.setattr(gate8_diagnostic,'main',model)
    original=Path.open
    def opened(path,*a,**kw):
        if path.name=='exit.json': raise OSError('deliberate receipt IO error')
        return original(path,*a,**kw)
    monkeypatch.setattr(Path,'open',opened)
    with pytest.raises(RuntimeError if original_failure else OSError): target.main()
