"""Versioned evidence bridge BEFORE S; never guesses an edge from overlap.

This separate Engineering consumer does not modify Nsight Canonical or frozen
S/A/B. Runtime/driver identities stay separate. A zero-payload logical submit
is retained, and is usable only in a proven closed single-FIFO projection.
"""
from collections import defaultdict
import importlib.util
from pathlib import Path
import re
import sys


def _math_source():
    path=Path(__file__).resolve().parents[1]/'scripts/analyze_completion_operation_candidate.py'
    name='_exposedpath_completion_math_v01'
    if name in sys.modules:
        module=sys.modules[name]
        if Path(module.__file__).resolve()!=path:raise ValueError('SUBMIT_EFFECT_MATH_SOURCE_CONFLICT')
        return module
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module
    try:spec.loader.exec_module(module)
    except BaseException:
        del sys.modules[name];raise
    return module


_math=_math_source()
Activity,Api,completion_overlap,recover_suffix=(_math.Activity,_math.Api,_math.completion_overlap,_math.recover_suffix)

VERSION='submit-effect-bridge/0.1.0'
INPUT_VERSION='submit-effect-evidence/0.1.0'
SAMPLED_VERSION='submit-effect-bridge/0.2.0'
SAMPLED_INPUT_VERSION='submit-effect-evidence/0.2.0'
LEGACY_TIMING='LEGACY_API_ENCLOSES_CALLBACK'
SAMPLED_TIMING='cupti-api22-distinct-api-callback-boundaries/0.2.0'
QUERY_VERSION='submit-effect-bridge/0.3.0'
QUERY_INPUT_VERSION='submit-effect-evidence/0.3.0'
SUBMITS={'cudaLaunchKernel':'KERNEL','cudaMemsetAsync':'MEMSET','cudaMemcpyAsync':'MEMCPY'}
DRIVER_SUBMITS={'cuLaunchKernel':'KERNEL','cuMemsetD8Async':'MEMSET','cuMemcpyDtoHAsync':'MEMCPY'}
SUBMITS.update(DRIVER_SUBMITS)


def require(ok,reason):
    if not ok:raise ValueError('SUBMIT_EFFECT_'+reason)


def integer(v):return type(v) is int and v>=0


def normal(name):return re.sub(r'_v\d+$','',name)


def key(r):return r['domain'],r['pid'],r['correlation']


def same_scope(r,s):return all(r[k]==s[k] for k in ('pid','device','context','stream'))


def validate_api_callback(a,c,*,policy=LEGACY_TIMING):
    """Join by SDK identity, not by a presumed instrumentation envelope.

    ActivityAPI.start/end time the API; client callback samples time the
    subscriber body. API22 defines the correlation join, not containment of
    either interval. The new narrow profile requires temporal intersection
    as a consistency check, NOT a dependency or an error/tolerance estimate.
    Both original intervals remain available; only ActivityAPI times enter
    the existing submission/accounting math.
    """
    require(policy in (LEGACY_TIMING,SAMPLED_TIMING),'TIMING_POLICY')
    if policy==LEGACY_TIMING:
        require(c['tid']==a['tid'] and normal(c['name'])==normal(a['name']) and
            a['start']<=c['start']<=c['end']<=a['end'] and a['return_code']==c['return_code'],
            'API_CALLBACK_CONFLICT')
        return None
    require(all(integer(a.get(k)) and a[k]>0 for k in ('start','end')) and a['start']<=a['end'],'API_SCOPE')
    require(all(integer(c.get(k)) and c[k]>0 for k in ('start','end')) and c['start']<=c['end'],'CALL_ORDER')
    require(all(a.get(k)==c.get(k) for k in ('domain','pid','tid','correlation','return_code')) and
        integer(a.get('cbid')) and a['cbid']==c.get('cbid') and
        normal(a['name'])==normal(c['name']),'API_CALLBACK_CONFLICT')
    require(max(a['start'],c['start'])<=min(a['end'],c['end']),'API_CALLBACK_TIME_CONFLICT')
    relation=('EQUAL' if (a['start'],a['end'])==(c['start'],c['end']) else
        'ACTIVITY_INSIDE_CALLBACK' if c['start']<=a['start']<=a['end']<=c['end'] else
        'CALLBACK_INSIDE_ACTIVITY' if a['start']<=c['start']<=c['end']<=a['end'] else
        'OVERLAP_NO_CONTAINMENT')
    return dict(api_id=a['id'],callback_id=c['id'],relation=relation,
        activity_interval_ns=[a['start'],a['end']],callback_sample_interval_ns=[c['start'],c['end']])


def analyze_scope(v):
    require(v.get('schema_version') in (INPUT_VERSION,SAMPLED_INPUT_VERSION,QUERY_INPUT_VERSION),'VERSION')
    query_profile=v['schema_version']==QUERY_INPUT_VERSION
    sampled=v['schema_version']!=INPUT_VERSION
    from .cupti_driver_queries import (VERSION as QUERY_POLICY,query_rule,RULES,NESTED_HELPERS,DRIVER_OPERATIONS,
        RUNTIME_VERSION,RUNTIME_RULES,runtime_query_rule)
    require((query_profile and v.get('driver_query_policy')==QUERY_POLICY) or
        (not query_profile and 'driver_query_policy' not in v),'DRIVER_QUERY_POLICY')
    require((query_profile and v.get('runtime_query_policy')==RUNTIME_VERSION) or
        (not query_profile and 'runtime_query_policy' not in v),'RUNTIME_QUERY_POLICY')
    policy=SAMPLED_TIMING if sampled else LEGACY_TIMING
    require((sampled and v.get('api_callback_timing_policy')==policy) or
        (not sampled and 'api_callback_timing_policy' not in v),'TIMING_POLICY')
    require(v.get('source') in ('HOST_ORACLE','HOST_SDK_DOUBLE','TARGET_CUPTI'),'SOURCE')
    s=v['scope'];q=v['quality']
    require(s['session_id']==v['session_id'] and s['pid']==v['pid'] and
            v['clock']=='CUPTI_TIMESTAMP_NS','SESSION')
    require(q.get('closed') is True and q.get('errors')==[] and all(type(q.get(k)) is int and q[k]==0
        for k in ('overflow','dropped','dropped_query_errors')) and
        [s['context'],s['stream']] in q.get('dropped_scopes',[]),'QUALITY')
    require(s.get('ownership')=='CLOSED_SINGLE_FIFO_NO_EVENTS_OR_GRAPHS','OWNERSHIP')
    require(all(integer(s[k]) for k in ('pid','tid','device','context','stream','drain_end','request_start','completion_end'))
        and s['drain_end']<=s['request_start']<=s['completion_end'],'SCOPE')
    require(s.get('completion_proof')=='HOST_TOKEN_READABLE' and s.get('actual_token_ids')
        and all(integer(t) for t in s['actual_token_ids']),'TOKEN_COMPLETION')

    calls={};call_keys={};sequences=set()
    for c in v['callbacks']:
        require(integer(c['id']) and c['id'] not in calls,'CALL_DUPLICATE')
        require(c['domain'] in ('RUNTIME','DRIVER') and integer(c['correlation']) and c['correlation']>0,'DOMAIN')
        require(c['pid']==v['pid'] and all(integer(c[k]) for k in ('start','end','enter_seq','exit_seq'))
            and c['start']<=c['end'] and c['enter_seq']<c['exit_seq'],'CALL_ORDER')
        require(not sequences.intersection((c['enter_seq'],c['exit_seq'])),'SEQUENCE_DUPLICATE')
        sequences.update((c['enter_seq'],c['exit_seq']))
        require(key(c) not in call_keys,'CALL_CORRELATION_DUPLICATE')
        calls[c['id']]=c;call_keys[key(c)]=c
    for c in calls.values():
        parent=c.get('parent_id')
        if parent is not None:
            p=calls.get(parent)
            require(p is not None and p['pid']==c['pid'] and p['tid']==c['tid'] and
                p['enter_seq']<c['enter_seq']<c['exit_seq']<p['exit_seq'] and
                p['start']<=c['start']<=c['end']<=p['end'],'PARENT')

    if sampled:
        # Sequences are acquired under a mutex; validate timestamps only within
        # a thread, not an invented global inter-thread order.
        threads=defaultdict(list)
        for c in calls.values():
            threads[c['tid']].extend(((c['enter_seq'],c['start']),(c['exit_seq'],c['end'])))
        for events in threads.values():
            ordered_events=sorted(events)
            require(all(a[1]<=b[1] for a,b in zip(ordered_events,ordered_events[1:])),'CALL_THREAD_ORDER')
    apis={};api_keys={};runtime=[];timing_counts=defaultdict(int)
    for a in v['apis']:
        require(a['id'] not in apis and key(a) not in api_keys,'API_DUPLICATE')
        require(a['domain'] in ('RUNTIME','DRIVER') and a['pid']==v['pid'] and
                integer(a['start']) and integer(a['end']) and a['start']<=a['end'],'API_SCOPE')
        c=call_keys.get(key(a));require(c is not None,'API_CALLBACK_COVERAGE')
        fact=validate_api_callback(a,c,policy=policy)
        if sampled:timing_counts[fact['relation']]+=1
        apis[a['id']]=a;api_keys[key(a)]=a
        if a['domain']=='RUNTIME':runtime.append(a)
    query_rules={}
    def ancestors(c):
        yield c
        while c.get('parent_id') is not None:
            c=calls[c['parent_id']];yield c
    if query_profile:
        def local_callback(c):
            a=api_keys.get(key(c))
            return ((c['start']<s['completion_end'] and s['request_start']<c['end']) or
                (a is not None and a['start']<s['completion_end'] and s['request_start']<a['end']))
        for c in calls.values():
            if not local_callback(c):continue
            if c['domain']=='RUNTIME':require(c.get('parent_id') is None,'NESTED_RUNTIME_UNSUPPORTED')
            if c['name'] in RULES:
                a=api_keys.get(key(c))
                # Preserve the existing parent-callback bridge when a nested
                # driver API activity is absent; never synthesize its duration.
                # A root call, unlike that child, needs its own API envelope.
                require(a is not None or c.get('parent_id') in calls,'DRIVER_API_COVERAGE')
                query_rules[c['id']]=query_rule(a,c)
            elif c['name'] in RUNTIME_RULES:
                query_rules[c['id']]=runtime_query_rule(api_keys.get(key(c)),c)
        # Query semantics must not hide work or physical completion on the
        # same call or any real descendant, even if its interval is short.
        for e in v['effects']:
            c=call_keys.get(key(e))
            if c is not None:require(not any(x['id'] in query_rules for x in ancestors(c)),
                'QUERY_DEVICE_EFFECT:'+str(e['id']))
        for fact in [*v['synchronizations'],*v.get('internal_completions',[])]:
            c=calls.get(fact.get('driver_call_id')) or call_keys.get((fact.get('domain'),v['pid'],fact['correlation']))
            if c is not None:require(not any(x['id'] in query_rules for x in ancestors(c)),
                'QUERY_SYNCHRONIZATION:'+str(fact['id']))
        for c in calls.values():
            if (c['name'],c.get('cbid')) not in DRIVER_OPERATIONS:continue
            if any(x['id'] in query_rules for x in list(ancestors(c))[1:]):
                require(False,('QUERY_SYNCHRONIZATION:' if normal(c['name'])=='cuStreamSynchronize' else
                    'QUERY_DEVICE_SUBMISSION:')+str(c['id']))
        for c in calls.values():
            if c['domain']!='DRIVER' or not local_callback(c):continue
            if c.get('parent_id') is None:require(key(c) in api_keys,'DRIVER_API_COVERAGE')
            if c['id'] in query_rules:continue
            if c.get('parent_id') is None:
                require((c['name'],c['cbid']) in DRIVER_OPERATIONS and normal(c['name']) in DRIVER_SUBMITS,
                    'DRIVER_ROOT_API_UNSUPPORTED:'+str(c['id'])+':'+c['name'])
            else:
                root=list(ancestors(c))[-1]
                require((c['name'],c['cbid']) in DRIVER_OPERATIONS or
                    NESTED_HELPERS.get((c['name'],c['cbid']))==normal(root['name']),
                    'DRIVER_NESTED_API_UNSUPPORTED:'+str(c['id'])+':'+c['name'])
    owners=runtime+[a for a in apis.values() if a['domain']=='DRIVER' and
        call_keys[key(a)].get('parent_id') is None and
        (normal(a['name']) in DRIVER_SUBMITS or call_keys[key(a)]['id'] in query_rules)]
    relevant=[a for a in owners if a['start']<s['completion_end'] and s['request_start']<a['end']]
    for c in calls.values():
        if c['domain']=='RUNTIME' and s['request_start']<=c['start']<s['completion_end']:
            require(key(c) in api_keys,'RUNTIME_API_COVERAGE')
    for a in relevant:
        require(a['tid']==s['tid'] and s['request_start']<=a['start']<=a['end']<=s['completion_end'],'SCOPE')
        if sampled:
            c=call_keys[key(a)]
            require(s['request_start']<=c['start']<=c['end']<=s['completion_end'],'CALLBACK_SCOPE')
        require(type(a['return_code']) is int and a['return_code']==0,'FAILED_API')
    for c in calls.values():
        if s['request_start']<=c['start']<s['completion_end']:
            require(type(c['return_code']) is int and c['return_code']==0,'FAILED_API')
            if c['domain']=='DRIVER':require(c['id'] in query_rules or c.get('parent_id') in calls or
                (c.get('parent_id') is None and normal(c['name']) in DRIVER_SUBMITS and key(c) in api_keys),'PARENT')

    copy=apis.get(s['copy_api']);sync=apis.get(s['sync_api'])
    require(copy in relevant and sync in relevant and normal(copy['name'])=='cudaMemcpyAsync'
        and normal(sync['name'])=='cudaStreamSynchronize' and copy['end']<=sync['start'],'COMPLETION_PAIR')
    cc=call_keys[key(copy)];sc=call_keys[key(sync)]
    require(same_scope(cc,s) and same_scope(sc,s),'SCOPE')
    require(isinstance(cc['params'],dict) and cc['params'].get('copy_kind')==2 and
        integer(cc['params'].get('count')) and cc['params']['count']>0,'D2H_PARAMETERS')

    def logical_runtime(c):
        seen=set()
        while c['domain']!='RUNTIME':
            if c.get('parent_id') is None:
                require(normal(c['name']) in DRIVER_SUBMITS and key(c) in api_keys,'PARENT')
                return c
            require(c['id'] not in seen and c.get('parent_id') in calls,'PARENT')
            seen.add(c['id']);c=calls[c['parent_id']]
        return c

    mapped=defaultdict(list);effect_to_runtime={};effects={};prior=[];effect_edges=[]
    for e in v['effects']:
        require(e['id'] not in effects and e.get('graph')==0 and integer(e['start'])
            and integer(e['end']) and e['start']<=e['end'],'EFFECT_ID_OR_GRAPH')
        require(e['pid']==v['pid'],'SCOPE')
        require(e['domain']=='DRIVER','EFFECT_BRIDGE')
        effects[e['id']]=e
        if e['end']<=s['drain_end']:
            prior.append(e['id']);continue
        c=call_keys.get(key(e));direct=None
        if e['kind']=='MEMCPY' and e.get('runtime_correlation',0):
            direct=call_keys.get(('RUNTIME',e['pid'],e['runtime_correlation']))
            require(direct is not None and normal(direct['name'])=='cudaMemcpyAsync','COPY_RUNTIME_CORRELATION')
        require(c is not None or direct is not None,'UNASSIGNED_EFFECT')
        if c is not None:
            require(c['domain']=='DRIVER','EFFECT_BRIDGE');root=logical_runtime(c)
            require(c['context']==root['context'],'SCOPE')
            if direct is not None:require(root['id']==direct['id'],'COPY_RUNTIME_CORRELATION')
        else:root=direct
        a=api_keys.get(key(root))
        require(a is not None and normal(a['name']) in SUBMITS,'EFFECT_BRIDGE')
        if a['start']>=s['completion_end']:continue
        require(same_scope(e,s) and same_scope(root,s),'SCOPE')
        require(a['start']<=e['start'] and e['end']<=sync['end'],'COMPLETION')
        require(e['kind']==SUBMITS[normal(a['name'])],'EFFECT_KIND')
        require(s['request_start']<=a['start']<=a['end']<=sync['start'],'SUBMISSION_BOUNDARY')
        mapped[a['id']].append(e)
        if root['domain']=='RUNTIME':effect_to_runtime[e['id']]=a['id']
        effect_edges.append(dict(effect_id=e['id'],submit_api_id=a['id'],submit_domain=root['domain'],
            runtime_call_id=root['id'] if root['domain']=='RUNTIME' else None,
            runtime_api_id=a['id'] if root['domain']=='RUNTIME' else None,
            driver_call_id=c['id'] if c else None,
            raw_correlation_domain=e['domain'],raw_correlation=e['correlation'],
            bridge='MEMCPY_RUNTIME_CORRELATION' if direct is not None else
                'DIRECT_DRIVER_API' if root['domain']=='DRIVER' else 'REAL_CALLBACK_PARENT_CHAIN'))
    for es in mapped.values():es.sort(key=lambda e:(e['start'],e['end'],e['id']))

    logical_zero=[];selected=[]
    for a in sorted(relevant,key=lambda a:(a['start'],a['end'])):
        n=normal(a['name'])
        if n=='cudaStreamSynchronize':continue
        if call_keys[key(a)]['id'] in query_rules:continue
        if n not in SUBMITS:
            # Do not silently call an unknown API non-submit.
            from .a_api_classification import classify_a_api_name
            require(classify_a_api_name(n)[0]=='non_submit','API_SEMANTICS:'+n)
            continue
        require(a['end']<=sync['start'],'SUBMISSION_BOUNDARY')
        c=call_keys[key(a)];require(same_scope(c,s),'SCOPE')
        if query_profile:
            require(isinstance(c.get('params'),dict) and integer(c['params'].get('native_stream')),'PARAMETERS')
        es=mapped[a['id']]
        if SUBMITS[n] in ('MEMSET','MEMCPY'):
            p=c.get('params');require(isinstance(p,dict) and integer(p.get('count'))
                and integer(p.get('native_stream')),'PARAMETERS')
            if p['count']==0:
                require(not es,'ZERO_EFFECT_CONFLICT')
                require(a['end']<=copy['start'],'ZERO_FRONTIER')
                logical_zero.append(c['id']);continue
            require(es,'POSITIVE_EFFECT_MISSING')
            require(all(integer(e.get('bytes')) for e in es) and sum(e['bytes'] for e in es)==p['count'],'PAYLOAD')
            if SUBMITS[n]=='MEMSET':
                require(type(p.get('value')) is int and all(e.get('value')==(p['value']&255) for e in es),'PAYLOAD')
            else:require(all(e.get('copy_kind')==p['copy_kind'] for e in es),'PAYLOAD')
        else:require(es,'POSITIVE_EFFECT_MISSING')
        selected.append(a)

    sync_rows=[]
    for y in v['synchronizations']:
        c=call_keys.get((y['domain'],v['pid'],y['correlation']))
        require(c is not None,'SYNC_BRIDGE')
        root=logical_runtime(c)
        if root['id']==sc['id']:sync_rows.append(y)
    require(len(sync_rows)==1,'SYNC_MAPPING')
    y=sync_rows[0]
    require((y['context'],y['stream'])==(s['context'],s['stream']) and
        sync['start']<=y['start']<=y['end']<=sync['end'],'SYNC_SCOPE')
    require(all(e['end']<=y['end'] for es in mapped.values() for e in es),'SYNC_COMPLETION')

    ordered=sorted(selected,key=lambda a:(a['start'],a['end']))
    require(all(a['end']<=b['start'] for a,b in zip(ordered,ordered[1:])),'FIFO_SUBMISSION_ORDER')
    # The explicit bridge creates a *derived* local submit key, never rewrites
    # either Raw correlation domain. Zero logical nodes have no activity row.
    synthetic_keys={a['id']:i+1 for i,a in enumerate(ordered)}
    ai=[Api(a['id'],a['start'],a['end'],synthetic_keys[a['id']],a['tid'],a['return_code']) for a in ordered]
    activities=[Activity(e['id'],e['start'],e['end'],synthetic_keys[a['id']],e['pid'],e['device'],e['context'],e['stream'],e['kind'])
        for a in ordered for e in mapped[a['id']]]
    members,closed,future=recover_suffix(activities,ai,request_start=s['request_start'],drain_end=s['drain_end'],
        sync=(sync['start'],sync['end']),scope=tuple(s[k] for k in ('pid','device','context','stream')),thread=s['tid'])
    require(not closed and not future and members,'SUFFIX')
    direct=mapped[copy['id']];require(len(direct)==1,'D2H_TERMINAL')
    terminal=direct[0];require(terminal['end']==max(a.end for a in members),'TERMINAL')
    require(all(a['start']<=b['start'] and a['end']<=b['start'] for a,b in
        zip([e for a in ordered for e in mapped[a['id']]],[e for a in ordered for e in mapped[a['id']]][1:])),'FIFO_EFFECT_ORDER')
    overlap=completion_overlap((copy['start'],copy['end']),(sync['start'],sync['end']),[(a.start,a.end) for a in members])
    internal=[]
    for fact in v.get('internal_completions',[]):
        d=calls[fact['driver_call_id']];root=logical_runtime(d);a=api_keys[key(root)]
        require(root['id']==fact['runtime_call_id'] and same_scope(d,s) and
            same_scope(root,s) and d['domain']=='DRIVER' and normal(d['name'])=='cuStreamSynchronize' and
            fact['flags']==3 and (fact['context'],fact['stream'])==(s['context'],s['stream']) and
            d['correlation']==fact['correlation'] and d['return_code']==0 and
            d['start']<=fact['start']<=fact['end']<=d['end'],'INTERNAL_SYNC_SCOPE')
        # Submission inside an unfinished outer API is established by the
        # actual child callback sequence, never by its future API return.
        necessary=[]
        for edge in effect_edges:
            submit=apis[edge['submit_api_id']]
            if submit['end']<=d['start']:
                necessary.append(effects[edge['effect_id']]);continue
            if edge['runtime_call_id']==root['id']:
                child=calls.get(edge['driver_call_id'])
                require(child is not None,'INTERNAL_SUBMISSION_BOUNDARY')
                if child['exit_seq']<d['enter_seq']:necessary.append(effects[edge['effect_id']])
                else:require(child['enter_seq']>d['exit_seq'],'INTERNAL_SUBMISSION_BOUNDARY')
        require(all(e['end']<=fact['end'] for e in necessary),'INTERNAL_SYNC_COMPLETION')
        intervals=[(max(e['start'],fact['start']),min(e['end'],fact['end'])) for e in necessary]
        intervals=[(lo,hi) for lo,hi in intervals if lo<hi]
        # FIFO activity intervals have already been verified disjoint above.
        driver_api=api_keys.get(key(d))
        internal.append(dict(source_record_id=fact['id'],runtime_api_id=a['id'],driver_call_id=d['id'],
            necessary_member_ids=[e['id'] for e in necessary],physical_interval_ns=[fact['start'],fact['end']],
            physical_activity_overlap_ns=sum(hi-lo for lo,hi in intervals),
            driver_api_interval_ns=[driver_api['start'],driver_api['end']] if driver_api else None,
            pure_host_blocking_ns=None))
    answer=dict(schema_version=QUERY_VERSION if query_profile else SAMPLED_VERSION if sampled else VERSION,status='VALID_UNDER_DECLARED_SUPPORT_ASSUMPTIONS',
        session_id=v['session_id'],source=v['source'],clock=v['clock'],
        members=[a.key for a in members],closed_prior_ids=prior,terminal=terminal['id'],
        logical_zero_call_ids=logical_zero,zero_projection='EMPTY_FIFO_NODE_PRESERVES_REAL_FIFO_ORDER',
        submit_effects={a['id']:[e['id'] for e in mapped[a['id']]] for a in relevant if normal(a['name']) in SUBMITS},
        effect_to_runtime=effect_to_runtime,effect_edges=effect_edges,synthetic_activities=[],
        internal_synchronizations=internal,
        runtime_api_intervals=[(a['start'],a['end']) for a in sorted(relevant,key=lambda a:a['start']) if a['domain']=='RUNTIME'],
        submission_api_sources=[dict(api_id=a['id'],domain=a['domain'],start=a['start'],end=a['end']) for a in ordered],
        coe_ns=overlap['candidate_ns'],sync_intersection_ns=overlap['original_sync_ns'],
        operation_wall_ns=overlap['wall_ns'],activity_union=overlap['activity_union'],
        production_A_B_changed=False,pure_host_blocking=None,provider_qualification='NOT_GRANTED_BY_THIS_CONSUMER',
        formal_eligible=False)
    if sampled:answer.update(api_callback_timing_policy=policy,api_callback_relation_counts=dict(timing_counts),
        activity_timestamp_source='CUpti_ActivityAPI.start/end',
        callback_timestamp_source='cuptiGetTimestamp sampled inside subscriber ENTER/EXIT')
    if query_profile:
        rows=[]
        for a in sorted(relevant,key=lambda a:(a['start'],a['end'])):
            c=call_keys[key(a)]
            rows.append(dict(api_id=a['id'],callback_id=c['id'],domain=a['domain'],name=a['name'],
                start=a['start'],end=a['end'],return_code=a['return_code']))
        # Exactly one outermost API owns each nested interval; driver children
        # remain observable provenance, not another addition to API wall cost.
        facts=[]
        for cid,rule in query_rules.items():
            c=calls[cid];a=api_keys.get(key(c));root=list(ancestors(c))[-1];owner=api_keys.get(key(root))
            require(owner is not None,'DRIVER_API_COVERAGE')
            facts.append(dict(api_id=a['id'] if a else None,callback_id=cid,pid=c['pid'],tid=c['tid'],
                domain=c['domain'],correlation=c['correlation'],cbid=c['cbid'],name=c['name'],
                parent_id=c.get('parent_id'),api_interval_ns=[a['start'],a['end']] if a else None,
                callback_sample_interval_ns=[c['start'],c['end']],return_code=c['return_code'],
                budget_owner_api_id=owner['id'],rule_id=rule['domain']+'/'+rule['name']))
        merged=[]
        for row in rows:
            if merged and row['start']<=merged[-1][1]:merged[-1][1]=max(merged[-1][1],row['end'])
            else:merged.append([row['start'],row['end']])
        answer.update(driver_query_policy=QUERY_POLICY,runtime_query_policy=RUNTIME_VERSION,
            driver_queries=[r for r in facts if r['domain']=='DRIVER'],
            runtime_queries=[r for r in facts if r['domain']=='RUNTIME'],
            query_rule_sources={r['domain']+'/'+r['name']:r for r in query_rules.values()},
            accounting_api_sources=rows,accounting_api_union_ns=sum(hi-lo for lo,hi in merged),
            accounting_interpretation='OBSERVED_API_WALL_NOT_PURE_CPU; SYNC_NOT_RECLASSIFIED',
            independent_driver_submit_api_ids=[a['id'] for a in ordered if a['domain']=='DRIVER'])
    return answer
