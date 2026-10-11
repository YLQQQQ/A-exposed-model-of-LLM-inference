"""Four prospective Engineering processes; existing verified entry and analysis."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from exposedpath import batch_load as contract
from exposedpath.gate8_isolated_preflight import read,sha,write_new


def check_profile_admission(result):
    if (result['status']=='A_SCOPE_ENGINEERING_ONLY' and result.get('error') is None
            and 'analysis_rejection' not in result):
        return
    # Keep the failure type and upstream reason instead of reducing a completed
    # capture / rejected request to the outer generic PROFILE_ADMISSION label.
    details={k:result[k] for k in ('status','error','analysis_rejection') if k in result}
    raise ValueError('BATCH_LOAD_PROFILE_ADMISSION:'+json.dumps(details,sort_keys=True))


def sync_evidence(records,proof):
    """Report an already admitted G1 suffix proof, not a physical B assertion."""
    from exposedpath_v141.activity_baseline import union
    syncs=[s for s in records['cuda_sync'] if s['record_id']==proof['sync_id']]
    contract.require(len(syncs)==1,'REPORT_SYNC_REFERENCE');s=syncs[0]
    apis=[a for a in records['cuda_api'] if a['record_id']==s['runtime_record_id']]
    contract.require(len(apis)==1,'REPORT_API_REFERENCE');a=apis[0]
    members=[r for r in records['device_activity'] if r['record_id'] in proof['suffix_activity_ids']]
    contract.require(len(members)==len(set(proof['suffix_activity_ids'])),'REPORT_MEMBER_REFERENCE')
    intervals=[(max(a['start_ns'],r['start_ns']),min(a['end_ns'],r['end_ns'])) for r in members
               if r['start_ns']<a['end_ns'] and a['start_ns']<r['end_ns']]
    markers=[r for r in records['nvtx'] if (r.get('text') or '').startswith('EXPOSEDPATH_JSON_V1:')
             and json.loads(r['text'].split(':',1)[1]).get('kind')=='sync'
             and r['start_ns']<=a['start_ns'] and r.get('end_ns') is not None and a['end_ns']<=r['end_ns']]
    return dict(sync_record_id=s['record_id'],runtime_api=a,physical_sync=s,
        host_api_duration_ns=a['end_ns']-a['start_ns'],necessary_activity_ids=proof['suffix_activity_ids'],
        dependency_scope=proof['scope'],last_necessary_activity_end_ns=max((r['end_ns'] for r in members),default=None),
        supported_device_wait_union_ns=union(intervals),sync_markers=markers,
        internal_api_wait='NOT_IDENTIFIABLE_NOT_SPLIT',physical_b_qualified=False)


def report_profile(output):
    """Consume the just-verified saved domain, retaining source references."""
    from exposedpath_v141.sync_semantics import load_canonical_bundle
    from exposedpath_v141.gate8_scope import load_projected_ownership
    from exposedpath_v141.activity_baseline import calculate,_driver_records
    from exposedpath_v141.a_api_classification import OPAQUE_VERSION
    output=Path(output);collection=read(output/'collection_report.json')
    path=output/'analyzed/domain.json'
    contract.require(collection.get('error') is None and collection.get('result_sha256')==sha(path),'REPORT_DOMAIN_HASH')
    result=read(path)
    contract.require(result['status']=='QUALITY_CHECK_PASSED_NOT_QUALIFICATION' and len(result['requests'])==1,'REPORT_ADMISSION')
    request=result['requests'][0];facts=request['facts'];proofs=facts['conditional_suffix_proofs']
    contract.require(len(proofs)==2 and proofs[0]['syncs']==proofs[1]['syncs'],'REPORT_DEPENDENCY_PROOFS')
    bundle=load_canonical_bundle(output/'analyzed/canonical/canonical_manifest.json')
    _,projections=load_projected_ownership(output/'analyzed/canonical/canonical_manifest.json',bundle,
        output/'analyzed/projection/scope.json')
    records=bundle['records'];apis=records['cuda_api'];drivers,driver_status=_driver_records(output/'capture.sqlite')
    owned=set(facts['observed_api_ids'])|{i for s in proofs[0]['syncs'] for i in s['suffix_activity_ids']}
    # Optional driver records retain UNKNOWN ownership; never infer it from nesting.
    drain_api=next(a for a in apis if a['record_id']==facts['drain_api_id'])
    windows=[]
    for a in request['a_records']:
        p=next(p for p in projections if p['phase']==a['phase'] and p['identity']==request['identity'])
        scope=dict(p,process_id=drain_api['process_id'],thread_id=drain_api['thread_id'])
        baseline=calculate(apis+drivers,records['device_activity'],scope,owned,registry_version=OPAQUE_VERSION)
        baseline.pop('timeline')
        if driver_status!='OBSERVED_TABLE':
            baseline['driver_api']=dict(count=None,sum_ns=None,union_ns=None,status=driver_status)
        copies=[r for r in apis+drivers if 'Memcpy' in r['api_name'] and r['process_id']==scope['process_id']
            and r['thread_id']==scope['thread_id'] and r['start_ns']<p['end_ns'] and p['start_ns']<r['end_ns']]
        windows.append(dict(phase=a['phase'],a=a,a_ratios={k:a[k]/a['T_window_ns'] if a['T_window_ns'] else None
            for k in ('A_device_wait_ns','A_cuda_api_ns','A_host_path_ns','A_sync_residual_ns','A_unattributed_ns')},
            activity_cost=baseline,copy_apis=copies,
            d2h_activities=[r for r in records['device_activity'] if r['record_id'] in owned
                and r['activity_kind']=='MEMCPY' and r.get('attributes',{}).get('copy_kind')==2
                and r['start_ns']<p['end_ns'] and p['start_ns']<r['end_ns']],
            completion_projection=p))
    return dict(schema_version='batch-load-observation/0.1.0',role='Engineering',
        domain_sha256=sha(path),input_receipt_sha256=sha(output/'input_receipt.json'),windows=windows,
        completion_anchors=read(output/'analyzed/projection/scope.json')['anchors'],
        synchronization=[sync_evidence(records,p) for p in proofs[0]['syncs']],driver_layer_status=driver_status,
        dropped_records_status='UNKNOWN',measurement_validity='NOT_ASSESSED',
        claim='SINGLE_CASE_DIAGNOSTIC_NOT_STATISTICAL_OR_FORMAL',
        device_wait='SUPPORTED_SYNC_NECESSARY_ACTIVITY_EXPOSURE_NOT_ALL_GPU_RELATED_HOST_BLOCKING',
        cuda_api='HOST_CALL_WALL_BUDGET_NOT_PURE_CPU; NON_SUBMIT_DOES_NOT_MEAN_NONBLOCKING')


def run(config,output,*,execute=False):
    contract.require(execute,'OPT_IN_REQUIRED')
    contract.require(config['schema_version']=='batch-load-delivery/0.1'
        and config['model_process_budget']==4 and config['profile_budget']==2,'BUDGET')
    from exposedpath.platform_adapter import git
    contract.require(git(['-C',str(ROOT),'rev-parse','HEAD']).strip()==config['commit']
        and not git(['-C',str(ROOT),'status','--porcelain']).strip(),'CLEAN_EXECUTION_COMMIT')
    contract.require(sha(config['nsys'])==config['nsys_sha256'].lower(),'COLLECTOR_HASH')
    out=Path(output);contract.require(not out.exists(),'OUTPUT_EXISTS');out.mkdir(parents=True)
    inputs=contract.make_inputs(config['seed_input'],config['prompt_512_sha256'],out/'inputs')
    from exposedpath.gate8_diagnostic import prepare_diagnostic
    from scripts.gate8_pair import baseline,summarize
    from scripts.gate8_diagnostic_collect import run_once
    pairs={};observations={}
    def collect(b,folder):
        folder.mkdir();prompt=inputs[0 if b['batch_size']==1 else 1]
        print(f"[stage] prepare {b['condition']} {b['pass_id']}",flush=True)
        prepared=prepare_diagnostic(output_dir=folder/'prepared',model_path=config['model'],
            inventory_path=config['inventory'],inventory_sha256=config['inventory_sha256'],prompt_path=prompt,
            prompt_sha256=sha(prompt),expected_commit=config['commit'],physical_gpu=3,
            engineering_attention_backend='sdpa',target_python=config['target_python'],site_root=config['site_root'],batch_binding=b)
        manifest=read(prepared/'manifest.json')
        from exposedpath_v141.gate8_adapter import normalized_uuid,normalized_pci
        contract.require(normalized_uuid(manifest['gpu_uuid'])==normalized_uuid(config['gpu_uuid'])
            and normalized_pci(manifest['gpu_pci_bus_id'])==normalized_pci(config['gpu_pci_bus_id']),'PREPARED_GPU')
        output=folder/'collection';result={}
        if b['pass_id']=='pass0':
            result=baseline(config['target_python'],prepared,output)
            contract.require(result['status']=='BASELINE_COMPLETE_NOT_ACCEPTANCE','BASELINE')
            pairs[b['condition']]=output
        else:
            argv=[str(Path(config['code_root'])/'.venv/Scripts/python.exe'),'-X','utf8','-u',str(ROOT/'scripts/gate8_diagnostic_collect.py'),
                '--nsys',config['nsys'],'--python',config['target_python'],'--prepared',str(prepared),
                '--output',str(output),'--execute-engineering-diagnostic','--engineering-a-only']
            process=run_once(argv,folder/'driver',timeout_seconds=900,progress=True)
            contract.require(process['status']=='COMPLETE','PROFILE_DRIVER')
            result=read(output/'collection_report.json')
            check_profile_admission(result)
            print(f"[stage] pair_and_observation {b['condition']}",flush=True)
            pair=summarize(pairs[b['condition']],output);write_new(folder/'pair.json',pair)
            observation=report_profile(output);write_new(folder/'observation.json',observation)
            observations[b['condition']]=dict(pair=pair,observation=observation)
        return dict(status='RUN_COMPLETE_PENDING_REVIEW',collection=str(output),manifest_sha256=sha(prepared/'manifest.json'))
    report=contract.run_batch(config['batch_id'],out/'batch',collect)
    if report['status']=='BATCH_COMPLETE_STOP_FOR_REVIEW':
        # No statistical claim or prescribed direction. Preserve both absolute values and signed deltas.
        write_new(out/'comparison.json',dict(version=contract.VERSION,role='Engineering',conditions=observations,
            batch4_minus_batch1_host_ns={p:{phase:observations['B4']['pair'][p]['timing_ns'][phase]-
                observations['B1']['pair'][p]['timing_ns'][phase] for phase in ('full_request','prefill','decode')}
                for p in ('pass0','pass1')},statistical_stability='NOT_ASSESSED'))
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--execute-reviewed-engineering-batch',action='store_true')
    a=p.parse_args();r=run(read(a.config),a.output,execute=a.execute_reviewed_engineering_batch)
    print(r['status'],flush=True);return 0 if r['status']=='BATCH_COMPLETE_STOP_FOR_REVIEW' else 1


if __name__=='__main__':raise SystemExit(main())
