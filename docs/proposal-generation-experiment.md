# Proposal generation experiment

Authorized on 2026-09-20 after the first reasoning controller completed 0/4
step-guided tasks. That [negative result](../reports/2026-09-20-reasoning-controller/README.md)
is preserved. This experiment changes the proposal prompt, not weights, frame
acceptance rules, or Jev's fixed validity/progress/completion thresholds.

## Hypothesis and bounded plan

Two worked examples may help Granite apply a rule to a subject instead of copying
premises, and may improve completion of the existing step/final tags. Introduce an
explicit `prompt_style` setting with `instructions` (existing behavior) and
`examples` (existing instructions plus two unrelated demonstrations). Keep the
original configuration/default unchanged. Record the complete actual prompt.

1. Test style validation, idempotent request preparation, custom-system retention,
   unchanged baseline prompt, and example/reference isolation before implementation.
2. Add four new development worlds with a deterministic forward-rule oracle. Run
   only root proposals for both styles, three candidates, seeds 42 and 43, and at
   most 96 new tokens each. This is 16 batches / at most 48 generated candidates.
   Score distinct complete frames using the unchanged Jev scorer, one HTTP attempt
   per batch, at most 16 HTTP attempts and 600 seconds for the stage. Log malformed
   and duplicate candidates and all discarded work. Jev eligibility is a development
   signal, not an independent correctness label; author review checks actual content.
3. Choose `examples` only if more development batches offer an eligible candidate
   and review finds genuine applied deductions or justified missing-premise answers.
   If it fails, permit at most one declared revised demonstration prompt, using the
   same development cases and budget; preserve both attempts. No open-ended tuning.
4. Freeze the chosen prompt before opening evaluation results. Evaluate six separate
   rule structures, seeds 42/43, and greedy, likelihood, final-only Jev, and step Jev:
   48 runs, at most 12 HTTP attempts per guided request. Use the same sampling,
   frame/search limits, and actual-work reporting in all modes. A stage cap of
   1,800 seconds bounds the live check; interrupted/not-started rows must be disclosed.
5. Publish all raw traces, oracle verdict agreement, completion, malformed verdicts,
   candidate coverage, duplicates, resource counts, timings, versions, and limitations.
   Update the existing PR and docs, run offline checks/build, and inspect CI/reviews.

## Tasks and grading

Each fictional world contains propositional atoms, explicit facts, and forward
implications with conjunctive premises. Positive and explicit negative atoms are
distinct. The oracle repeatedly applies rules to closure; missing facts are not
negated, rules are not reversible, and unseeded cycles prove nothing. Worlds with
both the goal and its explicit opposite derivable are invalid fixtures.

The public question requests a final answer beginning `ENTAILED`, `CONTRADICTED`,
or `UNKNOWN`, followed by a reason. The first verdict is graded against the
independent oracle; ambiguous/unrecognized verdicts and incomplete searches count
as failures of this narrow metric. A correct verdict does not verify its explanation
or intermediate steps. References/closure labels never enter generator or Jev inputs.

Development uses a two-hop chain, a direct conjunction, a missing conjunction,
and a one-rule explicit negative conclusion. Evaluation holds out longer chains,
branch merging, alternative derivations, negation through a longer chain, an
unseeded cycle, and a missing prerequisite behind a derived intermediate fact.
These are only six synthetic structures, not a general reasoning benchmark.
Prompt examples are separate worlds; neither their subjects nor facts are evidence
for current tasks. Seeds are repeated runs within cases, not independent new tasks.

The proposed model remains the pinned original Granite on MPS BF16; actual Jev is
hosted `jev-1.13.0`. Both are inference-only. Loading and a two-token warm-up are
excluded from per-run timing and documented. No network/provider-compute split or
colocated performance claim is possible here.

## Files, risks, and verification

Affected files: framing/request preparation, reasoning config, CLI request creation,
focused tests, a standalone root-proposal experiment/oracle and fixture, a new
example config, and a new report. No changes to the scorer or prior raw reports.

Main risks: example facts leaking into the current problem, duplicated prompts,
gold-label leakage, tuning on evaluation, overclaiming verdict agreement as semantic
correctness, and longer prompts exhausting prefill/context budgets. Tests use fake
backends/transports and no credentials; live work is bounded and fictional.

Primary context checked: [Granite model card](https://huggingface.co/ibm-granite/granite-4.0-1b)
and [TypeSafe citation checks](https://docs.typesafe.ai/cookbooks/citation_check).
The latter separates exact checks from semantic judgments; it does not validate
Jev's performance on this experiment. Existing API/request shapes remain unchanged.


## Development revision declared before evaluation

The first two-example prompt produced one eligible batch out of eight, versus zero
for instructions alone. It met the minimal relative-improvement condition, but
seven failures still showed the original bottleneck. After inspecting development
results, we chose the one bounded additional development round anticipated above;
this decision refines the original failure-only revision condition and is explicitly
post hoc development work. No evaluation outputs have been generated or inspected.

Revision two leads with the consequent of a rule, uses a `Therefore,` cue, matches
the fixture's Fact/Rule presentation, and includes separate positive, missing-premise,
and explicit-negative demonstrations. It also demonstrates the requested verdict
labels. These are several prompt changes together; this experiment cannot attribute
any gain to one phrase or example. Keep the original root results unchanged and
repeat the same 16-batch development comparison once. Then choose the style with
more eligible development batches, check actual contents, and freeze it for the
separate evaluation; no third development revision is allowed in this experiment.


## Frozen evaluation selection

The second example revision offered eligible candidates in 6/8 development batches,
versus 0/8 for instructions alone (both rounds) and 1/8 for the first examples.
Author review found clear new conclusions in four batches, weaker combination-of-
conditions steps in two, and continued failure on the missing-conjunction problem.
The [selection record](../reports/2026-09-20-proposal-generation/selection.json)
freezes the prompt/fixture hashes before evaluation. Use the examples config for all
four evaluation modes; do not revise prompts, thresholds, grading, or fixtures after
seeing evaluation results. The original default/config remains unchanged.

A review regression additionally requires the grader to match recorded question
and evidence to the oracle fixture; reusing an ID alone is not sufficient provenance.
Missing, incomplete, and unrecognized verdicts remain in the planned denominator.
