"""Independent candidate-budget adapter over already admitted evidence.

No new S recovery, production A/B modification, or qualification. The old
partition is audited against *every* original A category before any migration.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path

from .coe_candidate import (ROLE, VERSION as CANDIDATE_VERSION, clipped_union,
    interval, one, preview_budget, require, sha)
from exposedpath_v141.a_api_classification import _classify, VERSION as REGISTRY_VERSION
from exposedpath_v141.a_accounting import _covering_by_segment
from exposedpath_v141.intervals import atomic_segments

VERSION='coe-budget-preview/0.2.0'
CATEGORIES=dict(host='A_host_path_ns',submit='A_cuda_api_submit_ns',non_submit='A_cuda_api_non_submit_ns',
    device_wait='A_device_wait_ns',residual='A_sync_residual_ns',unattributed='A_unattributed_ns')


def _indexed(rows):
    require(len({r['record_id'] for r in rows})==len(rows),'RECORD_DUPLICATE')
    for r in rows:interval(r['start_ns'],r['end_ns'])
    return {r['record_id']:r for r in rows}


def _length(pieces):return sum(b-a for a,b in pieces)


def calculate_preview(candidate, admission, records):
    """Reuses closed-prior admission + its two-mode S proof, not overlap as W.

    API categories come from the existing registry; sync precedence and unions
    follow the frozen A contract. Disagreement with saved A rejects this audit.
    """
    require(candidate.get('version')==CANDIDATE_VERSION and candidate.get('role')==ROLE,'CANDIDATE_VERSION')
    require(admission.get('status')=='A_SCOPE_ENGINEERING_ONLY' and not admission.get('reasons'),'ADMISSION_INVALID')
    identity=admission['identity'];facts=admission['facts']
    require(candidate['source_sqlite_sha256'].lower()==facts['source_sqlite_sha256'].lower(),'SOURCE')
    require(all(candidate['source_identity'].get(k)==v for k,v in identity.items()
        if k not in ('request_id','repeat_id','formal_reference')),'IDENTITY')
    windows=admission['a_records'];by_phase={a['phase']:a for a in windows}
    require(len(windows)==3 and set(by_phase)=={'full_request','prefill','decode'},'WINDOWS')
    req,pre,dec=(by_phase[p] for p in ('full_request','prefill','decode'))
    require(req['window_start_ns']==pre['window_start_ns'] and pre['window_end_ns']==dec['window_start_ns']
        and dec['window_end_ns']==req['window_end_ns'],'WINDOWS')
    for a in windows:
        interval(a['window_start_ns'],a['window_end_ns'])
        require(all(a.get(k)==identity[k] for k in ('experiment_id','wmpc_id','run_id','run_role','pass_id','request_id','repeat_id')),'IDENTITY')
        require(not a['primary_reason'] and not a['secondary_reasons'],'ORIGINAL_A_INVALID')
    apis=_indexed(records['cuda_api']);effects=_indexed(records['device_activity'])
    raw_sync={s['record_id']:s for s in records['cuda_sync']}
    require(len(raw_sync)==len(records['cuda_sync']),'SYNC_MAPPING_DUPLICATE')
    proofs=facts['conditional_suffix_proofs']
    require(len(proofs)==2 and {p['mode'] for p in proofs}=={'LEGACY','PER_THREAD'}
        and proofs[0]['syncs']==proofs[1]['syncs'],'MODE_PROOF')
    syncs=[];waits=[];proof_by_api={}
    for p in proofs[0]['syncs']:
        require(p['scope']=='A_INTERSECTION_ONLY_NOT_PHYSICAL_W','PROOF_SCOPE')
        s=raw_sync.get(p['sync_id']);require(s is not None,'SYNC_MAPPING')
        api=apis.get(s['runtime_record_id']);require(api is not None,'SYNC_MAPPING')
        ids=p['suffix_activity_ids']
        require(len(set(ids))==len(ids),'MEMBER_DUPLICATE')
        require(all(k in effects for k in ids),'MEMBER_MISSING')
        proof_by_api[api['record_id']]=set(ids)
        syncs.append(dict(start=api['start_ns'],end=api['end_ns'],id=p['sync_id']))
        waits.extend((max(api['start_ns'],effects[k]['start_ns']),min(api['end_ns'],effects[k]['end_ns']))
            for k in ids if max(api['start_ns'],effects[k]['start_ns'])<min(api['end_ns'],effects[k]['end_ns']))
    observed=facts['observed_api_ids']
    require(len(set(observed))==len(observed) and all(k in apis for k in observed),'API_COVERAGE')
    start,end=req['window_start_ns'],req['window_end_ns']
    selected=[apis[k] for k in observed]
    process_ids={r['process_id'] for r in selected if 'process_id' in r}
    require(len(process_ids)<=1,'API_SCOPE')
    complete={r['record_id'] for r in apis.values() if start<=r['start_ns']<end and
        (not process_ids or r.get('process_id') in process_ids)}
    require(complete==set(observed),'API_COVERAGE')
    require(all(start<=r['start_ns']<=r['end_ns']<=end for r in selected),'API_SCOPE')
    q_by_op=[];positions=[];operation_ids=set()
    for op in candidate['operations']:
        require(op['operation_validity']=='VALID_UNDER_DECLARED_SUPPORT_ASSUMPTIONS' and not op['reasons'],'OPERATION_INVALID')
        require(op['identity']==identity,'OPERATION_IDENTITY')
        require(op['operation_id'] not in operation_ids,'OPERATION_DUPLICATE');operation_ids.add(op['operation_id'])
        members=op['members'];require(len(set(members))==len(members),'MEMBER_DUPLICATE')
        require(all(k in effects for k in members),'MEMBER_MISSING')
        require(op['sync_id'] in proof_by_api and set(members)==proof_by_api[op['sync_id']],'MEMBER_PROOF')
        require(op['copy_id'] in observed and op['sync_id'] in observed,'PAIR_COVERAGE')
        lo,hi=op['copy_interval'][0],op['sync_interval'][1]
        require(op['copy_interval']==[apis[op['copy_id']]['start_ns'],apis[op['copy_id']]['end_ns']]
            and op['sync_interval']==[apis[op['sync_id']]['start_ns'],apis[op['sync_id']]['end_ns']],'PAIR_INTERVAL')
        phase=by_phase.get(op['phase']);require(phase is not None and phase['window_start_ns']<=lo<=hi<=phase['window_end_ns'],'OPERATION_WINDOW')
        spans=[(effects[k]['start_ns'],effects[k]['end_ns']) for k in members]
        q=clipped_union(lo,hi,spans)
        require(q==[tuple(p) for p in op['activity_union']] and _length(q)==op['candidate_ns'],'OPERATION_INTERVAL_MISMATCH')
        q_by_op.append((op,q))
        total=clipped_union(start,hi,spans)
        before=clipped_union(start,lo,spans)
        after=clipped_union(hi,end,spans)
        submits=op.get('member_submits')
        position={}
        if submits is not None:
            require(len(submits)==len(members) and {s['record'] for s in submits}==set(members)
                and all(s['submit'] in apis for s in submits),'SUBMIT_MAPPING')
            preceding=[apis[s['submit']] for s in submits if apis[s['submit']]['end_ns']<=lo]
            kernels=[effects[k] for k in members if effects[k]['activity_kind']=='KERNEL']
            require(preceding and kernels,'POSITION_EVIDENCE')
            last=max(r['end_ns'] for r in preceding);last_kernel=max(r['end_ns'] for r in kernels)
            position=dict(L_ns=last,C_ns=lo,K_ns=last_kernel,H_ns=lo-last,D_ns=last_kernel-last,
                clock='NSYS_TRACE_RELATIVE_NS',terminal_ns=op['terminal_end_ns'])
        positions.append(dict(operation_id=op['operation_id'],token_index=op['token_index'],phase=op['phase'],
            member_ids=members,closed_prior_ids=op['closed_prior'],
            position_scope='QUALIFIED_REQUEST_SUFFIX_CUMULATIVE_NOT_PHASE_INCREMENT',
            position_union_ns=dict(before_copy=_length(before),inside_operation=_length(q),after_operation=_length(after),
                total_qualified_suffix=_length(total)),
            candidate_ns=op['candidate_ns'],original_sync_ns=op['original_sync_ns'],kernel_ns=op['kernel_ns'],
            memop_ns=op['memop_ns'],operation_wall_ns=op['wall_ns'],uncovered_ns=op['uncovered_ns'],
            kernel_memop_overlap_ns=op['kernel_ns']+op['memop_ns']-op['candidate_ns'],
            copy_wall_ns=op['copy_interval'][1]-lo,sync_wall_ns=op['sync_interval'][1]-op['sync_interval'][0],
            positions=position))
    require(q_by_op,'OPERATION_MISSING')
    # Split at all relevant endpoints and phase boundaries, then sweep once.
    wait_union=clipped_union(start,end,waits)
    boundaries=[pre['window_end_ns']]
    boundaries += [x for r in selected for x in (r['start_ns'],r['end_ns'])]
    boundaries += [x for r in syncs for x in (r['start'],r['end'])]
    boundaries += [x for p in wait_union for x in p]
    boundaries += [x for op,q in q_by_op for k in op['members'] for x in
        (max(start,effects[k]['start_ns']),min(end,effects[k]['end_ns'])) if start<=x<=end]
    boundaries += [x for _,q in q_by_op for p in q for x in p]
    segments=list(atomic_segments((start,end),boundaries));atoms=[]
    api_items=[(r,(r['start_ns'],r['end_ns'])) for r in selected]
    sync_items=[(r,(r['start'],r['end'])) for r in syncs]
    wait_items=[(None,p) for p in wait_union]
    for (a,b),aa,ss,ww in zip(segments,_covering_by_segment(api_items,segments),
            _covering_by_segment(sync_items,segments),_covering_by_segment(wait_items,segments)):
        if ww:category='device_wait'
        elif ss:category='residual'
        elif aa:
            cats={_classify(r['api_name'],REGISTRY_VERSION)[0] for r,_ in aa}
            category=next(iter(cats)) if len(cats)==1 and None not in cats else 'unattributed'
        else:category='host'
        atoms.append(dict(start=a,end=b,category=category,api_ids=sorted(r['record_id'] for r,_ in aa),
            sync_ids=sorted(r['id'] for r,_ in ss)))
    outputs=[]
    for original in windows:
        w=[original['window_start_ns'],original['window_end_ns']]
        local=[dict(r,start=max(w[0],r['start']),end=min(w[1],r['end'])) for r in atoms if r['start']<w[1] and w[0]<r['end']]
        totals={k:sum(r['end']-r['start'] for r in local if r['category']==k) for k in CATEGORIES}
        require(all(totals[k]==original[field] for k,field in CATEGORIES.items())
            and totals['submit']+totals['non_submit']==original['A_cuda_api_ns']
            and sum(totals.values())==original['T_window_ns'],'ORIGINAL_A_MISMATCH')
        preview=preview_budget(w,local,[q for _,q in q_by_op])
        for m in preview['migration']:
            atom=one((r for r in local if r['start']<=m['start']<m['end']<=r['end']),'MIGRATION_SOURCE')
            active=[op for op,q in q_by_op if any(a<=m['start']<m['end']<=b for a,b in q)]
            m.update(api_ids=atom['api_ids'],sync_ids=atom['sync_ids'],
                operation_ids=sorted(op['operation_id'] for op in active),activity_ids=sorted({k for op in active
                    for k in op['members'] if effects[k]['start_ns']<=m['start']<m['end']<=effects[k]['end_ns']}))
        budget=preview['budgets_ns'].copy();budget['completion_exposure']=budget.pop('device_wait')
        outputs.append(dict(phase=original['phase'],original_a=deepcopy(original),candidate_budgets_ns=budget,
            candidate_cuda_api_ns=preview['cuda_api_ns'],migrated_ns=preview['migrated_ns'],migration=preview['migration'],
            coe_union_ns=_length(clipped_union(*w,[p for _,q in q_by_op for p in q]))))
    o={w['phase']:w for w in outputs}
    require(all(o['full_request']['candidate_budgets_ns'][k]==o['prefill']['candidate_budgets_ns'][k]+o['decode']['candidate_budgets_ns'][k]
        for k in o['full_request']['candidate_budgets_ns']),'REQUEST_PHASE_SUM')
    return dict(schema_version=VERSION,role=ROLE,identity=identity,source_sqlite_sha256=candidate['source_sqlite_sha256'],
        windows=outputs,operations=positions,operation_coverage=candidate.get('coverage'),request_equals_phase_sum=True,
        production_A_B_modified=False,full_physical_W_qualified=False,pure_host_stall_ns=None,
        dropped_records_status='UNKNOWN',measurement_validity='NOT_ASSESSED')


def preview_files(candidate_path, admission_path, canonical_path, output):
    """Actual saved sensitivity -> saved candidate/hash -> Canonical -> preview.

    This is an evidence-consumption route, not a replacement acceptance gate.
    """
    from exposedpath_v141.sync_semantics import load_canonical_bundle
    paths=[Path(p).resolve() for p in (candidate_path,admission_path,canonical_path)]
    require(not Path(output).exists(),'NO_OVERWRITE')
    candidate=json.loads(paths[0].read_text(encoding='utf8'));saved=json.loads(paths[1].read_text(encoding='utf8'))
    require(saved['candidate_sha256']==sha(paths[0]),'CANDIDATE_HASH')
    require(saved.get('schema_version')=='observation-preparation-result/0.1.0','ADMITTED_RESULT_VERSION')
    require(len(saved['token_ids'])==len(candidate['operations']) and
        [o['token_index'] for o in candidate['operations']]==list(range(len(saved['token_ids']))),'TOKEN_COVERAGE')
    bundle=load_canonical_bundle(paths[2]);manifest=bundle['manifest']
    require(manifest['source']['sqlite']['sha256'].lower()==candidate['source_sqlite_sha256'].lower(),'CANONICAL_SOURCE')
    paths += [paths[2].parent/e['filename'] for e in manifest['files'].values()]
    source_hashes=candidate['source_hashes']
    for p in paths[2:]:
        suffix='/canonical/'+p.name
        bound=[h for k,h in source_hashes.items() if str(k).replace('\\','/').endswith(suffix)]
        require(len(bound)==1 and bound[0].lower()==sha(p),'CANONICAL_HASH_BINDING')
    hashes={str(p):sha(p) for p in paths}
    require(not any(p.is_relative_to(Path(output).resolve()) for p in paths),'OUTPUT_CONTAINS_INPUT')
    result=calculate_preview(candidate,saved['local_admission'],bundle['records'])
    root=Path(__file__).resolve().parents[1]
    modules=('analysis/coe_budget_preview.py','analysis/coe_candidate.py',
        'exposedpath_v141/a_api_classification.py','exposedpath_v141/a_accounting.py',
        'exposedpath_v141/intervals.py','exposedpath_v141/sync_semantics.py',
        'scripts/analyze_completion_operation_candidate.py','docs/v1_4_1/contracts/a_api_registry_v0_1.json')
    code_hashes={p:sha(root/p) for p in modules}
    result.update(source_hashes=hashes,analysis_code_sha256=sha(Path(__file__)),
        analysis_sources=code_hashes,registry_version=REGISTRY_VERSION)
    require(all(sha(p)==h for p,h in hashes.items()),'SOURCE_CHANGED')
    require(all(sha(root/p)==h for p,h in code_hashes.items()),'ANALYSIS_SOURCE_CHANGED')
    Path(output).mkdir(parents=True,exist_ok=False)
    path=Path(output)/'budget_preview.json'
    path.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')),encoding='utf8')
    return path


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('candidate','admission','canonical','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(preview_files(a.candidate,a.admission,a.canonical,a.output))


if __name__=='__main__':main()
