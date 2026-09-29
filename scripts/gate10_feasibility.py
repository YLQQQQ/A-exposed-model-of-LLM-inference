"""Two fixed G1 feasibility points, no retries, no Pilot statistics."""
import argparse
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from exposedpath.gate8_isolated_preflight import read,sha,write_new
from exposedpath.gate10_workload import LENGTHS,VERSION,require


def run_candidates(output,run_point,*,remaining_512_only=False):
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    result=dict(version=VERSION,status='BLOCKED',gate10_verdict='NOT_RUN',role='Engineering',
        automatic_retry=False,points=[dict(input_tokens=n,status='NOT_RUN') for n in ((512,) if remaining_512_only else LENGTHS)])
    for row in result['points']:
        try:
            value=run_point(row['input_tokens'],output/f"input_{row['input_tokens']}")
            row.update(value)
            if row['status']!='FEASIBLE_ONCE_NOT_STABILITY': break
        except Exception as exc:
            row.update(status='BLOCKED',failure_kind=('EXECUTION_CONTRACT_FAILURE' if isinstance(exc,ValueError)
                else 'EVIDENCE_OR_ANALYSIS_FAILURE' if isinstance(exc,FileNotFoundError)
                else 'UNCLASSIFIED_FAILURE'),error=f'{type(exc).__name__}: {exc}')
            break
    else: result['status']='BATCH_COMPLETE_PENDING_REVIEW'
    write_new(output/'batch_report.json',result)
    return result


def collect_point(n,path,c):
    from exposedpath.gate8_diagnostic import prepare_diagnostic
    from scripts.gate8_diagnostic_collect import run_once
    from scripts.gate8_pair import inspect_execution
    path.mkdir(parents=True,exist_ok=False)
    prompt=Path(c['input_root'])/f'input_{n}.json'
    require(sha(prompt)==c['input_hashes'][str(n)],'DELIVERY_INPUT_HASH')
    prepared=prepare_diagnostic(output_dir=path/'prepared',model_path=c['model'],
        inventory_path=c['inventory'],inventory_sha256=c['inventory_sha256'],
        prompt_path=prompt,prompt_sha256=c['input_hashes'][str(n)],expected_commit=c['commit'],
        physical_gpu=3,engineering_attention_backend='sdpa',target_python=c['target_python'],
        site_root=c['site_root'],gate10_input_tokens=n)
    manifest=read(prepared/'manifest.json')
    require(manifest['gpu_uuid'].lower()==c['gpu_uuid'].lower()
        and manifest['gpu_pci_bus_id'].lower()==c['gpu_pci_bus_id'].lower(),'DEVICE_CONFLICT')
    out=path/'collection'
    process=run_once([sys.executable,str(ROOT/'scripts/gate8_diagnostic_collect.py'),
        '--nsys',c['nsys'],'--python',c['target_python'],'--prepared',str(prepared),
        '--output',str(out),'--execute-engineering-diagnostic','--engineering-a-only'],path/'driver',timeout_seconds=900)
    report=read(out/'collection_report.json') if (out/'collection_report.json').is_file() else None
    if process['status']!='COMPLETE' or report is None or report.get('error') or report.get('status')!='A_SCOPE_ENGINEERING_ONLY':
        return dict(status='BLOCKED',failure_kind=failure_kind(out,process),
            process=process,collection_report=report)
    observed=inspect_execution(out,'pass1')
    raw=read(out/'diagnostic/workload_observed.json'); ledger=read(out/'diagnostic/producer/pass_identity.json')
    require(raw['schema_version']=='gate10-workload-observed/0.1'
        and raw['manifest_sha256']==observed['manifest_sha256']
        and raw['producer_receipt_sha256']==observed['producer_sha256']
        and raw['observations']==[dict(identity=ledger['requests'][1]['identity'],
            actual_input_tokens=n,actual_output_tokens=2,early_eos=False)],'ACTUAL_TOKEN_COUNTS')
    domain=read(out/'analyzed/domain.json')
    require(report['status']=='A_SCOPE_ENGINEERING_ONLY' and not report.get('error')
        and report['result_filename']=='domain.json' and report['result_sha256']==sha(out/'analyzed/domain.json')
        and domain['status']=='QUALITY_CHECK_PASSED_NOT_QUALIFICATION','DOMAIN_RESULT')
    return dict(status='FEASIBLE_ONCE_NOT_STABILITY',actual_input_tokens=n,actual_output_tokens=2,
        actual_input_basis='RUNNER_TENSOR_SHAPE',prompt_sha256=sha(prompt),
        manifest_sha256=observed['manifest_sha256'],domain_sha256=sha(out/'analyzed/domain.json'),
        host_timing_ns=observed['timing_ns'],dropped_records_status='UNKNOWN',measurement_validity='NOT_ASSESSED')


def failure_kind(output,process):
    if process.get('timed_out'): return 'TIMEOUT_UNRESOLVED'
    records=[]
    for name in ('diagnostic-entry/exit.json','diagnostic/producer/stage_ledger.json',
                 'diagnostic/producer/pass_identity.json'):
        p=Path(output)/name
        if p.is_file(): records.append(p.read_text(encoding='utf-8'))
    text='\n'.join(records)
    # Only an explicit producer exception type/message supports a resource verdict.
    if 'OutOfMemoryError' in text or 'CUDA out of memory' in text: return 'RESOURCE_INFEASIBLE'
    if 'EARLY_EOS_OR_OUTPUT_COUNT_MISMATCH' in text: return 'TOKEN_COUNT_EXCLUSION'
    report=Path(output)/'collection_report.json'
    if report.is_file():
        value=read(report)
        if value.get('collection',{}).get('timed_out'): return 'TIMEOUT_UNRESOLVED'
        if value.get('collection',{}).get('status')=='COMPLETE': return 'EVIDENCE_OR_ANALYSIS_FAILURE'
    return 'EXECUTION_FAILURE_UNRESOLVED'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',required=True,type=Path); p.add_argument('--output',required=True,type=Path)
    p.add_argument('--execute-reviewed-feasibility',required=True,action='store_true')
    p.add_argument('--remaining-512-only',action='store_true',help='New attempt for the unrun point only; requires prior 128 review, never resumes old output')
    a=p.parse_args(); c=read(a.config)
    return 0 if run_candidates(a.output,lambda n,path:collect_point(n,path,c),remaining_512_only=a.remaining_512_only)['status']=='BATCH_COMPLETE_PENDING_REVIEW' else 1


if __name__=='__main__': raise SystemExit(main())
