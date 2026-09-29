"""CPU recorder double; writes synthetic trace from actual producer operations."""
import json
import os
import sqlite3
import threading
import sys
import sysconfig
from pathlib import Path
from types import SimpleNamespace
from test_v141_canonical_raw import _make_source_sqlite
from test_gate8_identity import UUID,write_json,sha


def capture(tmp_path,monkeypatch,executor=None):
    from exposedpath_v141 import gate8_qualification as m
    assert hasattr(m,'prepare') and hasattr(m,'execute'), 'real qualification producer missing'
    monkeypatch.setattr(m,'check_git',lambda _:None)
    monkeypatch.setenv('CUDA_DEVICE_ORDER','PCI_BUS_ID'); monkeypatch.setenv('CUDA_VISIBLE_DEVICES','3')
    lib=tmp_path/'synthetic.dll'; lib.write_bytes(b'CPU DOUBLE, NOT NATIVE BINARY')
    pre=write_json(tmp_path/'pre.json',dict(gpu_index_physical=3,gpu_uuid=UUID,pci_bus_id='0000:E1:00.0',
        cuda_device_order='PCI_BUS_ID',cuda_visible_devices='3'))
    plan=m.prepare(tmp_path/'prepared',pre,lib,'d'*40,'qualification-test',
        target_python=Path(sys._base_executable),site_root=Path(sysconfig.get_path('purelib')))
    from exposedpath_v141 import gate8_target_python as target
    # In-process CPU backend double; real isolated child behavior has separate subprocess tests.
    monkeypatch.setattr(target,'current',lambda contract:dict(pid=os.getpid(),parent_pid=os.getppid(),snapshot=contract['actual']['snapshot']))
    path=tmp_path/'trace.sqlite'; _make_source_sqlite(path)
    db=sqlite3.connect(path)
    for table in ('NVTX_EVENTS','CUPTI_ACTIVITY_KIND_RUNTIME','CUPTI_ACTIVITY_KIND_SYNCHRONIZATION',
        'CUPTI_ACTIVITY_KIND_KERNEL','CUPTI_ACTIVITY_KIND_MEMCPY','CUPTI_ACTIVITY_KIND_MEMSET',
        'CUPTI_ACTIVITY_KIND_CUDA_EVENT','DIAGNOSTIC_EVENT'):
        db.execute('DELETE FROM '+table)
    db.execute('ALTER TABLE DIAGNOSTIC_EVENT ADD COLUMN globalPid INTEGER')
    db.execute('ALTER TABLE DIAGNOSTIC_EVENT ADD COLUMN timestampType INTEGER')
    db.execute('ALTER TABLE TARGET_INFO_GPU ADD COLUMN uuid TEXT')
    db.execute('ALTER TABLE TARGET_INFO_GPU ADD COLUMN busLocation TEXT')
    db.execute('UPDATE TARGET_INFO_GPU SET uuid=?,busLocation=?',(UUID,'0000:E1:00.0'))
    db.execute('CREATE TABLE TARGET_INFO_CUDA_DEVICE(pid INTEGER,cudaId INTEGER,uuid TEXT,gpuId INTEGER)')
    pid=os.getpid(); tid=(pid<<24)|threading.get_native_id()
    db.execute('INSERT INTO DIAGNOSTIC_EVENT VALUES (0,2,1,?, ?,1)',('Process '+str(pid)+' was launched by the profiler',pid<<24))
    db.execute('INSERT INTO TARGET_INFO_CUDA_DEVICE VALUES (?,0,?,0)',(pid,UUID))
    db.execute('UPDATE TARGET_INFO_CUDA_CONTEXT_INFO SET processId=?,nullStreamId=2',(pid,))
    db.execute('UPDATE TARGET_INFO_CUDA_STREAM SET processId=?,flag=0',(pid,))
    db.execute("INSERT INTO ENUM_CUPTI_SYNC_TYPE VALUES (2,'CONTEXT_SYNCHRONIZE','Context synchronize')")
    class Clock:
        value=0
        def __call__(self): self.value+=10; return self.value
    clock=Clock(); stack=[]; corr=100
    names={}
    def sid(name):
        if name not in names:
            names[name]=200+len(names)
            db.execute('INSERT INTO StringIds VALUES (?,?)',(names[name],name))
        return names[name]
    class Backend:
        pending=None; token=0; initialized=True
        def __init__(self,library):
            self.nvtx=SimpleNamespace(range_push=self.push,range_pop=self.pop)
            self.cuda=self
        def is_initialized(self): return self.initialized
        def current_device(self): return 0
        def current_stream(self,_): return SimpleNamespace(cuda_stream=0,device=SimpleNamespace(index=0))
        default_stream=current_stream
        def identity(self): return dict(gpu_uuid=UUID,pci_bus_id='0000:E1:00.0')
        def push(self,label): stack.append((clock(),label))
        def pop(self):
            a,label=stack.pop(); db.execute('INSERT INTO NVTX_EVENTS(start,end,eventType,text,globalTid) VALUES (?,?,59,?,?)',(a,clock(),label,tid))
        def mark(self,label): db.execute('INSERT INTO NVTX_EVENTS(start,end,eventType,text,globalTid) VALUES (?,NULL,34,?,?)',(clock(),label,tid))
        def api(self,name):
            nonlocal corr
            corr+=1; a,b=clock(),clock()
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?,?,0,?,?,?,0,NULL)',(a,b,tid,corr,sid(name)))
            return a,b,corr
        def prepare(self):
            a,b,c=self.api('cudaDeviceSynchronize')
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION VALUES (?,?,0,1,NULL,4294967295,?,?,NULL,2,4294967295,NULL)',(a+1,b-1,c,pid<<24))
        def submit(self,token): self.token=token; self.pending=('kernel',self.api('cudaLaunchKernel'))
        def copy(self):
            # A kernel without an internal wait completes before its copy.
            if self.pending:
                _,(a,b,c)=self.pending
                db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES (?,?,0,1,NULL,2,?,?,?, ?,NULL,NULL)',(b,b+2,c,pid<<24,sid('g8q_token_kernel'),sid('g8q_token_kernel')))
            self.pending=('copy',self.api('cudaMemcpyAsync'))
        def wait(self):
            a,b,c=self.api('cudaStreamSynchronize')
            kind,(x,y,k)=self.pending
            if kind=='kernel':
                db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES (?,?,0,1,NULL,2,?,?,?, ?,NULL,NULL)',(y,a+2,k,pid<<24,sid('g8q_token_kernel'),sid('g8q_token_kernel')))
            else:
                db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_MEMCPY VALUES (?,?,0,1,NULL,2,?,?,4,2,2,1,NULL)',(y,a+4,k,pid<<24))
            self.pending=None
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION VALUES (?,?,0,1,NULL,2,?,?,NULL,3,4294967295,NULL)',(a+1,b-1,c,pid<<24))
        def read(self): return self.token
        def close(self): self.initialized=False
    receipt=(m.execute(plan,tmp_path/'execution',backend_factory=Backend,clock_ns=clock)
             if executor is None else executor(Backend,clock,db,plan))
    db.commit(); db.close()
    rep=tmp_path/'synthetic.rep'; rep.write_bytes(b'SYNTHETIC NOT NSIGHT')
    export=write_json(tmp_path/'export.json',dict(status='PASS',error=None,analyzer_allowed=True,
        attempt_count=1,successful_attempt=1,rep_sha256=sha(rep),canonical_sqlite_sha256=sha(path),
        attempts=[dict(number=1,status='PASS',exit_code=0,process_exited=True,timed_out=False,
            terminated_pid=None,validation_issues=[],rep_sha256=sha(rep),sqlite_sha256=sha(path),sqlite_size=path.stat().st_size)]))
    return plan,receipt,path,rep,export
