"""Synthetic file evidence and hand arithmetic; not target-stack qualification."""
import inspect
import json
import sqlite3
from copy import deepcopy

import pytest
from test_gate8_signed_time import signed_inputs
from test_gate8_boundaries import project, record_request
from test_gate8_identity import write_json, sha


def closed_sources(tmp_path, monkeypatch, requests=2, shift=0, damage=None, return_inputs=False):
    from exposedpath.gate8_drain import DrainRecorder, DRAIN_VERSION
    inputs, host = signed_inputs(tmp_path, monkeypatch, shift=shift, return_sources=True)
    ledger = json.loads(inputs[3].read_text())
    if requests == 3:
        extra = deepcopy(ledger['requests'][-1])
        extra['identity'].update(request_id='request-2', repeat_id='2')
        extra.update(expected_boundary_ids=['r2','t2-0','t2-1'], observed_boundary_ids=['r2','t2-0','t2-1'])
        ledger['requests'].append(extra)
        ledger['planned_request_ids'].append('request-2')
        write_json(inputs[3], ledger)
    drain_records = []
    with sqlite3.connect(inputs[0]) as db:
        tid = db.execute('SELECT globalTid FROM CUPTI_ACTIVITY_KIND_RUNTIME LIMIT 1').fetchone()[0]
        for index in range(1, requests):
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME SELECT start+?,end+?,eventClass,globalTid,correlationId+?,nameId,returnValue,callchainId FROM CUPTI_ACTIVITY_KIND_RUNTIME WHERE correlationId IN (7,6)',(300*index,300*index,10*index))
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL SELECT start+?,end+?,deviceId,contextId,greenContextId,streamId,correlationId+?,globalPid,demangledName,shortName,graphNodeId,graphId FROM CUPTI_ACTIVITY_KIND_KERNEL WHERE correlationId=6',(300*index,300*index,10*index))
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION SELECT start+?,end+?,deviceId,contextId,greenContextId,streamId,correlationId+?,globalPid,deprecatedSyncType,syncType,eventId,eventSyncId FROM CUPTI_ACTIVITY_KIND_SYNCHRONIZATION WHERE correlationId=7',(300*index,300*index,10*index))
        if requests == 3:
            records, labels, ranges = record_request(monkeypatch, extra['identity'], extra['expected_boundary_ids'])
            write_json(host, json.loads(host.read_text()) + records)
            for t,label in zip((700,780,900), labels):
                db.execute('INSERT INTO NVTX_EVENTS(start,end,eventType,text,globalTid) VALUES (?,NULL,34,?,?)',(t+shift,label,tid))
            for (a,b),label in zip(((730,780),(850,900)), ranges):
                db.execute('INSERT INTO NVTX_EVENTS(start,end,eventType,text,globalTid) VALUES (?,?,59,?,?)',(a+shift,b+shift,label,tid))
        db.execute("INSERT INTO StringIds VALUES (21,'cudaDeviceSynchronize')")
        db.execute("INSERT INTO ENUM_CUPTI_SYNC_TYPE VALUES (2,'CONTEXT','Context synchronize')")
        for index, request in enumerate(ledger['requests']):
            labels = []
            ticks = iter((index*1000000+10, index*1000000+20))
            monkeypatch.setattr('exposedpath.gate8_drain.threading.get_native_id', lambda:4)
            recorder = DrainRecorder(request['identity'], f'drain-{index}', 0,
                                    clock_ns=lambda:next(ticks), push=labels.append, pop=lambda:None)
            recorder.observe(lambda:None)
            drain_records.append(recorder.record)
            db.execute('INSERT INTO NVTX_EVENTS(start,end,eventType,text,globalTid) VALUES (?,?,59,?,?)',
                       (75+index*300+shift,95+index*300+shift,labels[0],tid))
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME(start,end,eventClass,globalTid,correlationId,nameId,returnValue) VALUES (?,?,0,?,?,21,0)',
                       (80+index*300+shift,90+index*300+shift,tid,100+index))
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION VALUES (?,?,0,1,NULL,4294967295,?,?,NULL,2,4294967295,NULL)',
                       (81+index*300+shift,89+index*300+shift,100+index,tid-(tid%2**24)))
        lifetime = dict(schema_version='exposedpath-stream-lifetime-marker/0.1.0',
                        generation='live-0', mode='CONTINUOUS_OWNED', logical_device=0,
                        producer_source_sha256=ledger['runner_source_sha256'],
                        identity={k:ledger[k] for k in ('run_id','pass_id','attempt_id','pid')})
        db.execute('INSERT INTO NVTX_EVENTS(start,end,eventType,text,globalTid) VALUES (?,?,59,?,?)',
                   (shift,1000+shift,'EXPOSEDPATH_STREAM_LIFETIME_V1:'+json.dumps(lifetime),tid))
        if damage == 'missing_api':
            db.execute('DELETE FROM CUPTI_ACTIVITY_KIND_RUNTIME WHERE correlationId=101')
        elif damage == 'failed_api':
            db.execute('UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET returnValue=1 WHERE correlationId=101')
        elif damage == 'unowned':
            db.execute('UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET start=20+?,end=25+? WHERE correlationId=6',(shift,shift))
        elif damage == 'old_decode':
            db.execute('UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET start=220+?,end=225+? WHERE correlationId=6',(shift,shift))
            db.execute('UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET start=250+?,end=280+? WHERE correlationId=6',(shift,shift))
        elif damage == 'event':
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_CUDA_EVENT VALUES (?,0,1,NULL,2,8,?,9,10)', (50+shift, tid>>24))
        elif damage == 'drain_scope_missing':
            db.execute('DELETE FROM CUPTI_ACTIVITY_KIND_SYNCHRONIZATION WHERE correlationId=101')
        elif damage == 'drain_wrong_context':
            db.execute('UPDATE CUPTI_ACTIVITY_KIND_SYNCHRONIZATION SET contextId=99 WHERE correlationId=101')
        elif damage == 'lifetime_wrong_process':
            db.execute('UPDATE TARGET_INFO_CUDA_STREAM SET processId=99')
        elif damage == 'drain_wrong_process':
            db.execute('UPDATE CUPTI_ACTIVITY_KIND_SYNCHRONIZATION SET globalPid=99 WHERE correlationId=101')
        elif damage == 'lifecycle_change':
            db.execute("INSERT INTO StringIds VALUES (22,'cudaStreamDestroy'),(23,'cudaStreamCreate')")
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?,?,0,?,200,22,0,NULL)',(310+shift,315+shift,tid))
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?,?,0,?,201,23,0,NULL)',(320+shift,325+shift,tid))
        elif damage == 'default_stream':
            db.execute('UPDATE TARGET_INFO_CUDA_CONTEXT_INFO SET nullStreamId=2')
        elif damage == 'same_request_completed':
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?,?,0,?,210,20,0,NULL)',(405+shift,410+shift,tid))
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL SELECT ?,?,deviceId,contextId,greenContextId,streamId,210,globalPid,demangledName,shortName,graphNodeId,graphId FROM CUPTI_ACTIVITY_KIND_KERNEL WHERE correlationId=6',(415+shift,425+shift))
        elif damage == 'drain_unknown_version':
            rowid,label=db.execute("SELECT rowid,text FROM NVTX_EVENTS WHERE text LIKE 'EXPOSEDPATH_DRAIN_V1:%' LIMIT 1").fetchone()
            payload=json.loads(label.split(':',1)[1]); payload['schema_version']='future'
            db.execute('UPDATE NVTX_EVENTS SET text=? WHERE rowid=?',('EXPOSEDPATH_DRAIN_V1:'+json.dumps(payload),rowid))
            drain_records[0]['schema_version']='future'
    host_records=json.loads(host.read_text())
    ordinals={r['identity']['request_id']:i for i,r in enumerate(ledger['requests'])}
    for record in host_records:
        offset=ordinals[record['payload']['identity']['request_id']]*1000000
        for field in ('host_observed_ns','host_before_marker_ns','host_after_marker_ns'):
            record[field]+=offset
    write_json(host,host_records)
    canonical, scope = project(tmp_path, inputs, host)
    from exposedpath_v141.sync_semantics import load_canonical_bundle
    bundle = load_canonical_bundle(canonical)
    life = next(r for r in bundle['records']['nvtx'] if r['text'].startswith('EXPOSEDPATH_STREAM_LIFETIME_V1:'))
    activity = bundle['records']['device_activity'][0]
    if damage == 'wrong_pass':
        drain_records[1]['identity']['pass_id']='pass0'
    elif damage == 'host_reversal':
        drain_records[1]['host_end_ns']=0
    elif damage == 'duplicate_drain':
        drain_records.append(deepcopy(drain_records[-1]))
    elif damage == 'host_clock_unknown':
        drain_records[1]['host_clock_id']='UNKNOWN_OTHER_CLOCK'
    elif damage == 'host_drain_after_request':
        drain_records[1].update(host_start_ns=10**12,host_end_ns=10**12+10)
    drain = write_json(tmp_path/'drain.json', dict(schema_version=DRAIN_VERSION, drains=drain_records))
    evidence = dict(schema_version='exposedpath-closed-prior-evidence/0.1.0',
        canonical_manifest_sha256=sha(canonical), scope_sha256=sha(scope),
        drain_ledger={'filename':drain.name,'sha256':sha(drain)},
        lifetimes=[{'marker_record_id':life['record_id'],'binding_activity_id':activity['record_id']}])
    if damage == 'lifetime_missing':
        evidence['lifetimes'] = []
    if damage == 'hash':
        evidence['drain_ledger']['sha256'] = '0'*64
    if damage == 'unknown_version':
        evidence['schema_version'] = 'unknown'
    if return_inputs:
        return inputs, host, drain, evidence['lifetimes']
    return canonical, scope, write_json(tmp_path/'closed.json', evidence)


def calculate(paths, closed=True):
    from exposedpath_v141.gate8_scope import build_projected_ab_inputs
    from exposedpath_v141.time_representation import time_representation, SIGNED
    assert 'closed_prior_manifest' in inspect.signature(build_projected_ab_inputs).parameters
    with time_representation(SIGNED):
        result = build_projected_ab_inputs(paths[0],paths[1],closed_prior_manifest=paths[2] if closed else None)
        from exposedpath_v141.a_accounting import calculate_a_windows
        from exposedpath_v141.b_provenance import calculate_b_syncs
        return result, calculate_a_windows(result), calculate_b_syncs(result)


@pytest.mark.parametrize('requests,hidden', [(2,40),(3,70)])
@pytest.mark.parametrize('shift', [0,-160])
def test_complete_physical_prefix_and_current_window_accounting(monkeypatch,tmp_path,requests,hidden,shift):
    paths = closed_sources(tmp_path,monkeypatch,requests,shift)
    before = [sha(p) for p in paths]
    _, a, b = calculate(paths)
    target = next(r for r in b if r['request_id']==f'request-{requests-1}')
    assert target['validity'] == 'B_VALID'
    assert len(target['wait_set_activity_ids']) == requests
    assert target['wait_set_hidden_union_ns'] == hidden
    assert target['wait_set_exposed_union_ns'] == 20
    assert target['sync_return_tail_ns'] == 10
    assert target['cross_request_dependency'] is True
    assert target['cross_phase_dependency'] is False
    assert len(target['activity_provenance']) == requests
    assert {r['origin_identity']['request_id'] for r in target['activity_provenance']} == {f'request-{i}' for i in range(requests)}
    full = next(r for r in a if r['request_id']==f'request-{requests-1}' and r['phase']=='full_request')
    assert [full[k] for k in ('A_host_path_ns','A_cuda_api_ns','A_device_wait_ns','A_sync_residual_ns','A_unattributed_ns')] == [165,5,20,10,0]
    _, _, old = calculate(paths, closed=False)
    assert next(r for r in old if r['request_id']==f'request-{requests-1}')['primary_reason']=='INVOCATION_BLEED'
    assert [sha(p) for p in paths] == before


@pytest.mark.parametrize('damage', ['missing_api','failed_api','unowned','lifetime_missing','hash','unknown_version','event',
                                  'default_stream','wrong_pass','host_reversal','duplicate_drain'])
def test_evidence_gap_never_grants_closed_prior(monkeypatch,tmp_path,damage):
    with pytest.raises(ValueError):
        paths = closed_sources(tmp_path,monkeypatch,damage=damage)
        calculate(paths)


@pytest.mark.parametrize('damage', ['drain_scope_missing','drain_wrong_context',
                                  'lifetime_wrong_process','drain_wrong_process'])
def test_drain_api_name_and_marker_do_not_prove_scope(monkeypatch,tmp_path,damage):
    with pytest.raises(ValueError,match='CLOSED_PRIOR_|DEVICE_MAPPING_UNPROVEN'):
        paths = closed_sources(tmp_path,monkeypatch,damage=damage)
        calculate(paths)


def test_lifecycle_counterevidence_overrides_continuous_marker(monkeypatch,tmp_path):
    paths=closed_sources(tmp_path,monkeypatch,damage='lifecycle_change')
    with pytest.raises(ValueError,match='LIFETIME'):
        calculate(paths)


@pytest.mark.parametrize('damage',['host_clock_unknown','host_drain_after_request'])
def test_drain_host_diagnostics_are_consistent_with_request_anchor(monkeypatch,tmp_path,damage):
    paths=closed_sources(tmp_path,monkeypatch,damage=damage)
    with pytest.raises(ValueError,match='DRAIN_HOST'):
        calculate(paths)


def test_prior_decode_is_not_current_request_cross_phase(monkeypatch,tmp_path):
    _, _, b = calculate(closed_sources(tmp_path,monkeypatch,damage='old_decode'))
    row = next(r for r in b if r['request_id']=='request-1')
    assert row['activity_origin_phases']==['decode','prefill']
    assert row['cross_request_dependency'] is True
    assert row['cross_phase_dependency'] is False
    assert row['terminal_origin_phase']=='prefill'


def test_same_request_completed_prefix_not_removed_by_closed_prior(monkeypatch,tmp_path):
    _,a,b=calculate(closed_sources(tmp_path,monkeypatch,damage='same_request_completed'))
    row=next(r for r in b if r['request_id']=='request-1')
    # Old request 30 + completed same-request 10 + current pre-sync 10.
    assert row['wait_set_hidden_union_ns']==50
    assert row['wait_set_exposed_union_ns']==20 and row['sync_return_tail_ns']==10
    assert len(row['wait_set_activity_ids'])==3
    assert [p['relation_to_sync'] for p in row['activity_provenance']].count('same_request')==2
    full=next(r for r in a if r['request_id']=='request-1' and r['phase']=='full_request')
    assert [full[k] for k in ('A_host_path_ns','A_cuda_api_ns','A_device_wait_ns','A_sync_residual_ns','A_unattributed_ns')]==[160,10,20,10,0]


@pytest.mark.parametrize('shift',[0,-160])
def test_versioned_files_roundtrip_and_derived_remains_blocked(monkeypatch,tmp_path,shift):
    from exposedpath_v141.s_bundle import analyze_canonical_to_s
    from exposedpath_v141.ab_bundle import analyze_ab, load_ab_bundle
    from exposedpath_v141.derived import derive_exposure
    assert 'closed_prior_manifest' in inspect.signature(analyze_canonical_to_s).parameters
    canonical, scope, proof = closed_sources(tmp_path,monkeypatch,shift=shift)
    s = analyze_canonical_to_s(canonical,tmp_path/'s',scope_manifest=scope,closed_prior_manifest=proof)
    ab = analyze_ab(canonical,s,tmp_path/'ab',scope_manifest=scope,closed_prior_manifest=proof)
    result = load_ab_bundle(ab,canonical_manifest=canonical,s_manifest=s)
    assert result['manifest']['schema_version']=='exposedpath-ab/0.4.0'
    assert result['manifest']['s_schema_version']=='exposedpath-s-layer/0.3.0'
    assert result['manifest']['source']['closed_prior_manifest_sha256']==sha(proof).upper()
    assert next(r for r in result['b_sync_records'] if r['request_id']=='request-1')['wait_set_hidden_union_ns']==40
    with pytest.raises(ValueError):
        derive_exposure(ab,tmp_path/'derived')
    assert not (tmp_path/'derived/derived_manifest.json').exists()
    with pytest.raises(ValueError):
        analyze_ab(canonical,s,tmp_path/'mix',scope_manifest=scope)
    with pytest.raises(FileExistsError):
        analyze_canonical_to_s(canonical,tmp_path/'s',scope_manifest=scope,closed_prior_manifest=proof)


def test_drain_marker_version_is_not_inferred_from_matching_payload(monkeypatch,tmp_path):
    paths=closed_sources(tmp_path,monkeypatch,damage='drain_unknown_version')
    with pytest.raises(ValueError,match='DRAIN_'):
        calculate(paths)


def test_closed_schema_preserves_exact_integer_limits():
    from pathlib import Path
    from jsonschema import Draft202012Validator
    schema=json.loads(Path('docs/v1_4_1/contracts/ab_schema_v0_4.json').read_text())
    fields=schema['$defs']['a_window_record']['properties']
    time=Draft202012Validator(fields['window_start_ns'])
    duration=Draft202012Validator(fields['T_window_ns'])
    assert time.is_valid(-(2**63)) and time.is_valid(2**63-1)
    assert not time.is_valid(-(2**63)-1) and not time.is_valid(2**63)
    assert duration.is_valid(2**64-1) and not duration.is_valid(2**64)


def test_full_receipt_chain_persists_drains_and_blocks_unknown(monkeypatch,tmp_path):
    from test_gate8_file_chain import input_files
    from exposedpath_v141.gate8_files import write_input_receipt, process_gate8_receipt, load_chain_result
    assert 'closed_prior_bindings_path' in inspect.signature(process_gate8_receipt).parameters
    inputs, host, drain, lifetimes = closed_sources(tmp_path,monkeypatch,return_inputs=True)
    files = input_files(tmp_path,monkeypatch,source_factory=lambda *a,**k:(inputs,host))
    producer = json.loads(files['producer_receipt'].read_text())
    producer['schema_version']='exposedpath-gate8-producer-receipt/0.2.0'
    producer['files']['drain_ledger.json']={'filename':drain.name,'sha256':sha(drain),'size_bytes':drain.stat().st_size}
    write_json(files['producer_receipt'],producer)
    files['drain_ledger']=drain
    # The base fixture seals fresh source/WMPC hashes after producing Raw. Bind
    # this synthetic lifecycle witness to that source, never modify real Raw.
    ledger=json.loads(files['pass_identity'].read_text())
    with sqlite3.connect(files['sqlite']) as db:
        rowid, label=db.execute("SELECT rowid,text FROM NVTX_EVENTS WHERE text LIKE 'EXPOSEDPATH_STREAM_LIFETIME_V1:%'").fetchone()
        payload=json.loads(label.split(':',1)[1]); payload['producer_source_sha256']=ledger['runner_source_sha256']
        db.execute('UPDATE NVTX_EVENTS SET text=? WHERE rowid=?',('EXPOSEDPATH_STREAM_LIFETIME_V1:'+json.dumps(payload),rowid))
    export=json.loads(files['export_report'].read_text()); export['canonical_sqlite_sha256']=sha(files['sqlite'])
    export['attempts'][0].update(sqlite_sha256=sha(files['sqlite']),sqlite_size=files['sqlite'].stat().st_size)
    write_json(files['export_report'],export)
    receipt=write_input_receipt(tmp_path/'input.json',artifacts=files,collector_version='2026.1.1.204',capture_session_id='synthetic')
    bindings=write_json(tmp_path/'bindings.json',dict(schema_version='exposedpath-lifetime-bindings/0.1.0',
                        source_sqlite_sha256=sha(files['sqlite']),lifetimes=lifetimes))
    before={k:sha(p) for k,p in files.items()}
    blocked=process_gate8_receipt(receipt,tmp_path/'blocked',closed_prior_bindings_path=bindings)
    result=load_chain_result(blocked)
    assert result['status']=='BLOCKED'
    blocked_report=json.loads((blocked.parent/'analysis/gate8_local_analysis.json').read_text())
    assert 'CLOSED_PRIOR_TARGET_SOURCE_NOT_QUALIFIED' in blocked_report['reasons']
    assert (blocked.parent/'provenance/drain_ledger.json').is_file()
    assert not list(blocked.parent.rglob('ab_manifest.json'))
    counters=json.loads((blocked.parent/'analysis/integrity.json').read_text())
    for r in counters:
        r.update(status='ZERO_CONFIRMED',dropped_count=0,basis='COLLECTOR_COUNTER',finalized=True,
                 coverage_complete=True,evidence_refs=[{'sha256':'f'*64,'selector':'SYNTHETIC_COUNTER'}],reasons=[])
    synthetic=write_json(tmp_path/'synthetic.json',counters)
    path=process_gate8_receipt(receipt,tmp_path/'calculation',closed_prior_bindings_path=bindings,
                              integrity_receipts_path=synthetic,synthetic_fixture=True)
    loaded=load_chain_result(path)
    assert loaded['status']=='SYNTHETIC_CALCULATION_ONLY'
    assert not list(path.parent.rglob('derived_manifest.json'))
    from exposedpath_v141.ab_bundle import load_ab_bundle
    ab=load_ab_bundle(path.parent/'analysis/ab/ab_manifest.json')
    assert next(r for r in ab['b_sync_records'] if r['request_id']=='request-1')['wait_set_hidden_union_ns']==40
    assert {k:sha(p) for k,p in files.items()}==before
    (path.parent/'closed_prior/drain.json').write_text('{}')
    with pytest.raises(ValueError,match='HASH'):
        load_chain_result(path)
