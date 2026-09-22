"""Render standalone R17 scientific figures from the audited, published JSON only."""

import argparse
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
NAMES = {
    "native": "Granite",
    "r16": "R16 static",
    "mass_all": "Conserve, all tokens",
    "always": "Selected, always",
    "uncertainty_gate": "Uncertainty gate",
    "benefit_gate": "Benefit gate",
    "random_gate": "Random gate",
    "lexical": "Lexical relevance",
    "shuffled": "Shuffled relevance",
}
COLORS = {
    "native": "#667085",
    "always": "#175CD3",
    "benefit_gate": "#C65D15",
    "uncertainty_gate": "#0E9384",
    "mass_all": "#6941C6",
}


def render(report):
    a = json.loads((report / "independent-analysis.json").read_text())
    routing = json.loads((report / "routing-analysis.json").read_text())
    if not a["audit_passed"] or not routing["audit_passed"]:
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
        }
    )

    def save(fig, name):
        for suffix in ("png", "svg", "pdf"):
            fig.savefig(figures / f"{name}.{suffix}", bbox_inches="tight", facecolor="white")
        plt.close(fig)

    arms = list(NAMES)
    lookup = {(r["domain"], r["arm"]): r for r in a["summaries"]}
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.6), sharey=True)
    for ax, domain in zip(axes, ("synthetic", "hotpot"), strict=True):
        values = [100 * lookup[domain, arm]["quality"] for arm in arms]
        bars = ax.bar(range(len(arms)), values, color=[COLORS.get(arm, "#98A2B3") for arm in arms])
        ax.bar_label(bars, fmt="%.1f", padding=3, fontsize=9)
        ax.set_xticks(range(len(arms)), [NAMES[x] for x in arms], rotation=48, ha="right")
        ax.set_ylim(0, max(55, max(values) + 10))
        ax.set_title(
            "Authored free-text accuracy" if domain == "synthetic" else "HotpotQA answer F1"
        )
        ax.set_ylabel("Score (%)")
        ax.grid(axis="y", alpha=0.15)
        ax.set_axisbelow(True)
    fig.suptitle("R17: all nine held-out controls", fontsize=15)
    fig.tight_layout()
    save(fig, "quality-controls")

    primary = [r for r in a["contrasts"] if r["primary"]]
    fig, ax = plt.subplots(figsize=(10, 4.8))
    for i, row in enumerate(primary):
        middle, (low, high) = 100 * row["difference"], [100 * x for x in row["interval"]]
        ax.errorbar(
            middle,
            i,
            xerr=[[middle - low], [high - middle]],
            fmt="o",
            color=COLORS.get(row["left"], "#175CD3"),
            capsize=5,
        )
        ax.annotate(
            f"{middle:+.2f} [{low:+.2f}, {high:+.2f}]",
            (high, i),
            xytext=(8, 0),
            textcoords="offset points",
            va="center",
            fontsize=9,
        )
    labels = [
        f"{'Authored' if r['domain'] == 'synthetic' else 'HotpotQA'}: "
        f"{NAMES[r['left']]} − {NAMES[r['right']]}"
        for r in primary
    ]
    ax.set_yticks(range(len(primary)), labels)
    ax.invert_yaxis()
    ax.axvline(0, color="#667085", linewidth=1)
    ax.axvline(-3, color="#B42318", linestyle=":", label="−3 pp gate noninferiority margin")
    ax.set_xlabel("Paired difference (percentage points); individual 98.75% intervals")
    high = max(100 * r["interval"][1] for r in primary)
    low = min(-4, min(100 * r["interval"][0] for r in primary))
    ax.set_xlim(low - 2, high + max(12, (high - low) * 0.7))
    ax.set_title("Four prespecified primary comparisons")
    ax.legend(loc="lower right", fontsize=9)
    fig.tight_layout()
    save(fig, "primary-comparisons")

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    for ax, domain in zip(axes, ("synthetic", "hotpot"), strict=True):
        subset = ["native", "always", "uncertainty_gate", "benefit_gate", "random_gate"]
        offsets = [(6, -18), (-115, 10), (6, 10), (6, 26), (-100, -18)]
        for arm, offset in zip(subset, offsets, strict=True):
            row = lookup[domain, arm]
            x, y = 100 * row["call_fraction"], 100 * row["quality"]
            ax.scatter(x, y, s=70, color=COLORS.get(arm, "#98A2B3"), zorder=3)
            ax.annotate(
                NAMES[arm],
                (x, y),
                xytext=offset,
                textcoords="offset points",
                fontsize=9,
                arrowprops={"arrowstyle": "-", "color": "#98A2B3", "lw": 0.5},
            )
        ys = [100 * lookup[domain, arm]["quality"] for arm in subset]
        ax.set_ylim(max(0, min(ys) - 8), min(100, max(ys) + 8))
        ax.set_xlim(-8, 108)
        ax.set_xlabel("Questions calling Jev (%)")
        ax.set_ylabel("Authored accuracy (%)" if domain == "synthetic" else "Answer F1 (%)")
        ax.set_title("Authored tasks" if domain == "synthetic" else "HotpotQA")
        ax.grid(alpha=0.15)
    fig.suptitle("Quality and logical standalone Jev calls", fontsize=14)
    fig.tight_layout()
    save(fig, "quality-calls")

    modes = [(m, e) for m in ("additive", "conserve") for e in ("all", "prefill", "fade8")]
    strengths = [math.log(16), 5.0]
    policies = a["selected"]["all_policies"]
    matrix = [
        [
            100
            * next(
                r["quality"]
                for r in policies
                if r["policy"]["mode"] == m
                and r["policy"]["envelope"] == e
                and r["policy"]["strength"] == s
            )
            for s in strengths
        ]
        for m, e in modes
    ]
    fig, ax = plt.subplots(figsize=(7.6, 5.2))
    im = ax.imshow(matrix, cmap="Blues", aspect="auto")
    selected = a["selected"]["selected"]["policy"]
    for i, (mode, envelope) in enumerate(modes):
        for j, strength in enumerate(strengths):
            star = (
                " *"
                if (mode, envelope, strength)
                == (selected["mode"], selected["envelope"], selected["strength"])
                else ""
            )
            ax.text(
                j,
                i,
                f"{matrix[i][j]:.2f}{star}",
                ha="center",
                va="center",
                color="white"
                if matrix[i][j] > (min(map(min, matrix)) + max(map(max, matrix))) / 2
                else "#101828",
            )
    ax.set_xticks([0, 1], ["ln(16)", "5"])
    ax.set_yticks(range(6), [f"{m} / {e}" for m, e in modes])
    ax.set_xlabel("Attention-bias strength; * frozen selected policy")
    ax.set_title("Development search: equal-domain quality (%)")
    fig.colorbar(im, ax=ax, label="½ authored accuracy + ½ Hotpot F1")
    fig.tight_layout()
    save(fig, "development-search")

    rows = routing["results"]
    fig, ax = plt.subplots(figsize=(10, 5.2))
    for i, row in enumerate(rows):
        middle, (low, high) = 100 * row["routing_value"], [100 * x for x in row["interval"]]
        ax.errorbar(
            middle,
            i,
            xerr=[[max(0, middle - low)], [max(0, high - middle)]],
            fmt="o",
            capsize=4,
            color=COLORS.get(row["arm"], "#98A2B3"),
        )
        ax.annotate(
            f"{middle:+.2f}", (middle, i), xytext=(8, 8), textcoords="offset points", fontsize=9
        )
    ax.set_yticks(range(len(rows)), [f"{r['domain']} / {NAMES[r['arm']]}" for r in rows])
    ax.invert_yaxis()
    ax.axvline(0, color="#667085", linewidth=1)
    ax.set_xlabel("Quality versus expected random routing at the same call count (pp)")
    ax.set_title("Offline routing value; exploratory 95% world-bootstrap intervals")
    fig.tight_layout()
    save(fig, "routing-value")
    return {"figures": 5, "formats": ["PNG", "SVG", "PDF"]}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--report", type=Path, default=ROOT / "reports/2026-09-22-selective-attention")
    print(json.dumps(render(p.parse_args().report)))
