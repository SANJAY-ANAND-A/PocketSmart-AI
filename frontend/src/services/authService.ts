import { apiClient } from './api';
import type { AuthResponse, LoginRequest, RegisterRequest, User } from '../types/auth';

export const authService = {
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    return apiClient<AuthResponse>('/auth/login', {
      method: 'POST',
      body: credentials,
    });
  },

  async register(data: RegisterRequest): Promise<User> {
    return apiClient<User>('/auth/register', {
      method: 'POST',
      body: data,
    });
  },

  async getMe(): Promise<User> {
    return apiClient<User>('/auth/me', {
      method: 'GET',
    });
  },
};
