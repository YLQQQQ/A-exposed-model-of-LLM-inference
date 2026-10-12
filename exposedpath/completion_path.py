"""Prospective two-P1 completion-path Engineering contract, never natural G1."""
from copy import deepcopy
import os
import threading

from . import batch_load

VERSION='COMPLETION-PATH-ENGINEERING/0.1'
PROFILE='TARGET_SCOPE_COMPLETION_PATH_PREFILL/0.1'
PASS_VERSION='exposedpath-pass-identity/0.6.0'
EXECUTION_VERSION='exposedpath-completion-path-execution/0.1.0'
MARKER='EXPOSEDPATH_COMPLETION_PATH_V1:'
ORIGIN='engineering_precopy_completion'


def require(ok,reason):
    if not ok:raise ValueError('COMPLETION_PATH_'+reason)


def schedule(batch_id):
    batch_load.schedule(batch_id)  # Reuse the bounded identifier validation.
    return [dict(version=VERSION,batch_id=batch_id,variant=v,run_id=f'{batch_id}-{v}',
        pass_id='pass1',batch_size=4,input_tokens=512,output_tokens=2,warmup_count=3,
        repeat_count=1,phase='prefill',token_index=0,formal_eligible=False,
        purpose='COMPLETION_PATH_LOCAL_PREFILL_ONLY') for v in ('C0','Cpre')]


def validate_binding(value):
    require(isinstance(value,dict),'BINDING')
    require(any(value==b and all(type(value[k]) is type(v) for k,v in b.items())
        for b in schedule(value.get('batch_id'))),'BINDING')
    return value


def batch_binding(value):
    validate_binding(value)
    # Separate request/WMPC per variant; reuse the existing clone/token contract.
    return batch_load.schedule(value['run_id'])[3]


def minimal_fields(value):
    result=batch_load.minimal_fields(batch_binding(value))
    result.update(completion_path=deepcopy(value),study_mode='COMPLETION_PATH_ENGINEERING',
        domain_qualification=None)
    result['engineering_scope']['profile']=PROFILE
    return result


def validate(manifest):
    b=validate_binding(manifest.get('completion_path'))
    require(all(type(manifest.get(k)) is type(v) and manifest[k]==v
        for k,v in minimal_fields(b).items()),'DECLARATION')
    return b


class Execution:
    """One measured first-token hook; no new stream, warmup or Decode operation."""
    def __init__(self,binding,cuda):
        self.binding=validate_binding(binding);self.cuda=cuda;self.calls=[]

    def before_copy(self,identity,token_index,phase):
        if token_index!=0:return
        require(phase=='prefill' and not self.calls,'ACTUAL_COUNT_OR_PHASE')
        require(identity['run_id']==batch_binding(self.binding)['run_id']
            and identity['pass_id']=='pass1' and identity['request_id']=='request-0','ACTUAL_IDENTITY')
        stream=self.cuda.current_stream(0)
        require(stream.device.index==0 and type(stream.cuda_stream) is int,'ACTUAL_STREAM')
        call=dict(identity=deepcopy(identity),variant=self.binding['variant'],phase=phase,
            token_index=token_index,pid=os.getpid(),thread_id=threading.get_native_id(),
            logical_device=0,native_stream=stream.cuda_stream,sync_count=0,status='STARTED')
        self.calls.append(call)
        import json
        self.cuda.nvtx.range_push(MARKER+json.dumps(call,sort_keys=True,separators=(',',':')))
        try:
            if self.binding['variant']=='Cpre':
                from .nvtx import make_structured_nvtx_label
                marker=dict(identity,kind='sync',phase='prefill',sync_origin=ORIGIN,
                    callsite_id='engineering.prefill.precopy',sync_ordinal=0,
                    intervention_variant_id='Cpre',intervention_ordinal=0)
                self.cuda.nvtx.range_push(make_structured_nvtx_label(marker))
                try:
                    stream.synchronize();call['sync_count']=1
                finally:self.cuda.nvtx.range_pop()
            after=self.cuda.current_stream(0)
            require(after.device.index==0 and after.cuda_stream==stream.cuda_stream,'STREAM_CHANGED')
            call['status']='COMPLETE'
        except Exception:
            call['status']='FAILED';raise
        finally:self.cuda.nvtx.range_pop()


def validate_calls(manifest,ledger,execution):
    b=validate(manifest)
    require(ledger.get('completion_path')==b and execution.get('completion_path')==b,'CALL_BINDING')
    calls=execution.get('completion_calls')
    require(isinstance(calls,list) and len(calls)==1,'ACTUAL_COUNT')
    c=calls[0];identity=ledger['requests'][-1]['identity']
    require(set(c)=={'identity','variant','phase','token_index','pid','thread_id','logical_device',
        'native_stream','sync_count','status'},'CALL_SCHEMA')
    require(c['identity']==identity and c['variant']==b['variant'] and c['pid']==ledger['pid']
        and c['phase']=='prefill' and type(c['token_index']) is int and c['token_index']==0 and c['status']=='COMPLETE'
        and type(c['logical_device']) is int and c['logical_device']==0 and type(c['native_stream']) is int and c['native_stream']>=0
        and type(c['thread_id']) is int and c['thread_id']>0
        and type(c['sync_count']) is int and c['sync_count']==(1 if b['variant']=='Cpre' else 0),'ACTUAL_CALL')
    return c


def run_batch(batch_id,output,collect):
    from pathlib import Path
    from .gate8_isolated_preflight import write_new
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    result=dict(version=VERSION,status='BLOCKED',automatic_retry=False,model_process_budget=2,
        profile_budget=2,runs=[dict(binding=b,status='NOT_RUN') for b in schedule(batch_id)])
    for row in result['runs']:
        b=row['binding'];print('[completion] '+b['variant']+' START',flush=True)
        try:
            row.update(collect(b,out/b['variant']))
            require(row['status']=='PREFILL_COMPLETE_STOP_FOR_REVIEW','LOCAL_REVIEW')
        except Exception as exc:
            row.update(status='BLOCKED',error=f'{type(exc).__name__}: {exc}');break
        finally:write_new(out/(b['variant']+'.receipt.json'),row)
    else:result['status']='BATCH_COMPLETE_STOP_FOR_REVIEW'
    write_new(out/'batch_report.json',result)
    return result
