# AI development guardrails

This is the canonical repository guidance for every coding agent. Follow system
instructions, the user's current request, and applicable environment permissions;
then use this file and its linked guidance. Tool-specific entrypoints and role
guides must defer here rather than maintain conflicting copies.

## Read before work

- [Project.md](Project.md): purpose, users, architecture boundaries, and non-goals.
- [Development workflow](docs/development-workflow.md): planning, commands, and handoff.
- [LAUNCH.md](LAUNCH.md), [LIVE.md](LIVE.md), and [FEATURE.md](FEATURE.md): agreed scope,
  verified implementation, and the next experiment.
- [flows.md](flows.md): end-to-end paths and regression risks for the affected flow.
- [Rules](.claude/rules/), [workflow guides](.claude/skills/), and
  [role guides](agents/): read the relevant files listed in [CLAUDE.md](CLAUDE.md).

## Plan and verify before claiming success

1. Write a short plan stating the goal, affected files, corner cases, failure modes,
   and verification. Use the host's planning mode when available; a written plan
   suffices when it is not. A plan is not a request for extra permission.
2. For code or behavior changes, write a regression or capability test first and
   run it to observe the expected failure before implementing the smallest fix.
   Record what failed and why. Documentation-only changes use a validation plan
   instead of artificial tests. Honor explicit user exceptions and higher-level
   instructions; do not invent a past failing test after implementation.
3. Cover the least-initialized supported state: no credentials for baseline modes,
   no optional inference dependencies for core imports, empty/invalid inputs,
   budget exhaustion, unavailable services, and early completion as applicable.
4. Run the relevant flow in [flows.md](flows.md), then the canonical checks in
   [the workflow](docs/development-workflow.md). Inspect output and exit codes.
5. Use fresh evidence for current success claims. A historical report is evidence
   of that historical run, not proof that changed code still works. Do not repeat
   paid experiments for unrelated documentation edits or report them as rerun.

## Keep the experiment honest

- When testing whether Jev improves a generator's answers, that generator must
  produce the final answer in every compared arm. Keep Jev final classifiers as
  separately named experiments; their scores cannot stand in for generated-answer
  quality. Verify final-token provenance and a consistent prompt/grading contract.
- The package controllers select **text continuations during inference**. The
  separate R14–R17 research hooks apply Jev source-relevance biases inside selected
  Granite attention heads. R14 is static constrained QA; R16 adds serial cached
  generation, optional relevance refresh and full-vocabulary output contracts.
  R17 tests conditional dispatch, timing envelopes and local evidence-mass
  conservation. Distinguish each study from the package path. These are not neural
  fusion, access to hidden reasoning, training,
  a vLLM extension, or an improved model checkpoint. Claims need matching evidence.
- Preserve the original model weights and exact accepted token IDs in this scope.
  Rejected branches must never enter the continuation prefix or another request's cache.
- Retain explicit EOS, rejection, timeout, and budget outcomes. Empty EOS is a
  completion decision, not a demand to add another fact.
- Code owns limits, retries, selection, and external actions. Jev scores are fallible
  judgments; they cannot authorize extra spending, publishing, or bypassing tests.
- Compare the same prompts, model revisions, sampling settings, and candidate
  budgets; disclose **actual** generated tokens, padded slots, repeated prefill,
  latency, and API use. Equal ceilings do not prove equal computation.
- Separate a charged request from a successful intervention. A failed request can
  retain the native cache without restarting; its charge still belongs in cost
  accounting. Offline branch replay is not measured deployment savings.
- If syntax constraints are used, disclose their action-space restriction in every
  arm. Keep reference truth out of the grammar, preserve generator ownership of
  semantic choices, and treat guaranteed formatting as a controller property.
  A constrained-label baseline is not unrestricted default model generation.
  Report class balance and a trivial constant-label reference alongside absolute
  accuracy; a gain over a weak native baseline does not establish deployment utility.
- Separate calibration from held-out evaluation. Keep reference answers out of
  model inputs and Jev questions. Retain negative results and all incomplete runs.
- Lexical exact match/F1 are not general accuracy or grounding measures. Distinguish
  independent grading from the same scorer judging its own selections.
- Record seeds, versions, dataset hashes, hardware, warm-up, model-loading treatment,
  source revision, dirty state, and returned Jev version. Do not edit old raw results
  to match new code; write a new report and link the earlier one.
- Maintain the [research notebook](research/README.md) and
  [study register](research/study-register.md) for every subsequent experiment,
  including failed, interrupted and offline analyses. Register the protocol before
  new live inference; distinguish proposed mechanisms from implemented hooks and
  independently evaluated quality. Preserve corrections and negative evidence.

## Security and public content

Everything tracked here may be public: source, docs, fixtures, reports, PRs, issues,
and CI logs. Keep credentials, private customer material, internal operational notes,
and unpublished data outside the repository. An ignored file is not access control.
Preserve applicable software notices and disclose model/dataset/provider sources;
the package license does not relicense external models, datasets, or services.

Use [SECURITY.md](SECURITY.md) and [Jev guidance](docs/JEV.md) for external requests.
Never print keys or authorization headers, follow credential-bearing redirects to
another host, replay an ambiguous paid timeout blindly, or execute generated text.
Changes to limits, credentials, provider dispatch, cancellation, or output handling
need negative-path tests. Keep tests offline; live checks use explicitly scoped data
and budgets. Do not copy a contributor's machine permissions or private helper
requirements into public project defaults.

## Git and review discipline

- Keep each PR focused on a real problem; update an existing relevant PR rather
  than opening duplicates. Preserve unrelated edits in this and neighboring repos.
- Use conventional commit messages and PR titles: `<type>: <summary>`; include a
  real GitHub issue reference when one exists. Do not invent tracking identifiers
  or require a private issue tracker to contribute.
- Within the user's authorized repository task, agents may prepare commits, push
  the work branch, and manage the PR lifecycle without redundant confirmations.
  This is not authority for unrelated releases, account changes, or external messages.
- Review the full PR diff against its actual base. Document the problem, risk,
  exact checks, end-to-end evidence, and unverified areas using the PR template.
- Inspect CI plus review threads, resolved/outdated context, and automation comments.
  Address actionable P1/P2 feedback and blocking failures before handoff or merge.
  State when an automated review was unavailable; do not call its absence approval.
- Merge only within the authorized workflow, after required checks and reviews
  pass and branch protection allows it. Never bypass protection. A feature in a
  branch is not yet shipped on the default branch or published as a package.

## Preserve what reviews teach us

For a durable review lesson, fix the defect and add its regression first, then
distill the rule into the right file in the same PR. Inspect the full review context
before deciding the cause; do not paste raw comment history into guidance.
If no lasting rule is needed for a P1/P2 fix, explain why in the PR.
Keep README, CLI/config examples, protocols, flow checks, feature status, and
research claims aligned. Update `LIVE.md` only from verified evidence; revise
`LAUNCH.md` scope only when the project owner requests it.

Run `uv run --no-sync python scripts/check_ai_docs.py` whenever guidance or its
links/commands change. Only require installed tools, existing files, and commands
that work here. Optional role guides do not prove a separate agent is available;
follow the host's delegation rules and perform the review locally when needed.
