"""Read-only R25 reference/target/split audit against exact upstream Parquet bytes."""

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(value):
    return re.sub(r"\W+", " ", value.casefold()).strip()


def audit_rows(cases, references, targets, sources, exposed):
    def unique(rows):
        indexed = {r["id"]: r for r in rows}
        if len(indexed) != len(rows):
            raise ValueError("Duplicate identity")
        return indexed

    by_id, refs, target_map = unique(cases), unique(references), unique(targets)
    if set(refs) != set(by_id) or set(target_map) != {
        c["id"] for c in cases if c["split"] == "train"
    }:
        raise ValueError("Reference or target coverage mismatch")
    seen = {normalize(q) for q in exposed}
    counts = Counter()
    for case in cases:
        source_split, row_index = case["origin"].split("/")
        original = sources[case["task"] + "/" + source_split][int(row_index)]
        question = original["question"]
        normalized = normalize(question)
        if normalized in seen:
            raise ValueError("Duplicate or exposed question")
        seen.add(normalized)
        ref = refs[case["id"]]
        if ref["prompt_sha256"] != hashlib.sha256(case["prompt"].encode()).hexdigest():
            raise ValueError("Reference prompt digest mismatch")
        if case["task"] == "gsm8k":
            ident = f"gsm8k/{source_split}/{row_index}"
            allowed_split = {"train", "development"} if source_split == "train" else {"test"}
            answer = original["answer"].rpartition("####")[2].strip().replace(",", "")
            expected_ref = {"kind": "number", "answer": answer}
            prompt = (
                question + "\n\nReason through the problem and finish with a separate line: "
                "#### <numeric answer>."
            )
            target = re.sub(r"<<.*?>>", "", original["answer"])
        elif case["task"] == "arc":
            ident = f"arc/{source_split}/{original['id']}"
            allowed_split = {"validation": "development", "train": "train", "test": "test"}[
                source_split
            ]
            allowed_split = {allowed_split}
            pairs = list(
                zip(original["choices"]["label"], original["choices"]["text"], strict=True)
            )
            selected = [j for j, (label, _) in enumerate(pairs) if label == original["answerKey"]]
            if len(selected) != 1:
                raise ValueError("Ambiguous upstream answer label")
            letter = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[selected[0]]
            expected_ref = {"kind": "choice", "answer": letter, "choices": len(pairs)}
            prompt = (
                question
                + "\n\n"
                + "\n".join(
                    f"{'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[j]}. {text}"
                    for j, (_, text) in enumerate(pairs)
                )
                + "\n\nReason through the problem and finish with a separate line: Final: <letter>."
            )
            target = "Final: " + letter
        else:
            raise ValueError("Unexpected task")
        if (
            case["id"] != ident
            or case["split"] not in allowed_split
            or case["prompt"] != prompt
            or {k: v for k, v in ref.items() if k not in ("id", "prompt_sha256")} != expected_ref
        ):
            raise ValueError("Source question, options, answer or split mismatch")
        if case["split"] == "train" and target_map[ident]["target"] != target:
            raise ValueError("Training target differs from source")
        counts[case["task"] + "/" + case["split"]] += 1
    return dict(
        passed=True,
        cases=len(cases),
        references=len(refs),
        training_targets=len(targets),
        counts=dict(counts),
        normalized_duplicates=0,
        previously_exposed_matches=0,
        note=(
            "Exact pinned source and project-split consistency; not proof of factual label "
            "correctness or freedom from model pretraining exposure."
        ),
    )


def run(folder, upstream, exposed_path):
    import pyarrow.parquet as pq

    m = json.loads((folder / "manifest.json").read_text())
    sources, bindings = {}, {}
    for name, info in m["upstream"].items():
        path = upstream / (name.replace("/", "-") + ".parquet")
        digest = sha(path)
        if digest != info["sha256"]:
            raise ValueError("Upstream file hash mismatch")
        bindings[name] = digest
        sources[name] = pq.read_table(path).to_pylist()
    for name, digest in m["datasets"].items():
        if sha(folder / name) != digest:
            raise ValueError("Frozen artifact hash mismatch")
    cases = json.loads((folder / "cases.json").read_text())
    refs = [
        r
        for split in ("train", "development", "test")
        for r in json.loads((folder / f"{split}-references.json").read_text())
    ]
    targets = json.loads((folder / "training-targets.json").read_text())
    old = json.loads(exposed_path.read_text())
    exposed = []
    for row in old:
        if row["task"] != "gsm8k_train":
            continue
        question = sources["gsm8k/train"][int(row["origin_id"])]["question"]
        if not row["prompt"].startswith(question + "\n\n"):
            raise ValueError("Earlier exposure does not bind to its source row")
        exposed.append(question)
    result = audit_rows(cases, refs, targets, sources, exposed)
    if result["counts"] != {
        f"{t}/{s}": n
        for t in ("gsm8k", "arc")
        for s, n in [("train", 192), ("development", 32), ("test", 96)]
    }:
        raise ValueError("Unexpected cohort sizes")
    return result | dict(
        previously_exposed_questions=len(exposed),
        upstream_hashes=bindings,
        manifest_sha256=sha(folder / "manifest.json"),
        exposed_cases_sha256=sha(exposed_path),
        auditor_sha256=sha(Path(__file__)),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--exposed", type=Path, required=True)
    parser.add_argument("--save", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.freeze, args.upstream, args.exposed)
    with args.save.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
