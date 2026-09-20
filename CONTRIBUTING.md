# Contributing

Start with [Project.md](Project.md), [AGENTS.md](AGENTS.md), and the
[development workflow](docs/development-workflow.md). Contributions may improve
code, documentation, reproducibility, tests, or evidence of failure; a negative
experimental result is useful when its methods and limitations are clear.

Use a GitHub issue for substantial proposals when appropriate, and link real
issues in the PR. Small focused fixes do not need invented identifiers or a private
tracker account. Search existing issues/PRs to avoid duplicate work.

Plan scope and failure cases, test code behavior before implementing, and keep the
diff focused. Documentation-only contributions need relevant validation rather
than artificial tests. Run the documented checks and inspect their outputs before
claiming success. Read the [PR template](.github/pull_request_template.md).

You can contribute using core dependencies without a GPU or Jev account. Live
experiments are separate from offline tests; disclose missing resources and skipped
optional checks. Do not put keys, private prompts, customer traces, or unauthorized
data in issues, code, CI, or reports. Follow [SECURITY.md](SECURITY.md) for sensitive
reports and [Jev guidance](docs/JEV.md) for external evaluation.

Keep software attribution and required notices. Name external models/data and their
versions/terms; do not imply this repository owns or relicenses those assets.
Agent-assisted contributions meet the same review and evidence requirements as
other work; tool-specific settings and private paid services are not prerequisites.
