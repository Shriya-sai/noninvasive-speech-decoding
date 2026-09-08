# Temporal ridge protocol

Status: frozen before temporal feature extraction

Date: 2026-09-04

## Rationale

The first ridge baseline collapsed each five-second EEG window over time. Its
held-out result was null, while calibration-day resampling showed a small,
heterogeneous advantage over finite-candidate reference behavior. The next
diagnostic asks whether coarse within-window timing contains reproducible
information without introducing a deep architecture.

## EEG representation

The existing `audit_v1` preprocessed `128 x 1200` window is divided into 20
nonoverlapping 250 ms bins. For every channel and bin, the natural log of RMS
amplitude and first-difference RMS is computed with a `1e-12` floor. This gives
5,120 raw features and preserves coarse temporal ordering.

Within every training fold, features are standardized and reduced to exactly
128 principal components by deterministic SVD. PCA is not whitened. Component
sign is fixed by making its largest-absolute loading positive. Means, scales,
loadings, and signs are fitted on training-fold rows only and applied unchanged
to the held-out day.

## Acoustic target

The aligned 16 kHz vocal waveform is divided into the same 20 nonoverlapping
250 ms bins. Each bin is represented by the mean power in 80 log-mel bands,
giving a temporally ordered 1,600-feature target. STFT and mel parameters remain
the same as the frozen baseline. Target standardization is fitted inside each
training fold only.

This remains an acoustic prediction target. Success cannot by itself identify
a cortical, linguistic, or articulatory source.

## Development analysis

All model choices use the 12 calibration days through nested leave-one-day-out
resampling. Alpha is selected by inner-day macro-MRR. Candidate sets are formed
within each held-out day. The synchronized validation day can be evaluated once
after development choices are locked, but cannot be recycled to change them.

The three replacement confirmation runs remain unmaterialized during this
stage. Their signal contents, synchronization, VAD retention, and QC are unknown.

## Mandatory controls

Every control uses the same outer held-out days:

- circular EEG time-bin shifts of -1000, -500, +500, and +1000 ms;
- reversal of the 20-bin EEG time axis;
- a 20-bin simultaneous vocal-audio RMS-envelope model;
- an unseen-session intercept model;
- 99 within-run EEG/audio pairing permutations from one frozen seed stream.
  These permute target rows at held-out retrieval after the fold model is
  fitted; they do not refit or retune the model.

The model, feature scaling, PCA, and ridge weights are fitted on contemporaneous
training data only. Temporal perturbations are then applied to the held-out EEG
bins before those frozen transformations and weights are used; no shifted or
reversed model is refitted. Refitting would make these operations mere column
permutations for a linear model and therefore an invalid timing control.

Circular shifts preserve each held-out window's marginal values but disrupt its
declared coordinate alignment. They are timing diagnostics rather than literal
physiological models because the end of the window wraps to its beginning.

## Gate before confirmation

Development passes only if contemporaneous EEG exceeds its exact candidate-set
reference on at least nine of 12 outer days, exceeds the 95th percentile of the
99 pairing-null macro-MRR values, and exceeds the time-reversed control. All
daywise results and the complete lag curve must still be reported.

Failure means the three confirmation signals remain unread. Passing permits
download and mechanical eligibility checks, but the model, preprocessing,
reduction, alpha-selection rule, controls, and primary endpoint remain locked.
The confirmation model is never refitted on confirmation data.

### One-time validation gate

Validation is evaluated exactly once after all development decisions are
frozen. Ridge alpha is selected using calibration rows only: leave one recording
day out, refit the feature standardizer, PCA, target standardizer, and ridge in
each fold, and maximize day-macro MRR. Ties select the smaller alpha. The
selected alpha and a single calibration-fitted model are then applied to the
synchronized validation rows without refitting.

Validation passes only if primary MRR is strictly greater than the exact
within-session candidate-set reference MRR, the 95th percentile of 99 held-out
target-row pairing permutations, and the evaluation-only time-reversal control
MRR. The predeclared ±500 ms and ±1000 ms circular-shift controls are reported
but are not pass/fail criteria. Failure keeps confirmation signals unread and
no confirmation model is fitted.

### Final fit after a pass

Only after a validation pass, the calibration-selected alpha is held fixed.
The feature standardizer/PCA, target standardizer, and ridge are fitted once on
all calibration plus synchronized validation rows and serialized before any
confirmation download. This serialized model is immutable for confirmation;
confirmation data cannot select hyperparameters or refit any component.

## Interpretation boundary

A passed development gate would justify one confirmation attempt, not a neural
speech-decoding claim. Evidence for cortical origin additionally requires EMG,
peripheral-versus-central electrode, and physiologically plausible lag analyses.
Those are separate prespecified stages rather than post-hoc explanations for
this model's result.
