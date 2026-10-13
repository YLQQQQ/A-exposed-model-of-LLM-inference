"""CPU checks for bounded VS facts/binding; not target MSVC qualification."""
import importlib
import json
from pathlib import Path

import pytest


def api():
    return importlib.import_module('exposedpath.native_vs_precheck')


def facts(tmp_path):
    root=tmp_path/'VS'
    row=dict(installationPath=str(root),installationVersion='17.8.34330.188',
        isComplete=True,isLaunchable=True,instanceId='observed-instance')
    return dict(schema_version='exposedpath-native-vs-check/0.1.0',
        status='FACTS_COMPLETE_NOT_TOOLCHAIN_PASS',vs_root=str(root),
        queries={'all':[row],'vc':[row],'msbuild':[row],'qualified':[row]})


def test_binding_uses_reported_instance_version_not_compiler_version(tmp_path):
    value=api().bind_instance(facts(tmp_path),tmp_path/'VS')
    assert value==str(tmp_path/'VS')+',version=17.8.34330.188'


@pytest.mark.parametrize('change', ['missing','incomplete','wrong-root','wrong-version','ambiguous','query-failed'])
def test_unproved_instance_cannot_be_selected_from_compiler_presence(tmp_path,change):
    f=facts(tmp_path)
    if change=='missing':f['queries']['qualified']=[]
    if change=='incomplete':f['queries']['qualified'][0]['isComplete']=False
    if change=='wrong-root':f['queries']['qualified'][0]['installationPath']=str(tmp_path/'other')
    if change=='wrong-version':f['queries']['qualified'][0]['installationVersion']='19.38.33135'
    if change=='ambiguous':f['queries']['qualified'].append(dict(f['queries']['qualified'][0]))
    if change=='query-failed':f['queries']['qualified']=None
    with pytest.raises(ValueError):api().bind_instance(f,tmp_path/'VS')


def test_probe_uses_same_generator_toolchain_and_fresh_build_without_cuda(tmp_path):
    steps=api().probe_plan(tmp_path/'cmake.exe',tmp_path/'src',tmp_path/'new',
        str(tmp_path/'VS')+',version=17.8.34330.188')
    assert [s['name'] for s in steps]==['cxx_configure','cxx_compile_link']
    assert steps[0]['argv']==[str(tmp_path/'cmake.exe'),'-S',str(tmp_path/'src'),
        '-B',str(tmp_path/'new'/'cxx-build'),'-G','Visual Studio 17 2022','-A','x64',
        '-T','version=14.38.33130','-DCMAKE_GENERATOR_INSTANCE='+str(tmp_path/'VS')+',version=17.8.34330.188']
    assert steps[1]['argv'][-5:]==['--target','native-toolchain-check','--','/nodeReuse:false','/m:2']
    assert not any('cuda' in a.lower() or a.endswith('native-toolchain-check.exe') for s in steps for a in s['argv'])


def test_cmake_331_cache_stores_selected_location_not_version_argument(tmp_path):
    # Kitware 3.31.10 SetGeneratorInstance writes selected VS location to cache.
    cache={'CMAKE_GENERATOR_INSTANCE':(tmp_path/'VS').as_posix(),
        'CMAKE_GENERATOR':'Visual Studio 17 2022','CMAKE_GENERATOR_PLATFORM':'x64',
        'CMAKE_GENERATOR_TOOLSET':'version=14.38.33130'}
    api().validate_probe_cache(cache,str(tmp_path/'VS')+',version=17.8.34330.188')
    cache['CMAKE_GENERATOR_INSTANCE']=(tmp_path/'other').as_posix()
    with pytest.raises(ValueError):api().validate_probe_cache(cache,str(tmp_path/'VS')+',version=17.8.34330.188')


def test_failed_real_subprocess_preserves_error_and_stops_before_link(tmp_path):
    import sys
    from exposedpath import native_stage1 as stage
    root=tmp_path/'run';root.mkdir()
    runner=stage.Runner(root)
    steps=[dict(name='cxx_configure',argv=[sys.executable,'-I','-c',
        'import sys; sys.stderr.buffer.write(b"original configure failure"); sys.exit(9)']),
        dict(name='cxx_compile_link',argv=[sys.executable,'-I','-c','raise AssertionError("must not execute")'])]
    with pytest.raises(ValueError):api().run_probe_steps(steps,runner)
    assert (root/'logs/cxx_configure.stderr.txt').read_bytes()==b'original configure failure'
    assert stage.read(root/'logs/cxx_configure.json')['exit_code']==9
    assert not (root/'logs/cxx_compile_link.json').exists()


def test_inspection_missing_vswhere_keeps_unknown_and_records_component_files(tmp_path):
    from exposedpath import native_stage1 as stage
    cfg=dict(vs_root=str(tmp_path/'VS'),vswhere=str(tmp_path/'missing.exe'),
        prior_root=str(tmp_path/'old'),sdk_root=str(tmp_path/'SDK'))
    old=tmp_path/'old';old.mkdir()
    (old/'build').mkdir();(old/'build/CMakeCache.txt').write_text('CMAKE_GENERATOR_INSTANCE:INTERNAL=\n')
    root=tmp_path/'new';root.mkdir()
    value=api().inspect_files(cfg,root,stage.Runner(root))
    assert value['queries']=={'all':None,'vc':None,'msbuild':None,'qualified':None}
    assert value['vswhere']['exists'] is False
    assert value['files']['msbuild_x64']['exists'] is False
    assert value['prior_cache']['sha256']==stage.digest(old/'build/CMakeCache.txt')
    assert (root/'CMakeCache.review.txt').is_file()
    with pytest.raises(ValueError):api().bind_instance(value,tmp_path/'VS')


def test_successful_query_chain_is_not_a_compile_or_cuda_pass(tmp_path):
    from exposedpath import native_stage1 as stage
    exe=tmp_path/'vswhere.exe';exe.write_bytes(b'CPU substitute')
    root=tmp_path/'new';root.mkdir()
    row=facts(tmp_path)['queries']['all'][0]
    class QueryRunner:
        def run(self,name,argv,**kwargs):
            assert argv[1:]==['-nologo','-products','*','-version','[17.0,18.0)',
                '-format','json','-utf8',*{
                'vswhere_all':['-all'],
                'vswhere_vc':['-requires','Microsoft.VisualStudio.Component.VC.Tools.x86.x64'],
                'vswhere_msbuild':['-requires','Microsoft.Component.MSBuild'],
                'vswhere_qualified':['-requires','Microsoft.VisualStudio.Component.VC.Tools.x86.x64','Microsoft.Component.MSBuild']}[name]]
            return json.dumps([row]).encode('utf-8')
    cfg=dict(vs_root=str(tmp_path/'VS'),vswhere=str(exe),prior_root=str(tmp_path/'old'),sdk_root=str(tmp_path/'SDK'))
    value=api().inspect_files(cfg,root,QueryRunner())
    assert value['status']=='FACTS_COMPLETE_NOT_TOOLCHAIN_PASS'
    assert value['query_errors']=={}
    assert not value['cuda_initialized'] and not value['model_executed']
    stage.write(root/'vs_facts.json',value)
    stage.pack_review(root,tmp_path/'review.zip')
    import zipfile
    with zipfile.ZipFile(tmp_path/'review.zip') as z:
        assert stage.read(root/'vs_facts.json')['queries']['qualified']==[row]
        assert 'vs_facts.json' in z.namelist()


@pytest.mark.parametrize('bad_prior', [False,True])
def test_actual_standalone_inspect_entry_binds_checkout_and_prior_receipt(tmp_path,bad_prior):
    import shutil
    import subprocess
    import sys
    from exposedpath import native_stage1 as stage
    from tests.test_native_stage1 import tiny_repository
    repo=tmp_path/'code';head=tiny_repository(repo)
    old=tmp_path/'old';old.mkdir();stage.write(old/'receipt.json',{'status':'BLOCKED'})
    stage.write(old/'toolchain.json',{'cl_sha256':'a'*64})
    package=tmp_path/'package';package.mkdir()
    for name in ('native_vs_precheck','native_stage1'):
        shutil.copyfile(Path('exposedpath')/(name+'.py'),package/(name+'.py'))
    cfg=dict(schema_version='exposedpath-native-vs-check/0.1.0',model_process_budget=0,profile_budget=0,
        server_root=str(tmp_path),vs_root=str(tmp_path/'VS'),vswhere=str(tmp_path/'missing.exe'),
        prior_root=str(old),sdk_root=str(tmp_path/'SDK'),code_root=str(repo),git=shutil.which('git'),
        expected_checkout=head,prior_receipt_sha256='a'*64 if bad_prior else stage.digest(old/'receipt.json'),
        prior_toolchain_sha256=stage.digest(old/'toolchain.json'))
    stage.write(package/'config.json',cfg)
    stage.write(package/'package_manifest.json',dict(files=[dict(path=p.name,size_bytes=p.stat().st_size,
        sha256=stage.digest(p)) for p in package.iterdir()]))
    root=tmp_path/'diagnostics/new'
    result=subprocess.run([sys.executable,'-I',str(package/'native_vs_precheck.py'),'inspect',
        '--config',str(package/'config.json'),'--package',str(package),'--root',str(root)],capture_output=True)
    receipt=stage.read(root/'receipt.json')
    if bad_prior:
        assert result.returncode!=0 and receipt['status']=='BLOCKED'
        assert 'PRIOR_RECEIPT_BINDING' in receipt['error']
        assert not (root/'vs_facts.json').exists()
    else:
        assert result.returncode==0,result.stderr
        assert receipt['status']=='FACTS_COMPLETE_NOT_TOOLCHAIN_PASS'
        assert receipt['facts_sha256']==stage.digest(root/'vs_facts.json')
        assert stage.read(root/'vs_facts.json')['queries']['qualified'] is None
        assert not (root/'cxx-build').exists()


def test_inspection_keeps_invalid_utf8_raw_and_never_uses_empty_success(tmp_path):
    from exposedpath import native_stage1 as stage
    exe=tmp_path/'vswhere.exe';exe.write_bytes(b'CPU substitute')
    root=tmp_path/'new';root.mkdir()
    class QueryRunner:
        def run(self,name,argv,**kwargs):
            # Windows dependency replaced; parser and error retention stay real.
            return b'\xff'
    cfg=dict(vs_root=str(tmp_path/'VS'),vswhere=str(exe),prior_root=str(tmp_path/'old'),sdk_root=str(tmp_path/'SDK'))
    value=api().inspect_files(cfg,root,QueryRunner())
    assert value['queries']['all'] is None
    assert value['query_errors']['all']
    with pytest.raises(ValueError):api().bind_instance(value,tmp_path/'VS')


def test_cmake_default_vctools_reference_is_observed_not_replaced_by_pin(tmp_path):
    from exposedpath import native_stage1 as stage
    vs=tmp_path/'VS';p=vs/'VC/Auxiliary/Build/Microsoft.VCToolsVersion.default.txt'
    p.parent.mkdir(parents=True);p.write_bytes(b'14.42.34433\r\n')
    root=tmp_path/'new';root.mkdir()
    value=api().inspect_files(dict(vs_root=str(vs),vswhere=str(tmp_path/'missing'),
        prior_root=str(tmp_path/'old'),sdk_root=str(tmp_path/'SDK')),root,stage.Runner(root))
    assert value['vctools_default']=={'observed_version':'14.42.34433','directory_exists':False}
    assert p.read_bytes()==b'14.42.34433\r\n'
