"""Calibration-only robust thresholds for descriptive EEG QC metrics."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd


DEFAULT_DIRECTIONS = {
    "channel_mad_uv_minimum": "low",
    "channel_peak_to_peak_uv_maximum": "high",
    "channel_gradient_rms_uv_maximum": "high",
    "channel_line_noise_ratio_maximum": "high",
    "absolute_channel_correlation_maximum": "high",
    "clipped_value_fraction": "high",
}


def fit_robust_thresholds(
    frame: pd.DataFrame,
    directions: Mapping[str, str] = DEFAULT_DIRECTIONS,
    multiplier: float = 6.0,
    permitted_roles: Sequence[str] = ("calibration",),
) -> dict[str, dict[str, float | str]]:
    """Fit median/MAD thresholds using explicitly permitted rows only."""
    if multiplier <= 0:
        raise ValueError("multiplier must be positive")
    if "subset_role" not in frame:
        raise ValueError("QC table lacks subset_role")
    unexpected = sorted(set(frame["subset_role"]) - set(permitted_roles))
    if unexpected:
        raise ValueError(
            "threshold fitting received forbidden roles: " + ", ".join(unexpected)
        )
    if frame.empty:
        raise ValueError("cannot fit thresholds to an empty table")

    fitted = {}
    for metric, direction in directions.items():
        if direction not in {"low", "high"}:
            raise ValueError(f"invalid direction for {metric}: {direction}")
        values = frame[metric].to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise ValueError(f"non-finite calibration metric: {metric}")
        median = float(np.median(values))
        mad = float(np.median(np.abs(values - median)))
        robust_scale = 1.4826 * mad
        threshold = (
            median - multiplier * robust_scale
            if direction == "low"
            else median + multiplier * robust_scale
        )
        fitted[metric] = {
            "direction": direction,
            "median": median,
            "mad": mad,
            "robust_scale": robust_scale,
            "multiplier": multiplier,
            "threshold": threshold,
        }
    return fitted


def apply_thresholds(
    frame: pd.DataFrame,
    thresholds: Mapping[str, Mapping[str, float | str]],
) -> pd.DataFrame:
    """Return metric flags and an aggregate rejection decision."""
    flags = pd.DataFrame(index=frame.index)
    for metric, specification in thresholds.items():
        direction = specification["direction"]
        threshold = float(specification["threshold"])
        if direction == "low":
            flags[f"flag_{metric}"] = frame[metric] < threshold
        elif direction == "high":
            flags[f"flag_{metric}"] = frame[metric] > threshold
        else:
            raise ValueError(f"invalid direction for {metric}: {direction}")
    flags["artifact_rejected"] = flags.any(axis=1)
    return flags
