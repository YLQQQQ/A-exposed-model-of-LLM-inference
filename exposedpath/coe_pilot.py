"""Closed prospective COE Pilot execution domain; old G1/Pilot stay unchanged."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

from .gate8_isolated_preflight import read, sha, write_new

VERSION='COE-NATURAL-PREFILL-PILOT/0.1'
PROFILE='COE_LOCAL_PREFILL_PILOT/0.1'
PASS_VERSION='exposedpath-coe-pilot-pass/0.1.0'
EXECUTION_VERSION='exposedpath-coe-pilot-execution/0.1.0'
PRODUCER_VERSION='exposedpath-coe-pilot-producer/0.1.0'
TOKEN_VERSION='exposedpath-coe-pilot-tokens/0.1.0'
RECEIPT_VERSION='exposedpath-coe-pilot-input/0.1.0'
ORDERS=((1,2,4),(2,4,1),(4,1,2))
SOFTWARE=dict(runtime_version='python3.11.16',inference_framework_version='torch2.6.0+cu124',cuda_version_used='12.4')


def require(ok,reason):
    if not ok:raise ValueError('COE_PILOT_'+reason)


def active(value):
    from .coe_input_pilot import active as input_active
    return (isinstance(value,dict) and value.get('version')==VERSION) or input_active(value)


def software_identity(torch):
    import platform
    return dict(runtime_version='python'+platform.python_version(),
        inference_framework_version='torch'+torch.__version__,cuda_version_used=torch.version.cuda or 'unknown')


def validate_software(actual,manifest):
    require(actual==SOFTWARE and all(manifest.get(k)==v for k,v in actual.items()),'SOFTWARE_IDENTITY')


def schedule(batch_id,commit):
    require(isinstance(batch_id,str) and re.fullmatch(r'[A-Za-z0-9_-]{1,70}',batch_id),'BATCH_ID')
    require(isinstance(commit,str) and re.fullmatch(r'[0-9a-f]{40}',commit),'EXECUTION_COMMIT')
    return [dict(version=VERSION,batch_id=batch_id,execution_commit=commit,block=b,position=p,
        condition=f'B{n}',batch_size=n,variant=None,pair_id=f'{batch_id}-b{b}',
        run_id=f'{batch_id}-b{b}-B{n}-pass1',pass_id='pass1',input_tokens=512,output_tokens=2,
        warmup_count=3,repeat_count=1,purpose='CANDIDATE_STRUCTURE_PILOT_ONLY',
        declaration_role='PRE_EXECUTION',formal_eligible=False)
        for b,order in enumerate(ORDERS,1) for p,n in enumerate(order,1)]


def validate_binding(value):
    from . import coe_input_pilot as axis
    if axis.active(value):return axis.validate_binding(value)
    require(isinstance(value,dict),'BINDING')
    require(any(value==b and all(type(value[k]) is type(v) for k,v in b.items())
        for b in schedule(value.get('batch_id'),value.get('execution_commit'))),'BINDING')
    return value


def minimal_fields(binding):
    from . import coe_input_pilot as axis
    if axis.active(binding):return axis.minimal_fields(binding)
    b=validate_binding(binding)
    from .gate8_engineering_contract import declaration
    scope=declaration('sdpa');scope['profile']=PROFILE
    return dict(pilot=deepcopy(b),run_role='PILOT',data_role='Pilot',run_id=b['run_id'],
        fixed_input_tokens=512,fixed_output_tokens=2,batch_size=b['batch_size'],warmup_count=3,repeat_count=1,
        execution_mode='eager',attention_backend='sdpa',dtype_and_quantization='fp16',
        sampling_config={'do_sample':False},study_mode='G1_NATURAL',n1_intervention=None,
        engineering_scope=scope)


def input_identity(prompt,*,binding=None):
    from . import coe_input_pilot as axis
    if axis.active(binding):axis.validate_binding(binding);return axis.input_identity(prompt)
    samples=prompt['samples'];n=len(samples)
    require(n in (1,2,4) and prompt['fixed_input_tokens']==512,'INPUT_SHAPE')
    require([s.get('sample_index') for s in samples]==list(range(n)),'SAMPLE_IDENTITY')
    ids=[s['input_ids'] for s in samples];masks=[s['attention_mask'] for s in samples]
    require(all(len(x)==512 and all(type(i) is int and i>=0 for i in x) for x in ids),'INPUT_VALUES')
    require(all(x==[1]*512 and all(type(i) is int for i in x) for x in masks),'MASK')
    require(all(x==ids[0] for x in ids),'CLONED_SAMPLES')
    digest=lambda v:hashlib.sha256(json.dumps(v,separators=(',',':'),ensure_ascii=False).encode('utf8')).hexdigest()
    payload=dict(shape=[n,512],sample_indices=list(range(n)),input_ids=ids,attention_mask=masks)
    return dict(schema_version='coe-batch-input/0.1.0',shape=[n,512],sample_indices=list(range(n)),
        input_ids_sha256=digest(ids),attention_mask_sha256=digest(masks),batch_sha256=digest(payload),
        algorithm='SHA256_COMPACT_UTF8_JSON_IN_ORDER')


def validate_input(prompt,config,batch,*,binding=None):
    from . import coe_input_pilot as axis
    if axis.active(binding):axis.validate_binding(binding);return axis.validate_input(prompt,config,batch)
    from .gate10_workload import validate_input as single
    identity=input_identity(prompt)
    require(identity['shape']==[batch,512],'INPUT_SHAPE')
    single({**prompt,'samples':prompt['samples'][:1]},config,512)
    return identity


def validate(manifest):
    from . import coe_input_pilot as axis
    if axis.active(manifest.get('pilot')):return axis.validate(manifest)
    b=validate_binding(manifest.get('pilot'))
    require(not any(k in manifest for k in ('formal','batch_load','completion_path','n1_model',
        'n1_model_execution','engineering_pair','gate10_workload','domain_qualification')),'MIXED_DOMAIN')
    require(all(type(manifest.get(k)) is type(v) and manifest[k]==v
        for k,v in minimal_fields(b).items()),'DECLARATION')
    require(manifest.get('runner_git_commit')==b['execution_commit'] and manifest.get('runner_git_dirty') is False,'COMMIT')
    i=manifest.get('coe_input',{})
    require(set(i)=={'schema_version','shape','sample_indices','input_ids_sha256','attention_mask_sha256','batch_sha256','algorithm'}
        and i['schema_version']=='coe-batch-input/0.1.0' and i['shape']==[b['batch_size'],512]
        and i['sample_indices']==list(range(b['batch_size']))
        and i['algorithm']=='SHA256_COMPACT_UTF8_JSON_IN_ORDER'
        and all(isinstance(i[k],str) and re.fullmatch('[0-9a-f]{64}',i[k]) for k in
            ('input_ids_sha256','attention_mask_sha256','batch_sha256')),'INPUT_BINDING')
    return b


def validate_prepared(manifest,prepared,root):
    b=validate(manifest)
    require('target_python' in manifest and 'isolated_preflight_version' in manifest,'VERIFIED_ENTRY')
    require(sha(Path(prepared)/'prompt.json')==manifest['prompt_tokens_sha256']
        and sha(Path(root)/'exposedpath/runner.py')==manifest['runner_source_sha256'],'INPUT_HASH')
    require(validate_input(read(Path(prepared)/'prompt.json'),read(Path(manifest['model_id'])/'config.json'),
        b['batch_size'],binding=b)==manifest['coe_input'],'BATCH_CONTENT')
    from . import coe_input_pilot as axis
    if axis.active(b):
        require(manifest.get('preparation_source_sha256')==sha(Path(root)/'exposedpath/observation_preparation.py')
            and manifest.get('input_pilot_source_sha256')==sha(Path(root)/'exposedpath/coe_input_pilot.py'),'PREPARATION_SOURCE_HASH')


def validate_actual_requests(manifest,ledger):
    b=validate(manifest)
    from .gate11_warmup import request_plan
    require(ledger['pilot']==b and ledger['schema_version']==PASS_VERSION
        and ledger['run_role']=='PILOT' and ledger['data_role']=='Pilot','LEDGER')
    require([dict(request_id=r['identity']['request_id'],repeat_id=r['identity']['repeat_id'],request_role=r['request_role'])
        for r in ledger['requests']]==request_plan(b),'ACTUAL_PLAN')
    require(all(r['outcome']=='COMPLETE' and not r['reasons'] and r['expected_output_tokens']==2
        and ((r['actual_output_tokens'] is None and r['early_eos'] is None) if r['request_role']=='warmup'
        else (r['actual_output_tokens']==2 and r['early_eos'] is False)) for r in ledger['requests']),'ACTUAL_COMPLETION')


def observation(identity,result,manifest,actual_input):
    from . import coe_input_pilot as axis
    if axis.active(manifest.get('pilot')):
        from .observation_preparation import observation as prepared_observation
        require(actual_input==manifest['coe_input'],'ACTUAL_INPUT_IDENTITY')
        return dict(prepared_observation(identity,result,manifest),input_identity=deepcopy(actual_input))
    from .batch_load import observation as batch_observation
    require(actual_input==manifest['coe_input'],'ACTUAL_INPUT_IDENTITY')
    return dict(batch_observation(identity,result,manifest['batch_size']),input_identity=deepcopy(actual_input))


def validate_tokens(path,manifest,ledger,execution,manifest_path,producer_path):
    b=validate(manifest);validate_actual_requests(manifest,ledger)
    require(execution.get('schema_version')==EXECUTION_VERSION and execution.get('pilot')==b
        and execution.get('run_role')=='PILOT' and execution.get('data_role')=='Pilot'
        and execution.get('pilot_tokens_sha256')==sha(path),'EXECUTION_TOKEN_HASH')
    t=read(path)
    require(set(t)=={'schema_version','pilot','manifest_sha256','producer_receipt_sha256','requests'}
        and t['schema_version']==TOKEN_VERSION and t['pilot']==b
        and t['manifest_sha256']==sha(manifest_path) and t['producer_receipt_sha256']==sha(producer_path),'TOKEN_LINEAGE')
    require(len(t['requests'])==1,'TOKEN_REQUESTS');r=t['requests'][0];n=b['batch_size']
    require(set(r)=={'identity','actual_input_shape','sample_indices','token_ids',
        'actual_output_tokens_per_sample','early_eos','input_identity'}
        and r['identity']==ledger['requests'][-1]['identity'] and r['actual_input_shape']==[n,b['input_tokens']]
        and r['sample_indices']==list(range(n)) and r['actual_output_tokens_per_sample']==[2]*n
        and r['early_eos'] is False and r['input_identity']==manifest['coe_input'],'TOKEN_IDENTITY_SHAPE')
    ids=r['token_ids']
    require(isinstance(ids,list) and len(ids)==2 and all(isinstance(t,list) and len(t)==n
        and all(type(v) is int and v>=0 for v in t) for t in ids),'TOKEN_VALUES')
    from . import coe_input_pilot as axis
    if axis.active(b):axis.validate_preparation(manifest,ledger,execution,t)
    return ids


def execution_extension(manifest,ledger,execution,execution_path,manifest_path,producer_path,token_path):
    require(token_path is not None and Path(token_path).resolve()==Path(execution_path).resolve().parent/'pilot_tokens.json','TOKEN_PATH')
    validate_tokens(token_path,manifest,ledger,execution,manifest_path,producer_path)
    fields={'pilot','run_role','data_role','pilot_tokens_sha256'}
    from . import coe_input_pilot as axis
    if axis.active(manifest.get('pilot')):
        require(sha(Path(execution_path).parent/'preparation_source.py')==manifest['preparation_source_sha256'],'EXECUTED_PREPARATION_SOURCE_HASH')
        require(sha(Path(execution_path).parent/'input_pilot_source.py')==manifest['input_pilot_source_sha256'],'EXECUTED_INPUT_PILOT_SOURCE_HASH')
        fields.add('observation_preparation')
    return fields,EXECUTION_VERSION


def make_inputs(seed,expected_sha,output):
    require(sha(seed)==expected_sha,'SEED_HASH');value=read(seed);input_identity(value)
    require(len(value['samples'])==1,'SEED_SHAPE')
    out=Path(output);out.mkdir(parents=True,exist_ok=False);paths={}
    for n in (1,2,4):
        p=deepcopy(value);p['samples']=[dict(sample_index=i,input_ids=list(value['samples'][0]['input_ids']),
            attention_mask=list(value['samples'][0]['attention_mask'])) for i in range(n)]
        p['construction']=dict(rule='COE_CLONE_SEALED_512_SAMPLE0',source_sha256=expected_sha)
        path=out/f'input_b{n}.json';write_new(path,p);paths[n]=path
    return paths


def run_batch(batch_id,commit,output,collect):
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    report=dict(schema_version=VERSION,status='BLOCKED',automatic_retry=False,formal_eligible=False,
        runs=[dict(binding=b,status='NOT_RUN') for b in schedule(batch_id,commit)],blocks=[],incomplete_blocks=[1,2,3],
        dropped_records_status='UNKNOWN',measurement_validity='NOT_ASSESSED')
    # Updated after each slot, including failure; no incomplete-block stitching.
    def persist():
        path=out/'batch_report.json';temp=out/'batch_report.pending.json'
        write_new(temp,report);temp.replace(path)
    persist();reference=None
    for slot in report['runs']:
        b=slot['binding'];print(f"[coe] block={b['block']} position={b['position']} B{b['batch_size']} pass1 START",flush=True)
        try:
            r=collect(b,out/b['run_id'])
            require(r['status']=='COE_PILOT_PREFILL_ONLY_PENDING_REVIEW' and r['binding']==b,'LOCAL_RESULT')
            require(type(r['coe']['candidate_ns']) is int and r['coe']['candidate_ns']>=0,'COE_VALUE')
            tokens=r['token_ids'];n=b['batch_size']
            require(len(tokens)==2 and all(len(t)==n and all(type(v) is int and v>=0 for v in t) for t in tokens),'BATCH_TOKEN_SHAPE')
            scalar=[t[0] for t in tokens]
            require(all(all(v==scalar[i] for v in t) for i,t in enumerate(tokens)),'CLONED_SAMPLE_TOKEN_PARITY')
            require(reference is None or scalar==reference,'CROSS_RUN_TOKEN_PARITY');reference=scalar
            slot.update(status='COMPLETE',result=r)
            rows=[s for s in report['runs'] if s['binding']['block']==b['block']]
            if all(s['status']=='COMPLETE' for s in rows):
                q={s['binding']['batch_size']:s['result']['coe']['candidate_ns'] for s in rows}
                report['blocks'].append(dict(block=b['block'],b4_minus_b1_candidate_ns=q[4]-q[1]))
                report['incomplete_blocks'].remove(b['block'])
        except Exception as exc:
            slot.update(status='BLOCKED',error=f'{type(exc).__name__}: {exc}');persist();break
        persist()
    else:report['status']='FIXED_NINE_COMPLETE_STOP_FOR_REVIEW';persist()
    return report
