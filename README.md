# 🎙️ Freebuff Voice — Text-to-Voice Generator

Convert text into natural, expressive human-like speech with emotion, voice style, and multilingual support.

## ✨ Features

- **🎭 Emotion-Aware Speech** — Neutral, Happy, Sad, Excited tones with pitch/speed/volume modulation
- **🗣️ Multiple Voice Styles** — Male/Female, Calm/Energetic combinations
- **🌐 16 Languages** — English, Hindi, Spanish, French, German, Japanese, Chinese, Korean, Portuguese, Russian, Arabic, Tamil, Telugu, Bengali, Gujarati, Marathi
- **🎨 Beautiful Web UI** — Glassmorphism design with real-time audio waveform visualization
- **⬇️ Download & Replay** — Play generated speech or download as MP3
- **⚡ Dual TTS Engines** — Microsoft Edge TTS (primary, SSML-based) with Google TTS fallback
- **🔌 REST API** — Easy integration with other applications

## 📋 Prerequisites

- Python 3.10+
- Internet connection (for TTS API calls)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd text-to-voice-generator
pip install -r backend/requirements.txt
```

### 2. Start the Backend Server

Run from the **project root** directory:

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 9000 --reload
```

If you run this command from inside the `backend` directory, Python may not find the top-level `backend` package. In that case either run the server from the project root (recommended), or run this instead from inside `backend`:

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 9000 --reload
```

The API will be available at `http://localhost:9000`

### 3. Open the Web UI

Simply open `frontend/index.html` in your browser.

> Alternatively, serve the frontend with any HTTP server:
> ```bash
> python -m http.server 3000 --directory frontend
> ```

## 🎯 Usage

### Web Interface

1. **Enter text** in the text area (up to 5000 characters)
2. **Select voice style** — Male/Female × Calm/Energetic
3. **Choose emotion** — Neutral, Happy, Sad, or Excited
4. **Pick language** from 16 supported options
5. Click **Generate Speech** (or press `Ctrl+Enter`)
6. Listen, replay, or download the audio

### REST API

```bash
# List supported languages
curl http://localhost:9000/languages

# List available voices
curl http://localhost:9000/voices

# List emotions
curl http://localhost:9000/emotions

# Generate speech
curl -X POST http://localhost:9000/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, welcome to Freebuff Voice!",
    "voice": "female_calm",
    "emotion": "happy",
    "language": "en"
  }'
```

**Response:**
```json
{
  "success": true,
  "filename": "speech_abc123.mp3",
  "url": "http://localhost:9000/audio/speech_abc123.mp3",
  "engine": "edge-tts",
  "characters": 42,
  "estimated_duration_sec": 4.2,
  "fallback": false,
  "emotion_applied": true
}
```

**Python Example:**
```python
import requests

response = requests.post("http://localhost:9000/synthesize", json={
    "text": "नमस्ते! आप कैसे हैं?",
    "voice": "female_calm",
    "emotion": "happy",
    "language": "hi"
})

data = response.json()
print(f"Audio URL: {data['url']}")
print(f"Engine: {data['engine']}")
```

## 🧠 Emotion Profiles

| Emotion   | Pitch  | Speed  | Volume | Edge TTS Style |
|-----------|--------|--------|--------|----------------|
| Neutral   | 0%     | 0%     | 0dB    | neutral        |
| Happy     | +10%   | +15%   | +3dB   | cheerful       |
| Sad       | -10%   | -15%   | -5dB   | sad            |
| Excited   | +15%   | +25%   | +5dB   | excited        |

## 🏗️ Project Structure

```
text-to-voice-generator/
├── backend/
│   ├── main.py            # FastAPI server & endpoints
│   ├── tts_engine.py      # TTS synthesis engine
│   └── requirements.txt   # Python dependencies
├── frontend/
│   ├── index.html          # Web UI
│   ├── styles.css          # Visual styling
│   └── app.js             # Frontend logic
├── audio_files/            # Generated audio (auto-created)
└── README.md
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Backend   | FastAPI (Python) |
| Primary TTS | Microsoft Edge TTS via `edge-tts` |
| Fallback TTS | Google TTS via `gTTS` |
| Audio Processing | `pydub` |
| Frontend  | Vanilla JS + HTML5 Audio |
| API       | REST (JSON) |

## 📝 Notes

- First-time TTS requests may be slightly slower as the engine initializes
- `edge-tts` requires internet access to Microsoft's TTS servers
- Audio files are stored locally in `audio_files/` and cleaned on server shutdown
- Use `Ctrl+Enter` as a keyboard shortcut in the web UI

## 📄 License

MIT — Free to use, modify, and distribute.
