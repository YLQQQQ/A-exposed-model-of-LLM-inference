"""Narrow offline publication binding for the unused single-B2 model budget.

The reviewed A proves only its original delivery. A separately reviewed external
publication receipt and an exact Git bundle prove the NEW control version.
Neither a network exception nor a locally computed hash is publication evidence.
"""
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re

VERSION='cupti-batch-publication-repair/0.1.0'
BASE='e358d37f0bcd1b07c4de7a882fabc4d7788f905c'
PUBLISHED='4f2ffc769ac3a42bf08886c3cda09bccde067206'
SCIENCE='c8f3dad152659044691f9ff328498c7a127815ea'
MANIFEST='0aca6463d7c8b76a0ecc6095b9849afac56c9da0e75e95d5f7a7d3a452829634'
PREPARE='d17423afd2422c7843564777f7603d034ff8ed4f03403682a1222592f73d7e16'
A_INDEX='d3b39f51bcfed2e67bd5b60b18cb9ea1a63389cfef2fed2a2d124126cd3821fd'
FAILED_INDEX='2871303480d9dcecd02d4418cdd431262284a0eda175f1a828f2494edbf688cd'
FAILED_RECEIPT='4a3ec695bb63e2e0fff25b5ab9fdb6cf9ed748b3656e76f174163d6731eb826e'


def need(ok,reason):
    if not ok:raise ValueError('BATCH_REPAIR_'+reason)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_bytes())


def profile():
    return dict(schema_version=VERSION,parent_control_commit=BASE,parent_published_main=PUBLISHED,
        parent_manifest_sha256=MANIFEST,reviewed_prepare_sha256=PREPARE,reviewed_prepare_manifest_sha256=A_INDEX,
        failed_manifest_sha256=FAILED_INDEX,failed_receipt_sha256=FAILED_RECEIPT,
        prior_model_budget_consumed=0,remaining_model_process_budget=1,
        policy='PINNED_A_PUBLICATION_PLUS_SEPARATE_NEW_CONTROL_PUBLICATION',automatic_retry=False)


def validate(c):
    need(c.get('repair_profile')==profile(),'PROFILE')
    need(isinstance(c.get('delivery_control_commit'),str) and
        re.fullmatch('[0-9a-f]{40}',c['delivery_control_commit']) and c['delivery_control_commit']!=BASE,'CONTROL_VERSION')


def parent_paths(c):
    transfer=Path(c['server_root'])/'transfer';root=transfer/'coe_batch_L512B2_e358d37f0bcd'
    return dict(root=root,parent_package=transfer/'coe_batch_e358d37f0bcd_delivery',
        static_zip=transfer/(root.name+'_static.zip'),once_zip=transfer/(root.name+'_once.zip'),
        package_zip=transfer/'coe_batch_e358d37f0bcd_delivery.zip')


def no_reparse(p):
    for q in (Path(p),*Path(p).parents):
        need(not q.is_symlink() and not (q.exists() and getattr(q.lstat(),'st_file_attributes',0)&0x400),'REPARSE')


def verify_seal(root,expected,label,count):
    root=Path(root);no_reparse(root);index=root/'artifact_manifest.json'
    need(index.is_file(),label+'_INDEX_MISSING');need(sha(index)==expected,label+'_INDEX_HASH')
    rows=read(index)['files'];need(len(rows)==count,label+'_INDEX_COUNT');seen=set()
    for r in rows:
        n=r['path'];p=PurePosixPath(n)
        need(n and not p.is_absolute() and '..' not in p.parts and '\\' not in n and ':' not in n and
            p.as_posix()==n and n.casefold() not in seen,label+'_PATH')
        seen.add(n.casefold());target=root/n;no_reparse(target)
        need(target.is_file(),label+'_ARTIFACT_MISSING:'+n)
        need(target.stat().st_size==r['bytes'] and sha(target)==r['sha256'],label+'_ARTIFACT_HASH:'+n)
    actual=set()
    for d,dirs,files in os.walk(root,followlinks=False):
        for n in [*dirs,*files]:no_reparse(Path(d)/n)
        actual.update((Path(d)/n).relative_to(root).as_posix().casefold() for n in files)
    need(actual==seen|{'artifact_manifest.json'},label+'_COVERAGE')


def checked_parent(c,m,api,*,paths=None):
    """No subprocess/network. 'paths' is a filesystem adapter used by CPU tests."""
    validate(c);paths=parent_paths(c) if paths is None else paths
    parent=Path(paths['parent_package']);old=Path(paths['root']);prep=old/'prepare'
    need((parent/'package_manifest.json').is_file() and sha(parent/'package_manifest.json')==MANIFEST,'PARENT_PACKAGE_MANIFEST')
    try:api.verify_package_files(parent)
    except (OSError,ValueError) as exc:raise ValueError('BATCH_REPAIR_PARENT_PACKAGE_BYTES:'+str(exc)) from exc
    pc=read(parent/'delivery.json')
    ignored={'delivery_control_commit','control_sources','repair_profile','repair_bundle','package_root','storage_script'}
    canonical=read(Path(c['package_root'])/'delivery.json') if c.get('package_root') else c
    need({k:v for k,v in canonical.items() if k not in ignored}=={k:v for k,v in pc.items() if k not in ignored},'PARENT_CONFIG_CHANGED')
    if c.get('package_root'):
        changed={'cupti_batch_once_delivery.py','cupti_event_b.py','git_materialization.py','run_cupti_batch_once.ps1',
            'README.txt','delivery.json','local_authorization_scope.json'}
        for row in read(parent/'package_manifest.json')['files']:
            if row['path'] not in changed:
                now=Path(c['package_root'])/row['path']
                need(now.is_file() and now.read_bytes()==(parent/row['path']).read_bytes(),'UNCHANGED_COMPONENT:'+row['path'])
    need((prep/'receipt.json').is_file() and sha(prep/'receipt.json')==PREPARE,'A_RECEIPT_HASH')
    verify_seal(prep,A_INDEX,'A',129)
    api.checked_preparation(parent,dict(root=old),pc,m,PREPARE)
    need((prep/'delivery_manifest.json').read_bytes()==(parent/'package_manifest.json').read_bytes(),'A_DELIVERY_MANIFEST')
    r=read(prep/'receipt.json');pub=r['publication']
    need(pub['remote_main']==PUBLISHED and pub['delivery_control_commit']==BASE and
        pub['control_is_published_ancestor'] is True and pub['checkout_changed'] is pub['push_performed'] is False,'A_PUBLICATION')
    need((prep/'published_main.stdout').read_text().split()==[PUBLISHED,'refs/heads/main'],'A_PUBLICATION_REF')
    for i,row in enumerate(pc['control_sources']):
        b=(prep/('published_source_'+str(i)+'.stdout')).read_bytes()
        need(b==(parent/row['path']).read_bytes() and hashlib.sha256(b).hexdigest()==row['sha256'],'A_PUBLISHED_SOURCE')
    processes=[read(p) for p in prep.glob('*.process.json')]
    need(len(processes)==7 and all(p['status']=='EXITED' and p['exit_code']==0 and p['timed_out'] is False for p in processes),'A_PUBLICATION_PROCESS')
    f=old/'once/control_receipt.json'
    need(f.is_file() and sha(f)==FAILED_RECEIPT,'FAILED_ARTIFACT_HASH:once/control_receipt.json')
    verify_seal(old,FAILED_INDEX,'FAILED',140)
    failed=read(f);query=read(old/'once/published_main.process.json')
    need(failed['status']=='BLOCKED' and failed['phase']=='execute' and
        failed['error']=='ValueError:MEMSET_MICRO_COMMAND_EXIT:published_main:128' and
        failed['delivery_control_commit']==BASE and failed['scientific_commit']==SCIENCE and
        failed['actual_model_processes']==0 and failed['actual_cupti_sessions'] is None and
        failed['model_receipt'] is failed['publication'] is None,'FAILED_PRE_MODEL_STATE')
    need(query['status']=='EXITED' and query['exit_code']==128 and query['timed_out'] is False and
        query['argv']==[pc['git'],'ls-remote','https://github.com/YLQQQQ/A-exposed-model-of-LLM-inference','refs/heads/main'],'FAILED_QUERY')
    expected={'control_receipt.json','delivery.json','delivery_manifest.json','published_main.stdout',
        'published_main.stderr','published_main.process.json','startup_resources.json'}
    need({p.name for p in (old/'once').iterdir()}==expected,'FAILED_DISPATCH_OR_EXTRA_ARTIFACT')
    for key,size,digest in [('package_zip',146885,'b5e9190080bb6ac3d9e7be4b357f1f457a6f2698ec0250d91c0b5a8f2b434626'),
        ('static_zip',396343,'d5de969e86f44199d26b06bfc6d3baf41551d1aa8677855943aa1100b01aecf1'),
        ('once_zip',971445,'e7393356fa992633daf3b0136ac317a9c2d3f04b14c746c98ab46c8ba301c4f4')]:
        p=Path(paths[key]);no_reparse(p)
        need(p.is_file() and p.stat().st_size==size and sha(p)==digest,'SEALED_ARCHIVE:'+key)
    return dict(policy=VERSION,parent_A_receipt_sha256=PREPARE,parent_A_manifest_sha256=A_INDEX,
        parent_delivery_manifest_sha256=MANIFEST,historical_publication=pub,
        historical_A_is_not_new_control_publication=True,prior_failed_receipt_sha256=FAILED_RECEIPT,
        prior_actual_model_processes=0,prior_actual_cupti_sessions_original=None,prior_model_dispatch_reached=False,
        old_network_failure_preserved=True,old_evidence_modified=False,remaining_model_process_budget=1)


def check_release_evidence(c,flags):
    validate(c);encoded=flags.get('reviewed_control_publication');expected=flags.get('reviewed_control_publication_sha256')
    need(isinstance(encoded,str) and encoded and isinstance(expected,str) and re.fullmatch('[0-9a-fA-F]{64}',expected),
        'NEW_CONTROL_PUBLICATION_REQUIRED')
    try:raw=base64.b64decode(encoded,validate=True);r=json.loads(raw)
    except (ValueError,UnicodeDecodeError) as exc:raise ValueError('BATCH_REPAIR_NEW_CONTROL_PUBLICATION_FORMAT') from exc
    need(hashlib.sha256(raw).hexdigest()==expected.lower(),'NEW_CONTROL_PUBLICATION_HASH')
    need(r.get('schema_version')=='exposedpath-publication-receipt/0.1.0' and
        r.get('status')=='PUBLISHED_REMOTE_REF_VERIFIED' and
        r.get('repository')=='YLQQQQ/A-exposed-model-of-LLM-inference' and r.get('ref')=='refs/heads/main' and
        r.get('force_used') is False,'NEW_CONTROL_PUBLICATION_SCHEMA')
    target=c['delivery_control_commit']
    need(r.get('target')==r.get('remote_after')==target and r.get('base')==PUBLISHED and
        r.get('commits')==[target],'NEW_CONTROL_PUBLICATION_TARGET')
    return dict(new_control_commit=target,basis='EXTERNALLY_REVIEWED_PUBLICATION_RECEIPT',
        reviewed_receipt_sha256=expected.lower(),publication=r,server_network_used=False,
        receipt_is_operator_pinned_not_cryptographic_signature=True)


def verify_control_bundle(c,out,m):
    package=Path(c['package_root']);fact=c['repair_bundle'];bundle=package/'repair.bundle'
    need(fact['path']=='repair.bundle' and fact['prerequisite']==SCIENCE and
        fact['control_commit']==c['delivery_control_commit'] and bundle.stat().st_size==fact['bytes'] and
        sha(bundle)==fact['sha256'],'CONTROL_BUNDLE_IDENTITY')
    git,repo=c['git'],c['code_root'];objects=Path(os.environ['TEMP'])/'new_control_objects';objects.mkdir(exist_ok=False)
    m.command([git,'-C',repo,'rev-parse','--git-path','objects'],repo,out/'control_object_path',timeout=30)
    alternate=Path((out/'control_object_path.stdout').read_text().strip())
    if not alternate.is_absolute():alternate=Path(repo)/alternate
    env=dict(os.environ,GIT_OBJECT_DIRECTORY=str(objects.resolve()),GIT_ALTERNATE_OBJECT_DIRECTORIES=str(alternate.resolve()),
        GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='never')
    m.command([git,'-C',repo,'bundle','verify',str(bundle)],repo,out/'control_bundle_verify',env=env,timeout=30)
    m.command([git,'bundle','list-heads',str(bundle)],repo,out/'control_bundle_refs',env=env,timeout=30)
    need((out/'control_bundle_refs.stdout').read_text().split()==[c['delivery_control_commit'],'refs/heads/main'],'CONTROL_BUNDLE_REF')
    m.command([git,'-C',repo,'-c','gc.auto=0','-c','maintenance.auto=false','fetch','--no-tags','--no-write-fetch-head',
        str(bundle),'refs/heads/main'],repo,out/'control_bundle_objects',env=env,timeout=60)
    m.command([git,'-C',repo,'merge-base','--is-ancestor',SCIENCE,c['delivery_control_commit']],repo,
        out/'control_ancestry',env=env,timeout=30)
    mapping={'cupti_batch_once_delivery.py':'scripts/cupti_batch_once_delivery.py',
        'cupti_event_b.py':'scripts/cupti_event_b.py','run_cupti_batch_once.ps1':'scripts/run_cupti_batch_once.ps1',
        'git_materialization.py':'scripts/coe_controlled_deployment.py',
        'cupti_batch_publication_repair.py':'scripts/cupti_batch_publication_repair.py'}
    rows=c['control_sources'];need(len(rows)==len(mapping) and {r['path'] for r in rows}==set(mapping),'CONTROL_SOURCE_COVERAGE')
    for i,row in enumerate(rows):
        need(row['git_path']==mapping[row['path']],'CONTROL_SOURCE_PATH')
        label=out/('control_blob_'+str(i))
        m.command([git,'-C',repo,'cat-file','blob',c['delivery_control_commit']+':'+row['git_path']],repo,label,env=env,timeout=30)
        b=label.with_suffix('.stdout').read_bytes()
        need(b==(package/row['path']).read_bytes() and len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'],'CONTROL_SOURCE_BYTES')
    return dict(control_commit=c['delivery_control_commit'],bundle_sha256=fact['sha256'],source_count=len(rows),
        scientific_checkout_changed=False,network_used=False,objects=str(objects),fetch_head_written=False)


def checked_publication(c,out,m,api,flags):
    parent=checked_parent(c,m,api)
    release=check_release_evidence(c,flags)
    control=verify_control_bundle(c,out,m)
    return dict(policy=VERSION,historical_A=parent,new_control_publication=release,new_control_identity=control,
        current_server_network='NOT_ATTEMPTED',original_network_failure_reclassified=False)
