# R13: API recovery and controlled inference study

Status: API recovery succeeded; the first GPU pilot failed final formatting.
The [V2 common final-label correction](../../research/structured-study-v2-protocol.md)
is registered before another pilot. No R13 test outcomes exist at this report's
initial commit. Original Granite weights and all historical negative results are
preserved. This report will append subsequent execution evidence.

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
