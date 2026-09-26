# R29-A: localized feedback and preservation capacity study

Registered 2026-09-26 before inference. The owner authorized implementing and
exploring the [proposal](structured-correction-proposal.md). This first stage is
an authored mechanism study, **not a new public benchmark or north-star victory**.
Old protocols, outputs and benchmark scores remain unchanged.

## Plan and decision sequence

Implement new `research/iterations/structured_correction` data/checker, feedback,
bridge, training, execution and audit modules, with meaningful failing tests first.
Run tiny-model and reference-free API admission before paid GPU work. Complete
the controlled study, independently reconstruct outputs and publish the result.
Use that evidence to choose whether fresh public transfer, better correction
training, or stopping this mechanism is justified. Do not spend on broad suite
repeats while the basic mechanism is unsupported.

## Question, data and scope

Can independently localized judgments help a trained internal branch correct
natural Granite errors while retaining correct responses? Two authored task
families provide an independent executable oracle: temporal transfers of objects,
and compositional object/container/room tracking. Each world has three questions,
six objects, four containers, six rooms, eight ordered events, and distractors.
The oracle updates an explicit state; generation and Jev receive only the natural
language world and questions. All final tokens belong to Granite.

Generate 128 train, 32 development, 96 test worlds, balanced across two families,
using separate deterministic seeds 29001/29002/29003. Freeze exact case and reference
hashes before inference. Fresh instances share task templates: this tests new-world
generalization, not public benchmark performance, unseen task templates, or absence
of pretraining contamination. Include all natural drafts without filtering by
correctness. Publish authored data under the repository license.

Require three numbered answer lines; no constrained decoder, label menu or forced
UNKNOWN. Score semantic correctness of each requested location with a frozen
parser allowing case/whitespace and terminal punctuation variation. Score all
three correct as primary; report format compliance separately. Tests must cover
missing, duplicate, contradictory and extra answers. Gold locations are separate
from inference cases. Jev never receives the oracle state or reference answers.
An oracle-feedback diagnostic deliberately receives per-question correctness;
it is labeled nondeployable and excluded from live-Jev performance claims.

## Model, feedback and internal mechanism

Frozen dense Granite 4.0-1B revision
`6a7381ba1f54d684ff508d991aeb7dc580157103`, Torch 2.8.0 and Transformers 4.57.1.
FP32 backbone and adapter, greedy, at most 128 new tokens for native and repair,
2,048 input tokens and 256 training-target tokens. No silent truncation.

Jev 1.13.0 answers three independent Noul questions in one request, one per actual
numbered question, about whether the supplied draft answers it correctly. Retain
probabilities, complete payloads and receipts. One attempt per case, durable
maximum-input reservation before dispatch, no replay on unresolved errors.
Timeout/failure stops the stage with its reservation retained. Admission has at
most six calls and $0.02; study calls have a separate $0.18 cap.

Memory slot i contains the mean frozen input embeddings of question i and its
actual draft answer span, never its gold answer. Empty/unparsed spans are explicit.
Use a rank-32 branch after zero-indexed block 19. With normalized repair state n,
normalized memory m, correctness probabilities p, and learned D/K/V/U:

    a = softmax((D n) (K m)^T / sqrt(32))
    c = sum_i a_i (1 - p_i) tanh(V m_i)
    h' = h + 0.5 RMS(h) tanh(U (tanh(D n) * c))

U starts at zero. All-p=1 is exact branch identity even after training. Slot-wise
feedback changes the transformation direction, rather than just one global gain.
The embeddings and Granite/Jev weights remain frozen; train D/K/V/U only. This
four-matrix branch has 262,144 parameters at width 2,048. All trained arms have
identical capacity. Apply at the last repair-prompt position and subsequent repair
tokens, with independent caches and scoped hooks. Do not rewrite earlier states.

## Training and controls

Train five conditions with identical initialization/order/optimizer per seed
2901 and 2902: structured live, scalar live (mean repeated in all slots), constant
(all p=0.5), text feedback (live scores in repair instruction, p=0.5 internally),
and oracle (independently checked slot correctness). Two epochs, AdamW lr 0.001,
zero weight decay, accumulation eight, gradient norm clip one. Correct native
drafts use their exact original generated token sequence as preservation targets;
incorrect drafts use the independently constructed three-line answer plus EOS.
Formatting alone must not make a semantically correct draft a rewrite target.

Select each condition's epoch by development all-correct accuracy, earliest on
ties. Save all checkpoints and selection before any test generation or Jev calls.
Use a common blind repair instruction except the explicit text-feedback arm.
Test native, untrained blind repair, the ten selected trained conditions, and each
structured model with within-family cyclically shuffled probability vectors
(no self donor; valid recipient question/answer memory retained). Oracle is a
diagnostic, not a competitor in deployable headline scores.

Report raw repair candidates first. A secondary retention policy uses the minimum
live slot-correctness probability: repair when it is below threshold t in
{0, .1, .2, .4, .6, .8, 1, 1.01}. Choose t on development net correctness, ties
prefer fewer repairs then smaller t. Freeze it per structured seed; apply the same
case allocation to structured/shuffled/scalar/constant/text comparisons. Such
constant/text selections share Jev routing and are not wholly Jev-free systems.
Raw constant and blind repair remain independent Jev-free generation controls.
This is offline policy replay, not a claim of measured skipped API or GPU work.

## Admission, analysis and advance decisions

Before training, require initial zero-output parity, trained all-p=1 identity,
base gradients absent, finite loss and nonzero adapter gradients, scoped-position
and cache isolation, and FP32 cached/full agreement (max logit error <=0.001 and
equal argmax). Save original backbone digest before/after the complete study.
Development with fewer than four native errors is an underpowered admission
failure: stop without fresh test, preserve the result and design a new protocol.

For the fixed 96 test cases report each family and seed, paired seed-mean effects
with 10,000 stratified bootstrap draws (seed 2900), 95% exploratory intervals,
corrected errors, damaged correct answers, per-slot correctness, format, empty and
length stops, token-level feedback dependence, wall time and all resource usage.
Missing outputs make a stage incomplete; never shrink the denominator. These
small exploratory intervals are not confirmatory multi-benchmark evidence.

Three separate questions guide follow-up: (1) positive net gain over native,
(2) benefit from live alignment beyond constant/scalar/shuffled alternatives,
(3) benefit of internal placement beyond equally trained text feedback. Do not
equate one positive contrast with success on all three. Oracle success with live
failure points toward diagnosis/conditioning; oracle failure points toward repair
capacity/training. If a simpler control wins, pursue that evidence rather than
claiming internal architectural superiority. A public-transfer protocol is frozen
only after this diagnosis, with fresh source-disjoint cases and its own budget.

## Resource limits and recovery

Starting conservative cumulative estimate $113.99886002437508 against $125.
Reserve no more than $8.50 total for R29-A: one AWS g6.xlarge (one L4) for at most
five hours if refreshed price remains <=$1.02/hour, $0.15 disk, $0.20 Jev including
admission, $0.03 IPv4, $1 egress and $2 contingency. Worker maximum 4.5 hours,
independent host shutdown at five hours; no automatic extension or second GPU.
Local CPU/MPS checks may precede deployment. Stop before dispatch if the remaining
reservation cannot cover the request. Unconfirmed tax/network is not an invoice.

Monitor at least every 15 minutes, back up incrementally, preserve failed jobs and
unknown charges, verify final inventory/hashes before deleting owned resources.
No restart of ambiguous provider requests. If interrupted, register recovery from
exact completed artifacts before any resumed inference. Completion includes
independent audit, report/notebook/register updates, checks and cloud cleanup.
