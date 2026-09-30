import React from 'react';
import { Target, Award, Sparkles, AlertCircle } from 'lucide-react';
import ObjectiveMasteryCard from './ObjectiveMasteryCard';
import NextLearningAction from './NextLearningAction';

export default function MasteryProgress({
  masteryData,
  contractObjectives = [],
  onActionClick,
  onVoiceTutorClick
}) {
  if (!masteryData || !masteryData.objectives || masteryData.objectives.length === 0) {
    return null;
  }

  const { objectives, recommended_action } = masteryData;

  // Map description if contractObjectives provided
  const loDescMap = {};
  if (Array.isArray(contractObjectives)) {
    contractObjectives.forEach(lo => {
      loDescMap[lo.code] = lo.description;
    });
  }

  // Count summaries
  const masteredCount = objectives.filter(o => o.mastery_state === 'MASTERED').length;
  const developingCount = objectives.filter(o => o.mastery_state === 'DEVELOPING').length;
  const needsPracticeCount = objectives.filter(o => o.mastery_state === 'NEEDS_PRACTICE').length;

  return (
    <div className="premium-card p-6 shadow-sm space-y-6 font-sans">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#E2E8F0] pb-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold text-[#123C35] uppercase tracking-wider mb-1 font-mono">
            <Target className="w-4 h-4 text-[#D4AF37]" />
            <span>Adaptive Mastery Engine</span>
          </div>
          <h3 className="text-xl font-extrabold text-[#123C35] tracking-tight">
            Your Learning Progress
          </h3>
          <p className="text-xs text-[#64748B] mt-0.5 font-medium">
            Objective-level competence derived deterministically from your verified practice quiz answers.
          </p>
        </div>

        {/* Quick summary badges */}
        <div className="flex items-center gap-2 flex-wrap">
          {masteredCount > 0 && (
            <span className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-[#ECFDF5] text-[#065F46] border border-[#A7F3D0]">
              ✓ {masteredCount} Mastered
            </span>
          )}
          {developingCount > 0 && (
            <span className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-[#FFFBEB] text-[#92400E] border border-[#FDE68A]">
              ⚡ {developingCount} Developing
            </span>
          )}
          {needsPracticeCount > 0 && (
            <span className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-[#FEF2F2] text-[#991B1B] border border-[#FECACA]">
              ⚠ {needsPracticeCount} Needs Practice
            </span>
          )}
        </div>
      </div>

      {/* Objectives Breakdown Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {objectives.map((obj) => (
          <ObjectiveMasteryCard
            key={obj.objective_id}
            objective={obj}
            objectiveDescription={loDescMap[obj.objective_id]}
          />
        ))}
      </div>

      {/* Recommended Next Step Component */}
      {recommended_action && (
        <NextLearningAction
          recommendation={recommended_action}
          onActionClick={onActionClick}
          onVoiceTutorClick={onVoiceTutorClick}
        />
      )}
    </div>
  );
}
