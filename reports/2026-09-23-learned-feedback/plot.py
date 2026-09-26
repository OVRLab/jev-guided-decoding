"""Render the fixed R22 report numbers; needs matplotlib 3.10.6."""

import json
from pathlib import Path

import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "analysis.json").read_text())
labels = ["Native", "Trained control", "Jev feedback", "Shuffled feedback", "Oracle feedback"]
keys = ["native", "constant", "live", "permuted", "oracle"]
scores = [
    sum(v["accuracy"] for k, v in data["arms"].items() if k.startswith(mode + "/"))
    / (1 if mode == "native" else 2)
    * 100
    for mode in keys
]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "svg.fonttype": "none"})
fig, axes = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={"width_ratios": [1.2, 1]})
fig.suptitle("R22 · Learned internal bridge: no observed Jev contribution", fontsize=15, y=0.96)
colors = ["#5b677a", "#617d95", "#007d83", "#9aabab", "#b3bbbd"]
axes[0].barh(labels[::-1], scores[::-1], color=colors[::-1])
axes[0].set_xlim(0, 104)
axes[0].set_xlabel("Exact final-answer accuracy (%)")
axes[0].set_title("384 fresh worlds · two adapter seeds", fontsize=11)
for y, score in enumerate(scores[::-1]):
    axes[0].text(score - 2, y, f"{score:.2f}%", va="center", ha="right", color="white")
for y, key in enumerate(["live-native", "live-constant"]):
    row = data["contrasts"][key]
    lo, hi = [100 * x for x in row["interval"]]
    value = row["difference"] * 100
    axes[1].errorbar(
        value,
        y,
        xerr=[[value - lo], [hi - value]],
        fmt="o",
        capsize=5,
        color="#007d83",
        markersize=8,
    )
    axes[1].text(0, y + 0.22, f"{value:+.2f} pp [{lo:+.2f}, {hi:+.2f}]", ha="center", fontsize=10)
axes[1].axvline(0, color="#777777", linestyle="--", linewidth=1, zorder=0)
axes[1].set_yticks([0, 1], ["Jev − native", "Jev − trained control"])
axes[1].set_ylim(-0.5, 1.65)
axes[1].invert_yaxis()
axes[1].set_xlim(-2.5, 5)
axes[1].set_xlabel("Accuracy difference (percentage points)")
axes[1].set_title("Primary 97.5% paired bootstrap intervals", fontsize=11)
for ax in axes:
    ax.spines[["top", "right"]].set_visible(False)
fig.text(
    0.5,
    0.045,
    "Shuffled and oracle feedback change zero final token sequences in either seed.\n"
    "Narrow synthetic tasks; a zero-width interval is sample agreement, not universal equivalence.",
    ha="center",
    fontsize=10,
)
fig.subplots_adjust(left=0.15, right=0.98, bottom=0.23, top=0.8, wspace=0.65)
(HERE / "figures").mkdir(exist_ok=True)
for ext in ("png", "svg", "pdf"):
    fig.savefig(HERE / "figures" / f"results.{ext}", dpi=180, facecolor="white")
svg = HERE / "figures/results.svg"
svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
