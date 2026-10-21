"""Explicit same-process CUPTI session; importing this module runs no vendor API.

The new observation sink forwards the original NVTX calls at their existing
sites and adds non-synchronizing same-CUPTI-clock markers. It does not replace
the model, token copy, stream policy, or Host-readable completion operation.
Its overhead and provider qualification are separate from old Nsight results.
"""
from contextlib import contextmanager
import ctypes
import hashlib
import json
import os
from pathlib import Path


def require(ok,reason):
    if not ok:raise ValueError('CUPTI_TIMELINE_SESSION_'+reason)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


class CaptureSession:
    def __init__(self,config,output,*,allow_target_capture=False,_library_factory=None):
        self.config=dict(config);self.output=Path(output).resolve();self.allowed=allow_target_capture
        self.factory=_library_factory;self.lib=None;self.open_code=None;self.close_code=None;self.wrappers=0

    def __enter__(self):
        require(self.allowed is True,'EXPLICIT_OPT_IN_REQUIRED')
        if self.output.exists():raise FileExistsError(self.output)
        for key in ('client','cupti'):
            p=Path(self.config[key]);require(p.is_absolute() and p.is_file(),'LIBRARY_PATH')
            require(sha(p)==self.config[key+'_sha256'],'LIBRARY_HASH')
        require(isinstance(self.config['session_id'],str) and self.config['session_id'] and
            self.config['session_id'].isascii(),'SESSION_ID')
        self.output.mkdir(parents=True,exist_ok=False)
        if self.factory is None:
            require(os.name=='nt','WINDOWS_CLIENT_REQUIRED')
            self.lib=ctypes.WinDLL(str(Path(self.config['client']).resolve()),winmode=0x1100)
        else:self.lib=self.factory(str(Path(self.config['client']).resolve()))
        signatures={'ep_timeline_abi_version':[],
            'ep_timeline_open':[ctypes.c_wchar_p,ctypes.c_char_p],
            'ep_timeline_mark':[ctypes.c_int,ctypes.c_char_p],
            'ep_timeline_close':[ctypes.c_wchar_p]}
        for name,args in signatures.items():
            fn=getattr(self.lib,name);fn.argtypes=args;fn.restype=ctypes.c_int
        require(self.lib.ep_timeline_abi_version()==1,'ABI_VERSION')
        self.open_code=self.lib.ep_timeline_open(str(Path(self.config['cupti']).resolve()),self.config['session_id'].encode('ascii'))
        if self.open_code!=0:
            self.__exit__(RuntimeError,RuntimeError('OPEN_FAILED'),None)
            require(False,'OPEN_FAILED:'+str(self.open_code))
        return self

    def __exit__(self,typ,error,tb):
        require(not self.wrappers,'NVTX_WRAPPER_STILL_ACTIVE')
        self.close_code=self.lib.ep_timeline_close(str(self.output/'capture.json'))
        r=dict(schema_version='cupti-timeline-session-receipt/0.1.0',session_id=self.config['session_id'],
            pid=os.getpid(),open_code=self.open_code,close_code=self.close_code,
            model_error_type=typ.__name__ if typ else None,
            client_sha256=self.config['client_sha256'],cupti_sha256=self.config['cupti_sha256'],
            verification_mode='CPU_LIBRARY_DOUBLE_NOT_GPU' if self.factory else 'TARGET_CUPTI_UNQUALIFIED',
            capture_sha256=sha(self.output/'capture.json') if (self.output/'capture.json').is_file() else None,
            provider_qualification='NOT_GRANTED',A_COE_admission='NOT_ASSESSED',automatic_retry=False)
        with (self.output/'receipt.json').open('x',encoding='utf8') as f:json.dump(r,f,indent=2)
        if typ is None:require(self.open_code==0 and self.close_code==0,'CLOSE_FAILED:'+str(self.close_code))
        return False

    def mark(self,action,label):
        require(self.lib is not None and self.open_code==0 and self.close_code is None,'SESSION_NOT_OPEN')
        require(type(label) is str,'MARKER_LABEL')
        require(self.lib.ep_timeline_mark(action,label.encode('utf8'))==0,'MARKER_FAILED')

    @contextmanager
    def nvtx_sink(self,nvtx):
        require(self.open_code==0 and self.close_code is None,'SESSION_NOT_OPEN')
        require(not self.wrappers,'NESTED_NVTX_WRAPPER')
        old={k:getattr(nvtx,k) for k in ('range_push','range_pop','mark')}
        def push(label):
            self.mark(1,label);return old['range_push'](label)
        def pop():
            result=old['range_pop']();self.mark(2,'');return result
        def point(label):
            self.mark(0,label);return old['mark'](label)
        new=dict(range_push=push,range_pop=pop,mark=point);self.wrappers=1
        try:
            for key,fn in new.items():setattr(nvtx,key,fn)
            yield
        finally:
            conflict=False
            for key,fn in new.items():
                if getattr(nvtx,key) is fn:setattr(nvtx,key,old[key])
                else:conflict=True
            self.wrappers=0;require(not conflict,'NVTX_WRAPPER_CHANGED')
