"""One sequential Engineering pair; host completion timing, not statistical overhead."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from exposedpath.gate8_isolated_preflight import read,sha,write_new


def require(ok,reason):
    if not ok: raise ValueError('ENGINEERING_PAIR_'+reason)


def host_durations(records):
    require(len(records)==3,'BOUNDARY_COUNT')
    times=[]
    for i,r in enumerate(records):
        p=r['payload']; t=r['host_observed_ns']
        require(r['host_clock_id']=='PYTHON_PERF_COUNTER_NS' and type(t) is int
            and type(r['host_before_marker_ns']) is int and type(r['host_after_marker_ns']) is int
            and t<=r['host_before_marker_ns']<=r['host_after_marker_ns'],'CLOCK')
        require(p['boundary_kind']==('request_start' if i==0 else 'token_ready')
            and p['token_index']==(None if i==0 else i-1)
            and p['completion_mechanism']==('predrained_inputs_resident' if i==0 else 'device_to_host_token_ids'),'COMPLETION')
        times.append(t)
    require(times[0]<=times[1]<=times[2],'TIME_ORDER')
    return dict(full_request=times[2]-times[0],prefill=times[1]-times[0],decode=times[2]-times[1])


def overhead(pass0,pass1):
    require(set(pass0)==set(pass1)=={'full_request','prefill','decode'},'TIMING_FIELDS')
    require(all(type(x) is int and x>=0 for row in (pass0,pass1) for x in row.values()),'DURATION')
    return {k:dict(pass0_ns=pass0[k],pass1_ns=pass1[k],delta_ns=pass1[k]-pass0[k],
        relative_delta=(pass1[k]-pass0[k])/pass0[k] if pass0[k] else None) for k in pass0}


def unprofiled_argv(python,prepared,output):
    from scripts.gate8_diagnostic_collect import target_argv
    return target_argv(python,prepared,output)


def baseline(python,prepared,output):
    from scripts.gate8_diagnostic_collect import run_once
    from exposedpath import gate8_isolated_preflight as isolated
    from exposedpath.gate8_diagnostic import measurement_pass
    from exposedpath_v141.gate8_target_python import validate_probe,environment
    prepared,output=Path(prepared).resolve(),Path(output).resolve()
    manifest=read(prepared/'manifest.json'); target=validate_probe(manifest['target_python'])
    require(measurement_pass(manifest)=='pass0' and manifest['isolated_preflight_version']==isolated.VERSION,'BASELINE_DECLARATION')
    require(str(Path(python).resolve())==target['requested_executable'] and environment()==target['environment'],'TARGET')
    require(not output.exists(),'OUTPUT_EXISTS')
    write_new(prepared/'collection_intent.json',dict(run_id=manifest['run_id'],output_root=str(output),collector_pid=os.getpid()))
    output.mkdir(parents=True)
    report=dict(status='BLOCKED',gate8_verdict='NOT_RUN',role='UNPROFILED_ENGINEERING_BASELINE')
    if 'pilot' in manifest:
        report.update(role='UNPROFILED_LIMITED_PILOT',pilot=manifest['pilot'],run_role='PILOT',data_role='Pilot',gate11_verdict='NOT_RUN')
    try:
        receipt=isolated.seal(prepared,output,ROOT)
        process=run_once(unprofiled_argv(python,prepared,output),output/'collection_log')
        report['execution']=process
        require(process['status']=='COMPLETE','BASELINE_EXECUTION')
        isolated.finalize(receipt,prepared,ROOT)
        write_new(output/'auxiliary_preflight.final.json',dict(status='PASS',
            preflight_sha256=sha(receipt),target_claim_sha256=sha(output/'auxiliary_preflight.claim.json')))
        observed=inspect_execution(output,'pass0')
        require(observed['pid']==process['pid'],'BASELINE_DIRECT_PID')
        report.update(status='BASELINE_COMPLETE_NOT_ACCEPTANCE',observed=observed)
    except Exception as exc:
        report['error']=f'{type(exc).__name__}: {exc}'
    write_new(output/'baseline_report.json',report)
    return report


def inspect_execution(output,expected_pass):
    from exposedpath.gate8_diagnostic import measurement_pass
    from exposedpath.gate8_engineering_contract import validate_declaration
    from exposedpath.gate8_identity import validate_pass_identity
    from exposedpath_v141.gate8_target_python import bind_producer
    from exposedpath_v141.gate8_adapter import normalized_uuid,normalized_pci
    from exposedpath_v141.gate8_engineering_scope import _model_configuration
    output=Path(output); root=output/'diagnostic'
    manifest=read(root/'manifest.json'); producer=read(root/'producer/producer_receipt.json')
    ledger=read(root/'producer/pass_identity.json'); validate_pass_identity(ledger)
    declared=validate_declaration(manifest)
    require(measurement_pass(manifest)==ledger['pass_id']==expected_pass,'PASS')
    require(producer['status']=='COMPLETE' and producer['run_id']==ledger['run_id']==manifest['run_id']
        and producer['pass_id']==expected_pass and producer['attempt_id']==ledger['attempt_id'],'PRODUCER')
    require({'pass_identity.json','host_boundaries.json','drain_ledger.json','stage_ledger.json'}<=producer['files'].keys(),'PRODUCER_FILE_SET')
    for name,ref in producer['files'].items():
        p=root/'producer'/ref['filename']
        require(p.resolve().parent==(root/'producer').resolve() and name==ref['filename']
            and p.stat().st_size==ref['size_bytes'] and sha(p)==ref['sha256'],'PRODUCER_FILE')
    require(ledger['wmpc_manifest_sha256']==sha(root/'manifest.json')
        and ledger['prompt_sha256']==sha(root/'prompt.json')==manifest['prompt_tokens_sha256'],'INPUT_HASH')
    require(all(ledger[k]==manifest[k] for k in ('runner_git_commit','runner_git_dirty','runner_source_sha256','wmpc_id'))
        and ledger['runner_git_dirty'] is False and sha(root/'runner_source.py')==ledger['runner_source_sha256'],'CODE_IDENTITY')
    bind_producer(manifest['target_python'],read(root/'target_runtime.json'),ledger['pid'])
    exit_record=read(output/'diagnostic-entry/exit.json')
    require(exit_record['status']=='EXITED' and exit_record['exit_code']==0 and exit_record['pid']==ledger['pid'],'ENTRY')
    report=read(root/'diagnostic_report.json'); execution=read(root/'engineering_execution.json')
    require(report['status']=='DIAGNOSTIC_COMPLETE' and report['producer_receipt_sha256']==sha(root/'producer/producer_receipt.json')
        and execution['status']=='COMPLETE' and execution['manifest_sha256']==sha(root/'manifest.json')
        and execution['producer_receipt_sha256']==report['producer_receipt_sha256']
        and execution['identity']=={k:ledger[k] for k in ('run_id','pass_id','attempt_id','pid')}
        and execution['declaration']==declared,'REPORT')
    _model_configuration(execution['observed_configuration'],declared)
    probe=read(root/'cuda_probe.json')
    require(probe['pid']==ledger['pid'] and probe['gpu_index_logical']==manifest['gpu_index_logical']
        and normalized_uuid(probe['gpu_uuid'])==normalized_uuid(manifest['gpu_uuid'])
        and normalized_pci(probe['pci_bus_id'])==normalized_pci(manifest['gpu_pci_bus_id'])
        and probe['cuda_device_order']=='PCI_BUS_ID'
        and probe['cuda_visible_devices']==str(manifest['gpu_index_physical']),'DEVICE_IDENTITY')
    requests=ledger['requests']
    require(len(requests)==2 and [r['request_role'] for r in requests]==['warmup','measured']
        and all(r['outcome']=='COMPLETE' and not r['early_eos'] and not r['reasons']
            and r['actual_output_tokens']==r['expected_output_tokens']==2 for r in requests),'REQUESTS')
    measured=requests[1]; host=read(root/'producer/host_boundaries.json')
    require(len(host)==3 and all(r['payload']['identity']==measured['identity'] for r in host)
        and [r['payload']['boundary_id'] for r in host]==measured['observed_boundary_ids'],'HOST_IDENTITY')
    durations=host_durations(host)
    drains=read(root/'producer/drain_ledger.json')['drains']
    require(len(drains)==1 and drains[0]['identity']==measured['identity'] and drains[0]['status']=='COMPLETE'
        and drains[0]['error'] is None and drains[0]['host_clock_id']=='PYTHON_PERF_COUNTER_NS'
        and drains[0]['host_start_ns']<=drains[0]['host_end_ns']<=host[0]['host_observed_ns'],'DRAIN')
    stages=read(root/'producer/stage_ledger.json')['stages']
    require(len(stages)==3 and [s['payload']['stage_role'] for s in stages]==['setup','warmup','measured']
        and all(s['status']=='COMPLETE' and s['error'] is None
            and s['host_clock_id']=='PYTHON_PERF_COUNTER_NS'
            and type(s['host_start_ns']) is int and type(s['host_end_ns']) is int
            and s['host_start_ns']<=s['host_end_ns'] for s in stages)
        and stages[0]['host_end_ns']<=stages[1]['host_start_ns']
        and stages[1]['host_end_ns']<=stages[2]['host_start_ns']<=drains[0]['host_start_ns']
        and host[-1]['host_observed_ns']<=stages[2]['host_end_ns']
        and stages[2]['payload']['request_identity']==measured['identity'],'STAGE_ORDER')
    sealed=read(output/'auxiliary_preflight.json'); claim=read(output/'auxiliary_preflight.claim.json')
    require(sealed['run_id']==manifest['run_id']
        and sealed['input_hashes']['manifest.json']==sha(root/'manifest.json')
        and sealed['input_hashes']['prompt.json']==sha(root/'prompt.json')
        and claim==read(root/'isolated_preflight_target.json')
        and claim['target_pid']==ledger['pid'] and claim['nonce']==sealed['nonce']
        and claim['preflight_sha256']==sha(output/'auxiliary_preflight.json')
        and read(output/'auxiliary_preflight.final.json')==dict(status='PASS',preflight_sha256=sha(output/'auxiliary_preflight.json'),
            target_claim_sha256=sha(output/'auxiliary_preflight.claim.json')),'PREFLIGHT')
    if 'pilot' in manifest:
        from exposedpath.gate11_pilot import validate_tokens
        tokens=validate_tokens(root/'pilot_tokens.json',manifest,ledger,execution,root/'manifest.json',root/'producer/producer_receipt.json')
        require(report.get('pilot')==manifest['pilot'] and report.get('run_role')=='PILOT'
            and report.get('data_role')=='Pilot' and report.get('pilot_tokens_sha256')==sha(root/'pilot_tokens.json'),'PILOT_REPORT')
        if 'n1_model' in manifest:
            calls=read(root/'n1_model_calls.json')
            variant=manifest['n1_model']['variant']; count=0 if variant=='V0' else 1
            require(sha(root/'n1_model_calls.json')==execution.get('n1_model_calls_sha256')
                and calls['producer_receipt_sha256']==sha(root/'producer/producer_receipt.json')
                and calls['manifest_sha256']==sha(root/'manifest.json') and calls['pid']==ledger['pid']
                and len(calls['requests'])==2,'PILOT_N1_CALLS')
            for call,request in zip(calls['requests'],requests):
                require(call['identity']==request['identity'] and call['variant']==variant
                    and len(call['interventions'])==count and len(call['model_calls'])==2
                    and all(i['status']=='COMPLETE' and i['token_index']==1 and i['layer_index']==15
                        and i['synchronize_called']==(variant=='Vsync') for i in call['interventions']), 'PILOT_N1_INTERVENTION')
            require(calls['requests'][1]['observed_tokens']==tokens,'PILOT_N1_TOKENS')
    return dict(manifest=manifest,pid=ledger['pid'],timing_ns=durations,
        **(dict(token_ids=tokens,pilot=manifest['pilot']) if 'pilot' in manifest else {}),
        loaded_configuration=execution['observed_configuration'],cuda_probe=probe,
        manifest_sha256=sha(root/'manifest.json'),producer_sha256=sha(root/'producer/producer_receipt.json'))


def summarize(pass0,pass1):
    a,b=inspect_execution(pass0,'pass0'),inspect_execution(pass1,'pass1')
    ma,mb=a['manifest'],b['manifest']
    require(ma['engineering_pair']['pair_id']==mb['engineering_pair']['pair_id'] and ma['run_id']!=mb['run_id'],'PAIR_IDENTITY')
    keys=('runner_git_commit','runner_git_dirty','runner_source_sha256','model_id','model_content_snapshot',
        'prompt_tokens_sha256','fixed_input_tokens','fixed_output_tokens','batch_size','warmup_count','repeat_count',
        'dtype_and_quantization','sampling_config','execution_mode','attention_backend','engineering_scope',
        'gpu_index_physical','gpu_index_logical','gpu_uuid','gpu_pci_bus_id','isolated_preflight_version')
    require(all(k in ma and k in mb and ma[k]==mb[k] for k in keys),'CONTRACT_MISMATCH')
    require(ma['target_python']['actual']['snapshot']==mb['target_python']['actual']['snapshot'],'RUNTIME_MISMATCH')
    require(a['loaded_configuration']==b['loaded_configuration'],'LOADED_CONFIGURATION')
    require({k:v for k,v in a['cuda_probe'].items() if k!='pid'}=={k:v for k,v in b['cuda_probe'].items() if k!='pid'},'DEVICE_MISMATCH')
    require(read(Path(pass0)/'baseline_report.json')['status']=='BASELINE_COMPLETE_NOT_ACCEPTANCE','BASELINE_STATUS')
    collection=read(Path(pass1)/'collection_report.json')
    require(collection['collection']['status']=='COMPLETE' and collection['export_status']=='PASS','PROFILE_STATUS')
    require(collection.get('error') in (None,'MODEL_A_SCOPE_BLOCKED'),'PROFILE_ERROR')
    return dict(schema_version='gate8-pair-observation/0.1',status='PAIR_OBSERVED_NOT_ACCEPTANCE',gate8_verdict='NOT_RUN',
        pair_id=ma['engineering_pair']['pair_id'],clock='PYTHON_PERF_COUNTER_NS',order=['pass0','pass1'],
        timing='host_observed request start to host-readable token completion; no cross-process timestamp subtraction',
        overhead=overhead(a['timing_ns'],b['timing_ns']),pass0=a,pass1=b,
        statistical_stability='NOT_ASSESSED',output_token_value_parity='NOT_RECORDED_COUNT_ONLY',
        includes='profiler and instrumentation perturbation plus uncontrolled single-pair run variation',
        excludes='load, warmup, drain, cleanup, process launch and export')


def main():
    parser=argparse.ArgumentParser(description=__doc__); sub=parser.add_subparsers(dest='command',required=True)
    run=sub.add_parser('baseline')
    for name in ('python','prepared','output'): run.add_argument('--'+name,required=True,type=Path)
    authorization=run.add_mutually_exclusive_group(required=True)
    authorization.add_argument('--execute-engineering-baseline',action='store_true')
    authorization.add_argument('--execute-pilot-baseline',action='store_true')
    summary=sub.add_parser('summarize')
    for name in ('pass0','pass1','output'): summary.add_argument('--'+name,required=True,type=Path)
    args=parser.parse_args()
    if args.command=='baseline':
        manifest=read(args.prepared/'manifest.json')
        require(args.execute_pilot_baseline==('pilot' in manifest),'PILOT_OPT_IN')
    if args.command=='baseline':
        result=baseline(args.python,args.prepared,args.output)
        print(result['status']); return 0 if result['status']=='BASELINE_COMPLETE_NOT_ACCEPTANCE' else 1
    result=summarize(args.pass0,args.pass1); write_new(args.output,result); print(result['status']); return 0


if __name__=='__main__': raise SystemExit(main())
