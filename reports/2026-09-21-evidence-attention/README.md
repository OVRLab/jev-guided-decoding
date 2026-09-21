# R14: Jev-guided attention to source evidence

Status, before GPU execution: implementation and local verification complete;
real-model profiling, relevance admission and held-out evaluation pending.
No quality improvement is claimed. [Prospective protocol](../../research/evidence-attention-protocol.md)
defines the full plan, calibration gate, eight arms, statistics and $50 cumulative ceiling.

## Implementation and observed local checks

The experimental [attention hook](../../research/experiments/evidence_attention.py)
adds bounded source-key biases to selected query heads inside Granite attention.
[Runtime](../../research/experiments/evidence_runtime.py),
[authored data and graph grader](../../research/experiments/evidence_data.py),
[typed scorer](../../research/experiments/evidence_scorer.py) and
[runner](../../research/experiments/evidence_study.py) retain original weights and
Granite's ownership of the one-token constrained room answer. This is static
source attention during final generation, not dynamic reasoning-prefix guidance.

The first new test invocation failed at collection because the attention/data
modules did not exist. The study/scorer tests likewise first failed for the missing
runner. During implementation, the tiny hybrid-family model fixture required a
valid Mamba head count even though its layers are attention-only; that fixture was
corrected. A strict equality assertion on untouched query rows observed a
1.1176e-8 SDPA numerical difference when a nonzero 4D mask changes kernel dispatch;
the targeted final-row change was 0.016869. The untouched-row test now uses 1e-7
absolute tolerance, while zero-bias native identity remains exact. A recovery test
first failed for the absent diagnostic extractor, then passed after using the
client's actual preserved HTTP diagnostics.

All **329 tests passed in 3.96 seconds**, including 21 new tests. They cover causal
mask locality, GQA indexing, exact zero identity, nonzero causal effects, frozen
weights, exception cleanup, prefix/cache/nested-request rejection, source offsets,
balanced graph grading, generator-token provenance, API receipt/unknown accounting,
and an end-to-end mocked overload that preserves four failed dependent outputs
and continues only the next context. Mocked API tests are not a live Jev result.

Ruff lint/format (176 files), the AI-docs checker (49 guidance files) and package
build passed. A tokenizer-only preflight checked all 912 profile/calibration/test
context variants against the pinned real tokenizer: 144–420 tokens each, all seven
answer labels distinct single tokens, with zero model forwards. No reference
answers enter the ordinary Granite/Jev view; oracle maps are a named privileged
diagnostic. Public result artifacts and final conclusions will be added after
execution and independent audit; earlier negative studies remain unchanged.
