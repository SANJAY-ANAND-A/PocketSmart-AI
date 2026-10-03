export interface User {
  id: number;
  email: string;
  username: string;
  full_name?: string | null;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

export interface LoginRequest {
  username_or_email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  full_name?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}
