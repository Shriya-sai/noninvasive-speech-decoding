#!/usr/bin/env python3
"""Run the frozen waveform synchronization gate over a configured subset."""

from __future__ import annotations

import argparse
import tomllib
from pathlib import Path

import pandas as pd

from japaneeg_audit.synchronization import validate_waveform_sync


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/qc_calibration_subset.toml"),
    )
    args = parser.parse_args()

    config = tomllib.loads(args.config.read_text())
    rows = []
    for run in config["runs"]:
        result = validate_waveform_sync(
            args.dataset_root / run["eeg"],
            args.dataset_root / run["audio"],
        )
        best = result["best_pair"]
        rows.append(
            {
                "source_run": run["id"],
                "subset_role": run["role"],
                "timeline_stratum": run["stratum"],
                "calibration_wave": run.get(
                    "calibration_wave",
                    1 if run["role"] == "calibration" else None,
                ),
                "passes_gate": result["passes_gate"],
                "monitor_channel": best["monitor_channel"],
                "wav_channel": best["wav_channel"],
                "events": best["events"],
                "median_envelope_correlation": best[
                    "median_envelope_correlation"
                ],
                "median_residual_seconds": best["median_residual_seconds"],
            }
        )
        print(run["id"], result["passes_gate"], flush=True)
    frame = pd.DataFrame(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output, sep="\t", index=False)
    print(f"passed {int(frame['passes_gate'].sum())}/{len(frame)} runs")


if __name__ == "__main__":
    main()
