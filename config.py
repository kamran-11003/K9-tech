from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Gemini (RAG + TTS) ───────────────────────────────────────────────
    GEMINI_API_KEY: str

    # ── Gemini TTS voice ────────────────────────────────────────────────
    # Options: Aoede, Charon, Fenrir, Kore, Puck, Orbit, Zephyr …
    GEMINI_TTS_VOICE: str = "Aoede"

    # ── Whisper API (Colab ngrok server) ────────────────────────────────
    WHISPER_API_URL: str = ""         # e.g. https://xxxx.ngrok-free.app

    # ── Server ──────────────────────────────────────────────────────────
    SERVER_PORT: int = 8000

    # ── Data paths ──────────────────────────────────────────────────────
    DATA_DIR: str = "./data"

    # ── MongoDB ─────────────────────────────────────────────────────────
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB:  str = "k9"

    # ── Production safety knobs ────────────────────────────────────────
    # Token required for /leads & /appointments listings (set in .env).
    # Empty string = endpoints stay open (dev mode only).
    ADMIN_TOKEN: str = ""

    # CORS origins (comma-separated). "*" allows any.
    CORS_ORIGINS: str = "*"

    # Rate-limiting (per client IP, sliding window — best-effort, in-memory)
    RATE_LIMIT_PER_MIN: int = 30      # /chat, /voice, /tts
    CONTACT_LIMIT_PER_HOUR: int = 5   # /contact, /appointments POST
    BOOKING_LIMIT_PER_DAY: int = 8    # /appointments POST per IP

    # Input size caps
    MAX_MESSAGE_CHARS:  int = 2000
    MAX_AUDIO_BYTES:    int = 10 * 1024 * 1024   # 10 MB
    MAX_HISTORY_TURNS:  int = 12                 # trim Aria session memory

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
