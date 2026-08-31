#!/usr/bin/env python3
"""Run pinned VAD and emit a JSON summary of retained five-second windows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import mne
import pandas as pd

from japaneeg_audit.vad import silero_intervals
from japaneeg_audit.windowing import annotate_speech, construct_windows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("eeg", type=Path)
    parser.add_argument("audio", type=Path)
    args = parser.parse_args()

    stem = args.eeg.name.removesuffix("_eeg.edf")
    events = pd.read_csv(args.eeg.with_name(f"{stem}_events.tsv"), sep="\t")
    offsets = events["wav_onset"] - events["onset"]
    if offsets.std() >= 1e-6:
        raise ValueError("run does not have a constant EEG-to-WAV offset")
    offset = float(offsets.mean())

    raw = mne.io.read_raw_edf(args.eeg, preload=False, verbose="ERROR")
    intervals, audio_duration = silero_intervals(args.audio)
    windows = construct_windows(raw.n_times / raw.info["sfreq"], audio_duration, offset)
    windows = annotate_speech(windows, intervals)
    retained = [window for window in windows if window.retained]
    print(
        json.dumps(
            {
                "run": stem,
                "eeg_to_wav_offset_seconds": offset,
                "complete_windows": len(windows),
                "retained_windows": len(retained),
                "retained_seconds": len(retained) * 5.0,
                "retained_fraction": len(retained) / len(windows),
                "vad_speech_intervals": len(intervals),
                "vad_speech_seconds": sum(end - start for start, end in intervals),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
