# Architect guide

Read [Project.md](../Project.md), [CLAUDE.md](../CLAUDE.md), and [AGENTS.md](../AGENTS.md).
Map responsibilities, data flow, and ownership before proposing new abstractions.

For a significant change, record its problem, current behavior, alternatives,
decision, trade-offs, validation, and unverified assumptions. Pay particular
attention to token identity, mutable caches, batched requests, cancellation,
late scores, resource ceilings, provider latency, and output provenance.

Prefer the existing controller/backend/scorer boundaries. Distinguish a local
prototype from serving integration and neural fusion. A vLLM proposal must identify
actual scheduler/cache extension points and measured benefit; putting an HTTP call
in per-token GPU processing is not an adequate design.

Avoid speculative services, queues, model training, or dependency changes that do
not solve the current problem. Generalize when another validated backend/model
creates a real requirement, and keep core imports independent of optional inference.
