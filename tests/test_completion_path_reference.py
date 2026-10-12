"""Archive-backed C0 reuse is not batch resume or a role upgrade."""
import csv,hashlib,io,json,zipfile
from pathlib import Path
import pytest
from exposedpath.gate8_isolated_preflight import sha,write_new
@pytest.fixture
def ref():
    import importlib
    return importlib.import_module('scripts.completion_path_reference')


def archive(tmp_path,mutation=None):
    contents={'sample.txt':b'original'}
    rows=[dict(path=k,bytes=len(v),sha256=hashlib.sha256(v).hexdigest()) for k,v in contents.items()]
    if mutation=='hash':rows[0]['sha256']='0'*64
    text=io.StringIO();w=csv.DictWriter(text,fieldnames=['path','bytes','sha256']);w.writeheader();w.writerows(rows)
    contents['artifact_sha256.csv']=text.getvalue().encode()
    if mutation=='extra':contents['extra.txt']=b'unlisted'
    if mutation=='escape':contents['../escape']=b'escape'
    path=tmp_path/'source.zip'
    with zipfile.ZipFile(path,'x') as z:
        for k,v in contents.items():z.writestr(k,v)
    metadata=dict(archive_bytes=path.stat().st_size,archive_sha256=sha(path),
        archive_manifest_sha256=hashlib.sha256(contents['artifact_sha256.csv']).hexdigest())
    return path,metadata


def test_reference_archive_extracts_exact_verified_bytes(tmp_path,ref):
    path,metadata=archive(tmp_path)
    root=ref.extract_reference(path,metadata,tmp_path/'new')
    assert (root/'sample.txt').read_bytes()==b'original'
    assert path.is_file()


@pytest.mark.parametrize('damage',['hash','extra','escape','source','manifest'])
def test_reference_rejects_source_hash_scope_and_coverage_conflicts(tmp_path,damage,ref):
    path,metadata=archive(tmp_path,damage)
    if damage=='source':metadata['archive_sha256']='0'*64
    if damage=='manifest':metadata['archive_manifest_sha256']='0'*64
    with pytest.raises(ValueError):ref.extract_reference(path,metadata,tmp_path/'new')


@pytest.mark.parametrize('bytes_,expected',[(b'a\nb\n',True),(b'a\r\nb\r\n',True),(b'a\nbAD\n',False),(None,False)])
def test_current_measurement_bytes_not_normalized_or_relearned(tmp_path,bytes_,expected,ref):
    root=tmp_path/'code';root.mkdir()
    if bytes_ is not None:(root/'runner.py').write_bytes(bytes_)
    lf=b'a\nb\n';crlf=b'a\r\nb\r\n'
    item=dict(git_sha256=hashlib.sha256(lf).hexdigest(),old_runtime_sha256=hashlib.sha256(crlf).hexdigest(),
        representations=[dict(bytes=len(v),sha256=hashlib.sha256(v).hexdigest()) for v in (lf,crlf)])
    if expected:
        assert ref.check_sources(root,{'runner.py':item},{'tree_hashes':{'runner.py':item['old_runtime_sha256']}})['runner.py']['matched']
    else:
        with pytest.raises(ValueError):ref.check_sources(root,{'runner.py':item},{'tree_hashes':{'runner.py':item['old_runtime_sha256']}})


def test_unbound_old_runtime_source_cannot_be_replaced_by_current_bytes(tmp_path,ref):
    p=tmp_path/'runner.py';p.write_bytes(b'current')
    item=dict(git_sha256=sha(p),old_runtime_sha256=sha(p),representations=[dict(bytes=7,sha256=sha(p))])
    with pytest.raises(ValueError):ref.check_sources(tmp_path,{'runner.py':item},{'tree_hashes':{'runner.py':'0'*64}})
