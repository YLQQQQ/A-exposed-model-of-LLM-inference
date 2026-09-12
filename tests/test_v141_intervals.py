"""Tests for deterministic integer half-open interval primitives."""

from __future__ import annotations

import pytest

from exposedpath_v141.intervals import (
    atomic_segments,
    clip_intervals,
    intersect_interval,
    interval_length,
    union_intervals,
)


def test_intersect_interval_uses_half_open_boundaries():
    assert intersect_interval((2, 8), (5, 11)) == (5, 8)
    assert intersect_interval((2, 5), (5, 11)) is None
    assert intersect_interval((2, 2), (0, 10)) is None


def test_union_merges_adjacent_nested_duplicate_and_overlapping_ranges():
    intervals = [(10, 15), (0, 4), (4, 10), (3, 12), (10, 15), (6, 8)]
    assert union_intervals(intervals) == ((0, 15),)


def test_union_merges_overlapping_ranges_from_multiple_threads_deterministically():
    intervals = [(30, 40), (5, 20), (12, 35), (18, 25), (0, 5)]
    assert union_intervals(reversed(intervals)) == ((0, 40),)


def test_clip_intervals_intersects_and_sorts_records():
    intervals = [(9, 14), (0, 3), (3, 7), (5, 12), (15, 20)]
    assert clip_intervals(intervals, (2, 10)) == (
        (2, 3),
        (3, 7),
        (5, 10),
        (9, 10),
    )


def test_empty_intervals_are_ignored_and_do_not_create_length():
    assert union_intervals([(2, 2), (5, 5)]) == ()
    assert clip_intervals([(1, 1), (2, 6)], (1, 5)) == ((2, 5),)
    assert interval_length([(0, 0), (2, 4), (3, 8)]) == 6


@pytest.mark.parametrize(
    "operation, args",
    [
        (intersect_interval, ((4, 3), (0, 1))),
        (intersect_interval, ((-1, 3), (0, 1))),
        (clip_intervals, ([(0, 2), (4, 3)], (0, 5))),
        (clip_intervals, ([(0, 2)], (-1, 5))),
        (union_intervals, ([(0, 2), (3, -1)],)),
        (interval_length, ([(0, 2), (-1, 3)],)),
        (atomic_segments, ((4, 3), [0, 1])),
        (atomic_segments, ((0, 3), [-1, 1])),
    ],
)
def test_public_operations_reject_reverse_or_negative_time(operation, args):
    with pytest.raises(ValueError):
        operation(*args)


def test_public_operations_reject_non_integer_endpoints():
    with pytest.raises(TypeError):
        intersect_interval((0.0, 2), (0, 2))
    with pytest.raises(TypeError):
        union_intervals([(0, True)])
    with pytest.raises(TypeError):
        atomic_segments((0, 2), [1.5])


def test_atomic_segments_are_unique_gap_free_and_include_window_edges():
    assert atomic_segments((10, 20), [0, 10, 10, 13, 17, 20, 25]) == (
        (10, 13),
        (13, 17),
        (17, 20),
    )
    assert atomic_segments((10, 10), [10, 11]) == ()


def test_interval_length_uses_union_length_for_overlapping_ranges():
    assert interval_length([(0, 10), (2, 4), (8, 12), (20, 25)]) == 17
