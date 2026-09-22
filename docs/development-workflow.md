# Development workflow

Authority: [AGENTS.md](../AGENTS.md). Start from the user's goal and the existing
code, preserve relevant work already done, and scale the plan to the change.

## Plan

State the goal, files, dependencies, corner cases, and verification before editing.
For small work, a short task note is enough; keep a design document for decisions
that need to survive the session. Read [flows.md](../flows.md) for affected paths.
Search locally first. Check primary vendor documentation when an API/version claim
matters. Routine documentation edits do not require Jev or broad web research.

## Install and validate

Run from the repository root. Use the lockfile and the extras the task needs.

```bash
# Core development, no torch/model download required:
uv sync --locked --extra dev

# Inference work instead uses both extras:
uv sync --locked --extra dev --extra transformers
```

`uv sync` changes installed extras; avoid silently removing inference dependencies
from a working environment. Use `--no-sync` for checks once the environment is ready.
Run research/report helpers that import this package with `uv run --no-sync python`
or the same environment's Python, including helpers outside the tracked source tree.
System Python may lack the editable package and optional dependencies.

```bash
uv run --no-sync python scripts/check_ai_docs.py
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync pytest -q
uv build
```

Run focused tests while iterating. For code behavior changes, first observe the
new test fail for the intended reason, implement the smallest fix, then rerun it.
For guidance changes, validate local links, entrypoint discovery, portable commands,
and the contributor path through the docs. If a checker itself changes, test it first.
Do not add tests that merely assert prose spelling or repeat implementation logic.

The optional backend tests skip in core-only environments; report that distinction.
There is no enforced percentage coverage gate or configured static type checker
today. Do not claim one ran or invoke undeclared tooling. Cover meaningful outcomes
and negative paths; add tools intentionally with dependency and CI changes.

## End-to-end evidence

Match the evidence to the changed flow, not to the size of the diff:

- Documentation: checker, navigation/command inspection, CLI help when documented
  command usage changes; no paid inference for unchanged model behavior.
- Controller/client: deterministic model/scorer doubles covering the whole flow,
  including selected prefix, rejection, budgets, EOS, and failed service calls.
- Backend: offline tiny-model comparison and a bounded real-model run when behavior
  depends on its actual tokenizer/cache/device. State model/hardware limitations.
- Scorer prompts or evaluation: a scoped live fixture when access exists, plus
  separate held-out grading before any quality claim; report unavailable access.

Examples and larger benchmark commands are in [README.md](../README.md).
Never describe a fixture, skipped test, or mocked provider as a live integration.

## Review and handoff

Review the full diff and surrounding code, check the active PR's actual base, and
read all relevant review context. Resolve actionable P1/P2 and required-check
failures. Follow [.claude/rules/common-git-workflow.md](../.claude/rules/common-git-workflow.md)
and the [PR template](../.github/pull_request_template.md).

State what changed and why, commands and actual outcomes, end-to-end evidence,
risks, skipped/unavailable checks, and which docs were updated. Historical reports
remain linked as historical evidence. An unavailable review bot or missing GPU is
not a passing check; disclose it without blocking unrelated work unnecessarily.

When a review reveals a repeated failure pattern, capture a short operational rule
and regression in the same PR. Keep [LIVE.md](../LIVE.md) and public claims accurate;
do not mark a branch implementation merged or a planned optimization released.
