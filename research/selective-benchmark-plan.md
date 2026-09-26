# R26: selective internal repair across public benchmarks

Recorded 2026-09-24, after the completed R25 results and the owner's explicit request
to proceed with top benchmarks and original/larger-model comparisons. This is a
new prospective study, not execution of the earlier gated always-repair outline.
The owner now asks to evaluate the selective finding. R25's negative primary
result, failed spending gate and unexecuted outline remain unchanged.

## Objective and decisions before new inference

Test whether R25's selective science improvement transfers to fresh instances and
other benchmark domains, and compare identical problems with original Granite,
newer Granite 4.2-3B and Qwen3-4B-Instruct-2507. Keep all final answers generator
owned. No retraining, threshold tuning, seed selection or grader changes based on
new test outcomes. Use seed 2501, already prospectively fixed in the earlier
outline, and its R25 dev-selected live/constant checkpoints. Jev remains 1.13.0.

The new runtime actually skips a repair when Jev p(correct) >= .5 or unavailable.
When called, the trained branch after block 19 receives g=1-p(correct). The full
original draft token IDs enter a fresh repair cache unchanged. Original weights
remain frozen; no vocabulary restriction or fixed UNKNOWN is imposed.

Task-specific instructions replace R25's mixed math/choice repair instruction.
Remove literal angle-bracket placeholders in native numeric/choice prompts. Pin
independent extraction and grader behavior before test. Use separate exposed
development cases to admit formatting and numerical/cache behavior, never to
choose a new test checkpoint. Any development failure and resulting protocol
revision must be preserved before generating fresh test outcomes.

## Comparisons and attribution

Every case has original Granite, selective live repair, selective blind repair,
selective matched-constant repair, and same-live-weights constant-strength and
inverted-feedback controls. Routing is identical for the selective controls and
uses Jev, so they are not wholly Jev-free deployment systems. Include a fixed
within-task shuffled-strength control after all native feedback is collected;
shuffle only strength, not routing, to separate routing from internal modulation.
All retained answers are exact references to native output, with no fake generation.

Larger models run on the same question text and independent grader, with their
native templates and disclosed recommended sampling/thinking settings. Different
profiles and token ceilings are not matched-compute comparisons. Count every
input/output/padded token, cutoff, model/API time and charged request. Report
per-arm deployment work separately from shared experimental work. Do not count
API savings: every admitted native draft receives a critic call in this design.

## Scope, access and budget

Starting estimate $42.62708084740686; the owner has now increased the cumulative cap to **$110**, not $110 more.
The owner responded to the coverage/budget question by increasing the total cap
to $110, leaving approximately $67.37. Full-task workload and evaluator admission
are being costed before final cohort/resource freeze. The increase does not prove
that comparable complete runs of all ten tasks fit this envelope.

Keep the ten rows from `benchmark-suite-contract-v1.md`. Record unavailable access,
invalid evaluator behavior, restricted contexts, samples and agent-scaffold gaps
explicitly. Never relabel a sample/subset as an official complete task, average
available rows into a ten-benchmark score, or substitute easier tasks because a
score is poor. Fresh ARC/GSM cases are separate mechanism-replication auxiliaries.
Exclude all previous R23/R25 cases and normalized duplicates; MuSR also excludes
related story variants. Public pretraining contamination remains unknown.

GPQA access check with the owner's existing token returned HTTP 403 before any
example download; no access gate is bypassed. Source/evaluator and license admission
will be recorded per task. Generated code, if evaluated, must run in an isolated
credential-free, network-disabled container, never on the credential-bearing host.
Hidden references/tests stay out of generation and Jev inputs.

Before any paid worker launch: freeze code/data/model/checkpoint/environment hashes,
fixed per-task counts and contexts, inference profiles, charge limits, hardware
rate and hard expiry. Reserve at most **$60** for this stage, keeping roughly $7.37
headroom below the cumulative cap before tax/network. Use one cheap GPU; no 8xH200,
concurrent paid worker or unrelated resource changes. Preserve interrupted runs,
back up regularly, verify final bytes, then delete owned compute/disk/network.

## Implementation and verification

New modules under `research/iterations/selective_benchmarks/`, new offline tests,
a new protocol directory and report. Frozen R25 sources/artifacts remain immutable.
Implement and test token-preserving task-specific prefixes, actual selective skips,
missing/invalid feedback, arm provenance, no-overwrite files, deadline/budget stops,
batch padding/EOS when used, feedback/checkpoint binding and independent grading.
Observe each capability/regression test fail before implementation. Reuse validated
R25 adapter/cache/client/budget primitives without modifying them.

Validate source/reference joins separately from preparation. Admit real-model
zero-gate/cache behavior and developer fixtures before new held-out generation.
Compare all planned cases with failures retained in denominators. Use paired
problem or story-cluster bootstrap intervals; define the comparison family and
multiplicity treatment in the final manifest before test. Report effect sizes even
when uncertain; no guaranteed novelty or superiority follows from a passing hook.

Archive all raw outputs/receipts/decisions/checkpoint bindings, independently audit
final tokens and actual skipped work, reproduce public-safe analyses from a fresh
extraction, inspect representative failures without retroactive regrading, and
update the study register, status files and paper draft. Core checks, full PR diff,
CI and review context must pass before handoff. No model release or merge is implied.
