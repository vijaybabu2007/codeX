import React, { useState } from 'react';
import { AlertTriangle, AlertCircle, Info, CheckCircle, X, Shield, RefreshCw } from 'lucide-react';

export default function WarningAcknowledgementModal({
  isOpen,
  onClose,
  onConfirm,
  onRejectToRevision,
  itemTitle,
  warnings,
  isSubmitting
}) {
  const [selectedWarnings, setSelectedWarnings] = useState(() => {
    return warnings ? warnings.map(w => w.id || w.rule_code) : [];
  });
  const [notes, setNotes] = useState('');

  if (!isOpen || !warnings || warnings.length === 0) return null;

  const toggleWarning = (warningId) => {
    setSelectedWarnings(prev =>
      prev.includes(warningId)
        ? prev.filter(id => id !== warningId)
        : [...prev, warningId]
    );
  };

  const handleSelectAll = () => {
    setSelectedWarnings(warnings.map(w => w.id || w.rule_code));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onConfirm(selectedWarnings, notes.trim());
  };

  const handleNeedsRevision = () => {
    if (onRejectToRevision) {
      onRejectToRevision(notes.trim());
    }
  };

  const getSeverityBadge = (severity) => {
    const sev = (severity || 'WARNING').toUpperCase();
    if (sev === 'CRITICAL') {
      return (
        <span className="flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded bg-rose-50 text-rose-800 border border-rose-200">
          <AlertCircle className="w-3 h-3 text-rose-600" />
          CRITICAL
        </span>
      );
    }
    if (sev === 'INFO') {
      return (
        <span className="flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded bg-sky-50 text-sky-800 border border-sky-200">
          <Info className="w-3 h-3 text-sky-600" />
          INFO
        </span>
      );
    }
    return (
      <span className="flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded bg-amber-50 text-amber-900 border border-amber-300">
        <AlertTriangle className="w-3 h-3 text-amber-600" />
        WARNING
      </span>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-white border border-[#E2E8F0] rounded-2xl max-w-lg w-full p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-150 space-y-4">
        <div className="flex items-start justify-between border-b border-[#E2E8F0] pb-3">
          <div className="flex items-center gap-2 text-[#123C35]">
            <AlertTriangle className="w-5 h-5 text-[#D4AF37]" />
            <h3 className="text-lg font-bold text-[#123C35]">Review & Acknowledge Warnings</h3>
          </div>
          <button
            onClick={onClose}
            disabled={isSubmitting}
            className="text-slate-400 hover:text-[#123C35] transition disabled:opacity-50 cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="text-xs text-[#1F2937]">
          The following pedagogical notices were flagged for <strong className="text-[#123C35]">{itemTitle}</strong>.
          You can explicitly acknowledge these notices to approve the item, or route it back for revision.
        </p>

        <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
          {warnings.map((w, idx) => {
            const wId = w.id || w.rule_code;
            const isChecked = selectedWarnings.includes(wId);
            const severity = (w.severity || 'WARNING').toUpperCase();
            return (
              <label
                key={idx}
                className={`flex items-start gap-3 p-3 rounded-xl border text-xs cursor-pointer transition ${
                  isChecked
                    ? severity === 'CRITICAL'
                      ? 'bg-rose-50 border-rose-300 text-rose-950'
                      : 'bg-amber-50/80 border-amber-300 text-amber-950'
                    : 'bg-[#F8FAFC] border-[#E2E8F0] text-[#1F2937] hover:bg-slate-100'
                }`}
              >
                <input
                  type="checkbox"
                  checked={isChecked}
                  onChange={() => toggleWarning(wId)}
                  className="mt-0.5 rounded border-[#CBD5E1] text-[#123C35] focus:ring-[#123C35]"
                />
                <div className="space-y-1 flex-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-[#123C35] flex items-center gap-1.5">
                      <Shield className="w-3.5 h-3.5 text-[#D4AF37]" />
                      {w.rule_code || 'PEDAGOGICAL_CHECK'}
                    </span>
                    {getSeverityBadge(w.severity)}
                  </div>
                  <p className="text-[11px] text-[#1F2937] leading-relaxed">{w.message}</p>
                </div>
              </label>
            );
          })}
        </div>

        <div className="flex items-center justify-between text-xs pt-1">
          <button
            type="button"
            onClick={handleSelectAll}
            className="text-[#123C35] hover:underline font-bold text-[11px] cursor-pointer"
          >
            Select / Acknowledge All ({warnings.length})
          </button>
          <span className="text-[#64748B] text-[11px]">
            {selectedWarnings.length} of {warnings.length} selected
          </span>
        </div>

        <div className="text-xs space-y-1">
          <label className="block font-bold text-[#123C35]">
            Teacher Audit Notes (Optional)
          </label>
          <input
            type="text"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Add acknowledgement justification or revision instructions..."
            className="w-full bg-[#F8FAFC] border border-[#CBD5E1] rounded-xl px-3 py-2 text-[#1F2937] placeholder-slate-400 focus:outline-none focus:border-[#123C35] focus:bg-white text-xs"
          />
        </div>

        <div className="flex flex-wrap items-center justify-between gap-2 pt-3 border-t border-[#E2E8F0]">
          <div>
            {onRejectToRevision && (
              <button
                type="button"
                onClick={handleNeedsRevision}
                disabled={isSubmitting}
                className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold text-amber-900 bg-amber-50 hover:bg-amber-100 border border-amber-300 transition cursor-pointer"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Needs Revision</span>
              </button>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-3.5 py-2 rounded-xl text-xs font-semibold text-[#1F2937] hover:bg-slate-100 border border-[#CBD5E1] transition cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-white bg-[#123C35] hover:bg-[#0c2a25] disabled:opacity-50 transition shadow-sm cursor-pointer"
            >
              <CheckCircle className="w-4 h-4 text-[#D4AF37]" />
              <span>{isSubmitting ? 'Approving...' : 'Acknowledge & Approve'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
