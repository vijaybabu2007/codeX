import React, { useState, useEffect } from 'react';
import { fetchStudentPack, submitStudentQuiz, fetchStudentDashboard, fetchStudentMastery } from '../api';
import {
  GraduationCap,
  CheckCircle2,
  XCircle,
  ArrowRight,
  BookOpen,
  HelpCircle,
  Calculator,
  Compass,
  FileCheck2,
  Sparkles,
  Eye,
  EyeOff,
  Printer,
  RotateCcw,
  Award,
  AlertCircle,
  Layers,
  ArrowLeft,
  Volume2,
  Target
} from 'lucide-react';
import VoiceTutor from './VoiceTutor';
import MasteryProgress from './MasteryProgress';
import ObjectiveMasteryCard from './ObjectiveMasteryCard';
import NextLearningAction from './NextLearningAction';

export default function StudentPortal({ packId }) {
  const [internalPackId, setInternalPackId] = useState(packId || null);
  const [dashboardData, setDashboardData] = useState(null);
  const [dashboardLoading, setDashboardLoading] = useState(false);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [isSubmittingQuiz, setIsSubmittingQuiz] = useState(false);
  const [quizScoreResult, setQuizScoreResult] = useState(null);
  const [masteryData, setMasteryData] = useState(null);
  const [voiceTutorPrompt, setVoiceTutorPrompt] = useState(null);
  const [revealedGuidance, setRevealedGuidance] = useState({
    easy: false,
    advanced: false
  });
  const [viewMode, setViewMode] = useState('interactive'); // 'interactive' | 'handout'

  // Sync internalPackId if prop changes
  useEffect(() => {
    if (packId) {
      setInternalPackId(packId);
    }
  }, [packId]);

  // Load dashboard when no pack is selected
  useEffect(() => {
    if (!internalPackId) {
      setDashboardLoading(true);
      fetchStudentDashboard()
        .then(res => {
          setDashboardData(res);
        })
        .catch(err => {
          console.warn('Dashboard fetch error', err);
        })
        .finally(() => setDashboardLoading(false));
    }
  }, [internalPackId]);

  // Load pack when internalPackId is set
  useEffect(() => {
    if (!internalPackId) {
      setData(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    fetchStudentPack(internalPackId)
      .then(res => {
        setData(res);
        setError(null);
        setSelectedAnswers({});
        setQuizScoreResult(null);
      })
      .catch(err => {
        setError(err.message);
      })
      .finally(() => setLoading(false));

    // Fetch existing objective mastery data if student previously submitted
    fetchStudentMastery(internalPackId)
      .then(mRes => {
        setMasteryData(mRes);
      })
      .catch(err => {
        // No prior attempts or guest mode
        console.log('Prior mastery status not available:', err);
      });
  }, [internalPackId]);

  if (!internalPackId) {
    return (
      <div className="max-w-5xl mx-auto py-8 px-4 sm:px-6 space-y-6 font-sans text-[#1F2937]">
        {/* Student Welcome Header */}
        <div className="premium-card p-6 shadow-sm">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 text-xs font-bold text-[#123C35] uppercase tracking-wider mb-1 font-mono">
                <GraduationCap className="w-4 h-4 text-[#D4AF37]" />
                <span>Student Learning Dashboard</span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-[#123C35] tracking-tight">
                {dashboardData?.student_name ? `Welcome back, ${dashboardData.student_name}` : 'My Learning Portal'}
              </h1>
              <p className="text-xs text-[#64748B] mt-1 font-medium">
                Access your teacher-approved lessons, interactive practice quizzes, and bilingual Voice Tutor.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="px-3 py-1.5 rounded-xl bg-[#ECFDF5] border border-[#A7F3D0] text-[#065F46] text-xs font-bold flex items-center gap-1.5 shadow-sm">
                <CheckCircle2 className="w-3.5 h-3.5 text-[#059669]" />
                Server-Certified Grounding
              </span>
            </div>
          </div>
        </div>

        {/* Feature Highlights Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-2xl bg-white border border-[#E2E8F0] shadow-sm flex items-start gap-3">
            <div className="p-2 rounded-xl bg-[#123C35] text-white shadow-sm shrink-0">
              <BookOpen className="w-5 h-5 text-[#D4AF37]" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-[#123C35]">Grounded Lessons</h4>
              <p className="text-[11px] text-[#64748B] mt-0.5 leading-snug">Verified explanations and worked examples directly from textbook source material.</p>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-white border border-[#E2E8F0] shadow-sm flex items-start gap-3">
            <div className="p-2 rounded-xl bg-[#123C35] text-white shadow-sm shrink-0">
              <HelpCircle className="w-5 h-5 text-[#D4AF37]" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-[#123C35]">Interactive Quizzes</h4>
              <p className="text-[11px] text-[#64748B] mt-0.5 leading-snug">Instant scoring, objective-aligned questions, and guided answer feedback.</p>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-white border border-[#E2E8F0] shadow-sm flex items-start gap-3">
            <div className="p-2 rounded-xl bg-[#123C35] text-white shadow-sm shrink-0">
              <Volume2 className="w-5 h-5 text-[#D4AF37]" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-[#123C35]">Bilingual Voice Tutor</h4>
              <p className="text-[11px] text-[#64748B] mt-0.5 leading-snug">Spoken interactive tutoring in English & Tamil with strict source evidence boundaries.</p>
            </div>
          </div>
        </div>

        {/* Available Learning Packs Section */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-[#123C35] flex items-center gap-2">
              <Layers className="w-4 h-4 text-[#D4AF37]" />
              <span>Available Learning Materials</span>
            </h2>
            <span className="text-xs text-[#64748B] font-mono font-semibold">
              {dashboardData?.available_packs?.length || 0} Pack(s) Ready
            </span>
          </div>

          {dashboardLoading ? (
            <div className="py-12 text-center text-[#64748B]">
              <div className="animate-spin w-8 h-8 border-2 border-[#123C35] border-t-transparent rounded-full mx-auto mb-3"></div>
              <p className="text-xs font-medium">Loading approved learning content...</p>
            </div>
          ) : dashboardData?.available_packs && dashboardData.available_packs.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {dashboardData.available_packs.map((p) => (
                <div
                  key={p.pack_id}
                  className="p-5 rounded-2xl bg-white border border-[#E2E8F0] hover:border-[#123C35] shadow-sm hover:shadow-md transition-all flex flex-col justify-between gap-4 group"
                >
                  <div>
                    <div className="flex items-center justify-between text-[11px] text-[#64748B] mb-2">
                      <span className="px-2.5 py-0.5 rounded-full bg-[#ECFDF5] text-[#065F46] border border-[#A7F3D0] font-bold">
                        Approved Lesson
                      </span>
                      <span className="font-mono font-medium">{p.target_learner_level}</span>
                    </div>
                    <h3 className="text-base font-bold text-[#123C35] group-hover:text-[#0c2a25] transition-colors">
                      {p.title}
                    </h3>
                    <p className="text-xs text-[#64748B] mt-1 leading-relaxed">
                      {p.question_count} practice question{p.question_count === 1 ? '' : 's'} included • Worked examples • Summary notes
                    </p>
                  </div>

                  <div className="pt-3 border-t border-[#E2E8F0] flex items-center justify-between">
                    <span className="text-[11px] text-[#94A3B8] font-mono">
                      {new Date(p.created_at).toLocaleDateString()}
                    </span>
                    <button
                      type="button"
                      onClick={() => setInternalPackId(p.pack_id)}
                      className="px-3.5 py-1.5 rounded-xl bg-[#123C35] hover:bg-[#0c2a25] text-white text-xs font-bold flex items-center gap-1.5 transition shadow-sm cursor-pointer"
                    >
                      <span>Open Lesson</span>
                      <ArrowRight className="w-3.5 h-3.5 text-[#D4AF37]" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 rounded-2xl bg-white border border-[#E2E8F0] text-center space-y-2 shadow-sm">
              <GraduationCap className="w-10 h-10 text-[#94A3B8] mx-auto" />
              <h4 className="text-sm font-bold text-[#123C35]">No Approved Learning Packs Yet</h4>
              <p className="text-xs text-[#64748B] max-w-md mx-auto">
                Your teachers have not published any approved learning packs yet. Check back soon or contact your course instructor.
              </p>
            </div>
          )}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-3xl mx-auto py-12 px-4 space-y-4 font-sans">
        <div className="p-5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs shadow-sm space-y-2">
          <div className="flex items-center gap-2 font-bold text-sm text-rose-900">
            <AlertCircle className="w-4 h-4 text-rose-600" />
            <span>Student Projection Notice</span>
          </div>
          <p className="leading-relaxed font-medium">{error}</p>
        </div>
        <button
          type="button"
          onClick={() => {
            setError(null);
            setInternalPackId(null);
          }}
          className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold bg-[#123C35] text-white hover:bg-[#0c2a25] transition cursor-pointer shadow-sm"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Return to Dashboard</span>
        </button>
      </div>
    );
  }

  if (loading || !data) {
    return (
      <div className="max-w-3xl mx-auto py-16 text-center text-[#64748B]">
        <div className="animate-spin w-8 h-8 border-2 border-[#123C35] border-t-transparent rounded-full mx-auto mb-3"></div>
        <p className="text-sm font-semibold text-[#123C35]">Retrieving approved student projection...</p>
      </div>
    );
  }

  const handleSelectOption = (qId, option) => {
    if (quizScoreResult) return;
    setSelectedAnswers(prev => ({ ...prev, [qId]: option }));
  };

  const handleQuizSubmit = async () => {
    if (!data?.quiz_questions || data.quiz_questions.length === 0) return;
    setIsSubmittingQuiz(true);
    try {
      const res = await submitStudentQuiz(internalPackId, selectedAnswers);
      setQuizScoreResult(res);

      // If backend returned objective performance, update mastery progress immediately
      if (res?.objective_performance) {
        setMasteryData({
          pack_id: internalPackId,
          objectives: res.objective_performance,
          recommended_action: res.recommended_action
        });
      }
    } catch (err) {
      alert(`Submission failed: ${err.message}`);
    } finally {
      setIsSubmittingQuiz(false);
    }
  };

  const handleRetakeQuiz = () => {
    setSelectedAnswers({});
    setQuizScoreResult(null);
  };

  const handleActionClick = (target) => {
    if (target === 'concept_explanation') {
      document.getElementById('concept-explanation-section')?.scrollIntoView({ behavior: 'smooth' });
    } else if (target === 'worked_example') {
      document.getElementById('worked-example-section')?.scrollIntoView({ behavior: 'smooth' });
    } else if (target === 'easy_practice') {
      document.getElementById('easy-practice-section')?.scrollIntoView({ behavior: 'smooth' });
    } else if (target === 'advanced_practice') {
      document.getElementById('advanced-practice-section')?.scrollIntoView({ behavior: 'smooth' });
    } else if (target === 'retake_quiz') {
      handleRetakeQuiz();
      document.getElementById('quiz-section')?.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleVoiceTutorClick = (query) => {
    setVoiceTutorPrompt({ text: query, timestamp: Date.now() });
    document.getElementById('voice-tutor-section')?.scrollIntoView({ behavior: 'smooth' });
  };

  const toggleGuidance = (key) => {
    setRevealedGuidance(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handlePrint = () => {
    window.print();
  };

  const hasExplanation = !!data?.concept_explanation;
  const hasWorkedExample = !!data?.worked_example;
  const hasQuestions = data?.quiz_questions && data.quiz_questions.length > 0;
  const hasEasyPractice = !!data?.easy_practice;
  const hasAdvancedPractice = !!data?.advanced_practice;
  const hasRevisionSheet = !!data?.revision_sheet;

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 space-y-8 font-sans text-[#1F2937] print:p-0 print:m-0 print:max-w-full">
      {/* Student Pack Header & Controls */}
      <div className="premium-card p-6 shadow-sm print:border-none print:shadow-none print:p-0">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-bold text-[#123C35] uppercase tracking-wider mb-1 font-mono">
              <GraduationCap className="w-4 h-4 text-[#D4AF37]" />
              <span>Student Learning Session</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#123C35] tracking-tight m-0">
              {data?.contract_title || 'Approved Learning Session'}
            </h1>
            <div className="flex flex-wrap items-center gap-3 mt-2 text-xs text-[#64748B]">
              <span>Target Level: <strong className="text-[#1F2937]">{data?.target_learner_level || 'General'}</strong></span>
              <span>•</span>
              <span className="text-[#065F46] font-bold flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-[#059669]" />
                Server Certified: Approved Content Only
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 print:hidden">
            <button
              type="button"
              onClick={() => setInternalPackId(null)}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-white hover:bg-[#F8FAFC] text-[#123C35] border border-[#CBD5E1] transition cursor-pointer shadow-sm"
              title="Return to list of available lessons"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>All Lessons</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode(prev => prev === 'interactive' ? 'handout' : 'interactive')}
              className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-white hover:bg-[#F8FAFC] text-[#123C35] border border-[#CBD5E1] transition cursor-pointer shadow-sm"
            >
              {viewMode === 'interactive' ? 'Clean Handout' : 'Interactive'}
            </button>
            <button
              type="button"
              onClick={handlePrint}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold bg-[#123C35] hover:bg-[#0c2a25] text-white shadow-sm transition cursor-pointer"
              title="Print or export clean student document as PDF"
            >
              <Printer className="w-3.5 h-3.5 text-[#D4AF37]" />
              <span>Print / PDF</span>
            </button>
          </div>
        </div>
      </div>

      {data?.message && (
        <div className="p-4 rounded-2xl bg-amber-50 border border-amber-300 text-amber-800 text-xs shadow-sm font-medium">
          {data.message}
        </div>
      )}

      {/* 🎙️ LessonFoundry Voice Tutor */}
      <div id="voice-tutor-section" className="print:hidden">
        <VoiceTutor
          packId={internalPackId}
          lastQuizSubmission={quizScoreResult}
          externalPrompt={voiceTutorPrompt}
        />
      </div>

      {/* 🎯 Adaptive Mastery Engine: Your Learning Progress */}
      {masteryData && masteryData.objectives && masteryData.objectives.length > 0 && (
        <div id="mastery-progress-section" className="print:hidden">
          <MasteryProgress
            masteryData={masteryData}
            contractObjectives={data?.objectives || []}
            onActionClick={handleActionClick}
            onVoiceTutorClick={handleVoiceTutorClick}
          />
        </div>
      )}

      {/* 1. Concept Explanation */}
      {hasExplanation && (
        <div id="concept-explanation-section" className="premium-card p-6 shadow-sm space-y-4 print:border-slate-300 print:bg-white print:text-black print:shadow-none">
          <div className="flex items-center gap-2 text-xs font-bold text-[#123C35] mb-1 font-mono">
            <BookOpen className="w-4 h-4 text-[#D4AF37]" />
            <span>1. Core Lesson Concept</span>
          </div>
          <h2 className="text-xl font-bold text-[#123C35] tracking-tight mb-2 print:text-black">{data.concept_explanation.title}</h2>
          <div className="text-[#1F2937] text-sm leading-relaxed whitespace-pre-line bg-[#F8FAFC] p-4 rounded-xl border border-[#E2E8F0] font-sans print:bg-transparent print:border-none print:text-black print:p-0">
            {data.concept_explanation.explanation}
          </div>
          <div className="flex items-center gap-2 mt-4 text-xs text-[#64748B]">
            <span className="font-semibold">Aligned Objectives:</span>
            {data.concept_explanation.objective_ids.map(lo => (
              <span key={lo} className="px-2.5 py-0.5 rounded-full bg-[#123C35]/10 text-[#123C35] border border-[#123C35]/20 font-mono text-[11px] font-bold">
                {lo}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 2. Worked / Guided Example */}
      {hasWorkedExample && (
        <div id="worked-example-section" className="premium-card p-6 shadow-sm space-y-4 print:border-slate-300 print:bg-white print:text-black print:shadow-none">
          <div className="flex items-center gap-2 text-xs font-bold text-[#123C35] font-mono">
            <Calculator className="w-4 h-4 text-[#D4AF37]" />
            <span>2. Guided Step-by-Step Example</span>
          </div>
          <h2 className="text-lg font-bold text-[#123C35] tracking-tight print:text-black">{data.worked_example.title}</h2>
          <div className="p-4 rounded-xl bg-[#F8FAFC] border border-[#E2E8F0] space-y-3 print:bg-transparent print:border-slate-200 print:p-0">
            <div className="text-xs font-bold text-[#123C35]">Scenario / Problem Context:</div>
            <p className="text-xs text-[#1F2937] leading-relaxed">{data.worked_example.scenario}</p>

            <div className="text-xs font-bold text-[#123C35] pt-2">Step-by-Step Reasoning:</div>
            <ol className="space-y-2 list-decimal list-inside text-xs text-[#1F2937]">
              {data.worked_example.steps.map((st, i) => (
                <li key={i} className="pl-1 leading-relaxed">
                  <span className="text-[#1F2937]">{st}</span>
                </li>
              ))}
            </ol>

            <div className="mt-3 p-3.5 rounded-xl bg-[#ECFDF5] border border-[#A7F3D0] text-xs">
              <strong className="text-[#065F46] font-bold">Final Answer:</strong>{' '}
              <span className="text-[#065F46] font-semibold">{data.worked_example.final_answer}</span>
            </div>
          </div>
        </div>
      )}

      {/* 3. Formative Practice Quiz */}
      {hasQuestions && (
        <div id="quiz-section" className="premium-card p-6 shadow-sm space-y-6 print:border-slate-300 print:bg-white print:text-black print:shadow-none">
          <div className="flex flex-wrap items-center justify-between border-b border-[#E2E8F0] pb-3.5 gap-2">
            <div className="flex items-center gap-2 text-xs font-bold text-[#123C35] font-mono">
              <HelpCircle className="w-4 h-4 text-[#D4AF37]" />
              <span>3. Formative Practice Quiz ({data.quiz_questions.length} Items)</span>
            </div>

            {quizScoreResult && (
              <div className="flex items-center gap-3">
                <span className="text-xs font-bold px-3 py-1 bg-[#ECFDF5] text-[#065F46] border border-[#A7F3D0] rounded-full flex items-center gap-1.5 shadow-sm">
                  <Award className="w-3.5 h-3.5 text-[#D4AF37]" />
                  Score: {quizScoreResult.correct_count} / {quizScoreResult.total_questions} ({quizScoreResult.score_percentage}%)
                </span>
                <button
                  type="button"
                  onClick={handleRetakeQuiz}
                  className="flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-semibold bg-white hover:bg-[#F8FAFC] text-[#123C35] border border-[#CBD5E1] transition shadow-sm cursor-pointer"
                >
                  <RotateCcw className="w-3 h-3 text-[#D4AF37]" />
                  <span>Retake Quiz</span>
                </button>
              </div>
            )}
          </div>

          {/* Quiz Score Summary Banner (When Submitted) */}
          {quizScoreResult && (
            <div className={`p-4 rounded-xl border text-xs flex flex-wrap items-center justify-between gap-3 shadow-sm ${
              quizScoreResult.score_percentage >= 80
                ? 'bg-[#ECFDF5] border-[#A7F3D0] text-[#065F46]'
                : quizScoreResult.score_percentage >= 50
                ? 'bg-[#FFFBEB] border-[#FDE68A] text-[#92400E]'
                : 'bg-[#FEF2F2] border-[#FECACA] text-[#991B1B]'
            }`}>
              <div>
                <div className="font-bold text-sm">
                  {quizScoreResult.score_percentage === 100
                    ? '🎉 Perfect Score! Mastered All Objectives'
                    : quizScoreResult.score_percentage >= 70
                    ? '👍 Good Progress! Core Concepts Understood'
                    : '📘 Review Recommended: Check explanations below'}
                </div>
                <div className="mt-0.5 text-[11px] font-medium opacity-90">
                  You answered {quizScoreResult.correct_count} of {quizScoreResult.total_questions} questions correctly ({quizScoreResult.score_percentage}%).
                  Review the feedback and pedagogical explanations below.
                </div>
              </div>
            </div>
          )}

          {/* Objective-Level Performance & Adaptive Recommendation (Post-Submission) */}
          {quizScoreResult?.objective_performance && quizScoreResult.objective_performance.length > 0 && (
            <div className="space-y-4 pt-1">
              <div className="p-4 rounded-xl bg-[#F8FAFC] border border-[#CBD5E1] space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs font-bold text-[#123C35] font-mono">
                    <Target className="w-3.5 h-3.5 text-[#D4AF37]" />
                    <span>Objective Performance</span>
                  </div>
                  <span className="text-[11px] font-mono font-bold text-[#64748B]">
                    Overall: {quizScoreResult.score_percentage}%
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {quizScoreResult.objective_performance.map((obj) => (
                    <ObjectiveMasteryCard
                      key={obj.objective_id}
                      objective={obj}
                    />
                  ))}
                </div>
              </div>

              {quizScoreResult.recommended_action && (
                <NextLearningAction
                  recommendation={quizScoreResult.recommended_action}
                  onActionClick={handleActionClick}
                  onVoiceTutorClick={handleVoiceTutorClick}
                />
              )}
            </div>
          )}

          {/* Questions List */}
          <div className="space-y-6">
            {data.quiz_questions.map((q, idx) => {
              const resultItem = quizScoreResult?.results?.find(r => r.question_id === q.id);
              const isEvaluated = !!resultItem;
              const isCorrect = resultItem?.is_correct;

              return (
                <div
                  key={q.id}
                  className={`border rounded-xl p-5 space-y-3 transition ${
                    isEvaluated
                      ? isCorrect
                        ? 'bg-[#ECFDF5]/50 border-[#A7F3D0]'
                        : 'bg-[#FEF2F2]/50 border-[#FECACA]'
                      : 'bg-white border-[#E2E8F0]'
                  } shadow-sm`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="text-sm font-bold text-[#1F2937]">
                      <span className="text-[#123C35] font-mono mr-2 font-bold">Q{idx + 1}.</span>
                      {q.question_text}
                    </div>
                    {isEvaluated && (
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded flex items-center gap-1 ${
                        isCorrect
                          ? 'bg-[#ECFDF5] text-[#065F46] border border-[#A7F3D0]'
                          : 'bg-[#FEF2F2] text-[#991B1B] border border-[#FECACA]'
                      }`}>
                        {isCorrect ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                        {isCorrect ? 'Correct' : 'Incorrect'}
                      </span>
                    )}
                  </div>

                  {/* Options Grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                    {q.options.map((opt, optIdx) => {
                      const isSelected = selectedAnswers[q.id] === opt;
                      const letter = String.fromCharCode(65 + optIdx);

                      // Evaluation styling
                      let optClass = 'bg-white border-[#CBD5E1] text-[#1F2937] hover:border-[#123C35] hover:bg-[#F8FAFC]';
                      if (isEvaluated) {
                        const isActualCorrect = resultItem.correct_answer === opt;
                        if (isActualCorrect) {
                          optClass = 'bg-[#ECFDF5] border-[#059669] text-[#065F46] font-bold ring-1 ring-[#059669]';
                        } else if (isSelected && !isCorrect) {
                          optClass = 'bg-[#FEF2F2] border-[#DC2626] text-[#991B1B] line-through ring-1 ring-[#DC2626]';
                        } else {
                          optClass = 'bg-[#F8FAFC] border-[#E2E8F0] text-[#94A3B8] opacity-70';
                        }
                      } else if (isSelected) {
                        optClass = 'bg-[#123C35] text-white border-[#123C35] font-bold shadow-sm';
                      }

                      return (
                        <button
                          key={optIdx}
                          type="button"
                          disabled={isEvaluated}
                          onClick={() => handleSelectOption(q.id, opt)}
                          className={`flex items-center gap-3 p-3 rounded-xl text-left text-xs transition border cursor-pointer ${optClass}`}
                        >
                          <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 ${
                            isSelected ? 'bg-[#D4AF37] text-[#123C35]' : 'bg-[#F1F5F9] text-[#123C35]'
                          }`}>
                            {letter}
                          </span>
                          <span className="flex-1">{opt}</span>
                          {isEvaluated && resultItem.correct_answer === opt && (
                            <span className="text-[10px] text-[#065F46] font-bold ml-1">✓ Correct</span>
                          )}
                        </button>
                      );
                    })}
                  </div>

                  {/* Post-Submission Pedagogical Rationale */}
                  {isEvaluated && resultItem.rationale && (
                    <div className="mt-2 p-3.5 rounded-xl bg-[#F8FAFC] border border-[#CBD5E1] text-xs text-[#1F2937] space-y-1">
                      <div className="font-bold text-[#123C35] flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-[#D4AF37]" />
                        <span>Pedagogical Explanation:</span>
                      </div>
                      <p className="leading-relaxed font-medium">{resultItem.rationale}</p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Quiz Action Bar */}
          {!quizScoreResult ? (
            <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-[#E2E8F0] print:hidden">
              <span className="text-xs text-[#64748B] font-medium">
                {Object.keys(selectedAnswers).length} of {data.quiz_questions.length} questions answered
              </span>
              <button
                type="button"
                onClick={handleQuizSubmit}
                disabled={isSubmittingQuiz || Object.keys(selectedAnswers).length === 0}
                className="btn-primary flex items-center gap-2 px-6 py-2.5 text-xs font-bold shadow-md cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span>{isSubmittingQuiz ? 'Evaluating Answers...' : 'Submit & Check Answers'}</span>
                <ArrowRight className="w-4 h-4 text-[#D4AF37]" />
              </button>
            </div>
          ) : (
            <div className="flex justify-end pt-2 print:hidden">
              <button
                type="button"
                onClick={handleRetakeQuiz}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-white hover:bg-[#F8FAFC] text-[#123C35] border border-[#CBD5E1] text-xs font-bold transition shadow-sm cursor-pointer"
              >
                <RotateCcw className="w-3.5 h-3.5 text-[#D4AF37]" />
                <span>Reset / Retake Quiz</span>
              </button>
            </div>
          )}
        </div>
      )}

      {/* 4 & 5. Differentiated Practice Tasks */}
      {(hasEasyPractice || hasAdvancedPractice) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 print:grid-cols-1 print:gap-4">
          {hasEasyPractice && (
            <div id="easy-practice-section" className="premium-card p-6 shadow-sm space-y-3.5">
              <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-2.5">
                <span className="text-xs font-bold text-[#92400E] uppercase tracking-wider font-mono">
                  Easy Practice (Recall)
                </span>
                <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-[#FFFBEB] text-[#92400E] border border-[#FDE68A] font-mono font-bold">
                  Bloom: {data.easy_practice.bloom_level}
                </span>
              </div>
              <h3 className="text-base font-bold text-[#123C35] tracking-tight">{data.easy_practice.title}</h3>
              <p className="text-xs text-[#1F2937] leading-relaxed bg-[#F8FAFC] p-3.5 rounded-xl border border-[#E2E8F0] font-medium">
                {data.easy_practice.problem_statement}
              </p>

              {/* Guidance Toggle */}
              <div className="pt-1">
                <button
                  type="button"
                  onClick={() => toggleGuidance('easy')}
                  className="flex items-center gap-1.5 text-xs font-bold text-[#123C35] hover:text-[#0c2a25] print:hidden cursor-pointer"
                >
                  {revealedGuidance.easy ? <EyeOff className="w-3.5 h-3.5 text-[#D4AF37]" /> : <Eye className="w-3.5 h-3.5 text-[#D4AF37]" />}
                  <span>{revealedGuidance.easy ? 'Hide Solution Guidance' : 'Reveal Solution Guidance'}</span>
                </button>

                {(revealedGuidance.easy || viewMode === 'handout') && (
                  <div className="mt-2.5 p-3.5 rounded-xl bg-[#FFFBEB] border border-[#FDE68A] text-xs text-[#92400E] leading-relaxed font-medium">
                    <strong className="text-[#92400E] font-bold">Solution Guidance:</strong>{' '}
                    <span>{data.easy_practice.solution_guidance}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {hasAdvancedPractice && (
            <div id="advanced-practice-section" className="premium-card p-6 shadow-sm space-y-3.5">
              <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-2.5">
                <span className="text-xs font-bold text-[#5B21B6] uppercase tracking-wider font-mono">
                  Advanced Practice (Synthesis)
                </span>
                <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-[#F5F3FF] text-[#5B21B6] border border-[#DDD6FE] font-mono font-bold">
                  Bloom: {data.advanced_practice.bloom_level}
                </span>
              </div>
              <h3 className="text-base font-bold text-[#123C35] tracking-tight">{data.advanced_practice.title}</h3>
              <p className="text-xs text-[#1F2937] leading-relaxed bg-[#F8FAFC] p-3.5 rounded-xl border border-[#E2E8F0] font-medium">
                {data.advanced_practice.problem_statement}
              </p>

              {/* Guidance Toggle */}
              <div className="pt-1">
                <button
                  type="button"
                  onClick={() => toggleGuidance('advanced')}
                  className="flex items-center gap-1.5 text-xs font-bold text-[#123C35] hover:text-[#0c2a25] print:hidden cursor-pointer"
                >
                  {revealedGuidance.advanced ? <EyeOff className="w-3.5 h-3.5 text-[#D4AF37]" /> : <Eye className="w-3.5 h-3.5 text-[#D4AF37]" />}
                  <span>{revealedGuidance.advanced ? 'Hide Solution Guidance' : 'Reveal Solution Guidance'}</span>
                </button>

                {(revealedGuidance.advanced || viewMode === 'handout') && (
                  <div className="mt-2.5 p-3.5 rounded-xl bg-[#F5F3FF] border border-[#DDD6FE] text-xs text-[#5B21B6] leading-relaxed font-medium">
                    <strong className="text-[#5B21B6] font-bold">Solution Guidance:</strong>{' '}
                    <span>{data.advanced_practice.solution_guidance}</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 6. Concise Revision Sheet */}
      {hasRevisionSheet && (
        <div id="revision-sheet-section" className="premium-card p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2 text-xs font-bold text-[#123C35] font-mono">
            <FileCheck2 className="w-4 h-4 text-[#D4AF37]" />
            <span>6. Concise Revision Sheet</span>
          </div>
          <h2 className="text-lg font-bold text-[#123C35] tracking-tight">{data.revision_sheet.title}</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 rounded-xl bg-[#F8FAFC] border border-[#E2E8F0] space-y-2">
              <div className="font-bold text-[#123C35]">Key Takeaways:</div>
              <ul className="list-disc list-inside space-y-1.5 text-[#1F2937]">
                {data.revision_sheet.key_concepts.map((kc, i) => (
                  <li key={i} className="leading-relaxed font-medium">{kc}</li>
                ))}
              </ul>
            </div>

            <div className="p-4 rounded-xl bg-[#F8FAFC] border border-[#E2E8F0] space-y-2">
              <div className="font-bold text-[#123C35]">Key Definitions:</div>
              <div className="space-y-2 text-[#1F2937]">
                {data.revision_sheet.definitions.map((def, i) => (
                  <div key={i} className="leading-relaxed">
                    <strong className="text-[#123C35] font-bold">{def.term}:</strong> {def.definition}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
