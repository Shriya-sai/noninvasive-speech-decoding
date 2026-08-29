# Project charter

## Central question

Does open-vocabulary speech-decoding performance scale with EEG recording
duration because models learn increasingly stable neural representations, or
because they increasingly exploit participant-, session-, device-, acoustic-,
and articulation-specific signals?

## Anchor result

Sato et al. (2024) reported a strong scaling effect for contrastive retrieval
from approximately 175 hours of overt-speech EEG recorded from one participant.
The first stage will reproduce that analysis as closely as the released data and
methods permit. Reproduction results will not be treated as confirmation.

## Primary confirmation

The primary confirmatory analysis will preserve recording sessions as the
independence unit, prevent overlapping or adjacent windows from crossing data
partitions, audit lexical overlap, and compare EEG against matched EMG and
metadata baselines.

## Competing accounts

1. Stable neural representation: performance survives session holdout, EMG
   control, spatial restriction, and pre-articulation evaluation.
2. Myogenic/acoustic information: EMG or peripheral channels explain most
   performance and accuracy is concentrated during articulation.
3. Session learning: random-window accuracy collapses under held-out days.
4. Lexical familiarity: accuracy depends on repeated phrases or acoustic
   similarity rather than transferable speech representations.

## Claim boundaries

The dataset supports intensive participant-specific learning. It does not
support population-level claims: there are three participants, and the released
hours and events are repeated measurements nested within them.

## Initial gates

1. Reconstruct participant, device, task, session, and event coverage.
2. Reconstruct the original data split and candidate-set procedure.
3. Verify synchronization and recover planted synthetic signals.
4. Verify null performance before large-scale training.
5. Freeze the confirmation specification before inspecting its results.
