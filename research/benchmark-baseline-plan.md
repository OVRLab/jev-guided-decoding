# R23: public cross-domain baseline diagnostic

Registered before inference, 2026-09-23. Implements stage 1/2 of the
[north star](north-star.md), not a new Granite–Jev architecture or final scorecard.

## Question and scope

Where does the immutable Granite 4.0-1B generator fail on public tasks, and what
headroom does a newer Granite 4.2-3B generator show on the identical questions?
Build a versioned ten-task contract and a credential-free generation/independent
scoring path. Keep the previous experiments' frozen sources untouched.

Use 76 development problems, selected by SHA256 ordering of `r23/<task>/<id>`:
28 MMLU-Pro validation (two per subject), 24 GSM8K main training (auxiliary math
rather than consuming the tiny AIME final exam), 12 MuSR (four per family), and
12 IFBench. MuSR/IFBench have no supplied development split; selected source-test
IDs are explicitly consumed as project development and excluded from a future
untouched holdout. A full-source score including them would be exploratory.
No selected cases are training data for this run. No reference answers or
verifier metadata enter model requests. Freeze normalized cases and separate
references, upstream revisions/file digests, code and settings before inference.

This is a small zero-shot diagnostic, **not official benchmark scores**, a
representative estimate of the whole ten-task suite, a larger-model victory, or
evidence of Jev benefit. MMLU-Pro uses our explicit final-answer format rather
than its official five-shot protocol. GSM8K is outside the ten-task scorecard.

## Generation contract

Native chat templates; one independent generation per problem and model, full
vocabulary, no hooks, no forced UNKNOWN, no tools, no retries chosen by quality.
Original 4.0-1B revision `6a7381ba1f54d684ff508d991aeb7dc580157103`:
greedy, 2,048 new tokens. 4.2-3B revision
`e459acceac81e5fe67c07d9cfc72329a332e7eb1`: native thinking enabled, temperature
1.0/top-p 0.95 as supplied in its generation config, 8,192 new tokens. Seed 2301
reset before each problem. Both BF16/SDPA on one L40S, unquantized frozen weights,
Transformers 4.57.1/PyTorch 2.8.0. Different generation budgets are explicit;
this is a first native-profile diagnostic, not matched-compute or best-quality
certification. Record truncation, exact prompt/generated IDs, raw output,
reasoning closure, actual token counts, time, memory, model/dataset/source hashes.
Input limit 16,384 tokens; never silently truncate. Oversize/errors/missing runs
stay in planned denominators with status. For thinking output, grade only the
text after the final `</think>`; unfinished thinking is incomplete, not an answer.
A failure to load a model is recorded, never replaced with a different model.

## Independent scoring and failure map

MMLU-Pro/MuSR: last explicit `Final: <letter>` or `The answer is (<letter>)`;
otherwise a standalone letter; ambiguous or absent decisions are unparseable.
GSM8K: final `#### <number>` or `Final: <number>`, decimal numeric equality,
no reward for a number that appears only inside reasoning. IFBench: pinned
upstream strict and loose prompt-level verifiers, separately report both; no
rewritten checker or semantic quality claim. IFBench paper reports loose, while
our north-star working proposal requested strict: preserve both before selection.
Responses and grades are bound by case ID **and** prompt hash. Grade after inference.

Report correct/incorrect/unparseable/truncated/incomplete/operational outcomes,
by task/family, with paired native/3B differences and exploratory problem-bootstrap
95% intervals. No superiority hypothesis test on 12 examples. Failure categories
are observed behavior; a wrong multiple-choice answer alone does not prove a
knowledge gap rather than reasoning failure. Manually inspect a fixed sample of
errors, separately labeled qualitative evidence. No Jev calls: baseline quality
and evaluator integrity come before selecting a feedback mechanism.

## Implementation and validation

New files only under `research/iterations/benchmark_baseline`, protocol directory,
`tests/test_benchmark_baseline.py`, plan/contract/report and notebook links.
Capability tests first: missing module, leakage rejection, strict extraction,
unfinished reasoning, ID/prompt binding, source tampering, missing denominator,
exact EOS trimming, bounded settings. Use tiny offline doubles; no live services
in tests. Verify upstream IFBench evaluator on simple pass/fail fixtures before
launch. Freeze and commit before inference. Independent audit reconstructs
prompts, token decoding, grades and complete planned coverage from archives.
Run full existing suite, documentation checker, lint/format and build.

## Cost and stop conditions

Prior estimated cumulative use $33.76145561903811 of $50. Reserve at most $7.10
for this stage, including up to four hours L40S+80GiB disk at the last quoted
$1.75458082/h; verify current price/capacity first. Worker cap three hours, VM
expiry four hours. Copy artifacts during execution; stop/delete VM, disk and
owned security rules after backup, verify deletion, record actual metered-time
estimate. No provider inference fees or Jev credentials needed. No automatic
extension, no more expensive hardware substitution. Incomplete run remains
incomplete; any continuation gets a separately recorded decision and budget.
