# Calibration-day nested resampling

Status: complete; weak and heterogeneous development signal

Date: 2026-09-04

## Design

The analysis used only the 2,181 windows assigned to the 12 calibration days.
For each outer fold, one complete day was withheld. Within the remaining 11
days, each candidate ridge alpha was evaluated through inner leave-one-day-out
folds and selected by day-macro mean reciprocal rank. The chosen model was then
fitted on all 11 development days and evaluated once on the outer day.

Neither the original validation rows nor either consumed test day entered this
procedure. Candidate sets remained within each outer day.

## Result

Across 12 outer days, macro top-1 accuracy was 1.22%, macro top-10 accuracy was
9.17%, and macro MRR was 0.0483. The exact candidate-count reference macro-MRR
was 0.0408, a difference of 0.0075. Nine of 12 days were above their individual
reference MRR.

The result is heterogeneous:

| Stratum | Days | Observed MRR | Reference MRR | Difference |
| --- | ---: | ---: | ---: | ---: |
| Clean calibration runs | 10 | 0.0386 | 0.0356 | +0.0030 |
| High-artifact calibration runs | 2 | 0.0970 | 0.0669 | +0.0302 |
| All calibration runs | 12 | 0.0483 | 0.0408 | +0.0075 |

The largest positive difference occurs on the short, high-amplitude
`ses-20230905` run (38 candidates). The other high-artifact day is slightly
below reference. Thus artifact status is not a simple explanation, but the
macro advantage is not stable enough to support a neural interpretation.

Hyperparameter selection is also unstable: alpha 10 was selected in six outer
folds, alpha 100 in four, and alpha 1 and 1000 once each. This sensitivity is
consistent with substantial day-to-day distribution shift.

## Replacement confirmation reservation

Before this analysis, three later confirmation runs were frozen using annex
metadata only. The smallest complete EEG plus vocal-WAV run was selected in
each post–January 22 chronological block:

| Block | Reserved day and run | Combined size |
| --- | --- | ---: |
| 2025-01-27 to 2025-01-31 | 2025-01-29 run 05 | 331,388,358 bytes |
| 2025-02-03 to 2025-02-07 | 2025-02-06 run 05 | 347,421,958 bytes |
| 2025-02-10 | 2025-02-10 run 02 | 327,073,910 bytes |

Exact paths and SHA-256 hashes are frozen in
`configs/replacement_confirmation_v1.toml`. No signal QC or model outcome was
used, and the files were not downloaded at the time of reservation.

## Decision

The calibration result justifies investigating temporal information that the
bandpower summary discards, but only inside calibration/validation development
data. It does not reverse the held-out test null. The next model specification
must be frozen before the reserved confirmation signals are inspected. It must
also retain day-held-out resampling, artifact-stratum reporting, direct-acoustic
controls, and training-only preprocessing.
