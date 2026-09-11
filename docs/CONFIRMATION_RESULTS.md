# Locked Confirmation Results

Status: compound confirmation criterion passed; construct origin unresolved

## Primary result

The checksum-locked model was applied without any fitting operation to 187
windows from the two synchronization-eligible replacement-confirmation days.
Retrieval candidate sets were kept within day and the primary endpoint equally
weighted the two days.

| Day | Windows | Top-1 | Top-10 | MRR | Exact reference MRR |
|---|---:|---:|---:|---:|---:|
| 2025-02-06 run 05 | 88 | 0.0455 | 0.2159 | 0.12022 | 0.05750 |
| 2025-02-10 run 02 | 99 | 0.0101 | 0.1212 | 0.05892 | 0.05230 |
| Equal-day macro | — | 0.0278 | 0.1686 | 0.08957 | 0.05490 |

Both days individually exceeded their finite-candidate MRR references, although
the second-day margin was small. The evidence is therefore replicated in sign
but heterogeneous in magnitude.

## Frozen decision

All four preregistered checks passed:

- every eligible day exceeded its exact candidate-set reference;
- macro MRR exceeded the macro candidate reference;
- macro MRR exceeded the 99-permutation 95th percentile of 0.06302;
- macro MRR exceeded time-reversed EEG MRR of 0.05770.

The plus-one empirical permutation p-value was 0.01. The evaluator reported
zero fitted operations and verified the frozen model and feature checksums before
array loading.

## Timing controls

| EEG timing condition | Macro MRR |
|---|---:|
| Contemporaneous | 0.08957 |
| -1000 ms circular shift | 0.05824 |
| -500 ms circular shift | 0.06305 |
| +500 ms circular shift | 0.06218 |
| +1000 ms circular shift | 0.05119 |
| Time reversal | 0.05770 |

Unlike validation, no shifted condition exceeded the contemporaneous result.
The eligible rows all belong to the clean-run sensitivity stratum, so its result
equals the primary analysis. One previously observed window-level QC flag was
not a hard exclusion under the frozen policy.

## Execution audit

The first invocation completed the deterministic numerical path but failed while
serializing a NumPy `int64` run count, before writing or printing any metric. A
JSON-native integer conversion and regression test were committed as `7ead0e4`;
the same checksums, calculations, and decision rule were then rerun to recover
the output. No scientific logic or parameter changed.

- result JSON SHA-256: `28c0183c33c5c7925be1944c2a6e60ae29d190fcd55e40efafeaab5cb936eee6`
- feature SHA-256: `f1ae8b6b9735b56e046309c527e9781c9fd678656feb44f9a270fdc6e052b857`
- model SHA-256: `3aead58167b042c98a2b2fd3228b0ce4a4c2358f9ff3f1ed72ca88cddb56906c`

Participant-level arrays and result rows remain local and ignored.

## Interpretation

This confirms that the frozen coarse-temporal EEG ridge signal generalizes to
two later recording days for this participant. It does **not** establish that
the source is cortical language information. The very strong validation
audio-envelope control, overt-speech setting, possible peripheral contamination,
and between-day heterogeneity remain central limitations. The appropriate next
phase is a mechanistic source audit using EMG, spatial/peripheral channel groups,
and physiologically constrained lag analyses—not a larger decoder claim.
