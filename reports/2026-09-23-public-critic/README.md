# R24: Jev recognizes many public-task errors, but no answers are repaired yet

On 60 unambiguous **existing native Granite answers**, Jev flags **21/23 wrong
answers** and falsely flags **3/37 correct answers** at the registered probability
threshold of 0.5. This is useful evidence for testing conditional repair. It is
**critic discrimination on exposed development data**, not improved Granite
accuracy, a Jev-generated answer baseline, a new architecture result, or a model
release. Every original Granite answer is unchanged.

| Domain | Existing wrong answers flagged | Existing correct answers falsely flagged |
| --- | ---: | ---: |
| GSM8K training math | 2/2 | 0/19 |
| MMLU-Pro validation | 15/15 | 1/12 |
| MuSR narratives | 4/6 | 2/6 |
| Total | **21/23** | **3/37** |

Error recall is 91.30% (descriptive Wilson 95% interval 73.20–97.58%), false
rejection is 8.11% (2.80–21.30%), and 21 of the 24 flags identify actual wrong
answers (87.5% precision). AUROC is 0.9753 and Brier score 0.06438. Small domain
counts matter: two detected math mistakes do not establish perfect verification;
MuSR has two missed errors and two false alarms among only twelve cases.

## What ran

The [plan](../../research/public-critic-plan.md) and
[manifest](../../research/protocols/public-critic-v1/manifest.json) were committed
before requests (`e5aa80b`). The exact 60 public problem/response pairs exclude
four unresolved R23 readouts and twelve IFBench cases whose constraints already
have deterministic verifiers. Public questions may also have appeared in model pretraining.
Selection does not exclude wrong parsed answers:
37 are independently correct and 23 wrong. The R23 secondary choice readout is
post hoc; this pilot inherits that limitation and does not establish transfer.

Jev 1.13.0 received each problem/options and the original Granite response, with
one typed probability question about the expressed final answer. No reference
answer key, identification of the correct option, hidden correctness label or
worked reference solution was sent. Ordinary multiple-choice options are part
of the problem; the plan’s “correct alternative” means an oracle-marked option.
The key remained local; no Jev credential was sent to the GPU server in this run.
One attempt per request, no retries, no threshold search, no Granite inference
and no intervention at any hidden layer occurred in R24. All sixty eligible
answers were sent to Jev: this tests a signal for selective **repair**, not a
policy that calls Jev only when needed. No provider-call savings are measured.

All **60 requests succeeded** with the pinned version: 50,475 input tokens,
1,200 output tokens, 17.33 seconds summed serial request time, and **$0.002120**
estimated API cost. The separate $0.10 cap was not approached. Every request,
raw receipt, input/label binding and individual budget settlement passes audit;
there are zero unknown charges. Provider latency here is not a colocated estimate.

## Implication for the architecture

The useful next capability is **selective repair**: retain a correct answer when
feedback supports it, and improve the answer when feedback identifies a mistake.
R24 tests only detection. Whether Granite can produce the correction, whether a
learned internal module actually uses the signal, and whether repairs outweigh
new errors remain open. A follow-up needs a native additional-reasoning control,
a matched no-informative-feedback control, measured correct-to-wrong regressions,
and fresh validation cases before final benchmarking. A textual repair prototype
would be a behavioral control, not itself evidence of a novel neural architecture.

R22's two-scalar bridge ignored useful feedback at the final-token level. R24
strengthens the case for studying feedback use on real errors; it does not undo
R22's negative result or prove where a new module should be inserted.

See [analysis](analysis.json), [independent receipt audit](audit.json),
[intervals](descriptive-intervals.json), [exact artifacts](artifacts/receipts.json.gz),
[hashes](artifact-hashes.json), and [reproduction](reproduction.md).
The question excerpts retain R23's [dataset attribution and terms](../../research/protocols/public-baseline-v1/NOTICE.md);
the repository software license does not relicense those data.
