"""Explicit interpreter adapter for controlled and Engineering model entries. Probes are CPU-only.

No PATH interpreter selection, site auto-discovery, .pth execution or CUDA probe.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

VERSION='exposedpath-target-python/0.1.0'
ROOT=Path(__file__).resolve().parents[1]
BOOTSTRAP="import sys;sys.path[:0]=sys.argv[1:3];del sys.argv[1:3];from exposedpath_v141.gate8_target_python import main;raise SystemExit(main())"


def require(ok,reason):
    if not ok: raise ValueError('TARGET_PYTHON_'+reason)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def environment():
    return dict(CUDA_DEVICE_ORDER=os.environ.get('CUDA_DEVICE_ORDER'),
        CUDA_VISIBLE_DEVICES=os.environ.get('CUDA_VISIBLE_DEVICES'),
        path_sha256=hashlib.sha256(os.environ.get('PATH','').encode()).hexdigest())


def snapshot(site_root):
    import jsonschema
    site_root=Path(site_root).resolve(); origin=Path(jsonschema.__file__).resolve()
    require(origin.is_relative_to(site_root),'DEPENDENCY_ORIGIN')
    return dict(executable=str(Path(sys.executable).resolve()),executable_sha256=sha(sys.executable),
        base_executable=str(Path(sys._base_executable).resolve()),prefix=str(Path(sys.prefix).resolve()),
        base_prefix=str(Path(sys.base_prefix).resolve()),version=sys.version,
        isolated=bool(sys.flags.isolated),no_site=bool(sys.flags.no_site),
        site_root=str(site_root),jsonschema_file=str(origin),jsonschema_sha256=sha(origin),
        module_root=str(ROOT),sys_path=list(sys.path),environment=environment())


def argv(python,site_root,args):
    python=Path(python); site_root=Path(site_root)
    require(python.is_absolute() and python.is_file() and site_root.is_absolute() and site_root.is_dir(),'EXPLICIT_PATHS')
    return [str(python.resolve()),'-I','-S','-c',BOOTSTRAP,str(ROOT),str(site_root.resolve()),*args]


def validate_probe(value):
    require(value.get('schema_version')==VERSION,'VERSION')
    actual=value['actual']; s=actual['snapshot']
    require(type(value['launch_pid']) is int and value['launch_pid']>0
        and type(actual['pid']) is int and actual['pid']==value['launch_pid'] and actual['nonce']==value['nonce'],'PROBE_PID_NONCE')
    require(s['executable']==value['requested_executable']==s['base_executable']
        and s['executable_sha256']==value['requested_sha256'] and s['site_root']==value['site_root']
        and s['module_root']==value['module_root'] and s['isolated'] is True and s['no_site'] is True
        and s['environment']==value['environment'],'PROBE_ENVIRONMENT')
    return value


def probe(python,site_root):
    command=argv(python,site_root,['probe']); nonce=uuid.uuid4().hex
    command+=['--nonce',nonce,'--site-root',str(Path(site_root).resolve())]
    value=dict(schema_version=VERSION,requested_executable=str(Path(python).resolve()),
        requested_sha256=sha(python),site_root=str(Path(site_root).resolve()),module_root=str(ROOT),environment=environment(),nonce=nonce)
    process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,cwd=ROOT,shell=False)
    try: stdout,stderr=process.communicate(timeout=20)
    except subprocess.TimeoutExpired:
        process.kill(); process.communicate(timeout=10)
        raise ValueError('TARGET_PYTHON_PROBE_TIMEOUT_NO_RETRY')
    require(process.returncode==0,'PROBE_EXIT:'+stderr[-500:])
    value.update(launch_pid=process.pid,actual=json.loads(stdout))
    return validate_probe(value)


def current(contract):
    validate_probe(contract)
    actual=dict(pid=os.getpid(),parent_pid=os.getppid(),snapshot=snapshot(contract['site_root']))
    expected=contract['actual']['snapshot']; observed=actual['snapshot']
    if observed!=expected:
        error=ValueError('TARGET_PYTHON_RUNTIME_ENVIRONMENT')
        error.snapshot_difference={k:dict(expected=expected.get(k),observed=observed.get(k))
            for k in expected.keys() | observed.keys() if expected.get(k)!=observed.get(k)}
        raise error
    return actual


def bind_producer(contract,runtime,ledger_pid):
    validate_probe(contract)
    require(type(runtime['pid']) is int and runtime['pid']==ledger_pid and ledger_pid>0
        and runtime['snapshot']==contract['actual']['snapshot'],'PRODUCER_IDENTITY')


def bind_trace_launch(path,pid):
    import sqlite3
    import re
    path=Path(path).resolve(); before=sha(path)
    with sqlite3.connect(path.as_uri()+'?mode=ro&immutable=1',uri=True) as c:
        rows=c.execute('SELECT rowid,source,severity,text,globalPid FROM DIAGNOSTIC_EVENT').fetchall()
    matches=[]
    for row,source,severity,text,gpid in rows:
        match=re.fullmatch(r'Process (\d+) was launched by the profiler',text)
        if match:
            require(source==2 and severity==1 and type(gpid) is int and gpid>=0
                and gpid%(1<<24)==0 and ((gpid>>24)&0xffffff)==int(match[1]),'TRACE_LAUNCH_FIELDS')
            matches.append(dict(rowid=row,pid=int(match[1]),global_pid=gpid))
    require(len(matches)==1 and matches[0]['pid']==pid,'TRACE_LAUNCH_PID')
    with sqlite3.connect(path.as_uri()+'?mode=ro&immutable=1',uri=True) as c:
        tables={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if 'NVTX_EVENTS' in tables:
            # Numeric PID equality alone is insufficient across global namespaces.
            tids=[r[0] for r in c.execute('SELECT DISTINCT globalTid FROM NVTX_EVENTS')]
            require(tids and all(t-t%(1<<24)==matches[0]['global_pid'] for t in tids),'TRACE_GLOBAL_PROCESS')
    require(sha(path)==before,'TRACE_CHANGED')
    return dict(**matches[0],sqlite_sha256=before)


def model_entry():
    """Persist target-side evidence before model-module import; never bypass a gate.

    STARTED without exit.json is explicitly unfinished, not a successful exit.
    Native fd writes/aborts before Python dispatch are not guaranteed captured.
    """
    import argparse
    import contextlib
    import traceback
    p=argparse.ArgumentParser(add_help=False,allow_abbrev=False)
    p.add_argument('--output-dir',required=True)
    args,_=p.parse_known_args(sys.argv[2:])
    output=Path(args.output_dir).resolve()
    entry=output.with_name(output.name+'-entry')
    entry.mkdir(parents=True,exist_ok=False)
    report=dict(schema_version='exposedpath-target-entry/0.1.0',status='STARTED',
        pid=os.getpid(),parent_pid=os.getppid(),executable=str(Path(sys.executable).resolve()),
        argv=list(sys.argv),environment=environment(),exit_code=None)
    def persist(name,value):
        with (entry/name).open('x',encoding='utf-8') as handle:
            json.dump(value,handle,indent=2,sort_keys=True); handle.flush(); os.fsync(handle.fileno())
    persist('started.json',report)
    with (entry/'stdout.txt').open('x',encoding='utf-8',buffering=1) as stdout, \
            (entry/'stderr.txt').open('x',encoding='utf-8',buffering=1) as stderr:
        from exposedpath.process_origin import recording
        with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
            try:
                with recording(entry/'subprocess_origin.jsonl'):
                    from exposedpath.gate8_diagnostic import main as model
                    sys.argv[1:2]=['run']
                    code=model()
                report.update(status='EXITED',exit_code=0 if code is None else int(code))
                return code
            except BaseException as exc:
                code=(exc.code if isinstance(exc.code,int) else (0 if exc.code is None else 1)) if isinstance(exc,SystemExit) else (130 if isinstance(exc,KeyboardInterrupt) else 1)
                report.update(status='EXITED',exit_code=code,exception_type=type(exc).__name__,
                    exception_message=str(exc),traceback=traceback.format_exc())
                if hasattr(exc,'snapshot_difference'):
                    report['snapshot_difference']=exc.snapshot_difference
                traceback.print_exc(file=stderr)
                raise
            finally:
                report['runner_imported']='exposedpath.runner' in sys.modules
                # On persistence failure do not mask an already active original exception.
                original_exception=sys.exc_info()[0] is not None
                try:
                    stdout.flush(); stderr.flush(); os.fsync(stdout.fileno()); os.fsync(stderr.fileno())
                    persist('exit.json',report)
                except OSError as write_error:
                    # Last-resort diagnostics cannot replace either primary error.
                    try:
                        if sys.__stderr__ is not None:
                            print('TARGET_ENTRY_PERSIST_FAILED: '+str(write_error),file=sys.__stderr__)
                    except Exception:
                        pass
                    if not original_exception: raise


def main():
    if sys.argv[1:2]==['model-run']:
        return model_entry()
    if sys.argv[1:2]==['probe']:
        import argparse
        p=argparse.ArgumentParser(); p.add_argument('command'); p.add_argument('--nonce',required=True); p.add_argument('--site-root',required=True)
        a=p.parse_args(); print(json.dumps(dict(pid=os.getpid(),parent_pid=os.getppid(),nonce=a.nonce,snapshot=snapshot(a.site_root)))); return 0
    from .gate8_qualification import main as qualification
    return qualification(sys.argv[1:])
