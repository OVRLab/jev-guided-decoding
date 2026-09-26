# R31 audit correction: CUDA device naming

Recorded 26 September 2026 at approximately 12:47 UTC, during train/development
native-draft collection and before adapter training or held-out test generation.
No partial R31 quality scores were inspected for this correction.

The actual CUDA mechanical admission passes. Its implementation records
`str(next(model.parameters()).device)`, which is `cuda:0` on this single L4.
The frozen full-run auditor compared that field with the CLI device spelling
`cuda`, so an otherwise valid completed study would be rejected at that check.
This is a metadata alias defect, not a failed cache, gradient or model admission.

The [separate corrected audit entrypoint](diagnostics/audit_contextual_completion_v2.py)
normalizes only `cuda:0`/`cuda` to `cuda` in the mechanical-admission dictionary
supplied in memory to the original auditor. CPU, MPS and other device indices are
rejected. Every other field and all original source, input, token, memory, training,
checkpoint, API and statistical checks remain in force. The raw admission file is
not rewritten; its hash is checked afterward and recorded with the correction's
own source hash in the analysis.

The worker continues at frozen commit `30bb4bc184d3ce553af9b4f59f8e0da17a6a2eaf`.
Its code, protocol, cases, selected weights and outcomes are unchanged. This is
an explicitly documented audit revision, not a rewritten frozen experiment.
A regression was observed failing before the correction existed, and then passed
for the observed alias, immutability and rejection of invalid devices. The final
local audit must use this entrypoint on a copy of the verified backup.
