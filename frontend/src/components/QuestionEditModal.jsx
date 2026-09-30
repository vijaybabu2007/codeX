import React, { useState, useEffect } from 'react';
import { Edit3, X, Save, AlertCircle } from 'lucide-react';

export default function QuestionEditModal({
  isOpen,
  onClose,
  onSave,
  question,
  ordinal,
  isSubmitting,
  error
}) {
  const [questionText, setQuestionText] = useState('');
  const [options, setOptions] = useState(['', '', '', '']);
  const [correctAnswer, setCorrectAnswer] = useState('');
  const [rationale, setRationale] = useState('');
  const [teacherNotes, setTeacherNotes] = useState('');
  const [localError, setLocalError] = useState('');

  useEffect(() => {
    if (question) {
      setQuestionText(question.question_text || '');
      const opts = question.options && question.options.length > 0
        ? [...question.options]
        : ['', '', '', ''];
      while (opts.length < 4) opts.push('');
      setOptions(opts);
      setCorrectAnswer(question.correct_answer || opts[0] || '');
      setRationale(question.rationale || '');
      setTeacherNotes('');
      setLocalError('');
    }
  }, [question, isOpen]);

  if (!isOpen || !question) return null;

  const handleOptionChange = (idx, value) => {
    const next = [...options];
    const prevVal = next[idx];
    next[idx] = value;
    setOptions(next);
    // If the correct answer matched previous option value, keep it in sync
    if (correctAnswer === prevVal) {
      setCorrectAnswer(value);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!questionText.trim()) {
      setLocalError('Question stem cannot be empty.');
      return;
    }
    const filteredOpts = options.map(o => o.trim()).filter(Boolean);
    if (filteredOpts.length < 2) {
      setLocalError('Please provide at least 2 non-empty answer options.');
      return;
    }
    if (!correctAnswer.trim()) {
      setLocalError('Please designate a correct answer.');
      return;
    }
    if (!filteredOpts.some(opt => opt.toLowerCase() === correctAnswer.trim().toLowerCase())) {
      setLocalError('The designated correct answer must exactly match one of the options.');
      return;
    }

    setLocalError('');
    onSave({
      question_text: questionText.trim(),
      options: filteredOpts,
      correct_answer: correctAnswer.trim(),
      rationale: rationale.trim() || null,
      teacher_notes: teacherNotes.trim() || 'Manual teacher correction'
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-white border border-[#E2E8F0] rounded-2xl max-w-2xl w-full p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-150 space-y-4 my-8">
        <div className="flex items-start justify-between border-b border-[#E2E8F0] pb-3">
          <div className="flex items-center gap-2 text-[#123C35]">
            <Edit3 className="w-5 h-5 text-[#123C35]" />
            <h3 className="text-lg font-bold text-[#123C35]">
              Edit Question {ordinal} (Creates v{(question.version_number || 1) + 1})
            </h3>
          </div>
          <button
            onClick={onClose}
            disabled={isSubmitting}
            className="text-slate-400 hover:text-[#123C35] transition disabled:opacity-50 cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-950 leading-relaxed">
          <strong className="text-emerald-900">Immutable Versioning Rule:</strong> Current version <strong>v{question.version_number}</strong> will remain permanently preserved.
          Saving this edit creates a new immutable version in <strong>DRAFT</strong> status, keeping student views protected until explicit teacher approval.
        </div>

        {(localError || error) && (
          <div className="flex items-start gap-2 p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-900">
            <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
            <span>{localError || error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block font-bold text-[#123C35] mb-1">
              Question Stem <span className="text-rose-600">*</span>
            </label>
            <textarea
              value={questionText}
              onChange={(e) => setQuestionText(e.target.value)}
              rows={3}
              placeholder="Enter the question prompt..."
              className="w-full bg-[#F8FAFC] border border-[#CBD5E1] rounded-xl p-2.5 text-[#1F2937] placeholder-slate-400 focus:outline-none focus:border-[#123C35] focus:bg-white"
            />
          </div>

          <div className="space-y-2">
            <label className="block font-bold text-[#123C35]">
              Answer Options & Correct Answer Designation <span className="text-rose-600">*</span>
            </label>
            {options.map((opt, idx) => {
              const letter = String.fromCharCode(65 + idx);
              const isSelected = correctAnswer.trim() !== '' && correctAnswer.trim().toLowerCase() === opt.trim().toLowerCase();
              return (
                <div key={idx} className="flex items-center gap-2">
                  <span className="w-6 h-6 rounded-full bg-[#123C35] text-white border border-[#D4AF37] flex items-center justify-center font-mono font-bold text-xs flex-shrink-0">
                    {letter}
                  </span>
                  <input
                    type="text"
                    value={opt}
                    onChange={(e) => handleOptionChange(idx, e.target.value)}
                    placeholder={`Option ${letter}`}
                    className="flex-1 bg-[#F8FAFC] border border-[#CBD5E1] rounded-xl px-3 py-2 text-[#1F2937] placeholder-slate-400 focus:outline-none focus:border-[#123C35] focus:bg-white text-xs"
                  />
                  <button
                    type="button"
                    onClick={() => setCorrectAnswer(opt)}
                    className={`px-3 py-2 rounded-xl text-xs font-semibold transition border flex-shrink-0 cursor-pointer ${
                      isSelected
                        ? 'bg-[#123C35] text-white border-[#123C35] shadow-sm'
                        : 'bg-white text-[#1F2937] hover:bg-[#F8FAFC] border-[#CBD5E1]'
                    }`}
                  >
                    {isSelected ? '✓ Correct Answer' : 'Mark Correct'}
                  </button>
                </div>
              );
            })}
          </div>

          <div>
            <label className="block font-bold text-[#123C35] mb-1">
              Pedagogical Rationale / Explanation
            </label>
            <textarea
              value={rationale}
              onChange={(e) => setRationale(e.target.value)}
              rows={2}
              placeholder="Why this answer is correct and key conceptual distinction..."
              className="w-full bg-[#F8FAFC] border border-[#CBD5E1] rounded-xl p-2.5 text-[#1F2937] placeholder-slate-400 focus:outline-none focus:border-[#123C35] focus:bg-white"
            />
          </div>

          <div>
            <label className="block font-bold text-[#123C35] mb-1">
              Teacher Edit Reason / Notes
            </label>
            <input
              type="text"
              value={teacherNotes}
              onChange={(e) => setTeacherNotes(e.target.value)}
              placeholder="Reason for correction (e.g. 'Refined distractor B to match textbook wording')..."
              className="w-full bg-[#F8FAFC] border border-[#CBD5E1] rounded-xl px-3 py-2 text-[#1F2937] placeholder-slate-400 focus:outline-none focus:border-[#123C35] focus:bg-white"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-[#E2E8F0]">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-[#1F2937] hover:bg-slate-100 border border-[#CBD5E1] transition cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex items-center gap-1.5 px-5 py-2 rounded-xl text-xs font-bold text-white bg-[#123C35] hover:bg-[#0c2a25] disabled:opacity-50 transition shadow-sm cursor-pointer"
            >
              <Save className="w-4 h-4 text-[#D4AF37]" />
              <span>{isSubmitting ? 'Saving New Version...' : 'Save As New Version'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
