"""Independent contract arithmetic through actual producer/SQLite/file entry; CPU only."""
import importlib
import json
import sqlite3

import pytest
from test_gate8_engineering_scope import files, components
from test_gate8_identity import write_json, sha

G1 = 'G1_NATURAL_PROJECTED_A/0.1.0'
N1 = 'N1_EXPLICIT_STREAM_AB/0.1.0'


def module():
    assert importlib.util.find_spec('exposedpath_v141.gate9_domain'), 'domain file admission missing'
    return importlib.import_module('exposedpath_v141.gate9_domain')


def source(tmp_path, monkeypatch, damage=None, longer=False):
    def change(db, tid):
        end = 520 if longer else 500
        times = {16:(405,410),17:(425,440),36:(445,450),37:(end-25,end)}
        for corr,(a,b) in times.items():
            db.execute('UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET start=?,end=? WHERE correlationId=?',(a,b,corr))
            if corr in (17,37):
                db.execute('UPDATE CUPTI_ACTIVITY_KIND_SYNCHRONIZATION SET start=?,end=? WHERE correlationId=?',(a+1,b-1,corr))
        db.execute('UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET start=410,end=430 WHERE correlationId=16')
        db.execute('UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET start=450,end=? WHERE correlationId=36',(end-15,))
        db.execute("INSERT INTO StringIds VALUES (25,'cudaStreamIsCapturing_v10000')")
        db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (460,465,0,?,333,25,0,NULL)',(tid,))
        for rowid,text in db.execute('SELECT rowid,text FROM NVTX_EVENTS').fetchall():
            if 'request-1' not in text: continue
            if '"boundary_id":"t1-0"' in text:
                db.execute('UPDATE NVTX_EVENTS SET start=440 WHERE rowid=?',(rowid,))
            elif '"boundary_id":"t1-1"' in text:
                db.execute('UPDATE NVTX_EVENTS SET start=? WHERE rowid=?',(end,rowid))
            elif text.startswith('EXPOSEDPATH_JSON_V1:'):
                payload=json.loads(text.split(':',1)[1])
                a,b=(425,440) if payload['token_index']==0 else (end-25,end)
                db.execute('UPDATE NVTX_EVENTS SET start=?,end=? WHERE rowid=?',(a,b,rowid))
                if damage=='n1_marker':
                    payload.update(sync_origin='n1_intervention',intervention_variant_id='Vsync',intervention_ordinal=0)
                    db.execute('UPDATE NVTX_EVENTS SET text=? WHERE rowid=?',('EXPOSEDPATH_JSON_V1:'+json.dumps(payload),rowid))
        if damage=='correlation': db.execute('UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET correlationId=999 WHERE correlationId=16')
        if damage=='drain': db.execute('UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET returnValue=1 WHERE correlationId=101')
        if damage=='worker': db.execute('UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET globalTid=globalTid+1 WHERE correlationId=16')
        if damage=='stream': db.execute('UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET streamId=99 WHERE correlationId=16')
        if damage=='warning': db.execute("INSERT INTO DIAGNOSTIC_EVENT VALUES (0,3,2,'unbounded warning',?,2)",(99<<24,))
        if damage=='boundary': db.execute("DELETE FROM NVTX_EVENTS WHERE text LIKE '%\"boundary_id\":\"t1-0\"%'")
    receipt,execution,paths=files(tmp_path,monkeypatch,change)
    manifest=json.loads(paths['wmpc_manifest'].read_text())
    manifest['domain_qualification']={'contract':'G9-DOMAIN-QUALIFICATION/0.1.0','profile':G1,
        'declaration_role':'PRE_EXECUTION'}
    if damage=='version': manifest['domain_qualification']['profile']='future'
    write_json(paths['wmpc_manifest'],manifest)
    ledger=json.loads(paths['pass_identity'].read_text()); ledger['wmpc_manifest_sha256']=sha(paths['wmpc_manifest'])
    write_json(paths['pass_identity'],ledger)
    producer=json.loads(paths['producer_receipt'].read_text())
    producer['files']['pass_identity.json']['sha256']=sha(paths['pass_identity'])
    producer['files']['pass_identity.json']['size_bytes']=paths['pass_identity'].stat().st_size
    write_json(paths['producer_receipt'],producer)
    ex=json.loads(execution.read_text()); ex.update(manifest_sha256=sha(paths['wmpc_manifest']),producer_receipt_sha256=sha(paths['producer_receipt']))
    write_json(execution,ex)
    from exposedpath_v141.gate8_files import write_input_receipt
    receipt=write_input_receipt(tmp_path/'domain-input.json',artifacts=paths,collector_version='2026.2.1.210',capture_session_id='synthetic')
    return receipt,execution,paths


@pytest.mark.parametrize('longer,expected',[(False,[45,15,15,25,0]),(True,[65,15,15,25,0])])
def test_independent_three_windows_file_chain_and_length_not_q0(tmp_path,monkeypatch,longer,expected):
    receipt,execution,paths=source(tmp_path,monkeypatch,longer=longer)
    before={k:sha(p) for k,p in paths.items()}
    out=module().process_domain(receipt,execution,tmp_path/'domain')
    result=json.loads(out.read_text())
    r=result['requests'][1]
    assert r['status']=='QUALITY_CHECK_PASSED_NOT_QUALIFICATION'
    assert {a['phase']:components(a) for a in r['a_records']}=={
        'full_request':expected,'prefill':[20,5,5,10,0],
        'decode':[45 if longer else 25,10,10,15,0]}
    assert r['qualification_action']=='REUSE_PROFILE_CHECK_EACH_REQUEST'
    proofs=r['facts']['conditional_suffix_proofs']
    for proof in proofs:
        assert [len(s['suffix_activity_ids']) for s in proof['syncs']]==[1,2]
        assert all('dependency_edges' in s for s in proof['syncs'])
    assert result['dropped_records_status']=='UNKNOWN'
    assert result['gate9_verdict']=='NOT_RUN' and not result['formal_eligible']
    assert {k:sha(p) for k,p in paths.items()}==before
    assert module().load_domain(out,receipt,execution)==result
    with pytest.raises(FileExistsError): module().process_domain(receipt,execution,out.parent)


@pytest.mark.parametrize('damage',['correlation','drain','worker','stream','warning','boundary','version','n1_marker'])
def test_missing_or_unbounded_file_evidence_never_becomes_host(tmp_path,monkeypatch,damage):
    receipt,execution,_=source(tmp_path,monkeypatch,damage)
    try: out=module().process_domain(receipt,execution,tmp_path/'domain')
    except ValueError: assert not (tmp_path/'domain/domain.json').exists()
    else:
        result=json.loads(out.read_text())
        assert result['status']=='BLOCKED'
        assert result['requests'][1]['a_records']==[]


def test_equal_accounting_cannot_hide_different_mode_members(tmp_path,monkeypatch):
    receipt,execution,_=source(tmp_path,monkeypatch)
    from exposedpath_v141 import gate8_engineering_scope as scope
    original=scope.recover_wait_set
    def corrupt(inventory,sync):
        value=original(inventory,sync)
        if inventory['execution_context']['default_stream_mode']=='PER_THREAD' and len(value['wait_set_activity_ids'])==2:
            # Earlier K1 is complete before s2; deleting it leaves A unchanged.
            removed=value['wait_set_activity_ids'].pop(0)
            value['dependency_edges']=[e for e in value['dependency_edges'] if removed not in (e['from'],e['to'])]
        return value
    monkeypatch.setattr(scope,'recover_wait_set',corrupt)
    out=module().process_domain(receipt,execution,tmp_path/'domain')
    r=json.loads(out.read_text())['requests'][1]
    assert r['status']=='REJECTED' and not r['a_records']


def test_result_tamper_cannot_pass_reader(tmp_path,monkeypatch):
    receipt,execution,_=source(tmp_path,monkeypatch)
    out=module().process_domain(receipt,execution,tmp_path/'domain')
    result=json.loads(out.read_text()); result['requests'][1]['a_records'][0]['A_host_path_ns']+=1
    write_json(out,result)
    with pytest.raises(ValueError): module().load_domain(out,receipt,execution)


def test_bounded_category_evidence_fault_preserves_literal_five_ns_gap(tmp_path,monkeypatch):
    receipt,execution,_=source(tmp_path,monkeypatch)
    from exposedpath_v141 import a_accounting
    original=a_accounting._api_category
    # Independent scope evidence still establishes the supported non-submit call.
    # Only its A subclass evidence is withheld; no unknown dependency is excused.
    def withheld(api,*args):
        return None if api['api_name']=='cudaStreamIsCapturing_v10000' else original(api,*args)
    monkeypatch.setattr(a_accounting,'_api_category',withheld)
    out=module().process_domain(receipt,execution,tmp_path/'domain')
    r=json.loads(out.read_text())['requests'][1]
    assert {a['phase']:components(a) for a in r['a_records']}=={
        'full_request':[45,10,15,25,5],'prefill':[20,5,5,10,0],'decode':[25,5,10,15,5]}
    assert r['explanation_status']=='LOCALLY_INCOMPLETE'
