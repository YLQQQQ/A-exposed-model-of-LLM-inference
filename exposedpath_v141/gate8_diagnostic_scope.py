"""Source-bound diagnostic facts for the explicit Engineering scope profile.

Process identity is not impact assessment. No message-text inference, warning
exemption, collector completeness assertion, or frozen Canonical modification.
"""
import json
from pathlib import Path
import sqlite3

from exposedpath.gate8_identity import validate_pass_identity
from .gate8_adapter import digest

VERSION = 'exposedpath-diagnostic-scope/0.1.0'


def _require_sealed(database):
    # The declared hash covers only the exported main file, never WAL state.
    for suffix in ('-wal', '-journal'):
        sidecar = Path(str(database) + suffix)
        if sidecar.exists() and sidecar.stat().st_size:
            raise ValueError('DIAGNOSTIC_SCOPE_UNSEALED')


def _target_process(connection, ledger):
    """Bind full global namespace to original run/pass/attempt NVTX payloads."""
    fields = ('run_id','pass_id','attempt_id','experiment_id','wmpc_id')
    prefixes = ('EXPOSEDPATH_JSON_V1:', 'EXPOSEDPATH_BOUNDARY_V1:',
                'EXPOSEDPATH_DRAIN_V1:', 'EXPOSEDPATH_STAGE_V1:')
    matches = []
    try:
        for row in connection.execute('SELECT rowid AS source_rowid,text,globalTid FROM NVTX_EVENTS'):
            text = row['text']
            if not isinstance(text,str) or not text.startswith(prefixes):
                continue
            payload = json.loads(text.split(':',1)[1])
            identity = payload.get('identity',payload)
            if not isinstance(identity,dict) or any(identity.get(k)!=ledger[k] for k in fields):
                continue
            tid = row['globalTid']
            if type(tid) is not int or not 0 < tid < 2**63 or ((tid >> 24) & 0xffffff)!=ledger['pid']:
                raise ValueError('DIAGNOSTIC_SCOPE_TARGET_PROCESS')
            matches.append(dict(source_table='NVTX_EVENTS',source_rowid=row['source_rowid'],
                                global_tid=tid,global_pid=tid-tid % 2**24))
    except (sqlite3.Error, json.JSONDecodeError, AttributeError) as exc:
        raise ValueError('DIAGNOSTIC_SCOPE_TARGET_PROCESS') from exc
    if len({r['global_pid'] for r in matches})!=1:
        raise ValueError('DIAGNOSTIC_SCOPE_TARGET_PROCESS')
    return matches[0]['global_pid'], matches


def _derive(sqlite_path, pass_path):
    sqlite_path, pass_path = Path(sqlite_path).resolve(), Path(pass_path).resolve()
    _require_sealed(sqlite_path)
    source_hash, pass_hash = digest(sqlite_path), digest(pass_path)
    ledger = json.loads(pass_path.read_text(encoding='utf-8'))
    validate_pass_identity(ledger)
    if ledger['pass_id'] != 'pass1':
        raise ValueError('DIAGNOSTIC_SCOPE_PASS')
    records = []
    # Immutable reads cannot incorporate a sidecar created after the seal check.
    # Existing nonempty journals are rejected, never checkpointed or discarded.
    with sqlite3.connect(sqlite_path.as_uri()+'?mode=ro&immutable=1', uri=True) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA query_only=ON')
        target_global_pid, target_refs = _target_process(connection,ledger)
        columns = {r[1] for r in connection.execute('PRAGMA table_info(DIAGNOSTIC_EVENT)')}
        if not {'timestamp','source','severity','text'} <= columns:
            raise ValueError('DIAGNOSTIC_SCOPE_SCHEMA')
        optional = ('globalPid','timestampType')
        missing = [k for k in optional if k not in columns]
        selected = ['rowid AS source_rowid','timestamp','source','severity','text']
        selected.extend(k if k in columns else f'NULL AS {k}' for k in optional)
        for row in connection.execute('SELECT '+','.join(selected)+' FROM DIAGNOSTIC_EVENT ORDER BY rowid'):
            if (any(type(row[k]) is not int for k in ('source_rowid','timestamp','source','severity'))
                    or not isinstance(row['text'],str)
                    or any(row[k] is not None and type(row[k]) is not int for k in optional)):
                raise ValueError('DIAGNOSTIC_SCOPE_RECORD')
            global_pid = row['globalPid']
            # Nsight's serialized global PID has a process field in bits24..47.
            # Negative system sentinels and nonzero thread bits are not a PID.
            process_id = ((global_pid >> 24) & 0xffffff) if (
                type(global_pid) is int and 0 < global_pid < 2**63
                and global_pid % 2**24 == 0) else None
            if process_id == 0:
                process_id = None
            relation = ('UNKNOWN' if process_id is None else
                        'TARGET_PROCESS' if global_pid == target_global_pid else 'OTHER_PROCESS')
            records.append(dict(
                source_sqlite_sha256=source_hash, source_table='DIAGNOSTIC_EVENT',
                source_rowid=row['source_rowid'], timestamp_raw=row['timestamp'],
                timestamp_type=row['timestampType'], source_id=row['source'],
                severity_id=row['severity'], text=row['text'], global_pid=global_pid,
                process_id=process_id, process_relation=relation, impact_status='UNASSESSED'))
    _require_sealed(sqlite_path)
    if digest(sqlite_path)!=source_hash or digest(pass_path)!=pass_hash:
        raise ValueError('DIAGNOSTIC_SCOPE_SOURCE_CHANGED')
    return dict(schema_version=VERSION, source_sqlite_sha256=source_hash,
                pass_identity_sha256=pass_hash, target_pid=ledger['pid'],
                target_global_pid=target_global_pid, target_nvtx_refs=target_refs,
                identity={k:ledger[k] for k in ('run_id','pass_id','attempt_id')},
                missing_optional_columns=missing, records=records,
                dropped_records_status='UNKNOWN', scientific_outputs_allowed=False)


def write_diagnostic_scope(sqlite_path, pass_path, output_path):
    output = Path(output_path)
    if output.exists():
        raise FileExistsError(output)
    result = _derive(sqlite_path, pass_path)
    with output.open('x',encoding='utf-8',newline='\n') as handle:
        json.dump(result,handle,sort_keys=True,indent=2)
        handle.write('\n')
    return result


def load_diagnostic_scope(result_path, sqlite_path, pass_path):
    saved = json.loads(Path(result_path).read_text(encoding='utf-8'))
    if not isinstance(saved,dict) or saved.get('schema_version') != VERSION:
        raise ValueError('DIAGNOSTIC_SCOPE_VERSION')
    actual = _derive(sqlite_path,pass_path)
    if saved != actual:
        raise ValueError('DIAGNOSTIC_SCOPE_SOURCE_OR_CONTENT_MISMATCH')
    return saved
