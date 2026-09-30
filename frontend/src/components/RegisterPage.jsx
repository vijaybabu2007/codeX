import React, { useState } from 'react';
import {
  Sparkles,
  ShieldCheck,
  GraduationCap,
  LayoutDashboard,
  Eye,
  EyeOff,
  ArrowRight,
  AlertCircle,
  Lock,
  Mail,
  User as UserIcon,
  GitBranch,
  CheckCircle2
} from 'lucide-react';
import { authService } from '../services/authService';

export default function RegisterPage({ onRegisterSuccess, onNavigateToLogin }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState('teacher'); // 'teacher' | 'student'
  const [studentId, setStudentId] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validation
    const cleanName = name.trim();
    const cleanEmail = email.trim().toLowerCase();

    if (!cleanName) {
      setError('Please provide your full name.');
      return;
    }
    if (!cleanEmail || !cleanEmail.includes('@') || !cleanEmail.includes('.')) {
      setError('Please provide a valid email address.');
      return;
    }
    if (!password || password.length < 4) {
      setError('Password must be at least 4 characters in length.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match. Please re-enter.');
      return;
    }

    setLoading(true);
    try {
      const user = await authService.register(
        cleanName,
        cleanEmail,
        password,
        confirmPassword,
        role,
        role === 'student' ? studentId.trim() : null
      );
      if (onRegisterSuccess) {
        onRegisterSuccess(user);
      }
    } catch (err) {
      setError(err.message || 'Registration failed. Please check inputs.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-[#F8FAFC] flex flex-col lg:flex-row text-[#1F2937] font-sans selection:bg-[#123C35]/15 selection:text-[#123C35]">
      {/* Left Column: Deep Emerald Green Branding (#123C35) */}
      <div className="lg:w-6/12 p-8 sm:p-12 lg:p-16 flex flex-col justify-between border-b lg:border-b-0 lg:border-r border-[#E2E8F0] relative overflow-hidden bg-gradient-to-br from-[#123C35] via-[#0f2e29] to-[#0a1e1b] text-white">
        <div className="absolute -top-32 -left-32 w-[500px] h-[500px] bg-[#D4AF37]/10 rounded-full blur-[140px] pointer-events-none" />
        <div className="absolute -bottom-32 -right-32 w-[500px] h-[500px] bg-[#123C35]/40 rounded-full blur-[140px] pointer-events-none" />

        <div className="relative z-10">
          <div className="flex items-center gap-3.5 mb-8">
            <div className="h-11 w-11 rounded-2xl bg-[#0c2a25] border border-[#D4AF37]/40 flex items-center justify-center shadow-lg text-[#D4AF37] font-bold">
              <Sparkles className="w-6 h-6 text-[#D4AF37]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-2xl font-extrabold tracking-tight text-white">
                  LessonFoundry
                </span>
                <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-[#0c2a25] text-[#D4AF37] border border-[#D4AF37]/40 font-mono font-semibold tracking-wider uppercase">
                  SaaS Platform
                </span>
              </div>
              <p className="text-xs text-emerald-100/70 font-medium tracking-normal mt-0.5">
                Constraint-Aware Learning Asset Studio
              </p>
            </div>
          </div>

          <div className="mt-6 lg:mt-10 space-y-3 max-w-lg">
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-black text-white tracking-tight leading-tight">
              Create your institutional account
            </h1>
            <p className="text-sm text-emerald-100/90 leading-relaxed font-normal">
              Register as an educator to author and review grounded curriculum, or as a student to access interactive learning and voice-guided practice.
            </p>
          </div>
        </div>

        <div className="my-8 space-y-3 relative z-10 max-w-lg">
          <div className="flex items-center gap-3 p-3.5 rounded-xl bg-white/5 border border-white/10">
            <div className="p-2 rounded-lg bg-[#D4AF37]/15 text-[#D4AF37] border border-[#D4AF37]/30 shrink-0">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div className="text-xs">
              <strong className="text-white block font-semibold">Strict Educational Provenance</strong>
              <span className="text-emerald-100/70">Every asset cites verified ground-truth curriculum sentences.</span>
            </div>
          </div>

          <div className="flex items-center gap-3 p-3.5 rounded-xl bg-white/5 border border-white/10">
            <div className="p-2 rounded-lg bg-[#D4AF37]/15 text-[#D4AF37] border border-[#D4AF37]/30 shrink-0">
              <GitBranch className="w-4 h-4" />
            </div>
            <div className="text-xs">
              <strong className="text-white block font-semibold">Surgical Question Regeneration</strong>
              <span className="text-emerald-100/70">Regenerate only problematic questions while preserving approved siblings.</span>
            </div>
          </div>
        </div>

        <div className="relative z-10 pt-4 border-t border-white/10 text-xs text-emerald-200/70">
          LessonFoundry • Constraint-Aware Learning, Built with AI.
        </div>
      </div>

      {/* Right Column: Register Form on #F8FAFC Surface */}
      <div className="lg:w-6/12 flex items-center justify-center p-6 sm:p-12 lg:p-16 bg-[#F8FAFC]">
        <div className="w-full max-w-md space-y-5">
          <div className="text-left space-y-1">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-[#123C35] tracking-tight">
              Get Started
            </h2>
            <p className="text-xs text-[#64748B]">
              Select your role and create your credentials to begin
            </p>
          </div>

          {/* Role Intent Selection */}
          <div className="space-y-1.5">
            <label className="block text-xs font-bold text-[#1F2937]">
              Account Role
            </label>
            <div className="grid grid-cols-2 gap-3">
              {/* Teacher Choice */}
              <button
                type="button"
                onClick={() => setRole('teacher')}
                className={`p-3 rounded-2xl border-2 text-left transition-all cursor-pointer ${
                  role === 'teacher'
                    ? 'bg-white border-[#123C35] shadow-sm'
                    : 'bg-[#F1F5F9] border-[#E2E8F0] hover:border-[#CBD5E1] text-[#64748B]'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <div className={`p-1.5 rounded-xl ${role === 'teacher' ? 'bg-[#123C35] text-white' : 'bg-[#E2E8F0] text-[#64748B]'}`}>
                    <LayoutDashboard className="w-4 h-4" />
                  </div>
                  {role === 'teacher' && (
                    <CheckCircle2 className="w-4 h-4 text-[#123C35]" />
                  )}
                </div>
                <div className="font-bold text-xs text-[#123C35]">Teacher</div>
                <div className="text-[10px] text-[#64748B] mt-0.5 leading-snug">
                  Author, validate and approve learning packs
                </div>
              </button>

              {/* Student Choice */}
              <button
                type="button"
                onClick={() => setRole('student')}
                className={`p-3 rounded-2xl border-2 text-left transition-all cursor-pointer ${
                  role === 'student'
                    ? 'bg-white border-[#123C35] shadow-sm'
                    : 'bg-[#F1F5F9] border-[#E2E8F0] hover:border-[#CBD5E1] text-[#64748B]'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <div className={`p-1.5 rounded-xl ${role === 'student' ? 'bg-[#123C35] text-white' : 'bg-[#E2E8F0] text-[#64748B]'}`}>
                    <GraduationCap className="w-4 h-4" />
                  </div>
                  {role === 'student' && (
                    <CheckCircle2 className="w-4 h-4 text-[#123C35]" />
                  )}
                </div>
                <div className="font-bold text-xs text-[#123C35]">Student</div>
                <div className="text-[10px] text-[#64748B] mt-0.5 leading-snug">
                  Learn, practice and interact with voice tutor
                </div>
              </button>
            </div>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-2 shadow-sm">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <span className="leading-relaxed font-medium">{error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-3.5">
            {/* Full Name */}
            <div className="space-y-1">
              <label className="block text-xs font-bold text-[#1F2937]">
                Full Name
              </label>
              <div className="relative">
                <UserIcon className="w-4 h-4 text-[#64748B] absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder={role === 'teacher' ? 'Dr. Evelyn Reed' : 'Alex Johnson'}
                  className="w-full pl-10 pr-4 py-2 rounded-xl bg-white border border-[#CBD5E1] text-xs text-[#1F2937] placeholder-[#94A3B8] focus:outline-none focus:border-[#123C35] focus:ring-2 focus:ring-[#123C35]/15 transition-all shadow-sm font-medium"
                />
              </div>
            </div>

            {/* Email Field */}
            <div className="space-y-1">
              <label className="block text-xs font-bold text-[#1F2937]">
                Email Address
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-[#64748B] absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={role === 'teacher' ? 'educator@school.edu' : 'student@school.edu'}
                  className="w-full pl-10 pr-4 py-2 rounded-xl bg-white border border-[#CBD5E1] text-xs text-[#1F2937] placeholder-[#94A3B8] focus:outline-none focus:border-[#123C35] focus:ring-2 focus:ring-[#123C35]/15 transition-all shadow-sm font-medium"
                />
              </div>
            </div>

            {/* Optional Student ID Field for Student Role */}
            {role === 'student' && (
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <label className="block text-xs font-bold text-[#1F2937]">
                    Student ID
                  </label>
                  <span className="text-[10px] text-[#64748B] font-mono">Optional</span>
                </div>
                <div className="relative">
                  <UserIcon className="w-4 h-4 text-[#64748B] absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    value={studentId}
                    onChange={(e) => setStudentId(e.target.value)}
                    placeholder="e.g., STU001 (auto-assigned from email if blank)"
                    className="w-full pl-10 pr-4 py-2 rounded-xl bg-white border border-[#CBD5E1] text-xs text-[#1F2937] placeholder-[#94A3B8] focus:outline-none focus:border-[#123C35] focus:ring-2 focus:ring-[#123C35]/15 transition-all font-mono shadow-sm"
                  />
                </div>
              </div>
            )}

            {/* Password Field */}
            <div className="space-y-1">
              <label className="block text-xs font-bold text-[#1F2937]">
                Password (min 4 characters)
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-[#64748B] absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-10 pr-10 py-2 rounded-xl bg-white border border-[#CBD5E1] text-xs text-[#1F2937] placeholder-[#94A3B8] focus:outline-none focus:border-[#123C35] focus:ring-2 focus:ring-[#123C35]/15 transition-all font-mono shadow-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(prev => !prev)}
                  className="p-1 text-[#64748B] hover:text-[#123C35] absolute right-3 top-1/2 -translate-y-1/2 transition-colors cursor-pointer"
                >
                  {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>

            {/* Confirm Password Field */}
            <div className="space-y-1">
              <label className="block text-xs font-bold text-[#1F2937]">
                Confirm Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-[#64748B] absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-10 pr-4 py-2 rounded-xl bg-white border border-[#CBD5E1] text-xs text-[#1F2937] placeholder-[#94A3B8] focus:outline-none focus:border-[#123C35] focus:ring-2 focus:ring-[#123C35]/15 transition-all font-mono shadow-sm"
                />
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 rounded-xl font-bold text-xs text-white flex items-center justify-center gap-2 shadow-md bg-[#123C35] hover:bg-[#0c2a25] transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Creating Account...</span>
                </>
              ) : (
                <>
                  <span>Create {role === 'teacher' ? 'Teacher' : 'Student'} Account</span>
                  <ArrowRight className="w-3.5 h-3.5 text-[#D4AF37]" />
                </>
              )}
            </button>
          </form>

          {/* Login Link */}
          <div className="pt-3 border-t border-[#E2E8F0] text-center">
            <span className="text-xs text-[#64748B]">
              Already have an account?{' '}
              <button
                type="button"
                onClick={onNavigateToLogin}
                className="text-[#123C35] hover:text-[#0c2a25] font-bold cursor-pointer underline underline-offset-2 ml-1"
              >
                Sign In
              </button>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
