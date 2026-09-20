# Proposal generation experiment — 2026-09-20

This follow-up tests whether better proposal instructions give Jev useful
intermediate deductions to evaluate. It preserves the earlier
[0/4 step-guided result](../2026-09-20-reasoning-controller/README.md). Original
Granite weights remain frozen, and the actual hosted Jev model still evaluates
candidates during inference. No trained critic, changed checkpoint, or serving
extension is introduced.

## Development results and selection

Four new fictional development worlds were used with seeds 42 and 43. Each job
requested three root candidates, at most 96 tokens each, no resampling, one parent
expansion, and at most one Jev HTTP attempt. The existing scorer and fixed
0.75 validity / 0.60 progress / 0.75 completion thresholds were unchanged.
Each round therefore planned 16 batches and at most 16 calls. A 600-second stage
limit and 30-second per-request limit bounded the work. The root-only run's
`depth_budget` status is expected after an accepted step; it is not a completed
answer benchmark.

| Proposal prompt | Batches offering a Jev-eligible candidate | Eligible candidates | Generated tokens | Prefill tokens |
| --- | ---: | ---: | ---: | ---: |
| Original instructions, round 1 | 0/8 | 0 | 276 | 6,678 |
| Two examples, round 1 | 1/8 | 1 | 367 | 13,134 |
| Original instructions, round 2 | 0/8 | 0 | 276 | 6,678 |
| Conclusion-first examples, round 2 | 6/8 | 7 | 490 | 18,966 |

The first revision was only weakly useful. Although it met the minimal relative
improvement condition, seven of eight batches still had no eligible candidate.
We used one further development revision, refining the original failure-only
revision condition after seeing development results. This is disclosed post hoc
development work; no evaluation results existed yet. Both complete rounds are
retained, including the repeated original-prompt control.

The second revision combines a conclusion-first instruction, a `Therefore,` cue,
Fact/Rule examples matching the problem presentation, explicit-negative guidance,
and verdict-label examples. These changes were evaluated together; their separate
contributions were not isolated. Author review confirms clear new conclusions in
four of eight example batches (two chain cases, two negative cases). The other two
eligible batches only combine premises and say the rule conditions are satisfied;
they are weaker evidence of progress. Both missing-conjunction batches still failed.
Jev eligibility is a development selection signal, not independent correctness.

No generated development candidate copied the demonstration names Pera, Dexo, or
Bex. This exact-name check is narrower than proving absence of all example influence.
All 32 root traces had the empty parent prefix, one proposal batch, no resampling,
and at most one HTTP attempt. Generated-token and eligibility counts were checked
against their raw proposals/children.

Source for round 1: `ed06169`; source for round 2: `20aa845`. Both metadata records
show clean checkouts at capture. A separate [selection record](selection.json)
freezes the prompt and fixture hashes before evaluation. The original default
prompt remains available and unchanged; the example prompt is opt-in.

## Separate evaluation protocol

Six fictional worlds hold out complete rule graphs: a longer chain with a
distractor, merged branches, alternative negative derivations, a longer negative
chain, an unseeded cycle, and a missing prerequisite behind an intermediate fact.
They share elementary implication/conjunction motifs with development and are
not broad out-of-distribution coverage. There are two entailed, two contradicted,
and two unknown claims. Every mode receives the same frozen example prompt,
evidence, question, sampling settings, and configured resource ceilings.

Planned comparison: 6 cases × 2 seeds × 4 modes = 48 runs, rotating mode order.
Modes are greedy, likelihood search, final-only Jev, and step-guided Jev. A
1,800-second cooperative stage limit bounds the experiment; any not-started or
interrupted runs stay visible in the planned denominator. Loading and two-token
warm-ups at batch sizes one and three are excluded from per-run timing. Original
pinned Granite runs on Apple M1 Pro / MPS BF16; Jev is hosted remotely.

The deterministic oracle computes forward closure over explicitly provided facts
and conjunctive one-way rules. Missing facts are not false, implications are not
reversible, and cycles without a starting premise prove nothing. Only facts/rules
and the question reach generation and Jev; oracle labels are local benchmark data.
The grader verifies the recorded problem text, not just the case ID.

The final answer must begin `ENTAILED`, `CONTRADICTED`, or `UNKNOWN`. The frozen
grader compares that first word with the oracle. Missing/unrecognized labels,
incomplete searches, and not-started runs count as nonmatches. It does not grade
explanations or intermediate steps; a semantically sensible answer without the
requested label is a format failure, not automatically a factual error. The grader
is independent of Jev's own scores. Two seeds on one world are repeated observations,
not independent new problems. No prompt, threshold, or grading changes are allowed
after inspecting evaluation results.

The primary batch stopped after 35/48 jobs when a Jev call timed out at its
90-second request deadline. That failed request and unknown usage are retained.
A separate 900-second stage attempts only the thirteen jobs that never started,
using unchanged inference/grading settings. It reloads and warms the model for
each job, so restart effects limit latency comparisons. This execution-protocol
deviation is disclosed before continuation; no failed request is replayed. Results
and integrity checks follow after completion.

## Observed example of intervention timing

On `eval_alternative`, seed 42, the step-guided and final-only modes received
identical actual prompts and identical root candidate token sequences. Final-only
selection followed the higher-likelihood repetition of the overheating flag.
Subsequent unjudged steps incorrectly applied a rule requiring an unstated recall
notice. Jev rejected the contaminated derivation only when final answers were
proposed; the run exhausted 90 seconds while searching that area of the tree.

Step-guided Jev rejected the repeated fact for low progress (0.05) and accepted
the offered thermal-lock deduction (validity 0.96, progress 0.89). It then followed
the valid thermal-lock rule to the correct negative conclusion in 28.10 seconds.
This is an observed early-selection benefit against that final-only search run.
Greedy also answered correctly, so it is not an overall superiority claim.

Likelihood search produced the correct verdict word while using the unsupported
inspection/recall reasoning. This illustrates why verdict agreement alone does not
establish a valid derivation. The interpretation of these explanations is author
review against the supplied rules, not blinded independent natural-language grading.
The matching root token sequences were checked directly from the recorded traces.

For the same world at seed 43, both step-guided root batches offered only repeated
overheating-flag statements. All were rejected, and the run returned no answer.
Jev cannot select the useful thermal-lock deduction when generation omits it.
These paired observations preserve both the useful intervention and its failure.

## Artifacts and reproduction

- Development round 1: [metadata](development-v1/metadata.json),
  [all runs](development-v1/runs.jsonl), [summary](development-v1/summary.json).
- Development round 2: [metadata](development-v2/metadata.json),
  [all runs](development-v2/runs.jsonl), [summary](development-v2/summary.json).
- [Protocol and decisions](../../docs/proposal-generation-experiment.md),
  [symbolic fixtures](../../experiments/proposal_worlds.json),
  [runner and oracle](../../experiments/proposal_probe.py),
  [evaluation inputs](../../data/proposal-evaluation.jsonl),
  [example configuration](../../configs/granite-4.0-1b-reasoning-examples.toml).

```bash
# Development root comparison (current prompt revision):
uv run --no-sync python experiments/proposal_probe.py develop \
  --output results/new-proposal-development

# Frozen full-search evaluation, followed by offline verdict grading:
uv run --no-sync python experiments/proposal_probe.py evaluate \
  --config configs/granite-4.0-1b-reasoning-examples.toml \
  --output results/new-proposal-evaluation
uv run --no-sync python experiments/proposal_probe.py grade \
  --output results/new-proposal-evaluation
```

All output directories/grade paths must be new. Earlier source revisions reproduce
the earlier prompts; current commands use the current revision. Provider scores,
sampling across devices, and elapsed times may vary. All inputs are authored
fictional data, suitable for the public repository.
