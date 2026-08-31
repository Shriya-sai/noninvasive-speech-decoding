# Preprocessing and leakage-validation pilot

Status: implementation gate passed; artifact-rejection rule pending

Date: 2026-08-31

## Implemented profile

The `audit_v1` continuous EEG path restores channel roles from `channels.tsv`,
selects exactly 128 EEG channels, applies a 50 Hz notch, common-average
reference, 2-120 Hz band-pass, and resamples from 1200 to 240 Hz. Each retained
five-second window is then z-scored per channel over time and clipped to
`[-5, 5]`, producing a `float32` array shaped `128 x 1200`.

MNE's version-bounded defaults currently define the unresolved filter-design
details. NLMS is not enabled: the paper's step size and epsilon do not resolve
its tap structure, signal scaling, initialization, or reset boundaries.

## Execution results

| Run | Retained windows | Finite | Shape | Clipped values | Worst post-clip SD error |
| --- | ---: | --- | --- | ---: | ---: |
| 2023-08-31 run 06 | 90 | yes | 128 x 1200 | 0.165% | 0.573 |
| 2023-09-05 run 02 | 38 | yes | 128 x 1200 | 0.172% | 0.299 |

All 128 retained pilot windows passed channel-count, sample-count, dtype, and
finiteness invariants. The maximum absolute post-clipping channel mean was
0.041 in the larger run and 0.037 in the smaller run.

The global clipping fractions are low, but the worst channel-level standard
deviation deviations are material. This is consistent with sparse,
artifact-heavy channels or windows: clipping occurs after unit-variance
normalization and necessarily reduces variance when extreme samples are
present. These observations must not be hidden by global averages.

## Manifest and splits

The local, Git-ignored provenance manifest contains 242 complete candidate
windows: 128 retained and 114 rejected by the 20% speech rule. Every record has
an immutable dataset snapshot, participant, session, run, EEG/WAV bounds,
preprocessed sample bounds, control-channel availability, speech occupancy,
and an explicit retention decision.

The retained pilot splits are:

| Regime | Train | Validation | Test | Interpretation |
| --- | ---: | ---: | ---: | --- |
| Seeded random window | 102 | 12 | 14 | reproduction comparator only |
| Run held out | 90 | 0 | 38 | leakage-safe two-run pipeline check |
| Day held out | 90 | 0 | 38 | leakage-safe two-day pipeline check |

All regimes pass the no-cross-split temporal-overlap assertion. Run/day splits
also pass complete group isolation. With only two pilot days, validation cannot
be independent; model selection must wait for a larger multi-day subset.

## Reproduction

```bash
python scripts/build_window_manifest.py \
  data/raw/ds007808 results/pilot_window_manifest.tsv
python scripts/build_pilot_splits.py \
  results/pilot_window_manifest.tsv results/pilot_splits.tsv
python scripts/audit_preprocessing_pilot.py \
  <run_eeg.edf> results/pilot_window_manifest.tsv
```

The manifests and signal arrays remain local and ignored by Git.

## Next gate

Before training even a lightweight decoder, freeze window/channel artifact QC
using distributions from more than two days, download a small multi-day subset
that supports independent train/validation/test days, and verify that any QC
threshold is fitted without looking at held-out outcomes.
