"""Pinned Ninja build file gates; CPU substitutes are not CUDA qualification."""
import importlib
from pathlib import Path
import json

import pytest


def api():return importlib.import_module('exposedpath.native_ninja')


def tools(tmp_path):
    return {k:str(tmp_path/(k+'.exe')) for k in ('ninja','cl','link','lib','rc','mt','nvcc','cmake')}


def test_ninja_plan_pins_all_compilers_without_vs_instance_or_forcing_success(tmp_path):
    t=tools(tmp_path);a=api().configure_arguments(tmp_path/'source',tmp_path/'new',t)
    assert a[:6]==['-S',(tmp_path/'source').as_posix(),'-B',(tmp_path/'new').as_posix(),'-G','Ninja']
    for key,name in [('CMAKE_MAKE_PROGRAM','ninja'),('CMAKE_C_COMPILER','cl'),('CMAKE_CXX_COMPILER','cl'),
        ('CMAKE_CUDA_COMPILER','nvcc'),('CMAKE_CUDA_HOST_COMPILER','cl'),('CMAKE_LINKER','link'),
        ('CMAKE_AR','lib'),('CMAKE_RC_COMPILER','rc'),('CMAKE_MT','mt')]:assert '-D'+key+':FILEPATH='+Path(t[name]).as_posix() in a
    assert '-DCMAKE_BUILD_TYPE=Release' in a
    assert not any('FORCED' in x or 'WORKS' in x or 'GENERATOR_INSTANCE' in x or x=='-T' for x in a)


def test_build_receipt_versions_cannot_disguise_generator(tmp_path):
    from test_native_llama import prepared
    from exposedpath import native_llama as native
    from exposedpath import native_stage1 as stage
    spec=stage.read(prepared(tmp_path))
    b=stage.read(spec['sources']['build_receipt']['path']);c=stage.read(spec['sources']['conversion_receipt']['path'])
    # Old reader remains explicit; new Ninja configuration cannot masquerade as 0.1.
    b['configuration']=native.build_configuration('ninja')
    with pytest.raises(ValueError):native._validate_receipts(b,c)
    b['schema_version']=native.BUILD_NINJA_VERSION
    with pytest.raises(ValueError):native._validate_receipts(b,c) # missing actual precheck evidence


def test_environment_overrides_compiler_flags_and_pins_sdk_paths(tmp_path):
    cfg=dict(vs_root=str(tmp_path/'VS'),sdk_root=str(tmp_path/'SDK'),cuda_root=str(tmp_path/'CUDA'))
    t=tools(tmp_path)
    env=api().build_environment(cfg,t,{'PATH':'untrusted-tool-first','INCLUDE':'other-sdk','LIB':'other-lib',
        'CUDAHOSTCXX':'wrong.exe','CL':'/unexpected','CUDACXX':'wrong.exe','SystemRoot':str(tmp_path/'Windows')})
    assert 'untrusted-tool-first' not in env['PATH'] and 'other-sdk' not in env['INCLUDE']
    assert '10.0.20348.0' in env['INCLUDE'] and '14.38.33130' in env['LIB']
    assert 'CL' not in env and 'CUDACXX' not in env and 'CUDAHOSTCXX' not in env
    assert env['CUDA_VISIBLE_DEVICES']=='-1'


def test_all_missing_prerequisites_are_reported_together_before_subprocess(tmp_path):
    from exposedpath import native_stage1 as stage
    cfg=dict(vs_root=str(tmp_path/'VS'),sdk_root=str(tmp_path/'SDK'),cuda_root=str(tmp_path/'CUDA'))
    root=tmp_path/'new';root.mkdir()
    with pytest.raises(ValueError,match='PREREQUISITE_FILES'):api().bind_tools(cfg,tmp_path/'package',root,runner=None)
    r=stage.read(root/'toolchain_prerequisites.json')
    assert {i['name'] for i in r['issues']} >= {'cl','link','lib','rc','mt','nvcc'}


def write_build(tmp_path,t,kind='cxx',damage=None):
    from exposedpath import native_stage1 as stage
    b=tmp_path/kind;b.mkdir()
    keys={'CMAKE_GENERATOR':'Ninja','CMAKE_MAKE_PROGRAM':t['ninja'],'CMAKE_C_COMPILER':t['cl'],
        'CMAKE_CXX_COMPILER':t['cl'],'CMAKE_LINKER':t['link'],'CMAKE_AR':t['lib'],
        'CMAKE_RC_COMPILER':t['rc'],'CMAKE_MT':t['mt'],'CMAKE_BUILD_TYPE':'Release',
        'CMAKE_SYSTEM_VERSION':'10.0.20348.0','CMAKE_CUDA_ARCHITECTURES':'89'}
    if kind=='cuda':keys.update(CMAKE_CUDA_COMPILER=t['nvcc'],CMAKE_CUDA_HOST_COMPILER=t['cl'])
    if damage=='wrong-tool':keys['CMAKE_LINKER']=str(tmp_path/'other.exe')
    if damage=='wrong-arch':keys['CMAKE_CUDA_ARCHITECTURES']='80'
    (b/'CMakeCache.txt').write_text(''.join(k+':STRING='+v+'\n' for k,v in keys.items()))
    d=b/'CMakeFiles/3.31.10';d.mkdir(parents=True)
    for lang in (('C','CXX') if kind=='cxx' else ('CXX','CUDA')):
        version='12.4.131' if lang=='CUDA' else '19.38.33135'
        if damage=='wrong-version':version='19.44.35207'
        (d/('CMake'+lang+'Compiler.cmake')).write_text('set(CMAKE_'+lang+'_COMPILER_VERSION "'+version+'")\n'
            +'set(CMAKE_'+lang+'_COMPILER "'+t['nvcc' if lang=='CUDA' else 'cl'].replace('\\','/')+'")\n')
    exe=b/('native-toolchain-check.exe' if kind=='cxx' else 'native-cuda-link-check.exe')
    if damage!='missing-output':exe.write_bytes(b'CPU output; never executed')
    return b,exe


@pytest.mark.parametrize('kind',['cxx','cuda'])
@pytest.mark.parametrize('damage',[None,'wrong-tool','wrong-version','missing-output','wrong-arch'])
def test_actual_compiler_and_link_output_not_a_handfilled_success(tmp_path,kind,damage):
    t=tools(tmp_path);b,exe=write_build(tmp_path,t,kind,damage)
    if damage and not (damage=='wrong-arch' and kind=='cxx'):
        with pytest.raises(ValueError):api().validate_build(b,t,kind,exe)
    else:
        r=api().validate_build(b,t,kind,exe)
        assert r['status']=='COMPILE_LINK_PASS_NOT_EXECUTED' and r['program_invoked'] is False
        assert r['compiler_versions']['CUDA' if kind=='cuda' else 'CXX']==('12.4.131' if kind=='cuda' else '19.38.33135')


def test_cxx_failure_stops_before_cuda_or_native(tmp_path):
    root=tmp_path/'new';root.mkdir()
    class FailureRunner:
        def __init__(self):self.names=[]
        def run(self,name,*args,**kwargs):
            self.names.append(name)
            raise RuntimeError('original CXX configure failure')
    runner=FailureRunner()
    with pytest.raises(RuntimeError,match='original CXX'):api().run_prechecks(tmp_path/'code',root,tools(tmp_path),runner,{})
    assert runner.names==['cxx_configure']


def test_actual_stage1_file_consumer_reuses_cpu_and_gates_native_on_both_prechecks(tmp_path,monkeypatch):
    from test_native_stage1 import test_cpu_file_chain_runs_all_stage1_steps_and_creates_bound_receipts
    test_cpu_file_chain_runs_all_stage1_steps_and_creates_bound_receipts(tmp_path,monkeypatch,ninja=True)


@pytest.mark.parametrize('damage',['sdk','version','executed','swap'])
def test_new_receipt_refuses_changed_compile_evidence_even_if_rehashed(tmp_path,monkeypatch,damage):
    from test_native_stage1 import test_cpu_file_chain_runs_all_stage1_steps_and_creates_bound_receipts
    from exposedpath import native_stage1 as s,native_llama as n
    test_cpu_file_chain_runs_all_stage1_steps_and_creates_bound_receipts(tmp_path,monkeypatch,ninja=True)
    root=tmp_path/'diagnostics/new';b=s.read(root/'build_receipt.json');c=s.read(root/'conversion_receipt.json')
    ref=b['compile_link_prechecks']['cuda'];p=Path(ref['path']);v=s.read(p)
    if damage=='sdk':v['sdk_version']='10.0.26100.0'
    if damage=='version':v['compiler_versions']['CUDA']='12.6.0'
    if damage=='executed':v['program_invoked']=True
    if damage=='swap':v['compiler_versions']={'C':'19.38.33135','CXX':'19.38.33135'}
    p.write_text(json.dumps(v),encoding='utf-8')
    ref.update(sha256=s.digest(p),size_bytes=p.stat().st_size)
    with pytest.raises(ValueError):n._validate_receipts(b,c)


def test_review_manifest_keeps_new_route_version_and_actual_compile_files(tmp_path):
    from exposedpath import native_stage1 as stage
    import zipfile
    root=tmp_path/'run';root.mkdir()
    stage.write(root/'receipt.json',{'schema_version':'exposedpath-native-stage1/0.2.0','status':'BLOCKED'})
    d=root/'cuda-precheck/CMakeFiles/3.31.10';d.mkdir(parents=True)
    (d/'CMakeCUDACompiler.cmake').write_bytes(b'actual compiler facts')
    stage.pack_review(root,tmp_path/'return.zip')
    with zipfile.ZipFile(tmp_path/'return.zip') as z:
        m=json.loads(z.read('artifact_manifest.json'))
        assert m['schema_version']=='exposedpath-native-stage1/0.2.0'
        assert z.read('cuda-precheck/CMakeFiles/3.31.10/CMakeCUDACompiler.cmake')==b'actual compiler facts'
