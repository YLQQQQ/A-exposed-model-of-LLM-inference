"""Actual client DLL with a CPU-only CUPTI-shaped DLL, never a vendor library."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess

import pytest

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def startup(tmp_path_factory):
    spec=importlib.util.spec_from_file_location('_startup_build',ROOT/'scripts/build_cupti_timeline.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    assert hasattr(m,'build_startup_test_doubles'), 'real client startup failure test path missing'
    config=os.environ.get('CUPTI_TIMELINE_CPU_CONFIG')
    if not config:pytest.skip('Explicit real CUDA12.4/API22 header configuration absent; target qualification NOT_RUN')
    out=tmp_path_factory.mktemp('startup SDK CPU')
    c=json.loads(Path(config).read_text());built=m.build(c,out/'client')
    doubles=m.build_startup_test_doubles(c,out/'doubles')
    return built,doubles,out


def invoke(startup,tmp_path,mode,code=37):
    built,doubles,_=startup
    capture=tmp_path/'capture.json'
    p=subprocess.run([doubles['startup_host'],built['client'],doubles['startup_double'],
        str(capture),mode,str(code)],capture_output=True,timeout=20)
    assert p.returncode==0,p.stderr.decode(errors='replace')
    r=json.loads(p.stdout)
    assert r['role']=='CPU_DLL_STARTUP_DOUBLE_NOT_GPU' and r['vendor_loaded'] is False
    return r,json.loads(capture.read_text())


@pytest.mark.parametrize('mode,operation,kind',[
    ('stream_failure','cuptiActivityEnableAndDump',37),
    ('sync_failure','cuptiActivityEnable',38),
    ('subscribe_failure','cuptiSubscribe',None),
    ('thread_failure','cuptiSetThreadIdType',None),
    ('buffers_failure','cuptiActivityRegisterCallbacks',None),
    ('driver_domain_failure','cuptiEnableDomain',None),
])
def test_actual_dll_retains_original_failure_without_changing_generic_code(startup,tmp_path,mode,operation,kind):
    r,raw=invoke(startup,tmp_path,mode)
    assert r['open_code']==3 and r['close_code']!=0
    init=raw['initialization'];assert init['schema_version']=='cupti-timeline-startup/0.2.0'
    assert init['succeeded'] is False and init['overflow']==0
    failure=init['failure']
    assert failure['operation']==operation and failure['activity_kind']==kind
    assert failure['status_domain']=='CUPTI' and failure['status_code']==37
    assert init['steps'][-1]==failure
    assert raw['quality']['errors']==[1] and raw['quality']['dropped']==0
    if mode=='stream_failure':assert not any(s['activity_kind']==36 for s in init['steps'])
    if mode=='sync_failure':assert not any(s['activity_kind']==37 for s in init['steps'])


def test_actual_success_preserves_all_original_activity_types_and_order(startup,tmp_path):
    r,raw=invoke(startup,tmp_path,'success')
    assert r['open_code']==r['close_code']==0
    init=raw['initialization'];assert init['succeeded'] is True and init['failure'] is None
    kinds=[s['activity_kind'] for s in init['steps'] if s['activity_kind'] is not None]
    assert kinds==[5,4,10,1,2,38,9,37]
    operations=[s['operation'] for s in init['steps'] if s['status_domain']=='CUPTI']
    assert operations==['cuptiGetVersion','cuptiSubscribe','cuptiSetThreadIdType','cuptiActivityRegisterCallbacks',
        'cuptiEnableDomain','cuptiEnableDomain',*['cuptiActivityEnable']*6,
        'cuptiActivityEnableAndDump','cuptiActivityEnableAndDump']
    assert raw['quality']['closed'] is True and raw['quality']['errors']==[]


def test_missing_library_reports_win32_without_inventing_cupti_result(startup,tmp_path):
    r,raw=invoke(startup,tmp_path,'missing_library')
    failure=raw['initialization']['failure']
    assert r['open_code']==3 and failure['operation']=='LoadLibraryExW'
    assert failure['status_domain']=='WIN32' and failure['status_code']>0
    assert failure['activity_kind'] is None


def test_missing_export_retains_symbol_and_win32_error(startup,tmp_path):
    built,doubles,_=startup;capture=tmp_path/'capture.json'
    p=subprocess.run([doubles['startup_host'],built['client'],doubles['startup_missing_export'],
        str(capture),'success','0'],capture_output=True,timeout=20)
    assert p.returncode==0,p.stderr.decode(errors='replace')
    raw=json.loads(capture.read_text());failure=raw['initialization']['failure']
    assert failure['operation']=='GetProcAddress' and failure['detail']=='cuptiActivityEnableAndDump'
    assert failure['status_domain']=='WIN32' and failure['status_code']==127
    assert all(s.get('operation')!='cuptiActivityEnableAndDump' for s in raw['initialization']['steps'])


def test_version_conflict_is_separate_from_successful_getversion_result(startup,tmp_path):
    r,raw=invoke(startup,tmp_path,'version_conflict')
    init=raw['initialization'];failure=init['failure']
    assert r['open_code']==3 and failure['operation']=='CUPTI_API_VERSION'
    assert failure['status_domain']=='CONTRACT' and failure['status_code']==23
    assert any(s['operation']=='cuptiGetVersion' and s['status_code']==0 for s in init['steps'])


def test_real_client_dll_through_python_session_retains_exact_original_failure(startup,tmp_path):
    import sys
    built,doubles,_=startup
    body='''import ctypes,hashlib,importlib.util,json,sys
from pathlib import Path
source,client,library,output=sys.argv[1:]
spec=importlib.util.spec_from_file_location("cpu_session",source)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
fake=ctypes.WinDLL(library)
configure=fake.ep_startup_double_configure
configure.argtypes=[ctypes.c_char_p,ctypes.c_int,ctypes.c_int,ctypes.c_uint32]
configure.restype=None
configure(b"cuptiActivityEnable",38,37,22)
cfg=dict(client=client,client_sha256=m.sha(client),cupti=library,cupti_sha256=m.sha(library),session_id="CPU_DLL_DOUBLE")
try:
 with m.CaptureSession(cfg,output,allow_target_capture=True,_library_factory=ctypes.WinDLL):pass
except ValueError as error:
 message=str(error)
 assert "OPEN_FAILED:3" in message and "cuptiActivityEnable" in message and "37" in message
else:raise AssertionError("failure was accepted")
receipt=json.loads((Path(output)/"receipt.json").read_text())
assert receipt["startup_failure"]["status_code"]==37 and receipt["startup_failure"]["activity_kind"]==38
assert receipt["open_code"]==3 and receipt["close_code"]==4
assert receipt["verification_mode"]=="CPU_LIBRARY_DOUBLE_NOT_GPU"
k=ctypes.WinDLL("kernel32");k.GetModuleHandleW.argtypes=[ctypes.c_wchar_p];k.GetModuleHandleW.restype=ctypes.c_void_p
assert not any(k.GetModuleHandleW(n) for n in ("nvcuda.dll","cudart64_12.dll","cupti64_2024.1.1.dll"))
print(json.dumps(dict(role="CPU_DLL_DOUBLE",startup_failure=receipt["startup_failure"])))
'''
    p=subprocess.run([sys.executable,'-I','-S','-c',body,str(ROOT/'exposedpath/cupti_timeline.py'),
        built['client'],doubles['startup_double'],str(tmp_path/'session')],capture_output=True,timeout=20)
    assert p.returncode==0,p.stderr.decode(errors='replace')
    assert json.loads(p.stdout)['role']=='CPU_DLL_DOUBLE'
