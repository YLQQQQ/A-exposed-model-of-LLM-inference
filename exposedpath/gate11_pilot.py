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
    candidates=schedule(value.get('batch_id'))
    require(any(value==r and all(type(value[k]) is type(v) for k,v in r.items()) for r in candidates),'BINDING')
    return value


def minimal_fields(binding):
    validate_binding(binding)
    from exposedpath_v141.gate9_domain import declaration as domain, N1, G1
    from .n1_model import declaration, execution_declaration, CALLSITE
    length,variant=CONDITIONS[binding['condition']]
    result=dict(pilot=deepcopy(binding),run_role='PILOT',data_role='Pilot',run_id=binding['run_id'],
        fixed_input_tokens=length,fixed_output_tokens=2,batch_size=1,warmup_count=1,repeat_count=1,
        execution_mode='eager',attention_backend='sdpa',dtype_and_quantization='fp16',
        sampling_config={'do_sample':False},domain_qualification=domain(N1 if variant else G1),
        study_mode='N1_INTERVENTION' if variant else 'G1_NATURAL',n1_intervention=None)
    if variant:
        result.update(n1_model=declaration(variant),n1_model_execution=execution_declaration(),
            n1_intervention=dict(sync_origin='n1_intervention',callsite_id=CALLSITE,intervention_variant_id=variant))
    return result


def validate(manifest):
    binding=validate_binding(manifest.get('pilot'))
    expected=minimal_fields(binding)
    require(all(type(manifest.get(k)) is type(v) and manifest[k]==v for k,v in expected.items()),'DECLARATION_CONFLICT')
    require('engineering_pair' not in manifest,'LEGACY_PAIR_CONFLICT')
    if binding['variant'] is None:
        require('n1_model' not in manifest and 'n1_model_execution' not in manifest,'WRONG_DOMAIN')
    return binding


def roles(manifest):
    """No role inference from a friendly label; Pilot requires the whole declaration."""
    if 'pilot' in manifest or manifest.get('run_role')=='PILOT' or manifest.get('data_role')=='Pilot':
        validate(manifest)
        return dict(run_role='PILOT',data_role='Pilot')
    require(manifest.get('run_role')=='ENGINEERING' and manifest.get('data_role')=='Engineering','ROLE')
    return dict(run_role='ENGINEERING',data_role='Engineering')


def validate_prepared(manifest, prepared, root):
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
    import json
    binding=validate(manifest)
    require(ledger.get('pilot')==binding and ledger['schema_version']==PASS_VERSION
        and ledger['run_role']=='PILOT' and ledger['data_role']=='Pilot','PRODUCER_ROLE')
    require(execution.get('schema_version')==EXECUTION_VERSION and execution.get('pilot')==binding
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
    if 'pilot' not in manifest:
        return set(), 'exposedpath-engineering-execution/0.1.0'
    require(token_path is not None and Path(token_path).resolve()==(Path(execution_path).parent/'pilot_tokens.json').resolve(),
        'TOKEN_RECEIPT_SOURCE')
    validate_tokens(Path(execution_path).parent/'pilot_tokens.json',manifest,ledger,execution,manifest_path,producer_path)
    return {'pilot','run_role','data_role','pilot_tokens_sha256'}, EXECUTION_VERSION
