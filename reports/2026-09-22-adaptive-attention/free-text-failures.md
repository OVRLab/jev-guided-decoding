# Post-hoc reading of unrestricted-answer failures

After the completed main audit exposed reduced parser coverage, inspect the first four case IDs (lexicographically) with a complete, unparsed tuned answer in the original/open_explicit panel. This selection is explicitly post-hoc and illustrative. It is not a representative sample, a new correctness metric, a blinded human review or a change to the frozen grader.

Tuned coverage is 224/600 (37.33%), versus 462/600 (77.00%) native and 355/600 (59.17%) R15. These four tuned answers all ended with EOS before the 32-token ceiling. They show that at least some failures are unanswered questions or partial source restatements, rather than only a too-short generation cap. They do not quantify the causes of all failures.

## r16/test/0001/nugulogi/light

Which room contains the parcel nugulogi?

Reference: **red**. Stated chain depth: 2.

Native Granite — eos:

```text
The room red contains the parcel nugulogi.
```

R15 static — eos:

```text
The room red contains the parcel nugulogi.
```

Tuned static — eos:

```text
[E02]
```

## r16/test/0002/pililego/light

Which room contains the parcel pililego?

Reference: **blue**. Stated chain depth: 3.

Native Granite — token_limit:

```text
Based on the given evidence, the parcel pililego is contained in the crate rasimila, which is in the room blue. Therefore, the room that
```

R15 static — token_limit:

```text
Based on the evidence provided:

[E01] The crate rasimila contains the parcel pililego.
[E04] The crate bodelela contains the
```

Tuned static — eos:

```text
The crate rasimila contains the parcel pililego.
```

## r16/test/0004/rolitumi/heavy

Which room contains the parcel rolitumi?

Reference: **green**. Stated chain depth: 5.

Native Granite — eos:

```text
The room yellow contains the parcel rolitumi.
```

R15 static — eos:

```text
The room yellow contains the parcel rolitumi.
```

Tuned static — eos:

```text
The crate munebini contains the parcel rolitumi.
```

## r16/test/0004/rolitumi/light

Which room contains the parcel rolitumi?

Reference: **green**. Stated chain depth: 5.

Native Granite — token_limit:

```text
Based on the evidence provided:

[E03] The locker cabedode contains the crate kinipuni.
[E07] The crate kinipuni contains the parcel
```

R15 static — token_limit:

```text
Based on the evidence provided:

[E01] The crate befokute contains the crate rirukino.
[E02] The room green contains the locker cab
```

Tuned static — eos:

```text
Based on the evidence provided, the crate rirukino contains the crate ripefeli, which in turn contains the parcel rolitumi.
```

## Interpretation and next hypothesis

The first tuned answer is only a source ID even though native and R15 return the correct room. The second and third give a crate relationship without naming the requested room; the fourth gives an intermediate containment chain. In the third case native/R15 also name the wrong room, so these examples do not imply that either control is always correct.

A plausible hypothesis is that the stronger source-attention policy, selected under a seven-label contract, favors reproducing evidence over composing a free answer. This study does not directly measure that causal mechanism. The matched R15 policy performs better than the tuned policy on both direct free-text panels, but the policies differ in three settings and those factors were isolated only for constrained answers.

A subsequent study could calibrate steering separately for unrestricted generation and test reduced or fading bias during the final-answer phase, while retaining stronger guidance during evidence reading. It would need fresh development/evaluation cases, a preregistered output-quality check and a controlled comparison. No such new policy was tuned or tested here.

[Complete report](README.md) · [Exact selection and source hash](free-text-failure-selection.json) · [Frozen test cases](../../research/protocols/adaptive-attention-fp32/test.json).
