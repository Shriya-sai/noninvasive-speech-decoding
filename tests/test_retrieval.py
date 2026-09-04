import numpy as np
import pytest

from japaneeg_audit.retrieval import (
    RidgeRegression,
    evaluate_by_day,
    macro_average,
    nested_leave_one_day_out,
    permute_within_groups,
    retrieval_metrics,
    select_ridge_alpha,
)


def test_ridge_recovers_linear_multioutput_mapping() -> None:
    rng = np.random.default_rng(3)
    features = rng.normal(size=(40, 4))
    weights = rng.normal(size=(4, 3))
    targets = features @ weights + np.array([1.0, -2.0, 0.5])
    predicted = RidgeRegression(alpha=1e-8).fit(features, targets).predict(features)
    assert np.allclose(predicted, targets, atol=1e-7)


def test_perfect_retrieval() -> None:
    target = np.eye(12)
    metrics = retrieval_metrics(target, target)
    assert metrics["top_1_accuracy"] == 1.0
    assert metrics["top_10_accuracy"] == 1.0
    assert metrics["mean_reciprocal_rank"] == 1.0


def test_retrieval_rejects_zero_vectors() -> None:
    with pytest.raises(ValueError, match="zero vectors"):
        retrieval_metrics(np.zeros((2, 3)), np.ones((2, 3)))


def test_evaluation_keeps_day_candidate_sets_separate() -> None:
    target = np.vstack([np.eye(2), np.eye(2)])
    result = evaluate_by_day(target, target, ["day1", "day1", "day2", "day2"])
    assert set(result) == {"day1", "day2"}
    assert all(metrics["candidates"] == 2 for metrics in result.values())


def test_macro_average_equal_weights_days() -> None:
    result = macro_average(
        {
            "short": {
                "top_1_accuracy": 0.0,
                "top_10_accuracy": 0.0,
                "mean_reciprocal_rank": 0.0,
            },
            "long": {
                "top_1_accuracy": 1.0,
                "top_10_accuracy": 1.0,
                "mean_reciprocal_rank": 1.0,
            },
        }
    )
    assert result == {
        "top_1_accuracy": 0.5,
        "top_10_accuracy": 0.5,
        "mean_reciprocal_rank": 0.5,
    }


def test_alpha_selection_uses_validation_predictions() -> None:
    rng = np.random.default_rng(7)
    train_x = rng.normal(size=(30, 4))
    weights = rng.normal(size=(4, 5))
    train_y = train_x @ weights
    validation_x = rng.normal(size=(12, 4))
    validation_y = validation_x @ weights
    alpha, rows = select_ridge_alpha(
        train_x,
        train_y,
        validation_x,
        validation_y,
        ["validation"] * 12,
        [1000.0, 0.01],
    )
    assert alpha == 0.01
    assert [row["alpha"] for row in rows] == [0.01, 1000.0]


def test_grouped_permutation_is_reproducible_and_within_group() -> None:
    target = np.arange(18).reshape(6, 3)
    groups = ["a", "a", "a", "b", "b", "b"]
    first = permute_within_groups(target, groups, seed=101)
    second = permute_within_groups(target, groups, seed=101)
    assert np.array_equal(first, second)
    assert {tuple(row) for row in first[:3]} == {tuple(row) for row in target[:3]}
    assert {tuple(row) for row in first[3:]} == {tuple(row) for row in target[3:]}


def test_nested_day_resampling_returns_every_outer_day() -> None:
    rng = np.random.default_rng(11)
    features = rng.normal(size=(16, 3))
    targets = np.column_stack((features[:, 0], features[:, 1]))
    days = np.repeat(["a", "b", "c", "d"], 4)
    result = nested_leave_one_day_out(features, targets, days, [0.01, 10.0])
    assert set(result["days"]) == {"a", "b", "c", "d"}
    assert set(result["macro"]) == {
        "top_1_accuracy",
        "top_10_accuracy",
        "mean_reciprocal_rank",
    }


def test_nested_day_resampling_requires_four_days() -> None:
    with pytest.raises(ValueError, match="at least four days"):
        nested_leave_one_day_out(
            np.eye(3), np.eye(3), ["a", "b", "c"], [1.0]
        )
