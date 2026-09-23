"""Feedback admission is separate from downstream generated-answer improvement."""

import math
import random


def metrics(pairs):
    positives = [p for p, truth in pairs if truth]
    negatives = [p for p, truth in pairs if not truth]
    tp = sum(p >= 0.5 for p in positives)
    tn = sum(p < 0.5 for p in negatives)
    sensitivity = tp / len(positives) if positives else None
    specificity = tn / len(negatives) if negatives else None
    return dict(
        count=len(pairs),
        supported=len(positives),
        unsupported=len(negatives),
        true_positive=tp,
        false_negative=len(positives) - tp,
        true_negative=tn,
        false_positive=len(negatives) - tn,
        sensitivity=sensitivity,
        specificity=specificity,
        balanced_accuracy=(sensitivity + specificity) / 2 if positives and negatives else None,
        brier=sum((p - int(t)) ** 2 for p, t in pairs) / len(pairs) if pairs else None,
    )


def analyze(rows, *, planned=192):
    if len({r["id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate job")
    if len(rows) > planned or planned <= 0:
        raise ValueError("Invalid record count")
    good = [r for r in rows if r["status"] == "complete"]
    for r in good:
        if len(r["scores"]) != 3 or any(
            type(p) not in (int, float) or not math.isfinite(p) or not 0 <= p <= 1
            for p in r["scores"]
        ):
            raise ValueError("Invalid score record")
    constructed = [
        (p, t) for r in good for p, t in zip(r["scores"][:2], (True, False), strict=True)
    ]
    natural = [
        (r["scores"][2], r["draft_oracle"]["supported"])
        for r in good
        if r["draft_oracle"] is not None
    ]
    cm, nm = metrics(constructed), metrics(natural)
    motifs = {
        m: metrics(
            [
                (p, t)
                for r in good
                if r["motif"] == m
                for p, t in zip(r["scores"][:2], (True, False), strict=True)
            ]
        )
        for m in sorted({r["motif"] for r in rows})
    }
    coverage = len(natural) / planned
    gates = dict(
        all_records_complete=len(good) == planned,
        constructed_balanced_accuracy=(cm["balanced_accuracy"] or 0) >= 0.90,
        every_motif=len(motifs) == 6
        and all((m["balanced_accuracy"] or 0) >= 0.75 for m in motifs.values()),
        natural_coverage=coverage >= 0.80,
        natural_error_exposure=nm["supported"] >= 20 and nm["unsupported"] >= 20,
        natural_balanced_accuracy=(nm["balanced_accuracy"] or 0) >= 0.85,
    )
    rng, draws = random.Random(210923072), []
    if good:
        for _ in range(5000):
            sample = rng.choices(good, k=len(good))
            draws.append(
                sum((r["scores"][0] >= 0.5) + (r["scores"][1] < 0.5) for r in sample)
                / (2 * len(sample))
            )
        draws.sort()
    return dict(
        admitted=all(gates.values()),
        gates=gates,
        planned=planned,
        complete=len(good),
        missing=planned - len(rows),
        failed=len(rows) - len(good),
        constructed=cm,
        natural=nm,
        natural_coverage=coverage,
        by_motif=motifs,
        constructed_world_bootstrap_95=[draws[124], draws[4874]] if draws else None,
        interpretation="Signal admission only; no final-answer or adapter-quality result.",
    )
