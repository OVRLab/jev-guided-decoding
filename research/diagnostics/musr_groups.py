"""Bind MuSR evaluation units to author metadata without using correctness labels."""

import ast
import hashlib
import json

FAMILIES = {"murder_mystery", "object_placements", "team_allocation"}


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def signature(context, question, choices):
    if (
        not isinstance(context, str)
        or not context
        or not isinstance(question, str)
        or not question
        or not isinstance(choices, list)
        or not choices
        or any(not isinstance(c, str) for c in choices)
    ):
        raise ValueError("Invalid source question signature")
    return digest([context, question, choices])


def source_groups(family, records):
    if family not in FAMILIES or not records:
        raise ValueError("Unknown or empty source family")
    result = {}
    for row in records:
        for question in row["questions"]:
            if family == "object_placements":
                key = row["context"]
            else:
                data = question.get("intermediate_data", [])
                if len(data) != 1 or not isinstance(data[0], dict):
                    raise ValueError("Missing unique author metadata")
                metadata = data[0]
                if family == "murder_mystery":
                    key = metadata.get("story_hash_id")
                    if type(key) is not int:
                        raise ValueError("Missing author scenario identifier")
                else:
                    tasks, matrix = metadata.get("tasks"), metadata.get("matrix")
                    if (
                        not isinstance(tasks, list)
                        or not tasks
                        or any(not isinstance(t, str) for t in tasks)
                        or not isinstance(matrix, dict)
                        or not matrix
                        or any(not isinstance(n, str) for n in matrix)
                    ):
                        raise ValueError("Missing author task/character identities")
                    # Matrix values, best allocations, answers and reasoning trees
                    # never enter a grouping key or model payload.
                    key = [tasks, sorted(matrix)]
            sig = signature(row["context"], question["question"], question["choices"])
            if sig in result:
                raise ValueError("Duplicate source question signature")
            result[sig] = family + "/" + digest(key)
    return result


def bind_rows(family, rows, groups):
    if family not in FAMILIES or not rows:
        raise ValueError("Unknown or empty row family")
    result, seen = {}, set()
    for index, row in enumerate(rows):
        sig = signature(row["narrative"], row["question"], ast.literal_eval(row["choices"]))
        if sig not in groups or sig in seen or not groups[sig].startswith(family + "/"):
            raise ValueError("CSV row does not have a unique matching source")
        seen.add(sig)
        result[f"musr/{family}/{index}"] = groups[sig]
    if seen != set(groups):
        raise ValueError("CSV/source coverage differs")
    return result
