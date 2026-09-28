"""Bounded adapter-only process facts. Never a warning-scope exemption."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sys
from threading import Lock
import time
import uuid

VERSION='exposedpath-adapter-process-origin/0.1.0'
PURPOSES={'GIT_COMMIT_QUERY','GIT_DIRTY_QUERY','NVIDIA_SMI_QUERY','UNCLASSIFIED_ADAPTER_COMMAND'}
_active=None


class Recorder:
    def __init__(self,path):
        self.path=Path(path)
        self.handle=self.path.open('x',encoding='utf-8')
        self.lock=Lock()
        self.sequence=0
        self.failed=False
        self.parent_instance_id=uuid.uuid4().hex
        try:
            self.emit('OPEN',schema_version=VERSION,scope='ACTIVE_PLATFORM_ADAPTER_CALLS_ONLY',
                native_process_coverage='UNKNOWN',unrecorded_processes='UNKNOWN_NOT_ABSENCE',
                warning_disposition='NOT_ASSESSED',clock='PYTHON_PERF_COUNTER_NS',
                parent_executable=str(Path(sys.executable).resolve()))
        except BaseException:
            self.handle.close()
            raise

    def emit(self,event,**fields):
        with self.lock:
            if self.failed: raise OSError('PROCESS_ORIGIN_RECORDING_FAILED')
            row=dict(event=event,sequence=self.sequence,parent_pid=os.getpid(),
                parent_instance_id=self.parent_instance_id,time_ns=time.perf_counter_ns(),**fields)
            try:
                self.handle.write(json.dumps(row,sort_keys=True)+'\n')
                self.handle.flush()
                os.fsync(self.handle.fileno())
            except Exception:
                self.failed=True
                raise
            self.sequence+=1


def active():
    return _active


@contextmanager
def recording(path):
    global _active
    if _active is not None:
        raise ValueError('PROCESS_ORIGIN_ALREADY_ACTIVE')
    recorder=Recorder(path)
    _active=recorder
    try:
        yield recorder
    finally:
        original=sys.exc_info()[0] is not None
        _active=None
        try:
            recorder.emit('CLOSED')
            load_recording(path)
        except Exception:
            # Preserve execution failure; incomplete evidence cannot be accepted.
            if not original: raise
        finally:
            primary=original or sys.exc_info()[0] is not None
            try: recorder.handle.close()
            except Exception:
                if not primary: raise


def load_recording(path):
    """Reject incomplete/mixed lifecycles; CLOSED is not whole-process coverage."""
    rows=[json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines()]
    def require(ok):
        if not ok: raise ValueError('PROCESS_ORIGIN_INVALID_OR_INCOMPLETE')
    require(len(rows)>=2 and rows[0].get('event')=='OPEN' and rows[-1].get('event')=='CLOSED')
    header=rows[0]
    require(header.get('schema_version')==VERSION and header.get('native_process_coverage')=='UNKNOWN'
        and header.get('unrecorded_processes')=='UNKNOWN_NOT_ABSENCE'
        and header.get('warning_disposition')=='NOT_ASSESSED'
        and header.get('scope')=='ACTIVE_PLATFORM_ADAPTER_CALLS_ONLY'
        and header.get('clock')=='PYTHON_PERF_COUNTER_NS'
        and type(header.get('parent_pid')) is int and header['parent_pid']>0
        and isinstance(header.get('parent_instance_id'),str) and len(header['parent_instance_id'])==32)
    calls={}
    running_pids=set()
    last=-1
    for i,row in enumerate(rows):
        require(row.get('sequence')==i and row.get('parent_instance_id')==header['parent_instance_id']
            and row.get('parent_pid')==header['parent_pid'] and type(row.get('time_ns')) is int
            and row['time_ns']>=last)
        last=row['time_ns']
        event=row['event']
        if i in (0,len(rows)-1): continue
        key=row.get('call_id')
        require(isinstance(key,str) and bool(key))
        if event=='STARTING':
            require(key not in calls and row.get('purpose') in PURPOSES)
            calls[key]=row
        elif event=='STARTED':
            require(key in calls and calls[key]['event']=='STARTING' and type(row.get('pid')) is int
                and row['pid']>0 and isinstance(row.get('executable'),str) and bool(row['executable'])
                and row.get('image_evidence')=='RESOLVED_LAUNCH_IMAGE_NOT_OS_ATTESTED'
                and row['pid'] not in running_pids)
            running_pids.add(row['pid'])
            calls[key]=row
        elif event=='START_FAILED':
            require(key in calls and calls[key]['event']=='STARTING'
                and {'pid','returncode','error_type'}<=row.keys() and row['pid'] is None
                and row['returncode'] is None and isinstance(row['error_type'],str))
            calls[key]=row
        elif event=='EXITED':
            require(key in calls and calls[key]['event']=='STARTED' and row.get('pid')==calls[key]['pid']
                and type(row.get('returncode')) is int)
            running_pids.remove(row['pid'])
            calls[key]=row
        else: require(False)
    require(all(r['event'] in ('START_FAILED','EXITED') for r in calls.values()))
    return rows
