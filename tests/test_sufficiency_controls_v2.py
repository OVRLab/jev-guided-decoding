import copy
import json
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_saved_prompt_binding_accepts_json_roundtrip_but_rejects_content_changes():
    s = runpy.run_path(str(ROOT / "research/iterations/sufficiency_controls_v2.py"))
    runtime = {
        "id": "example",
        "input_ids": [7, 11, 13],
        "character_ranges": [(0, 7), (8, 13)],
        "rendered_prompt": "source prompt",
        "prompt_digest": "fixed",
    }
    stored = json.loads(json.dumps(runtime))
    assert runtime != stored
    s["validate_prompt_binding"](runtime, stored)
    for key, changed in (
        ("input_ids", [7, 11, 17]),
        ("character_ranges", [[0, 8], [8, 13]]),
        ("rendered_prompt", "altered prompt"),
        ("prompt_digest", "different"),
    ):
        altered = copy.deepcopy(stored)
        altered[key] = changed
        with pytest.raises(ValueError, match="Supplement prompt changed"):
            s["validate_prompt_binding"](runtime, altered)
