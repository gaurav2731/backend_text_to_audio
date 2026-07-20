"""
Text-to-Voice Generator — Vercel Python Serverless Function
Routes all /api/* requests to the FastAPI backend app.

Vercel bundles the entire project into the serverless function, so
backend/main.py and backend/tts_engine.py are available via
sys.path manipulation.
"""
import sys
import os
import json
import traceback

# ── Path setup ────────────────────────────────────────────────────
# Ensure backend/ is on sys.path so "from main import app" works
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


# ── ASGI Error-Catching Wrapper ───────────────────────────────────
# This is the OUTERMOST wrapper — it catches ANY exception that
# escapes the FastAPI middleware/exception-handler chain and
# returns JSON. Without this, Vercel intercepts unhandled ASGI
# exceptions and returns its default HTML 500 page.
def wrap_app(inner_app):
    """Wrap an ASGI app so it ALWAYS returns JSON on error."""
    async def wrapped_app(scope, receive, send):
        # Only intercept HTTP requests
        if scope["type"] != "http":
            await inner_app(scope, receive, send)
            return

        try:
            await inner_app(scope, receive, send)
        except Exception as exc:
            tb = traceback.format_exc()
            print(f"[Freebuff][VercelWrapper] Unhandled error: {exc}\n{tb}")

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


# ── Import FastAPI app with error diagnostics ─────────────────────
try:
    from main import app as fastapi_app
except Exception as e:
    print(f"[Freebuff] CRITICAL: Failed to import FastAPI app: {e}")
    print(f"sys.path: {sys.path}")
    traceback.print_exc()

    # Fallback: try to serve a minimal FastAPI diagnostic app
    try:
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
        app = wrap_app(fallback_app)

    except Exception as inner_e:
        # Last resort — none of the frameworks are usable. Return a raw ASGI response.
        err_msg = f"Server import error: {str(e)}"
        fallback_detail = f"{err_msg} (fallback also failed: {inner_e})"
        print(f"[Freebuff] FATAL: {fallback_detail}")

        async def fallback_asgi(scope, receive, send):
            if scope["type"] != "http":
                return
            body = json.dumps({"detail": err_msg}).encode("utf-8")
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

        app = wrap_app(fallback_asgi)
else:
    # Wrap the FastAPI app so ALL errors return JSON at the ASGI level
    app = wrap_app(fastapi_app)
