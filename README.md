# AI Inbound & Outbound Calling Agent

End-to-end voice agent built with **Twilio Media Streams → Whisper → Gemini (RAG) → ElevenLabs**.

```
Caller ──── Twilio ──── WebSocket ──── Whisper (Colab/ngrok)
                                            │
                                       Gemini 1.5 Flash
                                       + PDF knowledge base
                                            │
                                       ElevenLabs TTS
                                            │
                             ──── Twilio ──── Caller
```

---

## Prerequisites

| Service | What you need |
|---------|--------------|
| [Twilio](https://twilio.com) | Account SID, Auth Token, phone number |
| [Google AI Studio](https://aistudio.google.com) | Gemini API key |
| [ElevenLabs](https://elevenlabs.io) | API key + Voice ID |
| Google Colab | Run the Whisper notebook (see below) |
| [ngrok](https://ngrok.com) | Expose local port 8000 to the internet |

---

## Quick-start

### 1 — Whisper server (Google Colab)

Open the provided Colab notebook, run all cells, and copy the printed
ngrok URL.  It exposes a `/transcribe` endpoint built on `faster-whisper`
running on a T4 GPU.

### 2 — Local setup

```bash
# Clone / open this folder, then:
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### 3 — Environment

```bash
copy .env.example .env          # Windows
# Edit .env and fill in all values
```

### 4 — PDF knowledge base

Drop any number of `.pdf` files into the `data/` directory.

### 5 — Expose the server with ngrok

```bash
ngrok http 8000
# Copy the hostname (e.g. abcd-12-34-56-78.ngrok-free.app)
# Set SERVER_HOST=abcd-12-34-56-78.ngrok-free.app in .env
```

### 6 — Run the agent

```bash
python main.py
```

### 7 — Configure Twilio

In the [Twilio Console](https://console.twilio.com):

* Go to **Phone Numbers → Manage → Active Numbers → your number**
* Under **Voice & Fax → A call comes in**, set:
  * **Webhook:** `https://<SERVER_HOST>/inbound`
  * **HTTP:** `POST`

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/inbound` | Twilio inbound call webhook |
| `POST` | `/make-call` | Start an outbound call `{"to": "+1..."}` |
| `POST` | `/call-status` | Twilio status callback |
| `WS`   | `/ws/stream` | Twilio Media Stream WebSocket |
| `GET`  | `/health` | Health + readiness check |

### Outbound call example

```bash
curl -X POST https://<SERVER_HOST>/make-call \
     -H "Content-Type: application/json" \
     -d '{"to": "+14155551234"}'
```

---

## Architecture notes

* **Silence detection** — 800 ms of sub-threshold RMS triggers a transcription
  request.  Tweak `SILENCE_RMS` / `SILENCE_FRAMES` in `websocket/call_handler.py`
  for your noise environment.
* **Per-call state** — each WebSocket connection gets its own `CallHandler`
  instance with an isolated audio buffer and conversation history.
* **Gemini context window** — up to the top-3 most relevant PDF chunks are
  prepended to every turn; increase `_TOP_K` in `services/gemini_rag.py` for
  more context.
* **Audio format** — ElevenLabs is asked for `ulaw_8000` (G.711 µ-law, 8 kHz)
  which Twilio consumes directly — no re-encoding needed.
* **Python version** — `audioop` (stdlib) is used for µ-law ↔ PCM conversion.
  On Python 3.13+ `audioop-lts` is installed automatically from `requirements.txt`.
