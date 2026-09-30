"""Literal budgets and real producer files; no target CUDA execution."""
import json
from dataclasses import replace

import pytest

from test_n1_model_domain import source
from test_v141_a_accounting import _inputs, _api, _activity, _sync, _window, _nvtx


def test_actual_producer_allocation_file_chain_is_explicitly_opaque(tmp_path, monkeypatch):
    receipt, execution, calls = source(tmp_path, monkeypatch, variant='V0', allocations=True,
                                       internal=True, default_prefix=True, vm_bits=True)
    from exposedpath_v141.gate9_domain import process_domain, load_domain
    path = process_domain(receipt, execution, tmp_path/'derived', bridge_path=calls)
    result = load_domain(path, receipt, execution, bridge_path=calls)
    assert result['adapter_version']=='exposedpath-n1-model-ownership/0.3.0'
    assert result['ab_schema_version']=='exposedpath-ab/0.6.0'
    assert len(result['allocation_records'])==2
    assert all(a['allocation_size_bytes'] is None and a['internal_wait_status']=='NOT_DECOMPOSED'
               for a in result['allocation_records'])
    for a in result['a_records']:
        n=2 if a['phase']=='full_request' else 1
        # Two launches + D2H (30), malloc (10), two syncs (20) per phase.
        assert a['A_cuda_api_ns']==40*n and a['A_cuda_api_non_submit_ns']==10*n
        assert a['A_device_wait_ns']==0 and a['A_sync_residual_ns']==20*n
        assert a['A_unattributed_ns']==0 and a['primary_reason'] is None
        assert a['A_host_path_ns']==a['T_window_ns']-60*n
        assert a['opaque_resource_management']['occupied_non_submit_ns']==10*n
    assert sorted(len(b['wait_set_activity_ids']) for b in result['b_records'])==[1,3,4,6]
    assert all(b['validity']=='B_VALID' for b in result['b_records'])
    assert not any(b['sync_id'] in {r['api_record_id'] for r in result['allocation_records']}
                   for b in result['b_records'])
    assert result['measurement_validity']=='NOT_ASSESSED' and result['dropped_records_status']=='UNKNOWN'
    assert not result['signature_allowed'] and not result['d_score_allowed']


def hand_inputs():
    """[0,100): submit10, opaque10, sync20 with wait10. No overlap oracle."""
    full=_window(); pre=_window('prefill',0,35); dec=_window('decode',35,100)
    tid=101; pid=0; scope=(0,0,1,7)
    apis=[_api('drain',-20,-10,'cudaDeviceSynchronize',1),
          _api('submit',10,20,'cudaLaunchKernel',2),
          _api('alloc',30,40,'cudaMalloc_v3020',3),
          _api('wait',60,80,'cudaStreamSynchronize',4)]
    for i,a in enumerate(apis):
        a.update(return_value=0,process_id=pid,clock_domain_id='trace',source_table='CUPTI_ACTIVITY_KIND_RUNTIME',source_rowid=i+1)
    activity=_activity('kernel',60,70,'KERNEL',2)
    activity.update(global_pid=0,clock_domain_id='trace',device_id=0,context_id=1,stream_id=7,
                    enqueue_record_id='submit',enqueue_global_tid=tid,enqueue_end_ns=20,
                    ownership_status='VALID')
    wait=_sync('physical:wait',60,80,'VALID_NONEMPTY',['kernel'])
    wait.update(device_id=0,context_id=1,stream_id=7,dependency_closure_status='COMPLETE',
                terminal=dict(status='VALID',activity_id='kernel',end_ns=70,clock_domain_id='trace'))
    raw=[dict(record_id='physical:drain',runtime_record_id='drain',runtime_mapping_count=1,
              correlation_id=1,clock_domain_id='trace',global_pid=0,device_id=0,context_id=1,stream_id=None,start_ns=-19,end_ns=-11),
         dict(record_id='physical:wait',runtime_record_id='wait',runtime_mapping_count=1,
              correlation_id=4,global_pid=0,device_id=0,context_id=1,stream_id=7,start_ns=61,end_ns=79)]
    markers=tuple({**_nvtx(w),'clock_domain_id':'trace'} for w in (full,pre,dec))
    base=_inputs(windows=(full,pre,dec),apis=tuple(apis),activities=(activity,),syncs=(wait,),nvtx=markers)
    records={**base.canonical.records,'cuda_sync':raw,'cuda_event':[],
             'stream':[dict(process_id=0,context_id=1,stream_id=7,flag=2)],
             'context':[dict(process_id=0,device_id=0,context_id=1,null_stream_id=0)]}
    canonical=replace(base.canonical,records=records,
        manifest=dict(source={'sqlite':{'sha256':'a'*64}},gate8_sources={'pass_identity':{'sha256':'b'*64}}))
    return replace(base,canonical=canonical),scope


def test_hand_budget_clips_across_phase_without_double_count():
    from exposedpath_v141.time_representation import OPAQUE_ALLOCATION,time_representation
    from exposedpath_v141.opaque_allocation import admit_allocations
    from exposedpath_v141.a_accounting import calculate_a_windows
    inputs,scope=hand_inputs()
    with time_representation(OPAQUE_ALLOCATION):
        admissions=admit_allocations(inputs,scope,'drain')
        result=calculate_a_windows(replace(inputs,opaque_allocation_admissions=admissions))
    expected={'full_request':(100,60,20,10,10,10),
              'prefill':(35,20,15,0,0,5),'decode':(65,40,5,10,10,5)}
    for a in result:
        assert tuple(a[k] for k in ('T_window_ns','A_host_path_ns','A_cuda_api_ns','A_device_wait_ns',
                                   'A_sync_residual_ns')) + (a['opaque_resource_management']['occupied_non_submit_ns'],)==expected[a['phase']]
        assert a['A_unattributed_ns']==0


@pytest.mark.parametrize('damage', ['failed','missing_end','overlap','nested_sync','duplicate_correlation',
                                   'activity_conflict','other_stream','event','invalid_downstream','drain','identity'])
def test_opaque_admission_rejects_evidence_gaps_not_just_unknown_names(damage):
    from exposedpath_v141.time_representation import OPAQUE_ALLOCATION,time_representation
    from exposedpath_v141.opaque_allocation import admit_allocations
    inputs,scope=hand_inputs(); rows=inputs.canonical.records
    alloc=next(a for a in rows['cuda_api'] if a['record_id']=='alloc')
    if damage=='failed': alloc['return_value']=1
    if damage=='missing_end': alloc['end_ns']=None
    if damage=='overlap': rows['cuda_api'] += ({**alloc,**_api('overlap',35,45,'cudaStreamIsCapturing',9)},)
    if damage=='nested_sync': rows['cuda_api'][-1].update(start_ns=32,end_ns=38)
    if damage=='duplicate_correlation': rows['cuda_api'][1]['correlation_id']=3
    if damage=='activity_conflict': rows['device_activity'][0]['correlation_id']=3
    if damage=='other_stream': rows['device_activity'][0]['stream_id']=9
    if damage=='event': rows['cuda_event'].append(dict(process_id=0,start_ns=25))
    if damage=='invalid_downstream': inputs.s_records[0].update(validity='INVALID',primary_reason='MISSING_EDGE')
    if damage=='drain': rows['cuda_api'][0]['return_value']=1
    if damage=='identity': alloc['global_tid']=202
    with time_representation(OPAQUE_ALLOCATION),pytest.raises(ValueError):
        admit_allocations(inputs,scope,'drain')


def test_name_rule_never_grants_admission_or_legacy_support():
    from exposedpath_v141.time_representation import OPAQUE_ALLOCATION,RAW_PHYSICAL,time_representation
    from exposedpath_v141.a_api_classification import classify_a_api_name
    from exposedpath_v141.a_accounting import calculate_a_windows
    inputs,_=hand_inputs()
    with time_representation(RAW_PHYSICAL):
        assert classify_a_api_name('cudaMalloc_v3020')[0] is None
        assert next(a for a in calculate_a_windows(inputs) if a['phase']=='full_request')['A_unattributed_ns']==10
    with time_representation(OPAQUE_ALLOCATION):
        assert classify_a_api_name('cudaMalloc_v3020')[0]=='non_submit'
        assert next(a for a in calculate_a_windows(inputs) if a['phase']=='full_request')['A_unattributed_ns']==10
        for name in ('cudaMallocAsync','cudaMallocManaged','cudaMalloc_v0','cudaMalloc_v3020junk','cuMemAlloc','cudaUnknown'):
            assert classify_a_api_name(name)[0] is None


def test_schema_preserves_old_time_and_b_and_explicit_roundtrip(tmp_path,monkeypatch):
    from copy import deepcopy
    from exposedpath_v141.ab_bundle import _schema,analyze_ab,load_ab_bundle,ABBundleError
    from exposedpath_v141.time_representation import OPAQUE_ALLOCATION,RAW_PHYSICAL
    from exposedpath_v141.gate9_domain import process_domain
    from exposedpath_v141.s_bundle import analyze_canonical_to_s
    old,new=_schema(version=RAW_PHYSICAL),_schema(version=OPAQUE_ALLOCATION)
    assert new['$defs']['b_sync_record']==old['$defs']['b_sync_record']
    a=deepcopy(new['$defs']['a_window_record'])
    a['required'].remove('opaque_resource_management'); a['properties'].pop('opaque_resource_management')
    assert a==old['$defs']['a_window_record']
    receipt,execution,calls=source(tmp_path,monkeypatch,variant='V0',allocations=True,internal=True)
    path=process_domain(receipt,execution,tmp_path/'domain',bridge_path=calls)
    result=json.loads(path.read_text()); p=result['allocation_records'][0]
    canonical=path.parent/'canonical/canonical_manifest.json'; scope=path.parent/'projection/scope.json'
    args=dict(scope_manifest=scope,raw_physical_sync_ids={s['sync_id'] for s in result['physical_s_records']
        if s['sync_provenance']['basis']=='RAW_PHYSICAL'},isolated_nonblocking_scope=tuple(p['scope']))
    sm=analyze_canonical_to_s(canonical,tmp_path/'s',**args)
    ab=analyze_ab(canonical,sm,tmp_path/'ab',opaque_allocation_admissions=result['allocation_records'],**args)
    loaded=load_ab_bundle(ab,canonical_manifest=canonical,s_manifest=sm)
    assert loaded['manifest']['schema_version']==OPAQUE_ALLOCATION
    assert list(loaded['a_window_records'])==result['a_records']
    bad=json.loads(ab.read_text()); bad['a_api_registry']['sha256']='f'*64; ab.write_text(json.dumps(bad))
    with pytest.raises(ABBundleError,match='REGISTRY'): load_ab_bundle(ab)


def test_admission_source_mismatch_is_not_a_budget_override():
    from copy import deepcopy
    from exposedpath_v141.time_representation import OPAQUE_ALLOCATION,time_representation
    from exposedpath_v141.opaque_allocation import admit_allocations
    from exposedpath_v141.a_accounting import calculate_a_windows
    inputs,scope=hand_inputs()
    with time_representation(OPAQUE_ALLOCATION):
        proofs=deepcopy(admit_allocations(inputs,scope,'drain')); proofs[0]['start_ns']=29
        with pytest.raises(ValueError,match='SOURCE_MISMATCH'):
            calculate_a_windows(replace(inputs,opaque_allocation_admissions=proofs))


@pytest.mark.parametrize('name',['cudaDeviceSynchronize_v0','cudaDeviceSynchronize_v3020junk'])
def test_malformed_drain_suffix_cannot_grant_allocation_admission(name):
    from exposedpath_v141.time_representation import OPAQUE_ALLOCATION,time_representation
    from exposedpath_v141.opaque_allocation import admit_allocations
    inputs,scope=hand_inputs(); inputs.canonical.records['cuda_api'][0]['api_name']=name
    with time_representation(OPAQUE_ALLOCATION),pytest.raises(ValueError,match='DRAIN'):
        admit_allocations(inputs,scope,'drain')


@pytest.mark.parametrize('field,bad',[('clock_domain_id','foreign'),('correlation_id',99)])
def test_drain_mapping_cannot_cross_clock_or_correlation(field,bad):
    from exposedpath_v141.time_representation import OPAQUE_ALLOCATION,time_representation
    from exposedpath_v141.opaque_allocation import admit_allocations
    inputs,scope=hand_inputs(); inputs.canonical.records['cuda_sync'][0][field]=bad
    with time_representation(OPAQUE_ALLOCATION),pytest.raises(ValueError,match='DRAIN_MAPPING'):
        admit_allocations(inputs,scope,'drain')


def test_empty_sync_proof_is_consistent_but_does_not_grant_model_b_validity():
    from exposedpath_v141.time_representation import OPAQUE_ALLOCATION,time_representation
    from exposedpath_v141.opaque_allocation import admit_allocations
    inputs,scope=hand_inputs(); s=inputs.s_records[0]
    s.update(validity='VALID_EMPTY',wait_set_activity_ids=[],terminal=dict(status='NOT_APPLICABLE'))
    with time_representation(OPAQUE_ALLOCATION): assert len(admit_allocations(inputs,scope,'drain'))==1
    # Final N1 continues to demand B_VALID; no empty B is converted here.
