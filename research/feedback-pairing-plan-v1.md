# R30: within-draft feedback attribution and fresh replication

Registered 2026-09-26 before new model inference or Jev requests. This implements
the next decision in the [continuation program](feedback-exploration-program.md).
It tests fixed R29-A checkpoints, not a new trained model or public benchmark.

## Hypotheses and fixed data

R29-A raw structured repair improved 25.00% to 29.69% on 96 authored worlds and
beat donor-shuffled feedback, but did not establish superiority to separately
trained scalar feedback. Donor shuffling changes both overall reliability and
which answer receives each probability. R30 isolates those effects.

Generate **384 test worlds**, 192 temporal and 192 compositional, with seed 30001
and the same R29 templates, vocabulary, event count and three-room answer contract.
Reject duplicate prompts and any overlap with all 256 R29 worlds. Freeze cases,
separate references and hashes before inference. An independent graph replayer
must recover every reference from the supplied text. There is no new development
set, training, epoch selection or retention-threshold tuning in this stage.

Reuse the R29-selected structured and scalar adapters for seeds 2901 and 2902,
verified against the public R29 selection and backup inventory. Copy and hash the
four selected checkpoint files into the frozen input bundle. Preserve the original
Granite revision, FP32, greedy full-vocabulary generation, 128-new-token limit,
2,048-input-token cap and zero-indexed block-19 insertion. No silent truncation.
All original and adapter parameters stay frozen. Independently check their
digests before and after execution.

## Conditions

Generate one common native draft and one untrained blind repair per case. Obtain
one Jev 1.13.0 request containing the three unchanged R29 Noul questions, bound to
the exact native draft and problem, without reference answers. Then use the same
repair prompt, recipient question/draft memories and structured checkpoint for:

| Condition | Probabilities entering the branch |
| --- | --- |
| live | Correctly matched p1, p2, p3 |
| rotate_left | p2, p3, p1 |
| rotate_right | p3, p1, p2 |
| mean | Their mean repeated three times |
| donor | Probability vector from the next sorted case in the same task family |
| constant | 0.5 for every slot, same structured checkpoint |
| type_only | 1 if the parsed field is a known room name, otherwise 0; no state replay or Jev |
| oracle | Independently checked field correctness, same structured checkpoint; nondeployable |

Also run **scalar_trained**, using the separately trained R29 scalar checkpoint
and the repeated mean. The two cyclic permutations are the two possible
derangements of three positions; their multiset and mean match the live scores.
Uniform vectors can remain unchanged and are retained, not excluded. `type_only`
uses the fixed eight-room vocabulary and the frozen field parser, without knowing
which room is true. It is a cheap diagnostic for answer-type checking, not a
correctness oracle or forced decoding grammar. Its inherited training still used
Jev; inference for that arm does not need a Jev judgment.

There are **20 outputs per case, 7,680 total**, and **384 Jev requests**. Both
training seeds are fixed; native and blind outputs are shared across seeds.
Oracle flags are used only in the named diagnostic arm; live inputs and memories
must remain reference-free. Preserve exact original prompt/draft/final token IDs
and independent caches in every condition. Record intervention positions and
effective probability vectors, including donor identity.

## Analysis frozen before results

Primary outcome: all three requested room names correct under R29's unchanged
readout. Report per-field accuracy, requested format, empty/length stops, cases
fixed and native passes damaged, each task and each seed. The original native
denominator is always 384, including failures. Missing outputs make execution
incomplete and prevent a completed-study claim.

Three primary paired contrasts average correctness across the two training seeds:
live minus native, live minus same-checkpoint mean, and live minus the average of
the two within-draft permutations. Use 10,000 within-family paired bootstrap draws
with seed 3000; publish ordinary 95% intervals and Bonferroni **98.3333%** intervals
for this family of three contrasts. Case, not token or seed-output, is the
resampling unit. These remain conditional on two fixed training seeds.

Report all other pairwise live/control effects with descriptive 95% intervals,
and how often transformed feedback changes final token sequences. A ±2 percentage
point practical-equivalence band for live versus same-checkpoint mean is a
prospective secondary reference; only an interval wholly inside it supports that
narrow equivalence statement. It is not equivalence across tasks or architectures.

Separately replay (a) R29's frozen never-repair policy and (b) the prospectively
fixed policy retaining native when min(p) >= 0.5. The latter cutoff is informed by
R29's disclosed post-result diagnostic; it is not selected on R30. These are
secondary offline policies, not actual avoided calls or GPU work. Report every
comparison even if it disagrees with the main hypothesis; no conjunction of all
controls erases a supported native gain.

Decision: replicated native benefit supports continued study of repair; a local
benefit over both mean and permutation specifically supports localization. If the
mean matches or wins, pursue simpler reliability conditioning and better repair
capacity. Compare oracle and answer-type controls to diagnose whether extra
semantics helps. Do not claim the oracle score is a ceiling for future systems.
No result here establishes novel architecture, public transfer or larger-model
superiority. A subsequent architecture/transfer protocol must be frozen separately.

## Operational admission and budget

Reuse and recheck R29 real-model admission on the actual worker: zero/off identity,
frozen-gradient ownership and cached/full logits within 0.001 with equal argmax.
Test feedback transformations, disjoint data, exact checkpoint provenance, complete
coverage, reference isolation and audit rejection before paid execution.

The user increased the cumulative cap to **$175**. Starting conservative estimate
is $118.12281183983264. Reserve at most **$8.50** for R30: one L4 worker at a freshly
verified rate <=$1.02/hour for at most five hours, $0.18 study API cap, and disk,
network/IP and contingency allowances within the remaining reserve. Worker limit
is 4.5 hours; independent host shutdown at five hours. No unregistered second GPU.
The API has one reserved attempt per case and a 0.25-second deliberate delay;
unresolved errors stop the run and retain maximum unknown charges. Do not call
the delay an inherent Jev latency. [Current provider documentation](https://docs.typesafe.ai/models)
lists $0.042/M input tokens with free output; reserve using $0.05/M.

Monitor/backup at least every 15 minutes, independently audit a verified copy,
publish complete public-safe artifacts and delete owned cloud resources only
after exact inventory/hash verification. Preserve interrupted attempts. Completion
includes the report, notebook/register, research manuscript and repository checks.
