#!/usr/bin/env python3
"""Build the frozen baseline eligibility and sensitivity manifest."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from japaneeg_audit.experiment import build_model_manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("windows", type=Path)
    parser.add_argument("synchronization", type=Path)
    parser.add_argument("qc_flags", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    frame = build_model_manifest(
        pd.read_csv(args.windows, sep="\t"),
        pd.read_csv(args.synchronization, sep="\t"),
        pd.read_csv(args.qc_flags, sep="\t"),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output, sep="\t", index=False)
    summary = frame.groupby(
        ["subset_role", "sync_pass", "artifact_stratum"], dropna=False
    ).size()
    print(summary.to_string())
    print(f"wrote {len(frame)} retained windows to {args.output}")


if __name__ == "__main__":
    main()
