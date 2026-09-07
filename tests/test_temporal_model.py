import numpy as np
import pytest

from japaneeg_audit.temporal_model import FoldPCA, nested_temporal_leave_one_day_out


def test_fold_pca_is_deterministic_and_fixes_component_sign() -> None:
    rng = np.random.default_rng(7)
    features = rng.normal(size=(30, 12))
    first = FoldPCA(components=4).fit(features)
    second = FoldPCA(components=4).fit(features)
    assert np.allclose(first.components_, second.components_)
    anchors = np.argmax(np.abs(first.components_), axis=1)
    assert np.all(first.components_[np.arange(4), anchors] > 0)


def test_fold_pca_training_transform_is_centered() -> None:
    rng = np.random.default_rng(9)
    features = rng.normal(size=(40, 10))
    transformed = FoldPCA(components=3).fit(features).transform(features)
    assert transformed.shape == (40, 3)
    assert np.allclose(transformed.mean(axis=0), 0.0, atol=1e-10)


def test_fold_pca_rejects_too_many_components() -> None:
    with pytest.raises(ValueError, match="smaller than both"):
        FoldPCA(components=4).fit(np.ones((4, 8)))


def test_nested_temporal_evaluation_reports_held_out_controls() -> None:
    rng = np.random.default_rng(13)
    eeg = rng.normal(size=(24, 4, 3))
    targets = np.concatenate((eeg, eeg), axis=2)
    days = np.repeat(["a", "b", "c", "d"], 6)
    result = nested_temporal_leave_one_day_out(
        eeg,
        targets,
        days,
        [0.1, 10.0],
        components=3,
        lag_bins=(-1, 1),
        permutations=5,
        permutation_seed=17,
    )
    assert set(result["primary"]["days"]) == {"a", "b", "c", "d"}
    assert set(result["temporal_controls"]) == {
        "lag_-1_bins",
        "lag_+1_bins",
        "time_reversed",
    }
    assert result["pairing_null"]["permutations"] == 5
    assert len(result["pairing_null"]["rows"]) == 5
