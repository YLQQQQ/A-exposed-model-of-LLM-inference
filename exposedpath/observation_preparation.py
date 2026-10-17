"""Closed Engineering O/P ablation. No new completion or accounting semantics."""
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import threading

from .gate8_isolated_preflight import read,sha,write_new

VERSION='OBSERVATION-PREPARATION-ENGINEERING/0.1'
PROFILE='OBSERVATION_PREPARATION_BOTH_TOKENS/0.1'
PASS_VERSION='exposedpath-observation-preparation-pass/0.1.0'
EXECUTION_VERSION='exposedpath-observation-preparation-execution/0.1.0'
TOKEN_VERSION='exposedpath-observation-preparation-tokens/0.1.0'
RESULT_VERSION='observation-preparation-result/0.1.0'
STATUS='OBSERVATION_PREPARATION_BOTH_TOKENS_PENDING_REVIEW'
ORDERS=(((32,'O'),(32,'P'),(512,'P'),(512,'O')),
        ((512,'O'),(512,'P'),(32,'P'),(32,'O')))


def require(ok,reason):
    if not ok:raise ValueError('OBS_PREP_'+reason)


def active(value):
    return isinstance(value,dict) and value.get('version')==VERSION


def schedule(batch_id,commit):
    require(isinstance(batch_id,str) and re.fullmatch('[A-Za-z0-9_-]{1,60}',batch_id),'BATCH_ID')
    require(isinstance(commit,str) and re.fullmatch('[0-9a-f]{40}',commit),'COMMIT')
    return [dict(version=VERSION,batch_id=batch_id,execution_commit=commit,block=b,position=p,
        condition=f'G{n}{v}',variant=v,input_tokens=n,batch_size=1,output_tokens=2,
        pass_id='pass1',pair_id=f'{batch_id}-b{b}-G{n}',run_id=f'{batch_id}-b{b}-G{n}{v}-pass1',
        warmup_count=3,repeat_count=1,purpose='OBSERVATION_PREPARATION_SENSITIVITY_ONLY',
        declaration_role='PRE_EXECUTION',formal_eligible=False)
        for b,order in enumerate(ORDERS,1) for p,(n,v) in enumerate(order,1)]


def validate_binding(value):
    require(isinstance(value,dict),'BINDING')
    require(any(value==b and all(type(value[k]) is type(v) for k,v in b.items())
        for b in schedule(value.get('batch_id'),value.get('execution_commit'))),'BINDING')
    return value


def minimal_fields(binding):
    b=validate_binding(binding)
    from .gate8_engineering_contract import declaration
    scope=declaration('sdpa');scope['profile']=PROFILE
    return dict(batch_load=deepcopy(b),run_role='ENGINEERING',data_role='Engineering',run_id=b['run_id'],
        fixed_input_tokens=b['input_tokens'],fixed_output_tokens=2,batch_size=1,warmup_count=3,repeat_count=1,
        execution_mode='eager',attention_backend='sdpa',dtype_and_quantization='fp16',
        sampling_config={'do_sample':False},study_mode='G1_NATURAL',n1_intervention=None,engineering_scope=scope,
        engineering_pair=dict(schema_version='gate8-engineering-pair/0.1',pair_id=b['pair_id'],pass_id='pass1'))


def validate(manifest):
    b=validate_binding(manifest.get('batch_load'))
    require(not any(k in manifest for k in ('pilot','formal','n1_model','completion_path','domain_qualification','gate10_workload')),'MIXED_DOMAIN')
    require(all(type(manifest.get(k)) is type(v) and manifest[k]==v for k,v in minimal_fields(b).items()),'DECLARATION')
    require(manifest['runner_git_commit']==b['execution_commit'] and manifest['runner_git_dirty'] is False,'EXECUTION_IDENTITY')
    return b


def validate_input(prompt,config,length):
    from .gate10_workload import validate_input as single
    require(length in (32,512) and type(length) is int,'INPUT_LENGTH')
    # Reuse the exact token range, mask, specials and 32-token cycle checks.
    expanded=deepcopy(prompt)
    if length==32:
        require(prompt.get('fixed_input_tokens')==32 and len(prompt.get('samples',[]))==1,'INPUT_SHAPE')
        for key in ('input_ids','attention_mask'):
            require(len(prompt['samples'][0].get(key,[]))==32,'INPUT_SHAPE')
            expanded['samples'][0][key]=prompt['samples'][0][key]*16
        expanded['fixed_input_tokens']=512
    single(expanded,config,512)


def validate_prepared(manifest,prepared,root):
    b=validate(manifest)
    require('target_python' in manifest and 'isolated_preflight_version' in manifest,'VERIFIED_ENTRY')
    require(sha(Path(prepared)/'prompt.json')==manifest['prompt_tokens_sha256']
        and sha(Path(root)/'exposedpath/runner.py')==manifest['runner_source_sha256'],'INPUT_HASH')
    require(manifest.get('preparation_source_sha256')==sha(Path(root)/'exposedpath/observation_preparation.py'),'PREPARATION_SOURCE_HASH')
    validate_input(read(Path(prepared)/'prompt.json'),read(Path(manifest['model_id'])/'config.json'),b['input_tokens'])


@dataclass(frozen=True)
class PreparedToken:
    token_index:int
    phase:str
    label:str


class Execution:
    """Single request cache; only invariant identity/encoding runs before drain."""
    def __init__(self,binding):
        from . import coe_input_pilot as axis
        self.axis=axis.active(binding)
        self.binding=deepcopy(axis.validate_binding(binding) if self.axis else validate_binding(binding))
        self.variant='P' if self.axis else binding['variant']
        self.closed=True;self.used=[]

    def prepare(self,identity,output_len,runner):
        require(self.closed and not self.used and identity['run_id']==self.binding['run_id']
            and identity['request_id']=='request-0' and identity['repeat_id']=='0'
            and identity['run_role']==('PILOT' if self.axis else 'ENGINEERING') and identity['pass_id']=='pass1' and output_len==2,'CACHE_BINDING')
        self.identity=tuple(sorted(identity.items()));self.pid=os.getpid();self.tid=threading.get_native_id()
        self.closed=False;self.prepared=()
        if self.variant=='O':return runner.observe_token_ready_boundary
        self.prepared=tuple(PreparedToken(i,phase,runner.make_structured_nvtx_label(
            runner.make_natural_token_ready_identity(identity,phase=phase,token_index=i,
                callsite_id=f'{phase}.token_ready',sync_ordinal=i,token_ready_mechanism=runner.TOKEN_READY_MECHANISM)))
            for i,phase in enumerate(('prefill','decode')))
        def ready(token_tensor,*,token_index,identity_base,phase,clock_ns=runner.time.perf_counter_ns,
                  emit_nvtx,gate8_recorder=None,completion_controller=None):
            require(not self.closed and tuple(sorted(identity_base.items()))==self.identity
                and os.getpid()==self.pid and threading.get_native_id()==self.tid
                and type(token_index) is int and token_index==len(self.used) and token_index in (0,1)
                and phase==self.prepared[token_index].phase and completion_controller is None,'CACHE_BINDING_OR_STALE')
            prepared=self.prepared[token_index];self.used.append(token_index)
            if emit_nvtx:runner.torch.cuda.nvtx.range_push(prepared.label)
            try:
                values=token_tensor.detach().cpu().reshape(-1).tolist()
                host_token_ids=tuple(int(value) for value in values)
                if not host_token_ids:raise RuntimeError(f'Token-ready boundary {token_index} produced no Host-readable IDs')
                completed_ns=clock_ns()
                if gate8_recorder is not None:gate8_recorder.observe(completed_ns,token_index)
            finally:
                if emit_nvtx:runner.torch.cuda.nvtx.range_pop()
            return runner.TokenReadyBoundary(token_index,host_token_ids,completed_ns,'natural_token_ready',runner.TOKEN_READY_MECHANISM)
        return ready

    def invalidate(self):self.closed=True

    def finish(self,identity):
        require(not self.closed and tuple(sorted(identity.items()))==self.identity,'CACHE_FINISH')
        require(self.used==([0,1] if self.variant=='P' else []),'CACHE_USE_COUNT')
        self.closed=True
        # O call count is a source-contract fact, not a sampled measurement.
        return dict(version=self.binding['version'],binding=self.binding,identity=dict(self.identity),pid=self.pid,tid=self.tid,
            prepared_count=len(self.prepared),consumed_token_indices=list(self.used),
            prepared_labels=[p.label for p in self.prepared],closed=True,
            preparation_position='BEFORE_FINAL_DRAIN' if self.variant=='P' else 'ORIGINAL_HELPER_ONSITE',
            dynamic_operations_moved=False)


def observation(identity,result,manifest):
    require(result['batch_size']==1 and result['actual_input_tokens']==manifest['fixed_input_tokens'],'ACTUAL_INPUT')
    return dict(identity=identity,actual_input_shape=[1,manifest['fixed_input_tokens']],sample_indices=[0],
        token_ids=[list(t.host_token_ids) for t in result['token_ready_boundaries']],
        actual_output_tokens_per_sample=[result['actual_output_tokens']],early_eos=result['early_eos'])


def validate_actual_requests(manifest,ledger):
    b=validate(manifest)
    from .batch_load import request_plan
    require(ledger['schema_version']==PASS_VERSION and ledger['batch_load']==b
        and ledger['run_role']=='ENGINEERING' and ledger['data_role']=='Engineering','LEDGER')
    require([dict(request_id=r['identity']['request_id'],repeat_id=r['identity']['repeat_id'],request_role=r['request_role'])
        for r in ledger['requests']]==request_plan(b),'ACTUAL_PLAN')
    require(all(r['outcome']=='COMPLETE' and not r['reasons'] and r['expected_output_tokens']==2
        and ((r['actual_output_tokens'] is None and r['early_eos'] is None) if r['request_role']=='warmup'
        else r['actual_output_tokens']==2 and r['early_eos'] is False) for r in ledger['requests']),'ACTUAL_COMPLETION')


def validate_tokens(path,manifest,ledger,execution,manifest_path,producer_path):
    b=validate(manifest);validate_actual_requests(manifest,ledger)
    require(execution['schema_version']==EXECUTION_VERSION and execution['batch_load']==b
        and execution['batch_tokens_sha256']==sha(path),'EXECUTION_TOKEN_HASH')
    t=read(path)
    require(set(t)=={'schema_version','batch_load','manifest_sha256','producer_receipt_sha256','requests'}
        and t['schema_version']==TOKEN_VERSION and t['batch_load']==b and t['manifest_sha256']==sha(manifest_path)
        and t['producer_receipt_sha256']==sha(producer_path) and len(t['requests'])==1,'TOKEN_LINEAGE')
    r=t['requests'][0];ids=r['token_ids']
    require(set(r)=={'identity','actual_input_shape','sample_indices','token_ids','actual_output_tokens_per_sample','early_eos'}
        and r['identity']==ledger['requests'][-1]['identity'] and r['actual_input_shape']==[1,b['input_tokens']]
        and r['sample_indices']==[0] and r['actual_output_tokens_per_sample']==[2] and r['early_eos'] is False
        and isinstance(ids,list) and len(ids)==2 and all(isinstance(a,list) and len(a)==1
        and type(a[0]) is int and a[0]>=0 for a in ids),'TOKEN_VALUES_OR_IDENTITY')
    p=execution['observation_preparation']
    require(p['version']==VERSION and p['binding']==b and p['identity']==r['identity']
        and p['pid']==ledger['pid'] and type(p['tid']) is int and p['tid']>0 and p['closed'] is True
        and p['dynamic_operations_moved'] is False,'PREPARATION_RECEIPT')
    from .nvtx import make_natural_token_ready_identity,make_structured_nvtx_label
    from .results import TOKEN_READY_MECHANISM
    expected=[make_structured_nvtx_label(make_natural_token_ready_identity(r['identity'],phase=phase,token_index=i,
        callsite_id=f'{phase}.token_ready',sync_ordinal=i,token_ready_mechanism=TOKEN_READY_MECHANISM))
        for i,phase in enumerate(('prefill','decode'))]
    require(type(p['prepared_count']) is int and p['prepared_count']==(2 if b['variant']=='P' else 0)
        and p['consumed_token_indices']==([0,1] if b['variant']=='P' else [])
        and p['prepared_labels']==(expected if b['variant']=='P' else [])
        and p['preparation_position']==('BEFORE_FINAL_DRAIN' if b['variant']=='P' else 'ORIGINAL_HELPER_ONSITE'),'PREPARATION_CONTENT')
    return ids


def execution_extension(manifest,ledger,execution,execution_path,manifest_path,producer_path,token_path):
    require(token_path is not None and Path(token_path).resolve()==Path(execution_path).resolve().parent/'batch_tokens.json','TOKEN_PATH')
    validate_tokens(token_path,manifest,ledger,execution,manifest_path,producer_path)
    require(sha(Path(execution_path).parent/'preparation_source.py')==manifest['preparation_source_sha256'],'EXECUTED_PREPARATION_SOURCE_HASH')
    return {'batch_load','batch_tokens_sha256','observation_preparation'},EXECUTION_VERSION


def make_inputs(seed,expected_sha,output):
    require(sha(seed)==expected_sha,'SEED_HASH');value=read(seed)
    require(value['fixed_input_tokens']==512 and len(value['samples'])==1,'SEED_SHAPE')
    ids=value['samples'][0]['input_ids'];require(len(ids)==512 and ids==ids[:32]*16,'SEED_CYCLE')
    out=Path(output);out.mkdir(parents=True,exist_ok=False);paths={}
    for n in (32,512):
        p=deepcopy(value);p['fixed_input_tokens']=n
        p['samples']=[dict(sample_index=0,input_ids=ids[:n],attention_mask=[1]*n)]
        p['construction']=dict(rule='PREFIX_OF_VERIFIED_512_CYCLE32',source_sha256=expected_sha)
        path=out/f'input_{n}.json';write_new(path,p);paths[n]=path
    return paths


METRICS=('candidate_ns','original_sync_ns','kernel_ns','memop_ns','wall_ns','uncovered_ns',
         'copy_wall_ns','sync_wall_ns','same_operation_all_gpu_union_ns')


def block_contrasts(rows):
    """Predeclared complete four-condition block, signed P-O and 512-32."""
    require(len(rows)==4 and all(s['status']=='COMPLETE' for s in rows),'INCOMPLETE_BLOCK')
    values={(s['binding']['input_tokens'],s['binding']['variant']):s['result'] for s in rows}
    require(set(values)=={(32,'O'),(32,'P'),(512,'O'),(512,'P')},'BLOCK_CONDITIONS')
    result=[]
    for token in (0,1):
        metrics={}
        for key,r in values.items():
            op=r['operations'][token]
            require(op['token_index']==token,'TOKEN_ORDER')
            metrics[key]={**{k:op[k] for k in METRICS},**{k:op['positions'][k] for k in ('H_ns','D_ns')}}
        difference=lambda a,b:{k:metrics[a][k]-metrics[b][k] for k in metrics[a]}
        po={str(n):difference((n,'P'),(n,'O')) for n in (32,512)}
        length={v:difference((512,v),(32,v)) for v in ('O','P')}
        result.append(dict(token_index=token,phase='prefill' if token==0 else 'decode',
            P_minus_O=po,length_512_minus_32=length,
            difference_of_length_responses={k:length['P'][k]-length['O'][k] for k in length['P']}))
    return dict(block=rows[0]['binding']['block'],per_token=result,
        interpretation='SENSITIVITY_SCREEN_ONLY_NOT_STABILITY_OR_CAUSAL_EFFECT')


def run_batch(batch_id,commit,output,collect):
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    r=dict(version=VERSION,status='BLOCKED',run_role='ENGINEERING',data_role='Engineering',
        model_process_budget=8,profile_budget=8,automatic_retry=False,replacement=False,
        runs=[dict(binding=b,status='NOT_RUN') for b in schedule(batch_id,commit)],blocks=[],incomplete_blocks=[1,2],
        sensitivity_verdict='NOT_ASSESSED',formal_eligible=False,dropped_records_status='UNKNOWN',measurement_validity='NOT_ASSESSED')
    def persist():
        p=out/'batch_report.pending.json';write_new(p,r);p.replace(out/'batch_report.json')
    persist();tokens={}
    for slot in r['runs']:
        b=slot['binding'];print(f"[preparation] block={b['block']} position={b['position']} {b['condition']} START",flush=True)
        try:
            value=collect(b,out/b['run_id'])
            require(value['status']==STATUS and value['binding']==b,'RESULT_BINDING')
            ids=value['token_ids']
            require(isinstance(ids,list) and len(ids)==2 and all(isinstance(t,list) and len(t)==1
                and type(t[0]) is int and t[0]>=0 for t in ids),'ACTUAL_TOKENS')
            require(b['input_tokens'] not in tokens or tokens[b['input_tokens']]==ids,'SAME_INPUT_TOKEN_PARITY')
            require(len(value['operations'])==2 and all(type(o['candidate_ns']) is int and o['candidate_ns']>=0 for o in value['operations']),'OPERATION_VALUES')
            tokens[b['input_tokens']]=ids;slot.update(status='COMPLETE',result=value)
            rows=[s for s in r['runs'] if s['binding']['block']==b['block']]
            if all(s['status']=='COMPLETE' for s in rows):
                r['blocks'].append(block_contrasts(rows));r['incomplete_blocks'].remove(b['block'])
        except Exception as exc:
            slot.update(status='BLOCKED',error=f'{type(exc).__name__}: {exc}');persist();break
        persist()
    else:
        decreases=[t['P_minus_O'][str(n)]['H_ns']<0 for block in r['blocks'] for t in block['per_token'] for n in (32,512)]
        r.update(status='FIXED_EIGHT_COMPLETE_STOP_FOR_REVIEW',
            sensitivity_verdict='CONSISTENT_H_DECREASE_SCREEN_ONLY' if all(decreases) else 'INCONCLUSIVE_OR_MIXED',
            causal_effect_verdict='NOT_IDENTIFIED_AUTOMATICALLY_REVIEW_D_MEMBERS_AND_SUBMISSION_STRUCTURE')
        persist()
    return r
