"""Source-bound diagnostic identity; no real collector completeness assertion."""
import importlib
import json
import sqlite3

import pytest
from test_gate8_identity import sources, sha


def api():
    assert importlib.util.find_spec('exposedpath_v141.gate8_diagnostic_scope'), (
        'New scoped gate needs original diagnostic PID/time fields, not Canonical text guesses')
    return importlib.import_module('exposedpath_v141.gate8_diagnostic_scope')


def source(tmp_path):
    db, _, _, ledger = sources(tmp_path)
    with sqlite3.connect(db) as connection:
        connection.execute('ALTER TABLE DIAGNOSTIC_EVENT ADD COLUMN globalPid INTEGER')
        connection.execute('ALTER TABLE DIAGNOSTIC_EVENT ADD COLUMN timestampType INTEGER')
        connection.execute('DELETE FROM DIAGNOSTIC_EVENT')
        target_global_pid = (1 << 56) | (2 << 48) | (3 << 24)
        for i, pid in enumerate((target_global_pid, 7 << 24, None,
                                 -144115188075855872, target_global_pid+4)):
            connection.execute('INSERT INTO DIAGNOSTIC_EVENT VALUES (?,?,?, ?,?,?)',
                               (i, 3, 2, 'Not all NVTX events might have been collected.', pid, 1))
    return db, ledger


def test_original_pid_not_warning_text_determines_process_relation(tmp_path):
    db, ledger = source(tmp_path)
    before = sha(db)
    out = tmp_path/'diagnostic_scope.json'
    result = api().write_diagnostic_scope(db, ledger, out)
    assert json.loads(out.read_text()) == result
    assert result['source_sqlite_sha256'] == before
    assert result['pass_identity_sha256'] == sha(ledger)
    assert result['target_global_pid'] == (1 << 56) | (2 << 48) | (3 << 24)
    assert result['dropped_records_status'] == 'UNKNOWN'
    assert result['scientific_outputs_allowed'] is False
    assert [r['process_relation'] for r in result['records']] == [
        'TARGET_PROCESS','OTHER_PROCESS','UNKNOWN','UNKNOWN','UNKNOWN']
    assert [r['process_id'] for r in result['records']] == [3,7,None,None,None]
    assert [r['source_rowid'] for r in result['records']] == [1,2,3,4,5]
    assert all(r['impact_status']=='UNASSESSED' for r in result['records'])
    assert sha(db) == before
    assert api().load_diagnostic_scope(out, db, ledger) == result
    with pytest.raises(FileExistsError):
        api().write_diagnostic_scope(db, ledger, out)


def test_legacy_table_without_pid_preserves_unknown_not_inferred_pid(tmp_path):
    db, _, _, ledger = sources(tmp_path)
    with sqlite3.connect(db) as connection:
        connection.execute("INSERT INTO DIAGNOSTIC_EVENT VALUES (1,3,2,'Process 3 lost events')")
    result = api().write_diagnostic_scope(db, ledger, tmp_path/'out.json')
    row = result['records'][-1]
    assert row['global_pid'] is None and row['timestamp_type'] is None
    assert row['process_relation'] == 'UNKNOWN'
    assert result['missing_optional_columns'] == ['globalPid','timestampType']


@pytest.mark.parametrize('damage', ['source','identity','record','version'])
def test_reader_rederives_all_records_and_identity(tmp_path, damage):
    db, ledger = source(tmp_path)
    out=tmp_path/'out.json'
    api().write_diagnostic_scope(db,ledger,out)
    if damage=='source':
        with sqlite3.connect(db) as connection:
            connection.execute('DELETE FROM DIAGNOSTIC_EVENT WHERE rowid=2')
    elif damage=='identity':
        value=json.loads(ledger.read_text()); value['pid']=7
        ledger.write_text(json.dumps(value))
    else:
        value=json.loads(out.read_text())
        if damage=='record': value['records'][1]['impact_status']='OUT_OF_SCOPE'
        else: value['schema_version']='future'
        out.write_text(json.dumps(value))
    with pytest.raises(ValueError):
        api().load_diagnostic_scope(out,db,ledger)


def test_missing_diagnostic_table_is_not_empty_success(tmp_path):
    db, ledger=source(tmp_path)
    with sqlite3.connect(db) as connection:
        connection.execute('DROP TABLE DIAGNOSTIC_EVENT')
    with pytest.raises(ValueError,match='DIAGNOSTIC_SCOPE_SCHEMA'):
        api().write_diagnostic_scope(db,ledger,tmp_path/'out.json')
    assert not (tmp_path/'out.json').exists()


def test_equal_pid_number_in_other_global_namespace_is_not_target(tmp_path):
    db, ledger=source(tmp_path)
    with sqlite3.connect(db) as connection:
        connection.execute('UPDATE DIAGNOSTIC_EVENT SET globalPid=? WHERE rowid=2',
                           ((1 << 48) + (3 << 24),))
    result=api().write_diagnostic_scope(db,ledger,tmp_path/'out.json')
    assert result['records'][1]['process_id']==3
    assert result['records'][1]['process_relation']=='OTHER_PROCESS'


def test_conflicting_target_nvtx_global_process_is_rejected(tmp_path):
    db, ledger=source(tmp_path)
    with sqlite3.connect(db) as connection:
        connection.execute('UPDATE NVTX_EVENTS SET globalTid=globalTid+? WHERE rowid=2',(1 << 48,))
    with pytest.raises(ValueError,match='DIAGNOSTIC_SCOPE_TARGET_PROCESS'):
        api().write_diagnostic_scope(db,ledger,tmp_path/'out.json')


def test_uncheckpointed_wal_cannot_escape_source_file_hash(tmp_path):
    db, ledger=source(tmp_path)
    connection=sqlite3.connect(db)
    try:
        connection.execute('PRAGMA journal_mode=WAL')
        connection.execute("INSERT INTO DIAGNOSTIC_EVENT VALUES (99,3,2,'unsealed warning',NULL,1)")
        connection.commit()
        with pytest.raises(ValueError,match='DIAGNOSTIC_SCOPE_UNSEALED'):
            api().write_diagnostic_scope(db,ledger,tmp_path/'out.json')
        assert not (tmp_path/'out.json').exists()
    finally:
        connection.close()


def test_unknown_timestamp_type_is_not_assigned_a_clock_or_unit(tmp_path):
    db, ledger=source(tmp_path)
    with sqlite3.connect(db) as connection:
        connection.execute('UPDATE DIAGNOSTIC_EVENT SET timestamp=-17,timestampType=999 WHERE rowid=1')
    result=api().write_diagnostic_scope(db,ledger,tmp_path/'out.json')
    row=result['records'][0]
    assert row['timestamp_raw']==-17
    assert row['timestamp_type']==999
    assert 'timestamp_ns' not in row
