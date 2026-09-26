# R15: surgical refinement of Jev evidence attention

Prospective plan, 2026-09-22 Amsterdam. The owner authorized full implementation,
cloud testing and documentation after R14's positive native-baseline result.
This is a new experiment, not a change to R14's frozen success criterion or results.

## Goal, scope and navigation

Improve the **Granite-generated answer** beyond both original Granite and the
specific R14 Jev policy on fresh containment cases. Keep the same checkpoint,
provider rubric, evidence, seven-label grammar and frozen weights. Independently
measure whether the new policy generalizes to longer chains and whether simpler
controls explain its value. No promise that tuning will help.

1. Record exposed R14 diagnostics and hypotheses below; preserve its raw artifacts.
2. Implement fresh authored cohorts, a bounded policy grid, a thin wrapper over the
   verified R14 hook, and a durable calibration/test runner under
   `research/iterations/evidence_v2/`. Add capability/negative-path tests first.
3. Freeze this protocol, new source/data hashes, and the original R14 head-ranking/
   policy inputs before any new model inference. Run canonical local checks.
4. Use one small Nebius L40S or comparably priced AWS GPU within the existing $50
   cumulative ceiling. Verify credentials privately, retain deployment/cost records,
   provision an expiry timer and monitor independently from the client.
5. Evaluate all 90 configurations on 96 development worlds with two contexts each.
   Select once using only development outcomes; freeze before held-out inference.
6. Run the twelve-arm comparison on 600 fresh test worlds and separately on 120
   longer-chain challenge worlds. Keep all attempts, failures and unchanged ablations.
7. Independently audit token/source/bias provenance, selection, complete schedules,
   grades, raw receipts and paired statistics. Retrieve/hash all artifacts; delete
   task resources; publish the report, raw traces, figures and paper-draft update.

## Exposed evidence motivating the search

R14 is permanently exposed for design. It showed 42.22% native versus 51.25% Jev,
with +9.03 pp adjusted interval [5.83,12.50], but inconclusive lexical/prompt
superiority. Its one-link answerable cases score 40/120 native, 68/120 Jev and
91/120 lexical/oracle; two-link answerable cases score 21/120 native, 46/120 Jev
and 24/120 lexical. Three-link answerable cases score 13/120 native and 22/120 Jev.
These are post-hoc descriptive counts over paired context variants, not new tests.
They suggest separating weak emphasis on obvious evidence from useful bridge-fact
selection. They do not prove either mechanism causes the remaining errors.

R14 selects heads/strength using binary oracle scores, then deploys soft Jev scores.
A score of 0.9 receives only 80% of the oracle bias. Directly calibrating the deployed
Jev policy can test this mismatch. Hard thresholds may also amplify false positives
or lose bridge facts. A narrower query scope may preserve question processing;
more/fewer heads or higher strength may help or harm. All are hypotheses.

The [TypeSafe Noul contract](https://docs.typesafe.ai/primitives/noul.md) describes
probability of a yes/no judgment, not an attention coefficient; the mapping below
is an explicit controller choice. Its [reranking example](https://docs.typesafe.ai/cookbooks/rerank_typesafe.md)
is a pattern precedent, not evidence for these heads or thresholds. Live pages were
read on 2026-09-22 via direct HTTP after the browsing tool could not open them.

## Frozen policies and search

Original model: `ibm-granite/granite-4.0-1b`, revision
`6a7381ba1f54d684ff508d991aeb7dc580157103`; hosted requested model `jev-1.13.0`.
Use existing R14 Noul source-chain questions unchanged, with no reference answer,
final-label choice question, tensor or hidden state supplied to Jev.

The R14 policy is the exact top-eight query heads from its recorded ranking,
strength ln(8), soft mapping and all query positions following the evidence block.
Preserve its recorded parameters, not a retrospectively optimized reconstruction.

Search the complete Cartesian product, **90 configurations**:

| Factor | Fixed candidates |
| --- | --- |
| Head count | Top 1, 2, 4, 8 or 12 heads in the original R14 development ranking |
| Strength | ln(4), ln(8), ln(16), each below the hook's bound of 3 |
| Score mapping | `soft`: max(0,2r−1); `hard50`: indicator r>0.5; `hard80`: indicator r>0.8 |
| Query scope | `question`: all positions after evidence, as R14; `answer`: only the last input position predicting the answer token |

Only selected source-key/head/query coordinates change. All-equal **mapped** span
scores yield no intervention, preserving the existing hook's convention. Hard
mappings are represented as 0/1 scores through that hook; soft uses raw scores.
Record both original Jev scores and the actual mapped scores, selected heads,
requested per-token bias, scope boundary and returned logits. Applied masks use
ordinary BF16 quantization. The original R14 configuration is in the grid.

The runtime wrapper must not mutate the R14 modules or historical manifests. New
code lives outside R14's source-glob directory. Zero intervention must match native;
`answer` scope must change no earlier query coordinates. Reject malformed scores,
unknown policies, mismatched source counts, cache reuse and concurrent requests.
Granite chooses all semantic labels from the same seven allowed tokens.

## Fresh cohorts and selection

Generate all cohorts before inference, with independent fixed seeds and disjoint
case IDs/aliases from R14 and each other. Use the R14 held-out “contains” sentence
template for **both** new development and test, removing R14's development-to-test
wording shift. This difference is disclosed; R14 is rerun as a frozen comparator
on the same new inputs, not compared by its old aggregate accuracy.

- Development: 96 worlds, depths 1/2/3 crossed with complete/missing final link,
  balanced six cells, each with light (three irrelevant edges) and heavy (18) context.
- Primary test: 600 new worlds with the same six-cell structure and two contexts.
- Challenge: 120 new worlds, depths 4/5/6 crossed with complete/missing final link,
  two contexts. This tests longer chains, not unrestricted language generalization.

All room labels remain available in every case. Half of each cohort is UNKNOWN,
so publish the 50% constant-UNKNOWN reference and answerable/missing breakdowns.
Do not convert relevance or empty source maps directly into a final UNKNOWN label.
A separate visible-sentence parser follows directed links to grade every answer;
construction-time graph expectations and split disjointness are also checked.

Each development context has one native forward and all 90 configurations, using
one Jev receipt shared across policies. The first twelve contexts additionally
compare a zero hook to the native **full vocabulary** within 1e-6 and exact token
identity. All calls must have valid receipts and model-token provenance before
selection. No positive pilot score is required for technical admission.

A candidate is eligible if, on development, it reduces neither answerable nor
missing-link accuracy nor light-context accuracy by more than 3 pp relative to
R14. Select by overall accuracy, then mean reference log probability over the seven
labels, then fewer heads, lower strength, mapping name and scope name. The R14
candidate is always eligible; allow selection to remain unchanged. Tuning results
are optimistic development evidence, never the held-out result. Record every grid
outcome, eligibility reason and the selected-policy hash before opening test data.

## Twelve held-out arms

| Arm | Definition |
| --- | --- |
| native | Original Granite with complete evidence and common answer grammar |
| r14 | Exact previously selected R14 attention policy with a fresh shared Jev receipt |
| r15 | Development-selected new policy |
| shuffled | R15 policy with the same Jev scores deterministically permuted among sources |
| lexical | R15 heads/strength/scope/mapping with the existing query/source overlap scores |
| prompt | Same Jev evidence marked `<focus>` when raw relevance >0.5; no attention hook |
| oracle | R15 policy with privileged binary source annotations, diagnostic only |
| zero | R15 hook interface at strength zero, no semantic guidance |
| mapping_only | R14 parameters with only R15's selected mapping changed |
| heads_only | R14 parameters with only R15's selected head count changed |
| strength_only | R14 parameters with only R15's selected strength changed |
| scope_only | R14 parameters with only R15's selected query scope changed |

If an ablation equals R14, retain it and its identity evidence; do not substitute
another post-hoc interesting configuration. Native and attention prompts match;
prompt highlighting changes tokenization but retains every source. Rotate arm
order deterministically per context. Share each Jev receipt across dependent arms,
count actual calls once, and separately include one call in deployment latency.
No network call occurs inside an attention forward. No scoring is refreshed during
this one-token final generation; dynamic reasoning remains a different experiment.

## Statistical questions and decision criteria

**Primary improvement claims:** R15 minus native, and R15 minus the frozen R14
policy, on the 600-world primary test. Average the two contexts within each world;
use 10,000 paired world-bootstrap replicates and individual 97.5% intervals for
nominal 95% family coverage across these two comparisons. There are no duplicated
sampling seeds treated as extra independent problems.

A next-version advancement requires at least +2 pp versus R14 and positive lower
bounds for both primary intervals. Separately report whether the native contrast
supports a gain even if advancement is unmet. This criterion is prospective for
R15 and does not replace R14's all-four-control criterion. No assertion is “proven
for sure”; intervals are approximate and population scope is limited.

Lexical/prompt/shuffled controls, single-factor ablations, class/depth/context
breakdowns, constant UNKNOWN and the longer-chain challenge are **secondary
exploratory** evidence. Publish paired point changes and explicitly unadjusted 95%
intervals where shown; do not label them confirmatory superiority after multiple
searches. Do not gate completion on beating every simpler control. Hold the selected
policy fixed for the challenge; do not tune or choose it using challenge outcomes.

All missing/failed outputs stay incorrect in planned denominators. Report raw
counts, confidence intervals, fix/regression counts, actual model/API work, provider
incidents, memory/environment limitations and complete/failed/never-started schedules.

## Failure, resources and verification

Use fresh no-overwrite directories and a durable started record before each model
or scorer operation. No started job is replayed to replace failure or an unfavorable
answer. Reuse the verified one-attempt Jev transport and durable input-token budget.
During development stop on any provider error. During held-out stages, an explicit
429/529 may mark the eight Jev-dependent arms failed for that context, with usage
receipts absent and conservative maximum charge;
continue only never-started contexts after Retry-After (at least 60, at most 300 s),
at most three incidents over the entire run. Do not replay ambiguous timeouts.
Stop on other API/authentication/integrity/model failures, preserving partial outputs.

Exact dependent arms are r14, r15, shuffled, prompt, mapping_only, heads_only,
strength_only and scope_only (eight); native, lexical, oracle and zero are independent.
Report the full failed dependent set, not an inferred outcome. A failure during a
model forward stops the run and leaves every remaining scheduled key unstarted.

Prior cumulative estimate: $9.272902379. Keep the existing $50 total ceiling;
new conservative API cap $1 and cloud allowance $5. Use one L40S around $1.56/hour
including CPU/RAM/disk, verify price/capacity before launch; no 8-GPU machine.
Expected work: 17,472 grid/native forwards, twelve extra zero checks, 14,400 primary
and 2,880 challenge outputs = **34,764 model decisions**; **1,632 Jev calls** if complete.
Allow 90 minutes within the runner and a two-hour VM expiry, monitored externally.
If interrupted, preserve results and report the limit; do not extend into new spend
without checking the remaining cumulative authorization. Actual paid usage may be
lower than reservation ceilings; prior unknown usage remains conservatively carried.

Test before inference: fresh data/graph grades and no overlap, grid identity,
threshold boundaries/equal scores, head choices, exact R14 pass-through, last-query
mask locality, no input mutation, native/zero identity, failed-provider accounting,
complete scheduling, deterministic selection including unchanged winner and class
floors. Core tests remain offline; real tokenizer/model checks are clearly identified.

Public artifacts: protocol, manifests, selected policy, all grid and final traces,
exact inputs/token offsets, typed requests/receipts without keys, independent audit,
figures, cost/cleanup summary and hashes. Keep private account IDs, keys and network
records outside Git. Model weights must hash identically before/after. Update
notebook/register/paper draft, inspect PR/CI/review context, and report results with
separate engineering, statistical and publication status.
