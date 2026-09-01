# Multi-day artifact-QC calibration

Status: 16-run expansion complete; global hard-exclusion threshold not frozen

Date: 2026-09-02

## Selection and integrity

The 104 `sub-01` overt-speech Pangolin days were divided into ten contiguous
timeline strata. Within each stratum, the smallest complete EEG plus vocal-WAV
run was selected using annex byte size only. Signal quality, VAD retention, and
model outcomes were not used for selection.

The resulting 4.58 GiB subset contains six calibration days, two validation
days, and two test days spanning September 2023 through January 2025. All 20
signal files pass their frozen byte-size and SHA-256 checks. Raw files and
generated tables remain local and ignored by Git.

## Synchronization

Nine of ten runs pass the frozen speech-envelope gate. The
`ses-20241206` validation run has strong envelope agreement (`r = 0.950`) but a
median residual of -281 ms, outside the preregistered ±250 ms bound. The gate
was not relaxed after seeing this result.

One calibration run has an EEG-to-WAV offset of -2.4 ms. The window constructor
now keeps the same EEG-time-zero five-second grid and skips only grid windows
whose corresponding audio is out of bounds. This drops the first window of
that run without shifting later windows.

## Window inventory

The frozen Silero profile produces 1,867 complete candidate windows and retains
1,249 with at least 20% detected speech:

| Role | Retained windows |
| --- | ---: |
| Calibration, six days | 885 |
| Validation, two days | 224 |
| Test, two days | 140 |

## Threshold-free QC findings

Every retained window was processed continuously and characterized using
robust channel amplitude, peak-to-peak range, temporal gradient, residual
50 Hz burden, cross-channel correlation, and post-standardization clipping.

Selected run-median values show pronounced day effects:

| Day | Role | Maximum-channel peak-to-peak | Maximum gradient RMS | Clipped values |
| --- | --- | ---: | ---: | ---: |
| 2023-09-05 | calibration | 233,548 µV | 4,331 µV | 0.019% |
| 2023-10-13 | calibration | 1,048 µV | 110 µV | 0.056% |
| 2024-07-19 | calibration | 1,470,228 µV | 63,002 µV | 0.906% |
| 2024-07-30 | validation | 1,287 µV | 166 µV | 0.064% |
| 2025-01-07 | test | 39,590 µV | 646 µV | 0.057% |
| 2025-01-22 | test | 153,929 µV | 3,644 µV | 0.096% |

These shifts are not explained simply by the EDF calibration coefficient. They
may reflect sparse high-amplitude artifacts, run-level acquisition changes, or
both. The later test days differ materially from the clean validation days,
which is itself relevant to claims of temporal generalization.

## Rejected first threshold proposal

A six-scaled-MAD rule fitted only to the 885 calibration windows rejected:

| Role | Rejected | Total |
| --- | ---: | ---: |
| Calibration | 349 | 885 |
| Validation | 0 | 224 |
| Test | 70 | 140 |

The result is not accepted as a frozen artifact rule because:

1. windows are not independent calibration units;
2. the 276-window `ses-20240719` run dominates the pooled distribution;
3. fitted flatness and correlation bounds are nonphysical;
4. peak-to-peak and gradient flags are nearly redundant;
5. rejection is driven by entire-day shifts rather than isolated windows.

Validation and test rows were evaluated but never supplied to the fitting
function; the implementation raises if a forbidden role is passed for fitting.
The generated threshold JSON is exploratory and remains uncommitted.

## Consequence

The data-ingestion and metric gates pass, but universal window rejection is not
yet scientifically justified. The next calibration must treat day as the unit:

- add calibration runs/days without changing validation or test membership;
- fit run-level and within-run components separately;
- equal-weight calibration days;
- preserve high-artifact days as an explicit robustness stratum;
- examine results both with and without calibration-only exclusions.

Model training should not begin until that hierarchical rule is frozen or the
analysis is explicitly redesigned to use QC metrics as sensitivity variables
rather than hard exclusion criteria.

## Day-balanced expansion

A second calibration wave added six days, one from each of the original six
calibration timeline strata. Selection again used annex byte size and temporal
position only. The two validation days and two test days were not changed.
The expanded subset therefore contains 12 calibration days, two validation
days, and two test days. All 32 EEG/WAV objects pass their pinned byte-size and
SHA-256 checks.

The frozen synchronization gate passes 15 of 16 runs. All 12 calibration runs
and both test runs pass. The same `ses-20241206` validation run remains the
sole failure; its timing criterion was not relaxed.

Applying the already-frozen five-second grid and VAD rule gives 4,010 complete
candidate windows and retains 2,545:

| Role | Retained windows |
| --- | ---: |
| Calibration, 12 days | 2,181 |
| Validation, two days | 224 |
| Test, two days | 140 |

## Hierarchical threshold gate

The second proposal uses each calibration run as one equally weighted unit.
For every metric it fits a robust threshold to run medians in log space, then
uses a separate within-run robust-z rule to identify unusual windows. Physical
bounds are enforced for correlation and clipped fraction. Fitting code accepts
calibration rows only.

The combined 12-day fit flags:

| Role | Run-level | Additional window-level | Any flag | Total |
| --- | ---: | ---: | ---: | ---: |
| Calibration | 314 | 59 | 371 | 2,181 |
| Validation | 0 | 1 | 1 | 224 |
| Test | 140 | 7 | 140 | 140 |

The run-level calibration flags comprise the same extreme `ses-20240719` day
and the short, high-amplitude `ses-20230905` day. Both held-out test days exceed
the combined peak-to-peak run threshold; the later test day also exceeds the
gradient threshold. These held-out observations were evaluated only after the
calibration fit and were not used to alter it.

The decisive problem is calibration-wave instability. Peak-to-peak thresholds
are approximately 3.78e8 µV from wave 1 alone, 5.09e3 µV from wave 2 alone,
and 1.58e4 µV from both waves. Gradient thresholds similarly move from
1.14e4 µV to 1.34e3 µV, with a combined value of 2.29e3 µV. Wave 1 contains
two extreme run medians and is too small for a scaled-MAD rule to resist both;
wave 2 contains no comparable run. A single global hard threshold is therefore
not stable under the predeclared calibration expansion and is not frozen.

## Decision and next gate

The windowing and VAD rules remain frozen. Artifact metrics will next be used
as explicit run-level strata and sensitivity variables, while unequivocal
technical failures are handled by predeclared physical checks. The primary
model analysis must report performance across clean and high-artifact strata
rather than silently deleting entire held-out days. Any future hard-exclusion
rule requires a new calibration-only specification and another untouched
evaluation split; the current validation and test results cannot be reused to
tune it.
