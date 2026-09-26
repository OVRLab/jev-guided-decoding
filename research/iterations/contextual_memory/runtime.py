"""Serial candidate pipeline; no paid execution entrypoint before study admission."""

import hashlib
import runpy
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = runpy.run_path(str(HERE.parent / "structured_correction/study.py"))
P = runpy.run_path(str(HERE.parent / "feedback_pairing/common.py"))
C, F = OLD["C"], OLD["F"]
M = runpy.run_path(str(HERE / "memory.py"))
T = runpy.run_path(str(HERE / "training.py"))
D = runpy.run_path(str(HERE / "provenance.py"))


def specifications(informative):
    if informative not in ("structured", "scalar", "both"):
        raise ValueError("Unknown informative feedback form")
    feedbacks = (
        ("structured", "scalar", "constant") if informative == "both" else (informative, "constant")
    )
    return [
        (f"{memory}-{feedback}", memory, feedback)
        for memory in ("embedding", "contextual")
        for feedback in feedbacks
    ]


class Runner(OLD["Runner"]):
    def __init__(self, model, tok, eos, manifest, output, feedback):
        self.specs = specifications(manifest["informative"])
        if len(eos) != 1:
            raise ValueError("Candidate memory binds one explicit EOS token")
        (output / "memories").mkdir(exist_ok=False)
        super().__init__(model, tok, eos, manifest, output, feedback)

    def answer(self, case, arm, prompt, *, adapter=None, memory=None, probabilities=None):
        self.deadline()
        if (adapter is None) != (memory is None) or (adapter is None) != (probabilities is None):
            raise ValueError("Incomplete correction binding")
        tick = time.monotonic()
        binding = dict(
            id=case["id"],
            arm=arm,
            memory_digest=D["tensor_digest"](memory) if memory is not None else None,
            adapter_digest=self.runtime["weight_digest"](adapter) if adapter is not None else None,
            probabilities=probabilities,
            at=F["now"](),
        )
        binding["seconds"] = time.monotonic() - tick
        F["append"](self.output / "generation-bindings.jsonl", binding)
        return super().answer(
            case, arm, prompt, adapter=adapter, memory=memory, probabilities=probabilities
        )

    async def drafts(self, cases, refs):
        from safetensors.torch import save_file

        for case in cases:
            self.deadline()
            C["validate_case"](case)
            if case["id"] in self.prepared or any(
                row["id"] == case["id"] and row["arm"] == "native" for row in self.rows
            ):
                raise ValueError("Duplicate native draft request")
            ids = self.tok.apply_chat_template(
                [dict(role="user", content=case["prompt"])],
                tokenize=True,
                add_generation_prompt=True,
            )
            native = self.answer(case, "native", ids)
            values = C["probabilities"](await self.feedback.score(case, native["text"]))
            self.deadline()
            aligned = M["positions_for"](self.tok, case, native, eos=self.eos[0])
            extracted = M["memories"](
                self.model, aligned["ids"], aligned["slots"], layer=self.m["layer"]
            )
            memory = {kind: extracted[kind] for kind in ("embedding", "contextual")}
            name = "memories/" + hashlib.sha256(case["id"].encode()).hexdigest() + ".safetensors"
            path = self.output / name
            if path.exists():
                raise FileExistsError("Memory evidence already exists")
            save_file(memory, str(path))
            F["append"](
                self.output / "memory-records.jsonl",
                dict(
                    id=case["id"],
                    input_token_ids=aligned["ids"],
                    positions=extracted["positions"],
                    layer=extracted["layer"],
                    processed_tokens=extracted["processed_tokens"],
                    seconds=extracted["seconds"],
                    file=name,
                    sha256=C["sha"](path),
                    shape=list(memory["contextual"].shape),
                    at=F["now"](),
                ),
            )
            # Truth is accessed only after reference-free extraction is archived.
            self.prepared[case["id"]] = dict(
                native=native,
                p=values,
                memories=memory,
                grade=C["grade"](native["text"], refs[case["id"]]),
                prompt=C["repair_prefix"](self.tok, ids, native["generated_token_ids"]),
            )

    def train(self, train, dev, refs):
        return T["train"](
            self,
            train,
            dev,
            refs,
            specs=self.specs,
            **{
                key: self.m[key] for key in ("seeds", "epochs", "accumulate", "rank", "layer", "lr")
            },
        )

    def test(self, cases, adapters):
        donors = P["donors"](cases)
        C["dump"](self.output / "donors.json", donors)
        for case in cases:
            item = self.prepared[case["id"]]
            self.answer(case, "blind", item["prompt"])
            for seed in self.m["seeds"]:
                for name, memory_kind, feedback_kind in self.specs:
                    self.answer(
                        case,
                        f"{name}/{seed}",
                        item["prompt"],
                        adapter=adapters[name, seed],
                        memory=item["memories"][memory_kind],
                        probabilities=C["signal"](feedback_kind, item["p"]),
                    )
                for condition, memory_kind, informative in self.specs:
                    if informative == "constant":
                        continue
                    adapter = adapters[condition, seed]
                    diagnostic = {
                        "same_constant": [0.5] * 3,
                        "donor": C["signal"](informative, self.prepared[donors[case["id"]]]["p"]),
                        "oracle": C["signal"](
                            informative, [float(v) for v in item["grade"]["slots"]]
                        ),
                    }
                    for name, probabilities in diagnostic.items():
                        self.answer(
                            case,
                            f"{name}/{condition}/{seed}",
                            item["prompt"],
                            adapter=adapter,
                            memory=item["memories"][memory_kind],
                            probabilities=probabilities,
                        )
