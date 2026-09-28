"""CPU-only subprocess provenance, independent child PID/exit observations."""
import json
import os
from pathlib import Path
import sys

import pytest

from exposedpath import platform_adapter as adapter
from exposedpath.process_origin import recording, load_recording


@pytest.mark.parametrize('code',[0,7])
def test_real_child_pid_exit_and_private_arguments(tmp_path,code):
    path=tmp_path/'origin.jsonl'
    with recording(path):
        result=adapter.run_tool(sys._base_executable,
            ['-c',f'import os,sys; print(os.getpid()); sys.exit({code})','private-argument'],
            env={**os.environ,'PRIVATE_SENTINEL':'private-environment'})
    rows=load_recording(path)
    start=next(r for r in rows if r['event']=='STARTED')
    end=next(r for r in rows if r['event']=='EXITED')
    assert start['pid']==int(result.stdout) and start['parent_pid']==os.getpid()
    assert start['executable']==str(Path(sys._base_executable).resolve())
    assert end['returncode']==result.returncode==code
    assert start['call_id']==end['call_id'] and start['time_ns']<=end['time_ns']
    assert 'private-argument' not in path.read_text() and 'private-environment' not in path.read_text()
    assert rows[0]['native_process_coverage']=='UNKNOWN'
    assert rows[0]['warning_disposition']=='NOT_ASSESSED'


def test_launch_failure_preserves_original_without_inventing_pid(tmp_path,monkeypatch):
    path=tmp_path/'origin.jsonl'
    monkeypatch.setattr(adapter,'tool_argv',lambda *a,**k:[str(tmp_path/'nonexistent.exe')])
    with pytest.raises(OSError):
        with recording(path): adapter.run_tool('missing')
    rows=load_recording(path)
    failed=next(r for r in rows if r['event']=='START_FAILED')
    assert failed['pid'] is None and failed['returncode'] is None


def test_resolution_failure_recorded_without_private_error_text(tmp_path):
    path=tmp_path/'origin.jsonl'
    with pytest.raises(adapter.ToolUnavailableError):
        with recording(path): adapter.run_tool('private-nonexistent-tool-123')
    rows=load_recording(path)
    assert rows[-2]['event']=='START_FAILED'
    assert 'private-nonexistent-tool-123' not in path.read_text()


def test_missing_or_partial_recording_rejected(tmp_path):
    path=tmp_path/'origin.jsonl'
    with pytest.raises((ValueError,OSError)): load_recording(path)
    with recording(path): adapter.run_tool(sys._base_executable,['-c','pass'])
    rows=path.read_text().splitlines()
    path.write_text('\n'.join(rows[:-1])+'\n')
    with pytest.raises(ValueError): load_recording(path)


def test_missing_child_exit_rejected_even_with_footer(tmp_path):
    path=tmp_path/'origin.jsonl'
    with recording(path): adapter.run_tool(sys._base_executable,['-c','pass'])
    rows=[json.loads(line) for line in path.read_text().splitlines()]
    rows=[r for r in rows if r['event']!='EXITED']
    # Even apparently contiguous numbering cannot hide an open call.
    for i,row in enumerate(rows): row['sequence']=i
    path.write_text('\n'.join(json.dumps(r) for r in rows)+'\n')
    with pytest.raises(ValueError): load_recording(path)


def test_call_identity_not_just_pid_and_empty_does_not_claim_coverage(tmp_path):
    path=tmp_path/'origin.jsonl'
    with recording(path):
        for _ in range(2): adapter.run_tool(sys._base_executable,['-c','pass'])
    rows=load_recording(path)
    starts=[r for r in rows if r['event']=='STARTED']
    assert len({r['call_id'] for r in starts})==2
    assert len({r['parent_instance_id'] for r in starts})==1
    empty=tmp_path/'empty.jsonl'
    with recording(empty): pass
    assert load_recording(empty)[0]['unrecorded_processes']=='UNKNOWN_NOT_ABSENCE'


def test_model_entry_installs_recorder_before_dispatch(tmp_path,monkeypatch):
    from exposedpath import gate8_diagnostic
    from exposedpath_v141 import gate8_target_python as target
    monkeypatch.setattr(sys,'argv',['entry','model-run','--output-dir',str(tmp_path/'diagnostic')])
    monkeypatch.setattr(gate8_diagnostic,'main',lambda: adapter.run_tool(sys._base_executable,['-c','pass']).returncode)
    assert target.main()==0
    rows=load_recording(tmp_path/'diagnostic-entry/subprocess_origin.jsonl')
    assert any(r['event']=='STARTED' for r in rows)


def test_missing_record_blocks_successful_recording_close(tmp_path):
    path=tmp_path/'origin.jsonl'
    with pytest.raises((ValueError,OSError)):
        with recording(path):
            adapter.run_tool(sys._base_executable,['-c','pass'])
            # Corrupt the persisted log, not the child execution.
            path.write_text('')


def test_record_write_failure_does_not_launch_child(tmp_path,monkeypatch):
    from exposedpath.process_origin import Recorder
    path=tmp_path/'origin.jsonl'
    launched=[]
    monkeypatch.setattr(adapter.subprocess,'Popen',lambda *a,**k: launched.append(True))
    emit=Recorder.emit
    def fail(self,event,**fields):
        if event=='STARTING': raise OSError('record unavailable')
        return emit(self,event,**fields)
    monkeypatch.setattr(Recorder,'emit',fail)
    with pytest.raises(OSError,match='record unavailable'):
        with recording(path): adapter.run_tool(sys._base_executable,['-c','pass'])
    assert not launched


def test_timeout_preserves_run_exception_output_and_records_exit(tmp_path,monkeypatch):
    # Deterministic Popen double: independent of process boot scheduling.
    class Child:
        pid=12345
        returncode=None
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def communicate(self,timeout=None):
            if timeout is not None:
                raise adapter.subprocess.TimeoutExpired('child',timeout,output=b'partial')
            return b'complete output',b'complete error'
        def kill(self): self.returncode=9
    monkeypatch.setattr(adapter.subprocess,'Popen',lambda *a,**k:Child())
    path=tmp_path/'origin.jsonl'
    with pytest.raises(adapter.subprocess.TimeoutExpired) as caught:
        with recording(path): adapter.run_tool(sys._base_executable,[],timeout=1)
    expected=b'complete output' if sys.platform=='win32' else b'partial'
    assert caught.value.output==expected
    assert load_recording(path)[-2]['returncode']==9


def test_caught_write_failure_poisoned_recording_cannot_close_successfully(tmp_path):
    path=tmp_path/'origin.jsonl'
    with pytest.raises((ValueError,OSError)):
        with recording(path) as recorder:
            real=recorder.handle
            class FailOnce:
                def write(self,text):
                    recorder.handle=real
                    raise OSError('transient storage failure')
            recorder.handle=FailOnce()
            try: adapter.run_tool(sys._base_executable,['-c','pass'])
            except OSError: pass  # Existing optional-query callers can do this.
    with pytest.raises(ValueError): load_recording(path)


def test_entry_close_failure_is_recorded_as_failed_exit(tmp_path,monkeypatch):
    from exposedpath import gate8_diagnostic
    from exposedpath.process_origin import Recorder
    from exposedpath_v141 import gate8_target_python as target
    monkeypatch.setattr(sys,'argv',['entry','model-run','--output-dir',str(tmp_path/'diagnostic')])
    monkeypatch.setattr(gate8_diagnostic,'main',lambda:0)
    emit=Recorder.emit
    def fail(self,event,**fields):
        if event=='CLOSED': raise OSError('closure failure')
        return emit(self,event,**fields)
    monkeypatch.setattr(Recorder,'emit',fail)
    with pytest.raises(OSError,match='closure failure'): target.main()
    receipt=json.loads((tmp_path/'diagnostic-entry/exit.json').read_text())
    assert receipt['exit_code']==1 and receipt['exception_type']=='OSError'


def test_direct_python_subprocess_is_explicitly_outside_adapter_coverage(tmp_path):
    import subprocess
    path=tmp_path/'origin.jsonl'
    with recording(path):
        child=subprocess.run([sys._base_executable,'-c','pass'],check=True)
    assert child.returncode==0
    rows=load_recording(path)
    assert [r['event'] for r in rows]==['OPEN','CLOSED']
    assert rows[0]['unrecorded_processes']=='UNKNOWN_NOT_ABSENCE'


@pytest.mark.parametrize('field,value',[
    ('clock','wrong-clock'),('scope','ALL_PROCESSES'),
    ('native_process_coverage','COMPLETE'),('warning_disposition','EXEMPT'),
])
def test_loader_rejects_false_coverage_claims(tmp_path,field,value):
    path=tmp_path/'origin.jsonl'
    with recording(path): pass
    rows=[json.loads(line) for line in path.read_text().splitlines()]
    rows[0][field]=value
    path.write_text('\n'.join(json.dumps(r) for r in rows)+'\n')
    with pytest.raises(ValueError): load_recording(path)


def test_start_failure_missing_pid_is_not_explicit_unknown(tmp_path):
    path=tmp_path/'origin.jsonl'
    with pytest.raises(adapter.ToolUnavailableError):
        with recording(path): adapter.run_tool('nonexistent-origin-fixture')
    rows=[json.loads(line) for line in path.read_text().splitlines()]
    del rows[-2]['pid']
    path.write_text('\n'.join(json.dumps(r) for r in rows)+'\n')
    with pytest.raises(ValueError): load_recording(path)


def test_pid_reuse_requires_disjoint_call_lifecycles(tmp_path):
    path=tmp_path/'origin.jsonl'
    with recording(path):
        for _ in range(2): adapter.run_tool(sys._base_executable,['-c','pass'])
    rows=[json.loads(line) for line in path.read_text().splitlines()]
    # Independent fixture of OS PID reuse, not a claim the OS reused it here.
    for row in rows:
        if row['event'] in ('STARTED','EXITED'): row['pid']=12345
    def save(values):
        for i,row in enumerate(values): row.update(sequence=i,time_ns=i)
        path.write_text('\n'.join(json.dumps(r) for r in values)+'\n')
    save(rows)
    assert len(load_recording(path))==8
    # Same PID simultaneously attributed to two calls is ambiguous, not reuse.
    overlap=[rows[i] for i in (0,1,2,4,5,3,6,7)]
    save(overlap)
    with pytest.raises(ValueError): load_recording(path)
