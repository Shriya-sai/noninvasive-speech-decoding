"""Leakage-safe linear retrieval baselines and held-out-day metrics."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import numpy as np


class RidgeRegression:
    """Multi-output ridge regression with an unpenalized intercept."""

    def __init__(self, alpha: float):
        if alpha <= 0:
            raise ValueError("ridge alpha must be positive")
        self.alpha = float(alpha)

    def fit(self, features: np.ndarray, targets: np.ndarray) -> RidgeRegression:
        features = np.asarray(features, dtype=np.float64)
        targets = np.asarray(targets, dtype=np.float64)
        if features.ndim != 2 or targets.ndim != 2 or len(features) != len(targets):
            raise ValueError("ridge features and targets must be aligned 2D tables")
        if len(features) < 2 or not np.isfinite(features).all():
            raise ValueError("ridge training features must contain finite rows")
        if not np.isfinite(targets).all():
            raise ValueError("ridge training targets must be finite")
        self.feature_mean_ = features.mean(axis=0)
        self.target_mean_ = targets.mean(axis=0)
        centered_x = features - self.feature_mean_
        centered_y = targets - self.target_mean_
        left, singular, right = np.linalg.svd(centered_x, full_matrices=False)
        shrinkage = singular / (singular**2 + self.alpha)
        self.coefficient_ = (right.T * shrinkage) @ (left.T @ centered_y)
        return self

    def predict(self, features: np.ndarray) -> np.ndarray:
        if not hasattr(self, "coefficient_"):
            raise ValueError("ridge model must be fitted before prediction")
        features = np.asarray(features, dtype=np.float64)
        if features.ndim != 2 or features.shape[1] != len(self.feature_mean_):
            raise ValueError("prediction features do not match fitted ridge model")
        return (features - self.feature_mean_) @ self.coefficient_ + self.target_mean_


def retrieval_metrics(predicted: np.ndarray, target: np.ndarray) -> dict[str, float]:
    """Compute paired cosine retrieval metrics within one candidate set."""
    predicted = np.asarray(predicted, dtype=np.float64)
    target = np.asarray(target, dtype=np.float64)
    if predicted.ndim != 2 or predicted.shape != target.shape:
        raise ValueError("predicted and target features must have equal 2D shapes")
    finite = np.isfinite(predicted).all() and np.isfinite(target).all()
    if len(predicted) < 2 or not finite:
        raise ValueError("retrieval inputs must contain at least two finite rows")
    predicted_norm = np.linalg.norm(predicted, axis=1)
    target_norm = np.linalg.norm(target, axis=1)
    if np.any(predicted_norm == 0) or np.any(target_norm == 0):
        raise ValueError("cosine retrieval does not accept zero vectors")
    similarity = (predicted / predicted_norm[:, None]) @ (
        target / target_norm[:, None]
    ).T
    paired = np.diag(similarity)
    # Strictly larger similarities define rank; exact ties receive the most
    # conservative position after all tied candidates.
    ranks = 1 + (similarity >= paired[:, None]).sum(axis=1) - 1
    return {
        "candidates": int(len(target)),
        "top_1_accuracy": float(np.mean(ranks <= 1)),
        "top_10_accuracy": float(np.mean(ranks <= min(10, len(target)))),
        "mean_reciprocal_rank": float(np.mean(1.0 / ranks)),
    }


def evaluate_by_day(
    predicted: np.ndarray,
    target: np.ndarray,
    days: Sequence[str],
) -> dict[str, dict[str, float]]:
    """Evaluate each independent day without mixing candidate sets."""
    days = np.asarray(days, dtype=str)
    if len(days) != len(predicted):
        raise ValueError("day labels must match feature rows")
    output = {}
    for day in sorted(np.unique(days)):
        selected = days == day
        output[day] = retrieval_metrics(predicted[selected], target[selected])
    return output


def macro_average(
    day_metrics: dict[str, dict[str, float]],
) -> dict[str, float]:
    """Equal-weight independent days, excluding the candidate count."""
    if not day_metrics:
        raise ValueError("cannot average an empty day-metric table")
    names = ("top_1_accuracy", "top_10_accuracy", "mean_reciprocal_rank")
    return {
        name: float(np.mean([metrics[name] for metrics in day_metrics.values()]))
        for name in names
    }


def select_ridge_alpha(
    train_x: np.ndarray,
    train_y: np.ndarray,
    validation_x: np.ndarray,
    validation_y: np.ndarray,
    validation_days: Sequence[str],
    alphas: Iterable[float],
) -> tuple[float, list[dict[str, float]]]:
    """Select alpha by validation-day macro MRR with deterministic tie-break."""
    candidates = sorted({float(alpha) for alpha in alphas})
    if not candidates or any(alpha <= 0 for alpha in candidates):
        raise ValueError("ridge alphas must be positive")
    rows = []
    for alpha in candidates:
        model = RidgeRegression(alpha=alpha).fit(train_x, train_y)
        metrics = evaluate_by_day(
            model.predict(validation_x), validation_y, validation_days
        )
        macro = macro_average(metrics)
        rows.append({"alpha": alpha, **macro})
    best = max(rows, key=lambda row: (row["mean_reciprocal_rank"], -row["alpha"]))
    return float(best["alpha"]), rows


def permute_within_groups(
    target: np.ndarray,
    groups: Sequence[str],
    seed: int,
) -> np.ndarray:
    """Break pairing while preserving each training run's target distribution."""
    target = np.asarray(target)
    groups = np.asarray(groups, dtype=str)
    if len(target) != len(groups):
        raise ValueError("permutation groups must match target rows")
    rng = np.random.default_rng(seed)
    indices = np.arange(len(target))
    for group in np.unique(groups):
        selected = np.flatnonzero(groups == group)
        if len(selected) < 2:
            raise ValueError(f"cannot permute singleton group: {group}")
        indices[selected] = rng.permutation(selected)
    return target[indices]


def nested_leave_one_day_out(
    features: np.ndarray,
    targets: np.ndarray,
    days: Sequence[str],
    alphas: Iterable[float],
) -> dict[str, object]:
    """Run nested day-held-out ridge for development-set estimation."""
    features = np.asarray(features, dtype=np.float64)
    targets = np.asarray(targets, dtype=np.float64)
    days = np.asarray(days, dtype=str)
    unique_days = sorted(np.unique(days))
    candidates = sorted({float(alpha) for alpha in alphas})
    if len(unique_days) < 4:
        raise ValueError("nested day resampling requires at least four days")
    if len(features) != len(targets) or len(features) != len(days):
        raise ValueError("features, targets, and days must have aligned rows")
    if not candidates or any(alpha <= 0 for alpha in candidates):
        raise ValueError("ridge alphas must be positive")

    outer_results = {}
    for outer_day in unique_days:
        development = days != outer_day
        inner_scores = {alpha: [] for alpha in candidates}
        for inner_day in unique_days:
            if inner_day == outer_day:
                continue
            inner_test = days == inner_day
            inner_train = development & ~inner_test
            for alpha in candidates:
                model = RidgeRegression(alpha).fit(
                    features[inner_train], targets[inner_train]
                )
                metrics = retrieval_metrics(
                    model.predict(features[inner_test]), targets[inner_test]
                )
                inner_scores[alpha].append(metrics["mean_reciprocal_rank"])
        inner_macro = {
            alpha: float(np.mean(scores)) for alpha, scores in inner_scores.items()
        }
        selected_alpha = max(
            candidates, key=lambda alpha: (inner_macro[alpha], -alpha)
        )
        model = RidgeRegression(selected_alpha).fit(
            features[development], targets[development]
        )
        outer_test = ~development
        outer_results[outer_day] = {
            "selected_alpha": selected_alpha,
            "inner_mrr_by_alpha": inner_macro,
            **retrieval_metrics(
                model.predict(features[outer_test]), targets[outer_test]
            ),
        }
    metric_rows = {
        day: {
            name: result[name]
            for name in (
                "top_1_accuracy",
                "top_10_accuracy",
                "mean_reciprocal_rank",
            )
        }
        for day, result in outer_results.items()
    }
    return {"days": outer_results, "macro": macro_average(metric_rows)}
