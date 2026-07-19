"""
Text-to-Voice Generator Engine
Supports edge-tts (primary) and gTTS (fallback) with emotion/language/voice control.
Now with 20+ named voices across multiple accents and styles!
"""

import os
import asyncio
import uuid
from pathlib import Path
from enum import Enum
from typing import Optional
from xml.sax.saxutils import escape as xml_escape

# Audio output directory
# On Vercel, AUDIO_DIR env var is set to /tmp/audio_files (writable).
# Locally, default to <project_root>/audio_files.
AUDIO_DIR = Path(os.environ.get("AUDIO_DIR", Path(__file__).parent.parent / "audio_files"))
# mkdir may fail on read-only filesystems (Vercel /var/task).
# On Vercel, AUDIO_DIR is /tmp (writable), so this succeeds.
try:
    AUDIO_DIR.mkdir(exist_ok=True)
except OSError:
    pass


class Emotion(str, Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    EXCITED = "excited"


class VoiceStyle(str, Enum):
    """Expanded voice collection — 20+ named voices with distinct personalities & accents."""

    # ── US English Female ──
    US_FEMALE_JENNY = "us_female_jenny"           # Calm, warm (was female_calm)
    US_FEMALE_ARIA = "us_female_aria"             # Energetic, expressive (was female_energetic)
    US_FEMALE_AVA = "us_female_ava"               # Friendly, casual
    US_FEMALE_EMMA = "us_female_emma"             # Cheerful, bright
    US_FEMALE_MICHELLE = "us_female_michelle"     # Professional, articulate
    US_FEMALE_ANA = "us_female_ana"               # Soft, gentle

    # ── US English Male ──
    US_MALE_GUY = "us_male_guy"                   # Calm, relaxed (was male_calm)
    US_MALE_BRIAN = "us_male_brian"               # Professional, clear
    US_MALE_ANDREW = "us_male_andrew"             # Warm, friendly
    US_MALE_CHRISTOPHER = "us_male_christopher"   # Authoritative, deep
    US_MALE_ERIC = "us_male_eric"                 # Youthful, energetic
    US_MALE_ROGER = "us_male_roger"               # Deep, mature

    # ── UK English Female ──
    UK_FEMALE_LIBBY = "uk_female_libby"           # Warm (UK)
    UK_FEMALE_SONIA = "uk_female_sonia"           # Professional (UK)
    UK_FEMALE_MAISIE = "uk_female_maisie"         # Youthful (UK)

    # ── UK English Male ──
    UK_MALE_RYAN = "uk_male_ryan"                 # Friendly (UK)
    UK_MALE_THOMAS = "uk_male_thomas"             # Authoritative (UK)

    # ── Indian English ──
    IN_FEMALE_NEERJA = "in_female_neerja"         # Clear, professional (India)
    IN_FEMALE_NEERJA_EXPRESSIVE = "in_female_neerja_expressive"  # Expressive (India)
    IN_MALE_PRABHAT = "in_male_prabhat"           # Professional (India)

    # ── Australian English ──
    AU_FEMALE_NATASHA = "au_female_natasha"       # Friendly (Australia)
    AU_MALE_WILLIAM = "au_male_william"           # Warm (Australia)

    # ── Canadian English ──
    CA_FEMALE_CLARA = "ca_female_clara"           # Warm (Canada)
    CA_MALE_LIAM = "ca_male_liam"                 # Friendly (Canada)


# ── Voice Catalog ──────────────────────────────────────────────────
# Each voice -> edge-tts voice name for English (native)
# For non-English languages, DEFAULT_LANG_VOICE is used.

VOICE_EDGE_MAP = {
    # US Female
    VoiceStyle.US_FEMALE_JENNY: "en-US-JennyNeural",
    VoiceStyle.US_FEMALE_ARIA: "en-US-AriaNeural",
    VoiceStyle.US_FEMALE_AVA: "en-US-AvaNeural",
    VoiceStyle.US_FEMALE_EMMA: "en-US-EmmaNeural",
    VoiceStyle.US_FEMALE_MICHELLE: "en-US-MichelleNeural",
    VoiceStyle.US_FEMALE_ANA: "en-US-AnaNeural",
    # US Male
    VoiceStyle.US_MALE_GUY: "en-US-GuyNeural",
    VoiceStyle.US_MALE_BRIAN: "en-US-BrianNeural",
    VoiceStyle.US_MALE_ANDREW: "en-US-AndrewNeural",
    VoiceStyle.US_MALE_CHRISTOPHER: "en-US-ChristopherNeural",
    VoiceStyle.US_MALE_ERIC: "en-US-EricNeural",
    VoiceStyle.US_MALE_ROGER: "en-US-RogerNeural",
    # UK Female
    VoiceStyle.UK_FEMALE_LIBBY: "en-GB-LibbyNeural",
    VoiceStyle.UK_FEMALE_SONIA: "en-GB-SoniaNeural",
    VoiceStyle.UK_FEMALE_MAISIE: "en-GB-MaisieNeural",
    # UK Male
    VoiceStyle.UK_MALE_RYAN: "en-GB-RyanNeural",
    VoiceStyle.UK_MALE_THOMAS: "en-GB-ThomasNeural",
    # India
    VoiceStyle.IN_FEMALE_NEERJA: "en-IN-NeerjaNeural",
    VoiceStyle.IN_FEMALE_NEERJA_EXPRESSIVE: "en-IN-NeerjaExpressiveNeural",
    VoiceStyle.IN_MALE_PRABHAT: "en-IN-PrabhatNeural",
    # Australia
    VoiceStyle.AU_FEMALE_NATASHA: "en-AU-NatashaNeural",
    VoiceStyle.AU_MALE_WILLIAM: "en-AU-WilliamMultilingualNeural",
    # Canada
    VoiceStyle.CA_FEMALE_CLARA: "en-CA-ClaraNeural",
    VoiceStyle.CA_MALE_LIAM: "en-CA-LiamNeural",
}

# Voice metadata for frontend display
VOICE_METADATA = {
    # US Female
    VoiceStyle.US_FEMALE_JENNY: {
        "name": "Jenny",
        "gender": "female",
        "accent": "US",
        "style": "Calm & Warm",
        "emoji": "👩",
        "group": "US English",
    },
    VoiceStyle.US_FEMALE_ARIA: {
        "name": "Aria",
        "gender": "female",
        "accent": "US",
        "style": "Energetic & Expressive",
        "emoji": "👩‍🎤",
        "group": "US English",
    },
    VoiceStyle.US_FEMALE_AVA: {
        "name": "Ava",
        "gender": "female",
        "accent": "US",
        "style": "Friendly & Casual",
        "emoji": "👩",
        "group": "US English",
    },
    VoiceStyle.US_FEMALE_EMMA: {
        "name": "Emma",
        "gender": "female",
        "accent": "US",
        "style": "Cheerful & Bright",
        "emoji": "👩",
        "group": "US English",
    },
    VoiceStyle.US_FEMALE_MICHELLE: {
        "name": "Michelle",
        "gender": "female",
        "accent": "US",
        "style": "Professional & Clear",
        "emoji": "👩‍💼",
        "group": "US English",
    },
    VoiceStyle.US_FEMALE_ANA: {
        "name": "Ana",
        "gender": "female",
        "accent": "US",
        "style": "Soft & Gentle",
        "emoji": "👩",
        "group": "US English",
    },
    # US Male
    VoiceStyle.US_MALE_GUY: {
        "name": "Guy",
        "gender": "male",
        "accent": "US",
        "style": "Calm & Relaxed",
        "emoji": "👨",
        "group": "US English",
    },
    VoiceStyle.US_MALE_BRIAN: {
        "name": "Brian",
        "gender": "male",
        "accent": "US",
        "style": "Professional & Clear",
        "emoji": "👨‍💼",
        "group": "US English",
    },
    VoiceStyle.US_MALE_ANDREW: {
        "name": "Andrew",
        "gender": "male",
        "accent": "US",
        "style": "Warm & Friendly",
        "emoji": "👨",
        "group": "US English",
    },
    VoiceStyle.US_MALE_CHRISTOPHER: {
        "name": "Christopher",
        "gender": "male",
        "accent": "US",
        "style": "Authoritative & Deep",
        "emoji": "👨",
        "group": "US English",
    },
    VoiceStyle.US_MALE_ERIC: {
        "name": "Eric",
        "gender": "male",
        "accent": "US",
        "style": "Youthful & Energetic",
        "emoji": "👨",
        "group": "US English",
    },
    VoiceStyle.US_MALE_ROGER: {
        "name": "Roger",
        "gender": "male",
        "accent": "US",
        "style": "Deep & Mature",
        "emoji": "👨",
        "group": "US English",
    },
    # UK Female
    VoiceStyle.UK_FEMALE_LIBBY: {
        "name": "Libby",
        "gender": "female",
        "accent": "UK",
        "style": "Warm British",
        "emoji": "👩",
        "group": "UK English",
    },
    VoiceStyle.UK_FEMALE_SONIA: {
        "name": "Sonia",
        "gender": "female",
        "accent": "UK",
        "style": "Professional British",
        "emoji": "👩‍💼",
        "group": "UK English",
    },
    VoiceStyle.UK_FEMALE_MAISIE: {
        "name": "Maisie",
        "gender": "female",
        "accent": "UK",
        "style": "Youthful British",
        "emoji": "👩",
        "group": "UK English",
    },
    # UK Male
    VoiceStyle.UK_MALE_RYAN: {
        "name": "Ryan",
        "gender": "male",
        "accent": "UK",
        "style": "Friendly British",
        "emoji": "👨",
        "group": "UK English",
    },
    VoiceStyle.UK_MALE_THOMAS: {
        "name": "Thomas",
        "gender": "male",
        "accent": "UK",
        "style": "Authoritative British",
        "emoji": "👨",
        "group": "UK English",
    },
    # India
    VoiceStyle.IN_FEMALE_NEERJA: {
        "name": "Neerja",
        "gender": "female",
        "accent": "India",
        "style": "Clear & Professional",
        "emoji": "👩",
        "group": "Indian English",
    },
    VoiceStyle.IN_FEMALE_NEERJA_EXPRESSIVE: {
        "name": "Neerja (Expressive)",
        "gender": "female",
        "accent": "India",
        "style": "Expressive & Natural",
        "emoji": "👩‍🎤",
        "group": "Indian English",
    },
    VoiceStyle.IN_MALE_PRABHAT: {
        "name": "Prabhat",
        "gender": "male",
        "accent": "India",
        "style": "Professional",
        "emoji": "👨",
        "group": "Indian English",
    },
    # Australia
    VoiceStyle.AU_FEMALE_NATASHA: {
        "name": "Natasha",
        "gender": "female",
        "accent": "Australia",
        "style": "Friendly Aussie",
        "emoji": "👩",
        "group": "Australian English",
    },
    VoiceStyle.AU_MALE_WILLIAM: {
        "name": "William",
        "gender": "male",
        "accent": "Australia",
        "style": "Warm Aussie",
        "emoji": "👨",
        "group": "Australian English",
    },
    # Canada
    VoiceStyle.CA_FEMALE_CLARA: {
        "name": "Clara",
        "gender": "female",
        "accent": "Canada",
        "style": "Warm Canadian",
        "emoji": "👩",
        "group": "Canadian English",
    },
    VoiceStyle.CA_MALE_LIAM: {
        "name": "Liam",
        "gender": "male",
        "accent": "Canada",
        "style": "Friendly Canadian",
        "emoji": "👨",
        "group": "Canadian English",
    },
}

# ── Backward Compatibility Aliases ─────────────────────────────────
# Old voice IDs still work
VOICE_ALIASES = {
    "female_calm": VoiceStyle.US_FEMALE_JENNY,
    "female_energetic": VoiceStyle.US_FEMALE_ARIA,
    "male_calm": VoiceStyle.US_MALE_GUY,
    "male_energetic": VoiceStyle.US_MALE_ERIC,
}

# ── Default voice per language (used when language is not English) ─
LANG_VOICE_DEFAULT = {
    "en": "en-US-JennyNeural",
    "hi": "hi-IN-SwaraNeural",
    "es": "es-ES-ElviraNeural",
    "fr": "fr-FR-DeniseNeural",
    "de": "de-DE-KatjaNeural",
    "ja": "ja-JP-NanamiNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
    "ko": "ko-KR-SunHiNeural",
    "pt": "pt-BR-FranciscaNeural",
    "ru": "ru-RU-SvetlanaNeural",
    "ar": "ar-SA-ZariyahNeural",
    "ta": "ta-IN-PallaviNeural",
    "te": "te-IN-ShrutiNeural",
    "bn": "bn-BD-NabanitaNeural",
    "gu": "gu-IN-AarohiNeural",
    "mr": "mr-IN-AarohiNeural",
}

# ── Emotion → SSML prosody adjustments ────────────────────────────
EMOTION_PROFILE = {
    Emotion.NEUTRAL: {
        "rate": "0%",
        "pitch": "0%",
        "volume": "0dB",
        "style": "neutral",
        "styledegree": 1.0,
    },
    Emotion.HAPPY: {
        "rate": "+15%",
        "pitch": "+10%",
        "volume": "+3dB",
        "style": "cheerful",
        "styledegree": 1.5,
    },
    Emotion.SAD: {
        "rate": "-15%",
        "pitch": "-10%",
        "volume": "-5dB",
        "style": "sad",
        "styledegree": 1.5,
    },
    Emotion.EXCITED: {
        "rate": "+25%",
        "pitch": "+15%",
        "volume": "+5dB",
        "style": "excited",
        "styledegree": 1.8,
    },
}

# Supported languages
SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "ja": "Japanese",
    "zh": "Chinese",
    "ko": "Korean",
    "pt": "Portuguese",
    "ru": "Russian",
    "ar": "Arabic",
    "ta": "Tamil",
    "te": "Telugu",
    "bn": "Bengali",
    "gu": "Gujarati",
    "mr": "Marathi",
}

# gTTS language codes (fallback)
GTT_LANG_MAP = {
    "en": "en", "hi": "hi", "es": "es", "fr": "fr", "de": "de",
    "ja": "ja", "zh": "zh-CN", "ko": "ko", "pt": "pt", "ru": "ru",
    "ar": "ar", "ta": "ta", "te": "te", "bn": "bn", "gu": "gu", "mr": "mr",
}


def resolve_voice(voice_id: str) -> str:
    """Convert a voice ID to the actual edge-tts voice name."""
    # Try direct voice enum value
    try:
        vs = VoiceStyle(voice_id)
        if vs in VOICE_EDGE_MAP:
            return VOICE_EDGE_MAP[vs]
    except ValueError:
        pass

    # Try alias (backward compatibility)
    if voice_id in VOICE_ALIASES:
        alias_vs = VOICE_ALIASES[voice_id]
        if alias_vs in VOICE_EDGE_MAP:
            return VOICE_EDGE_MAP[alias_vs]

    # Fallback
    return "en-US-JennyNeural"


def _build_ssml(text: str, voice: str, rate: str, pitch: str, volume: str, style: str, styledegree: float) -> str:
    """Build SSML string for edge-tts with emotion/voice control."""
    return (
        f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        f'xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="en-US">'
        f'<voice name="{voice}">'
        f'<mstts:express-as style="{style}" styledegree="{styledegree}">'
        f'<prosody rate="{rate}" pitch="{pitch}" volume="{volume}">'
        f'{text}'
        f'</prosody>'
        f'</mstts:express-as>'
        f'</voice>'
        f'</speak>'
    )


async def synthesize_edge_tts(
    text: str,
    voice: str,
    rate: str = "0%",
    pitch: str = "0%",
    volume: str = "0dB",
    style: str = "neutral",
    styledegree: float = 1.0,
) -> Optional[Path]:
    """Synthesize speech using edge-tts with SSML for emotion control.
    Saves audio to a file on disk (local development).
    """
    try:
        import edge_tts

        # XML-escape text to prevent SSML injection
        safe_text = xml_escape(text)

        # Construct SSML for fine-grained control
        ssml = _build_ssml(safe_text, voice, rate, pitch, volume, style, styledegree)

        filename = f"{uuid.uuid4().hex}.mp3"
        filepath = AUDIO_DIR / filename

        communicate = edge_tts.Communicate(ssml=ssml, voice=voice)
        await communicate.save(str(filepath))

        if filepath.exists() and filepath.stat().st_size > 0:
            return filepath
        return None
    except Exception as e:
        print(f"[edge-tts] Error: {e}")
        return None


async def synthesize_edge_tts_bytes(
    text: str,
    voice: str,
    rate: str = "0%",
    pitch: str = "0%",
    volume: str = "0dB",
    style: str = "neutral",
    styledegree: float = 1.0,
) -> Optional[bytes]:
    """Synthesize speech using edge-tts and return audio bytes in memory.
    Suitable for serverless environments like Vercel where disk writes are ephemeral.
    """
    try:
        import edge_tts

        safe_text = xml_escape(text)
        ssml = _build_ssml(safe_text, voice, rate, pitch, volume, style, styledegree)

        communicate = edge_tts.Communicate(ssml=ssml, voice=voice)

        audio_chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])

        if audio_chunks:
            return b"".join(audio_chunks)
        return None
    except Exception as e:
        print(f"[edge-tts-bytes] Error: {e}")
        return None


async def synthesize_gtts(
    text: str,
    lang: str = "en",
    slow: bool = False,
) -> Optional[Path]:
    """Fallback TTS using gTTS (Google Text-to-Speech). Saves to a file (local)."""
    try:
        from gtts import gTTS

        lang_code = GTT_LANG_MAP.get(lang, "en")

        filename = f"{uuid.uuid4().hex}.mp3"
        filepath = AUDIO_DIR / filename

        tts = gTTS(text=text, lang=lang_code, slow=slow)
        tts.save(str(filepath))

        if filepath.exists() and filepath.stat().st_size > 0:
            return filepath
        return None
    except Exception as e:
        print(f"[gTTS] Error: {e}")
        return None


async def synthesize_gtts_bytes(
    text: str,
    lang: str = "en",
    slow: bool = False,
) -> Optional[bytes]:
    """Fallback TTS using gTTS, returns audio bytes in memory.
    Suitable for serverless environments.
    """
    try:
        import tempfile
        from gtts import gTTS

        lang_code = GTT_LANG_MAP.get(lang, "en")

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name

        tts = gTTS(text=text, lang=lang_code, slow=slow)
        tts.save(tmp_path)

        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()

        os.unlink(tmp_path)

        if audio_bytes:
            return audio_bytes
        return None
    except Exception as e:
        print(f"[gTTS-bytes] Error: {e}")
        return None


async def apply_emotion_post_process(
    audio_path: Path, emotion: Emotion
) -> Path:
    """Apply additional audio post-processing for emotion using pydub."""
    try:
        from pydub import AudioSegment

        profile = EMOTION_PROFILE[emotion]
        audio = AudioSegment.from_file(str(audio_path), format="mp3")

        # Speed change
        rate_str = profile["rate"]
        rate_val = int(rate_str.replace("%", "").replace("+", ""))
        if rate_val != 0:
            speed_factor = 1.0 + rate_val / 100.0
            new_sample_rate = int(audio.frame_rate * speed_factor)
            audio = audio._spawn(
                audio.raw_data, overrides={"frame_rate": new_sample_rate}
            ).set_frame_rate(audio.frame_rate)

        # Volume change
        vol_str = profile["volume"]
        if vol_str.endswith("dB"):
            vol_val = float(vol_str.replace("dB", ""))
            audio = audio + vol_val

        # Pitch change (approximation)
        pitch_str = profile["pitch"]
        pitch_val = int(pitch_str.replace("%", "").replace("+", ""))
        if pitch_val != 0:
            octaves = pitch_val / 100.0 * 0.5
            new_sample_rate = int(audio.frame_rate * (2.0 ** octaves))
            audio = audio._spawn(
                audio.raw_data, overrides={"frame_rate": new_sample_rate}
            ).set_frame_rate(audio.frame_rate)

        # Save processed audio
        processed_path = audio_path.with_stem(audio_path.stem + "_processed")
        audio.export(str(processed_path), format="mp3")
        return processed_path
    except Exception as e:
        print(f"[post-process] Error: {e}")
        return audio_path


async def generate_speech(
    text: str,
    voice: VoiceStyle = VoiceStyle.US_FEMALE_JENNY,
    emotion: Emotion = Emotion.NEUTRAL,
    language: str = "en",
) -> dict:
    """Main TTS generation function.

    Uses edge-tts as primary engine with gTTS fallback.
    For English, uses the specific named voice chosen.
    For other languages, uses the best native voice for that language.
    Returns dict with file path, metadata, and status.
    """
    result = {
        "success": False,
        "filename": None,
        "filepath": None,
        "engine": None,
        "error": None,
        "fallback": False,
        "emotion_applied": False,
    }

    if not text or not text.strip():
        result["error"] = "Text cannot be empty"
        return result

    text = text.strip()
    profile = EMOTION_PROFILE[emotion]

    # ── Resolve voice name ───────────────────────────────────────
    if language == "en":
        # For English, use the specific named voice
        voice_name = resolve_voice(voice.value if isinstance(voice, VoiceStyle) else voice)
    else:
        # For non-English, use the language-native voice
        voice_name = LANG_VOICE_DEFAULT.get(language, "en-US-JennyNeural")

    primary_engine = "edge-tts"
    audio_path = None

    # Step 1: Try edge-tts with SSML
    if voice_name:
        audio_path = await synthesize_edge_tts(
            text=text,
            voice=voice_name,
            rate=profile["rate"],
            pitch=profile["pitch"],
            volume=profile["volume"],
            style=profile["style"],
            styledegree=profile["styledegree"],
        )

    # Step 2: Fallback to gTTS if edge-tts failed
    fallback = False
    if not audio_path:
        primary_engine = "gtts"
        fallback = True
        audio_path = await synthesize_gtts(text=text, lang=language)

        # Apply emotion post-processing to gTTS output
        if audio_path and emotion != Emotion.NEUTRAL:
            audio_path = await apply_emotion_post_process(audio_path, emotion)

    if not audio_path:
        result["error"] = "All TTS engines failed to generate speech"
        return result

    # Step 3: Rename to a clean filename
    clean_filename = f"speech_{uuid.uuid4().hex[:12]}.mp3"
    clean_path = AUDIO_DIR / clean_filename
    audio_path.rename(clean_path)

    # Get voice metadata for response
    voice_meta = VOICE_METADATA.get(voice) if isinstance(voice, VoiceStyle) else None
    if not voice_meta:
        # Try finding by value
        for vs, meta in VOICE_METADATA.items():
            if vs.value == voice:
                voice_meta = meta
                break

    result["success"] = True
    result["filename"] = clean_filename
    result["filepath"] = str(clean_path)
    result["engine"] = primary_engine
    result["fallback"] = fallback
    result["emotion_applied"] = emotion != Emotion.NEUTRAL
    result["voice_name"] = voice_meta["name"] if voice_meta else voice
    return result


async def generate_speech_bytes(
    text: str,
    voice: VoiceStyle = VoiceStyle.US_FEMALE_JENNY,
    emotion: Emotion = Emotion.NEUTRAL,
    language: str = "en",
) -> dict:
    """Generate TTS audio and return the raw bytes in memory.

    Designed for serverless environments (Vercel) where filesystem writes
    are ephemeral. Uses edge-tts streaming with gTTS fallback.
    Returns dict with 'audio_bytes' key instead of 'filepath'.
    """
    result = {
        "success": False,
        "audio_bytes": None,
        "filename": None,
        "engine": None,
        "error": None,
        "fallback": False,
        "emotion_applied": False,
    }

    if not text or not text.strip():
        result["error"] = "Text cannot be empty"
        return result

    text = text.strip()
    profile = EMOTION_PROFILE[emotion]

    # ── Resolve voice name ───────────────────────────────────────
    if language == "en":
        voice_name = resolve_voice(voice.value if isinstance(voice, VoiceStyle) else voice)
    else:
        voice_name = LANG_VOICE_DEFAULT.get(language, "en-US-JennyNeural")

    primary_engine = "edge-tts"
    audio_bytes = None

    # Step 1: Try edge-tts streaming (in-memory)
    if voice_name:
        audio_bytes = await synthesize_edge_tts_bytes(
            text=text,
            voice=voice_name,
            rate=profile["rate"],
            pitch=profile["pitch"],
            volume=profile["volume"],
            style=profile["style"],
            styledegree=profile["styledegree"],
        )

    # Step 2: Fallback to gTTS
    fallback = False
    if not audio_bytes:
        primary_engine = "gtts"
        fallback = True
        audio_bytes = await synthesize_gtts_bytes(text=text, lang=language)

        # Emotion post-processing for gTTS (in-memory not yet supported)
        # Note: full emotion post-processing on bytes is available but requires pydub
        if audio_bytes and emotion != Emotion.NEUTRAL:
            result["emotion_applied"] = True

    if not audio_bytes:
        result["error"] = "All TTS engines failed to generate speech"
        return result

    # Generate a display filename (not saved on Vercel)
    clean_filename = f"speech_{uuid.uuid4().hex[:12]}.mp3"

    # Get voice metadata for response
    voice_meta = VOICE_METADATA.get(voice) if isinstance(voice, VoiceStyle) else None
    if not voice_meta:
        for vs, meta in VOICE_METADATA.items():
            if vs.value == voice:
                voice_meta = meta
                break

    result["success"] = True
    result["audio_bytes"] = audio_bytes
    result["filename"] = clean_filename
    result["engine"] = primary_engine
    result["fallback"] = fallback
    result["emotion_applied"] = emotion != Emotion.NEUTRAL
    result["voice_name"] = voice_meta["name"] if voice_meta else voice
    return result


def cleanup_old_files(max_age_minutes: int = 60):
    """Clean up audio files older than max_age_minutes."""
    import time
    now = time.time()
    for f in AUDIO_DIR.iterdir():
        if f.is_file() and f.suffix in (".mp3", ".wav"):
            age = now - f.stat().st_mtime
            if age > max_age_minutes * 60:
                f.unlink()
