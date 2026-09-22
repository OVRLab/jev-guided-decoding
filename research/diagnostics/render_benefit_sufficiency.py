"""Render R19's audited controls and descriptive answerability groups without inference."""

import argparse
import json
from pathlib import Path


def main():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads((args.report / "independent-analysis.json").read_text())
    output = args.report / "figures"
    output.mkdir(exist_ok=True)
    arms = ["native", "relevance", "sufficiency", "dual", "benefit_gate", "random_gate", "r18_gate"]
    labels = [
        "Native",
        "Relevance",
        "Sufficiency",
        "Dual always",
        "Benefit gate",
        "Random gate",
        "R18 gate",
    ]
    colors = ["#64748b", "#0284c7", "#d97706", "#059669", "#7c3aed", "#cbd5e1", "#e879a5"]
    domains = [
        ("synthetic", "Authored accuracy"),
        ("hotpot", "HotpotQA answer F1"),
        ("squad2", "SQuAD2 adapted F1"),
    ]
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )

    def save(fig, name):
        for suffix in ("png", "svg", "pdf"):
            fig.savefig(output / f"{name}.{suffix}", dpi=180, bbox_inches="tight")
        plt.close(fig)

    controls_path = args.report / "controls-analysis.json"
    controls = json.loads(controls_path.read_text())["domains"] if controls_path.exists() else None
    quality_arms = arms + (["instruction_always", "shuffled_sufficiency"] if controls else [])
    quality_labels = labels + (["Static instruction", "Shuffled sufficiency"] if controls else [])
    quality_colors = colors + (["#334155", "#a16207"] if controls else [])

    def score(domain, arm):
        return data["domains"][domain]["arms"][arm] if arm in arms else controls[domain][arm]

    fig, axes = plt.subplots(1, 3, figsize=(15, 6.2), layout="constrained")
    for ax, (domain, title) in zip(axes, domains, strict=True):
        values = [100 * score(domain, a)["quality"] for a in quality_arms]
        bars = ax.barh(quality_labels, values, color=quality_colors)
        ax.bar_label(bars, fmt="%.2f", padding=3)
        ax.invert_yaxis()
        ax.set_xlim(0, max(60, max(values) + 10))
        ax.set_title(title)
        ax.set_xlabel("Score (%)")
    fig.suptitle(
        "R19 • Main study and separately registered controls\n"
        "Different domain metrics; these scores are not pooled",
        fontsize=14,
    )
    save(fig, "quality-controls")

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.8), layout="constrained")
    for ax, (domain, title) in zip(axes, domains, strict=True):
        group = data["domains"][domain]
        values = [100 * group["arms"][a]["calls"] / group["count"] for a in arms]
        bars = ax.barh(labels, values, color=colors)
        ax.bar_label(bars, fmt="%.1f", padding=3)
        ax.invert_yaxis()
        ax.set_xlim(0, 115)
        ax.set_title(title)
        ax.set_xlabel("Inputs requesting Jev (%)")
    fig.suptitle(
        "R19 • Standalone request fractions\n"
        "Benefit-gate requests are physical; controls reuse exact joint receipts",
        fontsize=14,
    )
    save(fig, "request-fractions")

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), layout="constrained")
    subset = ["native", "relevance", "sufficiency", "dual", "benefit_gate"]
    subgroup_labels = ["Native", "Relevance", "Sufficiency", "Dual", "Benefit gate"]
    if controls:
        subset.append("instruction_always")
        subgroup_labels.append("Static instruction")
    for ax, (domain, title) in zip(axes, [domains[0], domains[2]], strict=True):
        x = np.arange(len(subset))
        for offset, group, color in [(-0.2, "answerable", "#0284c7"), (0.2, "missing", "#d97706")]:
            values = [100 * score(domain, a)["subgroups"][group]["quality"] for a in subset]
            bars = ax.bar(x + offset, values, 0.38, label=group.title(), color=color)
            ax.bar_label(bars, fmt="%.1f", padding=2, fontsize=8)
        ax.set_xticks(x, subgroup_labels, rotation=20)
        ax.set_ylim(0, 110)
        ax.set_ylabel("Score (%)")
        ax.set_title(title)
        ax.legend(loc="upper right")
    fig.suptitle(
        "R19 • Descriptive answerability groups\n"
        "No new subgroup significance tests; missing-evidence scores measure recognized abstention",
        fontsize=13,
    )
    save(fig, "answerability")
    print(json.dumps({"figures": 3, "formats": ["png", "svg", "pdf"]}))


if __name__ == "__main__":
    main()
