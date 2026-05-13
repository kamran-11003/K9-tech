"""
K9 Technologies — AI Platform
FastAPI application powering the K9 Technologies website.

Endpoints
---------
GET  /                         — Company website (landing page)
POST /chat                     — Text chat with Aria (Gemini RAG + tool dispatch)
POST /voice                    — Voice chat: audio → Whisper → Aria → JSON reply
POST /tts                      — Text-to-speech: text → Gemini TTS → WAV audio
POST /contact                  — Contact form saves lead to MongoDB
GET  /leads                    — List all captured leads
GET  /leads/{id}               — Single lead
GET  /appointments/slots       — Available appointment slots (next 14 days)
GET  /appointments             — List appointments (optional ?email=)
POST /appointments             — Book appointment
PATCH /appointments/{id}       — Update / reschedule appointment
DELETE /appointments/{id}      — Cancel appointment
GET  /health                   — Health / readiness probe
"""
import asyncio
import logging
import re
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from config import settings
from services.aria_tools import (
    execute_action,
    format_tool_result_for_model,
    plan_action,
)
from services.gemini_rag import GeminiRAG
from services.gemini_tts import GeminiTTS
from services.lead_qualifier import INBOUND_SYSTEM_PROMPT
from services.mongo_store import MongoStore
from services.whisper_client import WhisperClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ── Services ──────────────────────────────────────────────────────────────────
whisper_client = WhisperClient(api_url=settings.WHISPER_API_URL)
gemini_rag = GeminiRAG(api_key=settings.GEMINI_API_KEY, data_dir=settings.DATA_DIR)
gemini_tts = GeminiTTS(api_key=settings.GEMINI_API_KEY, voice=settings.GEMINI_TTS_VOICE)
mongo = MongoStore(uri=settings.MONGO_URI, db_name=settings.MONGO_DB)

# session_id -> conversation history
_sessions: dict[str, list[dict]] = {}

# ── HTML template ─────────────────────────────────────────────────────────────
_TEMPLATE_PATH = Path(__file__).parent / "templates" / "index.html"


def _get_html() -> str:
    return _TEMPLATE_PATH.read_text(encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# Production safety helpers — rate limiting, validation, admin guard
# ─────────────────────────────────────────────────────────────────────────────
_EMAIL_RE = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.IGNORECASE)
_PHONE_RE = re.compile(r"^[+0-9()\-\s]{7,25}$")
_SAFE_TEXT_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")  # control chars to strip

# Per-IP rolling timestamps for each bucket
_ip_buckets: dict[str, dict[str, deque]] = defaultdict(
    lambda: {
        "chat":    deque(),
        "contact": deque(),
        "booking": deque(),
    }
)


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _rate_limit(request: Request, bucket: str, limit: int, window_seconds: int) -> None:
    """Sliding-window per-IP limiter. Raises HTTPException(429) when exceeded."""
    if limit <= 0:
        return
    ip = _client_ip(request)
    now = time.time()
    dq = _ip_buckets[ip][bucket]
    cutoff = now - window_seconds
    while dq and dq[0] < cutoff:
        dq.popleft()
    if len(dq) >= limit:
        retry = int(window_seconds - (now - dq[0])) + 1
        raise HTTPException(
            status_code=429,
            detail=f"Too many requests — please wait {retry}s and try again.",
        )
    dq.append(now)


def _require_admin(token: Optional[str]) -> None:
    """Reject if ADMIN_TOKEN is configured and the header doesn't match."""
    expected = settings.ADMIN_TOKEN
    if not expected:
        return  # dev mode — endpoint stays open
    if not token or token != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _safe_text(value: str, max_len: int) -> str:
    if not value:
        return ""
    cleaned = _SAFE_TEXT_RE.sub("", str(value)).strip()
    return cleaned[:max_len]


def _valid_email(email: str) -> bool:
    return bool(email) and bool(_EMAIL_RE.match(email)) and len(email) <= 254


def _valid_phone(phone: str) -> bool:
    return not phone or bool(_PHONE_RE.match(phone))


def _valid_session_id(sid: str) -> bool:
    return bool(sid) and len(sid) <= 64 and re.fullmatch(r"[A-Za-z0-9_\-]+", sid) is not None


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic request models — automatic validation + rejection on bad payloads
# ─────────────────────────────────────────────────────────────────────────────
class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=settings.MAX_MESSAGE_CHARS)
    session_id: Optional[str] = None

    @field_validator("message")
    @classmethod
    def _clean_msg(cls, v: str) -> str:
        v = _safe_text(v, settings.MAX_MESSAGE_CHARS)
        if not v:
            raise ValueError("message empty")
        return v

    @field_validator("session_id")
    @classmethod
    def _check_sid(cls, v: Optional[str]) -> Optional[str]:
        if v and not _valid_session_id(v):
            raise ValueError("invalid session_id")
        return v


class TTSIn(BaseModel):
    text: str = Field(min_length=1, max_length=1000)

    @field_validator("text")
    @classmethod
    def _clean(cls, v: str) -> str:
        v = _safe_text(v, 1000)
        if not v:
            raise ValueError("text empty")
        return v


class ContactIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=254)
    phone: str = Field(default="", max_length=30)
    company: str = Field(default="", max_length=120)
    service: str = Field(default="", max_length=120)
    message: str = Field(default="", max_length=2000)

    @field_validator("email")
    @classmethod
    def _e(cls, v: str) -> str:
        v = v.strip().lower()
        if not _valid_email(v):
            raise ValueError("invalid email")
        return v

    @field_validator("phone")
    @classmethod
    def _p(cls, v: str) -> str:
        v = v.strip()
        if not _valid_phone(v):
            raise ValueError("invalid phone")
        return v

    @field_validator("name", "company", "service", "message", mode="before")
    @classmethod
    def _t(cls, v):
        return _safe_text(str(v or ""), 2000)


class BookingIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=254)
    phone: str = Field(default="", max_length=30)
    topic: str = Field(default="Discovery call", max_length=200)
    notes: str = Field(default="", max_length=1000)
    slot_iso: str = Field(min_length=10, max_length=40)

    @field_validator("email")
    @classmethod
    def _e(cls, v: str) -> str:
        v = v.strip().lower()
        if not _valid_email(v):
            raise ValueError("invalid email")
        return v

    @field_validator("phone")
    @classmethod
    def _p(cls, v: str) -> str:
        v = v.strip()
        if not _valid_phone(v):
            raise ValueError("invalid phone")
        return v

    @field_validator("name", "topic", "notes", mode="before")
    @classmethod
    def _t(cls, v):
        return _safe_text(str(v or ""), 2000)


class BookingPatchIn(BaseModel):
    slot_iso: Optional[str] = Field(default=None, max_length=40)
    name:  Optional[str]    = Field(default=None, max_length=120)
    email: Optional[str]    = Field(default=None, max_length=254)
    phone: Optional[str]    = Field(default=None, max_length=30)
    topic: Optional[str]    = Field(default=None, max_length=200)
    notes: Optional[str]    = Field(default=None, max_length=1000)

    @field_validator("email")
    @classmethod
    def _e(cls, v):
        if v is None:
            return v
        v = v.strip().lower()
        if not _valid_email(v):
            raise ValueError("invalid email")
        return v

    @field_validator("phone")
    @classmethod
    def _p(cls, v):
        if v is None:
            return v
        v = v.strip()
        if not _valid_phone(v):
            raise ValueError("invalid phone")
        return v


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "K9 Technologies platform started — KB chunks: %d  | Mongo: %s",
        len(gemini_rag.chunks),
        "ok" if mongo.ping() else "DOWN",
    )
    yield
    logger.info("Shutting down")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="K9 Technologies", version="1.2.0", lifespan=lifespan)

# CORS — in production set CORS_ORIGINS in .env to your domain(s)
_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins or ["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Static assets (CSS, JS, images) served at /static/*
_STATIC_DIR = Path(__file__).parent / "static"
_STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


# ── Global error handler ──────────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def _unhandled(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        {"ok": False, "error": "internal server error"},
        status_code=500,
    )


# ── Website ───────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def website() -> HTMLResponse:
    return HTMLResponse(_get_html())


# ─────────────────────────────────────────────────────────────────────────────
# Aria conversation core (shared by /chat and /voice)
# ─────────────────────────────────────────────────────────────────────────────
async def _aria_turn(user_text: str, session_id: str) -> tuple[str, dict]:
    """Run one Aria turn: plan → maybe execute tool → reply.
    Returns (reply_text, tool_result_dict)."""
    history = _sessions.get(session_id, [])

    # 1. Intent / tool planning
    plan = await plan_action(user_text, history)
    tool_result = execute_action(plan, mongo)
    tool_str = format_tool_result_for_model(tool_result)

    # 2. Build the system prompt — base persona + (optional) tool result
    system = INBOUND_SYSTEM_PROMPT
    if tool_str:
        system = INBOUND_SYSTEM_PROMPT + "\n\n" + tool_str

    # 3. Generate reply
    reply = await gemini_rag.generate_response(user_text, history, system_prompt=system)

    # 4. Persist conversation
    history.extend([
        {"role": "user",  "parts": [user_text]},
        {"role": "model", "parts": [reply]},
    ])
    # Trim to keep memory + token cost bounded
    max_msgs = settings.MAX_HISTORY_TURNS * 2
    if len(history) > max_msgs:
        history = history[-max_msgs:]
    _sessions[session_id] = history
    return reply, tool_result


# ── Text chat ─────────────────────────────────────────────────────────────────
@app.post("/chat")
async def chat(payload: ChatIn, request: Request) -> JSONResponse:
    _rate_limit(request, "chat", settings.RATE_LIMIT_PER_MIN, 60)
    session_id = payload.session_id or str(uuid.uuid4())
    reply, tool_result = await _aria_turn(payload.message, session_id)
    logger.info("Chat  user=%s | reply=%s | tool=%s",
                payload.message[:60], reply[:60], tool_result.get("tool"))
    return JSONResponse({
        "reply": reply,
        "session_id": session_id,
        "tool": tool_result.get("tool", "none"),
        "tool_ok": tool_result.get("ok"),
    })


# ── Voice chat ────────────────────────────────────────────────────────────────
@app.post("/voice")
async def voice(
    request: Request,
    audio: UploadFile = File(...),
    session_id: str = Form(default=""),
) -> JSONResponse:
    _rate_limit(request, "chat", settings.RATE_LIMIT_PER_MIN, 60)

    if session_id and not _valid_session_id(session_id):
        raise HTTPException(status_code=400, detail="invalid session_id")
    if not session_id:
        session_id = str(uuid.uuid4())

    wav = await audio.read()
    if not wav:
        raise HTTPException(status_code=400, detail="empty audio")
    if len(wav) > settings.MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="audio too large")

    transcript = await whisper_client.transcribe(wav)
    if not transcript:
        return JSONResponse({"session_id": session_id, "transcript": "", "reply": ""})

    transcript = _safe_text(transcript, settings.MAX_MESSAGE_CHARS)
    reply, tool_result = await _aria_turn(transcript, session_id)
    logger.info("Voice user=%s | reply=%s | tool=%s",
                transcript[:60], reply[:60], tool_result.get("tool"))
    return JSONResponse({
        "session_id": session_id,
        "transcript": transcript,
        "reply": reply,
        "tool": tool_result.get("tool", "none"),
    })


# ── Text-to-speech ────────────────────────────────────────────────────────────
@app.post("/tts")
async def tts(payload: TTSIn, request: Request) -> Response:
    _rate_limit(request, "chat", settings.RATE_LIMIT_PER_MIN, 60)
    text = payload.text

    try:
        wav_bytes = await asyncio.get_event_loop().run_in_executor(
            None, gemini_tts.synthesize, text
        )
    except Exception as exc:
        err_str = str(exc)
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            logger.warning("TTS quota exceeded")
            return JSONResponse({"error": "TTS quota exceeded — please try again later"}, status_code=429)
        logger.exception("TTS error")
        return JSONResponse({"error": "TTS synthesis failed"}, status_code=500)

    if not wav_bytes:
        return JSONResponse({"error": "TTS synthesis failed"}, status_code=500)

    logger.info("TTS chars=%d wav_bytes=%d", len(text), len(wav_bytes))
    return Response(content=wav_bytes, media_type="audio/wav")


# ── Contact form ──────────────────────────────────────────────────────────────
@app.post("/contact")
async def contact(payload: ContactIn, request: Request) -> JSONResponse:
    _rate_limit(request, "contact", settings.CONTACT_LIMIT_PER_HOUR, 3600)

    lead_id = mongo.save_lead({
        "name": payload.name,
        "email": payload.email,
        "phone": payload.phone,
        "company": payload.company,
        "service_interest": payload.service,
        "message": payload.message,
        "source": "website-contact",
    })
    logger.info("Lead saved id=%s name=%s email=%s", lead_id, payload.name, payload.email)
    return JSONResponse({"success": True, "lead_id": lead_id})


# ── Lead management (admin-guarded) ──────────────────────────────────────────
@app.get("/leads")
async def list_leads(x_admin_token: Optional[str] = Header(default=None)) -> JSONResponse:
    _require_admin(x_admin_token)
    return JSONResponse(mongo.list_leads())


@app.get("/leads/{lead_id}")
async def get_lead(lead_id: str, x_admin_token: Optional[str] = Header(default=None)) -> JSONResponse:
    _require_admin(x_admin_token)
    if not re.fullmatch(r"[A-Za-z0-9\-]{8,64}", lead_id):
        raise HTTPException(status_code=400, detail="invalid id")
    lead = mongo.get_lead(lead_id)
    if not lead:
        return JSONResponse({"error": "Lead not found"}, status_code=404)
    return JSONResponse(lead)


# ── Appointment endpoints ─────────────────────────────────────────────────────
@app.get("/appointments/slots")
async def appointment_slots() -> JSONResponse:
    return JSONResponse({"slots": mongo.list_available_slots()})


@app.get("/appointments")
async def list_appointments(
    email: str = "",
    x_admin_token: Optional[str] = Header(default=None),
) -> JSONResponse:
    if not email:
        _require_admin(x_admin_token)
        return JSONResponse(mongo.list_appointments())
    email = email.strip().lower()
    if not _valid_email(email):
        raise HTTPException(status_code=400, detail="invalid email")
    return JSONResponse(mongo.list_appointments(email=email))


@app.post("/appointments")
async def book_appointment(payload: BookingIn, request: Request) -> JSONResponse:
    _rate_limit(request, "booking", settings.BOOKING_LIMIT_PER_DAY, 86400)
    _rate_limit(request, "contact", settings.CONTACT_LIMIT_PER_HOUR, 3600)

    result = mongo.book_appointment(payload.model_dump())
    if not result.get("ok"):
        return JSONResponse(result, status_code=400)
    logger.info("Appointment booked id=%s slot=%s",
                result["appointment"]["id"], result["appointment"]["slot_iso"])
    return JSONResponse(result)


@app.patch("/appointments/{appt_id}")
async def patch_appointment(appt_id: str, payload: BookingPatchIn) -> JSONResponse:
    if not re.fullmatch(r"[A-Za-z0-9\-]{8,64}", appt_id):
        raise HTTPException(status_code=400, detail="invalid id")
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="nothing to update")
    result = mongo.update_appointment(appt_id, updates)
    if not result.get("ok"):
        return JSONResponse(result, status_code=400)
    return JSONResponse(result)


@app.delete("/appointments/{appt_id}")
async def cancel_appointment(appt_id: str) -> JSONResponse:
    if not re.fullmatch(r"[A-Za-z0-9\-]{8,64}", appt_id):
        raise HTTPException(status_code=400, detail="invalid id")
    result = mongo.cancel_appointment(appt_id)
    if not result.get("ok"):
        return JSONResponse(result, status_code=400)
    return JSONResponse(result)


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health() -> JSONResponse:
    whisper_ok = await whisper_client.health_check()
    mongo_ok = mongo.ping()
    body = {
        "status": "healthy" if mongo_ok else "degraded",
        "whisper_api": "ok" if whisper_ok else "unreachable",
        "mongo": "ok" if mongo_ok else "down",
        "kb_chunks": len(gemini_rag.chunks),
        "version": app.version,
    }
    return JSONResponse(body, status_code=200 if mongo_ok else 503)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.SERVER_PORT, reload=False)
