"""
Whisper Client
--------------
Sends PCM-16k WAV audio to the faster-whisper FastAPI server
running on Google Colab (exposed via ngrok) and returns the transcript.
"""
import logging

import httpx

logger = logging.getLogger(__name__)


class WhisperClient:
    def __init__(self, api_url: str) -> None:
        self.api_url = api_url.rstrip("/")

    async def transcribe(self, wav_bytes: bytes) -> str:
        """POST a WAV file to /transcribe and return the transcript string."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.api_url}/transcribe",
                files={"audio": ("audio.wav", wav_bytes, "audio/wav")},
            )
            resp.raise_for_status()
            return resp.json().get("text", "").strip()

    async def health_check(self) -> bool:
        """Return True if the Whisper API server is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.api_url}/")
                return resp.status_code == 200
        except Exception:
            return False
