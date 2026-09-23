# R20 supplementary blind inspection

The coding assistant reviewed the first 24 unique packets in their original random
order, after the grading freeze and before reading Qwen labels, treatment mappings
or aggregate scores. Its Boolean labels and reasons were saved before comparison.
Qwen agreed on **21/24 (87.5%)**. This small packet sample is descriptive; it is
not an estimate of the full benchmark's error rate or independent human validation.
The reviewer implemented the study and knew its hypotheses; strict operator
isolation is not claimed. The primary grades remain unchanged.

## Two clear completeness failures and one ambiguous disagreement

- **Packet 4, requested television network:** the answer begins identifying Glen
  Campbell and his show, then stops without saying CBS. The reviewer marked it
  incorrect. Qwen marked it correct and supplied CBS in its own reason, borrowing
  the missing answer from the evidence rather than requiring it in the response.
- **Packet 9, requested nationality:** the response is only “Belinda Peregrín.”
  The reviewer marked it incorrect because a person's name is not a nationality.
  Qwen marked it correct and described the nationality in its reason. This is
  another substitution of the judge's knowledge for the candidate's answer.
- **Packet 10, vote on crimes:** the packet labels the question unanswerable, while
  its evidence names China and the United States as abstaining on a referral
  resolution. The response names those countries. The reviewer followed the
  supplied unanswerable flag and marked it incorrect, explicitly flagging the
  ambiguous question wording. Qwen accepted the plausible referral-vote reading.
  This is a rubric/annotation ambiguity, not a cleanly established judge mistake.

These disagreements show why 96/96 on short constructed validation templates did
not establish reliable transfer to real generated answers. In particular, the
validation's incomplete-answer category did not cover the observed wrong answer
type and unfinished bridge-entity responses. The primary score is agreement with
this automated judge, not independently verified semantic correctness. Passing
the parse/coverage gate cannot remove this limitation.

## An additional reference problem

**Packet 21** asks for Detroit's percentage population decline. The evidence says
the later population was less than 40% of the 1950 population, implying a decline
over 60%, but the supplied reference is “40.” Both reviewers reject the candidate's
“98%,” so their agreement does not reveal or correct the reference inconsistency.
This is another reason label agreement cannot certify question/reference quality.
The finding was recorded in the original blind review reason before Qwen labels
were opened. No reference, answerability flag or primary grade was changed.

## Consequence for the architecture objective

The study measures a positive authored-task score effect and mixed external
effects, but neither those scores nor this small inspection prove better reasoning
or a generally superior Granite + Jev architecture. The next measurement revision
needs validation that specifically checks whether the response itself supplies the
requested answer, plus independently reviewed question/reference/answerability
labels. New validation and test cases must be separate from these exposed examples.
This review does not authorize a silent regrading or a new inference run.

The [complete review record](blind-review.json) contains all 24 anonymous packets,
the original timestamped labels, subsequent Qwen comparisons and hash bindings.
The [prospective rule](../../research/semantic-evaluation-blind-review.md) and
[method](method.md) document scope. HotpotQA and SQuAD content retain the report's
[HotpotQA](HotpotQA-NOTICE.md) and [SQuAD](SQuAD-NOTICE.md) attribution notices.
