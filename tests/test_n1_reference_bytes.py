"""Exact execution bytes and Git content are separate identities; CPU only."""
import hashlib
import json
from pathlib import Path

import pytest


def digest(data):
    return hashlib.sha256(data).hexdigest()


def test_source_proof_explains_old_crlf_without_accepting_local_lf(tmp_path):
    from scripts import n1_reference as api
    blob=b'# source\nvalue = 1\n'; actual=blob.replace(b'\n',b'\r\n')
    proof=api.source_proof(blob,blob,digest(actual))
    assert proof==dict(git_sha256=digest(blob),git_size_bytes=len(blob),
        execution_sha256=digest(actual),execution_size_bytes=len(actual),representation='LF_TO_CRLF')
    (tmp_path/'producer.py').write_bytes(actual)
    rows=[]; api.check_file(tmp_path,'producer.py',digest(actual),len(actual),rows)
    (tmp_path/'producer.py').write_bytes(blob)
    with pytest.raises(ValueError,match='HASH_MISMATCH'):
        api.check_file(tmp_path,'producer.py',digest(actual),len(actual),rows)
    assert rows[-1]['actual_sha256']==digest(blob)
    assert rows[-1]['actual_size_bytes']==len(blob)
    assert rows[-1]['expected_sha256']==digest(actual)
    assert rows[-1]['expected_size_bytes']==len(actual)


def test_sealed_lf_must_remain_lf(tmp_path):
    from scripts import n1_reference as api
    blob=b'v=1\n'; proof=api.source_proof(blob,blob,digest(blob))
    assert proof['representation']=='GIT_BYTES'
    p=tmp_path/'f'; p.write_bytes(blob)
    api.check_file(tmp_path,'f',digest(blob),len(blob),[])
    p.write_bytes(blob.replace(b'\n',b'\r\n'))
    with pytest.raises(ValueError,match='HASH_MISMATCH'): api.check_file(tmp_path,'f',digest(blob),len(blob),[])


@pytest.mark.parametrize('artifact,key,value',[
    ('auxiliary_preflight.claim.json','nonce','wrong'),
    ('auxiliary_preflight.claim.json','target_pid',999),
    ('auxiliary_preflight.final.json','status','BLOCKED'),
    ('auxiliary_preflight.final.json','target_claim_sha256','f'*64),
    ('diagnostic/isolated_preflight_target.json','target_pid',999),
    ('diagnostic/producer/pass_identity.json','runner_source_sha256','f'*64),
])
def test_rehashed_container_cannot_replace_original_identity_links(tmp_path,monkeypatch,artifact,key,value):
    run,_,code,root,review,ref=fixture(tmp_path,monkeypatch)
    p=root/artifact; v=json.loads(p.read_text()); v[key]=value; p.write_text(json.dumps(v))
    ref['baseline_files'][artifact]=digest(p.read_bytes()); ref['baseline_sizes'][artifact]=p.stat().st_size
    with pytest.raises(ValueError): run.validate_reference(ref,review,code)


@pytest.mark.parametrize('damage',['omit','hash','size','old_version','git_failure'])
def test_proof_cannot_shrink_or_rebind_observed_source(tmp_path,monkeypatch,damage):
    run,api,code,root,review,ref=fixture(tmp_path,monkeypatch)
    if damage=='omit': ref['source_compatibility']={}
    if damage=='hash': ref['source_compatibility']['producer.py']['execution_sha256']=digest(b'value = 1\n')
    if damage=='size': ref['source_compatibility']['producer.py']['execution_size_bytes']=10
    if damage=='old_version': ref['schema_version']='N1-REMAINING-REFERENCE/0.1'
    if damage=='git_failure':
        def missing(*args): raise ValueError('Git source unavailable')
        monkeypatch.setattr(api,'git_bytes',missing)
    with pytest.raises(ValueError): run.validate_reference(ref,review,code)


def test_cli_reference_reaches_real_collect_group_profile_boundary_only_after_binding(tmp_path,monkeypatch):
    from exposedpath import gate8_diagnostic
    from scripts import gate8_diagnostic_collect
    run,_,code,root,review,ref=fixture(tmp_path,monkeypatch)
    config=tmp_path/'config.json'; rp=tmp_path/'ref.json'; rp.write_text(json.dumps(ref))
    c=dict(baseline_reference=str(rp),baseline_review=str(review),commit='b'*40,variants=['Vmarker','V16'],
        prompt=str(root/'diagnostic/prompt.json'),prompt_sha256=digest(b'input'),model='cpu-only',inventory='cpu-only',
        inventory_sha256='e'*64,target_python='cpu-only',site_root='cpu-only',gpu_uuid='u',gpu_pci_bus_id='p',nsys='FORBIDDEN')
    config.write_text(json.dumps(c)); monkeypatch.setattr(run,'ROOT',code)
    prepared=tmp_path/'prepared'; prepared.mkdir()
    # Substitute hardware preparation only. Reference, CLI, common identity,
    # remaining orchestration and collect_group all execute production logic.
    manifest=json.loads((root/'diagnostic/manifest.json').read_text())
    manifest['runner_git_commit']='b'*40; manifest['n1_model']['protocol_variant']='Vmarker'
    (prepared/'manifest.json').write_text(json.dumps(manifest))
    monkeypatch.setattr(gate8_diagnostic,'prepare_diagnostic',lambda **kw:prepared)
    from exposedpath_v141 import gate8_adapter
    monkeypatch.setattr(gate8_adapter,'normalized_uuid',lambda x:x)
    monkeypatch.setattr(gate8_adapter,'normalized_pci',lambda x:x)
    reached=[]
    def stop(argv,path,**kw):
        reached.append(argv); raise ValueError('CPU_PROFILE_BOUNDARY_STOP')
    monkeypatch.setattr(gate8_diagnostic_collect,'run_once',stop)
    monkeypatch.setattr('sys.argv',['feasibility','--config',str(config),'--output',str(tmp_path/'batch'),'--execute-reviewed-feasibility'])
    assert run.main()==1
    assert len(reached)==1 and '--engineering-domain' in reached[0]
    report=json.loads((tmp_path/'batch/batch_report.json').read_text())
    assert 'CPU_PROFILE_BOUNDARY_STOP' in report['groups'][0]['error']
    assert report['groups'][1]['status']=='NOT_RUN'


def test_changed_bytes_between_groups_stop_before_second_profile(tmp_path,monkeypatch):
    run,_,code,root,review,ref=fixture(tmp_path,monkeypatch)
    rp=tmp_path/'ref.json'; rp.write_text(json.dumps(ref)); cfg=tmp_path/'config.json'
    cfg.write_text(json.dumps(dict(baseline_reference=str(rp),baseline_review=str(review),commit='b'*40,variants=['Vmarker','V16'])))
    monkeypatch.setattr(run,'ROOT',code); seen=[]
    def first(v,path,c):
        seen.append(v); (code/'producer.py').write_bytes(b'value = 1\n')
        return dict(status='FEASIBLE_ONCE_PENDING_REVIEW',common_identity={**ref['common_identity'],'runner_git_commit':'b'*40},observed_tokens=[[1],[2]])
    monkeypatch.setattr(run,'collect_group',first)
    monkeypatch.setattr('sys.argv',['feasibility','--config',str(cfg),'--output',str(tmp_path/'batch'),'--execute-reviewed-feasibility'])
    with pytest.raises(ValueError,match='HASH_MISMATCH'): run.main()
    assert seen==['Vmarker']


@pytest.mark.parametrize('key,value',[('variant','V16'),('request_role','warmup'),('identity',{'run_id':'other'}),('actual_input_tokens',128),('interventions',[{}])])
def test_baseline_calls_must_identify_measured_v0(tmp_path,monkeypatch,key,value):
    run,_,code,root,review,ref=fixture(tmp_path,monkeypatch)
    p=root/'diagnostic/n1_model_calls.json'; v=json.loads(p.read_text()); v['requests'][1][key]=value; p.write_text(json.dumps(v))
    ref['baseline_files']['diagnostic/n1_model_calls.json']=digest(p.read_bytes())
    ref['baseline_sizes']['diagnostic/n1_model_calls.json']=p.stat().st_size
    with pytest.raises(ValueError,match='BASELINE_MEASURED_V0_JOIN'): run.validate_reference(ref,review,code)


@pytest.mark.parametrize('damage',['different_commit_content','unbound_hash'])
def test_source_proof_never_approves_arbitrary_current_content(damage):
    from scripts import n1_reference as api
    blob=b'x=1\n'
    with pytest.raises(ValueError):
        api.source_proof(blob,b'x=2\n' if damage=='different_commit_content' else blob,
            digest(b'x=3\n') if damage=='unbound_hash' else digest(blob))


@pytest.mark.parametrize('name,kind',[('absent.py','FILE_MISSING'),('../outside','PATH_ESCAPE'),
    ('C:/outside','PATH_ESCAPE'),('a/../producer.py','PATH_ESCAPE')])
def test_exact_file_errors_are_distinct(tmp_path,name,kind):
    from scripts import n1_reference as api
    rows=[]
    with pytest.raises(ValueError,match=kind):
        api.check_file(tmp_path,name,'a'*64,10,rows)
    assert rows[-1]['status']==kind
    assert rows[-1]['actual_sha256'] is None and rows[-1]['actual_size_bytes'] is None


def fixture(tmp_path,monkeypatch):
    from scripts import n1_model_feasibility as run,n1_reference as api
    from exposedpath.gate8_isolated_preflight import sha,write_new
    code=tmp_path/'code'; code.mkdir(); root=tmp_path/'old'; (root/'diagnostic/producer').mkdir(parents=True)
    blob=b'value = 1\n'; target=blob.replace(b'\n',b'\r\n'); (code/'producer.py').write_bytes(target)
    old='a'*40; new='b'*40
    monkeypatch.setattr(api,'git_bytes',lambda r,*args: new.encode() if args[0]=='rev-parse' else blob)
    monkeypatch.setattr(api,'producer_paths',lambda r,c:['producer.py'])
    manifest=dict(model_id='m',prompt_tokens_sha256=digest(b'input'),fixed_input_tokens=32,fixed_output_tokens=2,
        batch_size=1,warmup_count=1,repeat_count=1,execution_mode='eager',attention_backend='sdpa',dtype_and_quantization='fp16',
        sampling_config={'do_sample':False},runner_git_commit=old,runner_git_dirty=False,runner_source_sha256='d'*64,
        gpu_index_physical=3,gpu_index_logical=0,gpu_uuid='u',gpu_pci_bus_id='p',model_content_snapshot={'inventory_sha256':'e'*64},
        n1_model={'stream_policy':'fixed','protocol_variant':'V0'},n1_model_execution={'version':'fixed'},
        target_python={'actual':{'snapshot':{'version':'cpu'}}},run_id='r',wmpc_id='w')
    write_new(root/'diagnostic/manifest.json',manifest); (root/'diagnostic/prompt.json').write_bytes(b'input')
    mh=sha(root/'diagnostic/manifest.json')
    (root/'diagnostic/runner_source.py').write_bytes(b'runner')
    manifest['runner_source_sha256']=digest(b'runner')
    (root/'diagnostic/manifest.json').write_text(json.dumps(manifest)); mh=sha(root/'diagnostic/manifest.json')
    identity=dict(run_id='r',wmpc_id='w',request_id='request-0',repeat_id='0')
    ledger=dict(pid=123,run_id='r',wmpc_id='w',runner_git_commit=old,runner_git_dirty=False,wmpc_manifest_sha256=mh,runner_source_sha256=digest(b'runner'),requests=[{},dict(identity=identity,request_role='measured')])
    write_new(root/'diagnostic/producer/pass_identity.json',ledger)
    lp=root/'diagnostic/producer/pass_identity.json'
    write_new(root/'diagnostic/producer/producer_receipt.json',dict(status='COMPLETE',run_id='r',files={'pass_identity.json':{'sha256':sha(lp),'size_bytes':lp.stat().st_size}}))
    write_new(root/'diagnostic/n1_model_calls.json',dict(pid=123,manifest_sha256=mh,
        producer_receipt_sha256=sha(root/'diagnostic/producer/producer_receipt.json'),requests=[{},dict(observed_tokens=[[1],[2]],identity=identity,
            request_role='measured',variant='V0',declaration={'protocol_variant':'V0'},actual_input_tokens=32,interventions=[])]))
    artifacts={k:dict(filename=n,sha256=sha(root/n),size_bytes=(root/n).stat().st_size) for k,n in
        dict(wmpc_manifest='diagnostic/manifest.json',prompt='diagnostic/prompt.json',pass_identity='diagnostic/producer/pass_identity.json',
            producer_receipt='diagnostic/producer/producer_receipt.json',runner_source='diagnostic/runner_source.py').items()}
    write_new(root/'input_receipt.json',dict(identity={'run_id':'r','wmpc_id':'w'},artifacts=artifacts))
    pre=dict(schema_version='exposedpath-isolated-preflight/0.1.0',git_commit=old,git_dirty=False,run_id='r',nonce='n',
        input_hashes={'manifest.json':mh,'prompt.json':digest(b'input')},tree_hashes={'producer.py':digest(target),'exposedpath/runner.py':digest(b'runner')})
    write_new(root/'auxiliary_preflight.json',pre); ph=sha(root/'auxiliary_preflight.json')
    claim=dict(schema_version=pre['schema_version'],preflight_sha256=ph,nonce='n',run_id='r',target_pid=123)
    write_new(root/'auxiliary_preflight.claim.json',claim)
    write_new(root/'diagnostic/isolated_preflight_target.json',claim)
    write_new(root/'auxiliary_preflight.final.json',dict(status='PASS',preflight_sha256=ph,
        target_claim_sha256=sha(root/'auxiliary_preflight.claim.json')))
    write_new(root/'collection_report.json',dict(collection={'status':'COMPLETE','exit_code':0,
        'argv':['nsys','--auxiliary-sha256',ph,'--launch-nonce','n']}))
    review=tmp_path/'review.json'; write_new(review,dict(status='V0_NEW_CONTRACT_ENGINEERING_SCOPE_CHECK_PASSED',
        execution_commit=old,source_receipt_sha256=sha(root/'input_receipt.json'),allocation_policy='N1_OPAQUE_ALLOCATION_BUDGET/0.1.0'))
    ref=dict(schema_version=api.VERSION,baseline_commit=old,execution_commit=new,baseline_root=str(root),
        review_sha256=sha(review),baseline_files={p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file()},
        baseline_sizes={p.relative_to(root).as_posix():p.stat().st_size for p in root.rglob('*') if p.is_file()},
        source_compatibility={'producer.py':api.source_proof(blob,blob,digest(target))},
        common_identity=run.common_identity(manifest),observed_tokens=[[1],[2]])
    for name in api.PREFLIGHT_FILES:
        dest=tmp_path/'baseline_binding'/name; dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes((root/name).read_bytes())
    return run,api,code,root,review,ref


@pytest.mark.parametrize('damage',[None,'current_lf','tamper','missing','wrong_run','wrong_claim','wrong_commit','empty_set'])
def test_bound_reference_gate_persists_failures_before_any_collection(tmp_path,monkeypatch,damage):
    run,api,code,root,review,ref=fixture(tmp_path,monkeypatch)
    if damage=='current_lf': (code/'producer.py').write_bytes(b'value = 1\n')
    if damage=='tamper': (code/'producer.py').write_bytes(b'value = 2\r\n')
    if damage=='missing': (code/'producer.py').unlink()
    if damage in ('wrong_run','wrong_claim'):
        p=root/'auxiliary_preflight.claim.json'; c=json.loads(p.read_text())
        c['run_id' if damage=='wrong_run' else 'preflight_sha256']='wrong'; p.write_text(json.dumps(c))
        # Even refreshed container hashes cannot replace the semantic source join.
        ref['baseline_files'][p.name]=digest(p.read_bytes()); ref['baseline_sizes'][p.name]=p.stat().st_size
    if damage=='wrong_commit': ref['execution_commit']='c'*40
    if damage=='empty_set': ref['source_compatibility']={}
    config=tmp_path/'config.json'; reference=tmp_path/'ref.json'; reference.write_text(json.dumps(ref))
    config.write_text(json.dumps(dict(baseline_reference=str(reference),baseline_review=str(review),commit='b'*40,variants=['Vmarker','V16'])))
    monkeypatch.setattr(run,'ROOT',code); reached=[]
    def boundary(variant,path,c):
        reached.append(variant)
        assert c['reviewed_baseline']==ref
        return dict(status='FEASIBLE_ONCE_PENDING_REVIEW',common_identity={**ref['common_identity'],'runner_git_commit':'b'*40},observed_tokens=[[1],[2]])
    monkeypatch.setattr(run,'collect_group',boundary)
    monkeypatch.setattr('sys.argv',['feasibility','--config',str(config),'--output',str(tmp_path/'batch'),'--execute-reviewed-feasibility'])
    if damage is None:
        assert run.main()==0 and reached==['Vmarker','V16']
    else:
        with pytest.raises(ValueError): run.main()
        assert reached==[]
    report=json.loads((tmp_path/'reference_validation.before.json').read_text())
    assert report['status']==('PASS' if damage is None else 'BLOCKED')
    if damage in ('current_lf','tamper','missing'):
        row=report['files'][-1]
        assert row['path']=='producer.py' and row['expected_size_bytes']==11
        assert row['status']==('FILE_MISSING' if damage=='missing' else 'HASH_MISMATCH')
