"""Two explicitly requested P1 runs. Only local Prefill evidence is reviewed."""
import argparse
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from exposedpath import completion_path as contract,batch_load
from exposedpath.gate8_isolated_preflight import read,sha,write_new


def run(config,output,*,execute=False):
    contract.require(execute,'OPT_IN_REQUIRED')
    contract.require(config['schema_version']=='completion-path-delivery/0.1'
        and config['model_process_budget']==2 and config['profile_budget']==2,'BUDGET')
    from exposedpath.platform_adapter import git
    contract.require(git(['-C',str(ROOT),'rev-parse','HEAD']).strip()==config['commit']
        and not git(['-C',str(ROOT),'status','--porcelain']).strip(),'CLEAN_EXECUTION_COMMIT')
    contract.require(sha(config['nsys'])==config['nsys_sha256'].lower(),'COLLECTOR_HASH')
    out=Path(output);contract.require(not out.exists(),'OUTPUT_EXISTS');out.mkdir(parents=True)
    prompt=batch_load.make_inputs(config['seed_input'],config['prompt_512_sha256'],out/'inputs')[1]
    from exposedpath.gate8_diagnostic import prepare_diagnostic
    from scripts.gate8_diagnostic_collect import run_once
    from exposedpath_v141.completion_path_scope import load
    tokens=[];observations=[]
    def collect(b,folder):
        folder.mkdir();print('[stage] prepare '+b['variant'],flush=True)
        prepared=prepare_diagnostic(output_dir=folder/'prepared',model_path=config['model'],
            inventory_path=config['inventory'],inventory_sha256=config['inventory_sha256'],prompt_path=prompt,
            prompt_sha256=sha(prompt),expected_commit=config['commit'],physical_gpu=3,
            engineering_attention_backend='sdpa',target_python=config['target_python'],site_root=config['site_root'],
            batch_binding=contract.batch_binding(b),completion_binding=b)
        manifest=read(prepared/'manifest.json')
        from exposedpath_v141.gate8_adapter import normalized_uuid,normalized_pci
        contract.require(normalized_uuid(manifest['gpu_uuid'])==normalized_uuid(config['gpu_uuid'])
            and normalized_pci(manifest['gpu_pci_bus_id'])==normalized_pci(config['gpu_pci_bus_id']),'PREPARED_GPU')
        target=folder/'collection'
        argv=[str(Path(config['code_root'])/'.venv/Scripts/python.exe'),'-X','utf8','-u',str(ROOT/'scripts/gate8_diagnostic_collect.py'),
            '--nsys',config['nsys'],'--python',config['target_python'],'--prepared',str(prepared),
            '--output',str(target),'--execute-engineering-diagnostic','--engineering-a-only']
        process=run_once(argv,folder/'driver',timeout_seconds=900,progress=True)
        contract.require(process['status']=='COMPLETE' and process['exit_code']==0 and not process['timed_out'],'PROFILE_DRIVER')
        report=read(target/'collection_report.json');result=target/'analyzed/prefill.json'
        contract.require(report['status']=='PREFILL_LOCAL_ENGINEERING_ONLY' and report['error'] is None
            and report['result_filename']=='prefill.json' and report['result_sha256']==sha(result),'LOCAL_COLLECTION')
        print('[stage] local_prefill_and_tokens '+b['variant'],flush=True)
        value=load(result,target/'input_receipt.json',target/'diagnostic/engineering_execution.json')
        contract.require(value['status']=='PREFILL_LOCAL_ENGINEERING_ONLY','PREFILL_REJECTED')
        token_values=read(target/'diagnostic/batch_tokens.json')['requests'][0]['token_ids']
        if tokens:contract.require(token_values==tokens[0],'CROSS_VARIANT_TOKEN_VALUES')
        tokens.append(token_values);observations.append(dict(variant=b['variant'],result_sha256=sha(result),
            result_reference=result.relative_to(out).as_posix(),prefill=value['prefill'],timeline=value['timeline'],
            full_pre_sync_dependencies=value['full_pre_sync_dependencies'],decode_unresolved_effects=value['decode_unresolved_effects']))
        return dict(status='PREFILL_COMPLETE_STOP_FOR_REVIEW',result_sha256=sha(result),
            request_status=value['request_status'],decode_status=value['decode_status'])
    result=contract.run_batch(config['batch_id'],out/'batch',collect)
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
    a=p.parse_args();r=run(read(a.config),a.output,execute=a.execute_reviewed_completion_path)
    print(r['status'],flush=True);return 0 if r['status']=='BATCH_COMPLETE_STOP_FOR_REVIEW' else 1


if __name__=='__main__':raise SystemExit(main())
