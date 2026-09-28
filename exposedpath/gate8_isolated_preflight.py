"""One-run pre-profile observations; target validation never launches tools."""
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import time
import uuid

from scripts.gate7_smoke_validation import validate_pre_model_identity

VERSION='exposedpath-isolated-preflight/0.1.0'
MAX_AGE_NS=120*10**9
INPUTS=('manifest.json','preflight.json','prompt.json','model_inventory.csv')


def require(ok,reason):
    if not ok: raise ValueError('ISOLATED_PREFLIGHT_'+reason)


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b''): digest.update(chunk)
    return digest.hexdigest()


def read(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write_new(path,value):
    with Path(path).open('x',encoding='utf-8') as handle:
        json.dump(value,handle,sort_keys=True,indent=2)
        handle.flush(); os.fsync(handle.fileno())


def _git_paths(root, output, *, tracked):
    """Preserve Git's NUL stream before strict parsing, never via locale text pipes."""
    from exposedpath import platform_adapter as adapter
    kind='tracked' if tracked else 'ignored'
    args=['-C',str(root),'ls-files']+(['--cached'] if tracked else
        ['--others','--ignored','--exclude-standard','--directory'])+['-z']
    prefix=Path(output)/('git_'+kind+'_paths')
    report=dict(status='BLOCKED',query=kind,args=args,exit_code=None,
                parser='strict-utf8-nul/1',stdout=None,stderr=None)
    try:
        result=adapter.run_tool(adapter.TOOL_GIT,args,text=False,timeout=5)
        report['exit_code']=result.returncode
        for stream in ('stdout','stderr'):
            raw=getattr(result,stream)
            if isinstance(raw,bytes):
                path=prefix.with_suffix('.'+stream+'.bin')
                with path.open('xb') as handle: handle.write(raw)
                report[stream]=dict(file=path.name,bytes=len(raw),sha256=sha(path))
        require(type(result.returncode) is int and result.returncode==0,'GIT_PATH_EXIT')
        require(isinstance(result.stdout,bytes) and isinstance(result.stderr,bytes),'GIT_PATH_READ')
        raw=result.stdout
        require(bool(raw) or not tracked,'GIT_PATH_EMPTY_TRACKED')
        require(not raw or raw.endswith(b'\0'),'GIT_PATH_TERMINATOR')
        try: names=raw[:-1].decode('utf-8',errors='strict').split('\0') if raw else []
        except UnicodeDecodeError as exc:
            raise ValueError('ISOLATED_PREFLIGHT_GIT_PATH_UTF8') from exc
        paths=set(); identities=set()
        for name in names:
            # Git emits forward slashes; reject aliases, traversal, drives and UNC.
            directory=name.endswith('/')
            plain=name[:-1] if directory else name
            require(bool(plain) and (not directory or not tracked) and '\\' not in name
                and not PureWindowsPath(name).drive and ':' not in name
                and all(part not in ('','.','..') for part in plain.split('/')),'GIT_PATH_SCOPE')
            key=os.path.normcase(plain)
            require(key not in identities,'GIT_PATH_DUPLICATE')
            identities.add(key); paths.add(name)
    except Exception as exc:
        report.update(error_type=type(exc).__name__,error=str(exc))
        try: write_new(prefix.with_suffix('.json'),report)
        except OSError as write_error: exc.add_note('Git query receipt write failed: '+str(write_error))
        raise
    report.update(status='PASS',path_count=len(paths))
    write_new(prefix.with_suffix('.json'),report)
    return paths


def tree(root,excluded):
    root=Path(root).resolve(); result={}
    for base,dirs,files in os.walk(root,followlinks=False):
        here=Path(base)
        kept=[]
        for name in dirs:
            p=here/name; relative=p.relative_to(root).as_posix()
            if name in ('.git','__pycache__','.pytest_cache') or relative+'/' in excluded: continue
            require(not p.is_symlink() and p.resolve()==p,'TREE_REDIRECT')
            kept.append(name)
        dirs[:]=kept
        for name in files:
            p=here/name; relative=p.relative_to(root).as_posix()
            if relative in excluded or p.suffix in ('.pyc','.pyo'): continue
            require(not p.is_symlink() and p.resolve()==p,'FILE_REDIRECT')
            result[relative]=sha(p)
    return result


def git_metadata(root):
    root=Path(root); git=root/'.git'
    require(git.is_dir() and not git.is_symlink(),'FIXED_CHECKOUT_REQUIRED')
    require(not any(git.rglob('*.lock')),'GIT_BUSY')
    paths=[git/name for name in ('HEAD','index','packed-refs','config','shallow','commondir')]
    paths+=list((git/'refs').rglob('*')) if (git/'refs').exists() else []
    return {p.relative_to(git).as_posix():sha(p) for p in paths if p.is_file()}


def verify_snapshot(value,prepared,root):
    require(str(Path(root).resolve())==value['project_root'],'ROOT')
    require({name:sha(Path(prepared)/name) for name in INPUTS}==value['input_hashes'],'INPUT_CHANGED')
    require(git_metadata(root)==value['git_metadata'],'GIT_CHANGED')
    require(tree(root,set(value['excluded']))==value['tree_hashes'],'CONTENT_CHANGED')
    from exposedpath_v141.gate8_target_python import environment
    require(environment()==value['environment'],'ENVIRONMENT_CHANGED')


def seal(prepared,output,root):
    """Collector only, immediately before profile. No receipt refresh or retry."""
    from exposedpath import platform_adapter as adapter
    from exposedpath_v141.gate8_adapter import normalized_uuid,normalized_pci
    from exposedpath_v141.gate8_target_python import environment
    prepared,output,root=map(lambda p:Path(p).resolve(),(prepared,output,root))
    manifest=read(prepared/'manifest.json')
    require(manifest.get('isolated_preflight_version')==VERSION,'VERSION')
    issues=validate_pre_model_identity(prepared/'manifest.json',prepared/'preflight.json',root)
    require(not issues,'IDENTITY:'+ '; '.join(issues))
    git=lambda args:adapter.git(['-C',str(root),*args])
    before=(git(['rev-parse','HEAD']),git(['status','--porcelain']))
    require(before==(manifest['runner_git_commit'],''),'GIT_IDENTITY')
    excluded=_git_paths(root,output,tracked=False)
    inventory=tree(root,excluded)
    tracked=_git_paths(root,output,tracked=True)
    require(tracked<=inventory.keys(),'TRACKED_CONTENT_NOT_SEALED')
    physical=manifest['gpu_index_physical']
    rows=adapter.nvidia_smi(['--id='+str(physical),'--query-gpu=index,uuid,pci.bus_id',
                            '--format=csv,noheader,nounits']).splitlines()
    require(len(rows)==1 and len(rows[0].split(','))==3,'GPU_QUERY')
    index,gpu,pci=[x.strip() for x in rows[0].split(',')]
    require(index==str(physical) and normalized_uuid(gpu)==normalized_uuid(manifest['gpu_uuid'])
        and normalized_pci(pci)==normalized_pci(manifest['gpu_pci_bus_id']),'GPU_CONFLICT')
    value=dict(schema_version=VERSION,run_id=manifest['run_id'],nonce=uuid.uuid4().hex,
        output_root=str(output),project_root=str(root),collector_pid=os.getpid(),
        git_commit=before[0],git_dirty=False,git_observation_role='PREFLIGHT_NOT_TARGET_GIT_QUERY',
        gpu_observation=dict(physical_index=physical,gpu_uuid=gpu,pci_bus_id=pci),
        input_hashes={name:sha(prepared/name) for name in INPUTS},
        excluded=sorted(excluded),tree_hashes=inventory,git_metadata=git_metadata(root),environment=environment())
    require((git(['rev-parse','HEAD']),git(['status','--porcelain']))==before,'PREFLIGHT_CHANGED')
    verify_snapshot(value,prepared,root)
    value.update(issued_wall_ns=time.time_ns(),issued_monotonic_ns=time.monotonic_ns())
    path=output/'auxiliary_preflight.json'; write_new(path,value)
    return path


def consume(*,receipt,expected_sha,nonce,prepared,output,root):
    require(sha(receipt)==expected_sha,'RECEIPT_HASH')
    value=read(receipt)
    require(value.get('schema_version')==VERSION,'VERSION')
    require(value['nonce']==nonce and value['output_root']==str(Path(output).resolve()),'LAUNCH_IDENTITY')
    require(Path(receipt).resolve()==Path(output).resolve()/'auxiliary_preflight.json','RECEIPT_LOCATION')
    require(value['run_id']==read(Path(prepared)/'manifest.json')['run_id'],'RUN')
    require(value['git_dirty'] is False and value['git_observation_role']=='PREFLIGHT_NOT_TARGET_GIT_QUERY','GIT_OBSERVATION')
    def fresh():
        for observed,key in ((time.time_ns(),'issued_wall_ns'),(time.monotonic_ns(),'issued_monotonic_ns')):
            require(type(value[key]) is int and 0<=observed-value[key]<=MAX_AGE_NS,'EXPIRED_OR_CLOCK')
    fresh()
    verify_snapshot(value,prepared,root)
    fresh()
    claim=dict(schema_version=VERSION,preflight_sha256=expected_sha,nonce=nonce,run_id=value['run_id'],
        target_pid=os.getpid(),parent_pid=os.getppid(),git_observation_role=value['git_observation_role'])
    write_new(Path(output)/'auxiliary_preflight.claim.json',claim)
    return claim


def finalize(receipt,prepared,root):
    """Collector post-profile check; never converts target failure to success."""
    value=read(receipt); verify_snapshot(value,prepared,root)
    from exposedpath import platform_adapter as adapter
    require(adapter.git(['-C',str(root),'rev-parse','HEAD'])==value['git_commit'] and
        adapter.git(['-C',str(root),'status','--porcelain'])=='','POST_GIT_CHANGED')
