# Reasoning controller implementation

The opt-in [fixed-verdict extension](fixed-verdict-experiment.md) runs this search
with a reserved final-call budget, then asks Jev to choose among three labels
supplied by code. Its `fixed-verdict-v1` result distinguishes the generated token
path from the rendered verdict and retains the original reasoning outcome. The
`reasoning-v1` contract below continues to describe the original search modes.

Authorized on 2026-09-20 following the
[investigation](reasoning-step-investigation.md). The actual Jev model participates
during inference; neither model is trained. The controller and offline checks are implemented in
the work branch. A [separate live report](../reports/2026-09-20-reasoning-controller/README.md)
records 16 runs, bounded recovery, and the negative step-guidance result. The investigation's historical results remain unchanged.

## Plan

Add a separate controller and configuration, typed step/final frames, a framed
proposal method in the Transformers adapter, and a phase-aware Jev scorer sharing
the existing transport. Expose generation and benchmarking through separate CLI
commands. Keep the original answer controller and its defaults compatible.

Use `<step>...</step>` and `<final>...</final>` text encoded by the existing
tokenizer. Preserve accepted token IDs exactly. Final completion depends on a
complete validated final frame, not on generating another EOS token. Incomplete
frames and a step followed by EOS are explicit failures, never completed answers.

Use bounded depth-first search, retaining up to two eligible children at each
expansion. Deduplicate exact candidate token sequences before scoring and across
one bounded resampling attempt at a parent. Keep deferred siblings for recovery.
All work counters belong to the request and remain monotonic across backtracking.
Each branch initially recomputes its exact prefix with an independent generation
cache; no retained-cache serving optimization is part of this change.

Test first: frame boundaries/partial frames, novel and repeated steps, final
summaries, duplicate proposals, poisoned prefixes, saved-branch recovery, global
token/context/prefill/depth/expansion/API/time budgets, malformed scores, late
responses, and cooperative cancellation. Use deterministic backends/scorers and
the offline tiny causal model, then run the existing checks and package build.

Finally run a bounded live fixture with the cached pinned Granite and Jev. Record
all proposed/selected steps, alternatives, errors, completion outcomes, resource
counts, provider usage, source/data versions, and timing. A live mechanism check
is separate from a held-out quality claim; do not tune on historical probes.

## Files and risks

New modules: `framing.py`, `reasoning.py`, and `reasoning_scorer.py`. Extend the
backend and CLI while retaining their answer-mode behavior. Add a reasoning config,
focused tests, a public synthetic dataset, documentation, and a dated live report.

Main risks are malformed model framing, judging incomplete statements, counting
duplicates as alternatives, applying a score to another prefix, restoring a wrong
token/cache state, resetting budgets during recovery, and releasing a request lock
while cancelled model work still runs. Cancellation must signal the worker and
wait for it to stop; a running GPU kernel cannot be instantly interrupted.

Code owns acceptance and resource policy. Jev probabilities remain fallible.
Scorer errors never become a fallback unverified answer, and empty rejection is
not proof that the evidence is insufficient. Only the final answer is returned in
`text`; intermediate steps and stopped partial paths remain explicit in the trace.

## Implemented contract

`ReasoningController`, `ReasoningConfig`, and `ReasoningCancelled` are importable
from the package without Torch. `ReasoningScorer` shares the original client's
credential handling, Noul validation, bounded retries, and usage accounting.
`TransformersBackend.propose_frames` stops at closing frame tags, including tags
that span tokens. Full-frame parsing then rejects malformed or partial output.

The controller uses a bounded depth-first search. Each parent deduplicates exact
token sequences across its proposal batches. If a batch has no eligible candidate,
or only one distinct eligible step, it can resample at the same parent with a new
seed. This seeks diversity without guaranteeing different meanings. All distinct
candidates, including invalid/rejected ones, remain in the trace. An eligible
final or a batch containing multiple distinct sequences ends resampling.

Eligible candidates are ranked by the smaller validity/progress probability for
steps or validity/completion probability for finals, then by mean model log
probability. These numbers are ranking heuristics, not calibrated joint certainty.
The best child is visited; up to `keep_branches - 1` siblings are saved. A dead end
restores the most recently saved sibling, with its exact IDs and own derivation.
Oldest pending siblings are discarded when `max_pending` is reached, and pruning
is recorded. Depth/path/context dead ends can recover through another branch.
Global work exhaustion stops the request; counters never reset during recovery.

`greedy`, `sample`, and `likelihood` use the same frames without Jev.
`final_jev` ranks intermediate steps by model likelihood and evaluates final
candidates with Jev; eligible finals outrank unjudged steps in a mixed batch.
`jev` evaluates both kinds. Comparisons must include actual computation because
branch lengths, rejection, resampling, and final selection can differ by mode.

## Limits and recorded results

The [example config](../configs/granite-4.0-1b-reasoning.toml) allows 3 candidates,
2 retained children, 1 resampling attempt per parent, and a maximum of 6 frames
along a path (including the final). Each frame has at most 96 new tokens. Per
request it permits 8 parent expansions, 6 pending siblings, 384 path tokens,
1,536 padded decode slots, 30,000 repeated-prefill tokens, a 4,096-token context,
12 HTTP attempts, and 90 seconds. Limits apply to all modes; baseline modes make
no API calls. These are initial experiment settings, not tuned optima.

`reason` writes one JSON trace. `reason-benchmark` writes metadata, incremental
JSONL runs, and summary JSON; it rotates modes, excludes the two-token kernel
warm-up and model loading from run times, and records both separately or in the
procedure. Reference answers stay local. The versioned `reasoning-v1` result has
`phase`, final `text`, selected `steps` and path `token_ids`, proposals, scored
indices, raw evaluations, node IDs, saved/pruned alternatives, backtracking, and
explicit stop reasons. Metadata records the actual frame system prompt per run.

Generated tokens, padded decode slots, and repeated prefill include discarded and
duplicate work. Selected-path throughput includes intermediate frames, final tags,
and Jev waiting; it is not answer-only tokens/sec or serving throughput. Jev time
is the observed API round trip, including retries/network where applicable; it
cannot be interpreted as model compute alone. MPS counters remain allocation
snapshots, not peaks. A pending sibling stores tokens, not a retained KV cache.

Cancellation signals a cooperative stop and drains the model worker before the
controller releases ownership. It cannot interrupt a running GPU kernel instantly.
Library callers receive `ReasoningCancelled.result`; CLI commands preserve that
partial result with exit code 130. Cancelling an HTTP await cannot establish
remote cancellation or billing; usage and total HTTP attempts are marked unknown.
A second forced process interrupt can prevent artifact writing. Global time limits
reject late results but cannot promise a hard wall-clock deadline for in-flight work.

## Verification record before the live run

Test-first checks initially failed because the new framing/scorer modules and
backend methods did not exist, and the CLI rejected `reason`/`reason-benchmark`.
These were capability failures, not evidence of an old production regression.
Focused tests then passed, including a real offline tiny causal-model generation
check for both proposal methods with unchanged weights.

Follow-up regressions exposed loss of an already validated step when a diversity
resample could not afford another API call, and an uncaught invalid custom-scorer
judgment. The controller now keeps that validated path without new spending and
records malformed custom results as scorer errors with unknown provider activity.
Tests also cover discarded-token accounting, exact sibling prefixes, partial
frames, completion without EOS, all resource ceilings, bounded pending branches,
late scores, worker cancellation, and remote cancellation. Live-model compatibility
and held-out improvement are separate questions from these deterministic checks.


## Live outcome and review follow-up

The [live mechanism check](../reports/2026-09-20-reasoning-controller/README.md)
verified all proposal/selected prefixes and five backtracks. Final-only Jev
recovered through a saved sibling once, while likelihood and final-only search
also demonstrated bounded exhaustion. Step guidance completed 0/4 cases because
Granite supplied copied premises rather than useful deductions; live step-guided
backtracking was not reached. No quality gain or broad compatibility is claimed.

After the run, an offline review test reproduced a single-run artifact overwrite
race during inference. The CLI now uses exclusive file creation; an initial
existence check alone was insufficient. The security rule records this lesson.
The live result remains tied to its original source and was not rerun for this
output-only fix. Final local verification passed 91 tests, lint, formatting,
documentation checks, package build, CLI help, and core imports without loading
optional inference dependencies. CI and review availability are recorded on PR #2.


## Optional worked examples

`ReasoningConfig.prompt_style` selects `instructions` (the original default) or
`examples`. The examples prompt demonstrates a rule's new conclusion, missing
requirements, and explicit negation. It does not change frame acceptance or Jev
thresholds. Prompt preparation preserves custom system text and the current
question/evidence, is idempotent, and can switch styles without accumulating old
examples. The CLI records the same full system prompt the backend encodes.

The [proposal experiment](proposal-generation-experiment.md) records two bounded
development rounds and a separately frozen evaluation. Its positive development
signal is candidate availability, not proof of general reasoning improvement.
Examples increase prompt length and repeated-prefill work. They remain opt-in;
the original config and historical reports keep their original behavior.
