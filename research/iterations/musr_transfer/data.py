"""Pinned public inputs, separate labels, and whole-scenario exposure exclusion."""

import ast
import csv
import hashlib
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
G = runpy.run_path(str(ROOT / "research/diagnostics/musr_groups.py"))
S = runpy.run_path(str(Path(__file__).with_name("single.py")))
ADMISSION = ROOT / "research/diagnostics/musr-admission-20260926/grouping-and-exposure.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bind(family, rows, groups, exposed):
    bindings = G["bind_rows"](family, rows, groups)
    if not isinstance(exposed, set) or not exposed <= set(bindings):
        raise ValueError("Unknown exposure identifier")
    prior_groups = {bindings[ident] for ident in exposed}
    cases, refs, selected_groups, excluded, ambiguous = [], {}, {}, [], []
    for index, row in enumerate(rows):
        ident = f"musr/{family}/{index}"
        if bindings[ident] in prior_groups and ident not in exposed:
            excluded.append(ident)
            continue
        case = dict(
            id=ident,
            task=family,
            split="development" if ident in exposed else "test",
            context=row["narrative"],
            question=row["question"],
            choices=ast.literal_eval(row["choices"]),
        )
        S["validate_case"](case)
        ref = int(row["answer_index"])
        if (
            str(ref) != row["answer_index"]
            or not 0 <= ref < len(case["choices"])
            or row["answer_choice"] != case["choices"][ref]
        ):
            raise ValueError("Inconsistent public reference")
        cases.append(case)
        refs[ident] = ref
        selected_groups[ident] = bindings[ident]
        if len({S["normalized"](c) for c in case["choices"]}) != len(case["choices"]):
            ambiguous.append(ident)
    return dict(
        cases=cases,
        references=refs,
        case_groups=selected_groups,
        excluded_related_ids=excluded,
        ambiguous_choice_ids=ambiguous,
    )


def load(folder):
    admission = json.loads(ADMISSION.read_text())
    if admission["passed"] is not True:
        raise ValueError("Source grouping not admitted")
    combined = dict(
        cases=[],
        references={},
        case_groups={},
        excluded_related_ids=[],
        ambiguous_choice_ids=[],
        sources={},
    )
    for family in sorted(G["FAMILIES"]):
        binding = admission["families"][family]
        csv_path, author_path = folder / f"{family}.csv", folder / f"{family}.json"
        if (
            sha(csv_path) != binding["hf_csv_sha256"]
            or sha(author_path) != binding["author_json_sha256"]
        ):
            raise ValueError("Pinned MuSR input hash mismatch")
        with csv_path.open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        groups = G["source_groups"](family, json.loads(author_path.read_text()))
        actual = G["bind_rows"](family, rows, groups)
        expected = {
            key: value
            for key, value in admission["case_groups"].items()
            if key.startswith(f"musr/{family}/")
        }
        if actual != expected:
            raise ValueError("Changed author group binding")
        result = bind(family, rows, groups, set(binding["prior_direct_ids"]))
        for key, value in result.items():
            if isinstance(value, list):
                combined[key].extend(value)
            else:
                if set(value) & set(combined[key]):
                    raise ValueError("Duplicate combined case")
                combined[key].update(value)
        combined["sources"].update({p.name: sha(p) for p in (csv_path, author_path)})
    fresh = [c for c in combined["cases"] if c["split"] == "test"]
    if (
        len(fresh) != 730
        or len(combined["cases"]) != 742
        or len({combined["case_groups"][c["id"]] for c in fresh}) != 428
    ):
        raise ValueError("Unexpected public transfer coverage")
    return combined
