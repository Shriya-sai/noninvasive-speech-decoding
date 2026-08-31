#!/usr/bin/env python3
"""Emit a JSON waveform-synchronization audit for one pilot run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from japaneeg_audit.synchronization import validate_waveform_sync


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("eeg", type=Path)
    parser.add_argument("audio", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate_waveform_sync(args.eeg, args.audio), indent=2))


if __name__ == "__main__":
    main()
