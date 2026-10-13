"""Native point/real-call bridge to existing S/A. Calculation is NOT qualification.

No Raw replacement, CUDA access, fake callsite, classifier fallback or opaque
allocation exception. A global mode is not inferred from a handle/trace ID.
"""
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
import tempfile

from exposedpath import native_llama as contract
from exposedpath.gate8_identity import make_gate8_pass_identity, PASS_FIELDS
from .gate8_adapter import resolve_device_mapping
from .gate8_scope import ProjectedScope
from .gate8_files import _write,_entry,_resolve
from .sync_semantics import load_canonical_bundle,build_semantic_inventory,analyze_sync_semantics,build_semantic_sync_candidates
from .time_representation import SIGNED,time_representation
from .ab_inputs import CanonicalBundle,ABInputs,RequestPhaseWindow,_validate_s_join,_global_quality_reasons

VERSION='exposedpath-native-llama-scope/0.1.0'


def _calculate(canonical,spec_path,producer,sqlite,preflight,raw,work):
    canonical,spec_path,producer,sqlite,preflight,raw=map(Path,(canonical,spec_path,producer,sqlite,preflight,raw))
    spec=contract.load_spec(spec_path);host=contract._read(producer)
    contract.read_producer(spec_path,producer)
    contract.require(spec['identity']['pass_id']=='pass1','PROFILE_PASS')
    bundle=load_canonical_bundle(canonical);manifest=bundle['manifest'];rows=bundle['records']
    contract.require(manifest['data_role']=='Engineering' and manifest['identity']['status']=='VALID'
        and all(manifest['identity']['values'][k]==spec['identity'][k]
            for k in manifest['identity']['values']),'CANONICAL_IDENTITY')
    contract.require(manifest['source']['sqlite']['sha256'].lower()==contract.digest(sqlite)
        and manifest['source']['raw']['sha256'].lower()==contract.digest(raw),'RAW_LINEAGE')
    from .gate8_diagnostic_scope import _require_sealed
    _require_sealed(sqlite)
    pre=contract._read(preflight)
    contract.require(contract._gpu(pre)==contract._gpu(spec['expected_gpu']),'PREFLIGHT_CONFLICT')
    probe=dict(host['actual_gpu'],pid=host['pid'])
    # resolve_device_mapping calls this ordinal fact pci_bus_id; no ordinal equality shortcut.
    with sqlite3.connect(sqlite.resolve().as_uri()+'?mode=ro&immutable=1',uri=True) as db:
        db.row_factory=sqlite3.Row
        mapping=resolve_device_mapping(db,sqlite_sha256=contract.digest(sqlite),preflight=pre,probe=probe,
            pid=host['pid'],preflight_sha256=contract.digest(preflight),probe_sha256=contract.digest(producer),records=rows)
    points=[];selected=[]
    for row in rows['nvtx']:
        if (row.get('text') or '').startswith(contract.PREFIX):
            payload=json.loads(row['text'][len(contract.PREFIX):])
            ordinal=len(points)
            contract.require(ordinal<3 and payload==host['boundaries'][ordinal]['payload']
                and row['end_ns'] is None and row['process_id']==host['pid']
                and row['thread_id']==host['tid'],'POINT_IDENTITY')
            points.append(row)
    contract.require(len(points)==3 and len({r['clock_domain_id'] for r in points})==1
        and all(a['start_ns']<b['start_ns'] for a,b in zip(points,points[1:])),'POINT_MISSING_OR_CLOCK')
    gpid=points[0]['global_tid']-points[0]['global_tid']%2**24
    contract.require(all(r['global_tid']==points[0]['global_tid'] for r in points),'PROCESS_INSTANCE')
    projections=[];owner=[]
    for i,(phase,start,end) in enumerate((('full_request',points[0],points[2]),
        ('prefill',points[0],points[1]),('decode',points[1],points[2]))):
        value=dict(schema_version=VERSION,identity=spec['identity'],phase=phase,
            start_ns=start['start_ns'],end_ns=end['start_ns'],clock_domain_id=start['clock_domain_id'],
            start_ref={k:start[k] for k in ('record_id','source_table','source_rowid')},
            end_ref={k:end[k] for k in ('record_id','source_table','source_rowid')},
            source_sqlite_sha256=contract.digest(sqlite),spec_sha256=contract.digest(spec_path),
            producer_sha256=contract.digest(producer),dependency_evidence=False)
        projections.append(value)
        owner.append(ProjectedScope(record_id=f'native-projection:{contract.digest(spec_path)}:{i}',
            source_kind='SCOPE_PROJECTION',projection=value,start_ns=value['start_ns'],end_ns=value['end_ns'],
            clock_domain_id=value['clock_domain_id'],global_tid=start['global_tid'],
            process_id=start['process_id'],thread_id=start['thread_id'],text=None,
            structured_identity=dict(spec['identity'],kind='request' if i==0 else 'phase',phase=phase)))
    # Legacy observed request/phase ranges may not silently override new anchors.
    contract.require(not any((r.get('structured_identity') or {}).get('kind') in ('request','phase') for r in rows['nvtx']),'CONFLICTING_RANGE')
    ownership=[*rows['nvtx'],*owner]
    enriched=deepcopy(manifest)
    enriched['execution_context']['selected_device_id']=mapping['trace_device_id']
    base=build_semantic_inventory({**bundle,'manifest':enriched,'ownership_records':ownership})
    calls=host['sync_calls'];matched=[];bridges=[]
    for s in base['syncs']:
        if not (points[0]['start_ns']<=s.get('host_start_ns',-1)<=s.get('host_end_ns',-1)<=points[2]['start_ns']):
            continue
        api=next((a for a in rows['cuda_api'] if a['record_id']==s['runtime_record_id']),None)
        markers=[r for r in rows['nvtx'] if r.get('structured_identity')
            and r['structured_identity'].get('native_profile')==contract.PROFILE
            and api is not None and r['global_tid']==api['global_tid']
            and r['start_ns']<=api['start_ns']<=api['end_ns']<=r['end_ns']]
        contract.require(len(markers)==1 and api is not None and api['return_value']==0
            and s['runtime_mapping_count']==1 and s['sync_kind']=='STREAM'
            and s['role']=='HOST_BLOCKING_SYNC','SYNC_MAPPING_OR_UNSUPPORTED')
        m=markers[0];payload=m['structured_identity']
        matches=[i for i,c in enumerate(calls) if c['payload']==payload]
        contract.require(len(matches)==1 and matches[0] not in matched,'CALL_LEDGER')
        c=calls[matches[0]]
        contract.require(c['return_value']==0 and c['pid']==host['pid'] and c['tid']==api['thread_id']
            and all(payload.get(k)==v for k,v in spec['identity'].items())
            and payload['spec_sha256']==contract.digest(spec_path)
            and payload['cuda_device']==host['actual_gpu']['gpu_index_logical']
            and payload['native_handle'].isdecimal()
            and s['device_id']==mapping['trace_device_id']
            and api['clock_domain_id']==m['clock_domain_id']==s['clock_domain_id']
            and s['correlation_id']==api['correlation_id']
            and payload['callsite_id'] in {'llama.cpp.'+n for n in contract.SYNC_CALLSITES}
            and payload['sync_origin']=='native_backend_synchronize'
            and payload['schema_version']=='exposedpath-native-sync/0.1.0','CALL_SCOPE')
        matched.append(matches[0]);selected.append(s['record_id'])
        bridges.append(dict(api_record_id=api['record_id'],sync_record_id=s['record_id'],
            marker_record_id=m['record_id'],correlation_id=api['correlation_id'],pid=host['pid'],
            tid=api['thread_id'],context_id=s['context_id'],trace_stream_id=s['stream_id'],
            native_handle=payload['native_handle'],cuda_device=payload['cuda_device'],
            backend_device_index=payload['backend_device_index'],clock_domain_id=api['clock_domain_id']))
    contract.require(selected and len(matched)==len(calls),'CALL_OR_RAW_SYNC_MISSING')
    from .a_api_classification import classify_a_api_name
    from .sync_semantics import classify_cuda_api
    for a in rows['cuda_api']:
        if a['process_id']!=host['pid'] or not (points[0]['start_ns']<=a['start_ns']<points[2]['start_ns']):continue
        category,rule=classify_a_api_name(a['api_name'])
        effects=[v for v in base['activities'] if v.get('enqueue_record_id')==a['record_id']]
        if category=='submit' and classify_cuda_api(a['api_name'])['role']!='DEPENDENCY_EDGE':
            contract.require(a['return_value']==0 and effects,'SUBMISSION_EFFECT_MISSING')
        if rule=='A-OPAQUE-RESOURCE-CUDAMALLOC':
            contract.require(False,'OPAQUE_ALLOCATION_NOT_AUTHORIZED_FOR_NATIVE')
    for handle in {b['native_handle'] for b in bridges}:
        contract.require(len({(b['context_id'],b['trace_stream_id']) for b in bridges if b['native_handle']==handle})==1,'HANDLE_REUSE_OR_CONFLICT')
    # Generic identity envelope only; does not assert the old resident-input boundary.
    ledger=make_gate8_pass_identity(**{k:spec['identity'][k] for k in PASS_FIELDS},pid=host['pid'],
        wmpc_manifest_sha256=contract.digest(spec_path),prompt_sha256=spec['sources']['token_input']['sha256'],
        runner_source_sha256=contract._read(spec['sources']['build_receipt']['path'])['native_source_sha256'],
        runner_git_commit=spec['execution_commit'],runner_git_dirty=False,requests=[dict(
            request_id=spec['identity']['request_id'],repeat_id=spec['identity']['repeat_id'],request_role='measured',
            expected_output_tokens=2,actual_output_tokens=2,early_eos=False,outcome='COMPLETE',reasons=[],
            expected_boundary_ids=[b['payload']['boundary_id'] for b in host['boundaries']],
            observed_boundary_ids=[b['payload']['boundary_id'] for b in host['boundaries']])])
    _write(work/'diagnostic_identity.json',ledger)
    from .gate8_diagnostic_scope import write_diagnostic_scope
    from .gate9_diagnostic_review import review
    diagnostic=write_diagnostic_scope(sqlite,work/'diagnostic_identity.json',work/'diagnostics.json')
    diagnostic_review=review(diagnostic,bundle) # reuse the accepted official rule, unchanged
    # Never infer a global mode from handle=0/ID. Equality includes complete W,
    # dependency edges, ownership, terminal, validity and reasons, not just A.
    results=[]
    with time_representation(SIGNED):
        for mode in ('LEGACY','PER_THREAD'):
            inv=deepcopy(base);inv['default_stream_mode']=mode
            results.append(tuple(analyze_sync_semantics(inv,s) for s in inv['syncs']))
        contract.require(results[0]==results[1],'DEFAULT_STREAM_MODE_AMBIGUOUS')
        s_records=results[0]
        contract.require(all(s['validity'] in ('VALID_NONEMPTY','VALID_EMPTY')
            for s in s_records if s['sync_id'] in selected),'SYNC_DEPENDENCY_OR_TERMINAL')
        records={k:tuple(v) for k,v in rows.items()}
        candidates=build_semantic_sync_candidates(records,ownership)
        cb=CanonicalBundle(manifest=enriched,records=records,schema=bundle['schema'],
            cuda_api_by_id={r['record_id']:r for r in rows['cuda_api']},
            activity_by_id={r['record_id']:r for r in rows['device_activity']},
            physical_sync_by_id={c.sync_id:c for c in candidates},projected_ownership=tuple(ownership))
        _validate_s_join(cb,s_records)
        windows=tuple(RequestPhaseWindow(window_id=r['record_id'],
            **{k:spec['identity'][k] for k in ('experiment_id','wmpc_id','run_id','run_role','pass_id','request_id','repeat_id')},
            phase=r['structured_identity']['phase'],start_ns=r['start_ns'],end_ns=r['end_ns'],nvtx_record_id=r['record_id']) for r in owner)
        inputs=ABInputs(canonical=cb,s_manifest={'qualification':'NOT_RUN'},s_records=s_records,windows=windows,
            global_quality_reasons=_global_quality_reasons(cb),window_discovery_issues=())
        from .a_accounting import calculate_a_windows
        a=list(calculate_a_windows(inputs))
    return dict(schema_version=VERSION,status='ADAPTER_CALCULATION_ONLY_NOT_QUALIFICATION',
        qualification='NOT_RUN',formal_eligible=False,dropped_records_status='UNKNOWN',measurement_validity='NOT_ASSESSED',
        physical_b_qualified=False,d_score_allowed=False,signature_allowed=False,
        projections=projections,device_mapping=mapping,call_bridges=bridges,s_records=list(s_records),a_records=a,
        diagnostic_review=diagnostic_review,default_stream_mode='UNKNOWN',mode_basis='FULL_S_CONDITIONAL_EQUIVALENCE',
        input_hashes={k:contract.digest(p) for k,p in dict(canonical=canonical,spec=spec_path,producer=producer,
            sqlite=sqlite,preflight=preflight,raw=raw).items()})


def write_review(canonical,spec,producer,sqlite,preflight,raw,output):
    output=Path(output).resolve()
    if output.exists():raise FileExistsError(output)
    sources=[Path(p).resolve() for p in (canonical,spec,producer,sqlite,preflight,raw)]
    contract.require(not any(p.is_relative_to(output) for p in sources)
        and not output.is_relative_to(sources[0].parent),'OUTPUT_INPUT_OVERLAP')
    hashes={p:contract.digest(p) for p in sources}
    output.parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='.'+output.name+'-partial-',dir=output.parent))
    result=_calculate(*sources,work)
    contract.require(all(contract.digest(p)==h for p,h in hashes.items()),'SOURCE_CHANGED')
    result['files']=[_entry(p,work) for p in sorted(work.rglob('*')) if p.is_file()]
    _write(work/'native_scope.json',result)
    work.rename(output)
    return output/'native_scope.json'


def load_review(result,*sources):
    result=Path(result);saved=contract._read(result)
    contract.require(saved.get('schema_version')==VERSION,'RESULT_VERSION')
    files=[_resolve(result.parent,r) for r in saved['files']]
    contract.require(len(files)==len(set(files)) and set(files)=={p.resolve() for p in result.parent.rglob('*') if p.is_file() and p!=result},'RESULT_FILE_SET')
    # Revalidate all file inputs and calculations, never trust saved accounting.
    scratch=Path(tempfile.mkdtemp(prefix='.native-revalidate-',dir=result.parent.parent))
    actual=_calculate(*sources,scratch)
    contract.require({k:v for k,v in saved.items() if k!='files'}==actual,'RESULT_CHANGED')
    return saved
