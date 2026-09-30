import React, { useState } from 'react';
import { RotateCcw, X, Sparkles, Loader2, AlertCircle } from 'lucide-react';

export default function RegenerateModal({
  isOpen,
  onClose,
  onConfirm,
  questionOrdinal,
  currentQuestionText,
  currentVersionNumber,
  isSubmitting,
  error
}) {
  const [teacherNotes, setTeacherNotes] = useState('');
  const [reason, setReason] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    onConfirm(teacherNotes, reason);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-white border border-[#E2E8F0] rounded-2xl max-w-lg w-full p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-150 space-y-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2 text-[#123C35]">
            <RotateCcw className="w-5 h-5 text-[#123C35]" />
            <h3 className="text-lg font-bold text-[#123C35]">Surgically Regenerate Question {questionOrdinal}</h3>
          </div>
          <button
            onClick={onClose}
            disabled={isSubmitting}
            className="text-slate-400 hover:text-[#123C35] transition disabled:opacity-50 cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="bg-[#F8FAFC] p-3.5 rounded-xl border border-[#E2E8F0] text-xs space-y-1">
          <div className="flex items-center justify-between text-[#64748B]">
            <span className="font-bold text-[#123C35]">Current Question (v{currentVersionNumber}):</span>
            <span className="text-[10px] bg-[#F1F5F9] text-[#123C35] border border-[#CBD5E1] px-1.5 py-0.5 rounded font-mono font-semibold">Immutable</span>
          </div>
          <p className="text-[#1F2937] italic">"{currentQuestionText}"</p>
        </div>

        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-[11px] text-emerald-950 leading-relaxed">
          <strong className="text-emerald-900">Approved Content Protection:</strong> Only Question {questionOrdinal} will be regenerated (yielding <strong>v{currentVersionNumber + 1}</strong> in <strong>DRAFT</strong>).
          All other approved assets and questions (e.g. Q1, Q2) remain permanently intact.
        </div>

        {error && (
          <div className="flex items-start gap-2 p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-900">
            <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-xs font-bold text-[#123C35] mb-1">
              Reason for Regeneration (Optional)
            </label>
            <input
              type="text"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              disabled={isSubmitting}
              placeholder="e.g., Too simple, ambiguous distractors, needs higher cognitive demand"
              className="w-full bg-[#F8FAFC] border border-[#CBD5E1] rounded-lg p-2.5 text-xs text-[#1F2937] placeholder-slate-400 focus:outline-none focus:border-[#123C35] focus:bg-white"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-[#123C35] mb-1">
              Teacher Feedback & Prompt Context
            </label>
            <textarea
              value={teacherNotes}
              onChange={(e) => setTeacherNotes(e.target.value)}
              disabled={isSubmitting}
              rows={3}
              placeholder="e.g., Focus specifically on the role of ATP synthase or light reactions. Ensure distractors test common misconceptions."
              className="w-full bg-[#F8FAFC] border border-[#CBD5E1] rounded-lg p-2.5 text-xs text-[#1F2937] placeholder-slate-400 focus:outline-none focus:border-[#123C35] focus:bg-white"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#E2E8F0]">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-3.5 py-1.5 rounded-lg border border-[#CBD5E1] text-[#1F2937] text-xs font-semibold hover:bg-slate-100 transition disabled:opacity-50 cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-[#123C35] hover:bg-[#0c2a25] text-white text-xs font-bold transition shadow-sm disabled:opacity-50 cursor-pointer"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Regenerating with LLM...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5 text-[#D4AF37]" />
                  <span>Generate New Version</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
