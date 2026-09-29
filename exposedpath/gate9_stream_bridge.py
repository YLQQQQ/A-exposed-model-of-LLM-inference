"""Held explicit-stream call evidence. Does not infer trace IDs or ownership."""
import json
import threading

PREFIX = 'EXPOSEDPATH_STREAM_BRIDGE_V1:'
VERSION = 'exposedpath-stream-bridge/0.1.0'


class StreamBridge:
    def __init__(self, cuda, stream, identity, generation):
        self.cuda, self.stream = cuda, stream  # Keep the native resource alive.
        self.handle = int(stream.cuda_stream)
        self.device = stream.device.index
        self.identity, self.generation = dict(identity), generation
        self.records, self.status = [], 'NOT_STARTED'
        self.thread = threading.get_native_id()

    def _current(self):
        stream = self.cuda.current_stream(self.device)
        if (self.handle <= 0 or stream.cuda_stream != self.handle
                or stream.device.index != self.device or threading.get_native_id() != self.thread):
            raise ValueError('STREAM_BRIDGE_ACTUAL_CURRENT_CONFLICT')
        return stream

    def _payload(self, operation, ordinal):
        return dict(schema_version=VERSION, identity=self.identity, generation=self.generation,
                    logical_device=self.device, native_handle=self.handle,
                    operation=operation, ordinal=ordinal)

    def _push(self, value):
        self.cuda.nvtx.range_push(PREFIX + json.dumps(value, sort_keys=True, separators=(',', ':')))

    def __enter__(self):
        self._current()
        if self.status != 'NOT_STARTED': raise ValueError('STREAM_BRIDGE_REUSE')
        self._push(self._payload('lifetime', -1))
        self.status = 'OPEN'
        return self

    def __exit__(self, kind, value, tb):
        self.status = 'FAILED'
        try:
            if kind is None:
                self._current()
                self.status = 'COMPLETE'
        finally:
            self.cuda.nvtx.range_pop()

    def observe(self, operation, call):
        if self.status != 'OPEN' or operation not in ('submit','copy','wait','internal_wait'):
            raise ValueError('STREAM_BRIDGE_OPERATION')
        self._current()
        payload = self._payload(operation, len(self.records))
        record = dict(payload=payload, operation=operation, before_native_handle=self.handle,
                      after_native_handle=None, status='FAILED', error=None)
        self.records.append(record)
        self._push(payload)
        try:
            result = call(self.handle)
            record['after_native_handle'] = int(self._current().cuda_stream)
            record['status'] = 'COMPLETE'
            return result
        except BaseException as exc:
            record['error'] = type(exc).__name__ + ':' + str(exc)
            raise
        finally:
            self.cuda.nvtx.range_pop()

    def synchronize(self, operation='wait'):
        return self.observe(operation, lambda _: self._current().synchronize())
