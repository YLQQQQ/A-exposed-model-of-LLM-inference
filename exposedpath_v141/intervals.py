"""Deterministic integer half-open interval primitives.

The functions in this module deliberately have no knowledge of the research
domain.  Intervals use the usual half-open form ``[start, end)`` and all
coordinates are non-negative integers.
"""

from __future__ import annotations

from collections.abc import Iterable


Interval = tuple[int, int]


def _validate_integer(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{label} must be an integer")
    if value < 0:
        raise ValueError(f"{label} must be non-negative")
    return value


def _validate_interval(interval: Interval, label: str = "interval") -> Interval:
    try:
        start, end = interval
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{label} must contain exactly two endpoints") from exc
    start = _validate_integer(start, f"{label}.start")
    end = _validate_integer(end, f"{label}.end")
    if start > end:
        raise ValueError(f"{label}.start must not exceed {label}.end")
    return start, end


def intersect_interval(left: Interval, right: Interval) -> Interval | None:
    """Return the positive-length intersection of two half-open intervals."""

    left_start, left_end = _validate_interval(left, "left")
    right_start, right_end = _validate_interval(right, "right")
    start = max(left_start, right_start)
    end = min(left_end, right_end)
    if start >= end:
        return None
    return start, end


def clip_intervals(
    intervals: Iterable[Interval], window: Interval
) -> tuple[Interval, ...]:
    """Clip each interval to ``window`` and return positive ranges in order."""

    validated_window = _validate_interval(window, "window")
    clipped: list[Interval] = []
    for index, interval in enumerate(intervals):
        validated = _validate_interval(interval, f"intervals[{index}]")
        intersection = intersect_interval(validated, validated_window)
        if intersection is not None:
            clipped.append(intersection)
    clipped.sort()
    return tuple(clipped)


def union_intervals(intervals: Iterable[Interval]) -> tuple[Interval, ...]:
    """Return the sorted union, merging overlapping and adjacent ranges."""

    validated = [
        _validate_interval(interval, f"intervals[{index}]")
        for index, interval in enumerate(intervals)
    ]
    validated = [interval for interval in validated if interval[0] < interval[1]]
    if not validated:
        return ()
    validated.sort()

    merged: list[list[int]] = [[validated[0][0], validated[0][1]]]
    for start, end in validated[1:]:
        current = merged[-1]
        if start <= current[1]:
            current[1] = max(current[1], end)
        else:
            merged.append([start, end])
    return tuple((start, end) for start, end in merged)


def interval_length(intervals: Iterable[Interval]) -> int:
    """Return the length of the union without enumerating individual points."""

    return sum(end - start for start, end in union_intervals(intervals))


def atomic_segments(window: Interval, boundaries: Iterable[int]) -> tuple[Interval, ...]:
    """Split ``window`` at unique boundaries that lie strictly inside it."""

    start, end = _validate_interval(window, "window")
    validated_boundaries = {
        _validate_integer(boundary, f"boundaries[{index}]")
        for index, boundary in enumerate(boundaries)
    }
    if start == end:
        return ()

    cuts = [start]
    cuts.extend(sorted(boundary for boundary in validated_boundaries if start < boundary < end))
    cuts.append(end)
    return tuple((left, right) for left, right in zip(cuts, cuts[1:]) if left < right)
