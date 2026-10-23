"""New batch contract file chain. CPU doubles do not qualify target CUDA runs."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.test_cupti_input_pilot import load, prompt
from tests.test_cupti_model_policy_reconnect import put, sha

ROOT=Path(__file__).resolve().parents[1]


def plan(role='Engineering'):
    # A small CPU fixture, NOT an authorized GPU matrix or run budget.
    return dict(schema_version='CUPTI-INPUT-PLAN/0.3.0',role=role,
        conditions=[dict(input_tokens=512,batch_size=1),dict(input_tokens=512,batch_size=2)],
        blocks=2,orders=[['G512B1P','G512B2P'],['G512B2P','G512B1P']],
        comparisons=[dict(low='G512B1P',high='G512B2P',role='PRIMARY',token_indices=[0,1])])


def output_policy(batch,role='Engineering'):
    return dict(version='cupti-output-validation/0.3.0',batch_size=batch,output_tokens=2,
        eos_policy='ANY_SAMPLE_EOS_REJECT_WHOLE_INVOCATION',
        mode='EXACT_REFERENCE' if role=='Pilot' else 'OBSERVED_ENGINEERING',
        expected_token_ids=[[17+j for j in range(batch)],[27+j for j in range(batch)]] if role=='Pilot' else None)


def test_full_ordered_batch_identity_and_actual_tensor_rows_not_single_row_digest():
    c=load('cupti_input_contract');source=prompt(512);before=deepcopy(source)
    p=c.batch_prompt(source,2)
    assert source==before and [r['sample_index'] for r in p['samples']]==[0,1]
    value=c.input_identity(p,512,batch_size=2,version='cupti-input-identity/0.2.0')
    ids=[list(range(100,132))*16]*2;masks=[[1]*512]*2
    digest=lambda v:hashlib.sha256(json.dumps(v,separators=(',',':')).encode()).hexdigest()
    assert value['shape']==[2,512] and value['sample_indices']==[0,1]
    assert value['input_ids_sha256']==digest(ids) and value['attention_mask_sha256']==digest(masks)
    assert value['batch_sha256']==digest(dict(shape=[2,512],sample_indices=[0,1],input_ids=ids,attention_mask=masks))
    assert value['batch_sha256']!=c.input_identity(source,512)['batch_sha256']
    assert c.tensor_rows(p,value)==(ids,masks)
    bad=deepcopy(p);bad['samples'][1]['attention_mask'][9]=0
    with pytest.raises(ValueError,match='MASK'):c.input_identity(bad,512,batch_size=2,version=value['schema_version'])
    bad=deepcopy(p);bad['samples'].reverse()
    with pytest.raises(ValueError,match='SAMPLE_ORDER'):c.input_identity(bad,512,batch_size=2,version=value['schema_version'])
    with pytest.raises(ValueError,match='INPUT_SHAPE'):c.input_identity(p,512)
    bad=deepcopy(p);bad['samples'][1]['input_ids']=[200+i for i in range(32)]*16
    with pytest.raises(ValueError,match='BATCH_REPEATED_INPUT'):
        c.input_identity(bad,512,batch_size=2,version=value['schema_version'])


def test_explicit_batch_plan_binds_slot_batch_and_rejects_old_or_spliced_roles():
    c=load('cupti_input_contract');p=plan('Pilot');slots=c.schedule('cpu-batch','a'*40,plan=p)
    assert [(s['block'],s['position'],s['input_tokens'],s['batch_size']) for s in slots]==[
        (1,1,512,1),(1,2,512,2),(2,1,512,2),(2,2,512,1)]
    assert [s['run_id'] for s in slots]==['cpu-batch-b1-G512B1P-pass1','cpu-batch-b1-G512B2P-pass1',
        'cpu-batch-b2-G512B2P-pass1','cpu-batch-b2-G512B1P-pass1']
    from exposedpath.gate11_pilot import validate_binding
    validate_binding(slots[1]['producer_binding'])
    bad=deepcopy(slots[1]['producer_binding']);bad['batch_size']=1
    with pytest.raises(ValueError,match='CUPTI'):validate_binding(bad)
    old=dict(schema_version='CUPTI-INPUT-PLAN/0.2.0',role='Pilot',input_lengths=[512],
        blocks=1,orders=[[512]],comparisons=[])
    oldslot=c.schedule('old','a'*40,plan=old)[0]
    assert oldslot['batch_size']==1 and oldslot['run_id']=='old-b1-G512P-pass1'
    bad=deepcopy(p);bad['role']='Formal'
    with pytest.raises(ValueError,match='CUPTI'):c.schedule('bad','a'*40,plan=bad)


def test_two_by_batch_actual_output_never_broadcast_or_per_sample_repeat():
    c=load('cupti_input_contract');p=output_policy(2,'Pilot')
    c.validate_output_policy(p,'Pilot',batch_size=2)
    result=c.validate_tokens([[17,18],[27,28]],p,dict(vocab_size=100,eos_token_ids=[99]))
    assert result['actual_token_ids']==[[17,18],[27,28]] and result['output_shape']==[2,2]
    for ids in ([[17],[27]],[[17,18]],[[17,18],[27,99]],[[17,18],[27,True]],[[18,17],[27,28]]):
        with pytest.raises(ValueError,match='TOKEN'):c.validate_tokens(ids,p,dict(vocab_size=100,eos_token_ids=[99]))
    bad=deepcopy(p);bad['expected_token_ids']=[[17],[27]]
    with pytest.raises(ValueError,match='OUTPUT_POLICY'):c.validate_output_policy(bad,'Pilot',batch_size=2)
    with pytest.raises(ValueError,match='OUTPUT_POLICY'):c.validate_output_policy(output_policy(2),'Pilot',batch_size=2)


def delivery(p=None):
    c=load('cupti_input_contract');p=plan() if p is None else p
    inputs={}
    for condition in p['conditions']:
        n,b=condition['input_tokens'],condition['batch_size'];key=f'G{n}B{b}P'
        inputs[key]=dict(path=f'input_{n}_B{b}.json',sha256='b'*64,
            identity=c.input_identity(c.batch_prompt(prompt(n),b),n,batch_size=b,version='cupti-input-identity/0.2.0'),
            output_validation=output_policy(b,p['role']))
    return dict(schema_version='CUPTI-INPUT-PLAN/0.3.0',plan=p,inputs=inputs,
        model_limits=dict(vocab_size=151936,max_position_embeddings=32768,eos_token_ids=[151645]),
        model_config_sha256='f'*64,native_commit=c.NATIVE,controller_commit='a'*40,code_root=str(ROOT),
        producer_policy_sha256='p'*64,activity_policy_version='cupti-api22-activity-policy/0.2.0',**c.POLICIES)


def test_new_model_config_and_P_cache_bind_full_batch_without_unlocking_old_versions():
    c=load('cupti_input_contract');controller=load('cupti_input_pilot');model=load('cupti_timeline_model')
    d=delivery();slot=c.schedule('cpu-batch','a'*40,plan=d['plan'])[1]
    cfg=controller.one_configuration(d,slot);mc=cfg['model_contract']
    mc['session']=dict(activity_policy_version=mc['activity_policy_version'])
    assert cfg['schema_version']=='cupti-timeline-stage-b/0.5.0'
    assert mc['schema_version']=='cupti-timeline-model/0.5.0' and mc['batch_size']==2
    assert model.validate_contract(mc)==c.NATIVE
    from exposedpath.observation_preparation import Execution
    p=model.preparer(mc)
    assert type(p).prepare is Execution.prepare and type(p).finish is Execution.finish
    assert p.binding['batch_size']==2 and p.binding['input_identity']==d['inputs']['G512B2P']['identity']
    bad=deepcopy(mc);bad['batch_size']=1
    with pytest.raises(ValueError,match='BATCH|SLOT'):model.validate_contract(bad)
    bad=deepcopy(mc);bad['schema_version']='cupti-timeline-model/0.4.0'
    with pytest.raises(ValueError,match='MODEL|PLAN'):model.validate_contract(bad)
    bad=deepcopy(mc);bad['output_tokens']=8
    with pytest.raises(ValueError,match='MODEL'):model.validate_contract(bad)


def test_complete_block_summary_keeps_B_as_one_invocation_and_preserves_signed_responses():
    c=load('cupti_input_contract');p=plan();slots=c.schedule('cpu-batch','a'*40,plan=p)
    rows=[]
    for s in slots:
        q,g=(20,100) if s['batch_size']==1 else (10,200)
        rows.append(dict(slot=s,metrics=[dict(token_index=i,coe_ns=q,phase_gpu_union_ns=g,
            coe_phase_ratio=q/1000,batch_size=s['batch_size'],completion_unit='WHOLE_BATCH_INVOCATION') for i in (0,1)]))
    result=c.summarize(slots,rows,plan=p)
    assert result['statistical_unit']=='COMPLETE_BLOCK_NOT_TOKEN_OR_BATCH_SAMPLE'
    assert result['complete_blocks']==[1,2] and len(result['comparisons'])==4
    assert [(v['delta_coe_ns'],v['R_ns']) for v in result['comparisons']]==[(-10,-30)]*4
    assert all(v['comparison_axis']=='BATCH_SIZE' and v['low_batch_size']==1 and v['high_batch_size']==2 for v in result['comparisons'])
    with pytest.raises(ValueError,match='INCOMPLETE'):c.summarize(slots,rows[:-1],plan=p)
    bad=deepcopy(rows);bad[1]['slot']['batch_size']=1
    with pytest.raises(ValueError,match='SLOT'):c.summarize(slots,bad,plan=p)
    zero=deepcopy(rows);zero[0]['metrics'][0]['phase_gpu_union_ns']=0
    z=c.summarize(slots,zero,plan=p)
    assert z['comparisons'][0]['R_ns'] is None and z['comparisons'][0]['R_exact'] is None
    bad=deepcopy(rows);bad[0]['metrics'][0]['batch_size']=2
    with pytest.raises(ValueError,match='METRIC_BATCH_IDENTITY'):c.summarize(slots,bad,plan=p)


@pytest.mark.parametrize('early',[False,True])
@pytest.mark.parametrize('role',['Engineering','Pilot'])
def test_original_runner_P_whole_batch_completion_records_actual_vectors_and_EOS(tmp_path,monkeypatch,early,role):
    import os
    from contextlib import nullcontext
    from exposedpath import runner
    from tests.test_runner_token_ready import _FakeInput,_FakeModel,_FakeToken,_patch_cpu_torch
    _patch_cpu_torch(monkeypatch)
    monkeypatch.setattr(runner.torch.cuda,'current_device',lambda:0)
    monkeypatch.setattr(runner.torch.cuda,'is_initialized',lambda:False)
    monkeypatch.setattr(runner.torch.cuda.nvtx,'mark',lambda _:None)
    c=load('cupti_input_contract');controller=load('cupti_input_pilot');model=load('cupti_timeline_model')
    d=delivery(plan(role));slot=c.schedule('cpu-batch','a'*40,plan=d['plan'])[1]
    mc=controller.one_configuration(d,slot)['model_contract'];mc['session']=dict(activity_policy_version=mc['activity_policy_version'])
    preparation=model.preparer(mc);events=[]
    class Input(_FakeInput):shape=(2,512)
    class Session:
        def __enter__(self):events.append('open');return self
        def __exit__(self,*a):events.append('close')
        def nvtx_sink(self,nvtx):return nullcontext()
    fields=dict(experiment_id='cpu',wmpc_id='w',run_id=slot['run_id'],run_role=role.upper(),data_role=role,
        pass_id='pass1',attempt_id='once',pid=os.getpid(),wmpc_manifest_sha256='a'*64,prompt_sha256='b'*64,
        runner_git_commit=c.NATIVE,runner_git_dirty=False,runner_source_sha256='c'*64)
    if role=='Pilot':fields['pilot']=slot['producer_binding']
    vectors=[[10,11]]*6+([[17,151645]] if early else [[17,18],[27,28]])
    resident=dict(model=_FakeModel(iter(_FakeToken(v,events) for v in vectors)),input_ids=Input(),attention_mask=object(),eos_token_id=151645)
    def observed(identity,result):
        model.record_batch_tokens(mc,tmp_path,preparation,identity,result,mc['input_identity'])
    receipt=model.resident_capture(runner,Session(),resident,fields,tmp_path,preparation,observed)
    assert json.loads(Path(receipt).read_text())['status']==('INCOMPLETE' if early else 'COMPLETE')
    tokens=json.loads((tmp_path/'tokens.json').read_text())
    assert events==(['open','host_read','close'] if early else ['open','host_read','host_read','close'])
    assert tokens['token_ids']==([[17,151645]] if early else [[17,18],[27,28]])
    assert tokens['output_shape']==([1,2] if early else [2,2])
    assert tokens['status']==('REJECTED_ACTUAL_OUTPUT' if early else 'COMPLETE')
    assert tokens['completion_unit']=='WHOLE_BATCH_INVOCATION'
    if early:assert tokens['eos_hits']==[dict(token_index=0,sample_index=1,token_id=151645)]
    else:
        assert tokens['preparation']['consumed_token_indices']==[0,1]
        assert len(json.loads((tmp_path/'producer/host_boundaries.json').read_text()))==3


def batch_files(root,batch=2,role='Engineering',model_cfg=None):
    """Explicit Host-SDK/timeline doubles, never target model execution."""
    from tests.test_cupti_configured_plan import plan as oldplan,planned_files
    c=load('cupti_input_contract');controller=load('cupti_input_pilot')
    oldslot=c.schedule('cpu-old','a'*40,plan=oldplan((512,),((512,),),role=role))[0]
    b,cfg=planned_files(root,oldslot)
    p=dict(schema_version='CUPTI-INPUT-PLAN/0.3.0',role=role,conditions=[dict(input_tokens=512,batch_size=batch)],
        blocks=1,orders=[[f'G512B{batch}P']],comparisons=[])
    slot=c.schedule('cpu-batch','a'*40,plan=p)[0]
    if model_cfg is not None:p=model_cfg['input_plan'];slot=model_cfg['input_slot']
    d=delivery(p);cfg.update(controller.one_configuration(d,slot))
    mc=cfg['model_contract'];input_path=root/f'input_512_B{batch}.json'
    put(input_path,c.batch_prompt(prompt(512),batch))
    mc.update(prompt=str(input_path),prompt_sha256=sha(input_path),session=dict(session_id=slot['run_id'],
        activity_policy_version=mc['activity_policy_version']))
    if model_cfg is not None:mc=deepcopy(model_cfg);cfg['model_config']=str(root.parent/'model_config.json')
    cfg['model_contract']=mc
    put(root/'model_config.json',mc)
    cfg.update(prompt_sha256=mc['prompt_sha256'],session_id=slot['run_id'])
    old_id=oldslot['run_id']
    def identity(v):
        if isinstance(v,dict):return {k:identity(x) for k,x in v.items()}
        if isinstance(v,list):return [identity(x) for x in v]
        if isinstance(v,str):
            if ':' in v and v.split(':',1)[0] in ('EXPOSEDPATH_DRAIN_V1','EXPOSEDPATH_BOUNDARY_V1','EXPOSEDPATH_JSON_V1'):
                prefix,payload=v.split(':',1);return prefix+':'+json.dumps(identity(json.loads(payload)),sort_keys=True,separators=(',',':'))
            if v==old_id:return slot['run_id']
        return v
    for n in ('tokens.json','scope_producers.json','producer/pass_identity.json','producer/host_boundaries.json',
              'producer/drain_ledger.json','timeline/capture.json'):
        put(root/n,identity(json.loads((root/n).read_text())))
    ids=[[17+j for j in range(batch)],[27+j for j in range(batch)]]
    tokens=json.loads((root/'tokens.json').read_text());tokens.update(schema_version='cupti-batch-token-observation/0.1.0',
        status='COMPLETE',input_slot=slot,input_identity=mc['input_identity'],batch_size=batch,
        token_ids=ids,output_shape=[2,batch],sample_indices=list(range(batch)),
        completion_unit='WHOLE_BATCH_INVOCATION',eos_hits=[],actual_output_tokens_per_sample=[2]*batch)
    if role=='Pilot':tokens['pilot']=slot
    put(root/'tokens.json',tokens)
    ledger=json.loads((root/'producer/pass_identity.json').read_text())
    ledger.update(wmpc_manifest_sha256=sha(Path(cfg['model_config'])),prompt_sha256=mc['prompt_sha256'])
    if role=='Pilot':ledger['pilot']=slot['producer_binding']
    put(root/'producer/pass_identity.json',ledger)
    receipt=json.loads((root/'producer/producer_receipt.json').read_text())
    if role=='Pilot':receipt['pilot']=slot['producer_binding']
    for entry in receipt['files'].values():
        file=root/'producer'/entry['filename'];entry.update(sha256=sha(file),size_bytes=file.stat().st_size)
    put(root/'producer/producer_receipt.json',receipt)
    setup=json.loads((root/'setup.json').read_text());setup.update(schema_version='cupti-model-setup/0.2.0',
        input_slot=slot,input_plan=p,input_identity=mc['input_identity'],input_shape=[batch,512],
        batch_size=batch,sample_indices=list(range(batch)),output_shape_expected=[2,batch],
        completion_unit='WHOLE_BATCH_INVOCATION',input_sha256=mc['prompt_sha256'],output_validation=mc['output_validation'],
        dtype='torch.float16',cuda_version='12.4',model_config_sha256=mc['model_config_sha256'],
        model_limits=mc['model_limits'])
    if role=='Pilot':setup['pilot']=slot
    put(root/'setup.json',setup)
    raw=json.loads((root/'timeline/capture.json').read_text());raw['session_id']=slot['run_id']
    for call in raw['callbacks']:
        if call['name'] in ('cudaMemcpyAsync','cuMemcpyDtoHAsync_v2') and call['params'] is not None:
            call['params']['count']=batch*8
    for row in raw['records']:
        if row['kind']=='MEMCPY':row['bytes']=batch*8
    put(root/'timeline/capture.json',raw)
    scopes=json.loads((root/'scope_producers.json').read_text())
    for i,s in enumerate(scopes):
        s.update(session_id=slot['run_id'],actual_token_ids=ids[i],schema_version='cupti-batch-token-scope-producer/0.1.0',
            batch_size=batch,sample_indices=list(range(batch)),input_identity=mc['input_identity'],completion_unit='WHOLE_BATCH_INVOCATION')
    put(root/'scope_producers.json',scopes)
    sr=json.loads((root/'timeline/receipt.json').read_text());sr.update(session_id=slot['run_id'],capture_sha256=sha(root/'timeline/capture.json'))
    if model_cfg is not None:sr.update(client_sha256=mc['session']['client_sha256'],cupti_sha256=mc['session']['cupti_sha256'])
    put(root/'timeline/receipt.json',sr)
    result=json.loads((root/'model_result.json').read_text());result.update(schema_version='cupti-timeline-model-result/0.5.0',
        input_slot=slot,batch_size=batch,input_identity=mc['input_identity'],config_sha256=sha(Path(cfg['model_config'])),
        control_commit=mc['control_commit'],model_entry_sha256=sha(ROOT/'scripts/cupti_timeline_model.py'))
    if role=='Pilot':result['pilot']=slot
    for k,n in dict(token_sha256='tokens.json',scope_producers_sha256='scope_producers.json',setup_sha256='setup.json',
        capture_sha256='timeline/capture.json',session_receipt_sha256='timeline/receipt.json',
        producer_receipt_sha256='producer/producer_receipt.json').items():result[k]=sha(root/n)
    put(root/'model_result.json',result)
    return b,cfg


@pytest.mark.parametrize('batch',[1,2,4])
def test_new_batch_real_file_chain_keeps_original_COE_and_extended_budgets_distinct(tmp_path,batch):
    root=tmp_path/'model';b,cfg=batch_files(root,batch)
    result=b.analyze_model(root,dict(pid=7),cfg)
    assert result['schema_version']=='cupti-timeline-model-review/0.5.0'
    assert result['batch_size']==batch and result['output_shape']==[2,batch]
    assert [r['result']['coe_ns'] for r in result['token_results']]==[20,1]
    index=json.loads((root/'batch_accounting/index.json').read_text())
    assert index['completion_unit']=='WHOLE_BATCH_INVOCATION' and index['batch_size']==batch
    assert set(index['files'])=={'original_a','coe','extended_completion_exposure'}
    data={k:json.loads((root/'batch_accounting'/v['filename']).read_text()) for k,v in index['files'].items()}
    assert data['original_a']['windows'][0]['budgets_ns']==dict(host=93,submit=22,non_submit=0,device_wait=16,residual=34,unattributed=0)
    assert data['coe']['windows'][0]['coe_union_ns']==21
    req=data['extended_completion_exposure']['windows'][0]
    assert req['budgets_ns']==dict(host=92,submit=18,non_submit=0,completion_exposure=21,residual=34,unattributed=0)
    assert req['new_migration_ns']==5 and req['old_wait_overlap_ns']==16
    assert req['migration_source_ns']==dict(submit=4,host=1)
    for v in index['files'].values():assert sha(root/'batch_accounting'/v['filename'])==v['sha256']


def test_runtime_driver_sync_coverage_uses_parent_identity_once_and_keeps_real_gaps():
    from tests.test_cupti_a_migration import fixture
    from analysis.cupti_a_migration import audit_run
    raw,scopes,saved=fixture()
    parent=raw['callbacks'][2]
    child=dict(parent,id=20,domain='DRIVER',parent_id=parent['id'],correlation=90,
        name='cuStreamSynchronize',cbid=126)
    raw['callbacks'].append(child)
    next(r for r in raw['records'] if r['id']=='s0')['correlation']=90
    good=audit_run(raw,scopes,saved)
    assert good['gaps']==[] and good['windows'][0]['original_budgets_ns']['device_wait']==2
    same=deepcopy(raw);same['callbacks'][-1]['correlation']=parent['correlation']
    next(r for r in same['records'] if r['id']=='s0')['correlation']=parent['correlation']
    assert audit_run(same,scopes,saved)['gaps']==[]
    duplicate=deepcopy(raw);duplicate['records'].append(dict(next(r for r in raw['records'] if r['id']=='s0'),id='duplicate'))
    assert any(g['reason']=='PHYSICAL_SYNC_DUPLICATE' for g in audit_run(duplicate,scopes,saved)['gaps'])
    bad=deepcopy(raw);bad['callbacks'][-1]['parent_id']=2
    with pytest.raises(ValueError,match='CALL_PARENT_SCOPE'):audit_run(bad,scopes,saved)


def test_saved_model_template_allows_only_bound_execution_fields(tmp_path):
    root=tmp_path/'model';b,cfg=batch_files(root)
    # This is how run_capture actually extends the per-run template.
    full=json.loads(Path(cfg['model_config']).read_text())
    cfg['model_contract']={k:v for k,v in full.items() if k not in ('prompt','prompt_sha256','session')}
    result=b.analyze_model(root,dict(pid=7),cfg)
    assert result['batch_accounting']['status']=='COMPLETE_WINDOW_SOURCE_PREVIEW_NOT_FORMAL'
    reader=load('cupti_batch_accounting');summary=reader.read_summary(root,result,cfg)
    assert summary['batch_size']==2 and summary['run_id']==cfg['run_id']
    bad=deepcopy(cfg);bad['run_id']='another-invocation'
    with pytest.raises(ValueError,match='INDEX_IDENTITY'):reader.read_summary(root,result,bad)
    index=root/'batch_accounting/index.json';before=index.read_bytes()
    with (root/'tokens.json').open('a',encoding='utf8') as f:f.write(' ')
    with pytest.raises(ValueError,match='SOURCE_HASH:tokens.json'):reader.read_summary(root,result,cfg)
    assert index.read_bytes()==before


@pytest.mark.parametrize('damage,reason',[('hash','CONSUMER_FILE:'),('origin','PARENT_ORIGIN:'),('missing','FILE_INDEX')])
def test_batch_cpu_overlay_refuses_wrong_source_before_loading(tmp_path,damage,reason):
    import shutil,subprocess,sys
    binding=load('cupti_model_consumer');consumer=tmp_path/'consumer'
    rows=[]
    for name in binding.BATCH_FILES:
        path=consumer/name;path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,path)
        rows.append(dict(path=name,sha256=sha(path),bytes=path.stat().st_size))
    cfg=dict(schema_version='cupti-timeline-stage-b/0.5.0',consumer_root=str(consumer),
        code_root=str(ROOT),consumer_files=rows)
    if damage=='hash':(consumer/'analysis/cupti_a_migration.py').write_bytes(b'# altered source\n')
    if damage=='origin':cfg['code_root']=str(tmp_path/'untrusted-root')
    if damage=='missing':cfg['consumer_files']=rows[:-1]
    config=tmp_path/'cfg.json';put(config,cfg)
    boot=('import sys,runpy,json;sys.path.insert(0,sys.argv[1]);'
        'runpy.run_path(sys.argv[2])["bind_consumer"](json.load(open(sys.argv[3])))')
    proc=subprocess.run([sys.executable,'-I','-S','-c',boot,str(ROOT),
        str(ROOT/'scripts/cupti_model_consumer.py'),str(config)],capture_output=True,timeout=20)
    assert proc.returncode!=0 and ('CUPTI_CONSUMER_'+reason).encode() in proc.stderr


@pytest.mark.parametrize('damage,reason',[
    ('copy_size','TOKEN_COPY_SIZE'),('unknown','SUBMIT_EFFECT_EFFECT_BRIDGE'),
    ('missing_effect','SUBMIT_EFFECT_POSITIVE_EFFECT_MISSING'),('drain','DRAIN_IDENTITY'),
    ('token','TOKEN_VALUES_OR_EOS'),('input','INPUT_IDENTITY')])
def test_batch_real_chain_preserves_specific_failure_and_never_publishes_budget(tmp_path,damage,reason):
    root=tmp_path/'model';b,cfg=batch_files(root)
    raw=json.loads((root/'timeline/capture.json').read_text());result=json.loads((root/'model_result.json').read_text())
    if damage in ('copy_size','unknown','missing_effect'):
        if damage=='copy_size':next(c for c in raw['callbacks'] if c['name']=='cudaMemcpyAsync')['params']['count']=8
        if damage=='unknown':next(c for c in raw['callbacks'] if c['name']=='cudaLaunchKernel')['name']='cudaUnknownLaunch'
        if damage=='missing_effect':raw['records']=[r for r in raw['records'] if r['kind']!='MEMSET']
        put(root/'timeline/capture.json',raw);result['capture_sha256']=sha(root/'timeline/capture.json')
        sr=json.loads((root/'timeline/receipt.json').read_text());sr['capture_sha256']=result['capture_sha256']
        put(root/'timeline/receipt.json',sr);result['session_receipt_sha256']=sha(root/'timeline/receipt.json')
    else:
        name='producer/drain_ledger.json' if damage=='drain' else 'tokens.json'
        v=json.loads((root/name).read_text())
        if damage=='drain':v['drains'][0]['status']='FAILED'
        if damage=='token':v['token_ids'][0]=[17]
        if damage=='input':v['input_identity']['batch_sha256']='0'*64
        put(root/name,v)
        if damage=='drain':
            receipt=json.loads((root/'producer/producer_receipt.json').read_text())
            receipt['files']['drain_ledger.json'].update(sha256=sha(root/name),size_bytes=(root/name).stat().st_size)
            put(root/'producer/producer_receipt.json',receipt);result['producer_receipt_sha256']=sha(root/'producer/producer_receipt.json')
        else:result['token_sha256']=sha(root/'tokens.json')
    put(root/'model_result.json',result)
    with pytest.raises(ValueError,match=reason):b.analyze_model(root,dict(pid=7),cfg)
    assert not (root/'batch_accounting/original_a.json').exists()


from tests.test_cupti_pilot_reference_dispatch import sealed,scene,reseal_package,read


@pytest.mark.parametrize('role,fail_second',[('Engineering',False),('Pilot',False),('Engineering',True)])
def test_batch_actual_config_controller_isolated_consumer_and_block_summary(scene,monkeypatch,role,fail_second):
    """Real contracts/receipts/CPU consumer; model/device/resource queries doubled."""
    import shutil,subprocess,sys,jsonschema
    pilot,b,stage,m,c,package,root,checks=scene
    helper=load('cupti_input_contract');p=plan(role)
    for n in (512,1024,2048):(package/f'input_{n}.json').unlink()
    d=delivery(p);c.update(schema_version=helper.BATCH_PLAN_VERSION,plan=p,inputs=d['inputs'],
        slots=helper.schedule(c['batch_id'],c['controller_commit'],plan=p),budget=pilot.fixed_budget(p))
    for condition in p['conditions']:
        n,B=condition['input_tokens'],condition['batch_size'];key=f'G{n}B{B}P'
        put(package/c['inputs'][key]['path'],helper.batch_prompt(prompt(n),B))
        c['inputs'][key]['sha256']=sha(package/c['inputs'][key]['path'])
    ref=dict(model_type='qwen2',vocab_size=151936,max_position_embeddings=32768,eos_token_id=151645)
    put(package/'model_config_reference.json',ref);c['model_config_sha256']=sha(package/'model_config_reference.json')
    c['model_limits']=helper.model_limits(ref);model=root/'actual_model_config_only';model.mkdir();put(model/'config.json',ref)
    c['model']=str(model)
    for name in ('cupti_input_contract.py','cupti_timeline_model.py','cupti_timeline_b.py','cupti_model_consumer.py','cupti_batch_accounting.py'):
        shutil.copyfile(ROOT/'scripts'/name,package/name)
    shutil.copyfile(ROOT/'exposedpath/gate11_pilot.py',package/'producer_policy.py')
    c['producer_policy_sha256']=sha(package/'producer_policy.py')
    consumer=load('cupti_model_consumer')
    for name in consumer.BATCH_FILES:
        target=package/'consumer'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    c['consumer_files']=[dict(path=n,bytes=(ROOT/n).stat().st_size,sha256=sha(ROOT/n)) for n in consumer.BATCH_FILES]
    c['cpu_sources']=[dict(path=v.relative_to(package).as_posix(),sha256=sha(v)) for v in package.rglob('*.py')]
    put(package/'delivery.json',c);reseal_package(package)
    # No contract or receipt validator is stubbed. Default path stays CPU-only.
    assert pilot.main(['--package',str(package)])==0
    static,_=pilot.locations(c,m,'A');sr=read(static/'receipt.json')
    assert sr['planned_model_processes']==4 and sr['actual_model_processes']==sr['actual_cupti_sessions']==0
    model_count=0;commands=[]
    def command(argv,cwd,log,**kw):
        nonlocal model_count
        commands.append((Path(log).name,kw['timeout']))
        if Path(log).name=='one_model':
            mc=read(Path(cwd)/'model_config.json');B=mc['batch_size']
            assert mc['input_identity']['shape']==[B,512] and read(mc['prompt'])['batch_size']==B
            assert Path(mc['prompt']).name==f'input_512_B{B}.json'
            assert mc['role']==role and '--run-reviewed-model' in argv
            batch_files(Path(cwd)/'model',B,role,model_cfg=mc)
            if fail_second and model_count==1:
                capture=Path(cwd)/'model/timeline/capture.json';raw=read(capture);raw['quality']['overflow']=1;put(capture,raw)
                rr=read(Path(cwd)/'model/model_result.json');rr['capture_sha256']=sha(capture)
                ss=read(Path(cwd)/'model/timeline/receipt.json');ss['capture_sha256']=rr['capture_sha256']
                put(Path(cwd)/'model/timeline/receipt.json',ss);rr['session_receipt_sha256']=sha(Path(cwd)/'model/timeline/receipt.json')
                put(Path(cwd)/'model/model_result.json',rr)
            model_count+=1;proc=dict(pid=7,status='EXITED',exit_code=0,timed_out=False)
        else:
            # Keep the sealed native checkout, its actual modules and delivery
            # overlay. Only Python/site paths are explicit local doubles.
            args=list(argv);args[0]=sys.executable
            args[args.index(c['code_root'])]=str(root/'code')
            args[args.index(c['site_root'])]=str(Path(jsonschema.__file__).parents[1])
            acfg=read(Path(cwd)/'analysis_config.json');acfg['code_root']=str(root/'code')
            put(Path(cwd)/'analysis_config.json',acfg)
            r=subprocess.run(args,cwd=cwd,env=kw['env'],capture_output=True,timeout=30)
            Path(log).with_suffix('.stderr').write_bytes(r.stderr)
            proc=dict(pid=99,status='EXITED',exit_code=r.returncode,timed_out=False)
        put(Path(log).with_suffix('.process.json'),proc)
        if proc['exit_code']:raise ValueError('CPU_ACTUAL_READER_FAILED')
        return proc
    monkeypatch.setattr(m,'command',command)
    rc=pilot.run(package,enabled=True,reviewed=c['reviewed_a_receipt_sha256'],
        reviewed_event=c['reviewed_event_receipt_sha256'],reviewed_static=sha(static/'receipt.json'))
    out,_=pilot.locations(c,m,'B');receipt=read(out/'receipt.json')
    errors='\n'.join(v.read_text() for v in out.rglob('same_run_analysis.stderr'))
    assert rc==(2 if fail_second else 0),errors
    assert model_count==(2 if fail_second else 4)
    assert commands==[('one_model',300),('same_run_analysis',180)]*model_count
    if fail_second:
        assert [s['status'] for s in receipt['slots']]==['COMPLETE_PENDING_REVIEW','BLOCKED','NOT_RUN','NOT_RUN']
        assert receipt['complete_blocks']==[] and not (out/'summary.json').exists()
    else:
        summary=read(out/'summary.json');assert summary['complete_blocks']==[1,2]
        assert len(summary['comparisons'])==4 and len(summary['rows'])==4
        assert all(v['delta_coe_ns']==0 and v['R_ns']==0 for v in summary['comparisons'])
        assert all(set(v['accounting']['views'])=={'original_a','coe','extended_completion_exposure'} for v in summary['rows'])
        assert all(read(out/'runs'/s['run_id']/'execution_plan.json')['batch_size']==s['batch_size'] for s in c['slots'])
        assert all(read(out/'runs'/s['run_id']/'model/consumer_binding.json')['schema_version']=='cupti-model-consumer-binding/0.2.0' for s in c['slots'])
