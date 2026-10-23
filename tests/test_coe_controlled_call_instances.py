"""Only the real one-to-many callback defect and its necessary counterexamples."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
POLICY = 'cupti-api22-call-instance-groups/0.1.0'


def sealed():
    p = ROOT / '.local/transfer/coe_controlled_c8f3dad_repair2_once.zip'
    assert hashlib.sha256(p.read_bytes()).hexdigest() == '680cb2418ee1aa3fd21c4d80f5b4e868df99a7709d3a66769833b42724cf06ed'
    with zipfile.ZipFile(p) as z:
        return (json.loads(z.read('once/bounded/run/timeline/capture.json')),
                json.loads(z.read('once/bounded/run/side.json')))


def entry():
    spec = importlib.util.spec_from_file_location('controlled_reference_entry', ROOT/'scripts/coe_cupti_controlled.py')
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def index(raw):
    from analysis.cupti_call_instances import CallInstances
    return CallInstances(raw['callbacks'], raw['pid'])


def test_original_reference_still_rejects_the_original_sealed_input():
    raw, side = sealed()
    with pytest.raises(ValueError, match='COE_CONTROLLED_CORRELATION_DUPLICATE'):
        entry().independent_reference(raw, side)


def test_sealed_reference_resolves_typed_instance_not_first_group_member():
    raw, side = sealed()
    before = deepcopy(raw)
    answer = entry().independent_reference(raw, side, call_instance_policy=POLICY)
    # Construction independently fixes early kernel, positive memset, late
    # kernel, D2H. Raw endpoints give 320+832+768 ns in both windows.
    assert answer['members'] == ['record:134','record:138','record:140','record:143']
    assert answer['terminal'] == 'record:143' and answer['excluded_ids'] == ['record:147']
    assert answer['logical_zero_call_ids'] == [152]
    assert answer['expected_coe_ns'] == answer['expected_sync_ns'] == 1920
    assert answer['wall_ns'] == 80600 and answer['complement_ns'] == 78680
    assert raw == before


def test_group_keeps_every_instance_including_repeated_same_cbid_queries():
    raw, _ = sealed(); ix = index(raw)
    assert len(ix.calls) == 160
    assert [c['id'] for c in ix.groups[('DRIVER',36144,119)]] == [120,121,122,123,124]
    assert [c['id'] for c in ix.groups[('DRIVER',36144,122)]] == [130,131,132,133,134]
    e = next(r for r in raw['records'] if r['id']=='record:134')
    assert ix.effect(e)['id'] == 145
    assert ix.root(ix.effect(e))['id'] == 139


@pytest.mark.parametrize('damage,reason', [('duplicate_id','CALL_DUPLICATE'),
    ('wrong_thread','PARENT'), ('wrong_cbid','EFFECT_MAPPING'), ('wrong_stream','EFFECT_MAPPING')])
def test_real_structure_rejects_specific_identity_and_mapping_corruption(damage, reason):
    raw, _ = sealed()
    if damage=='duplicate_id': raw['callbacks'].append(dict(raw['callbacks'][-1]))
    if damage=='wrong_thread': next(c for c in raw['callbacks'] if c['id']==145)['tid'] += 1
    if damage=='wrong_cbid': next(c for c in raw['callbacks'] if c['id']==145)['cbid'] = 678
    if damage=='wrong_stream': next(c for c in raw['callbacks'] if c['id']==145)['stream'] = 99
    with pytest.raises(ValueError, match='CUPTI_INSTANCES_'+reason):
        ix=index(raw); ix.effect(next(r for r in raw['records'] if r['id']=='record:134'))


def test_same_type_multiple_instances_are_not_resolved_by_time_nearness():
    raw, _ = sealed(); ix=index(raw)
    c=next(c for c in raw['callbacks'] if c['id']==132)
    a=dict(c, id='hypothetical-api', kind='API')
    with pytest.raises(ValueError, match='CUPTI_INSTANCES_API_AMBIGUOUS'):
        ix.api(a) # Even exact equality of endpoints cannot select among five.


def test_two_legitimate_launch_instances_in_one_group_are_ambiguous_for_effect():
    raw, _ = sealed()
    p=deepcopy(next(c for c in raw['callbacks'] if c['id']==139))
    c=deepcopy(next(c for c in raw['callbacks'] if c['id']==145))
    p.update(exit_seq=400, end=p['end']+10000)
    d=dict(c, id=999, enter_seq=350, exit_seq=351, start=c['end']+1, end=c['end']+2)
    raw['callbacks']=[p,c,d]
    with pytest.raises(ValueError, match='CUPTI_INSTANCES_EFFECT_MAPPING'):
        index(raw).effect(next(r for r in raw['records'] if r['id']=='record:134'))


def test_wrong_runtime_parent_cannot_be_repaired_by_equal_numeric_correlation():
    raw, _=sealed()
    child=next(c for c in raw['callbacks'] if c['id']==145)
    child['parent_id']=150
    with pytest.raises(ValueError, match='CUPTI_INSTANCES_PARENT'):
        index(raw)


def test_full_real_adapter_preserves_instances_and_reaches_specific_semantic_gate():
    from analysis.cupti_timeline import select_scope,to_evidence,analyze_scope
    raw,side=sealed(); m=entry()
    producer=dict(session_id=side['session_id'],pid=side['pid'],tid=side['tid'],
                  run_id=side['run_id'],actual_token_ids=side['actual_token_ids'],**side['labels'])
    scope=select_scope(raw,producer,timing_policy=m.TIMING,driver_query_policy=m.QUERIES,
                       call_instance_policy=POLICY)
    evidence=to_evidence(raw,scope,timing_policy=m.TIMING,driver_query_policy=m.QUERIES,
                         call_instance_policy=POLICY)
    assert {c['id'] for c in evidence['callbacks']} == {c['id'] for c in raw['callbacks']}
    assert next(e for e in evidence['effects'] if e['id']=='record:134')['submit_callback_id']==145
    # No new rule is invented for a lazy-module child just to pass this case.
    with pytest.raises(ValueError,match='SUBMIT_EFFECT_DRIVER_NESTED_API_UNSUPPORTED:140:cuLibraryLoadData'):
        analyze_scope(evidence)


def test_instance_file_chain_reuses_existing_contract_without_extra_driver_helpers(tmp_path):
    from tests.test_coe_cupti_controlled import controlled_files
    from analysis.cupti_timeline import select_scope,to_evidence,analyze_scope
    raw,side=controlled_files(tmp_path); m=entry()
    producer=dict(session_id=side['session_id'],pid=side['pid'],tid=side['tid'],
                  run_id=side['run_id'],actual_token_ids=side['actual_token_ids'],**side['labels'])
    scope=select_scope(raw,producer,timing_policy=m.TIMING,driver_query_policy=m.QUERIES,
                       call_instance_policy=POLICY)
    result=analyze_scope(to_evidence(raw,scope,timing_policy=m.TIMING,driver_query_policy=m.QUERIES,
                                    call_instance_policy=POLICY))
    assert result['coe_ns']==16 and result['sync_intersection_ns']==11
    assert result['members']==['effect-early_kernel','effect-positive_memset','effect-late_kernel','effect-copy']


def test_unknown_instance_policy_does_not_enable_grouped_support():
    raw,side=sealed()
    with pytest.raises(ValueError,match='COE_CONTROLLED_CALL_INSTANCE_POLICY'):
        entry().independent_reference(raw,side,call_instance_policy='unreviewed')


def test_offline_archive_entry_retains_reference_and_all_remaining_blockers(tmp_path):
    import subprocess,sys
    archive=ROOT/'.local/transfer/coe_controlled_c8f3dad_repair2_once.zip'
    before=archive.read_bytes()
    done=subprocess.run([sys.executable,'-B','-m','scripts.review_coe_controlled_offline',
        '--archive',str(archive),'--archive-sha256',hashlib.sha256(before).hexdigest(),
        '--output',str(tmp_path/'review')],cwd=ROOT,capture_output=True,timeout=30)
    assert done.returncode==2, done.stderr.decode(errors='replace')
    r=json.loads((tmp_path/'review/review.json').read_text())
    assert r['status']=='BLOCKED' and r['target_execution']=='EXECUTED'
    assert r['original_error']=='ValueError:COE_CONTROLLED_CORRELATION_DUPLICATE'
    assert r['reference']['expected_coe_ns']==1920
    assert r['error']=='ValueError:SUBMIT_EFFECT_DRIVER_NESTED_API_UNSUPPORTED:140:cuLibraryLoadData'
    assert [g['callback_id'] for g in r['remaining_semantic_gaps']]==[140,141,142,143,144]
    assert r['consumer_result'] is None and r['formal_eligible'] is False
    assert archive.read_bytes()==before
