# R19 supplement: static instruction and shuffled sufficiency controls

Registered on 2026-09-22 while R19 fitting is running, before calibration selection
or any held-out generation/quality inspection. This supplement leaves the frozen
[R19 main protocol](benefit-sufficiency-plan.md), its seven arms, six primary
contrasts and all original results unchanged. It addresses a design limitation:
improving over native or relevance alone does not establish that semantic selection
of instruction steering is better than always emphasizing that instruction.

After all main outcomes finish, before aggregate inspection, run two additional
arms on the same 608 held-out inputs, using the calibration-selected instruction
strength, unchanged original prompts, checkpoint, precision and 32-token ceiling:

- **Instruction always:** every input receives the existing abstention-clause bias,
  with no source bias and no Jev request. A canned callback supplies the fixed
  control state; it is explicitly counted as a local callback, not a Jev call.
- **Shuffled sufficiency:** keep each question's original source relevance but
  transplant the sufficiency probability from another question in the same domain.
  Order IDs by SHA-256 of `r19-sufficiency-shuffle/` plus ID and rotate by one.
  This fixed bijection preserves the domain probability distribution and has no
  self donor. Neither ordering nor donor selection uses labels or grades. Apply
  the unchanged dual treatment. Reuse main-study receipts only; make no new API
  requests. If either required receipt failed, preserve native fallback and count
  it, without substituting another donor or requesting a replacement.

Granite owns every final token in both controls. The static control requires zero
external inference; the shuffled control is a causal diagnostic using prerecorded
Jev judgments, not a deployable semantic policy or freshly measured provider latency.
Do not interpret a canned callback as live Jev. Record own/donor receipt IDs and
applied probabilities explicitly. No labels/references enter generator callbacks.

Keep all 1,216 supplemental outcomes and independently reconstruct source/selection,
maps, tokens, work, receipt provenance, weights and grades. The deterministic
permutation and supplement code are frozen before its inference. Compare main
dual minus static and dual minus shuffled separately by domain with exploratory
95% paired cluster-bootstrap intervals. Preserve six main adjusted intervals and
do not promote a favorable supplement to a preregistered primary outcome. Report
constant abstention references, answerability groups, raw/adapted lexical metrics,
call costs and harms. The comparisons do not establish historical novelty.

Reuse the existing single L40S within the same $10 cloud/$2 API reservation and
$50 cumulative authorization; the supplement adds no paid Jev requests. Run only
after main completion, with a 90-minute local deadline, inside the existing six-hour
VM expiry. Retrieve and hash-verify both sets of artifacts, audit and delete owned
resources; preserve interrupted work without selective replay. No policy retuning
or test-dependent threshold choice is permitted.
