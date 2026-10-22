import importlib.util
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT=Path(__file__).resolve().parents[1]


def module():
    path=ROOT/'scripts/cupti_timeline_model.py'
    assert path.is_file(), 'bounded real-model entry missing'
    spec=importlib.util.spec_from_file_location('timeline_model_test',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def config():
    return dict(schema_version='cupti-timeline-model/0.1.0',run_id='cupti768_once',
        input_tokens=768,batch_size=1,output_tokens=2,warmup_count=3,repeat_count=1,
        role='Engineering',completion_policy='HOST_READABLE_P',model_process_budget=1,
        nsight_profiles=0,torch_profiler=False,native_commit='7fa36efb340fe59a3138eb6132e162d6b0cbfc41')


def test_fixed_scope_is_not_old_pilot_or_input_sweep():
    m=module();m.validate_contract(config())
    for k,v in [('input_tokens',1024),('batch_size',2),('warmup_count',0),('repeat_count',2),
                ('role','Pilot'),('nsight_profiles',1),('torch_profiler',True),('completion_policy','Cpre')]:
        c=config();c[k]=v
        with pytest.raises(ValueError):m.validate_contract(c)


def test_engineering_preparer_reuses_original_p_methods_without_changing_helper():
    m=module()
    from exposedpath.observation_preparation import Execution
    p=m.preparer(config())
    assert type(p).prepare is Execution.prepare and type(p).finish is Execution.finish
    assert p.axis is False and p.variant=='P' and p.binding['run_id']=='cupti768_once'


def test_model_scope_uses_exact_producer_labels_not_nearest_time(tmp_path):
    m=module();identity=dict(run_id='r',request_id='request-0',repeat_id='0',run_role='ENGINEERING',
        data_role='Engineering',pass_id='pass1',experiment_id='e',wmpc_id='w',attempt_id='a')
    host=[dict(payload=dict(identity=identity,boundary_kind='request_start',token_index=None)),
          *[dict(payload=dict(identity=identity,boundary_kind='token_ready',token_index=i)) for i in range(2)]]
    drains=dict(drains=[dict(schema_version='exposedpath-drain-marker/0.1.0',operation_id='drain',
        identity=identity,logical_device=0,marker_role='non_sync_marker',thread_id=9,status='COMPLETE')])
    tokens=dict(identity=identity,pid=7,tid=9,token_ids=[[17],[18]],early_eos=False,
        actual_input_tokens=768,actual_output_tokens=2,prepared_labels=['helper0','helper1'])
    result=m.producer_scopes('session',host,drains,tokens)
    assert len(result)==2 and result[0]['actual_token_ids']==[17] and result[1]['actual_token_ids']==[18]
    assert result[0]['helper_label']=='helper0'
    assert json.loads(result[0]['drain_label'].split(':',1)[1])['operation_id']=='drain'
    assert 'host_start_ns' not in result[0]['drain_label']
    host[1]['payload']['identity']={**identity,'run_id':'foreign'}
    with pytest.raises(ValueError,match='IDENTITY'):m.producer_scopes('session',host,drains,tokens)


@pytest.mark.parametrize('damage',['missing_token','early_eos','wrong_thread','missing_drain'])
def test_incomplete_sidecars_never_grant_scope(damage):
    m=module();i=dict(run_id='r')
    host=[dict(payload=dict(identity=i,boundary_kind='request_start',token_index=None)),
        dict(payload=dict(identity=i,boundary_kind='token_ready',token_index=0)),
        dict(payload=dict(identity=i,boundary_kind='token_ready',token_index=1))]
    drains=dict(drains=[dict(schema_version='x',operation_id='d',identity=i,logical_device=0,
        marker_role='non_sync_marker',thread_id=9,status='COMPLETE')])
    tokens=dict(identity=i,pid=7,tid=9,token_ids=[[1],[2]],early_eos=False,
        actual_input_tokens=768,actual_output_tokens=2,prepared_labels=['a','b'])
    if damage=='missing_token':tokens['token_ids']=[[1]]
    if damage=='early_eos':tokens['early_eos']=True
    if damage=='wrong_thread':tokens['tid']=8
    if damage=='missing_drain':drains['drains']=[]
    with pytest.raises(ValueError):m.producer_scopes('s',host,drains,tokens)


def test_capture_starts_only_after_setup_and_three_original_warmups(tmp_path):
    m=module();events=[]
    class Session:
        def __enter__(self):events.append('capture_open');return self
        def __exit__(self,*args):events.append('capture_close')
        def nvtx_sink(self,nvtx):
            class Sink:
                def __enter__(self):events.append('markers_on')
                def __exit__(self,*args):events.append('markers_off')
            return Sink()
    runner=SimpleNamespace(torch=SimpleNamespace(cuda=SimpleNamespace(nvtx=object())),
        run_warmup=lambda *a:events.append(('warmup',a[-1])),
        run_gate8_requests_to_files=lambda **k:events.append(('measured',k)) or 'receipt')
    result=m.resident_capture(runner,Session(),dict(model=1,input_ids=2,attention_mask=3,eos_token_id=4),
        dict(run_id='cupti768_once'),tmp_path,object(),lambda *a:None)
    assert result=='receipt'
    assert events[:4]==[('warmup',1)]*3+['capture_open']
    assert events[-2:]==['markers_off','capture_close']
    measured=next(e[1] for e in events if isinstance(e,tuple) and e[0]=='measured')
    assert measured['request_plan']==[dict(request_id='request-0',repeat_id='0',request_role='measured')]
    assert measured['record_drains'] is True and measured['record_stages'] is True
    assert 'model_setup' not in measured


@pytest.mark.parametrize('length',[768,1024])
def test_original_runner_produces_two_bound_tokens_and_drain_with_cpu_model(tmp_path,monkeypatch,length):
    import os
    from exposedpath import runner
    from test_runner_token_ready import _FakeInput,_FakeModel,_FakeToken,_patch_cpu_torch
    assert Path(_FakeModel.__call__.__code__.co_filename).resolve()==Path(__file__).with_name('test_runner_token_ready.py').resolve()
    _patch_cpu_torch(monkeypatch)
    monkeypatch.setattr(runner.torch.cuda,'current_device',lambda:0)
    monkeypatch.setattr(runner.torch.cuda,'is_initialized',lambda:False)
    monkeypatch.setattr(runner.torch.cuda.nvtx,'mark',lambda label:None)
    events=[]
    class Input(_FakeInput):shape=(1,length)
    resident=dict(model=_FakeModel(iter(_FakeToken([10+i%2],events) for i in range(8))),
        input_ids=Input(),attention_mask=object(),eos_token_id=None)
    class Session:
        def __enter__(self):events.append('capture_open');return self
        def __exit__(self,*a):events.append('capture_close')
        def nvtx_sink(self,nvtx):
            from contextlib import nullcontext
            return nullcontext()
    m=module();c=config()
    if length==1024:
        from tests.test_cupti_model1024 import contract
        c=contract()
    p=m.preparer(c);observed={}
    fields=dict(experiment_id='e',wmpc_id='w',run_id=c['run_id'],pass_id='pass1',attempt_id='once',
        pid=os.getpid(),wmpc_manifest_sha256='a'*64,prompt_sha256='b'*64,runner_git_commit=m.NATIVE_COMMIT,
        runner_git_dirty=False,runner_source_sha256=hashlib.sha256(Path(runner.__file__).read_bytes()).hexdigest())
    def observer(identity,result):observed.update(identity=identity,result=result,preparation=p.finish(identity))
    receipt=m.resident_capture(runner,Session(),resident,fields,tmp_path,p,observer)
    assert json.loads(Path(receipt).read_text())['status']=='COMPLETE'
    assert events==['capture_open','host_read','host_read','capture_close']
    assert observed['result']['actual_input_tokens']==length and observed['result']['early_eos'] is False
    assert observed['preparation']['consumed_token_indices']==[0,1]
    assert json.loads((tmp_path/'producer/drain_ledger.json').read_text())['drains'][0]['status']=='COMPLETE'
