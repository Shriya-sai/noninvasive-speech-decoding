# Calibration-day nested resampling

Status: complete; weak and heterogeneous development signal

Date: 2026-09-04

## Design

The corrected analysis used only the raw features from the 2,181 windows
assigned to the 12 calibration days. Feature means and scales were refitted
inside every inner and outer training fold; each held-out day was transformed
with training-fold statistics only.
For each outer fold, one complete day was withheld. Within the remaining 11
days, each candidate ridge alpha was evaluated through inner leave-one-day-out
folds and selected by day-macro mean reciprocal rank. The chosen model was then
fitted on all 11 development days and evaluated once on the outer day.

Neither the original validation rows nor either consumed test day entered this
procedure. Candidate sets remained within each outer day.

## Result

Across 12 outer days, macro top-1 accuracy was 1.03%, macro top-10 accuracy was
9.61%, and macro MRR was 0.0466. The exact candidate-count reference macro-MRR
was 0.0408, a difference of 0.0058. Ten of 12 days were above their individual
reference MRR.

The result is heterogeneous:

| Stratum | Days | Observed MRR | Reference MRR | Difference |
| --- | ---: | ---: | ---: | ---: |
| Clean calibration runs | 10 | 0.0413 | 0.0356 | +0.0057 |
| High-artifact calibration runs | 2 | 0.0733 | 0.0669 | +0.0064 |
| All calibration runs | 12 | 0.0466 | 0.0408 | +0.0058 |

The two artifact strata have similar mean differences after correct foldwise
normalization. One high-artifact day remains below reference, and the largest
positive difference occurs on clean `ses-20230831`. Artifact status is not a
simple explanation, but the small macro advantage remains insufficient for a
neural interpretation.

Hyperparameter selection is also unstable: alpha 10 and 1000 were each selected
in four folds, alpha 100 in three, and alpha 1 once. This sensitivity is
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
