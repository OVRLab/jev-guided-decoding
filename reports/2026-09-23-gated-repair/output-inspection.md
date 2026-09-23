# R25 output inspection: choice recovery and formatting failures

This is **post-hoc, unblinded inspection** after all frozen analyses and public
replay passed. No reference, primary grade, threshold, model setting or selected
checkpoint changed. The [complete JSON](output-inspection.json) contains all native
unparseable outputs and all live full-repair/retention correctness transitions in
both seeds, with source question, answer and reference. Examples below illustrate
mechanisms; they are not independent human semantic annotations.

## Science: genuine final-choice changes under selective retention

| Live seed | Recovered parseable wrong choices | Recovered unparseable outputs | Damaged correct answers | Correct after retention |
| --- | ---: | ---: | ---: | ---: |
| 2501 | 16 | 0 | 0 | 85/96 |
| 2502 | 12 | 0 | 0 | 81/96 |

Original Granite answers 69/96 correctly. All recovered science cases already had
a parseable wrong choice, so the retained-live gain is not merely format rescue.
This still does not make every gain a newly correct reasoning process: some
native rationales conflict with their own final letters.

- `arc/test/MDSA_2013_8_32`: native chooses B (filter) to separate sand and iron;
  Jev p(correct) is 0.02. Both live seeds choose reference D (magnet).
- `arc/test/Mercury_409115`: native chooses A (both velocity and acceleration
  positive) for the parachute situation, with an incorrect explanation;
  p(correct) is 0.04. Both live seeds choose reference C (positive velocity,
  negative acceleration).
- `arc/test/Mercury_7009555`: native chooses B (energy dissipates) for light entering
  water from air; both live seeds choose reference C (wavelength and direction).
- `arc/test/MCAS_2014_8_16`: native chooses wrong B, although its sentence says air
  cools faster after sunset. Seed 2501 changes the final choice to correct D.
  This example limits any inference that every corrected letter represents new
  physical understanding.

## Science: always repairing introduces many invalid final formats

Each full-repair live seed turns **42/69 originally correct science answers into
incorrect readouts**: 38 become unparseable and four become parseable wrong choices.
Each seed has 41 unparseable science outputs overall. The math marker `####`
appears in 49 outputs for seed 2501 and 50 for seed 2502. Blind and text repair
also have many unparseable outputs (54 and 60), while the constant-branch mean is 2.5.

The shared repair instruction in the frozen `gated_repair/common.py` asks for both
`#### <numeric answer>` for math and `Final: <letter>` for choice questions. The
observed mixture of markers is evidence of an output-contract confound. Changing
that prompt was not experimentally tested here and cannot be asserted to fix it.
When Jev rates a native answer highly, the learned branch has little strength;
forcing another generation still exposes the answer to the common repair prompt.

Examples include `arc/test/ACTAAP_2007_7_36` and
`arc/test/LEAP_2005_8_10404`: correct native choices become a math marker or a
sentence plus that marker. Some changes are substantive errors instead:
`arc/test/MEA_2016_8_15` goes from correct native A to wrong live B.
Selective retention avoids these observed damages, but no claim of zero future
regressions follows from 96 science cases and two fitted seeds.

## Math: the fixed numeric contract limits score interpretation

**34/96 native math answers are unparseable.** The registered readout expects a
numeric answer on a separate `####` line. Some outputs include the right number
inline, reproduce the placeholder literally, or stop with a placeholder after
showing a result in the explanation.

- `gsm8k/test/1021`, reference 36: the native calculation ends with an inline
  `#### 36` rather than the required separate line.
- `gsm8k/test/1068`, reference 24: the output also ends with the right number
  inline; its earlier reasoning is flawed, so correct final arithmetic alone
  should not be equated with a fully correct explanation.
- `gsm8k/test/1114`, reference 8: native prints `#### <numeric answer>` followed
  by `$8` on another line.
- `gsm8k/test/1157`, reference 3: native works out three feet, then finishes
  with `#### <numeric answer>.` rather than an actual final number.

The primary 46.88% native math score is a format-and-answer score, not an estimate
of semantic math accuracy. Selective live repair changes neither correct count
nor correct-to-wrong/wrong-to-correct transitions under that fixed endpoint.
No post-hoc relaxed-parser score is substituted for the registered result.

## Interpretation for the next experiment

The positive finding is selective final-choice correction in science. The negative
finding is severe damage from mandatory repair, much of it associated with format.
Fresh validation should admit task-specific instructions and evaluator behavior
on exposed development cases, freeze them before new test generation, actually
skip unnecessary repair, and separate routing from feedback strength with matched
controls. R25 questions are now development evidence for any such redesign.
No threshold, prompt or architecture search on them can count as fresh confirmation.
