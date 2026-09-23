# R21: local semantic feedback and a learned internal bridge

Registered 2026-09-23, before new model/provider inference. The owner authorized
the staged proposal: validate Jev on local Granite reasoning, then train an internal
adapter if the signal is useful. This extends research scope to **new adapter
weights**, while original Granite and hosted Jev weights remain frozen. It does
not authorize changing old studies, merging the PR, or releasing a model.

## Question and stages

Can a focused judgment about a generated intermediate decision usefully condition
Granite's subsequent hidden computation? R19/R20 used handcrafted attention biases;
R11 already tested local claim scoring for branch selection. Repeating either is
not the proposed contribution. A learned conditional representation intervention
is a hypothesis, not an established new architecture or novelty claim.

**A — feedback admission.** Create 192 fresh fictional parcel/courier/badge worlds,
32 each of direct assignment, passive wording, reassignment, explicit negation,
unconfirmed rumor, and irrelevant distractors. Split by independent world, with
disjoint names from previous studies. The final task needs assignment plus badge
color, but Granite first produces the courier as an intermediate draft. Generate
one unconstrained, greedy draft per world, capped at 24 tokens. Wrap each name in the same explicit parcel-assignment claim for Jev; the wrapper
adds no final-answer information. Score exact courier
names with an independent structural oracle; other prose remains unassessed,
never silently false. Publish coverage and every unassessed output.

For each world also construct one supported and one unsupported courier claim,
with neither identified as such to Jev. These stress tests are separate from
Granite-produced drafts, not extra generator improvements. Ask independent Nouls
for support and completeness in one request. Send only assignment evidence, the
parcel and candidate claim; never the badge facts or final reference answer. Use
Jev 1.13.0, one attempt, no prompt/threshold tuning after results. Threshold 0.5
is a diagnostic decision boundary, not confidence in downstream correctness.

Admission for adapter training: all expected records accounted for; at least 90%
balanced support accuracy on the constructed pairs, at least 75% in every motif;
at least 80% independently assessable Granite drafts; at least 20 supported and
20 unsupported assessed drafts, with at least 85% balanced accuracy on those
natural drafts. These are conservative engineering requirements for training on
this feedback, not significance tests or a universal success criterion. If too few
natural mistakes occur, report insufficient error exposure, not verifier failure.
An admission failure completes this stage with a documented reason; it does not
justify spending on an adapter whose prerequisite was not demonstrated.

**B — conditional implementation/training.** Only after A passes, register and
freeze a separate training/development/test cohort and exact optimization settings
before any optimization. Implement a rank-16 residual adapter after a Granite
decoder block, initially zero-output, conditioned on local hidden state and Jev's
support/completeness vector. Start with zero-based block 19 as an inherited
location, not a claim of optimal placement. The decision boundary is after the
intermediate draft and before the final answer. Only subsequent positions change;
past generated tokens remain exact and caches must match the actual computation.
No Jev tensor access, new text from Jev, forced final label, or branch selection.

Train the adapter using generated synthetic worlds with independently known
answers; start from existing Granite weights and update only the new adapter.
This supplies an explicit small task dataset without needing Granite's original
pretraining data. Compare native Granite, a matched trained constant-feedback
adapter, live-feedback adapter, and its permuted-feedback ablation. Oracle feedback
is a diagnostic ceiling, never a deployable result. Match prompts, draft tokens,
training examples/updates and adapter capacity. Freeze on development data and
evaluate fresh worlds. No superiority claim from beating only the untrained base.

## Evaluation and failure isolation

Avoid R20's automatic-judge completion errors. In A, the independent oracle labels
known entity responses only; citations, incomplete sentences, multiple entities
and answers outside the contract are unassessed, not completed by a judge. Label
constructed pairs directly from the independent world representation, review their
rendering before inference, and test reassignment/negation/rumor semantics. This
is controlled synthetic evaluation, not broad natural-language correctness.

Report confusion matrices, each motif, Brier error and world-paired bootstrap
intervals. Separate constructed signal quality from naturally generated mistakes.
Retain failed calls, unknown charges, exact prompts/tokens, returned model versions,
source/data hashes, hardware, latency and all attempted work. Granite produces all
draft/final tokens; Jev support is never a final-answer score. Any stage-B result
requires its own final-answer evaluation and causal ablation.

Affected files: new `research/iterations/semantic_feedback/` data, scorer, runner
and analysis; capability/negative-path tests; this protocol, research register,
project scope/status, dated report and manuscript. Keep old scientific modules
unchanged so their freezes remain reproducible.

Tests first: oracle rejects incomplete/multiple/wrong entities; motifs have the
intended truth; scorer payload excludes final answers; malformed/failed calls retain
reservations; duplicate/resumed jobs cannot dispatch again; optional imports stay
optional. If B is admitted, add zero-adapter parity, gradient/frozen-weight checks,
prefix/cache provenance and matched training controls before implementation.

## Resources and stop policy

Prior estimated cumulative spend: $32.55153075054077/$50. Reserve at most $0.50
Jev and $10 compute/disk for A+B, retaining more than $6 margin before tax/network.
Use the cached local model for A if practical, otherwise one L40S, with a maximum
five-hour VM lifetime and a shorter process timeout; verify live prices/capacity.
No replay of ambiguous paid requests; retain unknown requests at the maximum token
charge and stop A on a provider failure. Retrieve and hash results before deleting
all owned temporary resources. Report estimates separately from invoices.

## Related work and provider fit

- [ReFT](https://arxiv.org/abs/2404.03592) already learns interventions on a frozen
  model's hidden representations. A residual adapter alone is not a novelty claim.
- [TypeSafe citation checking](https://docs.typesafe.ai/cookbooks/citation_check)
  demonstrates focused support verification, not downstream Granite improvement.
- [Jev limitations](https://docs.typesafe.ai/model-jaggedness/jev-1.13) motivate
  focused context and separating local support from multi-hop task completion.
- [API](https://docs.typesafe.ai/api), [Noul](https://docs.typesafe.ai/primitives/noul),
  [models/pricing](https://docs.typesafe.ai/models), and
  [Nebius pricing](https://docs.nebius.com/compute/resources/pricing) checked at setup.

Focused judgments plus a learned bridge are an experimental combination. A broader
prior-art review and external task replication are required before novelty or
general reasoning claims. Measurement repairs proceed alongside architecture work.
