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

# ── Import FastAPI app with error diagnostics ──────────────────────
try:
    from main import app as fastapi_app
except ImportError as e:
    import traceback
    print(f"[Freebuff] CRITICAL: Failed to import FastAPI app: {e}")
    print(f"sys.path: {sys.path}")
    print(traceback.format_exc())
    # Serve a minimal fallback for diagnostics
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    fallback_app = FastAPI(title="Freebuff Voice (Import Error)")

    @fallback_app.route("/{path:path}", methods=["GET", "POST", "OPTIONS", "HEAD"])
    async def catch_all(path: str):
        return JSONResponse(
            status_code=500,
            content={
                "detail": f"Server import error: {str(e)}",
                "sys_path": sys.path,
            },
        )

    app = fallback_app
else:
    app = fastapi_app
