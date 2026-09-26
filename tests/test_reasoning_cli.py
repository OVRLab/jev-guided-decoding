import asyncio
import json
import sys
from types import SimpleNamespace

import pytest

from jev_guided_decoding import cli
from jev_guided_decoding.types import Candidate, Proposal


@pytest.fixture
def backend(monkeypatch):
    class Backend:
        frame_text = "<final>Done</final>"

        @staticmethod
        def load(**kwargs):
            return Backend()

        def encode(self, request):
            assert "<step>" in request.system
            type(self).last_request = request
            return (1,)

        def decode(self, ids):
            return "".join(map(chr, ids))

        def propose_frames(self, prompt, prefix, **kwargs):
            if kwargs["max_tokens"] == 2:  # Excluded warm-up.
                return Proposal((), 0, 0, 0, 0.01)
            text = self.frame_text
            candidate = Candidate(tuple(map(ord, text)), text, -0.1, "frame", text)
            return Proposal((candidate,), len(text), len(text), 1, 0.01)

        def metadata(self):
            return {"backend": "offline-test"}

        def reset_memory_peak(self):
            pass

        def memory(self):
            return {}

    monkeypatch.setitem(
        sys.modules,
        "jev_guided_decoding.backends.transformers",
        SimpleNamespace(TransformersBackend=Backend),
    )
    monkeypatch.setattr(cli, "load_api_key", lambda *args: pytest.fail("baseline read a key"))
    return Backend


@pytest.mark.parametrize("prompt_style", ["instructions", "examples"])
def test_reason_command_works_without_credentials_and_records_actual_prompt(
    backend, tmp_path, prompt_style
):
    config = tmp_path / "config.toml"
    config.write_text(
        f'[model]\nmodel_id="fake"\n[reasoning]\nmax_resamples=0\nprompt_style="{prompt_style}"\n'
    )
    evidence = tmp_path / "evidence.txt"
    evidence.write_text("Public fixture")
    output = tmp_path / "run.json"
    args = cli.parser().parse_args(
        [
            "reason",
            "--config",
            str(config),
            "--output",
            str(output),
            "--question",
            "Q",
            "--evidence-file",
            str(evidence),
            "--mode",
            "likelihood",
        ]
    )
    assert asyncio.run(cli.run(args)) == 0
    saved = json.loads(output.read_text())
    assert saved["result"]["text"] == "Done"
    assert saved["result"]["schema_version"] == "reasoning-v1"
    assert "<step>" in saved["request"]["system"]
    from jev_guided_decoding.framing import REASONING_PROMPTS

    assert saved["request"]["system"] == REASONING_PROMPTS[prompt_style]
    assert backend.last_request.system == saved["request"]["system"]
    with pytest.raises(ValueError, match="already exists"):
        asyncio.run(cli.run(args))


def test_final_only_jev_control_is_available_in_reasoning_benchmark():
    args = cli.parser().parse_args(
        [
            "reason-benchmark",
            "--config",
            "config.toml",
            "--output",
            "result",
            "--dataset",
            "cases.jsonl",
            "--modes",
            "greedy",
            "likelihood",
            "final_jev",
            "jev",
        ]
    )
    assert args.modes == ["greedy", "likelihood", "final_jev", "jev"]


def test_reason_benchmark_records_incomplete_runs_without_credentials(backend, tmp_path):
    backend.frame_text = "<step>unfinished"
    config = tmp_path / "config.toml"
    config.write_text('[model]\nmodel_id="fake"\n[reasoning]\nmax_resamples=0\n')
    dataset = tmp_path / "cases.jsonl"
    dataset.write_text(
        json.dumps({"id": "case", "question": "Q", "evidence": "E", "answers": ["Reference only"]})
        + "\n"
    )
    output = tmp_path / "benchmark"
    args = cli.parser().parse_args(
        [
            "reason-benchmark",
            "--config",
            str(config),
            "--output",
            str(output),
            "--dataset",
            str(dataset),
            "--modes",
            "greedy",
            "likelihood",
        ]
    )
    assert asyncio.run(cli.run(args)) == 3
    rows = [json.loads(line) for line in (output / "runs.jsonl").read_text().splitlines()]
    assert len(rows) == 2
    assert all(row["result"]["phase"] == "stopped" for row in rows)
    assert all("Reference only" not in str(row["request"]) for row in rows)
    summary = json.loads((output / "summary.json").read_text())
    assert summary["likelihood"]["completed_runs"] == 0
    assert "selected_path_tokens_per_second" in summary["greedy"]
    assert "accepted_tokens_per_second" not in summary["greedy"]


def test_reason_cli_preserves_cancelled_result(backend, monkeypatch, tmp_path):
    from jev_guided_decoding.reasoning import ReasoningCancelled, ReasoningResult

    class Cancelled:
        def __init__(self, *args):
            pass

        async def run(self, request, mode):
            raise ReasoningCancelled(
                ReasoningResult(
                    mode=mode, phase="stopped", stop_reason="cancelled", usage_unknown=True
                )
            )

    monkeypatch.setattr(cli, "ReasoningController", Cancelled)
    config = tmp_path / "config.toml"
    config.write_text('[model]\nmodel_id="fake"\n')
    evidence = tmp_path / "evidence.txt"
    evidence.write_text("E")
    output = tmp_path / "cancelled.json"
    args = cli.parser().parse_args(
        [
            "reason",
            "--config",
            str(config),
            "--output",
            str(output),
            "--evidence-file",
            str(evidence),
            "--question",
            "Q",
            "--mode",
            "greedy",
        ]
    )
    assert asyncio.run(cli.run(args)) == 130
    saved = json.loads(output.read_text())["result"]
    assert saved["stop_reason"] == "cancelled" and saved["usage_unknown"]


def test_output_created_during_inference_is_not_overwritten(backend, monkeypatch, tmp_path):
    output = tmp_path / "run.json"
    propose = backend.propose_frames

    def competing_writer(self, *args, **kwargs):
        output.write_text("Another process's result")
        return propose(self, *args, **kwargs)

    monkeypatch.setattr(backend, "propose_frames", competing_writer)
    config = tmp_path / "config.toml"
    config.write_text('[model]\nmodel_id="fake"\n')
    evidence = tmp_path / "evidence.txt"
    evidence.write_text("E")
    args = cli.parser().parse_args(
        [
            "reason",
            "--config",
            str(config),
            "--output",
            str(output),
            "--evidence-file",
            str(evidence),
            "--question",
            "Q",
            "--mode",
            "greedy",
        ]
    )
    with pytest.raises(FileExistsError):
        asyncio.run(cli.run(args))
    assert output.read_text() == "Another process's result"
