#!/usr/bin/env python3
"""Fit and evaluate the frozen held-out-day ridge retrieval baseline."""

from __future__ import annotations

import argparse
import json
import tomllib
from pathlib import Path

import numpy as np

from japaneeg_audit.retrieval import (
    RidgeRegression,
    evaluate_by_day,
    macro_average,
    permute_within_groups,
    select_ridge_alpha,
)


def _jsonable_day_metrics(metrics: dict[str, dict[str, float]]) -> dict:
    return {day: dict(values) for day, values in metrics.items()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("features", type=Path)
    parser.add_argument("audio_envelope_features", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/baseline_v1.toml")
    )
    args = parser.parse_args()

    config = tomllib.loads(args.config.read_text())
    bundle = np.load(args.features)
    envelope_bundle = np.load(args.audio_envelope_features)
    if not np.array_equal(bundle["window_id"], envelope_bundle["window_id"]):
        raise ValueError("audio-envelope and primary feature rows do not align")
    roles = bundle["subset_role"]
    runs = bundle["source_run"]
    eeg = bundle["eeg"]
    audio = bundle["audio"]
    envelope = envelope_bundle["envelope"]
    train = roles == "calibration"
    validation = roles == "validation"
    test = roles == "test"
    if not train.any() or not validation.any() or not test.any():
        raise ValueError("feature bundle must contain all frozen subset roles")

    alpha, validation_grid = select_ridge_alpha(
        eeg[train],
        audio[train],
        eeg[validation],
        audio[validation],
        runs[validation],
        config["model"]["alphas"],
    )
    model = RidgeRegression(alpha=alpha).fit(eeg[train], audio[train])
    validation_days = evaluate_by_day(
        model.predict(eeg[validation]), audio[validation], runs[validation]
    )
    test_days = evaluate_by_day(model.predict(eeg[test]), audio[test], runs[test])

    intercept_prediction = np.repeat(
        audio[train].mean(axis=0, keepdims=True), test.sum(), axis=0
    )
    metadata_days = evaluate_by_day(
        intercept_prediction, audio[test], runs[test]
    )

    envelope_alpha, envelope_validation_grid = select_ridge_alpha(
        envelope[train],
        audio[train],
        envelope[validation],
        audio[validation],
        runs[validation],
        config["model"]["alphas"],
    )
    envelope_model = RidgeRegression(alpha=envelope_alpha).fit(
        envelope[train], audio[train]
    )
    envelope_days = evaluate_by_day(
        envelope_model.predict(envelope[test]), audio[test], runs[test]
    )

    permutation_results = []
    for seed in config["seeds"]["permutation"]:
        permuted_audio = permute_within_groups(audio[train], runs[train], seed)
        null_model = RidgeRegression(alpha=alpha).fit(eeg[train], permuted_audio)
        null_days = evaluate_by_day(
            null_model.predict(eeg[test]), audio[test], runs[test]
        )
        permutation_results.append(
            {
                "seed": seed,
                "days": _jsonable_day_metrics(null_days),
                "macro": macro_average(null_days),
            }
        )

    result = {
        "experiment": config["experiment"]["name"],
        "selected_alpha": alpha,
        "row_counts": {
            "calibration": int(train.sum()),
            "validation": int(validation.sum()),
            "test": int(test.sum()),
        },
        "validation_grid": validation_grid,
        "validation": {
            "days": _jsonable_day_metrics(validation_days),
            "macro": macro_average(validation_days),
        },
        "test": {
            "days": _jsonable_day_metrics(test_days),
            "macro": macro_average(test_days),
        },
        "session_metadata_only": {
            "definition": "training-target mean (unseen-day intercept baseline)",
            "days": _jsonable_day_metrics(metadata_days),
            "macro": macro_average(metadata_days),
        },
        "audio_envelope_only": {
            "selected_alpha": envelope_alpha,
            "validation_grid": envelope_validation_grid,
            "days": _jsonable_day_metrics(envelope_days),
            "macro": macro_average(envelope_days),
        },
        "permuted_pairing": permutation_results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
