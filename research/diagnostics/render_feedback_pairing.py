"""Render the audited R30 report; plotting requires the optional Matplotlib package."""

import argparse
import json
from pathlib import Path


def render(report):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    result = json.loads((report / "analysis.json").read_text())
    if not result["passed"] or result["outputs"] != 7680 or result["requests"] != 384:
        raise ValueError("A complete audited R30 result is required")
    labels = {
        "native": "Original Granite",
        "blind": "Blind repair",
        "live": "Paired Jev",
        "mean": "Repeated mean",
        "permutation_mean": "Within-draft permutations",
        "donor": "Same-family donor",
        "constant": "Constant 0.5",
        "type_only": "Room-type rule",
        "oracle": "Oracle (nondeployable)",
        "scalar_trained": "Separately trained scalar",
    }
    fig, (left, right) = plt.subplots(1, 2, figsize=(12, 5.6), layout="constrained")
    scores = [100 * result["scores"][arm]["accuracy"] for arm in labels]
    y = list(range(len(labels)))
    colors = ["#16806a" if arm == "live" else "#7689a3" for arm in labels]
    left.barh(y, scores, color=colors)
    left.set_yticks(y, labels.values())
    left.invert_yaxis()
    left.set_xlim(0, max(scores) * 1.3)
    for pos, score in zip(y, scores, strict=True):
        left.text(score + 0.4, pos, f"{score:.2f}%", va="center", fontsize=9)
    left.set_xlabel("All three answers correct (%)")
    left.set_title("384 fresh authored worlds")
    comparisons = ("native", "mean", "permutation_mean")
    for pos, arm in enumerate(comparisons):
        row = result["contrasts"]["live-minus-" + arm]
        low, high = row["family_ci_pp"]
        point = row["delta_pp"]
        right.errorbar(
            point,
            pos,
            xerr=[[point - low], [high - point]],
            fmt="o",
            color="#16806a",
            capsize=5,
        )
    right.axvline(0, color="#929292", linewidth=1)
    right.set_yticks(range(3), ["Paired − " + labels[a].lower() for a in comparisons])
    right.invert_yaxis()
    right.set_ylim(2.6, -0.6)
    right.set_xlabel("Paired accuracy difference (percentage points)")
    right.set_title("Three primary contrasts\n98.3333% within-family bootstrap intervals")
    for axis in (left, right):
        axis.spines[["top", "right"]].set_visible(False)
        axis.grid(axis="x", alpha=0.15)
        axis.set_axisbelow(True)
    fig.suptitle("R30: fixed checkpoints, no new training; two-seed means", fontsize=12)
    output = report / "figures"
    output.mkdir(exist_ok=True)
    fig.savefig(output / "r30-feedback-pairing.svg")
    fig.savefig(output / "r30-feedback-pairing.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    render(parser.parse_args().report)
