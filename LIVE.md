# Verified implementation inventory

[R20 blinded evaluation — completed](reports/2026-09-23-semantic-evaluation/README.md):
native/Jev Qwen-judged scores are **30.21%/42.71% authored**, **74.17%/73.33%
Hotpot** and **61.67%/67.50% SQuAD**. Only the authored primary contrast excludes
zero; no domain establishes superiority over static instruction steering. The
blind review agrees on 21/24 packets and exposes answer-completeness errors in the
judge, so reliable semantic improvement and architectural superiority remain
unproven. All 1,584 generations, 30,112 final tokens and 528 successful Jev requests
pass reconstruction; public replay matches. All cloud resources are deleted.
Estimated new cost is **$2.32**, cumulative **$32.55/$50** before tax/network.
See the [evaluator failures](reports/2026-09-23-semantic-evaluation/transfer-diagnostics.md)
and [paper draft](research/paper-draft.md#79-r20-blinded-semantic-evaluation-of-fixed-attention-interventions).

[R19 completed study](reports/2026-09-22-benefit-sufficiency/README.md) tests a local
benefit predictor and independent Jev sufficiency at the retained-prefill boundary.
Native/dual scores are **26.74%/43.06%** authored parser accuracy,
**27.68%/32.95%** Hotpot answer F1 and **25.44%/33.10%** adapted SQuAD F1.
The primary authored dual-minus-relevance interval excludes zero; the other five
primary intervals include zero. Material parser/F1 artifacts in saved answers
prevent claiming semantic improvement. Static instruction steering scores
**46.53%/32.90%/34.49%** without Jev; dual superiority is unestablished.
The learned gate uses **277/608** test requests (**54.44% fewer**) but has no
reliable advantage over random routing at matched within-domain call fractions.

All **7,312 successful outcomes**, **139,811 final tokens**, **1,824 exact branch
identities** and **1,068 successful Jev receipts** pass completed audits and public
replay. Granite owns every final token, with unchanged weights, one retained
prefill and no forced UNKNOWN spelling. A failed pre-generation supplement start
is preserved alongside separate serialization and floating-point audit amendments.
All **451 local tests** pass; the replacement GPU host passed its 449-test suite
before inference. Twelve real-checkpoint parity checks had zero logit/cache
difference. Both sequential L40S servers and their owned resources are verified
deleted. Estimated R19 cost is **$3.00**, cumulative **$30.23/$50** before tax/network.
This is completed research-branch evidence, not a released model or semantic
replication. R20, above, is the subsequent blinded evaluation.

[R18 completed study](reports/2026-09-22-boundary-attention/README.md).

**R18 completed:** the single-prefill gate raises authored accuracy from
**26.98% to 31.75%**, close to always Jev's **31.94%**, while saving **27.58%**
of requests. The exploratory selective-minus-native interval is **+4.76 pp
[1.79, 7.94]**. Hotpot native/always/selective F1 is **27.96% / 29.40% / 27.08%**;
SQuAD adapted F1 is **26.49% / 26.72% / 26.55%**. Primary routing intervals
include zero in all three domains, so reliable call selection is unestablished.

The gate uses **425/984 test requests**, saving **56.81% overall**, with one
prefill and zero discarded pilot tokens. Its domain call fractions are
72.42% / 18.33% / 6.67%; missing-evidence handling remains weak. Granite generates
every final token with unchanged weights and no required UNKNOWN spelling.
All **9,376 outcomes**, **184,889 final tokens** and **1,244 successful Jev
receipts** pass reconstruction; public archive replay reproduces the analysis.
There are zero provider failures. All temporary resources are deleted after
verified retrieval. New estimated cost is **$3.77**, cumulative **$27.23/$50**
before tax/separate network. This is research-branch evidence, with mixed external
quality, not a generally improved checkpoint or a serving-throughput benchmark.

R18 handoff verification: **435 tests passed in 6.89 seconds**, Ruff lint/format,
the 49-file guidance checker and source/wheel builds pass. All seven R18 figure
layouts were inspected; public archive reconstruction reproduces every main-audit
field except its timestamp. The review bot remains unavailable due to quota.

[R17 completed study](reports/2026-09-22-selective-attention/README.md).

**R17 completed:** Jev guidance raises authored free-text accuracy from
**28.77% to 33.13%**, and HotpotQA answer F1 from **25.23% to 28.76%**.
The primary 98.75% intervals include zero: **+4.37 pp [0.00, 8.93]** and
**+3.53 pp [−1.47, 8.58]**. Development selected the existing R16 policy;
new timing/conservation variants did not win that selection.

The live gates called on **every input**, saving no requests and adding pilot work.
In a separately registered **offline replay**, a development-frozen budget rule
uses 21.43% of calls on authored tasks for 31.55% accuracy, but only 25.00% Hotpot F1
at 18.50% calls. This is a limited routing signal, not measured deployment savings
or reliable transfer. All three replay budgets and negative findings are retained.
Natural abstention remains poor, and overall authored scores stay below the 50%
constant-abstention reference. Granite owns every final token; weights are unchanged.

All **8,364 development/test outcomes** pass token/input/source/weight and public
archive replay audits. **860 Jev attempts succeeded, with no provider failures**.
New estimated cost is **$3.77**, cumulative **$23.46/$50** before tax/separate
network; all temporary GPU, disk and network resources are deleted. No generally
superior architecture or trained model release is established.

At R17 completion, local verification: **415 tests passed**, Ruff lint/format, 49-file guidance
check and builds pass. Six standalone figures were visually checked; public archive
reconstruction reproduces every audit field except its timestamp.

[Previous R16 completed study](reports/2026-09-22-adaptive-attention/README.md):
**R16 interpretation:** constrained-task improvement is established within this
study; direct free-text performance regressed against matched R15, while dynamic
refresh and the primary HotpotQA contrast remain inconclusive.

All **16,120 main test outcomes** and **3,600 exploratory factorial outcomes**
are retained. On the new depth 1–6 constrained task, native Granite scores
**30.83%**, matched R15 **59.00%**,
and tuned Jev attention **72.00%**. The primary
tuned-minus-R15 contrast is **+13.00 pp [+8.67, +17.61]**.

Without an answer menu or required UNKNOWN token, open-explicit accuracy is
**27.33% native / 27.17% tuned**;
open-neutral accuracy is **26.17% / 21.50%**.
Refreshed versus static staged guidance changes accuracy by
**+0.42 pp [-3.33, +4.17]**. On 200 length-filtered HotpotQA questions,
direct answer F1 is **26.85% native /
29.67% tuned**, with primary contrast
**+2.82 pp [-1.35, +6.91]**. Primary intervals are 98.333%;
other comparisons are exploratory. These tasks and output contracts have separate
interpretations; historical R15 scores are from a different cohort and precision.

Granite generates every semantic token with unchanged weights; all arms use FP32.
The full report includes natural abstentions, answerable/missing breakdowns,
regressions, factor interactions, API failures, exact traces and three independent
audits. All temporary resources are deleted. New estimated cost is
**$8.52**, cumulative **$19.69/$50**
before tax/separate network charges. This is research-branch evidence, not a trained
checkpoint release or a general reasoning guarantee.

At R16 completion, the local inference suite passed **385 tests**. Core-only CI passes on
Python 3.11/3.12; optional inference tests are not represented by those CI jobs.
The original BF16 admission failure and prospective precision amendment are retained.

[R15 completed study](reports/2026-09-22-evidence-attention-refinement/README.md):
R15's fresh 600-world comparison scores **38.08% native Granite**, **47.33%
previous Jev attention**, and **68.42% refined Jev attention**. The paired primary
gains are +30.33 pp [26.67,34.00] versus native and +21.08 pp [17.92,24.25] versus
R14, using individual 97.5% intervals. The prespecified advancement criterion is
met. Lexical/prompt/shuffled comparisons are exploratory and favorable on this
primary cohort. Longer-chain challenge accuracy is only **41.67%**, below the
50% constant-UNKNOWN reference, so broad reasoning utility remains unestablished.

The complete schedule contains 34,777 records and 34,679 actual model forwards,
with two provider failures retained and no paid/model replay. Operational amendments,
including one after test start, are disclosed; the selected policy/test freeze and
weights stayed unchanged. All task cloud resources are deleted. New cost is about
**$1.90**, cumulative **$11.17/$50**. This is research
branch evidence, not a published trained checkpoint or unrestricted chat result.

Inventory introduced on 2026-09-20 by
[PR #1](https://github.com/OVRLab/jev-guided-decoding/pull/1); its GitHub status
records whether it has merged. Entries describe this checkout: on the work branch
they are changes under review, and on the default branch they are merged features.
No package or model publication is recorded. A merged feature is not automatically
a published release.

| Implemented in this checkout | Evidence |
| --- | --- |
| Generic controller with four selection modes and bounded outcomes | [controller](src/jev_guided_decoding/controller.py), [tests](tests/test_controller.py) |
| Jev client with typed validation and bounded retries | [client](src/jev_guided_decoding/jev.py), [tests](tests/test_jev.py) |
| Frozen Transformers backend and exact-token continuation | [backend](src/jev_guided_decoding/backends/transformers.py), [offline backend tests](tests/test_transformers_backend.py) |
| CLI, lexical benchmark, and pinned Granite configuration | [README](README.md), [config](configs/granite-4.0-1b.toml) |
| 12-case live smoke run plus separate two-sentence demonstration | [dated report and raw traces](reports/2026-09-20-granite-smoke/README.md) |
| Explicit step/final frames, exact-token search, deduplication, bounded resampling and backtracking | [implementation](docs/reasoning-controller.md), [controller tests](tests/test_reasoning.py), [scorer tests](tests/test_reasoning_scorer.py) |
| Reasoning CLI and final-only Jev control; baseline operation without credentials | [CLI tests](tests/test_reasoning_cli.py), [reasoning config](configs/granite-4.0-1b-reasoning.toml) |
| 16-run framed reasoning mechanism check: five verified backtracks, but no completed step-guided answers | [live report and all outcomes](reports/2026-09-20-reasoning-controller/README.md) |
| Opt-in worked proposal examples, fixed rule oracle, and a completion planner that excludes all prior attempts | [protocol](docs/proposal-generation-experiment.md), [prompt tests](tests/test_reasoning_prompts.py), [oracle tests](tests/test_proposal_probe.py), [completion tests](tests/test_proposal_completion.py) |
| 32 development batches and 48 separate evaluation attempts: step Jev 6/12 verdict matches, equal to greedy/likelihood; all UNKNOWN worlds unsolved | [full report, raw traces, and independent grades](reports/2026-09-20-proposal-generation/README.md) |
| Fixed final choices and direct-Jev control; separate generated-token/decision provenance, reserved budgets, and validated uncertainty/error outcomes | [implementation](src/jev_guided_decoding/verdict.py), [controller tests](tests/test_fixed_verdict.py), [client tests](tests/test_verdict_scorer.py), [CLI tests](tests/test_fixed_verdict_cli.py) |
| 18-run fixed-choice check: 6/6 verdict matches for both fixed mode and direct Jev, versus 2/6 existing step guidance; both UNKNOWN cases classified | [dated report and all evidence](reports/2026-09-20-fixed-verdict/README.md) |
| Intermediate-reasoning investigation: 16 fixed-candidate scorer calls and four generated-derivation runs | [follow-up report](reports/2026-09-20-reasoning-investigation/README.md), [proposed engine design](docs/reasoning-step-investigation.md) |
| Controlled-study runner, unguided/final-only fixed-choice controls, independently checked ProofWriter data and synthetic stress worlds | [protocol](docs/proofwriter-experiment.md), [runner tests](tests/test_controlled_study.py), [control tests](tests/test_unguided_verdict.py) |
| Nine-run ProofWriter development pilot on MPS: each executed arm matched 2/3 verdicts | [pilot report](reports/2026-09-20-proofwriter-pilot/README.md) |
| Twelve-run CUDA pilot on one L40S: all four executed arms matched 2/3 verdicts, without provider/backend errors | [CUDA pilot report](reports/2026-09-20-cuda-pilot/README.md) |
| Completed 2,400-job ProofWriter study and 96-job synthetic stress test; guided 84.5% versus direct Jev 84.7%, without demonstrated added accuracy | [final report, aggregate results, and integrity audit](reports/2026-09-20-controlled-study/README.md) |
| Separate controller keeps Granite as final answerer, scores intermediate steps only, and reserves final generation plus durable Jev spending | [replacement protocol](docs/generated-answer-experiment.md), [controller tests](tests/test_generated_answer.py), [budget tests](tests/test_experiment_budget.py) |
| Completed 3,600-job generated-answer study: no demonstrated accuracy gain; all final generations passed token-provenance audit | [final report, controls, intervals, and resource accounting](reports/2026-09-20-generated-answer-study/README.md) |
| Offline analysis of all 3,600 main and 48 development traces, checkpoint/source inspection, and persistent research register | [new aggregate report](reports/2026-09-21-architecture-reassessment/README.md), [analyzer tests](tests/test_trace_diagnostics.py), [research notebook](research/README.md) |
| Bounded full-distribution logit bias, isolated token selection, local-claim scoring and versioned critic pilots | [new report](reports/2026-09-21-logit-guidance/README.md), [bias tests](tests/test_logit_bias.py), [runtime tests](tests/test_logit_runtime.py), [controller tests](tests/test_logit_controller.py) |
| Asynchronous one-checkpoint scoring-to-token flow with no commit on provider failure/cancellation and a durable-budget requirement | [research interface](research/experiments/live_logit_checkpoint.py), [six offline flow tests](tests/test_live_logit_checkpoint.py); fresh hosted execution remains unverified |
| Four-prefix real-Granite replay check: changed probabilities, exact no-op identity, unchanged model state and all final-token provenance checks; no valid closing final frames | [mechanism artifacts](reports/2026-09-21-logit-guidance/mechanism-v1/summary.json), [full limitations](reports/2026-09-21-logit-guidance/README.md) |

The recorded smoke run used original Granite with zero trainable parameters.
Guided decoding averaged 3.71 seconds versus 1.10 seconds greedy, with no
established quality gain. One correct ending was rejected and misleading causal
wording was accepted elsewhere. These are historical small-sample findings,
not freshly rerun checks or a general accuracy estimate.

The [R13 report](reports/2026-09-21-structured-study/README.md) records the completed
seven-arm comparison: 6,300 planned jobs attempted, 6,299 completed and one
soft-step service failure retained. Direct/staged/likelihood/Jev accuracy is
42.67%/37.00%/35.44%/36.00%; none of the three adjusted Jev intervals excludes zero.
Independent audits match all 6,300 frozen prompts, all 6,299 completed token paths,
35,996 candidate grades and 10,798 accepted-claim grades. Zero bias reproduces all
900 staged paths, and all 3,600 initial-pool comparisons match. Both L40S deployments
and their task resources are deleted after verified retrieval. Cumulative estimated
spending at R13 completion was $8.49 before tax/separate network charges. R13 established no accuracy gain; the later R14 result is stated above.


## Not implemented or not demonstrated

The [controlled study](docs/proofwriter-experiment.md) specifies 200 distinct theories,
three seeds, four executed arms, and problem-level paired comparisons. Its expanded
offline suite passed 174 tests locally and on the GPU server before inference.
The [completed study](reports/2026-09-20-controlled-study/README.md) found no
demonstrated gain from intermediate guidance; 542/600 guided paths retained no
step. Conflicting output instructions limit interpretation of the derived
generated-answer controls. Remote Jev was used; colocated performance is unmeasured.
All temporary cloud resources were deleted after verified result retrieval.

The fixed-choice result answers a different question from whether Jev improves
Granite-generated answers. The owner authorized a replacement study with a $50
total budget. Its implementation has offline checks; its new development pilot and
fresh evaluation follow a separate protocol. The first pilot failed formatting;
the [corrected 48-job pilot](reports/2026-09-20-generated-answer-pilot-v2/README.md)
passed the admission gate, including an independent final-token audit and nine
changed intermediate selections. The [3,600-job evaluation](reports/2026-09-20-generated-answer-study/README.md)
is complete: math accuracy was 61.5% single, 67.8% likelihood, and 56.5% Jev;
logic was 52.7%, 52.8%, and 52.5%. The math decrease versus likelihood remained
below zero throughout its adjusted interval; other intervals included zero.
All 3,600 final generations passed the token audit, reproduced from local backups.
Jev retained no step in 572/600 logic runs. The 206-test local suite passed; raw
results were verified before the temporary server/disk/network resources were
deleted. Estimated compute, disk and Jev cost was $3.29 before tax and separate
network charges. Final-answer attribution is now an explicit invariant.

- vLLM extension or concurrent serving. The package proposal path recomputes
  prefixes; the separate R16 research runner retains an isolated request cache.
- Guaranteed semantic candidate diversity; deduplication currently uses exact token IDs.
- Neural fusion, training, changed model weights, or a new Hugging Face checkpoint.
- General mathematical reasoning improvement or a colocated/serving-throughput
  speedup; narrow held-out attention results are described above.
- Validated compatibility beyond the recorded Granite and tiny-model checks.
- A generally optimal hidden-layer mapping across tasks or models. R14–R16
  identify and test selected source-attention interventions on the recorded tasks.
  The [output-logit prototype](reports/2026-09-21-logit-guidance/README.md) is mechanically
  checked with replayed scores. R13 subsequently completed a fresh hosted seven-arm comparison without a
  demonstrated accuracy gain; its interrupted segment and bounded continuation
  are preserved separately. R12
  retains one actual-usage-unknown call at its full maximum charge; its original
  stopped protocol was not retroactively resumed or declared admitted.

Update this inventory when verified behavior changes, naming the PR/report and
keeping branch, merged, experimental, and released states distinct. Guidance-only
work is tracked in [the adaptation record](docs/ai-guidance-import.md).
