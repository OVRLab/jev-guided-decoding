"""Prospectively registered R19 supplement; no new external inference or altered main study."""

import argparse
import asyncio
import hashlib
import json
import platform
import random
import runpy
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
S = runpy.run_path(str(HERE / "benefit_sufficiency/study.py"))
D, P, J = (S[k] for k in ("D", "P", "J"))
ARMS = ("instruction_always", "shuffled_sufficiency")


def donors(cases):
    result = {}
    for domain in sorted({D["domain"](c) for c in cases}):
        ids = sorted(
            [c["id"] for c in cases if D["domain"](c) == domain],
            key=lambda ident: hashlib.sha256(
                ("r19-sufficiency-shuffle/" + ident).encode()
            ).hexdigest(),
        )
        if len(ids) < 2:
            raise ValueError("At least two cases per permutation domain")
        result.update(zip(ids, ids[1:] + ids[:1], strict=True))
    return result


def control_receipt(arm, source_count, own, donor):
    if arm == "instruction_always":
        return dict(
            status="complete", key="canned-instruction", scores=[0.5] * source_count, sufficient=0.0
        )
    if arm != "shuffled_sufficiency":
        raise ValueError("Unknown control")
    key = "shuffled/" + own["key"] + "/" + donor["key"]
    if own["status"] != "complete" or donor["status"] != "complete":
        return dict(status="failed", key=key)
    if len(own["scores"]) != source_count:
        raise ValueError("Source receipt mismatch")
    return dict(
        status="complete", key=key, scores=list(own["scores"]), sufficient=donor["sufficient"]
    )


def source_hashes():
    return {
        **S["source_hashes"](),
        str(Path(__file__).resolve().relative_to(ROOT)): D["sha"](Path(__file__)),
        "research/benefit-sufficiency-controls.md": D["sha"](
            ROOT / "research/benefit-sufficiency-controls.md"
        ),
    }


def schedule(cases):
    rows = list(cases)
    random.Random(190922907).shuffle(rows)
    jobs = []
    for c in rows:
        arms = list(ARMS)
        random.Random("r19-controls/" + c["id"]).shuffle(arms)
        jobs.extend(dict(case_id=c["id"], arm=a) for a in arms)
    return jobs


def prepare(folder, main_folder):
    if folder.exists():
        raise FileExistsError("Use a new supplement freeze")
    manifest = json.loads((main_folder / "manifest.json").read_text())
    if manifest["sources"] != S["source_hashes"]():
        raise ValueError("Main source freeze changed")
    cases = json.loads((main_folder / "test.json").read_text())
    folder.mkdir(parents=True)
    D["dump"](folder / "donors.json", donors(cases))
    D["dump"](folder / "schedule.json", schedule(cases))
    D["dump"](
        folder / "manifest.json",
        dict(
            protocol="r19-sufficiency-controls-v1",
            at=J["now"](),
            sources=source_hashes(),
            main_manifest_sha256=D["sha"](main_folder / "manifest.json"),
            main_test_sha256=D["sha"](main_folder / "test.json"),
            datasets={p.name: D["sha"](p) for p in folder.glob("*.json")},
            max_seconds=90 * 60,
            live_api_calls=0,
            outputs=1216,
        ),
    )


async def run(args):
    from jev_guided_decoding.backends.transformers import TransformersBackend

    R = runpy.run_path(str(HERE / "benefit_sufficiency/runtime.py"))
    manifest = json.loads((args.manifest / "manifest.json").read_text())
    main_manifest = json.loads((args.main_manifest / "manifest.json").read_text())
    if (
        manifest["sources"] != source_hashes()
        or manifest["main_manifest_sha256"] != D["sha"](args.main_manifest / "manifest.json")
        or any(D["sha"](args.manifest / n) != v for n, v in manifest["datasets"].items())
    ):
        raise ValueError("Supplement freeze mismatch")
    complete = json.loads((args.main_results / "completion.json").read_text())
    if not complete["completed_schedule"] or complete["outputs"] != 6096:
        raise ValueError("Main study incomplete")
    cases_list = json.loads((args.main_manifest / "test.json").read_text())
    cases = {c["id"]: c for c in cases_list}
    mapping = json.loads((args.manifest / "donors.json").read_text())
    jobs = json.loads((args.manifest / "schedule.json").read_text())
    if mapping != donors(cases_list) or jobs != schedule(cases_list):
        raise ValueError("Supplement schedule changed")
    selected = json.loads((args.main_results / "selected.json").read_text())
    receipts = {
        r["key"]: r
        for r in J["rows"](args.main_results / "receipts.jsonl")
        if r["status"] != "started"
    }
    by_case = {
        r["case_id"]: receipts[r["receipt_key"]]
        for r in J["rows"](args.main_results / "outputs.jsonl")
        if r["stage"] == "test" and r["arm"] == "dual"
    }
    inputs = {r["id"]: r for r in J["rows"](args.main_results / "inputs.jsonl")}
    started = time.monotonic()
    freeze = dict(
        **manifest,
        selected_sha256=D["sha"](args.main_results / "selected.json"),
        main_completion_sha256=D["sha"](args.main_results / "completion.json"),
    )
    with J["Journal"](args.output, freeze) as log:
        base = TransformersBackend.load(
            S["MODEL"],
            revision=S["REVISION"],
            device=args.device,
            dtype="float32",
            local_files_only=True,
        )
        runtime = R["Runtime"](base)
        before = S["OLD"]["OLD"]["PRIOR"]["weight_hash"](base)
        if before != complete["weights_before"]:
            raise ValueError("Supplement checkpoint changed")
        J["append"](
            args.output / "loads.jsonl",
            dict(
                at=J["now"](),
                weights_before=before,
                python=platform.python_version(),
                backend=base.metadata(),
                revision=subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
                ).strip(),
            ),
        )
        for i, job in enumerate(jobs):
            if time.monotonic() - started > manifest["max_seconds"]:
                raise TimeoutError("Supplement deadline")
            case, arm = cases[job["case_id"]], job["arm"]
            donor = mapping[case["id"]] if arm == "shuffled_sufficiency" else None
            receipt = control_receipt(
                arm, len(case["sources"]), by_case[case["id"]], by_case.get(donor)
            )
            metadata = dict(
                case_id=case["id"],
                world_id=case["world_id"],
                domain=D["domain"](case),
                stage="supplement",
                arm=arm,
                policy=main_manifest["treatment"],
                donor_case=donor,
                own_receipt_key=by_case[case["id"]]["key"] if donor else None,
                donor_receipt_key=by_case[donor]["key"] if donor else None,
                provider_kind="canned_control" if donor is None else "recorded_permutation",
                paid_api_attempts=0,
                standalone_jev_calls=0 if donor is None else 1,
            )
            ident = f"supplement/{case['id']}/{arm}"
            if not log.start(ident, metadata):
                continue
            try:
                encoded = R["encode"](base.tokenizer, D["public_view"](case))
                if {"id": case["id"], **encoded} != inputs[case["id"]]:
                    raise ValueError("Supplement prompt changed")

                async def callback(v, receipt=receipt):
                    return receipt

                with S["Profile"](base) as profile:
                    row = await R["generate"](
                        runtime,
                        encoded,
                        D["public_view"](case),
                        main_manifest["treatment"],
                        callback,
                        gate={"kind": "always"},
                        mode="sufficiency" if arm == "instruction_always" else "dual",
                        instruction_strength=selected["instruction_strength"],
                    )
                # The runtime's provider callback counter is not a paid Jev request.
                callback_count = row.pop("logical_jev_calls")
                row.update(
                    metadata,
                    local_callback_count=callback_count,
                    logical_jev_calls=metadata["standalone_jev_calls"],
                    physical_jev_attempts=0,
                    forward_events=profile.events,
                    peak_gpu_bytes=profile.peak,
                    grade=D["grade"](case, row["text"]),
                )
                log.finish(ident, row)
            except BaseException as exc:
                log.finish(
                    ident,
                    {
                        **metadata,
                        "status": "error",
                        "error_type": type(exc).__name__,
                        "work_unknown": True,
                    },
                )
                raise
            if i % 32 == 0:
                print(
                    json.dumps(
                        dict(stage="supplement", done=i + 1, planned=len(jobs), paid_api_attempts=0)
                    ),
                    flush=True,
                )
        after = S["OLD"]["OLD"]["PRIOR"]["weight_hash"](base)
        if before != after:
            raise ValueError("Supplement weights changed")
        D["dump"](
            args.output / "completion.json",
            dict(
                at=J["now"](),
                outputs=len(log.outputs),
                paid_api_attempts=0,
                weights_before=before,
                weights_after=after,
                completed_schedule=True,
            ),
        )
        print("SUPPLEMENT COMPLETE", flush=True)


def audit(args):
    from transformers import AutoTokenizer

    A = runpy.run_path(str(HERE / "benefit_sufficiency/analyze.py"))
    require = A["require"]
    manifest = json.loads((args.manifest / "manifest.json").read_text())
    main = json.loads((args.main_manifest / "manifest.json").read_text())
    require(manifest["sources"] == source_hashes(), "Supplement source changed")
    require(
        manifest["main_manifest_sha256"] == D["sha"](args.main_manifest / "manifest.json")
        and manifest["main_test_sha256"] == D["sha"](args.main_manifest / "test.json"),
        "Main binding mismatch",
    )
    require(
        all(D["sha"](args.manifest / n) == v for n, v in manifest["datasets"].items()),
        "Supplement dataset changed",
    )
    cases = json.loads((args.main_manifest / "test.json").read_text())
    mapping = donors(cases)
    require(mapping == json.loads((args.manifest / "donors.json").read_text()), "Donor mismatch")
    selected = json.loads((args.main_results / "selected.json").read_text())
    freeze = json.loads((args.results / "freeze.json").read_text())
    require(
        freeze
        == dict(
            **manifest,
            selected_sha256=D["sha"](args.main_results / "selected.json"),
            main_completion_sha256=D["sha"](args.main_results / "completion.json"),
        ),
        "Supplement execution freeze mismatch",
    )
    rows = J["rows"](args.results / "outputs.jsonl")
    starts = J["rows"](args.results / "starts.jsonl")
    expected = {f"supplement/{j['case_id']}/{j['arm']}" for j in schedule(cases)}
    require(
        len(rows) == len(starts) == len(expected) == 1216
        and {r["job"] for r in rows} == {r["job"] for r in starts} == expected,
        "Incomplete/duplicate supplement",
    )
    main_rows = {
        (r["case_id"], r["arm"]): r
        for r in J["rows"](args.main_results / "outputs.jsonl")
        if r["stage"] == "test"
    }
    receipts = {
        r["key"]: r
        for r in J["rows"](args.main_results / "receipts.jsonl")
        if r["status"] != "started"
    }
    by_case = {c["id"]: receipts[main_rows[c["id"], "dual"]["receipt_key"]] for c in cases}
    encoded = {r["id"]: r for r in J["rows"](args.main_results / "inputs.jsonl")}
    case_lookup = {c["id"]: c for c in cases}
    tokenizer = AutoTokenizer.from_pretrained(
        main["model"], revision=main["revision"], local_files_only=True, trust_remote_code=False
    )
    lookup = {}
    for row in rows:
        c = case_lookup[row["case_id"]]
        arm = row["arm"]
        donor = mapping[c["id"]] if arm == "shuffled_sufficiency" else None
        receipt = control_receipt(arm, len(c["sources"]), by_case[c["id"]], by_case.get(donor))
        require(
            row["donor_case"] == donor
            and row["provider_kind"]
            == ("canned_control" if donor is None else "recorded_permutation"),
            "Control attribution mismatch",
        )
        require(
            row["own_receipt_key"] == (by_case[c["id"]]["key"] if donor else None)
            and row["donor_receipt_key"] == (by_case[donor]["key"] if donor else None),
            "Donor receipt provenance mismatch",
        )
        require(
            row["receipt_key"] == receipt["key"]
            and row["raw_scores"] == receipt.get("scores")
            and row["sufficient"] == receipt.get("sufficient"),
            "Permuted judgment mismatch",
        )
        require(
            row["instruction_strength"] == selected["instruction_strength"]
            and row["policy"] == main["treatment"]
            and row["mode"] == ("sufficiency" if donor is None else "dual"),
            "Control treatment mismatch",
        )
        require(
            row["logical_jev_calls"] == row["standalone_jev_calls"] == int(donor is not None)
            and row["local_callback_count"] == 1
            and row["paid_api_attempts"] == row["physical_jev_attempts"] == 0,
            "Canned callback mislabeled as paid inference",
        )
        A["check_output"](
            {**row, "logical_jev_calls": row["local_callback_count"]},
            encoded[c["id"]],
            D["public_view"](c),
            tokenizer,
            main,
        )
        require(row["grade"] == D["grade"](c, row["text"]), "Supplement grade mismatch")
        require(
            row["features"] == main_rows[c["id"], "native"]["features"],
            "Native observation changed",
        )
        lookup[c["id"], arm] = row
    completion = json.loads((args.results / "completion.json").read_text())
    require(
        completion["completed_schedule"]
        and completion["outputs"] == 1216
        and completion["paid_api_attempts"] == 0
        and completion["weights_before"] == completion["weights_after"],
        "Supplement completion mismatch",
    )
    groups = {}
    for domain in ("synthetic", "hotpot", "squad2"):
        cohort = [c for c in cases if D["domain"](c) == domain]
        dual = [D["quality"](c, main_rows[c["id"], "dual"]["grade"]) for c in cohort]
        group = {}
        for arm in ARMS:
            out = [lookup[c["id"], arm] for c in cohort]
            quality = [D["quality"](c, r["grade"]) for c, r in zip(cohort, out, strict=True)]
            group[arm] = dict(
                quality=sum(quality) / len(quality),
                dual_minus_control=A["bootstrap"](cohort, dual, quality, 0.95, 19019),
                mean_model_seconds=sum(r["model_seconds"] for r in out) / len(out),
                tokens=sum(len(r["final"]["token_ids"]) for r in out),
                subgroups={},
            )
            for missing in (False, True):
                indices = [i for i, c in enumerate(cohort) if c["missing"] == missing]
                group[arm]["subgroups"]["missing" if missing else "answerable"] = dict(
                    count=len(indices),
                    quality=sum(quality[i] for i in indices) / len(indices) if indices else None,
                )
        groups[domain] = group
    return dict(
        at=J["now"](),
        outcomes=len(rows),
        paid_api_attempts=0,
        weights_unchanged=True,
        domains=groups,
        main_completion_sha256=D["sha"](args.main_results / "completion.json"),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare", "run", "audit"])
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--main-manifest", type=Path, required=True)
    parser.add_argument("--main-results", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--results", type=Path)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.manifest, args.main_manifest)
    elif args.command == "run":
        asyncio.run(run(args))
    else:
        value = audit(args)
        D["dump"](args.output, value)
        print(
            json.dumps(
                dict(outcomes=value["outcomes"], paid_api_attempts=0, weights_unchanged=True)
            )
        )


if __name__ == "__main__":
    main()
