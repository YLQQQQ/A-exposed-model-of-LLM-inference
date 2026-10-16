"""Deployment guards and receipts, with explicit CPU process/build boundaries."""
import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest


def api():return importlib.import_module('scripts.memset_micro')


def test_nonzero_cpu_process_preserves_original_output_exit_and_receipt(tmp_path):
    m=api()
    with pytest.raises(ValueError,match='COMMAND_EXIT'):
        m.command([sys.executable,'-c','raise RuntimeError("original CPU failure")'],tmp_path,tmp_path/'fail')
    p=json.loads((tmp_path/'fail.process.json').read_text())
    assert p['exit_code']==1 and p['timed_out'] is False
    assert b'original CPU failure' in (tmp_path/'fail.stderr').read_bytes()


def test_spawn_error_also_writes_exit_record_without_masking_oserror(tmp_path):
    m=api()
    with pytest.raises(OSError):m.command([str(tmp_path/'missing.exe')],tmp_path,tmp_path/'missing')
    p=json.loads((tmp_path/'missing.process.json').read_text())
    assert p['status']=='SPAWN_FAILED' and p['exit_code'] is None and p['error_type']=='FileNotFoundError'


def test_binding_missing_duplicate_escape_and_tamper_are_not_self_certified(tmp_path):
    m=api();p=tmp_path/'file.txt';p.write_bytes(b'fixed')
    rows=[dict(path='file.txt',bytes=5,sha256=m.sha(p))]
    m.verify_rows(tmp_path,rows)
    for changed,reason in [([], 'EMPTY_INDEX'),(rows*2,'DUPLICATE_PATH'),
        ([dict(rows[0],path='../file.txt')],'PATH'),([dict(rows[0],path='missing')],'FILE_MISSING')]:
        with pytest.raises(ValueError,match=reason):m.verify_rows(tmp_path,changed)
    p.write_bytes(b'wrong')
    with pytest.raises(ValueError,match='FILE_HASH'):m.verify_rows(tmp_path,rows)


def test_no_collection_from_default_or_old_review_receipt(tmp_path):
    m=api();a=tmp_path/'static';a.mkdir();p=a/'receipt.json'
    v=dict(status='STATIC_READY_FOR_REVIEW',execution_commit='a'*40,phase='A',
           package_index_sha256='b'*64,build_sha256='c'*64)
    m.write(p,v)
    with pytest.raises(ValueError,match='REVIEWED_STATIC_HASH'):m.check_reviewed_static(a,'0'*64,'a'*40,'b'*64)
    with pytest.raises(ValueError,match='STATIC_BINDING'):m.check_reviewed_static(a,m.sha(p),'d'*40,'b'*64)


def test_archive_refuses_unknown_descendants_and_keeps_partial(tmp_path):
    m=api();out=tmp_path/'evidence';out.mkdir()
    m.write(out/'collector.process.json',dict(status='BLOCKED',descendant_exit_status='UNKNOWN_STOP_AND_INSPECT_NO_RETRY'))
    with pytest.raises(ValueError,match='UNKNOWN_WRITER'):m.pack(out,tmp_path/'return.zip')
    assert (out/'collector.process.json').is_file() and not (tmp_path/'return.zip').exists()


def test_safe_pack_has_complete_index_and_does_not_modify_source(tmp_path):
    import zipfile
    m=api();out=tmp_path/'new';out.mkdir();(out/'receipt.json').write_bytes(b'{}')
    archive=tmp_path/'return.zip';m.pack(out,archive)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        rows=json.loads(z.read('artifact_manifest.json'))['files']
        assert {v['path'] for v in rows}=={'receipt.json'}
    with pytest.raises(ValueError,match='ARCHIVE_EXISTS'):m.pack(out,archive)


@pytest.mark.parametrize('low_tmp',[False,True])
def test_resources_check_both_temp_volumes_once_not_historical_census(tmp_path,monkeypatch,low_tmp):
    from types import SimpleNamespace
    from scripts import coe_startup_storage as storage
    m=api();out=tmp_path/'out';temp1=tmp_path/'temp1';temp2=tmp_path/'temp2'
    for p in (out,temp1,temp2):p.mkdir()
    monkeypatch.setenv('TEMP',str(temp1));monkeypatch.setenv('TMP',str(temp2));monkeypatch.delenv('TMPDIR',raising=False)
    seen=[]
    monkeypatch.setattr(storage,'volume_identity',lambda p:'V2' if p==temp2 else 'V1')
    def usage(p):
        seen.append(p)
        return SimpleNamespace(free=1 if low_tmp and p==temp2 else 2**30)
    monkeypatch.setattr(m.shutil,'disk_usage',usage)
    if low_tmp:
        with pytest.raises(ValueError,match='FREE_SPACE'):m.resources(out,tmp_path/'return.zip')
    else:
        result=m.resources(out,tmp_path/'return.zip')
        assert len(result['volumes'])==2 and len(seen)==2
        assert result['historical_ylq_total_bytes'] is None


def test_pinned_header_subset_avoids_unneeded_long_docs_but_rejects_zip_escape(tmp_path):
    import zipfile
    m=api();zpath=tmp_path/'headers.zip'
    with zipfile.ZipFile(zpath,'w') as z:
        z.writestr('root/include/header.h',b'exact header')
        z.writestr('root/docs/'+('long_'*70)+'.html',b'not needed')
    m.extract(zpath,tmp_path/'good',prefix='root/include/')
    assert (tmp_path/'good/header.h').read_bytes()==b'exact header'
    assert not (tmp_path/'good/root').exists()
    with zipfile.ZipFile(tmp_path/'bad.zip','w') as z:z.writestr('../escape',b'bad')
    with pytest.raises(ValueError,match='ZIP_PATH'):m.extract(tmp_path/'bad.zip',tmp_path/'bad',prefix='root/include/')


@pytest.mark.parametrize('argv,phase',[([], 'A'),(['-CollectReviewedMicro','-ReviewedStaticReceiptSHA256','a'*64],'B')])
def test_real_ps51_default_and_explicit_switch_dispatch_only(tmp_path,argv,phase):
    # The production PS entry invokes this CPU Python boundary, NOT any native
    # micro/collector. Actual deployment/build replay is a separate local audit.
    import shutil,os
    m=api();root=Path(__file__).resolve().parents[1]
    script=tmp_path/'run.ps1';shutil.copyfile(root/'scripts/run_memset_micro.ps1',script)
    driver=tmp_path/'memset_micro.py'
    driver.write_text('import json,sys\nfrom pathlib import Path\nPath(sys.argv[2]).joinpath("dispatch.json").write_text(json.dumps(sys.argv[1:]))\n',encoding='utf8')
    cfg=dict(python=sys.executable,bootstrap_sha256=m.sha(driver))
    m.write(tmp_path/'delivery.json',cfg)
    ps='C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe'
    env=os.environ.copy()
    # The host shell is PS7. Do not inject its incompatible module search path
    # into this explicit Windows PowerShell5.1 subprocess.
    env['PSModulePath']=str(Path(ps).parent/'Modules')
    done=subprocess.run([ps,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(script),*argv],env=env,capture_output=True,timeout=20)
    assert done.returncode==0,done.stdout+done.stderr
    args=json.loads((tmp_path/'dispatch.json').read_text())
    assert args[0]==('stage-a' if phase=='A' else 'stage-b')
    assert ('a'*64 in args)==(phase=='B')
