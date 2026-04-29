"""
MongoDB Store
-------------
Replaces the old CSV LeadStore. Stores two collections:

  leads        — captured contact-form / chat leads
  appointments — booked discovery-call slots

Connection string + DB name come from the environment via config.Settings.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError, PyMongoError

logger = logging.getLogger(__name__)


# Business hours — used to generate the bookable slot grid
WORK_HOURS = list(range(9, 18))   # 09:00 – 17:00 inclusive (last slot 17:00)
SLOT_MINUTES = 30                 # slot length
LOOKAHEAD_DAYS = 14               # how far ahead the calendar shows slots
MAX_PER_SLOT = 1                  # one booking per slot


class MongoStore:
    """Thin wrapper around two collections: leads + appointments."""

    def __init__(self, uri: str, db_name: str = "k9") -> None:
        self.uri = uri
        self.db_name = db_name
        self._client = MongoClient(uri, serverSelectionTimeoutMS=4000)
        self.db = self._client[db_name]
        self.leads: Collection = self.db["leads"]
        self.appointments: Collection = self.db["appointments"]
        self._setup_indexes()
        logger.info("MongoStore connected → %s / %s", uri, db_name)

    # ─────────────────────────────────────────────────────────────────── #
    # Indexes
    # ─────────────────────────────────────────────────────────────────── #
    def _setup_indexes(self) -> None:
        try:
            self.leads.create_index([("id", ASCENDING)], unique=True)
            self.leads.create_index([("created_at", ASCENDING)])
            self.appointments.create_index([("id", ASCENDING)], unique=True)
            self.appointments.create_index(
                [("slot_iso", ASCENDING), ("status", ASCENDING)],
            )
        except PyMongoError:
            logger.exception("Failed to create indexes (continuing anyway)")

    def ping(self) -> bool:
        try:
            self._client.admin.command("ping")
            return True
        except PyMongoError:
            return False

    # ─────────────────────────────────────────────────────────────────── #
    # Leads
    # ─────────────────────────────────────────────────────────────────── #
    def save_lead(self, data: dict) -> str:
        lead_id = data.get("id") or str(uuid.uuid4())
        doc = {
            "id": lead_id,
            "name": (data.get("name") or "").strip(),
            "email": (data.get("email") or "").strip(),
            "phone": (data.get("phone") or "").strip(),
            "company": (data.get("company") or "").strip(),
            "service_interest": (data.get("service_interest") or data.get("service") or "").strip(),
            "message": (data.get("message") or data.get("pain_points") or "").strip(),
            "source": data.get("source") or "website-contact",
            "created_at": datetime.now(timezone.utc),
        }
        try:
            self.leads.insert_one(doc)
        except DuplicateKeyError:
            self.leads.update_one({"id": lead_id}, {"$set": doc})
        return lead_id

    def list_leads(self) -> list[dict]:
        return [_clean(d) for d in self.leads.find().sort("created_at", -1)]

    def get_lead(self, lead_id: str) -> Optional[dict]:
        doc = self.leads.find_one({"id": lead_id})
        return _clean(doc) if doc else None

    # ─────────────────────────────────────────────────────────────────── #
    # Appointments
    # ─────────────────────────────────────────────────────────────────── #
    def list_available_slots(self) -> list[str]:
        """Return ISO-formatted slot strings (UTC) for the next LOOKAHEAD_DAYS."""
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        end = now + timedelta(days=LOOKAHEAD_DAYS)

        # taken slots in window
        taken = {
            d["slot_iso"]
            for d in self.appointments.find(
                {
                    "slot_iso": {"$gte": now.isoformat(), "$lte": end.isoformat()},
                    "status": {"$ne": "cancelled"},
                },
                {"slot_iso": 1, "_id": 0},
            )
        }

        slots: list[str] = []
        day = now.replace(hour=0)
        for _ in range(LOOKAHEAD_DAYS + 1):
            for h in WORK_HOURS:
                for m in range(0, 60, SLOT_MINUTES):
                    slot = day.replace(hour=h, minute=m)
                    if slot <= now:
                        continue
                    iso = slot.isoformat()
                    if iso not in taken:
                        slots.append(iso)
            day += timedelta(days=1)
        return slots

    def list_appointments(self, email: Optional[str] = None) -> list[dict]:
        q: dict = {"status": {"$ne": "cancelled"}}
        if email:
            q["email"] = email.strip().lower()
        return [_clean(d) for d in self.appointments.find(q).sort("slot_iso", 1)]

    def get_appointment(self, appt_id: str) -> Optional[dict]:
        doc = self.appointments.find_one({"id": appt_id})
        return _clean(doc) if doc else None

    def book_appointment(self, data: dict) -> dict:
        """
        Create an appointment if the slot is still free.
        Returns {"ok":True, "appointment":{...}} or {"ok":False, "error":"..."}.
        """
        name  = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip().lower()
        slot_iso = (data.get("slot_iso") or "").strip()
        if not name or not email or not slot_iso:
            return {"ok": False, "error": "name, email and slot_iso are required"}

        try:
            slot_dt = datetime.fromisoformat(slot_iso)
        except ValueError:
            return {"ok": False, "error": "slot_iso must be ISO 8601"}

        # Slot sanity: must be in the future, within lookahead window, on a valid grid time
        now = datetime.now(timezone.utc)
        if slot_dt.tzinfo is None:
            slot_dt = slot_dt.replace(tzinfo=timezone.utc)
        if slot_dt <= now:
            return {"ok": False, "error": "Slot must be in the future"}
        if slot_dt > now + timedelta(days=LOOKAHEAD_DAYS + 1):
            return {"ok": False, "error": f"Slot too far ahead (max {LOOKAHEAD_DAYS} days)"}
        if slot_dt.hour not in WORK_HOURS or slot_dt.minute % SLOT_MINUTES != 0:
            return {"ok": False, "error": "Slot is outside business hours"}

        # Conflict check — same slot
        existing = self.appointments.count_documents(
            {"slot_iso": slot_iso, "status": {"$ne": "cancelled"}}
        )
        if existing >= MAX_PER_SLOT:
            return {"ok": False, "error": "That slot is already taken"}

        # Duplicate-email guard — block more than one upcoming booking per email
        dupe = self.appointments.find_one({
            "email": email,
            "status": {"$ne": "cancelled"},
            "slot_iso": {"$gte": now.isoformat()},
        })
        if dupe:
            return {
                "ok": False,
                "error": "You already have an upcoming booking. Please cancel or reschedule it first.",
                "existing_id": dupe.get("id"),
            }

        appt_id = str(uuid.uuid4())
        doc = {
            "id": appt_id,
            "name": name,
            "email": email,
            "phone": (data.get("phone") or "").strip(),
            "topic": (data.get("topic") or "Discovery call").strip(),
            "notes": (data.get("notes") or "").strip(),
            "slot_iso": slot_iso,
            "slot_at": slot_dt,
            "status": "booked",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        self.appointments.insert_one(doc)
        return {"ok": True, "appointment": _clean(doc)}

    def update_appointment(self, appt_id: str, updates: dict) -> dict:
        """Move an appointment to a new slot or update its details."""
        existing = self.appointments.find_one({"id": appt_id})
        if not existing:
            return {"ok": False, "error": "Appointment not found"}
        if existing.get("status") == "cancelled":
            return {"ok": False, "error": "Appointment is cancelled"}

        patch: dict = {}
        if "slot_iso" in updates:
            new_slot = (updates["slot_iso"] or "").strip()
            try:
                new_dt = datetime.fromisoformat(new_slot)
            except ValueError:
                return {"ok": False, "error": "slot_iso must be ISO 8601"}
            conflict = self.appointments.count_documents(
                {
                    "slot_iso": new_slot,
                    "status": {"$ne": "cancelled"},
                    "id": {"$ne": appt_id},
                }
            )
            if conflict >= MAX_PER_SLOT:
                return {"ok": False, "error": "Requested slot is taken"}
            patch["slot_iso"] = new_slot
            patch["slot_at"] = new_dt

        for field in ("name", "email", "phone", "topic", "notes"):
            if field in updates and updates[field] is not None:
                val = str(updates[field]).strip()
                if field == "email":
                    val = val.lower()
                patch[field] = val

        if not patch:
            return {"ok": False, "error": "Nothing to update"}

        patch["updated_at"] = datetime.now(timezone.utc)
        self.appointments.update_one({"id": appt_id}, {"$set": patch})
        return {"ok": True, "appointment": self.get_appointment(appt_id)}

    def cancel_appointment(self, appt_id: str) -> dict:
        res = self.appointments.update_one(
            {"id": appt_id, "status": {"$ne": "cancelled"}},
            {"$set": {"status": "cancelled", "updated_at": datetime.now(timezone.utc)}},
        )
        if res.matched_count == 0:
            return {"ok": False, "error": "Appointment not found or already cancelled"}
        return {"ok": True, "appointment": self.get_appointment(appt_id)}

    def find_appointment_by_email(self, email: str) -> Optional[dict]:
        """Return the next upcoming booked appointment for an email."""
        now_iso = datetime.now(timezone.utc).isoformat()
        doc = self.appointments.find_one(
            {
                "email": email.strip().lower(),
                "status": {"$ne": "cancelled"},
                "slot_iso": {"$gte": now_iso},
            },
            sort=[("slot_iso", 1)],
        )
        return _clean(doc) if doc else None


def _clean(doc: Optional[dict]) -> dict:
    """Drop Mongo internals + serialise datetimes to ISO."""
    if not doc:
        return {}
    out = {}
    for k, v in doc.items():
        if k == "_id":
            continue
        if isinstance(v, datetime):
            out[k] = v.astimezone(timezone.utc).isoformat()
        else:
            out[k] = v
    return out
