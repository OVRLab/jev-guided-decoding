# R22 architecture and controls

This is a trained conditional residual adapter in Granite's computation, with
hosted Jev supplying two typed probabilities at one explicit reasoning boundary.
It does not merge Jev tensors or weights with Granite, read latent thoughts, or
make Jev generate a final answer. The adapter is related to representation tuning;
this experiment alone establishes no novelty.

```text
Assignment records + badge records + question
                   |
          frozen Granite, all 40 blocks
                   |
         generated intermediate courier name
                   | exact token IDs retained
                   +------ local assignment claim ------+
                   |                                    |
                   |                         hosted Jev 1.13.0
                   |                         assignment evidence only
                   |                         no badge facts/reference
                   |                                    |
                   |                          support, completeness
                   |                                    |
         common final-phase framing                      |
         re-prefill the exact conversation               |
                   |                                    |
            Granite blocks 0 ... 19                      |
                   |                                    |
              hidden state h ---------------------------+
                   |                                    |
                   +-- trained 65,568-parameter adapter --+
                   |     h' = h + bounded delta(h, s)
                   |     only final-boundary/later positions
            Granite blocks 20 ... 39
                   |
         original normalization + vocabulary head
                   |
         Granite-generated badge-color answer
         full vocabulary, greedy, at most 8 tokens
```

Block indices are zero-based. One physical Jev request evaluates the local claims
for each world; independent questions share the relevant assignment context.
For controlled offline comparisons the exact receipt is reused by multiple arms
and seeds. It is not a fresh physical call in every replayed final branch. A
deployed guided path would call once at the intermediate/final boundary. Dispatch
selection is not optimized in this pilot, and no per-layer or per-token API call
occurs. This differs from the previous single-prefill attention intervention.

The inherited verifier request includes three unlabeled, randomly ordered claims:
an authored supported claim, an authored unsupported claim, and the Granite draft
(the first claim duplicates the draft for authored training pairs). Each has
separate support/completeness questions. Thus evaluation receipts also contain
constructed control claims, including the true intermediate identity; they are
not marked correct/incorrect to Jev and contain no final badge facts/reference.
These extra claims can supply cross-question cues and make the request more
expensive. Standalone draft-only verification was not evaluated. Their scores are
never passed to the final adapter: evaluation uses only the generated draft's
two probabilities. This limitation matters when interpreting verifier accuracy
or projecting deployed cost, even though R22 shows no Jev-specific generation gain.

The rank-16 adapter computes
`h' = h + 0.1 RMS(h) tanh(U tanh(D(h/RMS(h)) + C(2s−1)))`.
The vector `s` contains support and completeness. U starts at zero, giving exact
native logits before training. Only D, U and C receive gradients; original Granite
parameters and hosted Jev remain unchanged. A per-forward scope removes its hooks
on exit and rejects nested bridge scopes and already-active earlier attention
wrappers. This is a single-request research runtime, not concurrent serving.

The real-checkpoint admission gives zero initial logit difference, nonzero adapter
gradients and no original-weight gradients. Full/cached nonzero-intervention logits
differ by at most 0.0000248, within the prospectively specified 0.0001 absolute and
relative tolerance. An initial tiny-model cache test failed because Transformers
4.57.1's empty hybrid-cache representation reported one token; reusing the existing
documented zero-length attention-cache repair resolves it. This was corrected and
tested before source/data freeze and live optimization, with no old study edited.

Every arm retains Granite's exact generated draft, including a mistaken draft.
The same added system/user framing switches to the final color task and carries
no feedback value or reference answer. Each final branch re-prefills its own
conversation/cache. Adapter effects begin at the final prompt's last token and
continue through subsequent generation, without changing earlier token IDs or
past cached values. Re-prefill and draft work are counted, not hidden as serving
efficiency. The intervention does not select among alternate final candidates.

Training uses 384 fresh authored worlds, each with a correct and an incorrect
**authored training draft**, for 768 supervised examples. Those drafts are not
claimed as Granite generations. The structural answer supplies final-token
supervision; no original Granite pretraining corpus is needed. Development (96)
and test (384) worlds instead use native Granite-generated drafts. All final
evaluated answers are native-vocabulary model outputs, never code-rendered labels.

For each of two seeds (2201/2202), real and constant-feedback adapters start from
identical tensors and see the same examples/order, learning rate, accumulation,
number of updates and development selection rule. The constant adapter receives
`[0.5,0.5]` and has the same nominal parameter count. Its 32 conditioning weights
multiply a zero signal and do not affect its output; the 65,536 residual weights
can still learn the task. Two epochs yield 192 optimizer
updates per adapter. Each arm selects its own better development checkpoint,
breaking ties toward epoch one, before any test draft is generated.

The held-out comparison contains native Granite once per world and four conditions
per trained seed: constant, live feedback, live adapter with within-motif permuted
feedback, and the live adapter with a contract-based oracle vector. The oracle
uses exact known-name support and sets unassessed drafts to `[0,0]`; this is a
conservative syntactic-contract diagnostic, not a universal semantic oracle. It
must not be interpreted as an achievable deployment score or proof that every
unassessed paraphrase is false.

The two primary contrasts are live-minus-native and live-minus-matched-constant,
averaging the two trained seeds within each world. The 10,000 paired bootstrap
draws use individual 97.5% intervals; permutation/oracle contrasts are exploratory.
No all-controls conjunction erases individual positive effects. The controls
distinguish task adaptation, reliance on feedback, and final-answer improvement.

Whole-response color correctness is deliberately narrow. Case/whitespace/terminal
periods normalize; partial phrases, contradictory strings, multiple colors and
citations receive no missing content from a judge. There is no decoder grammar,
answer menu or required UNKNOWN spelling. All worlds are answerable, so this does
not measure general natural-language correctness or missing-evidence abstention.
The same six authored motifs/templates occur across splits. Fresh names/assignment
and badge permutations do not establish external task or linguistic generalization.

See the [frozen protocol](../../research/learned-feedback-bridge-plan.md),
[manifest](../../research/protocols/learned-feedback-v1/manifest.json), and
[source](../../research/iterations/learned_feedback/study.py).
