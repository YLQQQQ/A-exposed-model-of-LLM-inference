"""Synthetic source certificates; no Nsight completeness or target qualification."""
import importlib.util
import json
import sqlite3

import pytest

from test_gate8_closed_prior import closed_sources
from test_gate8_identity import sha, write_json


def sources(tmp_path, monkeypatch, damage='unowned', mutate=None, shift=0):
    if mutate:
        import test_gate8_closed_prior as fixture
        original = fixture.project
        def project(root, inputs, host):
            with sqlite3.connect(inputs[0]) as db:
                mutate(db)
            return original(root, inputs, host)
        monkeypatch.setattr(fixture, 'project', project)
    canonical, scope, closed = closed_sources(tmp_path, monkeypatch, damage=damage, shift=shift)
    old = json.loads(closed.read_text())
    certificate = write_json(tmp_path/'prefix.json', {
        'schema_version': 'exposedpath-request-prefix-certificate/0.1.0',
        'canonical_manifest_sha256': sha(canonical), 'scope_sha256': sha(scope),
        'request_id': 'request-1', 'drain_ledger': old['drain_ledger'],
        'source_proof': {
            'basis': 'SYNTHETIC_CONTROLLED_ORACLE',
            'prefix_producers_closed': True, 'no_late_relevant_submission': True,
            'request_dependency_records_complete': True,
            'resource_lifetime_continuous': True,
        },
    })
    return canonical, scope, certificate


def run(paths, output, **kwargs):
    assert importlib.util.find_spec('exposedpath_v141.gate8_request_scope') is not None, (
        'Missing separate A-only request certificate path; physical S/B must stay unchanged')
    from exposedpath_v141.gate8_request_scope import analyze_request_scope
    return analyze_request_scope(*paths, output, **kwargs)


def test_prefix_missing_owner_preserves_physical_b_but_certifies_a(tmp_path, monkeypatch):
    paths = sources(tmp_path, monkeypatch)
    before = [sha(p) for p in paths]
    output = tmp_path/'a_scope.json'
    result = run(paths, output, synthetic_fixture=True)
    assert json.loads(output.read_text()) == result
    assert result['a_qualification'] == 'A_SCOPE_CERTIFIED'
    assert result['validation_role'] == 'SYNTHETIC_REGRESSION_ONLY'
    assert result['measurement_validity'] == 'NOT_ASSESSED'
    assert result['d_score_allowed'] is result['signature_allowed'] is False
    full = next(r for r in result['a_records'] if r['phase']=='full_request')
    # Independent arithmetic: [400,600), API [410,415), sync [440,470),
    # K [430,460): Host165/API5/wait20/residual10/unknown0.
    assert [full[k] for k in ('A_host_path_ns','A_cuda_api_ns','A_device_wait_ns',
                             'A_sync_residual_ns','A_unattributed_ns')] == [165,5,20,10,0]
    assert len(result['prefix_activity_refs']) == 1
    b = next(r for r in result['physical_b_records'] if r['request_id']=='request-1')
    assert b['validity'] != 'B_VALID'
    assert b['wait_set_hidden_union_ns'] is None
    from test_gate8_closed_prior import calculate
    original, _, original_b = calculate(paths, closed=False)
    assert result['physical_s_records'] == list(original.s_records)
    assert result['physical_b_records'] == list(original_b)
    assert [sha(p) for p in paths] == before
    with pytest.raises(ValueError, match='OUTPUT_EXISTS'):
        run(paths, output, synthetic_fixture=True)


def test_real_source_is_not_qualified_by_synthetic_certificate(tmp_path, monkeypatch):
    paths = sources(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match='SOURCE_NOT_QUALIFIED'):
        run(paths, tmp_path/'out.json')
    assert not (tmp_path/'out.json').exists()


@pytest.mark.parametrize('damage', ['failed_api', 'drain_scope_missing', 'drain_wrong_context',
    'drain_wrong_process', 'wrong_pass', 'host_reversal', 'duplicate_drain',
    'host_clock_unknown', 'host_drain_after_request', 'event', 'default_stream', 'lifecycle_change'])
def test_bad_drain_or_unsupported_dependency_blocks(tmp_path, monkeypatch, damage):
    with pytest.raises(ValueError):
        paths = sources(tmp_path, monkeypatch, damage=damage)
        run(paths, tmp_path/'out.json', synthetic_fixture=True)
    assert not (tmp_path/'out.json').exists()


@pytest.mark.parametrize('field', ['prefix_producers_closed', 'no_late_relevant_submission',
    'request_dependency_records_complete', 'resource_lifetime_continuous'])
def test_unknown_source_claim_cannot_become_zero(tmp_path, monkeypatch, field):
    paths = sources(tmp_path, monkeypatch)
    value = json.loads(paths[2].read_text())
    value['source_proof'][field] = None
    write_json(paths[2], value)
    with pytest.raises(ValueError, match='SOURCE_PROOF'):
        run(paths, tmp_path/'out.json', synthetic_fixture=True)


@pytest.mark.parametrize('sql', [
    'UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET globalTid=globalTid+1 WHERE correlationId=16',
    'UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET correlationId=999 WHERE correlationId=16',
    'UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET end=480 WHERE correlationId=16',
    'UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET end=390 WHERE correlationId=6',
    'UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET start=390,end=395 WHERE correlationId=16',
    'UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET start=400 WHERE correlationId=16',
])
def test_late_thread_mapping_or_terminal_counterevidence(tmp_path, monkeypatch, sql):
    with pytest.raises(ValueError):
        paths = sources(tmp_path, monkeypatch, mutate=lambda db:db.execute(sql))
        run(paths, tmp_path/'out.json', synthetic_fixture=True)
    assert not (tmp_path/'out.json').exists()


def test_signed_scopes_and_explicit_reader(tmp_path, monkeypatch):
    paths = sources(tmp_path, monkeypatch, shift=-550)
    output = tmp_path/'out.json'
    result = run(paths, output, synthetic_fixture=True)
    assert result['a_records'][0]['window_start_ns']==-150
    from exposedpath_v141.gate8_request_scope import load_request_scope
    assert load_request_scope(output,*paths,synthetic_fixture=True)==result
    result['a_records'][0]['A_host_path_ns'] += 1
    write_json(output,result)
    with pytest.raises(ValueError, match='RESULT_MISMATCH'):
        load_request_scope(output,*paths,synthetic_fixture=True)
    result['schema_version']='unknown'
    write_json(output,result)
    with pytest.raises(ValueError, match='RESULT_VERSION'):
        load_request_scope(output,*paths,synthetic_fixture=True)


def test_both_phases_have_literal_attribution(tmp_path, monkeypatch):
    def second_token(db):
        db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME SELECT start+120,end+120,eventClass,globalTid,correlationId+20,nameId,returnValue,callchainId FROM CUPTI_ACTIVITY_KIND_RUNTIME WHERE correlationId IN (16,17)')
        db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL SELECT start+120,end+120,deviceId,contextId,greenContextId,streamId,correlationId+20,globalPid,demangledName,shortName,graphNodeId,graphId FROM CUPTI_ACTIVITY_KIND_KERNEL WHERE correlationId=16')
        db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION SELECT start+120,end+120,deviceId,contextId,greenContextId,streamId,correlationId+20,globalPid,deprecatedSyncType,syncType,eventId,eventSyncId FROM CUPTI_ACTIVITY_KIND_SYNCHRONIZATION WHERE correlationId=17')
    paths = sources(tmp_path,monkeypatch,mutate=second_token)
    result = run(paths,tmp_path/'out.json',synthetic_fixture=True)
    expected = {'full_request':[130,10,40,20,0], 'prefill':[45,5,20,10,0], 'decode':[85,5,20,10,0]}
    for row in result['a_records']:
        assert [row[k] for k in ('A_host_path_ns','A_cuda_api_ns','A_device_wait_ns',
                                'A_sync_residual_ns','A_unattributed_ns')] == expected[row['phase']]


def test_empty_suffix_is_not_empty_physical_history(tmp_path,monkeypatch):
    def empty(db):
        db.execute('DELETE FROM CUPTI_ACTIVITY_KIND_KERNEL WHERE correlationId=16')
        db.execute('DELETE FROM CUPTI_ACTIVITY_KIND_RUNTIME WHERE correlationId=16')
    paths=sources(tmp_path,monkeypatch,mutate=empty)
    result=run(paths,tmp_path/'out.json',synthetic_fixture=True)
    full=next(r for r in result['a_records'] if r['phase']=='full_request')
    assert [full[k] for k in ('A_host_path_ns','A_cuda_api_ns','A_device_wait_ns',
                             'A_sync_residual_ns','A_unattributed_ns')]==[170,0,0,30,0]
    assert result['prefix_activity_refs']
    assert result['a_suffix_proof'][0]['suffix_activity_ids']==[]
    assert next(r for r in result['physical_b_records'] if r['request_id']=='request-1')['validity']!='B_VALID'


def test_other_valid_context_sync_is_not_empty_suffix(tmp_path,monkeypatch):
    def wrong_context(db):
        db.execute('INSERT INTO TARGET_INFO_CUDA_CONTEXT_INFO SELECT nullStreamId,hwId,vmId,processId,deviceId,2,parentContextId,isGreenContext FROM TARGET_INFO_CUDA_CONTEXT_INFO')
        db.execute('UPDATE CUPTI_ACTIVITY_KIND_SYNCHRONIZATION SET contextId=2 WHERE correlationId=17')
    paths=sources(tmp_path,monkeypatch,mutate=wrong_context)
    with pytest.raises(ValueError,match='SYNC_SCOPE'):
        run(paths,tmp_path/'out.json',synthetic_fixture=True)


def test_foreign_physical_sync_cannot_borrow_main_thread_api(tmp_path,monkeypatch):
    paths=sources(tmp_path,monkeypatch,mutate=lambda db:db.execute(
        'UPDATE CUPTI_ACTIVITY_KIND_SYNCHRONIZATION SET globalPid=99 WHERE correlationId=17'))
    with pytest.raises(ValueError,match='SYNC_SCOPE'):
        run(paths,tmp_path/'out.json',synthetic_fixture=True)


@pytest.mark.parametrize('correlation',[6,16])
def test_foreign_activity_cannot_borrow_main_thread_api(tmp_path,monkeypatch,correlation):
    paths=sources(tmp_path,monkeypatch,mutate=lambda db:db.execute(
        'UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET globalPid=99 WHERE correlationId=?',(correlation,)))
    with pytest.raises(ValueError,match='ACTIVITY_SCOPE'):
        run(paths,tmp_path/'out.json',synthetic_fixture=True)


@pytest.mark.parametrize('field', ['schema_version', 'canonical_manifest_sha256', 'scope_sha256'])
def test_version_and_lineage_fail_closed(tmp_path, monkeypatch, field):
    paths = sources(tmp_path, monkeypatch)
    value = json.loads(paths[2].read_text()); value[field] = 'unknown'
    write_json(paths[2], value)
    with pytest.raises(ValueError):
        run(paths, tmp_path/'out.json', synthetic_fixture=True)
