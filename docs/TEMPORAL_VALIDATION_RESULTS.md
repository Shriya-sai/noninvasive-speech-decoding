# Temporal Ridge Validation Results

## Decision

The one-time synchronized-validation gate **passed all three frozen criteria**.
This permits mechanical confirmation-data eligibility checks. It does not by
itself support a cortical speech-decoding claim.

The validation evaluation used 132 windows from one held-out recording day.
Ridge alpha 10.0 was selected exclusively by leave-one-calibration-day-out
macro-MRR, then the feature transform, PCA, target scaling, and ridge were fit
on the 2,181 calibration windows and applied unchanged to validation.

| Evaluation | Top-1 | Top-10 | MRR |
|---|---:|---:|---:|
| Contemporaneous EEG | 0.0152 | 0.1515 | 0.06124 |
| Exact 132-candidate reference | 0.0076 | 0.0758 | 0.04139 |
| Time-reversed EEG | 0.0076 | 0.0985 | 0.04432 |
| Audio-envelope control | 0.7803 | 0.9848 | 0.86936 |

The 99 held-out target-row permutations had a 95th-percentile MRR of 0.05617.
The observed EEG MRR exceeded it, with plus-one empirical `p = 0.02`.

## Frozen gate checks

- EEG MRR exceeded the exact candidate-set reference: **pass**.
- EEG MRR exceeded the pairing-null 95th percentile: **pass**.
- EEG MRR exceeded time reversal: **pass**.

## Timing diagnostics

The report-only lag MRRs were 0.04616 at -1000 ms, 0.04841 at -500 ms,
0.06377 at +500 ms, and 0.05737 at +1000 ms. The +500 ms score slightly
exceeded the contemporaneous score. This does not alter the preregistered gate,
but it weakens a simple aligned cortical interpretation and must remain visible
in all downstream claims.

The audio-envelope control was selected on calibration only (alpha 0.01) and
was vastly stronger than EEG on validation. The result therefore remains
compatible with acoustic, articulation, peripheral, or timing-related signal
pathways. Confirmation can test reproducibility, not settle signal origin.

## Locked confirmation model

Because validation passed, alpha 10.0 was held fixed and all transforms plus
ridge were fit once on the 2,313 calibration and synchronized-validation rows.
The model was serialized before any replacement-confirmation signal download:

- local artifact: `temporal_confirmation_model_v1.npz`
- size: 6,696,407 bytes
- SHA-256: `3aead58167b042c98a2b2fd3228b0ce4a4c2358f9ff3f1ed72ca88cddb56906c`

Generated arrays and participant-level outputs remain local and ignored. The
primary validation JSON SHA-256 is
`6a7b8596abcdd4e7024143024326ac80966b0af0c7888feaed9e3efdcc8b4ffc`;
the separate report-only audio-control JSON SHA-256 is
`2eb436128cea4fbf32faad4dd84bbd4bc38558ee980d0295ec0353b467f57160`.

## Next boundary

The next operation may materialize only the three metadata-reserved
confirmation runs. Synchronization and frozen VAD eligibility are applied
mechanically. The serialized model receives no refit, alpha change, threshold
tuning, or replacement of a failed run. Confirmation results are reported once.
