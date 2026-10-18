"""One explicitly requested source capture; never runs scientific admission."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def bind_capture(prepared,output):
    """Verify target/runtime/trace origin without entering S/A admission."""
    from exposedpath import memset_callsite as c,gate8_isolated_preflight as i
    from exposedpath_v141.gate8_target_python import bind_producer,bind_trace_launch
    prepared=Path(prepared);output=Path(output);d=output/'diagnostic'
    for name in ('manifest.json','prompt.json'):
        c.require(i.sha(d/name)==i.sha(prepared/name),'PREPARED_TARGET_BYTES:'+name)
    mf=i.read(d/'manifest.json');ledger=i.read(d/'producer/pass_identity.json')
    sealed=i.read(output/'auxiliary_preflight.json');claim=i.read(d/'isolated_preflight_target.json')
    c.require(claim==i.read(output/'auxiliary_preflight.claim.json') and claim['target_pid']==ledger['pid']
        and claim['nonce']==sealed['nonce'] and claim['preflight_sha256']==i.sha(output/'auxiliary_preflight.json')
        and sealed['run_id']==mf['run_id'],'ISOLATED_TARGET_BINDING')
    exited=i.read(output/'diagnostic-entry/exit.json')
    started=i.read(output/'diagnostic-entry/started.json')
    c.require(started['pid']==exited['pid']==ledger['pid'] and exited['status']=='EXITED' and exited['exit_code']==0,'TARGET_PID_EXIT')
    bind_producer(mf['target_python'],i.read(d/'target_runtime.json'),ledger['pid'])
    launch=bind_trace_launch(output/'capture.sqlite',ledger['pid']);i.write_new(output/'target_launch.json',launch)
    i.write_new(output/'auxiliary_preflight.final.json',dict(status='PASS',preflight_sha256=i.sha(output/'auxiliary_preflight.json'),
        target_claim_sha256=i.sha(output/'auxiliary_preflight.claim.json')))


def collect(nsys,python,prepared,output,root=ROOT):
    from exposedpath import memset_callsite as c,observation_preparation as prep,gate8_isolated_preflight as isolated
    from exposedpath_v141.gate8_target_python import validate_probe,environment
    from scripts.gate8_diagnostic_collect import run_once
    from scripts.gate7_nsys_postprocess import run_postprocess
    from analysis.memset_callsite import process
    prepared=Path(prepared).resolve();output=Path(output).resolve();root=Path(root).resolve()
    c.require(not output.exists(),'NO_OVERWRITE_RESUME_RETRY')
    manifest=isolated.read(prepared/'manifest.json')
    c.require(c.active(manifest.get('batch_load')),'EXPLICIT_SOURCE_ROLE')
    prep.validate_prepared(manifest,prepared,root)
    target=validate_probe(manifest['target_python'])
    c.require(target['requested_executable']==str(Path(python).resolve()) and target['environment']==environment(),'TARGET_PYTHON')
    output.mkdir(parents=True,exist_ok=False)
    report=dict(schema_version='memset-callsite-collection/0.1.0',status='BLOCKED',error=None,
        role='Engineering',model_process_budget=1,profile_budget=1,automatic_retry=False,
        scientific_outputs_allowed=False,parameter_evidence=False,a_admission='NOT_ASSESSED',coe_admission='NOT_ASSESSED')
    try:
        isolated.write_new(prepared/'collection_intent.json',dict(run_id=manifest['run_id'],output_root=str(output),collector_pid=os.getpid()))
        sealed=isolated.seal(prepared,output,root)
        argv=c.profile_argv(nsys,python,prepared,output,root)
        isolated.write_new(output/'profile_argv.json',argv)
        p=run_once(argv,output/'profile_log',timeout_seconds=300,progress=True);report['collection']=p
        c.require(p['status']=='COMPLETE' and p['exit_code']==0 and not p['timed_out'],'PROFILE_FAILED_NO_RETRY')
        isolated.finalize(sealed,prepared,root)
        exited=isolated.read(output/'diagnostic-entry/exit.json')
        c.require(exited['status']=='EXITED' and exited['exit_code']==0,'TARGET_EXIT')
        diagnostic=isolated.read(output/'diagnostic/diagnostic_report.json')
        c.require(diagnostic['status']=='DIAGNOSTIC_COMPLETE' and diagnostic['qualification']=='NOT_QUALIFIED'
            and diagnostic['scientific_outputs_allowed'] is False,'PRODUCER_COMPLETION')
        export=run_postprocess(nsys_exe=str(nsys),rep_path=output/'capture.nsys-rep',canonical_path=output/'capture.sqlite',
            report_path=output/'postprocess_report.json',max_attempts=1)
        report['export_status']=export['status'];c.require(export['status']=='PASS','EXPORT_FAILED_NO_RETRY')
        bind_capture(prepared,output)
        result=process(output/'capture.sqlite',output/'diagnostic',output/'analyzed');sources=isolated.read(result)
        report.update(result_sha256=isolated.sha(result),source_status=sources['status'])
        c.require(sources['token_ids']==[[29184],[6556]],'TOKEN_REFERENCE')
        c.require(sources['status']=='CALLSITE_LOCATED','SOURCE_QUERY:'+sources['status'])
        report['status']='CALLSITE_LOCATED_STOP_FOR_REVIEW'
    except (ValueError,OSError,KeyError) as exc:
        report['error']=type(exc).__name__+':'+str(exc)
    finally:
        closure=dict(status='BLOCKED',descendant_exit_status='UNKNOWN_STOP_AND_INSPECT_NO_RETRY')
        try:
            started=isolated.read(output/'diagnostic-entry/started.json')
            exited=isolated.read(output/'diagnostic-entry/exit.json')
            if type(started.get('pid')) is int and started['pid']==exited.get('pid') and exited.get('status')=='EXITED' and type(exited.get('exit_code')) is int:
                closure.update(status='EXITED',descendant_exit_status='TARGET_EXIT_OBSERVED',pid=started['pid'],exit_code=exited['exit_code'])
        except (ValueError,OSError,KeyError,TypeError):pass
        isolated.write_new(output/'target_closure.process.json',closure)
        if closure['status']!='EXITED':
            report['status']='BLOCKED'
            if report['error'] is None:report['error']='TARGET_EXIT_UNKNOWN_STOP_AND_INSPECT_NO_RETRY'
    isolated.write_new(output/'collection_report.json',report)
    print(report['status'],flush=True)
    return report


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('nsys','python','prepared','output'):p.add_argument('--'+n,required=True,type=Path)
    p.add_argument('--execute-reviewed-source-diagnostic',action='store_true',required=True)
    a=p.parse_args(argv);r=collect(a.nsys,a.python,a.prepared,a.output)
    return 0 if r['status']=='CALLSITE_LOCATED_STOP_FOR_REVIEW' else 1


if __name__=='__main__':raise SystemExit(main())
