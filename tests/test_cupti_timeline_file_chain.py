"""Hand-specified CPU trace/file-chain reference. No target GPU evidence."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]


def load(name):
    p=ROOT/'scripts'/name
    spec=importlib.util.spec_from_file_location('_cpu_'+p.stem,p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def fixture(root):
    from test_cupti_timeline_adapter import marked_capture
    assert Path(marked_capture.__code__.co_filename).resolve()==Path(__file__).with_name('test_cupti_timeline_adapter.py').resolve()
    from exposedpath.gate8_identity import make_gate8_pass_identity
    from exposedpath.gate8_boundary import Gate8BoundaryRecorder,BOUNDARY_PREFIX
    from exposedpath.nvtx import make_natural_token_ready_identity,make_structured_nvtx_label
    b=load('cupti_timeline_b.py');model=load('cupti_timeline_model.py')
    raw,_=marked_capture();raw['source']='TARGET_CUPTI' # CPU INPUT DOUBLE; never a target qualification.
    calls=[deepcopy(c) for c in raw['callbacks'] if c['id'] in (6,7,8,9)]
    for c in calls:
        c['id']+=100;c['parent_id']=c['parent_id']+100 if c['parent_id'] else None
        c['correlation']+=100;c['start']+=100;c['end']+=100;c['enter_seq']+=100;c['exit_seq']+=100
    raw['callbacks']+=calls
    rows=[deepcopy(r) for r in raw['records'] if r['id'] in ('api6','api8','d','sync')]
    for r in rows:
        r['id']+='second';r['correlation']+=100;r['start']+=100;r['end']+=100
        if r.get('runtime_correlation'):r['runtime_correlation']+=100
    raw['records']+=rows
    root.mkdir();(root/'producer').mkdir();(root/'timeline').mkdir()
    def put(name,v):
        p=root/name;p.write_text(json.dumps(v,sort_keys=True),encoding='utf8')
        return dict(filename=p.name,sha256=b.sha(p),size_bytes=p.stat().st_size)
    config=root/'model_config.json';put('model_config.json',dict(role='CPU_FIXTURE_NOT_TARGET'))
    fields=dict(experiment_id='cpu',wmpc_id='cpu',run_id='r',pass_id='pass1',attempt_id='once',pid=7,
        wmpc_manifest_sha256=b.sha(config),prompt_sha256='b'*64,runner_source_sha256='c'*64,
        runner_git_commit=b.NATIVE_COMMIT,runner_git_dirty=False)
    ledger=make_gate8_pass_identity(requests=[dict(request_id='request-0',repeat_id='0',request_role='measured',
        expected_output_tokens=2,actual_output_tokens=2,expected_boundary_ids=['b0','b1','b2'],
        observed_boundary_ids=['b0','b1','b2'],outcome='COMPLETE',early_eos=False,reasons=[])],**fields)
    identity=ledger['requests'][0]['identity'];labels=[]
    clock=iter(range(1000,1010));rec=Gate8BoundaryRecorder(identity,['b0','b1','b2'],marker_sink=labels.append,clock_ns=lambda:next(clock))
    rec.observe(0);rec.observe(0,0);rec.observe(0,1)
    helper=[make_structured_nvtx_label(make_natural_token_ready_identity(identity,phase=p,token_index=i,
        callsite_id=f'{p}.token_ready',sync_ordinal=i,token_ready_mechanism='torch_tensor_detach_cpu_tolist'))
        for i,p in enumerate(('prefill','decode'))]
    drains=dict(drains=[dict(schema_version='exposedpath-drain-marker/0.1.0',operation_id='drain',identity=identity,
        logical_device=0,marker_role='non_sync_marker',thread_id=9,status='COMPLETE')])
    tokens=dict(identity=identity,pid=7,tid=9,token_ids=[[17],[18]],early_eos=False,
        actual_input_tokens=768,actual_output_tokens=2,prepared_labels=helper)
    scopes=model.producer_scopes('test',rec.records,drains,tokens)
    raw['session_id']='test'
    raw['markers']=[dict(action=1,time=0,tid=9,label=scopes[0]['drain_label']),dict(action=2,time=6,tid=9,label=''),
        dict(action=0,time=10,tid=9,label=labels[0]),dict(action=1,time=39,tid=9,label=helper[0]),
        dict(action=0,time=75,tid=9,label=labels[1]),dict(action=2,time=76,tid=9,label=''),
        dict(action=1,time=139,tid=9,label=helper[1]),dict(action=0,time=175,tid=9,label=labels[2]),dict(action=2,time=176,tid=9,label='')]
    files={}
    for name,v in [('pass_identity.json',ledger),('host_boundaries.json',rec.records),('drain_ledger.json',drains)]:
        files[name]=put('producer/'+name,v)
    put('producer/producer_receipt.json',dict(status='COMPLETE',files=files))
    put('tokens.json',tokens);put('scope_producers.json',scopes);put('timeline/capture.json',raw)
    put('timeline/receipt.json',dict(pid=7,open_code=0,close_code=0,model_error_type=None,
        verification_mode='TARGET_CUPTI_UNQUALIFIED',capture_sha256=b.sha(root/'timeline/capture.json'),
        client_sha256='d'*64,cupti_sha256='e'*64))
    put('setup.json',dict(input_sha256='b'*64,input_shape=[1,768],runner_source_sha256='c'*64,
        python_version=[3,11,16],loaded_backend='sdpa',torch_version='2.6.0+cu124'))
    put('warmup_completed.json',dict(completed_count=3,subscription_active=False))
    r=dict(schema_version='cupti-timeline-model-result/0.1.0',status='MODEL_CAPTURE_COMPLETE_PENDING_ANALYSIS',
        role='Engineering',pid=7,config_sha256=b.sha(config))
    for k,n in dict(capture_sha256='timeline/capture.json',session_receipt_sha256='timeline/receipt.json',
        producer_receipt_sha256='producer/producer_receipt.json',token_sha256='tokens.json',scope_producers_sha256='scope_producers.json',
        setup_sha256='setup.json',warmup_sha256='warmup_completed.json').items():r[k]=b.sha(root/n)
    put('model_result.json',r)
    cfg=dict(model_config=str(config),client=dict(sha256='d'*64),cupti=dict(sha256='e'*64),session_id='test',
        run_id='r',prompt_sha256='b'*64,model_script=str(ROOT/'scripts/cupti_timeline_model.py'),expected_token_ids=[[17],[18]])
    return b,cfg


def test_cpu_reference_two_original_label_chains_reach_same_run_COE(tmp_path):
    b,cfg=fixture(tmp_path/'model')
    result=b.analyze_model(tmp_path/'model',dict(pid=7),cfg)
    assert result['status']=='BOTH_TOKENS_EVIDENCE_COMPLETE_PENDING_REVIEW'
    # First: [40,70] intersects kernel[30,55]+memset[56,60]+D2H[61,62] = 20ns.
    # Second: [140,170] only intersects the next D2H[161,162] = 1ns.
    assert [r['result']['coe_ns'] for r in result['token_results']]==[20,1]
    assert all(r['result']['pure_host_blocking'] is None for r in result['token_results'])


@pytest.mark.parametrize('damage',['pid','capture','token','scope','session','warmup'])
def test_real_file_consumer_rejects_mixed_or_corrupt_instance(tmp_path,damage):
    folder=tmp_path/'model';b,cfg=fixture(folder)
    if damage=='pid':
        with pytest.raises(ValueError):b.analyze_model(folder,dict(pid=8),cfg)
        return
    name=dict(capture='timeline/capture.json',token='tokens.json',scope='scope_producers.json',
        session='timeline/receipt.json',warmup='warmup_completed.json')[damage]
    value=json.loads((folder/name).read_text())
    if damage=='warmup':value['completed_count']=2
    elif damage=='capture':value['session_id']='foreign'
    elif damage=='token':value['token_ids']=[[99],[18]]
    elif damage=='scope':value[0]['run_id']='foreign'
    else:value['close_code']=4
    (folder/name).write_text(json.dumps(value),encoding='utf8')
    with pytest.raises(ValueError):b.analyze_model(folder,dict(pid=7),cfg)
