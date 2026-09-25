# Completed-system audit verification

Scope was written in `research/completed-granite-audit-v1.md` and linked in the
research notebook/register before fresh grades were inspected. The original
full-tranche auditor and its `review_required` result remain unchanged. No
completion marker was fabricated; the new result admits only the nine complete
Granite systems and never grades partial Qwen.

The first four tests failed because the new audit module was missing. Selection
tampering/coverage testing then passed using the frozen selection check. A further
evaluator-binding test failed because that capability was absent, then passed
after adding strict code/environment/seed verification. All six new tests pass;
38 targeted audit, recovery and reporting tests pass. The full suite passes
**640 tests in 13.57 seconds**. Lint, format and guidance checks pass.

Before either scoring dispatch, all 143 backup files matched the saved remote
SHA-256 inventories. A private pre-grading record binds the new auditor, frozen
v3 auditor and scope document. Both completed audit outputs match these exact
hashes. Full tokenizers were loaded only from the local pinned revision cache;
no model was loaded or generated. Each stream passes recovery/source envelopes,
frozen data/reference/checkpoint bindings, serial jobs/batches, native/repair
prefixes, EOS/terminal/limit decisions, decoded text, block-19 hook events,
unchanged completed-model weights, donor/feedback/selection provenance and Jev
receipts. There is one explicit unfinished Qwen native job per stream.

IFBench evaluator code and requirements hashes match its original manifest;
language seed remains 2701. Strict/loose scoring and the v3 answer readout are
unchanged. Full and project-untouched quality results both retain every expected
case. Export rejects altered denominators, omitted systems and included Qwen
scores, and removes private per-case grades and unrecognized payload fields.

The post-hoc parseability diagnostic uses only already-frozen boolean grades. It
partitions the guided/native wins and losses; it does not regrade answers,
inspect hidden reasoning, remove cases or establish causal semantic attribution.

Reproduction requires the privately archived freezes (including references), all
original/recovery output folders, and cached tokenizers at the manifest revisions.
Run from the repository environment:

```bash
uv run --no-sync python research/diagnostics/completed_granite_audit_v1.py --help
```

Supply
the ordered ancestry ending at the selected final output. IFBench also requires
the pinned evaluator, its requirements file and its existing evaluation environment.
The tool refuses to overwrite an existing audit. No API key, cloud VM or model
generation is required. Public aggregates alone cannot reproduce token auditing.

Neither the paired intervals nor the scope change establishes confirmatory
multi-benchmark superiority. Model parameter count excludes hosted Jev; recorded
tokens/time omit interrupted unfinished work and are lower bounds on total work.
No model, package, paper submission or repository merge is authorized by this audit.

A further post-hoc diagnostic exports the four GPQA reference-label counts and
all constant-letter accuracies. The always-B comparison is labeled retrospective;
no model, parser, option order or denominator was changed in response.
