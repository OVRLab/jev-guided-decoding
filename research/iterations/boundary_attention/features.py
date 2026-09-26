"""Read one native attention query row; reconstruct all gate features from saved masses."""

import math

FEATURES = ("evidence_mass", "source_entropy", "head_disagreement")


def reconstruct(head_source_mass):
    if not head_source_mass or not head_source_mass[0]:
        raise ValueError("Empty source attention")
    n = len(head_source_mass[0])
    if any(len(row) != n for row in head_source_mass):
        raise ValueError("Ragged source attention")
    if any(
        type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1.000001
        for row in head_source_mass
        for v in row
    ):
        raise ValueError("Invalid source attention")
    totals = [sum(row) for row in head_source_mass]
    if any(x > 1.00001 for x in totals):
        raise ValueError("Invalid attention mass")
    probabilities = [
        [v / total for v in row] if total > 0 else [1 / n] * n
        for row, total in zip(head_source_mass, totals, strict=True)
    ]
    mean = [sum(row[i] for row in probabilities) / len(probabilities) for i in range(n)]

    def entropy(row):
        return -sum(v * math.log(v) for v in row if v > 0)

    scale = math.log(n) if n > 1 else 1.0
    return dict(
        evidence_mass=sum(totals) / len(totals),
        source_entropy=entropy(mean) / scale,
        head_disagreement=max(
            0.0,
            (entropy(mean) - sum(entropy(row) for row in probabilities) / len(probabilities))
            / scale,
        ),
    )


def observe(query, key, mask, spans, scaling):
    import torch

    if (
        query.shape[0] != 1
        or key.shape[0] != 1
        or query.shape[1] % key.shape[1]
        or query.shape[-2] != key.shape[-2]
    ):
        raise ValueError("Single-request prefill GQA required")
    flat = [i for span in spans for i in span]
    if (
        not spans
        or any(not span for span in spans)
        or len(set(flat)) != len(flat)
        or any(type(i) is not int or not 0 <= i < key.shape[-2] for i in flat)
    ):
        raise ValueError("Invalid evidence spans")
    q = query[0, :, -1].float()
    k = key[0].float().repeat_interleave(query.shape[1] // key.shape[1], 0)
    logits = torch.einsum("hd,hkd->hk", q, k) * scaling
    if mask is not None:
        last = mask[0, :, -1, : key.shape[-2]]
        logits += torch.where(last, 0.0, -torch.inf) if last.dtype == torch.bool else last.float()
    probs = logits.softmax(-1)
    if not torch.isfinite(probs).all():
        raise ValueError("Nonfinite native attention")
    masses = torch.stack([probs[:, span].sum(-1) for span in spans], -1).tolist()
    return dict(
        features=reconstruct(masses),
        head_source_mass=masses,
        query_rows_computed=1,
        key_length=key.shape[-2],
    )
