"""Independent construction examples; synthetic Raw is NOT real qualification."""
import importlib.util
import importlib
import json
from types import SimpleNamespace
import pytest


def module():
    assert importlib.util.find_spec('exposedpath_v141.gate8_qualification'), 'qualification connector missing'
    return importlib.import_module('exposedpath_v141.gate8_qualification')


def test_controlled_declaration_is_not_a_fabricated_model():
    m=module()
    value=m.controlled_manifest_fields()
    assert value['model_workload'] is False
    assert 'attention_backend' not in value
    from exposedpath.gate8_engineering_contract import validate_declaration
    assert validate_declaration({**value,'run_role':'ENGINEERING','data_role':'Engineering'})
    with pytest.raises(ValueError):
        validate_declaration({**value,'run_role':'ENGINEERING','data_role':'Engineering','attention_backend':'sdpa'})


def test_operation_plan_fixes_internal_sync_and_readback():
    m=module()
    assert m.operations()==[
        ('submit',11),('internal_wait',None),('copy',None),('wait',None),('read',11),('boundary',0),
        ('submit',12),('copy',None),('wait',None),('read',12),('boundary',1)]
    assert m.operations(1)[0]==('submit',21) and m.operations(1)[6]==('submit',22)


def test_oracle_hand_example_and_unattributed_not_host():
    m=module()
    oracle=importlib.import_module('exposedpath_v141.gate8_qualification_oracle')
    # [0,100): API10; sync[30,60), needed work[20,45) => wait15, residual15.
    assert oracle.account_window((0,100),[(5,10),(70,75)],[(30,60)],[(20,45)],[])==[60,10,15,15,0]
    assert oracle.account_window((-20,80),[(5,10),(70,75)],[(30,60)],[(20,45)],[(-10,-5)])==[55,10,15,15,5]
    with pytest.raises(ValueError):
        oracle.account_window((0,100),[(5,10),(8,12)],[],[],[])


def test_oracle_rejects_wrong_categories_even_when_sum_closes():
    module()
    oracle=importlib.import_module('exposedpath_v141.gate8_qualification_oracle')
    with pytest.raises(ValueError):
        oracle.compare_components([60,10,15,15,0],[75,10,0,15,0])


def test_actual_controlled_file_chain_and_independent_oracle(tmp_path,monkeypatch):
    from qualification_fixture import capture
    m=module(); plan,execution,db,rep,export=capture(tmp_path,monkeypatch)
    out=m.audit(plan,execution,db,rep,export,tmp_path/'audit','2026.2.1.210')
    value=json.loads(out.read_text())
    assert value['status']=='CONTROLLED_SCOPE_MATCH'
    assert value['q0_status']==value['gate8_verdict']=='NOT_RUN'
    assert len(value['oracle']['requests'])==2
    assert all(len(r['syncs'])==3 for r in value['oracle']['requests'])
    assert value['oracle']['tokens']==[[11,12],[21,22]]
    assert value['d_score_allowed'] is False


@pytest.mark.parametrize('fault',['boundary','correlation','identity','warning'])
def test_qualification_faults_reject_without_rewriting_raw(tmp_path,monkeypatch,fault):
    from qualification_fixture import capture
    from test_gate8_identity import sha,write_json
    import sqlite3
    m=module(); plan,execution,db,rep,export=capture(tmp_path,monkeypatch)
    with sqlite3.connect(db) as c:
        if fault=='boundary': c.execute("DELETE FROM NVTX_EVENTS WHERE text LIKE 'EXPOSEDPATH_BOUNDARY%' AND rowid=(SELECT max(rowid) FROM NVTX_EVENTS WHERE text LIKE 'EXPOSEDPATH_BOUNDARY%')")
        elif fault=='correlation': c.execute('UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET correlationId=99999')
        elif fault=='identity': c.execute('UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET globalPid=globalPid+16777216')
        else: c.execute("INSERT INTO DIAGNOSTIC_EVENT VALUES (0,3,2,'Unknown scope warning',999999,2)")
    e=json.loads(export.read_text()); e['canonical_sqlite_sha256']=sha(db); e['attempts'][0].update(sqlite_sha256=sha(db),sqlite_size=db.stat().st_size); write_json(export,e)
    before=sha(db)
    with pytest.raises(ValueError): m.audit(plan,execution,db,rep,export,tmp_path/'audit','2026.2.1.210')
    assert sha(db)==before and not (tmp_path/'audit/qualification.json').exists()


def test_bounded_gap_file_chain_retains_two_ns_unknown(tmp_path,monkeypatch):
    from qualification_fixture import capture
    from test_gate8_identity import sha,write_json
    import sqlite3
    m=module(); plan,execution,db,rep,export=capture(tmp_path,monkeypatch)
    with sqlite3.connect(db) as c:
        start,tid=c.execute("SELECT start,globalTid FROM NVTX_EVENTS WHERE text LIKE 'EXPOSEDPATH_BOUNDARY%' ORDER BY start LIMIT 1").fetchone()
        c.execute("INSERT INTO StringIds VALUES (999,'cuKernelGetFunction')")
        c.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?,?,0,?,9999,999,0,NULL)',(start+1,start+3,tid))
    e=json.loads(export.read_text()); e['canonical_sqlite_sha256']=sha(db); e['attempts'][0].update(sqlite_sha256=sha(db),sqlite_size=db.stat().st_size); write_json(export,e)
    out=m.audit(plan,execution,db,rep,export,tmp_path/'audit','2026.2.1.210')
    assert json.loads(out.read_text())['oracle']['requests'][0]['windows']['full_request'][-1]==2


def test_rehashed_execution_cannot_change_predeclared_manifest(tmp_path,monkeypatch):
    from qualification_fixture import capture
    from test_gate8_identity import sha,write_json
    m=module(); plan,execution,db,rep,export=capture(tmp_path,monkeypatch)
    p=execution.parent/'manifest.json'; v=json.loads(p.read_text()); v['wmpc_id']='another'; write_json(p,v)
    # Exercise immutable plan binding directly, without depending on a later identity error.
    assert hasattr(m,'validate_execution'), 'sealed execution validator missing'
    v=json.loads(execution.read_text()); v['files']['manifest.json'].update(sha256=sha(p),size_bytes=p.stat().st_size); write_json(execution,v)
    with pytest.raises(ValueError): m.validate_execution(plan,execution)


def test_collection_timeout_stops_before_export(tmp_path,monkeypatch):
    m=module()
    assert hasattr(m,'collect'), 'bounded qualification orchestration missing'
    from qualification_fixture import capture
    plan,*_=capture(tmp_path,monkeypatch)
    import scripts.gate8_diagnostic_collect as bounded
    import scripts.gate7_nsys_postprocess as exporter
    monkeypatch.setattr(bounded,'run_once',lambda *a,**k:dict(status='BLOCKED',timed_out=True,exit_code=-1))
    def forbidden(**kwargs): raise AssertionError('export after failed collection')
    monkeypatch.setattr(exporter,'run_postprocess',forbidden)
    out=m.collect(plan,tmp_path/'collection','fake-nsys',json.loads(plan.read_text())['target_python']['requested_executable'])
    assert json.loads(out.read_text())['status']=='BLOCKED'
    assert 'COLLECTION_FAILED_NO_RETRY' in json.loads(out.read_text())['error']
    assert not (out.parent/'qualification.json').exists()


def test_plan_gpu_conflict_stops_before_native_load(tmp_path,monkeypatch):
    from qualification_fixture import capture
    from test_gate8_identity import sha,write_json
    m=module(); plan,*_=capture(tmp_path,monkeypatch)
    manifest=plan.parent/'manifest.json'; value=json.loads(manifest.read_text())
    value['gpu_index_physical']=9; write_json(manifest,value)
    value=json.loads(plan.read_text()); value['files']['manifest.json'].update(sha256=sha(manifest),size_bytes=manifest.stat().st_size); write_json(plan,value)
    def forbidden(_): raise AssertionError('native load before identity check')
    with pytest.raises(ValueError): m.execute(plan,tmp_path/'bad',backend_factory=forbidden)


def test_unknown_nsight_build_is_not_accepted_by_prefix():
    m=module()
    assert hasattr(m,'validate_tool_version'), 'exact tool build guard missing'
    assert m.validate_tool_version('NVIDIA Nsight Systems version 2026.2.1.210-262137639646v0')
    with pytest.raises(ValueError): m.validate_tool_version('version 2026.2.1.210-unknown')


def test_oracle_does_not_call_semantics_or_accounting(tmp_path,monkeypatch):
    from qualification_fixture import capture
    from exposedpath_v141 import sync_semantics,a_accounting
    from exposedpath_v141.gate8_qualification_oracle import check_raw
    plan,execution,db,*_=capture(tmp_path,monkeypatch)
    def forbidden(*a,**kw): raise AssertionError('oracle called tested analyzer')
    monkeypatch.setattr(sync_semantics,'recover_wait_set',forbidden)
    monkeypatch.setattr(a_accounting,'calculate_a_windows',forbidden)
    assert check_raw(db,execution.parent)['tokens']==[[11,12],[21,22]]


@pytest.mark.parametrize('fault',['drain','token_identity'])
def test_independent_oracle_rejects_unproved_drain_or_token_identity(tmp_path,monkeypatch,fault):
    from qualification_fixture import capture
    from exposedpath_v141.gate8_qualification_oracle import check_raw
    import sqlite3
    _,execution,db,*_=capture(tmp_path,monkeypatch)
    if fault=='drain':
        with sqlite3.connect(db) as c:
            c.execute('DELETE FROM CUPTI_ACTIVITY_KIND_SYNCHRONIZATION WHERE syncType=2')
    else:
        value=json.loads(execution.read_text()); value['observed_tokens'][0]['identity']['request_id']='foreign'
        execution.write_text(json.dumps(value),encoding='utf-8')
    with pytest.raises(ValueError): check_raw(db,execution.parent)


def test_oracle_uses_exported_sync_enum_not_fixture_numbers(tmp_path,monkeypatch):
    from qualification_fixture import capture
    from exposedpath_v141.gate8_qualification_oracle import check_raw
    import sqlite3
    _,execution,db,*_=capture(tmp_path,monkeypatch)
    with sqlite3.connect(db) as c:
        c.execute("UPDATE ENUM_CUPTI_SYNC_TYPE SET id=4,name='CONTEXT_SYNCHRONIZE' WHERE id=2")
        c.execute('UPDATE CUPTI_ACTIVITY_KIND_SYNCHRONIZATION SET syncType=4 WHERE syncType=2')
    assert len(check_raw(db,execution.parent)['requests'])==2


def test_membership_mismatch_rejected_even_with_same_a(tmp_path,monkeypatch):
    from qualification_fixture import capture
    from exposedpath_v141 import gate8_engineering_scope as scope
    m=module(); plan,execution,db,rep,export=capture(tmp_path,monkeypatch)
    original=scope.load_engineering_scope
    def corrupted(*args):
        value=original(*args)
        value['requests'][0]['facts']['conditional_suffix_proofs'][0]['syncs'][0]['suffix_activity_ids']=[]
        return value
    monkeypatch.setattr(scope,'load_engineering_scope',corrupted)
    with pytest.raises(ValueError): m.audit(plan,execution,db,rep,export,tmp_path/'audit','2026.2.1.210')


def test_full_nsight_sync_enum_names_have_same_independent_result(tmp_path,monkeypatch):
    from qualification_fixture import capture
    from exposedpath_v141.gate8_qualification_oracle import check_raw
    import sqlite3
    _,execution,db,*_=capture(tmp_path,monkeypatch)
    before=check_raw(db,execution.parent)
    with sqlite3.connect(db) as c:
        c.execute("UPDATE ENUM_CUPTI_SYNC_TYPE SET name='CUPTI_ACTIVITY_SYNCHRONIZATION_TYPE_' || name")
    assert check_raw(db,execution.parent)['requests']==before['requests']


@pytest.mark.parametrize('name,accepted',[
    ('cudaDeviceSynchronize',True),('cudaDeviceSynchronize_v3020',True),
    ('cudaDeviceSynchronize_v',False),('cudaDeviceSynchronize_v3020_extra',False),
    ('cudaDeviceSynchronize_v3020\n',False),('cudaDeviceSynchronize_v٣',False),
    ('cuCtxSynchronize_v3020',False),('cudaStreamSynchronize_v3020',False),
    ('prefixcudaDeviceSynchronize_v3020',False),
])
def test_drain_api_name_has_only_optional_ascii_version(tmp_path,monkeypatch,name,accepted):
    from qualification_fixture import capture
    from exposedpath_v141.gate8_qualification_oracle import check_raw
    import sqlite3
    _,execution,db,*_=capture(tmp_path,monkeypatch)
    with sqlite3.connect(db) as c:
        c.execute("UPDATE StringIds SET value=? WHERE value='cudaDeviceSynchronize'",(name,))
    if accepted:
        result=check_raw(db,execution.parent)
        assert len(result['requests'])==2 and result['tokens']==[[11,12],[21,22]]
    else:
        with pytest.raises(ValueError,match='QUALIFICATION_ORACLE_DRAIN_API'):
            check_raw(db,execution.parent)


@pytest.mark.parametrize('fault,reason',[
    ('return','DRAIN_API'),('duplicate','DRAIN_API'),('thread','DRAIN_API'),
    ('correlation','DRAIN_PHYSICAL_SYNC'),('sync_kind','DRAIN_PHYSICAL_SYNC'),
    ('warning','WARNING_IMPACT_UNKNOWN'),
])
def test_versioned_drain_preserves_evidence_guards(tmp_path,monkeypatch,fault,reason):
    from qualification_fixture import capture
    from exposedpath_v141.gate8_qualification_oracle import check_raw
    import sqlite3
    _,execution,db,*_=capture(tmp_path,monkeypatch)
    with sqlite3.connect(db) as c:
        c.execute("UPDATE StringIds SET value='cudaDeviceSynchronize_v3020' WHERE value='cudaDeviceSynchronize'")
        where="nameId=(SELECT id FROM StringIds WHERE value='cudaDeviceSynchronize_v3020')"
        if fault=='return': c.execute('UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET returnValue=1 WHERE '+where)
        elif fault=='duplicate': c.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME SELECT * FROM CUPTI_ACTIVITY_KIND_RUNTIME WHERE '+where)
        elif fault=='thread': c.execute('UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET globalTid=globalTid+1 WHERE '+where)
        elif fault=='correlation': c.execute('UPDATE CUPTI_ACTIVITY_KIND_SYNCHRONIZATION SET correlationId=99999 WHERE syncType=2')
        elif fault=='sync_kind': c.execute('UPDATE CUPTI_ACTIVITY_KIND_SYNCHRONIZATION SET syncType=3 WHERE syncType=2')
        else: c.execute("INSERT INTO DIAGNOSTIC_EVENT VALUES (0,3,2,'Unknown scope',999999,2)")
    with pytest.raises(ValueError,match='QUALIFICATION_ORACLE_'+reason):
        check_raw(db,execution.parent)
