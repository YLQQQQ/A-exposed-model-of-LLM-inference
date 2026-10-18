"""CPU-only callsite evidence; never an oracle for missing device effects."""
import importlib.util
import json
from pathlib import Path
import sqlite3

import pytest


def api():
    assert importlib.util.find_spec('analysis.memset_callsite'), 'missing callsite reader'
    from analysis import memset_callsite
    return memset_callsite


def fixture_db(tmp_path):
    path=tmp_path/'raw.sqlite'
    caller=tmp_path/'CPU_caller.dll';caller.write_bytes(b'CPU file identity, not a loaded DLL')
    with sqlite3.connect(path) as db:
        db.executescript('''
        CREATE TABLE StringIds(id INTEGER PRIMARY KEY,value TEXT);
        CREATE TABLE CUPTI_ACTIVITY_KIND_RUNTIME(start INTEGER,end INTEGER,globalTid INTEGER,
          nameId INTEGER,returnValue INTEGER,correlationId INTEGER,callchainId INTEGER,eventClass INTEGER);
        CREATE TABLE CUDA_CALLCHAINS(id INTEGER,stackDepth INTEGER,module INTEGER,symbol INTEGER,
          unresolved INTEGER,originalIP INTEGER);
        CREATE TABLE CUPTI_ACTIVITY_KIND_MEMSET(start INTEGER,end INTEGER,globalPid INTEGER,
          correlationId INTEGER,bytes INTEGER,deviceId INTEGER,contextId INTEGER,streamId INTEGER);
        ''')
        db.executemany('INSERT INTO StringIds VALUES (?,?)',[(1,'cudaMemsetAsync_v3020'),
            (2,str(caller)),(3,'CPU_symbol'),(4,'cudart64_12.dll'),(5,'unknown')])
        db.executemany('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?,?,?,?,?,?,?,?)',[
            (100,110,(12<<24)|7,1,0,51,9,0),
            (100,110,(12<<24)|7,1,0,52,10,0), # Same time, different stack.
            (120,130,(12<<24)|7,1,0,53,9,0), # Legal deduplicated stack reuse.
            (120,130,(13<<24)|7,1,0,51,10,0)])
        db.executemany('INSERT INTO CUDA_CALLCHAINS VALUES (?,?,?,?,?,?)',[
            (9,0,4,3,0,4096),(9,1,2,3,0,8192),(10,0,2,5,1,12288)])
        db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_MEMSET VALUES (?,?,?,?,?,?,?,?)',
            (101,105,12<<24,51,64,0,1,7))
    return path,dict(start=90,end=200,pid=12,tid=7,global_tid=(12<<24)|7),caller


def test_real_sqlite_id_join_and_legal_shared_stack(tmp_path):
    path,scope,caller=fixture_db(tmp_path)
    before=path.read_bytes();r=api().read_sources(path,scope)
    assert path.read_bytes()==before
    assert r['status']=='CALLSITE_LOCATED' and r['target_count']==3
    assert (r['mapped_count'],r['missing_effect_count'])==(1,2)
    assert [a['callchain_id'] for a in r['calls']]==[9,10,9]
    assert r['calls'][0]['frames'][1]['original_ip']==8192
    assert r['calls'][1]['frames'][0]['original_ip']==12288
    assert r['calls'][1]['frames'][0]['symbol_unresolved'] is True
    assert r['calls'][1]['effect_ids']==[]
    assert all(a['count'] is None for a in r['calls'])
    assert r['parameter_evidence'] is False and r['coe_admission']=='NOT_ASSESSED'
    assert r['module_files'][str(caller)]['sha256']


@pytest.mark.parametrize('damage',['null','dangling','duplicate_depth','missing_module','tools_only','python_only','missing_ip'])
def test_no_invented_stack_or_location(tmp_path,damage):
    path,scope,_=fixture_db(tmp_path)
    with sqlite3.connect(path) as db:
        if damage=='null':db.execute('UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET callchainId=NULL WHERE correlationId=52')
        if damage=='dangling':db.execute('UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET callchainId=99 WHERE correlationId=52')
        if damage=='duplicate_depth':db.execute('INSERT INTO CUDA_CALLCHAINS VALUES (10,0,2,3,0,12345)')
        if damage=='missing_module':db.execute('UPDATE CUDA_CALLCHAINS SET module=99 WHERE id=10')
        if damage=='tools_only':db.execute('UPDATE CUDA_CALLCHAINS SET module=4 WHERE id=10')
        if damage=='python_only':
            generic=tmp_path/'python311.dll';generic.write_bytes(b'CPU generic interpreter frame')
            db.execute('INSERT INTO StringIds VALUES (?,?)',(6,str(generic)))
            db.execute('UPDATE CUDA_CALLCHAINS SET module=6 WHERE id=10')
        if damage=='missing_ip':db.execute('UPDATE CUDA_CALLCHAINS SET originalIP=NULL WHERE id=10')
    r=api().read_sources(path,scope)
    assert r['status']=='INCONCLUSIVE' and r['issues']
    assert r['missing_effect_count']==2 and r['parameter_evidence'] is False


def test_absent_callchain_table_preserves_targets(tmp_path):
    path,scope,_=fixture_db(tmp_path)
    with sqlite3.connect(path) as db:db.execute('DROP TABLE CUDA_CALLCHAINS')
    r=api().read_sources(path,scope)
    assert r['status']=='INCONCLUSIVE' and r['target_count']==3
    assert all(not a['frames'] for a in r['calls'])


def test_no_missing_effect_is_not_a_repair_of_old_instance(tmp_path):
    path,scope,_=fixture_db(tmp_path)
    with sqlite3.connect(path) as db:
        for corr in (52,53):db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_MEMSET VALUES (101,105,?,?,?,?,?,?)',
            (12<<24,corr,64,0,1,7))
    r=api().read_sources(path,scope)
    assert r['status']=='NOT_DISCRIMINATING_FOR_MISSING_EFFECT_ORIGIN'
    assert r['old_attempt_repaired'] is False


def test_crossing_prefill_and_foreign_thread_are_not_silently_skipped(tmp_path):
    path,scope,_=fixture_db(tmp_path)
    with sqlite3.connect(path) as db:
        db.execute('UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET start=89 WHERE correlationId=52')
        db.execute('UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET globalTid=? WHERE correlationId=53',((12<<24)|8,))
    r=api().read_sources(path,scope)
    assert r['status']=='INCONCLUSIVE' and r['target_count']==3
    assert any('BOUNDARY' in i for i in r['issues']) and any('THREAD' in i for i in r['issues'])


def test_explicit_engineering_binding_reuses_p_but_cannot_be_pilot():
    assert importlib.util.find_spec('exposedpath.memset_callsite'), 'missing diagnostic contract'
    from exposedpath import memset_callsite as c,observation_preparation as p,batch_load
    b=c.binding('cpu-callsite','a'*40)
    m={**p.minimal_fields(b), 'runner_git_commit':'a'*40,'runner_git_dirty':False}
    assert p.active(b) and batch_load.active(b) and p.validate(m)==b
    assert m['run_role']=='ENGINEERING' and m['data_role']=='Engineering'
    assert m['fixed_input_tokens']==1024 and b['variant']=='P'
    assert 'pilot' not in m and m['engineering_scope']['profile']==c.PROFILE
    m['run_role']='PILOT'
    with pytest.raises(ValueError):p.validate(m)


def test_only_diagnostic_binding_allows_1024_preparation_input():
    from exposedpath import memset_callsite as c,observation_preparation as p
    prompt=dict(fixed_input_tokens=1024,samples=[dict(sample_index=0,input_ids=list(range(100,132))*32,attention_mask=[1]*1024)])
    config=dict(model_type='qwen2',vocab_size=1000,max_position_embeddings=32768)
    p.validate_input(prompt,config,1024,binding=c.binding('cpu','a'*40))
    with pytest.raises(ValueError):p.validate_input(prompt,config,1024)
    prompt['samples'][0]['attention_mask'][0]=0
    with pytest.raises(ValueError):p.validate_input(prompt,config,1024,binding=c.binding('cpu','a'*40))


def test_fixed_source_flags_preserve_target_completion_and_no_retry():
    from exposedpath import memset_callsite as c
    flags=c.PROFILE_FLAGS
    assert '--cudabacktrace=all:0' in flags and '--sample=process-tree' in flags
    assert '--sampling-frequency=200' in flags
    assert '--sample=none' not in flags and '--cpuctxsw=none' not in flags
    assert not any('python-backtrace' in f for f in flags)


def test_duration_leaves_time_to_finalize_before_driver_hard_timeout():
    from exposedpath import memset_callsite as c
    duration=int(next(f.split('=',1)[1] for f in c.PROFILE_FLAGS if f.startswith('--duration=')))
    assert 0<duration<300


def test_hardware_namespace_is_preserved_when_pid_is_reused(tmp_path):
    path,scope,_=fixture_db(tmp_path)
    with sqlite3.connect(path) as db:
        db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_MEMSET VALUES (101,105,?,?,?,?,?,?)',
            ((1<<48)|(12<<24),52,64,0,1,7))
        db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (100,110,?,1,0,52,9,0)',
            ((1<<48)|(12<<24)|7,))
    r=api().read_sources(path,scope)
    assert r['target_count']==3 and r['missing_effect_count']==2
    assert r['status']=='CALLSITE_LOCATED'


def test_actual_engineering_producer_and_projection_need_no_a_admission(tmp_path,monkeypatch):
    from test_n1_model_domain import source
    # Bind actual readers before the legacy fixture replaces the auxiliary
    # preflight read boundary. Those replacements are not production readers.
    from exposedpath import memset_callsite as c,observation_preparation,coe_input_pilot,coe_pilot,gate8_isolated_preflight
    from analysis.observation_preparation import process as ordinary_analysis
    real_read=gate8_isolated_preflight.read
    from exposedpath_v141.gate8_files import load_input_receipt
    receipt,execution,_=source(tmp_path,monkeypatch,batch_binding=c.binding('cpu-callsite','a'*40))
    monkeypatch.setattr(gate8_isolated_preflight,'read',real_read)
    assert coe_pilot.read is real_read
    _,paths=load_input_receipt(receipt)
    import shutil
    shutil.copyfile(paths['raw'],Path(execution).parent.parent/'capture.nsys-rep')
    # The fixture produced an actual CPU SQLite and producer ledger. No target
    # CUDA or real callsite claim: its ordinary trace has no requested backtrace.
    result=api().process(paths['sqlite'],Path(execution).parent,tmp_path/'sources')
    r=json.loads(result.read_text(encoding='utf8'))
    assert r['status']=='NO_TARGET_CALLS_NOT_DISCRIMINATING'
    assert r['binding']['version']==c.VERSION and r['token_ids']==[[17],[18]]
    assert r['coe_admission']=='NOT_ASSESSED' and r['parameter_evidence'] is False
    with pytest.raises(ValueError,match='SOURCE_ONLY'):
        ordinary_analysis(receipt,execution,tmp_path/'must_not_be_a')
