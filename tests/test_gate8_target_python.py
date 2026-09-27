"""Real CPU subprocess identity; no CUDA, native DLL or collector execution."""
import importlib.util
import importlib
import os
from pathlib import Path
import sys
import sysconfig
from copy import deepcopy
import pytest


def adapter():
    assert importlib.util.find_spec('exposedpath_v141.gate8_target_python'), 'explicit target adapter absent'
    return importlib.import_module('exposedpath_v141.gate8_target_python')


def test_direct_cpu_probe_binds_pid_executable_and_dependency_environment():
    m=adapter(); value=m.probe(Path(sys._base_executable),Path(sysconfig.get_path('purelib')))
    assert value['launch_pid']==value['actual']['pid']>0
    assert value['actual']['snapshot']['executable']==str(Path(sys._base_executable).resolve())
    assert value['actual']['snapshot']['isolated'] is True
    assert value['actual']['snapshot']['no_site'] is True
    assert Path(value['actual']['snapshot']['jsonschema_file']).is_relative_to(Path(sysconfig.get_path('purelib')).resolve())


@pytest.mark.parametrize('fault',['pid','executable','environment','nonce'])
def test_probe_identity_mismatch_rejected(fault):
    m=adapter(); value=m.probe(Path(sys._base_executable),Path(sysconfig.get_path('purelib')))
    bad=deepcopy(value)
    if fault=='pid': bad['actual']['pid']+=1
    elif fault=='executable': bad['actual']['snapshot']['executable']=str(Path(sys.executable).with_name('different.exe'))
    elif fault=='environment': bad['actual']['snapshot']['environment']['CUDA_VISIBLE_DEVICES']='foreign'
    else: bad['actual']['nonce']='foreign'
    with pytest.raises(ValueError): m.validate_probe(bad)


def test_unknown_sync_enum_is_not_suffix_guessed():
    from exposedpath_v141 import gate8_qualification_oracle as oracle
    assert hasattr(oracle,'sync_kind'), 'exact sync enum adapter missing'
    assert oracle.sync_kind('CUPTI_ACTIVITY_SYNCHRONIZATION_TYPE_CONTEXT_SYNCHRONIZE')=='CONTEXT_SYNCHRONIZE'
    assert oracle.sync_kind('STREAM_SYNCHRONIZE')=='STREAM_SYNCHRONIZE'
    with pytest.raises(ValueError): oracle.sync_kind('FOREIGN_STREAM_SYNCHRONIZE')
    with pytest.raises(ValueError): oracle.sync_kind('CUPTI_ACTIVITY_SYNCHRONIZATION_TYPE_STREAM_WAIT_EVENT')


def test_producer_pid_must_match_runtime_receipt():
    m=adapter(); p=m.probe(Path(sys._base_executable),Path(sysconfig.get_path('purelib')))
    runtime=dict(pid=123,parent_pid=100,snapshot=p['actual']['snapshot'])
    m.bind_producer(p,runtime,123)
    with pytest.raises(ValueError): m.bind_producer(p,runtime,124)


def test_production_plan_seals_explicit_target_and_pre_native_gate(tmp_path,monkeypatch):
    from qualification_fixture import capture
    import json
    from exposedpath_v141 import gate8_qualification as q
    plan,*_=capture(tmp_path,monkeypatch)
    value=json.loads(plan.read_text())
    assert 'target_python' in value, 'target runtime absent from production plan'
    # Changed environment must stop before loading a native library.
    monkeypatch.setenv('CUDA_DEVICE_ORDER','OTHER')
    with pytest.raises(ValueError): q.execute(plan,tmp_path/'rejected')


def test_nsight_launch_pid_must_bind_to_producer(tmp_path):
    m=adapter()
    assert hasattr(m,'bind_trace_launch'), 'collector-to-producer binding missing'
    import sqlite3
    p=tmp_path/'raw.sqlite'
    with sqlite3.connect(p) as c:
        c.execute('CREATE TABLE DIAGNOSTIC_EVENT(source INTEGER,severity INTEGER,text TEXT,globalPid INTEGER)')
        c.execute('INSERT INTO DIAGNOSTIC_EVENT VALUES (2,1,?,?)',('Process 123 was launched by the profiler',(1<<48)+(123<<24)))
    assert m.bind_trace_launch(p,123)['pid']==123
    with pytest.raises(ValueError): m.bind_trace_launch(p,124)


def test_nonisolated_producer_rejected_before_native_initialization(tmp_path,monkeypatch):
    from qualification_fixture import capture
    from exposedpath_v141 import gate8_qualification as q
    m=adapter(); actual_current=m.current
    plan,*_=capture(tmp_path,monkeypatch)
    monkeypatch.setattr(m,'current',actual_current)
    def forbidden(_): raise AssertionError('native initialization attempted')
    with pytest.raises(ValueError,match='RUNTIME_ENVIRONMENT'):
        q.execute(plan,tmp_path/'blocked',backend_factory=forbidden)
    assert not (tmp_path/'blocked').exists()


@pytest.mark.parametrize('fault',['missing','duplicate','namespace'])
def test_collector_identity_missing_ambiguous_or_foreign_namespace_rejected(tmp_path,fault):
    m=adapter(); import sqlite3
    p=tmp_path/'trace.sqlite'
    with sqlite3.connect(p) as c:
        c.execute('CREATE TABLE DIAGNOSTIC_EVENT(source INTEGER,severity INTEGER,text TEXT,globalPid INTEGER)')
        c.execute('CREATE TABLE NVTX_EVENTS(globalTid INTEGER)')
        c.execute('INSERT INTO NVTX_EVENTS VALUES (?)',((1<<48)+(123<<24)+7,))
        if fault!='missing':
            c.execute('INSERT INTO DIAGNOSTIC_EVENT VALUES (2,1,?,?)',('Process 123 was launched by the profiler',((2 if fault=='namespace' else 1)<<48)+(123<<24)))
        if fault=='duplicate': c.execute('INSERT INTO DIAGNOSTIC_EVENT SELECT * FROM DIAGNOSTIC_EVENT')
    with pytest.raises(ValueError): m.bind_trace_launch(p,123)


def test_profile_uses_sealed_target_not_orchestrator(tmp_path,monkeypatch):
    from qualification_fixture import capture
    from exposedpath_v141 import gate8_qualification as q
    import json
    plan,*_=capture(tmp_path,monkeypatch); target=json.loads(plan.read_text())['target_python']
    args=q.profile_argv('not-executed-nsys',target['requested_executable'],plan,tmp_path/'new')
    position=args.index(target['requested_executable'])
    assert args[position+1:position+4]==['-I','-S','-c']
    assert target['site_root'] in args
    with pytest.raises(ValueError): q.profile_argv('not-executed-nsys',sys.executable+'wrong',plan,tmp_path/'new')


def test_offline_probe_validation_does_not_require_auditor_checkout_path():
    m=adapter(); p=m.probe(Path(sys._base_executable),Path(sysconfig.get_path('purelib')))
    p['module_root']='different-host-checkout'
    p['actual']['snapshot']['module_root']='different-host-checkout'
    assert m.validate_probe(p)==p


def test_real_isolated_cpu_process_writes_bound_producer_files(tmp_path,monkeypatch):
    from qualification_fixture import capture
    from exposedpath_v141 import gate8_qualification as q
    import json
    import subprocess
    m=adapter(); plan,*_=capture(tmp_path,monkeypatch)
    target=json.loads(plan.read_text())['target_python']; output=tmp_path/'child-execution'
    command=m.argv(target['requested_executable'],target['site_root'],[])
    # Test-only bootstrap preserves exactly the production sys.path/isolation policy;
    # only native calls are replaced. No runtime identity function is mocked in child.
    command[4]="import sys,runpy;sys.path[:0]=sys.argv[1:3];del sys.argv[1:3];sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name='__main__')"
    command += [str(Path(__file__).with_name('target_python_cpu_child.py')),str(plan),str(output)]
    process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,cwd=m.ROOT)
    stdout,stderr=process.communicate(timeout=20)
    assert process.returncode==0,stderr
    execution=q.validate_execution(plan,output/'execution.json')
    assert execution['status']=='COMPLETE'
    assert process.pid==execution['target_runtime']['pid']==json.loads((output/'pass_identity.json').read_text())['pid']
    execution['target_runtime']['pid']+=1
    (output/'execution.json').write_text(json.dumps(execution),encoding='utf-8')
    with pytest.raises(ValueError,match='PRODUCER_IDENTITY'): q.validate_execution(plan,output/'execution.json')
