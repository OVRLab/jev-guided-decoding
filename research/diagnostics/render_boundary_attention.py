"""Render R18 scientific PNG/SVG/PDF figures from audited report JSON; no inference."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
NAMES = {
    "native": "Granite",
    "always": "Always Jev",
    "boundary_never": "Boundary, never",
    "boundary_always": "Boundary, always",
    "boundary_gate": "Boundary gate",
    "boundary_random": "Boundary random",
    "pilot_gate": "Pilot gate",
    "lexical": "Lexical",
    "shuffled": "Shuffled Jev",
}
COLORS = {
    "native": "#667085",
    "always": "#175CD3",
    "boundary_never": "#98A2B3",
    "boundary_always": "#84ADFF",
    "boundary_gate": "#C65D15",
    "boundary_random": "#9E77ED",
    "pilot_gate": "#0E9384",
    "lexical": "#C5A044",
    "shuffled": "#C98C92",
}
DOMAINS = {"synthetic": "Authored accuracy", "hotpot": "HotpotQA F1", "squad2": "SQuAD2 adapted F1"}


def render(report):
    a = json.loads((report / "independent-analysis.json").read_text())
    d = json.loads((report / "output-diagnostics.json").read_text())
    if not a["audit_passed"] or not d["audit_passed"]:
        raise ValueError("Audited artifacts required")
    figures = report / "figures"
    figures.mkdir(exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": 150,
            "savefig.dpi": 180,
            "svg.hashsalt": "r18-boundary-attention",
        }
    )

    def save(fig, name):
        for suffix in ("png", "svg", "pdf"):
            fig.savefig(figures / f"{name}.{suffix}", bbox_inches="tight", facecolor="white")
        plt.close(fig)

    arms = list(NAMES)
    lookup = {(r["domain"], r["arm"]): r for r in a["summaries"]}
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.8))
    for ax, domain in zip(axes, DOMAINS, strict=True):
        values = [100 * lookup[domain, arm]["quality"] for arm in arms]
        bars = ax.bar(range(len(arms)), values, color=[COLORS[arm] for arm in arms])
        ax.bar_label(bars, fmt="%.1f", padding=3, fontsize=8)
        ax.set_xticks(range(len(arms)), [NAMES[x] for x in arms], rotation=55, ha="right")
        ax.set_ylim(0, max(60, max(values) + 10))
        if domain != "hotpot":
            ax.axhline(50, color="#475467", linestyle="--", linewidth=1)
            ax.text(8.4, 51.2, "Constant abstention: 50%", ha="right", fontsize=8)
        ax.set_title(DOMAINS[domain])
        ax.set_ylabel("Score (%)")
        ax.grid(axis="y", alpha=0.15)
        ax.set_axisbelow(True)
    fig.suptitle("R18: all nine held-out controls; metrics differ by domain", fontsize=15)
    fig.tight_layout()
    save(fig, "quality-controls")

    primary = [r for r in a["routing"] if r["primary"]]
    fig, ax = plt.subplots(figsize=(11.5, 4.3))
    for i, row in enumerate(primary):
        middle, (low, high) = 100 * row["difference"], [100 * x for x in row["interval"]]
        ax.errorbar(
            middle,
            i,
            xerr=[[max(0, middle - low)], [max(0, high - middle)]],
            fmt="o",
            color=COLORS["boundary_gate"],
            capsize=5,
        )
        ax.annotate(
            f"{middle:+.2f} [{low:+.2f}, {high:+.2f}] pp; {100 * row['call_fraction']:.1f}% calls",
            (high, i),
            xytext=(10, 0),
            textcoords="offset points",
            va="center",
            fontsize=9,
        )
    ax.set_yticks(range(len(primary)), [DOMAINS[r["domain"]] for r in primary])
    ax.invert_yaxis()
    ax.axvline(0, color="#667085", linewidth=1)
    ax.set_xlabel("Quality over expected random guidance at the same test call count (pp)")
    low = min(100 * r["interval"][0] for r in primary)
    high = max(100 * r["interval"][1] for r in primary)
    ax.set_xlim(low - 1, high + max(8, (high - low) * 1.2))
    ax.set_ylim(2.6, -0.6)
    ax.set_title("Primary routing-value contrasts: individual 98.333% cluster intervals")
    fig.tight_layout()
    save(fig, "routing-value")

    subset = ["native", "always", "boundary_gate", "boundary_random", "pilot_gate"]
    fig, axes = plt.subplots(1, 3, figsize=(17.5, 5.3))
    for ax, domain in zip(axes, DOMAINS, strict=True):
        ax.plot(
            [0, 100],
            [100 * lookup[domain, x]["quality"] for x in ("native", "always")],
            "--",
            color="#98A2B3",
            linewidth=1,
            label="Expected random use",
        )
        for i, arm in enumerate(subset):
            row = lookup[domain, arm]
            x, y = 100 * row["call_fraction"], 100 * row["quality"]
            ax.scatter(x, y, s=60, color=COLORS[arm], zorder=3)
            offsets = [(8, -20), (-8, 14), (-8, 22), (8, -32), (8, 8)]
            if domain == "synthetic":
                offsets[3], offsets[4] = (-35, 16), (10, -18)
            elif domain == "hotpot":
                offsets[2] = (10, 18)
            else:
                offsets[2] = (15, 22)
            dx, dy = offsets[i]
            ax.annotate(
                NAMES[arm],
                (x, y),
                xytext=(dx, dy),
                ha="right" if dx < 0 else "left",
                textcoords="offset points",
                fontsize=8,
                arrowprops={"arrowstyle": "-", "color": "#98A2B3", "lw": 0.6},
            )
        ys = [100 * lookup[domain, arm]["quality"] for arm in subset]
        ax.set_ylim(max(0, min(ys) - 7), min(100, max(ys) + 7))
        ax.set_xlim(-8, 108)
        ax.set_xlabel("Questions requesting Jev (%)")
        ax.set_ylabel("Score (%)")
        ax.set_title(DOMAINS[domain])
        ax.grid(alpha=0.15)
        ax.legend(loc="lower right", fontsize=8)
    fig.suptitle("Quality and standalone logical requests; shared receipts are charged once")
    fig.tight_layout()
    save(fig, "quality-calls")

    timed = ["native", "boundary_never", "always", "boundary_always", "boundary_gate", "pilot_gate"]
    metrics = {
        "model_seconds": "Model time excluding provider wait",
        "estimated_uncached_first_token_seconds": "Uncached first-token proxy (estimate)",
        "estimated_uncached_wall_seconds": "Uncached elapsed (estimate)",
    }
    fig, axes = plt.subplots(3, 3, figsize=(17.5, 13))
    for row_axes, domain in zip(axes, DOMAINS, strict=True):
        for ax, (key, label) in zip(row_axes, metrics.items(), strict=True):
            stats = [lookup[domain, arm]["timings"][key] for arm in timed]
            ax.bar(range(len(timed)), [r["mean"] for r in stats], color=[COLORS[x] for x in timed])
            ax.scatter(
                range(len(timed)),
                [r["median"] for r in stats],
                marker="_",
                color="black",
                label="Median",
                zorder=3,
                s=110,
            )
            ax.scatter(
                range(len(timed)),
                [r["p95"] for r in stats],
                marker="D",
                color="#344054",
                label="p95",
                zorder=3,
                s=18,
            )
            ax.set_xticks(range(len(timed)), [NAMES[x] for x in timed], rotation=42, ha="right")
            ax.set_ylabel("Seconds per question; bars = mean")
            ax.set_title(f"{DOMAINS[domain]}\n{label}", fontsize=10)
            ax.set_ylim(bottom=0)
            ax.grid(axis="y", alpha=0.15)
            ax.set_axisbelow(True)
    axes[0, 0].legend(fontsize=8)
    fig.suptitle("Serial FP32 prototype timing; tokenization/loading excluded", fontsize=15)
    fig.tight_layout()
    save(fig, "timing")

    work = {
        "prefills": "Prefills per question",
        "processed_tokens": "Tokens processed per layer per question",
        "discarded_tokens": "Discarded pilot tokens per question",
    }
    fig, axes = plt.subplots(1, 3, figsize=(16.5, 5.8))
    work_arms = ["always", "boundary_gate", "pilot_gate"]
    x = np.arange(3)
    for ax, (key, label) in zip(axes, work.items(), strict=True):
        for j, arm in enumerate(work_arms):
            values = [lookup[dom, arm][key] / lookup[dom, arm]["cases"] for dom in DOMAINS]
            bars = ax.bar(
                x + (j - 1) * 0.25, values, width=0.24, color=COLORS[arm], label=NAMES[arm]
            )
            ax.bar_label(
                bars, fmt="%.2f" if key != "processed_tokens" else "%.0f", fontsize=8, padding=3
            )
        ax.set_xticks(x, ["Authored", "HotpotQA", "SQuAD2"], rotation=15)
        ax.set_ylabel(label)
        ax.margins(y=0.22)
        ax.grid(axis="y", alpha=0.15)
        ax.set_axisbelow(True)
    axes[0].legend(fontsize=8)
    fig.suptitle("Actual generation work; every layer counted, discarded pilot included")
    fig.tight_layout()
    save(fig, "generation-work")

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.3), sharey=True)
    for ax, domain in zip(axes, ("synthetic", "squad2"), strict=True):
        x = np.arange(2)
        for j, arm in enumerate(("native", "always", "boundary_gate")):
            values = [
                100 * lookup[domain, arm]["missing_subgroups"][str(v)]["quality"]
                for v in (False, True)
            ]
            bars = ax.bar(
                x + (j - 1) * 0.26, values, width=0.25, color=COLORS[arm], label=NAMES[arm]
            )
            ax.bar_label(bars, fmt="%.1f", padding=3, fontsize=9)
        ax.set_xticks(x, ["Answerable", "Missing / impossible"])
        ax.set_ylim(0, 100)
        ax.set_ylabel("Score (%)")
        ax.set_title(DOMAINS[domain])
        ax.grid(axis="y", alpha=0.15)
        ax.set_axisbelow(True)
    axes[0].legend(fontsize=9)
    fig.suptitle("Answerability groups; descriptive, no new significance tests")
    fig.tight_layout()
    save(fig, "answerability")

    desc = {(r["domain"], r["arm"]): r for r in d["diagnostics"]}
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.8), sharey=True)
    for ax, domain in zip(axes, DOMAINS, strict=True):
        cap = [100 * desc[domain, arm]["token_limit"] / desc[domain, arm]["cases"] for arm in arms]
        eos = [100 * desc[domain, arm]["eos"] / desc[domain, arm]["cases"] for arm in arms]
        ax.bar(range(len(arms)), eos, color="#84ADFF", label="EOS")
        ax.bar(range(len(arms)), cap, bottom=eos, color="#FDB022", label="32-token cap")
        ax.set_xticks(range(len(arms)), [NAMES[x] for x in arms], rotation=55, ha="right")
        ax.set_ylim(0, 105)
        ax.set_ylabel("Outputs (%)")
        ax.set_title(DOMAINS[domain])
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncols=2, fontsize=9)
    fig.suptitle("Termination is not correctness; all capped and empty outputs are retained")
    fig.tight_layout(rect=(0, 0.055, 1, 1))
    save(fig, "output-termination")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--report", type=Path, default=ROOT / "reports/2026-09-22-boundary-attention")
    render(p.parse_args().report)


if __name__ == "__main__":
    main()
