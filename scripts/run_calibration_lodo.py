#!/usr/bin/env python3
"""Run nested leave-one-day-out ridge evaluation on calibration data only."""

from __future__ import annotations

import argparse
import json
import tomllib
from pathlib import Path

import numpy as np

from japaneeg_audit.retrieval import nested_leave_one_day_out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("features", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/baseline_v1.toml")
    )
    args = parser.parse_args()

    config = tomllib.loads(args.config.read_text())
    bundle = np.load(args.features)
    calibration = bundle["subset_role"] == "calibration"
    result = nested_leave_one_day_out(
        bundle["eeg_raw"][calibration],
        bundle["audio_raw"][calibration],
        bundle["source_run"][calibration],
        config["model"]["alphas"],
    )
    result["scope"] = "calibration_rows_only"
    result["rows"] = int(calibration.sum())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
