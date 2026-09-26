"""Reference-free serial transfer components, without a paid execution entrypoint."""

import hashlib
import json
import math
import re
import runpy
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
S = runpy.run_path(str(HERE / "single.py"))
F = runpy.run_path(str(HERE / "feedback.py"))
D = runpy.run_path(str(HERE.parent / "contextual_memory/provenance.py"))
append, now = F["append"], F["now"]


def donors(cases, groups):
    if (
        not cases
        or len({c["id"] for c in cases}) != len(cases)
        or set(groups) != {c["id"] for c in cases}
    ):
        raise ValueError("Incomplete or duplicated donor cohort")
    for case in cases:
        S["validate_case"](case)
        if not isinstance(groups[case["id"]], str) or not groups[case["id"]].startswith(
            case["task"] + "/"
        ):
            raise ValueError("Invalid donor group")
    result = {}
    for family in sorted({c["task"] for c in cases}):
        ids = sorted((c["id"] for c in cases if c["task"] == family), key=lambda i: (groups[i], i))
        shift = max(sum(groups[i] == group for i in ids) for group in {groups[i] for i in ids})
        if 2 * shift > len(ids):
            raise ValueError("No scenario-independent donor derangement")
        result.update({ident: ids[(i + shift) % len(ids)] for i, ident in enumerate(ids)})
    if set(result) != set(result.values()) or any(
        groups[a] == groups[b] for a, b in result.items()
    ):
        raise ValueError("Invalid donor derangement")
    return result


class Runner:
    def __init__(self, model, tok, eos, manifest, output, feedback):
        if (
            len(eos) != 1
            or eos[0] != tok.convert_tokens_to_ids("<|end_of_text|>")
            or any(
                type(manifest[k]) is not int or not 1 <= manifest[k] <= 1024
                for k in ("native_limit", "repair_limit")
            )
            or type(manifest["context_limit"]) is not int
            or not 1 <= manifest["context_limit"] <= 4096
            or type(manifest["max_seconds"]) not in (int, float)
            or not math.isfinite(manifest["max_seconds"])
            or not 0 < manifest["max_seconds"] <= 86400
            or type(manifest["layer"]) is not int
            or not 0 <= manifest["layer"] < len(model.model.layers)
        ):
            raise ValueError("Invalid transfer runtime contract")
        self.model, self.tok, self.eos, self.m = model, tok, eos, manifest
        self.output, self.feedback = output, feedback
        self.runtime = runpy.run_path(str(HERE / "runtime.py"))
        self.runtime["idle_frozen"](model)
        output.mkdir(parents=True, exist_ok=False)
        (output / "memories").mkdir()
        self.started_at = time.monotonic()
        self.started, self.prepared, self.rows = set(), {}, []
        self.repairs_started = False

    def deadline(self):
        if time.monotonic() - self.started_at > self.m["max_seconds"]:
            raise TimeoutError("Transfer worker deadline")

    def answer(self, case, arm, ids, *, adapter=None, memory=None, probabilities=None):
        self.deadline()
        S["validate_case"](case)
        if (case["id"], arm) in self.started:
            raise ValueError("Duplicate generation refused")
        if (adapter is None) != (memory is None) or (adapter is None) != (probabilities is None):
            raise ValueError("Incomplete transfer binding")
        self.started.add((case["id"], arm))
        tick = time.monotonic()
        binding = dict(
            id=case["id"],
            arm=arm,
            at=now(),
            memory_digest=D["tensor_digest"](memory) if memory is not None else None,
            adapter_digest=self.runtime["weight_digest"](adapter) if adapter is not None else None,
            probabilities=probabilities,
        )
        binding["seconds"] = time.monotonic() - tick
        append(self.output / "generation-bindings.jsonl", binding)
        append(self.output / "jobs.jsonl", dict(id=case["id"], arm=arm, event="start", at=now()))
        row = self.runtime["generate"](
            self.model,
            self.tok,
            ids,
            limit=self.m["native_limit" if arm == "native" else "repair_limit"],
            eos=self.eos,
            context_limit=self.m["context_limit"],
            adapter=adapter,
            memory=memory,
            probabilities=probabilities,
            layer=self.m["layer"],
            deadline=self.deadline,
        )
        row.update(
            id=case["id"],
            arm=arm,
            task=case["task"],
            split=case["split"],
            probabilities=probabilities,
            at=now(),
        )
        append(self.output / "outputs.jsonl", row)
        self.rows.append(row)
        append(self.output / "jobs.jsonl", dict(id=case["id"], arm=arm, event="finish", at=now()))
        return row

    async def drafts(self, cases):
        from safetensors.torch import save_file

        if self.feedback is None or not cases:
            raise ValueError("Draft preparation requires cases and a declared verifier")
        if len({c["id"] for c in cases}) != len(cases) or any(
            (c["id"], "native") in self.started for c in cases
        ):
            raise ValueError("Duplicate native draft refused")
        for case in cases:
            S["validate_case"](case)
        for case in cases:
            self.deadline()
            ids = self.tok.apply_chat_template(
                [dict(role="user", content=S["prompt_for"](case))],
                tokenize=True,
                add_generation_prompt=True,
            )
            native = self.answer(case, "native", ids)
            p = await self.feedback.score(case, native["text"])
            self.deadline()
            aligned = S["positions_for"](
                self.tok, case, native, eos=self.eos[0], limit=self.m["context_limit"]
            )
            memory = self.runtime["extract"](
                self.model, aligned["ids"], aligned["positions"], layer=self.m["layer"]
            )
            tensors = {k: memory[k] for k in ("embedding", "contextual")}
            # Validate probability before allowing it to bind to a stored prepared case.
            S["as_three_slots"](tensors["contextual"], p)
            name = "memories/" + hashlib.sha256(case["id"].encode()).hexdigest() + ".safetensors"
            path = self.output / name
            if path.exists():
                raise FileExistsError("Memory artifact already exists")
            save_file(tensors, str(path))
            append(
                self.output / "memory-records.jsonl",
                dict(
                    id=case["id"],
                    at=now(),
                    input_token_ids=aligned["ids"],
                    positions=aligned["positions"],
                    layer=self.m["layer"],
                    processed_tokens=memory["processed_tokens"],
                    seconds=memory["seconds"],
                    file=name,
                    sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                    shape=list(tensors["contextual"].shape),
                ),
            )
            self.prepared[case["id"]] = dict(
                native=native,
                p=p,
                memories=tensors,
                prompt=S["repair_prefix"](self.tok, ids, native["generated_token_ids"]),
            )

    def repairs(self, cases, groups, adapters):
        if self.repairs_started:
            raise ValueError("Duplicate repair phase refused")
        if set(self.prepared) != {c["id"] for c in cases} or not adapters:
            raise ValueError("Incomplete prepared cases or selected adapters")
        if any(
            not re.fullmatch(r"(contextual|embedding)-(scalar|structured|constant)", name)
            or type(seed) is not int
            or seed < 0
            for name, seed in adapters
        ):
            raise ValueError("Unknown transfer adapter binding")
        pairing = donors(cases, groups)
        self.repairs_started = True
        with (self.output / "donors.json").open("x") as stream:
            json.dump(pairing, stream, indent=2)
            stream.write("\n")
        for case in cases:
            item = self.prepared[case["id"]]
            self.answer(case, "blind", item["prompt"])
            self.answer(
                case,
                "text",
                S["repair_prefix"](
                    self.tok,
                    item["native"]["prompt_token_ids"],
                    item["native"]["generated_token_ids"],
                    feedback=item["p"],
                ),
            )
            for (name, seed), adapter in sorted(adapters.items()):
                vector = item["memories"][name.split("-")[0]]
                controls = (
                    (("constant", 0.5),)
                    if name.endswith("-constant")
                    else (
                        ("live", item["p"]),
                        ("constant", 0.5),
                        ("donor", self.prepared[pairing[case["id"]]]["p"]),
                    )
                )
                for control, p in controls:
                    memory, _ = S["as_three_slots"](vector, p)
                    self.answer(
                        case,
                        f"{control}/{name}/{seed}",
                        item["prompt"],
                        adapter=adapter,
                        memory=memory,
                        probabilities=[float(p)] * 3,
                    )
