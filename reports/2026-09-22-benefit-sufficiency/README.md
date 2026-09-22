# R19: expected benefit and evidence sufficiency

**Running; quality results pending.** Original Granite generates every final token.
A local regression controller predicts whether a Jev intervention will help; Jev
separately judges source relevance and whether the evidence supports an answer.
Low sufficiency emphasizes the existing abstention instruction inside selected
attention heads without forcing an answer or changing the prompt or model weights.

[Prospective plan](../../research/benefit-sufficiency-plan.md) ·
[Architecture and controls](method.md) · [Validation](validation.md).

The data freeze contains 260 fit, 200 calibration and 608 held-out test inputs,
with seven test configurations and 6,096 total planned generation outcomes. Test
grades will not be inspected until all scheduled work and its independent audit
complete. The model has passed twelve real-checkpoint admission checks: maximum
logit difference and all-layer cache difference are both 0.0 against independent
native, relevance, failure and instruction-bias replay. Canned admission scores
made no hosted calls; the subsequent fit phase uses the real hosted Jev service.

445 tests pass locally and on the GPU host. One historical test was corrected to
use a deterministic clock before inference; all scientific source hashes remain
unchanged. Source/data protocol was committed at `73a26e0`; execution is pinned to
`8b0ab3f`, which adds only tests and report material. One L40S is bounded by a
six-hour automatic expiry, a five-hour inference deadline and $10 cloud/$2 API
reservations within the existing $50 cumulative authorization. Costs and cleanup
will be reported after verified artifact retrieval and deletion.

A [separately registered supplement](../../research/benefit-sufficiency-controls.md)
adds 1,216 outcomes after main completion: static instruction emphasis with no Jev,
and shuffled sufficiency using only existing receipts. Registration occurred during
fitting, before calibration selection/test inference or quality inspection; main
primaries remain unchanged. Its contrasts are exploratory.
