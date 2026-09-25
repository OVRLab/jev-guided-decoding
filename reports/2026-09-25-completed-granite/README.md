# R27 completed-Granite comparisons

The frozen Granite–Jev system improves the measured score over original Granite
on GPQA Diamond and IFBench, but not AIME. Most of the GPQA gain also appears with
fixed or shuffled adapter feedback. IFBench shows a larger margin over fixed
feedback, but only three more correct answers than shuffled feedback. These
results support further investigation of repair and instruction following; they
do not establish broad superiority, a benefit from correctly paired Jev scores
over shuffled scores, or the ten-benchmark objective.

This offline analysis was [specified before fresh scoring](../../research/completed-granite-audit-v1.md),
after the [generation deadline and cleanup](../2026-09-24-full-benchmark-tranche/README.md).
Nine complete systems use the full denominators. The incomplete Qwen comparator
is excluded from quality scoring and remains explicitly incomplete. No new model
generation, Jev request or cloud allocation was used for this analysis.

## Full-source results

Values are correct cases / all cases. IFBench is strict prompt-level accuracy;
GPQA and AIME use the frozen v3 answer readout. These are registered OVRLab
zero-shot profiles, not exact reproductions of every upstream leaderboard recipe.

| System | GPQA Diamond (198) | IFBench strict (300) | AIME 2026 (30) |
| --- | ---: | ---: | ---: |
| Original Granite 4.0-1B | 37 / 198 (18.69%) | 55 / 300 (18.33%) | 0 / 30 (0%) |
| Granite–Jev | 54 / 198 (27.27%) | 71 / 300 (23.67%) | 0 / 30 (0%) |
| Jev-free self-refinement | 33 / 198 (16.67%) | 59 / 300 (19.67%) | 0 / 30 (0%) |
| Routed blind repair | 36 / 198 (18.18%) | 59 / 300 (19.67%) | 0 / 30 (0%) |
| Constant-trained adapter | 53 / 198 (26.77%) | 59 / 300 (19.67%) | 0 / 30 (0%) |
| Live-trained adapter, constant feedback | 52 / 198 (26.26%) | 60 / 300 (20.00%) | 0 / 30 (0%) |
| Inverted feedback | 36 / 198 (18.18%) | 57 / 300 (19.00%) | 0 / 30 (0%) |
| Shuffled feedback | 51 / 198 (25.76%) | 68 / 300 (22.67%) | 0 / 30 (0%) |
| Granite 4.2-3B, thinking profile | 42 / 198 (21.21%) | 178 / 300 (59.33%) | 8 / 30 (26.67%) |

The six routed arms share the same Jev-based repair decision. Constant and shuffled
controls remove or misalign the score supplied to the adapter; they do not remove
Jev from routing. Therefore their performance does not measure an entirely
Jev-free system. Self-refinement is the separately measured Jev-free extra-work
baseline and repairs every case. `live_constant` uses the same live-trained
adapter at a fixed strength, whereas `constant` uses the separately trained
matched adapter.

## What the contrasts establish

- **Native comparison:** GPQA gains 17 correct answers (+8.59 percentage points),
  with 32 wins and 15 losses; IFBench gains 16 (+5.33 points), with 22 wins and
  six losses. The frozen descriptive paired 95% intervals are [2.02, 15.15] and
  [2.00, 8.67] points respectively. These are descriptive, unadjusted comparisons,
  not a confirmatory multi-benchmark superiority test.
- **Case-specific feedback:** GPQA exceeds the constant-trained adapter by only
  one answer, the fixed-strength live adapter by two, and shuffled feedback by
  three. All corresponding descriptive intervals include zero. IFBench exceeds
  those controls by 12, 11 and three answers respectively; the shuffled contrast
  is +1.00 point with interval [−1.00, 3.00]. Correctly paired feedback has not
  established superiority over shuffled feedback on either task.
- **Math:** all eight 1B systems score zero out of 30; the experiment demonstrates
  no AIME improvement. Zero observed wins does not establish a zero population
  effect. The larger Granite solves eight cases despite many truncations.
- **Larger model:** Granite 4.2-3B is much stronger on IFBench and AIME. Its GPQA
  run has 140/198 unfinished thinking responses at the 8,192-token ceiling,
  scored as missing final answers. The apparent GPQA advantage of the smaller
  system is not a general capability ranking; the guided-minus-3B descriptive
  interval also includes zero. No larger-model victory is established.

The untouched subsets retain the direction: original/guided GPQA **37/196 versus
53/196** (18.88% → 27.04%, +8.16 points, interval [1.53, 14.80]); IFBench
**52/288 versus 67/288** (18.06% → 23.26%, +5.21 points, interval [1.74, 8.68]).
On untouched GPQA the constant-trained adapter exactly matches guided at 53/196.
Project-untouched does not mean absent from pretraining data.

A post-hoc class-balance check finds GPQA correct labels A=35, B=70, C=52 and
D=41. Uniform random choice has an expected 25% score; always returning B would
score **70/198 (35.35%)**, above guided 54/198 (27.27%). This is a retrospective
fixed-output reference, not a prespecified selected policy or a model run.
The imbalance further limits any claim of useful absolute science capability
from the guided-versus-native gain. All label counts and constant-letter reference
scores are exported; no option order or grade was changed after inspection.

## Readout and failure diagnostics

GPQA unparseable finals fall from **67/198 to 16/198**. A post-hoc partition of
the unchanged grades finds that 16 of the 32 guided wins started from an
unparseable native answer; 16 started from a parseable wrong answer. All 15 losses
end in parseable wrong answers. Thus the net gain is +16 in transitions from
unparseable native answers and +1 in parseable answer changes. This partition
does not establish whether the underlying reasoning was correct before repair;
readout improvements must not be equated with improved scientific reasoning.

All 22 IFBench wins start from nonempty native answers, so the measured gain is
not merely converting empty outputs to nonempty ones. However, guided IFBench
length stops increase from four to 21, and empty/unparseable finals from zero to
ten. IFBench loose scores are original 68/300, guided 83/300 and larger Granite
186/300. These alternate scores were already in the frozen evaluator and do not
replace the strict result.

For AIME, unparseable 1B outputs rise from 11/30 to 21/30 with guidance. The larger
Granite has 22/30 unfinished thinking outputs. Its IFBench profile has 71 length
stops, including 70 unfinished thinking outputs. All such cases remain in the
denominators. No parser, prompt, token ceiling or model setting was retuned after
seeing these results.

## Mechanism, work and scope

The live-trained adapter has 262,144 parameters and acts after zero-indexed block
19; original Granite weights stay frozen and Granite generates every final token.
The original native answer is retained unless the frozen Jev judgment requests a
repair. Repairs execute for **172/198 GPQA** and **286/330 IFBench/AIME** cases.
All **528 cases call Jev**; skipping 70 repairs is not a saving of Jev requests.

Recorded native-plus-guided GPU generation time is approximately 1,519.60 seconds
for GPQA versus 1,486.55 native-only, and 3,953.23 seconds for IFBench/AIME versus
2,364.42 native-only. These sums exclude hosted Jev latency, loading, evaluator
work and interrupted partial work. They are not end-to-end serving latency or
throughput. Complete work counters, all control costs and API usage are in the
aggregate files. Larger profiles use different precision, sampling and ceilings.

Both saved streams pass exact-token decoding, hook-position, source/checkpoint,
weight, job/batch, selection and receipt checks: **4,551 saved output records**
and **3,902,358 generated tokens**, including warmups, probes and saved partial
Qwen outputs. Interrupted unfinished work remains unmeasured. Both lineage chains
and all 143 saved remote-file hashes match; 528 successful Jev calls have zero
retries or unknown charges. Scope and evaluator-binding tests first failed for missing audit capabilities;
all six new tests and all **640 repository tests** now pass.

Qwen has only 4/198 GPQA, 199/300 IFBench and 4/30 AIME outputs, scheduled by
prompt length. No Qwen accuracy or representative-subset claim is made. Seven
other full benchmark tasks remain incomplete; no ten-task aggregate is reported.
All owned cloud resources were deleted. The unchanged conservative cumulative
closure estimate is **$103.83/$110**, before tax/separate network, including
downtime at regular rates; it is not a provider invoice.

## Evidence

- [GPQA aggregate scores, contrasts, work and hashes](gpqa-analysis.json)
- [IFBench/AIME aggregate scores, contrasts, work and hashes](short-analysis.json)
- [Audit verification and reproduction constraints](verification.md)
- [Completed-system auditor](../../research/diagnostics/completed_granite_audit_v1.py)
- [Unchanged original full-tranche auditor](../../research/diagnostics/benchmark_execution_v3_audit.py)

Private archives retain questions, answers, exact tokens, receipts and per-case
grades. Public exports contain aggregate measurements and hashes only; this is
not a publicly redistributed raw-data replay or a released model checkpoint.
