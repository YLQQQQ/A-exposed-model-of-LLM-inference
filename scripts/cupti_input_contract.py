"""Configuration-driven inputs; this is not a table of GPU qualifications.

The Pilot plan is finite, whereas content validation is length-parameterized.
All measured behavior remains in the reviewed runner/P helper and S/COE.
"""
from copy import deepcopy
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

VERSION='CUPTI-INPUT-PILOT/0.1.0'
MODEL='cupti-timeline-model/0.3.0'
CONTROL='cupti-timeline-stage-b/0.3.0'
PLAN_VERSION='CUPTI-INPUT-PLAN/0.2.0'
PLAN_MODEL='cupti-timeline-model/0.4.0'
PLAN_CONTROL='cupti-timeline-stage-b/0.4.0'
BATCH_PLAN_VERSION='CUPTI-INPUT-PLAN/0.3.0'
BATCH_MODEL='cupti-timeline-model/0.5.0'
BATCH_CONTROL='cupti-timeline-stage-b/0.5.0'
BATCH_IDENTITY='cupti-input-identity/0.2.0'
NATIVE='6c744bf52daff3fc54571e264a0c34e3207aa1df'
POLICIES=dict(consumer_version='submit-effect-bridge/0.3.0',
    timing_policy='cupti-api22-distinct-api-callback-boundaries/0.2.0',
    driver_query_policy='cupti-api22-driver-queries/0.1.0',runtime_query_policy='cupti-api22-runtime-queries/0.1.0')


def require(ok,reason):
    if not ok:raise ValueError('CUPTI_INPUT_'+reason)


def role_policy():
    here=Path(__file__).resolve()
    source=here.parents[1]/'exposedpath/gate11_pilot.py' if here.parent.name=='scripts' else here.with_name('producer_policy.py')
    spec=importlib.util.spec_from_file_location('_cupti_role_plan',source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def batch_plan(plan):return isinstance(plan,dict) and plan.get('schema_version')==BATCH_PLAN_VERSION


def plan_inputs(plan):
    policy=role_policy();policy.validate_cupti_plan(plan)
    return ({policy.cupti_condition_key(c):c for c in plan['conditions']} if batch_plan(plan) else
        {str(n):dict(input_tokens=n,batch_size=1) for n in plan['input_lengths']})


def slot_input_key(slot):
    return slot['condition'] if slot['version']=='CUPTI-INPUT-SLOT/0.3.0' else str(slot['input_tokens'])


def input_filename(slot):
    return (f'input_{slot["input_tokens"]}_B{slot["batch_size"]}.json' if slot['version']=='CUPTI-INPUT-SLOT/0.3.0'
        else f'input_{slot["input_tokens"]}.json')


def configured_identity(prompt,c,model_config=None):
    return (input_identity(prompt,c['input_tokens'],model_config,batch_size=c['batch_size'],version=BATCH_IDENTITY)
        if c['schema_version']==BATCH_MODEL else input_identity(prompt,c['input_tokens'],model_config))


def schedule(batch_id,commit,*,plan=None):
    require(isinstance(commit,str) and re.fullmatch('[0-9a-f]{40}',commit),'COMMIT')
    # Reuse the existing producer's prospective Pilot identity contract ONLY.
    # This does not inherit its Nsight observation/analysis qualification.
    # Explicit source layouts: repository scripts/ vs flat reviewed delivery.
    module=role_policy()
    if plan is not None:
        rows=module.cupti_plan_schedule(batch_id,NATIVE,plan)
        return [dict(deepcopy(p),version='CUPTI-INPUT-SLOT/0.3.0' if plan['schema_version']==BATCH_PLAN_VERSION else 'CUPTI-INPUT-SLOT/0.2.0',controller_commit=commit,
            producer_binding=deepcopy(p) if plan['role']=='Pilot' else None,
            data_role=plan['role'],nsight_profiles=0,cupti_sessions=1) for p in rows]
    require(module.CUPTI_INPUT_VERSION=='CUPTI-INPUT-PRODUCER-PILOT/0.1.0','ROLE_POLICY_VERSION')
    original=module.cupti_schedule
    return [dict(deepcopy(p),version='CUPTI-INPUT-SLOT/0.1.0',controller_commit=commit,
        producer_binding=deepcopy(p),data_role='Pilot',nsight_profiles=0,cupti_sessions=1)
        for p in original(batch_id,NATIVE)]


def bind_producer(cfg):
    """One explicit role-policy overlay, never a new model runner or GPU probe."""
    source=Path(__file__).with_name('producer_policy.py')
    require(source.is_file() and hashlib.sha256(source.read_bytes()).hexdigest()==cfg['producer_policy_sha256'],
        'PRODUCER_POLICY_HASH')
    import exposedpath
    require(list(map(lambda p:Path(p).resolve(),exposedpath.__path__))==[Path(cfg['code_root']).resolve()/'exposedpath'],
        'PRODUCER_PARENT_ORIGIN')
    name='exposedpath.gate11_pilot';old=sys.modules.get(name)
    require(old is None,'PRODUCER_POLICY_ALREADY_LOADED')
    spec=importlib.util.spec_from_file_location(name,source);module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module
    try:spec.loader.exec_module(module)
    except BaseException:
        del sys.modules[name];raise
    exposedpath.gate11_pilot=module
    require(module.CUPTI_INPUT_VERSION=='CUPTI-INPUT-PRODUCER-PILOT/0.1.0','PRODUCER_POLICY_VERSION')
    return dict(version=module.CUPTI_INPUT_VERSION,origin=str(source),sha256=cfg['producer_policy_sha256'])


def validate_model(c):
    if c.get('schema_version') in (PLAN_MODEL,BATCH_MODEL):
        plan=c.get('input_plan');role_policy().validate_cupti_plan(plan)
        batched=c['schema_version']==BATCH_MODEL
        require(batched==batch_plan(plan),'MODEL_PLAN_VERSION')
        slot=c.get('input_slot');require(isinstance(slot,dict) and any(slot==s for s in
            schedule(slot.get('batch_id'),c.get('control_commit'),plan=plan)),'SLOT_BINDING')
        if batched:require(type(c.get('batch_size')) is int and c['batch_size']==slot['batch_size'],'MODEL_BATCH_SLOT')
        expected=dict(batch_size=slot['batch_size'] if batched else 1,output_tokens=2,warmup_count=3,repeat_count=1,role=plan['role'],
            completion_policy='HOST_READABLE_P',model_process_budget=1,nsight_profiles=0,torch_profiler=False,
            native_commit=NATIVE,activity_policy_version='cupti-api22-activity-policy/0.2.0',**POLICIES)
        require(all(type(c.get(k)) is type(v) and c[k]==v for k,v in expected.items()),'MODEL_CONTRACT')
        require(c.get('input_tokens')==slot['input_tokens'] and type(c.get('input_tokens')) is int
            and c.get('run_id')==slot['run_id'] and
            c.get('session',{}).get('activity_policy_version')==c['activity_policy_version'],'INPUT_OR_SESSION_BINDING')
        require(c.get('output_validation',{}).get('version')==('cupti-output-validation/0.3.0' if batched else 'cupti-output-validation/0.2.0'),'OUTPUT_POLICY')
        validate_output_policy(c.get('output_validation'),plan['role'],batch_size=c['batch_size'])
        require(isinstance(c.get('model_limits'),dict) and c['input_tokens']+2<=c['model_limits'].get('max_position_embeddings',0),
            'MODEL_CAPACITY_OR_VOCAB')
        if batched:
            require(c.get('input_identity',{}).get('schema_version')==BATCH_IDENTITY and
                c['input_identity'].get('shape')==[c['batch_size'],c['input_tokens']] and
                c['input_identity'].get('sample_indices')==list(range(c['batch_size'])),'MODEL_BATCH_INPUT_IDENTITY')
            require(len(c['model_limits'].get('eos_token_ids',[]))==1,'MODEL_MULTIPLE_EOS_NOT_SUPPORTED')
        return NATIVE
    require(c.get('schema_version')==MODEL,'MODEL_VERSION')
    expected=dict(batch_size=1,output_tokens=2,warmup_count=3,repeat_count=1,role='Pilot',
        completion_policy='HOST_READABLE_P',model_process_budget=1,nsight_profiles=0,torch_profiler=False,
        native_commit=NATIVE,activity_policy_version='cupti-api22-activity-policy/0.2.0',**POLICIES)
    require(all(type(c.get(k)) is type(v) and c[k]==v for k,v in expected.items()),'MODEL_CONTRACT')
    p=c.get('pilot');require(isinstance(p,dict),'PILOT_BINDING')
    require(any(p==r and all(type(p[k]) is type(v) for k,v in r.items())
        for r in schedule(p.get('batch_id'),c.get('control_commit'))),'SLOT_BINDING')
    require(type(c.get('input_tokens')) is int and c['input_tokens']==p['input_tokens'] and c['run_id']==p['run_id']
        and c.get('session',{}).get('activity_policy_version')==c['activity_policy_version'],'INPUT_OR_SESSION_BINDING')
    return NATIVE


def validate_output_policy(policy,role,*,batch_size=1):
    if isinstance(policy,dict) and policy.get('version')=='cupti-output-validation/0.3.0':
        require(type(batch_size) is int and batch_size in (1,2,4) and
            set(policy)=={'version','mode','expected_token_ids','batch_size','output_tokens','eos_policy'} and
            type(policy['batch_size']) is int and policy['batch_size']==batch_size and policy['output_tokens']==2 and
            policy['eos_policy']=='ANY_SAMPLE_EOS_REJECT_WHOLE_INVOCATION','OUTPUT_POLICY')
        if policy['mode']=='OBSERVED_ENGINEERING':
            require(role=='Engineering' and policy['expected_token_ids'] is None,'OUTPUT_POLICY')
        else:
            ids=policy['expected_token_ids']
            require(role in ('Engineering','Pilot') and policy['mode']=='EXACT_REFERENCE' and isinstance(ids,list) and
                len(ids)==2 and all(isinstance(v,list) and len(v)==batch_size and
                    all(type(t) is int and t>=0 for t in v) for v in ids),'OUTPUT_POLICY')
        return policy
    require(batch_size==1,'OUTPUT_POLICY')
    require(isinstance(policy,dict) and set(policy)=={'version','mode','expected_token_ids'}
        and policy['version']=='cupti-output-validation/0.2.0','OUTPUT_POLICY')
    if policy['mode']=='OBSERVED_ENGINEERING':
        require(role=='Engineering' and policy['expected_token_ids'] is None,'OUTPUT_POLICY')
    else:
        require(policy['mode']=='EXACT_REFERENCE' and role in ('Pilot','Engineering'),'OUTPUT_POLICY')
        require(isinstance(policy['expected_token_ids'],list) and len(policy['expected_token_ids'])==2
            and all(isinstance(v,list) and len(v)==1 and type(v[0]) is int and v[0]>=0
                for v in policy['expected_token_ids']),'OUTPUT_POLICY')
    return policy


def validate_tokens(ids,policy,model):
    batch=policy['batch_size'] if policy.get('version')=='cupti-output-validation/0.3.0' else 1
    validate_output_policy(policy,'Engineering',batch_size=batch)
    require(isinstance(ids,list) and len(ids)==2 and all(isinstance(v,list) and len(v)==batch
        and all(type(t) is int and 0<=t<model['vocab_size'] and t not in model['eos_token_ids'] for t in v) for v in ids),
        'TOKEN_VALUES_OR_EOS')
    if policy['mode']=='EXACT_REFERENCE':require(ids==policy['expected_token_ids'],'TOKEN_REFERENCE')
    return dict(mode=policy['mode'],actual_token_ids=ids,
        **(dict(output_shape=[2,batch],completion_unit='WHOLE_BATCH_INVOCATION') if policy.get('version')=='cupti-output-validation/0.3.0' else {}),
        independent_content_reference=policy['mode']=='EXACT_REFERENCE',numerical_correctness='NOT_ASSESSED')


def model_limits(config):
    eos=config.get('eos_token_id');eos=eos if isinstance(eos,list) else [eos]
    require(type(config.get('vocab_size')) is int and config['vocab_size']>0 and
        type(config.get('max_position_embeddings')) is int and all(type(v) is int and 0<=v<config['vocab_size'] for v in eos),
        'MODEL_LIMITS')
    return dict(vocab_size=config['vocab_size'],max_position_embeddings=config['max_position_embeddings'],eos_token_ids=eos)


def batch_prompt(single,batch_size):
    require(type(batch_size) is int and batch_size in (1,2,4),'BATCH_SIZE')
    input_identity(single,single.get('fixed_input_tokens'))
    value=deepcopy(single)
    value.update(batch_input_version='cupti-batch-input/0.1.0',batch_size=batch_size,
        samples=[dict(deepcopy(single['samples'][0]),sample_index=i) for i in range(batch_size)])
    return value


def tensor_rows(prompt,identity):
    version=identity['schema_version'];batch,length=identity['shape']
    require(input_identity(prompt,length,batch_size=batch,version=version)==identity,'TENSOR_INPUT_IDENTITY')
    return ([list(r['input_ids']) for r in prompt['samples']],
            [list(r['attention_mask']) for r in prompt['samples']])


def input_identity(prompt,length,model_config=None,*,batch_size=1,version='cupti-input-identity/0.1.0'):
    """The same 32-token cycle/mask rule, independent of an experiment's points."""
    require(type(length) is int and length>=32 and length%32==0,'INPUT_LENGTH')
    samples=prompt.get('samples')
    batched=version==BATCH_IDENTITY
    require(version in ('cupti-input-identity/0.1.0',BATCH_IDENTITY) and type(batch_size) is int and
        batch_size in ((1,2,4) if batched else (1,)),'INPUT_SHAPE')
    require(prompt.get('fixed_input_tokens')==length and isinstance(samples,list) and len(samples)==batch_size,'INPUT_SHAPE')
    if batched:
        require(prompt.get('batch_input_version')=='cupti-batch-input/0.1.0' and
            type(prompt.get('batch_size')) is int and prompt['batch_size']==batch_size,'INPUT_SHAPE')
        require(all(type(r.get('sample_index')) is int and r['sample_index']==i for i,r in enumerate(samples)),'SAMPLE_ORDER')
        for r in samples:
            one=dict(prompt,samples=[dict(r,sample_index=0)])
            input_identity(one,length,model_config)
        require(all(r['input_ids']==samples[0]['input_ids'] and r['attention_mask']==samples[0]['attention_mask']
                    for r in samples),'BATCH_REPEATED_INPUT')
        digest=lambda v:hashlib.sha256(json.dumps(v,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
        ids=[r['input_ids'] for r in samples];masks=[r['attention_mask'] for r in samples]
        return dict(schema_version=BATCH_IDENTITY,shape=[batch_size,length],sample_indices=list(range(batch_size)),
            input_ids_sha256=digest(ids),attention_mask_sha256=digest(masks),
            batch_sha256=digest(dict(shape=[batch_size,length],sample_indices=list(range(batch_size)),input_ids=ids,attention_mask=masks)),
            algorithm='SHA256_COMPACT_UTF8_JSON_IN_ORDER')
    row=samples[0];ids=row.get('input_ids');mask=row.get('attention_mask')
    require(type(row.get('sample_index')) is int and row['sample_index']==0 and isinstance(ids,list)
        and len(ids)==length and all(type(v) is int and v>=0 for v in ids),'INPUT_SHAPE')
    require(ids==ids[:32]*(length//32),'CONSTRUCTION')
    require(mask==[1]*length and all(type(v) is int for v in mask),'MASK')
    if model_config is not None:
        require(model_config.get('model_type')=='qwen2' and type(model_config.get('vocab_size')) is int
            and type(model_config.get('max_position_embeddings')) is int and length+2<=model_config['max_position_embeddings']
            and all(v<model_config['vocab_size'] for v in ids),'MODEL_CAPACITY_OR_VOCAB')
        specials=set()
        for source in (model_config,prompt.get('special_tokens',{})):
            for k in ('bos_token_id','eos_token_id','pad_token_id'):
                v=source.get(k)
                if isinstance(v,list):specials.update(v)
                elif v is not None:specials.add(v)
        require(not specials.intersection(ids),'SPECIAL_TOKEN')
    digest=lambda v:hashlib.sha256(json.dumps(v,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    return dict(schema_version='cupti-input-identity/0.1.0',shape=[1,length],sample_indices=[0],
        input_ids_sha256=digest([ids]),attention_mask_sha256=digest([mask]),
        batch_sha256=digest(dict(shape=[1,length],sample_indices=[0],input_ids=[ids],attention_mask=[mask])),
        algorithm='SHA256_COMPACT_UTF8_JSON_IN_ORDER')


def union(lo,hi,intervals):
    parts=sorted((max(lo,a),min(hi,b)) for a,b in intervals if max(lo,a)<min(hi,b));merged=[]
    for a,b in parts:
        if merged and a<=merged[-1][1]:merged[-1][1]=max(merged[-1][1],b)
        else:merged.append([a,b])
    return sum(b-a for a,b in merged)


def token_metrics(raw,scope,result,index,phase_start):
    require(index in (0,1) and type(phase_start) is int and phase_start<scope['completion_end'],'PHASE')
    records={r['id']:r for r in raw['records']}
    require(len(records)==len(raw['records']) and len(result['members'])==len(set(result['members']))
        and all(k in records for k in result['members']),'MEMBER_IDENTITY')
    necessary=[records[k] for k in result['members']]
    require(necessary and all(r['kind'] in ('KERNEL','MEMCPY','MEMSET') and
        all(r[k]==scope[k] for k in ('pid','device','context','stream')) for r in necessary),'MEMBER_SCOPE')
    copy=records[scope['copy_api']];sync=records[scope['sync_api']]
    lo,hi=copy['start'],sync['end'];phase_end=scope['completion_end'];phase=phase_end-phase_start
    require(phase_start<=lo<=copy['end']<=sync['start']<=hi<=phase_end,'OPERATION_PHASE')
    intervals=lambda rows:[(r['start'],r['end']) for r in rows]
    overlap=union(lo,hi,intervals(necessary))
    require(overlap==result['coe_ns'] and hi-lo==result['operation_wall_ns'],'INTERVAL_ARITHMETIC')
    gpu=[r for r in raw['records'] if r['kind'] in ('KERNEL','MEMCPY','MEMSET') and
        all(r[k]==scope[k] for k in ('pid','device','context'))]
    phase_gpu=union(phase_start,phase_end,intervals(gpu))
    member_set=set(result['members'])
    submitted=[a for a in result.get('submission_api_sources',[]) if a['end']<=lo
        and any(k in member_set for k in result.get('submit_effects',{}).get(a['api_id'],[]))]
    last=max((a['end'] for a in submitted),default=None)
    terminal=records.get(result.get('terminal'))
    require(terminal is not None and terminal['id'] in member_set and terminal['end']<=hi,'TERMINAL')
    return dict(schema_version='cupti-token-metrics/0.1.0',token_index=index,
        phase='Prefill' if index==0 else 'Decode',phase_start_ns=phase_start,phase_end_ns=phase_end,phase_ns=phase,
        coe_ns=overlap,coe_phase_ratio=overlap/phase,phase_gpu_union_ns=phase_gpu,
        coe_phase_gpu_ratio=overlap/phase_gpu if phase_gpu else None,
        operation_gpu_union_ns=union(lo,hi,intervals(gpu)),operation_wall_ns=hi-lo,
        operation_complement_ns=hi-lo-overlap,copy_wall_ns=copy['end']-copy['start'],sync_wall_ns=sync['end']-sync['start'],
        original_sync_intersection_ns=result['sync_intersection_ns'],
        kernel_coe_ns=union(lo,hi,intervals([r for r in necessary if r['kind']=='KERNEL'])),
        memop_coe_ns=union(lo,hi,intervals([r for r in necessary if r['kind']!='KERNEL'])),
        necessary_before_copy_ns=union(scope['request_start'],lo,intervals(necessary)),
        necessary_member_ids=result['members'],copy_api_id=scope['copy_api'],sync_api_id=scope['sync_api'],
        copy_entry_ns=lo,sync_return_ns=hi,last_pre_copy_required_submission_return_ns=last,
        copy_entry_after_last_submission_ns=lo-last if last is not None else None,
        terminal_id=result.get('terminal'),terminal_end_ns=terminal['end'] if terminal else None,
        terminal_after_copy_entry_ns=terminal['end']-lo if terminal else None,
        phase_gpu_scope='OBSERVED_PID_DEVICE_CONTEXT_PHASE_NOT_CUMULATIVE_W',
        pure_host_blocking_ns=None,formal_eligible=False)


def summarize(slots,rows,*,plan=None):
    if plan is not None:
        role_policy().validate_cupti_plan(plan)
        require(slots and slots==schedule(slots[0]['batch_id'],slots[0]['controller_commit'],plan=plan),'SLOT_PLAN')
    batched=batch_plan(plan)
    require(len(rows)==len(slots)==(9 if plan is None else plan['blocks']*len(plan_inputs(plan))),'INCOMPLETE_BLOCKS')
    require([r['slot'] for r in rows]==slots,'SLOT_IDENTITY_OR_ORDER')
    for r in rows:
        require([v['token_index'] for v in r['metrics']]==[0,1],'TOKEN_COVERAGE')
        if batched:
            require(all(v.get('batch_size')==r['slot']['batch_size'] and
                v.get('completion_unit')=='WHOLE_BATCH_INVOCATION' for v in r['metrics']),'METRIC_BATCH_IDENTITY')
    comparisons=[]
    blocks=[1,2,3] if plan is None else list(range(1,plan['blocks']+1))
    for block in blocks:
        by_length={r['slot']['condition'] if batched else r['slot']['input_tokens']:r for r in rows if r['slot']['block']==block}
        require(set(by_length)==(set(plan_inputs(plan)) if batched else {512,1024,2048} if plan is None else set(plan['input_lengths'])),'INCOMPLETE_BLOCKS')
        for token in (0,1):
            pairs=[dict(low=a,high=b,role='PRIMARY_ENDPOINT' if token==0 and (a,b)==(512,2048)
                else 'PREDECLARED_DESCRIPTION') for a,b in ((512,1024),(1024,2048),(512,2048))] if plan is None else [
                    v for v in plan['comparisons'] if token in v['token_indices']]
            for comparison in pairs:
                low,high=comparison['low'],comparison['high']
                a,b=(by_length[n]['metrics'][token] for n in (low,high))
                ga,gb=a['phase_gpu_union_ns'],b['phase_gpu_union_ns']
                defined=type(ga) is int and ga>0 and type(gb) is int and gb>=0
                value=Fraction(b['coe_ns'])-Fraction(a['coe_ns'])*Fraction(gb,ga) if defined else None
                comparisons.append(dict(block=block,token_index=token,low=low,high=high,
                    **(dict(comparison_axis='BATCH_SIZE' if by_length[low]['slot']['input_tokens']==by_length[high]['slot']['input_tokens'] else 'INPUT_LENGTH',
                        low_batch_size=by_length[low]['slot']['batch_size'],high_batch_size=by_length[high]['slot']['batch_size'],
                        low_input_tokens=by_length[low]['slot']['input_tokens'],high_input_tokens=by_length[high]['slot']['input_tokens']) if batched else {}),
                    comparison_role=comparison['role'],
                    delta_coe_ns=b['coe_ns']-a['coe_ns'],R_ns=float(value) if value is not None else None,
                    R_exact=dict(numerator=value.numerator,denominator=value.denominator) if value is not None else None,
                    R_undefined_reason=None if defined else 'NONPOSITIVE_OR_INVALID_LOW_PHASE_GPU_UNION',
                    coe_phase_percentage_point_delta=100*(b['coe_phase_ratio']-a['coe_phase_ratio'])))
    return dict(schema_version='cupti-input-summary/0.3.0' if batched else 'cupti-input-pilot-summary/0.1.0' if plan is None else 'cupti-input-summary/0.2.0',complete_blocks=blocks,rows=rows,
        comparisons=comparisons,statistical_unit='COMPLETE_BLOCK_NOT_TOKEN_OR_BATCH_SAMPLE' if batched else 'COMPLETE_BLOCK_NOT_TOKEN',
        stable_precision='NOT_ASSESSED',old_samples_pooled=False,pure_host_blocking=None,formal_eligible=False)
