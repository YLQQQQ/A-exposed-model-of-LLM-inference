"""Pinned CMake template roundtrips, exact raw versions and strict consumers."""
import json
from pathlib import Path
import subprocess

import pytest

from native_cmake_fixture import fixed_cmake,generate_metadata,generated_build


def test_real_rc_template_reads_same_tool_after_production_argument_serialization(tmp_path):
    from exposedpath import native_ninja as n,native_stage1 as s
    tools={k:str(tmp_path/'Tool space (x86)'/(k+'.exe')) for k in ('ninja','cl','link','lib','rc','mt','nvcc','cmake')}
    build=generate_metadata(tmp_path,tools)
    actual=s.read_cache(build/'CMakeCache.txt')
    # Real CMake emitted and included RC/C/CXX files. File identity did not
    # change; forward slashes are representation, not source normalization.
    assert Path(actual['CMAKE_RC_COMPILER']).resolve()==Path(tools['rc']).resolve()
    assert Path(actual['CMAKE_C_COMPILER']).resolve()==Path(tools['cl']).resolve()
    assert n.compiler_field(build/'CMakeFiles/3.31.10/CMakeCXXCompiler.cmake','CMAKE_CXX_COMPILER_VERSION')=='19.38.33135.0'
    assert Path(n.compiler_field(build/'CMakeFiles/3.31.10/CMakeRCCompiler.cmake','CMAKE_RC_COMPILER')).resolve()==Path(tools['rc']).resolve()
    # No linked output: passing metadata/version checks must NOT qualify build.
    with pytest.raises(ValueError,match='LINK_OUTPUT_MISSING'):n.validate_build(build,tools,'cxx',build/'absent.exe')


def test_native_source_and_git_arguments_roundtrip_through_real_cmake(tmp_path):
    from exposedpath import native_stage1 as s
    base=tmp_path/'source space (brackets)';base.mkdir()
    git=base/'git.exe';git.write_bytes(b'fixed Git file fixture, not invoked')
    plan=s.command_plan(base/'code',base/'engine',base/'new',base/'hf',base/'nvtx',base/'cuda',git_executable=git)
    script=tmp_path/'read.cmake'
    script.write_text('cmake_minimum_required(VERSION 3.31)\n'
        'file(SHA256 "${GIT_EXECUTABLE}" got)\n'
        'file(WRITE "${AUDIT_OUT}" "${LLAMA_SOURCE_ROOT}\\n${NATIVE_PATCHED_BACKEND}\\n${NVTX_INCLUDE_ROOT}\\n${CUDAToolkit_ROOT}\\n${got}")\n',encoding='utf-8')
    output=tmp_path/'readback.txt';before=s.digest(git)
    result=subprocess.run([str(fixed_cmake()),*[v for v in plan[0]['arguments'] if v.startswith('-D')],
        '-DAUDIT_OUT:FILEPATH='+output.as_posix(),'-P',str(script)],capture_output=True,timeout=60)
    assert result.returncode==0,result.stderr.decode('utf-8')
    values=output.read_text().splitlines()
    assert list(map(lambda p:Path(p).resolve(),values[:4]))==[base/'engine',base/'new/backend.cu',base/'nvtx',base/'cuda']
    assert values[4]==before==s.digest(git)


@pytest.mark.parametrize('kind',['cxx','cuda'])
@pytest.mark.parametrize('version',['19.38.33135.0','19.38.33135','19.38.33135.1','19.38.33135.0junk','19.38.33136',''])
def test_real_cmake_version_policy_preserves_raw_and_rejects_other_builds(tmp_path,kind,version):
    script=tmp_path/'check.cmake';out=tmp_path/'versions.txt'
    contract=Path('native/cmake/NativeBuildContract.cmake').resolve()
    script.write_text('cmake_minimum_required(VERSION 3.31)\ninclude("'+contract.as_posix()+'")\n'
        'set(CMAKE_C_COMPILER_VERSION "'+version+'")\nset(CMAKE_CXX_COMPILER_VERSION "'+version+'")\n'
        'set(CMAKE_CUDA_COMPILER_VERSION "12.4.131")\nexposedpath_require_msvc(C CXX)\n'
        +('exposedpath_require_cuda()\n' if kind=='cuda' else '')
        +'file(WRITE "'+out.as_posix()+'" "${CMAKE_CXX_COMPILER_VERSION}")\n',encoding='utf-8')
    p=subprocess.run([str(fixed_cmake()),'-P',str(script)],capture_output=True,timeout=60)
    if version in ('19.38.33135','19.38.33135.0'):
        assert p.returncode==0,p.stderr.decode('utf-8');assert out.read_text()==version
    else:assert p.returncode!=0 and b'PINNED_MSVC_VERSION' in p.stderr and not out.exists()


def test_four_part_versions_flow_from_real_cmake_to_stage1_and_receipt_consumer(tmp_path,monkeypatch):
    import test_native_ninja as fixtures
    from test_native_stage1 import test_cpu_file_chain_runs_all_stage1_steps_and_creates_bound_receipts
    from exposedpath import native_stage1 as s,native_llama as n
    monkeypatch.setattr(fixtures,'write_build',generated_build)
    test_cpu_file_chain_runs_all_stage1_steps_and_creates_bound_receipts(tmp_path,monkeypatch,ninja=True)
    root=tmp_path/'diagnostics/new';build=s.read(root/'build_receipt.json');conversion=s.read(root/'conversion_receipt.json')
    assert build['schema_version']=='exposedpath-native-llama-build/0.2.1'
    for kind,ref in build['compile_link_prechecks'].items():
        v=s.read(ref['path']);assert v['schema_version']=='exposedpath-native-compile-link/0.2.0'
        assert v['compiler_versions']['CXX']=='19.38.33135.0'
    n._validate_receipts(build,conversion)


@pytest.mark.parametrize('damage',['old-build','old-check','wrong-msvc','wrong-cuda','unknown-version'])
def test_receipt_version_policy_does_not_upgrade_legacy_or_relax_other_tools(tmp_path,monkeypatch,damage):
    import test_native_ninja as fixtures
    from test_native_stage1 import test_cpu_file_chain_runs_all_stage1_steps_and_creates_bound_receipts
    from exposedpath import native_stage1 as s,native_llama as n
    monkeypatch.setattr(fixtures,'write_build',generated_build)
    test_cpu_file_chain_runs_all_stage1_steps_and_creates_bound_receipts(tmp_path,monkeypatch,ninja=True)
    root=tmp_path/'diagnostics/new';build=s.read(root/'build_receipt.json');conversion=s.read(root/'conversion_receipt.json')
    ref=build['compile_link_prechecks']['cuda'];p=Path(ref['path']);check=s.read(p)
    if damage=='old-build':build['schema_version']='exposedpath-native-llama-build/0.2.0'
    if damage=='old-check':check['schema_version']='exposedpath-native-compile-link/0.1.0'
    if damage=='wrong-msvc':check['compiler_versions']['CXX']='19.38.33135.1'
    if damage=='wrong-cuda':check['compiler_versions']['CUDA']='12.4.131.0'
    if damage=='unknown-version':build['schema_version']='exposedpath-native-llama-build/99'
    p.write_text(json.dumps(check),encoding='utf-8');ref.update(size_bytes=p.stat().st_size,sha256=s.digest(p))
    with pytest.raises(ValueError):n._validate_receipts(build,conversion)


def test_explicit_legacy_receipt_still_reads_without_rewriting_raw_versions(tmp_path,monkeypatch):
    import test_native_ninja as fixtures
    from test_native_stage1 import test_cpu_file_chain_runs_all_stage1_steps_and_creates_bound_receipts
    from exposedpath import native_stage1 as s,native_llama as n
    monkeypatch.setattr(fixtures,'write_build',generated_build)
    test_cpu_file_chain_runs_all_stage1_steps_and_creates_bound_receipts(tmp_path,monkeypatch,ninja=True)
    root=tmp_path/'diagnostics/new';build=s.read(root/'build_receipt.json');conversion=s.read(root/'conversion_receipt.json')
    build['schema_version']='exposedpath-native-llama-build/0.2.0'
    for ref in build['compile_link_prechecks'].values():
        p=Path(ref['path']);check=s.read(p)
        check['schema_version']='exposedpath-native-compile-link/0.1.0'
        for lang in check['compiler_versions']:
            if lang!='CUDA':check['compiler_versions'][lang]='19.38.33135'
        p.write_text(json.dumps(check),encoding='utf-8');ref.update(size_bytes=p.stat().st_size,sha256=s.digest(p))
    originals={r['path']:Path(r['path']).read_bytes() for r in build['compile_link_prechecks'].values()}
    n._validate_receipts(build,conversion)
    assert all(Path(p).read_bytes()==data for p,data in originals.items())


@pytest.mark.parametrize('path',['','C:/x;y','C:/x${v}','C:/x"y','C:/x\ny','C:/x\x00y'])
def test_unrepresentable_cmake_paths_reject_instead_of_silently_changing_file(path):
    from exposedpath.native_build_contract import cmake_path_argument
    with pytest.raises(ValueError,match='PATH_UNREPRESENTABLE'):cmake_path_argument('CMAKE_RC_COMPILER',path)


@pytest.mark.parametrize('folder',['toolchain_precheck','cuda_toolchain_precheck','llama_cpp'])
@pytest.mark.parametrize('version',['19.38.33135.0','19.38.33135','19.38.33135.1','19.38.33135.0junk'])
def test_actual_three_cmakelists_apply_same_exact_version_gate_without_building(tmp_path,folder,version):
    script=tmp_path/'entry.cmake';source=Path('native')/folder/'CMakeLists.txt'
    script.write_text('cmake_minimum_required(VERSION 3.31)\n'
        'function(project)\nendfunction()\n'
        'function(find_package)\nmessage(FATAL_ERROR "CPU_TEST_AFTER_VERSION_GATES")\nendfunction()\n'
        'function(add_executable)\nmessage(FATAL_ERROR "CPU_TEST_AFTER_VERSION_GATES")\nendfunction()\n'
        'set(WIN32 TRUE)\nset(MSVC TRUE)\nset(MSVC_VERSION 1938)\nset(CMAKE_GENERATOR Ninja)\n'
        'set(CMAKE_C_COMPILER_VERSION "'+version+'")\nset(CMAKE_CXX_COMPILER_VERSION "'+version+'")\n'
        'set(CMAKE_CUDA_COMPILER_VERSION "12.4.131")\nset(CMAKE_CUDA_ARCHITECTURES 89)\n'
        'set(LLAMA_SOURCE_ROOT "unused")\nset(NATIVE_PATCHED_BACKEND "unused")\nset(NVTX_INCLUDE_ROOT "unused")\n'
        'include("'+source.resolve().as_posix()+'")\n',encoding='utf-8')
    result=subprocess.run([str(fixed_cmake()),'-P',str(script)],capture_output=True,timeout=60)
    assert result.returncode!=0 # deliberately stop after gates, never a build
    if version in ('19.38.33135','19.38.33135.0'):assert b'CPU_TEST_AFTER_VERSION_GATES' in result.stderr
    else:assert b'PINNED_MSVC_VERSION' in result.stderr
