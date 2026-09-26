"""Render audited R29 results; requires an optional Matplotlib environment."""

import argparse
import json
from pathlib import Path


def render(source, destination):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    data = json.loads(source.read_text())
    if not data.get("passed") or data.get("outputs") != 2144 or data.get("requests") != 256:
        raise ValueError("A complete audited R29-A analysis is required")
    destination.mkdir(parents=True, exist_ok=True)
    arms = ["native", "blind", "constant", "scalar", "structured", "text", "oracle"]
    labels = [
        "Original Granite",
        "Untrained repair",
        "Constant feedback",
        "Scalar Jev feedback",
        "Structured Jev feedback",
        "Text Jev feedback",
        "Oracle (not deployable)",
    ]
    values = [100 * data["scores"][arm]["accuracy"] for arm in arms]
    colors = ["#59616a", "#8b9299", "#8b9299", "#5680a1", "#176e5b", "#5680a1", "#b49871"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.4), gridspec_kw={"width_ratios": [1.2, 1]})
    axes[0].barh(labels, values, color=colors, height=0.65)
    axes[0].invert_yaxis()
    axes[0].set_xlim(0, 108)
    axes[0].set_xticks([0, 25, 50, 75, 100])
    axes[0].set_xlabel("All three answers correct (%)")
    axes[0].set_title("Raw repair candidates")
    for i, value in enumerate(values):
        axes[0].text(value + 1.1, i, f"{value:.1f}", va="center", fontsize=9)
    comparisons = ["native", "constant", "scalar", "shuffled", "text"]
    comparison_labels = [
        "Original Granite",
        "Constant feedback",
        "Scalar feedback",
        "Shuffled feedback",
        "Text feedback",
    ]
    for i, baseline in enumerate(comparisons):
        row = data["contrasts"][f"structured-minus-{baseline}"]
        lo, hi = row["ci95_pp"]
        axes[1].plot([lo, hi], [i, i], color="#176e5b", linewidth=2)
        axes[1].plot(row["delta_pp"], i, "o", color="#176e5b")
    axes[1].axvline(0, color="#9da2a7", linewidth=1, linestyle="--")
    axes[1].set_yticks(range(len(comparisons)), comparison_labels)
    axes[1].invert_yaxis()
    axes[1].set_xlabel("Structured minus comparator (percentage points)")
    axes[1].set_title("Paired effects, exploratory 95% intervals")
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="x", alpha=0.15)
        ax.set_axisbelow(True)
    fig.suptitle("R29-A: localized correction on authored tracking tasks", fontsize=14)
    fig.text(
        0.5,
        0.025,
        "96 held-out worlds; trained conditions averaged over two seeds. "
        "Not a public benchmark or larger-model comparison.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.06, 1, 0.94), w_pad=2.5)
    for extension in ("svg", "png"):
        fig.savefig(destination / f"r29-correction.{extension}", dpi=180)
    svg = destination / "r29-correction.svg"
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    render(args.analysis, args.destination)
