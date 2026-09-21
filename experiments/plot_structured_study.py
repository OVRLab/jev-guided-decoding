"""Render final R13 figures from the independently audited full-study summary.

Optional artifact tool; Matplotlib is not a library/runtime dependency. Validate
the exported figures visually and against the input table after the study ends.
"""

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path

LABELS = {
    "native": "Direct Granite",
    "staged": "Staged Granite",
    "likelihood": "Likelihood search",
    "jev": "Jev token guidance",
    "shuffled": "Shuffled scores",
    "zero": "Zero-bias shadow",
    "soft_step": "Soft step commitment",
}


def render(summary, output):
    if summary["planned"] != 6300 or summary["recorded"] != 6300 or summary["missing"]:
        raise ValueError("Figures require all 6,300 planned test outcomes")
    if summary["independent_token_audits"] != sum(a["complete"] for a in summary["arms"].values()):
        raise ValueError("Every completed model answer must pass independent token reconstruction")
    if summary["independent_input_audits"] != summary["recorded"]:
        raise ValueError("Every recorded prompt must match the frozen question and evidence")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "svg.fonttype": "none",
            "svg.hashsalt": "r13-structured-v2",
        }
    )
    output.mkdir(parents=True, exist_ok=False)
    names = list(LABELS)
    labels = list(LABELS.values())
    colors = ["#007c83" if n == "jev" else "#40566e" if n == "native" else "#939eaa" for n in names]

    def save(fig, name):
        for ext in ("png", "svg", "pdf"):
            metadata = (
                {"Date": None}
                if ext == "svg"
                else {"CreationDate": None, "ModDate": None}
                if ext == "pdf"
                else {}
            )
            fig.savefig(output / f"{name}.{ext}", dpi=180, facecolor="white", metadata=metadata)
        plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.9), sharey=True)
    accuracy = [100 * summary["arms"][n]["accuracy"] for n in names]
    seconds = [summary["diagnostics"]["arms"][n]["mean_seconds"] for n in names]
    for axis, values, title in zip(
        axes,
        (accuracy, seconds),
        ("Final-answer accuracy (%)", "Mean controller time (seconds)"),
        strict=True,
    ):
        bars = axis.barh(range(7), values, color=colors, height=0.62)
        axis.set_title(title, loc="left", fontweight="bold", pad=14)
        axis.set_yticks(range(7), labels)
        axis.set_axisbelow(True)
        axis.grid(axis="x", color="#e8ebef", linewidth=0.8)
        axis.bar_label(
            bars, labels=[f"{v:.1f}%" if axis is axes[0] else f"{v:.2f}" for v in values], padding=5
        )
        axis.set_xlim(0, 100 if axis is axes[0] else max(values) * 1.23)
    axes[0].invert_yaxis()
    fig.suptitle(
        "Granite + Jev on 300 synthetic logic worlds",
        x=0.02,
        ha="left",
        fontsize=15,
        fontweight="bold",
    )
    fig.text(
        0.02,
        0.025,
        "Three seeds per world; 900 planned jobs per arm. Failed jobs count as incorrect.\n"
        "All arms share a final-label grammar. Timing includes hosted Jev and discarded lookaheads;\n"
        "model loading and between-job recovery are excluded from these per-job means.",
        fontsize=9,
        color="#4d5660",
    )
    fig.subplots_adjust(left=0.19, right=0.98, top=0.83, bottom=0.18, wspace=0.22)
    save(fig, "accuracy-latency")

    controls = ("native", "staged", "likelihood")
    contrasts = [summary["contrasts"]["jev_minus_" + n] for n in controls]
    fig, axis = plt.subplots(figsize=(8.5, 3.9))
    extrema = [0.0]
    for i, c in enumerate(contrasts):
        point = c["difference"] * 100
        low, high = [100 * x for x in c["interval"]]
        axis.plot([low, high], [i, i], color="#40566e", linewidth=2.2)
        axis.plot(point, i, "o", color="#007c83", markersize=7)
        axis.plot([low, high], [i, i], "|", color="#40566e", markersize=9)
        axis.text(
            0.99,
            i + 0.19,
            f"{point:+.2f} pp  [{low:+.2f}, {high:+.2f}]",
            transform=axis.get_yaxis_transform(),
            ha="right",
            fontsize=9,
        )
        extrema.extend([low, high])
    axis.axvline(0, color="#9099a3", linestyle="--", linewidth=1)
    axis.set_yticks(range(3), ["Jev − " + LABELS[n] for n in controls])
    axis.set_ylim(2.55, -0.55)
    span = max(extrema) - min(extrema)
    axis.set_xlim(min(extrema) - max(1, span * 0.12), max(extrema) + max(1, span * 0.12))
    axis.set_xlabel("Accuracy difference (percentage points)")
    axis.set_title(
        "Prespecified Jev token-guidance contrasts", loc="left", fontweight="bold", pad=14
    )
    axis.spines["left"].set_visible(False)
    axis.grid(axis="x", color="#e8ebef", linewidth=0.8)
    fig.text(
        0.02,
        0.025,
        "World-cluster bootstrap: 5,000 draws after averaging seeds within each world.\n"
        "98.333% intervals adjust three comparisons to a nominal 95% family level.",
        fontsize=9,
        color="#4d5660",
    )
    fig.subplots_adjust(left=0.25, right=0.97, top=0.85, bottom=0.27)
    save(fig, "primary-contrasts")
    return {name: importlib.metadata.version(name) for name in ("matplotlib", "numpy", "pillow")}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.summary.read_bytes()
    versions = render(json.loads(raw), args.output)
    (args.output / "provenance.json").write_text(
        json.dumps(
            {
                "summary_sha256": hashlib.sha256(raw).hexdigest(),
                "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "versions": versions,
                "files": {
                    p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in args.output.iterdir()
                    if p.is_file()
                },
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
