"""Render every registered R28 comparison after integrity admission and cleanup."""

import argparse
import json
import math
from pathlib import Path

LABELS = {
    "native": "Original Granite",
    "always_constant": "Always repair, constant signal",
    "jev_constant": "Jev selection, constant signal",
    "confidence_constant": "Native confidence, constant signal",
    "random_constant": "Random selection, constant signal",
    "jev_live": "Jev selection, live signal",
    "jev_shuffled": "Jev selection, shuffled signal",
}
PRIMARY = [
    ("jev_constant", "random_constant", "Selection: Jev − random"),
    ("jev_constant", "confidence_constant", "Selection: Jev − native confidence"),
    ("jev_live", "jev_constant", "Feedback: live − constant"),
    ("jev_live", "jev_shuffled", "Feedback: live − shuffled"),
]


def validate(analysis, cost):
    integrity = analysis.get("integrity", {})
    if (
        analysis.get("protocol") != "r28-routing-feedback-v1"
        or analysis.get("status") != "completed"
        or analysis.get("cases") != 539
        or not integrity.get("passed")
        or integrity.get("cases") != 539
        or integrity.get("outputs") != 1616
        or integrity.get("policies") != 7
        or set(analysis.get("scores", {})) != set(LABELS)
        or any(r["n"] != 539 for r in analysis["scores"].values())
        or integrity["jev"]["calls"] != 539
        or integrity["jev"]["unresolved"]
        or integrity["jev"]["max_charged"]
    ):
        raise ValueError("Report needs complete admitted R28 evidence")
    passed = []
    for a, b, _ in PRIMARY:
        contrast = analysis["contrasts"][a + "__" + b]
        expected = (
            contrast["ci9875_pp"][0] > 0
            and contrast["delta_pp"] >= 2
            and all(v > 0 for v in contrast["block_delta_pp"])
        )
        if contrast["practical_success"] is not expected:
            raise ValueError("Contrast decision disagrees with registered criteria")
        passed.append(expected)
    if analysis["selection_pass"] is not all(passed[:2]) or analysis["feedback_pass"] is not all(
        passed[2:]
    ):
        raise ValueError("Component decision disagrees with registered contrasts")
    for key in (
        "instance_terminated",
        "owned_disk_deleted",
        "owned_security_group_deleted",
        "owned_subnet_deleted",
    ):
        if cost.get(key) is not True:
            raise ValueError("Cleanup is not verified")
    monetary = [
        "prior_conservative_usd",
        "cumulative_cap_usd",
        "compute_usd",
        "api_usd",
        "preflight_usd",
        "operating_allowance_usd",
        "stage_conservative_usd",
        "cumulative_conservative_usd",
    ]
    if any(
        type(cost[k]) not in (int, float) or not math.isfinite(cost[k]) or cost[k] < 0
        for k in monetary
    ):
        raise ValueError("Invalid cost values")
    stage = sum(
        cost[k] for k in ("compute_usd", "api_usd", "preflight_usd", "operating_allowance_usd")
    )
    if (
        not math.isclose(stage, cost["stage_conservative_usd"], abs_tol=1e-9)
        or not math.isclose(
            cost["prior_conservative_usd"] + stage,
            cost["cumulative_conservative_usd"],
            abs_tol=1e-9,
        )
        or not math.isclose(cost["api_usd"], integrity["jev"]["usd"], abs_tol=1e-12)
    ):
        raise ValueError("Cost accounting does not reconcile")


def interval(pair):
    return f"[{pair[0]:+.2f}, {pair[1]:+.2f}]"


def results_section(analysis):
    rows = [
        "| Policy | Strict prompt success | Loose prompt success | Repairs |",
        "| --- | ---: | ---: | ---: |",
    ]
    for name, label in LABELS.items():
        r = analysis["scores"][name]
        rows.append(
            f"| {label} | {r['strict']}/539 ({r['strict_pct']:.2f}%) | "
            f"{r['loose']}/539 ({100 * r['loose'] / 539:.2f}%) | {r['repairs']} |"
        )
    rows.extend(
        [
            "",
            "| Primary contrast | Difference (pp) | 98.75% interval | "
            "Wins / losses | Blocks (pp) |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for a, b, label in PRIMARY:
        r = analysis["contrasts"][a + "__" + b]
        blocks = ", ".join(f"{v:+.2f}" for v in r["block_delta_pp"])
        rows.append(
            f"| {label} | {r['delta_pp']:+.2f} | {interval(r['ci9875_pp'])} | "
            f"{r['wins']} / {r['losses']} | {blocks} |"
        )
    selection = "met" if analysis["selection_pass"] else "not met"
    feedback = "met" if analysis["feedback_pass"] else "not met"
    rows.extend(
        [
            "",
            f"Selection criterion: **{selection}**. Internal-feedback criterion: **{feedback}**.",
            "Each component requires both relevant adjusted lower bounds above zero, both",
            "point estimates at least +2 pp, and a positive difference in each block.",
            "Failure to meet that criterion does not establish equivalence or rule out",
            "smaller benefits. All planned comparisons are retained.",
        ]
    )
    return "\n".join(rows)


def render(analysis, cost):
    validate(analysis, cost)
    integrity = analysis["integrity"]
    api = integrity["jev"]
    native = analysis["scores"]["native"]
    guided = analysis["scores"]["jev_live"]
    gain = analysis["contrasts"]["jev_live__native"]
    text = f"""# R28: repair selection versus internal feedback

Status: **completed and independently audited**, with all **539 eligible cases**,
**1,616 generated answers** and **539 successful Jev judgments** accounted for.
Granite generates every final answer token. This report concerns strict
instruction compliance, not general semantic correctness or a larger-model win.

Original Granite scores **{native["strict"]}/539 ({native["strict_pct"]:.2f}%)**;
Jev-selected live repair scores **{guided["strict"]}/539 ({guided["strict_pct"]:.2f}%)**.
Their difference is **{gain["delta_pp"]:+.2f} percentage points**, with a descriptive
95% paired interval **{interval(gain["ci95_pp"])}**. Attribution rests on the
registered control comparisons below, not this native comparison alone.

## Registered results

{results_section(analysis)}

## Design and scope

The [protocol](../../research/routing-feedback-plan-v1.md) was frozen before
inference at source `c418df6`. The
[manifest](../../research/protocols/routing-feedback-v1/manifest.json)
binds data, source, model, evaluator and checkpoint. Google Research IFEval has
541 original cases; keys 1122 and 1129 were excluded prospectively because their
punctuation parameters trigger random letter substitution in the unchanged
upstream checker. The denominator is 539 eligible cases, not an official full
541-case score. No exact or five-word-shingle near overlap was found with 2,040
unique prior project prompts; pretraining exposure and semantic overlap are not
excluded by that check.

The fixed rank-64 residual adapter has 262,144 parameters and acts after
zero-indexed decoder block 19. Original Granite 4.0-1B weights are frozen. One Jev
probability per native answer selects repairs and/or scales the branch during
second-pass generation. Jev is not queried every layer or token and supplies no
textual correction. Original prompt/draft token IDs are preserved; each repair
uses a fresh cache. All arms use FP32, greedy decoding and a 2,048-token ceiling.

Two fixed hash-balanced blocks contain 270 and 269 cases. Each selector chooses
135 and 134 repairs. Jev ranks by lowest compliance probability; native confidence
ranks by lowest mean generated-token log probability; random uses seed 2801.
The constant-signal potential outcome is generated on every case, while live and
shuffled outcomes are generated on the 269 Jev-selected cases. Shuffling preserves
the selected score distribution exactly within each block and forbids self-donors.

These policies reuse freshly collected deterministic potential outcomes; they are
not independently measured deployment latency or API-savings experiments. The
study called Jev on every native answer. Confidence/random/always-constant policies
have no inference-time Jev dependency but share a checkpoint trained using Jev
judgments in R25. They do not establish Jev-free training performance.

Twenty thousand paired, block-stratified bootstrap draws use seed 2800. The four
primary comparisons use 98.75% intervals; native comparisons use descriptive 95%
intervals. Inference conditions on this selection/donor assignment. Blocks are
consistency checks, not independent trained-model replications. Equal repair
counts and token ceilings do not imply equal realized computation.

## Work and incomplete answers

| Policy | Empty | Length stops | Generated tokens* | Processed slots* | Seconds* |
| --- | ---: | ---: | ---: | ---: | ---: |
"""
    for name, label in LABELS.items():
        r = analysis["scores"][name]
        text += (
            f"| {label} | {r['empty']} | {r['length_stops']} | "
            f"{r['attributed_generated_tokens']:,} | {r['attributed_processed_slots']:,} | "
            f"{r['attributed_generation_seconds']:.2f} |\n"
        )
    random = analysis["random_100_seeds"]
    total = cost["cumulative_conservative_usd"]
    cap = cost["cumulative_cap_usd"]
    text += f"""
* Policy work attribution includes native generation plus that policy's selected
repair generations. It excludes loading, warm-up, hosted Jev and orchestration;
reused times do not constitute separate policy latency measurements. Whole-study
collection produced **{integrity["generated_tokens"]:,} tokens**, with
**{analysis["total_collected_generation_seconds"]:.2f} generation seconds**.
The counterfactual collection cost is greater than any single selective policy.

The registered secondary 100-seed random-selection sensitivity gives
{random["min_correct"]}–{random["max_correct"]} strict successes, mean
{random["mean_correct"]:.2f}; the primary random seed remains unchanged. No near
overlap cases were flagged, so that sensitivity uses the same cohort. Loose and
instruction-level scores are in the [complete analysis](replay/analysis.json);
they do not replace the registered strict primary outcome.

## Integrity, cost and resources

The independent audit covers exact prompt/repair prefixes and decoded final-token
paths, stopping decisions, native likelihoods, hook positions/scalars, donors,
allocation, complete job/work records, model bindings, unchanged base weights and
all provider request/response/usage receipts. The pinned original checker runs
locally after admission; references and checker metadata were absent on the GPU.
The checker passed 48 upstream tests and 12 strict pass/fail/empty fixtures before
inference. Numerical public replay reconstructs all seven policy scores and ten
paired contrasts without new inference or API calls.

Jev reports **{api["charged_tokens"]:,} charged input tokens**, **${api["usd"]:.8f}**,
with zero unresolved or maximum-charged requests. A separate successful preflight
cost ${cost["preflight_usd"]:.9f}. The AWS NVIDIA L4 instance was terminated after a
fresh exact-inventory/hash backup; its disk, security group and owned temporary
subnet are verified deleted. The existing default VPC was retained.

Compute is estimated at **${cost["compute_usd"]:.4f}** using the verified Frankfurt
on-demand rate of $1.0064/hour and a conservative lifetime through cleanup. The
additional **${cost["operating_allowance_usd"]:.2f}** retains reserved disk, public-IP,
egress and contingency allowances rather than assuming unbilled usage is zero.
The resulting stage estimate is **${cost["stage_conservative_usd"]:.4f}** and
cumulative estimate **${total:.2f} / ${cap:.0f}**.
These are conservative accounting estimates, not invoices; final tax and network
charges remain unconfirmed. See [cost and cleanup summary](cost-and-cleanup.json).

## Reproducibility and interpretation

The [numeric replay](replay/) contains case-level boolean outcomes, fixed policy
allocation, the complete analysis and file hashes. It excludes questions,
generated answer strings/token IDs, API payloads and credentials. This supports
statistical replay; it does not replace independent response grading or reproduce
the private raw-token integrity audit. Use the
[reproduction guide](../../research/routing-feedback-reproduction.md) for acquisition,
a deliberate newly budgeted run, audit, grading and export.

The [focused manuscript](../../research/manuscript.md) places these results beside
[R27's complete Granite comparisons](../2026-09-25-completed-granite/README.md).
This study tests one adapter, backbone, layer and task family. It does not identify
an optimal insertion point or establish broad superiority, parameter efficiency,
colocated serving speed, or a novel general model architecture. The ten-benchmark
and larger-model objective remains unachieved. No additional architecture sweep,
model release or paper submission follows automatically from these results.
"""
    return text


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    for flag in ("analysis", "cost", "output"):
        p.add_argument("--" + flag, type=Path, required=True)
    args = p.parse_args()
    content = render(json.loads(args.analysis.read_text()), json.loads(args.cost.read_text()))
    with args.output.open("x") as stream:
        stream.write(content)
