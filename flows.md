# Flow and regression catalog

Use [the development workflow](docs/development-workflow.md) and
[test guidance](agents/tdd-guide.md) to choose validation for changed behavior.
Existing test references are evidence of present coverage, not a claim that every
future edge case listed below is already tested.

| Flow | Contract and failure cases | Current evidence / suitable validation |
| --- | --- | --- |
| Learned internal feedback bridge | Zero-output parity; new adapter gradients only; exact draft prefix; real/constant matched training; source/data freeze; selection before fresh test; shuffled feedback and original weight preservation | [Mechanism tests](tests/test_learned_feedback_bridge.py), [study tests](tests/test_learned_feedback_study.py), [artifact tests](tests/test_learned_feedback_audit.py), [plan](research/learned-feedback-bridge-plan.md) |
| Jev-gated natural-draft repair | Explicit gate-zero identity; frozen base gradients; exact draft tokens; separate targets and feedback; matched seed training; locked selection; API unknown-charge stop | [Mechanism tests](tests/test_gated_repair.py), [execution tests](tests/test_gated_repair_execution.py), [R25 plan](research/gated-repair-plan.md) |
| Local semantic-feedback admission | Fresh exact Granite drafts; reference-free focused claim judgments; constructed and natural errors separate; one paid attempt; independent oracle and receipt/token reconstruction | [R21 capability tests](tests/test_semantic_feedback.py), [audit tests](tests/test_semantic_feedback_audit.py), [protocol](research/semantic-feedback-plan.md) |
| Blinded semantic evaluation | Independent judge must pass semantic fixtures before test generation; allowlisted anonymous packets exclude treatment/scorer metadata; duplicate answers share grades; malformed/capped judgments remain unresolved; freeze grades before joining arms | [R20 tests](tests/test_semantic_evaluation.py), [protocol](research/semantic-evaluation-plan.md), [pipeline](research/iterations/semantic_evaluation/pipeline.py) |
| Contributor setup | Core installation/imports without torch, GPU, key, or private helper; optional extras explicit | [CI](.github/workflows/checks.yml), package build, documented install and CLI help |
| Baseline generation | No Jev credential read or provider call; original model remains frozen | [controller tests](tests/test_controller.py), [backend tests](tests/test_transformers_backend.py), CLI smoke when backend changes |
| Candidate continuation | Exact accepted IDs feed the next step; discarded branches stay isolated; whitespace/Unicode decoding stays faithful | [controller tests](tests/test_controller.py), [backend tests](tests/test_transformers_backend.py), [two-sentence trace](reports/2026-09-20-granite-smoke/continuation/runs.jsonl) |
| Experimental evidence attention | Exact source-token offsets, selected GQA query heads, causal/query locality, frozen weights, no-op identity and exception cleanup; no cached/concurrent serving | [hook tests](tests/test_evidence_attention.py), [runtime tests](tests/test_evidence_runtime.py), [independent audit](tests/test_evidence_audit.py), [completed study](reports/2026-09-21-evidence-attention/README.md) |
| Adaptive cached research attention | Exact cached prefixes and query positions; head-specific biases; fallible-prefix relevance refresh; no output menu in open contracts; unchanged weights and fixed framing; serial execution only | [capability and full-flow tests](tests/test_adaptive_attention.py), [injection/contract tests](tests/test_adaptive_injection_audit.py), [frozen method](reports/2026-09-22-adaptive-attention/method.md), [precision amendment](research/adaptive-attention-fp32-amendment.md) |
| Selective research attention | Native pilot/cache retained on skip or provider failure; successful calls restart separately; phase boundaries and local mass conservation; exact call/branch provenance; serial only | [mechanism tests](tests/test_selective_attention.py), [runtime and cache checks](tests/test_selective_attention.py), [completed method](reports/2026-09-22-selective-attention/method.md), [offline replay and accounting](reports/2026-09-22-selective-attention/budget-frontier.md) |
| Benefit and sufficiency research | Native prefill features decide optional dispatch; Jev separately scores relevance and evidence sufficiency; source or existing instruction attention changes while Granite owns every final token | [R19 tests](tests/test_benefit_sufficiency.py), [disk round-trip regression](tests/test_sufficiency_controls_v2.py), [bounded audit portability and rejection tests](tests/test_benefit_audit_portability.py), [prospective protocol](research/benefit-sufficiency-plan.md), [completed report](reports/2026-09-22-benefit-sufficiency/README.md) |
| Single-prefill research attention | Observe native layer 18 once; optional Jev call before layer 19; preserve lower cache, one prefill and exact branch tokens; drain cancelled workers before releasing shared hooks; reject nested old/new scopes | [mechanics and ownership tests](tests/test_boundary_attention.py), [cohort/selection/audit tests](tests/test_boundary_study.py), [method and timing definitions](reports/2026-09-22-boundary-attention/method.md), [descriptive diagnostics](tests/test_boundary_outputs.py) |
| Experimental logit checkpoint | Full-vocabulary mass and bounded KL; zero bias reproduces native tokens; scores bind to exact prefix/model; provider failure/cancellation commits nothing | [bias tests](tests/test_logit_bias.py), [live-flow tests](tests/test_live_logit_checkpoint.py), [real-checkpoint report](reports/2026-09-21-logit-guidance/README.md) |
| Jev evaluation | Relevant evidence supplied explicitly; references withheld; malformed/missing/nonfinite judgments are errors | [client tests](tests/test_jev.py), scoped synthetic live check for changed API/prompts |
| Selection and EOS | Thresholds enforced; empty EOS checks completion; empty initial answer and premature end cannot pass by default | [controller tests](tests/test_controller.py), [EOS regression](tests/test_jev.py) |
| Rejection and budgets | Retry same prefix with bounded work; count discarded/padded work and HTTP attempts; keep partial result/status | [controller tests](tests/test_controller.py), new boundary tests for affected counters |
| Provider failure | Classify 429/529; honor Retry-After; timeout may be billed; no silent unscored fallback | [client tests](tests/test_jev.py), fake transport negative paths |
| Benchmark recording | Unique cases, no reference leakage, fresh output path, exact raw traces and summary; failed/incomplete runs retained | [benchmark tests](tests/test_benchmark.py), inspect CLI output and recompute summaries for changed artifacts |
| Reasoning search | Complete step/final boundaries; final without EOS; duplicate scoring once; saved sibling restores exact IDs; budgets never reset | [reasoning tests](tests/test_reasoning.py), [framed backend tests](tests/test_transformers_backend.py) |
| Reasoning scoring and CLI | Whole-prefix validity; distinct step/final rubrics; baseline without key; exact prompt saved; errors retain a stopped trace | [scorer tests](tests/test_reasoning_scorer.py), [CLI tests](tests/test_reasoning_cli.py), scoped live mechanism check |
| Reasoning cancellation | Signal model worker, drain before releasing request ownership; no late final commit; unknown remote usage explicit | [cancellation and deadline tests](tests/test_reasoning.py) |
| Proposal prompt and oracle evaluation | Styles preserve custom system/problem; no example/reference leakage; oracle checks conjunction, cycles, explicit negatives, and recorded problem identity; missing runs retained | [prompt tests](tests/test_reasoning_prompts.py), [experiment tests](tests/test_proposal_probe.py), [frozen protocol](docs/proposal-generation-experiment.md) |
| Fixed final verdict | Code supplies all three labels; Choice response validated; original evidence authoritative; no generated final label needed; uncertainty/errors are not UNKNOWN; preserve original token path and total budgets | [verdict tests](tests/test_fixed_verdict.py), [client tests](tests/test_verdict_scorer.py), [CLI tests](tests/test_fixed_verdict_cli.py), [protocol](docs/fixed-verdict-experiment.md) |
| Selective internal repair and independent readout | Exact native retention without repair work; gate/trace/prefix reconstruction; paid-attempt accounting; known full-option forms and conflicting finals | [Runtime tests](tests/test_selective_benchmark_runtime.py), [audit tests](tests/test_selective_admission_audit.py), [prospective readout regression](tests/test_choice_readout_v2.py), [frozen admission](research/selective-benchmark-admission-plan.md) |
| Completed-system offline audit | Require all nine Granite systems and full denominators; preserve partial Qwen and frozen graders; verify tokens/weights/selection/receipts; export aggregates only | [Scope and exclusion tests](tests/test_completed_granite_audit.py), [protocol](research/completed-granite-audit-v1.md), [completed report](reports/2026-09-25-completed-granite/README.md) |
| Documentation changes | Entrypoints discover rules, links remain local/valid, commands are portable, historical reports untouched | [AI-docs tests](tests/test_ai_docs.py), `uv run --no-sync python scripts/check_ai_docs.py` |
| Controlled reasoning evaluation | Unguided candidates receive no intermediate Jev calls; same final Choice, source/label oracle checks, one theory per problem, missing-run denominators, no replay of started jobs | [unguided tests](tests/test_unguided_verdict.py), [data tests](tests/test_proofwriter_data.py), [runner tests](tests/test_controlled_study.py), [protocol](docs/proofwriter-experiment.md) |
| Generator-owned final answer | Jev sees only intermediate frames; the final is generated by Granite with exact retained tokens; all-rejected steps still permit reserved model final generation; no classifier substitution | [controller tests](tests/test_generated_answer.py), [data/analysis tests](tests/test_generated_study.py), [protocol](docs/generated-answer-experiment.md) |
| Common syntax and constrained final labels | Every semantic alternative is available regardless of reference truth; original model probabilities choose final labels; separate final work reserve survives exhausted reasoning; exact token traces reconstruct | [grammar tests](tests/test_claim_grammar.py), [runtime tests](tests/test_structured_runtime.py), [controller tests](tests/test_structured_controller.py), [independent audit](tests/test_structured_audit.py), [V2 protocol](research/structured-study-v2-protocol.md) |
| Durable experiment spending | Reserve maximum input cost before each single attempt; settle only known usage; unknown usage survives restart; concurrent spending leases and changed terms rejected | [budget tests](tests/test_experiment_budget.py) |

For future parallel scheduling, extend request ownership, lock/cache isolation,
timeout, and late-result coverage before implementation. Do not claim the
single-backend prototype validates concurrent serving. Run real inference only
when the changed behavior needs it and scoped resources/data are available.

## R28 repair selection and feedback

Use the [registered protocol](research/routing-feedback-plan-v1.md) and
[regressions](tests/test_routing_feedback.py): equal-count reference-free routing,
selected-only donor derangement, likelihood parity, failed-provider charge retention,
and exact prefix/hook/work admission before independent grading. Fresh shared
potential outcomes support policy comparisons, not measured deployment savings.

## R29–R30 localized repair and feedback pairing

The [R29 protocol](research/structured-correction-plan-v1.md) and
[mechanism tests](tests/test_structured_correction.py) cover slot memory, scoped
repair positions, cached/full agreement, preservation training and provider failure.
The [R30 protocol](research/feedback-pairing-plan-v1.md) and
[pairing tests](tests/test_feedback_pairing.py) additionally bind fixed checkpoints
to their published lineage, retain fresh case denominators, preserve score multisets,
reject changed prompts/tokens/charges and refuse manifests that relax the registered
limits or omit checkpoints. Offline policy replay does not measure skipped calls.


## R31 contextual memory (running; quality unknown)

See [proposal](research/contextual-memory-proposal.md). Exact original prompt and
native draft IDs become three question/field position sets. One frozen, unmodified
prefill captures block-19 states; the matched embedding control pools identical
positions. Neither path sees targets or reference labels. Duplicate/missing fields
use question-only memory. Returned tensors are detached; hooks are scoped and
removed on exceptions. This changes memory construction; R30 is completed and its source is preserved.

Regression: `uv run --no-sync pytest -q tests/test_contextual_memory.py` covers
Unicode alignment, original-token binding, reference rejection, world-context
sensitivity, matched pooling, frozen weights, invalid state and hook cleanup.
Nine focused memory/training tests and all 256 historical pinned-tokenizer
alignments pass. Actual Granite MPS context extraction, initial/off identity and
cached/full agreement pass on one historical training draft; trained-quality
comparisons remain unrun. `tests/test_contextual_training.py` additionally checks
matched initialization, memory ownership, native preservation targets, development
selection and refusal to overwrite an earlier training attempt.


The conditional [next-study draft](research/contextual-memory-study-draft.md)
also has a fresh-data capability check:
`uv run --no-sync pytest -q tests/test_contextual_data.py`. It checks balanced
splits, full independent graph replay and disjointness from R29/R30, and rejects
a reused R30 seed before model/API work. This does not admit a paid study.

The serial contextual candidate runner now records native drafts, exact-ID memory
tensors, matched adapter training and all 38 test outputs per case for the full
2-memory × 3-feedback × 2-seed design. Offline tiny-model end-to-end tests exercise
both the full comparison and a smaller scalar-only contract. Independent checks
reject substituted memory, feedback, weights, targets, update order and development
selection; interrupted preparation cannot silently repeat a native draft.
Regression: `uv run --no-sync pytest -q tests/test_contextual_runtime.py tests/test_contextual_bindings.py`.
These are engineering tests with a fake scorer, not live Jev or task-quality results.
The [registered protocol](research/contextual-memory-plan-v1.md), bounded CLI and
independent full-run auditor are implemented. Freeze source/inputs and run actual
CUDA admission before any new training. CLI preparation rejects insufficient budget,
changed lineage/source, input substitution and dirty source; execution preserves
failed attempts and performs no ambiguous API retry.
Regression: `uv run --no-sync pytest -q tests/test_contextual_contract.py tests/test_contextual_freeze.py tests/test_contextual_execution.py`.
The four primary comparisons use scalar as lead, chosen after R30 but before R31
inference; the structured-memory contrast and memory-by-feedback interaction remain
reported secondary analyses.

Actual R31 CUDA admission passed. The separate [audit correction](research/contextual-memory-audit-correction.md)
normalizes `cuda:0` to `cuda` in memory, preserves raw bytes and rejects non-CUDA or
other-device records. Regression: `uv run --no-sync pytest -q tests/test_contextual_audit_device.py`.
No frozen worker/source/protocol change is made; full quality audit remains pending.

## MuSR single-question preparation (unpaid; no quality result)

The [conditional design](research/musr-transfer-design-draft.md) preserves one public
question, numbered choices and exact native IDs. References stay in a separate map;
related exposed scenarios cannot enter the fresh test set. Duplicate choice text
requires an explicit number. One pooled memory/probability is repeated internally
with tested numerical single-slot equivalence. New generation limits and a distinct
repair instruction do not change R31 sources. Fresh caches, hook cleanup, frozen
extraction, sampling reproducibility and a one-attempt provider ledger are tested.

Regression: `uv run --no-sync pytest -q tests/test_musr_single_interface.py tests/test_musr_runtime.py tests/test_musr_feedback.py tests/test_musr_data.py`.
All 756 pinned-tokenizer alignments and the 742-case exposure-aware assembly pass.
These are synthetic-span/tiny-model/fake-provider checks. Actual MuSR model/API
admission, a final registered matrix and independent complete-run audit remain unrun.

The separate [mechanical admission](research/musr-mechanical-admission.md) compares initial/off logits and nonzero-branch cached/full logits on an exact single-memory prefix. Regression: `uv run --no-sync pytest -q tests/test_musr_admission.py`. Actual-device results must be recorded separately from the passing tiny-model fixture.

The candidate serial pipeline and record auditor bind complete native/blind/live/
constant/donor outputs to exact memory, fixed checkpoints, receipts and maximum
pre-dispatch reservations. Donors never share a scenario group. Label-side grading
separates indexed choices from duplicate-text sensitivity; uncertainty resamples
whole scenarios. Regression: `uv run --no-sync pytest -q tests/test_musr_pipeline.py tests/test_musr_audit.py tests/test_musr_analysis.py`.
These checks pass on a tiny EOS-only model and fake provider; the final study
wrapper and actual public benchmark run are not admitted by the helper tests.

The separate [native readability admission](research/musr-native-admission-v1.md)
now has twelve real exposed-case Granite/MPS outputs, no accuracy labels or Jev
calls, unchanged original weights and no length stops. The original v1 readout
accepted 11/12; the [tested v2 final-line correction](research/musr-readout-v2.md)
accepts 12/12 by offline replay, preserving the original evidence. This admission
does not establish public transfer or accuracy.

## R32a conditional public-task admission (implemented, not launched)

The [prospective bounded plan](research/musr-live-admission-v1.md) binds only twelve
previously exposed questions and both scalar-trained R31 memory types/seeds.
The [contract](research/iterations/musr_transfer/contract.py) refuses missing or
incomplete R31 evidence, undeleted owned resources, insufficient cumulative budget,
changed development-selected checkpoints, altered inputs/sources and symlinks.
The worker exclusively claims its output before loading a model or key and never
loads reference labels into inference. One original model and one larger model
run serially, with explicit model unload and a shared deadline.

The [comparator](research/iterations/musr_transfer/comparator.py) preserves the
pinned larger model's templates, supported token ceilings, declared sampling and
case-local seeds. Its cached/full mechanics, raw coverage, token strings, timing
and original-weight identity are independently reconstructed. The exposed-case
summary separates generator quality from Jev correctness judgments, retains every
invalid/unfinished output and reports fix/damage counts without significance claims.

Regression: `uv run --no-sync pytest -q tests/test_musr_contract.py tests/test_musr_comparator.py tests/test_musr_study.py tests/test_musr_completion.py`.
All eight wrapper/comparator tests pass, including a complete tiny-model/fake-API
flow with a simulated device gate. This fixture uses CPU tensors and cannot pass
the actual CUDA/dtype completion audit. The real twelve-case CUDA/Jev/larger-model
admission and any 730-case fresh evaluation remain unrun. R31's active freeze still
verifies unchanged. CLI help works via `uv run --no-sync python research/iterations/musr_transfer/study.py --help`.

Before the R32a freeze, an ordinary text-feedback arm was added to compare channels
using the same actual Jev probability. No adapter or extra request enters that arm.
The registered admission now plans 204 outputs and 12 requests; its full simulated worker
fixture produces 44 outputs and four fake requests. Exact native prefixes and the rendered
probability are independently checked. Regression also rejects nonfinite/invalid
probability inputs and changed text-feedback prompt tokens. This is a prospective
control addition; it changes no R31 execution or previously archived outcome.


## Completed R31 report reconstruction

[The report](reports/2026-09-26-contextual-memory/README.md) reconstructs 11,840 outputs,
832 receipts, 832 paired memories, 12,288 training-example passes and 1,536 updates from four
disjoint public archives. Use the corrected audit entrypoint on a disposable copy
of the reconstructed run; exact analysis replay passes. Original device metadata
and frozen sources are unchanged. All owned cloud resources are verified deleted.
The report preserves the native gain, zero added scalar-memory accuracy, stronger
constant-trained control, and correction/preservation trade-off. Both PNG figures
were visually inspected; a caption collision was corrected before publication.
The plotting command and pinned environment are in the report. Public transfer,
conditional dispatch savings and larger-model superiority remain unverified.
