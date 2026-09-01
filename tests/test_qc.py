import numpy as np
import pytest

from japaneeg_audit.qc import compute_window_qc


def _window(seed: int = 1) -> np.ndarray:
    return np.random.default_rng(seed).normal(0, 2e-6, size=(128, 1200))


def test_qc_reports_expected_dimensions_and_finite_metrics() -> None:
    result = compute_window_qc(_window(), 240.0)
    assert result["finite"] is True
    assert result["channels"] == 128
    assert result["samples"] == 1200
    assert all(np.isfinite(value) for value in result.values())


def test_qc_detects_large_peak_to_peak_channel() -> None:
    window = _window()
    window[3, 100] = 1e-3
    result = compute_window_qc(window, 240.0)
    assert result["channel_peak_to_peak_uv_maximum"] > 900


def test_clipping_fraction_is_reported() -> None:
    window = _window()
    standardized = np.zeros_like(window)
    standardized[:, :12] = 5.0
    result = compute_window_qc(window, 240.0, standardized)
    assert result["clipped_value_fraction"] == pytest.approx(0.01)


def test_wrong_shape_fails() -> None:
    with pytest.raises(ValueError, match="128 channels"):
        compute_window_qc(np.zeros((127, 1200)), 240.0)


def test_nonfinite_signal_fails() -> None:
    window = _window()
    window[0, 0] = np.nan
    with pytest.raises(ValueError, match="non-finite"):
        compute_window_qc(window, 240.0)


def test_standardized_shape_must_match() -> None:
    with pytest.raises(ValueError, match="shape does not match"):
        compute_window_qc(_window(), 240.0, np.zeros((128, 600)))
