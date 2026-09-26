"""Bounded, frozen comparison of generated finals, fixed verdicts, and direct Jev."""

import argparse
import asyncio
import json
import runpy
from pathlib import Path

from jev_guided_decoding.cli import parser as cli_parser
from jev_guided_decoding.cli import run as cli_run

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "experiments/fixed_verdict_worlds.json"
DATASET = ROOT / "data/fixed-verdict-evaluation.jsonl"
CONFIG = ROOT / "configs/granite-4.0-1b-fixed-verdict.toml"
MODES = ["jev", "fixed_jev", "direct_jev"]
SEEDS = [42]
MAX_SECONDS = 1200

# Reuse the tested symbolic oracle and strict verdict parser without a model grader.
_probe = runpy.run_path(str(ROOT / "experiments/proposal_probe.py"))
render = _probe["render"]


def worlds():
    return json.loads(FIXTURE.read_text())


def grade(rows):
    return _probe["grade_rows"](rows, worlds(), SEEDS, MODES)


async def evaluate(output):
    args = cli_parser().parse_args(
        [
            "reason-benchmark",
            "--config",
            str(CONFIG),
            "--dataset",
            str(DATASET),
            "--modes",
            *MODES,
            "--seeds",
            *map(str, SEEDS),
            "--local-files-only",
            "--output",
            str(output),
        ]
    )
    try:
        return await asyncio.wait_for(cli_run(args), MAX_SECONDS)
    except TimeoutError:
        return 130


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["export", "evaluate", "grade"])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.action == "export":
        with args.output.open("x") as stream:
            for world in worlds():
                stream.write(json.dumps(render(world)) + "\n")
    elif args.action == "evaluate":
        return asyncio.run(evaluate(args.output))
    else:
        rows = [json.loads(line) for line in (args.output / "runs.jsonl").read_text().splitlines()]
        grades = grade(rows)
        with (args.output / "verdicts.json").open("x") as stream:
            stream.write(json.dumps(grades, indent=2) + "\n")
        print(json.dumps(grades["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
