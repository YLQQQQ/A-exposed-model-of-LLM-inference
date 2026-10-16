"""Actual Host Detours and SDK compile only; never executes the CUDA micro EXE."""
import importlib
import json
import os
from pathlib import Path
import subprocess

import pytest


@pytest.fixture(scope='module')
def native(tmp_path_factory):
    cfg=os.environ.get('MEMSET_MICRO_CPU_CONFIG')
    if not cfg:pytest.skip('Explicit local MSVC/SDK/dependency config required; target compile NOT_RUN')
    m=importlib.import_module('scripts.memset_micro')
    config=json.loads(Path(cfg).read_text(encoding='utf8'))
    existing=os.environ.get('MEMSET_MICRO_BUILT_JSON')
    if existing:
        build=Path(existing);result=json.loads(build.read_text(encoding='utf8'))
        m.verify_rows(build.parent,result['binary_files'])
        return m,result,build.parent
    out=tmp_path_factory.mktemp('real native (CPU)')
    return m,m.build_native(config,out),out


@pytest.mark.parametrize('mode,count,status',[('zero',0,0),('positive',64,0),('large',2**63+7,0),('failed',64,1)])
def test_real_host_dll_is_detoured_once_with_uint64_and_error_preservation(native,mode,count,status):
    m,b,out=native
    run=subprocess.run([b['host_test'],mode],cwd=out,capture_output=True,timeout=15)
    assert run.returncode==0,run.stderr.decode('utf8',errors='replace')
    v=json.loads(run.stdout)
    assert v['actual_target_calls']==1 and v['count']==count
    assert v['actual_target_count']==count and v['actual_target_stream_hex']=='12345678'
    assert v['return_code']==status and v['target_entry_last_error']==1234
    assert v['caller_last_error']==31337 and v['return_last_error']==31337
    assert v['native_stream_hex']=='12345678' and v['cuda_module_loaded'] is False
    assert v['forwarded_pointer_matches'] and v['forwarded_value']==123
    assert v['detach_code']==0 and v['after_detach_calls']==2


def test_complete_real_header_micro_is_compiled_but_never_run(native):
    m,b,out=native
    assert Path(b['micro']).is_file() and Path(b['recorder']).is_file()
    assert b['micro_invoked'] is False
    assert all('cudart' not in n.lower() and 'nvcuda' not in n.lower() and 'cupti' not in n.lower()
               for n in b['micro_imports'])
    assert b['cuda_header_version']==12040


def test_actual_cudart_pe_resource_is_not_toolkit_semver(native):
    m,b,out=native
    cfg=json.loads(Path(os.environ['MEMSET_MICRO_CPU_CONFIG']).read_text())
    path=Path(os.environ.get('MEMSET_MICRO_RUNTIME_FILE',str(Path(cfg['cuda_include']).parent/'bin/cudart64_12.dll')))
    assert m.runtime_fact(path)['file_version']=='6.14.11.12040'


@pytest.mark.parametrize('mode,field,want',[('wrong_entry','attach_rejected',True),('reentry','recorder_error',3)])
def test_real_host_wrong_entry_and_reentry_refuse(native,mode,field,want):
    m,b,out=native
    r=subprocess.run([b['host_test'],mode],cwd=out,capture_output=True,timeout=15)
    assert r.returncode==0,r.stderr.decode('utf8',errors='replace')
    value=json.loads(r.stdout);assert value[field]==want
    if mode=='reentry':assert value['actual_target_calls']==2

