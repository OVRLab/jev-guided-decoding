# R19 verification record

Before implementation, six capability tests failed because the new modules did not
exist; after implementing the scorer, policy and runtime they all passed. A fresh
split-isolation test then failed because data preparation was not implemented;
it passed after implementation. Finally the map/token/gate/cache audit regression
failed because the new analyzer did not exist; it passed after implementation.
Original test-first logs are retained locally; these failures demonstrate absent
capabilities, not a historical defect in R18.

Initial focused check: nine tests passed, including receipt failure/max charging,
no retry, cancellation drainage, native/cache preservation, attention-map scope,
reference exclusion, fit feature validation and audit rejection of tampering.
Twelve GPU admission comparisons passed against independent native, relevance,
failed-request and instruction-bias replay: maximum full-vocabulary logit and
all-layer cache differences were both 0.0. Admission used canned probabilities
and made no hosted calls. The live study subsequently verified successful joint
relevance/sufficiency receipts from the pinned hosted `jev-1.13.0` service.
The completed 7,312 outcomes now pass the main and corrected supplemental audits,
including the explicitly recorded numerical portability adapter below.

The separately registered static/shuffled supplement adds three focused tests.
Two initial capability tests failed because the supplemental module was absent,
then passed after implementation; a third exercises final-token ownership and
the distinction between local callbacks, logical requests and paid attempts.
At supplement registration, the local suite had 448 passing tests. The pre-inference 445-test suite
also passed on the GPU host; the extra three control tests were run locally.

## Pre-inference server correction

The first GPU-host environment check passed 443 tests and failed one historical
R14 overload-recovery test: its real 60-second wall clock expired on the slower
CPU host. No R19 admission, model download or hosted API request had begun. The
failure log is retained. That test now uses a module-scoped deterministic clock;
an additional regression confirms the production deadline still rejects the exact
limit. Asyncio and model-runtime clocks, scientific source hashes, experiment
limits, prompts, datasets, policies and graders are unchanged. This is a test
portability correction, not a quality-driven protocol amendment.

## Supplemental disk-round-trip correction

The original supplement stopped before generation on its first job: direct Python
equality rejected tuples in runtime `character_ranges` against their JSON list
representation. Re-encoding all 608 test prompts found zero serialized content
differences. The earlier control tests exercised permutation, receipts and the
token runtime, but missed this disk-join boundary.

The [explicit amendment](../../research/sufficiency-controls-canonicalization.md)
preserves v1 source and failed artifacts and registers a separate v2 runner. The
only generation-path change normalizes the live encoding through its original
JSON representation before comparison. A new test first failed because v2 was
absent; it now accepts the round trip and rejects changed IDs, prompt text,
character boundaries and digests. All 449 tests pass locally in 7.26 seconds.
The main 53 source hashes and original 55 supplemental hashes remain unchanged.
The corrected supplement completed all 1,216 outcomes; no main inference or paid
request was repeated. The initial server was deleted automatically after verified
retrieval, so the unchanged controls used one bounded replacement L40S. That host passed all
449 pre-inference tests in 127.18 seconds. Both servers are now verified deleted.


## Numerical reconstruction correction and completed replay

The original offline main audit stopped on exact equality of benefit features.
293/6,096 rows differ only in the last bit of two `log1p` values when reconstructed
on macOS from the Linux run; the maximum difference is 8.881784197001252e-16.
A decision-only reconstruction verified all 6,096 gate decisions unchanged before
any quality inspection. The original [failure log](execution/audit.log) is retained.

The [portability amendment](../../research/benefit-sufficiency-audit-portability.md)
adds a separate adapter, leaving all original scientific source files intact.
Two new tests first failed because the adapter was absent, then passed: one permits
only one adjacent float for the two logarithms and rejects other changes; the
other confirms raw records stay unchanged and original token-tampering rejection
still fires. All 451 current local tests pass in 8.07 seconds.

Both complete audits pass through the adapter: 293 normalized main rows and 54
normalized control rows, with every other comparison retained. They reconstruct
7,312 outcomes and 139,811 final tokens, and verify unchanged model weights,
1,824 conditional branch identities, all attention maps and work, and 1,068
successful hosted receipts with zero provider failures. The failed pre-generation
v1 control start remains separately archived, not erased or graded as an answer.

Public archive reconstruction reproduces every non-timestamp field of both analyses;
see [verification](public-replay-verification.json). No quality grades, generated
tokens, dataset records, decisions or scientific settings were edited. Four scientific
figure layouts were inspected in their actual PNG renders. Individual-answer review
identified material parser/lexical artifacts, prominently discussed in the report;
mechanical audit success does not resolve those semantic measurement limitations.

Two stale lock files survived in the local rolling backup after disappearing from
the first server. Replacement transfer admission rejected those extra files, while
all 12 recorded main artifacts matched. Only the uploaded stale copies were removed
after matching their local hashes; the recorded artifacts were untouched. The
replacement then verified all 608 prompt bindings and absence of a Jev key.

## Editorial and repository verification

The completed report passes the 49-file AI guidance checker, Ruff lint and format
(327 Python files), and source/wheel builds. The current local suite has 451 passing
tests; the later edits change reporting and labels, not inference or frozen graders.
All four final PNG layouts were inspected after the parser labels were clarified.
All 53/55/57 scientific source hashes, 28 raw/stored artifact hashes, analysis/cohort
bindings and portable-adapter source hashes match their saved records.

Public-content review scanned 921 files, including 89 decompressed gzip archives,
with zero matches for the actual Jev credential and private identifiers from both
cloud episodes. All 886 local links across the PR's 111 Markdown files resolve,
including inspected heading anchors. No blob exceeds GitHub's 100 MB file limit.
The full PR inventory against `feat/initial-controller` contains 868 changed files,
mostly accumulated research records; the new code/report diff and original audit
callers were reviewed with earlier implementation reviews retained. There are no
review threads or submitted reviews. The automated review bot reports exhausted
code-review quota and remains unavailable; this is not review approval.
The staged whitespace check flags only Matplotlib SVG paths and the preserved
failed-bootstrap log; those generated/verbatim bytes remain intact. Authored source,
prose and all other staged files pass the whitespace check.
