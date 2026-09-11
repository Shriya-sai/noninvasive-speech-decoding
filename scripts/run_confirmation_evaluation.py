#!/usr/bin/env python3
"""Apply the checksum-locked temporal model to confirmation exactly once."""

from __future__ import annotations

import argparse
import hashlib
import json
import tomllib
from pathlib import Path

import numpy as np

from japaneeg_audit.retrieval import evaluate_by_day, macro_average


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def apply_saved_model(model: dict[str, np.ndarray], eeg: np.ndarray) -> np.ndarray:
    """Apply saved scaling, PCA, and ridge arrays without any fitted operation."""
    flat = np.asarray(eeg, dtype=np.float64).reshape(len(eeg), -1)
    standardized = (flat - model["pca_mean"]) / model["pca_scale"]
    reduced = standardized @ model["pca_components"].T
    return (
        (reduced - model["ridge_feature_mean"]) @ model["ridge_coefficient"]
        + model["ridge_target_mean"]
    )


def candidate_reference(candidates: int) -> dict[str, float]:
    return {
        "top_1_accuracy": 1.0 / candidates,
        "top_10_accuracy": min(10, candidates) / candidates,
        "mean_reciprocal_rank": sum(1.0 / rank for rank in range(1, candidates + 1))
        / candidates,
    }


def serializable_run_counts(runs: np.ndarray, counts: np.ndarray) -> dict[str, int]:
    """Convert NumPy identity/count outputs into stable JSON-native values."""
    return {str(run): int(count) for run, count in zip(runs, counts)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("features", type=Path)
    parser.add_argument("model", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--config", type=Path,
                        default=Path("configs/confirmation_evaluation_v1.toml"))
    args = parser.parse_args()
    config = tomllib.loads(args.config.read_text())
    artifacts = config["artifacts"]
    observed_hashes = {"features": sha256(args.features), "model": sha256(args.model)}
    if observed_hashes["features"] != artifacts["feature_bundle_sha256"]:
        raise ValueError("confirmation feature-bundle checksum mismatch")
    if observed_hashes["model"] != artifacts["model_sha256"]:
        raise ValueError("confirmation model checksum mismatch")

    feature_file = np.load(args.features)
    model_file = np.load(args.model)
    features = {key: feature_file[key] for key in feature_file.files}
    model = {key: model_file[key] for key in model_file.files}
    rows = artifacts["expected_rows"]
    runs = np.asarray(features["source_run"], dtype=str)
    roles = np.asarray(features["subset_role"], dtype=str)
    if len(runs) != rows or set(roles) != {artifacts["expected_role"]}:
        raise ValueError("confirmation rows or roles do not match frozen scope")
    observed_runs, counts = np.unique(runs, return_counts=True)
    if list(observed_runs) != sorted(artifacts["expected_runs"]):
        raise ValueError("confirmation run identities do not match frozen scope")
    expected_counts = dict(zip(artifacts["expected_runs"], artifacts["expected_run_rows"]))
    if dict(zip(observed_runs, counts)) != expected_counts:
        raise ValueError("confirmation run row counts do not match frozen scope")
    if float(model["selected_alpha"]) != config["application"]["saved_alpha"]:
        raise ValueError("saved alpha does not match frozen evaluation config")
    numeric = [features["eeg_temporal_raw"], features["audio_temporal_raw"]]
    numeric += [value for key, value in model.items() if np.issubdtype(value.dtype, np.number)]
    if not all(np.isfinite(value).all() for value in numeric):
        raise ValueError("confirmation inputs or saved model contain non-finite values")

    eeg = features["eeg_temporal_raw"]
    raw_target = features["audio_temporal_raw"].reshape(rows, -1)
    target = (raw_target - model["target_mean"]) / model["target_scale"]
    prediction = apply_saved_model(model, eeg)
    primary_days = evaluate_by_day(prediction, target, runs)
    primary_macro = macro_average(primary_days)
    references = {day: candidate_reference(value["candidates"])
                  for day, value in primary_days.items()}
    reference_macro = macro_average(references)

    controls = {}
    for lag_ms in config["controls"]["lags_milliseconds"]:
        shifted = np.roll(eeg, shift=round(lag_ms / 250), axis=1)
        day_rows = evaluate_by_day(apply_saved_model(model, shifted), target, runs)
        controls[f"lag_{lag_ms:+d}_ms"] = {"days": day_rows, "macro": macro_average(day_rows)}
    reversed_rows = evaluate_by_day(
        apply_saved_model(model, eeg[:, ::-1, :]), target, runs
    )
    controls["time_reversed"] = {
        "days": reversed_rows, "macro": macro_average(reversed_rows)
    }

    rng = np.random.default_rng(config["controls"]["permutation_seed"])
    seeds = rng.integers(0, np.iinfo(np.uint32).max,
                        size=config["controls"]["within_day_pairing_permutations"],
                        dtype=np.uint32)
    null_rows = []
    for seed in seeds:
        order = np.arange(rows)
        local_rng = np.random.default_rng(int(seed))
        for day in observed_runs:
            selected = np.flatnonzero(runs == day)
            order[selected] = local_rng.permutation(selected)
        permuted = evaluate_by_day(prediction, target[order], runs)
        null_rows.append({"seed": int(seed), **macro_average(permuted)})
    null_mrr = np.asarray([row["mean_reciprocal_rank"] for row in null_rows])
    primary_mrr = primary_macro["mean_reciprocal_rank"]
    null_95 = float(np.quantile(null_mrr, 0.95))
    checks = {
        "each_day_above_candidate_reference": all(
            primary_days[day]["mean_reciprocal_rank"]
            > references[day]["mean_reciprocal_rank"] for day in observed_runs
        ),
        "primary_above_candidate_reference": primary_mrr
        > reference_macro["mean_reciprocal_rank"],
        "primary_above_pairing_null_95th_percentile": primary_mrr > null_95,
        "primary_above_time_reversal": primary_mrr
        > controls["time_reversed"]["macro"]["mean_reciprocal_rank"],
    }
    strata = np.asarray(features["artifact_stratum"], dtype=str)
    stratum_results = {}
    for stratum in sorted(np.unique(strata)):
        selected = strata == stratum
        if all(np.sum(selected & (runs == day)) >= 2 for day in observed_runs):
            day_rows = evaluate_by_day(prediction[selected], target[selected], runs[selected])
            stratum_results[stratum] = {"days": day_rows, "macro": macro_average(day_rows)}
    result = {
        "scope": {"rows": rows, "runs": serializable_run_counts(observed_runs, counts),
                  "role": artifacts["expected_role"]},
        "artifact_sha256": observed_hashes,
        "saved_alpha": float(model["selected_alpha"]),
        "primary": {"days": primary_days, "macro": primary_macro},
        "candidate_reference": {"days": references, "macro": reference_macro},
        "temporal_controls": controls,
        "pairing_null": {"permutations": len(null_rows), "rows": null_rows,
                         "mrr_95th_percentile": null_95,
                         "mrr_empirical_p_plus_one": float(
                             (1 + np.sum(null_mrr >= primary_mrr)) / (len(null_mrr) + 1)
                         )},
        "artifact_strata": stratum_results,
        "confirmation_decision": {"checks": checks, "passed": all(checks.values())},
        "fitted_operations": 0,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
