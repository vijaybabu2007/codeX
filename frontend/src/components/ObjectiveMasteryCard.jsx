import React from 'react';
import { CheckCircle2, AlertTriangle, TrendingUp } from 'lucide-react';

export default function ObjectiveMasteryCard({ objective, objectiveDescription }) {
  const { objective_id, attempted, correct, score_percentage, mastery_state } = objective;

  const stateConfig = {
    MASTERED: {
      label: 'MASTERED',
      badgeClass: 'bg-[#ECFDF5] text-[#065F46] border-[#A7F3D0]',
      barClass: 'bg-[#059669]',
      icon: <CheckCircle2 className="w-3.5 h-3.5 text-[#059669]" />
    },
    DEVELOPING: {
      label: 'DEVELOPING',
      badgeClass: 'bg-[#FFFBEB] text-[#92400E] border-[#FDE68A]',
      barClass: 'bg-[#D97706]',
      icon: <TrendingUp className="w-3.5 h-3.5 text-[#D97706]" />
    },
    NEEDS_PRACTICE: {
      label: 'NEEDS PRACTICE',
      badgeClass: 'bg-[#FEF2F2] text-[#991B1B] border-[#FECACA]',
      barClass: 'bg-[#DC2626]',
      icon: <AlertTriangle className="w-3.5 h-3.5 text-[#DC2626]" />
    }
  };

  const config = stateConfig[mastery_state] || stateConfig.DEVELOPING;
  const pct = Math.min(100, Math.max(0, Math.round(score_percentage)));

  return (
    <div className="p-4 rounded-xl bg-white border border-[#E2E8F0] shadow-sm space-y-2.5 transition hover:border-[#CBD5E1]">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-[#123C35]/10 text-[#123C35] border border-[#123C35]/20">
              {objective_id}
            </span>
            {objectiveDescription && (
              <span className="text-xs font-semibold text-[#1F2937] truncate" title={objectiveDescription}>
                {objectiveDescription}
              </span>
            )}
          </div>
          <div className="text-[11px] text-[#64748B] mt-1 font-medium">
            Answered {correct} of {attempted} {attempted === 1 ? 'question' : 'questions'} correctly ({pct}%)
          </div>
        </div>

        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold border tracking-wider uppercase shrink-0 ${config.badgeClass}`}>
          {config.icon}
          <span>{config.label}</span>
        </span>
      </div>

      {/* Deterministic Progress Bar */}
      <div className="space-y-1">
        <div className="w-full h-2 rounded-full bg-[#E2E8F0] overflow-hidden flex">
          <div
            className={`h-full rounded-full transition-all duration-500 ${config.barClass}`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <div className="flex justify-between items-center text-[10px] text-[#94A3B8] font-mono">
          <span>0%</span>
          <span className="font-semibold text-[#123C35]">{pct}% Mastery</span>
          <span>100%</span>
        </div>
      </div>
    </div>
  );
}
