#!/usr/bin/env python3
"""Run the report-only audio-envelope control for frozen validation."""

from __future__ import annotations

import argparse
import json
import tomllib
from pathlib import Path

import numpy as np

from japaneeg_audit.retrieval import RidgeRegression, evaluate_by_day, macro_average


def standardize(training: np.ndarray, held: np.ndarray):
    mean, scale = training.mean(axis=0), training.std(axis=0)
    if np.any(scale == 0):
        raise ValueError("invalid training scale")
    return (training - mean) / scale, (held - mean) / scale, mean, scale


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("features", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--config", type=Path,
                        default=Path("configs/temporal_ridge_v1.toml"))
    args = parser.parse_args()
    config = tomllib.loads(args.config.read_text())
    bundle = np.load(args.features)
    roles = bundle["subset_role"].astype(str)
    calibration = roles == config["resampling"]["development_role"]
    validation = roles == config["resampling"]["validation_role"]
    x = bundle["audio_envelope_raw"].astype(float)
    y = bundle["audio_temporal_raw"].reshape(len(roles), -1).astype(float)
    days = bundle["source_run"].astype(str)
    candidates = sorted(config["model"]["alphas"])
    scores = {alpha: {} for alpha in candidates}
    for day in sorted(np.unique(days[calibration])):
        held = calibration & (days == day)
        train = calibration & ~held
        train_x, held_x, _, _ = standardize(x[train], x[held])
        train_y, held_y, _, _ = standardize(y[train], y[held])
        for alpha in candidates:
            prediction = RidgeRegression(alpha).fit(train_x, train_y).predict(held_x)
            scores[alpha][day] = evaluate_by_day(
                prediction, held_y, days[held]
            )[day]
    rows = [{"alpha": alpha, **macro_average(scores[alpha])}
            for alpha in candidates]
    selected = max(rows, key=lambda row: (row["mean_reciprocal_rank"], -row["alpha"]))["alpha"]
    train_x, held_x, _, _ = standardize(x[calibration], x[validation])
    train_y, held_y, _, _ = standardize(y[calibration], y[validation])
    prediction = RidgeRegression(selected).fit(train_x, train_y).predict(held_x)
    day_rows = evaluate_by_day(prediction, held_y, days[validation])
    result = {
        "scope": "report_only_audio_envelope_validation_control",
        "selected_alpha": selected,
        "calibration_leave_one_day_out": rows,
        "validation": {"days": day_rows, "macro": macro_average(day_rows)},
        "affected_validation_gate": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
