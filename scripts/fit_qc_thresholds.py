#!/usr/bin/env python3
"""Fit robust artifact thresholds from calibration rows and evaluate all roles."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from japaneeg_audit.qc_thresholds import apply_thresholds, fit_robust_thresholds


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("metrics", type=Path)
    parser.add_argument("thresholds", type=Path)
    parser.add_argument("flags", type=Path)
    args = parser.parse_args()

    frame = pd.read_csv(args.metrics, sep="\t")
    calibration = frame.loc[frame["subset_role"] == "calibration"].copy()
    thresholds = fit_robust_thresholds(calibration)
    flags = apply_thresholds(frame, thresholds)
    output = pd.concat([frame[["window_id", "source_run", "subset_role"]], flags], axis=1)

    args.thresholds.parent.mkdir(parents=True, exist_ok=True)
    args.thresholds.write_text(json.dumps(thresholds, indent=2) + "\n")
    args.flags.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.flags, sep="\t", index=False)
    print(output.groupby("subset_role")["artifact_rejected"].agg(["sum", "count"]))


if __name__ == "__main__":
    main()
