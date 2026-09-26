# What the mass constraint and selective gate actually guarantee

This derives properties of the implemented R17 operations. It does not add a
policy, prove answer correctness, or claim the underlying mathematics is novel.

## A constrained change within evidence

For one query in one selected attention head, let `p = softmax(l)` be the attention
distribution for the current query/key vectors, S the evidence-token set, and
`m = sum(p[k] for k in S)`. Let b be the Jev-derived source bias. We want to favor
relevant evidence while keeping `q[k] = p[k]` outside S and `sum(q[S]) = m`.

The solution of the following entropy-regularized objective is an exponential tilt:

```text
maximize_q  sum_{k in S} q[k] b[k] − sum_{k in S} q[k] log(q[k] / p[k])
subject to  q[k] >= 0, sum_{k in S} q[k] = m, and q[k] = p[k] outside S.

q[k] = m p[k] exp(b[k]) / sum_{j in S} p[j] exp(b[j]),  k in S.
```

A Lagrange multiplier for the mass constraint gives
`log(q[k]/p[k]) = b[k] - constant`; normalizing within S gives the expression above.
The implementation obtains it by adding `b[k] - c` to every evidence-key logit,
where `c = LSE(l[S]+b[S]) - LSE(l[S])`. The evidence partition stays unchanged;
the total softmax denominator and all outside-evidence probabilities therefore
stay unchanged for those Q/K. Computing log-sum-exp avoids dividing by a small
floating-point probability mass. Uniform b would cancel exactly; the runtime
short-circuits uniform mapped scores as a literal no-op.

The constraint assigns responsibilities: Jev can redirect existing evidence
attention; the current Granite state determines the total evidence attention.
This could help when additive steering overemphasizes evidence at the expense of
the question or answer-generation context. It remains a hypothesis about quality.

The guarantee is **local to a particular head, query and current Q/K**. Earlier
interventions change later representations, so it does not imply that outside
probabilities or total evidence mass equal those of an entirely native forward
pass at every layer. The attended value mixture, residual stream, later caches
and eventual answer can all change. Incorrect relevance can still cause harm.
Thresholding and strength also remain fallible development-selected choices.

## Routing benefit is different from model uncertainty

For a held-out input i, define the measured guided-minus-native quality `d_i` and
the gate's pre-Jev decision `c_i` in {0,1}. Because accepted outputs are audited to
equal exactly one of the two deterministic branch outputs, the gate's average
improvement over native is `mean(c_i d_i)`.

Uniform random routing with the same total number of calls has expected improvement
`mean(c_i) mean(d_i)`. Their difference is:

```text
routing value = mean(c_i d_i) − mean(c_i) mean(d_i).
```

The gate needs positive association with **treatment benefit**, not merely with
incorrect or low-confidence native answers. Calling Jev on an uncertain answer
that Jev-guided attention would not improve consumes work without helping. Calling
on a confident answer that guidance would fix can be useful. R17's small fitted
threshold rule is one limited attempt to estimate that distinction from development
data; the held-out routing analysis tests it. A broad causal or population claim
still needs appropriate independent evaluation and uncertainty estimates.

Neither fewer calls nor positive routing value alone proves a useful generator:
absolute quality, gains against native, lost useful interventions and actual
discarded/prefill work remain necessary parts of the result.
