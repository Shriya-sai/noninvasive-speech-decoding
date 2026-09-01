#!/usr/bin/env python3
"""Build a local TSV manifest for one or more configured pilot runs."""

from __future__ import annotations

import argparse
import tomllib
from pathlib import Path

import mne
import pandas as pd

from japaneeg_audit.manifest import manifest_rows
from japaneeg_audit.vad import silero_intervals
from japaneeg_audit.windowing import annotate_speech, construct_windows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--config", type=Path, default=Path("configs/pilot_runs.toml"))
    args = parser.parse_args()

    config = tomllib.loads(args.config.read_text())
    if "dataset" in config:
        dataset_accession = config["dataset"]["accession"]
        dataset_snapshot = config["dataset"]["snapshot"]
        dataset_commit = config["dataset"]["git_commit"]
    else:
        selection = config["selection"]
        dataset_accession = selection["dataset_accession"]
        dataset_snapshot = selection["dataset_snapshot"]
        dataset_commit = selection["dataset_commit"]
    all_rows = []
    for run in config["runs"]:
        eeg_path = args.dataset_root / run["eeg"]
        audio_path = args.dataset_root / run["audio"]
        stem = eeg_path.name.removesuffix("_eeg.edf")
        events = pd.read_csv(eeg_path.with_name(f"{stem}_events.tsv"), sep="\t")
        offsets = events["wav_onset"] - events["onset"]
        if offsets.std() >= 1e-6:
            raise ValueError(f"nonconstant EEG-to-WAV offset in {stem}")
        raw = mne.io.read_raw_edf(eeg_path, preload=False, verbose="ERROR")
        speech, audio_duration = silero_intervals(audio_path)
        windows = construct_windows(
            raw.n_times / raw.info["sfreq"],
            audio_duration,
            float(offsets.mean()),
        )
        windows = annotate_speech(windows, speech)
        rows = manifest_rows(
            stem,
            windows,
            dataset_accession,
            dataset_snapshot,
            dataset_commit,
        )
        for row in rows:
            row["subset_role"] = run.get("role", "pilot")
            row["timeline_stratum"] = run.get("stratum")
            row["calibration_wave"] = run.get(
                "calibration_wave",
                1 if run.get("role") == "calibration" else None,
            )
        all_rows.extend(rows)

    frame = pd.DataFrame(all_rows)
    if not frame["window_id"].is_unique:
        raise ValueError("manifest contains duplicate window IDs")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output, sep="\t", index=False)
    retained = int(frame["retained"].sum())
    print(
        f"wrote {len(frame)} windows ({retained} retained, "
        f"{len(frame) - retained} rejected) to {args.output}"
    )


if __name__ == "__main__":
    main()
