"""Explicit Engineering A intersection; physical S/B and old entry unchanged.

No collector calls or zero-loss assertion. The formal gate has no warning bypass;
an explicitly requested hypothesis uses a separate, non-acceptance derivative.
Only predeclared executions are eligible. Signed times stay in trace clock.
"""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import re
import tempfile

from exposedpath.gate8_engineering_contract import PROFILE, EXECUTION_VERSION, CONTROLLED_EXECUTION_VERSION, CONSTRUCTION, validate_declaration
from .gate8_adapter import digest
from .gate8_files import load_input_receipt, _json, _write, _entry, _resolve
from .gate8_diagnostic_scope import write_diagnostic_scope, load_diagnostic_scope
from .gate8_scope import build_projected_ab_inputs, load_projected_ownership
from .gate8_request_scope import _drain, _same_request
from .sync_semantics import load_canonical_bundle, build_semantic_inventory, recover_wait_set, _semantic_frontier
from .time_representation import SIGNED, time_representation
from .a_api_classification import classify_a_api_name, VERSION as A_API_VERSION, REGISTRY_PATH as A_API_REGISTRY

VERSION = 'exposedpath-engineering-a-scope/0.1.0'
SUBMIT_APIS = {'cudaLaunchKernel', 'cuLaunchKernel', 'cudaMemcpyAsync', 'cudaMemsetAsync'}


def require(ok, reason):
    if not ok:
        raise ValueError('ENGINEERING_SCOPE_' + reason)


def _inputs(receipt_path, execution_path):
    receipt, paths = load_input_receipt(receipt_path)
    require(re.fullmatch(r'2026\.2\.1\.210(?:-262137639646v0)?',receipt['collector_version']) is not None,
            'COLLECTOR_VERSION')
    require({'drain_ledger','stage_ledger'} <= paths.keys(), 'PRODUCER_SOURCES')
    manifest, ledger, execution = _json(paths['wmpc_manifest']), _json(paths['pass_identity']), _json(execution_path)
    declared = validate_declaration(manifest)
    controlled=manifest.get('construction')==CONSTRUCTION
    extension=set(); expected_version=EXECUTION_VERSION
    if not controlled:
        from exposedpath.gate11_pilot import execution_extension
        extension,expected_version=execution_extension(manifest,ledger,execution,execution_path,paths['wmpc_manifest'],paths['producer_receipt'],token_path=paths.get('pilot_tokens'))
    require(set(execution)=={'schema_version','manifest_sha256','producer_receipt_sha256',
            'identity','declaration','observed_configuration','status'} | extension
        and execution['schema_version']==(CONTROLLED_EXECUTION_VERSION if controlled else expected_version)
        and execution['manifest_sha256']==digest(paths['wmpc_manifest'])
        and execution['producer_receipt_sha256']==digest(paths['producer_receipt'])
        and execution['identity']=={k:ledger[k] for k in ('run_id','pass_id','attempt_id','pid')}
        and execution['declaration']==declared and execution['status']=='COMPLETE', 'EXECUTION_IDENTITY')
    observed=execution['observed_configuration']
    if controlled:
        require(observed==dict(construction=CONSTRUCTION,warmup_token=0,model_workload=False),'CONTROLLED_CONFIGURATION')
        require(len(ledger['requests'])==2 and all(r['request_role']=='measured' for r in ledger['requests']),'CONTROLLED_PLAN')
    else:
        _model_configuration(observed,declared)
    from exposedpath.gate11_warmup import active
    if active(manifest.get('pilot')):
        from exposedpath.gate11_pilot import validate_actual_requests
        validate_actual_requests(manifest,ledger)
    else:
        require(all(r['outcome']=='COMPLETE' and not r['early_eos'] and not r['reasons']
                    and r['actual_output_tokens']==r['expected_output_tokens']>=2 for r in ledger['requests']), 'REQUEST_PLAN')
    return receipt, paths, declared, execution


def _model_configuration(observed,declared):
    require(set(observed)=={'configured_attention_backend','configured_use_cache','model_type','execution_mode'}
        and observed['configured_attention_backend']==declared['attention_backend']
        and observed['execution_mode']=='eager' and observed['configured_use_cache'] is True
        and isinstance(observed['model_type'],str) and bool(observed['model_type']), 'LOADED_CONFIGURATION')


def _diagnostics(diagnostic):
    # This version has no evidence-backed warning-scope resolver. Every warning
    # (including foreign PID) and unknown informational message therefore blocks.
    # Exact benign informational forms are NOT interpreted as zero dropped data.
    literals = {'Profiling has started.', 'Profiling has stopped.',
        'Common injection library initialized successfully.', 'NVTX injection initialized successfully.',
        'CUDA injection initialized successfully.', 'Enabling trace for device graph launch',
        'CUDA hardware tracing is not supported on this system. A legacy (software instrumented) trace was collected instead.',
        'Buffers holding CUDA trace data will be flushed on CudaProfilerStop() call. See --flush-on-cudaprofilerstop to control this behavior.'}
    patterns = (r'Number of (?:NVTX|CUDA) events collected: \s*\d+\.',
                r'Number of CUPTI events produced: \s*\d+, CUPTI buffers: \d+\.',
                r'Process \d+ was launched by the profiler', r'Loaded CUPTI library: [^\r\n]+')
    def contradicts_target(r):
        return r['process_relation']=='TARGET_PROCESS' and re.fullmatch(
            r'Number of (?:NVTX|CUDA) events collected: \s*0\.',r['text']) is not None
    return [dict(source_rowid=r['source_rowid'], process_relation=r['process_relation'],
                 disposition='INFORMATION_ONLY' if (not contradicts_target(r)
                    and r['severity_id']==1 and r['source_id'] in (1,2,3)
                    and (r['text'] in literals or any(re.fullmatch(p,r['text']) for p in patterns)))
                    else 'IMPACT_UNBOUNDED') for r in diagnostic['records']]


def _request(canonical, scope, paths, bundle, ownership, projection, original, stage, declared, diagnostics, *, domain_proof=False):
    identity=projection['identity']
    output=dict(identity=identity, status='REJECTED', reasons=[], a_records=[],
                assumptions=declared['assumptions'], local_gaps=[], facts={},
                request_projection=projection)
    try:
        require(all(d['disposition']=='INFORMATION_ONLY' for d in diagnostics), 'DIAGNOSTIC_IMPACT_UNBOUNDED')
        # Reuse the trace/API/drain scope join, not the old synthetic source proof.
        drain_ref={'filename':paths['drain_ledger'].name,'sha256':digest(paths['drain_ledger'])}
        drain_api, drain = _drain(paths['drain_ledger'],{'drain_ledger':drain_ref},bundle,
                                  projection,scope,canonical.parent)
        global_pid=drain_api['global_tid']-drain_api['global_tid']%2**24
        require(drain['global_pid']==global_pid,'DRAIN_GLOBAL_PROCESS')
        start,end,clock=projection['start_ns'],projection['end_ns'],projection['clock_domain_id']
        stages=[r for r in stage['stages'] if r['payload']['request_identity']==identity]
        require(len(stages)==1 and stages[0]['trace_start_ns']<=drain_api['start_ns']
                and stages[0]['trace_end_ns']>=end and not stages[0]['unresolved_submissions'], 'STAGE_SCOPE')
        observed_stages=_json(paths['stage_ledger'])
        setup=[r for r in stage['stages'] if r['payload']['stage_role']=='setup']
        require(len(setup)==1 and setup[0]['trace_end_ns']<=drain_api['start_ns'], 'SETUP_ORDER')
        observed=next(r for r in observed_stages['stages'] if r['payload']==stages[0]['payload'])
        require(observed['status']=='COMPLETE' and observed['error'] is None
                and all(p['status']=='OBSERVED' and p['current_native_handle']==p['default_native_handle']==0
                        for p in (observed['before'],observed['after'])), 'STREAM_PROBE')
        require(not original.global_quality_reasons, 'CANONICAL_QUALITY')
        inventory=build_semantic_inventory({**bundle,'ownership_records':ownership})
        require(inventory['input_status']=='VALID', 'INPUT_QUALITY')
        require(not inventory['event_records'] and not inventory['dependency_events'], 'EVENT_PATH')
        contexts=[c for c in inventory['contexts'] if c['context_id']==drain['context_id']
                  and c['process_id']==drain['process_id'] and c['device_id']==drain['device_id']]
        require(len(contexts)==1 and contexts[0]['null_stream_id'] is not None, 'CONTEXT')
        null=contexts[0]['null_stream_id']
        prefix,suffix=[],[]
        for activity in inventory['activities']:
            a,b=activity.get('enqueue_start_ns'),activity.get('enqueue_end_ns')
            require(type(a) is int and type(b) is int, 'CORRELATION')
            require(a<=b and a<=activity['start_ns']<=activity['end_ns'], 'ACTIVITY_ORDER')
            if a>=end:
                continue
            require(all(activity.get(k)==drain[k] for k in ('process_id','device_id','context_id','clock_domain_id')), 'ACTIVITY_SCOPE')
            require(activity['global_pid']==global_pid,'ACTIVITY_GLOBAL_PROCESS')
            if b<=drain_api['start_ns']:
                require(activity['end_ns']<=drain['end_ns'], 'PREFIX_PENDING')
                prefix.append(activity)
            else:
                require(start<=a<=b<=end and activity['end_ns']<=end
                    and _same_request(activity.get('invocation_identity'),identity)
                    and activity['enqueue_global_tid']==drain_api['global_tid'], 'SUBMISSION_SCOPE')
                require(activity['stream_id']==null, 'OTHER_STREAM')
                require(activity.get('graph_id') in (None,0) and activity.get('graph_node_id') in (None,0), 'GRAPH_UNSUPPORTED')
                suffix.append(activity)
        syncs=[s for s in inventory['syncs'] if type(s.get('host_start_ns')) is int
               and s['host_start_ns']<end and start<s['host_end_ns']]
        require(syncs, 'SYNC_MISSING')
        for s in syncs:
            require(s['sync_kind']=='STREAM' and s['stream_id']==null
                and s['global_pid']==global_pid
                and all(s.get(k)==drain[k] for k in ('process_id','device_id','context_id','clock_domain_id'))
                and s.get('runtime_global_tid')==drain_api['global_tid'] and s.get('runtime_mapping_count')==1
                and start<=s['host_start_ns']<=s['host_end_ns']<=end
                and s.get('ownership_status')=='VALID' and not s.get('ownership_reasons')
                and s.get('sync_identity_status')!='AMBIGUOUS'
                and _same_request(s.get('invocation_identity'),identity), 'SYNC_SCOPE')
        apis=[]
        for api in bundle['records']['cuda_api']:
            if api['start_ns']>=end or api['end_ns']<=drain_api['end_ns']:
                continue
            require(start<=api['start_ns']<=api['end_ns']<=end
                and api['global_tid']==drain_api['global_tid'] and api['return_value']==0
                and api['clock_domain_id']==clock, 'API_SCOPE')
            name=re.sub(r'_v\d+$','',api['api_name'])
            matches=[s for s in bundle['records']['cuda_sync'] if s['runtime_record_id']==api['record_id']]
            activities=[a for a in suffix if a['enqueue_record_id']==api['record_id']]
            if name=='cudaStreamSynchronize':
                require(len(matches)==1 and matches[0]['record_id'] in {s['record_id'] for s in syncs}, 'SYNC_MAPPING')
            elif name in SUBMIT_APIS:
                require(activities and not matches, 'SUBMIT_MAPPING')
            elif classify_a_api_name(api['api_name'])[0]=='non_submit':
                require(not activities and not matches, 'LOCAL_GAP_CONFLICT')
            else:
                require(False, 'API_SEMANTICS_UNBOUNDED:'+name)
            apis.append(api['record_id'])
        from .a_accounting import calculate_a_windows
        calculations, proofs=[],[]
        for mode in ('LEGACY','PER_THREAD'):
            restricted=deepcopy(inventory)
            restricted['activities']=deepcopy(suffix)
            restricted['execution_context']['default_stream_mode']=mode
            # A intersections do not assert a physical S marker/callsite or B
            # qualification. Internal syncs may have no kind=sync NVTX label.
            # Use the existing dependency recovery, never synthesize a label.
            semantics=[]
            dependencies={}
            for s in syncs:
                recovery=recover_wait_set(restricted,s)
                require(recovery['dependency_closure_status']=='COMPLETE' and not recovery['reasons'], 'SUFFIX_SEMANTICS')
                ids=recovery['wait_set_activity_ids']
                dependencies[s['record_id']]=recovery['dependency_edges']
                members=[a for a in suffix if a['record_id'] in ids]
                require(len(members)==len(ids) and all(a['end_ns']<=s['host_end_ns'] for a in members),
                        'ACTIVITY_AFTER_SYNC_RETURN')
                require(not ids or len(_semantic_frontier(ids,recovery['dependency_edges']))==1,
                        'TERMINAL_AMBIGUOUS')
                semantics.append(dict(sync_id=s['record_id'],host_start_ns=s['host_start_ns'],
                    host_end_ns=s['host_end_ns'],wait_set_activity_ids=ids,
                    validity='VALID_NONEMPTY' if ids else 'VALID_EMPTY',primary_reason=None,
                    secondary_reasons=[],a_intersection_only=True))
            calculations.append(calculate_a_windows(replace(original,s_records=semantics,
                windows=tuple(w for w in original.windows if w.request_id==identity['request_id']))))
            proofs.append(dict(mode=mode,syncs=[dict(sync_id=s['sync_id'],
                suffix_activity_ids=s['wait_set_activity_ids'],
                **({'dependency_edges':dependencies[s['sync_id']]} if domain_proof else {}),
                scope='A_INTERSECTION_ONLY_NOT_PHYSICAL_W') for s in semantics]))
        if domain_proof:
            require(proofs[0]['syncs']==proofs[1]['syncs'], 'DEFAULT_MEMBERSHIP_NOT_EQUIVALENT')
        require(len(calculations[0])==3 and calculations[0]==calculations[1], 'DEFAULT_NOT_EQUIVALENT')
        require(all(r['primary_reason'] in (None,'CUDA_API_SEMANTICS_UNRESOLVED')
                    and not r['secondary_reasons'] for r in calculations[0]), 'UNBOUNDED_ACCOUNTING_REASON')
        output.update(status='A_SCOPE_ENGINEERING_ONLY',a_records=list(calculations[0]),
            facts=dict(drain_record_id=drain['record_id'],drain_api_id=drain_api['record_id'],
                clock_domain_id=clock, default_equivalence_modes=['LEGACY','PER_THREAD'],
                prefix_activity_ids=[a['record_id'] for a in prefix], observed_api_ids=apis,
                source_sqlite_sha256=bundle['manifest']['source']['sqlite']['sha256'],
                projection=projection,conditional_suffix_proofs=proofs))
    except ValueError as exc:
        output['reasons']=[str(exc)]
    return output


def _calculate(root, receipt_path, execution_path, *, warning_assumption=None):
    receipt,paths,declared,execution=_inputs(receipt_path,execution_path)
    canonical=root/'canonical/canonical_manifest.json'
    scope=root/'projection/scope.json'
    diagnostic=load_diagnostic_scope(root/'diagnostics.json',paths['sqlite'],paths['pass_identity'])
    from .gate8_stage_scope import derive_stage_diagnostics
    from .b_provenance import calculate_b_syncs
    bundle=load_canonical_bundle(canonical)
    require(bundle['manifest']['source']['sqlite']['sha256'].lower()==digest(paths['sqlite'])
        and bundle['manifest']['source']['raw']['sha256'].lower()==digest(paths['raw']), 'RAW_LINEAGE')
    ownership,projections=load_projected_ownership(canonical,bundle,scope)
    stage=derive_stage_diagnostics(canonical,paths['stage_ledger'])
    with time_representation(SIGNED):
        original=build_projected_ab_inputs(canonical,scope)
        diagnostics=_diagnostics(diagnostic)
        effective=diagnostics
        assumed=None
        if warning_assumption is not None:
            from .gate8_warning_assumption import select_assumed_warnings
            assumed=select_assumed_warnings(diagnostic,diagnostics,warning_assumption)
            excluded={r['source_rowid'] for r in assumed['records']}
            effective=[r for r in diagnostics if r['source_rowid'] not in excluded]
        requests=[_request(canonical,scope,paths,bundle,ownership,p,original,stage,declared,effective)
                  for p in projections if p['phase']=='full_request']
        physical_b=list(calculate_b_syncs(original))
    require(requests, 'NO_REQUEST')
    result=dict(schema_version=VERSION,observation_profile=PROFILE,
        input_receipt_sha256=digest(Path(receipt_path)),execution_receipt_sha256=digest(Path(execution_path)),
        status='A_SCOPE_ENGINEERING_ONLY' if all(r['status']=='A_SCOPE_ENGINEERING_ONLY' for r in requests) else 'BLOCKED',
        validation_role='ENGINEERING_CONDITIONAL_ACCOUNTING',identity=receipt['identity'],
        support_declaration=declared,observed_configuration=execution['observed_configuration'],
        dropped_records_status='UNKNOWN',measurement_validity='NOT_ASSESSED',
        gate8_verdict='NOT_RUN',q0_status='NOT_RUN',d_score_allowed=False,signature_allowed=False,
        requests=requests,diagnostic_dispositions=diagnostics,
        physical_s_records=list(original.s_records),physical_b_records=physical_b)
    if assumed is not None:
        result.update(schema_version='exposedpath-conditional-a/0.1.0',trusted_a=False,
            api_classification_registry=dict(version=A_API_VERSION,sha256=digest(A_API_REGISTRY)),
            validation_role='WARNING_ASSUMPTION_CONDITIONAL_NOT_ACCEPTANCE',warning_assumption=assumed,
            status='CONDITIONAL_A_ONLY_NOT_ACCEPTED' if result['status']=='A_SCOPE_ENGINEERING_ONLY' else 'BLOCKED')
        for request in requests:
            if request['status']=='A_SCOPE_ENGINEERING_ONLY':
                request['status']='CONDITIONAL_A_ONLY_NOT_ACCEPTED'
            request['trusted_a']=False
    return result


def process_conditional_scope(formal_path, receipt_path, execution_path, output_dir, *, assumption):
    """Separate derivative; formal gate and sealed source bytes remain unchanged."""
    import shutil
    formal_path=Path(formal_path).resolve()
    formal=load_engineering_scope(formal_path,receipt_path,execution_path)
    require(formal['status']=='BLOCKED' and all(r['reasons']==[
        'ENGINEERING_SCOPE_DIAGNOSTIC_IMPACT_UNBOUNDED'] for r in formal['requests']), 'CONDITIONAL_FORMAL_REASON')
    output=Path(output_dir).resolve()
    require(not output.exists() and not output.is_relative_to(formal_path.parent)
            and not formal_path.is_relative_to(output),'CONDITIONAL_OUTPUT')
    _,paths,_,_=_inputs(receipt_path,execution_path)
    source_paths=[formal_path,Path(receipt_path),Path(execution_path),*paths.values()]
    hashes={Path(p):digest(Path(p)) for p in source_paths}
    require(not any(p.resolve().is_relative_to(output) for p in hashes),'OUTPUT_CONTAINS_INPUT')
    output.parent.mkdir(parents=True,exist_ok=True)
    root=Path(tempfile.mkdtemp(prefix='.'+output.name+'-partial-',dir=output.parent))
    for item in formal['files']:
        source=_resolve(formal_path.parent,item)
        target=root/source.relative_to(formal_path.parent)
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
    result=_calculate(root,receipt_path,execution_path,warning_assumption=assumption)
    require(all(digest(p)==sha for p,sha in hashes.items()),'SOURCE_CHANGED')
    result['formal_result_sha256']=hashes[formal_path]
    result['files']=[_entry(p,root) for p in sorted(root.rglob('*')) if p.is_file()]
    _write(root/'conditional_a.json',result)
    root.rename(output)
    return output/'conditional_a.json'


def process_engineering_scope(receipt_path, execution_path, output_dir):
    """New file pipeline; failures cannot publish a complete output directory."""
    output=Path(output_dir).resolve()
    if output.exists():
        raise FileExistsError(output)
    receipt,paths,_,_=_inputs(receipt_path,execution_path)
    hashes={str(p):digest(Path(p)) for p in [Path(receipt_path),Path(execution_path),*paths.values()]}
    require(not any(Path(p).resolve().is_relative_to(output) for p in hashes),'OUTPUT_CONTAINS_INPUT')
    output.parent.mkdir(parents=True,exist_ok=True)
    root=Path(tempfile.mkdtemp(prefix='.'+output.name+'-partial-',dir=output.parent))
    write_diagnostic_scope(paths['sqlite'],paths['pass_identity'],root/'diagnostics.json')
    from .canonical_raw import convert_sqlite_to_canonical
    from .gate8_scope import project_completion_scopes
    canonical=convert_sqlite_to_canonical(paths['sqlite'],root/'canonical','Engineering',
        raw_sha256=digest(paths['raw']),collector_version=receipt['collector_version'],
        gate8_sources={k:paths[k] for k in ('pass_identity','preflight','cuda_probe')})
    project_completion_scopes(canonical,paths['host_ledger'],root/'projection/scope.json')
    result=_calculate(root,receipt_path,execution_path)
    for p,sha in hashes.items():
        require(digest(Path(p))==sha,'SOURCE_CHANGED')
    result['files']=[_entry(p,root) for p in sorted(root.rglob('*')) if p.is_file()]
    _write(root/'engineering_a.json',result)
    root.rename(output)
    return output/'engineering_a.json'


def load_engineering_scope(result_path, receipt_path, execution_path):
    result_path=Path(result_path)
    result=_json(result_path)
    require(result.get('schema_version')==VERSION,'RESULT_VERSION')
    resolved=[_resolve(result_path.parent,r) for r in result['files']]
    require(len(set(resolved))==len(resolved) and set(resolved)=={
        p.resolve() for p in result_path.parent.rglob('*') if p.is_file() and p!=result_path},'FILE_SET')
    actual=_calculate(result_path.parent,receipt_path,execution_path)
    require({k:v for k,v in result.items() if k!='files'}==actual,'RESULT_MISMATCH')
    return result


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('input-receipt','execution-receipt','output-dir'):
        parser.add_argument('--'+name,required=True,type=Path)
    args=parser.parse_args()
    result=process_engineering_scope(args.input_receipt,args.execution_receipt,args.output_dir)
    status=_json(result)['status']
    print(status)
    return 0 if status=='A_SCOPE_ENGINEERING_ONLY' else 1


if __name__=='__main__':
    raise SystemExit(main())
