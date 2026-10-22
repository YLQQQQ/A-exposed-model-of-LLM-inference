"""Prepare/review one controlled completion chain; explicit target execution only.

Reuses the reviewed CaptureSession and v0.3 consumer. Import does not load CUDA.
No package, remote launcher, profiler coexistence, or measurement-rule changes.
"""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import sys
import importlib.util

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'configs/coe_cupti_controlled_v0_1.json'
CLIENT_SHA='5e0ffa4b332652c6107cb278ed300ddc9b1bc0e201a370dbe1040cb463d2247a'
CUPTI_SHA='560a36596b6c6db6ecb44bbdc1b9d3bbf34965e919d13e7285f4d1c3542916ce'
RUNTIME_SHA='f95273031fc5ea44cdb37e0a696a1b15b9d84a4ee977299a6f6e652ef4d790cf'
TIMING='cupti-api22-distinct-api-callback-boundaries/0.2.0'
QUERIES='cupti-api22-driver-queries/0.1.0'
RUNTIME_CBIDS={'cudaDeviceSynchronize':165,'cudaLaunchKernel':211,'cudaStreamSynchronize':131,
    'cudaMemsetAsync':51,'cudaMemcpyAsync':41} # fixed API22 runtime CBID header
SOURCE_FILES=('scripts/coe_cupti_controlled.py','scripts/coe_cupti_controlled.cu',
    'scripts/gate8_qualification_token.cu','analysis/cupti_timeline.py',
    'exposedpath_v141/submit_effect_bridge.py','exposedpath_v141/cupti_driver_queries.py',
    'scripts/analyze_completion_operation_candidate.py','exposedpath/cupti_timeline.py')


def require(ok,reason):
    if not ok:raise ValueError('COE_CONTROLLED_'+reason)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    with Path(path).open('x',encoding='utf8') as f:json.dump(value,f,indent=2)


def bind_sources(index):
    """Explicit checkout binding under -I/-S, after byte verification only."""
    require(type(index) is dict and set(index)==set(SOURCE_FILES),'SOURCE_INDEX')
    for n in SOURCE_FILES:
        path=ROOT/n
        require(path.is_file() and sha(path)==index[n],'SOURCE_HASH:'+n)
        for part in (path,*path.parents):
            require(not part.is_symlink() and not getattr(part.lstat(),'st_file_attributes',0)&0x400,'REPARSE')
            if part==ROOT:break
    sys.path.insert(0,str(ROOT)) if str(ROOT) not in sys.path else None
    import importlib
    for n in ('analysis','exposedpath','exposedpath_v141','analysis.cupti_timeline','exposedpath.cupti_timeline',
        'exposedpath_v141.submit_effect_bridge','exposedpath_v141.cupti_driver_queries'):
        m=importlib.import_module(n);expected=ROOT/Path(*n.split('.'))
        if n in ('analysis','exposedpath','exposedpath_v141'):
            require([Path(p).resolve() for p in getattr(m,'__path__',[])]==[expected.resolve()],'MODULE_ORIGIN:'+n)
        else:require(Path(m.__file__).resolve()==expected.with_suffix('.py').resolve(),'MODULE_ORIGIN:'+n)
    return dict(source_sha256=index,vendor_library_loaded=False)


def labels(run):
    require(isinstance(run,str) and run and run.isascii() and all(c.isalnum() or c in '_-' for c in run),'RUN_ID')
    return dict(drain_label='EXPOSEDPATH_DRAIN_V1:'+json.dumps(dict(identity=dict(run_id=run))),
        request_label='EXPOSEDPATH_BOUNDARY_V1:'+json.dumps(dict(identity=dict(run_id=run),point='request')),
        helper_label='EXPOSEDPATH_JSON_V1:'+json.dumps(dict(run_id=run,kind='controlled_completion')),
        token_label='EXPOSEDPATH_BOUNDARY_V1:'+json.dumps(dict(identity=dict(run_id=run),point='host_token')))


def exercise(lib,session,run,pid,tid,side_path,*,cpu_double=False):
    plan=json.loads(PLAN.read_text(encoding='utf8'));lab=labels(run)
    side=dict(schema_version='coe-cupti-controlled-side/0.1.0',construction=plan['construction'],
        plan_sha256=sha(PLAN),mode='CPU_EXECUTION_DOUBLE' if cpu_double else 'TARGET_CUPTI_UNQUALIFIED',
        status='BLOCKED',run_id=run,session_id=run,pid=pid,tid=tid,labels=lab,calls=[],actual_token_ids=[])
    def call(step,name,*args,custom=None,read=False):
        label=custom or 'COE-REF:'+run+':'+step
        session.mark(1,label)
        try:value=getattr(lib,name)(*args)
        finally:session.mark(2,'')
        side['calls'].append(dict(step=step,function=name,args=list(args),return_code=None if read else value,
                                  read_value=value if read else None,label=label))
        if not read:require(type(value) is int and value==0,'CUDA_CALL:'+step+':'+str(value))
        return value
    try:
        call('drain','ep_prepare',custom=lab['drain_label'])
        session.mark(0,lab['request_label'])
        call('early_kernel','ep_submit',17)
        call('early_wait','ep_wait') # Forces the first member complete before copy.
        call('positive_memset','ep_memset',4,0)
        call('late_kernel','ep_submit',23)
        call('zero_memset','ep_memset',0,123)
        session.mark(1,lab['helper_label'])
        try:
            call('copy','ep_copy');call('paired_sync','ep_wait')
            value=call('host_read','ep_read',read=True)
            require(value==23,'HOST_TOKEN');side['actual_token_ids']=[value]
            session.mark(0,lab['token_label'])
        finally:session.mark(2,'')
        call('future_kernel','ep_submit',29);call('future_wait','ep_wait')
        side['status']='CONSTRUCTION_COMPLETE_PENDING_REVIEW'
        return side
    finally:write(side_path,side)


def independent_intersection(window,intervals):
    """Independent event-count sweep; never imports S or candidate interval math."""
    a,b=window;require(type(a) is int and type(b) is int and a<=b,'REFERENCE_TIME')
    events={a:0,b:0}
    for lo,hi in intervals:
        require(type(lo) is int and type(hi) is int and lo<=hi,'REFERENCE_TIME')
        lo=max(lo,a);hi=min(hi,b)
        if lo<hi:events[lo]=events.get(lo,0)+1;events[hi]=events.get(hi,0)-1
    count=0;total=0;previous=a
    for point in sorted(events):
        if count:total+=point-previous
        count+=events[point];previous=point
    require(count==0,'REFERENCE_UNCLOSED');return total


def independent_reference(raw,side):
    """Construction picks logical steps; typed Raw joins only fill record IDs/time."""
    from analysis.cupti_timeline import marker_ranges # codec only, not set recovery
    p=json.loads(PLAN.read_text(encoding='utf8'))
    require(side['schema_version']=='coe-cupti-controlled-side/0.1.0' and side['plan_sha256']==sha(PLAN)
        and side['construction']==p['construction'] and side['status']=='CONSTRUCTION_COMPLETE_PENDING_REVIEW','SIDE')
    require(side['session_id']==raw['session_id'] and side['pid']==raw['pid'] and raw['clock']=='CUPTI_TIMESTAMP_NS','IDENTITY')
    require([v['step'] for v in side['calls']]==p['steps'] and side['actual_token_ids']==[23],'SIDE_ORDER_TOKEN')
    lab=labels(side['run_id']);require(side['labels']==lab and side['session_id']==side['run_id'],'SIDE_LABEL_IDENTITY')
    expected=[('ep_prepare',[]),('ep_submit',[17]),('ep_wait',[]),('ep_memset',[4,0]),
        ('ep_submit',[23]),('ep_memset',[0,123]),('ep_copy',[]),('ep_wait',[]),
        ('ep_read',[]),('ep_submit',[29]),('ep_wait',[])]
    require([(v['function'],v['args']) for v in side['calls']]==expected,'SIDE_ARGUMENTS')
    require(all(v['label']==(lab['drain_label'] if v['step']=='drain' else
        'COE-REF:'+side['run_id']+':'+v['step']) for v in side['calls']),'SIDE_LABEL_IDENTITY')
    require(all(v['return_code']==0 for v in side['calls'] if v['step']!='host_read') and
        side['calls'][8]['read_value']==23,'SIDE_RETURN')
    def one(rows,reason):
        rows=list(rows);require(len(rows)==1,reason);return rows[0]
    ranges=marker_ranges(raw['markers'])['ranges'];calls={c['id']:c for c in raw['callbacks']}
    require(len(calls)==len(raw['callbacks']),'CALL_DUPLICATE')
    for c in calls.values():
        require(c['closed'] is True and c['pid']==side['pid'],'CALL_CLOSED')
    chosen={};apis={};effects={}
    names=dict(drain='cudaDeviceSynchronize',early_kernel='cudaLaunchKernel',early_wait='cudaStreamSynchronize',
        positive_memset='cudaMemsetAsync',late_kernel='cudaLaunchKernel',zero_memset='cudaMemsetAsync',
        copy='cudaMemcpyAsync',paired_sync='cudaStreamSynchronize',future_kernel='cudaLaunchKernel',future_wait='cudaStreamSynchronize')
    def base(name):
        import re
        return re.sub(r'_v\d+$','',name)
    for row in side['calls']:
        step=row['step']
        if step=='host_read':continue
        ran=one((r for r in ranges if r['label']==row['label'] and r['tid']==side['tid']),'RANGE:'+step)
        cb=one((c for c in calls.values() if c['domain']=='RUNTIME' and c['tid']==side['tid'] and
            ran['start']<=c['start']<=c['end']<=ran['end']),'CALL:'+step)
        require(base(cb['name'])==names[step] and cb['cbid']==RUNTIME_CBIDS[names[step]] and
            type(cb['correlation']) is int and cb['correlation']>0 and
            cb['return_code']==0 and not cb['ptsz'],'CALL_IDENTITY:'+step)
        api=one((r for r in raw['records'] if r['kind']=='API' and r['domain']=='RUNTIME' and
            (r['pid'],r['tid'],r['correlation'],r['cbid'])==(cb['pid'],cb['tid'],cb['correlation'],cb['cbid'])),'API:'+step)
        require(api['return_code']==0 and ran['start']<=api['start']<=api['end']<=ran['end'],'API_RETURN_SCOPE')
        chosen[step]=cb;apis[step]=api
    require(all(apis[a]['end']<=apis[b]['start'] for a,b in zip(names,list(names)[1:])),'ORDER')
    def root(c):
        seen=set()
        while c.get('parent_id') is not None:
            require(c['id'] not in seen and c['parent_id'] in calls,'PARENT');seen.add(c['id'])
            parent=calls[c['parent_id']]
            require(parent['tid']==c['tid'] and parent['enter_seq']<c['enter_seq']<c['exit_seq']<parent['exit_seq']
                and parent['start']<=c['start']<=c['end']<=parent['end'],'PARENT');c=parent
        return c
    prior={c['id'] for c in calls.values() if c['correlation']==0 and c['end']<=apis['drain']['end']}
    while True:
        more={c['id'] for c in calls.values() if c.get('parent_id') in prior and c['end']<=apis['drain']['end']}
        if more<=prior:break
        prior.update(more)
    active=[c for c in calls.values() if c['id'] not in prior]
    keyed={(c['domain'],c['pid'],c['correlation']):c for c in active}
    require(len(keyed)==len(active),'CORRELATION_DUPLICATE')
    for step in ('early_kernel','positive_memset','late_kernel','zero_memset','copy','future_kernel'):
        cb=chosen[step];found=[]
        for e in raw['records']:
            if e['kind'] not in ('KERNEL','MEMSET','MEMCPY'):continue
            child=keyed.get((e.get('domain'),e.get('pid'),e.get('correlation')))
            direct=e['kind']=='MEMCPY' and e.get('pid')==cb['pid'] and e.get('runtime_correlation',0)==cb['correlation']
            match=child is not None and root(child)['id']==cb['id']
            if direct:require(child is None or match,'COPY_PARENT_CONFLICT')
            if match or direct:found.append(e)
        require(len(found)==(0 if step=='zero_memset' else 1),'EFFECT:'+step)
        if found:
            e=found[0];require((e['pid'],e['device'],e['context'],e['stream'])==
                (cb['pid'],cb['device'],cb['context'],cb['stream']),'EFFECT_SCOPE')
            effects[step]=e
    scope=chosen['copy']
    require(all(c['context']==scope['context'] and c['stream']==scope['stream'] and
        c.get('binding_status')==0 and c['params']['native_stream']==0 for k,c in chosen.items() if k!='drain'),'SCOPE_BINDING')
    for step,count,value in [('positive_memset',4,0),('zero_memset',0,123)]:
        require(chosen[step]['params']['count']==count and chosen[step]['params']['value']==value,'PAYLOAD')
    require(effects['positive_memset']['kind']=='MEMSET' and effects['positive_memset']['bytes']==4
        and effects['positive_memset']['value']==0,'PAYLOAD')
    require(effects['copy']['kind']=='MEMCPY' and effects['copy']['bytes']==4 and effects['copy']['copy_kind']==2,'D2H')
    members=[effects[k] for k in p['necessary_steps']];terminal=effects[p['terminal_step']]
    require(all(e['kind']=='KERNEL' for k,e in effects.items() if 'kernel' in k),'KERNEL_KIND')
    require(effects['early_kernel']['end']<=apis['early_wait']['end']<=apis['copy']['start'],'EARLY_COMPLETION')
    require(all(e['end']<=terminal['end']<=apis['paired_sync']['end'] for e in members),'TERMINAL')
    host=one((r for r in ranges if r['label']==side['calls'][8]['label'] and r['tid']==side['tid']),'HOST_READ_RANGE')
    point=one((r for r in marker_ranges(raw['markers'])['points'] if r['label']==lab['token_label'] and
        r['tid']==side['tid']),'TOKEN_POINT')
    require(apis['paired_sync']['end']<=host['start']<=host['end']<=point['time'],'HOST_READ_ORDER')
    require(point['time']<apis['future_kernel']['start'],'FUTURE_ORDER')
    intervals=[[e['start'],e['end']] for e in members]
    window=[apis['copy']['start'],apis['paired_sync']['end']];sync=[apis['paired_sync']['start'],apis['paired_sync']['end']]
    q=independent_intersection(window,intervals)
    return dict(members=[e['id'] for e in members],terminal=terminal['id'],logical_zero_call_ids=[chosen['zero_memset']['id']],
        closed_initialization_callback_ids=sorted(prior),
        excluded_ids=[effects['future_kernel']['id']],window=window,sync=sync,raw_intervals=intervals,
        expected_coe_ns=q,expected_sync_ns=independent_intersection(sync,intervals),wall_ns=window[1]-window[0],
        complement_ns=window[1]-window[0]-q,expected_source='PREDECLARED_CONSTRUCTION_PLUS_RAW_ENDPOINT_SWEEP')


def review(capture,side_path,output):
    a=Path(capture);b=Path(side_path);out=Path(output)
    require(not out.exists() and not a.resolve().is_relative_to(out.resolve()) and
        not b.resolve().is_relative_to(out.resolve()),'NEW_OUTPUT')
    originals=[a.read_bytes(),b.read_bytes()];raw,side=map(json.loads,originals)
    ref=independent_reference(raw,side) # expected is fixed BEFORE calling S
    from analysis.cupti_timeline import select_scope,analyze_files
    producer=dict(session_id=side['session_id'],pid=side['pid'],tid=side['tid'],run_id=side['run_id'],
        actual_token_ids=side['actual_token_ids'],**side['labels'])
    scope=select_scope(raw,producer,timing_policy=TIMING,driver_query_policy=QUERIES)
    out.mkdir();write(out/'reference.json',ref);write(out/'scope.json',scope)
    result=analyze_files(a,out/'scope.json',out/'consumer',timing_policy=TIMING,driver_query_policy=QUERIES)['result']
    require(result['members']==ref['members'] and result['terminal']==ref['terminal'] and
        result['logical_zero_call_ids']==ref['logical_zero_call_ids'],'MEMBER_OR_TERMINAL_MISMATCH')
    require(result['coe_ns']==ref['expected_coe_ns'] and result['sync_intersection_ns']==ref['expected_sync_ns']
        and result['operation_wall_ns']==ref['wall_ns'],'ARITHMETIC_MISMATCH')
    require([a.read_bytes(),b.read_bytes()]==originals,'SOURCE_CHANGED')
    r=dict(status='CONTROLLED_REFERENCE_MATCH_PENDING_REVIEW',source=raw['source'],mode=side['mode'],
        inputs=dict(capture_sha256=sha(a),side_sha256=sha(b),plan_sha256=sha(PLAN)),reference=ref,
        qualification='NOT_GRANTED_BY_THIS_REVIEW',formal_eligible=False)
    write(out/'review.json',r);return r


def capture_program(lib,session_factory,config,output,pid,tid,*,cpu_double=False):
    """Existing session owns initialization/resources; all setup precedes drain."""
    import uuid
    out=Path(output)
    with session_factory(config['session'],out/'timeline',allow_target_capture=True) as session:
        require(lib.ep_init(0)==0 and lib.ep_stream_handle()==0,'PROGRAM_INIT')
        uid=(ctypes.c_ubyte*16)();pci=ctypes.create_string_buffer(64)
        require(lib.ep_identity(uid,pci,64)==0,'DEVICE_QUERY')
        require('GPU-'+str(uuid.UUID(bytes=bytes(uid)))==config['gpu_uuid'] and
            pci.value.decode('ascii').lower()==config['gpu_pci'].lower(),'GPU_IDENTITY')
        return exercise(lib,session,config['run_id'],pid,tid,out/'side.json',cpu_double=cpu_double)


def run(config_path,output,*,enabled=False):
    require(enabled is True,'EXPLICIT_TARGET_APPROVAL_REQUIRED')
    require(os.name=='nt' and sys.flags.isolated and sys.flags.no_site and list(sys.version_info[:3])==[3,11,16],'TARGET_ENVIRONMENT')
    c=json.loads(Path(config_path).read_text(encoding='utf8'));plan=json.loads(PLAN.read_text(encoding='utf8'))
    require(c['schema_version']=='coe-cupti-controlled-run/0.1.0' and c['plan_sha256']==sha(PLAN)
        and c['budget']==plan['budget'] and c['role']=='Engineering','CONFIG')
    require(c['session']['session_id']==c['run_id'] and c['session']['client_sha256']==CLIENT_SHA
        and c['session']['cupti_sha256']==CUPTI_SHA and c['session']['activity_policy_version']==plan['activity_policy'],'LIBRARY_IDENTITY')
    require(sha(c['program'])==c['program_sha256'] and sha(c['runtime'])==RUNTIME_SHA,'PROGRAM_RUNTIME_HASH')
    bind_sources(c['source_sha256'])
    require(os.environ.get('CUDA_VISIBLE_DEVICES')==c['cuda_visible_devices'] and
        os.environ.get('CUDA_DEVICE_ORDER')=='PCI_BUS_ID','MASK')
    require(not any(n=='torch' or n.startswith('torch.') for n in sys.modules) and
        not any(k.startswith('NSYS_') or k in ('CUDA_INJECTION64_PATH','NVTX_INJECTION64_PATH') for k in os.environ),
        'PROFILER_COEXISTENCE')
    out=Path(output).resolve();require(not out.exists(),'NEW_OUTPUT');out.mkdir(parents=True)
    lib=None;initialized=False;status='BLOCKED';error=None
    try:
        runtime=ctypes.WinDLL(c['runtime'],winmode=0x1100)
        k=ctypes.WinDLL('kernel32',winmode=0x800)
        k.GetModuleFileNameW.argtypes=[ctypes.c_void_p,ctypes.c_wchar_p,ctypes.c_uint32]
        k.GetModuleFileNameW.restype=ctypes.c_uint32
        loaded=ctypes.create_unicode_buffer(32768)
        length=k.GetModuleFileNameW(runtime._handle,loaded,len(loaded))
        require(0<length<len(loaded) and Path(loaded.value).resolve()==Path(c['runtime']).resolve(),'LOADED_RUNTIME')
        lib=ctypes.WinDLL(c['program'],winmode=0x1100)
        signatures={'ep_coe_abi':[],'ep_init':[ctypes.c_int],'ep_identity':[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int],
            'ep_stream_handle':[],'ep_prepare':[],'ep_submit':[ctypes.c_int],'ep_memset':[ctypes.c_size_t,ctypes.c_int],
            'ep_copy':[],'ep_wait':[],'ep_read':[],'ep_close':[]}
        for n,args in signatures.items():
            fn=getattr(lib,n);fn.argtypes=args;fn.restype=ctypes.c_size_t if n=='ep_stream_handle' else ctypes.c_int
        require(lib.ep_coe_abi()==1,'PROGRAM_ABI')
        k.GetCurrentThreadId.restype=ctypes.c_uint32
        from exposedpath.cupti_timeline import CaptureSession
        initialized=True
        capture_program(lib,CaptureSession,c,out,os.getpid(),int(k.GetCurrentThreadId()))
        review(out/'timeline/capture.json',out/'side.json',out/'review')
        status='CONTROLLED_COMPLETE_PENDING_REVIEW'
    except BaseException as exc:error=type(exc).__name__+':'+str(exc)
    finally:
        if initialized:
            try:
                code=lib.ep_close()
                if code!=0:raise ValueError('CLEANUP:'+str(code))
            except BaseException as exc:error=(error+'; ' if error else '')+str(exc);status='BLOCKED'
        try:
            require(sha(c['program'])==c['program_sha256'] and sha(c['runtime'])==RUNTIME_SHA,'POST_IDENTITY')
        except BaseException as exc:error=(error+'; ' if error else '')+str(exc);status='BLOCKED'
        write(out/'receipt.json',dict(status=status,error=error,config_sha256=sha(config_path),
            automatic_retry=False,formal_eligible=False,provider_qualification='NOT_GRANTED'))
    return 0 if error is None else 2


def bounded_run(config_path,output,*,enabled=False):
    """Reuse the existing bounded process helper, no pack/retry/cleanup."""
    require(enabled is True,'EXPLICIT_TARGET_APPROVAL_REQUIRED')
    out=Path(output).resolve();require(not out.exists(),'NEW_OUTPUT');out.mkdir(parents=True)
    spec=importlib.util.spec_from_file_location('_coe_controlled_process',ROOT/'scripts/memset_micro.py')
    tools=importlib.util.module_from_spec(spec);spec.loader.exec_module(tools)
    return tools.command([sys.executable,'-I','-S','-B',str(Path(__file__).resolve()),
        '--config',str(Path(config_path).resolve()),'--output',str(out/'run'),
        '--execute-reviewed-controlled','--controlled-worker'],out,out/'process',timeout=120)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',required=True);p.add_argument('--output',required=True)
    p.add_argument('--execute-reviewed-controlled',action='store_true')
    p.add_argument('--controlled-worker',action='store_true',help=argparse.SUPPRESS);a=p.parse_args()
    if a.controlled_worker:return run(a.config,a.output,enabled=a.execute_reviewed_controlled)
    bounded_run(a.config,a.output,enabled=a.execute_reviewed_controlled);return 0
if __name__=='__main__':raise SystemExit(main())
