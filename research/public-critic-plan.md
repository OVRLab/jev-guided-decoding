# R24: can Jev detect real Granite errors?

Registered 2026-09-23 before API dispatch, while the R23 larger-model baseline
runs. This is a **critic diagnostic on exposed development data**, not a
Granite–Jev answer-generation result or an admission to a full benchmark claim.

Use all 60 native R23 responses with unambiguous mathematical or multiple-choice
answers under the recorded primary/secondary readout: 21 GSM8K training,
27 MMLU-Pro validation, 12 MuSR. Exclude the three math and one MMLU outputs still
unparseable (preserve IDs/reasons). Exclude 12 IFBench cases: its exact constraints
already have code verifiers, and this check focuses on semantic answer judgment.
These selections include both correct and incorrect responses, not just failures.
R23 refs/readout yield 37 correct and 23 incorrect among eligible cases; no such
labels, correct alternatives or worked reference solutions enter Jev state.

One Noul judgment per case asks whether the expressed final decision is correct
for the question, allowing ordinary subject knowledge for MMLU and the stated
story/rules for MuSR. Ignore missing requested output wrappers if the decision is
clear. Answer correctness, not every reasoning sentence, is the target. Jev sees
the original problem/options and Granite response; its judgments cannot alter any
Granite output. No model architecture, hidden layer or final generator changes.

Pin Jev 1.13.0, one attempt, 30-second deadline, serial requests. Reuse existing
validated no-redirect transport and durable reservation ledger. Reserve up to
65,536 input tokens before each attempt; settle actual usage. Stop on any unknown
usage/provider/model mismatch; no automatic replay. Budget $0.10 at $0.042/M input,
output free. This is additional to R23's bounded cloud stage, still below the
existing $50 cumulative authorization even at both stage ceilings. Credential
stays local and private; no additional cloud resources or key copy.

Freeze code, exact public inputs, label bindings and exclusions before requests.
Threshold p(correct)>=0.5 is fixed now. Report per-domain correct/error counts,
error recall, false-rejection rate, error precision, balanced accuracy, Brier score
and pairwise AUROC (ties half credit), retaining small denominators. No threshold
search, admission cutoff or generalization claim. Missing/provider-failed outcomes
are coverage failures, not predictions. Audit raw receipts, payload identity,
usage, returned version and ledger settlement before interpretation.

Tests first: reference leakage rejection, polarity/denominators for error
signals, ties and absent classes, duplicate/missing response rejection. Preserve
this exploratory choice after seeing native errors. A useful critic is only a
possible ingredient: generated-answer repair and harms to originally correct
answers still need a separate controlled, held-out study.
