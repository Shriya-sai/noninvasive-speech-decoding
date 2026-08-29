import pytest

from japaneeg_audit.splits import assert_disjoint_groups


def test_disjoint_sessions_pass() -> None:
    assert_disjoint_groups(["ses-01", "ses-02"], ["ses-03"])


def test_overlapping_sessions_fail() -> None:
    with pytest.raises(ValueError, match="ses-02"):
        assert_disjoint_groups(["ses-01", "ses-02"], ["ses-02", "ses-03"])
