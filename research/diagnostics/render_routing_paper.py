"""Standalone research figures from admitted aggregates; no grading or inference."""

import argparse
import hashlib
import json
from pathlib import Path


def save_figure(figure, destination, stem):
    for extension in ("svg", "png"):
        path = destination / (stem + "." + extension)
        figure.savefig(path, dpi=180)
        if extension == "svg":
            path.write_text(
                "\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n"
            )


def render(destination, r28=None):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    root = Path(__file__).resolve().parents[2]
    source = root / "reports/2026-09-25-completed-granite/short-analysis.json"
    data = json.loads(source.read_text())["full"]
    destination.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "svg.fonttype": "none",
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(12.6, 4.8), gridspec_kw={"width_ratios": [1.1, 1]})
    names = [
        ("original", "Original Granite"),
        ("self_refine", "Self-refinement"),
        ("live_constant", "Constant signal*"),
        ("shuffled", "Shuffled signal*"),
        ("guided", "Granite–Jev"),
        ("granite_4_2_3b", "Larger Granite 4.2-3B"),
    ]
    colors = ["#9aa4af", "#9aa4af", "#688ba3", "#688ba3", "#007f73", "#494c62"]
    for y, ((key, _label), color) in enumerate(zip(names, colors, strict=True)):
        row = data["summaries"][key]["ifbench"]
        score = 100 * row["accuracy"]
        ax.barh(y, score, color=color, height=0.56)
        ax.text(score + 0.8, y, f"{score:.1f}% ({row['correct']}/300)", va="center", fontsize=9)
    ax.set_yticks(range(len(names)), [label for _, label in names])
    ax.invert_yaxis()
    ax.set_xlim(0, 83)
    ax.set_xticks([0, 20, 40, 60, 80])
    ax.set_xlabel("Strict prompt success (%)")
    ax.set_title("R27: IFBench scores", loc="left", fontweight="bold", pad=16)
    contrasts = [
        ("guided-original", "vs original"),
        ("guided-self_refine", "vs self-refinement"),
        ("guided-live_constant", "vs constant signal*"),
        ("guided-shuffled", "vs shuffled signal*"),
    ]
    for y, (key, _label) in enumerate(contrasts):
        row = data["paired_differences"][key]["ifbench"]
        value = 100 * row["difference"]
        lo, hi = [100 * x for x in row["descriptive_paired_95"]]
        bx.errorbar(
            value, y, xerr=[[value - lo], [hi - value]], fmt="o", color="#007f73", capsize=4
        )
        bx.text(10.0, y, f"{value:+.2f} [{lo:+.2f}, {hi:+.2f}]", va="center", fontsize=9)
    bx.axvline(0, color="#707780", linewidth=1, linestyle="--")
    bx.set_yticks(range(len(contrasts)), [label for _, label in contrasts])
    bx.invert_yaxis()
    bx.set_xlim(-2, 21)
    bx.set_xticks([-2, 0, 2, 4, 6, 8])
    bx.set_xlabel("Granite–Jev difference (percentage points)")
    bx.set_title(
        "Granite–Jev paired differences\nDescriptive 95% intervals",
        loc="left",
        fontweight="bold",
        pad=16,
    )
    fig.subplots_adjust(left=0.18, right=0.98, bottom=0.24, top=0.82, wspace=0.65)
    fig.text(
        0.02,
        0.075,
        "* These controls retain Jev repair selection; they do not isolate routing.\n"
        "Intervals are unadjusted and descriptive. "
        "The larger model uses a different generation profile.",
        fontsize=9,
        color="#444444",
    )
    save_figure(fig, destination, "r27-instruction-evidence")
    plt.close(fig)
    metadata = {
        "matplotlib": matplotlib.__version__,
        "inputs": {str(source.relative_to(root)): hashlib.sha256(source.read_bytes()).hexdigest()},
    }
    if r28:
        result = json.loads(r28.read_text())
        if result["status"] != "completed" or not result["integrity"]["passed"]:
            raise ValueError("R28 figure needs completed admitted results")
        fig, ax = plt.subplots(figsize=(11.5, 4.6))
        contrasts = [
            ("jev_constant__random_constant", "Selection: Jev vs random"),
            ("jev_constant__confidence_constant", "Selection: Jev vs native confidence"),
            ("jev_live__jev_constant", "Feedback: live vs constant"),
            ("jev_live__jev_shuffled", "Feedback: live vs shuffled"),
        ]
        bounds = []
        for y, (key, _label) in enumerate(contrasts):
            row = result["contrasts"][key]
            v = row["delta_pp"]
            lo, hi = row["ci9875_pp"]
            bounds.extend([lo, hi])
            ax.errorbar(v, y, xerr=[[v - lo], [hi - v]], fmt="o", color="#007f73", capsize=4)
            ax.text(
                1.035,
                y,
                f"{v:+.2f} [{lo:+.2f}, {hi:+.2f}]",
                transform=ax.get_yaxis_transform(),
                va="center",
                fontsize=9,
            )
        ax.axvline(0, color="#707780", linestyle="--", linewidth=1)
        ax.set_yticks(range(4), [s for _, s in contrasts])
        ax.invert_yaxis()
        ax.set_xlim(min(-1, min(bounds) - 1), max(1, max(bounds) + 1))
        ax.set_xlabel("Strict prompt-success difference (percentage points)")
        ax.set_title(f"R28: {result['cases']} eligible IFEval cases", loc="left", fontweight="bold")
        fig.subplots_adjust(left=0.32, right=0.77, top=0.85, bottom=0.23)
        fig.text(
            0.025,
            0.06,
            "98.75% paired bootstrap intervals for the four planned comparisons.\n"
            "Equal repair counts; shared potential outcomes; one fixed adapter and backbone.",
            fontsize=9,
        )
        save_figure(fig, destination, "r28-attribution")
        plt.close(fig)
        metadata["inputs"][str(r28)] = hashlib.sha256(r28.read_bytes()).hexdigest()
    (destination / "figure-provenance.json").write_text(json.dumps(metadata, indent=2) + "\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--destination", type=Path, required=True)
    p.add_argument("--r28", type=Path)
    args = p.parse_args()
    render(args.destination, args.r28)
