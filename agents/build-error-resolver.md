# Build and dependency error guide

Use [AGENTS.md](../AGENTS.md) and [workflow commands](../docs/development-workflow.md).
Read the actual failure and exit status, inspect the owning dependency/import/config,
and make the smallest correction. Do not mix an architecture rewrite into a build fix.

Distinguish missing optional extras, unsupported Python/device versions, packaging
omissions, and real regressions. Keep `pyproject.toml`, `uv.lock`, documented extras,
and CI aligned. Do not delete lockfiles, disable failing tests, or broadly upgrade
dependencies as a first response. Preserve the user's working environment.

Rerun the original failing command and affected tests, then build the package when
packaging/dependencies changed. Report the verified interpreter and remaining
platform limitations; do not claim a passing core build validates GPU inference.
