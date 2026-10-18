"""Real SDK headers and Host callback doubles; never load CUDA/CUPTI DLLs."""
import json
import importlib.util
import os
from pathlib import Path
import subprocess

import pytest


@pytest.fixture(scope='module')
def native(tmp_path_factory):
    cfg=os.environ.get('INDEPENDENT_CUPTI_CPU_CONFIG')
    if not cfg:pytest.skip('Explicit MSVC/SDK config absent; native compile NOT_RUN')
    assert importlib.util.find_spec('scripts.independent_cupti_stage'), 'native build entry missing'
    from scripts import independent_cupti_stage as m
    built=os.environ.get('INDEPENDENT_CUPTI_BUILT_JSON')
    if built:
        result=json.loads(Path(built).read_text());m.verify_rows(Path(built).parent,result['binary_files'])
        return result,Path(built).parent
    out=tmp_path_factory.mktemp('real CUPTI headers (CPU)')
    return m.build_native(json.loads(Path(cfg).read_text()),out),out


@pytest.mark.parametrize('mode,count,code,entry',[
    ('ordinary',64,0,'ORDINARY'),('zero',0,0,'ORDINARY'),
    ('large',2**63+7,0,'ORDINARY'),('ptsz',64,0,'PTSZ'),('failed',64,2,'ORDINARY'),
    ('versioned_name',64,0,'ORDINARY'),('context_uid_zero',64,0,'ORDINARY')])
def test_real_header_entry_copy_survives_mutation_and_exit_keeps_return(native,mode,count,code,entry):
    b,out=native
    p=subprocess.run([b['host_test'],mode],cwd=out,capture_output=True,timeout=15)
    assert p.returncode==0,p.stderr.decode(errors='replace')
    r=json.loads(p.stdout)
    assert r['count']==count and r['value']==123 and r['native_stream']=='0x5670'
    assert r['return_code']==code and r['entry_kind']==entry and r['callback_error']==0
    assert r['vendor_dll_loaded'] is False and r['cuda_calls']==0 and r['cupti_calls']==0
    if mode=='versioned_name':assert r['observed_name']=='cudaMemsetAsync_v3020'
    if mode=='context_uid_zero':assert r['context_uid']==0


@pytest.mark.parametrize('mode',[
    'missing_params','missing_return','wrong_thread','reentry','overflow','wrong_exit','wrong_name'])
def test_native_callback_refuses_incomplete_conflicting_or_overflow_input(native,mode):
    b,out=native
    p=subprocess.run([b['host_test'],mode],cwd=out,capture_output=True,timeout=15)
    assert p.returncode==0,p.stderr.decode(errors='replace')
    assert json.loads(p.stdout)['callback_error']>0


def test_gpu_entry_compiles_and_links_with_no_static_cuda_import(native):
    b,out=native
    assert Path(b['micro']).is_file() and b['micro_invoked'] is False
    assert b['cuda_header_version']==12040 and b['cupti_header_version']==22
    assert all(not any(k in n.lower() for k in ('cuda','cupti','nvperf')) for n in b['imports']['micro'])


def test_host_dll_is_not_accidentally_loaded(native):
    b,out=native
    assert all(not any(k in n.lower() for k in ('cuda','cupti','nvperf')) for n in b['imports']['host_test'])


@pytest.mark.parametrize('mode,field,want',[
    ('buffer','api_count',1),('exhaust','buffer_exhaustion',1),('dropped','dropped_records',7),
    ('drop_error','dropped_query_errors',1),('parser_error','activity_error',1),
    ('overflow','activity_overflow',1),('bridge','driver_parent',1)])
def test_native_client_buffer_callbacks_and_domain_parent_bridge(native,mode,field,want):
    b,out=native
    assert 'host_client_test' in b, 'real client Host harness not implemented'
    p=subprocess.run([b['host_client_test'],mode],cwd=out,capture_output=True,timeout=15)
    assert p.returncode==0,p.stderr.decode(errors='replace')
    r=json.loads(p.stdout)
    assert r[field]==want and r['vendor_dll_loaded'] is False


def test_real_native_writer_to_independent_consumer_file_chain(native,tmp_path):
    from analysis.independent_cupti_memset import review_file
    b,out=native
    p=subprocess.run([b['host_client_test'],'evidence'],cwd=out,capture_output=True,timeout=15)
    assert p.returncode==0,p.stderr.decode(errors='replace')
    raw=tmp_path/'host_only_native.json';raw.write_bytes(p.stdout)
    result=review_file(raw,tmp_path/'derived')
    assert result['result']['source']=='HOST_CALLBACK_DOUBLE'
    assert result['result']['target_gpu_validated'] is False
    assert result['result']['cases'][1]['effect_records']==['memset:1']


def test_real_sdk_pe_exports_are_inspected_without_loading_vendor(native,tmp_path):
    from scripts import independent_cupti_stage as m
    assert hasattr(m,'inspect_exports'), 'PE export preflight not implemented'
    cfg=json.loads(Path(os.environ['INDEPENDENT_CUPTI_CPU_CONFIG']).read_text())
    runtime=Path(cfg.get('runtime_path',str(Path(cfg['cuda_include']).parent/'bin/cudart64_12.dll')))
    cupti=Path(cfg['cupti_include']).parent/'lib/cupti64_2024.1.1.dll'
    r=m.inspect_exports(cfg,runtime,cupti,tmp_path)
    assert r['vendor_dll_loaded'] is False and r['required_cupti_exports']==17
    assert r['required_runtime_exports']==9
