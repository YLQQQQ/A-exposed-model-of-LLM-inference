"""Prospective common-w3 Pilot pair; shared measurement path, closed budget."""
import json
from pathlib import Path
from jsonschema import Draft202012Validator, ValidationError
from .gate11_pilot import require

VERSION = 'G11-WARMUP3-PAIR/0.1'
SCHEMA = json.loads((Path(__file__).resolve().parents[1]/
    'docs/v1_4_1/contracts/gate11/warmup3_pair_schema_v0_1.json').read_text(encoding='utf-8'))


def schedule(batch_id):
    from .gate11_pilot import schedule as original
    return [dict(row,version=VERSION,warmup_count=3,purpose='COMMON_WARMUP_POLICY_ESTIMATION_ONLY')
            for row in original(batch_id)]


def active(value):
    return isinstance(value,dict) and value.get('version')==VERSION


def validate_binding(value):
    require(isinstance(value,dict),'WARMUP3_PAIR_BINDING')
    try: Draft202012Validator(SCHEMA).validate(value)
    except ValidationError as exc: raise ValueError('PILOT_WARMUP3_PAIR_SCHEMA: '+exc.message) from exc
    require(any(value==r and all(type(value[k]) is type(v) for k,v in r.items())
                for r in schedule(value.get('batch_id'))),'WARMUP3_PAIR_BINDING')
    return value
