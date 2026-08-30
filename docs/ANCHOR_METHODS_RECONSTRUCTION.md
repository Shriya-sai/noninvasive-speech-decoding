# Anchor-paper methods reconstruction

Status: primary-source reconstruction, before signal download
Audit date: 2026-08-30
Anchor: Sato et al. (2024), arXiv:2407.07595

## Purpose

This document reconstructs the protocol behind the reported 175-hour
speech-decoding scaling result. It separates:

- **reported** details stated in the paper;
- **figure-derived** details visible in the architecture diagram;
- **unresolved** details that are necessary for an exact reproduction but are
  not uniquely specified;
- **audit additions** that belong to this project rather than the original
  analysis.

No unspecified choice below should be silently filled with a conventional
default and then labeled paper-matched.

## Scientific claim and endpoints

The anchor paper claims that participant-specific open-vocabulary EEG speech
retrieval improves strongly with more training data. With the complete dataset,
the reported wav2vec2.0 condition achieved:

- top-1 accuracy: 48.5% among 512 candidates;
- top-10 accuracy: 76.0% among 512 candidates;
- nominal chance: 0.195% top-1 and 1.953% top-10.

The paper fitted power functions of accuracy against training duration and
reported no visible saturation. The same test set was used at every training
size.

## Participant and recording

### Reported

- One healthy male adult without neurological or psychiatric illness.
- Overt, natural-paced continuous reading of text corpora, novels, and
  text-based games displayed on a computer.
- Forty-eight recording days and 175 total recording hours.
- Eight 16-electrode g.Pangolin sheets, giving 128 EEG electrodes concentrated
  around left-hemisphere language and premotor regions.
- Simultaneous EOG, upper-orbicularis-oris EMG, lower-orbicularis-oris EMG, and
  speech audio.
- EEG acquisition at 1,200 Hz through the g.NEEDaccess Python API.
- Audio acquisition at 48 kHz.

### Release mapping

The matching released condition is expected to lie within
`sub-01`/`speechopen`/`acq-pangolin`, but the OpenNeuro release contains 104
recording days and 372 runs in that condition. The exact 48 paper days remain
unresolved.

## Signal preprocessing

### Reported in text

1. Denoising with MNE-Python.
2. Adaptive removal of EEG components linearly predictable from EOG and upper-
   and lower-lip EMG.
3. Audio downsampling from 48 kHz to 16 kHz.
4. Silero voice-activity detection.
5. EEG/audio timestamp synchronization.
6. Non-overlapping five-second epoching.
7. Per-window EEG z-scoring along time.
8. Clipping standardized EEG to [-5, 5].
9. Exclusion of windows containing less than 20% detected speech.

### Figure-derived order and parameters

The architecture figure shows this EEG order:

1. 50 Hz notch filter;
2. common-average reference;
3. 2-120 Hz band-pass filter;
4. resampling to 240 Hz;
5. normalized least-mean-square adaptive filter;
6. epoching;
7. z-score normalization;
8. clipping to [-5, 5].

The appendix reports NLMS adaptation coefficient `0.1` and epsilon `0.001`,
using `padasip` as the implementation basis.

### Unresolved

- MNE version and exact filter design, transition bandwidths, phase, padding,
  and notch implementation.
- Whether the 2-120 Hz filter was applied before resampling exactly as depicted;
  120 Hz is the Nyquist frequency after resampling to 240 Hz.
- Common-average channel inclusion/exclusion rules.
- Bad-channel detection and interpolation.
- How non-EEG channels were scaled before NLMS.
- NLMS initialization, reset boundaries, tap structure, and whether fitting was
  continuous, per run, or per window.
- Exact audio/EEG synchronization method and measured residual timing error.
- Silero model version, threshold, chunking, and post-processing.
- Whether five-second windows were aligned to run onset, audio onset, or a
  corrected common clock.
- Treatment of incomplete final windows.
- Whether z-scoring used every time point or only detected speech intervals.

These choices can materially change both retained hours and apparent EMG
suppression.

## Data partitioning

### Reported

The English methods state that data were divided chronologically into the first
80% for training, the next 10% for validation, and the final 10% for testing.
The model checkpoint with minimum validation loss was evaluated on the test
set. The test set was held constant across scaling conditions.

### Unresolved and consequential

The paper does not state whether chronological partitioning occurred:

1. once across the complete multi-day timeline;
2. separately within each recording day;
3. separately within each run/session;
4. after concatenating only VAD-retained windows;
5. or before window rejection.

These alternatives test different forms of generalization. A global split can
hold out later days, whereas a within-run split places temporally adjacent
windows from every run in all partitions.

The manuscript source contains a non-rendered drafting comment describing an
80/10/10 division from the beginning of each session. Because it is not part of
the rendered methods and conflicts with the English description, it is evidence
of ambiguity, not sufficient evidence to select the within-session scheme.

The split supplied with the earlier Harvard Dataverse deposit, if still
available, or author-released code/configuration is needed to resolve this.

## Training-set scaling

### Reported

- Every scaling model used a common fixed test set.
- Training duration was measured as total retained segment length.
- The appendix identifies a `1/32` condition as 2.89 training hours, implying
  approximately 92.5 retained hours at the full training fraction.
- Accuracy and loss were plotted against dataset size on logarithmic axes.

### Figure-derived

The scaling figure contains multiple approximately geometric training sizes
from roughly 1.5 to 92 hours. The exact subset fractions, window-selection
procedure, and nesting are not enumerated in the text.

### Unresolved

- Exact training fractions other than `1/32` and full.
- Whether smaller sets were strict nested prefixes, random subsets, complete
  days, or window samples.
- Whether more than one data subset was evaluated per duration.
- Whether more than one model initialization was trained per duration.
- Whether training epochs were held at 300 for all fractions, causing much less
  total optimization for smaller sets but repeated exposure per example.
- Whether word overlap was measured before or after Japanese token filtering.

The original scaling analysis necessarily co-varies hours, vocabulary coverage,
number of recording days, source material, and possibly optimization steps.

## EEG encoder

### Reported

The EEG encoder combines HTNet-style operations with Conformer blocks. The
audio encoder is frozen. Three audio encoders were compared: wav2vec2.0,
Whisper encoder, and Encodec. Wav2vec2.0 produced the strongest reported
retrieval result.

### Figure-derived architecture

For preprocessed input shaped `(batch, 1, channels, time)`:

1. temporal convolution with kernel 60 samples, corresponding to 250 ms at
   240 Hz, followed by group normalization;
2. Hilbert transform;
3. dilated spatial convolution with kernel 8 and dilation 16, followed by group
   normalization;
4. spatial convolution with kernel 16, followed by group normalization;
5. a Conformer stack marked `x11`, with the box also labeled `n_layers=8` and
   kernel 9;
6. temporal convolution and group normalization to match target time steps;
7. pointwise convolution to match target feature dimension.

### Unresolved

- Exact wav2vec2.0 checkpoint and software version.
- Which wav2vec layers were used and how their representations were combined.
- Whether time-varying latent maps were pooled before CLIP similarity and how.
- All feature widths (`F1`, `F2`, `F*`) and output time dimension.
- Padding, stride, bias, activation, dropout, and group counts.
- Meaning of the simultaneous `x11` and `n_layers=8` Conformer annotations.
- Conformer heads, feed-forward width, convolution expansion, normalization,
  residual scaling, and positional encoding.
- Weight initialization and random seeds.
- Whether the contrastive objective was EEG-to-audio only, symmetric, or used a
  learnable temperature. The displayed equation is one-directional and shows no
  temperature.

The paper figure and prose are insufficient to implement an exact encoder.

## Optimization

### Reported wav2vec2.0 condition

- Randomly initialized EEG encoder.
- Frozen audio encoder.
- 300 epochs.
- Batch size 512.
- LAMB optimizer.
- Initial learning rate 0.001.
- Weight decay 0.01.
- Cosine-annealing schedule.
- 1,000 warm-up iterations, described as 7.8 epochs.
- Lowest validation-loss checkpoint selected.
- Distributed data-parallel training on four 80 GB NVIDIA A100 GPUs.
- Approximately 40 hours for one full-data EEG-encoder training run.

### Unresolved

- LAMB implementation and remaining optimizer parameters.
- Mixed precision and gradient scaling.
- Effective global versus per-GPU batch size.
- Distributed sampler behavior and handling of incomplete batches.
- Gradient clipping and accumulation.
- Cosine schedule endpoint and whether warm-up is included in 300 epochs.
- Validation frequency and early-stopping behavior beyond checkpoint selection.
- Deterministic settings and seeds.

## Retrieval evaluation

### Reported

For a batch of 512 test examples, the paper computes all pairwise cosine
similarities between predicted EEG latents and recorded-audio latents. A query
is correct at top-k when its paired audio segment appears in its k nearest audio
candidates. Results are averaged over 16 batches of 512 test samples and
reported as mean plus or minus one standard deviation.

### Consequences

- The reported variability is across candidate batches, not across independent
  participants, recording days, model initializations, or data subsets.
- Candidate composition directly affects difficulty.
- Adjacent five-second windows can be easy negatives or encode shared session
  structure depending on construction.
- Sixteen batches account for 8,192 examples, while the speech-reconstruction
  analysis reports 8,448 test examples; the handling of the remaining 256
  examples is unspecified.

### Unresolved

- Whether batches were sequential, shuffled once, or repeatedly sampled.
- Whether candidates were drawn with replacement across batches.
- Whether nearby windows, same-source passages, and near-duplicate phrases were
  allowed as candidates.
- How latent time axes were reduced to a cosine-similarity score.
- Whether the same 16 candidate batches were used for every model.
- Whether evaluation preprocessing was fitted only on training data.

## EMG analysis

### Reported

The paper first applies NLMS removal of signals linearly predicted by EOG and
upper/lower lip EMG. It then trains augmentation conditions in which a signal
from a different segment is mixed into EEG:

`X = (1 - alpha) * EEG + alpha * EMG`, with `alpha` sampled from `[0, 0.95]`.

Separate augmentation models used EOG, upper-lip EMG, lower-lip EMG, or their
mean. At inference, EEG or replicated EMG was fed into the EEG encoder. The
unaugmented model achieved above-chance retrieval from EMG; augmented models
reduced EMG-input top-10 performance to roughly 3% while retaining approximately
69-72% EEG-input top-10 accuracy.

### What this establishes

The augmentation makes the trained representation less useful when the measured
EMG channel itself is substituted for EEG. It is evidence against exclusive
dependence on those specific EMG traces.

### What it does not establish

It does not prove that retained EEG information is cortical because:

- scalp myogenic activity may not be captured fully by three reference traces;
- propagation from muscle to scalp electrodes is spatially heterogeneous;
- the synthetic mixing distribution may differ from real contamination;
- electrode movement and acoustic vibration are not exhausted by lip EMG;
- neural, motor, and acoustic information are naturally correlated during overt
  speech;
- an encoder may reject substituted EMG yet retain correlated residual artifact
  embedded in EEG channels.

Our audit therefore needs EMG-only models, incremental EEG-beyond-EMG tests,
spatial controls, timing relative to EMG onset, and covert-speech transfer.

## Code and data availability

The paper states that analysis-ready train/validation/test data were uploaded to
a private Harvard Dataverse link and that code would be made public. Current
web and GitHub searches did not identify an author-maintained public training
repository.

The OpenNeuro release includes raw BIDS data, ingestion/preprocessing assets,
and provenance manifests, but its tagged tree does not contain the paper's
training and evaluation implementation despite the top-level README describing
such directories. Several released code paths are git-annex links.

A third-party Hugging Face derivative and training implementation exist, but
they are not authoritative evidence of the original protocol. They may be used
as an independent implementation reference only after provenance review.

## Reproduction classification

An **exact computational reproduction is not yet possible** from the published
paper alone because the exact 48-day subset, split mapping, architecture,
audio-embedding construction, candidate batching, and scaling-subset procedure
are unresolved.

The appropriate staged labels are:

1. **Paper-matched reconstruction:** implement every reported detail and mark
   each unresolved choice.
2. **Result reproduction:** attempt to recover the reported random/chronological
   retrieval curve after resolving the released split.
3. **Controlled conceptual replication:** use a fully specified session-held-out
   protocol on the public release.
4. **Novel mechanistic audit:** test neural, myogenic, acoustic, lexical, device,
   and session accounts.

## Immediate resolution actions

1. Inspect the tagged OpenNeuro metadata and git-annex preprocessing assets on a
   minimal clone.
2. Determine whether the earlier Dataverse release now has a public DOI or
   accessible metadata record without relying on an embedded private token.
3. Inspect author profiles and the dataset paper for a superseding code URL.
4. Compare run dates and retained durations with the reported 48-day/175-hour
   sample.
5. Prepare a concise author query covering only ambiguities that cannot be
   resolved from released assets.

## Gate decision

Proceed to a metadata-only clone and minimal two-run pilot. Do not freeze an
"exact reproduction" configuration or begin full-scale training yet.
