"""Portable R19 audit: bound log1p roundoff while retaining every original integrity check."""

import argparse
import hashlib
import json
import math
import runpy
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "research/iterations/benefit_sufficiency/analyze.py"
CONTROLS = ROOT / "research/iterations/sufficiency_controls_v2.py"
AMENDMENT = ROOT / "research/benefit-sufficiency-audit-portability.md"


def validate_feature_roundtrip(recorded, expected):
    for values in (recorded, expected):
        if (
            not isinstance(values, list)
            or len(values) != 6
            or any(type(v) not in (int, float) or not math.isfinite(v) for v in values)
        ):
            raise ValueError("Invalid feature vector")
    for i, (a, b) in enumerate(zip(recorded, expected, strict=True)):
        if a != b and (i not in (3, 4) or math.nextafter(a, b) != b):
            raise ValueError("Benefit feature mismatch beyond logarithm roundoff")


def guarded_checker(original, vector, statistics=None):
    def check(row, encoded, view, tokenizer, manifest):
        expected = vector(row["features"], encoded, view)
        recorded = row["benefit_features"]
        validate_feature_roundtrip(recorded, expected)
        original({**row, "benefit_features": expected}, encoded, view, tokenizer, manifest)
        if statistics is not None:
            statistics["checked_rows"] += 1
            changed = [i for i, (a, b) in enumerate(zip(recorded, expected, strict=True)) if a != b]
            statistics["normalized_rows"] += bool(changed)
            for i in changed:
                statistics["component_counts"][str(i)] += 1
                statistics["max_absolute_difference"] = max(
                    statistics["max_absolute_difference"], abs(recorded[i] - expected[i])
                )

    return check


def load_main(statistics):
    module = runpy.run_path(str(MAIN))
    checker = guarded_checker(module["check_output"], module["P"]["vector"], statistics)
    module["check_output"] = checker
    module["audit"].__globals__["check_output"] = checker
    return module


def audit(args):
    statistics = dict(
        checked_rows=0,
        normalized_rows=0,
        component_counts={"3": 0, "4": 0},
        max_absolute_difference=0.0,
    )
    main = load_main(statistics)
    if args.kind == "main":
        result = main["audit"](args.manifest, args.results)
    else:
        if args.main_manifest is None or args.main_results is None:
            raise ValueError("Main manifest and results required for control audit")
        control = runpy.run_path(str(CONTROLS))

        def load(path, **kwargs):
            return main if Path(path).resolve() == MAIN else runpy.run_path(path, **kwargs)

        # This replaces only the audit module's reference, never global runpy.
        control["audit"].__globals__["runpy"] = SimpleNamespace(run_path=load)
        result = control["audit"](args)
    metadata = dict(
        kind=args.kind,
        **statistics,
        source_hashes={
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (Path(__file__).resolve(), MAIN, CONTROLS, AMENDMENT)
        },
        raw_records_unchanged=True,
        original_checks_retained=True,
        permitted_roundoff="At most one adjacent float for indices 3 and 4 only",
        new_model_or_api_calls=0,
    )
    return result, metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("main", "controls"))
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--main-manifest", type=Path)
    parser.add_argument("--main-results", type=Path)
    args = parser.parse_args()
    result, metadata = audit(args)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    args.output.with_name(args.output.stem + "-adapter.json").write_text(
        json.dumps(metadata, indent=2) + "\n"
    )
    print(json.dumps({"outcomes": result["outcomes"], **metadata}))


if __name__ == "__main__":
    main()
