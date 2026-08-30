"""Header-level validation for downloaded JapanEEG pilot runs."""

from __future__ import annotations

import json
import wave
from collections import Counter
from pathlib import Path

import mne
import numpy as np
import pandas as pd


def _require_columns(frame: pd.DataFrame, required: set[str], label: str) -> None:
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"{label} missing columns: {', '.join(sorted(missing))}")


def summarize_run(eeg_path: Path, audio_path: Path) -> dict[str, object]:
    """Summarize one EEG/audio pair without preloading the EEG signal matrix."""
    stem = eeg_path.name.removesuffix("_eeg.edf")
    events_path = eeg_path.with_name(f"{stem}_events.tsv")
    channels_path = eeg_path.with_name(f"{stem}_channels.tsv")
    sidecar_path = eeg_path.with_name(f"{stem}_eeg.json")

    for path in (eeg_path, audio_path, events_path, channels_path, sidecar_path):
        if not path.is_file():
            raise FileNotFoundError(path)

    sidecar = json.loads(sidecar_path.read_text())
    channels = pd.read_csv(channels_path, sep="\t")
    events = pd.read_csv(events_path, sep="\t")
    _require_columns(channels, {"name", "type", "units"}, "channels.tsv")
    _require_columns(
        events,
        {"onset", "duration", "trial_type", "wav_onset", "sample", "value"},
        "events.tsv",
    )

    raw = mne.io.read_raw_edf(eeg_path, preload=False, verbose="ERROR")
    with wave.open(str(audio_path), "rb") as wav:
        audio_channels = wav.getnchannels()
        audio_rate = wav.getframerate()
        audio_frames = wav.getnframes()

    eeg_rate = float(raw.info["sfreq"])
    eeg_seconds = raw.n_times / eeg_rate
    audio_seconds = audio_frames / audio_rate
    offsets = events["wav_onset"].to_numpy() - events["onset"].to_numpy()
    sample_errors = (
        events["sample"].to_numpy() / eeg_rate - events["onset"].to_numpy()
    )

    return {
        "run": stem,
        "eeg": {
            "channels_in_edf": int(raw.info["nchan"]),
            "channels_in_sidecar": int(sidecar["TotalChannelCount"]),
            "sampling_hz": eeg_rate,
            "samples": int(raw.n_times),
            "duration_seconds": eeg_seconds,
        },
        "channel_types": dict(sorted(Counter(channels["type"]).items())),
        "audio": {
            "channels": audio_channels,
            "sampling_hz": audio_rate,
            "frames": audio_frames,
            "duration_seconds": audio_seconds,
        },
        "events": {
            "count": int(len(events)),
            "trial_types": dict(sorted(Counter(events["trial_type"]).items())),
            "first_eeg_onset_seconds": float(events["onset"].min()),
            "last_eeg_offset_seconds": float(
                (events["onset"] + events["duration"]).max()
            ),
            "eeg_to_wav_offset_mean_seconds": float(offsets.mean()),
            "eeg_to_wav_offset_sd_seconds": float(offsets.std()),
            "event_sample_error_max_seconds": float(np.abs(sample_errors).max()),
        },
        "checks": {
            "channel_count_matches": int(raw.info["nchan"])
            == int(sidecar["TotalChannelCount"])
            == len(channels),
            "events_within_eeg": bool(
                (events["onset"] >= 0).all()
                and ((events["onset"] + events["duration"]) <= eeg_seconds).all()
            ),
            "events_within_audio_after_offset": bool(
                (events["wav_onset"] >= 0).all()
                and ((events["wav_onset"] + events["duration"]) <= audio_seconds).all()
            ),
            "constant_eeg_audio_offset": bool(offsets.std() < 1e-6),
            "event_samples_match_onsets": bool(np.abs(sample_errors).max() <= 1 / eeg_rate),
        },
    }
