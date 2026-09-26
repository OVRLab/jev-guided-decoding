# Jev-guided decoding project

Build a Granite–Jev inference architecture that substantially outperforms original
Granite across ten leading, diverse LLM benchmarks and beats explicitly named
larger models, including newer Granite and another model family. This is the
owner's north star, recorded 2026-09-23; it is not an achieved result. The initial
generator remains dense IBM Granite 4.0 1B.

The [north-star strategy](research/north-star.md) defines the candidate scorecard,
larger-model ladder, quality/resource comparisons and research sequence. Architecture
choices serve that objective. The reusable Python controller is the initial
experimental implementation; broader internal mechanisms and trained adapters are
research paths with separate evidence. Granite must own the generated final answer.

## Users and promise

Researchers need reproducible evidence of quality, failure modes, latency, and
cost. Developers need a Python library and CLI with clear outcomes and bounded
work. Open-source contributors need documentation and offline tests that work
without the maintainer's credentials, machine, paid tools, or private issue tracker.

The promise is an experiment that can be inspected and reproduced, not guaranteed
reasoning improvement. Negative results and verifier mistakes are valid findings.

## Architecture and scope

The backend proposes token continuations. A scorer evaluates their text and
evidence. The controller selects an eligible continuation or explicitly stops.
The CLI records inputs, decisions, counts, and results; the benchmark compares
guided behavior with generation controls. A separate [R14 research path](reports/2026-09-21-evidence-attention/README.md)
maps Jev source relevance into selected internal attention heads during constrained
answer generation. See [CLAUDE.md](CLAUDE.md) for paths.

The initial package scope is frozen-weight inference, a Transformers adapter, Jev's hosted
API, and document-grounded fixtures. It does not merge neural networks, access
hidden reasoning, train weights, deploy a service, or publish an improved checkpoint.
The R16 research path implements serial retained-cache generation and relevance
refresh. R17 adds conditional dispatch after a generated pilot; R18 moves that
decision before layer 19 inside a single prefill, using native attention features.
R19 tests a small fitted benefit predictor and separate evidence sufficiency, with
source or existing-instruction attention steering. Granite and Jev weights remain
unchanged; the fitted controller is a separate statistical model.
Concurrent serving, vLLM integration and performance of a colocated Jev deployment
still need separate design and evidence.

The package has an MIT license. External models, datasets, dependencies, and Jev
remain governed by their own terms; name their sources and preserve required notices.
All tracked artifacts must be suitable for public access.

## Success and decision criteria

First demonstrate correct continuation control and bounded failures. Then evaluate
on held-out cases with independent grading, several seeds, and comparable actual
budgets. Measure total latency, throughput, prefill/decode work, and API usage.
Optimize or add a serving integration when the measured trade-off justifies it.
Use [LAUNCH.md](LAUNCH.md) for scope, [LIVE.md](LIVE.md) for verified status, and
[FEATURE.md](FEATURE.md) for the next experiment; do not turn a roadmap into a claim.

## Authorized research extensions

The owner authorized [local semantic feedback and a learned internal bridge](research/semantic-feedback-plan.md). This research extension may train new adapter parameters after feedback admission, while preserving original Granite and Jev weights. It is separate from the initial frozen-weight package prototype and does not imply a released checkpoint.

The subsequent north-star direction adds broad benchmark transfer and named
larger-model comparisons as the main research outcome. R21/R22 are completed
mechanism/verifier studies, not evidence of that outcome. Preserve original
checkpoints and old protocols; register new training or architecture changes before
evaluation. The existing spending ceiling remains in force until explicitly changed.
