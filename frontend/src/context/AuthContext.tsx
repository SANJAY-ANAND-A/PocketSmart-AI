import React, { useCallback, useEffect, useState } from 'react';
import type { AuthResponse, LoginRequest, RegisterRequest, User } from '../types/auth';
import { getStoredToken, removeStoredToken, setStoredToken } from '../services/api';
import { authService } from '../services/authService';
import { AuthContext, type AuthContextType } from './authContextDef';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(getStoredToken());
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const logout = useCallback(() => {
    removeStoredToken();
    setToken(null);
    setUser(null);
    setError(null);
  }, []);

  // Check existing token and validate session on initial application mount
  useEffect(() => {
    let isMounted = true;

    async function initializeAuth() {
      const storedToken = getStoredToken();
      if (!storedToken) {
        if (isMounted) {
          setIsLoading(false);
        }
        return;
      }

      try {
        const currentUser = await authService.getMe();
        if (isMounted) {
          setUser(currentUser);
          setToken(storedToken);
        }
      } catch {
        // If 401 or invalid token, discard and clear auth state
        if (isMounted) {
          removeStoredToken();
          setToken(null);
          setUser(null);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    initializeAuth();

    return () => {
      isMounted = false;
    };
  }, []);

  const login = useCallback(async (credentials: LoginRequest): Promise<AuthResponse> => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await authService.login(credentials);
      setStoredToken(response.access_token);
      setToken(response.access_token);
      setUser(response.user);
      return response;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Login failed. Please check credentials.';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(
    async (data: RegisterRequest): Promise<User> => {
      setIsLoading(true);
      setError(null);
      try {
        const newUser = await authService.register(data);
        // Automatically authenticate user after registration
        const loginResponse = await authService.login({
          username_or_email: data.username,
          password: data.password,
        });
        setStoredToken(loginResponse.access_token);
        setToken(loginResponse.access_token);
        setUser(loginResponse.user);
        return newUser;
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Registration failed. Please check your inputs.';
        setError(message);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [],
  );

  const value: AuthContextType = {
    user,
    token,
    isAuthenticated: !!user && !!token,
    isLoading,
    error,
    login,
    register,
    logout,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
