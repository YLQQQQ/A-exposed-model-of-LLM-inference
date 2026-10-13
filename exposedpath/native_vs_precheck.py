"""Bounded VS discovery facts and C/C++-only compile/link precheck.

No installer, CUDA language, model or binary execution. Inspection is read-only
outside a new diagnostic root. A precheck is separate and needs bound facts.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil

if __package__:
    from . import native_stage1 as stage
else:  # byte-bound standalone copy beside native_stage1.py
    import importlib.util
    spec=importlib.util.spec_from_file_location('native_stage1',Path(__file__).resolve().with_name('native_stage1.py'))
    stage=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stage)  # -I excludes script directory; no search-path fallback

VERSION='exposedpath-native-vs-check/0.1.0'


def file_fact(path):
    p=Path(path)
    stage.checked(p.parent,p.name)
    value=dict(path=str(p),exists=p.is_file())
    if value['exists']:value.update(size_bytes=p.stat().st_size,sha256=stage.digest(p))
    return value


def inspect_files(cfg,root,runner):
    """Query installer once per predicate; preserve absence/failure as unknown."""
    root=Path(root);vs=Path(cfg['vs_root']);prior=Path(cfg['prior_root'])
    exe=Path(cfg['vswhere']);queries={};errors={}
    env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
    env['GIT_OPTIONAL_LOCKS']='0'
    predicates={'all':['-all'], 'vc':['-requires','Microsoft.VisualStudio.Component.VC.Tools.x86.x64'],
        'msbuild':['-requires','Microsoft.Component.MSBuild'],
        'qualified':['-requires','Microsoft.VisualStudio.Component.VC.Tools.x86.x64','Microsoft.Component.MSBuild']}
    for name,args in predicates.items():
        queries[name]=None
        if not exe.is_file():errors[name]='VSWHERE_FILE_MISSING';continue
        try:
            raw=runner.run('vswhere_'+name,[exe,'-nologo','-products','*','-version','[17.0,18.0)',
                '-format','json','-utf8',*args],env=env)
            value=json.loads(raw.decode('utf-8-sig'))
            stage.require(isinstance(value,list) and all(isinstance(r,dict) for r in value),'VSWHERE_STRUCTURE')
            queries[name]=value
        except (ValueError,UnicodeError,OSError,RuntimeError) as e:errors[name]=str(e)
    paths={'cl':vs/'VC/Tools/MSVC/14.38.33130/bin/Hostx64/x64/cl.exe',
        'msbuild_x64':vs/'MSBuild/Current/Bin/amd64/MSBuild.exe',
        'msbuild_x86':vs/'MSBuild/Current/Bin/MSBuild.exe',
        'vctools_default':vs/'VC/Auxiliary/Build/Microsoft.VCToolsVersion.default.txt',
        'devshell':vs/'Common7/Tools/Microsoft.VisualStudio.DevShell.dll',
        'cuda_props':vs/'MSBuild/Microsoft/VC/v170/BuildCustomizations/CUDA 12.4.props',
        'cuda_targets':vs/'MSBuild/Microsoft/VC/v170/BuildCustomizations/CUDA 12.4.targets',
        'cmake':prior/'converter/Lib/site-packages/cmake/data/bin/cmake.exe'}
    files={k:file_fact(p) for k,p in paths.items()}
    default=None
    if files['vctools_default']['exists']:
        try:
            version=paths['vctools_default'].read_text(encoding='utf-8-sig').strip()
            stage.require(re.fullmatch(r'\d+\.\d+\.\d+',version) is not None,'VS_DEFAULT_TOOLS_VERSION')
            d=stage.checked(vs,'VC/Tools/MSVC/'+version)
            default=dict(observed_version=version,directory_exists=d.is_dir())
        except (ValueError,UnicodeError,OSError) as e:default=dict(error=str(e))
    sdk=Path(cfg['sdk_root']);sdks=[]
    inc=sdk/'Include'
    if inc.is_dir():
        stage.checked(sdk,'Include')
        for d in sorted(inc.iterdir()):
            if not d.is_dir() or not re.fullmatch(r'10\.0\.\d+\.0',d.name):continue
            sdks.append(dict(version=d.name,files=[file_fact(p) for p in
                (d/'um/Windows.h',d/'ucrt/stdio.h',sdk/'Lib'/d.name/'um/x64/kernel32.lib',
                 sdk/'Lib'/d.name/'ucrt/x64/ucrt.lib')]))
    cache=file_fact(prior/'build/CMakeCache.txt')
    if cache['exists']:shutil.copyfile(cache['path'],root/'CMakeCache.review.txt')
    configure=file_fact(prior/'build/CMakeFiles/CMakeConfigureLog.yaml')
    if configure['exists']:
        (root/'logs').mkdir(exist_ok=True)
        shutil.copyfile(configure['path'],root/'logs/prior_CMakeConfigureLog.yaml')
    return dict(schema_version=VERSION,status='FACTS_COMPLETE_NOT_TOOLCHAIN_PASS',vs_root=str(vs),
        vswhere=file_fact(exe),queries=queries,query_errors=errors,files=files,vctools_default=default,windows_sdks=sdks,
        prior_cache=cache,prior_configure_log=configure,
        environment={k:os.environ.get(k) for k in ('VSINSTALLDIR','VisualStudioVersion','VS170COMNTOOLS',
            'VCToolsVersion','VSCMD_ARG_HOST_ARCH','VSCMD_ARG_TGT_ARCH','EnterpriseWDK','DisableRegistryUse')},
        model_executed=False,cuda_initialized=False,collector_executed=False)


def bind_instance(facts,vs_root):
    stage.require(facts.get('schema_version')==VERSION and
        facts.get('status')=='FACTS_COMPLETE_NOT_TOOLCHAIN_PASS','VS_FACTS_VERSION_OR_STATUS')
    rows=facts['queries'].get('qualified')
    stage.require(isinstance(rows,list),'VS_QUERY_UNKNOWN')
    matches=[r for r in rows if Path(r.get('installationPath','')).resolve()==Path(vs_root).resolve()]
    stage.require(len(matches)==1,'VS_INSTANCE_MISSING_OR_AMBIGUOUS')
    row=matches[0];version=row.get('installationVersion','')
    stage.require(row.get('isComplete') is True and row.get('isLaunchable') is True
        and re.fullmatch(r'17\.\d+\.\d+\.\d+',version) is not None,'VS_INSTANCE_STATE_OR_VERSION')
    # Do not invent a portable version if Installer cannot report this instance.
    return str(Path(vs_root).resolve())+',version='+version


def probe_plan(cmake,source,root,instance):
    build=Path(root)/'cxx-build'
    return [dict(name='cxx_configure',argv=list(map(str,[cmake,'-S',source,'-B',build,
        '-G','Visual Studio 17 2022','-A','x64','-T','version=14.38.33130',
        '-DCMAKE_GENERATOR_INSTANCE='+instance]))),
        dict(name='cxx_compile_link',argv=list(map(str,[cmake,'--build',build,'--config','Release',
            '--target','native-toolchain-check','--','/nodeReuse:false','/m:2'])))]


def run_probe_steps(steps,runner):
    env={k:v for k,v in os.environ.items() if k not in
        ('CMAKE_GENERATOR','CMAKE_GENERATOR_INSTANCE','CMAKE_GENERATOR_PLATFORM','CMAKE_GENERATOR_TOOLSET')}
    env['CUDA_VISIBLE_DEVICES']='-1'
    for step in steps:
        print('[stage] '+step['name']+' START',flush=True)
        runner.run(step['name'],step['argv'],env=env,timeout=300)
        print('[stage] '+step['name']+' COMPLETE',flush=True)


def validate_probe_cache(cache,instance):
    # CMake 3.31.10 replaces the instance specification with selected location
    # in its cache. Version remains bound by the input facts and configure argv.
    location=instance.split(',version=',1)[0]
    actual=cache.get('CMAKE_GENERATOR_INSTANCE','')
    stage.require(Path(actual).is_absolute() and Path(actual).resolve()==Path(location).resolve()
        and cache.get('CMAKE_GENERATOR')=='Visual Studio 17 2022'
        and cache.get('CMAKE_GENERATOR_PLATFORM')=='x64'
        and cache.get('CMAKE_GENERATOR_TOOLSET')=='version=14.38.33130','VS_PRECHECK_CACHE_CONFLICT')


def precheck(cfg,package,root,facts_path,expected_sha):
    """Explicit second action after facts review; never called by inspect."""
    package=Path(package);root=Path(root);fp=Path(facts_path)
    stage.require(stage.digest(fp)==expected_sha,'VS_FACTS_HASH')
    facts=stage.read(fp);instance=bind_instance(facts,cfg['vs_root'])
    for name in ('cl','msbuild_x64','cmake'):
        old=facts['files'][name];now=file_fact(old['path'])
        stage.require(old==now and now['exists'],'VS_TOOL_CHANGED_OR_MISSING:'+name)
    stage.require(stage.read(cfg['prior_root']+'/toolchain.json')['cl_sha256'].lower()
        ==facts['files']['cl']['sha256'],'VS_ORIGINAL_COMPILER_BINDING')
    stage.require(not (root/'cxx-build').exists(),'VS_PRECHECK_NO_RESUME')
    source=package/'cxx_probe'
    runner=stage.Runner(root)
    receipt=dict(schema_version=VERSION,status='BLOCKED',facts_sha256=expected_sha,
        generator_instance=instance,automatic_retry=False,executable_invoked=False,
        cuda_initialized=False,model_executed=False,collector_executed=False)
    try:
        run_probe_steps(probe_plan(facts['files']['cmake']['path'],source,root,instance),runner)
        cache=stage.read_cache(root/'cxx-build/CMakeCache.txt')
        validate_probe_cache(cache,instance)
        for language in ('C','CXX'):
            compiler=root/'cxx-build/CMakeFiles/3.31.10'/('CMake'+language+'Compiler.cmake')
            text=compiler.read_text(encoding='utf-8')
            stage.require('set(CMAKE_'+language+'_COMPILER_VERSION "19.38.33135")' in text,'VS_PRECHECK_COMPILER_VERSION')
        binary=root/'cxx-build/Release/native-toolchain-check.exe'
        stage.require(binary.is_file(),'VS_PRECHECK_LINK_OUTPUT_MISSING')
        receipt.update(status='CXX_COMPILE_LINK_PASS_NOT_CUDA_QUALIFICATION',binary=file_fact(binary),cache=cache)
    except BaseException as e:receipt['error']=str(e);raise
    finally:receipt['steps']=runner.records;stage.write(root/'precheck_receipt.json',receipt)
    return receipt


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('inspect','precheck'))
    p.add_argument('--config',required=True);p.add_argument('--package',required=True)
    p.add_argument('--root',required=True);p.add_argument('--facts');p.add_argument('--facts-sha256')
    a=p.parse_args();cfg=stage.read(a.config);root=Path(a.root);package=Path(a.package)
    stage.require(cfg['schema_version']==VERSION and cfg['model_process_budget']==cfg['profile_budget']==0,'VS_ROLE')
    stage.require(root.resolve().is_relative_to(Path(cfg['server_root']).resolve()/'diagnostics'),'VS_OUTPUT_SCOPE')
    stage.checked(root.parent,root.name)
    stage.require(not stage.verify_files(package,stage.read(package/'package_manifest.json')['files']),'VS_PACKAGE_CONFLICT')
    if root.exists():raise FileExistsError(root)
    root.mkdir(parents=True);runner=stage.Runner(root)
    receipt=dict(schema_version=VERSION,status='BLOCKED',error=None,action=a.action,automatic_retry=False,
        expected_checkout=cfg['expected_checkout'],model_executed=False,cuda_initialized=False,collector_executed=False)
    try:
        env=dict(os.environ,GIT_OPTIONAL_LOCKS='0')
        for k in list(env):
            if k.startswith('GIT_') and k!='GIT_OPTIONAL_LOCKS':env.pop(k)
        head=runner.run('checkout_head',[cfg['git'],'-C',cfg['code_root'],'rev-parse','HEAD'],env=env).decode('ascii').strip()
        clean=runner.run('checkout_clean',[cfg['git'],'-C',cfg['code_root'],'status','--porcelain'],env=env).strip()
        stage.require(head==cfg['expected_checkout'] and not clean,'VS_CHECKOUT_IDENTITY')
        stage.require(stage.digest(Path(cfg['prior_root'])/'receipt.json')==cfg['prior_receipt_sha256'],'VS_PRIOR_RECEIPT_BINDING')
        stage.require(stage.digest(Path(cfg['prior_root'])/'toolchain.json')==cfg['prior_toolchain_sha256'],'VS_PRIOR_TOOLCHAIN_BINDING')
        if a.action=='inspect':
            facts=inspect_files(cfg,root,runner);stage.write(root/'vs_facts.json',facts)
            receipt.update(status='FACTS_COMPLETE_NOT_TOOLCHAIN_PASS',facts_sha256=stage.digest(root/'vs_facts.json'))
        else:
            value=precheck(cfg,package,root,a.facts,a.facts_sha256)
            receipt.update(status=value['status'],precheck_receipt_sha256=stage.digest(root/'precheck_receipt.json'))
    except BaseException as e:receipt['error']=str(e);raise
    finally:receipt['steps']=runner.records;stage.write(root/'receipt.json',receipt)


if __name__=='__main__':main()
