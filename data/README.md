# Knowledge base

`knowledge_base.txt` is the source of truth for Aria's RAG retrieval.
It is loaded at startup, chunked, indexed with TF-IDF, and the top matches
are injected into the Gemini prompt at query time.

To update Aria's knowledge:
1. Edit `knowledge_base.txt`
2. Restart the server (`python main.py`)
