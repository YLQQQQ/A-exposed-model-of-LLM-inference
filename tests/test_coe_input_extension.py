"""Finite 256 input extension; all OS/device/collector boundaries are CPU doubles."""
from copy import deepcopy
import json

import pytest

from tests.test_coe_input_pilot import row


VERSION = 'COE-INPUT-P-PILOT/0.3'
ORDERS = [[256, 512, 2048, 1024], [512, 1024, 256, 2048],
          [1024, 2048, 512, 256], [2048, 256, 1024, 512]]


def api():
    from exposedpath import coe_input_pilot
    return coe_input_pilot


def binding(length=256):
    return next(b for b in api().schedule('cpu-extension', 'a'*40, version=VERSION)
                if b['input_tokens'] == length)


def test_four_point_schedule_is_finite_and_position_balanced():
    m = api()
    bs = m.schedule('cpu-extension', 'a'*40, version=VERSION)
    assert [b['input_tokens'] for b in bs] == sum(ORDERS, [])
    assert len({b['run_id'] for b in bs}) == 16
    for position in range(1, 5):
        assert sorted(b['input_tokens'] for b in bs if b['position'] == position) == [256, 512, 1024, 2048]
    assert len(m.schedule('old', 'a'*40)) == 8
    assert len(m.schedule('old-mid', 'a'*40, version=m.MIDPOINT_VERSION)) == 9
    for version in (m.VERSION, m.MIDPOINT_VERSION, 'COE-INPUT-P-PILOT/0.4'):
        b = binding(); b['version'] = version
        with pytest.raises(ValueError, match='COE_INPUT_BINDING'):
            m.validate_binding(b)


def test_256_matrix_identity_has_independent_literal_digests_and_rejects_tampering(tmp_path):
    from exposedpath import coe_pilot
    from tests.test_gate8_identity import write_json, sha
    m = api()
    seed = write_json(tmp_path/'seed.json', dict(fixed_input_tokens=512,
        samples=[dict(sample_index=0, input_ids=list(range(3, 35))*16, attention_mask=[1]*512)]))
    paths = m.make_inputs(seed, sha(seed), tmp_path/'inputs', version=VERSION)
    assert set(paths) == {256, 512, 1024, 2048}
    p = json.loads(paths[256].read_text())
    assert p['samples'][0]['input_ids'] == list(range(3, 35))*8
    expected = dict(schema_version='coe-input-axis-identity/0.3.0', shape=[1, 256], sample_indices=[0],
        input_ids_sha256='fd4064e87c5bf79f04475d4294cb4d76a76d004654689565e6c64392604e01e0',
        attention_mask_sha256='84f8088ae6128f1785dfb442ea8c1e65cfa6a1bf8ee48751c7b02d4f79e3c4c3',
        batch_sha256='aa7c39c661b5fdec094860e503db8cd3b7b0700c7dbe5bfa8be62c187b5dac88',
        algorithm='SHA256_COMPACT_UTF8_JSON_IN_ORDER')
    config = dict(model_type='qwen2', vocab_size=100, max_position_embeddings=4096)
    assert coe_pilot.validate_input(p, config, 1, binding=binding()) == expected
    for version in (m.VERSION, m.MIDPOINT_VERSION):
        with pytest.raises(ValueError, match='COE_INPUT_INPUT_SHAPE'):
            m.input_identity(p, version=version)
    bad = deepcopy(p); bad['samples'][0]['input_ids'][250] = 99
    assert m.input_identity(bad, version=VERSION)['batch_sha256'] != expected['batch_sha256']
    with pytest.raises(ValueError, match='COE_INPUT_TOKEN_RANGE_OR_CONSTRUCTION'):
        m.validate_input(bad, config, 1, version=VERSION)
    bad = deepcopy(p); bad['samples'][0]['attention_mask'][7] = 0
    with pytest.raises(ValueError, match='COE_INPUT_MASK'):
        m.input_identity(bad, version=VERSION)
    with pytest.raises(ValueError, match='COE_INPUT_MODEL_CONFIG'):
        m.validate_input(p, {**config, 'max_position_embeddings':257}, 1, version=VERSION)
    with pytest.raises(ValueError, match='COE_INPUT_SEED_HASH'):
        m.make_inputs(seed, '0'*64, tmp_path/'bad-seed', version=VERSION)


def test_256_prepared_file_schema_and_role_remain_strict(tmp_path):
    from pathlib import Path
    from exposedpath import coe_pilot
    from tests.test_gate8_identity import write_json, sha
    m = api(); b = binding()
    prompt = dict(fixed_input_tokens=256,
                  samples=[dict(sample_index=0, input_ids=[7]*256, attention_mask=[1]*256)])
    model = tmp_path/'model'; model.mkdir()
    write_json(model/'config.json', dict(model_type='qwen2', vocab_size=100, max_position_embeddings=4096))
    write_json(tmp_path/'prompt.json', prompt)
    root = Path(__file__).resolve().parents[1]
    mf = {**m.minimal_fields(b), **dict(runner_git_commit='a'*40, runner_git_dirty=False,
        coe_input=m.input_identity(prompt, version=VERSION), target_python={}, isolated_preflight_version='cpu',
        model_id=str(model), prompt_tokens_sha256=sha(tmp_path/'prompt.json'),
        runner_source_sha256=sha(root/'exposedpath/runner.py'),
        preparation_source_sha256=sha(root/'exposedpath/observation_preparation.py'),
        input_pilot_source_sha256=sha(root/'exposedpath/coe_input_pilot.py'))}
    coe_pilot.validate_prepared(mf, tmp_path, root)
    bad = deepcopy(mf); bad['coe_input']['schema_version'] = 'coe-input-axis-identity/0.2.0'
    with pytest.raises(ValueError, match='COE_INPUT_INPUT_BINDING'):
        coe_pilot.validate_prepared(bad, tmp_path, root)
    bad = deepcopy(mf); bad.update(run_role='ENGINEERING', data_role='Engineering')
    with pytest.raises(ValueError, match='COE_INPUT_DECLARATION'):
        coe_pilot.validate_prepared(bad, tmp_path, root)
    prompt['samples'][0]['input_ids'][249] = 8
    write_json(tmp_path/'prompt.json', prompt)
    with pytest.raises(ValueError, match='COE_PILOT_INPUT_HASH'):
        coe_pilot.validate_prepared(mf, tmp_path, root)


def test_four_point_signed_references_preserve_negative_zero_and_unknown():
    m = api()
    rows = [row(binding(n), q, g) for n, q, g in
            [(256, 2, 4), (512, 10, 20), (1024, 9, 10), (2048, 12, 30)]]
    r = m.block_contrasts(rows)['per_token'][0]
    assert r['R_exact'] == dict(numerator=-3, denominator=1)
    assert r['coe_over_phase_gpu'] == {256:0.5, 512:0.5, 1024:0.9, 2048:0.4}
    assert [(x['lower_input'], x['higher_input'], x['delta_coe_ns'], x['R_ns'])
            for x in r['input_contrasts']] == [(256,512,8,0), (512,1024,-1,4), (1024,2048,3,-15)]
    rows[0]['result']['windows'][0]['baseline']['gpu_activity']['union_ns'] = 0
    r = m.block_contrasts(rows)['per_token'][0]
    assert r['input_contrasts'][0]['R_ns'] is None and r['R_ns'] == -3
    rows[2]['result']['windows'][0]['baseline']['gpu_activity']['status'] = 'UNKNOWN'
    r = m.block_contrasts(rows)['per_token'][0]
    assert r['R_ns'] == -3 and all(x['R_ns'] is None for x in r['input_contrasts'])
    with pytest.raises(ValueError, match='INCOMPLETE_BLOCK'):
        m.block_contrasts(rows[:3])


def test_1024_evidence_failure_stops_new_four_point_plan_without_stitching(tmp_path):
    m = api(); seen = []
    def collect(b, out):
        seen.append(b['input_tokens'])
        if b['input_tokens'] == 1024:
            raise ValueError('ENGINEERING_SCOPE_SUBMIT_MAPPING')
        return row(b, 0, 20)['result']
    r = m.run_batch('cpu-extension', 'a'*40, tmp_path/'batch', collect, version=VERSION)
    assert seen == [256, 512, 2048, 1024]
    assert [s['status'] for s in r['runs']] == ['COMPLETE']*3 + ['BLOCKED'] + ['NOT_RUN']*12
    assert r['blocks'] == [] and r['incomplete_blocks'] == [1, 2, 3, 4]
    assert r['status'] == 'BLOCKED' and r['model_process_budget'] == r['profile_budget'] == 16
    saved = json.loads((tmp_path/'batch/batch_report.json').read_text())
    assert saved['runs'][3]['error'] == 'ValueError: ENGINEERING_SCOPE_SUBMIT_MAPPING'


def test_four_complete_blocks_keep_legal_zero_and_reverse_values(tmp_path):
    m = api(); seen = []
    def collect(b, out):
        seen.append(b['run_id'])
        return row(b, {256:2, 512:10, 1024:0, 2048:8}[b['input_tokens']], 20)['result']
    r = m.run_batch('cpu-extension', 'a'*40, tmp_path/'complete', collect, version=VERSION)
    assert len(seen) == 16 and len(set(seen)) == 16
    assert len(r['blocks']) == 4 and r['incomplete_blocks'] == []
    assert r['status'] == 'FIXED_SIXTEEN_INPUT_PILOT_COMPLETE_STOP_FOR_REVIEW'
    assert all(x['per_token'][0]['delta_coe_ns'] == x['per_token'][0]['R_ns'] == -2 for x in r['blocks'])


@pytest.mark.parametrize('damage', [None, 'drain', 'dependency', 'future_gap', 'token'])
def test_256_actual_producer_canonical_both_tokens_and_candidate_budget(tmp_path, monkeypatch, damage):
    from tests import test_coe_input_pilot as old
    monkeypatch.setattr(old, 'binding', binding)
    old.test_real_producer_canonical_both_tokens_and_budget(tmp_path, monkeypatch, 256, damage)


def test_256_actual_prepare_seal_and_collector_boundary(tmp_path, monkeypatch):
    from tests import test_coe_input_pilot as old
    monkeypatch.setattr(old, 'binding', binding)
    old.test_actual_prepare_seal_and_profile_argv(tmp_path, monkeypatch, 256)


@pytest.mark.parametrize('damage', [None, 'hash', 'version', 'identity', 'exit', 'budget'])
def test_256_real_collection_consumer_keeps_strict_lineage(tmp_path, monkeypatch, damage):
    from tests import test_coe_input_pilot as old
    monkeypatch.setattr(old, 'binding', binding)
    old.test_real_collection_consumer_checks_both_tokens_and_preview(tmp_path, monkeypatch, damage)


def test_four_point_proposal_cannot_start_through_old_delivery_entry(tmp_path):
    from scripts.observation_preparation_batch import run
    with pytest.raises(ValueError, match='OPT_IN_REQUIRED'):
        run({}, tmp_path/'default', input_pilot=True)
    with pytest.raises(ValueError, match='DELIVERY_CONTRACT'):
        run(dict(schema_version='coe-input-pilot-delivery/0.3', input_contract_version=VERSION,
                 model_process_budget=16, profile_budget=16, commit='a'*40, analysis_commit='a'*40),
            tmp_path/'explicit', execute=True, input_pilot=True)
