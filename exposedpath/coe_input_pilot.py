"""Versioned finite P-wrapped input Pilots; none extends Formal qualification."""
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re

from .gate8_isolated_preflight import read,sha,write_new

VERSION='COE-INPUT-P-PILOT/0.1'
PROFILE='COE_INPUT_P_BOTH_TOKENS/0.1'
RESULT_VERSION='coe-input-pilot-result/0.1.0'
STATUS='COE_INPUT_BOTH_TOKENS_PENDING_REVIEW'
ORDERS=((512,2048),(2048,512),(2048,512),(512,2048))
MIDPOINT_VERSION='COE-INPUT-P-PILOT/0.2'
MIDPOINT_ORDERS=((512,1024,2048),(1024,2048,512),(2048,512,1024))
EXTENDED_VERSION='COE-INPUT-P-PILOT/0.3'
EXTENDED_ORDERS=((256,512,2048,1024),(512,1024,256,2048),
                 (1024,2048,512,256),(2048,256,1024,512))
LOW_SIDE_VERSION='COE-INPUT-P-LOW3-PILOT/0.1'
LOW_SIDE_ORDERS=((256,512,2048),(512,2048,256),(2048,256,512))


def require(ok,reason):
    if not ok:raise ValueError('COE_INPUT_'+reason)


def active(v):return isinstance(v,dict) and v.get('version') in (VERSION,MIDPOINT_VERSION,EXTENDED_VERSION,LOW_SIDE_VERSION)


def specification(version):
    require(version in (VERSION,MIDPOINT_VERSION,EXTENDED_VERSION,LOW_SIDE_VERSION),'BINDING_VERSION')
    if version==LOW_SIDE_VERSION:
        return dict(orders=LOW_SIDE_ORDERS,lengths=(256,512,2048),budget=9,
            profile='COE_INPUT_P_LOW3_BOTH_TOKENS/0.1',input_schema='coe-input-low3-identity/0.1.0',
            status='FIXED_NINE_LOW3_PILOT_COMPLETE_STOP_FOR_REVIEW')
    if version==EXTENDED_VERSION:
        return dict(orders=EXTENDED_ORDERS,lengths=(256,512,1024,2048),budget=16,
            profile='COE_INPUT_P_BOTH_TOKENS/0.3',input_schema='coe-input-axis-identity/0.3.0',
            status='FIXED_SIXTEEN_INPUT_PILOT_COMPLETE_STOP_FOR_REVIEW')
    orders=ORDERS if version==VERSION else MIDPOINT_ORDERS
    return dict(orders=orders,lengths=(512,2048) if version==VERSION else (512,1024,2048),
        budget=sum(map(len,orders)),profile=PROFILE if version==VERSION else 'COE_INPUT_P_BOTH_TOKENS/0.2',
        input_schema='coe-input-axis-identity/0.1.0' if version==VERSION else 'coe-input-axis-identity/0.2.0',
        status='FIXED_EIGHT_INPUT_PILOT_COMPLETE_STOP_FOR_REVIEW' if version==VERSION else 'FIXED_NINE_INPUT_PILOT_COMPLETE_STOP_FOR_REVIEW')


def schedule(batch_id,commit,*,version=VERSION):
    require(isinstance(batch_id,str) and re.fullmatch('[A-Za-z0-9_-]{1,60}',batch_id),'BATCH_ID')
    require(isinstance(commit,str) and re.fullmatch('[0-9a-f]{40}',commit),'COMMIT')
    spec=specification(version)
    return [dict(version=version,batch_id=batch_id,execution_commit=commit,block=b,position=p,
        condition=f'G{n}P',input_tokens=n,batch_size=1,output_tokens=2,variant=None,observation_variant='P',
        pass_id='pass1',pair_id=f'{batch_id}-b{b}',run_id=f'{batch_id}-b{b}-G{n}P-pass1',
        warmup_count=3,repeat_count=1,purpose='CANDIDATE_LOW_SIDE_RESPONSE_PILOT_ONLY' if version==LOW_SIDE_VERSION else 'CANDIDATE_INPUT_RESPONSE_PILOT_ONLY',
        declaration_role='PRE_EXECUTION',formal_eligible=False)
        for b,order in enumerate(spec['orders'],1) for p,n in enumerate(order,1)]


def validate_binding(v):
    require(isinstance(v,dict),'BINDING')
    require(any(v==b and all(type(v[k]) is type(x) for k,x in b.items())
        for b in schedule(v.get('batch_id'),v.get('execution_commit'),version=v.get('version'))),'BINDING')
    return v


def minimal_fields(binding):
    b=validate_binding(binding)
    from .gate8_engineering_contract import declaration
    scope=declaration('sdpa');scope['profile']=specification(b['version'])['profile']
    return dict(pilot=deepcopy(b),run_role='PILOT',data_role='Pilot',run_id=b['run_id'],
        fixed_input_tokens=b['input_tokens'],fixed_output_tokens=2,batch_size=1,warmup_count=3,repeat_count=1,
        execution_mode='eager',attention_backend='sdpa',dtype_and_quantization='fp16',
        sampling_config={'do_sample':False},study_mode='G1_NATURAL',n1_intervention=None,engineering_scope=scope)


def input_identity(prompt,*,version=VERSION):
    n=prompt.get('fixed_input_tokens');samples=prompt.get('samples')
    spec=specification(version)
    require(type(n) is int and n in spec['lengths'] and isinstance(samples,list) and len(samples)==1,'INPUT_SHAPE')
    s=samples[0];ids=s.get('input_ids');mask=s.get('attention_mask')
    require(type(s.get('sample_index')) is int and s['sample_index']==0 and isinstance(ids,list)
        and len(ids)==n and all(type(i) is int and i>=0 for i in ids),'INPUT_VALUES')
    require(mask==[1]*n and all(type(i) is int for i in mask),'MASK')
    digest=lambda v:hashlib.sha256(json.dumps(v,separators=(',',':'),ensure_ascii=False).encode('utf8')).hexdigest()
    return dict(schema_version=spec['input_schema'],shape=[1,n],sample_indices=[0],
        input_ids_sha256=digest([ids]),attention_mask_sha256=digest([mask]),
        batch_sha256=digest(dict(shape=[1,n],sample_indices=[0],input_ids=[ids],attention_mask=[mask])),
        algorithm='SHA256_COMPACT_UTF8_JSON_IN_ORDER')


def validate_input(prompt,config,batch,*,version=VERSION):
    identity=input_identity(prompt,version=version);n=prompt['fixed_input_tokens']
    require(type(batch) is int and batch==1,'BATCH')
    require(config.get('model_type')=='qwen2' and type(config.get('vocab_size')) is int
        and type(config.get('max_position_embeddings')) is int and n+2<=config['max_position_embeddings'],'MODEL_CONFIG')
    ids=prompt['samples'][0]['input_ids']
    require(all(i<config['vocab_size'] for i in ids) and ids==ids[:32]*(n//32),'TOKEN_RANGE_OR_CONSTRUCTION')
    specials=set()
    for source in (config,prompt.get('special_tokens',{})):
        for key in ('bos_token_id','eos_token_id','pad_token_id'):
            v=source.get(key)
            if isinstance(v,list):specials.update(v)
            elif v is not None:specials.add(v)
    require(not specials.intersection(ids),'SPECIAL_TOKEN')
    return identity


def validate(manifest):
    b=validate_binding(manifest.get('pilot'))
    require(not any(k in manifest for k in ('formal','batch_load','completion_path','n1_model',
        'n1_model_execution','engineering_pair','domain_qualification','gate10_workload')),'MIXED_DOMAIN')
    require(all(type(manifest.get(k)) is type(v) and manifest[k]==v for k,v in minimal_fields(b).items()),'DECLARATION')
    require(manifest.get('runner_git_commit')==b['execution_commit'] and manifest.get('runner_git_dirty') is False,'COMMIT')
    i=manifest.get('coe_input',{})
    require(set(i)=={'schema_version','shape','sample_indices','input_ids_sha256','attention_mask_sha256','batch_sha256','algorithm'}
        and i['schema_version']==specification(b['version'])['input_schema'] and i['shape']==[1,b['input_tokens']]
        and i['sample_indices']==[0] and i['algorithm']=='SHA256_COMPACT_UTF8_JSON_IN_ORDER'
        and all(isinstance(i[k],str) and re.fullmatch('[0-9a-f]{64}',i[k]) for k in
            ('input_ids_sha256','attention_mask_sha256','batch_sha256')),'INPUT_BINDING')
    return b


def make_inputs(seed,expected_sha,output,*,version=VERSION):
    require(sha(seed)==expected_sha,'SEED_HASH');v=read(seed)
    require(v['fixed_input_tokens']==512,'SEED_LENGTH');input_identity(v,version=version)
    ids=v['samples'][0]['input_ids'];require(ids==ids[:32]*16,'SEED_CONSTRUCTION')
    out=Path(output);out.mkdir(parents=True,exist_ok=False);paths={}
    for n in specification(version)['lengths']:
        p=deepcopy(v);p['fixed_input_tokens']=n
        p['samples']=[dict(sample_index=0,input_ids=ids[:32]*(n//32),attention_mask=[1]*n)]
        p['construction']=dict(rule='CYCLE_SEALED_SAMPLE0_32',source_sha256=expected_sha)
        paths[n]=out/f'input_{n}.json';write_new(paths[n],p)
    return paths


def validate_preparation(manifest,ledger,execution,tokens):
    b=validate(manifest);p=execution['observation_preparation'];r=tokens['requests'][0]
    require(p['version']==b['version'] and p['binding']==b and p['identity']==r['identity']
        and p['pid']==ledger['pid'] and type(p['tid']) is int and p['tid']>0 and p['closed'] is True
        and p['prepared_count']==2 and p['consumed_token_indices']==[0,1]
        and p['preparation_position']=='BEFORE_FINAL_DRAIN' and p['dynamic_operations_moved'] is False,'PREPARATION_RECEIPT')
    from .nvtx import make_natural_token_ready_identity,make_structured_nvtx_label
    from .results import TOKEN_READY_MECHANISM
    expected=[make_structured_nvtx_label(make_natural_token_ready_identity(r['identity'],phase=phase,token_index=i,
        callsite_id=f'{phase}.token_ready',sync_ordinal=i,token_ready_mechanism=TOKEN_READY_MECHANISM))
        for i,phase in enumerate(('prefill','decode'))]
    require(p['prepared_labels']==expected,'PREPARATION_CONTENT')


def block_contrasts(rows):
    require(rows and all(s['status']=='COMPLETE' for s in rows),'INCOMPLETE_BLOCK')
    bs=[validate_binding(s['binding']) for s in rows]
    spec=specification(bs[0]['version']);lengths=spec['lengths']
    require(len(rows)==len(lengths),'INCOMPLETE_BLOCK')
    require(len({(b['version'],b['batch_id'],b['execution_commit'],b['block']) for b in bs})==1,'BLOCK_IDENTITY')
    values={s['binding']['input_tokens']:s['result'] for s in rows}
    require(set(values)==set(lengths),'BLOCK_CONDITIONS');answer=[]
    for token,phase in enumerate(('prefill','decode')):
        require(all(len(values[n]['operations'])==2 for n in values),'TOKEN_COVERAGE')
        q={n:values[n]['operations'][token]['candidate_ns'] for n in values}
        require(all(values[n]['operations'][token]['token_index']==token
            and values[n]['operations'][token]['phase']==phase and type(q[n]) is int and q[n]>=0 for n in values),'OPERATION')
        windows={n:[w for w in values[n]['windows'] if w['phase']==phase] for n in values}
        require(all(len(windows[n])==1 for n in windows),'BLOCK_WINDOW_COVERAGE')
        gpu={n:windows[n][0]['baseline']['gpu_activity'] for n in windows}
        g={n:gpu[n]['union_ns'] for n in gpu}
        valid=all(gpu[n]['status']=='KNOWN' and type(g[n]) is int and g[n]>=0 for n in (512,2048)) and g[512]>0
        residual=Fraction(q[2048])-Fraction(q[512]*g[2048],g[512]) if valid else None
        result=dict(token_index=token,phase=phase,primary=token==0,coe_ns=q,phase_gpu_union_ns=g,
            delta_coe_ns=q[2048]-q[512],R_ns=float(residual) if residual is not None else None,
            R_exact=dict(numerator=residual.numerator,denominator=residual.denominator) if residual is not None else None,
            R_status='DEFINED_SIGNED' if valid else 'UNDEFINED_INVALID_PHASE_GPU_DENOMINATOR',
            denominator='SAME_PHASE_GPU_UNION_NOT_CUMULATIVE_W',
            interpretation='OBSERVED_PROGRAM_STRUCTURE_NOT_PURE_WAIT_OR_P0_PERFORMANCE')
        if bs[0]['version'] in (MIDPOINT_VERSION,EXTENDED_VERSION,LOW_SIDE_VERSION):
            result['coe_over_phase_gpu']={n:q[n]/g[n] if gpu[n]['status']=='KNOWN' and type(g[n]) is int and g[n]>0 else None for n in lengths}
            key='midpoint_contrasts' if bs[0]['version']==MIDPOINT_VERSION else 'input_contrasts'
            result[key]=[]
            for low,high in zip(lengths,lengths[1:]):
                valid_pair=all(gpu[n]['status']=='KNOWN' and type(g[n]) is int and g[n]>=0 for n in (low,high)) and g[low]>0
                r=Fraction(q[high])-Fraction(q[low]*g[high],g[low]) if valid_pair else None
                result[key].append(dict(lower_input=low,higher_input=high,delta_coe_ns=q[high]-q[low],
                    R_ns=float(r) if r is not None else None,R_exact=dict(numerator=r.numerator,denominator=r.denominator) if r is not None else None,
                    R_status='DEFINED_SIGNED' if valid_pair else 'UNDEFINED_INVALID_PHASE_GPU_DENOMINATOR'))
            if bs[0]['version']==LOW_SIDE_VERSION:
                # Same formula, separately labelled low-side comparison. The
                # original 512->2048 endpoint fields above remain unchanged.
                result['low_side_comparison']=result.pop(key)[0]
                result['raw_by_input']=low_side_values(values,windows,token,phase)
        answer.append(result)
    return dict(block=bs[0]['block'],per_token=answer)


def low_side_values(values,windows,token,phase):
    """Serialize already qualified facts; never reclassifies A or infers W."""
    answer={}
    for n,r in values.items():
        op=r['operations'][token];w=windows[n][0]
        duration=w['projection']['end_ns']-w['projection']['start_ns']
        budget=[b for b in r['candidate_budget_windows'] if b['phase']==phase]
        positions=[p for p in r['candidate_member_positions'] if p['token_index']==token]
        require(len(budget)==len(positions)==1,'BLOCK_BUDGET_OR_POSITION_COVERAGE')
        b=budget[0];cb=b['candidate_budgets_ns']
        require(type(duration) is int and duration>0 and duration==w['a']['T_window_ns']==b['original_a']['T_window_ns']
            and all(type(v) is int and v>=0 for v in cb.values()) and sum(cb.values())==duration,'BLOCK_BUDGET_WINDOW')
        answer[n]=dict(coe_ns=op['candidate_ns'],phase_ns=duration,coe_over_phase=op['candidate_ns']/duration,
            coe_over_phase_gpu=None if w['baseline']['gpu_activity']['status']!='KNOWN' or
                type(w['baseline']['gpu_activity']['union_ns']) is not int or w['baseline']['gpu_activity']['union_ns']<=0 else
                op['candidate_ns']/w['baseline']['gpu_activity']['union_ns'],
            original_a=deepcopy(w['a']),candidate_budgets_ns=deepcopy(cb),
            candidate_completion_budget_over_phase=cb['completion_exposure']/duration,
            phase_gpu_union_ns=w['baseline']['gpu_activity']['union_ns'],
            **{k:op[k] for k in ('copy_wall_ns','wall_ns','original_sync_ns','kernel_ns','memop_ns',
                'same_operation_all_gpu_union_ns','uncovered_ns','positions','members','member_submits')},
            necessary_member_position=deepcopy(positions[0]),
            position_interpretation='QUALIFIED_SUFFIX_CUMULATIVE_NOT_DECODE_INCREMENT')
    return answer


def run_batch(batch_id,commit,output,collect,*,version=VERSION):
    spec=specification(version)
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    r=dict(schema_version=version,status='BLOCKED',run_role='PILOT',data_role='Pilot',
        model_process_budget=spec['budget'],profile_budget=spec['budget'],automatic_retry=False,replacement=False,formal_eligible=False,
        runs=[dict(binding=b,status='NOT_RUN') for b in schedule(batch_id,commit,version=version)],blocks=[],incomplete_blocks=list(range(1,len(spec['orders'])+1)),
        measurement_validity='NOT_ASSESSED',dropped_records_status='UNKNOWN')
    def persist():
        p=out/'batch_report.pending.json';write_new(p,r);p.replace(out/'batch_report.json')
    persist();tokens={}
    for slot in r['runs']:
        b=slot['binding'];print(f"[input-pilot] block={b['block']} position={b['position']} {b['condition']} pass1 START",flush=True)
        try:
            v=collect(b,out/b['run_id']);require(v['status']==STATUS and v['binding']==b,'RESULT_BINDING')
            ids=v['token_ids'];require(isinstance(ids,list) and len(ids)==2 and all(isinstance(t,list) and len(t)==1
                and type(t[0]) is int and t[0]>=0 for t in ids),'ACTUAL_TOKENS')
            n=b['input_tokens'];require(n not in tokens or tokens[n]==ids,'SAME_INPUT_TOKEN_PARITY');tokens[n]=ids
            slot.update(status='COMPLETE',result=v)
            rows=[s for s in r['runs'] if s['binding']['block']==b['block']]
            if all(s['status']=='COMPLETE' for s in rows):
                r['blocks'].append(block_contrasts(rows));r['incomplete_blocks'].remove(b['block'])
        except Exception as exc:
            slot.update(status='BLOCKED',error=f'{type(exc).__name__}: {exc}');persist();break
        persist()
    else:r['status']=spec['status'];persist()
    return r
