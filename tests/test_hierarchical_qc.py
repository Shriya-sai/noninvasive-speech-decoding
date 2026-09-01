import pandas as pd
import pytest

from japaneeg_audit.hierarchical_qc import (
    apply_hierarchical_qc,
    fit_hierarchical_qc,
)


def _calibration() -> pd.DataFrame:
    rows = []
    for run, base, count in (
        ("r1", 1.0, 100),
        ("r2", 2.0, 5),
        ("r3", 3.0, 5),
        ("r4", 4.0, 5),
        ("r5", 5.0, 5),
        ("r6", 6.0, 5),
    ):
        rows.extend(
            {"subset_role": "calibration", "source_run": run, "metric": base}
            for _ in range(count)
        )
    return pd.DataFrame(rows)


def test_fit_equal_weights_runs_not_windows() -> None:
    specification = fit_hierarchical_qc(
        _calibration(), {"metric": "high"}, run_multiplier=1
    )
    center = specification["metrics"]["metric"]["run_log_center"]
    assert center > 1.0


def test_noncalibration_rows_cannot_fit() -> None:
    frame = _calibration()
    frame.loc[0, "subset_role"] = "validation"
    with pytest.raises(ValueError, match="calibration rows only"):
        fit_hierarchical_qc(frame, {"metric": "high"})


def test_requires_multiple_calibration_runs() -> None:
    frame = _calibration().loc[lambda value: value.source_run.isin(["r1", "r2"])]
    with pytest.raises(ValueError, match="at least six"):
        fit_hierarchical_qc(frame, {"metric": "high"})


def test_apply_separates_run_and_window_flags() -> None:
    calibration = _calibration()
    specification = fit_hierarchical_qc(
        calibration, {"metric": "high"}, run_multiplier=2, within_run_multiplier=2
    )
    evaluation = pd.DataFrame(
        {
            "source_run": ["clean"] * 5 + ["shifted"] * 5,
            "metric": [2.8, 3.0, 3.1, 3.2, 30, 90, 95, 100, 105, 110],
        }
    )
    flags = apply_hierarchical_qc(evaluation, specification)
    assert flags.loc[4, "window_qc_flagged"]
    assert flags.loc[5:, "run_qc_flagged"].all()
