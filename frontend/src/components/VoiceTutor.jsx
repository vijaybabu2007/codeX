import React, { useState, useEffect, useRef } from 'react';
import {
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  RotateCcw,
  Sparkles,
  AlertCircle,
  ShieldCheck,
  Send,
  Languages,
  BookOpen
} from 'lucide-react';
import { sttService } from '../services/sttService';
import { ttsService } from '../services/ttsService';
import { queryVoiceTutor } from '../api';

const STATES = {
  IDLE: 'IDLE',
  LISTENING: 'LISTENING',
  PROCESSING: 'PROCESSING',
  SPEAKING: 'SPEAKING',
  ERROR: 'ERROR'
};

const SUGGESTED_QUERIES = [
  { label: '💡 Explain simply', query: 'Explain this concept in simple terms.' },
  { label: '🔍 Give an example', query: 'Give me an example based on this lesson.' },
  { label: '🌐 Explain in Tamil', query: 'Explain this in Tamil.' },
  { label: '📝 Practice question', query: 'Give me one practice question from this lesson.' },
  { label: '❓ Review my quiz', query: 'Why was my answer wrong?' }
];

export default function VoiceTutor({ packId, lastQuizSubmission, externalPrompt }) {
  const [tutorState, setTutorState] = useState(STATES.IDLE);
  const [transcript, setTranscript] = useState('');
  const [inputText, setInputText] = useState('');
  const [response, setResponse] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [sttSupported, setSttSupported] = useState(true);
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  const activeListenerRef = useRef(null);

  useEffect(() => {
    setSttSupported(sttService.isSupported());
    return () => {
      sttService.stopListening();
      ttsService.stop();
    };
  }, []);

  const handleStartListening = () => {
    ttsService.stop();
    setErrorMessage('');
    setTranscript('');
    setTutorState(STATES.LISTENING);

    const handle = sttService.startListening({
      language: selectedLanguage === 'ta' ? 'ta-IN' : 'en-US',
      onResult: ({ transcript: text, isFinal }) => {
        setTranscript(text);
        setInputText(text);
      },
      onError: (err) => {
        setTutorState(STATES.ERROR);
        setErrorMessage(err.message || 'Microphone error.');
      },
      onEnd: (finalText) => {
        const textToQuery = finalText || transcript || inputText;
        if (textToQuery && textToQuery.trim()) {
          executeVoiceQuery(textToQuery.trim());
        } else {
          setTutorState(STATES.IDLE);
        }
      }
    });

    activeListenerRef.current = handle;
  };

  const handleStopListening = () => {
    sttService.stopListening();
    if (transcript && transcript.trim()) {
      executeVoiceQuery(transcript.trim());
    } else {
      setTutorState(STATES.IDLE);
    }
  };

  const executeVoiceQuery = async (queryText) => {
    if (!queryText || !queryText.trim()) return;

    sttService.stopListening();
    ttsService.stop();
    setTutorState(STATES.PROCESSING);
    setErrorMessage('');

    try {
      const payload = {
        pack_id: packId,
        question: queryText.trim(),
        language: selectedLanguage
      };

      if (lastQuizSubmission) {
        payload.quiz_submission = lastQuizSubmission;
      }

      const res = await queryVoiceTutor(payload);
      setResponse(res);

      if (res && res.answer) {
        setTutorState(STATES.SPEAKING);
        ttsService.speak(res.answer, {
          language: res.language === 'ta' ? 'ta-IN' : 'en-US',
          onEnd: () => setTutorState(STATES.IDLE),
          onError: () => setTutorState(STATES.IDLE)
        });
      } else {
        setTutorState(STATES.IDLE);
      }
    } catch (err) {
      setTutorState(STATES.ERROR);
      setErrorMessage(err.message || 'Voice tutor failed to generate a response.');
    }
  };

  // Handle external prompt from Adaptive Mastery or other components
  useEffect(() => {
    if (externalPrompt) {
      const promptText = typeof externalPrompt === 'string' ? externalPrompt : externalPrompt.text;
      if (promptText && promptText.trim()) {
        setInputText(promptText.trim());
        executeVoiceQuery(promptText.trim());
      }
    }
  }, [externalPrompt]);

  const handleTextSubmit = (e) => {
    e.preventDefault();
    if (inputText && inputText.trim()) {
      executeVoiceQuery(inputText.trim());
    }
  };

  const handleReplay = () => {
    if (response && response.answer) {
      ttsService.stop();
      setTutorState(STATES.SPEAKING);
      ttsService.speak(response.answer, {
        language: response.language === 'ta' ? 'ta-IN' : 'en-US',
        onEnd: () => setTutorState(STATES.IDLE),
        onError: () => setTutorState(STATES.IDLE)
      });
    }
  };

  const handleStopSpeaking = () => {
    ttsService.stop();
    setTutorState(STATES.IDLE);
  };

  return (
    <div className="bg-white border border-[#E2E8F0] rounded-2xl p-6 shadow-sm transition-all text-[#1F2937]">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-4 mb-5">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-[#123C35] text-[#D4AF37] shadow-sm">
            <Sparkles className="w-5 h-5 text-[#D4AF37]" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-[#123C35] flex items-center gap-2">
              🎙️ Ask LessonFoundry Voice Tutor
            </h3>
            <p className="text-xs text-[#64748B]">
              Conversational learning assistant grounded strictly in teacher-approved lesson materials
            </p>
          </div>
        </div>

        {/* State Badge & Language Selector */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#F8FAFC] border border-[#CBD5E1] text-xs">
            <Languages className="w-3.5 h-3.5 text-[#123C35]" />
            <select
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
              className="bg-transparent text-[#1F2937] outline-none text-xs cursor-pointer font-medium"
            >
              <option value="en">English</option>
              <option value="ta">Tamil (தமிழ்)</option>
            </select>
          </div>

          <span
            className={`px-3 py-1 rounded-full text-xs font-semibold tracking-wide uppercase flex items-center gap-1.5 ${
              tutorState === STATES.LISTENING
                ? 'bg-rose-100 text-rose-800 border border-rose-300 animate-pulse'
                : tutorState === STATES.PROCESSING
                ? 'bg-amber-100 text-amber-800 border border-amber-300'
                : tutorState === STATES.SPEAKING
                ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                : tutorState === STATES.ERROR
                ? 'bg-red-100 text-red-800 border border-red-300'
                : 'bg-[#123C35]/10 text-[#123C35] border border-[#123C35]/25'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                tutorState === STATES.LISTENING
                  ? 'bg-rose-600 animate-ping'
                  : tutorState === STATES.PROCESSING
                  ? 'bg-amber-600 animate-spin'
                  : tutorState === STATES.SPEAKING
                  ? 'bg-emerald-600'
                  : tutorState === STATES.ERROR
                  ? 'bg-red-600'
                  : 'bg-[#123C35]'
              }`}
            />
            {tutorState}
          </span>
        </div>
      </div>

      {/* Main Interaction Area */}
      <div className="flex flex-col gap-4">
        {/* Microphone Button & Wave animation */}
        <div className="flex flex-col items-center justify-center p-6 rounded-xl bg-[#F8FAFC] border border-[#E2E8F0]">
          <div className="relative flex items-center justify-center mb-3">
            {tutorState === STATES.LISTENING && (
              <span className="absolute w-20 h-20 rounded-full bg-rose-500/20 animate-ping" />
            )}
            {tutorState === STATES.SPEAKING && (
              <span className="absolute w-20 h-20 rounded-full bg-emerald-500/20 animate-pulse" />
            )}
            <button
              onClick={
                tutorState === STATES.LISTENING
                  ? handleStopListening
                  : handleStartListening
              }
              disabled={tutorState === STATES.PROCESSING}
              className={`relative z-10 w-16 h-16 rounded-full flex items-center justify-center shadow-md transition-all transform hover:scale-105 active:scale-95 cursor-pointer ${
                tutorState === STATES.LISTENING
                  ? 'bg-rose-600 hover:bg-rose-500 text-white ring-4 ring-rose-400/30'
                  : tutorState === STATES.SPEAKING
                  ? 'bg-emerald-600 hover:bg-emerald-500 text-white ring-4 ring-emerald-400/30'
                  : 'bg-[#123C35] hover:bg-[#0c2a25] text-[#D4AF37] ring-4 ring-[#123C35]/15'
              }`}
              title={
                tutorState === STATES.LISTENING
                  ? 'Click to Stop Listening'
                  : 'Click to Speak with LessonFoundry Voice Tutor'
              }
            >
              {tutorState === STATES.LISTENING ? (
                <MicOff className="w-7 h-7 text-white" />
              ) : (
                <Mic className="w-7 h-7" />
              )}
            </button>
          </div>

          <p className="text-sm font-semibold text-[#1F2937]">
            {tutorState === STATES.LISTENING
              ? '🎙️ Listening... Speak your question now'
              : tutorState === STATES.PROCESSING
              ? '⚡ Thinking with approved lesson context...'
              : tutorState === STATES.SPEAKING
              ? '🔊 Voice Tutor is speaking...'
              : 'Tap the microphone to speak, or type your question below'}
          </p>

          {!sttSupported && (
            <p className="text-xs text-amber-700 mt-1 flex items-center gap-1">
              <AlertCircle className="w-3.5 h-3.5" />
              Speech recognition unavailable in this browser; you can type queries below.
            </p>
          )}
        </div>

        {/* Suggested Quick Inquiries */}
        <div className="flex flex-wrap gap-2 pt-1">
          <span className="text-xs text-[#64748B] self-center font-bold">Quick Prompts:</span>
          {SUGGESTED_QUERIES.map((item, idx) => (
            <button
              key={idx}
              onClick={() => {
                setInputText(item.query);
                setTranscript(item.query);
                executeVoiceQuery(item.query);
              }}
              disabled={tutorState === STATES.PROCESSING || tutorState === STATES.LISTENING}
              className="text-xs px-3 py-1.5 rounded-lg bg-white hover:bg-[#F8FAFC] border border-[#CBD5E1] hover:border-[#123C35] text-[#123C35] font-semibold transition-all shadow-sm cursor-pointer"
            >
              {item.label}
            </button>
          ))}
        </div>

        {/* Text Input Fallback Bar */}
        <form onSubmit={handleTextSubmit} className="flex gap-2">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Or type a question about this lesson..."
            disabled={tutorState === STATES.PROCESSING || tutorState === STATES.LISTENING}
            className="flex-1 px-4 py-2.5 rounded-xl bg-white border border-[#CBD5E1] text-sm text-[#1F2937] placeholder-[#94A3B8] focus:outline-none focus:border-[#123C35] focus:ring-1 focus:ring-[#123C35]/20 transition-all font-medium"
          />
          <button
            type="submit"
            disabled={!inputText.trim() || tutorState === STATES.PROCESSING}
            className="px-5 py-2.5 rounded-xl bg-[#123C35] hover:bg-[#0c2a25] disabled:opacity-50 text-white font-bold text-sm flex items-center gap-1.5 shadow-sm transition-all cursor-pointer"
          >
            <Send className="w-4 h-4 text-[#D4AF37]" />
            Ask
          </button>
        </form>

        {/* Transcript Display */}
        {transcript && (
          <div className="p-3.5 rounded-xl bg-[#F8FAFC] border border-[#CBD5E1] text-xs">
            <span className="font-bold text-[#64748B] uppercase tracking-wider block mb-1">
              You Asked:
            </span>
            <p className="text-[#1F2937] italic font-medium">"{transcript}"</p>
          </div>
        )}

        {/* Error Display */}
        {tutorState === STATES.ERROR && errorMessage && (
          <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 text-sm flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
            <div className="flex-1">
              <span className="font-bold block">Notice</span>
              <p className="text-xs text-red-700 mt-0.5">{errorMessage}</p>
            </div>
          </div>
        )}

        {/* AI Response Display */}
        {response && (
          <div className="p-5 rounded-xl bg-[#F8FAFC] border border-[#CBD5E1] shadow-sm flex flex-col gap-3">
            <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-2.5">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-[#123C35] flex items-center gap-1">
                  <ShieldCheck className="w-4 h-4 text-[#059669]" />
                  Voice Tutor Answer
                </span>
                {response.intent && (
                  <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-[#123C35]/10 text-[#123C35] border border-[#123C35]/20">
                    Intent: {response.intent}
                  </span>
                )}
                {response.grounded && (
                  <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-[#ECFDF5] text-[#065F46] border border-[#A7F3D0]">
                    Grounded in Approved Material
                  </span>
                )}
              </div>

              {/* Audio Controls */}
              <div className="flex items-center gap-1.5">
                {tutorState === STATES.SPEAKING ? (
                  <button
                    onClick={handleStopSpeaking}
                    className="p-1.5 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-300 text-xs flex items-center gap-1 transition-all cursor-pointer font-semibold"
                    title="Stop Speaking"
                  >
                    <VolumeX className="w-3.5 h-3.5" />
                    Stop
                  </button>
                ) : (
                  <button
                    onClick={handleReplay}
                    className="p-1.5 rounded-lg bg-white hover:bg-slate-50 text-[#123C35] border border-[#CBD5E1] text-xs flex items-center gap-1 transition-all cursor-pointer font-semibold shadow-sm"
                    title="Replay Audio"
                  >
                    <RotateCcw className="w-3.5 h-3.5 text-[#D4AF37]" />
                    Replay
                  </button>
                )}
              </div>
            </div>

            {/* Answer Text */}
            <p className="text-sm text-[#1F2937] leading-relaxed font-sans whitespace-pre-wrap font-medium">
              {response.answer}
            </p>

            {/* Target Objectives */}
            {response.objective_ids && response.objective_ids.length > 0 && (
              <div className="flex items-center gap-1.5 pt-1">
                <span className="text-[11px] text-[#64748B] font-bold">Addressed:</span>
                <div className="flex flex-wrap gap-1">
                  {response.objective_ids.map(objId => (
                    <span key={objId} className="px-2 py-0.5 rounded bg-white text-[#123C35] border border-[#CBD5E1] font-mono text-[10px] font-bold shadow-sm">
                      {objId}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Supporting Evidence Citation */}
            {response.supporting_quote && (
              <div className="mt-1 p-3 rounded-lg bg-white border border-[#E2E8F0] text-xs space-y-1">
                <div className="flex items-center gap-1.5 text-[#123C35] font-bold">
                  <BookOpen className="w-3.5 h-3.5 text-[#D4AF37]" />
                  <span>Citations from Approved Material:</span>
                </div>
                <blockquote className="italic text-[#1F2937] pl-2.5 border-l-2 border-[#123C35]">
                  "{response.supporting_quote}"
                </blockquote>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
