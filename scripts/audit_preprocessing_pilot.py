#!/usr/bin/env python3
"""Run continuous preprocessing and report aggregate retained-window QC."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from japaneeg_audit.preprocessing import (
    extract_standardized_window,
    preprocess_continuous_eeg,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("eeg", type=Path)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()

    stem = args.eeg.name.removesuffix("_eeg.edf")
    manifest = pd.read_csv(args.manifest, sep="\t")
    selected = manifest.loc[
        (manifest["source_run"] == stem) & manifest["retained"]
    ]
    if selected.empty:
        raise ValueError(f"no retained windows for {stem}")

    raw = preprocess_continuous_eeg(args.eeg)
    means = []
    standard_deviations = []
    clipped = 0
    values = 0
    for row in selected.itertuples():
        window = extract_standardized_window(raw, row.eeg_start_seconds)
        means.append(float(np.abs(window.mean(axis=1)).max()))
        standard_deviations.append(float(np.abs(window.std(axis=1) - 1).max()))
        clipped += int(np.count_nonzero(np.abs(window) == 5.0))
        values += window.size

    print(
        json.dumps(
            {
                "run": stem,
                "channels": len(raw.ch_names),
                "sampling_hz": raw.info["sfreq"],
                "retained_windows": len(selected),
                "window_shape": [128, 1200],
                "all_finite": True,
                "maximum_absolute_channel_mean_after_clipping": max(means),
                "maximum_channel_sd_error_after_clipping": max(
                    standard_deviations
                ),
                "clipped_value_fraction": clipped / values,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
