# Single-question mechanical admission, before live transfer

This is an unpaid mechanics check, not a benchmark run or checkpoint selection.
While R31 remains frozen and active, validate the separate single-question runtime
on the local MPS device using the original pinned Granite 4.0 checkpoint. No Jev
request, new cloud resource or changed original weight is permitted by this check.

Use the lexicographically first of the twelve already exposed MuSR development
questions, a fixed synthetic `ANSWER: 1` draft and the actual pinned tokenizer.
The synthetic field is independent of its reference and must never be presented
as native inference or graded for accuracy. Bind exact IDs and pooled positions,
the single-question repair prefix, source hashes, model revision and device.

Add a mechanical helper in the separate MuSR directory and first observe a
tiny-model capability test fail before implementation. It must compare contextual
with position-matched embedding memory, initial-zero and disabled-branch logits
with the unmodified repair prompt, and full versus cached logits under a nonzero
dummy adapter. The maximum cache discrepancy must be at most 0.001 with equal
argmax. Require identical original-weight digests, absent backbone gradients and
cleaned hooks afterward. Record failure instead of relaxing tolerance.

The dummy adapter is neither trained nor a selected R31 checkpoint. Live verifier
compatibility, GPU-specific admission, real native drafts, end-to-end transfer,
public quality and larger-model inference remain separate work after R31 closure.
