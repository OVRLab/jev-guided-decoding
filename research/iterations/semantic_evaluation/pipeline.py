"""Sequential validation, generation, anonymous grading and immutable grading freeze."""

import argparse
import json
import runpy
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
S = runpy.run_path(str(HERE / "study.py"))
G = runpy.run_path(str(HERE / "judge.py"))
J = S["J"]
D = S["BASE_D"]


def run(folder, output, key_file):
    manifest = S["verify"](folder)
    if output.exists():
        raise FileExistsError("New pipeline output required")
    output.mkdir(parents=True)

    def call(script, *args):
        subprocess.run(
            [sys.executable, str(HERE / script), *map(str, args)], check=True, timeout=10500
        )

    validation = output / "validation.jsonl"
    call("grade.py", "--packets", folder / "validation-packets.json", "--output", validation)
    rows = J["rows"](validation)
    fixtures = json.loads((folder / "fixtures.json").read_text())
    result = G["admission"](
        fixtures["validation"],
        [r for r in rows if r["id"].startswith("validation/")],
        [
            {**r, "id": r["id"].removeprefix("repeat/")}
            for r in rows
            if r["id"].startswith("repeat/")
        ],
    )
    result.update(
        manifest_sha256=D["sha"](folder / "manifest.json"),
        at=J["now"](),
        validation_outputs_sha256=D["sha"](validation),
    )
    D["dump"](output / "judge-admission.json", result)
    print(json.dumps(dict(stage="judge_admission", **result)), flush=True)
    if not result["passed"]:
        D["dump"](
            output / "pipeline-completion.json",
            dict(
                at=J["now"](), status="admission_failed", generated_test_answers=0, paid_jev_calls=0
            ),
        )
        return
    call(
        "study.py",
        "generate",
        "--manifest",
        folder,
        "--output",
        output / "generation",
        "--key-file",
        key_file,
        "--judge-admission",
        output / "judge-admission.json",
    )
    cases = json.loads((folder / "test.json").read_text())
    generated = J["rows"](output / "generation/outputs.jsonl")
    if len(generated) != manifest["test_jobs"] or any(r["status"] != "complete" for r in generated):
        raise ValueError("Incomplete generation cannot enter grading")
    packets, mapping = G["blind"](cases, generated)
    D["dump"](output / "blind-packets.json", packets)
    D["dump"](output / "blind-mapping.json", mapping)
    call(
        "grade.py",
        "--packets",
        output / "blind-packets.json",
        "--output",
        output / "judgments.jsonl",
    )
    # Persist the grade bytes before any treatment join or aggregate inspection.
    D["dump"](
        output / "grading-freeze.json",
        dict(
            at=J["now"](),
            sources=manifest["sources"],
            packets_sha256=D["sha"](output / "blind-packets.json"),
            mapping_sha256=D["sha"](output / "blind-mapping.json"),
            judgments_sha256=D["sha"](output / "judgments.jsonl"),
            generation_sha256=D["sha"](output / "generation/outputs.jsonl"),
        ),
    )
    D["dump"](
        output / "pipeline-completion.json",
        dict(
            at=J["now"](),
            status="complete",
            generated_test_answers=len(generated),
            unique_judge_packets=len(packets),
        ),
    )
    print("PIPELINE COMPLETE; GRADES FROZEN BEFORE TREATMENT ANALYSIS", flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--key-file", type=Path, required=True)
    a = p.parse_args()
    run(a.manifest, a.output, a.key_file)


if __name__ == "__main__":
    main()
