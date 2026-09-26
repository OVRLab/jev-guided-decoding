# R16 prospective FP32 execution amendment

Registered 2026-09-22, after the admission failure and numerical diagnostic but
before any Jev request, development selection or evaluation output.
The [original protocol](adaptive-attention-protocol.md), initial runner and
manifest remain byte-for-byte preserved.

The [diagnostic](adaptive-attention-cache-diagnostic.md) ran 12 native/R15 cache
comparisons per precision on six mechanics/development contexts. BF16 had maximum
absolute vocabulary-logit difference 0.5458984375 and maximum KL(full||cache)
0.0044322864; FP32 reduced these to 0.0000591278 and 1.9134e-11. Argmax matched
in all 24 comparisons. This supports a precision-dependent numerical discrepancy,
not a mathematical cache/mask discrepancy on these examples.

Run every arm in FP32, preserving the checkpoint's stored parameter values through
exact widening, without training. Use full-vocabulary cache tolerance 0.0001 plus
equal argmax; preserve exact zero identity and exact prior/new hook equivalence.
The selected R15 policy is rerun in FP32 on the same new cases as every control;
its result must not be compared directly to the historical BF16 aggregate.

Use a separate `adaptive_attention_fp32.py` runner with the original implementation
preserved, and `adaptive-attention-fp32` manifest/output. Source inspection must
show only explicit precision/admission/manifest-path changes. All scientific
policies, development selection, seeds, prompt contracts, data, grading, job
schedule, API limits and primary contrasts remain unchanged. All six selected
JSON cohort/schedule files must hash-identically to the original manifest.
Record original stopped files and the diagnostic in the final report, including
cloud costs. No paid or benchmark work is replayed: none had started.
