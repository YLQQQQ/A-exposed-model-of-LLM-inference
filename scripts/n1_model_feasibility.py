"""Only V0/Vmarker/V16, 32/2, one request each; no effect/Pilot inference."""
import argparse
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from exposedpath.gate8_isolated_preflight import read,sha,write_new

VERSION='N1-MODEL-FEASIBILITY/0.1'
VARIANTS=('V0','Vmarker','V16')


def require(ok,reason):
    if not ok: raise ValueError('N1_FEASIBILITY_'+reason)


def run_groups(output,run_group):
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    result=dict(version=VERSION,status='BLOCKED',n1_model_feasibility='NOT_RUN',role='Engineering',
        automatic_retry=False,groups=[dict(variant=v,status='NOT_RUN') for v in VARIANTS])
    reference=None
    for row in result['groups']:
        try:
            value=run_group(row['variant'],output/row['variant']); row.update(value)
            if row['status']!='FEASIBLE_ONCE_PENDING_REVIEW': break
            common=dict(contract=value['common_identity'],tokens=value['observed_tokens'])
            require(reference is None or common==reference,'GROUP_CONTRACT_OR_TOKEN_PARITY')
            reference=common
        except Exception as exc:
            row.update(status='BLOCKED',error=f'{type(exc).__name__}: {exc}')
            break
    else: result['status']='BATCH_COMPLETE_PENDING_REVIEW'
    write_new(output/'batch_report.json',result)
    return result


def collect_group(variant,path,c):
    from exposedpath.gate8_diagnostic import prepare_diagnostic
    from scripts.gate8_diagnostic_collect import run_once
    from scripts.gate8_pair import inspect_execution
    from scripts.gate10_feasibility import failure_kind
    from exposedpath_v141.gate8_adapter import normalized_pci,normalized_uuid
    require(variant in VARIANTS,'VARIANT')
    path.mkdir(parents=True,exist_ok=False)
    prompt=Path(c['prompt'])
    require(sha(prompt)==c['prompt_sha256'],'INPUT_HASH')
    prepared=prepare_diagnostic(output_dir=path/'prepared',model_path=c['model'],
        inventory_path=c['inventory'],inventory_sha256=c['inventory_sha256'],
        prompt_path=prompt,prompt_sha256=c['prompt_sha256'],expected_commit=c['commit'],physical_gpu=3,
        engineering_attention_backend='sdpa',target_python=c['target_python'],site_root=c['site_root'],n1_variant=variant)
    manifest=read(prepared/'manifest.json')
    require(normalized_uuid(manifest['gpu_uuid'])==normalized_uuid(c['gpu_uuid'])
        and normalized_pci(manifest['gpu_pci_bus_id'])==normalized_pci(c['gpu_pci_bus_id']),'DEVICE')
    out=path/'collection'
    process=run_once([sys.executable,str(ROOT/'scripts/gate8_diagnostic_collect.py'),
        '--nsys',c['nsys'],'--python',c['target_python'],'--prepared',str(prepared),
        '--output',str(out),'--execute-engineering-diagnostic','--engineering-domain'],path/'driver',timeout_seconds=900)
    report=read(out/'collection_report.json') if (out/'collection_report.json').is_file() else None
    if process['status']!='COMPLETE' or report is None or report.get('error') or report.get('status')!='N1_MODEL_ENGINEERING_ONLY':
        return dict(status='BLOCKED',failure_kind=failure_kind(out,process),process=process,collection_report=report)
    actual=inspect_execution(out,'pass1')
    domain_path=out/'analyzed/domain.json'; domain=read(domain_path)
    require(report['result_filename']=='domain.json' and report['result_sha256']==sha(domain_path)
        and domain['adapter_version']=='exposedpath-n1-model-ownership/0.1.0'
        and domain['status']=='QUALITY_CHECK_PASSED_NOT_QUALIFICATION','DOMAIN_RESULT')
    calls=read(out/'diagnostic/n1_model_calls.json')['requests'][1]
    common={k:manifest[k] for k in ('model_id','prompt_tokens_sha256','fixed_input_tokens','fixed_output_tokens',
        'batch_size','warmup_count','repeat_count','execution_mode','attention_backend','dtype_and_quantization',
        'sampling_config','runner_git_commit','runner_source_sha256','gpu_index_physical','gpu_index_logical','gpu_uuid','gpu_pci_bus_id')}
    common['inventory_sha256']=manifest['model_content_snapshot']['inventory_sha256']
    common['stream_policy']=manifest['n1_model']['stream_policy']
    common['execution_policy']=manifest['n1_model_execution']
    common['target_snapshot']=manifest['target_python']['actual']['snapshot']
    return dict(status='FEASIBLE_ONCE_PENDING_REVIEW',actual_input_tokens=calls['actual_input_tokens'],
        actual_output_tokens=len(calls['observed_tokens']),observed_tokens=calls['observed_tokens'],
        observed_intervention_count=len(calls['interventions']),
        observed_sync_count=sum(i['synchronize_called'] for i in calls['interventions']),
        common_identity=common,manifest_sha256=actual['manifest_sha256'],domain_sha256=sha(domain_path),
        host_timing_ns=actual['timing_ns'],dropped_records_status='UNKNOWN',measurement_validity='NOT_ASSESSED')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',required=True,type=Path); p.add_argument('--output',required=True,type=Path)
    p.add_argument('--execute-reviewed-feasibility',required=True,action='store_true')
    a=p.parse_args(); c=read(a.config)
    return 0 if run_groups(a.output,lambda v,path:collect_group(v,path,c))['status']=='BATCH_COMPLETE_PENDING_REVIEW' else 1


if __name__=='__main__': raise SystemExit(main())
