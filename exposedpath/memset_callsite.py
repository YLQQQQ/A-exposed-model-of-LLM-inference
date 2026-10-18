"""One real 1024 source diagnostic. No parameter, S/A/B or COE admission."""
from copy import deepcopy
import re

VERSION='MEMSET-CALLSITE-ENGINEERING/0.1'
PROFILE='MEMSET_CALLSITE_SOURCE_ONLY/0.1'
PROFILE_FLAGS=('--trace=cuda,nvtx','--sample=process-tree','--sampling-frequency=200',
    '--cudabacktrace=all:0','--cuda-memory-usage=false','--cuda-trace-scope=process-tree',
    '--isr=false','--duration=240','--force-overwrite=false')


def require(ok,reason):
    if not ok:raise ValueError('MEMSET_CALLSITE_'+reason)


def active(value):return isinstance(value,dict) and value.get('version')==VERSION


def binding(run_id,commit):
    require(isinstance(run_id,str) and re.fullmatch('[A-Za-z0-9_-]{1,60}',run_id),'RUN_ID')
    require(isinstance(commit,str) and re.fullmatch('[0-9a-f]{40}',commit),'COMMIT')
    return dict(version=VERSION,batch_id=run_id,execution_commit=commit,run_id=run_id,
        condition='G1024P_SOURCE',variant='P',input_tokens=1024,batch_size=1,output_tokens=2,
        pass_id='pass1',pair_id=run_id+'-source',warmup_count=3,repeat_count=1,
        purpose='NATIVE_CALLSITE_ONLY_NOT_PARAMETERS_OR_PERFORMANCE',
        declaration_role='PRE_EXECUTION',formal_eligible=False)


def validate_binding(value):
    require(isinstance(value,dict),'BINDING')
    expected=binding(value.get('run_id'),value.get('execution_commit'))
    require(value==expected and all(type(value[k]) is type(v) for k,v in expected.items()),'BINDING')
    return value


def minimal_fields(value):
    b=validate_binding(value)
    from .gate8_engineering_contract import declaration
    scope=declaration('sdpa');scope['profile']=PROFILE
    return dict(batch_load=deepcopy(b),run_role='ENGINEERING',data_role='Engineering',run_id=b['run_id'],
        fixed_input_tokens=1024,fixed_output_tokens=2,batch_size=1,warmup_count=3,repeat_count=1,
        execution_mode='eager',attention_backend='sdpa',dtype_and_quantization='fp16',
        sampling_config={'do_sample':False},study_mode='G1_NATURAL',n1_intervention=None,
        engineering_scope=scope,engineering_pair=dict(schema_version='gate8-engineering-pair/0.1',
            pair_id=b['pair_id'],pass_id='pass1'))


def validate_input(prompt,config):
    from . import coe_input_pilot as axis
    require(prompt.get('fixed_input_tokens')==1024,'INPUT_LENGTH')
    return axis.validate_input(prompt,config,1,version=axis.MIDPOINT_VERSION)


def profile_argv(nsys,python,prepared,output,root):
    from pathlib import Path
    from scripts.gate8_diagnostic_collect import target_argv
    from .gate8_isolated_preflight import read
    from .observation_preparation import validate_prepared
    manifest=read(Path(prepared)/'manifest.json')
    require(active(manifest.get('batch_load')),'EXPLICIT_DIAGNOSTIC_ROLE')
    validate_prepared(manifest,prepared,root)
    return [str(nsys),'profile',*PROFILE_FLAGS,'--kill=true','--output='+str(Path(output)/'capture'),
        *target_argv(python,prepared,output,root)]
