# MuSR original-Granite readability admission — v1

Registered 26 September 2026 while R31 is running. This is a zero-API local
follow-up to the [synthetic-draft mechanics check](musr-mechanical-admission.md).
It does not wait for an R31 checkpoint because it uses only the original model;
it changes no R31 source or comparison and launches no cloud resource.

Generate one real native response for each of the twelve previously exposed MuSR
questions identified by the [source/exposure admission](musr-transfer-admission.md).
Use the existing single-question prompt unchanged, pinned Granite 4.0-1B revision
`6a7381ba1f54d684ff508d991aeb7dc580157103`, FP32 on local MPS, greedy decoding,
1,024 new-token ceiling and 4,096 total-context ceiling. Use exact original tokens,
a fresh cache per case, a single attempt and a 1,200-second generation deadline.
Do not load Jev credentials, apply an adapter, train weights or grade accuracy.

Freeze source hashes and the twelve reference-free input cases before execution.
Save every output's IDs, text, EOS/length status, work and timing. Independently
reconstruct tokens and readout after generation, and require unchanged original
weight digests and complete twelve-case coverage for mechanical completion.
Report readable final selections and truncations with the full denominator;
do not silently remove a difficult question or turn a formatting failure into a
correct answer. References are not included in the execution input.

The purpose is to expose output-contract problems before fresh public inference
and observe token lengths on already exposed material. There is no accuracy-based
promotion threshold, prompt search or architecture selection in this check.
Any subsequent prompt/readout correction must be versioned, tested and frozen
before the 730 fresh questions. Local timings do not estimate GPU throughput.

This prospectively extends the earlier preparation-only restriction for the
original native path. A paid transfer admission, trained R31 checkpoints, live Jev,
the larger comparator and fresh public scoring still require R31 completion,
cleanup and budget reconciliation first. Extra cloud/API cost is zero; local
electricity is not metered. The cumulative cloud/API ceiling remains $175.
