# R32a single-question transfer admission — conditional v1

Written before inspecting R31 held-out quality. Execute only after R31 completes,
its independent audit passes, owned resources are deleted and cost is reconciled.
A committed source/input/checkpoint freeze activates this protocol. Until then it
is a conditional admission plan, not a running study.

Use all twelve previously exposed MuSR questions; no fresh test question is
generated. Use both R31 scalar-trained memory types (contextual and matched
embedding), both seeds 3101/3102, and each condition's original development-selected
epoch. This choice follows R30's scalar evidence, not a search across R31 test
winners. No MuSR training, prompt search, checkpoint search or threshold tuning.
References are available only to a separate post-run evaluator.

Freeze the dataset's [source attribution and license notices](protocols/musr-transfer-v1/NOTICE.md)
with the input bundle, preserving the original card and author repository notice.
The dataset and its raw metadata retain their upstream terms.

For each question generate original Granite, collect one Jev 1.13 judgment, extract
one vector of each memory type from exact original tokens, and generate blind
repair, ordinary text-feedback repair, and live/constant-0.5/scenario-independent-donor
repairs for all four adapters. The text control conveys the same actual scalar
judgment in a new user instruction; its model has no adapter. Keep the exact native
token prefix, declare that its feedback channel changes the repair instruction,
and count its additional prompt tokens. This is 15 original-backbone outputs per
case, 180 total, and 12 Jev
requests. Use the frozen single-question prompt and `musr-exact-selection-v2`
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
outputs, making **204 planned outputs**. No Jev or adapter is attached to the
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
most **$5.25** including compute, storage, API, network and contingency under the
cumulative $175 cap. API maximum is $0.05 at a conservative $0.05 per million input
tokens, with a 65,536-token reservation before each single attempt; retain unknown
charges and stop on ambiguity. A separate expiry must delete/terminate the owned
worker within two hours of launch. No automatic paid replay or second worker.

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
