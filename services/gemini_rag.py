"""
Gemini RAG Service
------------------
1. Loads every *.txt from DATA_DIR at startup.
2. Splits the content into overlapping text chunks.
3. Builds a TF-IDF index (local, no API calls) for retrieval.
4. At query time, finds the top-K most relevant chunks (cosine similarity)
   and passes them as context to gemini-1.5-flash.
"""
import logging
from pathlib import Path
from typing import Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import google.generativeai as genai

logger = logging.getLogger(__name__)

_CHUNK_SIZE = 1000       # characters per chunk
_CHUNK_OVERLAP = 150     # overlap to preserve context across chunk boundaries
_TOP_K = 3               # chunks to inject into each prompt
_CHAT_MODEL = "gemini-2.5-flash"


class GeminiRAG:
    def __init__(self, api_key: str, data_dir: str = "./data") -> None:
        genai.configure(api_key=api_key)
        self.chat_model = genai.GenerativeModel(_CHAT_MODEL)
        self.data_dir = Path(data_dir)
        self.chunks: list[dict] = []          # {"text", "source", "line"}
        self.embeddings: Optional[np.ndarray] = None
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._load_txt_files()

    # ------------------------------------------------------------------ #
    # TXT loading & TF-IDF index
    # ------------------------------------------------------------------ #

    def _load_txt_files(self) -> None:
        txt_files = sorted(self.data_dir.glob("*.txt"))
        if not txt_files:
            logger.warning("No .txt files found in %s — running without RAG context", self.data_dir)
            return

        logger.info("Loading %d .txt file(s) from %s …", len(txt_files), self.data_dir)
        for txt_path in txt_files:
            try:
                text = txt_path.read_text(encoding="utf-8", errors="replace")
                for chunk in self._split(text):
                    self.chunks.append({"text": chunk, "source": txt_path.name, "line": "-"})
                logger.info("  ✓ %s (%d chars)", txt_path.name, len(text))
            except Exception:
                logger.exception("Failed to load %s", txt_path.name)

        if not self.chunks:
            logger.warning("No text extracted from .txt files.")
            return

        logger.info("Building TF-IDF index for %d chunks …", len(self.chunks))
        self._vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=1,
            stop_words="english",
        )
        texts = [c["text"] for c in self.chunks]
        self.embeddings = self._vectorizer.fit_transform(texts)
        logger.info("TF-IDF index ready — vocab size: %d", len(self._vectorizer.vocabulary_))

    @staticmethod
    def _split(text: str) -> list[str]:
        """Split text into overlapping chunks."""
        chunks, start = [], 0
        while start < len(text):
            chunk = text[start : start + _CHUNK_SIZE].strip()
            if chunk:
                chunks.append(chunk)
            start += _CHUNK_SIZE - _CHUNK_OVERLAP
        return chunks

    # ------------------------------------------------------------------ #
    # Retrieval (TF-IDF cosine similarity — fully local, no API)
    # ------------------------------------------------------------------ #

    def _retrieve(self, query: str) -> str:
        """Return the top-K most relevant chunks as a formatted string."""
        if self.embeddings is None or self._vectorizer is None or not self.chunks:
            return ""
        q_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(q_vec, self.embeddings).flatten()
        top_idx = np.argsort(scores)[-_TOP_K:][::-1]
        parts = [
            f"[{self.chunks[i]['source']}]\n{self.chunks[i]['text']}"
            for i in top_idx
            if scores[i] > 0
        ]
        return "\n\n---\n\n".join(parts)

    # ------------------------------------------------------------------ #
    # Generation
    # ------------------------------------------------------------------ #

    async def generate_response(
        self,
        user_message: str,
        conversation_history: list[dict],
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate a concise voice-optimised reply using RAG context.

        Parameters
        ----------
        system_prompt : If provided, overrides the default assistant persona.
                        Knowledge-base context is still appended when relevant.
        """
        context = self._retrieve(user_message)

        if system_prompt:
            system_turn = system_prompt
            if context:
                system_turn += f"\n\n=== KNOWLEDGE BASE CONTEXT (use if relevant) ===\n{context}"
        else:
            system_turn = (
                "You are a helpful voice assistant. Respond concisely (1–3 sentences). "
                "Use natural, spoken language — no bullet points or markdown.\n\n"
            )
            if context:
                system_turn += f"Use the following knowledge-base context to answer:\n\n{context}"

        # Seed history with a system-like turn (Gemini has no system role)
        seeded_history = [
            {"role": "user", "parts": [system_turn]},
            {"role": "model", "parts": ["Understood. I'm ready to help."]},
        ] + conversation_history

        try:
            chat = self.chat_model.start_chat(history=seeded_history)
            resp = await chat.send_message_async(user_message)
            return resp.text.strip()
        except Exception:
            logger.exception("Gemini generation error")
            return "I'm sorry, I ran into an issue. Could you please repeat that?"
