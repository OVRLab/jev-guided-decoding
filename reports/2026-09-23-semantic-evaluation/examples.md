# R20 illustrative score repairs and regressions

These are Qwen-scored examples and include judge mistakes. A citation-only response is incorrectly credited in the first authored score repair; an unfinished birth-date response is also credited for the static control. See [transfer diagnostics](transfer-diagnostics.md). No grades have been changed.

Selection rule fixed during grading, before treatment-level score inspection: within each domain and direction, take the first case by case ID where both grades are valid and dual changes native correctness. Show all three arms for each selected case. These are unblinded descriptive examples, not a representative error sample or additional endpoint. The separately registered [24-packet inspection](blind-review.md) has a different purpose.

## Authored: repair

Case: `r20/test/0001/titeteso/light`. Question: Which room contains the parcel titeteso?

Reference alternatives: ["black"].

**Native Granite** — incorrect:

> The room red contains the parcel titeteso.

Judge reason: The parcel titeteso is in the crate giguvoca (E02), which is in the room black (E03). The response incorrectly states 'room red.'

**Static instruction** — incorrect:

> The room red contains the parcel titeteso.

Judge reason: The parcel titeteso is in the crate giguvoca (E02), which is in the room black (E03). The response incorrectly states 'room red.'

**Granite + Jev** — correct:

> [E02]

Judge reason: E02 states the crate giguvoca contains the parcel titeteso. E03 links the room black to the crate giguvoca.

## Authored: regression

Case: `r20/test/0024/petopuvu/light/dependency`. Question: Following the stated dependencies, which terminal colour does the task petopuvu lead to?

Reference alternatives: ["black"].

**Native Granite** — correct:

> Based on the given dependencies, the task petopuvu leads to the terminal black.

Judge reason: The evidence directly states petopuvu depends on terminal black, matching the reference.

**Static instruction** — correct:

> Based on the evidence, the task petopuvu leads to the terminal black.

Judge reason: The evidence directly states petopuvu depends on terminal black, matching the reference.

**Granite + Jev** — incorrect:

> [E01]

Judge reason: The response [E01] only states the dependency, not the terminal color petopuvu leads to.

## HotpotQA: repair

Case: `r20/hotpot/5a7345ed5542992359bc32ce`. Question: Which field of studies did Semyon Aranovich Gershgorin and Anatoly Maltsev work in?

Reference alternatives: ["He was a mathematician"].

**Native Granite** — incorrect:

> Semyon Aranovich Gershgorin worked in mathematics, specifically in the field of mathematics related to the Gershgorin circle theorem. Anatoly

Judge reason: The response is incomplete and cuts off mid-sentence. It does not fully answer the question about Anatoly Maltsev's field of study.

**Static instruction** — correct:

> Semyon Aranovich Gershgorin worked in mathematics, while Anatoly Maltsev worked in mathematics.

Judge reason: The evidence confirms both Semyon Aranovich Gershgorin and Anatoly Maltsev were mathematicians.

**Granite + Jev** — correct:

> Semyon Aranovich Gershgorin worked in mathematics, while Anatoly Maltsev worked in mathematics.

Judge reason: The evidence confirms both Semyon Aranovich Gershgorin and Anatoly Maltsev were mathematicians.

## HotpotQA: regression

Case: `r20/hotpot/5a7625e8554299109176e66a`. Question: In which year was the King who made the 1925 Birthday Honours born?

Reference alternatives: ["1865"].

**Native Granite** — correct:

> The King who made the 1925 Birthday Honours was King George V, who was born on 3 June 1865.

Judge reason: The evidence identifies King George V as the monarch for the 1925 Birthday Honours and D07 confirms his birth year as 1865.

**Static instruction** — correct:

> The evidence provided states that the 1925 Birthday Honours were made by King George V. Evidence D07 establishes that George V was born on 3 June

Judge reason: The response correctly identifies King George V as the monarch for the 1925 Birthday Honours and cites D07 for his birth year, 1865.

**Granite + Jev** — incorrect:

> George V

Judge reason: The response 'George V' is the name of the King, not the year he was born. The correct answer should be 1865, as indicated in the references.

## SQuAD2: repair

Case: `r20/squad2/57269184f1498d1400e8e40a`. Question: Which territory did Margaret Thatcher compare Hong Kong to?

Reference alternatives: ["Falkland Islands"].

**Native Granite** — incorrect:

> According to evidence [S03], Margaret Thatcher initially wished to hold Hong Kong and proposed British administration with Chinese sovereignty, though this was rejected by China.

Judge reason: The response does not answer the question; it describes Thatcher's proposal, not the territory she compared Hong Kong to.

**Static instruction** — correct:

> Margaret Thatcher compared Hong Kong to the Falkland Islands.

Judge reason: The evidence explicitly states Thatcher saw parallels with the Falkland Islands when negotiating Hong Kong's future.

**Granite + Jev** — correct:

> Margaret Thatcher compared Hong Kong to the Falkland Islands.

Judge reason: The evidence explicitly states Thatcher saw parallels with the Falkland Islands when negotiating Hong Kong's future.

## SQuAD2: regression

Case: `r20/squad2/57271f22dd62a815002e993b`. Question: In what war was France defeated by Prussia?

Reference alternatives: ["Franco-Prussian War"].

**Native Granite** — correct:

> France was defeated by Prussia in the Franco-Prussian War of 1870–1871.

Judge reason: The response correctly identifies the Franco-Prussian War of 1870–1871 as the war in which France was defeated by Prussia, as stated in the evidence.

**Static instruction** — correct:

> The war in which France was defeated by Prussia was the Franco-Prussian War of 1870–1871.

Judge reason: The response correctly identifies the Franco-Prussian War of 1870–1871 as the war in which France was defeated by Prussia, as stated in the evidence.

**Granite + Jev** — incorrect:

> The Treaty of Paris stood until 1871, when France was defeated by Pr

Judge reason: The response is incomplete and cuts off mid-sentence, failing to provide the full correct answer 'Franco-Prussian War' as stated in the evidence.

Full evidence and exact selected records: [illustrative-examples.json](illustrative-examples.json). HotpotQA and SQuAD content retain their report attribution notices. These labels are the frozen Qwen judgments, not fresh human adjudication.
