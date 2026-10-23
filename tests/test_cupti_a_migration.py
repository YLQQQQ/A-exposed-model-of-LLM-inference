"""Literal same-source budgets and coverage failures, not GPU qualification."""
from copy import deepcopy
import hashlib
import importlib
import importlib.util
import json
import zipfile

import pytest


def reader():
    assert importlib.util.find_spec('analysis.cupti_a_migration'), 'same-source migration connection missing'
    return importlib.import_module('analysis.cupti_a_migration')


def fixture():
    # Two Host-readable operations. Request[100,124), Prefill[100,112).
    # Old: H2/API18/E2/Z2. Q: [104,111) U [114,118) U [119,121)=13.
    # Q intersects old E by2; move11 from submit -> new API7/E13, still24.
    names = ['cudaLaunchKernel', 'cudaMemcpyAsync', 'cudaStreamSynchronize']*2
    times = [(100,104),(104,110),(110,112),(112,114),(114,120),(120,122)]
    calls=[]; records=[]
    for i,(name,(a,b)) in enumerate(zip(names,times),1):
        params=dict(native_stream=70)
        if name=='cudaMemcpyAsync':params.update(count=8,copy_kind=2)
        c=dict(id=i,domain='RUNTIME',pid=7,tid=9,context=3,device=0,stream=4,
            correlation=10+i,cbid={'cudaLaunchKernel':211,'cudaMemcpyAsync':41,'cudaStreamSynchronize':131}[name],
            name=name,start=a,end=b,parent_id=None,params=params,return_code=0)
        calls.append(c)
        records.append(dict(id='a'+str(i),kind='API',domain='RUNTIME',pid=7,tid=9,
            correlation=10+i,cbid=c['cbid'],return_code=0,start=a,end=b))
    effects=[dict(id=k,kind=kind,pid=7,device=0,context=3,stream=4,start=a,end=b)
        for k,kind,a,b in [('k0','KERNEL',103,109),('d0','MEMCPY',109,111),
                            ('k1','KERNEL',113,118),('d1','MEMCPY',119,121)]]
    records+=effects
    for i,a,b,corr in [(0,110,112,13),(1,120,122,16)]:
        records.append(dict(id='s'+str(i),kind='SYNC',domain='UNSPECIFIED',pid=7,context=3,
            stream=4,flags=3,start=a,end=b,correlation=corr))
    common=dict(session_id='r',pid=7,tid=9,device=0,context=3,stream=4,request_start=100,
        drain_end=99,actual_token_ids=[17],completion_proof='HOST_TOKEN_READABLE',ownership='CLOSED_SINGLE_FIFO_NO_EVENTS_OR_GRAPHS')
    scopes=[dict(common,completion_end=112,copy_api='a2',sync_api='a3'),
            dict(common,completion_end=124,copy_api='a5',sync_api='a6',actual_token_ids=[18])]
    owners=[dict(api_id=r['id'],domain=r['domain'],name=c['name'],callback_id=c['id'],
        start=r['start'],end=r['end'],return_code=0) for r,c in zip(records[:6],calls)]
    submits={'a1':['k0'],'a2':['d0'],'a4':['k1'],'a5':['d1']}
    sources=[dict(api_id=r['api_id'],domain=r['domain'],start=r['start'],end=r['end']) for r in owners if r['api_id'] in submits]
    common_result=dict(schema_version='submit-effect-bridge/0.3.0',status='VALID_UNDER_DECLARED_SUPPORT_ASSUMPTIONS',
        session_id='r',clock='CUPTI_TIMESTAMP_NS',closed_prior_ids=[],logical_zero_call_ids=[],
        driver_queries=[],runtime_queries=[],internal_synchronizations=[],
        driver_query_policy='cupti-api22-driver-queries/0.1.0',runtime_query_policy='cupti-api22-runtime-queries/0.1.0',
        api_callback_timing_policy='cupti-api22-distinct-api-callback-boundaries/0.2.0')
    results=[dict(common_result,members=['k0','d0'],terminal='d0',coe_ns=7,operation_wall_ns=8,sync_intersection_ns=1,
        activity_union=[[104,111]],accounting_api_sources=owners[:3],submit_effects={k:v for k,v in submits.items() if k in ('a1','a2')},submission_api_sources=sources[:2]),
        dict(common_result,members=['k0','d0','k1','d1'],terminal='d1',coe_ns=6,operation_wall_ns=8,sync_intersection_ns=1,
        activity_union=[[114,118],[119,121]],accounting_api_sources=owners,submit_effects=submits,submission_api_sources=sources)]
    raw=dict(schema_version='cupti-timeline-capture/0.1.0',session_id='r',pid=7,clock='CUPTI_TIMESTAMP_NS',
        callbacks=calls,records=records,quality=dict(closed=True,errors=[],overflow=0,dropped=0,dropped_query_errors=0,dropped_scopes=[[3,4]]))
    return raw,scopes,results


def test_whole_window_same_raw_migration_deducts_exact_sources_and_phase_sum():
    raw,scopes,saved=fixture(); before=deepcopy(raw)
    r=reader().audit_run(raw,scopes,saved)
    assert r['status']=='COMPLETE_WINDOW_SOURCE_PREVIEW_NOT_FORMAL'
    req,pre,dec=r['windows']
    assert req['original_budgets_ns']==dict(host=2,submit=18,non_submit=0,device_wait=2,residual=2,unattributed=0)
    assert req['coe_union_ns']==13 and req['old_wait_overlap_ns']==2 and req['new_migration_ns']==11
    assert req['extended_budgets_ns']==dict(host=2,submit=7,non_submit=0,completion_exposure=13,residual=2,unattributed=0)
    assert req['migration_source_ns']==dict(submit=11)
    assert pre['extended_budgets_ns']['completion_exposure']==7
    assert dec['extended_budgets_ns']['completion_exposure']==6
    assert r['request_equals_phase_sum'] is True
    assert raw==before and r['production_A_B_changed'] is False
    assert all(m['original_A_extension']=='SAME_SOURCE_CANDIDATE_PREVIEW_ONLY' for m in r['operations'])


@pytest.mark.parametrize('damage,reason', [('missing_sync','PHYSICAL_SYNC_MISSING'),
    ('unknown_api','API_CLASSIFICATION_MISSING'),('missing_effect','SUBMIT_PROOF_MISSING'),
    ('wrong_thread','API_OWNER_SCOPE'),('missing_saved_owner','SAVED_OWNER_COVERAGE')])
def test_source_gaps_block_whole_A_instead_of_filling_zero(damage,reason):
    raw,scopes,saved=fixture()
    if damage=='missing_sync':raw['records']=[r for r in raw['records'] if r['id']!='s0']
    if damage=='unknown_api':raw['callbacks'][0]['name']='unknownLaunch';saved[-1]['accounting_api_sources'][0]['name']='unknownLaunch'
    if damage=='missing_effect':saved[-1]['submit_effects']['a1']=[]
    if damage=='wrong_thread':raw['records'][0]['tid']=8;raw['callbacks'][0]['tid']=8
    if damage=='missing_saved_owner':saved[-1]['accounting_api_sources']=saved[-1]['accounting_api_sources'][1:]
    result=reader().audit_run(raw,scopes,saved)
    assert result['status']=='BLOCKED_WHOLE_WINDOW_SOURCE_GAP'
    assert any(g['reason']==reason for g in result['gaps'])
    assert result['windows'] is None


def test_missing_internal_driver_API_time_is_not_replaced_by_physical_or_callback_time():
    raw,scopes,saved=fixture()
    child=dict(raw['callbacks'][1],id=20,domain='DRIVER',parent_id=2,correlation=90,
        name='cuStreamSynchronize',cbid=126,start=105,end=108)
    raw['callbacks'].append(child)
    raw['records'].append(dict(id='internal',kind='SYNC',domain='UNSPECIFIED',pid=7,
        context=3,stream=4,flags=3,correlation=90,start=106,end=107))
    saved[-1]['internal_synchronizations']=[dict(source_record_id='internal',runtime_api_id='a2',
        driver_call_id=20,necessary_member_ids=['k0'],physical_interval_ns=[106,107],driver_api_interval_ns=None)]
    result=reader().audit_run(raw,scopes,saved)
    gap=next(g for g in result['gaps'] if g['reason']=='INTERNAL_SYNC_HOST_API_INTERVAL_MISSING')
    assert gap['record_id']=='internal' and gap['owner_api_id']=='a2'
    assert gap['unsafe_interval_ns']==[104,110]
    assert result['windows'] is None
    assert result['local_previews'][0]['status']=='BLOCKED_LOCAL_SOURCE_GAP'


def test_prefix_proof_keeps_completed_members_and_excludes_later_submissions():
    raw,scopes,saved=fixture(); result=reader().audit_run(raw,scopes,saved)
    first=result['sync_projections'][0]
    assert first['member_ids']==['k0','d0']  # k0 already done at sync entry110.
    assert first['terminal_ids']==['d0']
    assert first['old_wait_ns']==1
    assert 'k1' not in first['member_ids']


def test_unmatched_nested_sync_callback_is_a_source_gap_not_ordinary_API():
    raw,scopes,saved=fixture()
    raw['callbacks'].append(dict(raw['callbacks'][1],id=20,domain='DRIVER',parent_id=2,
        correlation=90,name='cuStreamSynchronize',cbid=126,start=105,end=108))
    result=reader().audit_run(raw,scopes,saved)
    assert any(g['reason']=='SYNC_CALLBACK_PHYSICAL_COVERAGE' and g['callback_id']==20 for g in result['gaps'])
    assert result['windows'] is None


def test_duplicate_physical_sync_cannot_be_counted_twice():
    raw,scopes,saved=fixture()
    raw['records'].append(dict(raw['records'][-2],id='s0_duplicate'))
    result=reader().audit_run(raw,scopes,saved)
    assert any(g['reason']=='PHYSICAL_SYNC_DUPLICATE' for g in result['gaps'])
    assert result['windows'] is None


def test_saved_source_time_conflict_cannot_create_an_earlier_submit():
    raw,scopes,saved=fixture()
    saved[-1]['submission_api_sources'][-1]['end']=113
    result=reader().audit_run(raw,scopes,saved)
    assert any(g['reason']=='SUBMIT_SOURCE_IDENTITY' for g in result['gaps'])
    assert result['windows'] is None


def test_typed_query_identity_is_not_name_prefix_classification():
    raw,scopes,saved=fixture()
    # Replace first launch with an exact supported query but keep its old effect.
    c=raw['callbacks'][0];c.update(name='cudaGetDevice',cbid=17)
    raw['records'][0]['cbid']=17
    saved[-1]['accounting_api_sources'][0]['name']='cudaGetDevice'
    saved[-1]['runtime_queries']=[dict(callback_id=1,budget_owner_api_id='a1',name='cudaGetDevice',cbid=17)]
    result=reader().audit_run(raw,scopes,saved)
    assert any(g['reason']=='QUERY_UNEXPECTED_EFFECT' for g in result['gaps'])
    assert result['windows'] is None


def test_nested_real_API_outside_actual_owner_is_not_lost_into_host():
    raw,scopes,saved=fixture()
    raw['records'][0]['end']=102
    saved[-1]['accounting_api_sources'][0]['end']=102
    saved[-1]['submission_api_sources'][0]['end']=102
    raw['callbacks'].append(dict(raw['callbacks'][0],id=20,domain='DRIVER',parent_id=1,
        correlation=90,name='cuLaunchKernel',cbid=307,start=101,end=103))
    raw['records'].append(dict(id='child_api',kind='API',domain='DRIVER',pid=7,tid=9,
        correlation=90,cbid=307,return_code=0,start=101,end=104))
    result=reader().audit_run(raw,scopes,saved)
    assert result['windows'] is None
    gap=next(g for g in result['gaps'] if g['reason']=='NESTED_API_OUTSIDE_OWNER')
    assert gap['record_id']=='child_api' and gap['owner_api_id']=='a1'
    assert gap['unsafe_interval_ns']==[100,104]


def test_sparse_migration_reuses_literal_preview_without_rescanning_unaffected_atoms():
    from analysis.coe_candidate import preview_budget
    atoms=[dict(start=i,end=i+1,category=('submit','device_wait','host')[i%3],source_ids=[str(i)]) for i in range(100,130)]
    q=[[102,109],[107,113],[122,127]]
    assert reader().migrate_atoms([100,130],atoms,q)==preview_budget([100,130],atoms,[q])


def sealed_files(tmp_path, damage=None):
    raw,scopes,saved=fixture()
    encode=lambda v:json.dumps(v,sort_keys=True).encode()
    raw_bytes=encode(raw); raw_hash=hashlib.sha256(raw_bytes).hexdigest()
    files={'runs/r/model/timeline/capture.json':raw_bytes}
    tokens=dict(identity=dict(run_id='r',data_role='Pilot',run_role='PILOT'),token_ids=[[17],[18]],
        actual_input_tokens=512,actual_output_tokens=2,early_eos=False,pid=7,tid=9)
    if damage=='token':tokens['token_ids'][1]=[19]
    if damage=='role':tokens['identity']['data_role']='Formal'
    files['runs/r/model/tokens.json']=encode(tokens)
    for i,(s,r) in enumerate(zip(scopes,saved)):
        sb=encode(s);outer=dict(schema_version='cupti-timeline-adapter/0.3.0',input=dict(
            capture_sha256=raw_hash,scope_sha256=hashlib.sha256(sb).hexdigest()),result=r)
        if damage=='scope_hash' and i==1:outer['input']['scope_sha256']='0'*64
        files[f'runs/r/model/scope_token{i}.json']=sb
        files[f'runs/r/model/derived_token{i}/result.json']=encode(outer)
    manifest=encode(dict(files=[dict(path=n,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()) for n,b in files.items()]))
    package=tmp_path/'sealed.zip'
    with zipfile.ZipFile(package,'w') as z:
        for n,b in files.items():z.writestr(n,b)
        z.writestr('artifact_manifest.json',manifest)
    index=dict(schema_version='cupti-input-pilot-closeout/0.1.0',archive_reference=dict(
        bytes=package.stat().st_size,sha256=hashlib.sha256(package.read_bytes()).hexdigest(),
        manifest_sha256=hashlib.sha256(manifest).hexdigest()),runs=[dict(run_id='r',role='Pilot',
        input_tokens=512,block=1,tokens=[[17],[18]],capture_sha256=raw_hash,token_details=[dict(scope=s) for s in scopes])])
    if damage=='archive_hash':index['archive_reference']['sha256']='0'*64
    ip=tmp_path/'index.json';ip.write_bytes(encode(index))
    return package,ip


def test_real_file_chain_binds_manifest_scope_tokens_and_new_output(tmp_path):
    package,index=sealed_files(tmp_path);before=package.read_bytes();out=tmp_path/'derived'
    value=reader().review_archive(package,index,out,run_id='r')
    assert value['counts']==dict(runs=1,complete_window_previews=1,blocked=0)
    assert len(value['consumed_member_hashes'])==6
    result=value['runs'][0]['windows'][0]
    assert result['new_migration_ns']==11
    assert all(p['necessary_activity_ids'] and p['operation_sync_ids'] for p in result['migration'])
    assert json.loads((out/'same_source_migration.json').read_text())==value
    assert package.read_bytes()==before
    with pytest.raises(ValueError,match='NO_OVERWRITE'):reader().review_archive(package,index,out,run_id='r')


@pytest.mark.parametrize('damage,reason',[('token','RUN_TOKEN_IDENTITY'),('role','RUN_TOKEN_IDENTITY'),
    ('scope_hash','SAVED_INPUT_BINDING'),('archive_hash','ARCHIVE_HASH')])
def test_actual_file_chain_rejects_rebound_identity_without_writing_A(tmp_path,damage,reason):
    package,index=sealed_files(tmp_path,damage);out=tmp_path/'rejected'
    with pytest.raises(ValueError,match=reason):reader().review_archive(package,index,out,run_id='r')
    assert not out.exists()
