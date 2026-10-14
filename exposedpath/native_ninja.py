"""Explicit Ninja/MSVC/CUDA build adapter. Compile/link only, never run probes."""
import hashlib
import json
import os
from pathlib import Path
import re

from . import native_stage1 as stage

VERSION='exposedpath-native-stage1/0.2.0'
CHECK_VERSION='exposedpath-native-compile-link/0.1.0'
NINJA_VERSION='1.12.1'
SDK_VERSION='10.0.20348.0'
NINJA_SHA256='68865c3276d449d746cea5065fdec2baf755d7813e161ab04205b0907b2629b8'
TOOL_IDENTITY_VERSION='exposedpath-native-tool-identity/0.1.0'


def read_pe_version(path):
    """Read the Windows fixed version resource; never execute the tool."""
    import ctypes
    from ctypes import wintypes
    stage.require(os.name=='nt','PE_VERSION_WINDOWS_ONLY')
    dll=ctypes.WinDLL('version.dll',use_last_error=True,winmode=0x800) # System32 only
    size=dll.GetFileVersionInfoSizeW
    size.argtypes=[wintypes.LPCWSTR,ctypes.POINTER(wintypes.DWORD)];size.restype=wintypes.DWORD
    get=dll.GetFileVersionInfoW
    get.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,wintypes.LPVOID];get.restype=wintypes.BOOL
    query=dll.VerQueryValueW
    query.argtypes=[wintypes.LPCVOID,wintypes.LPCWSTR,ctypes.POINTER(wintypes.LPVOID),ctypes.POINTER(wintypes.UINT)]
    query.restype=wintypes.BOOL
    ignored=wintypes.DWORD();n=size(str(path),ctypes.byref(ignored))
    if not n:raise ctypes.WinError(ctypes.get_last_error())
    data=ctypes.create_string_buffer(n)
    if not get(str(path),0,n,data):raise ctypes.WinError(ctypes.get_last_error())
    pointer=wintypes.LPVOID();length=wintypes.UINT()
    if not query(data,'\\',ctypes.byref(pointer),ctypes.byref(length)):raise ctypes.WinError(ctypes.get_last_error())
    stage.require(pointer.value is not None and length.value==13*4,'PE_FIXED_RESOURCE_SIZE')
    raw=list(ctypes.cast(pointer,ctypes.POINTER(wintypes.DWORD*13)).contents)
    ms,ls=raw[2:4]
    return dict(file_version='.'.join(map(str,(ms>>16,ms&0xffff,ls>>16,ls&0xffff))),file_type=raw[9],fixed_info=raw)


def msvc_file_identity(name,path,expected,root,*,reader=None):
    """Versioned identity-only policy, separate from Runner's exit-zero gate."""
    path=Path(path);result=dict(schema_version=TOOL_IDENTITY_VERSION,tool=name,status='BLOCKED',error=None,
        query='GetFileVersionInfoW/VerQueryValueW',tool_invoked=False,exit_code=None,expected_file=expected)
    try:
        stage.require(name in ('link','lib') and path.name.lower()==name+'.exe','MSVC_IDENTITY_TOOL')
        result['file']=fact(path)
        stage.require(result['file']==expected and expected['exists'] and expected['size_bytes']>0,'MSVC_IDENTITY_FILE_CONFLICT')
        result['resource']=(reader or read_pe_version)(path)
        r=result['resource'];raw=r['fixed_info']
        stage.require(len(raw)==13 and raw[0]==0xFEEF04BD and raw[1]==0x10000,'MSVC_IDENTITY_RESOURCE')
        actual='.'.join(map(str,(raw[2]>>16,raw[2]&0xffff,raw[3]>>16,raw[3]&0xffff)))
        stage.require(actual==r['file_version']=='14.38.33135.0' and raw[9]==r['file_type']==1,'MSVC_IDENTITY_VERSION')
        stage.require(fact(path)==expected,'MSVC_IDENTITY_CHANGED_DURING_QUERY')
        result['status']='IDENTITY_ONLY_NOT_BUILD_CAPABILITY'
        return result
    except BaseException as error:result['error']=str(error);raise
    finally:stage.write(Path(root)/(name+'_file_identity.json'),result)


def validate_prior_roles(cfg,old,observation):
    source=cfg.get('reuse_cpu_commit')
    stage.require(isinstance(source,str) and re.fullmatch(r'[0-9a-f]{40}',source) is not None
        and old['execution_commit']==source and old['error']=='NATIVE_STAGE1_STEP_EXIT:configure'
        and observation['expected_checkout']==source,'NINJA_PRIOR_ROLE')


def reference_zip(path,expected_sha,output):
    import zipfile
    stage.require(stage.digest(path)==expected_sha,'NINJA_REFERENCE_ZIP_HASH')
    with zipfile.ZipFile(path) as z:
        manifest=json.loads(z.read('artifact_manifest.json'));names=z.namelist()
        rows=manifest['files']
        stage.require(len(names)==len({n.casefold() for n in names}) and
            set(names)=={r['path'] for r in rows}|{'artifact_manifest.json'},'NINJA_REFERENCE_COVERAGE')
        for r in rows:
            data=z.read(r['path'])
            stage.require(len(data)==r['size_bytes'] and hashlib.sha256(data).hexdigest()==r['sha256'],'NINJA_REFERENCE_CONTENT')
    stage.extract(path,output)
    return stage.read(Path(output)/'receipt.json')


def fact(path):
    p=Path(path);stage.checked(p.parent,p.name)
    return dict(path=str(p),exists=p.is_file(),**(dict(size_bytes=p.stat().st_size,sha256=stage.digest(p)) if p.is_file() else {}))


def bind_tools(cfg,package,root,runner):
    package,root=Path(package),Path(root)
    vc=Path(cfg['vs_root'])/'VC/Tools/MSVC/14.38.33130'
    sdk=Path(cfg['sdk_root']);cuda=Path(cfg['cuda_root'])
    prior=Path(cfg.get('reuse_cpu_root',root/'missing-prior'))
    paths=dict(cl=vc/'bin/Hostx64/x64/cl.exe',link=vc/'bin/Hostx64/x64/link.exe',
        lib=vc/'bin/Hostx64/x64/lib.exe',rc=sdk/'bin'/SDK_VERSION/'x64/rc.exe',
        mt=sdk/'bin'/SDK_VERSION/'x64/mt.exe',nvcc=cuda/'bin/nvcc.exe',ninja=package/'ninja.exe',
        cmake=prior/'converter/Lib/site-packages/cmake/data/bin/cmake.exe',
        python=prior/'converter/Scripts/python.exe',
        vcruntime_lib=vc/'lib/x64/vcruntime.lib',msvcrt_lib=vc/'lib/x64/msvcrt.lib',
        msvcprt_lib=vc/'lib/x64/msvcprt.lib',vector_h=vc/'include/vector',
        kernel32_lib=sdk/'Lib'/SDK_VERSION/'um/x64/kernel32.lib',ucrt_lib=sdk/'Lib'/SDK_VERSION/'ucrt/x64/ucrt.lib',
        windows_h=sdk/'Include'/SDK_VERSION/'um/Windows.h',stdio_h=sdk/'Include'/SDK_VERSION/'ucrt/stdio.h',
        cuda_header=cuda/'include/cuda_runtime.h',cudart_lib=cuda/'lib/x64/cudart.lib',
        cudart_static_lib=cuda/'lib/x64/cudart_static.lib',cuda_driver_lib=cuda/'lib/x64/cuda.lib',
        cublas_lib=cuda/'lib/x64/cublas.lib')
    values={k:fact(p) for k,p in paths.items()}
    issues=[dict(name=k,**v) for k,v in values.items() if not v['exists'] or v['size_bytes']==0]
    stage.write(root/'toolchain_prerequisites.json',dict(schema_version=CHECK_VERSION,files=values,issues=issues))
    stage.require(not issues,'NINJA_PREREQUISITE_FILES:'+json.dumps(issues))
    # All missing components are reported above BEFORE a compile or import.
    references=root/'references';references.mkdir()
    old=reference_zip(package/'prior_review.zip',cfg['prior_review_sha256'],references/'prior')
    observation=reference_zip(package/'vs_facts.zip',cfg['vs_facts_zip_sha256'],references/'vs')
    observed=stage.read(references/'vs/vs_facts.json');old_tool=stage.read(references/'prior/toolchain.json')
    validate_prior_roles(cfg,old,observation)
    for name in ('receipt.json','toolchain.json','cmake_probe_patch.json'):
        stage.require(stage.digest(prior/name)==stage.digest(references/'prior'/name),'NINJA_PRIOR_CHANGED:'+name)
    for key in ('cl','cmake'):
        stage.require(values[key]==observed['files'][key],'NINJA_OBSERVED_TOOL_CONFLICT:'+key)
    stage.require(values['nvcc']['sha256']==old_tool['nvcc_sha256'].lower() and
        values['ninja']['sha256']==NINJA_SHA256,'NINJA_FIXED_TOOL_BYTES')
    chosen=[r for r in observed['windows_sdks'] if r['version']==SDK_VERSION]
    stage.require(len(chosen)==1,'NINJA_SDK_OBSERVATION')
    for row in chosen[0]['files']:
        stage.require(fact(row['path'])==row,'NINJA_SDK_CHANGED')
    patch=stage.read(prior/'cmake_probe_patch.json')
    module=prior/'converter/Lib/site-packages/cmake/data/share/cmake-3.31/Modules/Internal/CMakeCUDAArchitecturesNative.cmake'
    stage.checked(module.parent,module.name)
    stage.require(stage.digest(module)==patch['patched_sha256']==hashlib.sha256(stage.PROBE_SHIM.encode()).hexdigest()
        and patch['original_sha256']==cfg['cmake_probe_sha256'],'NINJA_CUDA_PROBE_GUARD')
    stage.write(root/'cmake_probe_patch.json',dict(patch,reused_read_only=True,source=str(module)))
    tools={k:str(p) for k,p in paths.items() if k in ('cl','link','lib','rc','mt','nvcc','ninja','cmake','python')}
    env=build_environment(cfg,tools,os.environ)
    version=runner.run('ninja_version',[tools['ninja'],'--version'],env=env).decode('ascii').strip()
    stage.require(version==NINJA_VERSION,'NINJA_VERSION')
    stage.require(cfg.get('tool_identity_version')==TOOL_IDENTITY_VERSION,'NINJA_TOOL_IDENTITY_VERSION')
    query_ref=reference_zip(package/'query_review.zip',cfg['query_review_sha256'],references/'query')
    stage.require(query_ref['execution_commit']==cfg['query_reference_commit']
        and query_ref['error']=='NATIVE_STAGE1_STEP_EXIT:link_version'
        and not any(query_ref[k] for k in ('model_executed','cuda_initialization_program_invoked','collector_executed')),'NINJA_QUERY_REFERENCE_ROLE')
    query_files=stage.read(references/'query/toolchain_prerequisites.json')['files']
    identities={name:msvc_file_identity(name,tools[name],query_files[name],root) for name in ('link','lib')}
    stage.write(root/'toolchain.json',dict(schema_version=CHECK_VERSION,generator='Ninja',ninja_version=version,
        msvc_toolset='14.38.33130',sdk_version=SDK_VERSION,files=values,device_query_invoked=False,
        environment={k:env[k] for k in ('PATH','INCLUDE','LIB')},prior_reference_sha256=cfg['prior_review_sha256'],
        vs_facts_zip_sha256=cfg['vs_facts_zip_sha256'],tool_identity_version=TOOL_IDENTITY_VERSION,
        tool_identities=identities,query_reference_sha256=cfg['query_review_sha256'],reuse_cpu_commit=cfg['reuse_cpu_commit']))
    return tools,env


def build_environment(cfg,tools,parent):
    env={k:v for k,v in parent.items() if k.upper() not in
        ('PATH','INCLUDE','LIB','LIBPATH','CL','_CL_','LINK','CFLAGS','CXXFLAGS','CUDAFLAGS','CUDACXX',
         'CUDAHOSTCXX','CMAKE_GENERATOR','CMAKE_GENERATOR_INSTANCE','CMAKE_GENERATOR_PLATFORM','CMAKE_GENERATOR_TOOLSET')}
    vc=Path(cfg['vs_root'])/'VC/Tools/MSVC/14.38.33130';sdk=Path(cfg['sdk_root'])
    win=Path(parent.get('SystemRoot','C:/Windows'))
    env.update(PATH=';'.join(dict.fromkeys([str(Path(tools[k]).parent) for k in ('cl','nvcc','ninja','rc','cmake')]
        +[str(win/'System32'),str(win)])),
        INCLUDE=';'.join(map(str,[vc/'include',*[sdk/'Include'/SDK_VERSION/n for n in ('ucrt','shared','um','winrt')]])),
        LIB=';'.join(map(str,[vc/'lib/x64',sdk/'Lib'/SDK_VERSION/'ucrt/x64',sdk/'Lib'/SDK_VERSION/'um/x64'])),
        VCToolsInstallDir=str(vc)+os.sep,WindowsSdkDir=str(sdk)+os.sep,WindowsSDKVersion=SDK_VERSION+'\\',
        CUDA_PATH=str(cfg['cuda_root']),CUDA_VISIBLE_DEVICES='-1',CUDA_DEVICE_ORDER='PCI_BUS_ID',
        PYTHONDONTWRITEBYTECODE='1')
    return env


def configure_arguments(source,build,tools):
    mapping={'CMAKE_MAKE_PROGRAM':'ninja','CMAKE_C_COMPILER':'cl','CMAKE_CXX_COMPILER':'cl',
        'CMAKE_CUDA_COMPILER':'nvcc','CMAKE_CUDA_HOST_COMPILER':'cl','CMAKE_LINKER':'link',
        'CMAKE_AR':'lib','CMAKE_RC_COMPILER':'rc','CMAKE_MT':'mt'}
    return ['-S',str(source),'-B',str(build),'-G','Ninja','-DCMAKE_BUILD_TYPE=Release',
        '-DCMAKE_SYSTEM_VERSION='+SDK_VERSION,'-DCMAKE_CUDA_ARCHITECTURES=89',
        *('-D'+key+'='+tools[name] for key,name in mapping.items())]


def compiler_field(path,key):
    text=Path(path).read_text(encoding='utf-8')
    m=re.search(r'^set\('+re.escape(key)+r' "([^"]*)"\)',text,re.M)
    stage.require(m is not None,'NINJA_COMPILER_FIELD_MISSING:'+key)
    return m.group(1)


def validate_build(build,tools,kind,binary):
    build=Path(build);cache=stage.read_cache(build/'CMakeCache.txt')
    stage.require(cache.get('CMAKE_GENERATOR')=='Ninja' and cache.get('CMAKE_BUILD_TYPE')=='Release'
        and cache.get('CMAKE_SYSTEM_VERSION')==SDK_VERSION,'NINJA_CACHE_CONFIGURATION')
    mapping={'CMAKE_MAKE_PROGRAM':'ninja','CMAKE_CXX_COMPILER':'cl','CMAKE_LINKER':'link',
        'CMAKE_AR':'lib','CMAKE_RC_COMPILER':'rc','CMAKE_MT':'mt'}
    if kind=='cxx':mapping['CMAKE_C_COMPILER']='cl'
    else:
        mapping.update(CMAKE_CUDA_COMPILER='nvcc',CMAKE_CUDA_HOST_COMPILER='cl')
        stage.require(cache.get('CMAKE_CUDA_ARCHITECTURES')=='89','NINJA_ACTUAL_CUDA_ARCHITECTURES')
    for key,name in mapping.items():
        value=cache.get(key,'')
        stage.require(Path(value).is_absolute() and Path(value).resolve()==Path(tools[name]).resolve(),'NINJA_CACHE_TOOL_CONFLICT:'+key)
    versions={}
    for lang in (('C','CXX') if kind=='cxx' else ('CXX','CUDA')):
        path=build/'CMakeFiles/3.31.10'/('CMake'+lang+'Compiler.cmake')
        version=compiler_field(path,'CMAKE_'+lang+'_COMPILER_VERSION')
        stage.require(version==('12.4.131' if lang=='CUDA' else '19.38.33135'),'NINJA_ACTUAL_COMPILER_VERSION:'+lang)
        actual=compiler_field(path,'CMAKE_'+lang+'_COMPILER')
        stage.require(Path(actual).resolve()==Path(tools['nvcc' if lang=='CUDA' else 'cl']).resolve(),'NINJA_ACTUAL_COMPILER_PATH:'+lang)
        versions[lang]=version
    stage.require(Path(binary).is_file() and Path(binary).stat().st_size>0,'NINJA_LINK_OUTPUT_MISSING')
    return dict(schema_version=CHECK_VERSION,status='COMPILE_LINK_PASS_NOT_EXECUTED',program_invoked=False,
        generator='Ninja',compiler_versions=versions,cache=cache,binary=fact(binary),sdk_version=SDK_VERSION)


def run_prechecks(code,root,tools,runner,env):
    code,root=Path(code),Path(root);refs={}
    for kind,source,target in [('cxx','toolchain_precheck','native-toolchain-check'),
        ('cuda','cuda_toolchain_precheck','native-cuda-link-check')]:
        build=root/(kind+'-precheck')
        stage.require(not build.exists(),'NINJA_PRECHECK_NO_RESUME')
        print('[stage] '+kind+'_compile_link START; executable will NOT be run',flush=True)
        runner.run(kind+'_configure',[tools['cmake'],*configure_arguments(code/'native'/source,build,tools)],env=env,timeout=300)
        runner.run(kind+'_compile_link',[tools['cmake'],'--build',build,'--target',target,'--parallel','2','--verbose'],env=env,timeout=300)
        result=validate_build(build,tools,kind,build/(target+'.exe'))
        path=root/(kind+'_precheck.json');stage.write(path,result)
        refs[kind]=dict(path=str(path.resolve()),sha256=stage.digest(path),size_bytes=path.stat().st_size)
        print('[stage] '+kind+'_compile_link PASS (not executed)',flush=True)
    return refs


def reuse_cpu(tools,root,runner,env):
    py=Path(tools['python']);cmake=Path(tools['cmake'])
    runner.run('dependency_check',[py,'-I','-B','-m','pip','check'],env=env)
    cv=runner.run('cmake_version',[cmake,'--version'],env=env).decode('utf-8')
    stage.require(cv.splitlines()[0]=='cmake version '+stage.CMAKE_VERSION,'CMAKE_VERSION')
    return py,cmake
