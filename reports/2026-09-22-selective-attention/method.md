# R17 method and prospective scope

This study is being implemented and validated; no live quality result is claimed
by this initial method record. The [plan](../../research/selective-attention-plan.md)
defines hypotheses, selection, controls, data counts, budgets and primary tests.
The [related-work review](../../research/selective-attention-related-work.md)
separates prior ideas from the proposed combination.

```text
Question + complete evidence
            |
       Native Granite pilot (up to 8 tokens; not yet emitted)
            |
       Cheap gate from observed probabilities/entropy/source-word overlap
            |
       +----+---------------------+
       | skip                     | request help
       v                          v
Continue exact pilot       One Jev call: per-source relevance
tokens and KV cache               |
       |                   discard pilot; fresh Granite cache
       |                          |
       |                   selected attention heads:
       |                   additive or mass-preserving guidance
       |                   all / prefill / fade over 8 tokens
       |                          |
       +--------------------------+
                    |
          Granite-generated free-text answer
```

An API error continues the native path with an explicit recorded fallback; errors
are never treated as relevance scores. Every generated semantic token is chosen
by Granite's full-vocabulary argmax. There is no required UNKNOWN spelling, colour
list or code-generated answer. The pilot is retained as accepted output only when
the native path is used; a guided restart has a completely separate cache.

The existing R16 open-explicit system instruction is shared across every arm.
Each final has at most 32 tokens; the optional native pilot uses at most eight
additional discarded tokens. A gate can decide after an early EOS. It is therefore
a short buffered generation decision, not a mechanism that changes already emitted
user-visible tokens. It is invoked once per question, not inside every layer.

The custom SDPA callback receives post-rotary Q/K/V and adjusts only source-key
logits in eleven previously selected query heads across nine Granite layers.
The serial scope binds exact input IDs/cache positions and restores the original
attention dispatcher on all exits. This is a research implementation, not a
thread-safe service or vLLM extension. No Granite/Jev weights are trained.

For the mass-preserving variant, with original logits l, relevance bias b and
the set S of all evidence tokens, use `c = LSE(l[S]+b[S]) - LSE(l[S])` and add
`b[k]-c` for each k in S. Other logits are unchanged. The evidence partition,
its softmax mass and all outside probabilities are preserved for those Q/K.
The within-evidence distribution and attention output can change. Conservation
does not mean no downstream effect. Prefill-only guidance includes first-token
prediction and can leave changed cached question representations for later tokens.

The benefit gate fits one threshold, direction and feature on development outcomes.
It does not train the language model. Its features can fail to predict treatment
benefit; confidence is not a correctness guarantee. Fresh held-out comparisons
determine whether the gate saves calls and preserves quality.

Benefits/costs are paired by authored world or external question. All controls
receive the full original evidence. Static controls reuse exact Jev receipts,
while the benefit-gate arm always executes first on each test input. Report actual
HTTP attempts, logical calls for standalone deployment, discarded pilot work and
uncached latency estimates separately. Hosted latency is not a colocation result.
