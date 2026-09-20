# Jev-guided intermediate reasoning: investigation

Started 2026-09-20 at the owner's request, before merging PR #1. The target is
the actual Jev model evaluating intermediate steps during inference, with both
models' weights unchanged. This is a follow-up investigation, not an implemented
reasoning-search feature or a claim of improved Granite answers.

## Plan and diagnostic protocol

1. Read primary research and current TypeSafe contracts; inspect the existing
   controller, scorer, token boundaries, and Granite interface.
2. Run a small, preregistered diagnostic of the scorer before building a search
   engine: eight fictional rule problems, three fixed candidate statements each.
3. Compare the existing answer rubric with an intermediate-step rubric on exactly
   those candidates. Use a deterministic rule engine for expected judgments;
   never send its results to Jev. Do not tune prompts or thresholds after the run.
4. Record sources, all requests/responses/errors, budgets, limitations, an engine
   design, and a separate held-out end-to-end experiment specification.

The diagnostic uses finite forward implications and explicit negative facts;
missing information does not imply its negation. A valid candidate and the entire
tentative prefix must follow from the original facts/rules. A useful next step
also adds a fact on a dependency path to the goal which is absent from the
original facts and prefix. The oracle implements this deliberately narrow task,
not general natural-language reasoning. Text is rendered from the same symbolic
fixture, so there is no uncertain free-text parsing in the oracle.

The baseline uses the unmodified `build_payload` answer rubric. The new rubric asks
about grounded validity and a useful intermediate deduction, explicitly allowing
an unfinished answer. Both use the fixed existing thresholds 0.75 and 0.60, with
first-in-fixture tie breaking and `min(validity, progress)` ranking. These are
heuristics, not calibrated guarantees. The fixtures contain useful incomplete
steps, missing conjuncts, reversed implication, explicit negation, irrelevant
truths, repetitions, and an intentionally contaminated prefix.

Budget: 16 serial HTTP requests maximum, one attempt each, 15 seconds per request,
180 seconds total; requested model `jev-1.13.0`. No retry of an ambiguous timeout.
The candidates are authored fixtures, not Granite generations. This is an exposed
diagnostic set with no held-out split, so it cannot establish end-to-end quality,
generalization, Granite candidate coverage, or latency of a deployed engine.

Files: a standalone experiment and synthetic fixture under `experiments/`, offline
regressions under `tests/`, this design, and a new dated report. Existing inference
code, package interfaces, PR #1, and previous raw reports are outside the change.
Validate oracle edge cases, reference isolation, invalid scores, no network in
tests, bounded requests, output preservation, documentation links, lint/tests/build.

## Sources and working findings

- [Tree of Thoughts](https://arxiv.org/abs/2305.10601) explores intermediate text
  branches with evaluation and backtracking; it establishes a related search
  pattern, not evidence for Jev or Granite.
- [Self-Evaluation Guided Beam Search](https://arxiv.org/html/2305.00633v3) treats
  a reasoning step as several tokens and scores chains during bounded search.
  Its evaluated generators/verifiers and tasks differ from ours.
- [Scaling test-time compute](https://arxiv.org/abs/2408.03314) finds that the best
  use of extra inference work depends on problem difficulty and the base model.
  Compare quality at actual work budgets, not just equal request ceilings.
- [TypeSafe's interface](https://docs.typesafe.ai/api) evaluates supplied text/state
  using typed questions. It exposes no Granite activation or gradient interface.
- [Jev's documented limitations](https://docs.typesafe.ai/model-jaggedness/jev-1.13)
  include numerical precision, indirection, and adversarial framing. Narrow step
  checks need measurement; “reasoning verifier” is a proposed role, not a validated
  property of this model.
- [Citation-checking cookbook](https://docs.typesafe.ai/cookbooks/citation_check)
  separates exact checks in code from contextual judgments by Jev. That separation
  informs the proposed evaluator; its published results are not our measurements.
- [Granite model card](https://huggingface.co/ibm-granite/granite-4.0-1b) and the
  existing adapter provide ordinary causal generation. We will request explicit
  intermediate text; we have not identified a dedicated hidden-reasoning stream.

## Existing code and necessary changes

- `types.py` asks for a direct concise answer; a new reasoning request needs an
  explicit intermediate/final protocol rather than treating the current output
  as evidence of internal thoughts.
- `jev.py` judges direct-answer progress. A step scorer must allow useful partial
  deductions, distinguish uncertain hypotheses from facts, and check a prefix
  against original evidence instead of promoting earlier scores to truth.
- `controller.py` commits to one prefix, retries only that prefix, and discards
  alternatives. It has no search frontier or backtracking.
- `ChunkStop` uses sentence punctuation. Reasoning needs explicit step/final
  boundaries, including multi-token delimiters and truncated-step outcomes.
- `TransformersBackend.propose` already accepts exact prefix token IDs and uses
  an independent generation cache per proposal. This is a safe first implementation
  for branches; retained branch caches are a later optimization with ownership tests.

The implementation design and diagnostic outcome will be recorded here after the
fixed diagnostic completes, keeping planned behavior separate from measured facts.

## Follow-up generation check, declared after the scorer diagnostic

Both rubrics matched all eight fixture decisions, so there is no observed selection
advantage for the new rubric here. Before recommending an engine extension, check
whether the existing frozen Granite can produce explicit deductions. This is a
separate diagnostic, not an extension of the 16-call scorer result.

Run the existing controller on `useful-incomplete-step` and `missing-conjunct`, with
an explicit deduction/final-answer system prompt. Compare likelihood selection and
the existing Jev scorer, one seed (42), three candidates, 48-token chunks, four
steps, 160 accepted tokens and 576 decode slots maximum, no resampling retries,
120 seconds per run. Use at most eight Jev HTTP attempts across the two guided
runs. Rotate the two modes' order, load the already cached pinned Granite revision,
and warm up the three-candidate shape before timing. Keep all four results.

This checks generated step boundaries and exact-prefix continuation using existing
code. No backtracking, dedicated step scorer, or retained branch cache is added.
Qualitative review of generated traces is distinct from the symbolic oracle's
evaluation of the authored statements. No second attempt to repair a poor result.
