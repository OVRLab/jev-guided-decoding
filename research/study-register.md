# Study register

**Direction update, 2026-09-23 (no experiment):** the owner set broad ten-benchmark
improvement and named larger-model outperformance as the [north star](north-star.md).
The strategy records a candidate suite and comparator ladder. No R23 result,
new inference, training, cloud allocation or additional spend is implied.

Registered retrospectively on 2026-09-21 from the existing reports and artifacts.
This register does not turn historical development work into preregistration.
Frozen source revisions, dates, raw availability, device, exact prompts and budgets
are retained in each linked report. Study IDs are notebook identifiers, not issues.
All live rows below used original Granite where generation was involved and the
hosted Jev service. R22 trains new adapter weights while preserving the original
backbone; no generally improved checkpoint is established.

| ID / status | Evidence and scale | Output owner / observed result | Interpretation |
| --- | --- | --- | --- |
| R22 · completed, no observed Jev contribution | [Report](../reports/2026-09-23-learned-feedback/README.md): four matched adapters, two seeds, 384 fresh worlds, 3,456 final answers | Granite owns every final token; native 90.89%, constant/live/shuffled/oracle 92.19% mean; live-native +1.30 pp [−1.30,4.04], live-constant 0 | Exact live/shuffled/oracle tokens agree everywhere. Original weights frozen; 12 checkpoints and all artifacts audited/replayable. GPU resources deleted; +$1.18, cumulative $33.76/$50. |
| R21 · completed, feedback admitted by replication | [Report](../reports/2026-09-23-semantic-feedback/README.md): 192-world admission then a fixed 384-world replication | Correct support decisions on 192/192 and 383/383 assessed Granite drafts, including 12 and 36 natural errors; one unassessed fragment | R21A failed error exposure; R21B passes. No final-answer intervention. API cost $0.03193, cumulative $32.58346 before R22; all original weights unchanged. |
| R20 · completed, evaluator transfer limited | [Completed report](../reports/2026-09-23-semantic-evaluation/README.md): 96/96 judge validation, 528 fresh inputs × three arms, all 1,584 generations | Granite final tokens; blind Qwen native/dual scores 30.21%/42.71% authored, 74.17%/73.33% Hotpot, 61.67%/67.50% SQuAD | Primary authored +12.50 pp [4.17,21.18]; no static superiority. Blind review 21/24 exposes completeness errors; frozen scores remain provisional. All artifacts audited/replayed, resources deleted; +$2.32, cumulative $32.55/$50. |
| R19 offline audit · completed correction | [Portability amendment](benefit-sufficiency-audit-portability.md): one adjacent float allowed only in two logarithm features | Every other original integrity check remains; no new inference/API calls | All 6,096 main decisions reconstruct identically; main/control audits and public replay pass without editing raw records. |
| R19 supplement v2 · completed | [Serialization amendment](sufficiency-controls-canonicalization.md): unchanged 608 inputs × two arms, order and judgments | Granite owns final tokens; no new API calls; 1,216 successful outcomes | Static instruction scores 46.53%/32.90%/34.49%; dual superiority is unestablished. Authored dual-minus-shuffle parser effect +10.07 pp [4.51,15.97], exploratory 95%. |
| R19 supplement v1 · stopped before generation | [Static/shuffled controls](benefit-sufficiency-controls.md), registered during fitting | First disk-join check rejected equivalent tuple/list representations | One failed start, zero generated answers/API calls; original source and artifacts retained. |
| R19 main · completed, semantic validity limited | [Completed report](../reports/2026-09-22-benefit-sufficiency/README.md): 260 fit, 200 calibration, 608 test inputs; seven test arms; all 6,096 outcomes | Granite; native/dual scores 26.74%/43.06% authored, 27.68%/32.95% Hotpot, 25.44%/33.10% SQuAD | Primary authored dual-minus-relevance +15.28 pp [9.38,21.88], 99.1667%; material parser/F1 artifacts preclude a semantic improvement claim. Gate saves 54.44% of requests without reliable matched routing. |
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
| R13 · completed planned comparison; one failure retained | [Full report](../reports/2026-09-21-structured-study/README.md), [V1 protocol](structured-study-protocol.md), [V2 correction](structured-study-v2-protocol.md) | 300 worlds × three seeds × seven arms; 6,300 attempted, 6,299 completed, one failed soft-step request | Direct 42.67%, staged 37.00%, likelihood 35.44%, Jev 36.00%; all adjusted primary intervals include zero. All completed token paths independently audited; both deployments deleted; cumulative estimate $8.49/$50. V1 failed format and original V2 interruption remain preserved. |
| R13-C · completed operational continuation | [Registered recovery](structured-study-continuation.md), [frozen remaining schedule](protocols/structured-v2-completion/manifest.json), [new-segment records](../reports/2026-09-21-structured-study/continuation/runs.jsonl.gz) | Only 3,284 never-started jobs after the original 3,016 attempts; unchanged successful inference policy | All 3,284 completed, zero further recovery incidents. No started job or failed request replayed; original failure stays incorrect. Combined raw bytes exactly equal the two segments concatenated. |

## R14: completed internal evidence-attention comparison

The owner authorized full implementation/testing and a small cloud GPU after the
[proposal](evidence-attention-proposal.md). The [prospective protocol](evidence-attention-protocol.md)
was frozen before inference. All 640 heads were individually profiled on 24 worlds;
oracle calibration on 72 other worlds selected eight heads at ln(8), improving
46.53% native to 67.36%. A 12-context authenticated pilot passed operational gates.

All 360 held-out worlds × two contexts × eight arms = **5,760 outputs** completed,
with zero failures and Granite choosing every final token. Native scored 42.22%,
Jev attention 51.25%, shuffled 43.75%, lexical 48.89%, prompt 46.81%, random heads
41.39%, and oracle 56.67%. The adjusted native contrast is +9.03 pp [5.83,12.50];
lexical/prompt intervals cross zero, leaving the strict all-controls criterion unmet.
The descriptive constant-UNKNOWN reference is 50%. These are constrained authored
containment answers, not general reasoning or directly comparable R10/R13 scores.

[The final report](../reports/2026-09-21-evidence-attention/README.md) includes every
development/test trace, 23,136 independently audited model decisions, 732 Jev
receipts, initial test failures, unchanged weight hashes and reproducible figures.
Inference commit 9484509 and source/data/protocol hashes remained frozen. All task
VM/disk/network resources were deleted after retrieval; new cost about $0.78,
cumulative estimate $9.27/$50. No inference retry or protocol amendment was needed.

## R17: completed selective-attention study (registered prospectively)

Registered 2026-09-22 before live inference: [selective-attention plan](selective-attention-plan.md).
Test conditional Jev dispatch, prefill/fading interventions and evidence-mass
conservation on fresh unrestricted-answer tasks. Planned 2,028 development and
6,336 test outcomes, plus mechanical admission. Granite owns final tokens; a
development-fitted threshold controller may change but model weights do not.
All **2,028 development and 6,336 test outcomes completed**, with nine GPU admission
fixtures passing. Development selected additive/all-token strength 5, identical to
the fixed R16 control. All three gates called on every test input and exactly
matched always guidance; they are neither selective successes nor independent
replications. The benefit gate discarded 5,340 pilot tokens and added a prefill per
input, with no saved request.

[Final report](../reports/2026-09-22-selective-attention/README.md): authored accuracy
is 28.77% native / 33.13% selected Jev / 34.72% mass-conserving control; Hotpot F1
is 25.23% / 28.76% / 28.63%. Primary guided-minus-native intervals are +4.37 pp
[0.00,8.93] and +3.53 pp [−1.47,8.58], individually 98.75%. The exploratory
mass-versus-R16 contrasts are inconclusive. Answerable accuracy improves 50.40% to
61.11%, but missing-evidence accuracy declines 7.14% to 5.16%. All recognized
abstentions use natural wording, with zero bare UNKNOWN outputs. Overall authored
accuracy remains below constant abstention (50%).

Audits reconcile 8,364 outcomes, 860 exact inputs, 169,773 final tokens, 185,793
forwards, 704 native/fallback pairs, 2,112 pilot pairs and unchanged weights/source.
All 860 paid attempts succeeded (1,944,119 known input tokens; zero unknown calls).
Public lossless archives reproduce every main audit field except timestamp.
The initial bootstrap CPU timeout and its thread-setting repair are retained.
Local checks pass 415 tests; six scientific figures were visually inspected.
Estimated new cost is $3.77, cumulative $23.46/$50; all temporary resources were
deleted after 14 remote files were byte-verified against local backups.

The [offline routing supplement](selective-routing-supplement.md) was registered
after development began, before selection or held-out inference was inspected.
It compares routing to expected random assignment at the same observed call count;
it adds no live calls or generation and does not replace the original random arm.

The [budget frontier](selective-budget-frontier.md) was registered after development
selected always-calling guidance, while held-out inference was in progress and
before held-out aggregate inspection. Rules for 25/50/75% development request
ceilings were frozen at 12:22 UTC. It reconstructs quality and work from recorded
branches; it does not measure actual API savings or new live gated latency.
The [completed frontier](../reports/2026-09-22-selective-attention/budget-frontier.md)
reports all three frozen budgets. At the 25% development ceiling, authored replay
uses 21.43% of requests for 31.55% accuracy, +2.78 pp [1.19,4.56] versus native
and +1.84 pp [0.41,3.39] above same-count random routing (exploratory 95% intervals).
Hotpot replay instead scores 25.00% F1 at 18.50% calls, with no positive routing
value. The 50/75% ceilings yield authored 31.55/32.54% and Hotpot 25.69/27.09%.
This limited authored-task signal does not establish external transfer or a
confirmed low-cost deployment. No test-selected winning budget is promoted.

The [budget accounting amendment](selective-budget-accounting-amendment.md) repairs
reconstructed work after a failed request before supplementary analysis. It retains
the first freeze and binds a second to identical development rules; no main study
source, output, grade or call is changed or replayed.

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

## R15: completed refinement and fresh evaluation

The owner authorized iterating the positive R14 native-baseline result, then
explicitly requested a full plan, implementation, cloud test and documentation.
The [prospective R15 protocol](evidence-attention-v2-protocol.md) compares 90
bounded policies on 96 development worlds and freezes one before 600 primary-test
and 120 longer-chain challenge worlds. Twelve arms separate the previous R14
version, native Granite, simpler controls and one-factor ablations. The new primary
question is improvement over native and R14, with simpler controls secondary;
R14's historical criterion/results are unchanged. The initial checkpoint had 343
local passing tests and inference pending; its [pre-execution record](../reports/2026-09-22-evidence-attention-refinement/pre-execution.md)
is preserved. Final results follow the interruption history below.

R15 execution interruption: the 103rd development Jev request timed out after 102
complete contexts; original weights stayed unchanged and no held-out operation
started. The [prospective recovery amendment](evidence-attention-v2-recovery.md)
retains that common failed block, maximum unknown charge and all raw prefixes;
continues only never-started jobs with a 90-second transport limit; adds twelve
fresh full-vocabulary zero checks. Four recovery tests pass; all 349 local tests
pass before resumed inference. Selection and held-out results remain pending.

The first R15 recovery then stopped on a zero-check snapshot FileExistsError,
after two new successful provider requests, before selection/test. The
[checkpoint repair amendment](evidence-attention-v2-checkpoint-repair.md) preserves
that segment too and resumes individual never-started jobs. Two new full-development
mock tests reproduce the old checkpoint/partial-block failures and pass with the
separate repaired helper. Paid attempts and original scientific comparisons remain
unchanged; one additional fresh zero forward replaces missing persisted evidence.

The repaired R15 run finished development and 47 test contexts, then stopped on
HTTP 503 at the 48th test request. Its selected policy and original test freeze
remain unchanged. The [service continuation](evidence-attention-v2-service-continuation.md)
was registered after testing began, explicitly expands transient admission to
503 and related gateway errors, raises the incident bound to thirty within the
same budget/deadline, retains every failed dependent output and replays no paid
request. All original scientific comparisons are preserved; final interpretation
must identify the operational amendments. Two new offline continuation tests pass.

The service-continuation prelaunch rejected a list/tuple serialization mismatch in
its freeze check before any new model/scorer operations. Identical raw JSONL
prefixes verify zero new jobs. The [serialized-freeze repair](evidence-attention-v2-freeze-repair.md)
adds a regression that reproduces the false rejection, then confirms semantic
JSON comparison while preserving the original freeze bytes and rejecting actual
policy changes. Service admission and all scientific settings remain unchanged.

### Final R15 result

R15's fresh 600-world comparison scores **38.08% native Granite**, **47.33%
previous Jev attention**, and **68.42% refined Jev attention**. The paired primary
gains are +30.33 pp [26.67,34.00] versus native and +21.08 pp [17.92,24.25] versus
R14, using individual 97.5% intervals. The prespecified advancement criterion is
met. Lexical/prompt/shuffled comparisons are exploratory and favorable on this
primary cohort. Longer-chain challenge accuracy is only **41.67%**, below the
50% constant-UNKNOWN reference, so broad reasoning utility remains unestablished.

The complete schedule contains 34,777 records and 34,679 actual model forwards,
with two provider failures retained and no paid/model replay. Operational amendments,
including one after test start, are disclosed; the selected policy/test freeze and
weights stayed unchanged. All task cloud resources are deleted. New cost is about
**$1.90**, cumulative **$11.17/$50**. This is research
branch evidence, not a published trained checkpoint or unrestricted chat result.

The [full report](../reports/2026-09-22-evidence-attention-refinement/README.md)
contains five loaded segments, all four operational amendments, full exact public
traces, independent reconstruction, 15 scientific figure exports and cost/cleanup
records. The primary test has 14,392 complete outputs and eight failed dependent
outputs; challenge has 2,880 complete outputs. Development retains ninety failed
policy outputs for its single failed scorer context. All 1,465 saved zero/native
label-token pairs match and twelve persisted full-vocabulary comparisons pass.


## R16 — adaptive attention and relaxed answer contracts (registered 2026-09-22)

Prospective [full protocol](adaptive-attention-protocol.md). The owner authorized
head-specific tuning, dynamic relevance refresh, external transfer and removal of
fixed answer choices. Implementation lives in
`research/iterations/adaptive_attention/`; prior source/data/results are unchanged.
Status: **completed**, including the full main schedule, registered factorial
supplement and three artifact audits. [Complete report](../reports/2026-09-22-adaptive-attention/README.md).

All **16,120 main test outcomes** and **3,600 exploratory factorial outcomes**
are retained. On the new depth 1–6 constrained task, native Granite scores
**30.83%**, matched R15 **59.00%**,
and tuned Jev attention **72.00%**. The primary
tuned-minus-R15 contrast is **+13.00 pp [+8.67, +17.61]**.

Without an answer menu or required UNKNOWN token, open-explicit accuracy is
**27.33% native / 27.17% tuned**;
open-neutral accuracy is **26.17% / 21.50%**.
Refreshed versus static staged guidance changes accuracy by
**+0.42 pp [-3.33, +4.17]**. On 200 length-filtered HotpotQA questions,
direct answer F1 is **26.85% native /
29.67% tuned**, with primary contrast
**+2.82 pp [-1.35, +6.91]**. Primary intervals are 98.333%;
other comparisons are exploratory. These tasks and output contracts have separate
interpretations; historical R15 scores are from a different cohort and precision.

Granite generates every semantic token with unchanged weights; all arms use FP32.
The full report includes natural abstentions, answerable/missing breakdowns,
regressions, factor interactions, API failures, exact traces and three independent
audits. All temporary resources are deleted. New estimated cost is
**$8.52**, cumulative **$19.69/$50**
before tax/separate network charges. This is research-branch evidence, not a trained
checkpoint release or a general reasoning guarantee.

Development evaluated 70 policies on 96 new worlds before
freezing the selected policy. Initial capability tests first failed on missing
modules and then exposed the empty-cache representation; fixes preceded evaluation.
The final local inference suite passes 385 tests. Full model weights, inputs,
selection timing, generated tokens and attention maps pass independent audit.
The operational interruptions and supplementary registrations below remain part
of the record.

### R16 admission interruption: cache numerical discrepancy

The initial GPU admission at source `9c150df` stopped with cached/full-prefix
maximum vocabulary-logit difference 0.5 (allowed 0.125). No benchmark/model study
jobs or Jev requests started. The [registered diagnostic](adaptive-attention-cache-diagnostic.md)
compares BF16/FP32 on reserved mechanics/development inputs before deciding repair.


### R16 precision amendment, before selection or testing

The 24-comparison [cache diagnostic](adaptive-attention-cache-diagnostic.md) found
BF16 discrepancies up to 0.5458984 versus FP32 0.00005913, with identical argmax
in every comparison. The [prospective FP32 amendment](adaptive-attention-fp32-amendment.md)
uses FP32 for every arm and a stricter 0.0001 cache tolerance. Original R16 source,
protocol and stopped admission stay frozen. No Jev or benchmark job is replayed.

### R16 supplementary factorial controls (registered during main evaluation)

Development changed strength, one selected head and threshold together. Before
consulting held-out aggregate quality, the [exploratory supplement](adaptive-attention-factorial.md)
registers six missing corners of that 2×2×2 combination, 3,600 constrained forwards
using saved Jev receipts and no new API calls. It leaves the main 16,120-job study
and primary contrasts unchanged. It diagnoses factor effects on reused contexts;
it is not a fresh replication or permission to retune on test.

### R16 targeted related-method review (no inference)

On 2026-09-22, the [attention-method comparison](adaptive-attention-related-work.md)
reads AutoPASTA, Spotlight and CAFE against the frozen R16 implementation, retaining
primary-source retrieval hashes. It documents existing automatic/dynamic steering
and untested comparators. It does not modify the live schedule or claim reproduced
results or methodological novelty.

### R16 additional artifact audit (no inference)

During main evaluation, an independent supplementary audit was specified to bind
every test arm to the frozen selected policy, verify that selection preceded test
starts, reconcile actual attention-hook calls with generated phases, reject any
answer menu in unrestricted phases, and decode framing against fixed controller
text. Three tests first failed with missing scaffolding. This strengthens artifact
verification without changing the frozen main auditor, scientific metrics or run.

### R16 output-form diagnostics (no inference)

Before consulting aggregate test quality, the [descriptive output protocol](adaptive-attention-output-diagnostics.md)
records bare UNKNOWN versus other recognized abstentions, mistaken abstentions on
answerable cases and final/reasoning token-limit endings. Counts bind to the audited
output bytes and use the original parser; they neither repair grading nor exclude
bounded/failed outcomes. Three tests first failed on missing scaffolding before
the diagnostic implementation. This adds transparency about relaxed contracts,
not another primary comparison or fresh replication.

### R16 post-completion records and descriptive failure reading

Both inference schedules completed. A local supervisor then rejected the service
manager's return code 4 after the completed transient factorial service had been
removed. Exit code 0 and the full completion record were verified; original bytes
were retrieved and offline auditing/cleanup continued without inference replay.
The [recovery record](../reports/2026-09-22-adaptive-attention/supervisor-recovery.json)
preserves this operational interruption.

After the main quality audit, a [post-hoc reading](../reports/2026-09-22-adaptive-attention/free-text-failures.md)
examines the first four lexicographic unparsed tuned direct-answer cases. It
documents citations and partial source restatements with natural EOS endings.
The examples and deterministic selection are retained without regrading; they
motivate an untested phase-specific guidance hypothesis, not a new causal finding.

## R18: registered single-prefill boundary experiment

The owner authorized implementation and testing of the pre-layer-19 boundary after
R17 completion. The [prospective plan](boundary-attention-plan.md) registers one
internal decision, new native attention features, 520 development and 8,856 held-out
outcomes across fresh authored, Hotpot and SQuAD2.0 subsets. At registration, no
R18 live result existed.
Prior cumulative spend is $23.46/$50; up to $15 is reserved for this iteration.

### R18 completion and operational record

**R18 completed:** the single-prefill gate raises authored accuracy from
**26.98% to 31.75%**, close to always Jev's **31.94%**, while saving **27.58%**
of requests. The exploratory selective-minus-native interval is **+4.76 pp
[1.79, 7.94]**. Hotpot native/always/selective F1 is **27.96% / 29.40% / 27.08%**;
SQuAD adapted F1 is **26.49% / 26.72% / 26.55%**. Primary routing intervals
include zero in all three domains, so reliable call selection is unestablished.

The gate uses **425/984 test requests**, saving **56.81% overall**, with one
prefill and zero discarded pilot tokens. Its domain call fractions are
72.42% / 18.33% / 6.67%; missing-evidence handling remains weak. Granite generates
every final token with unchanged weights and no required UNKNOWN spelling.
All **9,376 outcomes**, **184,889 final tokens** and **1,244 successful Jev
receipts** pass reconstruction; public archive replay reproduces the analysis.
There are zero provider failures. All temporary resources are deleted after
verified retrieval. New estimated cost is **$3.77**, cumulative **$27.23/$50**
before tax/separate network. This is research-branch evidence, with mixed external
quality, not a generally improved checkpoint or a serving-throughput benchmark.

The [full report](../reports/2026-09-22-boundary-attention/README.md) records the
three primary routing contrasts: +1.17 pp [−0.70,3.03] authored, −1.14
[−2.98,0.61] Hotpot and +0.04 [−0.47,0.43] SQuAD, with individual 98.333%
intervals. All include zero. The source/data/selection freeze remained intact.
The [descriptive supplement](boundary-output-diagnostics.md) was registered during
execution before held-out aggregate inspection; no post-test policy change or
regrading occurred. Source freeze is `7e570c0` and real admission passes 27/27
full-logit/all-layer-cache comparisons with zero maximum differences.

The run has no inference interruption or provider failure. After byte-verifying all
15 remote result files, cleanup initially failed because CLI authentication expired;
refreshing the existing sign-in allowed complete resource deletion. A later
reporting metadata import used system Python without NumPy and was resumed in the
project environment after public reanalysis had already passed. Both interruptions
are retained in the validation record; neither caused a paid/model replay or a
change to the frozen scientific source. Authentication delay is included in cost.

## R23 — public cross-domain baseline diagnostic (registered 2026-09-23)

- [Plan](benchmark-baseline-plan.md), [frozen inputs](protocols/public-baseline-v1/manifest.json).
- 76 development cases: MMLU-Pro validation 28, GSM8K training 24, MuSR 12,
  IFBench 12; original Granite 4.0-1B and native-thinking Granite 4.2-3B.
- Native generation and independent grading only; no Jev intervention, training
  or final ten-benchmark superiority claim. Selected source-test cases are now
  project development, with exclusions recorded for future untouched holdouts.
- Registered before cloud creation/inference. Initial capability tests failed on
  missing module; subsequent readout-binding test failed on missing capability.
  Both failures are preserved in the dated report's validation archive.
