"""Fake native child only. No real Nsight or model."""
import importlib.util
import importlib
import json
import sys
from pathlib import Path

import pytest


def api():
    assert importlib.util.find_spec('scripts.gate8_diagnostic_collect'), 'Missing bounded collection adapter'
    return importlib.import_module('scripts.gate8_diagnostic_collect')


@pytest.mark.parametrize('mode', ['ok', 'failed', 'timeout'])
def test_native_process_is_attempted_once_and_preserved(tmp_path, mode):
    module=api()
    script=tmp_path/'child.py'
    script.write_text("import sys,time\nprint('started',flush=True)\n"+
        ("time.sleep(20)\n" if mode=='timeout' else "raise SystemExit("+('0' if mode=='ok' else '7')+")\n"))
    result=module.run_once([sys._base_executable,'-I','-S',str(script)],tmp_path/'logs',timeout_seconds=2 if mode=='timeout' else 10)
    assert result['attempt_count']==1
    assert result['status']==('COMPLETE' if mode=='ok' else 'BLOCKED')
    assert result['timed_out']==(mode=='timeout')
    assert (tmp_path/'logs/stdout.txt').read_text().strip()=='started'
    assert json.loads((tmp_path/'logs/process.json').read_text())==result


@pytest.mark.parametrize('platform,kill', [('win32','true'),('linux','sigkill')])
def test_profile_argv_is_minimal_fixed_and_bounded(tmp_path,monkeypatch,platform,kill):
    module=api()
    monkeypatch.setattr(module.sys,'platform',platform)
    argv=module.profile_argv('nsys.exe','python.exe',tmp_path/'prepared',tmp_path/'new',tmp_path/'repo')
    assert '--trace=cuda,nvtx' in argv and '--sample=none' in argv and '--cpuctxsw=none' in argv
    assert '--duration=120' in argv and '--kill='+kill in argv
    assert '--stats=true' not in argv and '--force-overwrite=true' not in argv
    assert argv.count('exposedpath.gate8_diagnostic')==1
    assert 'run' in argv


def test_verified_relative_python_is_executed_as_absolute(monkeypatch,tmp_path):
    module=api()
    repo=tmp_path/'repo'; repo.mkdir()
    python=repo/'.venv/Scripts/python.exe'; python.parent.mkdir(parents=True); python.touch()
    nsys=tmp_path/'nsys.exe'; nsys.touch()
    monkeypatch.setattr(module,'ROOT',repo)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys,'argv',['collect','--nsys',str(nsys),'--python','repo/.venv/Scripts/python.exe',
        '--prepared',str(tmp_path/'prepared'),'--output',str(tmp_path/'out'),'--execute-engineering-diagnostic'])
    def checked(argv,*a,**kw):
        assert str(python.resolve()) in argv
        return {'status':'BLOCKED'}
    monkeypatch.setattr(module,'run_once',checked)
    assert module.main()==1


def test_collection_intent_exists_before_child_starts(tmp_path):
    module=api()
    script=tmp_path/'child.py'
    report=tmp_path/'log/process.json'
    script.write_text("from pathlib import Path\nimport sys\nassert Path(sys.argv[1]).is_file()\n")
    result=module.run_once([sys._base_executable,'-I','-S',str(script),str(report)],tmp_path/'log',timeout_seconds=10)
    assert result['status']=='COMPLETE'


def test_receipt_write_failure_after_spawn_still_stops_recorded_process(monkeypatch,tmp_path):
    module=api()
    script=tmp_path/'sleep.py'; script.write_text('import time\ntime.sleep(20)\n')
    replace=Path.replace
    calls=[]; children=[]
    def fail_second(path,target):
        calls.append(path)
        if len(calls)==2: raise OSError('receipt write failure')
        return replace(path,target)
    popen=module.subprocess.Popen
    def record(*a,**kw):
        child=popen(*a,**kw); children.append(child); return child
    monkeypatch.setattr(Path,'replace',fail_second)
    monkeypatch.setattr(module.subprocess,'Popen',record)
    try:
        result=module.run_once([sys._base_executable,'-I','-S',str(script)],tmp_path/'log',timeout_seconds=1)
        assert result['status']=='BLOCKED'
        assert children[0].poll() is not None
    finally:
        for child in children:
            if child.poll() is None: child.kill(); child.wait(timeout=5)


def test_model_profile_uses_sealed_direct_interpreter(tmp_path):
    import sysconfig
    from exposedpath_v141 import gate8_target_python as target
    prepared=tmp_path/'prepared'; prepared.mkdir()
    contract=target.probe(sys._base_executable,sysconfig.get_path('purelib'))
    (prepared/'manifest.json').write_text(json.dumps({'target_python':contract}))
    argv=api().profile_argv('nsys',sys._base_executable,prepared,tmp_path/'out')
    assert str(Path(sys._base_executable).resolve()) in argv
    assert '-I' in argv and '-S' in argv and 'model-run' in argv
    with pytest.raises(ValueError,match='TARGET'):
        api().profile_argv('nsys','unsealed-python',prepared,tmp_path/'out')


def test_new_a_only_entry_rejects_unsealed_manifest_before_launch(tmp_path,monkeypatch):
    from exposedpath.gate8_engineering_contract import declaration
    module=api(); prepared=tmp_path/'prepared'; prepared.mkdir()
    (prepared/'manifest.json').write_text(json.dumps(dict(engineering_scope=declaration('sdpa'),
        attention_backend='sdpa',batch_size=1,execution_mode='eager',run_role='ENGINEERING',data_role='Engineering')))
    nsys=tmp_path/'nsys.exe'; nsys.touch()
    monkeypatch.setattr(sys,'argv',['collect','--nsys',str(nsys),'--python',sys._base_executable,
        '--prepared',str(prepared),'--output',str(tmp_path/'out'),'--execute-engineering-diagnostic','--engineering-a-only'])
    def forbidden(*a,**kw): raise AssertionError('launched before identity validation')
    monkeypatch.setattr(module,'run_once',forbidden)
    with pytest.raises(KeyError,match='target_python'): module.main()
    assert not (tmp_path/'out').exists()
