"""Prospective warmup control: real producer/files, CPU device/model doubles only."""
import importlib
import importlib.util
import json
import os
import sys
import sysconfig
from itertools import count
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_gate8_identity import sha, write_json


def api():
    assert importlib.util.find_spec('exposedpath.gate11_warmup'), 'Missing versioned warmup control'
    return importlib.import_module('exposedpath.gate11_warmup')


def produce(tmp_path, monkeypatch, condition='N16', warmups=3, runtime=None):
    from exposedpath import gate11_pilot as pilot, runner
    from test_n1_verified_entry import source
    module=api()
    binding=next(b for b in module.schedule('warm-files') if b['block']==1
                 and b['condition']==condition and b['warmup_count']==warmups)
    entry,args,state,events=source(tmp_path,monkeypatch,binding['variant'] or 'V0')
    # A deterministic CPU model must return the same phase token after any
    # number of warmups; the older fixture deliberately encoded call count.
    import test_n1_model_calls as model_fixture
    from test_runner_token_ready import _FakeToken
    monkeypatch.setattr(model_fixture,'_FakeToken',lambda values,events:_FakeToken(
        [13 if values[0]%2 else 14],events))
    serial=count(100)
    monkeypatch.setattr(runner.torch.cuda,'Stream',lambda **kw:SimpleNamespace(
        cuda_stream=next(serial),device=SimpleNamespace(index=0),
        synchronize=lambda:events.append(('sync','explicit'))))
    manifest=json.loads(args['manifest_path'].read_text())
    manifest.update(gpu_uuid='GPU-12345678-1234-1234-1234-123456789abc',gpu_pci_bus_id='0000:01:00.0')
    if runtime is not None:
        from exposedpath_v141 import gate8_target_python as target
        manifest['target_python']=runtime
        monkeypatch.setattr(target,'current',lambda _:dict(pid=os.getpid(),parent_pid=os.getppid(),snapshot=runtime['actual']['snapshot']))
    if binding['variant'] is None:
        manifest.pop('n1_model');manifest.pop('n1_model_execution')
    if condition=='G512':
        model=tmp_path.parent/'cpu_model';model.mkdir(exist_ok=True)
        write_json(model/'config.json',dict(model_type='qwen2',vocab_size=100,max_position_embeddings=1024))
        prompt=json.loads(args['prompt_path'].read_text());prompt['fixed_input_tokens']=512
        prompt['samples']=[dict(input_ids=[1]*512,attention_mask=[1]*512)]
        write_json(args['prompt_path'],prompt)
        manifest.update(model_id=str(model),prompt_tokens_sha256=sha(args['prompt_path']))
    manifest.update(pilot.minimal_fields(binding));write_json(args['manifest_path'],manifest)
    called=[]; original=runner.run_warmup
    def observed(*a,**kw):
        called.append(len(called));return original(*a,**kw)
    monkeypatch.setattr(runner,'run_warmup',observed)
    result=entry.run_diagnostic(**args)
    return binding,args,result,called,state


def pair_files(tmp_path,monkeypatch,condition='N16'):
    from exposedpath_v141 import gate8_target_python as target
    contract=target.probe(sys._base_executable,sysconfig.get_path('purelib'))
    rows=[]
    for count_ in next(b['warmup_order'] for b in api().schedule('warm-files')
                       if b['condition']==condition and b['block']==1):
        folder=tmp_path/f'w{count_}';folder.mkdir()
        with monkeypatch.context() as m:
            binding,args,path,called,state=produce(folder,m,condition,count_,contract)
        root=path.parent;manifest=json.loads((root/'manifest.json').read_text())
        (folder/'diagnostic-entry').mkdir()
        write_json(folder/'diagnostic-entry/exit.json',dict(status='EXITED',exit_code=0,pid=os.getpid()))
        sealed=dict(run_id=binding['run_id'],nonce=binding['run_id'],input_hashes={
            'manifest.json':sha(root/'manifest.json'),'prompt.json':sha(root/'prompt.json')})
        write_json(folder/'auxiliary_preflight.json',sealed)
        claim=dict(target_pid=os.getpid(),nonce=sealed['nonce'],preflight_sha256=sha(folder/'auxiliary_preflight.json'))
        write_json(folder/'auxiliary_preflight.claim.json',claim);write_json(root/'isolated_preflight_target.json',claim)
        write_json(folder/'auxiliary_preflight.final.json',dict(status='PASS',preflight_sha256=sha(folder/'auxiliary_preflight.json'),target_claim_sha256=sha(folder/'auxiliary_preflight.claim.json')))
        write_json(folder/'baseline_report.json',dict(status='BASELINE_COMPLETE_NOT_ACCEPTANCE',pilot=binding,role='UNPROFILED_LIMITED_PILOT'))
        rows.append(dict(binding=binding,output=str(folder)))
    return rows


@pytest.mark.parametrize('condition',['G32','G512','N0','Nm','N16'])
def test_real_pass0_file_pair_preserves_signed_differences(tmp_path,monkeypatch,condition):
    from scripts.gate11_warmup_batch import summarize_pair
    result=summarize_pair(*pair_files(tmp_path,monkeypatch,condition),tmp_path)
    assert result['status']=='PAIR_COMPLETE_PENDING_REVIEW' and result['gate11_verdict']=='BLOCKED'
    assert len(result['warmup1']['warmups'])==1 and len(result['warmup3']['warmups'])==3
    for d in result['measured_difference'].values():
        assert d['delta_ns']==d['warmup3_ns']-d['warmup1_ns']
    assert 'overhead' not in result and result['measurement_validity']=='NOT_ASSESSED'


@pytest.mark.parametrize('damage',['count','stage_order','role','pair','token','partial','warmup_fabricated','variant'])
def test_real_file_pair_refuses_damaged_producer_or_binding(tmp_path,monkeypatch,damage):
    from scripts.gate11_warmup_batch import summarize_pair
    rows=pair_files(tmp_path,monkeypatch);root=Path(rows[0]['output'])/'diagnostic'
    if damage=='pair':rows[0]['binding']=dict(rows[0]['binding'],pair_id='foreign')
    elif damage=='partial':(root/'producer/stage_ledger.json').unlink()
    elif damage in ('count','warmup_fabricated'):
        p=root/'producer/pass_identity.json';v=json.loads(p.read_text())
        if damage=='count':v['requests'].pop(0)
        else:v['requests'][0]['actual_output_tokens']=2
        write_json(p,v)
    elif damage=='stage_order':
        p=root/'producer/stage_ledger.json';v=json.loads(p.read_text());v['stages'].reverse();write_json(p,v)
    elif damage=='token':
        p=root/'pilot_tokens.json';v=json.loads(p.read_text());v['requests'][0]['token_ids'][0]=[99];write_json(p,v)
    else:
        p=root/'manifest.json';v=json.loads(p.read_text())
        if damage=='role':v['data_role']='Engineering'
        else:v['n1_model']['variant']='V0'
        write_json(p,v)
    with pytest.raises((ValueError,FileNotFoundError)):summarize_pair(*rows,tmp_path)


@pytest.mark.parametrize('condition',['G32','G512','N0','Nm','N16'])
def test_actual_prepare_to_verified_entry_warmup3(tmp_path,monkeypatch,condition):
    from exposedpath import gate11_pilot as pilot,runner
    import test_n1_verified_entry as fixture
    from test_gate11_pilot import test_actual_prepare_to_verified_cpu_entry as actual
    rows=[b for b in api().schedule('prepared') if b['warmup_count']==3]
    monkeypatch.setattr(pilot,'schedule',lambda *a:rows)
    original=fixture.source
    def expanded(*a,**kw):
        value=original(*a,**kw); serial=count(100)
        monkeypatch.setattr(runner.torch.cuda,'Stream',lambda **kw:SimpleNamespace(cuda_stream=next(serial),
            device=SimpleNamespace(index=0),synchronize=lambda:None))
        return value
    monkeypatch.setattr(fixture,'source',expanded)
    actual(tmp_path,monkeypatch,condition)


@pytest.mark.parametrize('condition',['G32','N0','Nm','N16'])
def test_real_preflight_to_direct_pass0_launch_cpu_stop(tmp_path,monkeypatch,condition):
    from test_n1_preprofile_identity import prepared_case
    from exposedpath import gate11_pilot as pilot,gate8_isolated_preflight as isolated
    from scripts import gate8_pair as pair,gate8_diagnostic_collect as collector
    from scripts.gate7_smoke_validation import validate_pre_model_identity
    root,prepared,m=prepared_case(tmp_path,monkeypatch)
    b=next(b for b in api().schedule('seal') if b['condition']==condition and b['warmup_count']==3)
    if not b['variant']:m.pop('n1_model');m.pop('n1_model_execution')
    m.update(pilot.minimal_fields(b));write_json(prepared/'manifest.json',m)
    assert not validate_pre_model_identity(prepared/'manifest.json',prepared/'preflight.json',root,execution_contract=api().VERSION)
    assert validate_pre_model_identity(prepared/'manifest.json',prepared/'preflight.json',root,execution_contract=pilot.VERSION)
    monkeypatch.setattr(pair,'ROOT',root);monkeypatch.setattr(collector,'ROOT',root)
    out=tmp_path/'baseline';calls=[]
    def stop(argv,*a,**kw):
        calls.append(argv)
        assert argv[0]==str(Path(sys._base_executable).resolve()) and 'model-run' in argv
        assert 'profile' not in argv and '--auxiliary-receipt' in argv
        sealed=isolated.read(out/'auxiliary_preflight.json')
        claim=isolated.consume(receipt=out/'auxiliary_preflight.json',expected_sha=sha(out/'auxiliary_preflight.json'),
            nonce=sealed['nonce'],prepared=prepared,output=out,root=root)
        assert claim['run_id']==b['run_id']
        return dict(status='BLOCKED',reason='CPU_STOP_BEFORE_MODEL')
    monkeypatch.setattr(collector,'run_once',stop)
    report=pair.baseline(sys._base_executable,prepared,out)
    assert len(calls)==1 and report['status']=='BLOCKED' and report['gate11_verdict']=='BLOCKED'
    assert report['execution']['reason']=='CPU_STOP_BEFORE_MODEL'


def test_closed_schedule_independent_expected_order_and_budget():
    module=api();rows=module.schedule('warm')
    assert len(rows)==30 and {r['pass_id'] for r in rows}=={'pass0'}
    assert [r['condition'] for r in rows[::2]]==[
        'G32','N0','Nm','N16','G512','G512','Nm','N16','N0','G32','G32','N16','N0','Nm','G512']
    assert [r['warmup_count'] for r in rows[:10]]==[1,3,3,1,1,3,3,1,1,3]
    assert len({r['run_id'] for r in rows})==30
    for damage in ('pass','count','role','order','extra'):
        b=dict(rows[0])
        if damage=='pass':b['pass_id']='pass1'
        if damage=='count':b['warmup_count']=2
        if damage=='role':b['purpose']='POLICY_ESTIMATION_ONLY'
        if damage=='order':b['warmup_order']=[3,1]
        if damage=='extra':b['unapproved']=True
        with pytest.raises(ValueError):module.validate_binding(b)


@pytest.mark.parametrize('condition',['G32','G512','N0','Nm','N16'])
@pytest.mark.parametrize('warmups',[1,3])
def test_actual_warmup_calls_order_unknown_fields_and_fresh_measured_stream(tmp_path,monkeypatch,condition,warmups):
    b,args,path,calls,state=produce(tmp_path,monkeypatch,condition,warmups)
    root=path.parent
    assert json.loads(path.read_text())['status']=='DIAGNOSTIC_COMPLETE'
    ledger=json.loads((root/'producer/pass_identity.json').read_text())
    assert calls==list(range(warmups)) and state['loads']==1
    assert [r['identity']['request_id'] for r in ledger['requests']]==[
        *[f'warmup-{i}' for i in range(warmups)],'request-0']
    for r in ledger['requests'][:-1]:
        assert r['outcome']=='COMPLETE' and r['actual_output_tokens'] is None
        assert r['early_eos'] is None and r['observed_boundary_ids']==[]
    assert ledger['requests'][-1]['actual_output_tokens']==2
    stages=json.loads((root/'producer/stage_ledger.json').read_text())['stages']
    assert [s['payload']['stage_role'] for s in stages]==['setup']+['warmup']*warmups+['measured']
    assert all(s['status']=='COMPLETE' and s['host_start_ns']<=s['host_end_ns'] for s in stages)
    if b['variant']:
        n1=json.loads((root/'n1_model_calls.json').read_text())['requests']
        assert [r['native_handle'] for r in n1]==list(range(100,101+warmups))
        assert all(len(r['interventions'])==(0 if b['variant']=='V0' else 1) for r in n1)
        assert all(r['observed_tokens'] is None for r in n1[:-1])
        assert n1[-1]['anchor'] is not None


@pytest.mark.parametrize('damage',['order','count','claimed_tokens','claimed_eos','measured_unknown','foreign_role'])
def test_closed_ledger_semantics_not_just_file_hashes(tmp_path,monkeypatch,damage):
    from exposedpath.gate8_identity import validate_pass_identity
    b,args,path,calls,state=produce(tmp_path,monkeypatch)
    ledger=json.loads((path.parent/'producer/pass_identity.json').read_text())
    if damage=='order':ledger['requests'][0],ledger['requests'][1]=ledger['requests'][1],ledger['requests'][0]
    elif damage=='count':ledger['requests'].pop(0)
    elif damage=='claimed_tokens':ledger['requests'][0]['actual_output_tokens']=2
    elif damage=='claimed_eos':ledger['requests'][0]['early_eos']=False
    elif damage=='measured_unknown':ledger['requests'][-1]['actual_output_tokens']=None
    else:ledger['pilot']['purpose']='POLICY_ESTIMATION_ONLY'
    with pytest.raises(ValueError):validate_pass_identity(ledger)


def test_budget_completion_stops_at30_without_profiles(tmp_path):
    from scripts.gate11_warmup_batch import run_batch
    api();calls=[]
    def execute(b,path):
        calls.append(b);return dict(binding=b,status='RUN_COMPLETE_PENDING_REVIEW')
    def summarize(a,b,out):
        return dict(status='PAIR_COMPLETE_PENDING_REVIEW',pair_id=a['binding']['pair_id'])
    result=run_batch(tmp_path/'batch','complete',execute,summarize)
    assert len(calls)==30 and len(result['pairs'])==15
    assert result['status']=='WARMUP_BATCH_COMPLETE_STOP_FOR_REVIEW' and result['gate11_verdict']=='BLOCKED'
    assert all(b['pass_id']=='pass0' for b in calls) and not result['automatic_retry']


def test_partial_warmup_failure_stops_before_measured_and_preserves_records(tmp_path,monkeypatch):
    module=api()
    from exposedpath import gate11_pilot as pilot,runner
    from test_n1_verified_entry import source
    entry,args,state,events=source(tmp_path,monkeypatch,'V0')
    b=next(b for b in module.schedule('failed') if b['condition']=='N0' and b['warmup_count']==3)
    m=json.loads(args['manifest_path'].read_text());m.update(pilot.minimal_fields(b));write_json(args['manifest_path'],m)
    calls=[];original=runner.run_warmup
    def fail(*a,**kw):
        calls.append(1)
        if len(calls)==2:raise RuntimeError('deliberate second warmup failure')
        return original(*a,**kw)
    monkeypatch.setattr(runner,'run_warmup',fail)
    path=entry.run_diagnostic(**args)
    assert json.loads(path.read_text())['status']=='DIAGNOSTIC_INCOMPLETE'
    ledger=json.loads((path.parent/'producer/pass_identity.json').read_text())
    assert len(calls)==2
    assert [r['outcome'] for r in ledger['requests']]==['COMPLETE','FAILED','FAILED','FAILED']
    assert ledger['requests'][2]['reasons']==['NOT_EXECUTED']
    assert ledger['requests'][-1]['observed_boundary_ids']==[]


def test_batch_stops_at_first_failure_no_replacement_or_resume(tmp_path):
    api()
    from scripts.gate11_warmup_batch import run_batch
    called=[]
    def fail(b,path):
        called.append(b);path.mkdir();(path/'partial').touch()
        raise RuntimeError('deliberate failure')
    result=run_batch(tmp_path/'batch','stop',fail,lambda *a:pytest.fail('pair must not execute'))
    assert len(called)==1 and result['status']=='BLOCKED' and result['gate11_verdict']=='BLOCKED'
    assert all(r['status']=='NOT_RUN' for r in result['runs'][1:])
    plan=json.loads((tmp_path/'batch/planned_runs.json').read_text())
    assert plan['model_process_budget']==30 and plan['profile_budget']==0
    with pytest.raises(FileExistsError):run_batch(tmp_path/'batch','stop',fail,lambda *a:None)
