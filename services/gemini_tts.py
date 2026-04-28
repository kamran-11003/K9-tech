"""
Gemini TTS Service
------------------
Converts text to speech using Google Gemini's native TTS model
(gemini-2.5-flash-preview-tts) via the google-genai SDK.

Returns WAV bytes ready to be served directly as audio/wav.
"""
import io
import logging
import mimetypes
import struct

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# Voice options: Aoede, Charon, Fenrir, Kore, Puck, etc.
DEFAULT_VOICE = "Aoede"


def _convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    """Wrap raw PCM data in a WAV header if needed."""
    bits_per_sample, sample_rate = _parse_audio_mime(mime_type)
    num_channels = 1
    data_size = len(audio_data)
    block_align = num_channels * (bits_per_sample // 8)
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", chunk_size, b"WAVE",
        b"fmt ", 16, 1, num_channels,
        sample_rate, byte_rate, block_align, bits_per_sample,
        b"data", data_size,
    )
    return header + audio_data


def _parse_audio_mime(mime_type: str) -> tuple[int, int]:
    """Extract bits_per_sample and sample_rate from a MIME type string."""
    bits_per_sample = 16
    sample_rate = 24000
    for part in mime_type.split(";"):
        part = part.strip()
        if part.lower().startswith("rate="):
            try:
                sample_rate = int(part.split("=", 1)[1])
            except (ValueError, IndexError):
                pass
        elif part.startswith("audio/L"):
            try:
                bits_per_sample = int(part.split("L", 1)[1])
            except (ValueError, IndexError):
                pass
    return bits_per_sample, sample_rate


class GeminiTTS:
    def __init__(
        self,
        api_key: str,
        voice: str = DEFAULT_VOICE,
        model: str = "gemini-2.5-flash-preview-tts",
    ) -> None:
        self._client = genai.Client(api_key=api_key)
        self.voice = voice
        self.model = model

    def synthesize(self, text: str) -> bytes:
        """
        Convert *text* to speech and return WAV bytes.

        Uses the streaming generate_content API so audio arrives in chunks
        and is assembled into a single WAV file.
        """
        config = types.GenerateContentConfig(
            temperature=1,
            response_modalities=["audio"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=self.voice
                    )
                )
            ),
        )

        raw_chunks: list[bytes] = []
        detected_mime: str | None = None

        for chunk in self._client.models.generate_content_stream(
            model=self.model,
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=text)],
                )
            ],
            config=config,
        ):
            if not chunk.parts:
                continue
            part = chunk.parts[0]
            if part.inline_data and part.inline_data.data:
                raw_chunks.append(part.inline_data.data)
                if detected_mime is None:
                    detected_mime = part.inline_data.mime_type

        if not raw_chunks:
            logger.warning("GeminiTTS: no audio data returned")
            return b""

        raw = b"".join(raw_chunks)
        mime = detected_mime or "audio/L16;rate=24000"

        # If the model returns a proper WAV, pass it straight through;
        # otherwise wrap raw PCM in a WAV header.
        ext = mimetypes.guess_extension(mime)
        if ext == ".wav":
            return raw
        return _convert_to_wav(raw, mime)
