# R22: a learned internal feedback bridge, with no observed Jev benefit

Completed 2026-09-23 on one Nebius L40S. The trained bridge works mechanically,
but its generated answers show **no added value from Jev** on this fresh narrow
test. A slightly higher score than native Granite is shared by the equally trained
constant-feedback control and is statistically uncertain.

| Final-answer generator | Correct / evaluated | Exact color accuracy |
| --- | ---: | ---: |
| Original Granite, staged prompt | 349 / 384 | 90.89% |
| Granite + equally trained constant-feedback adapter | 355 / 384; 353 / 384 | 92.19% mean |
| Granite + Jev-conditioned adapter | 355 / 384; 353 / 384 | 92.19% mean |
| Same Jev-trained adapters, shuffled feedback | 355 / 384; 353 / 384 | 92.19% mean |
| Same Jev-trained adapters, oracle feedback | 355 / 384; 353 / 384 | 92.19% mean |

The two counts are seeds 2201 and 2202. There are **384 independent test worlds**,
not 768 independent examples or 3,456 independent problems. Native is generated
once per world; all other arms twice, yielding 3,456 test answers. All final tokens
come from Granite's unchanged vocabulary head, with no label grammar or forced
UNKNOWN. Every task has one established answer; this is not an abstention test.

The primary live-minus-native effect is **+1.30 percentage points**, individual
97.5% paired world-bootstrap interval **[−1.30, +4.04]**. Live-minus-matched-control
is **0.00 pp**, empirical interval **[0.00, 0.00]**. The latter is degenerate because
every paired correctness value agrees, not proof of universal equivalence.

Shuffled and oracle feedback produce **exactly the same final token IDs as live
feedback on all 384 worlds in both seeds**. Live and constant have the same
correctness on every world; their token IDs match on 383/384 and 384/384 worlds.
The remaining difference is one incorrect color becoming a different incorrect
color. The evidence supports task adaptation with no observed feedback-dependent
answer benefit. It does not prove that activations or probabilities are identical,
nor that all possible bridges would ignore feedback.
An additional [post-result tensor check](feedback-path-diagnostic.json) finds
nonzero changes in the learned conditioning weights, and the permutation changes
301/384 feedback vectors. Thus the identical answers are not explained by an
identity permutation or wholly unchanged conditioning weights. The saved residual
norms scarcely change; that alone cannot establish the cause or quantify hidden
state directions.

## What was built and trained

The [architecture diagram and controls](method.md) show the actual intervention:
Granite generates an intermediate courier name; hosted Jev evaluates that local
claim against assignment evidence; its support/completeness probabilities condition
a **65,568-parameter rank-16 residual adapter after zero-based block 19**. Granite
then generates the badge color. Jev sees no badge facts or final reference.

Only the new adapter weights are trained. Original Granite and Jev stay frozen.
Training uses 384 synthetic worlds, two authored correct/incorrect drafts per
world, and structurally known final answers. These authored training drafts are
not Granite generations. A separate 96-world development set selects the epoch;
384 fresh test worlds supply actual Granite drafts. Logical templates overlap
across splits; identities, assignments and badge permutations are new. Despite
the inherited `r21b/` ID prefix, these are distinct R22 worlds.

Four models train for two epochs each, with equal initialization/order within
seed, optimizer settings, training examples and parameter capacity. All four
select epoch one, with development scores 84/96 for seed 2201 and 85/96 for 2202.
Each selected checkpoint contains 96 optimizer updates. `selection.json`'s
`updates: 192` records total training performed per model, including the unselected
second epoch; it is not the selected checkpoint's update count. All 12 initial/
epoch adapter checkpoints are retained in safetensors archives.

The [frozen plan](../../research/learned-feedback-bridge-plan.md),
[data/source manifest](../../research/protocols/learned-feedback-v1/manifest.json),
[selection](selection.json) and [audit](audit.json) bind the experiment. Scientific
source commit is `499577f`; data/inference revision is
`dffb8e4e0eceefc0156487b3337f7da3380d9f43`. No test outcome changed a checkpoint,
hyperparameter, layer or endpoint. The [related-work check](../../research/learned-feedback-related-work.md)
documents close prior work; no novelty or generally improved model is established.

## What the errors tell us

Jev correctly classifies support for all 345 correct and 39 incorrect test drafts
under the independent whole-name oracle. This extends the
[R21 admission evidence](../2026-09-23-semantic-feedback/README.md), but correct
verification alone does not imply improved final generation.
Those requests also contain unlabeled constructed control claims, as detailed in
the [method](method.md); standalone draft-only verifier accuracy was not measured.

On the 39 wrong drafts, native gives 9 correct final answers; the live adapters
give 23 and 22. On 345 correct drafts, native gives 340 correct finals, versus
332 and 331 for the adapters. The matched constant controls have those same counts:
these repairs and regressions cannot be attributed to Jev. Across all worlds,
seed 2201 repairs 14 and regresses 8 native answers; seed 2202 repairs 13 and
regresses 9. See [all motifs and selected examples](tables-and-examples.md).

The secondary complete-color readout changes no correct counts. Native produces
384 recognized colors; every adapter arm produces 383 colors and one empty EOS
answer. The empty answer is retained as incorrect in the primary endpoint and
unresolved in the conservative secondary grammar. It is not silently completed.

The [secondary readout](../../research/learned-feedback-semantic-readout.md) was
registered at 05:42:52 UTC **after test draft preparation began**, but before the
first final answer at 05:44:31 UTC and before outcome inspection. An initial
description incorrectly placed registration during training because the backup
lagged; the [timing correction](readout-timing-correction.json) and original text
are preserved. This is a secondary descriptive readout, not a replacement primary
metric or validated general semantic judge. Additional examples and pairing counts
are explicitly post-result descriptions.

## Work, latency and cost

The completed audit reconstructs 6,144 teacher-forced training forwards, 768 total
optimizer updates, 768 development answers, 3,456 test answers, 2,298 generated
intermediate tokens and 8,440 generated final tokens. Training processes
2,804,952 input positions and 12,288 target positions. All 864 physical Jev calls
succeed on their first attempt: 1,140,354 input and 101,952 output tokens, no
unknown paid usage. The same fixed receipt is reused across offline evaluation
arms; this is not measured concurrent deployment.

On test worlds, average intermediate generation takes 0.173 s and the hosted
Jev call 0.275 s. Native final generation averages 0.0983 s; guided final
generation is about 0.1001 s. Adding the shared draft and API components gives
approximately **0.271 s native versus 0.548 s guided** for the staged paths, an
accounting sum rather than a separately timed serving benchmark. The API is
remote; colocated latency is unmeasured. Every final branch re-prefills its exact
conversation into its own cache, and that work is counted.

The study loop takes 1,496 s after model loading/mechanical admission; allocated
GPU tensor peak is 8.68 GB (8.09 GiB). The machine exists for 38.65 minutes including
bootstrap and cleanup. Estimated R22 cost is **$1.17799**, including $0.04789 Jev,
with cumulative **$33.76146/$50** before tax/separate network and local electricity.
[Cost assumptions](cost.json) conservatively charge through verified deletion.
The VM, managed disk, security group/rules and automatic IP allocations are
[verified deleted](cleanup.json). A CLI sign-in expiry delayed initial cleanup;
refreshing the existing login resolved it without any inference replay.

## Evidence and interpretation

All 27 frozen scientific source files, data hashes, exact prompt/draft/final IDs,
reference-free provider questions, raw probabilities/usage, intervention positions,
checkpoint selection and original-weight digest pass independent reconstruction.
Zero-initialized adapter logits match exactly; nonzero cached/full logits agree
within tolerance. Only adapter parameters receive gradients. Public compressed
artifacts reproduce the results and preserve all trained checkpoints.

- [Primary scores](analysis.json), [descriptive counts](descriptive.json),
  [secondary readout](semantic-readout.json), [mechanical admission](mechanical-admission.json).
- [Raw artifact hashes and archives](raw-artifact-hashes.json),
  [reproduction and validation](reproduction.md), [working manuscript](../../research/paper-draft.md#711-r22-learned-conditional-representation-bridge).
- [Figure](figures/results.png), with [vector version](figures/results.svg).

This is a completed negative attribution result for one layer, rank, training
recipe and narrow family of generated tasks. Native already performs well. Two
feedback probabilities may be too weak, or the training objective may let the
adapter solve the task without using them; those are hypotheses, not identified
causes. A future design should first demonstrate a causal change in generation
under controlled feedback changes on development cases, then test fresh transfer.
The current checkpoints are research artifacts, not a Hugging Face release or
a generally superior Granite+Jev architecture. No further paid run was launched.
