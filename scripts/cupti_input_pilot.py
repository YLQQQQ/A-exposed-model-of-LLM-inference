"""Default static review, then an explicitly reviewed finite configured plan.

Reuses the single-run controller and native DLL. No deployment/rebuild, retry,
Nsight, fallback point, or alteration of production S/A/B is implemented here.
"""
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode=True


def load(name):
    spec=importlib.util.spec_from_file_location('_pilot_'+name,Path(__file__).with_name(name+'.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def control():return load('cupti_timeline_b')
def contract():return load('cupti_input_contract')


def fixed_budget(plan=None):
    if plan is not None:contract().role_policy().validate_cupti_plan(plan)
    count=9 if plan is None else len(plan['input_lengths'])*plan['blocks']
    return dict(model_process_budget=count,cupti_sessions=count,nsight_profiles=0,blocks=3 if plan is None else plan['blocks'],
        per_model_seconds=300,per_analysis_seconds=180,temporary_required_bytes=12*2**30,
        automatic_retry=False,automatic_replacement=False,automatic_cleanup=False)


def check_runtime(c):
    contract().require(Path(sys.executable).resolve()==Path(c['python']).resolve()
        and list(sys.version_info[:3])==[3,11,16],'CONTROLLER_PYTHON')
    return dict(executable=str(Path(sys.executable).resolve()),version=list(sys.version_info[:3]))


def configuration(package,b,m):
    m.verify_package(package);c=b.read(package/'delivery.json');helper=contract()
    planned=c['schema_version']==helper.PLAN_VERSION;plan=c.get('plan') if planned else None
    helper.require(c['schema_version'] in (helper.VERSION,helper.PLAN_VERSION) and c['controller_commit']==c['analysis_commit']
        and c['native_commit']==helper.NATIVE and c['budget']==fixed_budget(plan),'CONFIGURATION')
    helper.require(c['slots']==helper.schedule(c['batch_id'],c['controller_commit'],**(dict(plan=plan) if planned else {})),'SCHEDULE')
    b.consumer_policy(c)
    helper.require(set(c['inputs'])==({'512','1024','2048'} if not planned else {str(n) for n in plan['input_lengths']}),'INPUT_COVERAGE')
    for key,r in c['inputs'].items():
        helper.require(r['path']==f'input_{key}.json' and b.sha(package/r['path'])==r['sha256'],'INPUT_HASH')
        helper.require(helper.input_identity(b.read(package/r['path']),int(key))==r['identity'],'INPUT_IDENTITY')
        if planned:helper.validate_output_policy(r['output_validation'],plan['role'])
        else:
            ids=r['expected_token_ids']
            helper.require(isinstance(ids,list) and len(ids)==2 and all(isinstance(v,list) and len(v)==1
                and type(v[0]) is int and v[0]>=0 for v in ids),'TOKEN_REFERENCE')
    if planned:
        helper.require(b.sha(package/'model_config_reference.json')==c['model_config_sha256'],'MODEL_CONFIG_HASH')
        helper.require(c['model_limits']==helper.model_limits(b.read(package/'model_config_reference.json')),'MODEL_LIMITS')
        for n in plan['input_lengths']:helper.input_identity(b.read(package/f'input_{n}.json'),n,b.read(package/'model_config_reference.json'))
    helper.require(b.sha(package/'producer_policy.py')==c['producer_policy_sha256'],'PRODUCER_POLICY_HASH')
    return c


def one_configuration(c,slot):
    helper=contract();r=c['inputs'][str(slot['input_tokens'])]
    planned=c['schema_version']==helper.PLAN_VERSION;role=c['plan']['role'] if planned else 'Pilot'
    model=dict(schema_version=helper.PLAN_MODEL if planned else helper.MODEL,input_tokens=slot['input_tokens'],batch_size=1,output_tokens=2,
        warmup_count=3,repeat_count=1,role=role,completion_policy='HOST_READABLE_P',model_process_budget=1,
        nsight_profiles=0,torch_profiler=False,native_commit=c['native_commit'],control_commit=c['controller_commit'],
        activity_policy_version=c['activity_policy_version'],run_id=slot['run_id'],
        producer_policy_sha256=c['producer_policy_sha256'],code_root=c['code_root'],**helper.POLICIES)
    # Versioned per-run manifest is also the actual model configuration lineage.
    if planned:model.update(input_plan=c['plan'],input_slot=slot,output_validation=r['output_validation'],
        model_config_sha256=c['model_config_sha256'],model_limits=c['model_limits'])
    if role=='Pilot':model['pilot']=slot
    result=dict(c,schema_version=helper.PLAN_CONTROL if planned else helper.CONTROL,model_contract=model,
        run_id=slot['run_id'],session_id=slot['run_id'],input_identity=r['identity'],prompt_sha256=r['sha256'],
        budget=control().fixed_budget())
    if planned:result.update(input_slot=slot,output_validation=r['output_validation'])
    else:result['expected_token_ids']=r['expected_token_ids']
    if role=='Pilot':result['pilot']=slot
    return result


def locations(c,m,phase):
    tag=c['controller_commit'][:12];root=Path(c['server_root'])
    role=c.get('plan',{}).get('role','Pilot').lower()
    relative=f'diagnostics/cupti_input_{tag}_static' if phase=='A' else f'evidence/cupti_timeline/input_{tag}_{role}'
    suffix='static' if phase=='A' else role
    return m.safe(root,relative),m.safe(root,f'transfer/cupti_input_{tag}_{suffix}.zip')


def static(package):
    package=Path(package).resolve();b=control();stage,m=b.components(package);c=configuration(package,b,m)
    out,archive=locations(c,m,'A');b.require(not out.exists() and not archive.exists(),'NO_OVERWRITE_RESUME_RETRY')
    out.mkdir(parents=True,exist_ok=False);archive.parent.mkdir(parents=True,exist_ok=True)
    error=None;status='BLOCKED';verification=None;runtime=None
    try:
        runtime=check_runtime(c)
        # The batch contract is not a single-run observation contract. Derive
        # the already-defined run profile for native A + event reference checks
        # only; this neither executes nor qualifies the first (or any) slot.
        reference=one_configuration(c,c['slots'][0])
        ctx=b.checked_a(reference,stage,m);verification=ctx['verification']
        m.write(out/'static_precheck.json',verification)
        if c['schema_version']==contract().PLAN_VERSION:
            # CPU/file-only capacity evidence; never a GPU allocation or inference.
            b.require(b.sha(Path(c['model'])/'config.json')==c['model_config_sha256'],'MODEL_CONFIG_HASH')
            m.write(out/'model_limits.json',dict(model_config_sha256=c['model_config_sha256'],
                source='ACTUAL_INVENTORY_BOUND_CONFIG_NOT_GPU_QUALIFICATION',
                config=b.read(Path(c['model'])/'config.json')))
        resource=stage['startup_resources'](out,archive,dict(ctx['acfg'],temporary_required_bytes=12*2**30))
        m.write(out/'resources.json',resource)
        # Syntax/strict contracts only; no import of torch or vendor DLL.
        import py_compile
        for r in c['cpu_sources']:
            source=package/r['path'];b.require(source.is_file() and b.sha(source)==r['sha256'],'CPU_SOURCE_HASH')
            target=out/'compile'/(r['path'].replace('/','_')+'.pyc');target.parent.mkdir(exist_ok=True)
            py_compile.compile(str(source),cfile=str(target),doraise=True)
        for slot in c['slots']:
            mc=one_configuration(c,slot)['model_contract'];mc['session']=dict(activity_policy_version=c['activity_policy_version'])
            helper=contract();helper.validate_model(mc)
        m.verify_package(package);status='STATIC_READY_FOR_REVIEW'
    except BaseException as exc:error=type(exc).__name__+':'+str(exc)
    m.write(out/'delivery.json',c)
    m.write(out/'receipt.json',dict(schema_version='cupti-input-static-receipt/0.1.0',phase='A',status=status,error=error,
        controller_commit=c['controller_commit'],analysis_commit=c['analysis_commit'],native_commit=c['native_commit'],
        package_index_sha256=b.sha(package/'package_manifest.json'),runtime=runtime,verification=verification,
        planned_model_processes=len(c['slots']),actual_model_processes=0,actual_cupti_sessions=0,nsight_profiles=0,
        B_authorized=False,historical_ylq_total_bytes=None,long_term_target_exclusive_bytes=50000000000))
    try:print(json.dumps(m.pack(out,archive)),flush=True)
    except BaseException as exc:print('PACK_REFUSED_PRESERVE_SCENE:'+str(exc),flush=True);return 2
    return 2 if error else 0


def checked_static(package,c,b,m,reviewed):
    root,unused=locations(c,m,'A')
    b.require(isinstance(reviewed,str) and len(reviewed)==64 and b.sha(root/'receipt.json')==reviewed,'NEW_A_RECEIPT_HASH')
    m.verify_rows(root,b.read(root/'artifact_manifest.json')['files'])
    r=b.read(root/'receipt.json')
    b.require(r['schema_version']=='cupti-input-static-receipt/0.1.0' and r['status']=='STATIC_READY_FOR_REVIEW'
        and r['error'] is None and r['B_authorized'] is False and r['controller_commit']==c['controller_commit']
        and r['analysis_commit']==c['analysis_commit'] and r['native_commit']==c['native_commit']
        and r['package_index_sha256']==b.sha(package/'package_manifest.json')
        and all(type(r[k]) is int and r[k]==0 for k in ('actual_model_processes','actual_cupti_sessions','nsight_profiles')),
        'NEW_A_RECEIPT')
    return r


def run(package,*,enabled=False,reviewed=None,reviewed_event=None,reviewed_static=None):
    b=control();b.require(enabled is True,'EXPLICIT_REVIEWED_PILOT_REQUIRED');package=Path(package).resolve()
    stage,m=b.components(package);c=configuration(package,b,m)
    b.require(reviewed==c['reviewed_a_receipt_sha256'] and reviewed_event==c['reviewed_event_receipt_sha256'],'REVIEWED_REFERENCES')
    check_runtime(c)
    checked_static(package,c,b,m,reviewed_static)
    out,archive=locations(c,m,'B');b.require(not out.exists() and not archive.exists(),'NO_OVERWRITE_RESUME_RETRY')
    out.mkdir(parents=True,exist_ok=False);archive.parent.mkdir(parents=True,exist_ok=True)
    shutil.copytree(package,out/'delivery')
    states=[dict(slot=s,status='NOT_RUN',error=None) for s in c['slots']];rows=[];error=None
    try:
        for i,slot in enumerate(c['slots']):
            print(f'[slot] {i+1}/{len(c["slots"])} block={slot["block"]} position={slot["position"]} input={slot["input_tokens"]} START',flush=True)
            m.verify_package(package);cfg=one_configuration(c,slot);folder=out/'runs'/slot['run_id']
            folder.mkdir(parents=True,exist_ok=False)
            states[i]['status']='RUNNING'
            result=b.run_capture(package,cfg,stage,m,folder,archive,reviewed,reviewed_event,True,True,c['native_commit'],
                slot['input_tokens'],pack_result=False)
            if result:
                states[i].update(status='BLOCKED',error=b.read(folder/'receipt.json')['error'])
                raise ValueError('PILOT_SLOT_FAILED_NO_RETRY:'+str(i+1))
            report=b.read(folder/'model/analysis_report.json')
            planned=c['schema_version']==contract().PLAN_VERSION
            b.require(report['status']=='BOTH_TOKENS_EVIDENCE_COMPLETE_PENDING_REVIEW' and report['errors']==[]
                and report['role']==(c['plan']['role'] if planned else 'Pilot')
                and report['input_slot' if planned else 'pilot']==slot and len(report['metrics'])==2,'RUN_REPORT')
            rows.append(dict(slot=slot,metrics=report['metrics'],report_sha256=b.sha(folder/'model/analysis_report.json'),
                capture_sha256=report['capture_sha256']))
            states[i]['status']='COMPLETE_PENDING_REVIEW'
            print(f'[slot] {i+1}/{len(c["slots"])} COMPLETE_PENDING_REVIEW',flush=True)
        m.write(out/'summary.json',contract().summarize(c['slots'],rows,
            **(dict(plan=c['plan']) if c['schema_version']==contract().PLAN_VERSION else {})));m.verify_package(package)
    except BaseException as exc:
        error=type(exc).__name__+':'+str(exc)
        for s in states:
            if s['status']=='RUNNING':s.update(status='BLOCKED',error=error)
    planned=c['schema_version']==contract().PLAN_VERSION
    m.write(out/'receipt.json',dict(schema_version='cupti-input-run-receipt/0.2.0' if planned else 'cupti-input-pilot-receipt/0.1.0',role=c['plan']['role'] if planned else 'Pilot',
        status=('FIXED_PLAN_COMPLETE_STOP_FOR_REVIEW' if planned else 'NINE_RUNS_COMPLETE_STOP_FOR_REVIEW') if error is None else 'BLOCKED',error=error,slots=states,
        controller_commit=c['controller_commit'],analysis_commit=c['analysis_commit'],native_commit=c['native_commit'],
        reviewed_static_sha256=reviewed_static,completed_runs=len(rows),complete_blocks=[n for n in sorted({s['block'] for s in c['slots']})
            if all(s['status']=='COMPLETE_PENDING_REVIEW' for s in states if s['slot']['block']==n)],
        budget=c['budget'],historical_ylq_total_bytes=None,formal_eligible=False,automatic_retry=False,
        old_samples_pooled=False,summary_sha256=b.sha(out/'summary.json') if (out/'summary.json').is_file() else None))
    try:print(json.dumps(m.pack(out,archive)),flush=True)
    except BaseException as exc:print('PACK_REFUSED_PRESERVE_SCENE:'+str(exc),flush=True);return 2
    return 2 if error else 0


def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--package',required=True);p.add_argument('--run-reviewed-pilot',action='store_true')
    p.add_argument('--reviewed-a-receipt-sha256');p.add_argument('--reviewed-event-receipt-sha256');p.add_argument('--reviewed-static-sha256')
    a=p.parse_args(argv)
    return run(a.package,enabled=True,reviewed=a.reviewed_a_receipt_sha256,reviewed_event=a.reviewed_event_receipt_sha256,
        reviewed_static=a.reviewed_static_sha256) if a.run_reviewed_pilot else static(a.package)


if __name__=='__main__':raise SystemExit(main())
