"""Native producer/file boundary tests. All device evidence here is synthetic."""
import importlib
import json
from pathlib import Path
from copy import deepcopy
import struct
import shutil
import subprocess

import pytest

from test_gate8_identity import sha, write_json


def api():
    assert importlib.util.find_spec('exposedpath.native_llama'), 'native file contract missing'
    return importlib.import_module('exposedpath.native_llama')


IDENTITY = dict(experiment_id='native-exp', wmpc_id='native-wmpc', run_id='native-run',
    run_role='ENGINEERING', data_role='Engineering', pass_id='pass1', attempt_id='once',
    request_id='request-0', repeat_id='0')
GPU = dict(cuda_device_order='PCI_BUS_ID', cuda_visible_devices='3', gpu_index_physical=3,
    gpu_index_logical=0, gpu_uuid='GPU-12345678-1234-1234-1234-123456789abc',
    pci_bus_id='00000000:E1:00.0')


def prepared(tmp_path, pass_id='pass1'):
    a = api()
    binary = tmp_path/'native.exe'; binary.write_bytes(b'CPU fixture, not engine')
    model = tmp_path/'model.gguf'; model.write_bytes(b'CPU fixture, not model')
    prompt = tmp_path/'tokens.i32'; prompt.write_bytes(struct.pack('<32i', *([42]*32)))
    build = write_json(tmp_path/'build.json', dict(schema_version=a.BUILD_VERSION,
        engine_commit=a.ENGINE_COMMIT, execution_commit='a'*40, dirty=False,
        binary=dict(path=str(binary),sha256=sha(binary),size_bytes=binary.stat().st_size),
        configuration=a.build_configuration(), backend_original_sha256=a.BACKEND_SHA256,
        backend_instrumented_sha256='b'*64, native_source_sha256='c'*64))
    conversion = write_json(tmp_path/'conversion.json', dict(schema_version=a.CONVERSION_VERSION,
        engine_commit=a.ENGINE_COMMIT, hf_snapshot_manifest_sha256='d'*64,
        converter_source_sha256='e'*64, conversion_arguments=['--outtype','f16'],
        model=dict(path=str(model),sha256=sha(model),size_bytes=model.stat().st_size),
        architecture='qwen2', tensor_types={'F16':100,'F32':20}, revision=None))
    identity = dict(IDENTITY, pass_id=pass_id)
    spec = a.prepare_run(tmp_path/('prepared-'+pass_id), identity=identity,
        build_receipt=build, conversion_receipt=conversion, token_input=prompt, expected_gpu=GPU)
    return spec


def producer(spec):
    a=api(); value=json.loads(spec.read_text())
    identity=value['identity']
    points=[]
    for ordinal, token in enumerate((None,10,11)):
        payload=dict(schema_version='exposedpath-native-boundary/0.1.0',profile='LLAMA-NATIVE-WINDOW/0.1.0',
            identity=identity,spec_sha256=sha(spec),boundary_id=identity['request_id']+':'+str(ordinal),
            boundary_kind='request_start' if ordinal==0 else 'token_ready',
            token_index=None if ordinal==0 else ordinal-1,token_id=token,
            completion_mechanism='before_native_input_processing' if ordinal==0 else 'native_host_token_return')
        points.append(dict(payload=payload,
            host_observed_ns=100+ordinal*100,host_before_marker_ns=101+ordinal*100,
            host_after_marker_ns=102+ordinal*100,host_clock_id='STD_STEADY_CLOCK_NS'))
    return dict(schema_version=a.PRODUCER_VERSION, spec_sha256=sha(spec), identity=identity,
        execution_kind='CPU_SUBSTITUTE',
        pid=3,tid=4,status='COMPLETE',error=None, observed_configuration=value['configuration'],
        sampling_branch_basis='CONTEXT_WITHOUT_BACKEND_SAMPLERS',
        actual_gpu=dict(GPU), actual_input_tokens=32,actual_input_token_ids=[42]*32, tokens=[10,11],early_eos=False,
        warmups=[dict(ordinal=i,status='COMPLETE',tokens=[10,11],host_start_ns=i*10,host_end_ns=i*10+5) for i in range(3)],
        drain=dict(status='COMPLETE',host_start_ns=90,host_end_ns=95),
        boundaries=points,sync_calls=[])


def test_actual_prepare_consumer_preserves_candidate_not_qualification(tmp_path):
    spec=prepared(tmp_path); output=write_json(tmp_path/'producer.json',producer(spec))
    result=api().read_producer(spec,output)
    assert result['tokens']==[10,11]
    assert result['qualification']=='NOT_RUN'
    assert result['formal_eligible'] is False
    assert result['host_windows']==dict(full_request=[100,300],prefill=[100,200],decode=[200,300])
    assert result['declaration']['request_start']=='BEFORE_NATIVE_INPUT_PROCESSING'
    assert result['measurement_validity']=='NOT_ASSESSED'


@pytest.mark.parametrize('damage', ['role','pilot','commit','backend','quantized','gpu','input'])
def test_prepare_refuses_wrong_role_build_model_or_input(tmp_path,damage):
    spec=prepared(tmp_path); a=api(); s=json.loads(spec.read_text())
    identity=deepcopy(s['identity']); build=Path(s['sources']['build_receipt']['path'])
    conversion=Path(s['sources']['conversion_receipt']['path']); prompt=Path(s['sources']['token_input']['path'])
    if damage=='role': identity.update(run_role='FORMAL',data_role='Formal')
    if damage=='pilot':identity.update(run_role='PILOT',data_role='Pilot')
    if damage in ('commit','backend'):
        b=json.loads(build.read_text())
        if damage=='commit':b['engine_commit']='f'*40
        else:b['configuration']['cuda_graphs']=True
        write_json(build,b)
    if damage=='quantized':
        c=json.loads(conversion.read_text()); c['tensor_types']={'Q4_0':1};write_json(conversion,c)
    gpu=deepcopy(GPU)
    if damage=='gpu':gpu['gpu_index_logical']=3
    if damage=='input':prompt.write_bytes(struct.pack('<31i',*([42]*31)))
    with pytest.raises(ValueError):
        a.prepare_run(tmp_path/'bad',identity=identity,build_receipt=build,
            conversion_receipt=conversion,token_input=prompt,expected_gpu=gpu)
    assert not (tmp_path/'bad').exists()


@pytest.mark.parametrize('damage', ['spec','token','input_values','eos','warmup','drain','gpu','branch','order','missing','artifact'])
def test_real_file_consumer_rejects_incomplete_or_conflicting_producer(tmp_path,damage):
    spec=prepared(tmp_path); p=producer(spec)
    if damage=='spec':p['spec_sha256']='f'*64
    if damage=='token':p['tokens']=[10]
    if damage=='input_values':p['actual_input_token_ids'][0]=43
    if damage=='eos':p['early_eos']=True
    if damage=='warmup':p['warmups'].pop()
    if damage=='drain':p['drain']['host_end_ns']=101
    if damage=='gpu':p['actual_gpu']['gpu_uuid']='GPU-ffffffff-ffff-ffff-ffff-ffffffffffff'
    if damage=='branch':p['sampling_branch_basis']='UNKNOWN'
    if damage=='order':p['boundaries'][1]['payload']['token_index']=1
    if damage=='missing':p['boundaries'].pop()
    if damage=='artifact':Path(json.loads(spec.read_text())['sources']['token_input']['path']).write_bytes(b'changed')
    path=write_json(tmp_path/'producer.json',p)
    with pytest.raises((ValueError,OSError)):
        api().read_producer(spec,path)


def test_pair_checks_values_not_only_count(tmp_path):
    a=api(); p1=prepared(tmp_path); s=json.loads(p1.read_text())
    p0=a.prepare_run(tmp_path/'p0',identity=dict(IDENTITY,pass_id='pass0',run_id='run-p0'),
        build_receipt=s['sources']['build_receipt']['path'],conversion_receipt=s['sources']['conversion_receipt']['path'],
        token_input=s['sources']['token_input']['path'],expected_gpu=GPU)
    r1=write_json(tmp_path/'r1.json',producer(p1));r0=write_json(tmp_path/'r0.json',producer(p0))
    assert a.compare_pair(p0,r0,p1,r1)['status']=='TOKEN_AND_EXECUTION_PARITY_ONLY'
    v=json.loads(r0.read_text());v['tokens'][1]=12;v['boundaries'][-1]['payload']['token_id']=12;write_json(r0,v)
    with pytest.raises(ValueError,match='TOKEN'):
        a.compare_pair(p0,r0,p1,r1)


def test_resealed_spec_does_not_bypass_conversion_rules(tmp_path):
    spec=prepared(tmp_path);a=api();s=json.loads(spec.read_text())
    conversion=Path(s['sources']['conversion_receipt']['path'])
    c=json.loads(conversion.read_text());c['tensor_types']={'Q8_0':1};write_json(conversion,c)
    s['conversion']=c;s['sources']['conversion_receipt']['sha256']=sha(conversion)
    s['sources']['conversion_receipt']['size_bytes']=conversion.stat().st_size
    write_json(spec,s)
    with pytest.raises(ValueError,match='TENSOR'):a.load_spec(spec)


def test_fixed_backend_patch_is_byte_bound_and_preserves_one_sync(tmp_path):
    a=api(); source=Path('.local/diagnostics/llama_native_v0_1/ggml-cuda.original.cu')
    if not source.is_file():pytest.skip('optional pinned upstream byte audit input absent')
    original=source.read_bytes(); output=tmp_path/'patched.cu'
    a.instrument_backend(source,output)
    patched=output.read_text()
    assert patched.count('cudaStreamSynchronize(')==original.decode().count('cudaStreamSynchronize(')
    assert source.read_bytes()==original
    bad=tmp_path/'bad.cu';bad.write_bytes(original+b'\n// changed\n')
    with pytest.raises(ValueError,match='BACKEND_SOURCE'):
        a.instrument_backend(bad,tmp_path/'refused.cu')
    with pytest.raises(FileExistsError):a.instrument_backend(source,output)


def test_main_host_syntax_against_fixed_real_llama_api(tmp_path):
    compiler=shutil.which('g++');vendor=Path('.local/diagnostics/llama_native_v0_1/vendor')
    headers=Path('.local/diagnostics/llama_native_v0_1/sdk')
    if not compiler or not (headers/'llama.h').is_file():
        pytest.skip('optional pinned real SDK header audit inputs absent')
    p=subprocess.run([compiler,'-std=c++17','-fsyntax-only','-I',str(headers.resolve()),
        '-I',str(vendor.resolve()),'-I','tests/native_stubs','native/llama_cpp/main.cpp'],
        capture_output=True,timeout=60)
    assert p.returncode==0,p.stderr.decode('utf-8',errors='replace')


@pytest.fixture(scope='module')
def cpu_native_binary(tmp_path_factory):
    compiler=shutil.which('g++')
    vendor=Path('.local/diagnostics/llama_native_v0_1/vendor')
    if not compiler or not (vendor/'nlohmann/json.hpp').is_file():
        pytest.skip('CPU native compile needs compiler and explicit pinned JSON header')
    output=tmp_path_factory.mktemp('native-cpu')/'cpu.exe'
    p=subprocess.run([compiler,'-std=c++17','-O0','-I',str(vendor.resolve()),'-I','native/llama_cpp',
        'tests/cpu_native_llama.cpp','native/llama_cpp/observer.cpp','-lbcrypt','-o',str(output)],
        capture_output=True,timeout=60)
    assert p.returncode==0,p.stderr.decode('utf-8',errors='replace')
    return output


@pytest.mark.parametrize('fail',[False,True])
def test_compiled_native_producer_to_real_consumer(cpu_native_binary,tmp_path,fail):
    spec=prepared(tmp_path);out=tmp_path/'compiled-producer.json'
    p=subprocess.run([str(cpu_native_binary),str(spec),str(out),'fail' if fail else 'ok'],
        capture_output=True,timeout=20)
    observed=json.loads(out.read_text())
    if fail:
        assert p.returncode==1 and observed['error']=='deliberate process failure'
        assert observed['fake_engine_calls']==7
        assert observed['boundaries'] and len(observed['boundaries'])==1
        with pytest.raises(ValueError,match='PRODUCER_FAILED'):api().read_producer(spec,out)
    else:
        assert p.returncode==0 and observed['fake_engine_calls']==8
        assert len(observed['sync_calls'])==2
        assert [b['payload']['token_id'] for b in observed['boundaries']]==[None,10,11]
        assert api().read_producer(spec,out)['tokens']==[10,11]
        assert observed['execution_kind']=='CPU_SUBSTITUTE'
