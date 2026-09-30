// Speech-to-Text (STT) Abstraction Layer
// Wraps browser SpeechRecognition with fallback detection and error normalization.

export class STTService {
  constructor() {
    const SpeechRecognition =
      window.SpeechRecognition ||
      window.webkitSpeechRecognition ||
      null;
    this.SpeechRecognition = SpeechRecognition;
    this.recognitionInstance = null;
    this.isListening = false;
  }

  isSupported() {
    return Boolean(this.SpeechRecognition);
  }

  startListening({ onResult, onError, onEnd, language = 'en-US' }) {
    if (!this.isSupported()) {
      if (onError) {
        onError({
          code: 'UNSUPPORTED_BROWSER',
          message: 'Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari, or type your question.'
        });
      }
      return null;
    }

    if (this.isListening) {
      this.stopListening();
    }

    try {
      const recognition = new this.SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.maxAlternatives = 1;
      recognition.lang = language;

      let finalTranscript = '';

      recognition.onstart = () => {
        this.isListening = true;
      };

      recognition.onresult = (event) => {
        let interimTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }
        if (onResult) {
          onResult({
            transcript: finalTranscript || interimTranscript,
            isFinal: Boolean(finalTranscript)
          });
        }
      };

      recognition.onerror = (event) => {
        this.isListening = false;
        let userMessage = 'Speech recognition failed.';
        let code = event.error || 'UNKNOWN';

        switch (event.error) {
          case 'not-allowed':
          case 'service-not-allowed':
            userMessage = 'Microphone permission was denied. Please allow microphone access in your browser settings.';
            code = 'PERMISSION_DENIED';
            break;
          case 'no-speech':
            userMessage = 'No speech was detected. Please try speaking again.';
            code = 'NO_SPEECH';
            break;
          case 'audio-capture':
            userMessage = 'No microphone was found or microphone is busy.';
            code = 'AUDIO_CAPTURE';
            break;
          case 'network':
            userMessage = 'Network error occurred during speech recognition.';
            code = 'NETWORK_ERROR';
            break;
          case 'aborted':
            // User cancelled or stopped speaking
            return;
          default:
            userMessage = `Speech recognition error: ${event.error}`;
        }

        if (onError) {
          onError({ code, message: userMessage });
        }
      };

      recognition.onend = () => {
        this.isListening = false;
        if (onEnd) onEnd(finalTranscript);
      };

      this.recognitionInstance = recognition;
      recognition.start();

      return {
        stop: () => this.stopListening()
      };
    } catch (err) {
      this.isListening = false;
      if (onError) {
        onError({
          code: 'INITIALIZATION_FAILED',
          message: err.message || 'Failed to start microphone recognition.'
        });
      }
      return null;
    }
  }

  stopListening() {
    if (this.recognitionInstance) {
      try {
        this.recognitionInstance.stop();
      } catch {
        // Ignore stop error
      }
      this.recognitionInstance = null;
    }
    this.isListening = false;
  }
}

export const sttService = new STTService();
