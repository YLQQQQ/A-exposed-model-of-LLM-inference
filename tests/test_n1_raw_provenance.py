"""CPU file-chain expectations from two launches + D2H, not S/A outputs."""
import json
from copy import deepcopy

import pytest
from test_n1_model_domain import source


def test_internal_raw_identity_preserves_unknown_source_labels(tmp_path, monkeypatch):
    receipt, execution, calls = source(tmp_path, monkeypatch, variant='V0', internal=True,
                                       default_prefix=True, vm_bits=True)
    from exposedpath_v141.gate9_domain import process_domain, load_domain
    path = process_domain(receipt, execution, tmp_path/'derived', bridge_path=calls)
    result = load_domain(path, receipt, execution, bridge_path=calls)
    assert result['adapter_version'] == 'exposedpath-n1-model-ownership/0.2.0'
    assert result['ab_schema_version'] == 'exposedpath-ab/0.5.0'
    raw = [s for s in result['physical_s_records'] if s['sync_provenance']['basis']=='RAW_PHYSICAL']
    assert len(raw) == 2
    # Internal wait follows first launch. The second follows the prior 3 activities.
    assert [len(s['wait_set_activity_ids']) for s in raw] == [1, 4]
    assert all(s['validity']=='VALID_NONEMPTY' and s['dependency_closure_status']=='COMPLETE'
               and s['terminal']['status']=='VALID' for s in raw)
    assert all(s['sync_origin'] is s['callsite_id'] is s['sync_ordinal'] is None for s in raw)
    assert all(s['sync_provenance']['physical_source']['global_pid'] > 1 << 48 for s in raw)
    assert sorted(len(b['wait_set_activity_ids']) for b in result['b_records']) == [1, 3, 4, 6]
    assert all(b['validity']=='B_VALID' for b in result['b_records'])
    for a in result['a_records']:
        n = 2 if a['phase']=='full_request' else 1
        assert a['A_cuda_api_ns']==30*n and a['A_device_wait_ns']==0
        assert a['A_sync_residual_ns']==20*n and a['A_unattributed_ns']==0
        assert a['A_host_path_ns']==a['T_window_ns']-50*n
    assert result['measurement_validity']=='NOT_ASSESSED'


def test_allocation_remains_blocked_but_internal_raw_sync_is_recovered(tmp_path, monkeypatch):
    receipt, execution, calls = source(tmp_path, monkeypatch, variant='V0', allocations=True,
                                       internal=True, default_prefix=True)
    from exposedpath_v141.gate9_domain import process_domain
    with pytest.raises(ValueError, match='MODEL_UNSUPPORTED_API:') as error:
        process_domain(receipt, execution, tmp_path/'derived', bridge_path=calls)
    details = json.loads(str(error.value).split('MODEL_UNSUPPORTED_API:', 1)[1])
    assert details['physical_b_failures']==[]
    assert len(details['unsupported_apis'])==2
    for api in details['unsupported_apis']:
        assert api['category'] is None
        assert api['semantic_role']=='KNOWN_ALLOCATION'
        assert api['completion_support']=='UNSUPPORTED'
        assert api['completion_scope'] is None
        assert api['registry_rule_id']=='ALLOCATION-CUDAMALLOC-001'
    assert not (tmp_path/'derived/domain.json').exists()


@pytest.mark.parametrize('name', ['cudaMalloc', 'cudaMalloc_v3020', 'cudaMalloc_v12040'])
def test_known_allocation_is_not_a_completion_or_non_submit_rule(name):
    from exposedpath_v141.allocation_semantics import describe_allocation
    from exposedpath_v141.a_api_classification import classify_a_api_name
    result = describe_allocation(name)
    assert result['semantic_role']=='KNOWN_ALLOCATION'
    assert result['completion_support']=='UNSUPPORTED' and result['completion_scope'] is None
    assert classify_a_api_name(name)[0] is None


@pytest.mark.parametrize('name', ['cudaMalloc_v0', 'cudaMalloc_v3020junk', 'cudaMallocAsync',
                                 'cudaMallocManaged', 'cuMemAlloc', 'unknownAllocation'])
def test_unknown_allocation_like_names_cannot_inherit_rule(name):
    from exposedpath_v141.allocation_semantics import describe_allocation
    assert describe_allocation(name) is None


def test_raw_proof_version_shape_and_unknown_labels_are_strict():
    from exposedpath_v141.raw_sync_provenance import validate_provenance
    with pytest.raises(ValueError, match='PROVENANCE'):
        validate_provenance({'sync_provenance': {'schema_version':'future', 'basis':'RAW_PHYSICAL',
                                               'physical_source':None}})
    with pytest.raises(ValueError, match='PROVENANCE'):
        validate_provenance({'sync_provenance': {'schema_version':'exposedpath-sync-provenance/0.1.0',
                                               'basis':'RAW_PHYSICAL', 'physical_source':{}}})


@pytest.mark.parametrize('damage,variant', [('unmarked_token','V0'), ('unmarked_intervention','Vsync'),
                                           ('raw_marker_conflict','V0'), ('duplicate_map','V0'),
                                           ('stream','V0'), ('correlation','V0'), ('dependency','V0')])
def test_raw_path_never_replaces_mandatory_labels_or_conflicting_evidence(tmp_path,monkeypatch,damage,variant):
    receipt,execution,calls=source(tmp_path,monkeypatch,variant=variant,internal=True,damage=damage)
    from exposedpath_v141.gate9_domain import process_domain
    with pytest.raises(ValueError):
        process_domain(receipt,execution,tmp_path/'derived',bridge_path=calls)
    assert not (tmp_path/'derived/domain.json').exists()


def test_new_s_ab_roundtrip_and_legacy_version_rejection(tmp_path,monkeypatch):
    from exposedpath_v141.gate9_domain import process_domain,load_domain
    from exposedpath_v141.s_bundle import analyze_canonical_to_s
    from exposedpath_v141.ab_bundle import analyze_ab,load_ab_bundle,ABBundleError,_schema,_validate_schema
    from exposedpath_v141.time_representation import SIGNED,RAW_PHYSICAL
    from exposedpath_v141.ab_inputs import _load_s_records
    receipt,execution,calls=source(tmp_path,monkeypatch,variant='V0',internal=True)
    path=process_domain(receipt,execution,tmp_path/'derived',bridge_path=calls)
    result=json.loads(path.read_text())
    canonical=path.parent/'canonical/canonical_manifest.json'; scope=path.parent/'projection/scope.json'
    raw=[s for s in result['physical_s_records'] if s['sync_provenance']['basis']=='RAW_PHYSICAL']
    ids={s['sync_id'] for s in raw}; p=raw[0]['sync_provenance']['physical_source']
    args=dict(scope_manifest=scope,raw_physical_sync_ids=ids,
              isolated_nonblocking_scope=tuple(p[k] for k in ('global_pid','device_id','context_id','stream_id')))
    s=analyze_canonical_to_s(canonical,tmp_path/'s',**args)
    sm,sr=_load_s_records(s)
    assert sm['schema_version']=='exposedpath-s-layer/0.4.0'
    assert {r['sync_id'] for r in sr if r['sync_provenance']['basis']=='RAW_PHYSICAL'}==ids
    ab=analyze_ab(canonical,s,tmp_path/'ab',**args)
    loaded=load_ab_bundle(ab,canonical_manifest=canonical,s_manifest=s)
    assert loaded['manifest']['schema_version']==RAW_PHYSICAL
    assert list(loaded['a_window_records'])==result['a_records']
    from exposedpath_v141.gate8_scope import build_projected_ab_inputs
    from exposedpath_v141.ab_inputs import _validate_s_join
    from exposedpath_v141.time_representation import time_representation
    with time_representation(RAW_PHYSICAL):
        inputs=build_projected_ab_inputs(canonical,scope,raw_physical_sync_ids=ids,
                                        isolated_nonblocking_scope=args['isolated_nonblocking_scope'])
        for field,bad in [('raw_sqlite_sha256','f'*64),('model_forward_record_id','foreign'),
                          ('projection_record_ids',['projection:foreign']),('clock_domain_id','other')]:
            changed=deepcopy(list(inputs.s_records))
            target=next(r for r in changed if r['sync_provenance']['basis']=='RAW_PHYSICAL')
            target['sync_provenance']['physical_source'][field]=bad
            with pytest.raises(ValueError,match='PROVENANCE'):
                _validate_s_join(inputs.canonical,tuple(changed))
    with pytest.raises(ValueError,match='VERSION_MISMATCH'):
        analyze_ab(canonical,s,tmp_path/'wrong_version',scope_manifest=scope)
    new_b=next(r for r in loaded['b_sync_records'] if r['sync_provenance']['basis']=='RAW_PHYSICAL')
    with pytest.raises(ABBundleError):
        _validate_schema(_schema(version=SIGNED),'b_sync_record',new_b,'old B')
    with pytest.raises(ABBundleError,match='VERSION_UNSUPPORTED'):
        _schema(version='exposedpath-ab/future')
    # A foreign proof hash cannot be adopted simply by rewriting the envelope.
    saved=json.loads(path.read_text()); saved['physical_s_records'][0]['sync_provenance']['schema_version']='future'
    path.write_text(json.dumps(saved))
    with pytest.raises(ValueError,match='RESULT_MISMATCH'):
        load_domain(path,receipt,execution,bridge_path=calls)


def physical_source():
    """Independent Raw facts: success [10,20), physical [11,19), stream 7.

    This does not supply W/terminal: recovery must still prove them separately.
    """
    pid=13; tid=(pid<<24)|4
    identity=dict(experiment_id='e',wmpc_id='w',run_id='r',run_role='ENGINEERING',
                  pass_id='pass1',request_id='q',repeat_id='0',attempt_id='a',data_role='Engineering')
    api=dict(record_id='api:3',source_table='CUPTI_ACTIVITY_KIND_RUNTIME',source_rowid=3,
             correlation_id=9,return_value=0,clock_domain_id='trace',global_tid=tid,process_id=pid,
             start_ns=10,end_ns=20,api_name='cudaStreamSynchronize_v3020')
    sync=dict(record_id='sync:2',source_table='CUPTI_ACTIVITY_KIND_SYNCHRONIZATION',source_rowid=2,
        runtime_record_id='api:3',runtime_mapping_count=1,correlation_id=9,clock_domain_id='trace',
        global_pid=pid<<24,runtime_global_tid=tid,device_id=0,context_id=1,stream_id=7,
        start_ns=11,end_ns=19,role='HOST_BLOCKING_SYNC',sync_kind='STREAM',sync_identity_status='INVALID',
        ownership_status='VALID',ownership_reasons=[],sync_origin=None,callsite_id=None,sync_ordinal=None,
        invocation_identity={**identity, 'phase':'prefill', 'kind':'phase'},request_id='q',repeat_id='0',
        sync_owner_phase='prefill',ownership_range_record_ids=['projection:'+'c'*64+':1'])
    forward=dict(record_id='nvtx:4',start_ns=5,end_ns=25,global_tid=tid,clock_domain_id='trace',
        structured_identity=None,text='EXPOSEDPATH_N1_MODEL_V1:'+json.dumps(dict(
            schema_version='exposedpath-n1-model-calls/0.1.0',operation='model_forward',
            phase='prefill',identity=identity)))
    bundle=dict(manifest=dict(source={'sqlite':{'sha256':'a'*64}},
                gate8_sources={'pass_identity':{'sha256':'b'*64}}),
                records=dict(cuda_api=[api],cuda_sync=[sync],nvtx=[forward]))
    inventory=dict(input_status='VALID',syncs=[sync],isolated_nonblocking_scope=(pid<<24,0,1,7))
    return bundle,inventory,sync,api


@pytest.mark.parametrize('damage', ['success','mapping','clock','scope','process','ownership',
                                   'partial_label','quality','conflicting_marker','missing_forward'])
def test_raw_physical_facts_must_not_be_guessed(damage):
    from exposedpath_v141.raw_sync_provenance import attach_inventory_provenance
    bundle,inventory,sync,api=physical_source()
    if damage=='success': api['return_value']=1
    if damage=='mapping': sync['runtime_mapping_count']=2
    if damage=='clock': sync['clock_domain_id']='other'
    if damage=='scope': sync['context_id']=2
    if damage=='process': api['process_id']=99
    if damage=='ownership': sync['ownership_status']='AMBIGUOUS'
    if damage=='partial_label': sync['callsite_id']='invented'
    if damage=='quality': inventory['input_status']='INVALID'
    if damage=='missing_forward': bundle['records']['nvtx']=[]
    if damage=='conflicting_marker':
        bundle['records']['nvtx'].append(dict(start_ns=10,end_ns=20,structured_identity={'kind':'sync'},
            text='EXPOSEDPATH_JSON_V1:{}'))
    with pytest.raises(ValueError,match='PROVENANCE'):
        attach_inventory_provenance(bundle,inventory,{'sync:2'})


def test_raw_proof_is_positive_but_never_fills_source_labels():
    from exposedpath_v141.raw_sync_provenance import attach_inventory_provenance,validate_provenance
    bundle,inventory,sync,api=physical_source()
    attach_inventory_provenance(bundle,inventory,{'sync:2'})
    p=inventory['sync_provenance']['sync:2']
    assert p['basis']=='RAW_PHYSICAL'
    record=dict(sync_id='sync:2',sync_kind='STREAM',sync_origin=None,callsite_id=None,sync_ordinal=None,
        request_id='q',repeat_id='0',sync_owner_phase='prefill',host_start_ns=10,host_end_ns=20,
        sync_provenance=p)
    validate_provenance(record)
    assert p['physical_source']['correlation_id']==9 and p['physical_source']['model_forward_record_id']=='nvtx:4'
    for field in ('sync_origin','callsite_id','sync_ordinal'):
        conflicting=deepcopy(record); conflicting[field]='invented'
        with pytest.raises(ValueError,match='PROVENANCE_SOURCE_LABEL_CONFLICT'):
            validate_provenance(conflicting)


def test_new_schema_keeps_signed_time_and_duration_contract_exact():
    from exposedpath_v141.ab_bundle import _schema
    from exposedpath_v141.time_representation import SIGNED,RAW_PHYSICAL
    old,new=_schema(version=SIGNED),_schema(version=RAW_PHYSICAL)
    assert new['$defs']['a_window_record']==old['$defs']['a_window_record']
    b=deepcopy(new['$defs']['b_sync_record']); b['required'].remove('sync_provenance')
    b['properties'].pop('sync_provenance')
    assert b==old['$defs']['b_sync_record']


def test_previous_adapter_files_remain_explicitly_readable(tmp_path,monkeypatch):
    from exposedpath_v141.gate9_domain import process_domain,load_domain
    from exposedpath_v141.n1_model_scope import calculate_n1_model,LEGACY_ADAPTER
    receipt,execution,calls=source(tmp_path,monkeypatch,variant='V0')
    path=process_domain(receipt,execution,tmp_path/'derived',bridge_path=calls)
    saved=json.loads(path.read_text()); files=saved['files']
    legacy=calculate_n1_model(path.parent,receipt,execution,calls,adapter_version=LEGACY_ADAPTER)
    assert 'ab_schema_version' not in legacy
    assert all('sync_provenance' not in s for s in legacy['physical_s_records'])
    path.write_text(json.dumps(dict(legacy,files=files)))
    assert load_domain(path,receipt,execution,bridge_path=calls)['adapter_version']==LEGACY_ADAPTER
    legacy['adapter_version']='exposedpath-n1-model-ownership/99.0'
    path.write_text(json.dumps(dict(legacy,files=files)))
    with pytest.raises(ValueError,match='MODEL_ADAPTER_VERSION'):
        load_domain(path,receipt,execution,bridge_path=calls)
