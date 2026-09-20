# Intermediate reasoning investigation — 2026-09-20

Jev handled the fixed candidate diagnostic correctly, but a live Granite check
exposed duplicate proposals, repeated premises, missing final-state handling, and
an empty rejection outcome. The evidence supports investigating explicit step
control and bounded recovery; it does not demonstrate improved answer quality.

The actual Jev model participated at inference time. No training, replacement
critic, new weights, tree-search controller, or vLLM extension was introduced.
The [investigation and engine design](../../docs/reasoning-step-investigation.md)
records the protocol, research sources, proposed architecture, and next evaluation.

## Fixed-candidate diagnostic

Eight fictional rule problems supply three authored candidate statements each.
A deterministic forward-rule oracle evaluates validity, dependency on the goal,
novelty, and prefix contamination. No oracle labels reach Jev. This measures a
narrow symbolic task rendered as text, not arbitrary natural-language reasoning.

Both the existing answer rubric and an intermediate-step rubric were run once
against the same 24 statements, with fixed eligibility thresholds 0.75/0.60 and
no tuning. The case order alternates the two rubrics. Rules are forward implications;
absence is not negation. The exposed, related fixtures have no held-out split.

| Rubric | Correct selection or abstention | Eligible steps accepted | Ineligible steps rejected | HTTP calls |
| --- | ---: | ---: | ---: | ---: |
| Existing answer rubric | 8/8 | 5/5 | 19/19 | 8 |
| Intermediate-step rubric | 8/8 | 5/5 | 19/19 | 8 |

The useful incomplete step was accepted by both rubrics, while missing conjuncts,
reverse implications, unrelated truths, repetitions, and a contaminated prefix
were handled as specified. There is **no observed advantage for the new rubric**.
This is correctness of the combined eligibility decisions, not of every individual
score: the new rubric gave one contaminated-prefix continuation progress 0.64,
despite validity 0.07. The validity gate prevented that continuation's acceptance.
All 16 calls succeeded and returned `jev-1.13.0`; total usage was 21,172 input and
1,888 output tokens. The two rubric batches accumulated 2.725 and 2.144 seconds
respectively; this one serial diagnostic is not a latency comparison study.

The preregistered source was `3c05a7d` with a clean checkout. The experiment permits
16 requests, one attempt each, 15 seconds per call, and 180 seconds total. No retry,
timeout, threshold search, or manual candidate editing occurred after the run.

## Generated Granite derivations

After that diagnostic, a separate fixed follow-up asked the original cached
`ibm-granite/granite-4.0-1b` for explicit `Step:` deductions and a `Final:` answer.
It used revision `6a7381ba1f54d684ff508d991aeb7dc580157103`, zero trainable
parameters, MPS BF16, three candidates, seed 42, 48-token chunks, four steps,
160 accepted tokens, and 576 decode slots maximum. There was no resampling.
This uses the existing controller and existing Jev answer rubric; the new
intermediate-step rubric was not substituted into the production scorer.

| Problem | Mode | Observed result | Recorded stop | Elapsed |
| --- | --- | --- | --- | ---: |
| Solvable chain | Likelihood | Correct final statement | `step_budget` | 13.56 s |
| Solvable chain | Jev | Correct final statement | `step_budget` | 13.25 s |
| Missing manager approval | Likelihood | Invented approval, then derived entry; no final answer | `step_budget` | 8.33 s |
| Missing manager approval | Jev | Rejected all first steps; empty output | `all_rejected` | 2.11 s |

Both solvable outputs restated a fact and two rules before the correct conclusion.
Neither reached EOS within the fixed four-step limit; the current controller does
not treat a visible `Final:` label as a completion event. The two modes followed
the same first three selected texts and differed only in final phrasing. These
traces therefore do not demonstrate a better reasoning path chosen by Jev.

In the missing-premise case, all three first candidates were the same supported
restatement, `Step: Mira completed orientation.` Jev support was 0.98, but relevance
was 0.52–0.56, below 0.60, so the controller stopped. It **did not inspect or correct**
the later invented approval seen in the likelihood run. Preventing continuation
and returning an empty result is not a correct “insufficient evidence” answer.

Seven of thirteen proposal batches contained three identical token sequences.
Distinct samples therefore often provided no selection opportunity. Some duplicate
texts received slightly different Jev scores, supporting deduplication before
scoring rather than repeated judgments of the same candidate/state.

Exact selected-token concatenation and each subsequent text prefix were verified
from all four raw traces. This establishes continuation integrity, not faithful
access to hidden reasoning or semantic correctness. The interpretation of generated
text above is the implementation author's review, not blinded independent grading.

The source was `478e610` with a clean checkout. Four runs completed, using five Jev
calls and 7,099 input / 590 output tokens. The solvable guided run spent 11.429 s
generating and 1.814 s in Jev calls. Timing excluded model loading and one short
three-candidate warm-up. The slightly lower total guided time than likelihood is
a single-run observation with variable local generation time, not a speedup claim.
No network/provider-compute decomposition or colocated runtime was measured.

## Artifacts and reproduction

- Scorer: [metadata](scorer/metadata.json), [exact inputs and local labels](scorer/inputs.json),
  [all returned judgments](scorer/runs.jsonl), [summary](scorer/summary.json).
- Granite: [metadata](granite/metadata.json), [all candidates and traces](granite/runs.jsonl),
  [derived work, diversity, and continuity summary](granite/summary.json).
- [Synthetic source fixture](../../experiments/step_cases.json),
  [experiment runner](../../experiments/step_probe.py), and
  [offline regressions](../../tests/test_step_probe.py).

The entire request input and response body are retained for successful scorer
calls, without credentials or authorization headers. All inputs are fictional.
The total live investigation used 21 HTTP calls and 28,271 Jev input tokens; no
monetary estimate is offered as a substitute for actual provider billing.

From the repository root, after the documented development installation:

```bash
# Core dependencies and a Jev key are enough for the authored-step diagnostic:
uv run --no-sync python experiments/step_probe.py --output results/new-step-probe

# Also requires the Transformers extra and the pinned Granite snapshot cached locally:
uv run --no-sync python experiments/step_probe.py --granite --output results/new-granite-probe
```

Use new output directories. The runner refuses existing destinations. Historical
raw results are never overwritten; provider outputs and device timings may vary.
The Granite summary was derived offline from the recorded traces, including exact
token concatenation, text-prefix continuity, and unique candidate token sequences.
The CLI writes raw Granite metadata/traces; it does not label generated answers
with the authored-candidate oracle or claim successful completion from exit code alone.

The next engineering experiment should add explicit step/final phases, candidate
deduplication and bounded diversification, and saved alternative branches. Its
quality evaluation needs held-out problems, candidate-coverage measurements,
independent grading, and controls with actual work reported. The detailed proposal
is in the linked investigation; these capabilities are not implemented in this report.

## Repository validation

The investigation passed 56 offline tests, including optional tiny-model backend
checks, Ruff lint/format, the guidance checker (41 active Markdown documents),
package build, and `git diff --check`. The new oracle/payload/transport tests were
first run without the probe implementation and failed for that missing file; the
Granite request-isolation test initially failed for its missing builder. All
passed after implementation. Additional timeout coverage verified that ambiguous
requests are retained as unknown usage without retry. These offline checks are
separate from the live Jev and Granite diagnostics above.
