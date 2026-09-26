# R19 complete tables

Quality is authored parser accuracy, Hotpot full-answer F1, or adapted SQuAD F1.
Calls are standalone logical requests; benefit-gate requests were executed physically first.
No cross-domain quality average is reported.

## synthetic · 288 test inputs

| Arm | Quality % | Calls | Active interventions | Mean uncached seconds* | Tokens | Capped |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| native | 26.74 | 0 | 0 | 0.623 | 6047 | 103 |
| relevance | 27.78 | 288 | 266 | 1.157 | 6211 | 122 |
| sufficiency | 41.67 | 288 | 91 | 1.086 | 5919 | 92 |
| dual | 43.06 | 288 | 241 | 1.133 | 6028 | 106 |
| benefit_gate | 39.24 | 222 | 182 | 1.032 | 6074 | 105 |
| random_gate | 32.99 | 133 | 117 | 0.858 | 6007 | 101 |
| r18_gate | 36.81 | 223 | 182 | 1.024 | 6102 | 109 |

Primary differences (percentage points), individual 99.1667% intervals:

- Dual minus relevance: **+15.28 [+9.38, +21.88]**.
- Benefit-gate routing value above expected random at the same call count: **-0.08 [-3.79, +3.92]**.

Exploratory differences, ordinary 95% intervals:

- relevance_minus_native: +1.04 [-3.82, +5.90].
- dual_minus_native: +16.32 [+10.07, +22.57].
- sufficiency_minus_native: +14.93 [+10.42, +19.79].
- benefit_gate_minus_native: +12.50 [+7.64, +17.71].
- benefit_gate_minus_dual: -3.82 [-7.29, -0.35].
- benefit_gate_minus_r18_gate: +2.43 [-0.69, +5.56].

| Arm | Answerable count / score % | Missing-evidence count / score % |
| --- | ---: | ---: |
| native | 144 / 49.31 | 144 / 4.17 |
| relevance | 144 / 50.69 | 144 / 4.86 |
| sufficiency | 144 / 49.31 | 144 / 34.03 |
| dual | 144 / 52.08 | 144 / 34.03 |
| benefit_gate | 144 / 54.17 | 144 / 24.31 |
| random_gate | 144 / 49.31 | 144 / 16.67 |
| r18_gate | 144 / 49.31 | 144 / 24.31 |

Separate Jev sufficiency classification at 0.5: 253/288 correct against dataset answerability. This is not Granite answer accuracy.

## hotpot · 160 test inputs

| Arm | Quality % | Calls | Active interventions | Mean uncached seconds* | Tokens | Capped |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| native | 27.68 | 0 | 0 | 0.771 | 3063 | 38 |
| relevance | 32.97 | 160 | 157 | 1.209 | 2440 | 19 |
| sufficiency | 27.46 | 160 | 9 | 1.279 | 3068 | 38 |
| dual | 32.95 | 160 | 141 | 1.218 | 2515 | 21 |
| benefit_gate | 28.34 | 20 | 19 | 0.812 | 2997 | 37 |
| random_gate | 31.58 | 67 | 61 | 0.949 | 2797 | 32 |
| r18_gate | 28.59 | 24 | 20 | 0.829 | 2942 | 34 |

Primary differences (percentage points), individual 99.1667% intervals:

- Dual minus relevance: **-0.02 [-2.60, +2.57]**.
- Benefit-gate routing value above expected random at the same call count: **-0.00 [-2.29, +2.19]**.

Exploratory differences, ordinary 95% intervals:

- relevance_minus_native: +5.29 [+0.70, +9.96].
- dual_minus_native: +5.27 [+1.01, +9.66].
- sufficiency_minus_native: -0.22 [-0.61, +0.00].
- benefit_gate_minus_native: +0.65 [-1.14, +2.59].
- benefit_gate_minus_dual: -4.61 [-8.64, -0.75].
- benefit_gate_minus_r18_gate: -0.26 [-2.72, +2.12].

| Arm | Answerable count / score % | Missing-evidence count / score % |
| --- | ---: | ---: |
| native | 160 / 27.68 | 0 / n/a |
| relevance | 160 / 32.97 | 0 / n/a |
| sufficiency | 160 / 27.46 | 0 / n/a |
| dual | 160 / 32.95 | 0 / n/a |
| benefit_gate | 160 / 28.34 | 0 / n/a |
| random_gate | 160 / 31.58 | 0 / n/a |
| r18_gate | 160 / 28.59 | 0 / n/a |

Separate Jev sufficiency classification at 0.5: 143/160 correct against dataset answerability. This is not Granite answer accuracy.

## squad2 · 160 test inputs

| Arm | Quality % | Calls | Active interventions | Mean uncached seconds* | Tokens | Capped |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| native | 25.44 | 0 | 0 | 0.562 | 3047 | 23 |
| relevance | 27.66 | 160 | 105 | 0.972 | 2648 | 15 |
| sufficiency | 29.21 | 160 | 60 | 1.028 | 3028 | 22 |
| dual | 33.10 | 160 | 136 | 0.999 | 2716 | 15 |
| benefit_gate | 26.70 | 35 | 29 | 0.648 | 2987 | 20 |
| random_gate | 26.15 | 66 | 57 | 0.746 | 2947 | 20 |
| r18_gate | 25.37 | 10 | 8 | 0.591 | 3031 | 23 |

Primary differences (percentage points), individual 99.1667% intervals:

- Dual minus relevance: **+5.44 [-0.99, +12.51]**.
- Benefit-gate routing value above expected random at the same call count: **-0.41 [-3.68, +2.76]**.

Exploratory differences, ordinary 95% intervals:

- relevance_minus_native: +2.22 [-1.25, +5.57].
- dual_minus_native: +7.66 [+2.17, +13.10].
- sufficiency_minus_native: +3.77 [-1.12, +8.61].
- benefit_gate_minus_native: +1.26 [-1.63, +4.12].
- benefit_gate_minus_dual: -6.40 [-10.91, -1.99].
- benefit_gate_minus_r18_gate: +1.33 [-1.53, +4.18].

| Arm | Answerable count / score % | Missing-evidence count / score % |
| --- | ---: | ---: |
| native | 80 / 34.63 | 80 / 16.25 |
| relevance | 80 / 42.82 | 80 / 12.50 |
| sufficiency | 80 / 34.67 | 80 / 23.75 |
| dual | 80 / 42.46 | 80 / 23.75 |
| benefit_gate | 80 / 37.16 | 80 / 16.25 |
| random_gate | 80 / 36.04 | 80 / 16.25 |
| r18_gate | 80 / 34.49 | 80 / 16.25 |

| Arm | Raw EM % | Raw F1 % | Adapted F1 % |
| --- | ---: | ---: | ---: |
| native | 4.38 | 17.31 | 25.44 |
| relevance | 6.88 | 21.41 | 27.66 |
| sufficiency | 4.38 | 17.44 | 29.21 |
| dual | 6.88 | 21.33 | 33.10 |
| benefit_gate | 5.00 | 18.58 | 26.70 |
| random_gate | 5.00 | 18.13 | 26.15 |
| r18_gate | 4.38 | 17.24 | 25.37 |

Separate Jev sufficiency classification at 0.5: 141/160 correct against dataset answerability. This is not Granite answer accuracy.

*Benefit-gate elapsed time includes physical HTTP waits. Other guided arms may reuse
receipts; their uncached estimates add the original call duration. Serial FP32 L40S,
hosted Jev, no throughput or colocated serving claim.

## Separately registered static/shuffled controls

These are exploratory 95% comparisons registered during fitting, before test.
Static instruction requires no Jev. Shuffling reuses main receipts; it adds no paid calls.

| Domain | Control | Control score % | Dual minus control, pp [95% interval] |
| --- | --- | ---: | --- |
| synthetic | instruction_always | 46.53 | -3.47 [-10.42, +3.82] |
| synthetic | shuffled_sufficiency | 32.99 | +10.07 [+4.51, +15.97] |
| hotpot | instruction_always | 32.90 | +0.05 [-5.04, +4.98] |
| hotpot | shuffled_sufficiency | 32.60 | +0.35 [-2.35, +3.07] |
| squad2 | instruction_always | 34.49 | -1.39 [-6.02, +3.04] |
| squad2 | shuffled_sufficiency | 29.83 | +3.27 [-1.97, +8.27] |

One fixed permutation and the dual-calibrated instruction strength are used;
this is not a search for the strongest possible static intervention.
