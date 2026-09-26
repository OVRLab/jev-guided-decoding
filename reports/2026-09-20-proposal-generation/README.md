# Proposal generation experiment — 2026-09-20

This follow-up tests whether better proposal instructions give Jev useful
intermediate deductions to evaluate. It preserves the earlier
[0/4 step-guided result](../2026-09-20-reasoning-controller/README.md). Original
Granite weights remain frozen, and the actual hosted Jev model still evaluates
candidates during inference. No trained critic, changed checkpoint, or serving
extension is introduced.

The selected prompt improved development candidate availability, but the separate
evaluation did **not establish an overall verdict gain**: step-guided Jev, greedy,
and likelihood search each matched 6/12 oracle verdicts; final-only Jev matched
5/12. All 48 planned runs are retained. Early guidance helped one trace avoid an
invalid derivation, while both UNKNOWN worlds remained unsolved in every mode.

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

The primary batch stopped after 35/48 jobs when a Jev call timed out as the run
reached its 90-second request deadline. That failed request and unknown usage are
retained. A separate 900-second stage attempted all thirteen jobs that had never
started, using unchanged inference/grading settings. It reloaded and warmed the
model for each job, so restart effects limit latency comparisons. This execution-
protocol deviation was disclosed before continuation; no failed request was replayed.
The completion driver returned exit 3 because some searches remained incomplete.

Primary source: `11d3d7d0a2c2d81c38a25381b7cf2f2df0f748af`; completion source:
`dc91df9d843c41d35221dbd72065b1d348738cda`. All captures show clean source trees.
Generation/scoring code and all frozen hashes agree across these stages. This is
one interrupted comparison with a declared completion stage, not a second chance
for failed answers or an uninterrupted benchmark.

## Evaluation results

Each mode has 12 planned runs: six worlds, two seeds. A completed answer means a
valid final frame, irrespective of factual correctness or verdict-label spelling.
The frozen first-word metric includes every unfinished run in its denominator.

| Mode | Completed | Matching verdict | Wrong recognized verdict | Unrecognized label in completed answer | Unfinished |
| --- | ---: | ---: | ---: | ---: | ---: |
| Greedy | 8/12 | 6/12 | 2 | 0 | 4 |
| Likelihood search | 12/12 | 6/12 | 3 | 3 | 0 |
| Final-only Jev | 7/12 | 5/12 | 0 | 2 | 5 |
| Step-guided Jev | 7/12 | 6/12 | 0 | 1 | 5 |

All six unrecognized labels were the literal spelling `ENTAINED`. Five appeared
with sensible positive conclusions on the chain/merge worlds; the sixth appeared
with an unsupported positive conclusion on the cycle world. These format failures
were not silently repaired, nor are they all being called factual errors.
Jev accepted some misspelled verdicts, so its completion judgment did not enforce
the question's exact label requirement. Likewise, a matching label does not prove
a correct explanation, as the example below shows.

| World / expected verdict | Greedy matches | Likelihood matches | Final-only Jev matches | Step Jev matches |
| --- | ---: | ---: | ---: | ---: |
| Longer chain / ENTAILED | 2/2 | 2/2 | 1/2 | 2/2 |
| Merged prerequisites / ENTAILED | 0/2 | 0/2 | 1/2 | 1/2 |
| Alternative negative derivations / CONTRADICTED | 2/2 | 2/2 | 1/2 | 1/2 |
| Negative chain / CONTRADICTED | 2/2 | 2/2 | 2/2 | 2/2 |
| Unseeded cycle / UNKNOWN | 0/2 | 0/2 | 0/2 | 0/2 |
| Missing prerequisite / UNKNOWN | 0/2 | 0/2 | 0/2 | 0/2 |

On the unseeded cycle, greedy and likelihood search invented a connection between
camera visibility and an access list. Step Jev rejected the irrelevant visibility
deduction and unsupported vault-entry claim, but no justified UNKNOWN answer was
offered. On the missing-prerequisite world, it accepted the test-certificate
deduction and rejected installation clearance without the required site permit.
It exhausted the available branches instead of answering UNKNOWN. At seed 42,
it also restored a saved alternate wording of the certificate step, demonstrating
live step-guided backtracking but finding the same unsupported continuations.

These cases show error rejection and a remaining proposal bottleneck; an empty
result is not a corrected answer. The previous 0/4 mechanism check used different
tasks and prompts and must not be treated as a directly comparable quality baseline.
This evaluation compares modes using the selected prompt; it does not include an
original-prompt evaluation arm or establish a general verifier-accuracy estimate.

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

## Actual work, timing, and integrity

Totals below include all completed, failed, and unfinished evaluation runs, but
exclude development. The means are descriptive observations on this machine;
fewer completed answers or an earlier rejection can reduce time.

| Mode | Mean seconds/run | Generated tokens | Padded decode slots | Repeated prefill tokens | HTTP attempts | Known Jev input tokens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Greedy | 12.25 | 952 | 952 | 41,386 | 0 | 0 |
| Likelihood search | 43.59 | 3,888 | 4,341 | 163,191 | 0 | 0 |
| Final-only Jev | 61.86 | 5,079 | 5,943 | 224,937 | 27 | 28,196 |
| Step-guided Jev | 33.47 | 2,923 | 3,126 | 119,928 | 37 | 38,739 |

There were 64 HTTP attempts, 63 successful responses with recorded usage, and one
ambiguous timeout. Known usage totals 66,935 input and 4,278 output tokens. The
configuration's historical input-only rate yields about $0.00281 for known input
usage; this is not an invoice and excludes unknown usage, output charges, and local
compute. Development adds 32 successful calls in its separately retained reports.

Step guidance spent 377.80 seconds in local generation and 23.81 seconds awaiting
Jev across its twelve runs; final-only selection spent 724.34 and 17.94 seconds,
respectively. Search paths and discarded work differ, so hosted Jev latency alone
does not explain the total difference. The API timing does not separate network
time from provider compute. No colocated or GPU-server performance was measured.

The primary process loaded once (3.45 seconds) and warmed two tokens at batch sizes
one and three. Completion jobs each loaded afresh and warmed size one, plus size
three for search modes; their individual metadata records loading. Warm-ups and
loading are excluded from per-run times. Python 3.12.13, Torch 2.8.0, Transformers
4.57.1, macOS 26.3.1, M1 Pro/MPS BF16, and the pinned original Granite revision were
used throughout. Backend metadata records zero trainable parameters. Every returned
Jev version was `jev-1.13.0`.

The offline audit reconstructed **244 proposal prefixes, 48 selected/partial token
paths, and eight backtracks** using the pinned cached tokenizer. Saved siblings,
child token concatenation, decoded full text, deduplication, eligibility thresholds,
prompt/fixture hashes, per-job summaries, and global counters agreed with the raw
traces. Totals: 12,842 generated tokens, 14,362 padded slots, and 549,442 prefill
tokens. No generated candidate contained the exact example names Pera, Dexo, or Bex.

| Mode | Candidate frames that parse / all candidates | Recorded exact duplicates | Batches with eligible children |
| --- | ---: | ---: | ---: |
| Greedy | 44/48 | 0 | 44/48 |
| Likelihood search | 177/189 | 89 | 51/63 |
| Final-only Jev | 216/258 | 113 | 51/86 |
| Step-guided Jev | 136/141 | 73 | 27/47 |

Parsing only checks frame structure. In unjudged modes an eligible child is not a
Jev endorsement. Duplicate counts are per parent across resamples; nine final-only
candidates generated at the deadline were retained but never classified/scored.
Distinct malformed candidates were recorded as premature EOS; the raw counts and
these distinctions are in [candidate accounting](evaluation/candidate-accounting.json).

Configured token, prefill, context, expansion, pending-branch, and API ceilings
held. Time limits are cooperative: three final-only generation stops returned at
90.08, 92.28, and 93.74 seconds against a 90-second setting; their late candidates
were not accepted. The separate scorer error returned at 90.0018 seconds. Retaining
these overshoots matters; this is not a hard real-time execution guarantee.

## Verification

At completion, 117 offline tests passed, including optional tiny-model checks.
Ruff lint/format checks, guidance-link validation, package build, and whitespace
checks passed. Test-first failures covered missing prompt/experiment capabilities,
invalid prompt-style types, positional config compatibility, mismatched problem
text in oracle joins, and exclusion of failed/cancelled jobs from completion.
No live inference was repeated for reporting or documentation edits.

## Artifacts and reproduction

- Development round 1: [metadata](development-v1/metadata.json),
  [all runs](development-v1/runs.jsonl), [summary](development-v1/summary.json).
- Development round 2: [metadata](development-v2/metadata.json),
  [all runs](development-v2/runs.jsonl), [summary](development-v2/summary.json).
- Primary evaluation: [metadata](evaluation-primary/metadata.json),
  [35 original rows](evaluation-primary/runs.jsonl), [original summary](evaluation-primary/summary.json).
- Completion stage: [manifest](completion/manifest.json) and its thirteen job
  directories retain each raw record, metadata, summary, and dispatched case.
- Combined evaluation: [provenance and hashes](evaluation/metadata.json),
  [48 unchanged raw rows](evaluation/runs.jsonl), [resource summary](evaluation/summary.json),
  [independent verdict grades](evaluation/verdicts.json), and [integrity audit](evaluation/integrity.json).
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
