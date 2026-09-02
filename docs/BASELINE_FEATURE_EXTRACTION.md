# Baseline feature extraction

Status: complete and validated

Date: 2026-09-02

## Frozen representations

Each eligible preprocessed EEG window is summarized by channel-wise Welch
power in six bands: 2-4, 4-8, 8-13, 13-30, 30-55, and 65-120 Hz. Power is
integrated within band, floored at `1e-12`, and natural-log transformed. With
128 channels, this produces 768 EEG features per window. Welch uses a Hann
window, 240-sample segments, and 120-sample overlap at 240 Hz.

The corresponding vocal-audio interval is read from channel zero, converted to
floating point, and polyphase-resampled to 16 kHz. A 512-point STFT uses
400-sample Hann frames and a 160-sample hop. Eighty unit-area mel filters span
20-7,600 Hz. The mean and standard deviation of each log-mel band over time
produce 160 acoustic target features.

## Executed inventory

Feature extraction ran on every synchronized, VAD-retained row in the frozen
model manifest:

| Role | Windows |
| --- | ---: |
| Calibration | 2,181 |
| Validation | 132 |
| Test | 140 |
| Total | 2,453 |

The saved arrays have shapes `2453 x 768` for EEG and `2453 x 160` for audio.
Raw and standardized arrays are finite `float32`; window identifiers are unique.

## Leakage audit

Featurewise means and scales were fitted using the 2,181 calibration rows only,
then applied unchanged to validation and test. Calibration standardized means
are within `7.8e-7` of zero and standard deviations within `1.5e-6` of one.
Held-out distributions were not renormalized: average absolute standardized
means are 0.479/0.647 for validation/test EEG and 1.244/1.041 for validation/test
audio. These shifts are retained as properties of later recording days.

## Local artifact

The compressed feature bundle is 15.68 MiB and remains local rather than being
committed to Git:

`baseline_features_v1.npz`

SHA-256:
`e6ec5fa06b50dd9727f22b8efe4e9f8de03d13ac93862f3850b73493a08cb9da`

The artifact contains raw features, calibration-standardized features,
training means/scales, window IDs, source runs, frozen roles, and artifact
strata. It contains derived participant data and is intentionally excluded from
the public repository.

## Interpretation boundary

These features support a transparent diagnostic model. The acoustic target is
not a linguistic label, and successful retrieval can reflect neural activity,
myogenic contamination, acoustic vibration, or stable session structure.
Required controls and later spatial/temporal analyses remain necessary before
making a cortical speech-decoding claim.
