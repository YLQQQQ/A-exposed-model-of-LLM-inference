"""Real 768 excerpt + independent CPU oracles; no CUDA code is executed."""
from copy import deepcopy

import pytest

from exposedpath_v141 import submit_effect_bridge as bridge
from test_cupti_timeline_adapter import capture


POLICY='cupti-api22-distinct-api-callback-boundaries/0.2.0'


def real_pair():
    # Immutable source: 358e6d17...edbf ZIP, capture 43ee54b8...0078.
    # Prefill record:417 / callback622, not a historical setup call.
    api=dict(id='record:417',domain='RUNTIME',pid=27080,tid=50908,
        correlation=381,cbid=51,name='cudaMemsetAsync',return_code=0,
        start=2490881799278300,end=2490881799296500)
    callback=dict(id=622,domain='RUNTIME',pid=27080,tid=50908,
        correlation=381,cbid=51,name='cudaMemsetAsync',return_code=0,
        start=2490881799277700,end=2490881799296500)
    return api,callback


def check(a,c,policy=POLICY):
    assert hasattr(bridge,'validate_api_callback'), 'versioned boundary validator missing'
    return bridge.validate_api_callback(a,c,policy=policy)


def test_real_prefill_record_accepts_distinct_boundaries_and_retains_original_intervals():
    a,c=real_pair();before=deepcopy((a,c))
    fact=check(a,c)
    assert fact['activity_interval_ns']==[2490881799278300,2490881799296500]
    assert fact['callback_sample_interval_ns']==[2490881799277700,2490881799296500]
    assert fact['relation']=='ACTIVITY_INSIDE_CALLBACK'
    assert (a,c)==before
    with pytest.raises(ValueError,match='API_CALLBACK_CONFLICT'):check(a,c,'LEGACY_API_ENCLOSES_CALLBACK')


def test_new_policy_does_not_simply_reverse_containment_or_replace_activity_duration():
    a,c=real_pair();c['start']=a['start']+100;c['end']=a['end']-100
    assert check(a,c)['relation']=='CALLBACK_INSIDE_ACTIVITY'
    c['start']=a['start']-100;c['end']=a['end']-100
    assert check(a,c)['relation']=='OVERLAP_NO_CONTAINMENT'


@pytest.mark.parametrize('damage,reason',[
    ('pid','API_CALLBACK_CONFLICT'),('tid','API_CALLBACK_CONFLICT'),
    ('domain','API_CALLBACK_CONFLICT'),('correlation','API_CALLBACK_CONFLICT'),
    ('cbid','API_CALLBACK_CONFLICT'),('name','API_CALLBACK_CONFLICT'),
    ('return','API_CALLBACK_CONFLICT'),('disjoint','API_CALLBACK_TIME_CONFLICT'),
    ('reverse_api','API_SCOPE'),('reverse_callback','CALL_ORDER'),
    ('unknown_time','API_SCOPE'),('unknown_policy','TIMING_POLICY'),
])
def test_identity_and_temporal_conflicts_are_not_hidden_by_boundary_fix(damage,reason):
    a,c=real_pair();policy=POLICY
    if damage in ('pid','tid','correlation','cbid'):a[damage]+=1
    if damage=='domain':a['domain']='DRIVER'
    if damage=='name':a['name']='cudaMemcpyAsync'
    if damage=='return':a['return_code']=1
    if damage=='disjoint':c.update(start=a['end']+1,end=a['end']+2)
    if damage=='reverse_api':a['start']=a['end']+1
    if damage=='reverse_callback':c['start']=c['end']+1
    if damage=='unknown_time':a.update(start=0,end=0)
    if damage=='unknown_policy':policy='whatever'
    with pytest.raises(ValueError,match=reason):check(a,c,policy)


def test_explicit_new_file_chain_keeps_old_consumer_strict_and_hand_calculated_result(tmp_path):
    import json
    from analysis import cupti_timeline as adapter
    raw=capture();scope=raw.pop('scope')
    raw['callbacks'][0]['end']+=1
    # A single sample ends at the next root's entry; no call intervals overlap
    # out of sequence, and API/effect/marker times remain the hand oracle.
    p=tmp_path/'capture.json';p.write_text(json.dumps(raw))
    s=tmp_path/'scope.json';s.write_text(json.dumps(scope))
    with pytest.raises(ValueError,match='API_CALLBACK_CONFLICT'):
        adapter.analyze_files(p,s,tmp_path/'legacy')
    r=adapter.analyze_files(p,s,tmp_path/'new',timing_policy=POLICY)
    assert r['result']['coe_ns']==20 and r['result']['sync_intersection_ns']==15
    assert r['result']['members']==['k','m','d']
    assert r['schema_version']=='cupti-timeline-adapter/0.2.0'
    assert r['result']['schema_version']=='submit-effect-bridge/0.2.0'
    assert r['result']['api_callback_timing_policy']==POLICY
    assert not (tmp_path/'legacy').exists()


def test_new_timing_rule_does_not_relax_parent_or_scope_checks():
    from analysis import cupti_timeline as adapter
    raw=capture();scope=raw.pop('scope')
    raw['callbacks'][1]['parent_id']=4
    evidence=adapter.to_evidence(raw,scope,timing_policy=POLICY)
    with pytest.raises(ValueError,match='PARENT'):bridge.analyze_scope(evidence)


def test_offline_file_validation_uses_original_inputs_without_writing_legacy_reports(tmp_path):
    from test_cupti_timeline_file_chain import fixture
    b,cfg=fixture(tmp_path/'model')
    assert hasattr(b,'validate_model_files'), 'read-only file-chain validation missing'
    paths=set((tmp_path/'model').rglob('*'))
    raw,expected=b.validate_model_files(tmp_path/'model',dict(pid=7),cfg)
    assert raw['pid']==7 and [p['actual_token_ids'] for p in expected]==[[17],[18]]
    assert set((tmp_path/'model').rglob('*'))==paths
    (tmp_path/'model/tokens.json').write_text('{}')
    with pytest.raises(ValueError,match='MODEL_FILE:tokens.json'):
        b.validate_model_files(tmp_path/'model',dict(pid=7),cfg)


@pytest.mark.parametrize('damage,reason',[
    ('thread_order','CALL_THREAD_ORDER'),('callback_scope','CALLBACK_SCOPE'),
    ('mixed_version','TIMING_POLICY'),('unknown_sdk','TIMING_SDK_VERSION'),
])
def test_new_profile_still_rejects_order_scope_and_version_conflicts(damage,reason):
    from analysis import cupti_timeline as adapter
    raw=capture();s=raw.pop('scope')
    if damage=='thread_order':raw['callbacks'][2]['start']=15
    if damage=='callback_scope':raw['callbacks'][0]['start']=9
    if damage=='unknown_sdk':raw['source']='TARGET_CUPTI'
    with pytest.raises(ValueError,match=reason):
        e=adapter.to_evidence(raw,s,timing_policy=POLICY)
        if damage=='mixed_version':e['schema_version']='submit-effect-evidence/0.1.0'
        bridge.analyze_scope(e)


def test_original_producer_file_chain_both_tokens_with_new_boundaries(tmp_path):
    import json
    from test_cupti_model_policy_reconnect import new_files,reseal
    from analysis import cupti_timeline as adapter
    folder=tmp_path/'model';b,cfg=new_files(folder)
    # All external device records are a CPU hand oracle, not GPU qualification.
    raw=json.loads((folder/'timeline/capture.json').read_bytes())
    next(c for c in raw['callbacks'] if c['id']==1)['end']+=1
    (folder/'timeline/capture.json').write_text(json.dumps(raw))
    session=json.loads((folder/'timeline/receipt.json').read_bytes())
    session['capture_sha256']=b.sha(folder/'timeline/capture.json')
    (folder/'timeline/receipt.json').write_text(json.dumps(session))
    reseal(folder)
    raw,producers=b.validate_model_files(folder,dict(pid=7),cfg)
    answers=[]
    for i,p in enumerate(producers):
        scope=adapter.select_scope(raw,p,timing_policy=POLICY)
        scope_file=tmp_path/f'scope{i}.json';scope_file.write_text(json.dumps(scope))
        answers.append(adapter.analyze_files(folder/'timeline/capture.json',scope_file,
            tmp_path/f'result{i}',timing_policy=POLICY)['result'])
    assert [r['coe_ns'] for r in answers]==[20,1]
    assert [r['terminal'] for r in answers]==['d','dsecond']
    assert not (folder/'analysis_report.json').exists()
