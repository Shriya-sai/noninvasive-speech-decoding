# Phase 0 dataset audit

Status: initial metadata audit, no signal files downloaded
Audit date: 2026-08-29

## Authoritative release identity

- OpenNeuro accession: `ds007808`
- Snapshot tag: `1.0.0`
- Snapshot DOI: <https://doi.org/10.18112/openneuro.ds007808.v1.0.0>
- OpenNeuro Git commit for tag `1.0.0`: `dc37d8078c575eb067c26acc7f2d656f86af6bca`
- Dataset name in `dataset_description.json`: `EEG-Speech Brain Decoding Dataset`
- BIDS version: `1.9.0`
- Dataset type: raw
- License: CC0
- Git tree enumeration: 13,846 entries; API response was not truncated

The tag and commit above, rather than the mutable branch name, are the required
source identity for future downloads and manifests.

## Participants

The authoritative `participants.tsv` contains three right-handed healthy male
participants:

| Participant | Age | Sex | Group | Session directories |
|---|---:|---|---|---:|
| `sub-01` | 32 | M | control | 263 |
| `sub-02` | 44 | M | control | 46 |
| `sub-03` | 22 | M | control | 13 |

Session directories are dated recording days. Runs are nested within those
days. Neither windows nor runs are independent biological participants.

## Task and acquisition coverage

Counts below come from the complete set of 1,974 run-level `events.tsv` files
in the tagged Git tree.

| Participant | Task | Acquisition | Days | Runs |
|---|---|---|---:|---:|
| `sub-01` | listening | pangolin | 6 | 19 |
| `sub-01` | listeningcovert | pangolin | 66 | 199 |
| `sub-01` | speechopen | eego | 46 | 172 |
| `sub-01` | speechopen | pangolin | 104 | 372 |
| `sub-01` | speechopen | scarabeo | 41 | 138 |
| `sub-02` | listening | pangolin | 7 | 45 |
| `sub-02` | speechopen | pangolin | 39 | 980 |
| `sub-03` | speechopen | pangolin | 13 | 49 |

The unexpectedly large number of `sub-02` runs relative to days must be
understood before run count is used as a sampling or uncertainty unit.

## Released modalities and hardware

- `speechopen`: overt production of visually presented text
- `listening`: listening to prerecorded speech
- `listeningcovert`: listening followed by covert speech imagery
- g.Pangolin: 128 EEG channels plus audio monitor, EOG, EMG, trigger, and some
  auxiliary/reference channels depending on the recording
- g.SCARABEO: 62 analysis EEG channels plus mastoids and auxiliary channels
- eego sports: 63 EEG channels plus miscellaneous, audio-monitor, EOG, EMG, and
  trigger channels

Run-level `channels.tsv` files are authoritative. Only g.Pangolin recordings
have verified released electrode coordinates. A single assumed common channel
layout must not be imposed across devices.

## Published aggregate scale

The dataset paper reports approximately 1,020 recording hours and 955 GB. Its
event-level table reports:

- 287,404 overt events spanning about 457.5 event-hours
- 45,641 listening events spanning about 43.7 event-hours
- 20,515 covert events spanning about 28.5 event-hours

These are event counts and event durations, not independent sample sizes.

## Anchor-reproduction subset

The 2024 anchor paper describes 175 hours from one participant recorded across
48 days with 128-channel g.Pangolin EEG during overt speech. The released data
contain a broader `sub-01`/`speechopen`/`pangolin` collection: 104 days and 372
runs. The top-level BIDS metadata do not identify which exact 48 days formed the
paper's training, validation, and test sets.

Therefore the current anchor-subset status is **reconstructable in principle but
not yet uniquely mapped**.

Required resolution steps:

1. Extract the paper's date range and split algorithm from the full methods,
   supplement, or released training code.
2. Compare those details with run-level dates, event content, and durations.
3. Locate an upstream manifest or author-released checkpoint configuration.
4. If the exact mapping remains ambiguous, contact the authors before labeling
   any result an exact reproduction.
5. Keep a separately labeled conceptual reproduction using a fully specified
   subset available as a fallback.

No chronological subset should be guessed and retroactively presented as the
original 175-hour sample.

## Reproducibility assets

The release contains BIDS conversion and preprocessing paths under `code/`, but
many code entries in the GitHub mirror are git-annex links rather than directly
rendered source. The repository also contains a detailed ingestion manifest
with original and BIDS paths, acquisition time, sampling frequency, channel
count, source content type, and source title for many runs.

The ingestion manifest contains internal source paths and pre-anonymization
working labels. It may be used locally for provenance analysis but must not be
copied wholesale into this repository or published in derived reports.

## Confirmed design consequences

1. The primary strict split can use recording date as a defensible group.
2. Scaling must be reported against both hours and number of independent days.
3. Device transfer is possible only within `sub-01`; it is not separable from
   participant effects in the full dataset.
4. Cross-participant transfer should initially use the common g.Pangolin overt
   condition and remain exploratory because there are three participants.
5. Covert transfer is currently a within-`sub-01`, g.Pangolin question.
6. Phrase/source-content overlap must be audited because sessions include books,
   video games, and speech-corpus material.
7. Day-held-out and source-title-held-out tests answer different questions and
   should both be considered.

## Data-download strategy

Do not download the complete 955 GB release initially. Use staged retrieval:

1. top-level and run-level metadata only;
2. two small g.Pangolin overt runs for synchronization and channel validation;
3. a multi-day pilot subset for windowing and null tests;
4. the resolved anchor-paper subset;
5. other devices and covert/listening data only after the anchor pipeline passes.

Every stage requires a tag-pinned manifest and checksums. Raw files remain
immutable and excluded from Git.

## Current gate decision

**Proceed with metadata and methods reconstruction; do not begin full training.**

The dataset clearly supports the planned project. The immediate blocker is not
data quantity but exact reconstruction of the anchor sample and evaluation
procedure.

## Sources inspected

- OpenNeuro `ds007808` snapshot metadata and tagged Git tree
- Dataset `README`, `CHANGES`, `participants.tsv`, and ingestion-manifest header
- Sato et al. (2024), arXiv:2407.07595
- Sato et al. (2026), arXiv:2606.01264
