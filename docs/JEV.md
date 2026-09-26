# Using Jev in this project

Follow [AGENTS.md](../AGENTS.md) and [SECURITY.md](../SECURITY.md). Jev provides
focused semantic judgments; it is not the authority for code correctness,
authorization, spending, or release decisions.

## Access and contribution

The [repository client](../src/jev_guided_decoding/jev.py) reads a key from
`TYPESAFE_API_KEY`, then `~/.typesafe.ai/jev`; `--key-file` explicitly selects another
raw-key file. These are host-local inputs, not files to commit or requirements
for core/offline contributions. Do not print the key to test access.

Some maintainers have a `typesafe-ai` skill. If your host exposes it, read its
current guidance before using the helper; it is optional, not a repository dependency.
Do not assume another machine has that skill, an account, or credentials. Report
missing live access and continue work that can be verified offline; never invent results.

## Inputs and judgments

Jev sees only state and questions sent to its API. A URL, filename, or repository
path in a prompt does not let it fetch that resource. Supply relevant excerpts
with context and distinguish evidence from assumptions.

| Primitive | Meaning | Returned information |
| --- | --- | --- |
| Noul | Probability a yes/no condition holds | `noul`; no separate confidence |
| Choice | Select among supplied alternatives | Choice, alternative probabilities, confidence |
| Score | Position on an ordered descriptive rubric | Weighted score, rubric probabilities, confidence |

Question IDs identify results for code but convey no meaning to Jev; put meaning
in instructions and criteria. Choice compares options, while separate Nouls can
all be low. Do not treat confidence or a high probability as proof of correctness.

The default scorer uses independent Nouls for support/relevance and completion for
EOS. Empty EOS asks only support/completion and records relevance as `None`.
The [reasoning scorer](../src/jev_guided_decoding/reasoning_scorer.py) instead asks
about the validity of the entire tentative derivation, plus new progress for a
step or completion for a final frame. It never treats the prefix as independent
evidence. Final summaries may repeat prior deductions; progress is unasked for
final frames. The `final_jev` control leaves intermediate steps unjudged.
Thresholds and selection stay in Python. This API does not expose a hidden-state
interface to Granite.

The opt-in [fixed-verdict scorer](../src/jev_guided_decoding/verdict.py) uses a Choice
with code-defined ENTAILED/CONTRADICTED/UNKNOWN options. It validates all option
probabilities, the selected maximum, and provider confidence. It allows the small
sum discrepancy from rounding three probabilities to two decimal places; it does
not renormalize them. The controller requires a unique winner at its configured
probability threshold and records uncertainty separately from semantic UNKNOWN.
Original evidence is authoritative and supplied steps are untrusted suggestions.
Direct-Jev mode omits those steps. Both share the existing transport/error rules.

## Prepare an evaluation

1. Define the decision and gather relevant evidence without cherry-picking.
2. Ask one coherent question with direct wording and balanced criteria; handle
   missing evidence, unknown, and no-match cases where relevant.
3. Batch independent questions. Use a later request when an earlier result changes
   the evidence or candidate set. Keep arithmetic and exact checks in code.
4. Record actual answers/probabilities, returned model/version, usage, and code
   decision; distinguish Jev's judgment from your interpretation.
5. Calibrate on representative validation data before held-out testing. Do not
   repeat or rephrase requests just to obtain a preferred answer.

Optional developer uses include report classification, passage relevance, or
comparing an explanation with supplied logs. Those judgments guide investigation;
tests and observed behavior establish a fix. Routine edits, exact lookups, and
checks already answered by tests do not need a model call.

## Project example

After installing the inference extra and configuring your own key as described in
[README.md](../README.md), this sends the fictional fixture to Jev:

```bash
uv run --no-sync jev-decode generate \
  --config configs/granite-4.0-1b.toml \
  --question "Who owns the Lumen release checklist, and who is the backup reviewer?" \
  --evidence-file data/example-evidence.txt \
  --mode jev \
  --output results/jev-example.json
```

Use a new output path for another run. Inspect stop reason and trace, not just
text. [Existing live results](../reports/2026-09-20-granite-smoke/README.md) are dated
evidence, not fixed expected responses for future calls.

## Failure, data, and cost

Send only task-relevant content permitted for external evaluation. References
remain local to benchmark grading. Keep credentials, private identifiers, and
unrelated confidential data out of requests and public records. Traces contain
text; inspect them before publication.

The shared client validates response shapes and records usage. HTTP 429/529 can
use bounded retries respecting `Retry-After`; transport errors/timeouts are not
automatically replayed because the request may have been billed. Errors are not
negative judgments. Preserve unknown usage instead of reporting zero cost.
Pin model IDs and record the actual returned version; pinning/seeds do not guarantee
identical outputs.

Do not use Jev as the independent grader of its own selections. Documented limitations
include numerical precision and complex reasoning. Current smoke results include
false acceptance and rejection; use [evaluation guidance](../.claude/skills/evaluation-workflow.md)
before claiming quality gains.

## Maintenance

Check live primary documentation before changing contracts or model assumptions:
[index](https://docs.typesafe.ai/llms.txt), [API](https://docs.typesafe.ai/api),
[primitives](https://docs.typesafe.ai/primitives), [confidence](https://docs.typesafe.ai/confidence),
[models](https://docs.typesafe.ai/models), and
[limitations](https://docs.typesafe.ai/model-jaggedness/jev-1.13).
Guidance edits require `uv run --no-sync python scripts/check_ai_docs.py`, not a
paid live check of an unchanged API solely to validate Markdown.
