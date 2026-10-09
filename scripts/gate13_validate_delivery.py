"""Deployment CPU checks; no model import, CUDA query, collector or experiment."""
import argparse
from datetime import datetime,timezone
import importlib.util
import json
from pathlib import Path
import sys


def require(ok,reason):
    if not ok:raise ValueError('DELIVERY_CPU_'+reason)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True)
    a=p.parse_args();c=json.loads(a.config.read_text(encoding='utf-8-sig'))
    sys.path.insert(0,c['code_root'])
    from exposedpath.formal_protocol import validate_release,validate_artifacts
    from exposedpath.gate11_pilot import sha
    from exposedpath import platform_adapter
    root=a.config.resolve().parent
    release=json.loads((root/'signed_release.json').read_text(encoding='utf-8'))
    require(sha(root/'signed_release.json')==c['signed_release_sha256'],'SIGNED_RELEASE')
    require(c['commit']==release['protocol']['execution_commit']==release['protocol']['analysis_commit'],'COMMIT_BINDING')
    require(platform_adapter.git(['-C',c['code_root'],'rev-parse','HEAD'])==c['commit'],'CHECKOUT')
    require(not platform_adapter.git(['-C',c['code_root'],'status','--porcelain']),'DIRTY')
    validate_release(release['protocol'],release['approval'])
    actual=validate_artifacts(c['code_root'],release['protocol'])
    for name,key in [('prompt_tokens.json','prompt_sha256'),('prompt_512.json','prompt_512_sha256'),('model_sha256.csv','inventory_sha256')]:
        require(sha(root/name)==c[key],'INPUT_'+name)
    spec=importlib.util.spec_from_file_location('delivery_controller',root/'gate13_formal_batch.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    rows=module.plan(release,c['batch_id'],datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))
    require(len(rows)==60 and len({r['pair_id'] for r in rows})==30,'PLAN')
    require(c['model_process_budget']==60 and c['profile_budget']==30 and c['warmup_count']==3,'BUDGET')
    print(json.dumps(dict(status='DELIVERY_CPU_PASS',commit=c['commit'],source_files=len(actual),planned_runs=60,
        pairs=30,model_executed=False,cuda_initialized=False,collector_executed=False)))
    return 0


if __name__=='__main__':raise SystemExit(main())
