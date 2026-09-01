#!/usr/bin/env python3
"""Execute preprocessing and write threshold-free retained-window QC metrics."""

from __future__ import annotations

import argparse
import tomllib
from pathlib import Path

import pandas as pd

from japaneeg_audit.preprocessing import (
    extract_standardized_window,
    preprocess_continuous_eeg,
)
from japaneeg_audit.qc import compute_window_qc


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/qc_calibration_subset.toml"),
    )
    args = parser.parse_args()

    config = tomllib.loads(args.config.read_text())
    manifest = pd.read_csv(args.manifest, sep="\t")
    rows = []
    for run in config["runs"]:
        selected = manifest.loc[
            (manifest["source_run"] == run["id"]) & manifest["retained"]
        ]
        if selected.empty:
            raise ValueError(f"no retained windows for {run['id']}")
        raw = preprocess_continuous_eeg(args.dataset_root / run["eeg"])
        sampling_hz = float(raw.info["sfreq"])
        for window in selected.itertuples():
            start = raw.time_as_index(window.eeg_start_seconds, use_rounding=True)[0]
            stop = start + 1200
            unstandardized = raw.get_data(start=start, stop=stop)
            standardized = extract_standardized_window(
                raw, window.eeg_start_seconds
            )
            rows.append(
                {
                    "window_id": window.window_id,
                    "source_run": run["id"],
                    "subset_role": run["role"],
                    "timeline_stratum": run["stratum"],
                    "calibration_wave": run.get(
                        "calibration_wave",
                        1 if run["role"] == "calibration" else None,
                    ),
                    **compute_window_qc(
                        unstandardized,
                        sampling_hz,
                        standardized,
                    ),
                }
            )
        print(run["id"], len(selected), "windows", flush=True)

    output = pd.DataFrame(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, sep="\t", index=False)
    print(f"wrote {len(output)} QC rows to {args.output}")


if __name__ == "__main__":
    main()
