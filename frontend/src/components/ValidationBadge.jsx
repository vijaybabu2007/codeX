import React from 'react';
import { AlertCircle, AlertTriangle, CheckCircle2, ShieldAlert, Info } from 'lucide-react';

export default function ValidationBadge({ validations = [] }) {
  if (!validations || validations.length === 0) {
    return (
      <div className="flex items-center gap-1.5 text-xs text-[#065F46] bg-[#ECFDF5] border border-[#A7F3D0] px-3 py-1.5 rounded-xl font-semibold w-fit shadow-sm">
        <CheckCircle2 className="w-3.5 h-3.5 text-[#059669]" />
        <span>Deterministic Validations Clean • 0 Issues</span>
      </div>
    );
  }

  const criticals = validations.filter(v => v.severity === 'CRITICAL');
  const warnings = validations.filter(v => v.severity === 'WARNING');
  const infos = validations.filter(v => v.severity === 'INFO');

  return (
    <div className="flex flex-col gap-2 w-full my-3">
      {criticals.map((c, i) => (
        <div
          key={i}
          className="flex items-start gap-3 p-3.5 rounded-xl bg-[#FEF2F2] border border-[#FECACA] text-[#991B1B] text-xs shadow-sm"
        >
          <div className="p-1 rounded-lg bg-rose-100 text-rose-700 border border-rose-300 shrink-0 mt-0.5">
            <ShieldAlert className="w-4 h-4" />
          </div>
          <div className="flex-1 space-y-1">
            <div className="flex items-center justify-between">
              <span className="font-bold text-rose-800 uppercase tracking-wider text-[10px] font-mono">
                CRITICAL • {c.rule_code}
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-rose-200/80 text-rose-900 font-bold uppercase">
                Blocks Approval
              </span>
            </div>
            <p className="text-[#1F2937] font-medium leading-relaxed">{c.message}</p>
            {c.evidence_snippet && (
              <div className="mt-1.5 p-2 rounded-lg bg-white font-mono text-[11px] text-rose-800 border border-rose-200">
                <span className="text-slate-500 block text-[10px] uppercase tracking-wider font-semibold">Evidence:</span>
                "{c.evidence_snippet}"
              </div>
            )}
            <div className="text-[11px] text-rose-800 font-semibold pt-0.5">
              → Action Required: Use Surgical Regeneration or Manual Correction to resolve before approving.
            </div>
          </div>
        </div>
      ))}

      {warnings.map((w, i) => (
        <div
          key={i}
          className="flex items-start gap-3 p-3.5 rounded-xl bg-[#FFFBEB] border border-[#FDE68A] text-[#92400E] text-xs shadow-sm"
        >
          <div className="p-1 rounded-lg bg-amber-100 text-amber-700 border border-amber-300 shrink-0 mt-0.5">
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div className="flex-1 space-y-1">
            <div className="flex items-center justify-between">
              <span className="font-bold text-amber-800 uppercase tracking-wider text-[10px] font-mono">
                WARNING • {w.rule_code}
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-200/80 text-amber-900 font-bold uppercase">
                Teacher Review
              </span>
            </div>
            <p className="text-[#1F2937] font-medium leading-relaxed">{w.message}</p>
            {w.evidence_snippet && (
              <div className="mt-1.5 p-2 rounded-lg bg-white font-mono text-[11px] text-amber-800 border border-amber-200">
                <span className="text-slate-500 block text-[10px] uppercase tracking-wider font-semibold">Evidence:</span>
                "{w.evidence_snippet}"
              </div>
            )}
            <div className="text-[11px] text-amber-800 font-medium pt-0.5">
              → Requires explicit Teacher Review & Acknowledgement before approving.
            </div>
          </div>
        </div>
      ))}

      {infos.map((inf, i) => (
        <div
          key={i}
          className="flex items-start gap-2.5 p-2.5 rounded-xl bg-[#F8FAFC] border border-[#E2E8F0] text-[#1F2937] text-xs"
        >
          <Info className="w-3.5 h-3.5 text-[#123C35] shrink-0 mt-0.5" />
          <span>{inf.message}</span>
        </div>
      ))}
    </div>
  );
}
