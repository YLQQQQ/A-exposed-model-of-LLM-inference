"""Hand-authored same-capture oracle. CPU data is never GPU qualification."""
from copy import deepcopy
import importlib
import json
from pathlib import Path
import sqlite3

import pytest


def api():
    return importlib.import_module('analysis.memset_same_capture')


def fixture():
    side = dict(schema_version='memset-same-capture-side/0.1.0',
        role='ENGINEERING_MEMSET_MICRO', run_id='a'*32, pid=7, creation_filetime=12345,
        entry='cudaMemsetAsync', recorder_kind='CUDA_RUNTIME_EXPORT',
        runtime_path='C:/fixed/cudart64_12.dll', runtime_version=12040,
        attach_code=0, detach_code=0, recorder_error=0, setup_drain_return=0,
        gpu_uuid='GPU-fixed', pci_bus_id='0000:41:00.0',
        calls=[dict(call_id=i, pid=7, tid=9, count=n, value=123, stream_hex='0',
                    pointer_alias=1, return_code=0, forwards=1, completed=True,
                    push_level=0, pop_level=0) for i,n in [(1,0),(2,64)]],
        cases=[dict(call_id=i, sync_return=0, copy_return=0,
                    readback_hex=h*64) for i,h in [(1,'3c'),(2,'7b')]])
    raw=dict(schema_version='nsys-2026.2-memset-micro/0.1.0',clock_id='NSYS_TRACE_NS',
        ranges=[dict(record_id='range'+str(i),run_id='a'*32,call_id=i,pid=7,tid=9,
                    start=s,end=e,event_type=59) for i,s,e in [(1,10,20),(2,30,50)]],
        apis=[dict(record_id='r'+str(i),name='cudaMemsetAsync_v3020',event_class=0,
                  pid=7,tid=9,start=s,end=e,correlation_id=100+i,return_code=0)
              for i,s,e in [(1,11,19),(2,31,49)]],
        effects=[dict(record_id='m1',kind='MEMSET',pid=7,correlation_id=102,
                    bytes=64,value=123,device_id=0,context_id=3,stream_id=17,start=55,end=60)],
        verification_ranges=[dict(call_id=i,pid=7,tid=9,start=s,end=e)
                             for i,s,e in [(1,21,28),(2,50,66)]],
        synchronizations=[dict(pid=7,correlation_id=c,device_id=0,context_id=3,stream_id=17,sync_type='STREAM_SYNCHRONIZE')
                          for c in (201,202)],
        sync_apis=[dict(pid=7,tid=9,start=s,end=e,correlation_id=c,
                       name='cudaStreamSynchronize_v3020',return_code=0)
                   for s,e,c in [(22,27,201),(51,65,202)]], diagnostics=[])
    expected=dict(run_id='a'*32,runtime_path='C:/fixed/cudart64_12.dll',
                  gpu_uuid='GPU-fixed',pci_bus_id='0000:41:00.0')
    return side,raw,expected


def test_literal_zero_and_64_pairing_does_not_grant_coe():
    s,r,e=fixture();v=api().review(s,r,e)
    assert v['status']=='MICRO_EVIDENCE_COMPLETE_PENDING_REVIEW'
    assert [c['state'] for c in v['calls']]==['ZERO_LENGTH_ARGUMENT_OBSERVED','NONZERO_DEVICE_EFFECT_MAPPED']
    assert v['calls'][1]['effect_ids']==['m1']
    assert v['coe_admission']=='NOT_ASSESSED' and v['dropped_records_status']=='UNKNOWN'


@pytest.mark.parametrize('change,reason',[
    ('run','IDENTITY'),('pid','IDENTITY'),('creation','IDENTITY'),('entry','ENTRY'),('drain','DRAIN'),
    ('private','ENTRY'),('runtime','RUNTIME'),('return','CALL_RETURN'),
    ('count_float','COUNT'),('count_overflow','COUNT'),('forward','FORWARDING'),
    ('missing_range','RANGE_PAIR'),('duplicate_range','RANGE_PAIR'),('bad_range','RANGE_PAIR'),
    ('missing_runtime','RUNTIME_PAIR'),('duplicate_runtime','RUNTIME_PAIR'),
    ('reentry','RECORDER'),('unrecorded','RUNTIME_COVERAGE'),('wrong_thread','RUNTIME_PAIR'),
    ('wrong_stream','STREAM_SCOPE'),('effect_missing','NONZERO_EFFECT_MISSING'),
    ('effect_duplicate','EFFECT_CONFLICT'),('bytes','EFFECT_CONFLICT'),
    ('zero_positive','ZERO_EFFECT_CONFLICT'),('readback','FUNCTIONAL_ORACLE'),
    ('diagnostic','DIAGNOSTIC'),('missing_sync','STREAM_SCOPE'),('wrong_sync_type','STREAM_SCOPE')])
def test_precise_refusals_not_hidden_by_earlier_gates(change,reason):
    s,r,e=fixture()
    if change=='run':s['run_id']='b'*32
    elif change=='pid':s['calls'][0]['pid']=8
    elif change=='creation':s['creation_filetime']=None
    elif change=='entry':s['entry']='cudaMemsetAsync_ptsz'
    elif change=='drain':s['setup_drain_return']=1
    elif change=='private':s['recorder_kind']='STATIC_PRIVATE'
    elif change=='runtime':s['runtime_path']='C:/other/cudart64_12.dll'
    elif change=='return':s['calls'][1]['return_code']=1
    elif change=='count_float':s['calls'][1]['count']=64.0
    elif change=='count_overflow':s['calls'][1]['count']=2**64
    elif change=='forward':s['calls'][1]['forwards']=2
    elif change=='missing_range':r['ranges'].pop()
    elif change=='duplicate_range':r['ranges'].append(deepcopy(r['ranges'][0]))
    elif change=='bad_range':r['ranges'][1]['end']=None
    elif change=='missing_runtime':r['apis'].pop()
    elif change=='duplicate_runtime':r['apis'].append(dict(r['apis'][1],record_id='duplicate'))
    elif change=='reentry':s['recorder_error']=3
    elif change=='unrecorded':r['apis'].append(dict(r['apis'][1],record_id='uncovered',start=70,end=80,correlation_id=999))
    elif change=='wrong_thread':r['apis'][1]['tid']=11
    elif change=='wrong_stream':r['effects'][0]['stream_id']=18
    elif change=='effect_missing':r['effects']=[]
    elif change=='effect_duplicate':r['effects']*=2
    elif change=='bytes':r['effects'][0]['bytes']=63
    elif change=='zero_positive':r['effects'].append(dict(r['effects'][0],record_id='bad-zero',correlation_id=101))
    elif change=='readback':s['cases'][0]['readback_hex']='00'*64
    elif change=='diagnostic':r['diagnostics']=[dict(severity=2,message='new unknown failure')]
    elif change=='missing_sync':r['synchronizations']=[]
    elif change=='wrong_sync_type':r['synchronizations'][1]['sync_type']='EVENT_SYNCHRONIZE'
    with pytest.raises(ValueError,match='MEMSET_MICRO_'+reason):api().review(s,r,e)


def test_effect_finishing_after_runtime_return_is_legal_not_time_matched():
    s,r,e=fixture();r['effects'][0].update(start=52,end=61)
    assert api().review(s,r,e)['calls'][1]['effect_ids']==['m1']


def test_unrelated_overlap_does_not_supply_missing_effect():
    s,r,e=fixture();r['effects'][0].update(correlation_id=777,start=31,end=40)
    with pytest.raises(ValueError,match='NONZERO_EFFECT_MISSING'):api().review(s,r,e)


def test_pci_hex_case_is_not_a_different_device_and_raw_fact_survives():
    s,r,e=fixture();s['pci_bus_id']='0000:4A:00.0';e['pci_bus_id']='0000:4a:00.0'
    assert api().review(s,r,e)['status']=='MICRO_EVIDENCE_COMPLETE_PENDING_REVIEW'
    assert s['pci_bus_id']=='0000:4A:00.0'


def test_file_consumer_binds_exact_side_and_sqlite_bytes(tmp_path):
    # This is an independently authored miniature of the actual exported schema.
    s,r,e=fixture();p=tmp_path/'capture.sqlite'
    with sqlite3.connect(p) as c:
        c.executescript('CREATE TABLE StringIds(id INTEGER,value TEXT);'
            'CREATE TABLE NVTX_EVENTS(start INTEGER,end INTEGER,eventType INTEGER,globalTid INTEGER,endGlobalTid INTEGER,text TEXT,textId INTEGER);'
            'CREATE TABLE CUPTI_ACTIVITY_KIND_RUNTIME(start INTEGER,end INTEGER,eventClass INTEGER,globalTid INTEGER,correlationId INTEGER,nameId INTEGER,returnValue INTEGER);'
            'CREATE TABLE CUPTI_ACTIVITY_KIND_MEMSET(start INTEGER,end INTEGER,globalPid INTEGER,correlationId INTEGER,deviceId INTEGER,contextId INTEGER,streamId INTEGER,bytes INTEGER,value INTEGER);'
            'CREATE TABLE CUPTI_ACTIVITY_KIND_SYNCHRONIZATION(globalPid INTEGER,correlationId INTEGER,deviceId INTEGER,contextId INTEGER,streamId INTEGER,syncType INTEGER);'
            'CREATE TABLE ENUM_CUPTI_SYNC_TYPE(id INTEGER,name TEXT);'
            'CREATE TABLE DIAGNOSTIC_EVENT(source INTEGER,severity INTEGER,text TEXT,globalPid INTEGER,timestampType INTEGER);')
        c.execute('INSERT INTO ENUM_CUPTI_SYNC_TYPE VALUES (3,"STREAM_SYNCHRONIZE")')
        c.executemany('INSERT INTO StringIds VALUES (?,?)',[(1,'cudaMemsetAsync_v3020'),(2,'cudaStreamSynchronize_v3020')])
        c.execute('INSERT INTO NVTX_EVENTS VALUES (9,70,59,?,?,?,NULL)',((7<<24)|9,(7<<24)|9,'EP_MICRO:'+'a'*32))
        for i,start,end in [(1,10,20),(2,30,50)]:
            c.execute('INSERT INTO NVTX_EVENTS VALUES (?,?,59,?,?,?,NULL)',(start,end,(7<<24)|9,(7<<24)|9,'EP_MEMSET:'+'a'*32+':'+str(i)))
            c.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?,?,0,?,?,1,0)',(start+1,end-1,(7<<24)|9,100+i))
        for i,start,end in [(1,21,28),(2,50,66)]:
            c.execute('INSERT INTO NVTX_EVENTS VALUES (?,?,59,?,?,?,NULL)',(start,end,(7<<24)|9,(7<<24)|9,'EP_VERIFY:'+'a'*32+':'+str(i)))
        c.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (22,27,0,?,201,2,0)',((7<<24)|9,))
        c.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (51,65,0,?,202,2,0)',((7<<24)|9,))
        c.execute('INSERT INTO CUPTI_ACTIVITY_KIND_MEMSET VALUES (55,60,?,102,0,3,17,64,123)',(7<<24,))
        c.execute('INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION VALUES (?,202,0,3,17,3)',(7<<24,))
        c.execute('INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION VALUES (?,201,0,3,17,3)',(7<<24,))
    side=tmp_path/'side.json';side.write_text(json.dumps(s),encoding='utf8')
    out=tmp_path/'derived';v=api().review_files(p,side,e,out)
    assert v['status']=='MICRO_EVIDENCE_COMPLETE_PENDING_REVIEW'
    assert (out/'review.json').is_file() and (out/'source_hashes.json').is_file()
    with pytest.raises(FileExistsError):api().review_files(p,side,e,out)


def test_missing_diagnostic_table_is_not_an_empty_diagnostic_set(tmp_path):
    test_file_consumer_binds_exact_side_and_sqlite_bytes(tmp_path)
    with sqlite3.connect(tmp_path/'capture.sqlite') as c:c.execute('DROP TABLE DIAGNOSTIC_EVENT')
    _,_,e=fixture()
    with pytest.raises(ValueError,match='SQLITE_SCHEMA'):
        api().review_files(tmp_path/'capture.sqlite',tmp_path/'side.json',e,tmp_path/'missing_diag')


def test_a_kernel_effect_for_zero_call_cannot_be_silently_filtered(tmp_path):
    test_file_consumer_binds_exact_side_and_sqlite_bytes(tmp_path)
    with sqlite3.connect(tmp_path/'capture.sqlite') as c:
        c.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_KERNEL(start INTEGER,end INTEGER,globalPid INTEGER,correlationId INTEGER,deviceId INTEGER,contextId INTEGER,streamId INTEGER)')
        c.execute('INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES (12,18,?,101,0,3,17)',(7<<24,))
    _,_,e=fixture()
    with pytest.raises(ValueError,match='ZERO_EFFECT_CONFLICT'):
        api().review_files(tmp_path/'capture.sqlite',tmp_path/'side.json',e,tmp_path/'kernel_zero')

