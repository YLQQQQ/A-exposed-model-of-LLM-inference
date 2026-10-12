"""Independent CPU expectations; never loads CUDA/CUPTI or qualifies a trace."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess

import pytest


def sample(count=64):
    # CUDA12.4 MEMSET correlation is the DRIVER ID 201, not runtime 100.
    common = dict(run_id='new-forensics', process_instance='pid-7-start-A',
                  thread_id=9, request_id='request-0', phase='decode', context_uid=3)
    events = [
        dict(common, seq=1, site='ENTER', call_id='runtime-1', domain='RUNTIME',
             correlation_id=100, name='cudaMemsetAsync', time_ns=10,
             params={'count': count, 'value': 0, 'pointer_alias': 'ptr-1', 'stream_handle': 0}),
        dict(common, seq=2, site='ENTER', call_id='driver-1', domain='DRIVER',
             correlation_id=201, name='cuMemsetD8Async', time_ns=12),
        dict(common, seq=3, site='EXIT', call_id='driver-1', domain='DRIVER',
             correlation_id=201, name='cuMemsetD8Async', time_ns=18, return_code=0),
        dict(common, seq=4, site='EXIT', call_id='runtime-1', domain='RUNTIME',
             correlation_id=100, name='cudaMemsetAsync', time_ns=20, return_code=0),
    ]
    api = [dict(common, domain='RUNTIME', correlation_id=100, record_id='api-r', name='cudaMemsetAsync'),
           dict(common, domain='DRIVER', correlation_id=201, record_id='api-d', name='cuMemsetD8Async')]
    streams = [dict(run_id='new-forensics', process_instance='pid-7-start-A', context_uid=3,
                    thread_id=9,
                    stream_handle=0, stream_id=17, device_id=0, source='CUPTI_RESOURCE_QUERY',
                    start_ns=0, end_ns=100)]
    effects = [dict(run_id='new-forensics', process_instance='pid-7-start-A',
                    context_uid=3, device_id=0, stream_id=17, domain='DRIVER',
                    correlation_id=201, record_id='effect-1', kind='MEMSET', bytes=count,
                    start_ns=30, end_ns=40, timestamps_known=True)]
    return dict(version='memset-parameter-prototype/0.1.0', role='ENGINEERING_PARAMETER_FORENSICS',
                run_id='new-forensics', process_instance='pid-7-start-A',
                clock_id='synthetic-cupti', source='CPU_SYNTHETIC',
                dropped_records_status='UNKNOWN', callback_events=events,
                api_records=api, stream_bindings=streams, device_effects=effects)


def review(value):
    from scripts.memset_parameter_prototype import review_evidence
    return review_evidence(value)


def test_nonzero_requires_driver_bridge_and_preserves_unknown():
    result = review(sample())
    call = result['calls'][0]
    assert call['state'] == 'NONZERO_DEVICE_EFFECT_MAPPED'
    assert call['count'] == 64 and call['stream_handle'] == 0
    assert call['effect_record_ids'] == ['effect-1']
    assert call['driver_call_ids'] == ['driver-1']
    assert result['dropped_records_status'] == 'UNKNOWN'
    assert result['a_admission'] == 'NOT_ASSESSED'
    assert result['proof_scope'] == 'CPU_PROTOTYPE_NOT_TARGET_VALIDATION'


def test_zero_length_is_argument_fact_not_no_dependency_or_a_admission():
    value = sample(0)
    value['callback_events'] = [value['callback_events'][0], value['callback_events'][-1]]
    value['api_records'] = value['api_records'][:1]
    value['device_effects'] = []
    result = review(value)
    assert result['calls'][0]['state'] == 'ZERO_LENGTH_ARGUMENT_OBSERVED'
    assert result['a_admission'] == 'NOT_ASSESSED'
    assert result['calls'][0]['device_effect_completeness'] == 'NOT_PROVEN'


def test_nonzero_missing_effect_is_not_zero_or_host():
    value = sample()
    value['device_effects'] = []
    result = review(value)
    assert result['calls'][0]['state'] == 'NONZERO_EFFECT_MISSING'
    assert result['status'] == 'BLOCKED'
    assert result['a_admission'] == 'NOT_ASSESSED'


@pytest.mark.parametrize('change,reason', [
    ('params', 'PARAMETERS_UNKNOWN'), ('return', 'RETURN_UNKNOWN'),
    ('failed', 'API_FAILED'), ('wrong_process', 'IDENTITY_CONFLICT'),
    ('wrong_run', 'IDENTITY_CONFLICT'), ('missing_exit', 'INCOMPLETE_CALLBACK'),
    ('bad_order', 'CALLBACK_ORDER'), ('mismatch_exit', 'CALLBACK_IDENTITY'),
    ('context', 'CALLBACK_IDENTITY'), ('bad_count', 'PARAMETERS_UNKNOWN'),
    ('missing_api', 'API_MAPPING'), ('duplicate_api', 'API_MAPPING'),
    ('missing_stream', 'STREAM_MAPPING'), ('ambiguous_stream', 'STREAM_MAPPING'),
    ('out_of_lifetime', 'STREAM_MAPPING'), ('unknown_version', 'VERSION'),
    ('old_role', 'ROLE'), ('loss', 'OBSERVED_LOSS'),
])
def test_necessary_evidence_defects_refuse(change, reason):
    value = sample()
    if change == 'params': del value['callback_events'][0]['params']
    elif change == 'return': del value['callback_events'][-1]['return_code']
    elif change == 'failed': value['callback_events'][-1]['return_code'] = 2
    elif change == 'wrong_process': value['callback_events'][0]['process_instance'] = 'pid-reused'
    elif change == 'wrong_run': value['callback_events'][0]['run_id'] = 'old-run'
    elif change == 'missing_exit': value['callback_events'].pop()
    elif change == 'bad_order': value['callback_events'][1]['seq'] = 1
    elif change == 'mismatch_exit': value['callback_events'][-1]['correlation_id'] = 101
    elif change == 'context': value['callback_events'][-1]['context_uid'] = 4
    elif change == 'bad_count': value['callback_events'][0]['params']['count'] = None
    elif change == 'missing_api': value['api_records'].pop()
    elif change == 'duplicate_api': value['api_records'].append(deepcopy(value['api_records'][0]))
    elif change == 'missing_stream': value['stream_bindings'] = []
    elif change == 'ambiguous_stream': value['stream_bindings'] *= 2
    elif change == 'out_of_lifetime': value['stream_bindings'][0]['end_ns'] = 15
    elif change == 'unknown_version': value['version'] = 'future'
    elif change == 'old_role': value['role'] = 'FORMAL'
    elif change == 'loss': value['dropped_records_status'] = 'NONZERO'
    with pytest.raises(ValueError, match=reason):
        review(value)


@pytest.mark.parametrize('change', ['equal_runtime_id', 'wrong_context', 'wrong_stream', 'wrong_bytes', 'unknown_time'])
def test_effect_conflicts_or_equal_numbers_do_not_supply_bridge(change):
    value = sample()
    effect = value['device_effects'][0]
    if change == 'equal_runtime_id': effect['correlation_id'] = 100
    elif change == 'wrong_context': effect['context_uid'] = 4
    elif change == 'wrong_stream': effect['stream_id'] = 0
    elif change == 'wrong_bytes': effect['bytes'] = 63
    elif change == 'unknown_time': effect['timestamps_known'] = False
    result = review(value)
    assert result['status'] == 'BLOCKED'
    assert result['calls'][0]['state'] in {'NONZERO_EFFECT_MISSING', 'DEVICE_EFFECT_CONFLICT'}


def test_adjacent_driver_and_kernel_cannot_be_borrowed():
    value = sample()
    events = value['callback_events']
    value['callback_events'] = [events[0], dict(events[3], seq=2),
                               dict(events[1], seq=3, time_ns=21), dict(events[2], seq=4, time_ns=25)]
    assert review(value)['calls'][0]['state'] == 'NONZERO_EFFECT_MISSING'


def test_zero_with_nonzero_device_effect_is_conflict():
    value = sample(0)
    value['device_effects'][0]['bytes'] = 64
    result = review(value)
    assert result['status'] == 'BLOCKED'
    assert result['calls'][0]['state'] == 'ZERO_LENGTH_EFFECT_CONFLICT'


def test_native_zero_handle_cannot_borrow_another_threads_stream_binding():
    value = sample()
    value['stream_bindings'][0]['thread_id'] = 10
    with pytest.raises(ValueError, match='STREAM_MAPPING'):
        review(value)


def test_callback_correlation_reuse_cannot_reuse_the_same_api_and_effect():
    value = sample()
    repeated = deepcopy(value['callback_events'])
    for event in repeated:
        event['seq'] += 4
        event['time_ns'] += 40
        event['call_id'] += '-reused-correlation'
    value['callback_events'] += repeated
    with pytest.raises(ValueError, match='CORRELATION_REUSE'):
        review(value)


def test_driver_correlation_reuse_across_threads_is_not_disambiguated_by_thread():
    value = sample()
    repeated = deepcopy(value['callback_events'])
    for event in repeated:
        event.update(seq=event['seq']+4, time_ns=event['time_ns']+40, thread_id=10,
                     call_id=event['call_id']+'-other-thread')
        if event['domain'] == 'RUNTIME': event['correlation_id'] = 101
    value['callback_events'] += repeated
    value['api_records'] += [dict(record, thread_id=10, record_id=record['record_id']+'-other-thread',
                                 correlation_id=101 if record['domain'] == 'RUNTIME' else 201)
                             for record in deepcopy(value['api_records'])]
    value['stream_bindings'].append(dict(value['stream_bindings'][0], thread_id=10))
    with pytest.raises(ValueError, match='CORRELATION_REUSE'):
        review(value)


def test_zero_zero_device_timestamps_are_unknown_even_with_claimed_known_flag():
    value = sample()
    value['device_effects'][0].update(start_ns=0, end_ns=0)
    assert review(value)['calls'][0]['state'] == 'DEVICE_EFFECT_CONFLICT'


def test_multiple_effects_cannot_be_qualified_by_summing_bytes():
    value = sample()
    value['device_effects'][0]['bytes'] = 32
    value['device_effects'].append(dict(value['device_effects'][0], record_id='effect-2'))
    assert review(value)['calls'][0]['state'] == 'DEVICE_EFFECT_CONFLICT'


def test_actual_json_file_round_trip_does_not_upgrade_role(tmp_path):
    from scripts.memset_parameter_prototype import review_file
    source = tmp_path/'cpu-evidence.json'
    source.write_text(json.dumps(sample()), encoding='utf-8')
    before = source.read_bytes()
    result = review_file(source)
    assert result['calls'][0]['count'] == 64 and source.read_bytes() == before
    source.write_text(json.dumps(dict(sample(), role='FORMAL')), encoding='utf-8')
    with pytest.raises(ValueError, match='ROLE'):
        review_file(source)


@pytest.fixture(scope='module')
def cpu_native(tmp_path_factory):
    include = os.environ.get('MEMSET_CUPTI_INCLUDE')
    cuda_include = os.environ.get('MEMSET_CUDA_INCLUDE')
    cuda_crt_include = os.environ.get('MEMSET_CUDA_CRT_INCLUDE')
    compiler = os.environ.get('MEMSET_CPU_COMPILER')
    if not all([include, cuda_include, cuda_crt_include, compiler]):
        pytest.skip('Native CPU ABI test requires explicitly pinned CUDA12.4 SDK and MSVC; no CUDA runtime')
    root = Path(__file__).resolve().parents[1]
    build = tmp_path_factory.mktemp('native-copy')
    command = [compiler, '/nologo', '/EHsc', '/std:c++17', '/W4', '/WX', '/MD', '/utf-8',
               '/I'+include, '/I'+cuda_include, '/I'+cuda_crt_include,
               str(root/'scripts/prototypes/memset_callback_copy.cpp'),
               '/Fe:'+str(build/'cpu_copy.exe'), '/Fo:'+str(build/'cpu_copy.obj')]
    compile_env = os.environ.copy()
    # CL/_CL_ are compiler argument injection, not executable identity. The
    # compiler is selected explicitly above; no incidental user flags are used.
    compile_env.pop('CL', None)
    compile_env.pop('_CL_', None)
    done = subprocess.run(command, cwd=build, env=compile_env, capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stdout + done.stderr
    return build/'cpu_copy.exe'


@pytest.mark.parametrize('case', ['zero', 'positive', 'large', 'failed', 'missing_params', 'missing_return'])
def test_native_sdk_parameter_copy_uses_real_struct_without_cuda(cpu_native, case):
    done = subprocess.run([str(cpu_native), case], capture_output=True, text=True, timeout=10)
    assert done.returncode == 0, done.stderr
    result = json.loads(done.stdout)
    assert result['cupti_api_version'] == 22
    assert result['cuda_calls'] == 0 and result['cupti_calls'] == 0
    if case == 'missing_params': assert result['error'] == 'PARAMETERS_UNKNOWN'
    elif case == 'missing_return': assert result['error'] == 'RETURN_UNKNOWN'
    else:
        assert result['stream_handle'] == 0 and result['value'] == 7
        assert result['count'] == {'zero': 0, 'positive': 1536, 'large': 2**63 + 7, 'failed': 1536}[case]
        assert result['return_code'] == (2 if case == 'failed' else 0)
        assert result['copy_survives_parameter_mutation'] is True
