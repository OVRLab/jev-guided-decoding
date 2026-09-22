# R18 complete descriptive and inferential tables

Generated from the [main audit](independent-analysis.json) and [bound output diagnostics](output-diagnostics.json). The [main report](README.md) interprets these values. Every test arm and failed outcome remains in its planned denominator. Metrics differ by domain.

## Development selection

The request ceiling is 50% over development inputs; equal-domain quality selects the rule. Actual test call fractions can differ. Each gate has its own feature family.

| Gate | Rule | Development quality (%) | Calls | Call fraction (%) |
| --- | --- | --- | --- | --- |
| boundary | {"direction": "le", "feature": "head_disagreement", "kind": "threshold", "threshold": 0.05478179526607767} | 27.24 | 118 | 45.38 |
| pilot | {"direction": "le", "feature": "copy_fraction", "kind": "threshold", "threshold": 0.8571428571428571} | 26.69 | 128 | 49.23 |

## Authored accuracy

The same 32-token, full-vocabulary answer instruction and original evidence are used in all nine arms.

| Arm | Cases | Quality (%) | EM/correct (%) | Raw F1 (%) | Calls (%) | Failed fallbacks | Mean model time (s) | Mean uncached elapsed estimate (s) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Granite | 504 | 26.98 | 26.98 | 5.30 | 0.00 | 0 | 0.6263 | 0.6280 |
| Always Jev | 504 | 31.94 | 31.94 | 6.05 | 100.00 | 0 | 0.7277 | 1.3144 |
| Boundary never | 504 | 26.98 | 26.98 | 5.30 | 0.00 | 0 | 0.6322 | 0.6347 |
| Boundary always | 504 | 31.94 | 31.94 | 6.05 | 100.00 | 0 | 0.7162 | 1.2939 |
| Boundary gate | 504 | 31.75 | 31.75 | 6.16 | 72.42 | 0 | 0.7099 | 1.1225 |
| Boundary random | 504 | 30.36 | 30.36 | 5.68 | 45.24 | 0 | 0.6720 | 0.9351 |
| Pilot gate | 504 | 28.17 | 28.17 | 5.63 | 55.16 | 0 | 0.8027 | 1.1428 |
| Lexical | 504 | 19.64 | 19.64 | 3.51 | 0.00 | 0 | 0.7731 | 0.7853 |
| Shuffled Jev | 504 | 16.87 | 16.87 | 3.08 | 100.00 | 0 | 0.7421 | 1.3290 |

Exploratory paired contrasts use 95% cluster bootstrap intervals.

| Comparison | Difference and 95% interval (pp) | Clusters |
| --- | --- | --- |
| Always Jev minus Granite | +4.96 [+1.59, +8.33] | 252 |
| Boundary gate minus Granite | +4.76 [+1.79, +7.94] | 252 |
| Boundary gate minus Always Jev | -0.20 [-1.98, +1.39] | 252 |
| Boundary gate minus Pilot gate | +3.57 [+1.19, +5.95] | 252 |
| Boundary gate minus Boundary random | +1.39 [-0.99, +3.77] | 252 |
| Always Jev minus Lexical | +12.30 [+8.73, +16.07] | 252 |
| Always Jev minus Shuffled Jev | +15.08 [+10.52, +19.64] | 252 |

The exploratory 3 pp loss-margin result is within the margin (lower interval bound -1.98 pp). This is not equivalence or a conjunctive success criterion.

## HotpotQA F1

The same 32-token, full-vocabulary answer instruction and original evidence are used in all nine arms.

| Arm | Cases | Quality (%) | EM/correct (%) | Raw F1 (%) | Calls (%) | Failed fallbacks | Mean model time (s) | Mean uncached elapsed estimate (s) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Granite | 240 | 27.96 | 11.67 | 27.96 | 0.00 | 0 | 0.7438 | 0.7455 |
| Always Jev | 240 | 29.40 | 12.92 | 29.40 | 100.00 | 0 | 0.8719 | 1.5016 |
| Boundary never | 240 | 27.96 | 11.67 | 27.96 | 0.00 | 0 | 0.7460 | 0.7486 |
| Boundary always | 240 | 29.40 | 12.92 | 29.40 | 100.00 | 0 | 0.6876 | 1.2944 |
| Boundary gate | 240 | 27.08 | 11.25 | 27.08 | 18.33 | 0 | 0.7266 | 0.8283 |
| Boundary random | 240 | 27.06 | 11.25 | 27.06 | 40.00 | 0 | 0.7159 | 0.9578 |
| Pilot gate | 240 | 30.21 | 13.33 | 30.21 | 33.75 | 0 | 0.8936 | 1.1123 |
| Lexical | 240 | 24.45 | 8.75 | 24.45 | 0.00 | 0 | 1.3778 | 1.4080 |
| Shuffled Jev | 240 | 17.27 | 6.25 | 17.27 | 100.00 | 0 | 0.9380 | 1.5687 |

Exploratory paired contrasts use 95% cluster bootstrap intervals.

| Comparison | Difference and 95% interval (pp) | Clusters |
| --- | --- | --- |
| Always Jev minus Granite | +1.45 [-2.24, +5.11] | 240 |
| Boundary gate minus Granite | -0.87 [-2.53, +0.61] | 240 |
| Boundary gate minus Always Jev | -2.32 [-5.62, +1.01] | 240 |
| Boundary gate minus Pilot gate | -3.13 [-5.53, -0.98] | 240 |
| Boundary gate minus Boundary random | +0.02 [-2.50, +2.54] | 240 |
| Always Jev minus Lexical | +4.95 [+1.77, +8.27] | 240 |
| Always Jev minus Shuffled Jev | +12.13 [+7.67, +16.69] | 240 |

The exploratory 3 pp loss-margin result is not established (lower interval bound -5.62 pp). This is not equivalence or a conjunctive success criterion.

## SQuAD2 adapted F1

The same 32-token, full-vocabulary answer instruction and original evidence are used in all nine arms.

| Arm | Cases | Quality (%) | EM/correct (%) | Raw F1 (%) | Calls (%) | Failed fallbacks | Mean model time (s) | Mean uncached elapsed estimate (s) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Granite | 240 | 26.49 | 10.83 | 19.83 | 0.00 | 0 | 0.5335 | 0.5352 |
| Always Jev | 240 | 26.72 | 11.67 | 22.14 | 100.00 | 0 | 0.5470 | 1.1189 |
| Boundary never | 240 | 26.49 | 10.83 | 19.83 | 0.00 | 0 | 0.5375 | 0.5398 |
| Boundary always | 240 | 26.72 | 11.67 | 22.14 | 100.00 | 0 | 0.5422 | 1.1095 |
| Boundary gate | 240 | 26.55 | 10.83 | 19.88 | 6.67 | 0 | 0.5409 | 0.5740 |
| Boundary random | 240 | 25.66 | 10.83 | 20.24 | 41.25 | 0 | 0.5362 | 0.7725 |
| Pilot gate | 240 | 26.40 | 10.83 | 21.82 | 63.75 | 0 | 0.6843 | 1.0425 |
| Lexical | 240 | 22.45 | 7.50 | 21.20 | 0.00 | 0 | 0.5674 | 0.5763 |
| Shuffled Jev | 240 | 22.75 | 11.67 | 17.34 | 100.00 | 0 | 0.5521 | 1.1242 |

Exploratory paired contrasts use 95% cluster bootstrap intervals.

| Comparison | Difference and 95% interval (pp) | Clusters |
| --- | --- | --- |
| Always Jev minus Granite | +0.23 [-2.56, +2.91] | 23 |
| Boundary gate minus Granite | +0.05 [-0.38, +0.45] | 23 |
| Boundary gate minus Always Jev | -0.17 [-2.65, +2.47] | 23 |
| Boundary gate minus Pilot gate | +0.15 [-1.99, +2.25] | 23 |
| Boundary gate minus Boundary random | +0.89 [-0.75, +2.81] | 23 |
| Always Jev minus Lexical | +4.27 [+1.65, +7.38] | 23 |
| Always Jev minus Shuffled Jev | +3.97 [+1.79, +6.21] | 23 |

The exploratory 3 pp loss-margin result is within the margin (lower interval bound -2.65 pp). This is not equivalence or a conjunctive success criterion.

## Routing value at the same actual test request count

Boundary-gate rows are primary, with individual 98.333% intervals. Pilot and random rows are exploratory 95%. Authored worlds, Hotpot questions and SQuAD articles are bootstrap clusters. Expected random matches calls, not dollars or input tokens.

| Domain | Arm | Quality (%) | Calls (%) | Expected random quality (%) | Routing value and interval (pp) | Interval level (%) | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Authored accuracy | Boundary gate | 31.75 | 72.42 | 30.58 | +1.17 [-0.70, +3.03] | 98.333 | Primary |
| Authored accuracy | Pilot gate | 28.17 | 55.16 | 29.72 | -1.55 [-3.31, +0.21] | 95.000 | Exploratory |
| Authored accuracy | Boundary random | 30.36 | 45.24 | 29.23 | +1.13 [-0.48, +2.79] | 95.000 | Exploratory |
| HotpotQA F1 | Boundary gate | 27.08 | 18.33 | 28.22 | -1.14 [-2.98, +0.61] | 98.333 | Primary |
| HotpotQA F1 | Pilot gate | 30.21 | 33.75 | 28.44 | +1.77 [+0.11, +3.45] | 95.000 | Exploratory |
| HotpotQA F1 | Boundary random | 27.06 | 40.00 | 28.53 | -1.48 [-3.31, +0.38] | 95.000 | Exploratory |
| SQuAD2 adapted F1 | Boundary gate | 26.55 | 6.67 | 26.51 | +0.04 [-0.47, +0.43] | 98.333 | Primary |
| SQuAD2 adapted F1 | Pilot gate | 26.40 | 63.75 | 26.64 | -0.24 [-1.29, +0.73] | 95.000 | Exploratory |
| SQuAD2 adapted F1 | Boundary random | 25.66 | 41.25 | 26.59 | -0.93 [-2.29, +0.50] | 95.000 | Exploratory |

## Which calls were chosen?

Beneficial/harmful/tied compares audited always-guided versus native quality per input. These labels were not available to the inference-time gate. A failed request remains a call.

| Domain | Arm | Called beneficial | Called harmful | Called tied | Skipped benefit | Skipped harm | Skipped tie |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Authored accuracy | Boundary gate | 44 | 20 | 301 | 10 | 9 | 120 |
| Authored accuracy | Pilot gate | 27 | 21 | 230 | 27 | 8 | 191 |
| Authored accuracy | Boundary random | 29 | 12 | 187 | 25 | 17 | 234 |
| HotpotQA F1 | Boundary gate | 6 | 14 | 24 | 49 | 38 | 109 |
| HotpotQA F1 | Pilot gate | 23 | 17 | 41 | 32 | 35 | 92 |
| HotpotQA F1 | Boundary random | 17 | 25 | 54 | 38 | 27 | 79 |
| SQuAD2 adapted F1 | Boundary gate | 3 | 2 | 11 | 29 | 21 | 174 |
| SQuAD2 adapted F1 | Pilot gate | 22 | 15 | 116 | 10 | 8 | 69 |
| SQuAD2 adapted F1 | Boundary random | 13 | 12 | 74 | 19 | 11 | 111 |

## Requests, active interventions and changed answers

A successful no-op call returns valid scores but activates no head under the frozen uniform-score convention. Changed paths compare final token IDs with native, not a human semantic judgment. Lexical guidance can change paths without a Jev call.

| Domain | Arm | Logical calls | Physical experiment attempts | Successful active calls | Successful no-op calls | Called changed paths | All changed paths |
| --- | --- | --- | --- | --- | --- | --- | --- |
| HotpotQA F1 | Always Jev | 240 | 52 | 234 | 6 | 144 | 144 |
| HotpotQA F1 | Boundary always | 240 | 59 | 234 | 6 | 144 | 144 |
| HotpotQA F1 | Boundary gate | 44 | 44 | 44 | 0 | 24 | 24 |
| HotpotQA F1 | Boundary never | 0 | 0 | 0 | 0 | 0 | 0 |
| HotpotQA F1 | Boundary random | 96 | 22 | 93 | 3 | 62 | 62 |
| HotpotQA F1 | Lexical | 0 | 0 | 0 | 0 | 0 | 150 |
| HotpotQA F1 | Granite | 0 | 0 | 0 | 0 | 0 | 0 |
| HotpotQA F1 | Pilot gate | 81 | 17 | 78 | 3 | 63 | 63 |
| HotpotQA F1 | Shuffled Jev | 240 | 46 | 234 | 6 | 191 | 191 |
| SQuAD2 adapted F1 | Always Jev | 240 | 49 | 162 | 78 | 99 | 99 |
| SQuAD2 adapted F1 | Boundary always | 240 | 65 | 162 | 78 | 99 | 99 |
| SQuAD2 adapted F1 | Boundary gate | 16 | 16 | 11 | 5 | 8 | 8 |
| SQuAD2 adapted F1 | Boundary never | 0 | 0 | 0 | 0 | 0 | 0 |
| SQuAD2 adapted F1 | Boundary random | 99 | 21 | 66 | 33 | 44 | 44 |
| SQuAD2 adapted F1 | Lexical | 0 | 0 | 0 | 0 | 0 | 160 |
| SQuAD2 adapted F1 | Granite | 0 | 0 | 0 | 0 | 0 | 0 |
| SQuAD2 adapted F1 | Pilot gate | 153 | 38 | 95 | 58 | 67 | 67 |
| SQuAD2 adapted F1 | Shuffled Jev | 240 | 51 | 162 | 78 | 118 | 118 |
| Authored accuracy | Always Jev | 504 | 35 | 465 | 39 | 378 | 378 |
| Authored accuracy | Boundary always | 504 | 39 | 465 | 39 | 378 | 378 |
| Authored accuracy | Boundary gate | 365 | 365 | 344 | 21 | 284 | 284 |
| Authored accuracy | Boundary never | 0 | 0 | 0 | 0 | 0 | 0 |
| Authored accuracy | Boundary random | 228 | 20 | 210 | 18 | 168 | 168 |
| Authored accuracy | Lexical | 0 | 0 | 0 | 0 | 0 | 387 |
| Authored accuracy | Granite | 0 | 0 | 0 | 0 | 0 | 0 |
| Authored accuracy | Pilot gate | 278 | 17 | 247 | 31 | 222 | 222 |
| Authored accuracy | Shuffled Jev | 504 | 28 | 465 | 39 | 412 | 412 |

## Actual generation work

Processed tokens are counted per layer; each of the forty layers has the recorded count. Total layer-token work is forty times that value. Final tokens exclude discarded pilots.

| Domain | Arm | Model forwards | Final tokens | Prefills | Processed tokens per layer | Discarded pilot tokens | Mean observation (ms) | Peak GPU allocated (GiB) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Authored accuracy | Granite | 10801 | 10801 | 504 | 157310 | 0 | 0.000 | 6.238 |
| Authored accuracy | Always Jev | 11064 | 11064 | 504 | 157573 | 0 | 0.000 | 6.238 |
| Authored accuracy | Boundary never | 10801 | 10801 | 504 | 157310 | 0 | 1.076 | 6.238 |
| Authored accuracy | Boundary always | 11064 | 11064 | 504 | 157573 | 0 | 1.078 | 6.238 |
| Authored accuracy | Boundary gate | 11198 | 11198 | 504 | 157707 | 0 | 1.095 | 6.238 |
| Authored accuracy | Boundary random | 10956 | 10956 | 504 | 157465 | 0 | 1.078 | 6.238 |
| Authored accuracy | Pilot gate | 13158 | 10990 | 782 | 228816 | 2168 | 0.000 | 6.292 |
| Authored accuracy | Lexical | 11968 | 11968 | 504 | 158477 | 0 | 0.000 | 6.238 |
| Authored accuracy | Shuffled Jev | 11290 | 11290 | 504 | 157799 | 0 | 0.000 | 6.238 |
| HotpotQA F1 | Granite | 4448 | 4448 | 240 | 344348 | 0 | 0.000 | 7.205 |
| HotpotQA F1 | Always Jev | 3564 | 3564 | 240 | 343464 | 0 | 0.000 | 7.205 |
| HotpotQA F1 | Boundary never | 4448 | 4448 | 240 | 344348 | 0 | 1.386 | 7.205 |
| HotpotQA F1 | Boundary always | 3564 | 3564 | 240 | 343464 | 0 | 1.383 | 7.205 |
| HotpotQA F1 | Boundary gate | 4212 | 4212 | 240 | 344112 | 0 | 1.382 | 7.205 |
| HotpotQA F1 | Boundary random | 4025 | 4025 | 240 | 343925 | 0 | 1.394 | 7.205 |
| HotpotQA F1 | Pilot gate | 4501 | 3872 | 321 | 452068 | 629 | 0.000 | 7.505 |
| HotpotQA F1 | Lexical | 4078 | 4078 | 240 | 343978 | 0 | 0.000 | 7.205 |
| HotpotQA F1 | Shuffled Jev | 3720 | 3720 | 240 | 343620 | 0 | 0.000 | 7.205 |
| SQuAD2 adapted F1 | Granite | 4400 | 4400 | 240 | 65085 | 0 | 0.000 | 6.262 |
| SQuAD2 adapted F1 | Always Jev | 4106 | 4106 | 240 | 64791 | 0 | 0.000 | 6.262 |
| SQuAD2 adapted F1 | Boundary never | 4400 | 4400 | 240 | 65085 | 0 | 0.679 | 6.262 |
| SQuAD2 adapted F1 | Boundary always | 4106 | 4106 | 240 | 64791 | 0 | 1.209 | 6.262 |
| SQuAD2 adapted F1 | Boundary gate | 4392 | 4392 | 240 | 65077 | 0 | 0.680 | 6.262 |
| SQuAD2 adapted F1 | Boundary random | 4259 | 4259 | 240 | 64944 | 0 | 0.682 | 6.262 |
| SQuAD2 adapted F1 | Pilot gate | 5345 | 4147 | 393 | 105270 | 1198 | 0.000 | 6.349 |
| SQuAD2 adapted F1 | Lexical | 4115 | 4115 | 240 | 64800 | 0 | 0.000 | 6.262 |
| SQuAD2 adapted F1 | Shuffled Jev | 4147 | 4147 | 240 | 64832 | 0 | 0.000 | 6.262 |

## Matched boundary overhead

Each comparison has identical per-input final token paths. Values are differences of paired arithmetic means, with no new inferential interval. Model time excludes measured provider wait. The always comparison uses reconstructed uncached timings when receipts were reused.

| Domain | Comparison | Mean model difference (ms) | Mean uncached first-token difference (ms) | Mean uncached elapsed difference (ms) |
| --- | --- | --- | --- | --- |
| Authored accuracy | Boundary never minus Granite | +5.862 | +1.700 | +6.619 |
| Authored accuracy | Boundary always minus Always Jev | -11.489 | +0.411 | -20.471 |
| HotpotQA F1 | Boundary never minus Granite | +2.240 | +1.513 | +3.062 |
| HotpotQA F1 | Boundary always minus Always Jev | -184.302 | -12.995 | -207.144 |
| SQuAD2 adapted F1 | Boundary never minus Granite | +3.954 | +1.359 | +4.640 |
| SQuAD2 adapted F1 | Boundary always minus Always Jev | -4.759 | +0.940 | -9.431 |

## Timing distributions

Tokenization/loading/startup are excluded here and included in cloud cost. Actual first-token timing may reuse a receipt; uncached estimates add its recorded call time back. Model timing includes controller/feature work and discarded pilot work, excluding measured provider wait. First-token timestamps mark synchronized completion of the first retained forward, before argmax/statistics/text decoding; they are not client delivery latency. A retained pilot can compute its first token before deciding to release the buffered output; its proxy excludes that later decision wait. Serial hosted-API measurements are not colocated or vLLM throughput.

### Model time excluding provider wait

| Domain | Arm | Mean (s) | Median (s) | p95 (s) |
| --- | --- | --- | --- | --- |
| Authored accuracy | Granite | 0.6263 | 0.5481 | 0.9471 |
| Authored accuracy | Always Jev | 0.7277 | 0.7955 | 1.1038 |
| Authored accuracy | Boundary never | 0.6322 | 0.5537 | 0.9565 |
| Authored accuracy | Boundary always | 0.7162 | 0.7780 | 1.0630 |
| Authored accuracy | Boundary gate | 0.7099 | 0.7317 | 1.0647 |
| Authored accuracy | Boundary random | 0.6720 | 0.5799 | 1.0599 |
| Authored accuracy | Pilot gate | 0.8027 | 0.9044 | 1.2965 |
| Authored accuracy | Lexical | 0.7731 | 0.8399 | 1.0687 |
| Authored accuracy | Shuffled Jev | 0.7421 | 0.8813 | 1.1125 |
| HotpotQA F1 | Granite | 0.7438 | 0.7356 | 1.1514 |
| HotpotQA F1 | Always Jev | 0.8719 | 0.6891 | 1.8010 |
| HotpotQA F1 | Boundary never | 0.7460 | 0.7401 | 1.1634 |
| HotpotQA F1 | Boundary always | 0.6876 | 0.5733 | 1.2433 |
| HotpotQA F1 | Boundary gate | 0.7266 | 0.7296 | 1.1871 |
| HotpotQA F1 | Boundary random | 0.7159 | 0.7154 | 1.2109 |
| HotpotQA F1 | Pilot gate | 0.8936 | 0.8655 | 1.8714 |
| HotpotQA F1 | Lexical | 1.3778 | 1.1496 | 3.1195 |
| HotpotQA F1 | Shuffled Jev | 0.9380 | 0.8563 | 1.8551 |
| SQuAD2 adapted F1 | Granite | 0.5335 | 0.5207 | 0.9204 |
| SQuAD2 adapted F1 | Always Jev | 0.5470 | 0.5340 | 1.0477 |
| SQuAD2 adapted F1 | Boundary never | 0.5375 | 0.5222 | 0.9321 |
| SQuAD2 adapted F1 | Boundary always | 0.5422 | 0.5270 | 1.0355 |
| SQuAD2 adapted F1 | Boundary gate | 0.5409 | 0.5231 | 0.9316 |
| SQuAD2 adapted F1 | Boundary random | 0.5362 | 0.5231 | 0.9339 |
| SQuAD2 adapted F1 | Pilot gate | 0.6843 | 0.7062 | 1.2121 |
| SQuAD2 adapted F1 | Lexical | 0.5674 | 0.5550 | 1.0487 |
| SQuAD2 adapted F1 | Shuffled Jev | 0.5521 | 0.5392 | 1.0536 |

### Observed first-token time in shared-receipt study

| Domain | Arm | Mean (s) | Median (s) | p95 (s) |
| --- | --- | --- | --- | --- |
| Authored accuracy | Granite | 0.0463 | 0.0434 | 0.0640 |
| Authored accuracy | Always Jev | 0.0964 | 0.0546 | 0.3923 |
| Authored accuracy | Boundary never | 0.0480 | 0.0472 | 0.0656 |
| Authored accuracy | Boundary always | 0.1034 | 0.0557 | 0.7050 |
| Authored accuracy | Boundary gate | 0.4611 | 0.4076 | 0.9287 |
| Authored accuracy | Boundary random | 0.0721 | 0.0511 | 0.0704 |
| Authored accuracy | Pilot gate | 0.1986 | 0.2683 | 0.3271 |
| Authored accuracy | Lexical | 0.0515 | 0.0481 | 0.0690 |
| Authored accuracy | Shuffled Jev | 0.0864 | 0.0546 | 0.3185 |
| HotpotQA F1 | Granite | 0.2431 | 0.2333 | 0.3707 |
| HotpotQA F1 | Always Jev | 0.3942 | 0.2608 | 1.0331 |
| HotpotQA F1 | Boundary never | 0.2446 | 0.2348 | 0.3714 |
| HotpotQA F1 | Boundary always | 0.4010 | 0.2643 | 0.9657 |
| HotpotQA F1 | Boundary gate | 0.3425 | 0.2526 | 0.9236 |
| HotpotQA F1 | Boundary random | 0.2992 | 0.2444 | 0.8634 |
| HotpotQA F1 | Pilot gate | 0.4304 | 0.3132 | 1.1842 |
| HotpotQA F1 | Lexical | 0.2803 | 0.2704 | 0.4432 |
| HotpotQA F1 | Shuffled Jev | 0.3731 | 0.2676 | 0.9651 |
| SQuAD2 adapted F1 | Granite | 0.0416 | 0.0421 | 0.0492 |
| SQuAD2 adapted F1 | Always Jev | 0.1667 | 0.0488 | 0.7358 |
| SQuAD2 adapted F1 | Boundary never | 0.0430 | 0.0433 | 0.0507 |
| SQuAD2 adapted F1 | Boundary always | 0.2050 | 0.0493 | 0.7462 |
| SQuAD2 adapted F1 | Boundary gate | 0.0739 | 0.0438 | 0.3351 |
| SQuAD2 adapted F1 | Boundary random | 0.1000 | 0.0443 | 0.7026 |
| SQuAD2 adapted F1 | Pilot gate | 0.2832 | 0.2778 | 0.9701 |
| SQuAD2 adapted F1 | Lexical | 0.0476 | 0.0469 | 0.0558 |
| SQuAD2 adapted F1 | Shuffled Jev | 0.1639 | 0.0489 | 0.7711 |

### Uncached first-token estimate

| Domain | Arm | Mean (s) | Median (s) | p95 (s) |
| --- | --- | --- | --- | --- |
| Authored accuracy | Granite | 0.0463 | 0.0434 | 0.0640 |
| Authored accuracy | Always Jev | 0.6268 | 0.6898 | 0.9235 |
| Authored accuracy | Boundary never | 0.0480 | 0.0472 | 0.0656 |
| Authored accuracy | Boundary always | 0.6272 | 0.6903 | 0.9234 |
| Authored accuracy | Boundary gate | 0.4611 | 0.4076 | 0.9287 |
| Authored accuracy | Boundary random | 0.3104 | 0.0640 | 0.8559 |
| Authored accuracy | Pilot gate | 0.5138 | 0.5482 | 1.1772 |
| Authored accuracy | Lexical | 0.0515 | 0.0481 | 0.0690 |
| Authored accuracy | Shuffled Jev | 0.6268 | 0.6890 | 0.9238 |
| HotpotQA F1 | Granite | 0.2431 | 0.2333 | 0.3707 |
| HotpotQA F1 | Always Jev | 0.8594 | 0.8991 | 1.2090 |
| HotpotQA F1 | Boundary never | 0.2446 | 0.2348 | 0.3714 |
| HotpotQA F1 | Boundary always | 0.8464 | 0.8892 | 1.1987 |
| HotpotQA F1 | Boundary gate | 0.3425 | 0.2526 | 0.9236 |
| HotpotQA F1 | Boundary random | 0.4832 | 0.3190 | 0.9953 |
| HotpotQA F1 | Pilot gate | 0.5964 | 0.3132 | 1.4852 |
| HotpotQA F1 | Lexical | 0.2803 | 0.2704 | 0.4432 |
| HotpotQA F1 | Shuffled Jev | 0.8620 | 0.9061 | 1.2234 |
| SQuAD2 adapted F1 | Granite | 0.0416 | 0.0421 | 0.0492 |
| SQuAD2 adapted F1 | Always Jev | 0.6109 | 0.6952 | 0.8162 |
| SQuAD2 adapted F1 | Boundary never | 0.0430 | 0.0433 | 0.0507 |
| SQuAD2 adapted F1 | Boundary always | 0.6118 | 0.6926 | 0.8230 |
| SQuAD2 adapted F1 | Boundary gate | 0.0739 | 0.0438 | 0.3351 |
| SQuAD2 adapted F1 | Boundary random | 0.2782 | 0.0486 | 0.7737 |
| SQuAD2 adapted F1 | Pilot gate | 0.5480 | 0.5859 | 1.0317 |
| SQuAD2 adapted F1 | Lexical | 0.0476 | 0.0469 | 0.0558 |
| SQuAD2 adapted F1 | Shuffled Jev | 0.6109 | 0.6915 | 0.8201 |

### Uncached elapsed estimate

| Domain | Arm | Mean (s) | Median (s) | p95 (s) |
| --- | --- | --- | --- | --- |
| Authored accuracy | Granite | 0.6280 | 0.5498 | 0.9488 |
| Authored accuracy | Always Jev | 1.3144 | 1.3420 | 1.8289 |
| Authored accuracy | Boundary never | 0.6347 | 0.5563 | 0.9593 |
| Authored accuracy | Boundary always | 1.2939 | 1.3149 | 1.7751 |
| Authored accuracy | Boundary gate | 1.1225 | 1.1876 | 1.7858 |
| Authored accuracy | Boundary random | 0.9351 | 0.9366 | 1.7411 |
| Authored accuracy | Pilot gate | 1.1428 | 0.9563 | 1.9886 |
| Authored accuracy | Lexical | 0.7853 | 0.8539 | 1.0893 |
| Authored accuracy | Shuffled Jev | 1.3290 | 1.3586 | 1.8598 |
| HotpotQA F1 | Granite | 0.7455 | 0.7373 | 1.1534 |
| HotpotQA F1 | Always Jev | 1.5016 | 1.3386 | 2.4955 |
| HotpotQA F1 | Boundary never | 0.7486 | 0.7427 | 1.1665 |
| HotpotQA F1 | Boundary always | 1.2944 | 1.2090 | 1.9255 |
| HotpotQA F1 | Boundary gate | 0.8283 | 0.8522 | 1.4943 |
| HotpotQA F1 | Boundary random | 0.9578 | 0.9999 | 1.7499 |
| HotpotQA F1 | Pilot gate | 1.1123 | 0.9808 | 2.6394 |
| HotpotQA F1 | Lexical | 1.4080 | 1.1847 | 3.1816 |
| HotpotQA F1 | Shuffled Jev | 1.5687 | 1.4474 | 2.6426 |
| SQuAD2 adapted F1 | Granite | 0.5352 | 0.5223 | 0.9222 |
| SQuAD2 adapted F1 | Always Jev | 1.1189 | 1.1375 | 1.7214 |
| SQuAD2 adapted F1 | Boundary never | 0.5398 | 0.5245 | 0.9348 |
| SQuAD2 adapted F1 | Boundary always | 1.1095 | 1.1371 | 1.6818 |
| SQuAD2 adapted F1 | Boundary gate | 0.5740 | 0.5469 | 0.9388 |
| SQuAD2 adapted F1 | Boundary random | 0.7725 | 0.7317 | 1.4995 |
| SQuAD2 adapted F1 | Pilot gate | 1.0425 | 1.0574 | 1.8308 |
| SQuAD2 adapted F1 | Lexical | 0.5763 | 0.5636 | 1.0622 |
| SQuAD2 adapted F1 | Shuffled Jev | 1.1242 | 1.1336 | 1.7494 |

## Output forms

A token cap and an unparsed answer remain separate outcomes. Recognized uncertainty need not be the word UNKNOWN. Empty/EOS alone is not a correct abstention under the adapted contract. Dashes mean that the task has no registered abstention parser.

| Domain | Arm | EOS | Token cap | Empty | Natural abstentions | Bare UNKNOWN | Wrong abstentions | Unparsed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HotpotQA F1 | Always Jev | 219 | 21 | 0 | — | — | — | — |
| HotpotQA F1 | Boundary always | 219 | 21 | 0 | — | — | — | — |
| HotpotQA F1 | Boundary gate | 204 | 36 | 0 | — | — | — | — |
| HotpotQA F1 | Boundary never | 199 | 41 | 0 | — | — | — | — |
| HotpotQA F1 | Boundary random | 208 | 32 | 0 | — | — | — | — |
| HotpotQA F1 | Lexical | 214 | 26 | 0 | — | — | — | — |
| HotpotQA F1 | Granite | 199 | 41 | 0 | — | — | — | — |
| HotpotQA F1 | Pilot gate | 216 | 24 | 0 | — | — | — | — |
| HotpotQA F1 | Shuffled Jev | 215 | 25 | 0 | — | — | — | — |
| SQuAD2 adapted F1 | Always Jev | 214 | 26 | 0 | 11 | 0 | 0 | — |
| SQuAD2 adapted F1 | Boundary always | 214 | 26 | 0 | 11 | 0 | 0 | — |
| SQuAD2 adapted F1 | Boundary gate | 214 | 26 | 0 | 16 | 0 | 0 | — |
| SQuAD2 adapted F1 | Boundary never | 213 | 27 | 0 | 16 | 0 | 0 | — |
| SQuAD2 adapted F1 | Boundary random | 215 | 25 | 0 | 13 | 0 | 0 | — |
| SQuAD2 adapted F1 | Lexical | 215 | 25 | 0 | 3 | 0 | 0 | — |
| SQuAD2 adapted F1 | Granite | 213 | 27 | 0 | 16 | 0 | 0 | — |
| SQuAD2 adapted F1 | Pilot gate | 214 | 26 | 0 | 11 | 0 | 0 | — |
| SQuAD2 adapted F1 | Shuffled Jev | 208 | 32 | 0 | 13 | 0 | 0 | — |
| Authored accuracy | Always Jev | 285 | 219 | 0 | 12 | 0 | 0 | 290 |
| Authored accuracy | Boundary always | 285 | 219 | 0 | 12 | 0 | 0 | 290 |
| Authored accuracy | Boundary gate | 294 | 210 | 0 | 11 | 0 | 0 | 259 |
| Authored accuracy | Boundary never | 314 | 190 | 0 | 13 | 0 | 0 | 178 |
| Authored accuracy | Boundary random | 303 | 201 | 0 | 12 | 0 | 0 | 218 |
| Authored accuracy | Lexical | 278 | 226 | 0 | 12 | 0 | 0 | 330 |
| Authored accuracy | Granite | 314 | 190 | 0 | 13 | 0 | 0 | 178 |
| Authored accuracy | Pilot gate | 280 | 224 | 0 | 12 | 0 | 0 | 272 |
| Authored accuracy | Shuffled Jev | 280 | 224 | 0 | 12 | 0 | 0 | 220 |

## Raw versus adapted SQuAD2 metrics

Raw scores apply ordinary whole-answer EM/F1 to the unmodified text. Adapted scores use the frozen natural-abstention recognizer and reject empty output. This is not the official SQuAD no-answer-probability protocol. The cohort is balanced 120 answerable / 120 impossible.

| Arm | Raw EM (%) | Raw F1 (%) | Adapted EM (%) | Adapted F1 (%) |
| --- | --- | --- | --- | --- |
| Always Jev | 7.08 | 22.14 | 11.67 | 26.72 |
| Boundary always | 7.08 | 22.14 | 11.67 | 26.72 |
| Boundary gate | 4.17 | 19.88 | 10.83 | 26.55 |
| Boundary never | 4.17 | 19.83 | 10.83 | 26.49 |
| Boundary random | 5.42 | 20.24 | 10.83 | 25.66 |
| Lexical | 6.25 | 21.20 | 7.50 | 22.45 |
| Granite | 4.17 | 19.83 | 10.83 | 26.49 |
| Pilot gate | 6.25 | 21.82 | 10.83 | 26.40 |
| Shuffled Jev | 6.25 | 17.34 | 11.67 | 22.75 |

## Descriptive subgroups

All registered subgroups and arms are retained in output-diagnostics.json. Tables below show native, always and selected boundary gate for readability; no subgroup significance tests or post-test rule fitting were performed.

### Authored accuracy / condition

| Value | Cases per arm | Native (%) | Always (%) | Boundary gate (%) | Gate calls (%) |
| --- | --- | --- | --- | --- | --- |
| heavy | 252 | 23.81 | 34.92 | 34.52 | 88.10 |
| light | 252 | 30.16 | 28.97 | 28.97 | 56.75 |

### Authored accuracy / depth

| Value | Cases per arm | Native (%) | Always (%) | Boundary gate (%) | Gate calls (%) |
| --- | --- | --- | --- | --- | --- |
| 1 | 84 | 59.52 | 59.52 | 59.52 | 52.38 |
| 2 | 84 | 34.52 | 42.86 | 39.29 | 70.24 |
| 3 | 84 | 21.43 | 36.90 | 36.90 | 67.86 |
| 4 | 84 | 19.05 | 27.38 | 28.57 | 71.43 |
| 5 | 84 | 11.90 | 16.67 | 15.48 | 82.14 |
| 6 | 84 | 15.48 | 8.33 | 10.71 | 90.48 |

### Authored accuracy / family

| Value | Cases per arm | Native (%) | Always (%) | Boundary gate (%) | Gate calls (%) |
| --- | --- | --- | --- | --- | --- |
| dependency | 168 | 23.81 | 25.60 | 25.00 | 86.31 |
| original | 168 | 27.38 | 31.55 | 34.52 | 67.86 |
| paraphrase | 168 | 29.76 | 38.69 | 35.71 | 63.10 |

### Authored accuracy / missing

| Value | Cases per arm | Native (%) | Always (%) | Boundary gate (%) | Gate calls (%) |
| --- | --- | --- | --- | --- | --- |
| False | 252 | 48.81 | 59.13 | 59.13 | 74.60 |
| True | 252 | 5.16 | 4.76 | 4.37 | 70.24 |

### HotpotQA F1 / question_type

| Value | Cases per arm | Native (%) | Always (%) | Boundary gate (%) | Gate calls (%) |
| --- | --- | --- | --- | --- | --- |
| bridge | 202 | 29.35 | 29.56 | 28.22 | 20.30 |
| comparison | 38 | 20.54 | 28.54 | 21.06 | 7.89 |

### SQuAD2 adapted F1 / article

| Value | Cases per arm | Native (%) | Always (%) | Boundary gate (%) | Gate calls (%) |
| --- | --- | --- | --- | --- | --- |
| 1973_oil_crisis | 6 | 38.10 | 39.39 | 38.10 | 0.00 |
| Amazon_rainforest | 7 | 50.81 | 49.21 | 50.81 | 14.29 |
| Civil_disobedience | 9 | 20.67 | 22.32 | 20.67 | 0.00 |
| Computational_complexity_theory | 18 | 18.89 | 19.18 | 19.81 | 11.11 |
| Construction | 6 | 11.86 | 12.79 | 11.86 | 0.00 |
| Ctenophora | 11 | 15.89 | 14.37 | 15.89 | 0.00 |
| Economic_inequality | 14 | 25.63 | 32.05 | 25.63 | 0.00 |
| Force | 15 | 19.53 | 32.02 | 21.78 | 20.00 |
| French_and_Indian_War | 13 | 42.47 | 43.32 | 42.47 | 0.00 |
| Fresno,_California | 12 | 39.03 | 40.30 | 39.03 | 8.33 |
| Geology | 6 | 12.04 | 10.00 | 12.04 | 16.67 |
| Harvard_University | 7 | 26.80 | 26.12 | 26.80 | 0.00 |
| Imperialism | 13 | 10.72 | 13.53 | 10.60 | 15.38 |
| Islamism | 15 | 28.28 | 35.50 | 28.28 | 6.67 |
| Oxygen | 12 | 17.68 | 16.73 | 17.68 | 0.00 |
| Packet_switching | 13 | 37.74 | 26.51 | 37.74 | 0.00 |
| Pharmacy | 7 | 21.85 | 17.34 | 21.85 | 0.00 |
| Prime_number | 10 | 16.85 | 20.35 | 16.85 | 10.00 |
| Rhine | 8 | 20.69 | 14.42 | 16.20 | 12.50 |
| Scottish_Parliament | 10 | 39.87 | 40.37 | 39.87 | 0.00 |
| Southern_California | 4 | 57.89 | 57.89 | 57.89 | 25.00 |
| University_of_Chicago | 14 | 30.95 | 19.48 | 30.95 | 7.14 |
| Warsaw | 10 | 25.37 | 23.07 | 25.37 | 10.00 |

### SQuAD2 adapted F1 / missing

| Value | Cases per arm | Native (%) | Always (%) | Boundary gate (%) | Gate calls (%) |
| --- | --- | --- | --- | --- | --- |
| False | 120 | 39.66 | 44.28 | 39.76 | 8.33 |
| True | 120 | 13.33 | 9.17 | 13.33 | 5.00 |

### SQuAD2 adapted F1 / sources

| Value | Cases per arm | Native (%) | Always (%) | Boundary gate (%) | Gate calls (%) |
| --- | --- | --- | --- | --- | --- |
| 1 | 4 | 36.67 | 36.67 | 36.67 | 100.00 |
| 10 | 4 | 49.25 | 49.25 | 49.25 | 0.00 |
| 11 | 2 | 12.50 | 16.67 | 12.50 | 0.00 |
| 2 | 10 | 30.64 | 22.92 | 32.31 | 20.00 |
| 3 | 34 | 30.83 | 35.02 | 30.83 | 0.00 |
| 4 | 59 | 21.60 | 24.33 | 22.04 | 1.69 |
| 5 | 48 | 26.77 | 26.18 | 26.77 | 6.25 |
| 6 | 30 | 28.99 | 28.28 | 28.99 | 3.33 |
| 7 | 25 | 21.98 | 22.01 | 22.25 | 8.00 |
| 8 | 16 | 26.34 | 24.94 | 24.10 | 12.50 |
| 9 | 8 | 29.40 | 15.83 | 29.40 | 12.50 |

[First-by-ID illustrative examples](examples.md) include full public evidence and unmodified outputs. They are not representative samples or blinded human grades. External data retains [Hotpot](HotpotQA-NOTICE.md) and [SQuAD](SQuAD-NOTICE.md) attribution.
