"""Fold-local PCA and nested temporal ridge development evaluation."""

from __future__ import annotations

from itertools import combinations
from collections.abc import Iterable, Sequence

import numpy as np
from scipy.sparse.linalg import svds

from japaneeg_audit.retrieval import RidgeRegression, macro_average, retrieval_metrics


class FoldPCA:
    """Training-fold standardization and deterministic truncated PCA."""

    def __init__(self, components: int = 128):
        if components <= 0:
            raise ValueError("PCA components must be positive")
        self.components = int(components)

    def fit(self, features: np.ndarray) -> FoldPCA:
        features = np.asarray(features, dtype=np.float64)
        if features.ndim != 2 or len(features) < 2:
            raise ValueError("PCA features must be a two-dimensional table")
        if not np.isfinite(features).all():
            raise ValueError("PCA features must be finite")
        if self.components >= min(features.shape):
            raise ValueError("PCA components must be smaller than both dimensions")
        self.mean_ = features.mean(axis=0)
        self.scale_ = features.std(axis=0)
        if np.any(self.scale_ == 0) or not np.isfinite(self.scale_).all():
            raise ValueError("PCA training features contain an invalid scale")
        standardized = (features - self.mean_) / self.scale_
        _, singular, right = svds(
            standardized,
            k=self.components,
            which="LM",
            solver="propack",
            rng=np.random.default_rng(0),
        )
        order = np.argsort(singular)[::-1]
        self.singular_values_ = singular[order]
        self.components_ = right[order]
        anchors = np.argmax(np.abs(self.components_), axis=1)
        signs = np.sign(self.components_[np.arange(self.components), anchors])
        signs[signs == 0] = 1
        self.components_ *= signs[:, None]
        return self

    def transform(self, features: np.ndarray) -> np.ndarray:
        if not hasattr(self, "components_"):
            raise ValueError("PCA must be fitted before transformation")
        features = np.asarray(features, dtype=np.float64)
        if features.ndim != 2 or features.shape[1] != len(self.mean_):
            raise ValueError("PCA transform features have the wrong shape")
        return ((features - self.mean_) / self.scale_) @ self.components_.T


def _flatten(tensor: np.ndarray) -> np.ndarray:
    tensor = np.asarray(tensor, dtype=np.float64)
    if tensor.ndim != 3 or not np.isfinite(tensor).all():
        raise ValueError("temporal features must be a finite three-dimensional tensor")
    return tensor.reshape(len(tensor), -1)


def _scale_targets(
    training: np.ndarray, held_out: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    mean = training.mean(axis=0)
    scale = training.std(axis=0)
    if np.any(scale == 0) or not np.isfinite(scale).all():
        raise ValueError("target training features contain an invalid scale")
    return (training - mean) / scale, (held_out - mean) / scale


def _evaluate_model(
    model: RidgeRegression,
    pca: FoldPCA,
    held_eeg: np.ndarray,
    held_target: np.ndarray,
) -> dict[str, float]:
    predicted = model.predict(pca.transform(_flatten(held_eeg)))
    return retrieval_metrics(predicted, held_target)


def select_temporal_alpha_leave_one_day_out(
    eeg: np.ndarray,
    targets: np.ndarray,
    days: Sequence[str],
    alphas: Iterable[float],
    components: int = 128,
) -> dict[str, object]:
    """Select one alpha by calibration-only leave-one-day-out macro MRR."""
    flat_eeg = _flatten(eeg)
    flat_targets = _flatten(targets)
    days = np.asarray(days, dtype=str)
    candidates = sorted({float(alpha) for alpha in alphas})
    unique_days = sorted(np.unique(days))
    if len(unique_days) < 3:
        raise ValueError("alpha selection requires at least three calibration days")
    if len(flat_eeg) != len(flat_targets) or len(flat_eeg) != len(days):
        raise ValueError("temporal EEG, targets, and days must align")
    if not candidates or any(alpha <= 0 for alpha in candidates):
        raise ValueError("ridge alphas must be positive")
    day_rows = {alpha: {} for alpha in candidates}
    for day in unique_days:
        held = days == day
        training = ~held
        pca = FoldPCA(components).fit(flat_eeg[training])
        train_x = pca.transform(flat_eeg[training])
        train_y, held_y = _scale_targets(
            flat_targets[training], flat_targets[held]
        )
        held_x = pca.transform(flat_eeg[held])
        for alpha in candidates:
            model = RidgeRegression(alpha).fit(train_x, train_y)
            day_rows[alpha][day] = retrieval_metrics(
                model.predict(held_x), held_y
            )
    rows = []
    for alpha in candidates:
        rows.append({"alpha": alpha, **macro_average(day_rows[alpha])})
    best = max(rows, key=lambda row: (row["mean_reciprocal_rank"], -row["alpha"]))
    return {"selected_alpha": float(best["alpha"]), "rows": rows, "days": day_rows}


def fit_temporal_ridge(
    eeg: np.ndarray,
    targets: np.ndarray,
    alpha: float,
    components: int = 128,
) -> tuple[FoldPCA, RidgeRegression, np.ndarray, np.ndarray]:
    """Fit all frozen temporal transforms and ridge on the supplied rows."""
    flat_eeg = _flatten(eeg)
    flat_targets = _flatten(targets)
    if len(flat_eeg) != len(flat_targets):
        raise ValueError("temporal EEG and targets must align")
    pca = FoldPCA(components).fit(flat_eeg)
    target_mean = flat_targets.mean(axis=0)
    target_scale = flat_targets.std(axis=0)
    if np.any(target_scale == 0) or not np.isfinite(target_scale).all():
        raise ValueError("target training features contain an invalid scale")
    scaled_target = (flat_targets - target_mean) / target_scale
    model = RidgeRegression(alpha).fit(pca.transform(flat_eeg), scaled_target)
    return pca, model, target_mean, target_scale


def evaluate_frozen_temporal_model(
    pca: FoldPCA,
    model: RidgeRegression,
    target_mean: np.ndarray,
    target_scale: np.ndarray,
    eeg: np.ndarray,
    targets: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, dict[str, float]]:
    """Apply one fitted model to held-out temporal rows without refitting."""
    held_target = (_flatten(targets) - target_mean) / target_scale
    prediction = model.predict(pca.transform(_flatten(eeg)))
    return prediction, held_target, retrieval_metrics(prediction, held_target)


def nested_temporal_leave_one_day_out(
    eeg: np.ndarray,
    targets: np.ndarray,
    days: Sequence[str],
    alphas: Iterable[float],
    components: int = 128,
    lag_bins: Sequence[int] = (-4, -2, 2, 4),
    permutations: int = 0,
    permutation_seed: int = 20260904,
) -> dict[str, object]:
    """Nested day-held-out temporal ridge with evaluation-only timing controls."""
    eeg = np.asarray(eeg, dtype=np.float64)
    targets = np.asarray(targets, dtype=np.float64)
    days = np.asarray(days, dtype=str)
    unique_days = sorted(np.unique(days))
    candidates = sorted({float(alpha) for alpha in alphas})
    if len(unique_days) < 4:
        raise ValueError("nested temporal evaluation requires at least four days")
    if len(eeg) != len(targets) or len(eeg) != len(days):
        raise ValueError("temporal EEG, targets, and days must align")
    if eeg.ndim != 3 or targets.ndim != 3:
        raise ValueError("temporal EEG and targets must be three-dimensional")
    if not candidates or any(alpha <= 0 for alpha in candidates):
        raise ValueError("ridge alphas must be positive")
    if permutations < 0:
        raise ValueError("permutation count must be non-negative")

    flat_eeg = _flatten(eeg)
    flat_targets = _flatten(targets)
    inner_scores = {
        outer: {alpha: [] for alpha in candidates} for outer in unique_days
    }
    for first, second in combinations(unique_days, 2):
        training = (days != first) & (days != second)
        pca = FoldPCA(components).fit(flat_eeg[training])
        train_x = pca.transform(flat_eeg[training])
        train_y_raw = flat_targets[training]
        for outer, inner in ((first, second), (second, first)):
            held = days == inner
            train_y, held_y = _scale_targets(train_y_raw, flat_targets[held])
            for alpha in candidates:
                model = RidgeRegression(alpha).fit(train_x, train_y)
                metrics = retrieval_metrics(
                    model.predict(pca.transform(flat_eeg[held])), held_y
                )
                inner_scores[outer][alpha].append(
                    metrics["mean_reciprocal_rank"]
                )

    primary_days = {}
    control_days: dict[str, dict[str, dict[str, float]]] = {
        f"lag_{lag:+d}_bins": {} for lag in lag_bins
    }
    control_days["time_reversed"] = {}
    permutation_rng = np.random.default_rng(permutation_seed)
    permutation_seeds = permutation_rng.integers(
        0, np.iinfo(np.uint32).max, size=permutations, dtype=np.uint32
    )
    permutation_days = {int(seed): {} for seed in permutation_seeds}
    for outer in unique_days:
        inner_macro = {
            alpha: float(np.mean(scores))
            for alpha, scores in inner_scores[outer].items()
        }
        selected = max(candidates, key=lambda alpha: (inner_macro[alpha], -alpha))
        training = days != outer
        held = ~training
        pca = FoldPCA(components).fit(flat_eeg[training])
        train_x = pca.transform(flat_eeg[training])
        train_y, held_y = _scale_targets(
            flat_targets[training], flat_targets[held]
        )
        model = RidgeRegression(selected).fit(train_x, train_y)
        held_prediction = model.predict(pca.transform(flat_eeg[held]))
        primary_days[outer] = {
            "selected_alpha": selected,
            "inner_mrr_by_alpha": inner_macro,
            **retrieval_metrics(held_prediction, held_y),
        }
        for seed in permutation_seeds:
            order = np.random.default_rng(int(seed)).permutation(held.sum())
            permutation_days[int(seed)][outer] = retrieval_metrics(
                held_prediction, held_y[order]
            )
        for lag in lag_bins:
            shifted = np.roll(eeg[held], shift=lag, axis=1)
            control_days[f"lag_{lag:+d}_bins"][outer] = _evaluate_model(
                model, pca, shifted, held_y
            )
        control_days["time_reversed"][outer] = _evaluate_model(
            model, pca, eeg[held, ::-1, :], held_y
        )

    metric_names = ("top_1_accuracy", "top_10_accuracy", "mean_reciprocal_rank")
    primary_metric_rows = {
        day: {name: values[name] for name in metric_names}
        for day, values in primary_days.items()
    }
    result = {
        "primary": {
            "days": primary_days,
            "macro": macro_average(primary_metric_rows),
        },
        "temporal_controls": {
            name: {"days": values, "macro": macro_average(values)}
            for name, values in control_days.items()
        },
    }
    if permutations:
        null_rows = []
        for seed, values in permutation_days.items():
            null_rows.append({"seed": seed, **macro_average(values)})
        observed = result["primary"]["macro"]["mean_reciprocal_rank"]
        null_mrr = np.asarray(
            [row["mean_reciprocal_rank"] for row in null_rows]
        )
        result["pairing_null"] = {
            "permutations": permutations,
            "rows": null_rows,
            "mrr_95th_percentile": float(np.quantile(null_mrr, 0.95)),
            "mrr_empirical_p_plus_one": float(
                (1 + np.sum(null_mrr >= observed)) / (permutations + 1)
            ),
        }
    return result
