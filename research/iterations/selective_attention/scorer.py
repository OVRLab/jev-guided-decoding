"""R17 authorization label over the existing validated, one-attempt Jev transport."""

import runpy
from pathlib import Path

OLD = runpy.run_path(str(Path(__file__).resolve().parents[1] / "adaptive_attention/scorer.py"))
StudyClient = OLD["StudyClient"]
payload_for = OLD["payload_for"]


class ReceiptStore(OLD["ReceiptStore"]):
    def charge_unknown(self, reservation):
        self.budget.acknowledge_max_charge(
            reservation,
            reason="Failed R17 attempt; never replay this payload",
            authorization="User authorized bounded R17 study; prospective failure policy",
        )
