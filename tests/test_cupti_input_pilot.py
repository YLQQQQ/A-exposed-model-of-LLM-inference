"""Configuration/identity/Pilot checks; CPU oracles are not target CUDA evidence."""
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import zipfile

import pytest

ROOT=Path(__file__).resolve().parents[1]


def load(name):
    path=ROOT/'scripts'/(name+'.py')
    assert path.is_file(), 'missing unified CUPTI input/Pilot entry'
    spec=importlib.util.spec_from_file_location('_input_'+name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def prompt(length):
    return dict(fixed_input_tokens=length,samples=[dict(sample_index=0,
        input_ids=list(range(100,132))*(length//32),attention_mask=[1]*length)])


def contract(slot):
    m=load('cupti_input_contract')
    return dict(schema_version='cupti-timeline-model/0.3.0',input_tokens=slot['input_tokens'],batch_size=1,
        output_tokens=2,warmup_count=3,repeat_count=1,role='Pilot',completion_policy='HOST_READABLE_P',
        model_process_budget=1,nsight_profiles=0,torch_profiler=False,run_id=slot['run_id'],pilot=slot,
        native_commit='6c744bf52daff3fc54571e264a0c34e3207aa1df',control_commit='a'*40,
        activity_policy_version='cupti-api22-activity-policy/0.2.0',
        session=dict(activity_policy_version='cupti-api22-activity-policy/0.2.0'),**m.POLICIES)


def test_generic_input_identity_is_not_a_gpu_qualification_or_finite_length_switch():
    m=load('cupti_input_contract')
    model=dict(model_type='qwen2',vocab_size=151936,max_position_embeddings=32768,eos_token_id=151645)
    for n in (512,1024,1536,2048):
        r=m.input_identity(prompt(n),n,model)
        assert r['shape']==[1,n] and 'qualified' not in r and r['algorithm']=='SHA256_COMPACT_UTF8_JSON_IN_ORDER'
    bad=prompt(1024);bad['samples'][0]['attention_mask'][2]=0
    with pytest.raises(ValueError,match='MASK'):m.input_identity(bad,1024,model)
    with pytest.raises(ValueError,match='INPUT_SHAPE'):m.input_identity(prompt(512),1024,model)
    bad=prompt(1024);bad['samples'][0]['input_ids'][-1]+=1
    with pytest.raises(ValueError,match='CONSTRUCTION'):m.input_identity(bad,1024,model)


def test_exact_nine_slot_schedule_new_role_and_unchanged_P_methods():
    m=load('cupti_input_contract');rows=m.schedule('cpu-three','a'*40)
    assert [(r['block'],r['position'],r['input_tokens']) for r in rows]==[
        (1,1,512),(1,2,1024),(1,3,2048),(2,1,1024),(2,2,2048),(2,3,512),
        (3,1,2048),(3,2,512),(3,3,1024)]
    model=load('cupti_timeline_model')
    from exposedpath.observation_preparation import Execution
    for row in rows:
        c=contract(row);assert model.validate_contract(c)==c['native_commit']
        p=model.preparer(c)
        assert type(p).prepare is Execution.prepare and type(p).finish is Execution.finish
        assert p.axis is True and p.variant=='P' and p.binding['input_tokens']==row['input_tokens']
    for key,value in [('role','Engineering'),('input_tokens',768),('output_tokens',16),('batch_size',2)]:
        c=contract(rows[0]);c[key]=value
        with pytest.raises(ValueError):model.validate_contract(c)
    c=contract(rows[0]);c['pilot']['position']=3
    with pytest.raises(ValueError):model.validate_contract(c)


def test_complete_blocks_keep_signed_R_and_reject_splicing():
    m=load('cupti_input_contract');slots=m.schedule('cpu-three','a'*40);rows=[]
    # COE decreases at 1024, then grows exactly proportionally. No epsilon.
    for slot in slots:
        coe,gpu={512:(20,100),1024:(10,200),2048:(40,400)}[slot['input_tokens']]
        rows.append(dict(slot=slot,metrics=[dict(token_index=i,coe_ns=coe,phase_gpu_union_ns=gpu,
            phase_ns=1000,coe_phase_ratio=coe/1000) for i in (0,1)]))
    r=m.summarize(slots,rows)
    assert r['complete_blocks']==[1,2,3] and len(r['comparisons'])==18
    first=r['comparisons'][0]
    assert (first['low'],first['high'],first['delta_coe_ns'],first['R_ns'])==(512,1024,-10,-30)
    end=next(v for v in r['comparisons'] if v['block']==1 and v['token_index']==0 and v['low']==512 and v['high']==2048)
    assert end['R_ns']==-40 and end['delta_coe_ns']==20
    with pytest.raises(ValueError,match='INCOMPLETE'):m.summarize(slots,rows[:-1])
    bad=deepcopy(rows);bad[-1]['slot']=slots[0]
    with pytest.raises(ValueError,match='SLOT'):m.summarize(slots,bad)
    zero=deepcopy(rows)
    for row in zero:
        if row['slot']['input_tokens']==512:row['metrics'][0]['phase_gpu_union_ns']=0
    z=m.summarize(slots,zero)
    assert next(v for v in z['comparisons'] if v['low']==512)['R_ns'] is None


def test_phase_metrics_use_phase_not_cumulative_W_and_preserve_completed_members():
    m=load('cupti_input_contract')
    raw=dict(records=[dict(id='old',kind='KERNEL',pid=7,device=0,context=1,stream=7,start=10,end=30),
        dict(id='new',kind='KERNEL',pid=7,device=0,context=1,stream=7,start=105,end=130),
        dict(id='copy',kind='MEMCPY',pid=7,device=0,context=1,stream=7,start=131,end=132),
        dict(id='api',kind='API',start=120,end=135),dict(id='sync',kind='API',start=136,end=140)])
    scope=dict(pid=7,device=0,context=1,stream=7,request_start=0,completion_end=145,copy_api='api',sync_api='sync')
    result=dict(members=['old','new','copy'],coe_ns=11,sync_intersection_ns=0,operation_wall_ns=20,terminal='copy')
    r=m.token_metrics(raw,scope,result,1,100)
    assert r['phase_gpu_union_ns']==26 and r['necessary_before_copy_ns']==35
    assert r['coe_ns']==11 and r['operation_gpu_union_ns']==11 and r['phase_ns']==45
    assert r['necessary_member_ids']==['old','new','copy'] and r['pure_host_blocking_ns'] is None
    bad=deepcopy(result);bad['members'].append('old')
    with pytest.raises(ValueError,match='MEMBER'):m.token_metrics(raw,scope,bad,1,100)
    bad=deepcopy(result);bad['terminal']='missing'
    with pytest.raises(ValueError,match='TERMINAL'):m.token_metrics(raw,scope,bad,1,100)
    with pytest.raises(ValueError,match='OPERATION_PHASE'):m.token_metrics(raw,scope,result,1,125)


def pilot_files(root,slot,*,model_cfg=None):
    """Synthetic file chain, with real producer schemas/labels; no GPU."""
    from tests.test_cupti_model1024 import finite_files
    from tests.test_cupti_model_policy_reconnect import put,sha
    b,c=finite_files(root);m=load('cupti_input_contract');mc=contract(slot)
    put(root/'input.json',prompt(slot['input_tokens']))
    ident=m.input_identity(prompt(slot['input_tokens']),slot['input_tokens'])
    mc.update(prompt=str(root/'input.json'),prompt_sha256=sha(root/'input.json'),input_identity=ident)
    if model_cfg is not None:mc=deepcopy(model_cfg)
    put(root/'model_config.json',mc)
    config_hash=sha(root.parent/'model_config.json') if model_cfg is not None else sha(root/'model_config.json')
    session_id=mc.get('session',{}).get('session_id','test')
    c.update(schema_version=m.CONTROL,model_contract=mc,pilot=slot,run_id=slot['run_id'],session_id=session_id,
        input_identity=ident,prompt_sha256=mc['prompt_sha256'])
    old=json.loads((root/'tokens.json').read_text())['identity']
    new=dict(old,run_id=slot['run_id'],run_role='PILOT',data_role='Pilot')
    def convert(v):
        if isinstance(v,dict):return {k:convert(x) for k,x in v.items()}
        if isinstance(v,list):return [convert(x) for x in v]
        if isinstance(v,str):
            if ':' in v and v.split(':',1)[0] in ('EXPOSEDPATH_DRAIN_V1','EXPOSEDPATH_BOUNDARY_V1','EXPOSEDPATH_JSON_V1'):
                a,p=v.split(':',1);return a+':'+json.dumps(convert(json.loads(p)),sort_keys=True,separators=(',',':'))
            if v==old['run_id']:return new['run_id']
            if v=='ENGINEERING':return 'PILOT'
            if v=='Engineering':return 'Pilot'
        return v
    for name in ('tokens.json','scope_producers.json','producer/pass_identity.json','producer/host_boundaries.json','producer/drain_ledger.json','timeline/capture.json'):
        value=convert(json.loads((root/name).read_text()));put(root/name,value)
    t=json.loads((root/'tokens.json').read_text());t.update(actual_input_tokens=slot['input_tokens'],pilot=slot,input_identity=ident);put(root/'tokens.json',t)
    ledger=json.loads((root/'producer/pass_identity.json').read_text())
    ledger.update(pilot=slot['producer_binding'],schema_version='exposedpath-pass-identity/0.2.0',
        wmpc_manifest_sha256=config_hash,prompt_sha256=mc['prompt_sha256'])
    put(root/'producer/pass_identity.json',ledger)
    producer=json.loads((root/'producer/producer_receipt.json').read_text())
    for value in producer['files'].values():
        p=root/'producer'/value['filename'];value.update(sha256=sha(p),size_bytes=p.stat().st_size)
    producer.update(pilot=slot['producer_binding'],run_role='PILOT',data_role='Pilot',schema_version='exposedpath-coe-pilot-producer/0.1.0')
    put(root/'producer/producer_receipt.json',producer)
    setup=json.loads((root/'setup.json').read_text());setup.update(pilot=slot,input_shape=[1,slot['input_tokens']],input_identity=ident,input_sha256=mc['prompt_sha256']);put(root/'setup.json',setup)
    raw=json.loads((root/'timeline/capture.json').read_text());raw['session_id']=session_id;put(root/'timeline/capture.json',raw)
    scopes=json.loads((root/'scope_producers.json').read_text())
    for s in scopes:s['session_id']=session_id
    put(root/'scope_producers.json',scopes)
    session=json.loads((root/'timeline/receipt.json').read_text());session.update(session_id=session_id,capture_sha256=sha(root/'timeline/capture.json'));put(root/'timeline/receipt.json',session)
    result=json.loads((root/'model_result.json').read_text());result.update(schema_version='cupti-timeline-model-result/0.3.0',role='Pilot',pilot=slot,config_sha256=config_hash)
    for key,name in dict(token_sha256='tokens.json',scope_producers_sha256='scope_producers.json',setup_sha256='setup.json',capture_sha256='timeline/capture.json',session_receipt_sha256='timeline/receipt.json',producer_receipt_sha256='producer/producer_receipt.json').items():result[key]=sha(root/name)
    put(root/'model_result.json',result)
    return b,c


@pytest.mark.parametrize('length',[512,1024,2048])
def test_all_lengths_actual_producer_to_two_token_consumer(tmp_path,length):
    m=load('cupti_input_contract');slot=next(r for r in m.schedule('cpu-three','a'*40) if r['input_tokens']==length)
    b,c=pilot_files(tmp_path/'m',slot)
    report=b.analyze_model(tmp_path/'m',dict(pid=7),c)
    assert report['role']=='Pilot' and report['pilot']==slot
    assert [v['result']['coe_ns'] for v in report['token_results']]==[20,1]
    assert [v['token_index'] for v in report['metrics']]==[0,1]
    assert report['metrics'][1]['phase_start_ns']==report['metrics'][0]['phase_end_ns']


@pytest.mark.parametrize('damage,reason',[('role','MODEL_RESULT'),('token','TOKEN_REFERENCE'),
    ('input','INPUT_IDENTITY'),('slot','PILOT_FILE_BINDING'),('drain','DRAIN_IDENTITY')])
def test_unified_pilot_file_chain_keeps_specific_rejections(tmp_path,damage,reason):
    from tests.test_cupti_model_policy_reconnect import put,sha
    m=load('cupti_input_contract');slot=m.schedule('cpu-three','a'*40)[1]
    root=tmp_path/'m';b,c=pilot_files(root,slot);r=json.loads((root/'model_result.json').read_text())
    if damage=='role':r['role']='Engineering'
    else:
        name='producer/drain_ledger.json' if damage=='drain' else 'tokens.json'
        v=json.loads((root/name).read_text())
        if damage=='token':v['token_ids'][0]=[999]
        if damage=='input':v['input_identity']['input_ids_sha256']='0'*64
        if damage=='slot':v['pilot']['block']=2
        if damage=='drain':v['drains'][0]['status']='FAILED'
        put(root/name,v)
        if damage=='drain':
            pr=json.loads((root/'producer/producer_receipt.json').read_text())
            pr['files']['drain_ledger.json'].update(sha256=sha(root/name),size_bytes=(root/name).stat().st_size)
            put(root/'producer/producer_receipt.json',pr);r['producer_receipt_sha256']=sha(root/'producer/producer_receipt.json')
        else:r['token_sha256']=sha(root/name)
    put(root/'model_result.json',r)
    with pytest.raises(ValueError,match=reason):b.analyze_model(root,dict(pid=7),c)


def test_new_pilot_original_runner_records_actual_role_tokens_and_drains(tmp_path,monkeypatch):
    from exposedpath import runner
    from tests.test_runner_token_ready import _FakeInput,_FakeModel,_FakeToken,_patch_cpu_torch
    _patch_cpu_torch(monkeypatch)
    monkeypatch.setattr(runner.torch.cuda,'current_device',lambda:0)
    monkeypatch.setattr(runner.torch.cuda,'is_initialized',lambda:False)
    monkeypatch.setattr(runner.torch.cuda.nvtx,'mark',lambda _:None)
    events=[]
    class Input(_FakeInput):shape=(1,2048)
    class Session:
        def __enter__(self):events.append('open');return self
        def __exit__(self,*a):events.append('close')
        def nvtx_sink(self,nvtx):
            from contextlib import nullcontext
            return nullcontext()
    m=load('cupti_input_contract');slot=m.schedule('cpu-three','a'*40)[2]
    model=load('cupti_timeline_model');c=contract(slot);preparation=model.preparer(c);observed={}
    fields=dict(experiment_id='cpu',wmpc_id='w',run_id=slot['run_id'],run_role='PILOT',data_role='Pilot',
        pilot=slot['producer_binding'],pass_id='pass1',attempt_id='once',pid=os.getpid(),
        wmpc_manifest_sha256='a'*64,prompt_sha256='b'*64,runner_git_commit=m.NATIVE,
        runner_git_dirty=False,runner_source_sha256='c'*64)
    def observe(identity,result):observed.update(identity=identity,result=result,preparation=preparation.finish(identity))
    resident=dict(model=_FakeModel(iter(_FakeToken([17+i%2],events) for i in range(8))),input_ids=Input(),attention_mask=object(),eos_token_id=None)
    receipt=model.resident_capture(runner,Session(),resident,fields,tmp_path,preparation,observe)
    assert json.loads(Path(receipt).read_text())['status']=='COMPLETE'
    assert events==['open','host_read','host_read','close']
    assert observed['identity']['data_role']=='Pilot' and observed['result']['actual_input_tokens']==2048
    assert observed['preparation']['consumed_token_indices']==[0,1]
    assert json.loads((tmp_path/'producer/drain_ledger.json').read_text())['drains'][0]['identity']==observed['identity']


@pytest.mark.parametrize('fail_slot',[None,1])
def test_nine_run_control_actual_isolated_consumer_and_failure_stop(tmp_path,monkeypatch,fail_slot):
    b=load('cupti_timeline_b');pilot=load('cupti_input_pilot');m=load('cupti_input_contract')
    from tests.test_cupti_model_policy_reconnect import put,sha
    from shutil import copyfile
    import jsonschema
    package=tmp_path/'p';package.mkdir();ar=tmp_path/'a';(ar/'build').mkdir(parents=True);er=tmp_path/'e';(er/'probe/review').mkdir(parents=True)
    for n in ('receipt.json','artifact_manifest.json','source_bytes.json','build/build.json'):put(ar/n,dict(CPU_DOUBLE=True))
    for n in ('receipt.json','artifact_manifest.json','probe/review/review.json'):put(er/n,dict(CPU_DOUBLE=True))
    cfg=dict(schema_version=m.VERSION,controller_commit='a'*40,analysis_commit='a'*40,native_commit=m.NATIVE,
        activity_policy_version='cupti-api22-activity-policy/0.2.0',batch_id='cpu-three',
        slots=m.schedule('cpu-three','a'*40),server_root=str(tmp_path/'YLQ'),code_root=str(ROOT),python=sys.executable,
        target_python=sys.executable,site_root=str(Path(jsonschema.__file__).parents[1]),a_root=str(ar),event_root=str(er),
        reviewed_a_receipt_sha256='a'*64,reviewed_event_receipt_sha256='b'*64,
        model='CPU_MODEL_NOT_LOADED',inventory_sha256='i'*64,gpu_uuid='CPU_NOT_QUERIED',gpu_pci='CPU_NOT_QUERIED',
        client=dict(path='CPU_DLL_NOT_LOADED',sha256='d'*64),cupti=dict(path='CPU_DLL_NOT_LOADED',sha256='e'*64),
        budget=pilot.fixed_budget(),inputs={},**m.POLICIES)
    for length in (512,1024,2048):
        put(package/f'input_{length}.json',prompt(length))
        cfg['inputs'][str(length)]=dict(path=f'input_{length}.json',sha256=sha(package/f'input_{length}.json'),
            identity=m.input_identity(prompt(length),length),expected_token_ids=[[17],[18]])
    for name in ('cupti_timeline_b.py','cupti_timeline_model.py','cupti_model_consumer.py','cupti_input_contract.py','cupti_input_pilot.py'):
        copyfile(ROOT/'scripts'/name,package/name)
    copyfile(ROOT/'exposedpath/gate11_pilot.py',package/'producer_policy.py');cfg['producer_policy_sha256']=sha(package/'producer_policy.py')
    files=['exposedpath_v141/cupti_driver_queries.py','scripts/analyze_completion_operation_candidate.py','exposedpath_v141/submit_effect_bridge.py','analysis/cupti_timeline.py']
    for name in files:
        p=package/'consumer'/name;p.parent.mkdir(parents=True,exist_ok=True);copyfile(ROOT/name,p)
    cfg['consumer_files']=[dict(path=n,bytes=(ROOT/n).stat().st_size,sha256=sha(ROOT/n)) for n in files]
    cfg['cpu_sources']=[dict(path=p.relative_to(package).as_posix(),sha256=sha(p)) for p in package.rglob('*.py')]
    put(package/'delivery.json',cfg)
    put(package/'package_manifest.json',dict(files=[dict(path=p.relative_to(package).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in package.rglob('*') if p.is_file()]))
    support=load('memset_micro');commands=[];model_count=0
    def components(*_):return ({'startup_resources':lambda out,archive,cfg:dict(CPU_RESOURCE_DOUBLE=True)},support)
    def checked(*_):return dict(a_root=ar,acfg={},verification=dict(CPU_STATIC_DOUBLE=True))
    def command(argv,cwd,log,**kw):
        nonlocal model_count
        commands.append((Path(log).name,kw['timeout']))
        if Path(log).name=='one_model':
            c=json.loads((Path(cwd)/'model_config.json').read_text());slot=c['pilot'];folder=Path(cwd)/'model'
            _,localcfg=pilot_files(folder,slot,model_cfg=c)
            if model_count==fail_slot:
                raw=json.loads((folder/'timeline/capture.json').read_text());raw['records']=[r for r in raw['records'] if r['kind']!='MEMSET'];put(folder/'timeline/capture.json',raw)
                sr=json.loads((folder/'timeline/receipt.json').read_text());sr['capture_sha256']=sha(folder/'timeline/capture.json');put(folder/'timeline/receipt.json',sr)
                result=json.loads((folder/'model_result.json').read_text());result.update(capture_sha256=sha(folder/'timeline/capture.json'),session_receipt_sha256=sha(folder/'timeline/receipt.json'));put(folder/'model_result.json',result)
            model_count+=1;proc=dict(pid=7,status='EXITED',exit_code=0,timed_out=False)
        else:
            r=subprocess.run(argv,cwd=cwd,env=kw['env'],capture_output=True,timeout=20)
            Path(log).with_suffix('.stderr').write_bytes(r.stderr)
            proc=dict(pid=99,status='EXITED',exit_code=r.returncode,timed_out=False)
        put(Path(log).with_suffix('.process.json'),proc)
        if proc['exit_code']:raise ValueError('CPU_REAL_ANALYSIS_EXIT:'+str(proc['exit_code']))
        return proc
    support.command=command
    monkeypatch.setattr(pilot,'control',lambda:b)
    monkeypatch.setattr(b,'components',components);monkeypatch.setattr(b,'checked_a',checked)
    monkeypatch.setattr(pilot,'check_runtime',lambda *_:dict(mode='CPU_PYTHON_VERSION_DOUBLE'))
    for key in ('CUDA_INJECTION64_PATH','NVTX_INJECTION64_PATH','NV_COMPUTE_PROFILER_INJECTION_PATH'):monkeypatch.delenv(key,raising=False)
    assert pilot.static(package)==0
    static_root,unused=pilot.locations(cfg,support,'A');static_hash=sha(static_root/'receipt.json')
    with pytest.raises(ValueError,match='NEW_A_RECEIPT_HASH'):
        pilot.run(package,enabled=True,reviewed='a'*64,reviewed_event='b'*64,reviewed_static='0'*64)
    assert model_count==0
    assert pilot.run(package,enabled=True,reviewed='a'*64,reviewed_event='b'*64,reviewed_static=static_hash)==(0 if fail_slot is None else 2)
    assert model_count==(9 if fail_slot is None else 2)
    assert commands==[('one_model',300),('same_run_analysis',180)]*model_count
    with zipfile.ZipFile(next((tmp_path/'YLQ/transfer').glob('*_pilot.zip'))) as z:
        receipt=json.loads(z.read('receipt.json'));states=[r['status'] for r in receipt['slots']]
        if fail_slot is None:
            assert states==['COMPLETE_PENDING_REVIEW']*9
            summary=json.loads(z.read('summary.json'));assert summary['complete_blocks']==[1,2,3]
            assert len(summary['comparisons'])==18
        else:
            assert states==['COMPLETE_PENDING_REVIEW','BLOCKED']+['NOT_RUN']*7
            assert receipt['status']=='BLOCKED' and 'summary.json' not in z.namelist()


@pytest.mark.parametrize('mode',['static','missing_new_a','reviewed'])
def test_ps51_default_static_and_explicit_review_gate(tmp_path,mode):
    from tests.test_cupti_model_policy_reconnect import put,sha
    import shutil
    shutil.copyfile(ROOT/'scripts/run_cupti_input_pilot.ps1',tmp_path/'run.ps1')
    driver=tmp_path/'cupti_input_pilot.py'
    driver.write_text('import json,sys\nfrom pathlib import Path\nPath(__file__).with_name("argv.json").write_text(json.dumps(sys.argv[1:]))\n')
    put(tmp_path/'delivery.json',dict(schema_version='CUPTI-INPUT-PILOT/0.1.0',python=sys.executable,
        reviewed_a_receipt_sha256='a'*64,reviewed_event_receipt_sha256='b'*64,
        bootstrap_files=[dict(path=driver.name,sha256=sha(driver))]))
    ps=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
    args=[str(ps),'-NoProfile','-ExecutionPolicy','Bypass','-File',str(tmp_path/'run.ps1')]
    if mode!='static':args+=['-RunReviewedPilot','-ReviewedAReceiptSha256','a'*64,'-ReviewedEventReceiptSha256','b'*64]
    if mode=='reviewed':args+=['-ReviewedStaticSha256','c'*64]
    r=subprocess.run(args,cwd=tmp_path,capture_output=True,timeout=20)
    assert (r.returncode==0)==(mode!='missing_new_a')
    if mode=='missing_new_a':assert not (tmp_path/'argv.json').exists()
    else:
        actual=json.loads((tmp_path/'argv.json').read_text())
        assert ('--run-reviewed-pilot' in actual)==(mode=='reviewed')
