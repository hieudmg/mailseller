'use client';

import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { api } from '@/lib/api';

type User = {
  id: number;
  email: string;
} | null;

type ApiResponseVoid = { error?: string };

type AuthContextType = {
  user: User;
  loading: boolean;
  login: (email: string, password: string) => Promise<ApiResponseVoid>;
  register: (email: string, password: string) => Promise<ApiResponseVoid>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const refreshUser = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.getCurrentUser();
      if (data) {
        setUser({ id: data.id, email: data.email });
      } else {
        setUser(null);
      }
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // on mount, try to load current user
    void refreshUser();
  }, [refreshUser]);

  const login = useCallback(
    async (email: string, password: string) => {
      const resp = await api.login(email, password);
      if (!resp.error) {
        // successful login - refresh user
        await refreshUser();
      }
      return { error: resp.error };
    },
    [refreshUser],
  );

  const register = useCallback(
    async (email: string, password: string) => {
      const resp = await api.register(email, password);
      if (!resp.error) {
        // try to refresh user (maybe auto-login after register)
        await refreshUser();
      }
      return { error: resp.error };
    },
    [refreshUser],
  );

  const logout = useCallback(async () => {
    await api.logout();
    setUser(null);
  }, []);

  const value: AuthContextType = {
    user,
    loading,
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}

export { AuthContext };
