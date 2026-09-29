"""One opt-in controlled bridge collection; fixed input, no model, no retries."""
import argparse
import json
from pathlib import Path
import sys
import traceback
import uuid

ROOT=Path(__file__).resolve().parents[1]
BOOT='import sys;sys.path[:0]=sys.argv[1:3];del sys.argv[1:3];from scripts.gate9_bridge_target import main;raise SystemExit(main())'


def profile_argv(nsys,python,site,plan,output):
    return [str(nsys),'profile','--trace=cuda,nvtx','--sample=none','--cpuctxsw=none',
        '--cuda-memory-usage=false','--cuda-trace-scope=process-tree','--isr=false',
        '--duration=120','--kill='+('true' if sys.platform=='win32' else 'sigkill'),
        '--output='+str(Path(output)/'capture'),str(python),'-I','-S','-c',BOOT,str(ROOT),str(site),
        '--plan',str(plan),'--output',str(Path(output)/'producer'),'--execute-controlled']


def main(argv=None):
    p=argparse.ArgumentParser()
    for name in ('python','site','nsys','library','commit','uuid','pci','output'): p.add_argument('--'+name,required=True)
    p.add_argument('--execute-controlled',action='store_true',required=True)
    a=p.parse_args(argv)
    from exposedpath_v141.gate8_files import _write, _json, _entry, write_input_receipt
    from exposedpath_v141.gate8_adapter import digest, normalized_uuid, normalized_pci
    from exposedpath_v141.gate8_controlled_cli import check_git
    from exposedpath_v141.gate8_target_python import probe, bind_producer, bind_trace_launch
    from exposedpath_v141.gate9_domain import declaration, N1, process_domain, load_domain
    from exposedpath_v141.gate8_qualification import validate_tool_version
    from exposedpath import platform_adapter
    from exposedpath.gate8_isolated_preflight import _git_paths
    from scripts.gate9_stream_probe_run import BINARIES
    from scripts.gate8_diagnostic_collect import run_once
    from scripts.gate7_nsys_postprocess import run_postprocess
    from scripts.gate9_bridge_target import require
    output=Path(a.output).resolve()
    output.mkdir(parents=True,exist_ok=False)
    report=dict(status='BLOCKED',error=None,gate9_verdict='NOT_RUN',attempt_count=1)
    try:
        check_git(a.commit)
        version=platform_adapter.query_tool(a.nsys,['--version']); validate_tool_version(version)
        _write(output/'tool.json',dict(version=version,path=str(Path(a.nsys).resolve()),sha256=digest(Path(a.nsys))))
        import os
        require(os.environ.get('CUDA_DEVICE_ORDER')=='PCI_BUS_ID' and os.environ.get('CUDA_VISIBLE_DEVICES')=='3','MASK')
        smi=platform_adapter.nvidia_smi(['-i','3','--query-gpu=index,uuid,pci.bus_id','--format=csv,noheader,nounits'])
        parts=[x.strip() for x in smi.split(',')]
        require(len(parts)==3 and parts[0]=='3' and normalized_uuid(parts[1])==normalized_uuid(a.uuid)
            and normalized_pci(parts[2])==normalized_pci(a.pci),'PREFLIGHT_GPU')
        pre=dict(gpu_index_physical=3,gpu_uuid=parts[1],pci_bus_id=parts[2],cuda_device_order='PCI_BUS_ID',cuda_visible_devices='3')
        binary_hashes={n:digest(Path(a.site)/'torch/lib'/n) for n in BINARIES}
        require(binary_hashes==BINARIES,'TORCH_BINARY_CHANGED')
        _write(output/'binary_identity.json',binary_hashes)
        target=probe(a.python,a.site)
        paths=_git_paths(ROOT,output,tracked=True)
        sources={n:digest(ROOT/n) for n in sorted(paths)}
        _write(output/'prompt.json',dict(request_tokens=[[0,1],[11,12]],warmup_count=0))
        run='gate9-bridge-'+uuid.uuid4().hex
        manifest=dict(experiment_id='gate9-explicit-bridge',wmpc_id='explicit-bridge-v1',run_id=run,
            run_role='ENGINEERING',data_role='Engineering',runner_git_commit=a.commit,runner_git_dirty=False,
            runner_source_sha256=digest(ROOT/'scripts/gate9_bridge_target.py'),prompt_tokens_sha256=digest(output/'prompt.json'),
            domain_qualification=declaration(N1),gpu_index_physical=3,gpu_index_logical=0,
            gpu_uuid=pre['gpu_uuid'],gpu_pci_bus_id=pre['pci_bus_id'])
        _write(output/'manifest.json',manifest)
        plan=dict(schema_version='gate9-bridge-plan/0.1.0',sources=sources,target_python=target,preflight=pre,
            library=dict(path=str(Path(a.library).resolve()),sha256=digest(Path(a.library))),
            manifest=_entry(output/'manifest.json',output),prompt=_entry(output/'prompt.json',output))
        _write(output/'plan.json',plan)
        process=run_once(profile_argv(a.nsys,a.python,a.site,output/'plan.json',output),output/'collection-log',timeout_seconds=150)
        report['process']=process
        require(process['status']=='COMPLETE' and process['exit_code']==0 and not process['timed_out'],'TARGET_FAILED_NO_RETRY')
        producer=output/'producer'; execution=_json(producer/'execution.json')
        require(execution['status']=='COMPLETE' and execution['error'] is None,'PRODUCER_FAILED')
        bind_producer(target,execution['runtime'],_json(producer/'pass_identity.json')['pid'])
        require(all(digest(ROOT/n)==h for n,h in sources.items()),'TREE_CHANGED')
        check_git(a.commit)
        require({n:digest(Path(a.site)/'torch/lib'/n) for n in BINARIES}==binary_hashes,'BINARY_CHANGED')
        rep=output/'capture.nsys-rep'; require(rep.is_file() and rep.stat().st_size>0,'REP_MISSING')
        export=run_postprocess(nsys_exe=a.nsys,rep_path=rep,canonical_path=output/'capture.sqlite',
            report_path=output/'export.json',max_attempts=1)
        require(export['status']=='PASS' and export['analyzer_allowed'],'EXPORT_FAILED_NO_RETRY')
        report['launch']=bind_trace_launch(output/'capture.sqlite',execution['pid'])
        artifacts={key:producer/name for key,name in dict(pass_identity='pass_identity.json',host_ledger='host_boundaries.json',
            drain_ledger='drain_ledger.json',producer_receipt='producer_receipt.json',preflight='preflight.json',
            cuda_probe='cuda_probe.json',wmpc_manifest='manifest.json',prompt='prompt.json',runner_source='runner_source.py').items()}
        artifacts.update(raw=rep,sqlite=output/'capture.sqlite',export_report=output/'export.json')
        receipt=write_input_receipt(output/'input.json',artifacts=artifacts,collector_version=version.replace('NVIDIA Nsight Systems version ',''),capture_session_id=run)
        _write(output/'n1-execution.json',dict(schema_version='exposedpath-n1-bridge-execution/0.1.0',
            input_receipt_sha256=digest(receipt),bridge_sha256=digest(producer/'bridge.json'),status='COMPLETE'))
        result=process_domain(receipt,output/'n1-execution.json',output/'analysis',bridge_path=producer/'bridge.json')
        value=load_domain(result,receipt,output/'n1-execution.json',bridge_path=producer/'bridge.json')
        from exposedpath_v141.gate9_bridge_oracle import check
        oracle=check(output/'capture.sqlite',producer,value)
        _write(output/'independent_oracle.json',oracle)
        report.update(status='BRIDGE_MATCH_REVIEW_REQUIRED',result_sha256=digest(result),oracle_sha256=digest(output/'independent_oracle.json'))
    except BaseException:
        report['error']=traceback.format_exc()
    _write(output/'collection_report.json',report)
    return 0 if report['status']=='BRIDGE_MATCH_REVIEW_REQUIRED' else 1


if __name__=='__main__': raise SystemExit(main())
