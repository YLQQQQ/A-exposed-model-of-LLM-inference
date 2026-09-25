"""Independent integer-coordinate expectations; no profiler or GPU."""
import importlib
import pytest


def policy():
    spec = importlib.util.find_spec('exposedpath_v141.time_representation')
    assert spec is not None, 'explicit versioned timestamp/duration policy missing'
    return importlib.import_module('exposedpath_v141.time_representation')


def test_signed_intervals_and_legacy_isolation():
    p = policy()
    from exposedpath_v141.intervals import interval_length, intersect_interval
    with p.time_representation('exposedpath-ab/0.3.0'):
        assert interval_length([(-20, -10), (-15, 5)]) == 25
        assert intersect_interval((-20, 5), (-10, 10)) == (-10, 5)
        assert interval_length([(-2, -2)]) == 0
        assert interval_length([(-(2**63), 2**63-1)]) == 2**64-1
        with pytest.raises(ValueError):
            interval_length([(3, -1)])
    with pytest.raises(ValueError):
        interval_length([(-2, 1)])


@pytest.mark.parametrize('value', [None, True, 1.5, -(2**63)-1, 2**63])
def test_timestamp_invalid_not_coerced(value):
    p = policy()
    with p.time_representation('exposedpath-ab/0.3.0'):
        with pytest.raises((ValueError, TypeError)):
            p.timestamp(value, 'time')


def test_unsigned_duration_bounds_and_unknown_version():
    p = policy()
    with p.time_representation('exposedpath-ab/0.3.0'):
        assert p.duration(2**64-1, 'duration') == 2**64-1
        for bad in (-1, 2**64, None, True):
            with pytest.raises(ValueError):
                p.duration(bad, 'duration')
    with pytest.raises(ValueError, match='VERSION'):
        with p.time_representation('exposedpath-ab/future'):
            pass


def signed_inputs(tmp_path, monkeypatch, shift=-160, return_sources=False):
    import sqlite3
    from test_gate8_boundaries import boundary_sources, project
    inputs, host = boundary_sources(tmp_path, monkeypatch)
    with sqlite3.connect(inputs[0]) as conn:
        conn.execute('UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET start=140,end=170')
        conn.execute("INSERT INTO StringIds VALUES (20,'cudaLaunchKernel')")
        conn.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME(start,end,eventClass,globalTid,correlationId,nameId,returnValue) SELECT 110,115,0,globalTid,6,20,0 FROM CUPTI_ACTIVITY_KIND_RUNTIME LIMIT 1')
        conn.execute('UPDATE CUPTI_ACTIVITY_KIND_SYNCHRONIZATION SET start=145,end=165')
        conn.execute('UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET start=130,end=160')
        for table in ('CUPTI_ACTIVITY_KIND_MEMCPY', 'CUPTI_ACTIVITY_KIND_MEMSET', 'CUPTI_ACTIVITY_KIND_CUDA_EVENT'):
            conn.execute(f'DELETE FROM {table}')
        for table in ('NVTX_EVENTS', 'CUPTI_ACTIVITY_KIND_RUNTIME', 'CUPTI_ACTIVITY_KIND_SYNCHRONIZATION', 'CUPTI_ACTIVITY_KIND_KERNEL'):
            conn.execute(f'UPDATE {table} SET start=start+?,end=end+?', (shift, shift))
    return (inputs, host) if return_sources else project(tmp_path, inputs, host)


def test_signed_producer_projection_ab_keeps_hidden_progress(monkeypatch, tmp_path):
    p = policy()
    canonical, scope = signed_inputs(tmp_path, monkeypatch)
    from exposedpath_v141.gate8_scope import build_projected_ab_inputs
    from exposedpath_v141.a_accounting import calculate_a_windows
    from exposedpath_v141.b_provenance import calculate_b_syncs
    with p.time_representation(p.SIGNED):
        inputs = build_projected_ab_inputs(canonical, scope)
        a, b = calculate_a_windows(inputs), calculate_b_syncs(inputs)
    assert (a[0]['window_start_ns'], a[0]['window_end_ns']) == (-60, 140)
    assert [a[0][k] for k in ('A_host_path_ns','A_cuda_api_ns','A_device_wait_ns','A_sync_residual_ns','A_unattributed_ns')] == [165,5,20,10,0]
    assert (b[0]['sync_start_ns'], b[0]['sync_end_ns'], b[0]['terminal']['end_ns']) == (-20,10,0)
    assert [b[0][k] for k in ('wait_set_hidden_union_ns','wait_set_exposed_union_ns','terminal_pre_sync_ns','terminal_overlap_sync_ns','sync_return_tail_ns')] == [10,20,10,20,10]


def test_signed_schema_explicit_version_and_duration_range():
    from pathlib import Path
    import json
    from jsonschema import Draft202012Validator
    path = Path('docs/v1_4_1/contracts/ab_schema_v0_3.json')
    assert path.is_file(), 'new time representation must not mutate frozen 0.2 schema'
    schema = json.loads(path.read_text())
    Draft202012Validator.check_schema(schema)
    props = schema['$defs']['a_window_record']['properties']
    Draft202012Validator(props['window_start_ns']).validate(-(2**63))
    Draft202012Validator(props['T_window_ns']).validate(2**64-1)
    assert not Draft202012Validator(props['T_window_ns']).is_valid(2**64)
    assert not Draft202012Validator(props['window_start_ns']).is_valid(-(2**63)-1)
    old = json.loads(Path('docs/v1_4_1/contracts/ab_schema_v0_2.json').read_text())
    assert not Draft202012Validator(old['$defs']['a_window_record']['properties']['window_start_ns']).is_valid(-1)


def test_signed_file_roundtrip_and_derived_explicit_version(monkeypatch, tmp_path):
    from exposedpath_v141.s_bundle import analyze_canonical_to_s
    from exposedpath_v141.ab_bundle import analyze_ab, load_ab_bundle
    from exposedpath_v141.derived import derive_exposure, load_derived_bundle
    canonical, scope = signed_inputs(tmp_path, monkeypatch)
    s = analyze_canonical_to_s(canonical, tmp_path/'s', scope_manifest=scope)
    ab = analyze_ab(canonical, s, tmp_path/'ab', scope_manifest=scope)
    loaded = load_ab_bundle(ab, canonical_manifest=canonical, s_manifest=s)
    assert loaded['manifest']['schema_version'] == 'exposedpath-ab/0.3.0'
    from test_gate8_identity import sha
    assert loaded['manifest']['source']['scope_manifest_sha256'] == sha(scope).upper()
    assert loaded['a_window_records'][0]['window_start_ns'] == -60
    d = derive_exposure(ab, tmp_path/'derived')
    result = load_derived_bundle(d, ab_manifest=ab)
    assert result['manifest']['schema_version'] == 'exposedpath-derived/0.3.0'
    assert result['manifest']['input_schema_version'] == 'exposedpath-ab/0.3.0'
    assert result['manifest']['measurement_validity'] == 'NOT_ASSESSED'
    assert result['manifest']['validation_role'] == 'LOCAL_DETERMINISTIC_ONLY'
    full = next(r for r in result['d_window_records'] if r['request_id']=='request-0' and r['phase']=='full_request')
    assert full['D_margin_ns'] == -150
    assert full['D_score'] == -150/190
    assert result['manifest']['research_eligibility']['q0_status'] == 'NOT_RUN'
    import json
    original = ab.read_text()
    bad = json.loads(original)
    bad['schema_version'] = 'exposedpath-ab/unknown'
    ab.write_text(json.dumps(bad))
    with pytest.raises(ValueError):
        load_ab_bundle(ab)
    ab.write_text(original)
    bad = json.loads(original)
    bad['quality'] = {'status':'FAIL_CLOSED','reasons':['SYNTHETIC_MISSING_EVIDENCE']}
    ab.write_text(json.dumps(bad))
    with pytest.raises(ValueError, match='UPSTREAM'):
        derive_exposure(ab,tmp_path/'invalid-derived')
    ab.write_text(original)
    derived_doc = json.loads(d.read_text())
    derived_doc['input_schema_version'] = 'exposedpath-ab/0.2.0'
    d.write_text(json.dumps(derived_doc))
    with pytest.raises(ValueError):
        load_derived_bundle(d,ab_manifest=ab)


def test_int64_extremes_and_empty_window_survive_file_roundtrip(monkeypatch,tmp_path):
    from exposedpath_v141.s_bundle import analyze_canonical_to_s
    from exposedpath_v141.ab_bundle import analyze_ab, load_ab_bundle
    from tests.test_v141_derived import _write_a_records
    from copy import deepcopy
    canonical, scope = signed_inputs(tmp_path,monkeypatch)
    s=analyze_canonical_to_s(canonical,tmp_path/'s',scope_manifest=scope)
    ab=analyze_ab(canonical,s,tmp_path/'ab',scope_manifest=scope)
    records=list(load_ab_bundle(ab)['a_window_records'])
    # Serialization/validation test only: these replacement records are not
    # asserted to match the original fixture's Raw window.
    base=deepcopy(next(r for r in records if r['request_id']=='request-1' and r['phase']=='full_request'))
    base.update(window_start_ns=-(2**63),window_end_ns=2**63-1,T_window_ns=2**64-1,A_host_path_ns=2**64-1)
    _write_a_records(ab,[base])
    assert load_ab_bundle(ab)['a_window_records'][0]['T_window_ns']==2**64-1
    base.update(window_start_ns=-7,window_end_ns=-7,T_window_ns=0,A_host_path_ns=0)
    _write_a_records(ab,[base])
    assert load_ab_bundle(ab)['a_window_records'][0]['T_window_ns']==0
    for change in ({'window_end_ns':-8},{'window_start_ns':-(2**63)-1},{'A_host_path_ns':2**64},{'window_start_ns':None}):
        _write_a_records(ab,[{**base,**change}])
        with pytest.raises(ValueError):
            load_ab_bundle(ab)
