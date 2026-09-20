# Code review rules

Read [AGENTS.md](../../AGENTS.md) and [code-reviewer](../../agents/code-reviewer.md).
Review after code changes and before PR handoff. Establish the full diff against
the actual base, read surrounding call sites, and inspect complete review context.

Prioritize reproducible defects: incorrect tokens/decisions, leaked credentials,
unbounded requests, corrupted results, misleading metrics, and hidden coupling.
Distinguish mandatory correctness fixes from style preferences; group duplicate
findings and identify the concrete trigger and consequence.

Block unresolved critical/high correctness or security issues. For medium issues,
state the impact and disposition rather than implying an arbitrary numerical
confidence proves a finding. Do not label missing automated review as approval.

For P1/P2 fixes, reproduce the failure, add the regression, fix it, and decide whether
to update durable guidance. Explain when no general lesson is needed. Preserve
the [review learning loop](../../AGENTS.md) without pasting raw comment history.
