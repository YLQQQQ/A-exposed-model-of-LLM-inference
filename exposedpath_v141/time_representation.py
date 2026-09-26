"""Explicit A/B representation policy; never changes trace coordinates.

Context-local (not process-global) selection preserves the legacy default.
Only versioned file readers/writers or explicit deterministic callers select 0.3.
"""
from contextlib import contextmanager
from contextvars import ContextVar

LEGACY = 'exposedpath-ab/0.2.0'
SIGNED = 'exposedpath-ab/0.3.0'
CLOSED_PRIOR = 'exposedpath-ab/0.4.0'
INT64_MIN, INT64_MAX, UINT64_MAX = -(2**63), 2**63-1, 2**64-1
_version = ContextVar('ab_time_representation', default=LEGACY)


@contextmanager
def time_representation(version):
    if version not in (LEGACY, SIGNED, CLOSED_PRIOR):
        raise ValueError('TIME_REPRESENTATION_VERSION_UNSUPPORTED')
    token = _version.set(version)
    try:
        yield
    finally:
        _version.reset(token)


def signed_time():
    return _version.get() in (SIGNED, CLOSED_PRIOR)


def timestamp(value, label):
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f'{label}: integer timestamp required')
    if signed_time():
        if not INT64_MIN <= value <= INT64_MAX:
            raise ValueError(f'{label}: signed-int64 timestamp out of range')
    elif value < 0:
        raise ValueError(f'{label}: legacy timestamp must be non-negative')
    return value


def duration(value, label):
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f'{label}: non-negative integer duration required')
    if signed_time() and value > UINT64_MAX:
        raise ValueError(f'{label}: uint64 duration out of range')
    return value


def hidden_lower_bound():
    return INT64_MIN if signed_time() else 0
