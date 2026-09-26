"""Closed construction 0.2 diagnostics, never a loss certificate or model policy.

Called only AFTER independent operation/dependency matching. Source byte pins
prevent subsequent IPC/event/shared-memory changes inheriting this exclusion.
"""
import hashlib
from pathlib import Path
import re
import sqlite3

ROOT=Path(__file__).resolve().parents[1]
SOURCE_HASHES={
    'scripts/gate8_controlled_token.cu':{
        '82490f072468ca28bc432ebd4e5634467b9fe2299fd51e8b19f901ccabb28ab1',
        '6eda24c9519ff0b4a066f11cbf67f89efddce7eb6bc71f4f6d84e6094bbcf309'},
    'exposedpath_v141/gate8_controlled.py':{
        '496c1bd2db6a8b6399e6e0fdc3f5a46c3837d177862ca00f0d307daf94db96d9',
        '96e416f4aeee1a85e837aa7eb994c1469aa6b6c991ba4916bac12e85b4e69bbb'},
    'exposedpath_v141/gate8_controlled_cli.py':{
        '14eff33925ce2083339abc1b60e66497a566d999ccd68688f0ad077dcf4bc69d',
        '8f35f9a3104ffb5858a0e0f23511c65bac7dc122441ff475fdc2e0fa09b5cb8c'},
}
WARNINGS={
    'Not all NVTX events might have been collected.',
    'No NVTX events collected. Does the process use NVTX?',
    'CUDA profiling might have not been started correctly.',
    'No CUDA events collected. Does the process use CUDA?',
}
TARGET_INFO={
    'Common injection library initialized successfully.',
    'CUDA injection initialized successfully.',
    'NVTX injection initialized successfully.',
    'Enabling trace for device graph launch',
    'Buffers holding CUDA trace data will be flushed on CudaProfilerStop() call. See --flush-on-cudaprofilerstop to control this behavior.',
    'CUDA hardware tracing is not supported on this system. A legacy (software instrumented) trace was collected instead.',
}


def assess_diagnostics(conn,records,*,pid,sqlite_sha256,observed_cuda_pids):
    def require(ok):
        if not ok: raise ValueError('UNBOUNDED_DIAGNOSTIC_REQUIRES_REVIEW')
    sources={}
    for name,allowed in SOURCE_HASHES.items():
        path=ROOT/name
        require(path.is_file())
        sources[name]=hashlib.sha256(path.read_bytes()).hexdigest()
        require(sources[name] in allowed)
    try:
        for key,value in [('EXPORT_PRODUCT_VERSION','2026.2.1.210'),('EXPORT_SCHEMA_VERSION','3.25.0')]:
            require([r[0] for r in conn.execute('SELECT value FROM META_DATA_EXPORT WHERE name=?',(key,))]==[value])
        def enum(table):
            rows=list(conn.execute('SELECT id,name FROM '+table))
            require(len({r[0] for r in rows})==len(rows))
            return {r[0]:r[1] for r in rows}
        levels=enum('ENUM_DIAGNOSTIC_SEVERITY_LEVEL')
        origins=enum('ENUM_DIAGNOSTIC_SOURCE_TYPE')
        clocks=enum('ENUM_DIAGNOSTIC_TIMESTAMP_SOURCE')
    except sqlite3.Error as exc:
        raise ValueError('UNBOUNDED_DIAGNOSTIC_REQUIRES_REVIEW') from exc
    assessed=[]
    for record in records:
        require(set(('timestamp','timestampType','source','severity','text','globalPid','source_rowid'))<=record.keys())
        raw={k:v for k,v in record.items() if k!='source_rowid'}
        gpid=raw['globalPid']; text=raw['text']; stamp=raw['timestamp']
        require(type(gpid) is int and type(stamp) is int and isinstance(text,str))
        target=((gpid>>24)&0xFFFFFF) if gpid>=0 else None
        require(target is None or target>0)
        level=levels.get(raw['severity']); origin=origins.get(raw['source']); clock=clocks.get(raw['timestampType'])
        disposition=None
        if level=='Warning' and origin=='Analysis' and clock=='HostTimestamp':
            if target is not None and target!=pid and target not in observed_cuda_pids and text in WARNINGS:
                disposition='OUTSIDE_DECLARED_DEPENDENCY_SCOPE'
        elif level=='Info':
            if gpid==-144115188075855872 and origin=='Analysis' and clock=='TargetTimestamp':
                if text in {'Profiling has started.','Profiling has stopped.'}: disposition='COLLECTOR_STATUS_ONLY'
            elif target is not None:
                ok=False
                if origin=='Daemon' and clock=='TargetTimestamp':
                    ok=text==f'Process {target} was launched by the profiler'
                elif origin=='Injection' and clock=='TargetTimestamp':
                    ok=(text=='Common injection library initialized successfully.' or (target==pid and (
                        text in TARGET_INFO or re.fullmatch(r'Number of CUPTI events produced: \t[0-9]+, CUPTI buffers: [0-9]+\.',text) is not None
                        or re.fullmatch(r'Loaded CUPTI library: [A-Za-z]:\\(?:[^\\\r\n]+\\)*Nsight Systems 2026\.2\.1\\target-windows-x64\\cupti64_129\.dll',text) is not None)))
                elif origin=='Analysis' and clock=='HostTimestamp' and target==pid:
                    ok=re.fullmatch(r'Number of (?:NVTX|CUDA) events collected: \t[0-9]+\.',text) is not None
                if ok: disposition='COLLECTOR_STATUS_ONLY'
        require(disposition is not None)
        assessed.append(dict(raw_ref=dict(source_sqlite_sha256=sqlite_sha256,source_table='DIAGNOSTIC_EVENT',
                                         source_rowid=record['source_rowid']),raw=raw,
                             severity_name=level,source_name=origin,timestamp_domain=clock,
                             decoded_pid=target,disposition=disposition,
                             basis='PINNED_CLOSED_SOURCE_AND_MATCHED_PRIVATE_STREAM_DEPENDENCIES'
                                   if disposition=='OUTSIDE_DECLARED_DEPENDENCY_SCOPE' else 'EXACT_VERSIONED_STATUS_TEMPLATE'))
    return dict(schema_version='controlled-diagnostic-assessment/0.1.0',
                status='CONTROLLED_ENGINEERING_DIAGNOSTIC_ONLY',source_byte_hashes=sources,
                records=assessed,collector_integrity_status='UNKNOWN',
                limitations=['NO_PARENT_CHILD_CLAIM','HOST_TIMESTAMP_NOT_COMPARED_TO_TRACE_CLOCK',
                             'COUNTS_NOT_ZERO_LOSS_CERTIFICATE','NOT_ARBITRARY_MODEL_SUPPORT'])
