"""Bounded delivery for one frozen c8 L512/B2/P invocation, never a new provider.

History proves assets; a separate exact Git/content/index check proves c8.
All scientific payloads are c8 blobs. This module and the explicit event-reference
dispatch are control code. Default preparation cannot load CUDA or run a model.
"""
import argparse
import csv
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from types import SimpleNamespace

sys.dont_write_bytecode=True
SCIENCE='c8f3dad152659044691f9ff328498c7a127815ea'
NATIVE='6c744bf52daff3fc54571e264a0c34e3207aa1df'
COMPAT='cupti-batch-historical-assets-current-source/0.1.0'
A_SHA='9d6d4000d07ea7d752c78f4d337f88fe35085e99995ee88242eae5a824ad971e'
EVENT_SHA='824183fcea1e4ca5d0f3423cfedf6fb791379bc80a4f3dd47318854a0fac0ed9'
POLICY='cupti-api22-activity-policy/0.2.0'


def need(ok,reason):
    if not ok:raise ValueError('BATCH_ONCE_'+reason)


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def write(p,v):
    with Path(p).open('x',encoding='utf8') as f:json.dump(v,f,indent=2)


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def validate_compatibility(c):
    x=c.get('asset_compatibility',{})
    need(c.get('schema_version')=='cupti-timeline-stage-b/0.5.0' and x==dict(schema_version=COMPAT,
        historical_native_commit=NATIVE,current_scientific_commit=SCIENCE,
        reviewed_a_receipt_sha256=A_SHA,reviewed_event_receipt_sha256=EVENT_SHA,
        history_is_not_current_checkout=True),'COMPATIBILITY')
    model=c.get('model_contract',{})
    need(c.get('analysis_commit')==c.get('controller_commit')==SCIENCE and c.get('native_commit')==NATIVE and
        c.get('consumer_version')=='submit-effect-bridge/0.3.0' and all(model.get(k)==v for k,v in dict(
            schema_version='cupti-timeline-model/0.5.0',input_tokens=512,batch_size=2,output_tokens=2,
            warmup_count=3,repeat_count=1,role='Engineering',completion_policy='HOST_READABLE_P').items()),
        'COMPATIBILITY_SCOPE')


def validate_scientific_contract(c):
    need(c.get('scientific_commit')==c.get('analysis_commit')==c.get('controller_commit')==SCIENCE and
        c.get('native_commit')==NATIVE and c.get('consumer_version')=='submit-effect-bridge/0.3.0' and
        c.get('activity_policy_version')==POLICY,'SCIENCE_BINDING')
    need(c.get('plan')==dict(schema_version='CUPTI-INPUT-PLAN/0.3.0',role='Engineering',
        conditions=[dict(input_tokens=512,batch_size=2)],blocks=1,orders=[['G512B2P']],comparisons=[]),
        'SINGLE_INSTANCE_PLAN')
    need(c['budget']==dict(model_process_budget=1,cupti_sessions=1,nsight_profiles=0,blocks=1,
        per_model_seconds=300,per_analysis_seconds=180,temporary_required_bytes=12*2**30,
        automatic_retry=False,automatic_replacement=False,automatic_cleanup=False),'BUDGET')
    p=c.get('inputs',{}).get('G512B2P',{})
    need(p.get('output_validation')==dict(version='cupti-output-validation/0.3.0',batch_size=2,
        output_tokens=2,eos_policy='ANY_SAMPLE_EOS_REJECT_WHOLE_INVOCATION',
        mode='OBSERVED_ENGINEERING',expected_token_ids=None),'OUTPUT_POLICY')


def locations(c):
    transfer=Path(c['server_root'])/'transfer';tag=c['delivery_control_commit'][:12]
    root=transfer/('coe_batch_L512B2_'+tag+('_repair1' if 'repair_profile' in c else ''))
    return dict(root=root,temporary=root/'temporary',static_zip=transfer/(root.name+'_static.zip'),
        once_zip=transfer/(root.name+'_once.zip'))


def authorize(action,flags):
    if action=='prepare':need(flags.get('approve_prepare') is True,'PREPARE_AUTHORIZATION')
    else:
        need(flags.get('approve_model') is True and flags.get('shared_use_approved') is True and
            isinstance(flags.get('reviewed_prepare_sha256'),str) and
            re.fullmatch('[0-9a-fA-F]{64}',flags['reviewed_prepare_sha256']),'MODEL_AUTHORIZATION')
    need(isinstance(flags.get('operator_reference'),str) and
        re.fullmatch('[A-Za-z0-9_.:-]{1,100}',flags['operator_reference']),'OPERATOR_REFERENCE')
    return dict(action=action,operator_reference=flags['operator_reference'],
        explicit_operator_opt_in=True,shared_use_approved=flags.get('shared_use_approved') is True,
        old_micro_authorization_used=False,utc=datetime.now(timezone.utc).isoformat())


def target_environment(c):
    need(os.name=='nt' and sys.flags.isolated and sys.flags.no_site and
        list(sys.version_info[:3])==[3,11,16] and Path(sys.executable).resolve()==Path(c['python']).resolve(),
        'TARGET_ISOLATED_PYTHON')
    return dict(executable=str(Path(sys.executable).resolve()),version=list(sys.version_info[:3]),
        isolated=True,no_site=True,source='ACTUAL_TARGET_INTERPRETER')


def observe_asset(fact):
    p=Path(fact['path'])
    for q in (p,*p.parents):
        need(not q.is_symlink() and not (q.exists() and getattr(q.lstat(),'st_file_attributes',0)&0x400),'ASSET_REPARSE')
    need(p.is_file(),'ASSET_MISSING')
    return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))


def check_scientific_blobs(c,lock,fixed):
    names={n+'.py':'scripts/'+n+'.py' for n in ('cupti_input_contract','cupti_input_pilot',
        'cupti_model_consumer','cupti_batch_accounting','cupti_timeline_b','cupti_timeline_model')}
    names['producer_policy.py']='exposedpath/gate11_pilot.py'
    names['startup_storage.py']='scripts/coe_startup_storage.py'
    for p in ('exposedpath_v141/cupti_driver_queries.py','scripts/analyze_completion_operation_candidate.py',
        'exposedpath_v141/submit_effect_bridge.py','analysis/cupti_timeline.py','analysis/coe_helper_identity.py',
        'analysis/coe_candidate.py','analysis/coe_completion_model.py','analysis/cupti_a_migration.py'):
        names['consumer/'+p]=p
    rows=lock['package_science']
    need(len(rows)==len(names) and {r['path'] for r in rows}==set(names),'SCIENCE_BLOB_COVERAGE')
    for r in rows:
        need(r['git_path']==names[r['path']],'SCIENCE_BLOB_PATH')
        b=fixed.git_bytes(c['git'],c['code_root'],'cat-file','blob',SCIENCE+':'+r['git_path'])
        need(len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'],'SCIENCE_BLOB')


def checked_assets(c,stage,m):
    """New explicit reference branch. Never changes an old receipt/expectation."""
    validate_compatibility(c)
    package=Path(c['package_root']);lock=read(package/'science_lock.json')
    need(lock['scientific_commit']==SCIENCE and lock['native_commit']==NATIVE,'SOURCE_LOCK')
    parent=Path(c['compatibility_check_root']);parent.mkdir(parents=True,exist_ok=True)
    import uuid
    out=parent/('check_'+uuid.uuid4().hex);out.mkdir()
    fixed=load(package/'git_materialization.py','batch_fixed_git')
    check_scientific_blobs(c,lock,fixed)
    current=fixed.check_deployed_tree(c['git'],c['code_root'],SCIENCE,lock['current_sources'],out/'git')
    # Verify the historical sealed files in their original tree, not its old
    # working-tree identity against today's checkout.
    root=Path(c['a_root'])
    need(c['reviewed_a_receipt_sha256']==A_SHA and sha(root/'receipt.json')==A_SHA and
        sha(root/'artifact_manifest.json')==c['a_manifest_sha256'] and
        sha(root/'delivery.json')==c['a_delivery_sha256'],'HISTORICAL_A_HASH')
    m.verify_rows(root,read(root/'artifact_manifest.json')['files'])
    r=read(root/'receipt.json');a=read(root/'delivery.json');build=read(root/'build/build.json')
    need(r['schema_version']=='cupti-timeline-stage-a-receipt/0.1.2' and r['phase']=='A' and
        r['status']=='STATIC_READY_FOR_REVIEW' and r['error'] is None and r['B_authorized'] is False and
        r['execution_commit']==r['analysis_commit']==a['execution_commit']==a['analysis_commit']==NATIVE and
        r['startup_diagnostic_version']=='cupti-timeline-startup/0.2.0' and
        all(type(r[k]) is int and r[k]==0 for k in ('stage_a_cuda_programs_executed','model_process_budget',
            'micro_process_budget','profile_budget')),'HISTORICAL_A_RECEIPT')
    need(a['schema_version']=='cupti-timeline-stage-a/0.1.2' and
        r['activity_policy_version']==a['activity_policy_version']==build['activity_policy_version']==POLICY and
        build['schema_version']=='cupti-timeline-build/0.1.0' and build['vendor_gpu_executed'] is False,'HISTORICAL_BUILD')
    clients=[f for f in build['binaries'] if f['path']=='client.dll'];need(len(clients)==1,'HISTORICAL_CLIENT')
    expected=dict(client=dict(path=build['client'],bytes=clients[0]['bytes'],sha256=clients[0]['sha256']),
        cupti=read(root/'cupti_file.json'),runtime=read(root/'runtime_file.json'))
    for k in ('client','cupti','runtime'):
        fields={'path','bytes','sha256'}
        need(set(expected[k])==(fields|{'file_version'} if k=='runtime' else fields),'HISTORICAL_LIBRARY_FIELDS')
        if k=='runtime':need(expected[k]['file_version']=='6.14.11.12040','HISTORICAL_RUNTIME_VERSION')
        expected_fact={n:expected[k][n] for n in fields}
        need(c[k]==expected_fact and stage['observe_asset'](c[k])==expected_fact,'LIBRARY_IDENTITY:'+k)
    need(sha(root/'source_bytes.json')==c['a_source_bytes_sha256'],'HISTORICAL_SOURCE_INDEX')
    pairs=lock['native_source_equivalence']
    need({p['path'] for p in pairs}=={'scripts/native_cupti_timeline/'+n for n in
        ('client.cpp','core.h','writer.h','activity_policy.h')}|{'exposedpath/cupti_timeline.py',
            'exposedpath/runner.py','exposedpath/observation_preparation.py'},'NATIVE_SOURCE_COVERAGE')
    for p in pairs:
        b=fixed.git_bytes(c['git'],c['code_root'],'cat-file','blob',NATIVE+':'+p['path'])
        d=fixed.git_bytes(c['git'],c['code_root'],'cat-file','blob',SCIENCE+':'+p['path'])
        need(b==d and hashlib.sha256(b).hexdigest()==p['sha256'],'NATIVE_SOURCE_CHANGED')
    verification=dict(schema_version=COMPAT,historical_native_commit=NATIVE,current_scientific_commit=SCIENCE,
        historical_a_receipt_sha256=A_SHA,historical_event_receipt_sha256=EVENT_SHA,
        historical_source_index_sha256=c['a_source_bytes_sha256'],current_source=current,
        libraries={k:c[k] for k in expected},historical_library_metadata=expected,old_receipts_modified=False,
        unchanged_runner_content_reference=NATIVE,
        legacy_runner_git_fields_are_not_current_HEAD=True,
        current_checkout_commit_from_explicit_check=SCIENCE,
        current_checkout_is_not_claimed_to_be_native_commit=True)
    write(out/'binding.json',verification)
    # Existing run_capture uses acfg ONLY as its startup resource descriptor.
    return dict(a_root=root,acfg=dict(storage_script=str(package/'startup_storage.py'),temporary_required_bytes=12*2**30),
        verification=verification)


def startup_resources(out,archive,cfg):
    storage=load(Path(cfg['storage_script']),'batch_startup_storage')
    result=storage.check(out,[Path(os.environ['TEMP'])],archive)
    need(result['status']=='STARTUP_RESOURCES_READY','STARTUP_RESOURCES:'+json.dumps(result['errors']))
    return result


def check_publication(c,out,m,flags=None):
    if 'repair_profile' in c:
        repair=load(Path(c['package_root'])/'cupti_batch_publication_repair.py','batch_publication_repair')
        api=SimpleNamespace(verify_package_files=verify_package_files,checked_preparation=checked_preparation)
        return repair.checked_publication(c,out,m,api,flags or {})
    """Fetch into transfer-only temporary objects; no HEAD/index/ref writes."""
    git,repo=c['git'],c['code_root'];remote='https://github.com/YLQQQQ/A-exposed-model-of-LLM-inference'
    objects=Path(os.environ['TEMP'])/'publication_objects';objects.mkdir(exist_ok=True)
    original=subprocess.run([git,'-C',repo,'rev-parse','--git-path','objects'],capture_output=True,timeout=30)
    need(original.returncode==0,'PUBLICATION_OBJECT_PATH')
    original_path=Path(original.stdout.decode().strip())
    if not original_path.is_absolute():original_path=Path(repo)/original_path
    git_env=dict(os.environ,GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='never',
        GIT_OBJECT_DIRECTORY=str(objects.resolve()),GIT_ALTERNATE_OBJECT_DIRECTORIES=str(original_path.resolve()))
    m.command([git,'ls-remote',remote,'refs/heads/main'],repo,out/'published_main',timeout=30,env=git_env)
    text=(out/'published_main.stdout').read_text(encoding='ascii').strip().split()
    need(len(text)==2 and re.fullmatch('[0-9a-f]{40}',text[0]) and text[1]=='refs/heads/main','PUBLICATION_QUERY')
    m.command([git,'-C',repo,'-c','gc.auto=0','-c','maintenance.auto=false','fetch','--no-tags',
        '--no-write-fetch-head',remote,text[0]],repo,out/'published_objects',timeout=60,env=git_env)
    m.command([git,'-C',repo,'merge-base','--is-ancestor',c['delivery_control_commit'],text[0]],repo,
        out/'published_ancestry',timeout=30,env=git_env)
    for i,row in enumerate(c['control_sources']):
        label=out/('published_source_'+str(i))
        m.command([git,'-C',repo,'cat-file','blob',c['delivery_control_commit']+':'+row['git_path']],
            repo,label,timeout=30,env=git_env)
        b=label.with_suffix('.stdout').read_bytes()
        need(hashlib.sha256(b).hexdigest()==row['sha256'] and len(b)==row['bytes'],'PUBLISHED_CONTROL_SOURCE')
    return dict(remote_main=text[0],delivery_control_commit=c['delivery_control_commit'],
        control_is_published_ancestor=True,checkout_changed=False,push_performed=False,
        fetched_objects=str(objects.resolve()),fetch_head_written=False)


def verify_package_files(package):
    package=Path(os.path.abspath(package))
    for q in (package,*package.parents):
        need(not q.is_symlink() and not (q.exists() and getattr(q.lstat(),'st_file_attributes',0)&0x400),'PACKAGE_REPARSE')
    index=read(package/'package_manifest.json');seen=set()
    need(index.get('schema_version') in ('cupti-batch-once-package/0.1.0','cupti-batch-once-package/0.1.1') and
        index.get('scientific_commit')==SCIENCE,'PACKAGE_VERSION')
    for row in index['files']:
        name=row['path'];p=Path(name)
        need(isinstance(name,str) and not p.is_absolute() and name and '\\' not in name and ':' not in name and
            '..' not in p.parts and name.casefold() not in seen,'PACKAGE_PATH')
        seen.add(name.casefold());target=package/p
        for q in (target,*target.parents):
            need(not q.is_symlink() and not (q.exists() and getattr(q.lstat(),'st_file_attributes',0)&0x400),'PACKAGE_REPARSE')
            if q==package:break
        need(target.is_file() and target.stat().st_size==row['bytes'] and sha(target)==row['sha256'],'PACKAGE_BYTES:'+name)
    actual=set()
    for directory,dirs,files in os.walk(package,followlinks=False):
        for name in [*dirs,*files]:
            p=Path(directory)/name
            need(not p.is_symlink() and not getattr(p.lstat(),'st_file_attributes',0)&0x400,'PACKAGE_REPARSE')
        actual.update((Path(directory)/n).relative_to(package).as_posix().casefold() for n in files)
    need(actual==seen|{'package_manifest.json'},'PACKAGE_COVERAGE')
    return index


def configuration(package):
    # Verify every sibling BEFORE importing even the reviewed bootstrap.
    index=verify_package_files(package)
    package=Path(package).resolve();b=load(package/'cupti_timeline_b.py','batch_frozen_control')
    stage,m=b.components(package);pilot=load(package/'cupti_input_pilot.py','batch_frozen_plan')
    c=pilot.configuration(package,b,m);validate_scientific_contract(c)
    need(c['delivery_control_commit']==index['delivery_control_commit'],'PACKAGE_CONTROL_IDENTITY')
    if 'repair_profile' in c:
        need(index['schema_version']=='cupti-batch-once-package/0.1.1','REPAIR_PACKAGE_VERSION')
        load(package/'cupti_batch_publication_repair.py','batch_repair_config').validate(c)
    else:need(index['schema_version']=='cupti-batch-once-package/0.1.0','PACKAGE_CONTROL_VERSION')
    lock=read(package/'science_lock.json')
    need(lock['scientific_commit']==SCIENCE and lock['native_commit']==NATIVE,'SOURCE_LOCK')
    need({r['path'] for r in lock['package_science']}==set(c['scientific_files']),'SCIENCE_COVERAGE')
    m.verify_rows(package,lock['package_science'])
    c['package_root']=str(package)
    c['storage_script']=str(package/'startup_storage.py')
    one=pilot.one_configuration(c,c['slots'][0]);validate_compatibility(one)
    stage=dict(stage,startup_resources=startup_resources,observe_asset=observe_asset)
    return c,one,b,stage,m


def gpu_resources(c,out,m):
    need(not any(k.startswith('NSYS_') or k in ('CUDA_INJECTION64_PATH','NVTX_INJECTION64_PATH',
        'NV_COMPUTE_PROFILER_INJECTION_PATH') for k in os.environ),'PROFILER_ENVIRONMENT')
    smi=shutil.which('nvidia-smi.exe');need(smi is not None,'NVIDIA_SMI_MISSING')
    m.command([smi,'-i','3','--query-gpu=index,uuid,pci.bus_id,name,driver_version,memory.total,memory.free','--format=csv,noheader,nounits'],
        out,out/'gpu',timeout=15)
    rows=list(csv.reader((out/'gpu.stdout').read_text(encoding='utf8').splitlines()))
    need(len(rows)==1 and len(rows[0])==7,'GPU_QUERY')
    index,uid,pci,name,driver,total,free=[x.strip() for x in rows[0]]
    need(index=='3' and uid==c['gpu_uuid'] and pci.lower()==c['gpu_pci'].lower() and free.isdecimal(),'GPU_IDENTITY')
    need(name==c['gpu_reference']['name'] and driver==c['gpu_reference']['driver_version'] and
        total.isdecimal() and int(total)==c['gpu_reference']['total_mib'],'GPU_REFERENCE_CHANGED')
    need(int(free)>=8192,'GPU_FREE_RESERVE')
    visible='UNKNOWN';query_error=None
    try:
        m.command([smi,'-i',uid,'--query-compute-apps=gpu_uuid,pid,process_name,used_gpu_memory',
            '--format=csv,noheader,nounits'],out,out/'gpu_processes',timeout=15)
        visible='RAW_QUERY_ONLY_NOT_PROOF_OF_NO_PROFILER'
    except Exception as exc:query_error=type(exc).__name__+':'+str(exc)
    result=dict(gpu_uuid=uid,pci=pci,name=name,driver_version=driver,total_mib=int(total),physical_index=3,
        observed_free_mib=int(free),startup_reserve_mib=8192,
        reserve_is_not_measured_peak_or_noninterference_guarantee=True,other_process_visibility=visible,
        process_query_error=query_error,subscriber_conflict='MUST_PASS_REAL_SESSION_OPEN',
        performance_comparability='NOT_ESTABLISHED',utc=datetime.now(timezone.utc).isoformat())
    write(out/'shared_gpu_resources.json',result);return result


def checked_preparation(package,paths,c,m,reviewed):
    prep=paths['root']/'prepare'
    need(sha(prep/'receipt.json')==reviewed.lower(),'PREPARE_RECEIPT_HASH')
    m.verify_rows(prep,read(prep/'artifact_manifest.json')['files']);r=read(prep/'receipt.json')
    need(r['schema_version']=='cupti-batch-once-control-receipt/0.1.0' and r['phase']=='prepare' and
        r['status']=='PREPARED_NOT_EXECUTED' and r['error'] is None and
        r['package_manifest_sha256']==sha(Path(package)/'package_manifest.json') and
        r['scientific_commit']==SCIENCE and r['delivery_control_commit']==c['delivery_control_commit'] and
        type(r['actual_model_processes']) is int and type(r['actual_cupti_sessions']) is int and
        r['actual_model_processes']==r['actual_cupti_sessions']==0,'PREPARE_RECEIPT')
    return r


def consume_instance(model,c,b):
    """Read saved source-bound views; do not rerun S or migrate again."""
    model=Path(model);report=read(model/'analysis_report.json')
    need(report['schema_version']=='cupti-timeline-model-review/0.5.0' and
        report['status']=='BOTH_TOKENS_EVIDENCE_COMPLETE_PENDING_REVIEW' and report['errors']==[] and
        report['role']=='Engineering' and report['batch_size']==2 and report['output_shape']==[2,2] and
        report['completion_unit']=='WHOLE_BATCH_INVOCATION' and len(report['metrics'])==2 and
        report['capture_sha256']==sha(model/'timeline/capture.json'),'INSTANCE_REPORT')
    summary=b.batch_accounting().read_summary(model,report,c)
    index=read(model/'batch_accounting/index.json')
    need(index['request_equals_phase_sum'] is True,'INSTANCE_PHASE_SUM')
    tokens=read(model/'tokens.json')
    need(tokens['status']=='COMPLETE' and tokens['output_shape']==[2,2] and tokens['early_eos'] is False and
        tokens['eos_hits']==[] and len(tokens['token_ids'])==2 and
        all(len(row)==2 and all(type(t) is int for t in row) for row in tokens['token_ids']),'INSTANCE_TOKENS')
    return dict(schema_version='cupti-single-batch-output-review/0.1.0',run_id=c['run_id'],
        actual_token_ids=tokens['token_ids'],input_identity=summary['input_identity'],
        observed_completion_ns={w['name']:w['wall_ns'] for w in summary['views']['original_a']},
        clock='CUPTI_TIMESTAMP_NS',host_clock_record='producer/host_boundaries.json_SEPARATE_NOT_SUBTRACTED',
        statistical_unit='WHOLE_BATCH_INVOCATION',independent_output_numerical_correctness='NOT_ASSESSED',
        observed_execution_not_P0_performance=True,original_A_is_same_source_candidate_not_production=True,
        accounting=summary,formal_eligible=False)


def run(package,action,flags):
    package=Path(package).resolve();c,one,b,stage,m=configuration(package)
    if action=='verify':
        print(json.dumps(dict(status='PACKAGE_VERIFIED_NO_TARGET_ACCESS',scientific_commit=SCIENCE,
            delivery_control_commit=c['delivery_control_commit'],CUDA_initialized=False)));return 0
    repaired='repair_profile' in c
    if repaired:
        need(action=='execute','REPAIR_NO_A_REPLAY')
        need(str(flags.get('reviewed_prepare_sha256','')).lower()==c['repair_profile']['reviewed_prepare_sha256'],
            'REPAIR_A_RECEIPT')
    approval=authorize(action,flags);environment=None;paths=locations(c)
    root=paths['root'];out=root/('prepare' if action=='prepare' else 'once')
    fixed=load(package/'git_materialization.py','batch_materialization')
    fixed.no_reparse(root)
    need(not out.exists() and not paths['once_zip'].exists() and
        (not root.exists() if action=='prepare' or repaired else root.is_dir()) and
        (not paths['static_zip'].exists() if action=='prepare' or repaired else paths['static_zip'].is_file()),'NO_OVERWRITE_RESUME_RETRY')
    root.mkdir(parents=True,exist_ok=action=='execute');out.mkdir()
    paths['temporary'].mkdir(exist_ok=action=='execute')
    for k in ('TEMP','TMP','TMPDIR'):os.environ[k]=str(paths['temporary'])
    for k,leaf in [('HF_HOME','hf'),('TRANSFORMERS_CACHE','hf/transformers'),('HF_HUB_CACHE','hf/hub'),
        ('HUGGINGFACE_HUB_CACHE','hf/hub'),('HF_DATASETS_CACHE','hf/datasets'),('TORCH_HOME','torch'),
        ('XDG_CACHE_HOME','cache'),('TORCH_EXTENSIONS_DIR','torch_extensions'),
        ('TRITON_CACHE_DIR','triton'),('CUDA_CACHE_PATH','cuda_cache')]:os.environ[k]=str(paths['temporary']/leaf)
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    one['compatibility_check_root']=str(out/'identity_checks')
    error=None;publication=None;status='BLOCKED';capture_status=None
    try:
        environment=target_environment(c)
        startup=startup_resources(out,paths['static_zip'] if action=='prepare' else paths['once_zip'],c)
        write(out/'startup_resources.json',startup)
        publication=check_publication(c,out,m,flags)
        lock=read(package/'science_lock.json')
        if action=='prepare':
            fixed.materialize_sources(c['git'],c['code_root'],SCIENCE,lock['current_sources'],out/'source_materialization')
            ctx=b.checked_a(one,stage,m);write(out/'asset_source_binding.json',ctx['verification'])
            need(sha(Path(c['model'])/'config.json')==c['model_config_sha256'],'MODEL_CONFIG_HASH')
            import py_compile
            target=out/'compile';target.mkdir()
            for name in ('cupti_batch_once_delivery.py','cupti_event_b.py'):
                py_compile.compile(str(package/name),cfile=str(target/(name+'.pyc')),doraise=True)
            status='PREPARED_NOT_EXECUTED'
        else:
            if not repaired:checked_preparation(package,paths,c,m,flags['reviewed_prepare_sha256'])
            gpu_resources(c,out,m)
            code=b.run_capture(package,one,stage,m,out,paths['once_zip'],A_SHA,EVENT_SHA,True,True,NATIVE,512,pack_result=False)
            capture_status=read(out/'receipt.json');need(code==0,'MODEL_OR_ANALYSIS_FAILED:'+str(capture_status['error']))
            need(capture_status['post_execution_static_rechecked'] is True and capture_status['operation_error'] is None
                and capture_status['postcheck_error'] is None,'POST_EXECUTION_IDENTITY')
            views=consume_instance(out/'model',read(out/'analysis_config.json'),b)
            write(out/'batch_instance_review.json',views)
            status='ONE_BATCH_INSTANCE_COMPLETE_PENDING_REVIEW'
    except BaseException as exc:error=type(exc).__name__+':'+str(exc)
    write(out/'delivery.json',c);shutil.copyfile(package/'package_manifest.json',out/'delivery_manifest.json')
    model_processes=0;sessions=0 if action=='prepare' else None
    if (out/'one_model.process.json').is_file():
        p=read(out/'one_model.process.json');model_processes=int(type(p.get('pid')) is int and p['pid']>0)
    if (out/'model/timeline/receipt.json').is_file():
        session=read(out/'model/timeline/receipt.json')
        if type(session.get('open_code')) is int and session['open_code']==0:sessions=1
    record=dict(schema_version='cupti-batch-once-control-receipt/0.1.1' if repaired else 'cupti-batch-once-control-receipt/0.1.0',phase=action,status=status if error is None else 'BLOCKED',
        error=error,scientific_commit=SCIENCE,analysis_commit=SCIENCE,delivery_control_commit=c['delivery_control_commit'],
        native_commit=NATIVE,package_manifest_sha256=sha(package/'package_manifest.json'),operator_approval=approval,
        environment=environment,publication=publication,model_receipt=capture_status,
        actual_model_processes=model_processes,actual_cupti_sessions=sessions,qualification='NOT_GRANTED',formal_eligible=False,
        independent_output_numerical_correctness='NOT_ASSESSED',historical_ylq_total_bytes=None,
        automatic_retry=False,automatic_cleanup=False,old_micro_authorization_used=False)
    if repaired:record['repair_profile']=c['repair_profile']
    write(out/'control_receipt.json',record)
    if action=='prepare':
        # This is a NEW preparation receipt, not a replacement of any old A.
        shutil.copyfile(out/'control_receipt.json',out/'receipt.json')
    try:print(json.dumps(m.pack(out if action=='prepare' else root,paths['static_zip'] if action=='prepare' else paths['once_zip'])),flush=True)
    except BaseException as exc:print('PACK_REFUSED_PRESERVE_SCENE:'+str(exc),flush=True);return 2
    print(json.dumps(dict(status=record['status'],error=error)),flush=True)
    return 2 if error else 0


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','execute','verify'],nargs='?',default='prepare')
    p.add_argument('--package',type=Path,default=Path(__file__).resolve().parent)
    p.add_argument('--approve-prepare',action='store_true');p.add_argument('--approve-model',action='store_true')
    p.add_argument('--shared-use-approved',action='store_true');p.add_argument('--reviewed-prepare-sha256')
    p.add_argument('--reviewed-control-publication');p.add_argument('--reviewed-control-publication-sha256')
    p.add_argument('--operator-reference');a=p.parse_args(argv)
    return run(a.package,a.action,vars(a))


if __name__=='__main__':raise SystemExit(main())
