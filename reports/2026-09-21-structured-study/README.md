# R13: API recovery and controlled inference study

Status: the V2 test stopped after 3,015 completed jobs and one provider failure.
A bounded continuation is registered for the 3,284 never-started jobs; the failed
job remains incorrect. Accuracy improvement is unproven.
The first GPU pilot failed final formatting and is retained below. Original
Granite weights and all historical negative results are preserved. No test
outcomes existed at this report's initial commit; subsequent stages are appended.

## API recovery

Both frozen diagnostic requests succeeded with Jev 1.13.0: fresh authentication
and the exact previously failing request shape. Total 1,910 input tokens. This
verifies current access, not the unrecoverable cause of R12's HTTP 400. The old
unknown request is still actual-usage unknown and carried at its full reserved
65,536-token charge. Error handling now retains bounded, credential-redacted
response diagnostics. See the [recovery manifest](../../research/protocols/recovery-v1/api.json).

## V1 GPU pilot: failed operational admission

Source `4daa94e`, manifest/data freeze `98628a6`, original model revision
`6a7381ba1f54d684ff508d991aeb7dc580157103`. One NVIDIA L40S, BF16,
Torch 2.8.0 / Transformers 4.57.1 / Python 3.12.13. All 291 offline tests also
passed on that server. Its Jev key was copied privately with mode 600 and never
logged. The following 192 authenticated calls verify that the server used it.

| Arm | Complete | Valid final format | Independently correct |
| --- | ---: | ---: | ---: |
| Direct native | 24 | 23 | 9 |
| Staged native | 24 | 16 | 5 |
| Likelihood | 24 | 18 | 5 |
| Jev token | 24 | 16 | 5 |
| Shuffled | 24 | 16 | 5 |
| Zero bias | 24 | 16 | 5 |
| Soft step | 24 | 16 | 5 |

All 168 jobs ran in 243.53 seconds excluding model loading/warm-up. No provider or
backend errors occurred; 270,264 input / 29,952 output tokens were received from
192 Jev calls, $0.011351088 input list price. All 960 branch claims were graded,
all 240 possible checkpoints were reached, and all 168 token/prompt audits passed.
An independent local token reconstruction also certified 168/168. Staged/zero
token paths matched 24/24, and the weight digest before/after was
`311c1141187580dc0905c810e9d9e78853a0bf37b865bd5a5a511f6eed72f8c9`.

The format gate failed: 121/168 valid final responses. Granite sometimes generated
an empty EOS or an explanation rather than the requested label. The study correctly
stopped before test admission. These development accuracy figures do not establish
a benefit or a population comparison; the invalid answers remain incorrect.

The [V1 protocol](../../research/structured-study-protocol.md),
[V1 manifest](../../research/protocols/structured-v1/manifest.json),
[raw compressed attempts](pilot-v1/runs.jsonl.gz), [summary](pilot-v1/summary.json),
[independent analysis](pilot-v1/independent-analysis.json), and
[artifact hashes](artifact-hashes.json) preserve this attempt. All fixtures are
authored rule worlds; no claim of general math improvement is supported.

## V2 GPU pilot: passed operational admission

Source `b6ca4cb`, freeze `97fc05c`. The same development worlds were rerun after the
prospectively recorded [shared final-label grammar change](../../research/structured-study-v2-protocol.md).
Test data hashes are unchanged and no test outcome informed that correction.
All 295 offline tests passed locally and on the GPU server before V2 inference.

All 168 jobs completed with valid Granite-generated labels; 960/960 candidate
claims were independently gradable, 240/240 checkpoints were reached, 168/168
online token/prompt audits passed, and staged/zero paths matched 24/24 pairs.
Independent local token reconstruction also passed 168/168, including the final
constrained token loop; initial proposal pools matched all 96 paired comparisons.
Formatting is enforced by the shared grammar and is not learned instruction-following.

Pilot accuracy was 11/24 direct Granite, 8/24 staged, 7/24 likelihood and 8/24 in
each Jev/shuffled/zero/soft-step arm. This development pilot demonstrates operational
readiness, not an accuracy gain. In the Jev arm's 36 mixed-quality candidate sets,
Jev's highest-support proposal was independently correct in 36, versus 27 for
highest likelihood. This descriptive critic ranking is distinct from the bounded
stochastic token policy and its final-answer quality.

Elapsed pilot time was 244.39 seconds excluding loading/warm-up. All 192 Jev calls
succeeded: 270,264 input / 29,952 output tokens ($0.011351088 input list price).
The original cumulative ledger remains in use. The measured runtime plus the
prespecified margin admitted the full 6,300-job, 300-world, three-seed test.
No test outcome will change its method or trigger accuracy-based early stopping.

[Raw attempts](pilot-v2/runs.jsonl.gz), [summary](pilot-v2/summary.json),
[independent analysis](pilot-v2/independent-analysis.json),
[manifest](../../research/protocols/structured-v2/manifest.json).

The [figure renderer](../../experiments/plot_structured_study.py) is prepared for
the completed independent summary. It exports accuracy/latency and the three
primary contrast intervals as PNG, SVG and PDF, recording source/data hashes and
plotting-library versions. Figures require all 6,300 outcomes and will receive
visual/table verification after the run; no invented preview data is used.

During main execution, the offline auditor was strengthened to bind each recorded
question, evidence, system instruction and exact chat-template prompt tokens to
the frozen case. The new regression first failed because that independent check
was absent, then passed while rejecting altered inputs under an unchanged case ID.
All 168 V2 pilot prompts also passed this additional reconstruction. This changes
offline verification only; the frozen GPU inference code and protocol are unchanged.

## V2 service interruption and registered continuation

The original test stopped at attempt 3,016. Its last soft-step request followed
the HTTP 429/529 exhaustion branch, which lost the exact status/body and wrongly
labeled usage known. The ledger nevertheless retained the full 65,536-token
reservation. That client diagnostic defect is now regression-tested and fixed;
the lost status is not recoverable. All 19 remote result files matched the local
backup, and the first VM, disk and task network resources were deleted. Granite
weights remained unchanged. [All stopped attempts](stopped-v2/runs.jsonl.gz),
[stopped summary](stopped-v2/summary.json) and [completion record](stopped-v2/completion.json)
are preserved, including the original error fields.

The [prospective continuation](../../research/structured-study-continuation.md)
excludes every started key, preserves the 6,300-job denominator, and changes only
operational recovery and error diagnostics. Successful inference policy is fixed.
The unknown request was carried at its full maximum under the existing owner
authorization; it was not replayed or settled at zero. One [new service probe](continuation-api-recovery.json)
succeeded. A new L40S will execute only the 3,284 remaining jobs, with at most three
bounded cooldowns after explicit rate-limit/overload failures; each failed job
stays failed. Other service/backend failures stop the continuation. The original
$50 cumulative allowance remains in force.
