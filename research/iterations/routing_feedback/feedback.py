"""R28 stops on unresolved delivery; it never replays an ambiguous paid request."""

import runpy
from pathlib import Path

OLD = runpy.run_path(str(Path(__file__).resolve().parents[1] / "selective_benchmarks/feedback.py"))
append, now, payload = (OLD[k] for k in ("append", "now", "payload"))


class Feedback(OLD["Feedback"]):
    def retain(self, reservation):
        # Leave the full reservation charged. Explicitly stop instead of inheriting
        # R26's permission to proceed after a missing judgment or rejected attempt.
        raise RuntimeError("R28 unresolved provider request; study stopped without replay")
