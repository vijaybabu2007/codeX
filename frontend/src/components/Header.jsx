import React, { useState, useEffect, useRef } from 'react';
import {
  Sparkles,
  ShieldCheck,
  Database,
  GraduationCap,
  LayoutDashboard,
  LogOut,
  Cpu,
  ChevronDown,
  Eye,
  X
} from 'lucide-react';

export default function Header({
  mode,
  setMode,
  currentPackId,
  engineModel,
  user,
  isPreviewMode = false,
  onExitPreview,
  onEnterPreview,
  onSignOut
}) {
  const [model, setModel] = useState(engineModel || '');
  const [profileOpen, setProfileOpen] = useState(false);
  const profileRef = useRef(null);

  useEffect(() => {
    fetch('/health')
      .then(r => r.json())
      .then(d => {
        if (d.model_configured) setModel(d.model_configured);
      })
      .catch(() => {});
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e) {
      if (profileRef.current && !profileRef.current.contains(e.target)) {
        setProfileOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const rawRole = (user?.role || '').toUpperCase();
  const isTeacher = rawRole === 'TEACHER';
  const isStudent = rawRole === 'STUDENT';

  const displayName = user?.name || (isTeacher ? 'Educator' : 'Student');
  const userRole = isTeacher ? 'TEACHER' : (isStudent ? 'STUDENT' : 'GUEST');
  const userEmail = user?.email || (user?.student_id ? `ID: ${user.student_id}` : '');
  const userInitials = displayName
    .split(' ')
    .filter(Boolean)
    .map(n => n[0])
    .slice(0, 2)
    .join('')
    .toUpperCase() || 'LF';

  return (
    <header className="sticky top-0 z-40 px-4 sm:px-6 lg:px-8 py-3 transition-all bg-[#123C35] text-white border-b border-[#D4AF37]/25 shadow-md">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3">
        {/* Brand & Wordmark */}
        <div className="flex items-center gap-3 w-full md:w-auto justify-between md:justify-start">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-[#0c2a25] border border-[#D4AF37]/40 flex items-center justify-center shadow-md text-[#D4AF37] font-bold shrink-0">
              <Sparkles className="w-5 h-5 text-[#D4AF37]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-base sm:text-lg font-bold tracking-tight text-white">
                  LessonFoundry
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#0c2a25] text-[#D4AF37] border border-[#D4AF37]/35 font-mono font-semibold tracking-wider uppercase flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#D4AF37] animate-pulse"></span>
                  Verified
                </span>
              </div>
              <p className="text-[11px] text-emerald-100/70 hidden sm:block tracking-normal">
                Constraint-Aware Learning, Built with AI.
              </p>
            </div>
          </div>

          {/* Mobile Sign Out */}
          <div className="md:hidden flex items-center gap-2">
            <button
              onClick={() => onSignOut && onSignOut()}
              className="p-1.5 rounded-lg bg-[#0c2a25] border border-white/10 text-emerald-100 hover:text-rose-300 text-xs transition cursor-pointer"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Engine Telemetry Strip */}
        <div className="hidden lg:flex items-center gap-2 text-[11px] font-mono">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#0c2a25]/90 border border-white/10 text-emerald-100">
            <Cpu className="w-3.5 h-3.5 text-[#D4AF37]" />
            <span className="text-emerald-200/70">LLM:</span>
            <strong className="text-white font-medium">
              {model ? model.replace('openai/', '') : 'gpt-oss-20b'}
            </strong>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#0c2a25]/90 border border-white/10 text-emerald-100">
            <Database className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-emerald-200/70">Store:</span>
            <strong className="text-white font-medium">SQLite WAL</strong>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#0c2a25]/90 border border-white/10 text-emerald-100">
            <ShieldCheck className="w-3.5 h-3.5 text-[#D4AF37]" />
            <span className="text-emerald-200/70">Gate:</span>
            <strong className="text-white font-medium">Deterministic</strong>
          </div>
        </div>

        {/* Dynamic Navigation & Role Workspace */}
        <div className="flex items-center gap-3 w-full md:w-auto justify-end">
          {/* TEACHER WORKSPACE & PREVIEW CONTROLS */}
          {isTeacher && (
            <div className="flex items-center gap-2">
              {isPreviewMode ? (
                /* Explicit Student Preview Mode Indicator + Exit Button */
                <div className="flex items-center gap-2 bg-[#0c2a25] border border-[#D4AF37]/50 px-3 py-1.5 rounded-xl shadow-sm">
                  <div className="flex items-center gap-1.5 text-[#D4AF37] text-xs font-semibold">
                    <span className="w-2 h-2 rounded-full bg-[#D4AF37] animate-pulse" />
                    <span>Student Preview Mode</span>
                  </div>
                  <button
                    type="button"
                    onClick={onExitPreview}
                    className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-[#D4AF37]/20 hover:bg-[#D4AF37]/30 text-amber-200 text-xs font-semibold transition cursor-pointer border border-[#D4AF37]/40"
                  >
                    <X className="w-3 h-3" />
                    <span>Exit Preview</span>
                  </button>
                </div>
              ) : (
                /* Standard Teacher Studio Workspace Navigation */
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-[#0c2a25] text-white border border-[#D4AF37]/30 text-xs font-semibold shadow-inner">
                    <LayoutDashboard className="w-3.5 h-3.5 text-[#D4AF37]" />
                    <span>Teacher Studio</span>
                    <span className="w-1.5 h-1.5 rounded-full bg-[#D4AF37] animate-pulse ml-0.5" />
                  </div>
                  <button
                    type="button"
                    onClick={onEnterPreview}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white text-[#123C35] hover:bg-slate-100 font-semibold text-xs transition cursor-pointer shadow-sm border border-white/20"
                    title="Preview verified student portal experience"
                  >
                    <Eye className="w-3.5 h-3.5 text-[#123C35]" />
                    <span>Preview Student View</span>
                  </button>
                </div>
              )}
            </div>
          )}

          {/* STUDENT WORKSPACE */}
          {isStudent && (
            <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-[#0c2a25] text-white border border-[#D4AF37]/40 text-xs font-semibold shadow-md">
              <GraduationCap className="w-4 h-4 text-[#D4AF37]" />
              <span>Student Portal</span>
              <span className="w-1.5 h-1.5 rounded-full bg-[#D4AF37] animate-pulse ml-1" />
            </div>
          )}

          {/* Dynamic Authenticated User Profile Dropdown */}
          <div className="relative" ref={profileRef}>
            <button
              type="button"
              onClick={() => setProfileOpen(prev => !prev)}
              className="flex items-center gap-2 pl-2 pr-2.5 py-1 rounded-xl bg-[#0c2a25]/80 hover:bg-[#0c2a25] border border-white/15 transition-all cursor-pointer"
            >
              <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-[#123C35] bg-[#D4AF37] shadow-sm font-mono">
                {userInitials}
              </div>
              <div className="text-left hidden sm:block">
                <span className="text-xs font-semibold text-white block leading-tight">
                  {displayName}
                </span>
                <span className="text-[10px] block font-mono font-bold tracking-wider uppercase text-[#D4AF37]">
                  {userRole}
                </span>
              </div>
              <ChevronDown className="w-3.5 h-3.5 text-emerald-200/70 ml-0.5" />
            </button>

            {/* Profile Dropdown Popover (Clean White Surface) */}
            {profileOpen && (
              <div className="absolute right-0 mt-2 w-64 rounded-2xl bg-white border border-[#E2E8F0] shadow-2xl p-3 z-50 text-[#1F2937] animate-in fade-in slide-in-from-top-2 duration-150">
                <div className="p-3 rounded-xl bg-[#F8FAFC] border border-[#E2E8F0] mb-2.5">
                  <div className="flex items-center gap-2.5 mb-1.5">
                    <div className="w-9 h-9 rounded-xl flex items-center justify-center text-xs font-bold text-white bg-[#123C35]">
                      {userInitials}
                    </div>
                    <div className="overflow-hidden">
                      <div className="text-xs font-bold text-[#1F2937] truncate">
                        {displayName}
                      </div>
                      <div className="text-[11px] text-[#64748B] font-mono truncate">
                        {userEmail}
                      </div>
                    </div>
                  </div>
                  <div className="mt-2 pt-2 border-t border-[#E2E8F0] flex items-center justify-between text-[11px]">
                    <span className="text-[#64748B]">Authenticated Role:</span>
                    <span className="px-2 py-0.5 rounded-md font-mono font-bold text-[10px] tracking-wider uppercase bg-[#123C35] text-white">
                      {userRole}
                    </span>
                  </div>
                </div>

                <div className="space-y-1">
                  <button
                    type="button"
                    onClick={() => {
                      setProfileOpen(false);
                      onSignOut && onSignOut();
                    }}
                    className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-rose-600 hover:bg-rose-50 hover:text-rose-700 transition-colors text-xs font-medium cursor-pointer"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Sign Out</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
