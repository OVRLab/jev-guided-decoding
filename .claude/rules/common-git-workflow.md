# Git and pull request workflow

Follow [AGENTS.md](../../AGENTS.md). Use `<type>: <summary>` for commit messages and
PR titles, with `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, or `ci`.
Reference a real GitHub issue where available; do not invent issue/agent identifiers
or require access to a private tracker. Respect contributor attribution and licenses.

Inspect worktree changes and the existing PR before branching or pushing. Preserve
unrelated work, use the PR's actual base, and review its full diff and commit scope.
Do not create duplicate PRs or mix unrelated cleanup into the requested change.

Use the [PR template](../../.github/pull_request_template.md): problem/behavior,
risks, exact validation and end-to-end evidence, docs, blockers, and unverified areas.
Run the [canonical checks](../../docs/development-workflow.md) before handoff.
After pushing, inspect required CI and relevant review threads/comments. Resolve
blocking failures and actionable P1/P2 feedback; disclose unavailable review tools.

Operate within the user's authorized task and platform permissions. Merge only
when required checks/reviews and branch protection permit it; do not bypass them.
Keep branch implementation, merge, tag, package publication, and model release
as distinct states in [LIVE.md](../../LIVE.md). An ordinary code PR does not itself
publish a package or authorize unrelated messages or account changes.
