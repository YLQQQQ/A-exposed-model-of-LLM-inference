"""Two explicitly requested P1 runs. Only local Prefill evidence is reviewed."""
import argparse
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from exposedpath import completion_path as contract,batch_load
from exposedpath.gate8_isolated_preflight import read,sha,write_new


def validate_collection_report(report,target):
    """0.1.0 success may omit error; no other evidence becomes optional."""
    target=Path(target)
    required=dict(schema_version='gate8-qwen-engineering-collection/0.1.0',
        status='PREFILL_LOCAL_ENGINEERING_ONLY',qualification='NOT_QUALIFIED',gate8_verdict='NOT_RUN',
        scientific_outputs_allowed=False,export_status='PASS',result_filename='prefill.json',
        q0_status='NOT_RUN',dropped_records_status='UNKNOWN',measurement_validity='NOT_ASSESSED')
    contract.require(isinstance(report,dict) and all(type(report.get(k)) is type(v) and report[k]==v
        for k,v in required.items()) and ('error' not in report or report['error'] is None),'LOCAL_COLLECTION_CONTRACT')
    process=report.get('collection')
    contract.require(isinstance(process,dict) and process.get('status')=='COMPLETE'
        and type(process.get('exit_code')) is int and process['exit_code']==0
        and process.get('timed_out') is False,'LOCAL_COLLECTION_PROCESS')
    for key,name in [('result_sha256','analyzed/prefill.json'),('manifest_sha256','diagnostic/manifest.json'),
            ('target_runtime_sha256','diagnostic/target_runtime.json'),('target_launch_sha256','target_launch.json')]:
        p=target/name
        contract.require(p.is_file() and isinstance(report.get(key),str) and report[key]==sha(p),'LOCAL_COLLECTION_HASH_'+key)
    return target/'analyzed/prefill.json'


def consume_collection(target,binding,commit):
    """Same strict consumer for new collection and immutable C0 reference."""
    from exposedpath_v141.completion_path_scope import load
    target=Path(target);result=validate_collection_report(read(target/'collection_report.json'),target)
    manifest=read(target/'diagnostic/manifest.json')
    contract.require(contract.validate(manifest)==binding and manifest['runner_git_commit']==commit
        and manifest['runner_git_dirty'] is False,'CONSUMER_EXECUTION_BINDING')
    token_path=target/'diagnostic/batch_tokens.json';token_hash=sha(token_path)
    value=load(result,target/'input_receipt.json',target/'diagnostic/engineering_execution.json')
    contract.require(value['status']=='PREFILL_LOCAL_ENGINEERING_ONLY' and value['binding']==binding
        and value['request_status']==value['decode_status']=='NOT_ACCEPTED_LOCAL_REVIEW_ONLY','PREFILL_REJECTED')
    # load validates token/producer/input lineage and actual per-sample counts.
    token_values=read(token_path)['requests'][0]['token_ids']
    contract.require(sha(token_path)==token_hash,'TOKEN_CHANGED_DURING_REVIEW')
    return value,token_values


def run(config,output,*,execute=False):
    contract.require(execute,'OPT_IN_REQUIRED')
    remaining=config['schema_version']=='completion-path-remaining-delivery/0.1'
    budget=1 if remaining else 2
    contract.require(config['schema_version'] in ('completion-path-delivery/0.1','completion-path-remaining-delivery/0.1')
        and type(config['model_process_budget']) is int and config['model_process_budget']==budget
        and type(config['profile_budget']) is int and config['profile_budget']==budget,'BUDGET')
    from exposedpath.platform_adapter import git
    contract.require(git(['-C',str(ROOT),'rev-parse','HEAD']).strip()==config['commit']
        and not git(['-C',str(ROOT),'status','--porcelain']).strip(),'CLEAN_EXECUTION_COMMIT')
    contract.require(sha(config['nsys'])==config['nsys_sha256'].lower(),'COLLECTOR_HASH')
    out=Path(output);contract.require(not out.exists(),'OUTPUT_EXISTS');out.mkdir(parents=True)
    prompt=batch_load.make_inputs(config['seed_input'],config['prompt_512_sha256'],out/'inputs')[1]
    from exposedpath.gate8_diagnostic import prepare_diagnostic
    from scripts.gate8_diagnostic_collect import run_once
    tokens=[];observations=[]
    reference_manifest=None
    if remaining:
        from scripts.completion_path_reference import review_reference
        prior,prior_tokens,reference_manifest,prior_target=review_reference(config,out/'c0_reference',ROOT)
        tokens.append(prior_tokens)
        observations.append(dict(variant='C0',execution_commit=reference_manifest['runner_git_commit'],
            result_sha256=sha(prior_target/'analyzed/prefill.json'),
            result_reference='c0_reference/experiment/batch/C0/collection/analyzed/prefill.json',
            prefill=prior['prefill'],timeline=prior['timeline'],full_pre_sync_dependencies=prior['full_pre_sync_dependencies'],
            decode_unresolved_effects=prior['decode_unresolved_effects']))
    def collect(b,folder):
        folder.mkdir();print('[stage] prepare '+b['variant'],flush=True)
        prepared=prepare_diagnostic(output_dir=folder/'prepared',model_path=config['model'],
            inventory_path=config['inventory'],inventory_sha256=config['inventory_sha256'],prompt_path=prompt,
            prompt_sha256=sha(prompt),expected_commit=config['commit'],physical_gpu=3,
            engineering_attention_backend='sdpa',target_python=config['target_python'],site_root=config['site_root'],
            batch_binding=contract.batch_binding(b),completion_binding=b)
        manifest=read(prepared/'manifest.json')
        if reference_manifest is not None:
            from scripts.completion_path_reference import COMMON_FIELDS
            contract.require(all(k in manifest and k in reference_manifest
                and manifest[k]==reference_manifest[k] for k in COMMON_FIELDS),'CROSS_VARIANT_EXECUTION_CONTRACT')
        from exposedpath_v141.gate8_adapter import normalized_uuid,normalized_pci
        contract.require(normalized_uuid(manifest['gpu_uuid'])==normalized_uuid(config['gpu_uuid'])
            and normalized_pci(manifest['gpu_pci_bus_id'])==normalized_pci(config['gpu_pci_bus_id']),'PREPARED_GPU')
        target=folder/'collection'
        argv=[str(Path(config['code_root'])/'.venv/Scripts/python.exe'),'-X','utf8','-u',str(ROOT/'scripts/gate8_diagnostic_collect.py'),
            '--nsys',config['nsys'],'--python',config['target_python'],'--prepared',str(prepared),
            '--output',str(target),'--execute-engineering-diagnostic','--engineering-a-only']
        process=run_once(argv,folder/'driver',timeout_seconds=900,progress=True)
        contract.require(process['status']=='COMPLETE' and process['exit_code']==0 and not process['timed_out'],'PROFILE_DRIVER')
        result=target/'analyzed/prefill.json'
        print('[stage] local_prefill_and_tokens '+b['variant'],flush=True)
        value,token_values=consume_collection(target,b,config['commit'])
        if tokens:contract.require(token_values==tokens[0],'CROSS_VARIANT_TOKEN_VALUES')
        tokens.append(token_values);observations.append(dict(variant=b['variant'],execution_commit=config['commit'],result_sha256=sha(result),
            result_reference=result.relative_to(out).as_posix(),prefill=value['prefill'],timeline=value['timeline'],
            full_pre_sync_dependencies=value['full_pre_sync_dependencies'],decode_unresolved_effects=value['decode_unresolved_effects']))
        return dict(status='PREFILL_COMPLETE_STOP_FOR_REVIEW',result_sha256=sha(result),
            request_status=value['request_status'],decode_status=value['decode_status'])
    if remaining:
        # A fresh one-slot batch. The old BLOCKED report is never resumed/edited.
        folder=out/'batch';folder.mkdir();b=contract.schedule(config['batch_id'])[1]
        row=dict(binding=b,status='NOT_RUN')
        result=dict(version='completion-path-remaining-delivery/0.1',status='BLOCKED',automatic_retry=False,
            model_process_budget=1,profile_budget=1,runs=[row],reused_c0=dict(binding=prior['binding'],
                execution_commit=reference_manifest['runner_git_commit'],role='IMMUTABLE_PREFILL_REFERENCE_NOT_NEW_EXECUTION'))
        try:
            row.update(collect(b,folder/'Cpre'))
            contract.require(row['status']=='PREFILL_COMPLETE_STOP_FOR_REVIEW','LOCAL_REVIEW')
            result['status']='BATCH_COMPLETE_STOP_FOR_REVIEW'
        except Exception as exc:row.update(status='BLOCKED',error=f'{type(exc).__name__}: {exc}')
        write_new(folder/'Cpre.receipt.json',row);write_new(folder/'batch_report.json',result)
    else:result=contract.run_batch(config['batch_id'],out/'batch',collect)
    if result['status']=='BATCH_COMPLETE_STOP_FOR_REVIEW':
        a0,a1=[v['prefill']['a_records'][0] for v in observations]
        write_new(out/'comparison.json',dict(version=contract.VERSION,observations=observations,token_ids=tokens,
            signed_cpre_minus_c0_ns={k:a1[k]-a0[k] for k in ('T_window_ns','A_host_path_ns','A_cuda_api_ns',
                'A_device_wait_ns','A_sync_residual_ns','A_unattributed_ns')},
            request_accepted=False,decode_accepted=False,formal_eligible=False,
            api_delta_is_internal_wait=False,statistical_stability='NOT_ASSESSED',
            dropped_records_status='UNKNOWN',measurement_validity='NOT_ASSESSED'))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--execute-reviewed-completion-path',action='store_true')
    p.add_argument('--review-c0-reference',action='store_true',help='CPU-only archive/consumer check; never collect')
    a=p.parse_args()
    if a.review_c0_reference:
        contract.require(not a.execute_reviewed_completion_path,'REFERENCE_OPT_IN_CONFLICT')
        from scripts.completion_path_reference import review_reference
        review_reference(read(a.config),a.output,ROOT);print('C0_PREFILL_REFERENCE_REVIEWED',flush=True);return 0
    r=run(read(a.config),a.output,execute=a.execute_reviewed_completion_path)
    print(r['status'],flush=True);return 0 if r['status']=='BATCH_COMPLETE_STOP_FOR_REVIEW' else 1


if __name__=='__main__':raise SystemExit(main())
