#!/usr/bin/env python3
"""Execute the one-time frozen validation gate and conditional final fit."""

from __future__ import annotations

import argparse
import hashlib
import json
import tomllib
from pathlib import Path

import numpy as np

from japaneeg_audit.retrieval import evaluate_by_day, macro_average
from japaneeg_audit.temporal_model import (
    evaluate_frozen_temporal_model,
    fit_temporal_ridge,
    select_temporal_alpha_leave_one_day_out,
)


def _candidate_reference(candidates: int) -> dict[str, float]:
    return {
        "top_1_accuracy": 1.0 / candidates,
        "top_10_accuracy": min(10, candidates) / candidates,
        "mean_reciprocal_rank": sum(1.0 / r for r in range(1, candidates + 1))
        / candidates,
    }


def _checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("features", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("model_output", type=Path)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/temporal_ridge_v1.toml")
    )
    args = parser.parse_args()
    config = tomllib.loads(args.config.read_text())
    bundle = np.load(args.features)
    roles = bundle["subset_role"].astype(str)
    calibration = roles == config["resampling"]["development_role"]
    validation = roles == config["resampling"]["validation_role"]
    if not calibration.any() or not validation.any():
        raise ValueError("feature bundle must contain calibration and validation rows")

    eeg = bundle["eeg_temporal_raw"]
    target = bundle["audio_temporal_raw"]
    days = bundle["source_run"].astype(str)
    components = config["reduction"]["components"]
    selection = select_temporal_alpha_leave_one_day_out(
        eeg[calibration], target[calibration], days[calibration],
        config["model"]["alphas"], components=components,
    )
    alpha = selection["selected_alpha"]
    pca, model, target_mean, target_scale = fit_temporal_ridge(
        eeg[calibration], target[calibration], alpha, components=components
    )
    prediction, held_target, _ = evaluate_frozen_temporal_model(
        pca, model, target_mean, target_scale, eeg[validation], target[validation]
    )
    validation_days = days[validation]
    primary_days = evaluate_by_day(prediction, held_target, validation_days)
    primary_macro = macro_average(primary_days)

    bin_ms = config["input"]["bin_seconds"] * 1000
    controls = {}
    for lag_ms in config["temporal_controls"]["lags_milliseconds"]:
        if lag_ms == 0:
            continue
        shifted = np.roll(eeg[validation], round(lag_ms / bin_ms), axis=1)
        shifted_prediction, _, _ = evaluate_frozen_temporal_model(
            pca, model, target_mean, target_scale, shifted, target[validation]
        )
        rows = evaluate_by_day(shifted_prediction, held_target, validation_days)
        controls[f"lag_{lag_ms:+d}_ms"] = {"days": rows, "macro": macro_average(rows)}
    reversed_prediction, _, _ = evaluate_frozen_temporal_model(
        pca, model, target_mean, target_scale,
        eeg[validation, ::-1, :], target[validation],
    )
    reverse_days = evaluate_by_day(reversed_prediction, held_target, validation_days)
    controls["time_reversed"] = {"days": reverse_days, "macro": macro_average(reverse_days)}

    gate_config = config["validation_gate"]
    rng = np.random.default_rng(gate_config["permutation_seed"])
    seeds = rng.integers(0, np.iinfo(np.uint32).max,
                         size=gate_config["within_run_pairing_permutations"],
                         dtype=np.uint32)
    null_rows = []
    for seed in seeds:
        permutation = np.arange(validation.sum())
        local_rng = np.random.default_rng(int(seed))
        for day in np.unique(validation_days):
            selected = np.flatnonzero(validation_days == day)
            permutation[selected] = local_rng.permutation(selected)
        rows = evaluate_by_day(prediction, held_target[permutation], validation_days)
        null_rows.append({"seed": int(seed), **macro_average(rows)})
    null_mrr = np.array([row["mean_reciprocal_rank"] for row in null_rows])
    null_95 = float(np.quantile(null_mrr, 0.95))

    references = {day: _candidate_reference(value["candidates"])
                  for day, value in primary_days.items()}
    reference_macro = macro_average(references)
    primary_mrr = primary_macro["mean_reciprocal_rank"]
    checks = {
        "above_candidate_reference": primary_mrr > reference_macro["mean_reciprocal_rank"],
        "above_pairing_null_95th_percentile": primary_mrr > null_95,
        "above_time_reversal": primary_mrr > controls["time_reversed"]["macro"]["mean_reciprocal_rank"],
    }
    passed = all(checks.values())
    result = {
        "scope": "one_time_sync_passing_validation",
        "calibration_rows": int(calibration.sum()),
        "validation_rows": int(validation.sum()),
        "alpha_selection": selection,
        "primary": {"days": primary_days, "macro": primary_macro},
        "session_metadata_only": {"days": references, "macro": reference_macro},
        "temporal_controls": controls,
        "pairing_null": {
            "permutations": len(null_rows), "rows": null_rows,
            "mrr_95th_percentile": null_95,
            "mrr_empirical_p_plus_one": float((1 + np.sum(null_mrr >= primary_mrr)) / (len(null_mrr) + 1)),
        },
        "validation_gate": {"checks": checks, "passed": passed},
    }

    if passed:
        included = calibration | validation
        final_pca, final_model, final_target_mean, final_target_scale = fit_temporal_ridge(
            eeg[included], target[included], alpha, components=components
        )
        args.model_output.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            args.model_output,
            pca_mean=final_pca.mean_, pca_scale=final_pca.scale_,
            pca_components=final_pca.components_,
            pca_singular_values=final_pca.singular_values_,
            target_mean=final_target_mean, target_scale=final_target_scale,
            ridge_feature_mean=final_model.feature_mean_,
            ridge_target_mean=final_model.target_mean_,
            ridge_coefficient=final_model.coefficient_,
            selected_alpha=np.array(alpha), training_rows=np.array(included.sum()),
            source_runs=days[included], subset_roles=roles[included],
        )
        result["final_model"] = {
            "status": "serialized_before_confirmation_access",
            "path": str(args.model_output), "rows": int(included.sum()),
            "selected_alpha": alpha, "sha256": _checksum(args.model_output),
            "bytes": args.model_output.stat().st_size,
        }
    else:
        result["final_model"] = {"status": "not_fitted_validation_failed"}

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
