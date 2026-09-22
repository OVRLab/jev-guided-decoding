"""Supplement the frozen R16 auditor with exercised-hook and output-contract checks."""

import argparse
import hashlib
import json
import runpy
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research/iterations/adaptive_attention"
P = runpy.run_path(str(HERE / "policies.py"))
D = runpy.run_path(str(HERE / "data.py"))
J = runpy.run_path(str(HERE / "journal.py"))
FRAMES = {
    "reasoning cue": "Reasoning:\n",
    "chunk separator": "\n",
    "final cue": "\nFinal answer:",
}


def check_injection_and_contract(row, tokenizer=None):
    phases = row.get("phases", [])
    calls = sum(
        len({item["head"][0] for item in phase["maps"]}) * len(phase["token_ids"])
        for phase in phases
    )
    if calls != row.get("hook_calls", 0):
        raise ValueError("Recorded attention injection count does not match exercised phases")
    if sum(len(p["token_ids"]) for p in phases) != row.get("model_forwards", 0):
        raise ValueError("Forward count does not match phase tokens")
    frames = row.get("framing", [])
    if frames and row["contract"] != "staged":
        raise ValueError("Unexpected direct-answer framing")
    for frame in frames:
        if frame["name"] not in FRAMES or (
            tokenizer is not None
            and tokenizer.encode(FRAMES[frame["name"]], add_special_tokens=False)
            != frame["token_ids"]
        ):
            raise ValueError("Unexpected framing text")
    if row["status"] == "complete" and row["contract"] == "staged":
        names = [f["name"] for f in frames]
        if names[:1] != ["reasoning cue"] or names[-1:] != ["final cue"]:
            raise ValueError("Missing staged framing")
        if any(name != "chunk separator" for name in names[1:-1]) or len(names) > 4:
            raise ValueError("Unexpected staged framing sequence")
    for phase in phases:
        if phase["phase"] == "final":
            cap = 1 if row["contract"] == "constrained" else 32
        elif row["contract"] == "staged" and phase["phase"] in (
            "reasoning_1",
            "reasoning_2",
            "reasoning_3",
        ):
            cap = 24
        else:
            raise ValueError("Unexpected generation phase")
        if not 1 <= len(phase["token_ids"]) <= cap:
            raise ValueError("Phase exceeds generation budget")
        for token in phase["tokens"]:
            if row["contract"] != "constrained":
                if "allowed_ids" in token or "label_logits" in token:
                    raise ValueError("Open-vocabulary answer menu detected")
            elif tokenizer is not None:
                expected = [
                    tokenizer.encode(s, add_special_tokens=False) for s in (*D["COLORS"], "UNKNOWN")
                ]
                if any(len(ids) != 1 for ids in expected) or token["allowed_ids"] != [
                    x[0] for x in expected
                ]:
                    raise ValueError("Constrained answer menu changed")
    return dict(hook_calls=calls, active_phases=sum(bool(p["maps"]) for p in phases))


def analyze(manifest_folder, result_folder, tokenizer):
    manifest = json.loads((manifest_folder / "manifest.json").read_text())
    for name, digest in manifest["sources"].items():
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT) or D["sha"](path) != digest:
            raise ValueError("Frozen source changed")
    completion = json.loads((result_folder / "completion.json").read_text())
    if (
        not completion["completed_schedule"]
        or completion["weights_before"] != completion["weights_after"]
    ):
        raise ValueError("Incomplete study or changed weights")
    selection = json.loads((result_folder / "selected.json").read_text())
    selected = selection["selected"]["policy"]
    expected_freeze = dict(
        selected=selected,
        sources=manifest["sources"],
        schedule_sha256=manifest["datasets"]["schedule.json"],
    )
    if json.loads((result_folder / "test-freeze.json").read_text()) != expected_freeze:
        raise ValueError("Selected/test freeze mismatch")
    starts = J["rows"](result_folder / "starts.jsonl")
    test_starts = [r for r in starts if r["metadata"]["stage"] == "test"]
    if datetime.fromisoformat(selection["at"]) >= min(
        datetime.fromisoformat(r["at"]) for r in test_starts
    ):
        raise ValueError("Selection did not precede testing")
    outputs = J["rows"](result_folder / "outputs.jsonl")
    groups = defaultdict(lambda: defaultdict(int))
    for row in outputs:
        if row["stage"] == "test":
            expected = (
                None
                if row["arm"] in ("native", "zero")
                else P["r15"]()
                if row["arm"] == "r15"
                else selected
            )
            if row["policy"] != expected:
                raise ValueError("Test arm does not use its frozen policy")
            if expected is None and (
                row.get("updates") or any(p["maps"] for p in row.get("phases", []))
            ):
                raise ValueError("Native/zero arm received guidance")
        counts = check_injection_and_contract(row, tokenizer)
        key = "/".join(row[k] for k in ("stage", "family", "contract", "arm"))
        groups[key]["outcomes"] += 1
        groups[key]["outcomes_with_active_attention"] += int(counts["hook_calls"] > 0)
        for name, value in counts.items():
            groups[key][name] += value
    return dict(
        audit_passed=True,
        outcomes=len(outputs),
        selection_preceded_testing=True,
        selected_at=selection["at"],
        first_test_started_at=min(r["at"] for r in test_starts),
        all_test_policies_match_freeze=True,
        open_vocab_answer_menus=0,
        framing_matches_fixed_controller_text=True,
        attention_hook_calls=sum(g["hook_calls"] for g in groups.values()),
        groups=dict(groups),
        artifact_hashes={
            name: D["sha"](result_folder / name)
            for name in (
                "completion.json",
                "selected.json",
                "test-freeze.json",
                "outputs.jsonl",
                "starts.jsonl",
            )
        },
        auditor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    )


def main():
    from transformers import AutoTokenizer

    parser = argparse.ArgumentParser()
    for name in ("manifest", "results", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    tokenizer = AutoTokenizer.from_pretrained(
        "ibm-granite/granite-4.0-1b",
        revision="6a7381ba1f54d684ff508d991aeb7dc580157103",
        local_files_only=True,
    )
    result = analyze(args.manifest, args.results, tokenizer)
    D["dump"](args.output, result)
    print(json.dumps({k: v for k, v in result.items() if k not in ("groups", "artifact_hashes")}))


if __name__ == "__main__":
    main()
