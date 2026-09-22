"""Expected random routing at the observed call count; no model/provider execution."""

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path


def routing_value(rows):
    import numpy as np

    if not rows or any(
        type(r["called"]) is not bool
        or any(
            type(r[k]) not in (int, float) or not math.isfinite(r[k]) or not 0 <= r[k] <= 1
            for k in ("native", "guided")
        )
        for r in rows
    ):
        raise ValueError("Invalid potential outcomes")
    groups = defaultdict(list)
    for r in rows:
        groups[r["world"]].append(r)
    # Each world contributes count, calls, native sum, treatment sum, selected-treatment sum.
    x = np.asarray(
        [
            [
                len(g),
                sum(r["called"] for r in g),
                sum(r["native"] for r in g),
                sum(r["guided"] - r["native"] for r in g),
                sum(r["called"] * (r["guided"] - r["native"]) for r in g),
            ]
            for g in groups.values()
        ],
        dtype=float,
    )

    def value(sums):
        n, calls, native, delta, selected = np.moveaxis(sums, -1, 0)
        fraction = calls / n
        observed, random = (native + selected) / n, (native + fraction * delta) / n
        return observed - random

    rng = np.random.default_rng(170922353)
    bootstrap = np.empty(10000)
    for start in range(0, 10000, 500):
        indices = rng.integers(0, len(x), size=(500, len(x)))
        bootstrap[start : start + 500] = value(x[indices].sum(1))
    totals = x.sum(0)
    n, calls, native, delta, selected = totals
    treatment = np.asarray([r["guided"] - r["native"] for r in rows])
    extreme = 0
    for _ in range(10000):
        pick = rng.permutation(len(rows))[: int(calls)]
        extreme += int(treatment[pick].sum() >= selected - 1e-12)
    return dict(
        contexts=len(rows),
        worlds=len(groups),
        call_fraction=float(calls / n),
        gate_quality=float((native + selected) / n),
        expected_random_quality=float((native + (calls / n) * delta) / n),
        routing_value=float(value(totals)),
        interval=np.quantile(bootstrap, [0.025, 0.975]).tolist(),
        level=0.95,
        permutation_one_sided_p=(1 + extreme) / 10001,
        permutations=10000,
        bootstrap_draws=10000,
    )


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def analyze(manifest, results, main_analysis):
    audit = json.loads(main_analysis.read_text())
    if not audit["audit_passed"] or any(
        sha(results / name) != digest for name, digest in audit["artifact_hashes"].items()
    ):
        raise ValueError("Main audit/artifact binding failed")
    cases = json.loads((manifest / "test.json").read_text())
    outputs = [json.loads(s) for s in (results / "outputs.jsonl").read_text().splitlines()]
    index = {(r["case_id"], r["arm"]): r for r in outputs if r["stage"] == "test"}
    groups = defaultdict(list)
    for c in cases:
        domain = "hotpot" if c["family"] == "hotpot" else "synthetic"
        key = "f1" if domain == "hotpot" else "correct"
        native, guided = index[c["id"], "native"], index[c["id"], "always"]
        for arm in ("benefit_gate", "uncertainty_gate", "random_gate"):
            gate = index[c["id"], arm]
            called = gate["call_decision"]
            branch = guided if called else native
            if (
                gate["final"]["token_ids"] != branch["final"]["token_ids"]
                or gate["grade"] != branch["grade"]
            ):
                raise ValueError("Potential branch identity failed")
            groups[domain, arm].append(
                dict(
                    world=c["world_id"],
                    called=called,
                    native=native["grade"][key],
                    guided=guided["grade"][key],
                )
            )
    return dict(
        protocol="r17-prospective-offline-routing",
        main_analysis_sha256=sha(main_analysis),
        script_sha256=sha(__file__),
        audit_passed=True,
        live_calls=0,
        new_model_forwards=0,
        interpretation="Expected random routing at the same call count; not another live run.",
        results=[
            dict(domain=domain, arm=arm, **routing_value(rows))
            for (domain, arm), rows in sorted(groups.items())
        ],
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--results", type=Path, required=True)
    p.add_argument("--main-analysis", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    report = analyze(a.manifest, a.results, a.main_analysis)
    with a.output.open("x") as f:
        json.dump(report, f, indent=2, allow_nan=False)
        f.write("\n")
    print(json.dumps({"audit_passed": True, "controls": len(report["results"])}))


if __name__ == "__main__":
    main()
