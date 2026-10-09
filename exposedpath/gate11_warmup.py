"""Closed prospective Pass0 warmup control; not an overhead/qualification test."""
from .gate11_pilot import ORDERS, CONDITIONS, require
import json
from pathlib import Path
from jsonschema import Draft202012Validator,ValidationError

VERSION = 'G11-WARMUP-CONTROL/0.1'
PASS_VERSION = 'exposedpath-pass-identity/0.3.0'
EXECUTION_VERSION = 'exposedpath-pilot-execution/0.2.0'
SCHEMA=json.loads((Path(__file__).resolve().parents[1]/
    'docs/v1_4_1/contracts/gate11/warmup_control_schema_v0_1.json').read_text(encoding='utf-8'))


def schedule(batch_id):
    from .gate11_pilot import schedule as original
    original(batch_id)  # Reuse the closed ID and three-block constraints.
    rows=[]
    for b,order in enumerate(ORDERS,1):
        for j,condition in enumerate(order,1):
            counts=[1,3] if (b+j)%2==0 else [3,1]
            pair=f'{batch_id}-b{b}-{condition}'
            for count in counts:
                rows.append(dict(version=VERSION,batch_id=batch_id,block=b,position=j,
                    condition=condition,variant=CONDITIONS[condition][1],pair_id=pair,
                    run_id=f'{pair}-w{count}-pass0',pass_id='pass0',warmup_count=count,
                    warmup_order=list(counts),purpose='WARMUP_POLICY_ESTIMATION_ONLY',
                    declaration_role='PRE_EXECUTION',formal_eligible=False))
    return rows


def validate_binding(value):
    from .formal_protocol import active as formal_active,validate_binding as formal_validate
    if formal_active(value): return formal_validate(value)
    require(isinstance(value,dict),'WARMUP_BINDING')
    from . import gate11_warmup_pair as pair
    if pair.active(value):
        return pair.validate_binding(value)
    try:Draft202012Validator(SCHEMA).validate(value)
    except ValidationError as exc:raise ValueError('PILOT_WARMUP_SCHEMA: '+exc.message) from exc
    require(any(value==r and all(type(value[k]) is type(v) for k,v in r.items())
                for r in schedule(value.get('batch_id'))),'WARMUP_BINDING')
    return value


def active(value):
    """Shared actual-warmup semantics; both prospective bindings stay closed."""
    from .gate11_warmup_pair import active as pair_active
    from .formal_protocol import active as formal_active
    return (isinstance(value,dict) and value.get('version')==VERSION) or pair_active(value) or formal_active(value)


def request_plan(binding):
    validate_binding(binding)
    return [dict(request_id=f'warmup-{i}',repeat_id=f'warmup-{i}',request_role='warmup')
            for i in range(binding['warmup_count'])]+[
                dict(request_id='request-0',repeat_id='0',request_role='measured')]
