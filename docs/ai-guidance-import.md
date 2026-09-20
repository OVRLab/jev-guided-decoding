# OVRLab guidance adaptation record

## Purpose and source

On 2026-09-20 the project owner requested adapting the development guardrails in
the sibling `../ultranow` repository for this open-source Python project. This is
rewritten project guidance, not an unchanged bulk copy. Contributors do not need
access to the sibling repository.

The source checkout was at `d45567e2f2d64bee3d9be7665363cc8ebd5e996a` and contained
local edits to root guidance plus a new `docs/JEV.md`. The adaptation used the
readable working copy, not just that commit. The source was read, not modified.
Some source rules/guides identify ECC as their origin; their general workflow
lessons were rewritten alongside OVRLab's review-derived requirements rather than
copying framework-specific examples.

## Plan and risks

Preserve planning, test-first development, evidence, security, review learning,
and truthful status in portable, discoverable documents. Changes cover root
Markdown, rules, task/role guides, contributor docs, a Python checker, tests, and CI.
Inference code and historical benchmark artifacts are outside this change.

Risks include contradictory mirrors, missing links/tools, private tracker access,
unsafe machine-default requirements, stale product commands, internal material
in public docs, and treating experimental work as released or improved. Validate
with offline checker regressions, repository traversal, command/navigation review,
lint/format/tests, package build, and PR checks.

## Source-to-project mapping

Source paths below are provenance, not operating commands or dependencies.

| Source | Adapted destination and treatment |
| --- | --- |
| `AGENTS.md` | [AGENTS.md](../AGENTS.md): canonical plan/test/evidence/security/review policy with inference/research boundaries |
| `CLAUDE.md` | [CLAUDE.md](../CLAUDE.md): Python map and role routing, deferring shared policy to AGENTS |
| `GEMINI.md` | [GEMINI.md](../GEMINI.md): thin entrypoint using the same authority/checks |
| `Project.md`, `FEATURE.md` | [Project.md](../Project.md), [FEATURE.md](../FEATURE.md): agreed scope and separately labeled proposed evaluation |
| `LAUNCH.md`, `LIVE.md` | [LAUNCH.md](../LAUNCH.md), [LIVE.md](../LIVE.md): target versus evidence, branch/merged/released distinction |
| `flows.md` | [flows.md](../flows.md): controller/client/backend/benchmark and documentation flows |
| Root README workflow | [workflow](development-workflow.md), [CONTRIBUTING.md](../CONTRIBUTING.md), [README](../README.md) |
| `.claude/rules/common-*.md`, `agents.md` | [shared rules](../.claude/rules/): seven common guides and host-aware delegation |
| `.claude/rules/ts-*.md` | Python coding, patterns, security, and testing guides in [rules](../.claude/rules/) |
| `agents/` | [nine role guides](../agents/), with Python replacing TypeScript review and no forced model/tool metadata |
| `.claude/skills/tdd-workflow.md` | [TDD guide](../.claude/skills/tdd-workflow.md): pytest, offline fixtures, honest RED/GREEN evidence |
| `.claude/skills/security-review.md` | [security workflow](../.claude/skills/security-review.md), [SECURITY.md](../SECURITY.md): keys, provider boundaries, public artifacts |
| `.claude/skills/api-design.md` | [API guide](../.claude/skills/api-design.md): protocols, provider parsing, CLI/result compatibility |
| Evaluation-driven TDD/review addenda | [evaluation workflow](../.claude/skills/evaluation-workflow.md): held-out grading, actual budgets, negative results |
| `docs/JEV.md` | [Jev guide](JEV.md): optional host access, repository client, explicit context, probabilities and usage |
| `.github/scripts/check-ai-docs.js` and tests | [Python checker](../scripts/check_ai_docs.py), [tests](../tests/test_ai_docs.py), [CI](../.github/workflows/checks.yml) |
| PR evidence/review requirements | [PR template](../.github/pull_request_template.md) |

## Deliberate adaptations

- Jira-only naming becomes conventional commits with real GitHub references when
  available; private tracker access and invented identifiers are not prerequisites.
- Source `npm run build`, `npm run check`, and `npm run check:ai-docs` become the
  declared uv/Ruff/pytest/build/checker workflow. Browser, Worker, database, and
  tenant commands do not belong to this local inference library.
- Use a host planning mode when available and a written plan otherwise; Markdown
  cannot switch runtime modes. Role files do not provision agents or paid tools.
- Machine approval/sandbox defaults and global attribution preferences are not
  imposed on open-source contributors.
- Owned counters/caches may be mutable; hidden shared mutation remains a concern.
  Ownership and reviewability replace blanket immutability/arbitrary line quotas.
- Meaningful changed-behavior coverage is required without pretending an unconfigured
  numerical coverage gate or scanner exists.
- All tracked content may be public. Private repo-tracked records are not a safe
  default; preserve software attribution and external model/data/provider notices.
- Product-specific tenant, OAuth, ledger, D1, web UI, business/customer, fundraising,
  and client/vendor docs are omitted. General lessons about boundaries, bounded work,
  cancellation, aligned consumers, and durable evidence are retained.
- Database-migration machinery is not imported; applicable compatibility lessons
  become API/result-schema and immutable historical-record guidance.

## Validation and maintenance

Checker tests were written first and initially failed because the checker did not
exist. They then exercise valid guidance, missing entrypoints/links/scripts,
nonportable commands, repository escape, and historical-report exclusion. The
repository check caught missing role/rule links during construction as well.

The checker runs offline in CI. It checks local inline Markdown destinations,
entrypoint discovery, selected nonportable instructions, and referenced Python
scripts. It does not execute Markdown, fetch URLs, validate heading anchors, or
prove all prose is correct. This provenance document can mention source commands
but is not operating guidance. Historical reports are excluded from active-rule
checks and are not rewritten by this import.

Local verification for this adaptation: `pytest -q tests/test_ai_docs.py` first
reported nine failures for the absent checker; after implementation all nine passed.
The full `pytest -q` run passed 42 tests, the guidance check passed 40 Markdown
files, Ruff lint/format passed, package build succeeded, and CLI `--help` worked.
No new paid Jev evaluation or model benchmark was needed because inference behavior
and its historical artifacts were unchanged. These are dated adaptation results;
future changes must run their own relevant checks.

Maintain these as project-owned documents. Distill durable lessons into the right
file, keeping canonical policy, role links, public README, implementation status,
and actual tooling aligned. Future imports require the same adaptation.
