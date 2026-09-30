import React, { useState, useEffect, useMemo } from 'react';
import {
  Users,
  Award,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  HelpCircle,
  Search,
  Filter,
  RefreshCw,
  Download,
  BookOpen,
  ArrowRight,
  ChevronDown,
  X,
  Target,
  BarChart2,
  Clock,
  Sparkles,
  ShieldCheck,
  UserCheck,
  GraduationCap,
  ExternalLink,
  Info
} from 'lucide-react';
import { fetchTeacherAnalytics, fetchTeacherStudentDetail } from '../api';

export default function TeacherStudentPerformance({
  currentPackId = null,
  onNavigateToStudio
}) {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedPackId, setSelectedPackId] = useState(currentPackId || 'all');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL'); // 'ALL' | 'NEEDS_ATTENTION' | 'DEVELOPING' | 'EXCELLING' | 'NOT_STARTED'
  const [refreshing, setRefreshing] = useState(false);

  // Student Detail Modal state
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [studentDetail, setStudentDetail] = useState(null);

  const loadData = async (packId = selectedPackId) => {
    try {
      setError(null);
      const data = await fetchTeacherAnalytics(packId);
      setAnalytics(data);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Failed to load teacher analytics');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData(selectedPackId);
  }, [selectedPackId]);

  const handleRefresh = () => {
    setRefreshing(true);
    loadData(selectedPackId);
  };

  const handleOpenStudentDetail = async (student) => {
    setSelectedStudent(student);
    setDetailLoading(true);
    try {
      const detail = await fetchTeacherStudentDetail(student.student_id, selectedPackId);
      setStudentDetail(detail);
    } catch (err) {
      console.error(err);
      alert('Failed to load student diagnostic detail: ' + err.message);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCloseStudentDetail = () => {
    setSelectedStudent(null);
    setStudentDetail(null);
  };

  // Export CSV
  const handleExportCSV = () => {
    if (!analytics?.students) return;
    const headers = ['Student ID', 'Name', 'Email', 'Quizzes Attempted', 'Average Score %', 'Highest Score %', 'Latest Score %', 'Mastery Tier', 'Status'];
    const rows = analytics.students.map(s => [
      `"${s.custom_student_id || s.student_id}"`,
      `"${s.name}"`,
      `"${s.email}"`,
      s.attempts_count,
      s.average_score,
      s.highest_score,
      s.latest_score,
      `"${s.mastery_tier}"`,
      `"${s.status_label}"`
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `LessonFoundry_Student_Performance_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Filter students
  const filteredStudents = useMemo(() => {
    if (!analytics?.students) return [];
    return analytics.students.filter(s => {
      // Search
      const q = searchQuery.toLowerCase().trim();
      const matchSearch = !q ||
        s.name.toLowerCase().includes(q) ||
        s.email.toLowerCase().includes(q) ||
        (s.custom_student_id && s.custom_student_id.toLowerCase().includes(q));

      if (!matchSearch) return false;

      // Status Filter
      if (statusFilter === 'NEEDS_ATTENTION') return s.needs_intervention;
      if (statusFilter === 'DEVELOPING') return s.status_label === 'Developing';
      if (statusFilter === 'EXCELLING') return s.status_label === 'Excelling' || s.status_label === 'On Track';
      if (statusFilter === 'NOT_STARTED') return s.status_label === 'Not Started';

      return true;
    });
  }, [analytics?.students, searchQuery, statusFilter]);

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="w-12 h-12 rounded-full border-4 border-[#123C35]/20 border-t-[#123C35] animate-spin" />
        <p className="text-sm font-semibold text-[#123C35]">Loading student performance analytics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-3xl mx-auto my-12 p-6 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 space-y-3">
        <div className="flex items-center gap-2 font-bold text-base">
          <AlertTriangle className="w-5 h-5 text-rose-600" />
          <span>Unable to load student analytics</span>
        </div>
        <p className="text-xs font-mono text-rose-700">{error}</p>
        <button
          onClick={() => loadData(selectedPackId)}
          className="px-4 py-2 bg-rose-700 hover:bg-rose-800 text-white rounded-xl text-xs font-semibold cursor-pointer shadow-sm"
        >
          Try Again
        </button>
      </div>
    );
  }

  const { summary, objectives_analysis, recent_attempts, available_packs, insights } = analytics;

  return (
    <div className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-8 animate-in fade-in duration-200">
      {/* Top Banner / Breadcrumb & View Controls */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-4 border-b border-[#E2E8F0]">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="p-2 rounded-xl bg-[#123C35] text-[#D4AF37] shadow-md">
              <GraduationCap className="w-5 h-5" />
            </span>
            <div>
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-[#123C35]">
                Student Performance & Mastery Dashboard
              </h1>
              <p className="text-xs sm:text-sm text-[#64748B]">
                Classroom-wide formative quiz analytics, objective mastery tracking, and intervention diagnostics.
              </p>
            </div>
          </div>
        </div>

        {/* Global Controls */}
        <div className="flex flex-wrap items-center gap-2.5 w-full md:w-auto">
          {/* Pack Selector */}
          <div className="relative flex-1 md:flex-initial">
            <select
              value={selectedPackId}
              onChange={(e) => setSelectedPackId(e.target.value)}
              className="w-full md:w-64 appearance-none pl-3 pr-8 py-2 rounded-xl bg-white border border-[#CBD5E1] text-xs font-semibold text-[#1F2937] hover:border-[#123C35] focus:outline-none focus:ring-2 focus:ring-[#123C35]/20 shadow-xs cursor-pointer"
            >
              <option value="all">📚 All Learning Packs ({available_packs?.length || 0})</option>
              {available_packs?.map(p => (
                <option key={p.pack_id} value={p.pack_id}>
                  {p.title} ({p.attempts_count} attempt{p.attempts_count === 1 ? '' : 's'})
                </option>
              ))}
            </select>
            <ChevronDown className="w-4 h-4 text-[#64748B] absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>

          {/* Refresh Button */}
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-white hover:bg-slate-50 border border-[#CBD5E1] text-[#123C35] text-xs font-semibold transition cursor-pointer shadow-xs"
            title="Refresh latest student results"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-[#D4AF37]' : ''}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>

          {/* Export CSV */}
          <button
            onClick={handleExportCSV}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-[#123C35] hover:bg-[#0c2a25] text-white text-xs font-semibold transition cursor-pointer shadow-sm"
            title="Export student results to CSV"
          >
            <Download className="w-3.5 h-3.5 text-[#D4AF37]" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Actionable Pedagogical Insights Banner (if any) */}
      {insights && insights.length > 0 && (
        <div className="space-y-3">
          {insights.map((insight, idx) => (
            <div
              key={idx}
              className={`p-4 rounded-2xl border flex flex-col md:flex-row items-start md:items-center justify-between gap-3 shadow-xs ${
                insight.type === 'WARNING'
                  ? 'bg-amber-50/80 border-amber-200 text-amber-900'
                  : insight.type === 'ALERT'
                  ? 'bg-rose-50/80 border-rose-200 text-rose-900'
                  : 'bg-emerald-50/80 border-emerald-200 text-emerald-900'
              }`}
            >
              <div className="flex items-start gap-3">
                <div className={`p-2 rounded-xl shrink-0 mt-0.5 ${
                  insight.type === 'WARNING'
                    ? 'bg-amber-100 text-amber-800'
                    : insight.type === 'ALERT'
                    ? 'bg-rose-100 text-rose-800'
                    : 'bg-emerald-100 text-emerald-800'
                }`}>
                  {insight.type === 'WARNING' ? <AlertTriangle className="w-4 h-4" /> :
                   insight.type === 'ALERT' ? <Info className="w-4 h-4" /> :
                   <CheckCircle className="w-4 h-4" />}
                </div>
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider">{insight.title}</h4>
                  <p className="text-xs mt-0.5 leading-relaxed opacity-90">{insight.message}</p>
                  <p className="text-[11px] font-medium mt-1 text-[#123C35] bg-white/70 px-2 py-0.5 rounded-md inline-block border border-black/5">
                    💡 {insight.recommendation}
                  </p>
                </div>
              </div>

              {insight.type === 'ALERT' && (
                <button
                  onClick={() => setStatusFilter('NEEDS_ATTENTION')}
                  className="shrink-0 px-3 py-1.5 rounded-xl bg-rose-700 hover:bg-rose-800 text-white text-xs font-semibold cursor-pointer shadow-xs transition"
                >
                  View At-Risk Students
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Executive KPI Metric Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1: Class Average Score */}
        <div className="premium-card p-5 space-y-3">
          <div className="flex items-center justify-between text-[#64748B]">
            <span className="text-xs font-bold uppercase tracking-wider">Class Average Score</span>
            <span className="p-2 rounded-xl bg-[#123C35]/10 text-[#123C35]">
              <TrendingUp className="w-4 h-4 text-[#D4AF37]" />
            </span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className={`text-3xl font-extrabold ${
              summary.class_average_score >= 80 ? 'text-emerald-600' :
              summary.class_average_score >= 60 ? 'text-amber-600' : 'text-rose-600'
            }`}>
              {summary.class_average_score}%
            </span>
            <span className="text-xs text-[#64748B] font-medium">
              across {summary.total_quiz_attempts} quiz attempts
            </span>
          </div>
          <div className="flex items-center justify-between pt-2 border-t border-[#E2E8F0] text-xs">
            <span className="text-[#64748B]">Pass Rate (≥ 60%):</span>
            <span className="font-bold text-[#123C35]">{summary.pass_rate}%</span>
          </div>
        </div>

        {/* KPI 2: Quiz Attempts Completed */}
        <div className="premium-card p-5 space-y-3">
          <div className="flex items-center justify-between text-[#64748B]">
            <span className="text-xs font-bold uppercase tracking-wider">Total Quiz Submissions</span>
            <span className="p-2 rounded-xl bg-[#123C35]/10 text-[#123C35]">
              <CheckCircle className="w-4 h-4 text-[#123C35]" />
            </span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-[#123C35]">
              {summary.total_quiz_attempts}
            </span>
            <span className="text-xs text-[#64748B] font-medium">
              formative assessments
            </span>
          </div>
          <div className="flex items-center justify-between pt-2 border-t border-[#E2E8F0] text-xs">
            <span className="text-[#64748B]">Avg Attempts / Student:</span>
            <span className="font-bold text-[#123C35]">
              {summary.active_students_count > 0
                ? (summary.total_quiz_attempts / summary.active_students_count).toFixed(1)
                : '0'}
            </span>
          </div>
        </div>

        {/* KPI 3: Active Student Participation */}
        <div className="premium-card p-5 space-y-3">
          <div className="flex items-center justify-between text-[#64748B]">
            <span className="text-xs font-bold uppercase tracking-wider">Learner Engagement</span>
            <span className="p-2 rounded-xl bg-[#123C35]/10 text-[#123C35]">
              <Users className="w-4 h-4 text-[#123C35]" />
            </span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-[#123C35]">
              {summary.active_students_count}
            </span>
            <span className="text-xs text-[#64748B] font-medium">
              active / {summary.total_enrolled_students} enrolled
            </span>
          </div>
          <div className="w-full bg-[#E2E8F0] rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-[#123C35] h-full rounded-full transition-all duration-500"
              style={{
                width: `${Math.min(100, Math.round((summary.active_students_count / Math.max(1, summary.total_enrolled_students)) * 100))}%`
              }}
            />
          </div>
          <div className="flex items-center justify-between text-xs text-[#64748B]">
            <span>Participation:</span>
            <span className="font-bold text-[#123C35]">
              {Math.round((summary.active_students_count / Math.max(1, summary.total_enrolled_students)) * 100)}%
            </span>
          </div>
        </div>

        {/* KPI 4: Objective Mastery Tiers */}
        <div className="premium-card p-5 space-y-3">
          <div className="flex items-center justify-between text-[#64748B]">
            <span className="text-xs font-bold uppercase tracking-wider">Mastery Distribution</span>
            <span className="p-2 rounded-xl bg-[#123C35]/10 text-[#D4AF37]">
              <Award className="w-4 h-4 text-[#D4AF37]" />
            </span>
          </div>
          {/* Segmented Progress Bar */}
          <div className="w-full flex h-3 rounded-full overflow-hidden bg-[#E2E8F0] gap-0.5">
            <div
              className="bg-emerald-500 transition-all duration-500"
              style={{ width: `${summary.mastery_distribution.mastered_percent}%` }}
              title={`Mastered: ${summary.mastery_distribution.mastered_count} (${summary.mastery_distribution.mastered_percent}%)`}
            />
            <div
              className="bg-amber-400 transition-all duration-500"
              style={{ width: `${summary.mastery_distribution.developing_percent}%` }}
              title={`Developing: ${summary.mastery_distribution.developing_count} (${summary.mastery_distribution.developing_percent}%)`}
            />
            <div
              className="bg-rose-500 transition-all duration-500"
              style={{ width: `${summary.mastery_distribution.needs_practice_percent}%` }}
              title={`Needs Practice: ${summary.mastery_distribution.needs_practice_count} (${summary.mastery_distribution.needs_practice_percent}%)`}
            />
          </div>
          <div className="grid grid-cols-3 gap-1 pt-1 text-[11px] text-center">
            <div className="p-1 rounded bg-emerald-50 border border-emerald-200/60">
              <span className="block font-bold text-emerald-700">{summary.mastery_distribution.mastered_count}</span>
              <span className="text-[10px] text-emerald-800">Mastered</span>
            </div>
            <div className="p-1 rounded bg-amber-50 border border-amber-200/60">
              <span className="block font-bold text-amber-700">{summary.mastery_distribution.developing_count}</span>
              <span className="text-[10px] text-amber-800">Dev</span>
            </div>
            <div className="p-1 rounded bg-rose-50 border border-rose-200/60">
              <span className="block font-bold text-rose-700">{summary.mastery_distribution.needs_practice_count}</span>
              <span className="text-[10px] text-rose-800">Needs Help</span>
            </div>
          </div>
        </div>
      </div>

      {/* Curricular Objectives Mastery Heatmap */}
      {objectives_analysis && objectives_analysis.length > 0 && (
        <div className="premium-card p-6 space-y-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 pb-3 border-b border-[#E2E8F0]">
            <div>
              <h2 className="text-base font-bold text-[#123C35] flex items-center gap-2">
                <Target className="w-4 h-4 text-[#D4AF37]" />
                Curricular Objectives Mastery Analysis
              </h2>
              <p className="text-xs text-[#64748B]">
                Objective-level performance mapping across contract standards. Identifying curricular bottlenecks.
              </p>
            </div>
            <span className="text-xs font-mono font-semibold text-[#123C35] bg-[#F1F5F9] px-2.5 py-1 rounded-lg border border-[#CBD5E1]">
              {objectives_analysis.length} Standard{objectives_analysis.length === 1 ? '' : 's'} Evaluated
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {objectives_analysis.slice(0, 6).map((obj) => (
              <div
                key={obj.key}
                className={`p-4 rounded-2xl border transition-all ${
                  obj.needs_attention
                    ? 'bg-rose-50/40 border-rose-200 hover:border-rose-300'
                    : 'bg-white border-[#E2E8F0] hover:border-[#123C35]/30'
                } shadow-xs space-y-3`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="px-2.5 py-0.5 rounded-md bg-[#123C35] text-[#D4AF37] font-mono text-xs font-bold">
                    {obj.objective_id}
                  </span>
                  <div className="flex items-center gap-1.5">
                    <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 text-[10px] font-semibold border border-slate-200">
                      Bloom: {obj.bloom_level}
                    </span>
                    {obj.needs_attention && (
                      <span className="px-2 py-0.5 rounded-full bg-rose-100 text-rose-700 text-[10px] font-bold border border-rose-200 flex items-center gap-1">
                        <AlertTriangle className="w-2.5 h-2.5" />
                        Remediation
                      </span>
                    )}
                  </div>
                </div>

                <p className="text-xs text-[#1F2937] font-medium line-clamp-2 leading-relaxed" title={obj.description}>
                  {obj.description || 'Contract Learning Objective'}
                </p>

                {/* Score Progress Bar */}
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[#64748B]">Class Mastery:</span>
                    <span className={`font-bold font-mono ${
                      obj.average_score >= 80 ? 'text-emerald-700' :
                      obj.average_score >= 60 ? 'text-amber-700' : 'text-rose-700'
                    }`}>
                      {obj.average_score}%
                    </span>
                  </div>
                  <div className="w-full bg-[#E2E8F0] rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        obj.average_score >= 80 ? 'bg-emerald-500' :
                        obj.average_score >= 60 ? 'bg-amber-400' : 'bg-rose-500'
                      }`}
                      style={{ width: `${Math.min(100, Math.max(4, obj.average_score))}%` }}
                    />
                  </div>
                </div>

                {/* Mini student breakdown */}
                <div className="flex items-center justify-between pt-2 border-t border-[#E2E8F0]/70 text-[11px] text-[#64748B]">
                  <span>Evaluated: <strong>{obj.students_evaluated}</strong></span>
                  <div className="flex items-center gap-2">
                    <span className="text-emerald-700 font-semibold" title="Mastered">✓ {obj.students_mastered_count}</span>
                    <span className="text-amber-700 font-semibold" title="Developing">~ {obj.students_developing_count}</span>
                    <span className="text-rose-700 font-semibold" title="Needs Practice">✕ {obj.students_needs_practice_count}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main Student Roster Section */}
      <div className="premium-card p-6 space-y-5">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-4 border-b border-[#E2E8F0]">
          <div>
            <h2 className="text-base font-bold text-[#123C35] flex items-center gap-2">
              <Users className="w-4 h-4 text-[#D4AF37]" />
              Student Performance Roster
            </h2>
            <p className="text-xs text-[#64748B]">
              Real-time submission ledger, objective diagnostic scores, and tailored remediation triggers.
            </p>
          </div>

          {/* Search & Filter Controls */}
          <div className="flex flex-wrap items-center gap-2.5 w-full md:w-auto">
            {/* Search Input */}
            <div className="relative flex-1 md:w-64">
              <Search className="w-3.5 h-3.5 text-[#64748B] absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search student or ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 rounded-xl bg-[#F8FAFC] border border-[#CBD5E1] text-xs text-[#1F2937] placeholder-[#94A3B8] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#123C35]/20 shadow-xs"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#94A3B8] hover:text-[#1F2937]"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>

            {/* Status Filter Tabs */}
            <div className="flex flex-wrap gap-1 p-1 bg-[#F1F5F9] rounded-xl border border-[#CBD5E1] text-[11px] font-semibold">
              <button
                onClick={() => setStatusFilter('ALL')}
                className={`px-2.5 py-1 rounded-lg transition cursor-pointer ${
                  statusFilter === 'ALL'
                    ? 'bg-[#123C35] text-white shadow-xs'
                    : 'text-[#64748B] hover:text-[#123C35]'
                }`}
              >
                All ({analytics.students?.length || 0})
              </button>
              <button
                onClick={() => setStatusFilter('NEEDS_ATTENTION')}
                className={`px-2.5 py-1 rounded-lg transition cursor-pointer flex items-center gap-1 ${
                  statusFilter === 'NEEDS_ATTENTION'
                    ? 'bg-rose-700 text-white shadow-xs'
                    : 'text-rose-700 hover:bg-rose-50'
                }`}
              >
                <span>Needs Help</span>
                <span className="px-1.5 py-0.2 rounded-full bg-white/20 text-[10px]">
                  {summary.at_risk_count}
                </span>
              </button>
              <button
                onClick={() => setStatusFilter('EXCELLING')}
                className={`px-2.5 py-1 rounded-lg transition cursor-pointer ${
                  statusFilter === 'EXCELLING'
                    ? 'bg-emerald-700 text-white shadow-xs'
                    : 'text-emerald-700 hover:bg-emerald-50'
                }`}
              >
                Excelling / On Track
              </button>
              <button
                onClick={() => setStatusFilter('NOT_STARTED')}
                className={`px-2.5 py-1 rounded-lg transition cursor-pointer ${
                  statusFilter === 'NOT_STARTED'
                    ? 'bg-slate-700 text-white shadow-xs'
                    : 'text-slate-600 hover:bg-slate-200/50'
                }`}
              >
                Not Started
              </button>
            </div>
          </div>
        </div>

        {/* Student Table */}
        <div className="overflow-x-auto rounded-xl border border-[#E2E8F0]">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#F8FAFC] text-[#64748B] uppercase font-bold text-[10px] tracking-wider border-b border-[#E2E8F0]">
              <tr>
                <th className="py-3 px-4">Student</th>
                <th className="py-3 px-4">Student ID</th>
                <th className="py-3 px-4 text-center">Quizzes</th>
                <th className="py-3 px-4">Average Score</th>
                <th className="py-3 px-4">Highest</th>
                <th className="py-3 px-4">Latest Attempt</th>
                <th className="py-3 px-4">Mastery Tier</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E2E8F0] bg-white">
              {filteredStudents.length === 0 ? (
                <tr>
                  <td colSpan="8" className="py-10 text-center text-[#64748B]">
                    No students match the current filter or search criteria.
                  </td>
                </tr>
              ) : (
                filteredStudents.map((s) => {
                  const initials = s.name
                    ? s.name.split(' ').map(n => n[0]).slice(0, 2).join('').toUpperCase()
                    : 'ST';
                  return (
                    <tr
                      key={s.student_id}
                      className={`hover:bg-slate-50/80 transition-colors ${
                        s.needs_intervention ? 'bg-rose-50/20' : ''
                      }`}
                    >
                      {/* Name & Avatar */}
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-3">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold font-mono text-[11px] shrink-0 shadow-xs ${
                            s.mastery_tier === 'MASTERED'
                              ? 'bg-emerald-100 text-emerald-900 border border-emerald-300'
                              : s.needs_intervention
                              ? 'bg-rose-100 text-rose-900 border border-rose-300'
                              : 'bg-[#123C35] text-[#D4AF37]'
                          }`}>
                            {initials}
                          </div>
                          <div>
                            <div className="font-bold text-[#1F2937] hover:text-[#123C35] flex items-center gap-1.5">
                              <span>{s.name}</span>
                              {s.needs_intervention && (
                                <span className="w-2 h-2 rounded-full bg-rose-500" title="At risk - requires attention" />
                              )}
                            </div>
                            <div className="text-[11px] text-[#64748B] font-mono">{s.email}</div>
                          </div>
                        </div>
                      </td>

                      {/* Custom Student ID */}
                      <td className="py-3.5 px-4 font-mono font-semibold text-[#123C35]">
                        {s.custom_student_id}
                      </td>

                      {/* Quizzes count */}
                      <td className="py-3.5 px-4 text-center font-mono font-bold">
                        <span className={`px-2 py-0.5 rounded-full ${
                          s.attempts_count > 0 ? 'bg-slate-100 text-[#123C35]' : 'bg-slate-50 text-slate-400'
                        }`}>
                          {s.attempts_count}
                        </span>
                      </td>

                      {/* Average Score */}
                      <td className="py-3.5 px-4">
                        {s.attempts_count > 0 ? (
                          <div className="flex items-center gap-2">
                            <span className={`px-2.5 py-1 rounded-lg font-mono font-bold text-xs ${
                              s.average_score >= 80
                                ? 'bg-emerald-100 text-emerald-900 border border-emerald-300'
                                : s.average_score >= 60
                                ? 'bg-amber-100 text-amber-900 border border-amber-300'
                                : 'bg-rose-100 text-rose-900 border border-rose-300'
                            }`}>
                              {s.average_score}%
                            </span>
                          </div>
                        ) : (
                          <span className="text-[#94A3B8] font-mono">—</span>
                        )}
                      </td>

                      {/* Highest Score */}
                      <td className="py-3.5 px-4 font-mono text-[#64748B]">
                        {s.attempts_count > 0 ? `${s.highest_score}%` : '—'}
                      </td>

                      {/* Latest Attempt Date */}
                      <td className="py-3.5 px-4 text-[11px] text-[#64748B] font-mono">
                        {s.latest_attempt_at ? (
                          <span>{new Date(s.latest_attempt_at).toLocaleDateString()}</span>
                        ) : (
                          <span className="text-slate-400">Never</span>
                        )}
                      </td>

                      {/* Status / Mastery Tier */}
                      <td className="py-3.5 px-4">
                        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase border inline-flex items-center gap-1 ${
                          s.status_label === 'Excelling'
                            ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                            : s.status_label === 'On Track'
                            ? 'bg-teal-50 text-teal-800 border-teal-300'
                            : s.status_label === 'Developing'
                            ? 'bg-amber-50 text-amber-800 border-amber-300'
                            : s.status_label === 'Needs Attention'
                            ? 'bg-rose-50 text-rose-800 border-rose-300'
                            : 'bg-slate-50 text-slate-500 border-slate-200'
                        }`}>
                          {s.status_label === 'Needs Attention' && <AlertTriangle className="w-2.5 h-2.5 text-rose-600" />}
                          {s.status_label === 'Excelling' && <CheckCircle className="w-2.5 h-2.5 text-emerald-600" />}
                          {s.status_label}
                        </span>
                      </td>

                      {/* Actions */}
                      <td className="py-3.5 px-4 text-right">
                        <button
                          type="button"
                          onClick={() => handleOpenStudentDetail(s)}
                          className="px-3 py-1.5 rounded-xl bg-white hover:bg-[#123C35] hover:text-white border border-[#CBD5E1] text-[#123C35] font-semibold text-xs transition cursor-pointer shadow-xs"
                        >
                          Diagnostic Dossier
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recent Activity Ledger */}
      {recent_attempts && recent_attempts.length > 0 && (
        <div className="premium-card p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#E2E8F0]">
            <div>
              <h2 className="text-base font-bold text-[#123C35] flex items-center gap-2">
                <Clock className="w-4 h-4 text-[#D4AF37]" />
                Recent Student Quiz Submissions
              </h2>
              <p className="text-xs text-[#64748B]">Live audit trail of completed formative assessments.</p>
            </div>
            <span className="text-xs text-[#64748B] font-mono">
              Showing last {recent_attempts.length} submissions
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {recent_attempts.slice(0, 9).map((att) => (
              <div
                key={att.attempt_id}
                className="p-3.5 rounded-xl bg-white border border-[#E2E8F0] shadow-xs flex items-center justify-between gap-3"
              >
                <div className="overflow-hidden">
                  <div className="font-bold text-xs text-[#1F2937] truncate">{att.student_name}</div>
                  <div className="text-[11px] text-[#64748B] truncate" title={att.pack_title}>
                    {att.pack_title}
                  </div>
                  <div className="text-[10px] text-[#94A3B8] font-mono mt-0.5">
                    {att.created_at ? new Date(att.created_at).toLocaleString() : ''}
                  </div>
                </div>

                <div className="text-right shrink-0">
                  <span className={`px-2 py-1 rounded-lg font-mono font-bold text-xs ${
                    att.score_percentage >= 80
                      ? 'bg-emerald-100 text-emerald-900 border border-emerald-200'
                      : att.score_percentage >= 60
                      ? 'bg-amber-100 text-amber-900 border border-amber-200'
                      : 'bg-rose-100 text-rose-900 border border-rose-200'
                  }`}>
                    {att.score_percentage}%
                  </span>
                  <div className="text-[10px] text-[#64748B] font-mono mt-1">
                    {att.correct_count} / {att.total_questions} correct
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* STUDENT DIAGNOSTIC DOSSIER MODAL */}
      {selectedStudent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-150">
          <div className="bg-white rounded-3xl border border-[#E2E8F0] shadow-2xl max-w-3xl w-full max-h-[90vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="px-6 py-4 bg-[#123C35] text-white flex items-center justify-between border-b border-[#D4AF37]/30">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-[#0c2a25] border border-[#D4AF37]/40 flex items-center justify-center text-[#D4AF37] font-bold text-sm font-mono">
                  {selectedStudent.name ? selectedStudent.name.slice(0, 2).toUpperCase() : 'ST'}
                </div>
                <div>
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <span>{selectedStudent.name}</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#0c2a25] text-[#D4AF37] border border-[#D4AF37]/30">
                      {selectedStudent.custom_student_id}
                    </span>
                  </h3>
                  <p className="text-xs text-emerald-100/70 font-mono">{selectedStudent.email}</p>
                </div>
              </div>

              <button
                onClick={handleCloseStudentDetail}
                className="p-1.5 rounded-xl bg-white/10 hover:bg-white/20 text-white transition cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-6 flex-1 bg-[#F8FAFC]">
              {detailLoading ? (
                <div className="py-16 text-center space-y-3">
                  <div className="w-8 h-8 rounded-full border-2 border-[#123C35]/20 border-t-[#123C35] animate-spin mx-auto" />
                  <p className="text-xs font-semibold text-[#123C35]">Loading individual diagnostic dossier...</p>
                </div>
              ) : studentDetail ? (
                <>
                  {/* Summary Stat Strip */}
                  <div className="grid grid-cols-3 gap-3">
                    <div className="p-3.5 rounded-2xl bg-white border border-[#E2E8F0] text-center shadow-xs">
                      <span className="text-[10px] text-[#64748B] font-bold uppercase tracking-wider block">Average Score</span>
                      <span className={`text-2xl font-black font-mono ${
                        studentDetail.student.average_score >= 80 ? 'text-emerald-600' :
                        studentDetail.student.average_score >= 60 ? 'text-amber-600' : 'text-rose-600'
                      }`}>
                        {studentDetail.student.average_score}%
                      </span>
                    </div>
                    <div className="p-3.5 rounded-2xl bg-white border border-[#E2E8F0] text-center shadow-xs">
                      <span className="text-[10px] text-[#64748B] font-bold uppercase tracking-wider block">Total Attempts</span>
                      <span className="text-2xl font-black font-mono text-[#123C35]">
                        {studentDetail.student.total_attempts}
                      </span>
                    </div>
                    <div className="p-3.5 rounded-2xl bg-white border border-[#E2E8F0] text-center shadow-xs">
                      <span className="text-[10px] text-[#64748B] font-bold uppercase tracking-wider block">Highest Score</span>
                      <span className="text-2xl font-black font-mono text-[#123C35]">
                        {studentDetail.student.highest_score}%
                      </span>
                    </div>
                  </div>

                  {/* Personalized Adaptive Recommendation */}
                  {studentDetail.recommendation && (
                    <div className="p-4 rounded-2xl bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 text-amber-950 space-y-2 shadow-xs">
                      <div className="flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-amber-600" />
                        <span className="text-xs font-bold uppercase tracking-wider text-amber-900">
                          Automated Diagnostic Recommendation
                        </span>
                      </div>
                      <h4 className="text-xs font-bold text-amber-950">{studentDetail.recommendation.headline}</h4>
                      <p className="text-xs text-amber-900/90 leading-relaxed font-mono">
                        {studentDetail.recommendation.explanation}
                      </p>
                      {studentDetail.recommendation.actions?.length > 0 && (
                        <div className="pt-2 flex flex-wrap gap-2">
                          {studentDetail.recommendation.actions.map((act, i) => (
                            <span key={i} className="px-2.5 py-1 rounded-xl bg-white border border-amber-300 text-amber-900 text-xs font-semibold shadow-2xs">
                              {act.label}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Objectives Breakdown */}
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold text-[#123C35] uppercase tracking-wider flex items-center gap-1.5">
                      <Target className="w-3.5 h-3.5 text-[#D4AF37]" />
                      Curricular Objectives Breakdown
                    </h4>

                    {studentDetail.objectives?.length === 0 ? (
                      <p className="text-xs text-[#64748B] italic">No objective mastery records yet for this student.</p>
                    ) : (
                      <div className="space-y-2">
                        {studentDetail.objectives.map((obj, i) => (
                          <div
                            key={i}
                            className="p-3.5 rounded-2xl bg-white border border-[#E2E8F0] shadow-xs space-y-2"
                          >
                            <div className="flex items-center justify-between gap-2">
                              <div className="flex items-center gap-2">
                                <span className="px-2 py-0.5 rounded-md bg-[#123C35] text-[#D4AF37] font-mono text-xs font-bold">
                                  {obj.objective_id}
                                </span>
                                <span className="text-xs font-bold text-[#1F2937]">
                                  {obj.description || 'Learning Objective'}
                                </span>
                              </div>
                              <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase font-mono ${
                                obj.mastery_state === 'MASTERED'
                                  ? 'bg-emerald-100 text-emerald-900'
                                  : obj.mastery_state === 'DEVELOPING'
                                  ? 'bg-amber-100 text-amber-900'
                                  : 'bg-rose-100 text-rose-900'
                              }`}>
                                {obj.mastery_state}
                              </span>
                            </div>

                            <div className="flex items-center justify-between text-xs text-[#64748B] font-mono pt-1 border-t border-[#E2E8F0]/60">
                              <span>Questions: {obj.correct_count} / {obj.attempted_count} correct</span>
                              <span className="font-bold text-[#123C35]">{obj.score_percentage}%</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Chronological Attempt History */}
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold text-[#123C35] uppercase tracking-wider flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-[#D4AF37]" />
                      Submission History Log
                    </h4>

                    {studentDetail.attempts?.length === 0 ? (
                      <p className="text-xs text-[#64748B] italic">No recorded quiz attempts.</p>
                    ) : (
                      <div className="space-y-2">
                        {studentDetail.attempts.map((att, i) => (
                          <div
                            key={att.attempt_id}
                            className="p-3 rounded-xl bg-white border border-[#E2E8F0] text-xs flex items-center justify-between gap-3 shadow-xs"
                          >
                            <div>
                              <div className="font-bold text-[#1F2937]">{att.pack_title}</div>
                              <div className="text-[11px] text-[#64748B] font-mono">
                                {att.created_at ? new Date(att.created_at).toLocaleString() : ''}
                              </div>
                            </div>
                            <div className="text-right font-mono">
                              <span className={`font-bold ${
                                att.score_percentage >= 80 ? 'text-emerald-700' :
                                att.score_percentage >= 60 ? 'text-amber-700' : 'text-rose-700'
                              }`}>
                                {att.score_percentage}%
                              </span>
                              <div className="text-[10px] text-[#64748B]">
                                {att.correct_count} / {att.total_questions}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </>
              ) : null}
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-3.5 bg-white border-t border-[#E2E8F0] flex items-center justify-end">
              <button
                type="button"
                onClick={handleCloseStudentDetail}
                className="px-4 py-2 rounded-xl bg-[#123C35] hover:bg-[#0c2a25] text-white text-xs font-semibold transition cursor-pointer shadow-sm"
              >
                Close Dossier
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
