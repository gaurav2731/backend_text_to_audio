"""
Text-to-Voice Generator — Vercel Python Serverless Function
Routes all /api/* requests to the FastAPI backend app.

Vercel bundles the entire project into the serverless function, so
``backend/main.py`` and ``backend/tts_engine.py`` are available via
sys.path manipulation.
"""
import sys
import os

# ── Path setup ────────────────────────────────────────────────────
# Ensure backend/ is on sys.path so ``from main import app`` works
_api_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_api_dir)
_backend_path = os.path.join(_project_root, 'backend')

for p in [_backend_path, _project_root]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ── Vercel environment ────────────────────────────────────────────
os.environ.setdefault("VERCEL", "1")
os.environ.setdefault("AUDIO_DIR", "/tmp/audio_files")

# Ensure AUDIO_DIR exists (Vercel /tmp is ephemeral but writable)
os.makedirs("/tmp/audio_files", exist_ok=True)

# ── Import FastAPI app ────────────────────────────────────────────
from main import app as fastapi_app

# Vercel Python Runtime expects an ASGI-compatible ``app``
app = fastapi_app
