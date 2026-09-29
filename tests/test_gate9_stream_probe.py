"""CPU orchestration/oracle tests; no CUDA evidence is produced here."""
import importlib
import threading
import pytest


def module():
    return importlib.import_module('scripts.gate9_stream_probe')


class Backend:
    def __init__(self, before=False, after=False, worker_handle=0, fail=False):
        self.before, self.after = before, after
        self.worker_handle, self.fail = worker_handle, fail
        self.calls = []
        self.event = object()
        self.queries = 0

    def prepare(self): self.calls.append('prepare')
    def prepare_worker(self): self.calls.append('prepare_worker')
    def drain(self): self.calls.append('drain')
    def handles(self):
        return (self.worker_handle if threading.current_thread().name == 'gate9-worker' else 0, 0)
    def submit(self):
        self.calls.append('submit')
        if self.fail: raise RuntimeError('original worker failure')
        return self.event
    def query(self, event):
        assert event is self.event
        self.calls.append('query')
        self.queries += 1
        return self.before if self.queries == 1 else self.after
    def sync(self): self.calls.append('target_sync')
    def cleanup(self, event): self.calls.append('cleanup')


def test_pending_after_return_excludes_shared_wait_and_cleanup_is_outside():
    b = Backend()
    r = module().observe(b, timeout=1)
    assert module().decide(r) == 'NOT_SHARED_FOR_PROBED_CALL'
    assert b.calls == ['prepare', 'prepare_worker', 'drain', 'submit', 'query', 'target_sync', 'query', 'cleanup']
    assert r['worker_tid'] != r['main_tid']


@pytest.mark.parametrize('before,after', [(False, True), (True, True)])
def test_completion_is_not_proof_of_legacy(before, after):
    assert module().decide(module().observe(Backend(before, after), timeout=1)) == 'INCONCLUSIVE'


def test_complete_then_pending_rejects_event_identity_or_state_conflict():
    r = module().observe(Backend(True, False), timeout=1)
    with pytest.raises(ValueError, match='EVENT_STATE'):
        module().decide(r)


def test_wrong_worker_handle_stops_before_target_call():
    b = Backend(worker_handle=9)
    with pytest.raises(ValueError, match='HANDLE'):
        module().observe(b, timeout=1)
    assert 'target_sync' not in b.calls


def test_worker_failure_is_not_a_completed_probe():
    with pytest.raises(RuntimeError, match='original worker failure'):
        module().observe(Backend(fail=True), timeout=1)


@pytest.mark.parametrize('field', ['before', 'after', 'worker_tid', 'main_tid', 'order'])
def test_missing_observation_cannot_pass(field):
    r = module().observe(Backend(), timeout=1)
    del r[field]
    with pytest.raises((ValueError, KeyError)):
        module().decide(r)


def test_reordered_sync_or_same_thread_cannot_pass():
    r = module().observe(Backend(), timeout=1)
    r['order'] = list(reversed(r['order']))
    with pytest.raises(ValueError, match='ORDER'):
        module().decide(r)
    r = module().observe(Backend(), timeout=1)
    r['worker_tid'] = r['main_tid']
    with pytest.raises(ValueError, match='THREAD'):
        module().decide(r)


def test_timeout_stops_without_target_sync():
    class Slow(Backend):
        def submit(self):
            threading.Event().wait(.1)
            return super().submit()
    b = Slow()
    with pytest.raises(TimeoutError):
        module().observe(b, timeout=.001)
    assert 'target_sync' not in b.calls


def test_native_adapter_uses_real_pci_field_and_normalizes():
    uuid = 'GPU-00000000-0000-0000-0000-000000000001'
    module().check_device({'gpu_uuid': uuid, 'pci_bus_id': '0000:E1:00.0'},
                          uuid, '00000000:E1:00.0')
    with pytest.raises(ValueError, match='DEVICE'):
        module().check_device({'gpu_uuid': 'GPU-other', 'pci_bus_id': '00000000:E1:00.0'},
                              'GPU-ab', '00000000:E1:00.0')


def test_pid_failure_persists_before_importing_torch(tmp_path):
    import json
    out = tmp_path / 'run'
    code = module().main(['--output', str(out), '--expected-pid', '-1',
                          '--uuid', 'unused', '--pci', 'unused'])
    r = json.loads((out / 'report.json').read_text())
    assert code != 0 and r['status'] == 'BLOCKED'
    assert 'G9_LAUNCH_PID' in r['error']


def test_supervisor_preserves_bytes_and_actual_pid(tmp_path):
    import sys
    from scripts.gate9_stream_probe_run import supervise
    code = ('import os,sys; p=int(sys.stdin.readline());'
            'assert p==os.getpid();sys.stdout.buffer.write(bytes([255,0,129]));'
            'sys.stderr.buffer.write(b"original error");sys.exit(7)')
    r = supervise([sys._base_executable, '-c', code], tmp_path, 5,
                  tmp_path/'out', tmp_path/'err')
    assert r['exit_code'] == 7 and r['timed_out'] is False
    assert (tmp_path/'out').read_bytes() == b'\xff\x00\x81'
    assert (tmp_path/'err').read_bytes() == b'original error'


def test_supervisor_timeout_is_non_success(tmp_path):
    import sys
    from scripts.gate9_stream_probe_run import supervise
    r = supervise([sys._base_executable, '-c', 'import time;time.sleep(30)'], tmp_path, .05,
                  tmp_path/'out', tmp_path/'err')
    assert r['timed_out'] is True and r['exit_code'] != 0


def test_torch_backend_warms_before_drain_and_queries_same_event():
    class Stream:
        cuda_stream = 0
        def synchronize(self): calls.append('current_sync')
    class Event:
        def record(self, stream):
            assert stream is s
            calls.append('event_record')
        def synchronize(self): calls.append('event_sync')
        def query(self): calls.append('event_query'); return False
    class Cuda:
        def set_device(self, d): assert d == 0
        def init(self): pass
        def current_stream(self): return s
        def default_stream(self): return s
        def Event(self, enable_timing): assert enable_timing is False; return Event()
        def _sleep(self, cycles): calls.append(('work', cycles))
        def synchronize(self): calls.append('device_drain')
    class Torch: cuda = Cuda()
    calls, s = [], Stream()
    r = module().observe(module().TorchBackend(Torch()), timeout=1)
    assert module().decide(r) == 'NOT_SHARED_FOR_PROBED_CALL'
    assert calls == [('work', 1), 'event_record', 'event_sync', 'device_drain',
                     ('work', 50000000), 'event_record', 'event_query',
                     'current_sync', 'event_query', 'event_sync']
