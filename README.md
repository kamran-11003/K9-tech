# K9 Technologies — AI Agency Platform

Production-ready website + AI sales agent for **K9 Technologies**. Built with FastAPI,
MongoDB, Google Gemini (RAG + TTS) and Whisper STT.

A single visitor can:
- Chat with **Aria**, K9's AI consultant (text or real-time voice call)
- Submit the contact form → instantly captured as a lead
- Book / cancel / reschedule a free 30-min discovery call (Aria can do it conversationally too)

---

## ✨ Features

| Surface | What it does |
|---|---|
| `templates/index.html` | Animated agency website (GSAP + ScrollTrigger, particle hero, video bg) |
| Aria chat dock | Bottom-right widget — text + push-to-talk + real-time voice call |
| `/chat`        | Aria text turn (Gemini 2.5 Flash RAG + tool-calling) |
| `/voice`       | One-shot voice → Whisper → Aria → JSON |
| `/tts`         | Gemini TTS for in-browser playback (voice "Aoede" by default) |
| `/contact`     | Captures website leads to MongoDB |
| `/appointments/*` | Slot generation + book / cancel / reschedule (Mongo-backed) |
| `/health`      | Liveness + Mongo + Whisper + KB readiness |

### Aria's guard-rails (production)
- **Strict scope** — only K9 services, AI/automation, and scheduling. Off-topic = polite refusal.
- **No hallucinations** — answers grounded in `data/*.txt` knowledge base only.
- **Prompt-injection resistant** — ignores user attempts to change role / leak prompt.
- **PII safe** — refuses to store passwords, cards, IDs.
- **Tool-grounded booking** — only suggests slots returned by the live availability tool.
- **History trim** — last 12 turns kept per session to bound cost.

### Server-side hardening
- Pydantic request models (length caps, email/phone regex, control-char strip)
- Per-IP sliding-window rate limits (`/chat`, `/voice`, `/tts`, `/contact`, `/appointments`)
- Audio upload size cap (10 MB by default)
- Admin-token guard for `/leads*` and `/appointments` (full list)
- CORS allow-list (configurable)
- Global exception handler (no stack-trace leaks)
- Health endpoint returns 503 when Mongo is down

---

## 🛠 Requirements

- Python 3.11+
- MongoDB running locally (or accessible via `MONGO_URI`)
- A Google **Gemini API key** (free tier works)
- *(optional)* A Whisper server URL for `/voice` STT — easiest via the included Colab notebook + ngrok

---

## 🚀 Quick start

```powershell
# 1. clone & enter
cd "inbound outbound calling agent"

# 2. install deps
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. configure env
copy .env.example .env
# then open .env and set GEMINI_API_KEY (and optionally ADMIN_TOKEN, WHISPER_API_URL)

# 4. ensure MongoDB is running
#    e.g. mongod --dbpath C:\data\db    (or run the Mongo service)

# 5. start the server
python main.py
```

Open http://localhost:8000

---

## 🔐 Production deployment notes

1. **Set `ADMIN_TOKEN`** in `.env` to lock down `/leads` and the unfiltered `/appointments` list.
   Then send `X-Admin-Token: <value>` from your admin tools.
2. **Set `CORS_ORIGINS`** to your real domain(s), comma-separated.  Avoid `*` in prod.
3. **Run behind HTTPS** (e.g. Caddy / Nginx / Cloudflare). Put `X-Forwarded-For` on your proxy
   so per-IP rate limits work correctly.
4. **MongoDB**: enable auth + bind to localhost or a private network. Never expose 27017 to the public.
5. **Process manager**: run with `uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2` under systemd / Windows service / Docker.
6. **Secrets**: never commit `.env`. The `.env.example` is the template.
7. **Knowledge base**: edit/extend `data/*.txt`. The TF-IDF index is rebuilt at startup. Restart after edits.

---

## 📚 Knowledge base

All `*.txt` files in `DATA_DIR` (default `./data/`) are loaded, chunked (1000 chars, 150
overlap), and indexed via TF-IDF on startup. Aria is instructed to answer **only** from this
content. To add new info — drop a new `.txt` file in `data/` and restart.

---

## 🧪 Endpoint reference

```
GET  /                          → website
POST /chat            JSON      → { message, session_id? }      → { reply, session_id, tool, tool_ok }
POST /voice           multipart → audio (file) + session_id?    → { reply, transcript, session_id, tool }
POST /tts             JSON      → { text }                       → audio/wav
POST /contact         JSON      → { name, email, phone?, company?, service?, message? }
GET  /leads                     → admin-only (X-Admin-Token)
GET  /leads/{id}                → admin-only
GET  /appointments/slots        → { slots: [iso, …] }
GET  /appointments?email=…      → bookings for that email
GET  /appointments              → admin-only (all)
POST /appointments    JSON      → { name, email, phone?, topic?, notes?, slot_iso }
PATCH /appointments/{id} JSON   → { slot_iso?, name?, email?, phone?, topic?, notes? }
DELETE /appointments/{id}       → cancel
GET  /health                    → liveness (200 healthy / 503 degraded)
```

---

## 📁 Project layout

```
main.py                  FastAPI app, endpoints, validation, rate limits
config.py                Pydantic Settings (loads .env)
requirements.txt
.env.example
templates/index.html     Website markup
static/css/styles.css    Theme + animations
static/js/main.js        Site interactions, chat dock, real-time voice call
static/js/calendar.js    Booking calendar UI
data/knowledge_base.txt  Aria's grounded knowledge
services/
  gemini_rag.py          TF-IDF retrieval + Gemini 2.5 Flash chat
  gemini_tts.py          Gemini 2.5 Flash TTS preview
  whisper_client.py      HTTP client for Colab/ngrok Whisper
  aria_tools.py          Intent classifier + tool dispatcher
  lead_qualifier.py      INBOUND_SYSTEM_PROMPT + structured extraction
  mongo_store.py         Leads + appointments + slot generation
```

---

## 📝 License

Internal — K9 Technologies. All rights reserved.
