# R27: repaired evaluation runtime and prospective benchmark execution

Recorded 2026-09-24 before new inference. This follows the failed, immutable
[R26-A admission](../reports/2026-09-24-selective-admission/README.md) and the
[ten-task contract](benchmark-suite-contract-v1.md). The owner authorized execution
and a **$110 cumulative cap**; recorded spend entering this stage is
$46.17349123025742. All cloud/API attempts count, including failures.

## Execution sequence

1. Add a separate `research/iterations/benchmark_execution_v2` runner, leaving
   every R26 source, input, output and primary score unchanged. Observe regression
   tests failing before implementing the changes.
2. Integrate the already tested choice-readout v2. Keep answer extraction separate
   from reference comparison. Test valid, conflicting, malformed and empty outputs.
3. Run serial native generation to eliminate finished-row padding. For choice and
   numeric tasks only, stop after a complete newline-terminated `Final: LETTER` or
   `#### NUMBER` line, outside a thinking block. Preserve exact generated tokens;
   never synthesize a label or stop on partial numbers/letters. Original instruction
   tasks retain their exact prompts and EOS/length stopping. No repetition penalty,
   answer grammar, forced label, shortened thinking allowance or changed weights.
4. Validate this behavior, cache equivalence, zero gates, immutable base weights,
   deadlines and source/token provenance offline and on an exposed-only GPU pilot.
   Pilot selection is deterministic from the existing R26 cohort, at most 18 cases
   and **$5 total** including setup/cleanup. Pilot quality cannot select adapters,
   thresholds or architectures. Runtime/format diagnostics may correct engineering.
5. Download GPQA privately using the accepted gate, inspect schema/count and official
   protocol, then freeze its dataset hash, deterministic option shuffle, independent
   readout and exact sources before any fresh generation. Do not publish questions,
   options or answer-bearing traces. The runtime never reads reference files.
6. After measured throughput and evaluator admission, execute full GPQA Diamond,
   then full IFBench and MuSR if affordable. Assess the other seven tasks against
   their contracts and remaining funds; run admitted affordable tasks. Keep every
   missing or partial task visible. Full ten-task completion is not promised by a
   small pilot or by this authorization.

## Frozen comparisons and interpretation

Retain R26 model revisions, native chat templates, numerical types and sampling
profiles: Granite 4.0-1B FP32 greedy/2,048 tokens, Granite 4.2-3B BF16 thinking/
8,192 tokens, Qwen3-4B-Instruct-2507 BF16/16,384 tokens. Declare per-case seeds,
serial execution and terminal-line stopping as this new resource contract.
Choice/numeric prompts explicitly request the terminal line and stopping; these
instructions apply identically across compared models. Instruction prompts remain
unaltered. Never silently truncate an oversized prompt.

Reuse R25's selected live seed-2501 epoch-2 and constant epoch-1 adapters, frozen
after zero-indexed block 19. Jev 1.13.0 judges the native draft; p(correct)<0.5
triggers a fresh-cache repair, gate=1-p. Missing feedback retains the native draft
and remains an API failure. Include live, routed blind, matched constant,
live-checkpoint constant-strength, inverted and within-task shuffled-strength arms.
These six share Jev routing; report that explicitly. Also run **Granite-only
self-refinement on every case**, without a Jev call or adapter. It controls for an
extra inference pass and is not compute-matched when selective arms skip work.
All final answer tokens belong to Granite; original weights remain unchanged.

Use choice readout v2 / existing numeric readout and independently pinned IFBench
strict/loose evaluators. Unparseable/unfinished answers count as incorrect in the
declared denominator. Runner admission requires correct extraction and provenance,
not a favorable model accuracy or an arbitrary minimum formatting success rate.
R26's failed 38/40 gate remains its historical result; this prospective change
prevents excluding weak but validly measured models from comparison.

Primary result is paired live-minus-original accuracy for each completed task;
report paired differences against all controls and both larger models, confidence
intervals, wins/losses, failures and actual cost. Architecture is frozen before
fresh grades. No selecting a better checkpoint, threshold or prompt using test
answers. Descriptive results do not establish broad superiority or a ten-task mean.
Any confirmatory claim requires a separate multiplicity/replication contract.

## Verification and operational safeguards

Test the least-initialized baseline without credentials or inference imports in
core; stop before first forward on an expired deadline; remove hooks on failure;
reject invalid limits/inputs and unregistered resume. Record per-request real
tokens, prefill and decode slots, latency, finish reasons, sampled seed and selected
token hashes. Validate task/reference bindings only in the independent evaluator.
Run the repository's docs, Ruff, pytest and build checks before dispatch.

Before each paid stage, freeze source/data/checkpoint hashes, exact case list,
budget/time ceiling and immutable revisions. Restrict SSH to the current operator,
transfer keys privately, keep fresh references off the inference worker, back up
results regularly, verify final hashes and delete all owned resources. Use a VM
expiry independent of local supervision. Private GPQA artifacts stay private;
public evidence contains metadata, hashes, aggregate grades and reproducible code.
Update the notebook, study register, feasibility, results and manuscript with both
positive and negative evidence and a reconciled cumulative cost.
