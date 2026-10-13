"""Prospective Windows native Engineering contract. No model/tool/device imports.

This is not Gate13 admission, a collector or a replacement S/A implementation.
Actual artifacts are byte-bound; target-platform qualification remains separate.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import struct

from .gate8_identity import validate_shape
from exposedpath_v141.gate8_adapter import normalized_uuid, normalized_pci

ENGINE_COMMIT = 'd81235049384534c167caea52b85a694f6103d14'
BACKEND_SHA256 = '1315f06baff63da74e085b7ec01974474dac1f8ec1074af13eb70faba4751961'
JSON_HEADER_SHA256 = 'aaf127c04cb31c406e5b04a63f1ae89369fccde6d8fa7cdda1ed4f32dfc5de63'
PROFILE = 'LLAMA-NATIVE-WINDOW/0.1.0'
SPEC_VERSION = 'exposedpath-native-llama-spec/0.1.0'
PRODUCER_VERSION = 'exposedpath-native-llama-producer/0.1.0'
BUILD_VERSION = 'exposedpath-native-llama-build/0.1.0'
BUILD_NINJA_VERSION = 'exposedpath-native-llama-build/0.2.0'
CONVERSION_VERSION = 'exposedpath-native-llama-conversion/0.1.0'
BOUNDARY_VERSION = 'exposedpath-native-boundary/0.1.0'
PREFIX = 'EXPOSEDPATH_NATIVE_BOUNDARY_V1:'
SYNC_CALLSITES = ('ggml_backend_cuda_synchronize','ggml_backend_cuda_buffer_set_tensor',
    'ggml_backend_cuda_buffer_get_tensor','ggml_backend_cuda_buffer_set_tensor_2d',
    'ggml_backend_cuda_buffer_get_tensor_2d')


def require(ok, reason):
    if not ok:
        raise ValueError('NATIVE_LLAMA_'+reason)


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for data in iter(lambda:stream.read(1024*1024),b''):h.update(data)
    return h.hexdigest()


def _read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def _write(path,value):
    with Path(path).open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,sort_keys=True,indent=2)
        stream.write('\n')


def _hash(value):
    require(isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None,'HASH')


def _ref(path):
    path=Path(path).absolute()
    require(not any(p.is_symlink() or bool(getattr(p.lstat(),'st_file_attributes',0)&0x400)
        for p in (path,*path.parents)),'REPARSE_PATH')
    require(path.is_file() and path.stat().st_size>0,'FILE_MISSING_OR_EMPTY')
    return dict(path=str(path.resolve()),sha256=digest(path),size_bytes=path.stat().st_size)


def _verify(ref):
    require(set(ref)=={'path','sha256','size_bytes'},'ARTIFACT_SHAPE')
    _hash(ref['sha256'])
    require(type(ref['size_bytes']) is int and ref['size_bytes']>0,'ARTIFACT_SIZE')
    require(_ref(ref['path'])==ref,'ARTIFACT_CHANGED')


def build_configuration(route='vs2022'):
    require(route in ('vs2022','ninja'),'BUILD_ROUTE')
    value=dict(platform='WINDOWS_X64', generator='Visual Studio 17 2022' if route=='vs2022' else 'Ninja',
        toolset_version='14.38.33130', cuda_version='12.4', cuda_architectures='89',
        cuda_graphs=False, shared_libraries=False, native_cpu_arch=False,
        cuda_backend=True, flash_attention='DISABLED')
    if route=='ninja':value.update(ninja_version='1.12.1',sdk_version='10.0.20348.0',build_type='Release')
    return value


def configuration():
    return dict(input_tokens=32,output_tokens=2,batch_size=1,warmup_count=3,repeat_count=1,
        sampling='CPU_GREEDY',backend_sampler_count=0,n_ctx=64,n_batch=32,n_ubatch=32,
        n_threads=1,n_threads_batch=1,n_gpu_layers=-1,split_mode='NONE',
        backend='GGML_CUDA',cuda_graphs=False,flash_attention='DISABLED',kv_type='F16')


def declaration():
    return dict(profile=PROFILE,status='CANDIDATE_ENGINEERING_ONLY',
        request_start='BEFORE_NATIVE_INPUT_PROCESSING',
        token_completion='AFTER_ACTUAL_HOST_TOKEN_RETURN',
        start_contains_natural_preparation=True,text_and_persistence='OUTSIDE_WINDOW',
        pytorch_window_unchanged=True,qualification='NOT_RUN')


def _gpu(gpu):
    require(set(gpu)=={'cuda_device_order','cuda_visible_devices','gpu_index_physical',
        'gpu_index_logical','gpu_uuid','pci_bus_id'},'GPU_FIELDS')
    require(gpu['cuda_device_order']=='PCI_BUS_ID' and gpu['cuda_visible_devices'].isdecimal()
        and type(gpu['gpu_index_physical']) is int
        and int(gpu['cuda_visible_devices'])==gpu['gpu_index_physical']
        and type(gpu['gpu_index_logical']) is int and gpu['gpu_index_logical']==0,'GPU_MASK')
    return normalized_uuid(gpu['gpu_uuid']),normalized_pci(gpu['pci_bus_id'])


def _identity(value):
    validate_shape('identity',value)
    require(value['run_role']=='ENGINEERING' and value['data_role']=='Engineering','ROLE')


def _validate_receipts(build,conversion):
    version=build.get('schema_version')
    require(version in (BUILD_VERSION,BUILD_NINJA_VERSION) and conversion.get('schema_version')==CONVERSION_VERSION,'VERSION')
    route='ninja' if version==BUILD_NINJA_VERSION else 'vs2022'
    if route=='ninja':
        checks=build.get('compile_link_prechecks')
        require(isinstance(checks,dict) and set(checks)=={'cxx','cuda'},'BUILD_PRECHECKS')
        for kind,ref in checks.items():
            _verify(ref);v=_read(ref['path'])
            versions={'C':'19.38.33135','CXX':'19.38.33135'} if kind=='cxx' else {'CXX':'19.38.33135','CUDA':'12.4.131'}
            require(v.get('schema_version')=='exposedpath-native-compile-link/0.1.0' and
                v.get('status')=='COMPILE_LINK_PASS_NOT_EXECUTED' and v.get('program_invoked') is False
                and v.get('generator')=='Ninja' and v.get('compiler_versions')==versions
                and v.get('sdk_version')=='10.0.20348.0','BUILD_PRECHECK_STATUS')
    require(build.get('engine_commit')==conversion.get('engine_commit')==ENGINE_COMMIT,'ENGINE_COMMIT')
    require(isinstance(build.get('execution_commit'),str) and re.fullmatch('[0-9a-f]{40}',build['execution_commit'])
        and build.get('dirty') is False and build.get('configuration')==build_configuration(route),'BUILD_CONFIGURATION')
    require(build.get('backend_original_sha256')==BACKEND_SHA256,'BACKEND_SOURCE')
    for key in ('backend_instrumented_sha256','native_source_sha256'):_hash(build.get(key))
    for key in ('hf_snapshot_manifest_sha256','converter_source_sha256'):_hash(conversion.get(key))
    require(conversion.get('architecture')=='qwen2' and conversion.get('conversion_arguments')==['--outtype','f16'],'CONVERSION')
    types=conversion.get('tensor_types')
    require(isinstance(types,dict) and 'F16' in types and set(types)<={'F16','F32'}
        and all(type(n) is int and n>0 for n in types.values()),'QUANTIZED_OR_UNKNOWN_TENSOR_TYPE')
    _verify(build['binary']);_verify(conversion['model'])


def prepare_run(output,*,identity,build_receipt,conversion_receipt,token_input,expected_gpu):
    output=Path(output).resolve()
    if output.exists():raise FileExistsError(output)
    _identity(identity)
    sources={k:_ref(p) for k,p in dict(build_receipt=build_receipt,
        conversion_receipt=conversion_receipt,token_input=token_input).items()}
    build,conversion=_read(build_receipt),_read(conversion_receipt)
    _validate_receipts(build,conversion);_gpu(expected_gpu)
    data=Path(token_input).read_bytes()
    require(len(data)==128 and all(t>=0 for t in struct.unpack('<32i',data)),'INPUT_CONTENT')
    value=dict(schema_version=SPEC_VERSION,engine_commit=ENGINE_COMMIT,
        identity=deepcopy(identity),declaration=declaration(),configuration=configuration(),
        expected_gpu=deepcopy(expected_gpu),sources=sources,
        artifacts=dict(binary=build['binary'],model=conversion['model']),
        execution_commit=build['execution_commit'],conversion=conversion)
    output.mkdir(parents=True)
    _write(output/'run_spec.json',value)
    return output/'run_spec.json'


def load_spec(path):
    value=_read(path)
    require(set(value)=={'schema_version','engine_commit','identity','declaration','configuration',
        'expected_gpu','sources','artifacts','execution_commit','conversion'},'SPEC_FIELDS')
    require(value.get('schema_version')==SPEC_VERSION and value.get('engine_commit')==ENGINE_COMMIT,'SPEC_VERSION')
    _identity(value['identity'])
    require(value.get('declaration')==declaration() and value.get('configuration')==configuration(),'SPEC_DECLARATION')
    require(set(value['sources'])=={'build_receipt','conversion_receipt','token_input'}
        and set(value['artifacts'])=={'binary','model'},'SOURCE_SET')
    for ref in (*value['sources'].values(),*value['artifacts'].values()):_verify(ref)
    build=_read(value['sources']['build_receipt']['path']);conversion=_read(value['sources']['conversion_receipt']['path'])
    require(build['binary']==value['artifacts']['binary'] and conversion==value['conversion']
        and conversion['model']==value['artifacts']['model']
        and build['execution_commit']==value['execution_commit'],'SOURCE_BINDING')
    # Reapply exactly the same semantic/version constraints after resealing.
    _validate_receipts(build,conversion)
    data=Path(value['sources']['token_input']['path']).read_bytes()
    require(len(data)==128 and all(t>=0 for t in struct.unpack('<32i',data)),'INPUT_CONTENT')
    _gpu(value['expected_gpu'])
    return value


def boundary_payload(spec,ordinal,token_id,*,spec_sha256):
    require(type(ordinal) is int and 0<=ordinal<=2,'BOUNDARY_ORDINAL')
    require((ordinal==0 and token_id is None) or (ordinal>0 and type(token_id) is int and token_id>=0),'TOKEN')
    _hash(spec_sha256)
    return dict(schema_version=BOUNDARY_VERSION,profile=PROFILE,identity=deepcopy(spec['identity']),
        spec_sha256=spec_sha256,boundary_id=spec['identity']['request_id']+':'+str(ordinal),
        boundary_kind='request_start' if ordinal==0 else 'token_ready',
        token_index=None if ordinal==0 else ordinal-1,token_id=token_id,
        completion_mechanism='before_native_input_processing' if ordinal==0 else 'native_host_token_return')


def read_producer(spec_path,producer_path):
    spec=load_spec(spec_path);p=_read(producer_path);spec_hash=digest(spec_path)
    require(p.get('schema_version')==PRODUCER_VERSION and p.get('spec_sha256')==spec_hash
        and p.get('identity')==spec['identity'],'PRODUCER_BINDING')
    require(p.get('status')=='COMPLETE' and p.get('error') is None,'PRODUCER_FAILED')
    require(p.get('execution_kind') in ('NATIVE_CUDA','CPU_SUBSTITUTE'),'EXECUTION_KIND')
    if p['execution_kind']=='NATIVE_CUDA':
        runtime=p.get('runtime_identity',{})
        require(runtime.get('cuda_runtime_version')==12040
            and type(runtime.get('cuda_driver_api_version')) is int
            and runtime['cuda_driver_api_version']>=12040,'RUNTIME_IDENTITY')
    require(all(type(p.get(k)) is int and p[k]>0 for k in ('pid','tid')),'PROCESS_IDENTITY')
    require(p.get('observed_configuration')==spec['configuration']
        and p.get('sampling_branch_basis')=='CONTEXT_WITHOUT_BACKEND_SAMPLERS','ACTUAL_CONFIGURATION')
    require(_gpu(p['actual_gpu'])==_gpu(spec['expected_gpu'])
        and all(p['actual_gpu'][k]==spec['expected_gpu'][k] for k in ('cuda_device_order','cuda_visible_devices','gpu_index_physical','gpu_index_logical')),'GPU_CONFLICT')
    tokens=p.get('tokens')
    require(p.get('actual_input_tokens')==32 and isinstance(tokens,list) and len(tokens)==2
        and all(type(t) is int and t>=0 for t in tokens) and p.get('early_eos') is False,'TOKEN_OR_EOS')
    actual_input=p.get('actual_input_token_ids')
    require(isinstance(actual_input,list) and all(type(t) is int for t in actual_input)
        and actual_input==list(struct.unpack('<32i',Path(spec['sources']['token_input']['path']).read_bytes())),'ACTUAL_INPUT_VALUES')
    warmups=p.get('warmups')
    require(isinstance(warmups,list) and len(warmups)==3 and all(w.get('ordinal')==i
        and w.get('status')=='COMPLETE' and isinstance(w.get('tokens'),list) and len(w['tokens'])==2
        for i,w in enumerate(warmups)),'WARMUP_COUNT_OR_STATUS')
    require(all(type(w.get(k)) is int for w in warmups for k in ('host_start_ns','host_end_ns'))
        and all(w['host_start_ns']<=w['host_end_ns'] for w in warmups)
        and all(a['host_end_ns']<=b['host_start_ns'] for a,b in zip(warmups,warmups[1:])),'WARMUP_ORDER')
    boundaries=p.get('boundaries');require(isinstance(boundaries,list) and len(boundaries)==3,'BOUNDARY_COUNT')
    times=[]
    for i,b in enumerate(boundaries):
        expected=boundary_payload(spec,i,None if i==0 else tokens[i-1],spec_sha256=spec_hash)
        require(b.get('payload')==expected,'BOUNDARY_IDENTITY')
        clocks=[b.get(k) for k in ('host_observed_ns','host_before_marker_ns','host_after_marker_ns')]
        require(all(type(t) is int for t in clocks) and clocks==sorted(clocks)
            and b.get('host_clock_id')=='STD_STEADY_CLOCK_NS','HOST_CLOCK')
        times.append(clocks[0])
    require(times==sorted(times) and len(set(times))==3,'BOUNDARY_ORDER')
    drain=p.get('drain',{})
    require(drain.get('status')=='COMPLETE' and all(type(drain.get(k)) is int for k in ('host_start_ns','host_end_ns'))
        and warmups[-1]['host_end_ns']<=drain['host_start_ns']<=drain['host_end_ns']<=times[0],'DRAIN')
    require(isinstance(p.get('sync_calls'),list),'SYNC_LEDGER_MISSING')
    return dict(schema_version='exposedpath-native-producer-review/0.1.0',
        spec_sha256=spec_hash,producer_sha256=digest(producer_path),identity=p['identity'],
        declaration=spec['declaration'],tokens=tokens,qualification='NOT_RUN',formal_eligible=False,
        measurement_validity='NOT_ASSESSED',dropped_records_status='UNKNOWN',
        host_windows=dict(full_request=[times[0],times[2]],prefill=[times[0],times[1]],decode=[times[1],times[2]]))


def compare_pair(p0_spec,p0_result,p1_spec,p1_result):
    a,b=load_spec(p0_spec),load_spec(p1_spec)
    left,right=read_producer(p0_spec,p0_result),read_producer(p1_spec,p1_result)
    require(a['identity']['pass_id']=='pass0' and b['identity']['pass_id']=='pass1','PAIR_PASS')
    for key in ('experiment_id','wmpc_id','run_role','data_role','request_id','repeat_id'):
        require(a['identity'][key]==b['identity'][key],'PAIR_IDENTITY')
    require(a['identity']['run_id']!=b['identity']['run_id'],'PAIR_RUN')
    require(all(a[k]==b[k] for k in ('configuration','artifacts','expected_gpu','execution_commit','conversion'))
        and a['sources']['token_input']==b['sources']['token_input'],'PAIR_EXECUTION')
    require(left['tokens']==right['tokens'],'PAIR_TOKEN_VALUES')
    return dict(status='TOKEN_AND_EXECUTION_PARITY_ONLY',formal_eligible=False,qualification='NOT_RUN')


def instrument_backend(source,output):
    """New build input, never modify vendor original. Mark the existing call only."""
    source,output=Path(source),Path(output)
    if output.exists():raise FileExistsError(output)
    require(digest(source)==BACKEND_SHA256,'BACKEND_SOURCE')
    data=source.read_text(encoding='utf-8')
    old='    CUDA_CHECK(cudaStreamSynchronize(cuda_ctx->stream()));\n\n    GGML_UNUSED(backend);'
    require(data.count(old)==1,'BACKEND_SITE')
    new=('    const auto stream = cuda_ctx->stream();\n'
         '    exposedpath_native::SyncObservation observation(cuda_ctx->device,\n'
         '        ggml_cuda_get_physical_device(cuda_ctx->device), reinterpret_cast<uintptr_t>(stream));\n'
         '    const auto result = cudaStreamSynchronize(stream);\n'
         '    observation.finish(static_cast<int>(result));\n'
         '    CUDA_CHECK(result);\n\n    GGML_UNUSED(backend);')
    result='#include "observer.hpp"\n'+data.replace(old,new)
    # Natural input/output helpers have their own existing PTDS waits. Record
    # those real sites too; no with-stream assumption or invented callsite.
    for name in SYNC_CALLSITES[1:]:
        start=result.index('static void '+name+'(')
        end=result.index('\n}',start)
        body=result[start:end]
        needle='    CUDA_CHECK(cudaStreamSynchronize(cudaStreamPerThread));'
        require(body.count(needle)==1,'BUFFER_SYNC_SITE')
        replacement=('    exposedpath_native::SyncObservation observation(ctx->device,\n'
            '        ggml_cuda_get_physical_device(ctx->device), reinterpret_cast<uintptr_t>(cudaStreamPerThread),\n'
            '        "llama.cpp.'+name+'");\n'
            '    const auto result = cudaStreamSynchronize(cudaStreamPerThread);\n'
            '    observation.finish(static_cast<int>(result));\n'
            '    CUDA_CHECK(result);')
        result=result[:start]+body.replace(needle,replacement)+result[end:]
    with output.open('x',encoding='utf-8',newline='\n') as stream:stream.write(result)
    return dict(original_sha256=BACKEND_SHA256,instrumented_sha256=digest(output))
