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
POLICY_NATIVE_COMMIT='6c744bf52daff3fc54571e264a0c34e3207aa1df'
POLICY='cupti-api22-activity-policy/0.2.0'


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


def policy_profile(c):return c.get('schema_version') in ('cupti-timeline-stage-b/0.1.1','cupti-timeline-stage-b/0.2.0')


def finite_profile(c):return c.get('schema_version')=='cupti-timeline-stage-b/0.2.0'


def consumer_policy(c):
    expected=dict(consumer_version='submit-effect-bridge/0.3.0',
        timing_policy='cupti-api22-distinct-api-callback-boundaries/0.2.0',
        driver_query_policy='cupti-api22-driver-queries/0.1.0',runtime_query_policy='cupti-api22-runtime-queries/0.1.0')
    require(all(c.get(k)==v for k,v in expected.items()),'CONSUMER_POLICY')
    import re
    require(re.fullmatch('[0-9a-f]{40}',c.get('analysis_commit','')) is not None,'ANALYSIS_COMMIT')
    return {k:c[k] for k in ('timing_policy','driver_query_policy')}


def event_control():
    source=Path(__file__).with_name('cupti_event_b.py')
    spec=importlib.util.spec_from_file_location('_reviewed_model_event_control',source)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def checked_event(c,m):
    root=Path(c['event_root'])
    require(sha(root/'receipt.json')==c['reviewed_event_receipt_sha256'] and
        sha(root/'artifact_manifest.json')==c['event_manifest_sha256'],'EVENT_REFERENCE_HASH')
    m.verify_rows(root,read(root/'artifact_manifest.json')['files'])
    r=read(root/'receipt.json');ec=read(root/'delivery.json');proc=read(root/'one_event.process.json')
    require(r['schema_version']=='cupti-event-b-receipt/0.1.0' and r['role']=='Engineering'
        and r['status']=='EVENT_LINK_COMPLETE_STOP_FOR_REVIEW' and r['error'] is None
        and r['operation_error'] is None and r['postcheck_error'] is None and r['post_execution_static_rechecked'] is True
        and r['native_commit']==r['analysis_commit']==ec['native_commit']==POLICY_NATIVE_COMMIT
        and r['reviewed_a_receipt_sha256']==c['reviewed_a_receipt_sha256'] and r['process']==proc
        and proc['status']=='EXITED' and proc['exit_code']==0 and proc['timed_out'] is False,'EVENT_REFERENCE')
    for name in ('static_precheck.json','static_postcheck.json'):
        p=read(root/name)
        require(p['native_commit']==POLICY_NATIVE_COMMIT and p['clean'] is True and
            p['a_receipt_sha256']==c['reviewed_a_receipt_sha256'] and p['activity_policy_version']==POLICY
            and all(p['libraries'][k]==c[k]==ec[k] for k in ('client','cupti','runtime')),'EVENT_A_LIBRARY_BINDING')
    review=read(root/'probe/review/review.json');result=review['result']
    require(review['schema_version']=='cupti-event-link-review/0.1.0' and
        review['input_sha256']==[sha(root/'probe/timeline/capture.json'),sha(root/'probe/side.json')]
        and result['status']=='EVENT_LINK_COMPLETE_PENDING_REVIEW' and result['COE_admission']=='NOT_ASSESSED'
        and result['formal_eligible'] is False,'EVENT_REVIEW')
    return result


def checked_a(c,stage,m):
    if policy_profile(c):
        ctx=event_control().checked_a(c,stage,m)
        ctx['verification']['event_reference']=checked_event(c,m)
        return ctx
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


def validate_model_files(folder,process,cfg):
    """Read-only identity/producer verification, shared by live/offline readers.

    Offline callers must authenticate the original archive/config before
    resolving its file references locally. Relocation is not permission to
    replace a source hash or to alter any execution contract field.
    """
    folder=Path(folder);p=folder/'model_result.json'
    require(p.is_file(),'MODEL_RESULT')
    result=read(p)
    current=policy_profile(cfg);finite=finite_profile(cfg);native=POLICY_NATIVE_COMMIT if current else NATIVE_COMMIT
    require(cfg.get('schema_version') in (None,'cupti-timeline-stage-b/0.1.0','cupti-timeline-stage-b/0.1.1','cupti-timeline-stage-b/0.2.0'),'MODEL_VERSION')
    if current:
        if finite:consumer_policy(cfg)
        require(cfg['native_commit']==result.get('native_commit')==native and (finite or cfg['analysis_commit']==native)
            and result.get('control_commit')==cfg['controller_commit'] and result.get('activity_policy_version')==cfg['activity_policy_version']==POLICY
            and result.get('model_entry_sha256')==sha(cfg['model_script']),'MODEL_VERSION')
    require(result.get('schema_version')==('cupti-timeline-model-result/0.2.0' if finite else 'cupti-timeline-model-result/0.1.1' if current else 'cupti-timeline-model-result/0.1.0') and
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
    if current:
        from exposedpath.cupti_timeline import validate_startup_data,activity_policy
        init=validate_startup_data(raw)
        require(init and init['succeeded'] is True and init['activity_policy']==activity_policy()
            and session['schema_version']=='cupti-timeline-session-receipt/0.1.2'
            and session['activity_policy']==init['activity_policy'] and session['session_id']==cfg['session_id']
            and session['startup_report_error'] is None and session['startup_failure'] is None,'POLICY')
        s=raw['shutdown'];steps=s['steps']
        require(s['schema_version']=='cupti-timeline-shutdown/0.1.0' and s['succeeded'] is True and s['failure'] is None
            and s['overflow']==0 and [(v['operation'],v['activity_kind']) for v in steps]==
            [('cuptiActivityFlushAll',None),*[('cuptiActivityDisable',k) for k in (37,9,38,2,1,10,4,5)],
             ('cuptiActivityFlushAll',None),('cuptiUnsubscribe',None),('cuptiFinalize',None)]
            and all(v['status_domain']=='CUPTI' and v['success'] is True and type(v['status_code']) is int and v['status_code']==0 for v in steps),'SHUTDOWN')
    receipt=read(folder/'producer/producer_receipt.json')
    require(receipt['status']=='COMPLETE','PRODUCER_FAILED')
    for value in receipt['files'].values():
        source=folder/'producer'/value['filename']
        require(sha(source)==value['sha256'] and source.stat().st_size==value['size_bytes'],'PRODUCER_FILE')
    ledger=read(folder/'producer/pass_identity.json')
    require(ledger['pid']==process['pid'] and ledger['run_id']==cfg['run_id'] and ledger['runner_git_commit']==native
        and ledger['runner_git_dirty'] is False and ledger['prompt_sha256']==cfg['prompt_sha256'] and
        ledger['wmpc_manifest_sha256']==sha(cfg['model_config']) and len(ledger['requests'])==1 and
        ledger['requests'][0]['outcome']=='COMPLETE','PRODUCER_IDENTITY')
    from exposedpath.gate8_identity import validate_pass_identity
    validate_pass_identity(ledger)
    tokens=read(folder/'tokens.json')
    require(tokens['token_ids']==cfg['expected_token_ids'] and tokens['identity']==ledger['requests'][0]['identity'] and
        tokens['pid']==process['pid'],'TOKEN_REFERENCE')
    setup=read(folder/'setup.json');warmup=read(folder/'warmup_completed.json')
    require(setup['input_sha256']==cfg['prompt_sha256'] and setup['input_shape']==[1,1024 if finite else 768] and
        setup['runner_source_sha256']==ledger['runner_source_sha256'] and setup['python_version']==[3,11,16] and
        setup['loaded_backend']=='sdpa' and setup['torch_version']=='2.6.0+cu124' and
        warmup['completed_count']==3 and warmup['subscription_active'] is False,'SETUP_WARMUP_BINDING')
    # Rebuild labels from hashed producer sidecars, rather than trusting scope JSON.
    spec=importlib.util.spec_from_file_location('_bound_model_source',cfg['model_script'])
    model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
    if finite:
        mc=read(cfg['model_config']);model.validate_contract(mc)
        require(mc['schema_version']=='cupti-timeline-model/0.2.0' and mc['run_id']==cfg['run_id']
            and mc['control_commit']==cfg['controller_commit'] and mc['native_commit']==native
            and all(mc.get(k)==cfg[k] for k in ('consumer_version','timing_policy','driver_query_policy','runtime_query_policy')),'MODEL_VERSION')
        require(sha(mc['prompt'])==mc['prompt_sha256']==cfg['prompt_sha256'],'INPUT_HASH')
        from exposedpath.coe_input_pilot import input_identity,MIDPOINT_VERSION
        actual=input_identity(read(mc['prompt']),version=MIDPOINT_VERSION)
        require(actual['shape']==[1,1024] and actual==mc.get('input_identity')==cfg.get('input_identity')
            ==setup.get('input_identity')==tokens.get('input_identity'),'INPUT_IDENTITY')
    expected=model.producer_scopes(cfg['session_id'],read(folder/'producer/host_boundaries.json'),
        read(folder/'producer/drain_ledger.json'),tokens,**(dict(input_tokens=1024) if finite else {}))
    require(read(folder/'scope_producers.json')==expected,'SCOPE_PRODUCER_BINDING')
    return raw,expected


def analyze_model(folder,process,cfg):
    """Bound by the controller and executed in a CPU-only isolated child."""
    folder=Path(folder)
    raw,expected=validate_model_files(folder,process,cfg)
    current=policy_profile(cfg);finite=finite_profile(cfg);native=POLICY_NATIVE_COMMIT if current else NATIVE_COMMIT
    from analysis.cupti_timeline import select_scope,analyze_files
    options=consumer_policy(cfg) if finite else {}
    answers=[];errors=[];indexed={}
    for i,p in enumerate(expected):
        try:
            scope=select_scope(raw,p,**options);scope_path=folder/f'scope_token{i}.json'
            with scope_path.open('x',encoding='utf8') as f:json.dump(scope,f,indent=2)
            answer=analyze_files(folder/'timeline/capture.json',scope_path,folder/f'derived_token{i}',**options)
            answers.append(answer);indexed[i]=answer['result']
        except Exception as exc:errors.append(dict(token_index=i,error=type(exc).__name__+':'+str(exc)))
    if current:
        coverage=memset_coverage(raw,expected,indexed)
        with (folder/'memset_coverage.json').open('x',encoding='utf8') as f:json.dump(coverage,f,indent=2)
    report=dict(schema_version='cupti-timeline-model-review/0.2.0' if finite else 'cupti-timeline-model-review/0.1.1' if current else 'cupti-timeline-model-review/0.1.0',status='BOTH_TOKENS_EVIDENCE_COMPLETE_PENDING_REVIEW' if not errors else 'BLOCKED',
        errors=errors,token_results=answers,capture_sha256=sha(folder/'timeline/capture.json'),
        provider_qualification='NOT_GRANTED',production_A_B_changed=False,old_instance_repair=False,
        pure_host_blocking=None,formal_eligible=False)
    if current:report.update(controller_commit=cfg['controller_commit'],native_commit=native,S_COE_commit=native,
        model_entry_sha256=sha(cfg['model_script']),consumer_source_sha256=sha(__file__),
        memset_coverage_sha256=sha(folder/'memset_coverage.json'))
    if finite:report.update(analysis_commit=cfg['analysis_commit'],S_COE_commit=cfg['analysis_commit'],
        consumer_version=cfg['consumer_version'],timing_policy=cfg['timing_policy'],
        driver_query_policy=cfg['driver_query_policy'],runtime_query_policy=cfg['runtime_query_policy'])
    with (folder/'analysis_report.json').open('x',encoding='utf8') as f:json.dump(report,f,indent=2)
    require(not errors,'SAME_RUN_ANALYSIS:'+json.dumps(errors))
    return report


def memset_coverage(raw,producers,qualified):
    """Diagnostic only: qualification comes exclusively from the existing S/COE bridge."""
    from analysis.cupti_timeline import marker_ranges
    from exposedpath_v141.submit_effect_bridge import normal
    points=marker_ranges(raw['markers'])['points'];tokens=[]
    for i,p in enumerate(producers):
        bounds=[]
        for label in (p['request_label'],p['token_label']):
            hits=[r['time'] for r in points if r['label']==label and r['tid']==p['tid']]
            bounds.append(hits[0] if len(hits)==1 else None)
        valid_bounds=all(type(t) is int for t in bounds)
        answer=qualified.get(i);rows=[]
        for c in raw['callbacks']:
            if normal(c['name']) not in ('cudaMemsetAsync','cuMemsetD8Async'):continue
            if c['domain']=='DRIVER' and c.get('parent_id') is not None:continue
            if valid_bounds and not bounds[0]<=c['start']<bounds[1]:continue
            params=c.get('params');count=params.get('count') if isinstance(params,dict) else None
            known=type(count) is int and count>=0;status='UNRESOLVED_NOT_ADMITTED';effects=None
            if answer is not None:
                edges=[e for e in answer['effect_edges'] if e['runtime_call_id']==c['id'] or
                    (c['domain']=='DRIVER' and e['driver_call_id']==c['id'])]
                if c['id'] in answer['logical_zero_call_ids']:status='LOGICAL_ZERO_QUALIFIED';effects=[]
                elif edges:status='POSITIVE_EFFECT_QUALIFIED';effects=[e['effect_id'] for e in edges]
            rows.append(dict(call_id=c['id'],domain=c['domain'],correlation=c['correlation'],parent_id=c.get('parent_id'),
                pid=c['pid'],tid=c['tid'],context=c['context'],stream=c.get('stream'),ptsz=c.get('ptsz'),
                count=count if known else None,native_stream=params.get('native_stream') if isinstance(params,dict) else None,
                return_code=c['return_code'],parameter_class='OBSERVED_ZERO' if known and count==0 else 'OBSERVED_POSITIVE' if known else 'UNKNOWN',
                effect_ids=effects,status=status))
        tokens.append(dict(token_index=i,boundary_identified=valid_bounds,scope_admitted=answer is not None,calls=rows))
    return dict(schema_version='cupti-model-memset-coverage/0.1.0',capture_session=raw['session_id'],
        scope_authority='EXISTING_STRICT_S_COE_ONLY',membership_basis='REQUEST_PREFIX_THROUGH_EACH_TOKEN_NOT_DECODE_NEW_WORK',
        tokens=tokens,old_instance_repair=False)


def run(package,*,enabled=False,reviewed=None,reviewed_event=None):
    require(enabled is True,'EXPLICIT_REVIEWED_MODEL_REQUIRED')
    package=Path(package).resolve()
    finite=finite_profile(read(package/'delivery.json'))
    # New finite delivery permits only the explicit four-file CPU overlay.
    if finite:
        stage,m=components(package);m.verify_package(package)
    else:
        verify_legacy_package(package)
    c=read(package/'delivery.json')
    current=policy_profile(c);native=POLICY_NATIVE_COMMIT if current else NATIVE_COMMIT
    if finite:consumer_policy(c)
    require(reviewed==c['reviewed_a_receipt_sha256'] and c['schema_version'] in ('cupti-timeline-stage-b/0.1.0','cupti-timeline-stage-b/0.1.1','cupti-timeline-stage-b/0.2.0')
        and c['native_commit']==native and (finite or c['analysis_commit']==native) and c['budget']==fixed_budget(),'B_CONTRACT')
    if current:require(reviewed_event==c['reviewed_event_receipt_sha256'] and c['activity_policy_version']==POLICY,'EVENT_REVIEW_REQUIRED')
    else:require(reviewed_event is None,'LEGACY_EVENT_VERSION')
    require(Path(sys.executable)==Path(c['python']) and list(sys.version_info[:3])==[3,11,16],'CONTROLLER_PYTHON')
    if finite:require(c['controller_commit']==c['analysis_commit'] and c['model_contract']['schema_version']=='cupti-timeline-model/0.2.0','B_CONTRACT')
    if not finite:stage,m=components(package)
    root=Path(c['server_root']);tag=c['controller_commit'][:12];length=1024 if finite else 768
    out=m.safe(root,'evidence/cupti_timeline/model'+str(length)+'_'+tag+'_once')
    archive=m.safe(root,'transfer/cupti_timeline_'+tag+'_model'+str(length)+'_once.zip')
    require(not out.exists() and not archive.exists(),'NO_OVERWRITE_RESUME_RETRY')
    out.mkdir(parents=True,exist_ok=False);archive.parent.mkdir(parents=True,exist_ok=True)
    # Retain the complete small control/reference/consumer chain, never binaries.
    if finite:
        for r in read(package/'package_manifest.json')['files']:
            dest=out/'delivery'/r['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(package/r['path'],dest)
        shutil.copyfile(package/'package_manifest.json',out/'delivery/package_manifest.json')
    for n in ('delivery.json','package_manifest.json','cupti_timeline_b.py','cupti_timeline_model.py','run_cupti_timeline_b.ps1'):
        shutil.copyfile(package/n,out/n)
    return run_capture(package,c,stage,m,out,archive,reviewed,reviewed_event,finite,current,native,length)


def verify_legacy_package(package):
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


def run_capture(package,c,stage,m,out,archive,reviewed,reviewed_event,finite,current,native,length):
    error=None;process=None;analysis_process=None;status='BLOCKED';postchecked=False;operation_error=None;postcheck_error=None
    try:
        ctx=checked_a(c,stage,m)
        if current:m.write(out/'static_precheck.json',ctx['verification'])
        for src,dst in [('receipt.json','reviewed_a_receipt.json'),('artifact_manifest.json','reviewed_a_manifest.json'),
            ('source_bytes.json','reviewed_source_bytes.json'),('build/build.json','reviewed_build.json')]:
            shutil.copyfile(ctx['a_root']/src,out/dst)
        if current:
            for name in ('receipt.json','artifact_manifest.json','probe/review/review.json'):
                shutil.copyfile(Path(c['event_root'])/name,out/('reviewed_event_'+Path(name).name))
        resource_cfg=dict(ctx['acfg'],temporary_required_bytes=c['budget']['temporary_required_bytes']) if current else ctx['acfg']
        m.write(out/'resources.json',stage['startup_resources'](out,archive,resource_cfg))
        forbidden=('CUDA_INJECTION64_PATH','NVTX_INJECTION64_PATH','NV_COMPUTE_PROFILER_INJECTION_PATH')
        require(not any(os.environ.get(k) for k in forbidden),'EXTERNAL_PROFILER_ENVIRONMENT')
        model_cfg=dict(c['model_contract'],**{k:c[k] for k in ('model','inventory_sha256','prompt_sha256','gpu_uuid','gpu_pci','target_python','site_root')},
            inventory=str(package/'model_sha256.csv'),prompt=str(package/f'input_{length}.json'),
            session=dict(client=c['client']['path'],client_sha256=c['client']['sha256'],
                cupti=c['cupti']['path'],cupti_sha256=c['cupti']['sha256'],session_id=c['session_id']))
        if current:model_cfg['session']['activity_policy_version']=POLICY
        if finite:model_cfg['input_identity']=c['input_identity']
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
        m.write(out/'execution_plan.json',dict(argv=argv,budget=c['budget'],role='Engineering',input_tokens=length,
            output_tokens=2,batch_size=1,warmup_count=3,automatic_retry=False))
        try:
            process=m.command(argv,out,out/'one_model',env=env,timeout=300)
            require(process['status']=='EXITED' and process['exit_code']==0 and not process['timed_out'],'MODEL_EXIT')
            if current:m.verify_package(package)
            analysis_cfg=dict(c,model_config=str(out/'model_config.json'),model_script=str(model_script))
            if finite:analysis_cfg.update(consumer_root=str(package/'consumer'))
            m.write(out/'analysis_config.json',analysis_cfg)
            # Same capture, separate CPU-only consumer. No model is imported here.
            analyse_boot=('import sys,runpy,json;sys.dont_write_bytecode=True;'
                'p=sys.argv.pop(1);sys.path[:0]=sys.argv[1:3];del sys.argv[1:3];'
                'm=runpy.run_path(p);m["analyze_model"](sys.argv[1],json.loads(sys.argv[2]),json.load(open(sys.argv[3])))')
            if finite:
                analyse_boot=('import sys,runpy,json;sys.dont_write_bytecode=True;'
                    'p=sys.argv.pop(1);sys.path[:0]=sys.argv[1:3];del sys.argv[1:3];'
                    'c=json.load(open(sys.argv[3]));m=runpy.run_path(p);'
                    'b=runpy.run_path(str(__import__("pathlib").Path(p).with_name("cupti_model_consumer.py")));'
                    'fact=b["bind_consumer"](c);'
                    'json.dump(fact,open(str(__import__("pathlib").Path(sys.argv[1])/"consumer_binding.json"),"x"),indent=2);'
                    'm["analyze_model"](sys.argv[1],json.loads(sys.argv[2]),c)')
            analysis_process=m.command([c['python'],'-I','-S','-X','utf8','-c',analyse_boot,str(package/'cupti_timeline_b.py'),
                c['code_root'],c['site_root'],str(out/'model'),json.dumps(process),str(out/'analysis_config.json')],
                out,out/'same_run_analysis',env=env,timeout=180)
        except BaseException as exc:
            operation_error=type(exc).__name__+':'+str(exc);raise
        finally:
            # command() persists the actual original process record before it
            # raises on nonzero exit. Retain that fact instead of leaving null.
            if process is None and (out/'one_model.process.json').is_file():process=read(out/'one_model.process.json')
            if analysis_process is None and (out/'same_run_analysis.process.json').is_file():analysis_process=read(out/'same_run_analysis.process.json')
            try:
                if current:m.verify_package(package)
                after=checked_a(c,stage,m);postchecked=True
                if current:m.write(out/'static_postcheck.json',after['verification'])
            except BaseException as exc:postcheck_error=type(exc).__name__+':'+str(exc);raise
        status=f'MODEL{length}_BOTH_TOKENS_COMPLETE_STOP_FOR_REVIEW'
    except BaseException as exc:error=type(exc).__name__+':'+str(exc)
    m.write(out/'receipt.json',dict(schema_version='cupti-timeline-stage-b-receipt/0.2.0' if finite else 'cupti-timeline-stage-b-receipt/0.1.1' if current else 'cupti-timeline-stage-b-receipt/0.1.0',phase='B',status=status,error=error,
        controller_commit=c['controller_commit'],native_commit=native,analysis_commit=c['analysis_commit'],
        reviewed_a_receipt_sha256=reviewed,package_index_sha256=sha(package/'package_manifest.json'),process=process,
        post_execution_static_rechecked=postchecked,role='Engineering',budget=c['budget'],
        analysis_process=analysis_process,operation_error=operation_error,postcheck_error=postcheck_error,
        reviewed_event_receipt_sha256=reviewed_event,
        PyTorch_coverage='PENDING_REVIEW' if not error else 'NOT_QUALIFIED',COE_admission='NOT_ASSESSED',
        old_instance_repair=False,formal_eligible=False,historical_ylq_total_bytes=None,
        long_term_target_exclusive_bytes=50000000000))
    try:print(json.dumps(m.pack(out,archive)),flush=True)
    except BaseException as exc:print('PACK_REFUSED_PRESERVE_SCENE:'+str(exc),flush=True);return 2
    if error:print('STOP:'+error,flush=True);return 2
    return 0


def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--package',required=True);p.add_argument('--reviewed-a-receipt-sha256',required=True)
    p.add_argument('--reviewed-event-receipt-sha256')
    p.add_argument('--run-reviewed-model',action='store_true');a=p.parse_args(argv)
    return run(a.package,enabled=a.run_reviewed_model,reviewed=a.reviewed_a_receipt_sha256,
        reviewed_event=a.reviewed_event_receipt_sha256)


if __name__=='__main__':raise SystemExit(main())
