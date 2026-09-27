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


def run_once(argv, output, *, timeout_seconds=300):
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
                report['exit_code']=process.wait(timeout=timeout_seconds)
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


def profile_argv(nsys,python,prepared,output,root=ROOT):
    prepared,output=Path(prepared),Path(output)
    # Nsight's Windows CLI accepts booleans, not POSIX signal names.
    kill='true' if sys.platform=='win32' else 'sigkill'
    return [str(nsys),'profile','--trace=cuda,nvtx','--sample=none','--cpuctxsw=none',
        '--cuda-memory-usage=false','--cuda-trace-scope=process-tree','--isr=false',
        '--duration=120','--kill='+kill,'--output='+str(output/'capture'),
        str(python),'-m','exposedpath.gate8_diagnostic','run',
        '--manifest-path',str(prepared/'manifest.json'),'--prompt-path',str(prepared/'prompt.json'),
        '--preflight-path',str(prepared/'preflight.json'),'--project-root',str(root),
        '--output-dir',str(output/'diagnostic')]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('nsys','python','prepared','output'):
        parser.add_argument('--'+name,required=True,type=Path)
    parser.add_argument('--execute-engineering-diagnostic',action='store_true',required=True)
    args=parser.parse_args()
    output=args.output.resolve()
    if output.exists(): raise FileExistsError(output)
    if args.python.resolve()!=(ROOT/'.venv/Scripts/python.exe').resolve():
        raise ValueError('Explicit fixed checkout venv required')
    if not args.nsys.is_absolute() or not args.nsys.is_file():
        raise ValueError('Explicit Nsight executable required')
    output.mkdir(parents=True,exist_ok=False)
    process=run_once(profile_argv(args.nsys.resolve(),args.python.resolve(),args.prepared.resolve(),output,ROOT),output/'collection_log')
    report=dict(status='BLOCKED',qualification='NOT_QUALIFIED',gate8_verdict='NOT_RUN',
                scientific_outputs_allowed=False,collection=process)
    try:
        if process['status']!='COMPLETE': raise ValueError('Collection failed/timeout; no export or retry')
        diagnostic=json.loads((output/'diagnostic/diagnostic_report.json').read_text(encoding='utf-8'))
        if (diagnostic['status']!='DIAGNOSTIC_COMPLETE' or diagnostic['qualification']!='NOT_QUALIFIED'
                or diagnostic['scientific_outputs_allowed'] is not False):
            raise ValueError('Incomplete or inconsistent producer diagnostic')
        from scripts.gate7_nsys_postprocess import run_postprocess
        export=run_postprocess(nsys_exe=str(args.nsys),rep_path=output/'capture.nsys-rep',
            canonical_path=output/'capture.sqlite',report_path=output/'postprocess_report.json',max_attempts=1)
        report['export_status']=export['status']
        if export['status']!='PASS': raise ValueError('Single export failed; no retry')
        report['status']='DIAGNOSTIC_COLLECTED_NOT_QUALIFIED'
    except (ValueError,OSError,KeyError) as exc:
        report['error']=str(exc)
    (output/'collection_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(report['status'])
    return 0 if report['status']=='DIAGNOSTIC_COLLECTED_NOT_QUALIFIED' else 1


if __name__=='__main__': raise SystemExit(main())
