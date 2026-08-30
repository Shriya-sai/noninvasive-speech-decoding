# Two-run signal pilot audit

## Scope

This pilot asks whether raw JapanEEG files can be retrieved reproducibly and
whether the BIDS metadata are sufficient to align EEG, vocal audio, channels,
and events before any preprocessing or model training. It deliberately uses
two overt-speech runs from different recording days for `sub-01`.

The dataset was checked out at tag `1.0.0`, git commit
`dc37d8078c575eb067c26acc7f2d656f86af6bca`. Large files were downloaded from
OpenNeuro's object store and accepted only after SHA-256 verification against
their git-annex keys. Raw files remain ignored by Git.

## Runs and observations

| Session/run | EEG | Audio | Events | Constant EEG-to-WAV offset |
| --- | ---: | ---: | ---: | ---: |
| 2023-08-31 run 06 | 872.000 s | 837.717 s | 44 | 28.0500 s |
| 2023-09-05 run 02 | 472.000 s | 434.496 s | 29 | 28.5092 s |

Both EDFs contain 139 channels sampled at 1200 Hz. Their BIDS channel tables
resolve those channels as 128 EEG, 2 EOG, 4 EMG, 4 MISC, and 1 trigger channel.
Both WAV files are stereo at 48 kHz. All events are overt-speech events, lie
within both recordings after alignment, and agree with their recorded EEG
sample indices to within one EEG sample.

## Decisions

1. The timing offset is constant *within* each tested run but differs between
   runs by 0.4592 s. Therefore alignment must use each row's `wav_onset` (or a
   run-specific validated offset), never a dataset-wide hard-coded offset.
2. MNE's generic EDF import initially assigns all 139 signals the EEG type.
   Every loader must restore channel roles from `channels.tsv` before channel
   selection, preprocessing, or controls.
3. EEG and audio durations are not expected to match. Event-bound checks must
   be performed separately in EEG time and WAV time.
4. Header-level validation is sufficient to proceed to a small windowing and
   synchronization pilot; it is not evidence that waveform-level alignment or
   speech-decoding performance is correct.

## Reproduction

After placing the pinned dataset under `data/raw/ds007808`, run:

```bash
python scripts/inspect_pilot_run.py \
  data/raw/ds007808/<participant>/<session>/eeg/<run>_eeg.edf \
  data/raw/ds007808/<participant>/<session>/beh/<run>_recording-vocal_beh.wav
```

The command emits a JSON record containing header values, timing statistics,
and explicit pass/fail checks. The two local pilot files are not committed.

## Next gate

Before reproduction training, load short signal segments and test that event
audio, EDF audio-monitor channels, and vocal WAV waveforms agree at the
run-specific alignment. Then freeze the 5-second window construction and VAD
retention rules with leakage tests.
