"""Opt-in PyTorch explicit-current-stream bridge; no model or N1 variant matrix."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import shutil
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]


def require(ok,reason):
    if not ok: raise ValueError('G9_BRIDGE_'+reason)


def token_pair(backend,tokens,boundary):
    require(len(tokens)==2 and all(type(x) is int for x in tokens),'TOKEN_PLAN')
    observed=[]
    for index,token in enumerate(tokens):
        backend.submit(token)
        if index==0: backend.wait('internal_wait')
        backend.copy(); backend.wait('wait')
        actual=backend.read()
        require(type(actual) is int and actual==token,'TOKEN')
        observed.append(actual)
        boundary(index)
    return observed


def execute(plan_path, output):
    from exposedpath_v141.gate8_files import _json, _write, _entry, _resolve
    from exposedpath_v141.gate8_adapter import digest, normalized_uuid, normalized_pci
    from exposedpath_v141.gate8_target_python import current
    plan=_json(plan_path); output=Path(output).resolve()
    output.mkdir(parents=True,exist_ok=False)
    report=dict(status='FAILED',pid=os.getpid(),parent_pid=os.getppid(),error=None,observed_tokens=[])
    _write(output/'started.json',report)
    native=None
    try:
        require(plan['schema_version']=='gate9-bridge-plan/0.1.0','PLAN_VERSION')
        report['runtime']=current(plan['target_python'])
        require(os.environ.get('CUDA_DEVICE_ORDER')=='PCI_BUS_ID'
            and os.environ.get('CUDA_VISIBLE_DEVICES')==str(plan['preflight']['gpu_index_physical']),'MASK')
        require(digest(Path(plan['library']['path']))==plan['library']['sha256'],'LIBRARY_CHANGED')
        required={'scripts/gate9_bridge_target.py','scripts/gate9_bridge_token.cu',
            'scripts/gate8_qualification_token.cu','exposedpath/gate9_stream_bridge.py'}
        require(isinstance(plan['sources'],dict) and required<=plan['sources'].keys(),'SOURCES_MISSING')
        for name,ref in plan['sources'].items():
            source=(ROOT/name).resolve()
            require(not Path(name).is_absolute() and source.is_relative_to(ROOT)
                and digest(source)==ref,'SOURCE_CHANGED')
        manifest=_json(_resolve(Path(plan_path).parent,plan['manifest']))
        prompt=_json(_resolve(Path(plan_path).parent,plan['prompt']))
        require(prompt=={'request_tokens':[[0,1],[11,12]],'warmup_count':0},'FIXED_INPUT')
        require(manifest.get('domain_qualification')=={'contract':'G9-DOMAIN-QUALIFICATION/0.1.0',
            'profile':'N1_EXPLICIT_STREAM_AB/0.1.0','declaration_role':'PRE_EXECUTION'}
            and manifest.get('run_role')=='ENGINEERING' and manifest.get('data_role')=='Engineering'
            and manifest.get('runner_git_dirty') is False
            and manifest.get('runner_source_sha256')==digest(Path(__file__))
            and manifest.get('prompt_tokens_sha256')==digest(_resolve(Path(plan_path).parent,plan['prompt'])),'MANIFEST')
        import torch
        require(str(torch.__version__)=='2.6.0+cu124' and torch.version.cuda=='12.4','TORCH_VERSION')
        require(Path(torch.__file__).resolve().is_relative_to(Path(plan['target_python']['site_root'])),'TORCH_ORIGIN')
        from exposedpath.platform_adapter import cuda_identity_native
        device=cuda_identity_native(torch.cuda)
        require(normalized_uuid(device['gpu_uuid'])==normalized_uuid(plan['preflight']['gpu_uuid'])
            and normalized_pci(device['pci_bus_id'])==normalized_pci(plan['preflight']['pci_bus_id']),'DEVICE')
        from exposedpath_v141.gate8_controlled_cli import NativeBackend
        native=NativeBackend(plan['library']['path'])
        native_device=native.identity()
        require(normalized_uuid(native_device['gpu_uuid'])==normalized_uuid(device['gpu_uuid'])
            and normalized_pci(native_device['pci_bus_id'])==normalized_pci(device['pci_bus_id']),'NATIVE_DEVICE')
        report['native_device']=native_device
        native.library.ep_submit_on.argtypes=[ctypes.c_size_t,ctypes.c_int]
        native.library.ep_copy_on.argtypes=[ctypes.c_size_t]
        native.library.ep_flags.argtypes=[ctypes.c_size_t,ctypes.POINTER(ctypes.c_uint)]
        stream=torch.cuda.Stream(device=0)
        flags=ctypes.c_uint()
        native._call('ep_flags',stream.cuda_stream,ctypes.byref(flags))
        require(stream.cuda_stream!=0 and flags.value==1,'NONBLOCKING_STREAM')
        report.update(native_handle=int(stream.cuda_stream),native_flags=flags.value,
            torch_version=str(torch.__version__),cuda_version=torch.version.cuda)
        from exposedpath.gate8_identity import make_gate8_pass_identity
        from exposedpath.gate8_boundary import Gate8BoundaryRecorder
        from exposedpath.gate8_drain import DrainRecorder
        from exposedpath.gate9_stream_bridge import StreamBridge,VERSION
        from exposedpath.nvtx import make_structured_nvtx_label
        fields={k:manifest[k] for k in ('experiment_id','wmpc_id','run_id','run_role','data_role','runner_git_commit','runner_git_dirty')}
        fields.update(pass_id='pass1',attempt_id='bridge-once',pid=os.getpid(),
            runner_source_sha256=manifest['runner_source_sha256'],wmpc_manifest_sha256=digest(_resolve(Path(plan_path).parent,plan['manifest'])),
            prompt_sha256=digest(_resolve(Path(plan_path).parent,plan['prompt'])))
        entries=[dict(request_id='bridge-'+str(i),repeat_id=str(i),request_role='measured',
            expected_output_tokens=2,actual_output_tokens=0,early_eos=False,outcome='FAILED',reasons=['NOT_EXECUTED'],
            expected_boundary_ids=[manifest['run_id']+':'+str(i)+':'+str(j) for j in range(3)],observed_boundary_ids=[]) for i in (0,1)]
        ledger=make_gate8_pass_identity(requests=entries,**fields)
        host=[]; drains=[]; bridges=[]
        life=dict(schema_version='exposedpath-stream-lifetime-marker/0.1.0',generation='held-explicit-0',
            mode='CONTINUOUS_OWNED',logical_device=0,producer_source_sha256=fields['runner_source_sha256'],
            identity={k:fields[k] for k in ('run_id','pass_id','attempt_id','pid')})
        with torch.cuda.stream(stream):
            native.push('EXPOSEDPATH_STREAM_LIFETIME_V1:'+json.dumps(life))
            try:
                for index,entry in enumerate(ledger['requests']):
                    identity=entry['identity']; token_index=[0]; sync_ordinal=[0]
                    boundary=Gate8BoundaryRecorder(identity,entry['expected_boundary_ids'],marker_sink=native.mark)
                    drain=DrainRecorder(identity,'drain-'+str(index),0,clock_ns=time.perf_counter_ns,push=native.push,pop=native.pop)
                    drain.observe(native.prepare)  # Successful completion BEFORE request.
                    bridge=StreamBridge(torch.cuda,stream,identity,'held-explicit-0')
                    class Backend:
                        def submit(self,v): return bridge.observe('submit',lambda h:native._call('ep_submit_on',h,v))
                        def copy(self): return bridge.observe('copy',lambda h:native._call('ep_copy_on',h))
                        def read(self): return native.read()
                        def wait(self,kind):
                            label=dict(identity,kind='sync',phase='prefill' if token_index[0]==0 else 'decode',
                                callsite_id='gate9_bridge_'+kind,sync_origin='n1_intervention',sync_ordinal=sync_ordinal[0],
                                intervention_variant_id='bridge_qualification',intervention_ordinal=sync_ordinal[0])
                            native.push(make_structured_nvtx_label(label))
                            try: bridge.synchronize(kind)
                            finally: native.pop()
                            sync_ordinal[0]+=1
                    def ready(i): boundary.observe(time.perf_counter_ns(),i); token_index[0]=i+1
                    try:
                        with bridge:
                            boundary.observe(time.perf_counter_ns())
                            actual=token_pair(Backend(),prompt['request_tokens'][index],ready)
                        entry.update(actual_output_tokens=2,outcome='COMPLETE',reasons=[])
                        report['observed_tokens'].append(actual)
                    finally:
                        host.extend(boundary.records); drains.append(drain.record)
                        entry['observed_boundary_ids']=[r['payload']['boundary_id'] for r in boundary.records]
                        bridges.append(dict(identity=identity,generation='held-explicit-0',status=bridge.status,records=bridge.records))
            finally: native.pop()
        for source,name in ((plan['manifest'],'manifest.json'),(plan['prompt'],'prompt.json')):
            shutil.copyfile(_resolve(Path(plan_path).parent,source),output/name)
        shutil.copyfile(__file__,output/'runner_source.py')
        _write(output/'preflight.json',plan['preflight'])
        _write(output/'cuda_probe.json',dict(**device,pid=os.getpid(),gpu_index_logical=0,
            cuda_device_order='PCI_BUS_ID',cuda_visible_devices=os.environ['CUDA_VISIBLE_DEVICES']))
        artifacts={'pass_identity.json':ledger,'host_boundaries.json':host,
            'drain_ledger.json':dict(schema_version='exposedpath-drain-ledger/0.1.0',drains=drains)}
        for name,value in artifacts.items(): _write(output/name,value)
        _write(output/'bridge.json',dict(schema_version=VERSION,source_sha256=fields['runner_source_sha256'],pid=os.getpid(),requests=bridges))
        _write(output/'producer_receipt.json',dict(schema_version='exposedpath-gate8-producer-receipt/0.2.0',
            **{k:fields[k] for k in ('run_id','pass_id','attempt_id')},status='COMPLETE',gate8_verdict='NOT_RUN',
            files={name:_entry(output/name,output) for name in artifacts}))
        report['status']='COMPLETE'
    except BaseException:
        report['error']=traceback.format_exc()
    finally:
        if native is not None:
            try: native.close()
            except BaseException:
                report['cleanup_error']=traceback.format_exc(); report['status']='FAILED'
        _write(output/'execution.json',report)
    return 0 if report['status']=='COMPLETE' else 1


def main(argv=None):
    p=argparse.ArgumentParser()
    for name in ('plan','output'): p.add_argument('--'+name,required=True)
    p.add_argument('--execute-controlled',action='store_true',required=True)
    a=p.parse_args(argv)
    return execute(Path(a.plan),Path(a.output))


if __name__=='__main__': raise SystemExit(main())
