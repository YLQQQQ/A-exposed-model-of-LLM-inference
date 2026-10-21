"""Future reviewed single-session event probe. No execution through Stage A."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import sys


def require(ok,reason):
    if not ok:raise ValueError('CUPTI_EVENT_PROBE_'+reason)


def event_operations(runtime,native_stream,session,session_id,*,evidence_path=None):
    signatures={'cudaEventCreateWithFlags':[ctypes.POINTER(ctypes.c_void_p),ctypes.c_uint],
        'cudaEventRecord':[ctypes.c_void_p,ctypes.c_void_p],'cudaEventSynchronize':[ctypes.c_void_p],
        'cudaStreamSynchronize':[ctypes.c_void_p],'cudaEventDestroy':[ctypes.c_void_p]}
    for name,args in signatures.items():
        fn=getattr(runtime,name);fn.argtypes=args;fn.restype=ctypes.c_int
    rows=[];event=ctypes.c_void_p()
    def call(operation,name,args,mark=True):
        if mark:session.mark(1,'EVENT-PROBE:'+session_id+':'+operation)
        try:code=getattr(runtime,name)(*args)
        finally:
            if mark:session.mark(2,'')
        rows.append(dict(operation=operation,return_code=code))
        require(type(code) is int and code==0,'CUDA_CALL:'+operation+':'+str(code))
    kernel=ctypes.WinDLL('kernel32',winmode=0x800)
    kernel.GetCurrentThreadId.restype=ctypes.c_uint32
    facts=dict(schema_version='cupti-event-probe-side/0.1.0',session_id=session_id,pid=os.getpid(),
        tid=int(kernel.GetCurrentThreadId()),native_event=None,native_stream=native_stream,calls=rows)
    try:
        # A single empty nonblocking stream event: presence/link, not wait length.
        call('create','cudaEventCreateWithFlags',[ctypes.byref(event),2],False)
        call('record','cudaEventRecord',[event,ctypes.c_void_p(native_stream)])
        call('event_sync','cudaEventSynchronize',[event])
        call('stream_sync','cudaStreamSynchronize',[ctypes.c_void_p(native_stream)])
        call('destroy','cudaEventDestroy',[event],False)
        return facts
    finally:
        facts['native_event']=event.value
        if evidence_path is not None:
            with Path(evidence_path).open('x',encoding='utf8') as f:json.dump(facts,f,indent=2)


def run(config_path,output,*,enabled=False):
    require(enabled is True,'EXPLICIT_REVIEWED_EVENT_REQUIRED')
    c=json.loads(Path(config_path).read_text(encoding='utf8'))
    require(c.get('schema_version')=='cupti-event-probe/0.1.0' and c.get('role')=='Engineering' and
        c.get('budget')==dict(processes=1,sessions=1,models=0,nsight_profiles=0,hard_seconds=120),'CONTRACT')
    require(sys.flags.isolated and sys.flags.no_site and list(sys.version_info[:3])==[3,11,16] and
        Path(sys.executable).resolve()==Path(c['target_python']).resolve(),'PYTHON')
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='3' and os.environ.get('CUDA_DEVICE_ORDER')=='PCI_BUS_ID','MASK')
    require(c.get('context_policy')=='PYTORCH_EMPTY64_ONE_STREAM_DRAIN_BEFORE_SESSION','CONTEXT')
    from exposedpath.cupti_timeline import CaptureSession,ACTIVITY_POLICY_VERSION,sha
    require(c['session'].get('activity_policy_version')==ACTIVITY_POLICY_VERSION and
        c['session']['session_id']==c['session_id'],'POLICY')
    out=Path(output).resolve();require(not out.exists(),'NO_OVERWRITE_RESUME_RETRY');out.mkdir(parents=True)
    error=None;status='BLOCKED'
    try:
        from scripts.cupti_startup_probe import prepare_context
        facts,keepalive=prepare_context(c)
        with (out/'context.json').open('x',encoding='utf8') as f:json.dump(facts,f,indent=2)
        runtime=ctypes.WinDLL(c['runtime']['path'],winmode=0x1100)
        with CaptureSession(c['session'],out/'timeline',allow_target_capture=True) as session:
            event_operations(runtime,int(keepalive[1].cuda_stream),session,c['session_id'],evidence_path=out/'side.json')
        from analysis.cupti_event_probe import analyze_files
        analyze_files(out/'timeline/capture.json',out/'side.json',out/'review')
        status='EVENT_LINK_COMPLETE_PENDING_REVIEW'
    except BaseException as exc:error=type(exc).__name__+':'+str(exc)
    paths=[p for p in out.rglob('*') if p.is_file()]
    r=dict(schema_version='cupti-event-probe-result/0.1.0',status=status,error=error,pid=os.getpid(),
        config_sha256=sha(config_path),files={p.relative_to(out).as_posix():sha(p) for p in paths},
        COE_admission='NOT_ASSESSED',original_768_failure_resolved=False,original_1024_repaired=False,automatic_retry=False)
    with (out/'result.json').open('x',encoding='utf8') as f:json.dump(r,f,indent=2)
    return 2 if error else 0


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',required=True);p.add_argument('--output',required=True)
    p.add_argument('--run-reviewed-event',action='store_true');a=p.parse_args()
    return run(a.config,a.output,enabled=a.run_reviewed_event)
if __name__=='__main__':raise SystemExit(main())
