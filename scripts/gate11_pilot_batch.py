"""Fixed first Pilot batch. Explicit execution opt-in; no retry or continuation."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from exposedpath.gate11_pilot import schedule, validate, require, sha, VERSION
from exposedpath.gate8_isolated_preflight import read,write_new


def persist(path,value):
    pending=path.with_suffix('.pending.json')
    with pending.open('w',encoding='utf-8') as f:
        json.dump(value,f,indent=2,sort_keys=True); f.flush(); os.fsync(f.fileno())
    pending.replace(path)


def run_batch(output,batch_id,execute,summarize, *, warmup_control=False):
    require(type(warmup_control) is bool,'BATCH_KIND')
    from exposedpath.gate11_warmup import schedule as warmup_schedule,VERSION as warmup_version
    version=warmup_version if warmup_control else VERSION
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    plan=warmup_schedule(batch_id) if warmup_control else schedule(batch_id)
    write_new(output/'planned_runs.json',dict(version=version,runs=plan,
        model_process_budget=30,profile_budget=0 if warmup_control else 15,overall_future_cap_not_authorization=60))
    result=dict(version=version,status='BLOCKED',run_role='PILOT',data_role='Pilot',
        gate11_verdict='BLOCKED' if warmup_control else 'NOT_RUN',formal_eligible=False,automatic_retry=False,
        runs=[dict(binding=b,status='NOT_RUN') for b in plan],pairs=[],error=None)
    report=output/'batch_report.json'; persist(report,result)
    completed=[]
    for i,binding in enumerate(plan):
        print(f"[pilot {i+1}/30] block={binding['block']} condition={binding['condition']} pass={binding['pass_id']} warmup={binding.get('warmup_count',1)} START",flush=True)
        row=result['runs'][i]; row['status']='RUNNING'; persist(report,result)
        try:
            observed=execute(binding,output/binding['run_id'])
            require(observed.get('binding')==binding and observed.get('status')=='RUN_COMPLETE_PENDING_REVIEW','RUN_FAILED_OR_IDENTITY')
            row.update(observed); completed.append(observed)
            if i%2==1:
                pair=summarize(completed[-2],completed[-1],output)
                require(pair.get('status')=='PAIR_COMPLETE_PENDING_REVIEW' and pair.get('pair_id')==binding['pair_id'],'PAIR_FAILED')
                result['pairs'].append(pair)
                # Same 32-token input across G32/N1 and all blocks. Exact values,
                # not latency or A proportions, bind the intended computation.
                comparable=[p for p in result['pairs'] if p.get('condition')!='G512' and 'token_ids' in p]
                require(not comparable or all(p['token_ids']==comparable[0]['token_ids'] for p in comparable),'CROSS_VARIANT_TOKEN_MISMATCH')
                long=[p for p in result['pairs'] if p.get('condition')=='G512' and 'token_ids' in p]
                require(not long or all(p['token_ids']==long[0]['token_ids'] for p in long),'CROSS_BLOCK_TOKEN_MISMATCH')
                environments=[p['environment'] for p in result['pairs'] if 'environment' in p]
                require(not environments or all(e==environments[0] for e in environments),'CROSS_BLOCK_ENVIRONMENT')
            print(f"[pilot {i+1}/30] COMPLETE; review pending",flush=True)
        except BaseException as exc:
            row.update(status='BLOCKED',error=f'{type(exc).__name__}: {exc}')
            result['error']=row['error']; persist(report,result)
            print('[pilot] STOP '+row['error'],flush=True)
            if not isinstance(exc,Exception): raise
            break
        persist(report,result)
    else:
        require(len(result['pairs'])==15,'PAIR_BUDGET')
        result['status']='WARMUP_BATCH_COMPLETE_STOP_FOR_REVIEW' if warmup_control else 'FIRST_BATCH_COMPLETE_STOP_FOR_REVIEW'
        persist(report,result)
    return result


COMMON=('runner_git_commit','runner_git_dirty','runner_source_sha256','model_id','model_content_snapshot',
    'prompt_tokens_sha256','fixed_input_tokens','fixed_output_tokens','batch_size','warmup_count','repeat_count',
    'dtype_and_quantization','sampling_config','execution_mode','attention_backend','engineering_scope',
    'gpu_index_physical','gpu_index_logical','gpu_uuid','gpu_pci_bus_id','isolated_preflight_version',
    'domain_qualification','study_mode','n1_intervention')

GLOBAL_COMMON=tuple(k for k in COMMON if k not in ('prompt_tokens_sha256','fixed_input_tokens',
    'domain_qualification','study_mode','n1_intervention'))


def inspect_run(output, binding):
    from scripts.gate8_pair import inspect_execution
    observed=inspect_execution(output,binding['pass_id']); m=observed['manifest']
    require(validate(m)==binding and observed['pilot']==binding,'RUN_BINDING')
    if binding['pass_id']=='pass0':
        report=read(Path(output)/'baseline_report.json')
        require(report['status']=='BASELINE_COMPLETE_NOT_ACCEPTANCE' and report.get('pilot')==binding
            and report.get('role')=='UNPROFILED_LIMITED_PILOT','BASELINE_REPORT')
    else:
        report=read(Path(output)/'collection_report.json'); path=Path(output)/'analyzed/domain.json'
        domain=read(path)
        require(report.get('status')=='PILOT_RUN_COMPLETE_PENDING_REVIEW' and not report.get('error')
            and report.get('pilot')==binding and report['collection']['status']=='COMPLETE'
            and report['export_status']=='PASS' and report['result_sha256']==sha(path),'PROFILE_REPORT')
        require(domain['schema_version']=='exposedpath-pilot-domain-check/0.1.0'
            and domain.get('pilot')==binding and domain['identity']['run_id']==binding['run_id']
            and domain['status']=='QUALITY_CHECK_PASSED_NOT_QUALIFICATION'
            and domain['execution_receipt_sha256']==sha(Path(output)/'diagnostic/engineering_execution.json')
            and domain['input_receipt_sha256']==sha(Path(output)/'input_receipt.json')
            and domain['formal_eligible'] is False and domain['measurement_validity']=='NOT_ASSESSED'
            and domain['dropped_records_status']=='UNKNOWN','DOMAIN_RESULT')
    return observed


def summarize_pair(first,second,output):
    from scripts.gate8_pair import overhead
    ordered=(first['binding'],second['binding'])
    require(ordered[0]['pair_id']==ordered[1]['pair_id'] and ordered[0]['pass_order']==[x['pass_id'] for x in ordered],'PAIR_ORDER')
    runs={r['binding']['pass_id']:inspect_run(r['output'],r['binding']) for r in (first,second)}
    require(set(runs)=={'pass0','pass1'},'PAIR_PASSES')
    a,b=runs['pass0'],runs['pass1']; ma,mb=a['manifest'],b['manifest']
    require(all(k in ma and k in mb and ma[k]==mb[k] for k in COMMON),'PAIR_COMMON')
    require(ma.get('n1_model')==mb.get('n1_model') and ma.get('n1_model_execution')==mb.get('n1_model_execution'),'PAIR_N1')
    require(ma['target_python']['actual']['snapshot']==mb['target_python']['actual']['snapshot'],'PAIR_RUNTIME')
    require(a['loaded_configuration']==b['loaded_configuration'] and a['token_ids']==b['token_ids'],'PAIR_OUTPUT_OR_CONFIGURATION')
    result=dict(version=VERSION,status='PAIR_COMPLETE_PENDING_REVIEW',pair_id=ordered[0]['pair_id'],
        condition=ordered[0]['condition'],block=ordered[0]['block'],order=[x['pass_id'] for x in ordered],
        environment=dict(manifest={k:ma[k] for k in GLOBAL_COMMON},
            runtime=ma['target_python']['actual']['snapshot'],loaded_configuration=a['loaded_configuration']),
        run_role='PILOT',data_role='Pilot',gate11_verdict='NOT_RUN',formal_eligible=False,
        token_ids=a['token_ids'],output_token_value_parity='EXACT_MATCH',
        overhead=overhead(a['timing_ns'],b['timing_ns']),pass0=a,pass1=b,
        clock='PYTHON_PERF_COUNTER_NS',timing='host-observed start to last host-readable completion',
        interpretation='profiler/common instrumentation plus run variation; N1 intervention retained in both passes',
        statistical_stability='NOT_ASSESSED',measurement_validity='NOT_ASSESSED',dropped_records_status='UNKNOWN')
    write_new(Path(output)/(ordered[0]['pair_id']+'.json'),result)
    return result


def collect_run(binding,path,config):
    from exposedpath.gate8_diagnostic import prepare_diagnostic
    from scripts.gate8_diagnostic_collect import run_once
    from exposedpath_v141.gate8_adapter import normalized_uuid,normalized_pci
    path.mkdir(parents=True,exist_ok=False)
    prompt=Path(config['prompt_512'] if binding['condition']=='G512' else config['prompt'])
    expected=config['prompt_512_sha256'] if binding['condition']=='G512' else config['prompt_sha256']
    require(sha(prompt)==expected.lower(),'PROMPT')
    print('[stage] prepare START',flush=True)
    prepared=prepare_diagnostic(output_dir=path/'prepared',model_path=config['model'],
        inventory_path=config['inventory'],inventory_sha256=config['inventory_sha256'],
        prompt_path=prompt,prompt_sha256=expected,expected_commit=config['commit'],physical_gpu=3,
        engineering_attention_backend='sdpa',target_python=config['target_python'],site_root=config['site_root'],pilot_binding=binding)
    manifest=read(prepared/'manifest.json')
    require(validate(manifest)==binding and normalized_uuid(manifest['gpu_uuid'])==normalized_uuid(config['gpu_uuid'])
        and normalized_pci(manifest['gpu_pci_bus_id'])==normalized_pci(config['gpu_pci_bus_id']),'PREMODEL_IDENTITY')
    print('[stage] prepare COMPLETE',flush=True)
    out=path/'collection'
    if binding['pass_id']=='pass0':
        argv=[sys.executable,'-u',str(ROOT/'scripts/gate8_pair.py'),'baseline','--python',config['target_python'],
            '--prepared',str(prepared),'--output',str(out),'--execute-pilot-baseline']
    else:
        argv=[sys.executable,'-u',str(ROOT/'scripts/gate8_diagnostic_collect.py'),'--python',config['target_python'],
            '--nsys',config['nsys'],'--prepared',str(prepared),'--output',str(out),
            '--execute-engineering-diagnostic','--engineering-domain','--pilot']
    process=run_once(argv,path/'driver',timeout_seconds=900,progress=True)
    require(process['status']=='COMPLETE','DRIVER_FAILURE_STOP_NO_RETRY')
    observed=inspect_run(out,binding)
    return dict(status='RUN_COMPLETE_PENDING_REVIEW',binding=binding,output=str(out),
        manifest_sha256=observed['manifest_sha256'],producer_sha256=observed['producer_sha256'],process=process)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',required=True,type=Path); p.add_argument('--output',required=True,type=Path)
    p.add_argument('--batch-id',required=True); p.add_argument('--execute-reviewed-pilot',required=True,action='store_true')
    a=p.parse_args(); config=read(a.config)
    return 0 if run_batch(a.output,a.batch_id,lambda b,path:collect_run(b,path,config),summarize_pair)['status']=='FIRST_BATCH_COMPLETE_STOP_FOR_REVIEW' else 1


if __name__=='__main__': raise SystemExit(main())
