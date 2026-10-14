"""Offline stage1: compile/convert/file inspection; never execute native binaries.

Safe to use as the byte-bound bootstrap copy in a delivery package. Conversion
uses a NEW CPU-only environment. No CUDA/Nsight/device-probe imports or commands.
"""
import argparse
import csv
from collections import Counter
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import time
import zipfile

VERSION='exposedpath-native-stage1/0.1.0'
NINJA_VERSION='exposedpath-native-stage1/0.2.0'
CMAKE_VERSION='3.31.10'


def require(ok,reason):
    if not ok:raise ValueError('NATIVE_STAGE1_'+reason)


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path,value):
    with Path(path).open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,sort_keys=True,indent=2);stream.write('\n')


def relative(name):
    require(isinstance(name,str) and name and '\\' not in name and ':' not in name,'PATH')
    p=PurePosixPath(name)
    require(not p.is_absolute() and all(t not in ('','.','..') for t in name.split('/')),'PATH')
    require(all(not t.endswith((' ','.')) and t.split('.')[0].upper() not in
        {'CON','PRN','AUX','NUL',*(f'COM{i}' for i in range(1,10)),*(f'LPT{i}' for i in range(1,10))} for t in p.parts),'PATH')
    return p


def checked(root,name):
    root=Path(root).absolute();p=root.joinpath(*relative(name).parts)
    require(p.resolve().is_relative_to(root.resolve()),'PATH_ESCAPE')
    for part in (p,*p.parents):
        if part.exists():require(not part.is_symlink() and not getattr(part.lstat(),'st_file_attributes',0)&0x400,'REPARSE_POINT')
    return p


def extract(archive,output):
    output=Path(output)
    if output.exists():raise FileExistsError(output)
    with zipfile.ZipFile(archive) as z:
        seen=set()
        for r in z.infolist():
            name=r.filename.rstrip('/') if r.is_dir() else r.filename
            relative(name);require(name.casefold() not in seen,'ZIP_DUPLICATE');seen.add(name.casefold())
            require(not stat.S_ISLNK(r.external_attr>>16),'ZIP_SYMLINK')
        require(z.testzip() is None,'ZIP_CRC')
        output.mkdir(parents=True)
        for r in z.infolist():
            p=checked(output,r.filename.rstrip('/'))
            if r.is_dir():p.mkdir(parents=True,exist_ok=True)
            else:
                p.parent.mkdir(parents=True,exist_ok=True)
                with z.open(r) as src,p.open('xb') as dst:shutil.copyfileobj(src,dst)


def restore_source(archive,output,files,layout=None):
    if layout is not None:
        require(layout.get('schema_version')=='exposedpath-native-source-layout/0.1.0','SOURCE_LAYOUT_VERSION')
        require(digest(archive)==layout['source_archive_sha256'],'SOURCE_LAYOUT_ARCHIVE')
        names=layout['directories'];require(isinstance(names,list) and names,'SOURCE_LAYOUT_EMPTY')
        require(len(names)==len(set(n.casefold() for n in names)),'SOURCE_LAYOUT_DUPLICATE')
        for name in names:relative(name)
    extract(archive,output)
    if layout is not None:
        for name in names:checked(output,name).mkdir(parents=True,exist_ok=True)
        actual={p.relative_to(output).as_posix() for p in Path(output).rglob('*') if p.is_dir()}
        require(actual==set(names),'SOURCE_DIRECTORY_SET')
    require(not verify_files(output,files),'ENGINE_SOURCE_CONFLICT')


def inspect_repository(root,expected_commit,git,runner):
    root=Path(root).resolve()
    require(checked(root,'.git').is_dir() and checked(root,'.git/HEAD').is_file()
        and checked(root,'.git/objects').is_dir() and checked(root,'.git/refs').is_dir()
        and not (root/'.git/commondir').exists(),'GIT_STRUCTURE')
    env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
    env['GIT_OPTIONAL_LOCKS']='0' # read-only identity queries must not refresh index bytes
    prefix=[git,'--git-dir='+str(root/'.git'),'--work-tree='+str(root),'-C',root]
    gdir=runner.run('engine_gitdir',[*prefix,'rev-parse','--absolute-git-dir'],env=env).decode('utf-8').strip()
    top=runner.run('engine_toplevel',[*prefix,'rev-parse','--show-toplevel'],env=env).decode('utf-8').strip()
    require(Path(gdir).resolve()==root/'.git' and Path(top).resolve()==root,'ENGINE_REPOSITORY_SCOPE')
    head=runner.run('engine_head',[*prefix,'rev-parse','HEAD'],env=env).decode('ascii').strip()
    require(head==expected_commit,'ENGINE_COMMIT')
    require(not runner.run('engine_clean',[*prefix,'status','--porcelain'],env=env).strip(),'ENGINE_DIRTY')
    return dict(git_directory=str(Path(gdir).resolve()),work_tree=str(Path(top).resolve()),commit=head,dirty=False)


def verify_files(root,expected):
    require(isinstance(expected,list) and expected,'EMPTY_FILE_SET')
    seen=set();issues=[]
    for r in expected:
        name=r['path'];p=checked(root,name)
        require(name.casefold() not in seen,'DUPLICATE');seen.add(name.casefold())
        if not p.is_file():issues.append(dict(path=name,reason='FILE_MISSING'));continue
        size=p.stat().st_size;actual=digest(p)
        if size!=r['size_bytes'] or actual!=r['sha256']:
            issues.append(dict(path=name,reason='CONTENT_CONFLICT',expected_size_bytes=r['size_bytes'],
                actual_size_bytes=size,expected_sha256=r['sha256'],actual_sha256=actual))
    return issues


def resolve_assets(package,cfg):
    package=Path(package).resolve()
    if 'reuse_dependency_root' not in cfg:
        require('reuse_manifest_sha256' not in cfg,'REUSED_ROOT_MISSING');return package
    raw_root=Path(cfg['reuse_dependency_root']).absolute()
    checked(raw_root,'package_manifest.json') # reject redirected/reparse roots before resolving
    root=raw_root.resolve()
    require(digest(root/'package_manifest.json')==cfg['reuse_manifest_sha256'],'REUSED_MANIFEST')
    expected=read(root/'package_manifest.json')['files']
    require(not verify_files(root,expected),'REUSED_ASSET_CONTENT')
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    require(actual=={r['path'] for r in expected}|{'package_manifest.json'},'REUSED_ASSET_COVERAGE')
    return root


def verify_hf(root,expected):
    issues=verify_files(root,expected);require(not issues,'HF_CONTENT_CONFLICT:'+json.dumps(issues))
    config=read(checked(root,'config.json'))
    require(config.get('model_type')=='qwen2' and config.get('architectures') in (None,['Qwen2ForCausalLM']),'HF_ARCHITECTURE')
    return expected


def bound_hf_reference(package,expected_sha):
    package=Path(package);source=package/'model_sha256.csv';ref=read(package/'hf_reference.json')
    require(digest(source)==expected_sha==ref.get('source_manifest_sha256'),'HF_MANIFEST_BINDING')
    rows=list(csv.DictReader(io.StringIO(source.read_text(encoding='utf-8-sig'),newline='')))
    facts=[dict(path=r['RelativePath'].replace('\\','/'),size_bytes=int(r['Bytes']),sha256=r['SHA256'].lower()) for r in rows]
    require(facts and facts==ref['files'],'HF_REFERENCE_CONTENT')
    return facts


PROBE_SHIM='''# Stage1 CPU-only configuration; original saved and SHA256 bound.
function(cmake_cuda_architectures_native lang)
  message(STATUS "EXPOSEDPATH_STAGE1_CUDA_DEVICE_PROBE_DISABLED")
  set(CMAKE_${lang}_ARCHITECTURES_NATIVE "" PARENT_SCOPE)
endfunction()
'''


def disable_cuda_probe(module,expected_sha,original_copy):
    module=Path(module);require(digest(module)==expected_sha,'CMAKE_PROBE_SOURCE_CONFLICT')
    with Path(original_copy).open('xb') as stream:stream.write(module.read_bytes())
    module.write_bytes(PROBE_SHIM.encode('utf-8')) # private, new environment, not system CMake
    return dict(original_sha256=expected_sha,patched_sha256=digest(module),
        purpose='DISABLE_RUN_OF_CUDA_ABI_PROBE_ONLY',compile_and_link_checks_retained=True)


def inspect_gguf(path,*,reader_factory=None):
    if reader_factory is None:
        from gguf import GGUFReader
        reader_factory=lambda p:GGUFReader(p,mode='r')
    r=reader_factory(str(path));architecture=r.fields['general.architecture'].contents()
    require(architecture=='qwen2','GGUF_ARCHITECTURE')
    types=Counter();tensors=[];names=set()
    for t in r.tensors:
        typ=t.tensor_type.name;require(typ in ('F16','F32'),'GGUF_QUANTIZED_OR_UNKNOWN_TYPE')
        require(t.name not in names and int(t.n_bytes)>0,'GGUF_TENSOR_CONFLICT');names.add(t.name)
        types[typ]+=1
        tensors.append(dict(name=t.name,type=typ,shape=[int(x) for x in t.shape],
            size_bytes=int(t.n_bytes),data_offset=int(t.data_offset)))
    require(types['F16']>0,'GGUF_NO_F16')
    return dict(architecture=architecture,tensor_types=dict(types),tensors=tensors)


def command_plan(code,engine,root,hf,nvtx,cuda,*,tools=None,git_executable=None):
    code,engine,root,hf,nvtx,cuda=map(Path,(code,engine,root,hf,nvtx,cuda))
    prefix=['-S',str(code/'native/llama_cpp'),'-B',str(root/'build'),
        '-G','Visual Studio 17 2022','-A','x64','-T','version=14.38.33130']
    build=['--build',str(root/'build'),'--config','Release','--target','native-llama','--parallel','2','--','/nodeReuse:false']
    if tools is not None:
        from exposedpath import native_ninja
        prefix=native_ninja.configure_arguments(code/'native/llama_cpp',root/'build',tools)
        build=['--build',str(root/'build'),'--target','native-llama','--parallel','2','--verbose']
    return [dict(name='configure',arguments=[*prefix,
        *([] if git_executable is None else ['-DGIT_EXECUTABLE='+str(git_executable)]),
        '-DLLAMA_SOURCE_ROOT='+str(engine),'-DNATIVE_PATCHED_BACKEND='+str(root/'backend.cu'),
        '-DNVTX_INCLUDE_ROOT='+str(nvtx),'-DCUDAToolkit_ROOT='+str(cuda),
        '-DCMAKE_CUDA_ARCHITECTURES=89','-DFETCHCONTENT_FULLY_DISCONNECTED=ON',
        '-DGGML_CCACHE=OFF','-DGGML_CPU_KLEIDIAI=OFF','-DGGML_CUDA_CCCL_VERSION=',
        '-DGGML_OPENMP_FETCH=OFF','-DGGML_CUDA_NCCL=OFF',
        '-DLLAMA_BUILD_COMMON=OFF','-DLLAMA_BUILD_APP=OFF','-DLLAMA_BUILD_SERVER=OFF']),
        dict(name='build',arguments=build),
        dict(name='convert',arguments=[str(engine/'convert_hf_to_gguf.py'),str(hf),'--outfile',str(root/'model-f16.gguf'),'--outtype','f16']),
        dict(name='inspect',arguments=['inspect','--model',str(root/'model-f16.gguf'),'--engine',str(engine),'--output',str(root/'gguf_inspection.json')])]


class Runner:
    def __init__(self,root):self.root=Path(root);self.records=[]
    def run(self,name,argv,*,env=None,timeout=120,cwd=None):
        logs=self.root/'logs';logs.mkdir(exist_ok=True)
        start=time.monotonic();rec=dict(name=name,argv=[str(x) for x in argv],exit_code=None,
            timed_out=False,started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
        try:
            with (logs/(name+'.stdout.txt')).open('xb') as out,(logs/(name+'.stderr.txt')).open('xb') as err:
                p=subprocess.Popen(rec['argv'],stdout=out,stderr=err,env=env,cwd=cwd,shell=False)
                rec['pid']=p.pid
                try:
                    while True:
                        remaining=timeout-(time.monotonic()-start)
                        if remaining<=0:raise subprocess.TimeoutExpired(rec['argv'],timeout)
                        try:rec['exit_code']=p.wait(timeout=min(20,remaining));break
                        except subprocess.TimeoutExpired:
                            print(f'[progress] {name} pid={p.pid} elapsed={time.monotonic()-start:.1f}s',flush=True)
                except subprocess.TimeoutExpired:
                    rec['timed_out']=True;p.kill();rec['exit_code']=p.wait(timeout=10)
                    rec['descendant_exit_status']='UNKNOWN_STOP_AND_INSPECT_NO_RETRY'
                    raise RuntimeError('STAGE1_TIMEOUT_NO_RETRY:'+name)
            require(rec['exit_code']==0,'STEP_EXIT:'+name)
            return (logs/(name+'.stdout.txt')).read_bytes()
        except BaseException as error:rec['error']=str(error);raise
        finally:
            rec['elapsed_seconds']=time.monotonic()-start;self.records.append(rec)
            write(logs/(name+'.json'),rec)


def cpu_regression_plan(cfg,code,root,env,cmake,use_ninja):
    """Bind just this CPU entry's test/helper namespace, not all repository tests."""
    code=Path(code).resolve();root=Path(root)
    files=['tests/test_native_stage1.py']
    if use_ninja:files+=['tests/test_native_ninja.py','tests/test_native_tool_identity.py','tests/test_native_llama.py','tests/test_native_cpu_import.py']
    paths=[str(code/'tests'),str(code)]
    if env.get('PYTHONPATH'):paths.append(env['PYTHONPATH'])
    test_env=dict(env,EXPOSEDPATH_TEST_CMAKE=str(cmake),PYTHONPATH=os.pathsep.join(paths),
        CUDA_VISIBLE_DEVICES='-1',PYTHONDONTWRITEBYTECODE='1')
    modules=[Path(p).stem for p in files]
    if use_ninja:modules+=['test_gate8_identity','test_v141_canonical_raw']
    return dict(argv=[cfg['test_python'],'-X','utf8','-m','pytest','-q','-rs','-p','no:cacheprovider',
        *files,'--basetemp',str(root/'cpu-tests')],env=test_env,cwd=code,modules=modules)


def bind_cpu_regression_environment(plan,root,runner):
    # A fresh process with the SAME interpreter/cwd/env as pytest, not expected
    # values copied into an "observed" snapshot. No test or third-party import.
    probe='''import hashlib,importlib.util,json,os,shutil,sys
from pathlib import Path
modules={}
for name in json.loads(sys.argv[1]):
    spec=importlib.util.find_spec(name)
    origin=None if spec is None else spec.origin
    modules[name]=None if origin is None else dict(origin=str(Path(origin).resolve()),sha256=hashlib.sha256(Path(origin).read_bytes()).hexdigest())
namespace=importlib.util.find_spec('tests')
print(json.dumps(dict(executable=sys.executable,base_executable=sys._base_executable,python_version=sys.version,cwd=str(Path.cwd()),
    environment={k:os.environ.get(k) for k in ('PYTHONPATH','EXPOSEDPATH_TEST_CMAKE','CUDA_VISIBLE_DEVICES','PYTHONDONTWRITEBYTECODE')},
    modules=modules,tests_namespace_origin=None if namespace is None else namespace.origin,
    optional_native_audits=dict(gxx_path=shutil.which('g++'),
        backend_byte_input=Path('.local/diagnostics/llama_native_v0_1/ggml-cuda.original.cu').is_file(),
        sdk_header=Path('.local/diagnostics/llama_native_v0_1/sdk/llama.h').is_file(),
        json_header=Path('.local/diagnostics/llama_native_v0_1/vendor/nlohmann/json.hpp').is_file()))))
'''
    result=dict(status='BLOCKED',error=None)
    try:
        raw=runner.run('cpu_regression_environment',[plan['argv'][0],'-X','utf8','-c',probe,json.dumps(plan['modules'])],env=plan['env'],cwd=plan['cwd'])
        value=json.loads(raw);require(isinstance(value,dict),'CPU_TEST_ENVIRONMENT_STRUCTURE');result.update(value)
        require(Path(value['executable']).resolve()==Path(plan['argv'][0]).resolve() and
            Path(value['cwd']).resolve()==plan['cwd'],'CPU_TEST_PROCESS_IDENTITY')
        require(all(value['environment'][k]==plan['env'][k] for k in value['environment']),'CPU_TEST_ENVIRONMENT_CONFLICT')
        for name in plan['modules']:
            expected=checked(plan['cwd'],'tests/'+name+'.py');actual=value['modules'][name]
            require(actual is not None and Path(actual['origin'])==expected and actual['sha256']==digest(expected),'CPU_TEST_MODULE_ORIGIN:'+name)
        result['status']='CPU_TEST_ENVIRONMENT_BOUND_NOT_BUILD_QUALIFICATION'
        return result
    except BaseException as error:result['error']=str(error);raise
    finally:write(Path(root)/'cpu_regression_environment.json',result)


def execute(config,package,root,*,runner=None):
    """Root already created by PS with its transcript; no retries or resume."""
    cfg=read(config);package=Path(package);root=Path(root);code=Path(cfg['code_root'])
    require(cfg['schema_version'] in (VERSION,NINJA_VERSION) and cfg['model_process_budget']==cfg['profile_budget']==0,'ROLE_OR_BUDGET')
    use_ninja=cfg['schema_version']==NINJA_VERSION
    require(root.resolve().is_relative_to(Path(cfg['server_root']).resolve()/'diagnostics'),'OUTPUT_SCOPE')
    runner=runner or Runner(root)
    receipt=dict(schema_version=cfg['schema_version'],status='BLOCKED',error=None,execution_commit=cfg['execution_commit'],
        gpu_qualification='NOT_RUN',model_executed=False,cuda_initialization_program_invoked=False,collector_executed=False,
        measurement_validity='NOT_ASSESSED',dropped_records_status='UNKNOWN',automatic_retry=False)
    env=dict({k:v for k,v in os.environ.items() if not k.startswith('GIT_')},GIT_OPTIONAL_LOCKS='0',CUDA_VISIBLE_DEVICES='-1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
        HF_HOME=str(root/'hf-cache'),PYTHONNOUSERSITE='1',PYTHONUTF8='1',PIP_NO_INDEX='1',PIP_DISABLE_PIP_VERSION_CHECK='1',PYTHONDONTWRITEBYTECODE='1')
    tools=None;compile_checks=None
    try:
        issues=verify_files(package,read(package/'package_manifest.json')['files']);require(not issues,'PACKAGE_CONFLICT:'+json.dumps(issues))
        assets=resolve_assets(package,cfg)
        if assets!=package:write(root/'dependency_reuse.json',dict(root=str(assets),manifest_sha256=cfg['reuse_manifest_sha256'],status='BYTE_VALIDATED_NOT_EXECUTED'))
        head=runner.run('git_head',[cfg['git'],'-C',code,'rev-parse','HEAD']).decode('ascii').strip()
        dirty=runner.run('git_clean',[cfg['git'],'-C',code,'status','--porcelain']).strip()
        require(head==cfg['execution_commit'] and not dirty,'CHECKOUT_IDENTITY')
        sys.path.insert(0,str(code))
        if use_ninja:
            from exposedpath import native_ninja
            tools,_=native_ninja.bind_tools(cfg,package,root,runner)
        expected=bound_hf_reference(assets,cfg['hf_manifest_sha256']);verify_hf(cfg['model_root'],expected)
        write(root/'hf_input_check.json',dict(source_manifest_sha256=cfg['hf_manifest_sha256'],files=expected))
        engine=root/'engine'
        layout_path=package/'llama_source_layout.json'
        layout=read(layout_path) if layout_path.is_file() else None
        if layout is not None:
            if 'files_manifest_sha256' in layout:
                require(layout['files_manifest_sha256']==digest(assets/'llama_source_manifest.json'),'SOURCE_LAYOUT_FILE_BINDING')
            if 'engine_commit' in layout:require(layout['engine_commit']==cfg['engine_commit'],'SOURCE_LAYOUT_COMMIT')
        restore_source(assets/'llama_source.zip',engine,read(assets/'llama_source_manifest.json')['files'],layout)
        write(root/'engine_repository_identity.json',inspect_repository(engine,cfg['engine_commit'],cfg['git'],runner))
        nvtx=root/'nvtx';extract(assets/'nvtx_headers.zip',nvtx)
        runner.run('python_identity',[cfg['base_python'],'-I','-c',
            'import sys,json; assert sys.version_info[:2]==(3,11); print(json.dumps({"executable":sys.executable,"version":sys.version}))'])
        if use_ninja:
            py,cmake=native_ninja.reuse_cpu(tools,root,runner,env)
        else:
            runner.run('create_cpu_environment',[cfg['base_python'],'-I','-m','venv',root/'converter'],env=env)
            py=root/'converter/Scripts/python.exe'
            runner.run('offline_dependencies',[py,'-I','-m','pip','install','--no-index','--no-deps','--require-hashes',
                '--find-links',assets/'wheels','-r',assets/'requirements.lock'],env=env,timeout=600)
            runner.run('dependency_check',[py,'-I','-m','pip','check'],env=env)
            cmake=root/'converter/Lib/site-packages/cmake/data/bin/cmake.exe'
            module=root/'converter/Lib/site-packages/cmake/data/share/cmake-3.31/Modules/Internal/CMakeCUDAArchitecturesNative.cmake'
            write(root/'cmake_probe_patch.json',disable_cuda_probe(module,cfg['cmake_probe_sha256'],root/'CMakeCUDAArchitecturesNative.original.cmake'))
            cv=runner.run('cmake_version',[cmake,'--version']).decode('utf-8')
            require(cv.splitlines()[0]=='cmake version '+CMAKE_VERSION,'CMAKE_VERSION')
        from exposedpath import native_llama as native
        native.instrument_backend(engine/'ggml/src/ggml-cuda/ggml-cuda.cu',root/'backend.cu')
        env['PYTHONPATH']=str(engine/'gguf-py')
        runner.run('cpu_dependencies',[py,'-c',
            'import torch,transformers,numpy,json; assert torch.__version__=="2.11.0+cpu" and torch.version.cuda is None; '
            'assert transformers.__version__=="4.57.6" and numpy.__version__=="2.2.6"; '
            'print(json.dumps({"torch":torch.__version__,"cuda_build":torch.version.cuda,"transformers":transformers.__version__,"numpy":numpy.__version__}))'],env=env)
        # Target-related tests use existing pytest, not the conversion dependency
        # environment. Explicit CMake is the already patched private CPU tool.
        if 'test_python' in cfg:
            plan=cpu_regression_plan(cfg,code,root,env,cmake,use_ninja)
            bind_cpu_regression_environment(plan,root,runner)
            runner.run('cpu_regression',plan['argv'],env=plan['env'],cwd=plan['cwd'],timeout=300)
        build_env=env
        if use_ninja:
            build_env=native_ninja.build_environment(cfg,tools,env)
            compile_checks=native_ninja.run_prechecks(code,root,tools,runner,build_env)
        plan=command_plan(code,engine,root,cfg['model_root'],nvtx/'include',cfg['cuda_root'],tools=tools,git_executable=cfg['git'])
        for s in plan:
            print('[stage] '+s['name']+' START',flush=True)
            exe=cmake if s['name'] in ('configure','build') else py
            args=s['arguments'] if s['name']!='inspect' else [str(package/'native_stage1.py'),*s['arguments']]
            runner.run(s['name'],[exe,*args],env=build_env if s['name'] in ('configure','build') else env,timeout=5400 if s['name']=='build' else 1800)
            if use_ninja and s['name']=='build':
                write(root/'native_compile_link.json',native_ninja.validate_build(root/'build',tools,'cuda',root/'build/bin/native-llama.exe'))
            print('[stage] '+s['name']+' COMPLETE',flush=True)
        cache=read_cache(root/'build/CMakeCache.txt')
        require(cache.get('CMAKE_CUDA_ARCHITECTURES')=='89' and cache.get('GGML_CUDA_GRAPHS')=='OFF'
            and cache.get('GGML_NATIVE')=='OFF' and cache.get('FETCHCONTENT_FULLY_DISCONNECTED')=='ON','CMAKE_CACHE_CONFLICT')
        shutil.copyfile(root/'build/CMakeCache.txt',root/'CMakeCache.review.txt')
        binary=root/('build/bin/native-llama.exe' if use_ninja else 'build/bin/Release/native-llama.exe')
        require(binary.is_file(),'BINARY_MISSING')
        inspections=read(root/'gguf_inspection.json')
        build=dict(schema_version=native.BUILD_NINJA_VERSION if use_ninja else native.BUILD_VERSION,engine_commit=cfg['engine_commit'],execution_commit=head,dirty=False,
            binary=native._ref(binary),configuration=native.build_configuration('ninja' if use_ninja else 'vs2022'),
            backend_original_sha256=native.BACKEND_SHA256,backend_instrumented_sha256=digest(root/'backend.cu'),
            native_source_sha256=hashlib.sha256(json.dumps({p:digest(code/p) for p in cfg['native_source_paths']},sort_keys=True).encode()).hexdigest(),
            actual_cache=cache,toolchain=read(root/'toolchain.json'),cmake_probe_patch=read(root/'cmake_probe_patch.json'))
        if use_ninja:build['compile_link_prechecks']=compile_checks
        conversion=dict(schema_version=native.CONVERSION_VERSION,engine_commit=cfg['engine_commit'],
            hf_snapshot_manifest_sha256=cfg['hf_manifest_sha256'],converter_source_sha256=digest(engine/'convert_hf_to_gguf.py'),
            conversion_arguments=['--outtype','f16'],model=native._ref(root/'model-f16.gguf'),architecture=inspections['architecture'],
            tensor_types=inspections['tensor_types'],revision=None,actual_tensor_inspection_sha256=digest(root/'gguf_inspection.json'))
        native._validate_receipts(build,conversion)
        verify_hf(cfg['model_root'],expected)
        write(root/'build_receipt.json',build);write(root/'conversion_receipt.json',conversion)
        receipt.update(status='STAGE1_COMPLETE_NOT_QUALIFICATION',source_model_unchanged=True,
            build_receipt_sha256=digest(root/'build_receipt.json'),conversion_receipt_sha256=digest(root/'conversion_receipt.json'))
    except BaseException as error:receipt['error']=str(error);raise
    finally:
        receipt['steps']=runner.records;write(root/'receipt.json',receipt)


def deploy(config,package,root):
    cfg=read(config);package=Path(package);root=Path(root);runner=Runner(root)
    value=dict(status='BLOCKED',error=None,execution_commit=cfg['execution_commit'])
    try:
        code=Path(cfg['code_root']);git=cfg['git']
        head=runner.run('deploy_head',[git,'-C',code,'rev-parse','HEAD']).decode('ascii').strip()
        require(head==cfg['prerequisite'],'DEPLOY_PREREQUISITE')
        require(not runner.run('deploy_clean',[git,'-C',code,'status','--porcelain']).strip(),'DEPLOY_DIRTY')
        runner.run('bundle_verify',[git,'-C',code,'bundle','verify',package/'execution.bundle'])
        runner.run('bundle_fetch',[git,'-C',code,'fetch',package/'execution.bundle',cfg['bundle_ref']])
        fetched=runner.run('bundle_head',[git,'-C',code,'rev-parse','FETCH_HEAD']).decode('ascii').strip()
        require(fetched==cfg['execution_commit'],'BUNDLE_COMMIT')
        runner.run('checkout',[git,'-C',code,'checkout','--detach',cfg['execution_commit']])
        require(not runner.run('deployed_clean',[git,'-C',code,'status','--porcelain']).strip(),'DEPLOY_FINAL_DIRTY')
        value['status']='DEPLOYED_NOT_QUALIFICATION'
    except BaseException as error:value['error']=str(error);raise
    finally:value['steps']=runner.records;write(root/'deploy_receipt.json',value)


def read_cache(path):
    out={}
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        if not line or line.startswith(('#','//')) or ':' not in line or '=' not in line:continue
        key,rest=line.split(':',1);out[key]=rest.split('=',1)[1]
    return out


def pack_review(root,archive):
    root=Path(root).resolve();archive=Path(archive).resolve()
    require(not archive.exists() and not archive.is_relative_to(root),'RETURN_OVERWRITE_OR_SCOPE')
    # Explicit review products, NOT model, environment, source or build artifacts.
    files=sorted([p for p in root.glob('*.json') if p.is_file()]+[p for p in (root/'logs').glob('*') if p.is_file()])
    for name in ('transcript.txt','CMakeCUDAArchitecturesNative.original.cmake','CMakeCache.review.txt'):
        p=root/name
        if p.is_file():files.append(p)
    # New compile-only checks retain compiler/cache facts without shipping build
    # intermediates. Reference ZIPs remain separately immutable delivery inputs.
    for directory in ('cxx-precheck','cuda-precheck','build'):
        base=root/directory
        for p in [base/'CMakeCache.txt',base/'CMakeFiles/CMakeConfigureLog.yaml',
            *(base/'CMakeFiles/3.31.10'/('CMake'+lang+'Compiler.cmake') for lang in ('C','CXX','CUDA'))]:
            if p.is_file():files.append(p)
    refs=[dict(path=p.relative_to(root).as_posix(),size_bytes=p.stat().st_size,sha256=digest(p)) for p in files]
    require(refs,'RETURN_EMPTY')
    manifest_version=VERSION
    if (root/'receipt.json').is_file() and read(root/'receipt.json').get('schema_version')==NINJA_VERSION:
        manifest_version=NINJA_VERSION
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,allowZip64=True) as z:
        for p,r in zip(files,refs):z.write(p,r['path'])
        z.writestr('artifact_manifest.json',json.dumps(dict(schema_version=manifest_version,files=refs),sort_keys=True,indent=2)+'\n')
    require(not verify_files(root,refs),'RETURN_SOURCE_CHANGED')
    with zipfile.ZipFile(archive) as z:
        require(z.testzip() is None and len(z.namelist())==len(refs)+1,'RETURN_CRC_OR_COVERAGE')
        for r in refs:require(hashlib.sha256(z.read(r['path'])).hexdigest()==r['sha256'],'RETURN_CONTENT')
    return dict(path=str(archive),size_bytes=archive.stat().st_size,sha256=digest(archive),files=len(refs))


def main():
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='action',required=True)
    r=s.add_parser('run');r.add_argument('--config',required=True);r.add_argument('--package',required=True);r.add_argument('--root',required=True)
    r=s.add_parser('deploy');r.add_argument('--config',required=True);r.add_argument('--package',required=True);r.add_argument('--root',required=True)
    r=s.add_parser('inspect');r.add_argument('--model',required=True);r.add_argument('--engine',required=True);r.add_argument('--output',required=True)
    r=s.add_parser('pack');r.add_argument('--root',required=True);r.add_argument('--archive',required=True)
    r=s.add_parser('verify-package');r.add_argument('--package',required=True)
    a=p.parse_args()
    if a.action=='run':execute(a.config,a.package,a.root)
    elif a.action=='deploy':deploy(a.config,a.package,a.root)
    elif a.action=='inspect':
        sys.path.insert(0,str(Path(a.engine)/'gguf-py'));write(a.output,inspect_gguf(a.model))
    elif a.action=='pack':print(json.dumps(pack_review(a.root,a.archive)))
    else:
        manifest=read(Path(a.package)/'package_manifest.json');issues=verify_files(a.package,manifest['files'])
        actual={p.relative_to(a.package).as_posix() for p in Path(a.package).rglob('*') if p.is_file()}
        require(actual=={r['path'] for r in manifest['files']}|{'package_manifest.json'},'PACKAGE_COVERAGE')
        require(not issues,'PACKAGE_HASH_CONFLICT:'+json.dumps(issues))
        if (Path(a.package)/'config.json').is_file():resolve_assets(a.package,read(Path(a.package)/'config.json'))
    return 0


if __name__=='__main__':raise SystemExit(main())
