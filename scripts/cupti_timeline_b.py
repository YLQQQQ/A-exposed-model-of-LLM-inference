"""Reviewed Stage A -> exactly one new model capture -> same-run evidence.

This controller is shipped beside, and does not modify, the verified checkout.
No new CUDA compilation, Nsight, fallback input or retry is available.
"""
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
NATIVE_COMMIT='7fa36efb340fe59a3138eb6132e162d6b0cbfc41'


def require(ok,reason):
    if not ok:raise ValueError('CUPTI_TIMELINE_B_'+reason)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def read(p):return json.loads(Path(p).read_text(encoding='utf8'))


def fixed_budget():
    return dict(model_process_budget=1,cupti_sessions=1,nsight_profiles=0,micro_process_budget=0,timeout_seconds=300,
        analysis_timeout_seconds=180,temporary_required_bytes=12*2**30,automatic_retry=False,automatic_cleanup=False)


def components(package):
    stage=runpy.run_path(str(Path(package)/'reviewed_stage.py'))
    return stage,stage['support']()


def checked_a(c,stage,m):
    root=Path(c['a_root'])
    require(sha(root/'receipt.json')==c['reviewed_a_receipt_sha256'],'A_RECEIPT_HASH')
    require(sha(root/'artifact_manifest.json')==c['a_manifest_sha256'],'A_MANIFEST_HASH')
    require(sha(root/'delivery.json')==c['a_delivery_sha256'],'A_DELIVERY_HASH')
    r=read(root/'receipt.json')
    require(r.get('schema_version')=='cupti-timeline-stage-a-receipt/0.1.0' and r.get('phase')=='A' and
        r.get('status')=='STATIC_READY_FOR_REVIEW' and r.get('error') is None and
        r.get('execution_commit')==r.get('analysis_commit')==NATIVE_COMMIT and r.get('B_authorized') is False and
        all(r.get(k)==0 for k in ('stage_a_cuda_programs_executed','model_process_budget','micro_process_budget','profile_budget')),'A_RECEIPT')
    m.verify_rows(root,read(root/'artifact_manifest.json')['files'])
    acfg=read(root/'delivery.json');require(acfg['execution_commit']==acfg['analysis_commit']==NATIVE_COMMIT,'A_COMMIT')
    m.tree(acfg,NATIVE_COMMIT);m.verify_rows(acfg['code_root'],read(root/'source_bytes.json'))
    stage['bind_checkout_modules'](acfg)
    require(read(root/'build/build.json')['vendor_gpu_executed'] is False,'BUILD')
    for name in ('client','cupti','runtime'):
        fact=c[name];p=Path(fact['path'])
        require(p.is_file() and sha(p)==fact['sha256'],'LIBRARY_CHANGED:'+name)
    return dict(acfg=acfg,a_root=root)


def with_postcheck(operation,check):
    try:return operation()
    finally:check()


def analyze_model(folder,process,cfg):
    """Bound by the controller and executed in a CPU-only isolated child."""
    folder=Path(folder);p=folder/'model_result.json'
    require(p.is_file(),'MODEL_RESULT')
    result=read(p)
    require(result.get('schema_version')=='cupti-timeline-model-result/0.1.0' and
        result.get('status')=='MODEL_CAPTURE_COMPLETE_PENDING_ANALYSIS' and result.get('role')=='Engineering'
        and result.get('pid')==process['pid'] and result.get('config_sha256')==sha(cfg['model_config']),'MODEL_RESULT')
    paths={'capture_sha256':'timeline/capture.json','session_receipt_sha256':'timeline/receipt.json',
        'producer_receipt_sha256':'producer/producer_receipt.json','token_sha256':'tokens.json',
        'scope_producers_sha256':'scope_producers.json','setup_sha256':'setup.json','warmup_sha256':'warmup_completed.json'}
    for key,name in paths.items():require(result[key]==sha(folder/name),'MODEL_FILE:'+name)
    session=read(folder/'timeline/receipt.json');raw=read(folder/'timeline/capture.json')
    require(session['pid']==raw['pid']==process['pid'] and session['open_code']==session['close_code']==0 and
        session['model_error_type'] is None and session['verification_mode']=='TARGET_CUPTI_UNQUALIFIED' and
        session['capture_sha256']==sha(folder/'timeline/capture.json') and
        session['client_sha256']==cfg['client']['sha256'] and session['cupti_sha256']==cfg['cupti']['sha256'] and
        raw['source']=='TARGET_CUPTI' and raw['session_id']==cfg['session_id'],'SESSION_IDENTITY')
    receipt=read(folder/'producer/producer_receipt.json')
    require(receipt['status']=='COMPLETE','PRODUCER_FAILED')
    for value in receipt['files'].values():
        source=folder/'producer'/value['filename']
        require(sha(source)==value['sha256'] and source.stat().st_size==value['size_bytes'],'PRODUCER_FILE')
    ledger=read(folder/'producer/pass_identity.json')
    require(ledger['pid']==process['pid'] and ledger['run_id']==cfg['run_id'] and ledger['runner_git_commit']==NATIVE_COMMIT
        and ledger['runner_git_dirty'] is False and ledger['prompt_sha256']==cfg['prompt_sha256'] and
        ledger['wmpc_manifest_sha256']==sha(cfg['model_config']) and len(ledger['requests'])==1 and
        ledger['requests'][0]['outcome']=='COMPLETE','PRODUCER_IDENTITY')
    from exposedpath.gate8_identity import validate_pass_identity
    validate_pass_identity(ledger)
    tokens=read(folder/'tokens.json')
    require(tokens['token_ids']==cfg['expected_token_ids'] and tokens['identity']==ledger['requests'][0]['identity'] and
        tokens['pid']==process['pid'],'TOKEN_REFERENCE')
    setup=read(folder/'setup.json');warmup=read(folder/'warmup_completed.json')
    require(setup['input_sha256']==cfg['prompt_sha256'] and setup['input_shape']==[1,768] and
        setup['runner_source_sha256']==ledger['runner_source_sha256'] and setup['python_version']==[3,11,16] and
        setup['loaded_backend']=='sdpa' and setup['torch_version']=='2.6.0+cu124' and
        warmup['completed_count']==3 and warmup['subscription_active'] is False,'SETUP_WARMUP_BINDING')
    # Rebuild labels from hashed producer sidecars, rather than trusting scope JSON.
    spec=importlib.util.spec_from_file_location('_bound_model_source',cfg['model_script'])
    model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
    expected=model.producer_scopes(cfg['session_id'],read(folder/'producer/host_boundaries.json'),
        read(folder/'producer/drain_ledger.json'),tokens)
    require(read(folder/'scope_producers.json')==expected,'SCOPE_PRODUCER_BINDING')
    from analysis.cupti_timeline import select_scope,analyze_files
    answers=[];errors=[]
    for i,p in enumerate(expected):
        try:
            scope=select_scope(raw,p);scope_path=folder/f'scope_token{i}.json'
            with scope_path.open('x',encoding='utf8') as f:json.dump(scope,f,indent=2)
            answers.append(analyze_files(folder/'timeline/capture.json',scope_path,folder/f'derived_token{i}'))
        except Exception as exc:errors.append(dict(token_index=i,error=type(exc).__name__+':'+str(exc)))
    report=dict(schema_version='cupti-timeline-model-review/0.1.0',status='BOTH_TOKENS_EVIDENCE_COMPLETE_PENDING_REVIEW' if not errors else 'BLOCKED',
        errors=errors,token_results=answers,capture_sha256=sha(folder/'timeline/capture.json'),
        provider_qualification='NOT_GRANTED',production_A_B_changed=False,old_instance_repair=False,
        pure_host_blocking=None,formal_eligible=False)
    with (folder/'analysis_report.json').open('x',encoding='utf8') as f:json.dump(report,f,indent=2)
    require(not errors,'SAME_RUN_ANALYSIS:'+json.dumps(errors))
    return report


def run(package,*,enabled=False,reviewed=None):
    require(enabled is True,'EXPLICIT_REVIEWED_MODEL_REQUIRED')
    package=Path(package).resolve()
    # The previously reviewed package validator is bundled byte-for-byte.
    from pathlib import PurePosixPath
    index=read(package/'package_manifest.json');seen=set()
    for r in index['files']:
        name=r['path'];p=PurePosixPath(name)
        require(not p.is_absolute() and len(p.parts)==1 and name not in ('.','..') and ':' not in name and '\\' not in name
            and name.casefold() not in seen,'PACKAGE_PATH');seen.add(name.casefold())
        q=package/name
        require(q.is_file() and not q.is_symlink() and not getattr(q.lstat(),'st_file_attributes',0)&0x400 and
            q.stat().st_size==r['bytes'] and sha(q)==r['sha256'],'PACKAGE_FILE:'+name)
    require({p.name for p in package.iterdir()}=={r['path'] for r in index['files']}|{'package_manifest.json'},'PACKAGE_COVERAGE')
    c=read(package/'delivery.json')
    require(reviewed==c['reviewed_a_receipt_sha256'] and c['schema_version']=='cupti-timeline-stage-b/0.1.0'
        and c['native_commit']==c['analysis_commit']==NATIVE_COMMIT and c['budget']==fixed_budget(),'B_CONTRACT')
    require(Path(sys.executable)==Path(c['python']) and list(sys.version_info[:3])==[3,11,16],'CONTROLLER_PYTHON')
    stage,m=components(package);root=Path(c['server_root']);tag=c['controller_commit'][:12]
    out=m.safe(root,'evidence/cupti_timeline/model768_'+tag+'_once')
    archive=m.safe(root,'transfer/cupti_timeline_'+tag+'_model768_once.zip')
    require(not out.exists() and not archive.exists(),'NO_OVERWRITE_RESUME_RETRY')
    out.mkdir(parents=True,exist_ok=False);archive.parent.mkdir(parents=True,exist_ok=True)
    for n in ('delivery.json','package_manifest.json','cupti_timeline_b.py','cupti_timeline_model.py','run_cupti_timeline_b.ps1'):
        shutil.copyfile(package/n,out/n)
    error=None;process=None;status='BLOCKED';postchecked=False
    try:
        ctx=checked_a(c,stage,m)
        for src,dst in [('receipt.json','reviewed_a_receipt.json'),('artifact_manifest.json','reviewed_a_manifest.json'),
            ('source_bytes.json','reviewed_source_bytes.json'),('build/build.json','reviewed_build.json')]:
            shutil.copyfile(ctx['a_root']/src,out/dst)
        m.write(out/'resources.json',stage['startup_resources'](out,archive,ctx['acfg']))
        forbidden=('CUDA_INJECTION64_PATH','NVTX_INJECTION64_PATH','NV_COMPUTE_PROFILER_INJECTION_PATH')
        require(not any(os.environ.get(k) for k in forbidden),'EXTERNAL_PROFILER_ENVIRONMENT')
        model_cfg=dict(c['model_contract'],**{k:c[k] for k in ('model','inventory_sha256','prompt_sha256','gpu_uuid','gpu_pci','target_python','site_root')},
            inventory=str(package/'model_sha256.csv'),prompt=str(package/'input_768.json'),
            session=dict(client=c['client']['path'],client_sha256=c['client']['sha256'],
                cupti=c['cupti']['path'],cupti_sha256=c['cupti']['sha256'],session_id=c['session_id']))
        m.write(out/'model_config.json',model_cfg)
        env=os.environ.copy();env.update(CUDA_DEVICE_ORDER='PCI_BUS_ID',CUDA_VISIBLE_DEVICES='3')
        env.pop('PYTHONPATH',None)
        # -I/-S excludes ambient packages; explicitly bind the verified checkout
        # and target site, and verify the packaged model script in the child.
        boot=('import sys,hashlib,runpy;sys.dont_write_bytecode=True;'
            'p=sys.argv.pop(1);h=sys.argv.pop(1);'
            'assert hashlib.sha256(open(p,"rb").read()).hexdigest()==h;'
            'sys.path[:0]=sys.argv[1:3];del sys.argv[1:3];runpy.run_path(p,run_name="__main__")')
        model_script=package/'cupti_timeline_model.py'
        argv=[c['target_python'],'-I','-S','-X','utf8','-c',boot,str(model_script),sha(model_script),
            c['code_root'],c['site_root'],'--config',str(out/'model_config.json'),'--output',str(out/'model'),
            '--run-reviewed-model']
        m.write(out/'execution_plan.json',dict(argv=argv,budget=c['budget'],role='Engineering',input_tokens=768,
            output_tokens=2,batch_size=1,warmup_count=3,automatic_retry=False))
        try:
            process=m.command(argv,out,out/'one_model',env=env,timeout=300)
            require(process['status']=='EXITED' and process['exit_code']==0 and not process['timed_out'],'MODEL_EXIT')
            analysis_cfg=dict(c,model_config=str(out/'model_config.json'),model_script=str(model_script))
            m.write(out/'analysis_config.json',analysis_cfg)
            # Same capture, separate CPU-only consumer. No model is imported here.
            analyse_boot=('import sys,runpy,json;sys.dont_write_bytecode=True;'
                'p=sys.argv.pop(1);sys.path[:0]=sys.argv[1:3];del sys.argv[1:3];'
                'm=runpy.run_path(p);m["analyze_model"](sys.argv[1],json.loads(sys.argv[2]),json.load(open(sys.argv[3])))')
            m.command([c['python'],'-I','-S','-X','utf8','-c',analyse_boot,str(package/'cupti_timeline_b.py'),
                c['code_root'],c['site_root'],str(out/'model'),json.dumps(process),str(out/'analysis_config.json')],
                out,out/'same_run_analysis',env=env,timeout=180)
        finally:
            checked_a(c,stage,m);postchecked=True
        status='MODEL768_BOTH_TOKENS_COMPLETE_STOP_FOR_REVIEW'
    except BaseException as exc:error=type(exc).__name__+':'+str(exc)
    m.write(out/'receipt.json',dict(schema_version='cupti-timeline-stage-b-receipt/0.1.0',phase='B',status=status,error=error,
        controller_commit=c['controller_commit'],native_commit=NATIVE_COMMIT,analysis_commit=NATIVE_COMMIT,
        reviewed_a_receipt_sha256=reviewed,package_index_sha256=sha(package/'package_manifest.json'),process=process,
        post_execution_static_rechecked=postchecked,role='Engineering',budget=c['budget'],
        PyTorch_coverage='PENDING_REVIEW' if not error else 'NOT_QUALIFIED',COE_admission='NOT_ASSESSED',
        old_instance_repair=False,formal_eligible=False,historical_ylq_total_bytes=None,
        long_term_target_exclusive_bytes=50000000000))
    try:print(json.dumps(m.pack(out,archive)),flush=True)
    except BaseException as exc:print('PACK_REFUSED_PRESERVE_SCENE:'+str(exc),flush=True);return 2
    if error:print('STOP:'+error,flush=True);return 2
    return 0


def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--package',required=True);p.add_argument('--reviewed-a-receipt-sha256',required=True)
    p.add_argument('--run-reviewed-model',action='store_true');a=p.parse_args(argv)
    return run(a.package,enabled=a.run_reviewed_model,reviewed=a.reviewed_a_receipt_sha256)


if __name__=='__main__':raise SystemExit(main())
