from pathlib import Path

import mne
import numpy as np
import pandas as pd
import pytest

from japaneeg_audit.preprocessing import (
    PreprocessingConfig,
    apply_bids_channel_types,
    extract_standardized_window,
)


def _raw(channel_count: int = 128, seconds: float = 10.0) -> mne.io.RawArray:
    sampling_hz = 240.0
    times = np.arange(round(seconds * sampling_hz)) / sampling_hz
    data = np.vstack(
        [np.sin(2 * np.pi * (index + 1) * times / 20) for index in range(channel_count)]
    )
    info = mne.create_info(
        [f"EEG{index + 1:03d}" for index in range(channel_count)],
        sampling_hz,
        ch_types="eeg",
    )
    return mne.io.RawArray(data, info, verbose="ERROR")


def test_bids_channel_types_are_restored(tmp_path: Path) -> None:
    raw = _raw(channel_count=5)
    table = pd.DataFrame(
        {
            "name": raw.ch_names,
            "type": ["EEG", "EOG", "EMG", "MISC", "TRIG"],
        }
    )
    path = tmp_path / "channels.tsv"
    table.to_csv(path, sep="\t", index=False)
    apply_bids_channel_types(raw, path)
    assert raw.get_channel_types() == ["eeg", "eog", "emg", "misc", "stim"]


def test_channel_order_mismatch_fails(tmp_path: Path) -> None:
    raw = _raw(channel_count=2)
    path = tmp_path / "channels.tsv"
    pd.DataFrame(
        {"name": list(reversed(raw.ch_names)), "type": ["EEG", "EEG"]}
    ).to_csv(path, sep="\t", index=False)
    with pytest.raises(ValueError, match="names/order"):
        apply_bids_channel_types(raw, path)


def test_unknown_channel_type_fails(tmp_path: Path) -> None:
    raw = _raw(channel_count=1)
    path = tmp_path / "channels.tsv"
    pd.DataFrame({"name": raw.ch_names, "type": ["UNKNOWN"]}).to_csv(
        path, sep="\t", index=False
    )
    with pytest.raises(ValueError, match="unsupported BIDS channel types"):
        apply_bids_channel_types(raw, path)


def test_window_shape_dtype_and_normalization() -> None:
    window = extract_standardized_window(_raw(), 0.0)
    assert window.shape == (128, 1200)
    assert window.dtype == np.float32
    assert np.isfinite(window).all()
    assert np.abs(window.mean(axis=1)).max() < 1e-5
    assert np.abs(window.std(axis=1) - 1).max() < 1e-5


def test_window_is_clipped() -> None:
    raw = _raw()
    raw._data[0, 100] = 1_000_000
    window = extract_standardized_window(raw, 0.0)
    assert window.min() >= -5.0
    assert window.max() <= 5.0


def test_incomplete_window_fails() -> None:
    with pytest.raises(ValueError, match="incomplete EEG window"):
        extract_standardized_window(_raw(seconds=5.0), 1.0)


def test_constant_channel_fails() -> None:
    raw = _raw()
    raw._data[0] = 0
    with pytest.raises(ValueError, match="constant or non-finite"):
        extract_standardized_window(raw, 0.0)


def test_nondefault_window_has_exact_sample_count() -> None:
    config = PreprocessingConfig(window_seconds=2.5)
    assert extract_standardized_window(_raw(), 2.5, config).shape == (128, 600)
