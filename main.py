"""
K9 Technologies — AI Platform
FastAPI application powering the K9 Technologies website.

Endpoints
---------
GET  /             — Company website (landing page)
POST /chat         — Text chat with AI assistant (Gemini RAG)
POST /voice        — Voice chat: audio → Whisper → Gemini → JSON reply
POST /tts          — Text-to-speech: text → Gemini TTS → WAV audio
POST /contact      — Contact form saves lead to CSV
GET  /leads        — List all captured leads
GET  /leads/{id}   — Single lead
GET  /health       — Health / readiness probe
"""
import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response

from config import settings
from services.gemini_rag import GeminiRAG
from services.gemini_tts import GeminiTTS
from services.lead_qualifier import INBOUND_SYSTEM_PROMPT
from services.lead_store import LeadStore
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
lead_store = LeadStore(csv_path=settings.LEADS_CSV_PATH)

# session_id -> conversation history
_sessions: dict[str, list[dict]] = {}

# ── HTML template ─────────────────────────────────────────────────────────────
_TEMPLATE_PATH = Path(__file__).parent / "templates" / "index.html"


def _get_html() -> str:
    return _TEMPLATE_PATH.read_text(encoding="utf-8")


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("K9 Technologies platform started — KB chunks: %d", len(gemini_rag.chunks))
    yield
    logger.info("Shutting down")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="K9 Technologies", version="1.0.0", lifespan=lifespan)


# ── Website ───────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def website() -> HTMLResponse:
    return HTMLResponse(_get_html())


# ── Text chat ─────────────────────────────────────────────────────────────────
@app.post("/chat")
async def chat(request: Request) -> JSONResponse:
    body = await request.json()
    message = (body.get("message") or "").strip()
    session_id = (body.get("session_id") or "").strip() or str(uuid.uuid4())

    if not message:
        return JSONResponse({"error": "empty message"}, status_code=400)

    history = _sessions.get(session_id, [])
    reply = await gemini_rag.generate_response(
        message, history, system_prompt=INBOUND_SYSTEM_PROMPT
    )
    history.extend([
        {"role": "user", "parts": [message]},
        {"role": "model", "parts": [reply]},
    ])
    _sessions[session_id] = history

    logger.info("Chat  user=%s | reply=%s", message[:80], reply[:80])
    return JSONResponse({"reply": reply, "session_id": session_id})


# ── Voice chat ────────────────────────────────────────────────────────────────
@app.post("/voice")
async def voice(
    audio: UploadFile = File(...),
    session_id: str = Form(default=""),
) -> JSONResponse:
    if not session_id:
        session_id = str(uuid.uuid4())

    wav = await audio.read()
    transcript = await whisper_client.transcribe(wav)

    if not transcript:
        return JSONResponse({"session_id": session_id, "transcript": "", "reply": ""})

    history = _sessions.get(session_id, [])
    reply = await gemini_rag.generate_response(
        transcript, history, system_prompt=INBOUND_SYSTEM_PROMPT
    )
    history.extend([
        {"role": "user", "parts": [transcript]},
        {"role": "model", "parts": [reply]},
    ])
    _sessions[session_id] = history

    logger.info("Voice  user=%s | reply=%s", transcript[:80], reply[:80])
    return JSONResponse({"session_id": session_id, "transcript": transcript, "reply": reply})


# ── Text-to-speech ────────────────────────────────────────────────────────────
@app.post("/tts")
async def tts(request: Request) -> Response:
    body = await request.json()
    text = (body.get("text") or "").strip()

    if not text:
        return JSONResponse({"error": "empty text"}, status_code=400)

    # Gemini TTS is synchronous (blocking SDK call); run in threadpool
    wav_bytes = await asyncio.get_event_loop().run_in_executor(
        None, gemini_tts.synthesize, text
    )

    if not wav_bytes:
        return JSONResponse({"error": "TTS synthesis failed"}, status_code=500)

    logger.info("TTS  chars=%d  wav_bytes=%d", len(text), len(wav_bytes))
    return Response(content=wav_bytes, media_type="audio/wav")


# ── Contact form ──────────────────────────────────────────────────────────────
@app.post("/contact")
async def contact(request: Request) -> JSONResponse:
    body = await request.json()
    name = (body.get("name") or "").strip()
    email = (body.get("email") or "").strip()

    if not name or not email:
        return JSONResponse({"error": "Name and email required"}, status_code=400)

    lead_id = lead_store.save_lead({
        "name": name,
        "phone": (body.get("phone") or "").strip(),
        "company": email,
        "service_interest": (body.get("service") or "").strip(),
        "pain_points": (body.get("message") or "").strip(),
        "call_type": "website-contact",
        "followup_scheduled": "false",
    })
    logger.info("Contact lead saved  id=%s  name=%s  email=%s", lead_id, name, email)
    return JSONResponse({"success": True, "lead_id": lead_id})


# ── Lead management ───────────────────────────────────────────────────────────
@app.get("/leads")
async def list_leads() -> JSONResponse:
    return JSONResponse(lead_store.list_leads())


@app.get("/leads/{lead_id}")
async def get_lead(lead_id: str) -> JSONResponse:
    lead = lead_store.get_lead(lead_id)
    if not lead:
        return JSONResponse({"error": "Lead not found"}, status_code=404)
    return JSONResponse(lead)


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health() -> JSONResponse:
    whisper_ok = await whisper_client.health_check()
    return JSONResponse({
        "status": "healthy",
        "whisper_api": "ok" if whisper_ok else "unreachable",
        "kb_chunks": len(gemini_rag.chunks),
        "total_leads": len(lead_store.list_leads()),
    })


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.SERVER_PORT, reload=False)
