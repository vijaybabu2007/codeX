// Text-to-Speech (TTS) Abstraction Layer
// Wraps browser SpeechSynthesis with multilingual voice resolution (including Tamil).

export class TTSService {
  constructor() {
    this.synth = typeof window !== 'undefined' ? window.speechSynthesis : null;
    this.lastSpokenText = '';
    this.lastLanguage = 'en';
    this.currentUtterance = null;
    this.isSpeaking = false;
  }

  isSupported() {
    return Boolean(this.synth);
  }

  getVoices() {
    if (!this.synth) return [];
    return this.synth.getVoices() || [];
  }

  resolveVoice(language = 'en') {
    const voices = this.getVoices();
    if (!voices || voices.length === 0) return null;

    const langLower = (language || 'en').toLowerCase();

    // 1. Tamil matching
    if (langLower.startsWith('ta') || langLower.includes('tamil')) {
      const tamilVoice = voices.find(
        (v) =>
          v.lang.toLowerCase().startsWith('ta') ||
          v.name.toLowerCase().includes('tamil') ||
          v.name.toLowerCase().includes('valluvar') ||
          v.name.toLowerCase().includes('latha')
      );
      if (tamilVoice) return tamilVoice;
    }

    // 2. Hindi matching
    if (langLower.startsWith('hi') || langLower.includes('hindi')) {
      const hindiVoice = voices.find(
        (v) => v.lang.toLowerCase().startsWith('hi') || v.name.toLowerCase().includes('hindi')
      );
      if (hindiVoice) return hindiVoice;
    }

    // 3. English matching
    const enVoice = voices.find(
      (v) =>
        (v.lang.toLowerCase().startsWith('en') || v.lang.toLowerCase().includes('us') || v.lang.toLowerCase().includes('gb')) &&
        (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Microsoft') || v.default)
    ) || voices.find((v) => v.lang.toLowerCase().startsWith('en'));

    return enVoice || voices[0] || null;
  }

  speak(text, { language = 'en', onStart, onEnd, onError } = {}) {
    if (!this.isSupported() || !text || !text.trim()) {
      if (onEnd) onEnd();
      return;
    }

    this.stop();

    this.lastSpokenText = text;
    this.lastLanguage = language;

    try {
      // Clean markdown tags or bullets before speaking for smooth audio
      const cleanText = text
        .replace(/[*_#`~>]/g, '')
        .replace(/\n+/g, '. ')
        .trim();

      const utterance = new SpeechSynthesisUtterance(cleanText);
      const voice = this.resolveVoice(language);
      if (voice) {
        utterance.voice = voice;
        utterance.lang = voice.lang;
      } else {
        utterance.lang = language.startsWith('ta') ? 'ta-IN' : 'en-US';
      }

      utterance.rate = 1.0;
      utterance.pitch = 1.0;

      utterance.onstart = () => {
        this.isSpeaking = true;
        if (onStart) onStart();
      };

      utterance.onend = () => {
        this.isSpeaking = false;
        this.currentUtterance = null;
        if (onEnd) onEnd();
      };

      utterance.onerror = (e) => {
        this.isSpeaking = false;
        this.currentUtterance = null;
        if (onError) onError(e);
      };

      this.currentUtterance = utterance;
      this.synth.speak(utterance);
    } catch (err) {
      this.isSpeaking = false;
      if (onError) onError(err);
    }
  }

  stop() {
    if (this.synth) {
      try {
        this.synth.cancel();
      } catch {
        // Ignore cancel errors
      }
    }
    this.isSpeaking = false;
    this.currentUtterance = null;
  }

  replay({ onStart, onEnd, onError } = {}) {
    if (this.lastSpokenText) {
      this.speak(this.lastSpokenText, {
        language: this.lastLanguage,
        onStart,
        onEnd,
        onError
      });
    }
  }
}

export const ttsService = new TTSService();
