"""
Text-to-Voice Generator - FastAPI Server
Provides REST API for text-to-speech synthesis with emotion, voice, and language control.
Supports both local development (file-based) and Vercel (in-memory audio).
"""

import os
import sys
import base64
import traceback
from pathlib import Path
from contextlib import asynccontextmanager

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field
from typing import Optional

from tts_engine import (
    generate_speech,
    generate_speech_bytes,
    cleanup_old_files,
    SUPPORTED_LANGUAGES,
    VoiceStyle,
    Emotion,
    AUDIO_DIR,
    VOICE_METADATA,
)


# ─── Environment Detection ─────────────────────────────────────────

IS_VERCEL = os.environ.get("VERCEL", "0") == "1"


# ─── Request / Response Models ─────────────────────────────────────


class SynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Text to convert to speech")
    voice: VoiceStyle = Field(default=VoiceStyle.US_FEMALE_JENNY, description="Voice style")
    emotion: Emotion = Field(default=Emotion.NEUTRAL, description="Emotional tone")
    language: str = Field(default="en", description="Language code (e.g. en, hi)")


class SynthesizeResponse(BaseModel):
    success: bool
    audio_base64: Optional[str] = None
    filename: Optional[str] = None
    url: Optional[str] = None
    engine: Optional[str] = None
    error: Optional[str] = None
    characters: Optional[int] = None
    estimated_duration_sec: Optional[float] = None
    fallback: bool = False
    emotion_applied: bool = False


# ─── App Lifespan ──────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        AUDIO_DIR.mkdir(exist_ok=True)
    except OSError:
        pass
    yield
    # Shutdown
    if not IS_VERCEL:
        cleanup_old_files(max_age_minutes=10)


# ─── ASGI Middleware (catches ALL exceptions before Vercel's HTML 500) ──


class ErrorCatchMiddleware(BaseHTTPMiddleware):
    """
    Catches ANY exception raised during request processing and returns JSON.
    This is the LAST line of defense — placed before Vercel's default HTML 500.
    Without this, Vercel intercepts unhandled ASGI exceptions and returns HTML.
    """

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except HTTPException as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
            )
        except Exception as exc:
            tb = traceback.format_exc()
            print(f"[Freebuff][Middleware] Unhandled error: {exc}\n{tb}")
            return JSONResponse(
                status_code=500,
                content={"detail": f"Server error: {str(exc)}"},
            )


# ─── FastAPI App ───────────────────────────────────────────────────

app = FastAPI(
    title="Text-to-Voice Generator API",
    description="Convert text into natural human-like speech with emotion and voice control",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ADD the error-catching middleware LAST so it wraps everything
app.add_middleware(ErrorCatchMiddleware)


# ─── Global Exception Handler (FastAPI-level fallback) ────────────


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch ALL unhandled exceptions and return JSON instead of Vercel's HTML 500.
    Preserves HTTPException status codes and detail messages.
    This is the FastAPI-level handler; the middleware above is an ASGI-level safety net.
    """
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    error_detail = str(exc)
    tb = traceback.format_exc()
    print(f"[Freebuff][ExceptionHandler] Unhandled error: {error_detail}\n{tb}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Server error: {error_detail}"},
    )


# ─── Helpers ──────────────────────────────────────────────────────


def estimate_duration(text: str) -> float:
    """Rough estimate of speech duration in seconds (~150 words/min average)."""
    words = len(text.split())
    return round(max(words / 150 * 60, 1.0), 2)


def encode_audio_base64(audio_bytes: Optional[bytes]) -> Optional[str]:
    """Encode raw audio bytes to a base64 data URI for inline playback."""
    if not audio_bytes:
        return None
    return f"data:audio/mpeg;base64,{base64.b64encode(audio_bytes).decode('utf-8')}"


# ─── Root health-check (served both at /api and /) ─────────────────


@app.get("/api")
@app.get("/")
async def root():
    return {
        "service": "Text-to-Voice Generator",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "synthesize": "POST /api/synthesize",
            "languages": "GET /api/languages",
            "voices": "GET /api/voices",
            "emotions": "GET /api/emotions",
        },
    }


# ─── Languages ─────────────────────────────────────────────────────


@app.get("/api/languages")
async def get_languages():
    """Return list of supported languages."""
    return {
        "count": len(SUPPORTED_LANGUAGES),
        "languages": [
            {"code": code, "name": name}
            for code, name in SUPPORTED_LANGUAGES.items()
        ],
    }


# ─── Voices ────────────────────────────────────────────────────────


@app.get("/api/voices")
async def get_voices():
    """Return list of available voice styles with rich metadata."""
    voices = []
    for vs in VoiceStyle:
        meta = VOICE_METADATA.get(vs, {})
        voices.append({
            "id": vs.value,
            "name": meta.get("name", vs.value),
            "gender": meta.get("gender", "female"),
            "accent": meta.get("accent", "US"),
            "style": meta.get("style", ""),
            "emoji": meta.get("emoji", "🎙️"),
            "group": meta.get("group", "Other"),
        })
    return {
        "count": len(voices),
        "voices": voices,
    }


# ─── Emotions ──────────────────────────────────────────────────────


@app.get("/api/emotions")
async def get_emotions():
    """Return list of available emotions."""
    return {
        "count": len(Emotion),
        "emotions": [{"id": e.value, "label": e.value.title()} for e in Emotion],
    }


# ─── Synthesize ────────────────────────────────────────────────────


@app.post("/api/synthesize", response_model=SynthesizeResponse)
async def synthesize(request: SynthesizeRequest):
    """
    Convert text to speech with emotion, voice, and language control.
    On Vercel: returns audio as base64-encoded string (no file storage).
    Locally: also creates audio file and returns file URL.
    """
    # Validate language
    if request.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language: {request.language}. "
                   f"Supported: {', '.join(SUPPORTED_LANGUAGES.keys())}",
        )

    if IS_VERCEL:
        # ── Vercel mode: generate audio bytes in memory ──────────
        result = await generate_speech_bytes(
            text=request.text,
            voice=request.voice,
            emotion=request.emotion,
            language=request.language,
        )

        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Speech synthesis failed"),
            )

        audio_b64 = encode_audio_base64(result.get("audio_bytes"))

        return SynthesizeResponse(
            success=True,
            audio_base64=audio_b64,
            filename=result.get("filename"),
            engine=result["engine"],
            characters=len(request.text),
            estimated_duration_sec=estimate_duration(request.text),
            fallback=result.get("fallback", False),
            emotion_applied=result.get("emotion_applied", False),
        )

    else:
        # ── Local mode: generate and save to file ────────────────
        result = await generate_speech(
            text=request.text,
            voice=request.voice,
            emotion=request.emotion,
            language=request.language,
        )

        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Speech synthesis failed"),
            )

        base_url = os.environ.get("BASE_URL", "http://localhost:9000")

        # Also encode as base64 for frontend convenience
        audio_bytes = None
        filepath = result.get("filepath")
        if filepath:
            try:
                with open(filepath, "rb") as f:
                    audio_bytes = f.read()
            except Exception:
                pass

        audio_b64 = encode_audio_base64(audio_bytes)

        return SynthesizeResponse(
            success=True,
            audio_base64=audio_b64,
            filename=result["filename"],
            url=f"{base_url}/audio/{result['filename']}",
            engine=result["engine"],
            characters=len(request.text),
            estimated_duration_sec=estimate_duration(request.text),
            fallback=result.get("fallback", False),
            emotion_applied=result.get("emotion_applied", False),
        )


# ─── Serve audio files (local only — Vercel uses base64) ──────────


@app.get("/audio/{filename}")
async def get_audio(filename: str):
    """Serve generated audio files (local development only)."""
    filepath = AUDIO_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(
        path=str(filepath),
        media_type="audio/mpeg",
        filename=filename,
        headers={"Cache-Control": "public, max-age=3600"},
    )


# ─── Run ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    import socket

    def is_port_in_use(port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', port)) == 0

    port = int(os.environ.get("PORT", 9000))

    if is_port_in_use(port):
        print(f"[!] Port {port} is already in use. Trying port 9001.")
        port = 9001

    print(f"[*] Starting server on http://localhost:{port}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info",
    )
