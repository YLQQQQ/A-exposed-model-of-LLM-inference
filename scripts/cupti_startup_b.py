"""Reviewed diagnostic DLL -> one no-model context startup attempt. No deployment."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import runpy
import shutil
import sys
sys.dont_write_bytecode=True
NATIVE_COMMIT='ddc7abc8a1bf09b40fa868bf1a0c319f3977f80a'
FORBIDDEN=('CUDA_INJECTION64_PATH','NVTX_INJECTION64_PATH','NV_COMPUTE_PROFILER_INJECTION_PATH')
def require(ok,reason):
    if not ok:raise ValueError('CUPTI_STARTUP_B_'+reason)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def fixed_budget():
    return dict(model_process_budget=0,probe_process_budget=1,cupti_sessions=1,nsight_profiles=0,
        timeout_seconds=120,temporary_required_bytes=2*2**30,automatic_retry=False,automatic_cleanup=False)
def components(package):
    stage=runpy.run_path(str(Path(package)/'reviewed_stage.py'));return stage,stage['support']()

def checked_a(c,stage,m):
    root=Path(c['a_root'])
    for name,key in [('receipt.json','reviewed_a_receipt_sha256'),('artifact_manifest.json','a_manifest_sha256'),('delivery.json','a_delivery_sha256')]:
        require(sha(root/name)==c[key],'A_HASH:'+name)
    r=read(root/'receipt.json');acfg=read(root/'delivery.json')
    require(r['schema_version']=='cupti-timeline-stage-a-receipt/0.1.1' and r['status']=='STATIC_READY_FOR_REVIEW'
        and r['phase']=='A' and r['error'] is None and r['B_authorized'] is False
        and r['execution_commit']==r['analysis_commit']==acfg['execution_commit']==acfg['analysis_commit']==NATIVE_COMMIT
        and r['startup_diagnostic_version']=='cupti-timeline-startup/0.1.0'
        and all(type(r[k]) is int and r[k]==0 for k in ('stage_a_cuda_programs_executed','model_process_budget','micro_process_budget','profile_budget')),'A_RECEIPT')
    m.verify_rows(root,read(root/'artifact_manifest.json')['files'])
    require(all(Path(c[k]).resolve()==Path(acfg[k]).resolve() for k in ('code_root','server_root','python')),'A_EXECUTION_PATHS')
    m.tree(acfg,NATIVE_COMMIT);m.verify_rows(acfg['code_root'],read(root/'source_bytes.json'));stage['bind_checkout_modules'](acfg)
    build=read(root/'build/build.json');require(build['vendor_gpu_executed'] is False,'BUILD')
    client=[f for f in build['binaries'] if f['path']=='client.dll'];require(len(client)==1,'BUILD_CLIENT')
    expected=dict(client=dict(path=build['client'],sha256=client[0]['sha256']),
        cupti=read(root/'cupti_file.json'),runtime=read(root/'runtime_file.json'))
    for key in ('client','cupti','runtime'):
        require(Path(c[key]['path']).resolve()==Path(expected[key]['path']).resolve() and
            c[key]['sha256']==expected[key]['sha256'] and sha(c[key]['path'])==c[key]['sha256'],'LIBRARY:'+key)
    return dict(acfg=acfg,a_root=root)

def read_probe_result(out,process,c):
    folder=Path(out)/'probe';r=read(folder/'result.json')
    require(r['schema_version']=='cupti-startup-probe-result/0.1.0' and r['status']=='STARTUP_OPEN_CLOSE_COMPLETE_PENDING_REVIEW'
        and r['error'] is None and r['pid']==process['pid'] and r['session_id']==c['session_id']
        and r['native_commit']==NATIVE_COMMIT and r['config_sha256']==sha(Path(out)/'probe_config.json')
        and r['original_model_failure_resolved'] is False and r['COE_admission']=='NOT_ASSESSED','PROBE_RESULT')
    for key,name in [('context_sha256','context.json'),('capture_sha256','timeline/capture.json'),('session_receipt_sha256','timeline/receipt.json')]:
        require(r[key]==sha(folder/name),'PROBE_FILE:'+name)
    raw=read(folder/'timeline/capture.json');session=read(folder/'timeline/receipt.json');context=read(folder/'context.json')
    require(raw['pid']==session['pid']==context['pid']==process['pid'] and raw['source']=='TARGET_CUPTI'
        and raw['session_id']==session['session_id']==c['session_id'] and session['open_code']==session['close_code']==0
        and session['verification_mode']=='TARGET_CUPTI_UNQUALIFIED' and session['model_error_type'] is None
        and session['capture_sha256']==r['capture_sha256'] and session['client_sha256']==c['client']['sha256']
        and session['cupti_sha256']==c['cupti']['sha256'],'SESSION_IDENTITY')
    # Parent runs with -I and no checkout on sys.path. Load only this already
    # A-byte-verified, stdlib-only consumer; never relax isolation globally.
    source=Path(c['code_root'])/'exposedpath/cupti_timeline.py'
    spec=importlib.util.spec_from_file_location('_verified_startup_reader',source)
    reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
    startup=reader.startup_diagnostic(folder/'timeline/capture.json')
    require(startup is not None and startup['succeeded'] is True and startup['failure'] is None
        and [s['activity_kind'] for s in startup['steps'] if s['activity_kind'] is not None]==[5,4,10,1,2,38,9,37,36],'STARTUP_STEPS')
    q=raw['quality'];require(q['closed'] is True and q['errors']==[] and q['overflow']==0 and q['dropped']==0
        and q['dropped_query_errors']==0,'CAPTURE_QUALITY')
    require(context['setup_drained'] is True and context['subscription_active_during_setup'] is False
        and context['model_loaded'] is False and context['runtime_sha256']==c['runtime']['sha256'],'CONTEXT')
    require(any(m['label']=='CUPTI_STARTUP_PROBE_CONTEXT_READY' for m in raw['markers']),'MARKER_MISSING')
    return r

def run(package,*,enabled=False,reviewed=None):
    require(enabled is True,'EXPLICIT_REVIEWED_STARTUP_REQUIRED');package=Path(package).resolve()
    # Bootstrap files were hashed by the launcher before this import.
    stage,m=components(package);index=m.verify_package(package);c=read(package/'delivery.json')
    require(c['schema_version']=='cupti-startup-b/0.1.0' and c['native_commit']==NATIVE_COMMIT and
        reviewed==c['reviewed_a_receipt_sha256'] and c['budget']==fixed_budget(),'CONTRACT')
    require(Path(sys.executable)==Path(c['python']) and list(sys.version_info[:3])==[3,11,16],'CONTROLLER_PYTHON')
    root=Path(c['server_root']);tag=c['controller_commit'][:12]
    out=m.safe(root,'diagnostics/cupti_startup_'+tag+'_once');archive=m.safe(root,'transfer/cupti_startup_'+tag+'_once.zip')
    require(not out.exists() and not archive.exists(),'NO_OVERWRITE_RESUME_RETRY');out.mkdir(parents=True);archive.parent.mkdir(parents=True,exist_ok=True)
    for n in ('delivery.json','package_manifest.json','cupti_startup_b.py','cupti_startup_probe.py','run_cupti_startup_b.ps1'):shutil.copyfile(package/n,out/n)
    error=None;process=None;postchecked=False;status='BLOCKED';ctx=None
    try:
        ctx=checked_a(c,stage,m)
        for src,dst in [('receipt.json','reviewed_a_receipt.json'),('source_bytes.json','reviewed_source_bytes.json')]:shutil.copyfile(ctx['a_root']/src,out/dst)
        resource_cfg=dict(ctx['acfg'],temporary_required_bytes=c['budget']['temporary_required_bytes'])
        m.write(out/'resources.json',stage['startup_resources'](out,archive,resource_cfg))
        require(not any(os.environ.get(k) for k in FORBIDDEN),'EXTERNAL_PROFILER_ENVIRONMENT')
        probe=dict(schema_version='cupti-startup-probe/0.1.0',role='Engineering',native_commit=NATIVE_COMMIT,
            session_id=c['session_id'],model_process_budget=0,probe_process_budget=1,cupti_sessions=1,nsight_profiles=0,
            context_policy='PYTORCH_EMPTY64_ONE_STREAM_DRAIN_BEFORE_SESSION',allocation_bytes=64,
            **{k:c[k] for k in ('target_python','site_root','gpu_uuid','gpu_pci','runtime')},
            session=dict(client=c['client']['path'],client_sha256=c['client']['sha256'],cupti=c['cupti']['path'],
                cupti_sha256=c['cupti']['sha256'],session_id=c['session_id']))
        m.write(out/'probe_config.json',probe)
        env=os.environ.copy();env.update(CUDA_DEVICE_ORDER='PCI_BUS_ID',CUDA_VISIBLE_DEVICES='3');env.pop('PYTHONPATH',None)
        boot=('import sys,hashlib,runpy;sys.dont_write_bytecode=True;p=sys.argv.pop(1);h=sys.argv.pop(1);'
            'assert hashlib.sha256(open(p,"rb").read()).hexdigest()==h;'
            'sys.path[:0]=sys.argv[1:3];del sys.argv[1:3];runpy.run_path(p,run_name="__main__")')
        script=package/'cupti_startup_probe.py'
        argv=[c['target_python'],'-I','-S','-X','utf8','-c',boot,str(script),sha(script),c['code_root'],c['site_root'],
            '--config',str(out/'probe_config.json'),'--output',str(out/'probe'),'--run-reviewed-startup']
        m.write(out/'execution_plan.json',dict(argv=argv,budget=c['budget'],role='Engineering',model_loaded=False))
        try:
            process=m.command(argv,out,out/'one_startup',env=env,timeout=120)
            require(process['status']=='EXITED' and process['exit_code']==0 and process['timed_out'] is False,'PROBE_EXIT')
            # The controller uses verified checkout modules without ambient site packages.
            read_probe_result(out,process,c)
        finally:
            if process is None and (out/'one_startup.process.json').is_file():process=read(out/'one_startup.process.json')
            checked_a(c,stage,m);postchecked=True
        status='STARTUP_DIAGNOSTIC_COMPLETE_STOP_FOR_REVIEW'
    except BaseException as exc:error=type(exc).__name__+':'+str(exc)
    m.write(out/'receipt.json',dict(schema_version='cupti-startup-b-receipt/0.1.0',status=status,error=error,
        controller_commit=c['controller_commit'],native_commit=NATIVE_COMMIT,reviewed_a_receipt_sha256=reviewed,
        package_index_sha256=index,process=process,post_execution_static_rechecked=postchecked,role='Engineering',
        budget=c['budget'],original_model_failure_resolved=False,COE_admission='NOT_ASSESSED',formal_eligible=False,
        historical_ylq_total_bytes=None))
    try:print(json.dumps(m.pack(out,archive)),flush=True)
    except BaseException as exc:print('PACK_REFUSED_PRESERVE_SCENE:'+str(exc),flush=True);return 2
    if error:print('STOP:'+error,flush=True);return 2
    return 0

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--package',required=True);p.add_argument('--reviewed-a-receipt-sha256',required=True)
    p.add_argument('--run-reviewed-startup',action='store_true');a=p.parse_args(argv)
    return run(a.package,enabled=a.run_reviewed_startup,reviewed=a.reviewed_a_receipt_sha256)
if __name__=='__main__':raise SystemExit(main())
