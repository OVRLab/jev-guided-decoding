# Gemini entrypoint

Read [AGENTS.md](AGENTS.md) as the canonical development policy, then use the
[development workflow](docs/development-workflow.md), shared [rules](.claude/rules/),
and [repository map](CLAUDE.md). The same planning, test-first, evidence, privacy,
budget, and PR-review requirements apply to every coding assistant.

Read the relevant role guides through `CLAUDE.md`; use available host tools without
assuming named subagents, a GPU, or private credentials exist. Preserve the user's
active scope and the environment's permission/delegation settings.

Check [project purpose](Project.md), [implemented status](LIVE.md), and
[flow validation](flows.md) before changing claims or behavior. Jev usage follows
[docs/JEV.md](docs/JEV.md). Guidance changes require
`uv run --no-sync python scripts/check_ai_docs.py`.

Capture shared lessons in the canonical files, not a divergent Gemini-only copy.
