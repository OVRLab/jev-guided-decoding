# Contextual correction study — conditional draft, not registered

Prepared 2026-09-26 while R30 remains running and its quality results have not been
inspected. This is a bounded implementation plan, **not a frozen protocol or an
additional paid run**. R30 completion/audit, its interpretation and cost reconciliation
must precede the final protocol. The [program](feedback-exploration-program.md)
allocates provisionally up to $16; no new GPU is reserved by this document.

## Question and finite comparison

Does reading original Granite's context-dependent hidden representations make a
small Jev-conditioned correction branch more useful than reading input embeddings
at the same positions? [Engineering preparation](contextual-memory-proposal.md)
is implemented; its actual-model checks are not quality evidence.

Proposed finite conditions: two memory types (contextual versus position-matched
input embeddings), each trained with structured, repeated-mean scalar or constant
0.5 feedback, with two seeds. That is twelve adapters, each retaining the same 262,144-parameter
rank-32 branch after zero-indexed block 19. No original Granite/Jev weights change.

Retain **both** informative feedback forms: whether detailed feedback helps could
depend on memory quality, which R30 cannot settle using its older memory alone.
An earlier draft proposed choosing one form after R30; this revision expands the
finite factorial comparison before viewing R30 quality. R30 still informs study
admission and interpretation. Report unresolved intervals as unresolved; failure
to reject a difference is not equivalence. Mean feedback still uses three Jev
questions unless a separate question-equivalence experiment establishes otherwise.

## Proposed data and training

Generate 512 training, 64 development and 256 test worlds, balanced by temporal
and compositional family. Use a newly fixed random seed, reject all prompt overlap
with R29/R30 and independently replay references. Retain the same vocabulary and
question templates to isolate the representation change. This is a mechanism test,
not unseen-template generalization or a public benchmark.

Original Granite generates one actual native draft per case. Jev judges its three
fields once, without labels. Exact prompt plus draft token IDs feed one unmodified
prefill; pool each question and available unique draft field after block 19 and
pool input embeddings at those identical positions. Archive detached memory tensors,
position maps, source-ID hashes and actual extraction work. Duplicate/missing fields
use question-only memory. Targets and future repaired tokens never enter extraction.

Train two epochs with the existing preservation/correction targets, AdamW at 0.001,
accumulation eight and gradient clipping one. Share initialization and example order
across matched conditions; fix two new seeds before execution. Correct native drafts
use their exact original tokens; wrong drafts use independently constructed room
answers. For each condition/seed choose the earliest epoch with maximal development
all-three-correct accuracy, then freeze it before test generation. No test-tuned
threshold, learning rate, layer choice, checkpoint choice or extra epoch.

## Proposed test conditions and accounting

For each test case generate native and untrained blind repair, plus both memory
types under all three trained feedback conditions for both seeds. For each informatively
trained adapter also record same-checkpoint constant 0.5, next-case same-family
donor feedback, and a clearly nondeployable correctness oracle. For scalar
conditioning, transform oracle flags to their repeated mean too. Every arm preserves
the exact native draft prefix and owns a separate cache. Unrestricted greedy output
keeps the existing 128-new-token / 2,048-input-token limits without truncation.

This proposed design totals 38 outputs per test case: 9,728 test outputs, 576
training/development native drafts and 1,536 development repairs, or **11,840 outputs**.
There would be **832 Jev requests**, **832 contextual extractions**, **12,288 training
examples processed** and **1,536 optimizer updates**. Count each separately, including
work not used by a deployment condition; equal ceilings do not imply equal compute.

## Proposed analysis and decisions

Primary paired case effects would compare contextual structured repair with
(1) native, (2) matched embedding structured repair, (3) contextual scalar repair,
and (4) its same-checkpoint donor control. Constant-trained controls and the
memory-by-feedback interaction would be prespecified secondary analyses.
Average the two fixed seeds per
case, report per-seed results, and use a four-contrast adjusted interval family
alongside descriptive 95% intervals. Exact confidence levels, bootstrap seed and
all secondary analyses belong in the final frozen protocol.

The implementation can prepare a serial runner independently of the feedback
choice: exact native generation, one recorded judgment, reference-free memory
extraction, matched training and the fixed control matrix. A tiny-model end-to-end
test must precede that code. The runner alone will not expose a paid execution CLI;
frozen preparation, admission and an independent auditor are still required.

Report all-three correctness, per-field correctness, formatting, length stops,
native failures fixed and native passes damaged, plus family breakdowns and token
changes. A positive native contrast remains a positive native result even if another
contrast is unresolved. Claims specifically about contextual memory or Jev's runtime
information need their matching comparisons. Constant/oracle interventions share the
informative checkpoint; separately trained constant control remains separately named.

Retaining the saved native draft must remain a separate, prospectively specified
policy; an all-one branch gate only reproduces the unmodified model on the repair
prompt. Any offline retention replay must be labeled offline, with no asserted
avoided API calls or model work.

A supported improvement would justify the independently registered public transfer
stage, including the [MuSR exposure groups](musr-transfer-admission.md). If the
memory change fails, preserve the result and consider a different information
source: correctness probabilities may flag errors without supplying the corrective
content. That is a hypothesis for another bounded design, not permission for an
unlimited candidate search or a claim that such content will solve the problem.

## Operational completion

Freeze exact source/input hashes, limits, selected condition names and seeds before
new paid work. Recheck actual-worker mechanical admission with contextual memory;
MPS engineering evidence does not replace CUDA admission. Bind API receipts to exact
native drafts, reject ambiguous charges and never overwrite an interrupted attempt.
Independently audit complete denominators, selected weights, feedback treatment,
training targets, memory provenance, token chains and original-weight digests.

Reserve an explicit single-worker maximum within the reconciled $175 cumulative
cap, monitor every 15 minutes, back up incrementally and set independent expiry.
Completion includes verified raw backup, cloud deletion, statistical reconstruction,
public-safe artifacts, manuscript/notebook updates and repository checks. If a
prerequisite fails, record it and revise prospectively rather than silently relaxing
an admission or running a partial favorable subset.
