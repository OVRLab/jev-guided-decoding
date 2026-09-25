# R28: repair selection versus internal feedback

Status: **running**, launched 25 September 2026 at 17:46 UTC. This is an execution
record, not a completed result. Quality scoring waits for complete generation and
independent integrity admission. The source worker and scientific decisions remain
frozen while publication helpers and documentation are prepared separately.

## Question and registered comparison

Does Jev help by choosing which answers Granite revises, by supplying useful scalar
feedback inside its repair adapter, or both? Every final answer token is generated
by Granite. The fixed rank-64 adapter acts after decoder block 19 during a second
pass; Jev is called once after each native answer, not per layer or token.

The [prospective protocol](../../research/routing-feedback-plan-v1.md) registers
539 eligible IFEval cases, two fixed blocks, and 269 repairs per selective policy.
Seven policies use fresh shared potential outcomes: original Granite, always
constant repair, Jev/constant, confidence/constant, random/constant, Jev/live and
Jev/shuffled. The planned collection has **1,616 generated answers and 539 Jev
judgments**. Reused outcomes do not count as independent problems or as separately
measured deployments. Selection controls avoid Jev at inference but share an
adapter previously trained using Jev judgments.

Four primary paired comparisons use 98.75% intervals, a two-percentage-point
practical threshold and consistency across both blocks. Equal repair counts do
not imply equal token costs. No larger-model or ten-benchmark victory can be
established by this instruction-following attribution study.

## Admission and provenance

- Frozen worker source: `c418df6`; original Granite revision and checkpoint hashes
  are bound by the [public manifest](../../research/protocols/routing-feedback-v1/manifest.json).
- Google Research IFEval commit `e6890f85757dd84e27ca6df2dd30651dafad28e0` supplies
  541 original cases; checker keys 1122 and 1129 were excluded before inference
  because punctuation causes the upstream letter checker to substitute a random
  letter. The eligible denominator is 539, not the official full 541-case score.
- Admission found no exact or five-word-shingle near overlap with 2,040 distinct
  prior project prompts. This does not establish pretraining cleanliness.
- All 48 upstream checker tests and 12 constructed strict pass/fail/empty checks
  pass. The grader and constraint metadata remain outside the inference worker.
- The worker passed eight new mechanism/audit tests on CUDA. The combined local
  suite now passes 652 tests; the worker commit passed four GitHub CI jobs.
- Reacquisition from pinned public sources reproduced every case, reference and
  adapter hash. A synthetic grade/export/replay integration passed separately.
- A single Jev preflight returned the pinned model version with accounted usage.
  It is operational admission, not a benchmark accuracy result.

## Operations and spending

One AWS `g6.xlarge` with an NVIDIA L4 is running in Frankfurt at the verified
on-demand compute rate of $1.0064/hour. Incremental output backups run each minute
and cloud health checks every 15 minutes. Independent instance expiry is set to
12 hours; the worker has an 11-hour deadline. A final exact inventory/hash backup
precedes deletion of the owned instance, disk, security group and temporary subnet.
This record will only claim cleanup after those deletions are verified.

The user authorized a **$125 cumulative ceiling**. Prior conservative spending was
$103.82976781335556. The new operational reservation is $16.6468, including compute,
disk, API, public IP, network and contingency allowances, plus a $0.000015204
preflight. This is a conservative planning estimate, not an invoice; final usage,
taxes and network charges remain unconfirmed. No second worker or new training
sweep is part of this study.

## Results and publication package

**Pending.** No R28 quality grades have been inspected. Generation completion,
independent audit, original strict/loose grading and numerical replay will precede
the result table and interpretation. A provider failure, missing output or deadline
will remain an incomplete study instead of reducing the denominator silently.

The [focused manuscript](../../research/manuscript.md),
[related-work review](../../research/routing-feedback-related-work.md) and
[reproduction guide](../../research/routing-feedback-reproduction.md) are prepared.
The earlier [R27 completed-Granite report](../2026-09-25-completed-granite/README.md)
remains the source for historical scores. No paper submission, model release,
publication acceptance or achievement of the broader north star is asserted.
