"""Route A over real files and real S/A/B, with explicit synthetic Raw only.

Breaks caught: requiring session-zero instead of scoped evidence, hiding a
bounded invalid sync in Host/residual, and publishing after unbounded loss.
Expected categories are hand-written; the existing independent Q0 oracle
checks timing from a separately written construction, never analyzer output.
"""
import json
import sqlite3

import pytest

from test_gate8_file_chain import input_files, api
from test_gate8_identity import sha, write_json


def setup_case(tmp_path, monkeypatch, kind):
    files = input_files(tmp_path, monkeypatch)
    if kind == 'local':
        # Lose the kernel-to-submit link in a controlled copy. The construction
        # proves the affected sync; API boundaries and launch remain observable.
        with sqlite3.connect(files['sqlite']) as conn:
            conn.execute('UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET correlationId=999')
        export = json.loads(files['export_report'].read_text())
        export['canonical_sqlite_sha256'] = sha(files['sqlite'])
        export['attempts'][0].update(sqlite_sha256=sha(files['sqlite']),
                                   sqlite_size=files['sqlite'].stat().st_size)
        write_json(files['export_report'], export)
    receipt = api().write_input_receipt(tmp_path/'input.json', artifacts=files,
        collector_version='2026.1.1.204', capture_session_id='synthetic-route-a')
    # Construction in request-relative coordinates; Raw signed timestamps stay
    # unchanged. This is the existing oracle's construction/expected interface.
    oracle = {'construction': {'activities': [
        {'activity_label':'K', 'start_ns':30, 'end_ns':60}],
        'syncs':[{'sync_label':'S','start_ns':40,'end_ns':70}]},
        'expected': {'syncs':[{'sync_label':'S', 'wait_set_activity_labels':['K'],
                             'terminal':{'status':'VALID','activity_label':'K'}}]}}
    from exposedpath_v141.q0_oracle import calculate_expected_timing
    assert calculate_expected_timing(oracle,'S') == {
        'wait_set_hidden_union_ns':10, 'wait_set_exposed_union_ns':20,
        'terminal_pre_sync_ns':10, 'terminal_overlap_sync_ns':20,
        'sync_return_tail_ns':10}
    oracle_path = write_json(tmp_path/'independent_expected.json', oracle)
    assessment = dict(schema_version='exposedpath-target-scope-assessment/0.1.0',
        input_receipt_sha256=sha(receipt), basis='SYNTHETIC_CONTROLLED_ORACLE',
        collector_integrity_status='UNKNOWN', dropped_count=None,
        scope_status={'positive':'SUFFICIENT','local':'LOCAL_GAPS','unbounded':'UNBOUNDED'}[kind],
        boundary_identity_clock='PROVEN', required_api_universe='PROVEN',
        dependency_scope='PROVEN' if kind != 'unbounded' else 'UNKNOWN',
        requests=[{'request_id':f'request-{i}','repeat_id':str(i),
                   'start_ns':-60+300*i,'end_ns':140+300*i,
                   'dependency_start_ns':-60+300*i} for i in range(2)],
        local_gaps=([{'sync_id':'cuda_sync:CUPTI_ACTIVITY_KIND_SYNCHRONIZATION:1',
                      'request_id':'request-0','repeat_id':'0','start_ns':-20,'end_ns':10,
                      'reason':'MISSING_ACTIVITY_CORRELATION'}] if kind=='local' else []),
        reasons=['IMPACT_SCOPE_UNKNOWN'] if kind=='unbounded' else [],
        evidence=[{'filename':oracle_path.name,'sha256':sha(oracle_path)}])
    return receipt, files, write_json(tmp_path/'scope_assessment.json',assessment)


@pytest.mark.parametrize('kind,expected', [('positive',[165,5,20,10,0]),
                                         ('local',[165,0,0,0,35]),
                                         ('unbounded',None)])
def test_three_actual_file_chain_outcomes(tmp_path,monkeypatch,kind,expected):
    receipt,files,assessment = setup_case(tmp_path,monkeypatch,kind)
    before={k:sha(p) for k,p in files.items()}
    out=api().process_gate8_receipt(receipt,tmp_path/'result',
                                  scope_assessment_path=assessment,synthetic_fixture=True)
    result=api().load_chain_result(out)
    report=json.loads((out.parent/'analysis/gate8_local_analysis.json').read_text())
    assert result['gate8_verdict']=='NOT_RUN'
    assert report['measurement_validity']=='NOT_ASSESSED'
    assert report['target_scope']['collector_integrity_status']=='UNKNOWN'
    assert report['target_scope']['dropped_count'] is None
    assert (out.parent/'provenance/target_scope_assessment.json').read_bytes()==assessment.read_bytes()
    if kind=='unbounded':
        assert result['status']=='BLOCKED'
        assert not list(out.parent.rglob('ab_manifest.json'))
        assert not list(out.parent.rglob('derived_manifest.json'))
    else:
        from exposedpath_v141.ab_bundle import load_ab_bundle
        ab=load_ab_bundle(out.parent/'analysis/ab/ab_manifest.json')
        row=next(r for r in ab['a_window_records'] if r['request_id']=='request-0' and r['phase']=='full_request')
        assert [row[k] for k in ('A_host_path_ns','A_cuda_api_ns','A_device_wait_ns',
                                'A_sync_residual_ns','A_unattributed_ns')]==expected
        assert row['top_level_conservation_error_ns']==0
        publication=json.loads((out.parent/'analysis/publication.json').read_text())
        window=next(r for r in publication['windows'] if r['window_id']==row['window_id'])
        assert window['mechanism_claim_allowed'] is False  # synthetic != science
        if kind=='local':
            # A's frozen reason ordering prioritizes unresolved submit semantics;
            # S/B retain the missing correlation reason independently.
            assert row['primary_reason']=='CUDA_API_SEMANTICS_UNRESOLVED'
            assert 'MISSING_ACTIVITY_CORRELATION' in row['secondary_reasons']
            assert ab['b_sync_records'][0]['validity']=='B_INVALID'
            # Missing correlation invalidates both the 5ns submit attribution
            # and 30ns sync, not just the physical sync interval.
            assert window['accounting_D_margin_ns']==-165
            assert next(r for r in ab['a_window_records'] if r['request_id']=='request-0' and r['phase']=='prefill')['A_unattributed_ns']==35
            assert next(r for r in ab['a_window_records'] if r['request_id']=='request-0' and r['phase']=='decode')['A_unattributed_ns']==0
            assert window['interpretation']=='PARTIAL_ACCOUNTING_ONLY'
            assert window['signature_published'] is False
            assert not list(out.parent.rglob('derived_manifest.json'))
        else:
            assert row['primary_reason'] is None
            assert ab['b_sync_records'][0]['validity']=='B_VALID'
            assert [ab['b_sync_records'][0][k] for k in (
                'wait_set_hidden_union_ns','wait_set_exposed_union_ns',
                'terminal_pre_sync_ns','terminal_overlap_sync_ns','sync_return_tail_ns')] == [10,20,10,20,10]
            assert window['accounting_D_margin_ns']==-150
    assert {k:sha(p) for k,p in files.items()}==before


@pytest.mark.parametrize('damage', ['hash','unknown_version','boundary','dependency','gap','evidence',
                                  'zero_claim','duplicate_request','duplicate_evidence','time_bool'])
def test_scope_claim_cannot_override_missing_or_conflicting_facts(tmp_path,monkeypatch,damage):
    receipt,_,assessment=setup_case(tmp_path,monkeypatch,'positive')
    doc=json.loads(assessment.read_text())
    if damage=='hash': doc['input_receipt_sha256']='0'*64
    elif damage=='unknown_version': doc['schema_version']='future'
    elif damage=='boundary': doc['requests'][0]['end_ns']=141
    elif damage=='dependency': doc['dependency_scope']='UNKNOWN'
    elif damage=='gap':
        doc['scope_status']='LOCAL_GAPS'
        doc['local_gaps']=[dict(request_id='request-0',repeat_id='0',start_ns=-20,end_ns=10,reason='MISSING_STREAM_ID')]
    elif damage=='evidence': doc['evidence'][0]['sha256']='0'*64
    elif damage=='zero_claim': doc['collector_integrity_status']='ZERO_CONFIRMED'; doc['dropped_count']=0
    elif damage=='duplicate_request': doc['requests'].append(doc['requests'][0])
    elif damage=='duplicate_evidence': doc['evidence'].append(doc['evidence'][0])
    else: doc['requests'][0]['dependency_start_ns']=False
    write_json(assessment,doc)
    with pytest.raises(ValueError):
        api().process_gate8_receipt(receipt,tmp_path/'out',scope_assessment_path=assessment,synthetic_fixture=True)
    assert not (tmp_path/'out').exists()


def test_synthetic_scope_assessment_never_admits_real_input(tmp_path,monkeypatch):
    receipt,_,assessment=setup_case(tmp_path,monkeypatch,'positive')
    with pytest.raises(ValueError,match='SYNTHETIC'):
        api().process_gate8_receipt(receipt,tmp_path/'out',scope_assessment_path=assessment)


@pytest.mark.parametrize('field,value', [('basis','REAL'), ('collector_integrity_status','ZERO_CONFIRMED')])
def test_direct_analysis_entry_cannot_bypass_scope_shape(tmp_path,monkeypatch,field,value):
    receipt,_,assessment=setup_case(tmp_path,monkeypatch,'positive')
    result=api().process_gate8_receipt(receipt,tmp_path/'seed',scope_assessment_path=assessment,synthetic_fixture=True)
    doc=json.loads(assessment.read_text())
    doc[field]=value
    from exposedpath_v141.gate8_analysis import analyze_gate8_local
    with pytest.raises(ValueError):
        analyze_gate8_local(result.parent/'canonical/canonical_manifest.json',
            result.parent/'projection/scope.json',tmp_path/'bad',
            capture_session_id='synthetic-route-a',scope_assessment=doc,synthetic_fixture=True)
