"""File-resource identity checks are not compile/link qualification."""
import importlib
import json
import hashlib
import zipfile
from pathlib import Path
import sys

import pytest


def api():return importlib.import_module('exposedpath.native_ninja')


def resource():
    # Independently specified MSVC14.38 PE file-version resource expectation.
    return dict(file_version='14.38.33135.0',file_type=1,
        fixed_info=[0xFEEF04BD,0x10000,(14<<16)|38,(33135<<16),0,0,0,0,0,1,0,0,0])


@pytest.mark.parametrize('name',['link','lib'])
def test_fixed_file_identity_queries_resource_without_executing_tool(tmp_path,name):
    from exposedpath import native_stage1 as s
    p=tmp_path/(name+'.exe');p.write_bytes(b'CPU PE substitute, not a working compiler')
    expected=s.digest(p);calls=[]
    def reader(path):calls.append(path);return resource()
    root=tmp_path/'new';root.mkdir()
    result=api().msvc_file_identity(name,p,api().fact(p),root,reader=reader)
    assert calls==[p] and result['file']['sha256']==expected
    assert result['status']=='IDENTITY_ONLY_NOT_BUILD_CAPABILITY'
    assert result['tool_invoked'] is False and result['exit_code'] is None
    assert result['resource']['file_version']=='14.38.33135.0'
    assert s.read(root/(name+'_file_identity.json'))==result


@pytest.mark.parametrize('damage',['wrong-tool','bytes','length','missing','version','type','resource','read-error','changed-during-read'])
def test_identity_rejects_conflicts_and_keeps_diagnostic(tmp_path,damage):
    from exposedpath import native_stage1 as s
    p=tmp_path/'link.exe';p.write_bytes(b'fixed tool bytes');expected=api().fact(p)
    root=tmp_path/'new';root.mkdir()
    if damage=='wrong-tool':p=p.rename(tmp_path/'cl.exe')
    if damage=='bytes':p.write_bytes(b'wrong tool bytes')
    if damage=='length':expected['size_bytes']+=1
    if damage=='missing':p.unlink()
    def reader(path):
        if damage=='read-error':raise OSError('deliberate resource-read failure')
        r=resource()
        if damage=='version':r['file_version']='14.44.35207.0'
        if damage=='type':r['file_type']=2
        if damage=='resource':r['fixed_info'][0]=0
        if damage=='changed-during-read':path.write_bytes(b'tool changed during read')
        return r
    with pytest.raises((ValueError,OSError)):api().msvc_file_identity('link',p,expected,root,reader=reader)
    report=s.read(root/'link_file_identity.json')
    assert report['status']=='BLOCKED' and report['error']
    assert report['tool_invoked'] is False


def test_real_windows_file_version_reader_does_not_run_executable():
    if sys.platform!='win32':pytest.skip('Windows PE version adapter')
    r=api().read_pe_version(Path(sys.executable))
    assert r['fixed_info'][0]==0xFEEF04BD and r['file_type']==1
    assert r['file_version'].startswith(str(sys.version_info.major)+'.'+str(sys.version_info.minor)+'.')


def test_raw_link_help_exit_1100_is_still_failure_for_build_runner(tmp_path,monkeypatch):
    from exposedpath import native_stage1 as s
    # Raw return/banner reproduced from the sealed target receipt; no private path.
    raw=b'Microsoft (R) Incremental Linker Version 14.38.33135.0\r\n'
    raw+=b'Copyright (C) Microsoft Corporation.  All rights reserved.\r\n'
    raw+=b'LINK [options] [files] [@commandfile]\r\n /OUT:file\r\n /MACHINE:X64\r\n'
    class Child:
        pid=123
        def __init__(self,argv,stdout,stderr,**kw):stdout.write(raw)
        def wait(self,timeout):return 1100
    monkeypatch.setattr(s.subprocess,'Popen',Child)
    runner=s.Runner(tmp_path)
    with pytest.raises(ValueError,match='STEP_EXIT'):runner.run('link_version',['link.exe','/?'])
    receipt=s.read(tmp_path/'logs/link_version.json')
    assert receipt['exit_code']==1100 and receipt['error']
    assert (tmp_path/'logs/link_version.stdout.txt').read_bytes()==raw
    assert (tmp_path/'logs/link_version.stderr.txt').read_bytes()==b''


@pytest.mark.parametrize('damage',[None,'source-commit','expected-commit','error'])
def test_old_cpu_source_identity_is_separate_from_deployment_prerequisite(damage):
    cfg=dict(prerequisite='b'*40,reuse_cpu_commit='a'*40)
    old=dict(execution_commit='a'*40,error='NATIVE_STAGE1_STEP_EXIT:configure')
    observation=dict(expected_checkout='a'*40)
    if damage=='source-commit':old['execution_commit']='c'*40
    if damage=='expected-commit':observation['expected_checkout']='b'*40
    if damage=='error':old['error']=None
    if damage:
        with pytest.raises(ValueError):api().validate_prior_roles(cfg,old,observation)
    else:api().validate_prior_roles(cfg,old,observation)


def sealed(root,files):
    with zipfile.ZipFile(root,'x') as z:
        rows=[]
        for name,obj in files.items():
            data=json.dumps(obj,sort_keys=True).encode();z.writestr(name,data)
            rows.append(dict(path=name,size_bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
        z.writestr('artifact_manifest.json',json.dumps(dict(files=rows)))


@pytest.mark.parametrize('damage',[None,'deploy-moved','query-version','query-source','query-tool','query-diagnostic'])
def test_production_binder_consumes_real_reference_files_and_never_launches_help(tmp_path,monkeypatch,damage):
    from exposedpath import native_stage1 as s
    a=api();package=tmp_path/'package';package.mkdir();root=tmp_path/'new';root.mkdir()
    prior=tmp_path/'prior';sdk=tmp_path/'sdk';cuda=tmp_path/'cuda';vc=tmp_path/'vs/VC/Tools/MSVC/14.38.33130'
    cfg=dict(vs_root=str(tmp_path/'vs'),sdk_root=str(sdk),cuda_root=str(cuda),reuse_cpu_root=str(prior),
        prerequisite='b'*40,reuse_cpu_commit='a'*40,tool_identity_version=a.TOOL_IDENTITY_VERSION,query_reference_commit='b'*40)
    paths={k:vc/('bin/Hostx64/x64/'+k+'.exe') for k in ('cl','link','lib')}
    paths.update(rc=sdk/'bin/10.0.20348.0/x64/rc.exe',mt=sdk/'bin/10.0.20348.0/x64/mt.exe',
        nvcc=cuda/'bin/nvcc.exe',ninja=package/'ninja.exe',cmake=prior/'converter/Lib/site-packages/cmake/data/bin/cmake.exe',
        python=prior/'converter/Scripts/python.exe')
    for rel in ('lib/x64/vcruntime.lib','lib/x64/msvcrt.lib','lib/x64/msvcprt.lib','include/vector'):paths[rel]=vc/rel
    for rel in ('Lib/10.0.20348.0/um/x64/kernel32.lib','Lib/10.0.20348.0/ucrt/x64/ucrt.lib',
        'Include/10.0.20348.0/um/Windows.h','Include/10.0.20348.0/ucrt/stdio.h'):paths[rel]=sdk/rel
    for rel in ('include/cuda_runtime.h','lib/x64/cudart.lib','lib/x64/cudart_static.lib','lib/x64/cuda.lib','lib/x64/cublas.lib'):paths[rel]=cuda/rel
    for key,p in paths.items():p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(('CPU file '+key).encode())
    module=prior/'converter/Lib/site-packages/cmake/data/share/cmake-3.31/Modules/Internal/CMakeCUDAArchitecturesNative.cmake'
    module.parent.mkdir(parents=True);module.write_bytes(s.PROBE_SHIM.encode())
    patch=dict(original_sha256='c'*64,patched_sha256=s.digest(module));cfg['cmake_probe_sha256']='c'*64
    old=dict(execution_commit='a'*40,error='NATIVE_STAGE1_STEP_EXIT:configure')
    old_tool=dict(nvcc_sha256=s.digest(paths['nvcc']))
    originals={'receipt.json':old,'toolchain.json':old_tool,'cmake_probe_patch.json':patch}
    sealed(package/'prior_review.zip',originals)
    for name,obj in originals.items():(prior/name).write_bytes(json.dumps(obj,sort_keys=True).encode())
    observed=dict(files={k:a.fact(paths[k]) for k in ('cl','cmake')},windows_sdks=[dict(version=a.SDK_VERSION,files=[])])
    sealed(package/'vs_facts.zip',{'receipt.json':dict(expected_checkout='a'*40),'vs_facts.json':observed})
    query=dict(execution_commit='b'*40,error='NATIVE_STAGE1_STEP_EXIT:link_version',model_executed=False,
        cuda_initialization_program_invoked=False,collector_executed=False)
    query_files={k:a.fact(paths[k]) for k in ('link','lib')}
    if damage=='query-version':cfg['tool_identity_version']='unknown/1'
    if damage=='query-source':query['execution_commit']='d'*40
    if damage=='query-tool':query_files['lib']['sha256']='0'*64
    if damage=='query-diagnostic':query['error']='different failure'
    if damage=='deploy-moved':cfg['prerequisite']='e'*40
    sealed(package/'query_review.zip',{'receipt.json':query,'toolchain_prerequisites.json':dict(files=query_files)})
    for key,name in [('prior_review_sha256','prior_review.zip'),('vs_facts_zip_sha256','vs_facts.zip'),('query_review_sha256','query_review.zip')]:cfg[key]=s.digest(package/name)
    monkeypatch.setattr(a,'NINJA_SHA256',s.digest(paths['ninja']))
    monkeypatch.setattr(a,'read_pe_version',lambda p:resource())
    class QueryRunner:
        def __init__(self):self.calls=[]
        def run(self,name,argv,**kw):self.calls.append((name,argv));assert name=='ninja_version';return b'1.12.1\n'
    runner=QueryRunner()
    if damage not in (None,'deploy-moved'):
        with pytest.raises(ValueError):a.bind_tools(cfg,package,root,runner)
    else:
        tools,env=a.bind_tools(cfg,package,root,runner)
        report=s.read(root/'toolchain.json')
        assert report['reuse_cpu_commit']=='a'*40 and report['tool_identity_version']==a.TOOL_IDENTITY_VERSION
        assert set(report['tool_identities'])=={'link','lib'}
        assert tools['link']==str(paths['link']) and env['CUDA_VISIBLE_DEVICES']=='-1'
    assert all('/?' not in argv for name,argv in runner.calls)


def test_packager_requires_deployment_and_old_cpu_source_as_separate_identities():
    import inspect
    from scripts import package_native_llama_stage1 as p
    assert 'prerequisite' in inspect.signature(p.assemble_ninja).parameters
