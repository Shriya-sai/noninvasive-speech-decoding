from pathlib import Path
import tomllib


def test_temporal_protocol_is_locked_before_confirmation_access() -> None:
    path = Path(__file__).parents[1] / "configs" / "temporal_ridge_v1.toml"
    with path.open("rb") as stream:
        config = tomllib.load(stream)
    assert config["experiment"]["status"] == "frozen_before_feature_extraction"
    assert config["data"]["confirmation_signals_must_remain_unread_during_development"]
    assert config["eligibility"]["hard_artifact_exclusion"] is False
    assert config["resampling"]["outer_unit"] == "recording_day"
    assert config["resampling"]["inner_unit"] == "recording_day"
    assert config["resampling"]["fit_all_transforms_within_fold"] is True
    assert config["reduction"]["fit_scope"] == "training_fold_only"
    assert config["other_controls"]["within_run_pairing_permutations"] == 99
    assert config["other_controls"]["permutation_stage"] == (
        "held_out_retrieval_target_rows"
    )
    assert config["other_controls"]["permutation_refits_model"] is False
    assert config["temporal_controls"]["application"] == (
        "apply_training_fitted_transforms_and_model_without_refitting"
    )
    assert config["development_gate"]["failure_action"] == (
        "do not inspect confirmation signals"
    )
    gate = config["validation_gate"]
    assert gate["evaluation_count"] == 1
    assert gate["fit_rows"] == "calibration_only"
    assert gate["evaluation_rows"] == "sync_passing_validation_only"
    assert gate["alpha_selection"] == "calibration_leave_one_day_out_macro_mrr"
    assert gate["require_primary_above_candidate_reference"] is True
    assert gate["require_primary_above_pairing_null_95th_percentile"] is True
    assert gate["require_primary_above_time_reversal"] is True
    assert gate["timing_lags_are_report_only"] is True
    final_fit = config["final_fit"]
    assert final_fit["condition"] == "validation_gate_passed"
    assert final_fit["alpha"] == "fixed_from_calibration_leave_one_day_out"
    assert final_fit["serialize_before_confirmation_download"] is True
    assert final_fit["allow_confirmation_refit"] is False
    assert config["confirmation"]["no_refitting_on_confirmation"] is True


def test_temporal_dimensions_are_internally_consistent() -> None:
    path = Path(__file__).parents[1] / "configs" / "temporal_ridge_v1.toml"
    with path.open("rb") as stream:
        config = tomllib.load(stream)
    eeg = config["input"]
    target = config["target"]
    assert eeg["temporal_bins"] * eeg["samples_per_bin"] == eeg["window_samples"]
    assert eeg["raw_features"] == (
        eeg["channels"] * eeg["temporal_bins"] * len(eeg["statistics"])
    )
    assert target["features"] == target["temporal_bins"] * target["mel_bins"]
    assert target["samples_per_bin"] * target["temporal_bins"] == (
        target["sample_rate_hz"] * 5
    )
