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

## Completed local result

[Actual MPS record](diagnostics/musr-single-interface-20260926/actual-mps-mechanics.json)
passes on pinned Granite 4.0-1B, device `mps:0`, at source
`b954f97620569d699328784efb0e5aa920aaae4a`. The selected exposed case is
`musr/murder_mystery/134`; the fixed draft remains synthetic `ANSWER: 1`.
Initial-zero and disabled-branch logits exactly equal the original repair-prompt
logits. Nonzero-branch cached/full maximum logit discrepancy is **0.00007582**,
with equal argmax. Both original-weight digests match, all backbone gradients are
absent, and hooks are removed. The single contextual vector has width 2,048.

Extraction processes 1,153 original tokens in 1.95 seconds; the complete process
takes 43.25 seconds including loading. No API call or task-accuracy score is produced.
The [provenance receipt](diagnostics/musr-single-interface-20260926/actual-mps-provenance.json)
retains the exact input/result hashes. These timings are one local mechanical
measurement, not GPU throughput or a deployment benchmark.

Reproduction uses the [pinned MuSR source admission](musr-transfer-admission.md):
load its six CSV/author files with `musr_transfer/data.py`, select the first sorted
development case, load the original model with `structured_correction/study.py`,
build the single-question prompt and synthetic draft with its pinned tokenizer,
then pass `positions_for(...)` and `repair_prefix(...)` to
`musr_transfer/admission.py`'s `admission(...)`. Full source hashes accompany the
record. GPU-specific mechanics must still pass before any paid transfer run.
