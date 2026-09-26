# Development-frozen request-budget frontier

This is an exploratory **offline replay of saved deterministic branches**, not additional live generation. Each frozen rule selects the audited native or always-guided output using the native pilot features. It makes **zero new model forwards and zero API calls**. Request/work counts below are reconstructed deployment requirements, not measured savings, latency or throughput.

[Prospective supplement](../../research/selective-budget-frontier.md) · [Original selection](../../research/protocols/selective-budget-frontier-v1/selection.json) · [Fallback-accounting repair](../../research/selective-budget-accounting-amendment.md) · [Unchanged rules, repaired source binding](../../research/protocols/selective-budget-frontier-v1/selection-v2.json) · [Audited JSON](budget-frontier.json)

Registration followed development selection while the held-out run was in progress, before held-out aggregate inspection. The main quality-first gate selected calls everywhere. This separate analysis asks what quality remains under explicit development request ceilings. It does not replace that main result or select a winner using test quality.

The useful signal is confined to the authored task. At the lowest ceiling,
21.43% of calls gives 31.55% accuracy and positive exploratory routing value
relative to random calls at the same count. Hotpot instead gives 25.00% F1 at
18.50% calls, slightly below native. The other two budgets do not establish
positive routing value in either domain. None is promoted as a test-selected
winning policy, and no confirmatory noninferiority conclusion is attached to this
supplement. Fewer reconstructed API requests still entail extra pilot/restart work.

| Development ceiling (%) | Frozen rule | Development requests (%) | Overall replay requests (%) |
| ---: | --- | ---: | ---: |
| 25.00 | `{"direction": "gt", "feature": "min_probability", "kind": "threshold", "threshold": 0.7718728184700012}` | 24.36 | 20.60 |
| 50.00 | `{"direction": "gt", "feature": "min_probability", "kind": "threshold", "threshold": 0.6373283863067627}` | 49.36 | 43.18 |
| 75.00 | `{"direction": "gt", "feature": "min_probability", "kind": "threshold", "threshold": 0.5249033570289612}` | 74.36 | 66.48 |

Ceilings constrain the unweighted development request fraction. Distribution changes mean the test fraction can exceed the stated development ceiling. Policy quality uses an equal-domain objective, and call count does not imply equal input-token cost.

![Budget frontier](figures/budget-frontier.png)

| Domain | Dev ceiling (%) | Replay requests (%) | Native (%) | Always guided (%) | Replay (%) | Replay − native, 95% CI (pp) | Replay − always, 95% CI (pp) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| hotpot | 25.00 | 18.50 | 25.23 | 28.76 | 25.00 | -0.23 [-1.40, +1.13] | -3.76 [-7.57, -0.06] |
| synthetic | 25.00 | 21.43 | 28.77 | 33.13 | 31.55 | +2.78 [+1.19, +4.56] | -1.59 [-4.57, +1.39] |
| hotpot | 50.00 | 38.50 | 25.23 | 28.76 | 25.69 | +0.46 [-1.47, +2.54] | -3.07 [-6.55, +0.26] |
| synthetic | 50.00 | 45.04 | 28.77 | 33.13 | 31.55 | +2.78 [+0.79, +4.96] | -1.59 [-4.37, +1.19] |
| hotpot | 75.00 | 63.50 | 25.23 | 28.76 | 27.09 | +1.86 [-1.03, +4.96] | -1.67 [-4.17, +0.81] |
| synthetic | 75.00 | 67.66 | 28.77 | 33.13 | 32.54 | +3.77 [+1.19, +6.55] | -0.60 [-2.78, +1.59] |

Authored quality is conservative-parser accuracy; Hotpot quality is whole-answer token F1. Intervals are exploratory 95% paired world/question bootstrap intervals, not multiplicity-adjusted primary claims. Paired light/heavy contexts remain together. All three budgets and both domains are reported.

| Domain | Dev ceiling (%) | Random expected quality (%) | Routing value, 95% CI (pp) | Permutation tail p | Called benefits | Called harms | Missed benefits | Avoided harms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| hotpot | 25.00 | 25.88 | -0.88 [-2.10, +0.44] | 0.8748 | 3 | 6 | 48 | 30 |
| synthetic | 25.00 | 29.71 | +1.84 [+0.41, +3.39] | 0.0099 | 15 | 1 | 37 | 29 |
| hotpot | 50.00 | 26.59 | -0.90 [-2.65, +0.92] | 0.8232 | 13 | 12 | 38 | 24 |
| synthetic | 50.00 | 30.74 | +0.81 [-0.86, +2.52] | 0.2156 | 21 | 7 | 31 | 23 |
| hotpot | 75.00 | 27.47 | -0.38 [-2.35, +1.55] | 0.6526 | 27 | 22 | 24 | 14 |
| synthetic | 75.00 | 31.72 | +0.82 [-0.88, +2.52] | 0.1999 | 34 | 15 | 18 | 15 |

Random expectation fixes the replay’s actual request count within each domain; it is a counterfactual expectation rather than another measured model arm. Routing value separates where calls are placed from the average effect of calling. These exploratory comparisons do not establish general benefit prediction.

| Domain | Dev ceiling (%) | Reconstructed forwards | Processed tokens | Prefills | Discarded pilot tokens | Requested/charged input tokens | Unknown calls |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| hotpot | 25.00 | 3,668 | 352,285 | 237 | 233 | 98,008 | 0 |
| synthetic | 25.00 | 11,588 | 197,251 | 612 | 864 | 219,610 | 0 |
| hotpot | 50.00 | 4,001 | 411,671 | 277 | 498 | 200,654 | 0 |
| synthetic | 50.00 | 12,741 | 230,275 | 731 | 1,808 | 415,854 | 0 |
| hotpot | 75.00 | 4,270 | 485,173 | 327 | 853 | 329,037 | 0 |
| synthetic | 75.00 | 13,693 | 260,547 | 845 | 2,708 | 612,391 | 0 |

A successful requested intervention requires the native pilot plus a fresh guided prefill. A skipped or failed request retains the native pilot and cache; failure still counts as a requested call and its unknown charge is reserved at 65,536 input tokens. Fewer requests need not reduce GPU work, and these work totals do not measure deployment latency.

The replay is tied to the original experiment’s exact saved branch outputs and main audit. It is not fresh replication, an independently observed deployment or proof of a useful new LLM architecture. A selected rule would need a prospective live deployment test before measured performance claims.
