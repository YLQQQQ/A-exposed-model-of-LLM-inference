"""Real Detours on Host-only SDK-signature doubles; no CUDA DLL loaded."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import pytest


@pytest.fixture(scope='module')
def native(tmp_path_factory):
    assert importlib.util.find_spec('scripts.memset_prefill_native'), 'missing Prefill native build'
    from scripts import memset_prefill_native as build
    cfg=os.environ.get('MEMSET_MICRO_CPU_CONFIG')
    if not cfg:pytest.skip('Explicit MSVC/SDK config required; target native NOT_RUN')
    config=json.loads(Path(cfg).read_text());out=tmp_path_factory.mktemp('prefill native')
    if os.environ.get('MEMSET_PREFILL_BUILT_JSON'):
        from scripts.memset_micro import verify_rows
        path=Path(os.environ['MEMSET_PREFILL_BUILT_JSON']);b=json.loads(path.read_text());verify_rows(path.parent,b['binary_files'])
        return path.parent,b
    return out,build.build(config,out)


@pytest.mark.parametrize('mode,used,fault',[('normal',3,0),('overflow',4096,4),('foreign',0,5),
    ('failed',3,0),('reentry',3,3),('wrong_entry',0,0)])
def test_real_prefill_detour_scope_forwarding_capacity_and_threads(native,mode,used,fault):
    out,b=native
    p=subprocess.run([b['host_test'],mode],cwd=out,capture_output=True,timeout=20)
    assert p.returncode==0,p.stderr.decode('utf8',errors='replace')
    v=json.loads(p.stdout)
    assert v['cuda_module_loaded'] is False
    if mode=='wrong_entry':assert v['attach_rejected'];return
    assert v['used']==used and v['fault']==fault
    assert v['outside_calls_preserved'] and v['forward_calls_exact'] and v['last_error_preserved']
    if mode in ('normal','failed','reentry'):
        assert v['call_ids']==[1,2,3] and v['counts']==[0,64,9223372036854775815]
        assert v['aliases']==[1,2,1]
        assert v['returns']==([1]*3 if mode=='failed' else [0]*3)


def test_real_ctypes_sidecar_layout_and_lazy_prefill_lifecycle(native,tmp_path):
    import ctypes as c
    from exposedpath.memset_prefill import Recorder,binding
    from scripts.memset_micro import sha
    out,b=native;target=out/'host_target.dll'
    cpu=c.CDLL(str(target))
    fn=cpu.EpHostMemset;fn.argtypes=[c.c_void_p,c.c_int,c.c_size_t,c.c_void_p];fn.restype=c.c_int
    r=Recorder(binding('a'*32,'d'*40,dict(path=b['host_recorder'],sha256=sha(b['host_recorder'])),
        dict(path=str(target),sha256=sha(target))))
    # This is a real Python<->native ABI execution with the explicitly compiled
    # Host export substitute, never a CUDA runtime or model observation.
    identity=dict(run_id='a'*32,request_id='request-0');r.install(identity);r.begin(identity)
    for ptr,count in [(0x1111,0),(0x2222,64),(0x1111,2**63+7)]:assert fn(ptr,123,count,None)==0
    r.end(123456);r.close(tmp_path/'side.json');v=json.loads((tmp_path/'side.json').read_text())
    assert [x['count'] for x in v['calls']]==[0,64,2**63+7]
    assert [x['pointer_alias'] for x in v['calls']]==[1,2,1]
    assert v['completion_observed'] and v['attach_code']==v['detach_code']==v['recorder_error']==0
