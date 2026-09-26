"""Plot only the completed audited R31 result; no inference or partial-result read."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

BASE = Path(__file__).resolve().parent
OUT = BASE
a = json.loads((OUT / "analysis.json").read_text())
assert a["passed"] and a["outputs"] == 11840 and a["requests"] == 832
assert a["test_cases"] == 256 and len([v for v in a["contrasts"].values() if v["primary"]]) == 4
figures = OUT / "figures"
figures.mkdir(exist_ok=True)
plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "svg.fonttype": "none",
        "savefig.facecolor": "white",
    }
)
labels = {
    "native": "Original Granite",
    "blind": "Blind repair",
    "embedding-structured": "Embedding · structured",
    "embedding-scalar": "Embedding · scalar",
    "embedding-constant": "Embedding · constant",
    "contextual-structured": "Contextual · structured",
    "contextual-scalar": "Contextual · scalar",
    "contextual-constant": "Contextual · constant",
}
colors = {
    "native": "#4a4a4a",
    "blind": "#949494",
    **{
        n: ("#287da3" if n.startswith("contextual") else "#75a99a")
        for n in labels
        if n not in ("native", "blind")
    },
}
names = list(labels)
fig, (left, right) = plt.subplots(
    1, 2, figsize=(13.0, 5.8), gridspec_kw={"width_ratios": [1.08, 1]}
)
fig.subplots_adjust(left=0.18, right=0.985, top=0.83, bottom=0.23, wspace=0.85)
for y, name in enumerate(names):
    value = 100 * a["scores"][name]["accuracy"]
    left.barh(y, value, height=0.58, color=colors[name])
    left.text(value + 1, y, f"{value:.2f}%", va="center", fontsize=9)
left.set(
    yticks=range(len(names)),
    yticklabels=[labels[n] for n in names],
    xlim=(0, 100),
    xlabel="All three answers correct (%)",
    title="A   Complete held-out worlds",
)
left.invert_yaxis()
left.xaxis.set_major_locator(MultipleLocator(25))
left.grid(axis="x", alpha=0.16)
left.set_axisbelow(True)
contrasts = [
    ("contextual-scalar-minus-native", "Contextual scalar\n− original Granite"),
    ("contextual-scalar-minus-embedding-scalar", "Contextual scalar\n− embedding scalar"),
    ("contextual-structured-minus-contextual-scalar", "Contextual structured\n− contextual scalar"),
    ("contextual-scalar-minus-donor/contextual-scalar", "Contextual scalar\n− its donor control"),
]
span = max(abs(x) for key, _ in contrasts for x in a["contrasts"][key]["family_ci_pp"]) + 2
for y, (key, _label) in enumerate(contrasts):
    v = a["contrasts"][key]
    lo, hi = v["family_ci_pp"]
    cl, ch = v["ci95_pp"]
    point = v["delta_pp"]
    right.plot([lo, hi], [y, y], color="#287da3", linewidth=1.3)
    right.plot([cl, ch], [y, y], color="#287da3", linewidth=4, solid_capstyle="butt")
    right.scatter([point], [y], color="#123c50", s=34, zorder=3)
    right.text(span * 0.98, y - 0.26, f"{point:+.2f} pp", ha="right", fontsize=9)
right.axvline(0, color="#777777", linestyle="--", linewidth=1)
right.set(
    yticks=range(4),
    yticklabels=[label for _, label in contrasts],
    xlim=(-span, span),
    ylim=(3.55, -0.65),
    xlabel="Paired difference (percentage points)",
    title="B   Four registered primary contrasts",
)
right.grid(axis="x", alpha=0.16)
right.set_axisbelow(True)
fig.suptitle(
    "R31 · Matched memory representations and feedback", x=0.18, ha="left", fontsize=16, y=0.98
)
fig.text(
    0.18,
    0.90,
    "256 fresh authored worlds · original Granite 4.0-1B · two fixed training seeds",
    fontsize=10,
    color="#555555",
)
fig.text(
    0.18,
    0.045,
    "Bars: complete-world accuracy; adapter rows average seeds. "
    "Original/blind outputs are shared.\n"
    "Intervals: thick 95%, thin family-adjusted 98.75%; paired world bootstrap stratified by task "
    "(10,000 draws).\n"
    "This is a same-template mechanism study, not public-benchmark or larger-model performance.",
    fontsize=9,
    color="#555555",
    linespacing=1.5,
)
for suffix in ("png", "svg"):
    fig.savefig(figures / f"r31-contextual-memory.{suffix}", dpi=180)
plt.close(fig)
fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.8), sharey=True)
fig.subplots_adjust(left=0.10, right=0.98, top=0.77, bottom=0.23, wspace=0.18)
for ax, task in zip(axes, ("temporal", "compositional"), strict=True):
    for i, feedback in enumerate(("structured", "scalar", "constant")):
        for j, memory in enumerate(("embedding", "contextual")):
            name = memory + "-" + feedback
            value = 100 * a["scores"][name]["by_task"][task]
            ax.bar(
                i + (j - 0.5) * 0.32,
                value,
                width=0.30,
                color=colors[name],
                label=memory.title() if i == 0 else None,
            )
            ax.text(i + (j - 0.5) * 0.32, value + 1, f"{value:.1f}", ha="center", fontsize=8)
    ax.axhline(
        100 * a["scores"]["native"]["by_task"][task],
        color="#4a4a4a",
        linestyle="--",
        linewidth=1,
        label="Original",
    )
    ax.set(
        title=f"{task.title()} · 128 worlds",
        xticks=range(3),
        xticklabels=["Structured", "Scalar", "Constant"],
        ylim=(0, 100),
    )
    ax.grid(axis="y", alpha=0.16)
    ax.set_axisbelow(True)
axes[0].set_ylabel("All three answers correct (%)")
axes[1].legend(frameon=False, loc="upper right", fontsize=9)
fig.suptitle("R31 · Results by task family", x=0.10, ha="left", fontsize=15, y=0.98)
fig.text(
    0.10,
    0.08,
    "Two-seed mean accuracy, with the original-model baseline shown separately for each task.\n"
    "Both families retain the authored vocabulary/templates; these are not independent public "
    "benchmarks.",
    fontsize=9,
    color="#555555",
)
for suffix in ("png", "svg"):
    fig.savefig(figures / f"r31-task-families.{suffix}", dpi=180)
plt.close(fig)
print(
    json.dumps(
        {"figures": [p.name for p in figures.iterdir()], "source": "completed audited R31 analysis"}
    )
)
