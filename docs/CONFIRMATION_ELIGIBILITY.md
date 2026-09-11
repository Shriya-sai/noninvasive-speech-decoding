# Replacement Confirmation Eligibility

Status: three reserved runs materialized; eligibility frozen before model evaluation

## Protected-boundary audit

Immediately before download, all six reserved git-annex objects were absent and
the immutable confirmation-model SHA-256 matched the validation report:
`3aead58167b042c98a2b2fd3228b0ce4a4c2358f9ff3f1ed72ca88cddb56906c`.
Only the three runs in `replacement_confirmation_v1.toml` were downloaded. All
six EDF/WAV byte sizes and SHA-256 values matched the metadata-frozen values.

## Mechanical gates

| Reserved run | Sync | VAD-retained windows | Artifact stratum | Eligible |
|---|---:|---:|---|---:|
| 2025-01-29 run 05 | fail | 114 | high-artifact run | 0 |
| 2025-02-06 run 05 | pass | 88 | clean run | 88 |
| 2025-02-10 run 02 | pass | 99 | clean run | 99 |

The failed run is neither replaced nor repaired. Its best frozen sync audit used
monitor channel EEG131 and WAV channel 0, with 86 events, median envelope
correlation 0.8958, and median residual -0.2817 seconds. The passing runs had
median correlations 0.9286 and 0.9514 and residuals -0.2408 and -0.1475 seconds.

Frozen five-second windowing produced 427 candidate windows: 301 passed the
20% speech-fraction rule and 126 failed. Synchronization then leaves exactly
187 model-eligible windows across two independent confirmation days.

The calibration-fitted hierarchical QC specification was applied unchanged.
The failed-sync run was high-artifact at run level. Both eligible runs were
clean at run level; one of 88 windows on 2025-02-06 had a window-level flag.
Artifact flags remain sensitivity strata and do not exclude synchronized rows.

## Local provenance

- synchronization TSV SHA-256: `e06cefd02f5e09f7d51ea1836a0e985db3a247711fd714487456a875a48a22e4`
- window TSV SHA-256: `9b976f2cd1608ec50c82e3a151bd5f431873147832e989117590db8f3c751630`
- QC metrics TSV SHA-256: `751960682eca8882ca121f247c80b97aa7f663f100ed3cd0bac45f12cf32ee60`
- QC flags TSV SHA-256: `76d353be12ffc7816562e026b718e46c9bd0102eb41826b7a81a1d7b00970135`
- model manifest TSV SHA-256: `86dad816bf6c7a06599759a390159d14a6aa2341ff3e9dc9c974be3fd9ef273c`

Participant-level tables and signals remain local and ignored.

## Next boundary

Extract the already-frozen temporal tensors for the 187 eligible rows. Then
apply the serialized confirmation model once, without refitting, tuning, run
replacement, or eligibility changes. Report daywise results and their equal-day
macro average regardless of outcome.
