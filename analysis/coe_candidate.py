"""Independent COE candidate, never a production A/B or qualification reader.

The file entry reuses sealed producer/Canonical readers and the accepted
diagnostic disposition. No model, CUDA, collector or domain calculation runs.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from scripts.analyze_completion_operation_candidate import (
    Activity, Api, CandidateError, clipped_union, completion_overlap, enum_name,
    normalized, one, recover_suffix, verify_device_bridge,
)
from exposedpath_v141.a_api_classification import _classify, VERSION as A_API_REGISTRY_VERSION
from exposedpath_v141.sync_semantics import classify_cuda_api

VERSION = 'coe-candidate-analysis/0.1.0'
EVIDENCE_VERSION = 'coe-operation-evidence/0.1.0'
ROLE = 'EXPLORATORY_CANDIDATE_NOT_FORMAL_A'
CONTRACT = 'COE-CANDIDATE/0.1.0-draft'
HELPER_AST = '86b56df2f7d9381a6d73a14510c3345c911b1735825d2916521a5a3678bbde4a'
IDENTITY_FIELDS = ('experiment_id','wmpc_id','run_id','run_role','data_role',
                   'pass_id','attempt_id','request_id','repeat_id')
DEPENDENCIES = {'cudaStreamWaitEvent','cudaEventRecord','cudaEventSynchronize',
                'cudaGraphLaunch','cuStreamWaitEvent','cuEventRecord','cuGraphLaunch'}


def require(ok, reason):
    if not ok:
        raise CandidateError('COE_' + reason)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda:f.read(1024*1024),b''): h.update(part)
    return h.hexdigest()


def interval(a,b):
    require(type(a) is int and type(b) is int and -(2**63)<=a<=b<2**63
            and b-a<2**63,'TIME_RANGE')


def classifications(apis):
    # Reuse the same frozen registry object within this operation/run; never
    # reload JSON for each of tens of thousands of equal API names.
    from exposedpath_v141.sync_semantics import load_sync_registry
    registry=load_sync_registry()
    # Explicit version, independent of a caller's N1 opaque-allocation context.
    return {name:(_classify(name,A_API_REGISTRY_VERSION),classify_cuda_api(name,registry))
            for name in {a['name'] for a in apis}}


def select_pair(apis, *, thread, start, end):
    local=[r for r in apis if r['thread']==thread and start<=r['start']<=r['end']<=end]
    copy=one((r for r in local if normalized(r['name'])=='cudaMemcpyAsync'),'COPY_PAIR')
    sync=one((r for r in local if normalized(r['name'])=='cudaStreamSynchronize'),'SYNC_PAIR')
    require(len(local)==2,'PAIR_API_SET')
    return copy,sync


def validate_operation_identity(identity, payload, point, token_index, phase):
    require(all(payload.get(k)==identity[k] and point['identity'].get(k)==identity[k]
                for k in IDENTITY_FIELDS),'OPERATION_IDENTITY')
    require(payload.get('sync_origin')=='natural_token_ready' and payload.get('phase')==phase
            and payload.get('token_index')==point.get('token_index')==token_index
            and point.get('boundary_kind')=='token_ready','OPERATION_TOKEN_PHASE_IDENTITY')


def coverage_entry(api, effect_count, related_operation=None, *, classification=None):
    (category,rule),semantic=classification or classifications([api])[api['name']]
    reason=None
    if type(api['return_code']) is not int or api['return_code']!=0:reason='API_RETURN_UNRESOLVED_OR_FAILED'
    elif category=='submit' and effect_count==0:reason='SUBMIT_EFFECT_MISSING'
    elif category=='non_submit' and effect_count:reason='NON_SUBMIT_EFFECT_CONFLICT'
    if reason:
        status='UNRESOLVED_OR_OUT_OF_SCOPE'
    elif related_operation is not None:
        status=('SUPPORTED_OPERATION_COMPONENT' if related_operation['operation_validity'].startswith('VALID_')
                else 'PAIRED_BUT_UNRESOLVED_OPERATION')
        if status=='PAIRED_BUT_UNRESOLVED_OPERATION':reason='COMPOSITE_OPERATION_NOT_ADMITTED'
    elif category is not None:
        status='ORDINARY_API_BUDGET';reason='NO_SUPPORTED_COMPOSITE_PAIR_RETAIN_ORIGINAL_API_BUDGET'
    elif semantic['role']=='HOST_BLOCKING_SYNC':
        status='PHYSICAL_SYNC_NOT_COMPOSITE';reason='SINGLE_SYNC_SEMANTICS_UNCHANGED'
    else:
        status='UNRESOLVED_OR_OUT_OF_SCOPE';reason=semantic['role']
    return dict(record=api['id'],api=api['name'],category=category,rule=rule,status=status,
        start_ns=api['start'],end_ns=api['end'],reason=reason,
        related_token_index=related_operation['token_index'] if related_operation else None,
        operation_reasons=related_operation['reasons'] if related_operation else [])


def analyze_operation(*, apis, effects, copy, sync, physical, identity, scope, thread,
                      request_start, drain_end, completion_point, copy_effect, source_sha256):
    """Narrow, serial, closed-prior FIFO proof; not full physical default-stream W.

    Other streams/threads/events in the required suffix are refused, rather than
    borrowing an unproven default-stream mode or inventing a data-dependency DAG.
    """
    require(all(isinstance(identity.get(k),str) and identity[k] for k in IDENTITY_FIELDS),'IDENTITY')
    require(identity['pass_id']=='pass1' and (identity['run_role'],identity['data_role']) in
            (('ENGINEERING','Engineering'),('PILOT','Pilot'),('FORMAL','Formal')), 'IDENTITY_ROLE')
    require(len(source_sha256)==64 and all(c in '0123456789abcdef' for c in source_sha256),'SOURCE_HASH')
    require(len({r['id'] for r in apis})==len(apis),'DUPLICATE_API')
    require(copy in apis and sync in apis and copy['thread']==sync['thread']==thread,'PAIR_IDENTITY')
    require(normalized(copy['name'])=='cudaMemcpyAsync' and normalized(sync['name'])=='cudaStreamSynchronize','PAIR_NAME')
    require(type(copy['return_code']) is int and copy['return_code']==0,'COPY_FAILED')
    require(type(sync['return_code']) is int and sync['return_code']==0,'SYNC_FAILED')
    require(physical['correlation']==sync['correlation'] and physical['scope']==scope
            and physical['semantic']=='STREAM_SYNCHRONIZE','PHYSICAL_MAPPING')
    interval(physical['start'],physical['end'])
    require(sync['start']<=physical['start']<=physical['end']<=sync['end'],'PHYSICAL_MAPPING_TIME')
    for r in apis+effects: interval(r['start'],r['end'])
    interval(copy['start'],sync['end'])
    require(sync['end']<=completion_point,'COMPLETION_POINT')
    require(drain_end is not None and drain_end<=request_start<=copy['start'],'DRAIN_ORDER')
    interval(drain_end,request_start);interval(request_start,completion_point)
    classes=classifications(apis)
    for r in apis:
        if drain_end<=r['start']<sync['start']:
            require(normalized(r['name']) not in DEPENDENCIES,'DEPENDENCY_UNSUPPORTED')
            (category,_),semantic=classes[r['name']]
            require(semantic['universe_class']!='DEVICE_DEPENDENCY_EDGE','DEPENDENCY_UNSUPPORTED')
            require(category is not None or semantic['role']=='HOST_BLOCKING_SYNC','UNSUPPORTED_API:'+r['id'])
            require(type(r['return_code']) is int and r['return_code']==0,'PREFIX_API_FAILED:'+r['id'])
    api_values=[Api(r['id'],r['start'],r['end'],r['correlation'],r['thread'],r['return_code']) for r in apis]
    api_by_corr=defaultdict(list)
    for a in api_values:api_by_corr[a.correlation].append(a)
    effects_values=[Activity(r['id'],r['start'],r['end'],r['correlation'],*r['scope'],r['kind']) for r in effects]
    members,prior,future=recover_suffix(effects_values,api_values,request_start=request_start,
        drain_end=drain_end,sync=(sync['start'],sync['end']),scope=tuple(scope),thread=thread)
    require(copy_effect in {r.key for r in members},'COPY_EFFECT_MEMBERSHIP')
    d2h=one((r for r in members if r.key==copy_effect),'COPY_EFFECT')
    require(d2h.kind=='MEMCPY' and d2h.correlation==copy['correlation'],'COPY_EFFECT_MAPPING')
    counts=Counter(r.correlation for r in members)
    for r in apis:
        if request_start<=r['start']<sync['start'] and classes[r['name']][0][0]=='submit':
            require(counts[r['correlation']]>0,'SUBMIT_EFFECT_MISSING:'+r['id'])
    terminal=one((r for r in members if r.end==max(v.end for v in members)),'TERMINAL')
    result=completion_overlap((copy['start'],copy['end']),(sync['start'],sync['end']),[(r.start,r.end) for r in members])
    length=lambda pieces:sum(b-a for a,b in pieces)
    kernel=length(clipped_union(copy['start'],sync['end'],[(r.start,r.end) for r in members if r.kind=='KERNEL']))
    memop=length(clipped_union(copy['start'],sync['end'],[(r.start,r.end) for r in members if r.kind!='KERNEL']))
    op_id=hashlib.sha256(json.dumps([source_sha256,identity,copy['id'],sync['id']],sort_keys=True).encode()).hexdigest()
    return dict(version=VERSION,role=ROLE,operation_id=op_id,identity=identity,copy_id=copy['id'],sync_id=sync['id'],
        operation_validity='VALID_UNDER_DECLARED_SUPPORT_ASSUMPTIONS',profile_applicability='EXPLORATORY_MATCH_NOT_NEW_QUALIFICATION',
        members=[r.key for r in members],member_submits=[dict(record=r.key,submit=one(api_by_corr[r.correlation],'SUBMIT').key) for r in members],
        closed_prior=[r.key for r in prior],excluded_future=[r.key for r in future],terminal=terminal.key,
        terminal_end_ns=terminal.end,captured_submission_boundary_ns=sync['start'],
        kernel_ns=kernel,memop_ns=memop,mixed_ns=kernel+memop-result['candidate_ns'],
        completed_before_copy_count=sum(r.end<=copy['start'] for r in members),
        legacy_ptds_local_equivalence_basis='CLOSED_HISTORY_SERIAL_SAME_FIFO_NO_OBSERVED_INCOMING_EDGES',
        support_assumptions=['NO_UNRECORDED_INCOMING_DEPENDENCY'],full_physical_W_qualified=False,
        pure_host_stall_ns=None,removable_latency_ns=None,**result)


def preview_budget(window, atoms, operation_unions):
    """Optional atom input, never reads/writes a production A file."""
    interval(*window)
    ordered=sorted(atoms,key=lambda a:a['start'])
    require(ordered and ordered[0]['start']==window[0] and ordered[-1]['end']==window[1],'BUDGET_COVERAGE')
    require(all(a['end']==b['start'] for a,b in zip(ordered,ordered[1:])),'BUDGET_PARTITION')
    categories=('host','submit','non_submit','device_wait','residual','unattributed')
    budgets=dict.fromkeys(categories,0);migration=[]
    q=clipped_union(*window,[p for pieces in operation_unions for p in pieces])
    for a in ordered:
        interval(a['start'],a['end']);require(a['category'] in budgets,'BUDGET_CATEGORY')
        budgets[a['category']]+=a['end']-a['start']
        for lo,hi in clipped_union(a['start'],a['end'],q):
            if a['category']=='device_wait':continue
            require(a['category']!='unattributed','UNATTRIBUTED_NOT_RESOLVED')
            budgets[a['category']]-=hi-lo;budgets['device_wait']+=hi-lo
            migration.append(dict(start=lo,end=hi,from_category=a['category'],duration_ns=hi-lo))
    require(sum(budgets.values())==window[1]-window[0] and min(budgets.values())>=0,'BUDGET_CONSERVATION')
    return dict(budgets_ns=budgets,cuda_api_ns=budgets['submit']+budgets['non_submit'],migration=migration,
                migrated_ns=sum(r['duration_ns'] for r in migration),role='EXPLORATORY_BUDGET_PREVIEW_NOT_FORMAL_A')


def _publish(output, value):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    path=output/'candidate.json'
    with path.open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,separators=(',',':'))
    return path


def analyze_evidence_file(path, output):
    """Portable operation audit snapshot. This route never grants qualification."""
    path=Path(path).resolve();value=json.loads(path.read_text(encoding='utf8'))
    require(value.get('schema_version')==EVIDENCE_VERSION,'EVIDENCE_VERSION')
    require(value.get('validation_role') in ('CPU_SYNTHETIC_NOT_GPU_QUALIFICATION','EXPLORATORY_BOUND_OPERATION_NOT_QUALIFICATION'),'EVIDENCE_ROLE')
    item=value['source'];source=(path.parent/item['filename']).resolve()
    require(source.is_relative_to(path.parent) and source!=path,'SOURCE_PATH')
    require(source.is_file() and source.stat().st_size==item['size_bytes'] and sha(source)==item['sha256'],'SOURCE_HASH')
    require(value['operation']['source_sha256']==item['sha256'],'SOURCE_BINDING')
    before=sha(path);operation=analyze_operation(**value['operation'])
    require(sha(path)==before and sha(source)==item['sha256'],'SOURCE_CHANGED')
    return _publish(output,dict(version=VERSION,role=ROLE,validation_role=value['validation_role'],
        input_sha256=before,source=item,operation=operation,new_qualification=False))


def _canonical_records(bundle):
    r=bundle['records']
    apis=[dict(id=a['record_id'],name=a['api_name'],start=a['start_ns'],end=a['end_ns'],
        correlation=a['correlation_id'],thread=a['global_tid'],return_code=a['return_value']) for a in r['cuda_api']]
    effects=[dict(id=a['record_id'],start=a['start_ns'],end=a['end_ns'],correlation=a['correlation_id'],
        scope=[a[k] for k in ('global_pid','device_id','context_id','stream_id')],kind=a['activity_kind']) for a in r['device_activity']]
    return apis,effects


def analyze_files(receipt_path, canonical_path, output):
    """Actual receipt -> Canonical -> per-operation checks, no saved CSV answers.

    Recognized old source schemas remain source roles. This interface cannot
    create a future Pilot run or upgrade old data by changing role.
    """
    from exposedpath_v141.gate8_files import load_input_receipt
    from exposedpath_v141.sync_semantics import load_canonical_bundle
    from exposedpath_v141.gate8_diagnostic_scope import _derive
    from exposedpath_v141.gate9_diagnostic_review import review
    receipt_path=Path(receipt_path).resolve();canonical_path=Path(canonical_path).resolve()
    require(not Path(output).exists(),'NO_OVERWRITE')
    receipt,paths=load_input_receipt(receipt_path)
    bundle=load_canonical_bundle(canonical_path)
    source_sha=sha(paths['sqlite']);manifest=bundle['manifest']
    require(manifest['source']['sqlite']['sha256'].lower()==source_sha,'CANONICAL_SOURCE')
    require(manifest['data_role']==receipt['identity']['data_role'] and manifest['clock']['clock_domain_id']=='NSYS_TRACE_RELATIVE_NS','CANONICAL_IDENTITY_CLOCK')
    source_files={receipt_path,canonical_path,*paths.values(),*(canonical_path.parent/e['filename'] for e in manifest['files'].values())}
    code_root=Path(__file__).resolve().parents[1]
    source_files.update((code_root/p) for p in ('analysis/coe_candidate.py','scripts/analyze_completion_operation_candidate.py',
        'exposedpath_v141/a_api_classification.py','exposedpath_v141/sync_semantics.py',
        'exposedpath_v141/gate8_files.py','exposedpath_v141/gate8_diagnostic_scope.py','exposedpath_v141/gate9_diagnostic_review.py',
        'docs/v1_4_1/contracts/a_api_registry_v0_1.json','docs/v1_4_1/contracts/sync_semantics_registry_v0_2.json',
        'docs/v1_4_1/contracts/coe_candidate_analysis_v0_1.json',
        'docs/v1_4_1/completion_operation_contract_draft_v0_1.md'))
    hashes={str(p):sha(p) for p in source_files}
    require(not any(p.resolve().is_relative_to(Path(output).resolve()) for p in source_files),'OUTPUT_CONTAINS_INPUT')
    diagnostic=_derive(paths['sqlite'],paths['pass_identity']);disposition=review(diagnostic,bundle)
    read=lambda k:json.loads(paths[k].read_text(encoding='utf8'))
    producer=read('producer_receipt');ledger=read('pass_identity');mf=read('wmpc_manifest')
    require(producer['status']=='COMPLETE','PRODUCER_INCOMPLETE')
    source=paths['runner_source'].read_text(encoding='utf-8-sig')
    helper=one((n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='observe_token_ready_boundary'),'HELPER_SOURCE')
    require(hashlib.sha256(ast.dump(helper,include_attributes=False).encode()).hexdigest()==HELPER_AST,'HELPER_PROFILE_OUT_OF_SCOPE')
    require(not any(k in mf for k in ('n1_model','completion_path')) and mf['execution_mode']=='eager','NATURAL_PROFILE_OUT_OF_SCOPE')
    require(mf['inference_framework_version']=='torch2.6.0+cu124' and mf['attention_backend']=='sdpa'
            and mf['dtype_and_quantization']=='fp16','SOFTWARE_PROFILE_OUT_OF_SCOPE')
    require(all(r['clock_domain_id']=='NSYS_TRACE_RELATIVE_NS' for kind in ('cuda_api','cuda_sync','device_activity','nvtx')
                for r in bundle['records'][kind]),'RECORD_CLOCK_CONFLICT')
    token_key=one((k for k in ('formal_tokens','batch_tokens','pilot_tokens') if k in paths),'TOKEN_ARTIFACT')
    token=read(token_key)
    require(token['manifest_sha256']==sha(paths['wmpc_manifest']) and token['producer_receipt_sha256']==sha(paths['producer_receipt']),'TOKEN_LINEAGE')
    token_version={'formal_tokens':'exposedpath-formal-tokens/0.1.0','batch_tokens':'exposedpath-batch-load-tokens/0.1.0',
                   'pilot_tokens':'exposedpath-pilot-tokens/0.1.0'}[token_key]
    require(token['schema_version']==token_version,'TOKEN_VERSION')
    binding_key={'formal_tokens':'formal','pilot_tokens':'pilot','batch_tokens':'batch_load'}[token_key]
    require(token[binding_key]==mf[binding_key],'TOKEN_ROLE_BINDING')
    apis,effects=_canonical_records(bundle);operations=[];coverage=[];relevant={}
    classes=classifications(apis)
    nvtx=bundle['records']['nvtx'];syncs=bundle['records']['cuda_sync'];drains=read('drain_ledger')['drains']
    host=read('host_ledger');probe=read('cuda_probe');preflight=read('preflight')
    with sqlite3.connect(paths['sqlite'].resolve().as_uri()+'?mode=ro&immutable=1',uri=True) as db:
        db.row_factory=sqlite3.Row
        for tr in token['requests']:
            identity=tr['identity']
            require(all(identity[k]==v for k,v in receipt['identity'].items()),'TOKEN_IDENTITY')
            lr=one((r for r in ledger['requests'] if r['identity']==identity),'REQUEST_LEDGER')
            require(lr['request_role']=='measured' and lr['outcome']=='COMPLETE' and not lr['reasons'] and lr['early_eos'] is False,'ACTUAL_REQUEST')
            values=tr['token_ids'];batch=mf['batch_size']
            require(len(values)==mf['fixed_output_tokens']==lr['actual_output_tokens'] and
                all(len(t)==batch and all(type(v) is int and v>=0 for v in t) for t in values),'ACTUAL_TOKEN_SHAPE')
            if token_key=='batch_tokens':
                require(tr['actual_input_shape']==[batch,mf['fixed_input_tokens']] and tr['actual_output_tokens_per_sample']==[len(values)]*batch
                        and tr['early_eos'] is False,'ACTUAL_BATCH_SHAPE')
            markers=[];ranges=[];drange=[]
            for n in nvtx:
                text=n['text'] or ''
                if not text.startswith(('EXPOSEDPATH_BOUNDARY_V1:','EXPOSEDPATH_JSON_V1:','EXPOSEDPATH_DRAIN_V1:')):continue
                p=json.loads(text.split(':',1)[1]);i=p.get('identity',p)
                if not all(i.get(k)==identity[k] for k in IDENTITY_FIELDS):continue
                if text.startswith('EXPOSEDPATH_BOUNDARY_V1:'):markers.append((n,p))
                elif text.startswith('EXPOSEDPATH_DRAIN_V1:'):drange.append((n,p))
                elif p.get('sync_origin')=='natural_token_ready':ranges.append((n,p))
            origin,_=one(((n,p) for n,p in markers if p['boundary_kind']=='request_start'),'REQUEST_START')
            thread=origin['global_tid'];process=thread-thread%2**24
            ra=[a for a in apis if a['thread']-a['thread']%2**24==process]
            re=[e for e in effects if e['scope'][0]==process]
            ds,dp=one(drange,'DRAIN_RANGE');dl=one((d for d in drains if d['identity']==identity),'DRAIN_LEDGER')
            require(dl['status']=='COMPLETE' and dl['error'] is None and dl['operation_id']==dp['operation_id'],'DRAIN_BINDING')
            da=one((a for a in ra if a['thread']==thread and normalized(a['name'])=='cudaDeviceSynchronize'
                    and ds['start_ns']<=a['start']<=a['end']<=ds['end_ns']),'DRAIN_API')
            require(type(da['return_code']) is int and da['return_code']==0 and da['end']<=ds['end_ns']<=origin['start_ns'],'DRAIN_SUCCESS')
            ps=one((s for s in syncs if s['runtime_record_id']==da['id']),'DRAIN_PHYSICAL')
            require(ps['sync_type_name'].endswith('_CONTEXT_SYNCHRONIZE'),'DRAIN_SEMANTICS')
            for ti,actual in enumerate(values):
                phase='prefill' if ti==0 else 'decode';op=dict(token_index=ti,phase=phase,identity=identity,actual_host_token=actual,
                    operation_validity='UNRESOLVED',candidate_ns=None,reasons=[])
                try:
                    n,p=one(((n,p) for n,p in ranges if p['token_index']==ti),'TOKEN_PAIR_RANGE')
                    anchor,point=one(((n,p) for n,p in markers if p['boundary_kind']=='token_ready' and p['token_index']==ti),'TOKEN_POINT')
                    validate_operation_identity(identity,p,point,ti,phase)
                    require(n['global_tid']==anchor['global_tid']==thread and p['phase']==phase,'TOKEN_SCOPE_IDENTITY')
                    require(n['start_ns']<=anchor['start_ns']<=n['end_ns'],'POINT_RANGE')
                    h=one((v for v in host if v['payload']==point),'HOST_POINT_BINDING')
                    require(h['host_observed_ns']<=h['host_before_marker_ns']<=h['host_after_marker_ns'],'HOST_POINT_ORDER')
                    copy,sync=select_pair(ra,thread=thread,start=n['start_ns'],end=n['end_ns'])
                    for component in (copy['id'],sync['id']):relevant[component]=op
                    for mark in nvtx:
                        text=mark['text'] or ''
                        if mark['global_tid']!=thread or not origin['start_ns']<=mark['start_ns']<=sync['end']:continue
                        if text.startswith(('EXPOSEDPATH_BOUNDARY_V1:','EXPOSEDPATH_JSON_V1:')):
                            owner=json.loads(text.split(':',1)[1]);owner=owner.get('identity',owner)
                            if owner.get('request_id') is not None:
                                require(all(owner.get(k)==identity[k] for k in IDENTITY_FIELDS),'CROSS_REQUEST_OWNERSHIP')
                    phys=one((s for s in syncs if s['runtime_record_id']==sync['id']),'SYNC_PHYSICAL')
                    d=one((e for e in re if e['kind']=='MEMCPY' and e['correlation']==copy['correlation']),'COPY_EFFECT')
                    raw=one((e for e in bundle['records']['device_activity'] if e['record_id']==d['id']),'D2H_SOURCE')
                    attrs=raw['attributes']
                    require(enum_name(db,'ENUM_CUDA_MEMCPY_OPER',attrs['copy_kind'])=='CUDA_MEMCPY_KIND_DTOH'
                        and enum_name(db,'ENUM_CUDA_MEM_KIND',attrs['src_kind'])=='CUDA_MEMOPR_MEMORY_KIND_DEVICE'
                        and enum_name(db,'ENUM_CUDA_MEM_KIND',attrs['dst_kind'])=='CUDA_MEMOPR_MEMORY_KIND_PAGEABLE'
                        and attrs['bytes']==8*batch,'COPY_MEMORY_PROFILE')
                    bridge=verify_device_bridge(db,ledger['pid'],d['scope'][1],d['scope'][2],probe,preflight)
                    require(ps['device_id']==d['scope'][1] and ps['context_id']==d['scope'][2],'DRAIN_DEVICE_CONTEXT')
                    for a in ra:
                        if origin['start_ns']<=a['start']<sync['start'] and classes[a['name']][1]['role']=='HOST_BLOCKING_SYNC':
                            internal=one((s for s in syncs if s['runtime_record_id']==a['id']),'INTERNAL_SYNC_MAPPING')
                            require(a['return_code']==0 and internal['global_pid']==process
                                and internal['device_id']==d['scope'][1] and internal['context_id']==d['scope'][2], 'INTERNAL_SYNC_IDENTITY')
                            require(internal['sync_type_name'].endswith('_STREAM_SYNCHRONIZE')
                                and internal['stream_id']==d['scope'][3],'INTERNAL_SYNC_SCOPE')
                    physical=dict(id=phys['record_id'],correlation=phys['correlation_id'],scope=[phys[k] for k in ('global_pid','device_id','context_id','stream_id')],
                        start=phys['start_ns'],end=phys['end_ns'],semantic='STREAM_SYNCHRONIZE' if phys['sync_type_name'].endswith('_STREAM_SYNCHRONIZE') else 'UNSUPPORTED')
                    result=analyze_operation(apis=ra,effects=re,copy=copy,sync=sync,physical=physical,identity=identity,
                        scope=d['scope'],thread=thread,request_start=origin['start_ns'],drain_end=da['end'],completion_point=anchor['start_ns'],
                        copy_effect=d['id'],source_sha256=source_sha)
                    intervals=[(e['start'],e['end']) for e in re]
                    plain=clipped_union(copy['start'],sync['end'],intervals)
                    op.update(result,device_bridge=bridge,copy_wall_ns=copy['end']-copy['start'],sync_wall_ns=sync['end']-sync['start'],
                        d2h_id=d['id'],d2h_bytes=attrs['bytes'],copy_interval=[copy['start'],copy['end']],sync_interval=[sync['start'],sync['end']],
                        token_point_ref=anchor['record_id'],token_point_ns=anchor['start_ns'],request_start_ns=origin['start_ns'],
                        same_operation_all_gpu_union_ns=sum(b-a for a,b in plain))
                except (CandidateError,KeyError,TypeError,ValueError) as exc:
                    op['reasons']=[str(exc) if isinstance(exc,ValueError) else 'SCHEMA_'+type(exc).__name__+':'+str(exc)]
                    op['candidate_ns']=None
                operations.append(op)
            final=one(((n,p) for n,p in markers if p['boundary_kind']=='token_ready' and p['token_index']==len(values)-1),'FINAL_TOKEN')[0]['start_ns']
            effect_counts=Counter(e['correlation'] for e in re)
            for a in ra:
                if not origin['start_ns']<=a['start']<final:continue
                coverage.append(coverage_entry(a,effect_counts[a['correlation']],relevant.get(a['id']),classification=classes[a['name']]))
    require(all(sha(p)==h for p,h in hashes.items()),'SOURCE_CHANGED')
    return _publish(output,dict(version=VERSION,contract=CONTRACT,role=ROLE,source_identity=receipt['identity'],
        source_data_role=receipt['identity']['data_role'],source_sqlite_sha256=source_sha,operations=operations,coverage=coverage,
        source_hashes=hashes,diagnostic_review=disposition,analysis_code_sha256=sha(Path(__file__)),
        computation='CANONICAL_PLUS_REUSED_FIFO_RECOVERY',new_qualification=False,production_A_B_modified=False,
        dropped_records_status='UNKNOWN',measurement_validity='NOT_ASSESSED',pure_host_stall_ns=None))


def pilot_schedule(config, batch_id):
    """Validate a pending plan and enumerate identities. Never executes a run."""
    require(config.get('schema_version')=='coe-candidate-pilot-plan/0.1.0'
        and config.get('status')=='PENDING_REVIEW_NOT_EXECUTABLE'
        and config.get('execution_commit') is None,'PILOT_PLAN_STATUS')
    require(config['data_role']=='Pilot' and config['run_role']=='PILOT' and config['passes']==['pass1'],'PILOT_ROLE_PASS')
    require(config['block_orders']==[[1,2,4],[2,4,1],[4,1,2]],'PILOT_ORDERS')
    require(re.fullmatch(r'[A-Za-z0-9_-]{1,80}',batch_id) is not None,'PILOT_BATCH_ID')
    e=config['execution'];b=config['budget'];s=config['stopping']
    require(e['warmup_count']==3 and e['repeat_count']==1 and e['input_tokens_per_sample']==512
        and e['output_tokens_per_sample']==2 and e['fresh_process_per_run'] is True
        and e['completion_policy']=='NATURAL_HOST_READABLE_TOKEN_UNCHANGED_NO_CPRE'
        and e['execution_mode']=='eager' and e['dtype']=='fp16' and e['backend']=='sdpa','PILOT_EXECUTION')
    require(b['complete_blocks']==3 and b['model_processes']==9 and b['profiles']==9,'PILOT_BUDGET')
    require(s['automatic_retry'] is False and s['replacement'] is False and s['automatic_more_blocks'] is False,'PILOT_STOP')
    require(config['analysis_scope']=='QUALIFIED_LOCAL_PREFILL_ONLY' and config['primary_comparison']['signed'] is True
        and config['primary_comparison']['statistical_unit']=='COMPLETE_BLOCK','PILOT_ANALYSIS')
    return [dict(run_id=f'{batch_id}-b{bi}-B{batch}-pass1',block=bi,position=pos,batch_size=batch,
        run_role='PILOT',data_role='Pilot',pass_id='pass1',request_semantics='ONE_BATCHED_REQUEST',
        status='PLANNED_NOT_EXECUTABLE') for bi,order in enumerate(config['block_orders'],1) for pos,batch in enumerate(order,1)]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--receipt',type=Path,required=True);p.add_argument('--canonical',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(analyze_files(a.receipt,a.canonical,a.output))


if __name__=='__main__':main()
