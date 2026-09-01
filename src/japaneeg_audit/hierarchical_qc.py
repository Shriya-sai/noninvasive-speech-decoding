"""Day-balanced run-level and within-run EEG QC calibration."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd

from japaneeg_audit.qc_thresholds import DEFAULT_DIRECTIONS


METRIC_BOUNDS = {
    "channel_mad_uv_minimum": (0.0, None),
    "channel_peak_to_peak_uv_maximum": (0.0, None),
    "channel_gradient_rms_uv_maximum": (0.0, None),
    "channel_line_noise_ratio_maximum": (0.0, None),
    "absolute_channel_correlation_maximum": (0.0, 1.0),
    "clipped_value_fraction": (0.0, 1.0),
}


def _log_values(values: pd.Series) -> np.ndarray:
    array = values.to_numpy(dtype=float)
    if not np.isfinite(array).all() or np.any(array < 0):
        raise ValueError("hierarchical QC metrics must be finite and non-negative")
    return np.log(np.maximum(array, np.finfo(float).tiny))


def _median_scale(values: np.ndarray) -> tuple[float, float]:
    center = float(np.median(values))
    scale = float(1.4826 * np.median(np.abs(values - center)))
    return center, scale


def fit_hierarchical_qc(
    calibration: pd.DataFrame,
    directions: Mapping[str, str] = DEFAULT_DIRECTIONS,
    run_multiplier: float = 6.0,
    within_run_multiplier: float = 6.0,
) -> dict[str, object]:
    """Fit equal-run log thresholds and fixed within-run robust-z limits."""
    if calibration.empty:
        raise ValueError("cannot fit hierarchical QC to an empty table")
    if set(calibration["subset_role"]) != {"calibration"}:
        raise ValueError("hierarchical QC fitting accepts calibration rows only")
    if run_multiplier <= 0 or within_run_multiplier <= 0:
        raise ValueError("QC multipliers must be positive")
    runs = sorted(calibration["source_run"].unique())
    if len(runs) < 6:
        raise ValueError("hierarchical QC requires at least six calibration runs")

    metrics = {}
    for metric, direction in directions.items():
        if direction not in {"low", "high"}:
            raise ValueError(f"invalid direction for {metric}: {direction}")
        run_log_medians = []
        for _, group in calibration.groupby("source_run", sort=True):
            run_log_medians.append(float(np.median(_log_values(group[metric]))))
        center, scale = _median_scale(np.asarray(run_log_medians))
        signed_limit = (
            center - run_multiplier * scale
            if direction == "low"
            else center + run_multiplier * scale
        )
        threshold = float(np.exp(signed_limit))
        lower, upper = METRIC_BOUNDS.get(metric, (0.0, None))
        threshold = max(lower, threshold)
        if upper is not None:
            threshold = min(upper, threshold)
        metrics[metric] = {
            "direction": direction,
            "transform": "natural_log",
            "run_log_center": center,
            "run_log_robust_scale": scale,
            "run_multiplier": run_multiplier,
            "run_threshold": threshold,
            "within_run_robust_z_threshold": within_run_multiplier,
        }
    return {
        "calibration_unit": "source_run_equal_weight",
        "calibration_runs": len(runs),
        "metrics": metrics,
    }


def apply_hierarchical_qc(
    frame: pd.DataFrame,
    specification: Mapping[str, object],
) -> pd.DataFrame:
    """Apply frozen run-level thresholds and within-run robust deviations."""
    output = pd.DataFrame(index=frame.index)
    metric_specs = specification["metrics"]
    for metric, details in metric_specs.items():
        direction = details["direction"]
        run_threshold = float(details["run_threshold"])
        within_limit = float(details["within_run_robust_z_threshold"])
        run_medians = frame.groupby("source_run")[metric].transform("median")
        output[f"run_flag_{metric}"] = (
            run_medians < run_threshold
            if direction == "low"
            else run_medians > run_threshold
        )

        log_values = pd.Series(_log_values(frame[metric]), index=frame.index)
        run_center = log_values.groupby(frame["source_run"]).transform("median")
        absolute_deviation = (log_values - run_center).abs()
        run_scale = absolute_deviation.groupby(frame["source_run"]).transform(
            "median"
        ) * 1.4826
        signed_z = (log_values - run_center) / run_scale.replace(0, np.nan)
        signed_z = signed_z.fillna(0.0)
        output[f"within_run_z_{metric}"] = signed_z
        output[f"window_flag_{metric}"] = (
            signed_z < -within_limit
            if direction == "low"
            else signed_z > within_limit
        )

    run_flags = [column for column in output if column.startswith("run_flag_")]
    window_flags = [column for column in output if column.startswith("window_flag_")]
    output["run_qc_flagged"] = output[run_flags].any(axis=1)
    output["window_qc_flagged"] = output[window_flags].any(axis=1)
    output["qc_flagged"] = output["run_qc_flagged"] | output["window_qc_flagged"]
    return output
