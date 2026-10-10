"""Opt-in Gate8 identity producer. No device access or experiment qualification."""
from copy import deepcopy
import json
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError

PROFILE = "G8-OBS-BOUNDARY/0.1.0"
ADAPTER_VERSION = "exposedpath-gate8-adapter/0.2.0"
IDENTITY_FIELDS = (
    "experiment_id", "wmpc_id", "run_id", "run_role", "data_role",
    "pass_id", "attempt_id", "request_id", "repeat_id",
)
PASS_FIELDS = IDENTITY_FIELDS[:-2]
_SCHEMA = json.loads((Path(__file__).resolve().parents[1] / "docs/v1_4_1/contracts/gate8/observation_boundary_schema_v0_1.json").read_text(encoding="utf-8"))


def validate_shape(kind, value):
    """Validate an approved closed schema; cross-record checks are separate."""
    # Explicit stage extension; the frozen Engineering schema remains unchanged.
    # Raw markers carry the actual role, so relabelled old sidecars cannot match.
    def pilot_role(v):
        if isinstance(v,dict):
            return v.get('run_role')=='PILOT' or v.get('data_role')=='Pilot' or any(pilot_role(x) for x in v.values())
        return isinstance(v,list) and any(pilot_role(x) for x in v)
    schema=_SCHEMA
    from . import formal_protocol as formal
    def formal_role(v):
        if isinstance(v,dict): return v.get('run_role')=='FORMAL' or v.get('data_role')=='Formal' or any(formal_role(x) for x in v.values())
        return isinstance(v,list) and any(formal_role(x) for x in v)
    if formal_role(value):
        schema=deepcopy(_SCHEMA)
        references=[]
        for filename in ('formal_envelope_schema_v0_1.json','formal_envelope_schema_v0_1_1.json'):
            definition=json.loads((Path(__file__).resolve().parents[1]/'docs/v1_4_1/contracts'/filename).read_text(encoding='utf-8'))
            ref=deepcopy(definition['$defs']['reference'])
            for name in ('protocol_sha256','approval_sha256'):
                ref['properties'][name]=deepcopy(definition['$defs']['sha256'])
            references.append(ref)
        # Closed compatibility set, not a fallback. Cross-record validation
        # below additionally requires the exact signed binding's reference.
        reference_schema={'oneOf':references}
        identity=schema['$defs']['identity']
        identity['properties'].update(run_role={'const':'FORMAL'},data_role={'const':'Formal'},formal_reference=reference_schema)
        identity['required'].append('formal_reference')
        definition=schema['$defs']['pass_identity']
        definition['properties'].update(run_role={'const':'FORMAL'},data_role={'const':'Formal'},
            schema_version={'const':formal.PASS_VERSION},formal={'type':'object'})
        definition['required'].append('formal')
        entry=schema['$defs']['request_entry']
        for key in ('actual_output_tokens','early_eos'):
            entry['properties'][key]={'anyOf':[deepcopy(entry['properties'][key]),{'type':'null'}]}
    if pilot_role(value):
        from .gate11_pilot import versions
        from .gate11_warmup import active,SCHEMA as warmup_schema
        binding=value.get('pilot') if kind=='pass_identity' else None
        pass_version=versions(binding)[0] if binding is not None else 'exposedpath-pass-identity/0.2.0'
        schema=deepcopy(_SCHEMA)
        for name in ('identity','pass_identity'):
            schema['$defs'][name]['properties']['run_role']={'const':'PILOT'}
            schema['$defs'][name]['properties']['data_role']={'const':'Pilot'}
        definition=schema['$defs']['pass_identity']
        definition['properties']['schema_version']={'const':pass_version}
        definition['properties']['pilot']={'type':'object'}
        definition['required'].append('pilot')
        if active(binding):
            entry=schema['$defs']['request_entry']
            for key in ('actual_output_tokens','early_eos'):
                original=deepcopy(entry['properties'][key])
                entry['properties'][key]={'anyOf':[original,{'type':'null'}]}
            entry['allOf']=[{'if':{'properties':{'request_role':{'const':'warmup'}}},
                'then':deepcopy(warmup_schema['$defs']['warmup_observations']),
                'else':{'properties':{k:_SCHEMA['$defs']['request_entry']['properties'][k]
                                     for k in ('actual_output_tokens','early_eos')}}}]
    try:
        Draft202012Validator({"$defs": schema["$defs"], "$ref": f"#/$defs/{kind}"}).validate(value)
    except ValidationError as exc:
        raise ValueError(f"IDENTITY_CONFLICT: {kind}: {exc.message}") from exc


def validate_pass_identity(value, *, finalized=False):
    validate_shape("pass_identity", value)
    from . import formal_protocol as formal
    if value['run_role']=='FORMAL':
        b=formal.validate_binding(value['formal'])
        if value['run_id']!=b['run_id'] or value['pass_id']!=b['pass_id'] or value['runner_git_commit']!=b['protocol']['execution_commit'] or value['runner_git_dirty'] is not False:
            raise ValueError('FORMAL_LEDGER_BINDING')
        for r in value['requests']:
            if r['identity']['formal_reference']!=formal.reference(b): raise ValueError('FORMAL_NVTX_PROTOCOL_CONFLICT')
    if value['run_role']=='PILOT':
        from .gate11_pilot import validate_binding
        binding=validate_binding(value['pilot'])
        if any(value[k]!=binding[k] for k in ('run_id','pass_id')):
            raise ValueError('PILOT_LEDGER_BINDING')
        from .gate11_warmup import active,request_plan
        if active(binding):
            expected=request_plan(binding)
            actual=[dict(request_id=r['identity']['request_id'],repeat_id=r['identity']['repeat_id'],
                         request_role=r['request_role']) for r in value['requests']]
            if actual!=expected or value['planned_request_ids']!=[r['request_id'] for r in expected]:
                raise ValueError('PILOT_WARMUP_ACTUAL_ORDER_OR_COUNT')
    planned = value["planned_request_ids"]
    requests = value["requests"]
    ids = [r["identity"]["request_id"] for r in requests]
    if not planned or len(set(planned)) != len(planned) or len(set(ids)) != len(ids) or set(ids) != set(planned):
        raise ValueError("IDENTITY_CONFLICT: planned/request IDs must be unique and exact")
    repeats = []
    boundaries = []
    for entry in requests:
        identity = entry["identity"]
        if any(identity[k] != value[k] for k in PASS_FIELDS):
            raise ValueError("IDENTITY_CONFLICT: request/pass identity")
        repeats.append((entry["request_role"], identity["repeat_id"]))
        expected, observed = entry["expected_boundary_ids"], entry["observed_boundary_ids"]
        if len(set(expected)) != len(expected) or len(set(observed)) != len(observed):
            raise ValueError("IDENTITY_CONFLICT: duplicate boundary")
        if not set(observed) <= set(expected):
            raise ValueError("IDENTITY_CONFLICT: unplanned boundary")
        if entry["request_role"] == "measured" and len(expected) != entry["expected_output_tokens"] + 1:
            raise ValueError("IDENTITY_CONFLICT: boundary plan/token count")
        if entry["outcome"] == "COMPLETE":
            from .gate11_warmup import active
            unknown_warmup=entry['request_role']=='warmup' and active(formal.control(value))
            if ((not unknown_warmup and entry["actual_output_tokens"] != entry["expected_output_tokens"])
                    or entry["early_eos"] or entry["reasons"] or observed != expected):
                raise ValueError("IDENTITY_CONFLICT: incomplete COMPLETE request")
        elif not entry["reasons"]:
            raise ValueError("IDENTITY_CONFLICT: failed/excluded request needs reasons")
        boundaries.extend(expected)
    if len(set(repeats)) != len(repeats) or len(set(boundaries)) != len(boundaries):
        raise ValueError("IDENTITY_CONFLICT: duplicate repeat/boundary across requests")
    if finalized and value["pass_id"] == "pass1" and (
        value["raw_artifact_sha256"] is None or value["device_mapping_sha256"] is None
    ):
        raise ValueError("IDENTITY_CONFLICT: pass1 final lineage missing")


def make_gate8_pass_identity(*, requests, **pass_fields):
    """Construct the producer ledger without mutating a shared WMPC manifest.

    This is the pre-export form. The adapter writes a distinct finalized copy
    after Raw/device hashes exist; neither input nor Raw is back-patched.
    """
    pilot=pass_fields.get('pilot')
    from . import formal_protocol as formal
    formal_binding=pass_fields.get('formal')
    if formal_binding is not None:
        formal.validate_binding(formal_binding)
        if pilot is not None: raise ValueError('IDENTITY_CONFLICT: mixed roles')
    if pilot is not None:
        from .gate11_pilot import validate_binding, versions
        validate_binding(pilot)
    roles=dict(run_role='PILOT',data_role='Pilot') if pilot is not None else dict(run_role='ENGINEERING',data_role='Engineering')
    if formal_binding is not None: roles=dict(run_role='FORMAL',data_role='Formal')
    for field, required in roles.items():
        if field in pass_fields and pass_fields[field] != required:
            raise ValueError(f"IDENTITY_CONFLICT: producer {field}")
    result = {
        "schema_version": formal.PASS_VERSION if formal_binding is not None else versions(pilot)[0] if pilot is not None else "exposedpath-pass-identity/0.1.0",
        **deepcopy(pass_fields), **roles,
        "planned_request_ids": [r["request_id"] for r in requests],
        "requests": [], "raw_artifact_sha256": None, "device_mapping_sha256": None,
    }
    for source in requests:
        entry = deepcopy(source)
        identity = {k: result[k] for k in PASS_FIELDS}
        if formal_binding is not None: identity['formal_reference']=formal.reference(formal_binding)
        identity.update(request_id=entry.pop("request_id"), repeat_id=entry.pop("repeat_id"))
        result["requests"].append({"identity": identity, **entry})
    validate_pass_identity(result)
    return result
