import React, { useState, useEffect } from 'react';
import { GitCompare, X, ArrowRight, AlertCircle, FileText } from 'lucide-react';
import { fetchQuestionDiff } from '../api';

export default function VersionDiffModal({
  isOpen,
  onClose,
  question,
  ordinal
}) {
  const [versionA, setVersionA] = useState(1);
  const [versionB, setVersionB] = useState(1);
  const [diffData, setDiffData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const versions = question?.versions || [];

  useEffect(() => {
    if (question && versions.length > 0) {
      const vNums = versions.map(v => v.version_number).sort((a, b) => a - b);
      const vMin = vNums[0];
      const vMax = vNums[vNums.length - 1];
      // Default version A to previous or lowest, version B to highest
      setVersionA(vNums.length > 1 ? vNums[vNums.length - 2] : vMin);
      setVersionB(vMax);
    }
  }, [question, isOpen]);

  useEffect(() => {
    if (!isOpen || !question) return;

    let isMounted = true;
    const loadDiff = async () => {
      setIsLoading(true);
      setError('');
      try {
        const data = await fetchQuestionDiff(question.question_id, versionA, versionB);
        if (isMounted) setDiffData(data);
      } catch (err) {
        if (isMounted) setError(err.message || 'Failed to load version diff');
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    loadDiff();
    return () => { isMounted = false; };
  }, [question, versionA, versionB, isOpen]);

  if (!isOpen || !question) return null;

  const changedFields = diffData?.changed_fields || [];
  const detailsA = diffData?.version_a;
  const detailsB = diffData?.version_b;

  const isFieldChanged = (fieldName) => changedFields.includes(fieldName);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-white border border-[#E2E8F0] rounded-2xl max-w-4xl w-full p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-150 space-y-4 my-8 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-[#E2E8F0] pb-3 flex-shrink-0">
          <div className="flex items-center gap-2 text-[#123C35]">
            <GitCompare className="w-5 h-5 text-[#123C35]" />
            <div>
              <h3 className="text-lg font-bold text-[#123C35]">
                Version Comparison: Question {ordinal}
              </h3>
              <p className="text-xs text-[#64748B]">
                Inspect changes between immutable versions
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-[#123C35] transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Version Selector Bar */}
        <div className="bg-[#F8FAFC] p-3 rounded-xl border border-[#CBD5E1] flex flex-wrap items-center justify-between gap-4 flex-shrink-0">
          <div className="flex items-center gap-3 text-xs">
            <div className="flex items-center gap-1.5">
              <span className="text-[#64748B] font-semibold">Compare Base:</span>
              <select
                value={versionA}
                onChange={(e) => setVersionA(Number(e.target.value))}
                className="bg-white border border-[#CBD5E1] text-[#123C35] font-bold rounded-lg px-2.5 py-1 text-xs focus:outline-none focus:border-[#123C35]"
              >
                {versions.map(v => (
                  <option key={v.version_number} value={v.version_number}>
                    v{v.version_number} ({v.review_status})
                  </option>
                ))}
              </select>
            </div>

            <ArrowRight className="w-4 h-4 text-[#64748B]" />

            <div className="flex items-center gap-1.5">
              <span className="text-[#64748B] font-semibold">Target:</span>
              <select
                value={versionB}
                onChange={(e) => setVersionB(Number(e.target.value))}
                className="bg-white border border-[#CBD5E1] text-[#123C35] font-bold rounded-lg px-2.5 py-1 text-xs focus:outline-none focus:border-[#123C35]"
              >
                {versions.map(v => (
                  <option key={v.version_number} value={v.version_number}>
                    v{v.version_number} ({v.review_status})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[11px] text-[#64748B] font-semibold">
              {changedFields.length === 0
                ? 'Identical versions'
                : `${changedFields.length} field(s) modified: ${changedFields.join(', ')}`}
            </span>
          </div>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-900 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Diff Content View */}
        {isLoading ? (
          <div className="flex-1 flex items-center justify-center p-12 text-[#64748B] text-xs">
            Loading version comparison...
          </div>
        ) : diffData && detailsA && detailsB ? (
          <div className="flex-1 overflow-y-auto space-y-4 pr-1">
            {/* Question Stem Comparison */}
            <div className={`p-3.5 rounded-xl border text-xs ${
              isFieldChanged('question_text')
                ? 'bg-amber-50/70 border-amber-200'
                : 'bg-[#F8FAFC] border-[#E2E8F0]'
            }`}>
              <div className="flex items-center justify-between mb-2">
                <span className="font-bold text-[#123C35] flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-[#123C35]" />
                  Question Stem
                </span>
                {isFieldChanged('question_text') && (
                  <span className="text-[10px] bg-amber-100 text-amber-900 px-2 py-0.5 rounded font-mono font-bold border border-amber-300">
                    MODIFIED
                  </span>
                )}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="p-2.5 rounded-lg bg-white border border-[#E2E8F0]">
                  <div className="text-[10px] text-[#64748B] font-mono mb-1">Version v{detailsA.version_number} (Base)</div>
                  <div className="text-[#1F2937] leading-relaxed">{detailsA.question_text}</div>
                </div>
                <div className="p-2.5 rounded-lg bg-white border border-[#E2E8F0]">
                  <div className="text-[10px] text-[#64748B] font-mono mb-1">Version v{detailsB.version_number} (Target)</div>
                  <div className={`leading-relaxed ${isFieldChanged('question_text') ? 'text-amber-950 font-semibold' : 'text-[#1F2937]'}`}>
                    {detailsB.question_text}
                  </div>
                </div>
              </div>
            </div>

            {/* Answer Options & Correct Answer Comparison */}
            <div className={`p-3.5 rounded-xl border text-xs ${
              isFieldChanged('options') || isFieldChanged('correct_answer')
                ? 'bg-amber-50/70 border-amber-200'
                : 'bg-[#F8FAFC] border-[#E2E8F0]'
            }`}>
              <div className="flex items-center justify-between mb-2">
                <span className="font-bold text-[#123C35]">Answer Options & Correct Answer</span>
                {(isFieldChanged('options') || isFieldChanged('correct_answer')) && (
                  <span className="text-[10px] bg-amber-100 text-amber-900 px-2 py-0.5 rounded font-mono font-bold border border-amber-300">
                    OPTIONS / ANSWER KEY CHANGED
                  </span>
                )}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {/* Base Options */}
                <div className="space-y-1.5 p-2.5 rounded-lg bg-white border border-[#E2E8F0]">
                  <div className="text-[10px] text-[#64748B] font-mono mb-1">Version v{detailsA.version_number} Options</div>
                  {detailsA.options.map((opt, i) => {
                    const isCorrect = detailsA.correct_answer === opt;
                    return (
                      <div
                        key={i}
                        className={`p-2 rounded-lg border text-xs flex items-center justify-between ${
                          isCorrect
                            ? 'bg-emerald-50 border-emerald-300 text-emerald-950 font-semibold'
                            : 'bg-[#F8FAFC] border-[#E2E8F0] text-[#1F2937]'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-[#64748B] font-bold">{String.fromCharCode(65 + i)}.</span>
                          <span>{opt}</span>
                        </div>
                        {isCorrect && (
                          <span className="text-[10px] bg-emerald-100 text-emerald-900 px-1.5 py-0.2 rounded font-bold border border-emerald-300">
                            CORRECT
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>

                {/* Target Options */}
                <div className="space-y-1.5 p-2.5 rounded-lg bg-white border border-[#E2E8F0]">
                  <div className="text-[10px] text-[#64748B] font-mono mb-1">Version v{detailsB.version_number} Options</div>
                  {detailsB.options.map((opt, i) => {
                    const isCorrect = detailsB.correct_answer === opt;
                    const prevOpt = detailsA.options[i];
                    const optModified = prevOpt !== opt;
                    return (
                      <div
                        key={i}
                        className={`p-2 rounded-lg border text-xs flex items-center justify-between ${
                          isCorrect
                            ? 'bg-emerald-50 border-emerald-300 text-emerald-950 font-semibold'
                            : optModified
                            ? 'bg-amber-50 border-amber-300 text-amber-950 font-medium'
                            : 'bg-[#F8FAFC] border-[#E2E8F0] text-[#1F2937]'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-[#64748B] font-bold">{String.fromCharCode(65 + i)}.</span>
                          <span className={optModified ? 'font-semibold' : ''}>{opt}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          {optModified && (
                            <span className="text-[9px] bg-amber-100 text-amber-900 border border-amber-300 px-1 py-0.2 rounded font-bold">
                              EDITED
                            </span>
                          )}
                          {isCorrect && (
                            <span className="text-[10px] bg-emerald-100 text-emerald-900 px-1.5 py-0.2 rounded font-bold border border-emerald-300">
                              CORRECT
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Rationale Comparison */}
            <div className={`p-3.5 rounded-xl border text-xs ${
              isFieldChanged('rationale')
                ? 'bg-amber-50/70 border-amber-200'
                : 'bg-[#F8FAFC] border-[#E2E8F0]'
            }`}>
              <div className="flex items-center justify-between mb-2">
                <span className="font-bold text-[#123C35]">Pedagogical Rationale</span>
                {isFieldChanged('rationale') && (
                  <span className="text-[10px] bg-amber-100 text-amber-900 px-2 py-0.5 rounded font-mono font-bold border border-amber-300">
                    MODIFIED
                  </span>
                )}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="p-2.5 rounded-lg bg-white border border-[#E2E8F0] text-[#64748B]">
                  {detailsA.rationale || <span className="italic text-slate-400">None provided</span>}
                </div>
                <div className="p-2.5 rounded-lg bg-white border border-[#E2E8F0] text-[#1F2937]">
                  {detailsB.rationale || <span className="italic text-slate-400">None provided</span>}
                </div>
              </div>
            </div>

            {/* Metadata, Status & Notes Comparison */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <div className="p-3.5 rounded-xl bg-[#F8FAFC] border border-[#E2E8F0] space-y-2">
                <div className="font-bold text-[#123C35] flex items-center justify-between">
                  <span>v{detailsA.version_number} Status & Audit</span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                    detailsA.review_status === 'APPROVED' ? 'bg-emerald-100 text-emerald-900 border border-emerald-300' :
                    detailsA.review_status === 'OVERRIDE' ? 'bg-purple-100 text-purple-900 border border-purple-300' :
                    'bg-slate-100 text-slate-700'
                  }`}>
                    {detailsA.review_status}
                  </span>
                </div>
                <div className="text-[11px] text-[#64748B]">
                  <strong className="text-[#123C35]">Notes:</strong> {detailsA.teacher_notes || <span className="text-slate-400 italic">None</span>}
                </div>
                <div className="text-[10px] text-[#64748B] font-mono">
                  Created: {detailsA.created_at ? new Date(detailsA.created_at).toLocaleString() : 'N/A'}
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-[#F8FAFC] border border-[#E2E8F0] space-y-2">
                <div className="font-bold text-[#123C35] flex items-center justify-between">
                  <span>v{detailsB.version_number} Status & Audit</span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                    detailsB.review_status === 'APPROVED' ? 'bg-emerald-100 text-emerald-900 border border-emerald-300' :
                    detailsB.review_status === 'OVERRIDE' ? 'bg-purple-100 text-purple-900 border border-purple-300' :
                    'bg-slate-100 text-slate-700'
                  }`}>
                    {detailsB.review_status}
                  </span>
                </div>
                <div className="text-[11px] text-[#64748B]">
                  <strong className="text-[#123C35]">Notes:</strong> {detailsB.teacher_notes || <span className="text-slate-400 italic">None</span>}
                </div>
                <div className="text-[10px] text-[#64748B] font-mono">
                  Created: {detailsB.created_at ? new Date(detailsB.created_at).toLocaleString() : 'N/A'}
                </div>
              </div>
            </div>
          </div>
        ) : null}

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-[#E2E8F0] pt-3 flex-shrink-0 text-xs">
          <span className="text-[#64748B]">
            Immutable History: All versions are preserved permanently and cannot be overwritten.
          </span>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-[#123C35] hover:bg-[#0c2a25] text-white font-semibold transition cursor-pointer shadow-xs"
          >
            Close Diff
          </button>
        </div>
      </div>
    </div>
  );
}
