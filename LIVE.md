# Verified implementation inventory

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

- vLLM extension, retained-prefix cache reuse between chunks, or concurrent serving.
- Guaranteed semantic candidate diversity; deduplication currently uses exact token IDs.
- Neural fusion, training, changed model weights, or a new Hugging Face checkpoint.
- Improved held-out answer quality, general mathematical reasoning, or GPU-server speedups.
- Validated compatibility beyond the recorded Granite and tiny-model checks.
- A validated hidden-layer mapping or an effective layer identified by experiment.
  The [output-logit prototype](reports/2026-09-21-logit-guidance/README.md) is mechanically
  checked with replayed scores; a fresh live hosted end-to-end logit trial and an
  admitted independent answer-quality study have not run. One provider failure
  retains unknown usage; no further paid dispatch occurs under that stopped protocol.

Update this inventory when verified behavior changes, naming the PR/report and
keeping branch, merged, experimental, and released states distinct. Guidance-only
work is tracked in [the adaptation record](docs/ai-guidance-import.md).
