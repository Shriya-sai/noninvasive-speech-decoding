# Held-out-day ridge baseline

Status: complete; no evidence of above-control EEG retrieval

Date: 2026-09-04

## Execution

The frozen baseline used 2,181 calibration windows, 132 windows from the sole
synchronized validation day, and 140 windows from two held-out test days. A
multi-output ridge model mapped 768 standardized EEG log-bandpower features to
160 standardized vocal-audio log-mel summaries. Validation mean reciprocal
rank selected alpha 100 from the predeclared grid. Test data were not used for
model or hyperparameter selection.

Retrieval candidates were restricted to the same held-out recording day. This
produced 117 candidates on 2025-01-07 and 23 candidates on 2025-01-22. Because
candidate counts differ, each day is reported separately and the macro result
weights days equally.

## Results

| Condition | Top-1 macro | Top-10 macro | MRR macro |
| --- | ---: | ---: | ---: |
| EEG ridge | 2.60% | 21.66% | 0.0955 |
| Unseen-session intercept | 2.60% | 26.01% | 0.1040 |
| Vocal-audio RMS envelope | 3.03% | 26.87% | 0.1122 |

The EEG result by day was:

| Test day | Candidates | Top-1 | Top-10 | MRR |
| --- | ---: | ---: | ---: | ---: |
| 2025-01-07 | 117 | 0.85% | 8.55% | 0.0416 |
| 2025-01-22 | 23 | 4.35% | 34.78% | 0.1495 |

For an input that gives every query the same prediction, exact finite-candidate
behavior is one top-1 match, up to ten top-10 matches, and the harmonic mean of
ranks. The unseen-session intercept realizes that reference: MRR is 0.0457 for
117 candidates and 0.1624 for 23 candidates. EEG is below that reference on
both days.

## Pairing null

Five preregistered seeds permuted calibration targets within each source run,
preserving day distributions while breaking EEG/audio pairing. Their test
macro-MRR values were 0.1079, 0.1137, 0.1120, 0.1221, and 0.1184. Every
permuted model exceeded the correctly paired EEG model. With the finite-seed
plus-one calculation, the one-sided empirical p-value for EEG MRR exceeding
this null is 1.0. The permutation count is intentionally small at this gate and
does not provide a precise tail estimate; no tail claim is needed because the
observed statistic is in the wrong direction.

## Interpretation

This transparent feature/model combination does not generalize EEG-to-acoustic
retrieval to later days. The result is not evidence that JapanEEG contains no
decodable neural information: both test days are in the high-artifact stratum,
the target is a coarse acoustic summary, and a linear bandpower model discards
temporal structure. It does establish that the current subset cannot support a
positive claim from this baseline and that greater model flexibility must not
be selected by repeated inspection of these test days.

The audio-envelope control is slightly above the intercept reference but is
not clearly separated from the five EEG pairing-null results. Its purpose here
is diagnostic: simultaneous audio contains predictive structure unavailable to
the EEG baseline, while neither result warrants a cortical interpretation.

## Decision

The two current test days are now consumed for this baseline family. They will
not be used to tune architecture, bands, targets, or artifact handling. The
next scientifically valid step is a calibration/validation-only development
analysis with day-resampling and richer temporal controls, followed by a newly
reserved untouched day set before evaluating any upgraded model.

The complete generated JSON remains local with the derived feature arrays; the
public repository contains the frozen configuration, implementation, tests,
and this compact result report.
