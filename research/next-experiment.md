# Next experiment: earn the right to intervene

Date: 2026-09-21. Status: **design, not a frozen runnable protocol**. No live work
under this document has run. It defines the staged decision and controls; exact
fixtures, scoring code, thresholds, source hashes and runtime settings must be
committed in an execution manifest before each stage. R10 test results cannot
serve as the held-out evaluation of this redesign.

Execution update: [R12 development and mechanism report](../reports/2026-09-21-logit-guidance/README.md).
Versioned development protocols ran; a provider error interrupted scoring, local
proposal completion and replayed-score mechanism checks followed. The held-out
critic gate and Gate C did not run. This umbrella design remains the original
decision plan; frozen subprotocols and reports specify actual executed scope.

## Question and hypothesis

Can a hosted, non-generative semantic critic improve the final answers of a
frozen small language model by influencing intermediate token probabilities?
The proposed mechanism is in the [architecture review](architecture-reassessment.md).
The first hypothesis is narrow: local source-to-claim judgments contain useful
information beyond Granite likelihood on *Granite's own* continuations. If that
fails, a stronger insertion point is not justified for that domain.

Success means independent answer quality at a disclosed cost, not a higher Jev
score, fewer accepted claims, easier tasks, more refusals, or a prettier diagram.
The prior negative math and logic findings remain part of the paper if a new
semantic-grounding task succeeds. A domain change must be explicit.

## Gate A: critic reliability and candidate opportunity

Begin with short, authored, redistributable evidence-based problems. Separate
documents/worlds and generation templates across development and evaluation.
Include supported deductions, missing conditions, incorrect relation direction,
wrong entity attribution, correct setup/restatement, harmless paraphrases,
unsupported causal links, irrelevant truths and “not yet an assertion.” Include
arithmetic and multi-hop cases as declared diagnostic strata, not an assumed
primary Jev strength. Do not alter a domain's membership after seeing scores.

Collect candidates from the frozen Granite checkpoint, retaining duplicates and
failed boundaries in the opportunity denominator. Also use minimal, authored
positive/negative pairs to debug the rubric, but report their results separately
from generated candidates. The old fixed-candidate success did not transfer.
References and independent labels remain exclusively in the grader.

Have candidates graded without Jev scores, mode identities or answer outcomes
visible. Use an exact local oracle only where it validates the actual claim and
its justification; do not treat a parser's failure as semantic falsehood. For
unrestricted text, use a frozen human rubric with double labeling and adjudication,
or report that independent labeling is unavailable and keep this gate unpassed.
Jev cannot be its own independent grader. Another LLM alone is not a ground-truth
replacement without validation.

Predefine separate labels for correctness, relevance, novelty, and assessability.
Record discrimination on mixed-quality candidate pairs, false acceptance and
false rejection, calibration/Brier score for the precisely defined event, and
the rate of batches containing a correct usable alternative. Cluster uncertainty
by source problem, not by candidate or seed. Look for reliable ranking gain over
likelihood among mixed-quality sets; separately measure all-good/all-bad sets.
Assessability must not excuse excluding inconvenient outputs from answer scoring.

Practical initial development allocation: 60 fresh problems across at least six
declared motifs, three continuations per problem, with at most two rubric versions
considered on development data. A separate 100-problem gate set then checks the
frozen choice. This is a pilot, not a guaranteed well-powered estimate. The gate
requires a positive lower bound for the paired ranking advantage over likelihood
and a predeclared false-acceptance tolerance; choose that tolerance from the task's
utility before collecting gate results. Otherwise record a failed/inconclusive
gate and do not open the full model-quality study.

## Gate B: separate control policy from insertion location

First implement a single-step token-selector interface without live calls. Verify:

1. Zero bias leaves the committed-token sequence identical under isolated RNG
   streams, even when shadow lookaheads are computed and discarded.
2. A known synthetic bias changes the expected probability/selection and nothing
   else; probabilities normalize and the stated KL bound holds.
3. No-op, masks, EOS, temperature, equal scores and unsupported score types behave
   as declared. Partial/empty lookaheads do not become negative semantic labels.
4. Branch state cannot contaminate another branch; cancel/error/stale response
   handling is explicit; each consumed token/call remains charged.
5. Exact original weights and every final token's provenance are verified.

Then run a bounded real-checkpoint mechanical check on local or one small GPU.
It must establish the insertion point and probability effect, not answer-quality
improvement. Test a text-step *soft* control with the same rubric on development
data as an ablation: otherwise changing rubric, removing early stopping and moving
the hook simultaneously would obscure the reason for any gain.

Use intermediate-only intervention and the same final-generation rule initially.
Lookahead proposals are generated by Granite; there is no external final Choice.
Independent final grading is performed after generation. Retain native rollout
paths and all lookahead cost, including work from unselected actions.

## Gate C: frozen independent answer-quality study

Only after A and B pass, freeze a new manifest and unseen evaluation. Reconcile
the final prompt/grading contract on development first. Use fresh problem-level
splits and three recorded seeds; avoid duplicate documents/templates/theories
across splits. Publish rights-cleared cases where possible. Report possible
pretraining exposure for public datasets, even when we have not used a case before.

The minimum primary comparison is:

| Arm | Purpose |
| --- | --- |
| Native Granite, ordinary prompt and declared sampling | Measures practical base performance; reveals costs of forced staging |
| Staged Granite with the same intermediate/final contract | Isolates staging from Jev intervention |
| Granite with the same lookahead/candidate budget, likelihood-based selection | Controls additional search; final tokens remain Granite's |
| Granite with Jev's bounded logit bias | Proposed treatment |
| Same pipeline and sampled score multiset, shuffled across candidates | Tests whether useful score-to-candidate correspondence matters |
| Same pipeline, zero bias with separately consumed shadow work | Checks no-op identity and accounts for added work |

Use the soft step-selection ablation from Gate B if the claim specifically concerns
*placement* rather than the full redesigned system. A hard-filter arm can identify
the cost of stopping, but must not be the sole weak baseline. An oracle selection
ceiling is a separately labeled diagnostic, never a deployment method or main arm;
it may use labels only after scored production paths are fixed.

Use two resource analyses. Under identical candidate sets on common prefixes,
compare local selection quality. Under per-problem matched generation budgets,
compare complete policies and record divergences. Also report native Granite given
similar total dollar/time budgets, for example extra samples plus a prespecified
non-Jev aggregation rule. Equal ceilings, equal candidate count or shadow work
alone do not establish fair actual compute. Publish accuracy-versus-cost/latency
curves and all actual prefill/decode/padded work, network waits and API use.

Primary metric: independently correct Granite final answer, including all missing,
invalid, unfinished and failed attempts as incorrect. Secondary measures: supported
claims, useful completion/coverage, refusal/UNKNOWN precision and recall, token
length, intervention count, rejected work and runtime. A generic UNKNOWN/refusal
policy must not win by avoiding answers. Have the final grader blind to the mode.

Before test inference, choose the smallest worthwhile effect, number of independent
problems, primary contrasts, multiplicity correction, bootstrap seed/draws or
another justified paired test, and success rule. Use development discordance to
estimate precision/power and cost. A tentative 200 problems is not automatically
enough. If the available budget cannot resolve the target effect, call it a pilot
and report uncertainty rather than declaring equivalence or proof of benefit.

For a superiority claim, the multiplicity-adjusted lower bound must exceed zero
against both the appropriate native/staged baseline and the search control, with
prespecified minimum effect and cost requirements. The shuffled/no-op comparisons
test mechanism, not broad superiority alone. No optional stopping after a favorable
accuracy check. Do not inspect test outcomes to tune lambda, checkpoint frequency,
layer, rubric, examples or candidate count. A failed experiment gets a new record,
not a modified test protocol or selected-case rerun.

## Budget and stop rules

The owner's existing ceiling is $50 for the restarted study. The corrected main
study plus pilots used an estimated $3.29; about $46.71 remains **by estimate**,
subject to invoices and separate charges. This is not a new spending authorization
or a reset of the ceiling. Current reassessment used no paid inference/cloud GPU.

Proposed planning caps inside the existing ceiling: $3 for critic development/gate,
$5 for mechanism and small ablations, up to $25 for an admitted evaluation, and
$10 reserved for retrieval/cleanup/estimate error. Their sum plus previous spend
is below $50. These are caps, not cost predictions or permission to spend them
before a stage has a frozen execution manifest. If actual remaining funds are
lower, reduce scope before launch; do not weaken evidentiary standards silently.

Recheck actual rates and quota before provisioning one suitable small GPU; never
an eight-H200 machine for this task. Include model loading, disk, idle/setup time,
network and cleanup reserve. A durable shared ledger must include all new Jev
requests and prior spend; no disconnected per-stage budgets. Cap HTTP attempts,
input tokens, generated/padded tokens, prefill, wall time and intervention count.
No automatic retry of ambiguous paid timeouts. Unknown usage stops paid execution.

Fail closed on wrong answer ownership, leaked reference answers, inconsistent
prefix/cache state, missing trials, provider version mismatch, or manifest/source
drift. Preserve logs and planned denominators. After any cloud run, retrieve and
hash-check artifacts, delete task-created compute/disk/network resources, and
verify deletion. Colocation and vLLM throughput are separate future studies.

## Literal hidden-layer branch

If the project chooses activation intervention, create a separate registered arm
with a defined representation mapping and labeled calibration data. Test sites
and strengths on development, including no-op/random/reversed/fixed-direction
controls, then freeze a fresh evaluation. Do not append an uncalibrated vector
experiment to the output-logit trial and call its layer optimal. Original pretraining
data is unnecessary for a small calibration study, but evidence is still required.
