#!/usr/bin/env python3
"""Extract and training-standardize frozen baseline EEG/audio features."""

from __future__ import annotations

import argparse
import math
import tomllib
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import signal
from scipy.io import wavfile

from japaneeg_audit.features import (
    BandpowerConfig,
    LogMelConfig,
    TrainingStandardizer,
    extract_log_bandpower,
    extract_log_mel_summary,
)
from japaneeg_audit.preprocessing import (
    extract_standardized_window,
    preprocess_continuous_eeg,
)


def _audio_float(segment: np.ndarray) -> np.ndarray:
    if np.issubdtype(segment.dtype, np.integer):
        info = np.iinfo(segment.dtype)
        scale = max(abs(info.min), info.max)
        return segment.astype(np.float64) / scale
    return segment.astype(np.float64)


def _audio_window(
    audio: np.ndarray,
    source_hz: int,
    start_seconds: float,
    end_seconds: float,
    target_hz: int,
) -> np.ndarray:
    start = round(start_seconds * source_hz)
    stop = round(end_seconds * source_hz)
    if start < 0 or stop > len(audio) or stop <= start:
        raise ValueError("audio feature window is out of bounds")
    segment = audio[start:stop]
    if segment.ndim == 2:
        segment = segment[:, 0]
    if segment.ndim != 1:
        raise ValueError("vocal WAV must be mono or samples by channels")
    segment = _audio_float(segment)
    divisor = math.gcd(source_hz, target_hz)
    resampled = signal.resample_poly(
        segment,
        up=target_hz // divisor,
        down=source_hz // divisor,
    )
    expected = round((end_seconds - start_seconds) * target_hz)
    if abs(len(resampled) - expected) > 1:
        raise ValueError("resampled audio window has an unexpected length")
    return resampled[:expected]


def _feature_configs(baseline: dict) -> tuple[BandpowerConfig, LogMelConfig]:
    eeg = baseline["input"]
    audio = baseline["target"]
    return (
        BandpowerConfig(
            sampling_hz=eeg["sample_rate_hz"],
            bands_hz=tuple(tuple(band) for band in eeg["bands_hz"]),
            segment_samples=eeg["welch_segment_samples"],
            overlap_samples=eeg["welch_overlap_samples"],
            power_floor=eeg["power_floor"],
        ),
        LogMelConfig(
            sampling_hz=audio["sample_rate_hz"],
            mel_bins=audio["mel_bins"],
            frame_samples=audio["frame_samples"],
            hop_samples=audio["hop_samples"],
            fft_samples=audio["fft_samples"],
            minimum_hz=audio["minimum_hz"],
            maximum_hz=audio["maximum_hz"],
            power_floor=audio["power_floor"],
        ),
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
    subset = tomllib.loads(args.subset_config.read_text())
    eeg_config, audio_config = _feature_configs(baseline)
    paths = {run["id"]: run for run in subset["runs"]}
    manifest = pd.read_csv(args.model_manifest, sep="\t")
    manifest = manifest.loc[manifest["model_eligible"]].copy()
    manifest = manifest.sort_values(["source_run", "window_index"])

    eeg_rows: list[np.ndarray] = []
    audio_rows: list[np.ndarray] = []
    metadata_rows: list[pd.DataFrame] = []
    for source_run, rows in manifest.groupby("source_run", sort=True):
        if source_run not in paths:
            raise ValueError(f"manifest run missing from subset config: {source_run}")
        run = paths[source_run]
        raw = preprocess_continuous_eeg(args.dataset_root / run["eeg"])
        source_hz, audio = wavfile.read(
            args.dataset_root / run["audio"], mmap=True
        )
        for row in rows.itertuples(index=False):
            eeg_window = extract_standardized_window(raw, row.eeg_start_seconds)
            audio_window = _audio_window(
                audio,
                source_hz,
                row.audio_start_seconds,
                row.audio_end_seconds,
                audio_config.sampling_hz,
            )
            eeg_rows.append(extract_log_bandpower(eeg_window, eeg_config))
            audio_rows.append(extract_log_mel_summary(audio_window, audio_config))
        metadata_rows.append(rows)
        print(f"{source_run} {len(rows)} windows", flush=True)

    metadata = pd.concat(metadata_rows, ignore_index=True)
    eeg_raw = np.stack(eeg_rows)
    audio_raw = np.stack(audio_rows)
    calibration = metadata["subset_role"].eq("calibration").to_numpy()
    eeg_standardizer = TrainingStandardizer.fit(eeg_raw[calibration])
    audio_standardizer = TrainingStandardizer.fit(audio_raw[calibration])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.output,
        window_id=metadata["window_id"].to_numpy(dtype=str),
        source_run=metadata["source_run"].to_numpy(dtype=str),
        subset_role=metadata["subset_role"].to_numpy(dtype=str),
        artifact_stratum=metadata["artifact_stratum"].to_numpy(dtype=str),
        eeg_raw=eeg_raw,
        audio_raw=audio_raw,
        eeg=eeg_standardizer.transform(eeg_raw),
        audio=audio_standardizer.transform(audio_raw),
        eeg_training_mean=eeg_standardizer.mean,
        eeg_training_scale=eeg_standardizer.scale,
        audio_training_mean=audio_standardizer.mean,
        audio_training_scale=audio_standardizer.scale,
    )
    print(
        f"wrote {len(metadata)} rows: EEG {eeg_raw.shape[1]} features, "
        f"audio {audio_raw.shape[1]} features to {args.output}"
    )


if __name__ == "__main__":
    main()
