# Confirmation Temporal Feature Extraction

Status: complete; representations frozen before model evaluation

The guarded confirmation extractor consumed only rows marked `model_eligible`
in the checksum-frozen confirmation manifest. It did not load or apply the
serialized model.

## Scope audit

- rows: 187, matching the eligible manifest IDs exactly and in order
- roles: 187 `confirmation`; zero calibration, validation, or consumed-test rows
- days: 88 windows from 2025-02-06 run 05 and 99 from 2025-02-10 run 02
- EEG tensor: `(187, 20, 256)`, finite `float32`
- acoustic target: `(187, 20, 80)`, finite `float32`
- audio envelope: `(187, 20)`, finite `float32`

The representations use the already-frozen 20 nonoverlapping 250 ms bins,
128-channel log-RMS and log-gradient-RMS EEG statistics, and 80-band per-bin
log-mel acoustic target. No representation, eligibility, or threshold was
changed after confirmation signals became available.

## Local artifact

- filename: `confirmation_temporal_features_v1.npz`
- SHA-256: `f1ae8b6b9735b56e046309c527e9781c9fd678656feb44f9a270fdc6e052b857`

Participant-level arrays remain local and ignored.

## Next boundary

The next step is the single confirmation evaluation. It must verify both the
feature-bundle and serialized-model checksums, apply the saved PCA/scalers/ridge
without fitting any parameter, calculate retrieval independently within each
day, and report the equal-day macro average regardless of outcome.
