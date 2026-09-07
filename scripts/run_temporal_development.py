#!/usr/bin/env python3
"""Run the frozen primary temporal ridge and evaluation-only timing controls."""

from __future__ import annotations

import argparse
import json
import tomllib
from pathlib import Path

import numpy as np

from japaneeg_audit.temporal_model import nested_temporal_leave_one_day_out
from japaneeg_audit.retrieval import macro_average, nested_leave_one_day_out


def _candidate_reference(candidates: int) -> dict[str, float]:
    reciprocal_ranks = sum(1.0 / rank for rank in range(1, candidates + 1))
    return {
        "top_1_accuracy": 1.0 / candidates,
        "top_10_accuracy": min(10, candidates) / candidates,
        "mean_reciprocal_rank": reciprocal_ranks / candidates,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("features", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/temporal_ridge_v1.toml")
    )
    args = parser.parse_args()

    config = tomllib.loads(args.config.read_text())
    bundle = np.load(args.features)
    calibration = bundle["subset_role"] == config["resampling"]["development_role"]
    bin_ms = config["input"]["bin_seconds"] * 1000
    lag_bins = [
        round(lag / bin_ms)
        for lag in config["temporal_controls"]["lags_milliseconds"]
        if lag != 0
    ]
    result = nested_temporal_leave_one_day_out(
        bundle["eeg_temporal_raw"][calibration],
        bundle["audio_temporal_raw"][calibration],
        bundle["source_run"][calibration],
        config["model"]["alphas"],
        components=config["reduction"]["components"],
        lag_bins=lag_bins,
        permutations=config["other_controls"]["within_run_pairing_permutations"],
        permutation_seed=config["other_controls"]["permutation_seed"],
    )
    envelope = bundle["audio_envelope_raw"][calibration]
    target = bundle["audio_temporal_raw"][calibration].reshape(
        calibration.sum(), -1
    )
    result["audio_envelope_only"] = nested_leave_one_day_out(
        envelope,
        target,
        bundle["source_run"][calibration],
        config["model"]["alphas"],
    )
    references = {
        day: _candidate_reference(values["candidates"])
        for day, values in result["primary"]["days"].items()
    }
    result["session_metadata_only"] = {
        "days": references,
        "macro": macro_average(references),
    }
    days_above = sum(
        values["mean_reciprocal_rank"]
        > references[day]["mean_reciprocal_rank"]
        for day, values in result["primary"]["days"].items()
    )
    primary_mrr = result["primary"]["macro"]["mean_reciprocal_rank"]
    reverse_mrr = result["temporal_controls"]["time_reversed"]["macro"][
        "mean_reciprocal_rank"
    ]
    gate = config["development_gate"]
    checks = {
        "minimum_days_above_candidate_reference": days_above
        >= gate["minimum_days_above_candidate_reference"],
        "above_pairing_null_95th_percentile": primary_mrr
        > result["pairing_null"]["mrr_95th_percentile"],
        "above_time_reversal": primary_mrr > reverse_mrr,
    }
    result["development_gate"] = {
        "days_above_candidate_reference": days_above,
        "checks": checks,
        "passed": all(checks.values()),
    }
    result["scope"] = "calibration_rows_only"
    result["rows"] = int(calibration.sum())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
