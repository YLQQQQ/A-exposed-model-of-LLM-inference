"""Closed, prospective batch-load Engineering diagnostic; no new A/S/B semantics."""
from copy import deepcopy
import re
from pathlib import Path

from .gate8_isolated_preflight import read, sha, write_new

VERSION='BATCH-LOAD-ENGINEERING/0.1'
PROFILE='TARGET_SCOPE_ENGINEERING_BATCH_LOAD/0.1'
PASS_VERSION='exposedpath-pass-identity/0.5.0'
EXECUTION_VERSION='exposedpath-batch-load-execution/0.1.0'
TOKEN_VERSION='exposedpath-batch-load-tokens/0.1.0'


def require(ok,reason):
    if not ok: raise ValueError('BATCH_LOAD_'+reason)


def active(value):
    from .memset_prefill import active as parameter_active
    return (isinstance(value,dict) and value.get('version')==VERSION) or parameter_active(value)


def schedule(batch_id):
    require(isinstance(batch_id,str) and re.fullmatch(r'[A-Za-z0-9_-]{1,80}',batch_id),'BATCH_ID')
    return [dict(version=VERSION,batch_id=batch_id,condition=f'B{n}',batch_size=n,
        pair_id=f'{batch_id}-B{n}',run_id=f'{batch_id}-B{n}-{p}',pass_id=p,
        input_tokens=512,output_tokens=2,warmup_count=3,repeat_count=1,
        purpose='SAME_COMPLETION_BATCH_DIAGNOSTIC_ONLY',declaration_role='PRE_EXECUTION',
        formal_eligible=False) for n in (1,4) for p in ('pass0','pass1')]


def validate_binding(value):
    from . import memset_prefill as parameters
    if parameters.active(value):return parameters.validate_binding(value)
    require(isinstance(value,dict),'BINDING')
    require(any(value==r and all(type(value[k]) is type(v) for k,v in r.items())
        for r in schedule(value.get('batch_id'))),'BINDING')
    return value


def minimal_fields(binding):
    from . import memset_prefill as parameters
    if parameters.active(binding):return parameters.minimal_fields(binding)
    validate_binding(binding)
    from .gate8_engineering_contract import declaration
    from exposedpath_v141.gate9_domain import G1,declaration as domain
    scope=declaration('sdpa');scope['profile']=PROFILE
    return dict(batch_load=deepcopy(binding),run_role='ENGINEERING',data_role='Engineering',
        run_id=binding['run_id'],fixed_input_tokens=512,fixed_output_tokens=2,
        batch_size=binding['batch_size'],warmup_count=3,repeat_count=1,execution_mode='eager',
        attention_backend='sdpa',dtype_and_quantization='fp16',sampling_config={'do_sample':False},
        study_mode='G1_NATURAL',n1_intervention=None,engineering_scope=scope,
        domain_qualification=domain(G1),engineering_pair=dict(schema_version='gate8-engineering-pair/0.1',
            pair_id=binding['pair_id'],pass_id=binding['pass_id']))


def validate(manifest):
    from . import memset_prefill as parameters
    if parameters.active(manifest.get('batch_load')):return parameters.validate(manifest)
    b=validate_binding(manifest.get('batch_load'))
    require(not any(k in manifest for k in ('pilot','formal','n1_model','n1_model_execution','gate10_workload')),'ROLE_OR_DOMAIN')
    if 'completion_path' in manifest:
        from .completion_path import validate as completion_validate
        completion_validate(manifest)
    else:
        require(all(type(manifest.get(k)) is type(v) and manifest[k]==v
            for k,v in minimal_fields(b).items()),'DECLARATION')
    return b


def request_plan(binding):
    validate_binding(binding)
    return [dict(request_id=f'warmup-{i}',repeat_id=f'warmup-{i}',request_role='warmup')
        for i in range(3)]+[dict(request_id='request-0',repeat_id='0',request_role='measured')]


def validate_input(prompt,config,batch):
    require(type(batch) is int and batch in (1,4),'BATCH_SIZE')
    from .gate10_workload import validate_input as single
    samples=prompt.get('samples')
    require(isinstance(samples,list) and len(samples)==batch,'SAMPLE_COUNT')
    # Reuse token range, special-token, mask and frozen 32-token cycling checks.
    single({**prompt,'samples':samples[:1]},config,512)
    require([s.get('sample_index') for s in samples]==list(range(batch))
        and all(type(s.get('sample_index')) is int for s in samples),'SAMPLE_IDENTITY')
    require(all(s.get('input_ids')==samples[0]['input_ids'] and s.get('attention_mask')==[1]*512
        for s in samples),'CLONE_INPUT')


def make_inputs(seed,expected_sha,output):
    require(sha(seed)==expected_sha.lower(),'SEED_HASH')
    from .workload import load_prompt_tokens
    value=load_prompt_tokens(Path(seed))
    require(value['fixed_input_tokens']==512 and len(value['samples'])==1,'SEED_SHAPE')
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    paths=[]
    for n in (1,4):
        prompt=deepcopy(value)
        prompt['samples']=[dict(sample_index=i,input_ids=list(value['samples'][0]['input_ids']),
            attention_mask=list(value['samples'][0]['attention_mask'])) for i in range(n)]
        prompt['construction']=dict(rule='CLONE_SEALED_512_SAMPLE0',source_sha256=expected_sha.lower())
        path=out/f'input_b{n}.json';write_new(path,prompt);paths.append(path)
    return paths


def observation(identity,result,batch):
    require(result['batch_size']==batch and result['actual_input_tokens']==512,'ACTUAL_INPUT_SHAPE')
    tokens=[list(t.host_token_ids) for t in result['token_ready_boundaries']]
    require(len(tokens)==result['actual_output_tokens'] and all(len(t)==batch for t in tokens),'TOKEN_SHAPE')
    return dict(identity=identity,actual_input_shape=[batch,512],sample_indices=list(range(batch)),
        token_ids=tokens,actual_output_tokens_per_sample=[len(tokens)]*batch,early_eos=result['early_eos'])


def validate_actual_requests(manifest,ledger):
    b=validate(manifest)
    from .completion_path import PASS_VERSION as completion_pass
    version=completion_pass if 'completion_path' in manifest else PASS_VERSION
    require(ledger.get('batch_load')==b and ledger['schema_version']==version
        and ledger['run_role']=='ENGINEERING' and ledger['data_role']=='Engineering','LEDGER')
    require([dict(request_id=r['identity']['request_id'],repeat_id=r['identity']['repeat_id'],request_role=r['request_role'])
        for r in ledger['requests']]==request_plan(b),'ACTUAL_PLAN')
    require(all(r['outcome']=='COMPLETE' and not r['reasons'] and r['expected_output_tokens']==2
        and ((r['actual_output_tokens'] is None and r['early_eos'] is None) if r['request_role']=='warmup'
        else (r['actual_output_tokens']==2 and r['early_eos'] is False)) for r in ledger['requests']),'ACTUAL_COMPLETION')


def validate_tokens(path,manifest,ledger,execution,manifest_path,producer_path):
    b=validate(manifest);validate_actual_requests(manifest,ledger)
    from .completion_path import EXECUTION_VERSION as completion_execution
    version=completion_execution if 'completion_path' in manifest else EXECUTION_VERSION
    from . import memset_prefill as parameters
    if parameters.active(b):version=parameters.EXECUTION_VERSION
    require(execution.get('schema_version')==version and execution.get('batch_load')==b
        and execution.get('batch_tokens_sha256')==sha(path),'EXECUTION_TOKEN_HASH')
    value=read(path)
    require(set(value)=={'schema_version','batch_load','manifest_sha256','producer_receipt_sha256','requests'}
        and value['schema_version']==TOKEN_VERSION and value['batch_load']==b
        and value['manifest_sha256']==sha(manifest_path)
        and value['producer_receipt_sha256']==sha(producer_path),'TOKEN_LINEAGE')
    require(len(value['requests'])==1,'TOKEN_REQUESTS')
    r=value['requests'][0];n=b['batch_size']
    require(set(r)=={'identity','actual_input_shape','sample_indices','token_ids','actual_output_tokens_per_sample','early_eos'}
        and r['identity']==ledger['requests'][-1]['identity'] and r['actual_input_shape']==[n,512]
        and r['sample_indices']==list(range(n)) and r['actual_output_tokens_per_sample']==[2]*n
        and r['early_eos'] is False,'TOKEN_IDENTITY_OR_SHAPE')
    tokens=r['token_ids']
    require(isinstance(tokens,list) and len(tokens)==2 and all(isinstance(t,list) and len(t)==n
        and all(type(i) is int and i>=0 for i in t) for t in tokens),'TOKEN_VALUES')
    return tokens


def execution_extension(manifest,ledger,execution,execution_path,manifest_path,producer_path,token_path):
    require(token_path is not None and Path(token_path).resolve()==Path(execution_path).resolve().parent/'batch_tokens.json','TOKEN_PATH')
    path=Path(token_path)
    validate_tokens(path,manifest,ledger,execution,manifest_path,producer_path)
    from . import memset_prefill as parameters
    if parameters.active(manifest.get('batch_load')):
        require(execution.get('memset_parameters_sha256')==sha(Path(execution_path).parent/'memset_parameters.json'),'PARAMETER_FILE_HASH')
        return {'batch_load','batch_tokens_sha256','memset_parameters_sha256'},parameters.EXECUTION_VERSION
    if 'completion_path' in manifest:
        from .completion_path import validate_calls,EXECUTION_VERSION as completion_version
        validate_calls(manifest,ledger,execution)
        return {'batch_load','batch_tokens_sha256','completion_path','completion_calls'},completion_version
    return {'batch_load','batch_tokens_sha256'},EXECUTION_VERSION


def validate_prepared(manifest,prepared,root):
    from . import memset_prefill as parameters
    if parameters.active(manifest.get('batch_load')):return parameters.validate_prepared(manifest,prepared,root)
    validate(manifest)
    require(sha(Path(prepared)/'prompt.json')==manifest['prompt_tokens_sha256']
        and sha(Path(root)/'exposedpath/runner.py')==manifest['runner_source_sha256'],'INPUT_HASH')
    validate_input(read(Path(prepared)/'prompt.json'),read(Path(manifest['model_id'])/'config.json'),manifest['batch_size'])
    require('target_python' in manifest and 'isolated_preflight_version' in manifest,'VERIFIED_ENTRY')


def run_batch(batch_id,output,collect):
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    result=dict(version=VERSION,status='BLOCKED',role='Engineering',automatic_retry=False,
        model_process_budget=4,profile_budget=2,runs=[dict(binding=b,status='NOT_RUN') for b in schedule(batch_id)])
    for row in result['runs']:
        b=row['binding'];print(f"[batch] {b['condition']} {b['pass_id']} START",flush=True)
        try:
            row.update(collect(b,out/b['run_id']))
            require(row['status']=='RUN_COMPLETE_PENDING_REVIEW','RUN_FAILED')
        except Exception as exc:
            row.update(status='BLOCKED',error=f'{type(exc).__name__}: {exc}');break
        finally:write_new(out/(b['run_id']+'.receipt.json'),row)
    else:result['status']='BATCH_COMPLETE_STOP_FOR_REVIEW'
    write_new(out/'batch_report.json',result)
    return result
