"""Finite API22 controlled launch prefix only; altered cases are CPU fixtures."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from tests.test_coe_controlled_call_instances import sealed,entry,POLICY as CALL_POLICY

POLICY='cupti-api22-controlled-nested-launch/0.1.0'


def evidence():
    from analysis.cupti_timeline import select_scope,to_evidence
    raw,side=sealed();m=entry()
    producer=dict(session_id=side['session_id'],pid=side['pid'],tid=side['tid'],run_id=side['run_id'],
                  actual_token_ids=side['actual_token_ids'],**side['labels'])
    scope=select_scope(raw,producer,timing_policy=m.TIMING,driver_query_policy=m.QUERIES,
                       call_instance_policy=CALL_POLICY)
    v=to_evidence(raw,scope,timing_policy=m.TIMING,driver_query_policy=m.QUERIES,
                  call_instance_policy=CALL_POLICY)
    v.update(schema_version='submit-effect-evidence/0.3.2',nested_launch_policy=POLICY,
             resource_records=deepcopy([r for r in raw['records'] if r['kind'] in ('CONTEXT','STREAM')]))
    return raw,side,v


def validate(v):
    from exposedpath_v141.cupti_nested_launch_control import validate_nested_launch_controls
    return validate_nested_launch_controls(v)


def test_real_five_roles_preserve_context_and_do_not_invent_stream_or_module_handles():
    raw,side,v=evidence();before=deepcopy(v)
    facts=validate(v)
    assert [f['callback_id'] for f in facts]==[140,141,142,143,144]
    assert [f['role'] for f in facts]==['LIBRARY_LOAD','CONTEXT_PUSH','MODULE_HANDLE','CONTEXT_POP','FUNCTION_HANDLE']
    assert all(f['budget_owner_api_id']=='record:135' and f['additive_api_budget_ns']==0 for f in facts)
    assert all(f['api_interval_ns'] is None and f['library_module_function_handle_chain']=='NOT_CAPTURED_NOT_CLAIMED'
               and f['pure_cpu_cost'] is False for f in facts)
    assert all(f['observed_context_uid']==1 and f['native_stream_from_unbound_helper'] is None for f in facts)
    assert all(f['following_launch_call_id']==145 and f['kernel_effect_id']=='record:134' for f in facts)
    assert v==before


@pytest.mark.parametrize('damage,reason',[
    ('wrong_domain','IDENTITY'),('wrong_cbid','IDENTITY'),('failed_load','RETURN'),
    ('wrong_parent','PARENT'),('context_change','CONTEXT'),('missing_exit_context','CONTEXT'),
    ('missing_native_context','CONTEXT'),('missing_pop','CHILD_PATTERN'),
    ('unknown_child','CHILD_PATTERN'),('extra_effect','LAUNCH_EFFECT_COVERAGE'),
    ('extra_sync','COMPLETION'),('missing_resource','RESOURCE'),('resource_conflict','RESOURCE'),
    ('missing_launch_effect','LAUNCH_EFFECT_COVERAGE')])
def test_exact_rules_refuse_missing_ambiguous_or_conflicting_evidence(damage,reason):
    _,_,v=evidence();calls={c['id']:c for c in v['callbacks']}
    if damage=='wrong_domain':calls[140]['domain']='RUNTIME'
    if damage=='wrong_cbid':calls[140]['cbid']=999
    if damage=='failed_load':calls[140]['return_code']=1
    if damage=='wrong_parent':calls[140]['parent_id']=150
    if damage=='context_change':calls[143]['exit_context']=99
    if damage=='missing_exit_context':del calls[143]['exit_context']
    if damage=='missing_native_context':calls[141]['native_context']=0
    if damage=='missing_pop':v['callbacks']=[c for c in v['callbacks'] if c['id']!=143]
    if damage=='unknown_child':calls[142].update(name='cuUnknown',cbid=999)
    if damage=='extra_effect':v['effects'].append(dict(v['effects'][0],id='extra-effect'))
    if damage=='extra_sync':v['synchronizations'].append(dict(v['synchronizations'][0],
        id='extra-sync',callback_id=139,callback_bridge_ids=[140]))
    if damage=='missing_resource':v['resource_records']=[]
    if damage=='resource_conflict':
        for r in v['resource_records']:
            if r['kind']=='CONTEXT':r['device']=99
    if damage=='missing_launch_effect':v['effects']=[e for e in v['effects'] if e['id']!='record:134']
    with pytest.raises(ValueError,match='NESTED_LAUNCH_'+reason):validate(v)


def test_same_raw_full_consumer_matches_prior_literal_reference_and_keeps_all_calls():
    from analysis.cupti_timeline import select_scope,to_evidence,analyze_scope
    raw,side=sealed();before=deepcopy(raw);m=entry()
    ref=m.independent_reference(raw,side,call_instance_policy=CALL_POLICY)
    assert ref['members']==['record:134','record:138','record:140','record:143'] and ref['expected_coe_ns']==1920
    producer=dict(session_id=side['session_id'],pid=side['pid'],tid=side['tid'],run_id=side['run_id'],
                  actual_token_ids=side['actual_token_ids'],**side['labels'])
    scope=select_scope(raw,producer,timing_policy=m.TIMING,driver_query_policy=m.QUERIES,
                       call_instance_policy=CALL_POLICY,nested_launch_policy=POLICY)
    v=to_evidence(raw,scope,timing_policy=m.TIMING,driver_query_policy=m.QUERIES,
                  call_instance_policy=CALL_POLICY,nested_launch_policy=POLICY)
    r=analyze_scope(v)
    assert len(v['callbacks'])==160 and len(r['nested_launch_controls'])==5
    assert r['members']==['record:134','record:138','record:140','record:143']
    assert r['terminal']=='record:143' and r['logical_zero_call_ids']==[152]
    assert r['coe_ns']==r['sync_intersection_ns']==1920 and r['operation_wall_ns']==80600
    assert raw==before


def test_observed_child_api_is_provenance_not_an_extra_accounting_owner():
    from analysis.cupti_timeline import analyze_scope
    _,_,v=evidence();a=analyze_scope(v)
    c=next(c for c in v['callbacks'] if c['id']==140)
    v['apis'].append(dict(c,kind='API',id='observed-child-api',callback_id=140))
    b=analyze_scope(v)
    assert b['accounting_api_union_ns']==a['accounting_api_union_ns']
    assert b['accounting_api_sources']==a['accounting_api_sources']
    f=next(f for f in b['nested_launch_controls'] if f['callback_id']==140)
    assert f['api_id']=='observed-child-api' and f['api_interval_ns']==[c['start'],c['end']]
    assert f['additive_api_budget_ns']==0


@pytest.mark.parametrize('version,policy,reason',[
    ('submit-effect-evidence/0.3.1',POLICY,'NESTED_LAUNCH_POLICY'),
    ('submit-effect-evidence/0.3.2','unknown','NESTED_LAUNCH_POLICY'),
    ('submit-effect-evidence/9.9.9',POLICY,'VERSION')])
def test_old_or_unknown_contracts_cannot_silently_enable_the_new_rules(version,policy,reason):
    from analysis.cupti_timeline import analyze_scope
    _,_,v=evidence();v.update(schema_version=version,nested_launch_policy=policy)
    with pytest.raises(ValueError,match='SUBMIT_EFFECT_'+reason):analyze_scope(v)


def test_offline_explicit_policy_adjudicates_only_the_local_connection(tmp_path):
    import subprocess,sys,hashlib
    from tests.test_coe_controlled_call_instances import ROOT
    archive=ROOT/'.local/transfer/coe_controlled_c8f3dad_repair2_once.zip';before=archive.read_bytes()
    done=subprocess.run([sys.executable,'-B','-m','scripts.review_coe_controlled_offline',
        '--archive',str(archive),'--archive-sha256',hashlib.sha256(before).hexdigest(),
        '--output',str(tmp_path/'review'),'--nested-launch-policy',POLICY],
        cwd=ROOT,capture_output=True,timeout=30)
    assert done.returncode==0,done.stdout.decode(errors='replace')+done.stderr.decode(errors='replace')
    r=json.loads((tmp_path/'review/review.json').read_text())
    assert r['verdicts']=={'independent_reference':'PASS','consumer_admission':'PASS','controlled_connection':'PASS'}
    assert r['original_status']=='BLOCKED' and r['original_post_control_status']=='NOT_REACHED_AFTER_WORKER_REFUSAL'
    assert r['formal_eligible'] is False and r['full_Q0']=='NOT_GRANTED'
    assert r['consumer_result']['coe_ns']==1920 and r['remaining_semantic_gaps']==[]
    assert archive.read_bytes()==before
