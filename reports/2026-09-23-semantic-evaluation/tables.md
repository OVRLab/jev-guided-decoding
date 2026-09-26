# R20 results tables

All semantic scores use the frozen, admitted Qwen3-14B judge. Unresolved judgments count as incorrect in the lower score and correct in the upper score. These are automated judgments, not human-certified accuracy.

## Primary correctness

| Domain | Arm | Correct / inputs | Unresolved | Lower–upper (%) |
| --- | --- | ---: | ---: | ---: |
| Authored | Native Granite | 87 / 288 | 0 | 30.21–30.21 |
| Authored | Static instruction | 129 / 288 | 0 | 44.79–44.79 |
| Authored | Granite + Jev | 123 / 288 | 0 | 42.71–42.71 |
| HotpotQA | Native Granite | 89 / 120 | 0 | 74.17–74.17 |
| HotpotQA | Static instruction | 81 / 120 | 0 | 67.50–67.50 |
| HotpotQA | Granite + Jev | 88 / 120 | 0 | 73.33–73.33 |
| SQuAD2 | Native Granite | 74 / 120 | 0 | 61.67–61.67 |
| SQuAD2 | Static instruction | 84 / 120 | 0 | 70.00–70.00 |
| SQuAD2 | Granite + Jev | 81 / 120 | 0 | 67.50–67.50 |

## Six registered paired comparisons

Each interval uses 10,000 cluster bootstrap draws and 99.1667% nominal coverage; together the six comparisons target nominal 95% family coverage within R20. Effects are percentage points. There is no all-controls conjunction or pooled score.

| Domain | Dual minus | Difference (pp) | Primary interval (pp) | Clusters |
| --- | --- | ---: | ---: | ---: |
| Authored | Native Granite | +12.50 | [+4.17, +21.18] | 144 |
| Authored | Static instruction | -2.08 | [-10.42, +6.37] | 144 |
| HotpotQA | Native Granite | -0.83 | [-10.28, +8.33] | 120 |
| HotpotQA | Static instruction | +5.83 | [-5.00, +16.67] | 120 |
| SQuAD2 | Native Granite | +5.83 | [-1.70, +13.91] | 93 |
| SQuAD2 | Static instruction | -2.50 | [-8.65, +3.25] | 93 |

## Answerability groups (descriptive)

These groups were registered descriptively, not as additional primary endpoints. Wrong answerable responses include false refusals as well as wrong or incomplete answers; the binary grader does not provide a separately validated refusal taxonomy.

| Domain | Evidence | Arm | Correct / inputs | Lower–upper (%) |
| --- | --- | --- | ---: | ---: |
| Authored | Answerable | Native Granite | 67 / 144 | 46.53–46.53 |
| Authored | Answerable | Static instruction | 45 / 144 | 31.25–31.25 |
| Authored | Answerable | Granite + Jev | 64 / 144 | 44.44–44.44 |
| Authored | Missing | Native Granite | 20 / 144 | 13.89–13.89 |
| Authored | Missing | Static instruction | 84 / 144 | 58.33–58.33 |
| Authored | Missing | Granite + Jev | 59 / 144 | 40.97–40.97 |
| HotpotQA | Answerable | Native Granite | 89 / 120 | 74.17–74.17 |
| HotpotQA | Answerable | Static instruction | 81 / 120 | 67.50–67.50 |
| HotpotQA | Answerable | Granite + Jev | 88 / 120 | 73.33–73.33 |
| SQuAD2 | Answerable | Native Granite | 54 / 60 | 90.00–90.00 |
| SQuAD2 | Answerable | Static instruction | 52 / 60 | 86.67–86.67 |
| SQuAD2 | Answerable | Granite + Jev | 53 / 60 | 88.33–88.33 |
| SQuAD2 | Missing | Native Granite | 20 / 60 | 33.33–33.33 |
| SQuAD2 | Missing | Static instruction | 32 / 60 | 53.33–53.33 |
| SQuAD2 | Missing | Granite + Jev | 28 / 60 | 46.67–46.67 |

## Historical scoring on these same outputs

Authored uses the inherited abstention/answer parser; Hotpot uses answer F1; SQuAD uses the inherited adapted answer/abstention F1. These different score types are not substitutes for the semantic endpoint. The last column counts cases where full lexical credit (exactly 1.0) differs from a valid semantic Boolean; it is not a lexical error rate, since partial F1 is not a Boolean judgment.

| Domain | Arm | Legacy mean (%) | Full-credit/semantic disagreements |
| --- | --- | ---: | ---: |
| Authored | Native Granite | 29.86 | 31 |
| Authored | Static instruction | 45.83 | 21 |
| Authored | Granite + Jev | 47.92 | 45 |
| HotpotQA | Native Granite | 28.10 | 78 |
| HotpotQA | Static instruction | 34.99 | 61 |
| HotpotQA | Granite + Jev | 29.69 | 72 |
| SQuAD2 | Native Granite | 23.49 | 62 |
| SQuAD2 | Static instruction | 29.04 | 64 |
| SQuAD2 | Granite + Jev | 29.51 | 60 |

## Measured generation work (descriptive)

One serial L40S study with hosted Jev; these are instrumented per-answer timings, excluding checkpoint download/loading, admission and independent judging. Arm order was randomized within input. Different answer lengths change elapsed work. This is not optimized serving throughput or a measurement of colocated Jev.

| Arm | Final tokens | Mean tokens | Token-cap stops | Mean wall seconds | Median wall seconds | Mean Jev wait seconds | Physical requests |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Native Granite | 10494 | 19.88 | 134 | 0.629 | 0.577 | 0.000 | 0 |
| Static instruction | 9716 | 18.40 | 102 | 0.645 | 0.574 | 0.000 | 0 |
| Granite + Jev | 9902 | 18.75 | 127 | 1.017 | 0.985 | 0.370 | 528 |

## Jev intervention actions

These are realized policy actions, not causal estimates within the selected groups. A relevance decision with uniform source choices may apply no bias. Instruction attention and relevance attention affect the registered eleven heads; Jev does not select final tokens.

| Domain | Relevance decision | Abstention instruction | Other/native action | Actual nonempty bias |
| --- | ---: | ---: | ---: | ---: |
| Authored | 140 | 97 | 51 | 236 |
| HotpotQA | 100 | 8 | 12 | 108 |
| SQuAD2 | 65 | 45 | 10 | 107 |

For unresolved-judgment contrast sensitivities and exact values, see [independent-analysis.json](independent-analysis.json). All primary values come from that audit; work and policy counts come from its verified raw generation records.
