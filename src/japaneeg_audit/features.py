"""Frozen baseline EEG and vocal-audio feature extraction."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import signal


@dataclass(frozen=True)
class BandpowerConfig:
    sampling_hz: float = 240.0
    bands_hz: tuple[tuple[float, float], ...] = (
        (2.0, 4.0),
        (4.0, 8.0),
        (8.0, 13.0),
        (13.0, 30.0),
        (30.0, 55.0),
        (65.0, 120.0),
    )
    segment_samples: int = 240
    overlap_samples: int = 120
    power_floor: float = 1e-12


@dataclass(frozen=True)
class LogMelConfig:
    sampling_hz: int = 16_000
    mel_bins: int = 80
    frame_samples: int = 400
    hop_samples: int = 160
    fft_samples: int = 512
    minimum_hz: float = 20.0
    maximum_hz: float = 7_600.0
    power_floor: float = 1e-12


def extract_log_bandpower(
    eeg: np.ndarray,
    config: BandpowerConfig = BandpowerConfig(),
) -> np.ndarray:
    """Return channel-major log integrated Welch power in fixed bands."""
    array = np.asarray(eeg, dtype=np.float64)
    if array.ndim != 2 or array.shape[1] < config.segment_samples:
        raise ValueError("EEG must be channels by sufficient time samples")
    if not np.isfinite(array).all():
        raise ValueError("EEG contains non-finite values")
    frequencies, density = signal.welch(
        array,
        fs=config.sampling_hz,
        window="hann",
        nperseg=config.segment_samples,
        noverlap=config.overlap_samples,
        axis=1,
        scaling="density",
    )
    features = []
    for low, high in config.bands_hz:
        if low < 0 or high <= low or high > config.sampling_hz / 2:
            raise ValueError(f"invalid band: {low}-{high} Hz")
        include = (frequencies >= low) & (frequencies <= high)
        if include.sum() < 2:
            raise ValueError(f"band has insufficient frequency bins: {low}-{high}")
        power = np.trapezoid(density[:, include], frequencies[include], axis=1)
        features.append(np.log(np.maximum(power, config.power_floor)))
    output = np.stack(features, axis=1).reshape(-1)
    if not np.isfinite(output).all():
        raise ValueError("bandpower features are non-finite")
    return output.astype(np.float32)


def _hz_to_mel(frequency: np.ndarray | float) -> np.ndarray:
    return 2595.0 * np.log10(1.0 + np.asarray(frequency) / 700.0)


def _mel_to_hz(mel: np.ndarray | float) -> np.ndarray:
    return 700.0 * (10.0 ** (np.asarray(mel) / 2595.0) - 1.0)


def mel_filterbank(config: LogMelConfig = LogMelConfig()) -> np.ndarray:
    """Construct unit-area triangular mel filters for one-sided spectra."""
    if not 0 <= config.minimum_hz < config.maximum_hz <= config.sampling_hz / 2:
        raise ValueError("mel frequency bounds exceed the audio Nyquist range")
    mel_edges = np.linspace(
        _hz_to_mel(config.minimum_hz),
        _hz_to_mel(config.maximum_hz),
        config.mel_bins + 2,
    )
    edges = _mel_to_hz(mel_edges)
    frequencies = np.fft.rfftfreq(config.fft_samples, 1.0 / config.sampling_hz)
    filters = np.zeros((config.mel_bins, len(frequencies)), dtype=np.float64)
    for index, (left, center, right) in enumerate(
        zip(edges[:-2], edges[1:-1], edges[2:], strict=True)
    ):
        filters[index] = np.minimum(
            (frequencies - left) / (center - left),
            (right - frequencies) / (right - center),
        ).clip(0.0)
        area = np.trapezoid(filters[index], frequencies)
        if area <= 0:
            raise ValueError("mel filter has zero area")
        filters[index] /= area
    return filters


def extract_log_mel_summary(
    audio: np.ndarray,
    config: LogMelConfig = LogMelConfig(),
) -> np.ndarray:
    """Return concatenated temporal mean and SD of log-mel power."""
    array = np.asarray(audio, dtype=np.float64)
    if array.ndim != 1 or len(array) < config.frame_samples:
        raise ValueError("audio must be a mono vector with at least one frame")
    if not np.isfinite(array).all():
        raise ValueError("audio contains non-finite values")
    _, _, spectrum = signal.stft(
        array,
        fs=config.sampling_hz,
        window="hann",
        nperseg=config.frame_samples,
        noverlap=config.frame_samples - config.hop_samples,
        nfft=config.fft_samples,
        boundary=None,
        padded=False,
    )
    power = np.abs(spectrum) ** 2
    mel_power = mel_filterbank(config) @ power
    log_mel = np.log(np.maximum(mel_power, config.power_floor))
    output = np.concatenate((log_mel.mean(axis=1), log_mel.std(axis=1)))
    if not np.isfinite(output).all():
        raise ValueError("log-mel features are non-finite")
    return output.astype(np.float32)


@dataclass(frozen=True)
class TrainingStandardizer:
    mean: np.ndarray
    scale: np.ndarray

    @classmethod
    def fit(cls, features: np.ndarray) -> TrainingStandardizer:
        """Fit featurewise statistics to calibration rows only."""
        array = np.asarray(features, dtype=np.float64)
        if array.ndim != 2 or len(array) < 2 or not np.isfinite(array).all():
            raise ValueError("training features must be a finite two-dimensional table")
        mean = array.mean(axis=0)
        scale = array.std(axis=0)
        if np.any(scale == 0):
            raise ValueError("training features contain a constant column")
        return cls(mean=mean, scale=scale)

    def transform(self, features: np.ndarray) -> np.ndarray:
        array = np.asarray(features, dtype=np.float64)
        if array.ndim != 2 or array.shape[1] != len(self.mean):
            raise ValueError("feature table does not match fitted standardizer")
        output = (array - self.mean) / self.scale
        if not np.isfinite(output).all():
            raise ValueError("standardized features are non-finite")
        return output.astype(np.float32)
