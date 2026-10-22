"""Closed, prospective Gate11 role extension. Not a scientific qualification."""
from copy import deepcopy
import hashlib
import re
from pathlib import Path

VERSION = 'G11-LIMITED-PILOT/0.1'
PASS_VERSION = 'exposedpath-pass-identity/0.2.0'
EXECUTION_VERSION = 'exposedpath-pilot-execution/0.1.0'
ORDERS = (('G32','N0','Nm','N16','G512'), ('G512','Nm','N16','N0','G32'),
          ('G32','N16','N0','Nm','G512'))
CONDITIONS = {'G32':(32,None), 'G512':(512,None), 'N0':(32,'V0'),
              'Nm':(32,'Vmarker'), 'N16':(32,'Vsync')}
CUPTI_INPUT_VERSION='CUPTI-INPUT-PRODUCER-PILOT/0.1.0'
CUPTI_PLAN_VERSION='CUPTI-INPUT-PLAN/0.2.0'
CUPTI_PRODUCER_VERSION='CUPTI-INPUT-PRODUCER-PILOT/0.2.0'


def validate_cupti_plan(plan):
    """Finite declaration, not a list of qualified input sizes or a GPU probe."""
    require(isinstance(plan,dict) and set(plan)=={'schema_version','role','input_lengths','blocks','orders','comparisons'}
        and plan['schema_version']==CUPTI_PLAN_VERSION and plan['role'] in ('Pilot','Engineering'),'CUPTI_PLAN')
    lengths=plan['input_lengths'];orders=plan['orders'];count=plan['blocks']
    require(isinstance(lengths,list) and lengths and all(type(n) is int and n>=32 and n%32==0 for n in lengths)
        and len(lengths)==len(set(lengths)) and type(count) is int and count>0
        and count*len(lengths)<=64 and isinstance(orders,list) and len(orders)==count,'CUPTI_PLAN_SIZE')
    require(all(isinstance(order,list) and len(order)==len(lengths) and all(type(n) is int for n in order)
        and set(order)==set(lengths) for order in orders),'CUPTI_PLAN_ORDER')
    comparisons=plan['comparisons'];seen=set()
    require(isinstance(comparisons,list),'CUPTI_PLAN_COMPARISONS')
    for v in comparisons:
        require(isinstance(v,dict) and set(v)=={'low','high','role','token_indices'} and
            type(v['low']) is int and type(v['high']) is int and v['low'] in lengths and v['high'] in lengths
            and v['low']<v['high'] and v['role'] in ('PRIMARY','SECONDARY') and
            isinstance(v['token_indices'],list) and v['token_indices'] and
            all(type(i) is int and i in (0,1) for i in v['token_indices']) and
            len(v['token_indices'])==len(set(v['token_indices'])),'CUPTI_PLAN_COMPARISON')
        for i in v['token_indices']:
            key=(v['low'],v['high'],i)
            require(key not in seen,'CUPTI_PLAN_DUPLICATE_COMPARISON');seen.add(key)
    return plan


def cupti_plan_schedule(batch_id,native_commit,plan):
    validate_cupti_plan(plan)
    require(isinstance(batch_id,str) and re.fullmatch('[A-Za-z0-9_-]{1,32}',batch_id),'CUPTI_PLAN_BATCH')
    require(native_commit=='6c744bf52daff3fc54571e264a0c34e3207aa1df','CUPTI_PLAN_NATIVE')
    return [dict(version=CUPTI_PRODUCER_VERSION,batch_id=batch_id,execution_commit=native_commit,
        plan=deepcopy(plan),block=b,position=p,condition=f'G{n}P',input_tokens=n,
        batch_size=1,output_tokens=2,warmup_count=3,repeat_count=1,
        run_id=f'{batch_id}-b{b}-G{n}P-pass1',pair_id=f'{batch_id}-b{b}',pass_id='pass1',
        observation_variant='P',purpose='CUPTI_CANDIDATE_INPUT_RESPONSE_ONLY',
        warmup_position='BEFORE_SUBSCRIPTION_OUTSIDE_MEASURED_LEDGER',declaration_role='PRE_EXECUTION',formal_eligible=False)
        for b,order in enumerate(plan['orders'],1) for p,n in enumerate(order,1)]


def cupti_schedule(batch_id,native_commit):
    """Role only: resident warmups are observed before the single session.

    This is not the old Gate11 warmup request-plan contract or a provider grant.
    """
    require(isinstance(batch_id,str) and re.fullmatch('[A-Za-z0-9_-]{1,40}',batch_id),'CUPTI_BATCH_ID')
    require(native_commit=='6c744bf52daff3fc54571e264a0c34e3207aa1df','CUPTI_NATIVE_COMMIT')
    return [dict(version=CUPTI_INPUT_VERSION,batch_id=batch_id,execution_commit=native_commit,block=b,position=p,
        condition=f'G{n}P',input_tokens=n,batch_size=1,output_tokens=2,warmup_count=3,repeat_count=1,
        run_id=f'{batch_id}-b{b}-G{n}P-pass1',pair_id=f'{batch_id}-b{b}',pass_id='pass1',
        observation_variant='P',purpose='CUPTI_CANDIDATE_INPUT_RESPONSE_ONLY',
        warmup_position='BEFORE_SUBSCRIPTION_OUTSIDE_MEASURED_LEDGER',declaration_role='PRE_EXECUTION',formal_eligible=False)
        for b,order in enumerate(((512,1024,2048),(1024,2048,512),(2048,512,1024)),1) for p,n in enumerate(order,1)]


def require(ok, reason):
    if not ok:
        raise ValueError('PILOT_' + reason)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()


def schedule(batch_id, *, blocks=3):
    require(isinstance(batch_id,str) and re.fullmatch(r'[A-Za-z0-9_-]{1,100}',batch_id), 'BATCH_ID')
    require(type(blocks) is int and blocks==3, 'FIRST_BATCH_ONLY')
    rows=[]
    for b,order in enumerate(ORDERS,1):
        for j,condition in enumerate(order,1):
            passes=('pass0','pass1') if (b+j)%2==0 else ('pass1','pass0')
            for pass_id in passes:
                pair=f'{batch_id}-b{b}-{condition}'
                rows.append(dict(version=VERSION,batch_id=batch_id,block=b,position=j,
                    condition=condition,variant=CONDITIONS[condition][1],pair_id=pair,
                    run_id=pair+'-'+pass_id,pass_id=pass_id,pass_order=list(passes),
                    purpose='POLICY_ESTIMATION_ONLY',declaration_role='PRE_EXECUTION',
                    formal_eligible=False))
    return rows


def validate_binding(value):
    require(isinstance(value,dict),'BINDING')
    if value.get('version')==CUPTI_PRODUCER_VERSION:
        require(value.get('plan',{}).get('role')=='Pilot' and any(value==r and
            all(type(value[k]) is type(v) for k,v in r.items()) for r in
            cupti_plan_schedule(value.get('batch_id'),value.get('execution_commit'),value.get('plan'))),'CUPTI_PLAN_BINDING')
        return value
    if value.get('version')==CUPTI_INPUT_VERSION:
        require(any(value==r and all(type(value[k]) is type(v) for k,v in r.items())
            for r in cupti_schedule(value.get('batch_id'),value.get('execution_commit'))),'CUPTI_BINDING')
        return value
    from . import coe_pilot
    if coe_pilot.active(value): return coe_pilot.validate_binding(value)
    from . import gate11_warmup as warmup
    if warmup.active(value):
        return warmup.validate_binding(value)
    candidates=schedule(value.get('batch_id'))
    require(any(value==r and all(type(value[k]) is type(v) for k,v in r.items()) for r in candidates),'BINDING')
    return value


def minimal_fields(binding):
    validate_binding(binding)
    from . import coe_pilot
    if coe_pilot.active(binding): return coe_pilot.minimal_fields(binding)
    from exposedpath_v141.gate9_domain import declaration as domain, N1, G1
    from .n1_model import declaration, execution_declaration, CALLSITE
    length,variant=CONDITIONS[binding['condition']]
    from .gate11_warmup import active
    count=binding['warmup_count'] if active(binding) else 1
    result=dict(pilot=deepcopy(binding),run_role='PILOT',data_role='Pilot',run_id=binding['run_id'],
        fixed_input_tokens=length,fixed_output_tokens=2,batch_size=1,warmup_count=count,repeat_count=1,
        execution_mode='eager',attention_backend='sdpa',dtype_and_quantization='fp16',
        sampling_config={'do_sample':False},domain_qualification=domain(N1 if variant else G1),
        study_mode='N1_INTERVENTION' if variant else 'G1_NATURAL',n1_intervention=None)
    if variant:
        result.update(n1_model=declaration(variant),n1_model_execution=execution_declaration(warmup_count=count, control=active(binding)),
            n1_intervention=dict(sync_origin='n1_intervention',callsite_id=CALLSITE,intervention_variant_id=variant))
    return result


def validate(manifest):
    from . import coe_pilot
    if coe_pilot.active(manifest.get('pilot')): return coe_pilot.validate(manifest)
    binding=validate_binding(manifest.get('pilot'))
    expected=minimal_fields(binding)
    require(all(type(manifest.get(k)) is type(v) and manifest[k]==v for k,v in expected.items()),'DECLARATION_CONFLICT')
    require('engineering_pair' not in manifest,'LEGACY_PAIR_CONFLICT')
    if binding['variant'] is None:
        require('n1_model' not in manifest and 'n1_model_execution' not in manifest,'WRONG_DOMAIN')
    return binding


def roles(manifest):
    """No role inference from a friendly label; Pilot requires the whole declaration."""
    if 'formal' in manifest or manifest.get('run_role')=='FORMAL' or manifest.get('data_role')=='Formal':
        from .formal_protocol import validate as validate_formal
        validate_formal(manifest)
        return dict(run_role='FORMAL',data_role='Formal')
    if 'pilot' in manifest or manifest.get('run_role')=='PILOT' or manifest.get('data_role')=='Pilot':
        validate(manifest)
        return dict(run_role='PILOT',data_role='Pilot')
    require(manifest.get('run_role')=='ENGINEERING' and manifest.get('data_role')=='Engineering','ROLE')
    return dict(run_role='ENGINEERING',data_role='Engineering')


def validate_prepared(manifest, prepared, root):
    from . import coe_pilot
    if coe_pilot.active(manifest.get('pilot')): return coe_pilot.validate_prepared(manifest,prepared,root)
    from .gate8_engineering_contract import validate_declaration
    from .workload import load_prompt_tokens
    validate(manifest); validate_declaration(manifest)
    require('target_python' in manifest and 'isolated_preflight_version' in manifest,'VERIFIED_ENTRY')
    prompt=Path(prepared)/'prompt.json'
    require(sha(prompt)==manifest['prompt_tokens_sha256'] and sha(Path(root)/'exposedpath/runner.py')==manifest['runner_source_sha256'],'INPUT_HASH')
    require(load_prompt_tokens(prompt)['fixed_input_tokens']==manifest['fixed_input_tokens'],'INPUT_LENGTH')
    if 'n1_model' in manifest:
        from .n1_model import validate_prepared as n1
        n1(manifest,prepared,root)


def validate_tokens(path, manifest, ledger, execution, manifest_path, producer_path):
    from . import coe_pilot
    if coe_pilot.active(manifest.get('pilot')):
        return coe_pilot.validate_tokens(path,manifest,ledger,execution,manifest_path,producer_path)
    import json
    binding=validate(manifest)
    pass_version,execution_version=versions(binding)
    require(ledger.get('pilot')==binding and ledger['schema_version']==pass_version
        and ledger['run_role']=='PILOT' and ledger['data_role']=='Pilot','PRODUCER_ROLE')
    require(execution.get('schema_version')==execution_version and execution.get('pilot')==binding
        and execution.get('run_role')=='PILOT' and execution.get('data_role')=='Pilot'
        and execution.get('pilot_tokens_sha256')==sha(path),'EXECUTION_ROLE_OR_TOKEN_HASH')
    value=json.loads(Path(path).read_text(encoding='utf-8'))
    require(set(value)=={'schema_version','pilot','manifest_sha256','producer_receipt_sha256','requests'}
        and value['schema_version']=='exposedpath-pilot-tokens/0.1.0' and value['pilot']==binding
        and value['manifest_sha256']==sha(manifest_path) and value['producer_receipt_sha256']==sha(producer_path), 'TOKEN_LINEAGE')
    measured=[r for r in ledger['requests'] if r['request_role']=='measured']
    require(len(measured)==len(value['requests'])==1,'TOKEN_REQUESTS')
    row=value['requests'][0]
    require(set(row)=={'identity','token_ids'} and row['identity']==measured[0]['identity'],'TOKEN_IDENTITY')
    ids=row['token_ids']
    require(isinstance(ids,list) and len(ids)==2 and all(isinstance(x,list) and len(x)==1
        and type(x[0]) is int and x[0]>=0 for x in ids),'TOKEN_VALUES')
    return ids


def execution_extension(manifest, ledger, execution, execution_path, manifest_path, producer_path, *, token_path=None):
    """Validate new fields before reusing unchanged execution/measurement checks."""
    roles(manifest)
    from . import coe_pilot
    if coe_pilot.active(manifest.get('pilot')):
        return coe_pilot.execution_extension(manifest,ledger,execution,execution_path,manifest_path,producer_path,token_path)
    if 'formal' in manifest:
        from .formal_protocol import execution_extension as formal_extension
        return formal_extension(manifest,ledger,execution,execution_path,manifest_path,producer_path,token_path)
    if 'pilot' not in manifest:
        return set(), 'exposedpath-engineering-execution/0.1.0'
    require(token_path is not None and Path(token_path).resolve()==(Path(execution_path).parent/'pilot_tokens.json').resolve(),
        'TOKEN_RECEIPT_SOURCE')
    validate_tokens(Path(execution_path).parent/'pilot_tokens.json',manifest,ledger,execution,manifest_path,producer_path)
    return {'pilot','run_role','data_role','pilot_tokens_sha256'}, versions(manifest['pilot'])[1]


def versions(binding):
    validate_binding(binding)
    from . import coe_pilot
    if coe_pilot.active(binding): return coe_pilot.PASS_VERSION,coe_pilot.EXECUTION_VERSION
    from . import gate11_warmup as warmup
    return (warmup.PASS_VERSION,warmup.EXECUTION_VERSION) if warmup.active(binding) else (PASS_VERSION,EXECUTION_VERSION)


def validate_actual_requests(manifest, ledger):
    """Validate observed warmup nulls separately from measured completion facts."""
    from . import coe_pilot
    if coe_pilot.active(manifest.get('pilot')):return coe_pilot.validate_actual_requests(manifest,ledger)
    from .gate11_warmup import active, request_plan
    binding=validate(manifest)
    require(active(binding) and ledger.get('pilot')==binding,'OBSERVED_WARMUP_BINDING')
    from .gate8_identity import validate_pass_identity
    validate_pass_identity(ledger)
    require(len(ledger['requests'])==len(request_plan(binding)) and all(
        r['outcome']=='COMPLETE' and not r['reasons'] and r['expected_output_tokens']==2
        and ((r['actual_output_tokens'] is None and r['early_eos'] is None)
             if r['request_role']=='warmup' else
             (r['actual_output_tokens']==2 and r['early_eos'] is False))
        for r in ledger['requests']),'ACTUAL_WARMUP_OR_MEASURED_COMPLETION')
