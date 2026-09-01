import pandas as pd
import pytest

from japaneeg_audit.qc_thresholds import apply_thresholds, fit_robust_thresholds


def _frame(role: str = "calibration") -> pd.DataFrame:
    return pd.DataFrame(
        {
            "subset_role": [role] * 7,
            "low_metric": [9, 10, 10, 10, 10, 10, 11],
            "high_metric": [9, 10, 10, 10, 10, 10, 11],
        }
    )


def test_thresholds_fit_only_permitted_roles() -> None:
    thresholds = fit_robust_thresholds(
        _frame(), {"low_metric": "low", "high_metric": "high"}
    )
    assert thresholds["low_metric"]["threshold"] == 10
    assert thresholds["high_metric"]["threshold"] == 10


def test_validation_rows_cannot_fit_thresholds() -> None:
    with pytest.raises(ValueError, match="forbidden roles: validation"):
        fit_robust_thresholds(_frame("validation"), {"low_metric": "low"})


def test_apply_thresholds_flags_both_directions() -> None:
    frame = pd.DataFrame({"low": [0, 2], "high": [8, 12]})
    thresholds = {
        "low": {"direction": "low", "threshold": 1},
        "high": {"direction": "high", "threshold": 10},
    }
    flags = apply_thresholds(frame, thresholds)
    assert flags["artifact_rejected"].tolist() == [True, True]


def test_empty_calibration_table_fails() -> None:
    with pytest.raises(ValueError, match="empty"):
        fit_robust_thresholds(
            pd.DataFrame({"subset_role": [], "metric": []}),
            {"metric": "high"},
        )
