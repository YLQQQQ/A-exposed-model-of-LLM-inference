"""Nine prospective P1 processes; deployment alone never opts into collection."""
import argparse
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from exposedpath import coe_pilot as contract
from exposedpath.gate8_isolated_preflight import read,sha,write_new


def consume_collection(target,binding,commit):
    target=Path(target);report=read(target/'collection_report.json')
    expected=dict(schema_version='coe-pilot-collection/0.1.0',status='COE_PILOT_PREFILL_ONLY_PENDING_REVIEW',
        qualification='NOT_QUALIFIED',scientific_outputs_allowed=False,export_status='PASS',
        result_filename='prefill.json',run_role='PILOT',data_role='Pilot',pilot=binding,
        q0_status='NOT_RUN',dropped_records_status='UNKNOWN',measurement_validity='NOT_ASSESSED')
    contract.require(all(type(report.get(k)) is type(v) and report[k]==v for k,v in expected.items())
        and report.get('error') is None and 'analysis_rejection' not in report,'COLLECTION_CONTRACT')
    proc=report['collection']
    contract.require(proc['status']=='COMPLETE' and type(proc['exit_code']) is int and proc['exit_code']==0
        and proc['timed_out'] is False,'COLLECTION_PROCESS')
    for key,name in [('result_sha256','analyzed/prefill.json'),('manifest_sha256','diagnostic/manifest.json'),
        ('target_runtime_sha256','diagnostic/target_runtime.json'),('target_launch_sha256','target_launch.json')]:
        contract.require(report.get(key)==sha(target/name),'COLLECTION_HASH:'+key)
    from exposedpath_v141.gate8_files import load_input_receipt
    _,paths=load_input_receipt(target/'input_receipt.json')
    mf=read(paths['wmpc_manifest']);ledger=read(paths['pass_identity'])
    contract.require(contract.validate(mf)==binding and mf['runner_git_commit']==commit,'CONSUMER_EXECUTION')
    contract.validate_prepared(mf,paths['wmpc_manifest'].parent,ROOT)
    tokens=contract.validate_tokens(paths['pilot_tokens'],mf,ledger,read(target/'diagnostic/engineering_execution.json'),
        paths['wmpc_manifest'],paths['producer_receipt'])
    exit_record=read(target/'diagnostic-entry/exit.json')
    contract.require(exit_record['status']=='EXITED' and type(exit_record['exit_code']) is int
        and exit_record['exit_code']==0 and exit_record['pid']==ledger['pid'],'TARGET_EXIT')
    r=read(target/'analyzed/prefill.json');candidate=read(target/'analyzed/coe/candidate.json')
    contract.require(r['schema_version']=='coe-pilot-prefill-result/0.1.0' and r['status']==expected['status']
        and r['binding']==binding and r['input_receipt_sha256']==sha(target/'input_receipt.json')
        and r['execution_receipt_sha256']==sha(target/'diagnostic/engineering_execution.json')
        and r['candidate_sha256']==sha(target/'analyzed/coe/candidate.json')
        and r['token_ids']==tokens and r['input_identity']==mf['coe_input']
        and r['source_identity']==candidate['source_identity']
        and r['request_status']==r['decode_status']=='NOT_ACCEPTED','RESULT_BINDING')
    contract.require(all(sha(p)==h for p,h in candidate['source_hashes'].items()),'CANDIDATE_SOURCE_CHANGED')
    contract.require(r['coe'] in candidate['operations'] and r['coe']['phase']=='prefill'
        and r['coe']['operation_validity']=='VALID_UNDER_DECLARED_SUPPORT_ASSUMPTIONS','OPERATION_VALIDITY')
    # All single values, B2 and signs survive; no P0 or benefit inference.
    coe={k:r['coe'][k] for k in ('candidate_ns','original_sync_ns','wall_ns','uncovered_ns','kernel_ns','memop_ns',
        'copy_wall_ns','sync_wall_ns','same_operation_all_gpu_union_ns','terminal','terminal_end_ns','operation_id')}
    baseline={k:r['baseline'][k] for k in ('api','runtime_api','driver_api','sync_api','non_sync_api','kernel','memop',
        'gpu_activity','gpu_active_ratio','mapping_count','mapped_count','definitions')}
    return dict(status=r['status'],binding=binding,token_ids=tokens,coe=coe,
        prefill=r['prefill'],input_identity=r['input_identity'],decode_isolation=r['decode_isolation'],
        baseline=baseline,result_sha256=sha(target/'analyzed/prefill.json'),
        result_reference='collection/analyzed/prefill.json')


def run(config,output,*,execute=False):
    contract.require(execute,'OPT_IN_REQUIRED')
    contract.require(config.get('schema_version')=='coe-pilot-delivery/0.1'
        and config.get('model_process_budget')==config.get('profile_budget')==9
        and config.get('commit')==config.get('analysis_commit'),'DELIVERY_CONTRACT')
    from exposedpath.platform_adapter import git
    contract.require(git(['-C',str(ROOT),'rev-parse','HEAD']).strip()==config['commit']
        and not git(['-C',str(ROOT),'status','--porcelain']).strip(),'CLEAN_EXECUTION')
    contract.require(sha(config['nsys'])==config['nsys_sha256'],'COLLECTOR_HASH')
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    prompts=contract.make_inputs(config['seed_input'],config['prompt_512_sha256'],out/'inputs')
    from exposedpath.gate8_diagnostic import prepare_diagnostic
    from scripts.gate8_diagnostic_collect import run_once
    def collect(b,folder):
        folder.mkdir();prompt=prompts[b['batch_size']]
        print('[stage] prepare '+b['run_id'],flush=True)
        prepared=prepare_diagnostic(output_dir=folder/'prepared',model_path=config['model'],
            inventory_path=config['inventory'],inventory_sha256=config['inventory_sha256'],prompt_path=prompt,
            prompt_sha256=sha(prompt),expected_commit=config['commit'],physical_gpu=3,
            engineering_attention_backend='sdpa',target_python=config['target_python'],site_root=config['site_root'],pilot_binding=b)
        mf=read(prepared/'manifest.json')
        from exposedpath_v141.gate8_adapter import normalized_uuid,normalized_pci
        contract.require(normalized_uuid(mf['gpu_uuid'])==normalized_uuid(config['gpu_uuid'])
            and normalized_pci(mf['gpu_pci_bus_id'])==normalized_pci(config['gpu_pci_bus_id']),'PREPARED_GPU')
        target=folder/'collection'
        argv=[str(Path(config['code_root'])/'.venv/Scripts/python.exe'),'-X','utf8','-u',str(ROOT/'scripts/gate8_diagnostic_collect.py'),
            '--nsys',config['nsys'],'--python',config['target_python'],'--prepared',str(prepared),
            '--output',str(target),'--execute-engineering-diagnostic','--engineering-a-only','--pilot']
        p=run_once(argv,folder/'driver',timeout_seconds=900,progress=True)
        contract.require(p['status']=='COMPLETE' and type(p['exit_code']) is int and p['exit_code']==0
            and p['timed_out'] is False,'PROFILE_DRIVER')
        return consume_collection(target,b,config['commit'])
    return contract.run_batch(config['batch_id'],config['commit'],out/'batch',collect)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--collect-reviewed-coe-pilot',action='store_true')
    a=p.parse_args();r=run(read(a.config),a.output,execute=a.collect_reviewed_coe_pilot)
    print(r['status'],flush=True)
    return 0 if r['status']=='FIXED_NINE_COMPLETE_STOP_FOR_REVIEW' else 1


if __name__=='__main__':raise SystemExit(main())
