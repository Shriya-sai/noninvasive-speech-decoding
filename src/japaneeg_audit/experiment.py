"""Validation helpers for frozen experiment specifications and manifests."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import pandas as pd


ALLOWED_ROLES = {"calibration", "validation", "test"}


def build_model_manifest(
    windows: pd.DataFrame,
    synchronization: pd.DataFrame,
    qc_flags: pd.DataFrame,
) -> pd.DataFrame:
    """Join frozen eligibility and sensitivity evidence without dropping days."""
    retained = windows.loc[windows["retained"]].copy()
    sync = synchronization[["source_run", "subset_role", "passes_gate"]].copy()
    if sync["source_run"].duplicated().any():
        raise ValueError("synchronization table must contain one row per run")
    run_flags = qc_flags.groupby("source_run")["run_qc_flagged"].nunique()
    if (run_flags > 1).any():
        raise ValueError("run-level QC labels must be constant within each run")
    qc = (
        qc_flags.groupby("source_run", as_index=False)["run_qc_flagged"]
        .first()
        .rename(columns={"run_qc_flagged": "high_artifact_run"})
    )
    output = retained.merge(
        sync,
        on=["source_run", "subset_role"],
        how="left",
        validate="many_to_one",
    ).merge(qc, on="source_run", how="left", validate="many_to_one")
    if output[["passes_gate", "high_artifact_run"]].isna().any().any():
        raise ValueError("every retained window requires sync and QC evidence")
    output["sync_pass"] = output.pop("passes_gate").astype(bool)
    output["artifact_stratum"] = output.pop("high_artifact_run").map(
        {False: "clean_run", True: "high_artifact_run"}
    )
    output["model_eligible"] = output["sync_pass"]
    return output


def validate_baseline_specification(specification: Mapping[str, object]) -> None:
    """Reject specifications that weaken independence or held-out boundaries."""
    experiment = specification["experiment"]
    eligibility = specification["eligibility"]
    split = specification["split"]
    uncertainty = specification["uncertainty"]

    if experiment["status"] != "frozen_before_feature_extraction":
        raise ValueError("baseline specification must be frozen before extraction")
    if split["unit"] != "recording_day":
        raise ValueError("primary baseline split unit must be recording_day")
    if split["allow_window_random_primary"]:
        raise ValueError("window-random splitting cannot be the primary baseline")
    if split["allow_role_reassignment"]:
        raise ValueError("frozen subset roles cannot be reassigned")
    if set(split["fit_on_roles"]) != {"calibration"}:
        raise ValueError("fitting must use calibration days only")
    role_sets = [
        set(split["train_roles"]),
        set(split["validation_roles"]),
        set(split["test_roles"]),
    ]
    if set.union(*role_sets) != ALLOWED_ROLES:
        raise ValueError("train, validation, and test must cover the frozen roles")
    overlaps = (
        left & right
        for index, left in enumerate(role_sets)
        for right in role_sets[index + 1 :]
    )
    if any(overlaps):
        raise ValueError("split roles must be disjoint")
    if not eligibility["require_sync_gate"]:
        raise ValueError("paired decoding requires the frozen synchronization gate")
    if eligibility["hard_artifact_exclusion"]:
        raise ValueError("baseline must retain artifact strata, not hard-exclude them")
    if uncertainty["unit"] != "recording_day":
        raise ValueError("uncertainty unit must be recording_day")


def validate_model_manifest(
    frame: pd.DataFrame,
    expected_runs: Mapping[str, Sequence[str]],
) -> None:
    """Validate role isolation, sync eligibility, and artifact-stratum retention."""
    required = {
        "window_id",
        "source_run",
        "subset_role",
        "sync_pass",
        "artifact_stratum",
        "model_eligible",
    }
    missing = required.difference(frame.columns)
    if missing:
        names = ", ".join(sorted(missing))
        raise ValueError(f"model manifest missing columns: {names}")
    if frame["window_id"].duplicated().any():
        raise ValueError("model manifest window IDs must be unique")
    if not set(frame["subset_role"]).issubset(ALLOWED_ROLES):
        raise ValueError("model manifest contains an unknown subset role")
    if not set(frame["artifact_stratum"]).issubset({"clean_run", "high_artifact_run"}):
        raise ValueError("artifact strata must be explicit and predeclared")
    if (frame["model_eligible"] & ~frame["sync_pass"]).any():
        raise ValueError("sync-failing windows cannot be model eligible")

    observed_role_by_run = frame.groupby("source_run")["subset_role"].nunique()
    if (observed_role_by_run > 1).any():
        raise ValueError("a recording run occurs in multiple subset roles")
    for role, runs in expected_runs.items():
        observed = set(frame.loc[frame["subset_role"] == role, "source_run"])
        unexpected = observed.difference(runs)
        if unexpected:
            raise ValueError(f"unexpected {role} runs: {', '.join(sorted(unexpected))}")

    eligible = frame[frame["model_eligible"]]
    if eligible.empty:
        raise ValueError("model manifest has no eligible windows")
    if set(eligible["subset_role"]) != ALLOWED_ROLES:
        raise ValueError(
            "eligible manifest must retain train, validation, and test roles"
        )


def day_macro_average(day_values: Mapping[str, float]) -> float:
    """Average independent day estimates with equal weight."""
    if not day_values:
        raise ValueError("cannot average an empty set of days")
    values = [float(value) for value in day_values.values()]
    if any(not pd.notna(value) for value in values):
        raise ValueError("day estimates must be finite")
    return sum(values) / len(values)
