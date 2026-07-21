"""
Text-to-Voice Generator — Vercel Python Serverless Function
Routes all /api/* requests to the FastAPI backend app.
"""
import sys
import os
import json
import traceback

# ── Path setup ────────────────────────────────────────────────────
# api/index.py lives in <project_root>/api/
# main.py and tts_engine.py live in <project_root>/backend/
_api_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_api_dir)
_backend_dir = os.path.join(_project_root, "backend")

for p in [_backend_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ── Vercel environment ────────────────────────────────────────────
os.environ.setdefault("VERCEL", "1")
os.environ.setdefault("AUDIO_DIR", "/tmp/audio_files")
os.makedirs("/tmp/audio_files", exist_ok=True)


# ── ASGI Error-Catching Wrapper ───────────────────────────────────
# Wraps the app so that ANY unhandled exception returns JSON instead
# of Vercel's default HTML 500 page. This is the OUTERMOST defense
# layer (ASGI-level).


def wrap_app(inner_app):
    """Wrap an ASGI app so it ALWAYS returns JSON on error."""
    async def wrapped_app(scope, receive, send):
        if scope["type"] != "http":
            await inner_app(scope, receive, send)
            return

        try:
            await inner_app(scope, receive, send)
        except Exception as exc:
            tb = traceback.format_exc()
            print(f"[VercelWrapper] Unhandled ASGI error: {exc}\n{tb}")

            body = json.dumps({
                "detail": f"Server error: {str(exc)}"
            }).encode("utf-8")

            await send({
                "type": "http.response.start",
                "status": 500,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                    (b"access-control-allow-origin", b"*"),
                ],
            })
            await send({"type": "http.response.body", "body": body})

    return wrapped_app


# ── Import FastAPI app (with error diagnostics) ────────────────────
# IMPORTANT: Vercel does STATIC analysis on this file to find the
# top-level 'app' variable. The assignment MUST be at module scope,
# NOT inside a try/except block, otherwise the build fails with:
#   "Could not find a top-level 'app' in api/index.py"
#
# Strategy: declare app = None at top level first, then set it.

app = None  # <-- Signals to Vercel's analyzer: "app exists here"


def _build_app():
    """Import and wrap the FastAPI app; return a fallback on error."""
    try:
        from main import app as fastapi_app
        return wrap_app(fastapi_app)
    except Exception as e:
        print(f"[Vercel] CRITICAL: Failed to import FastAPI app: {e}")
        print(f"sys.path: {sys.path}")
        traceback.print_exc()

        detail = f"Server import error: {str(e)}"

        async def fallback_app(scope, receive, send):
            if scope["type"] != "http":
                return
            body = json.dumps({"detail": detail}).encode("utf-8")
            await send({
                "type": "http.response.start",
                "status": 500,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                    (b"access-control-allow-origin", b"*"),
                ],
            })
            await send({"type": "http.response.body", "body": body})

        return wrap_app(fallback_app)


# Top-level assignment — Vercel's static analyzer sees this.
app = _build_app()
