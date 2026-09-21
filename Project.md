# Jev-guided decoding project

Build a reusable, inspectable inference controller that tests whether TypeSafe
Jev can improve language-model output by evaluating continuations **during**
generation. The first model is original IBM Granite 4.0 1B; the controller should
support additional backends/models through explicit interfaces and validation.

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

The current scope is frozen-weight inference, a Transformers adapter, Jev's hosted
API, and document-grounded fixtures. It does not merge neural networks, access
hidden reasoning, train weights, deploy a service, or publish an improved checkpoint.
Retained-cache scheduling and vLLM integration need their own design and evidence.

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
