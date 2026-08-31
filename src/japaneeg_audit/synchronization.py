"""Waveform-level validation of the BIDS EEG-to-WAV time mapping."""

from __future__ import annotations

from pathlib import Path

import mne
import numpy as np
import pandas as pd
from scipy.io import wavfile
from scipy.signal import butter, correlate, resample_poly, sosfiltfilt


def validate_waveform_sync(
    eeg_path: Path,
    audio_path: Path,
    monitor_channels: tuple[str, ...] = ("EEG131", "EEG132"),
    envelope_hz: float = 8.0,
    event_padding_seconds: float = 1.0,
    maximum_residual_seconds: float = 0.5,
    minimum_median_correlation: float = 0.10,
    maximum_absolute_median_residual: float = 0.25,
) -> dict[str, object]:
    """Compare event-local monitor and WAV amplitude envelopes."""
    stem = eeg_path.name.removesuffix("_eeg.edf")
    events = pd.read_csv(eeg_path.with_name(f"{stem}_events.tsv"), sep="\t")
    raw = mne.io.read_raw_edf(eeg_path, preload=False, verbose="ERROR")
    eeg_rate = int(round(raw.info["sfreq"]))
    monitors = raw.get_data(picks=list(monitor_channels))

    audio_rate, audio = wavfile.read(audio_path)
    if audio.ndim == 1:
        audio = audio[:, None]
    audio = resample_poly(audio.astype(np.float64), eeg_rate, audio_rate, axis=0).T

    lowpass = butter(2, envelope_hz, fs=eeg_rate, output="sos")
    monitor_envelopes = sosfiltfilt(
        lowpass,
        np.abs(monitors - np.median(monitors, axis=1, keepdims=True)),
        axis=1,
    )
    audio_envelopes = sosfiltfilt(
        lowpass,
        np.abs(audio - np.median(audio, axis=1, keepdims=True)),
        axis=1,
    )

    pairs = []
    max_lag = round(maximum_residual_seconds * eeg_rate)
    for monitor_index, monitor_name in enumerate(monitor_channels):
        for audio_channel in range(audio.shape[0]):
            residuals = []
            correlations = []
            for event in events.itertuples():
                eeg_start = max(0, round((event.onset - event_padding_seconds) * eeg_rate))
                eeg_end = min(
                    monitors.shape[1],
                    round((event.onset + event.duration + event_padding_seconds) * eeg_rate),
                )
                wav_start = round((event.wav_onset - event_padding_seconds) * eeg_rate)
                wav_end = wav_start + (eeg_end - eeg_start)
                if wav_start < 0 or wav_end > audio.shape[1]:
                    continue
                x = monitor_envelopes[monitor_index, eeg_start:eeg_end]
                y = audio_envelopes[audio_channel, wav_start:wav_end]
                x = (x - x.mean()) / (x.std() + np.finfo(float).eps)
                y = (y - y.mean()) / (y.std() + np.finfo(float).eps)
                values = correlate(y, x, mode="same", method="fft")
                midpoint = len(values) // 2
                local = values[midpoint - max_lag : midpoint + max_lag + 1]
                peak_index = int(np.argmax(local))
                residuals.append((peak_index - max_lag) / eeg_rate)
                correlations.append(float(local[peak_index] / len(x)))
            pairs.append(
                {
                    "monitor_channel": monitor_name,
                    "wav_channel": audio_channel,
                    "events": len(correlations),
                    "median_residual_seconds": float(np.median(residuals)),
                    "median_envelope_correlation": float(np.median(correlations)),
                    "lower_quartile_envelope_correlation": float(
                        np.quantile(correlations, 0.25)
                    ),
                }
            )

    best = max(pairs, key=lambda pair: pair["median_envelope_correlation"])
    passed = bool(
        best["median_envelope_correlation"] >= minimum_median_correlation
        and abs(best["median_residual_seconds"])
        <= maximum_absolute_median_residual
    )
    return {
        "run": stem,
        "method": {
            "monitor_channels": list(monitor_channels),
            "envelope_lowpass_hz": envelope_hz,
            "event_padding_seconds": event_padding_seconds,
            "residual_search_seconds": maximum_residual_seconds,
            "minimum_median_correlation": minimum_median_correlation,
            "maximum_absolute_median_residual_seconds": (
                maximum_absolute_median_residual
            ),
        },
        "pairs": pairs,
        "best_pair": best,
        "passes_gate": passed,
    }
