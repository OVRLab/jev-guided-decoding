# R16: head-specific, adaptive and free-text Jev attention

Status: prospective plan, 2026-09-22; register before new inference. This follows
[R15](../reports/2026-09-22-evidence-attention-refinement/README.md). The owner
authorized all three directions, relaxed output rules, cloud execution and full
documentation. Earlier datasets, policies and reports remain frozen. This finite
study explores the specified alternatives; it cannot exhaust every architecture.

## Questions and boundaries

1. Does tuning individual attention-head strengths improve on frozen R15?
2. Does refreshing relevance from Granite's generated intermediate text improve
   on the same staged generation with static guidance and without guidance?
3. Do gains survive unrestricted vocabulary, natural uncertainty, changed relation
   wording and an independent document benchmark?

Granite always generates semantic output tokens. Jev judges source relevance, never
the final answer. Original `ibm-granite/granite-4.0-1b` revision
`6a7381ba1f54d684ff508d991aeb7dc580157103` and hosted `jev-1.13.0` stay fixed.
No weights are trained. New code lives in `research/iterations/adaptive_attention/`;
R14/R15 source files are unchanged. No vLLM extension or checkpoint release.

## Development, policies and independent tests

Use 96 new development worlds, balanced answerable/missing and depths 1–6, with
one heavy-distractor context each. Exclude every alias in R14/R15. Rank no new
heads: start from the exact twelve R15 heads. Development runs frozen R15,
leave-one-head-out (12), leave-one-layer-out (9), uniform strengths ln(4), 4 and 5,
then one ordered coordinate pass over the twelve heads with strengths
0, ln(4), ln(16), 4, 5. Reuse identical policy results; choose accuracy, then mean
reference log probability, then smaller total strength and deterministic ID.
Finally compare strict relevance thresholds .35/.5/.65/.8 and continuous
`max(0,2r-1)` on the selected strength vector. All-equal scores remain a no-op.
Selection has no hard subgroup harm floor; report subgroup regressions explicitly.
These development results are exploratory and optimistically selected.

Freeze the selected vector and mapping before test. Use 300 new test worlds,
balanced across depths 1–6 and answerability, each with light/heavy distractors
(600 contexts). The first 120 worlds (240 contexts) also receive two transfer
renderings: paraphrased containment and a dependency/terminal-colour relation.
Each rendering preserves its own independently verified graph answer.

Use 200 HotpotQA distractor development-set questions for external evaluation,
selected by seeded shuffled IDs and input length only (complete ten-paragraph
contexts, at most 2,048 prompt tokens; no answer/support-based filtering). Reserve
the first 12 other eligible questions for mechanics only, not policy tuning.
This is an independent dataset, not an unseen-pretraining guarantee or an official
leaderboard submission. Preserve upstream IDs, data hashes, CC BY-SA 4.0 notice,
source URL and full selection/exclusion record. No supporting facts enter inputs.

## Output contracts and arms

All arms within a panel share prompts, original evidence, greedy decoding and token
budgets. Constraints apply only to the explicitly constrained panel:

- **Constrained:** original R15 prompt and seven single-token choices, including
  UNKNOWN. Native, frozen R15, tuned policy, shuffled tuned, lexical tuned, zero.
- **Open explicit:** full vocabulary, short free-text answer, instruction to express
  insufficient evidence in the model's own words; no answer list or required token.
- **Open neutral:** full vocabulary, short answer, no special uncertainty instruction.
  Both open contracts use native, R15, tuned, shuffled and lexical; final cap 32 tokens.
- **Staged open:** three chunks of up to 24 unrestricted reasoning tokens, followed
  by a controller-supplied final-answer cue and up to 32 final tokens. Newline/EOS
  can end a chunk early; EOS ends reasoning. Exact generated token IDs are retained,
  with framing separately attributed. Native, R15-static, tuned-static,
  tuned-dynamic, shuffled-dynamic, lexical-dynamic; no rejection or path selection.
  Run on the first 120 test worlds and both transfer renderings, plus HotpotQA.
- **Hotpot direct:** open explicit native/R15/tuned/shuffled/lexical. Staged arms as
  above. No candidate answer list; 32 final tokens, standard answer EM/F1.

Initial synthetic relevance retains the R14 containment rubric on the original
rendering. Transfer/external tasks use generic question-to-source relevance.
Dynamic refresh after chunks 1 and 2 asks which records help the next reasoning
step, considering generated text as fallible claims and original evidence as
authoritative. All source questions are batched. Static calls/receipts are shared
only for byte-identical payloads; divergent dynamic prefixes get separate calls.
Shuffled controls deterministically permute the corresponding scores. Lexical
controls use question/current-prefix word overlap, without hosted calls.

## Internal mechanism and cache semantics

Add per-head bounded nonnegative source-key bias (maximum 5) before softmax at
post-evidence query positions. Implement cached autoregressive generation with
absolute query/key positions and isolated per-request state. A refresh affects
subsequent computation; existing higher-layer cached states are not recomputed.
This is an append-only intervention, not retroactive revision of earlier reasoning.
Validate static cached versus full-prefix logits (maximum absolute BF16 difference
0.125 and equal greedy argmax), zero identity and exact R15
equivalence before study admission. No HTTP call is made inside a layer.

## Grading, evidence and interpretation

Predefine a conservative free-text synthetic parser: a single asserted colour or
recognized natural abstention; ambiguous/multiple contradictory colours and
unrecognized responses fail. Save exact text and parser coverage; separately report
strict normalized answer match and abstention/answerable accuracy. A match does not
prove a valid explanation. HotpotQA uses upstream normalization/EM/token F1 on the
complete final text, without extracting an answer using its reference or Jev.

Keep every failed/empty/truncated outcome in denominators. Case/world-clustered
paired bootstrap, 10,000 draws. Three primary contrasts: tuned minus R15 on the
constrained 300-world panel; dynamic minus tuned-static on staged original
120-world panel; tuned minus native on direct Hotpot answer F1 (200 questions).
Use individual 98.333% intervals for nominal 95% coverage across these three.
Other comparisons and output-contract/transfer analyses use exploratory 95%
intervals. Report gains independently; no requirement to beat every control to
recognize a measured improvement. No overall success label hides negative panels.

## Plan, failure policy, resources and verification

1. Implement independent data/grade tests, head/cache tests, exact token/phase tests,
   and transport/budget/resume tests first; observe the actual failures.
2. Implement new hook/runtime, scorer, finite study and independent artifact audit.
3. Freeze data, source hashes, grader, contracts and scientific protocol; commit.
4. Provision one L40S or comparably priced GPU. Validate token transfer privately,
   pinned versions, tiny/full-model zero/cache/R15 equivalence and clean startup.
5. Run development, freeze selection, execute every planned panel; retain all raw
   payloads/receipts/prompt tokens/output tokens, logits summaries, phases and costs.
6. Independently reconstruct schedule, source spans, grades, selection, provenance,
   zero controls, score receipt binding and paired statistics. Retrieve and hash
   verify artifacts, delete all task cloud resources, publish the complete report
   and update notebook/register/manuscript/PR. Publication means repository evidence,
   not paper submission or merging a model checkpoint.

Stop before more than $5 Jev usage or eight GPU hours (cloud allowance $15),
below the $38.82646528 remaining original budget; use an eight-hour VM expiry and
local cleanup monitor. Reserve maximum input charge before each paid attempt.
90-second API timeout, one attempt per unique payload, no ambiguous replay.
Failed payloads remain failed and are memoized; preserve usage unknown at its
maximum. Continue independent jobs after transient 429/502/503/504/529/timeouts,
with 60-second minimum cooldown, honoring larger Retry-After up to remaining
deadline. Stop new calls at 20 incidents or 3 consecutive incidents; authentication,
contract, integrity, budget, model nonfinite or context errors stop immediately.
Resume only never-started jobs with identical source/data/config hashes. A started
unfinished model job is recorded interrupted, not silently rerun. All operational
amendments get separate records and cannot modify policy after test begins.

Failure modes include stale relevance reinforcing an erroneous step, excessive
bias harming useful heads, cache/mask causality mistakes, natural-answer grading
coverage, prompt-length selection bias and small subgroup uncertainty. Results
must name these limits and measured costs, not promise a general reasoning gain.

## Primary sources consulted

- [PASTA](https://arxiv.org/abs/2311.02262): selective attention steering precedent.
- [TypeSafe API](https://docs.typesafe.ai/api), [Noul](https://docs.typesafe.ai/primitives/noul)
  and [reranking](https://docs.typesafe.ai/cookbooks/rerank_typesafe): typed judgments.
- [HotpotQA](https://hotpotqa.github.io/): external data, license and official grader.
