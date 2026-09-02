# Baseline modeling protocol

Status: frozen before feature extraction or model fitting

Date: 2026-09-02

## Purpose

The first model is a diagnostic baseline, not an attempted reproduction of the
underspecified HTNet/Conformer architecture. It asks whether simple EEG summary
features retrieve paired acoustic summaries on genuinely later recording days,
and whether apparent performance survives session and artifact controls.

## Population and independence

The analysis is participant-specific (`sub-01`). The independence unit is the
recording day, never the five-second window. The 12 previously designated
calibration days are training data, the two validation days remain validation,
and the two final chronological days remain test. Roles cannot be reassigned.
All preprocessing statistics and model parameters are fitted on calibration
days only.

The `ses-20241206` validation run fails the frozen synchronization gate and is
ineligible for paired EEG/audio modeling. It remains in provenance and in the
synchronization report. Its failure is not repaired by changing the timing
tolerance. Hyperparameter selection therefore uses the other, synchronized
validation day. Both test days pass synchronization.

## Windows and artifact policy

Only windows retained by the frozen `audit_v1` five-second/VAD profile are
eligible. There is no learned hard artifact exclusion. Every synchronized run
is labeled `clean_run` or `high_artifact_run` from calibration-frozen QC
measurements, and performance is reported for the full eligible set and by
artifact stratum. Artifact labels are outcomes used for sensitivity analysis,
not a mechanism for optimizing the test set.

The executed manifest contains 2,453 model-eligible windows:

| Role and stratum | Eligible windows |
| --- | ---: |
| Calibration, clean run | 1,867 |
| Calibration, high-artifact run | 314 |
| Validation, clean run | 132 |
| Test, high-artifact run | 140 |

The additional 92 VAD-retained validation windows belong to the synchronization-
failing day and are marked ineligible rather than deleted from provenance. Both
test days fall in the high-artifact sensitivity stratum. Consequently, primary
test performance measures temporal generalization under a substantial signal-
quality shift; it cannot estimate clean-late-day performance from this subset.

## Input, target, and model

EEG input is represented by channel-wise log bandpower in six fixed bands:
2-4, 4-8, 8-13, 13-30, 30-55, and 65-120 Hz. The 55-65 Hz gap avoids the
50 Hz notch neighborhood. Features are standardized using calibration data
only.

The target is an 80-bin log-mel summary of the simultaneous vocal WAV,
represented by its mean and standard deviation over the window. This is an
acoustic target, so success establishes paired acoustic predictability—not
language comprehension or cortical origin.

A multi-output ridge regression maps EEG features to acoustic features.
Regularization is selected from the frozen alpha grid using validation-day
mean reciprocal rank. No deep architecture is justified until this transparent
baseline and its controls are understood.

## Retrieval and reporting

Cosine retrieval is performed within each held-out day using every eligible
window in that day as the candidate set. Top-1 accuracy, top-10 accuracy, and
mean reciprocal rank are reported separately for each day and as an equally
weighted day macro-average. Candidate counts are reported with every result;
metrics with different candidate counts are not treated as directly equivalent.

Required controls are:

1. audio-envelope-only features, which measure direct acoustic contamination;
2. session-metadata-only features, which measure candidate-set/session cues;
3. permuted EEG/audio pairing, which verifies nominal retrieval behavior.

The primary comparison retains all synchronized windows. Clean/high-artifact
results are sensitivity analyses. Random-window performance may later be shown
only as a paper-matched contrast and cannot replace the held-out-day result.

## Gate to training

Feature extraction may begin only after the configuration and manifest
validators pass. Model results must not be interpreted as neural speech
decoding until they outperform the acoustic and metadata controls and show
plausible spatial and temporal specificity in later project phases.
