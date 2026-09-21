# R15: surgical refinement of evidence attention

Status before GPU inference: implementation and local verification complete;
development selection and fresh held-out results pending. The owner requested
iterating R14's positive native-baseline result with a complete controlled test.

The [full prospective plan](../../research/evidence-attention-v2-protocol.md) defines
90 configurations, fresh cohorts, twelve arms, selection floors, primary and
secondary claims, budgets, and cleanup. The [frozen manifest](../../research/protocols/evidence-attention-v2/manifest.json)
records exact source/data hashes, seeds, candidate policies and the original R14
comparison. R14's results and all-controls criterion remain unchanged.

## Implementation and initial failures

New code under [research/iterations/evidence_v2](../../research/iterations/evidence_v2/)
wraps the existing R14 runtime without modifying its source. It searches top-head
count, strength, soft/hard relevance mapping and question-versus-answer query scope.
One Jev receipt per context is shared across configurations, with every final token
chosen by Granite. It implements fresh no-overwrite outputs, durable starts,
conservative spending, retained provider failures and exact per-arm policies.

The first new test invocation failed at collection because the new policy/data
modules did not exist. Two later runner tests failed for the missing runner before
implementation. Formatting/lint errors during initial construction were corrected;
no quality results existed at that point. Subsequent boundary coverage, including
the composed tiny-model query-scope test, passed immediately and is not described
as a previously failing regression.

All **343 local tests passed in 3.46 seconds**, including eight new tests. A real
small Granite-family model verifies that answer-only steering leaves all earlier
query rows at their original causal-mask values, changes selected source keys at
the final position, preserves input state/model weights, and removes its hooks.
A mocked explicit overload yields exactly eight failed Jev-dependent outputs while
native controls run; it proceeds to the next context without retrying the failed
one. This is offline service-failure evidence, not a live Jev result.

All **1,632 fresh context variants** passed a tokenizer-only preflight against the
pinned real Granite tokenizer: 144–438 tokens, seven distinct single-token labels,
complete source offsets, no model forwards and no alias overlap with R14 or between
new worlds. Model/scorer inputs exclude reference answers and oracle source maps.

Expected complete run: 34,764 model decisions across development, zero checks,
primary test and longer-chain challenge; 1,632 live Jev calls. Independent full
artifact auditing, scientific figures, final claims and cloud cleanup evidence will
be added after execution. Current cumulative estimate remains $9.27/$50, with no
new GPU allocated at this pre-execution checkpoint.
