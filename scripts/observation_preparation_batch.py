"""Explicit finite O/P Engineering or versioned input Pilot; never retry."""
import argparse
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from exposedpath import observation_preparation as contract
from exposedpath.gate8_isolated_preflight import read,sha


def consume_collection(target,binding,commit):
    from exposedpath import coe_input_pilot as axis,coe_pilot
    input_axis=axis.active(binding)
    rules=axis if input_axis else contract
    target=Path(target);report=read(target/'collection_report.json')
    expected=dict(schema_version='coe-input-pilot-collection/0.1.0' if input_axis else 'observation-preparation-collection/0.1.0',status=rules.STATUS,
        qualification='NOT_QUALIFIED',scientific_outputs_allowed=False,export_status='PASS',result_filename='sensitivity.json',
        **({'pilot':binding,'run_role':'PILOT','data_role':'Pilot'} if input_axis else {'batch_load':binding}),
        q0_status='NOT_RUN',dropped_records_status='UNKNOWN',measurement_validity='NOT_ASSESSED')
    contract.require(all(type(report.get(k)) is type(v) and report[k]==v for k,v in expected.items())
        and report.get('error') is None and 'analysis_rejection' not in report,'COLLECTION_CONTRACT')
    proc=report['collection']
    contract.require(proc['status']=='COMPLETE' and type(proc['exit_code']) is int and proc['exit_code']==0
        and proc['timed_out'] is False,'COLLECTION_PROCESS')
    for key,name in [('result_sha256','analyzed/sensitivity.json'),('manifest_sha256','diagnostic/manifest.json'),
        ('target_runtime_sha256','diagnostic/target_runtime.json'),('target_launch_sha256','target_launch.json')]:
        contract.require(report.get(key)==sha(target/name),'COLLECTION_HASH:'+key)
    from exposedpath_v141.gate8_files import load_input_receipt
    _,paths=load_input_receipt(target/'input_receipt.json')
    mf=read(paths['wmpc_manifest']);ledger=read(paths['pass_identity'])
    contract.require(rules.validate(mf)==binding and mf['runner_git_commit']==commit,'CONSUMER_EXECUTION')
    validator=coe_pilot if input_axis else contract
    validator.validate_prepared(mf,paths['wmpc_manifest'].parent,ROOT)
    execution=target/'diagnostic/engineering_execution.json'
    tokens=validator.validate_tokens(paths['pilot_tokens' if input_axis else 'batch_tokens'],mf,ledger,read(execution),paths['wmpc_manifest'],paths['producer_receipt'])
    exited=read(target/'diagnostic-entry/exit.json')
    contract.require(exited['status']=='EXITED' and type(exited['exit_code']) is int and exited['exit_code']==0
        and exited['pid']==ledger['pid'],'TARGET_EXIT')
    r=read(target/'analyzed/sensitivity.json');candidate_path=target/'analyzed/coe/candidate.json';candidate=read(candidate_path)
    contract.require(r['schema_version']==rules.RESULT_VERSION and r['status']==rules.STATUS and r['binding']==binding
        and r['input_receipt_sha256']==sha(target/'input_receipt.json') and r['execution_receipt_sha256']==sha(execution)
        and r['candidate_sha256']==sha(candidate_path) and r['token_ids']==tokens
        and r['preparation']==read(execution)['observation_preparation'] and r['physical_b_qualified'] is False
        and r['formal_eligible'] is False,'RESULT_BINDING')
    if input_axis or contract.input_axis(binding):
        from analysis.coe_budget_preview import VERSION as preview_version
        preview_path=target/'analyzed/candidate_budget_preview.json';preview=read(preview_path)
        contract.require(r.get('candidate_budget_preview_sha256')==sha(preview_path)
            and preview['schema_version']==preview_version and preview['candidate_sha256']==sha(candidate_path)
            and preview['input_receipt_sha256']==sha(target/'input_receipt.json'),'BUDGET_PREVIEW_BINDING')
    contract.require(all(sha(p)==h for p,h in candidate['source_hashes'].items()),'CANDIDATE_SOURCE_CHANGED')
    contract.require(len(r['operations'])==len(candidate['operations'])==2
        and all(all(op.get(k)==v for k,v in original.items())
            and op['operation_validity']=='VALID_UNDER_DECLARED_SUPPORT_ASSUMPTIONS'
            for op,original in zip(r['operations'],candidate['operations'])),'OPERATION_BINDING')
    return {**r,'result_sha256':sha(target/'analyzed/sensitivity.json'),
        'result_reference':'collection/analyzed/sensitivity.json'}


def run(config,output,*,execute=False,input_pilot=False):
    contract.require(execute,'OPT_IN_REQUIRED')
    from exposedpath import coe_input_pilot as axis
    rules=axis if input_pilot else contract
    version=axis.VERSION
    schema=config.get('schema_version')
    sensitivity=not input_pilot and schema=='observation-preparation-delivery/0.2'
    if sensitivity:
        version=contract.INPUT_VERSION
        contract.require(config.get('observation_contract_version')==version,'DELIVERY_CONTRACT_VERSION')
    if input_pilot and schema=='coe-input-pilot-delivery/0.2':
        version=axis.MIDPOINT_VERSION
        contract.require(config.get('input_contract_version')==version,'DELIVERY_CONTRACT_VERSION')
    expected_schema=('coe-input-pilot-delivery/0.2' if version==axis.MIDPOINT_VERSION else 'coe-input-pilot-delivery/0.1') if input_pilot else 'observation-preparation-delivery/0.2' if sensitivity else 'observation-preparation-delivery/0.1'
    budget=axis.specification(version)['budget'] if input_pilot else 8
    contract.require(schema==expected_schema
        and type(config.get('model_process_budget')) is int and type(config.get('profile_budget')) is int
        and config.get('model_process_budget')==config.get('profile_budget')==budget
        and config.get('commit')==config.get('analysis_commit'),'DELIVERY_CONTRACT')
    from exposedpath.platform_adapter import git
    contract.require(git(['-C',str(ROOT),'rev-parse','HEAD']).strip()==config['commit']
        and not git(['-C',str(ROOT),'status','--porcelain']).strip(),'CLEAN_EXECUTION')
    contract.require(sha(config['nsys'])==config['nsys_sha256'],'COLLECTOR_HASH')
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    kwargs={'version':version} if input_pilot or sensitivity else {}
    prompts=rules.make_inputs(config['seed_input'],config['prompt_512_sha256'],out/'inputs',**kwargs)
    if input_pilot or sensitivity:
        axis.require(set(config.get('input_bindings',{}))=={str(n) for n in prompts},'EXECUTION_INPUT_SET')
        for n,p in prompts.items():
            expected=config.get('input_bindings',{}).get(str(n),{})
            axis.require(expected==dict(file_sha256=sha(p),identity=axis.input_identity(read(p),version=version) if input_pilot else contract.input_identity(read(p))),
                'EXECUTION_INPUT_BINDING:'+str(n))
    from exposedpath.gate8_diagnostic import prepare_diagnostic
    from scripts.gate8_diagnostic_collect import run_once
    def collect(b,folder):
        folder.mkdir();prompt=prompts[b['input_tokens']]
        print('[stage] prepare '+b['run_id'],flush=True)
        prepared=prepare_diagnostic(output_dir=folder/'prepared',model_path=config['model'],
            inventory_path=config['inventory'],inventory_sha256=config['inventory_sha256'],prompt_path=prompt,
            prompt_sha256=config['input_bindings'][str(b['input_tokens'])]['file_sha256'] if input_pilot or sensitivity else sha(prompt),
            expected_commit=config['commit'],physical_gpu=3,
            engineering_attention_backend='sdpa',target_python=config['target_python'],site_root=config['site_root'],
            **({'pilot_binding':b} if input_pilot else {'batch_binding':b}))
        mf=read(prepared/'manifest.json')
        from exposedpath_v141.gate8_adapter import normalized_uuid,normalized_pci
        contract.require(normalized_uuid(mf['gpu_uuid'])==normalized_uuid(config['gpu_uuid'])
            and normalized_pci(mf['gpu_pci_bus_id'])==normalized_pci(config['gpu_pci_bus_id']),'PREPARED_GPU')
        target=folder/'collection'
        argv=[str(Path(config['code_root'])/'.venv/Scripts/python.exe'),'-X','utf8','-u',str(ROOT/'scripts/gate8_diagnostic_collect.py'),
            '--nsys',config['nsys'],'--python',config['target_python'],'--prepared',str(prepared),
            '--output',str(target),'--execute-engineering-diagnostic','--engineering-a-only','--pilot' if input_pilot else '--observation-preparation']
        p=run_once(argv,folder/'driver',timeout_seconds=900,progress=True)
        contract.require(p['status']=='COMPLETE' and type(p['exit_code']) is int and p['exit_code']==0
            and p['timed_out'] is False,'PROFILE_DRIVER')
        return consume_collection(target,b,config['commit'])
    return rules.run_batch(config['batch_id'],config['commit'],out/'batch',collect,**kwargs)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    group=p.add_mutually_exclusive_group()
    group.add_argument('--collect-reviewed-preparation',action='store_true')
    group.add_argument('--collect-reviewed-input-pilot',action='store_true')
    a=p.parse_args();r=run(read(a.config),a.output,execute=a.collect_reviewed_preparation or a.collect_reviewed_input_pilot,
        input_pilot=a.collect_reviewed_input_pilot)
    print(r['status'],flush=True)
    return 0 if r['status'] in ('FIXED_EIGHT_COMPLETE_STOP_FOR_REVIEW','FIXED_EIGHT_INPUT_PILOT_COMPLETE_STOP_FOR_REVIEW','FIXED_NINE_INPUT_PILOT_COMPLETE_STOP_FOR_REVIEW') else 1


if __name__=='__main__':raise SystemExit(main())
