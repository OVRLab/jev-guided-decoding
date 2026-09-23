# R21: focused feedback on Granite intermediate decisions

**Local feedback is promising on these controlled tasks; downstream improvement
has not been measured here.** Jev correctly separates supported and unsupported
claims among all oracle-assessed Granite drafts in two fresh cohorts. The first
cohort has insufficient natural error exposure for its registered admission; the
fixed fresh replication passes. The conditional learned-bridge pilot is R22,
registered separately in its [plan](../../research/learned-feedback-bridge-plan.md).
Its subsequent [completed result](../2026-09-23-learned-feedback/README.md) finds
no added Jev benefit over the equally trained adapter control.

| Observation | R21A: 192 worlds | R21B: 384 new worlds |
| --- | ---: | ---: |
| Constructed support judgments correct | 384/384 | 768/768 |
| Assessed Granite drafts | 192/192 | 383/384 |
| Supported drafts accepted | 180/180 | 347/347 |
| Unsupported drafts rejected | 12/12 | 36/36 |
| Unassessed drafts | 0 | 1 |
| Registered training admission | No: fewer than 20 natural errors | Passed |

These are verifier judgments, **not Granite+Jev final-answer accuracies**. The
constructed and generated claims can coincide and are evaluated in the same
request; they are not independent samples to pool into a larger success rate.
No branch was selected or hidden state changed in R21. Granite generated the
intermediate names; the checker did not supply an answer to the later color task.

## Method and retained limitations

The [original protocol](../../research/semantic-feedback-plan.md) fixes six motifs:
direct assignment, passive wording, reassignment, explicit negation, unconfirmed
rumor and distractors. Independent event records determine the currently assigned
courier; badge records define a later two-link task. Original Granite 4.0-1B,
revision `6a7381ba1f54d684ff508d991aeb7dc580157103`, produces one full-vocabulary,
greedy, at-most-24-token intermediate name in FP32 on local Apple MPS. No output
grammar or UNKNOWN label is forced. Exact draft token IDs and text are retained.

A common wrapper converts each name into an explicit parcel-assignment claim.
Jev 1.13.0 receives only assignment evidence and three separately questioned
claims: constructed supported, constructed unsupported and Granite's draft, in a
deterministic shuffled question order. It does not receive badge facts, final
reference colors, oracle labels, or the bookkeeping question-order map. Each claim
gets independent support and completeness Nouls. Support is classified at 0.5;
all raw probabilities and returned versions remain available.
The constructed controls include the true intermediate identity among unlabeled
claims. Cross-question cues are possible; draft-only verification was not tested.

The independent oracle accepts only a whole known courier name, allowing case,
whitespace and terminal periods. It does not infer a missing entity from evidence
or give credit to a fragment/citation. This prevents R20's completion-by-judge error
in the scored subset, but it does **not** validate arbitrary natural-language
reasoning, support every paraphrase, or make a structured name task general QA.

The first cohort made 12 natural errors across five motifs. Its frozen
`admitted=false` is preserved. The [replication](../../research/semantic-feedback-replication.md)
was registered after that result, with a fixed 384-world sample, unchanged
templates/rubric/thresholds and no enrichment toward observed error motifs. It
made 36 assessed errors across all six motifs. The replication alone meets the
original admission requirements. This is an adaptive engineering sequence, not
a pristine first confirmatory test or proof of a universal error rate.

The one unassessed replication draft is **`Fo`**, case
`r21b/7790edfbf55a085c3b21`; Jev assigns its wrapped claim **0.79 support**.
The response does not identify a full known courier. It remains unassessed in the
frozen primary metric, and its high support is a warning about partial names and
the claim wrapper. Do not summarize this study as Jev rejecting every possible
bad output. The 383/384 coverage denominator must accompany its natural results.

Constructed world-bootstrap intervals are [100%,100%] because no binary errors
occurred; this degenerate empirical bootstrap is **not** evidence of population
certainty. In particular, 12/12 or 36/36 observed error detections still have finite
sample uncertainty. No feedback prompt or threshold was tuned on either cohort.

## Integrity, cost and next architecture test

Both reconstruction audits pass: **576 generated drafts, 2,768 accepted draft
tokens, 576 successful physical Jev requests, 760,306 input tokens and no unknown
calls**. Source/data hashes, original weight hashes, exact prompt/draft tokens,
question mappings, raw provider probabilities and durable spending all agree.
R21A takes 233.00 seconds including load/hash; R21B takes 438.26 seconds. Mean
generation/API time is 0.804/0.284 seconds in A and 0.776/0.310 seconds in B.
This is serial local research timing, not serving throughput.

Both runs use the local cached checkpoint; **no cloud resources were created for
R21**. Estimated API cost is **$0.031932852**, cumulative **$32.58346360254077/$50**
before subsequent R22 work. Local electricity/depreciation is not estimated.
See [cost.json](cost.json), [A audit](admission-audit.json),
[B audit](replication-audit.json), [A analysis](admission-analysis.json), and
[B analysis](replication-analysis.json).

The evidence supports testing whether a learned internal bridge can use this
focused signal. It does not establish that earlier attention placement caused the
mixed results, that an adapter will improve final answers, or that the design is
novel. R22 compares equal-capacity trained adapters with real versus constant
feedback and a shuffled-feedback ablation, while Granite owns every final token.

## Reproduction and verification

Frozen scientific manifests: [A](../../research/protocols/semantic-feedback-v1/manifest.json)
and [B](../../research/protocols/semantic-feedback-replication-v1/manifest.json).
A's scientific source commit is `267a8de`, inference/data commit `af81e8c`; B's
source commit is `6307383`, inference/data commit `18f6f2e`. The recorded dirty
flags include newly generated, not-yet-committed cohort files; individual source
hashes bind the exact code used. Existing R20 scientific hashes remain unchanged.

All raw run files are losslessly compressed under [artifacts](artifacts/), with
original and compressed checksums in [raw-artifact-hashes.json](raw-artifact-hashes.json).
Extract each `admission-*.gz` or `replication-*.gz` into a fresh directory, removing
the corresponding prefix and `.gz`, and run the matching command:

```bash
uv run --no-sync python research/diagnostics/semantic_feedback_audit.py \
  --freeze research/protocols/semantic-feedback-v1 --results /path/to/admission
uv run --no-sync python research/diagnostics/semantic_feedback_audit.py \
  --freeze research/protocols/semantic-feedback-replication-v1 --results /path/to/replication
```

The offline audit requires the pinned tokenizer in the local cache but makes no
Jev request and performs no Granite forward pass. Test-first records are retained
alongside logs. Initial collection failures established missing implementation
files; a subsequent assertion caught an overly broad substring test (`red` inside
a fictional name), corrected to whole-word checking without changing the data or
scorer. Final focused checks and the full suite pass; see the repository's R22
handoff for the later combined suite count. No merge or model release is implied.
