"""Scientific figures from the completed R20 audit; no new inference or grading."""

import argparse
import json
from pathlib import Path


def main():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--report", type=Path, required=True)
    a = p.parse_args()
    report = a.report
    data = json.loads((report / "independent-analysis.json").read_text())
    out = report / "figures"
    out.mkdir(exist_ok=True)

    def save(fig, name):
        fig.tight_layout()
        for suffix in ("png", "svg", "pdf"):
            fig.savefig(out / (name + "." + suffix), dpi=180, bbox_inches="tight")
        plt.close(fig)

    categories = data["admission"]["categories"]
    labels = list(categories)
    values = [100 * categories[k] for k in labels]
    fig, ax = plt.subplots(figsize=(9, 5.4))
    ax.barh(
        [k.replace("_", " ") for k in labels],
        values,
        color=["#0284c7" if v >= 87.5 else "#dc2626" for v in values],
    )
    ax.axvline(87.5, color="#64748b", linestyle="--", label="Per-category floor: 87.5%")
    for i, v in enumerate(values):
        ax.text(v + 1, i, f"{v:.1f}", va="center", fontsize=9)
    ax.set_xlim(0, 112)
    ax.set_xlabel("Agreement with constructed gold labels (%)")
    ax.invert_yaxis()
    ax.legend(loc="lower left")
    status = "passed" if data["admission"]["passed"] else "failed"
    ax.set_title(
        f"R20 • Independent judge admission {status}\n"
        f"96 validation cases; overall agreement {100 * data['admission']['accuracy']:.2f}%"
    )
    save(fig, "judge-validation")
    if data["status"] == "complete":
        domains = [("synthetic", "Authored"), ("hotpot", "HotpotQA"), ("squad2", "SQuAD2")]
        arms = [
            ("native", "Granite", "#64748b"),
            ("static", "Static instruction", "#7c3aed"),
            ("dual", "Granite + Jev", "#059669"),
        ]
        fig, axes = plt.subplots(1, 3, figsize=(11, 4.3), sharey=True)
        for ax, (domain, label) in zip(axes, domains, strict=True):
            group = data["domains"][domain]
            for i, (arm, _title, color) in enumerate(arms):
                value = 100 * group["arms"][arm]["lower"]
                ax.bar(i, value, color=color)
                ax.text(i, value + 1.3, f"{value:.2f}", ha="center", fontsize=10)
            ax.set_xticks(range(3), [t for _, t, _ in arms], rotation=20, ha="right")
            ax.set_ylim(0, 100)
            ax.set_title(label)
        axes[0].set_ylabel("Answers judged semantically correct (%)")
        fig.suptitle(
            "R20 • Fixed architecture comparison\n"
            "Blinded Qwen3-14B judgments; unresolved answers count as incorrect here"
        )
        save(fig, "semantic-scores")
        fig, ax = plt.subplots(figsize=(10, 5))
        labels = []
        for domain, title in domains:
            for control, label, color in (
                ("native", "native", "#059669"),
                ("static", "static", "#7c3aed"),
            ):
                estimate = data["domains"][domain]["comparisons"][control]
                y = len(labels)
                labels.append(f"{title}: Jev minus {label}")
                low, high = [100 * v for v in estimate["interval"]]
                point = 100 * estimate["difference"]
                ax.plot([low, high], [y, y], color=color, linewidth=2)
                ax.scatter([point], [y], color=color, zorder=3)
                ax.annotate(
                    f"{point:+.2f} [{low:+.2f}, {high:+.2f}]",
                    (high, y),
                    xytext=(7, 0),
                    textcoords="offset points",
                    va="center",
                    fontsize=9,
                )
        left, right = ax.get_xlim()
        ax.set_xlim(left - 2, right + 18)
        ax.axvline(0, color="#64748b", linestyle="--", linewidth=1)
        ax.set_yticks(range(len(labels)), labels)
        ax.invert_yaxis()
        ax.set_xlabel("Difference in Qwen-judged correctness (percentage points)")
        ax.set_title("R20 • Six registered contrasts\n99.1667% paired cluster-bootstrap intervals")
        save(fig, "semantic-contrasts")
    print(json.dumps(dict(figures=3 if data["status"] == "complete" else 1)))


if __name__ == "__main__":
    main()
