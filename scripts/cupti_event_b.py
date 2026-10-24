"""Reviewed API22 Stage A -> one event-link probe. No deployment or build."""
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
NATIVE_COMMIT='6c744bf52daff3fc54571e264a0c34e3207aa1df'
POLICY='cupti-api22-activity-policy/0.2.0'
FORBIDDEN=('CUDA_INJECTION64_PATH','NVTX_INJECTION64_PATH','NV_COMPUTE_PROFILER_INJECTION_PATH')


def require(ok,reason):
    if not ok:raise ValueError('CUPTI_EVENT_B_'+reason)


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read(p):return json.loads(Path(p).read_text(encoding='utf8'))


def fixed_budget():
    return dict(model_process_budget=0,probe_process_budget=1,cupti_sessions=1,nsight_profiles=0,
        timeout_seconds=120,temporary_required_bytes=2*2**30,automatic_retry=False,automatic_cleanup=False)


def components(package):
    stage=runpy.run_path(str(Path(package)/'reviewed_stage.py'));return stage,stage['support']()


def checked_a(c,stage,m):
    if 'asset_compatibility' in c:
        # Explicit new control profile; the historical branch below is intact.
        source=Path(__file__).with_name('cupti_batch_once_delivery.py')
        spec=importlib.util.spec_from_file_location('_batch_current_source_control',source)
        current=importlib.util.module_from_spec(spec);spec.loader.exec_module(current)
        return current.checked_assets(c,stage,m)
    root=Path(c['a_root'])
    for name,key in [('receipt.json','reviewed_a_receipt_sha256'),('artifact_manifest.json','a_manifest_sha256'),('delivery.json','a_delivery_sha256')]:
        require(sha(root/name)==c[key],'A_HASH:'+name)
    r=read(root/'receipt.json');acfg=read(root/'delivery.json')
    require(r['schema_version']=='cupti-timeline-stage-a-receipt/0.1.2' and r['phase']=='A'
        and r['status']=='STATIC_READY_FOR_REVIEW' and r['error'] is None and r['B_authorized'] is False
        and r['execution_commit']==r['analysis_commit']==acfg['execution_commit']==acfg['analysis_commit']==NATIVE_COMMIT
        and r['startup_diagnostic_version']=='cupti-timeline-startup/0.2.0'
        and all(type(r[k]) is int and r[k]==0 for k in ('stage_a_cuda_programs_executed','model_process_budget','micro_process_budget','profile_budget')),'A_RECEIPT')
    m.verify_rows(root,read(root/'artifact_manifest.json')['files'])
    require(all(Path(c[k]).resolve()==Path(acfg[k]).resolve() for k in ('code_root','server_root','python')),'A_EXECUTION_PATHS')
    m.tree(acfg,NATIVE_COMMIT);m.verify_rows(acfg['code_root'],read(root/'source_bytes.json'))
    stage['bind_checkout_modules'](acfg)
    build=read(root/'build/build.json')
    require(build['vendor_gpu_executed'] is False and build['schema_version']=='cupti-timeline-build/0.1.0','BUILD')
    require(acfg['schema_version']=='cupti-timeline-stage-a/0.1.2' and
        c['activity_policy_version']==r['activity_policy_version']==acfg['activity_policy_version']==build['activity_policy_version']==POLICY,'BUILD_POLICY')
    clients=[f for f in build['binaries'] if f['path']=='client.dll'];require(len(clients)==1,'BUILD_CLIENT')
    expected=dict(client=dict(path=build['client'],bytes=clients[0]['bytes'],sha256=clients[0]['sha256']),
        cupti=read(root/'cupti_file.json'),runtime=read(root/'runtime_file.json'))
    for key in ('client','cupti','runtime'):
        fact=c[key];other=expected[key];p=Path(fact['path'])
        require(p.resolve()==Path(other['path']).resolve() and
            fact['sha256']==other['sha256']==sha(p) and fact['bytes']==other['bytes']==p.stat().st_size,'LIBRARY:'+key)
    return dict(acfg=acfg,a_root=root,verification=dict(native_commit=NATIVE_COMMIT,clean=True,
        a_receipt_sha256=sha(root/'receipt.json'),a_manifest_sha256=sha(root/'artifact_manifest.json'),
        source_index_sha256=sha(root/'source_bytes.json'),build_sha256=sha(root/'build/build.json'),
        activity_policy_version=POLICY,libraries={k:c[k] for k in ('client','cupti','runtime')}))


def read_probe_result(out,process,c):
    folder=Path(out)/'probe';r=read(folder/'result.json')
    require(r['schema_version']=='cupti-event-probe-result/0.1.0' and r['status']=='EVENT_LINK_COMPLETE_PENDING_REVIEW'
        and r['error'] is None and r['config_sha256']==sha(Path(out)/'probe_config.json')
        and r['COE_admission']=='NOT_ASSESSED' and r['original_768_failure_resolved'] is False
        and r['original_1024_repaired'] is False and r['automatic_retry'] is False,'PROBE_RESULT')
    required={'context.json','side.json','timeline/capture.json','timeline/receipt.json','review/review.json'}
    actual={p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}-{'result.json'}
    require(set(r['files'])==actual==required,'PROBE_COVERAGE')
    for name,digest in r['files'].items():require(sha(folder/name)==digest,'PROBE_FILE:'+name)
    raw=read(folder/'timeline/capture.json');session=read(folder/'timeline/receipt.json')
    context=read(folder/'context.json');side=read(folder/'side.json');review=read(folder/'review/review.json')
    require(raw['pid']==session['pid']==context['pid']==side['pid']==r['pid']==process['pid']
        and raw['session_id']==session['session_id']==side['session_id']==c['session_id'],'IDENTITY')
    require(raw['source']=='TARGET_CUPTI' and session['schema_version']=='cupti-timeline-session-receipt/0.1.2'
        and type(session['open_code']) is int and type(session['close_code']) is int
        and session['open_code']==session['close_code']==0 and session['model_error_type'] is None
        and session['verification_mode']=='TARGET_CUPTI_UNQUALIFIED' and session['startup_report_error'] is None
        and session['startup_failure'] is None and session['capture_sha256']==sha(folder/'timeline/capture.json')
        and session['client_sha256']==c['client']['sha256'] and session['cupti_sha256']==c['cupti']['sha256'],'SESSION')
    # The pure stdlib reader comes from the A-byte-verified checkout, not ambient imports.
    source=Path(c['code_root'])/'exposedpath/cupti_timeline.py'
    spec=importlib.util.spec_from_file_location('_verified_event_startup_reader',source)
    reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
    init=reader.validate_startup_data(raw)
    require(init and init['succeeded'] is True and init['activity_policy']==reader.activity_policy()
        and session['activity_policy']==init['activity_policy'],'POLICY')
    shut=raw['shutdown'];steps=shut['steps']
    expected=[('cuptiActivityFlushAll',None),*[('cuptiActivityDisable',k) for k in (37,9,38,2,1,10,4,5)],
        ('cuptiActivityFlushAll',None),('cuptiUnsubscribe',None),('cuptiFinalize',None)]
    require(shut['schema_version']=='cupti-timeline-shutdown/0.1.0' and shut['succeeded'] is True
        and shut['failure'] is None and type(shut['overflow']) is int and shut['overflow']==0
        and [(s['operation'],s['activity_kind']) for s in steps]==expected
        and all(s['status_domain']=='CUPTI' and s['success'] is True and type(s['status_code']) is int and s['status_code']==0 for s in steps),'SHUTDOWN')
    q=raw['quality'];require(q['closed'] is True and q['errors']==[] and
        all(type(q[k]) is int and q[k]==0 for k in ('overflow','dropped','dropped_query_errors')),'QUALITY')
    require(context['setup_drained'] is True and context['subscription_active_during_setup'] is False
        and context['model_loaded'] is False and context['runtime_sha256']==c['runtime']['sha256']
        and Path(context['runtime_path']).resolve()==Path(c['runtime']['path']).resolve()
        and context['logical_allocation_bytes']==64 and context['explicit_stream_count']==1,'CONTEXT')
    result=review['result']
    require(review['schema_version']=='cupti-event-link-review/0.1.0'
        and review['input_sha256']==[sha(folder/'timeline/capture.json'),sha(folder/'side.json')]
        and result['status']=='EVENT_LINK_COMPLETE_PENDING_REVIEW' and result['COE_admission']=='NOT_ASSESSED'
        and result['formal_eligible'] is False and result['pytorch_coverage']=='NOT_GRANTED'
        and result['event_completion_timestamp']=='NOT_AVAILABLE_IN_API22'
        and result['driver_api_duration']=='NOT_COMPUTED','REVIEW')
    return r


def run(package,*,enabled=False,reviewed=None):
    require(enabled is True,'EXPLICIT_REVIEWED_EVENT_REQUIRED');package=Path(package).resolve()
    stage,m=components(package);index=m.verify_package(package);c=read(package/'delivery.json')
    require(c['schema_version']=='cupti-event-b/0.1.0' and c['native_commit']==c['analysis_commit']==NATIVE_COMMIT
        and c['activity_policy_version']==POLICY and reviewed==c['reviewed_a_receipt_sha256']
        and c['budget']==fixed_budget(),'CONTRACT')
    require(Path(sys.executable).resolve()==Path(c['python']).resolve() and list(sys.version_info[:3])==[3,11,16],'CONTROLLER_PYTHON')
    root=Path(c['server_root']);tag=c['controller_commit'][:12]
    out=m.safe(root,'diagnostics/cupti_event_'+tag+'_once');archive=m.safe(root,'transfer/cupti_event_'+tag+'_once.zip')
    require(not out.exists() and not archive.exists(),'NO_OVERWRITE_RESUME_RETRY');out.mkdir(parents=True);archive.parent.mkdir(parents=True,exist_ok=True)
    for n in ('delivery.json','package_manifest.json','cupti_event_b.py','cupti_event_probe.py','run_cupti_event_b.ps1'):
        shutil.copyfile(package/n,out/n)
    error=None;operation_error=None;postcheck_error=None;process=None;postchecked=False;status='BLOCKED'
    try:
        ctx=checked_a(c,stage,m)
        m.write(out/'static_precheck.json',ctx['verification'])
        for src,dst in [('receipt.json','reviewed_a_receipt.json'),('source_bytes.json','reviewed_source_bytes.json')]:
            shutil.copyfile(ctx['a_root']/src,out/dst)
        resource_cfg=dict(ctx['acfg'],temporary_required_bytes=c['budget']['temporary_required_bytes'])
        m.write(out/'resources.json',stage['startup_resources'](out,archive,resource_cfg))
        require(not any(os.environ.get(k) for k in FORBIDDEN),'EXTERNAL_PROFILER_ENVIRONMENT')
        probe=dict(schema_version='cupti-event-probe/0.1.0',role='Engineering',session_id=c['session_id'],
            budget=dict(processes=1,sessions=1,models=0,nsight_profiles=0,hard_seconds=120),
            context_policy='PYTORCH_EMPTY64_ONE_STREAM_DRAIN_BEFORE_SESSION',
            **{k:c[k] for k in ('target_python','site_root','gpu_uuid','gpu_pci','runtime')},
            session=dict(client=c['client']['path'],client_sha256=c['client']['sha256'],cupti=c['cupti']['path'],
                cupti_sha256=c['cupti']['sha256'],session_id=c['session_id'],activity_policy_version=POLICY))
        m.write(out/'probe_config.json',probe)
        env=os.environ.copy();env.update(CUDA_DEVICE_ORDER='PCI_BUS_ID',CUDA_VISIBLE_DEVICES='3');env.pop('PYTHONPATH',None)
        boot=('import sys,hashlib,runpy;sys.dont_write_bytecode=True;p=sys.argv.pop(1);h=sys.argv.pop(1);'
            'assert hashlib.sha256(open(p,"rb").read()).hexdigest()==h;'
            'sys.path[:0]=sys.argv[1:3];del sys.argv[1:3];runpy.run_path(p,run_name="__main__")')
        script=package/'cupti_event_probe.py'
        argv=[c['target_python'],'-I','-S','-X','utf8','-c',boot,str(script),sha(script),c['code_root'],c['site_root'],
            '--config',str(out/'probe_config.json'),'--output',str(out/'probe'),'--run-reviewed-event']
        m.write(out/'execution_plan.json',dict(argv=argv,budget=c['budget'],role='Engineering',
            operations=['event_record','event_synchronize','stream_synchronize'],no_llm=True))
        try:
            process=m.command(argv,out,out/'one_event',env=env,timeout=120)
            require(process['status']=='EXITED' and process['exit_code']==0 and process['timed_out'] is False,'PROBE_EXIT')
            read_probe_result(out,process,c)
        except BaseException as exc:
            operation_error=type(exc).__name__+':'+str(exc);raise
        finally:
            if process is None and (out/'one_event.process.json').is_file():process=read(out/'one_event.process.json')
            try:
                after=checked_a(c,stage,m);postchecked=True
                m.write(out/'static_postcheck.json',after['verification'])
            except BaseException as exc:
                postcheck_error=type(exc).__name__+':'+str(exc);raise
        status='EVENT_LINK_COMPLETE_STOP_FOR_REVIEW'
    except BaseException as exc:error=type(exc).__name__+':'+str(exc)
    m.write(out/'receipt.json',dict(schema_version='cupti-event-b-receipt/0.1.0',status=status,error=error,
        controller_commit=c['controller_commit'],native_commit=NATIVE_COMMIT,analysis_commit=NATIVE_COMMIT,
        reviewed_a_receipt_sha256=reviewed,package_index_sha256=index,process=process,
        operation_error=operation_error,postcheck_error=postcheck_error,
        post_execution_static_rechecked=postchecked,role='Engineering',budget=c['budget'],
        original_768_failure_resolved=False,original_1024_repaired=False,COE_admission='NOT_ASSESSED',
        formal_eligible=False,historical_ylq_total_bytes=None,long_term_target_exclusive_bytes=50000000000))
    try:print(json.dumps(m.pack(out,archive)),flush=True)
    except BaseException as exc:print('PACK_REFUSED_PRESERVE_SCENE:'+str(exc),flush=True);return 2
    if error:print('STOP:'+error,flush=True);return 2
    return 0


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--package',required=True)
    p.add_argument('--reviewed-a-receipt-sha256',required=True);p.add_argument('--run-reviewed-event',action='store_true')
    a=p.parse_args(argv);return run(a.package,enabled=a.run_reviewed_event,reviewed=a.reviewed_a_receipt_sha256)
if __name__=='__main__':raise SystemExit(main())
