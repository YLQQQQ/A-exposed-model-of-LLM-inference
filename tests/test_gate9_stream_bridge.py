"""CPU producer and source-bound bridge tests; not platform CUDA evidence."""
import importlib
import json
from types import SimpleNamespace
import pytest


def api():
    assert importlib.util.find_spec('exposedpath.gate9_stream_bridge'), 'explicit stream producer missing'
    return importlib.import_module('exposedpath.gate9_stream_bridge')


def test_actual_current_stream_call_is_observed_not_with_context_claim(monkeypatch):
    events=[]; handle=[123]
    stream=SimpleNamespace(cuda_stream=123,device=SimpleNamespace(index=0),synchronize=lambda:events.append('sync'))
    cuda=SimpleNamespace(current_stream=lambda device:SimpleNamespace(cuda_stream=handle[0],device=stream.device,synchronize=stream.synchronize),
        nvtx=SimpleNamespace(range_push=lambda text:events.append(json.loads(text.split(':',1)[1])),range_pop=lambda:None))
    bridge=api().StreamBridge(cuda,stream,{'request_id':'r'},'generation-1')
    with bridge:
        bridge.observe('submit',lambda native:events.append(native))
        bridge.synchronize('wait')
    assert [r['operation'] for r in bridge.records]==['submit','wait']
    assert all(r['before_native_handle']==r['after_native_handle']==123 and r['status']=='COMPLETE' for r in bridge.records)
    assert 123 in events and 'sync' in events
    assert bridge.status=='COMPLETE'


@pytest.mark.parametrize('damage',['zero','changed','failure'])
def test_stream_probe_rejects_default_changed_or_failed_call(damage):
    events=[]; stream=SimpleNamespace(cuda_stream=0 if damage=='zero' else 123,device=SimpleNamespace(index=0))
    cuda=SimpleNamespace(current_stream=lambda device:stream,nvtx=SimpleNamespace(range_push=events.append,range_pop=lambda:None))
    bridge=api().StreamBridge(cuda,stream,{'request_id':'r'},'g')
    def call(native):
        if damage=='changed': stream.cuda_stream=124
        if damage=='failure': raise RuntimeError('native failure')
    with pytest.raises((ValueError,RuntimeError)):
        with bridge: bridge.observe('submit',call)
    assert bridge.status!='COMPLETE'
