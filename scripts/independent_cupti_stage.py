"""Stage A only: deployment, real-header build/link, Host doubles. No GPU run action."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sys


def support():
    sibling=Path(__file__).with_name('micro_support.py')
    if sibling.is_file():
        spec=importlib.util.spec_from_file_location('_cupti_micro_support',sibling)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
    from scripts import memset_micro
    return memset_micro


def verify_rows(root,rows):return support().verify_rows(root,rows)


def inspect_exports(config,runtime,cupti,out):
    m=support();out=Path(out);out.mkdir(parents=True,exist_ok=True)
    tool=Path(config['vc_root'])/'bin/Hostx64/x64/dumpbin.exe'
    required={'cupti':('cuptiGetVersion','cuptiGetCallbackName','cuptiUnsubscribe','cuptiFinalize','cuptiActivityDisable',
        'cuptiActivityFlushAll','cuptiActivityGetNextRecord','cuptiActivityGetNumDroppedRecords',
        'cuptiSubscribe','cuptiActivityRegisterCallbacks','cuptiSetThreadIdType','cuptiEnableCallback',
        'cuptiEnableDomain','cuptiGetContextId','cuptiGetDeviceId','cuptiGetStreamIdEx','cuptiActivityEnable'),
        'runtime':('cudaRuntimeGetVersion','cudaSetDevice','cudaStreamCreateWithFlags','cudaMalloc',
        'cudaMemcpy','cudaMemsetAsync','cudaStreamSynchronize','cudaFree','cudaStreamDestroy')}
    for name,path in (('runtime',runtime),('cupti',cupti)):
        m.command([str(tool),'/exports',str(path)],out,out/(name+'_exports'),env=m.compile_environment(config))
        text=(out/(name+'_exports.stdout')).read_bytes().decode('utf8',errors='replace')
        for symbol in required[name]:m.require(re.search(r'\b'+symbol+r'\b',text),'MISSING_EXPORT:'+symbol)
    result=dict(inspection='PE_BYTES_ONLY_NO_VENDOR_LOAD',vendor_dll_loaded=False,
        dumpbin=m.file_fact(tool),required_cupti_exports=len(required['cupti']),
        required_runtime_exports=len(required['runtime']))
    m.write(out/'exports.json',result);return result


def build_native(config,output):
    m=support();out=Path(output);out.mkdir(parents=True,exist_ok=True)
    root=Path(config.get('source_root',Path(__file__).resolve().parents[1]))
    # Packaged bootstrap calls this function from the verified checkout module.
    vc=Path(config['vc_root']);tools={n:str(vc/'bin/Hostx64/x64'/(n+'.exe')) for n in ('cl','link','dumpbin')}
    env=m.compile_environment(config)
    inc=[config[n] for n in ('cuda_include','crt_include','cupti_include')]
    m.require(all(Path(p).is_dir() for p in inc),'SDK_INCLUDE_MISSING')
    source=root/'scripts/native_cupti_memset';built={};imports={}
    for name in ('host_test','host_client_test','micro'):
        target=out/(name+'.exe')
        argv=[tools['cl'],'/nologo','/std:c++17','/EHsc','/MT','/Od','/W4','/WX','/utf-8',
            '/DWIN32_LEAN_AND_MEAN',*['/I'+p for p in inc],str(source/(name+'.cpp')),
            '/Fo:'+str(out/(name+'.obj')),'/Fe:'+str(target),'/link','bcrypt.lib']
        m.command(argv,out,out/('build_'+name),env=env)
        imports[name]=m.pe_imports(target,tools['dumpbin'],env,out)
        built[name]=str(target)
    built.update(micro_invoked=False,cuda_header_version=12040,cupti_header_version=22,
        imports=imports,tools={k:m.file_fact(p) for k,p in tools.items()},
        binary_files=[dict(path=Path(built[k]).name,bytes=Path(built[k]).stat().st_size,sha256=m.sha(built[k]))
                      for k in ('host_test','host_client_test','micro')])
    m.write(out/'build.json',built)
    return built


def verify_sources(code,representations):
    m=support();seen=[]
    for name,choices in representations.items():
        p=m.safe(code,name);actual=m.file_fact(p)
        m.require(any(actual['bytes']==r['bytes'] and actual['sha256']==r['sha256'] for r in choices),
            'SOURCE_BYTES:'+name)
        seen.append(dict(path=name,bytes=actual['bytes'],sha256=actual['sha256']))
    m.require(seen,'EMPTY_SOURCE_INDEX');return seen


def deploy(cfg,package,out):
    m=support();m.tree(cfg,cfg['prerequisite'])
    m.command([cfg['git'],'bundle','verify',str(package/'execution.bundle')],cfg['code_root'],out/'bundle_verify')
    ref='refs/remotes/independent-cupti/execution'
    m.command([cfg['git'],'-C',cfg['code_root'],'fetch',str(package/'execution.bundle'),'HEAD:'+ref],
        cfg['code_root'],out/'fetch')
    m.require(m.git_text(cfg['git'],cfg['code_root'],'rev-parse',ref)==cfg['execution_commit'],'BUNDLE_TARGET')
    m.command([cfg['git'],'-C',cfg['code_root'],'-c','core.autocrlf=false','checkout','--detach',cfg['execution_commit']],
        cfg['code_root'],out/'checkout')


def startup_resources(out,archive,cfg):
    m=support();r=m.resources(out,archive)
    for v in r['volumes'].values():
        m.require(v['free_bytes']>=cfg['temporary_required_bytes'],'FREE_SPACE')
        v['required_bytes']=cfg['temporary_required_bytes']
    return r


def stage_a(package):
    m=support();package=Path(package).resolve();index=m.verify_package(package)
    cfg=json.loads((package/'delivery.json').read_text(encoding='utf8'))
    m.require(cfg.get('schema_version')=='independent-cupti-stage-a/0.1.0' and
        cfg.get('default_stage')=='A_ONLY_NO_B_ENTRY' and
        cfg.get('micro_process_budget')==cfg.get('model_process_budget')==cfg.get('profile_budget')==0 and
        cfg.get('execution_commit')==cfg.get('analysis_commit') and
        re.fullmatch('[0-9a-f]{40}',cfg['execution_commit']) and
        bool(cfg.get('sdk_files')) and bool(cfg.get('cupti_files')) and
        cfg.get('prerequisite')=='9c78e355bb43a8696f7eccb44c48d8448f366d09','A_ONLY_DELIVERY')
    root=Path(cfg['server_root']);code=Path(cfg['code_root']);tag=cfg['execution_commit'][:12]
    out=m.safe(root,'diagnostics/independent_cupti_'+tag+'_static')
    archive=m.safe(root,'transfer/independent_cupti_'+tag+'_static.zip')
    m.require(not out.exists() and not archive.exists(),'NO_OVERWRITE_RESUME_RETRY')
    out.mkdir(parents=True,exist_ok=False);archive.parent.mkdir(parents=True,exist_ok=True)
    for name in ('delivery.json','package_manifest.json','prerequisite_reference.json','dependency_sources.json'):
        if (package/name).is_file():shutil.copyfile(package/name,out/name)
    status='BLOCKED';error=None
    try:
        m.require(list(sys.version_info[:3])==cfg['python_version'],'PYTHON_VERSION')
        deploy(cfg,package,out);m.tree(cfg,cfg['execution_commit'])
        m.write(out/'source_bytes.json',verify_sources(code,cfg['source_representations']))
        m.write(out/'resources.json',startup_resources(out,archive,cfg))
        for name,fact in cfg['toolchain_files'].items():
            m.require(m.file_fact(fact['path'])==fact,'TOOLCHAIN:'+name)
        runtime=m.runtime_fact(cfg['runtime_path']);m.write(out/'runtime_file.json',runtime)
        m.extract(package/'sdk.zip',out/'sdk');m.extract(package/'cupti.zip',out/'cupti')
        m.verify_rows(out/'sdk',cfg['sdk_files']);m.verify_rows(out/'cupti',cfg['cupti_files'])
        cupti=out/'cupti/lib/cupti64_2024.1.1.dll'
        m.require(m.sha(cupti)==cfg['cupti_dll_sha256'],'CUPTI_FILE_IDENTITY')
        m.write(out/'cupti_file.json',m.file_fact(cupti))
        build=dict(cfg['build'],source_root=str(code),runtime_path=cfg['runtime_path'],cuda_include=str(out/'sdk/include'),
            crt_include=str(out/'sdk/include'),cupti_include=str(out/'cupti/include'))
        inspect_exports(build,cfg['runtime_path'],cupti,out/'export_inspection')
        built=build_native(build,out/'build');m.write(out/'build_configuration.json',build)
        env=os.environ.copy()
        for k in ('PYTEST_ADDOPTS','PYTEST_PLUGINS'):env.pop(k,None)
        env.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',CUDA_VISIBLE_DEVICES='-1',
            INDEPENDENT_CUPTI_CPU_CONFIG=str(out/'build_configuration.json'),
            INDEPENDENT_CUPTI_BUILT_JSON=str(out/'build/build.json'))
        m.command([cfg['python'],'-X','utf8','-m','pytest','-q','-ra','-p','no:cacheprovider',
            'tests/test_independent_cupti_memset.py','tests/test_independent_cupti_native.py',
            'tests/test_independent_cupti_delivery.py','--basetemp',str(out/'cpu_tmp'),
            '--junitxml',str(out/'cpu.xml')],code,out/'cpu',env=env,timeout=300)
        import xml.etree.ElementTree as ET
        suites=ET.parse(out/'cpu.xml').getroot().findall('testsuite')
        m.require(suites and sum(int(x.attrib['tests']) for x in suites)==cfg['cpu_test_count'] and
            all(x.attrib[k]=='0' for x in suites for k in ('failures','errors','skipped')),'CPU_RESULT')
        verify_sources(code,cfg['source_representations']);m.verify_rows(out/'build',built['binary_files'])
        m.verify_rows(out/'sdk',cfg['sdk_files']);m.verify_rows(out/'cupti',cfg['cupti_files'])
        m.require(runtime==m.runtime_fact(cfg['runtime_path']),'RUNTIME_CHANGED_DURING_A')
        m.tree(cfg,cfg['execution_commit']);status='STATIC_READY_FOR_REVIEW'
    except BaseException as exc:error=type(exc).__name__+':'+str(exc)
    static_files={p.name:m.sha(p) for p in out.iterdir() if p.is_file()}
    m.write(out/'receipt.json',dict(schema_version='independent-cupti-stage-a-receipt/0.1.0',phase='A',
        status=status,error=error,execution_commit=cfg['execution_commit'],analysis_commit=cfg['analysis_commit'],
        package_index_sha256=index,static_files=static_files,stage_a_cuda_programs_executed=0,
        B_authorized=False,model_process_budget=0,micro_process_budget=0,profile_budget=0,
        automatic_retry=False,A_COE_admission='NOT_ASSESSED',pytorch_coverage='NOT_ASSESSED',
        historical_ylq_total_bytes=None,long_term_target_exclusive_bytes=50000000000))
    try:print(json.dumps(m.pack(out,archive)),flush=True)
    except BaseException as exc:
        print('PACK_REFUSED_PRESERVE_SCENE:'+str(exc),flush=True);return 2
    if error:print('STOP:'+error,flush=True);return 2
    return 0


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--package',required=True,type=Path)
    a=p.parse_args(argv)
    return stage_a(a.package)


if __name__=='__main__':raise SystemExit(main())
