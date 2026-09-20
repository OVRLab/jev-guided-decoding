# Python coding conventions

Use Python 3.11-compatible syntax within the project's supported range, four-space
indentation, `snake_case` functions/modules, `PascalCase` classes, and
`UPPER_SNAKE_CASE` constants. Ruff owns formatting and linting; its configured
line length is 100. Check [pyproject.toml](../../pyproject.toml) before changing tools.

Use dataclasses and protocols for explicit data/interfaces where already established.
Type public boundaries and narrow parsed JSON with runtime checks. A type hint,
cast, `assert`, or `Any` does not validate untrusted provider data. Treat booleans,
integers, missing values, NaN, and infinity deliberately in numeric configuration.

Prefer `pathlib`, context managers, precise exceptions, and explicit resource cleanup.
Keep heavy optional imports inside the inference backend or code path that needs
them. Avoid import-time downloads, API calls, or credential reads. Do not add a
static type checker requirement until it is declared and wired into the workflow.
