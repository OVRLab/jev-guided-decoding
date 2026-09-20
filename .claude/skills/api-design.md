# Python and provider API contract guide

Use for changes to backend/scorer protocols, CLI/JSON output, or the Jev client.
Read [AGENTS.md](../../AGENTS.md), [repository map](../../CLAUDE.md), and
[Jev contract guidance](../../docs/JEV.md). No public REST service exists today.

Keep request state, candidate identity, decisions, errors, usage, and completion
status explicit. Define how missing, empty, invalid, and partial values behave.
Validate external response values at runtime; annotations alone are not a contract.
Preserve raw model judgments and distinguish an unasked field from zero probability.

Centralize provider configuration, headers, parsing, retry classification, and
credential resolution in the shared client. Return stable local error categories
without leaking raw provider bodies or headers. Report attempted work separately
from successful responses and known token usage.

Maintain CLI help, examples, config, tests, and consumers together when a field or
behavior changes. Do not silently rename recorded fields or reinterpret old reports;
introduce a documented version/conversion when compatibility needs it. Preserve
append-only experiment provenance and no-overwrite outputs.

A future serving API needs its own versioned contract, authentication/resource
boundaries, cancellation semantics, and bounded concurrency. Do not add endpoint,
database, pagination, or web-framework machinery merely because this guide exists.
