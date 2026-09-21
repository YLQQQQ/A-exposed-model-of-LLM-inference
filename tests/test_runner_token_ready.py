from __future__ import annotations

from contextlib import nullcontext
from dataclasses import replace
from typing import Iterator

import pytest

from exposedpath import runner
from exposedpath.nvtx import (
    STRUCTURED_NVTX_PREFIX,
    make_n1_intervention_identity,
    make_natural_token_ready_identity,
)
from exposedpath.runner import (
    TokenReadyBoundary,
    observe_token_ready_boundary,
    token_ready_boundaries_to_records,
    validate_token_ready_boundaries,
)
from exposedpath.validation import validate_study_mode


class _FakeToken:
    def __init__(self, token_ids: list[int], events: list[str]):
        self._token_ids = token_ids
        self._events = events

    def detach(self):
        return self

    def cpu(self):
        self._events.append("host_read")
        return self

    def reshape(self, *_shape):
        return self

    def tolist(self):
        return list(self._token_ids)

    def unsqueeze(self, _dim):
        return self


class _FakeLogits:
    def __init__(self, token: _FakeToken):
        self._token = token

    def __getitem__(self, _item):
        return self

    def argmax(self, *, dim):
        assert dim == -1
        return self._token


class _FakeOutputs:
    def __init__(self, token: _FakeToken):
        self.logits = _FakeLogits(token)
        self.past_key_values = object()


class _FakeModel:
    def __init__(self, tokens: Iterator[_FakeToken]):
        self._tokens = tokens

    def __call__(self, **_kwargs):
        return _FakeOutputs(next(self._tokens))


class _FakeInput:
    shape = (1, 4)


def _identity_base() -> dict:
    return {
        "experiment_id": "exp",
        "wmpc_id": "wmpc",
        "run_id": "run",
        "run_role": "ENGINEERING",
        "pass_id": "pass1",
        "request_id": "request-0",
        "repeat_id": "0",
    }


def _clock(*values: int):
    iterator = iter(values)
    return lambda: next(iterator)


def _patch_cpu_torch(monkeypatch):
    monkeypatch.setattr(runner.torch, "inference_mode", nullcontext)
    monkeypatch.setattr(runner.torch.cuda, "synchronize", lambda: None)
    monkeypatch.setattr(runner.torch.cuda.nvtx, "range_push", lambda _label: None)
    monkeypatch.setattr(runner.torch.cuda.nvtx, "range_pop", lambda: None)


def test_first_and_later_tokens_share_host_readable_completion_boundary(monkeypatch):
    events: list[str] = []
    tokens = iter([_FakeToken([10], events), _FakeToken([11], events), _FakeToken([12], events)])
    _patch_cpu_torch(monkeypatch)

    result = runner.run_one_invocation(
        model=_FakeModel(tokens),
        input_ids=_FakeInput(),
        attention_mask=object(),
        output_len=3,
        device="cpu",
        nvtx_invocation_label="",
        nvtx_full_request_label="",
        nvtx_prefill_label="",
        nvtx_decode_label="",
        token_ready_identity_base=_identity_base(),
        clock_ns=_clock(100, 110, 120, 130),
    )

    assert events == ["host_read", "host_read", "host_read"]
    assert [b.token_index for b in result["token_ready_boundaries"]] == [0, 1, 2]
    assert [b.host_token_ids for b in result["token_ready_boundaries"]] == [(10,), (11,), (12,)]
    assert {b.sync_origin for b in result["token_ready_boundaries"]} == {"natural_token_ready"}
    assert result["inference_end_ns"] == 130


def test_eos_uses_already_host_readable_values_without_second_device_read(monkeypatch):
    events: list[str] = []
    tokens = iter([_FakeToken([10], events), _FakeToken([2], events)])
    _patch_cpu_torch(monkeypatch)

    result = runner.run_one_invocation(
        model=_FakeModel(tokens), input_ids=_FakeInput(), attention_mask=object(),
        output_len=3, device="cpu", nvtx_invocation_label="",
        nvtx_full_request_label="", nvtx_prefill_label="", nvtx_decode_label="",
        eos_token_id=2, token_ready_identity_base=_identity_base(),
        clock_ns=_clock(100, 110, 120),
    )

    assert events == ["host_read", "host_read"]
    assert result["early_eos"] is True
    assert result["actual_output_tokens"] == 2
    assert result["inference_end_ns"] == 120


def test_first_token_eos_stops_before_decode_without_second_device_read(monkeypatch):
    events: list[str] = []
    tokens = iter([_FakeToken([2], events)])
    _patch_cpu_torch(monkeypatch)

    result = runner.run_one_invocation(
        model=_FakeModel(tokens), input_ids=_FakeInput(), attention_mask=object(),
        output_len=3, device="cpu", nvtx_invocation_label="",
        nvtx_full_request_label="", nvtx_prefill_label="", nvtx_decode_label="",
        eos_token_id=2, token_ready_identity_base=_identity_base(),
        clock_ns=_clock(100, 110),
    )

    assert events == ["host_read"]
    assert result["early_eos"] is True
    assert result["actual_output_tokens"] == 1
    assert result["inference_end_ns"] == 110


def test_token_ready_helper_records_time_only_after_host_read():
    events: list[str] = []
    token = _FakeToken([7], events)

    def clock_ns():
        events.append("clock")
        return 123

    boundary = observe_token_ready_boundary(
        token, token_index=0, identity_base=_identity_base(), phase="prefill",
        clock_ns=clock_ns, emit_nvtx=False,
    )

    assert events == ["host_read", "clock"]
    assert boundary.completed_ns == 123
    assert boundary.host_token_ids == (7,)


def test_phase_ranges_close_before_boundary_validation_cleanup(monkeypatch):
    events: list[str] = []
    tokens = iter([_FakeToken([10], events), _FakeToken([11], events)])
    monkeypatch.setattr(runner.torch, "inference_mode", nullcontext)
    monkeypatch.setattr(runner.torch.cuda, "synchronize", lambda: None)
    monkeypatch.setattr(
        runner.torch.cuda.nvtx, "range_push", lambda label: events.append(f"push:{label}")
    )
    monkeypatch.setattr(runner.torch.cuda.nvtx, "range_pop", lambda: events.append("pop"))
    monkeypatch.setattr(
        runner,
        "validate_token_ready_boundaries",
        lambda *_args, **_kwargs: events.append("validate"),
    )

    clock_values = iter([100, 110, 120])

    def clock_ns():
        events.append("clock")
        return next(clock_values)

    runner.run_one_invocation(
        model=_FakeModel(tokens), input_ids=_FakeInput(), attention_mask=object(),
        output_len=2, device="cpu", nvtx_invocation_label="invocation",
        nvtx_full_request_label="full_request", nvtx_prefill_label="prefill",
        nvtx_decode_label="decode", token_ready_identity_base=_identity_base(),
        clock_ns=clock_ns,
    )

    assert events[-4:] == ["pop", "pop", "pop", "validate"]


def test_token_ready_boundaries_must_be_monotonic():
    boundaries = [
        TokenReadyBoundary(0, (1,), 110, "natural_token_ready", "device_to_host_token_ids"),
        TokenReadyBoundary(1, (2,), 120, "natural_token_ready", "device_to_host_token_ids"),
        TokenReadyBoundary(2, (3,), 120, "natural_token_ready", "device_to_host_token_ids"),
    ]
    validate_token_ready_boundaries(100, boundaries, expected_count=3)


def test_time_reversal_fails_closed():
    boundaries = [
        TokenReadyBoundary(0, (1,), 110, "natural_token_ready", "device_to_host_token_ids"),
        TokenReadyBoundary(1, (2,), 109, "natural_token_ready", "device_to_host_token_ids"),
    ]
    with pytest.raises(RuntimeError, match="not monotonic"):
        validate_token_ready_boundaries(100, boundaries, expected_count=2)


def test_missing_token_boundary_fails_closed():
    boundary = TokenReadyBoundary(
        0, (1,), 110, "natural_token_ready", "device_to_host_token_ids"
    )
    with pytest.raises(RuntimeError, match="expected 2 token-ready boundaries, got 1"):
        validate_token_ready_boundaries(100, [boundary], expected_count=2)


def test_token_ready_completion_times_are_machine_readable_in_results():
    boundaries = [
        TokenReadyBoundary(0, (10,), 110, "natural_token_ready", "device_to_host_token_ids"),
        TokenReadyBoundary(1, (11,), 120, "natural_token_ready", "device_to_host_token_ids"),
    ]
    assert token_ready_boundaries_to_records(boundaries) == [
        {
            "token_index": 0,
            "host_token_ids": [10],
            "completed_ns": 110,
            "sync_origin": "natural_token_ready",
            "token_ready_mechanism": "device_to_host_token_ids",
        },
        {
            "token_index": 1,
            "host_token_ids": [11],
            "completed_ns": 120,
            "sync_origin": "natural_token_ready",
            "token_ready_mechanism": "device_to_host_token_ids",
        },
    ]


def test_natural_and_n1_identities_are_disjoint():
    natural = make_natural_token_ready_identity(
        _identity_base(), phase="decode", token_index=1,
        callsite_id="decode.token_ready", sync_ordinal=1,
        token_ready_mechanism="device_to_host_token_ids",
    )
    intervention = make_n1_intervention_identity(
        _identity_base(), phase="decode", callsite_id="decode.n1.after_forward",
        sync_ordinal=1, intervention_variant_id="after_forward",
        intervention_ordinal=0,
    )

    assert natural["kind"] == intervention["kind"] == "sync"
    assert natural["sync_origin"] == "natural_token_ready"
    assert intervention["sync_origin"] == "n1_intervention"
    assert "intervention_variant_id" not in natural
    assert "token_index" not in intervention
    assert natural["callsite_id"] != intervention["callsite_id"]


@pytest.mark.parametrize(
    "manifest, expected_error",
    [
        ({"study_mode": "G1_NATURAL", "n1_intervention": {"intervention_variant_id": "x"}}, "forbids"),
        ({"study_mode": "G1_NATURAL", "n1_intervention": {}}, "forbids"),
        ({"study_mode": "N1_INTERVENTION", "n1_intervention": None}, "requires"),
        ({"study_mode": ["G1_NATURAL", "N1_INTERVENTION"]}, "must be one string"),
        ({"study_mode": "UNKNOWN"}, "unsupported"),
    ],
)
def test_illegal_study_mode_combinations_are_rejected(manifest, expected_error):
    errors = validate_study_mode(manifest)
    assert any(expected_error in error for error in errors)


def test_n1_execution_is_rejected_before_any_gpu_work(monkeypatch, tmp_path):
    manifest = {
        "run_id": "run",
        "experiment_id": "exp",
        "wmpc_id": "wmpc",
        "model_id": "model",
        "batch_size": 1,
        "fixed_output_tokens": 2,
        "warmup_count": 0,
        "repeat_count": 1,
        "run_role": "ENGINEERING",
        "data_role": "ENGINEERING",
        "study_mode": "N1_INTERVENTION",
    }
    monkeypatch.setattr(runner, "load_manifest", lambda _path: manifest)
    monkeypatch.setattr(
        runner, "load_model",
        lambda *_args, **_kwargs: pytest.fail("GPU/model work must not start for N1 identity-only mode"),
    )

    with pytest.raises(RuntimeError, match="N1_INTERVENTION execution is not enabled"):
        runner.execute_pass(tmp_path / "manifest.json", "pass0", tmp_path, use_nvtx=False)


def test_pass0_and_pass1_have_identical_token_ready_behavior(monkeypatch):
    events0: list[str] = []
    events1: list[str] = []
    pushes: list[str] = []
    monkeypatch.setattr(runner.torch.cuda.nvtx, "range_push", pushes.append)
    monkeypatch.setattr(runner.torch.cuda.nvtx, "range_pop", lambda: None)

    pass0 = observe_token_ready_boundary(
        _FakeToken([9], events0), token_index=0, identity_base=_identity_base(),
        phase="prefill", clock_ns=lambda: 100, emit_nvtx=False,
    )
    pass1 = observe_token_ready_boundary(
        _FakeToken([9], events1), token_index=0,
        identity_base={**_identity_base(), "pass_id": "pass1"},
        phase="prefill", clock_ns=lambda: 200, emit_nvtx=True,
    )

    assert events0 == events1 == ["host_read"]
    assert replace(pass0, completed_ns=0) == replace(pass1, completed_ns=0)
    assert len(pushes) == 1
    assert pushes[0].startswith(STRUCTURED_NVTX_PREFIX)


def test_cross_pass_parity_rejects_study_mode_mismatch():
    from exposedpath.cross_pass_validator import (
        PASS_EXECUTION_PARITY_MISMATCH,
        validate_pair,
    )

    pass0 = {"study_mode": "G1_NATURAL", "n1_intervention": None}
    pass1 = {
        "study_mode": "N1_INTERVENTION",
        "n1_intervention": {
            "sync_origin": "n1_intervention",
            "intervention_variant_id": "after_forward",
            "callsite_id": "decode.n1.after_forward",
        },
    }
    assert PASS_EXECUTION_PARITY_MISMATCH in validate_pair(pass0, pass1)


def test_cross_pass_parity_rejects_missing_study_mode_identity_on_both_sides():
    from exposedpath.cross_pass_validator import (
        PASS_EXECUTION_PARITY_MISMATCH,
        validate_pair,
    )

    legacy_pass0 = {"runner_source_sha256": "same"}
    legacy_pass1 = dict(legacy_pass0)

    assert PASS_EXECUTION_PARITY_MISMATCH in validate_pair(legacy_pass0, legacy_pass1)
