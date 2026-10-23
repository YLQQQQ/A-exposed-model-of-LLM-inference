"""Thin batch file binding around the unchanged, same-source A/COE preview.

No new S, interval formula, per-sample timing, collector or GPU interface.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path, PurePosixPath

VERSION='cupti-batch-budget-index/0.1.0'
STATUS='COMPLETE_WINDOW_SOURCE_PREVIEW_NOT_FORMAL'
FILES={'original_a':'original_a.json','coe':'coe.json',
    'extended_completion_exposure':'extended_completion_exposure.json'}


def require(ok,reason):
    if not ok:raise ValueError('CUPTI_BATCH_ACCOUNTING_'+reason)


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read(p):return json.loads(Path(p).read_text(encoding='utf8'))


def write(p,v):
    with Path(p).open('x',encoding='utf8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2)


def validate_token_copy(raw,scope,batch):
    """Vector argmax is int64; prove this operation transfers B actual IDs.

    This size check is additional binding, not effect/dependency admission.
    The existing S consumer still verifies real D2H payload and completion.
    """
    require(type(batch) is int and batch in (1,2,4) and len(scope['actual_token_ids'])==batch,'TOKEN_SHAPE')
    api=[r for r in raw['records'] if r['id']==scope['copy_api']]
    require(len(api)==1 and api[0]['kind']=='API' and api[0]['domain']=='RUNTIME','COPY_API')
    a=api[0];calls=[c for c in raw['callbacks'] if all(c[k]==a[k] for k in ('domain','pid','correlation'))]
    require(len(calls)==1 and calls[0]['name']=='cudaMemcpyAsync' and calls[0]['cbid']==41 and
        calls[0]['return_code']==0 and calls[0]['tid']==scope['tid'] and
        isinstance(calls[0].get('params'),dict) and type(calls[0]['params'].get('count')) is int and
        calls[0]['params']['count']==batch*8 and calls[0]['params'].get('copy_kind')==2,'TOKEN_COPY_SIZE')


def write_accounting(folder,raw,scopes,answers,cfg):
    from analysis.cupti_a_migration import audit_run,VERSION as ADAPTER
    folder=Path(folder);tokens=read(folder/'tokens.json');mc=read(cfg['model_config'])
    template=cfg['model_contract']
    execution_fields={'model','inventory','inventory_sha256','prompt','prompt_sha256','gpu_uuid','gpu_pci',
        'target_python','site_root','session'}
    require(cfg['schema_version']=='cupti-timeline-stage-b/0.5.0' and
        all(mc.get(k)==v for k,v in template.items()) and set(mc)-set(template)<=execution_fields and
        mc['prompt_sha256']==cfg['prompt_sha256'] and
        len(scopes)==len(answers)==2 and tokens['status']=='COMPLETE','CONFIG_OR_COMPLETENESS')
    capture_hash=sha(folder/'timeline/capture.json');sources={};persisted=[]
    for i,(scope,answer) in enumerate(zip(scopes,answers)):
        sn=f'scope_token{i}.json';rn=f'derived_token{i}/result.json'
        saved=read(folder/rn)
        # The persisted contract is JSON: tuple interval pairs from the live
        # S return become JSON arrays. Compare the exact serialized structure,
        # not Python container types, and consume the actual saved proof.
        require(read(folder/sn)==scope and saved==json.loads(json.dumps(answer)) and
            answer['input']['capture_sha256']==capture_hash and answer['input']['scope_sha256']==sha(folder/sn),
            'SAVED_SOURCE_BINDING')
        persisted.append(saved)
        for name in (sn,rn):sources[name]=sha(folder/name)
        require(scope['actual_token_ids']==tokens['token_ids'][i],'TOKEN_SCOPE')
    for name in ('timeline/capture.json','tokens.json','setup.json','producer/pass_identity.json'):
        sources[name]=sha(folder/name)
    binding=dict(schema_version=VERSION,run_id=cfg['run_id'],session_id=raw['session_id'],
        clock=raw['clock'],batch_size=mc['batch_size'],output_shape=[2,mc['batch_size']],
        input_identity=deepcopy(mc['input_identity']),input_slot=deepcopy(cfg['input_slot']),
        role=cfg['plan']['role'],completion_unit='WHOLE_BATCH_INVOCATION',capture_sha256=capture_hash,
        model_config_sha256=sha(cfg['model_config']),source_files=sources,analysis_commit=cfg['analysis_commit'],
        adapter_version=ADAPTER,production_A_B_changed=False,formal_eligible=False,full_physical_W_qualified=False)
    audit=audit_run(raw,scopes,[a['result'] for a in persisted])
    target=folder/'batch_accounting';require(not target.exists(),'NO_OVERWRITE');target.mkdir()
    if audit['windows'] is None:
        write(target/'index.json',dict(binding,status='BLOCKED_WHOLE_WINDOW_SOURCE_GAP',gaps=audit['gaps'],files={}))
        require(False,'SOURCE_GAP:'+json.dumps(audit['gaps'],separators=(',',':')))
    original=[];coe=[];extended=[]
    for w in audit['windows']:
        common={k:w[k] for k in ('name','window_ns','wall_ns')}
        original.append(dict(common,budgets_ns=w['original_budgets_ns'],cuda_api_ns=w['cuda_api_original_ns'],
            original_atom_count=w['original_atom_count'],original_atom_sha256=w['original_atom_sha256']))
        coe.append(dict(common,coe_union_ns=w['coe_union_ns'],intervals=w['coe_union']))
        extended.append(dict(common,budgets_ns=w['extended_budgets_ns'],cuda_api_ns=w['cuda_api_extended_ns'],
            **{k:w[k] for k in ('coe_union_ns','old_wait_overlap_ns','new_migration_ns','migration_source_ns','migration')}))
    views=dict(original_a=dict(windows=original,meaning='ORIGINAL_FORMULA_SAME_CUPTI_CANDIDATE_PARTITION'),
        coe=dict(windows=coe,operation_metrics=[dict(a['result'],saved_result_reference=f'derived_token{i}/result.json')
            for i,a in enumerate(answers)],meaning='NECESSARY_ACTIVITY_DURING_COMPLETION_NOT_PURE_HOST_BLOCKING'),
        extended_completion_exposure=dict(windows=extended,meaning='UNION_OLD_WAIT_AND_COE_NOT_PRODUCTION_DEVICE_WAIT'))
    refs={}
    for key,name in FILES.items():
        path=target/name;write(path,dict(binding,view=key,**views[key]))
        refs[key]=dict(filename=name,sha256=sha(path),bytes=path.stat().st_size)
    index=dict(binding,status=STATUS,files=refs,gaps=[],request_equals_phase_sum=audit['request_equals_phase_sum'],
        sync_projections=audit['sync_projections'],membership_assurance=audit['membership_assurance'])
    write(target/'index.json',index)
    return dict(index_file='batch_accounting/index.json',index_sha256=sha(target/'index.json'),
        status=STATUS,batch_size=mc['batch_size'],output_shape=[2,mc['batch_size']])


def read_summary(folder,report,cfg):
    folder=Path(folder);ref=report['batch_accounting']
    require(isinstance(ref,dict) and ref['index_file']=='batch_accounting/index.json' and
        sha(folder/ref['index_file'])==ref['index_sha256'],'INDEX_HASH')
    index=read(folder/ref['index_file'])
    require(index['schema_version']==VERSION and index['status']==ref['status']==STATUS and index['gaps']==[] and
        index['capture_sha256']==report['capture_sha256'] and index['batch_size']==report['batch_size'] and
        index['output_shape']==report['output_shape'] and set(index['files'])==set(FILES) and
        index['run_id']==cfg['run_id'] and index['input_slot']==cfg['input_slot'] and
        index['batch_size']==cfg['model_contract']['batch_size'] and
        index['input_identity']==cfg['input_identity'] and index['analysis_commit']==cfg['analysis_commit'] and
        index['model_config_sha256']==sha(cfg['model_config']) and
        index['completion_unit']=='WHOLE_BATCH_INVOCATION','INDEX_IDENTITY')
    expected={'timeline/capture.json','tokens.json','setup.json','producer/pass_identity.json',
        'scope_token0.json','scope_token1.json','derived_token0/result.json','derived_token1/result.json'}
    require(set(index['source_files'])==expected,'SOURCE_COVERAGE')
    for name,expected in index['source_files'].items():
        require(not PurePosixPath(name).is_absolute() and '\\' not in name and ':' not in name and
            '..' not in PurePosixPath(name).parts and
            sha(folder/name)==expected,'SOURCE_HASH:'+name)
    values={}
    for key,name in FILES.items():
        r=index['files'][key];p=folder/'batch_accounting'/name
        require(r['filename']==name and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],'VIEW_HASH:'+key)
        v=read(p)
        require(v['run_id']==index['run_id'] and v['capture_sha256']==index['capture_sha256'] and
            v['input_identity']==index['input_identity'] and v['view']==key,'VIEW_IDENTITY')
        values[key]=v['windows']
    return dict(schema_version=VERSION,status=STATUS,run_id=index['run_id'],input_slot=index['input_slot'],
        capture_sha256=index['capture_sha256'],batch_size=index['batch_size'],output_shape=index['output_shape'],
        completion_unit=index['completion_unit'],input_identity=index['input_identity'],
        index_sha256=ref['index_sha256'],views=values)
