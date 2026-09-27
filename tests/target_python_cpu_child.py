"""Test-only native replacement in a real isolated Python producer process."""
import sys
from pathlib import Path
from types import SimpleNamespace
from exposedpath_v141 import gate8_qualification as q
from exposedpath_v141.gate8_files import _json


class Backend:
    def __init__(self,library):
        self.cuda=self; self.nvtx=SimpleNamespace(range_push=self.push,range_pop=self.pop)
    def is_initialized(self): return True
    def current_device(self): return 0
    def current_stream(self,_): return SimpleNamespace(cuda_stream=0,device=SimpleNamespace(index=0))
    default_stream=current_stream
    def identity(self):
        pre=_json(Path(sys.argv[1]).parent/'preflight.json')
        return dict(gpu_uuid=pre['gpu_uuid'],pci_bus_id=pre['pci_bus_id'])
    def prepare(self): pass
    def submit(self,value): self.token=value
    def copy(self): pass
    def wait(self): pass
    def read(self): return self.token
    def mark(self,_): pass
    def push(self,_): pass
    def pop(self): pass
    def close(self): pass


q.check_git=lambda _:None  # Test checkout is intentionally dirty; no source/GPU gate bypass in production.
q.execute(Path(sys.argv[1]),Path(sys.argv[2]),backend_factory=Backend)
