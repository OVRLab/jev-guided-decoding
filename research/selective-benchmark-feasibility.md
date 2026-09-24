# Full-suite workload and admission: R26 cost investigation

Recorded 2026-09-24. The owner's cap is **$110 cumulative**, with an estimated
$42.627081 already consumed before R26. The $6 exposed-case profile is included
in the parent's $60 reserve. A full ten-task quote is not yet established, and
an increased spending cap does not itself admit a benchmark implementation.

## Workload inventory

Counts below describe source data, not model attempts, and are not scored results.
Sources/revisions are pinned in the [ten-task contract](benchmark-suite-contract-v1.md).

| Task | Complete-source workload | Remaining admission work |
| --- | ---: | --- |
| MMLU-Pro | 12,032 test questions | Official five-shot prompt/option mapping; independently bounded extraction without random fallback or gold-controlled retry. R26 zero-shot timings are only a rough cost proxy. |
| GPQA Diamond | Gated dataset; access not admitted | Existing owner-token check returns HTTP 403. Owner access is required before loading/validating Diamond cases. |
| AIME 2026 | 30 problems | Numeric pass@1 contract, sampling/repetition budget and problem-level uncertainty; GSM timing is not a reliable AIME estimate. |
| LiveCodeBench | Release/window must be frozen | Official code README describes 1,055 cumulative `release_v6` problems, while `v6` selects only its new increment. No model run has started; isolated hidden-test execution and asset attribution remain pending. |
| IFBench | 300 prompts | Pinned strict/loose evaluator environment and actual instruction-following outputs. Twelve prompts were already consumed for R23 development. |
| MuSR | 756 records in three families | Official prompt/scoring alignment and related-story clustering; previously exposed cases/variants remain development. |
| LongBench v2 | 503 questions | Tokenized lengths, declared context/truncation policy, memory/prefill profile, and a Jev input policy compatible with the admitted billing/context limits. |
| SimpleQA Verified | 1,000 questions | An independently calibrated, blinded judge; preserve correct/incorrect/abstention and evaluator expenses. |
| BFCL v4 | 4,696 source scoring records, before category expansion | Stateful tool harness, three memory backends, two web-search variants, category weighting and external-search access/cost. Record count is not total turns or attempts. |
| SWE-bench Verified | 500 repository issues | Fixed repair-agent scaffold, isolated repository environments, identical tool/time/token budgets and official patch tests. |

## Important source findings

The pinned [LongBench runner](https://github.com/THUDM/LongBench/blob/2e00731f8d0bff23dc4325161044d0ed8af94c1e/pred.py)
allows model-specific input caps and truncates to the first/last halves. Therefore
full-record coverage does not require unlimited context, but our current admission
runner's 16,384-token rejection policy is not yet an implementation of that full
protocol. Declare the limit and discarded tokens for every model, preserve the
question/options, and test prefill memory/runtime before allocating 503 cases.
The present 50-case profile cannot price long-context workloads.

The pinned [LiveCodeBench README](https://github.com/LiveCodeBench/LiveCodeBench/blob/28fef95ea8c9f7a547c8329f2cd3d32b92c1fa24/README.md)
uses multiple samples by default (`n=10`); one generated answer per problem is a
different sampling budget and must be labeled. The source loader distinguishes
cumulative releases from date increments. Generated code and decoded hidden-test
assets must stay in credential-free isolation. No hidden tests may enter Jev.

The BFCL [data card](https://github.com/ShishirPatil/gorilla/blob/6ea57973c7a6097fd7c5915698c54c17c5b1b6c8/berkeley-function-call-leaderboard/bfcl_eval/data/README.md)
labels its data Apache 2.0. Its pinned [category mapping](https://github.com/ShishirPatil/gorilla/blob/6ea57973c7a6097fd7c5915698c54c17c5b1b6c8/berkeley-function-call-leaderboard/bfcl_eval/constants/category_mapping.py)
expands memory into three backends and web search into two variants; format
sensitivity is explicitly non-scoring. Its [web implementation](https://github.com/ShishirPatil/gorilla/blob/6ea57973c7a6097fd7c5915698c54c17c5b1b6c8/berkeley-function-call-leaderboard/bfcl_eval/eval_checker/multi_turn_eval/func_source_code/web_search.py)
uses SerpAPI credentials. This access is not configured or budgeted in R26-A.
Do not substitute fabricated tool results and label them an official complete run.

SWE-bench's [evaluation guide](https://www.swebench.com/SWE-bench/guides/evaluation/)
applies generated patches in repository containers and executes their tests. A
question-answer timing profile does not estimate agent trajectories, environment
builds, patch testing or repository storage. These require a separate scoped
engineering pilot before a credible full quote.

## What the measured profile can establish

R26-A measures batched native generation for original Granite 4.0-1B, thinking
Granite 4.2-3B and Qwen3-4B-Instruct-2507, plus eight serial repeats each and actual
selective 1B repair controls. Exact outputs, padded token slots, prefill and API
work stay in the report. No repeat is selected as a preferred answer.

A per-task cost projection uses each batch's wall time divided by its batch size,
then extrapolates to source count. This is a descriptive, exposed-case estimate;
it is not per-request serial latency, a statistical upper bound or an invoice.
MMLU's full five-shot inputs differ from this zero-shot pilot. Repeated samples,
model loading, Jev calls, independent grading, failed jobs, CPU/container work,
disk/network and tax must be added explicitly. Missing domains retain unknown
cost rather than borrowing an unrelated cheap-task rate.

A full-source rerun containing development-exposed examples must be labeled as
partly exposed, with untouched results reported separately. It cannot be described
as a pristine held-out test even if every source row is completed.


## Full-source context tokenization (no model inference)

[Pinned workload records](../reports/2026-09-24-selective-admission/long-context-workload.json)
apply the official zero-shot template and each pinned native chat template to all
503 records, without truncation or generation. Input lengths include the wrapper.

| Model | Total untruncated input tokens | Median | Maximum | Above 16K pilot input limit | Above native window minus output reserve |
| --- | ---: | ---: | ---: | ---: | ---: |
| granite_4_0_1b | 123,432,745 | 99,171 | 4,145,218 | 475 | 190 |
| granite_4_2_3b | 137,307,823 | 108,476 | 5,140,628 | 479 | 223 |
| qwen3_4b_instruct | 131,092,015 | 99,523 | 4,163,923 | 476 | 103 |

This is a CPU-only workload scan, not a memory/latency test or a benchmark score.
The final column uses the profile output reserves (2,048 / 8,192 / 16,384 tokens)
and source model windows (131,072 / 131,072 / 262,144). Different declared context
policies require new counts and a prospective protocol.
