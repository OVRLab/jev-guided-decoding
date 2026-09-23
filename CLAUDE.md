# Claude entrypoint and repository map

Read [AGENTS.md](AGENTS.md) first; it is the authority for planning, test-first
development, evidence, security, PR review, and preserving lessons. The
[development workflow](docs/development-workflow.md) defines executable checks.
Shared [rules](.claude/rules/) apply across coding assistants. Do not duplicate or
weaken their requirements in this entrypoint.

## Architecture

| Path | Responsibility |
| --- | --- |
| [types.py](src/jev_guided_decoding/types.py) | Requests, configuration, immutable candidates, results, backend/scorer protocols |
| [controller.py](src/jev_guided_decoding/controller.py) | Accepted prefix, candidate selection, budgets, retry/stop outcomes |
| [reasoning.py](src/jev_guided_decoding/reasoning.py) | Explicit frames, branch selection, deferred siblings, global resource budgets and cancellation |
| [framing.py](src/jev_guided_decoding/framing.py) | Frame parsing and versioned-by-source instruction/example prompt variants |
| [reasoning_scorer.py](src/jev_guided_decoding/reasoning_scorer.py) | Whole-prefix validity, new-step progress, final completion using shared Jev transport |
| [verdict.py](src/jev_guided_decoding/verdict.py) | Fixed typed verdict choices, reserved final-call budget, and direct-Jev classification control |
| [generated_answer.py](src/jev_guided_decoding/generated_answer.py) | Intermediate-only selection with a reserved, generator-owned final answer; framing tokens have separate provenance |
| [experiment_budget.py](src/jev_guided_decoding/experiment_budget.py) | Exclusive durable reservations before paid attempts; known-usage settlement and fail-closed spending |
| [Generated-answer audit](experiments/audit_generated_answers.py) | Independent reconstruction of final tokens, accepted prefixes, scoring phases, and resource counters |
| [jev.py](src/jev_guided_decoding/jev.py) | Credentials, typed questions, HTTP validation, bounded retries, usage |
| [Transformers backend](src/jev_guided_decoding/backends/transformers.py) | Frozen causal model, token generation, stopping, likelihood, device accounting |
| [benchmark.py](src/jev_guided_decoding/benchmark.py) | Dataset validation, lexical metrics, summaries |
| [cli.py](src/jev_guided_decoding/cli.py) | Configuration, generation/benchmark flows, trace output |
| [Evidence attention research](research/experiments/evidence_attention.py) | Scoped source-key biases within selected Granite attention heads; [full study](reports/2026-09-21-evidence-attention/README.md), separate from package controllers |
| [Adaptive attention research](research/iterations/adaptive_attention/runtime.py) | Serial retained-cache generation with head-specific biases and optional Jev refresh; [FP32 runner](research/iterations/adaptive_attention_fp32.py), [method](reports/2026-09-22-adaptive-attention/method.md), [extra injection/contract audit](research/diagnostics/adaptive_injection_audit.py) |
| [Single-prefill attention research](research/iterations/boundary_attention/runtime.py) | Native layer-18 observation and optional Jev request before layer 19; same retained prefill/cache, serial ownership; [method](reports/2026-09-22-boundary-attention/method.md), [frozen audit](research/iterations/boundary_attention/analyze.py) |
| [Benefit and sufficiency research](research/iterations/benefit_sufficiency/runtime.py) | R19 uses a local benefit predictor and separate Jev sufficiency judgment to select source or instruction attention; [protocol](research/benefit-sufficiency-plan.md), [static/shuffled supplement](research/benefit-sufficiency-controls.md). Granite owns every final token; a canned callback is not a Jev request. |
| [R19 corrected controls](research/iterations/sufficiency_controls_v2.py) / [portable audit](research/diagnostics/benefit_sufficiency_audit.py) | Explicit JSON tuple/list correction and bounded logarithm roundoff adapter preserve frozen sources, raw records and all other audit checks; [completed report](reports/2026-09-22-benefit-sufficiency/README.md). |
| [configs](configs/) / [data](data/) | Pinned experiments and fictional fixtures |
| [Blinded semantic evaluation](research/iterations/semantic_evaluation/pipeline.py) | R20 validates a separate Qwen judge, then generates fixed native/static/Jev arms and freezes anonymous grading before analysis; [protocol](research/semantic-evaluation-plan.md). Constructed validation is not independent human annotation. |
| [Local semantic-feedback admission](research/iterations/semantic_feedback/study.py) | R21 validates focused Jev judgments on exact Granite intermediate drafts before any conditional adapter training; [plan](research/semantic-feedback-plan.md), [reconstruction](research/diagnostics/semantic_feedback_audit.py). Admission does not measure final-answer improvement. |
| [tests](tests/) / [reports](reports/) | Offline checks and immutable experimental evidence |

The code is Python, with optional Transformers/PyTorch dependencies. The core
controller and Jev client must remain importable without them. Core CI needs no
GPU, provider account, personal skill, or model download. The inference backend
is optional and currently validated on Granite; compatibility with other models
requires separate evidence. A vLLM backend is not implemented.

## Role guides

Read the relevant guide as instructions; these files do not provision subagents.

| Task | Read |
| --- | --- |
| Planning or design | [planner](agents/planner.md), [architect](agents/architect.md) |
| Code or behavior changes | [tdd-guide](agents/tdd-guide.md) |
| Reviews | [code-reviewer](agents/code-reviewer.md), [python-reviewer](agents/python-reviewer.md) |
| Credentials, provider calls, files, limits | [security-reviewer](agents/security-reviewer.md) |
| Build/import/dependency failures | [build-error-resolver](agents/build-error-resolver.md) |
| Refactoring | [refactor-cleaner](agents/refactor-cleaner.md) |
| End-to-end validation | [e2e-runner](agents/e2e-runner.md), [flow catalog](flows.md) |

Use the task guides in [.claude/skills](.claude/skills/) for more detailed test,
API, security, or evaluation work. They are repository documents; do not assume
an agent host automatically installs or exposes them as callable skills.

## Current implementation constraints

- The Transformers adapter recomputes the accepted prefix between chunks and
  uses KV caching within a chunk; do not call that retained-prefix optimization.
  R16 bypasses that adapter's `propose()` method with its own serial cached
  `Session`; new relevance affects subsequent computation, not old cached states.
- `JevScorer` returns optional relevance for empty EOS; `None` means unasked, not zero.
- `all_rejected` may retain a correct but uncompleted prefix. API failure is a
  separate outcome with potentially unknown usage; do not rewrite either as success.
- Reasoning results return only the final frame body in `text`; partial steps are separate.
  `final_jev` leaves intermediate steps unjudged; it does not invent passing scores.
- `fixed-verdict-v1` has a code-rendered Choice label and separate reasoning outcome;
  its Granite token path does not encode that final label. UNKNOWN is distinct from
  low confidence, budget stops, provider errors, and cancellation.
- Padded decode slots and accepted output tokens measure different things.
- Device sampling, API scores, and latency may vary despite fixed seeds/version IDs.
- MPS allocation snapshots are not peak-memory measurements.
- Use [Jev guidance](docs/JEV.md) before modifying request shapes or interpreting scores.

For guidance changes, run `uv run --no-sync python scripts/check_ai_docs.py`.
