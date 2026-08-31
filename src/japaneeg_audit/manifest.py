"""Provenance-rich records for aligned EEG/audio windows."""

from __future__ import annotations

from collections.abc import Iterable

from japaneeg_audit.windowing import AlignedWindow


def parse_bids_run(stem: str) -> dict[str, str]:
    """Parse key-value entities from a BIDS run stem."""
    entities = {}
    for component in stem.split("_"):
        if "-" in component:
            key, value = component.split("-", 1)
            entities[key] = value
    required = {"sub", "ses", "task", "acq", "run"}
    missing = required.difference(entities)
    if missing:
        raise ValueError(f"BIDS stem missing entities: {', '.join(sorted(missing))}")
    return entities


def manifest_rows(
    run_stem: str,
    windows: Iterable[AlignedWindow],
    dataset_accession: str,
    dataset_snapshot: str,
    dataset_commit: str,
    output_sampling_hz: int = 240,
    expected_eeg_channels: int = 128,
    eog_channels: int = 2,
    emg_channels: int = 4,
    microphone_monitor_channels: int = 2,
) -> list[dict[str, object]]:
    """Build deterministic tabular records without embedding signal arrays."""
    entities = parse_bids_run(run_stem)
    rows = []
    seen = set()
    for window in windows:
        window_id = f"{run_stem}_window-{window.index:05d}"
        if window_id in seen:
            raise ValueError(f"duplicate window ID: {window_id}")
        seen.add(window_id)
        start_sample = round(window.eeg_start * output_sampling_hz)
        stop_sample = round(window.eeg_end * output_sampling_hz)
        rows.append(
            {
                "window_id": window_id,
                "dataset_accession": dataset_accession,
                "dataset_snapshot": dataset_snapshot,
                "dataset_commit": dataset_commit,
                "participant": f"sub-{entities['sub']}",
                "session": f"ses-{entities['ses']}",
                "task": entities["task"],
                "acquisition": entities["acq"],
                "run": entities["run"],
                "source_run": run_stem,
                "window_index": window.index,
                "eeg_start_seconds": window.eeg_start,
                "eeg_end_seconds": window.eeg_end,
                "audio_start_seconds": window.audio_start,
                "audio_end_seconds": window.audio_end,
                "preprocessed_sample_start": start_sample,
                "preprocessed_sample_stop": stop_sample,
                "preprocessed_samples": stop_sample - start_sample,
                "expected_eeg_channels": expected_eeg_channels,
                "eog_channels_available": eog_channels,
                "emg_channels_available": emg_channels,
                "microphone_monitor_channels_available": (
                    microphone_monitor_channels
                ),
                "speech_seconds": window.speech_seconds,
                "speech_fraction": window.speech_fraction,
                "retained": window.retained,
                "rejection_reason": "" if window.retained else "speech_fraction_below_0.20",
            }
        )
    return rows
