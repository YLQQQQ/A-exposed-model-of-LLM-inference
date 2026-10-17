"""One prospective B2 Engineering parameter profile, not old batch/Pilot permission."""
from copy import deepcopy
import re
import json
from pathlib import Path
from .gate8_isolated_preflight import read,sha

VERSION='MEMSET-PYTORCH-PREFILL-PARAMS/0.1'
PROFILE='MEMSET_PREFILL_PARAMETER_DIAGNOSTIC/0.1'
EXECUTION_VERSION='exposedpath-memset-prefill-execution/0.1.0'


def require(ok,reason):
    if not ok:raise ValueError('MEMSET_PREFILL_'+reason)


def active(b):return isinstance(b,dict) and b.get('version')==VERSION


def binding(run_id,commit,recorder,runtime):
    require(isinstance(run_id,str) and re.fullmatch('[0-9a-f]{32}',run_id),'RUN_ID')
    require(isinstance(commit,str) and re.fullmatch('[0-9a-f]{40}',commit),'COMMIT')
    for r in (recorder,runtime):
        require(isinstance(r,dict) and set(r)=={'path','sha256'} and isinstance(r['path'],str) and r['path']
            and isinstance(r['sha256'],str) and re.fullmatch('[0-9a-f]{64}',r['sha256']),'MODULE_IDENTITY')
    return dict(version=VERSION,batch_id=run_id,condition='B2',batch_size=2,pair_id=run_id,
        run_id=run_id,pass_id='pass1',input_tokens=512,output_tokens=2,warmup_count=3,repeat_count=1,
        purpose='PREFILL_PARAMETERS_ONLY_NOT_PILOT',declaration_role='PRE_EXECUTION',formal_eligible=False,
        execution_commit=commit,recorder=deepcopy(recorder),runtime=deepcopy(runtime))


def validate_binding(b):
    require(isinstance(b,dict),'BINDING')
    expected=binding(b.get('run_id'),b.get('execution_commit'),b.get('recorder',{}),b.get('runtime',{}))
    require(b==expected and all(type(b[k]) is type(v) for k,v in expected.items()),'BINDING')
    return b


def minimal_fields(b):
    validate_binding(b)
    from .gate8_engineering_contract import declaration
    scope=declaration('sdpa');scope['profile']=PROFILE
    return dict(batch_load=deepcopy(b),run_role='ENGINEERING',data_role='Engineering',run_id=b['run_id'],
        fixed_input_tokens=512,fixed_output_tokens=2,batch_size=2,warmup_count=3,repeat_count=1,
        execution_mode='eager',attention_backend='sdpa',dtype_and_quantization='fp16',
        sampling_config={'do_sample':False},study_mode='G1_NATURAL',n1_intervention=None,engineering_scope=scope,
        required_software=dict(runtime_version='python3.11.16',inference_framework_version='torch2.6.0+cu124',cuda_version_used='12.4'))


def validate(m):
    b=validate_binding(m.get('batch_load'))
    require(not any(k in m for k in ('pilot','formal','completion_path','n1_model','domain_qualification','gate10_workload')),'MIXED_DOMAIN')
    require(all(type(m.get(k)) is type(v) and json.dumps(m[k],sort_keys=True)==json.dumps(v,sort_keys=True)
        for k,v in minimal_fields(b).items()),'DECLARATION')
    require(m['runner_git_commit']==b['execution_commit'] and m['runner_git_dirty'] is False,'COMMIT')
    return b


def validate_input(prompt,config):
    from .coe_pilot import validate_input as common
    return common(prompt,config,2)


def validate_target_software(actual,m):
    from .coe_pilot import SOFTWARE
    require(actual==SOFTWARE and m.get('required_software')==SOFTWARE,'TARGET_SOFTWARE')


def creation_filetime():
    import ctypes as c
    from ctypes import wintypes as w
    class FT(c.Structure):_fields_=[('low',w.DWORD),('high',w.DWORD)]
    k=c.WinDLL('kernel32',use_last_error=True);k.GetCurrentProcess.restype=w.HANDLE
    k.GetProcessTimes.argtypes=[w.HANDLE,*[c.POINTER(FT)]*4];k.GetProcessTimes.restype=w.BOOL
    times=[FT() for _ in range(4)]
    require(k.GetProcessTimes(k.GetCurrentProcess(),*[c.byref(v) for v in times]),'PROCESS_INSTANCE')
    return (times[0].high<<32)|times[0].low


def validate_prepared(m,prepared,root):
    b=validate(m)
    require('target_python' in m and 'isolated_preflight_version' in m,'VERIFIED_ENTRY')
    require(sha(Path(prepared)/'prompt.json')==m['prompt_tokens_sha256']
        and sha(Path(root)/'exposedpath/runner.py')==m['runner_source_sha256'],'INPUT_HASH')
    require(validate_input(read(Path(prepared)/'prompt.json'),read(Path(m['model_id'])/'config.json'))==m['memset_input'],'BATCH_INPUT')
    for key in ('recorder','runtime'):require(sha(b[key]['path'])==b[key]['sha256'],'MODULE_HASH:'+key)


class Recorder:
    """Install before the original drain; enable only after it. No CUDA API added."""
    def __init__(self,b):
        self.b=validate_binding(b);self.dll=None;self.value=None;self.enabled=False

    def install(self,identity):
        import ctypes as c
        from ctypes import wintypes as w
        import os
        require(self.dll is None,'RECORDER_REUSE')
        for key in ('recorder','runtime'):require(sha(self.b[key]['path'])==self.b[key]['sha256'],'MODULE_HASH:'+key)
        k=c.WinDLL('kernel32',use_last_error=True)
        k.GetModuleHandleW.argtypes=[w.LPCWSTR];k.GetModuleHandleW.restype=w.HMODULE
        k.GetModuleFileNameW.argtypes=[w.HMODULE,w.LPWSTR,w.DWORD];k.GetModuleFileNameW.restype=w.DWORD
        runtime=k.GetModuleHandleW(str(Path(self.b['runtime']['path']).resolve()))
        require(runtime,'SHARED_RUNTIME_NOT_LOADED')
        buf=c.create_unicode_buffer(32768);n=k.GetModuleFileNameW(runtime,buf,len(buf))
        require(0<n<len(buf) and Path(buf.value).resolve()==Path(self.b['runtime']['path']).resolve(),'LOADED_RUNTIME_PATH')
        k.GetCurrentThreadId.restype=w.DWORD
        self.value=dict(schema_version='memset-prefill-side/0.1.0',role='ENGINEERING_MEMSET_PREFILL',
            run_id=self.b['run_id'],pid=os.getpid(),tid=k.GetCurrentThreadId(),creation_filetime=creation_filetime(),
            identity=deepcopy(identity),entry='cudaMemsetAsync',runtime_sha256=self.b['runtime']['sha256'],
            recorder_sha256=self.b['recorder']['sha256'],runtime_path=buf.value,capacity=4096,
            begin_code=None,end_code=None,detach_code=None,completion_observed=False)
        self.dll=c.CDLL(str(Path(self.b['recorder']['path']).resolve()),winmode=0x1100)
        actual_recorder=c.create_unicode_buffer(32768)
        size=k.GetModuleFileNameW(self.dll._handle,actual_recorder,len(actual_recorder))
        require(0<size<len(actual_recorder) and Path(actual_recorder.value).resolve()==Path(self.b['recorder']['path']).resolve(),'RECORDER_LOADED_PATH')
        self.dll.ep_prefill_start.argtypes=[w.HMODULE,c.c_char_p];self.dll.ep_prefill_start.restype=w.LONG
        for name in ('begin','end','stop'):getattr(self.dll,'ep_prefill_'+name).argtypes=[];getattr(self.dll,'ep_prefill_'+name).restype=w.LONG
        self.value['attach_code']=self.dll.ep_prefill_start(runtime,self.b['run_id'].encode('ascii'))
        require(self.value['attach_code']==0,'ATTACH')

    def begin(self,identity):
        require(self.dll is not None and self.value['attach_code']==0 and self.value['identity']==identity
            and not self.enabled,'BEGIN_STATE')
        self.value['begin_code']=self.dll.ep_prefill_begin();self.enabled=self.value['begin_code']==0
        require(self.enabled,'BEGIN')

    def end(self,completed_ns):
        require(self.enabled,'END_STATE');self.value['host_completion_ns']=completed_ns
        self.value['end_code']=self.dll.ep_prefill_end();self.enabled=self.value['end_code']!=0
        self.value['completion_observed']=not self.enabled;require(not self.enabled,'END')

    def close(self,path):
        import ctypes as c
        from ctypes import wintypes as w
        from .gate8_isolated_preflight import write_new
        # Called in the entry's finally; preserve partial evidence even after a
        # model/attach failure. No active exception may be replaced by I/O.
        import sys
        original=sys.exc_info()[0]
        value=self.value or dict(schema_version='memset-prefill-side/0.1.0',role='ENGINEERING_MEMSET_PREFILL',
            status='NOT_STARTED',completion_observed=False)
        try:
            if self.dll is not None and value.get('attach_code')==0:
                if self.enabled:
                    value['abort_end_code']=self.dll.ep_prefill_end();self.enabled=False
                value['detach_code']=self.dll.ep_prefill_stop()
                class Row(c.Structure):
                    _fields_=[('call_id',c.c_uint64),('count',c.c_uint64),('pointer_alias',c.c_uint64),('stream',c.c_size_t),
                        *[(n,w.DWORD) for n in ('pid','tid','entry_error','return_error')],
                        *[(n,c.c_int) for n in ('value','return_code','forwards','completed','push_level','pop_level')]]
                fn=self.dll.ep_prefill_records;fn.argtypes=[c.POINTER(c.c_uint),c.POINTER(w.LONG)];fn.restype=c.POINTER(Row)
                n=c.c_uint();error=w.LONG();rows=fn(c.byref(n),c.byref(error));value['recorder_error']=error.value
                value['calls']=[]
                for i in range(n.value):
                    r=rows[i];row={name:getattr(r,name) for name,_ in Row._fields_ if name!='stream'}
                    row.update(stream_hex=format(r.stream,'x'),completed=bool(r.completed));value['calls'].append(row)
            write_new(path,value)
        except BaseException:
            if original is None:raise
        if original is None and value.get('attach_code')==0:require(value.get('detach_code')==0,'DETACH')
