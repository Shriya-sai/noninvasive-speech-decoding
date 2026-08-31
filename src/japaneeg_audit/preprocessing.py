"""Continuous EEG preprocessing and fixed-window extraction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import mne
import numpy as np
import pandas as pd


_BIDS_TO_MNE = {
    "EEG": "eeg",
    "EOG": "eog",
    "EMG": "emg",
    "MISC": "misc",
    "TRIG": "stim",
}


@dataclass(frozen=True)
class PreprocessingConfig:
    notch_hz: float = 50.0
    bandpass_low_hz: float = 2.0
    bandpass_high_hz: float = 120.0
    output_sampling_hz: float = 240.0
    window_seconds: float = 5.0
    clip_minimum: float = -5.0
    clip_maximum: float = 5.0


def channels_path_for(eeg_path: Path) -> Path:
    stem = eeg_path.name.removesuffix("_eeg.edf")
    return eeg_path.with_name(f"{stem}_channels.tsv")


def apply_bids_channel_types(raw: mne.io.BaseRaw, channels_path: Path) -> None:
    """Restore MNE channel types from the run's BIDS channel table."""
    channels = pd.read_csv(channels_path, sep="\t")
    required = {"name", "type"}
    missing = required.difference(channels.columns)
    if missing:
        raise ValueError(
            f"channels.tsv missing columns: {', '.join(sorted(missing))}"
        )
    names = channels["name"].astype(str).tolist()
    if names != raw.ch_names:
        raise ValueError("channels.tsv names/order do not match the EDF")
    unknown = sorted(set(channels["type"]) - set(_BIDS_TO_MNE))
    if unknown:
        raise ValueError(f"unsupported BIDS channel types: {', '.join(unknown)}")
    mapping = {
        name: _BIDS_TO_MNE[channel_type]
        for name, channel_type in zip(names, channels["type"], strict=True)
    }
    raw.set_channel_types(mapping, verbose="ERROR")


def load_typed_raw(eeg_path: Path) -> mne.io.BaseRaw:
    """Load an EDF lazily and restore its BIDS-declared signal roles."""
    raw = mne.io.read_raw_edf(eeg_path, preload=False, verbose="ERROR")
    apply_bids_channel_types(raw, channels_path_for(eeg_path))
    return raw


def preprocess_continuous_eeg(
    eeg_path: Path,
    config: PreprocessingConfig = PreprocessingConfig(),
) -> mne.io.BaseRaw:
    """Apply the reported continuous EEG operations through resampling."""
    raw = load_typed_raw(eeg_path)
    raw.pick("eeg")
    if len(raw.ch_names) != 128:
        raise ValueError(f"expected 128 EEG channels, found {len(raw.ch_names)}")
    if config.bandpass_high_hz >= raw.info["sfreq"] / 2:
        raise ValueError("band-pass high edge must be below the input Nyquist rate")

    raw.load_data(verbose="ERROR")
    raw.notch_filter(freqs=[config.notch_hz], verbose="ERROR")
    raw.set_eeg_reference(ref_channels="average", projection=False, verbose="ERROR")
    raw.filter(
        l_freq=config.bandpass_low_hz,
        h_freq=config.bandpass_high_hz,
        verbose="ERROR",
    )
    raw.resample(config.output_sampling_hz, verbose="ERROR")
    return raw


def extract_standardized_window(
    raw: mne.io.BaseRaw,
    eeg_start_seconds: float,
    config: PreprocessingConfig = PreprocessingConfig(),
) -> np.ndarray:
    """Extract one complete window, z-score per channel, and clip."""
    if eeg_start_seconds < 0:
        raise ValueError("window start must be non-negative")
    expected_samples = round(config.window_seconds * config.output_sampling_hz)
    start = raw.time_as_index(eeg_start_seconds, use_rounding=True)[0]
    stop = start + expected_samples
    if stop > raw.n_times:
        raise ValueError("incomplete EEG window")
    window = raw.get_data(start=start, stop=stop)
    if window.shape != (128, expected_samples):
        raise ValueError(
            f"expected window shape (128, {expected_samples}), got {window.shape}"
        )
    means = window.mean(axis=1, keepdims=True)
    scales = window.std(axis=1, keepdims=True)
    if np.any(scales == 0) or not np.isfinite(scales).all():
        raise ValueError("window contains a constant or non-finite channel")
    standardized = (window - means) / scales
    standardized = np.clip(
        standardized,
        config.clip_minimum,
        config.clip_maximum,
    )
    if not np.isfinite(standardized).all():
        raise ValueError("preprocessed window contains non-finite values")
    return standardized.astype(np.float32)
