"""Build/CPU checks and explicit future micro only. No PyTorch or A/B imports."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import shutil
import stat
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def require(ok,reason):
    if not ok:raise ValueError('MEMSET_MICRO_'+reason)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def write(path,value):
    with Path(path).open('x',encoding='utf8') as f:json.dump(value,f,indent=2)


def compile_environment(config):
    vc=Path(config['vc_root']);sdk=Path(config['sdk_root']);version=config['sdk_version']
    env=os.environ.copy()
    for key in ('CL','_CL_','LINK','_LINK_','CUDAHOSTCXX','CUDACXX'):env.pop(key,None)
    env.update(INCLUDE=os.pathsep.join(map(str,[vc/'include',*[sdk/'Include'/version/v for v in ('ucrt','shared','um','winrt')]])),
        LIB=os.pathsep.join(map(str,[vc/'lib/x64',sdk/'Lib'/version/'ucrt/x64',sdk/'Lib'/version/'um/x64'])),
        PATH=os.pathsep.join(map(str,[vc/'bin/Hostx64/x64',sdk/'bin'/version/'x64',Path(os.environ['SystemRoot'])/'System32'])),
        CUDA_VISIBLE_DEVICES='-1')
    return env


def command(argv,cwd,log,*,env=None,timeout=120):
    """Preserve bytes and original code; timeout is never silently success."""
    log=Path(log);log.parent.mkdir(parents=True,exist_ok=True)
    record=dict(argv=list(map(str,argv)),status='STARTING',exit_code=None,timed_out=False)
    print('[stage] '+log.name+' START',flush=True)
    try:
        with log.with_suffix('.stdout').open('xb') as stdout,log.with_suffix('.stderr').open('xb') as stderr:
            try:process=subprocess.Popen(record['argv'],cwd=cwd,env=env,stdout=stdout,stderr=stderr)
            except OSError as error:
                record.update(status='SPAWN_FAILED',error_type=type(error).__name__,error=str(error));raise
            record['pid']=process.pid
            try:record['exit_code']=process.wait(timeout=timeout);record['status']='EXITED'
            except subprocess.TimeoutExpired:
                process.kill();process.wait();record.update(status='BLOCKED',timed_out=True,
                    descendant_exit_status='UNKNOWN_STOP_AND_INSPECT_NO_RETRY');raise
    finally:
        # A receipt-writing failure may fail a successful step, never mask an
        # already active spawn/timeout exception (same bounded I/O discipline).
        original=sys.exc_info()[0]
        try:write(log.with_suffix('.process.json'),record)
        except OSError:
            if original is None:raise
    require(record['exit_code']==0,'COMMAND_EXIT:'+log.name+':'+str(record['exit_code']))
    print('[stage] '+log.name+' COMPLETE',flush=True)
    return record


def pe_imports(path,dumpbin,env,out):
    command([dumpbin,'/imports',str(path)],out,out/(Path(path).stem+'_imports'),env=env)
    import re
    data=(out/(Path(path).stem+'_imports.stdout')).read_bytes().decode('utf8',errors='replace')
    names=re.findall(r'^\s+([\w.\-]+\.dll)\s*$',data,re.MULTILINE|re.IGNORECASE)
    require(names and not any(any(v in n.lower() for v in ('cudart','nvcuda','cupti')) for n in names),'CUDA_IMPORT_FORBIDDEN')
    return sorted(set(names))


def build_native(config,output):
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    vc=Path(config['vc_root']);tools={n:str(vc/'bin/Hostx64/x64'/(n+'.exe')) for n in ('cl','lib','dumpbin','link')}
    env=compile_environment(config);det=Path(config['detours'])/'src'
    includes=[config['cuda_include'],config['crt_include'],str(det),config['nvtx_include']]
    require(all(Path(p).is_dir() for p in includes),'INCLUDE_MISSING')
    names=['detours','modules','disasm','image','creatwth','disolx86','disolx64','disolia64','disolarm','disolarm64']
    vendor=out/'vendor';vendor.mkdir();objects=[]
    for n in names:
        obj=vendor/(n+'.obj');objects.append(str(obj))
        command([tools['cl'],'/nologo','/c','/MT','/Od','/EHsc','/DWIN32_LEAN_AND_MEAN',
            '/D_WIN32_WINNT=0x0601','/I'+str(det),str(det/(n+'.cpp')),'/Fo:'+str(obj)],out,out/('detours_'+n),env=env)
    lib=out/'detours.lib';command([tools['lib'],'/nologo','/OUT:'+str(lib),*objects],out,out/'detours_lib',env=env)
    source=ROOT/'scripts/native_memset_probe'
    base=[tools['cl'],'/nologo','/EHsc','/std:c++17','/MT','/Od','/W4','/WX','/utf-8',*[ '/I'+p for p in includes]]
    outputs={}
    for key,src,dll,cpu in [('host_target','host_target.cpp',True,True),('host_recorder','recorder.cpp',True,True),
        ('host_test','host_test.cpp',False,True),('recorder','recorder.cpp',True,False),('micro','micro.cpp',False,False)]:
        target=out/(key+('.dll' if dll else '.exe'));outputs[key]=str(target)
        args=[*base,*(['/DEP_CPU_TEST'] if cpu else []),*(['/LD'] if dll else []),str(source/src),
            '/Fo:'+str(out/(key+'.obj')),'/Fe:'+str(target),'/link',str(lib)]
        command(args,out,out/('build_'+key),env=env)
    imports={k:pe_imports(outputs[k],tools['dumpbin'],env,out) for k in ('micro','recorder','host_test','host_recorder','host_target')}
    outputs.update(micro_invoked=False,cuda_header_version=12040,micro_imports=imports['micro'],
        imports=imports,tools={k:dict(path=p,sha256=sha(p)) for k,p in tools.items()},
        binary_files=[dict(path=Path(outputs[k]).name,bytes=Path(outputs[k]).stat().st_size,sha256=sha(outputs[k]))
                      for k in ('micro','recorder','host_test','host_recorder','host_target')])
    write(out/'build.json',outputs)
    return outputs


def safe(root,relative):
    root=Path(os.path.abspath(root));p=Path(relative)
    require(not p.is_absolute() and relative and '\\' not in relative and ':' not in relative
        and '..' not in p.parts,'PATH')
    target=root/p
    require(target.resolve().is_relative_to(root),'PATH')
    for v in (target,*target.parents):
        if v.exists():require(not v.is_symlink() and not getattr(v.lstat(),'st_file_attributes',0)&0x400,'REPARSE')
        if v==root:break
    return target


def verify_rows(root,rows):
    require(bool(rows),'EMPTY_INDEX');seen=set()
    for r in rows:
        p=safe(root,r['path']);key=str(p).casefold()
        require(key not in seen,'DUPLICATE_PATH');seen.add(key)
        require(p.is_file(),'FILE_MISSING:'+r['path'])
        actual=dict(bytes=p.stat().st_size,sha256=sha(p))
        require(actual['bytes']==r['bytes'] and actual['sha256']==r['sha256'],
            'FILE_HASH:'+json.dumps(dict(path=r['path'],expected=r,actual=actual)))


def verify_package(package):
    package=Path(package)
    rows=json.loads((package/'package_manifest.json').read_text(encoding='utf8'))['files']
    verify_rows(package,rows)
    require({p.relative_to(package).as_posix() for p in package.rglob('*') if p.is_file()}
        =={r['path'] for r in rows}|{'package_manifest.json'},'PACKAGE_COVERAGE')
    return sha(package/'package_manifest.json')


def extract(archive,output,*,prefix=''):
    out=Path(output);out.mkdir(exist_ok=False)
    with zipfile.ZipFile(archive) as z:
        names=z.namelist();require(len(names)==len(set(n.casefold() for n in names)),'ZIP_DUPLICATE')
        for r in z.infolist():
            require(not stat.S_ISLNK(r.external_attr>>16),'ZIP_SYMLINK')
            original=r.filename.rstrip('/')
            require(original and not original.startswith('/') and '\\' not in original
                and ':' not in original and '..' not in original.split('/'),'ZIP_PATH')
            if prefix and not r.filename.startswith(prefix):continue
            relative=r.filename[len(prefix):].rstrip('/')
            if not relative:continue
            p=safe(out,relative)
            if r.is_dir():p.mkdir(parents=True,exist_ok=True)
            else:
                p.parent.mkdir(parents=True,exist_ok=True)
                with z.open(r) as f,p.open('xb') as target:shutil.copyfileobj(f,target)


def pack(root,archive):
    root,archive=Path(root),Path(archive)
    require(not archive.exists(),'ARCHIVE_EXISTS')
    require(not archive.resolve().is_relative_to(root.resolve()),'ARCHIVE_INSIDE_SOURCE')
    for p in root.rglob('*.process.json'):
        v=json.loads(p.read_text(encoding='utf8'))
        require(v.get('descendant_exit_status')!='UNKNOWN_STOP_AND_INSPECT_NO_RETRY','UNKNOWN_WRITER')
        require(v.get('status') not in ('RUNNING','STARTING'),'ACTIVE_WRITER')
    rows=[]
    for p in sorted(root.rglob('*')):
        require(not p.is_symlink() and not getattr(p.lstat(),'st_file_attributes',0)&0x400,'REPARSE')
        if p.is_file():rows.append(dict(path=p.relative_to(root).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
    require(not (root/'artifact_manifest.json').exists(),'INDEX_EXISTS')
    write(root/'artifact_manifest.json',dict(schema_version='memset-micro-artifacts/0.1.0',files=rows))
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for r in rows:z.write(safe(root,r['path']),r['path'])
        z.write(root/'artifact_manifest.json','artifact_manifest.json')
    verify_rows(root,rows)
    with zipfile.ZipFile(archive) as z:
        require(z.testzip() is None,'ZIP_CRC')
        for r in rows:require(hashlib.sha256(z.read(r['path'])).hexdigest()==r['sha256'],'ZIP_BYTES')
    return dict(path=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),
        manifest_sha256=sha(root/'artifact_manifest.json'))


def check_reviewed_static(root,reviewed,target,index_sha):
    import re
    root=Path(root);p=root/'receipt.json'
    require(isinstance(reviewed,str) and re.fullmatch('[0-9a-fA-F]{64}',reviewed) and p.is_file()
        and sha(p)==reviewed.lower(),'REVIEWED_STATIC_HASH')
    v=json.loads(p.read_text(encoding='utf8'))
    require(v.get('status')=='STATIC_READY_FOR_REVIEW' and v.get('phase')=='A'
        and v.get('execution_commit')==target and v.get('package_index_sha256')==index_sha,'STATIC_BINDING')
    rows=json.loads((root/'artifact_manifest.json').read_text(encoding='utf8'))['files']
    verify_rows(root,rows)
    require(sha(root/'build/build.json')==v['build_sha256'],'STATIC_BUILD_CHANGED')
    require(sha(root/'runtime_file.json')==v['runtime_file_sha256'],'STATIC_RUNTIME_CHANGED')
    verify_rows(root/'build',json.loads((root/'build/build.json').read_text(encoding='utf8'))['binary_files'])
    return v


def git_text(git,code,*args):
    done=subprocess.run([git,'-C',str(code),*args],capture_output=True)
    require(done.returncode==0,'GIT_QUERY:'+done.stderr.decode('utf8',errors='replace'))
    return done.stdout.decode('utf8').strip()


def tree(cfg,target):
    require(git_text(cfg['git'],cfg['code_root'],'rev-parse','HEAD')==target,'COMMIT')
    require(not git_text(cfg['git'],cfg['code_root'],'status','--porcelain'),'DIRTY_CHECKOUT')


def deploy(cfg,package,out):
    tree(cfg,cfg['prerequisite'])
    bundle=Path(package)/'execution.bundle'
    command([cfg['git'],'bundle','verify',str(bundle)],cfg['code_root'],out/'bundle_verify')
    command([cfg['git'],'-C',cfg['code_root'],'fetch',str(bundle),'HEAD:refs/remotes/memset-micro/execution'],cfg['code_root'],out/'fetch')
    require(git_text(cfg['git'],cfg['code_root'],'rev-parse','refs/remotes/memset-micro/execution')==cfg['execution_commit'],'BUNDLE_TARGET')
    command([cfg['git'],'-C',cfg['code_root'],'-c','core.autocrlf=false','checkout','--detach',cfg['execution_commit']],cfg['code_root'],out/'checkout')


def resources(out,archive):
    # No history traversal/ACL query. Fresh local free bytes on each distinct
    # participating volume; long-term YLQ remains UNKNOWN, never zero.
    from scripts.coe_startup_storage import volume_identity,safe_directory,write_probe
    values={};temporary=[Path(os.environ['TEMP']),Path(os.environ['TMP'])]
    if os.environ.get('TMPDIR'):temporary.append(Path(os.environ['TMPDIR']))
    for path in (Path(out),Path(archive).parent,*temporary):
        path=safe_directory(path);write_probe(path);identity=volume_identity(path)
        if identity not in values:
            usage=shutil.disk_usage(path);require(type(usage.free) is int and usage.free>=268435456,'FREE_SPACE')
            values[identity]=dict(path=str(path),free_bytes=usage.free,required_bytes=268435456)
    return dict(volumes=values,historical_ylq_total_bytes=None,long_term_status='UNKNOWN_NOT_PROVEN',
        long_term_target_exclusive_bytes=50000000000,automatic_cleanup=False)


def file_fact(path):
    path=Path(path);require(path.is_file(),'FILE_MISSING:'+str(path))
    return dict(path=str(path),bytes=path.stat().st_size,sha256=sha(path))


def runtime_fact(path):
    # File resources only: version.dll reads PE bytes, never LoadLibrary(CUDART).
    import ctypes
    from ctypes import wintypes as w
    value=file_fact(path);dll=ctypes.WinDLL('version.dll',use_last_error=True,winmode=0x800)
    size=dll.GetFileVersionInfoSizeW;size.argtypes=[w.LPCWSTR,ctypes.POINTER(w.DWORD)];size.restype=w.DWORD
    get=dll.GetFileVersionInfoW;get.argtypes=[w.LPCWSTR,w.DWORD,w.DWORD,w.LPVOID];get.restype=w.BOOL
    query=dll.VerQueryValueW;query.argtypes=[w.LPCVOID,w.LPCWSTR,ctypes.POINTER(w.LPVOID),ctypes.POINTER(w.UINT)];query.restype=w.BOOL
    ignored=w.DWORD();n=size(str(path),ctypes.byref(ignored));require(n>0,'RUNTIME_PE_VERSION')
    data=ctypes.create_string_buffer(n);require(get(str(path),0,n,data),'RUNTIME_PE_VERSION')
    pointer=w.LPVOID();length=w.UINT()
    require(query(data,'\\',ctypes.byref(pointer),ctypes.byref(length)) and length.value==52,'RUNTIME_PE_VERSION')
    raw=list(ctypes.cast(pointer,ctypes.POINTER(w.DWORD*13)).contents)
    require(raw[0]==0xFEEF04BD,'RUNTIME_PE_VERSION')
    value['file_version']='.'.join(map(str,(raw[2]>>16,raw[2]&65535,raw[3]>>16,raw[3]&65535)))
    # Actual official CUDA12.4.127 Windows CUDART uses this PE resource tuple;
    # it is not the toolkit's semantic version. Runtime API12040 is queried in B.
    require(value['file_version']=='6.14.11.12040','RUNTIME_FILE_VERSION')
    return value


def stage(package,phase,reviewed=None):
    global ROOT
    package=Path(package).resolve();index_sha=verify_package(package)
    cfg=json.loads((package/'delivery.json').read_text(encoding='utf8'))
    import re
    require(cfg['schema_version']=='memset-micro-delivery/0.1.0' and phase in ('A','B')
        and cfg['micro_process_budget']==cfg['profile_budget']==1 and cfg['model_process_budget']==0
        and cfg['execution_commit']==cfg['analysis_commit']
        and re.fullmatch('[0-9a-f]{40}',cfg['execution_commit']) is not None,'DELIVERY')
    ROOT=Path(cfg['code_root']).resolve()
    if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
    root=Path(cfg['server_root']);short=cfg['execution_commit'][:12]
    out=safe(root,'diagnostics/memset_micro_'+short+('_static' if phase=='A' else '_once'))
    archive=safe(root,'transfer/memset_micro_'+short+('_static.zip' if phase=='A' else '_once.zip'))
    require(not out.exists() and not archive.exists(),'NO_OVERWRITE_RESUME_RETRY')
    old=root/'diagnostics'/('memset_micro_'+short+'_static')
    static=check_reviewed_static(old,reviewed,cfg['execution_commit'],index_sha) if phase=='B' else None
    out.mkdir(parents=True,exist_ok=False);shutil.copyfile(package/'delivery.json',out/'delivery.json')
    shutil.copyfile(package/'package_manifest.json',out/'delivery_package_manifest.json')
    for name in ('dependency_sources.json','prerequisite_reference.json','nsys_schema_reference.json'):
        if (package/name).is_file():shutil.copyfile(package/name,out/name)
    status='BLOCKED';error=None;built=None;build_sha=None
    try:
        require(list(sys.version_info[:3])==cfg['python_version'],'PYTHON_VERSION')
        if phase=='A':deploy(cfg,package,out)
        tree(cfg,cfg['execution_commit']);verify_rows(ROOT,cfg['sources'])
        write(out/'source_bytes.json',[dict(expected=r,actual=file_fact(safe(ROOT,r['path']))) for r in cfg['sources']])
        write(out/'resources.json',resources(out,archive))
        for name,ref in cfg['toolchain_files'].items():
            actual=file_fact(ref['path']);require(actual==ref,'TOOLCHAIN:'+name)
        runtime=runtime_fact(cfg['runtime_path'])
        if phase=='A':
            write(out/'runtime_file.json',runtime) # observed bytes; MUST be independently reviewed before B
            build_cfg=dict(cfg['build'])
            dumpbin=Path(build_cfg['vc_root'])/'bin/Hostx64/x64/dumpbin.exe'
            write(out/'dumpbin_file.json',file_fact(dumpbin))
            command([str(dumpbin),'/exports',cfg['runtime_path']],out,out/'runtime_exports',env=compile_environment(build_cfg))
            exports=(out/'runtime_exports.stdout').read_bytes().decode('ascii',errors='replace')
            for n in ('cudaMemsetAsync','cudaRuntimeGetVersion','cudaGetDeviceCount','cudaSetDevice',
                'cudaGetDeviceProperties_v2','cudaDeviceGetPCIBusId','cudaMalloc','cudaFree','cudaMemcpy',
                'cudaDeviceSynchronize','cudaStreamSynchronize'):
                require(re.search(r'\b'+n+r'\b',exports) is not None,'RUNTIME_EXPORT:'+n)
            extract(package/'detours.zip',out/'detours',prefix=cfg['detours_directory']+'/')
            extract(package/'nvtx.zip',out/'nvtx',prefix=cfg['nvtx_directory']+'/c/include/')
            extract(package/'sdk.zip',out/'sdk')
            build_cfg.update(detours=str(out/'detours'),
                nvtx_include=str(out/'nvtx'),
                cuda_include=str(out/'sdk/include'),crt_include=str(out/'sdk/include'))
            built=build_native(build_cfg,out/'build');build_sha=sha(out/'build/build.json')
            write(out/'build_configuration.json',build_cfg)
            cpu_env=os.environ.copy()
            for name in ('PYTEST_ADDOPTS','PYTEST_PLUGINS'):cpu_env.pop(name,None)
            cpu_env.update(MEMSET_MICRO_CPU_CONFIG=str(out/'build_configuration.json'),
                MEMSET_MICRO_BUILT_JSON=str(out/'build/build.json'),MEMSET_MICRO_RUNTIME_FILE=cfg['runtime_path'],
                CUDA_VISIBLE_DEVICES='-1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
            command([cfg['python'],'-X','utf8','-m','pytest','-q','-ra','-p','no:cacheprovider',
                'tests/test_memset_same_capture.py','tests/test_memset_micro_delivery.py','tests/test_memset_micro_native.py',
                '--basetemp',str(root/'diagnostics'/('memset_micro_'+short+'_cpu_tmp')),
                '--junitxml',str(out/'cpu.xml')],ROOT,out/'cpu_file_chain',env=cpu_env)
            import xml.etree.ElementTree as ET
            suite=ET.parse(out/'cpu.xml').getroot().find('testsuite')
            require(int(suite.attrib['tests'])==54 and all(suite.attrib[k]=='0' for k in ('failures','errors','skipped')),'CPU_RESULT')
            verify_rows(ROOT,cfg['sources']);require(runtime==runtime_fact(cfg['runtime_path']),'RUNTIME_CHANGED_DURING_A')
            tree(cfg,cfg['execution_commit']);status='STATIC_READY_FOR_REVIEW'
        else:
            require(runtime==json.loads((old/'runtime_file.json').read_text(encoding='utf8')),'RUNTIME_CHANGED_SINCE_A')
            built=json.loads((old/'build/build.json').read_text(encoding='utf8'))
            shutil.copyfile(old/'receipt.json',out/'reviewed_static_receipt.json')
            shutil.copyfile(old/'build/build.json',out/'reviewed_build.json')
            shutil.copyfile(old/'runtime_file.json',out/'reviewed_runtime_file.json')
            require(sha(cfg['nsys'])==cfg['nsys_sha256'],'COLLECTOR_IDENTITY')
            env=os.environ.copy();env.update(CUDA_VISIBLE_DEVICES='3',CUDA_DEVICE_ORDER='PCI_BUS_ID')
            side=out/'side.json';capture=out/'capture'
            command([cfg['nsys'],'--version'],out,out/'nsys_version',env=env,timeout=30)
            require(b'2026.2.1.210' in (out/'nsys_version.stdout').read_bytes(),'COLLECTOR_VERSION')
            command([cfg['nsys'],'profile','--trace=cuda,nvtx','--sample=none','--cpuctxsw=none',
                '--force-overwrite=false','--output',str(capture),built['micro'],cfg['runtime_path'],built['recorder'],
                cfg['run_id'],str(side),cfg['gpu_uuid'],cfg['gpu_pci']],out,out/'profile',env=env,timeout=120)
            command([cfg['nsys'],'export','--type=sqlite','--force-overwrite=false',
                '--output',str(out/'capture.sqlite'),str(out/'capture.nsys-rep')],out,out/'export',env=env,timeout=120)
            verify_rows(ROOT,cfg['sources']);verify_rows(old/'build',built['binary_files']);tree(cfg,cfg['execution_commit'])
            from analysis.memset_same_capture import review_files
            expected=dict(run_id=cfg['run_id'],runtime_path=cfg['runtime_path'],gpu_uuid=cfg['gpu_uuid'],pci_bus_id=cfg['gpu_pci'])
            review_files(out/'capture.sqlite',side,expected,out/'derived')
            require(runtime==runtime_fact(cfg['runtime_path']),'RUNTIME_CHANGED_DURING_CAPTURE')
            status='MICRO_EVIDENCE_COMPLETE_PENDING_REVIEW'
    except BaseException as exc:error=type(exc).__name__+':'+str(exc)
    write(out/'receipt.json',dict(schema_version='memset-micro-receipt/0.1.0',status=status,error=error,phase=phase,
        execution_commit=cfg['execution_commit'],analysis_commit=cfg['execution_commit'],package_index_sha256=index_sha,
        build_sha256=build_sha,reviewed_static_receipt_sha256=reviewed,role='Engineering',automatic_retry=False,
        runtime_file_sha256=sha(out/'runtime_file.json') if (out/'runtime_file.json').is_file() else None,
        stage_a_cuda_programs_executed=0 if phase=='A' else None,model_process_budget=0,
        micro_process_budget=0 if phase=='A' else 1,profile_budget=0 if phase=='A' else 1,
        coe_admission='NOT_ASSESSED',dropped_records_status='UNKNOWN',historical_ylq_total_bytes=None,
        long_term_target_exclusive_bytes=50000000000))
    try:print(json.dumps(pack(out,archive)),flush=True)
    except BaseException as exc:
        print('PACK_REFUSED_PRESERVE_SCENE:'+str(exc),flush=True);return 2
    if error:print('STOP:'+error,flush=True);return 2
    return 0


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['stage-a','stage-b']);p.add_argument('package',type=Path)
    p.add_argument('--reviewed-static-sha256')
    a=p.parse_args(argv)
    return stage(a.package,'A' if a.action=='stage-a' else 'B',a.reviewed_static_sha256)


if __name__=='__main__':raise SystemExit(main())
