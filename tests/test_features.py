import numpy as np
import pytest

from japaneeg_audit.features import (
    BandpowerConfig,
    LogMelConfig,
    TrainingStandardizer,
    extract_log_bandpower,
    extract_log_mel_summary,
    mel_filterbank,
)


def test_log_bandpower_finds_expected_frequency_band() -> None:
    sampling_hz = 240.0
    time = np.arange(1200) / sampling_hz
    eeg = np.vstack(
        [np.sin(2 * np.pi * 10 * time), np.sin(2 * np.pi * 40 * time)]
    )
    features = extract_log_bandpower(eeg).reshape(2, 6)
    assert features.shape == (2, 6)
    assert features[0].argmax() == 2
    assert features[1].argmax() == 4


def test_invalid_band_fails() -> None:
    config = BandpowerConfig(bands_hz=((100.0, 121.0),))
    with pytest.raises(ValueError, match="invalid band"):
        extract_log_bandpower(np.ones((2, 1200)), config)


def test_mel_filterbank_shape_area_and_finiteness() -> None:
    config = LogMelConfig(mel_bins=12)
    filters = mel_filterbank(config)
    assert filters.shape == (12, 257)
    assert np.isfinite(filters).all()
    assert (filters >= 0).all()


def test_log_mel_summary_shape_and_tone_dependence() -> None:
    config = LogMelConfig(mel_bins=20)
    time = np.arange(16_000) / 16_000
    low = extract_log_mel_summary(np.sin(2 * np.pi * 200 * time), config)
    high = extract_log_mel_summary(np.sin(2 * np.pi * 2000 * time), config)
    assert low.shape == high.shape == (40,)
    assert np.isfinite(low).all()
    assert not np.allclose(low, high)


def test_standardizer_uses_fitted_statistics_for_later_rows() -> None:
    training = np.array([[0.0, 10.0], [2.0, 14.0], [4.0, 12.0]])
    standardizer = TrainingStandardizer.fit(training)
    transformed_training = standardizer.transform(training)
    transformed_test = standardizer.transform(np.array([[8.0, 20.0]]))
    assert np.allclose(transformed_training.mean(axis=0), 0.0, atol=1e-6)
    assert np.allclose(transformed_training.std(axis=0), 1.0, atol=1e-6)
    assert transformed_test[0, 0] > 2.0


def test_standardizer_rejects_constant_training_column() -> None:
    with pytest.raises(ValueError, match="constant column"):
        TrainingStandardizer.fit(np.ones((3, 2)))
