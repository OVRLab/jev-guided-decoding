# Study register

Registered retrospectively on 2026-09-21 from the existing reports and artifacts.
This register does not turn historical development work into preregistration.
Frozen source revisions, dates, raw availability, device, exact prompts and budgets
are retained in each linked report. Study IDs are notebook identifiers, not issues.
All live rows below used original Granite where generation was involved and the
hosted Jev service; none trained an improved checkpoint.

| ID / status | Evidence and scale | Output owner / observed result | Interpretation |
| --- | --- | --- | --- |
| R00 · completed smoke | [Initial smoke](../reports/2026-09-20-granite-smoke/README.md): 12 questions × 4 modes, plus 2 continuation-demo runs | Granite; guided mean 3.71 s vs greedy 1.10 s, lexical F1 0.8154 vs 0.8181 | Mechanism worked; lexical scores are not general accuracy. A correct ending was rejected and misleading causal wording was accepted. |
| R01 · completed diagnostic | [Intermediate investigation](../reports/2026-09-20-reasoning-investigation/README.md): 8 authored candidate sets × 2 rubrics, then 4 Granite runs | Both rubric policies matched the symbolic decision on 8/8 sets; generated traces included repeated premises and empty rejection | No rubric advantage; fixed authored candidates did not establish performance on real model proposals. |
| R02 · completed mechanism check | [Reasoning controller](../reports/2026-09-20-reasoning-controller/README.md): 4 worlds × 4 modes | Granite; step-guided 0/4 completed frames; 5 backtracks across all modes | Exact-token recovery verified; useful live step-guided recovery not established by this check. Frame completion is not correctness. |
| R03 · completed development and interrupted/completed evaluation | [Proposal generation](../reports/2026-09-20-proposal-generation/README.md): 32 development batches; 6 separate worlds × 2 seeds × 4 modes = 48 evaluation attempts | Granite; step Jev, greedy, likelihood each 6/12 verdict matches; final-only filter 5/12 | Worked examples raised Jev-eligible development batches from 0/8 to 6/8; all UNKNOWN worlds remained unsolved. One ambiguous timeout retained; 13 never-started jobs completed under a disclosed extension. |
| R04 · completed final-classifier check | [Fixed verdict](../reports/2026-09-20-fixed-verdict/README.md): 6 fresh worlds × 3 modes = 18 runs | Existing Granite step mode 2/6; Jev fixed final Choice 6/6; direct Jev 6/6 | Both UNKNOWN cases classified; paired Granite paths unchanged. This improved the sampled pipeline's final classification, not Granite reasoning. |
| R05 · completed integration pilot | [ProofWriter MPS pilot](../reports/2026-09-20-proofwriter-pilot/README.md): 3 dev theories × 3 arms = 9 runs | Jev final Choice; all arms 2/3 | Integration only, no quality advantage; abstention is different from semantic UNKNOWN. |
| R06 · completed CUDA pilot | [L40S pilot](../reports/2026-09-20-cuda-pilot/README.md): same 3 dev theories × 4 arms = 12 runs | Jev final Choice; all arms 2/3 | Hardware integration; reused cases and different sampling paths preclude a controlled hardware speedup claim. |
| R07 · completed, objective mismatch documented | [Controlled study](../reports/2026-09-20-controlled-study/README.md): 200 test theories × 3 seeds × 4 arms = 2,400; separate 24-world × 4-arm stress = 96 | Jev final Choice; guided 507/600 (84.50%), direct 508/600 (84.67%); all adjusted intervals included zero | 542/600 guided paths had no retained step. The owner correctly rejected using these scores as Granite-generated answer improvement. Conflicting final-format instructions also compromise the derived Granite-only comparison. |
| R08 · failed admission gate | [Generated-answer pilot v1](../reports/2026-09-20-generated-answer-pilot-v1/README.md): 8 math train + 8 logic dev × 3 arms = 48 | Granite in every arm; valid-format totals 14/16 single, 14/16 likelihood, 15/16 Jev | Failed the 90% format gate. Preserved before a shared EOS/label/prompt correction on development data. |
| R09 · passed admission gate | [Generated-answer pilot v2](../reports/2026-09-20-generated-answer-pilot-v2/README.md): same 16 dev cases × 3 = 48 | Granite; format 15/16, 15/16, 16/16; correct math 4/8, 5/8, 5/8 and logic 3/8, 5/8, 4/8 | Provenance and format gate passed; nine Jev selections differed from local likelihood. Admission did not require reliable critic discrimination or accuracy gain. |
| R10 · completed negative evaluation | [Generated-answer study](../reports/2026-09-20-generated-answer-study/README.md): 200 math + 200 fresh logic test cases × 3 seeds × 3 arms = 3,600 | Granite; math 61.5% single / 67.8% likelihood / 56.5% Jev; logic 52.7% / 52.8% / 52.5% | No demonstrated Jev gain. Math Jev-minus-likelihood −11.33 pp, adjusted interval [−18.17, −4.50]. All finals independently token-audited. |
| R11 · completed offline analysis | [Architecture reassessment diagnostics](../reports/2026-09-21-architecture-reassessment/README.md): all 3,600 R10 traces + all 48 R09 traces; checkpoint/source inspection | No new generated output or Jev call | First-step failure separates 307 scored all-rejections and 265 no-valid-step events among 600 guided logic runs; candidate gates and exact source recorded. Post-hoc, not a new accuracy experiment. |
| R12 · development completed/interrupted; gate unexecuted | [Full report and raw attempts](../reports/2026-09-21-logit-guidance/README.md), [Gate A protocol](local-claim-gate-protocol.md), [V2 revision](claim-forks-protocol.md) | V1: 60/60 worlds, only two mixed scored sets. V2: six complete, seventh returned HTTP 400 without usage receipt | All attempts retained; one maximum reservation remains charged. No further paid call or Gate C is admitted. The held-out gate has no generated outcomes. |
| R12-D · completed local follow-up | [Completion/mechanism plan](local-followup-protocol.md), [results](../reports/2026-09-21-logit-guidance/README.md) | Finished 53/53 never-attempted proposals without Jev; total V2 grader coverage 150/224 (67%). Four-prefix × five-mode replay verifies bounded probabilities, exact no-op identity, unchanged weights and Granite final-token ownership | No fresh hosted checkpoint or quality gain established. All 20 finals omitted their closing frame; all five modes had identical sampled paths per world. No cloud launch or gate-set generation. |

## Corrections that the paper must retain

**Who answered:** R04–R07's fixed-choice results end in Jev. The number 84.5%
must never appear as “Granite + Jev generated-answer accuracy” beside a Granite
generation score. The original traces are intact; R08–R10 changed the experiment
to match the intended question.

**What zero steps means:** R10 reported 572/600 guided logic runs with no step.
R11 decomposes that count into 307 runs rejected at their scored first batch and
265 with no valid first proposal. The latter had no Jev decision at that point.
Neither count independently says whether a candidate was semantically correct.

**What the model is:** the checkpoint uses the `GraniteMoeHybridForCausalLM`
implementation, but its configuration instantiates 40 attention layers and zero
experts. It is the dense attention variant, not a Mamba hybrid. Hooks must target
the actual implementation class; the family name is insufficient.

**What the result proves:** R10 is a staged-prompt, selection-and-stopping-policy
comparison. It does not isolate rejection, ranking, prompt effects, or a hidden
layer. R11 changes none of its scores. Previously inspected data is permanently
marked exposed for future experimental design.

**Costs and runtime:** R10 and both replacement pilots cost an estimated $3.29
for compute/disk/Jev before tax and separate network charges, within the later
$50 authorization. This is not the total cost of every historical study or an
invoice. Their temporary resources were deleted after hash-verified retrieval.
R11 used local offline analysis and public document retrieval, with no paid model
calls or GPU server. Hosted timing does not measure a colocated Jev deployment.

## Traceability

The [historical report manifest](../reports/2026-09-21-architecture-reassessment/historical-reports.json)
records SHA-256 hashes of the eleven pre-existing report Markdown files at this
reassessment. Each original report links its own source/data/summary artifacts.
The new analyzer records its own source hash, parser hash and exact private input
file hash. Earlier reports saying “pending” describe their creation time; later
rows supply the completion record without rewriting those historical files.
