import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  LayoutDashboard,
  GraduationCap,
  Mail,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  AlertCircle,
  Info
} from 'lucide-react';
import { authService } from '../services/authService';

function GoogleIcon() {
  return (
    <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24">
      <path
        fill="#4285F4"
        d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.8-2.4 3.65v3.03h3.88c2.27-2.09 3.66-5.17 3.66-9.12z"
      />
      <path
        fill="#34A853"
        d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.03c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.13C3.26 21.4 7.34 24 12 24z"
      />
      <path
        fill="#FBBC05"
        d="M5.28 14.29c-.25-.72-.38-1.49-.38-2.29s.13-1.57.38-2.29V6.57H1.25C.45 8.16 0 9.97 0 12s.45 3.84 1.25 5.43l4.03-3.14z"
      />
      <path
        fill="#EA4335"
        d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.34 0 3.26 2.6 1.25 6.57l4.03 3.14c.95-2.83 3.6-4.96 6.72-4.96z"
      />
    </svg>
  );
}

function MicrosoftIcon() {
  return (
    <svg className="w-4 h-4 shrink-0" viewBox="0 0 23 23">
      <path fill="#f35325" d="M1 1h10v10H1z" />
      <path fill="#81bc06" d="M12 1h10v10H12z" />
      <path fill="#05a6f0" d="M1 12h10v10H1z" />
      <path fill="#ffba08" d="M12 12h10v10H12z" />
    </svg>
  );
}

function GithubIcon() {
  return (
    <svg className="w-4 h-4 shrink-0 text-[#17211E]" fill="currentColor" viewBox="0 0 24 24">
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
      />
    </svg>
  );
}

export default function LoginPage({
  onLoginSuccess,
  onNavigateToRegister,
  initialRole = 'teacher'
}) {
  const [selectedRole, setSelectedRole] = useState(initialRole || 'teacher');
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [infoMessage, setInfoMessage] = useState('');
  const [providers, setProviders] = useState({
    google: { enabled: false, message: 'Checking configuration...' },
    microsoft: { enabled: false, message: 'Microsoft authentication coming soon.' },
    github: { enabled: false, message: 'GitHub authentication coming soon.' }
  });

  // Check providers and incoming OAuth callbacks on mount
  useEffect(() => {
    // 1. Discover active authentication providers from backend
    fetch('/api/v1/auth/providers')
      .then((res) => res.json())
      .then((data) => {
        if (data && typeof data === 'object') {
          setProviders((prev) => ({ ...prev, ...data }));
        }
      })
      .catch(() => {});

    // 2. Check for OAuth callback parameters in window location
    if (typeof window !== 'undefined' && window.location.search) {
      const params = new URLSearchParams(window.location.search);
      const oauthToken = params.get('oauth_token') || params.get('token');
      const oauthError = params.get('error');

      if (oauthError) {
        setError(decodeURIComponent(oauthError));
        window.history.replaceState({}, document.title, window.location.pathname);
      } else if (oauthToken) {
        setLoading(true);
        setInfoMessage('Completing Google authentication...');
        window.history.replaceState({}, document.title, window.location.pathname);

        // Authoritative profile validation
        fetch('/api/v1/auth/me', {
          headers: { Authorization: `Bearer ${oauthToken}` }
        })
          .then(async (res) => {
            if (!res.ok) {
              throw new Error('Failed to validate session from Google Sign-In.');
            }
            const profile = await res.json();
            const normalized = { ...profile, authenticated: true };
            const storage = rememberMe ? localStorage : sessionStorage;
            storage.setItem('lf_auth_token', oauthToken);
            storage.setItem('lf_auth_user', JSON.stringify(normalized));
            if (onLoginSuccess) {
              onLoginSuccess(normalized);
            }
          })
          .catch((err) => {
            setError(err.message || 'Google authentication failed. Please sign in again.');
          })
          .finally(() => {
            setLoading(false);
          });
      }
    }
  }, []);

  const handleRoleChoose = (role) => {
    setSelectedRole(role);
    setError('');
    setInfoMessage('');
  };

  const handleGoogleClick = () => {
    setError('');
    setInfoMessage('');

    if (!providers.google?.enabled) {
      setError(
        'Google Sign-In is not configured for this deployment. Please use email/password or configure Google OAuth credentials.'
      );
      return;
    }

    setLoading(true);
    setInfoMessage('Connecting to Google...');
    // Real Google OAuth 2.0 Authorization Code flow redirect
    window.location.href = `/api/v1/auth/google?intended_role=${encodeURIComponent(selectedRole)}`;
  };

  const handleDisabledProviderClick = (provider) => {
    setError('');
    setInfoMessage(`${provider} sign-in is not yet implemented (coming soon). Please use your email/password.`);
  };

  const handleForgotPassword = () => {
    setInfoMessage('For account password assistance, please contact your institutional administrator or instructor.');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const cleanId = identifier.trim();
    if (!cleanId || !password) {
      setError(
        selectedRole === 'teacher'
          ? 'Please enter your Teacher email address and password.'
          : 'Please enter your Student ID or email and password.'
      );
      return;
    }

    setLoading(true);
    setError('');
    setInfoMessage('');

    try {
      const user = await authService.login(cleanId, password, selectedRole, rememberMe);
      if (onLoginSuccess) {
        onLoginSuccess(user);
      }
    } catch (err) {
      setError(err.message || 'Authentication failed. Please verify your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen w-full flex items-center justify-center p-4 sm:p-6 overflow-hidden bg-gradient-to-br from-[#F5F8F6] via-[#EEF5F1] to-[#E3EFE9] font-sans text-[#17211E] selection:bg-[#005B4F]/20 selection:text-[#005B4F]">
      {/* Nature-inspired soft blurred background layers */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Soft sunlit ambient orbs */}
        <div className="absolute -top-32 -left-32 w-[520px] h-[520px] bg-[#A7D7C5]/35 rounded-full blur-[110px]" />
        <div className="absolute top-10 -right-24 w-[460px] h-[460px] bg-[#F7EAC7]/45 rounded-full blur-[100px]" />
        <div className="absolute -bottom-36 -left-20 w-[580px] h-[580px] bg-[#2E6B56]/15 rounded-full blur-[130px]" />
        <div className="absolute -bottom-28 -right-24 w-[500px] h-[500px] bg-[#005B4F]/18 rounded-full blur-[120px]" />

        {/* Subtle foliage silhouette motifs */}
        <svg
          className="absolute -top-16 right-[15%] w-96 h-96 text-[#005B4F]/[0.035] transform rotate-12"
          viewBox="0 0 200 200"
          fill="currentColor"
        >
          <path d="M42.7,-64.2C54.9,-56.3,64.2,-43.8,70.1,-29.9C76,-16.1,78.5,-0.9,74.7,13.1C70.9,27.1,60.8,39.9,48.9,49.8C37,59.7,23.3,66.7,8.2,69.5C-6.9,72.3,-23.4,70.9,-37.2,63.4C-51,55.9,-62.1,42.3,-68.9,26.8C-75.7,11.3,-78.2,-6.1,-73.2,-21.2C-68.2,-36.3,-55.7,-49.1,-41.8,-56.5C-27.9,-63.9,-12.6,-65.9,1.9,-68.8C16.4,-71.7,30.5,-72.1,42.7,-64.2Z" transform="translate(100 100)" />
        </svg>
        <svg
          className="absolute -bottom-20 left-[10%] w-[420px] h-[420px] text-[#005B4F]/[0.03] transform -rotate-45"
          viewBox="0 0 200 200"
          fill="currentColor"
        >
          <path d="M47.7,-68.4C61.4,-59.9,71.8,-45.3,76.6,-28.9C81.4,-12.5,80.6,5.7,74.5,21.7C68.4,37.7,57,51.5,43,60.8C29,70.1,12.4,74.9,-4.4,77.3C-21.2,79.7,-38.2,79.7,-50.7,71.4C-63.2,63.1,-71.2,46.5,-75.4,29.6C-79.6,12.7,-80,-4.5,-74.6,-19.9C-69.2,-35.3,-58,-48.9,-44.6,-57.5C-31.2,-66.1,-15.6,-69.7,0.8,-70.8C17.2,-71.9,34,-68.9,47.7,-68.4Z" transform="translate(100 100)" />
        </svg>

        {/* Ambient overlay */}
        <div className="absolute inset-0 backdrop-blur-[2px] bg-white/20" />
      </div>

      {/* Main Frosted-Glass Login Card */}
      <div className="relative z-10 w-full max-w-[460px] mx-auto rounded-[24px] bg-white/80 backdrop-blur-2xl border border-white/70 shadow-[0_20px_50px_-10px_rgba(0,91,79,0.12),0_10px_25px_-5px_rgba(0,0,0,0.04),0_0_0_1px_rgba(255,255,255,0.6)_inset] p-6 sm:p-9 transition-all">
        {/* Brand Header */}
        <div className="flex flex-col items-center text-center">
          {/* Logo Mark */}
          <div className="w-12 h-12 rounded-2xl bg-[#005B4F] border border-[#D4AF37]/35 flex items-center justify-center text-[#D4AF37] shadow-md shadow-[#005B4F]/20 mb-3 transform hover:scale-105 transition-transform duration-200">
            <Sparkles className="w-6 h-6 text-[#D4AF37]" />
          </div>

          {/* Brand Wordmark */}
          <div className="flex items-center gap-1.5">
            <span className="text-2xl font-black tracking-tight text-[#17211E]">
              LessonFoundry
            </span>
          </div>

          {/* Subtitle Tagline */}
          <span className="text-[10px] tracking-[0.22em] uppercase font-bold text-[#005B4F] mt-0.5">
            AI FOR BETTER LEARNING
          </span>
        </div>

        {/* Welcome Text */}
        <div className="text-center mt-5 mb-5">
          <h1 className="text-[26px] sm:text-[28px] font-extrabold text-[#17211E] tracking-tight leading-tight">
            Welcome back
          </h1>
          <p className="text-xs sm:text-[13px] text-[#6B7470] mt-1 font-normal">
            Sign in to continue to your LessonFoundry account.
          </p>
        </div>

        {/* Role Selector: Teacher / Student */}
        <div className="grid grid-cols-2 gap-3 my-4">
          {/* Teacher Option */}
          <button
            type="button"
            id="role-select-teacher"
            onClick={() => handleRoleChoose('teacher')}
            className={`p-3 rounded-xl text-left transition-all duration-200 cursor-pointer flex items-center gap-3 border ${
              selectedRole === 'teacher'
                ? 'bg-[#005B4F] text-white border-[#005B4F] shadow-md shadow-[#005B4F]/25'
                : 'bg-white/70 hover:bg-white text-[#17211E] border-[#D5DEDA] hover:border-[#005B4F]/40'
            }`}
          >
            <div
              className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 transition-colors ${
                selectedRole === 'teacher'
                  ? 'bg-white/15 text-white'
                  : 'bg-[#005B4F]/10 text-[#005B4F]'
              }`}
            >
              <LayoutDashboard className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <div className="text-sm font-bold leading-tight">Teacher</div>
              <div
                className={`text-[10.5px] leading-tight truncate mt-0.5 ${
                  selectedRole === 'teacher' ? 'text-emerald-100/90' : 'text-[#6B7470]'
                }`}
              >
                Create & manage
              </div>
            </div>
          </button>

          {/* Student Option */}
          <button
            type="button"
            id="role-select-student"
            onClick={() => handleRoleChoose('student')}
            className={`p-3 rounded-xl text-left transition-all duration-200 cursor-pointer flex items-center gap-3 border ${
              selectedRole === 'student'
                ? 'bg-[#005B4F] text-white border-[#005B4F] shadow-md shadow-[#005B4F]/25'
                : 'bg-white/70 hover:bg-white text-[#17211E] border-[#D5DEDA] hover:border-[#005B4F]/40'
            }`}
          >
            <div
              className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 transition-colors ${
                selectedRole === 'student'
                  ? 'bg-white/15 text-white'
                  : 'bg-[#005B4F]/10 text-[#005B4F]'
              }`}
            >
              <GraduationCap className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <div className="text-sm font-bold leading-tight">Student</div>
              <div
                className={`text-[10.5px] leading-tight truncate mt-0.5 ${
                  selectedRole === 'student' ? 'text-emerald-100/90' : 'text-[#6B7470]'
                }`}
              >
                Learn & practice
              </div>
            </div>
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-4 p-3 rounded-xl bg-rose-50/90 border border-rose-200 text-rose-800 text-xs flex items-start gap-2.5 shadow-sm">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
            <span className="leading-relaxed font-medium">{error}</span>
          </div>
        )}

        {/* Informational Toast */}
        {infoMessage && (
          <div className="mb-4 p-3 rounded-xl bg-emerald-50/90 border border-emerald-200 text-[#005B4F] text-xs flex items-start gap-2.5 shadow-sm">
            <Info className="w-4 h-4 text-[#005B4F] shrink-0 mt-0.5" />
            <span className="leading-relaxed font-medium">{infoMessage}</span>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Email / Identifier Field */}
          <div className="space-y-1.5 text-left">
            <label className="block text-xs font-semibold text-[#17211E]">
              {selectedRole === 'teacher' ? 'Email address' : 'Student ID or Email'}
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-[#6B7470] absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                id="login-identifier"
                required
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                placeholder={
                  selectedRole === 'teacher'
                    ? 'youremail@college.edu'
                    : 'STU-001 or youremail@college.edu'
                }
                className="w-full h-[48px] sm:h-[50px] pl-10 pr-4 rounded-xl bg-white/95 border border-[#D5DEDA] text-sm text-[#17211E] placeholder-[#9CA3AF] focus:outline-none focus:border-[#005B4F] focus:ring-2 focus:ring-[#005B4F]/15 transition-all shadow-sm"
              />
            </div>
          </div>

          {/* Password Field */}
          <div className="space-y-1.5 text-left">
            <label className="block text-xs font-semibold text-[#17211E]">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-[#6B7470] absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type={showPassword ? 'text' : 'password'}
                id="login-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                className="w-full h-[48px] sm:h-[50px] pl-10 pr-11 rounded-xl bg-white/95 border border-[#D5DEDA] text-sm text-[#17211E] placeholder-[#9CA3AF] focus:outline-none focus:border-[#005B4F] focus:ring-2 focus:ring-[#005B4F]/15 transition-all shadow-sm"
              />
              <button
                type="button"
                id="toggle-password-visibility"
                onClick={() => setShowPassword((prev) => !prev)}
                className="p-1 text-[#6B7470] hover:text-[#005B4F] absolute right-3.5 top-1/2 -translate-y-1/2 transition-colors cursor-pointer"
                title={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Remember Me + Forgot Password Row */}
          <div className="flex items-center justify-between pt-0.5">
            <label className="flex items-center gap-2 cursor-pointer text-xs text-[#6B7470] select-none font-medium hover:text-[#17211E] transition-colors">
              <input
                type="checkbox"
                id="login-remember-me"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="rounded border-[#D5DEDA] text-[#005B4F] focus:ring-[#005B4F] w-4 h-4 cursor-pointer"
              />
              <span>Remember me</span>
            </label>

            <button
              type="button"
              id="login-forgot-password"
              onClick={handleForgotPassword}
              className="text-xs text-[#6B7470] hover:text-[#005B4F] hover:underline font-medium transition cursor-pointer"
            >
              Forgot password?
            </button>
          </div>

          {/* Primary Sign-In Button */}
          <button
            type="submit"
            id="login-submit-button"
            disabled={loading}
            className="w-full h-[48px] sm:h-[50px] rounded-xl font-semibold text-sm text-white flex items-center justify-center gap-2 shadow-md shadow-[#005B4F]/20 bg-[#005B4F] hover:bg-[#00473e] active:scale-[0.99] transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed group mt-2"
          >
            {loading ? (
              <>
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Signing in...</span>
              </>
            ) : (
              <>
                <span>Sign in</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </>
            )}
          </button>
        </form>

        {/* OR Divider */}
        <div className="relative my-5 flex items-center justify-center">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-[#D5DEDA]" />
          </div>
          <div className="relative px-3 bg-white/70 backdrop-blur-sm text-[11px] font-semibold text-[#8C9691] uppercase tracking-wider rounded-full">
            OR
          </div>
        </div>

        {/* Social Login Buttons: Google (active if configured), Microsoft & GitHub (coming soon) */}
        <div className="grid grid-cols-3 gap-2.5">
          {/* Google Button */}
          <button
            type="button"
            id="google-signin-button"
            onClick={handleGoogleClick}
            disabled={loading}
            className={`h-10 px-2.5 sm:px-3 rounded-xl border text-xs font-medium flex items-center justify-center gap-1.5 transition shadow-sm active:scale-[0.98] ${
              providers.google?.enabled
                ? 'bg-white hover:bg-slate-50 border-[#D5DEDA] hover:border-[#005B4F] text-[#17211E] cursor-pointer'
                : 'bg-slate-50/80 border-slate-200 text-slate-500 cursor-not-allowed opacity-75'
            }`}
            title={
              providers.google?.enabled
                ? 'Sign in with Google'
                : 'Google Sign-In is not configured for this deployment'
            }
          >
            <GoogleIcon />
            <span className="hidden sm:inline">Google</span>
            {!providers.google?.enabled && (
              <span className="text-[8.5px] uppercase tracking-wider text-slate-500 bg-slate-200/80 px-1 py-0.5 rounded font-mono">
                Off
              </span>
            )}
          </button>

          {/* Microsoft Button - Coming Soon */}
          <button
            type="button"
            id="microsoft-signin-button"
            onClick={() => handleDisabledProviderClick('Microsoft')}
            disabled
            className="h-10 px-2.5 sm:px-3 rounded-xl bg-slate-50/80 border border-slate-200 text-xs font-medium text-slate-400 flex items-center justify-center gap-1.5 transition shadow-sm cursor-not-allowed opacity-60"
            title="Microsoft authentication coming soon"
          >
            <MicrosoftIcon />
            <span className="hidden sm:inline">Microsoft</span>
            <span className="text-[8.5px] uppercase tracking-wider text-slate-500 bg-slate-200/80 px-1 py-0.5 rounded font-mono">
              Soon
            </span>
          </button>

          {/* GitHub Button - Coming Soon */}
          <button
            type="button"
            id="github-signin-button"
            onClick={() => handleDisabledProviderClick('GitHub')}
            disabled
            className="h-10 px-2.5 sm:px-3 rounded-xl bg-slate-50/80 border border-slate-200 text-xs font-medium text-slate-400 flex items-center justify-center gap-1.5 transition shadow-sm cursor-not-allowed opacity-60"
            title="GitHub authentication coming soon"
          >
            <GithubIcon />
            <span className="hidden sm:inline">GitHub</span>
            <span className="text-[8.5px] uppercase tracking-wider text-slate-500 bg-slate-200/80 px-1 py-0.5 rounded font-mono">
              Soon
            </span>
          </button>
        </div>

        {/* Registration Footer */}
        <div className="text-center pt-5 mt-4 border-t border-[#E5EAE7]">
          <span className="text-xs text-[#6B7470]">
            Don't have an account?{' '}
            <button
              type="button"
              id="navigate-to-register"
              onClick={onNavigateToRegister}
              className="text-[#005B4F] hover:text-[#00473e] font-bold cursor-pointer hover:underline ml-1 inline-flex items-center gap-0.5"
            >
              <span>Create account</span>
              <span aria-hidden="true">→</span>
            </button>
          </span>
        </div>
      </div>
    </div>
  );
}
