"""Startup resources, not a historical directory census. CPU-only OS doubles."""
from pathlib import Path
from types import SimpleNamespace
import pytest


def fixture(tmp_path, monkeypatch):
    from scripts import coe_startup_storage as m
    out=tmp_path/'new-output';out.mkdir()
    temporary=tmp_path/'temporary';temporary.mkdir()
    archive=tmp_path/'archive'/'new.zip';archive.parent.mkdir()
    monkeypatch.setattr(m,'volume_identity',lambda p:'CPU-VOLUME-1')
    calls=[]
    def free(p):
        calls.append(str(p))
        return SimpleNamespace(free=12884901888,total=100000000000)
    monkeypatch.setattr(m.shutil,'disk_usage',free)
    return m,out,temporary,archive,calls


def test_shared_volume_is_queried_once_and_history_unknown_is_not_failure(tmp_path,monkeypatch):
    m,out,temp,archive,calls=fixture(tmp_path,monkeypatch)
    r=m.check(out,[temp],archive)
    assert r['status']=='STARTUP_RESOURCES_READY' and len(calls)==1
    assert len(r['locations'])==3 and len(r['volumes'])==1
    assert r['historical_ylq_total_bytes'] is None and r['long_term_status']=='UNKNOWN_NOT_PROVEN'
    assert r['long_term_target_exclusive_bytes']==50000000000
    assert r['collection_authorized'] is False
    assert not archive.exists() and not list(out.iterdir()) and not list(temp.iterdir())


def test_different_volumes_are_not_added_together(tmp_path,monkeypatch):
    m,out,temp,archive,calls=fixture(tmp_path,monkeypatch)
    monkeypatch.setattr(m,'volume_identity',lambda p:str(p))
    r=m.check(out,[temp],archive)
    assert r['status']=='STARTUP_RESOURCES_READY' and len(calls)==3
    assert all(v['free_bytes']==12884901888 for v in r['volumes'])


@pytest.mark.parametrize('damage,reason',[
    ('low','FREE_SPACE_INSUFFICIENT'),('query','FREE_SPACE_UNKNOWN'),
    ('volume','VOLUME_IDENTITY_UNKNOWN'),('write','PATH_NOT_WRITABLE'),
    ('archive_exists','ARCHIVE_ALREADY_EXISTS'),('missing_temp','TEMPORARY_DIRECTORY_MISSING')])
def test_resource_failures_keep_observations_and_refuse(tmp_path,monkeypatch,damage,reason):
    m,out,temp,archive,calls=fixture(tmp_path,monkeypatch)
    if damage=='low':monkeypatch.setattr(m.shutil,'disk_usage',lambda p:SimpleNamespace(free=12884901887,total=20000000000))
    elif damage=='query':monkeypatch.setattr(m.shutil,'disk_usage',lambda p:(_ for _ in ()).throw(OSError('CPU query failed')))
    elif damage=='volume':monkeypatch.setattr(m,'volume_identity',lambda p:(_ for _ in ()).throw(OSError('CPU identity unavailable')))
    elif damage=='write':monkeypatch.setattr(m,'write_probe',lambda p:(_ for _ in ()).throw(PermissionError('CPU write denied')))
    elif damage=='archive_exists':archive.write_bytes(b'preserve')
    else:temp.rmdir()
    r=m.check(out,[temp],archive)
    assert r['status']=='STARTUP_RESOURCES_BLOCKED'
    assert reason in [v['reason'] for v in r['errors']]
    assert r['historical_ylq_total_bytes'] is None and not r['collection_authorized']
    if damage=='query':assert r['volumes'][0]['free_bytes'] is None
    if damage=='archive_exists':assert archive.read_bytes()==b'preserve'


def test_cli_writes_failure_receipt_without_overwriting_it(tmp_path,monkeypatch):
    m,out,temp,archive,calls=fixture(tmp_path,monkeypatch)
    import json
    monkeypatch.setattr(m.shutil,'disk_usage',lambda p:SimpleNamespace(free=0,total=1))
    receipt=out/'storage.json'
    args=['--output-directory',str(out),'--temporary-directory',str(temp),'--archive',str(archive),'--receipt',str(receipt)]
    assert m.main(args)==2
    assert json.loads(receipt.read_text())['status']=='STARTUP_RESOURCES_BLOCKED'
    before=receipt.read_bytes()
    with pytest.raises(FileExistsError):m.main(args)
    assert receipt.read_bytes()==before


def test_actual_windows_volume_identity_deduplicates_local_participating_paths(tmp_path):
    import os
    if os.name!='nt':pytest.skip('actual Windows volume API; not a Linux qualification')
    from scripts import coe_startup_storage as m
    out=tmp_path/'out';out.mkdir();temp=tmp_path/'temp';temp.mkdir()
    archive=tmp_path/'archive'/'new.zip';archive.parent.mkdir()
    r=m.check(out,[temp],archive)
    assert len(r['volumes'])==1 and r['volumes'][0]['status']=='OBSERVED'
    assert r['volumes'][0]['identity'].startswith('\\\\?\\volume{')
    assert not any(e['reason'] not in {'FREE_SPACE_INSUFFICIENT'} for e in r['errors'])
