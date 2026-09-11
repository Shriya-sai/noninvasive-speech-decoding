import importlib.util
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).parents[1] / "scripts" / "run_confirmation_evaluation.py"
SPEC = importlib.util.spec_from_file_location("confirmation_evaluator", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_saved_model_application_is_exact_matrix_path() -> None:
    eeg = np.arange(24, dtype=float).reshape(3, 2, 4)
    model = {
        "pca_mean": np.arange(8, dtype=float),
        "pca_scale": np.full(8, 2.0),
        "pca_components": np.eye(3, 8),
        "ridge_feature_mean": np.array([1.0, 2.0, 3.0]),
        "ridge_coefficient": np.arange(6, dtype=float).reshape(3, 2),
        "ridge_target_mean": np.array([0.5, -0.5]),
    }
    flat = eeg.reshape(3, 8)
    reduced = ((flat - model["pca_mean"]) / model["pca_scale"]) @ model["pca_components"].T
    expected = ((reduced - model["ridge_feature_mean"]) @ model["ridge_coefficient"]
                + model["ridge_target_mean"])
    assert np.array_equal(MODULE.apply_saved_model(model, eeg), expected)


def test_candidate_reference_is_exact() -> None:
    reference = MODULE.candidate_reference(4)
    assert reference["top_1_accuracy"] == 0.25
    assert reference["top_10_accuracy"] == 1.0
    assert np.isclose(
        reference["mean_reciprocal_rank"], (1 + 1 / 2 + 1 / 3 + 1 / 4) / 4
    )
