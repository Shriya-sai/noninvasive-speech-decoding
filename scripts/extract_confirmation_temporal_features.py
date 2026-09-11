#!/usr/bin/env python3
"""Extract frozen temporal features from confirmation-eligible rows only."""

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
    LogMelConfig,
    extract_rms_envelope,
    extract_temporal_eeg_statistics,
    extract_temporal_log_mel,
)
from japaneeg_audit.preprocessing import (
    extract_standardized_window,
    preprocess_continuous_eeg,
)


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
    if np.issubdtype(segment.dtype, np.integer):
        info = np.iinfo(segment.dtype)
        segment = segment.astype(np.float64) / max(abs(info.min), info.max)
    else:
        segment = segment.astype(np.float64)
    divisor = math.gcd(source_hz, target_hz)
    resampled = signal.resample_poly(
        segment, target_hz // divisor, source_hz // divisor
    )
    expected = round((end_seconds - start_seconds) * target_hz)
    if abs(len(resampled) - expected) > 1:
        raise ValueError("resampled audio window has an unexpected length")
    return resampled[:expected]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("model_manifest", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/temporal_ridge_v1.toml")
    )
    parser.add_argument(
        "--subset-config",
        type=Path,
        default=Path("configs/replacement_confirmation_v1.toml"),
    )
    args = parser.parse_args()

    config = tomllib.loads(args.config.read_text())
    subset = tomllib.loads(args.subset_config.read_text())
    input_config = config["input"]
    target_config = config["target"]
    mel_config = LogMelConfig(
        sampling_hz=target_config["sample_rate_hz"],
        mel_bins=target_config["mel_bins"],
        frame_samples=target_config["frame_samples"],
        hop_samples=target_config["hop_samples"],
        fft_samples=target_config["fft_samples"],
        minimum_hz=target_config["minimum_hz"],
        maximum_hz=target_config["maximum_hz"],
        power_floor=target_config["power_floor"],
    )
    paths = {run["id"]: run for run in subset["runs"]}
    manifest = pd.read_csv(args.model_manifest, sep="\t")
    if set(manifest["subset_role"]) != {"confirmation"}:
        raise ValueError("confirmation manifest must contain only confirmation rows")
    expected_runs = {run["id"] for run in subset["runs"]}
    unexpected = set(manifest["source_run"]).difference(expected_runs)
    if unexpected:
        raise ValueError(f"unexpected confirmation runs: {sorted(unexpected)}")
    manifest = manifest.loc[manifest["model_eligible"]].copy()
    if manifest.empty or manifest["source_run"].nunique() < 2:
        raise ValueError("confirmation requires eligible rows from at least two days")
    manifest = manifest.sort_values(["source_run", "window_index"])

    eeg_rows = []
    target_rows = []
    envelope_rows = []
    metadata_rows = []
    for source_run, rows in manifest.groupby("source_run", sort=True):
        run = paths[source_run]
        raw = preprocess_continuous_eeg(args.dataset_root / run["eeg"])
        source_hz, audio = wavfile.read(
            args.dataset_root / run["audio"], mmap=True
        )
        for row in rows.itertuples(index=False):
            eeg = extract_standardized_window(raw, row.eeg_start_seconds)
            vocal = _audio_window(
                audio,
                source_hz,
                row.audio_start_seconds,
                row.audio_end_seconds,
                target_config["sample_rate_hz"],
            )
            eeg_rows.append(
                extract_temporal_eeg_statistics(
                    eeg,
                    bins=input_config["temporal_bins"],
                    power_floor=input_config["power_floor"],
                )
            )
            target_rows.append(
                extract_temporal_log_mel(
                    vocal, bins=target_config["temporal_bins"], config=mel_config
                )
            )
            envelope_rows.append(
                extract_rms_envelope(vocal, bins=target_config["temporal_bins"])
            )
        metadata_rows.append(rows)
        print(f"{source_run} {len(rows)} windows", flush=True)

    metadata = pd.concat(metadata_rows, ignore_index=True)
    eeg = np.stack(eeg_rows)
    target = np.stack(target_rows)
    envelope = np.stack(envelope_rows)
    expected = (
        len(metadata),
        input_config["temporal_bins"],
        input_config["channels"] * len(input_config["statistics"]),
    )
    if eeg.shape != expected:
        raise ValueError(f"unexpected temporal EEG shape: {eeg.shape}")
    if target.shape != (
        len(metadata), target_config["temporal_bins"], target_config["mel_bins"]
    ):
        raise ValueError(f"unexpected temporal target shape: {target.shape}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.output,
        window_id=metadata["window_id"].to_numpy(dtype=str),
        source_run=metadata["source_run"].to_numpy(dtype=str),
        subset_role=metadata["subset_role"].to_numpy(dtype=str),
        artifact_stratum=metadata["artifact_stratum"].to_numpy(dtype=str),
        eeg_temporal_raw=eeg,
        audio_temporal_raw=target,
        audio_envelope_raw=envelope,
    )
    print(
        f"wrote {len(metadata)} confirmation rows: EEG {eeg.shape}, "
        f"audio {target.shape}, envelope {envelope.shape} to {args.output}"
    )


if __name__ == "__main__":
    main()
