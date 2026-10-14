"""Catch SDK interface errors before the expensive backend, without execution."""
import os
from pathlib import Path
import shutil
import subprocess

import pytest


def syntax_arguments():
    compiler=shutil.which('g++');base=Path('.local/diagnostics/llama_native_v0_1')
    headers=Path(os.environ.get('EXPOSEDPATH_TEST_CUDA_HEADERS','.local/vendor/cuda-runtime-12.4.127/headers'))
    crt=headers.parent/'nvcc-headers'
    if not compiler or not (headers/'cuda_runtime.h').is_file() or not (crt/'crt/host_defines.h').is_file():
        pytest.skip('optional fixed real CUDA12.4 host-header audit inputs/compiler absent; target adapter compile remains mandatory')
    return [compiler,'-std=c++17','-fsyntax-only','-I',str(headers.resolve()),'-I',str(crt.resolve()),
        '-I',str((base/'sdk').resolve()),'-I',str((base/'vendor').resolve()),'-I','tests/native_stubs']


def test_complete_main_compiles_against_fixed_real_cuda124_headers_without_stubs_overriding_them():
    p=subprocess.run([*syntax_arguments(),'native/llama_cpp/main.cpp'],capture_output=True,timeout=60)
    assert p.returncode==0,p.stderr.decode('utf-8',errors='backslashreplace')


def test_all_native_cuda_signatures_against_fixed_real_headers_without_invocation():
    p=subprocess.run([*syntax_arguments(),'tests/native_cuda_api_contract.cpp'],capture_output=True,timeout=30)
    assert p.returncode==0,p.stderr.decode('utf-8',errors='backslashreplace')


def test_syntax_stub_cannot_invent_an_api_missing_from_fixed_runtime(tmp_path):
    compiler=shutil.which('g++')
    if not compiler:pytest.skip('optional host syntax compiler absent')
    source=tmp_path/'invalid.cpp'
    source.write_text('#include <cuda_runtime.h>\nvoid invalid(){cudaUUID_t u;cudaDeviceGetUuid(&u,0);}\n')
    p=subprocess.run([compiler,'-std=c++17','-fsyntax-only','-I','tests/native_stubs',str(source)],capture_output=True,timeout=30)
    assert p.returncode!=0 and b'cudaDeviceGetUuid' in p.stderr


def test_adapter_failure_stops_real_stage1_file_chain_before_backend_or_conversion(tmp_path,monkeypatch):
    from exposedpath import native_stage1 as s
    from test_native_stage1 import test_cpu_file_chain_runs_all_stage1_steps_and_creates_bound_receipts
    original=s.execute
    def inject(config,package,root,*,runner):
        inner=runner.run
        def run(name,argv,**kw):
            if name=='adapter_compile':raise RuntimeError('SDK adapter compile failure fixture')
            return inner(name,argv,**kw)
        runner.run=run
        return original(config,package,root,runner=runner)
    monkeypatch.setattr(s,'execute',inject)
    with pytest.raises(RuntimeError,match='SDK adapter compile failure'):
        test_cpu_file_chain_runs_all_stage1_steps_and_creates_bound_receipts(tmp_path,monkeypatch,ninja=True)
    root=tmp_path/'diagnostics/new'
    receipt=s.read(root/'receipt.json')
    assert receipt['status']=='BLOCKED' and 'SDK adapter compile failure' in receipt['error']
    assert not (root/'model-f16.gguf').exists() and not (root/'build/bin/native-llama.exe').exists()


def test_real_cmake_adapter_target_compiles_real_objects_without_backend_or_execution(tmp_path):
    from native_cmake_fixture import fixed_cmake,fixed_ninja
    args=syntax_arguments();headers=Path(args[args.index('-I')+1]);crt=headers.parent/'nvcc-headers'
    engine=Path('.local/vendor/llama-d812-stage1').resolve()
    nvtx=Path('.local/vendor/nvtx-6230-stage1/c/include').resolve()
    if not (engine/'include/llama.h').is_file() or not (nvtx/'nvtx3/nvToolsExt.h').is_file():
        pytest.skip('optional fixed full llama/NVTX header assets absent; target compile mandatory')
    source=tmp_path/'source space (native)';source.mkdir();build=tmp_path/'build';sentinel=tmp_path/'backend-was-built'
    helper=Path('native/cmake/NativeAdapter.cmake').resolve()
    (source/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.31)\nproject(cpu_header_check LANGUAGES CXX)\n'
        'set(CMAKE_CXX_STANDARD 17)\nset(LLAMA_SOURCE_ROOT "'+engine.as_posix()+'")\n'
        'set(NVTX_INCLUDE_ROOT "'+nvtx.as_posix()+'")\nadd_library(CUDA::cudart INTERFACE IMPORTED)\n'
        'set_target_properties(CUDA::cudart PROPERTIES INTERFACE_INCLUDE_DIRECTORIES "'+headers.as_posix()+';'+crt.as_posix()+'")\n'
        'include("'+helper.as_posix()+'")\nexposedpath_native_adapter_targets()\n'
        'add_custom_target(llama ALL COMMAND "${CMAKE_COMMAND}" -E touch "'+sentinel.as_posix()+'")\n',encoding='utf-8')
    configured=subprocess.run([str(fixed_cmake()),'-S',str(source),'-B',str(build),'-G','Ninja',
        '-DCMAKE_CXX_COMPILER:FILEPATH='+Path(args[0]).as_posix(),'-DCMAKE_MAKE_PROGRAM:FILEPATH='+fixed_ninja().as_posix()],capture_output=True,timeout=60)
    assert configured.returncode==0,configured.stderr.decode('utf-8',errors='backslashreplace')
    compiled=subprocess.run([str(fixed_cmake()),'--build',str(build),'--target','native-adapter-headers','--parallel','2'],capture_output=True,timeout=90)
    assert compiled.returncode==0,(compiled.stdout+compiled.stderr).decode('utf-8',errors='backslashreplace')
    assert len(list((build/'CMakeFiles/exposedpath-native-adapter-main.dir').rglob('main.cpp.obj')))==1
    assert len(list((build/'CMakeFiles/exposedpath-native-observer.dir').rglob('observer.cpp.obj')))==1
    assert not sentinel.exists() and not list(build.rglob('native-llama.exe'))


def test_missing_adapter_evidence_cannot_qualify_new_build_receipt(tmp_path,monkeypatch):
    from exposedpath import native_stage1 as s,native_llama as n
    from test_native_stage1 import test_cpu_file_chain_runs_all_stage1_steps_and_creates_bound_receipts
    test_cpu_file_chain_runs_all_stage1_steps_and_creates_bound_receipts(tmp_path,monkeypatch,ninja=True)
    root=tmp_path/'diagnostics/new';build=s.read(root/'build_receipt.json');conversion=s.read(root/'conversion_receipt.json')
    build.pop('adapter_compile',None)
    with pytest.raises(ValueError,match='ADAPTER'):n._validate_receipts(build,conversion)


@pytest.mark.parametrize('damage',['executed','wrong-schema','header-version','source-binding','object-missing','header-changed'])
def test_adapter_receipt_cannot_hide_wrong_sdk_source_or_execution(tmp_path,monkeypatch,damage):
    from exposedpath import native_stage1 as s,native_llama as n
    from test_native_stage1 import test_cpu_file_chain_runs_all_stage1_steps_and_creates_bound_receipts
    test_cpu_file_chain_runs_all_stage1_steps_and_creates_bound_receipts(tmp_path,monkeypatch,ninja=True)
    root=tmp_path/'diagnostics/new';build=s.read(root/'build_receipt.json');conversion=s.read(root/'conversion_receipt.json')
    ref=build['adapter_compile'];path=Path(ref['path']);check=s.read(path)
    if damage=='executed':check['program_invoked']=True
    if damage=='wrong-schema':check['schema_version']='exposedpath-native-adapter-compile/999'
    if damage=='header-version':check['cuda_header_version']=13000
    if damage=='source-binding':check['native_source_sha256']='b'*64
    if damage=='object-missing':Path(check['objects']['main']['path']).unlink()
    if damage=='header-changed':Path(check['headers']['cuda_runtime.h']['path']).write_bytes(b'changed SDK')
    path=root/'candidate-adapter.json';s.write(path,check)
    ref.update(path=str(path),size_bytes=path.stat().st_size,sha256=s.digest(path))
    error=FileNotFoundError if damage=='object-missing' else ValueError
    with pytest.raises(error):n._validate_receipts(build,conversion)


def test_previous_cmake_build_receipt_remains_explicitly_readable_without_upgrading_it(tmp_path,monkeypatch):
    from exposedpath import native_stage1 as s,native_llama as n
    from test_native_stage1 import test_cpu_file_chain_runs_all_stage1_steps_and_creates_bound_receipts
    test_cpu_file_chain_runs_all_stage1_steps_and_creates_bound_receipts(tmp_path,monkeypatch,ninja=True)
    root=tmp_path/'diagnostics/new';build=s.read(root/'build_receipt.json');conversion=s.read(root/'conversion_receipt.json')
    build['schema_version']='exposedpath-native-llama-build/0.2.1';build.pop('adapter_compile')
    n._validate_receipts(build,conversion)
