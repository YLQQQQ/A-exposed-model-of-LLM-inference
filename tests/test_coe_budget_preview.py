"""Hand-calculated interval/source tests, not target CUDA qualification."""
from copy import deepcopy
import json

import pytest

from analysis import coe_candidate as coe


def fixture():
    identity=dict(experiment_id='e',wmpc_id='w',run_id='r',run_role='ENGINEERING',data_role='Engineering',
        pass_id='pass1',attempt_id='a',request_id='request',repeat_id='0')
    # [0,12): submit[0,10), supported sync[10,12); K[3,9), D[9,11).
    # E=1,Z=1,Csubmit=10. Q=[4,11) -> move 6 from API; old E not counted twice.
    apis=[dict(record_id='launch',api_name='cudaLaunchKernel',start_ns=0,end_ns=4,correlation_id=0),
        dict(record_id='copy',api_name='cudaMemcpyAsync',start_ns=4,end_ns=10,correlation_id=1),
        dict(record_id='sync',api_name='cudaStreamSynchronize',start_ns=10,end_ns=12,correlation_id=2)]
    acts=[dict(record_id='K',start_ns=3,end_ns=9,activity_kind='KERNEL'),
          dict(record_id='D',start_ns=9,end_ns=11,activity_kind='MEMCPY')]
    proof=[dict(sync_id='s',suffix_activity_ids=['K','D'],scope='A_INTERSECTION_ONLY_NOT_PHYSICAL_W')]
    def a(phase,start,end,host,submit,wait,residual):
        return dict(experiment_id='e',wmpc_id='w',run_id='r',run_role='ENGINEERING',pass_id='pass1',
            request_id='request',repeat_id='0',window_id=phase,phase=phase,window_start_ns=start,window_end_ns=end,
            T_window_ns=end-start,A_host_path_ns=host,A_cuda_api_ns=submit,A_cuda_api_submit_ns=submit,
            A_cuda_api_non_submit_ns=0,A_device_wait_ns=wait,A_sync_residual_ns=residual,A_unattributed_ns=0,
            primary_reason=None,secondary_reasons=[])
    admission=dict(status='A_SCOPE_ENGINEERING_ONLY',identity=identity,reasons=[],facts=dict(
        source_sqlite_sha256='a'*64,observed_api_ids=['launch','copy','sync'],conditional_suffix_proofs=[
            dict(mode='LEGACY',syncs=proof),dict(mode='PER_THREAD',syncs=deepcopy(proof))]),
        a_records=[a('full_request',0,20,8,10,1,1),a('prefill',0,12,0,10,1,1),a('decode',12,20,8,0,0,0)])
    op=dict(operation_id='op',identity=deepcopy(identity),token_index=0,phase='prefill',copy_id='copy',sync_id='sync',
        copy_interval=[4,10],sync_interval=[10,12],operation_validity='VALID_UNDER_DECLARED_SUPPORT_ASSUMPTIONS',
        members=['K','D'],activity_union=[(4,11)],candidate_ns=7,original_sync_ns=1,
        kernel_ns=5,memop_ns=2,wall_ns=8,uncovered_ns=1,reasons=[],closed_prior=[])
    candidate=dict(version=coe.VERSION,role=coe.ROLE,source_identity={k:v for k,v in identity.items() if k not in ('request_id','repeat_id')},
        source_sqlite_sha256='a'*64,operations=[op])
    records=dict(cuda_api=apis,device_activity=acts,cuda_sync=[dict(record_id='s',runtime_record_id='sync')])
    return candidate,admission,records


def test_admitted_preview_moves_same_wall_time_with_trace_sources():
    from analysis.coe_budget_preview import calculate_preview
    c,a,r=fixture();v=calculate_preview(c,a,r)
    p=next(w for w in v['windows'] if w['phase']=='prefill')
    assert p['candidate_budgets_ns']==dict(host=0,submit=4,non_submit=0,completion_exposure=7,residual=1,unattributed=0)
    assert p['migrated_ns']==6 and p['original_a']==a['a_records'][1]
    assert p['migration']==[dict(start=4,end=9,from_category='submit',duration_ns=5,
        api_ids=['copy'],sync_ids=[],operation_ids=['op'],activity_ids=['K']),
        dict(start=9,end=10,from_category='submit',duration_ns=1,
        api_ids=['copy'],sync_ids=[],operation_ids=['op'],activity_ids=['D'])]
    assert v['operations'][0]['position_union_ns']==dict(before_copy=1,inside_operation=7,after_operation=0,total_qualified_suffix=8)
    assert v['request_equals_phase_sum'] is True


@pytest.mark.parametrize('damage,reason',[
    ('unresolved','OPERATION_INVALID'),('member_missing','MEMBER_MISSING'),('duplicate','MEMBER_DUPLICATE'),
    ('old_A','ORIGINAL_A_MISMATCH'),('identity','IDENTITY'),('source','SOURCE'),
    ('proof','MODE_PROOF'),('sync_missing','SYNC_MAPPING'),('window','WINDOWS'),
    ('extra_api','API_COVERAGE'),('duplicate_sync','SYNC_MAPPING_DUPLICATE'),
    ('union','OPERATION_INTERVAL'),('failed_admission','ADMISSION_INVALID')])
def test_bad_evidence_cannot_create_preview(damage,reason):
    from analysis.coe_budget_preview import calculate_preview
    c,a,r=fixture()
    if damage=='unresolved':c['operations'][0]['operation_validity']='UNRESOLVED'
    elif damage=='member_missing':r['device_activity'].pop()
    elif damage=='duplicate':c['operations'][0]['members'].append('K')
    elif damage=='old_A':a['a_records'][0]['A_cuda_api_submit_ns']+=1
    elif damage=='identity':c['operations'][0]['identity']['request_id']='another'
    elif damage=='source':c['source_sqlite_sha256']='b'*64
    elif damage=='proof':a['facts']['conditional_suffix_proofs'][1]['syncs']=[]
    elif damage=='sync_missing':r['cuda_sync']=[]
    elif damage=='window':a['a_records'][2]['window_start_ns']=13
    elif damage=='extra_api':r['cuda_api'].append(dict(record_id='unobserved',api_name='cudaGetLastError',start_ns=1,end_ns=2,correlation_id=8))
    elif damage=='duplicate_sync':r['cuda_sync'].append(deepcopy(r['cuda_sync'][0]))
    elif damage=='union':c['operations'][0]['activity_union']=[(0,11)]
    elif damage=='failed_admission':a['status']='BLOCKED'
    with pytest.raises(ValueError,match=reason):calculate_preview(c,a,r)


def test_overlap_union_preview_and_unknown_remain_strict():
    # Existing kernel: Q[5,8) U Q[7,12) = 7, not 8; old E[10,12) excluded.
    atoms=[dict(start=0,end=4,category='host'),dict(start=4,end=10,category='submit'),
        dict(start=10,end=12,category='device_wait'),dict(start=12,end=20,category='host')]
    v=coe.preview_budget([0,20],atoms,[[(5,8)],[(7,12)],[(5,8)]])
    assert v['migrated_ns']==5 and v['budgets_ns']['device_wait']==7
    atoms[1]['category']='unattributed'
    with pytest.raises(ValueError,match='UNATTRIBUTED'):coe.preview_budget([0,20],atoms,[[(5,8)]])


def test_file_chain_rejects_changed_bound_source_before_reading_canonical(tmp_path):
    from analysis.coe_budget_preview import preview_files
    c,a,_=fixture();p=tmp_path/'candidate.json';p.write_text(json.dumps(c))
    result=tmp_path/'admitted.json';result.write_text(json.dumps(dict(
        schema_version='observation-preparation-result/0.1.0',candidate_sha256=coe.sha(p),local_admission=a)))
    p.write_text('{}')
    with pytest.raises(ValueError,match='CANDIDATE_HASH'):
        preview_files(p,result,tmp_path/'absent',tmp_path/'output')
    assert not (tmp_path/'output').exists()


def test_existing_actual_producer_entry_emits_independent_preview(tmp_path,monkeypatch):
    from test_n1_model_domain import source
    from test_observation_preparation import binding
    from analysis.observation_preparation import process
    from analysis.coe_budget_preview import VERSION
    receipt,execution,_=source(tmp_path,monkeypatch,batch_binding=binding('P',512))
    original=process(receipt,execution,tmp_path/'analysis')
    preview=tmp_path/'analysis/candidate_budget_preview.json'
    assert preview.is_file(), 'existing file-chain has no candidate-budget output'
    result=json.loads(preview.read_text(encoding='utf8'))
    saved=json.loads(original.read_text(encoding='utf8'))
    assert result['schema_version']==VERSION and result['production_A_B_modified'] is False
    assert [r['token_index'] for r in result['operations']]==[0,1]
    assert [r['original_a'] for r in result['windows']]==saved['local_admission']['a_records']
