# Contextual correction memory: prospective implementation candidate

Written 2026-09-26 while R30 is running, before inspecting its quality results.
This is preparation, not an admitted experiment or a claim of improvement.
The [continuation program](feedback-exploration-program.md) still requires R30
completion, attribution analysis and cost reconciliation before another paid stage.

R29's branch pools input embeddings of each question and draft answer. These
vectors encode token identity but have not processed the record of events. The
training-only overlap diagnostic motivates testing a more contextual memory;
it does not prove that overlap causes weak correction.

## Bounded implementation

Prepare `research/iterations/contextual_memory/memory.py` and offline capability
tests. Extract three frozen memory vectors from original Granite block 19 after
a reference-free prefill of the exact original prompt and actual draft tokens.
Each vector pools the positions belonging to its question and parsed draft field.
Duplicate or missing fields contribute no answer positions; the question remains.
The last draft token is included even if generation stopped at the length cap.
No training target, repaired answer, reference or oracle label enters extraction.

Build a matched control from original input embeddings at **exactly the same
positions**. This differs from R29's standalone text with a `Draft answer:` marker;
do not present that control as identical to the old memory. Keep the branch,
capacity, insertion layer, targets, optimization and data fixed in any comparison.
Extraction adds a real model pass: record its work and time, not just repair time.

Bind positions to original token IDs, preserving byte-level Unicode boundaries;
never replace saved draft IDs with a new tokenization. Reject ambiguous question
spans, inconsistent decoded text, oversized inputs, trainable backbone parameters
and nested intervention scopes. Remove hooks on every exit. Return detached memory
and auditable token positions; extraction cannot mutate model weights or caches.

Verify first with deterministic token fixtures and a tiny real Granite model:
reference rejection, duplicate/missing fields, Unicode, changed original IDs,
context sensitivity with unchanged slot tokens, matched pooling, no gradients,
and cleanup on exceptions. A scoped actual-model admission must precede training.
R30 source/protocol remains unchanged. Final architecture and evaluation choices
require a separate prospective protocol informed by R30, not tuning on its cases.

The preparatory training utility will compare explicitly named combinations of
the two memory representations and structured, scalar or constant feedback. It
will preserve R29's zero initialization, supervised targets, optimizer and
earliest-best development checkpoint rule, keep original weights frozen, and
record every optimizer step and selected file hash. This is reusable preparation;
the exact condition set, sample sizes, seeds and spending remain unregistered
until R30 closes. A tiny-model test must verify independent equal initialization,
correct memory ownership and checkpoint selection before implementation.

## Identity and retention are different contracts

An all-one correctness vector makes the residual branch exactly inactive. That
means equality with unmodified Granite **on the same repair prompt**; it does
not return the saved native draft automatically. A blind second pass can still
change an originally correct answer. Retaining the original answer is a separate
policy decision, so mechanical off-identity cannot be reported as a guarantee of
semantic preservation. R30 deliberately records raw repair and retained policies
separately. No result-dependent change is being made to either condition.

## Related work and limits

[ReFT](https://arxiv.org/abs/2404.03592) already studies learned interventions in
frozen hidden representations. The proposed memory change alone is not a novelty
claim. [SCoRe](https://arxiv.org/abs/2409.12917) documents limitations of supervised
self-correction and studies online reinforcement learning; our small supervised
branch does not reproduce that method or establish that RL would solve this task.

[MuSR](https://github.com/Zayne-sprague/MuSR) is a possible public transfer task,
with narrative object placement among its domains. Admission must inspect its
actual contract, length, license and split, and compare original/larger generators.
Adapting our three-field branch to its question contract is a separate intervention;
it must not be described as unchanged zero-shot transfer.

The subsequent [focused prior-art check](contextual-memory-related-work.md) adds
ATLAS and its text-verifier comparison. The mechanism must be positioned against
adaptive verifier-guided steering, not only against ordinary decoding.
