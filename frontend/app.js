/* ═══════════════════════════════════════════════════════════════════
   Freebuff Voice — Text‑to‑Voice Generator
   Frontend App: TTS API integration, audio player, waveform viz
   ═══════════════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  // ─── Config ─────────────────────────────────────────────────────
  // In production (Vercel), API lives at the same origin under /api/*.
  // Locally, point this to your FastAPI server, e.g. 'http://localhost:9000'.
  const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:9000/api'
    : '/api';

  // ─── DOM References ─────────────────────────────────────────────
  const textInput        = document.getElementById('textInput');
  const charCount        = document.getElementById('charCount');
  const clearBtn         = document.getElementById('clearBtn');
  const generateBtn      = document.getElementById('generateBtn');
  const generateText     = document.getElementById('generateText');
  const loadingSpinner   = document.getElementById('loadingSpinner');
  const resultSection    = document.getElementById('resultSection');
  const audioPlayer      = document.getElementById('audioPlayer');
  const playBtn          = document.getElementById('playBtn');
  const playIcon         = document.getElementById('playIcon');
  const seekBar          = document.getElementById('seekBar');
  const timeCurrent      = document.getElementById('timeCurrent');
  const timeTotal        = document.getElementById('timeTotal');
  const engineBadge      = document.getElementById('engineBadge');
  const durationBadge    = document.getElementById('durationBadge');
  const downloadBtn      = document.getElementById('downloadBtn');
  const downloadFormat    = document.getElementById('downloadFormat');
  const filenameInput     = document.getElementById('filenameInput');
  const waveformCanvas   = document.getElementById('waveformCanvas');
  const toastContainer   = document.getElementById('toastContainer');

  // Voice system
  const voiceAccentTabs  = document.querySelectorAll('#voiceAccentTabs .accent-tab');
  const voiceCardsContainer = document.getElementById('voiceCardsContainer');
  const emotionButtons   = document.querySelectorAll('#emotionButtons .ctrl-btn');
  const languageSelect   = document.getElementById('languageSelect');

  // History & i18n
  const historySection   = document.getElementById('historySection');
  const historyList      = document.getElementById('historyList');
  const historyEmpty     = document.getElementById('historyEmpty');
  const historyCount     = document.getElementById('historyCount');
  const historyClearBtn  = document.getElementById('historyClearBtn');
  const historyAutoSave  = document.getElementById('historyAutoSave');
  const langToggle       = document.getElementById('langToggle');

  // ─── State ──────────────────────────────────────────────────────
  let currentAudioUrl    = null;
  let currentFilename    = null;
  let currentText        = '';
  let currentVoice       = 'us_female_jenny';
  let currentEmotion     = 'neutral';
  let currentLanguage    = 'en';
  let isPlaying          = false;
  let audioContext       = null;
  let analyser           = null;
  let source             = null;
  let rafId              = null;
  let waveformData       = new Uint8Array(128).fill(128);
  let currentLang        = localStorage.getItem('fbv-lang') || 'en';
  const HISTORY_KEY      = 'fbv-history';
  const MAX_HISTORY      = 20;

  // ─── Character Counter ──────────────────────────────────────────
  textInput.addEventListener('input', () => {
    const len = textInput.value.length;
    charCount.textContent = `${len} / 5000`;
  });

  clearBtn.addEventListener('click', () => {
    textInput.value = '';
    textInput.dispatchEvent(new Event('input'));
    textInput.focus();
  });

  // ─── Tab-style Button Groups ────────────────────────────────────
  function setupButtonGroup(buttons) {
    buttons.forEach(btn => {
      btn.addEventListener('click', () => {
        buttons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      });
    });
  }

  setupButtonGroup(emotionButtons);

  // ─── Voice System (Cards + Accent Tabs) ─────────────────────────
  // Complete voice catalog matching the backend.
  // nameKey / styleKey reference translation keys in TRANSLATIONS.
  const VOICE_CATALOG = [
    // US Female
    { id: 'us_female_jenny', nameKey: 'v_jenny', styleKey: 's_calm_warm', emoji: '👩', group: 'US English', gender: 'female' },
    { id: 'us_female_aria', nameKey: 'v_aria', styleKey: 's_energetic', emoji: '👩‍🎤', group: 'US English', gender: 'female' },
    { id: 'us_female_ava', nameKey: 'v_ava', styleKey: 's_friendly', emoji: '👩', group: 'US English', gender: 'female' },
    { id: 'us_female_emma', nameKey: 'v_emma', styleKey: 's_cheerful', emoji: '👩', group: 'US English', gender: 'female' },
    { id: 'us_female_michelle', nameKey: 'v_michelle', styleKey: 's_professional', emoji: '👩‍💼', group: 'US English', gender: 'female' },
    { id: 'us_female_ana', nameKey: 'v_ana', styleKey: 's_gentle', emoji: '👩', group: 'US English', gender: 'female' },
    // US Male
    { id: 'us_male_guy', nameKey: 'v_guy', styleKey: 's_calm_relaxed', emoji: '👨', group: 'US English', gender: 'male' },
    { id: 'us_male_brian', nameKey: 'v_brian', styleKey: 's_professional', emoji: '👨‍💼', group: 'US English', gender: 'male' },
    { id: 'us_male_andrew', nameKey: 'v_andrew', styleKey: 's_warm', emoji: '👨', group: 'US English', gender: 'male' },
    { id: 'us_male_christopher', nameKey: 'v_christopher', styleKey: 's_authoritative', emoji: '👨', group: 'US English', gender: 'male' },
    { id: 'us_male_eric', nameKey: 'v_eric', styleKey: 's_energetic', emoji: '👨', group: 'US English', gender: 'male' },
    { id: 'us_male_roger', nameKey: 'v_roger', styleKey: 's_deep_mature', emoji: '👨', group: 'US English', gender: 'male' },
    // UK Female
    { id: 'uk_female_libby', nameKey: 'v_libby', styleKey: 's_warm_british', emoji: '👩', group: 'UK English', gender: 'female' },
    { id: 'uk_female_sonia', nameKey: 'v_sonia', styleKey: 's_professional_uk', emoji: '👩‍💼', group: 'UK English', gender: 'female' },
    { id: 'uk_female_maisie', nameKey: 'v_maisie', styleKey: 's_youthful_uk', emoji: '👩', group: 'UK English', gender: 'female' },
    // UK Male
    { id: 'uk_male_ryan', nameKey: 'v_ryan', styleKey: 's_friendly_uk', emoji: '👨', group: 'UK English', gender: 'male' },
    { id: 'uk_male_thomas', nameKey: 'v_thomas', styleKey: 's_authoritative_uk', emoji: '👨', group: 'UK English', gender: 'male' },
    // India
    { id: 'in_female_neerja', nameKey: 'v_neerja', styleKey: 's_clear_professional', emoji: '👩', group: 'Indian English', gender: 'female' },
    { id: 'in_female_neerja_expressive', nameKey: 'v_neerja_exp', styleKey: 's_expressive', emoji: '👩‍🎤', group: 'Indian English', gender: 'female' },
    { id: 'in_male_prabhat', nameKey: 'v_prabhat', styleKey: 's_professional', emoji: '👨', group: 'Indian English', gender: 'male' },
    // Australia
    { id: 'au_female_natasha', nameKey: 'v_natasha', styleKey: 's_friendly_aussie', emoji: '👩', group: 'Australian English', gender: 'female' },
    { id: 'au_male_william', nameKey: 'v_william', styleKey: 's_warm_aussie', emoji: '👨', group: 'Australian English', gender: 'male' },
    // Canada
    { id: 'ca_female_clara', nameKey: 'v_clara', styleKey: 's_warm_canadian', emoji: '👩', group: 'Canadian English', gender: 'female' },
    { id: 'ca_male_liam', nameKey: 'v_liam', styleKey: 's_friendly_canadian', emoji: '👨', group: 'Canadian English', gender: 'male' },
  ];

  // Backward compatibility: old voice IDs → new voice IDs
  const VOICE_ALIASES_FRONTEND = {
    'female_calm': 'us_female_jenny',
    'female_energetic': 'us_female_aria',
    'male_calm': 'us_male_guy',
    'male_energetic': 'us_male_eric',
  };

  let currentVoiceGroup = 'US English';
  let currentVoiceId = 'us_female_jenny';

  // ─── Translation helper ────────────────────────────────────────
  function tr(key) {
    const langObj = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
    return langObj[key] !== undefined ? langObj[key] : (TRANSLATIONS.en[key] || key);
  }

  function renderVoiceCards(group) {
    const voices = VOICE_CATALOG.filter(v => v.group === group);
    voiceCardsContainer.innerHTML = voices.map(v => `
      <button class="voice-card ${v.id === currentVoiceId ? 'active' : ''}" data-voice-id="${v.id}">
        <span class="voice-card-emoji">${v.emoji}</span>
        <span class="voice-card-name">${tr(v.nameKey)}</span>
        <span class="voice-card-style">${tr(v.styleKey)}</span>
      </button>
    `).join('');

    voiceCardsContainer.querySelectorAll('.voice-card').forEach(card => {
      card.addEventListener('click', () => {
        voiceCardsContainer.querySelectorAll('.voice-card').forEach(c => c.classList.remove('active'));
        card.classList.add('active');
        currentVoiceId = card.dataset.voiceId;
        try { localStorage.setItem('fbv-voice', currentVoiceId); } catch(e) {}
      });
    });
  }

  function updateAccentTabLabels() {
    const tabMap = {
      'US English': 'tab_us',
      'UK English': 'tab_uk',
      'Indian English': 'tab_india',
      'Australian English': 'tab_au',
      'Canadian English': 'tab_ca',
    };
    voiceAccentTabs.forEach(tab => {
      const key = tabMap[tab.dataset.group];
      if (key) {
        const flag = tab.dataset.flag || '';
        tab.textContent = flag ? `${flag} ${tr(key)}` : tr(key);
      }
    });
  }

  // Accent tabs
  voiceAccentTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      voiceAccentTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      currentVoiceGroup = tab.dataset.group;
      renderVoiceCards(currentVoiceGroup);
    });
  });

  // Load saved voice from localStorage
  try {
    const savedVoice = localStorage.getItem('fbv-voice');
    if (savedVoice) {
      const found = VOICE_CATALOG.find(v => v.id === savedVoice);
      if (found) {
        currentVoiceId = savedVoice;
        currentVoiceGroup = found.group;
        voiceAccentTabs.forEach(t => {
          t.classList.toggle('active', t.dataset.group === found.group);
        });
      }
    }
  } catch(e) {}

  // ─── Toast Notifications ────────────────────────────────────────
  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 0.3s';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  // ─── Audio Waveform ─────────────────────────────────────────────
  function initAudioContext() {
    if (!audioContext) {
      audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioContext.state === 'suspended') {
      audioContext.resume();
    }
  }

  function setupAnalyser() {
    if (!audioContext || !audioPlayer) return;
    try {
      if (source) { source.disconnect(); }
      source = audioContext.createMediaElementSource(audioPlayer);
      analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyser.connect(audioContext.destination);
    } catch (e) {
      console.debug('Waveform: source already connected');
    }
  }

  function drawWaveform() {
    if (!analyser || !waveformCanvas) return;
    const ctx = waveformCanvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const rect = waveformCanvas.getBoundingClientRect();
    waveformCanvas.width = rect.width * dpr;
    waveformCanvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const width = rect.width;
    const height = rect.height;

    function render() {
      if (!analyser) return;
      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      analyser.getByteTimeDomainData(dataArray);

      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = 'rgba(0,0,0,0.3)';
      ctx.fillRect(0, 0, width, height);

      ctx.lineWidth = 2;
      ctx.strokeStyle = '#8b5cf6';
      ctx.shadowColor = 'rgba(139, 92, 246, 0.5)';
      ctx.shadowBlur = 8;
      ctx.beginPath();
      const sliceWidth = width / bufferLength;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0;
        const y = (v * height) / 2;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
        x += sliceWidth;
      }
      ctx.lineTo(width, height / 2);
      ctx.stroke();

      ctx.shadowBlur = 0;
      ctx.strokeStyle = 'rgba(139, 92, 246, 0.2)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      x = 0;
      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0;
        const y = (v * height) / 2;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
        x += sliceWidth;
      }
      ctx.lineTo(width, height / 2);
      ctx.stroke();

      if (isPlaying) rafId = requestAnimationFrame(render);
    }
    render();
  }

  function stopWaveform() {
    if (rafId) { cancelAnimationFrame(rafId); rafId = null; }
    if (waveformCanvas) {
      const ctx = waveformCanvas.getContext('2d');
      const rect = waveformCanvas.getBoundingClientRect();
      ctx.clearRect(0, 0, rect.width, rect.height);
      ctx.fillStyle = 'rgba(0,0,0,0.3)';
      ctx.fillRect(0, 0, rect.width, rect.height);
      ctx.strokeStyle = 'rgba(139, 92, 246, 0.4)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, rect.height / 2);
      ctx.lineTo(rect.width, rect.height / 2);
      ctx.stroke();
    }
  }

  // ─── Audio Player Controls ──────────────────────────────────────
  function formatTime(seconds) {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  }

  async function downloadAudio(url) {
    if (!url) {
      showToast('No audio to download. Generate speech first.', 'error');
      return;
    }

    const format = downloadFormat.value;
    const userFilename = filenameInput.value.trim() || 'freebuff-speech';
    const ext = format === 'wav' ? '.wav' : '.mp3';
    const fullFilename = `${userFilename}${ext}`;

    downloadBtn.classList.add('downloading');
    downloadBtn.disabled = true;
    downloadBtn.innerHTML = `<div class="download-spinner"></div>`;

    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch audio');
      const blob = await response.blob();

      let finalBlob = blob;
      let finalExt = ext;
      if (format === 'wav') {
        try { finalBlob = await convertToWav(blob); }
        catch (convErr) { console.warn('WAV conversion failed, falling back to MP3', convErr); finalExt = '.mp3'; }
      }

      const finalFilename = `${userFilename}${finalExt}`;
      const blobUrl = URL.createObjectURL(finalBlob);
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = finalFilename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(() => URL.revokeObjectURL(blobUrl), 5000);

      const sizeKB = Math.round(finalBlob.size / 1024);
      showToast(`Downloaded: ${finalFilename} (${sizeKB} KB)`, 'success');
    } catch (err) {
      console.error('Download error:', err);
      showToast('Download failed: ' + err.message, 'error');
    } finally {
      downloadBtn.classList.remove('downloading');
      downloadBtn.disabled = false;
      downloadBtn.innerHTML = `
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="7 10 12 15 17 10"/>
          <line x1="12" y1="15" x2="12" y2="3"/>
        </svg>
      `;
    }
  }

  async function convertToWav(blob) {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    try {
      const arrayBuffer = await blob.arrayBuffer();
      const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);
      const numChannels = audioBuffer.numberOfChannels;
      const sampleRate = audioBuffer.sampleRate;
      const bitDepth = 16;

      let interleaved;
      if (numChannels === 2) {
        interleaved = interleave(audioBuffer.getChannelData(0), audioBuffer.getChannelData(1));
      } else {
        interleaved = audioBuffer.getChannelData(0);
      }

      const dataLength = interleaved.length * (bitDepth / 8);
      const totalLength = 44 + dataLength;
      const buffer = new ArrayBuffer(totalLength);
      const view = new DataView(buffer);

      writeString(view, 0, 'RIFF');
      view.setUint32(4, totalLength - 8, true);
      writeString(view, 8, 'WAVE');
      writeString(view, 12, 'fmt ');
      view.setUint32(16, 16, true);
      view.setUint16(20, 1, true);
      view.setUint16(22, numChannels, true);
      view.setUint32(24, sampleRate, true);
      view.setUint32(28, sampleRate * numChannels * (bitDepth / 8), true);
      view.setUint16(32, numChannels * (bitDepth / 8), true);
      view.setUint16(34, bitDepth, true);
      writeString(view, 36, 'data');
      view.setUint32(40, dataLength, true);

      let offset = 44;
      for (let i = 0; i < interleaved.length; i++) {
        const sample = Math.max(-1, Math.min(1, interleaved[i]));
        view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true);
        offset += 2;
      }
      return new Blob([buffer], { type: 'audio/wav' });
    } finally {
      audioCtx.close();
    }
  }

  function interleave(left, right) {
    const length = left.length + right.length;
    const result = new Float32Array(length);
    for (let i = 0; i < left.length; i++) {
      result[i * 2] = left[i];
      result[i * 2 + 1] = right[i];
    }
    return result;
  }

  function writeString(view, offset, string) {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  }

  function updatePlayIcon() {
    if (isPlaying) {
      playIcon.innerHTML = '<rect x="6" y="4" width="4" height="16" rx="1"/><rect x="14" y="4" width="4" height="16" rx="1"/>';
    } else {
      playIcon.innerHTML = '<polygon points="5 3 19 12 5 21 5 3"/>';
    }
  }

  playBtn.addEventListener('click', () => {
    if (audioPlayer.paused) { initAudioContext(); audioPlayer.play().catch(() => {}); }
    else { audioPlayer.pause(); }
  });

  audioPlayer.addEventListener('play', () => {
    isPlaying = true;
    updatePlayIcon();
    if (!audioContext) initAudioContext();
    drawWaveform();
  });

  audioPlayer.addEventListener('pause', () => { isPlaying = false; updatePlayIcon(); stopWaveform(); });
  audioPlayer.addEventListener('ended', () => { isPlaying = false; updatePlayIcon(); stopWaveform(); });

  audioPlayer.addEventListener('timeupdate', () => {
    if (audioPlayer.duration) {
      seekBar.value = (audioPlayer.currentTime / audioPlayer.duration) * 100;
      timeCurrent.textContent = formatTime(audioPlayer.currentTime);
    }
  });

  audioPlayer.addEventListener('loadedmetadata', () => {
    timeTotal.textContent = formatTime(audioPlayer.duration);
    seekBar.max = 100;
    try { setupAnalyser(); } catch (e) { /* ignored */ }
  });

  seekBar.addEventListener('input', () => {
    if (audioPlayer.duration) {
      audioPlayer.currentTime = (seekBar.value / 100) * audioPlayer.duration;
    }
  });

  downloadBtn.addEventListener('click', () => { downloadAudio(currentAudioUrl); });

  // ─── Helper: get audio URL from response ───────────────────────
  function getAudioUrlFromResponse(data) {
    // On Vercel, audio comes as base64; create an object URL from it.
    if (data.audio_base64) {
      try {
        const byteString = atob(data.audio_base64.split(',')[1]);
        const mimeString = data.audio_base64.split(',')[0].split(':')[1].split(';')[0];
        const ab = new ArrayBuffer(byteString.length);
        const ia = new Uint8Array(ab);
        for (let i = 0; i < byteString.length; i++) {
          ia[i] = byteString.charCodeAt(i);
        }
        const blob = new Blob([ab], { type: mimeString });
        return URL.createObjectURL(blob);
      } catch (e) {
        console.error('Failed to decode base64 audio:', e);
        return null;
      }
    }
    // Local dev: use the file URL
    return data.url || null;
  }

  // ─── Generate Speech ────────────────────────────────────────────
  generateBtn.addEventListener('click', async () => {
    const text = textInput.value.trim();
    if (!text) {
      showToast('Please enter some text first.', 'error');
      textInput.focus();
      return;
    }

    const voice     = currentVoiceId || 'us_female_jenny';
    const emotion   = document.querySelector('#emotionButtons .ctrl-btn.active')?.dataset.value || 'neutral';
    const language  = languageSelect.value;

    generateBtn.classList.add('loading');
    generateBtn.disabled = true;

    try {
      const response = await fetch(`${API_BASE}/synthesize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, voice, emotion, language }),
      });

      if (!response.ok) {
        let errorMsg = 'Synthesis failed';
        try {
          const err = await response.json();
          errorMsg = err.detail || errorMsg;
        } catch (jsonErr) {
          // Response wasn't JSON (e.g. Vercel HTML 500) — read as text
          try {
            const text = await response.text();
            errorMsg = text.slice(0, 200);
          } catch (textErr) {
            errorMsg = `HTTP ${response.status}: Server error`;
          }
        }
        throw new Error(errorMsg);
      }

      const data = await response.json();
      currentFilename = data.filename;
      currentAudioUrl = getAudioUrlFromResponse(data);

      if (!currentAudioUrl) {
        throw new Error('No audio URL or data in response');
      }

      if (source) { try { source.disconnect(); } catch (e) { /* ignored */ } source = null; }
      if (audioContext) { audioContext.close().catch(() => {}); audioContext = null; }

      audioPlayer.src = currentAudioUrl;
      audioPlayer.load();

      engineBadge.textContent = data.engine || 'edge-tts';
      if (data.fallback) {
        engineBadge.textContent += ' ⚠';
        engineBadge.title = 'Using fallback engine (emotion may be limited)';
      }
      durationBadge.textContent = data.estimated_duration_sec ? `${data.estimated_duration_sec}s` : '—';

      resultSection.style.display = 'block';
      resultSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

      audioPlayer.addEventListener('canplay', () => {
        initAudioContext();
        audioPlayer.play().catch(() => {});
      }, { once: true });

      addToHistory({
        text, voice, emotion, language,
        engine: data.engine, fallback: data.fallback,
        filename: data.filename, url: data.url,
        audio_base64: data.audio_base64,
        estimated_duration_sec: data.estimated_duration_sec, timestamp: Date.now(),
      });

      const currentTranslations = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
      showToast(currentTranslations.toastGenerating || 'Speech generated successfully!', 'success');
    } catch (err) {
      console.error('Generate error:', err);
      showToast(err.message || 'Failed to generate speech', 'error');
    } finally {
      generateBtn.classList.remove('loading');
      generateBtn.disabled = false;
    }
  });

  // ─── Keyboard Shortcut ──────────────────────────────────────────
  textInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      generateBtn.click();
    }
  });

  // ─── Initial Waveform ───────────────────────────────────────────
  stopWaveform();

  window.addEventListener('resize', () => { if (!isPlaying) stopWaveform(); });

  // ═════════════════════════════════════════════════════════════════
  // ─── i18n Translation System ───────────────────────────────────
  // ═════════════════════════════════════════════════════════════════

  function applyTranslations(lang) {
    const t = TRANSLATIONS[lang] || TRANSLATIONS.en;
    currentLang = lang;
    localStorage.setItem('fbv-lang', lang);

    langToggle.textContent = t.langSwitch || (lang === 'en' ? 'हिन्दी' : 'English');

    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.dataset.i18n;
      const text = t[key];
      if (text !== undefined) el.textContent = text;
    });

    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      const key = el.dataset.i18nPlaceholder;
      const text = t[key];
      if (text !== undefined) el.placeholder = text;
    });

    document.querySelectorAll('[data-i18n-title]').forEach(el => {
      const key = el.dataset.i18nTitle;
      const text = t[key];
      if (text !== undefined) el.title = text;
    });

    // Re-render voice cards & accent tabs with new language
    renderVoiceCards(currentVoiceGroup);
    updateAccentTabLabels();
  }

  langToggle.addEventListener('click', () => {
    const newLang = currentLang === 'en' ? 'hi' : 'en';
    applyTranslations(newLang);
  });

  // ═════════════════════════════════════════════════════════════════
  // ─── Speech History (localStorage) ─────────────────────────────
  // ═════════════════════════════════════════════════════════════════

  function getHistory() {
    try { const data = localStorage.getItem(HISTORY_KEY); return data ? JSON.parse(data) : []; }
    catch { return []; }
  }

  function saveHistory(history) {
    try { localStorage.setItem(HISTORY_KEY, JSON.stringify(history)); }
    catch (e) { console.warn('Failed to save history:', e); }
  }

  function addToHistory(entry) {
    if (!historyAutoSave.checked) return;
    let history = getHistory();
    history.unshift(entry);
    if (history.length > MAX_HISTORY) history = history.slice(0, MAX_HISTORY);
    saveHistory(history);
    renderHistory();
  }

  function removeFromHistory(index) {
    let history = getHistory();
    history.splice(index, 1);
    saveHistory(history);
    renderHistory();
  }

  function clearHistory() {
    const t = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
    if (!confirm(t.historyClearConfirm || 'Clear all history?')) return;
    saveHistory([]);
    renderHistory();
    showToast(t.historyToastCleared || 'History cleared', 'info');
  }

  function renderHistory() {
    const history = getHistory();
    const t = TRANSLATIONS[currentLang] || TRANSLATIONS.en;

    if (history.length === 0) {
      historySection.style.display = 'none';
      return;
    }

    historySection.style.display = 'block';
    historyCount.textContent = history.length;
    historyEmpty.style.display = 'none';

    historyList.innerHTML = history.map((item, index) => {
      const date = new Date(item.timestamp);
      const timeStr = date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      const textPreview = item.text.length > 60 ? item.text.slice(0, 60) + '…' : item.text;
      const emotionEmoji = { neutral: '😐', happy: '😊', sad: '😢', excited: '🎉' }[item.emotion] || '🎙️';

      return `
        <div class="history-item" data-index="${index}">
          <div class="history-item-main">
            <div class="history-item-text">${escapeHtml(textPreview)}</div>
            <div class="history-item-meta">
              <span class="history-meta-badge">${emotionEmoji} ${item.emotion}</span>
              <span class="history-meta-badge voice-badge">${getVoiceDisplayName(item.voice)}</span>
              <span class="history-meta-badge lang-badge">${item.language}</span>
              <span class="history-timestamp">${timeStr}</span>
            </div>
          </div>
          <div class="history-item-actions">
            <button class="history-action-btn replay-btn" data-index="${index}" title="${t.historyReplay || 'Replay'}">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
            </button>
            <button class="history-action-btn dl-btn" data-index="${index}" title="${t.historyDownload || 'Download'}">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            </button>
            <button class="history-action-btn del-btn" data-index="${index}" title="Delete">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
        </div>
      `;
    }).join('');

    historyList.querySelectorAll('.replay-btn').forEach(btn => {
      btn.addEventListener('click', (e) => { const idx = parseInt(e.currentTarget.dataset.index); replayFromHistory(idx); });
    });
    historyList.querySelectorAll('.dl-btn').forEach(btn => {
      btn.addEventListener('click', (e) => { const idx = parseInt(e.currentTarget.dataset.index); downloadFromHistory(idx); });
    });
    historyList.querySelectorAll('.del-btn').forEach(btn => {
      btn.addEventListener('click', (e) => { const idx = parseInt(e.currentTarget.dataset.index); removeFromHistory(idx); });
    });
  }

  function replayFromHistory(index) {
    const history = getHistory();
    const item = history[index];
    if (!item) return;

    currentFilename = item.filename;
    currentText = item.text;
    currentVoice = item.voice;
    currentEmotion = item.emotion;
    currentLanguage = item.language;

    // Get audio URL — prefer base64 (Vercel), fall back to file URL (local)
    currentAudioUrl = getAudioUrlFromResponse(item) || item.url;

    const resolvedVoiceId = VOICE_ALIASES_FRONTEND[item.voice] || item.voice;
    const foundVoice = VOICE_CATALOG.find(v => v.id === resolvedVoiceId);
    if (foundVoice) {
      currentVoiceId = resolvedVoiceId;
      currentVoiceGroup = foundVoice.group;
      voiceAccentTabs.forEach(t => { t.classList.toggle('active', t.dataset.group === foundVoice.group); });
      renderVoiceCards(currentVoiceGroup);
    }
    emotionButtons.forEach(b => { b.classList.toggle('active', b.dataset.value === item.emotion); });
    languageSelect.value = item.language;

    if (source) { try { source.disconnect(); } catch(e) {} source = null; }
    if (audioContext) { audioContext.close().catch(() => {}); audioContext = null; }

    audioPlayer.src = currentAudioUrl;
    audioPlayer.load();

    engineBadge.textContent = item.engine || 'edge-tts';
    durationBadge.textContent = item.estimated_duration_sec ? `${item.estimated_duration_sec}s` : '—';

    resultSection.style.display = 'block';

    audioPlayer.addEventListener('canplay', () => { initAudioContext(); audioPlayer.play().catch(() => {}); }, { once: true });

    const t = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
    showToast(t.historyToastReplay || 'Loaded from history', 'info');
  }

  async function downloadFromHistory(index) {
    const history = getHistory();
    const item = history[index];
    if (!item) return;
    currentAudioUrl = item.url;
    await downloadAudio(item.url);
  }

  function getVoiceDisplayName(voiceId) {
    const resolvedId = VOICE_ALIASES_FRONTEND[voiceId] || voiceId;
    const found = VOICE_CATALOG.find(v => v.id === resolvedId);
    if (found) return tr(found.nameKey);
    return voiceId.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  historyClearBtn.addEventListener('click', clearHistory);

  // ─── Apply i18n & render on load ────────────────────────────────
  applyTranslations(currentLang);
  renderHistory();

  console.log('🎙️ Freebuff Voice ready!');
  console.log('💡 Tip: Press Ctrl+Enter to generate speech');
  console.log('🌐 Toggle UI language with the हिन्दी button');
})();
