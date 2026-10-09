"""Archive first. Plan exact redundant files only after external batch review.

No deletion in Python. Mandatory Raw, reports and accepted outputs stay intact.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile


def require(ok,reason):
    if not ok:raise ValueError('RETENTION_'+reason)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def quiescent(root):
    root=Path(root)
    require(not (root/'.active').exists(),'ACTIVE_WRITER')
    for p in root.rglob('process.json'):
        v=json.loads(p.read_text(encoding='utf-8-sig'))
        require(v.get('descendant_exit_status')!='UNKNOWN_STOP_AND_INSPECT_NO_RETRY','UNKNOWN_WRITER')
        require(v.get('status') not in ('RUNNING','STARTING'),'ACTIVE_WRITER')
        # Positive liveness check only for recorded launchers, not name-wide.
        if v.get('pid') and __import__('os').name=='nt':
            import ctypes
            from ctypes import wintypes
            k=ctypes.WinDLL('kernel32',use_last_error=True)
            k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
            k.OpenProcess.restype=wintypes.HANDLE
            k.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD]
            k.CloseHandle.argtypes=[wintypes.HANDLE]
            handle=k.OpenProcess(0x100000,False,int(v['pid']))
            if handle:
                try:require(k.WaitForSingleObject(handle,0)==0,'LIVE_RECORDED_WRITER_OR_PID_REUSE')
                finally:k.CloseHandle(handle)
            else:require(ctypes.get_last_error()==87,'WRITER_QUERY_FAILED')


def files(root):
    root=Path(root).resolve();result=[]
    for p in sorted(root.rglob('*')):
        # Python 3.11 has no Path.is_junction(); reject all Windows reparse
        # entries through lstat, including junctions, without following them.
        require(not p.is_symlink() and not (getattr(p.lstat(),'st_file_attributes',0)&0x400),'REPARSE_PATH')
        require(p.resolve().is_relative_to(root),'PATH_OUTSIDE_ROOT')
        if p.is_file() and p!=root/'artifact_sha256.csv':result.append(p)
    return result


def pack(root,archive):
    root,archive=Path(root).resolve(),Path(archive).resolve()
    quiescent(root);require(not archive.is_relative_to(root),'ARCHIVE_INSIDE_INPUT')
    require(not archive.exists(),'ARCHIVE_EXISTS')
    pending=archive.with_suffix('.pending.zip');require(not pending.exists(),'PARTIAL_ARCHIVE_EXISTS')
    listing=files(root);index=root/'artifact_sha256.csv'
    require(not index.exists(),'MANIFEST_EXISTS_NO_OVERWRITE')
    with index.open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['path','bytes','sha256']);w.writeheader()
        for p in listing:w.writerow(dict(path=p.relative_to(root).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
    quiescent(root)
    with zipfile.ZipFile(pending,'x',zipfile.ZIP_DEFLATED) as z:
        for p in [*listing,index]:z.write(p,p.relative_to(root).as_posix())
    verify(root,pending)
    pending.replace(archive)
    return dict(zip_bytes=archive.stat().st_size,zip_sha256=sha(archive),manifest_sha256=sha(index))


def verify(root,archive):
    root,archive=Path(root).resolve(),Path(archive)
    quiescent(root)
    with zipfile.ZipFile(archive) as z:
        names=z.namelist();require(len(names)==len(set(names)),'DUPLICATE_ARCHIVE_MEMBER')
        require(all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts
            and '\\' not in n and ':' not in n for n in names),'ARCHIVE_PATH')
        rows=list(csv.DictReader(z.read('artifact_sha256.csv').decode('utf-8-sig').splitlines()))
        require(rows and len({r['path'] for r in rows})==len(rows),'MANIFEST')
        require(set(names)=={r['path'] for r in rows}|{'artifact_sha256.csv'},'MANIFEST_COVERAGE')
        require({p.relative_to(root).as_posix() for p in files(root)}=={r['path'] for r in rows},'LOCAL_COVERAGE')
        require(z.read('artifact_sha256.csv')==(root/'artifact_sha256.csv').read_bytes(),'MANIFEST_BYTES')
        for r in rows:
            p=(root/r['path']).resolve();require(p.is_relative_to(root),'PATH_OUTSIDE_ROOT')
            require(p.is_file() and p.stat().st_size==int(r['bytes']) and sha(p)==r['sha256'],'LOCAL_BYTES')
            h=hashlib.sha256();size=0
            with z.open(r['path']) as f:
                for b in iter(lambda:f.read(1024*1024),b''):h.update(b);size+=len(b)
            require(size==int(r['bytes']) and h.hexdigest()==r['sha256'],'ARCHIVE_BYTES')
    return rows


def make_cleanup_plan(root,archive,receipt):
    root,archive=Path(root).resolve(),Path(archive).resolve()
    require(receipt.get('status')=='BATCH_REVIEWED_ARCHIVE_VERIFIED' and bool(receipt.get('review_id')),'REVIEW_REQUIRED')
    require(receipt.get('archive_sha256')==sha(archive),'ARCHIVE_IDENTITY')
    rows=verify(root,archive)
    # Only reconstructible intermediates explicitly named here; final A/B,
    # domains/quality/provenance, Raw/SQLite, manifests and statistics retained.
    canonical_names={'nvtx.jsonl.gz','cuda_api.jsonl.gz','cuda_sync.jsonl.gz','device_activity.jsonl.gz',
        'cuda_event.jsonl.gz','context.jsonl.gz','stream.jsonl.gz','diagnostic.jsonl.gz'}
    candidates=[r for r in rows if '/collection/analyzed/canonical/' in r['path'] and
        PurePosixPath(r['path']).name in canonical_names
        or r['path'].endswith('/collection/analyzed/projection/scope.json')]
    return dict(schema_version='gate13-reviewed-cleanup-plan/0.1',root=str(root),archive=str(archive),
        archive_sha256=sha(archive),review=receipt,files=candidates,automatic_delete=False,
        scope='EXACT_ARCHIVED_REBUILDABLE_INTERMEDIATES_ONLY',raw_delete=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['pack','plan']);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--archive',type=Path,required=True);p.add_argument('--review',type=Path)
    p.add_argument('--plan-output',type=Path)
    a=p.parse_args()
    if a.action=='pack':print(json.dumps(pack(a.root,a.archive)));return 0
    require(a.review is not None and a.plan_output is not None,'REVIEW_REQUIRED')
    value=make_cleanup_plan(a.root,a.archive,json.loads(a.review.read_text(encoding='utf-8-sig')))
    with a.plan_output.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2)
    print(json.dumps(dict(plan=str(a.plan_output),files=len(value['files']),automatic_delete=False)))
    return 0


if __name__=='__main__':raise SystemExit(main())
