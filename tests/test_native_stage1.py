"""Stage1 CPU artifacts only: no native model/CUDA/collector execution."""
import importlib
import json
import zipfile
import hashlib
import subprocess
import warnings
import os
from pathlib import Path

import pytest


def api():
    assert importlib.util.find_spec('exposedpath.native_stage1'), 'stage1 delivery contract missing'
    return importlib.import_module('exposedpath.native_stage1')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def archive(tmp_path, entries):
    p=tmp_path/'source.zip'
    with zipfile.ZipFile(p,'w') as z:
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore',message='Duplicate name:')
            for name,data in entries:z.writestr(name,data)
    return p


def test_extract_preserves_bytes_and_rejects_resume(tmp_path):
    p=archive(tmp_path,[('src/a.txt',b'\r\nexact bytes')])
    out=tmp_path/'new'
    api().extract(p,out)
    assert (out/'src/a.txt').read_bytes()==b'\r\nexact bytes'
    with pytest.raises(FileExistsError):api().extract(p,out)


@pytest.mark.parametrize('names', [['../escape'],['C:/escape'],['a','A'],['a//b'],['a:ads'],['a','a'],['a/../b']])
def test_unsafe_or_duplicate_archive_rejected_before_writes(tmp_path,names):
    p=archive(tmp_path,[(n,b'x') for n in names]); out=tmp_path/'out'
    with pytest.raises(ValueError):api().extract(p,out)
    assert not out.exists()


def test_probe_patch_disables_execution_not_compilation(tmp_path):
    old=b'function(cmake_cuda_architectures_native lang)\nexecute_process(COMMAND gpu.exe)\nendfunction()\n'
    module=tmp_path/'module.cmake';module.write_bytes(old)
    receipt=api().disable_cuda_probe(module,sha(old),tmp_path/'original.cmake')
    assert receipt['original_sha256']==sha(old)
    assert (tmp_path/'original.cmake').read_bytes()==old
    cmake=Path(os.environ.get('EXPOSEDPATH_TEST_CMAKE','.local/vendor/cmake-stage1/cmake/data/bin/cmake.exe')).resolve()
    if not cmake.is_file():pytest.skip('fixed CPU CMake cache unavailable; no download in tests')
    caller=tmp_path/'caller.cmake'
    caller.write_text('include("'+module.as_posix()+'")\n'
        'set(CMAKE_CUDA_ARCHITECTURES_NATIVE "must-be-cleared")\n'
        'cmake_cuda_architectures_native(CUDA)\n'
        'if(NOT CMAKE_CUDA_ARCHITECTURES_NATIVE STREQUAL "")\nmessage(FATAL_ERROR "probe ran/not cleared")\nendif()\n')
    result=subprocess.run([str(cmake),'-P',str(caller)],capture_output=True)
    assert result.returncode==0,result.stderr
    assert b'EXPOSEDPATH_STAGE1_CUDA_DEVICE_PROBE_DISABLED' in result.stdout
    with pytest.raises(ValueError):api().disable_cuda_probe(module,sha(old),tmp_path/'another.cmake')


def test_hf_inventory_binds_exact_paths_and_content(tmp_path):
    root=tmp_path/'hf';root.mkdir();(root/'config.json').write_bytes(b'{"model_type":"qwen2"}')
    expected=[dict(path='config.json',size_bytes=22,sha256=sha((root/'config.json').read_bytes()))]
    # Literal length checked independently, not taken from the production function.
    assert len((root/'config.json').read_bytes())==22
    assert api().verify_hf(root,expected)[0]['sha256']==expected[0]['sha256']
    (root/'config.json').write_bytes(b'{"model_type":"evil!!"}')
    with pytest.raises(ValueError):api().verify_hf(root,expected)


@pytest.mark.parametrize('name',['../outside','C:/outside','config.json:ads'])
def test_hf_path_escape_rejected(tmp_path,name):
    with pytest.raises(ValueError):api().verify_hf(tmp_path,[dict(path=name,size_bytes=1,sha256='a'*64)])


def test_gguf_actual_types_not_requested_outtype(tmp_path):
    class Type:
        def __init__(self,name):self.name=name
    class Field:
        def contents(self):return 'qwen2'
    class Tensor:
        def __init__(self,name,typ):
            self.name=name;self.tensor_type=Type(typ);self.shape=[2,3];self.n_bytes=12;self.data_offset=16
    class Reader:
        fields={'general.architecture':Field()}
        tensors=[Tensor('weight','F16'),Tensor('norm','F32')]
    value=api().inspect_gguf('not-loaded-model',reader_factory=lambda p:Reader())
    assert value['tensor_types']=={'F16':1,'F32':1}
    assert value['architecture']=='qwen2'
    Reader.tensors=[Tensor('quantized','Q4_0')]
    with pytest.raises(ValueError):api().inspect_gguf('not-loaded-model',reader_factory=lambda p:Reader())


def test_pack_only_review_files_not_model_or_build_tree(tmp_path):
    root=tmp_path/'run';root.mkdir();(root/'receipt.json').write_text('{"status":"STAGE1_COMPLETE_NOT_QUALIFICATION"}')
    (root/'large.gguf').write_bytes(b'not for return')
    logs=root/'logs';logs.mkdir();(logs/'step.json').write_text('{"exit_code":0}')
    out=tmp_path/'return.zip'
    api().pack_review(root,out)
    with zipfile.ZipFile(out) as z:
        assert set(z.namelist())=={'receipt.json','logs/step.json','artifact_manifest.json'}
        m=json.loads(z.read('artifact_manifest.json'))
        assert len(m['files'])==2
        for r in m['files']:assert sha(z.read(r['path']))==r['sha256']


def test_command_plan_only_build_convert_inspect(tmp_path):
    p=api().command_plan(tmp_path/'code',tmp_path/'engine',tmp_path/'run',tmp_path/'hf',tmp_path/'nvtx',tmp_path/'cuda')
    assert [s['name'] for s in p]==['configure','build','convert','inspect']
    configure=p[0]['arguments']
    assert '-DCMAKE_CUDA_ARCHITECTURES=89' in configure
    assert '-DFETCHCONTENT_FULLY_DISCONNECTED=ON' in configure
    assert '--target' in p[1]['arguments'] and 'native-llama' in p[1]['arguments']
    assert p[2]['arguments'][-2:]==['--outtype','f16']
    assert not any('nsys' in a or a.endswith('native-llama.exe') for s in p for a in s['arguments'])


def test_artifact_mismatch_records_actual_not_replaced_expectation(tmp_path):
    p=tmp_path/'file';p.write_bytes(b'changed')
    failures=api().verify_files(tmp_path,[dict(path='file',size_bytes=4,sha256='a'*64)])
    assert failures==[dict(path='file',reason='CONTENT_CONFLICT',expected_size_bytes=4,
        actual_size_bytes=7,expected_sha256='a'*64,actual_sha256=sha(b'changed'))]


def test_missing_file_is_not_empty_set_success(tmp_path):
    failures=api().verify_files(tmp_path,[dict(path='missing',size_bytes=1,sha256='a'*64)])
    assert failures[0]['reason']=='FILE_MISSING'


def test_cpu_file_chain_runs_all_stage1_steps_and_creates_bound_receipts(tmp_path,monkeypatch):
    a=api(); from exposedpath import native_llama
    package=tmp_path/'package';package.mkdir(); root=tmp_path/'diagnostics'/'new';root.mkdir(parents=True)
    hf=tmp_path/'hf';hf.mkdir();(hf/'config.json').write_bytes(b'{"model_type":"qwen2"}')
    expected=[dict(path='config.json',size_bytes=22,sha256=sha((hf/'config.json').read_bytes()))]
    csv_data=('RelativePath,Bytes,SHA256\nconfig.json,22,'+expected[0]['sha256']+'\n').encode()
    (package/'model_sha256.csv').write_bytes(csv_data)
    a.write(package/'hf_reference.json',dict(source_manifest_sha256=sha(csv_data),files=expected))
    engine_archive=package/'llama_source.zip'
    with zipfile.ZipFile(engine_archive,'w') as z:z.writestr('convert_hf_to_gguf.py',b'# CPU fixture')
    a.write(package/'llama_source_manifest.json',dict(files=[dict(path='convert_hf_to_gguf.py',size_bytes=13,sha256=sha(b'# CPU fixture'))]))
    with zipfile.ZipFile(package/'nvtx_headers.zip','w') as z:z.writestr('include/nvtx3/nvToolsExt.h',b'fixture')
    (package/'requirements.lock').write_text('cpu fixture')
    original=b'function(cmake_cuda_architectures_native lang)\nendfunction()\n'
    a.write(root/'toolchain.json',dict(observed='CPU substitute; not target VS'))
    source=tmp_path/'code'/'native/llama_cpp/main.cpp';source.parent.mkdir(parents=True);source.write_bytes(b'CPU code')
    cfg=dict(schema_version=a.VERSION,model_process_budget=0,profile_budget=0,
        code_root=str(tmp_path/'code'),server_root=str(tmp_path),model_root=str(hf),cuda_root=str(tmp_path/'cuda'),
        git='git',base_python='python',execution_commit='a'*40,engine_commit=native_llama.ENGINE_COMMIT,
        cmake_probe_sha256=sha(original),hf_manifest_sha256=sha(csv_data),native_source_paths=['native/llama_cpp/main.cpp'])
    a.write(package/'config.json',cfg)
    files=[dict(path=p.name,size_bytes=p.stat().st_size,sha256=a.digest(p)) for p in package.iterdir()]
    a.write(package/'package_manifest.json',dict(files=files))
    # Only replace compilation/conversion external dependency; keep file gates,
    # source verification, orchestration and receipt creation real.
    monkeypatch.setattr(native_llama,'instrument_backend',lambda src,out:Path(out).write_bytes(b'compiled hook'))
    class CpuRunner:
        records=[]
        def run(self,name,argv,**kw):
            self.records.append(dict(name=name,exit_code=0,argv=[str(x) for x in argv]))
            if name=='git_head':return b'a'*40+b'\n'
            if name=='engine_head':return native_llama.ENGINE_COMMIT.encode()+b'\n'
            if name=='create_cpu_environment':
                p=root/'converter/Lib/site-packages/cmake/data/share/cmake-3.31/Modules/Internal/CMakeCUDAArchitecturesNative.cmake'
                p.parent.mkdir(parents=True);p.write_bytes(original)
            if name=='cmake_version':return b'cmake version 3.31.10\n'
            if name=='build':
                p=root/'build/bin/Release/native-llama.exe';p.parent.mkdir(parents=True);p.write_bytes(b'not executable')
                (root/'build/CMakeCache.txt').write_text('CMAKE_CUDA_ARCHITECTURES:STRING=89\nGGML_CUDA_GRAPHS:BOOL=OFF\nGGML_NATIVE:BOOL=OFF\nFETCHCONTENT_FULLY_DISCONNECTED:BOOL=ON\n')
            if name=='convert':(root/'model-f16.gguf').write_bytes(b'CPU GGUF substitute')
            if name=='inspect':a.write(root/'gguf_inspection.json',dict(architecture='qwen2',tensor_types={'F16':1,'F32':1}))
            return b''
    runner=CpuRunner();a.execute(package/'config.json',package,root,runner=runner)
    receipt=a.read(root/'receipt.json')
    assert receipt['status']=='STAGE1_COMPLETE_NOT_QUALIFICATION'
    assert receipt['gpu_qualification']=='NOT_RUN' and not receipt['model_executed']
    assert receipt['build_receipt_sha256']==a.digest(root/'build_receipt.json')
    assert a.read(root/'conversion_receipt.json')['tensor_types']=={'F16':1,'F32':1}
    assert 'dependency_check' in [r['name'] for r in runner.records]
    assert [r['name'] for r in runner.records][-4:]==['configure','build','convert','inspect']


def test_hf_reference_cannot_borrow_unbound_manifest_hash(tmp_path):
    a=api(); package=tmp_path/'package';package.mkdir()
    (package/'model_sha256.csv').write_bytes(b'other manifest')
    a.write(package/'hf_reference.json',dict(source_manifest_sha256='a'*64,files=[dict(path='config.json',size_bytes=1,sha256='b'*64)]))
    with pytest.raises(ValueError,match='HF_MANIFEST_BINDING'):
        a.bound_hf_reference(package,'a'*64)


def test_failing_cpu_subprocess_retains_raw_stderr_and_stops(tmp_path):
    a=api();root=tmp_path/'run';root.mkdir(); runner=a.Runner(root)
    import sys
    with pytest.raises(ValueError,match='STEP_EXIT'):
        runner.run('failure',[sys.executable,'-I','-c',
            'import os,sys; os.write(2,b"original\\xff error"); sys.exit(7)'])
    assert (root/'logs/failure.stderr.txt').read_bytes()==b'original\xff error'
    result=a.read(root/'logs/failure.json')
    assert result['exit_code']==7 and result['timed_out'] is False


def test_partial_build_does_not_produce_conversion_or_complete_receipt(tmp_path,monkeypatch):
    # Reuse the actual file-chain positive harness, replacing only Runner.build
    # by an external failure. At that boundary conversion must not be reached.
    a=api()
    original=a.execute
    def inject(config,package,root,*,runner):
        inner=runner.run
        def run(name,argv,**kw):
            if name=='build':raise RuntimeError('compiler failure fixture')
            return inner(name,argv,**kw)
        runner.run=run
        return original(config,package,root,runner=runner)
    monkeypatch.setattr(a,'execute',inject)
    with pytest.raises(RuntimeError,match='compiler failure fixture'):
        test_cpu_file_chain_runs_all_stage1_steps_and_creates_bound_receipts(tmp_path,monkeypatch)
    root=tmp_path/'diagnostics/new'
    assert a.read(root/'receipt.json')['status']=='BLOCKED'
    assert not (root/'conversion_receipt.json').exists()
    assert not (root/'model-f16.gguf').exists()


def test_bundle_advertises_fixed_commit_and_requires_history(tmp_path):
    from scripts import package_native_llama_stage1 as delivery
    repo=tmp_path/'tiny-git-fixture';repo.mkdir()
    def git(*args):return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.PIPE)
    git('init');git('config','user.name','CPU test');git('config','user.email','test@example.invalid')
    (repo/'file').write_text('first');git('add','file');git('commit','-m','first')
    parent=git('rev-parse','HEAD').decode().strip()
    (repo/'file').write_text('second');git('commit','-am','second')
    head=git('rev-parse','HEAD').decode().strip();bundle=tmp_path/'execution.bundle'
    delivery.create_execution_bundle(repo,head,parent,bundle)
    refs=subprocess.check_output(['git','bundle','list-heads',str(bundle)]).decode().strip()
    assert refs==head+' HEAD'
    git('bundle','verify',str(bundle))
    with pytest.raises(ValueError):delivery.create_execution_bundle(repo,parent,'a'*40,tmp_path/'wrong.bundle')


def test_powershell_entry_rejects_wrong_role_without_outputs(tmp_path):
    import shutil
    ps=shutil.which('powershell.exe')
    if not ps:pytest.skip('Windows PowerShell not present')
    package=tmp_path/'package';package.mkdir()
    (package/'config.json').write_text(json.dumps(dict(schema_version='FORMAL',model_process_budget=2,profile_budget=1)),encoding='utf-8')
    result=subprocess.run([ps,'-NoProfile','-ExecutionPolicy','Bypass','-File',
        str(Path('scripts/run_native_llama_stage1.ps1').resolve()),'-PackageRoot',str(package)],capture_output=True)
    assert result.returncode!=0
    assert {p.name for p in package.iterdir()}=={'config.json'}


def test_changed_return_source_is_not_valid_archive(tmp_path,monkeypatch):
    a=api();root=tmp_path/'run';root.mkdir();source=root/'receipt.json';source.write_text('{"status":"BLOCKED"}')
    original=zipfile.ZipFile.write
    def mutate(self,filename,*args,**kwargs):
        original(self,filename,*args,**kwargs)
        Path(filename).write_text('changed while copied')
    monkeypatch.setattr(zipfile.ZipFile,'write',mutate)
    with pytest.raises(ValueError,match='RETURN_SOURCE_CHANGED'):a.pack_review(root,tmp_path/'failed.zip')
    assert (tmp_path/'failed.zip').exists() # preserve failed copy, never label valid
