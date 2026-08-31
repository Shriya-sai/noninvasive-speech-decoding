"""Deterministic window construction and speech-occupancy filtering."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import floor
from typing import Iterable


@dataclass(frozen=True)
class AlignedWindow:
    index: int
    eeg_start: float
    eeg_end: float
    audio_start: float
    audio_end: float
    speech_seconds: float = 0.0
    speech_fraction: float = 0.0
    retained: bool = False

    def to_dict(self) -> dict[str, float | int | bool]:
        return asdict(self)


def construct_windows(
    eeg_duration: float,
    audio_duration: float,
    eeg_to_audio_offset: float,
    window_seconds: float = 5.0,
) -> list[AlignedWindow]:
    """Create complete, non-overlapping windows anchored at EEG time zero."""
    if min(eeg_duration, audio_duration, window_seconds) <= 0:
        raise ValueError("durations and window_seconds must be positive")
    if eeg_to_audio_offset < 0:
        raise ValueError("negative EEG-to-audio offsets are not supported")

    common_eeg_duration = min(eeg_duration, audio_duration - eeg_to_audio_offset)
    count = max(0, floor(common_eeg_duration / window_seconds))
    return [
        AlignedWindow(
            index=index,
            eeg_start=index * window_seconds,
            eeg_end=(index + 1) * window_seconds,
            audio_start=eeg_to_audio_offset + index * window_seconds,
            audio_end=eeg_to_audio_offset + (index + 1) * window_seconds,
        )
        for index in range(count)
    ]


def _merged_intervals(
    intervals: Iterable[tuple[float, float]],
) -> list[tuple[float, float]]:
    ordered = sorted((float(start), float(end)) for start, end in intervals)
    if any(end < start for start, end in ordered):
        raise ValueError("speech interval ends before it starts")
    merged: list[list[float]] = []
    for start, end in ordered:
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return [(start, end) for start, end in merged]


def annotate_speech(
    windows: Iterable[AlignedWindow],
    speech_intervals: Iterable[tuple[float, float]],
    minimum_speech_fraction: float = 0.2,
) -> list[AlignedWindow]:
    """Annotate windows using the union of VAD intervals in audio time."""
    if not 0 <= minimum_speech_fraction <= 1:
        raise ValueError("minimum_speech_fraction must lie in [0, 1]")
    intervals = _merged_intervals(speech_intervals)
    annotated = []
    for window in windows:
        speech_seconds = sum(
            max(0.0, min(window.audio_end, end) - max(window.audio_start, start))
            for start, end in intervals
        )
        duration = window.audio_end - window.audio_start
        fraction = min(1.0, speech_seconds / duration)
        annotated.append(
            AlignedWindow(
                **{
                    **window.to_dict(),
                    "speech_seconds": speech_seconds,
                    "speech_fraction": fraction,
                    "retained": fraction >= minimum_speech_fraction,
                }
            )
        )
    return annotated
