"""Narrow source diagnostic preparation. No profiler invocation or science admission.

The explicit run entry is separate from static preparation; importing this module
does not import Torch, load a model, initialize CUDA, or inspect the server.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import time
from types import SimpleNamespace

from .gate8_adapter import digest, normalized_uuid, normalized_pci
from .gate8_controlled_cli import check_git, ROOT
from .gate8_files import _entry, _resolve, _write

VERSION='exposedpath-source-probe-plan/0.1.0'
PROFILE='gate8-source-backtrace/0.1.0'
FLAGS=('--trace=cuda,nvtx','--sample=process-tree','--cpuctxsw=process-tree',
       '--sampling-frequency=200','--cudabacktrace=memory:0,sync:0',
       '--cuda-memory-usage=false','--cuda-trace-scope=process-tree','--isr=false')
SOURCES=('exposedpath_v141/gate8_source_probe.py','exposedpath/runner.py',
         'exposedpath/gate8_load_tasks.py','exposedpath/gate8_stages.py',
         'exposedpath/gate8_boundary.py','exposedpath/gate8_drain.py')


def profile_argv(nsys, python, plan_path, output_dir):
    """Reviewable argv only. Caller must obtain separate profile authorization."""
    output=Path(output_dir)
    if output.exists():
        raise FileExistsError(output)
    return [str(nsys),'profile',*FLAGS,'--output='+str(output/'capture'),str(python),
            '-m','exposedpath_v141.gate8_source_probe','run','--plan',str(plan_path),
            '--output',str(output/'producer'),'--execute-source-probe']


def _preflight(value):
    physical=value.get('gpu_index_physical')
    if (type(physical) is not int or physical<0 or value.get('cuda_device_order')!='PCI_BUS_ID'
            or value.get('cuda_visible_devices')!=str(physical)):
        raise ValueError('SOURCE_PROBE_MASK')
    normalized_uuid(value.get('gpu_uuid')); normalized_pci(value.get('pci_bus_id'))


def prepare(output_dir, *, preflight_path, expected_commit, run_id):
    output=Path(output_dir).resolve()
    if output.exists(): raise FileExistsError(output)
    check_git(expected_commit)
    if not isinstance(run_id,str) or re.fullmatch('[A-Za-z0-9_.-]+',run_id) is None:
        raise ValueError('SOURCE_PROBE_RUN_ID')
    pre=json.loads(Path(preflight_path).read_text(encoding='utf-8-sig'))
    _preflight(pre)
    output.mkdir(parents=True)
    shutil.copyfile(preflight_path,output/'preflight.json')
    sources={name:digest(ROOT/name) for name in SOURCES}
    plan=dict(schema_version=VERSION,profile=PROFILE,purpose='SOURCE_DIAGNOSTIC_ONLY',
        expected_commit=expected_commit,run_id=run_id,pass_id='pass1',attempt_id='0',
        expected_tokens=[[15,15],[15,15]],construction='two-vectors-0-to-15-scores-x+y+step',
        inputs={'preflight':_entry(output/'preflight.json',output)},source_sha256=sources,
        gate8_verdict='NOT_RUN',measurement_validity='NOT_ASSESSED',q0_status='NOT_RUN')
    _write(output/'plan.json',plan)
    return output/'plan.json'


class VectorModel:
    """Diagnostic arithmetic, not a language model or a W(s) oracle."""
    def __init__(self,x,y): self.x,self.y=x,y
    def __call__(self,*,past_key_values=None,**kwargs):
        step=0 if past_key_values is None else past_key_values
        return SimpleNamespace(logits=(self.x+self.y+step).reshape(1,1,16),past_key_values=step+1)


class TorchBackend:
    def __init__(self):
        import torch
        if str(torch.__version__)!='2.6.0+cu124' or torch.version.cuda!='12.4':
            raise ValueError('SOURCE_PROBE_TORCH_VERSION')
        self.torch,self.cuda=torch,torch.cuda
    def identity(self):
        from exposedpath import platform_adapter
        physical=os.environ['CUDA_VISIBLE_DEVICES']
        text=platform_adapter.nvidia_smi(['--id='+physical,'--query-gpu=index,uuid,pci.bus_id',
                                         '--format=csv,noheader,nounits'])
        rows=[x.strip().split(',') for x in text.splitlines() if x.strip()]
        if len(rows)!=1 or len(rows[0])!=3 or rows[0][0].strip()!=physical:
            raise ValueError('SOURCE_PROBE_GPU_QUERY')
        uuid,pci=(s.strip() for s in rows[0][1:])
        if (self.cuda.device_count()!=1 or self.cuda.current_device()!=0
                or normalized_uuid(str(self.cuda.get_device_properties(0).uuid))!=normalized_uuid(uuid)):
            raise ValueError('SOURCE_PROBE_LOGICAL_GPU')
        return dict(gpu_uuid=uuid,pci_bus_id=pci)
    def source(self):
        from exposedpath.gate8_load_tasks import resolve_target_source
        return resolve_target_source()
    def vectors(self): return [self.torch.arange(16,dtype=self.torch.float16,device='cpu') for _ in range(2)]
    def inputs(self):
        return (self.torch.tensor([[0]],dtype=self.torch.long,device='cuda:0'),
                self.torch.tensor([[1]],dtype=self.torch.long,device='cuda:0'))
    def model(self,values): return VectorModel(*values)


def _read_plan(path, *, current=False):
    plan=json.loads(Path(path).read_text(encoding='utf-8'))
    keys={'schema_version','profile','purpose','expected_commit','run_id','pass_id','attempt_id',
          'expected_tokens','construction','inputs','source_sha256','gate8_verdict','measurement_validity','q0_status'}
    if (type(plan) is not dict or set(plan)!=keys or plan['schema_version']!=VERSION
            or plan['profile']!=PROFILE or plan['purpose']!='SOURCE_DIAGNOSTIC_ONLY'
            or plan['pass_id']!='pass1' or plan['attempt_id']!='0'
            or plan['expected_tokens']!=[[15,15],[15,15]]
            or plan['construction']!='two-vectors-0-to-15-scores-x+y+step'
            or plan['gate8_verdict']!='NOT_RUN' or plan['q0_status']!='NOT_RUN'
            or plan['measurement_validity']!='NOT_ASSESSED'
            or set(plan['inputs'])!={'preflight'} or set(plan['source_sha256'])!=set(SOURCES)
            or not isinstance(plan['run_id'],str) or re.fullmatch('[A-Za-z0-9_.-]+',plan['run_id']) is None
            or not isinstance(plan['expected_commit'],str) or re.fullmatch('[0-9a-f]{40}',plan['expected_commit']) is None):
        raise ValueError('SOURCE_PROBE_PLAN')
    if any(not isinstance(h,str) or re.fullmatch('[0-9a-f]{64}',h) is None for h in plan['source_sha256'].values()):
        raise ValueError('SOURCE_PROBE_SOURCE_HASH')
    pre_path=_resolve(Path(path).parent,plan['inputs']['preflight'])
    pre=json.loads(pre_path.read_text(encoding='utf-8-sig')); _preflight(pre)
    if current:
        check_git(plan['expected_commit'])
        if plan['source_sha256']!={name:digest(ROOT/name) for name in SOURCES}:
            raise ValueError('SOURCE_PROBE_SOURCE_HASH')
        if any(os.environ.get(k)!=v for k,v in (
            ('CUDA_DEVICE_ORDER','PCI_BUS_ID'),('CUDA_VISIBLE_DEVICES',str(pre['gpu_index_physical'])))):
            raise ValueError('SOURCE_PROBE_MASK')
    return plan,pre,pre_path


def execute(plan_path,output_dir,*,backend_factory=TorchBackend):
    """Explicit source fixture only. Never calls a profiler/exporter or retries."""
    output=Path(output_dir).resolve(); plan_path=Path(plan_path).resolve()
    if output.exists(): raise FileExistsError(output)
    plan,pre,pre_path=_read_plan(plan_path,current=True)
    output.parent.mkdir(parents=True,exist_ok=True)
    staging=Path(tempfile.mkdtemp(prefix='.'+output.name+'-partial-',dir=output.parent))
    ledger=stages=observer=None
    host=[]; drains=[]; tokens=[]; request_results=[]
    try:
        # Copies are provenance, not executable snapshots. No circular hashes.
        _write(staging/'plan.json',plan)
        shutil.copyfile(pre_path,staging/'preflight.json')
        backend=backend_factory()
        observed=backend.identity()
        _write(staging/'cuda_probe.json',observed)
        if (normalized_uuid(observed.get('gpu_uuid'))!=normalized_uuid(pre['gpu_uuid'])
                or normalized_pci(observed.get('pci_bus_id'))!=normalized_pci(pre['pci_bus_id'])):
            raise ValueError('SOURCE_PROBE_GPU_IDENTITY')
        core,source,hook=backend.source()
        source={**source,'profile':'hf-source-probe/0.1.0'}
        from exposedpath import runner
        from exposedpath.gate8_identity import make_gate8_pass_identity, PASS_FIELDS
        from exposedpath.gate8_load_tasks import LoadTaskObserver, validate_load_tasks
        from exposedpath.gate8_stages import StageRecorder
        from exposedpath.gate8_boundary import Gate8BoundaryRecorder
        from exposedpath.gate8_drain import DrainRecorder
        identity=dict(experiment_id='gate8-source-probe',wmpc_id='vectors-v1',run_id=plan['run_id'],
                      run_role='ENGINEERING',data_role='Engineering',pass_id='pass1',attempt_id='0')
        manifest={**identity,'runner_git_commit':plan['expected_commit'],'runner_git_dirty':False,
            'runner_source_sha256':plan['source_sha256']['exposedpath/runner.py'],
            'probe_source_sha256':plan['source_sha256']['exposedpath_v141/gate8_source_probe.py'],
            'gpu_index_physical':pre['gpu_index_physical'],'gpu_index_logical':0,
            'gpu_uuid':pre['gpu_uuid'],'gpu_pci_bus_id':pre['pci_bus_id'],
            'purpose':plan['purpose'],'default_stream_mode':'UNKNOWN','measurement_validity':'NOT_ASSESSED'}
        _write(staging/'wmpc_manifest.json',manifest)
        _write(staging/'prompt.json',{'construction':plan['construction'],'expected_tokens':plan['expected_tokens']})
        requests=[]
        for i in range(2):
            prefix=plan['run_id']+':r'+str(i)
            requests.append(dict(request_id='r'+str(i),repeat_id=str(i),request_role='measured',
                expected_output_tokens=2,actual_output_tokens=0,expected_boundary_ids=[prefix+':'+str(j) for j in range(3)],
                observed_boundary_ids=[],outcome='FAILED',early_eos=False,reasons=['NOT_EXECUTED']))
        ledger=make_gate8_pass_identity(**identity,requests=requests,pid=os.getpid(),
            wmpc_manifest_sha256=digest(staging/'wmpc_manifest.json'),prompt_sha256=digest(staging/'prompt.json'),
            runner_source_sha256=manifest['runner_source_sha256'],runner_git_commit=plan['expected_commit'],runner_git_dirty=False)
        stages=StageRecorder(ledger,0,backend.cuda,time.perf_counter_ns,setup_observed=True)
        observer=None
        def setup():
            nonlocal observer
            observer=LoadTaskObserver(identity={k:ledger[k] for k in PASS_FIELDS},pid=os.getpid(),
                parent_stage_id=stages.value['stages'][0]['payload']['stage_id'],source=source,expected_hook=hook,
                push=backend.cuda.nvtx.range_push,pop=backend.cuda.nvtx.range_pop)
            def materialize():
                from concurrent.futures import ThreadPoolExecutor
                # Two tiny tasks only. Waiting is fixture consumption, not added
                # to the real model loader or performed by the observer.
                with ThreadPoolExecutor(max_workers=2) as pool:
                    futures=[core.spawn_materialize(pool,v,device='cuda:0') for v in backend.vectors()]
                    return [f.result() for f in futures]
            values=observer.run_attempt(core,materialize,branch='source_probe')
            ids,mask=backend.inputs()
            return backend.model(values),ids,mask
        model,ids,mask=stages.observe('setup',None,setup)
        for entry in ledger['requests']:
            boundary=Gate8BoundaryRecorder(entry['identity'],entry['expected_boundary_ids'],marker_sink=backend.cuda.nvtx.mark)
            drain=DrainRecorder(entry['identity'],entry['expected_boundary_ids'][0]+':drain',0,
                clock_ns=time.perf_counter_ns,push=backend.cuda.nvtx.range_push,pop=backend.cuda.nvtx.range_pop)
            try:
                result=stages.observe('measured',entry['identity'],lambda:runner.run_one_invocation(
                    model,ids,mask,2,'cuda:0','SOURCE_PROBE_REQUEST','','','',None,
                    token_ready_identity_base=entry['identity'],gate8_recorder=boundary,drain_recorder=drain))
            except BaseException as exc:
                entry.update(actual_output_tokens=max(0,len(boundary.records)-1),outcome='FAILED',
                             reasons=['RUNTIME_ERROR:'+type(exc).__name__])
                raise
            finally:
                entry['observed_boundary_ids']=[r['payload']['boundary_id'] for r in boundary.records]
                host.extend(boundary.records)
                if drain.record is not None: drains.append(drain.record)
            if any(len(b.host_token_ids)!=1 for b in result['token_ready_boundaries']):
                raise ValueError('SOURCE_PROBE_TOKEN_BATCH')
            tokens.append([b.host_token_ids[0] for b in result['token_ready_boundaries']])
            request_results.append(dict(identity=entry['identity'],
                token_ready_boundaries=runner.token_ready_boundaries_to_records(result['token_ready_boundaries'])))
            entry.update(actual_output_tokens=result['actual_output_tokens'],outcome='COMPLETE',reasons=[],
                         observed_boundary_ids=[r['payload']['boundary_id'] for r in boundary.records])
        tasks=observer.seal(); validate_load_tasks(tasks,ledger,stages.value)
        _write(staging/'request_results.json',request_results)
        artifacts={'pass_identity.json':ledger,'host_boundaries.json':host,
            'drain_ledger.json':{'schema_version':'exposedpath-drain-ledger/0.1.0','drains':drains},
            'stage_ledger.json':stages.value,'load_tasks.json':tasks}
        for name,value in artifacts.items(): _write(staging/name,value)
        _write(staging/'producer_receipt.json',dict(schema_version='exposedpath-gate8-producer-receipt/0.4.0',
            run_id=plan['run_id'],pass_id='pass1',attempt_id='0',gate8_verdict='NOT_RUN',
            status=tasks['observation_status'],files={name:_entry(staging/name,staging) for name in artifacts}))
        names=[*artifacts,'producer_receipt.json','plan.json','preflight.json','wmpc_manifest.json','prompt.json','cuda_probe.json','request_results.json']
        _write(staging/'source_receipt.json',dict(schema_version='exposedpath-source-probe-result/0.1.0',
            run_id=plan['run_id'],status='COMPLETE',tokens=tokens,measurement_validity='NOT_ASSESSED',
            source_binding='UNKNOWN',gate8_verdict='NOT_RUN',files={name:_entry(staging/name,staging) for name in names}))
        _validate_result(staging/'source_receipt.json')
        staging.rename(output)
        return output/'source_receipt.json'
    except BaseException as exc:
        # Partial observations are diagnostic only, never a promoted receipt.
        for name,item in (('pass_identity.json',ledger),('stage_ledger.json',None if stages is None else stages.value),
                          ('load_tasks.json',None if observer is None or observer.active else observer.seal()),
                          ('host_boundaries.json',host),('request_results.json',request_results),
                          ('drain_ledger.json',dict(schema_version='exposedpath-drain-ledger/0.1.0',drains=drains))):
            if item is not None and not (staging/name).exists(): _write(staging/name,item)
        _write(staging/'failure.json',dict(status='FAILED',error=type(exc).__name__,
            gate8_verdict='NOT_RUN',measurement_validity='NOT_ASSESSED'))
        raise


def read_result(path):
    """Local observation acceptance only; no Raw or scientific qualification."""
    path=Path(path).resolve()
    if path.parent.name.startswith('.') or (path.parent/'failure.json').exists():
        raise ValueError('SOURCE_PROBE_NOT_PUBLISHED_OR_FAILED')
    return _validate_result(path)


def _validate_result(path):
    path=Path(path).resolve(); value=json.loads(path.read_text())
    names={'pass_identity.json','host_boundaries.json','drain_ledger.json','stage_ledger.json','load_tasks.json',
           'producer_receipt.json','plan.json','preflight.json','wmpc_manifest.json','prompt.json','cuda_probe.json','request_results.json'}
    if (set(value)!={'schema_version','run_id','status','tokens','measurement_validity','source_binding','gate8_verdict','files'}
            or value['schema_version']!='exposedpath-source-probe-result/0.1.0'
            or value['status']!='COMPLETE' or value['tokens']!=[[15,15],[15,15]]
            or value['measurement_validity']!='NOT_ASSESSED' or value['source_binding']!='UNKNOWN'
            or value['gate8_verdict']!='NOT_RUN' or set(value['files'])!=names):
        raise ValueError('SOURCE_PROBE_RESULT')
    for name,ref in value['files'].items():
        if ref.get('filename')!=name: raise ValueError('SOURCE_PROBE_FILENAME')
        _resolve(path.parent,ref)
    plan,pre,_=_read_plan(path.parent/'plan.json')
    from exposedpath.gate8_load_tasks import load_producer_observations
    tasks=load_producer_observations(path.parent/'producer_receipt.json')
    ledger=json.loads((path.parent/'pass_identity.json').read_text())
    manifest=json.loads((path.parent/'wmpc_manifest.json').read_text())
    prompt=json.loads((path.parent/'prompt.json').read_text())
    observed=json.loads((path.parent/'cuda_probe.json').read_text())
    expected_manifest=dict(experiment_id='gate8-source-probe',wmpc_id='vectors-v1',run_id=plan['run_id'],
        run_role='ENGINEERING',data_role='Engineering',pass_id='pass1',attempt_id='0',
        runner_git_commit=plan['expected_commit'],runner_git_dirty=False,
        runner_source_sha256=plan['source_sha256']['exposedpath/runner.py'],
        probe_source_sha256=plan['source_sha256']['exposedpath_v141/gate8_source_probe.py'],
        gpu_index_physical=pre['gpu_index_physical'],gpu_index_logical=0,
        gpu_uuid=pre['gpu_uuid'],gpu_pci_bus_id=pre['pci_bus_id'],purpose=plan['purpose'],
        default_stream_mode='UNKNOWN',measurement_validity='NOT_ASSESSED')
    from exposedpath.gate8_identity import PASS_FIELDS
    if (manifest!=expected_manifest or prompt!={'construction':plan['construction'],'expected_tokens':[[15,15],[15,15]]}
            or any(ledger[k]!=expected_manifest[k] for k in PASS_FIELDS)
            or normalized_uuid(observed.get('gpu_uuid'))!=normalized_uuid(pre['gpu_uuid'])
            or normalized_pci(observed.get('pci_bus_id'))!=normalized_pci(pre['pci_bus_id'])):
        raise ValueError('SOURCE_PROBE_INPUT_IDENTITY')
    if (value['run_id']!=plan['run_id'] or ledger['run_id']!=value['run_id']
            or ledger['runner_git_commit']!=plan['expected_commit'] or ledger['runner_git_dirty'] is not False
            or ledger['runner_source_sha256']!=plan['source_sha256']['exposedpath/runner.py']
            or ledger['wmpc_manifest_sha256']!=digest(path.parent/'wmpc_manifest.json')
            or ledger['prompt_sha256']!=digest(path.parent/'prompt.json')
            or len(ledger['requests'])!=2 or any(r['outcome']!='COMPLETE' for r in ledger['requests'])
            or tasks['source_descriptor']['profile']!='hf-source-probe/0.1.0'
            or tasks['observation_status']!='COMPLETE' or len(tasks['attempts'])!=1 or len(tasks['tasks'])!=2):
        raise ValueError('SOURCE_PROBE_LINEAGE')
    results=json.loads((path.parent/'request_results.json').read_text())
    host=json.loads((path.parent/'host_boundaries.json').read_text())
    if len(results)!=2 or len(host)!=6: raise ValueError('SOURCE_PROBE_REQUEST_COUNT')
    for i,(row,entry) in enumerate(zip(results,ledger['requests'])):
        if (set(row)!={'identity','token_ready_boundaries'} or row['identity']!=entry['identity']
                or entry['identity']['request_id']!='r'+str(i) or entry['identity']['repeat_id']!=str(i)
                or entry['expected_output_tokens']!=2 or entry['request_role']!='measured'
                or len(row['token_ready_boundaries'])!=2):
            raise ValueError('SOURCE_PROBE_REQUEST_IDENTITY')
        for j,boundary in enumerate(row['token_ready_boundaries']):
            if (boundary.get('token_index')!=j or boundary.get('host_token_ids')!=[15]
                    or boundary.get('completed_ns')!=host[i*3+j+1]['host_observed_ns']
                    or host[i*3+j+1]['payload']['token_index']!=j):
                raise ValueError('SOURCE_PROBE_TOKEN_BOUNDARY')
    return value


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    prep=commands.add_parser('prepare')
    for name in ('output','preflight','expected-commit','run-id'):
        prep.add_argument('--'+name,required=True)
    run=commands.add_parser('run')
    run.add_argument('--plan',required=True); run.add_argument('--output',required=True)
    run.add_argument('--execute-source-probe',action='store_true',required=True)
    args=parser.parse_args(argv)
    if args.command=='prepare':
        return prepare(args.output,preflight_path=args.preflight,expected_commit=args.expected_commit,run_id=args.run_id)
    return execute(args.plan,args.output)


if __name__=='__main__':
    main()
