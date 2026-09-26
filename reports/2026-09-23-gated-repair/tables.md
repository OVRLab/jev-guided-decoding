# R25 audited result tables

Two-domain pilot; these are not official full-task or ten-suite scores. Branch seed means average the same cases across two fitted adapters, so correct counts can be fractional.

## Primary full-repair outcomes

| Arm | GSM8K (96) | ARC-Challenge (96) | Combined (192) |
| --- | --- | --- | --- |
| Original Granite | 45/96 (46.88%) | 69/96 (71.88%) | 114/192 (59.38%) |
| Blind repair | 44/96 (45.83%) | 31/96 (32.29%) | 75/192 (39.06%) |
| Jev text repair | 43/96 (44.79%) | 30/96 (31.25%) | 73/192 (38.02%) |
| constant/2501 | 42/96 (43.75%) | 62/96 (64.58%) | 104/192 (54.17%) |
| constant/2502 | 43/96 (44.79%) | 65/96 (67.71%) | 108/192 (56.25%) |
| Constant branch (seed mean) | 42.5/96 (44.27%) | 63.5/96 (66.15%) | 106/192 (55.21%) |
| live/2501 | 45/96 (46.88%) | 43/96 (44.79%) | 88/192 (45.83%) |
| live/2502 | 45/96 (46.88%) | 39/96 (40.62%) | 84/192 (43.75%) |
| Live Jev branch (seed mean) | 45/96 (46.88%) | 41/96 (42.71%) | 86/192 (44.79%) |
| shuffled/2501 | 45/96 (46.88%) | 30/96 (31.25%) | 75/192 (39.06%) |
| shuffled/2502 | 47/96 (48.96%) | 31/96 (32.29%) | 78/192 (40.62%) |
| Shuffled Jev (seed mean) | 46/96 (47.92%) | 30.5/96 (31.77%) | 76.5/192 (39.84%) |
| inverted/2501 | 18/96 (18.75%) | 13/96 (13.54%) | 31/192 (16.15%) |
| inverted/2502 | 34/96 (35.42%) | 29/96 (30.21%) | 63/192 (32.81%) |
| Inverted Jev (seed mean) | 26/96 (27.08%) | 21/96 (21.88%) | 47/192 (24.48%) |

## Paired effects

Percentage-point difference with individual 95% task-stratified bootstrap intervals; conditional on the two fitted seeds, not a simultaneous family guarantee.

| Contrast | GSM8K | ARC-Challenge | Combined |
| --- | --- | --- | --- |
| live_mean-vs-native | +0.00 [-3.12, +3.12] | -29.17 [-42.71, -15.10] | -14.58 [-21.61, -7.29] |
| live_mean-vs-constant_mean | +2.60 [-3.12, +8.33] | -23.44 [-35.94, -10.42] | -10.42 [-17.19, -3.39] |
| live_mean-vs-blind | +1.04 [-1.04, +3.65] | +10.42 [+0.52, +20.31] | +5.73 [+0.52, +10.94] |
| live_mean-vs-text | +2.08 [-2.08, +6.77] | +11.46 [+0.52, +22.40] | +6.77 [+1.04, +12.76] |
| live_mean-vs-shuffled_mean | -1.04 [-4.69, +2.08] | +10.94 [+0.00, +21.88] | +4.95 [-0.78, +10.68] |
| live_mean-vs-inverted_mean | +19.79 [+10.94, +29.17] | +20.83 [+8.85, +32.81] | +20.31 [+12.76, +27.86] |
| blind-vs-native | -1.04 [-4.17, +2.08] | -39.58 [-50.00, -29.17] | -20.31 [-25.52, -15.10] |
| text-vs-native | -2.08 [-5.21, +0.00] | -40.62 [-51.04, -30.21] | -21.35 [-26.56, -16.15] |

## Recovery and damage

Relative to the native draft. Recovered/damaged counts average the two seeds where applicable. All planned test cases remain included.

| Domain | Arm | Recovered native errors | Damaged native correct | Unparseable final | Length stops |
| --- | --- | --- | --- | --- | --- |
| gsm8k | Blind repair | 1/51 | 2/45 | 35 | 1 |
| gsm8k | Jev text repair | 0/51 | 2/45 | 37 | 0 |
| gsm8k | Constant branch (seed mean) | 3.5/51 | 6/45 | 34.5 | 1 |
| gsm8k | Live Jev branch (seed mean) | 1.5/51 | 1.5/45 | 34.5 | 0 |
| gsm8k | Shuffled Jev (seed mean) | 3/51 | 2/45 | 33.5 | 1 |
| gsm8k | Inverted Jev (seed mean) | 5/51 | 24/45 | 39 | 1 |
| arc | Blind repair | 1/27 | 39/69 | 54 | 0 |
| arc | Jev text repair | 1/27 | 40/69 | 60 | 0 |
| arc | Constant branch (seed mean) | 4.5/27 | 10/69 | 2.5 | 0 |
| arc | Live Jev branch (seed mean) | 14/27 | 42/69 | 41 | 0 |
| arc | Shuffled Jev (seed mean) | 4/27 | 42.5/69 | 41 | 0 |
| arc | Inverted Jev (seed mean) | 2/27 | 50/69 | 17 | 0 |
| all | Blind repair | 2/78 | 41/114 | 89 | 1 |
| all | Jev text repair | 1/78 | 42/114 | 97 | 0 |
| all | Constant branch (seed mean) | 8/78 | 16/114 | 37 | 1 |
| all | Live Jev branch (seed mean) | 15.5/78 | 43.5/114 | 75.5 | 0 |
| all | Shuffled Jev (seed mean) | 7/78 | 44.5/114 | 74.5 | 1 |
| all | Inverted Jev (seed mean) | 7/78 | 74/114 | 56 | 1 |

## Registered retention replay

Native is retained when valid Jev p(correct) is at least 0.5 or feedback is unavailable; otherwise use the corresponding repair. This is offline replay: every model branch was actually executed and no skipped execution is measured.

| Policy | GSM8K | ARC-Challenge | Combined |
| --- | --- | --- | --- |
| native | 46.88% | 71.88% | 59.38% |
| retained_blind | 46.88% | 71.88% | 59.38% |
| retained_text | 46.88% | 71.88% | 59.38% |
| retained_constant_mean | 47.92% | 76.04% | 61.98% |
| retained_live_mean | 46.88% | 86.46% | 66.67% |

| Retained live contrast | GSM8K | ARC-Challenge | Combined |
| --- | --- | --- | --- |
| live-vs-native | +0.00 [+0.00, +0.00] | +14.58 [+8.33, +21.88] | +7.29 [+4.17, +10.94] |
| live-vs-retained_constant_mean | -1.04 [-2.60, +0.00] | +10.42 [+5.21, +16.67] | +4.69 [+1.82, +7.81] |
| live-vs-retained_blind | +0.00 [+0.00, +0.00] | +14.58 [+7.29, +22.40] | +7.29 [+3.65, +11.20] |
| live-vs-retained_text | +0.00 [+0.00, +0.00] | +14.58 [+7.29, +22.40] | +7.29 [+3.65, +11.20] |

## Actual model generation work

Seed means for learned arms; measured serial generation time includes model prefill/generation but excludes API, training and loading. A deployed two-pass arm needs its native draft plus repair; the experiment shared drafts but executed every repair. Retention does not remove that actual experimental work.

| Arm | Native seconds/case | Repair seconds/case | Sum of model seconds/case | Repair processed tokens/case | Repair generated tokens/case |
| --- | --- | --- | --- | --- | --- |
| Blind repair | 3.901 | 2.653 | 6.554 | 383.1 | 87.0 |
| Jev text repair | 3.901 | 2.139 | 6.039 | 383.9 | 69.8 |
| Constant branch (seed mean) | 3.901 | 1.694 | 5.594 | 350.1 | 54.0 |
| Live Jev branch (seed mean) | 3.901 | 2.059 | 5.959 | 361.6 | 65.5 |
| Shuffled Jev (seed mean) | 3.901 | 2.161 | 6.061 | 365.0 | 68.9 |
| Inverted Jev (seed mean) | 3.901 | 0.674 | 4.575 | 317.3 | 21.2 |

See the raw outcomes for individual token IDs, timing, prompts and checkpoints; the cost report includes all cloud lifetime and conservatively charged API attempts. No throughput or colocated-Jev claim follows from these serial timings.
