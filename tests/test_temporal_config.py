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
    assert config["development_gate"]["failure_action"] == (
        "do not inspect confirmation signals"
    )
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
