# Signal synchronization and windowing gate

Status: passed on two checksum-pinned pilot runs

Profile: `audit_v1`

Date: 2026-08-31

## Question

Do the EDF speaking-microphone monitor channels support the event-table mapping
between EEG time and the vocal WAV, and can that mapping support deterministic
five-second windows with a fully specified speech-occupancy rule?

## Waveform method

For each annotated utterance, the analysis maps its EEG onset to its
`wav_onset`, adds one second of context on both sides, computes 8 Hz low-pass
amplitude envelopes, and searches only ±0.5 seconds for residual lag. It tests
the two BIDS speaking-microphone monitor channels (`EEG131`, `EEG132`) against
both WAV channels.

The gate requires the best channel pair in each run to have:

- median event-local envelope correlation at least 0.10;
- absolute median residual lag no greater than 0.25 seconds.

These thresholds test coarse speech-envelope agreement. They do not establish
sample-exact identity or justify interpreting an EDF monitor as the digital WAV.

## Results

| Run | Events | Best pair | Median correlation | Median residual | Gate |
| --- | ---: | --- | ---: | ---: | --- |
| 2023-08-31 run 06 | 44 | EEG132 / WAV 0 | 0.199 | -222 ms | pass |
| 2023-09-05 run 02 | 29 | EEG131 / WAV 1 | 0.162 | +103 ms | pass |

The best pair changes by run, and correlations are modest. Therefore the BIDS
event mapping is accepted for window alignment, while channel identity and
residual delay remain recorded quality-control variables. No global waveform
lag correction is applied from these two pilots.

## Frozen window profile

`audit_v1` uses:

1. run-specific `wav_onset - onset`, verified constant within each run;
2. complete, non-overlapping 5.0-second windows anchored at EEG run time zero;
3. WAV bounds `audio_start = eeg_start + run_offset`;
4. only windows fully contained in both EEG and vocal WAV;
5. incomplete final windows dropped;
6. Silero VAD 6.2.1 with its ONNX backend on zero-based WAV channel 0;
7. 16 kHz audio, threshold 0.5, minimum speech 250 ms, minimum silence 100 ms,
   and 30 ms speech padding;
8. retention when the union of detected speech covers at least 20% of a window.

Silero's maintained implementation documents these VAD defaults. The anchor
paper reports Silero and the 20% rule but not its model version or inference
parameters, so `audit_v1` is a frozen conceptual-replication profile rather
than a claim of paper-exact reconstruction.

## Pilot retention

| Run | Complete windows | Retained | Retained duration | VAD speech |
| --- | ---: | ---: | ---: | ---: |
| 2023-08-31 run 06 | 161 | 90 (55.9%) | 450 s | 291.0 s |
| 2023-09-05 run 02 | 81 | 38 (46.9%) | 190 s | 106.0 s |

VAD speech duration and retained-window duration are intentionally different:
a retained five-second window may contain as little as one second of speech.

## Reproduction

```bash
python scripts/validate_waveform_sync.py <run_eeg.edf> <run_vocal.wav>
python scripts/build_pilot_windows.py <run_eeg.edf> <run_vocal.wav>
```

The authoritative parameters are in `configs/signal_gate.toml`. Raw signals
and generated per-window manifests remain local and excluded from Git.

## Remaining boundary

This gate supports preprocessing development on the two runs. It does not show
that every dataset session has the same signal quality. Full ingestion must
emit these synchronization metrics per run, fail closed when the thresholds
are missed, and preserve rejected runs for sensitivity analysis.
