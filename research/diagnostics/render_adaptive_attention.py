"""Render standalone scientific figures from completed, independently audited R16 artifacts."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "reports/2026-09-22-adaptive-attention"
A = json.loads((REPORT / "independent-analysis.json").read_text())
assert A["audit_passed"]
FIG = REPORT / "figures"
FIG.mkdir(exist_ok=True)
plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.titleweight": "bold",
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
    }
)
COLORS = {
    "native": "#64748b",
    "r15": "#93c5fd",
    "tuned": "#0d9488",
    "dynamic": "#7c3aed",
    "shuffled": "#cbd5e1",
    "shuffled_dynamic": "#cbd5e1",
    "lexical": "#d97706",
    "lexical_dynamic": "#d97706",
    "zero": "#e2e8f0",
}
LABELS = {
    "native": "Granite",
    "r15": "R15 static",
    "tuned": "Tuned static",
    "dynamic": "Dynamic Jev",
    "shuffled": "Shuffled",
    "shuffled_dynamic": "Shuffled dynamic",
    "lexical": "Lexical",
    "lexical_dynamic": "Lexical dynamic",
    "zero": "Zero bias",
}


def save(fig, name):
    fig.savefig(FIG / (name + ".png"), dpi=200, bbox_inches="tight")
    fig.savefig(FIG / (name + ".svg"), bbox_inches="tight")
    fig.savefig(FIG / (name + ".pdf"), bbox_inches="tight")
    plt.close(fig)


keys = [
    "original/constrained",
    "original/open_explicit",
    "original/open_neutral",
    "original/staged",
    "paraphrase/staged",
    "dependency/staged",
    "hotpot/open_explicit",
    "hotpot/staged",
]
fig, axes = plt.subplots(4, 2, figsize=(13, 17), layout="constrained")
for ax, key in zip(axes.flat, keys, strict=True):
    panel = A["panels"][key]
    arms = [a for a in COLORS if a in panel["arms"] and a != "zero"]
    metric = "f1" if key.startswith("hotpot/") else "accuracy"
    values = [100 * panel["arms"][a][metric] for a in arms]
    bars = ax.barh(range(len(arms)), values, color=[COLORS[a] for a in arms])
    ax.set_yticks(range(len(arms)), [LABELS[a] for a in arms])
    ax.invert_yaxis()
    ax.set_xlim(0, 103)
    ax.set_xlabel("Answer F1 (%)" if metric == "f1" else "Parsed answer accuracy (%)")
    ax.set_title(key.replace("/", " · ").replace("_", " "), loc="left", fontsize=12)
    ax.bar_label(bars, labels=[f"{x:.1f}" for x in values], padding=4, fontsize=10)
    if not key.startswith("hotpot/"):
        ax.axvline(50, ls=":", color="#b91c1c", alpha=0.6)
    ax.grid(axis="x", alpha=0.13)
    ax.set_axisbelow(True)
fig.suptitle("R16: frozen-weight Granite with static and dynamic evidence attention", fontsize=16)
fig.supxlabel(
    "Synthetic panels: dotted line = always abstain (50%). "
    "HotpotQA: length-filtered 200-question subset.\n"
    "Descriptive point estimates; three prespecified paired comparisons are shown separately.",
    fontsize=10,
)
save(fig, "all-panels")
comparisons = [
    ("original/constrained", "r15", "Combined tuning − R15\nConstrained accuracy"),
    ("original/staged", "tuned", "Dynamic − tuned static\nStaged accuracy"),
    ("hotpot/open_explicit", "native", "Tuned − Granite\nHotpotQA answer F1"),
]
fig, ax = plt.subplots(figsize=(10, 4.8), layout="constrained")
for i, (key, control, _label) in enumerate(comparisons):
    c = A["panels"][key]["contrasts"][control]
    v = 100 * c["difference"]
    lo, hi = np.array(c["interval"]) * 100
    ax.errorbar(v, i, xerr=[[v - lo], [hi - v]], fmt="o", capsize=5, color="#0d9488", markersize=8)
    ax.annotate(
        f"{v:+.2f} [{lo:+.2f}, {hi:+.2f}]",
        (v, i),
        xytext=(0, 13),
        textcoords="offset points",
        ha="center",
        fontsize=10,
    )
ax.set_yticks(range(3), [v[2] for v in comparisons])
ax.invert_yaxis()
ax.axvline(0, color="#64748b", ls="--")
ax.grid(axis="x", alpha=0.15)
ax.set_xlabel("Paired difference, percentage points")
ax.set_ylim(2.55, -0.6)
ax.set_title("Three primary comparisons: 98.333% paired bootstrap intervals", loc="left")
save(fig, "primary-contrasts")
policy = A["selected"]["policy"]
heads = policy["heads"]
weights = policy["weights"]
fig, ax = plt.subplots(figsize=(11, 5), layout="constrained")
x = np.arange(len(heads))
ax.bar(x - 0.18, [np.log(16)] * len(heads), 0.36, label="Frozen R15", color="#93c5fd")
ax.bar(x + 0.18, weights, 0.36, label="Development-selected vector", color="#0d9488")
ax.set_xticks(x, [f"L{layer}\nH{head}" for layer, head in heads])
ax.set_ylabel("Additive attention-logit strength")
ax.set_xlabel("Zero-based layer / query-head index")
ax.set_ylim(0, 6.5)
ax.legend(frameon=False)
ax.set_title("Steering strengths selected before testing", loc="left")
save(fig, "selected-head-strengths")
fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), layout="constrained")
for ax, contract in zip(axes, ["constrained", "open_explicit", "staged"], strict=True):
    panel = A["panels"]["original/" + contract]
    for arm in ["native", "r15", "tuned", "dynamic"]:
        if arm not in panel["arms"]:
            continue
        depths = panel["arms"][arm]["per_depth"]
        x = sorted(map(int, depths))
        y = [100 * depths[str(d)]["accuracy"] for d in x]
        ax.plot(x, y, "o-", color=COLORS[arm], label=LABELS[arm])
    ax.axhline(50, ls=":", color="#b91c1c", alpha=0.6)
    ax.set_ylim(0, 105)
    ax.set_xticks(range(1, 7))
    ax.set_xlabel("Stated chain depth")
    ax.set_title(contract.replace("_", " "))
    ax.grid(alpha=0.15)
axes[0].set_ylabel("Parsed answer accuracy (%)")
axes[-1].legend(frameon=False, fontsize=9)
fig.suptitle("Depth breakdown: descriptive, with answerable and missing-link cases balanced")
save(fig, "depth-breakdown")
fig, ax = plt.subplots(figsize=(8, 5), layout="constrained")
for key, marker in [("hotpot/open_explicit", "o"), ("hotpot/staged", "s")]:
    for arm, metrics in A["panels"][key]["arms"].items():
        sec = (metrics["model_seconds"] + metrics["deployed_jev_seconds"]) / metrics["n"]
        ax.scatter(sec, 100 * metrics["f1"], s=80, marker=marker, color=COLORS[arm])
        ax.annotate(
            LABELS[arm] + (" (staged)" if marker == "s" else ""),
            (sec, 100 * metrics["f1"]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=9,
        )
ax.set_xlabel("Mean model + required hosted API seconds per question")
ax.set_ylabel("HotpotQA answer F1 (%)")
ax.grid(alpha=0.15)
ax.set_title("Observed answer quality versus serial model/API work", loc="left")
fig.supxlabel(
    "API time is charged to each deployment arm even where the study reused a receipt.\n"
    "Excludes loading, controller bookkeeping and cooldowns; "
    "includes model processing of framing tokens.",
    fontsize=9,
)
save(fig, "quality-latency")
print(json.dumps({"figures": len(list(FIG.glob("*.png"))), "formats": ["PNG", "SVG", "PDF"]}))
