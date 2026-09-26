# Ten-benchmark evaluation contract — version 1

Recorded 2026-09-23 for the [north star](north-star.md). This fixes the task list
and reporting rules. It is **not a claim that ten evaluators are installed or
that a final run is ready**. Revision observations below are source-discovery
pins; final input/evaluator/environment hashes require a separate admitted run
manifest. Changes require a versioned rationale before observing relevant scores.

## Primary metrics and admission status

All primary quality metrics are fractions multiplied by 100. No scores from
model cards enter our comparisons. Run every compared generator on identical
problems, reference evaluator, tool access and declared resource profile.

| Task | Primary score / unit | Current admission and remaining work |
| --- | --- | --- |
| MMLU-Pro | Generated-answer accuracy / question | Pinned public validation diagnostic implemented; full test adapter needs official five-shot prompts/extractor parity, subject coverage and option policy. |
| GPQA Diamond | Accuracy / question | Dataset metadata accessible; HF access is gated. Confirm account access/terms, pin Diamond selection and option shuffle before loading final examples. No gate bypass. |
| AIME 2026 | Numeric pass@1 / problem | Public source located; official numeric extraction, sampling repetitions and small-sample uncertainty need admission. GSM8K training is the R23 development proxy, not this task. |
| LiveCodeBench | Code generation pass@1 / problem | Public source located; freeze explicit release and date window, runner style and official test environment. Isolated execution, no network/credentials; hidden tests unavailable to the generator. |
| IFBench | Strict prompt success / prompt | R23 uses pinned upstream strict and loose evaluators; full-set adapter/environment validation remains. Always also show loose score, which the paper reports. Semantic usefulness is separate from constraint satisfaction. |
| MuSR | Accuracy / narrative problem | Pinned zero-shot diagnostic implemented, with three families. Full protocol needs official prompt/extraction parity; cluster shared narratives if any. |
| LongBench v2 | Accuracy / question or shared document cluster | Source located; audit native context support and full input token lengths for every model before launch. A short-context subset cannot substitute for the full task. No silent truncation. |
| SimpleQA Verified | Correct fraction / question | Source located; blind independent correctness/incorrect/abstention judge needs calibration against actual outputs and adjudication. Report all three fractions and official aggregate. Closed book, no browsing. |
| BFCL v4 | Official overall accuracy / official category/session weighting | Official implementation located; freeze v4 categories, schema, parser, stateful tools and official weighting. Tool result provenance and identical scaffold required. |
| SWE-bench Verified | Resolved fraction / issue, clustered by repository | Public 500-task set located; needs pinned agent scaffold, repository/container commits, identical tool/token/time budgets and official tests. This is a system benchmark. |

Do not replace unavailable tasks with easier tasks based on observed quality. An
unavailable evaluator produces an explicit missing cell. An unavailable task does
not become a zero quality score; a planned attempted problem that fails/times out
stays in that task's declared denominator under its frozen failure policy.

## Source inventory

Public metadata inspected on the recording date; license labels are upstream
metadata, not a relicensing determination. Code and underlying task assets can
have distinct terms. In particular, metadata `cc` alone does not resolve the
specific rights of all LiveCodeBench contest assets.

| Dataset / source | Observed immutable revision | Access / dataset terms |
| --- | --- | --- |
| [TIGER-Lab/MMLU-Pro](https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro) | `b189ec765aa7ed75c8acfea42df31fdae71f97be` | Public; MIT |
| [Idavidrein/gpqa](https://huggingface.co/datasets/Idavidrein/gpqa) | `83022cefff930aea54f654c0b282e74b9eeda5c6` | Automatic gate; CC BY 4.0 metadata |
| [math-ai/aime26](https://huggingface.co/datasets/math-ai/aime26) | `79037aebdb6580008fb960d17cb21fd3099083e3` | Public; Apache-2.0 metadata; inspect underlying problem attribution |
| [livecodebench/code_generation_lite](https://huggingface.co/datasets/livecodebench/code_generation_lite) | `0fe84c3912ea0c4d4a78037083943e8f0c4dd505` | Public; `cc` metadata; asset terms and exact window pending |
| [IFBench source/data](https://github.com/allenai/IFBench) | `1c40f0c10d9b5c5c2f10a175a28007ebb64f7f4d` | Public; Apache code, ODC-BY-1.0 data and source conditions |
| [TAUR-Lab/MuSR](https://huggingface.co/datasets/TAUR-Lab/MuSR) | `7c365b439a222150f317764d4f16ae6c96d7d94a` | Public; CC BY 4.0 |
| [THUDM/LongBench-v2](https://huggingface.co/datasets/THUDM/LongBench-v2) | `2b48e494f2c7a2f0af81aae178e05c7e1dde0fe9` | Public; Apache-2.0 metadata |
| [google/simpleqa-verified](https://huggingface.co/datasets/google/simpleqa-verified) | `0dc97e0d28d8233463e005cdc4475cc2a13ba2dc` | Public; MIT |
| [BFCL source](https://github.com/ShishirPatil/gorilla/tree/main/berkeley-function-call-leaderboard) | `6ea57973c7a6097fd7c5915698c54c17c5b1b6c8` | Public code located; v4 data/component license audit pending |
| [princeton-nlp/SWE-bench_Verified](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified) | `c104f840cc67f8b6eec6f759ebc8b2693d585d4a` | Public; card API has no license field; inspect dataset and individual repository terms |

Evaluator discovery revisions: [MMLU-Pro](https://github.com/TIGER-AI-Lab/MMLU-Pro)
`f418b116db00b065c2aea046518d8fcf74d39872`,
[GPQA](https://github.com/idavidrein/gpqa)
`56686c06f5e19865c153de0fdb11be3890014df7`,
[Inspect AIME](https://github.com/UKGovernmentBEIS/inspect_evals)
`e3402e36c6c1c161797a8b8e7ebbffca05e47fea`,
[LiveCodeBench](https://github.com/LiveCodeBench/LiveCodeBench)
`28fef95ea8c9f7a547c8329f2cd3d32b92c1fa24`,
[MuSR](https://github.com/Zayne-sprague/MuSR)
`b1f4d4168a9cfc6760e8b74d728e4516023dfaa5`,
[LongBench](https://github.com/THUDM/LongBench)
`2e00731f8d0bff23dc4325161044d0ed8af94c1e`,
[SWE-bench](https://github.com/SWE-bench/SWE-bench)
`02e7a74ffd0b707aab73d203fe87bdc7c76afc8e`.
These are retrieval pins, not claims of evaluator execution or correctness.

## Development, validation and final boundaries

R23's [manifest](protocols/public-baseline-v1/manifest.json) and
[IDs](protocols/public-baseline-v1/cases.json) define the initial consumed
**development** set. MMLU-Pro's public validation and GSM8K's training split
supply development. Twelve MuSR and twelve IFBench source-test items are also
explicitly consumed for development; remove their IDs and content duplicates
from any future untouched holdout. Report a full-source rerun as partly exposed.
No final AIME, GPQA, coding, LongBench, SimpleQA, BFCL or SWE problem was used in
R23 generation. Merely seeing repository metadata is not task inference.

**Split-admission clarification after R24 inspection, 2026-09-23:** MuSR murder
cases 212 and 213 share a scenario but differ in evidence and reference answer.
Future untouched splits must also exclude related scenario variants and use
story clusters where appropriate. Exact ID/content deduplication alone is
insufficient. This clarifies the pending split admission; it changes no recorded
R23/R24 input, primary metric, threshold, score or final-suite result.

Before architecture selection, freeze a separate validation cohort, ID/content
hash exclusions, deduplication procedure and query budget. After selection, lock
final inputs and run settings. Preserve task failures, all candidates searched,
and validation-driven decisions. Public benchmarks may have pretraining
contamination; disjoint project splits do not establish contamination freedom.

## Scorecard and comparisons

Publish ten rows per named model, showing numerator/denominator, primary score,
uncertainty, data/evaluator revisions, model revision, mode, output ceiling,
actual tokens, latency, hosted calls/cost, truncation and operational failures.
The equal-benchmark mean is available only after all ten primary cells satisfy
the same frozen contract. Also report the eight direct tasks and two agent tasks
separately. Do not average just successful/available tasks into a ten-task result.

Use paired problem/document/session/repository resampling as appropriate; keep
repeated samples within problem clusters. Aggregate only after each benchmark's
primary score is calculated. Predeclare the family of per-benchmark superiority
tests and multiplicity correction before a confirmatory run. Small development
intervals are descriptive and cannot certify larger-model superiority.

Original 4.0-1B remains the anchor. The ladder is 4.2-3B, 4.2-8B (first proposed
whole-suite target), 4.2-30B and Qwen3.8-27B. Native quality and matched total
cost/latency are separate views. Jev's hosted resources count; its unknown
parameter count prevents a claim about fewer total system parameters.

R23's [costed run plan](benchmark-baseline-plan.md) fits the existing $50 cumulative
cap. Full ten-task evaluation, agent tasks and larger-model replication have no
verified total quote yet; use observed throughput/context lengths to estimate
those stages before allocating compute. The current work does not authorize an
increase or assert that the whole research program fits the remaining amount.

## Executable scorecard guard

[The composer](evaluation/scorecard.py) accepts two named systems and completed
full-task cells, each carrying benchmark, 0–100 primary score, scope/status,
shared task-contract digest, dataset/evaluator revision and immutable system
revision. For a compound model, that system revision identifies the complete
checkpoint/controller/Jev-version configuration, not just Granite's weights.

It rejects development scores, duplicates, incompatible task contracts, invalid
numbers and a system that changes checkpoint between tasks. Missing tasks remain
visible, and no ten-task mean or paired mean difference is emitted until all ten
cells exist. Direct/agent subgroup means have the same completeness rule.
Aggregation alone never sets `superiority_established` true; inference needs the
independent statistical/replication requirements above. It does not replace the
per-task evaluator admissions or verify an operator's provenance assertions.

```bash
uv run --no-sync python research/evaluation/scorecard.py \
  --records results/admitted-full-task-cells.json \
  --models native guided --output results/ten-task-scorecard.json
```

The input is a JSON list. Required keys per cell: `model`, `benchmark`, `score`,
`scope` (`full`), `status` (`complete`), `contract`, `dataset_revision`,
`evaluator_revision`, `model_revision`. R23 development results cannot populate
these cells. Its initial final-scorecard state is deliberately empty.
