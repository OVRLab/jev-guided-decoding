# R28: separating repair selection from internal feedback

Status: prospective protocol and implementation plan, 2026-09-25. The owner
raised the cumulative research ceiling to **$125**, authorizing this follow-up
and manuscript preparation. Prior conservative cost is $103.82976781335556;
remaining authorization is $21.17023218664444 before unconfirmed taxes. Historical
protocols, reports and the $110 closure estimate remain unchanged.

## Question and scope

Does Jev help by choosing answers to repair, by supplying correctly paired
feedback to the internal adapter, or both? R27 cannot separate these because
all six routed controls used the same Jev selection. Preserve the long-term
[north star](north-star.md); this study answers a narrower question.

Use the pinned, previously trained live R25 repair checkpoint after zero-indexed
Granite block 19, unchanged Granite 4.0-1B weights, FP32, greedy serial decoding,
2,048 new tokens for native and repair answers, and the existing instruction
repair prompt. No training, layer search, prompt tuning or threshold optimization.
References/evaluator metadata stay off the inference host and out of Jev inputs.

## Data and independence

Use all 541 upstream IFEval cases at Google Research commit
`e6890f85757dd84e27ca6df2dd30651dafad28e0`, with its original strict prompt-level
checker as primary outcome, loose prompt-level and instruction-level outcomes
secondary. Before inference, scan normalized prompts against earlier project
inputs; report exact/near overlaps and fix the eligible IDs in the manifest.
Exclude exact previous-prompt matches prospectively. Also exclude upstream keys
1122 and 1129: their letter-frequency metadata uses `#` and `!`, which the
unmodified checker replaces with random alphabetic letters. This defect was
found during metadata admission before inference; preserve all 541 source rows,
but generate/grade only the 539 valid eligible cases if there are no overlaps.
Report this as an eligible IFEval cohort, not an official full-541 result.
Any near-overlap sensitivity
is fixed before grading. Project-fresh does not mean absent from pretraining.
This is transfer to another public benchmark, not newly authored unseen questions.
Validate the grader on constructed pass/fail fixtures without inspecting generated
test answers. Pin evaluator files/dependencies and deterministic language detection.

## Fixed selection and feedback factors

Split eligible IDs into two deterministic, hash-balanced evaluation blocks. In
each block select floor(n/2) cases for repair, with no correctness labels used.

- `jev`: lowest Jev probability that the original answer fulfills all requirements.
- `confidence`: lowest mean generated-token log probability under original Granite
  (excluding terminal EOS; empty responses have lowest confidence).
- `random`: hash ordering with fixed seed 2801, independent of outputs and labels.

Use stable ID hashing to break score ties. Three selectors have equal repair
counts and token ceilings, not necessarily equal realized FLOPs or latency.
Jev-free policies have no Jev dependency in selection or constant-strength repair.

For every eligible case generate a constant-strength (0.5) repair with the **same
live-trained adapter**, allowing complete paired potential-outcome comparisons.
For Jev-selected cases also generate live feedback strength `1 - p_correct` and
shuffled feedback. Donors are a seeded cyclic derangement **within the selected
cases of each block**, preserving exactly the gate distribution and selection.
The resulting policies are native, constant repair of every case, Jev/constant,
confidence/constant, random/constant, Jev/live, and Jev/shuffled. Also compute a
fixed 100-seed random-selection sensitivity from the same complete constant pool.
No outcome determines selection, donors or the number of repairs.

These policies reuse fresh deterministic potential outcomes. This is a paired
policy evaluation, **not separately deployed runs or measured request savings**.
Every original answer calls Jev during data collection; report that cost. Timing
per policy is an attributed work sum, not end-to-end serving latency. Record all
shared and unused counterfactual generation, API calls and load/admission work.

## Analysis, success and stop rules

Freeze selections/donors before any repair grading; do not grade until completion
and integrity admission. Primary paired contrasts (one family of four):

1. Jev/constant minus random/constant (repair selection).
2. Jev/constant minus confidence/constant (repair selection).
3. Jev/live minus Jev/constant (case-specific feedback magnitude).
4. Jev/live minus Jev/shuffled (case-score correspondence).

Report strict scores, wins/losses, empty/truncated outputs, actual token/prefill
work and hosted API use. Use 20,000 paired stratified bootstrap draws (seed 2800),
98.75% intervals for the four planned contrasts, and unadjusted 95% intervals
clearly labeled descriptive for native and other comparisons. A positive component
claim requires both its contrasts' corrected lower bounds above zero and each
point estimate at least +2 percentage points, with direction agreeing across the
two disjoint blocks. The margin is a prospective practical threshold, not a power
guarantee. The blocks are consistency checks, not independent model replications.
For n~541 this modest experiment may miss small effects; a null result is not
proof of equivalence. Use all eligible cases, without optional stopping on scores.

If selection passes, prioritize selective repair. If internal feedback passes,
register a separate richer-feedback hypothesis. If neither passes, close this
specific scalar-feedback configuration without a larger architecture sweep;
publish its limitations and determine a genuinely different next design through
prior art. No larger-model or ten-benchmark victory can follow from this study.

## Implementation, failure modes and verification

Add a separate `research/iterations/routing_feedback/` module and dedicated tests;
never edit frozen R25/R27 runtimes. Reuse their cache, hook, prefix and paid-request
contracts. Add native log-probability observation without changing logits, and
verify exact output parity on an exposed admission fixture. Bind original weight,
adapter, tokenizer, data, evaluator and source hashes. Audit every output prefix,
decode, hook position, selection/donor, API receipt and work record before grades.

Test first: equal-count routing/ties/invalid inputs; no self-donors and preserved
selected-score distribution; reference-free inference records; selected-token
provenance; incomplete coverage and changed bindings fail closed; paired outcomes
and budgets; native likelihood observation does not change generation. Record
actual red/green evidence. Run repository lint, formatting, docs, tests and build.

Missing Jev judgments, unknown charges, failed source/hardware admission or missing
outputs stop the main study; preserve incomplete artifacts, with no replacement
scores or silent denominator reduction. Explicit retryable rejection may use the
existing bounded transport rules; ambiguous timeouts are never blindly replayed.

## Compute and manuscript

Use at most one inexpensive GPU, preferably a regular L40S to avoid the previous
preemptions. Before launch save a current rate/capacity admission, bound worker
and VM lifetime, reserve API/storage/cleanup headroom, and ensure projected
cumulative spend remains below $125. No larger comparator, training run or broad
benchmark extension in this tranche. Budget exhaustion preserves an incomplete
result rather than changing the evaluation sample. Check owned resources every
15 minutes while running, retrieve and hash artifacts, and delete owned resources.

Prepare a focused manuscript separately from the chronological lab notebook:
question, related work, method, R27 evidence, R28 results when available, limitations
and reproducibility. Preserve all previous studies, corrections and negative
findings in appendices/linked records. Do not claim novelty from a new diagram,
submit a paper, merge a PR or release a model as a side effect of preparation.

Preflight implementation note: R28 fails closed on any unresolved provider
attempt, including explicit rejections; it does not use inherited R26 retries.
The GPU provider is AWS G6 (L4) after Nebius CLI authentication expired;
current verified on-demand compute price is $1.0064/hour in Frankfurt.
A maximum 12-hour VM / 11-hour worker window and $18.50 stage reservation
leave conservative cumulative exposure below $125. Actual elapsed usage replaces
that reservation in final accounting.
