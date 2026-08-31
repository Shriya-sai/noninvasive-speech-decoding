#!/usr/bin/env python3
"""Create and validate random, run-held-out, and day-held-out pilot splits."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from japaneeg_audit.splits import (
    assert_group_isolation,
    assert_no_cross_split_overlap,
    assign_chronological_groups,
    assign_random_windows,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    frame = pd.read_csv(args.manifest, sep="\t")
    frame = frame.loc[frame["retained"]].copy()
    ids = frame["window_id"].tolist()
    frame["split_random_window"] = frame["window_id"].map(
        assign_random_windows(ids)
    )

    run_groups = list(zip(ids, frame["source_run"], strict=True))
    run_assignments = assign_chronological_groups(run_groups)
    assert_group_isolation(run_assignments, run_groups)
    frame["split_run_held_out"] = frame["window_id"].map(run_assignments)

    day_groups = list(zip(ids, frame["session"], strict=True))
    day_assignments = assign_chronological_groups(day_groups)
    assert_group_isolation(day_assignments, day_groups)
    frame["split_day_held_out"] = frame["window_id"].map(day_assignments)

    intervals = list(
        zip(
            ids,
            frame["source_run"],
            frame["eeg_start_seconds"],
            frame["eeg_end_seconds"],
            strict=True,
        )
    )
    for column in (
        "split_random_window",
        "split_run_held_out",
        "split_day_held_out",
    ):
        assignments = dict(zip(ids, frame[column], strict=True))
        assert_no_cross_split_overlap(assignments, intervals)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output, sep="\t", index=False)
    for column in (
        "split_random_window",
        "split_run_held_out",
        "split_day_held_out",
    ):
        print(column, frame[column].value_counts().sort_index().to_dict())


if __name__ == "__main__":
    main()
