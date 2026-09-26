# R22: conditional local-feedback residual adapter pilot

Prepared 2026-09-23 while the fixed R21B replication runs. Live optimization and
evaluation require its independently reconstructed admission to pass. Offline
mechanism tests may be prepared now; no checkpoint or positive result is implied.
This is the conditional architecture stage authorized in the [R21 plan](semantic-feedback-plan.md).

## Mechanism

Keep original Granite 4.0-1B revision `6a7381ba1f54d684ff508d991aeb7dc580157103`
and Jev 1.13.0 weights frozen. A rank-16 adapter after zero-based block 19 learns
`delta = 0.1 * RMS(h) * tanh(U(tanh(D(h/RMS(h)) + C(2s-1))))`, where `s` contains
local support and completeness probabilities. Initialize U to zero. Train only
D, C and U; do not add the adapter to the original parameter checkpoint. The
intervention begins at the last token of the final-answer prompt and applies to
subsequent cached decode positions. Earlier positions and exact draft IDs remain
unchanged. This is a bounded residual intervention, not attention bias or logits
reranking. No assumption says block 19 or rank 16 is optimal.

Granite first generates the courier identity. At that semantic boundary, one Jev
request evaluates the local assignment claim, without badge facts or the final
reference. The vector conditions the hidden-state adapter while Granite generates
the badge-color answer from its full vocabulary. A fixed subsequent system turn
explicitly changes from the intermediate-name phase to the final-color phase;
it is identical in every arm and contains no Jev judgments. Re-prefill the exact
draft prefix for each compared final branch; count that extra work and do not
claim R18's one-prefill optimization. Retain each branch's own cache.

## Fixed data and training

After admission, freeze independently seeded worlds with the existing R21B
renderer: 384 training (`220923101`), 96 development (`220923102`) and 384 test
(`220923103`), excluding all prior names/worlds and earlier splits. Templates and
logical motifs overlap; names, assignments and badge permutations are fresh.
These are narrow authored tasks, not new external-benchmark reasoning evidence.

Each training world supplies two explicitly **authored training drafts**: its
correct courier and an incorrect courier. This is synthetic supervised training,
not a claim that Granite generated those draft tokens. Jev evaluates both in the
existing independent-question request shape. The target is the structurally known
badge color followed by EOS. Native Granite generates development and test drafts
greedily, at most 24 tokens; final answers in every evaluated arm are Granite
generations, at most 8 tokens, without a decoder grammar or answer menu.

Two initialization/order seeds, 2201 and 2202. For each seed train a live-feedback
adapter and an equal-parameter constant-feedback adapter (`s=[0.5,0.5]`) from the
same initial weights on the same 768 examples and order. AdamW, learning rate
0.003, zero weight decay, gradient norm cap 1, microbatch one, accumulate eight
examples per update, two epochs (192 optimizer updates total per model). FP32,
original model in eval mode, no dropout. Optimize exact final-token cross entropy
only. Evaluate each epoch on development; select the higher exact-answer score,
breaking ties in favor of epoch one. No test inspection chooses hyperparameters,
layer, checkpoint, thresholds, examples or method.

## Arms, checks and inference accounting

Evaluate native once per test world; for each of two seeds evaluate its selected
constant adapter, live-feedback adapter, same live adapter with feedback permuted
within motif, and same live adapter with oracle support/completeness. Oracle is
diagnostic only, never a deployable benefit. This makes nine generated final
answers per world, 3,456 test answers. Reuse one cached receipt per exact draft,
reporting physical and logical API use separately; sharing across offline arms
is not deployed inference. Permutation donors are fixed before outcomes.

Primary endpoints: whole-response color correctness, live minus native and live
minus matched constant, averaging seeds within world, paired bootstrap 10,000
draws with individual 97.5% intervals. This measures a narrow specified answer
contract. Citation-only, incomplete, contradictory or multiple-color answers get
no inferred missing content. Report exact color, format failure, natural draft
correctness, repairs/regressions, each motif and both seeds. No all-controls gate
is used to erase a positive contrast; ablations determine its interpretation.

Before training: zero-adapter exact parity on the real checkpoint, nonzero
intervention affects only allowed positions, cached-versus-full-forward agreement,
adapter gradients with absent original-weight gradients, finite vectors only,
nested-scope rejection and hook cleanup on exceptions. Original weight hashes
before/after; save adapter tensors in safetensors with configs/hashes. Raw traces
retain prompts, suffix/draft/final IDs, receipt payloads, accepted checkpoints,
training losses/update counts, epochs, RNG seeds, latency and full work counts.
Failed provider requests stop the study without replay; preserve partial work.

## Operations and decision

One Nebius L40S, at most five hours with automatic poweroff and a four-hour process
deadline; total compute/disk allowance $10, Jev $0.50, within the original $50
cumulative cap. Check the post-R21 cumulative amount before creation. Retrieve
and verify all evidence/checkpoints, then delete owned VM/disk/network resources.
The prototype is serial and experimental, not vLLM, concurrent serving, a colocated
Jev model, a Hugging Face release, or a validated general architecture improvement.

If live feedback beats the matched trained control, investigate replication and
transfer next. If both improve similarly, credit task adaptation. If feedback
ablation has little effect, the learned bridge may ignore Jev. Preserve negative
outcomes. ReFT already learns representation interventions on frozen models;
this pilot cannot establish novelty by itself ([ReFT](https://arxiv.org/abs/2404.03592)).
