# R20 validation and execution record

The independent Qwen3-14B judge passed **96/96 constructed validation cases**:
48/48 correct-answer labels and 48/48 incorrect-answer labels, with 8/8 in every
category. All twelve separately repeated validation labels agree. The 24 diagnostic
development cases also agree with their constructed labels. All 132 outputs parse.
This admission completed before new Granite test generation.

The categories cover short/verbose equivalence, numeric equivalence, complete
multipart answers, direct/contextual abstention, false refusal, wrong partial
overlap, contradiction, unsupported guessing, incomplete answers and prompt
injection. The cases use short fictional facts and repeated templates. Their
perfect score does not establish equivalent accuracy on longer benchmark evidence;
the separate registered answer inspection probes that transfer descriptively.

Before the main generation schedule, twelve checks on three previously exposed
R19 fit fixtures compared the instrumented Granite paths against independent
native, failed-request, relevance and instruction-bias replays. All passed with
zero maximum logit/cache difference. These checks use four generated tokens and
the inherited admission's instruction strength 2; the main R20 comparison uses
the separately frozen strength 5. Admission uses no live Jev calls and is not a
quality test or a search for architecture settings.

## Implementation checks and retained failures

The new capability tests were first observed failing for missing evaluator,
runner and audit modules. The capped-output regression initially demonstrated
that a parseable prefix could be accepted at the token limit; it now retains that
outcome as unresolved. Those original failures are retained in execution logs.

The completed local inference environment passed **462 tests in 8.01 seconds**.
The cloud host passed **462 tests in 158.43 seconds** before inference. The eleven
new tests cover identity exclusion, strict Boolean/duplicate-key parsing,
admission failure, packet deduplication, mapping tampering, unresolved score bounds,
native/static execution without provider access and capped judge outputs.

The first core-only CI run had 394 passes, 43 skips and three failures because
three research tests imported the optional Torch runtime without declaring that
dependency. A test-only correction added the existing `importorskip` convention.
A fresh isolated core environment then passed **394 tests with 46 skipped** in
3.78 seconds. Those research tests continue to run in the full environment; the
packet/schema checks also run without Torch. None of the 63 scientific source
hashes, model inputs, thresholds or inference settings changed for this fix.

Scientific inference uses commit `e1249c8`; the optional-dependency test correction
is `00aef20`. The additional blind inspection was registered in `d957d53` before
evaluator admission and main generation. Editorial reports and figures follow
the inference freeze and do not modify it. See the final report for post-run
audits, artifact reconstruction, cleanup and handoff checks.

## Completed reconstruction and handoff

The original R20 scientific auditor passes without amendment. Public unpacking
verifies 25 files and 63,104,571 raw bytes; running the same auditor against those
publicly reconstructed records reproduces every non-timestamp analysis field.
The original 63-file R20 freeze and the 53/55/57-file R19 freezes remain unchanged.
No paid inference was repeated for report generation.

The 49-file guidance check, Ruff lint/format and source/wheel builds pass. Ruff
reports 349 formatted files in this environment. Three actual scientific figures
were rendered and visually inspected. Tables, examples and the citation-only
diagnostic were regenerated from the publicly reconstructed records. Local links
and manuscript anchors were checked. Public candidate files, including decompressed
archives, were scanned against the actual Jev credential and this task's private
cloud resource identifiers, with zero matches.
Whitespace checking passes outside original execution logs and generated SVGs;
their recorded trailing spaces are preserved rather than rewriting evidence.

The full PR inventory against `feat/initial-controller`, the new source and report
diffs, call sites and available review context were inspected. There are no review
threads or submitted reviews at this checkpoint. The automated code reviewer
reports quota exhaustion; it was unavailable, not an approval. CI status is checked
again on the final pushed commit. The PR remains unmerged.

The main unresolved issue is experimental validity, explicitly preserved in the
[blind review](blind-review.md) and [transfer diagnostics](transfer-diagnostics.md).
The constructed evaluator admission passed, but real-answer completeness errors
and reference/answerability problems prevent a verified semantic-improvement claim.
