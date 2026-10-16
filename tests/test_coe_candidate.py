"""Independent tiny canonical records; not CUDA or new profile qualification."""
from copy import deepcopy
import importlib.util
import json

import pytest


def implementation():
    assert importlib.util.find_spec('analysis.coe_candidate'), 'reusable COE entry missing'
    from analysis import coe_candidate
    return coe_candidate


def example():
    # Planned FIFO: completed K0, long K1, D2H submitted INSIDE the operation,
    # future K2. An unrelated historical worker is closed by the device drain.
    identity = dict(run_id='arbitrary-run', request_id='r', repeat_id='7', pass_id='pass1',
                    attempt_id='a', experiment_id='e', wmpc_id='w', run_role='ENGINEERING', data_role='Engineering')
    apis = [dict(id='past-worker', name='cudaLaunchKernel', start=-10, end=-9, correlation=1, thread=99, return_code=0),
            dict(id='k0', name='cudaLaunchKernel_v3020', start=0, end=1, correlation=2, thread=12, return_code=0),
            dict(id='k1', name='cudaLaunchKernel', start=2, end=3, correlation=3, thread=12, return_code=0),
            dict(id='copy-x', name='cudaMemcpyAsync_v3020', start=4, end=10, correlation=4, thread=12, return_code=0),
            dict(id='sync-x', name='cudaStreamSynchronize_v3020', start=10, end=12, correlation=5, thread=12, return_code=0),
            dict(id='future', name='cudaLaunchKernel', start=15, end=16, correlation=6, thread=12, return_code=0)]
    def effect(key, a, b, corr, kind='KERNEL'):
        return dict(id=key, start=a, end=b, correlation=corr, scope=[100,0,1,7], kind=kind)
    effects=[effect('old',-8,-5,1),effect('K0',1,2,2),effect('K1',3,9,3),
             effect('D',9,10,4,'MEMCPY'),effect('K2',17,19,6)]
    physical=dict(id='physical', correlation=5, scope=[100,0,1,7], start=10, end=11,
                  semantic='STREAM_SYNCHRONIZE')
    return dict(apis=apis,effects=effects,copy=apis[3],sync=apis[4],physical=physical,
        identity=identity, scope=[100,0,1,7],thread=12,request_start=0,drain_end=-3,
        completion_point=14,copy_effect='D',source_sha256='a'*64)


def test_independent_members_cutoff_and_interval_not_pending_or_copy_only():
    r=implementation().analyze_operation(**example())
    assert r['members']==['K0','K1','D']
    assert r['closed_prior']==['old'] and r['excluded_future']==['K2']
    assert r['terminal']=='D'
    assert (r['candidate_ns'],r['original_sync_ns'],r['wall_ns'],r['uncovered_ns'])==(6,0,8,2)
    assert (r['kernel_ns'],r['memop_ns'])==(5,1)
    assert r['pure_host_stall_ns'] is None


@pytest.mark.parametrize('damage,reason',[
    ('stream','SCOPE'),('failed_sync','SYNC_FAILED'),('physical','PHYSICAL_MAPPING'),
    ('missing','CORRELATION'),('duplicate','CORRELATION'),('pending','PRIOR_NOT_CLOSED'),
    ('boundary','SUBMISSION_BOUNDARY'),('owner','THREAD'),('point','COMPLETION'),
    ('unsupported_dependency','DEPENDENCY'),('missing_effect','SUBMIT_EFFECT'),
    ('unknown_api','UNSUPPORTED_API'),('scope_identity','IDENTITY'),('return_unknown','SYNC_FAILED'),
    ('role_conflict','IDENTITY_ROLE')])
def test_reject_does_not_fill_unknown_with_zero(damage,reason):
    c=example()
    if damage=='stream':c['effects'][2]['scope'][-1]=8
    elif damage=='failed_sync':c['sync']['return_code']=1
    elif damage=='return_unknown':c['sync']['return_code']=None
    elif damage=='physical':c['physical']['correlation']=999
    elif damage=='missing':c['apis'].remove(c['apis'][1])
    elif damage=='duplicate':c['apis'].append({**c['apis'][1],'id':'ambiguous'})
    elif damage=='pending':c['effects'][0]['end']=1
    elif damage=='boundary':c['apis'][2]['end']=11
    elif damage=='owner':c['apis'][2]['thread']=99
    elif damage=='point':c['completion_point']=11
    elif damage=='unsupported_dependency':c['apis'][1]['name']='cudaStreamWaitEvent'
    elif damage=='missing_effect':c['effects'].remove(c['effects'][2])
    elif damage=='unknown_api':c['apis'][1]['name']='cudaUnknownWork'
    elif damage=='scope_identity':c['identity']['request_id']=''
    elif damage=='role_conflict':c['identity']['run_role']='FORMAL'
    with pytest.raises(ValueError,match=reason):implementation().analyze_operation(**c)


def test_operation_pairing_is_exact_not_longest_or_nearest():
    m=implementation(); c=example()
    assert m.select_pair(c['apis'],thread=12,start=4,end=14)==(c['copy'],c['sync'])
    for extra in ({**c['copy'],'id':'second','start':5,'end':6},
                  {**c['sync'],'id':'second-sync','start':12,'end':13}):
        with pytest.raises(ValueError,match='PAIR'):
            m.select_pair(c['apis']+[extra],thread=12,start=4,end=14)
    for missing in (c['copy'],c['sync']):
        with pytest.raises(ValueError,match='PAIR'):
            m.select_pair([a for a in c['apis'] if a is not missing],thread=12,start=4,end=14)


@pytest.mark.parametrize('damage',[None,'request','run','repeat','token','phase'])
def test_structured_operation_and_completion_identity_must_agree(damage):
    m=implementation();identity=example()['identity']
    payload=dict(identity,sync_origin='natural_token_ready',token_index=0,phase='prefill')
    point=dict(identity=dict(identity),token_index=0,boundary_kind='token_ready')
    if damage in ('request','run','repeat'):payload[damage+'_id']='another'
    elif damage=='token':point['token_index']=1
    elif damage=='phase':payload['phase']='decode'
    if damage is None:m.validate_operation_identity(identity,payload,point,0,'prefill')
    else:
        with pytest.raises(ValueError,match='IDENTITY'):m.validate_operation_identity(identity,payload,point,0,'prefill')


def test_coverage_does_not_turn_same_named_copy_or_missing_effect_into_an_operation():
    m=implementation();c=example()
    assert m.coverage_entry(c['copy'],1)['status']=='ORDINARY_API_BUDGET'
    missing=m.coverage_entry(c['copy'],0)
    assert missing['status']=='UNRESOLVED_OR_OUT_OF_SCOPE' and missing['reason']=='SUBMIT_EFFECT_MISSING'
    unknown={**c['copy'],'name':'cudaUnknownOperation'}
    assert m.coverage_entry(unknown,0)['status']=='UNRESOLVED_OR_OUT_OF_SCOPE'


def test_candidate_does_not_inherit_n1_opaque_allocation_context():
    from exposedpath_v141.time_representation import time_representation, OPAQUE_ALLOCATION
    c=example()
    c['apis'].append(dict(id='allocation',name='cudaMalloc',start=1,end=2,correlation=99,thread=12,return_code=0))
    with time_representation(OPAQUE_ALLOCATION):
        with pytest.raises(ValueError,match='UNSUPPORTED_API'):
            implementation().analyze_operation(**c)


def test_multi_operation_union_and_migration_do_not_double_count_old_sync():
    # Window [0,20): H=10,Csubmit=6,E=2,Z=2. Q1[5,8),Q2[7,12).
    # New Q union [5,12), old E[10,12): migrate [5,10) exactly 5, not 8.
    atoms=[dict(start=0,end=4,category='host'),dict(start=4,end=10,category='submit'),
           dict(start=10,end=12,category='device_wait'),dict(start=12,end=14,category='residual'),
           dict(start=14,end=20,category='host')]
    r=implementation().preview_budget([0,20],atoms,[[(5,8)],[(7,12)]])
    assert r['budgets_ns']==dict(host=10,submit=1,non_submit=0,device_wait=7,residual=2,unattributed=0)
    assert r['migrated_ns']==5 and r['cuda_api_ns']==1
    assert r['migration']==[dict(start=5,end=10,from_category='submit',duration_ns=5)]
    atoms[1]['category']='unattributed'
    with pytest.raises(ValueError,match='UNATTRIBUTED'):implementation().preview_budget([0,20],atoms,[[(5,8)]])


def test_snapshot_file_chain_and_input_changes_fail_closed(tmp_path):
    m=implementation(); c=example()
    source=tmp_path/'source.bin';source.write_bytes(b'CPU synthetic source, NOT CUDA')
    c['source_sha256']=m.sha(source)
    value=dict(schema_version=m.EVIDENCE_VERSION,validation_role='CPU_SYNTHETIC_NOT_GPU_QUALIFICATION',
        source=dict(filename='source.bin',sha256=m.sha(source),size_bytes=source.stat().st_size),operation=c)
    inp=tmp_path/'evidence.json';inp.write_text(json.dumps(value),encoding='utf8')
    out=m.analyze_evidence_file(inp,tmp_path/'derived')
    assert json.loads(out.read_text())['operation']['candidate_ns']==6
    assert source.read_bytes()==b'CPU synthetic source, NOT CUDA'
    with pytest.raises(FileExistsError):m.analyze_evidence_file(inp,tmp_path/'derived')
    source.write_bytes(b'changed')
    with pytest.raises(ValueError,match='SOURCE'):m.analyze_evidence_file(inp,tmp_path/'other')


@pytest.mark.parametrize('damage',['version','source_path','source_missing','role'])
def test_evidence_contract_is_not_a_qualification_bypass(tmp_path,damage):
    m=implementation();src=tmp_path/'raw';src.write_bytes(b'fixture')
    value=dict(schema_version=m.EVIDENCE_VERSION,validation_role='CPU_SYNTHETIC_NOT_GPU_QUALIFICATION',
        source=dict(filename='raw',sha256=m.sha(src),size_bytes=7),operation=example())
    if damage=='version':value['schema_version']='future'
    if damage=='source_path':value['source']['filename']='../raw'
    if damage=='source_missing':value['source']['filename']='absent'
    if damage=='role':value['validation_role']='Formal'
    inp=tmp_path/'evidence.json';inp.write_text(json.dumps(value),encoding='utf8')
    with pytest.raises(ValueError):m.analyze_evidence_file(inp,tmp_path/'out')


def test_legal_zero_and_host_useful_work_do_not_get_called_stall():
    m=implementation();c=example()
    c['effects'][2].update(start=2,end=3);c['effects'][3].update(start=4,end=4)
    r=m.analyze_operation(**c)
    assert r['candidate_ns']==0 and r['uncovered_ns']==8
    assert r['members']==['K0','K1','D'] and r['pure_host_stall_ns'] is None
    c=example();c['copy']['end']=6 # Host can do useful work [6,10).
    assert m.analyze_operation(**c)['candidate_ns']==6


def test_source_role_and_request_conflicts_rejected_at_real_receipt_entry(tmp_path,monkeypatch):
    from test_gate8_file_chain import receipt
    m=implementation();path,files=receipt(tmp_path,monkeypatch)
    files['raw'].write_bytes(b'altered source')
    with pytest.raises(ValueError,match='HASH'):
        m.analyze_files(path,tmp_path/'does-not-matter',tmp_path/'result')
    assert not (tmp_path/'result').exists()


@pytest.mark.parametrize('damage',[None,'budget','orders','p0','role','warmup','completion','retry'])
def test_pilot_config_cannot_expand_budget_or_upgrade_old_roles(damage):
    from pathlib import Path
    m=implementation()
    c=json.loads((Path(__file__).resolve().parents[1]/'configs/coe_candidate_pilot_v0_1.json').read_text())
    if damage=='budget':c['budget']['model_processes']=10
    elif damage=='orders':c['block_orders'][0]=[4,2,1]
    elif damage=='p0':c['passes']=['pass0','pass1']
    elif damage=='role':c['data_role']='Formal'
    elif damage=='warmup':c['execution']['warmup_count']=1
    elif damage=='completion':c['execution']['completion_policy']='Cpre'
    elif damage=='retry':c['stopping']['automatic_retry']=True
    if damage is None:
        rows=m.pilot_schedule(c,'new-candidate-batch')
        assert [r['batch_size'] for r in rows]==[1,2,4,2,4,1,4,1,2]
        assert len({r['run_id'] for r in rows})==9
        assert all(r['run_role']=='PILOT' and r['pass_id']=='pass1' for r in rows)
    else:
        with pytest.raises(ValueError):m.pilot_schedule(c,'new-candidate-batch')
