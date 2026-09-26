"""Synthetic diagnostic records; no Nsight/device execution or loss certificate."""
import os
import sqlite3
import pytest
from test_gate8_controlled_raw import controlled_raw, lazy_memset_absent
from exposedpath_v141.gate8_controlled_raw import check_controlled_raw


def diagnostic_fixture(tmp_path):
    path,producer=controlled_raw(tmp_path)
    add_diagnostics(path)
    return path,producer


def add_diagnostics(path):
    lazy_memset_absent(path)
    with sqlite3.connect(path) as db:
        db.execute('DROP TABLE DIAGNOSTIC_EVENT')
        db.execute('CREATE TABLE DIAGNOSTIC_EVENT(timestamp INTEGER,timestampType INTEGER,source INTEGER,severity INTEGER,text TEXT,globalPid INTEGER)')
        for table,values in (
            ('ENUM_DIAGNOSTIC_SEVERITY_LEVEL',[(1,'Info'),(2,'Warning')]),
            ('ENUM_DIAGNOSTIC_SOURCE_TYPE',[(1,'Injection'),(2,'Daemon'),(3,'Analysis')]),
            ('ENUM_DIAGNOSTIC_TIMESTAMP_SOURCE',[(1,'TargetTimestamp'),(2,'HostTimestamp')])):
            db.execute('CREATE TABLE '+table+'(id INTEGER,name TEXT)')
            db.executemany('INSERT INTO '+table+' VALUES (?,?)',values)
        db.executemany('INSERT INTO DIAGNOSTIC_EVENT VALUES (?,?,?,?,?,?)',[
            (0,1,3,1,'Profiling has started.',-144115188075855872),
            (10,2,3,2,'Not all NVTX events might have been collected.',(os.getpid()+1)<<24),
            (20,1,1,1,'CUDA injection initialized successfully.',os.getpid()<<24)])


def test_scoped_diagnostics_retained_not_zero_loss(tmp_path):
    path,producer=diagnostic_fixture(tmp_path)
    report=check_controlled_raw(path,producer)
    assessment=report['diagnostic_assessment']
    assert assessment['status']=='CONTROLLED_ENGINEERING_DIAGNOSTIC_ONLY'
    assert [r['disposition'] for r in assessment['records']]==[
        'COLLECTOR_STATUS_ONLY','OUTSIDE_DECLARED_DEPENDENCY_SCOPE','COLLECTOR_STATUS_ONLY']
    assert assessment['records'][1]['timestamp_domain']=='HostTimestamp'
    assert assessment['records'][1]['raw_ref']['source_rowid']==2
    assert assessment['records'][1]['raw']['text']=='Not all NVTX events might have been collected.'
    assert report['collector_integrity_status']=='UNKNOWN'
    assert report['gate8_verdict']==report['q0_status']=='NOT_RUN'


@pytest.mark.parametrize('fault',['target_warning','unknown_pid','global_warning','global_drop',
                                  'unknown_info','wrong_enum','wrong_clock','version','source_changed',
                                  'external_cuda_activity'])
def test_scoped_diagnostics_fail_closed(tmp_path,monkeypatch,fault):
    path,producer=diagnostic_fixture(tmp_path)
    with sqlite3.connect(path) as db:
        if fault=='target_warning': db.execute('UPDATE DIAGNOSTIC_EVENT SET globalPid=? WHERE rowid=2',(os.getpid()<<24,))
        elif fault=='unknown_pid': db.execute('UPDATE DIAGNOSTIC_EVENT SET globalPid=NULL WHERE rowid=2')
        elif fault=='global_warning': db.execute('UPDATE DIAGNOSTIC_EVENT SET globalPid=-144115188075855872 WHERE rowid=2')
        elif fault=='global_drop': db.execute("UPDATE DIAGNOSTIC_EVENT SET text='Session buffer overflow: records dropped' WHERE rowid=2")
        elif fault=='unknown_info': db.execute("UPDATE DIAGNOSTIC_EVENT SET text='Unrecognized information' WHERE rowid=3")
        elif fault=='wrong_enum': db.execute("UPDATE ENUM_DIAGNOSTIC_SEVERITY_LEVEL SET name='Unknown' WHERE id=1")
        elif fault=='wrong_clock': db.execute('UPDATE DIAGNOSTIC_EVENT SET timestampType=1 WHERE rowid=2')
        elif fault=='version': db.execute("UPDATE META_DATA_EXPORT SET value='future' WHERE name='EXPORT_PRODUCT_VERSION'")
        elif fault=='external_cuda_activity':
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME SELECT -2,-1,eventClass,?,9999,nameId,0,NULL FROM CUPTI_ACTIVITY_KIND_RUNTIME LIMIT 1',((os.getpid()+1)<<24,))
    if fault=='source_changed':
        from exposedpath_v141 import gate8_controlled_diagnostics as mod
        native=tmp_path/'scripts/gate8_controlled_token.cu'; native.parent.mkdir()
        native.write_bytes((mod.ROOT/'scripts/gate8_controlled_token.cu').read_bytes()+b'\n// changed IPC construction\n')
        monkeypatch.setattr(mod,'ROOT',tmp_path)
    with pytest.raises(ValueError): check_controlled_raw(path,producer)
