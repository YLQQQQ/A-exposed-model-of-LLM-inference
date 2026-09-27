"""Opt-in observations of the audited loader's host jobs, never S ownership."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import threading
import time
from types import CodeType

from .gate8_identity import PASS_FIELDS

VERSION = 'exposedpath-load-task-ledger/0.1.0'
PREFIX = 'EXPOSEDPATH_LOAD_TASK_V1:'
FAMILIES = {
    'hf-load-tasks/0.1.0': ('0.1.0', ('trust_remote_code', 'fallback')),
    'hf-source-probe/0.1.0': ('0.2.0', ('source_probe',)),
}
_PATCH_LOCK = threading.Lock()
TARGET_SOURCE_HASHES = {
    'core_model_loading.py':'c5b6bcdb6401a3cfdf825bc979d41ac3e7e075e09459021363dce5e68c54de22',
    'modeling_utils.py':'38c2bd02ed7af229f54e2f02dae65663be7af29ed2c9498bd1c460cf60fbb62d',
    'integrations/accelerate.py':'4469496da61fdc632faf9cacfc128729b12030eb03c5ef4bb70a66b6012b3a82',
}


def verify_source_files(root, expected):
    root=Path(root).resolve()
    rows=[]
    for relative, expected_hash in expected.items():
        path=(root/relative).resolve()
        if not path.is_relative_to(root) or Path(relative).is_absolute() or '..' in Path(relative).parts:
            raise ValueError('LOAD_SOURCE_PATH')
        if not path.is_file() or path.stat().st_size>2*1024*1024:
            raise ValueError('LOAD_SOURCE_FILE')
        data=path.read_bytes()
        actual=hashlib.sha256(data).hexdigest()
        if actual!=expected_hash:
            raise ValueError('LOAD_SOURCE_HASH')
        rows.append(dict(package_relative_path='transformers/'+relative,sha256=actual,size_bytes=len(data)))
    return rows


def resolve_target_source():
    """Called only by the explicit live-model entry, never by the static tool."""
    import importlib
    from importlib.metadata import version
    if version('transformers')!='5.17.0':
        raise ValueError('LOAD_SOURCE_VERSION')
    core=importlib.import_module('transformers.core_model_loading')
    path=Path(core.__file__).resolve()
    rows=verify_source_files(path.parent,TARGET_SOURCE_HASHES)
    original=core.spawn_materialize
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=TARGET_SOURCE_HASHES['core_model_loading.py']:
        raise ValueError('LOAD_SOURCE_HASH')
    # Compile, never execute, the verified bytes. Disk identity alone cannot
    # vouch for a replaced or stale in-memory function with the same filename.
    expected=[code for code in compile(data,str(path),'exec',dont_inherit=True).co_consts
              if isinstance(code,CodeType) and code.co_name=='spawn_materialize']
    if (not hasattr(original,'__code__') or Path(original.__code__.co_filename).resolve()!=path
            or original.__name__!='spawn_materialize' or len(expected)!=1 or original.__code__!=expected[0]):
        raise ValueError('LOAD_SOURCE_HOOK_CONFLICT')
    return core,dict(profile='hf-load-tasks/0.1.0',source_files=rows,qualification='NOT_ASSESSED'),original


def _digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


class LoadTaskObserver:
    """Wrap only spawn_materialize.submit during one loader attempt.

    Futures are returned unchanged. No result/exception consumption, waits,
    shutdowns, CUDA calls or stream probes are performed by this observer.
    A synchronous deferred callable is returned unchanged and explicitly UNKNOWN.
    """
    def __init__(self, *, identity, pid, parent_stage_id, source, push=None, pop=None, expected_hook=None):
        if (set(identity)!=set(PASS_FIELDS) or identity['pass_id'] not in ('pass0','pass1')
                or any(not isinstance(v,str) or not v for v in identity.values())
                or identity['run_role']!='ENGINEERING' or identity['data_role']!='Engineering'
                or type(pid) is not int or pid!=os.getpid()
                or len(parent_stage_id)!=64 or any(c not in '0123456789abcdef' for c in parent_stage_id)
                or source.get('qualification')!='NOT_ASSESSED'):
            raise ValueError('LOAD_TASK_IDENTITY')
        self.lock=threading.RLock()
        self.push,self.pop=push,pop
        self.source=deepcopy(source)
        if source.get('profile') not in FAMILIES:
            raise ValueError('LOAD_TASK_SOURCE_PROFILE')
        self.version,self.branches=FAMILIES[source['profile']]
        self.identity=deepcopy(identity)
        self.pid,self.parent_stage_id=pid,parent_stage_id
        self.attempts,self.tasks,self.issues=[],[],[]
        self.threads={}
        self.frozen=None
        self.active=False
        self.expected_hook=expected_hook
        self.expected_code=None if expected_hook is None else expected_hook.__code__

    def _issue(self, reason):
        with self.lock:
            if self.frozen is None and reason not in self.issues:
                self.issues.append(reason)

    def _update(self, entry, **fields):
        with self.lock:
            if self.frozen is None:
                entry.update(fields)

    def _job(self, entry, function, args, kwargs):
        with self.lock:
            native_tid=threading.get_native_id()
            thread=threading.current_thread()
            if thread not in self.threads:
                self.threads[thread]=_digest([self.identity,'thread',len(self.threads)])
            payload=dict(schema_version='exposedpath-load-task-marker/'+self.version,
                identity=self.identity,pid=self.pid,parent_stage_id=self.parent_stage_id,
                attempt_id=entry['attempt_id'],task_id=entry['task_id'],native_tid=native_tid,
                thread_instance_id=self.threads[thread],source_descriptor_sha256=_digest(self.source),
                scope_semantics='HOST_JOB_ONLY',request_identity=None,marker_role='non_sync_marker')
            self._update(entry,status='IN_FLIGHT',native_tid=native_tid,
                thread_instance_id=self.threads[thread],host_start_ns=time.perf_counter_ns(),
                marker_payload=deepcopy(payload))
        pushed=False
        if self.identity['pass_id']=='pass1':
            try:
                if self.push is None or self.pop is None:
                    raise ValueError('missing marker sink')
                self.push(PREFIX+json.dumps(payload,sort_keys=True,separators=(',',':')))
                pushed=True
            except Exception:
                self._issue('MARKER_PUSH_FAILED')
        status,error='COMPLETE',None
        try:
            result=function(*args,**kwargs)
            return result
        except BaseException as exc:
            status,error='FAILED',type(exc).__name__
            raise
        finally:
            if pushed:
                try:
                    self.pop()
                except Exception:
                    self._issue('MARKER_POP_FAILED')
            # One locked transition after marker cleanup: a concurrent seal
            # sees IN_FLIGHT or a complete terminal record, never half of one.
            self._update(entry,status=status,error=error,host_end_ns=time.perf_counter_ns())

    def run_attempt(self, module, operation, *, branch):
        if self.frozen is not None or branch not in self.branches:
            raise ValueError('LOAD_TASK_ATTEMPT_STATE')
        if not _PATCH_LOCK.acquire(blocking=False):
            raise ValueError('LOAD_TASK_SCOPE_ALREADY_ACTIVE')
        try:
            original=module.spawn_materialize
            if self.expected_hook is not None and (original is not self.expected_hook
                    or original.__code__!=self.expected_code):
                raise ValueError('LOAD_SOURCE_HOOK_CONFLICT')
        except BaseException:
            _PATCH_LOCK.release()
            raise
        submit_tid=threading.get_native_id()
        attempt=dict(attempt_id=_digest([self.identity,self.parent_stage_id,len(self.attempts)]),
            ordinal=len(self.attempts),branch=branch,status='FAILED',error=None,
            host_start_ns=time.perf_counter_ns(),host_end_ns=None,return_type=None)
        self.attempts.append(attempt)
        self.active=True
        observer=self
        def wrapped(thread_pool,*args,**kwargs):
            pool=thread_pool
            if threading.get_native_id()!=submit_tid:
                observer._issue('OTHER_SUBMIT_THREAD')
                return original(pool,*args,**kwargs)
            with observer.lock:
                entry=dict(task_id=_digest([attempt['attempt_id'],len(observer.tasks)]),
                    ordinal=len(observer.tasks),attempt_id=attempt['attempt_id'],submit_native_tid=submit_tid,
                    status='SUBMITTED',native_tid=None,thread_instance_id=None,
                    host_start_ns=None,host_end_ns=None,error=None,marker_payload=None)
                observer.tasks.append(entry)
            if pool is None:
                observer._update(entry,status='UNOBSERVED_SYNC_CALLABLE')
                return original(pool,*args,**kwargs)
            class SubmitProxy:
                def submit(self, function, *job_args, **job_kwargs):
                    try:
                        future=pool.submit(observer._job,entry,function,job_args,job_kwargs)
                    except BaseException as exc:
                        observer._update(entry,status='SUBMIT_FAILED',error=type(exc).__name__)
                        raise
                    def done(completed):
                        if completed.cancelled():
                            observer._update(entry,status='CANCELLED')
                    future.add_done_callback(done)
                    return future
            return original(SubmitProxy(),*args,**kwargs)
        try:
            module.spawn_materialize=wrapped
            result=operation()
            attempt.update(status='COMPLETE',return_type=f'{type(result).__module__}.{type(result).__qualname__}')
            return result
        except BaseException as exc:
            attempt['error']=type(exc).__name__
            raise
        finally:
            attempt['host_end_ns']=time.perf_counter_ns()
            if module.spawn_materialize is wrapped:
                module.spawn_materialize=original
            else:
                self._issue('PATCH_RESTORE_CONFLICT')
            self.active=False
            _PATCH_LOCK.release()

    def seal(self):
        """A point-in-time snapshot; never wait for jobs or rewrite it later."""
        with self.lock:
            if self.active:
                raise ValueError('LOAD_TASK_ATTEMPT_ACTIVE')
            if self.frozen is None:
                tasks=deepcopy(self.tasks)
                incomplete=bool(self.issues or not self.attempts
                    or any(a['status']!='COMPLETE' for a in self.attempts)
                    or any(t['status']!='COMPLETE' for t in tasks))
                self.frozen=dict(schema_version='exposedpath-load-task-ledger/'+self.version,identity=self.identity,pid=self.pid,
                    parent_stage_id=self.parent_stage_id,source_descriptor=self.source,
                    source_descriptor_sha256=_digest(self.source),attempts=deepcopy(self.attempts),tasks=tasks,
                    issues=list(self.issues),host_clock_id='PYTHON_PERF_COUNTER_NS',
                    sealed_host_ns=time.perf_counter_ns(),snapshot_semantics='AT_SEAL_NO_WAIT',
                    observation_status='INCOMPLETE' if incomplete else 'COMPLETE',
                    ownership_status='NOT_ASSESSED',default_stream_mode='UNKNOWN',
                    measurement_validity='NOT_ASSESSED')
            return deepcopy(self.frozen)


def validate_load_tasks(value, ledger, stages):
    """Validate observation provenance only; never grant S ownership/validity."""
    from .gate8_stages import validate_stage_ledger
    validate_stage_ledger(stages, ledger)
    def require(condition):
        if not condition:
            raise ValueError('LOAD_TASK_IDENTITY_OR_SHAPE')
    def timestamp(value):
        return type(value) is int and -(2**63) <= value < 2**63
    def positive(value):
        return type(value) is int and value > 0
    require(type(value) is dict and set(value)=={
        'schema_version','identity','pid','parent_stage_id','source_descriptor',
        'source_descriptor_sha256','attempts','tasks','issues','host_clock_id',
        'sealed_host_ns','snapshot_semantics','observation_status','ownership_status',
        'default_stream_mode','measurement_validity'})
    source=value['source_descriptor']
    require(type(source) is dict and isinstance(source.get('profile'),str)
        and source['profile'] in FAMILIES)
    version,branches=FAMILIES[source['profile']]
    require(value['schema_version']=='exposedpath-load-task-ledger/'+version and value['identity']=={k:ledger[k] for k in PASS_FIELDS}
        and type(value['pid']) is int and value['pid']==ledger['pid'])
    require(stages['setup_observed'] and stages['stages']
        and stages['stages'][0]['payload']['stage_role']=='setup'
        and value['parent_stage_id']==stages['stages'][0]['payload']['stage_id'])
    require(value['host_clock_id']=='PYTHON_PERF_COUNTER_NS'
        and timestamp(value['sealed_host_ns']) and value['snapshot_semantics']=='AT_SEAL_NO_WAIT'
        and value['ownership_status']=='NOT_ASSESSED' and value['default_stream_mode']=='UNKNOWN'
        and value['measurement_validity']=='NOT_ASSESSED')
    source=value['source_descriptor']
    require(type(source) is dict and set(source)=={'profile','source_files','qualification'}
        and source['qualification']=='NOT_ASSESSED'
        and type(source['source_files']) is list and bool(source['source_files'])
        and value['source_descriptor_sha256']==_digest(source))
    names=set()
    for row in source['source_files']:
        require(type(row) is dict and set(row)=={'package_relative_path','sha256','size_bytes'})
        name=row['package_relative_path']
        require(isinstance(name,str) and name.startswith('transformers/') and '\\' not in name
            and ':' not in name and '..' not in name.split('/') and name not in names
            and positive(row['size_bytes']) and isinstance(row['sha256'],str)
            and len(row['sha256'])==64 and all(c in '0123456789abcdef' for c in row['sha256']))
        names.add(name)
    require({row['package_relative_path']:row['sha256'] for row in source['source_files']}
        =={'transformers/'+name:sha for name,sha in TARGET_SOURCE_HASHES.items()})
    require(type(value['attempts']) is list and type(value['tasks']) is list
        and type(value['issues']) is list
        and all(isinstance(x,str) and x for x in value['issues']))
    attempts={}
    previous_end=None
    for ordinal, attempt in enumerate(value['attempts']):
        require(type(attempt) is dict and set(attempt)=={'attempt_id','ordinal','branch','status',
            'error','host_start_ns','host_end_ns','return_type'})
        require(type(attempt['ordinal']) is int and attempt['ordinal']==ordinal
            and attempt['attempt_id']==_digest([value['identity'],value['parent_stage_id'],ordinal])
            and attempt['branch'] in branches
            and attempt['status'] in ('COMPLETE','FAILED')
            and timestamp(attempt['host_start_ns']) and timestamp(attempt['host_end_ns'])
            and attempt['host_start_ns']<=attempt['host_end_ns']<=value['sealed_host_ns'])
        require(previous_end is None or previous_end<=attempt['host_start_ns'])
        previous_end=attempt['host_end_ns']
        require((attempt['status']=='COMPLETE' and attempt['error'] is None
                 and isinstance(attempt['return_type'],str) and bool(attempt['return_type']))
            or (attempt['status']=='FAILED' and isinstance(attempt['error'],str)
                 and bool(attempt['error']) and attempt['return_type'] is None))
        attempts[attempt['attempt_id']]=attempt
    threads={}
    for ordinal, task in enumerate(value['tasks']):
        require(type(task) is dict and set(task)=={'task_id','ordinal','attempt_id','submit_native_tid',
            'status','native_tid','thread_instance_id','host_start_ns','host_end_ns','error','marker_payload'})
        require(type(task['ordinal']) is int and task['ordinal']==ordinal
            and task['attempt_id'] in attempts and positive(task['submit_native_tid'])
            and task['task_id']==_digest([task['attempt_id'],ordinal]))
        status=task['status']
        require(status in ('COMPLETE','FAILED','IN_FLIGHT','SUBMITTED','SUBMIT_FAILED',
                            'CANCELLED','UNOBSERVED_SYNC_CALLABLE'))
        require((isinstance(task['error'],str) and bool(task['error']))
            if status in ('FAILED','SUBMIT_FAILED') else task['error'] is None)
        if status in ('COMPLETE','FAILED','IN_FLIGHT'):
            require(positive(task['native_tid']) and timestamp(task['host_start_ns'])
                and attempts[task['attempt_id']]['host_start_ns']<=task['host_start_ns']<=value['sealed_host_ns'])
            if status=='IN_FLIGHT':
                require(task['host_end_ns'] is None)
            else:
                require(timestamp(task['host_end_ns'])
                    and task['host_start_ns']<=task['host_end_ns']<=value['sealed_host_ns'])
            thread=task['thread_instance_id']
            require(isinstance(thread,str) and len(thread)==64
                and all(c in '0123456789abcdef' for c in thread))
            require(thread not in threads or threads[thread]==task['native_tid'])
            threads[thread]=task['native_tid']
            require(task['marker_payload']==dict(schema_version='exposedpath-load-task-marker/'+version,
                identity=value['identity'],pid=value['pid'],parent_stage_id=value['parent_stage_id'],
                attempt_id=task['attempt_id'],task_id=task['task_id'],native_tid=task['native_tid'],
                thread_instance_id=thread,source_descriptor_sha256=value['source_descriptor_sha256'],
                scope_semantics='HOST_JOB_ONLY',request_identity=None,marker_role='non_sync_marker'))
        else:
            require(all(task[k] is None for k in ('native_tid','thread_instance_id','host_start_ns',
                                                  'host_end_ns','marker_payload')))
    incomplete=bool(value['issues'] or not attempts
        or any(a['status']!='COMPLETE' for a in value['attempts'])
        or any(t['status']!='COMPLETE' for t in value['tasks']))
    require(value['observation_status']==('INCOMPLETE' if incomplete else 'COMPLETE'))


def load_producer_observations(receipt_path):
    """Read sealed 0.4 observations, not a scientific-chain input adapter."""
    receipt_path=Path(receipt_path).resolve()
    receipt=json.loads(receipt_path.read_bytes())
    def reject():
        raise ValueError('LOAD_TASK_PRODUCER_RECEIPT')
    names={'pass_identity.json','host_boundaries.json','drain_ledger.json','stage_ledger.json','load_tasks.json'}
    if (type(receipt) is not dict or set(receipt)!={'schema_version','run_id','pass_id','attempt_id',
            'status','files','gate8_verdict'}
            or receipt['schema_version']!='exposedpath-gate8-producer-receipt/0.4.0'
            or receipt['gate8_verdict']!='NOT_RUN' or type(receipt['files']) is not dict
            or set(receipt['files'])!=names):
        reject()
    artifacts={}
    for name in names:
        ref=receipt['files'][name]
        if (type(ref) is not dict or set(ref)!={'filename','sha256','size_bytes'} or ref['filename']!=name):
            reject()
        path=(receipt_path.parent/name).resolve()
        if path.parent!=receipt_path.parent or not path.is_file():
            reject()
        data=path.read_bytes()
        if (type(ref['size_bytes']) is not int or ref['size_bytes']!=len(data)
                or not data or hashlib.sha256(data).hexdigest()!=ref['sha256']):
            reject()
        artifacts[name]=json.loads(data)
    ledger=artifacts['pass_identity.json']
    value=artifacts['load_tasks.json']
    validate_load_tasks(value,ledger,artifacts['stage_ledger.json'])
    # These sidecars are not qualified for Canonical/S here, but a rehashed
    # cross-request/pass mixture must not pass an observation-file read.
    from .gate8_identity import validate_shape
    measured=[r for r in ledger['requests'] if r['request_role']=='measured']
    expected={b:r['identity'] for r in measured for b in r['observed_boundary_ids']}
    host=artifacts['host_boundaries.json']
    if not isinstance(host,list) or len(host)!=len(expected):
        reject()
    seen=set()
    for row in host:
        if type(row) is not dict or 'payload' not in row:
            reject()
        payload=row['payload']
        validate_shape('boundary_payload',payload)
        key=payload['boundary_id']
        if key in seen or key not in expected or payload['identity']!=expected[key]:
            reject()
        seen.add(key)
    drains=artifacts['drain_ledger.json']
    if (type(drains) is not dict or set(drains)!={'schema_version','drains'}
            or drains['schema_version']!='exposedpath-drain-ledger/0.1.0'
            or type(drains['drains']) is not list):
        reject()
    planned={r['expected_boundary_ids'][0]+':drain':r for r in measured}
    seen=set()
    for row in drains['drains']:
        if type(row) is not dict or row.get('operation_id') not in planned:
            reject()
        key=row['operation_id']
        if (key in seen or row.get('identity')!=planned[key]['identity']
                or row.get('schema_version')!='exposedpath-drain-marker/0.1.0'):
            reject()
        seen.add(key)
    if any(r['outcome']=='COMPLETE' and key not in seen for key,r in planned.items()):
        reject()
    if any(receipt[k]!=ledger[k] for k in ('run_id','pass_id','attempt_id')):
        reject()
    status='COMPLETE' if (all(r['outcome']=='COMPLETE' for r in ledger['requests'])
        and value['observation_status']=='COMPLETE') else 'INCOMPLETE'
    if receipt['status']!=status:
        reject()
    return value
