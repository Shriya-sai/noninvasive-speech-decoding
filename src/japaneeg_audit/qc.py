"""Window-level EEG artifact metrics, independent of rejection thresholds."""

from __future__ import annotations

import numpy as np
from scipy.signal import welch


def _percentile_summary(prefix: str, values: np.ndarray) -> dict[str, float]:
    return {
        f"{prefix}_minimum": float(np.min(values)),
        f"{prefix}_median": float(np.median(values)),
        f"{prefix}_maximum": float(np.max(values)),
    }


def compute_window_qc(
    window_volts: np.ndarray,
    sampling_hz: float,
    standardized_window: np.ndarray | None = None,
) -> dict[str, float | int | bool]:
    """Compute descriptive QC metrics without applying rejection thresholds."""
    window = np.asarray(window_volts, dtype=np.float64)
    if window.ndim != 2 or window.shape[0] != 128:
        raise ValueError("expected a channels-by-time array with 128 channels")
    if window.shape[1] < 2:
        raise ValueError("window must contain at least two time samples")
    if sampling_hz <= 0:
        raise ValueError("sampling_hz must be positive")
    finite = bool(np.isfinite(window).all())
    if not finite:
        raise ValueError("window contains non-finite values")

    microvolts = window * 1e6
    centered = microvolts - np.median(microvolts, axis=1, keepdims=True)
    channel_mad = np.median(np.abs(centered), axis=1)
    channel_std = microvolts.std(axis=1)
    channel_peak_to_peak = np.ptp(microvolts, axis=1)
    channel_gradient_rms = np.sqrt(np.mean(np.diff(microvolts, axis=1) ** 2, axis=1))

    frequencies, power = welch(
        microvolts,
        fs=sampling_hz,
        nperseg=min(window.shape[1], round(2 * sampling_hz)),
        axis=1,
    )
    line_mask = (frequencies >= 49.0) & (frequencies <= 51.0)
    reference_mask = (frequencies >= 45.0) & (frequencies <= 55.0) & ~line_mask
    line_power = power[:, line_mask].mean(axis=1)
    reference_power = power[:, reference_mask].mean(axis=1)
    line_ratio = line_power / (reference_power + np.finfo(float).eps)

    correlations = np.corrcoef(microvolts)
    upper = np.abs(correlations[np.triu_indices_from(correlations, k=1)])
    result: dict[str, float | int | bool] = {
        "finite": finite,
        "channels": int(window.shape[0]),
        "samples": int(window.shape[1]),
        **_percentile_summary("channel_mad_uv", channel_mad),
        **_percentile_summary("channel_std_uv", channel_std),
        **_percentile_summary("channel_peak_to_peak_uv", channel_peak_to_peak),
        **_percentile_summary("channel_gradient_rms_uv", channel_gradient_rms),
        **_percentile_summary("channel_line_noise_ratio", line_ratio),
        "absolute_channel_correlation_median": float(np.median(upper)),
        "absolute_channel_correlation_maximum": float(np.max(upper)),
    }
    if standardized_window is not None:
        standardized = np.asarray(standardized_window)
        if standardized.shape != window.shape:
            raise ValueError("standardized window shape does not match raw window")
        result["clipped_value_fraction"] = float(
            np.mean(np.abs(standardized) >= 5.0)
        )
    return result
