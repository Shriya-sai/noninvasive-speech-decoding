#!/usr/bin/env python3
"""Print a JSON header/synchronization audit for one JapanEEG run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from japaneeg_audit.pilot import summarize_run


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("eeg", type=Path)
    parser.add_argument("audio", type=Path)
    args = parser.parse_args()
    print(json.dumps(summarize_run(args.eeg, args.audio), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
