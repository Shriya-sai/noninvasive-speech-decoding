from copy import deepcopy

import pandas as pd
import pytest

from japaneeg_audit.experiment import (
    build_model_manifest,
    day_macro_average,
    validate_baseline_specification,
    validate_model_manifest,
)


def valid_specification() -> dict:
    return {
        "experiment": {"status": "frozen_before_feature_extraction"},
        "eligibility": {
            "require_sync_gate": True,
            "hard_artifact_exclusion": False,
        },
        "split": {
            "unit": "recording_day",
            "train_roles": ["calibration"],
            "validation_roles": ["validation"],
            "test_roles": ["test"],
            "fit_on_roles": ["calibration"],
            "allow_window_random_primary": False,
            "allow_role_reassignment": False,
        },
        "uncertainty": {"unit": "recording_day"},
    }


def test_frozen_baseline_specification_passes() -> None:
    validate_baseline_specification(valid_specification())


@pytest.mark.parametrize(
    ("section", "field", "value", "message"),
    [
        ("split", "unit", "window", "recording_day"),
        ("split", "allow_window_random_primary", True, "window-random"),
        ("split", "allow_role_reassignment", True, "cannot be reassigned"),
        ("split", "fit_on_roles", ["calibration", "validation"], "calibration"),
        ("eligibility", "require_sync_gate", False, "synchronization"),
        ("eligibility", "hard_artifact_exclusion", True, "artifact strata"),
        ("uncertainty", "unit", "window", "recording_day"),
    ],
)
def test_baseline_specification_rejects_leakage_prone_changes(
    section: str, field: str, value: object, message: str
) -> None:
    specification = deepcopy(valid_specification())
    specification[section][field] = value
    with pytest.raises(ValueError, match=message):
        validate_baseline_specification(specification)


def valid_manifest() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "window_id": ["a", "b", "c", "d"],
            "source_run": ["train1", "train2", "valid1", "test1"],
            "subset_role": ["calibration", "calibration", "validation", "test"],
            "sync_pass": [True, True, True, True],
            "artifact_stratum": [
                "clean_run",
                "high_artifact_run",
                "clean_run",
                "high_artifact_run",
            ],
            "model_eligible": [True, True, True, True],
        }
    )


def test_model_manifest_preserves_roles_and_artifact_strata() -> None:
    validate_model_manifest(
        valid_manifest(),
        {
            "calibration": ["train1", "train2"],
            "validation": ["valid1"],
            "test": ["test1"],
        },
    )


def test_sync_failure_cannot_be_eligible() -> None:
    frame = valid_manifest()
    frame.loc[2, "sync_pass"] = False
    with pytest.raises(ValueError, match="sync-failing"):
        validate_model_manifest(frame, {})


def test_day_macro_average_equal_weights_days() -> None:
    assert day_macro_average({"short": 0.0, "long": 1.0}) == 0.5


def test_model_manifest_builder_retains_artifact_runs_and_blocks_bad_sync() -> None:
    windows = pd.DataFrame(
        {
            "window_id": ["a", "b", "drop"],
            "source_run": ["train1", "valid1", "valid1"],
            "subset_role": ["calibration", "validation", "validation"],
            "retained": [True, True, False],
        }
    )
    synchronization = pd.DataFrame(
        {
            "source_run": ["train1", "valid1"],
            "subset_role": ["calibration", "validation"],
            "passes_gate": [True, False],
        }
    )
    flags = pd.DataFrame(
        {
            "source_run": ["train1", "valid1"],
            "run_qc_flagged": [True, False],
        }
    )
    result = build_model_manifest(windows, synchronization, flags)
    assert result["window_id"].tolist() == ["a", "b"]
    assert result["artifact_stratum"].tolist() == [
        "high_artifact_run",
        "clean_run",
    ]
    assert result["model_eligible"].tolist() == [True, False]
