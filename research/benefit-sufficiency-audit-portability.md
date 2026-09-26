# R19 logarithm reconstruction portability correction

Recorded on 2026-09-22 UTC after all 7,312 planned generations completed and before
held-out quality inspection. Both cloud episodes are deleted after verified retrieval.
This amendment concerns offline reconstruction only; no model or API call repeats.

The original main auditor rejected `benefit_features` before computing quality
tables. Across all 6,096 outcomes, 293 rows differ only in `log1p(source_count)`
or `log1p(prompt_tokens)` reconstructed on macOS from Linux-recorded inputs.
There are 158 source-count and 153 prompt-length component differences, with
overlap between rows. Every difference is one representable floating-point step;
the largest absolute difference is 8.881784197001252e-16. The four other features
match exactly. This is consistent with platform-specific `libm` rounding.

An independent decision-only pass checked all 6,096 original call decisions and
found zero differences, using both the saved feature vector and the locally
reconstructed vector for the fitted gate. No quality grades were inspected.

Preserve the original 53-file main, 55-file v1 and 57-file v2 source freezes and
the original failed audit log. Add a separate portable audit adapter. It must
accept at most one ULP for indices 3 and 4 only, reject nonfinite/malformed vectors,
require exact equality for the other four features, and retain every original
prompt, map, token, gate, weight, ledger, source and grade check. It passes a shallow
copy with only the two normalized logarithms to the original output checker;
stored records are never edited. The original selection replay already uses its
registered numerical coefficient tolerance and remains unchanged.

For supplemental reconstruction, load that same guarded output checker into the
unchanged v2 audit using a module-local loader adapter. Do not replace global
`runpy`, alter scientific source files or waive any other comparison. Record
the adapter source hash and observed normalization counts alongside results.
Regression tests must accept a one-ULP logarithm round trip, reject a larger
change or any change to an exact feature, and confirm the original checker still
receives and can reject unrelated tampering.

This tolerance is a disclosed post-completion audit correction, not a change to
generation, data, grading, endpoints or reported uncertainty. Repeat both complete
audits and public archive reconstruction through the same adapter before making
quality claims. Numerical portability does not justify changing any gate decision,
final token or raw artifact.
