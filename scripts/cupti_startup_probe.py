"""One initialized-context CUPTI open/close probe; no LLM or inference runner."""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import sys

NATIVE_COMMIT='ddc7abc8a1bf09b40fa868bf1a0c319f3977f80a'
def require(ok,reason):
    if not ok:raise ValueError('CUPTI_STARTUP_PROBE_'+reason)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def write(p,v):
    with Path(p).open('x',encoding='utf8') as f:json.dump(v,f,indent=2)

def validate_contract(c):
    expected=dict(schema_version='cupti-startup-probe/0.1.0',role='Engineering',native_commit=NATIVE_COMMIT,
        model_process_budget=0,probe_process_budget=1,cupti_sessions=1,nsight_profiles=0,
        context_policy='PYTORCH_EMPTY64_ONE_STREAM_DRAIN_BEFORE_SESSION',allocation_bytes=64)
    require(all(type(c.get(k)) is type(v) and c[k]==v for k,v in expected.items()),'CONTRACT')
    require(isinstance(c.get('session_id'),str) and re.fullmatch('[A-Za-z0-9_-]{1,60}',c['session_id']),'SESSION_ID')

def prepare_context(c):
    # Import only in the explicit child after parent A/hash/resource validation.
    import torch
    require(str(torch.__version__)=='2.6.0+cu124' and torch.version.cuda=='12.4','TORCH_VERSION')
    require(Path(torch.__file__).resolve().is_relative_to(Path(c['site_root']).resolve()),'TORCH_ORIGIN')
    torch.cuda.set_device(0)
    from exposedpath.platform_adapter import cuda_identity_native
    from exposedpath_v141.gate8_adapter import normalized_uuid,normalized_pci
    device=cuda_identity_native(torch.cuda)
    require(normalized_uuid(device['gpu_uuid'])==normalized_uuid(c['gpu_uuid']) and
        normalized_pci(device['pci_bus_id'])==normalized_pci(c['gpu_pci']),'DEVICE_IDENTITY')
    # Real module path, rather than merely hashing an un-loaded runtime copy.
    kernel=ctypes.WinDLL('kernel32',winmode=0x800)
    kernel.GetModuleHandleW.argtypes=[ctypes.c_wchar_p];kernel.GetModuleHandleW.restype=ctypes.c_void_p
    kernel.GetModuleFileNameW.argtypes=[ctypes.c_void_p,ctypes.c_wchar_p,ctypes.c_uint32]
    kernel.GetModuleFileNameW.restype=ctypes.c_uint32
    handle=kernel.GetModuleHandleW('cudart64_12.dll');require(bool(handle),'RUNTIME_NOT_LOADED')
    path=ctypes.create_unicode_buffer(32768);n=kernel.GetModuleFileNameW(handle,path,len(path))
    require(0<n<len(path) and Path(path.value).resolve()==Path(c['runtime']['path']).resolve()
        and sha(path.value)==c['runtime']['sha256'],'LOADED_RUNTIME')
    allocation=torch.empty(64,dtype=torch.uint8,device='cuda:0')
    stream=torch.cuda.Stream(device=0)
    torch.cuda.synchronize(0)  # Probe setup only, before CUPTI; no model completion change.
    return dict(schema_version='cupti-startup-context/0.1.0',pid=os.getpid(),device=device,
        torch_version=str(torch.__version__),torch_origin=str(Path(torch.__file__).resolve()),
        runtime_path=path.value,runtime_sha256=sha(path.value),logical_allocation_bytes=64,
        explicit_stream_count=1,setup_drained=True,subscription_active_during_setup=False,
        policy=c['context_policy'],model_loaded=False), (allocation,stream)

def exercise(c,out,prepare,session_type):
    """Ordered file chain; injected prepare/session are CPU test providers only."""
    out=Path(out);session=None;keepalive=None;error=None;status='BLOCKED'
    try:
        facts,keepalive=prepare(c);write(out/'context.json',facts)
        session=session_type(c['session'],out/'timeline',allow_target_capture=True)
        with session:session.mark(0,'CUPTI_STARTUP_PROBE_CONTEXT_READY')
        require(session.startup is not None and session.startup['succeeded'] is True and
            session.startup_report_error is None,'DIAGNOSTIC_MISSING_OR_FAILED')
        status='STARTUP_OPEN_CLOSE_COMPLETE_PENDING_REVIEW'
    except BaseException as exc:error=type(exc).__name__+':'+str(exc)
    # Keep the tensor/stream alive through close, including failed initialization.
    del keepalive
    raw=out/'timeline/capture.json';receipt=out/'timeline/receipt.json'
    result=dict(schema_version='cupti-startup-probe-result/0.1.0',status=status,error=error,pid=os.getpid(),
        session_id=c['session_id'],role='Engineering',native_commit=NATIVE_COMMIT,
        startup_failure=session.startup['failure'] if session and session.startup else None,
        startup_report_error=session.startup_report_error if session else None,
        context_sha256=sha(out/'context.json') if (out/'context.json').is_file() else None,
        capture_sha256=sha(raw) if raw.is_file() else None,session_receipt_sha256=sha(receipt) if receipt.is_file() else None,
        original_model_failure_resolved=False,COE_admission='NOT_ASSESSED',formal_eligible=False)
    return result

def run(config_path,out,*,enabled=False):
    require(enabled is True,'EXPLICIT_REVIEWED_STARTUP_REQUIRED')
    c=read(config_path);validate_contract(c)
    require(sys.flags.isolated and sys.flags.no_site and list(sys.version_info[:3])==[3,11,16]
        and Path(sys.executable).resolve()==Path(c['target_python']).resolve(),'TARGET_PYTHON')
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='3' and os.environ.get('CUDA_DEVICE_ORDER')=='PCI_BUS_ID','MASK')
    out=Path(out).resolve();require(not out.exists(),'NO_OVERWRITE_RESUME_RETRY');out.mkdir(parents=True,exist_ok=False)
    from exposedpath.cupti_timeline import CaptureSession
    result=exercise(c,out,prepare_context,CaptureSession);result['config_sha256']=sha(config_path)
    write(out/'result.json',result)
    if result['error']:print('STOP:'+result['error'],flush=True);return 2
    print(result['status'],flush=True);return 0

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',required=True);p.add_argument('--output',required=True)
    p.add_argument('--run-reviewed-startup',action='store_true');a=p.parse_args(argv)
    return run(a.config,a.output,enabled=a.run_reviewed_startup)
if __name__=='__main__':raise SystemExit(main())
