"""Legacy finite versions and configured input plans. Imported without CUDA.

Resident setup and three original warmups precede subscription. The unchanged
runner supplies the measured drain and two Host-readable token operations.
This provider is not a timing-equivalent replacement for Nsight.
"""
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import threading

NATIVE_COMMIT='7fa36efb340fe59a3138eb6132e162d6b0cbfc41'
POLICY_NATIVE_COMMIT='6c744bf52daff3fc54571e264a0c34e3207aa1df'


def require(ok,reason):
    if not ok:raise ValueError('CUPTI_MODEL_'+reason)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def read(path):return json.loads(Path(path).read_text(encoding='utf8'))


def write(path,value):
    with Path(path).open('x',encoding='utf8') as f:json.dump(value,f,indent=2,sort_keys=True)


def input_contract():
    source=Path(__file__).with_name('cupti_input_contract.py')
    spec=importlib.util.spec_from_file_location('_cupti_input_contract',source)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def validate_contract(c):
    version=c.get('schema_version')
    if version in ('cupti-timeline-model/0.3.0','cupti-timeline-model/0.4.0','cupti-timeline-model/0.5.0'):return input_contract().validate_model(c)
    require(version in ('cupti-timeline-model/0.1.0','cupti-timeline-model/0.1.1','cupti-timeline-model/0.2.0'),'CONTRACT_VERSION')
    current=version!='cupti-timeline-model/0.1.0';finite=version=='cupti-timeline-model/0.2.0'
    expected=dict(schema_version=version,input_tokens=1024 if finite else 768,batch_size=1,
        output_tokens=2,warmup_count=3,repeat_count=1,role='Engineering',completion_policy='HOST_READABLE_P',
        model_process_budget=1,nsight_profiles=0,torch_profiler=False,
        native_commit=POLICY_NATIVE_COMMIT if current else NATIVE_COMMIT)
    require(all(type(c.get(k)) is type(v) and c[k]==v for k,v in expected.items()),'CONTRACT')
    import re
    require(isinstance(c.get('run_id'),str) and re.fullmatch('[A-Za-z0-9_-]{1,60}',c['run_id']),'RUN_ID')
    if current:
        require(c.get('activity_policy_version')=='cupti-api22-activity-policy/0.2.0'
            and c.get('session',{}).get('activity_policy_version')==c['activity_policy_version']
            and re.fullmatch('[0-9a-f]{40}',c.get('control_commit','')),'CONTRACT_POLICY')
    else:require('activity_policy_version' not in c and 'control_commit' not in c,'CONTRACT_LEGACY')
    if finite:
        require(all(c.get(k)==v for k,v in dict(consumer_version='submit-effect-bridge/0.3.0',
            timing_policy='cupti-api22-distinct-api-callback-boundaries/0.2.0',
            driver_query_policy='cupti-api22-driver-queries/0.1.0',
            runtime_query_policy='cupti-api22-runtime-queries/0.1.0').items()),'CONTRACT_CONSUMER_POLICY')
    return expected['native_commit']


def preparer(config):
    """Versioned Engineering constructor; measured P methods are inherited exactly."""
    validate_contract(config)
    from exposedpath.observation_preparation import Execution
    class EngineeringPreparation(Execution):
        def __init__(self):
            self.axis=config['role']=='Pilot'
            self.binding=dict(version='CUPTI-TIMELINE-MODEL/BATCH-0.3' if config['schema_version']=='cupti-timeline-model/0.5.0' else 'CUPTI-TIMELINE-MODEL/PLAN-0.2' if config['schema_version']=='cupti-timeline-model/0.4.0' else 'CUPTI-TIMELINE-MODEL/PILOT-0.1' if self.axis else 'CUPTI-TIMELINE-MODEL/0.3' if config['schema_version']=='cupti-timeline-model/0.2.0' else 'CUPTI-TIMELINE-MODEL/0.2' if config['schema_version']=='cupti-timeline-model/0.1.1'
                else 'CUPTI-TIMELINE-MODEL/0.1',run_id=config['run_id'],
                role=config['role'],input_tokens=config['input_tokens'],output_tokens=2)
            if config['schema_version']=='cupti-timeline-model/0.5.0':
                self.binding.update(batch_size=config['batch_size'],input_identity=deepcopy(config['input_identity']))
            self.variant='P';self.closed=True;self.used=[]
    return EngineeringPreparation()


def resident_capture(runner,session,resident,fields,out,preparation,observer):
    for _ in range(3):runner.run_warmup(resident['model'],resident['input_ids'],resident['attention_mask'],2,1)
    write(Path(out)/'warmup_completed.json',dict(schema_version='cupti-model-warmups/0.1.0',
        completed_count=3,output_tokens=2,implementation='ORIGINAL_RUNNER_RUN_WARMUP',
        subscription_active=False))
    with session:
        with session.nvtx_sink(runner.torch.cuda.nvtx):
            return runner.run_gate8_requests_to_files(output_dir=Path(out)/'producer',**resident,
                output_len=2,device='cuda:0',pass_fields=fields,
                request_plan=[dict(request_id='request-0',repeat_id='0',request_role='measured')],
                record_drains=True,record_stages=True,observation_preparation=preparation,
                invocation_observer=observer)


def record_batch_tokens(config,out,preparation,identity,result,input_identity):
    """Persist already Host-readable vectors outside the window, including EOS.

    A rejected observation is data, not a successful producer. Return its status
    so the outer entry can stop after the existing stage ledger is persisted;
    do not raise from an out-of-stage observer and mislabel model execution.
    """
    ids=[list(b.host_token_ids) for b in result['token_ready_boundaries']]
    batch=config['batch_size'];shape_ok=all(len(v)==batch for v in ids)
    eos=set(config['model_limits']['eos_token_ids'])
    hits=[dict(token_index=i,sample_index=j,token_id=t) for i,v in enumerate(ids) for j,t in enumerate(v) if t in eos]
    value=dict(schema_version='cupti-batch-token-observation/0.1.0',status='REJECTED_ACTUAL_OUTPUT',
        identity=deepcopy(identity),pid=os.getpid(),tid=threading.get_native_id(),token_ids=ids,
        batch_size=result['batch_size'],sample_indices=list(range(batch)),output_shape=[len(ids),batch] if shape_ok else None,
        actual_input_tokens=result['actual_input_tokens'],actual_output_tokens=result['actual_output_tokens'],
        actual_output_tokens_per_sample=[len(ids)]*batch if shape_ok else None,early_eos=result['early_eos'],eos_hits=hits,
        prepared_labels=[v.label for v in preparation.prepared],input_identity=deepcopy(input_identity),
        input_slot=deepcopy(config['input_slot']),completion_unit='WHOLE_BATCH_INVOCATION',
        preparation=None,rejection_reason=None)
    if config['role']=='Pilot':value['pilot']=deepcopy(config['pilot'])
    try:
        require(result['batch_size']==batch and result['actual_input_tokens']==config['input_tokens'] and
            result['actual_output_tokens']==len(ids)==2 and result['early_eos'] is False and not hits,'BATCH_OUTPUT_COUNT_OR_EOS')
        input_contract().validate_tokens(ids,config['output_validation'],config['model_limits'])
        value['preparation']=preparation.finish(identity);value['status']='COMPLETE'
    except ValueError as exc:value['rejection_reason']=str(exc)
    write(Path(out)/'tokens.json',value)
    return value


def producer_scopes(session_id,host,drains,tokens,*,input_tokens=768,contract=None):
    if contract is not None:
        validate_contract(contract)
        planned=contract['schema_version'] in ('cupti-timeline-model/0.4.0','cupti-timeline-model/0.5.0')
        require(input_tokens==contract['input_tokens'] and
            (tokens.get('input_slot')==contract['input_slot'] if planned else
             contract['schema_version']=='cupti-timeline-model/0.3.0' and tokens.get('pilot')==contract['pilot']),
            'SCOPE_INPUT_VERSION')
    else:require(type(input_tokens) is int and input_tokens in (768,1024),'SCOPE_INPUT_VERSION')
    batched=contract is not None and contract['schema_version']=='cupti-timeline-model/0.5.0'
    batch=contract['batch_size'] if batched else 1
    require(tokens.get('early_eos') is False and tokens.get('actual_input_tokens')==input_tokens and
        tokens.get('actual_output_tokens')==2 and len(tokens.get('token_ids',[]))==2 and
        all(isinstance(v,list) and len(v)==batch and all(type(t) is int and t>=0 for t in v) for v in tokens['token_ids']) and
        len(tokens.get('prepared_labels',[]))==2,'TOKEN_COMPLETION')
    if batched:require(tokens.get('schema_version')=='cupti-batch-token-observation/0.1.0' and tokens.get('status')=='COMPLETE'
        and tokens.get('batch_size')==batch and tokens.get('sample_indices')==list(range(batch)) and
        tokens.get('output_shape')==[2,batch] and tokens.get('input_identity')==contract['input_identity'] and
        tokens.get('completion_unit')=='WHOLE_BATCH_INVOCATION','BATCH_TOKEN_IDENTITY')
    identity=tokens['identity'];rows=drains['drains']
    require(len(rows)==1 and rows[0]['status']=='COMPLETE' and rows[0]['identity']==identity and
        rows[0]['thread_id']==tokens['tid'],'DRAIN_IDENTITY')
    require(len(host)==3 and all(r['payload']['identity']==identity for r in host),'BOUNDARY_IDENTITY')
    payloads=[r['payload'] for r in host]
    require([(p['boundary_kind'],p['token_index']) for p in payloads]==
        [('request_start',None),('token_ready',0),('token_ready',1)],'BOUNDARY_ORDER')
    encode=lambda p:json.dumps(p,sort_keys=True,separators=(',',':'))
    d={k:rows[0][k] for k in ('schema_version','operation_id','identity','logical_device','marker_role')}
    return [dict(session_id=session_id,pid=tokens['pid'],tid=tokens['tid'],run_id=identity['run_id'],
        **(dict(schema_version='cupti-batch-token-scope-producer/0.1.0',batch_size=batch,sample_indices=list(range(batch)),
            input_identity=deepcopy(contract['input_identity']),completion_unit='WHOLE_BATCH_INVOCATION') if batched else {}),
        actual_token_ids=tokens['token_ids'][i],drain_label='EXPOSEDPATH_DRAIN_V1:'+encode(d),
        request_label='EXPOSEDPATH_BOUNDARY_V1:'+encode(payloads[0]),helper_label=tokens['prepared_labels'][i],
        token_label='EXPOSEDPATH_BOUNDARY_V1:'+encode(payloads[i+1])) for i in range(2)]


def memory_snapshot(cuda,position,device):
    """No synchronization. Called only outside resident_capture, not per-token.

    CUDA mem_get_info is an instantaneous device-wide free/total query; Torch
    peaks are allocator-only, covering resident baseline + warmups + measurement.
    They are NOT the peak occupancy of the whole GPU or a measured phase.
    """
    require(position in ('BEFORE_WARMUPS_AND_SESSION','AFTER_CAPTURE_CLOSED'),'MEMORY_POSITION')
    free,total=map(int,cuda.mem_get_info(device))
    return dict(position=position,logical_device=device,outside_measured_window=True,
        free_device_bytes=free,total_device_bytes=total,
        allocator_allocated_bytes=int(cuda.memory_allocated(device)),
        allocator_reserved_bytes=int(cuda.memory_reserved(device)),
        allocator_peak_allocated_bytes=int(cuda.max_memory_allocated(device)),
        allocator_peak_reserved_bytes=int(cuda.max_memory_reserved(device)),device_total_peak_bytes=None)


def run(config_path,out,*,enabled=False):
    require(enabled is True,'EXPLICIT_OPT_IN')
    c=read(config_path)
    batched=c.get('schema_version')=='cupti-timeline-model/0.5.0'
    planned=c.get('schema_version') in ('cupti-timeline-model/0.4.0','cupti-timeline-model/0.5.0')
    role_binding=input_contract().bind_producer(c) if c.get('schema_version')=='cupti-timeline-model/0.3.0' or planned and c.get('role')=='Pilot' else None
    native_commit=validate_contract(c);out=Path(out).resolve()
    require(not out.exists(),'NO_OVERWRITE_RESUME_RETRY');out.mkdir(parents=True,exist_ok=False)
    # The parent verifies checkout/source/library identity before this import.
    require(sys.flags.isolated and sys.flags.no_site and list(sys.version_info[:3])==[3,11,16],'TARGET_PYTHON')
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='3' and os.environ.get('CUDA_DEVICE_ORDER')=='PCI_BUS_ID','MASK')
    from exposedpath.gate8_diagnostic import verify_model_inventory
    model_fact=verify_model_inventory(c['model'],c['inventory'],c['inventory_sha256'])
    require(sha(c['prompt'])==c['prompt_sha256'],'INPUT_HASH')
    prompt=read(c['prompt']);cfg=read(Path(c['model'])/'config.json')
    from exposedpath.coe_input_pilot import validate_input,INCREMENTAL_VERSION,MIDPOINT_VERSION
    pilot=c['role']=='Pilot'
    finite=c['schema_version']=='cupti-timeline-model/0.2.0' or pilot or planned
    input_identity=(input_contract().configured_identity(prompt,c,cfg) if pilot or planned else
        validate_input(prompt,cfg,1,version=MIDPOINT_VERSION if finite else INCREMENTAL_VERSION))
    require(prompt['fixed_input_tokens']==c['input_tokens'],'INPUT_LENGTH')
    if finite:require(input_identity==c.get('input_identity'),'INPUT_IDENTITY')
    if planned:require(sha(Path(c['model'])/'config.json')==c['model_config_sha256'] and
        input_contract().model_limits(cfg)==c['model_limits'],'MODEL_CONFIG_HASH')
    import torch
    require(str(torch.__version__)=='2.6.0+cu124' and torch.version.cuda=='12.4','TORCH_VERSION')
    require(Path(sys.executable).resolve()==Path(c['target_python']).resolve() and
        Path(torch.__file__).resolve().is_relative_to(Path(c['site_root']).resolve()),'TARGET_MODULE_ORIGIN')
    from exposedpath.platform_adapter import cuda_identity_native
    from exposedpath_v141.gate8_adapter import normalized_uuid,normalized_pci
    device=cuda_identity_native(torch.cuda)
    require(torch.cuda.device_count()==1 and torch.cuda.current_device()==0 and
        normalized_uuid(device['gpu_uuid'])==normalized_uuid(c['gpu_uuid']) and
        normalized_pci(device['pci_bus_id'])==normalized_pci(c['gpu_pci']),'DEVICE_IDENTITY')
    from exposedpath import runner
    model,tokenizer,_,actual_device=runner.load_model(c['model'],3,allow_fallback=False)
    if planned:require((tokenizer.eos_token_id if isinstance(tokenizer.eos_token_id,list) else [tokenizer.eos_token_id])==c['model_limits']['eos_token_ids'],
        'TOKENIZER_EOS_BINDING')
    require(actual_device=='cuda:0' and str(model.dtype)=='torch.float16' and model.training is False and
        model.config.model_type=='qwen2' and model.config._attn_implementation=='sdpa' and
        model.config.use_cache is True,'LOADED_CONFIGURATION')
    ids,mask=input_contract().tensor_rows(prompt,input_identity) if batched else ([prompt['samples'][0]['input_ids']],[prompt['samples'][0]['attention_mask']])
    resident=dict(model=model,input_ids=torch.tensor(ids,dtype=torch.long,device='cuda:0'),
        attention_mask=torch.tensor(mask,dtype=torch.long,device='cuda:0'),eos_token_id=tokenizer.eos_token_id)
    write(out/'setup.json',dict(schema_version='cupti-model-setup/0.2.0' if batched else 'cupti-model-setup/0.1.0',model_content=model_fact,
        input_sha256=c['prompt_sha256'],input_shape=[c['batch_size'],c['input_tokens']],torch_version=str(torch.__version__),
        **(dict(batch_size=c['batch_size'],sample_indices=list(range(c['batch_size'])),output_shape_expected=[2,c['batch_size']],
            completion_unit='WHOLE_BATCH_INVOCATION') if batched else {}),
        cuda_version=torch.version.cuda,device=device,loaded_backend=model.config._attn_implementation,
        dtype=str(model.dtype),warmup_count=3,subscription_position='AFTER_SETUP_AND_WARMUPS_BEFORE_EXISTING_DRAIN',
        executable=str(Path(sys.executable).resolve()),python_version=list(sys.version_info[:3]),
        torch_origin=str(Path(torch.__file__).resolve()),runner_source_sha256=sha(runner.__file__),
        source_role='NEW_PROVIDER_ENGINEERING_NOT_NSIGHT_TIMING_EQUIVALENCE',
        **(dict(input_identity=input_identity) if finite else {}),
        **(dict(pilot=c['pilot'],producer_policy_binding=role_binding) if pilot else {}),
        **(dict(input_slot=c['input_slot'],input_plan=c['input_plan'],output_validation=c['output_validation'],
            model_limits=c['model_limits'],
            model_config_sha256=c['model_config_sha256']) if planned else {})))
    fields=dict(experiment_id='cupti-submit-effect-engineering',wmpc_id=c['run_id'],run_id=c['run_id'],
        run_role='PILOT' if pilot else 'ENGINEERING',data_role=c['role'],pass_id='pass1',attempt_id='once',pid=os.getpid(),
        wmpc_manifest_sha256=sha(config_path),prompt_sha256=c['prompt_sha256'],runner_git_commit=native_commit,
        runner_git_dirty=False,runner_source_sha256=sha(runner.__file__))
    if pilot:fields['pilot']=deepcopy(c['pilot']['producer_binding'])
    preparation=preparer(c);tokens={}
    def observed(identity,result):
        if batched:
            tokens.update(record_batch_tokens(c,out,preparation,identity,result,input_identity));return
        p=preparation.finish(identity)
        tokens.update(identity=deepcopy(identity),pid=os.getpid(),tid=threading.get_native_id(),
            token_ids=[list(b.host_token_ids) for b in result['token_ready_boundaries']],
            actual_input_tokens=result['actual_input_tokens'],actual_output_tokens=result['actual_output_tokens'],
            early_eos=result['early_eos'],prepared_labels=p['prepared_labels'],preparation=p)
        if finite:tokens['input_identity']=input_identity
        if pilot:tokens['pilot']=deepcopy(c['pilot'])
        if planned:tokens['input_slot']=deepcopy(c['input_slot'])
        write(out/'tokens.json',tokens)
    from exposedpath.cupti_timeline import CaptureSession
    session=CaptureSession(c['session'],out/'timeline',allow_target_capture=True)
    if planned:
        torch.cuda.reset_peak_memory_stats(0)
        write(out/'memory_before.json',memory_snapshot(torch.cuda,'BEFORE_WARMUPS_AND_SESSION',0))
    try:receipt=resident_capture(runner,session,resident,fields,out,preparation,observed)
    finally:
        preparation.invalidate()
        if planned:write(out/'memory_after.json',memory_snapshot(torch.cuda,'AFTER_CAPTURE_CLOSED',0))
    if batched:require(tokens.get('status')=='COMPLETE','BATCH_OUTPUT_REJECTED:'+str(tokens.get('rejection_reason')))
    require(read(receipt)['status']=='COMPLETE','PRODUCER_INCOMPLETE')
    host=read(out/'producer/host_boundaries.json');drains=read(out/'producer/drain_ledger.json')
    scopes=producer_scopes(c['session']['session_id'],host,drains,tokens,input_tokens=c['input_tokens'],
        **(dict(contract=c) if pilot or planned else {}))
    write(out/'scope_producers.json',scopes)
    result=dict(schema_version='cupti-timeline-model-result/0.1.0',
        status='MODEL_CAPTURE_COMPLETE_PENDING_ANALYSIS',pid=os.getpid(),role=c['role'],
        config_sha256=sha(config_path),capture_sha256=sha(out/'timeline/capture.json'),
        session_receipt_sha256=sha(out/'timeline/receipt.json'),producer_receipt_sha256=sha(receipt),
        token_sha256=sha(out/'tokens.json'),scope_producers_sha256=sha(out/'scope_producers.json'),
        setup_sha256=sha(out/'setup.json'),warmup_sha256=sha(out/'warmup_completed.json'),
        provider_qualification='NOT_GRANTED',A_COE_admission='NOT_ASSESSED')
    if c['schema_version']!='cupti-timeline-model/0.1.0':
        result.update(schema_version='cupti-timeline-model-result/0.5.0' if batched else 'cupti-timeline-model-result/0.4.0' if planned else 'cupti-timeline-model-result/0.3.0' if pilot else 'cupti-timeline-model-result/0.2.0' if finite else 'cupti-timeline-model-result/0.1.1',native_commit=native_commit,
            control_commit=c['control_commit'],activity_policy_version=c['activity_policy_version'],
            model_entry_sha256=sha(__file__))
    if pilot:result['pilot']=deepcopy(c['pilot'])
    if planned:result.update(input_slot=c['input_slot'],memory_before_sha256=sha(out/'memory_before.json'),
        memory_after_sha256=sha(out/'memory_after.json'))
    if batched:result.update(batch_size=c['batch_size'],input_identity=input_identity)
    write(out/'model_result.json',result)
    return 0


def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True)
    p.add_argument('--run-reviewed-model',action='store_true');a=p.parse_args(argv)
    return run(a.config,a.output,enabled=a.run_reviewed_model)


if __name__=='__main__':raise SystemExit(main())
