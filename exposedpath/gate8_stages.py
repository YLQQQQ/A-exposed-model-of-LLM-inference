"""Host-call observations, not completion, stream ownership or lifetime proof."""
from copy import deepcopy
import hashlib
import json
import threading

from .gate8_identity import PASS_FIELDS, validate_pass_identity

STAGE_PREFIX = 'EXPOSEDPATH_STAGE_V1:'
STAGE_VERSION = 'exposedpath-stage-ledger/0.1.0'
MARKER_VERSION = 'exposedpath-stage-marker/0.1.0'


def observe_stream(cuda, logical_device):
    """Never initialize CUDA for observation, change streams, query or synchronize."""
    result = dict(status='UNKNOWN', reason=None, logical_device=logical_device,
        current_native_handle=None, default_native_handle=None,
        default_stream_mode='UNKNOWN', lifetime_status='UNKNOWN')
    try:
        if not cuda.is_initialized():
            result['reason'] = 'CUDA_NOT_INITIALIZED'
            return result
        if cuda.current_device() != logical_device:
            result['reason'] = 'CURRENT_DEVICE_CONFLICT'
            return result
        current = cuda.current_stream(logical_device)
        default = cuda.default_stream(logical_device)
        if current.device.index != logical_device or default.device.index != logical_device:
            raise ValueError('stream device conflict')
        handles = (current.cuda_stream, default.cuda_stream)
        if any(type(h) is not int or h < 0 for h in handles):
            raise ValueError('native handle invalid')
        result.update(status='OBSERVED', current_native_handle=handles[0],
                      default_native_handle=handles[1])
    except Exception as exc:
        result['reason'] = 'PROBE_FAILED:' + type(exc).__name__
    return result


class StageRecorder:
    def __init__(self, ledger, logical_device, cuda, clock_ns, *, setup_observed):
        validate_pass_identity(ledger)
        self.ledger, self.logical_device = ledger, logical_device
        self.cuda, self.clock_ns = cuda, clock_ns
        self.value = dict(schema_version=STAGE_VERSION,
            identity={k:ledger[k] for k in PASS_FIELDS}, pid=ledger['pid'],
            producer_source_sha256=ledger['runner_source_sha256'],
            setup_observed=setup_observed, stages=[], measurement_validity='NOT_ASSESSED')

    def observe(self, role, request_identity, operation):
        payload = dict(schema_version=MARKER_VERSION, identity=self.value['identity'],
            pid=self.value['pid'], stage_role=role, request_identity=deepcopy(request_identity),
            logical_device=self.logical_device,
            producer_source_sha256=self.value['producer_source_sha256'],
            scope_semantics='HOST_CALL_ONLY', marker_role='non_sync_marker')
        payload['stage_id'] = hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
        if any(s['payload']['stage_id']==payload['stage_id'] for s in self.value['stages']):
            raise ValueError('STAGE_DUPLICATE')
        emit = self.ledger['pass_id']=='pass1'
        if emit:
            self.cuda.nvtx.range_push(STAGE_PREFIX+json.dumps(payload,sort_keys=True,separators=(',',':')))
        entry = dict(payload=payload,thread_id=threading.get_native_id(),
            host_clock_id='PYTHON_PERF_COUNTER_NS',host_start_ns=self.clock_ns(),
            host_end_ns=None,before=None,after=None,status='FAILED',error=None)
        self.value['stages'].append(entry)
        try:
            entry['before']=observe_stream(self.cuda,self.logical_device)
            result = operation()
            entry['status']='COMPLETE'
            return result
        except BaseException as exc:
            entry['error']=type(exc).__name__
            raise
        finally:
            entry['after']=observe_stream(self.cuda,self.logical_device)
            entry['host_end_ns']=self.clock_ns()
            if emit:
                self.cuda.nvtx.range_pop()
            if entry['host_end_ns'] < entry['host_start_ns']:
                entry.update(status='FAILED',error='STAGE_HOST_TIME_REVERSAL')
                raise ValueError('STAGE_HOST_TIME_REVERSAL')


def validate_stage_ledger(value, ledger):
    """Reject mismatches; host completion never confers scientific ownership."""
    validate_pass_identity(ledger)
    def require(ok):
        if not ok:
            raise ValueError('STAGE_IDENTITY_OR_SHAPE_CONFLICT')
    require(set(value)=={'schema_version','identity','pid','producer_source_sha256',
                         'setup_observed','stages','measurement_validity'})
    require(value['schema_version']==STAGE_VERSION and value['measurement_validity']=='NOT_ASSESSED'
            and value['identity']=={k:ledger[k] for k in PASS_FIELDS}
            and value['pid']==ledger['pid'] and type(value['pid']) is int
            and value['producer_source_sha256']==ledger['runner_source_sha256']
            and type(value['setup_observed']) is bool and isinstance(value['stages'],list))
    expected = ([('setup',None)] if value['setup_observed'] else []) + [
        (r['request_role'],r['identity']) for r in ledger['requests']]
    require(0 < len(value['stages']) <= len(expected))
    ids, previous_end = set(), None
    for index, entry in enumerate(value['stages']):
        require(set(entry)=={'payload','thread_id','host_clock_id','host_start_ns','host_end_ns',
                             'before','after','status','error'})
        payload=entry['payload']
        require(set(payload)=={'schema_version','identity','pid','stage_role','request_identity',
                              'logical_device','producer_source_sha256','scope_semantics','marker_role','stage_id'})
        require(payload['schema_version']==MARKER_VERSION and payload['identity']==value['identity']
            and payload['pid']==value['pid'] and payload['producer_source_sha256']==value['producer_source_sha256']
            and (payload['stage_role'],payload['request_identity'])==expected[index]
            and payload['scope_semantics']=='HOST_CALL_ONLY' and payload['marker_role']=='non_sync_marker'
            and type(payload['logical_device']) is int and payload['logical_device']>=0)
        digest=hashlib.sha256(json.dumps({k:v for k,v in payload.items() if k!='stage_id'},sort_keys=True).encode()).hexdigest()
        require(payload['stage_id']==digest and digest not in ids)
        ids.add(digest)
        require(entry['host_clock_id']=='PYTHON_PERF_COUNTER_NS' and type(entry['thread_id']) is int
            and entry['thread_id']>0 and all(type(entry[k]) is int and -(2**63)<=entry[k]<2**63
                for k in ('host_start_ns','host_end_ns'))
            and entry['host_start_ns']<=entry['host_end_ns']
            and (previous_end is None or previous_end<=entry['host_start_ns']))
        previous_end=entry['host_end_ns']
        require((entry['status']=='COMPLETE' and entry['error'] is None)
                or (entry['status']=='FAILED' and isinstance(entry['error'],str) and bool(entry['error'])
                    and index==len(value['stages'])-1))
        for probe in (entry['before'],entry['after']):
            require(set(probe)=={'status','reason','logical_device','current_native_handle',
                                'default_native_handle','default_stream_mode','lifetime_status'})
            require(probe['default_stream_mode']==probe['lifetime_status']=='UNKNOWN'
                    and probe['logical_device']==payload['logical_device'])
            handles=[probe[k] for k in ('current_native_handle','default_native_handle')]
            require((probe['status']=='OBSERVED' and probe['reason'] is None
                        and all(type(h) is int and h>=0 for h in handles))
                or (probe['status']=='UNKNOWN' and isinstance(probe['reason'],str) and bool(probe['reason'])
                    and handles==[None,None]))
    setup_count=int(value['setup_observed'])
    setup_failed=bool(setup_count and value['stages'][0]['status']=='FAILED')
    if len(value['stages'])<len(expected):
        require(value['stages'][-1]['status']=='FAILED')
    request_stages=value['stages'][setup_count:]
    for index,request in enumerate(ledger['requests']):
        if index<len(request_stages):
            stage=request_stages[index]
            require((stage['status']=='FAILED')==(request['outcome']=='FAILED'))
        else:
            require(request['outcome']=='FAILED' and request['actual_output_tokens']==0
                    and request['observed_boundary_ids']==[])
            require(request['reasons']==([f"SETUP_FAILED:{value['stages'][0]['error']}"]
                                        if setup_failed else ['NOT_EXECUTED']))
