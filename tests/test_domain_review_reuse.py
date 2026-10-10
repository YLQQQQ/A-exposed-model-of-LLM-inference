"""A reuse session must bind actual files, not trust a caller-filled result."""
import json
import pytest


def files(tmp_path, monkeypatch):
    from test_n1_model_domain import source
    from exposedpath_v141.gate9_domain import process_domain
    receipt, execution, bridge = source(tmp_path, monkeypatch, 'Vsync')
    domain = process_domain(receipt, execution, tmp_path/'domain', bridge_path=bridge)
    return domain, receipt, execution, bridge


def test_same_run_reuses_verified_domain_but_recomputes_baseline(tmp_path, monkeypatch):
    from exposedpath_v141 import gate9_domain as d, activity_baseline as b
    domain, receipt, execution, bridge = files(tmp_path, monkeypatch)
    baseline = b.write_baseline(domain, receipt, execution, tmp_path/'baseline', bridge_path=bridge)
    expected = b.load_baseline(baseline, domain, receipt, execution, bridge_path=bridge)
    original = d._calculate
    calls = []
    def counted(*args, **kwargs):
        calls.append(args)
        return original(*args, **kwargs)
    monkeypatch.setattr(d, '_calculate', counted)
    with d.DomainReview() as review:
        result = review.load(domain, receipt, execution, bridge_path=bridge)
        assert review._value == {'status': 'QUALITY_CHECK_PASSED_NOT_QUALIFICATION'}
        # A consumer mutation cannot change the verified value.
        result['status'] = 'tampered'
        actual = b.load_baseline(baseline, domain, receipt, execution,
                                 bridge_path=bridge, domain_review=review)
        assert actual == expected
        assert review.load(domain, receipt, execution, bridge_path=bridge)['status'] == 'QUALITY_CHECK_PASSED_NOT_QUALIFICATION'
    assert len(calls) == 1
    with pytest.raises(ValueError, match='REVIEW_CLOSED'):
        review.load(domain, receipt, execution, bridge_path=bridge)
    assert review._value is None and review._snapshot is None


@pytest.mark.parametrize('damage', ['receipt', 'execution', 'bridge', 'domain', 'canonical', 'extra', 'missing', 'different_run'])
def test_wrong_or_changed_evidence_cannot_reuse_verification(tmp_path, monkeypatch, damage):
    from exposedpath_v141.gate9_domain import DomainReview
    domain, receipt, execution, bridge = files(tmp_path, monkeypatch)
    with DomainReview() as review:
        review.load(domain, receipt, execution, bridge_path=bridge)
        if damage == 'different_run':
            other = tmp_path/'other_execution.json'
            other.write_bytes(execution.read_bytes())
            execution = other
        elif damage == 'extra':
            (domain.parent/'extra.json').write_text('{}')
        else:
            target = {'receipt': receipt, 'execution': execution, 'bridge': bridge,
                      'domain': domain, 'canonical': domain.parent/'canonical/canonical_manifest.json',
                      'missing': bridge}[damage]
            if damage == 'missing': target.unlink()
            else: target.write_bytes(target.read_bytes()+b' ')
        with pytest.raises((ValueError, FileNotFoundError)):
            review.load(domain, receipt, execution, bridge_path=bridge)


def test_baseline_tamper_still_rejected_with_verified_domain(tmp_path, monkeypatch):
    from exposedpath_v141.gate9_domain import DomainReview
    from exposedpath_v141.activity_baseline import write_baseline, load_baseline
    domain, receipt, execution, bridge = files(tmp_path, monkeypatch)
    baseline = write_baseline(domain, receipt, execution, tmp_path/'baseline', bridge_path=bridge)
    value=json.loads(baseline.read_text())
    value['windows'][0]['api']['sum_ns'] += 1
    baseline.write_text(json.dumps(value))
    with DomainReview() as review:
        review.load(domain, receipt, execution, bridge_path=bridge)
        with pytest.raises(ValueError, match='FILE_SCOPE_OR_VALUES'):
            load_baseline(baseline, domain, receipt, execution, bridge_path=bridge, domain_review=review)


def test_source_changed_during_baseline_recompute_is_rejected(tmp_path, monkeypatch):
    from exposedpath_v141.gate9_domain import DomainReview
    from exposedpath_v141 import activity_baseline as b
    domain, receipt, execution, bridge = files(tmp_path, monkeypatch)
    baseline = b.write_baseline(domain, receipt, execution, tmp_path/'baseline', bridge_path=bridge)
    calculate = b.calculate
    def changed(*args, **kwargs):
        result = calculate(*args, **kwargs)
        execution.write_bytes(execution.read_bytes()+b' ')
        return result
    with DomainReview() as review:
        review.load(domain, receipt, execution, bridge_path=bridge)
        monkeypatch.setattr(b, 'calculate', changed)
        with pytest.raises(ValueError, match='REVIEW_SOURCE_CHANGED'):
            b.load_baseline(baseline, domain, receipt, execution, bridge_path=bridge, domain_review=review)


def test_registry_change_cannot_reuse_even_engineering_result(tmp_path, monkeypatch):
    from exposedpath_v141 import sync_semantics as s
    from exposedpath_v141.gate9_domain import DomainReview
    domain, receipt, execution, bridge = files(tmp_path, monkeypatch)
    registry=tmp_path/'sync_registry.json'
    from pathlib import Path
    root=Path(s.__file__).resolve().parents[1]
    registry.write_bytes((root/s._REGISTRY_PATH).read_bytes())
    monkeypatch.setattr(s,'_REGISTRY_PATH',registry)
    with DomainReview() as review:
        review.load(domain, receipt, execution, bridge_path=bridge)
        registry.write_bytes(registry.read_bytes()+b' ')
        with pytest.raises(ValueError, match='REVIEW_SOURCE_CHANGED'):
            review.load(domain, receipt, execution, bridge_path=bridge)


def test_nested_schema_change_cannot_reuse_verified_status(tmp_path, monkeypatch):
    from pathlib import Path
    from exposedpath_v141 import gate9_domain as d, sync_semantics as s
    domain, receipt, execution, bridge = files(tmp_path, monkeypatch)
    # Minimal isolated contract source root, not a second checkout. Real
    # producer/domain validation still executes; only snapshot paths change.
    root = tmp_path/'contract_source'
    module = root/'exposedpath_v141/gate9_domain.py'
    module.parent.mkdir(parents=True)
    module.write_text('# test source identity\n')
    registry = root/s._REGISTRY_PATH
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_bytes((Path(s.__file__).resolve().parents[1]/s._REGISTRY_PATH).read_bytes())
    schema = root/'docs/v1_4_1/contracts/gate8/nested_schema.json'
    schema.parent.mkdir(parents=True, exist_ok=True)
    schema.write_text('{}')
    monkeypatch.setattr(d, '__file__', str(module))
    with d.DomainReview() as review:
        review.load(domain, receipt, execution, bridge_path=bridge)
        schema.write_text('{"changed": true}')
        with pytest.raises(ValueError, match='REVIEW_SOURCE_CHANGED'):
            review.admission(domain, receipt, execution, bridge_path=bridge)


@pytest.mark.parametrize('suffix', ['-wal', '-journal'])
def test_new_sqlite_sidecar_is_not_a_sealed_cache_hit(tmp_path, monkeypatch, suffix):
    from pathlib import Path
    from exposedpath_v141.gate8_files import load_input_receipt
    from exposedpath_v141.gate9_domain import DomainReview
    domain, receipt, execution, bridge = files(tmp_path, monkeypatch)
    _, paths = load_input_receipt(receipt)
    with DomainReview() as review:
        review.load(domain, receipt, execution, bridge_path=bridge)
        Path(str(paths['sqlite'])+suffix).write_bytes(b'writer state')
        with pytest.raises(ValueError, match='UNSEALED'):
            review.load(domain, receipt, execution, bridge_path=bridge)
