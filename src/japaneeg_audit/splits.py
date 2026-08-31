"""Deterministic split construction and hierarchical leakage validation."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from random import Random


def assert_disjoint_groups(
    train_groups: Iterable[str], test_groups: Iterable[str]
) -> None:
    """Raise when an independence group occurs in both train and test data."""
    overlap = set(train_groups).intersection(test_groups)
    if overlap:
        preview = ", ".join(sorted(overlap)[:5])
        raise ValueError(f"Train/test group leakage detected: {preview}")


def _validate_fractions(fractions: Sequence[float]) -> None:
    if len(fractions) != 3 or any(value < 0 for value in fractions):
        raise ValueError("split fractions must contain three non-negative values")
    if abs(sum(fractions) - 1.0) > 1e-9:
        raise ValueError("split fractions must sum to one")


def assign_random_windows(
    window_ids: Sequence[str],
    seed: int = 101,
    fractions: Sequence[float] = (0.8, 0.1, 0.1),
) -> dict[str, str]:
    """Assign individual windows after a seeded shuffle."""
    _validate_fractions(fractions)
    if len(set(window_ids)) != len(window_ids):
        raise ValueError("window IDs must be unique")
    shuffled = sorted(window_ids)
    Random(seed).shuffle(shuffled)
    train_stop = int(len(shuffled) * fractions[0])
    validation_stop = train_stop + int(len(shuffled) * fractions[1])
    return {
        window_id: (
            "train"
            if index < train_stop
            else "validation"
            if index < validation_stop
            else "test"
        )
        for index, window_id in enumerate(shuffled)
    }


def assign_chronological_groups(
    window_groups: Sequence[tuple[str, str]],
    fractions: Sequence[float] = (0.8, 0.1, 0.1),
) -> dict[str, str]:
    """Assign complete ordered groups, never individual windows."""
    _validate_fractions(fractions)
    window_ids = [window_id for window_id, _ in window_groups]
    if len(set(window_ids)) != len(window_ids):
        raise ValueError("window IDs must be unique")
    groups = sorted({group for _, group in window_groups})
    if len(groups) < 2:
        raise ValueError("group-held-out splitting requires at least two groups")
    train_stop = max(1, int(len(groups) * fractions[0]))
    train_stop = min(train_stop, len(groups) - 1)
    validation_stop = train_stop + int(len(groups) * fractions[1])
    validation_stop = min(validation_stop, len(groups) - 1)
    group_split = {
        group: (
            "train"
            if index < train_stop
            else "validation"
            if index < validation_stop
            else "test"
        )
        for index, group in enumerate(groups)
    }
    return {window_id: group_split[group] for window_id, group in window_groups}


def assert_group_isolation(
    assignments: dict[str, str],
    window_groups: Sequence[tuple[str, str]],
) -> None:
    """Require every group to occur in exactly one split."""
    group_splits: dict[str, set[str]] = {}
    for window_id, group in window_groups:
        if window_id not in assignments:
            raise ValueError(f"missing split assignment: {window_id}")
        group_splits.setdefault(group, set()).add(assignments[window_id])
    leaked = sorted(group for group, splits in group_splits.items() if len(splits) > 1)
    if leaked:
        raise ValueError(f"Group leakage detected: {', '.join(leaked[:5])}")


def assert_no_cross_split_overlap(
    assignments: dict[str, str],
    intervals: Sequence[tuple[str, str, float, float]],
) -> None:
    """Reject temporal overlap across splits within any source run."""
    by_run: dict[str, list[tuple[str, float, float]]] = {}
    for window_id, source_run, start, end in intervals:
        if end <= start:
            raise ValueError(f"invalid interval for {window_id}")
        by_run.setdefault(source_run, []).append((window_id, start, end))
    for source_run, run_intervals in by_run.items():
        ordered = sorted(run_intervals, key=lambda item: (item[1], item[2]))
        for left, right in zip(ordered, ordered[1:], strict=False):
            if right[1] < left[2] and assignments[left[0]] != assignments[right[0]]:
                raise ValueError(
                    f"Cross-split temporal overlap in {source_run}: "
                    f"{left[0]} / {right[0]}"
                )
