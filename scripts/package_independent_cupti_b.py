"""Bind a small B controller to reviewed Stage A. Never builds or runs native."""
import argparse
import hashlib
import json
from pathlib import Path,PureWindowsPath
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]
A_COMMIT='cedd70610588d4d5691c5a86cbcb923ef8ea6433'
A_SHA='71ff920f60e1fd27ec09f7f781c1f4c716e621019e11256c8479447d004decbf'
RECEIPT_SHA='67f02b575aa4ce37cdcdc9c861e1149a1e960d5d33b730d9983a541ae7877fb0'


def digest(data):return hashlib.sha256(data).hexdigest()


def build(output,static_archive,adjudication):
    from scripts.independent_cupti_b import package_index
    archive=Path(static_archive);review=json.loads(Path(adjudication).read_text(encoding='utf8'))
    assert digest(archive.read_bytes())==A_SHA and review['archive_sha256']==A_SHA
    assert review['verdict']=='PASS_STAGE_A_ONLY' and review['execution_commit']==A_COMMIT
    assert review['reviewed_receipt_sha256']==RECEIPT_SHA
    def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
    commit=git('rev-parse','HEAD').decode().strip();out=Path(output);out.mkdir(parents=True,exist_ok=False)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        receipt=z.read('receipt.json');index=z.read('artifact_manifest.json')
        assert digest(receipt)==RECEIPT_SHA and digest(index)==review['manifest_sha256']
        rows=json.loads(index)['files'];by={r['path']:r for r in rows}
        def raw(name):
            value=z.read(name);r=by[name]
            assert len(value)==r['bytes'] and digest(value)==r['sha256'];return value
        a=json.loads(raw('delivery.json'));built=json.loads(raw('build/build.json'))
        runtime=json.loads(raw('runtime_file.json'));cupti=json.loads(raw('cupti_file.json'))
        sources=json.loads(raw('source_bytes.json'));source_by={r['path']:r for r in sources}
        assert a['execution_commit']==a['analysis_commit']==A_COMMIT
        assert digest(raw('build/build.json'))==review['build_sha256']
        assert runtime['sha256']==review['runtime_sha256'] and cupti['sha256']==review['cupti_sha256']
        assert review['micro_binary'] in built['binary_files']
        assert digest(raw('build/micro.exe'))==review['micro_binary']['sha256']
        (out/'reviewed_a_receipt.json').write_bytes(receipt)
        (out/'reviewed_a_manifest.json').write_bytes(index)
    helper_rows=[]
    for original,name in [('scripts/independent_cupti_stage.py','reviewed_stage.py'),
                          ('scripts/memset_micro.py','micro_support.py')]:
        data=git('show',A_COMMIT+':'+original);r=source_by[original]
        assert len(data)==r['bytes'] and digest(data)==r['sha256']
        (out/name).write_bytes(data);helper_rows.append(dict(path=name,bytes=len(data),sha256=digest(data)))
    control=[]
    for original,name in [('scripts/independent_cupti_b.py','independent_cupti_b.py'),
                          ('scripts/run_independent_cupti_b.ps1','run_independent_cupti_b.ps1')]:
        data=git('show',commit+':'+original);assert (ROOT/original).read_bytes()==data
        (out/name).write_bytes(data);control.append(dict(path=name,bytes=len(data),sha256=digest(data)))
    cfg=dict(schema_version='independent-cupti-stage-b/0.1.0',controller_commit=commit,
        native_commit=A_COMMIT,analysis_commit=A_COMMIT,reviewed_a_receipt_sha256=RECEIPT_SHA,
        a_manifest_sha256=review['manifest_sha256'],a_root=str(PureWindowsPath(built['micro']).parent.parent),
        server_root=a['server_root'],build_sha256=review['build_sha256'],runtime_sha256=review['runtime_sha256'],
        cupti_sha256=review['cupti_sha256'],micro_binary=review['micro_binary'],python=a['python'],
        python_version=a['python_version'],gpu_uuid=a['gpu_uuid'],temporary_required_bytes=2**31,
        timeout_seconds=120,micro_process_budget=1,profile_budget=0,model_process_budget=0,
        helper_files=helper_rows,controller_sources=control,controller_sha256=control[0]['sha256'],
        reviewed_a_archive=dict(file=archive.name,bytes=archive.stat().st_size,sha256=A_SHA),
        automatic_retry=False,automatic_cleanup=False,A_COE_admission='NOT_ASSESSED',pytorch_coverage='NOT_ASSESSED')
    (out/'delivery.json').write_text(json.dumps(cfg,indent=2),encoding='utf8')
    files=[dict(path=p.name,bytes=p.stat().st_size,sha256=digest(p.read_bytes())) for p in sorted(out.iterdir())]
    (out/'package_manifest.json').write_text(json.dumps(dict(schema_version='independent-cupti-b-package/0.1.0',files=files),indent=2),encoding='utf8')
    manifest=package_index(out);result=out.with_suffix('.zip')
    with zipfile.ZipFile(result,'x',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(out.iterdir()):z.write(p,p.name)
    with zipfile.ZipFile(result) as z:
        assert z.testzip() is None and set(z.namelist())=={p.name for p in out.iterdir()}
        assert len(z.namelist())==len(set(n.casefold() for n in z.namelist()))
        for r in files:assert digest(z.read(r['path']))==r['sha256']
    return dict(controller_commit=commit,native_commit=A_COMMIT,analysis_commit=A_COMMIT,zip=str(result),
        bytes=result.stat().st_size,sha256=digest(result.read_bytes()),manifest_sha256=manifest,
        launcher_sha256=control[1]['sha256'],controller_sha256=control[0]['sha256'],
        return_zip=str(PureWindowsPath(a['server_root'])/'transfer'/('independent_cupti_'+commit[:12]+'_b_once.zip')))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('output','static-archive','adjudication'):p.add_argument('--'+name,required=True,type=Path)
    a=p.parse_args();print(json.dumps(build(a.output,a.static_archive,a.adjudication),indent=2))


if __name__=='__main__':main()
