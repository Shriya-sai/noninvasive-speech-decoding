# Non-Invasive Speech Decoding

An independent reproduction and mechanistic audit of data scaling in
non-invasive open-vocabulary speech decoding using the public JapanEEG dataset.

## Central question

Does speech-decoding performance scale with EEG recording duration because a
model learns increasingly stable neural representations, or because it learns
participant-, session-, device-, acoustic-, and articulation-specific signals?

## Current status

Phase 0 data, synchronization, windowing, preprocessing, and multi-day QC gates
are complete. A frozen held-out-day linear baseline has also been executed on
2,453 eligible windows. It did not show EEG retrieval above the unseen-session
or pairing-permutation controls. The current test days are therefore consumed
for this model family; richer model development must remain within calibration
and validation data. Three later confirmation runs have now been reserved by
metadata only and remain untouched. The temporal ridge protocol is frozen;
development-only temporal feature extraction is complete, and nested
calibration-day temporal evaluation has passed its prespecified gate. One-time
validation has now passed all three frozen criteria, and the immutable final
model was serialized on calibration plus synchronized validation before any
confirmation access. The dominant audio-envelope control and a stronger +500 ms
lag diagnostic sharply limit neural interpretation. The three reserved runs are
now materialized and mechanically screened: two synchronization-passing days
provide 187 frozen eligible windows. Their temporal tensors were scope-audited
and checksum-frozen, and the single no-refit confirmation evaluation passed all
prespecified criteria. The effect replicated across both days but was strongly
heterogeneous; mechanistic source auditing is now required before any neural
speech-decoding claim.

The project is anchored in Sato et al., *Scaling Law in Neural Data:
Non-Invasive Speech Decoding with 175 Hours of EEG Data* (2024), and the public
JapanEEG release described by Sato et al., *A 1000-hour EEG-EMG-audio dataset of
Japanese speech production* (2026).

## Evidential boundaries

- The primary biological unit is the participant; events and windows are not
  independent participants.
- Random-window evaluation is a reproduction condition, not the primary test.
- The primary confirmation uses held-out recording sessions or days.
- Above-chance overt-speech retrieval is not by itself evidence of cortical
  language decoding.
- EEG must be compared with facial EMG, metadata, temporal, and spatial controls.
- With three participants, cross-participant analyses are exploratory.

## Research roadmap

1. Audit the dataset, associated papers, and original split construction.
2. Validate synchronization, windowing, candidate construction, and null tests.
3. Reproduce the reported single-participant scaling result.
4. Compare random-window, run-held-out, session-held-out, and phrase-aware splits.
5. Decompose EEG, EMG, acoustic, device, and session contributions.
6. Test temporal/spatial plausibility and overt-to-covert transfer.

Phase 0 now includes a checksum-verified, two-run header and synchronization
pilot. See [the pilot data audit](docs/PILOT_DATA_AUDIT.md) for the observed
run-specific timing offsets and the resulting loader requirements.

The subsequent [signal synchronization and windowing gate](docs/SIGNAL_SYNCHRONIZATION_AND_WINDOWING.md)
validates the clock mapping at speech-envelope resolution and freezes the
`audit_v1` five-second window and Silero VAD eligibility profile.

The [preprocessing pilot](docs/PREPROCESSING_PILOT.md) executes the continuous
EEG pipeline on both pinned runs and records shape, finiteness, clipping, and
split-leakage results without committing signal arrays.

The [multi-day QC calibration report](docs/MULTIDAY_QC_CALIBRATION.md) expands
the audit to 16 timeline-stratified days. It documents why both the first
pooled threshold and a 12-day, day-balanced hierarchical hard-exclusion rule
were rejected rather than tuned against held-out sessions.

The [baseline modeling protocol](docs/BASELINE_MODELING_PROTOCOL.md) freezes a
transparent held-out-day ridge retrieval baseline, artifact sensitivity strata,
and mandatory acoustic, metadata, and permutation controls before training.

The [baseline feature-extraction report](docs/BASELINE_FEATURE_EXTRACTION.md)
records the executed EEG/audio representations, calibration-only
standardization audit, array inventory, and local artifact checksum.

The [held-out-day ridge results](docs/RIDGE_BASELINE_RESULTS.md) report the
first executed EEG retrieval baseline, direct audio and session controls,
within-run pairing nulls, and the resulting diagnostic null decision.

The [calibration-day resampling report](docs/CALIBRATION_DAY_RESAMPLING.md)
documents weak, heterogeneous leave-one-day-out evidence and the metadata-only
reservation of three replacement confirmation runs.

The [temporal ridge protocol](docs/TEMPORAL_MODEL_PROTOCOL.md) freezes the
within-window representation, foldwise PCA/ridge procedure, temporal and
pairing controls, and the gate that protects the reserved confirmation data.

The [temporal feature report](docs/TEMPORAL_FEATURE_EXTRACTION.md) records the
executed development-only tensors, scope audit, local checksum, and confirmation
non-access verification.

The [temporal development results](docs/TEMPORAL_DEVELOPMENT_RESULTS.md) report
the nested calibration-day result, lag/reversal diagnostics, 99-permutation
null, direct-audio control, and passed development-gate decision.

The [one-time temporal validation results](docs/TEMPORAL_VALIDATION_RESULTS.md)
record the passed frozen gate, lag and audio-envelope construct-validity
warnings, and checksum of the serialized no-refit confirmation model.

The [replacement confirmation eligibility report](docs/CONFIRMATION_ELIGIBILITY.md)
records the six verified downloads, one frozen synchronization failure, VAD/QC
audit, exact 187-window evaluation set, and local artifact checksums.

The [confirmation feature-extraction report](docs/CONFIRMATION_FEATURE_EXTRACTION.md)
records the exact two-day row identities, tensor shapes, finiteness audit, and
checksum frozen immediately before the one-time model evaluation.

The [locked confirmation results](docs/CONFIRMATION_RESULTS.md) report the
two-day no-refit result, permutation and timing controls, passed compound
decision, execution audit, and strict construct-validity interpretation.

## Repository map

```text
configs/                 Frozen dataset and experiment specifications
data/                    Local data only; raw and derived data are ignored
docs/                    Charter, provenance, decisions, and result reports
figures/                 Regenerable figures; ignored except for metadata
notebooks/               Exploration only; no confirmatory analysis
results/                 Regenerable outputs; ignored except for metadata
scripts/                 Thin executable entry points
src/japaneeg_audit/      Reusable analysis code
tests/                   Unit, leakage, and construct-validity tests
upstream/                External code checkouts; ignored and pinned in configs
```

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
```

No raw participant data, pretrained weights, credentials, or generated results
are committed to this repository.
