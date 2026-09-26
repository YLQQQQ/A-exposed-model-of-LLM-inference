"""Route-A scoped evidence adapter, v0.1: controlled local fixtures only.

This validates a construction's scope assertions, not a collector certificate.
Real target-scope admission requires separately qualified evidence production.
"""
import json
from pathlib import Path

from .gate8_adapter import digest

VERSION = 'exposedpath-target-scope-assessment/0.1.0'
FIELDS = {'schema_version', 'input_receipt_sha256', 'basis',
          'collector_integrity_status', 'dropped_count', 'scope_status',
          'boundary_identity_clock', 'required_api_universe', 'dependency_scope',
          'requests', 'local_gaps', 'reasons', 'evidence'}


def validate_assessment(value, synthetic_fixture):
    if not isinstance(value, dict):
        raise ValueError('TARGET_SCOPE_INVALID')
    if not synthetic_fixture or value.get('basis') != 'SYNTHETIC_CONTROLLED_ORACLE':
        raise ValueError('SYNTHETIC assessment cannot qualify real evidence')
    if (set(value) != FIELDS or value['schema_version'] != VERSION
            or value['collector_integrity_status'] != 'UNKNOWN'
            or value['dropped_count'] is not None
            or value['scope_status'] not in ('SUFFICIENT', 'LOCAL_GAPS', 'UNBOUNDED')
            or value['boundary_identity_clock'] != 'PROVEN'
            or value['required_api_universe'] != 'PROVEN'
            or value['dependency_scope'] not in ('PROVEN', 'UNKNOWN')
            or not isinstance(value['reasons'], list)
            or not isinstance(value['requests'], list) or not value['requests']
            or not isinstance(value['local_gaps'], list)
            or any(not isinstance(r, str) or not r for r in value['reasons'])
            or not isinstance(value['evidence'], list) or not value['evidence']):
        raise ValueError('TARGET_SCOPE_INVALID')
    unbounded = value['scope_status'] == 'UNBOUNDED'
    if (not unbounded and value['dependency_scope'] != 'PROVEN') or (unbounded and not value['reasons']):
        raise ValueError('DEPENDENCY_SCOPE_UNPROVEN')


def load_assessment(path, receipt_hash, synthetic_fixture):
    path = Path(path).resolve()
    value = json.loads(path.read_text(encoding='utf-8'))
    validate_assessment(value, synthetic_fixture)
    if value['input_receipt_sha256'] != receipt_hash:
        raise ValueError('TARGET_INPUT_RECEIPT_CONFLICT')
    sources = []
    for item in value['evidence']:
        if not isinstance(item, dict) or set(item) != {'filename', 'sha256'}:
            raise ValueError('TARGET_EVIDENCE_INVALID')
        source = (path.parent / item['filename']).resolve()
        if (not source.is_relative_to(path.parent) or not source.is_file()
                or source.stat().st_size == 0 or digest(source) != item['sha256']):
            raise ValueError('TARGET_EVIDENCE_HASH_OR_PATH_INVALID')
        sources.append(source)
    if len(set(sources)) != len(sources):
        raise ValueError('TARGET_EVIDENCE_DUPLICATE')
    return value, sources


def validate_projection(value, projections, inputs):
    expected = {(p['identity']['request_id'], p['identity']['repeat_id']):
                (p['start_ns'], p['end_ns']) for p in projections if p['phase'] == 'full_request'}
    actual = {}
    for r in value['requests']:
        if set(r) != {'request_id', 'repeat_id', 'start_ns', 'end_ns', 'dependency_start_ns'}:
            raise ValueError('TARGET_REQUEST_INVALID')
        if any(type(r[k]) is not int or not -(2**63) <= r[k] < 2**63
               for k in ('start_ns', 'end_ns', 'dependency_start_ns')):
            raise ValueError('TARGET_TIME_INVALID')
        key = (r['request_id'], r['repeat_id'])
        if key in actual or r['dependency_start_ns'] > r['start_ns']:
            raise ValueError('TARGET_REQUEST_CONFLICT')
        actual[key] = (r['start_ns'], r['end_ns'])
    if actual != expected:
        raise ValueError('TARGET_PROJECTION_CONFLICT')
    if inputs.global_quality_reasons:
        raise ValueError('TARGET_SCOPE_CANNOT_OVERRIDE_GLOBAL_FAILURE')
    if value['scope_status'] == 'UNBOUNDED':
        return False
    failures = {(r['sync_id'], r['request_id'], r['repeat_id'], r['host_start_ns'], r['host_end_ns'], r['primary_reason'])
                for r in inputs.s_records if r['validity'] not in ('VALID_NONEMPTY', 'VALID_EMPTY')}
    gaps = set()
    for gap in value['local_gaps']:
        if set(gap) != {'sync_id', 'request_id', 'repeat_id', 'start_ns', 'end_ns', 'reason'}:
            raise ValueError('LOCAL_GAP_INVALID')
        if any(type(gap[k]) is not int for k in ('start_ns', 'end_ns')):
            raise ValueError('LOCAL_GAP_TIME_INVALID')
        key = (gap['request_id'], gap['repeat_id'])
        if key not in expected or not expected[key][0] <= gap['start_ns'] <= gap['end_ns'] <= expected[key][1]:
            raise ValueError('LOCAL_GAP_OUTSIDE_REQUEST')
        gaps.add((gap['sync_id'], *key, gap['start_ns'], gap['end_ns'], gap['reason']))
    if (len(gaps) != len(value['local_gaps']) or gaps != failures
            or (value['scope_status'] == 'SUFFICIENT') != (not gaps)):
        raise ValueError('LOCAL_GAP_NOT_PROVEN')
    return True


def publication(a_records, validation_role='SYNTHETIC_REGRESSION_ONLY'):
    return {'schema_version': 'exposedpath-accounting-publication/0.1.0',
            'validation_role': validation_role, 'windows': [
                {'window_id': r['window_id'],
                 'accounting_D_margin_ns': r['A_device_wait_ns'] - r['A_host_path_ns'] - r['A_cuda_api_ns'],
                 'unattributed_ns': r['A_unattributed_ns'],
                 'interpretation': 'PARTIAL_ACCOUNTING_ONLY' if r['A_unattributed_ns'] or r['primary_reason'] else 'CONTROLLED_ACCOUNTING_ONLY',
                 'mechanism_claim_allowed': False, 'signature_published': False}
                for r in a_records]}
