import React, { useState } from 'react';
import { ShieldAlert, X, Check } from 'lucide-react';

export default function OverrideModal({ isOpen, onClose, onConfirm, itemTitle, warnings }) {
  const [notes, setNotes] = useState('');
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!notes.trim()) {
      setError('A written justification note is required to execute a critical override.');
      return;
    }
    const warningIds = warnings.map(w => w.id || w.rule_code);
    onConfirm(notes, warningIds);
    setNotes('');
    setError('');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-white border border-[#E2E8F0] rounded-2xl max-w-lg w-full p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2 text-rose-700">
            <ShieldAlert className="w-5 h-5 text-rose-600" />
            <h3 className="text-lg font-bold text-[#123C35]">Override Critical Validation</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-[#123C35] cursor-pointer">
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="text-xs text-[#1F2937] mt-2">
          You are explicitly overriding system guardrails for: <strong className="text-[#123C35]">{itemTitle}</strong>.
          This decision will be permanently logged in the audit trail and make this item eligible for student view.
        </p>

        {warnings && warnings.length > 0 && (
          <div className="mt-3 p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs">
            <div className="font-bold text-rose-950 mb-1">Warnings Being Acknowledged:</div>
            <ul className="list-disc list-inside text-rose-900 space-y-1">
              {warnings.map((w, idx) => (
                <li key={idx}>
                  <strong>{w.rule_code}:</strong> {w.message}
                </li>
              ))}
            </ul>
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-4">
          <label className="block text-xs font-bold text-[#123C35] mb-1">
            Teacher Justification Note <span className="text-rose-600">* (Mandatory)</span>
          </label>
          <textarea
            value={notes}
            onChange={(e) => {
              setNotes(e.target.value);
              if (error) setError('');
            }}
            placeholder="Explain why this content is pedagogically acceptable despite the critical warning (e.g. 'Alternative spelling accepted in classroom context')..."
            className="w-full h-24 bg-[#F8FAFC] border border-[#CBD5E1] rounded-xl p-2.5 text-xs text-[#1F2937] placeholder-slate-400 focus:outline-none focus:border-rose-600 focus:bg-white transition"
          />
          {error && <p className="text-xs text-rose-600 font-semibold mt-1">{error}</p>}

          <div className="flex items-center justify-end gap-2 mt-5">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-[#1F2937] hover:bg-slate-100 border border-[#CBD5E1] transition cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-bold text-white bg-rose-700 hover:bg-rose-800 transition shadow-sm cursor-pointer"
            >
              <Check className="w-4 h-4" />
              Sign Off & Override
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
