"""Build the offline delivery locally, never run toolchain or model programs."""
import argparse
import csv
from email.parser import Parser
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from exposedpath import native_stage1 as stage, native_llama as native


def git(*args):return subprocess.check_output(['git',*map(str,args)])


def create_execution_bundle(repo,commit,prerequisite,bundle):
    stage.require(git('-C',repo,'rev-parse','HEAD').decode().strip()==commit,'BUNDLE_HEAD')
    git('-C',repo,'merge-base','--is-ancestor',prerequisite,commit)
    git('-C',repo,'bundle','create',bundle,'HEAD','^'+prerequisite)
    stage.require(git('bundle','list-heads',bundle).decode().strip()==commit+' HEAD','BUNDLE_ADVERTISED_IDENTITY')


def index(root):
    root=Path(root)
    return [dict(path=p.relative_to(root).as_posix(),size_bytes=p.stat().st_size,sha256=stage.digest(p))
        for p in sorted(root.rglob('*')) if p.is_file()]


def directories(root):
    root=Path(root)
    names=[p.relative_to(root).as_posix() for p in sorted(root.rglob('*')) if p.is_dir()]
    for name in names:stage.require(stage.checked(root,name).is_dir(),'ARCHIVE_DIRECTORY')
    return names


def zip_tree(root,archive,*,subset=None):
    root=Path(root);rows=index(root) if subset is None else subset
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,allowZip64=True) as z:
        for name in directories(root):z.write(stage.checked(root,name),name+'/')
        for r in rows:z.write(stage.checked(root,r['path']),r['path'])
    return rows


def assemble_repair(destination,*,commit,prerequisite,reuse_delivery,engine_source,server):
    """Small repair; reuse ONLY byte-verified original offline dependency assets."""
    old=Path(reuse_delivery).resolve();destination=Path(destination).resolve()
    if destination.exists():raise FileExistsError(destination)
    old_manifest_sha='408c63b0ff6e3ebf01012190240d8dd075943daf76b259608a62bb4ec07a6a53'
    stage.resolve_assets(destination,dict(reuse_dependency_root=str(old),reuse_manifest_sha256=old_manifest_sha))
    old_cfg=stage.read(old/'config.json')
    stage.require(prerequisite==old_cfg['execution_commit']=='cc9b595a42a39ff5d6524274a4dda4c03717dc16','REPAIR_PREREQUISITE')
    for k in ('code_root','model_root','base_python','test_python','git','cuda_root','vs_root'):
        stage.require(server[k]==old_cfg[k],'REPAIR_EXECUTION_CONFIG')
    source_manifest=stage.read(old/'llama_source_manifest.json')
    stage.require(not stage.verify_files(engine_source,source_manifest['files']),'REPAIR_ORIGINAL_SOURCE_BYTES')
    stage.require(git('-C',engine_source,'rev-parse','HEAD').decode().strip()==native.ENGINE_COMMIT,'REPAIR_SOURCE_COMMIT')
    destination.mkdir(parents=True)
    create_execution_bundle('.',commit,prerequisite,destination/'execution.bundle')
    for source,target in [('exposedpath/native_stage1.py','native_stage1.py'),('scripts/run_native_llama_stage1.ps1','run_native_llama_stage1.ps1')]:
        (destination/target).write_bytes(git('show',commit+':'+source))
    stage.write(destination/'llama_source_layout.json',dict(schema_version='exposedpath-native-source-layout/0.1.0',
        source_archive_sha256=stage.digest(old/'llama_source.zip'),directories=directories(engine_source),
        engine_commit=native.ENGINE_COMMIT,files_manifest_sha256=stage.digest(old/'llama_source_manifest.json'),
        basis='Original producer directory snapshot; all source files byte-matched to sealed file manifest'))
    cfg=dict(old_cfg,**server)
    cfg.update(execution_commit=commit,prerequisite=prerequisite,bundle_ref='HEAD',
        reuse_dependency_root=server['reuse_dependency_root'],reuse_manifest_sha256=old_manifest_sha)
    stage.write(destination/'config.json',cfg)
    stage.write(destination/'package_manifest.json',dict(schema_version=stage.VERSION,execution_commit=commit,files=index(destination)))
    archive=destination.with_suffix('.zip');zip_tree(destination,archive)
    with zipfile.ZipFile(archive) as z:stage.require(z.testzip() is None,'REPAIR_ZIP_CRC')
    return dict(path=str(archive),size_bytes=archive.stat().st_size,sha256=stage.digest(archive),execution_commit=commit,
        prerequisite=prerequisite,launcher_sha256=stage.digest(destination/'run_native_llama_stage1.ps1'),
        manifest_sha256=stage.digest(destination/'package_manifest.json'),reused_manifest_sha256=old_manifest_sha)


def assemble_ninja(destination,*,commit,prerequisite,reuse_delivery,reuse_repair,ninja_exe,ninja_license,vs_facts,prior_review,query_review,server):
    """Fixed small route repair, no reinstall and no system metadata edits."""
    from exposedpath import native_ninja
    stage.require(prerequisite=='882425c02f3e0ec70679c0ed58875a852cf3cbd1','NINJA_REPAIR_PREREQUISITE')
    old=Path(reuse_delivery).resolve();repair=Path(reuse_repair).resolve();destination=Path(destination).resolve()
    if destination.exists():raise FileExistsError(destination)
    old_manifest_sha='408c63b0ff6e3ebf01012190240d8dd075943daf76b259608a62bb4ec07a6a53'
    stage.resolve_assets(destination,dict(reuse_dependency_root=str(old),reuse_manifest_sha256=old_manifest_sha))
    stage.require(stage.digest(repair/'package_manifest.json')=='6eae6928ced551c8480ac51a404d65700b0487e3b084a243c954579d9aa5fa0f','NINJA_LAYOUT_PACKAGE')
    stage.require(not stage.verify_files(repair,stage.read(repair/'package_manifest.json')['files']),'NINJA_LAYOUT_PACKAGE_CONTENT')
    stage.require(stage.digest(ninja_exe)==native_ninja.NINJA_SHA256,'NINJA_ASSET_HASH')
    stage.require(stage.digest(ninja_license)=='eb7e9ab9690124c5c9f42bdc81383d886a3dede26345b6ed15bbad7caf81f7ea','NINJA_LICENSE_HASH')
    stage.require(stage.digest(vs_facts)=='e1dad7999c2d4e0780c23e9664bb807e9e5f55d06483d7e884430bc05709d34d'
        and stage.digest(prior_review)=='ddfa4d5830874c2c0d98949deecd806fb447ccb07b329157ac37d2ec0b143e3c','NINJA_EVIDENCE_INPUTS')
    stage.require(stage.digest(query_review)=='3d8f2599cf0dec1499463e1a90d1ab1b3dcb32bbf2bd2df14314da3fa6746264','NINJA_QUERY_EVIDENCE_INPUT')
    original=stage.read(old/'config.json')
    for key in ('code_root','model_root','base_python','test_python','git','cuda_root','vs_root'):
        stage.require(server[key]==original[key],'NINJA_EXECUTION_CONFIG_CONFLICT:'+key)
    destination.mkdir(parents=True)
    create_execution_bundle('.',commit,prerequisite,destination/'execution.bundle')
    for source,target in [('exposedpath/native_stage1.py','native_stage1.py'),('scripts/run_native_llama_stage1.ps1','run_native_llama_stage1.ps1')]:
        (destination/target).write_bytes(git('show',commit+':'+source))
    for source,target in [(ninja_exe,'ninja.exe'),(ninja_license,'NINJA_COPYING'),
        (vs_facts,'vs_facts.zip'),(prior_review,'prior_review.zip'),(query_review,'query_review.zip'),
        (repair/'llama_source_layout.json','llama_source_layout.json')]:
        shutil.copyfile(source,destination/target)
    cfg=dict(original,**server)
    cfg.update(schema_version=native_ninja.VERSION,execution_commit=commit,prerequisite=prerequisite,bundle_ref='HEAD',
        reuse_manifest_sha256=old_manifest_sha,vs_facts_zip_sha256=stage.digest(vs_facts),prior_review_sha256=stage.digest(prior_review),
        reuse_cpu_commit='598d447811e948a3ffb54845185631f4be761985',query_reference_commit=prerequisite,
        tool_identity_version=native_ninja.TOOL_IDENTITY_VERSION,query_review_sha256=stage.digest(query_review))
    stage.write(destination/'config.json',cfg)
    stage.write(destination/'package_manifest.json',dict(schema_version=native_ninja.VERSION,execution_commit=commit,files=index(destination)))
    archive=destination.with_suffix('.zip');zip_tree(destination,archive)
    with zipfile.ZipFile(archive) as z:stage.require(z.testzip() is None,'NINJA_ZIP_CRC')
    return dict(path=str(archive),size_bytes=archive.stat().st_size,sha256=stage.digest(archive),execution_commit=commit,
        prerequisite=prerequisite,launcher_sha256=stage.digest(destination/'run_native_llama_stage1.ps1'),
        manifest_sha256=stage.digest(destination/'package_manifest.json'))


def assemble(destination,*,commit,prerequisite,engine_source,nvtx_source,wheels,hf_evidence,server):
    destination=Path(destination).resolve()
    if destination.exists():raise FileExistsError(destination)
    stage.require(git('rev-parse',commit).decode().strip()==commit,'COMMIT')
    stage.require(git('-C',engine_source,'rev-parse','HEAD').decode().strip()==native.ENGINE_COMMIT,'ENGINE_COMMIT')
    stage.require(not git('-C',engine_source,'status','--porcelain').strip(),'ENGINE_DIRTY')
    stage.require(stage.digest(Path(engine_source)/'ggml/src/ggml-cuda/ggml-cuda.cu')==native.BACKEND_SHA256,'ENGINE_BYTES')
    nvtx_commit='6230bdf710bc94f44d433acceba735aaa9090ba5'
    stage.require(git('-C',nvtx_source,'rev-parse','HEAD').decode().strip()==nvtx_commit,'NVTX_COMMIT')
    destination.mkdir(parents=True)
    # Local fixed source snapshot contains its shallow Git object/identity, but
    # no checkout of the research repo and no third-party code is pushed to ours.
    rows=zip_tree(engine_source,destination/'llama_source.zip')
    stage.write(destination/'llama_source_manifest.json',dict(engine_commit=native.ENGINE_COMMIT,files=rows))
    stage.write(destination/'llama_source_layout.json',dict(schema_version='exposedpath-native-source-layout/0.1.0',
        source_archive_sha256=stage.digest(destination/'llama_source.zip'),directories=directories(engine_source)))
    nvtx_root=Path(nvtx_source)/'c'
    nvtx_rows=index(nvtx_root/'include')
    with zipfile.ZipFile(destination/'nvtx_headers.zip','x',zipfile.ZIP_DEFLATED) as z:
        for r in nvtx_rows:z.write(nvtx_root/'include'/r['path'],'include/'+r['path'])
        z.write(Path(nvtx_source)/'LICENSE.txt','LICENSE.txt')
    bundle=destination/'execution.bundle'
    create_execution_bundle('.',commit,prerequisite,bundle)
    # HEAD is inside this sealed bundle and checked against commit before/after
    # creation and fetch; it is NOT a remote floating main reference.
    wheelroot=destination/'wheels';wheelroot.mkdir()
    lock=[];packages=[];probe_sha=None
    for p in sorted(Path(wheels).glob('*.whl')):
        with zipfile.ZipFile(p) as z:
            metadata=Parser().parsestr(z.read(next(n for n in z.namelist() if n.endswith('.dist-info/METADATA'))).decode())
            if metadata['Name']=='cmake':
                name=next(n for n in z.namelist() if n.endswith('/Internal/CMakeCUDAArchitecturesNative.cmake'))
                probe_sha=hashlib.sha256(z.read(name)).hexdigest()
        checksum=stage.digest(p);shutil.copyfile(p,wheelroot/p.name)
        lock.append(metadata['Name']+'=='+metadata['Version']+' --hash=sha256:'+checksum)
        packages.append(dict(name=metadata['Name'],version=metadata['Version'],filename=p.name,sha256=checksum))
    stage.require(probe_sha is not None and any(r['name']=='torch' and r['version']=='2.11.0+cpu' for r in packages),'CPU_WHEELS')
    (destination/'requirements.lock').write_text('\n'.join(lock)+'\n',encoding='utf-8')
    stage.write(destination/'dependencies.json',dict(engine_commit=native.ENGINE_COMMIT,nvtx_commit=nvtx_commit,
        python='3.11 Windows x64',packages=packages,gguf='fixed engine gguf-py (not PyPI)',
        sources=['https://github.com/ggml-org/llama.cpp','https://github.com/NVIDIA/NVTX',
                 'https://pypi.org/simple','https://download.pytorch.org/whl/cpu']))
    stage.require(stage.digest(hf_evidence)=='71ee4b6d618bf12acf937acac75673c06453236531af4d25eab2da765b14fd19','HF_SOURCE_ARCHIVE_IDENTITY')
    with zipfile.ZipFile(hf_evidence) as z:data=z.read('model_sha256.csv')
    checksum=hashlib.sha256(data).hexdigest()
    stage.require(checksum=='72465c906baeb0cfa4fd94d21ef6c69c1cd8046bb68c61a94c02a1580d2541f9','HF_MANIFEST_IDENTITY')
    (destination/'model_sha256.csv').write_bytes(data)
    facts=[dict(path=r['RelativePath'].replace('\\','/'),size_bytes=int(r['Bytes']),sha256=r['SHA256'].lower())
        for r in csv.DictReader(io.StringIO(data.decode('utf-8-sig'),newline=''))]
    stage.write(destination/'hf_reference.json',dict(source_manifest_sha256=checksum,files=facts,
        evidence_zip_sha256=stage.digest(hf_evidence),source_member='model_sha256.csv',
        role='Historical model-content snapshot, not new runtime or qualification evidence'))
    for source,target in [('exposedpath/native_stage1.py','native_stage1.py'),('scripts/run_native_llama_stage1.ps1','run_native_llama_stage1.ps1')]:
        (destination/target).write_bytes(git('show',commit+':'+source))
    cfg=dict(server,schema_version=stage.VERSION,execution_commit=commit,prerequisite=prerequisite,
        bundle_ref='HEAD',engine_commit=native.ENGINE_COMMIT,cmake_probe_sha256=probe_sha,
        hf_manifest_sha256=checksum,model_process_budget=0,profile_budget=0,
        native_source_paths=['native/llama_cpp/'+n for n in ('main.cpp','observer.cpp','observer.hpp','producer_core.hpp','CMakeLists.txt')])
    stage.write(destination/'config.json',cfg)
    stage.write(destination/'package_manifest.json',dict(schema_version=stage.VERSION,execution_commit=commit,files=index(destination)))
    archive=destination.with_suffix('.zip');zip_tree(destination,archive)
    with zipfile.ZipFile(archive) as z:stage.require(z.testzip() is None,'FINAL_ZIP_CRC')
    return dict(path=str(archive),size_bytes=archive.stat().st_size,sha256=stage.digest(archive),
        execution_commit=commit,prerequisite=prerequisite,launcher_sha256=stage.digest(destination/'run_native_llama_stage1.ps1'),
        manifest_sha256=stage.digest(destination/'package_manifest.json'))


def main():
    p=argparse.ArgumentParser()
    for name in ('destination','commit','prerequisite','engine-source','nvtx-source','wheels','hf-evidence','server-config'):
        p.add_argument('--'+name,required=True)
    p.add_argument('--reuse-delivery')
    a=p.parse_args()
    if a.reuse_delivery:
        result=assemble_repair(a.destination,commit=a.commit,prerequisite=a.prerequisite,reuse_delivery=a.reuse_delivery,
            engine_source=a.engine_source,server=stage.read(a.server_config))
    else:
        result=assemble(a.destination,commit=a.commit,prerequisite=a.prerequisite,engine_source=a.engine_source,
            nvtx_source=a.nvtx_source,wheels=a.wheels,hf_evidence=a.hf_evidence,server=stage.read(a.server_config))
    stage.write(Path(a.destination).with_suffix('.identity.json'),result);print(json.dumps(result,indent=2))


if __name__=='__main__':main()
