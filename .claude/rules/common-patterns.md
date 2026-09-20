# Shared patterns

Keep public types, controller behavior, backend/scorer adapters, CLI/configuration,
tests, and docs aligned. Share provider infrastructure in the existing client:
credential loading, endpoint selection, response parsing, timeout/retry policy,
and usage accounting should not drift across independent flows.

Use explicit state ownership, bounded work, and observable outcomes. A late score
must apply only to the candidate prefix that produced it. A failed or partial run
must retain its status and known work; do not manufacture a clean success record.

For future persisted state or result format changes, preserve provenance and
backward interpretation; add a documented version/migration rather than rewriting
historical artifacts. See [Python patterns](python-patterns.md) and
[API design](../skills/api-design.md).
