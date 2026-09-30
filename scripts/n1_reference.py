"""Versioned N1 continuation source binding, not an analyzer or byte normalizer."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess

from exposedpath.gate8_isolated_preflight import read, sha

VERSION='N1-REMAINING-REFERENCE/0.2'
PREFLIGHT_FILES=('auxiliary_preflight.json','auxiliary_preflight.claim.json',
    'auxiliary_preflight.final.json','diagnostic/isolated_preflight_target.json')
EXTRA_PRODUCERS={'exposedpath_v141/gate8_target_python.py','exposedpath_v141/gate8_files.py',
    'exposedpath_v141/gate8_adapter.py','exposedpath_v141/gate8_source_probe.py',
    'exposedpath_v141/gate8_controlled_cli.py','exposedpath_v141/gate8_qualification.py',
    'scripts/gate7_smoke_validation.py','scripts/gate8_diagnostic_collect.py'}


def require(ok,reason):
    if not ok: raise ValueError('N1_REFERENCE_'+reason)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git_bytes(root,*args):
    executable=shutil.which('git')
    require(executable is not None,'GIT_UNAVAILABLE')
    return subprocess.run([executable,'-C',str(root),*args],check=True,
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30).stdout


def producer_paths(root,commit):
    require(re.fullmatch('[0-9a-f]{40}',commit) is not None,'COMMIT')
    raw=git_bytes(root,'ls-tree','-r','--name-only','-z',commit)
    require(raw.endswith(b'\0'),'GIT_PATH_LIST')
    names=raw[:-1].decode('utf-8',errors='strict').split('\0')
    require(len(names)==len(set(names)) and '' not in names,'GIT_PATH_LIST')
    result={n for n in names if n.startswith('exposedpath/') and n.endswith('.py') or n in EXTRA_PRODUCERS}
    require(EXTRA_PRODUCERS<=result,'PRODUCER_SET')
    return sorted(result)


def source_proof(old_blob,new_blob,observed_hash):
    """Explain a SEALED hash, never infer an expectation from current worktree bytes."""
    require(old_blob==new_blob,'GIT_CONTENT_CHANGED')
    candidates={'GIT_BYTES':old_blob}
    if b'\r' not in old_blob and b'\n' in old_blob:
        candidates['LF_TO_CRLF']=old_blob.replace(b'\n',b'\r\n')
    matches=[(name,b) for name,b in candidates.items() if digest(b)==observed_hash]
    require(len(matches)==1,'EXECUTION_BYTES_UNEXPLAINED')
    name,actual=matches[0]
    return dict(git_sha256=digest(old_blob),git_size_bytes=len(old_blob),
        execution_sha256=observed_hash,execution_size_bytes=len(actual),representation=name)


def check_file(root,name,expected_hash,expected_size,rows):
    row=dict(root=str(Path(root).resolve()),path=name,expected_sha256=expected_hash,expected_size_bytes=expected_size,
        actual_sha256=None,actual_size_bytes=None,status='PATH_ESCAPE')
    rows.append(row)
    root=Path(root).resolve(); rel=PurePosixPath(name)
    safe=bool(name) and not rel.is_absolute() and ':' not in name and '\\' not in name and all(x not in ('','..','.') for x in name.split('/'))
    path=(root/name).resolve()
    if safe and path.is_relative_to(root):
        if not path.is_file(): row['status']='FILE_MISSING'
        else:
            try:
                data=path.read_bytes(); row.update(actual_sha256=digest(data),actual_size_bytes=len(data))
                row['status']='PASS' if digest(data)==expected_hash and len(data)==expected_size else 'HASH_MISMATCH'
            except OSError as exc:
                row.update(status='FILE_READ_ERROR',error=f'{type(exc).__name__}: {exc}')
    require(row['status']=='PASS',json.dumps(row,sort_keys=True))
    return path


def validate_sources(reference,code_root,rows,binding_root):
    require(reference.get('schema_version')==VERSION,'VERSION')
    root=Path(reference['baseline_root']); refs=reference['baseline_files']; sizes=reference['baseline_sizes']
    required=set(PREFLIGHT_FILES)|{'collection_report.json','input_receipt.json','diagnostic/manifest.json',
        'diagnostic/prompt.json','diagnostic/n1_model_calls.json','diagnostic/producer/pass_identity.json',
        'diagnostic/producer/producer_receipt.json'}
    require(required<=refs.keys() and refs.keys()==sizes.keys(),'BASELINE_SET')
    for name,expected in refs.items(): check_file(root,name,expected,sizes[name],rows)
    # Packaged originals are independently pinned, and must equal the retained
    # baseline originals. Neither a loose tree_hashes map nor current bytes win.
    for name in PREFLIGHT_FILES: check_file(binding_root,name,refs[name],sizes[name],rows)
    pre,claim,final,target=(read(root/name) for name in PREFLIGHT_FILES)
    manifest=read(root/'diagnostic/manifest.json'); ledger=read(root/'diagnostic/producer/pass_identity.json')
    receipt=read(root/'input_receipt.json'); producer=read(root/'diagnostic/producer/producer_receipt.json')
    calls=read(root/'diagnostic/n1_model_calls.json')
    ph=refs[PREFLIGHT_FILES[0]]; mh=refs['diagnostic/manifest.json']
    require(pre['schema_version']==claim['schema_version']=='exposedpath-isolated-preflight/0.1.0'
        and pre['git_commit']==reference['baseline_commit']==manifest['runner_git_commit']==ledger['runner_git_commit']
        and pre['git_dirty'] is False and ledger['runner_git_dirty'] is False
        and pre['run_id']==claim['run_id']==manifest['run_id']==ledger['run_id']==receipt['identity']['run_id']==producer['run_id']
        and pre['nonce']==claim['nonce'] and bool(pre['nonce'])
        and ph==claim['preflight_sha256']==final['preflight_sha256']
        and final['status']=='PASS' and final['target_claim_sha256']==refs[PREFLIGHT_FILES[1]]
        and target==claim and claim['target_pid']==ledger['pid']==calls['pid']
        and pre['input_hashes']['manifest.json']==mh==ledger['wmpc_manifest_sha256']
        and pre['input_hashes']['prompt.json']==refs['diagnostic/prompt.json']==manifest['prompt_tokens_sha256']
        and manifest['wmpc_id']==ledger['wmpc_id']==receipt['identity']['wmpc_id'],'PREFLIGHT_SOURCE_JOIN')
    collection=read(root/'collection_report.json')['collection']; argv=collection['argv']
    require(collection['status']=='COMPLETE' and collection['exit_code']==0,'BASELINE_COLLECTION')
    for flag,value in (('--auxiliary-sha256',ph),('--launch-nonce',pre['nonce'])):
        require(argv.count(flag)==1 and argv.index(flag)+1<len(argv) and argv[argv.index(flag)+1]==value,'COLLECTION_PREFLIGHT_JOIN')
    for item in receipt['artifacts'].values():
        require(refs.get(item['filename'])==item['sha256'] and sizes.get(item['filename'])==item['size_bytes'],'INPUT_RECEIPT_JOIN')
    required_artifacts={'wmpc_manifest':'diagnostic/manifest.json','prompt':'diagnostic/prompt.json',
        'pass_identity':'diagnostic/producer/pass_identity.json','producer_receipt':'diagnostic/producer/producer_receipt.json',
        'runner_source':'diagnostic/runner_source.py'}
    require(all(receipt['artifacts'].get(key,{}).get('filename')==name for key,name in required_artifacts.items()),'INPUT_RECEIPT_SET')
    require(pre['tree_hashes']['exposedpath/runner.py']==manifest['runner_source_sha256']==ledger['runner_source_sha256']
        ==refs['diagnostic/runner_source.py'],'RUNNER_SOURCE_JOIN')
    require(producer['files']['pass_identity.json']['sha256']==refs['diagnostic/producer/pass_identity.json']
        and producer['files']['pass_identity.json']['size_bytes']==sizes['diagnostic/producer/pass_identity.json'],'PRODUCER_LEDGER_JOIN')
    current=reference['execution_commit']; old=reference['baseline_commit']
    require(all(re.fullmatch('[0-9a-f]{40}',c) for c in (old,current)),'COMMIT')
    require(git_bytes(code_root,'rev-parse','HEAD').decode('ascii').strip()==current,'CURRENT_COMMIT')
    names=producer_paths(code_root,old)
    require(names==producer_paths(code_root,current) and set(names)==set(reference['source_compatibility']),'PRODUCER_SET')
    for name in names:
        proof=source_proof(git_bytes(code_root,'show',old+':'+name),git_bytes(code_root,'show',current+':'+name),pre['tree_hashes'][name])
        require(proof==reference['source_compatibility'][name],'SOURCE_COMPATIBILITY:'+name)
        check_file(code_root,name,proof['execution_sha256'],proof['execution_size_bytes'],rows)
