#!/usr/bin/env python3
"""Extract the frozen simultaneous-audio RMS-envelope control features."""

from __future__ import annotations

import argparse
import math
import tomllib
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import signal
from scipy.io import wavfile

from japaneeg_audit.features import TrainingStandardizer, extract_rms_envelope


def _window(
    audio: np.ndarray,
    source_hz: int,
    start_seconds: float,
    end_seconds: float,
    target_hz: int,
) -> np.ndarray:
    start = round(start_seconds * source_hz)
    stop = round(end_seconds * source_hz)
    segment = audio[start:stop]
    if segment.ndim == 2:
        segment = segment[:, 0]
    if np.issubdtype(segment.dtype, np.integer):
        info = np.iinfo(segment.dtype)
        segment = segment.astype(np.float64) / max(abs(info.min), info.max)
    else:
        segment = segment.astype(np.float64)
    divisor = math.gcd(source_hz, target_hz)
    return signal.resample_poly(
        segment, target_hz // divisor, source_hz // divisor
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("model_manifest", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--baseline-config",
        type=Path,
        default=Path("configs/baseline_v1.toml"),
    )
    parser.add_argument(
        "--subset-config",
        type=Path,
        default=Path("configs/qc_calibration_subset.toml"),
    )
    args = parser.parse_args()

    baseline = tomllib.loads(args.baseline_config.read_text())
    control = baseline["comparators"]["audio_envelope"]
    subset = tomllib.loads(args.subset_config.read_text())
    paths = {run["id"]: run for run in subset["runs"]}
    manifest = pd.read_csv(args.model_manifest, sep="\t")
    manifest = manifest.loc[manifest["model_eligible"]].copy()
    manifest = manifest.sort_values(["source_run", "window_index"])

    features = []
    ordered = []
    for source_run, rows in manifest.groupby("source_run", sort=True):
        source_hz, audio = wavfile.read(
            args.dataset_root / paths[source_run]["audio"], mmap=True
        )
        for row in rows.itertuples(index=False):
            waveform = _window(
                audio,
                source_hz,
                row.audio_start_seconds,
                row.audio_end_seconds,
                control["sample_rate_hz"],
            )
            features.append(
                extract_rms_envelope(waveform, control["bins_per_window"])
            )
        ordered.append(rows)
        print(f"{source_run} {len(rows)} windows", flush=True)

    metadata = pd.concat(ordered, ignore_index=True)
    raw = np.stack(features)
    training = metadata["subset_role"].eq("calibration").to_numpy()
    standardizer = TrainingStandardizer.fit(raw[training])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.output,
        window_id=metadata["window_id"].to_numpy(dtype=str),
        envelope_raw=raw,
        envelope=standardizer.transform(raw),
        training_mean=standardizer.mean,
        training_scale=standardizer.scale,
    )
    print(f"wrote {len(raw)} rows x {raw.shape[1]} features to {args.output}")


if __name__ == "__main__":
    main()
