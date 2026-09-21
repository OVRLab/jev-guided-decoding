# R14 execution plan and protocol v1

Registered 2026-09-21 before new model inference. Owner authorized full planning,
implementation, testing and a small Nebius/AWS GPU. This extends the
[design proposal](evidence-attention-proposal.md); it does not promise a gain.

## Navigation and deliverables

1. Implement authored evidence/answer data and independent grading, exact span
   mapping, a scoped attention hook, budgeted relevance scoring and a study runner.
   Files live under `research/experiments/evidence_*.py` with capability tests in
   `tests/test_evidence_*.py`. Preserve the existing production controller.
2. First run the new tests against missing capabilities; record the actual failure,
   implement, then verify the complete local suite and canonical project checks.
3. Freeze source/data manifests and this protocol before real inference. Start one
   inexpensive GPU only after local readiness; retain its exact hardware/software,
   private credential-transfer verification, cost timer and cleanup manifest.
4. On fresh development data run native/zero equivalence, individual-head profiling,
   oracle-span calibration and a live relevance pilot. Freeze selected parameters
   before touching held-out test outputs. Preserve every development attempt.
5. Run the admitted complete comparison, independently reconstruct token provenance,
   spans, intervention policies and grades; calculate paired uncertainty and controls.
6. Retrieve/hash-verify all raw data, delete task cloud resources, update the report,
   notebook/register/paper draft and review branch. Report negative outcomes too.

## Hypothesis and scope

Jev relevance over source spans can improve frozen Granite's evidence-grounded,
generated answers when a bounded bias changes selected internal attention heads.
The task is authored spatial containment QA, including irrelevant records, linked
facts and missing evidence. It is a mechanism study, not unrestricted chat, general
reasoning or an external-benchmark comparison with R10/R13.

Granite: `ibm-granite/granite-4.0-1b`, revision
`6a7381ba1f54d684ff508d991aeb7dc580157103`. Jev: `jev-1.13.0`.
Original weights remain frozen and are hashed before/after. Use the locked Python
environment, CUDA BF16, Transformers' existing SDPA implementation, one request at
a time. The local reference uses CPU float32 for tiny-model capability tests.

## Data, prompts and final ownership

Generate 24 profiling worlds, 72 calibration worlds and 360 held-out test worlds
from distinct fixed seeds. Each world has a complete-context and a distractor-heavy
version; profile only distractor-heavy cases, evaluate both versions elsewhere.
Test cases use a separately specified rendering template. Within each split,
cross chain lengths 1/2/3 with answerable/missing final link, balanced over six cells.
Randomize aliases, source order, target location and distractor relations. Missing
evidence must never be made answerable by an unrelated distractor.

The condition named `clean` has one unrelated three-link chain, while `distracted`
has six unrelated three-link chains. Thus clean means lighter distraction, not an
evidence context guaranteed free of irrelevant records. The same system instruction
in all arms explains that <focus> marks potentially relevant text and that all
records remain evidence. This does not change the source facts or answer choices.

Each world is a finite containment graph. An independent traversal grades the
room reachable from the queried parcel, or UNKNOWN if none is reachable. A second
construction-time expectation checks the graph grader. Oracle relevant spans are
the query's reachable containment chain, including the incomplete chain in missing
cases; they are privileged diagnostic data, never normal Jev inputs.

All evidence is retained in native and attention arms. No generated reasoning
steps are forced. Granite receives an instruction to answer from the records,
including UNKNOWN when a room is not established. The answer grammar permits all
six room labels and UNKNOWN in every case, regardless of truth. Require labels
to be distinct single tokens in the pinned tokenizer. Granite's next-token logits
choose the semantic answer; record the actual chosen token and all seven native
probabilities. This is explicitly constrained generated-answer QA. There is no
Jev final-label question and no code/reference substitution for the generated token.

## Internal intervention

Map character spans in the complete rendered chat prompt to exact tokenizer
offsets. Emphasize key positions belonging to the source span, only for query
positions after the evidence block. Apply a 4D additive causal attention mask at
selected query heads before softmax and value aggregation. Existing RoPE, GQA,
scaling and model parameters are retained. Scope hooks to a single request and
remove them even on failure; reject cached/incremental calls in this prototype.

Let relevance be r in [0,1]. Define emphasis e=max(0,2r-1); if all span scores are
equal, set every emphasis to zero. Add strength*e to the chosen evidence-key
coordinates of selected heads. Oracle uses binary span annotations. Unselected
heads and all other key positions receive zero added bias. This is a bounded
heuristic, not a claim that relevance is an attention probability. Zero strength
must pass the original mask through without changing the attention kernel path.

This first version computes one relevance map before generation; it is static
over the request. It guides internal attention during the final-answer forward
pass. The answer is Granite-generated but attention-guided, unlike R13's
unassisted final phase. Dynamic reasoning-prefix refresh and KV-serving optimization
are outside v1, not implied by a static hook.

## Development selection and admission

Profile every one of 640 individual query heads (40 layers x 16 heads) using
oracle span emphasis with strength log(4), on the 24 profile cases. Rank heads by
mean change in log probability of the reference answer; deterministic ties use
layer/head index. Record every native and intervention output, including negatives.

On the 144 calibration contexts, evaluate unions of the top 1/2/4/8 ranked heads
at strengths log(2), log(4), log(8). Select by highest overall accuracy, then mean
reference log probability, then fewer heads, then lower strength. These are tuned
development results, not independent quality evidence. Proceed to paid relevance
and the held-out study only if the selected oracle intervention improves calibration
accuracy by at least 3 percentage points while lowering clean-context accuracy by
no more than 3 points. Otherwise publish the negative causal-headroom result and
stop this mechanism without pretending Jev was tested.

Before profiling, compare no hook versus zero hook on every profile context: exact
chosen token and float32-logit maximum absolute difference <=1e-6 on the same
backend. Hook offset/mask validation and weight identity must pass. Run the selected
configuration and Jev scorer on 12 calibration contexts (one pair per design cell).
All calls must have valid typed receipts and token provenance; positive pilot
accuracy is not required. All development outcomes remain exposed and excluded
from the test. Freeze head/strength choice and all test source/data hashes before
test inference; no test-based retuning or best-run selection.

## Held-out arms and comparisons

The 360 test worlds each yield two contexts, for 720 contexts x eight arms = 5,760
planned outputs. Greedy generation has no sampling seed repetitions; the independent
statistical unit is the world, averaging its two context conditions.

| Arm | Operation |
| --- | --- |
| native | Original SDPA, complete evidence, no Jev |
| zero | Same hook interface, zero bias, no Jev; exact identity control |
| oracle | Selected heads with privileged relevant-span annotations; diagnostic only |
| jev | Selected heads with live Jev span scores |
| shuffled | Same Jev scores, deterministically permuted among source spans |
| lexical | Same heads/strength with normalized query/source content-word overlap |
| random_heads | Same Jev scores/strength, same number of deterministically selected other heads |
| prompt | Same Jev scores expressed as <focus> markers around spans with r>0.5, no attention hook |

The prompt arm changes tokenization/context length and is separately disclosed.
It retains all sources. Reuse each context's one Jev receipt across its dependent
arms; count actual calls once, and also report per-request deployment latency as
generation plus the shared call's latency. No live call is made inside a GPU layer.
Native/zero/oracle/lexical do not require a credential. Rotate arm order with a
fixed per-context seed; no benchmark references enter the normal model/scorer view.

Primary contrasts: jev minus native, shuffled, lexical and prompt. Use 10,000 paired
world-bootstrap replicates and 98.75% intervals for nominal 95% family coverage
across four contrasts. Report point differences, wins/losses/ties and per-condition
descriptive scores. A useful gain requires >=3 pp vs native and all four adjusted
interval lower bounds >0. Oracle and random-head comparisons are diagnostic.
All missing/failed outputs count incorrect in the frozen denominator. Assess span
relevance with independent chain annotations, including bridge and incomplete paths;
these are descriptive diagnostics, not a substitute for final-answer accuracy.

## Failures, budgets and audit

Preserve a durable started record before each scoring/model operation and an
immutable completed/failed row afterward. Fresh output directories only; never
replay a started job to replace an unfavorable or failed result. Provider requests
use the existing single-attempt transport and durable maximum input reservation.
Unknown paid usage remains conservatively charged. Stop on malformed responses,
authentication, model/backend or integrity failures. For explicit 429/529 responses,
record the affected Jev-dependent outputs as failed, retain their denominator,
wait at least Retry-After (default 60 seconds, at most 300), and continue only
never-started contexts, for at most three incidents. Explicitly acknowledge unknown
usage at maximum charge under this recovery policy before later calls; never erase
the reservation or call it a receipt. No ambiguous timeout is automatically replayed.

Prior cumulative estimate is $8.488813983 before tax/network. Keep $50 total as
the ceiling, with at most $3 new conservative Jev reservations and $25 new cloud
charges, leaving headroom for taxes/network/cleanup. Plan one L40S at about
$1.56/hour including CPU/RAM/disk, verify current price/capacity before launch.
Initial VM expiry is six hours; extend only if elapsed/projected total stays below
the cap. Stop the experiment before 14 total new cloud hours or its remaining
budget, whichever is earlier; independently monitor from the client and preserve
data if stopped. No 8-GPU machine. Benchmark deadlines must fit inside VM expiry.

Save source/data/manifest hashes, exact input IDs and token/span ranges, Jev payloads
and typed receipts without secrets, applied biases/head IDs, output-token logits,
mask/offset audits, model weights, timing, errors and source revision/dirty state.
Independently reconstruct each prompt, control map, allowed output distribution,
chosen token and graph-derived grade. Recompute paired statistics from raw rows.
Back up every result and verify hashes before deleting only task-owned VM, disk,
security rules and allocated addresses. Publish the authored fixtures, raw traces,
analysis and figures, with model/service sources and limitations.

## Execution log

- Plan written before implementation/inference; capability tests and outcomes will
  be recorded in the dated R14 report. This is prospective experimental design,
  informed by exposed R10/R13 outcomes, not a claim of external preregistration.
