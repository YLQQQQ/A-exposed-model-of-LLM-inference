"""Read-only native callchain query. Never infers payload from absent effects."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sqlite3

VERSION='memset-callsite-sources/0.1.0'


def _sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def read_sources(path,scope):
    """Actual IDs, never nearest timestamps; all encountered targets retained."""
    from exposedpath.memset_callsite import require
    require(set(scope)=={'start','end','pid','tid','global_tid'} and
        all(type(v) is int for v in scope.values()) and 0<=scope['start']<scope['end']
        and scope['pid']==(scope['global_tid']>>24)&0xffffff
        and scope['tid']==scope['global_tid']&0xffffff,'SCOPE')
    path=Path(path).resolve();source_sha=_sha(path);issues=[];calls=[];module_files={}
    with sqlite3.connect(path.as_uri()+'?mode=ro&immutable=1',uri=True) as db:
        db.row_factory=sqlite3.Row
        tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        require({'StringIds','CUPTI_ACTIVITY_KIND_RUNTIME'}<=tables,'PROVIDER_TABLES')
        strings=dict(db.execute('SELECT id,value FROM StringIds'))
        runtime=[dict(r) for r in db.execute('SELECT rowid AS source_rowid,* FROM CUPTI_ACTIVITY_KIND_RUNTIME')]
        cols={r[1] for r in db.execute('PRAGMA table_info(CUPTI_ACTIVITY_KIND_RUNTIME)')}
        require({'start','end','globalTid','nameId','returnValue','correlationId','eventClass'}<=cols,'RUNTIME_SCHEMA')
        target_chain_ids={a.get('callchainId') for a in runtime if a['globalTid']&~0xffffff==scope['global_tid']&~0xffffff
            and a['end']>scope['start'] and a['start']<scope['end']
            and re.fullmatch(r'cudaMemsetAsync(?:_ptsz)?(?:_v\d+)?',strings.get(a['nameId'],''))}
        target_chain_ids.discard(None)
        effects={}
        for table in ('CUPTI_ACTIVITY_KIND_MEMSET','CUPTI_ACTIVITY_KIND_MEMCPY','CUPTI_ACTIVITY_KIND_KERNEL'):
            if table not in tables:continue
            for row in db.execute('SELECT rowid AS source_rowid,* FROM '+table):
                r=dict(row)
                if r['globalPid']&~0xffffff!=scope['global_tid']&~0xffffff:continue
                effects.setdefault(r['correlationId'],[]).append(dict(record_id=table+':'+str(r['source_rowid']),
                    bytes=r.get('bytes'),start=r['start'],end=r['end'],device_id=r['deviceId'],
                    context_id=r['contextId'],stream_id=r['streamId']))
        chains={}
        if 'CUDA_CALLCHAINS' in tables:
            cc={r[1] for r in db.execute('PRAGMA table_info(CUDA_CALLCHAINS)')}
            require({'id','stackDepth','module','symbol','unresolved','originalIP'}<=cc,'CALLCHAIN_SCHEMA')
            ids=list(target_chain_ids)
            for low in range(0,len(ids),500):
                chunk=ids[low:low+500]
                for row in db.execute('SELECT rowid AS source_rowid,* FROM CUDA_CALLCHAINS WHERE id IN ('+','.join('?' for _ in chunk)+')',chunk):
                    r=dict(row);chains.setdefault(r['id'],[]).append(r)
        for a in runtime:
            gt=a['globalTid'];name=strings.get(a['nameId'],'')
            if gt&~0xffffff!=scope['global_tid']&~0xffffff or not re.fullmatch(r'cudaMemsetAsync(?:_ptsz)?(?:_v\d+)?',name):continue
            if a['end']<=scope['start'] or a['start']>=scope['end']:continue
            aid='CUPTI_ACTIVITY_KIND_RUNTIME:'+str(a['source_rowid']);reasons=[]
            if not scope['start']<=a['start']<=a['end']<=scope['end']:reasons.append('BOUNDARY')
            if gt!=scope['global_tid']:reasons.append('FOREIGN_THREAD')
            if a['eventClass']!=0 or a['returnValue']!=0:reasons.append('RUNTIME_CLASS_OR_RETURN')
            corr=a['correlationId']
            if type(corr) is not int or len([x for x in runtime if x['correlationId']==corr and
                x['globalTid']&~0xffffff==scope['global_tid']&~0xffffff and x['eventClass']==0])!=1:reasons.append('CORRELATION_AMBIGUOUS')
            chain=a.get('callchainId');rows=chains.get(chain,[]) if chain is not None else []
            depths=[r['stackDepth'] for r in rows]
            if not rows:reasons.append('CALLCHAIN_MISSING_OR_DANGLING')
            elif any(type(d) is not int or d<0 for d in depths) or len(set(depths))!=len(depths):
                reasons.append('CALLCHAIN_DEPTH_AMBIGUOUS')
            elif sorted(depths)!=list(range(len(depths))):reasons.append('CALLCHAIN_DEPTH_GAP')
            frames=[];useful=False
            for f in sorted(rows,key=lambda r:r['stackDepth'] if type(r['stackDepth']) is int else -1):
                module=strings.get(f['module']);symbol=strings.get(f['symbol']);ip=f['originalIP']
                good=bool(module) and type(ip) is int and 0<ip<2**64 and f['unresolved'] in (0,1)
                if not good:reasons.append('FRAME_MODULE_OR_IP_UNAVAILABLE')
                bound=False
                if module and module not in module_files:
                    p=Path(module)
                    try:
                        module_files[module]=dict(status='RAW_NAMED_FILE_READ_AFTER_CAPTURE_NOT_LOAD_PROOF',
                            bytes=p.stat().st_size,sha256=_sha(p)) if p.is_absolute() and p.is_file() else dict(status='FILE_UNAVAILABLE')
                    except OSError as exc:module_files[module]=dict(status='FILE_UNAVAILABLE',error=str(exc))
                if module:bound=module_files[module]['status']=='RAW_NAMED_FILE_READ_AFTER_CAPTURE_NOT_LOAD_PROOF'
                basename=module.replace('\\','/').rsplit('/',1)[-1].lower() if module else ''
                tool=any(s in basename for s in ('cudart','cupti','nvcuda','nsight','injection','ntdll','kernelbase','kernel32'))
                caller=good and bound and not tool;useful=useful or caller
                frames.append(dict(source_rowid=f['source_rowid'],depth=f['stackDepth'],module=module,symbol=symbol,
                    symbol_unresolved=f['unresolved']==1,original_ip=ip,useful_caller=caller,
                    ip_is_callee_entry=False,module_file_bound=bound))
            if not useful:reasons.append('NO_BOUND_USEFUL_CALLER')
            es=effects.get(corr,[])
            calls.append(dict(runtime_record_id=aid,start=a['start'],end=a['end'],global_tid=gt,
                pid=(gt>>24)&0xffffff,tid=gt&0xffffff,name=name,return_code=a['returnValue'],correlation_id=corr,
                callchain_id=chain,frames=frames,effect_ids=[e['record_id'] for e in es],effects=es,
                effect_observation='MAPPED_OBSERVED' if es else 'NO_ASSOCIATED_EFFECT_OBSERVED',
                count=None,source_location='ADDRESS_LEVEL' if useful and not reasons else 'UNRESOLVED',issues=reasons))
            issues.extend(aid+':'+r for r in dict.fromkeys(reasons))
    missing=sum(not a['effect_ids'] for a in calls)
    status=('NO_TARGET_CALLS_NOT_DISCRIMINATING' if not calls else
        'NOT_DISCRIMINATING_FOR_MISSING_EFFECT_ORIGIN' if not missing else 'INCONCLUSIVE' if issues else 'CALLSITE_LOCATED')
    require(_sha(path)==source_sha,'RAW_CHANGED')
    return dict(schema_version=VERSION,status=status,role='Engineering',scope=scope,
        sqlite_sha256=source_sha,target_count=len(calls),mapped_count=len(calls)-missing,missing_effect_count=missing,
        calls=calls,module_files=module_files,issues=issues,parameter_evidence=False,device_effect_recovery=False,
        old_attempt_repaired=False,a_admission='NOT_ASSESSED',coe_admission='NOT_ASSESSED',
        dropped_records_status='UNKNOWN',measurement_validity='NOT_ASSESSED',scientific_outputs_allowed=False)


def process(sqlite_path,diagnostic,output):
    """Producer + common-clock projection only; no S/A/COE generation."""
    from exposedpath.gate8_isolated_preflight import read,sha,write_new
    from exposedpath import observation_preparation as prep,memset_callsite as contract
    from exposedpath_v141.canonical_raw import convert_sqlite_to_canonical
    from exposedpath_v141.gate8_scope import project_completion_scopes
    d=Path(diagnostic);mf=read(d/'manifest.json');b=prep.validate(mf)
    contract.require(contract.active(b),'SOURCE_ROLE')
    ledger=read(d/'producer/pass_identity.json');execution=read(d/'engineering_execution.json')
    tokens=prep.validate_tokens(d/'batch_tokens.json',mf,ledger,execution,d/'manifest.json',d/'producer/producer_receipt.json')
    # The collector checks the fixed target's token reference separately. Here
    # the versioned producer validator establishes actual values + identity.
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    paths=dict(pass_identity=d/'producer/pass_identity.json',preflight=d/'adapter_preflight.json',cuda_probe=d/'cuda_probe.json')
    source_hashes={str(p):sha(p) for p in (d/'manifest.json',d/'prompt.json',d/'batch_tokens.json',
        d/'engineering_execution.json',d/'producer/producer_receipt.json',d/'producer/host_boundaries.json',*paths.values())}
    canonical=convert_sqlite_to_canonical(sqlite_path,out/'canonical','Engineering',raw_sha256=sha(d.parent/'capture.nsys-rep'),
        collector_version='2026.2.1.210',gate8_sources=paths)
    projection=out/'projection.json'
    project_completion_scopes(canonical,d/'producer/host_boundaries.json',projection)
    projected=read(projection)
    rows=projected.get('projections',[])
    row=[r for r in rows if r['phase']=='prefill']
    contract.require(len(row)==1,'PREFILL_PROJECTION')
    row=row[0];identity=row['identity']
    measured=[r for r in ledger['requests'] if r['request_role']=='measured']
    contract.require(len(measured)==1 and measured[0]['identity']==identity,'PREFILL_IDENTITY')
    from exposedpath_v141.sync_semantics import load_canonical_bundle
    bundle=load_canonical_bundle(canonical)
    anchors=[r for r in bundle['records']['nvtx'] if r['record_id']==row['start_ref']['record_id']]
    contract.require(len(anchors)==1 and anchors[0]['process_id']==ledger['pid'],'PREFILL_THREAD_ANCHOR')
    gt=anchors[0]['global_tid']
    result=read_sources(sqlite_path,dict(start=row['start_ns'],end=row['end_ns'],pid=ledger['pid'],tid=gt&0xffffff,global_tid=gt))
    result.update(binding=b,identity=identity,token_ids=tokens,manifest_sha256=sha(d/'manifest.json'),
        producer_receipt_sha256=sha(d/'producer/producer_receipt.json'),projection_sha256=sha(projection),source_hashes=source_hashes)
    contract.require(all(sha(p)==h for p,h in source_hashes.items()),'PRODUCER_FILES_CHANGED')
    write_new(out/'sources.json',result)
    return out/'sources.json'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sqlite',type=Path,required=True);p.add_argument('--diagnostic',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=process(a.sqlite,a.diagnostic,a.output);r=json.loads(result.read_text(encoding='utf8'));print(r['status'],flush=True)
    return 0 if r['status']=='CALLSITE_LOCATED' else 1


if __name__=='__main__':raise SystemExit(main())
