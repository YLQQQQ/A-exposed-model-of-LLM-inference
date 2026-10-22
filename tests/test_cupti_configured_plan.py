"""Plan/file-chain checks. External target GPU/space/Python are CPU doubles."""
from copy import deepcopy
import json
import subprocess
import sys
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest
from tests.test_cupti_input_pilot import load, prompt
from tests.test_cupti_model_policy_reconnect import put, sha
from tests.test_cupti_pilot_reference_dispatch import sealed, scene, reseal_package, read
ROOT=Path(__file__).resolve().parents[1]


def plan(lengths=(4096,), orders=((4096,),), role='Engineering'):
    return dict(schema_version='CUPTI-INPUT-PLAN/0.2.0',role=role,input_lengths=list(lengths),
        blocks=len(orders),orders=[list(v) for v in orders],comparisons=[])


def test_configured_schedule_one_or_many_points_blocks_and_identity():
    c=load('cupti_input_contract')
    p=plan((256,512),((512,256),(256,512)),role='Pilot')
    p['comparisons']=[dict(low=256,high=512,role='PRIMARY',token_indices=[0,1])]
    slots=c.schedule('future','a'*40,plan=p)
    assert [(s['block'],s['position'],s['input_tokens']) for s in slots]==[(1,1,512),(1,2,256),(2,1,256),(2,2,512)]
    assert [s['run_id'] for s in slots]==['future-b1-G512P-pass1','future-b1-G256P-pass1',
        'future-b2-G256P-pass1','future-b2-G512P-pass1']
    assert c.schedule('one','a'*40,plan=plan())[0]['data_role']=='Engineering'
    from exposedpath.gate11_pilot import validate_binding
    validate_binding(slots[0]['producer_binding'])
    bad=deepcopy(slots[0]['producer_binding']);bad['position']=2
    with pytest.raises(ValueError,match='CUPTI'):validate_binding(bad)


@pytest.mark.parametrize('damage', ['duplicate','missing','blocks','unknown_comparison','duplicate_comparison','role','bool_length'])
def test_plan_rejects_invalid_order_comparison_and_role(damage):
    c=load('cupti_input_contract');p=plan((512,2048),((512,2048),))
    if damage=='duplicate':p['orders'][0]=[512,512]
    if damage=='missing':p['orders'][0]=[512]
    if damage=='blocks':p['blocks']=2
    if damage=='role':p['role']='Formal'
    if damage=='bool_length':p['input_lengths'][0]=True
    if damage in ('unknown_comparison','duplicate_comparison'):
        p['comparisons']=[dict(low=512,high=4096 if damage=='unknown_comparison' else 2048,role='PRIMARY',token_indices=[0,1])]
        if damage=='duplicate_comparison':p['comparisons']*=2
    with pytest.raises(ValueError,match='PLAN'):c.schedule('x','a'*40,plan=p)


def test_generic_summary_signed_and_no_cross_block_splice_or_forced_comparison():
    c=load('cupti_input_contract');p=plan((512,2048),((512,2048),(2048,512)),role='Pilot')
    p['comparisons']=[dict(low=512,high=2048,role='PRIMARY',token_indices=[0,1])]
    slots=c.schedule('x','a'*40,plan=p);rows=[]
    for s in slots:
        coe,gpu=(20,100) if s['input_tokens']==512 else (10,200)
        rows.append(dict(slot=s,metrics=[dict(token_index=i,coe_ns=coe,phase_gpu_union_ns=gpu,
            coe_phase_ratio=coe/1000) for i in (0,1)]))
    r=c.summarize(slots,rows,plan=p)
    assert r['complete_blocks']==[1,2] and len(r['comparisons'])==4
    assert [(v['delta_coe_ns'],v['R_ns']) for v in r['comparisons']]==[(-10,-30)]*4
    with pytest.raises(ValueError,match='INCOMPLETE'):c.summarize(slots,rows[:-1],plan=p)
    bad=deepcopy(rows);bad[-1]['slot']=slots[0]
    with pytest.raises(ValueError,match='SLOT'):c.summarize(slots,bad,plan=p)
    for row in rows:
        if row['slot']['input_tokens']==512:row['metrics'][0]['phase_gpu_union_ns']=0
    assert c.summarize(slots,rows,plan=p)['comparisons'][0]['R_ns'] is None
    one=c.schedule('one','a'*40,plan=plan())
    assert c.summarize(one,[dict(slot=one[0],metrics=rows[0]['metrics'])],plan=plan())['comparisons']==[]


def test_unreferenced_engineering_tokens_not_inherited_and_never_pilot_permission():
    c=load('cupti_input_contract')
    policy=dict(version='cupti-output-validation/0.2.0',mode='OBSERVED_ENGINEERING',expected_token_ids=None)
    c.validate_output_policy(policy,'Engineering')
    assert c.validate_tokens([[42],[43]],policy,dict(vocab_size=100,eos_token_ids=[99]))['independent_content_reference'] is False
    with pytest.raises(ValueError,match='OUTPUT_POLICY'):c.validate_output_policy(policy,'Pilot')
    bad=deepcopy(policy);bad['expected_token_ids']=[[29184],[6556]]
    with pytest.raises(ValueError,match='OUTPUT_POLICY'):c.validate_output_policy(bad,'Engineering')
    for ids in ([[42]],[[42],[100]],[[42],[99]],[[42],[True]]):
        with pytest.raises(ValueError,match='TOKEN'):c.validate_tokens(ids,policy,dict(vocab_size=100,eos_token_ids=[99]))


def test_memory_snapshots_are_explicit_outside_window_allocator_not_total_peak():
    m=load('cupti_timeline_model');calls=[]
    cuda=SimpleNamespace(mem_get_info=lambda device:(calls.append(('free',device)) or (400,1000)),
        memory_allocated=lambda device:100,memory_reserved=lambda device:200,
        max_memory_allocated=lambda device:150,max_memory_reserved=lambda device:250)
    result=m.memory_snapshot(cuda,'AFTER_CAPTURE_CLOSED',0)
    assert calls==[('free',0)]
    assert result['free_device_bytes']==400 and result['allocator_peak_allocated_bytes']==150
    assert result['device_total_peak_bytes'] is None and result['outside_measured_window'] is True


def test_new_length_capacity_and_full_2d_identity_not_gpu_qualification():
    c=load('cupti_input_contract');model=dict(model_type='qwen2',max_position_embeddings=32768,vocab_size=151936)
    r=c.input_identity(prompt(4096),4096,model)
    assert r['shape']==[1,4096] and r!=c.input_identity(prompt(2048),2048,model)
    with pytest.raises(ValueError,match='MODEL_CAPACITY'):c.input_identity(prompt(4096),4096,dict(model,max_position_embeddings=4096))


def test_new_engineering_preserves_original_P_runner_completion_and_actual_tokens(tmp_path,monkeypatch):
    import os
    from exposedpath import runner
    from tests.test_runner_token_ready import _FakeInput,_FakeModel,_FakeToken,_patch_cpu_torch
    _patch_cpu_torch(monkeypatch)
    monkeypatch.setattr(runner.torch.cuda,'current_device',lambda:0)
    monkeypatch.setattr(runner.torch.cuda,'is_initialized',lambda:False)
    monkeypatch.setattr(runner.torch.cuda.nvtx,'mark',lambda _:None)
    c=load('cupti_input_contract');controller=load('cupti_input_pilot');model=load('cupti_timeline_model')
    slot=c.schedule('cpu','a'*40,plan=plan())[0]
    batch=dict(schema_version=c.PLAN_VERSION,plan=plan(),model_limits=dict(vocab_size=151936,max_position_embeddings=32768,eos_token_ids=[151645]),
        model_config_sha256='f'*64,native_commit=c.NATIVE,controller_commit='a'*40,activity_policy_version='cupti-api22-activity-policy/0.2.0',
        code_root=str(ROOT),producer_policy_sha256='p'*64,inputs={'4096':dict(identity=c.input_identity(prompt(4096),4096),sha256='b'*64,
            output_validation=dict(version='cupti-output-validation/0.2.0',mode='OBSERVED_ENGINEERING',expected_token_ids=None))},**c.POLICIES)
    mc=controller.one_configuration(batch,slot)['model_contract'];mc['session']=dict(activity_policy_version=mc['activity_policy_version'])
    preparation=model.preparer(mc);events=[];observed={}
    class Input(_FakeInput):shape=(1,4096)
    class Session:
        def __enter__(self):events.append('open');return self
        def __exit__(self,*a):events.append('close')
        def nvtx_sink(self,nvtx):
            from contextlib import nullcontext
            return nullcontext()
    fields=dict(experiment_id='cpu',wmpc_id='w',run_id=slot['run_id'],run_role='ENGINEERING',data_role='Engineering',
        pass_id='pass1',attempt_id='once',pid=os.getpid(),wmpc_manifest_sha256='a'*64,prompt_sha256='b'*64,
        runner_git_commit=c.NATIVE,runner_git_dirty=False,runner_source_sha256='c'*64)
    def observe(identity,result):observed.update(identity=identity,result=result,preparation=preparation.finish(identity))
    resident=dict(model=_FakeModel(iter(_FakeToken([17+i%2],events) for i in range(8))),input_ids=Input(),attention_mask=object(),eos_token_id=None)
    receipt=model.resident_capture(runner,Session(),resident,fields,tmp_path,preparation,observe)
    assert read(receipt)['status']=='COMPLETE' and events==['open','host_read','host_read','close']
    assert observed['identity']['data_role']=='Engineering' and observed['result']['actual_input_tokens']==4096
    assert observed['preparation']['consumed_token_indices']==[0,1]
    assert read(tmp_path/'producer/drain_ledger.json')['drains'][0]['identity']==observed['identity']


def test_ps51_new_plan_defaults_to_static_and_requires_review_for_capture(tmp_path):
    import os
    import shutil
    script=tmp_path/'run.ps1';shutil.copyfile(ROOT/'scripts/run_cupti_input_pilot.ps1',script)
    driver=tmp_path/'cupti_input_pilot.py'
    driver.write_text('import json,sys\nfrom pathlib import Path\nPath(__file__).with_name("entered.json").write_text(json.dumps(sys.argv[1:]))\n')
    put(tmp_path/'delivery.json',dict(schema_version='CUPTI-INPUT-PLAN/0.2.0',python=sys.executable,
        reviewed_a_receipt_sha256='a'*64,reviewed_event_receipt_sha256='b'*64,
        bootstrap_files=[dict(path=driver.name,sha256=sha(driver))]))
    ps=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
    argv=[str(ps),'-NoProfile','-ExecutionPolicy','Bypass','-File',str(script)]
    r=subprocess.run(argv,cwd=tmp_path,capture_output=True,timeout=20)
    assert r.returncode==0 and read(tmp_path/'entered.json')==['--package',str(tmp_path)]
    (tmp_path/'entered.json').unlink()
    r=subprocess.run(argv+['-RunReviewedPilot'],cwd=tmp_path,capture_output=True,timeout=20)
    assert r.returncode!=0 and not (tmp_path/'entered.json').exists()
    r=subprocess.run(argv+['-RunReviewedPilot','-ReviewedStaticSha256','c'*64,
        '-ReviewedAReceiptSha256','a'*64,'-ReviewedEventReceiptSha256','b'*64],cwd=tmp_path,capture_output=True,timeout=20)
    assert r.returncode==0 and '--run-reviewed-pilot' in read(tmp_path/'entered.json')


def planned_files(root,slot,model_cfg=None):
    """Hand-shaped two-token trace; actual S/COE consumer, no GPU."""
    from tests.test_cupti_model1024 import finite_files
    from tests.test_cupti_input_pilot import pilot_files
    c=load('cupti_input_contract');p=load('cupti_input_pilot');planned=slot['plan']
    if planned['role']=='Pilot':
        # Reuse the existing complete Pilot producer fixture, then bind new plan.
        b,cfg=pilot_files(root,slot)
    else:b,cfg=finite_files(root)
    limits=dict(vocab_size=151936,max_position_embeddings=32768,eos_token_ids=[151645])
    batch=dict(schema_version=c.PLAN_VERSION,plan=planned,inputs={str(slot['input_tokens']):dict(
        identity=c.input_identity(prompt(slot['input_tokens']),slot['input_tokens']),sha256='0'*64,
        output_validation=dict(version='cupti-output-validation/0.2.0',mode='OBSERVED_ENGINEERING',expected_token_ids=None))},
        model_limits=limits,model_config_sha256='f'*64,native_commit=c.NATIVE,controller_commit='a'*40,code_root=str(ROOT),
        producer_policy_sha256='p'*64,activity_policy_version='cupti-api22-activity-policy/0.2.0',**c.POLICIES)
    if planned['role']=='Pilot':batch['inputs'][str(slot['input_tokens'])]['output_validation'].update(mode='EXACT_REFERENCE',expected_token_ids=[[17],[18]])
    cfg.update(p.one_configuration(batch,slot))
    mc=cfg['model_contract'];put(root/f'input_{slot["input_tokens"]}.json',prompt(slot['input_tokens']))
    mc.update(prompt=str(root/f'input_{slot["input_tokens"]}.json'),prompt_sha256=sha(root/f'input_{slot["input_tokens"]}.json'),
        input_identity=batch['inputs'][str(slot['input_tokens'])]['identity'],session=dict(activity_policy_version=batch['activity_policy_version']))
    if model_cfg is not None:mc=deepcopy(model_cfg)
    put(root/'model_config.json',mc);cfg['model_contract']=mc
    config_hash=sha(root.parent/'model_config.json') if model_cfg is not None else sha(root/'model_config.json')
    session_id=mc.get('session',{}).get('session_id','test')
    cfg.update(input_identity=mc['input_identity'],prompt_sha256=mc['prompt_sha256'],session_id=session_id)
    # Replace only run identity in all sidecars/labels, preserving literal times.
    old=json.loads((root/'tokens.json').read_text())['identity']['run_id']
    def change(v):
        if isinstance(v,dict):return {k:change(x) for k,x in v.items()}
        if isinstance(v,list):return [change(x) for x in v]
        if isinstance(v,str):
            if ':' in v and v.split(':',1)[0] in ('EXPOSEDPATH_DRAIN_V1','EXPOSEDPATH_BOUNDARY_V1','EXPOSEDPATH_JSON_V1'):
                a,p=v.split(':',1);return a+':'+json.dumps(change(json.loads(p)),sort_keys=True,separators=(',',':'))
            if v==old:return slot['run_id']
        return v
    for name in ('tokens.json','scope_producers.json','producer/pass_identity.json','producer/host_boundaries.json','producer/drain_ledger.json','timeline/capture.json'):
        put(root/name,change(json.loads((root/name).read_text())))
    tokens=json.loads((root/'tokens.json').read_text());tokens.update(input_slot=slot,input_identity=mc['input_identity'],actual_input_tokens=slot['input_tokens']);put(root/'tokens.json',tokens)
    setup=json.loads((root/'setup.json').read_text());setup.update(input_slot=slot,input_plan=planned,output_validation=mc['output_validation'],
        model_config_sha256=mc['model_config_sha256'],model_limits=limits,input_identity=mc['input_identity'],input_sha256=mc['prompt_sha256'],input_shape=[1,slot['input_tokens']]);put(root/'setup.json',setup)
    ledger=json.loads((root/'producer/pass_identity.json').read_text());ledger.update(run_id=slot['run_id'],wmpc_manifest_sha256=config_hash,prompt_sha256=mc['prompt_sha256']);put(root/'producer/pass_identity.json',ledger)
    receipt=json.loads((root/'producer/producer_receipt.json').read_text())
    for value in receipt['files'].values():
        file=root/'producer'/value['filename'];value.update(sha256=sha(file),size_bytes=file.stat().st_size)
    put(root/'producer/producer_receipt.json',receipt)
    raw=json.loads((root/'timeline/capture.json').read_text());raw['session_id']=session_id;put(root/'timeline/capture.json',raw)
    scopes=json.loads((root/'scope_producers.json').read_text())
    for s in scopes:s['session_id']=session_id
    put(root/'scope_producers.json',scopes)
    sr=json.loads((root/'timeline/receipt.json').read_text());sr.update(session_id=session_id,capture_sha256=sha(root/'timeline/capture.json'),
        client_sha256=mc.get('session',{}).get('client_sha256','d'*64),cupti_sha256=mc.get('session',{}).get('cupti_sha256','e'*64));put(root/'timeline/receipt.json',sr)
    for name,pos in [('memory_before.json','BEFORE_WARMUPS_AND_SESSION'),('memory_after.json','AFTER_CAPTURE_CLOSED')]:
        put(root/name,dict(position=pos,outside_measured_window=True,logical_device=0,device_total_peak_bytes=None,
            free_device_bytes=400,total_device_bytes=1000,allocator_allocated_bytes=100,allocator_reserved_bytes=200,
            allocator_peak_allocated_bytes=150,allocator_peak_reserved_bytes=250))
    result=json.loads((root/'model_result.json').read_text());result.update(schema_version='cupti-timeline-model-result/0.4.0',role=planned['role'],input_slot=slot,
        control_commit=mc['control_commit'],config_sha256=config_hash)
    for key,name in dict(token_sha256='tokens.json',scope_producers_sha256='scope_producers.json',setup_sha256='setup.json',
        capture_sha256='timeline/capture.json',session_receipt_sha256='timeline/receipt.json',producer_receipt_sha256='producer/producer_receipt.json',
        memory_before_sha256='memory_before.json',memory_after_sha256='memory_after.json').items():result[key]=sha(root/name)
    put(root/'model_result.json',result)
    return b,cfg


@pytest.mark.parametrize('role',['Engineering','Pilot'])
def test_generic_two_token_file_chain_accepts_observed_engineering_or_referenced_pilot(tmp_path,role):
    c=load('cupti_input_contract');slot=c.schedule('test','a'*40,plan=plan(role=role))[0]
    b,cfg=planned_files(tmp_path/'m',slot)
    result=b.analyze_model(tmp_path/'m',dict(pid=7),cfg)
    assert result['role']==role and [a['result']['coe_ns'] for a in result['token_results']]==[20,1]
    assert len(result['metrics'])==2 and result['record_capacity']['overflow']==0
    assert result['independent_output_content_reference'] is (role=='Pilot')


@pytest.mark.parametrize('damage,reason', [('token','TOKEN_VALUES'),('scope','SCOPE_PRODUCER_BINDING'),
    ('mask','INPUT_IDENTITY'),('slot','PLAN_FILE_BINDING'),('memory','MEMORY_EVIDENCE'),('effect','SAME_RUN_ANALYSIS')])
def test_generic_file_chain_rejects_specific_corruption(tmp_path,damage,reason):
    c=load('cupti_input_contract');slot=c.schedule('test','a'*40,plan=plan())[0]
    b,cfg=planned_files(tmp_path/'m',slot);root=tmp_path/'m'
    name={'token':'tokens.json','scope':'scope_producers.json','mask':'tokens.json','slot':'tokens.json',
        'memory':'memory_after.json','effect':'timeline/capture.json'}[damage]
    v=json.loads((root/name).read_text())
    if damage=='token':v['token_ids']=[[151936],[18]]
    if damage=='mask':v['input_identity']['attention_mask_sha256']='0'*64
    if damage=='slot':v['input_slot']['position']=99
    if damage=='scope':v[0]['run_id']='other'
    if damage=='memory':v['outside_measured_window']=False
    if damage=='effect':v['records']=[r for r in v['records'] if r['kind']!='MEMSET']
    put(root/name,v)
    r=json.loads((root/'model_result.json').read_text());key={'tokens.json':'token_sha256','scope_producers.json':'scope_producers_sha256',
        'memory_after.json':'memory_after_sha256','timeline/capture.json':'capture_sha256'}[name];r[key]=sha(root/name)
    if damage=='effect':
        sr=json.loads((root/'timeline/receipt.json').read_text());sr['capture_sha256']=r[key];put(root/'timeline/receipt.json',sr);r['session_receipt_sha256']=sha(root/'timeline/receipt.json')
    put(root/'model_result.json',r)
    with pytest.raises(ValueError,match=reason):b.analyze_model(root,dict(pid=7),cfg)


def configured_scene(scene):
    pilot,b,stage,m,c,package,root,checks=scene
    helper=load('cupti_input_contract');p=plan();c.update(schema_version=helper.PLAN_VERSION,plan=p,
        slots=helper.schedule(c['batch_id'],c['controller_commit'],plan=p),budget=pilot.fixed_budget(p))
    for length in (512,1024,2048):(package/f'input_{length}.json').unlink()
    put(package/'input_4096.json',prompt(4096))
    c['inputs']={'4096':dict(path='input_4096.json',sha256=sha(package/'input_4096.json'),
        identity=helper.input_identity(prompt(4096),4096),output_validation=dict(version='cupti-output-validation/0.2.0',
            mode='OBSERVED_ENGINEERING',expected_token_ids=None))}
    ref=dict(model_type='qwen2',vocab_size=151936,max_position_embeddings=32768,eos_token_id=151645)
    put(package/'model_config_reference.json',ref);c['model_config_sha256']=sha(package/'model_config_reference.json')
    c['model_limits']=helper.model_limits(ref);model=root/'actual_model_config_only';model.mkdir();put(model/'config.json',ref)
    c['model']=str(model);put(package/'delivery.json',c);reseal_package(package)
    return pilot,b,stage,m,c,package,root,checks


@pytest.mark.parametrize('failure',[False,True])
def test_real_static_receipts_to_one_engineering_run_actual_isolated_consumer(scene,monkeypatch,failure):
    pilot,b,stage,m,c,package,root,checks=configured_scene(scene)
    # Ship actual current controls; real A/event validation remains untouched.
    import shutil
    for name in ('cupti_input_contract.py','cupti_timeline_model.py','cupti_timeline_b.py','cupti_model_consumer.py'):
        shutil.copyfile(ROOT/'scripts'/name,package/name)
    shutil.copyfile(ROOT/'exposedpath/gate11_pilot.py',package/'producer_policy.py');c['producer_policy_sha256']=sha(package/'producer_policy.py')
    c['cpu_sources']=[dict(path=v.relative_to(package).as_posix(),sha256=sha(v)) for v in package.rglob('*.py')]
    put(package/'delivery.json',c);reseal_package(package)
    assert pilot.main(['--package',str(package)])==0
    static,_=pilot.locations(c,m,'A');sr=read(static/'receipt.json')
    assert sr['planned_model_processes']==1 and sr['actual_model_processes']==sr['actual_cupti_sessions']==0
    # Actual external model process is the only execution double; the analysis
    # is a real -I/-S subprocess with the delivered four-file consumer overlay.
    import jsonschema
    model_count=0;commands=[]
    def command(argv,cwd,log,**kw):
        nonlocal model_count
        commands.append((Path(log).name,kw['timeout']))
        if Path(log).name=='one_model':
            mc=read(Path(cwd)/'model_config.json')
            assert mc['input_tokens']==4096 and mc['input_identity']['shape']==[1,4096]
            assert mc['role']=='Engineering' and 'pilot' not in mc and '--run-reviewed-model' in argv
            planned_files(Path(cwd)/'model',mc['input_slot'],model_cfg=mc)
            model_count+=1;proc=dict(pid=7,status='EXITED',exit_code=0,timed_out=False)
            if failure:
                raw=read(Path(cwd)/'model/timeline/capture.json');raw['quality']['overflow']=1;put(Path(cwd)/'model/timeline/capture.json',raw)
                rr=read(Path(cwd)/'model/model_result.json');rr['capture_sha256']=sha(Path(cwd)/'model/timeline/capture.json')
                ss=read(Path(cwd)/'model/timeline/receipt.json');ss['capture_sha256']=rr['capture_sha256'];put(Path(cwd)/'model/timeline/receipt.json',ss)
                rr['session_receipt_sha256']=sha(Path(cwd)/'model/timeline/receipt.json');put(Path(cwd)/'model/model_result.json',rr)
        else:
            # Relocate only target Python/modules, not the model/config files.
            args=list(argv);args[0]=sys.executable
            args[args.index(c['code_root'])]=str(ROOT);args[args.index(c['site_root'])]=str(Path(jsonschema.__file__).parents[1])
            analysis=read(Path(cwd)/'analysis_config.json');analysis['code_root']=str(ROOT);put(Path(cwd)/'analysis_config.json',analysis)
            r=subprocess.run(args,cwd=cwd,env=kw['env'],capture_output=True,timeout=30)
            Path(log).with_suffix('.stderr').write_bytes(r.stderr)
            proc=dict(pid=99,status='EXITED',exit_code=r.returncode,timed_out=False)
        put(Path(log).with_suffix('.process.json'),proc)
        if proc['exit_code']:raise ValueError('CPU_ACTUAL_READER_FAILED')
        return proc
    monkeypatch.setattr(m,'command',command)
    result=pilot.run(package,enabled=True,reviewed=c['reviewed_a_receipt_sha256'],
        reviewed_event=c['reviewed_event_receipt_sha256'],reviewed_static=sha(static/'receipt.json'))
    out,archive=pilot.locations(c,m,'B');receipt=read(out/'receipt.json')
    assert result==(2 if failure else 0),(out/'runs'/c['slots'][0]['run_id']/'same_run_analysis.stderr').read_text()
    assert model_count==1 and commands==[('one_model',300),('same_run_analysis',180)]
    assert receipt['role']=='Engineering' and len(receipt['slots'])==1
    if failure:assert receipt['status']=='BLOCKED' and not (out/'summary.json').exists()
    else:
        summary=read(out/'summary.json');assert summary['comparisons']==[] and summary['complete_blocks']==[1]
        assert [v['coe_ns'] for v in summary['rows'][0]['metrics']]==[20,1]
    assert archive.is_file() and checks==['CPU_TARGET_HEAD_CLEAN_DOUBLE','CPU_TARGET_IMPORT_BOUNDARY_DOUBLE']*3


def test_sealed_nine_run_old_summary_and_new_config_arithmetic_agree_without_reanalysis():
    import hashlib
    archive=ROOT/'.local/transfer/cupti_input_bd377c860faf_pilot.zip'
    if not archive.is_file():pytest.skip('Optional sealed Pilot summary unavailable; no GPU qualification implied')
    assert hashlib.file_digest(archive.open('rb'),'sha256').hexdigest()=='2b2597669e5a66789daa75e4fba24de3aa23329510310ddd2197b4fe1ce92308'
    with zipfile.ZipFile(archive) as z:
        index=json.loads(z.read('artifact_manifest.json'))['files']
        row=next(r for r in index if r['path']=='summary.json');data=z.read('summary.json')
        assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
        old=json.loads(data)
    c=load('cupti_input_contract');slots=[r['slot'] for r in old['rows']]
    assert c.summarize(slots,old['rows'])==old
    p=plan((512,1024,2048),((512,1024,2048),(1024,2048,512),(2048,512,1024)),role='Pilot')
    p['comparisons']=[dict(low=a,high=b,role='PRIMARY' if (a,b)==(512,2048) else 'SECONDARY',token_indices=[0,1])
        for a,b in ((512,1024),(1024,2048),(512,2048))]
    ns=c.schedule('replay','a'*40,plan=p)
    rows=[dict(r,slot=s) for r,s in zip(old['rows'],ns)]
    new=c.summarize(ns,rows,plan=p)
    for a,b in zip(new['comparisons'],old['comparisons']):
        assert {k:v for k,v in a.items() if k!='comparison_role'}=={k:v for k,v in b.items() if k!='comparison_role'}
