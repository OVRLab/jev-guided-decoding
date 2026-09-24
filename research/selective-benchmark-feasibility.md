# Full-suite workload and admission: R26 cost investigation

Recorded 2026-09-24. The owner's cap is **$110 cumulative**, with an estimated
$42.627081 already consumed before R26. The $6 exposed-case profile is included
in the parent's $60 reserve. A full ten-task quote is not yet established, and
an increased spending cap does not itself admit a benchmark implementation.

## Completed pilot and current funds

The [completed R26-A report](../reports/2026-09-24-selective-admission/README.md)
records 297 generated outputs, failed format admission, exact artifact
replay and deletion of all owned resources. Pilot estimate $3.5464;
cumulative $46.17/$110, leaving $63.83
before tax/separate network. For the current prototype, full MMLU-Pro on thinking
Granite 3B alone extrapolates to roughly $505.
This exposed, zero-shot timing estimate is not a guaranteed quote or the cost of
optimized serving. Resolve readout admission and runtime inefficiency before
using the remaining budget on a fresh full benchmark; the ten-task total is still
unpriced.

## GPQA access update

The [access recheck](../reports/2026-09-24-selective-admission/gpqa-access-update.json)
succeeded on 2026-09-24 at 09:16 UTC. This resolves the earlier access blocker; it
is not a dataset-schema check, benchmark run or model result. Only one byte was
read, no examples were displayed, and no inference was requested. GPQA examples
must remain outside public reports; reproducibility should use source revisions,
hashes, scripts and aggregate results consistent with the accepted access conditions.

## Workload inventory

Counts below describe source data, not model attempts, and are not scored results.
Sources/revisions are pinned in the [ten-task contract](benchmark-suite-contract-v1.md).

| Task | Complete-source workload | Remaining admission work |
| --- | ---: | --- |
| MMLU-Pro | 12,032 test questions | Official five-shot prompt/option mapping; independently bounded extraction without random fallback or gold-controlled retry. R26 zero-shot timings are only a rough cost proxy. |
| GPQA Diamond | Access verified after R26-A; dataset/evaluator admission pending | Authenticated one-byte GET succeeded with HTTP 206 on the pinned Diamond CSV after the owner enabled token permission and accepted the access conditions; pin option shuffling, validate source/schema and grading before inference. |
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


## Next work before another paid benchmark

1. Admit the separately versioned reader and official-compatible task prompts on
   exposed development outputs, preserving R26-A's frozen primary result. Test
   label/option conflicts, unfinished thinking, refusals, empty finals and each
   task's own scoring semantics before selecting any fresh test records. Freeze
   any stopping contract prospectively and apply it consistently: Qwen case 40
   mechanically repeats the same final-answer line until its 16,384-token ceiling,
   so that time is not all productive reasoning or an inherent benchmark cost.
2. Improve inference scheduling, with attention to finished rows that currently
   continue occupying padded decode slots. A new runtime needs cached/full and
   token-provenance checks, unchanged-base-weight evidence and a bounded timing
   comparison. Keep comparator generation profiles explicit; silently shortening
   only a slower baseline's reasoning budget would change the comparison.
3. Freeze a new protocol and quote from the admitted runtime. Include native
   drafts, actual conditional repair, Jev latency/charges, controls, failures and
   independent evaluation. Do not multiply the current tiny pilot into a firm
   all-domain quote or claim an optimization speedup before measuring it.
4. Admit long-context prefill/truncation and credential-free code/agent harnesses,
   resolve required dataset/service access, then price each remaining workload.
   Choose any affordable subset transparently under the existing $110 cumulative
   cap; partial coverage cannot be reported as full completion of all ten.

One candidate for testing is a fixed-size cache with compilation where the pinned
model supports it. Hugging Face's [cache guidance](https://huggingface.co/docs/transformers/en/kv_cache)
explains both the compilation benefit and the wasted masked work when sequence
lengths vary. This is a hypothesis for measurement, not a measured speedup or a
guarantee that Granite's model-specific cache and research hooks support it.


## Recommended sequence after GPQA access is resolved

This is a planning recommendation, not a frozen new experiment or a dispatched
worker. Estimated remaining funds are $63.83 before tax/separate network.

First integrate and validate the new readout with task-appropriate prompts, then
validate stopping behavior and improve batching/cache execution on already-exposed
development cases. Reserve at most $5 from the remaining budget for a separately
registered engineering profile after offline checks pass; require measured timing,
output-contract and token/weight provenance evidence before fresh evaluation.

Freeze the selected internal repair architecture, checkpoints, routing, generation
profiles, scoring and analysis before new test outcomes. Compare original Granite,
Granite-only additional inference, informative Jev repair and matched feedback
controls; disclose that earlier selective controls all shared Jev-based routing.
Include the pinned Granite 3B and Qwen 4B comparators on identical case sets, with
sampling/thinking profiles explicit and costs recorded.

Prioritize a complete GPQA Diamond comparison once its source and evaluator are
validated and its measured quote fits the cap. Add complete IFBench and MuSR runs
only where their evaluators and costs are admitted, disclosing previously exposed
records separately. Preserve all ten target rows: this initial tranche does not
replace the full-suite objective. Quote MMLU-Pro and the remaining math, coding,
long-context, factuality, tool-use and repository-repair workloads from validated
implementations before expansion. If a complete run does not fit, label any sample
explicitly and do not launch an unbudgeted full run.

Report absolute accuracy, paired improvement with uncertainty, failure modes,
actual Jev contribution, latency and total system cost. Use development failures
to choose the next architecture iteration and fresh evidence to test it; retain
all primary results and document findings in the research record and manuscript.


## R27 execution update — 2026-09-24

The owner has authorized proceeding. The [new runtime plan](benchmark-execution-v2-plan.md)
and [GPQA task protocol](gpqa-diamond-execution-v1.md) are recorded before fresh
inference. An 18-case exposed engineering pilot is now running on one bounded
L40S; this is not yet a new full-benchmark result. Local checks pass 597 tests.
All 94 completed original-Granite records pass independent token/prefix checks;
cache/zero-gate checks pass and all 18 Jev receipts are valid with no retries.
Larger-model completion, final audit and pilot cost reconciliation remain pending.

GPQA's complete private source has 198 unique questions. Preserve two repeated
distractors, and report two manually exposed public-demonstration overlaps apart
from the 196 untouched cases. All candidate inputs fit the 16,384-token runner
ceiling across all three tokenizers: GPQA maxima 2,816/2,808/2,796; IFBench
552/538/286; MuSR 1,556/1,630/1,534; AIME 396/395/381. These are input
checks, not inference or performance measurements.

[Short-task preparation](full-short-tasks-admission-v1.md) preserves all 300
IFBench prompts and validates strict/loose evaluation on empty and nonempty
fixtures without errors. Its untouched subset is 288. Narrative-only clustering
finds 26 exposed/related MuSR cases, leaving 730 untouched among 756; the story
heuristic and limitations are explicit. All 30 AIME inputs are prepared, pending
final source/evaluator admission. No new quality score is implied.

MMLU-Pro's full five-shot run, long-context admission, an independently validated
SimpleQA judge, isolated LiveCodeBench execution, full BFCL tools and a fixed
SWE-bench agent still have separate work/cost requirements. The ten-row contract
remains intact; no missing task is substituted or averaged away. The original
$110 cumulative authorization is unchanged.
