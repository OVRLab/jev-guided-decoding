# R17 prospective offline routing control

Registered 2026-09-22 after live development began, before policy selection or
held-out inference/aggregate inspection. This adds no generation, Jev call or
change to the frozen main study. The original random-gate arm remains intact.

The live random gate uses the benefit gate's **balanced development** call rate.
Its realized held-out call count need not equal the benefit gate's count, especially
if call rates differ between authored and Hotpot inputs. Calling it perfectly
budget-matched on test would be inaccurate. Add the following separate offline
counterfactual, clearly labeled as such.

The main audit checks that a gated final exactly equals native when skipped and
the selected always-guided final when called (including a common receipt failure's
native fallback). With these verified branch identities, every test case has both
potential branch outcomes. Within each domain, let `d_i = guided_quality_i -
native_quality_i`, `c_i` be the benefit gate's actual 0/1 call decision, and
`r = mean(c_i)`. Uniform random routing with exactly the same number of calls has
expected improvement `r * mean(d_i)`. The measured gate's improvement is
`mean(c_i * d_i)`. Their difference is the gate's routing value at that call count.

Report the observed gate quality, expected random quality, routing-value difference
and exploratory 95% paired bootstrap interval (10,000 world/question resamples).
Recompute the call fraction within each resample and keep light/heavy contexts
together. Also report a one-sided 10,000-permutation random-assignment tail
probability, fixing the domain's actual number of called contexts; this is an
exploratory routing diagnostic, not one of the four primary tests.

This matches **numbers of calls**, not request tokens, latency, or money; contexts
have different sizes and pilot lengths. It is an expected randomized policy,
not another observed model run or an extra independent dataset. It cannot rescue
a quality regression against native/always-guided or establish a speedup by itself.

Implementation lives in `research/diagnostics/selective_routing.py`. Test the
control on independent small beneficial/harmful fixtures and degenerate all/none
routing before analyzing the completed study. Preserve the original raw results
and main analysis unchanged.
