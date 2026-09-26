# R30 fresh feedback-pairing replication

**Running, 2026-09-26.** The worker started at 2026-09-26T11:00:24.557086+00:00; no R30 quality result
is available yet. [Protocol](../../research/feedback-pairing-plan-v1.md) and
[program](../../research/feedback-exploration-program.md) were recorded before
inference. This is an authored mechanism replication, not a public benchmark.

384 fresh worlds; fixed selected R29 structured/scalar checkpoints; two training
seeds; 20 generation conditions per world. Planned denominator: 7,680 outputs and
384 Jev requests. Primary contrasts isolate native gain, repeated-mean feedback
and within-draft score permutations. Other controls include donor feedback,
constant scores, answer-type checking, blind repair and nondeployable oracle flags.

Source: `d2ed7b898a044d75bc672ab20aa3c2a125ac23a0`. Frozen input manifest SHA256:
`793153d5b963a4265296ce6fd351dbd973763a62bd049acc636d66f59f8466f9`.
All 670 local tests, all four source CI jobs and 18 server tests pass. A separately
labeled artificial-record test exercises all 7,680 audit records and rejection
paths; none of its scores is a model result. Real-model admission runs before the
first paid Jev request. Original and adapter weights remain frozen.

One AWS L4 at freshly checked $1.0064/hour; maximum five-hour instance life,
4.5-hour worker limit, $8.412 reserved. The user-authorized cumulative ceiling is
$175, starting from the previous $118.12281183983264 conservative estimate.
The private monitor backs up every minute and checks cloud health every 15 minutes;
a separate host timer stops the instance at 15:53:51 UTC. Completion requires
independent token/feedback/weight/coverage audit and verified backup before deletion.
No cleanup completion, final spend or quality score is asserted in this running note.
