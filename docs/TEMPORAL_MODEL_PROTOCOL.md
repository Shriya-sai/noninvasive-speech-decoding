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

Every control uses the identical nested day-resampling structure:

- circular EEG time-bin shifts of -1000, -500, +500, and +1000 ms;
- reversal of the 20-bin EEG time axis;
- a 20-bin simultaneous vocal-audio RMS-envelope model;
- an unseen-session intercept model;
- 99 within-run EEG/audio pairing permutations from one frozen seed stream.

Circular shifts preserve the marginal feature distribution but disrupt the
declared alignment. They are timing diagnostics rather than literal physiological
models because the end of the window wraps to its beginning.

## Gate before confirmation

Development passes only if contemporaneous EEG exceeds its exact candidate-set
reference on at least nine of 12 outer days, exceeds the 95th percentile of the
99 pairing-null macro-MRR values, and exceeds the time-reversed control. All
daywise results and the complete lag curve must still be reported.

Failure means the three confirmation signals remain unread. Passing permits
download and mechanical eligibility checks, but the model, preprocessing,
reduction, alpha-selection rule, controls, and primary endpoint remain locked.
The confirmation model is never refitted on confirmation data.

## Interpretation boundary

A passed development gate would justify one confirmation attempt, not a neural
speech-decoding claim. Evidence for cortical origin additionally requires EMG,
peripheral-versus-central electrode, and physiologically plausible lag analyses.
Those are separate prespecified stages rather than post-hoc explanations for
this model's result.
