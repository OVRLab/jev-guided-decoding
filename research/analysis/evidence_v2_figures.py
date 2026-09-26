"""Standalone R15 scientific figures from audited, frozen result artifacts."""

import argparse
import hashlib
import json
from pathlib import Path


def render(results, diagnostics, output):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.patches import Rectangle

    output.mkdir(parents=True, exist_ok=False)

    def load(path):
        return json.loads(path.read_text())

    selection = load(results / "selected-policy.json")
    test = load(results / "test-summary.json")
    diag = load(diagnostics)
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    artifacts = []

    def save(fig, name):
        for extension in ("png", "svg", "pdf"):
            p = output / f"{name}.{extension}"
            fig.savefig(p, dpi=180, bbox_inches="tight")
            if extension == "svg":
                p.write_text("\n".join(line.rstrip() for line in p.read_text().splitlines()) + "\n")
            artifacts.append(p)
        plt.close(fig)

    fig, axes = plt.subplots(2, 3, figsize=(10, 7), layout="constrained")
    candidates = selection["candidates"]
    counts = [1, 2, 4, 8, 12]
    factors = [4, 8, 16]
    vmin = min(r["accuracy"] for r in candidates) * 100
    vmax = max(r["accuracy"] for r in candidates) * 100
    for qi, scope in enumerate(("question", "answer")):
        for mi, mapping in enumerate(("soft", "hard50", "hard80")):
            ax = axes[qi, mi]
            matrix = np.zeros((5, 3))
            indexed = {}
            for r in candidates:
                p = r["policy"]
                if p["scope"] == scope and p["mapping"] == mapping:
                    i = counts.index(p["count"])
                    j = factors.index(round(np.exp(p["strength"])))
                    matrix[i, j] = r["accuracy"] * 100
                    indexed[i, j] = r
            shown = ax.imshow(matrix, vmin=vmin, vmax=vmax, cmap="viridis", aspect="auto")
            for (i, j), r in indexed.items():
                label = f"{matrix[i, j]:.1f}" + (" ×" if not r["eligible"] else "")
                ax.text(
                    j,
                    i,
                    label,
                    ha="center",
                    va="center",
                    fontsize=9,
                    color="white" if matrix[i, j] < (vmin + vmax) / 2 else "black",
                )
                if r["policy"] == selection["selected"]["policy"]:
                    ax.add_patch(
                        Rectangle(
                            (j - 0.48, i - 0.48),
                            0.96,
                            0.96,
                            fill=False,
                            edgecolor="#f7b43b",
                            linewidth=3,
                        )
                    )
            ax.set(
                title=f"{scope} queries · {mapping}",
                xticks=range(3),
                xticklabels=["ln(4)", "ln(8)", "ln(16)"],
                yticks=range(5),
                yticklabels=counts,
                xlabel="Strength",
                ylabel="Selected head count",
            )
    fig.colorbar(shown, ax=axes, label="Development accuracy (%)", shrink=0.8)
    fig.suptitle(
        "Development search: 96 worlds, two contexts (not held-out)\n"
        "Gold outline: selected policy; ×: fails a development harm limit",
        fontsize=13,
    )
    save(fig, "development-grid")

    names = [
        "native",
        "r14",
        "r15",
        "lexical",
        "prompt",
        "shuffled",
        "oracle",
        "zero",
        "mapping_only",
        "heads_only",
        "strength_only",
        "scope_only",
    ]
    labels = [
        "Native Granite",
        "Previous Jev (R14)",
        "Refined Jev (R15)",
        "Lexical attention",
        "Jev prompt highlighting",
        "Shuffled Jev scores",
        "Oracle evidence*",
        "Zero bias",
        "Mapping only",
        "Heads only",
        "Strength only",
        "Query scope only",
    ]
    values = [test["arms"][name]["accuracy"] * 100 for name in names]
    colors = ["#6c7987", "#3877ac", "#7040a0"] + ["#bac4ce"] * 3 + ["#bf9254"] + ["#bac4ce"] * 5
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(labels, values, color=colors)
    for bar, value in zip(bars, values, strict=True):
        ax.text(
            value + 1, bar.get_y() + bar.get_height() / 2, f"{value:.2f}%", va="center", fontsize=9
        )
    ax.set(
        xlim=(0, 109),
        xlabel="Constrained generated-answer accuracy (%)",
        title="Primary test: 600 fresh worlds, two contexts\n"
        "*Oracle uses privileged source annotations",
    )
    ax.axvline(50, color="#555", linestyle=":", linewidth=0.8, label="Always UNKNOWN: 50%")
    ax.invert_yaxis()
    ax.legend(loc="lower right", fontsize=9)
    fig.tight_layout()
    save(fig, "primary-accuracy")

    fig, ax = plt.subplots(figsize=(9, 3))
    extrema = []
    for i, name in enumerate(("native", "r14")):
        c = test["primary"][name]
        point = c["difference"] * 100
        low, high = [v * 100 for v in c["interval"]]
        extrema += [low, high]
        ax.errorbar(
            point, i, xerr=[[point - low], [high - point]], fmt="o", color="#7040a0", capsize=5
        )
        ax.text(high + 0.5, i, f"{point:+.2f} [{low:+.2f}, {high:+.2f}]", va="center", fontsize=10)
    ax.set(
        yticks=[0, 1],
        yticklabels=["R15 − native", "R15 − R14"],
        xlabel="Accuracy difference (percentage points)",
        xlim=(min(0, min(extrema)) - 2, max(0, max(extrema)) + 17),
        ylim=(-0.5, 1.5),
        title="Primary paired contrasts\n"
        "97.5% world-bootstrap intervals; nominal 95% family coverage",
    )
    ax.axvline(0, color="#555", linestyle="--", linewidth=0.8)
    ax.invert_yaxis()
    fig.tight_layout()
    save(fig, "primary-contrasts")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    for missing, ax in zip((False, True), axes, strict=True):
        for mode, color, label in [
            ("native", "#6c7987", "Native"),
            ("r14", "#3877ac", "R14"),
            ("r15", "#7040a0", "R15"),
        ]:
            values = []
            for depth in range(1, 7):
                cell = diag["test" if depth <= 3 else "challenge"]["by_group"][mode][
                    f"depth-{depth}-missing-{missing}"
                ]
                values.append(100 * cell["correct"] / cell["total"])
            ax.plot(range(1, 7), values, "o-", color=color, label=label)
        ax.axvspan(3.5, 6.4, color="#eeeeee", zorder=-1)
        ax.set(
            title="Missing final link" if missing else "Answerable",
            xticks=range(1, 7),
            xlim=(0.6, 6.4),
            ylim=(-3, 103),
            xlabel="Chain depth",
        )
        ax.text(
            0.97,
            0.97,
            "Shaded: longer-chain challenge",
            ha="right",
            va="top",
            transform=ax.transAxes,
            fontsize=8,
        )
    axes[0].set_ylabel("Accuracy (%)")
    axes[1].legend(loc="best", fontsize=9)
    fig.suptitle(
        "Descriptive depth breakdown; the policy stays frozen for the challenge", fontsize=12
    )
    fig.tight_layout()
    save(fig, "depth-breakdown")

    names = ["mapping_only", "heads_only", "strength_only", "scope_only", "r15"]
    labels = [
        "Mapping only",
        "Heads only",
        "Strength only",
        "Query scope only",
        "Full selected policy",
    ]
    previous = test["arms"]["r14"]["accuracy"]
    points = [100 * (test["arms"][name]["accuracy"] - previous) for name in names]
    fig, ax = plt.subplots(figsize=(8, 3.5))
    bars = ax.barh(labels, points, color=["#bac4ce"] * 4 + ["#7040a0"])
    for b, value in zip(bars, points, strict=True):
        ax.text(
            value + (0.2 if value >= 0 else -0.2),
            b.get_y() + b.get_height() / 2,
            f"{value:+.2f}",
            ha="left" if value >= 0 else "right",
            va="center",
        )
    ax.set(
        xlim=(min(0, min(points)) - 3, max(0, max(points)) + 3),
        xlabel="Accuracy change versus R14 (percentage points)",
        title="Single-factor ablations on the primary test\n"
        "Descriptive point estimates; interactions are not decomposed",
    )
    ax.axvline(0, color="#555", linewidth=0.8)
    ax.invert_yaxis()
    fig.tight_layout()
    save(fig, "factor-ablations")

    inputs = [results / "selected-policy.json", results / "test-summary.json", diagnostics]
    provenance = dict(
        versions={"matplotlib": matplotlib.__version__, "numpy": np.__version__},
        source_hashes={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
        renderer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        artifacts={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in artifacts},
    )
    (output / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(json.dumps({"figures": len(artifacts), "output": str(output)}))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--results", type=Path, required=True)
    p.add_argument("--diagnostics", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    render(args.results, args.diagnostics, args.output)
