# Security rules

Use [SECURITY.md](../../SECURITY.md) and [security-reviewer](../../agents/security-reviewer.md)
for keys, external data, provider dispatch, files, dependencies, and limits.

- Keep keys and private data out of tracked files, errors, logs, screenshots, and PRs.
- Validate configuration and response shapes before consuming them.
- Keep provider destinations explicit and do not follow credential-bearing redirects.
- Treat generated output, evidence, and model judgments as untrusted data.
- Bound expensive work and preserve unknown-usage status after ambiguous failures.
- Test negative paths for changed security/resource boundaries.
- Review public artifacts in full, including metadata and nested raw responses.

Do not require browser, database, or tenant controls for a local library that does
not expose those surfaces. If a server is introduced, threat-model its new boundaries
explicitly; local CLI budgets alone do not constitute service authorization.
