import asyncio
import json
import sys

from test_fixed_verdict import Decider
from test_reasoning_cli import backend as backend

from jev_guided_decoding import cli


class Client(Decider):
    def __init__(self, *args, **kwargs):
        super().__init__({"Done": (0.01, None, 0.01)})

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


def setup(monkeypatch, tmp_path, mode):
    monkeypatch.setattr(cli, "load_api_key", lambda *args: "fake")
    monkeypatch.setattr(cli, "VerdictScorer", Client, raising=False)
    config = tmp_path / "config.toml"
    config.write_text('[model]\nmodel_id="fake"\n[reasoning]\nmax_resamples=0\n')
    evidence = tmp_path / "evidence.txt"
    evidence.write_text("Evidence only")
    output = tmp_path / "out.json"
    args = cli.parser().parse_args(
        [
            "reason",
            "--config",
            str(config),
            "--evidence-file",
            str(evidence),
            "--question",
            "Classify the claim",
            "--mode",
            mode,
            "--output",
            str(output),
        ]
    )
    return args, output


def test_direct_cli_does_not_import_or_load_the_optional_backend(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "jev_guided_decoding.backends.transformers", None)
    args, output = setup(monkeypatch, tmp_path, "direct_jev")
    args.config.write_text("[reasoning]\nmax_api_calls=1\n")
    assert asyncio.run(cli.run(args)) == 0
    row = json.loads(output.read_text())
    assert row["result"]["text"] == "UNKNOWN"
    assert row["metadata"]["backend"] is None and row["metadata"]["load_seconds"] == 0
    assert row["memory"] == {} and row["result"]["generated_tokens"] == 0


def test_fixed_cli_keeps_reasoning_failure_and_separate_choice_provenance(
    backend, monkeypatch, tmp_path
):
    args, output = setup(monkeypatch, tmp_path, "fixed_jev")
    assert asyncio.run(cli.run(args)) == 0
    row = json.loads(output.read_text())
    assert row["result"]["reasoning_outcome"]["stop_reason"] == "no_eligible_branch"
    assert row["result"]["text"] == "UNKNOWN" and row["result"]["output_source"] == "jev_choice"
    assert row["result"]["api_calls"] == 2
