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
    LEADS_CSV_PATH: str = "./data/leads.csv"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
