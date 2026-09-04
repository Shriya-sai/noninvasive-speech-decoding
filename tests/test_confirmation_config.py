from pathlib import Path
import tomllib


def test_confirmation_days_are_frozen_and_postdate_consumed_tests() -> None:
    path = Path(__file__).parents[1] / "configs" / "replacement_confirmation_v1.toml"
    with path.open("rb") as stream:
        config = tomllib.load(stream)
    selection = config["selection"]
    assert selection["status"] == "frozen_before_temporal_model_development"
    assert selection["selection_uses_signal_qc"] is False
    assert selection["selection_uses_model_outcomes"] is False
    assert selection["downloaded_at_freeze"] is False
    runs = config["runs"]
    assert len(runs) == 3
    assert len({run["id"] for run in runs}) == 3
    assert all("ses-20250122" < run["id"].split("_")[1] for run in runs)
    assert all(run["role"] == "confirmation" for run in runs)
    assert all(run["eeg_bytes"] > 0 and run["audio_bytes"] > 0 for run in runs)
    assert all(len(run["eeg_sha256"]) == 64 for run in runs)
    assert all(len(run["audio_sha256"]) == 64 for run in runs)
