"""Real API22 headers and a Host-only loader; no CUDA/CUPTI library execution."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess

import pytest


def test_native_build_entry_exists():
    assert (Path(__file__).resolve().parents[1]/'scripts/build_cupti_timeline.py').is_file(), 'timeline build entry missing'


@pytest.fixture(scope='module')
def native(tmp_path_factory):
    cfg=os.environ.get('CUPTI_TIMELINE_CPU_CONFIG')
    if not cfg:pytest.skip('Explicit native SDK build config absent; native qualification NOT_RUN')
    path=Path(__file__).resolve().parents[1]/'scripts/build_cupti_timeline.py'
    spec=importlib.util.spec_from_file_location('_reviewed_timeline_build',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    sealed=os.environ.get('CUPTI_TIMELINE_BUILT_JSON')
    if sealed:
        import hashlib
        b=json.loads(Path(sealed).read_text());out=Path(sealed).parent
        for r in b['binaries']:
            p=out/r['path'];assert p.stat().st_size==r['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
        return b,out
    out=tmp_path_factory.mktemp('cupti timeline real headers CPU')
    return m.build(json.loads(Path(cfg).read_text()),out),out


def test_real_headers_multithread_stack_and_entry_snapshot(native):
    b,out=native
    r=subprocess.run([b['host_test'],'snapshot'],cwd=out,capture_output=True,timeout=20)
    assert r.returncode==0,r.stderr.decode(errors='replace')
    v=json.loads(r.stdout)
    assert v['thread_stacks']==2 and v['copied_count']==2**63+7
    assert v['copied_stream']==0 and v['parent_ids']==[None,1,None,3]
    assert v['errors']==0 and v['vendor_calls']==0


def test_real_driver_sync_stream_is_copied_at_entry_without_vendor_calls(native):
    b,out=native
    r=subprocess.run([b['host_test'],'driver_sync'],cwd=out,capture_output=True,timeout=20)
    assert r.returncode==0,r.stderr.decode(errors='replace')
    assert json.loads(r.stdout)==dict(native_stream=0x3450,params=True,errors=0,vendor_calls=0)


@pytest.mark.parametrize('damage',['wrong_exit','capacity','missing_params','activity_kind','long_kernel_name'])
def test_native_incomplete_or_overflow_capture_is_rejected(native,damage):
    b,out=native
    r=subprocess.run([b['host_test'],damage],cwd=out,capture_output=True,timeout=20)
    assert r.returncode==0,r.stderr.decode(errors='replace')
    v=json.loads(r.stdout)
    assert v['errors']+v['overflow']>0 and v['vendor_calls']==0


def test_all_required_sdk_activity_structures_copy_before_buffer_return(native):
    b,out=native
    r=subprocess.run([b['host_test'],'activities'],cwd=out,capture_output=True,timeout=20)
    assert r.returncode==0,r.stderr.decode(errors='replace')
    v=json.loads(r.stdout)
    assert v['kinds']==['API','KERNEL','MEMCPY','MEMSET','SYNC','STREAM','CONTEXT','CUDA_EVENT']
    assert v['kernel_name']=='original kernel' and v['copy_runtime_correlation']==77
    assert v['errors']==0 and v['vendor_calls']==0


def test_client_dll_build_and_load_do_not_initialize_vendor_or_execute_gpu(native):
    b,out=native
    assert b['vendor_gpu_executed'] is False
    assert all(not any(s in name.lower() for s in ('cuda','cupti','nvperf'))
               for names in b['imports'].values() for name in names)
    r=subprocess.run([b['host_test'],'load',b['client']],cwd=out,capture_output=True,timeout=20)
    assert r.returncode==0,r.stderr.decode(errors='replace')
    v=json.loads(r.stdout)
    assert v==dict(loaded=True,vendor_loaded=False,abi_version=1)


def test_native_sdk_writer_to_marker_bridge_to_S_and_COE(native,tmp_path):
    from analysis.cupti_timeline import select_scope,to_evidence,analyze_scope
    b,out=native
    p=subprocess.run([b['host_test'],'evidence'],cwd=out,capture_output=True,timeout=20)
    assert p.returncode==0,p.stderr.decode(errors='replace')
    raw=json.loads(p.stdout)
    producer=dict(session_id='same-session',pid=7,tid=9,run_id='run',actual_token_ids=[17])
    for k,prefix in [('drain_label','EXPOSEDPATH_DRAIN_V1:'),('helper_label','EXPOSEDPATH_JSON_V1:')]:
        producer[k]=next(m['label'] for m in raw['markers'] if m['label'].startswith(prefix))
    points=[m['label'] for m in raw['markers'] if m['label'].startswith('EXPOSEDPATH_BOUNDARY_V1:')]
    producer.update(request_label=points[0],token_label=points[1])
    scope=select_scope(raw,producer);r=analyze_scope(to_evidence(raw,scope))
    assert r['coe_ns']==20 and r['sync_intersection_ns']==15
    assert len(r['logical_zero_call_ids'])==1 and r['synthetic_activities']==[]
    assert raw['source']=='HOST_SDK_DOUBLE' and r['provider_qualification']=='NOT_GRANTED_BY_THIS_CONSUMER'
    (tmp_path/'sdk_host_capture.json').write_bytes(p.stdout)
