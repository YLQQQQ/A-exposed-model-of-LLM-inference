"""N1 native-call -> physical-stream bridge. Narrow nonblocking FIFO only."""
import json
from pathlib import Path
import re

from exposedpath.gate9_stream_bridge import PREFIX, VERSION as BRIDGE_VERSION
from .gate8_files import load_input_receipt, _json, _write
from .gate8_adapter import digest
from .gate9_domain import VERSION, N1, require
from .gate8_scope import load_projected_ownership, build_projected_ab_inputs
from .sync_semantics import load_canonical_bundle, build_semantic_inventory
from .time_representation import SIGNED, time_representation


def bridge_bindings(bundle, projections, bridge, ledger):
    require(bridge.get('schema_version')==BRIDGE_VERSION and bridge.get('pid')==ledger['pid']
            and bridge.get('source_sha256')==ledger['runner_source_sha256'], 'BRIDGE_SOURCE')
    rows=bundle['records']; result=[]; full=[p for p in projections if p['phase']=='full_request']
    activities=build_semantic_inventory(bundle)['activities']
    require(len(bridge['requests'])==len(full), 'BRIDGE_REQUEST_SET')
    used=set(); generations={}
    for projection in full:
        candidates=[r for r in bridge['requests'] if r['identity']==projection['identity']]
        require(len(candidates)==1 and candidates[0]['status']=='COMPLETE', 'BRIDGE_REQUEST')
        request=candidates[0]
        require(request['records'], 'BRIDGE_EMPTY')
        markers=[]
        for row in rows['nvtx']:
            if (row.get('text') or '').startswith(PREFIX):
                payload=json.loads(row['text'][len(PREFIX):])
                if payload['identity']==projection['identity']: markers.append((payload,row))
        lives=[(p,r) for p,r in markers if p['operation']=='lifetime']
        require(len(lives)==1 and len(markers)==len(request['records'])+1, 'BRIDGE_LIFETIME_OR_MARKERS')
        life_payload,life=lives[0]
        handle=life_payload['native_handle']
        require(type(handle) is int and handle>0 and life_payload['logical_device']==0
            and life_payload['generation']==request['generation']
            and life['start_ns']<=projection['start_ns']<=projection['end_ns']<=life['end_ns'], 'BRIDGE_LIFETIME')
        previous=life['start_ns']; actual_scope=None
        for ordinal,record in enumerate(request['records']):
            payload=record['payload']; op=payload['operation']
            require(op in ('submit','copy','wait','internal_wait') and record['operation']==op
                and record['status']=='COMPLETE' and record['error'] is None
                and record['before_native_handle']==record['after_native_handle']==handle
                and payload==dict(schema_version=BRIDGE_VERSION,identity=projection['identity'],
                    generation=request['generation'],logical_device=life_payload['logical_device'],
                    native_handle=handle,operation=op,ordinal=ordinal), 'BRIDGE_OBSERVED_CALL')
            matches=[r for p,r in markers if p==payload]
            require(len(matches)==1, 'BRIDGE_MARKER')
            marker=matches[0]
            require(marker['global_tid']==life['global_tid'] and marker['process_id']==ledger['pid']
                and marker['clock_domain_id']==projection['clock_domain_id']
                and previous<=marker['start_ns']<=marker['end_ns']<=life['end_ns']
                and projection['start_ns']<=marker['start_ns']<=marker['end_ns']<=projection['end_ns'], 'BRIDGE_ORDER_SCOPE')
            previous=marker['end_ns']
            expected={'submit':'cudaLaunchKernel','copy':'cudaMemcpyAsync','wait':'cudaStreamSynchronize','internal_wait':'cudaStreamSynchronize'}[op]
            apis=[a for a in rows['cuda_api'] if a['global_tid']==marker['global_tid']
                and marker['start_ns']<=a['start_ns']<=a['end_ns']<=marker['end_ns']
                and re.fullmatch(re.escape(expected)+r'(?:_v[0-9]+)?',a['api_name'])]
            require(len(apis)==1 and apis[0]['return_value']==0, 'BRIDGE_API')
            api=apis[0]
            require(api['record_id'] not in used, 'BRIDGE_API_ALIAS'); used.add(api['record_id'])
            if op in ('submit','copy'):
                physical=[a for a in activities if a.get('enqueue_record_id')==api['record_id']]
            else:
                physical=[s for s in rows['cuda_sync'] if s['runtime_record_id']==api['record_id'] and s['runtime_mapping_count']==1]
            require(len(physical)==1, 'BRIDGE_CORRELATION')
            physical=physical[0]
            require(physical['process_id']==ledger['pid']
                and physical['global_pid']==marker['global_tid']-marker['global_tid']%2**24
                and physical['clock_domain_id']==projection['clock_domain_id'], 'BRIDGE_PHYSICAL_IDENTITY')
            scope=(physical['device_id'],physical['context_id'],physical['stream_id'])
            if actual_scope is None: actual_scope=scope
            require(scope==actual_scope, 'BRIDGE_PHYSICAL_SCOPE_CONFLICT')
            generation=(handle,request['generation'])
            require(scope not in generations or generations[scope]==generation,'BRIDGE_GENERATION_CONFLICT')
            generations[scope]=generation
            streams=[s for s in rows['stream'] if s['process_id']==ledger['pid'] and s['context_id']==scope[1] and s['stream_id']==scope[2]]
            contexts=[c for c in rows['context'] if c['process_id']==ledger['pid'] and c['context_id']==scope[1] and c['device_id']==scope[0]]
            # TARGET_INFO_CUDA_STREAM.flag is the CUPTI stream-type enum:
            # 1 DEFAULT, 2 NON_BLOCKING, 3 NULL. It is NOT cudaStream flags
            # (where cudaStreamNonBlocking == 1). Preserve the raw encoding.
            require(len(streams)==len(contexts)==1 and streams[0]['flag']==2
                    and contexts[0]['null_stream_id']!=scope[2], 'BRIDGE_EXPLICIT_NONBLOCKING')
            result.append(dict(identity=projection['identity'],generation=request['generation'],native_handle=handle,
                actual_trace_stream_id=scope[2],context_id=scope[1],device_id=scope[0],operation=op,
                correlation_id=api['correlation_id'],api_record_id=api['record_id'],physical_record_id=physical['record_id'],
                marker_record_id=marker['record_id'],lifetime_record_id=life['record_id']))
        # Every observed submitting/synchronizing API in the window must be bound.
        from .a_api_classification import classify_a_api_name
        for a in rows['cuda_api']:
            if a['end_ns']<=projection['start_ns'] or a['start_ns']>=projection['end_ns']: continue
            require(a['global_tid']==life['global_tid'] and a['return_value']==0
                and projection['start_ns']<=a['start_ns']<=a['end_ns']<=projection['end_ns'], 'BRIDGE_OTHER_API_SCOPE')
            if a['record_id'] not in used:
                require(classify_a_api_name(a['api_name'])[0]=='non_submit'
                    and not any(s['runtime_record_id']==a['record_id'] for s in rows['cuda_sync'])
                    and not any(x.get('enqueue_record_id')==a['record_id'] for x in activities), 'BRIDGE_UNBOUND_API')
    return result


def calculate_n1(root,receipt_path,execution_path,bridge_path):
    require(bridge_path is not None, 'BRIDGE_REQUIRED')
    receipt,paths=load_input_receipt(receipt_path)
    execution=_json(execution_path); bridge=_json(bridge_path); ledger=_json(paths['pass_identity'])
    require(execution==dict(schema_version='exposedpath-n1-bridge-execution/0.1.0',
        input_receipt_sha256=digest(Path(receipt_path)),bridge_sha256=digest(Path(bridge_path)),status='COMPLETE'), 'N1_EXECUTION')
    canonical=root/'canonical/canonical_manifest.json'; scope=root/'projection/scope.json'
    bundle=load_canonical_bundle(canonical)
    ownership,projections=load_projected_ownership(canonical,bundle,scope)
    from .gate8_engineering_scope import _diagnostics
    from .gate8_diagnostic_scope import load_diagnostic_scope
    diagnostic=load_diagnostic_scope(root/'diagnostics.json',paths['sqlite'],paths['pass_identity'])
    diagnostics=_diagnostics(diagnostic)
    from .gate9_diagnostic_review import review
    diagnostic_review=review(diagnostic,bundle)
    bindings=bridge_bindings(bundle,projections,bridge,ledger)
    from .gate8_closed_prior import LIFETIME_PREFIX
    import shutil
    lifetime=[]
    for marker in bundle['records']['nvtx']:
        if (marker.get('text') or '').startswith(LIFETIME_PREFIX):
            payload=json.loads(marker['text'][len(LIFETIME_PREFIX):])
            activities=[a for a in bundle['records']['device_activity'] if marker['start_ns']<=a['start_ns']<=a['end_ns']<=marker['end_ns']]
            require(activities, 'LIFETIME_BINDING_MISSING')
            require(all(b['generation']==payload['generation'] for b in bindings
                if b['physical_record_id'] in {a['record_id'] for a in activities}), 'LIFETIME_GENERATION')
            lifetime.append(dict(marker_record_id=marker['record_id'],binding_activity_id=activities[0]['record_id']))
    cert=dict(schema_version='exposedpath-closed-prior-evidence/0.1.0',canonical_manifest_sha256=digest(canonical),
        scope_sha256=digest(scope),drain_ledger={'filename':'drain.json','sha256':digest(paths['drain_ledger'])},lifetimes=lifetime)
    # Deterministic sidecars are written once, then rechecked on load.
    if not (root/'drain.json').exists(): shutil.copyfile(paths['drain_ledger'],root/'drain.json')
    require(digest(root/'drain.json')==digest(paths['drain_ledger']), 'DRAIN_SOURCE')
    if not (root/'closed.json').exists(): _write(root/'closed.json',cert)
    require(_json(root/'closed.json')==cert, 'CLOSED_SOURCE')
    with time_representation(SIGNED):
        inputs=build_projected_ab_inputs(canonical,scope,closed_prior_manifest=root/'closed.json')
        from .a_accounting import calculate_a_windows
        from .b_provenance import calculate_b_syncs
        a=list(calculate_a_windows(inputs)); b=list(calculate_b_syncs(inputs))
    require(not inputs.global_quality_reasons, 'CANONICAL_QUALITY')
    measured={r['identity']['request_id'] for r in ledger['requests'] if r['request_role']=='measured'}
    selected_b=[r for r in b if r['request_id'] in measured]
    require(selected_b and all(r['validity']=='B_VALID' for r in selected_b), 'N1_PHYSICAL_B_UNQUALIFIED')
    bound_sync={r['physical_record_id'] for r in bindings if r['operation'] in ('wait','internal_wait') and r['identity']['request_id'] in measured}
    require({r['sync_id'] for r in selected_b}==bound_sync, 'N1_SYNC_SET')
    require(a and all(r['A_unattributed_ns']==0 and r['primary_reason'] is None and not r['secondary_reasons'] for r in a), 'N1_A_UNQUALIFIED')
    return dict(schema_version=VERSION,declaration=_json(paths['wmpc_manifest'])['domain_qualification'],identity=receipt['identity'],
        status='QUALITY_CHECK_PASSED_NOT_QUALIFICATION',bridge_bindings=bindings,
        a_records=[r for r in a if r['request_id'] in measured],
        warmup_a_records=[r for r in a if r['request_id'] not in measured],b_records=selected_b,physical_b_records=b,
        physical_s_records=list(inputs.s_records),input_receipt_sha256=digest(Path(receipt_path)),
        execution_receipt_sha256=digest(Path(execution_path)),bridge_sha256=digest(Path(bridge_path)),
        diagnostic_dispositions=diagnostics,dropped_records_status='UNKNOWN',measurement_validity='NOT_ASSESSED',
        formal_eligible=False,gate9_verdict='NOT_RUN',d_score_allowed=False,signature_allowed=False,
        **({'diagnostic_review':diagnostic_review} if diagnostic_review is not None else {}))
