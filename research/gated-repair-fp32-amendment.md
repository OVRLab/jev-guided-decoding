# R25 v2: full-precision numerical admission and bounded restart

Registered 2026-09-23 after v1's real-checkpoint admission failed, before any
training draft, Jev request, optimizer update or held-out generation. Preserve
all v1 code, plan, data, source hashes and five backed-up output/log files.

V1's nonzero-adapter full-prefix versus cached-step test measured maximum absolute
logit difference 0.25 in BF16, above its fixed 0.125 bound; the run stopped as
specified. This is an operational/numerical failure, not a quality result. The
failed fixture did not save its argmax comparison or a native BF16 comparison;
we do not infer those observations from the exception. R22 used a float32 backbone.

V2 runs the same architecture, data, training recipe, two seeds, controls and
independent scoring in **float32** for both baseline and adapter arms. Original
checkpoint tensor values are loaded at full precision and remain frozen; every
within-study comparison shares the same dtype. No BF16 result is pooled with
FP32 results. Before live work, a separate diagnostic records native and nonzero
adapter cached/full discrepancies in BF16 and FP32 on the first three already
registered training questions, with no answer labels, training or API calls.
The diagnostic explains numerical behavior; it does not tune the architecture.

Admit the float32 worker only when initial/gate-zero logits match exactly, only
adapter gradients exist, and nonzero cached/full logits match with atol=1e-4,
rtol=1e-4 and identical argmax on the registered first training fixture. Keep
SDPA, disable TF32, record actual differences, and preserve all failed diagnostics.
There is no relaxation of the BF16 threshold; v1 remains failed. New files import
or copy the frozen runner with the explicit dtype/admission change; their manifest
includes the old dependencies and this amendment. The 640 cases/384 targets are
byte-identical to v1. No reference enters Jev or evaluation generation.

Because full precision can be slower, replace R25's $14.40 stage reservation with
**$20.00 total across both attempts**, within the owner's cumulative $75 cap.
Starting cumulative estimate before R25 remains $36.773534922020566; the old
server's actual elapsed cost counts inside this reservation. The replacement has
one L40S/16vCPU/64GiB, 80GiB disk, eleven-hour poweroff and ten-hour worker bound;
its ceiling is approximately $19.30 plus at most $0.25 API and the short first
attempt. If the combined reservation would exceed $20, shorten the new machine
bound before creation. Only one study VM at a time; verify old deletion first.
Back up throughout, stop/delete after completion and verify all owned resources.
No automatic further extension. All future inference after this amendment is v2.
