"""One-shot default-stream relation probe. No model, profiler or mode guessing.

The evaluator contains no timing threshold. A pending recorded event after S
only excludes a shared wait for this invocation; it is not a global PTDS flag.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import threading
import time
import traceback

VERSION = 'gate9-stream-relation/0.1'
ORDER = ['worker_recorded', 'query_before', 'sync_enter', 'sync_return', 'query_after']


def require(ok, reason):
    if not ok:
        raise ValueError('G9_' + reason)


def decide(r):
    require(r['order'] == ORDER, 'ORDER')
    require(type(r['main_tid']) is int and type(r['worker_tid']) is int
            and r['main_tid'] != r['worker_tid'], 'THREAD')
    require(r['main_handles'] == [0, 0] and r['worker_handles'] == [0, 0], 'HANDLE')
    require(type(r['before']) is bool and type(r['after']) is bool, 'EVENT_STATE')
    require(not (r['before'] and not r['after']), 'EVENT_STATE')
    return 'INCONCLUSIVE' if r['after'] else 'NOT_SHARED_FOR_PROBED_CALL'


def observe(backend, timeout=10, emit=lambda record: None):
    """Real Host threading; CUDA backend replaceable only for CPU tests."""
    ready, go, submitted, release = (threading.Event() for _ in range(4))
    r = dict(main_tid=threading.get_native_id(), order=[])
    shared = {}
    backend.prepare()
    r['main_handles'] = list(backend.handles())
    require(r['main_handles'] == [0, 0], 'HANDLE')

    def worker():
        try:
            backend.prepare_worker()  # initialization/warmup, outside relation
            r['worker_tid'] = threading.get_native_id()
            r['worker_handles'] = list(backend.handles())
            require(r['worker_handles'] == [0, 0], 'HANDLE')
            ready.set()
            if not go.wait(timeout):
                raise TimeoutError('WORKER_GO_TIMEOUT')
            shared['event'] = backend.submit()  # K -> E on worker current stream
            submitted.set()
            if not release.wait(timeout):
                raise TimeoutError('WORKER_RELEASE_TIMEOUT')
        except BaseException as error:
            shared['error'] = error
            ready.set()
            submitted.set()

    thread = threading.Thread(target=worker, name='gate9-worker', daemon=True)
    thread.start()
    try:
        if not ready.wait(timeout):
            raise TimeoutError('WORKER_READY_TIMEOUT')
        if 'error' in shared: raise shared['error']
        backend.drain()  # only after both contexts/event initialized; outside probe
        r['drain_complete_ns'] = time.perf_counter_ns()
        emit(dict(stage='drain_complete', **r))
        go.set()
        if not submitted.wait(timeout):
            raise TimeoutError('WORKER_SUBMIT_TIMEOUT')
        if 'error' in shared: raise shared['error']
        r['order'].append('worker_recorded')
        r['before'] = backend.query(shared['event'])
        r['order'].append('query_before')
        r['sync_enter_ns'] = time.perf_counter_ns()
        r['order'].append('sync_enter')
        emit(dict(stage='before_sync', **r))
        backend.sync()  # exactly torch.cuda.current_stream().synchronize()
        r['sync_return_ns'] = time.perf_counter_ns()
        r['order'].append('sync_return')
        r['after'] = backend.query(shared['event'])
        r['order'].append('query_after')
        emit(dict(stage='observed', **r))
        backend.cleanup(shared['event'])  # outside observation; never before query
        if 'error' in shared: raise shared['error']
        return r
    finally:
        go.set()
        release.set()
        thread.join(timeout)
        if thread.is_alive():
            raise TimeoutError('WORKER_EXIT_TIMEOUT')


class TorchBackend:
    def __init__(self, torch):
        self.torch = torch
        self.event = None

    def prepare(self):
        self.torch.cuda.set_device(0)
        self.torch.cuda.init()

    def handles(self):
        c = self.torch.cuda
        return int(c.current_stream().cuda_stream), int(c.default_stream().cuda_stream)

    def prepare_worker(self):
        c = self.torch.cuda
        c.set_device(0)
        self.event = c.Event(enable_timing=False)
        c._sleep(1)  # load kernel and materialize event before drain
        self.event.record(c.current_stream())
        self.event.synchronize()

    def drain(self): self.torch.cuda.synchronize()

    def submit(self):
        c = self.torch.cuda
        c._sleep(50_000_000)  # fixed finite work; never adaptive duration search
        self.event.record(c.current_stream())
        return self.event

    def query(self, event): return event.query()
    def sync(self): self.torch.cuda.current_stream().synchronize()
    def cleanup(self, event): event.synchronize()


def write_json(path, value):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=True, indent=2)


def check_device(identity, uuid, pci):
    from exposedpath_v141.gate8_adapter import normalized_pci
    require(identity['gpu_uuid'].lower() == uuid.lower()
            and normalized_pci(identity['pci_bus_id']) == normalized_pci(pci), 'DEVICE')


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('--output', required=True)
    p.add_argument('--expected-pid', type=int, required=True)
    p.add_argument('--uuid', required=True)
    p.add_argument('--pci', required=True)
    p.add_argument('--runtime-contract')
    args = p.parse_args(argv)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=False)
    report = dict(schema_version=VERSION, status='BLOCKED', pid=os.getpid(),
                  parent_pid=os.getppid(), executable=sys.executable,
                  role='ENGINEERING_RELATION_PROBE_NOT_FORMAL', error=None)
    try:
        require(os.getpid() == args.expected_pid, 'LAUNCH_PID')
        require(sys.version_info[:3] == (3, 11, 16), 'PYTHON_VERSION')
        if args.runtime_contract:
            from exposedpath_v141.gate8_target_python import current
            report['runtime'] = current(json.loads(Path(args.runtime_contract).read_text(encoding='utf-8')))
        require(os.environ.get('CUDA_DEVICE_ORDER') == 'PCI_BUS_ID'
                and os.environ.get('CUDA_VISIBLE_DEVICES') == '3', 'MASK')
        import torch
        if args.runtime_contract:
            site = Path(report['runtime']['snapshot']['site_root']).resolve()
            require(Path(torch.__file__).resolve().is_relative_to(site), 'TORCH_ORIGIN')
        require(str(torch.__version__) == '2.6.0+cu124' and torch.version.cuda == '12.4', 'TORCH_VERSION')
        from exposedpath.platform_adapter import cuda_identity_native
        identity = cuda_identity_native(torch.cuda)
        report['device'] = identity
        write_json(out / 'device.json', identity)
        # Keys/normalization follow the existing production adapter contract.
        check_device(identity, args.uuid, args.pci)
        records = []
        def emit(r):
            records.append(r)
            write_json(out / ('stage_%02d.json' % len(records)), r)
        result = observe(TorchBackend(torch), emit=emit)
        report.update(observation=result, status=decide(result))
    except BaseException:
        report['error'] = traceback.format_exc()
    write_json(out / 'report.json', report)
    return 0 if report['status'] == 'NOT_SHARED_FOR_PROBED_CALL' else 2


if __name__ == '__main__':
    raise SystemExit(main())
