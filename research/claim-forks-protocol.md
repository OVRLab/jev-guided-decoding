# R12-A2: property-boundary forks

Registered 2026-09-21 before V2 inference. This is the second and final development
proposal version for the current gate. The Jev rubric is unchanged. The frozen V1
data remain unchanged, including the 100 gate worlds whose outcomes have not been
generated or inspected. V1 results are retained under their original parser.

## Development finding and declared revision

V1 completed 60 worlds and 180 proposals. Only two worlds provided fully graded
mixed-quality scored sets. Among 66 unassessed proposals, 23 lacked a parsed body
and 40 used the exact positive wrapper “It is established that …”. The remaining
three need no retroactive label for this decision. Conditional on the 59 unique
graded/scored candidates, all 17 false claims had support below 0.2 and all 42 true
claims had support at least 0.8. These are correlated candidates from a narrow
development task, not a general accuracy estimate or a passed held-out gate.

The second version changes candidate opportunity, not the critic question:

- Granite samples its own prefix, up to 32 tokens after the shared `<step>` marker.
- The first complete subject/copula boundary (`X is`, optionally under an
  established/not-established wrapper or followed by `not`) becomes a checkpoint.
  Only entity names present in the authored input metadata locate the boundary;
  reference closure and truth labels remain unavailable to this operation.
- At that prefix, take four distinct top-probability tokens from the full native
  distribution and greedily continue each, at most 32 tokens including its forced
  first token. This is a search proposal policy, not four independent native samples.
- Score each complete claim using the unchanged two-Noul local support/assessability
  rubric. The exact full-claim parser additionally accepts the positive established
  wrapper; it still rejects compounds, partial claims and arbitrary justifications.
- Keep every no-checkpoint, incomplete and unassessed outcome. Require at least
  80% checkpoint coverage in addition to every original admission criterion.

The common prefix is excluded from branch likelihood. The comparator averages
log probability over branch tokens, including the native probability of its forced
root. This length-normalized search heuristic differs from ordinary native sampling.
Forced roots are counted separately from actual lookahead model work. All repeated
prefill, shadow decoding, native-prefix sampling and request usage are retained.

This is a disclosed deviation from V1's three complete sampled proposals. It was
chosen solely from development evidence. No third proposal revision will be tuned
on these gate outcomes. Development findings are reviewed before running the gate;
the frozen choice then runs all 100 gate worlds once, including failures. A failed
gate closes admission to the larger answer-quality trial for this version.

## Runtime and controls

Original pinned Granite, MPS, BF16, temperature 1 and top-p 1; four roots, 32 prefix
tokens and 32 tokens per branch. Prefix seed `872191 + 64 * index + position`,
greedy branch decoding with its separate backend RNG. Stage limit 1,800 seconds,
90 seconds per world's proposal work, 15 seconds per branch and one 30-second Jev
attempt per eligible world. These are cooperative wall limits, not process kill
deadlines. Context overflow, backend/provider failure or unknown paid usage stops
the stage. Incomplete jobs stay in the planned denominator; unavailable compute
from a failed backend operation is explicitly unknown.

The existing shared historical Jev ledger continues; no new cloud resource is
needed. `claim_forks.py prepare` freezes source/data hashes before execution.
Development results precede the gate; neither stage is a final-answer comparison.
Broader causal, arithmetic and unrestricted-language strata from the umbrella
plan are not silently represented by these six symbolic motifs. A separately
labeled authored diagnostic may inspect them, but cannot admit the quality study.

The optional `logit_runtime.py` implements the actual returned-logit inspection,
isolated sampling and discarded lookaheads. Its integration site is after the
model's final normalization, LM head and native logit scaling, before sampling.
No activation in any of the 40 transformer layers is changed. A separate bounded
mechanical run will test this on real Granite without presenting it as quality gain.

## Verification record

The new checkpoint/parser tests failed first because the script did not exist.
A subsequent interrupted-branch test failed on the missing record parameter;
the implementation now retains already-completed prefix and branch work if a
later branch fails. Twelve fork tests pass. The optional runtime's three tiny-model
tests passed after an observed missing-script failure: probabilities, unchanged
weights, zero-bias identity despite shadow work/global RNG changes, context and
invalid bias. Twelve sparse-bias tests check normalization, full-distribution KL,
untouched vocabulary mass, no-op and invalid inputs. These are offline evidence.
