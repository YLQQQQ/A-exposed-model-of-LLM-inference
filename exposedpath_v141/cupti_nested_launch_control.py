"""Finite API22 controlled-launch prefix, not generic no-effect query support.

No library/module/function handle chain is inferred. Loading can do resource
work; its unseparated cost stays within the actual outer API envelope. Context
postconditions are checked at recorded boundaries and at the real next launch.
This creates neither activity rows nor necessary members nor sync guarantees.
"""
from analysis.cupti_call_instances import CallInstances

POLICY='cupti-api22-controlled-nested-launch/0.1.0'
BASE='https://docs.nvidia.com/cuda/archive/12.4.1/cuda-driver-api/'
CBID_HEADER_SHA256='7cf5ee908f7254a188a8a6df3886b1d4bde84061b5cd57c0fcb0b7a6d40dd4f3'
RULES={
    'cuLibraryLoadData':(678,'LIBRARY_LOAD','group__CUDA__LIBRARY.html'),
    'cuCtxPushCurrent_v2':(323,'CONTEXT_PUSH','group__CUDA__CTX.html'),
    'cuLibraryGetModule':(682,'MODULE_HANDLE','group__CUDA__LIBRARY.html'),
    'cuCtxPopCurrent_v2':(324,'CONTEXT_POP','group__CUDA__CTX.html'),
    'cuModuleGetFunction':(23,'FUNCTION_HANDLE','group__CUDA__MODULE.html'),
}
CHILD_PATTERN=tuple((n,r[0]) for n,r in RULES.items())+(('cuLaunchKernel',307),)


def need(ok,reason):
    if not ok:raise ValueError('NESTED_LAUNCH_'+reason)


def validate_nested_launch_controls(v):
    need(v.get('schema_version')=='submit-effect-evidence/0.3.2' and
         v.get('nested_launch_policy')==POLICY,'POLICY')
    s=v['scope'];calls={c['id']:c for c in v['callbacks']}
    need(len(calls)==len(v['callbacks']),'IDENTITY')
    local=lambda c:c['start']<s['completion_end'] and s['request_start']<c['end']
    controls=[c for c in calls.values() if local(c) and
              (c['name'] in RULES or c['cbid'] in {r[0] for r in RULES.values()})]
    roots={}
    for c in controls:
        need(c['name'] in RULES and c['domain']=='DRIVER' and
             c['cbid']==RULES[c['name']][0] and c.get('ptsz') is False,'IDENTITY')
        need(type(c['return_code']) is int and c['return_code']==0,'RETURN')
        p=calls.get(c.get('parent_id'))
        need(p is not None and p['domain']=='RUNTIME' and p['name']=='cudaLaunchKernel' and
             p['cbid']==211 and p.get('parent_id') is None and p.get('ptsz') is False and
             c['pid']==p['pid']==v['pid'] and c['tid']==p['tid']==s['tid'] and
             p['enter_seq']<c['enter_seq']<c['exit_seq']<p['exit_seq'] and
             p['start']<=c['start']<=c['end']<=p['end'],'PARENT')
        need(p['closed'] is True and p['return_code']==0,'RETURN')
        roots[p['id']]=p
    ix=CallInstances(v['callbacks'],v['pid'])
    facts=[]
    for p in roots.values():
        children=sorted((c for c in calls.values() if c.get('parent_id')==p['id']),key=lambda c:c['enter_seq'])
        need(tuple((c['name'],c['cbid']) for c in children)==CHILD_PATTERN,'CHILD_PATTERN')
        need(all(a['exit_seq']<b['enter_seq'] and a['end']<=b['start'] for a,b in zip(children,children[1:])),
             'CHILD_PATTERN')
        need(not any(c.get('parent_id') in {x['id'] for x in children} for c in calls.values()),'CHILD_PATTERN')
        need(s['request_start']<=p['start']<=p['end']<=s['completion_end'],'PARENT')
        native=p.get('native_context')
        need(type(native) is int and native>0 and type(s['context']) is int and s['context']>0,'CONTEXT')
        # Helpers have no bound stream/device fields. Do not use their default
        # stream=0 or device=0 as resource evidence.
        for c in [p,*children]:
            need(c.get('context')==c.get('exit_context')==s['context'] and
                 c.get('native_context')==c.get('exit_native_context')==native,'CONTEXT')
        launch=children[-1]
        need(all(c.get('binding_status')==0 and c.get('device')==s['device'] and
                 c.get('stream')==s['stream'] and isinstance(c.get('params'),dict) and
                 c['params'].get('native_stream')==0 for c in (p,launch)),'RESOURCE')
        context=[r for r in v.get('resource_records',[]) if r['kind']=='CONTEXT' and r['context']==s['context']]
        stream=[r for r in v.get('resource_records',[]) if r['kind']=='STREAM' and
                (r['context'],r['stream'])==(s['context'],s['stream'])]
        need(context and all(r['device']==s['device'] and r['flags']==0 for r in context) and
             (any(r['stream']==s['stream'] for r in context) or bool(stream)),'RESOURCE')
        owner_api=[a for a in v['apis'] if a.get('callback_id')==p['id']]
        need(len(owner_api)==1,'PARENT')
        owner=ix.api(owner_api[0])
        need(owner['id']==p['id'],'PARENT')
        effects=[e for e in v['effects'] if e.get('submit_callback_id') in {c['id'] for c in children}]
        need(len(effects)==1 and effects[0]['kind']=='KERNEL' and
             effects[0].get('submit_callback_id')==launch['id'] and
             ix.effect(effects[0])['id']==launch['id'],'LAUNCH_EFFECT_COVERAGE')
        need(all(effects[0][k]==s[k] for k in ('pid','device','context','stream')),'RESOURCE')
        ids={c['id'] for c in children}|{p['id']}
        for y in [*v['synchronizations'],*v.get('internal_completions',[])]:
            need(y.get('callback_id') not in ids and y.get('driver_call_id') not in ids and
                 not ids.intersection(y.get('callback_bridge_ids',[])),'COMPLETION')
        for c in children[:-1]:
            api=[a for a in v['apis'] if a.get('callback_id')==c['id']]
            need(len(api)<=1,'IDENTITY')
            if api:need(ix.api(api[0])['id']==c['id'],'IDENTITY')
            facts.append(dict(policy_version=POLICY,callback_id=c['id'],domain=c['domain'],
                name=c['name'],cbid=c['cbid'],role=RULES[c['name']][1],parent_id=p['id'],
                pid=c['pid'],tid=c['tid'],correlation=c['correlation'],return_code=c['return_code'],
                callback_interval_ns=[c['start'],c['end']],api_id=api[0]['id'] if api else None,
                api_interval_ns=[api[0]['start'],api[0]['end']] if api else None,
                budget_owner_api_id=owner_api[0]['id'],additive_api_budget_ns=0,
                observed_context_uid=s['context'],observed_native_context=native,
                following_launch_call_id=launch['id'],kernel_effect_id=effects[0]['id'],
                native_stream_from_unbound_helper=None,pure_cpu_cost=False,
                library_module_function_handle_chain='NOT_CAPTURED_NOT_CLAIMED',
                library_loading_mode='NOT_INFERRED',internal_device_cost_ns=None,
                source=BASE+RULES[c['name']][2],cuda_documentation='12.4.1',
                effect_assumption='NO_SYNTHETIC_EFFECT; EXACT_REAL_LAUNCH_AND_RESOURCE_BINDING_ONLY'))
    return facts
