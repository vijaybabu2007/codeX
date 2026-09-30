import React from 'react';
import { Sparkles, ArrowRight, Mic, BookOpen, Calculator, Dumbbell, Award, RotateCcw } from 'lucide-react';

export default function NextLearningAction({ recommendation, onActionClick, onVoiceTutorClick }) {
  if (!recommendation) return null;

  const { objective_id, explanation, mastery_state, actions } = recommendation;
  const headlineText = recommendation.headline || recommendation.title || 'Next Recommended Step';

  const getActionIcon = (target) => {
    switch (target) {
      case 'voice_tutor':
        return <Mic className="w-3.5 h-3.5 text-[#D4AF37]" />;
      case 'concept_explanation':
        return <BookOpen className="w-3.5 h-3.5 text-[#D4AF37]" />;
      case 'worked_example':
        return <Calculator className="w-3.5 h-3.5 text-[#D4AF37]" />;
      case 'easy_practice':
      case 'advanced_practice':
        return <Dumbbell className="w-3.5 h-3.5 text-[#D4AF37]" />;
      case 'retake_quiz':
        return <RotateCcw className="w-3.5 h-3.5 text-[#D4AF37]" />;
      default:
        return <ArrowRight className="w-3.5 h-3.5 text-[#D4AF37]" />;
    }
  };

  const handleAction = (act) => {
    if (act.target === 'voice_tutor') {
      const query = act.prompt || act.contextual_query || `Help me understand ${objective_id} because I am struggling with this objective.`;
      if (onVoiceTutorClick) {
        onVoiceTutorClick(query);
      }
    } else if (onActionClick) {
      onActionClick(act.target);
    }
  };

  return (
    <div className="p-5 rounded-2xl bg-gradient-to-br from-[#123C35] to-[#0A241F] text-white shadow-md space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-white/10 text-[#D4AF37]">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <div className="text-[10px] font-bold uppercase tracking-wider text-[#D4AF37] font-mono">
              Recommended Next Step
            </div>
            <h4 className="text-sm sm:text-base font-bold text-white tracking-tight">
              {headlineText}
            </h4>
          </div>
        </div>

        {objective_id && (
          <span className="font-mono text-xs font-bold px-2.5 py-1 rounded-full bg-white/10 text-white border border-white/20 shrink-0">
            Target: {objective_id}
          </span>
        )}
      </div>

      {explanation && (
        <div className="p-3 rounded-xl bg-white/5 border border-white/10 text-xs text-white/90 leading-relaxed font-sans">
          <strong className="text-[#D4AF37] font-semibold">Evidence: </strong>
          <span>{explanation}</span>
        </div>
      )}

      {actions && actions.length > 0 && (
        <div className="space-y-2 pt-1">
          <div className="text-[11px] font-semibold text-white/70">
            Suggested Next Learning Actions:
          </div>
          <div className="flex flex-wrap items-center gap-2.5">
            {actions.map((act, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleAction(act)}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition shadow-sm cursor-pointer ${
                  act.target === 'voice_tutor'
                    ? 'bg-[#D4AF37] hover:bg-[#bfa031] text-[#123C35]'
                    : 'bg-white/10 hover:bg-white/20 text-white border border-white/20'
                }`}
                title={act.description}
              >
                {getActionIcon(act.target)}
                <span>{act.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
