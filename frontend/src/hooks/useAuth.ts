import { useState, useEffect, useCallback } from 'react';
import { authService } from '@/lib/auth';
import { Session, LoginCredentials, RegisterPayload, UserRole } from '@/lib/types';
import { useNavigate } from 'react-router-dom';

export function useAuth() {
  const [session, setSession] = useState<Session | null>(() => authService.getSession());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Sync session across tabs (if authService stores session in localStorage)
  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      setSession(authService.getSession());
    };

    window.addEventListener('storage', onStorage);
    return () => window.removeEventListener('storage', onStorage);
  }, []);

  const refreshSession = useCallback(() => {
    setSession(authService.getSession());
  }, []);

  const login = useCallback(async (credentials: LoginCredentials) => {
    setLoading(true);
    setError(null);

    try {
      const result = await authService.login(credentials);
      if (result.success) refreshSession();
      else setError(result.error || 'Login failed');
      return result;
    } finally {
      setLoading(false);
    }
  }, [refreshSession]);

  const register = useCallback(async (payload: RegisterPayload) => {
    setLoading(true);
    setError(null);

    try {
      const result = await authService.register(payload);
      if (result.success) refreshSession();
      else setError(result.error || 'Registration failed');
      return result;
    } finally {
      setLoading(false);
    }
  }, [refreshSession]);
  
  const navigate = useNavigate();
  const logout = useCallback(async () => {
    setLoading(true);
    try {
      await authService.logout();
      setSession(null);
      navigate('/', { replace: true });
    } finally {
      setLoading(false);
    }
  }, []);

  const forgotPassword = useCallback(async (email: string) => {
    setLoading(true);
    setError(null);
    try {
      return await authService.forgotPassword(email);
    } finally {
      setLoading(false);
    }
  }, []);

  const clearError = useCallback(() => setError(null), []);

  return {
    session,
    user: session?.user || null,
    tenant: session?.tenant || null,
    isAuthenticated: session !== null,
    isAdmin: session?.user.role === 'admin',
    loading,
    error,
    login,
    register,
    logout,
    forgotPassword,
    clearError,
    hasRole: (role: UserRole) => session?.user.role === role,
  };
}
