# Temporal feature extraction

Status: development-only extraction complete

Date: 2026-09-07

## Scope protection

Extraction used only synchronized rows labeled `calibration` or `validation`
in the frozen model manifest. The resulting bundle contains 2,181 calibration
windows and 132 validation windows from 13 runs. It contains no consumed test
rows and no replacement-confirmation rows.

After extraction, all six reserved EEG/audio objects were verified to remain
git-annex symlinks with absent local object content. Confirmation signals have
therefore not been downloaded or inspected.

## Executed representations

For each preprocessed EEG window, 20 nonoverlapping 250 ms bins were summarized
with channel-wise log-RMS and log-gradient-RMS. The saved EEG tensor has shape
`2313 x 20 x 256`: 128 channels times two statistics in each temporal bin.

Each aligned vocal-audio window was resampled to 16 kHz and divided into the
same 20 bins. Mean 80-band log-mel power in each bin gives an acoustic tensor
of shape `2313 x 20 x 80`. A matching RMS-envelope control has shape
`2313 x 20`.

All arrays are finite `float32`, all 2,313 window identifiers are unique, and
the bundle contains exactly 13 source runs. No global standardization or PCA is
stored: these transformations must be fitted separately inside each later
training fold.

## Local artifact

The 53.58 MiB compressed bundle remains local and is excluded from Git:

`temporal_features_v1.npz`

SHA-256:
`4b75d0130ab6628b94bdb2a90e19225c1846233a64c2dd6422f8986991f12f31`

The public repository contains the frozen specification, extraction code,
tests, tensor inventory, and checksum—but no derived participant arrays.

## Next gate

The next step is to implement fold-local standardization and deterministic PCA,
then run nested calibration-day evaluation for the contemporaneous model and
all prespecified controls. The synchronized validation day remains unused by
that nested development estimate and may be evaluated once only after the
development implementation is locked.
