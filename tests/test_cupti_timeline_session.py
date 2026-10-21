import hashlib
import importlib
import json
from types import SimpleNamespace

import pytest


class Function:
    def __init__(self,fn):self.fn=fn
    def __call__(self,*args):return self.fn(*args)


def module():
    spec=importlib.util.find_spec('exposedpath.cupti_timeline')
    assert spec is not None, 'same-process session loader missing'
    return importlib.import_module('exposedpath.cupti_timeline')


def test_no_vendor_load_on_import_and_explicit_new_session_required():
    m=module()
    assert hasattr(m,'CaptureSession')


@pytest.fixture
def setup(tmp_path):
    client=tmp_path/'client.dll';client.write_bytes(b'CLIENT CPU DOUBLE')
    cupti=tmp_path/'cupti.dll';cupti.write_bytes(b'CUPTI NOT LOADED')
    config=dict(session_id='session',client=str(client),client_sha256=hashlib.sha256(client.read_bytes()).hexdigest(),
        cupti=str(cupti),cupti_sha256=hashlib.sha256(cupti.read_bytes()).hexdigest())
    calls=[]
    def finish(path):
        calls.append('close');open(path,'w').write('{}');return 0
    lib=SimpleNamespace(ep_timeline_abi_version=Function(lambda:1),
        ep_timeline_open=Function(lambda *a:calls.append('open') or 0),
        ep_timeline_mark=Function(lambda kind,text:calls.append((kind,text.decode())) or 0),
        ep_timeline_close=Function(finish))
    def factory(path):calls.append('load_client_double');return lib
    return config,calls,factory,tmp_path/'out'


def test_explicit_capture_keeps_original_nvtx_calls_labels_and_restores_them(setup):
    cfg,calls,factory,out=setup;m=module()
    originals=[];nvtx=SimpleNamespace(range_push=lambda x:originals.append(('push',x)) or 0,
        range_pop=lambda:originals.append(('pop','')) or 0,mark=lambda x:originals.append(('mark',x)))
    old=nvtx.range_push
    session=m.CaptureSession(cfg,out,allow_target_capture=True,_library_factory=factory)
    assert calls==[]
    with session:
        with session.nvtx_sink(nvtx):
            nvtx.range_push('unchanged label');nvtx.mark('unchanged point');nvtx.range_pop()
    assert nvtx.range_push is old and originals==[('push','unchanged label'),('mark','unchanged point'),('pop','')]
    assert calls==['load_client_double','open',(1,'unchanged label'),(0,'unchanged point'),(2,''),'close']
    r=json.loads((out/'receipt.json').read_text())
    assert r['verification_mode']=='CPU_LIBRARY_DOUBLE_NOT_GPU' and r['open_code']==r['close_code']==0


@pytest.mark.parametrize('damage',['no_opt_in','hash','exists'])
def test_invalid_capture_is_rejected_before_any_vendor_boundary(setup,damage):
    cfg,calls,factory,out=setup
    if damage=='hash':cfg['cupti_sha256']='0'*64
    if damage=='exists':out.mkdir()
    with pytest.raises((ValueError,FileExistsError)):
        with module().CaptureSession(cfg,out,allow_target_capture=damage!='no_opt_in',_library_factory=factory):pass
    assert calls==[]
