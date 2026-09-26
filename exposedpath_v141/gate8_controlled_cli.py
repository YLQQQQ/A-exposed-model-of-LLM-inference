"""Explicit prepare/run entry for a narrow controlled Engineering request.

prepare is static; run --execute-controlled is the only CUDA execution entry.
Never used automatically by tests, Gate7 launcher, or importing the package.
"""
import argparse
import ctypes
import json
import os
from pathlib import Path
import re
import shutil
import uuid

from exposedpath import platform_adapter
from .gate8_adapter import digest, normalized_uuid, normalized_pci
from .gate8_controlled import CONSTRUCTION, TOKEN_PLAN, run_controlled_to_files
from .gate8_files import _entry, _resolve, _write

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'exposedpath_v141/gate8_controlled.py'
NATIVE=ROOT/'scripts/gate8_controlled_token.cu'
PLAN_VERSION='exposedpath-controlled-plan/0.1.0'


def check_git(expected):
    if not isinstance(expected,str) or re.fullmatch('[0-9a-f]{40}',expected) is None:
        raise ValueError('EXPECTED_COMMIT_INVALID')
    if (platform_adapter.git(['-C',str(ROOT),'rev-parse','HEAD']) != expected
            or platform_adapter.git(['-C',str(ROOT),'status','--porcelain'])):
        raise ValueError('GIT_IDENTITY_NOT_CLEAN_OR_CONFLICTING')


def prepare_controlled(output_dir, *, preflight_path, library_path, expected_commit, run_id):
    output_dir,library_path=Path(output_dir).resolve(),Path(library_path).resolve()
    if output_dir.exists(): raise FileExistsError(output_dir)
    check_git(expected_commit)
    pre=json.loads(Path(preflight_path).read_text(encoding='utf-8-sig'))
    physical=pre.get('gpu_index_physical')
    if (type(physical) is not int or physical<0 or pre.get('cuda_device_order')!='PCI_BUS_ID'
            or pre.get('cuda_visible_devices')!=str(physical)):
        raise ValueError('PHYSICAL_MASK_INVALID')
    normalized_uuid(pre.get('gpu_uuid')); normalized_pci(pre.get('pci_bus_id'))
    if not library_path.is_file() or library_path.stat().st_size==0:
        raise ValueError('NATIVE_LIBRARY_MISSING')
    if not isinstance(run_id,str) or re.fullmatch('[A-Za-z0-9_.-]+',run_id) is None:
        raise ValueError('RUN_ID_INVALID')
    output_dir.mkdir(parents=True)
    shutil.copyfile(SOURCE,output_dir/'runner_source.py')
    _write(output_dir/'preflight.json',pre)
    _write(output_dir/'prompt.json',{'construction':CONSTRUCTION,'token_plan':TOKEN_PLAN})
    identity=dict(experiment_id='exposedpath-controlled-d2h',wmpc_id='controlled-d2h-v1',run_id=run_id,
                  run_role='ENGINEERING',data_role='Engineering',runner_git_commit=expected_commit,runner_git_dirty=False)
    _write(output_dir/'wmpc_manifest.json',{**identity,'construction':CONSTRUCTION,
        'gpu_index':physical,'gpu_index_physical':physical,'gpu_index_logical':0,
        'gpu_uuid':pre['gpu_uuid'],'gpu_pci_bus_id':pre['pci_bus_id'],
        'runner_source_sha256':digest(SOURCE),'prompt_tokens_sha256':digest(output_dir/'prompt.json'),
        'native_source_sha256':digest(NATIVE),'native_library_sha256':digest(library_path),
        'study_mode':'CONTROLLED_ENGINEERING','model_workload':False,
        'request_stream_policy':'DISJOINT_NONBLOCKING_STREAMS_WARMUP_SEPARATE'})
    plan=dict(schema_version=PLAN_VERSION,construction=CONSTRUCTION,identity=identity,expected_commit=expected_commit,
        library={'path':str(library_path),'sha256':digest(library_path)},
        native_source_sha256=digest(NATIVE),cli_source_sha256=digest(Path(__file__)),
        inputs={k:_entry(output_dir/name,output_dir) for k,name in (
            ('preflight','preflight.json'),('prompt','prompt.json'),('wmpc_manifest','wmpc_manifest.json'),
            ('runner_source','runner_source.py'))},gate8_verdict='NOT_RUN',q0_status='NOT_RUN')
    _write(output_dir/'control_plan.json',plan)
    return output_dir/'control_plan.json'


class NativeBackend:
    def __init__(self,library):
        self.library=ctypes.CDLL(str(library))
        for name in ('ep_init','ep_submit'):
            getattr(self.library,name).argtypes=[ctypes.c_int]
        for name in ('ep_prepare','ep_copy','ep_wait','ep_read','ep_close','ep_pop'):
            getattr(self.library,name).argtypes=[]
        for name in ('ep_mark','ep_push'):
            getattr(self.library,name).argtypes=[ctypes.c_char_p]
            getattr(self.library,name).restype=None
        self.library.ep_pop.restype=None
        self.library.ep_identity.argtypes=[ctypes.POINTER(ctypes.c_ubyte),ctypes.c_char_p,ctypes.c_int]
        try: self._call('ep_init',0)
        except Exception:
            self.library.ep_close()
            raise
    def _call(self,name,*args):
        status=getattr(self.library,name)(*args)
        if status!=0: raise RuntimeError(f'{name}: CUDA status {status}')
    def identity(self):
        raw=(ctypes.c_ubyte*16)(); pci=ctypes.create_string_buffer(64)
        self._call('ep_identity',raw,pci,64)
        return {'gpu_uuid':'GPU-'+str(uuid.UUID(bytes=bytes(raw))),'pci_bus_id':pci.value.decode('ascii')}
    def prepare(self): self._call('ep_prepare')
    def submit(self,token): self._call('ep_submit',token)
    def copy(self): self._call('ep_copy')
    def wait(self): self._call('ep_wait')
    def read(self): return self.library.ep_read()
    def mark(self,text): self.library.ep_mark(text.encode('utf-8'))
    def push(self,text): self.library.ep_push(text.encode('utf-8'))
    def pop(self): self.library.ep_pop()
    def close(self): self._call('ep_close')


def execute_controlled(plan_path,output_dir,*,backend_factory=NativeBackend):
    plan_path,output_dir=Path(plan_path).resolve(),Path(output_dir).resolve()
    if output_dir.exists(): raise FileExistsError(output_dir)
    plan=json.loads(plan_path.read_text(encoding='utf-8'))
    if plan.get('schema_version')!=PLAN_VERSION or plan.get('construction')!=CONSTRUCTION:
        raise ValueError('CONTROLLED_PLAN_VERSION_INVALID')
    check_git(plan['expected_commit'])
    if (set(plan['inputs'])!={'preflight','prompt','wmpc_manifest','runner_source'}
            or plan.get('gate8_verdict')!='NOT_RUN' or plan.get('q0_status')!='NOT_RUN'):
        raise ValueError('CONTROLLED_PLAN_INPUTS_OR_QUALIFICATION_INVALID')
    inputs={k:_resolve(plan_path.parent,v) for k,v in plan['inputs'].items()}
    library=Path(plan['library']['path'])
    if (digest(library)!=plan['library']['sha256'] or digest(SOURCE)!=digest(inputs['runner_source'])
            or digest(NATIVE)!=plan['native_source_sha256'] or digest(Path(__file__))!=plan['cli_source_sha256']):
        raise ValueError('CONTROLLED_SOURCE_OR_LIBRARY_MISMATCH')
    pre=json.loads(inputs['preflight'].read_text())
    manifest=json.loads(inputs['wmpc_manifest'].read_text())
    expected_identity={k:manifest[k] for k in ('experiment_id','wmpc_id','run_id','run_role','data_role',
                                               'runner_git_commit','runner_git_dirty')}
    if (plan['identity']!=expected_identity or manifest['runner_git_commit']!=plan['expected_commit']
            or manifest['runner_git_dirty'] is not False or manifest['data_role']!='Engineering'
            or manifest['run_role']!='ENGINEERING' or manifest.get('construction')!=CONSTRUCTION
            or manifest.get('gpu_index_physical')!=pre['gpu_index_physical'] or manifest.get('gpu_index_logical')!=0
            or normalized_uuid(manifest.get('gpu_uuid'))!=normalized_uuid(pre['gpu_uuid'])
            or normalized_pci(manifest.get('gpu_pci_bus_id'))!=normalized_pci(pre['pci_bus_id'])
            or manifest.get('prompt_tokens_sha256')!=digest(inputs['prompt'])
            or manifest.get('runner_source_sha256')!=digest(inputs['runner_source'])
            or manifest.get('native_library_sha256')!=digest(library)):
        raise ValueError('CONTROLLED_PRE_EXECUTION_IDENTITY_CONFLICT')
    if (os.environ.get('CUDA_DEVICE_ORDER')!='PCI_BUS_ID'
            or os.environ.get('CUDA_VISIBLE_DEVICES')!=str(pre['gpu_index_physical'])):
        raise ValueError('CONTROLLED_MASK_CONFLICT')
    output_dir.mkdir(parents=True)
    report=dict(schema_version='exposedpath-controlled-execution/0.1.0',status='BLOCKED',
        plan_path=str(plan_path),output_dir=str(output_dir),python_executable=os.sys.executable,
        plan_sha256=digest(plan_path),commit=plan['expected_commit'],process_id=os.getpid(),
        init_status='NOT_RUN',warmup_status='NOT_RUN',cleanup_status='NOT_RUN',errors=[],
        exit_code_basis='SELF_REPORTED_RETURN_VALUE_NOT_EXTERNAL_PROCESS_RECEIPT',
        gate8_verdict='NOT_RUN',q0_status='NOT_RUN')
    backend=None
    try:
        backend=backend_factory(library)
        report['init_status']='COMPLETE'
        observed=backend.identity()
        if (normalized_uuid(observed['gpu_uuid'])!=normalized_uuid(pre['gpu_uuid'])
                or normalized_pci(observed['pci_bus_id'])!=normalized_pci(pre['pci_bus_id'])):
            raise ValueError('CONTROLLED_DEVICE_IDENTITY_CONFLICT')
        _write(output_dir/'cuda_probe.json',{**observed,'pid':os.getpid(),'gpu_index_logical':0,
            'cuda_device_order':os.environ['CUDA_DEVICE_ORDER'],'cuda_visible_devices':os.environ['CUDA_VISIBLE_DEVICES']})
        # One explicit same-kernel warmup, outside all measured request markers.
        backend.submit(0); backend.copy(); backend.wait()
        if backend.read()!=0: raise ValueError('CONTROLLED_WARMUP_READBACK_FAILED')
        report['warmup_status']='COMPLETE'
        fields={k:plan['identity'][k] for k in ('experiment_id','wmpc_id','run_id','runner_git_commit','runner_git_dirty')}
        fields.update(pass_id='pass1',attempt_id='controlled-attempt-1',pid=os.getpid(),
            wmpc_manifest_sha256=digest(inputs['wmpc_manifest']),prompt_sha256=digest(inputs['prompt']),
            runner_source_sha256=digest(inputs['runner_source']))
        receipt=run_controlled_to_files(output_dir/'producer',pass_fields=fields,backend=backend)
        report['producer_receipt_sha256']=digest(receipt)
        if json.loads(receipt.read_text())['status']!='COMPLETE':
            raise ValueError('CONTROLLED_PRODUCER_INCOMPLETE')
        report['status']='COMPLETE'
    except Exception as exc:
        report['errors'].append(f'{type(exc).__name__}:{exc}')
    finally:
        if backend is not None:
            try: backend.close(); report['cleanup_status']='COMPLETE'
            except Exception as exc:
                report['cleanup_status']='FAILED'; report['status']='BLOCKED'
                report['errors'].append(f'CLEANUP:{type(exc).__name__}:{exc}')
    report['process_exit_code']=0 if report['status']=='COMPLETE' else 1
    _write(output_dir/'execution_receipt.json',report)
    return output_dir/'execution_receipt.json'


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    prepare=sub.add_parser('prepare')
    for name in ('output-dir','preflight','library','expected-commit','run-id'):
        prepare.add_argument('--'+name,required=True)
    run=sub.add_parser('run')
    run.add_argument('--plan',required=True); run.add_argument('--output-dir',required=True)
    run.add_argument('--execute-controlled',action='store_true',required=True)
    audit=sub.add_parser('audit',help='offline only; never profiles or exports')
    for name in ('plan','execution-dir','rep','sqlite','export-report','collection-receipt',
                 'input-receipt','output-dir','collector-version'):
        audit.add_argument('--'+name,required=True)
    args=parser.parse_args(argv)
    if args.command=='prepare':
        result=prepare_controlled(args.output_dir,preflight_path=args.preflight,library_path=args.library,
                                  expected_commit=args.expected_commit,run_id=args.run_id)
        print(result); return 0
    if args.command=='audit':
        from .gate8_files import write_input_receipt,process_gate8_receipt
        plan_path=Path(args.plan).resolve(); execution_dir=Path(args.execution_dir).resolve()
        plan=json.loads(plan_path.read_text(encoding='utf-8'))
        inputs={k:_resolve(plan_path.parent,v) for k,v in plan['inputs'].items()}
        producer=execution_dir/'producer'
        receipt=write_input_receipt(args.input_receipt,collector_version=args.collector_version,
            capture_session_id=plan['identity']['run_id'],artifacts=dict(raw=Path(args.rep),sqlite=Path(args.sqlite),
            export_report=Path(args.export_report),pass_identity=producer/'pass_identity.json',
            host_ledger=producer/'host_boundaries.json',producer_receipt=producer/'producer_receipt.json',
            cuda_probe=execution_dir/'cuda_probe.json',**inputs))
        result=process_gate8_receipt(receipt,args.output_dir,controlled_sources=dict(plan=plan_path,
            execution=execution_dir/'execution_receipt.json',collection=Path(args.collection_receipt),
            controlled_receipt=producer/'controlled_receipt.json',operation_ledger=producer/'operation_ledger.json'))
        report=json.loads((result.parent/'analysis/gate8_local_analysis.json').read_text())
        print(json.dumps(dict(result=str(result),status=report['status'],gate8_verdict='NOT_RUN',
                              q0_status='NOT_RUN',model_workload_authorized=False)))
        return 0 if report['status']=='CONTROLLED_CALCULATION_ONLY' else 1
    result=execute_controlled(args.plan,args.output_dir)
    print(result)
    return json.loads(result.read_text())['process_exit_code']


if __name__=='__main__':
    raise SystemExit(main())
