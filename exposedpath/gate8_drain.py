"""Observe the runner's existing drain; this recorder never issues a CUDA call."""
from copy import deepcopy
import json
import threading

DRAIN_PREFIX = 'EXPOSEDPATH_DRAIN_V1:'
DRAIN_VERSION = 'exposedpath-drain-ledger/0.1.0'


class DrainRecorder:
    def __init__(self, identity, operation_id, logical_device, *, clock_ns, push=None, pop=None):
        from .gate8_identity import validate_shape
        validate_shape('identity', identity)
        if not isinstance(operation_id,str) or not operation_id:
            raise ValueError('DRAIN_OPERATION_ID_INVALID')
        if type(logical_device) is not int or logical_device < 0:
            raise ValueError('DRAIN_LOGICAL_DEVICE_INVALID')
        if ((identity['pass_id'] == 'pass1' and (not callable(push) or not callable(pop)))
                or (identity['pass_id'] == 'pass0' and (push is not None or pop is not None))):
            raise ValueError('DRAIN_PASS_MARKER_CONFLICT')
        self.payload = dict(schema_version='exposedpath-drain-marker/0.1.0',
                            operation_id=operation_id, identity=deepcopy(identity),
                            logical_device=logical_device, marker_role='non_sync_marker')
        self.clock_ns, self.push, self.pop = clock_ns, push, pop
        self.record = None

    def observe(self, existing_drain):
        if self.record is not None:
            raise ValueError('DRAIN_DUPLICATE')
        if self.push is not None:
            self.push(DRAIN_PREFIX + json.dumps(self.payload, sort_keys=True, separators=(',', ':')))
        start = self.clock_ns()
        self.record = {**deepcopy(self.payload), 'thread_id': threading.get_native_id(),
                       'host_start_ns': start, 'host_end_ns': None,
                       'host_clock_id': 'PYTHON_PERF_COUNTER_NS', 'status': 'FAILED', 'error': None}
        try:
            existing_drain()
            self.record['status'] = 'COMPLETE'
        except BaseException as exc:
            self.record['error'] = type(exc).__name__
            raise
        finally:
            self.record['host_end_ns'] = self.clock_ns()
            if self.pop is not None:
                self.pop()
        if self.record['host_end_ns'] < start:
            self.record.update(status='FAILED', error='DRAIN_HOST_TIME_REVERSAL')
            raise ValueError('DRAIN_HOST_TIME_REVERSAL')
