"""A category registry, separate from physical synchronization semantics.

Non-submit is not a nonblocking guarantee. The caller must apply synchronization
and ownership priority first. No category is inferred from absence of activity.
"""
from functools import lru_cache
import json
from pathlib import Path
import re
from .sync_semantics import classify_cuda_api

VERSION = 'exposedpath-a-api-registry/0.1.0'
REGISTRY_PATH = Path(__file__).resolve().parents[1]/'docs/v1_4_1/contracts/a_api_registry_v0_1.json'


OPAQUE_VERSION = 'exposedpath-a-api-registry/0.2.0'


@lru_cache(maxsize=2)
def _rules(version=VERSION):
    path=REGISTRY_PATH if version==VERSION else REGISTRY_PATH.with_name('a_api_registry_v0_2.json')
    registry=json.loads(path.read_text(encoding='utf-8'))
    if registry.get('registry_version')!=version or version not in (VERSION,OPAQUE_VERSION):
        raise ValueError('A_API_REGISTRY_VERSION')
    rules=dict(_rules()) if version==OPAQUE_VERSION else {}
    if version==OPAQUE_VERSION and registry.get('inherits_version')!=VERSION:
        raise ValueError('A_API_REGISTRY_BASE_VERSION')
    for rule in registry['rules']:
        if rule['category'] not in ('submit','non_submit') or not rule['basis'] or not rule['source']:
            raise ValueError('A_API_REGISTRY_RULE')
        for name in rule['names']:
            if name in rules: raise ValueError('A_API_REGISTRY_DUPLICATE')
            rules[name]=(rule['category'],rule['id'])
    return rules


@lru_cache(maxsize=256)
def _classify(name,version):
    """Return (category, rule id); physical/unsupported sync never becomes API."""
    if not isinstance(name,str): return (None,None)
    normalized=re.sub(r'_v[1-9][0-9]*$','',name)
    # Unknown/malformed suffixes never gain support through prefix matching.
    sync=classify_cuda_api(name)
    if sync['role'] in ('HOST_BLOCKING_SYNC','UNSUPPORTED'):
        return (None,sync['registry_rule_id'])
    if sync['universe_class']=='DEVICE_DEPENDENCY_EDGE':
        return ('submit',sync['registry_rule_id'])
    if sync['universe_class']=='NON_BLOCKING_QUERY':
        return ('non_submit',sync['registry_rule_id'])
    return _rules(version).get(normalized,(None,None))


def classify_a_api_name(name):
    from .time_representation import opaque_allocation
    return _classify(name,OPAQUE_VERSION if opaque_allocation() else VERSION)
