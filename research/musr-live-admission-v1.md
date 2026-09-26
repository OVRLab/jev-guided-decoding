# R32a single-question transfer admission — conditional v1

Initially written before inspecting R31 held-out quality; the separately recorded
constant-control amendment below follows completed R31 evidence. Execute only after R31 completes,
its independent audit passes, owned resources are deleted and cost is reconciled.
A committed source/input/checkpoint freeze activates this protocol. Until then it
is a conditional admission plan, not a running study.

Use all twelve previously exposed MuSR questions; no fresh test question is
generated. Use both R31 scalar-trained memory types (contextual and matched
embedding), both seeds 3101/3102, and each condition's original development-selected
epoch. This choice follows R30's scalar evidence, not a search across R31 test
winners. Additionally include both independently constant-trained memory types and
both seeds, using their original development-selected epochs. This addition follows
the completed R31 result, not MuSR quality. No MuSR training, prompt search,
checkpoint search or threshold tuning.
References are available only to a separate post-run evaluator.

Freeze the dataset's [source attribution and license notices](protocols/musr-transfer-v1/NOTICE.md)
with the input bundle, preserving the original card and author repository notice.
The dataset and its raw metadata retain their upstream terms.

For each question generate original Granite, collect one Jev 1.13 judgment, extract
one vector of each memory type from exact original tokens, and generate blind
repair, ordinary text-feedback repair, and live/constant-0.5/scenario-independent-donor
repairs for the four scalar-trained adapters. The four constant-trained adapters
each receive only their training-matched 0.5 signal, not live/donor transformations. The text control conveys the same actual scalar
judgment in a new user instruction; its model has no adapter. Keep the exact native
token prefix, declare that its feedback channel changes the repair instruction,
and count its additional prompt tokens. This is 19 original-backbone outputs per
case, 228 total, and 12 Jev requests. Use the frozen single-question prompt and `musr-exact-selection-v2`
parser, FP32, greedy decoding, 1,024 new tokens and 4,096 total-context ceiling.
No truncation or constrained grammar. Granite owns every final token. A missing
selection has no draft-span memory and is explicitly marked missing to Jev.

Then unload the original model and run pinned original Granite 4.2-3B once per
case in each supported mode: non-thinking (2,048 tokens) and thinking (8,192).
Use BF16, SDPA, temperature 1.0, top-p 0.95, explicit top-k 50, 16,384 context
ceiling and deterministic per-case/profile seeds from SHA-256 of
`3200/{profile}/{case_id}`, first eight bytes modulo 2^63. Preserve its own chat
template and require closed thinking before scoring. Its limits, precision and
sampling differ from the small generator and must be reported. This adds 24
outputs, making **252 planned outputs**. No Jev or adapter is attached to the
larger comparator; Jev's undisclosed size still belongs to combined-system claims.

Require actual CUDA initial/off identity and nonzero cached/full agreement for
the single-memory branch using the first exposed saved native draft. FP32 maximum
absolute cache error must be ≤0.001 and argmax equal. Separately check the actual
larger model's cached/full next-token logits before its first generation; BF16
tolerance is 0.25 with equal argmax. Report measured error and dtype, rather than
claiming exact floating-point equivalence. Check original and adapter hashes
before/after, clean hooks, no original gradients and complete raw coverage.

The single worker has a 5,400-second generation deadline across both model phases;
model load/download time is separately bounded by service/host expiry. Reserve at
most **$5.50** including compute, storage, API, network and contingency under the
cumulative $175 cap. API maximum is $0.05 at a conservative $0.05 per million input
tokens, with a 65,536-token reservation before each single attempt; retain unknown
charges and stop on ambiguity. A separate host expiry stops execution within two
hours of launch. The monitor verifies the final backup before deleting owned
resources; an incomplete deadline stop retains recovery evidence for verified
cleanup. The envelope allows another fifteen minutes of conservative compute
accounting for resource closure. No
automatic paid replay or second worker.

Report all exposed-case results, including failures, readability, length stops,
feedback discrimination, actual tokens/latency and fix/damage counts. Accuracy is
descriptive development evidence, not a public benchmark win. No significance
test on twelve cases determines a winner. The next fresh-case protocol must be
frozen separately, using measured throughput to choose an affordable complete
matrix before fresh labels/outputs are inspected. A failure preserves evidence,
cost and cleanup; it does not silently license modified reruns.

Pre-freeze amendment: the text-feedback control was added while R31 held-out
generation was running and before inspecting its quality. It tests the added
value of an internal channel against an ordinary way to give Granite the same
judgment. It adds twelve generations and no provider requests within the unchanged
stage envelope. The running R31 protocol and comparisons are unaffected.


Result-informed pre-freeze amendment after R31, 26 September 2026: R31's scalar
conditions score 46.29% and contextual constant-trained repair 47.85%, with different
fix/damage counts. Preserve both originally proposed scalar conditions and add the
four independently constant-trained checkpoints as strong Jev-free controls. This
adds 48 generations, zero provider requests and no retraining. The resulting matrix
has 252 outputs and 12 requests on the same twelve exposed cases. The source/manifest
freeze has not yet occurred and no R32 instance has been launched. These are
result-informed control additions, not changes to R31's protocol or comparisons.

The stage reserve rises from $5.25 to $5.50 before launch to include fifteen minutes of
conservative shutdown/deletion accounting beyond the two-hour execution ceiling;
R31 graceful termination took several minutes after its verified backup. The
cumulative $175 cap is unchanged, with R31 closed at $129.42416324505962. The worker's
5400-second limit and the two-hour independent host expiry remain unchanged.

Implementation/verification plan: update the checkpoint contract, serial arm
coverage, independent record auditor, combined worker counts and development
summary. First reproduce failures for missing constant-trained checkpoints,
incorrect arm coverage, changed constant feedback and incomplete combined counts.
Then verify constant-trained arms use exactly 0.5, retain exact native tokens and
unchanged weights, and cause no extra provider dispatch. Carry both seeds through
summary aggregation. Re-run all MuSR flow tests and canonical checks before a new
committed source/input freeze. No R31 frozen source or artifact may change.
