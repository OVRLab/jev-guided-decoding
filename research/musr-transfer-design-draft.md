# Single-question MuSR transfer — conditional design, not registration

Prepared while R31 runs, without inspecting partial R31 quality. The current
worker and frozen sources are unchanged. This document authorizes no additional
paid stage: finish R31, reconcile cost, choose any candidate transparently and
freeze a separate protocol before public inference. The purpose is to test
whether an internal repair branch transfers beyond authored room-tracking tasks
and how it compares with a larger original Granite generator.

## Input and architectural extension to test locally

MuSR asks one question per record. Preserve that single question and its original
choices; do not repeat questions in the model prompt to satisfy the three-slot
research implementation. A candidate interface constructs one memory vector from
the complete question/choice section and an available unique final-choice span in
the actual native draft. Only original token IDs may enter extraction. Missing or
ambiguous choice spans use question/choice tokens only; no gold label is consulted.

Repeat the resulting vector and one verifier probability three times **inside**
the existing adapter interface. With identical keys, values and probabilities,
the attention-weighted value is mathematically the same as a single-slot branch,
up to floating-point arithmetic. This needs a numerical regression using nonzero
weights and multiple hidden states. It is an interface equivalence, not evidence
that a three-question-trained adapter generalizes well to this distribution.

Contextual and matched embedding memories must use the same positions. Keep the
original block and trained matrices unchanged; exact native tokens remain in the
repair prefix, with a new single-question repair instruction. R29's instruction
requiring three room names is unsuitable. Every final answer remains generated
by Granite. A single-question Jev payload needs its own bounded admission on
previously exposed cases; the earlier three-question mean is not assumed equivalent.

Prototype files can live in a separate `research/iterations/musr_transfer` directory,
with tests for numerical equivalence, token/span provenance, ambiguous readout,
reference isolation, context limits and rejection of malformed input. Do not edit
R31's frozen modules or the package dependency/source inventory while it runs.

## Prompt and grading inspection

The pinned [author evaluator](https://github.com/Zayne-sprague/MuSR/blob/b1f4d4168a9cfc6760e8b74d728e4516023dfaa5/eval/eval.py)
offers regular, chain-of-thought and domain-hinted chain-of-thought prompts. Choices
are numbered and the requested final field uses an `ANSWER:` marker. The active
default in that file uses domain hints; a simpler direct-answer profile would
therefore be a declared prompting choice, not reproduction of that default.

Its parser reads the last nonempty answer field, falls back to a random choice
when no index is found, and checks whether the gold number appears in that field.
Consequently, a field containing multiple numbers can be credited without an
unambiguous selection. These source behaviors must not silently become reasoning
success in our comparison. A prospective strict parser should reject missing or
ambiguous answers and report them separately, while accepting declared unambiguous
forms without consulting truth. Any departure from the original scoring must be
named, and resulting scores cannot be presented as directly interchangeable with
the paper's published numbers. The source was inspected, not executed.

The locally inspected `eval.py` SHA-256 is
`07f325490cd2ae5d0ed773b1b5df99930aa5bab28ea8560835982e75607d4878`.
The original code is MIT-licensed; MuSR data have their separate CC BY 4.0 terms.
No original evaluator code is incorporated by this draft.

## Fair comparison and held-out evidence

Use the [existing exposure/group map](musr-transfer-admission.md): 730 eligible
fresh questions in 428 scenario groups, excluding 26 development-related rows.
Related object-story questions and counterfactual murder variants must remain
together for splitting and uncertainty. The previously exposed 12 questions can
support bounded prompt/readout and verifier admission; they cannot become fresh
confirmatory test data. MuSR includes beliefs and soft reasoning, which physical
room tracking does not establish.

Proposed controls are original Granite, an ordinary extra repair pass, the selected
trained branch with live Jev, and the same branch with constant/donor feedback.
Keep all denominators, exact final-token provenance, failed parsings, truncations,
actual generated tokens and cost. Any conditional repair policy requires its own
prospective rule and measured dispatch/work accounting; saved-output replay is not
an avoided-call measurement. The final arm matrix remains to be frozen after R31.

The intended larger comparator is original `ibm-granite/granite-4.2-3b`, pinned to
`e459acceac81e5fe67c07d9cfc72329a332e7eb1`. Its [official model card](https://huggingface.co/ibm-granite/granite-4.2-3b)
supports both thinking and non-thinking, and recommends sampling at temperature
1.0/top-p 0.95 with 8,192/2,048 output tokens respectively. A proper comparison
needs a declared supported profile and format/stop admission; earlier shortened
thinking outputs were not a sound basis for a larger-model victory. Any smaller
generator ceiling, sampling difference and actual compute must be disclosed.

## Local implementation plan and input correction

Before any paid admission, implement a separate bounded runtime, leaving the R31
inventory untouched. It will preserve the exact native prefix, extract one
contextual/embedding vector from matched original positions, use the single-answer
repair instruction, and record every generated token and hook position. Generation
must support a declared larger-model sampling profile and sufficient output limits;
fresh cache ownership, EOS, deadlines, invalid input and hook cleanup need offline
tests. A separate one-question verifier must reserve a single attempt and record
unknown usage on ambiguous failures. No implicit paid resume is permitted.

The first tokenizer-only pass stopped at object-placement row 140: rows 140–143
contain both `pantry` and `pantry ` as separate numbered choices. Preserve all rows
and option order. An explicit index identifies a choice, while bare duplicate text
does not. The initial uniqueness check was too strict; its replacement regression
was observed failing before the fix. Before registration, bind these four records
as a dataset ambiguity flag and prespecify index accuracy plus a separately named
normalized-choice equivalence sensitivity analysis. This input inspection used no
model inference or accuracy results. It must not silently exclude the four cases.

The budget and final prompt may admit both larger-model modes or a named subset;
no claim about its strongest performance follows from non-thinking alone. Jev's
own undisclosed model size/compute belongs to the combined system. Calling the
Granite backbone smaller does not establish that the whole Granite–Jev system
uses fewer parameters or resources than the larger comparator.

Completion would include a separately frozen plan/source/data/readout, bounded
admission, full planned inference, grouped paired analysis, public-safe raw
evidence, original-weight checks and cloud cleanup. There is currently no new
MuSR model result, no larger-model result and no public-transfer success claim.

## Preparation evidence

The separate single-question prototype is now implemented: [interface](iterations/musr_transfer/single.py),
[runtime](iterations/musr_transfer/runtime.py), [verifier](iterations/musr_transfer/feedback.py)
and [pinned data assembly](iterations/musr_transfer/data.py). Eleven focused offline
tests pass after observed test-first failures. They cover ambiguous choices,
original IDs, numerical single-slot equivalence, extended output limits, private
sampling RNG, hook ownership/cleanup, frozen extraction and failed-charge retention.
Generation supports greedy or explicit temperature/top-p sampling with Transformers
`top_k=50`; the final protocol must declare the chosen profiles. Input/output/context
ceilings are validated before model work and no truncation is silently applied.

[Tokenizer-only admission](diagnostics/musr-single-interface-20260926/single-tokenizer-admission.json)
passes on all 756 rows with a **fixed synthetic** `ANSWER: 1` field, independent of
labels. Prompt maxima are 1,561/1,503/871 tokens for murder/object/team, respectively.
This validates token alignment, not an actual native draft or answer quality.
[Pinned data assembly](diagnostics/musr-single-interface-20260926/single-data-admission.json)
produces 12 exposed development and 730 fresh questions, with all references kept
in a separate mapping. Four object-placement records retain the duplicate-text flag.
[Source inventory](diagnostics/musr-single-interface-20260926/source-inventory.json)
binds the initial `b861bc0` preparation; it is not a live-study freeze or GPU admission.

The verifier shape follows the inspected [TypeSafe API](https://docs.typesafe.ai/api)
and [Noul contract](https://docs.typesafe.ai/primitives/noul): one yes/no probability
about the generator's actual selected answer. Its typed output remains a fallible
judgment. Live compatibility and useful discrimination on exposed MuSR drafts still
need their own bounded admission before a final transfer run.

### Larger-model compatibility correction before live admission

Inspection of the pinned larger checkpoint's config showed `model_type=granite`;
the original 4.0 checkpoint uses an all-attention `granitemoehybrid` implementation.
A new regression first reproduced the wrong-cache failure, then verified the
larger architecture's dynamic cache against full-prefix greedy logits. Only the
original backbone accepts the repair branch in this prototype; the larger model
remains an unmodified comparator. A second regression covers closed thinking tags
before the final answer and refuses an unclosed thinking segment.

[Larger-tokenizer/config admission](diagnostics/musr-single-interface-20260926/larger-tokenizer-admission.json)
checks all 742 assembled cases in both supported modes (maximum 1,638 prompt
tokens). Non-thinking places `<think></think>` in the prompt; thinking ends the
prompt at `<think>`, so its generated output must close the segment before grading.
Resolved pinned generation defaults are sampling, temperature 1.0, top-p 0.95 and
top-k 50. These are tokenizer/config checks, not inference or quality evidence.

CI at `b861bc0` exposed one pure-prefix test importing the optional Torch runtime
in a core-only environment. The prefix helper now lives with the pure token
interface; a test that explicitly blocks Torch/Transformers imports first failed,
then passed. Twelve focused local tests pass after these corrections. The original
preparation snapshot remains available; [revised sources](diagnostics/musr-single-interface-20260926/source-inventory-v2.json)
bind the corrected preparation. Existing least-initialized-state guidance already
covers this lesson; no additional optional dependency is added to core CI.
