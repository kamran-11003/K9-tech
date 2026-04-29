"""
Aria Tools
----------
Lightweight intent + slot extraction so the chat agent can:
  - list available appointment slots
  - book a discovery call
  - look up an existing booking by email
  - cancel an upcoming booking
  - reschedule an existing booking to a new slot

We let Gemini decide WHEN to act by asking it (between the user message
and the final reply) to emit a single JSON object describing the action.
The JSON is parsed; if it's a tool call, we execute it against MongoStore
and feed the structured result back into the model for the user-facing reply.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

import google.generativeai as genai

logger = logging.getLogger(__name__)

# Conservative cheap model for the planner step
_PLANNER_MODEL = "gemini-2.5-flash"

PLANNER_SYSTEM = """
You are an intent classifier for an AI sales assistant called Aria.
Read the user's latest message in the context of the conversation, and decide
whether the user is asking about appointments / discovery calls.

Return ONLY a single JSON object — nothing else. Schema:

{
  "action": "none" | "list_slots" | "book" | "lookup" | "cancel" | "reschedule",
  "name":  string|null,
  "email": string|null,
  "phone": string|null,
  "topic": string|null,
  "notes": string|null,
  "slot_iso": string|null,        // ISO 8601 in UTC, e.g. "2026-05-02T15:00:00+00:00"
  "appointment_id": string|null   // for cancel / reschedule when known from history
}

Rules:
- If the user just chats normally (pricing, services, greetings), action = "none".
- "book" requires intent to schedule. Missing fields are fine — set them to null.
- "lookup" = user asks about their existing booking.
- "cancel" / "reschedule" reference an existing booking; use email or appointment_id.
- Only fill slot_iso if the user gave a concrete date AND time. Otherwise leave null.
- The current UTC date-time is: {now_iso}
- Output JUST the JSON. No prose, no markdown, no code fences.
""".strip()


def _planner_model() -> "genai.GenerativeModel":
    return genai.GenerativeModel(_PLANNER_MODEL)


async def plan_action(user_message: str, history: list[dict]) -> dict[str, Any]:
    """Ask Gemini to classify the user's intent. Returns a dict (action='none' on parse fail)."""
    now_iso = datetime.now(timezone.utc).isoformat()
    sys = PLANNER_SYSTEM.replace("{now_iso}", now_iso)

    # Compact history for the planner
    convo = []
    for turn in history[-6:]:
        role = "User" if turn.get("role") == "user" else "Aria"
        parts = turn.get("parts") or []
        text = parts[0] if parts else ""
        convo.append(f"{role}: {text}")
    convo.append(f"User: {user_message}")
    convo_str = "\n".join(convo)

    prompt = f"{sys}\n\n=== CONVERSATION ===\n{convo_str}\n\n=== JSON ==="

    try:
        resp = await _planner_model().generate_content_async(prompt)
        raw = (resp.text or "").strip()
        return _parse_json(raw)
    except Exception:
        logger.exception("plan_action failed")
        return {"action": "none"}


def _parse_json(raw: str) -> dict[str, Any]:
    """Robust JSON parse — strips ```json fences and surrounding prose."""
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?", "", raw, flags=re.IGNORECASE).strip()
    raw = re.sub(r"```$", "", raw).strip()
    # find the first {...} block
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        return {"action": "none"}
    try:
        data = json.loads(m.group(0))
        if not isinstance(data, dict):
            return {"action": "none"}
        data.setdefault("action", "none")
        return data
    except json.JSONDecodeError:
        return {"action": "none"}


# ─────────────────────────────────────────────────────────────────────────────
# Tool dispatcher
# ─────────────────────────────────────────────────────────────────────────────
def execute_action(plan: dict[str, Any], store) -> dict[str, Any]:
    """
    Run the planned action against MongoStore.
    Returns a dict containing the structured tool result, suitable for
    feeding back into the response model.
    """
    action = (plan.get("action") or "none").lower()

    if action == "none":
        return {"tool": "none"}

    if action == "list_slots":
        slots = store.list_available_slots()[:30]
        return {"tool": "list_slots", "slots": slots}

    if action == "book":
        # Need name + email + slot — otherwise return "missing"
        missing = [k for k in ("name", "email", "slot_iso") if not plan.get(k)]
        if missing:
            return {
                "tool": "book",
                "ok": False,
                "missing": missing,
                "available_slots": store.list_available_slots()[:12],
            }
        # Light email sanity check before hitting the store
        email = (plan.get("email") or "").strip()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            return {
                "tool": "book",
                "ok": False,
                "error": "Email address looks invalid — please confirm it.",
            }
        result = store.book_appointment({
            "name":  plan.get("name"),
            "email": email,
            "phone": plan.get("phone") or "",
            "topic": plan.get("topic") or "Discovery call",
            "notes": plan.get("notes") or "",
            "slot_iso": plan.get("slot_iso"),
        })
        result["tool"] = "book"
        return result

    if action == "lookup":
        if plan.get("appointment_id"):
            doc = store.get_appointment(plan["appointment_id"])
        elif plan.get("email"):
            doc = store.find_appointment_by_email(plan["email"])
        else:
            return {"tool": "lookup", "ok": False, "missing": ["email or appointment_id"]}
        return {"tool": "lookup", "ok": bool(doc), "appointment": doc}

    if action == "cancel":
        appt_id = plan.get("appointment_id")
        if not appt_id and plan.get("email"):
            doc = store.find_appointment_by_email(plan["email"])
            if doc:
                appt_id = doc["id"]
        if not appt_id:
            return {"tool": "cancel", "ok": False, "missing": ["appointment_id or email"]}
        result = store.cancel_appointment(appt_id)
        result["tool"] = "cancel"
        return result

    if action == "reschedule":
        if not plan.get("slot_iso"):
            return {
                "tool": "reschedule",
                "ok": False,
                "missing": ["slot_iso"],
                "available_slots": store.list_available_slots()[:12],
            }
        appt_id = plan.get("appointment_id")
        if not appt_id and plan.get("email"):
            doc = store.find_appointment_by_email(plan["email"])
            if doc:
                appt_id = doc["id"]
        if not appt_id:
            return {"tool": "reschedule", "ok": False, "missing": ["appointment_id or email"]}
        result = store.update_appointment(appt_id, {"slot_iso": plan["slot_iso"]})
        result["tool"] = "reschedule"
        return result

    return {"tool": "none"}


def format_tool_result_for_model(tool_result: dict[str, Any]) -> str:
    """Serialise the tool outcome so the response model can read it as system context."""
    if not tool_result or tool_result.get("tool") in (None, "none"):
        return ""
    return (
        "[INTERNAL TOOL RESULT — do NOT mention internal IDs unless asked]\n"
        + json.dumps(tool_result, indent=2, default=str)
        + "\nUse this result to craft your final reply naturally and conversationally. "
        + "If a booking succeeded, confirm date/time in human-friendly form. "
        + "If something is missing, ask the user for it. "
        + "If listing slots, suggest 2-4 specific times in a natural sentence."
    )
