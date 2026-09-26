# R25 completion and verification record

Final reporting edits consolidate completed results without changing frozen source,
protocols, raw model evidence or primary grades. Validation covers metric agreement,
local documentation links, artifact hashes, replay, secret exclusion, visual figure
inspection, package checks and the actual PR diff/review context. This is a reporting
plan and record, not a new paid experiment.

## Execution and provenance

V4 completes with exit code zero. All 57 final files are retrieved and byte-checked
before deleting the owned VM/disk/network resources. The archive contains 12 adapter
checkpoints and predecessor evidence. The worker's source is `640987e`; freeze is
`6bade56`. The final original-weight hash matches its admitted starting value.
All figures derive from frozen audit JSON, and their PNG versions were visually
inspected for readable labels, intervals and disclosure. SVG/PDF versions are
included for publication editing.

An early report-only delivery check accidentally called the predecessor verifier
through helper alias `C`, rejecting v4 with `Continuation source/settings mismatch`.
The caller was corrected to the v4 common verifier used by the frozen primary
analyzer. No scientific source changed and no inference or paid request was repeated.
The final primary/training/delivery audits supersede those preliminary checks.

The worker clock was approximately 40 seconds behind the workstation. Cross-host
wall-clock ordering is approximate; checkpoint selection/test ordering is verified
within worker records. Monotonic model durations, rather than backup timestamps,
are used for per-arm work. Cleanup timestamps use the workstation UTC clock.

## Reproduction

[Public replay](public-replay.json) reconstructs all four principal analyses exactly,
including tokenizer prefixes, charges, training order and selected checkpoints.
The separate [feedback replay](feedback-replay.json) also matches. Replay adds no
GPU inference or provider charge and is not independent replication.

[Source-data verification](data-audit.json) checks upstream questions, labels,
training targets and exact overlap independently of the data-preparation helper.
See [method commands](method.md). The post-hoc [output inspection](output-inspection.json)
retains complete transitions without regrading. Its original report-only script is
archived verbatim as [inspection source](inspection-source.py.txt); copy it to a
`.py` file and run from the repository root after extracting the public replay to
`results/r25-public-replay` to reproduce its JSON, including its source hash.
It writes only that inspection artifact; no model/API call occurs.

The primary analysis SHA256 is
`ece56a062723fb003973725e9b38949a00f033f2bca4515819c2a02279934c2d`.
The raw archive index SHA256 is
`a7ff23d4462e75bf3eaa2a82c1d5b02df0e6d4f4c49a412b36dc8876fc281302`.
All source and raw bindings remain available in the manifests and archive index.

## Engineering checks and scope

The frozen cloud worker passed 536 tests in 16.99 seconds. Additional read-only
source/replay/feedback helpers had ten failing tests before implementation and
bring the local suite to 546 passing tests (10.62 seconds). Ruff, formatting,
package build and the 49-file guidance check passed. Final reporting changes use
link/metric/hash and visual validation; they do not rerun paid model experiments.

No PR merge, package publication or Hugging Face release occurs. The working
manuscript is not peer reviewed; the automated reviewer reported its review quota
exhausted, which is not approval. The unexecuted larger-model outline remains
gated off by the primary result. All historical negative results stay available.


Final reporting verification scans 90 new/changed files, including decompressed
archives, for the actual Jev credential and encoded forms, private-key/token
patterns and local user paths: no matches. All 57 raw/archive hash pairs match;
more than 400 local Markdown links resolve. The inspection script and primary-analysis
hashes match their recorded bindings. All three figures were visually checked.
The final local Ruff/format checks pass (473 files), package build passes, the
49-file guidance checker passes, and `git diff --check` is clean. Frozen scientific
files were not changed by this reporting commit.
