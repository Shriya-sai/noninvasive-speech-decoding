#!/usr/bin/env python3
"""Apply an existing calibration-fitted hierarchical QC specification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from japaneeg_audit.hierarchical_qc import apply_hierarchical_qc


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("metrics", type=Path)
    parser.add_argument("specification", type=Path)
    parser.add_argument("flags", type=Path)
    args = parser.parse_args()
    frame = pd.read_csv(args.metrics, sep="\t")
    specification = json.loads(args.specification.read_text())
    flags = apply_hierarchical_qc(frame, specification)
    identity = frame[["window_id", "source_run", "subset_role"]]
    output = pd.concat([identity, flags], axis=1)
    args.flags.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.flags, sep="\t", index=False)
    print(output.groupby("source_run")[["run_qc_flagged", "window_qc_flagged", "qc_flagged"]].agg(["sum", "count"]).to_string())


if __name__ == "__main__":
    main()
