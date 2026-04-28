"""
Lead Store
----------
Thread-safe CSV database for leads collected during calls.

Columns
-------
id               — UUID, primary key
phone            — caller's E.164 phone number
name             — prospect's name
company          — prospect's company
service_interest — which service(s) they're interested in
budget           — stated budget
timeline         — stated timeline to start
decision_maker   — yes / no / shared
pain_points      — their main problem / goal
call_sid         — Twilio Call SID
call_type        — inbound | outbound
call_time        — ISO 8601 UTC timestamp of the call
followup_scheduled  — true | false
followup_called     — true | false
followup_outcome    — e.g. "booked discovery call", "voicemail", "no answer"
notes            — free-text notes from the agent
"""
import csv
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

COLUMNS: list[str] = [
    "id", "phone", "name", "company", "service_interest",
    "budget", "timeline", "decision_maker", "pain_points",
    "call_sid", "call_type", "call_time",
    "followup_scheduled", "followup_called", "followup_outcome", "notes",
]


class LeadStore:
    """CSV-backed lead database. All public methods are thread-safe."""

    def __init__(self, csv_path: str = "./data/leads.csv") -> None:
        self.path = Path(csv_path)
        self._lock = threading.Lock()
        self._ensure_file()

    # ------------------------------------------------------------------ #
    # Setup
    # ------------------------------------------------------------------ #

    def _ensure_file(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            with self._open_write() as f:
                csv.DictWriter(f, fieldnames=COLUMNS).writeheader()

    def _open_write(self):
        return open(self.path, "w", newline="", encoding="utf-8")

    def _open_read(self):
        return open(self.path, "r", newline="", encoding="utf-8")

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def save_lead(self, data: dict) -> str:
        """Append a new lead row. Returns the lead id."""
        lead_id = data.get("id") or str(uuid.uuid4())
        row = {col: data.get(col, "") for col in COLUMNS}
        row["id"] = lead_id
        row["call_time"] = row["call_time"] or datetime.now(timezone.utc).isoformat()
        row["followup_scheduled"] = row["followup_scheduled"] or "false"
        row["followup_called"] = row["followup_called"] or "false"

        with self._lock:
            with open(self.path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=COLUMNS)
                writer.writerow(row)
        return lead_id

    def get_lead(self, lead_id: str) -> Optional[dict]:
        """Return a single lead by id, or None."""
        with self._lock:
            with self._open_read() as f:
                for row in csv.DictReader(f):
                    if row["id"] == lead_id:
                        return dict(row)
        return None

    def update_lead(self, lead_id: str, updates: dict) -> bool:
        """In-place update of a lead row. Returns True if found."""
        with self._lock:
            rows: list[dict] = []
            found = False
            with self._open_read() as f:
                for row in csv.DictReader(f):
                    if row["id"] == lead_id:
                        row.update({k: v for k, v in updates.items() if k in COLUMNS})
                        found = True
                    rows.append(row)

            if found:
                with self._open_write() as f:
                    writer = csv.DictWriter(f, fieldnames=COLUMNS)
                    writer.writeheader()
                    writer.writerows(rows)
        return found

    def list_leads(self) -> list[dict]:
        """Return all leads as a list of dicts."""
        with self._lock:
            with self._open_read() as f:
                return [dict(row) for row in csv.DictReader(f)]

    def get_pending_followups(self) -> list[dict]:
        """Return inbound leads that need a follow-up call and haven't had one yet."""
        return [
            r for r in self.list_leads()
            if r.get("followup_scheduled") == "true"
            and r.get("followup_called") == "false"
            and r.get("phone", "").strip()
        ]

    def mark_followup_called(self, lead_id: str, outcome: str = "") -> None:
        self.update_lead(lead_id, {"followup_called": "true", "followup_outcome": outcome})
