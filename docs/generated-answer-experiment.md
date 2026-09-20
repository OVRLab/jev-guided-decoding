# Generated-answer experiment: Granite remains the answerer

Plan recorded on 2026-09-20 before implementation or new paid inference. The
owner rejected the previous study as an answer to the intended research question:
its final decision came from Jev. Historical results remain intact, but they are
not evidence of improved Granite-generated answers. This replacement asks whether
Jev selection of intermediate continuations improves Granite's own final answer.

## Contract and controls

All three arms use original frozen Granite 4.0 1B, identical task instructions,
an identical final-answer contract, and the same common final-generation rule:

1. `single`: one sampled Granite continuation per reasoning step; no Jev.
2. `likelihood`: three sampled continuations, selected by Granite mean log
   probability; no Jev. This controls for extra candidate generation.
3. `jev`: the same three-candidate mechanism, with intermediate steps ranked by
   Jev support/progress judgments. No Jev final-answer call or final reranking.

This is a controlled staged-generation comparison; `single` is not a claim about
an unrestricted default chat interface. The implementation will separately record
generated token IDs and controller-supplied frame delimiters. Code can open a
`<step>` or `<final>` frame but cannot insert the answer, alter selected model
tokens, or copy a Jev judgment into the final answer. Accepted reasoning tokens
remain in the same assistant continuation for final generation. The backend still
recomputes its accepted prefix between chunks; this is not a retained-cache engine.

Use up to eight intermediate frames of at most 64 generated tokens each, followed
by one greedy Granite final generation of at most 96 tokens. All arms use this
final rule even if no intermediate candidate is usable. Duplicate/malformed or
repeated steps do not enter the prefix. Jev ranks intermediate steps by
`min(support, progress)`, with model likelihood breaking ties; initial support
and progress floors are 0.5. An all-rejected batch ends reasoning, then Granite
generates the answer from the retained prefix. No resampling, alternate-tree search,
final-answer classifier, or answer-repair model is in this experiment.

A resource or ordinary reasoning stop may still permit the reserved final stage;
provider/backend errors or cancellation stop the request without hidden fallback.
Reserve final decode, context, prefill, and time before intermediate work. The
initial total per-job ceilings are 1,632 padded decode slots, 100,000 prefill
tokens, 4,096 context tokens, 8 Jev calls, and 90 seconds, including a 15-second
final reserve. Report actual work, not only equal ceilings.

## Data and grading

Use two independently reported tasks: numerical word problems from the authors'
GSM8K release and ProofWriter OWA D5 logic questions. GSM8K references stay out of
both models' inputs; its requested final frame contains only the numeric answer.
Logic references and proof depth stay out of model inputs; its final frame contains
only ENTAILED, CONTRADICTED, or UNKNOWN. System instructions and examples must agree
with these requirements. A deterministic parser/oracle grades the same Granite
output field for every arm. Report answer accuracy and format completion separately;
do not silently correct misspelled labels or infer answers from intermediate text.

Development uses GSM8K train and ProofWriter dev. The new logic evaluation excludes
every theory/evidence already used in live evaluation or development. GSM8K test
has not been used by this project. Hash source files, selection, exclusion sets,
prompts, source, and configuration before inference; retain source identifiers.
Public benchmark contamination remains possible. Raw ProofWriter text stays private
because its archive has no explicit dataset license; inspect and preserve GSM8K's
notices before publishing any of its examples.

Target 200 distinct problems per task, seeds 42/43/44, three arms: 3,600 jobs.
Rotate mode order and interleave task families. Three seeds are repeated observations
of the same problem. Primary contrasts are Jev minus single and Jev minus likelihood
within each task: four total, with 5,000 paired problem-cluster bootstrap draws and
98.75% intervals per contrast (Bonferroni nominal familywise 95%). Show each task
separately, all incomplete/failed/missing outcomes in denominators, completion,
seed variation, paired wins/losses/ties, costs, and latency. A broad positive claim
requires all four lower bounds above zero and a complete study without service,
provenance, or unknown-usage failures. No result can prove general reasoning ability.

## Development gate and budget

Before test freeze, run a development integration pilot on eight problems per task
and all three arms. Inspect final-token provenance, candidate diversity, accepted
steps, Jev's changed selections, and model answer formatting. Do not require higher
accuracy to pass a pilot: that would select for a favorable result. Require every
final answer to have model-token provenance, no Jev scoring of finals, no errors,
at least 90% final-frame completion per arm, and evidence that intermediate guidance
actually executes and selects a different candidate on at least one development
prefix. If those fail, correct the mechanism using development data only and preserve
all attempts. Freeze exact settings and sample size before test inference, using
the pilot to confirm that the run fits the remaining cloud lifetime.

The owner's total incremental budget is **USD 50**, including cloud and Jev, with
headroom for tax and cleanup. Prefer one L40S at checked compute/disk rates of about
$1.56/hour. Limit aggregate running time to 20 hours, including setup and pilot,
and Jev usage to $3 with a durable reservation ledger. At current documented pricing
($0.042/million input tokens, output free), conservatively account at $0.05/million
and reserve the full documented 65,536-token request ceiling before each single
attempt. Unknown usage retains its reservation and stops inference. Configure no
automatic retries. A shutdown timer, recovery disabled, per-minute backups, and
hash-verified cleanup bound cloud use. Do not start another server or extend the
lifetime without subtracting all spending already incurred from this budget.

## Implementation and verification plan

Add a separate generated-answer controller, public literal-control-token encoding,
an intermediate-only scorer, a persistent input-token budget, a fresh dataset
adapter/runner/config, and focused regression tests. Leave old experiment behavior
and raw records unchanged. Tests first cover answer provenance, no final scoring,
baseline operation without credentials, rejected-prefix isolation, forced-final
generation after zero accepted steps, identical prompt contracts, malformed output,
all resource reservations, cancellation, ambiguous provider failures, durable spend
accounting, disjoint data selection, independent grading, exclusive recording and
no replay of started jobs. Run canonical checks and a small real CUDA pilot before
freezing the new evaluation. Review results against these contracts before claims.

Primary sources: [GSM8K](https://github.com/openai/grade-school-math),
[TypeSafe API](https://docs.typesafe.ai/api),
[Jev model pricing and limits](https://docs.typesafe.ai/models), and
[Nebius pricing](https://docs.nebius.com/compute/resources/pricing).
