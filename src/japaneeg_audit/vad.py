"""Pinned Silero VAD inference for JapanEEG vocal WAV files."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from scipy.io import wavfile
from scipy.signal import resample_poly
from silero_vad import get_speech_timestamps, load_silero_vad


def silero_intervals(
    audio_path: Path,
    channel: int = 0,
    sampling_hz: int = 16_000,
    threshold: float = 0.5,
    minimum_speech_ms: int = 250,
    minimum_silence_ms: int = 100,
    speech_padding_ms: int = 30,
) -> tuple[list[tuple[float, float]], float]:
    """Return speech intervals and resampled audio duration in WAV time."""
    source_rate, audio = wavfile.read(audio_path)
    if audio.ndim == 1:
        audio = audio[:, None]
    if not 0 <= channel < audio.shape[1]:
        raise ValueError(f"audio channel {channel} is unavailable")
    mono = audio[:, channel].astype(np.float32)
    peak = float(np.max(np.abs(mono)))
    if peak:
        mono /= peak
    mono = resample_poly(mono, sampling_hz, source_rate).astype(np.float32)

    model = load_silero_vad(onnx=True)
    timestamps = get_speech_timestamps(
        torch.from_numpy(mono),
        model,
        sampling_rate=sampling_hz,
        threshold=threshold,
        min_speech_duration_ms=minimum_speech_ms,
        min_silence_duration_ms=minimum_silence_ms,
        speech_pad_ms=speech_padding_ms,
        return_seconds=False,
    )
    intervals = [
        (item["start"] / sampling_hz, item["end"] / sampling_hz)
        for item in timestamps
    ]
    return intervals, len(mono) / sampling_hz
