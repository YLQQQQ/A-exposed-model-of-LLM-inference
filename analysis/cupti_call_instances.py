"""API22 correlation groups are not invocation IDs. No timestamp-based choice.

The recorder's entry index is the call ID; its per-thread stack is parentage.
The fixed SDK domain/name/CBID and explicit resources select device submitters.
This module grants neither a query classification nor a completion dependency.
"""
from collections import defaultdict
import re

POLICY = 'cupti-api22-call-instance-groups/0.1.0'
DRIVER_EFFECTS = {'KERNEL': ('cuLaunchKernel', 307),
                  'MEMSET': ('cuMemsetD8Async', 216),
                  'MEMCPY': ('cuMemcpyDtoHAsync', 279)}


def need(ok, reason):
    if not ok:
        raise ValueError('CUPTI_INSTANCES_' + reason)


def normal(name):
    return re.sub(r'_v\d+$', '', name)


class CallInstances:
    def __init__(self, rows, pid):
        self.calls = {}; self.groups = defaultdict(list); sequences = set()
        for c in rows:
            need(type(c['id']) is int and c['id'] > 0 and c['id'] not in self.calls, 'CALL_DUPLICATE')
            need(c['domain'] in ('DRIVER', 'RUNTIME') and c['pid'] == pid and
                 type(c['correlation']) is int and c['correlation'] >= 0, 'IDENTITY')
            need(c.get('closed') is True and all(type(c[k]) is int for k in
                 ('start','end','enter_seq','exit_seq','cbid','tid','return_code')) and
                 c['start'] <= c['end'] and c['enter_seq'] < c['exit_seq'], 'CALL_ORDER')
            need(not sequences.intersection((c['enter_seq'],c['exit_seq'])), 'SEQUENCE_DUPLICATE')
            sequences.update((c['enter_seq'],c['exit_seq']))
            self.calls[c['id']] = c
            self.groups[(c['domain'],c['pid'],c['correlation'])].append(c)
        for c in self.calls.values():
            if c.get('parent_id') is not None:
                p=self.calls.get(c['parent_id'])
                need(p is not None and p['pid']==c['pid'] and p['tid']==c['tid'] and
                     p['enter_seq']<c['enter_seq']<c['exit_seq']<p['exit_seq'] and
                     p['start']<=c['start']<=c['end']<=p['end'], 'PARENT')

    def root(self, c):
        while c.get('parent_id') is not None:
            c=self.calls[c['parent_id']]
        return c

    def unique(self, group_key):
        group=self.groups.get(group_key, [])
        need(len(group)<=1, 'GROUP_AMBIGUOUS:'+str(group_key))
        return group[0] if group else None

    def api(self, a):
        # Time is checked by the timing policy only AFTER unique identity.
        candidates=[c for c in self.groups.get((a['domain'],a['pid'],a['correlation']), [])
                    if all(c[k]==a[k] for k in ('cbid','tid','return_code')) and
                    (not a.get('name') or normal(c['name'])==normal(a['name']))]
        need(len(candidates)==1, 'API_AMBIGUOUS:'+str(a['id']))
        return candidates[0]

    def effect(self, e):
        need(e['kind'] in DRIVER_EFFECTS and e['domain']=='DRIVER', 'EFFECT_KIND')
        name, cbid=DRIVER_EFFECTS[e['kind']]
        group=self.groups.get(('DRIVER',e['pid'],e['correlation']), [])
        candidates=[c for c in group if normal(c['name'])==name and c['cbid']==cbid and
                    c['return_code']==0 and c.get('ptsz') is False and
                    all(c[k]==e[k] for k in ('device','context','stream'))]
        direct=None
        if e['kind']=='MEMCPY' and e.get('runtime_correlation',0):
            roots=self.groups.get(('RUNTIME',e['pid'],e['runtime_correlation']), [])
            need(len(roots)==1 and normal(roots[0]['name'])=='cudaMemcpyAsync' and
                 roots[0]['cbid']==41 and roots[0]['return_code']==0, 'COPY_RUNTIME')
            direct=roots[0]
        if not group and direct is not None:
            return None # SDK's explicit runtimeCorrelationId route; no invented child.
        need(len(candidates)==1, 'EFFECT_MAPPING:'+str(e['id']))
        child=candidates[0]
        if direct is not None:
            need(self.root(child)['id']==direct['id'], 'COPY_PARENT_CONFLICT')
        return child

    def inventory(self):
        return [dict(domain=k[0],pid=k[1],correlation=k[2],call_ids=[c['id'] for c in rows])
                for k,rows in sorted(self.groups.items()) if len(rows)>1]
