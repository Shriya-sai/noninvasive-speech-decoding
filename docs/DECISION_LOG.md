# Decision log

## 2026-09-04 — Temporal ridge protocol frozen

- Froze 20 nonoverlapping 250 ms bins for EEG and acoustic targets before
  temporal feature extraction.
- Chose channel/bin log-RMS and log-gradient-RMS EEG features followed by 128
  training-fold-only PCA components and multi-output ridge regression.
- Required nested day-held-out fitting for standardization, PCA, target scaling,
  and alpha selection.
- Prespecified circular lag, time reversal, vocal-envelope, unseen-session, and
  99 within-run pairing-permutation controls.
- Prohibited access to the three reserved confirmation signals unless the
  calibration development gate passes; prohibited confirmation refitting.

## 2026-09-04 — Calibration-only resampling and confirmation reservation

- Reserved three post-test confirmation runs using chronology, completeness,
  annex byte size, and hash metadata only; signals were not downloaded.
- Ran nested leave-one-day-out ridge evaluation using only the 12 calibration
  days, with inner day-held-out alpha selection.
- After correcting normalization to refit inside every resampling fold,
  observed macro-MRR 0.0466 versus a candidate-count reference of 0.0408;
  foldwise alpha still ranged 1-1000.
- Classified the result as weak heterogeneous development evidence, not a
  contradiction of the held-out test null or a confirmatory result.
- Required the temporal-model specification to be frozen before inspecting the
  three reserved confirmation signals.

## 2026-09-04 — Held-out-day ridge baseline

- Selected ridge alpha 100 using only the synchronized validation day.
- Evaluated the two test days once with within-day candidate sets and
  day-macro reporting.
- Found EEG macro-MRR 0.0955, below the unseen-session intercept (0.1040) and
  all five within-run pairing permutations (0.1079-0.1221).
- Ran the frozen vocal-audio RMS-envelope control, which reached macro-MRR
  0.1122 but did not justify a neural interpretation.
- Classified the result as a diagnostic null rather than tuning a more complex
  model on the consumed test days.
- Reserved future model development for calibration/validation-only analyses;
  an upgraded confirmatory model requires newly untouched evaluation days.

## 2026-09-02 — Baseline feature extraction

- Froze all Welch, band, STFT, mel, flooring, and summary parameters in the
  baseline configuration before fitting a model.
- Extracted 768 EEG log-bandpower features and 160 vocal-audio log-mel summary
  features for all 2,453 eligible windows.
- Fitted featurewise normalization on the 2,181 calibration windows only and
  applied it unchanged to validation and test, preserving held-out shifts.
- Kept the 15.68 MiB derived feature artifact local and recorded its SHA-256;
  no participant arrays were added to Git.

## 2026-09-02 — Baseline modeling protocol

- Froze recording day as the baseline independence and uncertainty unit.
- Preserved the 12 calibration, two validation, and two test day assignments;
  preprocessing and fitting may use calibration days only.
- Made the synchronization gate mandatory. The known failing validation day
  remains in provenance but is ineligible for paired EEG/audio fitting.
- Replaced unstable global artifact exclusion with explicit clean/high-artifact
  sensitivity strata, retaining synchronized held-out days in the primary set.
- Chose a transparent ridge baseline from EEG log-bandpower to vocal-audio
  log-mel summaries before attempting a deep encoder.
- Required audio-envelope, session-metadata, and permuted-pairing controls and
  equally weighted day-level reporting.

## 2026-09-01 — Multi-day artifact calibration

- Froze ten timeline strata and selected the smallest complete run in each
  using annex metadata size only, before reading signal QC.
- Assigned the first six strata to calibration, the next two to validation,
  and the final two to test; downloaded and SHA-256 verified all 20 files.
- Generalized window bounds to support a verified -2.4 ms run-specific audio
  offset while preserving the EEG-anchored five-second grid.
- Kept the frozen synchronization gate: nine runs pass and one validation run
  fails at -281 ms despite strong envelope correlation.
- Rejected the initial pooled-window artifact thresholds. They overweighted a
  long, globally shifted calibration run, produced nonphysical bounds, and
  yielded strongly role-dependent rejection rates.
- Did not refit using validation or test QC. Threshold development now requires
  hierarchical, day-balanced calibration and additional calibration runs.

## 2026-08-31 — Preprocessing pilot

- Executed the continuous notch, common-average reference, band-pass, and
  resampling pipeline on both checksum-pinned EDFs.
- Confirmed all 128 retained windows yield finite `128 x 1200` arrays at 240 Hz.
- Kept NLMS disabled because the anchor methods do not specify a reproducible
  tap structure, signal scaling, initialization, or reset boundary.
- Recorded post-clipping dispersion as QC evidence; it reveals artifact-heavy
  channel/windows that require a frozen rejection or sensitivity rule before
  model training.
- Confirmed window-random, run-held-out, and day-held-out split construction
  contains no temporal overlap; the two-day pilot cannot supply an independent
  validation day.

## 2026-08-31 — Signal synchronization and window eligibility

- Accepted the BIDS event mapping at speech-envelope resolution after both
  pilot runs passed a preregistered median-correlation/residual timing gate.
- Did not interpret the monitor and WAV signals as sample-identical; analog
  monitor filtering and channel differences remain visible.
- Froze audit profile `audit_v1`: complete non-overlapping five-second windows
  anchored at EEG run time zero, with corresponding audio required in bounds.
- Froze Silero VAD 6.2.1 defaults at 16 kHz on vocal WAV channel 0 and retained
  windows with at least 20% detected speech.
- These are reproducible audit choices because the anchor paper leaves window
  origin, Silero version, channel selection, and VAD parameters unresolved.

## 2026-08-30 — Project rename

- Renamed the project from JapanEEG Speech-Decoding Audit to Non-Invasive
  Speech Decoding.
- The broader name reflects that JapanEEG is the primary dataset rather than
  the permanent boundary of the research program.
- Reproduction and construct-validity analyses remain central methods, without
  defining the project solely as an audit.

## 2026-08-29 — Repository initialization

- Chosen project name: JapanEEG Speech-Decoding Audit.
- Primary focus: distinguish neural scaling from myogenic, acoustic, session,
  device, and lexical explanations.
- Primary confirmation unit: held-out recording session or day.
- Random-window splitting is retained only for paper-matched reproduction.
- Raw data and generated outputs are excluded from version control.
- All experiment configurations remain `draft` until the data and methods audit
  is complete.
