# R29-A admission record before GPU inference

2026-09-26, source `71bf964`, manifest
`025db0b26b7c3c6223ab4e66bd0aaf092f1b05be4286069872e87e2f97fd26cc`.
The [protocol](structured-correction-plan-v1.md) and all inference/training code
were committed before these checks. No test-set Granite outputs were generated.

- All 661 repository tests, lint, formatting, documentation checks and build pass.
- Actual Granite FP32 on local MPS passes initial and trained-off identity, frozen
  backbone gradients, nonzero adapter gradients, and cache/full agreement:
  maximum logit difference 0.0000748634, identical argmax. New branch: 262,144
  parameters. This is a mechanical check, not an answer-quality result.
- Six constructed Jev fixtures use three training worlds and one deliberately
  wrong answer per world. All six single requests succeed with model 1.13.0;
  5,064 input tokens cost a conservative $0.0002532 at $0.05/million.
- Fixture judgment accuracy is 16/18 slots, with exact three-slot correctness on
  4/6 requests. The private fixture script's all-correct `passed` flag is **false**.
  In both variants of the compositional world, Jev incorrectly rejects a correct
  third answer: after the coin moves into the red crate, its room is garage.
  The answer is independently confirmed by replaying the text's location graph.

Decision before GPU allocation: continue the registered experiment with **unchanged
feedback questions and data**, treating Jev as fallible. The protocol requires
operational/API checks but did not set an all-slots-correct verifier threshold.
This decision does not convert the failed fixture-quality flag into success.
The separate oracle-trained/oracle-feedback condition measures whether accurate
localized signals can help the repair branch. No prompt was tuned on these fixtures;
the subsequent native-draft judgments remain distinct from constructed admission.

The live AWS price query gives $1.0064/hour for one g6.xlarge in Frankfurt. The
five-hour maximum, disk, API, IPv4, egress and contingency reserve totals $8.412,
within the registered $8.50 allocation and cumulative $125 cap. GPU allocation
and study completion are not implied by this admission record.
