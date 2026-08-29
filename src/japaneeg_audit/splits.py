"""Hierarchical split validation utilities."""

from collections.abc import Iterable


def assert_disjoint_groups(
    train_groups: Iterable[str], test_groups: Iterable[str]
) -> None:
    """Raise when an independence group occurs in both train and test data."""
    overlap = set(train_groups).intersection(test_groups)
    if overlap:
        preview = ", ".join(sorted(overlap)[:5])
        raise ValueError(f"Train/test group leakage detected: {preview}")
