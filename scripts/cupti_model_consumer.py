"""Load the four hash-bound CPU consumer files, not a stale checkout reader.

The model process still uses the reviewed native checkout. This separate CPU
process imports only the explicit overlay; it neither loads vendor DLLs nor
grants new provider qualification. The caller authenticates the package index.
"""
import hashlib
import importlib
import importlib.util
from pathlib import Path
import sys

FILES=('exposedpath_v141/cupti_driver_queries.py','scripts/analyze_completion_operation_candidate.py',
       'exposedpath_v141/submit_effect_bridge.py','analysis/cupti_timeline.py')


def require(ok,reason):
    if not ok:raise ValueError('CUPTI_CONSUMER_'+reason)


def bind_consumer(cfg):
    root=Path(cfg['consumer_root']).resolve();code=Path(cfg['code_root']).resolve()
    rows=cfg['consumer_files']
    require(len(rows)==len(FILES) and {r['path'] for r in rows}==set(FILES),'FILE_INDEX')
    for r in rows:
        p=root/r['path']
        require(p.resolve().is_relative_to(root) and p.is_file(),'CONSUMER_FILE:'+r['path'])
        for part in (p,*p.parents):
            require(not part.is_symlink() and not getattr(part.lstat(),'st_file_attributes',0)&0x400,'REPARSE')
            if part==root:break
        require(p.stat().st_size==r['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'],
            'CONSUMER_FILE:'+r['path'])
    # The already byte-checked checkout supplies the unmodified common modules.
    for name in ('exposedpath_v141','analysis'):
        parent=importlib.import_module(name)
        require(list(map(lambda p:Path(p).resolve(),parent.__path__))==[code/name],'PARENT_ORIGIN:'+name)
    modules=[]
    for name,rel in [('exposedpath_v141.cupti_driver_queries',FILES[0]),
        ('_exposedpath_completion_math_v01',FILES[1]),
        ('exposedpath_v141.submit_effect_bridge',FILES[2]),('analysis.cupti_timeline',FILES[3])]:
        source=root/rel
        require(name not in sys.modules,'MODULE_ALREADY_LOADED:'+name)
        spec=importlib.util.spec_from_file_location(name,source)
        module=importlib.util.module_from_spec(spec);sys.modules[name]=module
        try:spec.loader.exec_module(module)
        except BaseException:
            del sys.modules[name];raise
        if '.' in name:
            parent,leaf=name.rsplit('.',1);setattr(sys.modules[parent],leaf,module)
        modules.append(dict(name=name,origin=str(source),sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
    bridge=sys.modules['exposedpath_v141.submit_effect_bridge']
    require(bridge.QUERY_VERSION=='submit-effect-bridge/0.3.0','VERSION')
    return dict(schema_version='cupti-model-consumer-binding/0.1.0',consumer_version=bridge.QUERY_VERSION,
        modules=modules,model_imported=False,vendor_library_loaded=False)
