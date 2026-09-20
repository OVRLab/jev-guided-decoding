# Security review workflow

Use [AGENTS.md](../../AGENTS.md), [SECURITY.md](../../SECURITY.md), and the
[Python security rules](../rules/python-security.md). This is a portable reading
guide, not an installed scanner or a requirement for private tools.

## Review the changed boundary

1. Identify data sources, credentials, provider destinations, generated artifacts,
   and code-execution or spending paths. Follow nested errors and trace metadata.
2. Check validation and ownership before dispatch: finite limits, explicit endpoint,
   allowed data, per-run state, and supported model-loading behavior.
3. Inspect completed responses separately from indeterminate transport failures.
   Honor provider retry policy and bounded deadlines; preserve potentially unknown
   usage and do not silently replay a possibly billed timeout.
4. Verify the negative path with fake inputs/transport and redacted errors. Test
   the actual boundary changed, rather than importing unrelated web-app checklists.
5. Review tracked files and public artifacts, including fixtures and examples, for
   private content and credentials; a passing unit suite does not prove no secret leaked.

For future concurrency or durable jobs, define exact ownership of leases, budgets,
completion, and cancellation before implementation. Do not release or reuse a claim
while a dispatched request can still finish ambiguously. Record such work as planned
until it exists; today's CLI is not a multi-tenant serving system.

If exposure is confirmed, stop further disclosure and coordinate remediation with
the owner. Keep the issue record redacted and avoid public exploit details. Do not
assume secret rotation, a private reporting channel, or a security scan happened.
