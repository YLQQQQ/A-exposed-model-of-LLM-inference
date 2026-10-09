"""External delivery controller; imports the frozen checkout, never changes it.

No default collection. The signed release and explicit manual switch are both
required. Measurement, identity, S/A/B and statistics remain in frozen modules.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def require(ok, reason):
    if not ok: raise ValueError('DELIVERY_' + reason)


def persist(path,value):
    from exposedpath.gate8_isolated_preflight import write_new
    path=Path(path)
    pending=path.with_suffix('.pending.json')
    write_new(pending,value)
    pending.replace(path)


def plan(release,batch_id,declared_at):
    from exposedpath.formal_protocol import make_binding,ORDERS,validate_release
    validate_release(release['protocol'],release['approval'])
    result=[]
    for block,conditions in enumerate(ORDERS,1):
        for position,condition in enumerate(conditions,1):
            order=['pass0','pass1'] if (block+position)%2==0 else ['pass1','pass0']
            for pass_id in order:
                result.append(make_binding(release['protocol'],release['approval'],batch_id=batch_id,
                    block=block,condition=condition,pass_id=pass_id,declared_at=declared_at))
    require(len(result)==60 and sum(b['pass_id']=='pass1' for b in result)==30,'BUDGET')
    return result


def run_batch(output,release,batch_id,execute,summarize,*,declared_at):
    bindings=plan(release,batch_id,declared_at)
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    persist(output/'planned_runs.json',dict(runs=bindings,model_process_budget=60,profile_budget=30))
    result=dict(schema_version='gate13-fixed-batch/0.1',status='BLOCKED',error=None,
        runs=[dict(binding=b,status='NOT_RUN') for b in bindings],pairs=[],automatic_retry=False,
        gate13='NOT_RUN',measurement_validity='NOT_ASSESSED',dropped_records_status='UNKNOWN')
    report=output/'batch_report.json';persist(report,result)
    for i,b in enumerate(bindings):
        row=result['runs'][i];row['status']='RUNNING';persist(report,result)
        print(f"[formal {i+1}/60] block={b['block']} condition={b['condition']} pass={b['pass_id']} START",flush=True)
        try:
            observed=execute(b,output/b['run_id'])
            require(observed.get('binding')==b and observed.get('status')=='RUN_COMPLETE_PENDING_REVIEW','ACTUAL_BINDING')
            row.update(observed)
            if i%2:
                pair=summarize(result['runs'][i-1],row,output)
                require(pair['pair_id']==b['pair_id'] and pair['status']=='PAIR_COMPLETE_PENDING_REVIEW','PAIR')
                result['pairs'].append(pair)
                for length in (32,512):
                    group=[p for p in result['pairs'] if p.get('input_tokens')==length]
                    require(not group or all(p['token_ids']==group[0]['token_ids'] for p in group),'BATCH_TOKENS')
                environments=[p['environment'] for p in result['pairs'] if 'environment' in p]
                require(not environments or all(e==environments[0] for e in environments),'BATCH_ENVIRONMENT')
        except BaseException as exc:
            row.update(status='BLOCKED',error=f'{type(exc).__name__}: {exc}')
            result['error']=row['error'];persist(report,result)
            print('[formal] STOP '+row['error'],flush=True)
            if not isinstance(exc,Exception):raise
            break
        persist(report,result)
    else:
        persist(output/'formal_index.json',dict(schema_version='exposedpath-formal-batch-index/0.1.0',
                                                runs=[r['index_entry'] for r in result['runs']]))
        result['status']='FORMAL_BATCH_COLLECTED_PENDING_REVIEW';persist(report,result)
    return result


def collect(binding,path,config):
    from exposedpath.formal_protocol import validate
    from exposedpath.gate8_diagnostic import prepare_diagnostic
    from exposedpath.gate11_pilot import sha
    from scripts.gate8_diagnostic_collect import run_once
    from scripts.gate8_pair import inspect_execution
    path.mkdir(parents=True,exist_ok=False)
    long=binding['condition']=='G512'
    prompt=Path(config['prompt_512'] if long else config['prompt'])
    expected=config['prompt_512_sha256'] if long else config['prompt_sha256']
    require(sha(prompt)==expected,'INPUT_CONTENT')
    print('[stage] prepare START',flush=True)
    prepared=prepare_diagnostic(output_dir=path/'prepared',model_path=config['model'],
        inventory_path=config['inventory'],inventory_sha256=config['inventory_sha256'],
        prompt_path=prompt,prompt_sha256=expected,expected_commit=config['commit'],physical_gpu=3,
        engineering_attention_backend='sdpa',target_python=config['target_python'],
        site_root=config['site_root'],formal_binding=binding)
    require(validate(read(prepared/'manifest.json'))==binding,'PREMODEL_IDENTITY')
    out=path/'collection';root=Path(config['code_root'])
    if binding['pass_id']=='pass0':
        args=[sys.executable,'-u',str(root/'scripts/gate8_pair.py'),'baseline','--python',config['target_python'],
            '--prepared',str(prepared),'--output',str(out),'--execute-signed-formal-baseline']
    else:
        args=[sys.executable,'-u',str(root/'scripts/gate8_diagnostic_collect.py'),'--python',config['target_python'],
            '--nsys',config['nsys'],'--prepared',str(prepared),'--output',str(out),
            '--execute-engineering-diagnostic','--engineering-domain','--signed-formal-protocol']
    print('[stage] execute/collection/export/analysis START',flush=True)
    proc=run_once(args,path/'driver',timeout_seconds=900,progress=True)
    require(proc['status']=='COMPLETE','DRIVER_FAILURE_NO_RETRY')
    facts=inspect_execution(out,binding['pass_id'])
    require(facts.get('formal')==binding,'ACTUAL_FORMAL_BINDING')
    mpath=out/'diagnostic/manifest.json';epath=out/'diagnostic/engineering_execution.json'
    index=dict(output_dir=str(out.relative_to(path.parent)),manifest_sha256=sha(mpath),
        execution_sha256=sha(epath),domain_sha256=None,baseline_sha256=None)
    if binding['pass_id']=='pass1':
        domain=out/'analyzed/domain.json'
        cr=read(out/'collection_report.json')
        require(cr.get('status')=='FORMAL_RUN_COMPLETE_PENDING_REVIEW' and cr.get('error') is None
            and cr.get('formal')==binding and cr.get('result_sha256')==sha(domain),'P1_REPORT')
        print('[stage] fair same-window baseline START',flush=True)
        process=run_once([sys.executable,'-X','utf8','-u',str(Path(__file__).resolve()),
            '--config',config['_config_path'],'--output',str(out),'--derive-baseline-only'],
            path/'baseline_driver',timeout_seconds=900,progress=True)
        require(process['status']=='COMPLETE','BASELINE_FAILED_NO_RETRY')
        base=out/'baseline/baseline.json'
        index.update(domain_sha256=sha(domain),baseline_sha256=sha(base))
    else:
        cr=read(out/'baseline_report.json')
        require(cr.get('role')=='UNPROFILED_LIMITED_FORMAL' and cr.get('formal')==binding
            and cr['status']=='BASELINE_COMPLETE_NOT_ACCEPTANCE','P0_REPORT')
    print('[stage] run COMPLETE; acceptance pending',flush=True)
    return dict(binding=binding,status='RUN_COMPLETE_PENDING_REVIEW',index_entry=index,process=proc)


def compare_pair(a,b,root):
    from scripts.gate8_pair import inspect_execution
    from scripts.gate11_pilot_batch import COMMON,GLOBAL_COMMON
    by={r['binding']['pass_id']:r for r in (a,b)}
    require(set(by)=={'pass0','pass1'},'PAIR_PASSES')
    p0=inspect_execution(Path(root)/by['pass0']['index_entry']['output_dir'],'pass0')
    p1=inspect_execution(Path(root)/by['pass1']['index_entry']['output_dir'],'pass1')
    m0,m1=p0['manifest'],p1['manifest']
    require(all(k in m0 and k in m1 and m0[k]==m1[k] for k in COMMON)
        and m0.get('n1_model')==m1.get('n1_model') and m0.get('n1_model_execution')==m1.get('n1_model_execution'),'PAIR_CONFIG')
    require(p0['formal']==by['pass0']['binding'] and p1['formal']==by['pass1']['binding']
        and p0['loaded_configuration']==p1['loaded_configuration'] and p0['token_ids']==p1['token_ids']
        and m0['target_python']['actual']['snapshot']==m1['target_python']['actual']['snapshot'],'PAIR_ACTUAL')
    result=dict(status='PAIR_COMPLETE_PENDING_REVIEW',pair_id=a['binding']['pair_id'],
        input_tokens=m0['fixed_input_tokens'],token_ids=p0['token_ids'],
        environment=dict(common={k:m0[k] for k in GLOBAL_COMMON},loaded=p0['loaded_configuration'],
            runtime=m0['target_python']['actual']['snapshot']),
        pass0_ns=p0['timing_ns'],pass1_ns=p1['timing_ns'],
        signed_difference_ns={k:p1['timing_ns'][k]-p0['timing_ns'][k] for k in p0['timing_ns']},
        interpretation='observational difference plus run variation; not pure profiler overhead')
    persist(Path(root)/(result['pair_id']+'.json'),result)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--batch-id');p.add_argument('--execute-reviewed-signed-formal',action='store_true')
    p.add_argument('--finish-only',action='store_true')
    p.add_argument('--derive-baseline-only',action='store_true')
    a=p.parse_args();c=read(a.config)
    sys.path.insert(0,str(Path(c['code_root']).resolve()))
    from exposedpath.formal_protocol import validate_release,validate_artifacts
    from exposedpath import platform_adapter
    from exposedpath.gate11_pilot import sha
    release=read(c['signed_release']);protocol=release['protocol']
    require(sha(c['signed_release'])==c['signed_release_sha256'],'SIGNED_RELEASE_FILE')
    validate_release(protocol,release['approval'])
    require(c['commit']==protocol['execution_commit']==protocol['analysis_commit']
        and platform_adapter.git(['-C',c['code_root'],'rev-parse','HEAD'])==c['commit']
        and not platform_adapter.git(['-C',c['code_root'],'status','--porcelain']),'CHECKOUT')
    validate_artifacts(c['code_root'],protocol)
    require(sum((a.finish_only,a.derive_baseline_only,a.execute_reviewed_signed_formal))==1,'EXPLICIT_SINGLE_ACTION')
    if a.derive_baseline_only:
        from exposedpath_v141.activity_baseline import write_baseline
        from exposedpath.formal_protocol import validate
        binding=validate(read(a.output/'diagnostic/manifest.json'))
        require(binding['protocol']==protocol and binding['approval']==release['approval'],'BASELINE_RELEASE')
        write_baseline(a.output/'analyzed/domain.json',a.output/'input_receipt.json',
            a.output/'diagnostic/engineering_execution.json',a.output/'baseline',
            **({'bridge_path':a.output/'diagnostic/n1_model_calls.json'} if binding['variant'] else {}))
        return 0
    if a.finish_only:
        from exposedpath_v141.paired_statistics import write_formal_report
        report=read(a.output/'batch_report.json')
        require(report['status']=='FORMAL_BATCH_COLLECTED_PENDING_REVIEW','INCOMPLETE_BATCH')
        print('[stage] complete-block file review/statistics START (no model or collection)',flush=True)
        write_formal_report(a.output/'formal_index.json',a.output/'statistics')
        report['status']='FORMAL_BATCH_COMPLETE_STOP_FOR_REVIEW'
        persist(a.output/'batch_report.json',report)
        return 0
    require(a.execute_reviewed_signed_formal and a.batch_id,'EXPLICIT_OPT_IN_REQUIRED')
    c['_config_path']=str(a.config.resolve())
    result=run_batch(a.output,release,a.batch_id,lambda b,path:collect(b,path,c),compare_pair,
        declared_at=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))
    if result['status']!='FORMAL_BATCH_COLLECTED_PENDING_REVIEW':return 1
    from scripts.gate8_diagnostic_collect import run_once
    # This is a CPU post-processing bound, not an increased collection/model
    # timeout or permission to extend the six-block experimental budget.
    process=run_once([sys.executable,'-X','utf8','-u',str(Path(__file__).resolve()),
        '--config',str(a.config.resolve()),'--output',str(a.output.resolve()),'--finish-only'],
        a.output/'finish_driver',timeout_seconds=7200,progress=True)
    if process['status']!='COMPLETE':
        result.update(status='BLOCKED_POSTPROCESSING',error='COMPLETE_BLOCK_REVIEW_FAILED_NO_RETRY')
        persist(a.output/'batch_report.json',result)
        return 1
    require(read(a.output/'batch_report.json')['status']=='FORMAL_BATCH_COMPLETE_STOP_FOR_REVIEW','FINAL_REPORT')
    return 0


if __name__=='__main__':raise SystemExit(main())
