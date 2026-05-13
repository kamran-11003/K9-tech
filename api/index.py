"""
Vercel entry point — imports the FastAPI ASGI app from the project root.
Vercel calls `app` directly; uvicorn.run() in main.py is never reached.
"""
import sys
import os

# Make the project root importable (vercel runs from /api/)
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app  # noqa: F401  — Vercel picks up `app` automatically
