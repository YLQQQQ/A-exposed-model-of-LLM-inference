"""Prospective limited Formal envelope. Never signs a protocol or runs a model.

Approval is an externally supplied human receipt, NOT a cryptographic attestation.
The archive must retain the user's approval of the exact candidate content hash.
"""
from copy import deepcopy
from datetime import datetime
import hashlib
import json
import re
from pathlib import Path

VERSION = 'G12-FORMAL-ENVELOPE/0.1'
PASS_VERSION = 'exposedpath-formal-pass-identity/0.1.0'
EXECUTION_VERSION = 'exposedpath-formal-execution/0.1.0'
PRODUCER_VERSION = 'exposedpath-formal-producer-receipt/0.1.0'
TOKEN_VERSION = 'exposedpath-formal-tokens/0.1.0'
ORDERS = (('G32','N0','Nm','N16','G512'),('G512','Nm','N16','N0','G32'),
          ('G32','N16','N0','Nm','G512'),('G512','N16','Nm','N0','G32'),
          ('G32','N0','N16','Nm','G512'),('G512','Nm','N0','N16','G32'))
REQUIRED_ARTIFACTS={'exposedpath/formal_protocol.py','exposedpath/runner.py',
    'exposedpath/gate8_identity.py','exposedpath/gate8_diagnostic.py',
    'exposedpath_v141/gate9_domain.py','exposedpath_v141/activity_baseline.py',
    'exposedpath_v141/paired_statistics.py','docs/v1_4_1/contracts/a_api_registry_v0_1.json',
    'docs/v1_4_1/contracts/a_api_registry_v0_2.json',
    'docs/v1_4_1/contracts/formal_envelope_schema_v0_1.json'}


def require(ok, reason):
    if not ok: raise ValueError('FORMAL_' + reason)


def content_bytes(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True)+'\n').encode('utf-8')


def content_hash(value):
    return hashlib.sha256(content_bytes(value)).hexdigest()


def _date(text):
    require(isinstance(text,str) and text.endswith('Z'),'UTC_TIME')
    return datetime.fromisoformat(text.replace('Z','+00:00'))


def validate_release(protocol, approval):
    keys={'version','status','execution_commit','analysis_commit','artifact_hashes',
          'warmup_count','blocks','input_hashes','supported_domains','claims',
          'p0_composition_transfer','d_signature','execution_constraints'}
    require(isinstance(protocol,dict) and set(protocol)==keys,'PROTOCOL_SCHEMA')
    require(protocol['version']=='G12-ROUTEA/0.1' and protocol['status']=='FREEZE_CANDIDATE','PROTOCOL_VERSION')
    require(all(isinstance(protocol[k],str) and re.fullmatch('[0-9a-f]{40}',protocol[k])
                for k in ('execution_commit','analysis_commit')),'CODE_COMMIT')
    require(type(protocol['blocks']) is int and protocol['blocks']==6
        and type(protocol['warmup_count']) is int and protocol['warmup_count']==3,'POLICY')
    require(protocol['supported_domains']==['G1_NATURAL_PROJECTED_A/0.1.0','N1_EXPLICIT_STREAM_AB/0.1.0']
        and protocol['claims']==['P0_PERFORMANCE','P1_ACCOUNTING_AND_SINGLE_SYNC_B']
        and protocol['p0_composition_transfer'] is False and protocol['d_signature'] is False,'CLAIM_SCOPE')
    for name in ('artifact_hashes','input_hashes'):
        value=protocol[name]
        require(isinstance(value,dict) and value and all(isinstance(k,str) and k
            and isinstance(v,str) and re.fullmatch('[0-9a-f]{64}',v) for k,v in value.items()),'CONTENT_HASHES')
    require(set(protocol['input_hashes'])=={'G32','G512'},'INPUT_SET')
    require(REQUIRED_ARTIFACTS<=protocol['artifact_hashes'].keys(),'SOURCE_LOCK_INCOMPLETE')
    c=protocol['execution_constraints']
    require(isinstance(c,dict) and set(c)=={'model_inventory_sha256','gpu','software','collector_version'}
        and isinstance(c['model_inventory_sha256'],str) and re.fullmatch('[0-9a-f]{64}',c['model_inventory_sha256']),'EXECUTION_CONSTRAINTS')
    require(set(c['gpu'])=={'physical_index','logical_index','uuid','pci'}
        and type(c['gpu']['physical_index']) is int and c['gpu']['physical_index']>=0
        and type(c['gpu']['logical_index']) is int and c['gpu']['logical_index']==0,'GPU_CONSTRAINT')
    from exposedpath_v141.gate8_adapter import normalized_uuid,normalized_pci
    normalized_uuid(c['gpu']['uuid']);normalized_pci(c['gpu']['pci'])
    require(set(c['software'])=={'nvidia_driver_version','cuda_version_used','inference_framework_version','runtime_version'}
        and all(isinstance(v,str) and v for v in c['software'].values())
        and c['collector_version']=='2026.2.1.210','SOFTWARE_CONSTRAINT')
    require(isinstance(approval,dict) and set(approval)=={'version','status','protocol_sha256',
        'authority','signed_at','approval_id','scope','budget_approved'},'APPROVAL_SCHEMA')
    require(approval['version']=='exposedpath-protocol-approval/0.1.0','APPROVAL_VERSION')
    require(approval['status']=='SIGNED' and approval['budget_approved'] is True,'UNSIGNED_OR_UNAPPROVED_BUDGET')
    require(approval['protocol_sha256']==content_hash(protocol),'PROTOCOL_HASH')
    require(approval['authority']=='HUMAN_USER' and approval['scope']=='LIMITED_ROUTE_A'
        and isinstance(approval['approval_id'],str) and bool(approval['approval_id']),'APPROVAL_AUTHORITY')
    _date(approval['signed_at'])


def make_binding(protocol,approval,*,batch_id,block,condition,pass_id,declared_at):
    validate_release(protocol,approval)
    from .gate11_pilot import CONDITIONS
    require(isinstance(batch_id,str) and re.fullmatch('[A-Za-z0-9_-]{1,100}',batch_id),'BATCH_ID')
    require(type(block) is int and 1<=block<=6 and condition in CONDITIONS
        and pass_id in ('pass0','pass1'),'SLOT')
    require(_date(declared_at)>_date(approval['signed_at']),'NOT_PROSPECTIVE')
    position=ORDERS[block-1].index(condition)+1
    pair=f'{batch_id}-b{block}-{condition}'
    passes=['pass0','pass1'] if (block+position)%2==0 else ['pass1','pass0']
    return dict(version=VERSION,protocol=deepcopy(protocol),approval=deepcopy(approval),
        batch_id=batch_id,block=block,condition=condition,variant=CONDITIONS[condition][1],
        position=position,pair_id=pair,run_id=pair+'-'+pass_id,pass_id=pass_id,
        pass_order=passes,warmup_count=3,declared_at=declared_at,
        purpose='PROSPECTIVE_LIMITED_FORMAL',declaration_role='PRE_EXECUTION')


def active(value):
    return isinstance(value,dict) and value.get('version')==VERSION


def control(value):
    """Select a role's execution plan, never infer role from a filename."""
    return value.get('formal',value.get('pilot'))


def validate_binding(value):
    require(active(value),'BINDING_VERSION')
    expected=make_binding(value['protocol'],value['approval'],**{k:value[k] for k in
        ('batch_id','block','condition','pass_id','declared_at')})
    require(value==expected and all(type(value[k]) is type(v) for k,v in expected.items()),'BINDING_CONFLICT')
    return value


def reference(value):
    validate_binding(value)
    return dict(protocol_version=value['protocol']['version'],
        protocol_sha256=content_hash(value['protocol']),approval_sha256=content_hash(value['approval']))


def minimal_fields(value):
    validate_binding(value)
    # Reuse the qualified common execution policy, not the old Pilot role.
    from .gate11_pilot import minimal_fields as pilot_fields
    from .gate11_warmup_pair import schedule
    seed=next(r for r in schedule('formal-policy-template') if r['condition']==value['condition']
              and r['block']==1 and r['pass_id']==value['pass_id'])
    result=pilot_fields(seed)
    result.pop('pilot')
    result.update(formal=deepcopy(value),run_role='FORMAL',data_role='Formal',run_id=value['run_id'])
    return result


def validate(manifest):
    require('pilot' not in manifest and 'engineering_pair' not in manifest,'LEGACY_ROLE_UPGRADE')
    value=validate_binding(manifest.get('formal'))
    require(all(type(manifest.get(k)) is type(v) and manifest[k]==v
                for k,v in minimal_fields(value).items()),'MANIFEST_CONFLICT')
    require(manifest.get('runner_git_commit')==value['protocol']['execution_commit']
        and manifest.get('runner_git_dirty') is False,'EXECUTION_IDENTITY')
    key='G512' if value['condition']=='G512' else 'G32'
    require(manifest.get('prompt_tokens_sha256')==value['protocol']['input_hashes'][key],'INPUT_HASH')
    if value['variant'] is None:
        require('n1_model' not in manifest and 'n1_model_execution' not in manifest,'WRONG_DOMAIN')
    c=value['protocol']['execution_constraints']
    from exposedpath_v141.gate8_adapter import normalized_uuid,normalized_pci
    require(type(manifest.get('gpu_index_physical')) is int and type(manifest.get('gpu_index_logical')) is int
        and manifest.get('gpu_index_physical')==c['gpu']['physical_index']
        and manifest.get('gpu_index_logical')==c['gpu']['logical_index']
        and normalized_uuid(manifest.get('gpu_uuid'))==normalized_uuid(c['gpu']['uuid'])
        and normalized_pci(manifest.get('gpu_pci_bus_id'))==normalized_pci(c['gpu']['pci']),'FROZEN_GPU')
    require(manifest.get('model_content_snapshot',{}).get('inventory_sha256')==c['model_inventory_sha256'],'FROZEN_MODEL')
    require(all(manifest.get(k)==v for k,v in c['software'].items()),'FROZEN_SOFTWARE')
    return value


def validate_artifacts(root,protocol):
    """Explicit Git-content LF / CRLF representation proof; retain actual bytes.

    Never updates the expected digest. This is source-content compatibility,
    separate from the strict actual byte seal already used at launch.
    """
    root=Path(root).resolve(); observed={}
    require(isinstance(protocol.get('artifact_hashes'),dict) and protocol['artifact_hashes'],'ARTIFACT_SET')
    for name,expected in protocol['artifact_hashes'].items():
        relative=Path(name);target=(root/relative).resolve()
        require(not relative.is_absolute() and '..' not in relative.parts and target.is_relative_to(root),'ARTIFACT_PATH')
        require(target.is_file(),'ARTIFACT_MISSING')
        data=target.read_bytes();actual=hashlib.sha256(data).hexdigest()
        representation='EXACT'
        if actual!=expected:
            require(b'\r\n' in data and hashlib.sha256(data.replace(b'\r\n',b'\n')).hexdigest()==expected,'ARTIFACT_CONTENT')
            representation='CRLF_GIT_CONTENT_EQUIVALENT'
        observed[name]=dict(actual_sha256=actual,size_bytes=len(data),git_content_sha256=expected,
                            representation=representation)
    return observed


def validate_prepared(manifest,prepared,root):
    from .gate8_engineering_contract import validate_declaration
    from .workload import load_prompt_tokens
    from .gate11_pilot import sha
    b=validate(manifest);validate_declaration(manifest)
    require('target_python' in manifest and 'isolated_preflight_version' in manifest,'VERIFIED_ENTRY')
    require(sha(Path(prepared)/'prompt.json')==manifest['prompt_tokens_sha256']
        and sha(Path(root)/'exposedpath/runner.py')==manifest['runner_source_sha256'],'PREPARED_CONTENT')
    require(load_prompt_tokens(Path(prepared)/'prompt.json')['fixed_input_tokens']==manifest['fixed_input_tokens'],'INPUT_LENGTH')
    validate_artifacts(root,b['protocol'])
    if b['variant'] is not None:
        from .n1_model import validate_prepared as n1
        n1(manifest,prepared,root)


def validate_analysis(manifest):
    from . import platform_adapter
    b=validate(manifest);root=Path(__file__).resolve().parents[1]
    require(platform_adapter.git(['-C',str(root),'rev-parse','HEAD'])==b['protocol']['analysis_commit']
        and not platform_adapter.git(['-C',str(root),'status','--porcelain']),'ANALYSIS_IDENTITY')
    return validate_artifacts(root,b['protocol'])


def validate_actual_requests(manifest,ledger):
    value=validate(manifest)
    from .gate8_identity import validate_pass_identity
    from .gate11_warmup import request_plan
    validate_pass_identity(ledger)
    require(ledger.get('formal')==value and len(ledger['requests'])==4,'PRODUCER_BINDING')
    require([dict(request_id=r['identity']['request_id'],repeat_id=r['identity']['repeat_id'],
        request_role=r['request_role']) for r in ledger['requests']]==request_plan(value),'ACTUAL_ORDER')
    require(all(r['outcome']=='COMPLETE' and not r['reasons'] and r['expected_output_tokens']==2
        and ((r['actual_output_tokens'] is None and r['early_eos'] is None) if r['request_role']=='warmup'
             else (r['actual_output_tokens']==2 and r['early_eos'] is False)) for r in ledger['requests']), 'ACTUAL_REQUESTS')


def execution_extension(manifest,ledger,execution,execution_path,manifest_path,producer_path,token_path):
    from pathlib import Path
    from .gate11_pilot import sha
    b=validate(manifest); validate_actual_requests(manifest,ledger)
    require(token_path is not None and Path(token_path).resolve()==Path(execution_path).parent/'formal_tokens.json','TOKEN_SOURCE')
    token=json.loads(Path(token_path).read_text(encoding='utf-8'))
    require(set(token)=={'schema_version','formal','manifest_sha256','producer_receipt_sha256','requests'}
        and token['schema_version']==TOKEN_VERSION and token['formal']==b
        and token['manifest_sha256']==sha(manifest_path) and token['producer_receipt_sha256']==sha(producer_path),'TOKEN_LINEAGE')
    measured=next(r for r in ledger['requests'] if r['request_role']=='measured')
    require(len(token['requests'])==1 and token['requests'][0]['identity']==measured['identity'],'TOKEN_IDENTITY')
    ids=token['requests'][0]['token_ids']
    require(isinstance(ids,list) and len(ids)==2 and all(isinstance(x,list) and len(x)==1
        and type(x[0]) is int and x[0]>=0 for x in ids),'TOKEN_VALUES')
    require(execution.get('formal')==b and execution.get('run_role')=='FORMAL'
        and execution.get('data_role')=='Formal' and execution.get('formal_tokens_sha256')==sha(token_path),'EXECUTION_ROLE')
    return {'formal','run_role','data_role','formal_tokens_sha256'},EXECUTION_VERSION
