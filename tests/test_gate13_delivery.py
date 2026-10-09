"""CPU delivery controls only; no target/CUDA/collector qualification."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import shutil
import zipfile

import pytest

from scripts import gate13_formal_batch as batch
from scripts import gate13_retention as retention


def release():
    c=json.loads(Path('docs/v1_4_1/gate12_freeze_candidate_v0_1.json').read_text(encoding='utf-8'))
    return dict(protocol=c['protocol'],approval=dict(version='exposedpath-protocol-approval/0.1.0',
        status='SIGNED',protocol_sha256=c['protocol_sha256'],authority='HUMAN_USER',
        signed_at='2026-10-09T00:00:00Z',approval_id='SYNTHETIC_CPU_ONLY',scope='LIMITED_ROUTE_A',budget_approved=True))


def fake(binding,path):
    path.mkdir();(path/'actual.json').write_text(json.dumps(binding))
    return dict(status='RUN_COMPLETE_PENDING_REVIEW',binding=binding,
                index_entry={'output_dir':str(path.name)})


def paired(a,b,root):
    assert a['binding']['pair_id']==b['binding']['pair_id']
    return dict(pair_id=a['binding']['pair_id'],status='PAIR_COMPLETE_PENDING_REVIEW')


def test_schedule_executes_exactly_sixty_slots_thirty_pairs_and_no_continuation(tmp_path):
    seen=[]
    def execute(b,p):seen.append((b['block'],b['condition'],b['pass_id']));return fake(b,p)
    result=batch.run_batch(tmp_path/'batch',release(),'cpu',execute,paired,declared_at='2026-10-09T00:00:01Z')
    assert result['status']=='FORMAL_BATCH_COLLECTED_PENDING_REVIEW'
    assert len(seen)==60 and len(result['pairs'])==30
    assert seen[:4]==[(1,'G32','pass0'),(1,'G32','pass1'),(1,'N0','pass1'),(1,'N0','pass0')]
    assert seen[-2:]==[(6,'G32','pass1'),(6,'G32','pass0')]
    with pytest.raises(FileExistsError):batch.run_batch(tmp_path/'batch',release(),'cpu',execute,paired,declared_at='2026-10-09T00:00:01Z')
    assert len(seen)==60


def test_hard_failure_stops_once_preserves_partial_and_not_run(tmp_path):
    calls=[]
    def execute(b,p):
        calls.append(b['run_id'])
        if len(calls)==3:
            p.mkdir();(p/'partial').write_bytes(b'raw');raise ValueError('IDENTITY_CONFLICT')
        return fake(b,p)
    result=batch.run_batch(tmp_path/'batch',release(),'cpu',execute,paired,declared_at='2026-10-09T00:00:01Z')
    assert len(calls)==3 and result['status']=='BLOCKED'
    assert result['runs'][2]['status']=='BLOCKED'
    assert all(r['status']=='NOT_RUN' for r in result['runs'][3:])
    assert (tmp_path/'batch'/calls[2]/'partial').read_bytes()==b'raw'
    assert not (tmp_path/'batch'/'formal_index.json').exists()


@pytest.mark.parametrize('change',['unsigned','wrong_hash','stale'])
def test_invalid_approval_never_reaches_executor(tmp_path,change):
    r=release()
    if change=='unsigned':r['approval']['status']='PENDING'
    if change=='wrong_hash':r['approval']['protocol_sha256']='0'*64
    when='2026-10-08T00:00:00Z' if change=='stale' else '2026-10-09T00:00:01Z'
    with pytest.raises(ValueError):batch.run_batch(tmp_path/'batch',r,'cpu',lambda *_:pytest.fail('executed'),paired,declared_at=when)
    assert not (tmp_path/'batch').exists()


def test_wrong_actual_binding_stops_batch(tmp_path):
    def execute(b,p):
        r=fake(b,p);r['binding']=deepcopy(b);r['binding']['condition']='G512';return r
    r=batch.run_batch(tmp_path/'batch',release(),'cpu',execute,paired,declared_at='2026-10-09T00:00:01Z')
    assert r['status']=='BLOCKED' and all(x['status']=='NOT_RUN' for x in r['runs'][1:])


def test_archive_is_verified_and_cleanup_proposes_only_exact_redundant_files(tmp_path):
    root=tmp_path/'run';root.mkdir();(root/'capture.nsys-rep').write_bytes(b'raw')
    d=root/'runs/x/collection/analyzed/canonical';d.mkdir(parents=True);(d/'cuda_api.jsonl.gz').write_bytes(b'canonical')
    (root/'receipt.json').write_text('{"status":"DONE"}')
    archive=tmp_path/'sealed.zip';retention.pack(root,archive)
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    identity=hashlib.sha256(archive.read_bytes()).hexdigest()
    receipt=dict(status='BATCH_REVIEWED_ARCHIVE_VERIFIED',archive_sha256=identity,review_id='USER_CPU_FIXTURE')
    plan=retention.make_cleanup_plan(root,archive,receipt)
    assert [x['path'] for x in plan['files']]==['runs/x/collection/analyzed/canonical/cuda_api.jsonl.gz']
    assert plan['files'][0]['sha256']==hashlib.sha256(b'canonical').hexdigest()
    assert plan['automatic_delete'] is False and (root/'capture.nsys-rep').exists()


@pytest.mark.parametrize('failure',['active','archive_changed','file_changed','no_review','unlisted'])
def test_archive_and_cleanup_reject_live_changed_unreviewed_inputs(tmp_path,failure):
    root=tmp_path/'run';root.mkdir();(root/'receipt.json').write_bytes(b'{}')
    archive=tmp_path/'sealed.zip';retention.pack(root,archive)
    receipt=dict(status='BATCH_REVIEWED_ARCHIVE_VERIFIED',archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),review_id='CPU')
    if failure=='active':(root/'.active').write_text('writer')
    if failure=='archive_changed':archive.write_bytes(b'bad')
    if failure=='file_changed':(root/'receipt.json').write_bytes(b'changed')
    if failure=='no_review':receipt['status']='PENDING'
    if failure=='unlisted':(root/'extra').write_bytes(b'unlisted')
    with pytest.raises((ValueError,zipfile.BadZipFile)):
        retention.make_cleanup_plan(root,archive,receipt)


def test_timeout_unknown_descendant_prevents_packaging(tmp_path):
    root=tmp_path/'run';root.mkdir();(root/'process.json').write_text(json.dumps(dict(descendant_exit_status='UNKNOWN_STOP_AND_INSPECT_NO_RETRY')))
    with pytest.raises(ValueError,match='WRITER'):retention.pack(root,tmp_path/'sealed.zip')
    assert not (tmp_path/'sealed.zip').exists()


def test_nested_static_manifest_is_archived_not_silently_excluded(tmp_path):
    root=tmp_path/'run';(root/'static').mkdir(parents=True)
    (root/'static/artifact_sha256.csv').write_bytes(b'original static manifest')
    archive=tmp_path/'sealed.zip';retention.pack(root,archive)
    with zipfile.ZipFile(archive) as z:
        assert z.read('static/artifact_sha256.csv')==b'original static manifest'


@pytest.mark.parametrize('condition',['G32','N16'])
def test_real_signed_producer_files_feed_delivery_pair_and_reject_identity(tmp_path,monkeypatch,condition):
    # Existing qualified CPU file fixtures, not a hand-filled consumer table.
    from test_gate12_formal import binding
    from test_gate11_pilot_files import pair_files
    b0=binding(condition,'pass0');b1=binding(condition,'pass1')
    items=pair_files(tmp_path,monkeypatch,condition,[b0,b1])
    # The existing fixture creates a synthetic source/commit-bound CPU release,
    # distinct from the seed template. Use its actual declared binding; this
    # test concerns pair consumption, not a production permission to rebind.
    rows=[dict(binding=json.loads((Path(x['output'])/'diagnostic/manifest.json').read_text())['formal'],
               index_entry=dict(output_dir=Path(x['output']).relative_to(tmp_path).as_posix())) for x in items]
    pair=batch.compare_pair(*rows,tmp_path)
    assert pair['status']=='PAIR_COMPLETE_PENDING_REVIEW'
    assert pair['input_tokens']==32 and len(pair['token_ids'])==2
    assert set(pair['signed_difference_ns'])=={'full_request','prefill','decode'}
    damaged=deepcopy(rows[1]);damaged['binding']['run_id']='wrong-run'
    with pytest.raises(ValueError,match='PAIR_ACTUAL'):batch.compare_pair(rows[0],damaged,tmp_path)


@pytest.mark.skipif(os.name!='nt',reason='Windows PowerShell delivery adapter')
@pytest.mark.parametrize('action',['dry','delete','changed_archive'])
def test_powershell_cleanup_is_review_bound_file_only_and_receipted(tmp_path,action):
    root=tmp_path/'run';d=root/'runs/x/collection/analyzed/canonical';d.mkdir(parents=True)
    item=d/'cuda_api.jsonl.gz';item.write_bytes(b'rebuildable')
    raw=root/'capture.nsys-rep';raw.write_bytes(b'irreplaceable')
    archive=tmp_path/'sealed.zip';retention.pack(root,archive)
    review=dict(status='BATCH_REVIEWED_ARCHIVE_VERIFIED',review_id='CPU_ONLY',archive_sha256=retention.sha(archive))
    plan=retention.make_cleanup_plan(root,archive,review);path=tmp_path/'plan.json'
    path.write_text(json.dumps(plan),encoding='utf-8')
    if action=='changed_archive':archive.write_bytes(b'changed')
    powershell=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
    args=[str(powershell),'-NoProfile','-File','scripts/cleanup_gate13_reviewed.ps1','-PlanPath',str(path)]
    if action!='dry':args.append('-DeleteReviewedFiles')
    result=subprocess.run(args,capture_output=True)
    assert (result.returncode==0)==(action!='changed_archive')
    assert item.exists()==(action!='delete') and raw.read_bytes()==b'irreplaceable'
    if action=='delete':
        receipt=json.loads(Path(str(path)+'.cleanup_receipt.json').read_text(encoding='utf-8-sig'))
        assert len(receipt['files'])==1 and receipt['files'][0]['deleted'] is True
        assert receipt['recoverable_from_archive'] is True


@pytest.mark.parametrize('damage',[None,'commit','input'])
def test_actual_deployment_cpu_entry_checks_content_without_device_probe(tmp_path,monkeypatch,damage):
    from scripts import gate13_validate_delivery as validator
    from exposedpath import platform_adapter,formal_protocol as formal
    from test_gate12_formal import release as cpu_release
    p,a=cpu_release();root=Path.cwd()
    p['execution_commit']=p['analysis_commit']='b'*40
    a['protocol_sha256']=formal.content_hash(p)
    signed=tmp_path/'signed_release.json';signed.write_text(json.dumps(dict(protocol=p,approval=a)),encoding='utf-8')
    shutil.copyfile('scripts/gate13_formal_batch.py',tmp_path/'gate13_formal_batch.py')
    for name in ('prompt_tokens.json','prompt_512.json','model_sha256.csv'):(tmp_path/name).write_bytes(name.encode())
    c=dict(code_root=str(root),commit='b'*40,batch_id='CPU_ONLY',model_process_budget=60,profile_budget=30,warmup_count=3,
        signed_release_sha256=retention.sha(signed),prompt_sha256=retention.sha(tmp_path/'prompt_tokens.json'),
        prompt_512_sha256=retention.sha(tmp_path/'prompt_512.json'),inventory_sha256=retention.sha(tmp_path/'model_sha256.csv'))
    if damage=='commit':c['commit']='c'*40
    if damage=='input':(tmp_path/'prompt_tokens.json').write_bytes(b'wrong')
    config=tmp_path/'delivery.json';config.write_text(json.dumps(c),encoding='utf-8')
    monkeypatch.setattr(sys,'argv',['validator','--config',str(config)])
    monkeypatch.setattr(platform_adapter,'git',lambda args:'b'*40 if 'rev-parse' in args else '')
    monkeypatch.setattr(platform_adapter,'cuda_identity_native',lambda *_:pytest.fail('must not query CUDA'))
    if damage is None:assert validator.main()==0
    else:
        with pytest.raises(ValueError):validator.main()


@pytest.mark.skipif(os.name!='nt',reason='Windows junction safety')
def test_cleanup_rejects_root_replaced_with_junction_after_plan(tmp_path):
    root=tmp_path/'run';d=root/'runs/x/collection/analyzed/canonical';d.mkdir(parents=True)
    (d/'cuda_api.jsonl.gz').write_bytes(b'original')
    archive=tmp_path/'sealed.zip';retention.pack(root,archive)
    review=dict(status='BATCH_REVIEWED_ARCHIVE_VERIFIED',review_id='CPU_ONLY',archive_sha256=retention.sha(archive))
    path=tmp_path/'plan.json';path.write_text(json.dumps(retention.make_cleanup_plan(root,archive,review)))
    original=tmp_path/'original';outside=tmp_path/'outside'
    assert root.resolve().is_relative_to(tmp_path.resolve()) and outside.resolve().is_relative_to(tmp_path.resolve())
    root.rename(original);shutil.copytree(original,outside)
    command=Path(os.environ['SystemRoot'])/'System32/cmd.exe'
    made=subprocess.run([str(command),'/d','/c','mklink','/J',str(root),str(outside)],capture_output=True)
    assert made.returncode==0
    powershell=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
    result=subprocess.run([str(powershell),'-NoProfile','-File','scripts/cleanup_gate13_reviewed.ps1',
        '-PlanPath',str(path),'-DeleteReviewedFiles'],capture_output=True)
    assert result.returncode!=0
    assert (outside/'runs/x/collection/analyzed/canonical/cuda_api.jsonl.gz').read_bytes()==b'original'
