# ProofWriter development integration pilot

The nine-run MPS pilot completed without provider or backend failures. Each of the
three executed arms matched two of three independently checked verdicts. This tiny
development check establishes integration only; it does not establish an accuracy
gain. The 200-problem, three-seed, four-arm evaluation remains pending.

| Executed arm | Correct / planned | Completed | Total seconds | HTTP attempts |
| --- | --- | --- | --- | --- |
| Step-guided Granite + fixed Jev choice | 2/3 | 3/3 | 57.85 | 9 |
| Unguided Granite + same fixed Jev choice | 2/3 | 2/3 | 211.89 | 3 |
| Direct Jev choice | 2/3 | 2/3 | 0.96 | 3 |

All arms correctly classified the entailed and unknown cases. On the contradicted
case, guided mode returned UNKNOWN while the other two abstained because their
maximum choice probability was below the fixed 0.75 threshold. Abstentions count
incorrect and are distinct from semantic UNKNOWN. Guided search itself completed
no generated answer; unguided search completed one noncanonical answer, with zero
strict verdict matches. Those generated outcomes reuse the same paths without
additional inference and are not independent runs.

The guided arm generated 386 tokens, consumed 429 padded decode slots and 16,170
prefill tokens. The unguided arm generated 1,502 tokens, consumed 1,752 padded slots
and 60,033 prefill tokens across its three jobs. Equal per-job ceilings therefore
did not produce equal computation. Guided search exhausted eligible candidates
early; two unguided paths reached their time budget. Timing excludes model loading
and the two-token warm-up at batch sizes one and three.

## Provenance and limits

- Source: `f97ef497049545c26bb15ee558e6440e70f30457`, clean at freeze.
- Freeze time: 2026-09-20 14:13:31 UTC; development split only; seed 42.
- Cases: `RelNeg-OWA-D5-455/Q8`, `AttNoneg-OWA-D5-844/Q3`,
  `RelNoneg-OWA-D5-481/Q20` (one distinct theory each).
- Model: original `ibm-granite/granite-4.0-1b`, revision
  `6a7381ba1f54d684ff508d991aeb7dc580157103`, zero trainable parameters.
- Runtime: MPS, bfloat16, Python 3.12.13, Torch 2.8.0, Transformers 4.57.1,
  macOS 26.3.1 arm64; model load 3.93 seconds.
- Jev: pinned `jev-1.13.0`; 15 total HTTP attempts; no unknown usage.
- Frozen dataset SHA-256:
  `87ebd5b4f005cf97e3cd2de56cb0bd9e72fc89cebd5290e87434ecb3c7b7addd`.
- Raw runs SHA-256:
  `d7021f31917887935314c4a940cea4d992b16a6c1a5b4ab3a891d83a665d88b2`.

The [protocol](../../docs/proofwriter-experiment.md) specifies archive provenance,
reproduction, budgets, the independent symbolic oracle, and data-rights limits.
Raw external examples and full traces are retained privately in
`results/proofwriter-pilot-20260920`; this report publishes aggregates and IDs.
The leading-claim checker is a partial semantic audit, not verification of complete
reasoning or cited justifications. The final-only control was added afterward to
remove a confound, before any held-out inference; its GPU pilot remains pending.
