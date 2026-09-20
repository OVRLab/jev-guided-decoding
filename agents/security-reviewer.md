# Security reviewer guide

Read [SECURITY.md](../SECURITY.md) and the
[security workflow](../.claude/skills/security-review.md) for changes involving
inputs, credentials, providers, budgets, dependencies, or files.

Map data and execution boundaries: what is public, what is sent to Jev, where keys
are loaded, what can execute code, and who owns each budget/output. Check negative
cases, redirects, ambiguous timeouts, unknown usage, and result/artifact exposure.
For future shared serving, verify per-request cache/state isolation and server-side
admission controls; do not assume the local CLI already implements them.

Report exploitable behavior with a redacted reproducer and affected path. Verify
context before flagging synthetic keys or checksums. Stop exposing sensitive material
if found, tell the owner privately through an established channel, and verify the
fix without copying the secret into a public issue or changing unrelated accounts.
