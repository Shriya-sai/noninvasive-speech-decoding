# Temporal ridge development results

Status: prespecified calibration gate passed; not confirmation

Date: 2026-09-07

## Scope

The analysis used only the 2,181 calibration windows from 12 recording days.
Every outer day was held out while feature scaling, 128-component PCA, target
scaling, ridge fitting, and alpha selection were performed within the remaining
days. The synchronized validation day, consumed test days, and three reserved
confirmation days were not used.

## Primary result

| Condition | Top-1 macro | Top-10 macro | MRR macro |
| --- | ---: | ---: | ---: |
| Contemporaneous temporal EEG | 2.34% | 16.28% | 0.0759 |
| Candidate/session reference | 0.78% | 7.84% | 0.0408 |
| Time-reversed held-out EEG | 1.49% | 8.55% | 0.0486 |

Eleven of 12 outer days exceeded their exact candidate-count reference MRR.
Selected alpha remained heterogeneous: all six grid values were selected at
least once, with alpha 100 selected four times and 1000 three times. The daywise
consistency supports proceeding, while the hyperparameter variation remains a
warning about acquisition shift.

## Temporal controls

The contemporaneous model was applied to circularly shifted held-out EEG bins
without refitting:

| Held-out EEG perturbation | MRR macro |
| --- | ---: |
| -1000 ms | 0.0449 |
| -500 ms | 0.0562 |
| none | 0.0759 |
| +500 ms | 0.0498 |
| +1000 ms | 0.0430 |
| time reversal | 0.0486 |

The peak at the declared alignment is compatible with temporally specific
information. These circular perturbations are diagnostics, not estimates of a
physiological neural latency.

## Pairing null

Ninety-nine held-out, within-day target-row permutations were generated from
the frozen seed stream after each fold model was fitted. Null macro-MRR ranged
from 0.0327 to 0.0464; its 95th percentile was 0.0456. The observed 0.0759
exceeded every permutation, giving a plus-one empirical p-value of 0.01, the
smallest attainable value with 99 permutations.

## Direct-acoustic control

The nested 20-bin vocal-audio RMS-envelope model achieved macro top-1 58.24%,
top-10 79.26%, and MRR 0.6539. This confirms that the temporally resolved
log-mel target is strongly determined by its source audio and that temporal
alignment matters. It is not a fair neural benchmark or evidence that the EEG
effect is cortical; instead it establishes the scale of directly available
acoustic information.

## Gate decision

All three frozen development checks pass:

1. at least nine calibration days above candidate reference: 11/12;
2. primary MRR above the pairing-null 95th percentile: 0.0759 > 0.0456;
3. primary MRR above time reversal: 0.0759 > 0.0486.

This permits a one-time validation and, if the complete pipeline is then
locked, mechanical download of the three reserved confirmation runs. It does
not permit changing temporal bins, PCA dimension, lag controls, target,
artifact policy, or endpoints in response to validation or confirmation.

## Interpretation boundary

The result demonstrates cross-day predictability in coarse temporal EEG
statistics within the calibration era. It does not identify the predictive
source. Broadband RMS and gradient features can contain cortical activity,
facial/cranial EMG, electrode motion, and acoustic vibration. EMG and spatial
controls remain necessary before any neural speech-decoding claim.

The full generated JSON remains local. SHA-256:
`4bc2bb81e8f422569ea98cbda24a566aebcd85a0dadd392ab87985ee24cae418`.
