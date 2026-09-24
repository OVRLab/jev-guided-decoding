# Granite–Jev north star

**R26-A completed and audited:** the [50-case exposed-data cost pilot](../reports/2026-09-24-selective-admission/README.md)
measured actual selective repair: 20 cases repaired and 30 retained per arm, with
50 successful Jev calls. All three native profiles finished, but output-format
admission failed; a separately versioned readout correction is prepared. No fresh
benchmark score or larger-model superiority is established. All owned resources
are deleted; estimated cumulative spend **$46.17/$110**, leaving
**$63.83** before tax/separate network. Local checks: **584 tests pass**.

**R25 completed and audited:** always repairing lowers the combined score from
59.38% to 44.79%. The predeclared selective-retention replay instead reaches
66.67%: science improves **71.88% → 86.46%**, while math stays **46.88%**.
Formatting failures limit interpretation, especially for math. All 3,072 outputs
and 12 adapter checkpoints are archived; public replay matches all four main
analyses. All cloud resources are deleted. Cumulative estimate **$42.63/$75**
before tax/separate network; **546 local tests pass**. The ten-benchmark and
larger-model objectives remain unmet. See the [completed report](../reports/2026-09-23-gated-repair/README.md).


Owner direction recorded 2026-09-23, after R22. This is a research objective and
evaluation strategy, not a claim of achieved performance or a frozen inference
protocol. It supersedes treating a particular insertion point or a small authored
task as the project's final objective. Historical protocols/results remain intact.

## Objective

Build a Granite–Jev inference architecture that substantially improves the
original Granite generator across ten leading, diverse LLM benchmarks and
outperforms explicitly named larger models, including newer larger Granite models
and models from another family. The architecture is a means to that outcome.
Generalization, reproducibility and demonstrated Jev contribution matter alongside
scores. Novelty requires a separate prior-art argument; a new diagram alone is not
the research contribution.

The initial target remains the existing dense Granite 4.0-1B checkpoint. Its
marketed name is 1B; R22 measured 1,631,750,144 original parameters. Preserve the
immutable original checkpoint as a control. New adapters and alternative internal
inference mechanisms are within the research direction. If a future study adapts
original weights or changes the backbone, save a new checkpoint and declare that
change prospectively; compare against its corresponding unmodified backbone too.
Changing to a larger generator cannot silently satisfy the small-generator goal.

Granite continues to generate the final answers, code and tool-call tokens. Jev
participates during inference; a final Jev classifier or routing the answer to a
larger generator cannot be credited as an improved Granite generator. A trained
internal repair module, sparse feedback routing and richer claim/evidence-linked
signals are hypotheses to compare, not an architecture already selected to win.

## What counts as progress and success

Publish a scorecard for every benchmark and every named comparator, including
losses and unresolved outcomes. Report individual effects with uncertainty and a
prospectively fixed suite summary. A win on one task is useful progress but does
not establish broad superiority. An all-benchmark dominance claim requires wins
on all benchmarks; an aggregate claim must be labeled as aggregate. No conjunction
of all ablations erases an otherwise supported positive individual result.

Working engineering targets, proposed here rather than attributed to the owner:

1. **Substantial native improvement:** at least +5 percentage points in the
   equal-benchmark mean of the ten 0–100 primary task scores, with an aggregate
   paired 95% interval above zero. Also show the ten effects individually, broad
   domain coverage, and all regressions; a concentrated gain is not broad transfer.
2. **Larger-model outperformance:** exceed a predeclared larger model on the same
   complete suite and frozen summary, with an aggregate paired interval above
   zero. Use the same larger model across the suite; do not assemble a weak
   comparator by choosing a different loser for each benchmark. Beating a 3B
   model is an early milestone; 8B and 27–30B systems remain stronger targets.
3. **Jev attribution:** compare with the same trained architecture without
   informative Jev feedback, and with a sensible Granite-only use of additional
   inference time. Demonstrate that relevant feedback improves actual task outcomes
   on unseen cases. Changed activations alone do not establish useful feedback.
4. **Independent replication:** reproduce the selected system on a locked suite
   and fresh task instances/time windows where available, retaining exact source,
   weight, input, evaluator and cost provenance before making a release claim.

These targets will be operationalized before live evaluation. The suite mean is
a project summary, not an official universal intelligence score. Pin one primary
metric per benchmark on a common 0–100 success scale; do not mix latency or
unbounded reward scores into that mean. Resample paired problems, repositories,
documents or sessions as appropriate within each fixed benchmark, then aggregate;
repeated samples and correlated problems are not independent benchmarks. Correct
the declared family of per-benchmark superiority tests for multiplicity. Keep the
effect sizes and intervals visible even when a decision threshold is not met.

## Candidate ten-benchmark suite

There is no source-independent definition of the ten most important benchmarks.
This candidate suite balances established comparisons with demanding reasoning,
coding, context, factuality and tool use. It must pass an access/licensing,
implementation and evaluator audit before its versions, splits and metrics are
frozen. No benchmark is dropped or substituted because of the architecture's score.

| Benchmark / primary source | Capability | Proposed primary measurement and main caveat |
| --- | --- | --- |
| [MMLU-Pro](https://github.com/TIGER-AI-Lab/MMLU-Pro) | Broad knowledge and reasoning | Generated-answer accuracy with pinned few-shot/prompt/extraction settings; report subject scores and option-order handling. |
| [GPQA Diamond](https://github.com/idavidrein/gpqa) | Difficult scientific reasoning | Generated-answer accuracy on the Diamond subset; small sample, chance performance and access conditions require explicit treatment. |
| [AIME 2026, Inspect evaluation](https://ukgovernmentbeis.github.io/inspect_evals/evals/aime2026/index.html) | Competition mathematics | Numeric correctness, pass@1 averaged over prespecified sampling seeds; cluster repeated outputs by problem and retain the small problem denominator. |
| [LiveCodeBench](https://github.com/LiveCodeBench/LiveCodeBench) | Executable programming | Pass@1 on a fixed release/time window, judged with the benchmark tests in isolation; hidden tests never become generation feedback. |
| [IFBench](https://github.com/allenai/IFBench) | Precise instruction following | Pinned official instruction/response success metric, with strict evaluation and semantic spot-checks; do not optimize formatting alone. |
| [MuSR](https://arxiv.org/abs/2310.16049) | Multi-step reasoning over narratives | Generated-answer accuracy with task-family breakdowns; avoids relying solely on our own courier templates. |
| [LongBench v2](https://longbench2.github.io/) | Long-context reasoning | Official answer accuracy plus context-length strata; disclose context limits and any truncation. A restricted context subset is not the full benchmark. |
| [SimpleQA Verified](https://huggingface.co/datasets/google/simpleqa-verified) | Factual knowledge and abstention | Correct-answer fraction plus wrong/abstained fractions and official metrics; validate a blind independent grader on actual response forms. No browsing in the closed-book track. |
| [BFCL v4](https://gorilla.cs.berkeley.edu/leaderboard.html) | Function calling and tool interaction | Official aggregate and category scores with identical schemas, allowed tools and environment; freeze evaluator version and tool-access rules. |
| [SWE-bench Verified](https://www.swebench.com/) | Repository-level software repair | Resolved-task percentage with the same agent scaffold, tools and execution budget for each generator; explicitly a system benchmark, not pure token prediction. |

The eight direct language/code tasks and two tool/agent tasks also get separate
summaries. The external scaffold for BFCL/SWE is held fixed; the intervention
under study remains in the Granite–Jev inference path. A different scaffold is a
different experiment. Inference-time checks may use only tests/evidence permitted
by the benchmark, never its held-out evaluation answers or hidden tests.

This is **not** Artificial Analysis's current index. On the source-check date,
[its methodology](https://artificialanalysis.ai/methodology/intelligence-benchmarking)
lists v4.3.2 and a different ten-task mix, with MMLU-Pro, AIME 2025 and LiveCodeBench
retired from its active reporting. We keep those distinctions explicit rather than
calling familiar older benchmarks the current frontier index. Independent
frontier evaluation, including harder suites such as that index, is a later
external-validity target; availability, modality and access must be established.
Saturating the candidate suite would trigger a new prospectively chosen harder
evaluation, not a claim to have beaten every frontier model.

## Comparator ladder

Use actual reruns under compatible evaluation contracts, not a subtraction from
unmatched numbers in model cards. Freeze exact revisions before inference.

- **Anchor:** [original Granite 4.0-1B](https://huggingface.co/ibm-granite/granite-4.0-1b),
  including a normal model-native baseline as well as any shared staged-prompt
  control needed to attribute the architecture. Do not weaken the baseline by
  imposing a prompt required only by our experimental controller.
- **Same-family ladder:** [Granite 4.2-3B](https://huggingface.co/ibm-granite/granite-4.2-3b),
  [4.2-8B](https://huggingface.co/ibm-granite/granite-4.2-8b) and
  [4.2-30B](https://huggingface.co/ibm-granite/granite-4.2-30b).
  [IBM's release](https://research.ibm.com/blog/introducing-granite-4-2) identifies
  these sizes and native reasoning. Preserve and report their supported reasoning
  modes; disabling thinking on competitors is not a fair best-quality comparison.
- **Other-family challenge:** [Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B),
  evaluated on the same text tasks. Its additional modalities do not become
  extra inputs denied to Granite. Check supported inference settings and runtime
  compatibility before budgeting or downloading weights.

The 8B Granite is the proposed first complete-suite larger-model comparator;
3B is a cheaper intermediate milestone, with 30B Granite and 27B Qwen the next
challenge tier. Pin this order before quality results, and retain any failures.
Their published model-card scores are context only, not project measurements.

## Fair quality and efficiency claims

Run two clearly labeled views: model-native best-quality evaluation under a common
benchmark contract, and quality at matched total monetary/latency budgets using
development-calibrated settings. Equal token caps do not imply equal compute across
models. Count discarded work, repeat prefills, repair passes, all Jev calls and
all permitted tools. Account for total inference cost, time to final answer,
throughput and memory separately; higher quality can be valuable even when slower.

Granite–Jev is a compound system. Jev's hosted compute, weight size and provider
internals are not measured by our Granite parameter count. Until total resources
are known, say “small Granite generator plus Jev,” not “a 1B model beats a 30B
model using fewer total parameters.” Report unknowns; use measured end-to-end
cost/latency where internal FLOPs are unavailable. Local memory excludes hosted
Jev memory, and colocated performance cannot be inferred from API timings.

[TypeSafe's current documentation](https://docs.typesafe.ai/models) exposes typed
text judgments through an API and no per-customer Jev weight adaptation. Our plan
must work with that actual interface; hidden-state exchange, joint Jev training
or a colocated weight deployment requires separately available capabilities.

## Research sequence

1. **Establish the scorecard:** audit the ten task/evaluator contracts, leakage
   controls, rights, context limits and larger-model runners; freeze the initial
   development/validation/final-test boundaries and produce a costed run manifest.
2. **Map failure modes:** on designated development data, separate knowledge gaps,
   reasoning mistakes, context failures, instruction violations and tool errors.
   Determine where Jev can supply a useful judgment without being shown the answer.
3. **Compare mechanisms:** test the simplest credible candidates, including a
   learned internal repair path, sparse conditional intervention and claim/evidence
   feedback richer than R22's two scalars. Select on downstream development
   correctness and measured cost; do not assume block 19 or any current design wins.
4. **Train for the missing behavior:** if repair is the chosen mechanism, use
   verified error-to-repair examples from separate public/synthetic training data.
   Compare matched training without Jev and feedback ablations. Original Granite
   pretraining data are not required for adaptation; a suitable new dataset is.
5. **Test transfer early:** require development evidence across unrelated domains,
   not just a better local verifier score or successful hook. Native fallback may
   be learned/validated where Jev is unhelpful, and its call rate remains measured.
6. **Lock, evaluate, replicate:** freeze one selected architecture and comparator
   configuration, run the ten-benchmark scorecard, publish all outcomes and
   uncertainty, and seek independent reproduction before a performance release.

Validation should identify a useful operating range; it need not reproduce
high-stakes final benchmarking on every experimental change. Use disjoint
development data and prospective held-out windows, record all searches, and never
train on benchmark solutions or use final-test outcomes for iterative selection.
Previously exposed examples in this repository are not fresh tests. Check possible
pretraining contamination where evidence exists; fresh names alone do not prove
novel skills. For learned judges, preserve anonymity, validate response completeness
and use independent human review for a defensible publication claim. Jev never
grades the success of its own intervention as the primary quality measure.

## Starting evidence, resource envelope and immediate work

R22 native/constant/live scores were 90.89%/92.19%/92.19% on one authored task;
real/shuffled/oracle feedback gave identical final tokens. R21/R22 establish useful
mechanical and local-verifier observations, not progress measured on this suite.
The [R22 report](../reports/2026-09-23-learned-feedback/README.md) and every preceding
negative/corrected result remain part of the paper record.

This direction does not increase the existing spending authorization. Recorded
cumulative estimated usage is $33.76146 of $50, leaving about $16.24 before
tax/separate network. That is remaining spending headroom, not a quote for the
complete program. No paid run or model download was started for this update.
Estimate each stage and reserve cleanup overhead before launch; do not commit to
the full larger-model suite under an unverified cost assumption. Work that fits
the existing authorization can proceed without a redundant approval; an actual
budget extension needs an explicit new limit.

Immediate deliverable: a versioned ten-task evaluation contract and runnable
baseline path, followed by a bounded cross-domain diagnostic before selecting
the next architecture. We have recorded candidate sources, not implemented or
run that new suite. New live studies receive their own registered protocol, model
and dataset hashes, cost ceiling, report and study-register entry.

Documentation validation for this objective update: review links and scope for
consistency, run the repository guidance checker and canonical checks, inspect
the PR's actual base/review context, and preserve all frozen scientific hashes.

Completed documentation checks on 2026-09-23: all ten changed/new Markdown files
have valid local links; 49 guidance files pass; Ruff lint/format and source/wheel
builds pass; the unchanged code suite passes 485 tests. All R20/R21/R22 scientific
source/data hashes remain intact. PR #2 has no submitted reviews or review threads;
the automated review bot remains unavailable because its quota is exhausted.
This update changes research direction and documentation only, with no new
quality measurement, resource allocation, model training or release.


## First stage completed: R23/R24, 2026-09-23

The [versioned ten-task contract](benchmark-suite-contract-v1.md) now records
source pins, evaluation/admission gaps and a composer that rejects partial or
development scorecards. It does not imply all ten evaluators are ready.
[R23](../reports/2026-09-23-public-baseline/README.md) completes 76 development
problems on each of original 1B and newer thinking 3B, with all 152 outputs,
cutoffs, primary/readout differences and public replay retained.

The [R24 critic diagnostic](../reports/2026-09-23-public-critic/README.md) identifies
21/23 wrong native answers with 3/37 false flags on reference-correct answers.
It changes no Granite output. This is evidence to test conditional error repair,
not a demonstrated architecture improvement. Correct final decisions with flawed
explanations and related narrative variants constrain both the repair objective
and future split construction. The next candidate should train on natural Granite
errors and verified repairs, measure correct-answer regressions, and demonstrate
feedback-dependent generation against matched training and additional reasoning.
Its layer placement, selective-call policy and broad transfer remain hypotheses.

All temporary resources are deleted. New R23/R24 estimated cost is $3.01208,
cumulative $36.77353/$50, leaving about $13.23 before tax/separate network.
This is not a quote for the unrun full suite or the complete architecture program.
All 507 local tests and documented archive audits pass. The earlier R22 negative
feedback-ablation result and every prior study remain preserved.

## Budget extension and R25, 2026-09-23

The owner explicitly increased the cumulative cap to **$75**. Starting estimate
is $36.773534922020566, leaving approximately $38.23 before tax/network. Reserve
$14.40 for the [registered internal repair experiment](gated-repair-plan.md),
including its hard cloud expiry and API cap. Older $50 entries are historical.
R25 tests a direct Jev gate on a newly trained residual branch using natural
Granite drafts from public math/science data, with matched training, blind repair,
text feedback and feedback ablations. The full ten-task comparison remains a
later evidence-gated stage; budget authorization is not evidence of success.


### Historical registration: R25 numerical restart and retention supplement

The BF16 pilot stopped at its numerical admission gate before any training drafts,
API calls or optimizer updates. Its $0.293387 cost and all five artifacts are
preserved; the first worker and owned resources are deleted. A diagnostic confirms
that the cached/full discrepancy also occurs in native Granite, while all six
float32 native/intervened checks pass within 1e-4. The separately frozen
[full-precision restart](gated-repair-fp32-amendment.md) now runs the same training
and evaluation design. The combined R25 reserve is **$20**, replacing $14.40,
within the owner-authorized cumulative **$75**. Prior estimated usage plus the
failed attempt is $37.066922 before tax/network; the active worker adds metered
use until verified deletion.

A [retention-policy replay](gated-repair-retention-supplement.md), frozen before
any test inference, separately checks preserving high-confidence native answers
and repairing only Jev-flagged cases. It retains every original primary comparison
and does not claim measured skipped execution or fewer Jev calls. Quality results
remain pending; source and data revisions are in the [R25 report](../reports/2026-09-23-gated-repair/README.md).

### Historical registration: R25 service continuation, 20:01 UTC

The full-precision worker passed admission but stopped after 113 training drafts,
112 valid Jev receipts and one unknown-usage failure, before any optimizer/test.
All owned resources were deleted. The [v3 continuation](gated-repair-continuation.md)
reuses exact drafts/receipts and retains maximum unknown charges without replay.
Missing scores stay null in evidence, with a neutral effective gate explicitly
labeled; all cases remain in primary grading. Training and held-out quality remain
unmeasured. Estimated cumulative use is $37.690485 before v3/tax/network; the $75
cap and combined $20 R25 reserve are unchanged. This is still a two-domain
mechanism pilot, not the ten-benchmark/larger-model north-star result.


## R25 completed: narrower positive signal, broad target still unproven

The [completed pilot](../reports/2026-09-23-gated-repair/README.md) trains an internal
feedback-dependent branch on natural math/science drafts. Always repairing reduces
combined accuracy from 59.38% to 44.79%. A retention policy registered before test
keeps answers Jev rates at least 0.5 and improves science from 71.88% to 86.46%,
versus 76.04% for the retained constant branch. Math stays 46.88% and has substantial
format-readout limitations. All retained science recoveries start from parseable
wrong choices, though some native rationales already imply the right choice.
This is a useful conditional-repair finding, not broad semantic improvement.

All repairs were actually executed; retention is offline replay, with no measured
saved work or fewer Jev calls. The larger-comparison spending gate is false and
its [outline](gated-repair-larger-replication-outline.md) stays unexecuted. A separately
registered fresh selective-repair validation should admit task-specific output
instructions on development data, fix checkpoints and thresholds, isolate routing
from feedback strength, and measure real execution. No such run is claimed yet.
Do not skip evaluator admission or substitute this two-domain pilot for the
versioned ten-task scorecard.

All 3,072 outputs, 12 adapter checkpoints and all failed attempts are archived.
Public replay reproduces all four main analyses exactly; original weights remain
unchanged. All resources are deleted. R25 adds **$5.85**, reaching **$42.63/$75**
with approximately **$32.37** remaining before tax/separate network. The budget
increase is cumulative and has not been treated as $75 additional spending.
