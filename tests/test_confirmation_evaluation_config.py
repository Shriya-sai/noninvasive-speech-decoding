from pathlib import Path
import tomllib


def test_confirmation_evaluation_is_checksum_locked_and_no_refit() -> None:
    path = Path(__file__).parents[1] / "configs" / "confirmation_evaluation_v1.toml"
    with path.open("rb") as stream:
        config = tomllib.load(stream)
    assert config["experiment"]["status"] == "frozen_before_model_application"
    assert config["experiment"]["evaluation_count"] == 1
    assert len(config["artifacts"]["feature_bundle_sha256"]) == 64
    assert len(config["artifacts"]["model_sha256"]) == 64
    assert config["artifacts"]["expected_rows"] == 187
    assert config["artifacts"]["expected_run_rows"] == [88, 99]
    assert config["application"]["allow_fit"] is False
    assert config["application"]["allow_refit"] is False
    assert config["application"]["saved_alpha"] == 10.0
    assert config["controls"]["permutation_refits_model"] is False
    decision = config["decision"]
    assert decision["require_each_day_above_candidate_reference"] is True
    assert decision["require_primary_above_pairing_null_95th_percentile"] is True
    assert decision["require_primary_above_time_reversal"] is True
    assert decision["report_regardless_of_outcome"] is True
