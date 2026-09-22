# R16 admission failure and cache diagnosis

Registered 2026-09-22 after the first GPU admission attempt, before any development,
test or Jev call. Source `9c150df` stopped because cached/full-prefix vocabulary
logits differed by up to 0.5, exceeding the prospective BF16 threshold 0.125.
No benchmark result exists. The stopped output/log is retained; do not relabel
this admission as passed or silently loosen the threshold.

Compare native and R15 attention under BF16 and FP32, on three reserved external
mechanics examples and three development examples. Record prefill equivalence,
second-step cache/full maximum and mean differences, argmax, top-two gap and KL.
Keep the original hook/runtime fixed. This will distinguish a precision-dependent
numerical discrepancy from a structural mask/cache defect. No Jev calls. Original
protocol and manifested source remain frozen. Any changed execution precision or
admission policy needs a separate prospective amendment before benchmark inference.
