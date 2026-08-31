import pytest

from japaneeg_audit.splits import (
    assert_disjoint_groups,
    assert_group_isolation,
    assert_no_cross_split_overlap,
    assign_chronological_groups,
    assign_random_windows,
)


def test_disjoint_sessions_pass() -> None:
    assert_disjoint_groups(["ses-01", "ses-02"], ["ses-03"])


def test_overlapping_sessions_fail() -> None:
    with pytest.raises(ValueError, match="ses-02"):
        assert_disjoint_groups(["ses-01", "ses-02"], ["ses-02", "ses-03"])


def test_random_assignment_is_reproducible() -> None:
    ids = [f"w{index}" for index in range(20)]
    assert assign_random_windows(ids, seed=7) == assign_random_windows(ids, seed=7)
    counts = list(assign_random_windows(ids, seed=7).values())
    assert counts.count("train") == 16
    assert counts.count("validation") == 2
    assert counts.count("test") == 2


def test_grouped_assignment_keeps_groups_intact() -> None:
    groups = [("a1", "day1"), ("a2", "day1"), ("b1", "day2")]
    assignments = assign_chronological_groups(groups)
    assert assignments["a1"] == assignments["a2"] == "train"
    assert assignments["b1"] == "test"
    assert_group_isolation(assignments, groups)


def test_group_leakage_fails() -> None:
    groups = [("a1", "day1"), ("a2", "day1")]
    with pytest.raises(ValueError, match="day1"):
        assert_group_isolation({"a1": "train", "a2": "test"}, groups)


def test_temporal_overlap_within_split_passes() -> None:
    assignments = {"a": "train", "b": "train"}
    assert_no_cross_split_overlap(
        assignments,
        [("a", "run1", 0.0, 5.0), ("b", "run1", 4.0, 9.0)],
    )


def test_cross_split_temporal_overlap_fails() -> None:
    assignments = {"a": "train", "b": "test"}
    with pytest.raises(ValueError, match="Cross-split temporal overlap"):
        assert_no_cross_split_overlap(
            assignments,
            [("a", "run1", 0.0, 5.0), ("b", "run1", 4.99, 9.99)],
        )


def test_adjacent_windows_do_not_overlap() -> None:
    assignments = {"a": "train", "b": "test"}
    assert_no_cross_split_overlap(
        assignments,
        [("a", "run1", 0.0, 5.0), ("b", "run1", 5.0, 10.0)],
    )
