"""Explicit new controlled construction; never a model or automatic collection."""
from exposedpath.gate8_engineering_contract import PROFILE, CONSTRUCTION, ASSUMPTIONS
from exposedpath.gate8_engineering_contract import CONTROLLED_EXECUTION_VERSION
from .gate8_controlled_cli import NativeBackend as BaseBackend, check_git
from .gate8_adapter import digest, normalized_uuid, normalized_pci
from .gate8_files import _write, _entry, _resolve, _json
from pathlib import Path
from types import SimpleNamespace
import ctypes
import json
import os
import re
import shutil
import time

ROOT=Path(__file__).resolve().parents[1]
NATIVE=ROOT/'scripts/gate8_qualification_token.cu'
VERSION='exposedpath-controlled-qualification/0.1.0'

OP_PREFIX='EXPOSEDPATH_QUALIFICATION_OP_V1:'


def controlled_manifest_fields():
    return dict(construction=CONSTRUCTION,model_workload=False,execution_mode='controlled_native',
        engineering_scope=dict(profile=PROFILE,construction=CONSTRUCTION,
            assumptions=list(ASSUMPTIONS),declaration_role='PRE_EXECUTION'))


def operations(request_index=0):
    if type(request_index) is not int or request_index not in (0,1):
        raise ValueError('CONTROLLED_REQUEST_INDEX')
    token=11+10*request_index
    return [('submit',token),('internal_wait',None),('copy',None),('wait',None),
            ('read',token),('boundary',0),('submit',token+1),('copy',None),
            ('wait',None),('read',token+1),('boundary',1)]


def require(ok,reason):
    if not ok: raise ValueError('QUALIFICATION_'+reason)


class NativeBackend(BaseBackend):
    def __init__(self,library):
        abi=ctypes.CDLL(str(library))
        abi.ep_construction.argtypes=[]; abi.ep_construction.restype=ctypes.c_char_p
        require(abi.ep_construction()==CONSTRUCTION.encode(),'NATIVE_CONSTRUCTION')
        super().__init__(library)
        self.library.ep_stream_handle.argtypes=[]; self.library.ep_stream_handle.restype=ctypes.c_size_t
        self.library.ep_current_device.argtypes=[]; self.library.ep_current_device.restype=ctypes.c_int
        self.cuda=self; self.initialized=True
        self.nvtx=SimpleNamespace(range_push=self.push,range_pop=self.pop)
    def is_initialized(self): return self.initialized
    def current_device(self): return self.library.ep_current_device()
    def current_stream(self,device):
        return SimpleNamespace(device=SimpleNamespace(index=device),cuda_stream=int(self.library.ep_stream_handle()))
    default_stream=current_stream
    def close(self):
        super().close(); self.initialized=False


def prepare(output,preflight,library,commit,run_id):
    output=Path(output).resolve(); library=Path(library).resolve()
    if output.exists(): raise FileExistsError(output)
    check_git(commit)
    pre=json.loads(Path(preflight).read_text(encoding='utf-8-sig'))
    require(type(pre.get('gpu_index_physical')) is int and pre['gpu_index_physical']>=0
        and pre.get('cuda_device_order')=='PCI_BUS_ID'
        and pre.get('cuda_visible_devices')==str(pre['gpu_index_physical']),'MASK')
    normalized_uuid(pre.get('gpu_uuid')); normalized_pci(pre.get('pci_bus_id'))
    require(re.fullmatch('[A-Za-z0-9_.-]+',run_id) is not None and library.stat().st_size>0,'PLAN_INPUT')
    output.mkdir(parents=True)
    _write(output/'preflight.json',pre)
    _write(output/'prompt.json',dict(construction=CONSTRUCTION,operations=[operations(0),operations(1)],tokens=[[11,12],[21,22]]))
    shutil.copyfile(__file__,output/'runner_source.py')
    _write(output/'manifest.json',dict(**controlled_manifest_fields(),experiment_id='controlled-null-fifo',
        wmpc_id='controlled-null-fifo-v1',run_id=run_id,run_role='ENGINEERING',data_role='Engineering',
        runner_git_commit=commit,runner_git_dirty=False,runner_source_sha256=digest(Path(__file__)),
        prompt_tokens_sha256=digest(output/'prompt.json'),gpu_index_physical=pre['gpu_index_physical'],
        gpu_index_logical=0,gpu_uuid=pre['gpu_uuid'],gpu_pci_bus_id=pre['pci_bus_id']))
    _write(output/'plan.json',dict(schema_version=VERSION,construction=CONSTRUCTION,commit=commit,
        native_source_sha256=digest(NATIVE),library=dict(path=str(library),sha256=digest(library)),
        files={n:_entry(output/n,output) for n in ('preflight.json','prompt.json','runner_source.py','manifest.json')}))
    return output/'plan.json'


def read_plan(path,current=False):
    path=Path(path); plan=_json(path)
    require(plan.get('schema_version')==VERSION and plan.get('construction')==CONSTRUCTION,'PLAN_VERSION')
    require(set(plan['files'])=={'preflight.json','prompt.json','runner_source.py','manifest.json'},'PLAN_FILES')
    paths={n:_resolve(path.parent,v) for n,v in plan['files'].items()}
    manifest=_json(paths['manifest.json'])
    from exposedpath.gate8_engineering_contract import validate_declaration
    validate_declaration(manifest)
    pre=_json(paths['preflight.json'])
    require(type(pre.get('gpu_index_physical')) is int and pre['gpu_index_physical']>=0
        and pre.get('cuda_device_order')=='PCI_BUS_ID'
        and pre.get('cuda_visible_devices')==str(pre['gpu_index_physical'])
        and manifest.get('gpu_index_physical')==pre['gpu_index_physical']
        and manifest.get('gpu_index_logical')==0
        and normalized_uuid(manifest.get('gpu_uuid'))==normalized_uuid(pre.get('gpu_uuid'))
        and normalized_pci(manifest.get('gpu_pci_bus_id'))==normalized_pci(pre.get('pci_bus_id')),'PLAN_GPU_IDENTITY')
    require(manifest['runner_git_commit']==plan['commit'] and manifest['runner_git_dirty'] is False
        and manifest['runner_source_sha256']==digest(paths['runner_source.py'])
        and manifest['prompt_tokens_sha256']==digest(paths['prompt.json'])
        and _json(paths['prompt.json'])==dict(construction=CONSTRUCTION,
            operations=[[list(x) for x in operations(i)] for i in (0,1)],tokens=[[11,12],[21,22]]),'PLAN_BINDING')
    if current:
        check_git(plan['commit'])
        require(digest(Path(__file__))==digest(paths['runner_source.py'])
            and digest(NATIVE)==plan['native_source_sha256']
            and digest(Path(plan['library']['path']))==plan['library']['sha256'],'SOURCE_CHANGED')
        pre=_json(paths['preflight.json'])
        require(os.environ.get('CUDA_DEVICE_ORDER')=='PCI_BUS_ID'
            and os.environ.get('CUDA_VISIBLE_DEVICES')==str(pre['gpu_index_physical']),'MASK')
    return plan,paths,manifest


def execute(plan_path,output,*,backend_factory=NativeBackend,clock_ns=time.perf_counter_ns):
    from exposedpath.gate8_identity import make_gate8_pass_identity
    from exposedpath.gate8_boundary import Gate8BoundaryRecorder
    from exposedpath.gate8_drain import DrainRecorder
    from exposedpath.gate8_stages import StageRecorder
    output=Path(output).resolve()
    if output.exists(): raise FileExistsError(output)
    plan,paths,manifest=read_plan(plan_path,True)
    output.mkdir(parents=True)
    for name,path in paths.items(): shutil.copyfile(path,output/name)
    shutil.copyfile(plan_path,output/'plan.json')
    fields={k:manifest[k] for k in ('experiment_id','wmpc_id','run_id','run_role','data_role','runner_git_commit','runner_git_dirty')}
    fields.update(pid=os.getpid(),pass_id='pass1',attempt_id='qualification-1',
        runner_source_sha256=manifest['runner_source_sha256'],wmpc_manifest_sha256=digest(paths['manifest.json']),
        prompt_sha256=digest(paths['prompt.json']))
    entries=[dict(request_id='controlled-'+str(i),repeat_id=str(i),request_role='measured',
        expected_output_tokens=2,actual_output_tokens=0,early_eos=False,outcome='FAILED',reasons=['NOT_EXECUTED'],
        expected_boundary_ids=[manifest['run_id']+':'+str(i)+':'+str(j) for j in range(3)],observed_boundary_ids=[]) for i in range(2)]
    ledger=make_gate8_pass_identity(requests=entries,**fields)
    host=[]; drains=[]; observed=[]; backend=None; stage=None; error=None
    try:
        backend=backend_factory(Path(plan['library']['path']))
        device=backend.identity(); pre=_json(paths['preflight.json'])
        require(normalized_uuid(device['gpu_uuid'])==normalized_uuid(pre['gpu_uuid'])
            and normalized_pci(device['pci_bus_id'])==normalized_pci(pre['pci_bus_id']),'DEVICE')
        _write(output/'cuda_probe.json',dict(**device,pid=os.getpid(),gpu_index_logical=0,
            cuda_device_order='PCI_BUS_ID',cuda_visible_devices=os.environ['CUDA_VISIBLE_DEVICES']))
        stage=StageRecorder(ledger,0,backend.cuda,clock_ns,setup_observed=True)
        def warmup():
            backend.submit(0); backend.copy(); backend.wait()
            require(backend.read()==0,'WARMUP_TOKEN')
        stage.observe('setup',None,warmup)
        for i,entry in enumerate(ledger['requests']):
            identity=entry['identity']
            boundary=Gate8BoundaryRecorder(identity,entry['expected_boundary_ids'],clock_ns=clock_ns,marker_sink=backend.mark)
            drain=DrainRecorder(identity,identity['request_id']+':drain',0,clock_ns=clock_ns,push=backend.push,pop=backend.pop)
            def request():
                drain.observe(backend.prepare)
                boundary.observe(clock_ns())
                for ordinal,(name,value) in enumerate(operations(i)):
                    if name=='boundary': boundary.observe(clock_ns(),value); continue
                    payload=dict(construction=CONSTRUCTION,identity=identity,ordinal=ordinal,operation=name,value=value)
                    backend.push(OP_PREFIX+json.dumps(payload,sort_keys=True,separators=(',',':')))
                    try:
                        if name=='submit': backend.submit(value)
                        elif name in ('wait','internal_wait'): backend.wait()
                        elif name=='copy': backend.copy()
                        else:
                            actual=backend.read(); require(type(actual) is int and actual==value,'TOKEN')
                            observed.append(dict(identity=identity,ordinal=ordinal,token=actual))
                            entry['actual_output_tokens']+=1
                    finally: backend.pop()
                entry.update(outcome='COMPLETE',reasons=[])
            try: stage.observe('measured',identity,request)
            finally:
                host.extend(boundary.records); entry['observed_boundary_ids']=[r['payload']['boundary_id'] for r in boundary.records]
                if drain.record is not None: drains.append(drain.record)
    except BaseException as exc:
        error=type(exc).__name__+':'+str(exc)
    finally:
        if backend is not None:
            try: backend.close()
            except Exception as exc: error='CLEANUP:'+str(exc)
    status='COMPLETE' if error is None and all(r['outcome']=='COMPLETE' for r in ledger['requests']) else 'INCOMPLETE'
    artifacts={'pass_identity.json':ledger,'host_boundaries.json':host,
        'drain_ledger.json':dict(schema_version='exposedpath-drain-ledger/0.1.0',drains=drains),
        'stage_ledger.json':None if stage is None else stage.value}
    for name,value in artifacts.items(): _write(output/name,value)
    _write(output/'producer_receipt.json',dict(schema_version='exposedpath-gate8-producer-receipt/0.3.0',
        **{k:fields[k] for k in ('run_id','pass_id','attempt_id')},status=status,gate8_verdict='NOT_RUN',
        files={n:_entry(output/n,output) for n in artifacts}))
    _write(output/'engineering_execution.json',dict(schema_version=CONTROLLED_EXECUTION_VERSION,
        manifest_sha256=digest(output/'manifest.json'),producer_receipt_sha256=digest(output/'producer_receipt.json'),
        identity={k:fields[k] for k in ('run_id','pass_id','attempt_id','pid')},declaration=manifest['engineering_scope'],
        observed_configuration=dict(construction=CONSTRUCTION,warmup_token=0,model_workload=False),status=status))
    _write(output/'execution.json',dict(schema_version=VERSION,status=status,error=error,observed_tokens=observed,
        plan_sha256=digest(Path(plan_path)),files={p.name:_entry(p,output) for p in output.iterdir() if p.is_file()},
        q0_status='NOT_RUN',gate8_verdict='NOT_RUN'))
    return output/'execution.json'


def validate_execution(plan_path,execution_path):
    plan_path=Path(plan_path); execution_path=Path(execution_path); root=execution_path.parent
    read_plan(plan_path)
    execution=_json(execution_path)
    require(execution['schema_version']==VERSION and execution['status']=='COMPLETE' and execution['error'] is None
        and execution['plan_sha256']==digest(plan_path),'EXECUTION')
    require(set(execution['files'])=={'preflight.json','prompt.json','runner_source.py','manifest.json','plan.json',
        'cuda_probe.json','pass_identity.json','host_boundaries.json','drain_ledger.json','stage_ledger.json',
        'producer_receipt.json','engineering_execution.json'},'EXECUTION_FILE_SET')
    for name,item in execution['files'].items(): require(_resolve(root,item)==(root/name).resolve(),'EXECUTION_FILES')
    require(digest(root/'plan.json')==digest(plan_path),'EXECUTION_PLAN')
    read_plan(root/'plan.json')  # Bind copied inputs to original pre-execution hashes.
    return execution


def audit(plan_path,execution_path,sqlite,rep,export,output,collector_version):
    from .gate8_files import write_input_receipt
    from .gate8_engineering_scope import process_engineering_scope,load_engineering_scope
    from .gate8_qualification_oracle import check_raw,compare_components
    plan_path=Path(plan_path); execution_path=Path(execution_path); output=Path(output).resolve()
    if output.exists(): raise FileExistsError(output)
    validate_execution(plan_path,execution_path); root=execution_path.parent
    output.mkdir(parents=True)
    # Receipt must live above referenced source files; never copy or rewrite Raw.
    receipt=write_input_receipt(output.parent/(output.name+'-input.json'),collector_version=collector_version,
        capture_session_id=_json(root/'manifest.json')['run_id'],artifacts=dict(
        raw=Path(rep),sqlite=Path(sqlite),export_report=Path(export),
        **{k:root/v for k,v in dict(pass_identity='pass_identity.json',host_ledger='host_boundaries.json',
            producer_receipt='producer_receipt.json',drain_ledger='drain_ledger.json',stage_ledger='stage_ledger.json',
            preflight='preflight.json',cuda_probe='cuda_probe.json',wmpc_manifest='manifest.json',
            prompt='prompt.json',runner_source='runner_source.py').items()}))
    oracle=check_raw(sqlite,root)
    _write(output/'oracle.json',oracle)
    result=process_engineering_scope(receipt,root/'engineering_execution.json',output/'analyzed')
    actual=load_engineering_scope(result,receipt,root/'engineering_execution.json')
    require(actual['status']=='A_SCOPE_ENGINEERING_ONLY','A_SCOPE_BLOCKED')
    require(len(actual['requests'])==2,'A_REQUEST_COUNT')
    keys=('A_host_path_ns','A_cuda_api_ns','A_device_wait_ns','A_sync_residual_ns','A_unattributed_ns')
    for expected,got in zip(oracle['requests'],actual['requests']):
        require(expected['identity']==got['identity'],'A_IDENTITY')
        def canonical_id(kind,ref): return kind+':'+ref['table']+':'+str(ref['rowid'])
        members={canonical_id('cuda_sync',s['sync']):{
            canonical_id('device_activity',r) for r in s['members']} for s in expected['syncs']}
        proofs=got['facts']['conditional_suffix_proofs']
        require(len(proofs)==2 and {p['mode'] for p in proofs}=={'LEGACY','PER_THREAD'},'MODE_PROOFS')
        for proof in proofs:
            require(len(proof['syncs'])==3 and {s['sync_id']:set(s['suffix_activity_ids'])
                for s in proof['syncs']}==members,'SUFFIX_MEMBERSHIP')
        require({r['phase'] for r in got['a_records']}==set(expected['windows']),'A_WINDOWS')
        for row in got['a_records']: compare_components(expected['windows'][row['phase']],[row[k] for k in keys])
    _write(output/'qualification.json',dict(schema_version=VERSION,status='CONTROLLED_SCOPE_MATCH',oracle=oracle,
        execution_sha256=digest(execution_path),input_receipt_sha256=digest(receipt),analyzer_sha256=digest(result),
        q0_status='NOT_RUN',gate8_verdict='NOT_RUN',measurement_validity='NOT_ASSESSED',
        d_score_allowed=False,signature_allowed=False,qualification_scope='PENDING_INDEPENDENT_REAL_EVIDENCE_AUDIT'))
    return output/'qualification.json'


def profile_argv(nsys,python,plan,output):
    import sys
    return [str(nsys),'profile','--trace=cuda,nvtx','--sample=none','--cpuctxsw=none',
        '--cuda-memory-usage=false','--cuda-trace-scope=process-tree','--isr=false',
        '--duration=120','--kill='+('true' if sys.platform=='win32' else 'sigkill'),
        '--output='+str(Path(output)/'capture'),str(python),'-m','exposedpath_v141.gate8_qualification',
        'run','--plan',str(plan),'--output',str(Path(output)/'execution'),'--execute-controlled']


def validate_tool_version(value):
    require(re.fullmatch(r'(?:NVIDIA Nsight Systems version )?2026\.2\.1\.210(?:-262137639646v0)?',value.strip()) is not None,'NSYS_VERSION')
    return value.strip()


def collect(plan,output,nsys,python,tool_version='2026.2.1.210'):
    """Explicit single collection/export; never retry or weaken a warning gate."""
    from scripts.gate8_diagnostic_collect import run_once
    from scripts.gate7_nsys_postprocess import run_postprocess
    output=Path(output).resolve(); plan=Path(plan).resolve()
    if output.exists(): raise FileExistsError(output)
    read_plan(plan,current=True)
    output.mkdir(parents=True)
    report=dict(schema_version=VERSION,status='BLOCKED',plan_sha256=digest(plan),
        q0_status='NOT_RUN',gate8_verdict='NOT_RUN',attempt_count=1,collector_version=validate_tool_version(tool_version))
    try:
        process=run_once(profile_argv(nsys,python,plan,output),output/'collection_log',timeout_seconds=180)
        report['process']=process
        require(process['status']=='COMPLETE' and not process['timed_out'] and process['exit_code']==0,'COLLECTION_FAILED_NO_RETRY')
        validate_execution(plan,output/'execution/execution.json')
        rep=output/'capture.nsys-rep'; require(rep.is_file() and rep.stat().st_size>0,'REP_MISSING')
        report.update(rep_sha256=digest(rep),execution_sha256=digest(output/'execution/execution.json'))
        export=run_postprocess(nsys_exe=str(nsys),rep_path=rep,canonical_path=output/'capture.sqlite',
            report_path=output/'postprocess.json',max_attempts=1)
        require(export['status']=='PASS' and export['analyzer_allowed'] is True,'EXPORT_FAILED_NO_RETRY')
        result=audit(plan,output/'execution/execution.json',output/'capture.sqlite',rep,
            output/'postprocess.json',output/'audit','2026.2.1.210')
        report.update(status='CONTROLLED_SCOPE_MATCH',result_sha256=digest(result))
    except Exception as exc:
        report['error']=type(exc).__name__+':'+str(exc)
    _write(output/'collection_report.json',report)
    return output/'collection_report.json'


def main(argv=None):
    import argparse
    import sys
    parser=argparse.ArgumentParser(description=__doc__)
    subs=parser.add_subparsers(dest='command',required=True)
    prep=subs.add_parser('prepare')
    for n in ('output','preflight','library','commit','run-id'): prep.add_argument('--'+n,required=True)
    run=subs.add_parser('run')
    for n in ('plan','output'): run.add_argument('--'+n,required=True)
    run.add_argument('--execute-controlled',action='store_true',required=True)
    collection=subs.add_parser('collect')
    for n in ('plan','output','nsys'): collection.add_argument('--'+n,required=True)
    collection.add_argument('--execute-controlled',action='store_true',required=True)
    args=parser.parse_args(argv)
    if args.command=='prepare':
        print(prepare(args.output,args.preflight,args.library,args.commit,args.run_id)); return 0
    if args.command=='run':
        result=execute(args.plan,args.output)
        return 0 if _json(result)['status']=='COMPLETE' else 1
    require(Path(args.nsys).is_absolute() and Path(args.nsys).is_file(),'NSYS_PATH')
    import subprocess
    version=subprocess.run([args.nsys,'--version'],capture_output=True,text=True,check=True,timeout=15).stdout
    validate_tool_version(version)
    result=collect(args.plan,args.output,args.nsys,sys.executable,version)
    print(result)
    return 0 if _json(result)['status']=='CONTROLLED_SCOPE_MATCH' else 1


if __name__=='__main__': raise SystemExit(main())
