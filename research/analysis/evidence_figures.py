"""Standalone scientific figures from audited R14 artifacts; no model inference."""

import argparse
import hashlib
import json
from pathlib import Path


def render(results, output):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    output.mkdir(parents=True, exist_ok=False)
    ranking = json.loads((results / "head-ranking.json").read_text())
    policy = json.loads((results / "selected-policy.json").read_text())
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    artifacts = []

    def save(fig, name):
        for extension in ("png", "svg", "pdf"):
            path = output / f"{name}.{extension}"
            fig.savefig(path, dpi=180, bbox_inches="tight")
            if extension == "svg":
                path.write_text(
                    "\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n"
                )
            artifacts.append(path)
        plt.close(fig)

    values = np.zeros((40, 16))
    for row in ranking:
        values[tuple(row["head"])] = row["mean_logprob_change"]
    limit = max(abs(values.min()), abs(values.max()), 1e-6)
    fig, ax = plt.subplots(figsize=(8.2, 9))
    shown = ax.imshow(values, aspect="auto", cmap="RdBu_r", vmin=-limit, vmax=limit)
    for layer, head in policy["heads"]:
        ax.scatter(head, layer, s=100, facecolors="none", edgecolors="black", linewidths=1.2)
    ax.set(
        xticks=range(16),
        yticks=range(0, 40, 2),
        xlabel="Query head (zero based)",
        ylabel="Transformer layer (zero based)",
        title="Oracle evidence: individual-head profiling\n"
        "24 development worlds; circles mark selected heads",
    )
    fig.colorbar(
        shown,
        ax=ax,
        label="Mean change in reference log probability (seven-label grammar)",
        shrink=0.8,
    )
    fig.tight_layout()
    save(fig, "head-profile")

    configurations = policy["all_configurations"]
    labels = ["Native"] + [
        f"{c['count']} head{'s' if c['count'] != 1 else ''}\nln({round(np.exp(c['strength']))})"
        for c in configurations
    ]
    scores = [policy["native"]["accuracy"]] + [c["accuracy"] for c in configurations]
    colors = ["#526679"] + [
        "#bf9254"
        if c["count"] == policy["count"] and c["strength"] == policy["strength"]
        else "#cad1d8"
        for c in configurations
    ]
    fig, ax = plt.subplots(figsize=(12.5, 4.6))
    bars = ax.bar(range(len(scores)), np.array(scores) * 100, color=colors)
    for bar, score in zip(bars, scores, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            score * 100 + 1,
            f"{score * 100:.1f}",
            ha="center",
            fontsize=9,
        )
    ax.set(
        xticks=range(len(labels)),
        xticklabels=labels,
        ylim=(0, 108),
        ylabel="Accuracy (%)",
        title="Oracle evidence: calibration, not held-out performance\n"
        "72 worlds, two context conditions; gold bar is the selected configuration",
    )
    ax.axhline(policy["native"]["accuracy"] * 100, color="#526679", linestyle="--", linewidth=0.8)
    fig.tight_layout()
    save(fig, "oracle-calibration")

    test_file = results / "test-summary.json"
    if test_file.exists():
        summary = json.loads(test_file.read_text())
        names = ["native", "zero", "oracle", "jev", "shuffled", "lexical", "random_heads", "prompt"]
        labels = [
            "Granite",
            "Zero bias",
            "Oracle*",
            "Jev attention",
            "Shuffled",
            "Lexical",
            "Random heads",
            "Prompt focus",
        ]
        accuracy = [summary["arms"][name]["accuracy"] * 100 for name in names]
        fig, ax = plt.subplots(figsize=(10.5, 4.8))
        bars = ax.bar(
            labels,
            accuracy,
            color=[
                "#6c7987",
                "#bbc4cc",
                "#bf9254",
                "#7040a0",
                "#bbc4cc",
                "#bbc4cc",
                "#bbc4cc",
                "#bbc4cc",
            ],
        )
        for bar, score in zip(bars, accuracy, strict=True):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                score + 1.2,
                f"{score:.2f}%",
                ha="center",
                fontsize=9,
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.5},
            )
        ax.set(
            ylim=(0, 108),
            ylabel="Constrained generated-answer accuracy (%)",
            title="Held-out evidence-attention comparison\n"
            "360 worlds, two contexts; *oracle uses privileged span annotations",
        )
        ax.tick_params(axis="x", rotation=15)
        ax.axhline(50, color="#333333", linestyle=":", linewidth=0.8)
        ax.text(
            0.99,
            0.88,
            "Always UNKNOWN: 50% (post-hoc descriptive reference)",
            transform=ax.transAxes,
            ha="right",
            fontsize=9,
        )
        fig.tight_layout()
        save(fig, "test-accuracy")

        contrasts = summary["comparisons"]
        names = ["native", "shuffled", "lexical", "prompt"]
        fig, ax = plt.subplots(figsize=(8.8, 4.0))
        for i, name in enumerate(names):
            row = contrasts[name]
            point = row["difference"] * 100
            low, high = [x * 100 for x in row["interval"]]
            ax.errorbar(
                point, i, xerr=[[point - low], [high - point]], fmt="o", color="#7040a0", capsize=4
            )
            ax.text(
                high + 0.4, i, f"{point:+.2f} [{low:+.2f}, {high:+.2f}]", va="center", fontsize=9
            )
        low = min(r["interval"][0] * 100 for r in contrasts.values())
        high = max(r["interval"][1] * 100 for r in contrasts.values())
        ax.set(
            xlim=(min(-1, low) - 2, max(1, high) + 15),
            yticks=range(4),
            yticklabels=["Jev - " + n for n in names],
            xlabel="Accuracy difference (percentage points)",
            title="Primary paired contrasts\n"
            "98.75% world-bootstrap intervals; nominal 95% family coverage",
        )
        ax.axvline(0, color="#555555", linestyle="--", linewidth=0.9)
        ax.invert_yaxis()
        fig.tight_layout()
        save(fig, "primary-contrasts")

    sources = [results / "head-ranking.json", results / "selected-policy.json"]
    if test_file.exists():
        sources.append(test_file)
    provenance = dict(
        versions={"matplotlib": matplotlib.__version__, "numpy": np.__version__},
        source_hashes={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        renderer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        artifacts={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in artifacts},
    )
    (output / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(json.dumps({"figures": len(artifacts), "output": str(output)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    render(args.results, args.output)
