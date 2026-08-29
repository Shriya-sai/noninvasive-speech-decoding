#!/usr/bin/env python3
"""Verify that a local JapanEEG checkout has required top-level metadata."""

import argparse
from pathlib import Path

from japaneeg_audit.inventory import require_bids_metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_root", type=Path)
    args = parser.parse_args()
    description, participants = require_bids_metadata(args.dataset_root)
    print(f"dataset_description={description}")
    print(f"participants={participants}")


if __name__ == "__main__":
    main()
