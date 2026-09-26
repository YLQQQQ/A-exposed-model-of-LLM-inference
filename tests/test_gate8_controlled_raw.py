"""Independent Raw checker uses emitted producer markers, never S as oracle."""
import importlib
import json
import os
import sqlite3

import pytest

from test_gate8_controlled_producer import Backend,fields
from test_v141_canonical_raw import _make_source_sqlite


def controlled_raw(tmp_path,pass_fields=None):
    from exposedpath_v141.gate8_controlled import run_controlled_to_files
    path=tmp_path/'raw.sqlite'; _make_source_sqlite(path)
    db=sqlite3.connect(path)
    for table in ('NVTX_EVENTS','CUPTI_ACTIVITY_KIND_RUNTIME','CUPTI_ACTIVITY_KIND_SYNCHRONIZATION',
                  'CUPTI_ACTIVITY_KIND_KERNEL','CUPTI_ACTIVITY_KIND_MEMCPY','CUPTI_ACTIVITY_KIND_MEMSET',
                  'CUPTI_ACTIVITY_KIND_CUDA_EVENT','DIAGNOSTIC_EVENT'):
        db.execute('DELETE FROM '+table)
    db.execute('CREATE TABLE ENUM_NSYS_EVENT_CLASS(id INTEGER,name TEXT,label TEXT)')
    db.executemany('INSERT INTO ENUM_NSYS_EVENT_CLASS VALUES (?,?,?)',[(0,'TRACE_PROCESS_EVENT_CUDA_RUNTIME','CUDA runtime'),(1,'TRACE_PROCESS_EVENT_CUDA_DRIVER','CUDA driver')])
    db.execute('CREATE TABLE ENUM_CUDA_MEMCPY_OPER(id INTEGER,name TEXT,label TEXT)')
    db.execute("INSERT INTO ENUM_CUDA_MEMCPY_OPER VALUES (2,'CUDA_MEMCPY_KIND_DTOH','Device-to-Host')")
    class Clock:
        value=100
        def __call__(self): self.value+=10; return self.value
    clock=Clock(); pid=os.getpid(); tid=(pid<<24)|11
    names={}
    def sid(name):
        if name not in names:
            value=100+len(names); names[name]=value
            db.execute('INSERT INTO StringIds VALUES (?,?)',(value,name))
        return names[name]
    class Captured(Backend):
        def __init__(self): super().__init__(); self.stack=[]; self.corr=100; self.stream=1
        def api(self,name):
            self.corr+=1; start,end=clock(),clock()
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?,?,0,?,?,?,0,NULL)',(start,end,tid,self.corr,sid(name)))
            return start,end,self.corr
        def mark(self,label):
            db.execute('INSERT INTO NVTX_EVENTS(start,end,eventType,text,globalTid) VALUES (?,NULL,34,?,?)',(clock(),label,tid))
        def push(self,label): self.stack.append((clock(),label))
        def pop(self):
            start,label=self.stack.pop()
            db.execute('INSERT INTO NVTX_EVENTS(start,end,eventType,text,globalTid) VALUES (?,?,59,?,?)',(start,clock(),label,tid))
        def prepare(self): self.stream+=1; self.api('cudaDeviceSynchronize_v3020')
        def submit(self,token):
            self.token=token; self.launch=self.api('cudaLaunchKernel_v7000'); self.api('cudaGetLastError_v3020')
        def copy(self): self.copy_api=self.api('cudaMemcpyAsync_v3020')
        def wait(self):
            start,end,corr=self.api('cudaStreamSynchronize_v3020')
            kernel_end=start+2; copy_end=start+4
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES (?,?,0,1,NULL,?,?, ?,?,?,NULL,NULL)',
                       (self.launch[1],kernel_end,self.stream,self.launch[2],pid<<24,sid('g8_token_kernel(int*, int)'),sid('g8_token_kernel')))
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_MEMCPY VALUES (?,?,0,1,NULL,?,?,?,4,2,2,1,NULL)',
                       (kernel_end,copy_end,self.stream,self.copy_api[2],pid<<24))
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION VALUES (?,?,0,1,NULL,?,?,?,NULL,3,4294967295,NULL)',
                       (start+1,end-1,self.stream,corr,pid<<24))
    receipt=run_controlled_to_files(tmp_path/'producer',pass_fields=pass_fields or fields(),backend=Captured(),clock_ns=clock)
    db.commit(); db.close()
    return path,receipt.parent


def test_raw_independent_controlled_match_not_zero_loss_or_qualification(tmp_path):
    path,producer=controlled_raw(tmp_path)
    mod=importlib.import_module('exposedpath_v141.gate8_controlled_raw')
    report=mod.check_controlled_raw(path,producer)
    assert report['status']=='CONTROLLED_RAW_MATCH'
    assert report['collector_integrity_status']=='UNKNOWN'
    assert report['dropped_count'] is None
    assert len(report['sync_expectations'])==4
    assert [len(s['wait_set_refs']) for s in report['sync_expectations']]==[2,4,2,4]
    assert report['gate8_verdict']=='NOT_RUN'


@pytest.mark.parametrize('damage',['missing_api','extra_driver','wrong_stream','extra_activity','boundary','wrong_token',
                                  'extra_sync','duplicate_sync','prior_memset','driver_table'])
def test_raw_checker_refuses_unexplained_target_evidence(tmp_path,damage):
    path,producer=controlled_raw(tmp_path)
    if damage=='wrong_token':
        ledger=producer/'operation_ledger.json'; value=json.loads(ledger.read_text()); value['tokens'][0]['observed_token']=99
        ledger.write_text(json.dumps(value))
    else:
        with sqlite3.connect(path) as db:
            if damage=='missing_api': db.execute('DELETE FROM CUPTI_ACTIVITY_KIND_RUNTIME WHERE rowid=(SELECT max(rowid) FROM CUPTI_ACTIVITY_KIND_RUNTIME)')
            elif damage=='extra_driver':
                db.execute("INSERT INTO StringIds VALUES (999,'cuLaunchKernel')")
                db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME SELECT start,end,1,globalTid,9999,999,0,NULL FROM CUPTI_ACTIVITY_KIND_RUNTIME ORDER BY rowid DESC LIMIT 1')
            elif damage=='wrong_stream': db.execute('UPDATE CUPTI_ACTIVITY_KIND_MEMCPY SET streamId=99')
            elif damage=='extra_activity': db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL SELECT * FROM CUPTI_ACTIVITY_KIND_KERNEL LIMIT 1')
            elif damage=='boundary': db.execute('DELETE FROM NVTX_EVENTS WHERE end IS NULL AND start=(SELECT max(start) FROM NVTX_EVENTS WHERE end IS NULL)')
            elif damage in ('extra_sync','duplicate_sync'):
                db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION SELECT * FROM CUPTI_ACTIVITY_KIND_SYNCHRONIZATION LIMIT 1')
                if damage=='extra_sync': db.execute('UPDATE CUPTI_ACTIVITY_KIND_SYNCHRONIZATION SET correlationId=5555 WHERE rowid=(SELECT max(rowid) FROM CUPTI_ACTIVITY_KIND_SYNCHRONIZATION)')
            elif damage=='prior_memset':
                db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_MEMSET SELECT 0,1,deviceId,contextId,NULL,streamId,5000,globalPid,0,4,NULL,2 FROM CUPTI_ACTIVITY_KIND_KERNEL LIMIT 1')
            else:
                db.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_DRIVER AS SELECT * FROM CUPTI_ACTIVITY_KIND_RUNTIME LIMIT 1')
    mod=importlib.import_module('exposedpath_v141.gate8_controlled_raw')
    with pytest.raises(ValueError): mod.check_controlled_raw(path,producer)
