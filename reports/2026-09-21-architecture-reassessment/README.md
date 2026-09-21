# Architecture reassessment: offline evidence — 2026-09-21

**New finding:** the old policy combines a substantial proposal-format/EOS problem
with an aggressive progress gate. These are distinct mechanisms. The following
counts reproduce the frozen policy, not independent judgments of step correctness.
This report adds no model inference, no new accuracy score, and no causal estimate
of the quality effect of disabling a gate.

## What was analyzed

All 3,600 rows of the [completed generated-answer study](../2026-09-20-generated-answer-study/README.md)
and all 48 rows of its [second development pilot](../2026-09-20-generated-answer-pilot-v2/README.md)
were read locally. No cases, seeds, modes or bad outcomes were dropped. The analyzer
replays frame parsing, exact-token deduplication, previously accepted-body exclusion,
support/progress thresholds of 0.5, and Jev selection/tie-breaking. It verifies the
accepted-step ledger and rejects inconsistent or unscored valid Jev batches.
Its scope is these successful-provider traces, not arbitrary interrupted studies.

## First proposal, before reasoning paths diverge

| Task / 600 Jev runs | First step accepted | All valid options rejected | No valid option to score |
| --- | ---: | ---: | ---: |
| Math | 450 | 120 | 30 |
| Logic | 28 | 307 | 265 |

The likelihood arm has the same initial proposal batches: it accepts an initial
step in 570 math and 335 logic runs. Thus the initial guided logic collapse is
not entirely attributable to the scorer: 265/600 runs offer no valid first step
under the common generation/parser contract. The further 307/600 are stopped by
the scorer/controller policy. Their sum reproduces the 572 zero-step logic runs.
This is an exact control-flow attribution, not proof that rejected steps deserved
acceptance or that accepting them would improve the final answer.

Among the initial likelihood winners that Jev actually scored:

| Winner's gate status | Math, n=570 | Logic, n=335 |
| --- | ---: | ---: |
| Passes both | 385 | 9 |
| Fails only progress | 123 | 293 |
| Fails only support | 34 | 0 |
| Fails both | 28 | 33 |

Jev selected a different accepted first option from the local likelihood winner
in 180 math and 19 logic runs. These are first-batch counts; the original report's
484 changes cover all visited prefixes. Common initial batches permit this local
comparison. Later prefixes diverge and are not paired causal counterfactuals.

## All unique scored candidates on Jev's visited paths

| Gate status | Math | Logic |
| --- | ---: | ---: |
| Eligible | 2,593 | 61 |
| Fails only progress | 835 | 614 |
| Fails only support | 132 | 1 |
| Fails both | 223 | 132 |
| Total | 3,783 | 808 |

Of 499 math and 334 logic `all_rejected` batch stops, respectively 435 and 313
contain at least one support-passing candidate blocked by progress. Removing the
progress gate would mechanically make an option eligible in those recorded
batches. It would change future prefixes, proposals, costs and answers; none of
those unobserved outcomes can be calculated from these counters.

Jev's logic traces contain 832 EOS candidate endings and 834 parsing failures out
of 1,944 raw candidate occurrences; math contains 548 EOS endings and 564 parsing
failures out of 5,919. Finish reason and invalid-reason counters overlap and must
not be added. Invalid causes use the controller's first applicable exclusion:
an empty EOS normally falls into `parse_failure` before the finish-reason check.
EOS may be natural completion rather than bad reasoning. All modes' separate
finish/invalid counters are available in [main diagnostics](main-diagnostics.json).

## Development warning was already visible

On the 16-case development pilot, guided math retained no step on 3/8 cases and
guided logic on 7/8. Logic's seven split into five no-valid-step and two scored
all-rejections at the root. All three later logic all-rejection stops contained
a support-passing option blocked by progress. The pilot was admitted for format,
provenance and exercised selection; it did not require useful branch coverage or
independent critic quality. The next protocol adds those gates rather than tuning
on the completed test. See [development diagnostics](development-diagnostics.json).

## Checkpoint and interface inspection

[Model audit](model-audit.json) records 40 attention layers, hidden width 2,048,
16 attention heads, 4 KV heads, zero experts, vocabulary 100,352, tied embeddings,
and output-logit scaling by 8. The installed Transformers 4.57.1 hybrid-family
implementation exactly matches the retrieved upstream source SHA-256. This was
configuration/source inspection, not an activation or quality experiment.

Live primary-source review also found the provider's stated numerical and
multi-hop limitations for Jev 1.13. That supports a critic-capability hypothesis;
it does not independently prove why any historical answer was wrong. Sources and
the proposed insertion point are in the [architecture review](../../research/architecture-reassessment.md).

## Reproduce and verify

From a checkout containing the private backups, use new output filenames:

```bash
uv run --no-sync python research/analysis/trace_diagnostics.py \
  --runs results/generated-answer-nebius-20260920/generated-answer-main/runs.jsonl \
  --output results/new-main-diagnostics.json
uv run --no-sync python research/analysis/trace_diagnostics.py \
  --runs results/generated-answer-nebius-20260920/generated-answer-pilot-v2/runs.jsonl \
  --output results/new-development-diagnostics.json
uv run --no-sync pytest -q tests/test_trace_diagnostics.py
```

The [analyzer](../../research/analysis/trace_diagnostics.py) publishes counters,
not source text, candidate text, answers, tokens, or credentials. Both JSON reports
contain input/analyzer/parser hashes. Source execution was on the research branch
based on `6a7270170abf51848c3ecff697eb06a74de6ebb0`; the new analyzer was uncommitted
at execution, with its exact file hash recorded. No historical model runner changed.

Six focused tests were first attempted before the analyzer existed and failed at
collection for the absent module. The final test loader follows the repository's
`runpy` convention. All six pass, covering unscored EOS versus rejection, the exact
threshold boundary, distinct gate causes, malformed/missing judgments, inconsistent
selection and duplicate jobs. Both full analyses completed and reconcile to the
original accepted-step totals: single 4,058, likelihood 4,637, Jev 1,421 in main;
41, 44, 19 in development. Final local validation passed all 212 tests, including
the five optional backend checks, Ruff lint/format, the 47-file guidance check,
package build and whitespace checks. A separate link audit covered the eight new
Markdown files; all eleven historical report files matched their prior committed
bytes. Production source, frozen runners and model configurations were unchanged.
CI and review status are recorded in the PR. Automated Codex review was unavailable
because the account's review quota was exhausted; this is not review approval.

The historical test data is now explicitly used for exploratory mechanism analysis.
There is no new significance test, threshold fitting, final-answer regrading, or
claim that a proposed intervention has improved accuracy. Public aggregates alone
cannot reproduce the private per-example audit; that limitation remains in the
paper. Original reports and raw results are unchanged.
