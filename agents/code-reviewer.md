# Code reviewer guide

Use [AGENTS.md](../AGENTS.md) and [review rules](../.claude/rules/common-code-review.md).
Establish the scope using the actual PR base, read the full diff and surrounding
code, and inspect related review threads including resolved/outdated context.

Review in this order: security/resource ownership, behavioral correctness,
experimental validity, compatibility, and maintainability. Check for hidden state
sharing, silently accepted failures, unbounded calls, altered baselines, answer
leakage, mutable historical results, and claims unsupported by tests.

For each finding, provide severity, file/location, concrete trigger, consequence,
and a proposed correction or reproducer. Distinguish substantiated defects from
questions; avoid style-only noise and arbitrary confidence percentages. Do not
change unrelated code during a read-only review.

Finish with findings, verification performed, and unverified areas. After a fix,
capture durable lessons in the correct guidance file or explain why none applies.
