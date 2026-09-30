// Authentication Service for LessonFoundry
// Provides clean session management, role handling, registration, and token persistence.

const TOKEN_KEY = 'lf_auth_token';
const USER_KEY = 'lf_auth_user';

export const authService = {
  getToken() {
    try {
      return localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY) || null;
    } catch {
      return null;
    }
  },

  getCurrentUser() {
    try {
      const raw = localStorage.getItem(USER_KEY) || sessionStorage.getItem(USER_KEY);
      if (!raw) return null;
      const user = JSON.parse(raw);
      if (!user) return null;
      // Normalize role to uppercase for strict role checks (TEACHER | STUDENT)
      return {
        ...user,
        role: (user.role || '').toUpperCase(),
        authenticated: true
      };
    } catch {
      return null;
    }
  },

  isAuthenticated() {
    return Boolean(this.getToken() && this.getCurrentUser());
  },

  async register(name, email, password, confirmPassword, role = 'teacher', studentId = null) {
    const res = await fetch('/api/v1/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name,
        email,
        password,
        confirm_password: confirmPassword,
        role: role.toLowerCase(),
        student_id: studentId || undefined
      })
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Registration failed.' }));
      throw new Error(err.detail || 'Registration failed. Please check inputs.');
    }

    const data = await res.json();
    const normalizedUser = {
      id: data.user?.id || data.user_id,
      user_id: data.user_id || data.user?.id,
      name: data.name || data.user?.name,
      email: data.user?.email || email,
      role: (data.role || data.user?.role || role).toUpperCase(),
      student_id: data.user?.student_id || studentId || null,
      authenticated: true
    };

    try {
      localStorage.setItem(TOKEN_KEY, data.token);
      localStorage.setItem(USER_KEY, JSON.stringify(normalizedUser));
    } catch (e) {
      console.warn('Storage write failed', e);
    }
    return normalizedUser;
  },

  async login(identifier, password, role = null, remember = true) {
    const res = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        identifier: identifier.trim(),
        email: identifier.trim(),
        password,
        role: role ? role.toLowerCase() : null
      })
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Authentication failed.' }));
      throw new Error(err.detail || 'Invalid email or password.');
    }

    const data = await res.json();
    const storage = remember ? localStorage : sessionStorage;

    const normalizedUser = {
      id: data.user?.id || data.user_id,
      user_id: data.user_id || data.user?.id,
      name: data.name || data.user?.name,
      email: data.user?.email || identifier,
      role: (data.role || data.user?.role || role || '').toUpperCase(),
      student_id: data.user?.student_id || null,
      authenticated: true
    };

    try {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
      sessionStorage.removeItem(TOKEN_KEY);
      sessionStorage.removeItem(USER_KEY);

      storage.setItem(TOKEN_KEY, data.token);
      storage.setItem(USER_KEY, JSON.stringify(normalizedUser));
    } catch (e) {
      console.warn('Storage write failed', e);
    }

    return normalizedUser;
  },

  async logout() {
    const token = this.getToken();
    if (token) {
      try {
        await fetch('/api/v1/auth/logout', {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` }
        });
      } catch {
        // Ignore network errors on logout
      }
    }

    try {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
      sessionStorage.removeItem(TOKEN_KEY);
      sessionStorage.removeItem(USER_KEY);
    } catch (e) {
      console.warn('Storage clear failed', e);
    }
  }
};
