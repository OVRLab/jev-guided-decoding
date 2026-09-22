# R18: a conditional Jev decision inside one Granite prefill

Registered 2026-09-22 before new model inference or paid calls. This implements the
[earlier boundary hypothesis](selective-attention-next-design.md) after the completed
[R17 results](../reports/2026-09-22-selective-attention/README.md). It is an experiment,
not a claim of novelty, an improved checkpoint, or an authorized merge/model release.

## Questions and mechanism

1. Can a gate immediately before zero-indexed Granite layer 19 preserve the native
   or always-guided full logits, accepted tokens and cache while avoiding R17's
   buffered eight-token pilot and repeated prefill?
2. Do native attention features at layer 18 identify questions that benefit from
   Jev relevance guidance under an explicit development request budget?
3. Does any benefit transfer to fresh external QA and natural unanswerability?

Use unchanged `ibm-granite/granite-4.0-1b` revision
`6a7381ba1f54d684ff508d991aeb7dc580157103`, FP32, Torch 2.8.0, Transformers 4.57.1,
SDPA, greedy full-vocabulary generation capped at 32 final tokens. Every arm uses
R16/R17's open-explicit system instruction; no colour menu, forced UNKNOWN or
code-generated semantic answer. Granite owns every final token; no weights train.

The fixed treatment is R17's selected additive/all-token strength-5 policy,
relevance >0.65, eleven query heads across nine layers. No new head/strength search.
The earliest controlled layer is 19. The normal model layer loop remains intact.
A serial scoped callback observes the final prompt query's native, post-RoPE
attention distribution at layer 18. A pre-hook before layer 19 decides whether to
make one Jev request on the original question and source text. References, model
features and generated answer tokens are not sent to Jev. Skip or provider failure
continues the same native computation/cache; success activates the fixed biases
for the remaining layers and subsequent decoding. There is one prefill in either
branch, no native pilot, no rollback and no discarded output tokens.

The three feature families are mean evidence attention mass, entropy of the mean
within-evidence source distribution normalized by log(source count), and mean
Jensen–Shannon disagreement of head-wise source distributions. Use only the final
query row (heads × keys), not a full prompt attention tensor. Save sufficient
per-source/head statistics to reconstruct features within 1e-12 arithmetic tolerance;
gate decisions use the recorded native features exactly. Features are read before any
intervention. A synchronous model worker bridges to the owned async provider loop;
cancellation must drain the worker before restoring/reusing global dispatch state.
Concurrent requests and vLLM serving remain unsupported. API failure is not a score.

## Finite development and frozen selection

New code lives in `research/iterations/boundary_attention/`; previous scientific
source/cohorts/outcomes stay unchanged. Before quality inference, freeze source and
data hashes in `research/protocols/boundary-attention-v1/manifest.json` and commit.

Development: 108 fresh authored heavy-context worlds (three relation wordings ×
depths 1–6 × answerable/missing), 72 fresh length-eligible HotpotQA questions and 80
SQuAD2.0 questions (40 answerable, 40 impossible). Run native-with-observation and
always-guided boundary branches for every input: 260 × 2 = 520 outputs. The observed
native branch also supplies R17's first-eight-token probability, entropy and
source-word-overlap features without an extra development inference.

Fit one threshold rule (feature, direction and threshold) to guided-minus-native
quality, under an unweighted development call ceiling of 50%. Candidates: never,
plus each feature's empirical quantiles at 0, .05, .10, …, 1 in both directions.
Maximize equal-domain quality (authored parser accuracy, Hotpot token F1, adapted
SQuAD token F1), then minimize calls, then canonical JSON order. Fit the boundary
and R17 pilot rules separately using their respective three features. Do not fit
on test or choose a winning budget after test. Never-calling remains permitted.
Use the boundary rule's unweighted development call fraction for a deterministic
hash-random live control. Freeze selected rules before the first test outcome.

## Fresh test and controls

Test: 252 authored worlds each in light/heavy contexts (504 inputs), 240 Hotpot
questions and 240 SQuAD2.0 questions (120 answerable, 120 impossible): 984 inputs.
All authored names are disjoint from R14–R17 and development. Hotpot questions are
disjoint from R16/R17, retaining ten complete paragraphs and a 3,072 prompt-token
ceiling. Use six additional disjoint external admission fixtures.

SQuAD2.0 is new to this project. Use the official public development file, split
by article title into our development/admission/test pools before sampling. Keep
one question per paragraph within each split, class balance fixed, and deterministic
selection independent of generated answers. Keep the complete original paragraph,
split at sentence-ending whitespace into source units (1–32); do not add gold
annotations or distractors, truncate evidence, or filter by predicted quality.
Record upstream IDs, paragraph/title groups, eligibility and source-file hashes.
This is a length-filtered, article-disjoint project subset, not the official hidden
test or a leaderboard submission. Pretraining exposure is unknown.

Nine held-out arms, all with identical original evidence and prompt:

- `native`: R17 native runtime without observation or Jev.
- `always`: R17 fixed always-guided reference without boundary observation.
- `boundary_never`: observe layer 18, skip Jev, continue natively.
- `boundary_always`: observe, call once at layer 19, continue with guidance.
- `boundary_gate`: selected 50%-ceiling development rule at the internal boundary.
- `boundary_random`: hash-random call control at the development gate call fraction.
- `pilot_gate`: separately fitted R17 feature rule, retaining its pilot/restart work.
- `lexical`: the fixed treatment with R17's lexical relevance, no Jev.
- `shuffled`: the fixed treatment with deterministic shuffled Jev relevance.

984 × 9 = 8,856 test outputs. Boundary gate executes first per input, proving its
physical dispatch/skip decision before any receipt exists. Remaining arms execute
in a fixed seeded randomized order and reuse byte-identical source receipts. Report
actual HTTP attempts separately from standalone logical calls. Timing that adds a
saved call duration to a cache-hit run is an estimate, not a fresh latency trial.

## Admission, tests and scoring

Write tests first and preserve their observed failures: correct attention feature
reconstruction with GQA/masks; exact native/always full-logit and all-layer cache
parity; once-only boundary ordering; binding and cross-request/nested rejection;
first-token/early-EOS behavior; failed-call fallback; cancellation cleanup; finite
feature/gate validation; fresh cohort/schedule selection; independent audit rejecting
token, feature, gate, source, request and work tampering. Core imports remain usable
without model/GPU/provider dependencies; offline tiny models need no credentials.

Before live quality work, real-checkpoint admission uses three authored development
fixtures and six reserved external fixtures. Compare native versus boundary-never,
R17 always versus boundary-always, and forced failed-receipt fallback versus native.
Require maximum full-vocabulary logit and cache difference <=1e-4, same greedy
accepted tokens, same layer cache lengths, exact source/weight identity, one prefill
per boundary branch, and no lower-layer recomputation. Record full evidence and
stop on a failed admission; any repair is a separate preserved amendment.

Authored and Hotpot grades retain the R17 contracts. SQuAD uses the maximum
normalized EM/F1 over its gold answer strings. A frozen conservative natural
abstention recognizer maps an explicit whole-answer uncertainty phrase to empty
prediction; empty/EOS alone remains an unsuccessful answer, not automatic abstention.
Report raw whole-answer EM/F1 separately from this adaptation, answerable/impossible
subgroups, recognized abstentions, wrong abstentions, token caps and exact examples.
This adapted natural-answer contract is not the official SQuAD no-answer-probability
protocol. The same recognizer applies regardless of gold class. References never
enter model/scorer inputs. No regrading after seeing quality.

## Analysis and separate conclusions

The three primary quality contrasts are boundary-gate routing value versus the
expected random use of audited native/always branches at the **same actual test
call count**, separately for each domain. Report 10,000 paired world/question
bootstrap intervals at individual 98.333% coverage (nominal 95% family coverage).
Authored light/heavy contexts stay together; SQuAD uses one question per paragraph
and bootstrap resampling groups its questions by article title. Hotpot groups by
question. This retains shared-article dependence in the SQuAD intervals.
No conjunctive all-controls success requirement and no general claim from one domain.

Secondary exploratory 95% intervals: always−native; boundary gate−native/always;
boundary gate−pilot gate; boundary gate−live random; always−lexical/shuffled.
The gate-versus-always 3 pp loss margin is descriptive exploratory noninferiority;
report calls alongside it and never treat an all-call gate as selective success.
Save fixes/harms/missed fixes/avoided harms and all three-domain scores. No post-test
budget or feature tuning. No offline extra budget policy is part of this protocol.

Mechanical conclusions are distinct: native/boundary-never and always/boundary-always
must match token paths; all boundaries must precede layer 19 and retain lower-cache
state. Compare mean/median/p95 time to first token, model time excluding measured
provider wait, estimated uncached elapsed, forward and per-layer token counts,
prefills, pilot tokens, peak allocated GPU memory and feature overhead. Tokenization
and model loading are excluded from per-question timings and included in whole-run
cloud cost. Measure the
actual work; identical outputs alone do not establish faster execution. Hosted
service variability and shared receipts limit causal latency inference.

## Operations, budget and finish

Prior verified spend $23.456365263925505 of the $50 allowance. Use one non-preemptible
L40S (8 CPU, 32 GiB RAM, 80 GiB SSD) if available. Reserve <=$13 compute/disk and
<=$2 Jev, leaving room below the cumulative allowance. Eight-hour VM stop timer,
six-hour inference limit, one intra-op and inter-op CPU thread. Check current price
and capacity before launch. If unavailable, inspect cheaper authorized alternatives
without launching an eight-GPU machine. Privately transfer and verify the Jev key;
never record it in source, process arguments, public files or provider payloads.

One provider attempt per exact payload, maximum 90 seconds, durable reservation
before dispatch. Unknown attempts stay fully charged and are never replayed.
Fallback remains in the denominator; stop after three consecutive or twenty total
incidents, or non-transient contract/auth errors. Preserve interrupted jobs without
replaying them. Cooldowns occur outside active GPU forward ownership where possible.

Retrieve and byte-verify every artifact, independently reconstruct grades/choices/
token provenance/requests/work/freeze, verify unchanged weights, then delete all
task VM/disk/network resources. Publish safe lossless traces with Hotpot/SQuAD
CC BY-SA notices, source/runtime versions, all failures and costs, scientific figures,
updated register/notebook/paper, and the existing PR. Inspect tests, CI and review
context before handoff. No human or automated scientific approval is implied.
