"""One bounded Engineering collection. No scientific analyzer or automatic retry."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


class ModelScopeBlocked(ValueError):
    """Preserve rejected analysis provenance without changing admission or Raw."""
    def __init__(self, result, value):
        from exposedpath.gate8_diagnostic import _sha
        super().__init__('MODEL_A_SCOPE_BLOCKED')
        self.details=dict(version='model-scope-rejection/0.1.0',
            result_filename=Path(result).name,result_sha256=_sha(result),
            status=value['status'],requests=[{k:r[k] for k in ('identity','status','reasons') if k in r}
                for r in value['requests']])


def check_model_admission(result, value, *, domain):
    wanted='QUALITY_CHECK_PASSED_NOT_QUALIFICATION' if domain else 'A_SCOPE_ENGINEERING_ONLY'
    if value['status']!=wanted or len(value['requests'])!=1:
        raise ModelScopeBlocked(result,value)


def record_analysis_error(report, exc):
    report['error']=str(exc)
    if isinstance(exc,ModelScopeBlocked):
        report['analysis_rejection']=exc.details


def run_once(argv, output, *, timeout_seconds=300, progress=False):
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    report=dict(argv=list(argv),attempt_count=1,status='BLOCKED',timed_out=False,
                pid=None,exit_code=None,descendant_exit_status='NOT_OBSERVED')
    started=time.monotonic()
    def persist():
        pending=output/'process.pending.json'
        with pending.open('w',encoding='utf-8') as handle:
            json.dump(report,handle,indent=2)
            handle.flush(); os.fsync(handle.fileno())
        pending.replace(output/'process.json')
    persist()
    process=None
    try:
        with (output/'stdout.txt').open('xb') as stdout, (output/'stderr.txt').open('xb') as stderr:
            process=subprocess.Popen(argv,stdout=stdout,stderr=stderr,shell=False,cwd=ROOT)
            report['pid']=process.pid
            persist()
            try:
                if not progress:
                    report['exit_code']=process.wait(timeout=timeout_seconds)
                else:
                    deadline=time.monotonic()+timeout_seconds
                    with (output/'stdout.txt').open('rb') as visible:
                        def display():
                            # Display only; persisted bytes are authoritative and
                            # never decoded/replaced for an identity check.
                            text=visible.read().decode('utf-8',errors='backslashreplace')
                            if text:
                                try: print(text,end='',flush=True)
                                except (OSError,UnicodeError): pass
                        while True:
                            remaining=deadline-time.monotonic()
                            if remaining<=0: raise subprocess.TimeoutExpired(argv,timeout_seconds)
                            try:
                                report['exit_code']=process.wait(timeout=min(20,remaining))
                                display(); break
                            except subprocess.TimeoutExpired:
                                display()
                                print(f'[progress] active pid={process.pid} elapsed={time.monotonic()-started:.1f}s',flush=True)
            except subprocess.TimeoutExpired:
                report['timed_out']=True
                process.kill()  # Only the recorded launcher, never a name-wide kill.
                report['exit_code']=process.wait(timeout=10)
                report['descendant_exit_status']='UNKNOWN_STOP_AND_INSPECT_NO_RETRY'
            if report['exit_code']==0 and not report['timed_out']:
                report['status']='COMPLETE'
    except (OSError,subprocess.TimeoutExpired) as exc:
        report['error']=f'{type(exc).__name__}: {exc}'
        if process is not None and process.poll() is None:
            report['descendant_exit_status']='UNKNOWN_STOP_AND_INSPECT_NO_RETRY'
            try:
                process.kill()
                report['exit_code']=process.wait(timeout=10)
            except (OSError,subprocess.TimeoutExpired) as stop_error:
                report['stop_error']=str(stop_error)
    report['elapsed_seconds']=time.monotonic()-started
    try:
        persist()
    except OSError as exc:
        report.update(status='BLOCKED',receipt_write_error=str(exc))
        print(json.dumps(report),file=sys.stderr)
    return report


def target_argv(python,prepared,output,root=ROOT):
    prepared,output=Path(prepared),Path(output)
    args=['--manifest-path',str(prepared/'manifest.json'),'--prompt-path',str(prepared/'prompt.json'),
        '--preflight-path',str(prepared/'preflight.json'),'--project-root',str(root),
        '--output-dir',str(output/'diagnostic')]
    manifest=prepared/'manifest.json'
    value=json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else {}
    if 'isolated_preflight_version' in value:
        from exposedpath import gate8_isolated_preflight as isolated
        receipt=output/'auxiliary_preflight.json'
        if value['isolated_preflight_version']!=isolated.VERSION or not receipt.is_file():
            raise ValueError('ISOLATED_PREFLIGHT_REQUIRED_BEFORE_PROFILE')
        sealed=isolated.read(receipt)
        if sealed['run_id']!=value['run_id'] or sealed['output_root']!=str(output.resolve()):
            raise ValueError('ISOLATED_PREFLIGHT_LAUNCH_CONFLICT')
        args+=['--auxiliary-receipt',str(receipt.resolve()),'--auxiliary-sha256',isolated.sha(receipt),
               '--launch-nonce',sealed['nonce']]
    if 'target_python' in value:
        from exposedpath_v141.gate8_target_python import argv,validate_probe
        target=validate_probe(value['target_python'])
        if str(Path(python).resolve())!=target['requested_executable']:
            raise ValueError('TARGET_PYTHON_ARGUMENT')
        command=argv(python,target['site_root'],['model-run',*args])
    else:
        command=[str(python),'-m','exposedpath.gate8_diagnostic','run',*args]
    return command


def profile_argv(nsys,python,prepared,output,root=ROOT):
    from exposedpath.gate8_diagnostic import measurement_pass
    manifest=Path(prepared)/'manifest.json'
    if manifest.exists() and measurement_pass(json.loads(manifest.read_text(encoding='utf-8')))!='pass1':
        raise ValueError('ENGINEERING_PAIR_PROFILE_PASS')
    kill='true' if sys.platform=='win32' else 'sigkill'
    from exposedpath.memset_prefill import active as parameter_active
    duration=300 if manifest.exists() and parameter_active(json.loads(manifest.read_text(encoding='utf-8')).get('batch_load')) else 120
    return [str(nsys),'profile','--trace=cuda,nvtx','--sample=none','--cpuctxsw=none',
        '--cuda-memory-usage=false','--cuda-trace-scope=process-tree','--isr=false',
        '--duration='+str(duration),'--kill='+kill,'--output='+str(output/'capture'),
        *target_argv(python,prepared,output,root)]


def analyze_receipt(manifest,receipt,execution,output):
    from exposedpath import coe_pilot
    from exposedpath.memset_prefill import active as parameter_active
    if parameter_active(manifest.get('batch_load')):
        r=run_once([sys.executable,'-X','utf8','-u','-m','analysis.memset_prefill','--receipt',str(receipt),
            '--execution',str(execution),'--output',str(output)],Path(output).with_name(Path(output).name+'_parameters_driver'),
            timeout_seconds=300,progress=True)
        if r['status']!='COMPLETE' or r['timed_out'] or r['exit_code']!=0:raise ValueError('PARAMETER_OFFLINE_DRIVER_FAILED_SEE_ORIGINAL_LOG')
        result=Path(output)/'parameters.json'
        value=json.loads(result.read_text(encoding='utf8'))
    elif coe_pilot.active(manifest.get('pilot')):
        from analysis.coe_pilot import process
        result=process(receipt,execution,output)
        value=json.loads(result.read_text(encoding='utf8'))
    elif 'completion_path' in manifest:
        from exposedpath_v141.completion_path_scope import process,load
        result=process(receipt,execution,output)
        value=load(result,receipt,execution)
    elif 'domain_qualification' in manifest:
        from exposedpath_v141.gate9_domain import process_domain,load_domain,declaration,G1,N1
        options={}
        if 'n1_model' in manifest:
            from exposedpath.n1_model import validate_manifest
            validate_manifest(manifest)
            options['bridge_path']=Path(execution).parent/'n1_model_calls.json'
        elif manifest['domain_qualification']!=declaration(G1):
            raise ValueError('MODEL_DOMAIN_DECLARATION')
        result=process_domain(receipt,execution,output,**options)
        from exposedpath_v141.gate9_domain import analysis_stage
        with analysis_stage('result_reload_validation'):
            value=load_domain(result,receipt,execution,**options)
    else:
        from exposedpath_v141.gate8_engineering_scope import process_engineering_scope,load_engineering_scope
        result=process_engineering_scope(receipt,execution,output)
        value=load_engineering_scope(result,receipt,execution)
    return result,value


def analyze_model(output,prepared,collector_version):
    """Bind target runtime/producer/trace before entering existing A-only gate."""
    from exposedpath_v141.gate8_target_python import bind_producer,bind_trace_launch
    from exposedpath_v141.gate8_files import write_input_receipt
    from exposedpath.gate8_diagnostic import _sha
    output=Path(output); root=output/'diagnostic'; prepared=Path(prepared)
    read=lambda p:json.loads(p.read_text(encoding='utf-8'))
    if _sha(root/'manifest.json')!=_sha(prepared/'manifest.json') or _sha(root/'prompt.json')!=_sha(prepared/'prompt.json'):
        raise ValueError('MODEL_PREPARED_IDENTITY')
    manifest=read(root/'manifest.json'); ledger=read(root/'producer/pass_identity.json')
    if 'isolated_preflight_version' in manifest:
        from exposedpath import gate8_isolated_preflight as isolated
        receipt=output/'auxiliary_preflight.json'
        sealed=read(receipt); claim=read(root/'isolated_preflight_target.json')
        final=read(output/'auxiliary_preflight.final.json')
        if (sealed['schema_version']!=isolated.VERSION or sealed['run_id']!=manifest['run_id']
                or claim!=read(output/'auxiliary_preflight.claim.json')
                or claim['target_pid']!=ledger['pid'] or claim['nonce']!=sealed['nonce']
                or claim['preflight_sha256']!=isolated.sha(receipt)
                or final!=dict(status='PASS',preflight_sha256=isolated.sha(receipt),
                    target_claim_sha256=isolated.sha(output/'auxiliary_preflight.claim.json'))):
            raise ValueError('ISOLATED_PREFLIGHT_TARGET_BINDING')
    bind_producer(manifest['target_python'],read(root/'target_runtime.json'),ledger['pid'])
    launch=bind_trace_launch(output/'capture.sqlite',ledger['pid'])
    with (output/'target_launch.json').open('x',encoding='utf-8') as handle:
        json.dump(launch,handle,indent=2)
    names={'preflight':'adapter_preflight.json','cuda_probe':'cuda_probe.json',
        'wmpc_manifest':'manifest.json','prompt':'prompt.json','runner_source':'runner_source.py',
        'producer_receipt':'producer/producer_receipt.json','pass_identity':'producer/pass_identity.json',
        'host_ledger':'producer/host_boundaries.json','drain_ledger':'producer/drain_ledger.json',
        'stage_ledger':'producer/stage_ledger.json'}
    if 'pilot' in manifest:
        names['pilot_tokens']='pilot_tokens.json'
    if 'formal' in manifest:
        names['formal_tokens']='formal_tokens.json'
    if 'batch_load' in manifest:
        names['batch_tokens']='batch_tokens.json'
    receipt=write_input_receipt(output/'input_receipt.json',collector_version=collector_version,
        capture_session_id=manifest['run_id'],artifacts=dict(raw=output/'capture.nsys-rep',
        sqlite=output/'capture.sqlite',export_report=output/'postprocess_report.json',
        **{k:root/v for k,v in names.items()}))
    result,value=analyze_receipt(manifest,receipt,root/'engineering_execution.json',output/'analyzed')
    from exposedpath.coe_pilot import active
    from exposedpath.memset_prefill import active as parameter_active
    if parameter_active(manifest.get('batch_load')):
        if value['status']!='MEMSET_PREFILL_EVIDENCE_COMPLETE_PENDING_REVIEW':raise ValueError('PARAMETER_SCOPE_BLOCKED')
    elif active(manifest.get('pilot')):
        if value['status']!='COE_PILOT_PREFILL_ONLY_PENDING_REVIEW':raise ModelScopeBlocked(result,value)
    elif 'completion_path' in manifest:
        if value['status']!='PREFILL_LOCAL_ENGINEERING_ONLY':raise ModelScopeBlocked(result,value)
    else:check_model_admission(result,value,domain='domain_qualification' in manifest)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('nsys','python','prepared','output'):
        parser.add_argument('--'+name,required=True,type=Path)
    parser.add_argument('--execute-engineering-diagnostic',action='store_true',required=True)
    parser.add_argument('--engineering-a-only','--engineering-domain',dest='engineering_a_only',action='store_true')
    parser.add_argument('--pilot',action='store_true',help='Require prospective G11 Pilot declaration (no role relabelling)')
    parser.add_argument('--signed-formal-protocol',action='store_true',help='Explicit opt-in; exact external human approval is required')
    parser.add_argument('--memset-prefill-parameters',action='store_true',help='Explicit one-new-B2 Engineering parameter diagnostic only')
    args=parser.parse_args()
    if args.pilot and not args.engineering_a_only:
        raise ValueError('PILOT_DOMAIN_ENTRY_REQUIRED')
    if args.signed_formal_protocol and (args.pilot or not args.engineering_a_only):
        raise ValueError('FORMAL_DOMAIN_ENTRY_REQUIRED')
    if args.memset_prefill_parameters and (not args.engineering_a_only or args.pilot or args.signed_formal_protocol):
        raise ValueError('PARAMETER_DOMAIN_ENTRY_REQUIRED')
    output=args.output.resolve()
    if output.exists(): raise FileExistsError(output)
    if not args.engineering_a_only and args.python.resolve()!=(ROOT/'.venv/Scripts/python.exe').resolve():
        raise ValueError('Explicit fixed checkout venv required')
    if not args.nsys.is_absolute() or not args.nsys.is_file():
        raise ValueError('Explicit Nsight executable required')
    if args.engineering_a_only:
        from exposedpath.gate8_engineering_contract import validate_declaration
        from exposedpath_v141.gate8_target_python import validate_probe,environment
        from exposedpath_v141.gate8_qualification import validate_tool_version
        manifest=json.loads((args.prepared/'manifest.json').read_text(encoding='utf-8'))
        validate_declaration(manifest)
        from exposedpath.memset_prefill import active as parameter_active
        if args.memset_prefill_parameters!=parameter_active(manifest.get('batch_load')):
            raise ValueError('PARAMETER_COLLECTION_OPT_IN_CONFLICT')
        if args.pilot != ('pilot' in manifest):
            raise ValueError('PILOT_COLLECTION_OPT_IN_CONFLICT')
        if args.signed_formal_protocol!=('formal' in manifest):
            raise ValueError('FORMAL_COLLECTION_OPT_IN_CONFLICT')
        if args.signed_formal_protocol:
            from exposedpath.formal_protocol import validate_prepared
            validate_prepared(manifest,args.prepared,ROOT)
        target=validate_probe(manifest['target_python'])
        if target['environment']!=environment() or str(args.python.resolve())!=target['requested_executable']:
            raise ValueError('TARGET_PYTHON_COLLECT_ENVIRONMENT')
        version=subprocess.run([str(args.nsys),'--version'],capture_output=True,text=True,timeout=20,check=True).stdout
        validate_tool_version(version)
        if 'isolated_preflight_version' in manifest:
            from exposedpath import gate8_isolated_preflight as isolated
            isolated.write_new(args.prepared/'collection_intent.json',dict(
                run_id=manifest['run_id'],output_root=str(output),collector_pid=os.getpid()))
    output.mkdir(parents=True,exist_ok=False)
    isolated_receipt=None
    if args.engineering_a_only and 'isolated_preflight_version' in manifest:
        from exposedpath import gate8_isolated_preflight as isolated
        isolated_receipt=isolated.seal(args.prepared,output,ROOT)
    from exposedpath_v141.gate9_domain import analysis_stage
    with analysis_stage('collection'):
        process=run_once(profile_argv(args.nsys.resolve(),args.python.resolve(),args.prepared.resolve(),output,ROOT),output/'collection_log')
    report=dict(status='BLOCKED',qualification='NOT_QUALIFIED',gate8_verdict='NOT_RUN',
                scientific_outputs_allowed=False,collection=process)
    if args.pilot:
        report.update(pilot=manifest['pilot'],run_role='PILOT',data_role='Pilot',gate11_verdict='NOT_RUN')
    if args.signed_formal_protocol:
        from exposedpath.formal_protocol import reference
        report.update(formal=manifest['formal'],formal_reference=reference(manifest['formal']),run_role='FORMAL',data_role='Formal')
    try:
        if process['status']!='COMPLETE': raise ValueError('Collection failed/timeout; no export or retry')
        if isolated_receipt is not None:
            isolated.finalize(isolated_receipt,args.prepared,ROOT)
            isolated.write_new(output/'auxiliary_preflight.final.json',dict(status='PASS',
                preflight_sha256=isolated.sha(isolated_receipt),
                target_claim_sha256=isolated.sha(output/'auxiliary_preflight.claim.json')))
        diagnostic=json.loads((output/'diagnostic/diagnostic_report.json').read_text(encoding='utf-8'))
        if (diagnostic['status']!='DIAGNOSTIC_COMPLETE' or diagnostic['qualification']!='NOT_QUALIFIED'
                or diagnostic['scientific_outputs_allowed'] is not False):
            raise ValueError('Incomplete or inconsistent producer diagnostic')
        from scripts.gate7_nsys_postprocess import run_postprocess
        with analysis_stage('sqlite_export_validation'):
            export=run_postprocess(nsys_exe=str(args.nsys),rep_path=output/'capture.nsys-rep',
                canonical_path=output/'capture.sqlite',report_path=output/'postprocess_report.json',max_attempts=1)
        report['export_status']=export['status']
        if export['status']!='PASS': raise ValueError('Single export failed; no retry')
        report['status']='DIAGNOSTIC_COLLECTED_NOT_QUALIFIED'
        if args.engineering_a_only:
            from exposedpath.gate8_diagnostic import _sha
            result=analyze_model(output,args.prepared,'2026.2.1.210')
            status=('PREFILL_LOCAL_ENGINEERING_ONLY' if 'completion_path' in manifest else
                'N1_MODEL_ENGINEERING_ONLY' if 'n1_model' in manifest else 'A_SCOPE_ENGINEERING_ONLY')
            report.update(status=status,result_sha256=_sha(result),
                result_filename=result.name,
                schema_version='gate8-qwen-engineering-collection/0.1.0',
                manifest_sha256=_sha(output/'diagnostic/manifest.json'),
                target_runtime_sha256=_sha(output/'diagnostic/target_runtime.json'),
                target_launch_sha256=_sha(output/'target_launch.json'),
                q0_status='NOT_RUN',dropped_records_status='UNKNOWN',measurement_validity='NOT_ASSESSED')
            if args.pilot:
                report.update(status='PILOT_RUN_COMPLETE_PENDING_REVIEW',schema_version='gate11-pilot-collection/0.1.0')
                from exposedpath.coe_pilot import active
                if active(manifest['pilot']):
                    report.update(status='COE_PILOT_PREFILL_ONLY_PENDING_REVIEW',schema_version='coe-pilot-collection/0.1.0')
            if args.signed_formal_protocol:
                report.update(status='FORMAL_RUN_COMPLETE_PENDING_REVIEW',schema_version='gate12-formal-collection/0.1.0')
            if args.memset_prefill_parameters:
                report.update(status='MEMSET_PREFILL_EVIDENCE_COMPLETE_PENDING_REVIEW',schema_version='memset-prefill-collection/0.1.0',
                    a_admission='NOT_ASSESSED',coe_admission='NOT_ASSESSED')
    except (ValueError,OSError,KeyError) as exc:
        record_analysis_error(report,exc)
        if args.memset_prefill_parameters:
            # This diagnostic requires the offline parameter evidence, not only
            # a successful capture/export. Do not retain the legacy exit0
            # diagnostic-only status after an analysis/result-file failure.
            report['status']='BLOCKED'
    (output/'collection_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(report['status'])
    return 0 if report['status'] in ('MEMSET_PREFILL_EVIDENCE_COMPLETE_PENDING_REVIEW','COE_PILOT_PREFILL_ONLY_PENDING_REVIEW','PREFILL_LOCAL_ENGINEERING_ONLY','DIAGNOSTIC_COLLECTED_NOT_QUALIFIED','A_SCOPE_ENGINEERING_ONLY','N1_MODEL_ENGINEERING_ONLY','PILOT_RUN_COMPLETE_PENDING_REVIEW','FORMAL_RUN_COMPLETE_PENDING_REVIEW') else 1


if __name__=='__main__': raise SystemExit(main())
