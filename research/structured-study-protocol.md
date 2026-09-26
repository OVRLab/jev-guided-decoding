# R13: common-syntax inference comparison

Registered 2026-09-21 before new Granite inference. Implements the owner's request
to repair all issues and run a full Nebius comparison under the existing $50 cap.
The [recovery plan](../docs/recovery-and-nebius-study.md) records the prospective
change from R12's unpassed critic-superiority gate to operational admission for an
exploratory comparison. R12 remains unchanged. Negative results are retained.

## Hypothesis and scope

At a property commitment during an intermediate claim, Jev scores four short
counterfactual Granite continuations against the original evidence. A bounded
change to the next-token distribution may improve Granite's eventual answer.
This is an output-logit intervention during inference, after Granite's final
normalization/projection/scaling, not a hidden-layer fusion or trained checkpoint.
Hosted API latency is included. No colocated-speed claim is supported.

Authored finite unary rule worlds provide exact independent grades: 24 development
worlds, then 300 fresh test worlds with 100 each TRUE/FALSE/UNKNOWN. Six motifs are
forward chains, conjunctions, explicit negative chains, negative conjunctions,
missing conditions and reversed implications. All include distractor entities.
Development uses depths 2/4; test uses 3/5 and a different rendering template.
Motifs overlap deliberately. This tests controlled rule reasoning, not broad
language/math ability or an independently sourced benchmark distribution. R10's
GSM8K/ProofWriter findings remain separate. Reference labels and symbolic rules
never enter the controller's input view or Jev payload.

## Seven arms

All use the identical task/evidence/system prompt and original pinned Granite
4.0 1B weights. The native arm opens the final frame immediately. Other arms
produce exactly two tentative intermediate claim frames before the final phase.
A shared token trie allows every positive, negative and not-established sentence
over the input lexicon, irrespective of truth. It fixes syntax, not semantics.
It therefore changes staged inference and is explicitly controlled, not described
as unmodified native generation. Opening delimiters are code-supplied and counted
separately; semantic tokens and closing delimiters come from Granite distributions.

| Arm | Intermediate decision |
| --- | --- |
| native | Direct Granite final answer, no intermediate work or Jev |
| staged | Native sampling under the shared grammar |
| likelihood | Four greedy lookaheads; commit the root with highest mean masked log probability, then native-sampled tail |
| jev | Same lookaheads; bounded Jev bias selects one root token, then native-sampled tail |
| shuffled | Same procedure with Jev utilities permuted across roots |
| zero | Same Jev shadow work, strength zero; must reproduce staged exact tokens |
| soft_step | Same Jev root policy, but commit the entire selected greedy lookahead if its root was evaluated |

The first entity–predicate boundary per step triggers at most one intervention.
Top four distinct syntax-permitted roots are evaluated; other permitted probability
mass remains. Native means the grammar-conditioned distribution at this point.
Jev support is used only when assessability ≥0.5; an unassessed top-probability
reference produces a no-op. Bias strength 2, absolute cap 0.5, full-distribution
KL cap 0.02. No Jev hard threshold removes a root. The likelihood arm is a
length-normalized search heuristic, not native sampling. All modes use isolated
per-position RNG seeds; shadow work cannot consume the committed sampling stream.
Final decoding is greedy and unconstrained by the claim grammar. Native repetitions
across seeds are expected to be identical and are clustered by world in analysis.

The final contract accepts exactly TRUE, FALSE or UNKNOWN terminated by </final>
or model EOS; a token/time truncation is invalid. Jev never sees or supplies that
answer. Exact accepted IDs are preserved, and the final backend's full text is
reconstructed from those IDs before the run can count as successful. R12's missing
closing frames are not retroactively regraded under this new contract.

## Freeze, execution and admission

The prepare command writes source hashes, pinned model revision, data files/hashes,
prompts, limits, seeds and statistics in a new immutable protocol directory.
Commit that directory before running. Source/data drift is fatal. The pilot is
24 worlds × one seed × seven arms = 168 jobs. If admitted, test is 300 worlds ×
three seeds × seven arms = 6,300 jobs. Arm order is deterministically shuffled
within each world/seed. Every job is durably marked started before inference;
every completed or failed trace is fsynced. No automatic replay/resume is allowed.

Admission requires all jobs complete, each arm ≥90% final-format success, overall
≥95%, independent grading of ≥99% of lookahead claims, checkpoint coverage ≥80%,
all token/prompt audits passing and exact staged/zero identity for all pairs.
Accuracy gains and critic ranking are reported, not admission criteria. The pilot
also projects runtime with a 1.5× margin before admitting main execution.
If the gate fails, preserve it and diagnose; any changed protocol is a new version
with the failed pilot disclosed. Test outcomes never guide a protocol correction.

Reasoning ceilings per job: two steps, 40 tokens/frame, four roots/checkpoint,
384 forward calls and 200,000 repeated prefill tokens, context 4,096 tokens.
Wall limit 90 seconds reserves 15 seconds and 16 new tokens for the final answer.
Each lookahead allows 15 seconds; Jev permits one attempt, at most 30 seconds and
never beyond remaining reasoning time. A reasoning work limit retains the last
complete prefix and uses the final reserve. Provider/backend/integrity failures
stop the stage and remain failures, never silent baseline fallbacks. Explicit
unknown usage stays charged at its reservation maximum and blocks new dispatch.

Model execution re-prefills at each explicit token step; lookaheads are isolated.
This is a correctness reference, not retained-KV serving. Count repeated prefill,
actual forward calls, speculative tokens, forced root tokens, final decode slots,
latency, API requests and receipts; equal ceilings are not equal realized compute.
Weight digests before/after, software/hardware metadata and loading/warm-up timing
are retained. Inference tests use CPU tiny models; all paid work is separate.

## Analysis and resources

All planned jobs enter accuracy denominators; invalid, missing and failed answers
are incorrect. Average the three seeds within each world, then bootstrap worlds
5,000 times (seed 198271). Primary contrasts: Jev minus native, staged, likelihood;
98.333% individual intervals give a Bonferroni 95% family level. A claimed useful
gain requires a point difference ≥5 percentage points and an interval above zero.
Report other controls descriptively; do not select a winning placement after test.
Report critic discrimination, mixed candidate sets and selection changes separately
from final-answer quality. Such diagnostics cannot replace an independent outcome.

One temporary Nebius L40S, 8 vCPU/32 GiB, 80 GiB managed SSD, 18-hour shutdown guard;
current compute $1.5484/hour plus disk/network, conservative planning $1.57/hour.
New cloud cap $30, shared historical Jev cap $3 and prior total estimate $3.2913
remain inside the owner's $50 total with overhead reserve. Pricing source:
[Nebius](https://docs.nebius.com/compute/resources/pricing). Jev 1.13.0 input pricing
$0.042/M, outputs free per [provider models](https://docs.typesafe.ai/models);
ledger reserves at $0.05/M with 65,536 input tokens per attempted request.
Copy the existing key privately to a mode-600 file on the task server; never log it.
Verify successful authenticated scoring in the pilot. Retrieve all artifacts,
verify hashes and delete only this deployment's VM, managed disk and network rules.

The API recovery manifest was committed before two successful local calls: fresh
authentication and the exact earlier failing request shape, 1,910 input tokens
total. This demonstrates current access, not the cause of the old HTTP 400. The
old unknown call was explicitly carried at its full maximum charge; no usage
receipt was fabricated. Enhanced errors now retain redacted diagnostic bodies.

Tests were added and observed failing before implementation for error diagnostics,
durable unknown-cost resumption, grammar/trie/EOS, tokenizer boundary preservation,
independent balanced worlds, controller no-op/failure/final reserve/provenance,
and missing-job/duplicate/clustered-statistics handling. Preflight: 291 tests passed
before this protocol was written; subsequent changes require fresh checks.
