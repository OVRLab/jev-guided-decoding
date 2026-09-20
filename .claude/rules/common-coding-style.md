# Common coding principles

Prefer simple, explicit control flow, cohesive modules, meaningful names, and
existing patterns. Introduce abstractions when repeated behavior justifies them;
avoid speculative serving frameworks while evaluating the controller.

Keep request/config/candidate values immutable where practical. Mutation must have
an explicit owner: run counters, trace accumulation, and a backend's local cache
can be mutable without exposing that state across requests or rejected branches.
Do not force expensive tensor copies merely to satisfy a blanket style rule.

Validate external inputs and outputs at boundaries. Preserve error context safely
and never turn a provider failure into a negative judgment or successful answer.
Keep CLI messages useful without exposing secrets or private payloads.

Split complex code when it improves reviewability, not solely to meet a line quota.
Use the repository's [Python conventions](python-coding-style.md), format/lint
configuration, and tests; do not introduce a second style system.
