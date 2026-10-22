"""Known-member v0.3 file-chain preparation; no CUDA or model execution.

Breaks caught: pending-only membership, using the copy entry as submit cutoff,
future-prefix bleed, wrong terminal, or API-wall-as-exposure arithmetic.
The literal expected answers live outside the consumer and its set recovery.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from tests.test_cupti_driver_queries import query_capture
from tests.test_cupti_timeline_adapter import marked_capture

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'tests/fixtures/coe_completion_reference_v0_1.json'


def prepared(case):
    # Reuse the already hand-shaped API22 callback/resource fixture. Only the
    # controlled effect intervals change; expected members are never recovered.
    raw, scope = query_capture()
    historical, producer = marked_capture()
    for callback in raw['callbacks']:
        callback['enter_seq'] += 2
        callback['exit_seq'] += 2
    # Reuse the established same-clock producer/drain fixture, rather than
    # handing a successful derived scope straight to the consumer.
    raw['callbacks'].append(deepcopy(next(c for c in historical['callbacks'] if c['id'] == 10)))
    raw['records'].extend(deepcopy([r for r in historical['records'] if r['id'] in ('apiD', 'physicalD')]))
    raw['markers'] = deepcopy(historical['markers'])
    for row in raw['records']:
        if row['id'] in case['intervals']:
            row['start'], row['end'] = case['intervals'][row['id']]
    rt = dict(next(c for c in raw['callbacks'] if c['id'] == 1),
              id=60, parent_id=None, correlation=600, start=80, end=84,
              enter_seq=100, exit_seq=103)
    dr = dict(next(c for c in raw['callbacks'] if c['id'] == 2),
              id=61, parent_id=60, correlation=601, start=81, end=83,
              enter_seq=101, exit_seq=102)
    raw['callbacks'].extend([rt, dr])
    for cb in (rt, dr):
        raw['records'].append(dict(cb, id='future-api-'+str(cb['id']), kind='API'))
    kernel = next(r for r in raw['records'] if r['id'] == 'k')
    raw['records'].append(dict(kernel, id='future-kernel', correlation=601, start=90, end=95))
    return raw, scope, producer


def put(path, value):
    path.write_text(json.dumps(value, sort_keys=True), encoding='utf8')


BOOT = '''import sys,runpy,json
from pathlib import Path
sys.path.insert(0,sys.argv[1])
root=Path(sys.argv[1]);folder=Path(sys.argv[2])
cfg=json.loads((folder/'consumer_binding.json').read_text())
binding=runpy.run_path(str(root/'scripts/cupti_model_consumer.py'))['bind_consumer'](cfg)
from analysis.cupti_timeline import analyze_files,select_scope
raw=json.loads((folder/'capture.json').read_text())
producer=json.loads((folder/'producer.json').read_text())
scope=select_scope(raw,producer,
 timing_policy='cupti-api22-distinct-api-callback-boundaries/0.2.0',
 driver_query_policy='cupti-api22-driver-queries/0.1.0')
assert scope==json.loads((folder/'scope.json').read_text()),'REFERENCE_SCOPE_CONFLICT'
value=analyze_files(folder/'capture.json',folder/'scope.json',folder/'derived',
 timing_policy='cupti-api22-distinct-api-callback-boundaries/0.2.0',
 driver_query_policy='cupti-api22-driver-queries/0.1.0')
assert not any(n=='torch' or n.startswith('torch.') for n in sys.modules)
print(json.dumps({'binding':binding,'result':value['result']}))
'''


def run_files(folder, raw, scope, producer):
    folder.mkdir()
    put(folder/'capture.json', raw)
    put(folder/'scope.json', scope)
    put(folder/'producer.json', producer)
    files = ('exposedpath_v141/cupti_driver_queries.py',
             'scripts/analyze_completion_operation_candidate.py',
             'exposedpath_v141/submit_effect_bridge.py', 'analysis/cupti_timeline.py')
    put(folder/'consumer_binding.json', dict(consumer_root=str(ROOT), code_root=str(ROOT),
        consumer_files=[dict(path=n, bytes=(ROOT/n).stat().st_size,
                            sha256=hashlib.sha256((ROOT/n).read_bytes()).hexdigest()) for n in files]))
    before = {p.name: p.read_bytes() for p in folder.iterdir()}
    process = subprocess.run([sys.executable, '-I', '-S', '-B', '-c', BOOT, str(ROOT), str(folder)],
        cwd=folder, capture_output=True, text=True, encoding='utf8', timeout=20)
    assert all((folder/n).read_bytes() == data for n, data in before.items())
    (folder/'stdout.txt').write_text(process.stdout, encoding='utf8')
    (folder/'stderr.txt').write_text(process.stderr, encoding='utf8')
    put(folder/'process.json', dict(return_code=process.returncode, isolated=True,
        environment='LOCAL_CPU_NOT_TARGET_GPU', python=sys.version, plan_sha256=hashlib.sha256(PLAN.read_bytes()).hexdigest()))
    return process


REFERENCE = json.loads(PLAN.read_text(encoding='utf8'))


@pytest.mark.parametrize('case', REFERENCE['cases'], ids=lambda c: c['id'])
def test_literal_construction_through_isolated_bound_v03_file_consumer(tmp_path, case):
    raw, scope, producer = prepared(case)
    folder = tmp_path/'files'
    process = run_files(folder, raw, scope, producer)
    assert process.returncode == 0, process.stderr
    result = json.loads(process.stdout)['result']
    assert result['schema_version'] == 'submit-effect-bridge/0.3.0'
    assert result['members'] == REFERENCE['members']
    assert result['terminal'] == REFERENCE['terminal']
    assert result['logical_zero_call_ids'] == REFERENCE['logical_zero_call_ids']
    actual = {k: result[k] for k in ('coe_ns', 'sync_intersection_ns', 'operation_wall_ns')}
    # v0.3 does not publish a separate complement field. This reference report
    # derives it explicitly; it does not silently invent a consumer field.
    actual['complement_ns'] = result['operation_wall_ns'] - result['coe_ns']
    assert actual == case['expected']
    assert result['synthetic_activities'] == []
    assert result['pure_host_blocking'] is None
    # Reference-side arithmetic consumes only the manually chosen pieces, not
    # completion_overlap/recover_suffix/the consumer's interval union.
    assert sum(b-a for a,b in case['manual_intersection_pieces']) == case['expected']['coe_ns']
    put(folder/'reference_comparison.json', dict(status='CPU_REFERENCE_MATCH_NOT_GPU_QUALIFICATION',
        case=case['id'], expected_members=REFERENCE['members'], expected_terminal=REFERENCE['terminal'],
        expected=case['expected'], actual=actual))


@pytest.mark.parametrize('damage,reason', [
    ('missing_positive', 'SUBMIT_EFFECT_POSITIVE_EFFECT_MISSING'),
    ('wrong_stream', 'SUBMIT_EFFECT_SCOPE'),
    ('unknown_payload', 'SUBMIT_EFFECT_PARAMETERS'),
    ('failed_sync', 'SUBMIT_EFFECT_FAILED_COMPLETION'),
    ('late_terminal', 'SUBMIT_EFFECT_COMPLETION'),
    ('duplicate_pair', 'SUBMIT_EFFECT_RECORD_DUPLICATE'),
])
def test_independent_reference_does_not_turn_missing_facts_into_zero(tmp_path, damage, reason):
    raw, scope, producer = prepared(REFERENCE['cases'][0])
    if damage == 'missing_positive':
        raw['records'] = [r for r in raw['records'] if r['id'] != 'm']
    elif damage == 'wrong_stream':
        next(r for r in raw['records'] if r['id'] == 'k')['stream'] = 5
    elif damage == 'unknown_payload':
        next(c for c in raw['callbacks'] if c['id'] == 3)['params'] = None
    elif damage == 'failed_sync':
        next(c for c in raw['callbacks'] if c['id'] == 8)['return_code'] = 2
        next(r for r in raw['records'] if r['id'] == 'api8')['return_code'] = 2
    elif damage == 'late_terminal':
        next(r for r in raw['records'] if r['id'] == 'd')['end'] = 80
    elif damage == 'duplicate_pair':
        raw['records'].append(deepcopy(next(r for r in raw['records'] if r['id'] == 'sync')))
    process = run_files(tmp_path/'files', raw, scope, producer)
    assert process.returncode != 0
    assert reason in process.stderr, process.stderr
    assert not (tmp_path/'files/derived/result.json').exists()
